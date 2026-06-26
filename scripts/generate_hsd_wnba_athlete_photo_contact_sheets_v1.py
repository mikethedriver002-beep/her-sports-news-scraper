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


VERSION = "hsd-wnba-athlete-photo-contact-sheets-v1-review-only"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUT_DIR = output_path("data/asset_registry/wnba/athlete_photo_contact_sheets")
OUT_INDEX = output_path("data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_index.md")
OUT_CSV = output_path("data/asset_registry/wnba/wnba_athlete_photo_contact_sheet.csv")
OUT_INTAKE = output_path("data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv")
OUT_JSON = output_path("data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_manifest.json")

CONTACT_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "team_name",
    "conference",
    "local_headshot_path",
    "local_headshot_exists",
    "approved_marker_path",
    "approved_marker_exists",
    "current_approval_status",
    "identity_review_status",
    "provider_player_id",
    "official_roster_page_candidate",
    "official_player_profile_candidate",
    "official_roster_photo_candidate_url",
    "source_evidence",
    "crop_readiness_notes",
    "allowed_decisions",
    "human_intake_file",
    "team_contact_sheet_path",
    "team_review_board_path",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]

INTAKE_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "team_name",
    "local_headshot_path",
    "approved_marker_path",
    "provider_player_id",
    "official_roster_page_candidate",
    "official_player_profile_candidate",
    "official_roster_photo_candidate_url",
    "current_approval_status",
    "identity_review_status",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "source_reviewed",
    "local_file_reviewed",
    "source_url_to_record",
    "provider_player_id_verified",
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def boolish(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def slug(value: Any) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", clean(value).lower())).strip("_") or "unknown"


def url_slug(value: Any) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", clean(value).lower())).strip("-")


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def by_key(rows: Iterable[Mapping[str, str]], key: str) -> Dict[str, Mapping[str, str]]:
    return {clean(row.get(key)): row for row in rows if clean(row.get(key))}


def project_path(raw: Any) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


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


def official_profile_url(provider_player_id: str, athlete_name: str) -> str:
    if not provider_player_id:
        return ""
    return f"https://www.wnba.com/player/{provider_player_id}/{url_slug(athlete_name)}"


def team_contact_sheet_path(team_id: str) -> str:
    return (OUT_DIR / f"{slug(team_id)}.png").as_posix()


def team_review_board_path(team_id: str) -> str:
    return (OUT_DIR / f"{slug(team_id)}.md").as_posix()


def build_rows() -> List[Dict[str, str]]:
    teams = by_key(
        [
            row
            for row in read_csv("data/asset_registry/wnba/teams.csv")
            if clean(row.get("league")).upper() == "WNBA" and boolish(row.get("active"))
        ],
        "team_id",
    )
    roster_sources = by_key(read_csv("data/asset_registry/wnba/athlete_sources.csv"), "team_id")
    catalog_rows = [
        row
        for row in read_csv("data/asset_registry/wnba/athlete_photo_catalog.csv")
        if clean(row.get("league")).upper() == "WNBA" and clean(row.get("asset_kind")) == "headshot"
    ]
    rows: List[Dict[str, str]] = []
    for row in sorted(catalog_rows, key=lambda item: (clean(item.get("team_id")), clean(item.get("athlete_name")))):
        team_id = clean(row.get("team_id"))
        team = teams.get(team_id, {})
        source = roster_sources.get(team_id, {})
        athlete_name = clean(row.get("athlete_name"))
        provider_player_id = clean(row.get("provider_player_id"))
        local_path = clean(row.get("local_asset_path"))
        marker_path = clean(row.get("approved_marker_path"))
        rows.append(
            {
                "athlete_id": clean(row.get("athlete_id")),
                "athlete_name": athlete_name,
                "team_id": team_id,
                "team_name": clean(team.get("team_name")) or team_id,
                "conference": clean(team.get("conference")),
                "local_headshot_path": local_path,
                "local_headshot_exists": str(project_path(local_path).exists()).lower() if local_path else "false",
                "approved_marker_path": marker_path,
                "approved_marker_exists": str(project_path(marker_path).exists()).lower() if marker_path else "false",
                "current_approval_status": clean(row.get("approval_status")) or clean(row.get("status")) or "manual_review_required",
                "identity_review_status": clean(row.get("identity_review_status")) or "manual_identity_review_required",
                "provider_player_id": provider_player_id,
                "official_roster_page_candidate": clean(source.get("roster_url")) or clean(row.get("source_url")),
                "official_player_profile_candidate": official_profile_url(provider_player_id, athlete_name),
                "official_roster_photo_candidate_url": clean(row.get("source_url")),
                "source_evidence": clean(row.get("source_evidence")),
                "crop_readiness_notes": clean(row.get("crop_readiness_notes")),
                "allowed_decisions": "approve_for_review_only_renderer_use|hold_identity|revise_asset|revise_source_metadata",
                "human_intake_file": "data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv",
                "team_contact_sheet_path": team_contact_sheet_path(team_id),
                "team_review_board_path": team_review_board_path(team_id),
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


def existing_intake_by_athlete() -> Dict[str, Mapping[str, str]]:
    return by_key(read_csv("data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv"), "athlete_id")


def intake_rows(rows: Iterable[Mapping[str, str]], existing: Mapping[str, Mapping[str, str]] | None = None) -> List[Dict[str, str]]:
    existing = existing or existing_intake_by_athlete()
    output: List[Dict[str, str]] = []
    for row in rows:
        prior = existing.get(clean(row.get("athlete_id")), {})
        output.append(
            {
                "athlete_id": clean(row.get("athlete_id")),
                "athlete_name": clean(row.get("athlete_name")),
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "local_headshot_path": clean(row.get("local_headshot_path")),
                "approved_marker_path": clean(row.get("approved_marker_path")),
                "provider_player_id": clean(row.get("provider_player_id")),
                "official_roster_page_candidate": clean(row.get("official_roster_page_candidate")),
                "official_player_profile_candidate": clean(row.get("official_player_profile_candidate")),
                "official_roster_photo_candidate_url": clean(row.get("official_roster_photo_candidate_url")),
                "current_approval_status": clean(row.get("current_approval_status")),
                "identity_review_status": clean(row.get("identity_review_status")),
                "allowed_decisions": clean(row.get("allowed_decisions")),
                "operator_decision": clean(prior.get("operator_decision")) or "operator_fill_required",
                "identity_verified": clean(prior.get("identity_verified")) or "operator_fill_required",
                "source_reviewed": clean(prior.get("source_reviewed")) or "operator_fill_required",
                "local_file_reviewed": clean(prior.get("local_file_reviewed")) or "operator_fill_required",
                "source_url_to_record": clean(prior.get("source_url_to_record")),
                "provider_player_id_verified": clean(prior.get("provider_player_id_verified")),
                "registry_action": clean(prior.get("registry_action")),
                "operator_notes": clean(prior.get("operator_notes")),
                "reviewed_by": clean(prior.get("reviewed_by")),
                "reviewed_at_local": clean(prior.get("reviewed_at_local")),
                "approval_scope": "review_only_renderer_athlete_photo_trust_manual_intake",
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
    if not value:
        return ""
    if text_width(draw, value, font) <= max_width:
        return value
    suffix = "..."
    while value and text_width(draw, value + suffix, font) > max_width:
        value = value[:-1]
    return (value.rstrip() + suffix) if value else suffix


def draw_card(sheet: Any, draw: Any, row: Mapping[str, str], x: int, y: int, card_w: int, card_h: int) -> None:
    font_name = load_font(20, bold=True)
    font_small = load_font(14)
    font_tiny = load_font(12)
    draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=10, fill=(255, 255, 255), outline=(212, 220, 228), width=2)
    local_path = project_path(row.get("local_headshot_path"))
    if local_path.exists() and Image is not None:
        try:
            headshot = fit_image(local_path, 116, 90)
            sheet.paste(headshot, (x + 16, y + 38), headshot)
        except Exception:
            draw.rectangle((x + 16, y + 38, x + 132, y + 128), fill=(236, 240, 244), outline=(180, 188, 196))
            draw.text((x + 26, y + 76), "render failed", fill=(130, 38, 38), font=font_tiny)
    else:
        draw.rectangle((x + 16, y + 38, x + 132, y + 128), fill=(236, 240, 244), outline=(180, 188, 196))
        draw.text((x + 34, y + 76), "missing local", fill=(130, 38, 38), font=font_tiny)

    text_x = x + 148
    text_w = card_w - 164
    draw.text((x + 16, y + 12), ellipsize(draw, clean(row.get("athlete_name")), font_name, card_w - 32), fill=(12, 20, 28), font=font_name)
    status = clean(row.get("identity_review_status")) or "manual_review_required"
    status_fill = (154, 99, 0) if "review" in status or "hold" in status else (18, 118, 86)
    draw.text((text_x, y + 42), ellipsize(draw, f"Status: {status}", font_small, text_w), fill=status_fill, font=font_small)
    draw.text((text_x, y + 64), ellipsize(draw, f"Provider: {clean(row.get('provider_player_id')) or 'missing'}", font_tiny, text_w), fill=(74, 83, 94), font=font_tiny)
    draw.text((text_x, y + 84), ellipsize(draw, f"Official: {clean(row.get('official_player_profile_candidate')) or clean(row.get('official_roster_page_candidate'))}", font_tiny, text_w), fill=(74, 83, 94), font=font_tiny)
    draw.text((text_x, y + 104), ellipsize(draw, f"Photo URL: {clean(row.get('official_roster_photo_candidate_url')) or 'missing'}", font_tiny, text_w), fill=(74, 83, 94), font=font_tiny)
    draw.text((x + 16, y + 144), ellipsize(draw, f"Local: {clean(row.get('local_headshot_path'))}", font_tiny, card_w - 32), fill=(74, 83, 94), font=font_tiny)
    draw.text((x + 16, y + 164), ellipsize(draw, f"Decision file: {clean(row.get('human_intake_file'))}", font_tiny, card_w - 32), fill=(74, 83, 94), font=font_tiny)


def make_team_contact_sheet(team_id: str, team_rows: List[Mapping[str, str]]) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    out_path = output_path(team_contact_sheet_path(team_id))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if Image is None or ImageDraw is None:
        warnings.append(f"{team_id}:pillow_unavailable_contact_sheet_not_created")
        return out_path.as_posix(), warnings
    cols = 2
    card_w, card_h = 620, 196
    margin = 28
    header_h = 86
    row_count = max(1, (len(team_rows) + cols - 1) // cols)
    width = margin * 2 + cols * card_w + 18
    height = margin * 2 + header_h + row_count * (card_h + 18)
    image = Image.new("RGB", (width, height), (246, 248, 250))
    draw = ImageDraw.Draw(image)
    font_title = load_font(32, bold=True)
    font_body = load_font(16)
    team_name = clean(team_rows[0].get("team_name")) if team_rows else team_id
    draw.text((margin, 20), f"{team_name} athlete photo review", fill=(12, 20, 28), font=font_title)
    draw.text((margin, 58), "Review-only: local headshots plus official roster/profile source candidates. No downloads or approvals.", fill=(74, 83, 94), font=font_body)
    for index, row in enumerate(team_rows):
        col = index % cols
        row_i = index // cols
        x = margin + col * (card_w + 18)
        y = margin + header_h + row_i * (card_h + 18)
        draw_card(image, draw, row, x, y, card_w, card_h)
    image.save(out_path)
    return out_path.as_posix(), warnings


def render_team_board(team_id: str, team_rows: List[Mapping[str, str]], sheet_path: str, generated_at: str) -> str:
    team_name = clean(team_rows[0].get("team_name")) if team_rows else team_id
    lines = [
        f"# {team_name} Athlete Photo Contact Sheet",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only board for human identity/source review. Official roster photo URLs are source candidates only; this generator does not download official photos, approve assets, move files, publish, or create a publish-ready lane.",
        "",
        f"![{team_name} athlete photo contact sheet]({Path(sheet_path).name})",
        "",
        "## Rows",
        "",
    ]
    for row in team_rows:
        lines.append(
            f"- {row.get('athlete_name')} | local={row.get('local_headshot_path')} | local_exists={row.get('local_headshot_exists')} | "
            f"identity={row.get('identity_review_status')} | approval={row.get('current_approval_status')} | "
            f"profile={row.get('official_player_profile_candidate') or 'missing'} | roster_photo_candidate={row.get('official_roster_photo_candidate_url') or 'missing'}"
        )
    return "\n".join(lines) + "\n"


def render_index(rows: List[Mapping[str, str]], team_outputs: Mapping[str, Mapping[str, str]], generated_at: str) -> str:
    teams = sorted(team_outputs)
    local_count = sum(1 for row in rows if clean(row.get("local_headshot_exists")) == "true")
    hold_count = sum(1 for row in rows if clean(row.get("identity_review_status")).startswith("hold_") or "recheck" in clean(row.get("identity_review_status")))
    lines = [
        "# WNBA Athlete Photo Contact Sheets",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only sweep board for WNBA athlete photos by team. Local headshots are shown in generated contact sheets; official roster/profile/photo URLs are source candidates only and are not downloaded by this generator.",
        "",
        "## Summary",
        "",
        f"- Athlete rows: `{len(rows)}`",
        f"- Teams: `{len(teams)}`",
        f"- Local headshots present: `{local_count}`",
        f"- Identity/source review rows: `{hold_count}`",
        "- Human-edited intake CSV: `data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv`",
        "- Allowed decisions: `approve_for_review_only_renderer_use|hold_identity|revise_asset|revise_source_metadata`",
        "- Guardrails: review_only=true; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false",
        "",
        "## Team Boards",
        "",
    ]
    for team_id in teams:
        info = team_outputs[team_id]
        lines.append(f"- {info.get('team_name')} | rows={info.get('rows')} | [board]({Path(info.get('board_path', '')).as_posix()}) | [contact sheet]({Path(info.get('sheet_path', '')).as_posix()})")
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_iso()
    rows = build_rows()
    team_outputs: Dict[str, Dict[str, str]] = {}
    warnings: List[str] = []
    by_team: Dict[str, List[Mapping[str, str]]] = {}
    for row in rows:
        by_team.setdefault(clean(row.get("team_id")), []).append(row)
    for team_id, team_rows in sorted(by_team.items()):
        sheet_path, sheet_warnings = make_team_contact_sheet(team_id, team_rows)
        warnings.extend(sheet_warnings)
        board_path = output_path(team_review_board_path(team_id))
        board_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(board_path, render_team_board(team_id, team_rows, sheet_path, generated_at))
        team_outputs[team_id] = {
            "team_id": team_id,
            "team_name": clean(team_rows[0].get("team_name")) if team_rows else team_id,
            "rows": str(len(team_rows)),
            "sheet_path": team_contact_sheet_path(team_id),
            "board_path": team_review_board_path(team_id),
        }
    write_csv(OUT_CSV, rows, CONTACT_FIELDS)
    write_csv(OUT_INTAKE, intake_rows(rows), INTAKE_FIELDS)
    write_text(OUT_INDEX, render_index(rows, team_outputs, generated_at))
    manifest = {
        "version": VERSION,
        "generated_at_utc": generated_at,
        "status": "contact_sheets_ready" if rows else "no_rows",
        "review_only": True,
        "athlete_rows": len(rows),
        "team_rows": len(team_outputs),
        "local_headshots_present": sum(1 for row in rows if clean(row.get("local_headshot_exists")) == "true"),
        "index": OUT_INDEX.as_posix(),
        "contact_sheet_data": OUT_CSV.as_posix(),
        "human_intake_csv": OUT_INTAKE.as_posix(),
        "team_outputs": list(team_outputs.values()),
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
    print(json.dumps({"version": VERSION, "status": manifest["status"], "athlete_rows": len(rows), "team_rows": len(team_outputs), "index": OUT_INDEX.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
