from __future__ import annotations

import csv
import json
import re
import runpy
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

VERSION = "v2.1-template-polish-review-only"
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2")
IMG_DIR = OUT_DIR / "renders"
MANIFEST_CSV = OUT_DIR / "hsd_template_renderer_v2_manifest.csv"
MANIFEST_JSON = OUT_DIR / "hsd_template_renderer_v2_manifest.json"
REPORT_MD = OUT_DIR / "hsd_template_renderer_v2_report.md"
ZIP_PATH = OUT_DIR / "hsd_template_renderer_v2_renders.zip"
RENDER_MAP_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping/hsd_template_render_map.json")
RENDER_MAP_SCRIPT = Path("scripts/generate_hsd_template_render_map_v1.py")
CONTRACT = Path("results_contract_v2.csv")
FINALS = Path("today_final_results.csv")
BRAND_POLICY = Path("config/graphics/brand_policy_v1.json")
LOGOS_CSV = Path("data/asset_registry/wnba/team_logos.csv")
TEAMS_CSV = Path("data/asset_registry/wnba/teams.csv")
ALIASES_CSV = Path("data/asset_registry/wnba/team_aliases.csv")
FIELDS = ["item_id", "template_id", "platform", "mode", "headline", "output_path", "width", "height", "status", "review_only", "notes"]

BG = (4, 5, 10)
PANEL = (10, 12, 20)
INK = (248, 249, 252)
MUTED = (166, 172, 184)
GOLD = (228, 181, 77)
ORANGE = (239, 107, 49)
PURPLE = (156, 76, 255)
BLUE = (56, 136, 255)
WHITE = (255, 255, 255)


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


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in FIELDS})


def font(size: int, bold: bool = False):
    choices = []
    if bold:
        choices += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    choices += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in choices:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, start: int, floor: int, bold: bool = True):
    size = start
    while size >= floor:
        f = font(size, bold)
        if text_w(draw, text, f) <= max_w:
            return f
        size -= 2
    return font(floor, bold)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    if not words:
        return []
    lines: List[str] = []
    cur = words[0]
    for word in words[1:]:
        candidate = cur + " " + word
        if text_w(draw, candidate, fnt) <= max_w:
            cur = candidate
        else:
            lines.append(cur)
            cur = word
            if len(lines) >= max_lines - 1:
                break
    lines.append(cur)
    if len(" ".join(lines).split()) < len(words) and lines:
        lines[-1] = lines[-1].rstrip("., ") + "..."
    return lines[:max_lines]


def draw_center(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True) -> None:
    x, y, w, h = box
    f = fit(draw, text, w, size, 18, bold)
    b = draw.textbbox((0, 0), text, font=f)
    draw.text((x + (w - (b[2] - b[0])) // 2, y + (h - (b[3] - b[1])) // 2), text, font=f, fill=fill)


def draw_left(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True, max_lines: int = 2) -> None:
    x, y, w, h = box
    f = fit(draw, text, w, size, 24, bold)
    lines = wrap(draw, text, f, w, max_lines)
    gap = 6
    total = len(lines) * f.size + max(0, len(lines) - 1) * gap
    yy = y + max(0, (h - total) // 2)
    for line in lines:
        draw.text((x, yy), line, font=f, fill=fill)
        yy += f.size + gap


def rect(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], outline=(255, 255, 255, 80), fill=(255, 255, 255, 12), width: int = 2, radius: int = 18) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=outline, fill=fill, width=width)


def pill(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, fill=GOLD, ink=(5, 7, 12), size: int = 28) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill)
    draw_center(draw, box, text.upper(), size, ink, True)


def source_index() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in read_csv(CONTRACT):
        for key in ["event_id", "dedupe_key"]:
            if row.get(key):
                out[row[key]] = row
    for row in read_csv(FINALS):
        for key in ["event_uid", "canonical_key", "event_id", "dedupe_key"]:
            if row.get(key):
                out[row[key]] = row
    return out


def team_logo_registry() -> Tuple[Dict[str, str], Dict[str, str]]:
    aliases: Dict[str, str] = {}
    for row in read_csv(TEAMS_CSV):
        tid = row.get("team_id", "")
        if not tid:
            continue
        for k in ["team_name", "nickname", "city"]:
            if row.get(k):
                aliases[norm(row[k])] = tid
    for row in read_csv(ALIASES_CSV):
        if row.get("team_id") and row.get("alias"):
            aliases[norm(row["alias"])] = row["team_id"]
    logos = {row.get("team_id", ""): row.get("file_path", "") for row in read_csv(LOGOS_CSV) if row.get("team_id")}
    return aliases, logos


def resolve_team(name: str, aliases: Dict[str, str]) -> str:
    n = norm(name)
    if n in aliases:
        return aliases[n]
    for alias, tid in aliases.items():
        if alias and alias in n:
            return tid
    return ""


def load_logo(name: str, aliases: Dict[str, str], logos: Dict[str, str]) -> Image.Image | None:
    path = Path(clean(logos.get(resolve_team(name, aliases), "")))
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def initials(name: str) -> str:
    bits = [b for b in re.split(r"\W+", clean(name).upper()) if b and b not in {"THE", "FC"}]
    return "".join(b[0] for b in bits[:3]) or "HSD"


def load_badge() -> Image.Image | None:
    policy = load_json(BRAND_POLICY)
    paths = []
    logo_policy = policy.get("public_logo_policy", {})
    for key in ["official_public_badge_asset", "current_repo_fallback_asset"]:
        if logo_policy.get(key):
            paths.append(Path(logo_policy[key]))
    paths += [Path("assets/branding/official_hsd_watermark.png"), Path("data/assets/brand/hsd_watermark.png")]
    for p in paths:
        if p.exists():
            try:
                return Image.open(p).convert("RGBA")
            except Exception:
                pass
    return None


def paste_badge(img: Image.Image, badge: Image.Image | None, story: bool = False) -> None:
    if badge is None:
        return
    b = badge.copy()
    max_w = 88 if story else 80
    b.thumbnail((max_w, max_w), Image.LANCZOS)
    img.alpha_composite(b, ((52 if story else 48), (48 if story else 42)))


def background(size: Tuple[int, int], accent: Tuple[int, int, int], accent2: Tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(4 + 11 * t)
        g = int(5 + 11 * t)
        b = int(10 + 16 * t)
        d.line((0, y, w, y), fill=(r, g, b, 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-360, 90, int(w * .78), int(h * .62)), fill=(*accent, 62))
    gd.ellipse((int(w * .38), int(h * .18), w + 360, int(h * .72)), fill=(*accent2, 48))
    gd.rectangle((0, int(h * .74), w, h), fill=(0, 0, 0, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(34))
    img.alpha_composite(glow)
    # subtle arena-light energy, not the old loud diagonal stripe field
    for x in [95, 180, w - 180, w - 95]:
        d.ellipse((x - 18, 70, x + 18, 106), fill=(255, 255, 255, 80))
        d.line((x, 100, w // 2, h // 2), fill=(255, 255, 255, 10), width=7)
    d.rectangle((0, 0, w, h), outline=(255, 255, 255, 20), width=2)
    return img


def ghost(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int) -> None:
    draw_center(draw, box, text.upper(), size, fill=(255, 255, 255, 24), bold=True)


def logo_card(img: Image.Image, draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], team: str, logo: Image.Image | None, accent=GOLD, dim: bool = False) -> None:
    fill = (7, 8, 12, 225 if not dim else 185)
    outline = (*accent, 210 if not dim else 90)
    rect(draw, box, outline=outline, fill=fill, width=3 if not dim else 2, radius=12)
    x, y, w, h = box
    if logo:
        lg = logo.copy()
        lg.thumbnail((w - 42, h - 42), Image.LANCZOS)
        img.alpha_composite(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2))
    else:
        # branded fallback mark instead of noisy APPROVED LOGO placeholders
        cx, cy = x + w // 2, y + h // 2
        r = min(w, h) // 3
        draw.regular_polygon((cx, cy, r), n_sides=6, rotation=30, outline=outline, fill=(0, 0, 0, 60))
        draw_center(draw, (x + 20, y + h // 2 - 34, w - 40, 68), initials(team), 46, fill=(accent if not dim else MUTED), bold=True)


def canvas_for(row: Dict[str, Any]) -> Tuple[int, int]:
    return (1080, 1920) if row.get("platform") == "stories" else (1080, 1350)


def event_data(map_row: Dict[str, Any], index: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    sid = clean(map_row.get("source_id"))
    if sid in index:
        return index[sid]
    first = clean(map_row.get("item_id")).split("::")[0]
    return index.get(first, {})


def final_names(row: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("primary_team") or row.get("home_team_name") or row.get("home_team_display") or "PRIMARY TEAM")
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("secondary_team") or row.get("away_team_name") or row.get("away_team_display") or "SECONDARY TEAM")
    sh = clean(row.get("score_home") or row.get("home_score"))
    sa = clean(row.get("score_away") or row.get("away_score"))
    home = clean(row.get("home_team_name") or row.get("home_team_display"))
    if winner and home and winner == home:
        score = f"{sh}-{sa}" if sh and sa else clean(row.get("score_display") or row.get("final_score_display") or "00-00")
    else:
        score = f"{sa}-{sh}" if sh and sa else clean(row.get("score_display") or row.get("final_score_display") or "00-00")
    return winner, loser, score, clean(row.get("league") or row.get("league_norm") or "WNBA"), clean(row.get("event_date_local") or row.get("scheduled_date_local") or "")


def score_parts(score: str) -> Tuple[str, str]:
    pieces = re.split(r"[-–—]", clean(score))
    if len(pieces) >= 2:
        return pieces[0].strip(), pieces[1].strip()
    return clean(score), ""


def render_game_final(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    story = map_row.get("platform") == "stories"
    img = background(canvas_for(map_row), GOLD, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    winner, loser, score, league, date = final_names(src)
    s1, s2 = score_parts(score)
    if story:
        ghost(d, (80, 110, 920, 155), "GAME RECAP", 118)
        draw_center(d, (90, 220, 900, 150), "QUICK FINAL", 118, GOLD, True)
        draw_center(d, (120, 390, 840, 54), f"{league} • {date} • FINAL".upper(), 31, INK, True)
        logo_card(img, d, (70, 520, 260, 260), winner, load_logo(winner, aliases, logos), GOLD)
        draw_left(d, (370, 520, 330, 150), winner.upper(), 62, INK, True, 2)
        draw_center(d, (705, 475, 300, 310), s1, 168, GOLD, True)
        logo_card(img, d, (70, 840, 220, 220), loser, load_logo(loser, aliases, logos), MUTED, dim=True)
        draw_left(d, (370, 860, 310, 112), loser.upper(), 48, MUTED, True, 2)
        if s2:
            draw_center(d, (725, 835, 245, 230), s2, 118, MUTED, True)
        rect(d, (70, 1180, 940, 118), outline=(*GOLD, 180), fill=(0, 0, 0, 120), radius=0)
        draw_center(d, (100, 1190, 880, 95), "KEY PERFORMER  •  TEXT-ONLY STRIP", 40, INK, True)
        draw_center(d, (90, 1405, 900, 150), clean(src.get("summary") or "CLUTCH CLOSEOUT."), 58, GOLD, True)
    else:
        ghost(d, (90, 70, 900, 210), "GAME RECAP", 128)
        draw_center(d, (180, 250, 720, 76), "FINAL SCORE", 60, GOLD, True)
        draw_center(d, (180, 350, 720, 46), f"FINAL • {league} • {date}".upper(), 30, INK, True)
        logo_card(img, d, (58, 465, 252, 252), winner, load_logo(winner, aliases, logos), GOLD)
        pill(d, (345, 456, 250, 56), "PRIMARY", fill=GOLD, ink=BG, size=26)
        draw_left(d, (340, 525, 390, 135), winner.upper(), 78, INK, True, 2)
        draw_center(d, (735, 430, 300, 300), s1, 174, GOLD, True)
        logo_card(img, d, (58, 760, 220, 220), loser, load_logo(loser, aliases, logos), MUTED, dim=True)
        draw_left(d, (340, 792, 370, 118), loser.upper(), 58, MUTED, True, 2)
        if s2:
            draw_center(d, (760, 748, 250, 230), s2, 112, MUTED, True)
        rect(d, (58, 1025, 964, 92), outline=(*GOLD, 180), fill=(0, 0, 0, 130), radius=0)
        draw_center(d, (78, 1032, 924, 74), "KEY PERFORMER  •  TEXT-ONLY STRIP", 36, INK, True)
        draw_center(d, (90, 1170, 900, 105), clean(src.get("hook") or "STATEMENT WIN."), 58, GOLD, True)
    return img


def render_tonight(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    img = background((1080, 1350), ORANGE, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, False)
    home = clean(src.get("home_team_name") or src.get("home_team_display") or "TEAM ONE")
    away = clean(src.get("away_team_name") or src.get("away_team_display") or "TEAM TWO")
    time = clean(src.get("time_et") or src.get("start_time_et") or src.get("scheduled_time_local") or src.get("status") or "TIME / TV / CONTEXT")
    draw_center(d, (120, 82, 840, 154), "TONIGHT", 122, GOLD, True)
    draw_center(d, (120, 232, 840, 78), "IN THE W", 58, INK, True)
    rect(d, (255, 340, 570, 66), outline=(*GOLD, 150), fill=(0, 0, 0, 115), radius=0)
    draw_center(d, (270, 347, 540, 52), time.upper(), 32, INK, True)
    logo_card(img, d, (58, 468, 280, 280), home, load_logo(home, aliases, logos), GOLD)
    logo_card(img, d, (742, 468, 280, 280), away, load_logo(away, aliases, logos), PURPLE)
    draw_center(d, (360, 470, 360, 92), home.upper(), 50, INK, True)
    draw_center(d, (360, 568, 360, 64), "VS.", 44, GOLD, True)
    draw_center(d, (360, 632, 360, 92), away.upper(), 50, INK, True)
    rect(d, (125, 815, 830, 124), outline=(*GOLD, 180), fill=(*GOLD, 230), radius=0)
    draw_center(d, (145, 825, 790, 104), "WHO NEEDS THIS ONE MORE?", 52, BG, True)
    rect(d, (70, 1000, 940, 175), outline=(255, 255, 255, 70), fill=(0, 0, 0, 120))
    for i, label in enumerate(["KEY MATCHUP", "WATCH POINT", "WHY IT MATTERS"]):
        x = 100 + i * 300
        draw_center(d, (x, 1017, 250, 48), label, 28, GOLD, True)
        draw_center(d, (x, 1068, 250, 78), "EDITABLE FIELD", 24, INK, False)
    draw_center(d, (100, 1210, 880, 70), "PREVIEW MODE • ONE LOWER MODULE ACTIVE", 26, MUTED, True)
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
    draw_center(d, (120, 92 if not story else 130, 840, 118), "LAST NIGHT", 96 if not story else 112, INK, True)
    draw_center(d, (120, 205 if not story else 270, 840, 70), "IN THE W", 48 if not story else 56, GOLD, True)
    draw_center(d, (170, 305 if not story else 390, 740, 44), f"{len(finals)} FINALS. ONE RECAP.", 30, MUTED, True)
    if tid.endswith("c.carousel.v1"):
        rect(d, (90, 430, 900, 300), outline=(*GOLD, 150), fill=(0, 0, 0, 120), radius=24)
        draw_center(d, (120, 465, 840, 110), "FULL RECAP PACKAGE", 56, INK, True)
        draw_center(d, (120, 595, 840, 70), "SWIPE FOR THE BIGGEST FINALS", 32, GOLD, True)
        draw_center(d, (90, 860, 900, 170), "WHICH RESULT MATTERED MOST?", 54, INK, True)
        return img
    start = 395 if not story else 500
    row_h = 150 if not story else 160
    for i, r in enumerate(finals[:4 if not story else 5]):
        y = start + i * (row_h + 18)
        winner, loser, score, league, date = final_names(r)
        if i == 0 and not story:
            rect(d, (60, y, 960, 235), outline=(*GOLD, 180), fill=(0, 0, 0, 135), radius=20)
            logo_card(img, d, (92, y + 34, 150, 150), winner, load_logo(winner, aliases, logos), GOLD)
            draw_left(d, (270, y + 38, 470, 82), winner.upper(), 48, INK, True, 2)
            draw_center(d, (748, y + 38, 230, 86), score, 56, GOLD, True)
            draw_left(d, (270, y + 126, 470, 58), "FEATURED FINAL", 30, MUTED, True, 1)
            start += 95
            continue
        rect(d, (70, y, 940, row_h), outline=(*GOLD, 112), fill=(0, 0, 0, 112), radius=16)
        logo_card(img, d, (94, y + 26, 88, 88), winner, load_logo(winner, aliases, logos), GOLD)
        draw_left(d, (205, y + 30, 490, 76), winner.upper(), 36 if not story else 40, INK, True, 2)
        draw_center(d, (720, y + 20, 230, 90), score, 50 if not story else 56, GOLD, True)
    cta_y = 1138 if not story else 1480
    rect(d, (70, cta_y, 940, 120), outline=(*PURPLE, 150), fill=(0, 0, 0, 120), radius=18)
    draw_center(d, (90, cta_y + 12, 900, 94), "WHICH RESULT MATTERED MOST?", 42 if not story else 48, INK, True)
    return img


def render_generic(map_row: Dict[str, Any], badge) -> Image.Image:
    img = background(canvas_for(map_row), BLUE, GOLD)
    d = ImageDraw.Draw(img)
    story = map_row.get("platform") == "stories"
    paste_badge(img, badge, story)
    draw_center(d, (80, 170, 920, 170), clean(map_row.get("template_family") or "HSD TEMPLATE").upper(), 70, INK, True)
    draw_center(d, (80, 390, 920, 150), clean(map_row.get("template_variant") or "REVIEW RENDER"), 46, GOLD, True)
    rect(d, (80, 620, 920, 240), outline=(*GOLD, 150), fill=(0, 0, 0, 100))
    draw_left(d, (120, 650, 840, 180), clean(map_row.get("headline") or "HEADLINE"), 52, INK, True, 3)
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
    aliases, logos = team_logo_registry()
    index = source_index()
    manifest: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        if row.get("status") != "mapped":
            continue
        img = render_one(row, event_data(row, index), badge, aliases, logos)
        name = f"{i:02d}_{slug(row.get('platform'))}_{slug(row.get('template_id'))}_{slug(row.get('headline'))}.png"
        out = IMG_DIR / name
        img.convert("RGB").save(out, quality=96)
        manifest.append({
            "item_id": row.get("item_id"),
            "template_id": row.get("template_id"),
            "platform": row.get("platform"),
            "mode": row.get("mode"),
            "headline": row.get("headline"),
            "output_path": out.as_posix(),
            "width": img.size[0],
            "height": img.size[1],
            "status": "rendered_review",
            "review_only": "true",
            "notes": "Template Renderer v2.1 compile proof. Human review required before publishing.",
        })
    write_csv(MANIFEST_CSV, manifest)
    payload = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_only": True,
        "rendered_count": len(manifest),
        "source_render_map": RENDER_MAP_JSON.as_posix(),
        "items": manifest,
    }
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for item in manifest:
            p = Path(item["output_path"])
            if p.exists():
                z.write(p, p.relative_to(OUT_DIR.parent).as_posix())
    lines = [
        "# HSD Template Renderer v2.1",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{VERSION}`",
        "",
        "## Policy",
        "",
        "- Review-only compile proof.",
        "- Focused polish for Game Recap, Tonight in the W, and Last Night in the W mappings.",
        "- Human review required before publishing.",
        "",
        "## Summary",
        "",
        f"- Rendered files: `{len(manifest)}`",
        f"- Zip: `{ZIP_PATH.as_posix()}`",
        "",
    ]
    for item in manifest:
        lines.append(f"- `{item['template_id']}` | {item['platform']} | {item['headline']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": len(manifest), "out_dir": OUT_DIR.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
