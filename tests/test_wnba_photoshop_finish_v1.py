from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_photoshop_finish_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_photoshop_finish_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_photoshop_jsx_limits_work_to_jackie_and_aja(tmp_path: Path) -> None:
    module = load_module()
    rows = [
        {
            "variant_id": "jackie_final_cover",
            "base_render_path": (tmp_path / "jackie.png").as_posix(),
            "photoshop_render_path": (tmp_path / "jackie_ps.png").as_posix(),
        },
        {
            "variant_id": "aja_control_line",
            "base_render_path": (tmp_path / "aja.png").as_posix(),
            "photoshop_render_path": (tmp_path / "aja_ps.png").as_posix(),
        },
    ]

    jsx = module.build_photoshop_jsx(rows, tmp_path / "result.json")

    assert "jackie_final_cover" in jsx
    assert "aja_control_line" in jsx
    assert "app.open(inputFile)" in jsx
    assert "applyUnSharpMask" in jsx
    assert "adjustBrightnessContrast" in jsx
    assert "doc.saveAs(outputFile" in jsx
    assert "app.version" in jsx
    assert "arike_break_shot" not in jsx
    assert "nneka_front_page" not in jsx
