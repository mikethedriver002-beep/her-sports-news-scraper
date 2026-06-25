from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-visual-qa-operator-decision-draft-v1.0.0-copy-safe"
OUT_MD = output_path("manual_visual_qa_operator_decision_draft.md")
OUT_CSV = output_path("manual_visual_qa_operator_decision_draft.csv")
OUT_JSON = output_path("manual_visual_qa_operator_decision_draft.json")
COPY_TARGET = "operator/inbox/manual_visual_qa_operator_decisions.csv"
ALLOWED_DECISIONS = "approve_for_manual_next_step|hold|revise"

DRAFT_FIELDS = [
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


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def repo_root() -> Path:
    return Path.cwd().resolve()


def input_candidates(relative: str) -> List[Path]:
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / relative)
    candidates.append(repo_root() / relative)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / relative)
    return candidates


def first_existing(relative: str) -> Path | None:
    for candidate in input_candidates(relative):
        if candidate.exists():
            return candidate
    return None


def read_json(path: Path | None) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_csv_rows(path: Path | None) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def build_draft_row(intake_row: Dict[str, str], intake_path: Path | None) -> Dict[str, str]:
    source_intake_id = clean(intake_row.get("intake_id")) or "manual_visual_qa_preview_1"
    qa_status = clean(intake_row.get("qa_status")) or "missing_visual_qa_status"
    automated_hold_count = clean(intake_row.get("automated_hold_count")) or "0"
    if qa_status == "human_review_required" and automated_hold_count == "0":
        copy_status = "ready_for_operator_fill_after_opening_preview"
        instructions = (
            f"Copy this row to {COPY_TARGET} only after opening the preview and QA report. "
            "Fill operator_decision with approve_for_manual_next_step, hold, or revise plus notes."
        )
    else:
        copy_status = "hold_or_revise_recommended_before_copy"
        instructions = (
            f"Copy to {COPY_TARGET} only if you are deliberately recording hold or revise. "
            "Do not choose approve_for_manual_next_step until QA status is human_review_required with zero automated holds."
        )

    return {
        "decision_draft_id": f"decision_draft_{source_intake_id}",
        "source_intake_id": source_intake_id,
        "preview_path": clean(intake_row.get("preview_path")),
        "qa_status": qa_status,
        "automated_hold_count": automated_hold_count,
        "allowed_decisions": ALLOWED_DECISIONS,
        "operator_decision": "operator_fill_required",
        "operator_notes": "",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "required_evidence": clean(intake_row.get("required_evidence"))
        or "Open draft_preview.png and manual_visual_qa_report.md before filling the decision.",
        "copy_target": COPY_TARGET,
        "copy_instructions": instructions,
        "copy_status": copy_status,
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def placeholder_row(intake_path: Path | None) -> Dict[str, str]:
    return {
        "decision_draft_id": "decision_draft_missing_visual_qa_approval_intake",
        "source_intake_id": "missing_manual_visual_qa_approval_intake",
        "preview_path": "",
        "qa_status": "missing_visual_qa_approval_intake",
        "automated_hold_count": "0",
        "allowed_decisions": ALLOWED_DECISIONS,
        "operator_decision": "operator_fill_required",
        "operator_notes": "",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "required_evidence": "Run .\\hsd.cmd run -Mode render to create the visual QA approval intake before filling a decision.",
        "copy_target": COPY_TARGET,
        "copy_instructions": f"Do not copy this placeholder row to {COPY_TARGET}; first generate a real approval intake.",
        "copy_status": "blocked_missing_visual_qa_approval_intake",
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def report_lines(manifest: Dict[str, Any], rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "# HSD Manual Visual QA Operator Decision Draft",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        "This helper creates a copy-safe draft row for the operator decision after visual QA.",
        "It does not edit the generated approval intake, does not approve anything, does not move files, and does not publish.",
        "",
        "## How To Use",
        "",
        f"1. Open `manual_visual_qa_operator_decision_draft.csv`.",
        f"2. Open the preview and QA report referenced in the row.",
        f"3. Copy the row into `{COPY_TARGET}` only after review.",
        f"4. Fill `operator_decision` with one of `{ALLOWED_DECISIONS}` plus notes.",
        "5. Keep this as manual-next-step approval only; it is not a publishing approval.",
        "",
        "## Draft Rows",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"- Draft: `{row['decision_draft_id']}`",
                f"  Source intake: `{row['source_intake_id']}`",
                f"  QA status: `{row['qa_status']}`",
                f"  Automated holds: `{row['automated_hold_count']}`",
                f"  Copy status: `{row['copy_status']}`",
                f"  Copy target: `{row['copy_target']}`",
                f"  Preview: `{row['preview_path'] or 'missing'}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Guardrails",
            "",
            "- `publish_ready=false` for every row.",
            "- `auto_approval=false` for every row.",
            "- `auto_publish=false` for every row.",
            "- `move_files=false` for every row.",
            "- Paid APIs remain false.",
            "",
        ]
    )
    return lines


def main() -> None:
    intake_path = first_existing("manual_visual_qa_approval_intake.csv")
    intake_manifest_path = first_existing("manual_visual_qa_approval_intake.json")
    intake_rows = read_csv_rows(intake_path)
    rows = [build_draft_row(row, intake_path) for row in intake_rows]
    if not rows:
        rows = [placeholder_row(intake_path)]
    blocked = any(row["copy_status"].startswith("blocked") for row in rows)
    ready = any(row["copy_status"] == "ready_for_operator_fill_after_opening_preview" for row in rows)
    status = "blocked_missing_visual_qa_approval_intake" if blocked else ("draft_ready_for_operator_fill" if ready else "draft_requires_hold_or_revise")

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "approval_status": "not_approved_decision_draft_only",
        "inputs": {
            "approval_intake_path": intake_path.as_posix() if intake_path else "",
            "approval_intake_manifest_path": intake_manifest_path.as_posix() if intake_manifest_path else "",
            "intake_row_count": len(intake_rows),
        },
        "copy_target": COPY_TARGET,
        "draft_rows": rows,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "copy_safe_draft": True,
            "edits_generated_intake": False,
            "move_files": False,
            "auto_approval": False,
            "auto_publish": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, rows, DRAFT_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest, rows)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
