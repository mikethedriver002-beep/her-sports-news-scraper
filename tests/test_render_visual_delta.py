from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_render_visual_delta_v1.py"


def python_executable() -> str:
    bundled = REPO / ".venv" / "Scripts" / "python.exe"
    return str(bundled if bundled.exists() else Path(sys.executable))


def make_reference(path: Path, size: tuple[int, int] = (360, 450), *, shifted: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, (10, 16, 28))
    draw = ImageDraw.Draw(image)
    offset = 18 if shifted else 0
    draw.rectangle((20 + offset, 38, size[0] - 20 + offset, 96), fill=(246, 246, 241))
    draw.rectangle((20, 132 + offset, size[0] - 20, 286 + offset), outline=(226, 186, 65), width=6)
    draw.rectangle((28, 144 + offset, 94, 210 + offset), fill=(245, 245, 245))
    draw.rectangle((106, 146 + offset, 212, 188 + offset), fill=(245, 245, 245))
    draw.rectangle((226, 128 + offset, size[0] - 34, 228 + offset), fill=(245, 245, 245))
    draw.rectangle((20, 320, size[0] - 20, 414), fill=(22, 28, 41))
    draw.rectangle((20, size[1] - 25, size[0] - 20, size[1] - 12), fill=(205, 31, 47))
    image.save(path)


def run_delta(tmp_path: Path, manifest: dict) -> tuple[dict, list[dict[str, str]]]:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)
    (run_dir / "manual_review_renderer_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
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
    payload = json.loads((run_dir / "render_visual_delta_manifest.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((run_dir / "render_visual_delta.csv").open(newline="", encoding="utf-8")))
    assert (run_dir / "render_visual_delta_report.md").exists()
    assert (run_dir / "render_visual_revision_plan.md").exists()
    assert (run_dir / "render_visual_revision_plan.csv").exists()
    assert (run_dir / "render_visual_revision_plan.json").exists()
    assert (run_dir / "render_next_level_editorial_qa.md").exists()
    assert (run_dir / "render_next_level_editorial_qa.csv").exists()
    assert (run_dir / "render_next_level_editorial_qa.json").exists()
    return payload, rows


def test_render_visual_delta_scores_drafts_against_public_and_layout_references(tmp_path: Path) -> None:
    draft = tmp_path / "drafts" / "draft_preview_ig_feed.png"
    public = tmp_path / "refs" / "public.png"
    layout = tmp_path / "refs" / "layout.png"
    make_reference(draft)
    make_reference(public)
    make_reference(layout, shifted=True)
    manifest = {
        "status": "draft_preview_created",
        "content_module": {
            "visual_mode": "no_photo_premium_result",
            "hero_image_mode": "logo_score_fallback_no_person_image",
            "action_photo_hero_contract": "manual_review_action_photo_not_available_no_download",
            "action_photo_candidate_status": "not_available_to_renderer",
            "athlete_led_render_status": "athlete_led_blocked_missing_verified_player_context",
        },
        "visual_comparison_board": {
            "visual_mode": "no_photo_premium_result",
            "fallback_comparison_status": "fallback_active_label_no_athlete_photo",
            "action_photo_candidate_status": "not_available_to_renderer",
        },
        "format_options": [
            {
                "format_id": "ig_feed_4x5",
                "path": draft.as_posix(),
                "reference_public_mockup_path": public.as_posix(),
                "reference_layout_path": layout.as_posix(),
                "reference_exact_format_match": True,
            }
        ],
        "guardrails": {"manual_only": True, "auto_publish": False, "approved": False, "paid_apis": False},
    }

    payload, rows = run_delta(tmp_path, manifest)

    assert payload["status"] == "visual_delta_review_ready"
    assert payload["approval_status"] == "not_approved_human_review_required"
    assert payload["guardrails"]["auto_approval"] is False
    assert payload["guardrails"]["auto_publish"] is False
    assert payload["guardrails"]["publish_ready"] is False
    assert payload["summary"]["comparison_count"] == 2
    assert {row["reference_kind"] for row in rows} == {"public_mockup", "layout"}
    assert all(row["reference_visual_delta_score"].isdigit() for row in rows)
    assert all(row["approval_policy"].startswith("review-only warning") for row in rows)
    assert payload["format_summaries"]["ig_feed_4x5"]["reference_visual_delta_score"].isdigit()
    revision = json.loads((tmp_path / "run" / "files" / "render_visual_revision_plan.json").read_text(encoding="utf-8"))
    assert revision["status"] == "manual_revision_plan_ready"
    assert revision["guardrails"]["auto_publish"] is False
    assert revision["guardrails"]["publish_ready"] is False
    revision_row = revision["revision_rows"][0]
    assert revision_row["format_id"] == "ig_feed_4x5"
    assert revision_row["revision_focus"]
    assert "Compare" in revision_row["specific_manual_revisions"] or "Open" in revision_row["inspect_first"]
    assert revision_row["approval_policy"].startswith("review-only manual guidance")
    next_level = json.loads((tmp_path / "run" / "files" / "render_next_level_editorial_qa.json").read_text(encoding="utf-8"))
    assert next_level["status"] == "next_level_editorial_qa_ready"
    assert next_level["guardrails"]["asset_downloads"] is False
    assert next_level["guardrails"]["headshot_writes"] is False
    assert next_level["guardrails"]["approved_marker_writes"] is False
    assert next_level["summary"]["action_photo_return_needed_count"] == 1
    focal_row = next(row for row in next_level["rows"] if row["gate_id"] == "premium_editorial_focal_point")
    assert focal_row["gate_status"] == "blocked_action_photo_return_needed"
    assert focal_row["return_path"] == "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    assert "headshot_bridge" in focal_row["primary_blocker"]
    next_level_md = (tmp_path / "run" / "files" / "render_next_level_editorial_qa.md").read_text(encoding="utf-8")
    assert "action-photo evidence return and validation" in next_level_md


def test_render_visual_delta_warns_when_reference_is_missing(tmp_path: Path) -> None:
    draft = tmp_path / "drafts" / "draft_preview_square.png"
    public = tmp_path / "refs" / "public.png"
    make_reference(draft, size=(300, 300))
    make_reference(public, size=(300, 300))
    manifest = {
        "status": "draft_preview_created",
        "format_options": [
            {
                "format_id": "square_feed_1x1",
                "path": draft.as_posix(),
                "reference_public_mockup_path": public.as_posix(),
                "reference_layout_path": (tmp_path / "refs" / "missing.png").as_posix(),
                "reference_exact_format_match": False,
            }
        ],
    }

    payload, rows = run_delta(tmp_path, manifest)

    missing = next(row for row in rows if row["reference_kind"] == "layout")
    assert missing["drift_band"] == "not_scored_missing_reference"
    assert missing["comparison_status"] == "manual_review_required"
    assert missing["reference_visual_delta_score"] == "0"
    assert payload["summary"]["warning_count"] >= 1
    assert payload["guardrails"]["move_files"] is False
    revision = json.loads((tmp_path / "run" / "files" / "render_visual_revision_plan.json").read_text(encoding="utf-8"))
    assert revision["revision_rows"][0]["revision_priority"] == "revise_before_manual_next_step"
