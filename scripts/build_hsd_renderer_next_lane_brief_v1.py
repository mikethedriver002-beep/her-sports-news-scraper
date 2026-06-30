from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-renderer-next-lane-brief-v1-review-only"
GENERATED_BY = "scripts/build_hsd_renderer_next_lane_brief_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
ADOBE_SPEC_JSON_REL = Path("adobe_visual_qa_renderer_revision_spec.json")
ADOBE_SPEC_CSV_REL = Path("adobe_visual_qa_renderer_revision_spec.csv")
APQ001_MANIFEST_REL = Path("apq001_renderer_recheck_packet/manifest.json")
APQ001_PLAN_REL = Path("apq001_renderer_recheck_packet/renderer_recheck_plan.csv")
OUT_DIR_REL = Path("renderer_next_lane_brief")
OUT_MANIFEST_REL = OUT_DIR_REL / "manifest.json"
OUT_BRIEF_REL = OUT_DIR_REL / "README.md"
OUT_QUEUE_REL = OUT_DIR_REL / "next_renderer_lane_task_queue.csv"
OUT_CHECKLIST_REL = OUT_DIR_REL / "next_renderer_lane_guardrail_checklist.csv"
OUT_PROMPT_REL = OUT_DIR_REL / "next_prompt_to_send_codex.md"

QUEUE_FIELDS = [
    "task_id",
    "source_packet",
    "source_id",
    "priority",
    "renderer_area",
    "task_title",
    "task_summary",
    "acceptance_check",
    "verification_artifact",
    "next_manual_action",
    "candidate_quarantine_path",
    "review_only",
    "artifact_only",
    "image_edits",
    "new_downloads",
    "asset_downloads",
    "approval_state_change",
    "approved_marker_writes",
    "headshot_writes",
    "renderer_behavior_change",
    "publish_ready",
    "publishing",
    "move_files",
]

CHECKLIST_FIELDS = [
    "check_id",
    "scope",
    "question",
    "expected_answer",
    "artifact_to_inspect",
    "review_only",
    "artifact_only",
    "image_edits",
    "new_downloads",
    "asset_downloads",
    "approval_state_change",
    "approved_marker_writes",
    "headshot_writes",
    "renderer_behavior_change",
    "publish_ready",
    "publishing",
    "move_files",
]

FALSE_GUARDRAIL_FIELDS = [
    "image_edits",
    "new_downloads",
    "asset_downloads",
    "approval_state_change",
    "approved_marker_writes",
    "headshot_writes",
    "publish_ready",
    "publishing",
    "move_files",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def csv_value(value: Any) -> str:
    return str(value or "").strip()


def normalized(value: Any) -> str:
    return clean(value).lower()


def truthy(value: Any) -> bool:
    return normalized(value) in {"1", "true", "yes", "y", "pass", "ready"}


def output_rel(path: Path) -> Path:
    if run_output_dir():
        return output_path(path)
    return output_path(LATEST_FILES_ROOT / path)


def input_candidates(path: Path) -> list[Path]:
    candidates: list[Path] = []
    run_root = run_output_dir()
    if run_root:
        candidates.append(run_root / path)
    candidates.append(LATEST_FILES_ROOT / path)
    candidates.append(path)
    return candidates


def input_path(path: Path) -> Path:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return input_candidates(path)[0].resolve()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return [{str(key): csv_value(value) for key, value in row.items()} for row in reader], list(reader.fieldnames or [])


def guardrail_values() -> dict[str, str]:
    return {
        "review_only": "true",
        "artifact_only": "true",
        "image_edits": "false",
        "new_downloads": "false",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "approved_marker_writes": "false",
        "headshot_writes": "false",
        "renderer_behavior_change": "false",
        "publish_ready": "false",
        "publishing": "false",
        "move_files": "false",
    }


def validate_source_manifest(manifest: Mapping[str, Any], path: Path, source: str, ready_statuses: set[str]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return [{"source": source, "field": "input", "issue": "source_manifest_missing"}]
    status = clean(manifest.get("status"))
    if status not in ready_statuses:
        issues.append({"source": source, "field": "status", "issue": "source_manifest_not_ready", "detail": status})
    if manifest.get("validation_issue_count") not in {0, "0", None}:
        issues.append({"source": source, "field": "validation_issue_count", "issue": "source_manifest_has_validation_issues"})
    if not truthy(manifest.get("review_only")):
        issues.append({"source": source, "field": "review_only", "issue": "source_manifest_must_be_review_only"})
    if not truthy(manifest.get("artifact_only")):
        issues.append({"source": source, "field": "artifact_only", "issue": "source_manifest_must_be_artifact_only"})
    for field in FALSE_GUARDRAIL_FIELDS:
        if truthy(manifest.get(field)):
            issues.append({"source": source, "field": field, "issue": "source_manifest_guardrail_truthy"})
    renderer_flag = manifest.get("renderer_behavior_change", manifest.get("renderer_behavior_changed"))
    if truthy(renderer_flag):
        issues.append({"source": source, "field": "renderer_behavior", "issue": "source_manifest_renderer_behavior_truthy"})
    return issues


def validate_rows(rows: list[Mapping[str, str]], fields: list[str], required: list[str], source: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in required:
        if field not in fields:
            issues.append({"source": source, "field": field, "issue": "required_field_missing"})
    for index, row in enumerate(rows, start=2):
        if normalized(row.get("review_only")) != "true":
            issues.append({"source": source, "row": str(index), "field": "review_only", "issue": "row_must_be_review_only"})
        if normalized(row.get("artifact_only")) != "true":
            issues.append({"source": source, "row": str(index), "field": "artifact_only", "issue": "row_must_be_artifact_only"})
        for field in FALSE_GUARDRAIL_FIELDS:
            if field in row and normalized(row.get(field)) != "false":
                issues.append({"source": source, "row": str(index), "field": field, "issue": "row_guardrail_field_must_be_false"})
        renderer_value = row.get("renderer_behavior_change", row.get("renderer_behavior_changed", "false"))
        if normalized(renderer_value) != "false":
            issues.append({"source": source, "row": str(index), "field": "renderer_behavior", "issue": "row_renderer_behavior_must_be_false"})
    return issues


def adobe_queue_rows(rows: list[Mapping[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "task_id": f"RNL{len(out) + 1:03d}",
                "source_packet": "adobe_renderer_revision_spec",
                "source_id": csv_value(row.get("spec_id")),
                "priority": csv_value(row.get("priority")),
                "renderer_area": csv_value(row.get("renderer_area")),
                "task_title": csv_value(row.get("implementation_task")),
                "task_summary": csv_value(row.get("revision_spec")),
                "acceptance_check": csv_value(row.get("acceptance_check")),
                "verification_artifact": csv_value(row.get("verification_artifact")),
                "next_manual_action": csv_value(row.get("next_manual_action")),
                "candidate_quarantine_path": "",
                **guardrail_values(),
            }
        )
    return out


def apq001_queue_rows(rows: list[Mapping[str, str]], offset: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        out.append(
            {
                "task_id": f"RNL{offset + len(out) + 1:03d}",
                "source_packet": "apq001_renderer_recheck_packet",
                "source_id": csv_value(row.get("plan_id")),
                "priority": csv_value(row.get("priority")),
                "renderer_area": csv_value(row.get("renderer_recheck_area")),
                "task_title": csv_value(row.get("renderer_recheck_area")).replace("_", " ").title(),
                "task_summary": csv_value(row.get("planning_note")),
                "acceptance_check": csv_value(row.get("acceptance_check")),
                "verification_artifact": "apq001_renderer_recheck_packet/renderer_recheck_plan.csv",
                "next_manual_action": csv_value(row.get("next_manual_action")),
                "candidate_quarantine_path": csv_value(row.get("candidate_quarantine_path")),
                **guardrail_values(),
            }
        )
    return out


def checklist_rows() -> list[dict[str, str]]:
    rows = [
        {
            "scope": "renderer_behavior",
            "question": "Does this brief change renderer code or renderer behavior?",
            "expected_answer": "false",
            "artifact_to_inspect": "renderer_next_lane_brief/next_renderer_lane_task_queue.csv",
        },
        {
            "scope": "apq001_quarantine",
            "question": "Does APQ001 remain under the quarantine review-only path?",
            "expected_answer": "true",
            "artifact_to_inspect": "apq001_renderer_recheck_packet/manifest.json",
        },
        {
            "scope": "approval_publish",
            "question": "Does this brief approve assets, mark publish-ready, or publish?",
            "expected_answer": "false",
            "artifact_to_inspect": "renderer_next_lane_brief/manifest.json",
        },
        {
            "scope": "future_lane_boundary",
            "question": "Is actual renderer implementation deferred to a separate explicit PR?",
            "expected_answer": "true",
            "artifact_to_inspect": "renderer_next_lane_brief/next_prompt_to_send_codex.md",
        },
    ]
    return [
        {
            "check_id": f"RNLGC{index:03d}",
            **row,
            **guardrail_values(),
        }
        for index, row in enumerate(rows, start=1)
    ]


def status_for(adobe_path: Path, apq_manifest_path: Path, apq_plan_path: Path, issues: list[Mapping[str, str]], queue: list[Mapping[str, str]]) -> str:
    if not adobe_path.exists() or not apq_manifest_path.exists() or not apq_plan_path.exists():
        return "renderer_next_lane_brief_missing_inputs"
    if issues:
        return "renderer_next_lane_brief_has_validation_issues"
    if not queue:
        return "renderer_next_lane_brief_waiting_for_tasks"
    return "renderer_next_lane_brief_ready"


def render_brief(payload: Mapping[str, Any], queue: list[Mapping[str, str]]) -> str:
    lines = [
        "# Renderer Next Lane Brief",
        "",
        f"Status: `{payload['status']}`",
        f"Generated: `{payload['generated_at_utc']}`",
        "",
        "This review-only brief combines Adobe visual QA renderer revision tasks with APQ001 quarantine-only renderer recheck planning. It is a handoff for a future implementation lane; it does not edit renderer behavior, images, assets, approvals, marker files, publish-ready state, or publishing.",
        "",
        "## Counts",
        "",
        f"- Adobe spec rows: `{payload['adobe_spec_rows']}`",
        f"- APQ001 recheck plan rows: `{payload['apq001_plan_rows']}`",
        f"- Combined task queue rows: `{payload['task_queue_rows']}`",
        f"- Validation issues: `{payload['validation_issue_count']}`",
        "",
        "## Priority Counts",
        "",
    ]
    for priority, count in payload["priority_counts"].items():
        lines.append(f"- `{priority}`: `{count}`")
    if not payload["priority_counts"]:
        lines.append("- None")
    lines.extend(["", "## Top Tasks", ""])
    for row in queue:
        lines.append(
            "- "
            f"`{row['task_id']}` `{row['priority']}` `{row['renderer_area']}` "
            f"from `{row['source_packet']}`: {row['task_title']}"
        )
    if not queue:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- artifact_only=true",
            "- image_edits=false",
            "- new_downloads=false",
            "- asset_downloads=false",
            "- approval_state_change=false",
            "- approved_marker_writes=false",
            "- headshot_writes=false",
            "- renderer_behavior_change=false",
            "- publish_ready=false",
            "- publishing=false",
            "- move_files=false",
        ]
    )
    return "\n".join(lines)


def render_next_prompt(payload: Mapping[str, Any]) -> str:
    return f"""# Next Prompt To Send Codex

You are the HSD Project Conductor. Start from clean main. Inspect open PRs first. If none need merge-safety review, start a separate implementation lane for the next renderer work using `outputs/local/latest/files/renderer_next_lane_brief/README.md`, `outputs/local/latest/files/renderer_next_lane_brief/next_renderer_lane_task_queue.csv`, `outputs/local/latest/files/adobe_visual_qa_renderer_revision_spec.md`, and `outputs/local/latest/files/apq001_renderer_recheck_packet/renderer_recheck_handoff.md`.

Scope for that future lane: implement the smallest renderer behavior PR that addresses the P0 Adobe visual QA items first: story title safe-zone offset and square score-grid deboxing. Keep APQ001 as quarantine-only input for planning/recheck evidence only unless a separate explicit instruction says otherwise. Do not approve APQ001, do not create marker files, do not move files into renderer/headshot/approved folders, do not download assets, do not publish, and do not mark publish-ready.

Before editing renderer behavior, rerun or inspect:
- `outputs/local/latest/files/renderer_next_lane_brief/next_renderer_lane_task_queue.csv`
- `outputs/local/latest/files/renderer_next_lane_brief/next_renderer_lane_guardrail_checklist.csv`
- `outputs/local/latest/files/adobe_visual_qa_renderer_revision_spec.csv`
- `outputs/local/latest/files/apq001_renderer_recheck_packet/renderer_recheck_plan.csv`

Validation expected after that future renderer lane:
- focused renderer tests
- focused Command Center tests if visibility changes
- py_compile for changed Python files
- branch diff guardrail scan
- latest-output guardrail scan

Current brief status: `{payload['status']}` with `{payload['task_queue_rows']}` queued review-only tasks.
"""


def build_brief(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    adobe_manifest_path = input_path(Path(args.adobe_spec_json) if args.adobe_spec_json else ADOBE_SPEC_JSON_REL)
    adobe_csv_path = input_path(Path(args.adobe_spec_csv) if args.adobe_spec_csv else ADOBE_SPEC_CSV_REL)
    apq_manifest_path = input_path(Path(args.apq001_manifest) if args.apq001_manifest else APQ001_MANIFEST_REL)
    apq_plan_path = input_path(Path(args.apq001_plan) if args.apq001_plan else APQ001_PLAN_REL)

    adobe_manifest = read_json(adobe_manifest_path)
    apq_manifest = read_json(apq_manifest_path)
    adobe_rows, adobe_fields = read_csv_rows(adobe_csv_path)
    apq_rows, apq_fields = read_csv_rows(apq_plan_path)

    issues = [
        *validate_source_manifest(
            adobe_manifest,
            adobe_manifest_path,
            ADOBE_SPEC_JSON_REL.as_posix(),
            {"adobe_visual_qa_renderer_revision_spec_ready"},
        ),
        *validate_source_manifest(
            apq_manifest,
            apq_manifest_path,
            APQ001_MANIFEST_REL.as_posix(),
            {"apq001_renderer_recheck_packet_ready"},
        ),
        *validate_rows(
            adobe_rows,
            adobe_fields,
            [
                "spec_id",
                "priority",
                "format",
                "renderer_area",
                "implementation_task",
                "revision_spec",
                "acceptance_check",
                "verification_artifact",
                "review_only",
                "artifact_only",
            ],
            ADOBE_SPEC_CSV_REL.as_posix(),
        ),
        *validate_rows(
            apq_rows,
            apq_fields,
            [
                "plan_id",
                "priority",
                "renderer_recheck_area",
                "planning_note",
                "acceptance_check",
                "candidate_quarantine_path",
                "review_only",
                "artifact_only",
            ],
            APQ001_PLAN_REL.as_posix(),
        ),
    ]
    queue = [] if issues else [*adobe_queue_rows(adobe_rows), *apq001_queue_rows(apq_rows, len(adobe_rows))]
    checks = checklist_rows()
    priority_counts = dict(sorted(Counter(row["priority"] for row in queue).items()))
    source_counts = dict(sorted(Counter(row["source_packet"] for row in queue).items()))
    area_counts = dict(sorted(Counter(row["renderer_area"] for row in queue).items()))

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status_for(adobe_manifest_path, apq_manifest_path, apq_plan_path, issues, queue),
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "adobe_spec_manifest": str(adobe_manifest_path),
        "adobe_spec_csv": str(adobe_csv_path),
        "apq001_recheck_manifest": str(apq_manifest_path),
        "apq001_recheck_plan_csv": str(apq_plan_path),
        "adobe_spec_rows": len(adobe_rows),
        "apq001_plan_rows": len(apq_rows),
        "task_queue_rows": len(queue),
        "guardrail_checklist_rows": len(checks),
        "priority_counts": priority_counts,
        "source_packet_counts": source_counts,
        "renderer_area_counts": area_counts,
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "brief_md": str(output_rel(OUT_BRIEF_REL)),
        "task_queue_csv": str(output_rel(OUT_QUEUE_REL)),
        "guardrail_checklist_csv": str(output_rel(OUT_CHECKLIST_REL)),
        "next_prompt_md": str(output_rel(OUT_PROMPT_REL)),
        "review_only": True,
        "artifact_only": True,
        "paid_apis": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "image_edits": False,
        "new_downloads": False,
        "asset_downloads": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "renderer_behavior_change": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
    }

    write_csv(output_rel(OUT_QUEUE_REL), queue, QUEUE_FIELDS)
    write_csv(output_rel(OUT_CHECKLIST_REL), checks, CHECKLIST_FIELDS)
    write_json(output_rel(OUT_MANIFEST_REL), payload, sort_keys=True)
    write_text(output_rel(OUT_BRIEF_REL), render_brief(payload, queue), normalize=strip_volatile_markdown_lines)
    write_text(output_rel(OUT_PROMPT_REL), render_next_prompt(payload), normalize=strip_volatile_markdown_lines)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only renderer next-lane brief from Adobe and APQ001 planning artifacts.")
    parser.add_argument("--adobe-spec-json", default="")
    parser.add_argument("--adobe-spec-csv", default="")
    parser.add_argument("--apq001-manifest", default="")
    parser.add_argument("--apq001-plan", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_brief(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "adobe_spec_rows": payload["adobe_spec_rows"],
                "apq001_plan_rows": payload["apq001_plan_rows"],
                "task_queue_rows": payload["task_queue_rows"],
                "validation_issue_count": payload["validation_issue_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["validation_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
