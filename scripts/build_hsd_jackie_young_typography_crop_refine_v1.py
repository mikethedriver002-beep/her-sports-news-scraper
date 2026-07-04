from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts import build_hsd_apcs114_visual_upgrade_v2 as base

try:
    from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageChops = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageEnhance = None  # type: ignore[assignment]
    ImageFilter = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-wnba-apcs039-typography-crop-refine-v1-review-only"
GENERATED_BY = "scripts/build_hsd_jackie_young_typography_crop_refine_v1.py"
DEFAULT_SOURCE_IMAGE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_apcs039_typography_crop_refine_v1")
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
CANVAS = {"width": 1080, "height": 1350}
REVIEW_ONLY_BURN_IN = "REVIEW ONLY - APCS039"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "headshot_writes": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
}

CSV_FIELDS = [
    "variant_id",
    "variant_name",
    "render_path",
    "crop_strategy",
    "typography_treatment",
    "visual_strength",
    "known_limit",
    "operator_decision",
    "operator_notes",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_source_image(explicit: str | None = None) -> Path:
    raw = Path(explicit) if explicit else DEFAULT_SOURCE_IMAGE
    return raw if raw.is_absolute() else repo_root() / raw


def load_font(size: int, *, bold: bool = True) -> Any:
    return base.load_font(size, bold=bold)


def sha256_file(path: Path) -> str:
    return base.sha256_file(path)


def png_dimensions(path: Path) -> list[int]:
    if Image is None:
        return []
    with Image.open(path) as image:
        return [int(image.size[0]), int(image.size[1])]


def fit_crop(source_image: Path, center: list[float], zoom: float) -> Any:
    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow is required for APCS039 crop refinement")
    with Image.open(source_image) as source:
        rgb = source.convert("RGB")
        width, height = rgb.size
        target_ratio = CANVAS["width"] / CANVAS["height"]
        if width / height > target_ratio:
            base_height = height
            base_width = int(round(height * target_ratio))
        else:
            base_width = width
            base_height = int(round(width / target_ratio))
        zoom = max(1.0, float(zoom))
        crop_width = max(1, int(round(base_width / zoom)))
        crop_height = max(1, int(round(base_height / zoom)))
        center_x = int(round(width * float(center[0])))
        center_y = int(round(height * float(center[1])))
        left = max(0, min(width - crop_width, center_x - crop_width // 2))
        top = max(0, min(height - crop_height, center_y - crop_height // 2))
        crop = rgb.crop((left, top, left + crop_width, top + crop_height))
        fitted = crop.resize((CANVAS["width"], CANVAS["height"]), getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1))
        return fitted


def apply_grade(image: Any, grade: dict[str, Any]) -> Any:
    if Image is None or ImageEnhance is None or ImageOps is None:
        raise RuntimeError("Pillow enhancements are required for APCS039 visual refinement")
    graded = ImageOps.autocontrast(image.convert("RGB"), cutoff=1)
    graded = ImageEnhance.Brightness(graded).enhance(float(grade.get("brightness", 0.76)))
    graded = ImageEnhance.Contrast(graded).enhance(float(grade.get("contrast", 1.22)))
    graded = ImageEnhance.Color(graded).enhance(float(grade.get("color", 0.93)))
    graded = ImageEnhance.Sharpness(graded).enhance(float(grade.get("sharpness", 1.08)))

    width, height = graded.size
    vignette = float(grade.get("vignette", 0.0))
    if vignette > 0:
        mask = Image.new("L", (width, height), 0)
        center_x = width * 0.56
        center_y = height * 0.44
        max_distance = ((max(center_x, width - center_x) ** 2) + (max(center_y, height - center_y) ** 2)) ** 0.5
        pixels = []
        for y in range(height):
            for x in range(width):
                distance = (((x - center_x) ** 2) + ((y - center_y) ** 2)) ** 0.5 / max_distance
                strength = max(0.0, min(1.0, (distance - 0.43) / 0.57))
                pixels.append(int(255 * vignette * strength))
        mask.putdata(pixels)
        dark = Image.new("RGB", (width, height), (8, 10, 14))
        graded = Image.composite(dark, graded, mask)

    top_scrim = float(grade.get("top_scrim", 0.0))
    if top_scrim > 0:
        scrim = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        alpha = Image.new("L", (width, height), 0)
        alpha_pixels: list[int] = []
        fade_height = max(1, int(height * 0.36))
        for y in range(height):
            local = max(0.0, 1.0 - (y / fade_height))
            alpha_pixels.extend([int(255 * top_scrim * local)] * width)
        alpha.putdata(alpha_pixels)
        scrim.putalpha(alpha)
        graded = Image.alpha_composite(graded.convert("RGBA"), scrim).convert("RGB")

    return graded


def make_text_shadow(draw: Any, position: tuple[int, int], text: str, font: Any, fill: tuple[int, int, int], shadow: tuple[int, int, int], offset: tuple[int, int] = (2, 2)) -> None:
    x, y = position
    draw.text((x + offset[0], y + offset[1]), text, fill=shadow, font=font)
    draw.text((x, y), text, fill=fill, font=font)


def text_size(draw: Any, text: str, font: Any) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_right_aligned(draw: Any, right_x: int, y: int, text: str, font: Any, fill: tuple[int, int, int], shadow: tuple[int, int, int], offset: tuple[int, int] = (2, 2)) -> int:
    width, height = text_size(draw, text, font)
    make_text_shadow(draw, (right_x - width, y), text, font, fill, shadow, offset=offset)
    return height


def draw_centered(draw: Any, center_x: int, y: int, text: str, font: Any, fill: tuple[int, int, int], shadow: tuple[int, int, int], offset: tuple[int, int] = (2, 2)) -> int:
    width, height = text_size(draw, text, font)
    make_text_shadow(draw, (center_x - width // 2, y), text, font, fill, shadow, offset=offset)
    return height


def draw_left_block(draw: Any, x: int, y: int, lines: list[dict[str, Any]]) -> int:
    cursor_y = y
    for line in lines:
        font = line["font"]
        fill = line["fill"]
        shadow = line["shadow"]
        offset = line.get("offset", (2, 2))
        text = str(line["text"])
        draw.text((x + offset[0], cursor_y + offset[1]), text, fill=shadow, font=font)
        draw.text((x, cursor_y), text, fill=fill, font=font)
        cursor_y += text_size(draw, text, font)[1] + int(line.get("gap", 0))
    return cursor_y - y


def add_gradient_scrim(base_image: Any, side: str, strength: float, width_ratio: float) -> Any:
    if Image is None:
        raise RuntimeError("Pillow is required for APCS039 overlays")
    width, height = base_image.size
    band_width = int(width * width_ratio)
    alpha = max(0, min(255, int(255 * strength)))
    if band_width <= 0 or alpha <= 0:
        return base_image.convert("RGBA")

    if side in {"left", "right"}:
        grad = Image.linear_gradient("L").resize((band_width, height))
        if side == "right":
            grad = ImageOps.mirror(grad)
        mask = Image.new("L", (width, height), 0)
        mask.paste(grad, (0 if side == "left" else width - band_width, 0))
    else:
        grad = Image.linear_gradient("L").rotate(90, expand=True).resize((width, band_width))
        if side == "bottom":
            grad = ImageOps.flip(grad)
        mask = Image.new("L", (width, height), 0)
        mask.paste(grad, (0, 0 if side == "top" else height - band_width))

    mask = ImageEnhance.Brightness(mask).enhance(alpha / 255.0)
    band = Image.new("RGBA", (width, height), (8, 10, 14, 0))
    band.putalpha(mask)
    return Image.alpha_composite(base_image.convert("RGBA"), band)


def draw_accent_line(draw: Any, x: int, y: int, width: int, color: tuple[int, int, int], alpha: int = 255) -> None:
    draw.rounded_rectangle((x, y, x + width, y + 8), radius=4, fill=(*color, alpha))


def build_variant_specs() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "variant_01_photo_anchor",
            "variant_name": "Score-Ready Photo Anchor",
            "output_name": "variant_01_photo_anchor.png",
            "crop_strategy": "apcs039_center_right_photo_anchor_crop",
            "crop_center": [0.54, 0.48],
            "crop_zoom": 1.06,
            "grade": {"brightness": 0.74, "contrast": 1.22, "color": 0.94, "sharpness": 1.10, "vignette": 0.26, "top_scrim": 0.10},
            "scrim_side": "right",
            "scrim_strength": 0.22,
            "scrim_width_ratio": 0.26,
            "headline": "JACKIE\nYOUNG",
            "kicker": "FINAL / LAS VEGAS",
            "detail": "APCS039 REVIEW ONLY",
            "accent": [236, 92, 109],
            "typography_treatment": "hero_stack_right_scrim",
            "visual_strength": "best_score_ready_route_with_strong_subject_read",
            "known_limit": "review_only_official_gallery_candidate_not_asset_approved",
            "text_box": {"x": 658, "y": 128, "w": 332, "h": 920},
            "headline_size": 108,
            "kicker_size": 28,
            "detail_size": 24,
            "headline_align": "right",
            "accent_y": 908,
            "text_top": 122,
            "footer": "REVIEW ONLY",
        },
        {
            "variant_id": "variant_02_face_first_lede",
            "variant_name": "Face-First Lede",
            "output_name": "variant_02_face_first_lede.png",
            "crop_strategy": "apcs039_face_led_tighter_crop",
            "crop_center": [0.50, 0.43],
            "crop_zoom": 1.12,
            "grade": {"brightness": 0.76, "contrast": 1.24, "color": 0.95, "sharpness": 1.12, "vignette": 0.30, "top_scrim": 0.08},
            "scrim_side": "top",
            "scrim_strength": 0.14,
            "scrim_width_ratio": 0.18,
            "headline": "FACE\nFIRST",
            "kicker": "JACKIE YOUNG / WNBA",
            "detail": "LAS VEGAS ACES",
            "accent": [244, 204, 121],
            "typography_treatment": "lede_stack_with_open_bottom",
            "visual_strength": "tightest_readable_hero_crop",
            "known_limit": "ball_is_close_to_edge_by_design",
            "text_box": {"x": 72, "y": 90, "w": 380, "h": 470},
            "headline_size": 100,
            "kicker_size": 26,
            "detail_size": 24,
            "headline_align": "left",
            "accent_y": 522,
            "text_top": 82,
            "footer": "APCS039",
        },
        {
            "variant_id": "variant_03_ball_side_action",
            "variant_name": "Ball-Side Action",
            "output_name": "variant_03_ball_side_action.png",
            "crop_strategy": "apcs039_right_ball_keep_crop",
            "crop_center": [0.58, 0.49],
            "crop_zoom": 1.09,
            "grade": {"brightness": 0.75, "contrast": 1.26, "color": 0.94, "sharpness": 1.11, "vignette": 0.28, "top_scrim": 0.12},
            "scrim_side": "left",
            "scrim_strength": 0.20,
            "scrim_width_ratio": 0.22,
            "headline": "LAS\nVEGAS",
            "kicker": "ACES / JACKIE YOUNG",
            "detail": "REVIEW ONLY / APCS039",
            "accent": [215, 52, 76],
            "typography_treatment": "left_column_typography_with_open_action",
            "visual_strength": "best_ball_and_arm_preservation",
            "known_limit": "tighter_crop_requires_manual_read_check",
            "text_box": {"x": 72, "y": 100, "w": 350, "h": 780},
            "headline_size": 96,
            "kicker_size": 26,
            "detail_size": 23,
            "headline_align": "left",
            "accent_y": 782,
            "text_top": 92,
            "footer": "WNBA",
        },
        {
            "variant_id": "variant_04_clean_story_stack",
            "variant_name": "Clean Editorial Stack",
            "output_name": "variant_04_clean_story_stack.png",
            "crop_strategy": "apcs039_clean_story_stack_crop",
            "crop_center": [0.52, 0.47],
            "crop_zoom": 1.02,
            "grade": {"brightness": 0.78, "contrast": 1.20, "color": 0.93, "sharpness": 1.08, "vignette": 0.24, "top_scrim": 0.08},
            "scrim_side": "bottom",
            "scrim_strength": 0.14,
            "scrim_width_ratio": 0.16,
            "headline": "FINAL",
            "kicker": "JACKIE YOUNG",
            "detail": "LAS VEGAS ACES / APCS039",
            "accent": [232, 198, 141],
            "typography_treatment": "calm_story_header_with_footer_tag",
            "visual_strength": "cleanest_editorial_route",
            "known_limit": "most_conservative_read_for_future_context_use",
            "text_box": {"x": 84, "y": 82, "w": 376, "h": 270},
            "headline_size": 104,
            "kicker_size": 26,
            "detail_size": 22,
            "headline_align": "left",
            "accent_y": 304,
            "text_top": 82,
            "footer": "REVIEW ONLY",
        },
    ]


def render_variant(source_image: Path, output_path: Path, spec: dict[str, Any]) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for APCS039 visual refinement renders")

    base_crop = fit_crop(source_image, list(spec["crop_center"]), float(spec["crop_zoom"]))
    graded = apply_grade(base_crop, dict(spec.get("grade", {})))
    layered = add_gradient_scrim(graded, str(spec.get("scrim_side", "right")), float(spec.get("scrim_strength", 0.3)), float(spec.get("scrim_width_ratio", 0.28)))
    draw = ImageDraw.Draw(layered, "RGBA")

    width, height = layered.size
    box = spec.get("text_box", {"x": 72, "y": 72, "w": 360, "h": 500})
    accent = tuple(spec.get("accent", [230, 92, 110]))
    title_color = (248, 248, 248)
    support_color = (214, 220, 232)
    detail_color = (190, 196, 210)
    shadow = (8, 8, 12)
    headline_font = load_font(int(spec.get("headline_size", 100)), bold=True)
    kicker_font = load_font(int(spec.get("kicker_size", 24)), bold=True)
    detail_font = load_font(int(spec.get("detail_size", 22)), bold=False)
    footer_font = load_font(18, bold=True)

    # Keep the subject dominant, and make the typography read like a sports editorial page rather than a framed mockup.
    if spec["variant_id"] == "variant_01_photo_anchor":
        x = int(box["x"])
        y = int(box["y"])
        draw_left_block(
            draw,
            x,
            y,
            [
                {"text": spec["kicker"], "font": kicker_font, "fill": support_color, "shadow": shadow, "gap": 22},
                {"text": spec["headline"].split("\n")[0], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 6},
                {"text": spec["headline"].split("\n")[1], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 14},
                {"text": spec["detail"], "font": detail_font, "fill": support_color, "shadow": shadow, "gap": 0},
            ],
        )
        draw_accent_line(draw, x, int(spec["accent_y"]), 250, accent, 220)
        draw.text((x, height - 66), spec["footer"], fill=(230, 232, 238, 220), font=footer_font)
    elif spec["variant_id"] == "variant_02_face_first_lede":
        x = int(box["x"])
        y = int(box["y"])
        draw_left_block(
            draw,
            x,
            y,
            [
                {"text": spec["kicker"], "font": kicker_font, "fill": support_color, "shadow": shadow, "gap": 18},
                {"text": spec["headline"].split("\n")[0], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 4},
                {"text": spec["headline"].split("\n")[1], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 18},
                {"text": spec["detail"], "font": detail_font, "fill": support_color, "shadow": shadow, "gap": 0},
            ],
        )
        draw_accent_line(draw, x, int(spec["accent_y"]), 210, accent, 205)
        draw.text((x, height - 64), spec["footer"], fill=(230, 232, 238, 210), font=footer_font)
    elif spec["variant_id"] == "variant_03_ball_side_action":
        x = int(box["x"])
        y = int(box["y"])
        draw_left_block(
            draw,
            x,
            y,
            [
                {"text": spec["kicker"], "font": kicker_font, "fill": support_color, "shadow": shadow, "gap": 20},
                {"text": spec["headline"].split("\n")[0], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 4},
                {"text": spec["headline"].split("\n")[1], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 16},
                {"text": spec["detail"], "font": detail_font, "fill": support_color, "shadow": shadow, "gap": 0},
            ],
        )
        draw_accent_line(draw, x, int(spec["accent_y"]), 228, accent, 210)
        draw.text((x, height - 64), spec["footer"], fill=(230, 232, 238, 210), font=footer_font)
    else:
        x = int(box["x"])
        y = int(box["y"])
        draw_left_block(
            draw,
            x,
            y,
            [
                {"text": spec["kicker"], "font": kicker_font, "fill": support_color, "shadow": shadow, "gap": 18},
                {"text": spec["headline"], "font": headline_font, "fill": title_color, "shadow": shadow, "gap": 18},
                {"text": spec["detail"], "font": detail_font, "fill": support_color, "shadow": shadow, "gap": 0},
            ],
        )
        draw_accent_line(draw, x, int(spec["accent_y"]), 176, accent, 200)
        draw.text((x, height - 64), spec["footer"], fill=(230, 232, 238, 210), font=footer_font)

    # A tiny data tag keeps the packet readable while avoiding the heavy compliance copy from the earlier lane.
    tag = "APCS039 / JACKIE YOUNG"
    tag_font = load_font(16, bold=False)
    tag_w, _ = text_size(draw, tag, tag_font)
    draw.text((width - tag_w - 32, height - 42), tag, fill=(228, 232, 239, 180), font=tag_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    layered.convert("RGB").save(output_path, "PNG")


def build_contact_sheet(output_dir: Path, variants: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for the APCS039 contact sheet")
    sheet = Image.new("RGB", (1080, 1350), (10, 12, 18))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(24, bold=True)
    small_font = load_font(16, bold=False)
    sub_font = load_font(18, bold=True)
    draw.text((36, 28), "APCS039 TYPOGRAPHY + CROP REFINE V1", fill=(245, 246, 250), font=title_font)
    draw.text((36, 62), "Review-only follow-up from the merged Jackie Young lane. No downloads, no approvals, no publish-ready state.", fill=(190, 197, 210), font=small_font)

    positions = [
        (36, 112),
        (552, 112),
        (36, 738),
        (552, 738),
    ]
    for (x, y), spec in zip(positions, variants):
        with Image.open(spec["output_png_path"]) as image:
            thumb = ImageOps.fit(image.convert("RGB"), (492, 560), method=getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1))
        sheet.paste(thumb, (x, y))
        draw.text((x, y + 572), spec["variant_name"], fill=(244, 245, 248), font=sub_font)
        draw.text((x, y + 596), spec["visual_strength"], fill=(175, 183, 196), font=small_font)

    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path, "PNG")
    return path


def build_manual_rows(variant_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in variant_rows:
        rows.append(
            {
                "variant_id": row["variant_id"],
                "variant_name": row["variant_name"],
                "render_path": row["output_png_path"],
                "crop_strategy": row["crop_strategy"],
                "typography_treatment": row["typography_treatment"],
                "visual_strength": row["visual_strength"],
                "known_limit": row["known_limit"],
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return rows


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            f"| `{row['variant_id']}` | {row['variant_name']} | {row['crop_strategy']} | {row['typography_treatment']} | {row['known_limit']} |"
            for row in manifest["variant_rows"]
        ]
    )
    return f"""# APCS039 Typography Crop Refine V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet tightens the Jackie Young review-only APCS039 candidate into four 1080x1350 editorial variants with better crop control, less compliance text, and stronger WNBA typography. It intentionally avoids the boxed-stage / gray-floor look from the earlier lane.

## Visual Read

- Best overall route: `variant_04_clean_story_stack`, because it keeps the athlete dominant, stays the farthest from mockup language, and reads most like a flat editorial sports frame.
- Score-ready comparison: `variant_01_photo_anchor`, because it still gives the strongest final-score style headline treatment without pushing back into the boxed-stage family.
- Tightest hero crop: `variant_02_face_first_lede`, because it pushes closest to Jackie's face and expression while keeping the frame editorial rather than staged.
- Best action preservation: `variant_03_ball_side_action`, because it protects the right-side ball read and keeps the subject moving across open space.
- Cleanest newsroom tone: `variant_04_clean_story_stack`, because it trims the copy down to a sparse story stack and stays the farthest from mockup language.
- Blender overlay note: not used here; the source image already carries the frame better than a stage-style overlay would.

## Outputs

- Contact sheet: `{manifest['contact_sheet_path']}`
- Report: `{manifest['report_path']}`
- Manifest: `{manifest['manifest_path']}`

| Variant | Name | Crop | Treatment | Limit |
| --- | --- | --- | --- | --- |
{rows}

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- source_auto_enabled=false
- paid_apis=false
"""


def build_packet(*, source_image: Path, output_dir: Path, head_commit: str = "") -> dict[str, Any]:
    source_image = source_image.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = build_variant_specs()

    variant_rows: list[dict[str, Any]] = []
    for spec in specs:
        output_path = output_dir / spec["output_name"]
        render_variant(source_image, output_path, spec)
        row = dict(spec)
        row.update(
            {
                "output_png_path": output_path.as_posix(),
                "source_image_path": source_image.as_posix(),
                "source_image_present": source_image.exists(),
                "source_image_sha256": sha256_file(source_image) if source_image.exists() else "",
                "dimensions": png_dimensions(output_path),
                "review_only": True,
                "burn_in_text": REVIEW_ONLY_BURN_IN,
            }
        )
        variant_rows.append(row)

    contact_sheet_path = build_contact_sheet(output_dir, variant_rows)
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    best_variant_id = "variant_04_clean_story_stack"
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_apcs039_typography_crop_refine_ready",
        "repo_head": head_commit,
        "output_dir": output_dir.as_posix(),
        "source_image_path": source_image.as_posix(),
        "source_image_present": source_image.exists(),
        "source_image_sha256": sha256_file(source_image) if source_image.exists() else "",
        "contact_sheet_path": contact_sheet_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "variant_count": len(variant_rows),
        "best_variant_id": best_variant_id,
        "variant_rows": variant_rows,
        "known_source_limit": "APCS039 is a review-only official-gallery candidate; download approval is not asset approval.",
        "review_only": True,
        "approved_marker_writes": False,
        **FALSE_GUARDRAILS,
    }

    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    write_csv(output_dir / CSV_NAME, build_manual_rows(variant_rows), CSV_FIELDS)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build APCS039 WNBA typography/crop refinement packet.")
    parser.add_argument("--source-image", default=DEFAULT_SOURCE_IMAGE.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_image = resolve_source_image(args.source_image)
    output_dir = resolve_output_dir(args.output_dir or None)
    manifest = build_packet(source_image=source_image, output_dir=output_dir, head_commit=args.head_commit)
    print(json.dumps({"version": VERSION, "status": manifest["status"], "variant_count": manifest["variant_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
