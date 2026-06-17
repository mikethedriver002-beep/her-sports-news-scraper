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

VERSION = "v2.2-core-template-polish-review-only"
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
INK = (248, 249, 252)
MUTED = (164, 172, 186)
GOLD = (230, 183, 78)
ORANGE = (238, 108, 50)
PURPLE = (151, 80, 255)
CARD = (8, 10, 18)
LOGO_CACHE: Dict[str, Image.Image | None] = {}
FONT_CACHE: Dict[Tuple[int, bool], Any] = {}


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
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key in FONT_CACHE:
        return FONT_CACHE[key]
    choices = []
    if bold:
        choices += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    choices += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in choices:
        if Path(path).exists():
            FONT_CACHE[key] = ImageFont.truetype(path, size)
            return FONT_CACHE[key]
    FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


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
    out: List[str] = []
    cur = words[0]
    for word in words[1:]:
        test = cur + " " + word
        if text_w(draw, test, fnt) <= max_w:
            cur = test
        else:
            out.append(cur)
            cur = word
            if len(out) >= max_lines - 1:
                break
    out.append(cur)
    if len(" ".join(out).split()) < len(words) and out:
        out[-1] = out[-1].rstrip("., ") + "..."
    return out[:max_lines]


def center(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True) -> None:
    x, y, w, h = box
    fnt = fit(draw, text, w, size, 18, bold)
    bb = draw.textbbox((0, 0), text, font=fnt)
    draw.text((x + (w - (bb[2] - bb[0])) // 2, y + (h - (bb[3] - bb[1])) // 2), text, font=fnt, fill=fill)


def left(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True, max_lines: int = 2) -> None:
    x, y, w, h = box
    fnt = fit(draw, text, w, size, 24, bold)
    lines = wrap(draw, text, fnt, w, max_lines)
    yy = y + max(0, (h - len(lines) * (fnt.size + 7)) // 2)
    for line in lines:
        draw.text((x, yy), line, font=fnt, fill=fill)
        yy += fnt.size + 7


def rect(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], outline=(255, 255, 255, 78), fill=(255, 255, 255, 10), width=2, radius=18) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=outline, fill=fill, width=width)


def pill(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, fill=GOLD, ink=BG, size=28) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill)
    center(draw, box, text.upper(), size, ink, True)


def background(size: Tuple[int, int], accent: Tuple[int, int, int], accent2: Tuple[int, int, int]) -> Image.Image:
    # v2.2 removes foreground crossing beams. Lights are edge-only and cannot cross content.
    w, h = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line((0, y, w, y), fill=(int(4 + 10 * t), int(5 + 10 * t), int(10 + 14 * t), 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-360, -180, int(w * .72), int(h * .55)), fill=(*accent, 54))
    gd.ellipse((int(w * .45), int(h * .15), w + 420, int(h * .70)), fill=(*accent2, 42))
    gd.rectangle((0, int(h * .72), w, h), fill=(0, 0, 0, 80))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(42)))
    for x in [92, 150, w - 150, w - 92]:
        d.ellipse((x - 18, 60, x + 18, 96), fill=(255, 255, 255, 58))
    d.rectangle((0, 0, w, h), outline=(255, 255, 255, 16), width=2)
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


def logo_for(name: str, aliases: Dict[str, str], logos: Dict[str, str]) -> Image.Image | None:
    team_id = resolve(name, aliases)
    path = logos.get(team_id, "")
    if path in LOGO_CACHE:
        return LOGO_CACHE[path]
    p = Path(clean(path))
    if not p.exists():
        LOGO_CACHE[path] = None
        return None
    try:
        LOGO_CACHE[path] = Image.open(p).convert("RGBA")
    except Exception:
        LOGO_CACHE[path] = None
    return LOGO_CACHE[path]


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
        # premium team-name badge fallback, not coded initials or placeholder labels
        center(draw, (x + 18, y + 24, w - 36, h - 48), clean(team).upper(), 32 if w < 170 else 40, fill=(accent if not dim else MUTED), bold=True)


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
        center(d, (88, 120, 904, 110), "GAME RECAP", 95, fill=(255, 255, 255, 35), bold=True)
        center(d, (82, 235, 916, 145), "QUICK FINAL", 116, GOLD, True)
        center(d, (120, 392, 840, 50), f"{league} • {date} • FINAL".upper(), 31, INK, True)
        team_badge(img, d, (66, 510, 260, 260), winner, logo_for(winner, aliases, logos), GOLD)
        left(d, (360, 520, 340, 145), winner.upper(), 64, INK, True, 2)
        center(d, (700, 470, 305, 310), s1, 176, GOLD, True)
        team_badge(img, d, (66, 835, 225, 225), loser, logo_for(loser, aliases, logos), MUTED, dim=True)
        left(d, (360, 855, 330, 120), loser.upper(), 50, MUTED, True, 2)
        if s2:
            center(d, (715, 818, 270, 250), s2, 124, MUTED, True)
        rect(d, (66, 1185, 948, 116), outline=(*GOLD, 170), fill=(0, 0, 0, 125), radius=0)
        center(d, (90, 1195, 900, 90), "KEY PERFORMER  •  TEXT-ONLY STRIP", 40, INK, True)
        center(d, (86, 1410, 910, 150), clean(src.get("summary") or "CLUTCH CLOSEOUT."), 60, GOLD, True)
    else:
        center(d, (80, 62, 920, 205), "GAME RECAP", 130, fill=(255, 255, 255, 28), bold=True)
        center(d, (178, 250, 724, 78), "FINAL SCORE", 62, GOLD, True)
        center(d, (172, 352, 736, 48), f"FINAL • {league} • {date}".upper(), 30, INK, True)
        team_badge(img, d, (55, 465, 255, 255), winner, logo_for(winner, aliases, logos), GOLD)
        pill(d, (346, 456, 230, 54), "PRIMARY", GOLD, BG, 25)
        left(d, (340, 522, 398, 140), winner.upper(), 80, INK, True, 2)
        center(d, (730, 430, 305, 305), s1, 180, GOLD, True)
        team_badge(img, d, (55, 765, 220, 220), loser, logo_for(loser, aliases, logos), MUTED, dim=True)
        left(d, (340, 795, 380, 118), loser.upper(), 58, MUTED, True, 2)
        if s2:
            center(d, (758, 750, 250, 232), s2, 112, MUTED, True)
        rect(d, (55, 1025, 970, 92), outline=(*GOLD, 170), fill=(0, 0, 0, 132), radius=0)
        center(d, (78, 1034, 924, 72), "KEY PERFORMER  •  TEXT-ONLY STRIP", 36, INK, True)
        center(d, (90, 1168, 900, 108), clean(src.get("hook") or "STATEMENT WIN."), 60, GOLD, True)
    return img


def render_tonight(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    img = background((1080, 1350), ORANGE, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, False)
    home = clean(src.get("home_team_name") or src.get("home_team_display") or "TEAM ONE")
    away = clean(src.get("away_team_name") or src.get("away_team_display") or "TEAM TWO")
    time = clean(src.get("time_et") or src.get("start_time_et") or src.get("scheduled_time_local") or src.get("status") or "TIME / TV / CONTEXT")
    center(d, (120, 72, 840, 156), "TONIGHT", 124, GOLD, True)
    center(d, (120, 226, 840, 78), "IN THE W", 58, INK, True)
    rect(d, (250, 338, 580, 66), outline=(*GOLD, 150), fill=(0, 0, 0, 116), radius=0)
    center(d, (268, 346, 544, 50), time.upper(), 32, INK, True)
    team_badge(img, d, (55, 470, 280, 280), home, logo_for(home, aliases, logos), GOLD)
    team_badge(img, d, (745, 470, 280, 280), away, logo_for(away, aliases, logos), PURPLE)
    center(d, (360, 468, 360, 96), home.upper(), 52, INK, True)
    center(d, (360, 565, 360, 64), "VS.", 44, GOLD, True)
    center(d, (360, 632, 360, 96), away.upper(), 52, INK, True)
    rect(d, (120, 815, 840, 124), outline=(*GOLD, 185), fill=(*GOLD, 232), radius=0)
    center(d, (142, 825, 796, 104), "WHO NEEDS THIS ONE MORE?", 52, BG, True)
    rect(d, (70, 1000, 940, 168), outline=(255, 255, 255, 66), fill=(0, 0, 0, 122), radius=18)
    labels = ["KEY MATCHUP", "WATCH POINT", "WHY IT MATTERS"]
    for i, label in enumerate(labels):
        x = 100 + i * 300
        center(d, (x, 1018, 250, 44), label, 28, GOLD, True)
        center(d, (x, 1067, 250, 70), "EDITABLE FIELD", 24, INK, False)
    center(d, (100, 1210, 880, 62), "PREVIEW MODE • ONE LOWER MODULE ACTIVE", 25, MUTED, True)
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
    center(d, (120, 96 if not story else 135, 840, 118), "LAST NIGHT", 98 if not story else 112, INK, True)
    center(d, (120, 210 if not story else 276, 840, 70), "IN THE W", 48 if not story else 56, GOLD, True)
    center(d, (170, 310 if not story else 396, 740, 44), f"{len(finals)} FINALS. ONE RECAP.", 30, MUTED, True)
    if tid.endswith("c.carousel.v1"):
        rect(d, (90, 430, 900, 300), outline=(*GOLD, 150), fill=(0, 0, 0, 120), radius=24)
        center(d, (120, 462, 840, 112), "FULL RECAP PACKAGE", 58, INK, True)
        center(d, (120, 596, 840, 70), "SWIPE FOR THE BIGGEST FINALS", 32, GOLD, True)
        center(d, (90, 860, 900, 170), "WHICH RESULT MATTERED MOST?", 54, INK, True)
        return img
    start = 395 if not story else 505
    row_h = 150 if not story else 160
    offset_extra = 0
    for i, r in enumerate(finals[:4 if not story else 5]):
        y = start + offset_extra + i * (row_h + 18)
        winner, loser, score, league, date = final_names(r)
        if i == 0 and not story:
            rect(d, (60, y, 960, 235), outline=(*GOLD, 180), fill=(0, 0, 0, 136), radius=20)
            team_badge(img, d, (92, y + 34, 150, 150), winner, logo_for(winner, aliases, logos), GOLD)
            left(d, (270, y + 38, 470, 82), winner.upper(), 48, INK, True, 2)
            center(d, (748, y + 38, 230, 86), score, 56, GOLD, True)
            left(d, (270, y + 126, 470, 58), "FEATURED FINAL", 30, MUTED, True, 1)
            offset_extra += 95
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
        name = f"{i:02d}_{slug(row.get('platform'))}_{slug(row.get('template_id'))}_{slug(row.get('headline'))}.png"
        out = IMG_DIR / name
        img.convert("RGB").save(out, quality=96)
        manifest.append({"item_id": row.get("item_id"), "template_id": row.get("template_id"), "platform": row.get("platform"), "mode": row.get("mode"), "headline": row.get("headline"), "output_path": out.as_posix(), "width": img.size[0], "height": img.size[1], "status": "rendered_review", "review_only": "true", "notes": "Template Renderer v2.2 compile proof. Human review required before publishing."})
    write_csv(MANIFEST_CSV, manifest)
    payload = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "review_only": True, "rendered_count": len(manifest), "source_render_map": RENDER_MAP_JSON.as_posix(), "items": manifest}
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for item in manifest:
            p = Path(item["output_path"])
            if p.exists():
                z.write(p, p.relative_to(OUT_DIR.parent).as_posix())
    report = ["# HSD Template Renderer v2.2", "", f"Generated: `{payload['generated_at_utc']}`", f"Version: `{VERSION}`", "", "## Policy", "", "- Review-only compile proof.", "- Removed foreground crossing lines.", "- Uses team-name badge fallback when logos are unavailable.", "- Focused on Game Recap, Tonight in the W, and Last Night in the W mappings.", "- Human review required before publishing.", "", "## Summary", "", f"- Rendered files: `{len(manifest)}`", f"- Zip: `{ZIP_PATH.as_posix()}`", ""]
    for item in manifest:
        report.append(f"- `{item['template_id']}` | {item['platform']} | {item['headline']}")
    REPORT_MD.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": len(manifest), "out_dir": OUT_DIR.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
