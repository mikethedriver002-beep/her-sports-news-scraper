from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "create_hsd_manual_visual_qa_operator_decision_inbox_starter_v1.py"
INBOX = Path("operator/inbox/manual_visual_qa_operator_decisions.csv")
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


def run_starter(tmp_path: Path, run_dir: Path, *, explicit: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    if explicit:
        env["HSD_EXPLICIT_OPERATOR_INBOX_STARTER"] = "1"
    else:
        env.pop("HSD_EXPLICIT_OPERATOR_INBOX_STARTER", None)
    return subprocess.run(
        [str(REPO / ".venv" / "Scripts" / "python.exe"), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def read_manifest(run_dir: Path) -> dict:
    return json.loads((run_dir / "manual_visual_qa_operator_decision_inbox_starter.json").read_text(encoding="utf-8"))


def test_inbox_starter_refuses_without_explicit_local_mode(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_starter(tmp_path, run_dir, explicit=False)

    assert proc.returncode == 0, proc.stderr
    manifest = read_manifest(run_dir)
    assert manifest["status"] == "blocked_requires_explicit_local_mode"
    assert manifest["explicit_mode_requested"] is False
    assert manifest["created_file"] is False
    assert not (tmp_path / INBOX).exists()
    assert manifest["guardrails"]["explicit_local_mode_required"] is True
    assert manifest["guardrails"]["fills_decision_rows"] is False


def test_inbox_starter_creates_header_only_csv_when_explicit(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_starter(tmp_path, run_dir, explicit=True)

    assert proc.returncode == 0, proc.stderr
    manifest = read_manifest(run_dir)
    inbox = tmp_path / INBOX
    with inbox.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    report = (run_dir / "manual_visual_qa_operator_decision_inbox_starter.md").read_text(encoding="utf-8")

    assert manifest["status"] == "header_only_inbox_created"
    assert manifest["explicit_mode_requested"] is True
    assert manifest["created_folder"] is True
    assert manifest["created_file"] is True
    assert rows == [FIELDS]
    assert manifest["existing_data_rows"] == 0
    assert manifest["guardrails"]["header_only"] is True
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["auto_publish"] is False
    assert manifest["guardrails"]["move_files"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert "does not fill any decision row" in report


def test_inbox_starter_preserves_existing_operator_rows(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)
    inbox = tmp_path / INBOX
    inbox.parent.mkdir(parents=True)
    existing = dict.fromkeys(FIELDS, "")
    existing.update(
        {
            "decision_draft_id": "decision_draft_manual_visual_qa_preview_1",
            "source_intake_id": "manual_visual_qa_preview_1",
            "operator_decision": "hold",
            "operator_notes": "Manual hold note.",
            "hold_reason": "Needs headline revision.",
            "operator_name": "Test Operator",
            "reviewed_at_local": "2026-06-25 10:30",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
        }
    )
    with inbox.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(existing)

    proc = run_starter(tmp_path, run_dir, explicit=True)

    assert proc.returncode == 0, proc.stderr
    manifest = read_manifest(run_dir)
    rows = list(csv.DictReader(inbox.open(newline="", encoding="utf-8")))
    assert manifest["status"] == "existing_operator_inbox_preserved"
    assert manifest["created_file"] is False
    assert manifest["existing_data_rows"] == 1
    assert rows == [existing]
