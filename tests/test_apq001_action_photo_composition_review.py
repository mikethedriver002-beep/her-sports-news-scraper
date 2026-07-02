from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apq001_action_photo_composition_review_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apq001_action_photo_composition_review_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_image(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color)
    image.save(path)


def seed_sources(run_dir: Path, *, include_sandbox: bool = True) -> None:
    make_image(run_dir / "render_handoff_top_packet" / "review_drafts" / "draft_preview_ig_feed.png", (1080, 1350), (28, 40, 55))
    make_image(
        run_dir
        / "data"
        / "assets"
        / "quarantine"
        / "review_only_candidates"
        / "action_photo_candidates"
        / "wnba"
        / "apq001"
        / "apq001_review_only_candidate.jpg",
        (1200, 1500),
        (64, 28, 54),
    )
    if include_sandbox:
        make_image(run_dir / "apq001_quarantine_4x5_render_sandbox" / "prototype_ig_feed_4x5.png", (1080, 1350), (26, 62, 44))
        write_json(
            run_dir / "apq001_quarantine_4x5_render_sandbox" / "manifest.json",
            {
                "status": "apq001_quarantine_4x5_render_sandbox_ready",
                "review_only": True,
                "artifact_only": True,
            },
        )
    write_json(
        run_dir / "apq001_manual_review_result_manifest.json",
        {
            "status": "apq001_manual_review_result_artifacts_ready",
            "review_only": True,
            "artifact_only": True,
        },
    )
    (run_dir / "apq001_manual_review_result_report.md").write_text("# APQ001 manual review\n\nReview-only.\n", encoding="utf-8")
    write_json(
        run_dir / "apq001_action_photo_4x5_prototype_plan" / "manifest.json",
        {
            "status": "apq001_action_photo_4x5_prototype_plan_ready",
            "review_only": True,
            "artifact_only": True,
        },
    )
    write_csv(
        run_dir / "apq001_renderer_recheck_packet" / "renderer_recheck_plan.csv",
        [
            {
                "plan_id": "APQRR001",
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "renderer_behavior_change": "false",
                "publish_ready": "false",
                "publishing": "false",
                "move_files": "false",
            }
        ],
        [
            "plan_id",
            "review_only",
            "artifact_only",
            "asset_downloads",
            "approval_state_change",
            "renderer_behavior_change",
            "publish_ready",
            "publishing",
            "move_files",
        ],
    )


def test_builds_apq001_action_photo_composition_review_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir)

    assert module.main([]) == 0

    out = run_dir / "apq001_action_photo_composition_review"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    review_md = (out / "composition_review.md").read_text(encoding="utf-8")
    intake_rows = read_csv(out / "manual_composition_intake.csv")

    assert manifest["version"] == "hsd-apq001-action-photo-composition-review-v1-review-only"
    assert manifest["status"] == "apq001_action_photo_composition_review_ready"
    assert manifest["comparison_contact_sheet_present"] is True
    assert manifest["current_headshot_present"] is True
    assert manifest["current_headshot_readable"] is True
    assert manifest["candidate_present"] is True
    assert manifest["candidate_readable"] is True
    assert manifest["sandbox_present"] is True
    assert manifest["sandbox_readable"] is True
    assert manifest["prototype_plan_present"] is True
    assert manifest["recheck_plan_present"] is True
    assert manifest["manual_manifest_present"] is True
    assert manifest["manual_report_present"] is True
    assert manifest["manual_question_count"] == 4
    assert manifest["manual_intake_rows"] == 4
    assert manifest["optional_source_missing_count"] == 0
    assert manifest["optional_source_unreadable_count"] == 0
    assert manifest["validation_issue_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    assert manifest["asset_approved"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["download_performed"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["move_files"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["renderer_behavior_change"] is False
    assert (out / "composition_contact_sheet.png").exists()
    assert [row["question_id"] for row in intake_rows] == [
        "APQ001-CR01",
        "APQ001-CR02",
        "APQ001-CR03",
        "APQ001-CR04",
    ]
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["artifact_only"] == "true" for row in intake_rows)
    assert all(row["apq001_quarantine_only"] == "true" for row in intake_rows)
    assert all(row["asset_approved"] == "false" for row in intake_rows)
    assert all(row["approval_state_change"] == "false" for row in intake_rows)
    assert all(row["download_performed"] == "false" for row in intake_rows)
    assert all(row["asset_downloads"] == "false" for row in intake_rows)
    assert all(row["image_edits"] == "false" for row in intake_rows)
    assert all(row["move_files"] == "false" for row in intake_rows)
    assert all(row["publish_ready"] == "false" for row in intake_rows)
    assert all(row["publishing"] == "false" for row in intake_rows)
    assert all(row["renderer_behavior_change"] == "false" for row in intake_rows)
    assert "Does APQ001 materially reduce the roster-card or headshot feel" in review_md
    assert "Are face, subject, and action context readable enough for a renderer recheck?" in review_md
    assert "What crop or layout notes are needed before any renderer implementation lane?" in review_md
    assert "Should the next lane prototype an action-photo-aware 4:5 layout" in review_md
    assert "approve" not in intake_rows[0]["question"].lower()
    assert "approve" not in intake_rows[0]["decision_options"].lower()
    assert "publish" not in intake_rows[0]["question"].lower()
    assert "publish" not in intake_rows[0]["decision_options"].lower()
    assert "approval" not in intake_rows[0]["decision_options"].lower()
    assert "approval" not in intake_rows[1]["decision_options"].lower()


def test_missing_optional_sandbox_degrades_gracefully(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir, include_sandbox=False)

    assert module.main([]) == 0

    out = run_dir / "apq001_action_photo_composition_review"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    intake_rows = read_csv(out / "manual_composition_intake.csv")
    review_md = (out / "composition_review.md").read_text(encoding="utf-8")

    assert manifest["status"] == "apq001_action_photo_composition_review_ready"
    assert manifest["sandbox_present"] is False
    assert manifest["sandbox_readable"] is False
    assert manifest["optional_source_missing_count"] == 1
    assert manifest["comparison_contact_sheet_present"] is True
    assert manifest["validation_issue_count"] == 0
    assert len(intake_rows) == 4
    assert intake_rows[0]["sandbox_path"].endswith("apq001_quarantine_4x5_render_sandbox/prototype_ig_feed_4x5.png")
    assert "APQ001 sandbox readable: `False`" in review_md
    assert "comparison sheet written" in review_md.lower()
