from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-operator-status-v3.2.2-bebe-ops-v2.1"
FIELDS = ["run_id", "bundle_id", "bundle_name", "readiness", "publish_eligible", "reason_code", "reason_detail", "manual_action"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def issue_counts(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"critical": 0, "review": 0, "warning": 0}
    for i in issues:
        sev = clean(i.get("severity")).lower()
        if sev in out:
            out[sev] += 1
    return out


def main() -> None:
    current = read_json("hsd_current_run.json")
    run_id = current.get("run_id", "")
    guard = read_json("publish_guard_report.json")
    packs = read_csv("graphics_upload_pack_status.csv")
    ready_clean = [p for p in packs if p.get("upload_pack_status") == "ready"]
    ready_review = [p for p in packs if p.get("upload_pack_status") == "ready_with_review"]
    blocked = [p for p in packs if p.get("upload_pack_status") not in {"ready", "ready_with_review"}]
    issues = guard.get("issues", []) or []
    counts = issue_counts(issues)

    if counts["critical"]:
        overall = "NO-GO"
    elif ready_review:
        overall = "REVIEW_READY"
    elif ready_clean:
        overall = "READY_FOR_GRAPHICS"
    elif packs:
        overall = "NO_READY_PACK"
    else:
        overall = "NO-GO"

    rows: List[Dict[str, str]] = []
    for p in ready_clean:
        rows.append({
            "run_id": run_id,
            "bundle_id": p.get("bundle_id", ""),
            "bundle_name": p.get("bundle_name", ""),
            "readiness": p.get("upload_pack_status", ""),
            "publish_eligible": "Review" if not guard.get("publish_allowed") else "Yes",
            "reason_code": "ready_upload_pack",
            "reason_detail": p.get("zip_path", ""),
            "manual_action": "Send pack to graphics chat, generate slides, then run rendered-slide QA before posting.",
        })
    for p in ready_review:
        rows.append({
            "run_id": run_id,
            "bundle_id": p.get("bundle_id", ""),
            "bundle_name": p.get("bundle_name", ""),
            "readiness": p.get("upload_pack_status", ""),
            "publish_eligible": "Review",
            "reason_code": "ready_with_review_upload_pack",
            "reason_detail": p.get("zip_path", ""),
            "manual_action": "Open upload pack, visually verify public player images/crop rules, then send to graphics chat. Do not post until rendered-slide QA passes.",
        })
    for p in blocked:
        rows.append({
            "run_id": run_id,
            "bundle_id": p.get("bundle_id", ""),
            "bundle_name": p.get("bundle_name", ""),
            "readiness": p.get("upload_pack_status", ""),
            "publish_eligible": "No",
            "reason_code": "blocked_upload_pack",
            "reason_detail": p.get("missing_asset_names") or p.get("notes") or "blocked pack",
            "manual_action": "Resolve blocked pack reason before graphics handoff.",
        })
    if not rows:
        rows.append({
            "run_id": run_id,
            "bundle_id": "",
            "bundle_name": "Pipeline",
            "readiness": overall,
            "publish_eligible": "No",
            "reason_code": "no_ready_pack",
            "reason_detail": "No ready upload packs found.",
            "manual_action": "Check results_contract_report.md, studio_bundle_queue.csv, preview_bundle_quality.md, and graphics_upload_pack_status.csv.",
        })

    with Path("operator_status.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    status = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "overall": overall,
        "publish_allowed": bool(guard.get("publish_allowed")),
        "graphics_handoff_allowed": bool(guard.get("graphics_handoff_allowed")),
        "ready_upload_packs": len(ready_clean),
        "ready_with_review_upload_packs": len(ready_review),
        "blocked_upload_packs": len(blocked),
        "critical_issue_count": counts["critical"],
        "review_issue_count": counts["review"],
        "issues": issues,
        "manual_actions": [r["manual_action"] for r in rows],
    }
    Path("operator_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

    md = [
        "# HSD Operator Status",
        "",
        f"Generated: {status['generated_at_utc']}",
        f"Version: {VERSION}",
        "",
        f"## {overall}",
        "",
        f"- Graphics handoff allowed: {status['graphics_handoff_allowed']}",
        f"- Publish allowed: {status['publish_allowed']}",
        f"- Clean ready upload packs: {len(ready_clean)}",
        f"- Ready-with-review upload packs: {len(ready_review)}",
        f"- Blocked upload packs: {len(blocked)}",
        f"- Critical issues: {counts['critical']}",
        f"- Review issues: {counts['review']}",
        "",
        "## Manual actions",
        "",
    ]
    md += [f"- {r['bundle_name'] or 'Pipeline'}: {r['readiness']} — {r['manual_action']}" for r in rows]
    if issues:
        md += ["", "## Issues / review notes", ""]
        md += [f"- {clean(i.get('severity'))} | {clean(i.get('code'))} | {clean(i.get('headline')) or clean(i.get('detail'))}" for i in issues]
    Path("operator_status.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"overall": overall, "ready": len(ready_clean), "ready_with_review": len(ready_review)}, indent=2))


if __name__ == "__main__":
    main()
