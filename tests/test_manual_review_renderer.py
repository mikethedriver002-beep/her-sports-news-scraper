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
    assert manifest["version"] == "hsd-manual-review-renderer-v1.12.0-editorial-microcopy"
    assert manifest["title"] == "Test Liberty result"
    assert manifest["source_artifact"] == "news_fact_packets.csv"
    assert manifest["source_cue"] == "source_confidence_ready"
    assert manifest["copy_context"] == "4 source(s); publish_grade score 92."
    assert manifest["renderer_mode"] == "template_driven_review_drafts"
    assert manifest["content_module"]["content_module_mode"] == "game_edge_fallback"
    assert manifest["content_module"]["content_module_status"] == "fallback_game_edge_no_verified_stat_text"
    assert manifest["content_module"]["content_module_fallback_label"] == "SCORE-DERIVED EDGE"
    assert manifest["content_module"]["stat_source_confidence"] == "score_only_fallback_manual_context_required"
    assert manifest["content_module"]["editorial_microcopy_status"] == "source_safe_editorial_microcopy_ready"
    assert manifest["content_module"]["editorial_microcopy_variant"] == "scoreline_spine"
    assert "LIBERTY +11 FINAL" == manifest["content_module"]["editorial_microcopy_headline"]
    assert "anchor the angle" in manifest["content_module"]["editorial_microcopy_body"]
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
    primary_logo = next(slot for slot in manifest["asset_slots"] if slot["slot_id"] == "primary_team_logo")
    assert primary_logo["status"] == "registry_logo_review_required"
    assert primary_logo["logo_approval_cue"] == "LOGO REVIEW"
    assert primary_logo["logo_review_required"] == "true"
    assert primary_logo["team_accent_hex"]
    assert primary_logo["team_accent_source"] == "sampled_from_local_logo_review_asset"
    secondary_logo = next(slot for slot in manifest["asset_slots"] if slot["slot_id"] == "secondary_team_logo")
    assert secondary_logo["status"] == "approved_logo"
    assert secondary_logo["asset_path"] == "assets/leagues/wnba/teams/las_vegas_aces/logo.png"
    assert secondary_logo["render_method"] == "source_png"
    assert secondary_logo["logo_approval_cue"] == "APPROVED LOGO"
    assert secondary_logo["logo_review_required"] == "false"
    assert secondary_logo["team_accent_hex"] == "#c41e3a"
    assert secondary_logo["team_accent_source"] == "local_wnba_team_registry_primary_color_logo_no_distinct_color"
    team_profiles = {item["role"]: item for item in manifest["team_visual_profiles"]}
    assert team_profiles["winner"]["logo_approval_cue"] == "LOGO REVIEW"
    assert team_profiles["winner"]["logo_review_required"] is True
    assert team_profiles["winner"]["team_accent_source"] == "sampled_from_local_logo_review_asset"
    assert team_profiles["opponent"]["logo_approval_cue"] == "APPROVED LOGO"
    assert team_profiles["opponent"]["logo_review_required"] is False
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
    assert "## Team Color And Logo Review Cues" in report
    assert "LOGO REVIEW" in report
    assert "Editorial microcopy" in report
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


def test_manual_review_renderer_builds_source_safe_final_score_callouts() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    packet = {
        "copy_context": "4 source(s); publish_grade.",
        "source_cue": "source_confidence_ready",
    }
    score = {
        "winner": "New York Liberty",
        "loser": "Las Vegas Aces",
        "winner_score": "87",
        "loser_score": "76",
    }

    assert module.score_margin(score) == 11
    assert module.score_total(score) == 163
    assert module.source_count(packet) == "4"
    assert module.source_quality_label(packet) == "PUBLISH-GRADE"
    assert module.final_score_callouts(packet, score) == [
        {"label": "MARGIN", "value": "+11"},
        {"label": "TOTAL", "value": "163"},
        {"label": "SOURCES", "value": "4"},
    ]
    microcopy = module.selected_editorial_microcopy(packet, score, {"status": "fallback_game_edge_no_verified_stat_text"})
    assert microcopy["selected_variant_id"] == "scoreline_spine"
    assert microcopy["headline"] == "LIBERTY +11 FINAL"
    assert microcopy["context"] == "LIBERTY +11 vs ACES; 163 combined points"
    assert "anchor the angle" in microcopy["body"]
    assert "why/how" in microcopy["review_cue"]
    edge = module.game_edge_module(score)
    assert edge["headline"] == "CLEAR EDGE"
    assert edge["eyebrow"] == "SCORE-DERIVED EDGE"
    assert "11-point advantage" in edge["body"]
    assert module.review_prompt(score) == "WHAT FUELED LIBERTY'S SEPARATION?"


def test_manual_review_renderer_selects_verified_winning_team_stat_module() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    packet = {
        "top_performers": "A'ja Wilson (Las Vegas Aces): PTS 16, REB 9, AST 5; Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4"
    }
    score = {
        "winner": "New York Liberty",
        "loser": "Las Vegas Aces",
        "winner_score": "87",
        "loser_score": "76",
    }

    performers = module.parse_verified_stat_performers(packet)
    assert len(performers) == 2
    selected = module.select_verified_stat_module(packet, score)
    assert selected["status"] == "verified_player_stat_module"
    assert selected["player_name"] == "Breanna Stewart"
    assert selected["headline"] == "STEWART LED LIBERTY"
    assert selected["matchup_note"] == "LIBERTY +11 vs ACES"
    assert "20 PTS / 6 REB / 4 AST" in selected["editorial_line"]
    microcopy = module.selected_editorial_microcopy({"copy_context": "4 source(s); publish_grade."}, score, selected)
    assert microcopy["selected_variant_id"] == "verified_player_ledger"
    assert microcopy["headline"] == "STEWART + LIBERTY"
    assert "Stewart's verified 20 PTS, 6 REB, 4 AST" in microcopy["body"]
    assert "named lead" in microcopy["body"]
    assert selected["callouts"][:3] == [
        {"label": "PTS", "value": "20"},
        {"label": "REB", "value": "6"},
        {"label": "AST", "value": "4"},
    ]
    summary = module.content_module_summary(
        {
            **packet,
            "copy_headline": "New York Liberty beat Las Vegas Aces",
            "copy_dek": "New York Liberty beat Las Vegas Aces. Verified final: New York Liberty 87, Las Vegas Aces 76.",
        },
        {"tone": "result"},
    )
    assert summary["content_module_mode"] == "verified_player_stats"
    assert summary["content_module_player"] == "Breanna Stewart"
    assert summary["content_module_title"] == "STEWART LED LIBERTY"
    assert summary["content_module_matchup_note"] == "LIBERTY +11 vs ACES"
    assert summary["editorial_microcopy_variant"] == "verified_player_ledger"
    assert summary["editorial_microcopy_headline"] == "STEWART + LIBERTY"
    assert len(summary["editorial_microcopy_variants"]) == 3
    assert summary["stat_source_confidence"] == "verified_stat_text_ready_manual_crosscheck_required"
    assert "Confirm the named performer" in summary["stat_review_cue"]


def test_manual_review_renderer_falls_back_when_stat_text_is_not_parseable() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    selected = module.select_verified_stat_module(
        {"top_performers": "Top performers pending manual review"},
        {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "87", "loser_score": "76"},
    )

    assert selected["status"] == "fallback_game_edge_no_verified_stat_text"
