from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_hsd_template_renderer_v4_phase6k as phase6k
from hsd_asset_assurance_core import clean

VERSION = "v1.7-phase6m-render-safe-renderer-validator"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
OUT_JSON = Path("template_renderer_v4_validation_report.json")
OUT_MD = Path("template_renderer_v4_validation_report.md")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _final_b_intentional_asset_downgrade(manifest: Dict[str, Any]) -> bool:
    return phase6k.intentional_final_b_downgrade(manifest)


def validate(manifest: Dict[str, Any]) -> Dict[str, Any]:
    base_report = phase6k.validate(manifest)
    items = [dict(item) for item in manifest.get("items") or [] if isinstance(item, dict)]
    assurance_safe = all(clean(item.get("asset_render_safe")) == "true" for item in items) if items else False
    final_b_asset_downgrade = _final_b_intentional_asset_downgrade(manifest)

    # Phase 6K's exact-logo blockers are replaced by Phase 6M's stronger
    # render-safe contract. We only suppress them when every item passed the
    # assurance core; unsafe rows are separately hard-blocked below.
    filtered: List[str] = []
    for blocker in base_report.get("blockers") or []:
        if assurance_safe and (
            blocker.startswith("insufficient_team_logos:")
            or blocker.startswith("unapproved_team_logo_mode:")
        ):
            continue
        if blocker == "fixture_audit_missing_template:hsd_game_recap_final_score_b" and final_b_asset_downgrade:
            continue
        if blocker == "missing_template_without_recorded_downgrade:hsd_game_recap_final_score_b" and final_b_asset_downgrade:
            continue
        filtered.append(blocker)

    blockers = list(filtered)
    warnings = list(base_report.get("warnings") or [])
    if final_b_asset_downgrade:
        warnings.append("final_score_b_downgraded_no_approved_player_asset")
    if not manifest:
        blockers.append("renderer_manifest_missing")
    if manifest.get("phase6m_asset_assurance") is not True:
        blockers.append("phase6m_asset_assurance_flag_missing")
    if clean(manifest.get("phase6m_effective_renderer_version")) != "v4.8-phase6m-asset-assurance-core":
        blockers.append("phase6m_effective_renderer_version_missing")
    if int(manifest.get("phase6m_input_rows_skipped_for_assets") or 0) != 0:
        blockers.append("phase6m_asset_rows_were_skipped")
    if not items:
        blockers.append("no_renderer_v4_items")

    for item in items:
        ident = ":".join([
            clean(item.get("template_id")),
            clean(item.get("platform")),
            clean(item.get("module_mode")),
            clean(item.get("headline")),
        ])
        if clean(item.get("asset_assurance_status")) != "passed_render_safe":
            blockers.append(f"asset_assurance_not_render_safe:{ident}")
        if clean(item.get("asset_render_safe")) != "true":
            blockers.append(f"asset_render_safe_false:{ident}")
        if int(item.get("team_asset_count") or 0) < 2:
            blockers.append(f"insufficient_render_safe_team_assets:{ident}")
        if clean(item.get("fixture_only_player_asset")).lower() == "true":
            blockers.append(f"fixture_player_asset_escaped_phase6m:{ident}")
        if clean(item.get("requested_module_mode")).lower() == "player":
            mode = clean(item.get("asset_assurance_player_mode"))
            if mode not in {"approved_player_asset", "team_spotlight_fallback"}:
                blockers.append(f"player_request_has_no_safe_route:{ident}")
        if clean(item.get("asset_assurance_player_mode")) == "fixture_reference_asset":
            blockers.append(f"fixture_reference_player_not_downgraded:{ident}")
        if clean(item.get("asset_release_lane")) in {"hsd_badge_review", "team_spotlight_review"}:
            warnings.append(f"asset_fallback_requires_human_review:{ident}")

    status = "passed_renderer_v4_validation" if not blockers else "blocked_renderer_v4_validation"
    report = {
        **base_report,
        "version": VERSION,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "renderer_version": manifest.get("version"),
        "phase6m_effective_renderer_version": manifest.get("phase6m_effective_renderer_version"),
        "rendered_count": len(items),
        "asset_render_safe_count": sum(clean(item.get("asset_render_safe")) == "true" for item in items),
        "asset_exact_rows": sum(clean(item.get("asset_release_lane")) == "exact_assets" for item in items),
        "asset_hsd_badge_review_rows": sum(clean(item.get("asset_release_lane")) == "hsd_badge_review" for item in items),
        "asset_team_spotlight_rows": sum(clean(item.get("asset_release_lane")) == "team_spotlight_review" for item in items),
        "final_score_b_asset_downgrade": final_b_asset_downgrade,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
    }
    return report


def write_report(report: Dict[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Renderer v4 Phase 6M Validation",
        "",
        f"Status: `{report['status']}`",
        f"Rendered: `{report['rendered_count']}`",
        f"Render-safe: `{report['asset_render_safe_count']}`",
        f"Exact-asset rows: `{report['asset_exact_rows']}`",
        f"HSD badge review rows: `{report['asset_hsd_badge_review_rows']}`",
        f"Team spotlight rows: `{report['asset_team_spotlight_rows']}`",
        f"Final Score B asset downgrade: `{report['final_score_b_asset_downgrade']}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings") or []] or ["- None"]
    lines += [
        "",
        "Phase 6M permits clearly-labelled render-safe fallbacks while preserving human approval and live handoff gates.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = validate(read_json(MANIFEST))
    write_report(report)
    print(json.dumps({key: report[key] for key in ["version", "status", "rendered_count", "asset_render_safe_count", "asset_hsd_badge_review_rows", "asset_team_spotlight_rows", "blockers", "warnings"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
