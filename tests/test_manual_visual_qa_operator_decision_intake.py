from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_operator_decision_intake_v1.py"


FIELDS = [
    "decision_draft_id",
    "source_intake_id",
    "preview_path",
    "qa_status",
    "automated_hold_count",
    "allowed_decisions",
    "operator_decision",
    "operator_notes",
    "hold_reason",
    "revision_request",
    "operator_name",
    "reviewed_at_local",
    "required_evidence",
    "copy_target",
    "copy_instructions",
    "copy_status",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]


def draft_row(run_dir: Path) -> dict[str, str]:
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(b"fake png path for decision intake only")
    return {
        "decision_draft_id": "decision_draft_manual_visual_qa_preview_1",
        "source_intake_id": "manual_visual_qa_preview_1",
        "preview_path": preview.as_posix(),
        "qa_status": "human_review_required",
        "automated_hold_count": "0",
        "allowed_decisions": "approve_for_manual_next_step|hold|revise",
        "operator_decision": "operator_fill_required",
        "operator_notes": "",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "required_evidence": "Open draft_preview.png.",
        "copy_target": "operator/inbox/manual_visual_qa_operator_decisions.csv",
        "copy_instructions": "Copy after review.",
        "copy_status": "ready_for_operator_fill_after_opening_preview",
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def write_draft(run_dir: Path) -> dict[str, str]:
    run_dir.mkdir(parents=True, exist_ok=True)
    row = draft_row(run_dir)
    with (run_dir / "manual_visual_qa_operator_decision_draft.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
    (run_dir / "manual_visual_qa_operator_decision_draft.json").write_text(
        json.dumps({"status": "draft_ready_for_operator_fill"}),
        encoding="utf-8",
    )
    return row


def write_decision(tmp_path: Path, row: dict[str, str], **updates: str) -> Path:
    decision = dict(row)
    decision.update(
        {
            "operator_decision": "approve_for_manual_next_step",
            "operator_notes": "Looks readable, source-safe, and draft-marked.",
            "operator_name": "Test Operator",
            "reviewed_at_local": "2026-06-25 10:05",
        }
    )
    decision.update(updates)
    inbox = tmp_path / "operator" / "inbox" / "manual_visual_qa_operator_decisions.csv"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    with inbox.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(decision)
    return inbox


def run_intake(tmp_path: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
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
    manifest = json.loads((run_dir / "manual_visual_qa_operator_decision_intake.json").read_text(encoding="utf-8"))
    row = next(csv.DictReader((run_dir / "manual_visual_qa_operator_decision_intake.csv").open(newline="", encoding="utf-8")))
    report = (run_dir / "manual_visual_qa_operator_decision_intake.md").read_text(encoding="utf-8")
    return manifest, row, report


def test_operator_decision_intake_validates_approve_row_against_draft(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    row = write_draft(run_dir)
    write_decision(tmp_path, row)

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, validated, report = read_outputs(run_dir)
    assert manifest["status"] == "valid_operator_decision_ready_for_staging"
    assert manifest["approval_status"] == "not_approved_validated_decision_only"
    assert validated["operator_decision"] == "approve_for_manual_next_step"
    assert validated["validation_status"] == "valid_operator_decision"
    assert validated["validation_issue"] == ""
    assert validated["publish_ready"] == "false"
    assert validated["auto_approval"] == "false"
    assert validated["auto_publish"] == "false"
    assert validated["move_files"] == "false"
    assert manifest["guardrails"]["publish_ready"] is False
    assert "does not approve publishing" in report


def test_operator_decision_intake_flags_invalid_rows(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    row = write_draft(run_dir)
    write_decision(tmp_path, row, preview_path="wrong.png", operator_notes="")

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, validated, _ = read_outputs(run_dir)
    assert manifest["status"] == "operator_decision_needs_review"
    assert validated["validation_status"] == "invalid_preview_path_mismatch"
    assert validated["publish_ready"] == "false"
    assert validated["copy_to_publish_lane"] == "false"


def test_operator_decision_intake_awaits_missing_inbox(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_draft(run_dir)

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, validated, _ = read_outputs(run_dir)
    assert manifest["status"] == "awaiting_operator_decision"
    assert validated["validation_status"] == "awaiting_operator_decision"
    assert validated["operator_decision"] == "operator_fill_required"
    assert "operator/inbox/manual_visual_qa_operator_decisions.csv" in validated["validation_issue"]


def test_operator_decision_intake_blocks_missing_draft(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, validated, _ = read_outputs(run_dir)
    assert manifest["status"] == "blocked_missing_decision_draft"
    assert validated["validation_status"] == "blocked_missing_decision_draft"
    assert validated["publish_ready"] == "false"
