from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-visual-qa-approval-intake-v1.0.0-review-only"
OUT_MD = output_path("manual_visual_qa_approval_intake.md")
OUT_CSV = output_path("manual_visual_qa_approval_intake.csv")
OUT_JSON = output_path("manual_visual_qa_approval_intake.json")
ALLOWED_DECISIONS = "approve_for_manual_next_step|hold|revise"

INTAKE_FIELDS = [
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


def missing_required_paths(paths: Dict[str, Path | None]) -> List[str]:
    return [name for name, path in paths.items() if path is None]


def checklist_summary(rows: List[Dict[str, str]]) -> Dict[str, int]:
    automated_rows = [row for row in rows if clean(row.get("qa_result")) not in {"human_required"}]
    return {
        "checklist_rows": len(rows),
        "automated_rows": len(automated_rows),
        "human_required_rows": len(rows) - len(automated_rows),
        "blank_operator_decisions": sum(1 for row in rows if clean(row.get("operator_decision")) == "operator_fill_required"),
    }


def build_intake_row(paths: Dict[str, Path | None], qa_manifest: Dict[str, Any], checklist_rows: List[Dict[str, str]]) -> Dict[str, str]:
    summary = qa_manifest.get("summary") if isinstance(qa_manifest.get("summary"), dict) else {}
    hold_count = clean(summary.get("hold_count")) or "0"
    qa_status = clean(qa_manifest.get("status")) or "missing_visual_qa_manifest"
    preview_path = clean(qa_manifest.get("preview_path"))
    if not preview_path and paths.get("preview"):
        preview_path = paths["preview"].as_posix()

    if qa_status == "human_review_required" and hold_count == "0":
        next_step = "Operator may record approve_for_manual_next_step only after opening the preview and confirming every required visual/source note by eye."
    elif qa_status:
        next_step = "Operator should hold or revise until automated holds and visual/source concerns are resolved."
    else:
        next_step = "Run .\\hsd.cmd run -Mode render first, then review the generated visual QA files."

    return {
        "intake_id": "manual_visual_qa_preview_1",
        "preview_path": preview_path,
        "qa_status": qa_status,
        "automated_hold_count": hold_count,
        "qa_report_path": paths["report"].as_posix() if paths.get("report") else "",
        "qa_manifest_path": paths["manifest"].as_posix() if paths.get("manifest") else "",
        "qa_checklist_path": paths["checklist"].as_posix() if paths.get("checklist") else "",
        "allowed_decisions": ALLOWED_DECISIONS,
        "operator_decision": "operator_fill_required",
        "operator_notes": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "required_evidence": "Open draft_preview.png plus manual_visual_qa_report.md; confirm readable text, draft watermark, footer guardrail, source-safe copy, crop safety, and any checklist holds.",
        "next_manual_step": next_step,
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "paid_apis": "false",
    }


def report_lines(manifest: Dict[str, Any], row: Dict[str, str]) -> List[str]:
    missing = manifest["inputs"]["missing"]
    status = manifest["status"]
    lines = [
        "# HSD Manual Visual QA Approval Intake",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{status}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        "This file gives the operator one place to record the human decision for a draft preview.",
        "It does not approve the preview by itself, does not publish, and does not move anything into a publish-ready lane.",
        "",
        "## Operator Decision",
        "",
        f"- Intake CSV: `manual_visual_qa_approval_intake.csv`",
        f"- Allowed decisions: `{ALLOWED_DECISIONS}`",
        "- Fill `operator_decision`, `operator_notes`, `operator_name`, and `reviewed_at_local` manually.",
        "- Use `approve_for_manual_next_step` only for the next manual production step, not for publishing.",
        "",
        "## Current Draft",
        "",
        f"- Preview: `{row['preview_path'] or 'missing'}`",
        f"- QA status: `{row['qa_status']}`",
        f"- Automated hold count: `{row['automated_hold_count']}`",
        f"- Next manual step: {row['next_manual_step']}",
        "",
        "## Guardrails",
        "",
        "- Publish-ready remains false.",
        "- Auto-approval remains false.",
        "- Auto-publish remains false.",
        "- Paid APIs remain false.",
        "",
    ]
    if missing:
        lines.extend(["## Missing Inputs", ""])
        lines.extend(f"- `{item}`" for item in missing)
        lines.append("")
    lines.extend(
        [
            "## Stop/Go Rule",
            "",
            "- Stop if the preview has an automated hold.",
            "- Stop if the operator cannot confirm text readability, crop safety, source safety, or draft guardrails.",
            "- Continue only by manually recording a decision in the intake CSV.",
            "- Publishing still requires a separate future approval lane.",
            "",
        ]
    )
    return lines


def main() -> None:
    paths = {
        "preview": first_existing("render_handoff_top_packet/draft_preview.png"),
        "report": first_existing("manual_visual_qa_report.md"),
        "manifest": first_existing("manual_visual_qa_manifest.json"),
        "checklist": first_existing("manual_visual_qa_checklist.csv"),
    }
    qa_manifest = read_json(paths["manifest"])
    checklist = read_csv_rows(paths["checklist"])
    row = build_intake_row(paths, qa_manifest, checklist)
    missing = missing_required_paths(paths)
    status = "ready_for_manual_decision" if not missing else "blocked_missing_visual_qa_inputs"

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "approval_status": "not_approved_operator_input_required",
        "inputs": {
            "preview_path": paths["preview"].as_posix() if paths.get("preview") else "",
            "qa_report_path": paths["report"].as_posix() if paths.get("report") else "",
            "qa_manifest_path": paths["manifest"].as_posix() if paths.get("manifest") else "",
            "qa_checklist_path": paths["checklist"].as_posix() if paths.get("checklist") else "",
            "missing": missing,
        },
        "visual_qa": {
            "status": row["qa_status"],
            "automated_hold_count": row["automated_hold_count"],
            **checklist_summary(checklist),
        },
        "intake_row": row,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "operator_decision_required": True,
            "auto_approval": False,
            "auto_publish": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, [row], INTAKE_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest, row)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
