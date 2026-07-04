from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_apcs039_score_command_refine_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_apcs039_score_command_refine_v2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_source(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1080, 1920), (36, 28, 34))
    image.save(path, "JPEG")


def test_apcs039_score_command_specs_define_low_banner_and_side_accent_routes() -> None:
    module = load_module()
    specs = module.build_variant_specs()

    assert [spec["variant_id"] for spec in specs] == [
        "variant_01_score_command_low_banner",
        "variant_02_lower_banner_lead",
        "variant_03_side_accent_block",
        "variant_04_clean_story_stack",
    ]
    assert all("apcs039" in spec["crop_strategy"] for spec in specs)
    assert all(any(term in spec["banner_placement"] for term in ["banner", "bar", "rail"]) for spec in specs)
    assert any("low_banner" in spec["typography_treatment"] for spec in specs)
    assert any("side_accent" in spec["side_accent_grammar"] for spec in specs)


def test_build_packet_writes_four_review_only_1080x1350_variants(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg"
    output_dir = tmp_path / "outputs/local/tmp/wnba_apcs039_score_command_refine_v2"
    write_source(source)

    manifest = module.build_packet(source_image=source, output_dir=output_dir, head_commit="abc123")

    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "visual_report.md").read_text(encoding="utf-8")
    rows = read_csv(output_dir / "manual_visual_review_intake.csv")

    assert manifest["status"] == "wnba_apcs039_score_command_refine_ready"
    assert manifest_json["version"] == "hsd-wnba-apcs039-score-command-refine-v2-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["variant_count"] == 4
    assert manifest_json["best_variant_id"] == "variant_01_score_command_low_banner"
    assert manifest_json["review_only"] is True
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False
    assert manifest_json["source_auto_enabled"] is False
    assert manifest_json["paid_apis"] is False
    report_lower = report.lower()
    assert "lower banner placement" in report_lower
    assert "side-accent grammar" in report_lower
    assert len(rows) == 4
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["source_auto_enabled"] == "false" for row in rows)
    assert all(row["paid_apis"] == "false" for row in rows)

    assert Image.open(output_dir / "contact_sheet.png").size == (1080, 1350)
    for row in manifest_json["variant_rows"]:
        assert Path(row["output_png_path"]).exists()
        assert row["dimensions"] == [1080, 1350]
