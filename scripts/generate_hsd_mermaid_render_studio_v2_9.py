from __future__ import annotations

import csv
import io
import json
import math
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

VERSION = "v2.9.1-visual-polish-pass1-exact-logo-lock"
OUT_DIR = Path("rendered_handoff_graphics")
ZIP_DIR = Path("rendered_handoff_zips")
STATUS = Path("rendered_handoff_status.csv")
MANIFEST = Path("rendered_handoff_manifest.csv")
REPORT = Path("rendered_handoff_qa_report.md")
CONTACT = Path("rendered_handoff_contact_sheet.jpg")
META = Path("rendered_handoff_metadata.json")
PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
WATERMARK_PNGS = [Path("assets/branding/official_hsd_watermark.png"), Path("data/assets/brand/hsd_watermark.png"), Path("data/assets/brand/hsd_official_watermark.png")]
CANVAS = {"IG Feed": (1080, 1350), "Threads": (1080, 1350), "IG Stories": (1080, 1920)}
STATUS_FIELDS = ["packet_id", "platform", "headline", "status", "reason", "rendered_files", "used_watermark", "used_logos", "template", "missing_logos", "used_score_context", "internal_text_found", "decision"]
MANIFEST_FIELDS = ["packet_id", "platform", "headline", "output_path", "width", "height", "used_watermark", "used_logos", "template"]
BG = (6, 9, 18)
INK = (248, 250, 255)
MUTED = (181, 190, 207)
LINE = (52, 62, 90)
BLUE = (75, 139, 255)
PINK = (244, 88, 164)
GOLD = (246, 198, 66)
GREEN = (82, 214, 145)
RED = (240, 80, 80)


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, data: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in data:
            w.writerow({k: r.get(k, "") for k in fields})


def font(size: int, bold: bool = False):
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in choices:
        if p and Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt) -> Tuple[int, int]:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int, max_lines: int = 10) -> List[str]:
    words = clean(text).split()
    if not words:
        return [""]
    lines: List[str] = []
    cur = words[0]
    for word in words[1:]:
        test = cur + " " + word
        if text_size(draw, test, fnt)[0] <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = word
            if len(lines) >= max_lines - 1:
                break
    lines.append(cur)
    return lines[:max_lines]


def draw_block(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, max_w: int, gap: int = 8, max_lines: int = 10) -> int:
    for line in wrap(draw, text, fnt, max_w, max_lines=max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        y = draw.textbbox((x, y), line, font=fnt)[3] + gap
    return y


def load_watermark() -> Tuple[Optional[Image.Image], str]:
    for p in WATERMARK_PNGS:
        if p.exists():
            try:
                return Image.open(p).convert("RGBA"), p.as_posix()
            except Exception:
                pass
    return None, "missing"


def discover_packets() -> List[Path]:
    found: Dict[str, Path] = {}
    for d in PACKET_DIRS:
        if d.exists():
            for z in d.glob("*.zip"):
                if z.name.startswith("rendered_"):
                    continue
                found[z.name] = z
    return [found[k] for k in sorted(found)]


def parse_packet(zp: Path) -> Optional[Dict[str, Any]]:
    try:
        with zipfile.ZipFile(zp) as z:
            data = json.loads(z.read("content_packet.json").decode("utf-8"))
        slot = data.get("slot", {})
        pub = data.get("public_copy", {})
        return {
            "packet_id": data.get("packet_id") or zp.stem,
            "platform": clean(slot.get("platform") or pub.get("platform") or "IG Feed"),
            "headline": clean(pub.get("headline") or slot.get("headline") or zp.stem),
            "league": clean(pub.get("league") or slot.get("league")),
            "content_type": clean(pub.get("content_type") or slot.get("content_type")),
            "hook": clean(pub.get("hook") or slot.get("copy_hook")),
            "first": clean(pub.get("first") or slot.get("first_comment")),
            "slot_id": clean(slot.get("slot_id")),
        }
    except Exception:
        return None


def parse_selected_finals() -> List[Dict[str, str]]:
    finals: List[Dict[str, str]] = []
    for path in [Path("final_score_story_guard_report.md"), Path("ig_story_results_frames.md"), Path("mermaid_master_content_board.md")]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"-\s*([A-Za-z .]+?)\s+(\d{2,3})\s*[·\-–]\s*([A-Za-z .]+?)\s+(\d{2,3})", text):
            a, sa, b, sb = [clean(x) for x in m.groups()]
            finals.append({"team_a": a, "score_a": sa, "team_b": b, "score_b": sb})
    seen = set()
    unique = []
    for g in finals:
        key = tuple(g.values())
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique


def teams_from_headline(headline: str) -> List[str]:
    h = clean(headline)
    m = re.match(r"(.+?)\s+beat\s+(.+)$", h, flags=re.I)
    if m:
        return [m.group(1).strip(), m.group(2).strip()]
    m = re.match(r"(.+?)\s+(?:at|vs\.?|versus)\s+(.+)$", h, flags=re.I)
    if m:
        return [m.group(1).strip(), m.group(2).strip()]
    return []


def approved_logo_registry() -> Dict[str, Path]:
    registry: Dict[str, Path] = {}
    for csv_path in [Path("approved_graphics_assets.csv"), Path("hsd_pipeline_lite_review/files/approved_graphics_assets.csv")]:
        for row in read_csv(csv_path):
            if clean(row.get("entity_type")).lower() != "team":
                continue
            name = clean(row.get("entity_name"))
            if not name:
                continue
            for field in ["master_path", "web_path", "file_path", "asset_path"]:
                val = clean(row.get(field))
                p = Path(val) if val else None
                if p and p.exists() and ("logo" in p.as_posix().lower() or p.suffix.lower() in {".svg", ".png"}):
                    registry[name.lower()] = p
                    break
    return registry


def load_logo_image(path: Path) -> Optional[Image.Image]:
    try:
        if path.suffix.lower() == ".svg":
            try:
                import cairosvg  # type: ignore
                raw = cairosvg.svg2png(url=str(path))
                return Image.open(io.BytesIO(raw)).convert("RGBA")
            except Exception:
                return None
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def logo_path_for(team: str, registry: Dict[str, Path]) -> Optional[Path]:
    key = clean(team).lower()
    if key in registry and registry[key].exists():
        return registry[key]
    team_slug = slug(team)
    search_roots = [Path("data/assets/approved"), Path("assets/reference/wnba/team_logos"), Path("assets/team_logos"), Path("graphics_chat_upload_pack"), Path("ig_story_results_upload_pack"), Path("hsd_pipeline_lite_review")]
    for root in search_roots:
        if not root.exists():
            continue
        matches = []
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
                continue
            low = p.as_posix().lower()
            if team_slug in low and "logo" in low:
                matches.append(p)
        matches.sort(key=lambda p: (p.suffix.lower() != ".png", len(p.as_posix())))
        for p in matches:
            if load_logo_image(p):
                return p
    return None


def required_logo_paths(teams: List[str], registry: Dict[str, Path]) -> Tuple[Dict[str, Path], List[str]]:
    logos: Dict[str, Path] = {}
    missing: List[str] = []
    for t in teams:
        path = logo_path_for(t, registry)
        if path:
            logos[t] = path
        else:
            missing.append(t)
    return logos, missing


def gradient_bg(size: Tuple[int, int], tint: Tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    pix = img.load()
    for y in range(h):
        for x in range(w):
            nx = x / max(1, w)
            ny = y / max(1, h)
            r = int(BG[0] + tint[0] * (0.10 + 0.22 * nx + 0.09 * ny))
            g = int(BG[1] + tint[1] * (0.08 + 0.18 * ny))
            b = int(BG[2] + tint[2] * (0.10 + 0.20 * (1 - nx)))
            pix[x, y] = (min(255, r), min(255, g), min(255, b), 255)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((-260, -260, int(w * .75), int(h * .52)), fill=(*tint, 72))
    d.ellipse((int(w * .55), int(h * .58), w + 280, h + 220), fill=(PINK[0], PINK[1], PINK[2], 58))
    for i in range(-h, w, 150):
        d.line((i, 0, i + h, h), fill=(255, 255, 255, 16), width=2)
    img.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(1)))
    return img


def tint_for(packet: Dict[str, Any]) -> Tuple[int, int, int]:
    if packet.get("league") == "LPGA":
        return (18, 92, 68)
    if packet.get("content_type") == "preview_event":
        return (50, 84, 178)
    if "last night" in packet.get("headline", "").lower():
        return (88, 58, 146)
    return (52, 82, 168)


def paste_watermark(img: Image.Image, wm: Image.Image) -> None:
    mark = wm.copy().convert("RGBA")
    box = mark.getbbox()
    if box:
        mark = mark.crop(box)
    mark.thumbnail((92, 92), Image.LANCZOS)
    chip = Image.new("RGBA", (mark.width + 22, mark.height + 22), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chip)
    cd.rounded_rectangle((0, 0, chip.width - 1, chip.height - 1), radius=18, fill=(255, 255, 255, 24), outline=(255, 255, 255, 44), width=1)
    chip.alpha_composite(mark, (11, 11))
    img.alpha_composite(chip, (54, 46))


def frame(img: Image.Image, packet: Dict[str, Any], template: str, wm: Image.Image) -> ImageDraw.ImageDraw:
    d = ImageDraw.Draw(img)
    w, _ = img.size
    paste_watermark(img, wm)
    label = packet.get("league") or "HSD"
    f = font(25, True)
    tw, _ = text_size(d, label.upper(), f)
    d.rounded_rectangle((w - tw - 94, 50, w - 54, 92), radius=20, fill=(255, 255, 255, 20), outline=(255, 255, 255, 46), width=1)
    d.text((w - tw - 72, 60), label.upper(), font=f, fill=MUTED)
    d.text((54, 126), template.upper(), font=font(22, True), fill=(255, 255, 255, 145))
    d.line((54, 156, w - 54, 156), fill=(255, 255, 255, 28), width=1)
    return d


def logo_chip(path: Path, size: int = 188) -> Image.Image:
    chip = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(chip)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=36, fill=(255, 255, 255, 18), outline=(255, 255, 255, 42), width=2)
    logo = load_logo_image(path)
    if not logo:
        return chip
    logo.thumbnail((size - 44, size - 44), Image.LANCZOS)
    chip.alpha_composite(logo, ((size - logo.width) // 2, (size - logo.height) // 2))
    return chip


def score_for_pair(left: str, right: str, finals: List[Dict[str, str]]) -> Tuple[str, str]:
    for g in finals:
        a, b = g["team_a"], g["team_b"]
        if {a.lower(), b.lower()} == {left.lower(), right.lower()}:
            if a.lower() == left.lower():
                return g["score_a"], g["score_b"]
            return g["score_b"], g["score_a"]
    return "", ""


def render_matchup(packet: Dict[str, Any], wm: Image.Image, registry: Dict[str, Path], finals: List[Dict[str, str]]) -> Tuple[Optional[Image.Image], str, str, List[str], str]:
    teams = teams_from_headline(packet["headline"])
    if len(teams) != 2:
        return None, "blocked", "Could not identify exactly two teams from headline", [], "matchup"
    logos, missing = required_logo_paths(teams, registry)
    if missing:
        return None, "blocked", "Missing required exact team logo(s): " + ", ".join(missing), missing, "matchup"
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = gradient_bg(size, tint_for(packet))
    template_label = "matchup board" if packet.get("content_type") == "preview_event" else "final board"
    d = frame(img, packet, template_label, wm)
    w, h = size
    left, right = teams
    logo_y = 238 if h < 1500 else 360
    img.alpha_composite(logo_chip(logos[left], 188), (96, logo_y))
    img.alpha_composite(logo_chip(logos[right], 188), (w - 284, logo_y))
    s1, s2 = score_for_pair(left, right, finals)
    mid = "FINAL" if packet.get("content_type") == "result_or_recap" else "AT"
    d.rounded_rectangle((w // 2 - 88, logo_y + 48, w // 2 + 88, logo_y + 140), radius=28, fill=(255, 255, 255, 20), outline=(255, 255, 255, 56), width=2)
    d.text((w // 2, logo_y + 94), mid, font=font(34, True), fill=INK, anchor="mm")
    if s1 and s2:
        d.text((190, logo_y + 228), s1, font=font(72, True), fill=GOLD, anchor="ma")
        d.text((w - 190, logo_y + 228), s2, font=font(72, True), fill=GOLD, anchor="ma")
        name_y = logo_y + 302
    else:
        name_y = logo_y + 228
    d.text((190, name_y), left.upper(), font=font(29, True), fill=INK, anchor="ma")
    d.text((w - 190, name_y), right.upper(), font=font(29, True), fill=INK, anchor="ma")
    y = name_y + 70
    title_font = font(76 if h < 1500 else 88, True)
    y = draw_block(d, 82, y, packet["headline"], title_font, INK, w - 164, gap=8, max_lines=3) + 24
    hook = packet.get("hook") or ("Who owns the first run?" if packet.get("content_type") == "preview_event" else "What changed after this result?")
    y = draw_block(d, 86, y, hook, font(38 if h < 1500 else 44, False), MUTED, w - 172, gap=8, max_lines=3) + 28
    accent = BLUE if packet.get("content_type") == "preview_event" else GOLD
    d.rounded_rectangle((82, y, w - 82, y + 12), radius=6, fill=accent)
    cta = packet.get("first") or ("Who needs this one more?" if packet.get("content_type") == "preview_event" else "What changes next?")
    cta_y = h - (210 if h < 1500 else 260)
    d.rounded_rectangle((76, cta_y, w - 76, cta_y + 138), radius=34, fill=(255, 255, 255, 18), outline=(255, 255, 255, 48), width=2)
    draw_block(d, 108, cta_y + 32, cta, font(34, True), INK, w - 216, gap=4, max_lines=2)
    return img, "rendered", "ok", [], "matchup"


def render_editorial(packet: Dict[str, Any], wm: Image.Image) -> Tuple[Image.Image, str]:
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = gradient_bg(size, tint_for(packet))
    d = frame(img, packet, "editorial watch", wm)
    w, h = size
    d.rounded_rectangle((58, 220, 116, h - 190), radius=28, fill=(255, 255, 255, 18), outline=(255, 255, 255, 44), width=1)
    side = packet.get("league") or "HSD"
    for i, ch in enumerate(side.upper()[:12]):
        d.text((87, 260 + i * 38), ch, font=font(24, True), fill=(255, 255, 255, 150), anchor="mm")
    kicker = "LPGA WATCH" if packet.get("league") == "LPGA" else "ON THE BOARD"
    d.text((146, 230), kicker, font=font(34, True), fill=GOLD if packet.get("league") == "LPGA" else BLUE)
    y = 284
    title_font = font(74 if h < 1500 else 84, True)
    y = draw_block(d, 146, y, packet["headline"], title_font, INK, w - 216, gap=8, max_lines=5) + 30
    hook = packet.get("hook") or "A women’s sports story worth keeping on the board."
    y = draw_block(d, 150, y, hook, font(38 if h < 1500 else 44, False), MUTED, w - 232, gap=8, max_lines=4) + 18
    d.rounded_rectangle((150, y, min(w - 90, 150 + 360), y + 12), radius=6, fill=GREEN if packet.get("league") == "LPGA" else PINK)
    cta_y = h - (220 if h < 1500 else 270)
    d.rounded_rectangle((146, cta_y, w - 82, cta_y + 140), radius=36, fill=(255, 255, 255, 18), outline=(255, 255, 255, 42), width=2)
    draw_block(d, 178, cta_y + 34, packet.get("first") or "Are we underrating this story?", font(34, True), INK, w - 270, gap=4, max_lines=2)
    return img, "editorial"


def render_last_night(packet: Dict[str, Any], wm: Image.Image, registry: Dict[str, Path], finals: List[Dict[str, str]]) -> Tuple[Optional[Image.Image], str, str, List[str], str]:
    if not finals:
        return None, "blocked", "Missing final-score context for Last Night scoreboard", [], "last_night_scoreboard"
    teams = []
    for g in finals[:4]:
        teams.extend([g["team_a"], g["team_b"]])
    _, missing = required_logo_paths(teams, registry)
    if missing:
        return None, "blocked", "Missing required exact team logo(s): " + ", ".join(sorted(set(missing))), missing, "last_night_scoreboard"
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = gradient_bg(size, (92, 66, 160))
    d = frame(img, packet, "WNBA scoreboard", wm)
    w, h = size
    d.text((84, 226), "LAST NIGHT", font=font(68 if h < 1500 else 86, True), fill=INK)
    d.text((84, 304 if h < 1500 else 334), "IN THE W", font=font(108 if h < 1500 else 132, True), fill=INK)
    y = 476 if h < 1500 else 560
    for i, g in enumerate(finals[:4]):
        cy = y + i * (118 if h < 1500 else 145)
        d.rounded_rectangle((84, cy, w - 84, cy + 92), radius=26, fill=(255, 255, 255, 18), outline=(255, 255, 255, 42), width=1)
        d.text((116, cy + 26), f"0{i+1}", font=font(26, True), fill=PINK)
        line = f"{g['team_a'].upper()} {g['score_a']}   —   {g['team_b'].upper()} {g['score_b']}"
        d.text((184, cy + 24), line, font=font(32, True), fill=INK)
    cta = packet.get("first") or "Which result mattered most?"
    cta_y = h - (220 if h < 1500 else 270)
    d.rounded_rectangle((84, cta_y, w - 84, cta_y + 136), radius=34, fill=(255, 255, 255, 20), outline=(255, 255, 255, 48), width=2)
    draw_block(d, 118, cta_y + 32, cta, font(34, True), INK, w - 236, gap=4, max_lines=2)
    return img, "rendered", "ok", [], "last_night_scoreboard"


def render_packet(packet: Dict[str, Any], wm: Image.Image, registry: Dict[str, Path], finals: List[Dict[str, str]]) -> Tuple[str, List[Path], str, str, str, str]:
    headline = packet.get("headline", "")
    content_type = packet.get("content_type", "")
    if "last night" in headline.lower():
        img, status, reason, missing, template = render_last_night(packet, wm, registry, finals)
    elif content_type in {"preview_event", "result_or_recap"} or teams_from_headline(headline):
        img, status, reason, missing, template = render_matchup(packet, wm, registry, finals)
    else:
        img, template = render_editorial(packet, wm)
        status, reason, missing = "rendered", "ok", []
    if status != "rendered" or img is None:
        return "blocked", [], reason, template, ", ".join(missing), "no"
    folder = OUT_DIR / packet["packet_id"]
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / (slug(headline)[:84] + ".png")
    img.convert("RGB").save(out, quality=95)
    used_score = "yes" if template in {"matchup", "last_night_scoreboard"} and ("last night" in headline.lower() or score_for_pair(*(teams_from_headline(headline)[:2]), finals) != ("", "") if len(teams_from_headline(headline)) == 2 else False) else "no"
    return "rendered", [out], "ok", template, "", used_score


def contact_sheet(paths: List[Path]) -> None:
    if not paths:
        return
    thumbs = []
    for p in paths[:12]:
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((340, 340), Image.LANCZOS)
            cell = Image.new("RGB", (370, 410), (7, 10, 20))
            cell.paste(im, ((370 - im.size[0]) // 2, 14))
            ImageDraw.Draw(cell).text((18, 366), p.parent.name[:34], font=font(17, True), fill=INK)
            thumbs.append(cell)
        except Exception:
            pass
    if not thumbs:
        return
    cols = 3
    sheet = Image.new("RGB", (cols * 370 + 24, math.ceil(len(thumbs) / cols) * 410 + 24), (4, 6, 12))
    for i, t in enumerate(thumbs):
        sheet.paste(t, (12 + (i % cols) * 370, 12 + (i // cols) * 410))
    sheet.save(CONTACT, quality=94)


def zip_outputs() -> None:
    if ZIP_DIR.exists():
        shutil.rmtree(ZIP_DIR)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    for folder in OUT_DIR.glob("*"):
        if folder.is_dir():
            with zipfile.ZipFile(ZIP_DIR / f"{folder.name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
                for f in folder.rglob("*"):
                    if f.is_file():
                        z.write(f, f.relative_to(folder))


def has_internal_text(headline: str) -> str:
    bad = ["review before publish", "control rules", "do not render", "internal", "workflow"]
    h = headline.lower()
    return "yes" if any(x in h for x in bad) else "no"


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wm, wm_source = load_watermark()
    registry = approved_logo_registry()
    finals = parse_selected_finals()
    packets = [p for p in (parse_packet(z) for z in discover_packets()) if p]
    status_rows: List[Dict[str, Any]] = []
    manifest_rows: List[Dict[str, Any]] = []
    rendered_files: List[Path] = []
    if not wm:
        for p in packets:
            status_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "status": "blocked", "reason": f"official HSD watermark asset missing or unreadable: {wm_source}", "rendered_files": 0, "used_watermark": "no", "used_logos": "no", "template": "blocked", "missing_logos": "", "used_score_context": "no", "internal_text_found": has_internal_text(p["headline"]), "decision": "block"})
    else:
        for p in packets:
            st, outs, reason, template, missing, used_score = render_packet(p, wm, registry, finals)
            used_logos = "yes" if st == "rendered" and template in {"matchup", "last_night_scoreboard"} else ("n/a" if template == "editorial" and st == "rendered" else "no")
            status_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "status": st, "reason": reason, "rendered_files": len(outs), "used_watermark": "yes", "used_logos": used_logos, "template": template, "missing_logos": missing, "used_score_context": used_score, "internal_text_found": has_internal_text(p["headline"]), "decision": "pass" if st == "rendered" else "block"})
            for out in outs:
                rendered_files.append(out)
                with Image.open(out) as im:
                    W, H = im.size
                manifest_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "output_path": out.as_posix(), "width": W, "height": H, "used_watermark": "yes", "used_logos": used_logos, "template": template})
    write_csv(STATUS, status_rows, STATUS_FIELDS)
    write_csv(MANIFEST, manifest_rows, MANIFEST_FIELDS)
    contact_sheet(rendered_files)
    zip_outputs()
    rendered = sum(1 for r in status_rows if r["status"] == "rendered")
    blocked = sum(1 for r in status_rows if r["status"] == "blocked")
    lines = ["# Mermaid Render Studio v2.9 Visual Polish QA Report", "", f"- version: {VERSION}", f"- rendered packets: {rendered}", f"- blocked packets: {blocked}", f"- watermark source: {wm_source}", f"- team logo policy: exact_required", f"- score context finals found: {len(finals)}", f"- template families: last_night_scoreboard, matchup, editorial", "", "## Packet Status", ""]
    lines += [f"- {r['packet_id']} | {r['platform']} | {r['headline']} | {r['template']} | {r['status']} | {r['reason']}" for r in status_rows]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    META.write_text(json.dumps({"version": VERSION, "rendered": rendered, "blocked": blocked, "watermark_source": wm_source, "team_logo_policy": "exact_required", "score_context_finals": len(finals), "templates": ["last_night_scoreboard", "matchup", "editorial"]}, indent=2), encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": rendered, "blocked": blocked, "watermark_source": wm_source, "team_logo_policy": "exact_required"}, indent=2))


if __name__ == "__main__":
    main()
