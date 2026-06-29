from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_operator_decision_draft_v1.py"
PYTHON = REPO / ".venv" / "Scripts" / "python.exe"


def write_intake(
    run_dir: Path,
    *,
    qa_status: str = "human_review_required",
    hold_count: str = "0",
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(b"fake png path for decision draft only")
    with (run_dir / "manual_visual_qa_approval_intake.csv").open("w", newline="", encoding="utf-8") as handle:
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
                "allowed_decisions": "hold|revise|approve_for_manual_next_step",
                "operator_decision": "operator_fill_required",
                "operator_notes": "",
                "operator_name": "",
                "reviewed_at_local": "",
                "required_evidence": "Open draft_preview.png plus manual_visual_qa_report.md.",
                "next_manual_step": "Manual next step only.",
                "approval_scope": "manual_next_step_only_not_publish_ready",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "paid_apis": "false",
            }
        )
    (run_dir / "manual_visual_qa_approval_intake.json").write_text(
        json.dumps({"status": "ready_for_manual_decision"}),
        encoding="utf-8",
    )


def run_draft(tmp_path: Path, run_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    return subprocess.run(
        [str(PYTHON if PYTHON.exists() else sys.executable), str(SCRIPT)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def read_outputs(run_dir: Path) -> tuple[dict, dict, str]:
    manifest = json.loads((run_dir / "manual_visual_qa_operator_decision_draft.json").read_text(encoding="utf-8"))
    row = next(csv.DictReader((run_dir / "manual_visual_qa_operator_decision_draft.csv").open(newline="", encoding="utf-8")))
    report = (run_dir / "manual_visual_qa_operator_decision_draft.md").read_text(encoding="utf-8")
    return manifest, row, report


def test_manual_visual_qa_operator_decision_draft_is_copy_safe_ready_row(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_intake(run_dir)

    proc = run_draft(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, row, report = read_outputs(run_dir)
    assert manifest["status"] == "draft_ready_for_operator_fill"
    assert manifest["approval_status"] == "not_approved_decision_draft_only"
    assert row["source_intake_id"] == "manual_visual_qa_preview_1"
    assert row["operator_decision"] == "operator_fill_required"
    assert row["allowed_decisions"] == "hold|revise|approve_for_manual_next_step"
    assert row["copy_target"] == "operator/inbox/manual_visual_qa_operator_decisions.csv"
    assert row["copy_status"] == "ready_for_operator_fill_after_opening_preview"
    assert row["publish_ready"] == "false"
    assert row["auto_approval"] == "false"
    assert row["auto_publish"] == "false"
    assert row["move_files"] == "false"
    assert manifest["guardrails"]["edits_generated_intake"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert "does not edit the generated approval intake" in report
    assert "Approve for manual next step only" in report


def test_manual_visual_qa_operator_decision_draft_recommends_hold_or_revise_when_qa_has_holds(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_intake(run_dir, qa_status="hold_for_manual_review", hold_count="2")

    proc = run_draft(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, row, _ = read_outputs(run_dir)
    assert manifest["status"] == "draft_requires_hold_or_revise"
    assert row["copy_status"] == "hold_or_revise_recommended_before_copy"
    assert "Do not choose approve_for_manual_next_step" in row["copy_instructions"]
    assert row["publish_ready"] == "false"


def test_manual_visual_qa_operator_decision_draft_blocks_missing_intake(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_draft(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest, row, _ = read_outputs(run_dir)
    assert manifest["status"] == "blocked_missing_visual_qa_approval_intake"
    assert row["copy_status"] == "blocked_missing_visual_qa_approval_intake"
    assert "Do not copy this placeholder row" in row["copy_instructions"]
    assert row["auto_publish"] == "false"
