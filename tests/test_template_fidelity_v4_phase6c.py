from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_hsd_template_fidelity_v4.py"
MATRIX = ROOT / "config" / "graphics" / "v4" / "fidelity" / "template_fidelity_matrix_v4.json"
WORKFLOW = ROOT / ".github" / "workflows" / "hsd-v4-phase6c-template-fidelity.yml"


def test_fidelity_script_compiles() -> None:
    ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))


def test_fidelity_matrix_has_phase6b_templates() -> None:
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    templates = data["templates"]
    required = {
        "hsd_tonight_in_the_w_a",
        "hsd_game_recap_final_score_a",
        "hsd_game_recap_final_score_b",
        "hsd_game_recap_final_score_c_story",
    }
    assert required <= set(templates)
    for template_id in required:
        row = templates[template_id]
        assert row["baseline"].endswith(".png")
        assert row["layout_reference"].endswith(".png")
        assert row["phase6b_required"] is True


def test_phase6c_workflow_runs_renderer_then_fidelity_gate() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Run Template Renderer v4 proof lane" in workflow
    assert "Run Phase 6C fidelity gate" in workflow
    assert "python scripts/generate_hsd_template_renderer_v4.py" in workflow
    assert "python scripts/validate_hsd_template_renderer_v4.py" in workflow
    assert "python scripts/validate_hsd_template_fidelity_v4.py --strict" in workflow
    assert workflow.index("Run Template Renderer v4 proof lane") < workflow.index("Run Phase 6C fidelity gate")


def test_fidelity_gate_does_not_cutover_production() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    script = SCRIPT.read_text(encoding="utf-8")
    assert matrix["cutover_allowed"] is False
    assert "cutover_allowed" in script
    assert "HSD_QUALITY_GRAPHICS" not in script
