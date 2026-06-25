from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts/validate_hsd_template_contract_v4.py"
APPROVED = REPO / "config/graphics/v4/approved"
WORKFLOW = REPO / ".github/workflows/hsd-v4-phase6a-template-contract.yml"
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_phase6a_contract_passes_strict_validation() -> None:
    module = load_module()
    report = module.build_report()
    assert report["status"] == "passed_template_contract"
    assert report["strict_exit_code"] == 0
    assert report["template_count"] == 7
    assert set(report["template_ids"]) == EXPECTED_IDS
    assert report["badge_hash_valid"] is True
    assert report["font_contract_status"] == "selected"
    assert report["blockers"] == []
    assert report["missing_assets"] == []
    assert report["hash_mismatches"] == []
    assert report["dimension_mismatches"] == []
    assert report["invalid_zones"] == []


def test_registry_specs_and_reference_assets_are_hash_locked() -> None:
    registry = json.loads((APPROVED / "template_registry_v4.json").read_text(encoding="utf-8"))
    assert registry["status"] == "canonical_frozen"
    assert registry["renderer_cutover_allowed"] is False
    assert len(registry["templates"]) == 7
    for row in registry["templates"]:
        for path_key, hash_key in [
            ("spec_path", "spec_sha256"),
            ("public_mockup_path", "public_mockup_sha256"),
            ("layout_reference_path", "layout_reference_sha256"),
            ("badge_path", "badge_sha256"),
        ]:
            path = REPO / row[path_key]
            assert path.exists(), path
            assert sha256(path) == row[hash_key], path


def test_official_hsd_badge_uses_transparent_background() -> None:
    manifest = json.loads((APPROVED / "source_manifest_v4.json").read_text(encoding="utf-8"))
    badge = manifest["badge"]
    path = REPO / badge["path"]
    image = Image.open(path).convert("RGBA")

    assert image.size == tuple(badge["dimensions"])
    assert image.getpixel((0, 0))[3] == 0
    assert image.getbbox() is not None


def test_routing_matrix_covers_every_canonical_template() -> None:
    matrix = json.loads((APPROVED / "variant_matrix_v4.json").read_text(encoding="utf-8"))
    registry = json.loads((APPROVED / "template_registry_v4.json").read_text(encoding="utf-8"))
    routed = {row["template_id"] for row in matrix["routes"]}
    registered = {row["template_id"] for row in registry["templates"]}
    assert routed == registered
    assert matrix["global_rules"]["registered_templates_only"] is True
    assert matrix["global_rules"]["invented_layouts_allowed"] is False


def test_font_contract_blocks_silent_fallback_and_cutover() -> None:
    contract = json.loads((APPROVED / "font_contract_v4.json").read_text(encoding="utf-8"))
    assert contract["silent_fallback_allowed"] is False
    assert contract["renderer_cutover_allowed"] is False
    assert contract["status"] == "selected_phase6e_system_fonts"
    assert contract["selected_fonts"]["display_condensed_headline"]["system_package"] == "fonts-noto-core"
    assert "Bebas Neue" in contract["roles"]["display_condensed_headline"]["candidate_families"]


def test_phase6a_workflow_runs_strict_contract_and_uploads_reports() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Run Phase 6A canonical template contract" in workflow
    assert "python scripts/validate_hsd_template_contract_v4.py --strict" in workflow
    assert "pytest tests/test_template_contract_v4.py" in workflow
    assert "outputs/latest/HSD_TEMPLATE_CONTRACT/template_contract_v4_report.json" in workflow
    assert "config/graphics/v4/approved/wnba/*.json" in workflow
