from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_post_approval_render_staging_v1.py"


def write_intake(
    run_dir: Path,
    *,
    decision: str = "operator_fill_required",
    hold_count: str = "0",
    qa_status: str = "human_review_required",
    approval_scope: str = "manual_next_step_only_not_publish_ready",
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(b"fake png path for staging only")
    intake_path = run_dir / "manual_visual_qa_approval_intake.csv"
    with intake_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "intake_id",
                "preview_path",
                "qa_status",
                "automated_hold_count",
                "qa_report_path",
                "qa_manifest_path",
                "qa_checklist_path",
                "allowed_decisions",
                "operator_decision",
                "operator_notes",
                "operator_name",
                "reviewed_at_local",
                "required_evidence",
                "next_manual_step",
                "approval_scope",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "paid_apis",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "intake_id": "manual_visual_qa_preview_1",
                "preview_path": preview.as_posix(),
                "qa_status": qa_status,
                "automated_hold_count": hold_count,
                "qa_report_path": (run_dir / "manual_visual_qa_report.md").as_posix(),
                "qa_manifest_path": (run_dir / "manual_visual_qa_manifest.json").as_posix(),
                "qa_checklist_path": (run_dir / "manual_visual_qa_checklist.csv").as_posix(),
                "allowed_decisions": "approve_for_manual_next_step|hold|revise",
                "operator_decision": decision,
                "operator_notes": "Reviewed by operator.",
                "operator_name": "Test Operator",
                "reviewed_at_local": "2026-06-25 09:45",
                "required_evidence": "Open draft_preview.png.",
                "next_manual_step": "Manual next step only.",
                "approval_scope": approval_scope,
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "paid_apis": "false",
            }
        )
    (run_dir / "manual_visual_qa_approval_intake.json").write_text(
        json.dumps({"status": "ready_for_manual_decision", "guardrails": {"publish_ready": False, "auto_publish": False}}),
        encoding="utf-8",
    )


def run_staging(tmp_path: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    return subprocess.run(
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def read_outputs(run_dir: Path) -> tuple[dict, dict, str]:
    manifest = json.loads((run_dir / "manual_post_approval_render_staging.json").read_text(encoding="utf-8"))
    row = next(csv.DictReader((run_dir / "manual_post_approval_render_staging.csv").open(newline="", encoding="utf-8")))
    report = (run_dir / "manual_post_approval_render_staging.md").read_text(encoding="utf-8")
    return manifest, row, report


def test_manual_post_approval_render_staging_allows_only_next_manual_step(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_intake(run_dir, decision="approve_for_manual_next_step")

    proc = run_staging(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, row, report = read_outputs(run_dir)
    assert manifest["status"] == "review_only_staging_ready"
    assert manifest["approval_status"] == "not_approved_review_only_staging"
    assert row["staging_lane"] == "approved_for_next_manual_step"
    assert row["move_files"] == "false"
    assert row["copy_to_publish_lane"] == "false"
    assert row["publish_ready"] == "false"
    assert row["auto_approval"] == "false"
    assert row["auto_publish"] == "false"
    assert "do not move files" in row["next_safe_action"]
    assert "does not move files" in report
    assert manifest["guardrails"]["publish_ready"] is False


def test_manual_post_approval_render_staging_prefers_validated_operator_decision(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_intake(run_dir)
    with (run_dir / "manual_visual_qa_operator_decision_intake.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "intake_id",
                "decision_draft_id",
                "source_intake_id",
                "preview_path",
                "qa_status",
                "automated_hold_count",
                "operator_decision",
                "validation_status",
                "validation_issue",
                "operator_notes",
                "hold_reason",
                "revision_request",
                "operator_name",
                "reviewed_at_local",
                "approval_scope",
                "source_decision_path",
                "source_draft_path",
                "source_qa_report_path",
                "copy_to_publish_lane",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "intake_id": "manual_visual_qa_preview_1",
                "decision_draft_id": "decision_draft_manual_visual_qa_preview_1",
                "source_intake_id": "manual_visual_qa_preview_1",
                "preview_path": (run_dir / "render_handoff_top_packet" / "draft_preview.png").as_posix(),
                "qa_status": "human_review_required",
                "automated_hold_count": "0",
                "operator_decision": "approve_for_manual_next_step",
                "validation_status": "valid_operator_decision",
                "validation_issue": "",
                "operator_notes": "Human checked.",
                "hold_reason": "",
                "revision_request": "",
                "operator_name": "Test Operator",
                "reviewed_at_local": "2026-06-25 10:15",
                "approval_scope": "manual_next_step_only_not_publish_ready",
                "source_decision_path": "operator/inbox/manual_visual_qa_operator_decisions.csv",
                "source_draft_path": "manual_visual_qa_operator_decision_draft.csv",
                "source_qa_report_path": "manual_visual_qa_report.md",
                "copy_to_publish_lane": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    (run_dir / "manual_visual_qa_operator_decision_intake.json").write_text(
        json.dumps({"status": "valid_operator_decision_ready_for_staging"}),
        encoding="utf-8",
    )

    proc = run_staging(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, row, _ = read_outputs(run_dir)
    assert manifest["inputs"]["source_type"] == "validated_operator_decision_intake"
    assert manifest["status"] == "review_only_staging_ready"
    assert row["staging_lane"] == "approved_for_next_manual_step"
    assert row["operator_decision"] == "approve_for_manual_next_step"
    assert row["publish_ready"] == "false"
    assert row["copy_to_publish_lane"] == "false"


def test_manual_post_approval_render_staging_separates_hold_and_revise(tmp_path: Path) -> None:
    for decision, expected_lane in [("hold", "hold_for_operator_review"), ("revise", "revise_required")]:
        run_dir = tmp_path / decision / "files"
        write_intake(run_dir, decision=decision)

        proc = run_staging(tmp_path, run_dir)

        assert proc.returncode == 0, proc.stderr
        manifest, row, _ = read_outputs(run_dir)
        assert manifest["status"] == "review_only_staging_needs_operator_action"
        assert row["staging_lane"] == expected_lane
        assert row["operator_decision"] == decision
        assert row["publish_ready"] == "false"


def test_manual_post_approval_render_staging_flags_awaiting_invalid_and_bad_approval(tmp_path: Path) -> None:
    cases = [
        ("operator_fill_required", "0", "human_review_required", "manual_next_step_only_not_publish_ready", "awaiting_operator_decision"),
        ("send_it", "0", "human_review_required", "manual_next_step_only_not_publish_ready", "invalid_operator_decision"),
        ("approve_for_manual_next_step", "2", "human_review_required", "manual_next_step_only_not_publish_ready", "blocked_approval_with_visual_qa_holds"),
        ("approve_for_manual_next_step", "0", "hold_for_manual_review", "manual_next_step_only_not_publish_ready", "blocked_approval_without_clear_visual_qa"),
        ("approve_for_manual_next_step", "0", "human_review_required", "publish_ready", "blocked_approval_scope_mismatch"),
    ]
    for index, (decision, hold_count, qa_status, scope, expected_lane) in enumerate(cases):
        run_dir = tmp_path / f"case_{index}" / "files"
        write_intake(run_dir, decision=decision, hold_count=hold_count, qa_status=qa_status, approval_scope=scope)

        proc = run_staging(tmp_path, run_dir)

        assert proc.returncode == 0, proc.stderr
        manifest, row, _ = read_outputs(run_dir)
        assert manifest["status"] == "review_only_staging_needs_operator_action"
        assert row["staging_lane"] == expected_lane
        assert row["publish_ready"] == "false"
        assert row["copy_to_publish_lane"] == "false"


def test_manual_post_approval_render_staging_blocks_missing_intake(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_staging(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, row, report = read_outputs(run_dir)
    assert manifest["status"] == "blocked_missing_approval_intake"
    assert row["staging_lane"] == "blocked_missing_approval_intake"
    assert row["move_files"] == "false"
    assert "manual_visual_qa_approval_intake.csv was not found" in row["blocked_reason"]
    assert "Publishing requires a separate future workflow" in report
