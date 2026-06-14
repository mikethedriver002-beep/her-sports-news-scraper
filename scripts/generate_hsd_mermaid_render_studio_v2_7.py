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

from PIL import Image, ImageDraw, ImageFont

VERSION = "v2.7"
OUT_DIR = Path("rendered_handoff_graphics")
ZIP_DIR = Path("rendered_handoff_zips")
STATUS = Path("rendered_handoff_status.csv")
MANIFEST = Path("rendered_handoff_manifest.csv")
REPORT = Path("rendered_handoff_qa_report.md")
CONTACT = Path("rendered_handoff_contact_sheet.jpg")
META = Path("rendered_handoff_metadata.json")

PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
WATERMARK_CANDIDATES = [
    Path("data/assets/brand/hsd_watermark.png"),
    Path("data/assets/brand/hsd_official_watermark.png"),
    Path("assets/hsd_watermark.png"),
    Path("brand/hsd_watermark.png"),
]

STATUS_FIELDS = ["packet_id", "platform", "headline", "status", "reason", "rendered_files", "used_watermark", "used_logos"]
MANIFEST_FIELDS = ["packet_id", "platform", "headline", "output_path", "width", "height", "used_watermark", "used_logos"]

BG = (10, 14, 24)
PANEL = (18, 24, 38)
PANEL_2 = (26, 32, 52)
TEXT = (246, 248, 252)
MUTED = (177, 187, 205)
ACCENT = (92, 154, 255)
LINE = (48, 58, 86)
CANVAS = {"IG Feed": (1080, 1350), "Threads": (1080, 1350), "IG Stories": (1080, 1920)}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def rows(path: Path) -> List[Dict[str, str]]:
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
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in choices:
        if p and Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> List[str]:
    words = clean(text).split()
    if not words:
        return [""]
    out, cur = [], words[0]
    for word in words[1:]:
        test = cur + " " + word
        box = draw.textbbox((0, 0), test, font=fnt)
        if box[2] - box[0] <= max_w:
            cur = test
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    return out


def draw_block(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, max_w: int, gap: int = 8) -> int:
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y = draw.textbbox((x, y), line, font=fnt)[3] + gap
    return y


def find_watermark() -> Optional[Path]:
    for p in WATERMARK_CANDIDATES:
        if p.exists():
            return p
    for p in Path(".").rglob("*"):
        low = p.as_posix().lower()
        if p.is_file() and "watermark" in low and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            return p
    return None


def open_img(path: Optional[Path]) -> Optional[Image.Image]:
    if not path or not path.exists():
        return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def logo_registry() -> Dict[str, Path]:
    reg: Dict[str, Path] = {}
    for p in [Path("approved_graphics_assets.csv"), Path("hsd_pipeline_lite_review/files/approved_graphics_assets.csv")]:
        for r in rows(p):
            name = clean(r.get("entity_name"))
            if not name:
                continue
            for key in ["master_path", "web_path"]:
                val = clean(r.get(key))
                if val and Path(val).exists():
                    reg[name.lower()] = Path(val)
                    break
    return reg


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
        }
    except Exception:
        return None


def canvas(size: Tuple[int, int]) -> Image.Image:
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    w, h = size
    d.ellipse((-260, -240, 660, 620), fill=(24, 36, 70, 235))
    d.ellipse((w - 420, h - 460, w + 260, h + 230), fill=(55, 25, 72, 210))
    d.rounded_rectangle((48, 140, w - 48, h - 72), radius=36, fill=PANEL, outline=LINE, width=2)
    return img


def paste_watermark(img: Image.Image, wm: Image.Image) -> None:
    w = min(170, img.size[0] // 5)
    mark = wm.copy()
    mark.thumbnail((w, w), Image.LANCZOS)
    img.alpha_composite(mark, (56, 44))


def render_packet(packet: Dict[str, Any], wm: Image.Image, logos: Dict[str, Path]) -> Tuple[str, List[Path], str, str]:
    size = CANVAS.get(packet["platform"], (1080, 1350))
    img = canvas(size)
    d = ImageDraw.Draw(img)
    paste_watermark(img, wm)
    W, H = size
    small = font(27, True)
    title = font(72 if H < 1500 else 82, True)
    sub = font(34 if H < 1500 else 40, False)
    meta = font(28, False)
    cta = font(31, True)

    d.rounded_rectangle((48, 98, 230, 130), radius=16, fill=ACCENT)
    d.text((68, 102), packet["platform"].upper(), font=small, fill=TEXT)
    league = packet.get("league") or "HSD"
    box = d.textbbox((0, 0), league.upper(), font=small)
    pw = box[2] - box[0] + 48
    d.rounded_rectangle((W - pw - 52, 98, W - 52, 130), radius=16, fill=PANEL_2, outline=LINE, width=2)
    d.text((W - pw - 28, 102), league.upper(), font=small, fill=MUTED)

    y = 230 if H < 1500 else 280
    y = draw_block(d, 84, y, packet["headline"], title, TEXT, W - 168, 10) + 18
    y = draw_block(d, 84, y, packet.get("hook") or packet["headline"], sub, MUTED, W - 168, 8) + 24
    d.line((84, y, W - 84, y), fill=LINE, width=2)
    y += 30
    bits = [f"Type: {packet.get('content_type')}", f"League: {league}"]
    if packet.get("first"):
        bits.append(f"Debate: {packet['first']}")
    for bit in bits:
        y = draw_block(d, 84, y, bit, meta, TEXT, W - 168, 8) + 8

    cta_y = H - (170 if H < 1500 else 220)
    d.rounded_rectangle((84, cta_y, W - 84, cta_y + 110), radius=28, fill=PANEL_2, outline=LINE, width=2)
    draw_block(d, 112, cta_y + 22, packet.get("first") or "What is your biggest takeaway?", cta, TEXT, W - 224, 6)

    # Review stamp is intentionally outside public display copy hierarchy.
    d.text((84, H - 52), "Review before publish", font=font(20, False), fill=MUTED)

    out_dir = OUT_DIR / packet["packet_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (slug(packet["headline"])[:80] + ".png")
    img.convert("RGB").save(out, quality=95)
    return "rendered", [out], "ok", "no"


def contact_sheet(paths: List[Path]) -> None:
    if not paths:
        return
    thumbs = []
    for p in paths[:12]:
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((280, 280), Image.LANCZOS)
            cell = Image.new("RGB", (300, 320), (8, 12, 24))
            cell.paste(im, ((300 - im.size[0]) // 2, 12))
            ImageDraw.Draw(cell).text((12, 292), p.parent.name[:30], font=font(15, True), fill=TEXT)
            thumbs.append(cell)
        except Exception:
            pass
    if not thumbs:
        return
    cols = 3
    rows_needed = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 300 + 20, rows_needed * 320 + 20), (6, 8, 15))
    for i, t in enumerate(thumbs):
        sheet.paste(t, (10 + (i % cols) * 300, 10 + (i // cols) * 320))
    sheet.save(CONTACT, quality=92)


def zip_outputs() -> None:
    if ZIP_DIR.exists():
        shutil.rmtree(ZIP_DIR)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    for folder in OUT_DIR.glob("*"):
        if not folder.is_dir():
            continue
        zp = ZIP_DIR / f"{folder.name}.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in folder.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(folder))


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wm_path = find_watermark()
    wm = open_img(wm_path)
    reg = logo_registry()
    packets = [parse_packet(z) for z in discover_packets()]
    packets = [p for p in packets if p]
    status_rows: List[Dict[str, Any]] = []
    manifest_rows: List[Dict[str, Any]] = []
    files: List[Path] = []
    if not wm:
        for p in packets:
            status_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "status": "blocked", "reason": "official HSD watermark asset missing", "rendered_files": 0, "used_watermark": "no", "used_logos": "no"})
    else:
        for p in packets:
            st, outs, reason, logo_state = render_packet(p, wm, reg)
            status_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "status": st, "reason": reason, "rendered_files": len(outs), "used_watermark": "yes", "used_logos": logo_state})
            for out in outs:
                files.append(out)
                with Image.open(out) as im:
                    W, H = im.size
                manifest_rows.append({"packet_id": p["packet_id"], "platform": p["platform"], "headline": p["headline"], "output_path": out.as_posix(), "width": W, "height": H, "used_watermark": "yes", "used_logos": logo_state})
    write_csv(STATUS, status_rows, STATUS_FIELDS)
    write_csv(MANIFEST, manifest_rows, MANIFEST_FIELDS)
    contact_sheet(files)
    zip_outputs()
    rendered = sum(1 for r in status_rows if r["status"] == "rendered")
    blocked = sum(1 for r in status_rows if r["status"] == "blocked")
    lines = ["# Mermaid Render Studio v2.7 QA Report", "", f"- rendered packets: {rendered}", f"- blocked packets: {blocked}", f"- watermark: {wm_path.as_posix() if wm_path else 'missing'}", "", "## Packet Status", ""]
    lines += [f"- {r['packet_id']} | {r['platform']} | {r['headline']} | {r['status']} | {r['reason']}" for r in status_rows]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    META.write_text(json.dumps({"version": VERSION, "rendered": rendered, "blocked": blocked, "watermark": wm_path.as_posix() if wm_path else ""}, indent=2), encoding="utf-8")
    print(json.dumps({"rendered": rendered, "blocked": blocked}, indent=2))


if __name__ == "__main__":
    main()
