from __future__ import annotations

import argparse
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

from hsd_phase8b_result_language import clean, generate_result_editorial

VERSION = "v1.0-phase8b-daily-multisport-card-renderer"
EVENTS_JSON = Path("outputs/latest/HSD_PHASE8B/daily_multisport_events.json")
OUT_DIR = Path("outputs/latest/HSD_PHASE8B_MULTISPORT")
RENDER_DIR = OUT_DIR / "renders"
MANIFEST_JSON = OUT_DIR / "phase8b_multisport_manifest.json"
CONTACT_SHEET = OUT_DIR / "phase8b_multisport_contact_sheet.jpg"
REPORT_JSON = Path("phase8b_multisport_renderer_report.json")
REPORT_MD = Path("phase8b_multisport_renderer_report.md")
GOLD = (223, 161, 38)
BG = (4, 6, 12)
INK = (238, 236, 226)
MUTED = (190, 187, 177)
SPORT_LABELS = {"nwsl":"NWSL","uswnt":"USWNT","tennis":"WOMEN'S TENNIS","lpga":"LPGA","ncaa_softball":"NCAA SOFTBALL","volleyball":"VOLLEYBALL","wnba":"WNBA"}


def font(size: int, bold: bool = True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_width, max_lines=2):
    words = clean(text).split()
    lines=[]; line=""
    for word in words:
        cand=f"{line} {word}".strip()
        if draw.textbbox((0,0), cand, font=fnt)[2] <= max_width:
            line=cand
        else:
            if line: lines.append(line)
            line=word
        if len(lines)>=max_lines: break
    if line and len(lines)<max_lines: lines.append(line)
    return lines[:max_lines]


def load_events() -> List[Dict[str, Any]]:
    if not EVENTS_JSON.exists():
        return []
    payload = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    return [item for item in payload.get("items") or [] if isinstance(item, dict) and clean(item.get("sport_id")) != "wnba" and clean(item.get("phase8b_packet_status")) == "passed_phase8b_packet_validation"]


def card_copy(event: Dict[str, Any]) -> Dict[str, str]:
    kind = clean(event.get("kind"))
    sport = clean(event.get("sport_id"))
    if kind == "result":
        ed = generate_result_editorial(event)
        return {
            "headline": clean(ed.get("phase8b_result_headline")),
            "label": clean(ed.get("phase8b_result_label")),
            "body": clean(ed.get("phase8b_result_body")),
            "cta": clean(ed.get("phase8b_result_cta")),
            "scoreline": clean(ed.get("phase8b_result_scoreline")),
        }
    primary = clean(event.get("primary_short") or event.get("primary_name"))
    secondary = clean(event.get("secondary_short") or event.get("secondary_name"))
    angle = clean(event.get("verified_angle"))
    if sport in {"nwsl", "uswnt"}:
        label = "PRESS OR WIDTH?"
        body = angle or "Watch the release pass, wide lane, and second-ball battle."
    elif sport == "tennis":
        label = "FIRST-STRIKE READ"
        body = angle or "Return depth and second-serve pressure decide the shape."
    elif sport == "lpga":
        label = "SCORING WINDOW"
        body = angle or "Approach control and the putter decide the card."
    elif sport == "ncaa_softball":
        label = "CIRCLE CHECK"
        body = angle or "Traffic, first-pitch strikes, and free passes decide the inning."
    elif sport == "volleyball":
        label = "SERVE-PASS EDGE"
        body = angle or "First contact and sideout pressure decide the run."
    else:
        label = "SPORT-SPECIFIC READ"
        body = angle or "Track the matchup lever."
    return {
        "headline": f"{primary.upper()} VS {secondary.upper()}" if secondary else primary.upper(),
        "label": label,
        "body": body,
        "cta": "What are you watching first?",
        "scoreline": clean(event.get("event_title")),
    }


def render_card(event: Dict[str, Any], idx: int) -> Dict[str, Any]:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1080, 1350), BG)
    draw = ImageDraw.Draw(img)
    # Background texture lines
    for y in range(0, 1350, 34):
        col = (10 + (y % 80), 12 + (y % 40), 18 + (y % 50))
        draw.line((0, y, 1080, y + 200), fill=col, width=1)
    draw.rounded_rectangle((50, 44, 152, 146), radius=14, outline=GOLD, width=2)
    draw.text((66, 62), "HSD", font=font(31), fill=INK)
    sport = clean(event.get("sport_id"))
    label = SPORT_LABELS.get(sport, sport.upper())
    draw.text((180, 64), label, font=font(30), fill=GOLD)
    draw.text((180, 102), clean(event.get("kind")).upper() or "STORY", font=font(22), fill=MUTED)
    copy = card_copy(event)
    draw.text((72, 240), copy["headline"], font=font(64), fill=INK)
    draw.line((72, 333, 1008, 333), fill=GOLD, width=3)
    draw.text((72, 405), copy["label"], font=font(52), fill=GOLD)
    y = 500
    for line in wrap(draw, copy["body"], font(38, False), 900, 3):
        draw.text((72, y), line, font=font(38, False), fill=INK)
        y += 54
    if copy.get("scoreline"):
        y += 30
        for line in wrap(draw, copy["scoreline"], font(34), 900, 2):
            draw.text((72, y), line, font=font(34), fill=MUTED)
            y += 48
    draw.rounded_rectangle((72, 1120, 1008, 1244), radius=18, outline=GOLD, width=2, fill=(0,0,0))
    draw.text((104, 1154), "HSD READ", font=font(28), fill=GOLD)
    draw.text((310, 1151), copy["cta"].upper(), font=font(34), fill=INK)
    out = RENDER_DIR / f"{idx:02d}_{clean(event.get('event_id'))}.png"
    img.save(out)
    return {**event, **{f"phase8b_card_{k}": v for k, v in copy.items()}, "output_path": out.as_posix(), "phase8b_multisport_card_status": "passed_phase8b_multisport_card"}


def make_contact_sheet(items: List[Dict[str, Any]]) -> None:
    if not items:
        return
    thumbs=[]
    for i,item in enumerate(items,1):
        im=Image.open(item['output_path']).convert('RGB').resize((216,270))
        d=ImageDraw.Draw(im)
        d.rectangle((0,0,52,42), fill=(0,0,0))
        d.text((10,7), str(i), font=font(26), fill=GOLD)
        thumbs.append(im)
    cols=4; rows=(len(thumbs)+cols-1)//cols
    sheet=Image.new('RGB',(cols*216,rows*270),BG)
    for i,im in enumerate(thumbs):
        sheet.paste(im,((i%cols)*216,(i//cols)*270))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main(argv: Optional[List[str]]=None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixture_audit','live_data'], default='fixture_audit')
    parser.add_argument('--strict', action='store_true')
    args=parser.parse_args(argv)
    events=load_events()
    items=[]; errors=[]
    for idx,event in enumerate(events,1):
        try:
            items.append(render_card(event, idx))
        except Exception as exc:
            errors.append(f"{event.get('event_id')}:render_error:{exc}")
    make_contact_sheet(items)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps({"version": VERSION, "items": items}, indent=2, sort_keys=True), encoding='utf-8')
    report={"version":VERSION,"mode":args.mode,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"status":"passed_phase8b_multisport_renderer" if not errors else "blocked_phase8b_multisport_renderer","strict_exit_code":0 if not errors else 2,"events_loaded":len(events),"cards_rendered":len(items),"sports_present":sorted({clean(i.get('sport_id')) for i in items}),"blockers":errors,"warnings":["no_non_wnba_daily_packets_found"] if args.mode=='live_data' and not items else [],"contact_sheet":CONTACT_SHEET.as_posix() if CONTACT_SHEET.exists() else ""}
    REPORT_JSON.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    lines=["# HSD Phase 8B Multi-Sport Card Renderer","",f"Mode: `{args.mode}`",f"Status: `{report['status']}`",f"Cards rendered: `{len(items)}`",f"Sports: `{', '.join(report['sports_present']) or 'none'}`","","## Blockers"]
    lines += [f"- `{b}`" for b in errors] or ["- None"]
    lines += ["", "## Warnings"] + ([f"- `{w}`" for w in report['warnings']] or ["- None"])
    REPORT_MD.write_text("\n".join(lines)+"\n",encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['version','mode','status','cards_rendered','sports_present','blockers','warnings']}, indent=2))
    return report['strict_exit_code'] if args.strict else 0

if __name__ == '__main__':
    raise SystemExit(main())
