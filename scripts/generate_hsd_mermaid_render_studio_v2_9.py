from __future__ import annotations

import base64
import csv
import io
import json
import math
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

VERSION = "v2.9"
OUT_DIR = Path("rendered_handoff_graphics")
ZIP_DIR = Path("rendered_handoff_zips")
STATUS = Path("rendered_handoff_status.csv")
MANIFEST = Path("rendered_handoff_manifest.csv")
REPORT = Path("rendered_handoff_qa_report.md")
CONTACT = Path("rendered_handoff_contact_sheet.jpg")
META = Path("rendered_handoff_metadata.json")
PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
WATERMARK_PNGS = [
    Path("assets/branding/official_hsd_watermark.png"),
    Path("data/assets/brand/hsd_watermark.png"),
    Path("data/assets/brand/hsd_official_watermark.png"),
    Path("assets/hsd_watermark.png"),
    Path("brand/hsd_watermark.png"),
]
WATERMARK_B64 = Path("data/assets/brand/hsd_watermark_base64.txt")
CANVAS = {"IG Feed": (1080, 1350), "Threads": (1080, 1350), "IG Stories": (1080, 1920)}
STATUS_FIELDS = ["packet_id", "platform", "headline", "status", "reason", "rendered_files", "used_watermark", "used_logos", "template"]
MANIFEST_FIELDS = ["packet_id", "platform", "headline", "output_path", "width", "height", "used_watermark", "used_logos", "template"]
BG = (7, 10, 20)
PANEL = (15, 20, 34)
INK = (248, 250, 255)
MUTED = (177, 187, 205)
LINE = (48, 58, 86)
BLUE = (73, 135, 255)
PINK = (242, 88, 161)
GOLD = (244, 197, 66)
GREEN = (82, 214, 145)


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
    lines, cur = [], words[0]
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
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return lines


def draw_block(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, max_w: int, gap: int = 8, max_lines: int = 10, anchor: str = "la") -> int:
    for line in wrap(draw, text, fnt, max_w, max_lines=max_lines):
        draw.text((x, y), line, font=fnt, fill=fill, anchor=anchor)
        y = draw.textbbox((x, y), line, font=fnt, anchor=anchor)[3] + gap
    return y


def load_watermark() -> Tuple[Optional[Image.Image], str]:
    for p in WATERMARK_PNGS:
        if p.exists():
            try:
                return Image.open(p).convert("RGBA"), p.as_posix()
            except Exception:
                pass
    if WATERMARK_B64.exists():
        try:
            raw = base64.b64decode(WATERMARK_B64.read_text(encoding="utf-8").strip())
            return Image.open(io.BytesIO(raw)).convert("RGBA"), WATERMARK_B64.as_posix()
        except Exception as exc:
            return None, f"base64 decode failed: {type(exc).__name__}"
    return None, "missing"


def discover_packets() -> List[Path]:
    found: Dict[str, Path] = {}
    for d in PACKET_DIRS:
        if d.exists():
            for z in d.glob("*.zip"):
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


def gradient_bg(size: Tuple[int, int], tint: Tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    pix = img.load()
    for y in range(h):
        for x in range(w):
            nx = x / max(1, w)
            ny = y / max(1, h)
            r = int(BG[0] + tint[0] * (0.12 + 0.24 * nx + 0.10 * ny))
            g = int(BG[1] + tint[1] * (0.10 + 0.17 * ny))
            b = int(BG[2] + tint[2] * (0.10 + 0.22 * (1 - nx)))
            pix[x, y] = (min(255, r), min(255, g), min(255, b), 255)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((-260, -260, int(w * .75), int(h * .52)), fill=(*tint, 70))
    d.ellipse((int(w * .55), int(h * .58), w + 280, h + 220), fill=(PINK[0], PINK[1], PINK[2], 62))
    d.polygon([(w * .70, 0), (w, 0), (w, h * .28), (w * .62, h * .18)], fill=(255, 255, 255, 18))
    img.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(2)))
    return img


def tint_for(packet: Dict[str, Any]) -> Tuple[int, int, int]:
    if packet.get("league") == "LPGA":
        return (20, 95, 70)
    if packet.get("content_type") == "preview_event":
        return (52, 90, 180)
    if "last night" in packet.get("headline", "").lower():
        return (95, 60, 140)
    return (42, 86, 170)


def paste_watermark(img: Image.Image, wm: Image.Image) -> None:
    mark = wm.copy()
    # Crop checkerboard/transparent padding if present.
    if mark.mode != "RGBA":
        mark = mark.convert("RGBA")
    alpha_box = mark.getbbox()
    if alpha_box:
        mark = mark.crop(alpha_box)
    target_w = 92
    mark.thumbnail((target_w, target_w), Image.LANCZOS)
    # Soft translucent chip behind mark, not visible checkerboard.
    chip = Image.new("RGBA", (mark.width + 22, mark.height + 22), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chip)
    cd.rounded_rectangle((0, 0, chip.width - 1, chip.height - 1), radius=18, fill=(255, 255, 255, 24), outline=(255, 255, 255, 44), width=1)
    chip.alpha_composite(mark, (11, 11))
    img.alpha_composite(chip, (54, 46))


def load_logo_image(path: Path) -> Optional[Image.Image]:
    if not path.exists():
        return None
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


def approved_logo_registry() -> Dict[str, Path]:
    registry: Dict[str, Path] = {}
    for csv_path in [Path("approved_graphics_assets.csv"), Path("hsd_pipeline_lite_review/files/approved_graphics_assets.csv")]:
        for row in read_csv(csv_path):
            name = clean(row.get("entity_name"))
            if not name:
                continue
            for field in ["master_path", "web_path"]:
                val = clean(row.get(field))
                if val and Path(val).exists():
                    registry[name.lower()] = Path(val)
                    break
    return registry


def find_logo(team: str, registry: Dict[str, Path]) -> Optional[Image.Image]:
    if team.lower() in registry:
        img = load_logo_image(registry[team.lower()])
        if img:
            return img
    team_slug = slug(team)
    for root in [Path("data/assets/approved"), Path("graphics_chat_upload_pack"), Path("ig_story_results_upload_pack"), Path("hsd_pipeline_lite_review")]:
        if not root.exists():
            continue
        matches = sorted([p for p in root.rglob("*") if p.is_file() and team_slug in p.as_posix().lower() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}], key=lambda p: (p.suffix.lower() != ".png", len(p.as_posix())))
        for m in matches:
            img = load_logo_image(m)
            if img:
                return img
    return None


def teams_from_headline(headline: str) -> List[str]:
    h = clean(headline)
    m = re.match(r"(.+?)\s+beat\s+(.+)$", h, flags=re.I)
    if m:
        return [m.group(1).strip(), m.group(2).strip()]
    m = re.match(r"(.+?)\s+(?:at|vs\.?|versus)\s+(.+)$", h, flags=re.I)
    if m:
        return [m.group(1).strip(), m.group(2).strip()]
    return []


def logo_chip(img: Optional[Image.Image], label: str, size: int = 168) -> Image.Image:
    chip = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(chip)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=36, fill=(255, 255, 255, 18), outline=(255, 255, 255, 42), width=2)
    if img:
        logo = img.copy()
        logo.thumbnail((size - 46, size - 46), Image.LANCZOS)
        chip.alpha_composite(logo, ((size - logo.width) // 2, (size - logo.height) // 2))
    else:
        initials = "".join([w[0] for w in label.split()[:3]]).upper()[:3]
        f = font(52, True)
        d.text((size // 2, size // 2), initials, font=f, fill=INK, anchor="mm")
    return chip


def frame(img: Image.Image, packet: Dict[str, Any], template: str, wm: Image.Image) -> ImageDraw.ImageDraw:
    d = ImageDraw.Draw(img)
    w, h = img.size
    paste_watermark(img, wm)
    # Kicker pills
    label = packet.get("league") or "HSD"
    f = font(25, True)
    tw, th = text_size(d, label.upper(), f)
    d.rounded_rectangle((w - tw - 94, 50, w - 54, 92), radius=20, fill=(255, 255, 255, 20), outline=(255, 255, 255, 46), width=1)
    d.text((w - tw - 72, 60), label.upper(), font=f, fill=MUTED)
    d.text((54, 126), template.upper(), font=font(22, True), fill=(255, 255, 255, 145))
    d.line((54, 156, w - 54, 156), fill=(255, 255, 255, 28), width=1)
    return d


def render_matchup(packet: Dict[str, Any], wm: Image.Image, registry: Dict[str, Path]) -> Tuple[Image.Image, str]:
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = gradient_bg(size, tint_for(packet))
    d = frame(img, packet, "matchup board" if packet.get("content_type") == "preview_event" else "final board", wm)
    w, h = size
    teams = teams_from_headline(packet["headline"])
    logo_y = 238 if h < 1500 else 360
    if len(teams) == 2:
        left, right = teams
        left_chip = logo_chip(find_logo(left, registry), left, 188)
        right_chip = logo_chip(find_logo(right, registry), right, 188)
        img.alpha_composite(left_chip, (96, logo_y))
        img.alpha_composite(right_chip, (w - 284, logo_y))
        mid = "FINAL" if packet.get("content_type") == "result_or_recap" else "AT"
        d.rounded_rectangle((w // 2 - 76, logo_y + 52, w // 2 + 76, logo_y + 136), radius=26, fill=(255, 255, 255, 18), outline=(255, 255, 255, 54), width=2)
        d.text((w // 2, logo_y + 94), mid, font=font(32, True), fill=INK, anchor="mm")
        d.text((190, logo_y + 220), left.upper(), font=font(29, True), fill=INK, anchor="ma")
        d.text((w - 190, logo_y + 220), right.upper(), font=font(29, True), fill=INK, anchor="ma")
        title_y = logo_y + 292
    else:
        title_y = 270
    title = packet["headline"]
    title_font = font(80 if h < 1500 else 90, True)
    title_y = draw_block(d, 82, title_y, title, title_font, INK, w - 164, gap=8, max_lines=4) + 24
    hook = packet.get("hook") or "The game lane to watch."
    title_y = draw_block(d, 86, title_y, hook, font(39 if h < 1500 else 46, False), MUTED, w - 172, gap=8, max_lines=3) + 28
    accent = GOLD if packet.get("content_type") == "result_or_recap" else BLUE
    d.rounded_rectangle((82, title_y, w - 82, title_y + 12), radius=6, fill=accent)
    cta = packet.get("first") or ("Who needs this one more?" if packet.get("content_type") == "preview_event" else "What changed after this result?")
    cta_y = h - (210 if h < 1500 else 260)
    d.rounded_rectangle((76, cta_y, w - 76, cta_y + 138), radius=34, fill=(255, 255, 255, 18), outline=(255, 255, 255, 48), width=2)
    draw_block(d, 108, cta_y + 32, cta, font(34, True), INK, w - 216, gap=4, max_lines=2)
    return img, "matchup"


def render_editorial(packet: Dict[str, Any], wm: Image.Image) -> Tuple[Image.Image, str]:
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = gradient_bg(size, tint_for(packet))
    d = frame(img, packet, "editorial watch", wm)
    w, h = size
    # Magazine-style sidebar + huge title.
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


def render_last_night(packet: Dict[str, Any], wm: Image.Image) -> Tuple[Image.Image, str]:
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = gradient_bg(size, (92, 66, 160))
    d = frame(img, packet, "WNBA recap", wm)
    w, h = size
    d.text((84, 230), "LAST NIGHT", font=font(70 if h < 1500 else 88, True), fill=INK)
    d.text((84, 310 if h < 1500 else 335), "IN THE W", font=font(112 if h < 1500 else 138, True), fill=INK)
    y = 470 if h < 1500 else 540
    cards = ["Result board", "Momentum check", "What changed next?"]
    for i, card in enumerate(cards):
        cy = y + i * (112 if h < 1500 else 150)
        d.rounded_rectangle((84, cy, w - 84, cy + 82), radius=26, fill=(255, 255, 255, 18), outline=(255, 255, 255, 42), width=1)
        d.text((116, cy + 23), f"0{i+1}", font=font(28, True), fill=PINK)
        d.text((180, cy + 24), card.upper(), font=font(31, True), fill=INK)
    cta = packet.get("first") or "What was the biggest swing?"
    cta_y = h - (220 if h < 1500 else 270)
    d.rounded_rectangle((84, cta_y, w - 84, cta_y + 136), radius=34, fill=(255, 255, 255, 20), outline=(255, 255, 255, 48), width=2)
    draw_block(d, 118, cta_y + 32, cta, font(34, True), INK, w - 236, gap=4, max_lines=2)
    return img, "last_night"


def render_packet(packet: Dict[str, Any], wm: Image.Image, registry: Dict[str, Path]) -> Tuple[str, List[Path], str, str]:
    if "last night" in packet.get("headline", "").lower():
        img, template = render_last_night(packet, wm)
    elif packet.get("content_type") in {"preview_event", "result_or_recap"} or teams_from_headline(packet.get("headline", "")):
        img, template = render_matchup(packet, wm, registry)
    else:
        img, template = render_editorial(packet, wm)
    folder = OUT_DIR / packet["packet_id"]
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / (slug(packet["headline"])[:84] + ".png")
    img.convert("RGB").save(out, quality=95)
    return "rendered", [out], "ok", template


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


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wm, wm_source = load_watermark()
    registry = approved_logo_registry()
    packets = [p for p in (parse_packet(z) for z in discover_packets()) if p]
    status_rows: List[Dict[str, Any]] = []
    manifest_rows: List[Dict[str, Any]] = []
    rendered_files: List[Path] = []
    if not wm:
        for p in packets:
            status_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "status": "blocked", "reason": f"official HSD watermark asset missing or unreadable: {wm_source}", "rendered_files": 0, "used_watermark": "no", "used_logos": "no", "template": "blocked"})
    else:
        for p in packets:
            st, outs, reason, template = render_packet(p, wm, registry)
            status_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "status": st, "reason": reason, "rendered_files": len(outs), "used_watermark": "yes", "used_logos": "exact_when_available", "template": template})
            for out in outs:
                rendered_files.append(out)
                with Image.open(out) as im:
                    W, H = im.size
                manifest_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "output_path": out.as_posix(), "width": W, "height": H, "used_watermark": "yes", "used_logos": "exact_when_available", "template": template})
    write_csv(STATUS, status_rows, STATUS_FIELDS)
    write_csv(MANIFEST, manifest_rows, MANIFEST_FIELDS)
    contact_sheet(rendered_files)
    zip_outputs()
    rendered = sum(1 for r in status_rows if r["status"] == "rendered")
    blocked = sum(1 for r in status_rows if r["status"] == "blocked")
    lines = ["# Mermaid Render Studio v2.9 Visual Polish QA Report", "", f"- rendered packets: {rendered}", f"- blocked packets: {blocked}", f"- watermark source: {wm_source}", f"- template families: last_night, matchup, editorial", "", "## Packet Status", ""]
    lines += [f"- {r['packet_id']} | {r['platform']} | {r['headline']} | {r['template']} | {r['status']} | {r['reason']}" for r in status_rows]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    META.write_text(json.dumps({"version": VERSION, "rendered": rendered, "blocked": blocked, "watermark_source": wm_source, "templates": ["last_night", "matchup", "editorial"]}, indent=2), encoding="utf-8")
    print(json.dumps({"version": VERSION, "rendered": rendered, "blocked": blocked, "watermark_source": wm_source}, indent=2))


if __name__ == "__main__":
    main()
