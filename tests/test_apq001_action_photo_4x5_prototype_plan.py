from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apq001_action_photo_4x5_prototype_plan_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apq001_action_photo_4x5_prototype_plan_v1", SCRIPT)
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


def seed_sources(run_dir: Path) -> None:
    write_json(
        run_dir / "apq001_manual_review_result_manifest.json",
        {
            "status": "apq001_manual_review_result_artifacts_ready",
            "candidate_queue_id": "APQ001",
            "review_only": True,
            "artifact_only": True,
            "validation_issue_count": 0,
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
        },
    )
    (run_dir / "apq001_manual_review_result_report.md").write_text(
        "# APQ001 Manual Review Result\n\nReview-only.\n",
        encoding="utf-8",
    )
    write_json(
        run_dir / "apq001_renderer_recheck_packet" / "manifest.json",
        {
            "status": "apq001_renderer_recheck_packet_ready",
            "review_only": True,
            "artifact_only": True,
            "validation_issue_count": 0,
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
        },
    )
    write_csv(
        run_dir / "apq001_renderer_recheck_packet" / "renderer_recheck_plan.csv",
        [
            {
                "plan_id": "APQRR001",
                "source_finding_id": "APQMR001",
                "candidate_queue_id": "APQ001",
                "review_step": "manual_asset_review",
                "priority": "P1",
                "renderer_recheck_area": "action_photo_renderer_recheck",
                "source_operator_decision": "suitable_for_renderer_handoff_review",
                "source_operator_finding": "action anchor intact",
                "source_renderer_handoff_recommendation": "suitable_for_renderer_recheck",
                "planning_note": "Use APQ001 as a quarantine-only review candidate.",
                "acceptance_check": "Future lane keeps APQ001 review-only.",
                "next_manual_action": "Keep APQ001 quarantine-only.",
                "candidate_quarantine_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg",
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
        ],
        [
            "plan_id",
            "source_finding_id",
            "candidate_queue_id",
            "review_step",
            "priority",
            "renderer_recheck_area",
            "source_operator_decision",
            "source_operator_finding",
            "source_renderer_handoff_recommendation",
            "planning_note",
            "acceptance_check",
            "next_manual_action",
            "candidate_quarantine_path",
            "review_only",
            "artifact_only",
            "image_edits",
            "new_downloads",
            "asset_downloads",
            "approval_state_change",
            "approved_marker_writes",
            "headshot_writes",
            "renderer_behavior_change",
            "publish_ready",
            "publishing",
            "move_files",
        ],
    )
    write_csv(
        run_dir / "adobe_visual_qa_renderer_revision_spec.csv",
        [
            {
                "spec_id": "AVQRS001",
                "source_plan_id": "AVQRP001",
                "source_revision_id": "AVQR001",
                "priority": "P0",
                "format": "ig_feed_4x5",
                "renderer_area": "score_rail_typography",
                "source_issue_bucket": "score_rail_dashboard_violation",
                "implementation_task": "Score rail typography pass",
                "revision_spec": "Plan a review-only 4:5 score rail pass.",
                "acceptance_check": "Future rerender reads as editorial sports design.",
                "verification_artifact": "adobe_visual_qa_packet/drafts/draft_preview_ig_feed.png",
                "next_manual_action": "Use this in a separate renderer implementation lane.",
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "image_edits": "false",
                "renderer_behavior_changed": "false",
                "approval_state_change": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "publishing": "false",
                "move_files": "false",
            }
        ],
        [
            "spec_id",
            "source_plan_id",
            "source_revision_id",
            "priority",
            "format",
            "renderer_area",
            "source_issue_bucket",
            "implementation_task",
            "revision_spec",
            "acceptance_check",
            "verification_artifact",
            "next_manual_action",
            "review_only",
            "artifact_only",
            "asset_downloads",
            "image_edits",
            "renderer_behavior_changed",
            "approval_state_change",
            "approved_marker_writes",
            "publish_ready",
            "publishing",
            "move_files",
        ],
    )
    write_csv(
        run_dir / "renderer_next_lane_brief" / "next_renderer_lane_task_queue.csv",
        [
            {
                "task_id": "RNL001",
                "source_packet": "apq001_renderer_recheck_packet",
                "source_id": "APQRR001",
                "priority": "P1",
                "renderer_area": "action_photo_renderer_recheck",
                "task_title": "Action Photo Renderer Recheck",
                "task_summary": "Use APQ001 as a quarantine-only input.",
                "acceptance_check": "Keep the candidate in quarantine.",
                "verification_artifact": "apq001_renderer_recheck_packet/renderer_recheck_plan.csv",
                "next_manual_action": "Do not edit or move the asset.",
                "candidate_quarantine_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg",
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
        ],
        [
            "task_id",
            "source_packet",
            "source_id",
            "priority",
            "renderer_area",
            "task_title",
            "task_summary",
            "acceptance_check",
            "verification_artifact",
            "next_manual_action",
            "candidate_quarantine_path",
            "review_only",
            "artifact_only",
            "image_edits",
            "new_downloads",
            "asset_downloads",
            "approval_state_change",
            "approved_marker_writes",
            "headshot_writes",
            "renderer_behavior_change",
            "publish_ready",
            "publishing",
            "move_files",
        ],
    )
    (run_dir / "render_handoff_top_packet" / "review_drafts").mkdir(parents=True, exist_ok=True)
    (run_dir / "render_handoff_top_packet" / "review_drafts" / "draft_preview_ig_feed.png").write_bytes(b"preview-bytes")


def test_builds_apq001_action_photo_4x5_prototype_plan(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir)

    assert module.main([]) == 0

    out = run_dir / "apq001_action_photo_4x5_prototype_plan"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    readme = (out / "README.md").read_text(encoding="utf-8")
    plan_rows = read_csv(out / "prototype_plan.csv")
    checklist_rows = read_csv(out / "prototype_checklist.csv")

    assert manifest["version"] == "hsd-apq001-action-photo-4x5-prototype-plan-v1-review-only"
    assert manifest["status"] == "apq001_action_photo_4x5_prototype_plan_ready"
    assert manifest["manual_review_manifest_status"] == "apq001_manual_review_result_artifacts_ready"
    assert manifest["manual_review_report_present"] is True
    assert manifest["recheck_plan_rows"] == 1
    assert manifest["adobe_spec_rows"] == 1
    assert manifest["task_queue_rows"] == 1
    assert manifest["preview_reference_path"] == "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png"
    assert manifest["preview_reference_present"] is True
    assert manifest["prototype_plan_rows"] == 1
    assert manifest["checklist_rows"] == 5
    assert manifest["validation_issue_count"] == 0
    assert manifest["handoff_status"] == "quarantine_review_lock"
    assert manifest["auto_publish"] is False
    assert manifest["apq001_quarantine_image_path"].endswith("apq001_review_only_candidate.jpg")
    assert manifest["burn_in_label"] == "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER"
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
    assert plan_rows[0]["prototype_id"] == "APQ4X5-001"
    assert plan_rows[0]["prototype_mode"] == "metadata_only_annotated_plan"
    assert plan_rows[0]["handoff_status"] == "quarantine_review_lock"
    assert plan_rows[0]["apq001_quarantine_image_path"].endswith("apq001_review_only_candidate.jpg")
    assert plan_rows[0]["burn_in_label"] == "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER"
    assert plan_rows[0]["candidate_quarantine_path"].endswith("apq001_review_only_candidate.jpg")
    assert plan_rows[0]["review_only"] == "true"
    assert plan_rows[0]["artifact_only"] == "true"
    assert plan_rows[0]["image_edits"] == "false"
    assert plan_rows[0]["new_downloads"] == "false"
    assert plan_rows[0]["asset_downloads"] == "false"
    assert plan_rows[0]["approval_state_change"] == "false"
    assert plan_rows[0]["approved_marker_writes"] == "false"
    assert plan_rows[0]["renderer_behavior_change"] == "false"
    assert plan_rows[0]["publish_ready"] == "false"
    assert plan_rows[0]["publishing"] == "false"
    assert plan_rows[0]["move_files"] == "false"
    assert len(checklist_rows) == 5
    assert all(row["review_only"] == "true" for row in checklist_rows)
    assert all(row["artifact_only"] == "true" for row in checklist_rows)
    assert all(row["asset_downloads"] == "false" for row in checklist_rows)
    assert all(row["renderer_behavior_change"] == "false" for row in checklist_rows)
    assert "metadata-only" in readme
    assert "Do not edit the quarantine candidate" in readme
    assert "No image edits" in readme
    assert "No .approved markers" in readme
    assert "quarantine_review_lock" in readme
    assert "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER" in readme
    assert "dynamic action-photo crop or full-bleed treatment" in readme
    assert "debox the score rail into raw high-contrast typography" in readme
    assert "middle dots instead of slashes" in readme
    assert "apq001_quarantine_image_path" in readme


def test_apq001_action_photo_4x5_prototype_plan_reports_missing_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "apq001_action_photo_4x5_prototype_plan" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "apq001_action_photo_4x5_prototype_plan_missing_inputs"
    assert manifest["validation_issue_count"] >= 1
    assert manifest["review_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False


def test_apq001_action_photo_4x5_prototype_plan_blocks_guardrail_drift(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir)
    write_json(
        run_dir / "apq001_manual_review_result_manifest.json",
        {
            "status": "apq001_manual_review_result_artifacts_ready",
            "candidate_queue_id": "APQ001",
            "review_only": True,
            "artifact_only": True,
            "validation_issue_count": 0,
            "asset_downloads": True,
            "image_edits": False,
            "new_downloads": False,
            "approval_state_change": False,
            "approved_marker_writes": False,
            "headshot_writes": False,
            "renderer_behavior_change": False,
            "publish_ready": False,
            "publishing": False,
            "move_files": False,
        },
    )

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "apq001_action_photo_4x5_prototype_plan" / "manifest.json").read_text(encoding="utf-8"))
    issue_pairs = {(issue.get("field"), issue.get("issue")) for issue in manifest["validation_issues"]}

    assert manifest["status"] == "apq001_action_photo_4x5_prototype_plan_has_validation_issues"
    assert ("asset_downloads", "source_manifest_guardrail_truthy") in issue_pairs
    assert manifest["asset_downloads"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False


def test_apq001_action_photo_4x5_prototype_plan_skips_timestamp_only_rewrites(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_sources(run_dir)

    assert module.main([]) == 0

    out = run_dir / "apq001_action_photo_4x5_prototype_plan"
    manifest_path = out / "manifest.json"
    readme_path = out / "README.md"
    plan_path = out / "prototype_plan.csv"
    checklist_path = out / "prototype_checklist.csv"
    first_manifest = manifest_path.read_text(encoding="utf-8")
    first_readme = readme_path.read_text(encoding="utf-8")
    first_plan = plan_path.read_text(encoding="utf-8")
    first_checklist = checklist_path.read_text(encoding="utf-8")

    assert module.main([]) == 0

    assert manifest_path.read_text(encoding="utf-8") == first_manifest
    assert readme_path.read_text(encoding="utf-8") == first_readme
    assert plan_path.read_text(encoding="utf-8") == first_plan
    assert checklist_path.read_text(encoding="utf-8") == first_checklist
