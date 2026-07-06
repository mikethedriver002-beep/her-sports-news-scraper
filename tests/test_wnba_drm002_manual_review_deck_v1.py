from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_drm002_manual_review_deck_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_drm002_manual_review_deck_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_drm002_manual_review_deck_builds_swipe_surface_with_click_to_load_preview(tmp_path: Path) -> None:
    module = load_module()
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_drm002_manual_review_deck_v1"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_drm002_manual_review_deck_v1"

    manifest = module.build_packet(
        intake_csv=REPO
        / "data"
        / "asset_registry"
        / "action_photo_candidates"
        / "review_only_action_photo_research_return_intake_v1.csv",
        output_dir=output_dir,
        latest_output_dir=latest_dir,
        head_commit="test-head",
    )

    assert manifest["status"] == "wnba_drm002_manual_review_deck_ready"
    assert manifest["candidate_queue_id"] == "DRM002"
    assert manifest["remote_image_loaded_by_deck"] is False
    assert manifest["remote_preview_mode"] == "operator_click_to_load_in_browser"
    assert manifest["download_approved"] == "no"
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False

    board_rows = read_csv(output_dir / "drm002_manual_review_board.csv")
    assert len(board_rows) == 1
    assert board_rows[0]["scout_candidate_id"] == "DRM002"
    assert board_rows[0]["candidate_image_url"].startswith("file:///")
    assert board_rows[0]["candidate_remote_image_url"].startswith("https://cdn.wnba.com/")
    assert board_rows[0]["download_approved"] == "no"
    assert board_rows[0]["review_only"] == "true"

    deck_manifest = json.loads((output_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["deck_item_count"] == 1
    assert deck_manifest["download_approved_default"] == "no"
    assert deck_manifest["asset_downloads"] is False

    deck_html = (output_dir / "review_deck" / "action_photo_review_deck.html").read_text(encoding="utf-8")
    assert "HSD Action Photo Review Deck" in deck_html
    assert "DRM002" in deck_html
    assert "load-remote-preview" in deck_html
    assert "drm002RemotePreviewUrl" in deck_html
    assert "https://cdn.wnba.com/sites/1611661330/2026/06/6.9-story.png" in deck_html
    assert '"image_or_render_url": "https://cdn.wnba.com/sites/1611661330/2026/06/6.9-story.png"' not in deck_html
    assert "drm002_manual_review_placeholder.svg" in deck_html

    decision_rows = read_csv(output_dir / "review_deck" / "manual_decision_export_template.csv")
    assert decision_rows[0]["candidate_id"] == "DRM002"
    assert decision_rows[0]["download_approved"] == "no"
    assert decision_rows[0]["asset_downloads"] == "false"
    assert decision_rows[0]["publish_ready"] == "false"

    assert (latest_dir / "review_deck" / "action_photo_review_deck.html").exists()
    latest_deck_html = (latest_dir / "review_deck" / "action_photo_review_deck.html").read_text(encoding="utf-8")
    assert output_dir.as_uri() not in latest_deck_html
    assert latest_dir.as_uri() in latest_deck_html
    latest_board_rows = read_csv(latest_dir / "drm002_manual_review_board.csv")
    assert latest_board_rows[0]["candidate_image_url"].startswith(latest_dir.as_uri())
