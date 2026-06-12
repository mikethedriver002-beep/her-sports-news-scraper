from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-exact-asset-audit-v1.1-bebe-ops-v2.8-current-logo-lock"

INPUT_MANIFEST = Path("graphics_chat_upload_manifest.csv")
INPUT_STATUS = Path("graphics_upload_pack_status.csv")
INPUT_APPROVED = Path("approved_graphics_assets.csv")
INPUT_LOGO_REGISTRY = Path("config/hsd_verified_logo_registry_v1.json")
OUT_CSV = Path("exact_asset_audit.csv")
OUT_MD = Path("exact_asset_audit_report.md")
OUT_JSON = Path("exact_asset_audit_manifest.json")

FIELDS = [
    "entity_name", "entity_type", "bundle_name", "post_slug", "source_url", "asset_ready", "exact_asset_status",
    "local_asset_path", "local_png_path", "download_status", "conversion_status", "decision", "reason"
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def registry_for_team(entity: str) -> Dict[str, Any]:
    data = read_json(INPUT_LOGO_REGISTRY)
    teams = data.get("teams") if isinstance(data.get("teams"), dict) else {}
    return teams.get(entity, {})


def url_is_blocked_for_team(url: str, entity: str) -> bool:
    reg = registry_for_team(entity)
    low = clean(url).lower()
    for token in reg.get("blocked_url_substrings", []) or []:
        if str(token).lower() in low:
            return True
    return False


def main() -> None:
    rows_in = read_csv(INPUT_MANIFEST)
    if not rows_in:
        # Pre-upload-pack phase: build a lightweight audit from approved assets if available.
        rows_in = []
        for r in read_csv(INPUT_APPROVED):
            rows_in.append({
                "entity_name": r.get("entity_name", ""),
                "entity_type": r.get("entity_type", ""),
                "bundle_name": "pre_upload_pack",
                "post_slug": "",
                "asset_ready": "Unknown",
                "exact_asset_status": "pending_upload_pack",
                "source_url": r.get("source_url", ""),
                "local_asset_path": r.get("master_path") or r.get("web_path") or "",
                "local_png_path": "",
                "download_status": "not_checked_pre_upload_pack",
                "conversion_status": "not_checked_pre_upload_pack",
            })

    audit: List[Dict[str, Any]] = []
    for r in rows_in:
        entity = clean(r.get("entity_name"))
        etype = clean(r.get("entity_type")).lower()
        source_url = clean(r.get("source_url"))
        asset_ready = clean(r.get("asset_ready"))
        exact = clean(r.get("exact_asset_status"))
        local_asset = clean(r.get("local_asset_path"))
        local_png = clean(r.get("local_png_path"))
        dstatus = clean(r.get("download_status"))
        cstatus = clean(r.get("conversion_status"))
        low_paths = " ".join([local_asset, local_png, dstatus, cstatus]).lower()
        reasons: List[str] = []
        decision = "pass"
        if "text-team-badge" in low_paths or "text_badge" in low_paths or "fallback_not_logo" in low_paths:
            decision = "fail"
            reasons.append("text/logo fallback detected; prohibited")
        if etype == "team" and url_is_blocked_for_team(source_url or local_asset or local_png, entity):
            decision = "fail"
            reasons.append("blocked stale/legacy logo source detected")
        if etype == "team" and asset_ready != "Yes":
            decision = "fail"
            reasons.append("missing exact team logo")
        if etype in {"player", "person", "athlete"} and asset_ready != "Yes":
            decision = "fail"
            reasons.append("missing exact player/person image")
        if asset_ready == "Yes" and not (local_asset or local_png):
            decision = "review" if decision == "pass" else decision
            reasons.append("asset_ready yes but no local path recorded")
        audit.append({
            "entity_name": entity,
            "entity_type": r.get("entity_type", ""),
            "bundle_name": r.get("bundle_name", ""),
            "post_slug": r.get("post_slug", ""),
            "source_url": source_url,
            "asset_ready": asset_ready,
            "exact_asset_status": exact,
            "local_asset_path": local_asset,
            "local_png_path": local_png,
            "download_status": dstatus,
            "conversion_status": cstatus,
            "decision": decision,
            "reason": "; ".join(reasons) or "exact asset requirement satisfied or pending pre-upload check",
        })

    status_rows = read_csv(INPUT_STATUS)
    blocked = [r for r in status_rows if clean(r.get("upload_pack_status")).startswith("blocked")]
    fail_count = sum(1 for r in audit if r.get("decision") == "fail")
    review_count = sum(1 for r in audit if r.get("decision") == "review")
    pass_count = sum(1 for r in audit if r.get("decision") == "pass")

    write_csv(OUT_CSV, audit, FIELDS)
    manifest = {
        "version": VERSION,
        "generated_at_utc": now(),
        "rule": "Exact real team logos and player/person images required. Text fallback prohibited.",
        "counts": {
            "assets_checked": len(audit),
            "pass": pass_count,
            "review": review_count,
            "fail": fail_count,
            "blocked_upload_packs": len(blocked),
        },
        "outputs": [OUT_CSV.as_posix(), OUT_MD.as_posix(), OUT_JSON.as_posix()],
    }
    OUT_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "# HSD Exact Asset Audit v1",
        "",
        f"Generated: {manifest['generated_at_utc']}",
        "",
        "Rule: **real exact logo/player assets required; no text fallback.**",
        "",
        f"- assets checked: {len(audit)}",
        f"- pass: {pass_count}",
        f"- review: {review_count}",
        f"- fail: {fail_count}",
        f"- blocked upload packs: {len(blocked)}",
        "",
    ]
    if blocked:
        lines += ["## Blocked upload packs", ""]
        for r in blocked:
            lines.append(f"- {r.get('bundle_name') or r.get('post_slug')}: {r.get('upload_pack_status')} | missing logos: {r.get('missing_team_logos','')} | missing players: {r.get('missing_player_images','')}")
        lines.append("")
    if audit:
        lines += ["## Asset audit", ""]
        for r in audit[:100]:
            icon = "✅" if r["decision"] == "pass" else "⚠️" if r["decision"] == "review" else "❌"
            lines.append(f"- {icon} {r['entity_type']} | {r['entity_name']} | {r['decision']} | {r['reason']}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
