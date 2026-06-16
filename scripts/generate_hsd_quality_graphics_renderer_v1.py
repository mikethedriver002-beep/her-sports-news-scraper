from __future__ import annotations

import csv
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

VERSION = "v1.0-hsd-quality-graphics-renderer"
OUT_ROOT = Path("outputs/latest/HSD_QUALITY_GRAPHICS")
MANIFEST = Path("hsd_quality_graphics_manifest.csv")
REPORT = Path("hsd_quality_graphics_report.md")
CONTRACT = Path("results_contract_v2.csv")
SLATE = Path("daily_slate_plan.csv")
TEAMS_CSV = Path("data/asset_registry/wnba/teams.csv")
ALIASES_CSV = Path("data/asset_registry/wnba/team_aliases.csv")
LOGOS_CSV = Path("data/asset_registry/wnba/team_logos.csv")
WATERMARKS = [Path("assets/branding/official_hsd_watermark.png"), Path("data/assets/brand/hsd_watermark.png"), Path("data/assets/brand/hsd_official_watermark.png")]
CANVASES = {"ig_feed": (1080, 1350), "threads": (1080, 1350), "stories": (1080, 1920)}
FIELDS = ["event_id", "platform", "row_kind", "headline", "output_path", "width", "height", "used_home_logo", "used_away_logo", "status", "notes"]
BG = (5, 8, 16)
INK = (248, 250, 255)
MUTED = (172, 184, 205)
WHITE = (255, 255, 255)
GOLD = (246, 201, 80)
PINK = (245, 89, 160)
BLUE = (53, 154, 255)


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "graphic"


def norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


def font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, size: int, min_size: int, bold: bool = True):
    while size > min_size:
        f = font(size, bold)
        if text_w(draw, text, f) <= max_w:
            return f
        size -= 2
    return font(min_size, bold)


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
        lines[-1] = lines[-1].rstrip("., ") + "…"
    return lines[:max_lines]


def draw_wrapped(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, max_w: int, max_lines: int, gap: int = 8) -> int:
    for line in wrap(draw, text, fnt, max_w, max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        y = draw.textbbox((x, y), line, font=fnt)[3] + gap
    return y


def parse_hex(v: str, fallback: Tuple[int, int, int]) -> Tuple[int, int, int]:
    s = clean(v).lstrip("#")
    if len(s) == 6:
        try:
            return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
        except Exception:
            pass
    return fallback


def load_registry() -> Tuple[Dict[str, Dict[str, str]], Dict[str, str], Dict[str, str]]:
    teams = {r.get("team_id", ""): r for r in read_csv(TEAMS_CSV) if r.get("team_id")}
    aliases: Dict[str, str] = {}
    for tid, row in teams.items():
        for key in ["team_name", "nickname", "city"]:
            aliases[norm(row.get(key, ""))] = tid
    for row in read_csv(ALIASES_CSV):
        if row.get("team_id"):
            aliases[norm(row.get("alias", ""))] = row["team_id"]
    logos = {r.get("team_id", ""): r.get("file_path", "") for r in read_csv(LOGOS_CSV) if r.get("team_id")}
    return teams, aliases, logos


def resolve_team(name: str, aliases: Dict[str, str]) -> str:
    n = norm(name)
    if n in aliases:
        return aliases[n]
    for alias, tid in aliases.items():
        if alias and alias in n:
            return tid
    return ""


def team_name(tid: str, teams: Dict[str, Dict[str, str]]) -> str:
    return clean(teams.get(tid, {}).get("team_name") or tid.replace("_", " ").title())


def team_color(tid: str, teams: Dict[str, Dict[str, str]], fallback: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return parse_hex(teams.get(tid, {}).get("primary_hex", ""), fallback)


def load_logo(tid: str, logos: Dict[str, str]) -> Image.Image | None:
    p = Path(clean(logos.get(tid, "")))
    if not p.exists():
        return None
    try:
        return Image.open(p).convert("RGBA")
    except Exception:
        return None


def load_watermark() -> Image.Image | None:
    for p in WATERMARKS:
        if p.exists():
            try:
                return Image.open(p).convert("RGBA")
            except Exception:
                pass
    return None


def paste_watermark(img: Image.Image, wm: Image.Image | None) -> None:
    if wm is None:
        return
    mark = wm.copy()
    mark.thumbnail((92, 92), Image.LANCZOS)
    chip = Image.new("RGBA", (mark.width + 34, mark.height + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(chip)
    d.rounded_rectangle((0, 0, chip.width - 1, chip.height - 1), radius=20, fill=(7, 10, 18, 224), outline=(255, 255, 255, 52), width=1)
    chip.alpha_composite(mark, (17, 15))
    img.alpha_composite(chip, (54, 42))


def make_bg(size: Tuple[int, int], a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    for y in range(h):
        blend = y / max(h - 1, 1)
        r = int(BG[0] * (1 - blend) + 12 * blend)
        g = int(BG[1] * (1 - blend) + 15 * blend)
        bb = int(BG[2] * (1 - blend) + 28 * blend)
        d.line((0, y, w, y), fill=(r, g, bb, 255))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-360, -290, int(w * 0.82), int(h * 0.58)), fill=(*a, 96))
    gd.ellipse((int(w * 0.38), int(h * 0.48), w + 420, h + 360), fill=(*b, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(glow)
    for x in range(-w, w * 2, 182):
        d.polygon([(x, 0), (x + 24, 0), (x + w + 24, h), (x + w, h)], fill=(255, 255, 255, 11))
    d.line((0, int(h * 0.13), w, int(h * 0.13) - 170), fill=(*a, 140), width=10)
    d.line((0, int(h * 0.88), w, int(h * 0.88) - 170), fill=(*b, 130), width=10)
    return img


def logo_badge(img: Image.Image, logo: Image.Image | None, center: Tuple[int, int], size: int, accent: Tuple[int, int, int]) -> None:
    x, y = center
    d = ImageDraw.Draw(img)
    d.ellipse((x - size//2 - 12, y - size//2 - 12, x + size//2 + 12, y + size//2 + 12), fill=(*accent, 92))
    d.ellipse((x - size//2, y - size//2, x + size//2, y + size//2), fill=(245, 248, 255, 245), outline=(255, 255, 255, 170), width=3)
    if logo:
        lg = logo.copy()
        lg.thumbnail((size - 34, size - 34), Image.LANCZOS)
        img.alpha_composite(lg, (x - lg.width//2, y - lg.height//2))


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color: Tuple[int, int, int]) -> None:
    label = clean(text).upper()
    f = font(26, True)
    w = text_w(draw, label, f)
    draw.rounded_rectangle((x, y, x + w + 42, y + 42), radius=18, fill=(*color, 245))
    draw.text((x + 21, y + 7), label, font=f, fill=WHITE)


def platform_slug(platform: str) -> str:
    return {"ig_feed":"ig_feed", "threads":"threads", "stories":"stories"}[platform]


def render_result(row: Dict[str, str], size: Tuple[int, int], platform: str, teams, aliases, logos, wm) -> Tuple[Image.Image, Dict[str, str]]:
    home = row["home_team_name"]; away = row["away_team_name"]
    winner = row["winner_team_name"] or home
    loser = row["loser_team_name"] or away
    win_id = resolve_team(winner, aliases); lose_id = resolve_team(loser, aliases)
    a = team_color(win_id, teams, BLUE); b = team_color(lose_id, teams, GOLD)
    img = make_bg(size, a, b); d = ImageDraw.Draw(img); W, H = size; paste_watermark(img, wm)
    top = 170 if H <= 1350 else 250
    chip(d, 82, top, "FINAL", a)
    d.text((82, top + 62), "FINAL SCORE", font=font(40, True), fill=MUTED)
    headline = f"{winner.upper()}"
    hf = fit_font(d, headline, W - 164, 86 if H <= 1350 else 110, 54, True)
    d.text((82, top + 116), headline, font=hf, fill=INK)
    score_y = top + (230 if H <= 1350 else 330)
    score_text = f"{row.get('score_home') if winner == home else row.get('score_away')}–{row.get('score_away') if winner == home else row.get('score_home')}"
    d.text((82, score_y), score_text, font=font(154 if H <= 1350 else 204, True), fill=INK)
    d.text((86, score_y + (154 if H <= 1350 else 206)), "OVER", font=font(34 if H <= 1350 else 44, True), fill=MUTED)
    lf = fit_font(d, loser.upper(), W - 164, 58 if H <= 1350 else 72, 38, True)
    d.text((82, score_y + (198 if H <= 1350 else 260)), loser.upper(), font=lf, fill=(*b, 255))
    badge_y = score_y + (76 if H <= 1350 else 104)
    logo_badge(img, load_logo(win_id, logos), (W - 250, badge_y - 18), 178 if H <= 1350 else 220, a)
    logo_badge(img, load_logo(lose_id, logos), (W - 116, badge_y + 118), 112 if H <= 1350 else 142, b)
    mid_y = H - (330 if H <= 1350 else 430)
    d.rounded_rectangle((76, mid_y, W - 76, mid_y + 150), radius=32, fill=(10, 15, 27, 224), outline=(255,255,255,56), width=2)
    summary = row.get("summary") or row.get("headline")
    draw_wrapped(d, 112, mid_y + 34, summary, font(35 if H <= 1350 else 44, False), INK, W - 224, 3, 9)
    cta = "What was the swing moment?"
    d.text((82, H - 96), cta.upper(), font=font(30 if H <= 1350 else 38, True), fill=(255,255,255,210))
    return img, {"used_home_logo":"yes" if load_logo(resolve_team(home, aliases), logos) else "no", "used_away_logo":"yes" if load_logo(resolve_team(away, aliases), logos) else "no"}


def render_preview(row: Dict[str, str], size: Tuple[int, int], platform: str, teams, aliases, logos, wm) -> Tuple[Image.Image, Dict[str, str]]:
    home = row["home_team_name"]; away = row["away_team_name"]
    home_id = resolve_team(home, aliases); away_id = resolve_team(away, aliases)
    a = team_color(away_id, teams, BLUE); b = team_color(home_id, teams, GOLD)
    img = make_bg(size, a, b); d = ImageDraw.Draw(img); W, H = size; paste_watermark(img, wm)
    top = 170 if H <= 1350 else 250
    chip(d, 82, top, "TONIGHT", GOLD)
    d.text((82, top + 66), "IN THE W", font=font(44 if H <= 1350 else 56, True), fill=MUTED)
    title = f"{away.upper()} AT {home.upper()}"
    tf = fit_font(d, title, W - 164, 76 if H <= 1350 else 96, 42, True)
    d.text((82, top + 128), title, font=tf, fill=INK)
    card_y = top + (270 if H <= 1350 else 380)
    d.rounded_rectangle((70, card_y, W - 70, card_y + (390 if H <= 1350 else 520)), radius=44, fill=(9, 14, 27, 222), outline=(255,255,255,62), width=2)
    logo_badge(img, load_logo(away_id, logos), (250, card_y + (150 if H <= 1350 else 205)), 188 if H <= 1350 else 242, a)
    logo_badge(img, load_logo(home_id, logos), (W - 250, card_y + (150 if H <= 1350 else 205)), 188 if H <= 1350 else 242, b)
    d.text((W//2, card_y + (150 if H <= 1350 else 205)), "AT", font=font(46 if H <= 1350 else 60, True), fill=MUTED, anchor="mm")
    d.text((250, card_y + (280 if H <= 1350 else 375)), away.upper(), font=fit_font(d, away.upper(), 340, 34 if H <= 1350 else 44, 24, True), fill=INK, anchor="ma")
    d.text((W-250, card_y + (280 if H <= 1350 else 375)), home.upper(), font=fit_font(d, home.upper(), 340, 34 if H <= 1350 else 44, 24, True), fill=INK, anchor="ma")
    y = card_y + (430 if H <= 1350 else 590)
    draw_wrapped(d, 82, y, "Who needs this one more?", font(56 if H <= 1350 else 74, True), INK, W - 164, 2, 8)
    d.text((82, H - 96), "DROP YOUR PICK BEFORE TIP".upper(), font=font(30 if H <= 1350 else 38, True), fill=(255,255,255,210))
    return img, {"used_home_logo":"yes" if load_logo(home_id, logos) else "no", "used_away_logo":"yes" if load_logo(away_id, logos) else "no"}


def eligible_rows() -> List[Dict[str, str]]:
    rows = [r for r in read_csv(CONTRACT) if r.get("content_eligibility") == "eligible" and r.get("manual_review") != "Yes" and r.get("league") == "WNBA"]
    slate = read_csv(SLATE)
    rank = {r.get("source_id"): int(r.get("slot_rank") or 99) for r in slate}
    rows.sort(key=lambda r: rank.get(r.get("event_id"), 99))
    return rows[:5]


def main() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    teams, aliases, logos = load_registry()
    wm = load_watermark()
    manifest: List[Dict[str, Any]] = []
    for row in eligible_rows():
        for platform, size in CANVASES.items():
            try:
                if row.get("row_kind") == "result":
                    img, used = render_result(row, size, platform, teams, aliases, logos, wm)
                else:
                    img, used = render_preview(row, size, platform, teams, aliases, logos, wm)
                folder = OUT_ROOT / platform
                folder.mkdir(parents=True, exist_ok=True)
                out = folder / f"{slug(row.get('headline','graphic'))}.png"
                img.convert("RGB").save(out, quality=96)
                manifest.append({"event_id": row.get("event_id"), "platform": platform, "row_kind": row.get("row_kind"), "headline": row.get("headline"), "output_path": out.as_posix(), "width": size[0], "height": size[1], "used_home_logo": used.get("used_home_logo"), "used_away_logo": used.get("used_away_logo"), "status":"rendered", "notes":"HSD quality renderer v1; human review before publishing"})
            except Exception as exc:
                manifest.append({"event_id": row.get("event_id"), "platform": platform, "row_kind": row.get("row_kind"), "headline": row.get("headline"), "output_path": "", "width": size[0], "height": size[1], "used_home_logo":"", "used_away_logo":"", "status":"error", "notes": f"{type(exc).__name__}: {exc}"})
    write_csv(MANIFEST, manifest, FIELDS)
    lines = ["# HSD Quality Graphics Renderer v1", "", f"Generated: `{datetime.now(timezone.utc).isoformat()}`", f"Version: `{VERSION}`", "", "## Policy", "", "- Uses only contract rows, official HSD watermark, and approved registry logos.", "- No player images, no fake athletes, no invented stats.", "- Output is human-review before publish.", "", f"Rendered files: `{sum(1 for r in manifest if r.get('status')=='rendered')}`", "", "## Files", ""]
    for row in manifest:
        lines.append(f"- {row.get('status')} | {row.get('platform')} | {row.get('headline')} | {row.get('output_path') or row.get('notes')}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"quality_graphics_rendered": sum(1 for r in manifest if r.get("status") == "rendered"), "quality_graphics_rows": len(manifest)}, indent=2))


if __name__ == "__main__":
    main()
