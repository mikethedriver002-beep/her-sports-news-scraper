from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_jackie_young_typography_crop_refine_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_jackie_young_typography_crop_refine_v1", SCRIPT)
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
    image = Image.new("RGB", (1080, 1920), (40, 28, 36))
    image.save(path, "JPEG")


def test_apcs039_typography_specs_define_source_led_and_clean_editorial_routes() -> None:
    module = load_module()
    specs = module.build_variant_specs()

    assert [spec["variant_id"] for spec in specs] == [
        "variant_01_photo_anchor",
        "variant_02_face_first_lede",
        "variant_03_ball_side_action",
        "variant_04_clean_story_stack",
    ]
    assert any("score_ready" in spec["visual_strength"] for spec in specs)
    assert any("editorial" in spec["variant_name"].lower() for spec in specs)
    assert all("apcs039" in spec["crop_strategy"] for spec in specs)
    assert all(spec["scrim_side"] in {"left", "right", "top", "bottom"} for spec in specs)


def test_build_packet_writes_four_review_only_1080x1350_variants(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg"
    output_dir = tmp_path / "outputs/local/tmp/wnba_apcs039_typography_crop_refine_v1"
    write_source(source)

    manifest = module.build_packet(
        source_image=source,
        output_dir=output_dir,
        head_commit="abc123",
    )

    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "visual_report.md").read_text(encoding="utf-8")
    rows = read_csv(output_dir / "manual_visual_review_intake.csv")

    assert manifest["status"] == "wnba_apcs039_typography_crop_refine_ready"
    assert manifest_json["version"] == "hsd-wnba-apcs039-typography-crop-refine-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["variant_count"] == 4
    assert manifest_json["best_variant_id"] in {
        "variant_01_photo_anchor",
        "variant_02_face_first_lede",
        "variant_03_ball_side_action",
        "variant_04_clean_story_stack",
    }
    assert manifest_json["review_only"] is True
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False
    assert "Blender overlay note: not used here" in report
    assert "boxed-stage" in report
    assert len(rows) == 4
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)

    assert Image.open(output_dir / "contact_sheet.png").size == (1080, 1350)
    for row in manifest_json["variant_rows"]:
        assert Path(row["output_png_path"]).exists()
        assert row["dimensions"] == [1080, 1350]

