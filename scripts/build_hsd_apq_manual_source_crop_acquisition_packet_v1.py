from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-apq-manual-source-crop-acquisition-packet-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apq_manual_source_crop_acquisition_packet_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("apq_manual_source_crop_acquisition")

PACKET_NAME = "manual_source_crop_acquisition_packet.md"
CSV_NAME = "manual_source_crop_acquisition_intake.csv"
README_NAME = "README.md"
MANIFEST_NAME = "manifest.json"

EVIDENCE_TARGETS = [
    {
        "row_id": "EVID001",
        "label": "Before/after decision packet report",
        "target_path": LATEST_FILES_ROOT / "blender_apq_before_after_decision_packet" / "visual_qa_report.md",
        "fallbacks": [
            Path("outputs/local/tmp/blender_apq_before_after_decision_packet_v1/visual_qa_report.md"),
        ],
        "why": "Captures the post-v10 accept/revise/pause decision context.",
    },
    {
        "row_id": "EVID002",
        "label": "Visual acceptance rubric",
        "target_path": LATEST_FILES_ROOT / "blender_apq_visual_acceptance_rubric" / "visual_acceptance_rubric.md",
        "fallbacks": [
            Path("outputs/local/tmp/blender_apq_visual_acceptance_rubric_v1/visual_acceptance_rubric.md"),
        ],
        "why": "States the hard blocker and the decision matrix for next steps.",
    },
    {
        "row_id": "EVID003",
        "label": "variant_03_clean_editorial",
        "target_path": LATEST_FILES_ROOT / "blender_apq_composition_variants" / "variant_03_clean_editorial.png",
        "fallbacks": [
            Path("outputs/local/tmp/blender_apq_clean_editorial_crop_v10/variant_03_clean_editorial.png"),
        ],
        "why": "Best current baseline, but still not face-safe with the current source candidate.",
    },
    {
        "row_id": "EVID004",
        "label": "Current composition contact sheet",
        "target_path": LATEST_FILES_ROOT / "blender_apq_composition_variants" / "contact_sheet.png",
        "fallbacks": [
            Path("outputs/local/tmp/blender_apq_clean_editorial_crop_v10/contact_sheet.png"),
        ],
        "why": "Shows the full current composition surface at a glance.",
    },
]

MANUAL_INTAKE_FIELDS = [
    "source_url",
    "source_type",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "face_fully_in_frame_expected",
    "wider_frame_available",
    "download_approved",
    "manual_reviewer_notes",
    "reject_reason",
]

CSV_FIELDS = [
    "row_kind",
    "row_id",
    "source_url",
    "source_type",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "face_fully_in_frame_expected",
    "wider_frame_available",
    "download_approved",
    "manual_reviewer_notes",
    "reject_reason",
    "future_lane_recommendation",
    "evidence_target_path",
    "evidence_resolved_path",
    "evidence_present",
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
    "publish_ready",
    "publishing",
    "auto_publish",
    "auto_approval",
]


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


def resolve_evidence(item: dict[str, Any]) -> dict[str, Any]:
    candidates = [repo_root() / item["target_path"]]
    candidates.extend(repo_root() / fallback for fallback in item["fallbacks"])
    resolved = next((candidate.resolve() for candidate in candidates if candidate.exists() and candidate.is_file()), candidates[0].resolve())
    return {
        "row_id": item["row_id"],
        "label": item["label"],
        "target_path": item["target_path"].as_posix(),
        "resolved_path": resolved.as_posix(),
        "present": resolved.exists(),
        "why": item["why"],
    }


def load_current_truth() -> dict[str, Any]:
    manifest_path = repo_root() / LATEST_FILES_ROOT / "blender_apq_composition_variants" / "manifest.json"
    fallback = repo_root() / Path("outputs/local/tmp/blender_apq_clean_editorial_crop_v10/manifest.json")
    for candidate in [manifest_path, fallback]:
        if candidate.exists():
            try:
                manifest = json.loads(candidate.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            for row in manifest.get("variant_rows", []) or []:
                if clean(row.get("variant_id")) == "variant_03_clean_editorial":
                    checks = dict(row.get("layout_polish_checks", {}) or {})
                    return {
                        "baseline_variant_id": "variant_03_clean_editorial",
                        "baseline_variant_is_strongest": True,
                        "baseline_subject_face_within_frame_intent": truthy(row.get("subject_face_within_frame_intent")),
                        "baseline_face_edge_clipping_reduced": truthy(checks.get("face_edge_clipping_reduced")),
                        "baseline_top_spotlight_softened": truthy(row.get("top_spotlight_softened")),
                        "baseline_minimalist_font_scaling_standardized": truthy(row.get("minimalist_font_scaling_standardized")),
                        "baseline_review_only_derived_crop": truthy(row.get("review_only_derived_crop")),
                        "baseline_source_photo_crop_mode": clean(row.get("source_photo_crop_mode")),
                        "baseline_source_photo_focus_region": row.get("source_photo_focus_region", {}),
                        "baseline_score_typography_treatment": clean(row.get("score_typography_treatment")),
                    }
    return {
        "baseline_variant_id": "variant_03_clean_editorial",
        "baseline_variant_is_strongest": True,
        "baseline_subject_face_within_frame_intent": False,
        "baseline_face_edge_clipping_reduced": False,
        "baseline_top_spotlight_softened": False,
        "baseline_minimalist_font_scaling_standardized": False,
        "baseline_review_only_derived_crop": False,
        "baseline_source_photo_crop_mode": "",
        "baseline_source_photo_focus_region": {},
        "baseline_score_typography_treatment": "",
    }


def packet_dir() -> Path:
    return packet_root()


def render_report(payload: dict[str, Any]) -> str:
    evidence_lines = [
        f"- `{item['label']}`"
        f" -> target `{item['target_path']}`"
        f" ({'present' if item['present'] else 'missing'} at `{item['resolved_path']}`)"
        for item in payload["evidence_items"]
    ]
    return f"""# APQ Manual Source / Crop Acquisition Packet

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This is a review-only manual acquisition-prep packet for APQ001. It is APQ001 quarantine-only, not approved, not publish-ready, and it does not download, scrape, move, or auto-enable any source.

## Why APQ Layout Is Paused

- `variant_03_clean_editorial` is still the best baseline.
- The current source candidate fails the face-safe crop criterion.
- The current review-only Blender layout should not get micro-polished until a wider review-only crop/source candidate is manually identified.

variant_03_clean_editorial is still the best baseline, but the current source candidate fails the face-safe crop criterion.

## Decision Evidence

{chr(10).join(evidence_lines)}

## Current Truth Snapshot

- Strongest baseline candidate: `variant_03_clean_editorial`
- Face fully in frame: `{str(payload['current_truth']['baseline_subject_face_within_frame_intent']).lower()}`
- Face edge clipping reduced: `{str(payload['current_truth']['baseline_face_edge_clipping_reduced']).lower()}`
- Top spotlight softened: `{str(payload['current_truth']['baseline_top_spotlight_softened']).lower()}`
- Minimalist font scaling standardized: `{str(payload['current_truth']['baseline_minimalist_font_scaling_standardized']).lower()}`
- Review-only derived crop used: `{str(payload['current_truth']['baseline_review_only_derived_crop']).lower()}`
- Source photo crop mode: `{payload['current_truth']['baseline_source_photo_crop_mode'] or 'missing'}`
- Score typography treatment: `{payload['current_truth']['baseline_score_typography_treatment'] or 'missing'}`

## Manual Acquisition Checklist

Fill one row in `manual_source_crop_acquisition_intake.csv` for any candidate you want reviewed next.

- `source_url`
- `source_type`
- `entity_id`
- `rights_class`
- `identity_confidence`
- `intended_review_only_use`
- `face_fully_in_frame_expected`
- `wider_frame_available`
- `download_approved`
- `manual_reviewer_notes`
- `reject_reason`

## Candidate Acceptance Criteria

- Athlete face fully in frame.
- Enough margin around the face and right edge for a 4:5 layout.
- No severe body or jersey text conflict where type has to sit.
- Source provenance and rights class are manually reviewable.
- Identity confidence is manually documented.
- Quarantine destination only, if later approved for a review-only download through the human intake flow.

## Next-Lane Decision Logic

- If a better review-only crop is manually approved later, run a future crop-refresh lane.
- If no better crop exists, pause APQ Blender polish and choose another visual/source strategy.
- Do not continue layout micro-polish against the current crop.

## Hard Guardrails

- No automatic downloads.
- No automatic scraping.
- No source auto-enablement.
- No asset approval.
- No approval-state changes.
- No `.approved` markers.
- No protected asset moves.
- No publish-ready state/files.
- No publishing.

## Review-Only / Manual-Only

- review_only={str(payload['review_only']).lower()}
- apq001_quarantine_only={str(payload['apq001_quarantine_only']).lower()}
- not_approved={str(payload['not_approved']).lower()}
- not_publish_ready={str(payload['not_publish_ready']).lower()}
"""


def render_readme(payload: dict[str, Any]) -> str:
    return f"""# Manual Source / Crop Acquisition Packet

This packet is a manual-only intake surface for a better review-only APQ001 source/crop candidate.

It does not download, scrape, approve, move, or auto-enable sources.

Default intake posture:
- `download_approved=no`
- review-only
- APQ001 quarantine-only
- not approved
- not publish-ready

If you later find a better review-only crop, use the human-edited intake flow with the required source and rights fields.

Generated from `{payload['evidence_items'][0]['target_path']}` style decision evidence and the current post-v10 truth state.
"""


def build_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    row = {
        "row_kind": "manual_intake_template",
        "row_id": "APQ001_CROP_INTAKE_TEMPLATE",
        "source_url": "",
        "source_type": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "face_fully_in_frame_expected": "",
        "wider_frame_available": "",
        "download_approved": "no",
        "manual_reviewer_notes": "",
        "reject_reason": "",
        "future_lane_recommendation": "pause_current_layout_polish_until_better_review_only_crop_exists",
        "evidence_target_path": "",
        "evidence_resolved_path": "",
        "evidence_present": "",
        "review_only": "true",
        "apq001_quarantine_only": "true",
        "not_approved": "true",
        "not_publish_ready": "true",
        "asset_downloads": "false",
        "download_performed": "false",
        "source_auto_enabled": "false",
        "approval_state_change": "false",
        "asset_approved": "false",
        "move_files": "false",
        "protected_asset_moves": "false",
        "publish_ready": "false",
        "publishing": "false",
        "auto_publish": "false",
        "auto_approval": "false",
    }
    return [row]


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    evidence_items = [resolve_evidence(item) for item in EVIDENCE_TARGETS]
    current_truth = load_current_truth()
    ready = all(item["present"] for item in evidence_items)
    status = "apq_manual_source_crop_acquisition_ready" if ready else "apq_manual_source_crop_acquisition_missing_sources"

    out_dir = packet_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / MANIFEST_NAME
    report_path = out_dir / PACKET_NAME
    csv_path = out_dir / CSV_NAME
    readme_path = out_dir / README_NAME

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_at_utc": now_iso(),
        "generated_by": GENERATED_BY,
        "repo_head": clean(args.head_commit),
        "packet_dir": out_dir.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "csv_path": csv_path.as_posix(),
        "readme_path": readme_path.as_posix(),
        "evidence_items": evidence_items,
        "current_truth": current_truth,
        "manual_intake_fields": MANUAL_INTAKE_FIELDS,
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
        "publish_ready": False,
        "publishing": False,
        "auto_publish": False,
        "auto_approval": False,
        "download_approved_default": "no",
        "future_lane_decision_logic": [
            "If a better review-only crop is manually approved later, run a future crop-refresh lane.",
            "If no better crop exists, pause APQ Blender polish and choose another visual/source strategy.",
            "Do not continue layout micro-polish against the current crop.",
        ],
    }

    rows = build_rows(payload)
    write_text(report_path, render_report(payload), normalize=strip_volatile_markdown_lines)
    write_text(readme_path, render_readme(payload), normalize=strip_volatile_markdown_lines)
    write_csv(csv_path, rows, CSV_FIELDS, extrasaction="ignore")
    write_json(manifest_path, payload, sort_keys=True)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a manual APQ source/crop acquisition packet.")
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
                "publish_ready": False,
                "publishing": False,
                "auto_publish": False,
                "auto_approval": False,
                "download_approved_default": "no",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
