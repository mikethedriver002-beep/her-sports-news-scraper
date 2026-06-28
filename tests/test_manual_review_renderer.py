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
    contact_sheet = review_drafts / "draft_preview_visual_contact_sheet.png"
    manifest_path = run_dir / "manual_review_renderer_manifest.json"
    report_path = run_dir / "manual_review_renderer_report.md"
    board_path = run_dir / "manual_review_renderer_visual_comparison_board.md"
    assert preview.exists()
    assert (review_drafts / "draft_preview_ig_feed.png").exists()
    assert (review_drafts / "draft_preview_story.png").exists()
    assert (review_drafts / "draft_preview_square.png").exists()
    assert contact_sheet.exists()
    assert manifest_path.exists()
    assert report_path.exists()
    assert board_path.exists()
    assert (run_dir / "render_handoff_top_packet" / "handoff_manifest.json").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "draft_preview_created"
    assert manifest["version"] == "hsd-manual-review-renderer-v1.38.0-athlete-focal-contract"
    assert manifest["title"] == "Test Liberty result"
    assert manifest["source_artifact"] == "news_fact_packets.csv"
    assert manifest["source_cue"] == "source_confidence_ready"
    assert manifest["copy_context"] == "4 source(s); publish_grade score 92."
    assert manifest["renderer_mode"] == "template_driven_review_drafts"
    assert manifest["content_module"]["content_module_mode"] == "game_edge_fallback"
    assert manifest["content_module"]["content_module_status"] == "fallback_game_edge_no_verified_stat_text"
    assert manifest["content_module"]["content_module_fallback_label"] == "SCORE-DERIVED EDGE"
    assert manifest["content_module"]["athlete_led_render_status"] == "athlete_led_blocked_missing_verified_player_context"
    assert "athlete_name" in manifest["content_module"]["athlete_led_missing_fields"]
    assert "verified stat/story context" in manifest["content_module"]["athlete_led_missing_fields"]
    assert "No athlete-led preview produced" in manifest["content_module"]["athlete_led_blocker"]
    assert manifest["content_module"]["visual_mode"] == "no_photo_premium_result"
    assert manifest["content_module"]["hero_asset_required"] == "approved_local_athlete_photo_missing"
    assert manifest["content_module"]["focal_entity_type"] == "team_matchup"
    assert manifest["content_module"]["score_lock_variant"] == "final_score_locked_logo_first"
    assert manifest["content_module"]["proof_strip_variant"] == "score_edge_only"
    assert manifest["content_module"]["copy_unlock_state"] == "score_only_copy_locked_manual_review"
    assert manifest["content_module"]["background_family"] == "hsd_premium_sports_editorial"
    assert "Photo-first route blocked" in manifest["content_module"]["template_fit_reason"]
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
    assert manifest["render_background_style"] == "hsd_premium_sports_editorial_v12_athlete_focal_contract"
    assert "quiet_score_zones" in manifest["render_background_cues"]
    assert "subtle_stadium_light_sweep" in manifest["render_background_cues"]
    assert "team_accent_rim_light" in manifest["render_background_cues"]
    assert "soft_editorial_rule_grid" in manifest["render_background_cues"]
    assert "restrained_halftone_noise" in manifest["render_background_cues"]
    assert "logo_first_score_atmosphere" in manifest["render_background_cues"]
    assert "sports_editorial_depth_markers" in manifest["render_background_cues"]
    assert "square_compact_review_footer" in manifest["render_background_cues"]
    assert "square_context_score_hierarchy" in manifest["render_background_cues"]
    assert "proof_artifact_athlete_led_bridge" in manifest["render_background_cues"]
    assert "stat_proof_rail" in manifest["render_background_cues"]
    assert "photo_first_score_lock_slab" in manifest["render_background_cues"]
    assert "photo_first_score_type_lockup" in manifest["render_background_cues"]
    assert "photo_first_context_score_rail" in manifest["render_background_cues"]
    assert "photo_first_subject_glow_bridge" in manifest["render_background_cues"]
    assert "photo_first_soft_focal_frame" in manifest["render_background_cues"]
    assert "photo_first_athlete_primary_focal_contract" in manifest["render_background_cues"]
    assert "photo_first_editorial_nameplate" in manifest["render_background_cues"]
    assert "compact_square_photo_footer" in manifest["render_background_cues"]
    assert "generated_preview_qa" in manifest["render_background_cues"]
    assert {item["format_id"] for item in manifest["format_options"]} == {"ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"}
    assert all(item["review_only"] is True for item in manifest["format_options"])
    assert all(item["publish_ready"] is False for item in manifest["format_options"])
    assert all(item["render_background_style"] == "hsd_premium_sports_editorial_v12_athlete_focal_contract" for item in manifest["format_options"])
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
    assert all(item["visual_mode"] == "no_photo_premium_result" for item in manifest["format_options"])
    assert all(item["hero_asset_required"] == "approved_local_athlete_photo_missing" for item in manifest["format_options"])
    assert all(item["focal_entity_type"] == "team_matchup" for item in manifest["format_options"])
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
    visual_board = manifest["visual_comparison_board"]
    assert visual_board["status"] == "review_only_visual_comparison_ready"
    assert visual_board["review_only"] is True
    assert visual_board["publish_ready"] is False
    assert visual_board["approval_status"] == "not_approved_human_review_required"
    assert visual_board["path"] == board_path.as_posix()
    assert visual_board["contact_sheet_path"] == contact_sheet.as_posix()
    assert visual_board["contact_sheet_status"] == "visual_comparison_contact_sheet_ready"
    assert visual_board["format_count"] == 3
    assert visual_board["preview_freshness_status"] == "generated_from_current_handoff_packet"
    assert visual_board["visual_mode"] == "no_photo_premium_result"
    assert visual_board["background_style"] == "hsd_premium_sports_editorial_v12_athlete_focal_contract"
    assert visual_board["hero_asset_required"] == "approved_local_athlete_photo_missing"
    assert visual_board["focal_priority"] == "non_athlete_fallback"
    assert visual_board["athlete_focal_contract"] == "logo_score_fallback_not_athlete_led"
    assert visual_board["fallback_comparison_status"] == "fallback_active_label_no_athlete_photo"
    assert visual_board["score_layout_contract"] == "logo_score_fallback_score_team_caption_clearance"
    assert "manual visual QA intake" in visual_board["next_manual_review_step"] or "hold" in visual_board["next_manual_review_step"]
    assert {item["format_id"] for item in visual_board["rows"]} == {"ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"}
    assert all(item["review_only"] is True for item in visual_board["rows"])
    assert all(item["publish_ready"] is False for item in visual_board["rows"])
    assert all(item["automated_qa_status"] == "preview_qa_pass" for item in visual_board["rows"])
    assert all(item["focal_priority"] == "non_athlete_fallback" for item in visual_board["rows"])
    assert all(item["fallback_comparison_status"] == "fallback_active_label_no_athlete_photo" for item in visual_board["rows"])
    assert all(item["reference_public_mockup_path"] for item in visual_board["rows"])
    assert all(item["reference_layout_path"] for item in visual_board["rows"])

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
    contact = Image.open(contact_sheet)
    assert story.size == (1080, 1920)
    assert square.size == (1080, 1080)
    assert contact.size == (2400, 1600)
    assert ImageChops.difference(contact.convert("RGB"), Image.new("RGB", contact.size, contact.getpixel((0, 0)))).getbbox()
    square_title_crop = square.convert("L").crop((48, 112, 1032, 244))
    square_title_histogram = square_title_crop.histogram()
    bright_square_title_ratio = sum(square_title_histogram[200:]) / sum(square_title_histogram)
    assert bright_square_title_ratio > 0.025
    report = report_path.read_text(encoding="utf-8")
    assert "Renderer state: Review draft created" in report
    assert "Review draft is for human review only" in report
    assert "Preview source packet: `Test Liberty result`" in report
    assert "Preview freshness: generated from the current handoff packet." in report
    assert "Visual comparison board:" in report
    assert "Visual contact sheet:" in report
    assert "Source handoff generated: `2026-06-27T17:38:08+00:00`" in report
    assert "Preview decision cue" in report
    assert "## Review Draft Formats" in report
    assert "templates_hsd_20260625" in report
    assert "hsd_game_recap_final_score_a" in report
    assert "## Team Color And Logo Review Cues" in report
    assert "## Generated Preview QA" in report
    assert "preview_qa_pass" in report
    assert "Visual mode: `no_photo_premium_result`" in report
    assert "Visual contract: score_lock=`final_score_locked_logo_first`" in report
    assert "Athlete focal contract: priority=`non_athlete_fallback`" in report
    assert "Fallback comparison note: No athlete/person focal frame rendered" in report
    assert "Score layout contract: `logo_score_fallback_score_team_caption_clearance`" in report
    assert "Template fit reason: Photo-first route blocked" in report
    assert "visual_mode=`no_photo_premium_result`" in report
    assert "APPROVED LOGO" in report or "LOGO REVIEW" in report
    assert "Editorial microcopy" in report
    assert "publish_ready=`false`" in report
    board = board_path.read_text(encoding="utf-8")
    assert "# HSD Renderer Visual Comparison Board" in board
    assert "Review-only visual comparison artifact" in board
    assert "Does not publish or mark anything publish-ready" in board
    assert "Contact sheet:" in board
    assert "Preview freshness: `generated_from_current_handoff_packet`" in board
    assert "Visual mode: `no_photo_premium_result`" in board
    assert "Background style: `hsd_premium_sports_editorial_v12_athlete_focal_contract`" in board
    assert "Hero asset status: `approved_local_athlete_photo_missing`" in board
    assert "Focal priority: `non_athlete_fallback`" in board
    assert "Athlete focal contract: `logo_score_fallback_not_athlete_led`" in board
    assert "Fallback comparison: `fallback_active_label_no_athlete_photo`" in board
    assert "draft_preview_ig_feed.png" in board
    assert "draft_preview_story.png" in board
    assert "draft_preview_square.png" in board
    assert "reference_public_mockup_path" not in board
    assert "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight" in board
    assert "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight" in board
    assert "manual visual QA" in board or "hold if an athlete-led asset" in board
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


def test_manual_review_renderer_bridges_score_only_handoff_to_existing_stat_proof_athlete(tmp_path: Path, monkeypatch) -> None:
    import importlib.util

    monkeypatch.chdir(tmp_path)
    proof_path = tmp_path / "final_score_stat_proof_v1.csv"
    with proof_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "proof_id",
                "event_uid",
                "matchup",
                "recap_candidate",
                "fact_type",
                "fact_value",
                "named_player",
                "player_team",
                "stat_line",
                "proof_status",
                "source_url",
                "source_domain",
                "operator_note_path",
                "limitations",
                "review_only",
                "approval_state_change",
                "publish_action",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "proof_id": "proof_kamilla_cardoso",
                "event_uid": "event_d24648ed698733c7",
                "matchup": "Portland Fire at Chicago Sky",
                "recap_candidate": "Yes",
                "fact_type": "named_player_stat_line",
                "fact_value": "Kamilla Cardoso (Chicago Sky): PTS 30, REB 8, AST 1, BLK 1",
                "named_player": "Kamilla Cardoso",
                "player_team": "Chicago Sky",
                "stat_line": "PTS 30, REB 8, AST 1, BLK 1",
                "proof_status": "named_stat_line_source_backed_operator_verify",
                "source_url": "https://www.espn.com/wnba/game/_/gameId/401857025",
                "source_domain": "www.espn.com",
                "operator_note_path": "final_score_stat_proof_confirmation_intake_v1.csv proof_id=proof_kamilla_cardoso",
                "limitations": "Review-only stat proof derived from current box-score context; operator must verify the source before editorial or render use.",
                "review_only": "Yes",
                "approval_state_change": "none",
                "publish_action": "none_artifact_only",
            }
        )

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    packet = {
        "copy_headline": "Chicago Sky beat Portland Fire",
        "copy_dek": "Chicago Sky beat Portland Fire. Verified final: Chicago Sky 124, Portland Fire 94.",
        "top_performers": "",
    }
    score = module.parse_final_score(packet)

    selected = module.select_verified_stat_module(packet, score)
    assert selected["status"] == "verified_player_stat_module"
    assert selected["player_name"] == "Kamilla Cardoso"
    assert selected["proof_artifact_bridge_used"] == "true"
    assert selected["proof_source"] == "final_score_stat_proof_v1.csv"
    assert selected["proof_id"] == "proof_kamilla_cardoso"
    assert selected["athlete_led_render_status"] == "athlete_led_review_preview_ready"
    assert selected["athlete_led_missing_fields"] == ""
    assert selected["athlete_photo_status"] == "approved_local_headshot"
    assert selected["athlete_photo_path"] == "assets/leagues/wnba/athletes/chicago_sky_kamilla_cardoso/headshot.png"

    summary = module.content_module_summary(packet, {"tone": "result"})
    assert summary["content_module_mode"] == "verified_player_stats"
    assert summary["content_module_player"] == "Kamilla Cardoso"
    assert summary["proof_artifact_bridge_used"] == "true"
    assert summary["proof_source"] == "final_score_stat_proof_v1.csv"
    assert summary["athlete_led_render_status"] == "athlete_led_review_preview_ready"
    assert summary["visual_mode"] == "photo_first_performer"
    assert summary["hero_asset_required"] == "approved_local_athlete_photo"
    assert summary["focal_entity_type"] == "athlete"
    assert summary["score_lock_variant"] == "final_score_locked_photo_first"
    assert summary["proof_strip_variant"] == "player_stat_proof_strip"
    assert summary["copy_unlock_state"] == "verified_stat_copy_locked_manual_review"
    assert summary["focal_priority"] == "athlete_primary"
    assert summary["athlete_focal_contract"] == "approved_or_review_local_person_image_primary"
    assert summary["fallback_comparison_status"] == "fallback_not_used_athlete_preview_ready"
    assert summary["score_layout_contract"] == "photo_first_score_team_caption_clearance_locked"
    assert summary["background_family"] == "hsd_premium_sports_editorial"
    assert "photo-first result routing" in summary["template_fit_reason"]
    assert summary["athlete_photo_template_family"] == "approved_athlete_photo_final_score"
    feed_layout = module.athlete_photo_layout_for_format(summary, {"format_id": "ig_feed_4x5", "height": 1350})
    square_layout = module.athlete_photo_layout_for_format(summary, {"format_id": "square_feed_1x1", "height": 1080})
    assert feed_layout["athlete_photo_layout_mode"] == "photo_first_final_score"
    assert square_layout["athlete_photo_layout_mode"] == "square_photo_first_score_panel"
    feed_contract = module.visual_mode_contract(summary, feed_layout)
    assert feed_contract["visual_mode"] == "photo_first_performer"
    assert feed_contract["focal_priority"] == "athlete_primary"
    assert feed_contract["fallback_comparison_status"] == "fallback_not_used_athlete_preview_ready"
    square_contract = module.visual_mode_contract(summary, square_layout)
    assert square_contract["visual_mode"] == "photo_first_performer_square"
    assert square_contract["score_lock_variant"] == "final_score_locked_square_photo_panel"
    assert square_contract["score_layout_contract"] == "photo_first_score_team_caption_clearance_locked"
    assert summary["content_module_title"] == "CARDOSO + STATEMENT MARGIN"
    assert summary["content_module_matchup_note"] == "CHICAGO SKY 124, PORTLAND FIRE 94"
    assert summary["content_module_game_shape"] == "statement_margin"
    assert summary["content_module_stat_strength"] == "lead_ledger"
    assert summary["athlete_photo_status"] == selected["athlete_photo_status"]
    assert summary["athlete_photo_approval_cue"] == selected["athlete_photo_approval_cue"]
    assert summary["athlete_photo_review_required"] == str(bool(selected["athlete_photo_review_required"])).lower()
    assert summary["athlete_photo_path"] == "assets/leagues/wnba/athletes/chicago_sky_kamilla_cardoso/headshot.png"
    assert summary["athlete_photo_layout_options"] == "photo_first_final_score,square_photo_first_score_panel,compact_headshot_chip,logo_first_fallback,safe_no_photo_fallback"
    assert summary["athlete_photo_template_family"] in {"approved_athlete_photo_final_score", "logo_first_final_score_fallback"}
    assert summary["athlete_photo_identity_review_status"] == selected["athlete_photo_identity_review_status"]
    assert summary["athlete_photo_identity_resolution_status"] == "identity_resolution_missing"
    assert summary["editorial_microcopy_variant"] == "verified_player_ledger"
    assert summary["editorial_microcopy_headline"] == "CARDOSO + STATEMENT MARGIN"
    assert summary["editorial_microcopy_game_shape"] == "statement_margin"
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
    assert module.athlete_photo_layout_for_format(content, {"format_id": "square_feed_1x1", "height": 1080})["athlete_photo_layout_mode"] == "square_photo_first_score_panel"
    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    assert geometry["template_family"] == "approved_athlete_photo_final_score"
    assert geometry["photo_stage_box"] == [58, 372, 408, 590]
    assert geometry["stat_strip_box"] == [58, 990, 964, 132]
    assert geometry["minimum_clearance_px"] == 24
    square_geometry = module.photo_first_layout_geometry({"format_id": "square_feed_1x1", "width": 1080, "height": 1080})
    assert square_geometry["photo_stage_box"] == [60, 346, 308, 384]
    assert square_geometry["winner_score_row_box"] == [396, 360, 624, 124]
    assert square_geometry["loser_score_row_box"] == [396, 504, 624, 108]
    assert square_geometry["stat_strip_box"] == [60, 748, 960, 96]
    assert square_geometry["matchup_angle_box"] == [60, 862, 960, 112]
    for box in (
        square_geometry["photo_stage_box"],
        square_geometry["winner_score_row_box"],
        square_geometry["loser_score_row_box"],
        square_geometry["score_context_box"],
        square_geometry["stat_strip_box"],
        square_geometry["matchup_angle_box"],
    ):
        assert box[0] >= 0
        assert box[1] >= 0
        assert box[0] + box[2] <= 1080
        assert box[1] + box[3] <= 1080
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
            score_slab = module.photo_first_score_slab_box(tuple(row), winner=winner)
            assert score_slab[0] + score_slab[2] <= row[0] + row[2] - 26
            assert score_slab[1] >= row[1]
            assert score_slab[1] + score_slab[3] <= row[1] + row[3]
            assert team_text_box[0] + team_text_box[2] <= score_slab[0] - 26
            assert team_text_box[2] >= 128


def test_manual_review_renderer_photo_first_score_slab_stays_inside_score_row() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for format_spec in [
        {"format_id": "ig_feed_4x5", "width": 1080, "height": 1350},
        {"format_id": "ig_story_9x16", "width": 1080, "height": 1920},
        {"format_id": "square_feed_1x1", "width": 1080, "height": 1080},
    ]:
        geometry = module.photo_first_layout_geometry(format_spec)
        for key, winner in [("winner_score_row_box", True), ("loser_score_row_box", False)]:
            row = geometry[key]
            slab = module.photo_first_score_slab_box(tuple(row), winner=winner)
            text_box = module.photo_first_score_team_text_box(tuple(row), winner=winner)
            assert slab[0] >= row[0]
            assert slab[1] >= row[1]
            assert slab[0] + slab[2] <= row[0] + row[2] - 24
            assert slab[1] + slab[3] <= row[1] + row[3]
            assert slab[2] >= 132
            assert slab[3] >= 80
            assert text_box[0] + text_box[2] <= slab[0] - 26
            assert text_box[2] >= 128


def test_manual_review_renderer_photo_first_score_lock_slab_has_fitted_number_cell() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    row = tuple(geometry["winner_score_row_box"])
    module.draw_photo_first_score_row(
        image,
        row,
        "Chicago Sky",
        "124",
        (72, 144, 216),
        {},
        {},
        winner=True,
    )

    assert "photo_first_score_lock_slab" in module.RENDER_BACKGROUND_CUES
    assert "photo_first_score_type_lockup" in module.RENDER_BACKGROUND_CUES
    sx, sy, sw, sh = module.photo_first_score_slab_box(row, winner=True)
    slab = image.crop((sx, sy, sx + sw, sy + sh)).convert("RGB")
    data = slab.tobytes()
    pixels = max(1, len(data) // 3)
    pale_cell_pixels = 0
    dark_number_pixels = 0
    accent_spine_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 220 and g >= 225 and b >= 230:
            pale_cell_pixels += 1
        if r <= 28 and g <= 32 and b <= 40:
            dark_number_pixels += 1
        if b >= 120 and 45 <= r <= 110 and 90 <= g <= 170:
            accent_spine_pixels += 1

    assert pale_cell_pixels / pixels > 0.42
    assert dark_number_pixels / pixels > 0.08
    assert accent_spine_pixels / pixels > 0.015


def test_manual_review_renderer_photo_first_context_rail_has_score_hierarchy() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    box = tuple(geometry["score_context_box"])
    module.draw_photo_first_score_context_rail(image, box, "FEVER 111, SPARKS 87 / 198 PTS", (216, 48, 48), (232, 192, 48))

    assert "photo_first_context_score_rail" in module.RENDER_BACKGROUND_CUES
    x, y, w, h = box
    crop = image.crop((x, y, x + w, y + h)).convert("RGB")
    data = crop.tobytes()
    pixels = max(1, len(data) // 3)
    red_spine_pixels = 0
    gold_rule_pixels = 0
    light_text_pixels = 0
    dark_rail_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 120 and g <= 90 and b <= 90:
            red_spine_pixels += 1
        if r >= 150 and g >= 120 and b <= 90:
            gold_rule_pixels += 1
        if r >= 190 and g >= 190 and b >= 180:
            light_text_pixels += 1
        if r <= 18 and g <= 22 and b <= 32:
            dark_rail_pixels += 1

    assert red_spine_pixels / pixels > 0.015
    assert gold_rule_pixels / pixels > 0.006
    assert light_text_pixels / pixels > 0.025
    assert dark_rail_pixels / pixels > 0.45


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


def test_manual_review_renderer_photo_first_stage_draws_editorial_nameplate() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    module_payload = {
        "player_name": "Breanna Stewart",
        "athlete_photo_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "athlete_photo_status": "approved_local_headshot",
        "callouts": [
            {"value": "22", "label": "PTS"},
            {"value": "7", "label": "REB"},
            {"value": "4", "label": "AST"},
        ],
    }
    drawn = module.draw_photo_first_athlete_stage(
        image,
        tuple(geometry["photo_stage_box"]),
        module_payload,
        (72, 144, 216),
        tuple(geometry["photo_face_focus_box"]),
    )

    assert drawn is True
    assert module.photo_first_stage_caption(module_payload) == "22 PTS / 7 REB"
    assert "photo_first_editorial_nameplate" in module.RENDER_BACKGROUND_CUES
    x, y, w, h = geometry["photo_stage_box"]
    nameplate_crop = image.crop((x + 20, y + h - 70, x + min(w - 20, 300), y + h - 16)).convert("RGB")
    data = nameplate_crop.tobytes()
    pixels = max(1, len(data) // 3)
    gold_pixels = 0
    light_text_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 180 and g >= 135 and b <= 105:
            gold_pixels += 1
        if r >= 205 and g >= 205 and b >= 185:
            light_text_pixels += 1
    assert gold_pixels / pixels > 0.004
    assert light_text_pixels / pixels > 0.006


def test_manual_review_renderer_photo_first_stage_adds_portrait_spotlight() -> None:
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
            "callouts": [{"value": "22", "label": "PTS"}, {"value": "7", "label": "REB"}],
        },
        (72, 144, 216),
        tuple(geometry["photo_face_focus_box"]),
    )

    assert drawn is True
    assert "photo_first_portrait_spotlight" in module.RENDER_BACKGROUND_CUES
    assert "photo_first_soft_focal_frame" in module.RENDER_BACKGROUND_CUES
    assert "photo_first_athlete_primary_focal_contract" in module.RENDER_BACKGROUND_CUES
    x, y, w, h = geometry["photo_stage_box"]
    stage_crop = image.crop((x + 8, y + 34, x + w - 8, y + h - 14)).convert("RGB")
    data = stage_crop.tobytes()
    pixels = max(1, len(data) // 3)
    bright_portrait_pixels = 0
    blue_spotlight_pixels = 0
    gold_rim_pixels = 0
    soft_frame_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 170 and g >= 135 and b >= 110:
            bright_portrait_pixels += 1
        if b >= 118 and 45 <= r <= 130 and 80 <= g <= 175:
            blue_spotlight_pixels += 1
        if r >= 170 and 115 <= g <= 215 and b <= 115:
            gold_rim_pixels += 1
        if r >= 185 and g >= 165 and 70 <= b <= 170:
            soft_frame_pixels += 1

    assert bright_portrait_pixels / pixels > 0.145
    assert blue_spotlight_pixels / pixels > 0.008
    assert gold_rim_pixels / pixels > 0.003
    assert soft_frame_pixels / pixels > 0.002


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


def test_manual_review_renderer_background_draws_editorial_depth_markers_without_washing_title() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    marker_image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    module.draw_sports_editorial_depth_markers(marker_image, (72, 144, 216), (192, 35, 48), photo_first=True)

    assert "sports_editorial_depth_markers" in module.RENDER_BACKGROUND_CUES
    left_depth = marker_image.crop((54, 930, 507, 1000)).convert("RGB")
    right_depth = marker_image.crop((540, 930, 1026, 1000)).convert("RGB")
    left_data = left_depth.tobytes()
    right_data = right_depth.tobytes()
    left_pixels = max(1, len(left_data) // 3)
    right_pixels = max(1, len(right_data) // 3)
    warm_pixels = 0
    blue_bias_pixels = 0
    red_bias_pixels = 0
    for index in range(0, len(left_data), 3):
        r, g, b = left_data[index], left_data[index + 1], left_data[index + 2]
        if r >= 45 and g >= 38 and b <= 60 and r >= g:
            warm_pixels += 1
        if b > r and b >= 35 and g >= 25:
            blue_bias_pixels += 1
    for index in range(0, len(right_data), 3):
        r, g, b = right_data[index], right_data[index + 1], right_data[index + 2]
        if r >= 45 and g >= 38 and b <= 60 and r >= g:
            warm_pixels += 1
        if r > b and r >= 35 and g <= 45:
            red_bias_pixels += 1
    assert warm_pixels / (left_pixels + right_pixels) > 0.020
    assert blue_bias_pixels / left_pixels > 0.20
    assert red_bias_pixels / right_pixels > 0.20

    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    module.draw_reference_background(image, "final", (72, 144, 216), (192, 35, 48), photo_first=True)
    title_crop = image.crop((50, 130, 1030, 285)).convert("RGB")
    title_data = title_crop.tobytes()
    title_pixels = max(1, len(title_data) // 3)
    title_dark = 0
    for index in range(0, len(title_data), 3):
        r, g, b = title_data[index], title_data[index + 1], title_data[index + 2]
        if (r + g + b) / 3 <= 54:
            title_dark += 1
    assert title_dark / title_pixels > 0.70


def test_manual_review_renderer_photo_first_depth_stage_adds_focal_atmosphere() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1350), (2, 4, 9, 255))
    geometry = module.photo_first_layout_geometry({"format_id": "ig_feed_4x5", "width": 1080, "height": 1350})
    module.draw_photo_first_focal_depth_stage(image, geometry, (72, 144, 216), (192, 35, 48))

    assert "photo_first_focal_depth_stage" in module.RENDER_BACKGROUND_CUES
    assert "photo_first_subject_glow_bridge" in module.RENDER_BACKGROUND_CUES
    athlete_crop = image.crop((40, 330, 500, 975)).convert("RGB")
    score_crop = image.crop((480, 360, 1040, 792)).convert("RGB")
    shelf_crop = image.crop((56, 966, 1024, 995)).convert("RGB")
    bridge_crop = image.crop((420, 420, 800, 820)).convert("RGB")
    athlete_data = athlete_crop.tobytes()
    score_data = score_crop.tobytes()
    shelf_data = shelf_crop.tobytes()
    bridge_data = bridge_crop.tobytes()
    athlete_pixels = max(1, len(athlete_data) // 3)
    score_pixels = max(1, len(score_data) // 3)
    shelf_pixels = max(1, len(shelf_data) // 3)
    bridge_pixels = max(1, len(bridge_data) // 3)

    blue_depth = 0
    red_depth = 0
    gold_shelf = 0
    bridge_red = 0
    bridge_gold = 0
    for index in range(0, len(athlete_data), 3):
        r, g, b = athlete_data[index], athlete_data[index + 1], athlete_data[index + 2]
        if b > r and b >= 24 and g >= 18:
            blue_depth += 1
    for index in range(0, len(score_data), 3):
        r, g, b = score_data[index], score_data[index + 1], score_data[index + 2]
        if r > b and r >= 18 and g <= 34:
            red_depth += 1
    for index in range(0, len(shelf_data), 3):
        r, g, b = shelf_data[index], shelf_data[index + 1], shelf_data[index + 2]
        if r >= 48 and g >= 38 and b <= 105:
            gold_shelf += 1
    for index in range(0, len(bridge_data), 3):
        r, g, b = bridge_data[index], bridge_data[index + 1], bridge_data[index + 2]
        if r > b and r >= 24 and g <= 48:
            bridge_red += 1
        if r >= 44 and g >= 36 and b <= 72:
            bridge_gold += 1

    assert blue_depth / athlete_pixels > 0.25
    assert red_depth / score_pixels > 0.08
    assert gold_shelf / shelf_pixels > 0.015
    assert bridge_red / bridge_pixels > 0.08
    assert bridge_gold / bridge_pixels > 0.025


def test_manual_review_renderer_square_reference_spec_keeps_title_quiet_zone() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    square_spec = module.square_reference_spec()
    assert square_spec["canvas"] == {"width": 1080, "height": 1080}
    assert square_spec["zones"]["title"] == {"x": 60, "y": 116, "w": 960, "h": 132}
    key_box = square_spec["zones"]["key_performer"]
    hook_box = square_spec["zones"]["hook_takeaway"]
    assert key_box["h"] >= 96
    assert hook_box["h"] >= 90
    assert key_box["y"] + key_box["h"] + 12 <= hook_box["y"]
    assert hook_box["y"] + hook_box["h"] <= 1020
    assert "square_context_score_hierarchy" in module.RENDER_BACKGROUND_CUES
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


def test_manual_review_renderer_square_lower_module_shows_body_line_inside_card() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1080), (2, 4, 9, 255))
    hook_box = tuple(module.square_reference_spec()["zones"]["hook_takeaway"].values())
    module.draw_lower_reference_module(
        image,
        hook_box,
        "MATCHUP ANGLE",
        "CHICAGO SKY 124, PORTLAND FIRE 94; hold for source proof.",
        (37, 99, 163),
        headline="CHICAGO SKY +30 FINAL",
    )

    x, y, w, h = hook_box
    body_crop = image.crop((x + 24, y + 60, x + w - 24, y + h - 8)).convert("RGB")
    data = body_crop.tobytes()
    pixels = max(1, len(data) // 3)
    bright_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 185 and g >= 185 and b >= 185:
            bright_pixels += 1
    assert bright_pixels / pixels > 0.006


def test_manual_review_renderer_square_compact_footer_keeps_review_marker_without_full_red_band() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1080), (2, 4, 9, 255))
    module.draw_reference_guardrail(image, compact_footer=True)

    assert "square_compact_review_footer" in module.RENDER_BACKGROUND_CUES
    footer_crop = image.crop((54, 1010, 1026, 1063)).convert("RGB")
    data = footer_crop.tobytes()
    pixels = max(1, len(data) // 3)
    red_pixels = 0
    light_text_pixels = 0
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 135 and 18 <= g <= 75 and 28 <= b <= 90:
            red_pixels += 1
        if r >= 210 and g >= 210 and b >= 200:
            light_text_pixels += 1

    red_ratio = red_pixels / pixels
    assert 0.22 <= red_ratio <= 0.64
    assert light_text_pixels / pixels > 0.008


def test_manual_review_renderer_photo_first_square_template_uses_compact_footer() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("manual_renderer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    image = Image.new("RGBA", (1080, 1080), (2, 4, 9, 255))
    format_spec = {"format_id": "square_feed_1x1", "width": 1080, "height": 1080}
    template = {"template_id": "hsd_game_recap_final_score_a", "template_family": "game_recap_final_score"}
    score = {"winner": "New York Liberty", "loser": "Las Vegas Aces", "winner_score": "87", "loser_score": "76"}
    rendered = module.draw_photo_first_final_score_template(
        image,
        {"copy_context": "4 source(s); publish_grade score 92."},
        template,
        format_spec,
        score,
        {},
        {
            "player_name": "Breanna Stewart",
            "athlete_photo_status": "approved_local_headshot",
            "athlete_photo_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
            "headline": "STEWART + CLOSE FINISH",
            "editorial_line": "22 PTS / 7 REB / 4 AST in the New York Liberty 87, Las Vegas Aces 76 final.",
            "matchup_note": "NEW YORK LIBERTY 87, LAS VEGAS ACES 76",
            "callouts": [
                {"value": "22", "label": "PTS"},
                {"value": "7", "label": "REB"},
                {"value": "4", "label": "AST"},
            ],
        },
    )

    assert rendered is True
    assert "compact_square_photo_footer" in module.RENDER_BACKGROUND_CUES
    upper_footer_zone = image.crop((54, 1016, 1026, 1032)).convert("RGB")
    footer_band = image.crop((54, 1038, 1026, 1074)).convert("RGB")

    def red_ratio(crop: Image.Image) -> float:
        data = crop.tobytes()
        pixels = max(1, len(data) // 3)
        red_pixels = 0
        for index in range(0, len(data), 3):
            r, g, b = data[index], data[index + 1], data[index + 2]
            if r >= 135 and 18 <= g <= 80 and 28 <= b <= 95:
                red_pixels += 1
        return red_pixels / pixels

    assert red_ratio(upper_footer_zone) < 0.18
    assert red_ratio(footer_band) > 0.35


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
