from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_hsd_template_renderer_v4.py"
MATRIX = ROOT / "config" / "graphics" / "v4" / "fidelity" / "template_fidelity_matrix_v4.json"
DOC = ROOT / "docs" / "HSD_RENDERER_V4_VISUAL_CORRECTION_PHASE6D.md"
WORKFLOW = ROOT / ".github" / "workflows" / "hsd-v4-phase6d-visual-correction.yml"


def test_phase6d_generator_compiles_and_has_visual_correction_version() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    ast.parse(source, filename=str(GENERATOR))
    assert "v4.1-phase6d-visual-correction-template-skin" in source
    assert "template_skin_mode" in source


def test_phase6d_renderer_uses_approved_mockup_skin_not_blurred_invented_style() -> None:
    source = GENERATOR.read_text(encoding="utf-8")
    assert "approved public mockup as the template skin" in source
    assert "GaussianBlur(34)" not in source
    assert "for x in range(-h, w, 74)" not in source
    assert "diagonal" not in source.lower()


def test_phase6d_fidelity_matrix_is_stricter_but_still_review_only() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    thresholds = matrix["thresholds"]
    assert matrix["version"] == "hsd-template-fidelity-matrix-v4.1-phase6d"
    assert matrix["cutover_allowed"] is False
    assert thresholds["minimum_structure_score"] >= 0.60
    assert thresholds["minimum_tone_score"] >= 0.60
    assert thresholds["minimum_edge_similarity"] >= 0.45
    assert thresholds["production_cutover_minimum_overall_score"] >= 0.84


def test_phase6d_workflow_runs_renderer_fidelity_and_tests() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Run Phase 6A contract guard" in workflow
    assert "Run Phase 6D corrected Renderer v4 lane" in workflow
    assert "Run Phase 6D fidelity gate" in workflow
    assert "pytest tests/test_template_renderer_v4_phase6d.py" in workflow
    assert workflow.index("Run Phase 6D corrected Renderer v4 lane") < workflow.index("Run Phase 6D fidelity gate")


def test_phase6d_documentation_states_no_cutover() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "No `HSD_QUALITY_GRAPHICS` cutover" in text
    assert "Production cutover remains blocked" in text
