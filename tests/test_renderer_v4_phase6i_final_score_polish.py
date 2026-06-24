from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_renderer_version_is_phase6i():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6i")
    assert module.VERSION == "v4.5-phase6j-final-score-content-modules"


def test_renderer_manifest_fields_include_final_score_polish():
    module = load_module(ROOT / "scripts" / "generate_hsd_template_renderer_v4.py", "renderer_v4_phase6i_fields")
    assert "final_score_polish_status" in module.MANIFEST_FIELDS
    assert "final_score_polish_score" in module.MANIFEST_FIELDS
    assert "final_score_polish_reasons" in module.MANIFEST_FIELDS


def test_live_policy_enables_final_score_polish_release_review():
    data = json.loads((ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_v4.json").read_text())
    assert data["version"] == "v1.3-phase6j-final-score-content-module-policy"
    assert data["minimum_final_score_polish_score"] == 0.92
    assert data["phase6j_final_score_content_modules_release_review"] is True
    assert data["production_cutover_allowed"] is False
    assert data["auto_publish_allowed"] is False


def test_validator_exposes_final_score_polish_fields():
    module = load_module(ROOT / "scripts" / "validate_hsd_live_post_ready_v4.py", "live_gate_v4_phase6i")
    assert module.VERSION == "v1.3-phase6j-final-score-content-module-live-gate"
    assert "final_score_polish_status" in module.FIELDS
    assert "final_score_polish_score" in module.FIELDS
    assert "final_score_polish_reasons" in module.FIELDS
    assert "content_module_status" in module.FIELDS
