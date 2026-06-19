from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts" / "validate_hsd_template_contract_v4.py"
REGISTRY = REPO / "config" / "graphics" / "v4" / "approved" / "template_registry_v4.json"
ROUTING = REPO / "config" / "graphics" / "v4" / "approved" / "routing_v4.json"
SCHEMA = REPO / "config" / "graphics" / "v4" / "approved" / "template_spec_schema_v4.json"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v4-phase6a-template-contract.yml"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_hsd_template_contract_v4", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase6a_schema_uses_json_schema_2020_12() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["badge"]["properties"]["asset"]["const"] == "official_hsd_badge_reference.png"


def test_phase6a_registry_freezes_seven_unique_templates() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    templates = registry["templates"]
    ids = [item["template_id"] for item in templates]
    assert registry["status"] == "canonical_contract_frozen"
    assert registry["renderer_cutover_allowed"] is False
    assert len(ids) == 7
    assert len(ids) == len(set(ids))


def test_phase6a_routing_preserves_registered_fallbacks() -> None:
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    routes = routing["routes"]
    final_asset = next(item for item in routes if item["use_case"] == "single_final_asset")
    preview_asset = next(item for item in routes if item["use_case"] == "preview_asset")
    assert len(routes) == 8
    assert final_asset["template_id"] == "hsd_game_recap_final_score_b"
    assert final_asset["fallback_template_id"] == "hsd_game_recap_final_score_a"
    assert preview_asset["fallback_code"] == "watch_point"


def test_phase6a_contract_validator_passes() -> None:
    module = load_validator()
    report = module.build_report(REPO)
    assert report["status"] == "passed_template_contract", report
    assert report["template_count"] == 7
    assert report["missing_assets"] == []
    assert report["invalid_zones"] == []
    assert report["duplicate_template_ids"] == []
    assert report["badge_hash_valid"] is True
    assert report["font_contract_status"] == "declared"


def test_phase6a_workflow_runs_strict_contract_and_uploads_reports() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "HSD V4 Phase 6A Template Contract" in workflow
    assert "python scripts/validate_hsd_template_contract_v4.py --strict" in workflow
    assert "pytest tests/test_template_contract_v4.py" in workflow
    assert "template_contract_v4_report.json" in workflow
    assert "template_contract_v4_report.md" in workflow
