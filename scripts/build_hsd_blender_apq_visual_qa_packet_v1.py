from __future__ import annotations

import argparse
import json
import math
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text

try:  # pragma: no cover - Pillow is expected in the repo, but this keeps the packet resilient.
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:  # pragma: no cover - runtime fallback
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-blender-apq-before-after-decision-packet-v1-review-only"
GENERATED_BY = "scripts/build_hsd_blender_apq_visual_qa_packet_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("blender_apq_before_after_decision_packet")
PREVIOUS_VARIANTS_ROOT = LATEST_FILES_ROOT / "blender_apq_visual_qa_packet"
PREVIOUS_CONTACT_SHEET_REL = PREVIOUS_VARIANTS_ROOT / "visual_qa_contact_sheet.png"
PREVIOUS_REPORT_REL = PREVIOUS_VARIANTS_ROOT / "visual_qa_report.md"
PREVIOUS_MANUAL_REVIEW_INTAKE_REL = PREVIOUS_VARIANTS_ROOT / "manual_visual_review_intake.csv"
PREVIOUS_MANIFEST_REL = PREVIOUS_VARIANTS_ROOT / "manifest.json"
CURRENT_VARIANTS_ROOT = LATEST_FILES_ROOT / "blender_apq_composition_variants"
CURRENT_CONTACT_SHEET_REL = CURRENT_VARIANTS_ROOT / "contact_sheet.png"
CURRENT_VARIANT_01_REL = CURRENT_VARIANTS_ROOT / "variant_01_photo_anchor.png"
CURRENT_VARIANT_02_REL = CURRENT_VARIANTS_ROOT / "variant_02_score_drama.png"
CURRENT_VARIANT_03_REL = CURRENT_VARIANTS_ROOT / "variant_03_clean_editorial.png"
CURRENT_MANIFEST_REL = CURRENT_VARIANTS_ROOT / "manifest.json"
CURRENT_MANUAL_REVIEW_INTAKE_REL = CURRENT_VARIANTS_ROOT / "manual_variant_review_intake.csv"
LEGACY_REFERENCE_ROOTS = [
    Path("outputs/local/tmp/blender_apq_visual_qa_refresh_v9"),
    Path("outputs/local/tmp/blender_apq_clean_editorial_crop_v10"),
]
REPORT_NAME = "visual_qa_report.md"
README_NAME = "README.md"
MANIFEST_NAME = "manifest.json"
INTAKE_NAME = "manual_visual_review_intake.csv"
CONTACT_SHEET_NAME = "visual_qa_contact_sheet.png"

MANUAL_REVIEW_QUESTIONS = [
    {
        "row_id": "APQBQQ001",
        "question": "Accept variant_03_clean_editorial as the lead direction despite the current face-crop limitation?",
        "decision_options": "accept_baseline|revise_if_better_review_only_crop_exists|pause_for_manual_acceptance_qa",
    },
    {
        "row_id": "APQBQQ002",
        "question": "Does the post-v10 after surface feel meaningfully better than the pre-v10 before surface?",
        "decision_options": "yes|mostly|no|unclear",
    },
    {
        "row_id": "APQBQQ003",
        "question": "Should the next lane continue Blender polish, try a different crop/framing, or pause for manual QA?",
        "decision_options": "continue_blender_composition_polish|try_different_crop_framing|pause_for_manual_acceptance_qa",
    },
]

SOURCE_ARTIFACTS = [
    {
        "row_id": "APQBFR001",
        "comparison_surface": "before_pre_v10",
        "row_kind": "source_artifact",
        "display_name": "Before: pre-v10 visual QA contact sheet",
        "artifact_path": PREVIOUS_CONTACT_SHEET_REL.as_posix(),
        "source_role": "before_contact_sheet",
        "review_question": "Open this first and judge the earlier pre-v10 visual QA surface at a glance.",
    },
    {
        "row_id": "APQBFR002",
        "comparison_surface": "before_pre_v10",
        "row_kind": "source_artifact",
        "display_name": "Before: pre-v10 visual QA report",
        "artifact_path": PREVIOUS_REPORT_REL.as_posix(),
        "source_role": "before_report",
        "review_question": "Use this to compare the earlier decision questions and summary against the current packet.",
    },
    {
        "row_id": "APQBFR003",
        "comparison_surface": "before_pre_v10",
        "row_kind": "source_artifact",
        "display_name": "Before: pre-v10 manual review intake",
        "artifact_path": PREVIOUS_MANUAL_REVIEW_INTAKE_REL.as_posix(),
        "source_role": "before_manual_review_intake",
        "review_question": "Use this intake to compare the earlier prompts against the current decision packet.",
    },
    {
        "row_id": "APQBFR004",
        "comparison_surface": "before_pre_v10",
        "row_kind": "source_artifact",
        "display_name": "Before: pre-v10 manifest",
        "artifact_path": PREVIOUS_MANIFEST_REL.as_posix(),
        "source_role": "before_manifest",
        "review_question": "Use this manifest to confirm the earlier guardrail posture and surface evidence.",
    },
    {
        "row_id": "APQBAR001",
        "comparison_surface": "after_post_v10",
        "row_kind": "source_artifact",
        "display_name": "After: post-v10 current contact sheet",
        "artifact_path": CURRENT_CONTACT_SHEET_REL.as_posix(),
        "source_role": "after_contact_sheet",
        "review_question": "Open this second and judge the current post-v10 composition variants at a glance.",
    },
    {
        "row_id": "APQBAR002",
        "comparison_surface": "after_post_v10",
        "row_kind": "source_artifact",
        "display_name": "After: post-v10 variant_01_photo_anchor",
        "artifact_path": CURRENT_VARIANT_01_REL.as_posix(),
        "source_role": "after_variant_image",
        "review_question": "Use this variant to decide whether the full-photo direction deserves to remain in the packet.",
    },
    {
        "row_id": "APQBAR003",
        "comparison_surface": "after_post_v10",
        "row_kind": "source_artifact",
        "display_name": "After: post-v10 variant_02_score_drama",
        "artifact_path": CURRENT_VARIANT_02_REL.as_posix(),
        "source_role": "after_variant_image",
        "review_question": "Use this variant to compare the score-forward rhythm against the lead direction.",
    },
    {
        "row_id": "APQBAR004",
        "comparison_surface": "after_post_v10",
        "row_kind": "source_artifact",
        "display_name": "After: post-v10 variant_03_clean_editorial",
        "artifact_path": CURRENT_VARIANT_03_REL.as_posix(),
        "source_role": "after_variant_image",
        "review_question": "Use this variant to judge the calmer baseline that Gemini treated as strongest.",
    },
    {
        "row_id": "APQBAR005",
        "comparison_surface": "after_post_v10",
        "row_kind": "source_artifact",
        "display_name": "After: post-v10 current manifest",
        "artifact_path": CURRENT_MANIFEST_REL.as_posix(),
        "source_role": "after_manifest",
        "review_question": "Use this manifest to confirm the review-only guardrails and texture evidence.",
    },
    {
        "row_id": "APQBAR006",
        "comparison_surface": "after_post_v10",
        "row_kind": "source_artifact",
        "display_name": "After: post-v10 current manual review intake",
        "artifact_path": CURRENT_MANUAL_REVIEW_INTAKE_REL.as_posix(),
        "source_role": "after_manual_review_intake",
        "review_question": "Use this intake to compare the current prompts with the before/after decision packet.",
    },
]

CSV_FIELDS = [
    "row_kind",
    "row_id",
    "comparison_surface",
    "display_name",
    "artifact_path",
    "source_exists",
    "source_status",
    "review_question",
    "decision_options",
    "operator_decision",
    "operator_notes",
    "review_only",
    "artifact_only",
    "apq001_quarantine_only",
    "asset_downloads",
    "download_performed",
    "image_edits",
    "generated_contact_sheet_allowed",
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

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "image_edits": False,
    "move_files": False,
    "production_renderer_replacement": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "renderer_behavior_change": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def packet_root() -> Path:
    run_root = run_output_dir()
    if run_root:
        return run_root
    return repo_root() / LATEST_FILES_ROOT / OUT_DIR_REL


def source_candidates(path: Path) -> list[Path]:
    if path.is_absolute():
        return [path]
    candidates: list[Path] = []
    run_root = run_output_dir()
    if run_root:
        candidates.append(run_root / path)
    candidates.append(repo_root() / path)
    candidates.append(Path.cwd() / path)
    try:
        suffix = path.relative_to(LATEST_FILES_ROOT)
    except ValueError:
        suffix = None
    if suffix is not None:
        for legacy_root in LEGACY_REFERENCE_ROOTS:
            candidates.append(repo_root() / legacy_root / path.name)
    return candidates


def find_existing_input(path: Path) -> Path | None:
    for candidate in source_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def current_variant_candidates() -> list[Path]:
    return [
        candidate.resolve(strict=False)
        for candidate in (
            source_candidates(CURRENT_VARIANT_01_REL)[0],
            source_candidates(CURRENT_VARIANT_02_REL)[0],
            source_candidates(CURRENT_VARIANT_03_REL)[0],
        )
    ]


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_question_options(options: str) -> str:
    return clean(options)


def make_artifact_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base_row in SOURCE_ARTIFACTS:
        exists = find_existing_input(Path(base_row["artifact_path"])) is not None
        rows.append(
            {
                **base_row,
                "source_exists": exists,
                "source_status": "present" if exists else "missing",
                "comparison_surface": str(base_row.get("comparison_surface") or ""),
                "decision_options": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": True,
                "artifact_only": True,
                "apq001_quarantine_only": True,
                "asset_downloads": False,
                "download_performed": False,
                "image_edits": False,
                "generated_contact_sheet_allowed": False,
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
        )

    return rows


def make_question_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for question in MANUAL_REVIEW_QUESTIONS:
        rows.append(
            {
                "row_kind": "question",
                "row_id": question["row_id"],
                "comparison_surface": "",
                "display_name": question["question"],
                "artifact_path": "",
                "source_exists": "",
                "source_status": "",
                "review_question": question["question"],
                "decision_options": normalize_question_options(question["decision_options"]),
                "operator_decision": "",
                "operator_notes": "",
                "review_only": True,
                "artifact_only": True,
                "apq001_quarantine_only": True,
                "asset_downloads": False,
                "download_performed": False,
                "image_edits": False,
                "generated_contact_sheet_allowed": False,
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
        )
    return rows


def build_contact_sheet(image_rows: list[dict[str, Any]], packet_dir: Path) -> dict[str, Any]:
    contact_sheet_path = packet_dir / CONTACT_SHEET_NAME
    if Image is None or ImageDraw is None or ImageFont is None:
        return {
            "created": False,
            "path": "",
            "reason": "pillow_unavailable",
            "source_count": len(image_rows),
        }
    if not image_rows:
        return {
            "created": False,
            "path": "",
            "reason": "no_reference_images_found",
            "source_count": 0,
        }

    images: list[dict[str, Any]] = []
    for row in image_rows:
        path = find_existing_input(Path(row["artifact_path"])) or Path(row["artifact_path"])
        try:
            image = Image.open(path).convert("RGB")
        except Exception as exc:  # pragma: no cover - defensive on unreadable local files
            row["source_status"] = f"unreadable:{type(exc).__name__}"
            continue
        images.append({"row": row, "image": image})

    if not images:
        return {
            "created": False,
            "path": "",
            "reason": "no_readable_images_found",
            "source_count": len(image_rows),
        }

    margin = 28
    title_h = 112
    footer_h = 72
    cols = 2 if len(images) > 1 else 1
    cell_w = 530
    cell_h = 610
    sheet_w = cols * cell_w + margin * 2
    rows = math.ceil(len(images) / cols)
    sheet_h = title_h + rows * cell_h + footer_h + margin
    canvas = Image.new("RGB", (sheet_w, sheet_h), (247, 248, 250))
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

    draw.rectangle((0, 0, sheet_w, title_h), fill=(232, 236, 242))
    draw.text((margin, 18), "APQ001 Blender Before/After Decision Packet", fill=(22, 28, 38), font=title_font)
    draw.text(
        (margin, 48),
        "Review-only, artifact-only, no approvals. Compare the pre-v10 visual QA surface with the post-v10 composition variants.",
        fill=(50, 58, 69),
        font=body_font,
    )

    for index, item in enumerate(images):
        row = index // cols
        col = index % cols
        x0 = margin + col * cell_w
        y0 = title_h + row * cell_h
        draw.rounded_rectangle((x0, y0, x0 + cell_w - 18, y0 + cell_h - 18), radius=20, fill=(255, 255, 255), outline=(199, 205, 214), width=2)
        image = item["image"]
        thumb_box = (cell_w - 70, 420)
        thumb = ImageOps.contain(image, thumb_box) if ImageOps else image.copy()
        thumb_x = x0 + (cell_w - 18 - thumb.width) // 2
        thumb_y = y0 + 22
        canvas.paste(thumb, (thumb_x, thumb_y))
        label = item["row"]["display_name"]
        label_lines = textwrap.wrap(label, width=32) or [label]
        label_y = y0 + 460
        for line in label_lines[:2]:
            draw.text((x0 + 18, label_y), line, fill=(20, 25, 34), font=title_font)
            label_y += 18
        path_lines = textwrap.wrap(item["row"]["artifact_path"], width=58) or [item["row"]["artifact_path"]]
        for line in path_lines[:2]:
            draw.text((x0 + 18, label_y + 8), line, fill=(74, 84, 94), font=body_font)
            label_y += 12

    draw.text(
        (margin, sheet_h - footer_h + 14),
        "Burn-in legibility, APQ001 photo-first clarity, and noise reduction are the review focus.",
        fill=(50, 58, 69),
        font=body_font,
    )
    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(contact_sheet_path, "PNG")
    return {
        "created": True,
        "path": contact_sheet_path.as_posix(),
        "reason": "",
        "source_count": len(images),
    }


def render_readme(payload: dict[str, Any]) -> str:
    before_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})"
        for row in payload["artifact_rows"]
        if row["row_kind"] == "source_artifact" and row.get("comparison_surface") == "before_pre_v10"
    )
    after_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})"
        for row in payload["artifact_rows"]
        if row["row_kind"] == "source_artifact" and row.get("comparison_surface") == "after_post_v10"
    )
    contact_sheet_line = (
        f"- Comparison sheet: `{payload['contact_sheet_path']}`" if payload["contact_sheet_created"] else "- Comparison sheet: not generated locally"
    )
    return f"""# Blender/APQ Visual QA Packet v1

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is review-only and artifact-only. It packages the pre-v10 visual QA surface and the current post-v10 Blender/APQ composition variants for manual visual QA. It does not change renderer behavior, edit source images, download assets, approve assets, move files, or publish anything.

## Open In Order

1. `visual_qa_report.md`
2. `manual_visual_review_intake.csv`
3. The before and after contact sheets if they are present locally
4. `{CONTACT_SHEET_NAME}` if it was generated

## Before Surface

{before_lines}

## After Surface

{after_lines}

{contact_sheet_line}

## Manual Review Questions

{chr(10).join(f"- {row['review_question']}" for row in payload['review_question_rows'])}

## Guardrails

- review_only=true
- artifact_only=true
- apq001_quarantine_only=true
- asset_downloads=false
- download_performed=false
- image_edits=false
- generated_contact_sheet_allowed={str(payload['generated_contact_sheet_allowed']).lower()}
- approval_state_change=false
- asset_approved=false
- move_files=false
- protected_asset_moves=false
- renderer_behavior_change=false
- production_renderer_replacement=false
- publish_ready=false
- publishing=false
- auto_publish=false
- auto_approval=false
"""


def render_report(payload: dict[str, Any]) -> str:
    before_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})"
        for row in payload["artifact_rows"]
        if row["row_kind"] == "source_artifact" and row.get("comparison_surface") == "before_pre_v10"
    )
    after_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})"
        for row in payload["artifact_rows"]
        if row["row_kind"] == "source_artifact" and row.get("comparison_surface") == "after_post_v10"
    )
    missing_lines = "\n".join(f"- `{path}`" for path in payload["missing_primary_artifact_paths"]) or "- None"
    reference_lines = "\n".join(f"- `{path}`" for path in payload["reference_artifact_paths"]) or "- None"
    question_lines = "\n".join(
        f"- {row['review_question']}  \n  Options: `{row['decision_options']}`" for row in payload["review_question_rows"]
    )
    next_lane_lines = "\n".join(
        [
            "- Accept the current clean-editorial baseline if the after surface is the clearest lead direction.",
            "- Revise only if a better review-only source crop exists locally.",
            "- Pause Blender polish and move to manual QA if the current source candidate stays too tight on the face.",
        ]
    )
    contact_sheet_line = (
        f"- Comparison sheet created at `{payload['contact_sheet_path']}` with `{payload['contact_sheet_source_count']}` source image(s)."
        if payload["contact_sheet_created"]
        else "- No comparison sheet was generated because no readable source images were found locally."
    )
    return f"""# Blender/APQ Visual QA Report

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This is a review-only artifact packet for the APQ001 Blender/APQ before/after decision surface. It is meant to help a human compare the earlier pre-v10 visual QA packet against the current post-v10 composition variants before deciding the next lane.

## What To Review

- Before contact sheet path: `{payload['previous_contact_sheet_path']}`
- After contact sheet path: `{payload['current_contact_sheet_path']}`
- Current manifest path: `{payload['current_manifest_path']}`
- Current manual review intake path: `{payload['current_manual_review_intake_path']}`
{contact_sheet_line}

## Before Surface

{before_lines}

## After Surface

{after_lines}

## Reference Artifacts

{reference_lines}

## Missing Primary Artifacts

{missing_lines}

## Local Reference Images Discovered

{reference_lines}

## Manual Review Questions

{question_lines}

## Next Lane Choices

{next_lane_lines}

## Guardrails

{chr(10).join(f"- {key}={str(value).lower()}" for key, value in sorted(payload["guardrails"].items()))}
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    packet_dir = packet_root()
    packet_dir.mkdir(parents=True, exist_ok=True)

    artifact_rows = make_artifact_rows()
    question_rows = make_question_rows()
    previous_contact_sheet_row = next((row for row in artifact_rows if row["row_id"] == "APQBFR001"), None)
    previous_manifest_row = next((row for row in artifact_rows if row["row_id"] == "APQBFR004"), None)
    current_contact_sheet_row = next((row for row in artifact_rows if row["row_id"] == "APQBAR001"), None)
    current_manifest_row = next((row for row in artifact_rows if row["row_id"] == "APQBAR005"), None)
    current_intake_row = next((row for row in artifact_rows if row["row_id"] == "APQBAR006"), None)
    previous_contact_sheet_present = bool(previous_contact_sheet_row and previous_contact_sheet_row["source_exists"])
    current_contact_sheet_present = bool(current_contact_sheet_row and current_contact_sheet_row["source_exists"])
    previous_manifest_present = bool(previous_manifest_row and previous_manifest_row["source_exists"])
    current_manifest_present = bool(current_manifest_row and current_manifest_row["source_exists"])
    current_intake_present = bool(current_intake_row and current_intake_row["source_exists"])
    reference_artifact_paths = [row["artifact_path"] for row in artifact_rows if row["row_kind"] == "source_artifact"]
    comparison_sheet_rows = [row for row in artifact_rows if row["row_kind"] == "source_artifact" and row.get("display_name", "").startswith(("Before: pre-v10 visual QA contact sheet", "After: post-v10 current contact sheet"))]
    missing_primary_artifact_paths = [row["artifact_path"] for row in artifact_rows if not row["source_exists"]]

    contact_sheet_rows = [row for row in comparison_sheet_rows if row["source_exists"]]
    contact_sheet_info = build_contact_sheet(contact_sheet_rows, packet_dir)
    contact_sheet_created = bool(contact_sheet_info["created"])
    if contact_sheet_created:
        artifact_rows.append(
            {
                "row_kind": "generated_artifact",
                "row_id": "APQBGC001",
                "comparison_surface": "generated_before_after",
                "display_name": "Generated APQ001 before/after decision sheet",
                "artifact_path": contact_sheet_info["path"],
                "source_exists": True,
                "source_status": "present",
                "review_question": "Use this generated comparison sheet to compare the before and after surfaces quickly.",
                "decision_options": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": True,
                "artifact_only": True,
                "apq001_quarantine_only": True,
                "asset_downloads": False,
                "download_performed": False,
                "image_edits": False,
                "generated_contact_sheet_allowed": True,
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
        )

    any_source_present = any(row["source_exists"] for row in artifact_rows if row["row_kind"] == "source_artifact")
    status = (
        "blender_apq_before_after_decision_packet_ready"
        if previous_contact_sheet_present and current_contact_sheet_present
        else "blender_apq_before_after_decision_packet_reference_only"
        if any_source_present
        else "blender_apq_before_after_decision_packet_missing_sources"
    )

    readme_path = packet_dir / README_NAME
    report_path = packet_dir / REPORT_NAME
    manifest_path = packet_dir / MANIFEST_NAME
    intake_path = packet_dir / INTAKE_NAME
    contact_sheet_path = packet_dir / CONTACT_SHEET_NAME if contact_sheet_created else Path("")

    guardrails = dict(FALSE_GUARDRAILS)
    guardrails["generated_contact_sheet_allowed"] = contact_sheet_created

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_at_utc": now_iso(),
        "generated_by": GENERATED_BY,
        "repo_head": clean(args.head_commit),
        "packet_dir": packet_dir.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "readme_path": readme_path.as_posix(),
        "report_path": report_path.as_posix(),
        "manual_visual_review_intake_path": intake_path.as_posix(),
        "contact_sheet_path": contact_sheet_path.as_posix() if contact_sheet_created else "",
        "contact_sheet_created": contact_sheet_created,
        "contact_sheet_source_count": contact_sheet_info["source_count"] if contact_sheet_created else 0,
        "generated_contact_sheet_allowed": contact_sheet_created,
        "previous_contact_sheet_path": PREVIOUS_CONTACT_SHEET_REL.as_posix(),
        "previous_contact_sheet_present": previous_contact_sheet_present,
        "previous_manifest_path": PREVIOUS_MANIFEST_REL.as_posix(),
        "previous_manifest_present": previous_manifest_present,
        "current_contact_sheet_path": CURRENT_CONTACT_SHEET_REL.as_posix(),
        "current_contact_sheet_present": current_contact_sheet_present,
        "current_variant_image_paths": [
            CURRENT_VARIANT_01_REL.as_posix(),
            CURRENT_VARIANT_02_REL.as_posix(),
            CURRENT_VARIANT_03_REL.as_posix(),
        ],
        "current_variant_image_count": 3,
        "current_manifest_path": CURRENT_MANIFEST_REL.as_posix(),
        "current_manifest_present": current_manifest_present,
        "current_manual_review_intake_path": CURRENT_MANUAL_REVIEW_INTAKE_REL.as_posix(),
        "current_manual_review_intake_present": current_intake_present,
        "source_artifacts": artifact_rows,
        "artifact_rows": artifact_rows,
        "artifact_row_count": len(artifact_rows),
        "review_question_rows": question_rows,
        "review_question_count": len(question_rows),
        "manual_review_questions": [row["review_question"] for row in question_rows],
        "manual_review_decision_vocabulary": [row["decision_options"] for row in question_rows],
        "reference_artifact_paths": reference_artifact_paths,
        "reference_artifact_count": len(reference_artifact_paths),
        "reference_image_paths": [row["artifact_path"] for row in comparison_sheet_rows if row["source_exists"]],
        "reference_image_count": len([row for row in comparison_sheet_rows if row["source_exists"]]),
        "missing_primary_artifact_paths": missing_primary_artifact_paths,
        "guardrails": guardrails,
        "review_only": True,
        "artifact_only": True,
        "apq001_quarantine_only": True,
        "asset_downloads": False,
        "download_performed": False,
        "image_edits": False,
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
        "previous_contact_sheet_status": "present" if previous_contact_sheet_present else "missing",
        "previous_manifest_status": "present" if previous_manifest_present else "missing",
        "current_contact_sheet_status": "present" if current_contact_sheet_present else "missing",
        "current_manifest_status": "present" if current_manifest_present else "missing",
        "current_manual_review_intake_status": "present" if current_intake_present else "missing",
        "contact_sheet_reason": contact_sheet_info["reason"],
    }

    write_csv(intake_path, [*artifact_rows, *question_rows], CSV_FIELDS, extrasaction="ignore")
    write_text(report_path, render_report(payload), normalize=strip_volatile_markdown_lines)
    write_text(readme_path, render_readme(payload), normalize=strip_volatile_markdown_lines)
    write_json(manifest_path, payload, sort_keys=True)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only Blender/APQ visual QA packet.")
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
                "artifact_row_count": payload["artifact_row_count"],
                "review_question_count": payload["review_question_count"],
                "contact_sheet_created": payload["contact_sheet_created"],
                "generated_contact_sheet_allowed": payload["generated_contact_sheet_allowed"],
                "current_contact_sheet_present": payload["current_contact_sheet_present"],
                "current_manifest_present": payload["current_manifest_present"],
                "review_only": True,
                "artifact_only": True,
                "apq001_quarantine_only": True,
                "asset_downloads": False,
                "download_performed": False,
                "image_edits": False,
                "approval_state_change": False,
                "asset_approved": False,
                "move_files": False,
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
