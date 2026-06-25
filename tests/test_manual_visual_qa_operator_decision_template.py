from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_operator_decision_template_v1.py"
INTAKE_SCRIPT = REPO / "generate_hsd_manual_visual_qa_operator_decision_intake_v1.py"
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


def write_decision_draft(run_dir: Path) -> dict[str, str]:
    run_dir.mkdir(parents=True, exist_ok=True)
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(b"fake png path for template only")
    row = {
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
        "required_evidence": "Open draft_preview.png plus manual_visual_qa_report.md.",
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
    with (run_dir / "manual_visual_qa_operator_decision_draft.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
    return row


def run_template(tmp_path: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
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


def run_intake(tmp_path: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    return subprocess.run(
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(INTAKE_SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_operator_decision_template_writes_copy_only_examples(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    draft = write_decision_draft(run_dir)

    proc = run_template(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    csv_path = run_dir / "manual_visual_qa_operator_decision_template.csv"
    md_path = run_dir / "manual_visual_qa_operator_decision_template.md"
    manifest_path = run_dir / "manual_visual_qa_operator_decision_template.json"
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["status"] == "template_ready_copy_only"
    assert manifest["approval_status"] == "not_approved_template_only"
    assert {row["operator_decision"] for row in rows} == {"approve_for_manual_next_step", "hold", "revise"}
    assert all(row["source_intake_id"] == draft["source_intake_id"] for row in rows)
    assert all(row["copy_target"] == "operator/inbox/manual_visual_qa_operator_decisions.csv" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["auto_approval"] == "false" for row in rows)
    assert all(row["auto_publish"] == "false" for row in rows)
    assert all(row["move_files"] == "false" for row in rows)
    assert all("REPLACE_WITH_" in row["operator_name"] for row in rows)
    assert manifest["guardrails"]["writes_operator_inbox"] is False
    assert "Template rows are not approvals" in md_path.read_text(encoding="utf-8")


def test_operator_decision_template_placeholder_rows_are_rejected_by_intake(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_decision_draft(run_dir)
    proc = run_template(tmp_path, run_dir)
    assert proc.returncode == 0, proc.stderr

    template_rows = list(csv.DictReader((run_dir / "manual_visual_qa_operator_decision_template.csv").open(newline="", encoding="utf-8")))
    inbox = tmp_path / "operator" / "inbox" / "manual_visual_qa_operator_decisions.csv"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    with inbox.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerow(template_rows[0])

    intake_proc = run_intake(tmp_path, run_dir)

    assert intake_proc.returncode == 0, intake_proc.stderr
    validated = next(csv.DictReader((run_dir / "manual_visual_qa_operator_decision_intake.csv").open(newline="", encoding="utf-8")))
    assert validated["validation_status"] == "invalid_template_placeholder"
    assert "placeholder" in validated["validation_issue"]
    assert validated["publish_ready"] == "false"


def test_operator_decision_template_writes_placeholder_when_draft_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_template(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_operator_decision_template.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((run_dir / "manual_visual_qa_operator_decision_template.csv").open(newline="", encoding="utf-8")))
    assert manifest["status"] == "template_placeholder_only_missing_decision_draft"
    assert rows[0]["decision_draft_id"] == "REPLACE_WITH_DECISION_DRAFT_ID"
    assert rows[0]["publish_ready"] == "false"
