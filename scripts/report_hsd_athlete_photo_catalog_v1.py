from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_csv as write_run_csv, write_json

ROOT = Path("data/asset_registry/wnba")
ATHLETES = ROOT / "athletes.csv"
ATHLETE_IMAGES = ROOT / "athlete_images.csv"
APPROVED_ASSETS = ROOT / "athlete_image_approved_assets.csv"
MATCH_REVIEW = ROOT / "athlete_image_match_review.csv"
TEMPLATE_DOC_ROOT = Path("assets/graphics/v4/approved/source_docs")

OUT_CSV = "data/asset_registry/wnba/athlete_photo_catalog.csv"
OUT_JSON = "data/asset_registry/wnba/athlete_photo_catalog.json"
OUT_MD = "data/asset_registry/wnba/athlete_photo_catalog.md"

VERSION = "hsd-athlete-photo-catalog-v1-review-only"
CATALOG_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "league",
    "provider_player_id",
    "asset_kind",
    "local_asset_path",
    "file_exists",
    "approved_marker_path",
    "approved_marker_exists",
    "status",
    "source_evidence",
    "crop_readiness_notes",
    "render_template_uses",
    "review_only_policy",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def boolish(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "approved"}


def image_size_note(path: Path) -> str:
    if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return ""
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            width, height = image.size
        if width >= 260 and height >= 190:
            return f"image_size={width}x{height}; meets_headshot_floor"
        return f"image_size={width}x{height}; below_headshot_floor_review_crop"
    except Exception:
        return "image_size_unverified"


def template_label(path: Path, text: str, slot: str) -> str:
    parts = [part for part in path.with_suffix("").parts if part not in {".", "assets", "graphics", "v4", "approved", "source_docs"}]
    label = "/".join(parts[-3:]) if parts else path.stem
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = clean(title_match.group(1)) if title_match else label
    return f"{title} ({slot})"


def discover_render_template_uses(template_root: Path = TEMPLATE_DOC_ROOT) -> List[str]:
    if not template_root.exists():
        return ["approved_player_photo_slot", "approved_image_slot"]
    uses: List[str] = []
    seen = set()
    for path in sorted(template_root.rglob("*")):
        if path.suffix.lower() not in {".md", ".json"} or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        low = text.lower()
        slots: List[str] = []
        if "approved_player_photo_slot" in low or "approved player photo" in low:
            slots.append("approved_player_photo_slot")
        if "approved image slot" in low or "approved_image_slot" in low:
            slots.append("approved_image_slot")
        for slot in slots:
            label = template_label(path, text, slot)
            if label not in seen:
                seen.add(label)
                uses.append(label)
    return uses or ["approved_player_photo_slot", "approved_image_slot"]


def by_key(rows: Iterable[Mapping[str, str]], *fields: str) -> Dict[Tuple[str, ...], Mapping[str, str]]:
    out: Dict[Tuple[str, ...], Mapping[str, str]] = {}
    for row in rows:
        key = tuple(clean(row.get(field)) for field in fields)
        if all(key):
            out[key] = row
    return out


def matched_approved_registry_row(
    image_row: Mapping[str, str],
    approved_by_athlete: Mapping[Tuple[str, ...], Mapping[str, str]],
) -> Mapping[str, str]:
    athlete_id = clean(image_row.get("athlete_id"))
    image_path = clean(image_row.get("file_path"))
    approved = approved_by_athlete.get((athlete_id,), {})
    if approved and clean(approved.get("approved_file")) == image_path:
        return approved
    return {}


def manual_source_warnings(approved: Mapping[str, str]) -> List[str]:
    if not approved:
        return ["approved_assets_registry_missing_manual_review_required"]

    warnings: List[str] = []
    decision_source = clean(approved.get("decision_source")).lower()
    if not decision_source or decision_source == "unknown":
        warnings.append("unknown_decision_source_manual_review_required")
    elif decision_source == "default" or decision_source.startswith("default_"):
        warnings.append("default_decision_source_manual_recheck_required")

    source_file = clean(approved.get("source_file")).lower()
    if not source_file or source_file == "unknown":
        warnings.append("source_file_missing_manual_review_required")

    approved_at = clean(approved.get("approved_at_utc")).lower()
    if not approved_at or approved_at == "unknown":
        warnings.append("approved_timestamp_missing_manual_review_required")

    return warnings


def source_evidence_for(
    image_row: Mapping[str, str],
    approved_by_athlete: Mapping[Tuple[str, ...], Mapping[str, str]],
    review_by_athlete: Mapping[Tuple[str, ...], Mapping[str, str]],
) -> str:
    athlete_id = clean(image_row.get("athlete_id"))
    approved = matched_approved_registry_row(image_row, approved_by_athlete)
    if approved:
        parts = [
            "approved_assets_registry",
            f"decision_source={clean(approved.get('decision_source')) or 'unknown'}",
            f"source_file={clean(approved.get('source_file')) or 'unknown'}",
            f"approved_at_utc={clean(approved.get('approved_at_utc')) or 'unknown'}",
        ]
        return "; ".join(parts)
    review = review_by_athlete.get((athlete_id,)) if clean(image_row.get("image_type")) == "headshot" else None
    if review:
        parts = [
            "match_review_registry",
            f"status={clean(review.get('status')) or 'unknown'}",
            f"image_url={clean(review.get('image_url')) or 'unknown'}",
            f"confidence={clean(review.get('confidence')) or 'unknown'}",
        ]
        return "; ".join(parts)
    note = clean(image_row.get("source_note")) or "unknown"
    return f"athlete_images_registry; source_note={note}"


def status_for(path: Path, marker: Path, registry_approved: bool) -> str:
    file_exists = path.exists()
    marker_exists = marker.exists()
    if file_exists and marker_exists and registry_approved:
        return "approved"
    if file_exists:
        return "unapproved"
    return "missing"


def crop_notes(path: Path, asset_kind: str, status: str, registry_approved: bool, marker_exists: bool) -> str:
    notes: List[str] = []
    if status == "approved":
        notes.append("approved_marker_present")
    elif status == "unapproved":
        notes.append("file_present_but_not_public_use")
    else:
        notes.append("asset_file_missing")
    if registry_approved and not marker_exists:
        notes.append("registry_says_approved_but_marker_missing")
    if asset_kind == "cutout":
        notes.append("cutout_slot_requires_manual_crop_review")
    else:
        notes.append("headshot_slot_requires_identity_and_crop_review")
    size_note = image_size_note(path)
    if size_note:
        notes.append(size_note)
    return "; ".join(notes)


def render_template_uses_for(status: str, approved_templates: str, source_warnings: List[str]) -> str:
    if status == "approved" and not source_warnings:
        return approved_templates
    if status == "approved" and source_warnings:
        return "review_only_manual_source_recheck_required: " + "; ".join(source_warnings)
    return "review_only_not_renderable_until_approved"


def build_catalog(
    athlete_rows: List[Mapping[str, str]],
    image_rows: List[Mapping[str, str]],
    approved_rows: List[Mapping[str, str]],
    review_rows: List[Mapping[str, str]],
    template_uses: List[str],
) -> List[Dict[str, str]]:
    athletes = by_key(athlete_rows, "athlete_id")
    approved_by_athlete = by_key(approved_rows, "athlete_id")
    review_by_athlete = by_key(review_rows, "athlete_id")
    approved_templates = "; ".join(template_uses)
    rows: List[Dict[str, str]] = []
    for image in sorted(image_rows, key=lambda row: (clean(row.get("team_id")), clean(row.get("display_name")), clean(row.get("image_type")))):
        athlete_id = clean(image.get("athlete_id"))
        athlete = athletes.get((athlete_id,), {})
        path = Path(clean(image.get("file_path")))
        marker = Path(path.as_posix() + ".approved")
        registry_approved = boolish(image.get("approved"))
        marker_exists = marker.exists()
        status = status_for(path, marker, registry_approved)
        asset_kind = clean(image.get("image_type")) or "photo"
        approved_registry_row = matched_approved_registry_row(image, approved_by_athlete)
        source_warnings = manual_source_warnings(approved_registry_row) if status == "approved" else []
        notes = crop_notes(path, asset_kind, status, registry_approved, marker_exists)
        if source_warnings:
            notes = "; ".join([notes, *source_warnings])
        rows.append({
            "athlete_id": athlete_id,
            "athlete_name": clean(image.get("display_name")) or clean(athlete.get("display_name")),
            "team_id": clean(image.get("team_id")) or clean(athlete.get("team_id")),
            "league": clean(athlete.get("league")) or "WNBA",
            "provider_player_id": clean(image.get("provider_player_id")) or clean(athlete.get("provider_player_id")),
            "asset_kind": asset_kind,
            "local_asset_path": path.as_posix(),
            "file_exists": "true" if path.exists() else "false",
            "approved_marker_path": marker.as_posix(),
            "approved_marker_exists": "true" if marker_exists else "false",
            "status": status,
            "source_evidence": source_evidence_for(image, approved_by_athlete, review_by_athlete),
            "crop_readiness_notes": notes,
            "render_template_uses": render_template_uses_for(status, approved_templates, source_warnings),
            "review_only_policy": "catalog_only_no_auto_approval_no_file_movement",
        })
    return rows


def summarize(rows: List[Mapping[str, str]], template_uses: List[str], out_csv: Path, out_json: Path, out_md: Path) -> Dict[str, Any]:
    by_status: Dict[str, int] = {}
    by_kind: Dict[str, Dict[str, int]] = {}
    for row in rows:
        status = clean(row.get("status"))
        kind = clean(row.get("asset_kind"))
        by_status[status] = by_status.get(status, 0) + 1
        by_kind.setdefault(kind, {})
        by_kind[kind][status] = by_kind[kind].get(status, 0) + 1
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "catalog_csv": out_csv.as_posix(),
        "catalog_json": out_json.as_posix(),
        "catalog_md": out_md.as_posix(),
        "rows": len(rows),
        "status_counts": dict(sorted(by_status.items())),
        "asset_kind_status_counts": by_kind,
        "render_template_uses_discovered": template_uses,
        "policy": "This catalog reports existing athlete photo readiness only. It does not approve, copy, move, fetch, publish, or auto-enable athlete photos.",
    }


def write_markdown(path: Path, report: Mapping[str, Any], rows: List[Mapping[str, str]]) -> None:
    counts = report.get("status_counts") or {}
    approved = [row for row in rows if row.get("status") == "approved"]
    manual_source_recheck = [
        row for row in approved if clean(row.get("render_template_uses")).startswith("review_only_manual_source_recheck_required")
    ]
    needs_review = [row for row in rows if row.get("status") != "approved"]
    lines = [
        "# HSD Athlete Photo Catalog v1",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        "",
        "## Policy",
        "",
        "- Review-only catalog. No athlete photo was approved, moved, fetched, published, or auto-enabled by this report.",
        "- Public-use readiness requires a local asset file and its sibling `.approved` marker.",
        "- Unapproved and missing rows must stay out of renderer photo slots until a human approval workflow updates the canonical files.",
        "",
        "## Counts",
        "",
        f"- rows: {report.get('rows')}",
        f"- approved: {counts.get('approved', 0)}",
        f"- unapproved: {counts.get('unapproved', 0)}",
        f"- missing: {counts.get('missing', 0)}",
        f"- approved rows requiring manual source recheck: {len(manual_source_recheck)}",
        "",
        "## Template Slots Found",
        "",
    ]
    for item in report.get("render_template_uses_discovered") or []:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Registry-Approved Headshot/Cutout Rows",
        "",
    ]
    for row in approved[:40]:
        lines.append(
            f"- {row.get('athlete_name')} | {row.get('team_id')} | {row.get('asset_kind')} | "
            f"`{row.get('local_asset_path')}` | {row.get('render_template_uses')}"
        )
    if len(approved) > 40:
        lines.append(f"- ...and {len(approved) - 40} more approved rows in the CSV.")
    lines += [
        "",
        "## Manual Source Recheck Sample",
        "",
    ]
    if manual_source_recheck:
        for row in manual_source_recheck[:40]:
            lines.append(
                f"- {row.get('athlete_name')} | {row.get('team_id')} | {row.get('asset_kind')} | "
                f"`{row.get('local_asset_path')}` | {row.get('render_template_uses')}"
            )
        if len(manual_source_recheck) > 40:
            lines.append(f"- ...and {len(manual_source_recheck) - 40} more source-recheck rows in the CSV.")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Needs Review Sample",
        "",
    ]
    for row in needs_review[:40]:
        lines.append(f"- {row.get('status')} | {row.get('athlete_name')} | {row.get('team_id')} | {row.get('asset_kind')} | `{row.get('local_asset_path')}`")
    if len(needs_review) > 40:
        lines.append(f"- ...and {len(needs_review) - 40} more review rows in the CSV.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    out_csv = output_path(OUT_CSV)
    out_json = output_path(OUT_JSON)
    out_md = output_path(OUT_MD)
    template_uses = discover_render_template_uses()
    rows = build_catalog(
        read_csv(ATHLETES),
        read_csv(ATHLETE_IMAGES),
        read_csv(APPROVED_ASSETS),
        read_csv(MATCH_REVIEW),
        template_uses,
    )
    report = summarize(rows, template_uses, out_csv, out_json, out_md)
    write_run_csv(OUT_CSV, rows, CATALOG_FIELDS)
    write_json(OUT_JSON, {"report": report, "rows": rows}, indent=2)
    write_markdown(out_md, report, rows)
    print(json.dumps({key: report[key] for key in ["version", "rows", "status_counts", "catalog_csv", "catalog_md"]}, indent=2))


if __name__ == "__main__":
    main()
