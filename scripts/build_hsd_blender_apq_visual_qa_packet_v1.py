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


VERSION = "hsd-blender-apq-visual-qa-packet-v1-review-only"
GENERATED_BY = "scripts/build_hsd_blender_apq_visual_qa_packet_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("blender_apq_visual_qa_packet")
CURRENT_PROTO_IMAGE_REL = LATEST_FILES_ROOT / "blender_apq_4x5_prototype" / "blender_apq_4x5_prototype_4x5.png"
CURRENT_PROTO_MANIFEST_REL = LATEST_FILES_ROOT / "blender_apq_4x5_prototype" / "blender_apq_4x5_prototype_manifest.json"
REPORT_NAME = "visual_qa_report.md"
README_NAME = "README.md"
MANIFEST_NAME = "manifest.json"
INTAKE_NAME = "manual_visual_review_intake.csv"
CONTACT_SHEET_NAME = "visual_qa_contact_sheet.png"

MANUAL_REVIEW_QUESTIONS = [
    {
        "row_id": "APQBVQQ001",
        "question": "Does v3 materially reduce noise, grain, or blockiness compared with the prior APQ Blender prototype direction?",
        "decision_options": "materially_improved|about_the_same|worse|unclear",
    },
    {
        "row_id": "APQBVQQ002",
        "question": "Does APQ001 read as a useful photo-first visual anchor?",
        "decision_options": "yes|mostly|no|unclear",
    },
    {
        "row_id": "APQBVQQ003",
        "question": "Is the review-only burn-in legible and appropriately prominent?",
        "decision_options": "yes|mostly|no|unclear",
    },
    {
        "row_id": "APQBVQQ004",
        "question": "Should the next lane continue Blender composition polish, try a different crop or framing, or pause for external visual QA?",
        "decision_options": "continue_blender_composition_polish|try_different_crop_framing|pause_for_external_visual_qa",
    },
]

PRIMARY_ARTIFACTS = [
    {
        "row_id": "APQBVQ001",
        "row_kind": "source_artifact",
        "display_name": "Current APQ001 Blender 4:5 prototype image",
        "artifact_path": CURRENT_PROTO_IMAGE_REL.as_posix(),
        "source_role": "current_prototype_image",
        "review_question": "Open this image first and judge the current v3 prototype visually.",
    },
    {
        "row_id": "APQBVQ002",
        "row_kind": "source_artifact",
        "display_name": "Current APQ001 Blender prototype manifest",
        "artifact_path": CURRENT_PROTO_MANIFEST_REL.as_posix(),
        "source_role": "current_prototype_manifest",
        "review_question": "Use this companion manifest to confirm the current review-only guardrails.",
    },
]

CSV_FIELDS = [
    "row_kind",
    "row_id",
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
    return candidates


def find_existing_input(path: Path) -> Path | None:
    for candidate in source_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def current_proto_candidates() -> list[Path]:
    return [candidate.resolve(strict=False) for candidate in source_candidates(CURRENT_PROTO_IMAGE_REL)]


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_question_options(options: str) -> str:
    return clean(options)


def discovered_reference_images() -> list[dict[str, Any]]:
    patterns = [
        "outputs/local/latest/files/blender_apq_4x5_prototype*/*.png",
        "outputs/local/latest/files/blender_apq_4x5_prototype*/**/*.png",
        "outputs/local/latest/files/blender_apq_4x5_prototype*/*.jpg",
        "outputs/local/latest/files/blender_apq_4x5_prototype*/**/*.jpg",
        "outputs/local/latest/files/blender_apq_4x5_prototype*/*.jpeg",
        "outputs/local/latest/files/blender_apq_4x5_prototype*/**/*.jpeg",
    ]
    roots = [repo_root()]
    run_root = run_output_dir()
    if run_root:
        roots.insert(0, run_root)

    current_images = {candidate for candidate in current_proto_candidates()}
    seen: set[Path] = set()
    matches: list[dict[str, Any]] = []

    for base in roots:
        for pattern in patterns:
            for candidate in sorted(base.glob(pattern)):
                if not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                status = "present"
                role = "current_latest_prototype_image" if resolved in current_images else "reference_prototype_image"
                matches.append(
                    {
                        "path": resolved,
                        "artifact_path": resolved.as_posix(),
                        "display_name": (
                            "Current prototype image"
                            if role == "current_latest_prototype_image"
                            else f"Reference prototype image: {resolved.parent.name}"
                        ),
                        "row_kind": "source_artifact",
                        "row_id": "APQBVQ001" if role == "current_latest_prototype_image" else f"APQBVQREF{len(matches) + 1:03d}",
                        "source_role": role,
                        "source_exists": True,
                        "source_status": status,
                        "review_question": (
                            "Open the current prototype image first."
                            if role == "current_latest_prototype_image"
                            else "Use this local reference image only for comparison; do not edit or approve it."
                        ),
                    }
                )
    return matches


def make_artifact_rows() -> list[dict[str, Any]]:
    current_image = find_existing_input(CURRENT_PROTO_IMAGE_REL)
    current_manifest = find_existing_input(CURRENT_PROTO_MANIFEST_REL)
    reference_images = discovered_reference_images()
    reference_image_rows = [row for row in reference_images if row["source_role"] != "current_latest_prototype_image"]
    current_image_present = current_image is not None
    current_manifest_present = current_manifest is not None

    rows: list[dict[str, Any]] = []
    for base_row in PRIMARY_ARTIFACTS:
        exists = current_image_present if base_row["row_id"] == "APQBVQ001" else current_manifest_present
        rows.append(
            {
                **base_row,
                "source_exists": exists,
                "source_status": "present" if exists else "missing",
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

    for index, row in enumerate(reference_image_rows, start=1):
        rows.append(
            {
                "row_kind": "source_artifact",
                "row_id": f"APQBVQREF{index:03d}",
                "display_name": row["display_name"],
                "artifact_path": row["artifact_path"],
                "source_exists": True,
                "source_status": "present",
                "review_question": row["review_question"],
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
        path = Path(row["artifact_path"])
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
    draw.text((margin, 18), "APQ001 Blender Visual QA Contact Sheet", fill=(22, 28, 38), font=title_font)
    draw.text(
        (margin, 48),
        "Review-only, artifact-only, no approvals. Compare the current prototype with any local references.",
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
    reference_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})"
        for row in payload["artifact_rows"]
        if row["row_kind"] == "source_artifact"
    )
    contact_sheet_line = (
        f"- Contact sheet: `{payload['contact_sheet_path']}`" if payload["contact_sheet_created"] else "- Contact sheet: not generated locally"
    )
    return f"""# Blender/APQ Visual QA Packet v1

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is review-only and artifact-only. It does not change renderer behavior, edit source images, download assets, approve assets, move files, or publish anything.

## Open In Order

1. `visual_qa_report.md`
2. `manual_visual_review_intake.csv`
3. The current prototype image if it is present locally
4. `{CONTACT_SHEET_NAME}` if it was generated

## Local Review Targets

{reference_lines}

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
    source_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})"
        for row in payload["artifact_rows"]
        if row["row_kind"] == "source_artifact"
    )
    missing_lines = "\n".join(f"- `{path}`" for path in payload["missing_primary_artifact_paths"]) or "- None"
    reference_lines = "\n".join(f"- `{path}`" for path in payload["reference_image_paths"]) or "- None"
    question_lines = "\n".join(
        f"- {row['review_question']}  \n  Options: `{row['decision_options']}`" for row in payload["review_question_rows"]
    )
    next_lane_lines = "\n".join(
        [
            "- Continue Blender composition polish if the image is strong but still needs small cleanup.",
            "- Try a different crop or framing if the current composition feels close but not quite right.",
            "- Pause for external visual QA if the result needs a second set of eyes before another renderer pass.",
        ]
    )
    contact_sheet_line = (
        f"- Contact sheet created at `{payload['contact_sheet_path']}` with `{payload['contact_sheet_source_count']}` source image(s)."
        if payload["contact_sheet_created"]
        else "- No contact sheet was generated because no readable source images were found locally."
    )
    return f"""# Blender/APQ Visual QA Report

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This is a review-only artifact packet for the APQ001 Blender 4:5 prototype progression. It is meant to help a human compare the current prototype against any local prior references before deciding the next lane.

## What To Review

- Current prototype image path: `{payload['current_prototype_image_path']}`
- Current prototype manifest path: `{payload['current_prototype_manifest_path']}`
{contact_sheet_line}

## Source Artifacts

{source_lines}

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
    current_image_row = next((row for row in artifact_rows if row["row_id"] == "APQBVQ001"), None)
    current_manifest_row = next((row for row in artifact_rows if row["row_id"] == "APQBVQ002"), None)
    current_image_present = bool(current_image_row and current_image_row["source_exists"])
    current_manifest_present = bool(current_manifest_row and current_manifest_row["source_exists"])

    discovered_images = discovered_reference_images()
    current_image_candidates = set(current_proto_candidates())
    reference_image_paths = [row["artifact_path"] for row in discovered_images]
    missing_primary_artifact_paths = [
        path
        for path, present in [
            (CURRENT_PROTO_IMAGE_REL.as_posix(), current_image_present),
            (CURRENT_PROTO_MANIFEST_REL.as_posix(), current_manifest_present),
        ]
        if not present
    ]

    contact_sheet_rows = [row for row in discovered_images if row["path"] not in current_image_candidates]
    if current_image_present:
        current_discovered_rows = [row for row in discovered_images if row["path"] in current_image_candidates]
        contact_sheet_rows = [*current_discovered_rows, *contact_sheet_rows]
    contact_sheet_info = build_contact_sheet(contact_sheet_rows, packet_dir)
    contact_sheet_created = bool(contact_sheet_info["created"])
    if contact_sheet_created:
        artifact_rows.append(
            {
                "row_kind": "generated_artifact",
                "row_id": "APQBVQCS001",
                "display_name": "Generated APQ001 visual QA contact sheet",
                "artifact_path": contact_sheet_info["path"],
                "source_exists": True,
                "source_status": "present",
                "review_question": "Use this generated contact sheet for quick comparison between the current prototype and any local references.",
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

    status = (
        "blender_apq_visual_qa_packet_ready"
        if current_image_present
        else "blender_apq_visual_qa_packet_reference_only"
        if discovered_images
        else "blender_apq_visual_qa_packet_missing_sources"
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
        "current_prototype_image_path": CURRENT_PROTO_IMAGE_REL.as_posix(),
        "current_prototype_manifest_path": CURRENT_PROTO_MANIFEST_REL.as_posix(),
        "current_prototype_image_present": current_image_present,
        "current_prototype_manifest_present": current_manifest_present,
        "source_artifacts": artifact_rows,
        "artifact_rows": artifact_rows,
        "artifact_row_count": len(artifact_rows),
        "review_question_rows": question_rows,
        "review_question_count": len(question_rows),
        "manual_review_questions": [row["review_question"] for row in question_rows],
        "manual_review_decision_vocabulary": [row["decision_options"] for row in question_rows],
        "reference_image_paths": reference_image_paths,
        "reference_image_count": len(reference_image_paths),
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
        "current_prototype_manifest_status": "present" if current_manifest_present else "missing",
        "current_prototype_image_status": "present" if current_image_present else "missing",
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
                "current_prototype_image_present": payload["current_prototype_image_present"],
                "current_prototype_manifest_present": payload["current_prototype_manifest_present"],
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
