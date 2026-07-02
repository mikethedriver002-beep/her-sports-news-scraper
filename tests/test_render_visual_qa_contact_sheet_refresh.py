from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_render_visual_qa_contact_sheet_refresh_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_render_visual_qa_contact_sheet_refresh_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_sources(run_dir: Path, module) -> None:
    for path in [
        "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
        "render_handoff_top_packet/review_drafts/draft_preview_story.png",
        "render_handoff_top_packet/review_drafts/draft_preview_square.png",
        "adobe_visual_qa_packet/drafts/draft_preview_visual_contact_sheet.png",
        "render_handoff_top_packet/handoff_manifest.json",
    ]:
        source = run_dir / path
        source.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".json":
            source.write_text(json.dumps({"status": "ready_for_review"}), encoding="utf-8")
        else:
            source.write_bytes(f"seeded bytes for {path}".encode("utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_builds_review_only_contact_sheet_refresh_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir, module)

    assert module.main(["--head-commit", "abc123"]) == 0

    packet = run_dir / "render_visual_qa_contact_sheet_refresh"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    readme = (packet / "README.md").read_text(encoding="utf-8")
    summary = (packet / "render_visual_qa_contact_sheet_refresh.md").read_text(encoding="utf-8")
    rows = read_csv(packet / "render_visual_qa_contact_sheet_refresh.csv")

    assert manifest["version"] == "hsd-render-visual-qa-contact-sheet-refresh-v1-review-only"
    assert manifest["status"] == "render_visual_qa_contact_sheet_refresh_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["artifact_count"] == 5
    assert manifest["present_source_count"] == 5
    assert manifest["missing_source_count"] == 0
    assert manifest["latest_4x5_render_path"] == "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png"
    assert manifest["story_render_path"] == "render_handoff_top_packet/review_drafts/draft_preview_story.png"
    assert manifest["square_render_path"] == "render_handoff_top_packet/review_drafts/draft_preview_square.png"
    assert manifest["contact_sheet_path"] == "adobe_visual_qa_packet/drafts/draft_preview_visual_contact_sheet.png"
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False
    assert manifest["paid_apis"] is False

    assert "Score rail deboxed." in readme
    assert "Lower stat rail softened." in readme
    assert "Feed-only stat separator changed to middots." in readme
    assert "Hold, revise, or continue to the next renderer lane?" in readme
    assert "APQ001 quarantine action-photo prototypes remain review-only" in readme
    assert "review-only contact-sheet refresh packet" in readme

    assert "Latest 4:5 render" in summary
    assert "Adobe visual QA contact sheet" in summary
    assert "hold|revise|continue_next_renderer_lane" in {row["decision_options"] for row in rows if row.get("decision_options")}
    assert len([row for row in rows if row.get("artifact_id")]) == 5
    assert len([row for row in rows if row.get("question_id")]) == 3


def test_refresh_packet_reports_missing_sources_without_publish_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "render_visual_qa_contact_sheet_refresh" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["present_source_count"] == 0
    assert manifest["missing_source_count"] == 5
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
