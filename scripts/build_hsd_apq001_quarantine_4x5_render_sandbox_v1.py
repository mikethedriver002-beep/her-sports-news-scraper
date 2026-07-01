from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, strip_volatile_markdown_lines, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, PngImagePlugin, UnidentifiedImageError
except Exception:  # pragma: no cover - handled at runtime
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]
    PngImagePlugin = None  # type: ignore[assignment]
    UnidentifiedImageError = Exception  # type: ignore[assignment]


VERSION = "hsd-apq001-quarantine-4x5-render-sandbox-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apq001_quarantine_4x5_render_sandbox_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("apq001_quarantine_4x5_render_sandbox")
OUT_MANIFEST_REL = OUT_DIR_REL / "manifest.json"
OUT_REPORT_REL = OUT_DIR_REL / "report.md"
OUT_IMAGE_REL = OUT_DIR_REL / "prototype_ig_feed_4x5.png"
SOURCE_CANDIDATE_REL = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
    "apq001_review_only_candidate.jpg"
)
REFERENCE_RENDER_REL = Path("render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png")
CANVAS_SIZE = (1080, 1350)
WATERMARK_TEXT = "PROTOTYPE ONLY - APQ001 QUARANTINE LAYER"

FALSE_GUARDRAIL_FIELDS = [
    "review_only",
    "artifact_only",
    "image_edits",
    "asset_downloads",
    "new_downloads",
    "approval_state_change",
    "approved_marker_writes",
    "headshot_writes",
    "renderer_behavior_change",
    "publish_ready",
    "publishing",
    "move_files",
    "auto_publish",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "ready", "pass"}


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


def find_input(path: Path) -> Path | None:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_font(size: int, bold: bool = True):
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


def measure(draw: Any, text: str, font: Any) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def fit_source(source_path: Path, reference_path: Path | None) -> tuple[dict[str, Any], Any | None, str | None]:
    if Image is None or ImageOps is None:
        return {}, None, "pillow_unavailable"
    try:
        with Image.open(source_path) as source:
            image = source.convert("RGB")
    except FileNotFoundError:
        return {}, None, "missing_source"
    except (UnidentifiedImageError, OSError):
        return {}, None, "unreadable_source"

    if reference_path and reference_path.exists():
        reference_present = True
    else:
        reference_present = False

    canvas = ImageOps.fit(image, CANVAS_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
    canvas = canvas.convert("RGBA")
    return {"source_size": list(image.size), "reference_present": reference_present}, canvas, None


def add_vignette(canvas: Any) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = canvas.size
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Dark scrim and soft edge falloff to keep the action-photo read legible.
    draw.rectangle((0, 0, width, height), fill=(5, 8, 12, 118))
    for inset, alpha in ((0, 96), (42, 72), (86, 48), (132, 28)):
        draw.rectangle((inset, inset, width - inset, height - inset), outline=(0, 0, 0, alpha), width=2)

    canvas.alpha_composite(overlay)


def add_score_rail(canvas: Any) -> None:
    if ImageDraw is None:
        return
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size

    # Open typography instead of a boxed roster-card panel.
    top_label_font = load_font(30, bold=True)
    score_font = load_font(132, bold=True)
    period_font = load_font(34, bold=True)
    small_font = load_font(24, bold=False)

    draw.text((72, 74), "QUARANTINE PROTOTYPE", font=top_label_font, fill=(236, 240, 245, 240))
    draw.text((72, 112), "ACTION PHOTO 4:5 SANDBOX", font=small_font, fill=(205, 212, 221, 220))
    draw.text((72, 186), "82", font=score_font, fill=(255, 245, 230, 255))
    draw.text((310, 212), "•", font=period_font, fill=(235, 238, 240, 235))
    draw.text((345, 186), "79", font=score_font, fill=(235, 238, 240, 225))
    draw.text((72, 340), "OPEN SCORE TYPOGRAPHY", font=small_font, fill=(220, 226, 233, 195))
    draw.line((72, 384, width - 72, 384), fill=(255, 255, 255, 48), width=2)


def add_lower_stat_strip(canvas: Any) -> None:
    if ImageDraw is None:
        return
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    strip_top = height - 202
    draw.rectangle((0, strip_top, width, height), fill=(10, 14, 20, 168))
    draw.line((72, strip_top + 26, width - 72, strip_top + 26), fill=(255, 255, 255, 42), width=1)

    label_font = load_font(24, bold=True)
    stat_font = load_font(31, bold=False)
    small_font = load_font(20, bold=False)

    draw.text((72, strip_top + 40), "APQ001 QUARANTINE LAYER", font=label_font, fill=(247, 247, 244, 248))
    draw.text((72, strip_top + 78), "PTS 22 • REB 7 • AST 5 • TOV 2", font=stat_font, fill=(232, 238, 244, 232))
    draw.text((72, strip_top + 124), "RAW EDITORIAL STUDY ONLY", font=small_font, fill=(203, 211, 221, 210))


def add_watermark(canvas: Any) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = canvas.size
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    watermark_font = load_font(28, bold=True)
    tiny_font = load_font(20, bold=True)

    # Visible burn-in repeated across the image.
    for row_y in range(72, height - 220, 112):
        offset = 42 if (row_y // 112) % 2 else 0
        for x in range(-20, width + 240, 340):
            draw.text((x + offset, row_y), WATERMARK_TEXT, font=watermark_font, fill=(255, 255, 255, 42))

    draw.rounded_rectangle((56, 58, width - 56, 132), radius=24, outline=(255, 255, 255, 65), width=2, fill=(0, 0, 0, 0))
    draw.text((86, 80), WATERMARK_TEXT, font=tiny_font, fill=(255, 255, 255, 190))
    draw.rectangle((56, height - 150, width - 56, height - 56), outline=(255, 255, 255, 55), width=2)
    draw.text((88, height - 126), WATERMARK_TEXT, font=tiny_font, fill=(255, 255, 255, 176))

    canvas.alpha_composite(overlay)


def render_canvas(source_path: Path, reference_path: Path | None) -> tuple[Any | None, dict[str, Any], str | None]:
    base_info, canvas, issue = fit_source(source_path, reference_path)
    if issue or canvas is None:
        return None, base_info, issue
    add_vignette(canvas)
    add_score_rail(canvas)
    add_lower_stat_strip(canvas)
    add_watermark(canvas)
    canvas.info["burn_in_label"] = WATERMARK_TEXT
    canvas.info["handoff_status"] = "quarantine_review_lock"
    canvas.info["review_only"] = "true"
    canvas.info["artifact_only"] = "true"
    canvas.info["image_edits"] = "false"
    canvas.info["asset_downloads"] = "false"
    canvas.info["publish_ready"] = "false"
    canvas.info["publishing"] = "false"
    return canvas, base_info, None


def render_report(payload: dict[str, Any]) -> str:
    if payload["status"] != "apq001_quarantine_4x5_render_sandbox_ready":
        return f"""# APQ001 Quarantine 4x5 Render Sandbox

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This sandbox is blocked because the APQ001 quarantine source image could not be found or opened.

## Missing Input

- Required source candidate: `{payload['source_candidate_path']}`

## Next Step

Provide the exact missing file path if the candidate was moved, renamed, or not checked out in this worktree. Do not approve anything, do not download anything, and do not treat this as a production renderer change.
"""

    return f"""# APQ001 Quarantine 4x5 Render Sandbox

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This is a review-only quarantine sandbox. It reads the APQ001 quarantine source image as input and writes a new 4:5 prototype PNG only in the sandbox output directory. It does not approve the asset, does not move files, does not create `.approved` markers, does not publish, and does not change production renderer behavior.

## Output

- Sandbox PNG: `{payload['output_png_path']}`
- Handoff status: `{payload['handoff_status']}`
- Burn-in label: `{payload['burn_in_label']}`
- Reference render present: `{payload['reference_render_present']}`

## Guardrails

- review_only=true
- artifact_only=true
- image_edits=false
- asset_downloads=false
- new_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- headshot_writes=false
- renderer_behavior_change=false
- publish_ready=false
- publishing=false
- move_files=false
- auto_publish=false

## Prototype Notes

- Full-bleed action-photo crop with a dark scrim and vignette.
- Open score typography instead of a boxed roster-card layout.
- Lightweight lower stat strip with middle dots.
- Visible burn-in watermark: `PROTOTYPE ONLY - APQ001 QUARANTINE LAYER`.
"""


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    source_path = find_input(Path(args.source_candidate)) or Path(args.source_candidate)
    reference_path = find_input(Path(args.reference_render)) if args.reference_render else None
    out_dir = output_rel(OUT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "source_candidate_path": Path(args.source_candidate).as_posix(),
        "reference_render_path": Path(args.reference_render).as_posix(),
        "output_dir": str(out_dir),
        "output_png_path": str(output_rel(OUT_IMAGE_REL)),
        "report_path": str(output_rel(OUT_REPORT_REL)),
        "handoff_status": "quarantine_review_lock",
        "burn_in_label": WATERMARK_TEXT,
        "review_only": True,
        "artifact_only": True,
        "image_edits": False,
        "asset_downloads": False,
        "new_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "headshot_writes": False,
        "renderer_behavior_change": False,
        "publish_ready": False,
        "publishing": False,
        "move_files": False,
        "auto_publish": False,
        "reference_render_present": bool(reference_path and reference_path.exists()),
    }

    if not source_path.exists():
        manifest.update(
            {
                "status": "apq001_quarantine_4x5_render_sandbox_blocked_missing_source",
                "source_candidate_present": False,
                "source_candidate_readable": False,
                "source_candidate_sha256": "",
                "source_size": [],
                "validation_issue": "missing_source",
                "validation_issue_count": 1,
            }
        )
        write_json(output_rel(OUT_MANIFEST_REL), manifest, sort_keys=True)
        write_text(output_rel(OUT_REPORT_REL), render_report(manifest), normalize=strip_volatile_markdown_lines)
        return manifest

    canvas, base_info, issue = render_canvas(source_path, reference_path)
    if issue or canvas is None:
        validation_issue = "unreadable_source" if issue == "unreadable_source" else "pillow_unavailable" if issue == "pillow_unavailable" else "missing_source"
        manifest.update(
            {
                "status": f"apq001_quarantine_4x5_render_sandbox_blocked_{validation_issue}",
                "source_candidate_present": True,
                "source_candidate_readable": False,
                "source_candidate_sha256": sha256_file(source_path) if source_path.exists() else "",
                "source_size": base_info.get("source_size", []),
                "validation_issue": validation_issue,
                "validation_issue_count": 1,
            }
        )
        write_json(output_rel(OUT_MANIFEST_REL), manifest, sort_keys=True)
        write_text(output_rel(OUT_REPORT_REL), render_report(manifest), normalize=strip_volatile_markdown_lines)
        return manifest

    png_info = PngImagePlugin.PngInfo() if PngImagePlugin is not None else None
    metadata_items = {
        "version": VERSION,
        "handoff_status": "quarantine_review_lock",
        "burn_in_label": WATERMARK_TEXT,
        "review_only": "true",
        "artifact_only": "true",
        "image_edits": "false",
        "asset_downloads": "false",
        "publish_ready": "false",
        "publishing": "false",
        "move_files": "false",
    }
    if png_info is not None:
        for key, value in metadata_items.items():
            png_info.add_text(key, str(value))

    output_png = output_rel(OUT_IMAGE_REL)
    canvas.save(output_png, pnginfo=png_info)
    manifest.update(
        {
            "status": "apq001_quarantine_4x5_render_sandbox_ready",
            "source_candidate_present": True,
            "source_candidate_readable": True,
            "source_candidate_sha256": sha256_file(source_path),
            "source_size": base_info.get("source_size", []),
            "render_size": list(CANVAS_SIZE),
            "validation_issue": "",
            "validation_issue_count": 0,
            "png_metadata_keys": sorted(metadata_items.keys()),
        }
    )
    write_json(output_rel(OUT_MANIFEST_REL), manifest, sort_keys=True)
    write_text(output_rel(OUT_REPORT_REL), render_report(manifest), normalize=strip_volatile_markdown_lines)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an APQ001 quarantine-only 4:5 render sandbox.")
    parser.add_argument(
        "--source-candidate",
        default=SOURCE_CANDIDATE_REL.as_posix(),
        help="Quarantine source image path to read in review-only mode.",
    )
    parser.add_argument(
        "--reference-render",
        default=REFERENCE_RENDER_REL.as_posix(),
        help="Optional review-only reference render path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "output_png_path": payload["output_png_path"],
                "validation_issue_count": payload["validation_issue_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["validation_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
