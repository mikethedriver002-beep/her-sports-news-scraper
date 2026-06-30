from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "import_hsd_apq001_manual_review_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("import_hsd_apq001_manual_review_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def manual_row(**overrides: str) -> dict[str, str]:
    row = {
        "review_step": "manual_asset_review",
        "candidate_queue_id": "APQ001",
        "candidate_packet_path": "candidate/apq001_review_only_candidate.jpg",
        "quarantine_source_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg",
        "identity_match": "operator_fill_required",
        "action_photo_quality": "operator_fill_required",
        "rights_review": "operator_fill_required",
        "crop_fit_square_1x1": "operator_fill_required",
        "crop_fit_feed_4x5": "operator_fill_required",
        "crop_fit_story_9x16": "operator_fill_required",
        "operator_decision": "operator_fill_required",
        "operator_notes": "",
        "reviewed_by": "",
        "reviewed_at_local": "",
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "move_files": "false",
        "publishing": "false",
    }
    row.update(overrides)
    return row


def handoff_row(step: str, recommendation: str = "operator_fill_required", finding: str = "operator_fill_required", **overrides: str) -> dict[str, str]:
    row = {
        "review_step": step,
        "candidate_queue_id": "APQ001",
        "candidate_packet_path": "candidate/apq001_review_only_candidate.jpg",
        "renderer_handoff_question": f"Question for {step}?",
        "operator_finding": finding,
        "renderer_handoff_recommendation": recommendation,
        "revision_request": "",
        "operator_notes": "",
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "false",
        "renderer_behavior_change": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "move_files": "false",
        "publishing": "false",
    }
    row.update(overrides)
    return row


def seed_packet(run_dir: Path, module, manual_rows: list[dict[str, str]], handoff_rows: list[dict[str, str]]) -> None:
    packet = run_dir / "apq001_manual_asset_review_packet"
    write_csv(packet / "manual_asset_review_intake.csv", manual_rows, module.MANUAL_FIELDS)
    write_csv(packet / "renderer_handoff_review_checklist.csv", handoff_rows, module.HANDOFF_FIELDS)


def test_imports_filled_apq001_packet_as_review_only_result_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_packet(
        run_dir,
        module,
        [
            manual_row(
                identity_match="not_supplied_in_shorthand",
                action_photo_quality="not_supplied_in_shorthand",
                rights_review="not_supplied_in_shorthand",
                crop_fit_square_1x1="not_supplied_in_shorthand",
                crop_fit_feed_4x5="not_supplied_in_shorthand",
                crop_fit_story_9x16="not_supplied_in_shorthand",
                operator_decision="suitable_for_renderer_handoff_review",
                operator_notes="guardrail_passed=true from Mike shorthand intake",
                reviewed_by="Mike",
                reviewed_at_local="2026-06-30T15:25:31-04:00",
            )
        ],
        [
            handoff_row("identity_context", recommendation="operator_fill_required", finding="not_supplied_in_shorthand"),
            handoff_row(
                "square_crop_fit",
                recommendation="needs_crop_or_layout_notes",
                finding="initial_framing",
                operator_notes="override_applied=false from Mike shorthand intake",
            ),
            handoff_row(
                "feed_crop_fit",
                recommendation="suitable_for_renderer_recheck",
                finding="image_clarity",
                operator_notes="override_applied=false from Mike shorthand intake",
            ),
            handoff_row("story_crop_fit"),
            handoff_row("renderer_bridge"),
        ],
    )

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "apq001_manual_review_result_manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "apq001_manual_review_result_report.md").read_text(encoding="utf-8")
    findings = read_csv(run_dir / "apq001_manual_review_result_findings.csv")

    assert manifest["version"] == "hsd-apq001-manual-review-importer-v1-review-only"
    assert manifest["status"] == "apq001_manual_review_result_artifacts_ready"
    assert manifest["manual_asset_review_rows"] == 1
    assert manifest["renderer_handoff_rows"] == 5
    assert manifest["finding_rows"] == 3
    assert manifest["validation_issue_count"] == 0
    assert manifest["manual_operator_decision_counts"]["suitable_for_renderer_handoff_review"] == 1
    assert manifest["renderer_handoff_recommendation_counts"]["needs_crop_or_layout_notes"] == 1
    assert manifest["renderer_handoff_recommendation_counts"]["suitable_for_renderer_recheck"] == 1
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["image_edits"] is False
    assert manifest["new_downloads"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False
    assert [row["finding_id"] for row in findings] == ["APQMR001", "APQMR002", "APQMR003"]
    assert findings[0]["operator_decision"] == "suitable_for_renderer_handoff_review"
    assert findings[1]["renderer_handoff_recommendation"] == "needs_crop_or_layout_notes"
    assert findings[2]["renderer_handoff_recommendation"] == "suitable_for_renderer_recheck"
    assert all(row["review_only"] == "true" for row in findings)
    assert all(row["approval_state_change"] == "false" for row in findings)
    assert all(row["publish_ready"] == "false" for row in findings)
    assert "does not approve the asset" in report
    assert "No renderer behavior changes." in report


def test_importer_waits_when_packet_has_no_filled_review(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_packet(
        run_dir,
        module,
        [manual_row()],
        [handoff_row("identity_context"), handoff_row("square_crop_fit")],
    )

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "apq001_manual_review_result_manifest.json").read_text(encoding="utf-8"))
    findings = read_csv(run_dir / "apq001_manual_review_result_findings.csv")

    assert manifest["status"] == "apq001_manual_review_waiting_for_filled_packet"
    assert manifest["finding_rows"] == 0
    assert manifest["validation_issue_count"] == 0
    assert findings == []
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False


def test_importer_blocks_approval_and_publish_guardrail_drift(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_packet(
        run_dir,
        module,
        [
            manual_row(
                candidate_queue_id="WRONG",
                operator_decision="approved",
                review_only="false",
                publish_ready="true",
                approval_state_change="true",
                approved_marker_writes="true",
            )
        ],
        [
            handoff_row(
                "identity_context",
                recommendation="render_ready",
                renderer_behavior_change="true",
                move_files="true",
            )
        ],
    )

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "apq001_manual_review_result_manifest.json").read_text(encoding="utf-8"))
    issue_pairs = {(issue["field"], issue["issue"]) for issue in manifest["validation_issues"]}

    assert manifest["status"] == "apq001_manual_review_import_has_validation_issues"
    assert ("candidate_queue_id", "unexpected_candidate_queue_id") in issue_pairs
    assert ("operator_decision", "operator_decision_not_allowed") in issue_pairs
    assert ("operator_decision", "forbidden_approval_or_publish_value") in issue_pairs
    assert ("review_only", "review_only_must_be_true") in issue_pairs
    assert ("publish_ready", "guardrail_field_must_be_false") in issue_pairs
    assert ("approval_state_change", "guardrail_field_must_be_false") in issue_pairs
    assert ("approved_marker_writes", "guardrail_field_must_be_false") in issue_pairs
    assert ("renderer_handoff_recommendation", "renderer_handoff_recommendation_not_allowed") in issue_pairs
    assert ("renderer_handoff_recommendation", "forbidden_approval_or_publish_value") in issue_pairs
    assert ("renderer_behavior_change", "renderer_behavior_change_must_be_false") in issue_pairs
    assert ("move_files", "guardrail_field_must_be_false") in issue_pairs
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
