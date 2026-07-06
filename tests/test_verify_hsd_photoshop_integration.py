from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_hsd_photoshop_integration.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_hsd_photoshop_integration", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_build_smoke_jsx_references_png_and_proof_paths(tmp_path: Path) -> None:
    module = load_module()
    png_path = tmp_path / "smoke.png"
    proof_path = tmp_path / "result.json"

    jsx = module.build_smoke_jsx(png_path, proof_path)

    assert "#target photoshop" in jsx
    assert png_path.as_posix() in jsx
    assert proof_path.as_posix() in jsx
    assert "doc.saveAs" in jsx
    assert '"ok":true' in jsx
