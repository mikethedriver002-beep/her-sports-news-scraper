from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, ImageStat
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageChops = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageEnhance = None  # type: ignore[assignment]
    ImageFilter = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]
    ImageStat = None  # type: ignore[assignment]


VERSION = "hsd-wnba-editorial-rescue-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_editorial_rescue_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_editorial_rescue_v1")
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
LAYER_MAP_NAME = "layer_map.md"
BURN_IN = "REVIEW ONLY - WNBA EDITORIAL RESCUE"
CANVAS = {"width": 1080, "height": 1350}

FALSE_GUARDRAILS = {
    "review_only": True,
    "asset_downloads": False,
    "approval_state_change": False,
    "approved_marker_writes": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
    "blender_used": False,
    "photoshop_used": False,
}

SOURCE_POOL: dict[str, dict[str, Any]] = {
    "jackie_young": {
        "source_image_path": Path("data/assets/player_images/jackie-young_img_6028f5e4a8042a.jpg"),
        "player_name": "Jackie Young",
        "team_name": "Las Vegas Aces",
        "accent": (239, 84, 92),
        "support": (227, 213, 165),
    },
    "aja_wilson": {
        "source_image_path": Path("data/assets/player_images/a-ja-wilson_img_bc9d5ea0730f15.jpg"),
        "player_name": "A'ja Wilson",
        "team_name": "Las Vegas Aces",
        "accent": (245, 194, 92),
        "support": (223, 231, 242),
    },
    "arike_ogunbowale": {
        "source_image_path": Path("data/assets/player_images/arike-ogunbowale_img_b657bc0d660f71.jpg"),
        "player_name": "Arike Ogunbowale",
        "team_name": "Dallas Wings",
        "accent": (230, 53, 75),
        "support": (210, 216, 228),
    },
    "nneka_ogwumike": {
        "source_image_path": Path("data/assets/player_images/nneka-ogwumike_img_5f16a036aea79f.jpg"),
        "player_name": "Nneka Ogwumike",
        "team_name": "Los Angeles Sparks",
        "accent": (247, 205, 53),
        "support": (224, 224, 226),
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_source_image(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_font(size: int, *, bold: bool = True) -> Any:
    if ImageFont is None:
        raise RuntimeError("Pillow ImageFont is unavailable")
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\bahnschrift.ttf"),
        Path(r"C:\Windows\Fonts\seguisb.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def png_dimensions(path: Path) -> list[int]:
    if Image is None:
        return []
    with Image.open(path) as image:
        return [int(image.size[0]), int(image.size[1])]


def fit_crop(source_image: Path, center: list[float], zoom: float) -> Any:
    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow is required for WNBA editorial rescue renders")
    with Image.open(source_image) as image:
        rgb = image.convert("RGB")
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
        resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)
        return crop.resize((CANVAS["width"], CANVAS["height"]), resample)


def apply_grade(image: Any, grade: dict[str, Any]) -> Any:
    if Image is None or ImageEnhance is None or ImageOps is None:
        raise RuntimeError("Pillow enhancements are required for WNBA editorial rescue renders")
    graded = ImageOps.autocontrast(image.convert("RGB"), cutoff=1)
    graded = ImageEnhance.Brightness(graded).enhance(float(grade.get("brightness", 0.76)))
    graded = ImageEnhance.Contrast(graded).enhance(float(grade.get("contrast", 1.25)))
    graded = ImageEnhance.Color(graded).enhance(float(grade.get("color", 0.94)))
    graded = ImageEnhance.Sharpness(graded).enhance(float(grade.get("sharpness", 1.08)))

    width, height = graded.size
    vignette = float(grade.get("vignette", 0.0))
    if vignette > 0:
        mask = Image.new("L", (width, height), 0)
        stat = ImageStat.Stat(graded.convert("L"))
        center_x = width * 0.54
        center_y = height * 0.44
        max_distance = ((max(center_x, width - center_x) ** 2) + (max(center_y, height - center_y) ** 2)) ** 0.5
        threshold = max(50, min(140, int(stat.mean[0] + 18)))
        pixels: list[int] = []
        for y in range(height):
            for x in range(width):
                distance = (((x - center_x) ** 2) + ((y - center_y) ** 2)) ** 0.5 / max_distance
                strength = max(0.0, min(1.0, (distance - 0.42) / 0.58))
                pixels.append(int(255 * vignette * strength))
        mask.putdata(pixels)
        dark = Image.new("RGB", (width, height), (7, 9, 13))
        graded = Image.composite(dark, graded, mask)

    top_scrim = float(grade.get("top_scrim", 0.0))
    if top_scrim > 0:
        scrim = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        alpha = Image.new("L", (width, height), 0)
        alpha_pixels: list[int] = []
        fade_height = max(1, int(height * 0.34))
        for y in range(height):
            local = max(0.0, 1.0 - (y / fade_height))
            alpha_pixels.extend([int(255 * top_scrim * local)] * width)
        alpha.putdata(alpha_pixels)
        scrim.putalpha(alpha)
        graded = Image.alpha_composite(graded.convert("RGBA"), scrim).convert("RGB")

    return graded


def add_gradient_scrim(image: Any, side: str, strength: float, width_ratio: float) -> Any:
    if Image is None or ImageEnhance is None or ImageOps is None:
        raise RuntimeError("Pillow is required for WNBA editorial rescue scrims")
    width, height = image.size
    band_width = max(1, int(width * width_ratio))
    alpha = max(0, min(255, int(255 * strength)))
    if alpha <= 0:
        return image.convert("RGBA")

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
    band = Image.new("RGBA", (width, height), (6, 8, 12, 0))
    band.putalpha(mask)
    return Image.alpha_composite(image.convert("RGBA"), band)


def text_size(draw: Any, text: str, font: Any) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def draw_shadowed_text(
    draw: Any,
    position: tuple[int, int],
    text: str,
    font: Any,
    fill: tuple[int, int, int] | tuple[int, int, int, int],
    shadow: tuple[int, int, int],
    *,
    offset: tuple[int, int] = (2, 2),
) -> None:
    x, y = position
    draw.text((x + offset[0], y + offset[1]), text, fill=shadow, font=font)
    draw.text((x, y), text, fill=fill, font=font)


def draw_text_block(
    draw: Any,
    x: int,
    y: int,
    lines: list[dict[str, Any]],
    *,
    align: str = "left",
    box_width: int | None = None,
) -> int:
    cursor_y = y
    total_height = 0
    for line in lines:
        text = str(line["text"])
        font = line["font"]
        fill = line["fill"]
        shadow = line["shadow"]
        gap = int(line.get("gap", 0))
        tracking = int(line.get("tracking", 0))
        width = 0
        for idx, ch in enumerate(text):
            char_width, char_height = text_size(draw, ch, font)
            width += char_width
            if idx < len(text) - 1:
                width += tracking
        line_height = text_size(draw, text or "Ag", font)[1]
        draw_x = x
        if align == "center" and box_width is not None:
            draw_x = x + max(0, (box_width - width) // 2)
        elif align == "right" and box_width is not None:
            draw_x = x + max(0, box_width - width)

        cursor_x = draw_x
        for idx, ch in enumerate(text):
            char_width, _ = text_size(draw, ch, font)
            draw.text((cursor_x + 2, cursor_y + 2), ch, font=font, fill=shadow)
            draw.text((cursor_x, cursor_y), ch, font=font, fill=fill)
            cursor_x += char_width
            if idx < len(text) - 1:
                cursor_x += tracking
        cursor_y += line_height + gap
        total_height += line_height + gap
    return total_height


def build_subject_mask(image: Any) -> Any:
    if Image is None or ImageFilter is None or ImageStat is None or ImageOps is None:
        raise RuntimeError("Pillow is required for WNBA editorial rescue masks")
    gray = ImageOps.autocontrast(image.convert("L"), cutoff=2)
    stat = ImageStat.Stat(gray)
    threshold = max(24, min(110, int(stat.mean[0] * 0.55)))
    mask = gray.point(lambda p: 255 if p >= threshold else 0)
    mask = mask.filter(ImageFilter.MaxFilter(11))
    mask = mask.filter(ImageFilter.MinFilter(7))
    mask = mask.filter(ImageFilter.GaussianBlur(2.5))
    return mask


def source_label(source_key: str) -> str:
    source = SOURCE_POOL[source_key]
    return f"{source['player_name']} / {source['team_name']}"


def build_variant_specs() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "jackie_final_cover",
            "variant_name": "Jackie Final Cover",
            "source_key": "jackie_young",
            "output_name": "variant_01_jackie_final_cover.png",
            "decision": "keep",
            "visual_strength": "strongest premium cover route",
            "crop_center": [0.51, 0.49],
            "crop_zoom": 1.04,
            "grade": {"brightness": 0.76, "contrast": 1.28, "color": 0.94, "sharpness": 1.10, "vignette": 0.32, "top_scrim": 0.16},
            "scrim_side": "right",
            "scrim_strength": 0.18,
            "scrim_width_ratio": 0.26,
            "headline_lines": ["FINAL", "JACKIE YOUNG"],
            "headline_align": "left",
            "headline_size": 110,
            "headline_tracking": 0,
            "headline_x": 74,
            "headline_y": 118,
            "headline_gap": 10,
            "kicker": "LAS VEGAS ACES",
            "kicker_size": 26,
            "kicker_tracking": 1,
            "dek": "REVIEW-ONLY EDITORIAL RESCUE",
            "dek_size": 22,
            "accent_rule": [74, 370, 252],
            "footer": "WNBA / REVIEW ONLY",
            "footer_right": "LOCAL PHOTO SOURCE",
            "shadow_offset": (18, 18),
            "known_limit": "strongest premium cover route; slightly assertive but still clean",
        },
        {
            "variant_id": "aja_control_line",
            "variant_name": "A'ja Control Line",
            "source_key": "aja_wilson",
            "output_name": "variant_02_aja_control_line.png",
            "decision": "keep",
            "visual_strength": "cleanest magazine lane",
            "crop_center": [0.53, 0.46],
            "crop_zoom": 1.02,
            "grade": {"brightness": 0.75, "contrast": 1.26, "color": 0.96, "sharpness": 1.08, "vignette": 0.30, "top_scrim": 0.14},
            "scrim_side": "left",
            "scrim_strength": 0.18,
            "scrim_width_ratio": 0.24,
            "headline_lines": ["CONTROL", "A'JA WILSON"],
            "headline_align": "right",
            "headline_size": 102,
            "headline_tracking": 0,
            "headline_x": 92,
            "headline_y": 114,
            "headline_gap": 10,
            "kicker": "LAS VEGAS ACES",
            "kicker_size": 25,
            "kicker_tracking": 1,
            "dek": "PAINT PRESSURE / ELITE READ",
            "dek_size": 22,
            "accent_rule": [760, 370, 272],
            "footer": "FRONT-PAGE SPORTS TONE",
            "footer_right": "FULL-BLEED PHOTO",
            "shadow_offset": (16, 16),
            "known_limit": "cleanest magazine lane; a little less violent than the Jackie route",
        },
        {
            "variant_id": "arike_break_shot",
            "variant_name": "Arike Break Shot",
            "source_key": "arike_ogunbowale",
            "output_name": "variant_03_arike_break_shot.png",
            "decision": "keep",
            "visual_strength": "most dynamic comparison card",
            "crop_center": [0.48, 0.50],
            "crop_zoom": 1.03,
            "grade": {"brightness": 0.74, "contrast": 1.30, "color": 0.95, "sharpness": 1.11, "vignette": 0.30, "top_scrim": 0.16},
            "scrim_side": "top",
            "scrim_strength": 0.16,
            "scrim_width_ratio": 0.20,
            "headline_lines": ["BREAK", "ARIKE OGUNBOWALE"],
            "headline_align": "left",
            "headline_size": 106,
            "headline_tracking": 0,
            "headline_x": 74,
            "headline_y": 120,
            "headline_gap": 8,
            "kicker": "DALLAS WINGS",
            "kicker_size": 24,
            "kicker_tracking": 1,
            "dek": "LATE-CLOCK FIRE / SPORTS DESK READ",
            "dek_size": 21,
            "accent_rule": [76, 382, 224],
            "footer": "REPORTING-STYLE COVER",
            "footer_right": "HIGH-ENERGY SOURCE",
            "shadow_offset": (17, 17),
            "known_limit": "most dynamic frame; type has to stay disciplined or it gets noisy",
        },
        {
            "variant_id": "nneka_front_page",
            "variant_name": "Nneka Front Page",
            "source_key": "nneka_ogwumike",
            "output_name": "variant_04_nneka_front_page.png",
            "decision": "kill",
            "visual_strength": "weakest premium route",
            "crop_center": [0.49, 0.48],
            "crop_zoom": 1.01,
            "grade": {"brightness": 0.73, "contrast": 1.24, "color": 0.92, "sharpness": 1.06, "vignette": 0.28, "top_scrim": 0.16},
            "scrim_side": "bottom",
            "scrim_strength": 0.14,
            "scrim_width_ratio": 0.18,
            "headline_lines": ["FEATURE", "NNEKA OGWUMIKE"],
            "headline_align": "center",
            "headline_size": 98,
            "headline_tracking": 0,
            "headline_x": 62,
            "headline_y": 116,
            "headline_gap": 10,
            "kicker": "LOS ANGELES SPARKS",
            "kicker_size": 24,
            "kicker_tracking": 1,
            "dek": "GOOD SOURCE, BUT THE CROP FIGHTS THE OPENING PAGE READ",
            "dek_size": 20,
            "accent_rule": [410, 378, 268],
            "footer": "WEAKEST OF THE FOUR",
            "footer_right": "KILL UNLESS YOU WANT TEXTURE",
            "shadow_offset": (15, 15),
            "known_limit": "busier crowd plane makes this feel less premium than the top three",
        },
    ]


def variant_text_color(spec: dict[str, Any]) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    source = SOURCE_POOL[spec["source_key"]]
    accent = tuple(int(v) for v in source["accent"])
    support = tuple(int(v) for v in source["support"])
    text = (246, 246, 244)
    return text, accent, support


def render_variant(source_image: Path, output_path: Path, spec: dict[str, Any]) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for WNBA editorial rescue renders")

    base_crop = fit_crop(source_image, list(spec["crop_center"]), float(spec["crop_zoom"]))
    graded = apply_grade(base_crop, dict(spec.get("grade", {})))
    background = add_gradient_scrim(graded, str(spec.get("scrim_side", "right")), float(spec.get("scrim_strength", 0.16)), float(spec.get("scrim_width_ratio", 0.22)))
    background = background.convert("RGBA")
    draw = ImageDraw.Draw(background, "RGBA")

    title_color, accent_color, support_color = variant_text_color(spec)
    shadow = (8, 8, 12)
    headline_font = load_font(int(spec.get("headline_size", 100)), bold=True)
    kicker_font = load_font(int(spec.get("kicker_size", 24)), bold=True)
    dek_font = load_font(int(spec.get("dek_size", 20)), bold=False)
    footer_font = load_font(18, bold=True)
    small_font = load_font(15, bold=False)

    x = int(spec.get("headline_x", 72))
    y = int(spec.get("headline_y", 104))
    box_width = 460 if spec["headline_align"] != "center" else 560
    draw_text_block(
        draw,
        x,
        y,
        [
            {
                "text": spec["kicker"],
                "font": kicker_font,
                "fill": support_color,
                "shadow": shadow,
                "gap": 14,
                "tracking": int(spec.get("kicker_tracking", 0)),
            },
            {
                "text": spec["headline_lines"][0],
                "font": headline_font,
                "fill": title_color,
                "shadow": shadow,
                "gap": int(spec.get("headline_gap", 8)),
                "tracking": int(spec.get("headline_tracking", 0)),
            },
            {
                "text": spec["headline_lines"][1],
                "font": headline_font,
                "fill": title_color,
                "shadow": shadow,
                "gap": 18,
                "tracking": int(spec.get("headline_tracking", 0)),
            },
        ],
        align=str(spec.get("headline_align", "left")),
        box_width=box_width,
    )
    # editorial rule: thin, not boxed
    rule_x, rule_y, rule_w = [int(v) for v in spec["accent_rule"]]
    draw.rounded_rectangle((rule_x, rule_y, rule_x + rule_w, rule_y + 6), radius=3, fill=(*accent_color, 214))

    dek_y = y + 276
    draw_shadowed_text(draw, (x, dek_y), spec["dek"], dek_font, support_color, shadow, offset=(1, 1))
    draw_shadowed_text(draw, (x, CANVAS["height"] - 66), spec["footer"], footer_font, (232, 236, 241), shadow, offset=(1, 1))
    footer_right = str(spec.get("footer_right", ""))
    if footer_right:
        right_w, _ = text_size(draw, footer_right, small_font)
        draw_shadowed_text(draw, (CANVAS["width"] - right_w - 32, CANVAS["height"] - 41), footer_right, small_font, (210, 216, 226), shadow, offset=(1, 1))

    draw = ImageDraw.Draw(background, "RGBA")
    draw_shadowed_text(draw, (32, 30), "WNBA / REVIEW ONLY", small_font, (216, 220, 230), shadow, offset=(1, 1))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.convert("RGB").save(output_path, "PNG")


def build_contact_sheet(output_dir: Path, rows: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None or ImageOps is None:
        raise RuntimeError("Pillow is required for the contact sheet")
    sheet = Image.new("RGB", (1080, 1350), (10, 12, 18))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(24, bold=True)
    small_font = load_font(16, bold=False)
    sub_font = load_font(17, bold=True)
    draw.text((34, 28), "WNBA EDITORIAL RESCUE V1", fill=(245, 246, 248), font=title_font)
    draw.text(
        (34, 60),
        "Local player images only. No downloads, no Photoshop automation, no Blender. Built as a blunt rescue pass against the dead APCS039 language.",
        fill=(188, 196, 208),
        font=small_font,
    )

    positions = [(36, 104), (552, 104), (36, 730), (552, 730)]
    resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)
    for (x, y), row in zip(positions, rows):
        with Image.open(row["render_path"]) as image:
            thumb = ImageOps.fit(image.convert("RGB"), (492, 560), method=resample)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + 572), row["variant_name"], fill=(244, 245, 248), font=sub_font)
        verdict = row["decision"].upper()
        draw.text((x, y + 596), f"{verdict}  |  {row['visual_strength']}", fill=(178, 185, 197), font=small_font)

    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path, "PNG")
    return path


def build_layer_map(output_dir: Path, rows: list[dict[str, Any]], layered_path: Path) -> Path:
    lines = [
        "# Layer Map",
        "",
        "This is the manual follow-up reference for a future Photoshop reconstruction.",
        "",
        f"- Planned layered file reference: `{layered_path.as_posix()}`",
        "- Actual rescue pass was flattened to PNG because Photoshop is not installed locally.",
        "",
        "## Intended layer stack",
        "",
        "- background crop",
        "- editorial grade",
        "- gradient scrims",
        "- headline and kicker text",
        "- rule line accent",
        "- soft silhouette shadow",
        "- subject cutout foreground",
        "- footer tag",
        "",
        "## Variants",
        "",
    ]
    for row in rows:
        lines.append(f"- {row['variant_id']}: {row['source_image_path']}")
    path = output_dir / LAYER_MAP_NAME
    write_text(path, "\n".join(lines) + "\n")
    return path


def build_manual_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for row in rows:
        result.append(
            {
                "variant_id": row["variant_id"],
                "variant_name": row["variant_name"],
                "render_path": row["render_path"],
                "source_image_path": row["source_image_path"],
                "decision": row["decision"],
                "visual_strength": row["visual_strength"],
                "known_limit": row["known_limit"],
                "photoshop_used": "false",
                "blender_used": "false",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return result


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            f"| `{row['variant_id']}` | {row['variant_name']} | {row['decision'].upper()} | {row['source_image_path']} | {row['known_limit']} |"
            for row in manifest["variant_rows"]
        ]
    )
    keep_rows = [row for row in manifest["variant_rows"] if row["decision"] == "keep"]
    kill_rows = [row for row in manifest["variant_rows"] if row["decision"] == "kill"]
    keep_line = ", ".join(f"`{row['variant_id']}`" for row in keep_rows) if keep_rows else "none"
    kill_line = ", ".join(f"`{row['variant_id']}`" for row in kill_rows) if kill_rows else "none"
    strongest = manifest["best_variant_id"]
    return f"""# WNBA Editorial Rescue V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This is a review-only rescue pass built from local WNBA player images only. Photoshop was not available locally, so the comping was rendered with Pillow instead. That is fine for the handoff, but it means the layered follow-up should happen manually if somebody wants a true PSD stack later.

## Blunt Read

- Best premium route: `{strongest}`
- Keep: {keep_line}
- Kill: {kill_line}
- Hard boundary: no boxed social scaffolding, no HUD brackets, no neon rails, no muddy lower bar, no downloads, no approvals, no publishing.

## Why It Works

- The Jackie and A'ja routes feel closest to elite sports journalism.
- The Arike route is the most aggressive, which makes it the best comparison card.
- The Nneka route is the weakest because the crowd plane steals a little too much authority from the headline.

## Output Table

| Variant | Verdict | Source | Note |
| --- | --- | --- | --- |
{rows}

## Deliverables

- Contact sheet: `{manifest['contact_sheet_path']}`
- Visual report: `{manifest['report_path']}`
- Manifest: `{manifest['manifest_path']}`
- Layer map: `{manifest['layer_map_path']}`

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- source_auto_enabled=false
- paid_apis=false
- photoshop_used=false
- blender_used=false
"""


def build_packet(*, output_dir: Path, head_commit: str = "") -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = build_variant_specs()

    variant_rows: list[dict[str, Any]] = []
    for spec in specs:
        source = SOURCE_POOL[spec["source_key"]]
        source_image = resolve_source_image(source["source_image_path"])
        output_path = output_dir / spec["output_name"]
        render_variant(source_image, output_path, spec)
        row = dict(spec)
        row.update(
            {
                "source_image_path": source_image.as_posix(),
                "source_image_present": source_image.exists(),
                "source_image_sha256": sha256_file(source_image) if source_image.exists() else "",
                "render_path": output_path.as_posix(),
                "dimensions": png_dimensions(output_path),
                "photoshop_used": False,
                "blender_used": False,
                "review_only": True,
                "burn_in_text": BURN_IN,
                "source_label": source_label(spec["source_key"]),
                "visual_strength": str(spec.get("visual_strength", "")),
            }
        )
        variant_rows.append(row)

    contact_sheet_path = build_contact_sheet(output_dir, variant_rows)
    layered_path = output_dir / "working" / "wnba_editorial_rescue_v1.psd"
    layer_map_path = build_layer_map(output_dir, variant_rows, layered_path)
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME

    best_variant_id = "jackie_final_cover"
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_editorial_rescue_ready",
        "repo_head": head_commit,
        "output_dir": output_dir.as_posix(),
        "contact_sheet_path": contact_sheet_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "layer_map_path": layer_map_path.as_posix(),
        "layered_working_file_path_reference": layered_path.as_posix(),
        "variant_count": len(variant_rows),
        "best_variant_id": best_variant_id,
        "variant_rows": variant_rows,
        "photoshop_used": False,
        "blender_used": False,
        "review_only": True,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
        "source_auto_enabled": False,
        "paid_apis": False,
        "traceback_present": False,
        **FALSE_GUARDRAILS,
    }

    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    write_csv(output_dir / CSV_NAME, build_manual_rows(variant_rows), [
        "variant_id",
        "variant_name",
        "render_path",
        "source_image_path",
        "decision",
        "visual_strength",
        "known_limit",
        "photoshop_used",
        "blender_used",
        "operator_decision",
        "operator_notes",
        "review_only",
        "asset_downloads",
        "approval_state_change",
        "publish_ready",
        "publishing",
    ])
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only WNBA editorial rescue packet.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None)
    manifest = build_packet(output_dir=output_dir, head_commit=args.head_commit.strip())
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "variant_count": manifest["variant_count"],
                "best_variant_id": manifest["best_variant_id"],
                "review_only": True,
                "photoshop_used": False,
                "blender_used": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
