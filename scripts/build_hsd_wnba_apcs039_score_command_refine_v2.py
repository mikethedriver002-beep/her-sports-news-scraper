from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts import build_hsd_jackie_young_typography_crop_refine_v1 as base

try:
    from PIL import Image, ImageDraw, ImageOps
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-wnba-apcs039-score-command-refine-v2-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_apcs039_score_command_refine_v2.py"
DEFAULT_SOURCE_IMAGE = base.DEFAULT_SOURCE_IMAGE
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_apcs039_score_command_refine_v2")
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
BURN_IN = "REVIEW ONLY - APCS039 SCORE COMMAND V2"

FALSE_GUARDRAILS = {
    "review_only": True,
    "asset_downloads": False,
    "approval_state_change": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
    "paid_apis": False,
    "approved_marker_writes": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "headshot_writes": False,
    "move_files": False,
    "protected_asset_moves": False,
}

CSV_FIELDS = [
    "variant_id",
    "variant_name",
    "render_path",
    "crop_strategy",
    "typography_treatment",
    "banner_placement",
    "side_accent_grammar",
    "tracking",
    "visual_strength",
    "known_limit",
    "operator_decision",
    "operator_notes",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
    "source_auto_enabled",
    "paid_apis",
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
    return base.fit_crop(source_image, center, zoom)


def apply_grade(image: Any, grade: dict[str, Any]) -> Any:
    return base.apply_grade(image, grade)


def add_gradient_scrim(base_image: Any, side: str, strength: float, width_ratio: float) -> Any:
    return base.add_gradient_scrim(base_image, side, strength, width_ratio)


def text_size(draw: Any, text: str, font: Any) -> tuple[int, int]:
    return base.text_size(draw, text, font)


def text_width(draw: Any, text: str, font: Any, tracking: int = 0) -> int:
    if not text:
        return 0
    total = 0
    for idx, ch in enumerate(text):
        total += text_size(draw, ch, font)[0]
        if idx < len(text) - 1:
            total += tracking
    return total


def text_height(draw: Any, text: str, font: Any) -> int:
    return text_size(draw, text or "Ag", font)[1]


def draw_tracked_line(
    draw: Any,
    x: int,
    y: int,
    text: str,
    font: Any,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
    shadow: tuple[int, int, int],
    *,
    tracking: int = 0,
    align: str = "left",
    box_width: int | None = None,
    shadow_offset: tuple[int, int] = (2, 2),
) -> tuple[int, int]:
    line_width = text_width(draw, text, font, tracking=tracking)
    line_height = text_height(draw, text, font)
    draw_x = x
    if align == "center" and box_width is not None:
        draw_x = x + max(0, (box_width - line_width) // 2)
    elif align == "right" and box_width is not None:
        draw_x = x + max(0, box_width - line_width)

    cursor_x = draw_x
    for idx, ch in enumerate(text):
        char_width = text_size(draw, ch, font)[0]
        draw.text((cursor_x + shadow_offset[0], y + shadow_offset[1]), ch, font=font, fill=shadow)
        draw.text((cursor_x, y), ch, font=font, fill=fill)
        cursor_x += char_width
        if idx < len(text) - 1:
            cursor_x += tracking
    return line_width, line_height


def draw_tracked_block(
    draw: Any,
    x: int,
    y: int,
    lines: list[dict[str, Any]],
    *,
    box_width: int,
) -> int:
    cursor_y = y
    for line in lines:
        text = str(line["text"])
        font = line["font"]
        fill = line["fill"]
        shadow = line["shadow"]
        tracking = int(line.get("tracking", 0))
        gap = int(line.get("gap", 0))
        line_height = draw_tracked_line(
            draw,
            x,
            cursor_y,
            text,
            font,
            fill,
            shadow,
            tracking=tracking,
            align=str(line.get("align", "left")),
            box_width=box_width,
            shadow_offset=tuple(line.get("shadow_offset", (2, 2))),
        )[1]
        cursor_y += line_height + gap
    return cursor_y - y


def draw_horizontal_bar(
    draw: Any,
    x: int,
    y: int,
    width: int,
    color: tuple[int, int, int],
    *,
    alpha: int = 200,
    thickness: int = 8,
) -> None:
    draw.rounded_rectangle((x, y, x + width, y + thickness), radius=max(2, thickness // 2), fill=(*color, alpha))


def draw_vertical_grammar(
    draw: Any,
    x: int,
    y: int,
    height: int,
    color: tuple[int, int, int],
    *,
    alpha: int = 160,
    thickness: int = 10,
    cap_width: int = 50,
    cap_y_offset: int = 10,
) -> None:
    draw.rounded_rectangle((x, y, x + thickness, y + height), radius=max(2, thickness // 2), fill=(*color, alpha))
    draw.rounded_rectangle(
        (x - cap_width + thickness, y + cap_y_offset, x + thickness, y + cap_y_offset + 10),
        radius=4,
        fill=(*color, min(255, alpha + 30)),
    )


def draw_footer_tag(draw: Any, width: int, height: int, text: str) -> None:
    font = load_font(16, bold=False)
    tag_w, _ = text_size(draw, text, font)
    draw.text((width - tag_w - 30, height - 42), text, fill=(224, 230, 238, 175), font=font)


def build_variant_specs() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "variant_01_score_command_low_banner",
            "variant_name": "Score Command Low Banner",
            "output_name": "variant_01_score_command_low_banner.png",
            "crop_strategy": "apcs039_score_command_right_anchor_safe_crop",
            "crop_center": [0.54, 0.48],
            "crop_zoom": 1.05,
            "grade": {"brightness": 0.74, "contrast": 1.23, "color": 0.94, "sharpness": 1.10, "vignette": 0.26, "top_scrim": 0.10},
            "scrim_side": "right",
            "scrim_strength": 0.22,
            "scrim_width_ratio": 0.25,
            "headline": "JACKIE\nYOUNG",
            "headline_lines": ["JACKIE", "YOUNG"],
            "headline_align": "right",
            "typography_treatment": "score_command_right_stack_with_low_banner",
            "tracking": 1,
            "headline_size": 104,
            "headline_tracking": 1,
            "headline_gap": 2,
            "kicker": "FINAL / LAS VEGAS",
            "kicker_size": 26,
            "kicker_tracking": 1,
            "detail": "APCS039 SCORE COMMAND",
            "detail_size": 22,
            "detail_tracking": 0,
            "banner_placement": "lower_right_banner",
            "banner_y": 884,
            "banner_width": 246,
            "side_accent_grammar": "right_side_accent_vertical_block_with_muted_lower_bar",
            "vertical_x": 1000,
            "vertical_y": 148,
            "vertical_height": 496,
            "vertical_alpha": 160,
            "horizontal_x": 664,
            "horizontal_y": 930,
            "horizontal_width": 232,
            "horizontal_alpha": 200,
            "footer": "REVIEW ONLY",
            "text_box": {"x": 654, "y": 126, "w": 340, "h": 920},
            "visual_strength": "strongest_score_command_route_with_low_banner",
            "known_limit": "review_only_official_gallery_candidate_not_asset_approved",
        },
        {
            "variant_id": "variant_02_lower_banner_lead",
            "variant_name": "Lower Banner Lead",
            "output_name": "variant_02_lower_banner_lead.png",
            "crop_strategy": "apcs039_left_lead_lower_banner_crop",
            "crop_center": [0.52, 0.49],
            "crop_zoom": 1.03,
            "grade": {"brightness": 0.76, "contrast": 1.22, "color": 0.95, "sharpness": 1.09, "vignette": 0.24, "top_scrim": 0.08},
            "scrim_side": "bottom",
            "scrim_strength": 0.16,
            "scrim_width_ratio": 0.20,
            "headline": "FINAL",
            "headline_lines": ["FINAL"],
            "headline_align": "left",
            "typography_treatment": "lower_banner_lead_with_tall_final",
            "tracking": 2,
            "headline_size": 108,
            "headline_tracking": 2,
            "headline_gap": 0,
            "kicker": "JACKIE YOUNG / WNBA",
            "kicker_size": 24,
            "kicker_tracking": 1,
            "detail": "LAS VEGAS ACES",
            "detail_size": 22,
            "detail_tracking": 0,
            "banner_placement": "left_low_banner",
            "banner_y": 522,
            "banner_width": 214,
            "side_accent_grammar": "left_side_accent_vertical_rule_and_short_cap",
            "vertical_x": 56,
            "vertical_y": 92,
            "vertical_height": 338,
            "vertical_alpha": 152,
            "horizontal_x": 82,
            "horizontal_y": 528,
            "horizontal_width": 188,
            "horizontal_alpha": 192,
            "footer": "APCS039",
            "text_box": {"x": 74, "y": 92, "w": 402, "h": 496},
            "visual_strength": "best_balanced_entry_route_with_lower_banner",
            "known_limit": "banner_is_low_by_design_and_should_be_checked_on_mobile",
        },
        {
            "variant_id": "variant_03_side_accent_block",
            "variant_name": "Side Accent Block",
            "output_name": "variant_03_side_accent_block.png",
            "crop_strategy": "apcs039_side_accent_right_keep_crop",
            "crop_center": [0.57, 0.50],
            "crop_zoom": 1.07,
            "grade": {"brightness": 0.75, "contrast": 1.25, "color": 0.94, "sharpness": 1.11, "vignette": 0.27, "top_scrim": 0.12},
            "scrim_side": "left",
            "scrim_strength": 0.20,
            "scrim_width_ratio": 0.24,
            "headline": "JACKIE\nYOUNG",
            "headline_lines": ["JACKIE", "YOUNG"],
            "headline_align": "left",
            "typography_treatment": "side_accent_block_with_midrail",
            "tracking": 1,
            "headline_size": 98,
            "headline_tracking": 1,
            "headline_gap": 0,
            "kicker": "LAS VEGAS ACES",
            "kicker_size": 24,
            "kicker_tracking": 1,
            "detail": "APCS039 / REVIEW ONLY",
            "detail_size": 22,
            "detail_tracking": 0,
            "banner_placement": "right_side_accent_midrail",
            "banner_y": 804,
            "banner_width": 226,
            "side_accent_grammar": "left_side_accent_vertical_block_with_midrail",
            "vertical_x": 60,
            "vertical_y": 118,
            "vertical_height": 508,
            "vertical_alpha": 160,
            "horizontal_x": 92,
            "horizontal_y": 826,
            "horizontal_width": 228,
            "horizontal_alpha": 190,
            "footer": "WNBA",
            "text_box": {"x": 76, "y": 106, "w": 384, "h": 782},
            "visual_strength": "best_side_accent_grammar_and_ball_side_read",
            "known_limit": "tighter_crop_needs_manual_read_check_on_lower_text",
        },
        {
            "variant_id": "variant_04_clean_story_stack",
            "variant_name": "Clean Story Stack",
            "output_name": "variant_04_clean_story_stack.png",
            "crop_strategy": "apcs039_clean_story_stack_lower_banner_crop",
            "crop_center": [0.51, 0.47],
            "crop_zoom": 1.01,
            "grade": {"brightness": 0.78, "contrast": 1.20, "color": 0.93, "sharpness": 1.08, "vignette": 0.24, "top_scrim": 0.08},
            "scrim_side": "bottom",
            "scrim_strength": 0.14,
            "scrim_width_ratio": 0.16,
            "headline": "FINAL",
            "headline_lines": ["FINAL"],
            "headline_align": "left",
            "typography_treatment": "clean_story_stack_with_footer_bar",
            "tracking": 2,
            "headline_size": 102,
            "headline_tracking": 2,
            "headline_gap": 0,
            "kicker": "JACKIE YOUNG",
            "kicker_size": 24,
            "kicker_tracking": 1,
            "detail": "LAS VEGAS ACES / APCS039",
            "detail_size": 21,
            "detail_tracking": 0,
            "banner_placement": "clean_story_footer_bar",
            "banner_y": 324,
            "banner_width": 186,
            "side_accent_grammar": "minimal_side_accent_lower_bar_with_no_staged_box",
            "vertical_x": 0,
            "vertical_y": 0,
            "vertical_height": 0,
            "vertical_alpha": 0,
            "horizontal_x": 86,
            "horizontal_y": 332,
            "horizontal_width": 178,
            "horizontal_alpha": 180,
            "footer": "REVIEW ONLY",
            "text_box": {"x": 84, "y": 82, "w": 396, "h": 282},
            "visual_strength": "cleanest_editorial_route_with_score_command_carryover",
            "known_limit": "most_conservative_read_for_future_context_use",
        },
    ]


def render_variant(source_image: Path, output_path: Path, spec: dict[str, Any]) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for APCS039 score-command refinement renders")

    base_crop = fit_crop(source_image, list(spec["crop_center"]), float(spec["crop_zoom"]))
    graded = apply_grade(base_crop, dict(spec.get("grade", {})))
    layered = add_gradient_scrim(
        graded,
        str(spec.get("scrim_side", "right")),
        float(spec.get("scrim_strength", 0.18)),
        float(spec.get("scrim_width_ratio", 0.24)),
    )
    draw = ImageDraw.Draw(layered, "RGBA")

    width, height = layered.size
    box = dict(spec.get("text_box", {"x": 72, "y": 72, "w": 360, "h": 500}))
    accent = (228, 108, 118)
    if spec["variant_id"] in {"variant_02_lower_banner_lead", "variant_04_clean_story_stack"}:
        accent = (236, 204, 132)
    elif spec["variant_id"] == "variant_03_side_accent_block":
        accent = (212, 58, 74)

    title_color = (248, 248, 248)
    support_color = (214, 220, 232)
    shadow = (8, 8, 12)
    kicker_font = load_font(int(spec.get("kicker_size", 24)), bold=True)
    headline_font = load_font(int(spec.get("headline_size", 100)), bold=True)
    detail_font = load_font(int(spec.get("detail_size", 21)), bold=False)
    footer_font = load_font(18, bold=True)

    x = int(box["x"])
    y = int(box["y"])
    box_width = int(box["w"])
    draw_tracked_block(
        draw,
        x,
        y,
        [
            {
                "text": spec["kicker"],
                "font": kicker_font,
                "fill": support_color,
                "shadow": shadow,
                "tracking": int(spec.get("kicker_tracking", 0)),
                "gap": 18,
                "align": spec["headline_align"],
                "shadow_offset": (2, 2),
            },
        ],
        box_width=box_width,
    )

    line_gap = int(spec.get("headline_gap", 0))
    headline_y = y + text_height(draw, spec["kicker"], kicker_font) + 18
    for idx, line in enumerate(spec.get("headline_lines", [spec["headline"]])):
        line_text = str(line)
        line_align = str(spec.get("headline_align", "left"))
        draw_tracked_line(
            draw,
            x,
            headline_y,
            line_text,
            headline_font,
            title_color,
            shadow,
            tracking=int(spec.get("headline_tracking", 0)),
            align=line_align,
            box_width=box_width,
        )
        headline_y += text_height(draw, line_text, headline_font) + (line_gap if idx < len(spec.get("headline_lines", [])) - 1 else 10)

    detail_y = headline_y + 4
    draw_tracked_line(
        draw,
        x,
        detail_y,
        str(spec["detail"]),
        detail_font,
        support_color,
        shadow,
        tracking=int(spec.get("detail_tracking", 0)),
        align=str(spec.get("headline_align", "left")),
        box_width=box_width,
        shadow_offset=(1, 1),
    )

    banner_y = int(spec.get("banner_y", detail_y + 100))
    horizontal_x = int(spec.get("horizontal_x", x))
    horizontal_width = int(spec.get("horizontal_width", 180))
    draw_horizontal_bar(
        draw,
        horizontal_x,
        banner_y,
        horizontal_width,
        accent,
        alpha=int(spec.get("horizontal_alpha", 180)),
        thickness=8,
    )

    vertical_alpha = int(spec.get("vertical_alpha", 0))
    vertical_height = int(spec.get("vertical_height", 0))
    if vertical_alpha > 0 and vertical_height > 0:
        draw_vertical_grammar(
            draw,
            int(spec.get("vertical_x", 0)),
            int(spec.get("vertical_y", 0)),
            vertical_height,
            accent,
            alpha=vertical_alpha,
            thickness=10,
            cap_width=48,
        )

    footer = str(spec.get("footer", "REVIEW ONLY"))
    if spec["variant_id"] == "variant_01_score_command_low_banner":
        footer_x = 32
        footer_y = height - 66
        draw.text((footer_x, footer_y), footer, fill=(230, 232, 238, 220), font=footer_font)
    elif spec["variant_id"] == "variant_02_lower_banner_lead":
        tag_font = load_font(16, bold=False)
        draw.text((width - 146, height - 42), "APCS039 / JACKIE YOUNG", fill=(228, 232, 239, 180), font=tag_font)
        draw.text((32, height - 66), footer, fill=(230, 232, 238, 210), font=footer_font)
    elif spec["variant_id"] == "variant_03_side_accent_block":
        draw.text((32, height - 66), footer, fill=(230, 232, 238, 210), font=footer_font)
    else:
        draw.text((32, height - 66), footer, fill=(230, 232, 238, 210), font=footer_font)

    draw_footer_tag(draw, width, height, BURN_IN)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    layered.convert("RGB").save(output_path, "PNG")


def build_contact_sheet(output_dir: Path, variants: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None or ImageOps is None:
        raise RuntimeError("Pillow is required for the APCS039 contact sheet")
    sheet = Image.new("RGB", (1080, 1350), (10, 12, 18))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(24, bold=True)
    small_font = load_font(16, bold=False)
    sub_font = load_font(18, bold=True)
    draw.text((36, 28), "APCS039 SCORE COMMAND REFINE V2", fill=(245, 246, 250), font=title_font)
    draw.text(
        (36, 62),
        "Review-only follow-up from the strongest WNBA score command direction. Lower banners, cleaner side bars, no staged mockup language.",
        fill=(190, 197, 210),
        font=small_font,
    )

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
                "banner_placement": row["banner_placement"],
                "side_accent_grammar": row["side_accent_grammar"],
                "tracking": str(row["tracking"]),
                "visual_strength": row["visual_strength"],
                "known_limit": row["known_limit"],
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
                "source_auto_enabled": "false",
                "paid_apis": "false",
            }
        )
    return rows


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            f"| `{row['variant_id']}` | {row['variant_name']} | {row['crop_strategy']} | {row['typography_treatment']} | {row['banner_placement']} | {row['known_limit']} |"
            for row in manifest["variant_rows"]
        ]
    )
    return f"""# APCS039 Score Command Refine V2

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet carries forward the strongest current WNBA graphic direction from the prior APCS039 lane and tightens it around score-command hierarchy, lower banner placement, and the muted horizontal bar plus side-accent grammar. It stays source-led, review-only, and intentionally avoids boxed-stage or gray-floor mockup language.

## Visual Read

- Best overall route: `variant_01_score_command_low_banner`, because it most clearly keeps the score-command treatment alive while lowering the banner and preserving the vertical side block.
- Best editorial fallback: `variant_04_clean_story_stack`, because it is the cleanest and least noisy route while still carrying the score-command grammar.
- Best entry route: `variant_02_lower_banner_lead`, because the type reads fastest and the lower banner stays anchored instead of floating.
- Best side-accent grammar: `variant_03_side_accent_block`, because it gives the strongest vertical rule and mid-rail combination without looking staged.
- Blender note: not used; the local source-led layout already solves the brief more cleanly than a heavier overlay would.

## Outputs

- Contact sheet: `{manifest['contact_sheet_path']}`
- Report: `{manifest['report_path']}`
- Manifest: `{manifest['manifest_path']}`

| Variant | Name | Crop | Treatment | Banner | Limit |
| --- | --- | --- | --- | --- | --- |
{rows}

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
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
                "burn_in_text": BURN_IN,
                "tracking": int(spec.get("tracking", spec.get("headline_tracking", 0))),
            }
        )
        variant_rows.append(row)

    contact_sheet_path = build_contact_sheet(output_dir, variant_rows)
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    best_variant_id = "variant_01_score_command_low_banner"
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_apcs039_score_command_refine_ready",
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
        **FALSE_GUARDRAILS,
    }

    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    write_csv(output_dir / CSV_NAME, build_manual_rows(variant_rows), CSV_FIELDS)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build APCS039 WNBA score-command refinement packet.")
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
