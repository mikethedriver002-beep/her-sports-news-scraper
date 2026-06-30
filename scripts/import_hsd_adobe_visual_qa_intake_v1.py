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


VERSION = "hsd-adobe-visual-qa-intake-importer-v1-review-only"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
INTAKE_REL = Path("adobe_visual_qa_packet/manual_adobe_visual_qa_intake.csv")
OUT_MANIFEST_REL = Path("adobe_visual_qa_result_manifest.json")
OUT_REPORT_REL = Path("adobe_visual_qa_result_report.md")
OUT_REVISION_REQUESTS_REL = Path("adobe_visual_qa_revision_requests.csv")
GENERATED_BY = "scripts/import_hsd_adobe_visual_qa_intake_v1.py"

INTAKE_FIELDS = [
    "format",
    "crop_fit",
    "title_safety",
    "score_rail_dashboard_violation",
    "lower_stat_strip_violation",
    "logo_readiness",
    "action_photo_suitability",
    "operator_decision",
    "revision_request",
    "operator_notes",
]

EXPECTED_FORMATS = [
    "ig_feed_4x5",
    "ig_story_9x16",
    "square_1x1",
    "contact_sheet",
]

ALLOWED_DECISIONS = {
    "hold",
    "revise",
    "approve_for_manual_next_step",
}

PENDING_VALUES = {
    "",
    "operator_fill_required",
}

REVISION_REQUEST_FIELDS = [
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def csv_value(value: Any) -> str:
    return str(value or "").strip()


def relative_output_path(path: Path) -> Path:
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


def input_csv_path(path: Path = INTAKE_REL) -> Path:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return input_candidates(path)[0].resolve()


def read_intake_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def field_is_filled(row: Mapping[str, str], field: str) -> bool:
    return clean(row.get(field)).lower() not in PENDING_VALUES


def row_has_manual_review(row: Mapping[str, str]) -> bool:
    return any(field_is_filled(row, field) for field in INTAKE_FIELDS if field != "format")


def normalized_decision(row: Mapping[str, str]) -> str:
    return clean(row.get("operator_decision")).lower()


def should_create_revision_request(row: Mapping[str, str]) -> bool:
    decision = normalized_decision(row)
    return decision in {"hold", "revise"} or bool(clean(row.get("revision_request")))


def revision_request_rows(rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for index, row in enumerate((row for row in rows if should_create_revision_request(row)), start=1):
        out.append(
            {
                "revision_id": f"AVQR{index:03d}",
                "format": clean(row.get("format")),
                "operator_decision": normalized_decision(row),
                "revision_request": csv_value(row.get("revision_request")),
                "operator_notes": csv_value(row.get("operator_notes")),
                "crop_fit": csv_value(row.get("crop_fit")),
                "title_safety": csv_value(row.get("title_safety")),
                "score_rail_dashboard_violation": csv_value(row.get("score_rail_dashboard_violation")),
                "lower_stat_strip_violation": csv_value(row.get("lower_stat_strip_violation")),
                "logo_readiness": csv_value(row.get("logo_readiness")),
                "action_photo_suitability": csv_value(row.get("action_photo_suitability")),
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "image_edits": "false",
                "approval_state_change": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "publishing": "false",
                "move_files": "false",
            }
        )
    return out


def validate_intake(rows: list[Mapping[str, str]], fields: list[str], source_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not source_path.exists():
        return [
            {
                "row": "0",
                "field": "input_csv",
                "issue": "manual_adobe_visual_qa_intake_missing",
                "detail": str(source_path),
            }
        ]
    missing_fields = [field for field in INTAKE_FIELDS if field not in fields]
    for field in missing_fields:
        issues.append({"row": "1", "field": field, "issue": "required_field_missing"})

    seen_formats: set[str] = set()
    for index, row in enumerate(rows, start=2):
        format_name = clean(row.get("format"))
        decision = normalized_decision(row)
        if not format_name:
            issues.append({"row": str(index), "field": "format", "issue": "required_format_blank"})
        elif format_name not in EXPECTED_FORMATS:
            issues.append({"row": str(index), "field": "format", "issue": "unexpected_format"})
        elif format_name in seen_formats:
            issues.append({"row": str(index), "field": "format", "issue": "duplicate_format"})
        seen_formats.add(format_name)

        if decision not in ALLOWED_DECISIONS and decision not in PENDING_VALUES:
            issues.append({"row": str(index), "field": "operator_decision", "issue": "operator_decision_not_allowed"})
        if decision == "revise" and not clean(row.get("revision_request")):
            issues.append({"row": str(index), "field": "revision_request", "issue": "revise_decision_requires_revision_request"})

    missing_formats = [format_name for format_name in EXPECTED_FORMATS if format_name not in seen_formats]
    for format_name in missing_formats:
        issues.append({"row": "0", "field": "format", "issue": "expected_format_missing", "detail": format_name})
    return issues


def status_for(*, source_exists: bool, issues: list[Mapping[str, str]], filled_rows: int, revision_rows: int) -> str:
    if not source_exists:
        return "adobe_visual_qa_intake_missing"
    if issues:
        return "adobe_visual_qa_intake_has_validation_issues"
    if filled_rows == 0:
        return "adobe_visual_qa_waiting_for_manual_review"
    if revision_rows:
        return "adobe_visual_qa_revision_requests_ready"
    return "adobe_visual_qa_manual_next_step_review_ready"


def decision_counts(rows: Iterable[Mapping[str, str]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        decision = normalized_decision(row) or "blank"
        counter[decision] += 1
    return dict(sorted(counter.items()))


def render_report(payload: Mapping[str, Any], rows: list[Mapping[str, str]], revision_rows: list[Mapping[str, str]]) -> str:
    lines = [
        "# HSD Adobe Visual QA Intake Result",
        "",
        f"Status: `{payload['status']}`",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Input CSV: `{payload['source_intake_csv']}`",
        "",
        "This importer reads the human-filled Adobe visual QA worksheet and produces review-only planning artifacts. It does not edit images, fetch sources, download files, approve assets, change approval state, create `.approved` markers, create a publish-ready lane, or publish.",
        "",
        "## Counts",
        "",
        f"- Intake rows: `{payload['intake_rows']}`",
        f"- Filled manual review rows: `{payload['filled_manual_review_rows']}`",
        f"- Revision request rows: `{payload['revision_request_rows']}`",
        f"- Validation issues: `{payload['validation_issue_count']}`",
        "",
        "## Decisions",
        "",
    ]
    for decision, count in payload["operator_decision_counts"].items():
        lines.append(f"- `{decision}`: `{count}`")
    if not payload["operator_decision_counts"]:
        lines.append("- None")

    lines.extend(["", "## Format Rows", ""])
    for row in rows:
        lines.append(
            "- "
            f"`{clean(row.get('format'))}` decision=`{normalized_decision(row) or 'blank'}` "
            f"revision=`{csv_value(row.get('revision_request')) or 'none'}`"
        )

    lines.extend(["", "## Revision Requests", ""])
    if revision_rows:
        for row in revision_rows:
            lines.append(
                "- "
                f"`{row['revision_id']}` `{row['format']}` decision=`{row['operator_decision']}`: "
                f"{row['revision_request'] or row['operator_notes'] or 'manual revision detail not supplied'}"
            )
    else:
        lines.append("- None yet. Fill `manual_adobe_visual_qa_intake.csv` with manual Adobe/Gemini/ChatGPT review notes, then rerun this importer.")

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
            "- No paid APIs.",
            "- No source fetching.",
            "- No automatic downloads.",
            "- No image edits.",
            "- No asset approval or approval-state changes.",
            "- No .approved marker writes.",
            "- No publish-ready lane.",
            "- No publishing.",
        ]
    )
    return "\n".join(lines)


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    source_path = input_csv_path(Path(args.input_csv) if args.input_csv else INTAKE_REL)
    rows, fields = read_intake_rows(source_path)
    issues = validate_intake(rows, fields, source_path)
    filled_rows = sum(1 for row in rows if row_has_manual_review(row))
    revision_rows = revision_request_rows(rows)
    manifest_path = relative_output_path(OUT_MANIFEST_REL)
    report_path = relative_output_path(OUT_REPORT_REL)
    revision_path = relative_output_path(OUT_REVISION_REQUESTS_REL)
    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status_for(
            source_exists=source_path.exists(),
            issues=issues,
            filled_rows=filled_rows,
            revision_rows=len(revision_rows),
        ),
        "generated_at_utc": generated_at,
        "generated_by": GENERATED_BY,
        "source_intake_csv": str(source_path),
        "result_manifest": str(manifest_path),
        "result_report": str(report_path),
        "revision_requests_csv": str(revision_path),
        "intake_rows": len(rows),
        "filled_manual_review_rows": filled_rows,
        "pending_operator_fill_rows": sum(1 for row in rows if normalized_decision(row) in PENDING_VALUES),
        "revision_request_rows": len(revision_rows),
        "operator_decision_counts": decision_counts(rows),
        "expected_formats": EXPECTED_FORMATS,
        "formats_present": [clean(row.get("format")) for row in rows if clean(row.get("format"))],
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "review_only": True,
        "artifact_only": True,
        "paid_apis": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "image_edits": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
    }
    write_csv(revision_path, revision_rows, REVISION_REQUEST_FIELDS)
    write_text(report_path, render_report(payload, rows, revision_rows))
    write_json(manifest_path, payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import the review-only Adobe visual QA worksheet.")
    parser.add_argument("--input-csv", default="", help="Optional alternate manual_adobe_visual_qa_intake.csv path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_result(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "intake_rows": payload["intake_rows"],
                "filled_manual_review_rows": payload["filled_manual_review_rows"],
                "revision_request_rows": payload["revision_request_rows"],
                "validation_issue_count": payload["validation_issue_count"],
                "review_only": True,
                "asset_downloads": False,
                "image_edits": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            },
            indent=2,
        )
    )
    if payload["status"] in {"adobe_visual_qa_intake_missing", "adobe_visual_qa_intake_has_validation_issues"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
