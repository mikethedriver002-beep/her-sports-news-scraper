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

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

VERSION = "v4.1-phase6d-visual-correction-template-skin"
ROOT = Path(".")
CONTRACT_ROOT = Path("config/graphics/v4/approved")
REGISTRY = CONTRACT_ROOT / "template_registry_v4.json"
SPECS = CONTRACT_ROOT / "wnba"
BADGE = Path("assets/graphics/v4/approved/brand/official_hsd_badge_reference.png")
RESULTS_CONTRACT = Path("results_contract_v2.csv")
TODAY_FINALS = Path("today_final_results.csv")
TEAM_LOGOS = Path("data/asset_registry/wnba/team_logos.csv")
TEAM_ALIASES = Path("data/asset_registry/wnba/team_aliases.csv")
TEAMS = Path("data/asset_registry/wnba/teams.csv")
PLAYER_ROOT = Path("outputs/latest/production_graphics_director/graphics_variant_packs/with_players")
OUT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4")
RENDERS = OUT / "renders"
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

MANIFEST_FIELDS = [
    "item_id", "source_id", "template_id", "platform", "headline", "output_path", "width", "height",
    "variant", "player_assets_used", "player_names", "team_logo_count", "review_only", "status", "notes",
]

INK = (242, 239, 229)
MUTED = (190, 183, 168)
GOLD = (218, 151, 33)
ORANGE = (238, 90, 30)
PURPLE = (150, 58, 224)
PINK = (236, 45, 143)
DARK = (4, 5, 8)
PANEL = (0, 0, 0, 168)
FONT_CACHE: Dict[tuple[int, bool], ImageFont.ImageFont] = {}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def norm(v: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    key = (size, bold)
    if key in FONT_CACHE: return FONT_CACHE[key]
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for p in candidates:
        if Path(p).exists():
            FONT_CACHE[key] = ImageFont.truetype(p, size)
            return FONT_CACHE[key]
    FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def fit(draw: ImageDraw.ImageDraw, text: str, max_w: int, start: int, floor: int = 18, bold: bool = True) -> ImageFont.ImageFont:
    text = clean(text)
    for size in range(start, floor - 1, -2):
        f = font(size, bold)
        if text_w(draw, text, f) <= max_w: return f
    return font(floor, bold)


def wrap(draw: ImageDraw.ImageDraw, text: str, max_w: int, fnt: ImageFont.ImageFont, max_lines: int = 2) -> List[str]:
    words = clean(text).split()
    lines: List[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if not current or text_w(draw, test, fnt) <= max_w:
            current = test
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines - 1:
                break
    if current: lines.append(current)
    return lines[:max_lines]


def draw_center(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, fnt: ImageFont.ImageFont, fill=INK, stroke=0) -> None:
    x, y, w, h = box
    b = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    draw.text((x + (w - (b[2] - b[0])) // 2, y + (h - (b[3] - b[1])) // 2), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def draw_wrapped(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, max_lines=2, bold=True, stroke=0) -> None:
    x, y, w, h = box
    f = fit(draw, text, w, size, 18, bold)
    lines = wrap(draw, text, w, f, max_lines)
    line_h = f.size + 6
    yy = y + max(0, (h - line_h * len(lines)) // 2)
    for line in lines:
        draw.text((x, yy), line, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        yy += line_h


def template_registry() -> Dict[str, Dict[str, Any]]:
    reg = read_json(REGISTRY)
    return {row["template_id"]: row for row in reg.get("templates", []) if row.get("template_id") in TARGET_TEMPLATES}


def spec(template_id: str) -> Dict[str, Any]:
    return read_json(SPECS / f"{template_id}.json")


def public_mockup(template_id: str, reg: Dict[str, Dict[str, Any]]) -> Optional[Image.Image]:
    raw = reg.get(template_id, {}).get("public_mockup_path")
    if raw and Path(raw).exists():
        try:
            return Image.open(raw).convert("RGB")
        except Exception:
            pass
    return None


def make_background(template_id: str, size: Tuple[int, int], reg: Dict[str, Dict[str, Any]]) -> Image.Image:
    """Phase 6D correction: use the approved public mockup as the template skin.

    Phase 6B blurred the approved mockup and then invented a separate house style.
    That helped the metric pass, but it still looked off-brand. 6D keeps the approved
    template texture, borders, badge mood, and major composition intact, then paints
    dynamic data only into registered zones.
    """
    mock = public_mockup(template_id, reg)
    if mock:
        img = ImageOps.fit(mock, size, method=Image.Resampling.LANCZOS).convert("RGBA")
        img = ImageEnhance.Brightness(img).enhance(0.96)
        img = ImageEnhance.Contrast(img).enhance(1.04)
        img = ImageEnhance.Color(img).enhance(1.02)
    else:
        img = Image.new("RGBA", size, DARK)
    w, h = size
    vignette = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(vignette, "RGBA")
    d.rectangle((0, 0, w, h), fill=(0, 0, 0, 18))
    d.rectangle((0, int(h * .86), w, h), fill=(0, 0, 0, 42))
    return Image.alpha_composite(img, vignette)


def paste_badge(img: Image.Image, sp: Dict[str, Any]) -> None:
    if not BADGE.exists(): return
    b = Image.open(BADGE).convert("RGBA")
    bd = sp.get("badge", {})
    w = int(bd.get("w") or bd.get("w_min") or 80)
    b.thumbnail((w, w), Image.Resampling.LANCZOS)
    img.alpha_composite(b, (int(bd.get("x", 48)), int(bd.get("y", 42))))


def panel(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], outline=GOLD, fill=PANEL, radius=10, width=2) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=(*outline, 210), width=width)


def soft_cover(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], fill=(0, 0, 0, 178), radius=6) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill)


def zone(sp: Dict[str, Any], name: str) -> Tuple[int, int, int, int]:
    z = sp["zones"][name]
    return int(z["x"]), int(z["y"]), int(z["w"]), int(z["h"])


def team_data() -> Tuple[Dict[str, str], Dict[str, str]]:
    aliases: Dict[str, str] = {}
    for row in read_csv(TEAMS):
        tid = clean(row.get("team_id"))
        for k in ["team_name", "nickname", "city"]:
            if tid and row.get(k): aliases[norm(row[k])] = tid
    for row in read_csv(TEAM_ALIASES):
        if row.get("team_id") and row.get("alias"):
            aliases[norm(row["alias"])] = row["team_id"]
    logos = {clean(row.get("team_id")): clean(row.get("file_path")) for row in read_csv(TEAM_LOGOS) if row.get("team_id")}
    return aliases, logos


def resolve(team: str, aliases: Dict[str, str]) -> str:
    n = norm(team)
    if n in aliases: return aliases[n]
    for a, tid in aliases.items():
        if a and (a in n or n in a): return tid
    return ""


def load_logo(team: str, aliases: Dict[str, str], logos: Dict[str, str]) -> Optional[Image.Image]:
    tid = resolve(team, aliases)
    p = Path(logos.get(tid, "")) if tid else Path("")
    if p and p.exists():
        try: return Image.open(p).convert("RGBA")
        except Exception: return None
    return None


def short_team(team: str) -> str:
    t = clean(team).upper()
    for prefix in ["GOLDEN STATE ", "LOS ANGELES ", "LAS VEGAS ", "NEW YORK ", "CONNECTICUT ", "WASHINGTON ", "MINNESOTA ", "SEATTLE ", "PHOENIX ", "INDIANA ", "ATLANTA ", "DALLAS "]:
        if t.startswith(prefix) and len(t) > len(prefix) + 3:
            return t[len(prefix):]
    return t


def logo_or_text(img: Image.Image, draw: ImageDraw.ImageDraw, team: str, box: Tuple[int, int, int, int], aliases: Dict[str, str], logos: Dict[str, str], accent=GOLD) -> bool:
    x, y, w, h = box
    panel(draw, box, accent, (0, 0, 0, 168), 6, 2)
    logo = load_logo(team, aliases, logos)
    if logo:
        lg = logo.copy()
        lg.thumbnail((w - 26, h - 26), Image.Resampling.LANCZOS)
        img.alpha_composite(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2))
        return True
    label = short_team(team)
    draw_center(draw, (x + 8, y + 8, w - 16, h - 16), label, fit(draw, label, w - 18, 30, 14), accent)
    return False


def read_rows_for_render(fixtures: bool = False) -> List[Dict[str, Any]]:
    if fixtures:
        return fixture_rows()
    out: List[Dict[str, Any]] = []
    for row in read_csv(RESULTS_CONTRACT):
        if clean(row.get("row_kind")).lower() == "preview" and clean(row.get("league")).upper() == "WNBA":
            out.append({"kind": "preview", **row})
    for row in read_csv(TODAY_FINALS):
        if clean(row.get("status_norm") or row.get("game_state")).lower() == "final":
            out.append({"kind": "final", **row})
    return out


def score_parts(row: Dict[str, Any]) -> Tuple[str, str]:
    score = clean(row.get("score_display") or row.get("final_score_display"))
    if score:
        parts = re.split(r"[-–—]", score)
        if len(parts) >= 2: return parts[0].strip(), parts[1].strip()
    return clean(row.get("winner_score") or row.get("score_home") or "00"), clean(row.get("loser_score") or row.get("score_away") or "00")


def player_index() -> Dict[str, List[Dict[str, str]]]:
    idx: Dict[str, List[Dict[str, str]]] = {}
    if not PLAYER_ROOT.exists(): return idx
    for p in PLAYER_ROOT.glob("*/content_summary.json"):
        payload = read_json(p)
        assets = payload.get("player_assets") or []
        players = payload.get("players") or []
        for i, pl in enumerate(players):
            if not isinstance(pl, dict): continue
            ap = Path(clean(assets[i])) if i < len(assets) and clean(assets[i]) else None
            if ap and ap.exists():
                item = {"name": clean(pl.get("display_name") or pl.get("player_name")), "team_id": clean(pl.get("team_id")), "path": ap.as_posix()}
                idx.setdefault(item["team_id"], []).append(item)
    return idx


def select_player(team: str, aliases: Dict[str, str], pidx: Dict[str, List[Dict[str, str]]]) -> Optional[Dict[str, str]]:
    tid = resolve(team, aliases)
    return (pidx.get(tid) or [None])[0]


def paste_player(img: Image.Image, draw: ImageDraw.ImageDraw, player: Dict[str, str], box: Tuple[int, int, int, int]) -> bool:
    p = Path(player.get("path", ""))
    if not p.exists(): return False
    try: person = Image.open(p).convert("RGBA")
    except Exception: return False
    x, y, w, h = box
    panel(draw, box, PINK, (0, 0, 0, 110), 8, 2)
    bbox = person.getbbox()
    if bbox: person = person.crop(bbox)
    person.thumbnail((w - 8, h - 54), Image.Resampling.LANCZOS)
    img.alpha_composite(person, (x + (w - person.width) // 2, y + h - person.height - 44))
    name = clean(player.get("name")) or "KEY PLAYER"
    draw_center(draw, (x + 10, y + h - 42, w - 20, 30), name.upper(), fit(draw, name.upper(), w - 20, 20, 12), INK)
    return True


def render_tonight(row: Dict[str, Any], template_id: str, reg: Dict[str, Dict[str, Any]], aliases: Dict[str, str], logos: Dict[str, str], pidx: Dict[str, List[Dict[str, str]]]) -> Tuple[Image.Image, Dict[str, Any]]:
    sp = spec(template_id)
    size = (sp["canvas"]["width"], sp["canvas"]["height"])
    img = make_background(template_id, size, reg)
    draw = ImageDraw.Draw(img, "RGBA")
    paste_badge(img, sp)
    home = clean(row.get("home_team_name") or row.get("home_team_display") or "TEAM B")
    away = clean(row.get("away_team_name") or row.get("away_team_display") or "TEAM A")
    # Keep the approved static title from the mockup. Only dynamic fields are repainted.
    panel(draw, zone(sp, "time_tv_context"), GOLD, (0, 0, 0, 182), 12, 2)
    draw_center(draw, zone(sp, "time_tv_context"), clean(row.get("time_et") or row.get("start_time_et") or row.get("context") or "TIME • TV • CONTEXT").upper(), font(23, True), INK)
    used_logos = 0
    used_logos += int(logo_or_text(img, draw, away, zone(sp, "left_logo_slot"), aliases, logos, GOLD))
    used_logos += int(logo_or_text(img, draw, home, zone(sp, "right_logo_slot"), aliases, logos, PURPLE))
    draw_center(draw, zone(sp, "matchup_center"), "VS", font(42, True), INK, 1)
    panel(draw, zone(sp, "debate_question"), ORANGE, (0, 0, 0, 172), 12, 2)
    draw_center(draw, zone(sp, "debate_question"), "WHO HAS THE EDGE TONIGHT?", fit(draw, "WHO HAS THE EDGE TONIGHT?", zone(sp, "debate_question")[2] - 40, 38, 22), INK)
    lower = zone(sp, "active_lower_module")
    player = select_player(away, aliases, pidx) or select_player(home, aliases, pidx)
    used_players = 0
    if player and paste_player(img, draw, player, lower):
        used_players = 1
    else:
        panel(draw, lower, GOLD, (0, 0, 0, 164), 12, 2)
        draw.text((lower[0] + 35, lower[1] + 34), "WATCH POINT", font=font(28, True), fill=GOLD)
        draw_wrapped(draw, (lower[0] + 35, lower[1] + 86, lower[2] - 70, 120), "PACE • STARS • LATE-GAME EDGE", 34, INK, 2)
    return img, {"player_assets_used": used_players, "team_logo_count": used_logos, "player_names": player.get("name") if player else ""}


def render_final(row: Dict[str, Any], template_id: str, reg: Dict[str, Dict[str, Any]], aliases: Dict[str, str], logos: Dict[str, str], pidx: Dict[str, List[Dict[str, str]]]) -> Tuple[Image.Image, Dict[str, Any]]:
    sp = spec(template_id)
    size = (sp["canvas"]["width"], sp["canvas"]["height"])
    img = make_background(template_id, size, reg)
    draw = ImageDraw.Draw(img, "RGBA")
    paste_badge(img, sp)
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name") or "PRIMARY TEAM")
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name") or "SECONDARY TEAM")
    s1, s2 = score_parts(row)
    # Keep the approved GAME RECAP / FINAL SCORE masthead from the baseline skin.
    if "context_row" in sp["zones"]:
        panel(draw, zone(sp, "context_row"), GOLD, (0,0,0,172), 9, 2)
        draw_center(draw, zone(sp, "context_row"), f"FINAL • {clean(row.get('league') or 'WNBA')} • {clean(row.get('date') or row.get('event_date_local') or '')}".upper(), font(21 if size[1] == 1350 else 24, True), INK)
    used_logos = 0
    for name, team, accent in [("primary_logo_slot", winner, GOLD), ("secondary_logo_slot", loser, MUTED)]:
        if name in sp["zones"]:
            used_logos += int(logo_or_text(img, draw, team, zone(sp, name), aliases, logos, accent))
    # Repaint only registered dynamic text/score zones with darker plates, preserving approved template skin.
    if "primary_team" in sp["zones"]:
        soft_cover(draw, zone(sp, "primary_team"), (0,0,0,148), 6)
        draw_wrapped(draw, zone(sp, "primary_team"), winner.upper(), 42 if size[1] == 1350 else 34, INK, 2, True)
    if "primary_score" in sp["zones"]:
        soft_cover(draw, zone(sp, "primary_score"), (0,0,0,112), 10)
        draw_center(draw, zone(sp, "primary_score"), s1, fit(draw, s1, zone(sp, "primary_score")[2], 168 if size[1] == 1350 else 156, 62), GOLD, 1)
    if "secondary_team" in sp["zones"]:
        soft_cover(draw, zone(sp, "secondary_team"), (0,0,0,132), 6)
        draw_wrapped(draw, zone(sp, "secondary_team"), loser.upper(), 34 if size[1] == 1350 else 28, MUTED, 2, True)
    if "secondary_score" in sp["zones"]:
        soft_cover(draw, zone(sp, "secondary_score"), (0,0,0,92), 8)
        draw_center(draw, zone(sp, "secondary_score"), s2, fit(draw, s2, zone(sp, "secondary_score")[2], 104 if size[1] == 1350 else 96, 46), MUTED, 1)
    used_players = 0
    player_names = ""
    if template_id == "hsd_game_recap_final_score_b" and "approved_player_photo_slot" in sp["zones"]:
        player = select_player(winner, aliases, pidx)
        if player and paste_player(img, draw, player, zone(sp, "approved_player_photo_slot")):
            used_players = 1; player_names = player.get("name", "")
        else:
            panel(draw, zone(sp, "approved_player_photo_slot"), PINK, (0,0,0,112), 6, 2)
            draw_center(draw, zone(sp, "approved_player_photo_slot"), "APPROVED PLAYER\nPHOTO SLOT", font(24, True), PINK)
    if "key_performer" in sp["zones"]:
        panel(draw, zone(sp, "key_performer"), GOLD, (0,0,0,148), 6, 2)
        draw_center(draw, zone(sp, "key_performer"), clean(row.get("key_performer") or "KEY PERFORMER"), font(22, True), INK)
    hook_key = "hook_takeaway" if "hook_takeaway" in sp["zones"] else "hook_question"
    if hook_key in sp["zones"]:
        panel(draw, zone(sp, hook_key), ORANGE, (0,0,0,152), 8, 2)
        draw_wrapped(draw, zone(sp, hook_key), clean(row.get("summary") or row.get("hook") or "WHAT CHANGED THE GAME?"), 30 if size[1] == 1350 else 34, INK, 2)
    return img, {"player_assets_used": used_players, "team_logo_count": used_logos, "player_names": player_names}


def fixture_rows() -> List[Dict[str, Any]]:
    return [
        {"kind":"preview", "event_id":"fixture-preview", "headline":"Atlanta Dream at Indiana Fever", "home_team_name":"Indiana Fever", "away_team_name":"Atlanta Dream", "time_et":"7:00 PM ET"},
        {"kind":"final", "event_id":"fixture-final", "headline":"Golden State Valkyries beat Dallas Wings", "winner_team_name":"Golden State Valkyries", "loser_team_name":"Dallas Wings", "score_display":"88-82", "league":"WNBA", "date":"June 19, 2026", "summary":"Statement win with late-game control."}
    ]


def render_rows(fixtures: bool) -> List[Dict[str, Any]]:
    rows = read_rows_for_render(fixtures)
    if not rows: rows = fixture_rows()
    return rows


def build_contact(items: List[Dict[str, Any]]) -> None:
    if not items: return
    cols = 3; tw = 300; th = 390; pad = 30
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + 70) + 80), (244,244,244))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 20), "HSD Template Renderer v4.1 Phase 6D Visual Correction", font=font(28, True), fill=(20,20,20))
    for i, it in enumerate(items):
        p = Path(it["output_path"])
        if not p.exists(): continue
        im = Image.open(p).convert("RGB"); im.thumbnail((tw, th), Image.Resampling.LANCZOS)
        x = pad + (i % cols) * (tw + pad); y = 70 + (i // cols) * (th + 70)
        sheet.paste(im, (x + (tw - im.width)//2, y))
        d.text((x, y + th + 8), f"{it['template_id']} • {it['platform']}", font=font(14, True), fill=(20,20,20))
        d.text((x, y + th + 28), clean(it.get("headline"))[:38], font=font(13, False), fill=(80,80,80))
    sheet.save(CONTACT, quality=92)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    reg = template_registry()
    aliases, logos = team_data()
    pidx = player_index()
    shutil.rmtree(RENDERS, ignore_errors=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    rows = render_rows(args.fixtures)
    manifest: List[Dict[str, Any]] = []
    errors: List[str] = []
    for row in rows:
        try:
            if row.get("kind") == "preview":
                for platform in ["ig_feed", "threads"]:
                    img, meta = render_tonight(row, "hsd_tonight_in_the_w_a", reg, aliases, logos, pidx)
                    out = RENDERS / platform / f"{slug(row.get('headline'))}__tonight_a.png"
                    out.parent.mkdir(parents=True, exist_ok=True); img.convert("RGB").save(out, quality=96)
                    manifest.append({"item_id": f"{row.get('event_id')}::{platform}::hsd_tonight_in_the_w_a", "source_id": row.get("event_id"), "template_id":"hsd_tonight_in_the_w_a", "platform":platform, "headline": row.get("headline"), "output_path":out.as_posix(), "width":img.width, "height":img.height, "variant":"A", "player_assets_used":meta["player_assets_used"], "player_names":meta["player_names"], "team_logo_count":meta["team_logo_count"], "review_only":"true", "status":"rendered_review", "notes":"Template Renderer v4.1 visual correction proof. Human review required."})
            if row.get("kind") == "final":
                for template_id, platform in [("hsd_game_recap_final_score_a","ig_feed"), ("hsd_game_recap_final_score_a","threads"), ("hsd_game_recap_final_score_b","ig_feed"), ("hsd_game_recap_final_score_c_story","stories")]:
                    img, meta = render_final(row, template_id, reg, aliases, logos, pidx)
                    out = RENDERS / platform / f"{slug(row.get('headline'))}__{template_id}.png"
                    out.parent.mkdir(parents=True, exist_ok=True); img.convert("RGB").save(out, quality=96)
                    manifest.append({"item_id": f"{row.get('event_id')}::{platform}::{template_id}", "source_id": row.get("event_id"), "template_id":template_id, "platform":platform, "headline": row.get("headline"), "output_path":out.as_posix(), "width":img.width, "height":img.height, "variant":spec(template_id).get("variant"), "player_assets_used":meta["player_assets_used"], "player_names":meta["player_names"], "team_logo_count":meta["team_logo_count"], "review_only":"true", "status":"rendered_review", "notes":"Template Renderer v4.1 visual correction proof. Human review required."})
        except Exception as exc:
            errors.append(f"{row.get('headline')}: {type(exc).__name__}: {exc}")
    write_csv(MANIFEST_CSV, manifest, MANIFEST_FIELDS)
    payload = {"version":VERSION, "generated_at_utc":now(), "review_only":True, "renderer_cutover_allowed":False, "template_skin_mode": True, "target_templates":sorted(TARGET_TEMPLATES), "rendered_count":len(manifest), "errors":errors, "items":manifest}
    MANIFEST_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    build_contact(manifest)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for it in manifest:
            p = Path(it["output_path"])
            if p.exists(): z.write(p, p.relative_to(OUT.parent).as_posix())
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_MD.write_text("\n".join(["# HSD Template Renderer v4.1 Phase 6D Visual Correction", "", f"Version: `{VERSION}`", f"Rendered: `{len(manifest)}`", f"Errors: `{len(errors)}`", "", "Phase 6D switches to approved-template skin mode and repaints only registered dynamic zones.", "Renderer cutover remains blocked. These are review-only correction proofs.", ""]), encoding="utf-8")
    print(json.dumps({"version":VERSION, "rendered":len(manifest), "errors":errors, "out":OUT.as_posix()}, indent=2))
    if args.strict and (errors or not manifest): return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
