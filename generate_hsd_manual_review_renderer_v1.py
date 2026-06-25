from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from hsd_run_io import output_path, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - validated by runtime status report
    Image = None
    ImageDraw = None
    ImageFont = None


VERSION = "hsd-manual-review-renderer-v1.2.0-mobile-score-review-drafts"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
OUT_DIR = output_path(HANDOFF_DIR_NAME)
OUT_PREVIEW = OUT_DIR / "draft_preview.png"
OUT_REVIEW_DRAFTS = OUT_DIR / "review_drafts"
OUT_REPORT = output_path("manual_review_renderer_report.md")
OUT_MANIFEST = output_path("manual_review_renderer_manifest.json")

FORMAT_SPECS = [
    {"format_id": "ig_feed_4x5", "filename": "draft_preview_ig_feed.png", "width": 1080, "height": 1350, "primary": True},
    {"format_id": "ig_story_9x16", "filename": "draft_preview_story.png", "width": 1080, "height": 1920, "primary": False},
    {"format_id": "square_feed_1x1", "filename": "draft_preview_square.png", "width": 1080, "height": 1080, "primary": False},
]

PALETTE = {
    "ink": (248, 250, 255),
    "deep": (13, 20, 35),
    "navy": (22, 48, 79),
    "blue": (35, 92, 148),
    "cyan": (54, 183, 196),
    "gold": (232, 186, 72),
    "paper": (248, 246, 241),
    "paper_2": (255, 255, 255),
    "line": (218, 222, 230),
    "muted": (93, 102, 118),
    "red": (190, 39, 54),
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def repo_root() -> Path:
    return Path.cwd().resolve()


def input_handoff_candidates() -> List[Path]:
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / HANDOFF_DIR_NAME)
    return candidates


def find_handoff_dir() -> Path | None:
    for candidate in input_handoff_candidates():
        if (candidate / "handoff_manifest.json").exists():
            return candidate
    return None


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def copy_handoff_to_output(src: Path) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dest = OUT_DIR / item.name
        if item.resolve() == dest.resolve():
            continue
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def text_size(draw: Any, text: str, fnt: Any) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), clean(text), font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_right_text(draw: Any, right: int, y: int, text: str, fnt: Any, fill: tuple[int, int, int]) -> None:
    width, _ = text_size(draw, text, fnt)
    draw.text((right - width, y), text, font=fnt, fill=fill)


def draw_rounded(draw: Any, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    else:  # pragma: no cover - Pillow fallback
        draw.rectangle(box, fill=fill, outline=outline, width=width)


def draw_chip(draw: Any, x: int, y: int, label: str, fill: tuple[int, int, int], text_fill: tuple[int, int, int], size: int = 22) -> int:
    fnt = font(size, True)
    text_w, text_h = text_size(draw, label, fnt)
    pad_x = 18
    pad_y = 9
    draw_rounded(draw, (x, y, x + text_w + pad_x * 2, y + text_h + pad_y * 2), 8, fill)
    draw.text((x + pad_x, y + pad_y - 1), label, font=fnt, fill=text_fill)
    return x + text_w + pad_x * 2 + 10


def wrap_text(draw: Any, text: str, fnt: Any, max_width: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    lines: List[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=fnt)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
            continue
        lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if words and len(lines) == max_lines:
        consumed = " ".join(lines).split()
        if len(consumed) < len(words):
            lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def draw_text_block(draw: Any, xy: tuple[int, int], text: str, fnt: Any, fill: tuple[int, int, int], max_width: int, max_lines: int, line_gap: int) -> int:
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width, max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        bbox = draw.textbbox((x, y), line, font=fnt)
        y = bbox[3] + line_gap
    return y


def choose_template(packet: Dict[str, Any]) -> Dict[str, str]:
    text = " ".join(
        clean(packet.get(key))
        for key in ["template_fit", "title", "copy_headline", "copy_dek", "renderer_family", "template_shape"]
    ).lower()
    if any(token in text for token in ["beat", "defeat", "final", "score", "result"]):
        return {
            "template_id": "hsd_final_score_review_v1",
            "template_family": "final_score_editorial_card",
            "angle_label": "FINAL",
            "tone": "result",
        }
    if any(token in text for token in ["tonight", "preview", "matchup"]):
        return {
            "template_id": "hsd_matchup_preview_review_v1",
            "template_family": "matchup_preview_card",
            "angle_label": "TONIGHT",
            "tone": "preview",
        }
    return {
        "template_id": "hsd_news_fact_review_v1",
        "template_family": "news_fact_editorial_card",
        "angle_label": "NEWS",
        "tone": "news",
    }


def asset_slots(packet: Dict[str, Any], template: Dict[str, str]) -> List[Dict[str, str]]:
    requirement = clean(packet.get("asset_requirement")) or "No player asset required; use HSD brand treatment and verified source text only."
    asset_cue = clean(packet.get("asset_cue")) or "asset_review_not_required"
    return [
        {
            "slot_id": "primary_photo",
            "status": "not_required_for_review_draft" if "no player asset" in requirement.lower() else "operator_asset_review_required",
            "requirement": requirement,
        },
        {
            "slot_id": "brand_treatment",
            "status": "rendered_locally",
            "requirement": "HSD editorial treatment, draft watermark, and source-safe text only.",
        },
        {
            "slot_id": "source_evidence",
            "status": "manual_review_required",
            "requirement": clean(packet.get("source_artifact")) or "Open source proof before approval.",
        },
        {
            "slot_id": "asset_cue",
            "status": asset_cue,
            "requirement": "Asset readiness cue copied into the renderer manifest for operator review.",
        },
    ]


def score_parts(packet: Dict[str, Any]) -> tuple[str, str]:
    headline = clean(packet.get("copy_headline")) or clean(packet.get("title"))
    dek = clean(packet.get("copy_dek"))
    text = f"{headline} {dek}"
    if "," in text and any(char.isdigit() for char in text):
        return headline, dek
    return headline, dek or "Verified update ready for operator review."


def parse_final_score(packet: Dict[str, Any]) -> Dict[str, str]:
    headline = clean(packet.get("copy_headline")) or clean(packet.get("title"))
    dek = clean(packet.get("copy_dek"))
    combined = f"{headline}. {dek}"
    score_match = re.search(r"([A-Z][A-Za-z .'-]+?)\s+(\d{2,3})\s*,\s*([A-Z][A-Za-z .'-]+?)\s+(\d{2,3})", combined)
    if not score_match:
        return {}
    team_a = clean(score_match.group(1))
    score_a = clean(score_match.group(2))
    team_b = clean(score_match.group(3))
    score_b = clean(score_match.group(4))
    try:
        winner = team_a if int(score_a) >= int(score_b) else team_b
        loser = team_b if winner == team_a else team_a
        winner_score = score_a if winner == team_a else score_b
        loser_score = score_b if winner == team_a else score_a
    except Exception:
        winner, loser, winner_score, loser_score = team_a, team_b, score_a, score_b
    verb = "beat"
    headline_match = re.search(r"(.+?)\s+(beat|defeated|tops|over)\s+(.+)", headline, re.IGNORECASE)
    if headline_match:
        winner = clean(headline_match.group(1))
        loser = clean(headline_match.group(3))
        verb = clean(headline_match.group(2)).lower()
    return {
        "winner": winner,
        "loser": loser,
        "winner_score": winner_score,
        "loser_score": loser_score,
        "verb": verb,
    }


def draw_review_chrome(draw: Any, width: int, height: int, template: Dict[str, str], format_label: str) -> None:
    red = PALETTE["red"]
    gold = PALETTE["gold"]
    blue = PALETTE["blue"]
    ink = PALETTE["ink"]
    draw.rectangle((0, 0, width, 24), fill=blue)
    draw.rectangle((0, 24, width, 34), fill=gold)
    draw_rounded(draw, (54, 70, width - 54, 146), 0, (255, 255, 255), PALETTE["line"], 2)
    draw.text((82, 88), "HER SPORTS DAILY", font=font(30, True), fill=(24, 28, 36))
    draw_right_text(draw, width - 82, 88, "DRAFT REVIEW ONLY", font(28, True), red)
    draw_chip(draw, 82, 162, template["angle_label"], gold, (19, 31, 49), 22)
    draw_chip(draw, 82 + 132, 162, format_label.upper(), (232, 239, 249), PALETTE["blue"], 20)
    draw.rectangle((54, height - 64, width - 54, height - 36), fill=red)
    draw.text((70, height - 62), "NOT APPROVED - NOT PUBLISH READY - AUTO-RENDER OFF - AUTO-PUBLISH OFF", font=font(20, True), fill=ink)


def draw_brand_pattern(draw: Any, width: int, height: int, tone: str) -> None:
    deep = PALETTE["deep"]
    navy = PALETTE["navy"]
    cyan = PALETTE["cyan"]
    gold = PALETTE["gold"]
    draw.rectangle((0, 0, width, height), fill=deep)
    draw.polygon([(width * 0.58, 0), (width, 0), (width, height * 0.42), (width * 0.42, height * 0.18)], fill=navy)
    draw.polygon([(0, height * 0.36), (width * 0.32, height * 0.16), (width * 0.58, height), (0, height)], fill=(18, 39, 65))
    accent = cyan if tone != "result" else gold
    for offset in range(-160, width, 210):
        draw.line((offset, height - 150, offset + 380, 120), fill=accent, width=3)
    for x in range(72, width, 168):
        draw.ellipse((x, height - 310, x + 9, height - 301), fill=(255, 255, 255))


def draw_center_text(draw: Any, center_x: int, y: int, text: str, fnt: Any, fill: tuple[int, int, int]) -> None:
    width, _ = text_size(draw, text, fnt)
    draw.text((center_x - width // 2, y), text, font=fnt, fill=fill)


def fit_text_font(draw: Any, text: str, max_width: int, start_size: int, min_size: int = 28, bold: bool = True) -> Any:
    size = start_size
    while size > min_size:
        fnt = font(size, bold)
        if text_size(draw, text, fnt)[0] <= max_width:
            return fnt
        size -= 3
    return font(min_size, bold)


def draw_score_panel(draw: Any, x: int, y: int, w: int, h: int, team: str, score: str, *, winner: bool) -> None:
    fill = PALETTE["deep"] if winner else (255, 255, 255)
    outline = PALETTE["gold"] if winner else PALETTE["line"]
    text_fill = PALETTE["ink"] if winner else (23, 27, 36)
    muted_fill = PALETTE["gold"] if winner else PALETTE["muted"]
    draw_rounded(draw, (x, y, x + w, y + h), 18, fill, outline, 3)
    draw.text((x + 30, y + 28), "WINNER" if winner else "FINAL", font=font(23, True), fill=muted_fill)
    team_font = fit_text_font(draw, team.upper(), w - 240, 42, 28, True)
    draw.text((x + 30, y + 76), team.upper(), font=team_font, fill=text_fill)
    score_font = font(96 if h >= 180 else 78, True)
    draw_right_text(draw, x + w - 30, y + 48, score, score_font, text_fill)


def draw_final_score_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any], score: Dict[str, str]) -> None:
    width, height = spec["width"], spec["height"]
    draw = ImageDraw.Draw(image)
    draw_brand_pattern(draw, width, height, "result")
    draw_review_chrome(draw, width, height, template, clean(spec["format_id"]).replace("_", " "))

    source = clean(packet.get("source_artifact")) or "source proof required"
    confidence = clean(packet.get("source_cue")) or "source review required"
    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Verified source review required."
    is_story = height > 1500
    is_square = height <= 1100

    content_top = 228
    content_bottom = height - 104
    left = 54
    right = width - 54
    card_h = content_bottom - content_top
    draw_rounded(draw, (left, content_top, right, content_bottom), 22, PALETTE["paper"], (255, 255, 255), 2)
    draw.rectangle((left, content_top, left + 22, content_bottom), fill=PALETTE["gold"])

    text_left = 92
    text_right = right - 48
    y = content_top + (58 if not is_square else 44)
    draw.text((text_left, y), "FINAL SCORE", font=font(32, True), fill=PALETTE["blue"])
    draw_right_text(draw, text_right, y, "VERIFIED", font(24, True), PALETTE["muted"])
    y += 60

    hero_font = font(64 if not is_square else 56, True)
    y = draw_text_block(draw, (text_left, y), f"{score['winner']} {score['verb']} {score['loser']}", hero_font, (22, 26, 36), text_right - text_left, 3, 10)
    y += 34

    panel_h = 178 if not is_square else 145
    gap = 18
    draw_score_panel(draw, text_left, y, text_right - text_left, panel_h, score["winner"], score["winner_score"], winner=True)
    y += panel_h + gap
    draw_score_panel(draw, text_left, y, text_right - text_left, panel_h, score["loser"], score["loser_score"], winner=False)
    y += panel_h + (42 if is_story else 30)

    if not is_square:
        note_h = min(260, content_bottom - y - 34)
        if note_h >= 110:
            draw_rounded(draw, (text_left, y, text_right, y + note_h), 0, (255, 255, 255), PALETTE["line"], 2)
            draw.text((text_left + 24, y + 24), "Review evidence", font=font(25, True), fill=(24, 28, 36))
            note_y = y + 70
            evidence = [
                f"Source: {source}",
                f"Confidence: {confidence}",
                f"Context: {context}",
            ]
            for item in evidence:
                note_y = draw_text_block(draw, (text_left + 24, note_y), item, font(22, False), PALETTE["muted"], text_right - text_left - 48, 1, 7)
                note_y += 2
            if is_story:
                callout_top = y + note_h + 56
                callout_bottom = min(content_bottom - 54, callout_top + 300)
                if callout_bottom - callout_top >= 220:
                    draw_rounded(draw, (text_left, callout_top, text_right, callout_bottom), 18, PALETTE["deep"], PALETTE["gold"], 3)
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 34, "FINAL", font(34, True), PALETTE["gold"])
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 86, f"{score['winner_score']} - {score['loser_score']}", font(124, True), PALETTE["ink"])
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 226, "REVIEW ONLY DRAFT", font(25, True), PALETTE["gold"])
    else:
        chip_y = min(y, content_bottom - 74)
        draw_chip(draw, text_left, chip_y, f"SOURCE: {source}".upper(), (232, 239, 249), PALETTE["blue"], 19)
        draw_chip(draw, text_left + 320, chip_y, "REVIEW ONLY", PALETTE["gold"], (19, 31, 49), 19)


def draw_primary_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any]) -> None:
    width, height = spec["width"], spec["height"]
    draw = ImageDraw.Draw(image)
    tone = template["tone"]
    parsed_score = parse_final_score(packet) if tone == "result" else {}
    if parsed_score:
        draw_final_score_template(image, packet, template, spec, parsed_score)
        return

    draw_brand_pattern(draw, width, height, tone)
    draw_review_chrome(draw, width, height, template, clean(spec["format_id"]).replace("_", " "))

    headline, dek = score_parts(packet)
    source = clean(packet.get("source_artifact")) or "source proof required"
    confidence = clean(packet.get("source_cue")) or "source review required"
    asset = clean(packet.get("asset_requirement")) or "No player asset required"
    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Manual source review required before any post."

    card_top = 214
    card_bottom = height - 96
    left = 54
    right = width - 54
    draw_rounded(draw, (left, card_top, right, card_bottom), 18, PALETTE["paper"], (255, 255, 255), 2)
    draw.rectangle((left, card_top, left + 20, card_bottom), fill=PALETTE["gold"] if tone == "result" else PALETTE["cyan"])

    text_left = 88
    text_right = right - 48
    y = card_top + 58
    draw.text((text_left, y), "REVIEW PREVIEW", font=font(28, True), fill=PALETTE["blue"])
    y += 58
    headline_font = font(76 if height >= 1350 else 62, True)
    y = draw_text_block(draw, (text_left, y), headline, headline_font, (23, 27, 36), text_right - text_left, 4, 12)
    y += 22
    draw.line((text_left, y, text_right, y), fill=(203, 206, 211), width=3)
    y += 34
    y = draw_text_block(draw, (text_left, y), dek, font(36 if height >= 1350 else 31, False), (28, 34, 46), text_right - text_left, 5, 10)

    if height >= 1260:
        module_top = max(y + 46, int(height * 0.69))
    else:
        module_top = max(y + 30, int(height * 0.62))
    module_bottom = card_bottom - 42
    draw_rounded(draw, (text_left, module_top, text_right, module_bottom), 0, (255, 255, 255), PALETTE["line"], 2)
    draw.text((text_left + 26, module_top + 26), "Manual render context", font=font(27, True), fill=(24, 28, 36))
    y = module_top + 80
    context_lines = [
        f"Template: {template['template_id']}",
        f"Source: {source}",
        f"Confidence: {confidence}",
        f"Assets: {asset}",
        f"Context: {context}",
    ]
    for item in context_lines:
        max_lines = 2 if item.startswith("Assets:") else 1
        text_font = font(21 if height >= 1350 else 19, False)
        y = draw_text_block(draw, (text_left + 26, y), item, text_font, PALETTE["muted"], text_right - text_left - 52, max_lines, 6)
        y += 3


def render_format(packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for manual review rendering.")
    image = Image.new("RGB", (spec["width"], spec["height"]), PALETTE["deep"])
    draw_primary_template(image, packet, template, spec)
    OUT_REVIEW_DRAFTS.mkdir(parents=True, exist_ok=True)
    output = OUT_REVIEW_DRAFTS / spec["filename"]
    image.save(output)
    if spec.get("primary"):
        image.save(OUT_PREVIEW)
    return output


def render_preview(packet: Dict[str, Any]) -> Dict[str, Any]:
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    template = choose_template(packet)
    outputs = []
    for spec in FORMAT_SPECS:
        output = render_format(packet, template, spec)
        outputs.append(
            {
                "format_id": spec["format_id"],
                "path": output.as_posix(),
                "width": spec["width"],
                "height": spec["height"],
                "primary": bool(spec.get("primary")),
                "review_only": True,
                "publish_ready": False,
            }
        )
    return {
        "template": template,
        "format_options": outputs,
        "asset_slots": asset_slots(packet, template),
    }


def report_lines(status: str, manifest: Dict[str, Any], preview_path: str, reason: str = "", render_result: Dict[str, Any] | None = None) -> List[str]:
    packet = manifest.get("packet") if isinstance(manifest.get("packet"), dict) else {}
    render_result = render_result or {}
    template = render_result.get("template") if isinstance(render_result.get("template"), dict) else {}
    formats = render_result.get("format_options") if isinstance(render_result.get("format_options"), list) else []
    slots = render_result.get("asset_slots") if isinstance(render_result.get("asset_slots"), list) else []
    lines = [
        "# HSD Manual Review Renderer",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{status}`",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Guardrails",
        "",
        "- Manual-only mode.",
        "- Draft preview is for human review only.",
        "- Does not publish.",
        "- Does not approve the image.",
        "- Does not call paid APIs.",
        "- Does not move files into a publish-ready lane.",
        "",
        "## Output",
        "",
        f"- Preview: `{preview_path or 'not_created'}`",
        f"- Story: `{clean(packet.get('title')) or 'none'}`",
        f"- Template: `{clean(template.get('template_id')) or 'not_selected'}`",
        f"- Template family: `{clean(template.get('template_family')) or 'not_selected'}`",
        f"- Reason: {reason or 'n/a'}",
        "",
        "## Review Draft Formats",
        "",
    ]
    if formats:
        lines.extend(
            f"- `{item.get('format_id')}` | `{item.get('width')}x{item.get('height')}` | `{item.get('path')}` | publish_ready=`false`"
            for item in formats
        )
    else:
        lines.append("- none")
    lines += ["", "## Asset Slots", ""]
    if slots:
        lines.extend(
            f"- `{item.get('slot_id')}` | `{item.get('status')}` | {clean(item.get('requirement'))}"
            for item in slots
        )
    else:
        lines.append("- none")
    return [
        *lines,
    ]


def main() -> None:
    handoff = find_handoff_dir()
    if not handoff:
        manifest = {
            "version": VERSION,
            "status": "blocked_missing_handoff",
            "preview_path": "",
            "guardrails": {"manual_only": True, "auto_render": False, "auto_publish": False, "approved": False, "paid_apis": False},
        }
        write_json(OUT_MANIFEST, manifest)
        write_text(OUT_REPORT, "\n".join(report_lines("blocked_missing_handoff", {}, "", "render_handoff_top_packet/handoff_manifest.json was not found.")))
        print(json.dumps(manifest, indent=2))
        return

    copy_handoff_to_output(handoff)
    source_manifest = read_json(handoff / "handoff_manifest.json")
    packet = source_manifest.get("packet") if isinstance(source_manifest.get("packet"), dict) else {}
    status = "draft_preview_created"
    reason = ""
    preview = ""
    render_result: Dict[str, Any] = {"template": {}, "format_options": [], "asset_slots": []}
    try:
        render_result = render_preview(packet)
        preview = OUT_PREVIEW.as_posix()
    except Exception as exc:
        status = "blocked_preview_not_created"
        reason = str(exc)

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_handoff_dir": handoff.as_posix(),
        "output_handoff_dir": OUT_DIR.as_posix(),
        "preview_path": preview,
        "packet_id": clean(packet.get("packet_id")),
        "title": clean(packet.get("title")),
        "renderer_mode": "template_driven_review_drafts",
        "selected_template": render_result.get("template", {}),
        "format_options": render_result.get("format_options", []),
        "asset_slots": render_result.get("asset_slots", []),
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_render": False,
            "auto_publish": False,
            "approved": False,
            "paid_apis": False,
            "move_files": False,
            "publish_ready": False,
        },
        "approval_status": "not_approved_human_review_required",
        "reason": reason,
    }
    write_json(OUT_MANIFEST, manifest)
    write_text(OUT_REPORT, "\n".join(report_lines(status, source_manifest, preview, reason, render_result)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
