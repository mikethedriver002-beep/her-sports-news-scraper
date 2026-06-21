from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "v1.5-phase6k-renderer-v4-validator"
RENDERER_VERSION = "v4.6-phase6k-story-context-cta-polish"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
OUT_JSON = Path("template_renderer_v4_validation_report.json")
OUT_MD = Path("template_renderer_v4_validation_report.md")
EXPECTED: Dict[str, Tuple[int, int]] = {
    "hsd_tonight_in_the_w_a": (1080, 1350),
    "hsd_game_recap_final_score_a": (1080, 1350),
    "hsd_game_recap_final_score_b": (1080, 1350),
    "hsd_game_recap_final_score_c_story": (1080, 1920),
}
ALWAYS_REQUIRED = {
    "hsd_tonight_in_the_w_a",
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_c_story",
}


def clean(value: Any) -> str:
    return str(value or "").strip()


def as_int(value: Any) -> int:
    try:
        return int(float(clean(value) or "0"))
    except Exception:
        return 0


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def route_key(row: Dict[str, Any]) -> str:
    return clean(row.get("source_id") or row.get("headline"))


def final_a_route_keys(manifest: Dict[str, Any]) -> set[str]:
    return {
        route_key(item)
        for item in (manifest.get("items") or [])
        if isinstance(item, dict)
        and clean(item.get("template_id")) == "hsd_game_recap_final_score_a"
        and route_key(item)
    }


def final_b_routing_rows(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = manifest.get("final_score_b_routing")
    if not isinstance(raw, list) or not raw or any(not isinstance(row, dict) for row in raw):
        return []
    return list(raw)


def final_b_routing_coverage_ok(manifest: Dict[str, Any]) -> bool:
    rows = final_b_routing_rows(manifest)
    expected = final_a_route_keys(manifest)
    route_keys = [route_key(row) for row in rows]
    if not rows or not expected or any(not key for key in route_keys):
        return False
    return len(route_keys) == len(set(route_keys)) and set(route_keys) == expected


def intentional_final_b_downgrade(manifest: Dict[str, Any]) -> bool:
    rows = final_b_routing_rows(manifest)
    return final_b_routing_coverage_ok(manifest) and all(
        not bool(row.get("rendered"))
        and clean(row.get("route_decision")).startswith("downgraded_to_final_a_")
        for row in rows
    )


def validate(manifest: Dict[str, Any]) -> Dict[str, Any]:
    blockers: List[str] = []
    warnings: List[str] = []
    items = manifest.get("items") if isinstance(manifest.get("items"), list) else []
    fixture_mode = bool(manifest.get("fixture_mode"))

    if not manifest:
        blockers.append("renderer_v4_manifest_missing")
    if manifest.get("version") != RENDERER_VERSION:
        blockers.append("renderer_v4_version_not_phase6k_v4_6")
    if manifest.get("renderer_cutover_allowed") is not False:
        blockers.append("renderer_cutover_must_remain_blocked")
    if manifest.get("clean_plate_mode") is not True:
        blockers.append("clean_plate_mode_not_enabled")
    if manifest.get("near_post_ready_gate_required") is not True:
        blockers.append("near_post_ready_gate_not_required")
    if not items:
        blockers.append("no_renderer_v4_items")
    if manifest.get("phase6k_story_context_cta") is not True:
        blockers.append("phase6k_story_context_cta_manifest_flag_missing")
    if manifest.get("rendered_copy_metadata_required") is not True:
        blockers.append("rendered_copy_metadata_requirement_missing")
    if as_int(manifest.get("rendered_copy_placeholder_rows")) != 0:
        blockers.append("rendered_copy_placeholder_rows_present")

    templates = {clean(item.get("template_id")) for item in items}
    for template_id in ALWAYS_REQUIRED:
        if template_id not in templates:
            blockers.append(f"missing_template:{template_id}")

    final_b_present = "hsd_game_recap_final_score_b" in templates
    routing_rows = final_b_routing_rows(manifest)
    routing_coverage_ok = final_b_routing_coverage_ok(manifest)
    intentional_b = intentional_final_b_downgrade(manifest)
    if final_a_route_keys(manifest) and not routing_coverage_ok:
        blockers.append("final_score_b_routing_coverage_mismatch")
    for route in routing_rows:
        if bool(route.get("rendered")):
            continue
        if not clean(route.get("route_decision")).startswith("downgraded_to_final_a_"):
            blockers.append("final_score_b_invalid_nonrender_route")
    if not final_b_present:
        if fixture_mode:
            blockers.append("fixture_audit_missing_template:hsd_game_recap_final_score_b")
        elif intentional_b:
            warnings.append("final_score_b_intentionally_downgraded_no_verified_player_package")
        else:
            blockers.append("missing_template_without_recorded_downgrade:hsd_game_recap_final_score_b")

    for item in items:
        template_id = clean(item.get("template_id"))
        expected = EXPECTED.get(template_id)
        output = Path(clean(item.get("output_path")))
        plate = Path(clean(item.get("clean_plate_path")))
        mask = Path(clean(item.get("dynamic_mask_path")))
        if expected is None:
            blockers.append(f"unknown_template:{template_id}")
            continue
        if (as_int(item.get("width")), as_int(item.get("height"))) != expected:
            blockers.append(f"bad_dimensions:{template_id}:{item.get('width')}x{item.get('height')}")
        if not output.exists():
            blockers.append(f"missing_output:{output}")
        if not plate.exists():
            blockers.append(f"missing_clean_plate:{plate}")
        if not mask.exists():
            blockers.append(f"missing_dynamic_mask:{mask}")
        if clean(item.get("review_only")) != "true":
            blockers.append(f"not_review_only:{template_id}")
        if as_int(item.get("placeholder_layer_count")) != 0:
            blockers.append(f"placeholder_layer_present:{template_id}:{item.get('module_mode')}")
        if as_int(item.get("context_placeholder_count")) != 0:
            blockers.append(f"rendered_context_placeholder_present:{template_id}:{item.get('module_mode')}")
        if as_int(item.get("rendered_copy_placeholder_count")) != 0:
            blockers.append(f"rendered_copy_placeholder_present:{template_id}:{item.get('module_mode')}")
        if not clean(item.get("rendered_copy")):
            blockers.append(f"rendered_copy_metadata_missing:{template_id}:{item.get('module_mode')}")
        if not clean(item.get("context_segments")):
            blockers.append(f"context_segments_metadata_missing:{template_id}:{item.get('module_mode')}")
        if as_int(item.get("zone_overflow_count")) != 0:
            blockers.append(f"zone_overflow:{template_id}:{item.get('module_mode')}")
        logo_count = as_int(item.get("team_logo_count"))
        logo_modes = [value.strip() for value in clean(item.get("team_logo_modes")).split(";") if value.strip()]
        if logo_count < 2 or len(logo_modes) < 2:
            blockers.append(f"insufficient_team_logos:{template_id}:{item.get('module_mode')}")
        if not logo_modes:
            blockers.append(f"missing_logo_mode:{template_id}")
        elif any(value != "approved_logo" for value in logo_modes):
            blockers.append(f"unapproved_team_logo_mode:{template_id}:{item.get('module_mode')}")
        if not clean(item.get("clean_plate_sha256")):
            blockers.append(f"missing_clean_plate_hash:{template_id}")
        if not clean(item.get("dynamic_mask_sha256")):
            blockers.append(f"missing_dynamic_mask_hash:{template_id}")

        if template_id == "hsd_tonight_in_the_w_a":
            if clean(item.get("context_time_status")) not in {"verified", "omitted_missing"}:
                blockers.append("tonight_time_status_invalid")
            if clean(item.get("context_network_status")) not in {"verified", "omitted_missing"}:
                blockers.append("tonight_network_status_invalid")

        if template_id == "hsd_game_recap_final_score_b":
            if as_int(item.get("player_assets_used")) < 1:
                blockers.append("final_score_b_missing_player_asset")
            if clean(item.get("fixture_only_player_asset")) == "true":
                if fixture_mode:
                    warnings.append("final_score_b_uses_fixture_only_reference_asset")
                else:
                    blockers.append("production_final_score_b_uses_fixture_asset")
            if as_int(item.get("content_module_stat_count")) < 1:
                blockers.append("final_score_b_missing_verified_stat_module")

        if template_id.startswith("hsd_game_recap_final_score"):
            if clean(item.get("content_module_status")) != "passed_final_score_content_modules":
                blockers.append(f"final_score_content_module_not_passed:{template_id}:{item.get('module_mode')}")
            if not clean(item.get("content_module_mode")):
                blockers.append(f"final_score_content_module_mode_missing:{template_id}")
            if not clean(item.get("content_module_title")):
                blockers.append(f"final_score_content_module_title_missing:{template_id}")
            if not clean(item.get("content_module_body")):
                blockers.append(f"final_score_content_module_body_missing:{template_id}")

        if template_id == "hsd_game_recap_final_score_c_story":
            if as_int(item.get("context_placeholder_count")) != 0:
                blockers.append("story_context_placeholder_present")
            if clean(item.get("context_location_status")) not in {"verified", "omitted_missing"}:
                blockers.append("story_context_location_status_invalid")
            if clean(item.get("story_cta_status")) != "passed_story_context_cta":
                blockers.append("story_cta_not_passed")
            if not clean(item.get("story_prompt")):
                blockers.append("story_prompt_missing")
            winner_token = clean(item.get("story_winner_short_name")).upper()
            if not winner_token or winner_token not in clean(item.get("story_prompt")).upper():
                blockers.append("story_prompt_not_matchup_specific")
            if not clean(item.get("story_cta_label")) or not clean(item.get("story_cta_body")):
                blockers.append("story_cta_copy_missing")

        if clean(item.get("module_mode")) == "player" and as_int(item.get("player_assets_used")) < 1:
            blockers.append("tonight_player_module_missing_player_asset")

    status = "passed_renderer_v4_validation" if not blockers else "blocked_renderer_v4_validation"
    return {
        "version": VERSION,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "renderer_version": manifest.get("version"),
        "fixture_mode": fixture_mode,
        "rendered_count": len(items),
        "near_post_ready_candidates": sum(clean(item.get("near_post_ready_candidate")) == "true" for item in items),
        "templates": sorted(template for template in templates if template),
        "final_score_b_present": final_b_present,
        "final_score_b_routing_rows": len(routing_rows),
        "final_score_b_routing_coverage_ok": routing_coverage_ok,
        "final_score_b_intentional_downgrade": intentional_b,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = validate(read_json(MANIFEST))
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Renderer v4 Phase 6K Validation",
        "",
        f"Status: `{report['status']}`",
        f"Rendered: `{report['rendered_count']}`",
        f"Near-post-ready candidates: `{report['near_post_ready_candidates']}`",
        f"Fixture mode: `{report['fixture_mode']}`",
        f"Final Score B present: `{report['final_score_b_present']}`",
        f"Final Score B routing rows: `{report['final_score_b_routing_rows']}`",
        f"Final Score B routing coverage: `{report['final_score_b_routing_coverage_ok']}`",
        f"Final Score B intentional downgrade: `{report['final_score_b_intentional_downgrade']}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report["warnings"]] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
