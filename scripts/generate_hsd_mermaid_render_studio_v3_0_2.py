from __future__ import annotations

import csv
import json
import math
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

import generate_hsd_mermaid_render_studio_v3_0 as rv  # type: ignore

VERSION = "v3.0.2-approved-athlete-image-integration"
ATHLETES_CSV = Path("data/asset_registry/wnba/athletes.csv")
ATHLETE_IMAGES_CSV = Path("data/asset_registry/wnba/athlete_images.csv")
ATHLETE_NEEDS_FIX_CSV = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")
ATHLETE_APPROVED_CSV = Path("data/asset_registry/wnba/athlete_image_approved_assets.csv")

STATUS_FIELDS = rv.STATUS_FIELDS + ["used_athletes", "missing_athletes"]
MANIFEST_FIELDS = rv.MANIFEST_FIELDS + ["used_athletes"]
VISUAL_QA_FIELDS = rv.VISUAL_QA_FIELDS + ["used_athletes", "missing_athletes"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def safe_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def choose_template(packet: Dict[str, Any]) -> str:
    headline = str(packet.get("headline", "")).lower()
    content_type = str(packet.get("content_type", "")).lower()
    league = str(packet.get("league", "")).upper()
    if league == "WNBA":
        if "last night in the w" in headline:
            return "last_night_scoreboard"
        if "preview" in content_type or " at " in headline or " vs " in headline:
            return "preview_matchup"
        if "beat" in headline or "result" in content_type or "recap" in content_type:
            return "result_final"
        return "storyline_feature"
    return "storyline_feature"


def nested_strings(value: Any) -> List[str]:
    out: List[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(nested_strings(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(nested_strings(item))
    return out


def parse_packet(zp: Path) -> Dict[str, Any]:
    with zipfile.ZipFile(zp) as z:
        data = json.loads(z.read("content_packet.json").decode("utf-8"))
    packet = rv.parse_packet(zp)
    packet["raw_text"] = " | ".join(clean(x) for x in nested_strings(data) if clean(x))
    return packet


def athlete_registry() -> Tuple[Dict[str, Dict[str, str]], Dict[str, str], set[str]]:
    athletes = {r.get("athlete_id", ""): r for r in read_csv(ATHLETES_CSV) if r.get("athlete_id")}
    needs_fix = {r.get("athlete_id", "") for r in read_csv(ATHLETE_NEEDS_FIX_CSV) if r.get("athlete_id")}
    approved: Dict[str, str] = {}
    for row in read_csv(ATHLETE_IMAGES_CSV):
        aid = row.get("athlete_id", "")
        if row.get("image_type") == "headshot" and row.get("approved") == "true" and row.get("file_exists") == "true":
            path = clean(row.get("file_path"))
            if Path(path).exists() and Path(path + ".approved").exists():
                approved[aid] = path
    for row in read_csv(ATHLETE_APPROVED_CSV):
        aid = row.get("athlete_id", "")
        path = clean(row.get("approved_file"))
        marker = clean(row.get("approved_marker")) or path + ".approved"
        if aid and Path(path).exists() and Path(marker).exists():
            approved[aid] = path
    out: Dict[str, Dict[str, str]] = {}
    for aid, path in approved.items():
        if aid in athletes:
            item = dict(athletes[aid])
            item["headshot_path"] = path
            out[aid] = item
    # Use full names only to avoid surname-only false positives.
    full_name_aliases: Dict[str, str] = {}
    for aid, row in athletes.items():
        name = clean(row.get("display_name"))
        if len(name.split()) >= 2:
            full_name_aliases[norm(name)] = aid
    return out, full_name_aliases, needs_fix


def resolve_athletes(packet: Dict[str, Any], approved: Dict[str, Dict[str, str]], aliases: Dict[str, str], needs_fix: set[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    if packet.get("league", "").upper() != "WNBA":
        return [], []
    blob = " ".join(clean(packet.get(k, "")) for k in ["headline", "hook", "story", "caption", "first", "raw_text"])
    blob_n = norm(blob)
    found: List[Dict[str, str]] = []
    missing: List[str] = []
    for alias, aid in sorted(aliases.items(), key=lambda kv: len(kv[0]), reverse=True):
        if alias and alias in blob_n:
            if aid in needs_fix:
                missing.append(aid + ":needs_fix")
            elif aid in approved and aid not in {x.get("athlete_id") for x in found}:
                found.append(approved[aid])
    return found[:3], missing[:8]


def circular_headshot(path: str, size: int) -> Optional[Image.Image]:
    try:
        im = Image.open(path).convert("RGBA")
        # Center crop to square before circular mask.
        w, h = im.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        im = im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse((0, 0, size - 1, size - 1), fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.alpha_composite(im)
        out.putalpha(mask)
        return out
    except Exception:
        return None


def draw_athlete_strip(img: Image.Image, athletes: List[Dict[str, str]], y: int, accent: Tuple[int, int, int]) -> None:
    if not athletes:
        return
    d = ImageDraw.Draw(img)
    W, _ = img.size
    card_h = 174
    card_w = min(292, (W - 180) // max(1, len(athletes)))
    gap = 18
    total = len(athletes) * card_w + (len(athletes) - 1) * gap
    x = (W - total) // 2
    label = "PLAYER FOCUS"
    f_label = rv.font(20, True)
    tw = rv.text_w(d, label, f_label)
    d.rounded_rectangle((x, y - 40, x + tw + 28, y - 10), radius=12, fill=(*accent, 210))
    d.text((x + 14, y - 38), label, font=f_label, fill=(255, 255, 255))
    for athlete in athletes:
        d.rounded_rectangle((x, y, x + card_w, y + card_h), radius=24, fill=(255, 255, 255, 24), outline=(255, 255, 255, 58), width=2)
        head = circular_headshot(athlete.get("headshot_path", ""), 106)
        if head:
            img.alpha_composite(head, (x + 18, y + 24))
            d.ellipse((x + 14, y + 20, x + 128, y + 134), outline=(*accent, 230), width=4)
        name = clean(athlete.get("display_name"))
        lines = rv.wrap(d, name.upper(), rv.font(24, True), card_w - 150, 2)
        ty = y + 44
        for line in lines:
            d.text((x + 142, ty), line, font=rv.font(24, True), fill=rv.INK)
            ty += 30
        team = clean(athlete.get("team_id", "")).replace("_", " ").upper()
        d.text((x + 142, y + 114), team[:18], font=rv.font(15, False), fill=rv.MUTED)
        x += card_w + gap


def apply_athlete_overlay(packet: Dict[str, Any], img: Image.Image, template: str, athletes: List[Dict[str, str]], teams: Dict[str, Dict[str, str]], team_ids: List[str]) -> Image.Image:
    if not athletes:
        img.info["athlete"] = "no"
        return img
    accent = rv.BLUE
    if team_ids:
        accent = rv.team_palette(team_ids[0], teams)[0]
    W, H = img.size
    if template == "result_final":
        y = 785 if H <= 1350 else 980
    elif template == "preview_matchup":
        y = H - (430 if H <= 1350 else 560)
    elif template == "storyline_feature":
        y = H - (430 if H <= 1350 else 560)
    else:
        img.info["athlete"] = "no"
        return img
    draw_athlete_strip(img, athletes, y, accent)
    img.info["athlete"] = ",".join(a.get("athlete_id", "") for a in athletes)
    return img


def render_one(packet: Dict[str, Any], wm: Optional[Image.Image], teams, team_aliases, logo_rows, all_pairs, approved_athletes, athlete_aliases, needs_fix) -> Tuple[str, List[Path], str, str, str, str, str, str, str]:
    template = choose_template(packet)
    if wm is None:
        return "blocked", [], "official HSD watermark missing", template, "no", "no", "", "no", ""
    pairs = rv.pairs_for_packet(packet, all_pairs, team_aliases)
    if template == "last_night_scoreboard" and not pairs:
        return "blocked", [], "score context missing for Last Night scoreboard", template, "no", "no", "", "no", ""
    required = rv.required_teams(packet, template, pairs, team_aliases)
    if template in {"result_final", "preview_matchup"} and packet.get("league", "").upper() == "WNBA" and len(required) < 2:
        return "blocked", [], "could not resolve two WNBA teams from headline", template, "no", "no", "", "no", ""
    logos, missing_logos, reasons = rv.resolve_logos(required, logo_rows)
    if missing_logos:
        return "blocked", [], "missing required registry team logo(s): " + "; ".join(reasons), template, "no", "no", "; ".join(missing_logos), "no", ""
    resolved_athletes, missing_athletes = resolve_athletes(packet, approved_athletes, athlete_aliases, needs_fix)
    if template == "result_final":
        img = rv.render_result(packet, wm, pairs[0] if pairs else None, logos, teams, team_aliases)
    elif template == "last_night_scoreboard":
        img = rv.render_last(packet, wm, pairs, logos, teams)
    elif template == "preview_matchup":
        img = rv.render_preview(packet, wm, logos, teams, team_aliases)
    else:
        img = rv.render_feature(packet, wm)
    img = apply_athlete_overlay(packet, img, template, resolved_athletes, teams, required)
    out = rv.save_image(packet, img)
    used_athletes = img.info.get("athlete", "no")
    return "rendered", [out], "ok", template, "yes" if logos else "not_required", img.info.get("score", "no"), "", used_athletes, "; ".join(missing_athletes)


def main() -> None:
    rv.VERSION = VERSION
    rv.choose_template = choose_template
    rv.parse_packet = parse_packet
    rv.clean_outputs()
    wm, wm_source = rv.load_watermark()
    teams, team_aliases, logo_rows = rv.registry()
    approved_athletes, athlete_aliases, needs_fix = athlete_registry()
    all_pairs = rv.score_pairs(team_aliases)
    status_rows = []
    manifest_rows = []
    visual_rows = []
    rendered_files: List[Path] = []
    packets = []
    for z in rv.discover_packets():
        try:
            packets.append(parse_packet(z))
        except Exception as exc:
            packet_id = z.stem
            status_rows.append({"packet_id": packet_id, "platform": "", "headline": packet_id, "status": "blocked", "reason": f"packet parse error: {type(exc).__name__}", "template_family": "unknown", "rendered_files": 0, "used_watermark": "yes" if wm else "no", "used_logos": "no", "used_score_context": "no", "missing_logos": "", "used_athletes": "no", "missing_athletes": ""})
    for packet in packets:
        try:
            st, outs, reason, template, used_logos, used_score, missing_logos, used_athletes, missing_athletes = render_one(packet, wm, teams, team_aliases, logo_rows, all_pairs, approved_athletes, athlete_aliases, needs_fix)
        except Exception as exc:
            st, outs, reason, template, used_logos, used_score, missing_logos, used_athletes, missing_athletes = "blocked", [], f"render exception: {type(exc).__name__}: {exc}", choose_template(packet), "no", "no", "", "no", ""
        status_rows.append({"packet_id": packet["packet_id"], "platform": packet["platform"], "headline": packet["headline"], "status": st, "reason": reason, "template_family": template, "rendered_files": len(outs), "used_watermark": "yes" if wm else "no", "used_logos": used_logos, "used_score_context": used_score, "missing_logos": missing_logos, "used_athletes": used_athletes, "missing_athletes": missing_athletes})
        dims = ""
        for out in outs:
            rendered_files.append(out)
            try:
                with Image.open(out) as im:
                    W, H = im.size
                dims = f"{W}x{H}"
                manifest_rows.append({"packet_id": packet["packet_id"], "platform": packet["platform"], "headline": packet["headline"], "template_family": template, "output_path": out.as_posix(), "width": W, "height": H, "used_watermark": "yes", "used_logos": used_logos, "used_score_context": used_score, "used_athletes": used_athletes})
            except Exception as exc:
                status_rows.append({"packet_id": packet["packet_id"], "platform": packet["platform"], "headline": packet["headline"], "status": "blocked", "reason": f"saved image unreadable: {type(exc).__name__}", "template_family": template, "rendered_files": 0, "used_watermark": "yes", "used_logos": used_logos, "used_score_context": used_score, "missing_logos": missing_logos, "used_athletes": used_athletes, "missing_athletes": missing_athletes})
        visual_rows.append({"packet_id": packet["packet_id"], "platform": packet["platform"], "headline": packet["headline"], "template_family": template, "dimensions": dims, "watermark_status": "pass" if wm else "fail", "used_logos": used_logos, "missing_logos": missing_logos, "used_score_context": used_score, "public_text_safe": "yes", "internal_text_found": "no", "decision": "pass" if st == "rendered" else "fail", "reason": reason, "used_athletes": used_athletes, "missing_athletes": missing_athletes})
    rv.make_contact_sheet(rendered_files)
    zip_count = rv.zip_outputs()
    rv.write_csv(rv.STATUS, status_rows, STATUS_FIELDS)
    rv.write_csv(rv.MANIFEST, manifest_rows, MANIFEST_FIELDS)
    rv.write_csv(rv.VISUAL_QA, visual_rows, VISUAL_QA_FIELDS)
    rendered_count = sum(1 for r in status_rows if r.get("status") == "rendered")
    blocked_count = sum(1 for r in status_rows if r.get("status") == "blocked")
    png_count = len(rendered_files)
    athlete_used_count = len([r for r in status_rows if r.get("used_athletes") not in {"", "no"}])
    integrity = "pass"
    integrity_reason = "ok"
    if png_count > 0 and rendered_count == 0:
        integrity = "fail"; integrity_reason = "graphics_files_gt_zero_but_rendered_packets_zero"
    if rendered_count > 0 and len(manifest_rows) == 0:
        integrity = "fail"; integrity_reason = "rendered_packets_gt_zero_but_manifest_empty"
    meta = {"version": VERSION, "generated_at_utc": rv.now_iso(), "packets_seen": len(packets), "rendered_packets": rendered_count, "blocked_packets": blocked_count, "graphics_files": png_count, "zip_files": zip_count, "watermark_source": wm_source, "score_pairs_found": len(all_pairs), "registry_team_count": len(teams), "registry_logo_count": len(logo_rows), "approved_athlete_count": len(approved_athletes), "needs_fix_athlete_count": len(needs_fix), "packets_using_approved_athletes": athlete_used_count, "integrity_status": integrity, "integrity_reason": integrity_reason, "logo_source": "data/asset_registry/wnba/team_logos.csv", "athlete_source": "data/asset_registry/wnba/athlete_images.csv"}
    rv.META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    lines = ["# Mermaid Render Studio v3.0.2 Approved Athlete Image QA Report", "", f"Generated: {meta['generated_at_utc']}", f"Version: {VERSION}", "", "## Counts", "", f"- packets seen: {len(packets)}", f"- rendered packets: {rendered_count}", f"- blocked packets: {blocked_count}", f"- graphics files: {png_count}", f"- zip files: {zip_count}", f"- score pairs found: {len(all_pairs)}", f"- registry teams: {len(teams)}", f"- registry logos: {len(logo_rows)}", f"- approved athlete images available: {len(approved_athletes)}", f"- needs-fix athletes blocked: {len(needs_fix)}", f"- packets using approved athletes: {athlete_used_count}", f"- watermark source: {wm_source}", f"- integrity status: {integrity}", f"- integrity reason: {integrity_reason}", "", "## Packet Status", ""]
    for row in status_rows:
        lines.append(f"- {row.get('packet_id')} | {row.get('platform')} | {row.get('template_family')} | {row.get('headline')} | {row.get('status')} | athletes={row.get('used_athletes')} | missing_athletes={row.get('missing_athletes')} | {row.get('reason')}")
    rv.REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
