from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_graphic_system_premium_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_graphic_system_premium_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def write_png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1080, 1350), color).save(path)


def test_builds_review_only_packet_with_two_blender_backed_directions(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_graphic_system_premium_v1"

    def fake_pillow(spec, source_image, out_path):
        write_png(out_path, (30, 40, 55))
        return {"status": "ready", "source_meta": {"present": True}}

    def fake_blender(spec, source_image, out_path, blender_executable):
        write_png(out_path, (70, 40, 30))
        return {"status": "ready", "source_meta": {"present": True}}

    monkeypatch.setattr(module, "render_pillow_layout", fake_pillow)
    monkeypatch.setattr(module, "render_blender_layout", fake_blender)
    monkeypatch.setattr(module, "maybe_mirror_to_latest", lambda output_dir: None)

    manifest = module.build_packet(output_dir=out_dir, blender_executable=Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"))

    assert manifest["status"] == "wnba_graphic_system_premium_ready"
    assert manifest["proof_count"] == 5
    assert manifest["blender_available"] is True
    assert manifest["blender_backed_proof_count"] == 2
    assert manifest["validation_issue_count"] == 0
    assert manifest["boxed_stage_rejected"] is True

    expected_paths = [
        out_dir / "manifest.json",
        out_dir / "visual_report.md",
        out_dir / "manual_visual_review_intake.csv",
        out_dir / "blunt_visual_rubric.md",
        out_dir / "contact_sheet.png",
    ]
    for path in expected_paths:
        assert path.exists()

    for row in manifest["proof_rows"]:
        assert row["dimensions"] == [1080, 1350]
        assert Path(row["output_png_path"]).exists()

    with Image.open(out_dir / "contact_sheet.png") as contact_sheet:
        assert contact_sheet.size == (1080, 1560)


def test_rubric_explicitly_rejects_boxed_stage() -> None:
    module = load_module()
    rubric = module.blunt_rubric_text().lower()
    assert "#527 boxed-stage look" in rubric
    assert "gray floor toy mockups" in rubric
    assert "floating perspective panels" in rubric
