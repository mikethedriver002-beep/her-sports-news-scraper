from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_drm002_photoshop_finish_v3.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_drm002_photoshop_finish_v3", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_photoshop_jsx_contains_v3_luxury_controls(tmp_path: Path) -> None:
    module = load_module()
    jsx = module.build_photoshop_jsx(
        source_path=tmp_path / "source.jpg",
        export_dir=tmp_path / "exports",
        working_dir=tmp_path / "working",
        proof_dir=tmp_path / "proof",
        result_path=tmp_path / "working" / "result.json",
    )

    assert "drm002_raw_friction_lux" in jsx
    assert "drm002_luxury_pressure" in jsx
    assert "drm002_quiet_casefile" in jsx
    assert "addSoftShadow" in jsx
    assert "CASE STUDY" in jsx
    assert "UNYIELDING|PRESSURE" in jsx
    assert "MOTION|STUDY" in jsx
