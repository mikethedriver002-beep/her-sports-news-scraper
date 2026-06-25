from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_v1.py"


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
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
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
    assert "footer_guardrail_zone" in check_ids
    assert "headline_text_zone" in check_ids
    assert "score_team_text_zone" in check_ids
    assert "context_text_zone" in check_ids
    assert "lower_module_text_zone" in check_ids
    assert "player_ledger_readability" in check_ids
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
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
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
    assert manifest["status"] == "human_review_required"
    assert title_check["qa_result"] == "pass"
    assert title_check["check_label"] == "Title readable contrast and safe-zone fit"
    assert "Style=reference_white_gold_title" in title_check["evidence"]
    assert "title ink ratio" in title_check["evidence"]
    assert ledger_check["qa_result"] == "pass"
    assert "content_module=verified_player_stats" in ledger_check["evidence"]
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
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
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
