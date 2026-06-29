from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_v1.py"


def python_executable() -> str:
    bundled = REPO / ".venv" / "Scripts" / "python.exe"
    return str(bundled if bundled.exists() else Path(sys.executable))


def make_preview(path: Path, *, size: tuple[int, int] = (1080, 1350)) -> None:
    image = Image.new("RGB", size, (248, 246, 241))
    draw = ImageDraw.Draw(image)
    headline_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 68)
    score_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 190)
    team_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 58)
    body_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
    small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    draw.rectangle((710, 74, 1030, 150), fill=(190, 39, 54))
    draw.rectangle((54, 1288, 1028, 1318), fill=(190, 39, 54))
    draw.text((74, 260), "Test Liberty result", font=headline_font, fill=(24, 28, 36))
    draw.text((74, 342), "Verified final: Liberty 87, Aces 76.", font=headline_font, fill=(24, 28, 36))
    draw.text((320, 450), "LIBERTY", font=team_font, fill=(24, 28, 36))
    draw.text((720, 420), "87", font=score_font, fill=(24, 28, 36))
    draw.text((320, 675), "ACES", font=team_font, fill=(24, 28, 36))
    draw.text((760, 650), "76", font=score_font, fill=(24, 28, 36))
    draw.text((74, 910), "Source confidence ready and assets not required.", font=body_font, fill=(24, 28, 36))
    draw.text((82, 980), "Manual render context", font=body_font, fill=(24, 28, 36))
    draw.text((82, 1040), "Approval: human visual review required before any post", font=small_font, fill=(24, 28, 36))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_reference_style_preview(path: Path) -> None:
    image = Image.new("RGB", (1080, 1350), (8, 12, 22))
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
    score_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 190)
    team_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 58)
    body_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
    small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    gold = (247, 203, 84)
    ink = (244, 247, 252)
    muted = (204, 210, 222)
    draw.rectangle((710, 74, 1030, 150), fill=(190, 39, 54))
    draw.rectangle((54, 1288, 1028, 1318), fill=(190, 39, 54))
    draw.line((60, 245, 1020, 245), fill=gold, width=3)
    draw.text((210, 170), "GAME RECAP", font=title_font, fill=ink, stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((620, 170), "FINAL SCORE", font=title_font, fill=gold, stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((70, 338), "FINAL / WNBA / SOURCE CHECKED", font=body_font, fill=gold, stroke_width=1, stroke_fill=(0, 0, 0))
    draw.text((820, 338), "REVIEW DRAFT", font=small_font, fill=ink, stroke_width=1, stroke_fill=(0, 0, 0))
    draw.text((320, 450), "LIBERTY", font=team_font, fill=ink)
    draw.text((720, 420), "87", font=score_font, fill=ink)
    draw.text((320, 675), "ACES", font=team_font, fill=muted)
    draw.text((760, 650), "76", font=score_font, fill=ink)
    draw.text((82, 970), "GAME EDGE", font=body_font, fill=gold)
    draw.text((82, 1018), "LIBERTY SEPARATES", font=body_font, fill=ink)
    draw.text((82, 1066), "New York created enough late cushion to hold off Las Vegas.", font=body_font, fill=ink)
    draw.text((82, 1114), "Verified final: Liberty 87, Aces 76.", font=body_font, fill=ink)
    draw.text((82, 1178), "YOUR TAKE", font=body_font, fill=(42, 132, 216))
    draw.text((82, 1226), "WHAT SWUNG LIBERTY VS ACES?", font=body_font, fill=ink)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_photo_first_preview(path: Path) -> None:
    image = Image.new("RGB", (1080, 1350), (6, 10, 18))
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
    score_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 118)
    team_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 42)
    body_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 34)
    small_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
    gold = (247, 203, 84)
    mint = (144, 216, 192)
    ink = (244, 247, 252)
    red = (190, 39, 54)
    draw.rectangle((710, 74, 1030, 150), fill=red)
    draw.rectangle((54, 1288, 1028, 1318), fill=red)
    draw.line((60, 245, 1020, 245), fill=gold, width=3)
    draw.text((210, 170), "GAME RECAP", font=title_font, fill=ink, stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((620, 170), "FINAL SCORE", font=title_font, fill=gold, stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((70, 338), "FINAL / WNBA / PHOTO-FIRST DRAFT", font=body_font, fill=gold, stroke_width=1, stroke_fill=(0, 0, 0))
    draw.rounded_rectangle((58, 372, 466, 962), radius=30, fill=(18, 42, 38), outline=mint, width=4)
    draw.text((94, 402), "PLAYER FOCUS", font=small_font, fill=mint)
    draw.ellipse((178, 538, 346, 714), fill=(210, 152, 118), outline=(255, 224, 200), width=4)
    draw.ellipse((222, 588, 236, 602), fill=(20, 24, 28))
    draw.ellipse((288, 588, 302, 602), fill=(20, 24, 28))
    draw.arc((232, 624, 296, 670), start=10, end=170, fill=(95, 32, 42), width=5)
    draw.rectangle((178, 706, 346, 918), fill=(28, 110, 96))
    draw.rounded_rectangle((80, 904, 300, 942), radius=8, fill=(3, 5, 10), outline=mint, width=2)
    draw.text((104, 911), "APPROVED PHOTO", font=small_font, fill=mint)
    for y, team, score, outline in [(398, "LIBERTY", "87", mint), (598, "ACES", "76", red)]:
        draw.rounded_rectangle((494, y, 1022, y + 176), radius=18, fill=(2, 4, 9), outline=outline, width=3)
        draw.text((620, y + 70), team, font=team_font, fill=ink)
        draw.text((860, y + 12), score, font=score_font, fill=ink, stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((494, 796), "LIBERTY +11 VS ACES / 163 PTS", font=small_font, fill=mint)
    draw.rounded_rectangle((58, 990, 1022, 1122), radius=16, fill=(2, 4, 9), outline=mint, width=3)
    draw.text((86, 1002), "PHOTO-FIRST / VERIFIED STAT TEXT", font=small_font, fill=mint)
    draw.text((86, 1038), "STEWART LED LIBERTY", font=team_font, fill=ink)
    draw.text((86, 1084), "20 PTS / 6 REB / 4 AST in the LIBERTY +11 vs ACES final.", font=small_font, fill=ink)
    draw.rounded_rectangle((58, 1148, 1022, 1260), radius=16, fill=(2, 4, 9), outline=red, width=3)
    draw.text((86, 1166), "MATCHUP ANGLE", font=small_font, fill=red)
    draw.text((86, 1202), "STEWART + CLEAR SEPARATION", font=team_font, fill=ink)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_guardrail_inputs(run_dir: Path) -> None:
    handoff_dir = run_dir / "render_handoff_top_packet"
    (handoff_dir / "handoff_manifest.json").write_text(
        json.dumps({"guardrails": {"review_only": True, "auto_render": False, "auto_publish": False, "paid_apis": False}}),
        encoding="utf-8",
    )
    (run_dir / "manual_review_renderer_manifest.json").write_text(
        json.dumps(
            {
                "status": "draft_preview_created",
                "approval_status": "not_approved_human_review_required",
                "guardrails": {
                    "manual_only": True,
                    "review_only": True,
                    "auto_render": False,
                    "auto_publish": False,
                    "approved": False,
                    "paid_apis": False,
                },
            }
        ),
        encoding="utf-8",
    )


def test_manual_visual_qa_writes_review_only_report_and_checklist(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    make_preview(handoff_dir / "draft_preview.png")
    write_guardrail_inputs(run_dir)
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest_path = run_dir / "manual_visual_qa_manifest.json"
    report_path = run_dir / "manual_visual_qa_report.md"
    checklist_path = run_dir / "manual_visual_qa_checklist.csv"
    assert manifest_path.exists()
    assert report_path.exists()
    assert checklist_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "human_review_required"
    assert manifest["approval_status"] == "not_approved_human_review_required"
    assert manifest["dimensions"] == {"width": 1080, "height": 1350}
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["auto_publish"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert manifest["summary"]["human_decision_required"] is True

    rows = list(csv.DictReader(checklist_path.open(newline="", encoding="utf-8")))
    check_ids = {row["check_id"] for row in rows}
    assert "dimensions_1080x1350" in check_ids
    assert "top_draft_label_zone" in check_ids
    assert "footer_guardrail_zone" not in check_ids
    assert "headline_text_zone" in check_ids
    assert "score_team_text_zone" in check_ids
    assert "context_text_zone" in check_ids
    assert "lower_module_text_zone" in check_ids
    assert "photo_first_template_readiness" in check_ids
    assert "player_ledger_readability" in check_ids
    assert "premium_editorial_clutter_scan" in check_ids
    assert "anti_dashboard_score_spine_review" in check_ids
    assert "lower_third_card_weight_review" in check_ids
    assert "preview_freshness_current_handoff" in check_ids
    assert "approval_guardrails" in check_ids
    assert "operator_visual_review" in check_ids
    assert all(row["operator_decision"] == "operator_fill_required" for row in rows)
    assert "Does not approve the preview" in report_path.read_text(encoding="utf-8")


def test_manual_visual_qa_accepts_reference_style_white_gold_title_signal(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    make_reference_style_preview(handoff_dir / "draft_preview.png")
    write_guardrail_inputs(run_dir)
    renderer_manifest = json.loads((run_dir / "manual_review_renderer_manifest.json").read_text(encoding="utf-8"))
    renderer_manifest["content_module"] = {
        "content_module_mode": "verified_player_stats",
        "content_module_status": "verified_player_stat_module",
        "content_module_player": "Breanna Stewart",
        "content_module_source_text": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4",
        "stat_source_confidence": "verified_stat_text_ready_manual_crosscheck_required",
    }
    (run_dir / "manual_review_renderer_manifest.json").write_text(json.dumps(renderer_manifest), encoding="utf-8")
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_manifest.json").read_text(encoding="utf-8"))
    title_check = next(check for check in manifest["checks"] if check["check_id"] == "headline_text_zone")
    ledger_check = next(check for check in manifest["checks"] if check["check_id"] == "player_ledger_readability")
    clutter_check = next(check for check in manifest["checks"] if check["check_id"] == "premium_editorial_clutter_scan")
    anti_dashboard_check = next(check for check in manifest["checks"] if check["check_id"] == "anti_dashboard_score_spine_review")
    lower_third_check = next(check for check in manifest["checks"] if check["check_id"] == "lower_third_card_weight_review")
    assert manifest["status"] == "human_review_required"
    assert title_check["qa_result"] == "pass"
    assert title_check["check_label"] == "Title readable contrast and safe-zone fit"
    assert "Style=reference_white_gold_title" in title_check["evidence"]
    assert "title ink ratio" in title_check["evidence"]
    assert ledger_check["qa_result"] == "pass"
    assert "content_module=verified_player_stats" in ledger_check["evidence"]
    assert clutter_check["qa_result"] in {"pass", "pass_human_review_required"}
    assert "premium editorial hierarchy" in clutter_check["evidence"]
    assert anti_dashboard_check["qa_result"] == "pass_human_review_required"
    assert "anti-dashboard score-spine" in anti_dashboard_check["check_label"].lower()
    assert lower_third_check["qa_result"] == "pass_human_review_required"
    assert "lower-third card-weight" in lower_third_check["check_label"].lower()
    assert "Non-final-score render" in lower_third_check["evidence"]
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["publish_ready"] is False


def test_manual_visual_qa_holds_final_score_missing_lower_third_rail_contract(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    make_reference_style_preview(handoff_dir / "draft_preview.png")
    write_guardrail_inputs(run_dir)
    renderer_manifest = json.loads((run_dir / "manual_review_renderer_manifest.json").read_text(encoding="utf-8"))
    renderer_manifest["selected_template"] = {
        "template_id": "hsd_game_recap_final_score_a",
        "template_family": "game_recap_final_score",
    }
    renderer_manifest["content_module"] = {
        "visual_mode": "no_photo_premium_result",
        "score_layout_contract": "logo_first_editorial_score_spine_no_dashboard_panels",
        "anti_dashboard_contract": "open_score_spine_no_nested_cards_no_metric_tiles",
    }
    renderer_manifest["render_background_cues"] = "logo_first_no_dashboard_card_panels,anti_dashboard_visual_qa"
    (run_dir / "manual_review_renderer_manifest.json").write_text(json.dumps(renderer_manifest), encoding="utf-8")
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_manifest.json").read_text(encoding="utf-8"))
    checks = {check["check_id"]: check for check in manifest["checks"]}
    assert checks["anti_dashboard_score_spine_review"]["qa_result"] == "pass_human_review_required"
    assert checks["lower_third_card_weight_review"]["qa_result"] == "hold"
    assert "lower_third_contract=missing" in checks["lower_third_card_weight_review"]["evidence"]
    assert manifest["guardrails"]["publish_ready"] is False


def test_manual_visual_qa_checks_photo_first_crop_and_clearance(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    make_photo_first_preview(handoff_dir / "draft_preview.png")
    write_guardrail_inputs(run_dir)
    renderer_manifest = json.loads((run_dir / "manual_review_renderer_manifest.json").read_text(encoding="utf-8"))
    renderer_manifest["render_background_cues"] = "photo_first_editorial_score_rails,photo_first_subtle_logo_identifiers"
    renderer_manifest["format_options"] = [
        {
            "format_id": "ig_feed_4x5",
            "primary": True,
            "athlete_photo_layout_mode": "photo_first_final_score",
            "photo_first_template_geometry": {
                "photo_stage_box": [58, 372, 408, 590],
                "photo_face_focus_box": [106, 572, 312, 188],
                "winner_score_row_box": [494, 398, 528, 176],
                "loser_score_row_box": [494, 598, 528, 160],
                "score_context_box": [494, 786, 528, 54],
                "stat_strip_box": [58, 990, 964, 132],
                "matchup_angle_box": [58, 1148, 964, 112],
                "minimum_clearance_px": 24,
            },
        }
    ]
    renderer_manifest["content_module"] = {
        "content_module_mode": "verified_player_stats",
        "content_module_status": "verified_player_stat_module",
        "content_module_player": "Breanna Stewart",
        "content_module_source_text": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4",
        "stat_source_confidence": "verified_stat_text_ready_manual_crosscheck_required",
    }
    (run_dir / "manual_review_renderer_manifest.json").write_text(json.dumps(renderer_manifest), encoding="utf-8")
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_manifest.json").read_text(encoding="utf-8"))
    checks = {check["check_id"]: check for check in manifest["checks"]}
    assert checks["score_team_text_zone"]["check_label"] == "Photo-first editorial score-rail readable signal"
    assert "min 0.035" in checks["score_team_text_zone"]["evidence"]
    assert checks["photo_first_crop_signal"]["qa_result"] == "pass"
    assert checks["photo_first_face_visibility"]["qa_result"] == "pass"
    assert checks["photo_first_text_clearance"]["qa_result"] == "pass"
    assert "minimum_clearance" in checks["photo_first_text_clearance"]["evidence"]
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["publish_ready"] is False


def test_manual_visual_qa_accepts_photo_first_no_redundant_score_context(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    preview_path = handoff_dir / "draft_preview.png"
    make_photo_first_preview(preview_path)
    image = Image.open(preview_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((480, 770, 1030, 858), fill=(6, 10, 18))
    image.save(preview_path)
    write_guardrail_inputs(run_dir)
    renderer_manifest = json.loads((run_dir / "manual_review_renderer_manifest.json").read_text(encoding="utf-8"))
    renderer_manifest["render_background_cues"] = (
        "photo_first_editorial_score_rails,photo_first_no_redundant_score_context"
    )
    renderer_manifest["format_options"] = [
        {
            "format_id": "ig_feed_4x5",
            "primary": True,
            "athlete_photo_layout_mode": "photo_first_final_score",
            "photo_first_template_geometry": {
                "photo_stage_box": [58, 372, 408, 590],
                "photo_face_focus_box": [106, 572, 312, 188],
                "winner_score_row_box": [494, 398, 528, 176],
                "loser_score_row_box": [494, 598, 528, 160],
                "score_context_box": [494, 786, 528, 54],
                "stat_strip_box": [58, 990, 964, 132],
                "matchup_angle_box": [58, 1148, 964, 112],
                "minimum_clearance_px": 24,
            },
        }
    ]
    renderer_manifest["content_module"] = {
        "content_module_mode": "verified_player_stats",
        "content_module_status": "verified_player_stat_module",
        "content_module_player": "Breanna Stewart",
        "content_module_source_text": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4",
        "stat_source_confidence": "verified_stat_text_ready_manual_crosscheck_required",
    }
    (run_dir / "manual_review_renderer_manifest.json").write_text(json.dumps(renderer_manifest), encoding="utf-8")
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_manifest.json").read_text(encoding="utf-8"))
    checks = {check["check_id"]: check for check in manifest["checks"]}
    assert checks["context_text_zone"]["qa_result"] == "pass"
    assert checks["context_text_zone"]["check_label"] == "Photo-first redundant score context removed"
    assert "No public score-context copy expected" in checks["context_text_zone"]["evidence"]
    assert checks["overall_text_signal"]["qa_result"] == "pass_human_review_required"


def test_manual_visual_qa_holds_stale_preview_against_newer_handoff(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    make_reference_style_preview(handoff_dir / "draft_preview.png")
    write_guardrail_inputs(run_dir)

    handoff_manifest = json.loads((handoff_dir / "handoff_manifest.json").read_text(encoding="utf-8"))
    handoff_manifest["generated_at_utc"] = "2026-06-27T17:38:08+00:00"
    handoff_manifest["packet"] = {"packet_id": "render_prep_1_current-story"}
    (handoff_dir / "handoff_manifest.json").write_text(json.dumps(handoff_manifest), encoding="utf-8")

    renderer_manifest = json.loads((run_dir / "manual_review_renderer_manifest.json").read_text(encoding="utf-8"))
    renderer_manifest["generated_at_utc"] = "2026-06-27T17:11:43+00:00"
    renderer_manifest["packet_id"] = "render_prep_1_current-story"
    renderer_manifest["selected_template"] = {"template_id": "hsd_game_recap_final_score_a", "template_family": "game_recap_final_score"}
    renderer_manifest["reference_pack"] = {"pack_id": "templates_hsd_20260625"}
    (run_dir / "manual_review_renderer_manifest.json").write_text(json.dumps(renderer_manifest), encoding="utf-8")

    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_manifest.json").read_text(encoding="utf-8"))
    freshness_check = next(check for check in manifest["checks"] if check["check_id"] == "preview_freshness_current_handoff")
    assert manifest["status"] == "hold_for_manual_review"
    assert freshness_check["qa_result"] == "hold"
    assert "fresh_after_handoff=False" in freshness_check["evidence"]
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["publish_ready"] is False


def test_manual_visual_qa_holds_wrong_dimensions_without_approval(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    handoff_dir = run_dir / "render_handoff_top_packet"
    make_preview(handoff_dir / "draft_preview.png", size=(1000, 1000))
    (handoff_dir / "handoff_manifest.json").write_text(
        json.dumps({"guardrails": {"review_only": True, "auto_render": False, "auto_publish": False, "paid_apis": False}}),
        encoding="utf-8",
    )
    (run_dir / "manual_review_renderer_manifest.json").write_text(
        json.dumps(
            {
                "approval_status": "not_approved_human_review_required",
                "guardrails": {
                    "manual_only": True,
                    "review_only": True,
                    "auto_render": False,
                    "auto_publish": False,
                    "approved": False,
                    "paid_apis": False,
                },
            }
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [python_executable(), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_manifest.json").read_text(encoding="utf-8"))
    dimension_check = next(check for check in manifest["checks"] if check["check_id"] == "dimensions_1080x1350")
    assert manifest["status"] == "hold_for_manual_review"
    assert dimension_check["qa_result"] == "hold"
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["publish_ready"] is False
