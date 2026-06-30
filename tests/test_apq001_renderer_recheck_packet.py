from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apq001_renderer_recheck_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apq001_renderer_recheck_packet_v1", SCRIPT)
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


def source_manifest(**overrides) -> dict:
    payload = {
        "status": "apq001_manual_review_result_artifacts_ready",
        "candidate_queue_id": "APQ001",
        "finding_rows": 3,
        "validation_issue_count": 0,
        "renderer_handoff_recommendation_counts": {
            "needs_crop_or_layout_notes": 1,
            "operator_fill_required": 3,
            "suitable_for_renderer_recheck": 1,
        },
        "review_only": True,
        "artifact_only": True,
        "image_edits": False,
        "new_downloads": False,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "headshot_writes": False,
        "renderer_behavior_change": False,
        "publish_ready": False,
        "publishing": False,
        "move_files": False,
    }
    payload.update(overrides)
    return payload


def finding_row(finding_id: str, review_step: str, **overrides: str) -> dict[str, str]:
    row = {
        "finding_id": finding_id,
        "source_csv": "apq001_manual_asset_review_packet/renderer_handoff_review_checklist.csv",
        "review_step": review_step,
        "candidate_queue_id": "APQ001",
        "operator_decision": "",
        "operator_finding": "",
        "renderer_handoff_recommendation": "",
        "revision_request": "",
        "operator_notes": "",
        "reviewed_by": "",
        "reviewed_at_local": "",
        "review_only": "true",
        "artifact_only": "true",
        "image_edits": "false",
        "new_downloads": "false",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "approved_marker_writes": "false",
        "headshot_writes": "false",
        "renderer_behavior_change": "false",
        "publish_ready": "false",
        "publishing": "false",
        "move_files": "false",
    }
    row.update(overrides)
    return row


def seed_sources(run_dir: Path, module, manifest: dict | None = None, rows: list[dict[str, str]] | None = None) -> None:
    write_json(run_dir / "apq001_manual_review_result_manifest.json", manifest or source_manifest())
    write_csv(
        run_dir / "apq001_manual_review_result_findings.csv",
        rows
        if rows is not None
        else [
            finding_row(
                "APQMR001",
                "manual_asset_review",
                source_csv="apq001_manual_asset_review_packet/manual_asset_review_intake.csv",
                operator_decision="suitable_for_renderer_handoff_review",
                operator_notes="guardrail_passed=true from Mike shorthand intake",
                reviewed_by="Mike",
                reviewed_at_local="2026-06-30T15:25:31-04:00",
            ),
            finding_row(
                "APQMR002",
                "square_crop_fit",
                operator_finding="initial_framing",
                renderer_handoff_recommendation="needs_crop_or_layout_notes",
                operator_notes="override_applied=false from Mike shorthand intake",
            ),
            finding_row(
                "APQMR003",
                "feed_crop_fit",
                operator_finding="image_clarity",
                renderer_handoff_recommendation="suitable_for_renderer_recheck",
                operator_notes="override_applied=false from Mike shorthand intake",
            ),
        ],
        module.FINDING_FIELDS,
    )


def test_builds_apq001_renderer_recheck_packet_from_manual_review_results(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir, module)

    assert module.main([]) == 0

    packet = run_dir / "apq001_renderer_recheck_packet"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    readme = (packet / "README.md").read_text(encoding="utf-8")
    handoff = (packet / "renderer_recheck_handoff.md").read_text(encoding="utf-8")
    plan_rows = read_csv(packet / "renderer_recheck_plan.csv")
    checklist_rows = read_csv(packet / "renderer_recheck_checklist.csv")

    assert manifest["version"] == "hsd-apq001-renderer-recheck-packet-v1-review-only"
    assert manifest["status"] == "apq001_renderer_recheck_packet_ready"
    assert manifest["source_finding_rows"] == 3
    assert manifest["plan_rows"] == 3
    assert manifest["checklist_rows"] == 4
    assert manifest["validation_issue_count"] == 0
    assert manifest["pending_operator_fill_required_rows"] == 3
    assert manifest["priority_counts"] == {"P0": 1, "P1": 2}
    assert manifest["renderer_recheck_area_counts"] == {
        "action_photo_crop_layout_notes": 1,
        "action_photo_renderer_recheck": 1,
        "manual_asset_review_gate": 1,
    }
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

    assert [row["renderer_recheck_area"] for row in plan_rows] == [
        "manual_asset_review_gate",
        "action_photo_crop_layout_notes",
        "action_photo_renderer_recheck",
    ]
    assert [row["priority"] for row in plan_rows] == ["P1", "P0", "P1"]
    assert all(row["candidate_quarantine_path"].endswith("apq001_review_only_candidate.jpg") for row in plan_rows)
    assert all(row["review_only"] == "true" for row in plan_rows)
    assert all(row["artifact_only"] == "true" for row in plan_rows)
    assert all(row["image_edits"] == "false" for row in plan_rows)
    assert all(row["new_downloads"] == "false" for row in plan_rows)
    assert all(row["asset_downloads"] == "false" for row in plan_rows)
    assert all(row["approval_state_change"] == "false" for row in plan_rows)
    assert all(row["approved_marker_writes"] == "false" for row in plan_rows)
    assert all(row["renderer_behavior_change"] == "false" for row in plan_rows)
    assert all(row["publish_ready"] == "false" for row in plan_rows)
    assert any(row["check_type"] == "quarantine_boundary" for row in checklist_rows)
    assert all(row["asset_downloads"] == "false" for row in checklist_rows)
    assert "does not approve APQ001" in readme
    assert "Do not copy it into renderer, headshot, approved, or publish-ready folders." in readme
    assert "APQ001 remains a quarantine-only review candidate" in handoff
    assert "renderer_behavior_change=false" in handoff


def test_renderer_recheck_packet_waits_when_manual_review_has_no_findings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(
        run_dir,
        module,
        manifest=source_manifest(status="apq001_manual_review_waiting_for_filled_packet", finding_rows=0),
        rows=[],
    )

    assert module.main([]) == 0

    packet = run_dir / "apq001_renderer_recheck_packet"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    plan_rows = read_csv(packet / "renderer_recheck_plan.csv")
    checklist_rows = read_csv(packet / "renderer_recheck_checklist.csv")

    assert manifest["status"] == "apq001_renderer_recheck_packet_waiting_for_manual_review_findings"
    assert manifest["source_finding_rows"] == 0
    assert manifest["plan_rows"] == 0
    assert manifest["checklist_rows"] == 0
    assert manifest["validation_issue_count"] == 0
    assert plan_rows == []
    assert checklist_rows == []
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False


def test_renderer_recheck_packet_blocks_guardrail_drift(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(
        run_dir,
        module,
        manifest=source_manifest(asset_downloads=True),
        rows=[
            finding_row(
                "APQMR001",
                "manual_asset_review",
                operator_decision="approved",
                asset_downloads="true",
                publish_ready="true",
                renderer_behavior_change="true",
            )
        ],
    )

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "apq001_renderer_recheck_packet" / "manifest.json").read_text(encoding="utf-8"))
    issue_pairs = {(issue.get("field"), issue.get("issue")) for issue in manifest["validation_issues"]}
    plan_rows = read_csv(run_dir / "apq001_renderer_recheck_packet" / "renderer_recheck_plan.csv")

    assert manifest["status"] == "apq001_renderer_recheck_packet_has_validation_issues"
    assert ("asset_downloads", "source_manifest_guardrail_truthy") in issue_pairs
    assert ("asset_downloads", "finding_guardrail_field_must_be_false") in issue_pairs
    assert ("publish_ready", "finding_guardrail_field_must_be_false") in issue_pairs
    assert ("renderer_behavior_change", "finding_guardrail_field_must_be_false") in issue_pairs
    assert ("operator_decision", "forbidden_approval_or_publish_value") in issue_pairs
    assert plan_rows == []
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False


def test_renderer_recheck_packet_reports_missing_manual_review_results(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "apq001_renderer_recheck_packet" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "apq001_renderer_recheck_packet_missing_manual_review_results"
    assert manifest["validation_issue_count"] == 2
    assert manifest["plan_rows"] == 0
    assert manifest["checklist_rows"] == 0
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publishing"] is False
