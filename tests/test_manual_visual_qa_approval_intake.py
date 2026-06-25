from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_visual_qa_approval_intake_v1.py"


def write_visual_qa_inputs(run_dir: Path, *, hold_count: int = 0) -> None:
    preview = run_dir / "render_handoff_top_packet" / "draft_preview.png"
    preview.parent.mkdir(parents=True)
    preview.write_bytes(b"fake png path for intake only")
    (run_dir / "manual_visual_qa_report.md").write_text("# QA\n", encoding="utf-8")
    (run_dir / "manual_visual_qa_manifest.json").write_text(
        json.dumps(
            {
                "status": "human_review_required" if hold_count == 0 else "hold_for_manual_review",
                "approval_status": "not_approved_human_review_required",
                "preview_path": preview.as_posix(),
                "summary": {
                    "check_count": 8,
                    "pass_count": 8 - hold_count,
                    "hold_count": hold_count,
                    "human_decision_required": True,
                },
                "guardrails": {
                    "manual_only": True,
                    "review_only": True,
                    "auto_approval": False,
                    "auto_publish": False,
                    "publish_ready": False,
                    "paid_apis": False,
                },
            }
        ),
        encoding="utf-8",
    )
    with (run_dir / "manual_visual_qa_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "check_id",
                "check_label",
                "qa_result",
                "operator_decision",
                "operator_notes",
                "evidence",
                "approval_policy",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "check_id": "dimensions_1080x1350",
                "check_label": "Expected draft dimensions",
                "qa_result": "pass" if hold_count == 0 else "hold",
                "operator_decision": "operator_fill_required",
                "operator_notes": "",
                "evidence": "Found 1080x1350.",
                "approval_policy": "manual approve/hold required",
            }
        )
        writer.writerow(
            {
                "check_id": "operator_visual_review",
                "check_label": "Human readable review",
                "qa_result": "human_required",
                "operator_decision": "operator_fill_required",
                "operator_notes": "",
                "evidence": "Open draft_preview.png.",
                "approval_policy": "No automatic approval.",
            }
        )


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


def test_manual_visual_qa_approval_intake_creates_operator_decision_row(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)
    write_visual_qa_inputs(run_dir)

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    csv_path = run_dir / "manual_visual_qa_approval_intake.csv"
    md_path = run_dir / "manual_visual_qa_approval_intake.md"
    json_path = run_dir / "manual_visual_qa_approval_intake.json"
    assert csv_path.exists()
    assert md_path.exists()
    assert json_path.exists()

    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    assert len(rows) == 1
    row = rows[0]
    assert row["operator_decision"] == "operator_fill_required"
    assert row["allowed_decisions"] == "approve_for_manual_next_step|hold|revise"
    assert row["publish_ready"] == "false"
    assert row["auto_approval"] == "false"
    assert row["auto_publish"] == "false"
    assert row["approval_scope"] == "manual_next_step_only_not_publish_ready"
    assert "Open draft_preview.png" in row["required_evidence"]

    manifest = json.loads(json_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "ready_for_manual_decision"
    assert manifest["approval_status"] == "not_approved_operator_input_required"
    assert manifest["visual_qa"]["automated_hold_count"] == "0"
    assert manifest["visual_qa"]["blank_operator_decisions"] == 2
    assert manifest["guardrails"]["operator_decision_required"] is True
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert "does not approve the preview by itself" in md_path.read_text(encoding="utf-8")


def test_manual_visual_qa_approval_intake_preserves_hold_guidance(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)
    write_visual_qa_inputs(run_dir, hold_count=1)

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    row = next(csv.DictReader((run_dir / "manual_visual_qa_approval_intake.csv").open(newline="", encoding="utf-8")))
    manifest = json.loads((run_dir / "manual_visual_qa_approval_intake.json").read_text(encoding="utf-8"))
    assert row["qa_status"] == "hold_for_manual_review"
    assert row["automated_hold_count"] == "1"
    assert "hold or revise" in row["next_manual_step"]
    assert row["operator_decision"] == "operator_fill_required"
    assert manifest["guardrails"]["auto_publish"] is False


def test_manual_visual_qa_approval_intake_blocks_missing_inputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    run_dir.mkdir(parents=True)

    proc = run_intake(tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((run_dir / "manual_visual_qa_approval_intake.json").read_text(encoding="utf-8"))
    row = next(csv.DictReader((run_dir / "manual_visual_qa_approval_intake.csv").open(newline="", encoding="utf-8")))
    assert manifest["status"] == "blocked_missing_visual_qa_inputs"
    assert set(manifest["inputs"]["missing"]) == {"preview", "report", "manifest", "checklist"}
    assert row["operator_decision"] == "operator_fill_required"
    assert row["publish_ready"] == "false"
