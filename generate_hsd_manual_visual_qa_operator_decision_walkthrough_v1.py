from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-visual-qa-operator-decision-walkthrough-v1.0.0-report-only"
INBOX_PATH = "operator/inbox/manual_visual_qa_operator_decisions.csv"
OUT_MD = output_path("manual_visual_qa_operator_decision_walkthrough.md")
OUT_CSV = output_path("manual_visual_qa_operator_decision_walkthrough.csv")
OUT_JSON = output_path("manual_visual_qa_operator_decision_walkthrough.json")

WALKTHROUGH_FIELDS = [
    "step_number",
    "step_title",
    "action",
    "file_to_open",
    "template_row_to_copy",
    "fields_to_replace",
    "expected_result",
    "guardrail",
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


def p(path: Path | None) -> str:
    return path.as_posix() if path else ""


def template_row_summary(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "No template rows found; rerun .\\hsd.cmd run -Mode render."
    parts = []
    for row in rows:
        parts.append(f"{clean(row.get('template_row_type'))} -> {clean(row.get('operator_decision'))}")
    return " | ".join(parts)


def build_steps(paths: Dict[str, Path | None], template_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    fields_to_replace = "operator_notes; hold_reason if holding; revision_request if revising; operator_name; reviewed_at_local; remove every REPLACE_WITH_* placeholder"
    template_choices = template_row_summary(template_rows)
    return [
        {
            "step_number": "1",
            "step_title": "Open the draft preview",
            "action": "Visually inspect the draft image for readability, crop safety, draft watermark, and source-safe copy.",
            "file_to_open": p(paths["preview"]),
            "template_row_to_copy": "",
            "fields_to_replace": "",
            "expected_result": "You know whether the draft should be approve_for_manual_next_step, hold, or revise.",
            "guardrail": "Do not publish or move the image.",
        },
        {
            "step_number": "2",
            "step_title": "Open visual QA evidence",
            "action": "Read the visual QA report and confirm automated holds, dimensions, text zones, and guardrails.",
            "file_to_open": p(paths["qa_report"]),
            "template_row_to_copy": "",
            "fields_to_replace": "",
            "expected_result": "If there are holds or visual concerns, choose hold or revise.",
            "guardrail": "Automated PASS does not equal approval.",
        },
        {
            "step_number": "3",
            "step_title": "Choose one template row",
            "action": "Open the copy-only template and choose exactly one example row.",
            "file_to_open": p(paths["template_csv"]),
            "template_row_to_copy": template_choices,
            "fields_to_replace": fields_to_replace,
            "expected_result": f"One edited row is ready to paste into {INBOX_PATH}.",
            "guardrail": "Template rows are not valid until all placeholders are replaced.",
        },
        {
            "step_number": "4",
            "step_title": "Create or update the operator inbox",
            "action": f"Paste exactly one completed row into {INBOX_PATH}. Keep the header from the template CSV.",
            "file_to_open": INBOX_PATH,
            "template_row_to_copy": "exactly one completed approve, hold, or revise row",
            "fields_to_replace": fields_to_replace,
            "expected_result": "The inbox contains one real operator decision row.",
            "guardrail": "Do not set publish_ready, auto_approval, auto_publish, or move_files to true.",
        },
        {
            "step_number": "5",
            "step_title": "Rerun validation",
            "action": "Run .\\hsd.cmd run -Mode render from the repo root.",
            "file_to_open": "D:/HSD Github Repo CLone/her-sports-news-scraper",
            "template_row_to_copy": "",
            "fields_to_replace": "",
            "expected_result": "manual_visual_qa_operator_decision_intake.csv validates the row, and staging updates review-only guidance.",
            "guardrail": "Render mode still does not publish, approve, or move files.",
        },
        {
            "step_number": "6",
            "step_title": "Review validation and staging",
            "action": "Open the operator decision intake and staging reports to confirm the validation result and next safe action.",
            "file_to_open": f"{p(paths['decision_intake'])} | {p(paths['staging'])}",
            "template_row_to_copy": "",
            "fields_to_replace": "",
            "expected_result": "Valid rows move only into review-only staging guidance; invalid rows explain what to fix.",
            "guardrail": "No publish-ready lane is created.",
        },
    ]


def report_lines(manifest: Dict[str, Any], steps: List[Dict[str, str]]) -> List[str]:
    lines = [
        "# HSD Manual Operator Decision Walkthrough",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        "This report tells the operator exactly which latest files to open, which template row to copy, what fields to replace, and how to rerun validation.",
        "It does not edit the inbox, approve anything, move files, publish, or create a publish-ready lane.",
        "",
        "## Latest Files",
        "",
    ]
    for label, value in manifest["latest_files"].items():
        lines.append(f"- {label}: `{value or 'missing'}`")
    lines.extend(["", "## Steps", ""])
    for step in steps:
        lines.extend(
            [
                f"### {step['step_number']}. {step['step_title']}",
                "",
                f"- Action: {step['action']}",
                f"- File to open: `{step['file_to_open'] or 'n/a'}`",
                f"- Template row to copy: {step['template_row_to_copy'] or 'n/a'}",
                f"- Fields to replace: {step['fields_to_replace'] or 'n/a'}",
                f"- Expected result: {step['expected_result']}",
                f"- Guardrail: {step['guardrail']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Guardrails",
            "",
            "- Report-only.",
            "- Does not write `operator/inbox/manual_visual_qa_operator_decisions.csv`.",
            "- Does not approve, publish, move files, or create a publish-ready lane.",
            "- Paid APIs remain false.",
            "",
        ]
    )
    return lines


def main() -> None:
    paths = {
        "preview": first_existing("render_handoff_top_packet/draft_preview.png"),
        "qa_report": first_existing("manual_visual_qa_report.md"),
        "template_csv": first_existing("manual_visual_qa_operator_decision_template.csv"),
        "template_md": first_existing("manual_visual_qa_operator_decision_template.md"),
        "decision_intake": first_existing("manual_visual_qa_operator_decision_intake.md"),
        "staging": first_existing("manual_post_approval_render_staging.md"),
        "draft_csv": first_existing("manual_visual_qa_operator_decision_draft.csv"),
    }
    template_rows = read_csv_rows(paths["template_csv"])
    steps = build_steps(paths, template_rows)
    missing = [key for key, value in paths.items() if key not in {"decision_intake", "staging"} and not value]
    status = "walkthrough_ready" if not missing else "walkthrough_missing_render_artifacts"
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "approval_status": "not_approved_walkthrough_only",
        "latest_files": {key: p(value) for key, value in paths.items()},
        "operator_inbox_target": INBOX_PATH,
        "missing_required_inputs": missing,
        "template_row_count": len(template_rows),
        "steps": steps,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "report_only": True,
            "writes_operator_inbox": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "copy_to_publish_lane": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, steps, WALKTHROUGH_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest, steps)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
