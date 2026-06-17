from __future__ import annotations

import csv
import io
import json
import re
import runpy
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import cairosvg  # type: ignore
except Exception:  # pragma: no cover
    cairosvg = None

VERSION = "v2.4-hsd-quality-core-polish-local-svg-logo-fix-review-only"
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2")
IMG_DIR = OUT_DIR / "renders"
MANIFEST_CSV = OUT_DIR / "hsd_template_renderer_v2_manifest.csv"
MANIFEST_JSON = OUT_DIR / "hsd_template_renderer_v2_manifest.json"
REPORT_MD = OUT_DIR / "hsd_template_renderer_v2_report.md"
ZIP_PATH = OUT_DIR / "hsd_template_renderer_v2_renders.zip"
LOGO_AUDIT_JSON = OUT_DIR / "hsd_template_renderer_v2_logo_audit.json"
LOGO_AUDIT_CSV = OUT_DIR / "hsd_template_renderer_v2_logo_audit.csv"
RENDER_MAP_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping/hsd_template_render_map.json")
RENDER_MAP_SCRIPT = Path("scripts/generate_hsd_template_render_map_v1.py")
CONTRACT = Path("results_contract_v2.csv")
FINALS = Path("today_final_results.csv")
BRAND_POLICY = Path("config/graphics/brand_policy_v1.json")
LOGOS_CSV = Path("data/asset_registry/wnba/team_logos.csv")
TEAMS_CSV = Path("data/asset_registry/wnba/teams.csv")
ALIASES_CSV = Path("data/asset_registry/wnba/team_aliases.csv")
FIELDS = ["item_id", "template_id", "platform", "mode", "headline", "output_path", "width", "height", "status", "review_only", "notes"]
LOGO_FIELDS = ["team", "team_id", "source_path", "status", "note"]

BG = (4, 5, 10)
INK = (248, 249, 252)
MUTED = (162, 170, 184)
GOLD = (232, 185, 78)
ORANGE = (239, 108, 50)
PURPLE = (151, 80, 255)
LOGO_CACHE: Dict[str, Image.Image | None] = {}
FONT_CACHE: Dict[Tuple[int, bool], Any] = {}
LOGO_AUDIT_ROWS: List[Dict[str, str]] = []


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def norm(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key in FONT_CACHE:
        return FONT_CACHE[key]
    choices = []
    if bold:
        choices += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    choices += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in choices:
        if Path(p).exists():
            FONT_CACHE[key] = ImageFont.truetype(p, size)
            return FONT_CACHE[key]
    FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, start: int, floor: int, bold: bool = True):
    size = start
    while size >= floor:
        fnt = font(size, bold)
        if text_w(draw, text, fnt) <= max_w:
            return fnt
        size -= 2
    return font(floor, bold)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    if not words:
        return []
    lines: List[str] = []
    cur = words[0]
    for word in words[1:]:
        test = cur + " " + word
        if text_w(draw, test, fnt) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = word
            if len(lines) >= max_lines - 1:
                break
    lines.append(cur)
    if len(" ".join(lines).split()) < len(words) and lines:
        lines[-1] = lines[-1].rstrip("., ") + "..."
    return lines[:max_lines]


def center(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True) -> None:
    x, y, w, h = box
    fnt = fit(draw, text, w, size, 18, bold)
    b = draw.textbbox((0, 0), text, font=fnt)
    draw.text((x + (w - (b[2] - b[0])) // 2, y + (h - (b[3] - b[1])) // 2), text, font=fnt, fill=fill)


def left(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True, max_lines: int = 2) -> None:
    x, y, w, h = box
    fnt = fit(draw, text, w, size, 22, bold)
    lines = wrap(draw, text, fnt, w, max_lines)
    yy = y + max(0, (h - len(lines) * (fnt.size + 7)) // 2)
    for line in lines:
        draw.text((x, yy), line, font=fnt, fill=fill)
        yy += fnt.size + 7


def rect(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], outline=(255, 255, 255, 72), fill=(255, 255, 255, 10), width=2, radius=18) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=outline, fill=fill, width=width)


def background(size: Tuple[int, int], accent: Tuple[int, int, int], accent2: Tuple[int, int, int]) -> Image.Image:
    # v2.4: no top dots and no foreground crossing lines. Background energy stays behind content.
    w, h = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(int(4 + 10 * t), int(5 + 10 * t), int(10 + 14 * t), 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-420, -220, int(w * .78), int(h * .56)), fill=(*accent, 48))
    gd.ellipse((int(w * .45), int(h * .12), w + 460, int(h * .68)), fill=(*accent2, 36))
    gd.rectangle((0, int(h * .72), w, h), fill=(0, 0, 0, 86))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(48)))
    d.rectangle((0, 0, w, h), outline=(255, 255, 255, 14), width=2)
    return img


def load_badge() -> Image.Image | None:
    policy = load_json(BRAND_POLICY).get("public_logo_policy", {})
    paths = [Path(clean(policy.get("official_public_badge_asset"))), Path(clean(policy.get("current_repo_fallback_asset"))), Path("assets/branding/official_hsd_watermark.png")]
    for path in paths:
        if path.exists():
            try:
                return Image.open(path).convert("RGBA")
            except Exception:
                pass
    return None


def paste_badge(img: Image.Image, badge: Image.Image | None, story: bool = False) -> None:
    if not badge:
        return
    b = badge.copy()
    b.thumbnail((88 if story else 80, 88 if story else 80), Image.LANCZOS)
    img.alpha_composite(b, ((52 if story else 48), (48 if story else 42)))


def team_registries() -> Tuple[Dict[str, str], Dict[str, str]]:
    aliases: Dict[str, str] = {}
    for row in read_csv(TEAMS_CSV):
        tid = row.get("team_id", "")
        for key in ["team_name", "nickname", "city"]:
            if tid and row.get(key):
                aliases[norm(row[key])] = tid
    for row in read_csv(ALIASES_CSV):
        if row.get("team_id") and row.get("alias"):
            aliases[norm(row["alias"])] = row["team_id"]
    logos = {row.get("team_id", ""): row.get("file_path", "") for row in read_csv(LOGOS_CSV) if row.get("team_id")}
    return aliases, logos


def resolve(name: str, aliases: Dict[str, str]) -> str:
    n = norm(name)
    if n in aliases:
        return aliases[n]
    for alias, team_id in aliases.items():
        if alias and alias in n:
            return team_id
    return ""


def audit(team: str, team_id: str, source_path: str, status: str, note: str) -> None:
    LOGO_AUDIT_ROWS.append({"team": clean(team), "team_id": team_id, "source_path": source_path, "status": status, "note": note})


def raster_svg(path: Path) -> Image.Image | None:
    if cairosvg is None:
        return None
    try:
        png = cairosvg.svg2png(bytestring=path.read_bytes(), output_width=512, output_height=512)
        return Image.open(io.BytesIO(png)).convert("RGBA")
    except Exception:
        return None


def open_logo_file(path: Path) -> Image.Image | None:
    if not path.exists():
        return None
    if path.suffix.lower() == ".svg":
        return raster_svg(path)
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def logo_for(name: str, aliases: Dict[str, str], logos: Dict[str, str]) -> Image.Image | None:
    team_id = resolve(name, aliases)
    path_s = clean(logos.get(team_id, ""))
    cache_key = f"{team_id}:{path_s}"
    if cache_key in LOGO_CACHE:
        return LOGO_CACHE[cache_key]
    path = Path(path_s)
    img = open_logo_file(path) if path_s else None
    if img:
        audit(name, team_id, path_s, "loaded", "local png/svg logo rendered")
    else:
        audit(name, team_id, path_s or "", "fallback", "local logo missing or not renderable")
    LOGO_CACHE[cache_key] = img
    return img


def short_team(name: str) -> str:
    n = clean(name).upper()
    for prefix in ["GOLDEN STATE ", "LOS ANGELES ", "LAS VEGAS ", "NEW YORK ", "CONNECTICUT ", "WASHINGTON ", "MINNESOTA ", "SEATTLE ", "PHOENIX ", "INDIANA ", "TORONTO "]:
        if n.startswith(prefix) and len(n) > len(prefix) + 3:
            return n[len(prefix):]
    return n


def team_badge(img: Image.Image, draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], team: str, logo: Image.Image | None, accent=GOLD, dim=False) -> None:
    fill = (7, 8, 13, 226 if not dim else 188)
    outline = (*accent, 210 if not dim else 95)
    rect(draw, box, outline=outline, fill=fill, width=3 if not dim else 2, radius=12)
    x, y, w, h = box
    if logo:
        lg = logo.copy()
        lg.thumbnail((w - 42, h - 42), Image.LANCZOS)
        img.alpha_composite(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2))
    else:
        center(draw, (x + 16, y + 20, w - 32, h - 40), short_team(team), 34 if w < 170 else 42, fill=(accent if not dim else MUTED), bold=True)


def source_index() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in read_csv(CONTRACT) + read_csv(FINALS):
        for key in ["event_id", "dedupe_key", "event_uid", "canonical_key"]:
            if row.get(key):
                out[row[key]] = row
    return out


def event_data(map_row: Dict[str, Any], index: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    sid = clean(map_row.get("source_id"))
    if sid in index:
        return index[sid]
    return index.get(clean(map_row.get("item_id")).split("::")[0], {})


def final_names(row: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name") or row.get("home_team_display") or "PRIMARY TEAM")
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name") or row.get("away_team_display") or "SECONDARY TEAM")
    sh = clean(row.get("score_home") or row.get("home_score"))
    sa = clean(row.get("score_away") or row.get("away_score"))
    home = clean(row.get("home_team_name") or row.get("home_team_display"))
    score = f"{sh}-{sa}" if winner == home and sh and sa else f"{sa}-{sh}" if sh and sa else clean(row.get("score_display") or row.get("final_score_display") or "00-00")
    return winner, loser, score, clean(row.get("league") or row.get("league_norm") or "WNBA"), clean(row.get("event_date_local") or row.get("scheduled_date_local") or "")


def score_parts(score: str) -> Tuple[str, str]:
    parts = re.split(r"[-–—]", clean(score))
    return (parts[0].strip(), parts[1].strip()) if len(parts) >= 2 else (clean(score), "")


def canvas_for(row: Dict[str, Any]) -> Tuple[int, int]:
    return (1080, 1920) if row.get("platform") == "stories" else (1080, 1350)


def render_game_final(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    story = map_row.get("platform") == "stories"
    img = background(canvas_for(map_row), GOLD, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    winner, loser, score, league, date = final_names(src)
    s1, s2 = score_parts(score)
    if story:
        center(d, (86, 105, 908, 120), "GAME RECAP", 100, fill=(255, 255, 255, 34), bold=True)
        center(d, (82, 230, 916, 145), "QUICK FINAL", 118, GOLD, True)
        center(d, (118, 390, 844, 52), f"{league} • {date} • FINAL".upper(), 31, INK, True)
        team_badge(img, d, (64, 508, 262, 262), winner, logo_for(winner, aliases, logos), GOLD)
        left(d, (360, 516, 345, 150), winner.upper(), 66, INK, True, 2)
        center(d, (698, 468, 310, 312), s1, 180, GOLD, True)
        team_badge(img, d, (64, 836, 225, 225), loser, logo_for(loser, aliases, logos), MUTED, dim=True)
        left(d, (360, 852, 332, 120), loser.upper(), 52, MUTED, True, 2)
        if s2:
            center(d, (715, 816, 270, 250), s2, 126, MUTED, True)
        rect(d, (64, 1168, 952, 118), outline=(*GOLD, 170), fill=(0, 0, 0, 128), radius=0)
        center(d, (90, 1178, 900, 92), "KEY TAKEAWAY • FINAL SCORE STORY", 40, INK, True)
        rect(d, (70, 1358, 940, 210), outline=(*GOLD, 115), fill=(0, 0, 0, 118), radius=18)
        center(d, (92, 1395, 896, 135), clean(src.get("summary") or "CLUTCH CLOSEOUT."), 62, GOLD, True)
    else:
        center(d, (76, 56, 928, 210), "GAME RECAP", 132, fill=(255, 255, 255, 28), bold=True)
        center(d, (178, 248, 724, 80), "FINAL SCORE", 64, GOLD, True)
        center(d, (170, 350, 740, 48), f"FINAL • {league} • {date}".upper(), 30, INK, True)
        team_badge(img, d, (54, 462, 258, 258), winner, logo_for(winner, aliases, logos), GOLD)
        left(d, (340, 492, 400, 168), winner.upper(), 86, INK, True, 2)
        center(d, (728, 428, 308, 310), s1, 186, GOLD, True)
        team_badge(img, d, (54, 764, 222, 222), loser, logo_for(loser, aliases, logos), MUTED, dim=True)
        left(d, (340, 793, 382, 120), loser.upper(), 60, MUTED, True, 2)
        if s2:
            center(d, (758, 748, 250, 232), s2, 114, MUTED, True)
        rect(d, (54, 1025, 972, 92), outline=(*GOLD, 170), fill=(0, 0, 0, 132), radius=0)
        center(d, (78, 1034, 924, 72), "KEY TAKEAWAY • FINAL SCORE STORY", 36, INK, True)
        center(d, (88, 1168, 904, 108), clean(src.get("hook") or "STATEMENT WIN."), 62, GOLD, True)
    return img


def render_tonight(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    img = background((1080, 1350), ORANGE, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, False)
    home = clean(src.get("home_team_name") or src.get("home_team_display") or "TEAM ONE")
    away = clean(src.get("away_team_name") or src.get("away_team_display") or "TEAM TWO")
    time = clean(src.get("time_et") or src.get("start_time_et") or src.get("scheduled_time_local") or src.get("status") or "TIME / TV / CONTEXT")
    center(d, (118, 70, 844, 158), "TONIGHT", 126, GOLD, True)
    center(d, (118, 224, 844, 80), "IN THE W", 60, INK, True)
    rect(d, (230, 335, 620, 68), outline=(*GOLD, 150), fill=(0, 0, 0, 116), radius=0)
    center(d, (248, 344, 584, 50), time.upper(), 32, INK, True)
    team_badge(img, d, (44, 448, 320, 320), home, logo_for(home, aliases, logos), GOLD)
    team_badge(img, d, (716, 448, 320, 320), away, logo_for(away, aliases, logos), PURPLE)
    center(d, (370, 455, 340, 106), short_team(home), 60, INK, True)
    center(d, (370, 560, 340, 62), "VS.", 48, GOLD, True)
    center(d, (370, 620, 340, 106), short_team(away), 60, INK, True)
    rect(d, (108, 805, 864, 126), outline=(*GOLD, 185), fill=(*GOLD, 232), radius=0)
    center(d, (135, 815, 810, 106), "WHO NEEDS THIS ONE MORE?", 54, BG, True)
    rect(d, (86, 995, 908, 168), outline=(255, 255, 255, 70), fill=(0, 0, 0, 122), radius=18)
    center(d, (115, 1014, 850, 54), "KEY MATCHUP / WATCH POINT", 36, GOLD, True)
    center(d, (135, 1074, 810, 58), "PACE • STARS • LATE-GAME EDGE", 32, INK, True)
    return img


def final_rows() -> List[Dict[str, str]]:
    return [r for r in read_csv(FINALS) if clean(r.get("status_norm")).lower() == "final" or clean(r.get("game_state")).lower() == "final"]


def render_last_night(map_row: Dict[str, Any], badge, aliases, logos) -> Image.Image:
    tid = clean(map_row.get("template_id"))
    story = clean(map_row.get("platform")) == "stories"
    img = background((1080, 1920) if story else (1080, 1350), PURPLE, ORANGE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    finals = final_rows()[:5]
    center(d, (120, 95 if not story else 132, 840, 120), "LAST NIGHT", 100 if not story else 114, INK, True)
    center(d, (120, 210 if not story else 276, 840, 72), "IN THE W", 50 if not story else 58, GOLD, True)
    center(d, (170, 312 if not story else 400, 740, 44), f"{len(finals)} FINALS. ONE RECAP.", 31, MUTED, True)
    if tid.endswith("c.carousel.v1"):
        rect(d, (90, 430, 900, 300), outline=(*GOLD, 150), fill=(0, 0, 0, 120), radius=24)
        center(d, (120, 462, 840, 112), "FULL RECAP PACKAGE", 58, INK, True)
        center(d, (120, 596, 840, 70), "SWIPE FOR THE BIGGEST FINALS", 32, GOLD, True)
        center(d, (90, 860, 900, 170), "WHICH RESULT MATTERED MOST?", 54, INK, True)
        return img
    start = 395 if not story else 505
    row_h = 150 if not story else 160
    extra = 0
    for i, r in enumerate(finals[:4 if not story else 5]):
        y = start + extra + i * (row_h + 18)
        winner, loser, score, league, date = final_names(r)
        if i == 0 and not story:
            rect(d, (58, y, 964, 235), outline=(*GOLD, 180), fill=(0, 0, 0, 136), radius=20)
            team_badge(img, d, (92, y + 34, 150, 150), winner, logo_for(winner, aliases, logos), GOLD)
            left(d, (270, y + 38, 470, 82), winner.upper(), 48, INK, True, 2)
            center(d, (748, y + 38, 230, 86), score, 56, GOLD, True)
            left(d, (270, y + 126, 470, 58), "FEATURED FINAL", 30, MUTED, True, 1)
            extra += 95
            continue
        rect(d, (70, y, 940, row_h), outline=(*GOLD, 112), fill=(0, 0, 0, 112), radius=16)
        team_badge(img, d, (94, y + 26, 88, 88), winner, logo_for(winner, aliases, logos), GOLD)
        left(d, (205, y + 30, 490, 76), winner.upper(), 36 if not story else 40, INK, True, 2)
        center(d, (720, y + 20, 230, 90), score, 50 if not story else 56, GOLD, True)
    cta_y = 1138 if not story else 1480
    rect(d, (70, cta_y, 940, 120), outline=(*PURPLE, 150), fill=(0, 0, 0, 120), radius=18)
    center(d, (90, cta_y + 12, 900, 94), "WHICH RESULT MATTERED MOST?", 42 if not story else 48, INK, True)
    return img


def render_generic(map_row: Dict[str, Any], badge) -> Image.Image:
    img = background(canvas_for(map_row), PURPLE, GOLD)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, map_row.get("platform") == "stories")
    center(d, (80, 170, 920, 170), clean(map_row.get("template_family") or "HSD TEMPLATE").upper(), 70, INK, True)
    center(d, (80, 390, 920, 150), clean(map_row.get("template_variant") or "REVIEW RENDER"), 46, GOLD, True)
    rect(d, (80, 620, 920, 240), outline=(*GOLD, 150), fill=(0, 0, 0, 105))
    left(d, (120, 650, 840, 180), clean(map_row.get("headline") or "HEADLINE"), 52, INK, True, 3)
    return img


def render_one(map_row: Dict[str, Any], source: Dict[str, str], badge, aliases, logos) -> Image.Image:
    tid = clean(map_row.get("template_id"))
    if tid in {"game_recap_final_score.a.v1", "game_recap_final_score.c.story.v1"}:
        return render_game_final(map_row, source, badge, aliases, logos)
    if tid == "tonight_in_the_w.a.v1":
        return render_tonight(map_row, source, badge, aliases, logos)
    if tid.startswith("last_night_in_the_w"):
        return render_last_night(map_row, badge, aliases, logos)
    return render_generic(map_row, badge)


def main() -> None:
    if not RENDER_MAP_JSON.exists() and RENDER_MAP_SCRIPT.exists():
        runpy.run_path(RENDER_MAP_SCRIPT.as_posix(), run_name="__main__")
    rows = load_json(RENDER_MAP_JSON).get("rows", [])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if IMG_DIR.exists():
        shutil.rmtree(IMG_DIR)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    badge = load_badge()
    aliases, logos = team_registries()
    index = source_index()
    manifest: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        if row.get("status") != "mapped":
            continue
        img = render_one(row, event_data(row, index), badge, aliases, logos)
        out = IMG_DIR / f"{i:02d}_{slug(row.get('platform'))}_{slug(row.get('template_id'))}_{slug(row.get('headline'))}.png"
        img.convert("RGB").save(out, quality=96)
        manifest.append({"item_id": row.get("item_id"), "template_id": row.get("template_id"), "platform": row.get("platform"), "mode": row.get("mode"), "headline": row.get("headline"), "output_path": out.as_posix(), "width": img.size[0], "height": img.size[1], "status": "rendered_review", "review_only": "true", "notes": "Template Renderer v2.4 compile proof. Human review required before publishing."})
    write_csv(MANIFEST_CSV, manifest, FIELDS)
    write_csv(LOGO_AUDIT_CSV, LOGO_AUDIT_ROWS, LOGO_FIELDS)
    payload = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "review_only": True, "rendered_count": len(manifest), "source_render_map": RENDER_MAP_JSON.as_posix(), "logo_audit": LOGO_AUDIT_JSON.as_posix(), "items": manifest}
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOGO_AUDIT_JSON.write_text(json.dumps({"version": VERSION, "generated_at_utc": payload["generated_at_utc"], "rows": LOGO_AUDIT_ROWS}, indent=2), encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for item in manifest:
            p = Path(item["output_path"])
            if p.exists():
                z.write(p, p.relative_to(OUT_DIR.parent).as_posix())
    report = ["# HSD Template Renderer v2.4", "", f"Generated: `{payload['generated_at_utc']}`", f"Version: `{VERSION}`", "", "## Policy", "", "- Review-only compile proof.", "- Free local SVG/PNG logo raster support from the approved registry.", "- Removed top dots and foreground crossing lines.", "- Enlarged Tonight matchup area and simplified lower module row.", "- Uses premium team-name badge fallback only when local logo cannot be rendered.", "- Human review required before publishing.", "", "## Summary", "", f"- Rendered files: `{len(manifest)}`", f"- Logo audit rows: `{len(LOGO_AUDIT_ROWS)}`", f"- Zip: `{ZIP_PATH.as_posix()}`", ""]
    for item in manifest:
        report.append(f"- `{item['template_id']}` | {item['platform']} | {item['headline']}")
    REPORT_MD.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": len(manifest), "logo_audit_rows": len(LOGO_AUDIT_ROWS), "out_dir": OUT_DIR.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
