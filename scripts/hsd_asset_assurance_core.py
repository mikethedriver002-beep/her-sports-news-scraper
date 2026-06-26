from __future__ import annotations

"""Shared, sport-agnostic asset assurance helpers for Her Sports Daily.

The core separates two questions that earlier phases mixed together:

1. Can the renderer always produce a clean, truthful graphic? ``render_safe``
2. Is the exact asset package ready for limited operator handoff? ``live_ready_pre_human``

Missing logos and player images therefore never need to crash rendering. The core
uses clearly labelled HSD-owned fallback assets and records the exact resolution
mode in the manifest. Human visual approval remains mandatory for every live hash.
"""

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

VERSION = "v1.0-phase6m-asset-assurance-core"

RENDER_SAFE_TEAM_MODES = {
    "approved_logo",
    "official_fallback_logo",
    "hsd_team_badge",
}
LIVE_READY_TEAM_MODES = {
    "approved_logo",
    "official_fallback_logo",
}
RENDER_SAFE_PLAYER_MODES = {
    "not_requested",
    "approved_player_asset",
    "fixture_reference_asset",
    "team_spotlight_fallback",
}
LIVE_READY_PLAYER_MODES = {
    "not_requested",
    "approved_player_asset",
    "team_spotlight_fallback",
}

DEFAULT_PRIMARY = "#DFA126"
DEFAULT_SECONDARY = "#080A10"
DEFAULT_TEXT = "#F1EEE5"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any, separator: str = "_") -> str:
    return re.sub(r"[^a-z0-9]+", separator, clean(value).lower()).strip(separator) or "entity"


def as_bool(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def as_int(value: Any) -> int:
    try:
        return int(float(clean(value) or "0"))
    except Exception:
        return 0


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_hex(value: Any, fallback: str) -> str:
    raw = clean(value).lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{6}", raw):
        return f"#{raw.upper()}"
    return fallback


def rgb(value: Any, fallback: str = DEFAULT_PRIMARY) -> Tuple[int, int, int]:
    normalized = normalize_hex(value, fallback).lstrip("#")
    return tuple(int(normalized[index:index + 2], 16) for index in (0, 2, 4))  # type: ignore[return-value]


def image_decodable(path: Path) -> bool:
    """Return True only when an asset can actually be decoded for rendering."""
    if not path.exists() or not path.is_file() or path.stat().st_size <= 100:
        return False
    if path.suffix.lower() == ".svg":
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "<svg" not in text:
                return False
            import cairosvg

            buffer = io.BytesIO()
            cairosvg.svg2png(url=path.as_posix(), write_to=buffer, output_width=64, output_height=64)
            buffer.seek(0)
            with Image.open(buffer) as image:
                image.verify()
            return True
        except Exception:
            return False
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.convert("RGBA")
        return True
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return False


def _font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-CondensedBlack.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDisplay-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for raw in candidates:
        path = Path(raw)
        if path.exists():
            return ImageFont.truetype(path.as_posix(), size=size)
    return ImageFont.load_default()


def _initials(display_name: str, maximum: int = 3) -> str:
    words = [word for word in re.findall(r"[A-Za-z0-9]+", display_name) if word]
    if not words:
        return "HSD"
    if len(words) == 1:
        return words[0][:maximum].upper()
    return "".join(word[0] for word in words[:maximum]).upper()


def _fit_text(draw: ImageDraw.ImageDraw, text: str, width: int, start: int, floor: int, bold: bool = True) -> ImageFont.ImageFont:
    for size in range(start, floor - 1, -2):
        font = _font(size, bold=bold)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= width:
            return font
    return _font(floor, bold=bold)


def generate_team_badge(
    output_path: Path,
    display_name: str,
    *,
    sport_label: str = "HSD",
    primary_hex: str = DEFAULT_PRIMARY,
    secondary_hex: str = DEFAULT_SECONDARY,
    size: int = 512,
) -> Path:
    """Create a clearly labelled HSD-owned team badge, never a fake official logo."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    primary = rgb(primary_hex, DEFAULT_PRIMARY)
    secondary = rgb(secondary_hex, DEFAULT_SECONDARY)
    text_color = rgb(DEFAULT_TEXT, DEFAULT_TEXT)
    image = Image.new("RGBA", (size, size), (*secondary, 255))
    draw = ImageDraw.Draw(image, "RGBA")

    margin = max(20, size // 22)
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=max(24, size // 11),
        fill=(*secondary, 255),
        outline=(*primary, 255),
        width=max(6, size // 48),
    )
    inner = margin * 2
    draw.ellipse((inner, inner, size - inner, size - inner), fill=(*primary, 42), outline=(*primary, 220), width=max(4, size // 64))

    initials = _initials(display_name)
    initials_font = _fit_text(draw, initials, int(size * 0.48), int(size * 0.27), int(size * 0.13), bold=True)
    initials_box = draw.textbbox((0, 0), initials, font=initials_font)
    initials_w = initials_box[2] - initials_box[0]
    initials_h = initials_box[3] - initials_box[1]
    draw.text(((size - initials_w) / 2, size * 0.29 - initials_h / 2), initials, font=initials_font, fill=(*text_color, 255), stroke_width=2, stroke_fill=(*secondary, 255))

    label = clean(display_name).upper() or "TEAM"
    label_font = _fit_text(draw, label, int(size * 0.76), int(size * 0.075), int(size * 0.038), bold=True)
    label_box = draw.textbbox((0, 0), label, font=label_font)
    label_w = label_box[2] - label_box[0]
    draw.text(((size - label_w) / 2, size * 0.69), label, font=label_font, fill=(*text_color, 255))

    owner = f"HSD TEAM BADGE • {clean(sport_label).upper() or 'SPORT'}"
    owner_font = _fit_text(draw, owner, int(size * 0.74), int(size * 0.034), int(size * 0.022), bold=False)
    owner_box = draw.textbbox((0, 0), owner, font=owner_font)
    owner_w = owner_box[2] - owner_box[0]
    draw.text(((size - owner_w) / 2, size * 0.865), owner, font=owner_font, fill=(*primary, 255))

    image.save(output_path, format="PNG", optimize=True)
    return output_path


def generate_individual_nameplate(
    output_path: Path,
    display_name: str,
    *,
    sport_label: str,
    primary_hex: str = DEFAULT_PRIMARY,
    secondary_hex: str = DEFAULT_SECONDARY,
    size: int = 512,
) -> Path:
    """Create a no-portrait identity card for individual sports.

    It is deliberately labelled as an HSD card so it cannot be mistaken for a
    verified athlete photograph.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    primary = rgb(primary_hex, DEFAULT_PRIMARY)
    secondary = rgb(secondary_hex, DEFAULT_SECONDARY)
    image = Image.new("RGBA", (size, size), (*secondary, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    margin = max(20, size // 22)
    draw.rounded_rectangle((margin, margin, size - margin, size - margin), radius=size // 12, fill=(*secondary, 255), outline=(*primary, 255), width=max(6, size // 48))
    draw.ellipse((size * 0.32, size * 0.15, size * 0.68, size * 0.51), fill=(*primary, 48), outline=(*primary, 210), width=max(4, size // 64))
    initials = _initials(display_name, maximum=2)
    initials_font = _fit_text(draw, initials, int(size * 0.25), int(size * 0.20), int(size * 0.10), bold=True)
    ib = draw.textbbox((0, 0), initials, font=initials_font)
    draw.text(((size - (ib[2] - ib[0])) / 2, size * 0.245), initials, font=initials_font, fill=rgb(DEFAULT_TEXT, DEFAULT_TEXT))
    label = clean(display_name).upper() or "ATHLETE"
    label_font = _fit_text(draw, label, int(size * 0.78), int(size * 0.075), int(size * 0.036), bold=True)
    lb = draw.textbbox((0, 0), label, font=label_font)
    draw.text(((size - (lb[2] - lb[0])) / 2, size * 0.62), label, font=label_font, fill=rgb(DEFAULT_TEXT, DEFAULT_TEXT))
    footer = f"HSD {clean(sport_label).upper()} IDENTITY CARD • NO PHOTO"
    footer_font = _fit_text(draw, footer, int(size * 0.78), int(size * 0.032), int(size * 0.020), bold=False)
    fb = draw.textbbox((0, 0), footer, font=footer_font)
    draw.text(((size - (fb[2] - fb[0])) / 2, size * 0.84), footer, font=footer_font, fill=(*primary, 255))
    image.save(output_path, format="PNG", optimize=True)
    return output_path


def resolve_team_asset(
    *,
    sport_id: str,
    entity_id: str,
    display_name: str,
    exact_path: Optional[Path],
    output_root: Path,
    primary_hex: str = DEFAULT_PRIMARY,
    secondary_hex: str = DEFAULT_SECONDARY,
    exact_mode: str = "approved_logo",
) -> Dict[str, Any]:
    if exact_path and image_decodable(exact_path):
        return {
            "sport_id": clean(sport_id),
            "entity_id": clean(entity_id) or slug(display_name),
            "display_name": clean(display_name),
            "resolution_mode": exact_mode,
            "resolved_path": exact_path.as_posix(),
            "render_safe": True,
            "live_ready_pre_human": True,
            "requires_asset_visual_approval": False,
            "reason": "verified_decodable_exact_asset",
        }
    fallback = output_root / slug(sport_id) / "team_badges" / f"{slug(entity_id or display_name)}.png"
    generate_team_badge(
        fallback,
        display_name,
        sport_label=sport_id,
        primary_hex=primary_hex,
        secondary_hex=secondary_hex,
    )
    return {
        "sport_id": clean(sport_id),
        "entity_id": clean(entity_id) or slug(display_name),
        "display_name": clean(display_name),
        "resolution_mode": "hsd_team_badge",
        "resolved_path": fallback.as_posix(),
        "render_safe": image_decodable(fallback),
        "live_ready_pre_human": False,
        "requires_asset_visual_approval": True,
        "reason": "exact_asset_missing_or_undecodable_hsd_badge_generated",
    }


def resolve_player_asset(
    candidate: Optional[Mapping[str, Any]],
    *,
    requested: bool,
    team_name: str = "",
) -> Dict[str, Any]:
    if not requested:
        return {
            "resolution_mode": "not_requested",
            "render_safe": True,
            "live_ready_pre_human": True,
            "requires_asset_visual_approval": False,
            "reason": "player_asset_not_requested",
        }
    candidate = dict(candidate or {})
    path = Path(clean(candidate.get("path"))) if clean(candidate.get("path")) else None
    fixture_only = as_bool(candidate.get("fixture_only"))
    if path and image_decodable(path):
        mode = "fixture_reference_asset" if fixture_only else "approved_player_asset"
        return {
            "resolution_mode": mode,
            "resolved_path": path.as_posix(),
            "display_name": clean(candidate.get("name")),
            "render_safe": True,
            "live_ready_pre_human": not fixture_only,
            "requires_asset_visual_approval": fixture_only,
            "reason": "fixture_reference_only" if fixture_only else "verified_decodable_player_asset",
        }
    return {
        "resolution_mode": "team_spotlight_fallback",
        "resolved_path": "",
        "display_name": "",
        "team_name": clean(team_name),
        "render_safe": True,
        "live_ready_pre_human": True,
        "requires_asset_visual_approval": True,
        "reason": "verified_player_asset_unavailable_routed_to_non_player_team_spotlight",
    }


def split_modes(value: Any) -> List[str]:
    return [clean(part) for part in clean(value).split(";") if clean(part)]


def assurance_from_item(item: Mapping[str, Any]) -> Dict[str, Any]:
    modes = split_modes(item.get("team_logo_modes"))
    team_asset_count = len(modes)
    exact_count = sum(mode in LIVE_READY_TEAM_MODES for mode in modes)
    fallback_count = sum(mode == "hsd_team_badge" for mode in modes)
    team_render_safe = team_asset_count >= 2 and all(mode in RENDER_SAFE_TEAM_MODES for mode in modes)

    requested_module = clean(item.get("requested_module_mode") or item.get("module_mode")).lower()
    effective_module = clean(item.get("module_mode")).lower()
    player_mode = clean(item.get("asset_assurance_player_mode"))
    if not player_mode:
        if requested_module in {"player", "with_player", "with_players", "player_feature"}:
            player_mode = "approved_player_asset" if as_int(item.get("player_assets_used")) >= 1 else "team_spotlight_fallback"
        else:
            player_mode = "not_requested"
    player_render_safe = player_mode in RENDER_SAFE_PLAYER_MODES
    player_live_ready = player_mode in LIVE_READY_PLAYER_MODES and not as_bool(item.get("fixture_only_player_asset"))

    reasons: List[str] = []
    if not team_render_safe:
        reasons.append("team_asset_resolution_not_render_safe")
    if not player_render_safe:
        reasons.append("player_asset_resolution_not_render_safe")
    if as_int(item.get("placeholder_layer_count")) != 0:
        reasons.append("placeholder_layer_present")
    if as_int(item.get("zone_overflow_count")) != 0:
        reasons.append("zone_overflow_present")
    if as_bool(item.get("fixture_only_player_asset")):
        reasons.append("fixture_only_player_asset")

    render_safe = not reasons
    if not render_safe:
        release_lane = "blocked"
    elif fallback_count:
        release_lane = "hsd_badge_review"
    elif player_mode == "team_spotlight_fallback" or effective_module == "team_spotlight_fallback":
        release_lane = "team_spotlight_review"
    else:
        release_lane = "exact_assets"

    live_ready_pre_human = render_safe and exact_count >= 2 and player_live_ready
    live_candidate_eligible = render_safe and not as_bool(item.get("fixture_only_player_asset"))
    requires_visual = release_lane in {"hsd_badge_review", "team_spotlight_review"} or not live_ready_pre_human
    fallback_review_cues = {
        "blocked": "Asset assurance is blocked; do not use this row for review renders until the listed blockers are cleared.",
        "hsd_badge_review": "HSD team badges are review-only stand-ins for missing or undecodable exact logos; they do not approve logo identity or create a publish-ready lane.",
        "team_spotlight_review": "Team spotlight fallback is a non-player review route when verified athlete assets are unavailable; it does not approve athlete identity or photo-first rendering.",
        "exact_assets": "Exact assets are technically render-safe, but human visual QA remains required before any next step.",
    }
    return {
        "asset_assurance_version": VERSION,
        "asset_assurance_status": "passed_render_safe" if render_safe else "blocked_render_safe",
        "asset_assurance_reasons": ";".join(sorted(set(reasons))),
        "asset_render_safe": "true" if render_safe else "false",
        "asset_live_candidate_eligible": "true" if live_candidate_eligible else "false",
        "asset_live_ready_pre_human": "true" if live_ready_pre_human else "false",
        "asset_requires_visual_approval": "true" if requires_visual else "false",
        "asset_release_lane": release_lane,
        "team_asset_count": team_asset_count,
        "team_exact_logo_count": exact_count,
        "team_fallback_badge_count": fallback_count,
        "asset_assurance_player_mode": player_mode,
        "asset_fallback_review_cue": fallback_review_cues.get(release_lane, "Human asset review remains required before any next step."),
    }
