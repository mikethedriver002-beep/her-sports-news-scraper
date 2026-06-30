from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "import_hsd_adobe_visual_qa_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("import_hsd_adobe_visual_qa_intake_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_intake(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def blank_row(format_name: str) -> dict[str, str]:
    return {
        "format": format_name,
        "crop_fit": "operator_fill_required",
        "title_safety": "operator_fill_required",
        "score_rail_dashboard_violation": "operator_fill_required",
        "lower_stat_strip_violation": "operator_fill_required",
        "logo_readiness": "operator_fill_required",
        "action_photo_suitability": "operator_fill_required",
        "operator_decision": "operator_fill_required",
        "revision_request": "",
        "operator_notes": "",
    }


def test_importer_reads_blank_packet_intake_as_waiting_review_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    intake = run_dir / "adobe_visual_qa_packet" / "manual_adobe_visual_qa_intake.csv"
    write_intake(intake, [blank_row(format_name) for format_name in module.EXPECTED_FORMATS], module.INTAKE_FIELDS)

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "adobe_visual_qa_result_manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "adobe_visual_qa_result_report.md").read_text(encoding="utf-8")
    revisions = read_csv(run_dir / "adobe_visual_qa_revision_requests.csv")

    assert manifest["version"] == "hsd-adobe-visual-qa-intake-importer-v1-review-only"
    assert manifest["status"] == "adobe_visual_qa_waiting_for_manual_review"
    assert manifest["intake_rows"] == 4
    assert manifest["filled_manual_review_rows"] == 0
    assert manifest["pending_operator_fill_rows"] == 4
    assert manifest["revision_request_rows"] == 0
    assert manifest["validation_issue_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["paid_apis"] is False
    assert manifest["source_fetching"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert revisions == []
    assert "No automatic downloads." in report
    assert "No .approved marker writes." in report


def test_importer_writes_revision_requests_without_approval_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    intake = run_dir / "adobe_visual_qa_packet" / "manual_adobe_visual_qa_intake.csv"
    rows = [
        {
            **blank_row("ig_feed_4x5"),
            "crop_fit": "fits but lower rail feels boxed",
            "title_safety": "safe",
            "score_rail_dashboard_violation": "yes",
            "lower_stat_strip_violation": "yes",
            "logo_readiness": "manual logo review required",
            "action_photo_suitability": "would improve after quarantine review clears",
            "operator_decision": "revise",
            "revision_request": "Make score rail borderless and lighten lower stat strip.",
            "operator_notes": "Keep review-only.",
        },
        {
            **blank_row("ig_story_9x16"),
            "crop_fit": "headline crowded near top safe zone",
            "title_safety": "needs top safe-zone relief",
            "score_rail_dashboard_violation": "yes",
            "lower_stat_strip_violation": "no",
            "logo_readiness": "manual logo review required",
            "action_photo_suitability": "action photo preferred later",
            "operator_decision": "hold",
            "revision_request": "Move headline down and simplify context copy.",
            "operator_notes": "Hold until visual spacing is cleaner.",
        },
        {
            **blank_row("square_1x1"),
            "crop_fit": "acceptable",
            "title_safety": "safe",
            "score_rail_dashboard_violation": "no",
            "lower_stat_strip_violation": "no",
            "logo_readiness": "manual next step only",
            "action_photo_suitability": "neutral",
            "operator_decision": "approve_for_manual_next_step",
            "operator_notes": "No publish approval implied.",
        },
        {
            **blank_row("contact_sheet"),
            "crop_fit": "compare all formats",
            "title_safety": "story draft is crowded",
            "score_rail_dashboard_violation": "yes",
            "lower_stat_strip_violation": "yes",
            "logo_readiness": "manual logo review required",
            "action_photo_suitability": "action-photo bridge still blocked",
            "operator_decision": "revise",
            "revision_request": "Use contact sheet to prioritize borderless score and open caption rail.",
            "operator_notes": "Do not edit source images.",
        },
    ]
    write_intake(intake, rows, module.INTAKE_FIELDS)

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "adobe_visual_qa_result_manifest.json").read_text(encoding="utf-8"))
    revisions = read_csv(run_dir / "adobe_visual_qa_revision_requests.csv")
    report = (run_dir / "adobe_visual_qa_result_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "adobe_visual_qa_revision_requests_ready"
    assert manifest["filled_manual_review_rows"] == 4
    assert manifest["revision_request_rows"] == 3
    assert manifest["operator_decision_counts"] == {
        "approve_for_manual_next_step": 1,
        "hold": 1,
        "revise": 2,
    }
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["auto_approval"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert [row["format"] for row in revisions] == ["ig_feed_4x5", "ig_story_9x16", "contact_sheet"]
    assert all(row["review_only"] == "true" for row in revisions)
    assert all(row["asset_downloads"] == "false" for row in revisions)
    assert all(row["approval_state_change"] == "false" for row in revisions)
    assert all(row["publish_ready"] == "false" for row in revisions)
    assert "AVQR001" in report
    assert "No image edits." in report


def test_importer_blocks_invalid_decisions_and_missing_required_shape(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    intake = run_dir / "adobe_visual_qa_packet" / "manual_adobe_visual_qa_intake.csv"
    fields = [field for field in module.INTAKE_FIELDS if field != "operator_notes"]
    rows = [
        {
            key: value
            for key, value in {
                **blank_row("ig_feed_4x5"),
                "operator_decision": "approved",
            }.items()
            if key in fields
        },
        {
            key: value
            for key, value in {
                **blank_row("ig_feed_4x5"),
                "operator_decision": "revise",
                "revision_request": "",
            }.items()
            if key in fields
        },
        {
            key: value
            for key, value in {
                **blank_row("wrong_format"),
                "operator_decision": "hold",
            }.items()
            if key in fields
        },
    ]
    write_intake(intake, rows, fields)

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "adobe_visual_qa_result_manifest.json").read_text(encoding="utf-8"))
    issue_pairs = {(issue["field"], issue["issue"]) for issue in manifest["validation_issues"]}

    assert manifest["status"] == "adobe_visual_qa_intake_has_validation_issues"
    assert ("operator_notes", "required_field_missing") in issue_pairs
    assert ("operator_decision", "operator_decision_not_allowed") in issue_pairs
    assert ("revision_request", "revise_decision_requires_revision_request") in issue_pairs
    assert ("format", "duplicate_format") in issue_pairs
    assert ("format", "unexpected_format") in issue_pairs
    assert ("format", "expected_format_missing") in issue_pairs
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
