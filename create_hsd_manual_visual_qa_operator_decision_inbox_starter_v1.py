from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-visual-qa-operator-decision-inbox-starter-v1.0.0-header-only"
INBOX_PATH = Path("operator/inbox/manual_visual_qa_operator_decisions.csv")
EXPLICIT_ENV = "HSD_EXPLICIT_OPERATOR_INBOX_STARTER"
OUT_MD = output_path("manual_visual_qa_operator_decision_inbox_starter.md")
OUT_CSV = output_path("manual_visual_qa_operator_decision_inbox_starter.csv")
OUT_JSON = output_path("manual_visual_qa_operator_decision_inbox_starter.json")

INBOX_FIELDS = [
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

SUMMARY_FIELDS = [
    "status",
    "inbox_path",
    "created_folder",
    "created_file",
    "existing_data_rows",
    "header_status",
    "next_safe_action",
    "approval_status",
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


def explicit_mode_requested() -> bool:
    return clean(os.environ.get(EXPLICIT_ENV)).lower() in {"1", "true", "yes", "manual"}


def read_existing(path: Path) -> tuple[List[str], int]:
    if not path.exists() or not path.is_file():
        return [], 0
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            row_count = sum(1 for row in reader if any(clean(cell) for cell in row))
        return header, row_count
    except Exception:
        return [], 0


def write_header_only(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INBOX_FIELDS)
        writer.writeheader()


def report_lines(manifest: Dict[str, Any]) -> List[str]:
    lines = [
        "# HSD Manual Visual QA Operator Decision Inbox Starter",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        f"This manual-only starter creates `{INBOX_PATH.as_posix()}` as a header-only CSV only when the explicit local inbox starter mode requests it.",
        "It does not fill any decision row, approve anything, move files, publish, or create a publish-ready lane.",
        "",
        "## Result",
        "",
        f"- Inbox path: `{manifest['inbox_path']}`",
        f"- Created folder: `{manifest['created_folder']}`",
        f"- Created file: `{manifest['created_file']}`",
        f"- Existing data rows preserved: `{manifest['existing_data_rows']}`",
        f"- Header status: `{manifest['header_status']}`",
        f"- Next safe action: {manifest['next_safe_action']}",
        "",
        "## Header",
        "",
        "```csv",
        ",".join(INBOX_FIELDS),
        "```",
        "",
        "## Guardrails",
        "",
        "- Header-only starter.",
        "- Does not write approve, hold, or revise rows.",
        "- Does not overwrite existing operator decisions.",
        "- `publish_ready=false` remains required for any future row.",
        "- `auto_approval=false`, `auto_publish=false`, and `move_files=false` remain required.",
        "- Paid APIs remain false.",
        "",
    ]
    return lines


def main() -> None:
    inbox = repo_root() / INBOX_PATH
    explicit = explicit_mode_requested()
    created_folder = False
    created_file = False
    header, data_rows = read_existing(inbox)

    if not explicit:
        status = "blocked_requires_explicit_local_mode"
        header_status = "not_checked"
        next_safe_action = "Run .\\hsd.cmd run -Mode decision-inbox to intentionally create the header-only inbox starter."
    elif inbox.exists():
        header_status = "matches_expected_header" if header == INBOX_FIELDS else "header_needs_review"
        if data_rows > 0:
            status = "existing_operator_inbox_preserved"
            next_safe_action = "Open the existing inbox and keep or revise human-entered rows; this starter did not overwrite them."
        elif header_status == "matches_expected_header":
            status = "starter_already_ready"
            next_safe_action = "Copy exactly one completed template row into the inbox only after opening the draft preview and QA report."
        else:
            status = "existing_inbox_header_needs_review"
            next_safe_action = "Review the existing inbox header before adding decisions; this starter did not overwrite the file."
    else:
        created_folder = not inbox.parent.exists()
        write_header_only(inbox)
        created_file = True
        status = "header_only_inbox_created"
        header_status = "matches_expected_header"
        next_safe_action = "Open the walkthrough and copy exactly one completed approve, hold, or revise row after visual review."
        header, data_rows = read_existing(inbox)

    summary = {
        "status": status,
        "inbox_path": inbox.as_posix(),
        "created_folder": str(created_folder).lower(),
        "created_file": str(created_file).lower(),
        "existing_data_rows": str(data_rows),
        "header_status": header_status,
        "next_safe_action": next_safe_action,
        "approval_status": "not_approved_header_only",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "explicit_mode_requested": explicit,
        "inbox_path": inbox.as_posix(),
        "created_folder": created_folder,
        "created_file": created_file,
        "existing_data_rows": data_rows,
        "header_status": header_status,
        "header_fields": INBOX_FIELDS,
        "next_safe_action": next_safe_action,
        "approval_status": "not_approved_header_only",
        "guardrails": {
            "manual_only": True,
            "explicit_local_mode_required": True,
            "header_only": True,
            "fills_decision_rows": False,
            "overwrites_existing_inbox": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "copy_to_publish_lane": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, [summary], SUMMARY_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
