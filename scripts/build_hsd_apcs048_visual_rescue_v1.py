from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
except Exception:  # pragma: no cover - Pillow is required in the local HSD runtime.
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageEnhance = None  # type: ignore[assignment]
    ImageFilter = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-apcs048-visual-rescue-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apcs048_visual_rescue_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/apcs048_visual_rescue_v1")
LOCAL_SOURCE_IMAGE_CANDIDATES = (
    Path(
        "data/assets/quarantine/review_only_candidates/action_photo_candidates/manual_decision_batch/"
        "au_volleyball_jordan_thompson/apcs048_operator_review.png"
    ),
)
CANVAS = {"width": 1080, "height": 1350}
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
RUBRIC_NAME = "visual_rubric.json"
REVIEW_LABEL = "REVIEW ONLY - APCS048 QUARANTINE VISUAL RESCUE"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "candidate_state_change": False,
    "download_performed": False,
    "headshot_writes": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
    "source_fetching": False,
}

CSV_FIELDS = [
    "candidate_id",
    "entity_name",
    "variant_id",
    "variant_name",
    "output_png_path",
    "visual_direction",
    "source_use",
    "rubric_verdict",
    "carry_forward_recommendation",
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


def resolve_source_image(explicit: str | None = None, root: Path | None = None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    root = root or repo_root()
    for relative_path in LOCAL_SOURCE_IMAGE_CANDIDATES:
        candidate = (root / relative_path).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
    candidates = ", ".join(path.as_posix() for path in LOCAL_SOURCE_IMAGE_CANDIDATES)
    raise FileNotFoundError(
        "No repo-local APCS048 quarantine source/reference was found. "
        f"Checked: {candidates}. "
        "Pass --source-image explicitly to use a quarantine source from another worktree."
    )


def require_pillow() -> None:
    if any(item is None for item in (Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps)):
        raise RuntimeError("Pillow is required to build the APCS048 visual rescue packet")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_font(size: int, *, bold: bool = True) -> Any:
    require_pillow()
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


def fit_font(draw: Any, text: str, size: int, max_width: int, *, bold: bool = True, floor: int = 16) -> Any:
    for current in range(size, floor - 1, -1):
        font = load_font(current, bold=bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
    return load_font(floor, bold=bold)


def build_variant_specs() -> list[dict[str, Any]]:
    return [
        {
            "variant_id": "rescue_01_gold_confetti_hero",
            "variant_name": "Gold Confetti Hero",
            "filename": "rescue_01_gold_confetti_hero.png",
            "visual_direction": "Full-bleed championship photo crop with bottom-left story lockup and controlled black-gold contrast.",
            "crop_center": [0.56, 0.47],
            "zoom": 1.0,
            "grade": {"brightness": 0.90, "contrast": 1.24, "color": 1.04, "sharpness": 1.08, "vignette": 0.22},
            "treatment": "hero_lockup",
            "headline": "CHAMPIONSHIP NIGHT",
            "subhead": "Jordan Thompson / APCS048 source read",
            "accent": [248, 213, 88],
            "accent_2": [246, 248, 252],
            "rubric_verdict": "strong_carry_forward_candidate",
            "carry_forward_recommendation": "carry_forward_first",
            "source_use": "dominant_full_bleed_source_crop",
            "notes": "Best balance of source confidence, premium social energy, and protected score/story negative space.",
        },
        {
            "variant_id": "rescue_02_score_window_right",
            "variant_name": "Score Window Right",
            "filename": "rescue_02_score_window_right.png",
            "visual_direction": "Near-full-bleed crop with a quiet right-side score/story rail, built for match-result copy.",
            "crop_center": [0.52, 0.49],
            "zoom": 1.06,
            "grade": {"brightness": 0.82, "contrast": 1.34, "color": 0.96, "sharpness": 1.06, "vignette": 0.32},
            "treatment": "score_rail",
            "headline": "FINAL",
            "subhead": "Score-ready social frame",
            "accent": [98, 191, 255],
            "accent_2": [249, 217, 97],
            "rubric_verdict": "useful_score_template_candidate",
            "carry_forward_recommendation": "carry_forward_second",
            "source_use": "dominant_source_crop_with_right_negative_space",
            "notes": "Most practical result-template direction; less celebratory than variant 01 but easier to operationalize.",
        },
        {
            "variant_id": "rescue_03_medal_closeup_cover",
            "variant_name": "Medal Closeup Cover",
            "filename": "rescue_03_medal_closeup_cover.png",
            "visual_direction": "Cinematic close crop around the athlete and medal with magazine-cover typography.",
            "crop_center": [0.56, 0.54],
            "zoom": 1.32,
            "grade": {"brightness": 0.86, "contrast": 1.30, "color": 0.98, "sharpness": 1.10, "vignette": 0.38},
            "treatment": "cover_crop",
            "headline": "THOMPSON",
            "subhead": "Gold-night source proof",
            "accent": [237, 187, 75],
            "accent_2": [238, 80, 96],
            "rubric_verdict": "revise_before_carry_forward",
            "carry_forward_recommendation": "revise_crop_if_used",
            "source_use": "tight_source_crop",
            "notes": "Punchy, but the crop may over-tighten useful scene context for HSD score usage.",
        },
        {
            "variant_id": "rescue_04_motion_stack_feature",
            "variant_name": "Motion Stack Feature",
            "filename": "rescue_04_motion_stack_feature.png",
            "visual_direction": "Layered source-led feature graphic with blurred full-bleed background and a crisp subject crop.",
            "crop_center": [0.57, 0.48],
            "zoom": 1.0,
            "grade": {"brightness": 0.78, "contrast": 1.42, "color": 0.88, "sharpness": 1.04, "vignette": 0.42},
            "treatment": "motion_stack",
            "headline": "SOURCE READ",
            "subhead": "Celebration frame / review only",
            "accent": [252, 210, 73],
            "accent_2": [230, 234, 242],
            "rubric_verdict": "experimental_but_viable",
            "carry_forward_recommendation": "hold_for_art_direction_review",
            "source_use": "source_duplicate_depth_treatment",
            "notes": "More stylized than the cleaner candidates; useful if HSD wants a feature-card route.",
        },
        {
            "variant_id": "rescue_05_clean_news_cover",
            "variant_name": "Clean News Cover",
            "filename": "rescue_05_clean_news_cover.png",
            "visual_direction": "Premium news-cover treatment with sober typography, clean top masthead, and source-led image read.",
            "crop_center": [0.55, 0.50],
            "zoom": 1.08,
            "grade": {"brightness": 0.84, "contrast": 1.20, "color": 0.94, "sharpness": 1.06, "vignette": 0.28},
            "treatment": "news_cover",
            "headline": "ATHLETES UNLIMITED",
            "subhead": "Jordan Thompson candidate review",
            "accent": [242, 243, 236],
            "accent_2": [238, 196, 70],
            "rubric_verdict": "solid_but_less_distinctive",
            "carry_forward_recommendation": "alternate_only",
            "source_use": "dominant_source_crop",
            "notes": "Professional and safe, but less visually ownable than the first two routes.",
        },
        {
            "variant_id": "rescue_06_black_gold_result_poster",
            "variant_name": "Black Gold Result Poster",
            "filename": "rescue_06_black_gold_result_poster.png",
            "visual_direction": "Dark cinematic result poster with gold score block and photo-driven arena energy.",
            "crop_center": [0.61, 0.48],
            "zoom": 1.14,
            "grade": {"brightness": 0.72, "contrast": 1.48, "color": 0.86, "sharpness": 1.05, "vignette": 0.48},
            "treatment": "result_poster",
            "headline": "RESULT",
            "subhead": "Story space without a stage box",
            "accent": [235, 185, 62],
            "accent_2": [245, 246, 248],
            "rubric_verdict": "carry_forward_if_darker_feed_needed",
            "carry_forward_recommendation": "third_choice",
            "source_use": "darkened_full_bleed_source_crop",
            "notes": "Strong feed contrast, though darker than the preferred HSD championship direction.",
        },
    ]


def crop_to_canvas(source: Any, center: list[float], zoom: float) -> Any:
    require_pillow()
    width, height = source.size
    target_ratio = CANVAS["width"] / CANVAS["height"]
    base_height = height
    base_width = int(round(base_height * target_ratio))
    if base_width > width:
        base_width = width
        base_height = int(round(base_width / target_ratio))
    zoom = max(1.0, float(zoom))
    crop_width = max(1, int(round(base_width / zoom)))
    crop_height = max(1, int(round(base_height / zoom)))
    center_x = int(round(width * float(center[0])))
    center_y = int(round(height * float(center[1])))
    left = max(0, min(width - crop_width, center_x - crop_width // 2))
    top = max(0, min(height - crop_height, center_y - crop_height // 2))
    crop = source.crop((left, top, left + crop_width, top + crop_height))
    return crop.resize((CANVAS["width"], CANVAS["height"]), getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1))


def add_vignette(image: Any, strength: float) -> Any:
    if strength <= 0:
        return image
    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    pixels = []
    center_x = width * 0.52
    center_y = height * 0.40
    max_distance = math.sqrt(max(center_x, width - center_x) ** 2 + max(center_y, height - center_y) ** 2)
    for y in range(height):
        for x in range(width):
            distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) / max_distance
            value = int(255 * strength * max(0.0, min(1.0, (distance - 0.28) / 0.72)))
            pixels.append(value)
    mask.putdata(pixels)
    dark = Image.new("RGB", (width, height), (5, 7, 10))
    return Image.composite(dark, image, mask)


def add_linear_scrim(image: Any, *, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0) -> Any:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    width, height = image.size
    pixels = overlay.load()
    for y in range(height):
        for x in range(width):
            alpha = 0
            if top:
                alpha = max(alpha, int(top * max(0.0, 1.0 - y / (height * 0.46))))
            if bottom:
                alpha = max(alpha, int(bottom * max(0.0, (y - height * 0.48) / (height * 0.52))))
            if left:
                alpha = max(alpha, int(left * max(0.0, 1.0 - x / (width * 0.42))))
            if right:
                alpha = max(alpha, int(right * max(0.0, (x - width * 0.50) / (width * 0.50))))
            if alpha:
                pixels[x, y] = (0, 0, 0, min(230, alpha))
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def apply_grade(image: Any, grade: dict[str, Any]) -> Any:
    require_pillow()
    graded = ImageOps.autocontrast(image.convert("RGB"), cutoff=1)
    graded = ImageEnhance.Brightness(graded).enhance(float(grade.get("brightness", 1.0)))
    graded = ImageEnhance.Contrast(graded).enhance(float(grade.get("contrast", 1.0)))
    graded = ImageEnhance.Color(graded).enhance(float(grade.get("color", 1.0)))
    graded = ImageEnhance.Sharpness(graded).enhance(float(grade.get("sharpness", 1.0)))
    graded = add_vignette(graded, float(grade.get("vignette", 0.0)))
    return graded.convert("RGBA")


def rgb(color: list[int], alpha: int = 255) -> tuple[int, int, int, int]:
    return (int(color[0]), int(color[1]), int(color[2]), alpha)


def draw_review_label(draw: Any, variant_id: str) -> None:
    label_font = load_font(21, bold=True)
    draw.rounded_rectangle((30, 28, 506, 70), radius=4, fill=(5, 7, 10, 172))
    draw.text((48, 39), REVIEW_LABEL, fill=(244, 246, 250, 235), font=label_font)
    id_font = load_font(17, bold=False)
    draw.text((48, 74), variant_id, fill=(221, 228, 238, 205), font=id_font)


def draw_footer_lock(draw: Any, text: str = "Quarantine proof / not asset-approved / not publish-ready") -> None:
    footer_font = load_font(18, bold=False)
    draw.rounded_rectangle((30, 1278, 720, 1322), radius=4, fill=(5, 7, 10, 166))
    draw.text((48, 1291), text, fill=(232, 237, 245, 222), font=footer_font)


def draw_hero_lockup(image: Any, spec: dict[str, Any]) -> Any:
    image = add_linear_scrim(image, bottom=208, left=128)
    draw = ImageDraw.Draw(image)
    accent = rgb(spec["accent"])
    draw.rectangle((54, 1018, 392, 1028), fill=accent)
    title_font = fit_font(draw, spec["headline"], 88, 910, bold=True)
    sub_font = load_font(30, bold=True)
    draw.text((52, 1042), spec["headline"], fill=(248, 249, 251, 255), font=title_font)
    draw.text((56, 1138), spec["subhead"], fill=accent, font=sub_font)
    small = load_font(23, bold=False)
    draw.text((56, 1184), "Source-led 4:5 rescue / social-ready negative space", fill=(228, 234, 242, 230), font=small)
    draw_review_label(draw, spec["variant_id"])
    draw_footer_lock(draw)
    return image


def draw_score_rail(image: Any, spec: dict[str, Any]) -> Any:
    image = add_linear_scrim(image, right=230, bottom=110)
    draw = ImageDraw.Draw(image)
    accent = rgb(spec["accent"])
    draw.rounded_rectangle((714, 172, 1024, 1058), radius=8, fill=(7, 10, 15, 196), outline=rgb(spec["accent_2"], 210), width=2)
    draw.rectangle((738, 214, 998, 224), fill=accent)
    draw.text((738, 258), spec["headline"], fill=(248, 250, 253, 255), font=load_font(78, bold=True))
    draw.text((742, 350), "0 - 0", fill=rgb(spec["accent_2"]), font=load_font(88, bold=True))
    draw.text((746, 462), spec["subhead"], fill=(226, 233, 242, 235), font=load_font(25, bold=True))
    for idx, label in enumerate(("MATCH NOTE", "HERO COPY", "PHOTO CHECK")):
        y = 626 + idx * 88
        draw.text((746, y), label, fill=(191, 204, 220, 220), font=load_font(20, bold=False))
        draw.line((746, y + 35, 978, y + 35), fill=(191, 204, 220, 82), width=2)
    draw_review_label(draw, spec["variant_id"])
    draw_footer_lock(draw)
    return image


def draw_cover_crop(image: Any, spec: dict[str, Any]) -> Any:
    image = add_linear_scrim(image, top=122, bottom=184)
    draw = ImageDraw.Draw(image)
    accent = rgb(spec["accent"])
    title_font = fit_font(draw, spec["headline"], 148, 980, bold=True)
    draw.text((48, 148), spec["headline"], fill=(248, 248, 244, 248), font=title_font)
    draw.text((54, 294), spec["subhead"], fill=accent, font=load_font(34, bold=True))
    draw.rectangle((54, 342, 390, 352), fill=rgb(spec["accent_2"]))
    draw.rounded_rectangle((54, 1056, 438, 1166), radius=6, fill=(6, 8, 12, 182))
    draw.text((78, 1078), "MEDAL FRAME", fill=accent, font=load_font(30, bold=True))
    draw.text((80, 1122), "Tight crop review", fill=(229, 235, 244, 225), font=load_font(22, bold=False))
    draw_review_label(draw, spec["variant_id"])
    draw_footer_lock(draw)
    return image


def draw_motion_stack(source: Any, image: Any, spec: dict[str, Any]) -> Any:
    background = image.filter(ImageFilter.GaussianBlur(10))
    background = ImageEnhance.Brightness(background.convert("RGB")).enhance(0.68).convert("RGBA")
    sharp = crop_to_canvas(source, [0.59, 0.47], 1.18).convert("RGBA")
    sharp = apply_grade(sharp, {"brightness": 0.92, "contrast": 1.22, "color": 0.98, "sharpness": 1.12, "vignette": 0.18})
    mask = Image.new("L", (CANVAS["width"], CANVAS["height"]), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((116, 118, 988, 1142), radius=12, fill=255)
    shadow = Image.new("RGBA", background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((138, 142, 1010, 1166), radius=12, fill=(0, 0, 0, 145))
    image = Image.alpha_composite(background, shadow)
    image.paste(sharp, (0, 0), mask)
    image = add_linear_scrim(image, bottom=180)
    draw = ImageDraw.Draw(image)
    draw.rectangle((92, 1112, 650, 1124), fill=rgb(spec["accent"]))
    draw.text((92, 1148), spec["headline"], fill=(248, 250, 252, 255), font=load_font(64, bold=True))
    draw.text((96, 1224), spec["subhead"], fill=(220, 228, 239, 230), font=load_font(25, bold=False))
    draw_review_label(draw, spec["variant_id"])
    draw_footer_lock(draw)
    return image


def draw_news_cover(image: Any, spec: dict[str, Any]) -> Any:
    image = add_linear_scrim(image, top=150, bottom=172)
    draw = ImageDraw.Draw(image)
    accent = rgb(spec["accent_2"])
    draw.rectangle((0, 0, CANVAS["width"], 116), fill=(5, 7, 10, 198))
    draw.text((42, 36), "HER SPORTS NEWS", fill=(246, 248, 250, 245), font=load_font(38, bold=True))
    draw.text((760, 44), "APCS048", fill=accent, font=load_font(26, bold=True))
    title_font = fit_font(draw, spec["headline"], 72, 910, bold=True)
    draw.text((54, 1078), spec["headline"], fill=(248, 248, 244, 248), font=title_font)
    draw.text((58, 1160), spec["subhead"], fill=accent, font=load_font(29, bold=True))
    draw_review_label(draw, spec["variant_id"])
    draw_footer_lock(draw)
    return image


def draw_result_poster(image: Any, spec: dict[str, Any]) -> Any:
    image = add_linear_scrim(image, top=112, bottom=210, left=120)
    draw = ImageDraw.Draw(image)
    accent = rgb(spec["accent"])
    draw.rounded_rectangle((54, 812, 514, 1116), radius=8, fill=(5, 7, 10, 194), outline=accent, width=2)
    draw.text((82, 854), spec["headline"], fill=(247, 248, 250, 255), font=load_font(74, bold=True))
    draw.text((86, 944), "3 - 2", fill=accent, font=load_font(96, bold=True))
    draw.text((90, 1054), spec["subhead"], fill=(225, 232, 241, 230), font=load_font(22, bold=False))
    draw.rectangle((54, 754, 390, 764), fill=accent)
    draw_review_label(draw, spec["variant_id"])
    draw_footer_lock(draw)
    return image


def render_variant(source: Any, spec: dict[str, Any], output_path: Path) -> dict[str, Any]:
    base = crop_to_canvas(source, spec["crop_center"], float(spec["zoom"]))
    image = apply_grade(base, dict(spec["grade"]))
    if spec["treatment"] == "hero_lockup":
        image = draw_hero_lockup(image, spec)
    elif spec["treatment"] == "score_rail":
        image = draw_score_rail(image, spec)
    elif spec["treatment"] == "cover_crop":
        image = draw_cover_crop(image, spec)
    elif spec["treatment"] == "motion_stack":
        image = draw_motion_stack(source, image, spec)
    elif spec["treatment"] == "news_cover":
        image = draw_news_cover(image, spec)
    elif spec["treatment"] == "result_poster":
        image = draw_result_poster(image, spec)
    else:
        raise ValueError(f"Unknown treatment: {spec['treatment']}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "PNG")
    with Image.open(output_path) as rendered:
        dimensions = [int(rendered.width), int(rendered.height)]
    return {
        "candidate_id": "APCS048",
        "entity_name": "Jordan Thompson",
        "variant_id": spec["variant_id"],
        "variant_name": spec["variant_name"],
        "output_png_path": output_path.as_posix(),
        "dimensions": dimensions,
        "visual_direction": spec["visual_direction"],
        "source_use": spec["source_use"],
        "rubric_verdict": spec["rubric_verdict"],
        "carry_forward_recommendation": spec["carry_forward_recommendation"],
        "notes": spec["notes"],
        "review_only": True,
    }


def create_contact_sheet(output_dir: Path, rows: list[dict[str, Any]]) -> Path:
    require_pillow()
    sheet = Image.new("RGB", (1680, 2140), (12, 15, 20))
    draw = ImageDraw.Draw(sheet)
    draw.text((42, 34), "APCS048 VISUAL RESCUE V1", fill=(246, 248, 251), font=load_font(42, bold=True))
    draw.text((44, 88), "Review-only quarantine rescue. Source-led crops; no boxed stage; no asset approval.", fill=(197, 207, 220), font=load_font(25, bold=False))
    positions = [(42, 146), (596, 146), (1150, 146), (42, 1110), (596, 1110), (1150, 1110)]
    thumb_size = (500, 625)
    for row, (x, y) in zip(rows, positions):
        with Image.open(row["output_png_path"]).convert("RGB") as image:
            thumb = image.resize(thumb_size, getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1))
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + thumb_size[0], y + thumb_size[1]), outline=(83, 93, 108), width=2)
        draw.text((x, y + 648), row["variant_name"], fill=(246, 248, 251), font=load_font(24, bold=True))
        draw.text((x, y + 684), row["rubric_verdict"], fill=(231, 196, 82), font=load_font(20, bold=False))
        wrapped = wrap_text(str(row["visual_direction"]), 40)
        draw.text((x, y + 720), wrapped, fill=(190, 201, 214), font=load_font(18, bold=False), spacing=4)
    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path, "PNG")
    return path


def wrap_text(text: str, width: int) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines[:4])


def write_csv_local(path: Path, rows: list[dict[str, Any]]) -> None:
    rendered_rows = []
    for row in rows:
        rendered_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "entity_name": row["entity_name"],
                "variant_id": row["variant_id"],
                "variant_name": row["variant_name"],
                "output_png_path": row["output_png_path"],
                "visual_direction": row["visual_direction"],
                "source_use": row["source_use"],
                "rubric_verdict": row["rubric_verdict"],
                "carry_forward_recommendation": row["carry_forward_recommendation"],
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rendered_rows)


def build_rubric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "failed_route": {
            "route": "PR_527_boxed_3d_stage_pasted_photo_panel",
            "verdict": "fail_do_not_polish",
            "why": [
                "The boxed stage makes the athlete photo feel pasted into a toy set instead of leading the asset.",
                "Generic gray-floor staging reads like a renderer demo, not premium HSD sports editorial.",
                "The stage geometry competes with the championship image and wastes 4:5 social space.",
                "Compliance and proof framing should support review, not become the visual concept.",
            ],
        },
        "rescue_criteria": [
            "source image must dominate the composition",
            "crop must feel confident at 1080x1350",
            "negative space must be useful for score or story copy",
            "typography must be controlled and secondary to the athlete/source image",
            "no conference-stage mockup, gray floor grid, toy set, or pasted-photo panel",
            "review-only label must be clear without dominating the design",
        ],
        "best_candidate": "rescue_01_gold_confetti_hero",
        "best_score_template_candidate": "rescue_02_score_window_right",
        "rows": [
            {
                "variant_id": row["variant_id"],
                "variant_name": row["variant_name"],
                "rubric_verdict": row["rubric_verdict"],
                "carry_forward_recommendation": row["carry_forward_recommendation"],
                "blunt_read": row["notes"],
            }
            for row in rows
        ],
    }


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{row['variant_id']}` | {row['variant_name']} | {row['rubric_verdict']} | {row['carry_forward_recommendation']} | `{row['dimensions'][0]}x{row['dimensions'][1]}` |"
        for row in manifest["variant_rows"]
    )
    return f"""# APCS048 Visual Rescue V1

Status: `{manifest['status']}`
Version: `{manifest['version']}`
Generated: `{manifest['generated_at_utc']}`

This packet is review-only and quarantine-only. It uses the already available APCS048 quarantine source/reference as local input, creates six 1080x1350 source-led editorial/social rescue directions, and does not fetch, download, approve, move protected assets, create a publish-ready lane, or publish.

## Source

- Source present: `{manifest['source_image_present']}`
- Source path: `{manifest['source_image_path']}`
- Source dimensions: `{manifest['source_dimensions']}`
- Source SHA256: `{manifest['source_image_sha256']}`

## Blunt Visual Rubric

The PR #527 boxed 3D stage / pasted photo panel route fails this rescue rubric. It reads like a demo stage with a photo stuck on it, not like premium HSD sports editorial. Do not polish that direction.

The strongest carry-forward candidate is `rescue_01_gold_confetti_hero` because it lets the actual championship photo lead, keeps the confetti energy, and leaves enough controlled lower-frame space for story or score copy. The most operational score-template candidate is `rescue_02_score_window_right`.

## Outputs

- Contact sheet: `{manifest['contact_sheet_path']}`
- Manual review intake: `{manifest['manual_visual_review_intake_path']}`
- Rubric JSON: `{manifest['visual_rubric_path']}`

| Variant | Name | Rubric verdict | Carry-forward recommendation | Dimensions |
| --- | --- | --- | --- | --- |
{rows}

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
- source_fetching=false
- source_auto_enabled=false
- protected_asset_moves=false
- publish_ready=false
- publishing=false
- paid_apis=false
- approval marker files written=false
"""


def image_dimensions(path: Path) -> list[int]:
    require_pillow()
    with Image.open(path) as image:
        return [int(image.width), int(image.height)]


def build_packet(*, source_image: Path, output_dir: Path, head_commit: str = "") -> dict[str, Any]:
    require_pillow()
    source_image = source_image.resolve(strict=False)
    if not source_image.exists() or not source_image.is_file():
        raise FileNotFoundError(f"APCS048 source/reference is inaccessible: {source_image}")
    output_dir = output_dir.resolve(strict=False)
    renders_dir = output_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(source_image).convert("RGB") as source:
        source_dimensions = [int(source.width), int(source.height)]
        rows = []
        for spec in build_variant_specs():
            output_path = renders_dir / spec["filename"]
            rows.append(render_variant(source, spec, output_path))
    contact_sheet_path = create_contact_sheet(output_dir, rows)
    intake_path = output_dir / CSV_NAME
    write_csv_local(intake_path, rows)
    rubric = build_rubric(rows)
    rubric_path = write_json(output_dir / RUBRIC_NAME, rubric, sort_keys=True)
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "apcs048_visual_rescue_ready",
        "repo_head": head_commit,
        "candidate_id": "APCS048",
        "entity_name": "Jordan Thompson",
        "output_dir": output_dir.as_posix(),
        "source_image_path": source_image.as_posix(),
        "source_image_present": True,
        "source_dimensions": source_dimensions,
        "source_image_sha256": sha256_file(source_image),
        "contact_sheet_path": contact_sheet_path.as_posix(),
        "manual_visual_review_intake_path": intake_path.as_posix(),
        "visual_rubric_path": Path(rubric_path).as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "output_dimensions": dict(CANVAS),
        "variant_count": len(rows),
        "variant_rows": rows,
        "failed_prior_route": "PR_527_boxed_3d_stage_pasted_photo_panel",
        "failed_prior_route_verdict": "fail_do_not_polish",
        "strongest_carry_forward_variant": "rescue_01_gold_confetti_hero",
        "score_template_variant": "rescue_02_score_window_right",
        "review_only": True,
        "quarantine_review_lock": True,
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build APCS048 review-only visual rescue packet.")
    parser.add_argument(
        "--source-image",
        default="",
        help="Optional explicit APCS048 quarantine source/reference. Without this, repo-local quarantine candidates are checked.",
    )
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        source_image=resolve_source_image(args.source_image or None),
        output_dir=resolve_output_dir(args.output_dir or None),
        head_commit=args.head_commit,
    )
    print(json.dumps({"version": VERSION, "status": manifest["status"], "variant_count": manifest["variant_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
