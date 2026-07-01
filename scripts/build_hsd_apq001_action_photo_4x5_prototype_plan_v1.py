from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-apq001-action-photo-4x5-prototype-plan-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apq001_action_photo_4x5_prototype_plan_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
IN_MANIFEST_REL = Path("apq001_manual_review_result_manifest.json")
IN_REPORT_REL = Path("apq001_manual_review_result_report.md")
IN_RECHECK_MANIFEST_REL = Path("apq001_renderer_recheck_packet/manifest.json")
IN_RECHECK_PLAN_REL = Path("apq001_renderer_recheck_packet/renderer_recheck_plan.csv")
IN_ADOBE_SPEC_REL = Path("adobe_visual_qa_renderer_revision_spec.csv")
IN_TASK_QUEUE_REL = Path("renderer_next_lane_brief/next_renderer_lane_task_queue.csv")
OPTIONAL_PREVIEW_REL = Path("render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png")
OUT_DIR_REL = Path("apq001_action_photo_4x5_prototype_plan")
OUT_MANIFEST_REL = OUT_DIR_REL / "manifest.json"
OUT_README_REL = OUT_DIR_REL / "README.md"
OUT_PLAN_REL = OUT_DIR_REL / "prototype_plan.csv"
OUT_CHECKLIST_REL = OUT_DIR_REL / "prototype_checklist.csv"
CANDIDATE_QUARANTINE_PATH = (
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
    "apq001_review_only_candidate.jpg"
)

PLAN_FIELDS = [
    "prototype_id",
    "source_recheck_plan_id",
    "source_spec_id",
    "source_queue_id",
    "prototype_mode",
    "handoff_status",
    "apq001_quarantine_image_path",
    "burn_in_label",
    "prototype_subject",
    "visual_qa_guidance",
    "focus_crop_constraints",
    "safe_zone_constraints",
    "score_rail_placement",
    "lower_stat_rail_treatment",
    "avoided_behaviors",
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
    "prototype_id",
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
    "renderer_behavior_change",
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def validate_source_manifest(manifest: Mapping[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return [{"source": IN_MANIFEST_REL.as_posix(), "field": "input", "issue": "manual_review_result_manifest_missing"}]
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


def validate_csv_rows(rows: list[Mapping[str, str]], fields: list[str], required: list[str], source: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not rows:
        issues.append({"source": source, "field": "rows", "issue": "source_csv_has_no_rows"})
        return issues
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
    return issues


def select_first(rows: list[Mapping[str, str]], *predicates: str) -> Mapping[str, str]:
    for row in rows:
        haystack = " ".join(clean(row.get(field)) for field in predicates).lower()
        if haystack.strip():
            return row
    return rows[0] if rows else {}


def source_preview_present() -> bool:
    return input_path(OPTIONAL_PREVIEW_REL).exists()


def build_plan_row(
    *,
    recheck_rows: list[Mapping[str, str]],
    spec_rows: list[Mapping[str, str]],
    queue_rows: list[Mapping[str, str]],
) -> dict[str, str]:
    recheck_row = recheck_rows[0] if recheck_rows else {}
    spec_row = select_first(spec_rows, "format", "renderer_area", "implementation_task", "revision_spec")
    queue_row = select_first(queue_rows, "source_packet", "renderer_area", "task_title", "task_summary")
    return {
        "prototype_id": "APQ4X5-001",
        "source_recheck_plan_id": csv_value(recheck_row.get("plan_id")),
        "source_spec_id": csv_value(spec_row.get("spec_id")),
        "source_queue_id": csv_value(queue_row.get("task_id")),
        "prototype_mode": "metadata_only_annotated_plan",
        "handoff_status": "quarantine_review_lock",
        "apq001_quarantine_image_path": CANDIDATE_QUARANTINE_PATH,
        "burn_in_label": "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER",
        "prototype_subject": "APQ001 action-photo-aware 4:5 composition prototype",
        "visual_qa_guidance": (
            "Treat the latest 4:5 render as review-only guidance: remove the roster-card box feel, "
            "debox the score rail into raw high-contrast typography, dissolve the lower stat slab into a lighter editorial strip, "
            "and prefer a dynamic action-photo crop or full-bleed treatment with a dark scrim for legibility."
        ),
        "focus_crop_constraints": (
            "Keep the athlete face, jersey, and primary motion cue inside a centered upper-mid crop band; "
            "do not trim the action anchor or force a portrait-only headshot read. If the quarantine asset lacks alpha, "
            "treat it as a rectangular review-only source and do not pretend it is a clean cutout."
        ),
        "safe_zone_constraints": (
            "Leave clean breathing room at the top for title/score-safe treatment, keep title/score zones clear of the athlete head line, "
            "and preserve room for a dark scrim or vignette rather than a hard panel."
        ),
        "score_rail_placement": (
            "Place the score rail in the open upper third with inset typography, no horizontal container lines, "
            "winner crisp white/gold, loser lower-opacity off-white."
        ),
        "lower_stat_rail_treatment": (
            "Keep the lower stat rail thin, legible, and partially transparent so it floats over the vignette; "
            "use lighter editorial type and middle dots instead of slashes."
        ),
        "avoided_behaviors": (
            "No image edits, downloads, approvals, .approved markers, publish-ready states, file movement, renderer cutover, "
            "or unguarded approval/publish wording in the prototype lane."
        ),
        "acceptance_check": (
            "A human can review the note as a 4:5 prototype without any asset movement, and the manifest stays locked to quarantine review."
        ),
        "verification_artifact": "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
        "next_manual_action": (
            "Use this review-only prototype note as the handoff for a later renderer lane via apq001_quarantine_image_path; "
            "do not turn it into production behavior."
        ),
        "candidate_quarantine_path": CANDIDATE_QUARANTINE_PATH,
        **guardrail_values(),
    }


def build_checklist_rows(plan_row: Mapping[str, str]) -> list[dict[str, str]]:
    checks = [
        (
            "focus_crop",
            "Does the crop keep the athlete and primary action cue inside the centered upper-mid focus band?",
            "yes",
        ),
        (
            "safe_zone",
            "Is the top safe zone clean enough for score/title treatment without crowding the athlete head line?",
            "yes",
        ),
        (
            "score_rail",
            "Does the score rail read as open typography in the upper third instead of a boxed dashboard panel?",
            "yes",
        ),
        (
            "lower_stat_rail",
            "Does the lower stat rail stay thin, readable, and editorial instead of heavy or enclosed?",
            "yes",
        ),
        (
            "guardrails",
            "Does the artifact stay review-only with no edits, downloads, approvals, marker files, file moves, or publishing?",
            "yes",
        ),
    ]
    rows: list[dict[str, str]] = []
    for index, (scope, question, expected) in enumerate(checks, start=1):
        rows.append(
            {
                "check_id": f"APQ4X5C{index:03d}",
                "prototype_id": csv_value(plan_row.get("prototype_id")),
                "question": question,
                "expected_answer": expected,
                "artifact_to_inspect": OUT_PLAN_REL.as_posix(),
                **guardrail_values(),
            }
        )
    return rows


def status_for(
    *,
    manifest_path: Path,
    report_path: Path,
    recheck_manifest_path: Path,
    recheck_plan_path: Path,
    spec_path: Path,
    queue_path: Path,
    issues: list[Mapping[str, str]],
    plan_rows: list[Mapping[str, str]],
) -> str:
    required_paths = [manifest_path, report_path, recheck_manifest_path, recheck_plan_path, spec_path, queue_path]
    if any(not path.exists() for path in required_paths):
        return "apq001_action_photo_4x5_prototype_plan_missing_inputs"
    if issues:
        return "apq001_action_photo_4x5_prototype_plan_has_validation_issues"
    if not plan_rows:
        return "apq001_action_photo_4x5_prototype_plan_waiting_for_source_rows"
    return "apq001_action_photo_4x5_prototype_plan_ready"


def render_readme(payload: Mapping[str, Any], plan_row: Mapping[str, str]) -> str:
    row = {
        "prototype_id": "",
        "source_recheck_plan_id": "",
        "source_spec_id": "",
        "source_queue_id": "",
        "prototype_mode": "",
        "handoff_status": "",
        "apq001_quarantine_image_path": CANDIDATE_QUARANTINE_PATH,
        "burn_in_label": "",
        "prototype_subject": "",
        "visual_qa_guidance": "",
        "focus_crop_constraints": "",
        "safe_zone_constraints": "",
        "score_rail_placement": "",
        "lower_stat_rail_treatment": "",
        "avoided_behaviors": "",
        "acceptance_check": "",
        "verification_artifact": "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
        "next_manual_action": "",
        "candidate_quarantine_path": CANDIDATE_QUARANTINE_PATH,
    }
    row.update(plan_row)
    return f"""# APQ001 Action Photo 4x5 Prototype Plan

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This artifact is review-only and metadata-only. It turns the APQ001 manual review result, APQ001 recheck plan, Adobe visual QA renderer revision spec, and next-lane task queue into a small 4:5 composition prototype note. Do not edit the quarantine candidate, do not download anything, do not create `.approved` markers, do not move files, do not mark publish-ready, do not publish, and do not change renderer behavior.

## Prototype

- Prototype ID: `{row['prototype_id'] or 'missing'}`
- Mode: `{row['prototype_mode'] or 'missing'}`
- Handoff status: `{row['handoff_status'] or 'missing'}`
- Source recheck plan row: `{row['source_recheck_plan_id'] or 'missing'}`
- Source Adobe spec row: `{row['source_spec_id'] or 'missing'}`
- Source task queue row: `{row['source_queue_id'] or 'missing'}`
- Quarantine candidate: `{row['candidate_quarantine_path']}`
- `apq001_quarantine_image_path`: `{row['apq001_quarantine_image_path']}`
- Burn-in label: `{row['burn_in_label'] or 'missing'}`
- Preview reference: `{row['verification_artifact']}`
- Preview present: `{payload['preview_reference_present']}`

## Counts

- Manual review manifest: `{payload['manual_review_manifest_status']}`
- Manual review report present: `{payload['manual_review_report_present']}`
- APQ001 recheck plan rows: `{payload['recheck_plan_rows']}`
- Adobe spec rows: `{payload['adobe_spec_rows']}`
- Next-lane queue rows: `{payload['task_queue_rows']}`
- Prototype plan rows: `{payload['prototype_plan_rows']}`
- Checklist rows: `{payload['checklist_rows']}`
- Validation issues: `{payload['validation_issue_count']}`

## Composition Notes

- Visual QA guidance: {row['visual_qa_guidance'] or 'missing'}
- Focus/crop: {row['focus_crop_constraints'] or 'missing'}
- Safe zone: {row['safe_zone_constraints'] or 'missing'}
- Score rail: {row['score_rail_placement'] or 'missing'}
- Lower stat rail: {row['lower_stat_rail_treatment'] or 'missing'}
- Avoided behaviors: {row['avoided_behaviors'] or 'missing'}
- Acceptance check: {row['acceptance_check'] or 'missing'}

## Guardrails

- No .approved markers.
- review_only=true
- artifact_only=true
- image_edits=false
- new_downloads=false
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- headshot_writes=false
- renderer_behavior_change=false
- publish_ready=false
- publishing=false
- move_files=false

## Next Step

Keep this as a handoff for a later explicit renderer lane. Do not treat it as approval or a production cutover.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    manifest_path = input_path(Path(args.manifest) if args.manifest else IN_MANIFEST_REL)
    report_path = input_path(Path(args.report) if args.report else IN_REPORT_REL)
    recheck_manifest_path = input_path(Path(args.recheck_manifest) if args.recheck_manifest else IN_RECHECK_MANIFEST_REL)
    recheck_plan_path = input_path(Path(args.recheck_plan) if args.recheck_plan else IN_RECHECK_PLAN_REL)
    spec_path = input_path(Path(args.adobe_spec) if args.adobe_spec else IN_ADOBE_SPEC_REL)
    queue_path = input_path(Path(args.task_queue) if args.task_queue else IN_TASK_QUEUE_REL)

    manual_manifest = read_json(manifest_path)
    report_text = read_text(report_path)
    recheck_manifest = read_json(recheck_manifest_path)
    recheck_rows, recheck_fields = read_csv_rows(recheck_plan_path)
    spec_rows, spec_fields = read_csv_rows(spec_path)
    queue_rows, queue_fields = read_csv_rows(queue_path)

    issues = [
        *validate_source_manifest(manual_manifest, manifest_path),
        *validate_csv_rows(
            recheck_rows,
            recheck_fields,
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
            IN_RECHECK_PLAN_REL.as_posix(),
        ),
        *validate_csv_rows(
            spec_rows,
            spec_fields,
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
            IN_ADOBE_SPEC_REL.as_posix(),
        ),
        *validate_csv_rows(
            queue_rows,
            queue_fields,
            [
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
            ],
            IN_TASK_QUEUE_REL.as_posix(),
        ),
    ]

    plan_row = build_plan_row(recheck_rows=recheck_rows, spec_rows=spec_rows, queue_rows=queue_rows) if not issues else {}
    plan_rows = [plan_row] if plan_row else []
    checklist_rows = build_checklist_rows(plan_row) if plan_row else []
    queue_source_counts = dict(sorted(Counter(row.get("source_packet", "") or "blank" for row in queue_rows).items()))
    prototype_counts = dict(sorted(Counter(row.get("prototype_mode", "") or "blank" for row in plan_rows).items()))

    status = status_for(
        manifest_path=manifest_path,
        report_path=report_path,
        recheck_manifest_path=recheck_manifest_path,
        recheck_plan_path=recheck_plan_path,
        spec_path=spec_path,
        queue_path=queue_path,
        issues=issues,
        plan_rows=plan_rows,
    )

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "manual_review_manifest": str(manifest_path),
        "manual_review_manifest_status": clean(manual_manifest.get("status")),
        "manual_review_report": str(report_path),
        "manual_review_report_present": bool(report_text.strip()),
        "recheck_manifest": str(recheck_manifest_path),
        "recheck_manifest_status": clean(recheck_manifest.get("status")),
        "recheck_plan_csv": str(recheck_plan_path),
        "recheck_plan_rows": len(recheck_rows),
        "adobe_spec_csv": str(spec_path),
        "adobe_spec_rows": len(spec_rows),
        "task_queue_csv": str(queue_path),
        "task_queue_rows": len(queue_rows),
        "preview_reference_path": OPTIONAL_PREVIEW_REL.as_posix(),
        "preview_reference_present": source_preview_present(),
        "prototype_plan_rows": len(plan_rows),
        "checklist_rows": len(checklist_rows),
        "handoff_status": "quarantine_review_lock",
        "auto_publish": False,
        "apq001_quarantine_image_path": CANDIDATE_QUARANTINE_PATH,
        "burn_in_label": "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER",
        "queue_source_counts": queue_source_counts,
        "prototype_mode_counts": prototype_counts,
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "prototype_plan_csv": str(output_rel(OUT_PLAN_REL)),
        "prototype_checklist_csv": str(output_rel(OUT_CHECKLIST_REL)),
        "readme_md": str(output_rel(OUT_README_REL)),
        "review_only": True,
        "artifact_only": True,
        "image_edits": False,
        "new_downloads": False,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "headshot_writes": False,
        "renderer_behavior_change": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
    }

    write_csv(output_rel(OUT_PLAN_REL), plan_rows, PLAN_FIELDS)
    write_csv(output_rel(OUT_CHECKLIST_REL), checklist_rows, CHECKLIST_FIELDS)
    write_json(output_rel(OUT_MANIFEST_REL), payload, sort_keys=True)
    write_text(output_rel(OUT_README_REL), render_readme(payload, plan_row), normalize=strip_volatile_markdown_lines)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an APQ001 review-only 4:5 action-photo prototype plan.")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--report", default="")
    parser.add_argument("--recheck-manifest", default="")
    parser.add_argument("--recheck-plan", default="")
    parser.add_argument("--adobe-spec", default="")
    parser.add_argument("--task-queue", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "recheck_plan_rows": payload["recheck_plan_rows"],
                "adobe_spec_rows": payload["adobe_spec_rows"],
                "task_queue_rows": payload["task_queue_rows"],
                "prototype_plan_rows": payload["prototype_plan_rows"],
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
