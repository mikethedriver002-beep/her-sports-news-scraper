from __future__ import annotations

import csv
import json
import math
import re
import runpy
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

VERSION = "v2.0-approved-template-compiler-review-only"
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2")
IMG_DIR = OUT_DIR / "renders"
MANIFEST_CSV = OUT_DIR / "hsd_template_renderer_v2_manifest.csv"
MANIFEST_JSON = OUT_DIR / "hsd_template_renderer_v2_manifest.json"
REPORT_MD = OUT_DIR / "hsd_template_renderer_v2_report.md"
ZIP_PATH = OUT_DIR / "hsd_template_renderer_v2_renders.zip"
RENDER_MAP_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping/hsd_template_render_map.json")
RENDER_MAP_SCRIPT = Path("scripts/generate_hsd_template_render_map_v1.py")
REGISTRY = Path("config/graphics/template_registry_v1.json")
CONTRACT = Path("results_contract_v2.csv")
FINALS = Path("today_final_results.csv")
BRAND_POLICY = Path("config/graphics/brand_policy_v1.json")
LOGOS_CSV = Path("data/asset_registry/wnba/team_logos.csv")
TEAMS_CSV = Path("data/asset_registry/wnba/teams.csv")
ALIASES_CSV = Path("data/asset_registry/wnba/team_aliases.csv")
FIELDS = ["item_id", "template_id", "platform", "mode", "headline", "output_path", "width", "height", "status", "review_only", "notes"]
BG = (5, 7, 14)
INK = (246, 248, 255)
MUTED = (168, 177, 195)
GOLD = (235, 184, 76)
ORANGE = (242, 117, 55)
PURPLE = (165, 89, 255)
BLUE = (74, 157, 255)
GREEN = (82, 191, 133)
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
        choices += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    choices += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
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


def draw_wrapped(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = False, max_lines: int = 3) -> None:
    x, y, w, h = box
    f = fit(draw, text, w, size, max(18, min(size, 24)), bold)
    lines = wrap(draw, text, f, w, max_lines)
    gap = 8
    total = len(lines) * (f.size + gap)
    yy = y + max(0, (h - total) // 2)
    for line in lines:
        draw.text((x, yy), line, font=f, fill=fill)
        yy += f.size + gap


def draw_center(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, size: int, fill=INK, bold: bool = True) -> None:
    x, y, w, h = box
    f = fit(draw, text, w, size, 18, bold)
    b = draw.textbbox((0, 0), text, font=f)
    draw.text((x + (w - (b[2] - b[0])) // 2, y + (h - (b[3] - b[1])) // 2), text, font=f, fill=fill)


def rect(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], outline=(255, 255, 255, 80), fill=(255, 255, 255, 12), width: int = 2, radius: int = 22) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=outline, fill=fill, width=width)


def load_registry() -> Dict[str, Dict[str, Any]]:
    data = load_json(REGISTRY)
    return {row.get("template_id", ""): row for row in data.get("families", []) if row.get("template_id")}


def source_index() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in read_csv(CONTRACT):
        for key in ["event_id", "dedupe_key"]:
            if row.get(key):
                out[row[key]] = row
    for row in read_csv(FINALS):
        for key in ["event_uid", "canonical_key"]:
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
    tid = resolve_team(name, aliases)
    path = Path(clean(logos.get(tid, "")))
    if not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


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
    x, y = (52, 48) if story else (48, 42)
    img.alpha_composite(b, (x, y))


def background(size: Tuple[int, int], accent: Tuple[int, int, int], accent2: Tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(BG[0] * (1 - t) + 15 * t)
        g = int(BG[1] * (1 - t) + 16 * t)
        b = int(BG[2] * (1 - t) + 25 * t)
        d.line((0, y, w, y), fill=(r, g, b, 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-300, 120, int(w * 0.72), int(h * 0.65)), fill=(*accent, 70))
    gd.ellipse((int(w * 0.35), int(h * 0.2), w + 420, h + 260), fill=(*accent2, 58))
    glow = glow.filter(ImageFilter.GaussianBlur(32))
    img.alpha_composite(glow)
    for x in range(-w, w * 2, 210):
        d.polygon([(x, 0), (x + 24, 0), (x + w + 24, h), (x + w, h)], fill=(255, 255, 255, 8))
    return img


def team_slot(img: Image.Image, draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], label: str, logo: Image.Image | None, accent=GOLD) -> None:
    rect(draw, box, outline=(*accent, 165), fill=(255, 255, 255, 12), width=2, radius=26)
    x, y, w, h = box
    if logo:
        lg = logo.copy()
        lg.thumbnail((w - 34, h - 34), Image.LANCZOS)
        img.alpha_composite(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2))
    else:
        draw_center(draw, box, label.upper(), 30, fill=MUTED, bold=True)


def canvas_for(row: Dict[str, Any]) -> Tuple[int, int]:
    return (1080, 1920) if row.get("platform") == "stories" else (1080, 1350)


def event_data(map_row: Dict[str, Any], index: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    sid = clean(map_row.get("source_id"))
    if sid in index:
        return index[sid]
    if "::" in clean(map_row.get("item_id")):
        first = clean(map_row.get("item_id")).split("::")[0]
        return index.get(first, {})
    return {}


def final_names(row: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    winner = clean(row.get("winner_team_name") or row.get("winner") or row.get("home_team_name") or row.get("home_team_display") or "PRIMARY TEAM")
    loser = clean(row.get("loser_team_name") or row.get("loser") or row.get("away_team_name") or row.get("away_team_display") or "SECONDARY TEAM")
    sh = clean(row.get("score_home") or row.get("home_score"))
    sa = clean(row.get("score_away") or row.get("away_score"))
    home = clean(row.get("home_team_name") or row.get("home_team_display"))
    if winner and home and winner == home:
        score = f"{sh}-{sa}" if sh and sa else clean(row.get("score_display") or row.get("final_score_display") or "00-00")
    else:
        score = f"{sa}-{sh}" if sh and sa else clean(row.get("score_display") or row.get("final_score_display") or "00-00")
    date = clean(row.get("event_date_local") or row.get("scheduled_date_local") or "")
    return winner, loser, score, clean(row.get("league") or row.get("league_norm") or "WNBA"), date


def render_game_final(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    story = map_row.get("platform") == "stories"
    size = canvas_for(map_row)
    img = background(size, GOLD, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    winner, loser, score, league, date = final_names(src)
    if story:
        draw_center(d, (90, 150, 900, 170), "QUICK FINAL", 112, GOLD, True)
        d.text((88, 360), f"{league}  •  {date}  •  FINAL".upper(), font=font(32, True), fill=INK)
        team_slot(img, d, (80, 500, 230, 230), "APPROVED LOGO", load_logo(winner, aliases, logos), GOLD)
        draw_wrapped(d, (340, 520, 360, 120), winner.upper(), 64, INK, True, 2)
        draw_center(d, (700, 470, 300, 300), score.split("-")[0] if "-" in score else score, 160, GOLD, True)
        team_slot(img, d, (80, 840, 230, 230), "APPROVED LOGO", load_logo(loser, aliases, logos), MUTED)
        draw_wrapped(d, (340, 880, 360, 110), loser.upper(), 48, MUTED, True, 2)
        if "-" in score:
            draw_center(d, (720, 820, 260, 250), score.split("-")[-1], 128, MUTED, True)
        rect(d, (80, 1210, 920, 120), outline=(255, 255, 255, 70), fill=(0, 0, 0, 80))
        draw_center(d, (110, 1220, 860, 90), "KEY PERFORMER / TAKEAWAY", 42, INK, True)
        draw_center(d, (90, 1430, 900, 160), clean(src.get("summary") or "QUESTION / CTA"), 54, GOLD, True)
    else:
        d.text((82, 150), "GAME RECAP", font=font(64, True), fill=(255, 255, 255, 40))
        draw_center(d, (180, 235, 720, 80), "FINAL SCORE", 58, GOLD, True)
        d.text((240, 345), f"FINAL  •  {league}  •  {date}".upper(), font=font(30, True), fill=INK)
        team_slot(img, d, (60, 460, 250, 250), "APPROVED LOGO", load_logo(winner, aliases, logos), GOLD)
        draw_wrapped(d, (340, 480, 380, 145), winner.upper(), 76, INK, True, 2)
        draw_center(d, (760, 430, 260, 290), score.split("-")[0] if "-" in score else score, 150, GOLD, True)
        team_slot(img, d, (60, 760, 220, 220), "APPROVED LOGO", load_logo(loser, aliases, logos), MUTED)
        draw_wrapped(d, (340, 790, 370, 120), loser.upper(), 58, MUTED, True, 2)
        if "-" in score:
            draw_center(d, (760, 750, 230, 220), score.split("-")[-1], 104, MUTED, True)
        rect(d, (60, 1035, 960, 90), outline=(*GOLD, 180), fill=(0, 0, 0, 80))
        draw_center(d, (80, 1042, 920, 70), "KEY PERFORMER  •  TEXT-ONLY STRIP", 34, INK, True)
        draw_center(d, (90, 1180, 900, 95), "STATEMENT WIN.", 54, GOLD, True)
    return img


def render_tonight(map_row: Dict[str, Any], src: Dict[str, str], badge, aliases, logos) -> Image.Image:
    img = background((1080, 1350), ORANGE, PURPLE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, False)
    home = clean(src.get("home_team_name") or "TEAM ONE")
    away = clean(src.get("away_team_name") or "TEAM TWO")
    time = clean(src.get("status") or src.get("scheduled_start_utc") or "TIME / TV / CONTEXT")
    draw_center(d, (120, 100, 840, 120), "TONIGHT", 110, GOLD, True)
    draw_center(d, (120, 230, 840, 80), "IN THE W", 56, INK, True)
    rect(d, (240, 350, 600, 62), outline=(*GOLD, 150), fill=(0, 0, 0, 90))
    draw_center(d, (250, 355, 580, 52), time.upper(), 32, INK, True)
    team_slot(img, d, (70, 490, 250, 250), "APPROVED LOGO", load_logo(home, aliases, logos), GOLD)
    team_slot(img, d, (760, 490, 250, 250), "APPROVED LOGO", load_logo(away, aliases, logos), PURPLE)
    draw_wrapped(d, (340, 500, 400, 180), f"{away.upper()}\nVS\n{home.upper()}", 56, INK, True, 3)
    rect(d, (130, 820, 820, 115), outline=(*GOLD, 190), fill=(*GOLD, 52), radius=16)
    draw_center(d, (150, 830, 780, 92), "WHO NEEDS THIS ONE MORE?", 48, (5, 7, 14), True)
    rect(d, (80, 990, 920, 170), outline=(255, 255, 255, 70), fill=(0, 0, 0, 78))
    draw_center(d, (100, 1002, 880, 60), "KEY MATCHUP / WATCH POINT", 38, GOLD, True)
    draw_wrapped(d, (130, 1070, 820, 70), "One active lower module per post.", 28, INK, False, 2)
    return img


def final_rows() -> List[Dict[str, str]]:
    rows = read_csv(FINALS)
    out = [r for r in rows if clean(r.get("status_norm")).lower() == "final" or clean(r.get("game_state")).lower() == "final"]
    return out


def render_last_night(map_row: Dict[str, Any], badge, aliases, logos) -> Image.Image:
    platform = clean(map_row.get("platform"))
    story = platform == "stories"
    size = (1080, 1920) if story else (1080, 1350)
    img = background(size, PURPLE, ORANGE)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    finals = final_rows()[:5]
    draw_center(d, (110, 110 if not story else 140, 860, 120), "LAST NIGHT", 92 if not story else 106, INK, True)
    draw_center(d, (110, 230 if not story else 280, 860, 70), "IN THE W", 48 if not story else 56, GOLD, True)
    d.text((90, 330 if not story else 410), f"{len(finals)} FINALS. ONE RECAP.".upper(), font=font(30, True), fill=INK)
    start = 410 if not story else 520
    row_h = 130 if not story else 155
    for i, r in enumerate(finals[:4 if not story else 5]):
        y = start + i * (row_h + 20)
        winner, loser, score, league, date = final_names(r)
        rect(d, (70, y, 940, row_h), outline=(*GOLD, 120), fill=(0, 0, 0, 85), radius=18)
        team_slot(img, d, (92, y + 20, 80, 80), "LOGO", load_logo(winner, aliases, logos), GOLD)
        draw_wrapped(d, (190, y + 24, 490, 72), winner.upper(), 36, INK, True, 2)
        draw_center(d, (720, y + 16, 230, 88), score, 56, GOLD, True)
    cta_y = 1120 if not story else 1460
    rect(d, (70, cta_y, 940, 120), outline=(*PURPLE, 150), fill=(0, 0, 0, 85), radius=20)
    draw_center(d, (90, cta_y + 12, 900, 96), "WHICH RESULT MATTERED MOST?", 40 if not story else 46, INK, True)
    return img


def render_generic(map_row: Dict[str, Any], badge) -> Image.Image:
    size = canvas_for(map_row)
    story = map_row.get("platform") == "stories"
    img = background(size, BLUE, GOLD)
    d = ImageDraw.Draw(img)
    paste_badge(img, badge, story)
    draw_center(d, (80, 170, 920, 170), clean(map_row.get("template_family") or "HSD TEMPLATE").upper(), 70, INK, True)
    draw_center(d, (80, 390, 920, 150), clean(map_row.get("template_variant") or "REVIEW RENDER"), 46, GOLD, True)
    rect(d, (80, 620, 920, 240), outline=(*GOLD, 150), fill=(0, 0, 0, 80))
    draw_wrapped(d, (120, 650, 840, 180), clean(map_row.get("headline") or "HEADLINE"), 52, INK, True, 3)
    rect(d, (80, 940 if not story else 1180, 920, 160), outline=(255, 255, 255, 72), fill=(0, 0, 0, 70))
    draw_center(d, (100, 965 if not story else 1210, 880, 100), "APPROVED TEMPLATE COMPILE", 36, MUTED, True)
    return img


def render_one(map_row: Dict[str, Any], source: Dict[str, str], badge, aliases, logos) -> Image.Image:
    tid = clean(map_row.get("template_id"))
    if tid == "game_recap_final_score.a.v1" or tid == "game_recap_final_score.c.story.v1":
        return render_game_final(map_row, source, badge, aliases, logos)
    if tid == "tonight_in_the_w.a.v1":
        return render_tonight(map_row, source, badge, aliases, logos)
    if tid.startswith("last_night_in_the_w"):
        return render_last_night(map_row, badge, aliases, logos)
    return render_generic(map_row, badge)


def main() -> None:
    if not RENDER_MAP_JSON.exists() and RENDER_MAP_SCRIPT.exists():
        runpy.run_path(RENDER_MAP_SCRIPT.as_posix(), run_name="__main__")
    render_map = load_json(RENDER_MAP_JSON)
    rows = render_map.get("rows", [])
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(IMG_DIR)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    badge = load_badge()
    aliases, logos = team_logo_registry()
    index = source_index()
    manifest: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        if row.get("status") != "mapped":
            continue
        src = event_data(row, index)
        img = render_one(row, src, badge, aliases, logos)
        width, height = img.size
        name = f"{i:02d}_{slug(row.get('platform'))}_{slug(row.get('template_id'))}_{slug(row.get('headline'))}.png"
        out = IMG_DIR / name
        img.convert("RGB").save(out, quality=95)
        manifest.append({
            "item_id": row.get("item_id"),
            "template_id": row.get("template_id"),
            "platform": row.get("platform"),
            "mode": row.get("mode"),
            "headline": row.get("headline"),
            "output_path": out.as_posix(),
            "width": width,
            "height": height,
            "status": "rendered_review",
            "review_only": "true",
            "notes": "Template Renderer v2 compile proof. Human review required before publishing.",
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
    md = [
        "# HSD Template Renderer v2",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Version: `{VERSION}`",
        "",
        "## Policy",
        "",
        "- Review-only compile proof.",
        "- Uses the template render map and approved template IDs.",
        "- Human review required before publishing.",
        "",
        "## Summary",
        "",
        f"- Rendered files: `{len(manifest)}`",
        f"- Zip: `{ZIP_PATH.as_posix()}`",
        "",
    ]
    for item in manifest:
        md.append(f"- `{item['template_id']}` | {item['platform']} | {item['headline']}")
    REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": len(manifest), "out_dir": OUT_DIR.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
