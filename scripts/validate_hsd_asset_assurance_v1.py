from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hsd_asset_assurance_core import clean

VERSION = "v1.0-phase6m-asset-assurance-gate"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
PREFLIGHT = Path("asset_assurance_preflight_v1_report.json")
OUT_JSON = Path("asset_assurance_v1_report.json")
OUT_MD = Path("asset_assurance_v1_report.md")
OUT_CSV = Path("outputs/latest/HSD_ASSET_ASSURANCE/asset_assurance_v1_rows.csv")
FIELDS = [
    "item_id",
    "source_id",
    "template_id",
    "platform",
    "module_mode",
    "requested_module_mode",
    "headline",
    "asset_assurance_status",
    "asset_assurance_reasons",
    "asset_render_safe",
    "asset_live_candidate_eligible",
    "asset_live_ready_pre_human",
    "asset_requires_visual_approval",
    "asset_release_lane",
    "team_asset_count",
    "team_exact_logo_count",
    "team_fallback_badge_count",
    "asset_assurance_player_mode",
    "asset_assurance_player_route",
    "validation_status",
    "validation_reasons",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def evaluate(root: Path) -> Dict[str, Any]:
    manifest = read_json(root / MANIFEST)
    preflight = read_json(root / PREFLIGHT)
    blockers: List[str] = []
    warnings: List[str] = []
    if not manifest:
        blockers.append("renderer_manifest_missing")
    if not preflight:
        blockers.append("asset_assurance_preflight_missing")
    elif clean(preflight.get("status")) != "passed_asset_assurance_preflight":
        blockers.append("asset_assurance_preflight_not_passed")
    if manifest.get("phase6m_asset_assurance") is not True:
        blockers.append("phase6m_manifest_flag_missing")
    if int(manifest.get("phase6m_input_rows_skipped_for_assets") or 0) != 0:
        blockers.append("asset_input_rows_skipped")

    rows: List[Dict[str, Any]] = []
    for raw in manifest.get("items") or []:
        item = dict(raw)
        reasons: List[str] = []
        if clean(item.get("asset_assurance_status")) != "passed_render_safe":
            reasons.append("asset_assurance_status_not_passed")
        if clean(item.get("asset_render_safe")) != "true":
            reasons.append("asset_render_safe_false")
        if clean(item.get("asset_live_candidate_eligible")) != "true":
            if clean(item.get("fixture_only_player_asset")) != "true":
                reasons.append("asset_not_live_candidate_eligible")
        if int(item.get("team_asset_count") or 0) < 2:
            reasons.append("team_asset_count_below_two")
        if clean(item.get("requested_module_mode")).lower() == "player":
            if clean(item.get("asset_assurance_player_mode")) not in {"approved_player_asset", "fixture_reference_asset", "team_spotlight_fallback"}:
                reasons.append("player_request_without_safe_resolution")
        lane = clean(item.get("asset_release_lane"))
        if lane in {"hsd_badge_review", "team_spotlight_review"}:
            warnings.append(f"human_asset_review_required:{clean(item.get('item_id'))}:{lane}")
        item["validation_status"] = "passed_asset_assurance" if not reasons else "blocked_asset_assurance"
        item["validation_reasons"] = ";".join(sorted(set(reasons)))
        rows.append(item)
        if reasons:
            blockers.append(f"asset_assurance_failures_present:{clean(item.get('item_id'))}")

    if not rows:
        blockers.append("no_renderer_rows")
    status = "passed_asset_assurance" if not blockers else "blocked_asset_assurance"
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "rendered_rows": len(rows),
        "render_safe_rows": sum(row["validation_status"] == "passed_asset_assurance" for row in rows),
        "exact_asset_rows": sum(clean(row.get("asset_release_lane")) == "exact_assets" for row in rows),
        "hsd_badge_review_rows": sum(clean(row.get("asset_release_lane")) == "hsd_badge_review" for row in rows),
        "team_spotlight_rows": sum(clean(row.get("asset_release_lane")) == "team_spotlight_review" for row in rows),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "human_visual_approval_required": True,
        "rows": rows,
    }


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / OUT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(root / OUT_CSV, report.get("rows") or [])
    lines = [
        "# HSD Phase 6M Asset Assurance Gate",
        "",
        f"Status: `{report['status']}`",
        f"Rendered rows: `{report['rendered_rows']}`",
        f"Render-safe rows: `{report['render_safe_rows']}`",
        f"Exact-asset rows: `{report['exact_asset_rows']}`",
        f"HSD badge review rows: `{report['hsd_badge_review_rows']}`",
        f"Team spotlight rows: `{report['team_spotlight_rows']}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings") or []] or ["- None"]
    (root / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = evaluate(root)
    write_report(root, report)
    print(json.dumps({key: report[key] for key in ["version", "status", "rendered_rows", "render_safe_rows", "exact_asset_rows", "hsd_badge_review_rows", "team_spotlight_rows", "blockers", "warnings"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
