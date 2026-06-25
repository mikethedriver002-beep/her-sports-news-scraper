from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-visual-qa-operator-decision-template-v1.0.0-copy-only"
OUT_MD = output_path("manual_visual_qa_operator_decision_template.md")
OUT_CSV = output_path("manual_visual_qa_operator_decision_template.csv")
OUT_JSON = output_path("manual_visual_qa_operator_decision_template.json")
COPY_TARGET = "operator/inbox/manual_visual_qa_operator_decisions.csv"

TEMPLATE_FIELDS = [
    "template_row_type",
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


def read_csv_rows(path: Path | None) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def base_from_draft(row: Dict[str, str]) -> Dict[str, str]:
    return {
        "decision_draft_id": clean(row.get("decision_draft_id")),
        "source_intake_id": clean(row.get("source_intake_id")),
        "preview_path": clean(row.get("preview_path")),
        "qa_status": clean(row.get("qa_status")),
        "automated_hold_count": clean(row.get("automated_hold_count")) or "0",
        "allowed_decisions": clean(row.get("allowed_decisions")) or "approve_for_manual_next_step|hold|revise",
        "required_evidence": clean(row.get("required_evidence")) or "Open draft_preview.png and manual_visual_qa_report.md before filling the decision.",
        "copy_target": COPY_TARGET,
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def placeholder_base() -> Dict[str, str]:
    return {
        "decision_draft_id": "REPLACE_WITH_DECISION_DRAFT_ID",
        "source_intake_id": "REPLACE_WITH_SOURCE_INTAKE_ID",
        "preview_path": "REPLACE_WITH_PREVIEW_PATH",
        "qa_status": "REPLACE_WITH_QA_STATUS",
        "automated_hold_count": "REPLACE_WITH_AUTOMATED_HOLD_COUNT",
        "allowed_decisions": "approve_for_manual_next_step|hold|revise",
        "required_evidence": "Open draft_preview.png and manual_visual_qa_report.md before filling the decision.",
        "copy_target": COPY_TARGET,
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def template_rows(base: Dict[str, str]) -> List[Dict[str, str]]:
    examples = [
        {
            "template_row_type": "approve_example_copy_then_replace_placeholders",
            "operator_decision": "approve_for_manual_next_step",
            "operator_notes": "REPLACE_WITH_APPROVAL_NOTES_AFTER_OPENING_PREVIEW_AND_QA_REPORT",
            "hold_reason": "",
            "revision_request": "",
            "copy_status": "template_only_not_valid_until_placeholders_replaced",
            "copy_instructions": f"Copy only this row to {COPY_TARGET} after visual review, then replace every REPLACE_WITH_* value before rerunning render.",
        },
        {
            "template_row_type": "hold_example_copy_then_replace_placeholders",
            "operator_decision": "hold",
            "operator_notes": "REPLACE_WITH_HOLD_NOTES",
            "hold_reason": "REPLACE_WITH_HOLD_REASON",
            "revision_request": "",
            "copy_status": "template_only_not_valid_until_placeholders_replaced",
            "copy_instructions": f"Copy this row to {COPY_TARGET} only to record a hold, then replace every REPLACE_WITH_* value before rerunning render.",
        },
        {
            "template_row_type": "revise_example_copy_then_replace_placeholders",
            "operator_decision": "revise",
            "operator_notes": "REPLACE_WITH_REVISION_NOTES",
            "hold_reason": "",
            "revision_request": "REPLACE_WITH_REVISION_REQUEST",
            "copy_status": "template_only_not_valid_until_placeholders_replaced",
            "copy_instructions": f"Copy this row to {COPY_TARGET} only to request revision, then replace every REPLACE_WITH_* value before rerunning render.",
        },
    ]
    rows: List[Dict[str, str]] = []
    for example in examples:
        row = dict(base)
        row.update(example)
        row["operator_name"] = "REPLACE_WITH_OPERATOR_NAME"
        row["reviewed_at_local"] = "REPLACE_WITH_LOCAL_REVIEW_TIME"
        rows.append(row)
    return rows


def report_lines(manifest: Dict[str, Any], rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "# HSD Manual Visual QA Operator Decision Template",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        f"This copy-only template gives approve, hold, and revise examples for `{COPY_TARGET}`.",
        "It does not write the inbox, approve anything, move files, publish, or create a publish-ready lane.",
        "",
        "## How To Use",
        "",
        "1. Open `manual_visual_qa_operator_decision_template.csv`.",
        f"2. Copy exactly one example row into `{COPY_TARGET}` after opening the preview and QA report.",
        "3. Replace every `REPLACE_WITH_*` value with real operator notes, name, and local review time.",
        "4. Rerun `./hsd.cmd run -Mode render` so the intake reader validates the row.",
        "",
        "## Examples",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"- `{row['template_row_type']}` -> `{row['operator_decision']}`",
                f"  Copy status: `{row['copy_status']}`",
                f"  Target: `{row['copy_target']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Guardrails",
            "",
            "- Template rows are not approvals.",
            "- Placeholder values are intentionally rejected by the intake reader.",
            "- `publish_ready=false` for every row.",
            "- `auto_approval=false` for every row.",
            "- `auto_publish=false` for every row.",
            "- `move_files=false` for every row.",
            "",
        ]
    )
    return lines


def main() -> None:
    draft_path = first_existing("manual_visual_qa_operator_decision_draft.csv")
    draft_rows = read_csv_rows(draft_path)
    base = base_from_draft(draft_rows[0]) if draft_rows else placeholder_base()
    rows = template_rows(base)
    status = "template_ready_copy_only" if draft_rows else "template_placeholder_only_missing_decision_draft"
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "approval_status": "not_approved_template_only",
        "inputs": {
            "decision_draft_path": draft_path.as_posix() if draft_path else "",
            "decision_draft_rows": len(draft_rows),
        },
        "copy_target": COPY_TARGET,
        "template_rows": rows,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "template_only": True,
            "writes_operator_inbox": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "copy_to_publish_lane": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, rows, TEMPLATE_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest, rows)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
