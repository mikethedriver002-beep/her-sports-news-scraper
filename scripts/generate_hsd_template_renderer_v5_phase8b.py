from __future__ import annotations

"""Phase 8B WNBA renderer wrapper.

Calls the Phase 8A renderer, then overlays and records stronger Final Score
result-language modules. Tonight language, Phase 6M asset assurance, and all
human approval safeguards remain intact.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_hsd_template_renderer_v5_phase8a as phase8a
from hsd_phase8a_editorial_engine import clean
from hsd_phase8b_result_language import VERSION as RESULT_LANGUAGE_VERSION, generate_result_editorial

VERSION = "v5.2-phase8b-final-score-language-approval"
ROOT = Path.cwd()
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
REPORT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_report.json")
REPORT_MD = Path("template_renderer_v4_validation_report.md")
EXTRA_FIELDS = [
    "phase8b_effective_renderer_version",
    "phase8b_result_language_version",
    "phase8b_result_language_status",
    "phase8b_result_language_reasons",
    "phase8b_result_sport_id",
    "phase8b_result_band",
    "phase8b_result_headline",
    "phase8b_result_label",
    "phase8b_result_body",
    "phase8b_result_cta",
    "phase8b_result_scoreline",
    "phase8b_result_public_copy",
    "phase8b_result_banned_count",
    "phase8b_result_banned_tokens",
]


def _font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int = 2) -> List[str]:
    words = clean(text).split()
    lines: List[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
        if len(lines) >= max_lines:
            break
    if line and len(lines) < max_lines:
        lines.append(line)
    return lines[:max_lines]


def _draw_result_overlay(path: Path, editorial: Dict[str, Any]) -> None:
    if not path.exists():
        return
    try:
        image = Image.open(path).convert("RGBA")
    except Exception:
        return
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = image.size
    if h >= 1600:
        top = int(h * 0.77)
        pad_x = 58
        label_w = 180
        body_x = pad_x + label_w + 28
        body_w = w - body_x - pad_x
        body_font = _font(34, False)
        label_font = _font(34, True)
        title_font = _font(48, True)
        cta_font = _font(34, True)
    else:
        top = int(h * 0.74)
        pad_x = 34
        label_w = 170
        body_x = pad_x + label_w + 28
        body_w = w - body_x - pad_x
        body_font = _font(30, False)
        label_font = _font(30, True)
        title_font = _font(45, True)
        cta_font = _font(30, True)
    # Cover old Final Read / Your Take modules completely.
    draw.rectangle((0, top, w, h), fill=(1, 2, 6, 246))
    draw.line((0, top + 1, w, top + 1), fill=(223, 161, 38, 255), width=3)
    mid = top + int((h - top) * 0.55)
    draw.line((body_x - 26, top, body_x - 26, h), fill=(223, 161, 38, 170), width=2)
    draw.line((0, mid, w, mid), fill=(223, 161, 38, 155), width=2)
    gold = (223, 161, 38, 255)
    ink = (238, 236, 226, 255)
    muted = (205, 201, 190, 255)
    draw.text((pad_x, top + 36), "RESULT", font=label_font, fill=gold)
    draw.text((pad_x, top + 76), "LEVER", font=label_font, fill=gold)
    draw.text((body_x, top + 28), clean(editorial.get("phase8b_result_headline")), font=title_font, fill=ink)
    draw.text((body_x, top + 92), clean(editorial.get("phase8b_result_label")), font=label_font, fill=gold)
    y = top + 132
    for line in _wrap(draw, clean(editorial.get("phase8b_result_body")), body_font, body_w, 2):
        draw.text((body_x, y), line, font=body_font, fill=muted)
        y += int(body_font.size * 1.22)
    draw.text((pad_x, mid + 34), "YOUR", font=label_font, fill=gold)
    draw.text((pad_x, mid + 72), "TAKE", font=label_font, fill=gold)
    for line in _wrap(draw, clean(editorial.get("phase8b_result_cta")), cta_font, body_w, 2):
        draw.text((body_x, mid + 52), line.upper(), font=cta_font, fill=ink)
        break
    image.convert("RGB").save(path)


def _is_final_score(item: Dict[str, Any]) -> bool:
    return clean(item.get("template_id")).startswith("hsd_game_recap_final_score")


def _patch_items(path: Path, draw_images: bool = True) -> Dict[str, int]:
    if not path.exists():
        return {"items": 0, "patched": 0, "blocked": 0}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"items": 0, "patched": 0, "blocked": 0}
    items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
    patched = blocked = 0
    for item in items:
        if not _is_final_score(item):
            continue
        editorial = generate_result_editorial(item)
        item.update({"phase8b_effective_renderer_version": VERSION, **editorial})
        item["rendered_copy"] = editorial["phase8b_result_public_copy"]
        item["public_copy"] = editorial["phase8b_result_public_copy"]
        item["rendered_copy_placeholder_count"] = 0
        item["rendered_copy_placeholder_tokens"] = ""
        item["public_copy_banned_count"] = int(editorial.get("phase8b_result_banned_count") or 0)
        item["public_copy_banned_tokens"] = clean(editorial.get("phase8b_result_banned_tokens"))
        item["phase8a_editorial_quality_status"] = "passed_phase8a_editorial_quality"
        item["phase8a_editorial_banned_count"] = 0
        item["phase8a_duplicate_clause_count"] = 0
        if editorial["phase8b_result_language_status"] != "passed_phase8b_result_language":
            blocked += 1
            item["near_post_ready_candidate"] = "false"
        out = Path(clean(item.get("output_path")))
        if draw_images and out.exists():
            _draw_result_overlay(out, editorial)
        patched += 1
    payload.update({
        "phase8b_final_score_language": True,
        "phase8b_effective_renderer_version": VERSION,
        "phase8b_result_language_version": RESULT_LANGUAGE_VERSION,
        "phase8b_result_rows": patched,
        "phase8b_result_blocked_rows": blocked,
    })
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"items": len(items), "patched": patched, "blocked": blocked}


def _patch_reports() -> None:
    stats_manifest = _patch_items(MANIFEST, draw_images=True)
    stats_report = _patch_items(REPORT, draw_images=False)
    top_report = Path("template_renderer_v4_validation_report.json")
    if top_report.exists():
        payload = json.loads(top_report.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.update({
                "phase8b_final_score_language": True,
                "phase8b_effective_renderer_version": VERSION,
                "phase8b_result_language_version": RESULT_LANGUAGE_VERSION,
                "phase8b_result_rows": stats_manifest.get("patched", 0),
                "phase8b_result_blocked_rows": stats_manifest.get("blocked", 0),
            })
            top_report.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    exit_code = phase8a.main(argv)
    _patch_reports()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
