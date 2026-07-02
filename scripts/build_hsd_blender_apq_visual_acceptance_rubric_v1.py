from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-blender-apq-visual-acceptance-rubric-v1-review-only"
GENERATED_BY = "scripts/build_hsd_blender_apq_visual_acceptance_rubric_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("blender_apq_visual_acceptance_rubric")

BEFORE_AFTER_ROOT = LATEST_FILES_ROOT / "blender_apq_before_after_decision_packet"
CURRENT_VARIANTS_ROOT = LATEST_FILES_ROOT / "blender_apq_composition_variants"
BEFORE_AFTER_FALLBACK_ROOTS = [Path("outputs/local/tmp/blender_apq_before_after_decision_packet_v1")]
CURRENT_VARIANTS_FALLBACK_ROOTS = [Path("outputs/local/tmp/blender_apq_clean_editorial_crop_v10")]

REPORT_NAME = "visual_acceptance_rubric.md"
CSV_NAME = "visual_acceptance_rubric.csv"
README_NAME = "README.md"
MANIFEST_NAME = "manifest.json"

DECISION_CATEGORIES = [
    {
        "category_id": "accept_baseline",
        "title": "Accept baseline",
        "when_to_use": "The clean editorial baseline is the best available review-only direction and the face-safe limitation is an accepted tradeoff.",
    },
    {
        "category_id": "revise_only_if_better_review_only_crop_exists",
        "title": "Revise only if a better review-only crop exists",
        "when_to_use": "The baseline is close, but a better quarantine-scoped crop could fix the hard blocker without new assets or approvals.",
    },
    {
        "category_id": "pause_for_manual_qa",
        "title": "Pause for manual QA",
        "when_to_use": "The current source candidate still fails the hard blocker and any further change would be blind polishing.",
    },
    {
        "category_id": "continue_limited_polish_only_if_fixable_without_new_assets",
        "title": "Continue limited polish only if fixable without new assets",
        "when_to_use": "A concrete failing criterion can be fixed with the current review-only assets and without changing renderer behavior.",
    },
]

HARD_BLOCKERS = [
    {
        "criterion_id": "HB01",
        "title": "Face fully in frame",
        "description": "The athlete face should be fully within frame; no severe decapitation or hard edge slicing.",
        "current_state": "fail",
        "evidence_key": "subject_face_within_frame_intent",
    },
    {
        "criterion_id": "HB02",
        "title": "No text over jersey or high-texture body area",
        "description": "Typography should stay off the jersey and away from high-contrast body texture whenever possible.",
        "current_state": "review_required",
        "evidence_key": "text_kept_off_face",
    },
    {
        "criterion_id": "HB03",
        "title": "Burn-in stays controlled",
        "description": "The review-only burn-in must remain visible, inside canvas, and off the primary body/jersey as much as feasible.",
        "current_state": "pass",
        "evidence_key": "burn_in_off_primary_body",
    },
    {
        "criterion_id": "HB04",
        "title": "No gimmicky type effects",
        "description": "Avoid decorative or debug-style treatments such as the line-through FINAL effect from score_drama.",
        "current_state": "review_required",
        "evidence_key": "typography_hierarchy_improved",
    },
    {
        "criterion_id": "HB05",
        "title": "Review-only guardrails stay locked",
        "description": "The packet remains review-only / APQ001 quarantine-only / not approved / not publish-ready.",
        "current_state": "pass",
        "evidence_key": "guardrails_locked_false",
    },
]

ADVISORY_CRITERIA = [
    {
        "criterion_id": "AD01",
        "title": "Dark controlled text plane or sufficient contrast",
        "description": "Use a controlled dark plane or scrim so readable text does not fight the photo.",
        "current_state": "pass",
        "evidence_key": "score_panel_softened",
    },
    {
        "criterion_id": "AD02",
        "title": "Clean minimalist font scaling",
        "description": "Keep typography sizing consistent and calm rather than stencil-like or oversized.",
        "current_state": "pass",
        "evidence_key": "minimalist_font_scaling_standardized",
    },
    {
        "criterion_id": "AD03",
        "title": "APQ001 review wording remains visible and accurate",
        "description": "The packet must keep sober review-only language and the quarantine-only label intact.",
        "current_state": "pass",
        "evidence_key": "review_only_wording_present",
    },
]

MANUAL_INTAKE_FIELDS = [
    "reviewer_decision",
    "reviewer_notes",
    "blocked_by_source_candidate_limitations",
    "future_lane_recommendation",
]

CSV_FIELDS = [
    "row_kind",
    "row_id",
    "section",
    "title",
    "criterion_type",
    "severity",
    "decision_category",
    "when_to_use",
    "description",
    "current_state",
    "evidence_key",
    "evidence_path",
    "source_exists",
    "reviewer_decision",
    "reviewer_notes",
    "blocked_by_source_candidate_limitations",
    "future_lane_recommendation",
    "review_only",
    "apq001_quarantine_only",
    "not_approved",
    "not_publish_ready",
    "asset_downloads",
    "download_performed",
    "source_auto_enabled",
    "approval_state_change",
    "asset_approved",
    "move_files",
    "protected_asset_moves",
    "renderer_behavior_change",
    "production_renderer_replacement",
    "publish_ready",
    "publishing",
    "auto_publish",
    "auto_approval",
]

BASE_FLAGS = {
    "review_only": True,
    "apq001_quarantine_only": True,
    "not_approved": True,
    "not_publish_ready": True,
    "asset_downloads": False,
    "download_performed": False,
    "source_auto_enabled": False,
    "approval_state_change": False,
    "asset_approved": False,
    "move_files": False,
    "protected_asset_moves": False,
    "renderer_behavior_change": False,
    "production_renderer_replacement": False,
    "publish_ready": False,
    "publishing": False,
    "auto_publish": False,
    "auto_approval": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def packet_root() -> Path:
    root = run_output_dir()
    if root:
        return root
    return repo_root() / LATEST_FILES_ROOT / OUT_DIR_REL


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def locate_surface_file(surface_root: Path, filename: str, fallbacks: Iterable[Path]) -> Path:
    candidates = [repo_root() / surface_root / filename]
    for fallback_root in fallbacks:
        candidates.append(repo_root() / fallback_root / filename)
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def extract_variant_row(manifest: dict[str, Any], variant_id: str) -> dict[str, Any]:
    for row in manifest.get("variant_rows", []) or []:
        if clean(row.get("variant_id")) == variant_id:
            return dict(row)
    return {}


def current_truth(manifest: dict[str, Any]) -> dict[str, Any]:
    row = extract_variant_row(manifest, "variant_03_clean_editorial")
    checks = dict(row.get("layout_polish_checks", {}) or {})
    return {
        "baseline_variant_id": "variant_03_clean_editorial",
        "baseline_variant_title": "variant_03_clean_editorial",
        "baseline_variant_is_strongest": True,
        "baseline_variant_lead_direction": clean(row.get("lead_direction")) or "clean_editorial",
        "baseline_subject_face_within_frame_intent": truthy(row.get("subject_face_within_frame_intent")),
        "baseline_face_edge_clipping_reduced": truthy(checks.get("face_edge_clipping_reduced")),
        "baseline_top_spotlight_softened": truthy(row.get("top_spotlight_softened")),
        "baseline_minimalist_font_scaling_standardized": truthy(row.get("minimalist_font_scaling_standardized")),
        "baseline_review_only_derived_crop": truthy(row.get("review_only_derived_crop")),
        "baseline_source_photo_crop_mode": clean(row.get("source_photo_crop_mode")),
        "baseline_score_typography_treatment": clean(row.get("score_typography_treatment")),
        "baseline_layout_polish_checks": checks,
        "baseline_layout_truth_summary": (
            "variant_03_clean_editorial is the strongest baseline, but the current review-only source candidate still fails face-safe framing."
        ),
    }


def source_artifacts_list(paths: list[Path]) -> list[dict[str, Any]]:
    meta = [
        ("SRC001", "before_after_surface", "Before/after decision packet report", "Review the post-v10 before/after summary."),
        ("SRC002", "before_after_surface", "Before/after decision packet manifest", "Confirms the review-only state of the before/after packet."),
        ("SRC003", "before_after_surface", "Before/after decision packet intake CSV", "Contains the manual questions that led to the current decision surface."),
        ("SRC101", "current_surface", "Current composition variants contact sheet", "Shows the current post-v10 variants together at a glance."),
        ("SRC102", "current_surface", "Current variant_01_photo_anchor image", "Comparison surface only; not the lead baseline."),
        ("SRC103", "current_surface", "Current variant_02_score_drama image", "Comparison surface only; useful for spotting risky type treatments."),
        ("SRC104", "current_surface", "Current variant_03_clean_editorial image", "The strongest baseline candidate, but still face-safe limited."),
        ("SRC105", "current_surface", "Current composition variants manifest", "Provides the truth state for the post-v10 visual acceptance rubric."),
    ]
    artifacts: list[dict[str, Any]] = []
    for (row_id, section, title, description), path in zip(meta, paths):
        artifacts.append(
            {
                "row_id": row_id,
                "section": section,
                "title": title,
                "path": path,
                "source_exists": path.exists(),
                "description": description,
            }
        )
    return artifacts


def build_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in payload["source_artifacts"]:
        rows.append(
            {
                "row_kind": "source_artifact",
                "row_id": artifact["row_id"],
                "section": artifact["section"],
                "title": artifact["title"],
                "criterion_type": "source",
                "severity": "info",
                "decision_category": "",
                "when_to_use": "",
                "description": artifact["description"],
                "current_state": "present" if artifact["source_exists"] else "missing",
                "evidence_key": "source_path",
                "evidence_path": artifact["path"].as_posix(),
                "source_exists": artifact["source_exists"],
                "reviewer_decision": "",
                "reviewer_notes": "",
                "blocked_by_source_candidate_limitations": "",
                "future_lane_recommendation": "",
                **BASE_FLAGS,
            }
        )
    for item in DECISION_CATEGORIES:
        rows.append(
            {
                "row_kind": "decision_category",
                "row_id": item["category_id"],
                "section": "decision_matrix",
                "title": item["title"],
                "criterion_type": "decision",
                "severity": "policy",
                "decision_category": item["category_id"],
                "when_to_use": item["when_to_use"],
                "description": item["when_to_use"],
                "current_state": "available",
                "evidence_key": "decision_category",
                "evidence_path": "",
                "source_exists": True,
                "reviewer_decision": "",
                "reviewer_notes": "",
                "blocked_by_source_candidate_limitations": "",
                "future_lane_recommendation": "",
                **BASE_FLAGS,
            }
        )
    for item in HARD_BLOCKERS:
        rows.append(
            {
                "row_kind": "criterion",
                "row_id": item["criterion_id"],
                "section": "hard_blockers",
                "title": item["title"],
                "criterion_type": "hard_blocker",
                "severity": "hard",
                "decision_category": "",
                "when_to_use": "",
                "description": item["description"],
                "current_state": item["current_state"],
                "evidence_key": item["evidence_key"],
                "evidence_path": payload["current_manifest_path"],
                "source_exists": True,
                "reviewer_decision": "",
                "reviewer_notes": "",
                "blocked_by_source_candidate_limitations": "",
                "future_lane_recommendation": "",
                **BASE_FLAGS,
            }
        )
    for item in ADVISORY_CRITERIA:
        rows.append(
            {
                "row_kind": "criterion",
                "row_id": item["criterion_id"],
                "section": "advisory_criteria",
                "title": item["title"],
                "criterion_type": "advisory",
                "severity": "advisory",
                "decision_category": "",
                "when_to_use": "",
                "description": item["description"],
                "current_state": item["current_state"],
                "evidence_key": item["evidence_key"],
                "evidence_path": payload["current_manifest_path"],
                "source_exists": True,
                "reviewer_decision": "",
                "reviewer_notes": "",
                "blocked_by_source_candidate_limitations": "",
                "future_lane_recommendation": "",
                **BASE_FLAGS,
            }
        )
    rows.append(
        {
            "row_kind": "manual_intake_template",
            "row_id": "INTAKE001",
            "section": "manual_intake",
            "title": "Reviewer decision intake",
            "criterion_type": "manual_intake",
            "severity": "policy",
            "decision_category": "",
            "when_to_use": "",
            "description": "Fill this in to capture the acceptance decision without implying approval or publishing.",
            "current_state": "blank",
            "evidence_key": "manual_intake_fields",
            "evidence_path": "",
            "source_exists": True,
            "reviewer_decision": "",
            "reviewer_notes": "",
            "blocked_by_source_candidate_limitations": "",
            "future_lane_recommendation": "",
            **BASE_FLAGS,
        }
    )
    return rows


def render_report(payload: dict[str, Any]) -> str:
    source_lines = [
        f"- `{artifact['title']}` -> `{artifact['path'].as_posix()}` ({'present' if artifact['source_exists'] else 'missing'})"
        for artifact in payload["source_artifacts"]
    ]
    decision_lines = [
        f"- `{item['category_id']}`: {item['title']} - {item['when_to_use']}"
        for item in DECISION_CATEGORIES
    ]
    hard_lines = [
        f"- `{item['criterion_id']}` {item['title']} - {item['description']} Current state: `{item['current_state']}`."
        for item in HARD_BLOCKERS
    ]
    advisory_lines = [
        f"- `{item['criterion_id']}` {item['title']} - {item['description']} Current state: `{item['current_state']}`."
        for item in ADVISORY_CRITERIA
    ]
    current = payload["current_truth"]
    manual_questions = [
        "- Should we accept `variant_03_clean_editorial` as the baseline despite the face-safe limitation?",
        "- Should we revise only if a better review-only crop exists, or pause for manual QA because the source candidate is too tight?",
        "- Should future lanes continue limited polish only when a concrete failing criterion is fixable without new assets?",
    ]
    return f"""# APQ001 Visual Acceptance Rubric

Status: `blender_apq_visual_acceptance_rubric_ready` if all required inputs are present, otherwise `blender_apq_visual_acceptance_rubric_missing_sources`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This is a review-only artifact. It is APQ001 quarantine-only, not approved, and not publish-ready.

## Source Surfaces

{chr(10).join(source_lines)}

## Top-Level Decision Categories

{chr(10).join(decision_lines)}

## Hard Blockers

{chr(10).join(hard_lines)}

## Advisory Criteria

{chr(10).join(advisory_lines)}

## Current Truth Snapshot

- Strongest baseline candidate: `variant_03_clean_editorial`
- variant_03_clean_editorial is the strongest baseline.
- Baseline lead direction: `{current['baseline_variant_lead_direction']}`
- Face-safe framing intent: `{str(current['baseline_subject_face_within_frame_intent']).lower()}`
- Face edge clipping reduced: `{str(current['baseline_face_edge_clipping_reduced']).lower()}`
- Review-only derived crop used: `{str(current['baseline_review_only_derived_crop']).lower()}`
- Source photo crop mode: `{current['baseline_source_photo_crop_mode']}`
- Score typography treatment: `{current['baseline_score_typography_treatment']}`

`variant_03_clean_editorial` is the strongest baseline, but the current review-only source candidate still fails the face-safe criterion.

## Manual Review Questions

{chr(10).join(manual_questions)}

## Manual Intake Fields

- `reviewer_decision`
- `reviewer_notes`
- `blocked_by_source_candidate_limitations`
- `future_lane_recommendation`

## Guardrails

- review_only={str(payload['review_only']).lower()}
- apq001_quarantine_only={str(payload['apq001_quarantine_only']).lower()}
- not_approved={str(payload['not_approved']).lower()}
- not_publish_ready={str(payload['not_publish_ready']).lower()}
- asset_downloads={str(payload['asset_downloads']).lower()}
- download_performed={str(payload['download_performed']).lower()}
- source_auto_enabled={str(payload['source_auto_enabled']).lower()}
- approval_state_change={str(payload['approval_state_change']).lower()}
- asset_approved={str(payload['asset_approved']).lower()}
- move_files={str(payload['move_files']).lower()}
- protected_asset_moves={str(payload['protected_asset_moves']).lower()}
- renderer_behavior_change={str(payload['renderer_behavior_change']).lower()}
- production_renderer_replacement={str(payload['production_renderer_replacement']).lower()}
- publish_ready={str(payload['publish_ready']).lower()}
- publishing={str(payload['publishing']).lower()}
- auto_publish={str(payload['auto_publish']).lower()}
- auto_approval={str(payload['auto_approval']).lower()}
"""


def render_readme(payload: dict[str, Any]) -> str:
    return f"""# Visual Acceptance Rubric

Open `visual_acceptance_rubric.md` first, then use `visual_acceptance_rubric.csv` to capture the reviewer decision.

This packet is review-only, APQ001 quarantine-only, not approved, and not publish-ready.

Source truth: `variant_03_clean_editorial` remains the strongest baseline, but the current review-only source candidate still fails the face-safe criterion.
variant_03_clean_editorial is the strongest baseline, but the current review-only source candidate still fails the face-safe criterion.

Manual decision categories:
- `accept_baseline`
- `revise_only_if_better_review_only_crop_exists`
- `pause_for_manual_qa`
- `continue_limited_polish_only_if_fixable_without_new_assets`

Top-level manual questions:
- Should we accept `variant_03_clean_editorial` as the baseline despite the face-safe limitation?
- Should we revise only if a better review-only crop exists, or pause for manual QA because the source candidate is too tight?
- Should future lanes continue limited polish only when a concrete failing criterion is fixable without new assets?

Manual intake fields:
- `reviewer_decision`
- `reviewer_notes`
- `blocked_by_source_candidate_limitations`
- `future_lane_recommendation`

Generated from `{payload['before_after_manifest_path']}` and `{payload['current_manifest_path']}`.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    before_after_manifest_path = locate_surface_file(BEFORE_AFTER_ROOT, "manifest.json", BEFORE_AFTER_FALLBACK_ROOTS)
    before_after_report_path = locate_surface_file(BEFORE_AFTER_ROOT, "visual_qa_report.md", BEFORE_AFTER_FALLBACK_ROOTS)
    before_after_csv_path = locate_surface_file(BEFORE_AFTER_ROOT, "manual_visual_review_intake.csv", BEFORE_AFTER_FALLBACK_ROOTS)
    current_manifest_path = locate_surface_file(CURRENT_VARIANTS_ROOT, "manifest.json", CURRENT_VARIANTS_FALLBACK_ROOTS)
    current_contact_sheet_path = locate_surface_file(CURRENT_VARIANTS_ROOT, "contact_sheet.png", CURRENT_VARIANTS_FALLBACK_ROOTS)
    current_variant_01_path = locate_surface_file(CURRENT_VARIANTS_ROOT, "variant_01_photo_anchor.png", CURRENT_VARIANTS_FALLBACK_ROOTS)
    current_variant_02_path = locate_surface_file(CURRENT_VARIANTS_ROOT, "variant_02_score_drama.png", CURRENT_VARIANTS_FALLBACK_ROOTS)
    current_variant_03_path = locate_surface_file(CURRENT_VARIANTS_ROOT, "variant_03_clean_editorial.png", CURRENT_VARIANTS_FALLBACK_ROOTS)

    paths = [
        before_after_report_path,
        before_after_manifest_path,
        before_after_csv_path,
        current_contact_sheet_path,
        current_variant_01_path,
        current_variant_02_path,
        current_variant_03_path,
        current_manifest_path,
    ]
    source_artifacts = source_artifacts_list(paths)
    current_manifest = read_json(current_manifest_path)
    before_after_manifest = read_json(before_after_manifest_path)
    truth = current_truth(current_manifest)

    missing_required_source_paths = [path.as_posix() for path in paths if not path.exists()]
    status = "blender_apq_visual_acceptance_rubric_ready" if not missing_required_source_paths else "blender_apq_visual_acceptance_rubric_missing_sources"

    packet_dir = packet_root()
    packet_dir.mkdir(parents=True, exist_ok=True)
    report_path = packet_dir / REPORT_NAME
    csv_path = packet_dir / CSV_NAME
    readme_path = packet_dir / README_NAME
    manifest_path = packet_dir / MANIFEST_NAME

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_at_utc": now_iso(),
        "generated_by": GENERATED_BY,
        "repo_head": clean(args.head_commit),
        "packet_dir": packet_dir.as_posix(),
        "report_path": report_path.as_posix(),
        "csv_path": csv_path.as_posix(),
        "readme_path": readme_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "before_after_manifest_path": before_after_manifest_path.as_posix(),
        "before_after_report_path": before_after_report_path.as_posix(),
        "before_after_csv_path": before_after_csv_path.as_posix(),
        "current_manifest_path": current_manifest_path.as_posix(),
        "current_contact_sheet_path": current_contact_sheet_path.as_posix(),
        "current_variant_01_path": current_variant_01_path.as_posix(),
        "current_variant_02_path": current_variant_02_path.as_posix(),
        "current_variant_03_path": current_variant_03_path.as_posix(),
        "missing_required_source_paths": missing_required_source_paths,
        "source_artifacts": source_artifacts,
        "decision_categories": DECISION_CATEGORIES,
        "hard_blockers": HARD_BLOCKERS,
        "advisory_criteria": ADVISORY_CRITERIA,
        "manual_intake_fields": MANUAL_INTAKE_FIELDS,
        "current_truth": truth,
        "current_before_after_packet_status": clean(before_after_manifest.get("status")),
        "current_before_after_packet_present": before_after_manifest_path.exists(),
        "current_surface_status": clean(current_manifest.get("status")),
        "current_surface_present": current_manifest_path.exists(),
        "review_only": True,
        "apq001_quarantine_only": True,
        **BASE_FLAGS,
        "source_surface_truth_summary": "variant_03_clean_editorial is the strongest baseline, but the current review-only source candidate still fails the face-safe criterion.",
    }

    rows = build_rows(payload)
    write_text(report_path, render_report(payload), normalize=strip_volatile_markdown_lines)
    write_text(readme_path, render_readme(payload), normalize=strip_volatile_markdown_lines)
    write_csv(csv_path, rows, CSV_FIELDS, extrasaction="ignore")
    manifest_payload = dict(payload)
    manifest_payload["source_artifacts"] = [
        {
            "row_id": artifact["row_id"],
            "section": artifact["section"],
            "title": artifact["title"],
            "path": artifact["path"].as_posix(),
            "source_exists": artifact["source_exists"],
            "description": artifact["description"],
        }
        for artifact in source_artifacts
    ]
    write_json(manifest_path, manifest_payload, sort_keys=True)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only APQ visual acceptance rubric.")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "packet_dir": payload["packet_dir"],
                "review_only": True,
                "apq001_quarantine_only": True,
                "not_approved": True,
                "not_publish_ready": True,
                "asset_downloads": False,
                "download_performed": False,
                "source_auto_enabled": False,
                "approval_state_change": False,
                "asset_approved": False,
                "move_files": False,
                "protected_asset_moves": False,
                "renderer_behavior_change": False,
                "production_renderer_replacement": False,
                "publish_ready": False,
                "publishing": False,
                "auto_publish": False,
                "auto_approval": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
