from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "v1.4-phase6j-renderer-v4-validator"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
OUT_JSON = Path("template_renderer_v4_validation_report.json")
OUT_MD = Path("template_renderer_v4_validation_report.md")
EXPECTED: Dict[str, Tuple[int, int]] = {
    "hsd_tonight_in_the_w_a": (1080, 1350),
    "hsd_game_recap_final_score_a": (1080, 1350),
    "hsd_game_recap_final_score_b": (1080, 1350),
    "hsd_game_recap_final_score_c_story": (1080, 1920),
}


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    manifest = read_json(MANIFEST)
    blockers: List[str] = []
    warnings: List[str] = []
    items = manifest.get("items") if isinstance(manifest.get("items"), list) else []
    fixture_mode = bool(manifest.get("fixture_mode"))

    if not manifest:
        blockers.append("renderer_v4_manifest_missing")
    if manifest.get("version") not in {"v4.2-phase6e-clean-plate-near-post-ready", "v4.3-phase6h-targeted-fidelity-lift", "v4.4-phase6i-final-score-template-polish", "v4.5-phase6j-final-score-content-modules"}:
        blockers.append("renderer_v4_version_not_phase6e_or_later")
    if manifest.get("renderer_cutover_allowed") is not False:
        blockers.append("renderer_cutover_must_remain_blocked")
    if manifest.get("clean_plate_mode") is not True:
        blockers.append("clean_plate_mode_not_enabled")
    if manifest.get("near_post_ready_gate_required") is not True:
        blockers.append("near_post_ready_gate_not_required")
    if not items:
        blockers.append("no_renderer_v4_items")

    templates = {str(item.get("template_id") or "") for item in items}
    for template_id in EXPECTED:
        if template_id not in templates:
            blockers.append(f"missing_template:{template_id}")

    for item in items:
        template_id = str(item.get("template_id") or "")
        expected = EXPECTED.get(template_id)
        output = Path(str(item.get("output_path") or ""))
        plate = Path(str(item.get("clean_plate_path") or ""))
        mask = Path(str(item.get("dynamic_mask_path") or ""))
        if expected is None:
            blockers.append(f"unknown_template:{template_id}")
            continue
        if (int(item.get("width") or 0), int(item.get("height") or 0)) != expected:
            blockers.append(f"bad_dimensions:{template_id}:{item.get('width')}x{item.get('height')}")
        if not output.exists():
            blockers.append(f"missing_output:{output}")
        if not plate.exists():
            blockers.append(f"missing_clean_plate:{plate}")
        if not mask.exists():
            blockers.append(f"missing_dynamic_mask:{mask}")
        if str(item.get("review_only")) != "true":
            blockers.append(f"not_review_only:{template_id}")
        if int(item.get("placeholder_layer_count") or 0) != 0:
            blockers.append(f"placeholder_layer_present:{template_id}:{item.get('module_mode')}")
        if int(item.get("zone_overflow_count") or 0) != 0:
            blockers.append(f"zone_overflow:{template_id}:{item.get('module_mode')}")
        if int(item.get("team_logo_count") or 0) < 0:
            blockers.append(f"bad_logo_count:{template_id}")
        if not str(item.get("team_logo_modes") or ""):
            blockers.append(f"missing_logo_mode:{template_id}")
        if not str(item.get("clean_plate_sha256") or ""):
            blockers.append(f"missing_clean_plate_hash:{template_id}")
        if not str(item.get("dynamic_mask_sha256") or ""):
            blockers.append(f"missing_dynamic_mask_hash:{template_id}")
        if template_id == "hsd_game_recap_final_score_b":
            if int(item.get("player_assets_used") or 0) < 1:
                blockers.append("final_score_b_missing_player_asset")
            if str(item.get("fixture_only_player_asset")) == "true":
                if fixture_mode:
                    warnings.append("final_score_b_uses_fixture_only_reference_asset")
                else:
                    blockers.append("production_final_score_b_uses_fixture_asset")
        if template_id.startswith("hsd_game_recap_final_score"):
            if str(item.get("content_module_status") or "") != "passed_final_score_content_modules":
                blockers.append(f"final_score_content_module_not_passed:{template_id}:{item.get('module_mode')}")
            if not str(item.get("content_module_mode") or ""):
                blockers.append(f"final_score_content_module_mode_missing:{template_id}")
            if not str(item.get("content_module_title") or ""):
                blockers.append(f"final_score_content_module_title_missing:{template_id}")
            if not str(item.get("content_module_body") or ""):
                blockers.append(f"final_score_content_module_body_missing:{template_id}")
        if template_id == "hsd_game_recap_final_score_b" and int(item.get("content_module_stat_count") or 0) < 1:
            blockers.append("final_score_b_missing_verified_stat_module")
        if str(item.get("module_mode")) == "player" and int(item.get("player_assets_used") or 0) < 1:
            blockers.append("tonight_player_module_missing_player_asset")

    status = "passed_renderer_v4_validation" if not blockers else "blocked_renderer_v4_validation"
    report = {
        "version": VERSION,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "renderer_version": manifest.get("version"),
        "fixture_mode": fixture_mode,
        "rendered_count": len(items),
        "near_post_ready_candidates": sum(str(item.get("near_post_ready_candidate")) == "true" for item in items),
        "templates": sorted(template for template in templates if template),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Renderer v4 Phase 6J Validation",
        "",
        f"Status: `{report['status']}`",
        f"Rendered: `{report['rendered_count']}`",
        f"Near-post-ready candidates: `{report['near_post_ready_candidates']}`",
        f"Fixture mode: `{fixture_mode}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{blocker}`" for blocker in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{warning}`" for warning in report["warnings"]] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 2 if args.strict and blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
