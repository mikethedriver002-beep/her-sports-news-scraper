from __future__ import annotations

import json
import os
import subprocess
import csv
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_review_renderer_v1.py"


def write_identity_resolution_inbox(run_dir: Path, **overrides: str) -> None:
    path = run_dir / "operator" / "inbox" / "wnba_athlete_identity_resolution.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "provider_player_id": "1630993",
        "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "operator_decision": "identity_verified_approved_for_review_renders",
        "identity_verified": "yes",
        "provider_player_id_verified": "yes",
        "approved_source_url": "https://www.wnba.com/player/1630993/breanna-stewart",
        "secondary_source_url": "https://liberty.wnba.com/",
        "backfill_provider_player_id": "",
        "operator_notes": "Verified source-backed identity for review-only renderer eligibility.",
        "operator_name": "Test Operator",
        "reviewed_at_local": "2026-06-25T12:00:00",
        "issue_resolution_status": "resolved",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    row.update(overrides)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


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
                "generated_at_utc": "2026-06-27T17:38:08+00:00",
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

    python_exe = REPO / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    proc = subprocess.run(
        [str(python_exe), str(SCRIPT)],
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
    assert manifest["version"] == "hsd-manual-review-renderer-v1.22.0-premium-editorial-backgrounds"
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
    assert manifest["content_module"]["editorial_microcopy_variant"] == "score_only_hold"
    assert "LIBERTY +11 FINAL" == manifest["content_module"]["editorial_microcopy_headline"]
    assert "No verified player stat line" in manifest["content_module"]["editorial_microcopy_body"]
    assert manifest["content_module"]["editorial_microcopy_game_shape"] == "clear_separation"
    assert manifest["selected_template"]["template_id"] == "hsd_game_recap_final_score_a"
    assert manifest["selected_template"]["template_family"] == "game_recap_final_score"
    assert manifest["selected_template"]["reference_pack_id"] == "templates_hsd_20260625"
    assert manifest["reference_pack"]["pack_id"] == "templates_hsd_20260625"
    assert manifest["reference_pack"]["guardrails"]["reference_only"] is True
    assert manifest["reference_pack"]["guardrails"]["auto_publish"] is False
    assert manifest["preview_source_title"] == "Test Liberty result"
    assert manifest["preview_freshness_status"] == "generated_from_current_handoff_packet"
    assert manifest["source_handoff_generated_at_utc"] == "2026-06-27T17:38:08+00:00"
    assert manifest["renderer_generated_at_utc"]
    assert "rerun the renderer" in manifest["preview_decision_cue"]
    assert len(manifest["format_options"]) == 3
    assert manifest["render_background_style"] == "hsd_premium_sports_editorial_v4_dimensional"
    assert "quiet_score_zones" in manifest["render_background_cues"]
    assert "subtle_stadium_light_sweep" in manifest["render_background_cues"]
    assert "team_accent_rim_light" in manifest["render_background_cues"]
    assert "soft_editorial_rule_grid" in manifest["render_background_cues"]
    assert "restrained_halftone_noise" in manifest["render_background_cues"]
    assert "logo_first_score_atmosphere" in manifest["render_background_cues"]
    assert "stat_proof_rail" in manifest["render_background_cues"]
    assert "generated_preview_qa" in manifest["render_background_cues"]
    assert {item["format_id"] for item in manifest["format_options"]} == {"ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"}
    assert all(item["review_only"] is True for item in manifest["format_options"])
    assert all(item["publish_ready"] is False for item in manifest["format_options"])
    assert all(item["render_background_style"] == "hsd_premium_sports_editorial_v4_dimensional" for item in manifest["format_options"])
    assert len(manifest["generated_preview_qa"]) == 3
    assert {item["format_id"] for item in manifest["generated_preview_qa"]} == {"ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"}
    assert all(item["status"] == "preview_qa_pass" for item in manifest["generated_preview_qa"])
    assert all(item["review_only"] is True for item in manifest["generated_preview_qa"])
    assert all(item["publish_ready"] is False for item in manifest["generated_preview_qa"])
    assert all(item["qa_policy"] == "generated_preview_visibility_only_not_asset_approval_or_publish_readiness" for item in manifest["generated_preview_qa"])
    by_format = {item["format_id"]: item for item in manifest["format_options"]}
    assert all(by_format[format_id]["preview_qa_status"] == "preview_qa_pass" for format_id in by_format)
    assert by_format["ig_feed_4x5"]["reference_template_id"] == "hsd_game_recap_final_score_a"
    assert by_format["ig_feed_4x5"]["reference_exact_format_match"] is True
    assert by_format["ig_story_9x16"]["reference_template_id"] == "hsd_game_recap_final_score_c_story"
    assert by_format["ig_story_9x16"]["reference_exact_format_match"] is True
    assert by_format["square_feed_1x1"]["reference_exact_format_match"] is False
    assert by_format["square_feed_1x1"]["reference_derivation"] == "square_review_draft_derived_from_imported_4x5_layout"
    assert by_format["ig_feed_4x5"]["athlete_photo_layout_mode"] == "safe_no_photo_fallback"
    assert by_format["ig_story_9x16"]["athlete_photo_layout_mode"] == "safe_no_photo_fallback"
    assert by_format["square_feed_1x1"]["athlete_photo_layout_mode"] == "safe_no_photo_fallback"
    assert any(slot["slot_id"] == "primary_photo" and slot["status"] == "not_required_for_review_draft" for slot in manifest["asset_slots"])
    assert any(slot["slot_id"] == "primary_team_logo" for slot in manifest["asset_slots"])
    primary_logo = next(slot for slot in manifest["asset_slots"] if slot["slot_id"] == "primary_team_logo")
    assert primary_logo["status"] in {"approved_logo", "registry_logo_review_required"}
    assert primary_logo["logo_approval_cue"] in {"APPROVED LOGO", "LOGO REVIEW"}
    assert primary_logo["logo_review_required"] == ("false" if primary_logo["status"] == "approved_logo" else "true")
    assert primary_logo["team_accent_hex"]
    assert primary_logo["team_accent_source"]
    secondary_logo = next(slot for slot in manifest["asset_slots"] if slot["slot_id"] == "secondary_team_logo")
    assert secondary_logo["status"] == "approved_logo"
    assert secondary_logo["asset_path"] == "assets/leagues/wnba/teams/las_vegas_aces/logo.png"
    assert secondary_logo["render_method"] == "source_png"
    assert secondary_logo["logo_approval_cue"] == "APPROVED LOGO"
    assert secondary_logo["logo_review_required"] == "false"
    assert secondary_logo["team_accent_hex"] == "#c41e3a"
    assert secondary_logo["team_accent_source"] == "local_wnba_team_registry_primary_color_logo_no_distinct_color"
    team_profiles = {item["role"]: item for item in manifest["team_visual_profiles"]}
    assert team_profiles["winner"]["logo_approval_cue"] in {"APPROVED LOGO", "LOGO REVIEW"}
    assert team_profiles["winner"]["logo_review_required"] is (primary_logo["status"] != "approved_logo")
    assert team_profiles["winner"]["team_accent_source"]
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
    context_crop = image.convert("L").crop((55, 320, 1030, 405))
    context_histogram = context_crop.histogram()
    bright_context_ratio = sum(context_histogram[190:]) / sum(context_histogram)
    assert bright_context_ratio > 0.04
    story = Image.open(review_drafts / "draft_preview_story.png")
    square = Image.open(review_drafts / "draft_preview_square.png")
    assert story.size == (1080, 1920)
    assert square.size == (1080, 1080)
    square_title_crop = square.convert("L").crop((48, 112, 1032, 244))
    square_title_histogram = square_title_crop.histogram()
    bright_square_title_ratio = sum(square_title_histogram[200:]) / sum(square_title_histogram)
    assert bright_square_title_ratio > 0.025
    report = report_path.read_text(encoding="utf-8")
    assert "Renderer state: Review draft created" in report
    assert "Review draft is for human review only" in report
    assert "Preview source packet: `Test Liberty result`" in report
    assert "Preview freshness: generated from the current handoff packet." in report
    assert "Source handoff generated: `2026-06-27T17:38:08+00:00`" in report
    assert "Preview decision cue" in report
    assert "## Review Draft Formats" in report
    assert "templates_hsd_20260625" in report
    assert "hsd_game_recap_final_score_a" in report
    assert "## Team Color And Logo Review Cues" in report
    assert "## Generated Preview QA" in report
    assert "preview_qa_pass" in report
    assert "APPROVED LOGO" in report or "LOGO REVIEW" in report
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
    assert module.game_shape(score)["game_shape"] == "clear_separation"
    assert module.game_shape({**score, "winner_score": "78", "loser_score": "76"})["game_shape"] == "close_finish"
    assert module.game_shape({**score, "winner_score": "102", "loser_score": "74"})["game_shape"] == "statement_margin"
    assert module.source_count(packet) == "4"
    assert module.source_quality_label(packet) == "SOURCE-READY"
    assert module.REVIEW_DRAFT_PILL_LABEL == "REVIEW DRAFT ONLY"
    assert module.REVIEW_DRAFT_FOOTER_LABEL == "REVIEW DRAFT ONLY - HUMAN CHECK REQUIRED"
    assert "publish" not in module.REVIEW_DRAFT_FOOTER_LABEL.lower()
    assert module.final_score_callouts(packet, score) == [
        {"label": "MARGIN", "value": "+11"},
        {"label": "TOTAL", "value": "163"},
        {"label": "SOURCES", "value": "4"},
    ]
    microcopy = module.selected_editorial_microcopy(packet, score, {"status": "fallback_game_edge_no_verified_stat_text"})
    assert microcopy["selected_variant_id"] == "score_only_hold"
    assert microcopy["headline"] == "LIBERTY +11 FINAL"
    assert microcopy["context"] == "LIBERTY 87, ACES 76; +11 margin; 163 total points"
    assert microcopy["game_shape"] == "clear_separation"
    assert "No verified player stat line" in microcopy["body"]
    assert "why/how" in microcopy["review_cue"]
    assert all("publish" not in item["body"].lower() for item in microcopy["variants"])
    edge = module.game_edge_module(score)
    assert edge["headline"] == "CONTROL WINDOW"
    assert edge["eyebrow"] == "SCORE-DERIVED EDGE"
    assert edge["game_shape"] == "clear_separation"
    assert "final margin" in edge["body"]
    assert module.review_prompt(score) == "WHAT FUELED LIBERTY'S SEPARATION?"


def test_manual_review_renderer_logo_first_score_atmosphere_paints_depth() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1080), (2, 4, 9, 255))
    before = image.copy()
    module.draw_logo_first_score_atmosphere(
        image,
        module.square_reference_spec(),
        (72, 144, 216),
        (196, 30, 58),
    )

    score_stack = (42, 326, 1038, 840)
    diff = ImageChops.difference(before.crop(score_stack), image.crop(score_stack))
    assert diff.convert("RGB").getbbox()
    assert ImageStat.Stat(diff.convert("L")).mean[0] > 2.0

    title_quiet_zone = (48, 112, 1032, 244)
    title_diff = ImageChops.difference(before.crop(title_quiet_zone), image.crop(title_quiet_zone))
    assert not title_diff.getbbox()


def test_manual_review_renderer_score_only_fallback_avoids_generic_result_copy() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    score = {"winner": "Phoenix Mercury", "loser": "Seattle Storm", "winner_score": "103", "loser_score": "74"}
    edge = module.game_edge_module(score)
    public = f"{edge['headline']} {edge['body']}".lower()

    assert edge["headline"] == "NO-CHASE FINAL"
    assert "statement win" not in public
    assert "point victory" not in public
    assert "margin" not in public


def test_manual_review_renderer_selects_verified_winning_team_stat_module(tmp_path: Path, monkeypatch) -> None:
    import importlib.util

    monkeypatch.chdir(tmp_path)
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
    assert selected["matchup_note"] == "LIBERTY 87, ACES 76"
    assert selected["athlete_photo_status"] in {"approved_local_headshot", "athlete_photo_identity_hold"}
    assert selected["athlete_photo_approval_cue"] in {"APPROVED PHOTO", "IDENTITY HOLD"}
    assert selected["athlete_photo_review_required"] is (selected["athlete_photo_status"] != "approved_local_headshot")
    assert selected["athlete_photo_path"] == "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png"
    assert selected["athlete_photo_render_method"] in {"approved_local_png_with_marker", "safe_text_fallback_identity_hold"}
    assert selected["athlete_photo_identity_review_status"] in {"identity_resolution_missing", "hold_identity_resolution_required"}
    assert selected["athlete_photo_identity_resolution_status"] == "identity_resolution_missing"
    if selected["athlete_photo_status"] == "athlete_photo_identity_hold":
        assert "operator/inbox/wnba_athlete_identity_resolution.csv" in selected["athlete_photo_blocker"]
    assert "20 PTS / 6 REB / 4 AST" in selected["editorial_line"]
    microcopy = module.selected_editorial_microcopy({"copy_context": "4 source(s); publish_grade."}, score, selected)
    assert microcopy["selected_variant_id"] == "verified_player_ledger"
    assert microcopy["headline"] == "STEWART + CLEAR SEPARATION"
    assert microcopy["game_shape"] == "clear_separation"
    assert "Stewart added 20 PTS, 6 REB, 4 AST" in microcopy["body"]
    assert "liberty 87, aces 76" in microcopy["body"]
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
    assert summary["content_module_matchup_note"] == "LIBERTY 87, ACES 76"
    assert summary["content_module_game_shape"] == "clear_separation"
    assert summary["content_module_stat_strength"] == "lead_ledger"
    assert summary["athlete_photo_status"] == selected["athlete_photo_status"]
    assert summary["athlete_photo_approval_cue"] == selected["athlete_photo_approval_cue"]
    assert summary["athlete_photo_review_required"] == str(bool(selected["athlete_photo_review_required"])).lower()
    assert summary["athlete_photo_path"] == "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png"
    assert summary["athlete_photo_layout_options"] == "photo_first_final_score,compact_headshot_chip,logo_first_fallback,safe_no_photo_fallback"
    assert summary["athlete_photo_template_family"] in {"approved_athlete_photo_final_score", "logo_first_final_score_fallback"}
    assert summary["athlete_photo_identity_review_status"] == selected["athlete_photo_identity_review_status"]
    assert summary["athlete_photo_identity_resolution_status"] == "identity_resolution_missing"
    assert summary["editorial_microcopy_variant"] == "verified_player_ledger"
    assert summary["editorial_microcopy_headline"] == "STEWART + CLEAR SEPARATION"
    assert summary["editorial_microcopy_game_shape"] == "clear_separation"
    assert len(summary["editorial_microcopy_variants"]) == 3
    assert summary["stat_source_confidence"] == "verified_stat_text_ready_manual_crosscheck_required"
    assert "Confirm the named performer" in summary["stat_review_cue"]


def test_manual_review_renderer_identity_resolution_inbox_clears_default_marker_for_review_only(tmp_path: Path, monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    run_dir = tmp_path / "run" / "files"
    write_identity_resolution_inbox(run_dir)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module._ATHLETE_PHOTO_ONBOARDING_CACHE = None
    module._ATHLETE_IDENTITY_AUDIT_CACHE = None
    module._ATHLETE_IDENTITY_RESOLUTION_CACHE = None

    selected = module.select_verified_stat_module(
        {"top_performers": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4"},
        {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "87", "loser_score": "76"},
    )

    assert selected["athlete_photo_status"] == "approved_local_headshot"
    assert selected["athlete_photo_approval_cue"] == "APPROVED PHOTO"
    assert selected["athlete_photo_review_required"] is False
    assert selected["athlete_photo_identity_review_status"] == "identity_resolution_cleared_for_review_renders"
    assert selected["athlete_photo_identity_resolution_status"] == "identity_resolution_cleared_for_review_renders"
    assert selected["athlete_photo_identity_resolution_evidence_url"] == "https://www.wnba.com/player/1630993/breanna-stewart"


def test_manual_review_renderer_uses_run_scoped_athlete_photo_variant_metadata(tmp_path: Path, monkeypatch) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    run_dir = tmp_path / "run" / "files"
    metadata_path = run_dir / "athlete_photo_onboarding" / "athlete_photo_onboarding_metadata.json"
    variant_path = run_dir / "athlete_photo_onboarding" / "variants" / "new_york_liberty" / "new_york_liberty_breanna_stewart__photo_first_feed.png"
    variant_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (380, 518), (20, 120, 110, 255)).save(variant_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "athletes": {
                    "new_york_liberty_breanna_stewart": {
                        "athlete_id": "new_york_liberty_breanna_stewart",
                        "source_headshot_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
                        "feed_variant_path": variant_path.as_posix(),
                        "story_variant_path": variant_path.as_posix(),
                        "square_variant_path": variant_path.as_posix(),
                        "variant_status": "review_variant_ready",
                        "crop_readiness_score": "91",
                        "approval_scope": "review_only_derivative_from_approved_headshot",
                        "review_only_policy": "derived_variant_does_not_approve_move_publish_or_mark_publish_ready",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    write_identity_resolution_inbox(run_dir)
    module._ATHLETE_PHOTO_ONBOARDING_CACHE = None
    module._ATHLETE_IDENTITY_AUDIT_CACHE = None
    module._ATHLETE_IDENTITY_RESOLUTION_CACHE = None

    selected = module.select_verified_stat_module(
        {"top_performers": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4"},
        {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "87", "loser_score": "76"},
    )

    assert selected["athlete_photo_status"] == "approved_local_headshot"
    assert selected["athlete_photo_path"] == "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png"
    assert selected["athlete_photo_review_variant_status"] == "review_variant_available"
    assert selected["athlete_photo_review_variant_feed_path"] == variant_path.as_posix()
    assert selected["athlete_photo_review_variant_crop_readiness_score"] == "91"
    assert selected["athlete_photo_review_variant_policy"] == "derived_variant_does_not_approve_move_publish_or_mark_publish_ready"
    assert module.athlete_photo_review_variant_path(selected, "photo_first_feed") == variant_path


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


def test_manual_review_renderer_adapts_close_and_statement_margin_copy() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    packet = {"top_performers": "Sabrina Ionescu (New York Liberty): PTS 18, REB 5, AST 7"}
    close_score = {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "78", "loser_score": "76"}
    close_module = module.select_verified_stat_module(packet, close_score)
    close_microcopy = module.selected_editorial_microcopy({"copy_context": "2 source(s)."}, close_score, close_module)
    assert close_module["headline"] == "IONESCU + CLOSE FINISH"
    assert close_module["game_shape"] == "close_finish"
    assert close_microcopy["headline"] == "IONESCU + CLOSE FINISH"
    assert "close finish" in close_microcopy["body"]
    assert module.review_prompt(close_score) == "WHO MADE THE DIFFERENCE LATE?"

    statement_score = {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "102", "loser_score": "74"}
    statement_module = module.select_verified_stat_module(packet, statement_score)
    statement_microcopy = module.selected_editorial_microcopy({"copy_context": "2 source(s)."}, statement_score, statement_module)
    assert statement_module["headline"] == "IONESCU + STATEMENT MARGIN"
    assert statement_module["game_shape"] == "statement_margin"
    assert statement_microcopy["headline"] == "IONESCU + STATEMENT MARGIN"
    assert "statement margin" in statement_microcopy["body"]


def test_manual_review_renderer_keeps_low_stat_packets_as_supporting_context() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    packet = {"top_performers": "Bench Guard (New York Liberty): PTS 4, REB 2, AST 1"}
    score = {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "78", "loser_score": "76"}
    selected = module.select_verified_stat_module(packet, score)
    microcopy = module.selected_editorial_microcopy({"copy_context": "2 source(s)."}, score, selected)
    summary = module.content_module_summary(
        {"copy_angle": "New York Liberty beat Las Vegas Aces", "copy_dek": "Verified final: New York Liberty 78, Las Vegas Aces 76.", **packet},
        {"tone": "result"},
    )

    assert selected["status"] == "verified_supporting_stat_module"
    assert selected["headline"] == "GUARD STAT NOTE"
    assert selected["stat_strength"] == "low_stat_context"
    assert selected["stat_source_confidence"] == "verified_low_stat_context_manual_crosscheck_required"
    assert "supporting context" in selected["stat_review_cue"]
    assert microcopy["selected_variant_id"] == "verified_supporting_stat_note"
    assert microcopy["headline"] == "LIBERTY CLOSE FINISH"
    assert "supporting context" in microcopy["body"]
    assert summary["content_module_status"] == "verified_supporting_stat_module"
    assert summary["content_module_stat_strength"] == "low_stat_context"
    assert summary["editorial_microcopy_variant"] == "verified_supporting_stat_note"


def test_manual_review_renderer_holds_missing_athlete_photo() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    score = {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "87", "loser_score": "76"}
    selected = module.select_verified_stat_module(
        {"top_performers": "Imaginary Player (New York Liberty): PTS 22, REB 7, AST 4"},
        score,
    )

    assert selected["status"] == "verified_player_stat_module"
    assert selected["athlete_photo_status"] == "athlete_photo_missing"
    assert selected["athlete_photo_approval_cue"] == "PHOTO MISSING"
    assert selected["athlete_photo_review_required"] is True
    assert selected["athlete_photo_render_method"] == "safe_text_fallback"
    assert "No local athlete headshot" in selected["athlete_photo_blocker"]


def test_manual_review_renderer_selects_photo_layout_by_format() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    content = {
        "athlete_photo_status": "approved_local_headshot",
        "athlete_photo_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "athlete_photo_identity_review_status": "identity_resolution_cleared_for_review_renders",
        "athlete_photo_identity_resolution_status": "identity_resolution_cleared_for_review_renders",
    }

    assert module.athlete_photo_layout_for_format(content, {"format_id": "ig_feed_4x5", "height": 1350})["athlete_photo_layout_mode"] == "photo_first_final_score"
    assert module.athlete_photo_layout_for_format(content, {"format_id": "ig_story_9x16", "height": 1920})["athlete_photo_layout_mode"] == "photo_first_final_score"
    assert module.athlete_photo_layout_for_format(content, {"format_id": "ig_feed_4x5", "height": 1350})["athlete_photo_layout_status"] == "approved_photo_first_template"
    assert module.athlete_photo_layout_for_format(content, {"format_id": "square_feed_1x1", "height": 1080})["athlete_photo_layout_mode"] == "compact_headshot_chip"
    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    assert geometry["template_family"] == "approved_athlete_photo_final_score"
    assert geometry["photo_stage_box"] == [58, 372, 408, 590]
    assert geometry["stat_strip_box"] == [58, 990, 964, 132]
    assert geometry["minimum_clearance_px"] == 24
    assert (
        module.athlete_photo_layout_for_format({"athlete_photo_status": "athlete_photo_missing", "athlete_photo_blocker": "missing"}, {"format_id": "ig_feed_4x5", "height": 1350})[
            "athlete_photo_layout_mode"
        ]
        == "safe_no_photo_fallback"
    )


def test_manual_review_renderer_photo_first_geometry_keeps_feed_and_story_clearance() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def right(box: list[int]) -> int:
        return box[0] + box[2]

    def bottom(box: list[int]) -> int:
        return box[1] + box[3]

    for format_spec in [
        {"format_id": "ig_feed_4x5", "width": 1080, "height": 1350},
        {"format_id": "ig_story_9x16", "width": 1080, "height": 1920},
    ]:
        geometry = module.photo_first_layout_geometry(format_spec)
        clearance = geometry["minimum_clearance_px"]
        photo = geometry["photo_stage_box"]
        focus = geometry["photo_face_focus_box"]
        winner = geometry["winner_score_row_box"]
        loser = geometry["loser_score_row_box"]
        context = geometry["score_context_box"]
        stat = geometry["stat_strip_box"]
        hook = geometry["matchup_angle_box"]

        assert right(photo) + clearance <= winner[0]
        assert right(photo) + clearance <= loser[0]
        assert bottom(winner) + clearance <= loser[1]
        assert bottom(loser) + clearance <= context[1]
        assert bottom(context) + clearance <= stat[1]
        assert bottom(stat) + clearance <= hook[1]
        assert photo[0] < focus[0] < right(focus) < right(photo)
        assert photo[1] < focus[1] < bottom(focus) < bottom(photo)
        for row, winner in [(winner, True), (loser, False)]:
            team_text_box = module.photo_first_score_team_text_box(tuple(row), winner=winner)
            score_plate_left = row[0] + row[2] - 178 - 14
            assert team_text_box[0] + team_text_box[2] <= score_plate_left - 20
            assert team_text_box[2] >= 128


def test_manual_review_renderer_photo_first_stage_preserves_face_edge_signal() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    drawn = module.draw_photo_first_athlete_stage(
        image,
        tuple(geometry["photo_stage_box"]),
        {
            "player_name": "Breanna Stewart",
            "athlete_photo_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
            "athlete_photo_status": "approved_local_headshot",
        },
        (72, 144, 216),
        tuple(geometry["photo_face_focus_box"]),
    )

    assert drawn is True
    x, y, w, h = geometry["photo_face_focus_box"]
    crop = image.crop((x, y, x + w, y + h)).convert("L")
    data = crop.tobytes()
    edges = 0
    checks = 0
    for row_y in range(0, crop.height, 2):
        row = row_y * crop.width
        for col_x in range(0, crop.width - 2, 2):
            if abs(data[row + col_x] - data[row + col_x + 2]) >= 55:
                edges += 1
            checks += 1
    for row_y in range(0, crop.height - 2, 2):
        row = row_y * crop.width
        next_row = (row_y + 2) * crop.width
        for col_x in range(0, crop.width, 2):
            if abs(data[row + col_x] - data[next_row + col_x]) >= 55:
                edges += 1
            checks += 1
    assert edges / checks >= 0.014


def test_manual_review_renderer_stat_strip_draws_visible_proof_rail() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    module.draw_photo_first_stat_strip(
        image,
        (58, 990, 964, 132),
        {
            "player_name": "Kamilla Cardoso",
            "headline": "CARDOSO + STATEMENT MARGIN",
            "editorial_line": "30 PTS / 8 REB / 1 AST in the CHICAGO SKY 124, PORTLAND FIRE 94 final.",
            "callouts": [
                {"value": "30", "label": "PTS"},
                {"value": "8", "label": "REB"},
                {"value": "1", "label": "AST"},
            ],
        },
        (72, 144, 216),
    )

    assert "stat_proof_rail" in module.RENDER_BACKGROUND_CUES
    crop = image.crop((60, 990, 1020, 1122)).convert("RGB")
    data = crop.tobytes()
    pixels = max(1, len(data) // 3)
    gold_pixels = 0
    blue_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 185 and g >= 145 and b <= 105:
            gold_pixels += 1
        if b >= 135 and 45 <= r <= 115 and 90 <= g <= 175:
            blue_pixels += 1
    assert gold_pixels / pixels > 0.006
    assert blue_pixels / pixels > 0.006


def test_manual_review_renderer_square_reference_spec_keeps_title_quiet_zone() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    square_spec = module.square_reference_spec()
    assert square_spec["canvas"] == {"width": 1080, "height": 1080}
    assert square_spec["zones"]["title"] == {"x": 60, "y": 116, "w": 960, "h": 132}
    assert module.format_reference_spec({"format_id": "square_feed_1x1"}, {})["zones"]["title"] == square_spec["zones"]["title"]


def test_manual_review_renderer_square_title_lockup_is_visible() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1080), (2, 4, 9, 255))
    template_spec = module.square_reference_spec()
    module.draw_final_score_reference_title(image, template_spec, "square_feed_1x1")

    title_crop = image.convert("L").crop((48, 112, 1032, 258))
    title_histogram = title_crop.histogram()
    bright_title_ratio = sum(title_histogram[190:]) / sum(title_histogram)
    assert bright_title_ratio > 0.025


def test_manual_review_renderer_keeps_partial_approved_module_out_of_photo_first_layout() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    content = {
        "athlete_photo_status": "approved_local_headshot",
        "athlete_photo_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "athlete_photo_identity_review_status": "hold_identity_resolution_required",
        "athlete_photo_identity_resolution_status": "identity_resolution_not_cleared",
        "athlete_photo_blocker": "Identity remains held.",
    }

    assert module.photo_first_eligible(content) is False
    layout = module.athlete_photo_layout_for_format(content, {"format_id": "ig_feed_4x5", "height": 1350})
    assert layout["athlete_photo_layout_mode"] == "safe_no_photo_fallback"
    assert layout["athlete_photo_layout_status"] == "photo_not_rendered"
    assert layout["athlete_photo_layout_detail"] == "Identity remains held."
