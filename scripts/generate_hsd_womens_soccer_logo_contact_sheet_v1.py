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


VERSION = "hsd-womens-soccer-logo-contact-sheet-v1-review-only"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUT_MD = output_path("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md")
OUT_CSV = output_path("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.csv")
OUT_PNG = output_path("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.png")
OUT_INTAKE = output_path("data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv")
OUT_JSON = output_path("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.json")

REGISTRY_ROOT = Path("data/asset_registry/womens_soccer")
REGISTRY_SCOPES = ["nwsl", "europe_top_flight"]

CONTACT_FIELDS = [
    "scope_id",
    "league_id",
    "league_name",
    "entity_type",
    "entity_id",
    "display_name",
    "country",
    "asset_slot",
    "local_logo_path",
    "logo_image_path",
    "logo_file_exists",
    "current_source_url",
    "official_source_candidate",
    "current_approval_status",
    "manual_review_status",
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
    "scope_id",
    "league_id",
    "entity_type",
    "entity_id",
    "display_name",
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

LEAGUE_SOURCE_KIND_PRIORITY = [
    "league_home",
    "league_about",
    "clubs_index",
    "teams_index",
    "logo_review_source",
]

TEAM_SOURCE_KIND_PRIORITY = [
    "logo_review_source",
    "team_site",
    "roster",
    "nwsl_team_detail",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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


def by_key(rows: Iterable[Mapping[str, str]], key: str) -> Dict[str, Mapping[str, str]]:
    return {clean(row.get(key)): row for row in rows if clean(row.get(key))}


def source_map(rows: Iterable[Mapping[str, str]]) -> Dict[Tuple[str, str], Dict[str, str]]:
    mapped: Dict[Tuple[str, str], Dict[str, str]] = {}
    for row in rows:
        mapped.setdefault((clean(row.get("entity_type")), clean(row.get("entity_id"))), {})[
            clean(row.get("source_kind"))
        ] = clean(row.get("source_url"))
    return mapped


def preferred_source(sources: Mapping[str, str], kinds: Iterable[str]) -> str:
    for kind in kinds:
        value = clean(sources.get(kind))
        if value:
            return value
    for value in sources.values():
        if clean(value):
            return clean(value)
    return ""


def approval_lookup(rows: Iterable[Mapping[str, str]]) -> Dict[Tuple[str, str, str], str]:
    output: Dict[Tuple[str, str, str], str] = {}
    for row in rows:
        output[
            (
                clean(row.get("entity_type")),
                clean(row.get("entity_id")),
                clean(row.get("approval_scope")),
            )
        ] = clean(row.get("approval_status"))
    return output


def slot_rows(scope: str) -> List[Mapping[str, str]]:
    rows = []
    for row in read_csv(REGISTRY_ROOT / scope / "asset_slots.csv"):
        entity_type = clean(row.get("entity_type"))
        asset_slot = clean(row.get("asset_slot"))
        if entity_type == "league" and asset_slot in {"league_mark", "federation_mark"}:
            rows.append(row)
        elif entity_type == "team" and asset_slot in {"primary_logo", "national_team_crest"}:
            rows.append(row)
    return rows


def entity_display(
    entity_type: str,
    entity_id: str,
    leagues: Mapping[str, Mapping[str, str]],
    teams: Mapping[str, Mapping[str, str]],
) -> Tuple[str, str]:
    if entity_type == "league":
        row = leagues.get(entity_id, {})
        return clean(row.get("league_name")) or entity_id, clean(row.get("country"))
    row = teams.get(entity_id, {})
    return clean(row.get("team_name")) or entity_id, clean(row.get("country") or row.get("city"))


def build_scope_rows(scope: str) -> List[Dict[str, str]]:
    leagues = by_key(read_csv(REGISTRY_ROOT / scope / "leagues.csv"), "league_id")
    teams = by_key(read_csv(REGISTRY_ROOT / scope / "teams.csv"), "team_id")
    sources = source_map(read_csv(REGISTRY_ROOT / scope / "source_urls.csv"))
    approvals = approval_lookup(read_csv(REGISTRY_ROOT / scope / "approval_status.csv"))
    rows: List[Dict[str, str]] = []
    for slot in slot_rows(scope):
        entity_type = clean(slot.get("entity_type"))
        entity_id = clean(slot.get("entity_id"))
        league_id = clean(slot.get("league_id")) or entity_id
        display_name, country = entity_display(entity_type, entity_id, leagues, teams)
        path = clean(slot.get("local_file_path")) or clean(slot.get("target_path"))
        source_kinds = LEAGUE_SOURCE_KIND_PRIORITY if entity_type == "league" else TEAM_SOURCE_KIND_PRIORITY
        current_source = preferred_source(sources.get((entity_type, entity_id), {}), source_kinds)
        scope_name = "league_mark" if entity_type == "league" else "team_logo"
        rows.append(
            {
                "scope_id": scope,
                "league_id": league_id,
                "league_name": clean(leagues.get(league_id, {}).get("league_name")) or league_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "display_name": display_name,
                "country": country,
                "asset_slot": clean(slot.get("asset_slot")),
                "local_logo_path": path,
                "logo_image_path": path,
                "logo_file_exists": str(project_path(path).exists()).lower() if path else "false",
                "current_source_url": current_source,
                "official_source_candidate": current_source,
                "current_approval_status": approvals.get((entity_type, entity_id, scope_name), clean(slot.get("approval_status")) or "not_approved"),
                "manual_review_status": "review_required",
                "operator_action": "manual_logo_or_mark_review_required",
                "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                "human_intake_file": "data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv",
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


def build_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for scope in REGISTRY_SCOPES:
        rows.extend(build_scope_rows(scope))
    return rows


def existing_intake_by_key() -> Dict[Tuple[str, str, str], Mapping[str, str]]:
    return {
        (clean(row.get("scope_id")), clean(row.get("entity_type")), clean(row.get("entity_id"))): row
        for row in read_csv("data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv")
    }


def intake_rows(
    rows: Iterable[Mapping[str, str]],
    existing_by_key: Mapping[Tuple[str, str, str], Mapping[str, str]] | None = None,
) -> List[Dict[str, str]]:
    existing_by_key = existing_by_key or existing_intake_by_key()
    output: List[Dict[str, str]] = []
    for row in rows:
        existing = existing_by_key.get(
            (clean(row.get("scope_id")), clean(row.get("entity_type")), clean(row.get("entity_id"))),
            {},
        )
        output.append(
            {
                "scope_id": clean(row.get("scope_id")),
                "league_id": clean(row.get("league_id")),
                "entity_type": clean(row.get("entity_type")),
                "entity_id": clean(row.get("entity_id")),
                "display_name": clean(row.get("display_name")),
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
                "approval_scope": "review_only_renderer_womens_soccer_logo_trust_manual_intake",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return output


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

    cols = 4
    card_w, card_h = 370, 300
    margin = 32
    header_h = 96
    rows_count = max(1, (len(rows) + cols - 1) // cols)
    width = margin * 2 + cols * card_w
    height = margin * 2 + header_h + rows_count * card_h
    image = Image.new("RGB", (width, height), (247, 248, 246))
    draw = ImageDraw.Draw(image)
    font_title = load_font(30, bold=True)
    font_body = load_font(18)
    font_small = load_font(14)
    draw.text((margin, 24), "Women's Soccer Logo and Mark Review Contact Sheet", fill=(17, 24, 32), font=font_title)
    draw.text((margin, 62), "Review-only board. Human decisions belong in womens_soccer_logo_review_intake.csv.", fill=(70, 80, 88), font=font_body)

    for index, row in enumerate(rows):
        col = index % cols
        row_i = index // cols
        x = margin + col * card_w
        y = margin + header_h + row_i * card_h
        draw.rounded_rectangle((x + 8, y + 8, x + card_w - 14, y + card_h - 14), radius=10, fill=(255, 255, 255), outline=(215, 222, 224), width=2)
        logo_path = project_path(row.get("logo_image_path"))
        if logo_path.exists():
            try:
                logo = fit_image(logo_path, 198, 126)
                image.paste(logo, (x + 84, y + 24), logo)
            except Exception as exc:
                warnings.append(f"{row.get('scope_id')}:{row.get('entity_id')}:logo_render_failed:{exc}")
                draw.text((x + 102, y + 74), "logo render failed", fill=(138, 43, 43), font=font_small)
        else:
            draw.rectangle((x + 96, y + 42, x + 274, y + 132), fill=(237, 240, 241), outline=(180, 188, 191))
            draw.text((x + 124, y + 76), "asset not local", fill=(138, 75, 20), font=font_small)
        status = clean(row.get("current_approval_status")) or "review"
        text_max = card_w - 50
        draw.text((x + 24, y + 166), ellipsize(draw, clean(row.get("display_name")), font_body, text_max), fill=(17, 24, 32), font=font_body)
        draw.text((x + 24, y + 194), f"{clean(row.get('scope_id'))} | {clean(row.get('entity_type'))}", fill=(70, 80, 88), font=font_small)
        draw.text((x + 24, y + 218), f"Status: {status}", fill=(150, 94, 0), font=font_small)
        draw.text((x + 24, y + 240), ellipsize(draw, f"Path: {clean(row.get('local_logo_path'))}", font_small, text_max), fill=(70, 80, 88), font=font_small)
        draw.text((x + 24, y + 262), ellipsize(draw, f"Source: {clean(row.get('official_source_candidate'))}", font_small, text_max), fill=(70, 80, 88), font=font_small)

    image.save(out_path)
    return out_path.as_posix(), warnings


def render_markdown(rows: List[Mapping[str, str]], png_path: str, generated_at: str) -> str:
    league_rows = sum(1 for row in rows if clean(row.get("entity_type")) == "league")
    team_rows = sum(1 for row in rows if clean(row.get("entity_type")) == "team")
    scope_counts: Dict[str, int] = {}
    for row in rows:
        scope = clean(row.get("scope_id")) or "unknown"
        scope_counts[scope] = scope_counts.get(scope, 0) + 1
    lines = [
        "# Women's Soccer Logo Contact Sheet",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only sweep board for NWSL team logos plus a European top-flight source-candidate pilot. This file does not approve assets, download files, move files, publish, or create a publish-ready lane.",
        "",
        f"![Women's soccer logo contact sheet]({Path(png_path).name})",
        "",
        "## Summary",
        "",
        f"- Rows: `{len(rows)}`",
        f"- League mark rows: `{league_rows}`",
        f"- Team logo rows: `{team_rows}`",
        "- Human-edited intake CSV: `data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv`",
        "- Allowed decisions: `approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata`",
        "- Guardrails: review_only=true; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false",
        "",
        "## Scope Counts",
        "",
    ]
    for scope, count in sorted(scope_counts.items()):
        lines.append(f"- `{scope}`: `{count}`")
    lines += ["", "## Rows", ""]
    for row in rows:
        lines.append(
            f"- {row.get('display_name')} | scope={row.get('scope_id')} | type={row.get('entity_type')} | "
            f"status={row.get('current_approval_status')} | local={row.get('local_logo_path')} | "
            f"source_candidate={row.get('official_source_candidate') or 'missing'} | action={row.get('operator_action')}"
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
        "row_count": len(rows),
        "league_mark_rows": sum(1 for row in rows if clean(row.get("entity_type")) == "league"),
        "team_logo_rows": sum(1 for row in rows if clean(row.get("entity_type")) == "team"),
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
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "rows": len(rows),
                "contact_sheet": OUT_PNG.as_posix(),
                "intake": OUT_INTAKE.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
