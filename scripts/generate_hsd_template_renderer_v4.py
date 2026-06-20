from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

VERSION = "v4.2-phase6e-clean-plate-near-post-ready"
ROOT = Path(".")
CONTRACT_ROOT = Path("config/graphics/v4/approved")
SPECS = CONTRACT_ROOT / "wnba"
CLEAN_ROOT = Path("assets/graphics/v4/approved/clean_plates/wnba")
MASK_ROOT = Path("assets/graphics/v4/approved/dynamic_masks/wnba")
PUBLIC_ROOT = Path("assets/graphics/v4/approved/public_mockups/wnba")
RESULTS_CONTRACT = Path("results_contract_v2.csv")
TODAY_FINALS = Path("today_final_results.csv")
TEAM_LOGOS = Path("data/asset_registry/wnba/team_logos.csv")
TEAM_ALIASES = Path("data/asset_registry/wnba/team_aliases.csv")
TEAMS = Path("data/asset_registry/wnba/teams.csv")
PLAYER_ROOT = Path("outputs/latest/production_graphics_director/graphics_variant_packs/with_players")
OUT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4")
RENDERS = OUT / "renders"
FIXTURES = OUT / "fixtures"
MANIFEST_CSV = OUT / "hsd_template_renderer_v4_manifest.csv"
MANIFEST_JSON = OUT / "hsd_template_renderer_v4_manifest.json"
REPORT_MD = OUT / "hsd_template_renderer_v4_report.md"
REPORT_JSON = OUT / "hsd_template_renderer_v4_report.json"
CONTACT = OUT / "hsd_template_renderer_v4_contact_sheet.jpg"
ZIP_PATH = OUT / "hsd_template_renderer_v4_renders.zip"

TARGET_TEMPLATES = {
    "hsd_tonight_in_the_w_a",
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_b",
    "hsd_game_recap_final_score_c_story",
}
PLACEHOLDER_TOKENS = {
    "PRIMARY TEAM",
    "SECONDARY TEAM",
    "APPROVED",
    "TEAM LOGO SLOT",
    "PLAYER NAME",
    "SCORE SLOT",
    "00–00",
    "00-00",
    "VENUE NAME",
    "CITY, STATE",
    "COMPETITION NAME",
}
MANIFEST_FIELDS = [
    "item_id", "source_id", "template_id", "platform", "headline", "output_path", "width", "height",
    "variant", "module_mode", "player_assets_used", "player_names", "player_asset_kind", "fixture_only_player_asset",
    "team_logo_count", "team_logo_modes", "clean_plate_path", "clean_plate_sha256", "dynamic_mask_path",
    "dynamic_mask_sha256", "placeholder_layer_count", "zone_overflow_count", "review_only", "near_post_ready_candidate",
    "status", "notes",
]

INK = (241, 238, 229)
MUTED = (192, 188, 178)
GOLD = (222, 161, 38)
GOLD_LIGHT = (247, 203, 84)
ORANGE = (235, 88, 25)
PURPLE = (126, 48, 202)
PINK = (228, 39, 141)
DARK = (3, 4, 7)
PANEL_FILL = (2, 3, 6, 224)
FONT_CACHE: Dict[Tuple[str, int], ImageFont.ImageFont] = {}

FONT_CANDIDATES = {
    "display": [
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-ExtraCondensedBlack.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-CondensedBlack.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    ],
    "score": [
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-ExtraCondensedBlack.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-CondensedBlack.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    ],
    "context": [
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-SemiCondensedBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-CondensedBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
    ],
    "body": [
        "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",
        "/usr/share/fonts/truetype/noto/NotoSansDisplay-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "item"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def spec(template_id: str) -> Dict[str, Any]:
    return read_json(SPECS / f"{template_id}.json")


def zone(template_spec: Dict[str, Any], name: str) -> Tuple[int, int, int, int]:
    value = template_spec["zones"][name]
    return int(value["x"]), int(value["y"]), int(value["w"]), int(value["h"])


def clean_plate_path(template_id: str) -> Path:
    return CLEAN_ROOT / f"{template_id}_clean_plate.png"


def dynamic_mask_path(template_id: str) -> Path:
    return MASK_ROOT / f"{template_id}_dynamic_mask.png"


def ensure_clean_plates() -> None:
    if all(clean_plate_path(template_id).exists() and dynamic_mask_path(template_id).exists() for template_id in TARGET_TEMPLATES):
        return
    from build_hsd_template_clean_plates_v4 import build_all
    report = build_all()
    if report.get("blockers"):
        raise RuntimeError(f"Clean plate build failed: {report['blockers']}")


def font(role: str, size: int) -> ImageFont.ImageFont:
    key = (role, size)
    if key in FONT_CACHE:
        return FONT_CACHE[key]
    for raw in FONT_CANDIDATES.get(role, FONT_CANDIDATES["body"]):
        path = Path(raw)
        if path.exists():
            FONT_CACHE[key] = ImageFont.truetype(path.as_posix(), size=size)
            return FONT_CACHE[key]
    FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def text_bbox(draw: ImageDraw.ImageDraw, text: str, typeface: ImageFont.ImageFont, stroke: int = 0) -> Tuple[int, int, int, int]:
    return draw.textbbox((0, 0), clean(text), font=typeface, stroke_width=stroke)


def text_width(draw: ImageDraw.ImageDraw, text: str, typeface: ImageFont.ImageFont, stroke: int = 0) -> int:
    box = text_bbox(draw, text, typeface, stroke)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, width: int, typeface: ImageFont.ImageFont, max_lines: int) -> List[str]:
    words = clean(text).split()
    output: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or text_width(draw, candidate, typeface) <= width:
            current = candidate
        else:
            output.append(current)
            current = word
            if len(output) >= max_lines - 1:
                break
    if current:
        output.append(current)
    return output[:max_lines]


def fit_font(draw: ImageDraw.ImageDraw, text: str, box: Tuple[int, int, int, int], role: str, start: int, floor: int, max_lines: int = 1, line_gap: int = 4) -> Tuple[ImageFont.ImageFont, List[str]]:
    _, _, width, height = box
    for size in range(start, floor - 1, -2):
        typeface = font(role, size)
        lines = wrap_text(draw, text, width, typeface, max_lines)
        line_height = size + line_gap
        if lines and all(text_width(draw, line, typeface, 1) <= width for line in lines) and line_height * len(lines) <= height:
            return typeface, lines
    typeface = font(role, floor)
    return typeface, wrap_text(draw, text, width, typeface, max_lines)


def texture(base: Tuple[int, int, int], size: Tuple[int, int], seed: int) -> Image.Image:
    width, height = size
    import random
    randomizer = random.Random(seed)
    small = Image.new("RGB", (max(8, width // 8), max(8, height // 8)))
    pixels = []
    for _ in range(small.width * small.height):
        delta = randomizer.randint(-22, 22)
        pixels.append(tuple(max(0, min(255, channel + delta)) for channel in base))
    small.putdata(pixels)
    return small.resize(size, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(0.4))


def draw_textured_text(
    image: Image.Image,
    box: Tuple[int, int, int, int],
    text: str,
    role: str,
    start: int,
    floor: int,
    color: Tuple[int, int, int] = INK,
    max_lines: int = 1,
    align: str = "left",
    stroke: int = 1,
    uppercase: bool = True,
) -> int:
    text = clean(text)
    if uppercase:
        text = text.upper()
    if not text:
        return 0
    x, y, width, height = box
    draw = ImageDraw.Draw(image, "RGBA")
    typeface, lines = fit_font(draw, text, box, role, start, floor, max_lines)
    line_height = typeface.size + 4
    total_height = line_height * len(lines)
    y_cursor = y + max(0, (height - total_height) // 2)
    overflow = 0
    for line in lines:
        line_width = text_width(draw, line, typeface, stroke)
        if align == "center":
            x_cursor = x + (width - line_width) // 2
        elif align == "right":
            x_cursor = x + width - line_width
        else:
            x_cursor = x
        if x_cursor < x or x_cursor + line_width > x + width or y_cursor + line_height > y + height:
            overflow += 1
        draw.text((x_cursor + 2, y_cursor + 3), line, font=typeface, fill=(0, 0, 0, 175), stroke_width=stroke + 1, stroke_fill=(0, 0, 0, 180))
        glyph_box = typeface.getbbox(line, stroke_width=stroke)
        glyph_width = max(1, glyph_box[2] - glyph_box[0])
        glyph_height = max(1, glyph_box[3] - glyph_box[1])
        local_mask = Image.new("L", (glyph_width + 6, glyph_height + 6), 0)
        local_draw = ImageDraw.Draw(local_mask)
        local_draw.text((3 - glyph_box[0], 3 - glyph_box[1]), line, font=typeface, fill=255, stroke_width=stroke, stroke_fill=255)
        text_texture = texture(color, local_mask.size, seed=sum(ord(character) for character in f"{line}:{role}:{typeface.size}"))
        image.paste(text_texture, (x_cursor + glyph_box[0] - 3, y_cursor + glyph_box[1] - 3), local_mask)
        y_cursor += line_height
    return overflow


def panel(image: Image.Image, box: Tuple[int, int, int, int], outline: Tuple[int, int, int] = GOLD, radius: int = 12, fill: Tuple[int, int, int, int] = PANEL_FILL, width: int = 2) -> None:
    x, y, box_width, box_height = box
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((x + 5, y + 8, x + box_width + 5, y + box_height + 8), radius=radius, fill=(0, 0, 0, 95))
    draw.rounded_rectangle((x, y, x + box_width, y + box_height), radius=radius, fill=fill, outline=(*outline, 230), width=width)
    image.alpha_composite(layer)


def line(image: Image.Image, xy: Tuple[int, int, int, int], color: Tuple[int, int, int] = GOLD, width: int = 2) -> None:
    ImageDraw.Draw(image, "RGBA").line(xy, fill=(*color, 220), width=width)


def icon_clock(draw: ImageDraw.ImageDraw, center: Tuple[int, int], radius: int = 17) -> None:
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=(*GOLD, 255), width=3)
    draw.line((x, y, x, y - 9), fill=(*GOLD, 255), width=3)
    draw.line((x, y, x + 8, y + 4), fill=(*GOLD, 255), width=3)


def icon_tv(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int]) -> None:
    x, y, width, height = box
    draw.rounded_rectangle((x, y, x + width, y + height), radius=3, outline=(*GOLD, 255), width=3)
    draw.line((x + width // 2 - 7, y + height + 5, x + width // 2 + 7, y + height + 5), fill=(*GOLD, 255), width=3)


def icon_star(draw: ImageDraw.ImageDraw, center: Tuple[int, int], radius: int = 18) -> None:
    x, y = center
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        current_radius = radius if index % 2 == 0 else radius * 0.45
        points.append((x + math.cos(angle) * current_radius, y + math.sin(angle) * current_radius))
    draw.polygon(points, outline=(*GOLD, 255))


def icon_chat(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int]) -> None:
    x, y, width, height = box
    draw.rounded_rectangle((x, y, x + width, y + height - 10), radius=10, outline=(*GOLD_LIGHT, 255), width=4)
    draw.polygon([(x + 18, y + height - 12), (x + 28, y + height + 2), (x + 40, y + height - 12)], outline=(*GOLD_LIGHT, 255))
    for offset in [22, 37, 52]:
        draw.ellipse((x + offset, y + 20, x + offset + 6, y + 26), fill=(*GOLD_LIGHT, 255))


def icon_binoculars(draw: ImageDraw.ImageDraw, center: Tuple[int, int], scale: int = 1) -> None:
    x, y = center
    radius = 18 * scale
    draw.ellipse((x - 40 * scale, y - radius, x - 4 * scale, y + radius), outline=(*GOLD_LIGHT, 255), width=4)
    draw.ellipse((x + 4 * scale, y - radius, x + 40 * scale, y + radius), outline=(*GOLD_LIGHT, 255), width=4)
    draw.rectangle((x - 8 * scale, y - 12 * scale, x + 8 * scale, y + 12 * scale), outline=(*GOLD_LIGHT, 255), width=3)


def team_data() -> Tuple[Dict[str, str], Dict[str, str]]:
    aliases: Dict[str, str] = {}
    for row in read_csv(TEAMS):
        team_id = clean(row.get("team_id"))
        for key in ["team_name", "nickname", "city"]:
            if team_id and clean(row.get(key)):
                aliases[norm(row[key])] = team_id
    for row in read_csv(TEAM_ALIASES):
        if clean(row.get("team_id")) and clean(row.get("alias")):
            aliases[norm(row["alias"])] = clean(row["team_id"])
    logos = {clean(row.get("team_id")): clean(row.get("file_path")) for row in read_csv(TEAM_LOGOS) if clean(row.get("team_id"))}
    return aliases, logos


def resolve_team(team: str, aliases: Dict[str, str]) -> str:
    normalized = norm(team)
    if normalized in aliases:
        return aliases[normalized]
    for alias, team_id in aliases.items():
        if alias and (alias in normalized or normalized in alias):
            return team_id
    return ""


def load_logo(team: str, aliases: Dict[str, str], logos: Dict[str, str]) -> Optional[Image.Image]:
    team_id = resolve_team(team, aliases)
    raw = logos.get(team_id, "")
    path = Path(raw) if raw else Path("")
    if not path.exists():
        return None
    try:
        if path.suffix.lower() == ".svg":
            try:
                import cairosvg
                png = OUT / "logo_cache" / f"{team_id}.png"
                png.parent.mkdir(parents=True, exist_ok=True)
                cairosvg.svg2png(url=path.as_posix(), write_to=png.as_posix(), output_width=500, output_height=500)
                return Image.open(png).convert("RGBA")
            except Exception:
                return None
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def short_team(team: str) -> str:
    text = clean(team).upper()
    prefixes = ["GOLDEN STATE ", "LOS ANGELES ", "LAS VEGAS ", "NEW YORK ", "CONNECTICUT ", "WASHINGTON ", "MINNESOTA ", "SEATTLE ", "PHOENIX ", "INDIANA ", "ATLANTA ", "DALLAS "]
    for prefix in prefixes:
        if text.startswith(prefix) and len(text) > len(prefix) + 3:
            return text[len(prefix):]
    return text


def draw_team_asset(image: Image.Image, team: str, box: Tuple[int, int, int, int], aliases: Dict[str, str], logos: Dict[str, str], accent: Tuple[int, int, int]) -> str:
    panel(image, box, accent, 10, (1, 2, 5, 220), 2)
    logo = load_logo(team, aliases, logos)
    x, y, width, height = box
    if logo is not None:
        logo = logo.copy()
        logo.thumbnail((width - 34, height - 34), Image.Resampling.LANCZOS)
        image.alpha_composite(logo, (x + (width - logo.width) // 2, y + (height - logo.height) // 2))
        return "approved_logo"
    draw_textured_text(image, (x + 14, y + 14, width - 28, height - 28), short_team(team), "context", 34, 16, accent, 2, "center")
    return "approved_text_fallback"


def player_index() -> Dict[str, List[Dict[str, str]]]:
    output: Dict[str, List[Dict[str, str]]] = {}
    if not PLAYER_ROOT.exists():
        return output
    for summary in PLAYER_ROOT.glob("*/content_summary.json"):
        payload = read_json(summary)
        players = payload.get("players") or []
        assets = payload.get("player_assets") or []
        for index, player in enumerate(players):
            if not isinstance(player, dict) or index >= len(assets):
                continue
            path = Path(clean(assets[index]))
            if not path.exists():
                continue
            team_id = clean(player.get("team_id"))
            output.setdefault(team_id, []).append({
                "name": clean(player.get("display_name") or player.get("player_name")),
                "team_id": team_id,
                "path": path.as_posix(),
                "asset_kind": clean(player.get("asset_kind") or "headshot"),
                "fixture_only": "false",
            })
    return output


def fixture_player_asset() -> Dict[str, str]:
    source = PUBLIC_ROOT / "01_game_recap_final_score_variant_A_public.png"
    FIXTURES.mkdir(parents=True, exist_ok=True)
    output = FIXTURES / "fixture_player_reference_crop.png"
    if not output.exists():
        image = Image.open(source).convert("RGB")
        crop = image.crop((640, 990, 1080, 1200))
        crop = ImageEnhance.Contrast(crop).enhance(1.08)
        crop.save(output, format="PNG", optimize=True)
    return {
        "name": "FEATURED PLAYER",
        "team_id": "indiana_fever",
        "path": output.as_posix(),
        "asset_kind": "fixture_reference_crop",
        "fixture_only": "true",
    }


def select_player(team: str, aliases: Dict[str, str], index: Dict[str, List[Dict[str, str]]], fixtures: bool = False) -> Optional[Dict[str, str]]:
    team_id = resolve_team(team, aliases)
    players = index.get(team_id) or []
    if players:
        return players[0]
    return fixture_player_asset() if fixtures else None


def paste_player(image: Image.Image, player: Dict[str, str], box: Tuple[int, int, int, int]) -> bool:
    path = Path(clean(player.get("path")))
    if not path.exists():
        return False
    try:
        source = Image.open(path).convert("RGBA")
    except Exception:
        return False
    x, y, width, height = box
    panel(image, box, GOLD, 8, (6, 6, 8, 220), 2)
    alpha = source.getchannel("A")
    if alpha.getbbox() and alpha.getbbox() != (0, 0, source.width, source.height):
        source = source.crop(alpha.getbbox())
        source.thumbnail((width - 12, height - 12), Image.Resampling.LANCZOS)
        image.alpha_composite(source, (x + (width - source.width) // 2, y + height - source.height - 6))
    else:
        placed = ImageOps.fit(source.convert("RGB"), (width - 8, height - 8), method=Image.Resampling.LANCZOS, centering=(0.5, 0.35)).convert("RGBA")
        image.alpha_composite(placed, (x + 4, y + 4))
    return True


def read_rows(fixtures: bool) -> List[Dict[str, Any]]:
    if fixtures:
        return fixture_rows()
    output: List[Dict[str, Any]] = []
    for row in read_csv(RESULTS_CONTRACT):
        if clean(row.get("row_kind")).lower() == "preview" and clean(row.get("league")).upper() == "WNBA":
            output.append({"kind": "preview", **row})
    for row in read_csv(TODAY_FINALS):
        if clean(row.get("status_norm") or row.get("game_state")).lower() == "final":
            output.append({"kind": "final", **row})
    return output


def fixture_rows() -> List[Dict[str, Any]]:
    return [
        {
            "kind": "preview",
            "event_id": "fixture-preview",
            "headline": "Atlanta Dream at Indiana Fever",
            "home_team_name": "Indiana Fever",
            "away_team_name": "Atlanta Dream",
            "time_et": "7:00 PM ET",
            "tv_network": "ION",
            "preview_label": "PREMIUM MATCHUP PREVIEW",
            "debate_question": "WHO HAS THE EDGE TONIGHT?",
            "watch_title": "WATCH POINT",
            "watch_body": "Control the glass. Own the pace. Win the fourth quarter.",
        },
        {
            "kind": "final",
            "event_id": "fixture-final",
            "headline": "Indiana Fever beat Atlanta Dream",
            "winner_team_name": "Indiana Fever",
            "loser_team_name": "Atlanta Dream",
            "score_display": "88-82",
            "league": "WNBA",
            "date": "JUNE 19, 2026",
            "location": "INDIANAPOLIS, IN",
            "competition": "REGULAR SEASON",
            "key_performer": "TOP PERFORMER",
            "stat_points": "24",
            "stat_rebounds": "8",
            "stat_assists": "6",
            "stat_steals": "2",
            "summary": "Late-game execution and defensive pressure decided the finish.",
            "hook": "WHAT CHANGED THE GAME?",
        },
    ]


def score_parts(row: Dict[str, Any]) -> Tuple[str, str]:
    display = clean(row.get("score_display") or row.get("final_score_display"))
    if display:
        parts = re.split(r"[-–—]", display)
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
    return clean(row.get("winner_score") or row.get("score_home")), clean(row.get("loser_score") or row.get("score_away"))


def content_has_placeholder(row: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    for value in row.values():
        text = clean(value).upper()
        for token in PLACEHOLDER_TOKENS:
            if token in text:
                hits.append(token)
    return sorted(set(hits))


def draw_context_tonight(image: Image.Image, row: Dict[str, Any]) -> int:
    box = (82, 538, 916, 64)
    panel(image, box, GOLD, 12, (1, 2, 5, 224), 2)
    draw = ImageDraw.Draw(image, "RGBA")
    icon_clock(draw, (148, 570), 16)
    icon_tv(draw, (401, 553, 36, 24))
    icon_star(draw, (620, 570), 17)
    overflow = 0
    overflow += draw_textured_text(image, (180, 548, 165, 45), clean(row.get("time_et") or row.get("start_time_et") or "TIME TBA"), "context", 27, 18, INK, 1, "left")
    line(image, (360, 548, 360, 592), GOLD, 2)
    overflow += draw_textured_text(image, (450, 548, 120, 45), clean(row.get("tv_network") or "TV TBA"), "context", 24, 17, INK, 1, "left")
    line(image, (580, 548, 580, 592), GOLD, 2)
    overflow += draw_textured_text(image, (650, 548, 310, 45), clean(row.get("preview_label") or "MATCHUP PREVIEW"), "context", 22, 15, INK, 1, "left")
    return overflow


def render_tonight(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str], players: Dict[str, List[Dict[str, str]]], module_mode: str, fixtures: bool) -> Tuple[Image.Image, Dict[str, Any]]:
    template_id = "hsd_tonight_in_the_w_a"
    image = Image.open(clean_plate_path(template_id)).convert("RGBA")
    home = clean(row.get("home_team_name") or row.get("home_team_display"))
    away = clean(row.get("away_team_name") or row.get("away_team_display"))
    overflow = draw_context_tonight(image, row)
    logo_modes = [
        draw_team_asset(image, away, (108, 618, 330, 294), aliases, logos, GOLD),
        draw_team_asset(image, home, (642, 618, 330, 294), aliases, logos, INK),
    ]
    debate = (78, 922, 924, 136)
    panel(image, debate, GOLD_LIGHT, 13, (1, 2, 5, 226), 2)
    draw = ImageDraw.Draw(image, "RGBA")
    icon_chat(draw, (120, 944, 105, 76))
    overflow += draw_textured_text(image, (255, 938, 705, 68), clean(row.get("debate_question") or "WHO HAS THE EDGE TONIGHT?"), "display", 48, 27, GOLD_LIGHT, 1, "center")
    overflow += draw_textured_text(image, (270, 1000, 675, 35), "SOUND OFF IN THE COMMENTS.", "body", 24, 15, INK, 1, "center")
    lower = (78, 1070, 924, 226)
    player = select_player(away, aliases, players, fixtures) if module_mode == "player" else None
    player_used = 0
    player_name = ""
    player_kind = ""
    fixture_only = "false"
    if player:
        panel(image, lower, GOLD_LIGHT, 13, (1, 2, 5, 226), 2)
        photo_box = (96, 1088, 240, 190)
        if paste_player(image, player, photo_box):
            player_used = 1
            player_name = clean(player.get("name"))
            player_kind = clean(player.get("asset_kind"))
            fixture_only = clean(player.get("fixture_only") or "false")
            overflow += draw_textured_text(image, (365, 1100, 580, 54), player_name or "PLAYER FEATURE", "display", 42, 22, GOLD_LIGHT, 1, "left")
            overflow += draw_textured_text(image, (365, 1160, 580, 88), "PLAYER SPOTLIGHT • MATCHUP IMPACT • LATE-GAME EDGE", "body", 28, 17, INK, 2, "left")
    else:
        panel(image, lower, GOLD_LIGHT, 13, (1, 2, 5, 226), 2)
        icon_binoculars(draw, (200, 1180), 1)
        line(image, (300, 1095, 300, 1270), GOLD, 2)
        overflow += draw_textured_text(image, (345, 1090, 600, 62), clean(row.get("watch_title") or "WATCH POINT"), "display", 52, 26, GOLD_LIGHT, 1, "left")
        overflow += draw_textured_text(image, (345, 1155, 600, 105), clean(row.get("watch_body") or "PACE • STARS • LATE-GAME EDGE"), "body", 31, 18, INK, 3, "left", uppercase=False)
    return image, {
        "player_assets_used": player_used,
        "player_names": player_name,
        "player_asset_kind": player_kind,
        "fixture_only_player_asset": fixture_only,
        "team_logo_count": sum(mode == "approved_logo" for mode in logo_modes),
        "team_logo_modes": ";".join(logo_modes),
        "zone_overflow_count": overflow,
    }


def draw_context_final(image: Image.Image, row: Dict[str, Any], story: bool = False) -> int:
    if story:
        box = (38, 352, 854, 82)
        segments = [clean(row.get("date") or row.get("event_date_local") or "DATE TBA"), clean(row.get("location") or "LOCATION TBA"), clean(row.get("competition") or row.get("league") or "WNBA")]
        widths = [230, 270, 260]
    else:
        box = (80, 308, 920, 66)
        segments = [clean(row.get("date") or row.get("event_date_local") or "DATE TBA"), clean(row.get("location") or "LOCATION TBA"), clean(row.get("competition") or row.get("league") or "WNBA")]
        widths = [240, 310, 270]
    panel(image, box, GOLD, 8, (1, 2, 5, 224), 2)
    overflow = 0
    x = box[0] + 26
    for index, (segment, width) in enumerate(zip(segments, widths)):
        overflow += draw_textured_text(image, (x, box[1] + 10, width, box[3] - 20), segment, "context", 22 if not story else 24, 14, INK, 1, "center")
        x += width
        if index < 2:
            line(image, (x + 5, box[1] + 14, x + 5, box[1] + box[3] - 14), GOLD, 2)
            x += 20
    return overflow


def stats_values(row: Dict[str, Any]) -> List[Tuple[str, str]]:
    return [
        (clean(row.get("stat_points")), "PTS"),
        (clean(row.get("stat_rebounds")), "REB"),
        (clean(row.get("stat_assists")), "AST"),
        (clean(row.get("stat_steals")), "STL"),
    ]


def render_final_a(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str]) -> Tuple[Image.Image, Dict[str, Any]]:
    template_id = "hsd_game_recap_final_score_a"
    image = Image.open(clean_plate_path(template_id)).convert("RGBA")
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name"))
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name"))
    score_winner, score_loser = score_parts(row)
    overflow = 0
    context = (24, 184, 1032, 68)
    panel(image, context, GOLD, 8, (1, 2, 5, 222), 2)
    overflow += draw_textured_text(image, (70, 194, 940, 48), f"FINAL • {clean(row.get('league') or 'WNBA')} • {clean(row.get('date') or row.get('event_date_local') or '')}", "context", 24, 15, INK, 1, "center")
    logo_modes = [
        draw_team_asset(image, winner, (92, 302, 260, 300), aliases, logos, GOLD),
        draw_team_asset(image, loser, (92, 692, 260, 270), aliases, logos, MUTED),
    ]
    overflow += draw_textured_text(image, (390, 292, 550, 130), winner, "display", 74, 34, INK, 2, "left")
    line(image, (390, 430, 950, 430), GOLD, 2)
    overflow += draw_textured_text(image, (372, 432, 610, 300), score_winner, "score", 280, 120, INK, 1, "center", 1)
    overflow += draw_textured_text(image, (390, 746, 425, 90), loser, "display", 52, 25, MUTED, 2, "left")
    line(image, (390, 838, 820, 838), MUTED, 2)
    overflow += draw_textured_text(image, (390, 840, 285, 140), score_loser, "score", 132, 62, MUTED, 1, "left")
    performer_panel = (0, 1000, 1080, 196)
    panel(image, performer_panel, GOLD, 0, (2, 3, 6, 232), 2)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((0, 1000, 205, 1196), fill=(7, 7, 8, 235))
    overflow += draw_textured_text(image, (38, 1025, 145, 140), "KEY PERFORMER", "context", 31, 18, GOLD_LIGHT, 2, "left")
    name = clean(row.get("key_performer"))
    overflow += draw_textured_text(image, (235, 1015, 420, 60), name, "display", 42, 23, INK, 1, "left") if name else 0
    stat_list = [(value, label) for value, label in stats_values(row)[:3] if value]
    if stat_list:
        start_x = 235
        for index, (value, label_text) in enumerate(stat_list):
            x = start_x + index * 125
            overflow += draw_textured_text(image, (x, 1075, 95, 70), value, "score", 58, 30, GOLD_LIGHT, 1, "center")
            overflow += draw_textured_text(image, (x, 1144, 95, 34), label_text, "context", 22, 13, INK, 1, "center")
            if index < len(stat_list) - 1:
                line(image, (x + 105, 1085, x + 105, 1175), GOLD, 1)
    takeaway = (0, 1198, 1080, 152)
    panel(image, takeaway, GOLD, 0, (2, 3, 6, 232), 2)
    draw.rectangle((0, 1198, 205, 1350), fill=(7, 7, 8, 235))
    overflow += draw_textured_text(image, (38, 1220, 145, 110), "THE TAKEAWAY", "context", 31, 18, GOLD_LIGHT, 2, "left")
    overflow += draw_textured_text(image, (235, 1215, 805, 118), clean(row.get("summary") or row.get("hook")), "body", 29, 17, INK, 3, "left", uppercase=False)
    return image, {
        "player_assets_used": 0,
        "player_names": "",
        "player_asset_kind": "",
        "fixture_only_player_asset": "false",
        "team_logo_count": sum(mode == "approved_logo" for mode in logo_modes),
        "team_logo_modes": ";".join(logo_modes),
        "zone_overflow_count": overflow,
    }


def render_final_b(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str], players: Dict[str, List[Dict[str, str]]], fixtures: bool) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
    template_id = "hsd_game_recap_final_score_b"
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name"))
    player = select_player(winner, aliases, players, fixtures)
    if player is None:
        return None, {"route_decision": "downgraded_to_final_a_missing_player"}
    image = Image.open(clean_plate_path(template_id)).convert("RGBA")
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name"))
    score_winner, score_loser = score_parts(row)
    overflow = draw_context_final(image, row, False)
    logo_modes = [
        draw_team_asset(image, winner, (28, 385, 176, 170), aliases, logos, GOLD),
        draw_team_asset(image, loser, (28, 916, 176, 170), aliases, logos, MUTED),
    ]
    overflow += draw_textured_text(image, (225, 390, 450, 150), winner, "display", 76, 34, INK, 2, "left")
    line(image, (225, 550, 675, 550), GOLD, 2)
    overflow += draw_textured_text(image, (25, 558, 650, 335), score_winner, "score", 285, 120, GOLD_LIGHT, 1, "center")
    overflow += draw_textured_text(image, (225, 910, 400, 80), loser, "display", 49, 24, MUTED, 2, "left")
    overflow += draw_textured_text(image, (225, 990, 210, 100), score_loser, "score", 95, 48, MUTED, 1, "left")
    player_box = (700, 390, 342, 505)
    if not paste_player(image, player, player_box):
        return None, {"route_decision": "downgraded_to_final_a_unreadable_player"}
    stats_panel = (700, 900, 342, 192)
    panel(image, stats_panel, GOLD, 0, (2, 3, 6, 236), 2)
    overflow += draw_textured_text(image, (710, 908, 322, 45), clean(row.get("key_performer") or player.get("name")), "context", 25, 15, INK, 1, "center")
    stat_list = [(value, label) for value, label in stats_values(row)[:3] if value]
    for index, (value, label_text) in enumerate(stat_list):
        x = 712 + index * 104
        overflow += draw_textured_text(image, (x, 956, 90, 70), value, "score", 60, 28, GOLD_LIGHT, 1, "center")
        overflow += draw_textured_text(image, (x, 1025, 90, 38), label_text, "context", 21, 13, INK, 1, "center")
    takeaway = (28, 1116, 1016, 192)
    panel(image, takeaway, GOLD, 7, (2, 3, 6, 236), 2)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon([(65, 1168), (105, 1168), (135, 1193), (105, 1218), (65, 1218), (95, 1193)], fill=(*GOLD_LIGHT, 255))
    overflow += draw_textured_text(image, (160, 1135, 840, 65), clean(row.get("headline")), "display", 42, 24, INK, 2, "left")
    overflow += draw_textured_text(image, (160, 1200, 840, 80), clean(row.get("summary")), "body", 27, 16, INK, 3, "left", uppercase=False)
    return image, {
        "route_decision": "rendered_final_b_with_player",
        "player_assets_used": 1,
        "player_names": clean(player.get("name")),
        "player_asset_kind": clean(player.get("asset_kind")),
        "fixture_only_player_asset": clean(player.get("fixture_only") or "false"),
        "team_logo_count": sum(mode == "approved_logo" for mode in logo_modes),
        "team_logo_modes": ";".join(logo_modes),
        "zone_overflow_count": overflow,
    }


def render_final_c(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str]) -> Tuple[Image.Image, Dict[str, Any]]:
    template_id = "hsd_game_recap_final_score_c_story"
    template_spec = spec(template_id)
    image = Image.open(clean_plate_path(template_id)).convert("RGBA")
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name"))
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name"))
    score_winner, score_loser = score_parts(row)
    overflow = 0
    context = zone(template_spec, "context_row")
    panel(image, context, GOLD, 8, (1, 2, 5, 228), 2)
    segments = [
        clean(row.get("date") or row.get("event_date_local") or "DATE TBA"),
        clean(row.get("location") or "LOCATION TBA"),
        clean(row.get("competition") or row.get("league") or "WNBA"),
    ]
    segment_width = (context[2] - 80) // 3
    x_cursor = context[0] + 20
    for index, segment in enumerate(segments):
        overflow += draw_textured_text(image, (x_cursor, context[1] + 10, segment_width, context[3] - 20), segment, "context", 25, 14, INK, 1, "center")
        x_cursor += segment_width
        if index < 2:
            line(image, (x_cursor + 5, context[1] + 14, x_cursor + 5, context[1] + context[3] - 14), GOLD, 2)
            x_cursor += 20

    primary_panel = (56, 466, 968, 370)
    panel(image, primary_panel, GOLD, 8, (2, 3, 6, 232), 2)
    primary_logo = zone(template_spec, "primary_logo_slot")
    primary_team = zone(template_spec, "primary_team")
    primary_score = zone(template_spec, "primary_score")
    logo_modes = [draw_team_asset(image, winner, primary_logo, aliases, logos, GOLD)]
    overflow += draw_textured_text(image, primary_team, winner, "display", 58, 27, INK, 2, "left")
    line(image, (primary_team[0], primary_team[1] + primary_team[3] - 8, primary_team[0] + primary_team[2], primary_team[1] + primary_team[3] - 8), GOLD, 2)
    overflow += draw_textured_text(image, primary_score, score_winner, "score", 245, 110, INK, 1, "center")

    secondary_panel = (56, 804, 968, 350)
    panel(image, secondary_panel, GOLD, 8, (2, 3, 6, 232), 2)
    secondary_logo = zone(template_spec, "secondary_logo_slot")
    secondary_team = zone(template_spec, "secondary_team")
    secondary_score = zone(template_spec, "secondary_score")
    logo_modes.append(draw_team_asset(image, loser, secondary_logo, aliases, logos, MUTED))
    overflow += draw_textured_text(image, secondary_team, loser, "display", 54, 25, MUTED, 2, "left")
    line(image, (secondary_team[0], secondary_team[1] + secondary_team[3] - 8, secondary_team[0] + secondary_team[2], secondary_team[1] + secondary_team[3] - 8), GOLD, 2)
    overflow += draw_textured_text(image, secondary_score, score_loser, "score", 220, 100, INK, 1, "center")

    performer = (56, 1184, 968, 210)
    panel(image, performer, GOLD, 8, (2, 3, 6, 235), 2)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((56, 1184, 160, 1394), fill=(*GOLD_LIGHT, 244))
    overflow += draw_textured_text(image, (66, 1195, 84, 188), "KEY PERFORMER", "context", 26, 14, DARK, 2, "center")
    overflow += draw_textured_text(image, (190, 1195, 790, 54), clean(row.get("key_performer")), "display", 44, 23, INK, 1, "left")
    stat_list = [(value, label) for value, label in stats_values(row) if value]
    for index, (value, label_text) in enumerate(stat_list):
        x = 190 + index * 190
        overflow += draw_textured_text(image, (x, 1250, 145, 82), value, "score", 68, 32, GOLD_LIGHT, 1, "center")
        overflow += draw_textured_text(image, (x, 1330, 145, 40), label_text, "context", 22, 13, INK, 1, "center")

    hook = (56, 1410, 968, 230)
    panel(image, hook, GOLD, 8, (2, 3, 6, 235), 2)
    overflow += draw_textured_text(image, (75, 1420, 175, 200), "?", "score", 160, 85, GOLD_LIGHT, 1, "center")
    overflow += draw_textured_text(image, (270, 1430, 710, 105), clean(row.get("hook") or "WHAT CHANGED THE GAME?"), "display", 50, 24, INK, 2, "left")
    overflow += draw_textured_text(image, (270, 1540, 710, 55), "DROP YOUR TAKE IN THE COMMENTS.", "context", 26, 14, INK, 1, "left")
    overflow += draw_textured_text(image, (100, 1810, 880, 55), "WOMEN'S SPORTS. ALL DAY. EVERY DAY.", "context", 27, 15, GOLD_LIGHT, 1, "center")
    return image, {
        "player_assets_used": 0,
        "player_names": "",
        "player_asset_kind": "",
        "fixture_only_player_asset": "false",
        "team_logo_count": sum(mode == "approved_logo" for mode in logo_modes),
        "team_logo_modes": ";".join(logo_modes),
        "zone_overflow_count": overflow,
    }


def make_manifest_item(row: Dict[str, Any], template_id: str, platform: str, variant: str, module_mode: str, output: Path, image: Image.Image, meta: Dict[str, Any]) -> Dict[str, Any]:
    plate = clean_plate_path(template_id)
    mask = dynamic_mask_path(template_id)
    placeholders = content_has_placeholder(row)
    placeholder_count = len(placeholders)
    return {
        "item_id": f"{clean(row.get('event_id') or row.get('event_uid'))}::{platform}::{template_id}::{module_mode}",
        "source_id": clean(row.get("event_id") or row.get("event_uid")),
        "template_id": template_id,
        "platform": platform,
        "headline": clean(row.get("headline")),
        "output_path": output.as_posix(),
        "width": image.width,
        "height": image.height,
        "variant": variant,
        "module_mode": module_mode,
        "player_assets_used": int(meta.get("player_assets_used") or 0),
        "player_names": clean(meta.get("player_names")),
        "player_asset_kind": clean(meta.get("player_asset_kind")),
        "fixture_only_player_asset": clean(meta.get("fixture_only_player_asset") or "false"),
        "team_logo_count": int(meta.get("team_logo_count") or 0),
        "team_logo_modes": clean(meta.get("team_logo_modes")),
        "clean_plate_path": plate.as_posix(),
        "clean_plate_sha256": sha256(plate),
        "dynamic_mask_path": mask.as_posix(),
        "dynamic_mask_sha256": sha256(mask),
        "placeholder_layer_count": placeholder_count,
        "zone_overflow_count": int(meta.get("zone_overflow_count") or 0),
        "review_only": "true",
        "near_post_ready_candidate": "true" if placeholder_count == 0 and int(meta.get("zone_overflow_count") or 0) == 0 and clean(meta.get("fixture_only_player_asset") or "false") != "true" else "false",
        "status": "rendered_near_post_ready_review",
        "notes": clean(meta.get("route_decision") or "Phase 6E clean-plate render. Human visual approval required."),
    }


def save_render(image: Image.Image, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output, format="PNG", optimize=True)


def build_contact(items: List[Dict[str, Any]]) -> None:
    if not items:
        return
    columns = 3
    cell_width = 340
    cell_height = 490
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGB", (columns * cell_width + 40, rows * cell_height + 85), (242, 242, 242))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 22), "HSD Template Renderer v4.2 Phase 6E — Clean Plate Near-Post-Ready Proof", fill=(20, 20, 20))
    for index, item in enumerate(items):
        path = Path(clean(item.get("output_path")))
        if not path.exists():
            continue
        render = Image.open(path).convert("RGB")
        render.thumbnail((300, 400), Image.Resampling.LANCZOS)
        column = index % columns
        row_index = index // columns
        x = 20 + column * cell_width + (300 - render.width) // 2
        y = 60 + row_index * cell_height
        sheet.paste(render, (x, y))
        label_x = 20 + column * cell_width
        draw.text((label_x, y + 408), f"{item['template_id']} • {item['platform']} • {item['module_mode']}", fill=(20, 20, 20))
        draw.text((label_x, y + 430), clean(item.get("headline"))[:44], fill=(80, 80, 80))
        draw.text((label_x, y + 450), f"logos={item['team_logo_modes']} player={item['player_assets_used']} near={item['near_post_ready_candidate']}", fill=(80, 80, 80))
    sheet.save(CONTACT, quality=92)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    ensure_clean_plates()
    aliases, logos = team_data()
    players = player_index()
    rows = read_rows(args.fixtures)
    if not rows:
        rows = fixture_rows()
        args.fixtures = True
    shutil.rmtree(RENDERS, ignore_errors=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    manifest: List[Dict[str, Any]] = []
    errors: List[str] = []
    for row in rows:
        try:
            if clean(row.get("kind")) == "preview":
                for module_mode in ["watch_point", "player"]:
                    if module_mode == "player" and select_player(clean(row.get("away_team_name")), aliases, players, args.fixtures) is None:
                        continue
                    for platform in ["ig_feed", "threads"]:
                        image, meta = render_tonight(row, aliases, logos, players, module_mode, args.fixtures)
                        output = RENDERS / platform / f"{slug(row.get('headline'))}__tonight_a__{module_mode}.png"
                        save_render(image, output)
                        manifest.append(make_manifest_item(row, "hsd_tonight_in_the_w_a", platform, "A", module_mode, output, image, meta))
            elif clean(row.get("kind")) == "final":
                for platform in ["ig_feed", "threads"]:
                    image_a, meta_a = render_final_a(row, aliases, logos)
                    output_a = RENDERS / platform / f"{slug(row.get('headline'))}__final_a.png"
                    save_render(image_a, output_a)
                    manifest.append(make_manifest_item(row, "hsd_game_recap_final_score_a", platform, "A", "logos_only", output_a, image_a, meta_a))
                image_b, meta_b = render_final_b(row, aliases, logos, players, args.fixtures)
                if image_b is not None:
                    output_b = RENDERS / "ig_feed" / f"{slug(row.get('headline'))}__final_b__with_player.png"
                    save_render(image_b, output_b)
                    manifest.append(make_manifest_item(row, "hsd_game_recap_final_score_b", "ig_feed", "B", "with_player", output_b, image_b, meta_b))
                image_c, meta_c = render_final_c(row, aliases, logos)
                output_c = RENDERS / "stories" / f"{slug(row.get('headline'))}__final_c_story.png"
                save_render(image_c, output_c)
                manifest.append(make_manifest_item(row, "hsd_game_recap_final_score_c_story", "stories", "C", "vertical_quick_final", output_c, image_c, meta_c))
        except Exception as exc:
            errors.append(f"{clean(row.get('headline'))}: {type(exc).__name__}: {exc}")
    write_csv(MANIFEST_CSV, manifest, MANIFEST_FIELDS)
    payload = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "near_post_ready_gate_required": True,
        "renderer_cutover_allowed": False,
        "clean_plate_mode": True,
        "fixture_mode": bool(args.fixtures),
        "placeholder_layer_policy": "zero_allowed",
        "target_templates": sorted(TARGET_TEMPLATES),
        "rendered_count": len(manifest),
        "near_post_ready_candidates": sum(item.get("near_post_ready_candidate") == "true" for item in manifest),
        "errors": errors,
        "items": manifest,
    }
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    build_contact(manifest)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in manifest:
            path = Path(item["output_path"])
            if path.exists():
                archive.write(path, path.relative_to(OUT.parent).as_posix())
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_MD.write_text("\n".join([
        "# HSD Template Renderer v4.2 Phase 6E",
        "",
        f"Version: `{VERSION}`",
        f"Rendered: `{len(manifest)}`",
        f"Near-post-ready candidates: `{payload['near_post_ready_candidates']}`",
        f"Errors: `{len(errors)}`",
        "",
        "Renderer v4.2 uses generated clean plates and dynamic masks. Flattened mockup placeholders are not rendering layers.",
        "All outputs remain review-only and require human visual approval before any production cutover.",
        "",
    ]), encoding="utf-8")
    print(json.dumps({
        "version": VERSION,
        "rendered": len(manifest),
        "near_post_ready_candidates": payload["near_post_ready_candidates"],
        "errors": errors,
        "out": OUT.as_posix(),
    }, indent=2))
    return 2 if args.strict and (errors or not manifest) else 0


if __name__ == "__main__":
    raise SystemExit(main())
