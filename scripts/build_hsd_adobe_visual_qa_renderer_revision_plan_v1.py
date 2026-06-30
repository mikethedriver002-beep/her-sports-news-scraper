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

from hsd_run_io import output_path, run_output_dir


VERSION = "hsd-adobe-visual-qa-renderer-revision-plan-v1-review-only"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
IN_REVISION_REQUESTS_REL = Path("adobe_visual_qa_revision_requests.csv")
OUT_PLAN_CSV_REL = Path("adobe_visual_qa_renderer_revision_plan.csv")
OUT_PLAN_MD_REL = Path("adobe_visual_qa_renderer_revision_plan.md")
OUT_PLAN_JSON_REL = Path("adobe_visual_qa_renderer_revision_plan.json")
GENERATED_BY = "scripts/build_hsd_adobe_visual_qa_renderer_revision_plan_v1.py"

INPUT_REQUIRED_FIELDS = [
    "revision_id",
    "format",
    "operator_decision",
    "revision_request",
    "operator_notes",
    "crop_fit",
    "title_safety",
    "score_rail_dashboard_violation",
    "lower_stat_strip_violation",
    "logo_readiness",
    "action_photo_suitability",
]

REVISION_REQUEST_FIELDS = [
    *INPUT_REQUIRED_FIELDS,
    "review_only",
    "artifact_only",
    "asset_downloads",
    "image_edits",
    "approval_state_change",
    "approved_marker_writes",
    "publish_ready",
    "publishing",
    "move_files",
]

PLAN_FIELDS = [
    "plan_id",
    "source_revision_id",
    "priority",
    "format",
    "renderer_area",
    "issue_bucket",
    "operator_decision",
    "revision_request",
    "operator_notes",
    "renderer_planning_note",
    "next_manual_action",
    "review_only",
    "artifact_only",
    "asset_downloads",
    "image_edits",
    "renderer_behavior_changed",
    "approval_state_change",
    "approved_marker_writes",
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


def input_csv_path(path: Path = IN_REVISION_REQUESTS_REL) -> Path:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return input_candidates(path)[0].resolve()


def read_revision_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return [{str(key): csv_value(value) for key, value in row.items()} for row in reader], list(reader.fieldnames or [])


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def normalized(value: Any) -> str:
    return clean(value).lower()


def is_issue(value: Any) -> bool:
    return normalized(value) not in {"", "none", "no", "pass", "passes", "ok", "safe"}


def renderer_area(row: Mapping[str, str]) -> str:
    text = " ".join(
        [
            normalized(row.get("format")),
            normalized(row.get("revision_request")),
            normalized(row.get("operator_notes")),
        ]
    )
    if "story" in text or "safe zone" in text or "upper text" in text or "top interface" in text:
        return "story_title_safe_zone"
    if "square" in text or "1x1" in text or "score grid" in text:
        return "square_score_grid"
    if "contact_sheet" in text or "contact sheet" in text:
        return "contact_sheet_rerender"
    if "score" in text or "rail" in text or "dashboard" in text or "widget" in text:
        return "score_rail_typography"
    return "renderer_revision_planning"


def issue_bucket(row: Mapping[str, str]) -> str:
    buckets: list[str] = []
    if is_issue(row.get("score_rail_dashboard_violation")):
        buckets.append("score_rail_dashboard_violation")
    if is_issue(row.get("lower_stat_strip_violation")):
        buckets.append("lower_stat_strip_violation")
    if is_issue(row.get("title_safety")):
        buckets.append("title_safe_zone")
    if is_issue(row.get("crop_fit")):
        buckets.append("crop_fit")
    if is_issue(row.get("logo_readiness")):
        buckets.append("logo_readiness")
    if is_issue(row.get("action_photo_suitability")):
        buckets.append("action_photo_suitability")
    return "|".join(buckets) or "manual_revision_request"


def priority(row: Mapping[str, str]) -> str:
    area = renderer_area(row)
    score_issue = normalized(row.get("score_rail_dashboard_violation"))
    title_issue = normalized(row.get("title_safety"))
    if area in {"story_title_safe_zone", "square_score_grid"}:
        return "P0"
    if score_issue == "major" or title_issue in {"hold", "revise", "major"}:
        return "P0"
    if is_issue(row.get("score_rail_dashboard_violation")) or is_issue(row.get("lower_stat_strip_violation")):
        return "P1"
    if area == "contact_sheet_rerender":
        return "P2"
    return "P2"


def planning_note(row: Mapping[str, str]) -> str:
    area = renderer_area(row)
    if area == "story_title_safe_zone":
        return "Plan a review-only layout adjustment that adds vertical safe-zone offset for 9x16 story text and brand marks."
    if area == "square_score_grid":
        return "Plan a review-only score-grid simplification for 1x1 so the rail reads as open typography instead of boxed widgets."
    if area == "score_rail_typography":
        return "Plan a review-only score rail treatment with softer texture integration and less enclosed dashboard framing."
    if area == "contact_sheet_rerender":
        return "Rerun contact sheet review only after individual format revision planning is complete."
    return "Carry this Adobe visual QA note into review-only renderer revision planning."


def next_manual_action(row: Mapping[str, str]) -> str:
    area = renderer_area(row)
    if area == "contact_sheet_rerender":
        return "After format-specific plans are reviewed, regenerate contact sheet artifacts and rerun Adobe visual QA import."
    return "Review this plan row manually before any separate renderer implementation lane; do not edit renderer behavior in this planning packet."


def build_plan_rows(revision_rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, row in enumerate(revision_rows, start=1):
        rows.append(
            {
                "plan_id": f"AVQRP{index:03d}",
                "source_revision_id": clean(row.get("revision_id")),
                "priority": priority(row),
                "format": clean(row.get("format")),
                "renderer_area": renderer_area(row),
                "issue_bucket": issue_bucket(row),
                "operator_decision": normalized(row.get("operator_decision")),
                "revision_request": csv_value(row.get("revision_request")),
                "operator_notes": csv_value(row.get("operator_notes")),
                "renderer_planning_note": planning_note(row),
                "next_manual_action": next_manual_action(row),
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "image_edits": "false",
                "renderer_behavior_changed": "false",
                "approval_state_change": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "publishing": "false",
                "move_files": "false",
            }
        )
    return rows


def validate_inputs(revision_rows: list[Mapping[str, str]], fields: list[str], source_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not source_path.exists():
        return [{"row": "0", "field": "input_csv", "issue": "adobe_visual_qa_revision_requests_missing", "detail": str(source_path)}]
    for field in INPUT_REQUIRED_FIELDS:
        if field not in fields:
            issues.append({"row": "1", "field": field, "issue": "required_field_missing"})
    seen_ids: set[str] = set()
    for index, row in enumerate(revision_rows, start=2):
        revision_id = clean(row.get("revision_id"))
        if not revision_id:
            issues.append({"row": str(index), "field": "revision_id", "issue": "required_revision_id_blank"})
        elif revision_id in seen_ids:
            issues.append({"row": str(index), "field": "revision_id", "issue": "duplicate_revision_id"})
        seen_ids.add(revision_id)
        if not clean(row.get("format")):
            issues.append({"row": str(index), "field": "format", "issue": "required_format_blank"})
        if normalized(row.get("operator_decision")) not in {"hold", "revise", "approve_for_manual_next_step"}:
            issues.append({"row": str(index), "field": "operator_decision", "issue": "operator_decision_not_allowed"})
        if not clean(row.get("revision_request")) and not clean(row.get("operator_notes")):
            issues.append({"row": str(index), "field": "revision_request", "issue": "revision_or_notes_required"})
        for field in ["asset_downloads", "image_edits", "approval_state_change", "approved_marker_writes", "publish_ready", "publishing", "move_files"]:
            if normalized(row.get(field)) == "true":
                issues.append({"row": str(index), "field": field, "issue": "upstream_revision_request_guardrail_truthy"})
    return issues


def validate_plan_rows(plan_rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for index, row in enumerate(plan_rows, start=2):
        for field in [
            "asset_downloads",
            "image_edits",
            "renderer_behavior_changed",
            "approval_state_change",
            "approved_marker_writes",
            "publish_ready",
            "publishing",
            "move_files",
        ]:
            if normalized(row.get(field)) != "false":
                issues.append({"row": str(index), "field": field, "issue": "plan_rows_must_keep_guardrail_false"})
        if normalized(row.get("review_only")) != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "plan_rows_must_remain_review_only"})
    return issues


def render_report(payload: Mapping[str, Any], plan_rows: list[Mapping[str, str]]) -> str:
    lines = [
        "# HSD Adobe Visual QA Renderer Revision Plan",
        "",
        f"Status: `{payload['status']}`",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Input CSV: `{payload['source_revision_requests_csv']}`",
        "",
        "This is a review-only renderer planning artifact. It converts Adobe/Gemini manual visual QA revision requests into prioritized planning rows. It does not edit renderer behavior, images, assets, approvals, `.approved` markers, publish-ready state, or publishing.",
        "",
        "## Counts",
        "",
        f"- Revision request rows: `{payload['revision_request_rows']}`",
        f"- Plan rows: `{payload['plan_rows']}`",
        f"- Validation issues: `{payload['validation_issue_count']}`",
        "",
        "## Priority Counts",
        "",
    ]
    for item, count in payload["priority_counts"].items():
        lines.append(f"- `{item}`: `{count}`")
    if not payload["priority_counts"]:
        lines.append("- None")
    lines.extend(["", "## Plan Rows", ""])
    if plan_rows:
        for row in plan_rows:
            lines.append(
                "- "
                f"`{row['plan_id']}` `{row['priority']}` `{row['format']}` `{row['renderer_area']}`: "
                f"{row['renderer_planning_note']}"
            )
    else:
        lines.append("- None yet. Run the Adobe visual QA importer after manual review rows are filled.")
    lines.extend(["", "## Validation Issues", ""])
    if payload["validation_issues"]:
        for issue in payload["validation_issues"]:
            detail = f" detail=`{issue.get('detail')}`" if issue.get("detail") else ""
            lines.append(f"- row `{issue.get('row')}` field `{issue.get('field')}`: `{issue.get('issue')}`{detail}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Review-only and artifact-only.",
            "- No image edits.",
            "- No renderer behavior changes.",
            "- No downloads or source fetching.",
            "- No asset approval or approval-state changes.",
            "- No .approved marker writes.",
            "- No publish-ready lane.",
            "- No publishing.",
        ]
    )
    return "\n".join(lines)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    source_path = input_csv_path(Path(args.input_csv) if args.input_csv else IN_REVISION_REQUESTS_REL)
    revision_rows, fields = read_revision_rows(source_path)
    input_issues = validate_inputs(revision_rows, fields, source_path)
    plan_rows = build_plan_rows(revision_rows) if not input_issues else []
    plan_issues = validate_plan_rows(plan_rows)
    issues = [*input_issues, *plan_issues]
    priority_counts = dict(sorted(Counter(row["priority"] for row in plan_rows).items()))
    area_counts = dict(sorted(Counter(row["renderer_area"] for row in plan_rows).items()))
    status = "adobe_visual_qa_renderer_revision_plan_ready"
    if not source_path.exists():
        status = "adobe_visual_qa_revision_requests_missing"
    elif issues:
        status = "adobe_visual_qa_renderer_revision_plan_has_validation_issues"
    elif not plan_rows:
        status = "adobe_visual_qa_renderer_revision_plan_waiting_for_revision_requests"

    out_csv = output_rel(OUT_PLAN_CSV_REL)
    out_md = output_rel(OUT_PLAN_MD_REL)
    out_json = output_rel(OUT_PLAN_JSON_REL)
    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_at_utc": generated_at,
        "generated_by": GENERATED_BY,
        "source_revision_requests_csv": str(source_path),
        "plan_csv": str(out_csv),
        "plan_md": str(out_md),
        "plan_json": str(out_json),
        "revision_request_rows": len(revision_rows),
        "plan_rows": len(plan_rows),
        "priority_counts": priority_counts,
        "renderer_area_counts": area_counts,
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "review_only": True,
        "artifact_only": True,
        "paid_apis": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "image_edits": False,
        "renderer_behavior_changed": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
    }
    write_csv(out_csv, plan_rows, PLAN_FIELDS)
    write_text(out_md, render_report(payload, plan_rows))
    write_json(out_json, payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only renderer revision plan from Adobe visual QA requests.")
    parser.add_argument("--input-csv", default="", help="Optional alternate adobe_visual_qa_revision_requests.csv path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "revision_request_rows": payload["revision_request_rows"],
                "plan_rows": payload["plan_rows"],
                "validation_issue_count": payload["validation_issue_count"],
                "review_only": True,
                "asset_downloads": False,
                "image_edits": False,
                "renderer_behavior_changed": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            },
            indent=2,
        )
    )
    return 1 if payload["validation_issues"] or payload["status"].endswith("_missing") else 0


if __name__ == "__main__":
    raise SystemExit(main())
