from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping

POLICY = Path("config/graphics/v5/phase8a/asset_registry_policy_v1.json")
REGISTRY = Path("data/asset_registry/wnba/team_logos.csv")
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
OUT_JSON = Path("phase8a_asset_registry_report.json")
OUT_MD = Path("phase8a_asset_registry_report.md")


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def build_report(mode: str) -> Dict[str, Any]:
    policy = read_json(POLICY)
    required = set(policy.get("required_wnba_team_ids") or [])
    rows = read_csv(REGISTRY)
    by_team = {clean(row.get("team_id")): row for row in rows}
    blockers: List[str] = []
    warnings: List[str] = []
    missing = sorted(required - set(by_team))
    for team_id in missing:
        blockers.append(f"missing_required_team_logo_row:{team_id}")
    exact_ready = []
    for team_id in sorted(required & set(by_team)):
        row = by_team[team_id]
        if clean(row.get("approved")).lower() != "true":
            blockers.append(f"unapproved_team_logo:{team_id}")
        if clean(row.get("file_exists")).lower() != "true" and not Path(clean(row.get("file_path"))).exists():
            blockers.append(f"team_logo_file_missing:{team_id}")
        else:
            exact_ready.append(team_id)
    manifest = read_json(MANIFEST)
    fallback_rows = []
    for item in manifest.get("items") or []:
        if not isinstance(item, dict):
            continue
        if int(item.get("team_fallback_badge_count") or 0) > 0 and clean(item.get("near_post_ready_candidate")) == "true":
            fallback_rows.append(clean(item.get("item_id") or item.get("headline")))
    if fallback_rows:
        warnings.append("release_rows_have_fallback_badges_require_human_hold")
    status = "passed_phase8a_asset_registry" if not blockers else "blocked_phase8a_asset_registry"
    return {"version": "v1.0-phase8a-asset-registry-gate", "mode": mode, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": status, "strict_exit_code": 0 if not blockers else 2, "required_team_count": len(required), "exact_ready_count": len(exact_ready), "missing_count": len(missing), "fallback_release_candidate_count": len(fallback_rows), "blockers": sorted(set(blockers)), "warnings": sorted(set(warnings)), "fallback_rows": fallback_rows[:50]}


def write_report(report: Mapping[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# HSD Phase 8A Asset Registry Gate", "", f"Status: `{report.get('status')}`", f"Exact ready: `{report.get('exact_ready_count')}/{report.get('required_team_count')}`", f"Fallback release candidates: `{report.get('fallback_release_candidate_count')}`", "", "## Blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings") or []] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.mode)
    write_report(report)
    print(json.dumps({key: report[key] for key in ["version", "mode", "status", "exact_ready_count", "required_team_count", "fallback_release_candidate_count", "blockers", "warnings"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0

if __name__ == "__main__":
    raise SystemExit(main())
