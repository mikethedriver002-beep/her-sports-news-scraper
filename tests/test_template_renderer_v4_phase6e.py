from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_hsd_template_clean_plates_v4.py"
RENDERER = ROOT / "scripts" / "generate_hsd_template_renderer_v4.py"
RENDER_VALIDATOR = ROOT / "scripts" / "validate_hsd_template_renderer_v4.py"
NEAR_GATE = ROOT / "scripts" / "validate_hsd_near_post_ready_v4.py"
RECIPES = ROOT / "config" / "graphics" / "v4" / "clean_plates" / "clean_plate_recipes_v4.json"
FONT_CONTRACT = ROOT / "config" / "graphics" / "v4" / "approved" / "font_contract_v4.json"
FIDELITY = ROOT / "config" / "graphics" / "v4" / "fidelity" / "template_fidelity_matrix_v4.json"
WORKFLOW = ROOT / ".github" / "workflows" / "hsd-v4-phase6e-clean-plate-near-post-ready.yml"
DOC = ROOT / "docs" / "HSD_RENDERER_V4_CLEAN_PLATES_PHASE6E.md"


def test_phase6e_scripts_compile_and_versions_are_frozen() -> None:
    for path in [BUILDER, RENDERER, RENDER_VALIDATOR, NEAR_GATE]:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert "v1.0-phase6e-clean-plate-builder" in BUILDER.read_text(encoding="utf-8")
    assert "v4.5-phase6j-final-score-content-modules" in RENDERER.read_text(encoding="utf-8")
    assert "v1.4-phase6j-renderer-v4-validator" in RENDER_VALIDATOR.read_text(encoding="utf-8")
    assert "v1.1-phase6j-near-post-ready-gate" in NEAR_GATE.read_text(encoding="utf-8")


def test_phase6e_clean_plate_recipes_cover_four_required_templates() -> None:
    data = json.loads(RECIPES.read_text(encoding="utf-8"))
    templates = data["templates"]
    assert set(templates) == {
        "hsd_tonight_in_the_w_a",
        "hsd_game_recap_final_score_a",
        "hsd_game_recap_final_score_b",
        "hsd_game_recap_final_score_c_story",
    }
    for template_id, recipe in templates.items():
        assert recipe["source"].endswith(".png"), template_id
        assert len(recipe["regions"]) >= 5, template_id
        for region in recipe["regions"]:
            assert len(region["rect"]) == 4
            assert all(int(value) >= 0 for value in region["rect"])


def test_phase6e_renderer_uses_clean_plates_and_strict_player_fallbacks() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    assert "clean_plate_mode" in source
    assert "placeholder_layer_policy" in source
    assert "zero_allowed" in source
    assert "downgraded_to_final_a_missing_matching_player" in source
    assert "fixture_only_player_asset" in source
    assert "dynamic_mask_sha256" in source
    assert "approved_text_fallback" in source
    assert "content_module_status" in source
    assert "PRIMARY TEAM" in source  # token appears only in the blocklist, never as rendered copy
    assert '"PRIMARY TEAM"' in source


def test_phase6e_font_contract_selects_free_system_fonts_without_cutover() -> None:
    data = json.loads(FONT_CONTRACT.read_text(encoding="utf-8"))
    assert data["version"] == "hsd-font-contract-v4.2-phase6e"
    assert data["status"] == "selected_phase6e_system_fonts"
    assert data["renderer_cutover_allowed"] is False
    assert data["silent_fallback_allowed"] is False
    selected = data["selected_fonts"]
    assert selected["display_condensed_headline"]["family"] == "Noto Sans Display"
    assert selected["score_numeric"]["system_package"] == "fonts-noto-core"


def test_phase6e_fidelity_and_near_post_ready_remain_review_only() -> None:
    matrix = json.loads(FIDELITY.read_text(encoding="utf-8"))
    assert matrix["version"] == "hsd-template-fidelity-matrix-v4.2-phase6e-clean-plate"
    assert matrix["cutover_allowed"] is False
    assert matrix["policy"]["production_cutover_requires_human_approval"] is True
    gate = NEAR_GATE.read_text(encoding="utf-8")
    assert '"cutover_allowed": False' in gate
    assert '"human_visual_approval_required": True' in gate
    assert "fixture_only_player_variants_require_real_asset_before_approval" in gate


def test_phase6e_workflow_order_and_artifacts() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    required_steps = [
        "Run Phase 6A contract guard",
        "Build Phase 6E clean plates and masks",
        "Run Phase 6E Renderer v4.2 fixtures",
        "Run Phase 6C fidelity comparison",
        "Run Phase 6E near-post-ready gate",
        "Run Phase 6E tests",
    ]
    for step in required_steps:
        assert step in workflow
    positions = [workflow.index(step) for step in required_steps]
    assert positions == sorted(positions)
    assert "clean_plate_v4_report.json" in workflow
    assert "near_post_ready_v4_report.json" in workflow
    assert "assets/graphics/v4/approved/clean_plates/wnba/**" in workflow
    assert "assets/graphics/v4/approved/dynamic_masks/wnba/**" in workflow


def test_phase6e_runtime_reports_pass_after_workflow_setup() -> None:
    clean_report = ROOT / "clean_plate_v4_report.json"
    renderer_report = ROOT / "template_renderer_v4_validation_report.json"
    near_report = ROOT / "near_post_ready_v4_report.json"
    if not (clean_report.exists() and renderer_report.exists() and near_report.exists()):
        return
    assert json.loads(clean_report.read_text(encoding="utf-8"))["status"] == "passed_clean_plate_build"
    assert json.loads(renderer_report.read_text(encoding="utf-8"))["status"] == "passed_renderer_v4_validation"
    near = json.loads(near_report.read_text(encoding="utf-8"))
    assert near["status"] == "passed_near_post_ready_setup"
    assert near["near_post_ready_candidates"] >= 5
    assert near["cutover_allowed"] is False


def test_phase6e_is_free_only() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in [BUILDER, RENDERER, RENDER_VALIDATOR, NEAR_GATE, WORKFLOW])
    for token in ["openai", "anthropic", "serpapi", "rapidapi", "brightdata", "scrapingbee", "paid_api"]:
        assert token not in combined.lower()
    assert "free" in DOC.read_text(encoding="utf-8").lower()



def test_phase6e_hotfix_vertical_story_label_is_width_safe() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    assert "stroke=stroke" in source
    assert '"KEY PERFORMER", "context", 26, 14, DARK, 2, "center"' not in source
    assert '"KEY", "context", 24, 12, DARK, 1, "center"' in source
    assert '"PLAYER", "context", 22, 11, DARK, 1, "center"' in source
