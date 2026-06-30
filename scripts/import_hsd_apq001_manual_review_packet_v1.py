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


VERSION = "hsd-apq001-manual-review-importer-v1-review-only"
GENERATED_BY = "scripts/import_hsd_apq001_manual_review_packet_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
PACKET_DIR_REL = Path("apq001_manual_asset_review_packet")
MANUAL_ASSET_REVIEW_REL = PACKET_DIR_REL / "manual_asset_review_intake.csv"
RENDERER_HANDOFF_REL = PACKET_DIR_REL / "renderer_handoff_review_checklist.csv"
OUT_MANIFEST_REL = Path("apq001_manual_review_result_manifest.json")
OUT_REPORT_REL = Path("apq001_manual_review_result_report.md")
OUT_FINDINGS_REL = Path("apq001_manual_review_result_findings.csv")
CANDIDATE_ID = "APQ001"

MANUAL_FIELDS = [
    "review_step",
    "candidate_queue_id",
    "candidate_packet_path",
    "quarantine_source_path",
    "identity_match",
    "action_photo_quality",
    "rights_review",
    "crop_fit_square_1x1",
    "crop_fit_feed_4x5",
    "crop_fit_story_9x16",
    "operator_decision",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "move_files",
    "publishing",
]

HANDOFF_FIELDS = [
    "review_step",
    "candidate_queue_id",
    "candidate_packet_path",
    "renderer_handoff_question",
    "operator_finding",
    "renderer_handoff_recommendation",
    "revision_request",
    "operator_notes",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "renderer_behavior_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "move_files",
    "publishing",
]

FINDING_FIELDS = [
    "finding_id",
    "source_csv",
    "review_step",
    "candidate_queue_id",
    "operator_decision",
    "operator_finding",
    "renderer_handoff_recommendation",
    "revision_request",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
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

ALLOWED_MANUAL_DECISIONS = {
    "hold_asset_review",
    "needs_rights_or_identity_review",
    "suitable_for_renderer_handoff_review",
}

ALLOWED_HANDOFF_RECOMMENDATIONS = {
    "hold_renderer_handoff",
    "needs_crop_or_layout_notes",
    "suitable_for_renderer_recheck",
}

PENDING_VALUES = {
    "",
    "operator_fill_required",
    "not_supplied_in_shorthand",
}

FORBIDDEN_VALUES = {
    "approved",
    "asset_approved",
    "publish_ready",
    "render_ready",
    "renderer_approved",
}

FALSE_GUARDRAIL_FIELDS = [
    "publish_ready",
    "approval_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "move_files",
    "publishing",
]

MANUAL_SIGNAL_FIELDS = [
    "identity_match",
    "action_photo_quality",
    "rights_review",
    "crop_fit_square_1x1",
    "crop_fit_feed_4x5",
    "crop_fit_story_9x16",
    "operator_decision",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def csv_value(value: Any) -> str:
    return str(value or "").strip()


def normalized(value: Any) -> str:
    return clean(value).lower()


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


def input_csv_path(path: Path) -> Path:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return input_candidates(path)[0].resolve()


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
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


def filled(value: Any) -> bool:
    return normalized(value) not in PENDING_VALUES


def row_has_manual_signal(row: Mapping[str, str]) -> bool:
    return any(filled(row.get(field)) for field in MANUAL_SIGNAL_FIELDS)


def count_values(rows: Iterable[Mapping[str, str]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = normalized(row.get(field)) or "blank"
        counter[value] += 1
    return dict(sorted(counter.items()))


def guardrail_issues(row: Mapping[str, str], index: int, source_name: str, *, handoff: bool = False) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if normalized(row.get("review_only")) != "true":
        issues.append({"row": str(index), "source_csv": source_name, "field": "review_only", "issue": "review_only_must_be_true"})
    for field in FALSE_GUARDRAIL_FIELDS:
        if normalized(row.get(field)) != "false":
            issues.append({"row": str(index), "source_csv": source_name, "field": field, "issue": "guardrail_field_must_be_false"})
    if handoff and normalized(row.get("renderer_behavior_change")) != "false":
        issues.append(
            {
                "row": str(index),
                "source_csv": source_name,
                "field": "renderer_behavior_change",
                "issue": "renderer_behavior_change_must_be_false",
            }
        )
    for field, value in row.items():
        if normalized(value) in FORBIDDEN_VALUES:
            issues.append({"row": str(index), "source_csv": source_name, "field": field, "issue": "forbidden_approval_or_publish_value"})
    return issues


def validate_manual_rows(rows: list[Mapping[str, str]], fields: list[str], source_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    source_name = MANUAL_ASSET_REVIEW_REL.as_posix()
    if not source_path.exists():
        return [{"row": "0", "source_csv": source_name, "field": "input_csv", "issue": "manual_asset_review_intake_missing"}]
    for field in MANUAL_FIELDS:
        if field not in fields:
            issues.append({"row": "1", "source_csv": source_name, "field": field, "issue": "required_field_missing"})
    for index, row in enumerate(rows, start=2):
        if clean(row.get("candidate_queue_id")) != CANDIDATE_ID:
            issues.append({"row": str(index), "source_csv": source_name, "field": "candidate_queue_id", "issue": "unexpected_candidate_queue_id"})
        decision = normalized(row.get("operator_decision"))
        if decision not in ALLOWED_MANUAL_DECISIONS and decision not in PENDING_VALUES:
            issues.append({"row": str(index), "source_csv": source_name, "field": "operator_decision", "issue": "operator_decision_not_allowed"})
        issues.extend(guardrail_issues(row, index, source_name))
    return issues


def validate_handoff_rows(rows: list[Mapping[str, str]], fields: list[str], source_path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    source_name = RENDERER_HANDOFF_REL.as_posix()
    if not source_path.exists():
        return [{"row": "0", "source_csv": source_name, "field": "input_csv", "issue": "renderer_handoff_review_checklist_missing"}]
    for field in HANDOFF_FIELDS:
        if field not in fields:
            issues.append({"row": "1", "source_csv": source_name, "field": field, "issue": "required_field_missing"})
    seen_steps: set[str] = set()
    for index, row in enumerate(rows, start=2):
        if clean(row.get("candidate_queue_id")) != CANDIDATE_ID:
            issues.append({"row": str(index), "source_csv": source_name, "field": "candidate_queue_id", "issue": "unexpected_candidate_queue_id"})
        step = clean(row.get("review_step"))
        if not step:
            issues.append({"row": str(index), "source_csv": source_name, "field": "review_step", "issue": "review_step_blank"})
        elif step in seen_steps:
            issues.append({"row": str(index), "source_csv": source_name, "field": "review_step", "issue": "duplicate_review_step"})
        seen_steps.add(step)
        recommendation = normalized(row.get("renderer_handoff_recommendation"))
        if recommendation not in ALLOWED_HANDOFF_RECOMMENDATIONS and recommendation not in PENDING_VALUES:
            issues.append(
                {
                    "row": str(index),
                    "source_csv": source_name,
                    "field": "renderer_handoff_recommendation",
                    "issue": "renderer_handoff_recommendation_not_allowed",
                }
            )
        issues.extend(guardrail_issues(row, index, source_name, handoff=True))
    return issues


def finding_rows(manual_rows: list[Mapping[str, str]], handoff_rows: list[Mapping[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    counter = 1
    for row in manual_rows:
        if not row_has_manual_signal(row):
            continue
        out.append(
            {
                "finding_id": f"APQMR{counter:03d}",
                "source_csv": MANUAL_ASSET_REVIEW_REL.as_posix(),
                "review_step": csv_value(row.get("review_step")),
                "candidate_queue_id": csv_value(row.get("candidate_queue_id")),
                "operator_decision": normalized(row.get("operator_decision")),
                "operator_finding": "",
                "renderer_handoff_recommendation": "",
                "revision_request": "",
                "operator_notes": csv_value(row.get("operator_notes")),
                "reviewed_by": csv_value(row.get("reviewed_by")),
                "reviewed_at_local": csv_value(row.get("reviewed_at_local")),
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
        )
        counter += 1
    for row in handoff_rows:
        if not filled(row.get("renderer_handoff_recommendation")) and not filled(row.get("operator_finding")):
            continue
        out.append(
            {
                "finding_id": f"APQMR{counter:03d}",
                "source_csv": RENDERER_HANDOFF_REL.as_posix(),
                "review_step": csv_value(row.get("review_step")),
                "candidate_queue_id": csv_value(row.get("candidate_queue_id")),
                "operator_decision": "",
                "operator_finding": csv_value(row.get("operator_finding")),
                "renderer_handoff_recommendation": normalized(row.get("renderer_handoff_recommendation")),
                "revision_request": csv_value(row.get("revision_request")),
                "operator_notes": csv_value(row.get("operator_notes")),
                "reviewed_by": "",
                "reviewed_at_local": "",
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
        )
        counter += 1
    return out


def status_for(*, missing_inputs: bool, issues: list[Mapping[str, str]], findings: list[Mapping[str, str]]) -> str:
    if missing_inputs:
        return "apq001_manual_review_packet_missing_inputs"
    if issues:
        return "apq001_manual_review_import_has_validation_issues"
    if findings:
        return "apq001_manual_review_result_artifacts_ready"
    return "apq001_manual_review_waiting_for_filled_packet"


def render_report(payload: Mapping[str, Any], findings: list[Mapping[str, str]]) -> str:
    lines = [
        "# APQ001 Manual Review Import Result",
        "",
        f"Status: `{payload['status']}`",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Manual asset review CSV: `{payload['manual_asset_review_csv']}`",
        f"Renderer handoff checklist CSV: `{payload['renderer_handoff_review_csv']}`",
        "",
        "This importer reads the filled APQ001 manual review packet and writes review-only result artifacts. It does not approve the asset, create `.approved` markers, move files into renderer/headshot/approved folders, publish, or change renderer behavior.",
        "",
        "## Counts",
        "",
        f"- Manual asset review rows: `{payload['manual_asset_review_rows']}`",
        f"- Renderer handoff review rows: `{payload['renderer_handoff_rows']}`",
        f"- Filled result findings: `{payload['finding_rows']}`",
        f"- Validation issues: `{payload['validation_issue_count']}`",
        "",
        "## Manual Asset Decisions",
        "",
    ]
    for decision, count in payload["manual_operator_decision_counts"].items():
        lines.append(f"- `{decision}`: `{count}`")
    if not payload["manual_operator_decision_counts"]:
        lines.append("- None")

    lines.extend(["", "## Renderer Handoff Recommendations", ""])
    for recommendation, count in payload["renderer_handoff_recommendation_counts"].items():
        lines.append(f"- `{recommendation}`: `{count}`")
    if not payload["renderer_handoff_recommendation_counts"]:
        lines.append("- None")

    lines.extend(["", "## Findings", ""])
    if findings:
        for row in findings:
            detail = row["renderer_handoff_recommendation"] or row["operator_decision"] or "manual_note"
            lines.append(f"- `{row['finding_id']}` `{row['review_step']}`: `{detail}`")
    else:
        lines.append("- None yet.")

    lines.extend(["", "## Validation Issues", ""])
    if payload["validation_issues"]:
        for issue in payload["validation_issues"]:
            lines.append(
                f"- `{issue.get('source_csv')}` row `{issue.get('row')}` field `{issue.get('field')}`: `{issue.get('issue')}`"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Review-only and artifact-only.",
            "- No image edits.",
            "- No new downloads.",
            "- No approval-state changes.",
            "- No .approved marker writes.",
            "- No headshot, renderer, or approved-folder writes.",
            "- No publish-ready lane.",
            "- No publishing.",
            "- No renderer behavior changes.",
        ]
    )
    return "\n".join(lines)


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    manual_path = input_csv_path(Path(args.manual_asset_review_csv) if args.manual_asset_review_csv else MANUAL_ASSET_REVIEW_REL)
    handoff_path = input_csv_path(Path(args.renderer_handoff_review_csv) if args.renderer_handoff_review_csv else RENDERER_HANDOFF_REL)
    manual_rows, manual_fields = read_csv_rows(manual_path)
    handoff_rows, handoff_fields = read_csv_rows(handoff_path)
    issues = [
        *validate_manual_rows(manual_rows, manual_fields, manual_path),
        *validate_handoff_rows(handoff_rows, handoff_fields, handoff_path),
    ]
    findings = finding_rows(manual_rows, handoff_rows)
    missing_inputs = not manual_path.exists() or not handoff_path.exists()
    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status_for(missing_inputs=missing_inputs, issues=issues, findings=findings),
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "candidate_queue_id": CANDIDATE_ID,
        "manual_asset_review_csv": str(manual_path),
        "renderer_handoff_review_csv": str(handoff_path),
        "manual_asset_review_rows": len(manual_rows),
        "renderer_handoff_rows": len(handoff_rows),
        "finding_rows": len(findings),
        "manual_operator_decision_counts": count_values(manual_rows, "operator_decision"),
        "renderer_handoff_recommendation_counts": count_values(handoff_rows, "renderer_handoff_recommendation"),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "result_findings_csv": str(relative_output_path(OUT_FINDINGS_REL)),
        "review_only": True,
        "artifact_only": True,
        "image_edits": False,
        "new_downloads": False,
        "asset_downloads": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "approval_state_change": False,
        "auto_approval": False,
        "approved_marker_writes": False,
        "headshot_writes": False,
        "renderer_behavior_change": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
        "paid_apis": False,
    }
    write_csv(relative_output_path(OUT_FINDINGS_REL), findings, FINDING_FIELDS)
    write_json(relative_output_path(OUT_MANIFEST_REL), payload)
    write_text(relative_output_path(OUT_REPORT_REL), render_report(payload, findings))
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import APQ001 manual review packet into review-only result artifacts.")
    parser.add_argument("--manual-asset-review-csv", default="")
    parser.add_argument("--renderer-handoff-review-csv", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_result(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "manual_asset_review_rows": payload["manual_asset_review_rows"],
                "renderer_handoff_rows": payload["renderer_handoff_rows"],
                "finding_rows": payload["finding_rows"],
                "validation_issue_count": payload["validation_issue_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["validation_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
