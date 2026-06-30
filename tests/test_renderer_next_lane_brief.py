from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_renderer_next_lane_brief_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_renderer_next_lane_brief_v1", SCRIPT)
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


def adobe_manifest(**overrides) -> dict:
    payload = {
        "status": "adobe_visual_qa_renderer_revision_spec_ready",
        "review_only": True,
        "artifact_only": True,
        "spec_rows": 2,
        "validation_issue_count": 0,
        "image_edits": False,
        "new_downloads": False,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "headshot_writes": False,
        "renderer_behavior_changed": False,
        "publish_ready": False,
        "publishing": False,
        "move_files": False,
    }
    payload.update(overrides)
    return payload


def apq001_manifest(**overrides) -> dict:
    payload = {
        "status": "apq001_renderer_recheck_packet_ready",
        "review_only": True,
        "artifact_only": True,
        "plan_rows": 2,
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
    }
    payload.update(overrides)
    return payload


def adobe_row(spec_id: str, priority: str, area: str, title: str) -> dict[str, str]:
    return {
        "spec_id": spec_id,
        "source_plan_id": spec_id.replace("RS", "RP"),
        "source_revision_id": spec_id.replace("RS", "R"),
        "priority": priority,
        "format": "ig_story_9x16" if area == "story_title_safe_zone" else "square_1x1",
        "renderer_area": area,
        "source_issue_bucket": "score_rail_dashboard_violation",
        "implementation_task": title,
        "revision_spec": f"Review-only task for {title}.",
        "acceptance_check": f"Future rerender passes {title}.",
        "verification_artifact": "adobe_visual_qa_packet/drafts/draft_preview_story.png",
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


def apq001_row(plan_id: str, priority: str, area: str) -> dict[str, str]:
    return {
        "plan_id": plan_id,
        "source_finding_id": plan_id.replace("RR", "MR"),
        "candidate_queue_id": "APQ001",
        "review_step": "square_crop_fit",
        "priority": priority,
        "renderer_recheck_area": area,
        "source_operator_decision": "",
        "source_operator_finding": "initial_framing",
        "source_renderer_handoff_recommendation": "needs_crop_or_layout_notes",
        "planning_note": f"Plan APQ001 {area}.",
        "acceptance_check": f"Future APQ001 recheck covers {area}.",
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


def seed_inputs(run_dir: Path, module, *, unsafe: bool = False) -> None:
    write_json(run_dir / "adobe_visual_qa_renderer_revision_spec.json", adobe_manifest(asset_downloads=unsafe))
    write_csv(
        run_dir / "adobe_visual_qa_renderer_revision_spec.csv",
        [
            adobe_row("AVQRS001", "P0", "story_title_safe_zone", "Story safe-zone offset"),
            adobe_row("AVQRS002", "P0", "square_score_grid", "Square score-grid deboxing"),
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
    apq_dir = run_dir / "apq001_renderer_recheck_packet"
    write_json(apq_dir / "manifest.json", apq001_manifest())
    apq_rows = [
        apq001_row("APQRR001", "P0", "action_photo_crop_layout_notes"),
        apq001_row("APQRR002", "P1", "action_photo_renderer_recheck"),
    ]
    if unsafe:
        apq_rows[0]["publish_ready"] = "true"
        apq_rows[0]["renderer_behavior_change"] = "true"
    write_csv(apq_dir / "renderer_recheck_plan.csv", apq_rows, module.QUEUE_FIELDS[:0] or [
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
    ])


def test_builds_renderer_next_lane_brief(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_inputs(run_dir, module)

    assert module.main([]) == 0

    out = run_dir / "renderer_next_lane_brief"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    readme = (out / "README.md").read_text(encoding="utf-8")
    prompt = (out / "next_prompt_to_send_codex.md").read_text(encoding="utf-8")
    queue = read_csv(out / "next_renderer_lane_task_queue.csv")
    checklist = read_csv(out / "next_renderer_lane_guardrail_checklist.csv")

    assert manifest["version"] == "hsd-renderer-next-lane-brief-v1-review-only"
    assert manifest["status"] == "renderer_next_lane_brief_ready"
    assert manifest["adobe_spec_rows"] == 2
    assert manifest["apq001_plan_rows"] == 2
    assert manifest["task_queue_rows"] == 4
    assert manifest["guardrail_checklist_rows"] == 4
    assert manifest["validation_issue_count"] == 0
    assert manifest["priority_counts"] == {"P0": 3, "P1": 1}
    assert manifest["source_packet_counts"] == {
        "adobe_renderer_revision_spec": 2,
        "apq001_renderer_recheck_packet": 2,
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

    assert [row["task_id"] for row in queue] == ["RNL001", "RNL002", "RNL003", "RNL004"]
    assert queue[0]["source_packet"] == "adobe_renderer_revision_spec"
    assert queue[2]["source_packet"] == "apq001_renderer_recheck_packet"
    assert all(row["review_only"] == "true" for row in queue)
    assert all(row["artifact_only"] == "true" for row in queue)
    assert all(row["asset_downloads"] == "false" for row in queue)
    assert all(row["renderer_behavior_change"] == "false" for row in queue)
    assert all(row["publish_ready"] == "false" for row in queue)
    assert len(checklist) == 4
    assert "does not edit renderer behavior" in readme
    assert "Next Prompt To Send Codex" in prompt
    assert "story title safe-zone offset and square score-grid deboxing" in prompt


def test_renderer_next_lane_brief_reports_missing_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 1

    out = run_dir / "renderer_next_lane_brief"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    queue = read_csv(out / "next_renderer_lane_task_queue.csv")

    assert manifest["status"] == "renderer_next_lane_brief_missing_inputs"
    assert manifest["task_queue_rows"] == 0
    assert manifest["validation_issue_count"] >= 3
    assert queue == []
    assert manifest["asset_downloads"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publishing"] is False


def test_renderer_next_lane_brief_blocks_unsafe_upstream_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_inputs(run_dir, module, unsafe=True)

    assert module.main([]) == 1

    out = run_dir / "renderer_next_lane_brief"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    queue = read_csv(out / "next_renderer_lane_task_queue.csv")
    issue_pairs = {(issue.get("field"), issue.get("issue")) for issue in manifest["validation_issues"]}

    assert manifest["status"] == "renderer_next_lane_brief_has_validation_issues"
    assert ("asset_downloads", "source_manifest_guardrail_truthy") in issue_pairs
    assert ("publish_ready", "row_guardrail_field_must_be_false") in issue_pairs
    assert ("renderer_behavior", "row_renderer_behavior_must_be_false") in issue_pairs
    assert queue == []
    assert manifest["asset_downloads"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False
