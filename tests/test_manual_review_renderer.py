from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_review_renderer_v1.py"


def test_manual_review_renderer_reads_latest_handoff_and_writes_review_draft(tmp_path: Path) -> None:
    latest_handoff = tmp_path / "outputs" / "local" / "latest" / "files" / "render_handoff_top_packet"
    latest_handoff.mkdir(parents=True)
    packet = {
        "packet_id": "render_prep_1_test-story",
        "packet_status": "ready_for_manual_render_review",
        "render_readiness_score": "100",
        "render_readiness_band": "render_ready_review",
        "title": "Test Liberty result",
        "copy_headline": "Test Liberty result",
        "copy_dek": "Verified final: Liberty 87, Aces 76.",
        "copy_context": "4 source(s); publish_grade score 92.",
        "source_artifact": "news_fact_packets.csv",
        "source_cue": "source_confidence_ready",
        "source_detail": "Multiple free public sources.",
        "template_fit": "news_fact_card_review",
        "template_shape": "IG feed 1080x1350; Threads crop-safe summary",
        "asset_requirement": "No player asset required; use HSD brand treatment and verified source text only.",
        "asset_cue": "artifact_assets_ready_or_not_required",
        "manual_path": "manual_review_artifact_ready:news_fact_packets.csv",
        "renderer_family": "news_or_quality_graphics_manual_review",
        "manual_renderer_steps": "Open news_fact_packets.csv manually. | Prepare the graphic manually.",
        "approval_gate": "human_visual_review_required_before_any_post",
        "paid_api_policy": "free_public_sources_only_no_paid_api",
    }
    (latest_handoff / "handoff_manifest.json").write_text(
        json.dumps(
            {
                "handoff_status": "ready_for_manual_review",
                "guardrails": {"review_only": True, "auto_render": False, "auto_publish": False, "paid_apis": False},
                "packet": packet,
            }
        ),
        encoding="utf-8",
    )
    for name in ["README.md", "copy_sheet.md", "asset_checklist.md", "source_proof.md", "manual_renderer_prompt.md"]:
        (latest_handoff / name).write_text(f"# {name}\n", encoding="utf-8")

    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    review_drafts = run_dir / "render_handoff_top_packet" / "review_drafts"
    manifest_path = run_dir / "manual_review_renderer_manifest.json"
    report_path = run_dir / "manual_review_renderer_report.md"
    assert preview.exists()
    assert (review_drafts / "draft_preview_ig_feed.png").exists()
    assert (review_drafts / "draft_preview_story.png").exists()
    assert (review_drafts / "draft_preview_square.png").exists()
    assert manifest_path.exists()
    assert report_path.exists()
    assert (run_dir / "render_handoff_top_packet" / "handoff_manifest.json").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "draft_preview_created"
    assert manifest["version"] == "hsd-manual-review-renderer-v1.4.1-hsd-final-score-readable-polish"
    assert manifest["title"] == "Test Liberty result"
    assert manifest["source_artifact"] == "news_fact_packets.csv"
    assert manifest["source_cue"] == "source_confidence_ready"
    assert manifest["copy_context"] == "4 source(s); publish_grade score 92."
    assert manifest["renderer_mode"] == "template_driven_review_drafts"
    assert manifest["selected_template"]["template_id"] == "hsd_game_recap_final_score_a"
    assert manifest["selected_template"]["template_family"] == "game_recap_final_score"
    assert manifest["selected_template"]["reference_pack_id"] == "templates_hsd_20260625"
    assert manifest["reference_pack"]["pack_id"] == "templates_hsd_20260625"
    assert manifest["reference_pack"]["guardrails"]["reference_only"] is True
    assert manifest["reference_pack"]["guardrails"]["auto_publish"] is False
    assert len(manifest["format_options"]) == 3
    assert {item["format_id"] for item in manifest["format_options"]} == {"ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"}
    assert all(item["review_only"] is True for item in manifest["format_options"])
    assert all(item["publish_ready"] is False for item in manifest["format_options"])
    by_format = {item["format_id"]: item for item in manifest["format_options"]}
    assert by_format["ig_feed_4x5"]["reference_template_id"] == "hsd_game_recap_final_score_a"
    assert by_format["ig_feed_4x5"]["reference_exact_format_match"] is True
    assert by_format["ig_story_9x16"]["reference_template_id"] == "hsd_game_recap_final_score_c_story"
    assert by_format["ig_story_9x16"]["reference_exact_format_match"] is True
    assert by_format["square_feed_1x1"]["reference_exact_format_match"] is False
    assert by_format["square_feed_1x1"]["reference_derivation"] == "square_review_draft_derived_from_imported_4x5_layout"
    assert any(slot["slot_id"] == "primary_photo" and slot["status"] == "not_required_for_review_draft" for slot in manifest["asset_slots"])
    assert any(slot["slot_id"] == "primary_team_logo" for slot in manifest["asset_slots"])
    secondary_logo = next(slot for slot in manifest["asset_slots"] if slot["slot_id"] == "secondary_team_logo")
    assert secondary_logo["status"] == "approved_logo"
    assert secondary_logo["asset_path"] == "assets/leagues/wnba/teams/las_vegas_aces/logo.png"
    assert secondary_logo["render_method"] == "source_png"
    assert manifest["guardrails"]["manual_only"] is True
    assert manifest["guardrails"]["auto_render"] is False
    assert manifest["guardrails"]["auto_publish"] is False
    assert manifest["guardrails"]["approved"] is False
    assert manifest["guardrails"]["move_files"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert manifest["approval_status"] == "not_approved_human_review_required"

    image = Image.open(preview)
    assert image.size == (1080, 1350)
    title_crop = image.convert("L").crop((40, 150, 1040, 280))
    title_histogram = title_crop.histogram()
    bright_title_ratio = sum(title_histogram[200:]) / sum(title_histogram)
    assert bright_title_ratio > 0.03
    story = Image.open(review_drafts / "draft_preview_story.png")
    square = Image.open(review_drafts / "draft_preview_square.png")
    assert story.size == (1080, 1920)
    assert square.size == (1080, 1080)
    report = report_path.read_text(encoding="utf-8")
    assert "Draft preview is for human review only" in report
    assert "## Review Draft Formats" in report
    assert "templates_hsd_20260625" in report
    assert "hsd_game_recap_final_score_a" in report
    assert "publish_ready=`false`" in report
    assert not (tmp_path / "render_handoff_top_packet" / "draft_preview.png").exists()


def test_manual_review_renderer_parses_final_score_for_mobile_first_card() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    parsed = module.parse_final_score(
        {
            "copy_headline": "New York Liberty beat Las Vegas Aces",
            "copy_dek": "New York Liberty beat Las Vegas Aces. Verified final: New York Liberty 87, Las Vegas Aces 76.",
        }
    )

    assert parsed["winner"] == "New York Liberty"
    assert parsed["loser"] == "Las Vegas Aces"
    assert parsed["winner_score"] == "87"
    assert parsed["loser_score"] == "76"
