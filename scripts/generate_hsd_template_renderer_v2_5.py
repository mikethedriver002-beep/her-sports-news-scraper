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

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    import cairosvg  # type: ignore
except Exception:  # pragma: no cover
    cairosvg = None

VERSION = "v2.5-hsd-quality-tonight-logo-integrity-review-only"
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2")
IMG_DIR = OUT_DIR / "renders"
LOGO_CACHE_DIR = OUT_DIR / "logo_cache"
MANIFEST_CSV = OUT_DIR / "hsd_template_renderer_v2_manifest.csv"
MANIFEST_JSON = OUT_DIR / "hsd_template_renderer_v2_manifest.json"
REPORT_MD = OUT_DIR / "hsd_template_renderer_v2_report.md"
ZIP_PATH = OUT_DIR / "hsd_template_renderer_v2_renders.zip"
LOGO_AUDIT_CSV = OUT_DIR / "hsd_template_renderer_v2_logo_audit.csv"
LOGO_AUDIT_JSON = OUT_DIR / "hsd_template_renderer_v2_logo_audit.json"
RENDER_MAP_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping/hsd_template_render_map.json")
RENDER_MAP_SCRIPT = Path("scripts/generate_hsd_template_render_map_v1.py")
CONTRACT = Path("results_contract_v2.csv")
FINALS = Path("today_final_results.csv")
BRAND_POLICY = Path("config/graphics/brand_policy_v1.json")
LOGOS_CSV = Path("data/asset_registry/wnba/team_logos.csv")
TEAMS_CSV = Path("data/asset_registry/wnba/teams.csv")
ALIASES_CSV = Path("data/asset_registry/wnba/team_aliases.csv")
VERIFIED_LOGOS = Path("config/hsd_verified_logo_registry_v1.json")
FIELDS = ["item_id", "template_id", "platform", "mode", "headline", "output_path", "width", "height", "status", "review_only", "notes"]
LOGO_FIELDS = ["team", "team_id", "source", "path_or_url", "status", "note"]

BG = (3, 4, 9)
INK = (249, 250, 253)
MUTED = (165, 173, 188)
GOLD = (235, 184, 74)
ORANGE = (241, 108, 47)
PURPLE = (152, 82, 255)
DEEP = (8, 10, 18)
FONT_CACHE: Dict[Tuple[int, bool], Any] = {}
LOGO_CACHE: Dict[str, Image.Image | None] = {}
LOGO_AUDIT: List[Dict[str, str]] = []


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def norm(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def slug(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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
    candidates = []
    if bold:
        candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if Path(p).exists():
            FONT_CACHE[key] = ImageFont.truetype(p, size)
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


def center(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True) -> None:
    x, y, w, h = box
    fnt = fit(draw, clean(text), w, size, 18, bold)
    b = draw.textbbox((0, 0), clean(text), font=fnt)
    draw.text((x + (w - (b[2] - b[0])) // 2, y + (h - (b[3] - b[1])) // 2), clean(text), font=fnt, fill=fill)


def left(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True, max_lines: int = 2) -> None:
    x, y, w, h = box
    words = clean(text).split()
    fnt = fit(draw, clean(text), w, size, 22, bold)
    lines: List[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if text_w(draw, test, fnt) <= w or not current:
            current = test
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    if current:
        lines.append(current)
    lines = lines[:max_lines]
    yy = y + max(0, (h - len(lines) * (fnt.size + 7)) // 2)
    for line in lines:
        draw.text((x, yy), line, font=fnt, fill=fill)
        yy += fnt.size + 7


def rect(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], outline=(255, 255, 255, 70), fill=(255, 255, 255, 10), width=2, radius=18) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=outline, fill=fill, width=width)


def bg(size: Tuple[int, int], accent=ORANGE, accent2=PURPLE) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line((0, y, w, y), fill=(int(3 + 11 * t), int(4 + 11 * t), int(9 + 16 * t), 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-420, -250, int(w * .70), int(h * .55)), fill=(*accent, 45))
    gd.ellipse((int(w * .45), int(h * .15), w + 420, int(h * .70)), fill=(*accent2, 38))
    gd.rectangle((0, int(h * .72), w, h), fill=(0, 0, 0, 88))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(48)))
    d.rectangle((0, 0, w, h), outline=(255, 255, 255, 14), width=2)
    return img


def load_badge() -> Image.Image | None:
    policy = load_json(BRAND_POLICY).get("public_logo_policy", {})
    for raw in [policy.get("official_public_badge_asset"), policy.get("current_repo_fallback_asset"), "assets/branding/official_hsd_watermark.png"]:
        path = Path(clean(raw))
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


def registries() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Any]]:
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
    verified = {norm(name): data for name, data in load_json(VERIFIED_LOGOS).get("teams", {}).items()}
    return aliases, logos, verified


def resolve(team: str, aliases: Dict[str, str]) -> str:
    n = norm(team)
    if n in aliases:
        return aliases[n]
    for alias, tid in aliases.items():
        if alias and alias in n:
            return tid
    return ""


def audit(team: str, tid: str, source: str, path_or_url: str, status: str, note: str) -> None:
    LOGO_AUDIT.append({"team": clean(team), "team_id": tid, "source": source, "path_or_url": path_or_url, "status": status, "note": note})


def svg_to_img(data: bytes) -> Image.Image | None:
    if cairosvg is None:
        return None
    try:
        return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data, output_width=768, output_height=768))).convert("RGBA")
    except Exception:
        return None


def image_from_file(path: Path) -> Image.Image | None:
    if not path.exists():
        return None
    if path.suffix.lower() == ".svg":
        return svg_to_img(path.read_bytes())
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def fetch_verified(team: str, tid: str, verified: Dict[str, Any]) -> Image.Image | None:
    data = verified.get(norm(team), {})
    blocked = data.get("blocked_url_substrings", [])
    LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for url in data.get("direct_urls", []):
        if any(bad in url for bad in blocked):
            audit(team, tid, "verified_remote", url, "skip", "blocked by registry")
            continue
        key = LOGO_CACHE_DIR / f"{slug(team)}_{slug(url.split('/')[-1]) or 'logo'}"
        try:
            if key.exists() and key.stat().st_size > 0:
                raw = key.read_bytes()
            else:
                r = requests.get(url, timeout=8, headers={"User-Agent": "HSD-template-renderer-v2.5"})
                if r.status_code >= 400 or not r.content:
                    audit(team, tid, "verified_remote", url, "warning_fallback", f"http_{r.status_code}")
                    continue
                raw = r.content
                key.write_bytes(raw)
            img = svg_to_img(raw) if raw.lstrip().startswith(b"<") or url.lower().endswith(".svg") else Image.open(io.BytesIO(raw)).convert("RGBA")
            if img:
                audit(team, tid, "verified_remote", url, "loaded", "verified registry logo loaded")
                return img
        except Exception as exc:
            audit(team, tid, "verified_remote", url, "warning_fallback", type(exc).__name__)
    return None


def logo_for(team: str, aliases: Dict[str, str], logos: Dict[str, str], verified: Dict[str, Any]) -> Image.Image | None:
    tid = resolve(team, aliases)
    local = clean(logos.get(tid, ""))
    cache_key = f"{tid}:{local}:{norm(team)}"
    if cache_key in LOGO_CACHE:
        return LOGO_CACHE[cache_key]
    img = image_from_file(Path(local)) if local else None
    if img:
        audit(team, tid, "local_registry", local, "loaded", "local approved png/svg logo loaded")
        LOGO_CACHE[cache_key] = img
        return img
    if local:
        audit(team, tid, "local_registry", local, "warning_fallback", "local logo missing or not renderable")
    img = fetch_verified(team, tid, verified)
    if img:
        LOGO_CACHE[cache_key] = img
        return img
    audit(team, tid, "fallback", "team_name_badge", "warning_fallback", "real logo unavailable for active render")
    LOGO_CACHE[cache_key] = None
    return None


def short_team(team: str) -> str:
    n = clean(team).upper()
    for prefix in ["GOLDEN STATE ", "LOS ANGELES ", "LAS VEGAS ", "NEW YORK ", "CONNECTICUT ", "WASHINGTON ", "MINNESOTA ", "SEATTLE ", "PHOENIX ", "INDIANA ", "TORONTO "]:
        if n.startswith(prefix) and len(n) > len(prefix) + 3:
            return n[len(prefix):]
    return n


def logo_panel(img: Image.Image, draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], team: str, logo: Image.Image | None, accent=GOLD, dim=False, angle: str = "left") -> None:
    x, y, w, h = box
    skew = 34
    poly = [(x + (0 if angle == "left" else skew), y), (x + w, y), (x + w - (skew if angle == "left" else 0), y + h), (x, y + h)]
    draw.polygon(poly, fill=(8, 10, 18, 228 if not dim else 188), outline=(*accent, 210 if not dim else 90))
    if logo:
        lg = logo.copy()
        lg.thumbnail((w - 72, h - 72), Image.LANCZOS)
        img.alpha_composite(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2))
    else:
        center(draw, (x + 32, y + 42, w - 64, h - 84), short_team(team), 44 if w > 250 else 34, fill=(accent if not dim else MUTED), bold=True)


def source_index() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in read_csv(CONTRACT) + read_csv(FINALS):
        for key in ["event_id", "dedupe_key", "event_uid", "canonical_key"]:
            if row.get(key):
                out[row[key]] = row
    return out


def event_data(row: Dict[str, Any], index: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    sid = clean(row.get("source_id"))
    if sid in index:
        return index[sid]
    return index.get(clean(row.get("item_id")).split("::")[0], {})


def final_names(row: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name") or row.get("home_team_display") or "PRIMARY TEAM")
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name") or row.get("away_team_display") or "SECONDARY TEAM")
    sh = clean(row.get("score_home") or row.get("home_score"))
    sa = clean(row.get("score_away") or row.get("away_score"))
    home = clean(row.get("home_team_name") or row.get("home_team_display"))
    score = f"{sh}-{sa}" if winner == home and sh and sa else f"{sa}-{sh}" if sh and sa else clean(row.get("score_display") or row.get("final_score_display") or "00-00")
    league = clean(row.get("league") or row.get("league_norm") or "WNBA")
    date = clean(row.get("event_date_local") or row.get("scheduled_date_local") or "")
    return winner, loser, score, league, date


def score_parts(score: str) -> Tuple[str, str]:
    parts = re.split(r"[-–—]", clean(score))
    return (parts[0].strip(), parts[1].strip()) if len(parts) >= 2 else (clean(score), "")


def render_tonight(row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos, verified) -> Image.Image:
    img = bg((1080, 1350), ORANGE, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, False)
    home = clean(src.get("home_team_name") or src.get("home_team_display") or "TEAM ONE")
    away = clean(src.get("away_team_name") or src.get("away_team_display") or "TEAM TWO")
    time = clean(src.get("time_et") or src.get("start_time_et") or src.get("scheduled_time_local") or src.get("status") or "TIME / TV / CONTEXT")
    center(d, (120, 72, 840, 150), "TONIGHT", 124, GOLD, True)
    center(d, (120, 218, 840, 78), "IN THE W", 60, INK, True)
    rect(d, (225, 330, 630, 68), outline=(*GOLD, 142), fill=(0, 0, 0, 118), radius=0)
    center(d, (245, 338, 590, 52), time.upper(), 32, INK, True)
    logo_panel(img, d, (42, 452, 340, 330), home, logo_for(home, aliases, logos, verified), GOLD, angle="left")
    logo_panel(img, d, (698, 452, 340, 330), away, logo_for(away, aliases, logos, verified), PURPLE, angle="right")
    center(d, (386, 442, 308, 102), short_team(home), 58, INK, True)
    center(d, (386, 552, 308, 70), "VS.", 50, GOLD, True)
    center(d, (386, 626, 308, 102), short_team(away), 58, INK, True)
    rect(d, (108, 810, 864, 126), outline=(*GOLD, 180), fill=(*GOLD, 234), radius=0)
    center(d, (135, 820, 810, 106), "WHO NEEDS THIS ONE MORE?", 54, BG, True)
    rect(d, (90, 1000, 900, 158), outline=(255, 255, 255, 70), fill=(0, 0, 0, 130), radius=18)
    center(d, (120, 1014, 840, 52), "WATCH POINT", 38, GOLD, True)
    center(d, (130, 1072, 820, 58), "PACE • STARS • LATE-GAME EDGE", 32, INK, True)
    center(d, (100, 1202, 880, 64), "PREGAME READ • HSD", 25, MUTED, True)
    return img


def render_game(row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos, verified) -> Image.Image:
    story = row.get("platform") == "stories"
    img = bg((1080, 1920) if story else (1080, 1350), GOLD, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    winner, loser, score, league, date = final_names(src)
    s1, s2 = score_parts(score)
    if story:
        center(d, (86, 105, 908, 120), "GAME RECAP", 100, fill=(255, 255, 255, 34), bold=True)
        center(d, (82, 230, 916, 145), "QUICK FINAL", 118, GOLD, True)
        center(d, (118, 390, 844, 52), f"{league} • {date} • FINAL".upper(), 31, INK, True)
        logo_panel(img, d, (64, 508, 270, 270), winner, logo_for(winner, aliases, logos, verified), GOLD)
        left(d, (360, 516, 345, 150), winner.upper(), 66, INK, True, 2)
        center(d, (698, 468, 310, 312), s1, 180, GOLD, True)
        logo_panel(img, d, (64, 836, 228, 228), loser, logo_for(loser, aliases, logos, verified), MUTED, True)
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
        logo_panel(img, d, (54, 462, 260, 260), winner, logo_for(winner, aliases, logos, verified), GOLD)
        left(d, (340, 492, 400, 168), winner.upper(), 86, INK, True, 2)
        center(d, (728, 428, 308, 310), s1, 186, GOLD, True)
        logo_panel(img, d, (54, 764, 222, 222), loser, logo_for(loser, aliases, logos, verified), MUTED, True)
        left(d, (340, 793, 382, 120), loser.upper(), 60, MUTED, True, 2)
        if s2:
            center(d, (758, 748, 250, 232), s2, 114, MUTED, True)
        rect(d, (54, 1025, 972, 92), outline=(*GOLD, 170), fill=(0, 0, 0, 132), radius=0)
        center(d, (78, 1034, 924, 72), "KEY TAKEAWAY • FINAL SCORE STORY", 36, INK, True)
        center(d, (88, 1168, 904, 108), clean(src.get("hook") or "STATEMENT WIN."), 62, GOLD, True)
    return img


def final_rows() -> List[Dict[str, str]]:
    return [r for r in read_csv(FINALS) if clean(r.get("status_norm")).lower() == "final" or clean(r.get("game_state")).lower() == "final"]


def render_last(row: Dict[str, Any], badge, aliases, logos, verified) -> Image.Image:
    story = row.get("platform") == "stories"
    img = bg((1080, 1920) if story else (1080, 1350), PURPLE, ORANGE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    finals = final_rows()[:5]
    center(d, (120, 95 if not story else 132, 840, 120), "LAST NIGHT", 100 if not story else 114, INK, True)
    center(d, (120, 210 if not story else 276, 840, 72), "IN THE W", 50 if not story else 58, GOLD, True)
    center(d, (170, 312 if not story else 400, 740, 44), f"{len(finals)} FINALS. ONE RECAP.", 31, MUTED, True)
    y = 395 if not story else 505
    for i, r in enumerate(finals[:4 if not story else 5]):
        winner, loser, score, _, _ = final_names(r)
        row_h = 155 if story else 145
        rect(d, (70, y, 940, row_h), outline=(*GOLD, 112), fill=(0, 0, 0, 112), radius=16)
        logo_panel(img, d, (94, y + 24, 92, 92), winner, logo_for(winner, aliases, logos, verified), GOLD)
        left(d, (210, y + 26, 490, 76), winner.upper(), 38 if not story else 40, INK, True, 2)
        center(d, (720, y + 20, 230, 90), score, 52 if not story else 56, GOLD, True)
        y += row_h + 22
    rect(d, (70, 1138 if not story else 1480, 940, 120), outline=(*PURPLE, 150), fill=(0, 0, 0, 120), radius=18)
    center(d, (90, 1150 if not story else 1492, 900, 94), "WHICH RESULT MATTERED MOST?", 42 if not story else 48, INK, True)
    return img


def render_one(row: Dict[str, Any], source: Dict[str, str], badge, aliases, logos, verified) -> Image.Image:
    tid = clean(row.get("template_id"))
    if tid == "tonight_in_the_w.a.v1":
        return render_tonight(row, source, badge, aliases, logos, verified)
    if tid in {"game_recap_final_score.a.v1", "game_recap_final_score.c.story.v1"}:
        return render_game(row, source, badge, aliases, logos, verified)
    if tid.startswith("last_night_in_the_w"):
        return render_last(row, badge, aliases, logos, verified)
    return bg((1080, 1920) if row.get("platform") == "stories" else (1080, 1350), PURPLE, GOLD)


def source_index() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for r in read_csv(CONTRACT) + read_csv(FINALS):
        for key in ["event_id", "dedupe_key", "event_uid", "canonical_key"]:
            if r.get(key):
                out[r[key]] = r
    return out


def event_data(row: Dict[str, Any], index: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    sid = clean(row.get("source_id"))
    return index.get(sid) or index.get(clean(row.get("item_id")).split("::")[0], {})


def main() -> None:
    if not RENDER_MAP_JSON.exists() and RENDER_MAP_SCRIPT.exists():
        runpy.run_path(RENDER_MAP_SCRIPT.as_posix(), run_name="__main__")
    rows = load_json(RENDER_MAP_JSON).get("rows", [])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if IMG_DIR.exists():
        shutil.rmtree(IMG_DIR)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    badge = load_badge()
    aliases, logos, verified = registries()
    index = source_index()
    manifest: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        if row.get("status") != "mapped":
            continue
        img = render_one(row, event_data(row, index), badge, aliases, logos, verified)
        out = IMG_DIR / f"{i:02d}_{slug(row.get('platform'))}_{slug(row.get('template_id'))}_{slug(row.get('headline'))}.png"
        img.convert("RGB").save(out, quality=96)
        manifest.append({"item_id": row.get("item_id"), "template_id": row.get("template_id"), "platform": row.get("platform"), "mode": row.get("mode"), "headline": row.get("headline"), "output_path": out.as_posix(), "width": img.size[0], "height": img.size[1], "status": "rendered_review", "review_only": "true", "notes": "Template Renderer v2.5 compile proof. Human review required before publishing."})
    write_csv(MANIFEST_CSV, manifest, FIELDS)
    write_csv(LOGO_AUDIT_CSV, LOGO_AUDIT, LOGO_FIELDS)
    payload = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "review_only": True, "rendered_count": len(manifest), "fallback_logo_warnings": len([r for r in LOGO_AUDIT if r.get("status") == "warning_fallback"]), "source_render_map": RENDER_MAP_JSON.as_posix(), "logo_audit": LOGO_AUDIT_JSON.as_posix(), "items": manifest}
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    LOGO_AUDIT_JSON.write_text(json.dumps({"version": VERSION, "rows": LOGO_AUDIT}, indent=2), encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for item in manifest:
            p = Path(item["output_path"])
            if p.exists():
                z.write(p, p.relative_to(OUT_DIR.parent).as_posix())
    report = ["# HSD Template Renderer v2.5", "", f"Generated: `{payload['generated_at_utc']}`", f"Version: `{VERSION}`", "", "## Summary", "", f"- Rendered files: `{len(manifest)}`", f"- Fallback logo warnings: `{payload['fallback_logo_warnings']}`", f"- Logo audit: `{LOGO_AUDIT_JSON.as_posix()}`", "", "## Changes", "", "- Real logo priority: local PNG/SVG first, verified registry fallback second, text badge last.", "- Stronger Tonight in the W matchup composition with premium angled team panels.", "- Less boxy logo treatment and stronger editorial watch-point band.", "- Review-only. Human approval required before publishing.", ""]
    for item in manifest:
        report.append(f"- `{item['template_id']}` | {item['platform']} | {item['headline']}")
    REPORT_MD.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": len(manifest), "fallback_logo_warnings": payload["fallback_logo_warnings"], "out_dir": OUT_DIR.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
