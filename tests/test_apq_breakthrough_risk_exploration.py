from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "render_hsd_apq_breakthrough_risk_exploration_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_hsd_apq_breakthrough_risk_exploration_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (2048, 1152), (118, 118, 122))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 640, 2048, 1152), fill=(17, 23, 59))
    draw.rectangle((0, 470, 2048, 560), fill=(247, 193, 69))
    draw.rectangle((0, 560, 2048, 635), fill=(181, 35, 54))
    draw.ellipse((620, 100, 1140, 700), fill=(230, 210, 205))
    draw.rectangle((760, 520, 1460, 1152), fill=(12, 24, 68))
    draw.text((840, 736), "22", fill=(247, 193, 69))
    image.save(path, "JPEG")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_main_renders_four_experiments_and_supporting_artifacts(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "apq_breakthrough_risk_exploration_v1"
    source = tmp_path / "review_only_candidates" / "action_photo_candidates" / "wnba" / "apq001" / "apq001_review_only_candidate.jpg"
    baseline = tmp_path / "baseline_v03.png"
    write_source(source)
    Image.new("RGBA", (1080, 1350), (40, 44, 52, 255)).save(baseline, "PNG")

    fake_blender = tmp_path / "blender.exe"
    fake_blender.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(module, "probe_blender_version", lambda blender_executable: "Blender 5.1.2")

    assert (
        module.main(
            [
                "--source-image",
                source.as_posix(),
                "--baseline-image",
                baseline.as_posix(),
                "--output-dir",
                out_dir.as_posix(),
                "--blender-executable",
                fake_blender.as_posix(),
            ]
        )
        == 0
    )

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "report.md").read_text(encoding="utf-8")
    rows = read_csv(out_dir / "manual_review_intake.csv")

    assert manifest["version"] == "hsd-apq-breakthrough-risk-exploration-v1-review-only"
    assert manifest["status"] == "apq_breakthrough_risk_exploration_ready"
    assert manifest["variant_count"] == 4
    assert manifest["source_image_size"] == {"width": 2048, "height": 1152}
    assert manifest["baseline_present"] is True
    assert manifest["blender_version"] == "Blender 5.1.2"
    assert manifest["strongest_direction_id"] == "experiment_01_jersey_texture_poster"
    assert manifest["overall_answer"] == "conditional_yes"
    assert manifest["meaningfully_better_than_v03"] is True
    assert manifest["next_action"] == "continue_risky_apq_treatment_with_jersey_texture_only"
    assert manifest["renderer_strategy"] == "pil_only_review_only_breakthrough_prototypes_after_blender_behavior_inspection"
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["approval_state_change"] is False
    assert manifest["asset_approved"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["auto_publish"] is False
    assert manifest["publish_ready"] is False
    assert manifest["source_auto_enabled"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["contact_sheet_source_count"] == 5

    expected_ids = [
        "experiment_01_jersey_texture_poster",
        "experiment_02_score_hero_atmosphere",
        "experiment_03_double_exposure_scrim",
        "experiment_04_material_plane_scene",
    ]
    assert [row["variant_id"] for row in manifest["variant_rows"]] == expected_ids
    assert [row["variant_id"] for row in rows] == expected_ids
    assert rows[0]["operator_decision"] == ""
    assert rows[0]["operator_notes"] == ""
    assert rows[0]["meaningfully_better_than_v03"] == "true"

    for output_name in [
        "experiment_01_jersey_texture_poster.png",
        "experiment_02_score_hero_atmosphere.png",
        "experiment_03_double_exposure_scrim.png",
        "experiment_04_material_plane_scene.png",
    ]:
        with Image.open(out_dir / output_name) as image:
            assert image.size == (1080, 1350)

    with Image.open(out_dir / "contact_sheet.png") as contact_sheet:
        assert contact_sheet.size[0] > 1000
        assert contact_sheet.size[1] > 900

    assert "Can APQ001 produce a visually premium social artifact without a better source crop?" in report
    assert "Jersey Texture Poster" in report
    assert "Continue risky APQ treatment only in the jersey-texture direction." in report
