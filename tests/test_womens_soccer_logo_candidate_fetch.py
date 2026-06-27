from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "fetch_hsd_womens_soccer_logo_candidates_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_hsd_womens_soccer_logo_candidates_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_save_as_png_writes_review_candidate_without_approval(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "source.png"
    Image.new("RGBA", (180, 140), (20, 80, 140, 255)).save(source)
    target = tmp_path / "assets/leagues/womens_soccer/nwsl/teams/test/logo.png"

    ok, reason = module.save_as_png(source.read_bytes(), target)

    assert ok is True
    assert reason.startswith("saved_png:")
    assert target.exists()
    with Image.open(target) as image:
        assert image.size == (180, 140)


def test_normalize_candidate_url_converts_svg_to_png() -> None:
    module = load_module()

    assert module.normalize_candidate_url("https://example.com/page", "/logo.svg") == "https://example.com/logo.png"
