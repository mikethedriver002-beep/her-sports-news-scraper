from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import re

from PIL import Image, ImageDraw

import generate_hsd_mermaid_render_studio_v3_0 as base  # type: ignore
import generate_hsd_mermaid_render_studio_v3_0_3 as runner  # type: ignore

VERSION = "v3.0.4-hsd-premium-render-skin-v1"
INK = (247, 250, 255)
MUTED = (170, 181, 203)
BG = (5, 8, 16)
CARD = (13, 18, 31, 238)
STROKE = (255, 255, 255, 42)


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def font(size: int, bold: bool = False):
    return base.font(size, bold)


def text_w(draw: ImageDraw.ImageDraw, text: str, fnt) -> int:
    return base.text_w(draw, text, fnt)


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
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    # Add ellipsis only when text was actually truncated.
    rendered_words = " ".join(lines).split()
    if len(rendered_words) < len(words) and lines:
        lines[-1] = lines[-1].rstrip("., ") + "…"
    return lines


def draw_text_block(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, fnt, fill, max_w: int, max_lines: int, gap: int = 8) -> int:
    x, y = xy
    for line in wrap(draw, text, fnt, max_w, max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        y = draw.textbbox((x, y), line, font=fnt)[3] + gap
    return y


def canvas(size: Tuple[int, int], a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Image.Image:
    W, H = size
    img = Image.new("RGBA", size, BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=BG)
    d.ellipse((-260, -290, int(W * .82), int(H * .54)), fill=(*a, 64))
    d.ellipse((int(W * .42), int(H * .50), W + 360, H + 310), fill=(*b, 58))
    for x in range(-W, W * 2, 176):
        d.polygon([(x, 0), (x + 32, 0), (x + W + 32, H), (x + W, H)], fill=(255, 255, 255, 10))
    d.rounded_rectangle((48, 138, W - 48, H - 64), radius=42, fill=CARD, outline=STROKE, width=2)
    return img


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: Tuple[int, int, int]) -> None:
    f = font(24, True)
    label = clean(text).upper()
    tw = text_w(draw, label, f)
    draw.rounded_rectangle((x, y, x + tw + 34, y + 36), radius=16, fill=fill)
    draw.text((x + 17, y + 4), label, font=f, fill=(255, 255, 255))


def logo_disc(img: Image.Image, center: Tuple[int, int], logo: Image.Image, accent: Tuple[int, int, int], size: int = 150) -> None:
    x, y = center
    d = ImageDraw.Draw(img)
    d.ellipse((x - size // 2 - 12, y - size // 2 - 12, x + size // 2 + 12, y + size // 2 + 12), fill=(*accent, 48))
    d.ellipse((x - size // 2, y - size // 2, x + size // 2, y + size // 2), fill=(8, 12, 22, 245), outline=(255, 255, 255, 66), width=2)
    lg = logo.copy()
    lg.thumbnail((size - 36, size - 36), Image.LANCZOS)
    img.alpha_composite(lg, (x - lg.width // 2, y - lg.height // 2))


def team_card(img: Image.Image, box: Tuple[int, int, int, int], team_id: str, logo: Image.Image, teams: Dict[str, Dict[str, str]], accent: Tuple[int, int, int]) -> None:
    d = ImageDraw.Draw(img)
    x1, y1, x2, y2 = box
    d.rounded_rectangle(box, radius=30, fill=(255, 255, 255, 18), outline=(255, 255, 255, 46), width=2)
    logo_disc(img, ((x1 + x2) // 2, y1 + 120), logo, accent, 142)
    name = base.team_name(team_id, teams).upper()
    lines = wrap(d, name, font(28, True), x2 - x1 - 36, 2)
    ty = y2 - 88
    for line in lines:
        d.text(((x1 + x2) // 2, ty), line, font=font(28, True), fill=INK, anchor="ma")
        ty += 34


def render_preview(packet, wm, logos, teams, aliases):
    ids = base.teams_from_headline(packet["headline"], aliases)
    left, right = ids[0], ids[1]
    a, _ = base.team_palette(left, teams)
    b, _ = base.team_palette(right, teams)
    img = canvas(base.CANVAS.get(packet["platform"], (1080, 1350)), a, b)
    d = ImageDraw.Draw(img)
    base.paste_watermark(img, wm)
    W, H = img.size
    chip(d, 84, 180, "TONIGHT", (246, 201, 80))
    d.text((84, 258), "MATCHUP", font=font(76 if H <= 1350 else 94, True), fill=INK)
    d.text((84, 340), "PREVIEW", font=font(54 if H <= 1350 else 70, True), fill=(*a, 255))
    card_y = 455 if H <= 1350 else 610
    team_card(img, (84, card_y, 476, card_y + 330), left, logos[left], teams, a)
    team_card(img, (604, card_y, W - 84, card_y + 330), right, logos[right], teams, b)
    d.text((W // 2, card_y + 132), "AT", font=font(44, True), fill=MUTED, anchor="mm")
    story = clean(packet.get("story") or packet.get("hook") or packet.get("caption") or "Who controls the pace tonight?")
    story = re.sub(r"^WATCH THIS:\s*", "", story, flags=re.I)
    y = card_y + 385
    draw_text_block(d, (84, y), story, font(40 if H <= 1350 else 50, True), INK, W - 168, 3, 10)
    cta_y = H - (210 if H <= 1350 else 280)
    d.rounded_rectangle((84, cta_y, W - 84, cta_y + 112), radius=28, fill=(255, 255, 255, 18), outline=(255, 255, 255, 46), width=2)
    draw_text_block(d, (118, cta_y + 28), packet.get("first") or "Which side are you trusting tonight?", font(32 if H <= 1350 else 40, True), INK, W - 236, 2, 8)
    img.info["score"] = "no"
    return img


def render_feature(packet, wm):
    accent = (88, 215, 154) if packet.get("league", "").upper() == "LPGA" else (74, 144, 255)
    img = canvas(base.CANVAS.get(packet["platform"], (1080, 1350)), accent, (246, 201, 80))
    d = ImageDraw.Draw(img)
    base.paste_watermark(img, wm)
    W, H = img.size
    chip(d, 84, 180, packet.get("league") or "HSD", accent)
    y = 275 if H <= 1350 else 350
    y = draw_text_block(d, (84, y), packet["headline"], font(60 if H <= 1350 else 76, True), INK, W - 168, 5, 8) + 26
    d.line((84, y, W - 84, y), fill=(*accent, 220), width=4)
    y += 34
    draw_text_block(d, (84, y), packet.get("hook") or packet.get("caption") or "This belongs on the board.", font(34 if H <= 1350 else 44, False), MUTED, W - 168, 5, 10)
    cta_y = H - (210 if H <= 1350 else 280)
    d.rounded_rectangle((84, cta_y, W - 84, cta_y + 112), radius=28, fill=(255, 255, 255, 18), outline=(255, 255, 255, 46), width=2)
    draw_text_block(d, (118, cta_y + 28), packet.get("first") or "Are we paying enough attention?", font(32 if H <= 1350 else 40, True), INK, W - 236, 2, 8)
    img.info["score"] = "no"
    return img


def main() -> None:
    base.render_preview = render_preview
    base.render_feature = render_feature
    runner.main()


if __name__ == "__main__":
    main()
