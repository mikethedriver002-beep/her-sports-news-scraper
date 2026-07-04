from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_manual_surface_attachment_pack_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_manual_surface_attachment_pack_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, "PNG")


def test_builds_review_only_attachment_pack_with_thumbnails(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    latest_root = tmp_path / "outputs" / "local" / "latest" / "files"
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "action_photo_manual_surface_attachment_pack_v1"
    screenshot_dir = output_dir / "browser_screenshots"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(output_dir))

    write_png(latest_root / "apcs048_visual_rescue_v1" / "contact_sheet.png", (1680, 2140), (8, 16, 24))
    write_text(latest_root / "action_photo_manual_surface_index_v1" / "action_photo_manual_surface_index.html", "<html>manual index</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v6" / "action_photo_review_deck.html", "<html>uconn</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v5" / "action_photo_review_deck.html", "<html>world rugby</html>")
    write_text(latest_root / "action_photo_ranker_review_deck_v17" / "action_photo_review_deck.html", "<html>broad latest</html>")

    write_png(screenshot_dir / "manual_surface_index.png", (1280, 1800), (44, 44, 72))
    write_png(screenshot_dir / "uconn_v6_focus_deck.png", (1280, 1800), (52, 36, 28))
    write_png(screenshot_dir / "world_rugby_v5_focus_deck.png", (1280, 1800), (16, 50, 56))
    write_png(screenshot_dir / "latest_broad_deck.png", (1280, 1800), (60, 20, 48))

    manifest = module.build_packet(output_dir=output_dir, latest_files_root=latest_root, screenshot_dir=screenshot_dir)

    with (output_dir / "action_photo_manual_surface_attachment_index.csv").open(newline="", encoding="utf-8") as handle:
        index_rows = list(csv.DictReader(handle))
    report = (output_dir / "action_photo_manual_surface_attachment_pack_report.md").read_text(encoding="utf-8")
    mirror_manifest = json.loads((latest_root / "action_photo_manual_surface_attachment_pack_v1" / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_manual_surface_attachment_pack_ready"
    assert manifest["review_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["attachment_count"] == 5
    assert manifest["thumbnail_count"] == 5
    assert manifest["missing_source_count"] == 0
    assert manifest["mirror_dir"].endswith("outputs/local/latest/files/action_photo_manual_surface_attachment_pack_v1")

    assert [row["surface_id"] for row in index_rows] == [
        "apcs048_visual_rescue",
        "manual_surface_index",
        "uconn_v6_focus_deck",
        "world_rugby_v5_focus_deck",
        "latest_broad_deck",
    ]
    assert (output_dir / "attachments" / "apcs048_contact_sheet.png").exists()
    assert (output_dir / "attachments" / "manual_surface_index_screenshot.png").exists()
    assert (output_dir / "thumbnails" / "manual_surface_index_screenshot.png").exists()
    assert Image.open(output_dir / "thumbnails" / "apcs048_contact_sheet.png").size[0] <= 480
    assert Image.open(output_dir / "thumbnails" / "manual_surface_index_screenshot.png").size[0] <= 480
    assert "Attach this literal PNG first" in report
    assert "Browser screenshot of the current manual surface index" in report
    assert mirror_manifest["attachment_count"] == 5


def test_builds_report_when_browser_screenshots_are_missing(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    latest_root = tmp_path / "outputs" / "local" / "latest" / "files"
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "action_photo_manual_surface_attachment_pack_v1"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(output_dir))

    write_png(latest_root / "apcs048_visual_rescue_v1" / "contact_sheet.png", (1680, 2140), (8, 16, 24))
    write_text(latest_root / "action_photo_manual_surface_index_v1" / "action_photo_manual_surface_index.html", "<html>manual index</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v6" / "action_photo_review_deck.html", "<html>uconn</html>")
    write_text(latest_root / "action_photo_review_deck_official_source_expansion_v5" / "action_photo_review_deck.html", "<html>world rugby</html>")
    write_text(latest_root / "action_photo_ranker_review_deck_v17" / "action_photo_review_deck.html", "<html>broad latest</html>")

    manifest = module.build_packet(output_dir=output_dir, latest_files_root=latest_root, screenshot_dir=output_dir / "browser_screenshots")

    report = (output_dir / "action_photo_manual_surface_attachment_pack_report.md").read_text(encoding="utf-8")
    assert manifest["attachment_count"] == 1
    assert manifest["thumbnail_count"] == 1
    assert manifest["missing_source_count"] == 4
    assert "browser_screenshots" in report
