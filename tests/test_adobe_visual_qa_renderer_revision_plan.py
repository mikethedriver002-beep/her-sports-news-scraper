from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_adobe_visual_qa_renderer_revision_plan_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_adobe_visual_qa_renderer_revision_plan_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def revision_row(revision_id: str, format_name: str, request: str, notes: str = "") -> dict[str, str]:
    return {
        "revision_id": revision_id,
        "format": format_name,
        "operator_decision": "revise",
        "revision_request": request,
        "operator_notes": notes,
        "crop_fit": "pass",
        "title_safety": "pass",
        "score_rail_dashboard_violation": "minor",
        "lower_stat_strip_violation": "minor",
        "logo_readiness": "pass",
        "action_photo_suitability": "revise",
        "review_only": "true",
        "artifact_only": "true",
        "asset_downloads": "false",
        "image_edits": "false",
        "approval_state_change": "false",
        "approved_marker_writes": "false",
        "publish_ready": "false",
        "publishing": "false",
        "move_files": "false",
    }


def test_renderer_revision_plan_builds_review_only_plan_rows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    rows = [
        revision_row(
            "AVQR001",
            "ig_feed_4x5",
            "Integrate background textures across the score split to soften the rigid widget appearance.",
        ),
        revision_row(
            "AVQR002",
            "ig_story_9x16",
            "Shift upper text blocks down vertically to clear the top interface safe zone.",
            "Header elements are crowding the upper limits.",
        ),
        {
            **revision_row(
                "AVQR003",
                "square_1x1",
                "Restructure the team score grid to prevent a cramped dashboard appearance within the 1x1 bounding box.",
            ),
            "score_rail_dashboard_violation": "major",
            "crop_fit": "revise",
        },
        {
            **revision_row(
                "AVQR004",
                "contact_sheet",
                "Re-render the final contact sheet once individual template layout adjustments are verified.",
            ),
            "score_rail_dashboard_violation": "none",
            "lower_stat_strip_violation": "none",
            "action_photo_suitability": "hold",
        },
    ]
    write_csv(run_dir / "adobe_visual_qa_revision_requests.csv", rows, module.REVISION_REQUEST_FIELDS)

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "adobe_visual_qa_renderer_revision_plan.json").read_text(encoding="utf-8"))
    plan_rows = read_csv(run_dir / "adobe_visual_qa_renderer_revision_plan.csv")
    report = (run_dir / "adobe_visual_qa_renderer_revision_plan.md").read_text(encoding="utf-8")
    spec_manifest = json.loads((run_dir / "adobe_visual_qa_renderer_revision_spec.json").read_text(encoding="utf-8"))
    spec_rows = read_csv(run_dir / "adobe_visual_qa_renderer_revision_spec.csv")
    spec_report = (run_dir / "adobe_visual_qa_renderer_revision_spec.md").read_text(encoding="utf-8")

    assert manifest["version"] == "hsd-adobe-visual-qa-renderer-revision-plan-v1-review-only"
    assert manifest["status"] == "adobe_visual_qa_renderer_revision_plan_ready"
    assert manifest["revision_request_rows"] == 4
    assert manifest["plan_rows"] == 4
    assert manifest["spec_rows"] == 4
    assert manifest["spec_status"] == "adobe_visual_qa_renderer_revision_spec_ready"
    assert manifest["validation_issue_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["renderer_behavior_changed"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert [row["renderer_area"] for row in plan_rows] == [
        "score_rail_typography",
        "story_title_safe_zone",
        "square_score_grid",
        "contact_sheet_rerender",
    ]
    assert [row["priority"] for row in plan_rows] == ["P1", "P0", "P0", "P2"]
    assert [row["implementation_task"] for row in spec_rows] == [
        "Score rail typography pass",
        "Story safe-zone offset",
        "Square score-grid deboxing",
        "Contact-sheet rerender verification",
    ]
    assert all(row["review_only"] == "true" for row in plan_rows)
    assert all(row["renderer_behavior_changed"] == "false" for row in plan_rows)
    assert all(row["publish_ready"] == "false" for row in plan_rows)
    assert all(row["review_only"] == "true" for row in spec_rows)
    assert all(row["asset_downloads"] == "false" for row in spec_rows)
    assert all(row["image_edits"] == "false" for row in spec_rows)
    assert all(row["renderer_behavior_changed"] == "false" for row in spec_rows)
    assert all(row["approval_state_change"] == "false" for row in spec_rows)
    assert all(row["approved_marker_writes"] == "false" for row in spec_rows)
    assert all(row["publish_ready"] == "false" for row in spec_rows)
    assert all(row["publishing"] == "false" for row in spec_rows)
    assert spec_manifest["status"] == "adobe_visual_qa_renderer_revision_spec_ready"
    assert spec_manifest["asset_downloads"] is False
    assert spec_manifest["image_edits"] is False
    assert spec_manifest["renderer_behavior_changed"] is False
    assert spec_manifest["approval_state_change"] is False
    assert spec_manifest["approved_marker_writes"] is False
    assert spec_manifest["publish_ready"] is False
    assert spec_manifest["publishing"] is False
    assert "No renderer behavior changes." in report
    assert "Review-only implementation checklist" in spec_report
    assert "renderer_behavior_changed=false" in spec_report


def test_renderer_revision_plan_waits_when_revision_csv_has_no_rows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    write_csv(run_dir / "adobe_visual_qa_revision_requests.csv", [], module.REVISION_REQUEST_FIELDS)

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "adobe_visual_qa_renderer_revision_plan.json").read_text(encoding="utf-8"))
    plan_rows = read_csv(run_dir / "adobe_visual_qa_renderer_revision_plan.csv")
    spec_rows = read_csv(run_dir / "adobe_visual_qa_renderer_revision_spec.csv")

    assert manifest["status"] == "adobe_visual_qa_renderer_revision_plan_waiting_for_revision_requests"
    assert manifest["spec_status"] == "adobe_visual_qa_renderer_revision_spec_waiting_for_revision_requests"
    assert manifest["revision_request_rows"] == 0
    assert manifest["plan_rows"] == 0
    assert manifest["spec_rows"] == 0
    assert manifest["validation_issue_count"] == 0
    assert plan_rows == []
    assert spec_rows == []
    assert manifest["renderer_behavior_changed"] is False
    assert manifest["publish_ready"] is False


def test_renderer_revision_plan_blocks_invalid_or_unsafe_revision_rows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    fields = [field for field in module.REVISION_REQUEST_FIELDS if field != "operator_notes"]
    rows = [
        {
            key: value
            for key, value in {
                **revision_row("AVQR001", "ig_feed_4x5", ""),
                "operator_decision": "approved",
                "asset_downloads": "true",
                "publish_ready": "true",
            }.items()
            if key in fields
        },
        {
            key: value
            for key, value in revision_row("AVQR001", "ig_story_9x16", "duplicate id").items()
            if key in fields
        },
    ]
    write_csv(run_dir / "adobe_visual_qa_revision_requests.csv", rows, fields)

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "adobe_visual_qa_renderer_revision_plan.json").read_text(encoding="utf-8"))
    issue_pairs = {(issue["field"], issue["issue"]) for issue in manifest["validation_issues"]}

    assert manifest["status"] == "adobe_visual_qa_renderer_revision_plan_has_validation_issues"
    assert ("operator_notes", "required_field_missing") in issue_pairs
    assert ("operator_decision", "operator_decision_not_allowed") in issue_pairs
    assert ("revision_request", "revision_or_notes_required") in issue_pairs
    assert ("revision_id", "duplicate_revision_id") in issue_pairs
    assert ("asset_downloads", "upstream_revision_request_guardrail_truthy") in issue_pairs
    assert ("publish_ready", "upstream_revision_request_guardrail_truthy") in issue_pairs
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["renderer_behavior_changed"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False


def test_renderer_revision_plan_skips_timestamp_only_rewrites(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    write_csv(
        run_dir / "adobe_visual_qa_revision_requests.csv",
        [revision_row("AVQR001", "ig_story_9x16", "Shift upper text blocks down vertically to clear the top interface safe zone.")],
        module.REVISION_REQUEST_FIELDS,
    )

    assert module.main([]) == 0

    plan_json = run_dir / "adobe_visual_qa_renderer_revision_plan.json"
    plan_md = run_dir / "adobe_visual_qa_renderer_revision_plan.md"
    spec_json = run_dir / "adobe_visual_qa_renderer_revision_spec.json"
    spec_md = run_dir / "adobe_visual_qa_renderer_revision_spec.md"
    first_plan_json = plan_json.read_text(encoding="utf-8")
    first_plan_md = plan_md.read_text(encoding="utf-8")
    first_spec_json = spec_json.read_text(encoding="utf-8")
    first_spec_md = spec_md.read_text(encoding="utf-8")

    assert module.main([]) == 0

    assert plan_json.read_text(encoding="utf-8") == first_plan_json
    assert plan_md.read_text(encoding="utf-8") == first_plan_md
    assert spec_json.read_text(encoding="utf-8") == first_spec_json
    assert spec_md.read_text(encoding="utf-8") == first_spec_md
