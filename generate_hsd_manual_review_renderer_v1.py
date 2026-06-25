from __future__ import annotations

import base64
import json
import os
import re
import shutil
import csv
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from hsd_run_io import output_path, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except Exception:  # pragma: no cover - validated by runtime status report
    Image = None
    ImageDraw = None
    ImageFilter = None
    ImageFont = None


VERSION = "hsd-manual-review-renderer-v1.4.1-hsd-final-score-readable-polish"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
OUT_DIR = output_path(HANDOFF_DIR_NAME)
OUT_PREVIEW = OUT_DIR / "draft_preview.png"
OUT_REVIEW_DRAFTS = OUT_DIR / "review_drafts"
OUT_REPORT = output_path("manual_review_renderer_report.md")
OUT_MANIFEST = output_path("manual_review_renderer_manifest.json")
PROJECT_ROOT = Path(__file__).resolve().parent
REFERENCE_PACK_ID = "templates_hsd_20260625"
REFERENCE_PACK_MANIFEST = PROJECT_ROOT / "config" / "graphics" / "v4" / "template_reference_packs_v1.json"
REFERENCE_SPEC_ROOT = PROJECT_ROOT / "config" / "graphics" / "v4" / "reference_specs" / REFERENCE_PACK_ID
REFERENCE_PUBLIC_ROOT = PROJECT_ROOT / "assets" / "graphics" / "v4" / "approved" / "public_mockups"
REFERENCE_LAYOUT_ROOT = PROJECT_ROOT / "assets" / "graphics" / "v4" / "approved" / "layout_references"
REFERENCE_BRAND_ROOT = PROJECT_ROOT / "assets" / "graphics" / "v4" / "approved" / "brand"
TEAM_ALIASES_CSV = PROJECT_ROOT / "data" / "asset_registry" / "wnba" / "team_aliases.csv"
TEAM_LOGOS_CSV = PROJECT_ROOT / "data" / "asset_registry" / "wnba" / "team_logos.csv"

FORMAT_SPECS = [
    {"format_id": "ig_feed_4x5", "filename": "draft_preview_ig_feed.png", "width": 1080, "height": 1350, "primary": True},
    {"format_id": "ig_story_9x16", "filename": "draft_preview_story.png", "width": 1080, "height": 1920, "primary": False},
    {"format_id": "square_feed_1x1", "filename": "draft_preview_square.png", "width": 1080, "height": 1080, "primary": False},
]

REFERENCE_FINAL_SCORE_FORMATS = {
    "ig_feed_4x5": {
        "reference_family_key": "wnba_final_score_tonight",
        "reference_template_id": "hsd_game_recap_final_score_a",
        "reference_spec_path": "config/graphics/v4/reference_specs/templates_hsd_20260625/wnba_final_score_tonight/hsd_game_recap_final_score_a.json",
        "reference_public_mockup_path": "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/01_game_recap_final_score_variant_A_public.png",
        "reference_layout_path": "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/02_game_recap_final_score_variant_A_layout_reference.png",
        "reference_exact_format_match": True,
        "reference_derivation": "exact_imported_reference_spec",
    },
    "ig_story_9x16": {
        "reference_family_key": "wnba_final_score_tonight",
        "reference_template_id": "hsd_game_recap_final_score_c_story",
        "reference_spec_path": "config/graphics/v4/reference_specs/templates_hsd_20260625/wnba_final_score_tonight/hsd_game_recap_final_score_c_story.json",
        "reference_public_mockup_path": "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/05_game_recap_final_score_variant_C_story_public.png",
        "reference_layout_path": "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/06_game_recap_final_score_variant_C_story_layout_reference.png",
        "reference_exact_format_match": True,
        "reference_derivation": "exact_imported_reference_spec",
    },
    "square_feed_1x1": {
        "reference_family_key": "wnba_final_score_tonight",
        "reference_template_id": "hsd_game_recap_final_score_a",
        "reference_spec_path": "config/graphics/v4/reference_specs/templates_hsd_20260625/wnba_final_score_tonight/hsd_game_recap_final_score_a.json",
        "reference_public_mockup_path": "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/01_game_recap_final_score_variant_A_public.png",
        "reference_layout_path": "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/02_game_recap_final_score_variant_A_layout_reference.png",
        "reference_exact_format_match": False,
        "reference_derivation": "square_review_draft_derived_from_imported_4x5_layout",
    },
}

PALETTE = {
    "ink": (248, 250, 255),
    "deep": (13, 20, 35),
    "navy": (22, 48, 79),
    "blue": (35, 92, 148),
    "cyan": (54, 183, 196),
    "gold": (232, 186, 72),
    "paper": (248, 246, 241),
    "paper_2": (255, 255, 255),
    "line": (218, 222, 230),
    "muted": (93, 102, 118),
    "red": (190, 39, 54),
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def repo_root() -> Path:
    return Path.cwd().resolve()


def project_path(raw: Any) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def input_handoff_candidates() -> List[Path]:
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / HANDOFF_DIR_NAME)
    return candidates


def find_handoff_dir() -> Path | None:
    for candidate in input_handoff_candidates():
        if (candidate / "handoff_manifest.json").exists():
            return candidate
    return None


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def copy_handoff_to_output(src: Path) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dest = OUT_DIR / item.name
        if item.resolve() == dest.resolve():
            continue
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


REFERENCE_FONT_CACHE: Dict[Tuple[str, int], Any] = {}


def font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def reference_font(role: str, size: int):
    if ImageFont is None:
        return None
    key = (role, size)
    if key in REFERENCE_FONT_CACHE:
        return REFERENCE_FONT_CACHE[key]
    candidates = {
        "display": [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialnb.ttf",
            "C:/Windows/Fonts/bahnschrift.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ],
        "score": [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialnb.ttf",
            "C:/Windows/Fonts/seguisb.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "context": [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/bahnschrift.ttf",
        ],
        "body": [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
    }
    for raw in candidates.get(role, candidates["body"]):
        try:
            path = Path(raw)
            if path.exists():
                REFERENCE_FONT_CACHE[key] = ImageFont.truetype(path.as_posix(), size)
                return REFERENCE_FONT_CACHE[key]
        except Exception:
            continue
    REFERENCE_FONT_CACHE[key] = font(size, role != "body")
    return REFERENCE_FONT_CACHE[key]


def resample_filter() -> Any:
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)


def text_size(draw: Any, text: str, fnt: Any) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), clean(text), font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def texture_patch(base: tuple[int, int, int], size: tuple[int, int], seed: int) -> Any:
    width, height = max(1, size[0]), max(1, size[1])
    randomizer = random.Random(seed)
    small = Image.new("RGB", (max(8, width // 7), max(8, height // 7)))
    pixels = []
    for _ in range(small.width * small.height):
        delta = randomizer.randint(-24, 24)
        pixels.append(tuple(max(0, min(255, channel + delta)) for channel in base))
    patch = small.resize((width, height), resample_filter())
    if ImageFilter is not None:
        patch = patch.filter(ImageFilter.GaussianBlur(0.35))
    return patch.convert("RGBA")


def draw_right_text(draw: Any, right: int, y: int, text: str, fnt: Any, fill: tuple[int, int, int]) -> None:
    width, _ = text_size(draw, text, fnt)
    draw.text((right - width, y), text, font=fnt, fill=fill)


def draw_rounded(draw: Any, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    else:  # pragma: no cover - Pillow fallback
        draw.rectangle(box, fill=fill, outline=outline, width=width)


def draw_chip(draw: Any, x: int, y: int, label: str, fill: tuple[int, int, int], text_fill: tuple[int, int, int], size: int = 22) -> int:
    fnt = font(size, True)
    text_w, text_h = text_size(draw, label, fnt)
    pad_x = 18
    pad_y = 9
    draw_rounded(draw, (x, y, x + text_w + pad_x * 2, y + text_h + pad_y * 2), 8, fill)
    draw.text((x + pad_x, y + pad_y - 1), label, font=fnt, fill=text_fill)
    return x + text_w + pad_x * 2 + 10


def wrap_text(draw: Any, text: str, fnt: Any, max_width: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    lines: List[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=fnt)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
            continue
        lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if words and len(lines) == max_lines:
        consumed = " ".join(lines).split()
        if len(consumed) < len(words):
            lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def draw_text_block(draw: Any, xy: tuple[int, int], text: str, fnt: Any, fill: tuple[int, int, int], max_width: int, max_lines: int, line_gap: int) -> int:
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width, max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        bbox = draw.textbbox((x, y), line, font=fnt)
        y = bbox[3] + line_gap
    return y


def choose_template(packet: Dict[str, Any]) -> Dict[str, str]:
    text = " ".join(
        clean(packet.get(key))
        for key in ["template_fit", "title", "copy_headline", "copy_dek", "renderer_family", "template_shape"]
    ).lower()
    if any(token in text for token in ["beat", "defeat", "final", "score", "result"]):
        return {
            "template_id": "hsd_game_recap_final_score_a",
            "template_family": "game_recap_final_score",
            "reference_pack_id": REFERENCE_PACK_ID,
            "reference_family_key": "wnba_final_score_tonight",
            "angle_label": "FINAL",
            "tone": "result",
        }
    if any(token in text for token in ["tonight", "preview", "matchup"]):
        return {
            "template_id": "hsd_matchup_preview_review_v1",
            "template_family": "matchup_preview_card",
            "angle_label": "TONIGHT",
            "tone": "preview",
        }
    return {
        "template_id": "hsd_news_fact_review_v1",
        "template_family": "news_fact_editorial_card",
        "angle_label": "NEWS",
        "tone": "news",
    }


def asset_slots(packet: Dict[str, Any], template: Dict[str, str]) -> List[Dict[str, str]]:
    requirement = clean(packet.get("asset_requirement")) or "No player asset required; use HSD brand treatment and verified source text only."
    asset_cue = clean(packet.get("asset_cue")) or "asset_review_not_required"
    slots = [
        {
            "slot_id": "primary_photo",
            "status": "not_required_for_review_draft" if "no player asset" in requirement.lower() else "operator_asset_review_required",
            "requirement": requirement,
        },
        {
            "slot_id": "brand_treatment",
            "status": "rendered_locally",
            "requirement": "HSD editorial treatment, draft watermark, and source-safe text only.",
        },
        {
            "slot_id": "source_evidence",
            "status": "manual_review_required",
            "requirement": clean(packet.get("source_artifact")) or "Open source proof before approval.",
        },
        {
            "slot_id": "asset_cue",
            "status": asset_cue,
            "requirement": "Asset readiness cue copied into the renderer manifest for operator review.",
        },
    ]
    score = parse_final_score(packet)
    if score and clean(template.get("reference_pack_id")) == REFERENCE_PACK_ID:
        aliases, logos = team_registry()
        for slot_id, team_name in [("primary_team_logo", score.get("winner")), ("secondary_team_logo", score.get("loser"))]:
            result = load_team_logo(clean(team_name), aliases, logos)
            status = clean(result.get("status")) or "logo_review_required"
            requirement_note = "Approved WNBA logo slot from Templates-hsd reference pack; do not invent or replace identity."
            if status != "approved_logo":
                requirement_note += " Human review must confirm this logo asset before any later production use."
            slots.append(
                {
                    "slot_id": slot_id,
                    "status": status,
                    "requirement": requirement_note,
                    "asset_path": clean(result.get("path")),
                    "blocker": clean(result.get("blocker")),
                    "render_method": clean(result.get("render_method")),
                    "team": clean(team_name),
                }
            )
    return slots


def score_parts(packet: Dict[str, Any]) -> tuple[str, str]:
    headline = clean(packet.get("copy_headline")) or clean(packet.get("title"))
    dek = clean(packet.get("copy_dek"))
    text = f"{headline} {dek}"
    if "," in text and any(char.isdigit() for char in text):
        return headline, dek
    return headline, dek or "Verified update ready for operator review."


def parse_final_score(packet: Dict[str, Any]) -> Dict[str, str]:
    headline = clean(packet.get("copy_headline")) or clean(packet.get("title"))
    dek = clean(packet.get("copy_dek"))
    combined = f"{headline}. {dek}"
    score_match = re.search(r"([A-Z][A-Za-z .'-]+?)\s+(\d{2,3})\s*,\s*([A-Z][A-Za-z .'-]+?)\s+(\d{2,3})", combined)
    if not score_match:
        return {}
    team_a = clean(score_match.group(1))
    score_a = clean(score_match.group(2))
    team_b = clean(score_match.group(3))
    score_b = clean(score_match.group(4))
    try:
        winner = team_a if int(score_a) >= int(score_b) else team_b
        loser = team_b if winner == team_a else team_a
        winner_score = score_a if winner == team_a else score_b
        loser_score = score_b if winner == team_a else score_a
    except Exception:
        winner, loser, winner_score, loser_score = team_a, team_b, score_a, score_b
    verb = "beat"
    headline_match = re.search(r"(.+?)\s+(beat|defeated|tops|over)\s+(.+)", headline, re.IGNORECASE)
    if headline_match:
        winner = clean(headline_match.group(1))
        loser = clean(headline_match.group(3))
        verb = clean(headline_match.group(2)).lower()
    return {
        "winner": winner,
        "loser": loser,
        "winner_score": winner_score,
        "loser_score": loser_score,
        "verb": verb,
    }


def reference_pack_summary() -> Dict[str, Any]:
    manifest = read_json(REFERENCE_PACK_MANIFEST)
    packs = manifest.get("packs") if isinstance(manifest.get("packs"), list) else []
    pack = next((item for item in packs if isinstance(item, dict) and clean(item.get("pack_id")) == REFERENCE_PACK_ID), {})
    guardrails = pack.get("guardrails") if isinstance(pack.get("guardrails"), dict) else {}
    return {
        "pack_id": REFERENCE_PACK_ID,
        "status": clean(pack.get("status")) or clean(manifest.get("status")) or "reference_only",
        "purpose": clean(pack.get("purpose")) or "Canonical HSD visual quality references.",
        "renderer_cutover_allowed": bool(manifest.get("renderer_cutover_allowed")),
        "auto_render_allowed": bool(manifest.get("auto_render_allowed")),
        "auto_publish_allowed": bool(manifest.get("auto_publish_allowed")),
        "paid_api_required": bool(manifest.get("paid_api_required")),
        "guardrails": {
            "reference_only": guardrails.get("reference_only") is not False,
            "publish_ready": guardrails.get("publish_ready") is True,
            "auto_approval": guardrails.get("auto_approval") is True,
            "auto_render": guardrails.get("auto_render") is True,
            "auto_publish": guardrails.get("auto_publish") is True,
            "paid_apis": guardrails.get("paid_apis") is True,
        },
    }


def reference_for_format(format_spec: Dict[str, Any], template: Dict[str, str]) -> Dict[str, Any]:
    if clean(template.get("reference_pack_id")) != REFERENCE_PACK_ID:
        return {}
    reference = dict(REFERENCE_FINAL_SCORE_FORMATS.get(clean(format_spec.get("format_id")), {}))
    if not reference:
        return {}
    reference["reference_pack_id"] = REFERENCE_PACK_ID
    for key in ["reference_spec_path", "reference_public_mockup_path", "reference_layout_path"]:
        path = project_path(reference.get(key))
        reference[f"{key}_exists"] = path.exists()
    return reference


def load_reference_spec(reference: Dict[str, Any]) -> Dict[str, Any]:
    path = project_path(reference.get("reference_spec_path"))
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def zone_box(template_spec: Dict[str, Any], name: str) -> Tuple[int, int, int, int]:
    zones = template_spec.get("zones") if isinstance(template_spec.get("zones"), dict) else {}
    zone = zones.get(name) if isinstance(zones.get(name), dict) else {}
    return int(zone.get("x", 0)), int(zone.get("y", 0)), int(zone.get("w", 0)), int(zone.get("h", 0))


def draw_reference_text(
    image: Any,
    box: Tuple[int, int, int, int],
    text: str,
    role: str,
    start_size: int,
    min_size: int,
    fill: tuple[int, int, int],
    *,
    max_lines: int = 1,
    align: str = "left",
    uppercase: bool = True,
    stroke: int = 0,
    stroke_fill: tuple[int, int, int] = (0, 0, 0),
    line_gap: int = 5,
) -> int:
    if ImageDraw is None:
        return 0
    draw = ImageDraw.Draw(image)
    x, y, w, h = box
    prepared = clean(text).upper() if uppercase else clean(text)
    if not prepared:
        return 0
    chosen = reference_font(role, min_size)
    lines: List[str] = [prepared]
    for size in range(start_size, min_size - 1, -2):
        candidate = reference_font(role, size)
        candidate_lines = wrap_text(draw, prepared, candidate, w, max_lines)
        line_height = size + line_gap
        if candidate_lines and line_height * len(candidate_lines) <= h and all(text_size(draw, line, candidate)[0] <= w for line in candidate_lines):
            chosen = candidate
            lines = candidate_lines
            break
    line_height = getattr(chosen, "size", min_size) + line_gap
    total_h = line_height * len(lines)
    y_cursor = y + max(0, (h - total_h) // 2)
    overflow = 0
    for line in lines:
        line_w, _ = text_size(draw, line, chosen)
        if align == "center":
            x_cursor = x + (w - line_w) // 2
        elif align == "right":
            x_cursor = x + w - line_w
        else:
            x_cursor = x
        if x_cursor < x or x_cursor + line_w > x + w or y_cursor + line_height > y + h:
            overflow += 1
        if stroke:
            draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        else:
            draw.text((x_cursor + 2, y_cursor + 3), line, font=chosen, fill=(0, 0, 0))
        if role in {"display", "score", "context"} and Image is not None:
            mask = Image.new("L", image.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.text((x_cursor, y_cursor), line, font=chosen, fill=255)
            patch = texture_patch(fill, image.size, sum(ord(character) for character in f"{line}:{role}:{getattr(chosen, 'size', min_size)}"))
            image.alpha_composite(Image.composite(patch, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask))
            draw = ImageDraw.Draw(image)
            if stroke:
                draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            else:
                draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill)
        elif not stroke:
            draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill)
        y_cursor += line_height
    return overflow


def draw_reference_panel(image: Any, box: Tuple[int, int, int, int], outline: tuple[int, int, int], *, fill: tuple[int, int, int, int] = (2, 4, 9, 220), radius: int = 12, width: int = 2) -> None:
    x, y, w, h = box
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((x + 7, y + 10, x + w + 7, y + h + 10), radius=radius, fill=(0, 0, 0, 110))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=(*outline, 235), width=width)
    image.alpha_composite(layer)


def draw_reference_background(image: Any, tone: str = "final") -> None:
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 0, width, height), fill=(3, 5, 10, 255))
    draw.polygon([(int(width * 0.52), 0), (width, 0), (width, int(height * 0.54)), (int(width * 0.35), int(height * 0.22))], fill=(14, 24, 43, 238))
    draw.polygon([(0, int(height * 0.58)), (int(width * 0.28), int(height * 0.31)), (int(width * 0.58), height), (0, height)], fill=(10, 20, 38, 235))
    for x in range(-height, width + height, 185):
        draw.line((x, height + 80, x + int(height * 0.72), -60), fill=(222, 161, 38, 120), width=3)
    for x in range(-height, width + height, 340):
        draw.line((x, height + 160, x + int(height * 0.58), -30), fill=(37, 99, 163, 90), width=2)
    for y in [int(height * 0.14), int(height * 0.74), int(height * 0.88)]:
        draw.line((30, y, width - 30, y), fill=(222, 161, 38, 105), width=2)
    randomizer = random.Random(width * 17 + height * 31)
    for _ in range(420 if height > 1500 else 290):
        x = randomizer.randrange(0, width)
        y = randomizer.randrange(0, height)
        alpha = randomizer.randrange(18, 76)
        color = (245, 204, 88, alpha) if randomizer.random() < 0.38 else (245, 245, 245, alpha)
        draw.rectangle((x, y, x + randomizer.randrange(1, 3), y + randomizer.randrange(1, 3)), fill=color)
    for cx, cy, rx, ry, alpha in [
        (int(width * 0.20), int(height * 0.16), int(width * 0.55), int(height * 0.25), 38),
        (int(width * 0.90), int(height * 0.72), int(width * 0.46), int(height * 0.24), 26),
        (int(width * 0.72), int(height * 0.08), int(width * 0.24), int(height * 0.10), 34),
    ]:
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer, "RGBA")
        layer_draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(245, 204, 88, alpha))
        if ImageFilter is not None:
            layer = layer.filter(ImageFilter.GaussianBlur(42))
        image.alpha_composite(layer)

def draw_reference_badge(image: Any, template_spec: Dict[str, Any]) -> str:
    badge = template_spec.get("badge") if isinstance(template_spec.get("badge"), dict) else {}
    x = int(badge.get("x", 48))
    y = int(badge.get("y", 42))
    spec_w = int(badge.get("w", 80))
    spec_h = int(badge.get("h", 80))
    canvas_w, canvas_h = image.size
    target = max(spec_w, min(124, int(min(canvas_w, canvas_h) * 0.115)))
    w = h = target
    badge_path = REFERENCE_BRAND_ROOT / clean(badge.get("asset") or "official_hsd_badge_reference.png")
    if badge_path.exists():
        try:
            logo = Image.open(badge_path).convert("RGBA")
            bbox = logo.getbbox()
            if bbox:
                logo = logo.crop(bbox)
            logo.thumbnail((w, h), resample_filter())
            shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow, "RGBA")
            shadow_draw.rounded_rectangle((x + 4, y + 6, x + w + 4, y + h + 6), radius=10, fill=(0, 0, 0, 80))
            if ImageFilter is not None:
                shadow = shadow.filter(ImageFilter.GaussianBlur(3))
            image.alpha_composite(shadow)
            image.alpha_composite(logo, (x + (w - logo.width) // 2, y + (h - logo.height) // 2))
            return badge_path.relative_to(PROJECT_ROOT).as_posix()
        except Exception:
            pass
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((x, y, x + w, y + h), outline=(222, 161, 38, 255), width=3)
    draw_reference_text(image, (x + 8, y + 8, w - 16, h - 16), "HSD", "context", 28, 16, PALETTE["ink"], max_lines=1, align="center")
    return "badge_missing_text_fallback"


def draw_reference_guardrail(image: Any) -> None:
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    label = "DRAFT REVIEW ONLY - NOT APPROVED - NO AUTO-PUBLISH"
    pill_w = min(326, width - 760)
    if pill_w > 180:
        draw.rounded_rectangle((width - pill_w - 50, 76, width - 50, 122), radius=8, fill=(190, 39, 54, 232), outline=(241, 238, 229, 180), width=1)
        draw_reference_text(image, (width - pill_w - 38, 80, pill_w - 24, 36), "DRAFT REVIEW ONLY", "context", 19, 12, PALETTE["ink"], max_lines=1, align="center")
    strip_h = 64
    draw.rectangle((0, height - strip_h, width, height), fill=(190, 39, 54, 244))
    draw_reference_text(image, (24, height - strip_h + 12, width - 48, strip_h - 18), label, "context", 24, 14, PALETTE["ink"], max_lines=1, align="center")


def team_registry() -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    aliases: Dict[str, str] = {}
    for row in read_csv(TEAM_ALIASES_CSV):
        alias = clean(row.get("alias"))
        team_id = clean(row.get("team_id"))
        if alias and team_id:
            aliases[norm(alias)] = team_id
    logos: Dict[str, Dict[str, str]] = {}
    for row in read_csv(TEAM_LOGOS_CSV):
        team_id = clean(row.get("team_id"))
        if team_id:
            logos[team_id] = row
    return aliases, logos


def resolve_team_id(team: str, aliases: Dict[str, str]) -> str:
    normalized = norm(team)
    if normalized in aliases:
        return aliases[normalized]
    for alias, team_id in aliases.items():
        if alias and (alias in normalized or normalized in alias):
            return team_id
    return ""


def short_team(team: str) -> str:
    text = clean(team).upper()
    prefixes = [
        "GOLDEN STATE ",
        "LOS ANGELES ",
        "LAS VEGAS ",
        "NEW YORK ",
        "CONNECTICUT ",
        "WASHINGTON ",
        "MINNESOTA ",
        "SEATTLE ",
        "PHOENIX ",
        "INDIANA ",
        "ATLANTA ",
        "DALLAS ",
        "CHICAGO ",
    ]
    for prefix in prefixes:
        if text.startswith(prefix) and len(text) > len(prefix) + 3:
            return text[len(prefix):]
    return text


def score_margin(score: Dict[str, str]) -> int | None:
    try:
        return max(0, int(score.get("winner_score", "0")) - int(score.get("loser_score", "0")))
    except Exception:
        return None


def game_edge_module(score: Dict[str, str]) -> Dict[str, str]:
    winner = clean(score.get("winner"))
    loser = clean(score.get("loser"))
    margin = score_margin(score)
    if margin is None:
        return {
            "eyebrow": "GAME EDGE",
            "headline": "FINAL RESULT",
            "body": f"{winner} finished ahead of {loser}.",
        }
    if margin <= 4:
        headline = f"{short_team(winner)} SURVIVES"
        body = f"{winner} closed out a one-possession final over {loser}."
    elif margin <= 11:
        headline = f"{short_team(winner)} SEPARATES"
        body = f"{winner} created enough late cushion to hold off {loser}."
    else:
        headline = f"{short_team(winner)} CONTROLS IT"
        body = f"{winner} owned the scoreboard by {margin} and kept {loser} chasing."
    return {"eyebrow": "GAME EDGE", "headline": headline, "body": body}


def review_prompt(score: Dict[str, str]) -> str:
    winner = short_team(clean(score.get("winner")))
    loser = short_team(clean(score.get("loser")))
    margin = score_margin(score)
    if margin is not None and margin <= 4:
        return f"WHAT DECIDED {winner}'S CLOSE?"
    if margin is not None and margin >= 12:
        return f"WHERE DID {winner} TAKE CONTROL?"
    return f"WHAT SWUNG {winner} VS {loser}?"


def logo_candidates(team_id: str, row: Dict[str, str]) -> List[Path]:
    candidates: List[Path] = []
    raw = clean(row.get("file_path"))
    if raw:
        candidates.append(project_path(raw))
    if team_id:
        base = PROJECT_ROOT / "assets" / "leagues" / "wnba" / "teams" / team_id
        candidates.extend([base / "logo.png", base / "logo.svg"])
    seen: set[str] = set()
    unique: List[Path] = []
    for path in candidates:
        key = path.as_posix().lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def rasterize_svg_with_local_browser(svg_path: Path, output_path: Path, size: int = 700) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"status": "blocked", "reason": f"playwright unavailable: {clean(exc)}"}
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        svg_payload = base64.b64encode(svg_path.read_bytes()).decode("ascii")
        svg_uri = f"data:image/svg+xml;base64,{svg_payload}"
        html_doc = f"""
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              html, body {{
                margin: 0;
                width: {size}px;
                height: {size}px;
                background: transparent;
                overflow: hidden;
              }}
              img {{
                width: {size}px;
                height: {size}px;
                object-fit: contain;
                display: block;
              }}
            </style>
          </head>
          <body><img alt="team logo" src={json.dumps(svg_uri)}></body>
        </html>
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=playwright.chromium.executable_path)
            page = browser.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
            page.set_content(html_doc, wait_until="load")
            page.locator("img").wait_for(state="visible", timeout=5000)
            page.screenshot(path=output_path.as_posix(), omit_background=True)
            browser.close()
        image = Image.open(output_path).convert("RGBA")
        if not image.getbbox():
            return {"status": "blocked", "reason": "local browser produced a blank SVG raster."}
        image.save(output_path)
        return {"status": "ok", "path": output_path.as_posix()}
    except Exception as exc:
        return {"status": "blocked", "reason": clean(exc)[:240]}


def load_team_logo(team: str, aliases: Dict[str, str], logos: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    team_id = resolve_team_id(team, aliases)
    row = logos.get(team_id, {})
    approved = clean(row.get("approved")).lower() == "true"
    found_svg_path = ""
    svg_blocker = ""
    for path in logo_candidates(team_id, row):
        if not path.exists():
            continue
        try:
            if path.suffix.lower() == ".svg":
                found_svg_path = path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else path.as_posix()
                import cairosvg

                cache = OUT_DIR / "logo_cache" / f"{team_id or norm(team)}.png"
                cache.parent.mkdir(parents=True, exist_ok=True)
                cairosvg.svg2png(url=path.as_posix(), write_to=cache.as_posix(), output_width=700, output_height=700)
                image = Image.open(cache).convert("RGBA")
                render_path = cache
                render_method = "cairosvg"
            else:
                image = Image.open(path).convert("RGBA")
                render_path = path
                render_method = "source_png"
            return {
                "image": image,
                "team_id": team_id,
                "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else path.as_posix(),
                "render_path": render_path.as_posix(),
                "status": "approved_logo" if approved else "registry_logo_review_required",
                "approved": approved,
                "render_method": render_method,
            }
        except Exception as exc:
            if path.suffix.lower() == ".svg":
                svg_blocker = clean(exc)[:220]
            continue
    if found_svg_path:
        svg_path = project_path(found_svg_path)
        cache = OUT_DIR / "logo_cache" / f"{team_id or norm(team)}_browser.png"
        browser_result = rasterize_svg_with_local_browser(svg_path, cache)
        if browser_result.get("status") == "ok":
            try:
                return {
                    "image": Image.open(cache).convert("RGBA"),
                    "team_id": team_id,
                    "path": found_svg_path,
                    "render_path": cache.as_posix(),
                    "status": "approved_svg_logo_rasterized_for_review" if approved else "svg_logo_rasterized_review_required",
                    "approved": approved,
                    "render_method": "local_browser_svg_to_png",
                }
            except Exception as exc:
                svg_blocker = clean(exc)[:220]
        else:
            svg_blocker = clean(browser_result.get("reason")) or svg_blocker
        return {
            "image": None,
            "team_id": team_id,
            "path": found_svg_path,
            "render_path": "",
            "status": "approved_svg_logo_converter_unavailable" if approved else "svg_logo_converter_unavailable_review_required",
            "approved": approved,
            "blocker": svg_blocker or "SVG converter unavailable in local Python runtime.",
        }
    return {
        "image": None,
        "team_id": team_id,
        "path": "",
        "render_path": "",
        "status": "logo_missing_team_name_placeholder",
        "approved": False,
    }


def draw_team_logo_slot(image: Any, team: str, box: Tuple[int, int, int, int], aliases: Dict[str, str], logos: Dict[str, Dict[str, str]], accent: tuple[int, int, int]) -> Dict[str, Any]:
    draw_reference_panel(image, box, accent, fill=(1, 2, 7, 232), radius=16, width=2)
    x, y, w, h = box
    result = load_team_logo(team, aliases, logos)
    logo = result.get("image")
    if logo is not None:
        logo = logo.copy()
        logo.thumbnail((w - 36, h - 36), resample_filter())
        image.alpha_composite(logo, (x + (w - logo.width) // 2, y + (h - logo.height) // 2))
    else:
        draw_reference_text(image, (x + 18, y + 26, w - 36, h - 70), short_team(team), "context", 34, 18, accent, max_lines=2, align="center")
        draw_reference_text(image, (x + 18, y + h - 58, w - 36, 38), "LOGO REVIEW", "context", 18, 12, PALETTE["ink"], max_lines=1, align="center")
    return {
        "team": clean(team),
        "team_id": clean(result.get("team_id")),
        "status": clean(result.get("status")),
        "approved": bool(result.get("approved")),
        "asset_path": clean(result.get("path")),
        "render_method": clean(result.get("render_method")),
    }


def draw_review_chrome(draw: Any, width: int, height: int, template: Dict[str, str], format_label: str) -> None:
    red = PALETTE["red"]
    gold = PALETTE["gold"]
    blue = PALETTE["blue"]
    ink = PALETTE["ink"]
    draw.rectangle((0, 0, width, 24), fill=blue)
    draw.rectangle((0, 24, width, 34), fill=gold)
    draw_rounded(draw, (54, 70, width - 54, 146), 0, (255, 255, 255), PALETTE["line"], 2)
    draw.text((82, 88), "HER SPORTS DAILY", font=font(30, True), fill=(24, 28, 36))
    draw_right_text(draw, width - 82, 88, "DRAFT REVIEW ONLY", font(28, True), red)
    draw_chip(draw, 82, 162, template["angle_label"], gold, (19, 31, 49), 22)
    draw_chip(draw, 82 + 132, 162, format_label.upper(), (232, 239, 249), PALETTE["blue"], 20)
    draw.rectangle((54, height - 64, width - 54, height - 36), fill=red)
    draw.text((70, height - 62), "NOT APPROVED - NOT PUBLISH READY - AUTO-RENDER OFF - AUTO-PUBLISH OFF", font=font(20, True), fill=ink)


def draw_brand_pattern(draw: Any, width: int, height: int, tone: str) -> None:
    deep = PALETTE["deep"]
    navy = PALETTE["navy"]
    cyan = PALETTE["cyan"]
    gold = PALETTE["gold"]
    draw.rectangle((0, 0, width, height), fill=deep)
    draw.polygon([(width * 0.58, 0), (width, 0), (width, height * 0.42), (width * 0.42, height * 0.18)], fill=navy)
    draw.polygon([(0, height * 0.36), (width * 0.32, height * 0.16), (width * 0.58, height), (0, height)], fill=(18, 39, 65))
    accent = cyan if tone != "result" else gold
    for offset in range(-160, width, 210):
        draw.line((offset, height - 150, offset + 380, 120), fill=accent, width=3)
    for x in range(72, width, 168):
        draw.ellipse((x, height - 310, x + 9, height - 301), fill=(255, 255, 255))


def draw_center_text(draw: Any, center_x: int, y: int, text: str, fnt: Any, fill: tuple[int, int, int]) -> None:
    width, _ = text_size(draw, text, fnt)
    draw.text((center_x - width // 2, y), text, font=fnt, fill=fill)


def fit_text_font(draw: Any, text: str, max_width: int, start_size: int, min_size: int = 28, bold: bool = True) -> Any:
    size = start_size
    while size > min_size:
        fnt = font(size, bold)
        if text_size(draw, text, fnt)[0] <= max_width:
            return fnt
        size -= 3
    return font(min_size, bold)


def draw_score_panel(draw: Any, x: int, y: int, w: int, h: int, team: str, score: str, *, winner: bool) -> None:
    fill = PALETTE["deep"] if winner else (255, 255, 255)
    outline = PALETTE["gold"] if winner else PALETTE["line"]
    text_fill = PALETTE["ink"] if winner else (23, 27, 36)
    muted_fill = PALETTE["gold"] if winner else PALETTE["muted"]
    draw_rounded(draw, (x, y, x + w, y + h), 18, fill, outline, 3)
    draw.text((x + 30, y + 28), "WINNER" if winner else "FINAL", font=font(23, True), fill=muted_fill)
    team_font = fit_text_font(draw, team.upper(), w - 240, 42, 28, True)
    draw.text((x + 30, y + 76), team.upper(), font=team_font, fill=text_fill)
    score_font = font(96 if h >= 180 else 78, True)
    draw_right_text(draw, x + w - 30, y + 48, score, score_font, text_fill)


def square_reference_spec() -> Dict[str, Any]:
    return {
        "template_id": "hsd_game_recap_final_score_a_square_review_derivative",
        "family": "game_recap_final_score",
        "variant": "A-square-review-derivative",
        "format": "square_review",
        "canvas": {"width": 1080, "height": 1080},
        "badge": {"asset": "official_hsd_badge_reference.png", "x": 48, "y": 42, "w": 80, "h": 80},
        "zones": {
            "title": {"x": 60, "y": 108, "w": 960, "h": 150},
            "context_row": {"x": 60, "y": 282, "w": 960, "h": 58},
            "primary_logo_slot": {"x": 70, "y": 376, "w": 190, "h": 190},
            "primary_team": {"x": 292, "y": 386, "w": 330, "h": 92},
            "primary_score": {"x": 642, "y": 350, "w": 360, "h": 235},
            "secondary_logo_slot": {"x": 70, "y": 612, "w": 190, "h": 190},
            "secondary_team": {"x": 292, "y": 636, "w": 330, "h": 86},
            "secondary_score": {"x": 692, "y": 602, "w": 260, "h": 190},
            "key_performer": {"x": 60, "y": 806, "w": 960, "h": 88},
            "hook_takeaway": {"x": 60, "y": 914, "w": 960, "h": 88},
        },
    }


def format_reference_spec(format_spec: Dict[str, Any], reference: Dict[str, Any]) -> Dict[str, Any]:
    if clean(format_spec.get("format_id")) == "square_feed_1x1":
        return square_reference_spec()
    loaded = load_reference_spec(reference)
    canvas = loaded.get("canvas") if isinstance(loaded.get("canvas"), dict) else {}
    if int(canvas.get("width", 0)) == int(format_spec.get("width", 0)) and int(canvas.get("height", 0)) == int(format_spec.get("height", 0)):
        return loaded
    return loaded or square_reference_spec()


def draw_context_divider(image: Any, box: Tuple[int, int, int, int], text: str) -> None:
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line((x, y + h - 6, x + w, y + h - 6), fill=(222, 161, 38, 210), width=3)
    draw_reference_text(image, (x, y, w, h - 12), text, "context", 34, 18, (247, 203, 84), max_lines=1, align="left")
    draw_reference_text(image, (x, y, w, h - 12), "REVIEW DRAFT", "context", 24, 14, (241, 238, 229), max_lines=1, align="right")


def draw_lower_reference_module(image: Any, box: Tuple[int, int, int, int], eyebrow: str, body: str, accent: tuple[int, int, int], *, headline: str = "") -> None:
    x, y, w, h = box
    draw_reference_panel(image, box, accent, fill=(2, 4, 9, 218), radius=14, width=2)
    draw_reference_text(image, (x + 24, y + 12, w - 48, min(34, h - 16)), eyebrow, "context", 24, 14, accent, max_lines=1)
    body_top = y + 48 if h >= 92 else y + 34
    if headline:
        draw_reference_text(
            image,
            (x + 24, body_top, w - 48, min(44, h - 46)),
            headline,
            "display",
            38 if h >= 110 else 28,
            16,
            PALETTE["ink"],
            max_lines=1,
        )
        body_top += 48 if h >= 110 else 34
    draw_reference_text(
        image,
        (x + 24, body_top, w - 48, max(28, y + h - body_top - 14)),
        body,
        "body",
        27 if h >= 100 else 20,
        14,
        PALETTE["ink"],
        max_lines=2,
        uppercase=False,
    )


def draw_reference_final_score_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], format_spec: Dict[str, Any], score: Dict[str, str], reference: Dict[str, Any]) -> None:
    template_spec = format_reference_spec(format_spec, reference)
    width, height = int(format_spec["width"]), int(format_spec["height"])
    aliases, logos = team_registry()

    draw_reference_background(image, "final")
    draw_reference_badge(image, template_spec)

    title_box = zone_box(template_spec, "title")
    title = "GAME RECAP FINAL SCORE"
    if clean(format_spec.get("format_id")) == "ig_story_9x16":
        title = "QUICK FINAL SCORE"
    draw_reference_text(image, title_box, title, "display", 94 if height <= 1350 else 100, 40, PALETTE["ink"], max_lines=2, stroke=2, stroke_fill=(0, 0, 0))

    context_box = zone_box(template_spec, "context_row")
    draw_context_divider(image, context_box, "FINAL / WNBA / SOURCE CHECKED")

    draw_team_logo_slot(image, score["winner"], zone_box(template_spec, "primary_logo_slot"), aliases, logos, (247, 203, 84))
    draw_team_logo_slot(image, score["loser"], zone_box(template_spec, "secondary_logo_slot"), aliases, logos, (37, 99, 163))

    draw_reference_text(image, zone_box(template_spec, "primary_team"), short_team(score["winner"]), "context", 58, 24, PALETTE["ink"], max_lines=2, stroke=1, stroke_fill=(0, 0, 0))
    draw_reference_text(image, zone_box(template_spec, "secondary_team"), short_team(score["loser"]), "context", 46, 22, (204, 210, 222), max_lines=2, stroke=1, stroke_fill=(0, 0, 0))
    draw_reference_text(image, zone_box(template_spec, "primary_score"), score["winner_score"], "score", 238 if height <= 1350 else 254, 88, (247, 203, 84), max_lines=1, align="right", stroke=3, stroke_fill=(0, 0, 0))
    draw_reference_text(image, zone_box(template_spec, "secondary_score"), score["loser_score"], "score", 176 if height <= 1350 else 188, 72, PALETTE["ink"], max_lines=1, align="right", stroke=2, stroke_fill=(0, 0, 0))

    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Free-source evidence ready for human review."
    edge = game_edge_module(score)
    key_box = zone_box(template_spec, "key_performer")
    draw_lower_reference_module(image, key_box, edge["eyebrow"], edge["body"], (247, 203, 84), headline=edge["headline"])

    hook_name = "hook_question" if zone_box(template_spec, "hook_question") != (0, 0, 0, 0) else "hook_takeaway"
    hook_box = zone_box(template_spec, hook_name)
    dek = clean(packet.get("copy_dek"))
    if not dek:
        dek = f"Verified final: {score['winner']} {score['winner_score']}, {score['loser']} {score['loser_score']}."
    prompt = review_prompt(score)
    prompt_body = dek
    if hook_name == "hook_question":
        prompt_body = "Tell us what you saw after reviewing the final."
    draw_lower_reference_module(image, hook_box, "YOUR TAKE", prompt_body, (37, 99, 163), headline=prompt)

    draw_reference_guardrail(image)


def draw_final_score_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any], score: Dict[str, str]) -> None:
    width, height = spec["width"], spec["height"]
    reference = reference_for_format(spec, template)
    if reference:
        draw_reference_final_score_template(image, packet, template, spec, score, reference)
        return
    draw = ImageDraw.Draw(image)
    draw_brand_pattern(draw, width, height, "result")
    draw_review_chrome(draw, width, height, template, clean(spec["format_id"]).replace("_", " "))

    source = clean(packet.get("source_artifact")) or "source proof required"
    confidence = clean(packet.get("source_cue")) or "source review required"
    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Verified source review required."
    is_story = height > 1500
    is_square = height <= 1100

    content_top = 228
    content_bottom = height - 104
    left = 54
    right = width - 54
    card_h = content_bottom - content_top
    draw_rounded(draw, (left, content_top, right, content_bottom), 22, PALETTE["paper"], (255, 255, 255), 2)
    draw.rectangle((left, content_top, left + 22, content_bottom), fill=PALETTE["gold"])

    text_left = 92
    text_right = right - 48
    y = content_top + (58 if not is_square else 44)
    draw.text((text_left, y), "FINAL SCORE", font=font(32, True), fill=PALETTE["blue"])
    draw_right_text(draw, text_right, y, "VERIFIED", font(24, True), PALETTE["muted"])
    y += 60

    hero_font = font(64 if not is_square else 56, True)
    y = draw_text_block(draw, (text_left, y), f"{score['winner']} {score['verb']} {score['loser']}", hero_font, (22, 26, 36), text_right - text_left, 3, 10)
    y += 34

    panel_h = 178 if not is_square else 145
    gap = 18
    draw_score_panel(draw, text_left, y, text_right - text_left, panel_h, score["winner"], score["winner_score"], winner=True)
    y += panel_h + gap
    draw_score_panel(draw, text_left, y, text_right - text_left, panel_h, score["loser"], score["loser_score"], winner=False)
    y += panel_h + (42 if is_story else 30)

    if not is_square:
        note_h = min(260, content_bottom - y - 34)
        if note_h >= 110:
            draw_rounded(draw, (text_left, y, text_right, y + note_h), 0, (255, 255, 255), PALETTE["line"], 2)
            draw.text((text_left + 24, y + 24), "Review evidence", font=font(25, True), fill=(24, 28, 36))
            note_y = y + 70
            evidence = [
                f"Source: {source}",
                f"Confidence: {confidence}",
                f"Context: {context}",
            ]
            for item in evidence:
                note_y = draw_text_block(draw, (text_left + 24, note_y), item, font(22, False), PALETTE["muted"], text_right - text_left - 48, 1, 7)
                note_y += 2
            if is_story:
                callout_top = y + note_h + 56
                callout_bottom = min(content_bottom - 54, callout_top + 300)
                if callout_bottom - callout_top >= 220:
                    draw_rounded(draw, (text_left, callout_top, text_right, callout_bottom), 18, PALETTE["deep"], PALETTE["gold"], 3)
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 34, "FINAL", font(34, True), PALETTE["gold"])
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 86, f"{score['winner_score']} - {score['loser_score']}", font(124, True), PALETTE["ink"])
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 226, "REVIEW ONLY DRAFT", font(25, True), PALETTE["gold"])
    else:
        chip_y = min(y, content_bottom - 74)
        draw_chip(draw, text_left, chip_y, f"SOURCE: {source}".upper(), (232, 239, 249), PALETTE["blue"], 19)
        draw_chip(draw, text_left + 320, chip_y, "REVIEW ONLY", PALETTE["gold"], (19, 31, 49), 19)


def draw_primary_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any]) -> None:
    width, height = spec["width"], spec["height"]
    draw = ImageDraw.Draw(image)
    tone = template["tone"]
    parsed_score = parse_final_score(packet) if tone == "result" else {}
    if parsed_score:
        draw_final_score_template(image, packet, template, spec, parsed_score)
        return

    draw_brand_pattern(draw, width, height, tone)
    draw_review_chrome(draw, width, height, template, clean(spec["format_id"]).replace("_", " "))

    headline, dek = score_parts(packet)
    source = clean(packet.get("source_artifact")) or "source proof required"
    confidence = clean(packet.get("source_cue")) or "source review required"
    asset = clean(packet.get("asset_requirement")) or "No player asset required"
    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Manual source review required before any post."

    card_top = 214
    card_bottom = height - 96
    left = 54
    right = width - 54
    draw_rounded(draw, (left, card_top, right, card_bottom), 18, PALETTE["paper"], (255, 255, 255), 2)
    draw.rectangle((left, card_top, left + 20, card_bottom), fill=PALETTE["gold"] if tone == "result" else PALETTE["cyan"])

    text_left = 88
    text_right = right - 48
    y = card_top + 58
    draw.text((text_left, y), "REVIEW PREVIEW", font=font(28, True), fill=PALETTE["blue"])
    y += 58
    headline_font = font(76 if height >= 1350 else 62, True)
    y = draw_text_block(draw, (text_left, y), headline, headline_font, (23, 27, 36), text_right - text_left, 4, 12)
    y += 22
    draw.line((text_left, y, text_right, y), fill=(203, 206, 211), width=3)
    y += 34
    y = draw_text_block(draw, (text_left, y), dek, font(36 if height >= 1350 else 31, False), (28, 34, 46), text_right - text_left, 5, 10)

    if height >= 1260:
        module_top = max(y + 46, int(height * 0.69))
    else:
        module_top = max(y + 30, int(height * 0.62))
    module_bottom = card_bottom - 42
    draw_rounded(draw, (text_left, module_top, text_right, module_bottom), 0, (255, 255, 255), PALETTE["line"], 2)
    draw.text((text_left + 26, module_top + 26), "Manual render context", font=font(27, True), fill=(24, 28, 36))
    y = module_top + 80
    context_lines = [
        f"Template: {template['template_id']}",
        f"Source: {source}",
        f"Confidence: {confidence}",
        f"Assets: {asset}",
        f"Context: {context}",
    ]
    for item in context_lines:
        max_lines = 2 if item.startswith("Assets:") else 1
        text_font = font(21 if height >= 1350 else 19, False)
        y = draw_text_block(draw, (text_left + 26, y), item, text_font, PALETTE["muted"], text_right - text_left - 52, max_lines, 6)
        y += 3


def render_format(packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for manual review rendering.")
    image = Image.new("RGBA", (spec["width"], spec["height"]), (*PALETTE["deep"], 255))
    draw_primary_template(image, packet, template, spec)
    OUT_REVIEW_DRAFTS.mkdir(parents=True, exist_ok=True)
    output = OUT_REVIEW_DRAFTS / spec["filename"]
    image.save(output)
    if spec.get("primary"):
        image.save(OUT_PREVIEW)
    return output


def render_preview(packet: Dict[str, Any]) -> Dict[str, Any]:
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    template = choose_template(packet)
    outputs = []
    for spec in FORMAT_SPECS:
        output = render_format(packet, template, spec)
        reference = reference_for_format(spec, template)
        row = {
            "format_id": spec["format_id"],
            "path": output.as_posix(),
            "width": spec["width"],
            "height": spec["height"],
            "primary": bool(spec.get("primary")),
            "review_only": True,
            "publish_ready": False,
        }
        if reference:
            row.update(reference)
        outputs.append(row)
    return {
        "template": template,
        "reference_pack": reference_pack_summary() if clean(template.get("reference_pack_id")) == REFERENCE_PACK_ID else {},
        "format_options": outputs,
        "asset_slots": asset_slots(packet, template),
    }


def report_lines(status: str, manifest: Dict[str, Any], preview_path: str, reason: str = "", render_result: Dict[str, Any] | None = None) -> List[str]:
    packet = manifest.get("packet") if isinstance(manifest.get("packet"), dict) else {}
    render_result = render_result or {}
    template = render_result.get("template") if isinstance(render_result.get("template"), dict) else {}
    reference_pack = render_result.get("reference_pack") if isinstance(render_result.get("reference_pack"), dict) else {}
    formats = render_result.get("format_options") if isinstance(render_result.get("format_options"), list) else []
    slots = render_result.get("asset_slots") if isinstance(render_result.get("asset_slots"), list) else []
    lines = [
        "# HSD Manual Review Renderer",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{status}`",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Guardrails",
        "",
        "- Manual-only mode.",
        "- Draft preview is for human review only.",
        "- Does not publish.",
        "- Does not approve the image.",
        "- Does not call paid APIs.",
        "- Does not move files into a publish-ready lane.",
        "",
        "## Output",
        "",
        f"- Preview: `{preview_path or 'not_created'}`",
        f"- Story: `{clean(packet.get('title')) or 'none'}`",
        f"- Template: `{clean(template.get('template_id')) or 'not_selected'}`",
        f"- Template family: `{clean(template.get('template_family')) or 'not_selected'}`",
        f"- Reference pack: `{clean(reference_pack.get('pack_id')) or 'not_used'}`",
        f"- Reason: {reason or 'n/a'}",
        "",
        "## Review Draft Formats",
        "",
    ]
    if formats:
        for item in formats:
            ref = clean(item.get("reference_template_id")) or "none"
            derivation = clean(item.get("reference_derivation")) or "not_reference_packed"
            lines.append(
                f"- `{item.get('format_id')}` | `{item.get('width')}x{item.get('height')}` | `{item.get('path')}` | reference=`{ref}` | derivation=`{derivation}` | publish_ready=`false`"
            )
    else:
        lines.append("- none")
    if formats:
        lines += ["", "## Reference Assets", ""]
        for item in formats:
            if not clean(item.get("reference_template_id")):
                continue
            lines.append(f"- `{item.get('format_id')}` spec: `{clean(item.get('reference_spec_path'))}`")
            lines.append(f"- `{item.get('format_id')}` public mockup: `{clean(item.get('reference_public_mockup_path'))}`")
            lines.append(f"- `{item.get('format_id')}` layout reference: `{clean(item.get('reference_layout_path'))}`")
    lines += ["", "## Asset Slots", ""]
    if slots:
        lines.extend(
            f"- `{item.get('slot_id')}` | `{item.get('status')}` | {clean(item.get('requirement'))}"
            for item in slots
        )
    else:
        lines.append("- none")
    return [
        *lines,
    ]


def main() -> None:
    handoff = find_handoff_dir()
    if not handoff:
        manifest = {
            "version": VERSION,
            "status": "blocked_missing_handoff",
            "preview_path": "",
            "guardrails": {"manual_only": True, "auto_render": False, "auto_publish": False, "approved": False, "paid_apis": False},
        }
        write_json(OUT_MANIFEST, manifest)
        write_text(OUT_REPORT, "\n".join(report_lines("blocked_missing_handoff", {}, "", "render_handoff_top_packet/handoff_manifest.json was not found.")))
        print(json.dumps(manifest, indent=2))
        return

    copy_handoff_to_output(handoff)
    source_manifest = read_json(handoff / "handoff_manifest.json")
    packet = source_manifest.get("packet") if isinstance(source_manifest.get("packet"), dict) else {}
    status = "draft_preview_created"
    reason = ""
    preview = ""
    render_result: Dict[str, Any] = {"template": {}, "format_options": [], "asset_slots": []}
    try:
        render_result = render_preview(packet)
        preview = OUT_PREVIEW.as_posix()
    except Exception as exc:
        status = "blocked_preview_not_created"
        reason = str(exc)

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_handoff_dir": handoff.as_posix(),
        "output_handoff_dir": OUT_DIR.as_posix(),
        "preview_path": preview,
        "packet_id": clean(packet.get("packet_id")),
        "title": clean(packet.get("title")),
        "source_artifact": clean(packet.get("source_artifact")),
        "source_cue": clean(packet.get("source_cue")),
        "source_detail": clean(packet.get("source_detail")),
        "copy_context": clean(packet.get("copy_context")),
        "renderer_mode": "template_driven_review_drafts",
        "selected_template": render_result.get("template", {}),
        "reference_pack": render_result.get("reference_pack", {}),
        "format_options": render_result.get("format_options", []),
        "asset_slots": render_result.get("asset_slots", []),
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_render": False,
            "auto_publish": False,
            "approved": False,
            "paid_apis": False,
            "move_files": False,
            "publish_ready": False,
        },
        "approval_status": "not_approved_human_review_required",
        "reason": reason,
    }
    write_json(OUT_MANIFEST, manifest)
    write_text(OUT_REPORT, "\n".join(report_lines(status, source_manifest, preview, reason, render_result)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
