from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts" / "validate_hsd_template_contract_v4.py"
REGISTRY = REPO / "config" / "graphics" / "v4" / "approved" / "template_registry_v4.json"
MATRIX = REPO / "config" / "graphics" / "v4" / "approved" / "variant_matrix_v4.json"
FONT_CONTRACT = REPO / "config" / "graphics" / "v4" / "approved" / "font_contract_v4.json"
SOURCE_PACK = REPO / "assets" / "graphics" / "v4" / "approved" / "hsd_wnba_canonical_templates_v4.zip"
PHASE6A_WORKFLOW = REPO / ".github" / "workflows" / "hsd-v4-phase6a-template-contract.yml"
SANITY_WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"

EXPECTED_IDS = {
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_b",
    "hsd_game_recap_final_score_c_story",
    "hsd_tonight_in_the_w_a",
    "hsd_last_night_in_the_w_variant_a_multi_game_feed",
    "hsd_last_night_in_the_w_variant_b_story_rolling_recap",
    "hsd_last_night_in_the_w_variant_c_carousel_cover_recap_package",
}


def load_module():
    spec = importlib.util.spec_from_file_location("validate_hsd_template_contract_v4", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_phase6a_required_contract_files_exist() -> None:
    required = [REGISTRY, MATRIX, FONT_CONTRACT, SOURCE_PACK, PHASE6A_WORKFLOW, VALIDATOR]
    for path in required:
        assert path.exists(), path


def test_registry_contains_exact_canonical_template_set() -> None:
    registry = read_json(REGISTRY)
    templates = registry["templates"]
    assert registry["status"] == "canonical_frozen"
    assert registry["template_count"] == 7
    assert {item["template_id"] for item in templates} == EXPECTED_IDS
    assert all(item["review_only"] is True for item in templates)
    assert all(item["renderer_v4_cutover_allowed"] is False for item in templates)


def test_variant_matrix_locks_player_fallbacks_and_exact_routes() -> None:
    matrix = read_json(MATRIX)
    routes = matrix["routes"]
    assert matrix["status"] == "canonical_frozen"
    assert matrix["global_rules"]["registered_templates_only"] is True
    assert matrix["global_rules"]["invented_layouts_allowed"] is False
    assert {item["template_id"] for item in routes} == EXPECTED_IDS
    final_b = next(item for item in routes if item["template_id"] == "hsd_game_recap_final_score_b")
    assert final_b["fallback"] == "hsd_game_recap_final_score_a"
    preview_player = next(item for item in routes if item["template_id"] == "hsd_tonight_in_the_w_a" and item["player_asset_state"] == "approved")
    assert preview_player["active_module"] == "APPROVED PLAYER PHOTO SLOT"


def test_font_contract_is_free_declared_and_blocks_cutover() -> None:
    contract = read_json(FONT_CONTRACT)
    assert contract["status"] == "declared_reference_match_required"
    assert contract["silent_fallback_allowed"] is False
    assert contract["renderer_cutover_allowed"] is False
    assert contract["selected_fonts"] == {}
    assert "free/open" in contract["license_policy"]


def test_strict_validator_passes_with_exact_uploaded_source_pack() -> None:
    module = load_module()
    report = module.build_report(REPO)
    assert report["status"] == "passed_template_contract", report
    assert report["blockers"] == []
    assert report["template_count"] == 7
    assert report["source_pack_hash_valid"] is True
    assert report["badge_hash_valid"] is True
    assert report["badge_dimensions_valid"] is True
    assert report["duplicate_template_ids"] == []
    assert report["missing_assets"] == []
    assert report["invalid_zones"] == []
    assert report["spec_hash_mismatches"] == []
    assert report["reference_hash_mismatches"] == []
    assert report["reference_dimension_mismatches"] == []
    assert all(item["spec_semantic_match"] is True for item in report["templates"])


def test_phase6a_is_standalone_and_does_not_cut_over_production_renderer() -> None:
    phase6a = PHASE6A_WORKFLOW.read_text(encoding="utf-8")
    sanity = SANITY_WORKFLOW.read_text(encoding="utf-8")
    assert "python scripts/validate_hsd_template_contract_v4.py --strict" in phase6a
    assert "pytest tests/test_template_contract_v4.py" in phase6a
    assert "hsd-v4-phase6a-template-contract-${{ github.run_number }}" in phase6a
    assert "hsd_wnba_canonical_templates_v4.zip" in phase6a
    assert "run_hsd_template_renderer_v3.py" in sanity
    assert "template_renderer_v4" not in sanity
