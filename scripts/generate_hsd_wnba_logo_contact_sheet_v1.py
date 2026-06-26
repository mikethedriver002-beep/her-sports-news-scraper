from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - reported in manifest
    Image = None
    ImageDraw = None
    ImageFont = None


VERSION = "hsd-wnba-logo-contact-sheet-v1-review-only"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUT_MD = output_path("data/asset_registry/wnba/wnba_team_logo_contact_sheet.md")
OUT_CSV = output_path("data/asset_registry/wnba/wnba_team_logo_contact_sheet.csv")
OUT_PNG = output_path("data/asset_registry/wnba/wnba_team_logo_contact_sheet.png")
OUT_INTAKE = output_path("data/asset_registry/wnba/wnba_team_logo_review_intake.csv")
OUT_JSON = output_path("data/asset_registry/wnba/wnba_team_logo_contact_sheet.json")

CONTACT_FIELDS = [
    "team_id",
    "team_name",
    "conference",
    "active",
    "local_logo_path",
    "logo_image_path",
    "logo_file_exists",
    "current_source_url",
    "current_source_note",
    "official_source_candidate",
    "current_approval_status",
    "required",
    "source_trust_status",
    "logo_readiness_status",
    "renderer_fallback_cue",
    "operator_action",
    "allowed_decisions",
    "human_intake_file",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]

INTAKE_FIELDS = [
    "team_id",
    "team_name",
    "local_logo_path",
    "current_source_url",
    "official_source_candidate",
    "current_approval_status",
    "allowed_decisions",
    "operator_decision",
    "source_reviewed",
    "identity_match",
    "source_url_to_record",
    "registry_action",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]

TEAM_SOURCE_CANDIDATES = {
    "atlanta_dream": "https://www.wnba.com/team/atlanta-dream",
    "chicago_sky": "https://www.wnba.com/team/chicago-sky",
    "connecticut_sun": "https://www.wnba.com/team/connecticut-sun",
    "indiana_fever": "https://www.wnba.com/team/indiana-fever",
    "new_york_liberty": "https://www.wnba.com/team/new-york-liberty",
    "toronto_tempo": "https://www.wnba.com/team/toronto-tempo",
    "washington_mystics": "https://www.wnba.com/team/washington-mystics",
    "dallas_wings": "https://www.wnba.com/team/dallas-wings",
    "golden_state_valkyries": "https://www.wnba.com/team/golden-state-valkyries",
    "las_vegas_aces": "https://www.wnba.com/team/las-vegas-aces",
    "los_angeles_sparks": "https://www.wnba.com/team/los-angeles-sparks",
    "minnesota_lynx": "https://www.wnba.com/team/minnesota-lynx",
    "phoenix_mercury": "https://www.wnba.com/team/phoenix-mercury",
    "portland_fire": "https://www.wnba.com/team/portland-fire",
    "seattle_storm": "https://www.wnba.com/team/seattle-storm",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def boolish(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def project_path(raw: Any) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        return path.as_posix()


def by_key(rows: Iterable[Mapping[str, str]], key: str) -> Dict[str, Mapping[str, str]]:
    return {clean(row.get(key)): row for row in rows if clean(row.get(key))}


def load_font(size: int, *, bold: bool = False) -> Any:
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for raw in candidates:
        path = Path(raw)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def source_candidate(team_id: str, team_name: str) -> str:
    if team_id in TEAM_SOURCE_CANDIDATES:
        return TEAM_SOURCE_CANDIDATES[team_id]
    slug = re.sub(r"[^a-z0-9]+", "-", team_name.lower()).strip("-")
    return f"https://www.wnba.com/team/{slug}" if slug else "https://www.wnba.com/teams"


def logo_path_for(team_logo: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    for key in ["png_path", "local_logo_path"]:
        raw = clean(catalog_row.get(key))
        if raw and project_path(raw).exists():
            return raw
    raw = clean(team_logo.get("file_path")) or clean(catalog_row.get("local_logo_path"))
    return raw


def approval_status(team_logo: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    catalog_status = clean(catalog_row.get("approval_status"))
    if catalog_status:
        return catalog_status
    if boolish(team_logo.get("approved")):
        return "approved"
    if boolish(team_logo.get("file_exists")):
        return "unapproved_review_required"
    return "missing"


def build_rows() -> List[Dict[str, str]]:
    teams = [
        row
        for row in read_csv("data/asset_registry/wnba/teams.csv")
        if clean(row.get("league")).upper() == "WNBA" and boolish(row.get("active"))
    ]
    logos = by_key(read_csv("data/asset_registry/wnba/team_logos.csv"), "team_id")
    sources = by_key(read_csv("data/asset_registry/wnba/logo_sources.csv"), "team_id")
    catalog = {
        clean(row.get("team_id")): row
        for row in read_csv("data/asset_registry/logo_asset_catalog.csv")
        if clean(row.get("league")).upper() == "WNBA" and clean(row.get("entity_type")) == "team_logo"
    }

    rows: List[Dict[str, str]] = []
    for team in teams:
        team_id = clean(team.get("team_id"))
        team_name = clean(team.get("team_name")) or team_id
        logo = logos.get(team_id, {})
        source = sources.get(team_id, {})
        cat = catalog.get(team_id, {})
        logo_path = logo_path_for(logo, cat)
        rows.append(
            {
                "team_id": team_id,
                "team_name": team_name,
                "conference": clean(team.get("conference")),
                "active": clean(team.get("active")) or "true",
                "local_logo_path": clean(logo.get("file_path")) or clean(cat.get("local_logo_path")),
                "logo_image_path": logo_path,
                "logo_file_exists": str(project_path(logo_path).exists()).lower() if logo_path else "false",
                "current_source_url": clean(source.get("source_url")) or clean(cat.get("source_url")),
                "current_source_note": clean(source.get("source_note")) or clean(cat.get("source_note")),
                "official_source_candidate": source_candidate(team_id, team_name),
                "current_approval_status": approval_status(logo, cat),
                "required": clean(logo.get("required")) or clean(cat.get("required")) or "true",
                "source_trust_status": clean(cat.get("source_trust_status")) or "source_review_required",
                "logo_readiness_status": clean(cat.get("logo_readiness_status")) or "manual_review_required",
                "renderer_fallback_cue": clean(cat.get("renderer_fallback_cue")) or "Renderer fallback remains review-only until manual review.",
                "operator_action": clean(cat.get("operator_action")) or "manual_logo_review_required",
                "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                "human_intake_file": "data/asset_registry/wnba/wnba_team_logo_review_intake.csv",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return rows


def existing_intake_by_team() -> Dict[str, Mapping[str, str]]:
    return by_key(read_csv("data/asset_registry/wnba/wnba_team_logo_review_intake.csv"), "team_id")


def intake_rows(rows: Iterable[Mapping[str, str]], existing_by_team: Mapping[str, Mapping[str, str]] | None = None) -> List[Dict[str, str]]:
    existing_by_team = existing_by_team or existing_intake_by_team()
    output: List[Dict[str, str]] = []
    for row in rows:
        existing = existing_by_team.get(clean(row.get("team_id")), {})
        output.append(
            {
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "local_logo_path": clean(row.get("local_logo_path")),
                "current_source_url": clean(row.get("current_source_url")),
                "official_source_candidate": clean(row.get("official_source_candidate")),
                "current_approval_status": clean(row.get("current_approval_status")),
                "allowed_decisions": clean(row.get("allowed_decisions")),
                "operator_decision": clean(existing.get("operator_decision")),
                "source_reviewed": clean(existing.get("source_reviewed")),
                "identity_match": clean(existing.get("identity_match")),
                "source_url_to_record": clean(existing.get("source_url_to_record")),
                "registry_action": clean(existing.get("registry_action")),
                "operator_notes": clean(existing.get("operator_notes")),
                "reviewed_by": clean(existing.get("reviewed_by")),
                "reviewed_at_local": clean(existing.get("reviewed_at_local")),
                "approval_scope": "review_only_renderer_logo_trust_manual_intake",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return output


def fit_image(path: Path, box_w: int, box_h: int) -> Any:
    image = Image.open(path).convert("RGBA")
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    scale = min(box_w / max(1, image.width), box_h / max(1, image.height))
    resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (box_w, box_h), (255, 255, 255, 0))
    canvas.alpha_composite(resized, ((box_w - resized.width) // 2, (box_h - resized.height) // 2))
    return canvas


def text_width(draw: Any, text: str, font: Any) -> int:
    if hasattr(draw, "textbbox"):
        box = draw.textbbox((0, 0), text, font=font)
        return int(box[2] - box[0])
    return int(draw.textlength(text, font=font))


def ellipsize(draw: Any, text: str, font: Any, max_width: int) -> str:
    value = clean(text)
    if text_width(draw, value, font) <= max_width:
        return value
    suffix = "..."
    while value and text_width(draw, value + suffix, font) > max_width:
        value = value[:-1]
    return (value.rstrip() + suffix) if value else suffix


def make_contact_sheet(rows: List[Mapping[str, str]], out_path: Path = OUT_PNG) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if Image is None or ImageDraw is None:
        warnings.append("pillow_unavailable_contact_sheet_not_created")
        return out_path.as_posix(), warnings

    cols = 5
    card_w, card_h = 330, 290
    margin = 32
    header_h = 92
    rows_count = max(1, (len(rows) + cols - 1) // cols)
    width = margin * 2 + cols * card_w
    height = margin * 2 + header_h + rows_count * card_h
    image = Image.new("RGB", (width, height), (246, 248, 250))
    draw = ImageDraw.Draw(image)
    font_title = load_font(32, bold=True)
    font_body = load_font(18)
    font_small = load_font(14)
    draw.text((margin, 24), "WNBA Team Logo Review Contact Sheet", fill=(12, 20, 28), font=font_title)
    draw.text((margin, 62), "Review-only board. Human decisions belong in wnba_team_logo_review_intake.csv.", fill=(74, 83, 94), font=font_body)

    for index, row in enumerate(rows):
        col = index % cols
        row_i = index // cols
        x = margin + col * card_w
        y = margin + header_h + row_i * card_h
        draw.rounded_rectangle((x + 8, y + 8, x + card_w - 14, y + card_h - 14), radius=10, fill=(255, 255, 255), outline=(215, 222, 230), width=2)
        logo_path = project_path(row.get("logo_image_path"))
        if logo_path.exists():
            try:
                logo = fit_image(logo_path, 188, 126)
                image.paste(logo, (x + 70, y + 24), logo)
            except Exception as exc:
                warnings.append(f"{row.get('team_id')}:logo_render_failed:{exc}")
                draw.text((x + 80, y + 74), "logo render failed", fill=(138, 43, 43), font=font_small)
        else:
            draw.rectangle((x + 78, y + 44, x + 250, y + 130), fill=(236, 240, 244), outline=(180, 188, 196))
            draw.text((x + 104, y + 76), "logo missing", fill=(138, 43, 43), font=font_small)
        status = clean(row.get("current_approval_status")) or "review"
        status_fill = (18, 118, 86) if status == "approved" else (154, 99, 0) if "review" in status or "hold" in status else (130, 38, 38)
        text_max = card_w - 48
        draw.text((x + 24, y + 168), clean(row.get("team_name")), fill=(12, 20, 28), font=font_body)
        draw.text((x + 24, y + 196), f"Status: {status}", fill=status_fill, font=font_small)
        draw.text((x + 24, y + 218), ellipsize(draw, f"Path: {clean(row.get('local_logo_path'))}", font_small, text_max), fill=(74, 83, 94), font=font_small)
        draw.text((x + 24, y + 242), ellipsize(draw, f"Decision: {clean(row.get('allowed_decisions')).split('|')[0]}", font_small, text_max), fill=(74, 83, 94), font=font_small)

    image.save(out_path)
    return out_path.as_posix(), warnings


def render_markdown(rows: List[Mapping[str, str]], png_path: str, generated_at: str) -> str:
    approved = sum(1 for row in rows if clean(row.get("current_approval_status")) == "approved")
    unapproved = sum(1 for row in rows if "unapproved" in clean(row.get("current_approval_status")))
    lines = [
        "# WNBA Team Logo Contact Sheet",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only sweep board for every active WNBA team logo in the local registry. This file does not approve assets, download files, move files, publish, or create a publish-ready lane.",
        "",
        f"![WNBA team logo contact sheet]({Path(png_path).name})",
        "",
        "## Summary",
        "",
        f"- Teams: `{len(rows)}`",
        f"- Approved: `{approved}`",
        f"- Needs manual review: `{unapproved}`",
        "- Human-edited intake CSV: `data/asset_registry/wnba/wnba_team_logo_review_intake.csv`",
        "- Allowed decisions: `approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata`",
        "- Guardrails: review_only=true; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false",
        "",
        "## Rows",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row.get('team_name')} | status={row.get('current_approval_status')} | local={row.get('local_logo_path')} | "
            f"current_source={row.get('current_source_url') or 'missing'} | official_candidate={row.get('official_source_candidate')} | "
            f"action={row.get('operator_action')}"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_iso()
    rows = build_rows()
    png_path, warnings = make_contact_sheet(rows)
    decisions = intake_rows(rows)
    write_csv(OUT_CSV, rows, CONTACT_FIELDS)
    write_csv(OUT_INTAKE, decisions, INTAKE_FIELDS)
    write_text(OUT_MD, render_markdown(rows, png_path, generated_at))
    manifest = {
        "version": VERSION,
        "generated_at_utc": generated_at,
        "review_only": True,
        "status": "contact_sheet_ready" if rows else "no_rows",
        "team_rows": len(rows),
        "contact_sheet": OUT_PNG.as_posix(),
        "contact_sheet_data": OUT_CSV.as_posix(),
        "human_intake_csv": OUT_INTAKE.as_posix(),
        "warnings": warnings,
        "guardrails": {
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
            "asset_downloads": False,
            "publishing": False,
        },
    }
    write_json(OUT_JSON, manifest)
    print(json.dumps({"version": VERSION, "status": manifest["status"], "rows": len(rows), "contact_sheet": OUT_PNG.as_posix(), "intake": OUT_INTAKE.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
