from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-manual-post-approval-render-staging-v1.0.0-review-only"
OUT_MD = output_path("manual_post_approval_render_staging.md")
OUT_CSV = output_path("manual_post_approval_render_staging.csv")
OUT_JSON = output_path("manual_post_approval_render_staging.json")
ALLOWED_DECISIONS = {"approve_for_manual_next_step", "hold", "revise"}

STAGING_FIELDS = [
    "intake_id",
    "preview_path",
    "operator_decision",
    "staging_lane",
    "qa_status",
    "automated_hold_count",
    "next_safe_action",
    "blocked_reason",
    "operator_notes",
    "operator_name",
    "reviewed_at_local",
    "approval_scope",
    "source_intake_path",
    "source_qa_report_path",
    "move_files",
    "copy_to_publish_lane",
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


def parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def lane_for_row(row: Dict[str, str]) -> tuple[str, str, str]:
    decision = clean(row.get("operator_decision"))
    qa_status = clean(row.get("qa_status"))
    hold_count = parse_int(row.get("automated_hold_count"))
    approval_scope = clean(row.get("approval_scope"))

    if decision in {"", "operator_fill_required"}:
        return (
            "awaiting_operator_decision",
            "Open manual_visual_qa_approval_intake.csv and record approve_for_manual_next_step, hold, or revise with notes.",
            "operator_decision is not filled",
        )
    if decision not in ALLOWED_DECISIONS:
        return (
            "invalid_operator_decision",
            "Correct the intake decision to approve_for_manual_next_step, hold, or revise before staging.",
            f"operator_decision={decision or 'blank'} is not allowed",
        )
    if decision == "hold":
        return (
            "hold_for_operator_review",
            "Keep the draft in review; resolve the operator hold reason before any next manual production step.",
            "",
        )
    if decision == "revise":
        return (
            "revise_required",
            "Revise the draft copy, layout, source evidence, or assets, then rerun manual render and visual QA.",
            "",
        )
    if hold_count > 0:
        return (
            "blocked_approval_with_visual_qa_holds",
            "Do not advance; resolve visual QA holds and regenerate the approval intake before recording approval.",
            f"automated_hold_count={hold_count}",
        )
    if qa_status != "human_review_required":
        return (
            "blocked_approval_without_clear_visual_qa",
            "Do not advance; visual QA status must be human_review_required with zero automated holds.",
            f"qa_status={qa_status or 'missing'}",
        )
    if approval_scope != "manual_next_step_only_not_publish_ready":
        return (
            "blocked_approval_scope_mismatch",
            "Do not advance; approval scope must stay manual_next_step_only_not_publish_ready.",
            f"approval_scope={approval_scope or 'missing'}",
        )
    return (
        "approved_for_next_manual_step",
        "Operator may prepare the next manual production pass using the draft and QA notes; do not move files or publish.",
        "",
    )


def build_staging_rows(intake_rows: Iterable[Dict[str, str]], intake_path: Path | None) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for raw in intake_rows:
        lane, next_action, blocked_reason = lane_for_row(raw)
        rows.append(
            {
                "intake_id": clean(raw.get("intake_id")) or "manual_visual_qa_preview_1",
                "preview_path": clean(raw.get("preview_path")),
                "operator_decision": clean(raw.get("operator_decision")) or "operator_fill_required",
                "staging_lane": lane,
                "qa_status": clean(raw.get("qa_status")),
                "automated_hold_count": clean(raw.get("automated_hold_count")) or "0",
                "next_safe_action": next_action,
                "blocked_reason": blocked_reason,
                "operator_notes": clean(raw.get("operator_notes")),
                "operator_name": clean(raw.get("operator_name")),
                "reviewed_at_local": clean(raw.get("reviewed_at_local")),
                "approval_scope": clean(raw.get("approval_scope")) or "manual_next_step_only_not_publish_ready",
                "source_intake_path": intake_path.as_posix() if intake_path else "",
                "source_qa_report_path": clean(raw.get("qa_report_path")),
                "move_files": "false",
                "copy_to_publish_lane": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "paid_apis": "false",
            }
        )
    if not rows:
        rows.append(
            {
                "intake_id": "missing_manual_visual_qa_approval_intake",
                "preview_path": "",
                "operator_decision": "operator_fill_required",
                "staging_lane": "blocked_missing_approval_intake",
                "qa_status": "",
                "automated_hold_count": "0",
                "next_safe_action": "Run .\\hsd.cmd run -Mode render to create the approval intake, then fill the intake manually.",
                "blocked_reason": "manual_visual_qa_approval_intake.csv was not found or had no rows",
                "operator_notes": "",
                "operator_name": "",
                "reviewed_at_local": "",
                "approval_scope": "manual_next_step_only_not_publish_ready",
                "source_intake_path": intake_path.as_posix() if intake_path else "",
                "source_qa_report_path": "",
                "move_files": "false",
                "copy_to_publish_lane": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "paid_apis": "false",
            }
        )
    return rows


def counts_by_lane(rows: Iterable[Dict[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        lane = clean(row.get("staging_lane")) or "unknown"
        counts[lane] = counts.get(lane, 0) + 1
    return counts


def report_lines(manifest: Dict[str, Any], rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "# HSD Manual Post-Approval Render Staging",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Purpose",
        "",
        "This report reads the manual visual QA approval intake and separates draft previews into review-only staging lanes.",
        "It does not move files, approve publishing, auto-publish, or create a publish-ready lane.",
        "",
        "## Lane Counts",
        "",
    ]
    for lane, count in sorted(manifest["lane_counts"].items()):
        lines.append(f"- `{lane}`: `{count}`")
    lines.extend(["", "## Staging Guidance", ""])
    for lane in [
        "approved_for_next_manual_step",
        "hold_for_operator_review",
        "revise_required",
        "awaiting_operator_decision",
        "invalid_operator_decision",
        "blocked_approval_with_visual_qa_holds",
        "blocked_approval_without_clear_visual_qa",
        "blocked_approval_scope_mismatch",
        "blocked_missing_approval_intake",
    ]:
        lane_rows = [row for row in rows if row["staging_lane"] == lane]
        if not lane_rows:
            continue
        lines.extend([f"### {lane}", ""])
        for row in lane_rows:
            lines.extend(
                [
                    f"- Intake: `{row['intake_id']}`",
                    f"  Preview: `{row['preview_path'] or 'missing'}`",
                    f"  Decision: `{row['operator_decision']}`",
                    f"  Next safe action: {row['next_safe_action']}",
                    f"  Blocked reason: {row['blocked_reason'] or 'none'}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Guardrails",
            "",
            "- `move_files=false` for every row.",
            "- `copy_to_publish_lane=false` for every row.",
            "- `publish_ready=false` for every row.",
            "- `auto_approval=false` for every row.",
            "- `auto_publish=false` for every row.",
            "- Paid APIs remain false.",
            "",
            "## Stop/Go Rule",
            "",
            "- Continue only inside the named manual next action.",
            "- Stop if the lane is awaiting, invalid, blocked, hold, or revise.",
            "- Publishing requires a separate future workflow and is not authorized here.",
            "",
        ]
    )
    return lines


def main() -> None:
    intake_path = first_existing("manual_visual_qa_approval_intake.csv")
    intake_manifest_path = first_existing("manual_visual_qa_approval_intake.json")
    intake_rows = read_csv_rows(intake_path)
    staging_rows = build_staging_rows(intake_rows, intake_path)
    lane_counts = counts_by_lane(staging_rows)
    approved_count = lane_counts.get("approved_for_next_manual_step", 0)
    blocked_count = sum(count for lane, count in lane_counts.items() if lane != "approved_for_next_manual_step")
    status = "review_only_staging_ready" if approved_count and not blocked_count else "review_only_staging_needs_operator_action"
    if lane_counts.get("blocked_missing_approval_intake"):
        status = "blocked_missing_approval_intake"

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "approval_status": "not_approved_review_only_staging",
        "inputs": {
            "approval_intake_path": intake_path.as_posix() if intake_path else "",
            "approval_intake_manifest_path": intake_manifest_path.as_posix() if intake_manifest_path else "",
            "intake_row_count": len(intake_rows),
        },
        "lane_counts": lane_counts,
        "staging_rows": staging_rows,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "move_files": False,
            "copy_to_publish_lane": False,
            "auto_approval": False,
            "auto_publish": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_csv(OUT_CSV, staging_rows, STAGING_FIELDS)
    write_json(OUT_JSON, manifest)
    write_text(OUT_MD, "\n".join(report_lines(manifest, staging_rows)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
