from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_jackie_young_visual_upgrade_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_jackie_young_visual_upgrade_v2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1080, 1920), (44, 34, 38))
    image.save(path, "JPEG")


def test_jackie_young_visual_upgrade_specs_define_three_stronger_routes() -> None:
    module = load_module()
    specs = module.build_proof_specs()

    assert [spec["proof_id"] for spec in specs] == [
        "upgrade_01_score_command",
        "upgrade_02_cover_spotlight",
        "upgrade_03_wire_story_depth",
    ]
    assert all(spec["texture_filename"].endswith("_texture.png") for spec in specs)
    assert all("apcs039" in spec["crop_strategy"] for spec in specs)
    assert all(spec["texture_grade"]["contrast"] >= 1.24 for spec in specs)
    assert specs[0]["visual_strength"] == "strongest_premium_score_anchor"
    assert specs[0]["composition_treatment_mode"] == "photo_plus_dark_score_plane_blender_depth"


def test_runner_script_uses_v2_burn_in_and_real_texture() -> None:
    module = load_module()
    runner = module.build_runner_script()

    assert "ShaderNodeTexImage" in runner
    assert "bpy.data.images.load" in runner
    assert "add_photo(spec)" in runner
    assert "bpy.ops.render.render(write_still=True)" in runner
    assert "scene.render.resolution_x = 1080" in runner
    assert "scene.render.resolution_y = 1350" in runner
    assert "REVIEW ONLY - JACKIE YOUNG VISUAL UPGRADE V2" in runner
    assert "JACKIE YOUNG QUARANTINE PROOF" not in runner


def test_build_packet_writes_review_only_v2_proofs_with_stubbed_render(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    source = tmp_path / "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg"
    output_dir = tmp_path / "outputs/local/tmp/jackie_young_visual_upgrade_v2"
    write_source(source)

    def fake_probe(_blender: Path | None) -> str:
        return "Blender 5.1.2"

    def fake_render(_blender: Path, _runner: Path, specs_file: Path):
        payload = json.loads(specs_file.read_text(encoding="utf-8"))
        for row in payload["proof_specs"]:
            image = Image.new("RGB", (1080, 1350), (20, 18, 26))
            image.save(Path(row["output_png_path"]), "PNG")
        return module.v1.base.RenderResult(0, "stub render ok", "")

    monkeypatch.setattr(module.v1.base, "probe_blender_version", fake_probe)
    monkeypatch.setattr(module.v1.base, "run_blender_render", fake_render)

    manifest = module.build_packet(
        source_image=source,
        output_dir=output_dir,
        blender_executable=Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"),
        head_commit="abc123",
    )

    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "visual_upgrade_report.md").read_text(encoding="utf-8")
    rows = read_csv(output_dir / "manual_visual_review_intake.csv")

    assert manifest["status"] == "jackie_young_visual_upgrade_ready"
    assert manifest_json["version"] == "hsd-jackie-young-visual-upgrade-v2-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["source_image_present"] is True
    assert manifest_json["blender_used"] is True
    assert manifest_json["blender_version"] == "Blender 5.1.2"
    assert manifest_json["render_exit_code"] == 0
    assert manifest_json["traceback_present"] is False
    assert manifest_json["proof_count"] == 3
    assert manifest_json["strongest_proof_id"] == "upgrade_01_score_command"
    assert manifest_json["review_only"] is True
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["download_performed"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["approved_marker_writes"] is False
    assert manifest_json["headshot_writes"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False
    assert manifest_json["paid_apis"] is False
    assert manifest_json["source_auto_enabled"] is False

    for proof in manifest_json["proof_rows"]:
        assert proof["dimensions"] == [1080, 1350]
        assert proof["review_only"] is True
        assert Path(proof["texture_path"]).exists()
        assert Path(proof["output_png_path"]).exists()

    assert Image.open(output_dir / "contact_sheet.png").size == (1080, 562)
    assert "stronger contrast" in report
    assert "not asset approval" in report
    assert len(rows) == 3
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
