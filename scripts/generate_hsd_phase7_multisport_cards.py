from __future__ import annotations

"""Render Phase 7 multi-sport editorial review cards.

These cards are review artifacts, not auto-publish outputs. Team and athlete identity
falls back to clearly labelled HSD-owned badges/nameplates when exact assets are absent.
"""

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hsd_phase7_editorial_engine import clean, generate_editorial, normalize_event, slug

try:
    from hsd_asset_assurance_core import generate_individual_nameplate, generate_team_badge, image_decodable
except Exception:  # pragma: no cover - fallback is exercised only outside the HSD repo
    generate_individual_nameplate = None
    generate_team_badge = None

    def image_decodable(path: Path) -> bool:
        try:
            with Image.open(path) as image:
                image.verify()
            return True
        except Exception:
            return False

VERSION = "v1.0-phase7-multisport-review-card-renderer"
EVENTS_JSON = Path("outputs/latest/HSD_PHASE7/phase7_editorial_events.json")
OUT_ROOT = Path("outputs/latest/HSD_PHASE7_MULTISPORT")
CARDS_ROOT = OUT_ROOT / "review_cards"
MANIFEST_JSON = OUT_ROOT / "phase7_multisport_manifest.json"
MANIFEST_CSV = OUT_ROOT / "phase7_multisport_manifest.csv"
CONTACT_SHEET = OUT_ROOT / "phase7_multisport_contact_sheet.jpg"
REPORT_JSON = Path("phase7_multisport_renderer_report.json")
REPORT_MD = Path("phase7_multisport_renderer_report.md")

WIDTH = 1080
HEIGHT = 1350
INK = (9, 11, 17)
INK_2 = (17, 20, 29)
GOLD = (223, 161, 38)
GOLD_LIGHT = (245, 209, 126)
PAPER = (244, 241, 232)
MUTED = (164, 170, 181)
WHITE = (255, 255, 255)

FIELDS = [
    "item_id",
    "event_id",
    "sport_id",
    "kind",
    "platform",
    "primary_name",
    "secondary_name",
    "editorial_headline",
    "debate_question",
    "watch_title",
    "watch_body",
    "cta",
    "phase7_editorial_quality_status",
    "phase7_editorial_quality_score",
    "phase7_editorial_quality_reasons",
    "phase7_editorial_banned_count",
    "primary_asset_mode",
    "secondary_asset_mode",
    "output_path",
    "fixture_only",
    "review_only",
    "human_visual_approval_required",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def _font_candidates(bold: bool = False) -> List[Path]:
    if bold:
        return [
            Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-CondensedBlack.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]
    return [
        Path("/usr/share/fonts/truetype/noto/NotoSansDisplay-Medium.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    for path in _font_candidates(bold=bold):
        if path.exists():
            return ImageFont.truetype(path.as_posix(), size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, chosen_font: ImageFont.ImageFont, max_width: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    if not words:
        return []
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        box = draw.textbbox((0, 0), candidate, font=chosen_font)
        if current and box[2] - box[0] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    if len(lines) == max_lines and len(" ".join(lines).split()) < len(words):
        lines[-1] = lines[-1].rstrip(".,;:!?") + "…"
    return lines


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_lines: int, start: int, floor: int, bold: bool = False) -> Tuple[ImageFont.ImageFont, List[str]]:
    for size in range(start, floor - 1, -2):
        candidate = font(size, bold=bold)
        lines = wrap_text(draw, text, candidate, max_width, max_lines)
        if not lines:
            return candidate, []
        if len(lines) <= max_lines and all(draw.textbbox((0, 0), line, font=candidate)[2] <= max_width for line in lines):
            return candidate, lines
    candidate = font(floor, bold=bold)
    return candidate, wrap_text(draw, text, candidate, max_width, max_lines)


def draw_lines(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], lines: List[str], chosen_font: ImageFont.ImageFont, fill: Tuple[int, int, int], line_gap: int = 8, anchor: str = "la") -> int:
    x, y = xy
    cursor = y
    for line in lines:
        draw.text((x, cursor), line, font=chosen_font, fill=fill, anchor=anchor)
        box = draw.textbbox((x, cursor), line, font=chosen_font, anchor=anchor)
        cursor += (box[3] - box[1]) + line_gap
    return cursor


def team_sport(sport_id: str) -> bool:
    return sport_id in {"wnba", "nwsl", "uswnt", "ncaa_softball", "volleyball"}


def make_fallback_asset(event: Mapping[str, Any], which: str, output_dir: Path) -> Tuple[Path, str]:
    sport_id = clean(event.get("sport_id"))
    name = clean(event.get(f"{which}_name")) or ("THE FIELD" if sport_id == "lpga" else "OPPONENT")
    raw_path = clean(event.get(f"{which}_asset_path"))
    if raw_path:
        exact = Path(raw_path)
        if image_decodable(exact):
            return exact, "verified_exact_asset"

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{slug(which)}_{slug(name)}.png"
    if team_sport(sport_id):
        if callable(generate_team_badge):
            generate_team_badge(output, name, sport_label=sport_id.upper())
        else:
            _simple_badge(output, name, f"HSD {sport_id.upper()} TEAM BADGE")
        return output, "hsd_team_badge_review"
    if callable(generate_individual_nameplate):
        generate_individual_nameplate(output, name, sport_label=sport_id.upper())
    else:
        _simple_badge(output, name, f"HSD {sport_id.upper()} IDENTITY CARD • NO PHOTO")
    return output, "hsd_no_photo_nameplate_review"


def _simple_badge(output: Path, name: str, footer: str) -> None:
    image = Image.new("RGBA", (512, 512), (*INK, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, 484, 484), radius=58, outline=GOLD, width=9, fill=(*INK_2, 255))
    initials = "".join(part[0] for part in re.findall(r"[A-Za-z0-9]+", name)[:3]).upper() or "HSD"
    f_initials, initial_lines = fit_font(draw, initials, 360, 1, 130, 60, bold=True)
    draw_lines(draw, (256, 170), initial_lines, f_initials, PAPER, anchor="ma")
    f_name, name_lines = fit_font(draw, name.upper(), 390, 2, 38, 22, bold=True)
    draw_lines(draw, (256, 315), name_lines, f_name, PAPER, anchor="ma")
    f_footer, footer_lines = fit_font(draw, footer, 410, 2, 20, 14, bold=False)
    draw_lines(draw, (256, 426), footer_lines, f_footer, GOLD, anchor="ma")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)


def paste_asset(canvas: Image.Image, path: Path, box: Tuple[int, int, int, int]) -> None:
    x, y, width, height = box
    with Image.open(path) as source:
        image = source.convert("RGBA")
    fitted = ImageOps.contain(image, (width, height), method=Image.Resampling.LANCZOS)
    panel = Image.new("RGBA", (width, height), (*INK_2, 255))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle((1, 1, width - 2, height - 2), radius=24, outline=(*GOLD, 235), width=3, fill=(*INK_2, 255))
    panel.alpha_composite(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2))
    canvas.alpha_composite(panel, (x, y))


def render_card(event: Mapping[str, Any], editorial: Mapping[str, Any], output: Path) -> Dict[str, Any]:
    normalized = normalize_event(event)
    sport_id = clean(normalized.get("sport_id"))
    kind = clean(editorial.get("phase7_editorial_kind") or normalized.get("kind")).upper()
    image = Image.new("RGBA", (WIDTH, HEIGHT), (*INK, 255))
    draw = ImageDraw.Draw(image, "RGBA")

    # Background grid and editorial stripe.
    for x in range(0, WIDTH, 90):
        draw.line((x, 0, x, HEIGHT), fill=(255, 255, 255, 7), width=1)
    for y in range(0, HEIGHT, 90):
        draw.line((0, y, WIDTH, y), fill=(255, 255, 255, 7), width=1)
    draw.rectangle((0, 0, WIDTH, 146), fill=(*INK_2, 255))
    draw.rectangle((0, 146, WIDTH, 156), fill=(*GOLD, 255))
    draw.rectangle((0, 1180, WIDTH, HEIGHT), fill=(*INK_2, 255))

    draw.text((56, 40), "HER SPORTS DAILY", font=font(38, bold=True), fill=PAPER)
    sport_label = sport_id.replace("_", " ").upper()
    draw.text((1024, 48), sport_label, font=font(26, bold=True), fill=GOLD, anchor="ra")
    draw.text((56, 108), f"PHASE 7 • {kind} • REVIEW ONLY", font=font(17), fill=MUTED)

    primary_asset, primary_mode = make_fallback_asset(normalized, "primary", OUT_ROOT / "identity_assets" / sport_id)
    secondary_asset, secondary_mode = make_fallback_asset(normalized, "secondary", OUT_ROOT / "identity_assets" / sport_id)
    paste_asset(image, primary_asset, (70, 198, 300, 300))
    paste_asset(image, secondary_asset, (710, 198, 300, 300))

    draw.text((540, 338), "VS" if kind != "RESULT" else "FINAL", font=font(34, bold=True), fill=GOLD_LIGHT, anchor="mm")
    primary_name = clean(normalized.get("primary_name"))
    secondary_name = clean(normalized.get("secondary_name"))
    primary_label = clean(normalized.get("primary_short")) or primary_name
    secondary_label = clean(normalized.get("secondary_short")) or secondary_name
    f_name, lines = fit_font(draw, primary_label.upper(), 300, 2, 30, 18, bold=True)
    draw_lines(draw, (220, 520), lines, f_name, PAPER, line_gap=4, anchor="ma")
    f_name2, lines2 = fit_font(draw, secondary_label.upper(), 300, 2, 30, 18, bold=True)
    draw_lines(draw, (860, 520), lines2, f_name2, PAPER, line_gap=4, anchor="ma")

    scoreline = clean(normalized.get("scoreline"))
    if kind == "RESULT" and scoreline:
        f_score, score_lines = fit_font(draw, scoreline.upper(), 800, 2, 46, 26, bold=True)
        draw_lines(draw, (540, 520), score_lines, f_score, GOLD_LIGHT, line_gap=5, anchor="ma")

    headline = clean(editorial.get("editorial_headline")).upper()
    f_head, head_lines = fit_font(draw, headline, 920, 2, 68, 36, bold=True)
    head_bottom = draw_lines(draw, (540, 615), head_lines, f_head, PAPER, line_gap=8, anchor="ma")

    question = clean(editorial.get("debate_question")).upper()
    f_question, question_lines = fit_font(draw, question, 900, 2, 42, 25, bold=True)
    question_bottom = draw_lines(draw, (540, head_bottom + 25), question_lines, f_question, GOLD, line_gap=7, anchor="ma")

    panel_top = max(790, question_bottom + 24)
    panel_bottom = 1145
    draw.rounded_rectangle((55, panel_top, 1025, panel_bottom), radius=28, fill=(28, 32, 44, 235), outline=(*GOLD, 220), width=3)
    watch_title = clean(editorial.get("watch_title"))
    f_watch, watch_lines = fit_font(draw, watch_title, 850, 2, 44, 27, bold=True)
    watch_bottom = draw_lines(draw, (100, panel_top + 36), watch_lines, f_watch, GOLD_LIGHT, line_gap=5)
    watch_body = clean(editorial.get("watch_body"))
    f_body, body_lines = fit_font(draw, watch_body, 850, 3, 35, 22, bold=False)
    body_bottom = draw_lines(draw, (100, watch_bottom + 20), body_lines, f_body, PAPER, line_gap=8)
    cta = clean(editorial.get("cta"))
    f_cta, cta_lines = fit_font(draw, cta, 850, 2, 28, 20, bold=True)
    draw_lines(draw, (100, min(panel_bottom - 70, body_bottom + 24)), cta_lines, f_cta, GOLD, line_gap=5)

    draw.text((56, 1225), "HUMAN VISUAL APPROVAL REQUIRED", font=font(23, bold=True), fill=PAPER)
    draw.text((1024, 1225), "AUTO-PUBLISH OFF", font=font(21, bold=True), fill=GOLD, anchor="ra")
    source_ref = clean(normalized.get("source_ref"))
    source_text = f"SOURCE: {source_ref}" if source_ref else "SOURCE: FIXTURE / MANUAL PACKET CONTRACT"
    f_source, source_lines = fit_font(draw, source_text, 940, 1, 17, 13)
    draw_lines(draw, (56, 1283), source_lines, f_source, MUTED)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return {
        "primary_asset_mode": primary_mode,
        "secondary_asset_mode": secondary_mode,
        "width": WIDTH,
        "height": HEIGHT,
    }


def build_contact_sheet(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    columns = 3
    cell_w, cell_h = 360, 500
    header = 90
    count_rows = math.ceil(len(rows) / columns)
    sheet = Image.new("RGB", (columns * cell_w + 30, header + count_rows * cell_h + 20), (235, 235, 235))
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 18), "HSD Phase 7 Multi-Sport Editorial Review", font=font(26, bold=True), fill=(18, 18, 18))
    draw.text((20, 55), "All cards are review-only. Cross-sport live handoff remains disabled.", font=font(14), fill=(80, 80, 80))
    for index, row in enumerate(rows):
        column = index % columns
        line = index // columns
        x = 15 + column * cell_w
        y = header + line * cell_h
        path = Path(clean(row.get("output_path")))
        if path.exists():
            with Image.open(path) as source:
                card = source.convert("RGB")
            card.thumbnail((320, 400), Image.Resampling.LANCZOS)
            sheet.paste(card, (x + (320 - card.width) // 2 + 10, y + 4))
        draw.text((x + 10, y + 415), f"{index + 1}. {row.get('sport_id')} • {row.get('kind')}", font=font(12, bold=True), fill=(25, 25, 25))
        draw.text((x + 10, y + 438), clean(row.get("editorial_headline"))[:48], font=font(11), fill=(70, 70, 70))
        draw.text((x + 10, y + 460), clean(row.get("phase7_editorial_quality_status")), font=font(10), fill=(90, 90, 90))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET, quality=92)


def build(events_path: Path, mode: str, include_wnba: bool) -> Dict[str, Any]:
    payload = read_json(events_path)
    raw_events = payload.get("events") if isinstance(payload.get("events"), list) else []
    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            continue
        event = normalize_event(raw)
        if clean(event.get("sport_id")) == "wnba" and not include_wnba:
            continue
        try:
            editorial = generate_editorial(event)
            output = CARDS_ROOT / clean(event.get("sport_id")) / f"{slug(event.get('event_id'))}__{slug(event.get('kind'))}.png"
            asset_meta = render_card(event, editorial, output)
            row = {
                "item_id": f"{event.get('event_id')}::{event.get('sport_id')}::{event.get('kind')}::ig_feed",
                **event,
                **editorial,
                **asset_meta,
                "platform": "ig_feed",
                "output_path": output.as_posix(),
                "review_only": "true",
                "human_visual_approval_required": "true",
            }
            rows.append(row)
        except Exception as exc:
            errors.append(f"{clean(event.get('event_id'))}:{type(exc).__name__}:{exc}")

    blockers: List[str] = []
    warnings: List[str] = []
    if not rows:
        if mode == "fixture_audit":
            blockers.append("no_phase7_multisport_cards")
        else:
            warnings.append("no_non_wnba_live_packets_available_for_phase7_cards")
    failed = [row for row in rows if clean(row.get("phase7_editorial_quality_status")) != "passed_phase7_editorial_quality"]
    if failed:
        blockers.append("phase7_editorial_quality_failures_present")
    if errors:
        blockers.append("phase7_multisport_render_errors_present")
    if mode == "fixture_audit":
        expected = {"wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"} if include_wnba else {"nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"}
        rendered = {clean(row.get("sport_id")) for row in rows}
        for sport_id in sorted(expected - rendered):
            blockers.append(f"fixture_multisport_card_missing:{sport_id}")

    status = "passed_phase7_multisport_renderer" if not blockers else "blocked_phase7_multisport_renderer"
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "mode": mode,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "rendered_count": len(rows),
        "sport_counts": {sport_id: sum(clean(row.get("sport_id")) == sport_id for row in rows) for sport_id in sorted({clean(row.get("sport_id")) for row in rows})},
        "editorial_failed_count": len(failed),
        "errors": errors,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "review_only": True,
        "human_visual_approval_required": True,
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "rows": rows,
    }
    return report


def write_outputs(report: Mapping[str, Any]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps({"version": VERSION, "mode": report.get("mode"), "items": report.get("rows") or []}, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(MANIFEST_CSV, report.get("rows") or [])
    build_contact_sheet(list(report.get("rows") or []))
    REPORT_JSON.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 7 Multi-Sport Review Card Renderer",
        "",
        f"Mode: `{report.get('mode')}`",
        f"Status: `{report.get('status')}`",
        f"Rendered: `{report.get('rendered_count')}`",
        f"Editorial failures: `{report.get('editorial_failed_count')}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Sports",
        "",
    ]
    for sport_id, count in (report.get("sport_counts") or {}).items():
        lines.append(f"- `{sport_id}`: `{count}`")
    lines += ["", "## Blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Render Phase 7 multi-sport editorial review cards.")
    parser.add_argument("--events", default=EVENTS_JSON.as_posix())
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--include-wnba", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build(Path(args.events), args.mode, args.include_wnba)
    write_outputs(report)
    print(json.dumps({key: report[key] for key in ["version", "mode", "status", "rendered_count", "sport_counts", "editorial_failed_count", "blockers", "errors"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
