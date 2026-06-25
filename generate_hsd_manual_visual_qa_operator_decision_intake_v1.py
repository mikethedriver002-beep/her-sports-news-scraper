from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-visual-qa-operator-decision-intake-v1.0.0-review-only"
INBOX_PATH = "operator/inbox/manual_visual_qa_operator_decisions.csv"
OUT_MD = output_path("manual_visual_qa_operator_decision_intake.md")
OUT_CSV = output_path("manual_visual_qa_operator_decision_intake.csv")
OUT_JSON = output_path("manual_visual_qa_operator_decision_intake.json")
ALLOWED_DECISIONS = {"approve_for_manual_next_step", "hold", "revise"}

VALIDATED_FIELDS = [
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


def draft_by_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for row in rows:
        draft_id = clean(row.get("decision_draft_id"))
        source_id = clean(row.get("source_intake_id"))
        if draft_id:
            mapping[draft_id] = row
        if source_id:
            mapping[source_id] = row
    return mapping


def row_bool_is_false(row: Dict[str, str], key: str) -> bool:
    value = clean(row.get(key)).lower()
    return value in {"", "false", "no", "0"}


def has_placeholder(value: Any) -> bool:
    text = clean(value).upper()
    return "REPLACE_WITH_" in text or text.startswith("TEMPLATE_") or text.startswith("EXAMPLE_")


def validate_decision(row: Dict[str, str], draft: Dict[str, str] | None) -> tuple[str, str]:
    decision = clean(row.get("operator_decision"))
    if not draft:
        return "invalid_no_matching_decision_draft", "No generated decision draft matched this row."
    for key in ["operator_notes", "hold_reason", "revision_request", "operator_name", "reviewed_at_local"]:
        if has_placeholder(row.get(key)):
            return "invalid_template_placeholder", f"{key} still contains a template placeholder."
    if decision not in ALLOWED_DECISIONS:
        return "invalid_operator_decision", f"operator_decision must be one of {', '.join(sorted(ALLOWED_DECISIONS))}."
    if clean(row.get("source_intake_id")) != clean(draft.get("source_intake_id")):
        return "invalid_source_intake_mismatch", "source_intake_id does not match the generated decision draft."
    if clean(row.get("preview_path")) != clean(draft.get("preview_path")):
        return "invalid_preview_path_mismatch", "preview_path does not match the generated decision draft."
    if clean(row.get("approval_scope")) not in {"", "manual_next_step_only_not_publish_ready"}:
        return "invalid_approval_scope", "approval_scope must remain manual_next_step_only_not_publish_ready."
    for key in ["publish_ready", "auto_approval", "auto_publish", "move_files"]:
        if not row_bool_is_false(row, key):
            return "invalid_guardrail_flag", f"{key} must be false."
    if not clean(row.get("operator_notes")):
        return "invalid_missing_operator_notes", "operator_notes are required."
    if not clean(row.get("operator_name")):
        return "invalid_missing_operator_name", "operator_name is required."
    if not clean(row.get("reviewed_at_local")):
        return "invalid_missing_reviewed_at_local", "reviewed_at_local is required."
    if decision == "approve_for_manual_next_step":
        if clean(draft.get("copy_status")) != "ready_for_operator_fill_after_opening_preview":
            return "blocked_approval_not_copy_ready", "Generated decision draft was not ready for approve_for_manual_next_step."
        if clean(draft.get("qa_status")) != "human_review_required" or clean(draft.get("automated_hold_count")) != "0":
            return "blocked_approval_visual_qa_not_clear", "Visual QA must be human_review_required with zero automated holds."
    if decision == "hold" and not (clean(row.get("hold_reason")) or clean(row.get("operator_notes"))):
        return "invalid_missing_hold_reason", "hold rows require hold_reason or operator_notes."
    if decision == "revise" and not (clean(row.get("revision_request")) or clean(row.get("operator_notes"))):
        return "invalid_missing_revision_request", "revise rows require revision_request or operator_notes."
    return "valid_operator_decision", ""


def awaiting_row(draft: Dict[str, str] | None, draft_path: Path | None, decision_path: Path | None) -> Dict[str, str]:
    draft = draft or {}
    return {
        "intake_id": clean(draft.get("source_intake_id")) or "manual_visual_qa_preview_1",
        "decision_draft_id": clean(draft.get("decision_draft_id")),
        "source_intake_id": clean(draft.get("source_intake_id")) or "manual_visual_qa_preview_1",
        "preview_path": clean(draft.get("preview_path")),
        "qa_status": clean(draft.get("qa_status")),
        "automated_hold_count": clean(draft.get("automated_hold_count")) or "0",
        "operator_decision": "operator_fill_required",
        "validation_status": "awaiting_operator_decision",
        "validation_issue": f"Copy a draft row into {INBOX_PATH}, then fill approve_for_manual_next_step, hold, or revise with notes.",
        "operator_notes": "",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "source_decision_path": decision_path.as_posix() if decision_path else "",
        "source_draft_path": draft_path.as_posix() if draft_path else "",
        "source_qa_report_path": "",
        "copy_to_publish_lane": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def validated_row(row: Dict[str, str], draft: Dict[str, str] | None, status: str, issue: str, draft_path: Path | None, decision_path: Path | None) -> Dict[str, str]:
    draft = draft or {}
    return {
        "intake_id": clean(draft.get("source_intake_id")) or clean(row.get("source_intake_id")) or clean(row.get("intake_id")),
        "decision_draft_id": clean(row.get("decision_draft_id")) or clean(draft.get("decision_draft_id")),
        "source_intake_id": clean(row.get("source_intake_id")) or clean(draft.get("source_intake_id")),
        "preview_path": clean(row.get("preview_path")) or clean(draft.get("preview_path")),
        "qa_status": clean(draft.get("qa_status")) or clean(row.get("qa_status")),
        "automated_hold_count": clean(draft.get("automated_hold_count")) or clean(row.get("automated_hold_count")) or "0",
        "operator_decision": clean(row.get("operator_decision")) or "operator_fill_required",
        "validation_status": status,
        "validation_issue": issue,
        "operator_notes": clean(row.get("operator_notes")),
        "hold_reason": clean(row.get("hold_reason")),
        "revision_request": clean(row.get("revision_request")),
        "operator_name": clean(row.get("operator_name")),
        "reviewed_at_local": clean(row.get("reviewed_at_local")),
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "source_decision_path": decision_path.as_posix() if decision_path else "",
        "source_draft_path": draft_path.as_posix() if draft_path else "",
        "source_qa_report_path": clean(draft.get("source_qa_report_path")),
        "copy_to_publish_lane": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def report_lines(manifest: Dict[str, Any], rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "# HSD Manual Visual QA Operator Decision Intake",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        f"This report reads `{INBOX_PATH}` and validates operator decisions against the generated decision draft.",
        "It does not approve publishing, move files, auto-publish, or create a publish-ready lane.",
        "",
        "## Decision Rows",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"- Intake: `{row['intake_id']}`",
                f"  Decision: `{row['operator_decision']}`",
                f"  Validation: `{row['validation_status']}`",
                f"  Issue: {row['validation_issue'] or 'none'}",
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
            "- `copy_to_publish_lane=false` for every row.",
            "- Paid APIs remain false.",
            "",
        ]
    )
    return lines


def main() -> None:
    draft_path = first_existing("manual_visual_qa_operator_decision_draft.csv")
    draft_manifest_path = first_existing("manual_visual_qa_operator_decision_draft.json")
    decision_path = first_existing(INBOX_PATH)
    draft_rows = read_csv_rows(draft_path)
    decision_rows = read_csv_rows(decision_path)
    draft_map = draft_by_id(draft_rows)

    output_rows: List[Dict[str, str]] = []
    if not draft_rows:
        output_rows.append(awaiting_row(None, draft_path, decision_path))
        output_rows[-1]["validation_status"] = "blocked_missing_decision_draft"
        output_rows[-1]["validation_issue"] = "Run .\\hsd.cmd run -Mode render to create manual_visual_qa_operator_decision_draft.csv."
    elif not decision_rows:
        output_rows.append(awaiting_row(draft_rows[0], draft_path, decision_path))
    else:
        for row in decision_rows:
            draft_key = clean(row.get("decision_draft_id")) or clean(row.get("source_intake_id"))
            draft = draft_map.get(draft_key)
            status, issue = validate_decision(row, draft)
            output_rows.append(validated_row(row, draft, status, issue, draft_path, decision_path))

    valid_count = sum(1 for row in output_rows if row["validation_status"] == "valid_operator_decision")
    invalid_count = sum(1 for row in output_rows if row["validation_status"].startswith("invalid") or row["validation_status"].startswith("blocked"))
    awaiting_count = sum(1 for row in output_rows if row["validation_status"] == "awaiting_operator_decision")
    status = "valid_operator_decision_ready_for_staging" if valid_count and not invalid_count and not awaiting_count else "operator_decision_needs_review"
    if awaiting_count and not valid_count and not invalid_count:
        status = "awaiting_operator_decision"
    if any(row["validation_status"] == "blocked_missing_decision_draft" for row in output_rows):
        status = "blocked_missing_decision_draft"

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "approval_status": "not_approved_validated_decision_only",
        "inputs": {
            "decision_inbox_path": decision_path.as_posix() if decision_path else "",
            "decision_draft_path": draft_path.as_posix() if draft_path else "",
            "decision_draft_manifest_path": draft_manifest_path.as_posix() if draft_manifest_path else "",
            "decision_row_count": len(decision_rows),
            "draft_row_count": len(draft_rows),
        },
        "counts": {
            "valid": valid_count,
            "invalid_or_blocked": invalid_count,
            "awaiting": awaiting_count,
        },
        "validated_rows": output_rows,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "validates_operator_inbox": True,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "copy_to_publish_lane": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, output_rows, VALIDATED_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest, output_rows)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
