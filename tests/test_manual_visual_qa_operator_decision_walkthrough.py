from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_operator_decision_walkthrough_v1.py"
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
    "template_row_type",
]


def run_walkthrough(tmp_path: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
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


def write_render_decision_inputs(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(b"fake png for walkthrough")
    (run_dir / "manual_visual_qa_report.md").write_text("# Manual visual QA\n", encoding="utf-8")
    (run_dir / "manual_visual_qa_operator_decision_template.md").write_text("# Copy-only template\n", encoding="utf-8")
    (run_dir / "manual_visual_qa_operator_decision_intake.md").write_text("# Operator decision intake\n", encoding="utf-8")
    (run_dir / "manual_post_approval_render_staging.md").write_text("# Review-only staging\n", encoding="utf-8")

    base_row = {
        "decision_draft_id": "decision_draft_manual_visual_qa_preview_1",
        "source_intake_id": "manual_visual_qa_preview_1",
        "preview_path": preview.as_posix(),
        "qa_status": "human_review_required",
        "automated_hold_count": "0",
        "allowed_decisions": "approve_for_manual_next_step|hold|revise",
        "operator_notes": "REPLACE_WITH_OPERATOR_NOTES",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "REPLACE_WITH_OPERATOR_NAME",
        "reviewed_at_local": "REPLACE_WITH_REVIEW_TIME",
        "required_evidence": "Open draft_preview.png plus manual_visual_qa_report.md.",
        "copy_target": "operator/inbox/manual_visual_qa_operator_decisions.csv",
        "copy_instructions": "Copy after review.",
        "copy_status": "copy_only_unapproved_example",
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    rows = []
    for decision in ["approve_for_manual_next_step", "hold", "revise"]:
        row = dict(base_row)
        row["operator_decision"] = decision
        row["template_row_type"] = decision
        rows.append(row)
    with (run_dir / "manual_visual_qa_operator_decision_template.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    with (run_dir / "manual_visual_qa_operator_decision_draft.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerow(rows[0])


def test_operator_decision_walkthrough_writes_report_only_steps(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_render_decision_inputs(run_dir)

    proc = run_walkthrough(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_operator_decision_walkthrough.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((run_dir / "manual_visual_qa_operator_decision_walkthrough.csv").open(newline="", encoding="utf-8")))
    report = (run_dir / "manual_visual_qa_operator_decision_walkthrough.md").read_text(encoding="utf-8")

    assert manifest["status"] == "walkthrough_ready"
    assert manifest["approval_status"] == "not_approved_walkthrough_only"
    assert manifest["operator_inbox_target"] == "operator/inbox/manual_visual_qa_operator_decisions.csv"
    assert manifest["template_row_count"] == 3
    assert manifest["guardrails"]["writes_operator_inbox"] is False
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["auto_publish"] is False
    assert manifest["guardrails"]["move_files"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert manifest["guardrails"]["paid_apis"] is False
    assert [row["step_title"] for row in rows] == [
        "Open the draft preview",
        "Open visual QA evidence",
        "Choose one template row",
        "Create or update the operator inbox",
        "Rerun validation",
        "Review validation and staging",
    ]
    assert "does not edit the inbox" in report
    assert "operator/inbox/manual_visual_qa_operator_decisions.csv" in report
    assert "REPLACE_WITH_*" in report
    assert ".\\hsd.cmd run -Mode render" in report
    assert not (tmp_path / "operator" / "inbox" / "manual_visual_qa_operator_decisions.csv").exists()


def test_operator_decision_walkthrough_flags_missing_render_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_walkthrough(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_operator_decision_walkthrough.json").read_text(encoding="utf-8"))
    report = (run_dir / "manual_visual_qa_operator_decision_walkthrough.md").read_text(encoding="utf-8")

    assert manifest["status"] == "walkthrough_missing_render_artifacts"
    assert set(manifest["missing_required_inputs"]) == {"preview", "qa_report", "template_csv", "template_md", "draft_csv"}
    assert manifest["template_row_count"] == 0
    assert manifest["guardrails"]["writes_operator_inbox"] is False
    assert manifest["guardrails"]["auto_publish"] is False
    assert "No template rows found" in report
