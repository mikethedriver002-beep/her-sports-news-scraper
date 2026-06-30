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


VERSION = "hsd-apq001-renderer-recheck-packet-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apq001_renderer_recheck_packet_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
IN_MANIFEST_REL = Path("apq001_manual_review_result_manifest.json")
IN_FINDINGS_REL = Path("apq001_manual_review_result_findings.csv")
OUT_PACKET_DIR_REL = Path("apq001_renderer_recheck_packet")
OUT_MANIFEST_REL = OUT_PACKET_DIR_REL / "manifest.json"
OUT_README_REL = OUT_PACKET_DIR_REL / "README.md"
OUT_PLAN_REL = OUT_PACKET_DIR_REL / "renderer_recheck_plan.csv"
OUT_CHECKLIST_REL = OUT_PACKET_DIR_REL / "renderer_recheck_checklist.csv"
OUT_HANDOFF_REL = OUT_PACKET_DIR_REL / "renderer_recheck_handoff.md"
CANDIDATE_ID = "APQ001"
CANDIDATE_QUARANTINE_PATH = (
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
    "apq001_review_only_candidate.jpg"
)

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

PLAN_FIELDS = [
    "plan_id",
    "source_finding_id",
    "candidate_queue_id",
    "review_step",
    "priority",
    "renderer_recheck_area",
    "source_operator_decision",
    "source_operator_finding",
    "source_renderer_handoff_recommendation",
    "planning_note",
    "acceptance_check",
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
    "source_plan_id",
    "candidate_queue_id",
    "priority",
    "check_type",
    "question",
    "expected_artifact",
    "pass_condition",
    "next_manual_action",
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
    "renderer_behavior_change",
    "publish_ready",
    "publishing",
    "move_files",
]

FORBIDDEN_VALUES = {
    "approved",
    "asset_approved",
    "publish_ready",
    "render_ready",
    "renderer_approved",
}


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


def base_guardrail_values() -> dict[str, str]:
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


def validate_source_manifest(manifest: Mapping[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return [{"source": IN_MANIFEST_REL.as_posix(), "field": "input", "issue": "manual_review_result_manifest_missing"}]
    if clean(manifest.get("candidate_queue_id")) != CANDIDATE_ID:
        issues.append({"source": IN_MANIFEST_REL.as_posix(), "field": "candidate_queue_id", "issue": "unexpected_candidate_queue_id"})
    if normalized(manifest.get("status")) not in {"apq001_manual_review_result_artifacts_ready", "apq001_manual_review_waiting_for_filled_packet"}:
        issues.append({"source": IN_MANIFEST_REL.as_posix(), "field": "status", "issue": "manual_review_result_not_ready"})
    if manifest.get("validation_issue_count") not in {0, "0", None}:
        issues.append({"source": IN_MANIFEST_REL.as_posix(), "field": "validation_issue_count", "issue": "manual_review_result_has_validation_issues"})
    if not truthy(manifest.get("review_only")):
        issues.append({"source": IN_MANIFEST_REL.as_posix(), "field": "review_only", "issue": "source_manifest_must_be_review_only"})
    if not truthy(manifest.get("artifact_only")):
        issues.append({"source": IN_MANIFEST_REL.as_posix(), "field": "artifact_only", "issue": "source_manifest_must_be_artifact_only"})
    for field in FALSE_GUARDRAIL_FIELDS:
        if truthy(manifest.get(field)):
            issues.append({"source": IN_MANIFEST_REL.as_posix(), "field": field, "issue": "source_manifest_guardrail_truthy"})
    return issues


def validate_findings(rows: list[Mapping[str, str]], fields: list[str], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return [{"source": IN_FINDINGS_REL.as_posix(), "field": "input", "issue": "manual_review_result_findings_missing"}]
    for field in FINDING_FIELDS:
        if field not in fields:
            issues.append({"source": IN_FINDINGS_REL.as_posix(), "field": field, "issue": "required_field_missing"})
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        finding_id = clean(row.get("finding_id"))
        if not finding_id:
            issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": "finding_id", "issue": "finding_id_blank"})
        elif finding_id in seen_ids:
            issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": "finding_id", "issue": "duplicate_finding_id"})
        seen_ids.add(finding_id)
        if clean(row.get("candidate_queue_id")) != CANDIDATE_ID:
            issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": "candidate_queue_id", "issue": "unexpected_candidate_queue_id"})
        if normalized(row.get("review_only")) != "true":
            issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": "review_only", "issue": "finding_must_be_review_only"})
        if normalized(row.get("artifact_only")) != "true":
            issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": "artifact_only", "issue": "finding_must_be_artifact_only"})
        for field in FALSE_GUARDRAIL_FIELDS:
            if normalized(row.get(field)) != "false":
                issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": field, "issue": "finding_guardrail_field_must_be_false"})
        for field, value in row.items():
            if normalized(value) in FORBIDDEN_VALUES:
                issues.append({"source": IN_FINDINGS_REL.as_posix(), "row": str(index), "field": field, "issue": "forbidden_approval_or_publish_value"})
    return issues


def plan_area(row: Mapping[str, str]) -> str:
    recommendation = normalized(row.get("renderer_handoff_recommendation"))
    decision = normalized(row.get("operator_decision"))
    step = normalized(row.get("review_step"))
    finding = normalized(row.get("operator_finding"))
    text = " ".join([recommendation, decision, step, finding, normalized(row.get("operator_notes"))])
    if recommendation == "suitable_for_renderer_recheck" or "clarity" in text:
        return "action_photo_renderer_recheck"
    if recommendation == "needs_crop_or_layout_notes" or "crop" in text or "framing" in text:
        return "action_photo_crop_layout_notes"
    if decision == "suitable_for_renderer_handoff_review":
        return "manual_asset_review_gate"
    return "manual_review_context"


def plan_priority(row: Mapping[str, str]) -> str:
    area = plan_area(row)
    if area == "action_photo_crop_layout_notes":
        return "P0"
    if area in {"action_photo_renderer_recheck", "manual_asset_review_gate"}:
        return "P1"
    return "P2"


def planning_note(row: Mapping[str, str]) -> str:
    area = plan_area(row)
    if area == "action_photo_crop_layout_notes":
        return "Capture crop and layout constraints before any future APQ001 renderer recheck."
    if area == "action_photo_renderer_recheck":
        return "Use APQ001 only as a quarantine-local review candidate for a future renderer recheck."
    if area == "manual_asset_review_gate":
        return "Treat the manual review result as handoff-review suitability, not asset approval."
    return "Carry this APQ001 manual review finding into review-only renderer planning."


def acceptance_check(row: Mapping[str, str]) -> str:
    area = plan_area(row)
    if area == "action_photo_crop_layout_notes":
        return "Future renderer lane records square/feed/story crop notes without moving or approving the image."
    if area == "action_photo_renderer_recheck":
        return "Future renderer lane produces review-only comparison artifacts and keeps renderer behavior changes in its own PR."
    if area == "manual_asset_review_gate":
        return "Future lane keeps APQ001 in quarantine and labels the handoff as review-only."
    return "Future lane preserves all APQ001 guardrails and reports manual findings."


def next_manual_action(row: Mapping[str, str]) -> str:
    area = plan_area(row)
    if area == "action_photo_crop_layout_notes":
        return "Write format-specific crop/layout notes for APQ001 before renderer experimentation."
    if area == "action_photo_renderer_recheck":
        return "Plan an isolated renderer recheck using APQ001 as quarantine-only input."
    if area == "manual_asset_review_gate":
        return "Keep APQ001 out of approved/headshot/renderer asset folders until a separate human asset approval process exists."
    return "Review the source finding before planning renderer work."


def build_plan_rows(findings: list[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in findings:
        if not clean(row.get("operator_decision")) and not clean(row.get("renderer_handoff_recommendation")):
            continue
        plan_id = f"APQRR{len(rows) + 1:03d}"
        rows.append(
            {
                "plan_id": plan_id,
                "source_finding_id": csv_value(row.get("finding_id")),
                "candidate_queue_id": CANDIDATE_ID,
                "review_step": csv_value(row.get("review_step")),
                "priority": plan_priority(row),
                "renderer_recheck_area": plan_area(row),
                "source_operator_decision": normalized(row.get("operator_decision")),
                "source_operator_finding": csv_value(row.get("operator_finding")),
                "source_renderer_handoff_recommendation": normalized(row.get("renderer_handoff_recommendation")),
                "planning_note": planning_note(row),
                "acceptance_check": acceptance_check(row),
                "next_manual_action": next_manual_action(row),
                "candidate_quarantine_path": CANDIDATE_QUARANTINE_PATH,
                **base_guardrail_values(),
            }
        )
    return rows


def checklist_rows(plan_rows: list[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for plan in plan_rows:
        rows.append(
            {
                "check_id": f"APQRC{len(rows) + 1:03d}",
                "source_plan_id": csv_value(plan.get("plan_id")),
                "candidate_queue_id": CANDIDATE_ID,
                "priority": csv_value(plan.get("priority")),
                "check_type": csv_value(plan.get("renderer_recheck_area")),
                "question": csv_value(plan.get("acceptance_check")),
                "expected_artifact": "review_only_renderer_recheck_notes_or_contact_sheet",
                "pass_condition": "Future lane writes review-only evidence without approval, protected asset writes, renderer behavior changes in this packet, or publishing.",
                "next_manual_action": csv_value(plan.get("next_manual_action")),
                **base_guardrail_values(),
            }
        )
    rows.append(
        {
            "check_id": f"APQRC{len(rows) + 1:03d}",
            "source_plan_id": "guardrail_check",
            "candidate_queue_id": CANDIDATE_ID,
            "priority": "P0",
            "check_type": "quarantine_boundary",
            "question": "Does APQ001 remain under data/assets/quarantine/review_only_candidates only?",
            "expected_artifact": "local_path_check",
            "pass_condition": "No copies are written into renderer, headshot, approved, or publish-ready folders.",
            "next_manual_action": "Stop and report if any future lane attempts protected asset movement.",
            **base_guardrail_values(),
        }
    )
    return rows


def validate_output_rows(rows: list[Mapping[str, str]], fields: list[str], row_type: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if clean(row.get("candidate_queue_id")) != CANDIDATE_ID:
            issues.append({"source": row_type, "row": str(index), "field": "candidate_queue_id", "issue": "unexpected_candidate_queue_id"})
        for field in fields:
            if field in {"review_only", "artifact_only"}:
                if normalized(row.get(field)) != "true":
                    issues.append({"source": row_type, "row": str(index), "field": field, "issue": "output_row_must_be_true"})
            elif field in FALSE_GUARDRAIL_FIELDS:
                if normalized(row.get(field)) != "false":
                    issues.append({"source": row_type, "row": str(index), "field": field, "issue": "output_guardrail_field_must_be_false"})
    return issues


def status_for(source_manifest_path: Path, findings_path: Path, issues: list[Mapping[str, str]], plan_rows: list[Mapping[str, str]]) -> str:
    if not source_manifest_path.exists() or not findings_path.exists():
        return "apq001_renderer_recheck_packet_missing_manual_review_results"
    if issues:
        return "apq001_renderer_recheck_packet_has_validation_issues"
    if not plan_rows:
        return "apq001_renderer_recheck_packet_waiting_for_manual_review_findings"
    return "apq001_renderer_recheck_packet_ready"


def render_readme(payload: Mapping[str, Any]) -> str:
    return f"""# APQ001 Renderer Recheck Packet

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This review-only packet turns APQ001 manual review findings into renderer recheck planning notes. It does not approve APQ001, edit images, download assets, move files into renderer/headshot/approved folders, create marker files, publish, or change renderer behavior.

## Files

- `renderer_recheck_plan.csv`: planning rows derived from APQ001 manual review findings.
- `renderer_recheck_checklist.csv`: checklist rows for a future isolated renderer recheck lane.
- `renderer_recheck_handoff.md`: plain-English handoff for the future lane.
- `manifest.json`: counts and guardrail evidence.

## Candidate Boundary

APQ001 must remain at:

`{CANDIDATE_QUARANTINE_PATH}`

Do not copy it into renderer, headshot, approved, or publish-ready folders.

## Counts

- Source finding rows: `{payload['source_finding_rows']}`
- Plan rows: `{payload['plan_rows']}`
- Checklist rows: `{payload['checklist_rows']}`
- Validation issues: `{payload['validation_issue_count']}`

## Next Local Action

Use this packet to brief a future renderer recheck lane only. That future lane should generate review-only comparison evidence and keep any renderer behavior changes in a separate, explicitly reviewed PR.
"""


def render_handoff(payload: Mapping[str, Any], plan_rows: list[Mapping[str, str]]) -> str:
    lines = [
        "# APQ001 Renderer Recheck Handoff",
        "",
        f"Status: `{payload['status']}`",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Source findings: `{payload['source_findings_csv']}`",
        "",
        "This handoff is for future renderer planning only. APQ001 remains a quarantine-only review candidate and is not approved for renderer asset folders or publishing.",
        "",
        "## Priority Rows",
        "",
    ]
    if plan_rows:
        for row in plan_rows:
            lines.append(
                "- "
                f"`{row['plan_id']}` `{row['priority']}` `{row['renderer_recheck_area']}` "
                f"from `{row['source_finding_id']}`: {row['planning_note']}"
            )
    else:
        lines.append("- None yet.")
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


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    manifest_path = input_path(Path(args.input_manifest) if args.input_manifest else IN_MANIFEST_REL)
    findings_path = input_path(Path(args.input_findings) if args.input_findings else IN_FINDINGS_REL)
    source_manifest = read_json(manifest_path)
    findings, fields = read_csv_rows(findings_path)

    source_issues = validate_source_manifest(source_manifest, manifest_path)
    finding_issues = validate_findings(findings, fields, findings_path)
    plan_rows = build_plan_rows(findings) if not source_issues and not finding_issues else []
    checks = checklist_rows(plan_rows) if plan_rows else []
    output_issues = [
        *validate_output_rows(plan_rows, PLAN_FIELDS, OUT_PLAN_REL.as_posix()),
        *validate_output_rows(checks, CHECKLIST_FIELDS, OUT_CHECKLIST_REL.as_posix()),
    ]
    issues = [*source_issues, *finding_issues, *output_issues]
    priority_counts = dict(sorted(Counter(row["priority"] for row in plan_rows).items()))
    area_counts = dict(sorted(Counter(row["renderer_recheck_area"] for row in plan_rows).items()))
    handoff_counts = source_manifest.get("renderer_handoff_recommendation_counts")
    if not isinstance(handoff_counts, dict):
        handoff_counts = dict(sorted(Counter(normalized(row.get("renderer_handoff_recommendation")) or "blank" for row in findings).items()))

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status_for(manifest_path, findings_path, issues, plan_rows),
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "candidate_queue_id": CANDIDATE_ID,
        "candidate_quarantine_path": CANDIDATE_QUARANTINE_PATH,
        "source_manifest": str(manifest_path),
        "source_findings_csv": str(findings_path),
        "source_manual_review_status": clean(source_manifest.get("status")),
        "source_finding_rows": len(findings),
        "source_renderer_handoff_recommendation_counts": handoff_counts,
        "pending_operator_fill_required_rows": int(handoff_counts.get("operator_fill_required", 0) or 0),
        "plan_rows": len(plan_rows),
        "checklist_rows": len(checks),
        "priority_counts": priority_counts,
        "renderer_recheck_area_counts": area_counts,
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "packet_dir": str(output_rel(OUT_PACKET_DIR_REL)),
        "plan_csv": str(output_rel(OUT_PLAN_REL)),
        "checklist_csv": str(output_rel(OUT_CHECKLIST_REL)),
        "handoff_md": str(output_rel(OUT_HANDOFF_REL)),
        "readme_md": str(output_rel(OUT_README_REL)),
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

    write_csv(output_rel(OUT_PLAN_REL), plan_rows, PLAN_FIELDS)
    write_csv(output_rel(OUT_CHECKLIST_REL), checks, CHECKLIST_FIELDS)
    write_json(output_rel(OUT_MANIFEST_REL), payload, sort_keys=True)
    write_text(output_rel(OUT_README_REL), render_readme(payload), normalize=strip_volatile_markdown_lines)
    write_text(output_rel(OUT_HANDOFF_REL), render_handoff(payload, plan_rows), normalize=strip_volatile_markdown_lines)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an APQ001 review-only renderer recheck planning packet.")
    parser.add_argument("--input-manifest", default="")
    parser.add_argument("--input-findings", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_packet(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "source_finding_rows": payload["source_finding_rows"],
                "plan_rows": payload["plan_rows"],
                "checklist_rows": payload["checklist_rows"],
                "validation_issue_count": payload["validation_issue_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["validation_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
