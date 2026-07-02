from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
except Exception:  # pragma: no cover - handled at runtime
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]
    UnidentifiedImageError = Exception  # type: ignore[assignment]


VERSION = "hsd-apq001-action-photo-composition-review-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apq001_action_photo_composition_review_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("apq001_action_photo_composition_review")
OUT_MANIFEST_REL = OUT_DIR_REL / "manifest.json"
OUT_COMPOSITION_REL = OUT_DIR_REL / "composition_review.md"
OUT_INTAKE_REL = OUT_DIR_REL / "manual_composition_intake.csv"
OUT_CONTACT_SHEET_REL = OUT_DIR_REL / "composition_contact_sheet.png"

CURRENT_HEADSHOT_REL = Path("render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png")
APQ001_CANDIDATE_REL = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
    "apq001_review_only_candidate.jpg"
)
APQ001_SANDBOX_REL = Path("apq001_quarantine_4x5_render_sandbox/prototype_ig_feed_4x5.png")
APQ001_PROTO_PLAN_REL = Path("apq001_action_photo_4x5_prototype_plan/manifest.json")
APQ001_RECHECK_PLAN_REL = Path("apq001_renderer_recheck_packet/renderer_recheck_plan.csv")
APQ001_MANUAL_RESULT_MANIFEST_REL = Path("apq001_manual_review_result_manifest.json")
APQ001_MANUAL_RESULT_REPORT_REL = Path("apq001_manual_review_result_report.md")

MANUAL_QUESTIONS = [
    {
        "question_id": "APQ001-CR01",
        "review_focus": "headshot_bridge_feel",
        "question": "Does APQ001 materially reduce the roster-card or headshot feel compared with the current 4:5 headshot bridge?",
        "decision_options": "yes, materially|somewhat|no, it still reads like a headshot bridge",
        "manual_notes_prompt": "Say which elements still feel portrait-like, if any.",
    },
    {
        "question_id": "APQ001-CR02",
        "review_focus": "subject_readability",
        "question": "Are face, subject, and action context readable enough for a renderer recheck?",
        "decision_options": "yes|borderline|no",
        "manual_notes_prompt": "Note whether the subject/action read survives the crop.",
    },
    {
        "question_id": "APQ001-CR03",
        "review_focus": "crop_layout_notes",
        "question": "What crop or layout notes are needed before any renderer implementation lane?",
        "decision_options": "freeform notes",
        "manual_notes_prompt": "List the smallest layout changes you would want next.",
    },
    {
        "question_id": "APQ001-CR04",
        "review_focus": "next_lane_choice",
        "question": "Should the next lane prototype an action-photo-aware 4:5 layout, or hold APQ001 for more review?",
        "decision_options": "prototype action-photo-aware 4:5|hold for more review|keep the current headshot bridge",
        "manual_notes_prompt": "Pick the next lane only after the crop read feels clear.",
    },
]

GUARDRAILS = {
    "review_only": True,
    "artifact_only": True,
    "apq001_quarantine_only": True,
    "asset_approved": False,
    "approval_state_change": False,
    "download_performed": False,
    "asset_downloads": False,
    "image_edits": False,
    "move_files": False,
    "publish_ready": False,
    "publishing": False,
    "renderer_behavior_change": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalized(value: Any) -> str:
    return clean(value).lower()


def truthy(value: Any) -> bool:
    return normalized(value) in {"1", "true", "yes", "y", "ready", "pass"}


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


def find_existing_input(path: Path) -> Path | None:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


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


def base_row(label: str, artifact_path: Path, source_exists: bool, *, required: bool = False) -> dict[str, str]:
    status = "present" if source_exists else ("missing_required" if required else "missing_optional")
    return {
        "artifact_label": label,
        "artifact_path": artifact_path.as_posix(),
        "source_exists": "true" if source_exists else "false",
        "source_status": status,
        "review_only": "true",
        "artifact_only": "true",
        "apq001_quarantine_only": "true",
        "asset_approved": "false",
        "approval_state_change": "false",
        "download_performed": "false",
        "asset_downloads": "false",
        "image_edits": "false",
        "move_files": "false",
        "publish_ready": "false",
        "publishing": "false",
        "renderer_behavior_change": "false",
    }


def guardrail_values() -> dict[str, bool]:
    return dict(GUARDRAILS)


def validate_manifest(manifest: Mapping[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        issues.append({"source": path.as_posix(), "field": "input", "issue": "missing_input"})
        return issues
    if normalized(manifest.get("status")) not in {
        "apq001_manual_review_result_artifacts_ready",
        "apq001_manual_review_waiting_for_filled_packet",
    }:
        issues.append({"source": path.as_posix(), "field": "status", "issue": "manual_review_result_not_ready"})
    if not truthy(manifest.get("review_only")):
        issues.append({"source": path.as_posix(), "field": "review_only", "issue": "source_must_be_review_only"})
    if not truthy(manifest.get("artifact_only")):
        issues.append({"source": path.as_posix(), "field": "artifact_only", "issue": "source_must_be_artifact_only"})
    return issues


def validate_plan_manifest(manifest: Mapping[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return issues
    if normalized(manifest.get("status")) not in {
        "apq001_action_photo_4x5_prototype_plan_ready",
        "apq001_action_photo_4x5_prototype_plan_waiting_for_source_rows",
    }:
        issues.append({"source": path.as_posix(), "field": "status", "issue": "prototype_plan_not_ready"})
    return issues


def validate_sandbox_manifest(manifest: Mapping[str, Any], path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return issues
    if normalized(manifest.get("status")) not in {
        "apq001_quarantine_4x5_render_sandbox_ready",
        "apq001_quarantine_4x5_render_sandbox_blocked_missing_source",
        "apq001_quarantine_4x5_render_sandbox_blocked_unreadable_source",
    }:
        issues.append({"source": path.as_posix(), "field": "status", "issue": "sandbox_manifest_unexpected_status"})
    return issues


def try_open_image(path: Path) -> tuple[Any | None, dict[str, Any]]:
    if Image is None:
        return None, {"readable": False, "reason": "pillow_unavailable"}
    if not path.exists():
        return None, {"readable": False, "reason": "missing"}
    try:
        with Image.open(path) as image:
            loaded = image.convert("RGB")
            return loaded, {"readable": True, "size": list(loaded.size)}
    except (UnidentifiedImageError, OSError):
        return None, {"readable": False, "reason": "unreadable"}


def font(size: int, bold: bool = True):
    if ImageFont is None:
        raise RuntimeError("Pillow is unavailable")
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf") if bold else Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_placeholder(draw: Any, box: tuple[int, int, int, int], title: str, note: str) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=22, outline=(98, 105, 115), width=3, fill=(22, 26, 33))
    draw.line((x1 + 18, y1 + 18, x2 - 18, y2 - 18), fill=(72, 78, 87), width=2)
    draw.line((x1 + 18, y2 - 18, x2 - 18, y1 + 18), fill=(72, 78, 87), width=2)
    draw.text((x1 + 22, y1 + 18), title, font=font(26, bold=True), fill=(240, 242, 245))
    draw.text((x1 + 22, y1 + 54), note, font=font(18, bold=False), fill=(198, 204, 214))


def make_sheet_card(
    *,
    title: str,
    subtitle: str,
    artifact_path: str,
    source_exists: bool,
    source_readable: bool,
    image: Any | None,
    note: str,
    size: tuple[int, int] = (920, 690),
) -> Any:
    if Image is None or ImageDraw is None or ImageOps is None:
        raise RuntimeError("Pillow is unavailable")
    card = Image.new("RGB", size, (12, 16, 22))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=24, outline=(52, 58, 69), width=2, fill=(17, 21, 28))
    draw.text((24, 20), title, font=font(26, bold=True), fill=(248, 249, 251))
    draw.text((24, 56), subtitle, font=font(18, bold=False), fill=(181, 188, 198))
    draw.text((24, 82), artifact_path, font=font(16, bold=False), fill=(145, 153, 165))
    image_box = (24, 120, size[0] - 24, size[1] - 80)
    if source_exists and source_readable and image is not None:
        fitted = ImageOps.fit(image, (image_box[2] - image_box[0], image_box[3] - image_box[1]), method=Image.Resampling.LANCZOS)
        card.paste(fitted, (image_box[0], image_box[1]))
        draw.rounded_rectangle(image_box, radius=18, outline=(255, 255, 255), width=1)
    else:
        draw_placeholder(draw, image_box, "Missing input" if not source_exists else "Unreadable input", note)
    draw.text((24, size[1] - 52), note, font=font(16, bold=False), fill=(210, 216, 224))
    return card


def render_contact_sheet(payload: Mapping[str, Any]) -> Any | None:
    if Image is None or ImageDraw is None:
        return None
    width, height = 1900, 1520
    canvas = Image.new("RGB", (width, height), (10, 13, 18))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=28, outline=(52, 58, 69), width=2)
    draw.text((32, 24), "APQ001 Action-Photo Composition Review", font=font(30, bold=True), fill=(249, 250, 252))
    draw.text(
        (32, 66),
        "Review-only comparison between the current 4:5 headshot bridge and APQ001 action-photo artifacts.",
        font=font(18, bold=False),
        fill=(188, 196, 207),
    )
    draw.text(
        (32, 98),
        "No approvals, no downloads, no file moves, no publish-ready state, and no renderer behavior change.",
        font=font(16, bold=False),
        fill=(160, 169, 181),
    )
    card_specs = [
        ("Current 4:5 headshot bridge", "Baseline to compare against", payload["current_headshot_path"], payload["current_headshot_present"], payload["current_headshot_readable"], payload["current_headshot_note"]),
        ("APQ001 quarantine candidate", "Review-only source asset", payload["candidate_path"], payload["candidate_present"], payload["candidate_readable"], payload["candidate_note"]),
        ("APQ001 quarantine sandbox", "Optional sandbox render", payload["sandbox_path"], payload["sandbox_present"], payload["sandbox_readable"], payload["sandbox_note"]),
        ("Prototype plan manifest", "Review-only composition direction", payload["prototype_plan_path"], payload["prototype_plan_present"], True, payload["prototype_plan_note"]),
    ]
    positions = [(30, 160), (970, 160), (30, 900), (970, 900)]
    sizes = [(900, 700), (900, 700), (900, 560), (900, 560)]
    for (title, subtitle, artifact_path, source_exists, source_readable, note), (x, y), size in zip(card_specs, positions, sizes, strict=True):
        card = make_sheet_card(
            title=title,
            subtitle=subtitle,
            artifact_path=artifact_path,
            source_exists=source_exists,
            source_readable=source_readable,
            image=payload["image_map"].get(artifact_path),
            note=note,
            size=size,
        )
        canvas.paste(card, (x, y))
    draw.text(
        (32, 1438),
        "Questions: headshot-feel reduction, face/action readability, crop notes, and whether the next lane should prototype action-photo-aware 4:5 layout.",
        font=font(16, bold=False),
        fill=(187, 195, 206),
    )
    return canvas


def build_intake_rows(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for question in payload["manual_questions"]:
        rows.append(
            {
                "question_id": question["question_id"],
                "review_focus": question["review_focus"],
                "question": question["question"],
                "decision_options": question["decision_options"],
                "manual_notes_prompt": question["manual_notes_prompt"],
                "current_headshot_path": payload["current_headshot_path"],
                "candidate_path": payload["candidate_path"],
                "sandbox_path": payload["sandbox_path"],
                "prototype_plan_path": payload["prototype_plan_path"],
                "recheck_plan_path": payload["recheck_plan_path"],
                "review_only": "true",
                "artifact_only": "true",
                "apq001_quarantine_only": "true",
                "asset_approved": "false",
                "approval_state_change": "false",
                "download_performed": "false",
                "asset_downloads": "false",
                "image_edits": "false",
                "move_files": "false",
                "publish_ready": "false",
                "publishing": "false",
                "renderer_behavior_change": "false",
            }
        )
    return rows


def render_composition_review(payload: Mapping[str, Any]) -> str:
    current_status = "present" if payload["current_headshot_present"] else "missing"
    candidate_status = "present" if payload["candidate_present"] else "missing"
    sandbox_status = "present" if payload["sandbox_present"] else "missing"
    return f"""# APQ001 Action-Photo Composition Review

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is review-only and artifact-only. It exists to make APQ001 action-photo planning visible again without approving, moving, downloading, or production-integrating the asset.

## What To Compare

- Current 4:5 headshot bridge: `{payload['current_headshot_path']}` ({current_status})
- APQ001 quarantine candidate: `{payload['candidate_path']}` ({candidate_status})
- APQ001 quarantine sandbox preview: `{payload['sandbox_path']}` ({sandbox_status})
- APQ001 prototype plan manifest: `{payload['prototype_plan_path']}` ({'present' if payload['prototype_plan_present'] else 'missing'})
- APQ001 renderer recheck plan: `{payload['recheck_plan_path']}` ({'present' if payload['recheck_plan_present'] else 'missing'})

## Manual Review Questions

{chr(10).join(f"- {item['question']}" for item in payload['manual_questions'])}

## Plain-English Review Guidance

- Compare the headshot bridge against APQ001 and ask whether the action-photo path finally reads like a live sports frame instead of a roster card.
- Check whether face, subject, and action context survive the crop cleanly enough for a renderer recheck.
- Write the smallest crop or layout notes needed before any renderer implementation lane.
- Choose whether the next lane should prototype an action-photo-aware 4:5 layout or hold APQ001 for more review.

## Optional Inputs

- Current headshot readable: `{payload['current_headshot_readable']}`
- APQ001 candidate readable: `{payload['candidate_readable']}`
- APQ001 sandbox readable: `{payload['sandbox_readable']}`
- Comparison sheet written: `{payload['comparison_contact_sheet_present']}`

## Guardrails

- review_only=true
- artifact_only=true
- apq001_quarantine_only=true
- asset_approved=false
- approval_state_change=false
- download_performed=false
- asset_downloads=false
- image_edits=false
- move_files=false
- publish_ready=false
- publishing=false
- renderer_behavior_change=false

## Next Step

Open the contact sheet first if it exists, then review the CSV rows and write only manual notes. Keep APQ001 in quarantine until a later lane is explicitly asked to prototype renderer behavior.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = output_rel(OUT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)

    current_headshot_path = input_path(Path(args.current_headshot) if args.current_headshot else CURRENT_HEADSHOT_REL)
    candidate_path = input_path(Path(args.candidate) if args.candidate else APQ001_CANDIDATE_REL)
    sandbox_path = input_path(Path(args.sandbox) if args.sandbox else APQ001_SANDBOX_REL)
    prototype_plan_path = input_path(Path(args.prototype_plan) if args.prototype_plan else APQ001_PROTO_PLAN_REL)
    recheck_plan_path = input_path(Path(args.recheck_plan) if args.recheck_plan else APQ001_RECHECK_PLAN_REL)
    manual_manifest_path = input_path(Path(args.manual_manifest) if args.manual_manifest else APQ001_MANUAL_RESULT_MANIFEST_REL)
    manual_report_path = input_path(Path(args.manual_report) if args.manual_report else APQ001_MANUAL_RESULT_REPORT_REL)
    sandbox_manifest_path = input_path(Path(args.sandbox_manifest) if args.sandbox_manifest else Path("apq001_quarantine_4x5_render_sandbox/manifest.json"))

    manual_manifest = read_json(manual_manifest_path)
    prototype_plan = read_json(prototype_plan_path)
    sandbox_manifest = read_json(sandbox_manifest_path)
    recheck_plan_text = read_text(recheck_plan_path)

    current_image, current_meta = try_open_image(current_headshot_path)
    candidate_image, candidate_meta = try_open_image(candidate_path)
    sandbox_image, sandbox_meta = try_open_image(sandbox_path)

    image_map: dict[str, Any] = {}
    if current_image is not None:
        image_map[current_headshot_path.as_posix()] = current_image
    if candidate_image is not None:
        image_map[candidate_path.as_posix()] = candidate_image
    if sandbox_image is not None:
        image_map[sandbox_path.as_posix()] = sandbox_image

    current_present = current_headshot_path.exists()
    candidate_present = candidate_path.exists()
    sandbox_present = sandbox_path.exists()
    current_readable = bool(current_meta.get("readable"))
    candidate_readable = bool(candidate_meta.get("readable"))
    sandbox_readable = bool(sandbox_meta.get("readable"))

    validations = [
        *validate_manifest(manual_manifest, manual_manifest_path),
        *validate_plan_manifest(prototype_plan, prototype_plan_path),
        *validate_sandbox_manifest(sandbox_manifest, sandbox_manifest_path),
    ]

    status = "apq001_action_photo_composition_review_ready"
    if not current_present:
        status = "apq001_action_photo_composition_review_blocked_missing_current_headshot"
        validations.append(
            {
                "source": current_headshot_path.as_posix(),
                "field": "current_headshot",
                "issue": "missing_required_current_headshot",
            }
        )
    elif not current_readable:
        status = "apq001_action_photo_composition_review_blocked_unreadable_current_headshot"
        validations.append(
            {
                "source": current_headshot_path.as_posix(),
                "field": "current_headshot",
                "issue": "unreadable_current_headshot",
            }
        )

    optional_missing_count = sum(1 for present in [candidate_present, sandbox_present] if not present)
    optional_unreadable_count = sum(
        1 for present, readable in [(candidate_present, candidate_readable), (sandbox_present, sandbox_readable)] if present and not readable
    )

    card_payload = {
        "current_headshot_path": current_headshot_path.as_posix(),
        "candidate_path": candidate_path.as_posix(),
        "sandbox_path": sandbox_path.as_posix(),
        "prototype_plan_path": prototype_plan_path.as_posix(),
        "recheck_plan_path": recheck_plan_path.as_posix(),
        "current_headshot_present": current_present,
        "candidate_present": candidate_present,
        "sandbox_present": sandbox_present,
        "prototype_plan_present": prototype_plan_path.exists(),
        "recheck_plan_present": recheck_plan_path.exists(),
        "current_headshot_readable": current_readable,
        "candidate_readable": candidate_readable,
        "sandbox_readable": sandbox_readable,
        "comparison_contact_sheet_present": False,
        "current_headshot_note": "Current bridge to compare against.",
        "candidate_note": "Review-only quarantine candidate; keep it in quarantine.",
        "sandbox_note": "Optional sandbox preview if present; otherwise a placeholder will show the gap.",
        "prototype_plan_note": "Prototype plan manifest for renderer-direction context.",
        "manual_questions": MANUAL_QUESTIONS,
        "image_map": image_map,
    }

    contact_sheet = render_contact_sheet(card_payload)
    comparison_contact_sheet_present = False
    if contact_sheet is not None:
        contact_sheet_path = output_rel(OUT_CONTACT_SHEET_REL)
        contact_sheet.save(contact_sheet_path)
        comparison_contact_sheet_present = contact_sheet_path.exists()
    else:
        contact_sheet_path = output_rel(OUT_CONTACT_SHEET_REL)

    card_payload["comparison_contact_sheet_present"] = comparison_contact_sheet_present
    intake_rows = build_intake_rows(card_payload)

    write_csv(
        output_rel(OUT_INTAKE_REL),
        intake_rows,
        [
            "question_id",
            "review_focus",
            "question",
            "decision_options",
            "manual_notes_prompt",
            "current_headshot_path",
            "candidate_path",
            "sandbox_path",
            "prototype_plan_path",
            "recheck_plan_path",
            "review_only",
            "artifact_only",
            "apq001_quarantine_only",
            "asset_approved",
            "approval_state_change",
            "download_performed",
            "asset_downloads",
            "image_edits",
            "move_files",
            "publish_ready",
            "publishing",
            "renderer_behavior_change",
        ],
    )

    payload = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": status,
        "output_dir": out_dir.as_posix(),
        "comparison_contact_sheet_path": contact_sheet_path.as_posix(),
        "comparison_contact_sheet_present": comparison_contact_sheet_present,
        "composition_review_path": output_rel(OUT_COMPOSITION_REL).as_posix(),
        "manual_composition_intake_path": output_rel(OUT_INTAKE_REL).as_posix(),
        "current_headshot_path": current_headshot_path.as_posix(),
        "current_headshot_present": current_present,
        "current_headshot_readable": current_readable,
        "candidate_path": candidate_path.as_posix(),
        "candidate_present": candidate_present,
        "candidate_readable": candidate_readable,
        "sandbox_path": sandbox_path.as_posix(),
        "sandbox_present": sandbox_present,
        "sandbox_readable": sandbox_readable,
        "prototype_plan_path": prototype_plan_path.as_posix(),
        "prototype_plan_present": prototype_plan_path.exists(),
        "recheck_plan_path": recheck_plan_path.as_posix(),
        "recheck_plan_present": recheck_plan_path.exists(),
        "manual_manifest_path": manual_manifest_path.as_posix(),
        "manual_manifest_present": manual_manifest_path.exists(),
        "manual_report_path": manual_report_path.as_posix(),
        "manual_report_present": manual_report_path.exists(),
        "sandbox_manifest_path": sandbox_manifest_path.as_posix(),
        "sandbox_manifest_present": sandbox_manifest_path.exists(),
        "manual_questions": MANUAL_QUESTIONS,
        "manual_question_count": len(MANUAL_QUESTIONS),
        "manual_intake_rows": len(intake_rows),
        "optional_source_missing_count": optional_missing_count,
        "optional_source_unreadable_count": optional_unreadable_count,
        "validation_issue_count": len(validations),
        "validation_issues": validations,
        **guardrail_values(),
    }

    write_json(output_rel(OUT_MANIFEST_REL), payload, sort_keys=True)
    write_text(output_rel(OUT_COMPOSITION_REL), render_composition_review(payload), normalize=strip_volatile_markdown_lines)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only APQ001 action-photo composition comparison packet.")
    parser.add_argument("--current-headshot", default=CURRENT_HEADSHOT_REL.as_posix())
    parser.add_argument("--candidate", default=APQ001_CANDIDATE_REL.as_posix())
    parser.add_argument("--sandbox", default=APQ001_SANDBOX_REL.as_posix())
    parser.add_argument("--prototype-plan", default=APQ001_PROTO_PLAN_REL.as_posix())
    parser.add_argument("--recheck-plan", default=APQ001_RECHECK_PLAN_REL.as_posix())
    parser.add_argument("--manual-manifest", default=APQ001_MANUAL_RESULT_MANIFEST_REL.as_posix())
    parser.add_argument("--manual-report", default=APQ001_MANUAL_RESULT_REPORT_REL.as_posix())
    parser.add_argument("--sandbox-manifest", default="apq001_quarantine_4x5_render_sandbox/manifest.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "comparison_contact_sheet_present": payload["comparison_contact_sheet_present"],
                "validation_issue_count": payload["validation_issue_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["validation_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
