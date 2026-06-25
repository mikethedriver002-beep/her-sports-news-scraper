from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hsd_run_io import output_path, write_csv, write_json, write_text

import report_hsd_athlete_photo_catalog_v1 as photo_catalog

try:
    from PIL import Image, ImageDraw, ImageFont, ImageStat
except Exception:  # pragma: no cover - runtime report captures missing image stack
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageStat = None


VERSION = "hsd-athlete-photo-onboarding-v1-review-only"
OUT_DIR = output_path("athlete_photo_onboarding")
VARIANT_DIR = OUT_DIR / "variants"
SHEET_DIR = OUT_DIR / "contact_sheets"
OUT_REPORT = OUT_DIR / "athlete_photo_onboarding_report.md"
OUT_MANIFEST = OUT_DIR / "athlete_photo_onboarding_manifest.json"
OUT_METADATA_CSV = OUT_DIR / "athlete_photo_onboarding_metadata.csv"
OUT_METADATA_JSON = OUT_DIR / "athlete_photo_onboarding_metadata.json"
OUT_DECISION_TEMPLATE = OUT_DIR / "athlete_photo_onboarding_decision_template.csv"
OUT_CONTACT_INDEX = OUT_DIR / "athlete_photo_contact_sheet_index.md"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_ROWS = int(os.environ.get("HSD_ATHLETE_PHOTO_ONBOARDING_MAX", "0") or "0")

VARIANT_SPECS = [
    ("photo_first_feed", 380, 518, 0.18, "IG feed/story score-card photo stage"),
    ("photo_first_story", 382, 638, 0.16, "IG Story taller photo-first stage"),
    ("compact_square", 220, 220, 0.22, "Square/compact player chip"),
]

METADATA_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "source_headshot_path",
    "source_approval_marker_path",
    "source_approved_at_utc",
    "source_evidence",
    "feed_variant_path",
    "story_variant_path",
    "square_variant_path",
    "recommended_review_variant_path",
    "variant_status",
    "crop_readiness_score",
    "crop_readiness_notes",
    "contact_sheet_path",
    "renderer_review_candidate",
    "approval_scope",
    "review_only_policy",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

DECISION_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "source_headshot_path",
    "contact_sheet_path",
    "recommended_review_variant_path",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "crop_choice",
    "operator_notes",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_slug(value: Any) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", clean(value).lower())).strip("_") or "unknown"


def project_path(raw: Any) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def relative_or_absolute(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        return path.as_posix()


def load_font(size: int) -> Any:
    if ImageFont is None:
        return None
    for raw in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        path = Path(raw)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def source_rows() -> List[Dict[str, str]]:
    rows = photo_catalog.build_catalog(
        photo_catalog.read_csv(photo_catalog.ATHLETES),
        photo_catalog.read_csv(photo_catalog.ATHLETE_IMAGES),
        photo_catalog.read_csv(photo_catalog.APPROVED_ASSETS),
        photo_catalog.read_csv(photo_catalog.MATCH_REVIEW),
        photo_catalog.discover_render_template_uses(),
    )
    approved = [
        row
        for row in rows
        if row.get("status") == "approved"
        and row.get("asset_kind") == "headshot"
        and project_path(row.get("local_asset_path")).exists()
    ]
    if MAX_ROWS > 0:
        return approved[:MAX_ROWS]
    return approved


def fit_crop(path: Path, target_w: int, target_h: int, vertical_bias: float) -> Any:
    image = Image.open(path).convert("RGBA")
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    scale = max(target_w / max(1, image.width), target_h / max(1, image.height))
    resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
    left = max(0, min(resized.width - target_w, (resized.width - target_w) // 2))
    top = max(0, min(resized.height - target_h, int((resized.height - target_h) * vertical_bias)))
    cropped = resized.crop((left, top, left + target_w, top + target_h))
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    canvas.alpha_composite(cropped, (0, 0))
    return canvas


def image_signal(path: Path) -> Dict[str, Any]:
    if Image is None or ImageStat is None or not path.exists():
        return {"status": "image_stack_unavailable", "score": 0, "notes": "PIL unavailable or file missing"}
    try:
        image = Image.open(path).convert("L")
        stat = ImageStat.Stat(image)
        histogram = image.histogram()
        total = max(1, sum(histogram))
        bright = sum(histogram[170:]) / total
        dark = sum(histogram[:36]) / total
        variance = float(stat.var[0]) if stat.var else 0.0
        score = 0
        score += 35 if image.width >= 220 and image.height >= 220 else 10
        score += 35 if variance >= 900 else int(min(34, variance / 900 * 35))
        score += 15 if bright >= 0.02 else int(min(14, bright / 0.02 * 15))
        score += 15 if dark <= 0.92 else 6
        notes = f"size={image.width}x{image.height}; variance={variance:.1f}; bright={bright:.3f}; dark={dark:.3f}"
        return {"status": "measured", "score": min(100, score), "notes": notes}
    except Exception as exc:
        return {"status": "image_signal_failed", "score": 0, "notes": f"{type(exc).__name__}: {exc}"}


def variant_paths(row: Mapping[str, str]) -> Dict[str, Path]:
    athlete_id = safe_slug(row.get("athlete_id"))
    team_id = safe_slug(row.get("team_id"))
    return {
        variant_id: VARIANT_DIR / team_id / f"{athlete_id}__{variant_id}.png"
        for variant_id, *_ in VARIANT_SPECS
    }


def build_variants(row: Mapping[str, str]) -> Tuple[Dict[str, str], Dict[str, Any]]:
    source = project_path(row.get("local_asset_path"))
    paths = variant_paths(row)
    if Image is None:
        return {}, {"score": 0, "notes": "PIL unavailable; variants not generated"}
    signals: List[Dict[str, Any]] = []
    for variant_id, width, height, bias, _label in VARIANT_SPECS:
        out = paths[variant_id]
        out.parent.mkdir(parents=True, exist_ok=True)
        fit_crop(source, width, height, bias).save(out)
        signals.append(image_signal(out))
    score = min([int(item.get("score", 0)) for item in signals] or [0])
    notes = "; ".join(clean(item.get("notes")) for item in signals if item.get("notes"))
    return {variant_id: path.as_posix() for variant_id, path in paths.items()}, {"score": score, "notes": notes}


def draw_contact_cell(sheet: Any, draw: Any, row: Mapping[str, str], metadata: Mapping[str, str], x: int, y: int, cell_w: int, cell_h: int) -> None:
    title_font = load_font(18)
    small_font = load_font(12)
    draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), fill=(248, 250, 252), outline=(207, 213, 224), width=2)
    draw.rectangle((x, y, x + cell_w - 1, y + 34), fill=(7, 13, 25))
    draw.text((x + 12, y + 9), clean(row.get("athlete_name"))[:28], fill=(255, 255, 255), font=small_font)
    draw.text((x + cell_w - 112, y + 9), clean(row.get("team_id"))[:14], fill=(247, 203, 84), font=small_font)
    preview_paths = [
        ("SRC", project_path(row.get("local_asset_path"))),
        ("FEED", Path(clean(metadata.get("feed_variant_path")))),
        ("STORY", Path(clean(metadata.get("story_variant_path")))),
        ("SQ", Path(clean(metadata.get("square_variant_path")))),
    ]
    thumb_w, thumb_h = 92, 120
    for idx, (label, path) in enumerate(preview_paths):
        px = x + 14 + idx * 102
        py = y + 50
        draw.rectangle((px, py, px + thumb_w, py + thumb_h), fill=(3, 6, 12), outline=(148, 163, 184), width=1)
        if path.exists():
            try:
                image = Image.open(path).convert("RGBA")
                image.thumbnail((thumb_w - 8, thumb_h - 22), Image.Resampling.LANCZOS)
                sheet.alpha_composite(image, (px + (thumb_w - image.width) // 2, py + 8))
            except Exception:
                draw.text((px + 10, py + 45), "ERR", fill=(203, 49, 65), font=title_font)
        else:
            draw.text((px + 10, py + 45), "MISS", fill=(203, 49, 65), font=small_font)
        draw.text((px + 8, py + thumb_h - 18), label, fill=(226, 232, 240), font=small_font)
    draw.text((x + 14, y + 184), f"score {metadata.get('crop_readiness_score')} / {metadata.get('variant_status')}", fill=(15, 23, 42), font=small_font)
    draw.text((x + 14, y + 204), "review-only derivative; source approval marker required", fill=(71, 85, 105), font=small_font)


def write_contact_sheets(rows: List[Mapping[str, str]], metadata_by_athlete: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    if Image is None or ImageDraw is None:
        return {}
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    sheets: Dict[str, str] = {}
    by_team: Dict[str, List[Mapping[str, str]]] = {}
    for row in rows:
        by_team.setdefault(clean(row.get("team_id")) or "unknown", []).append(row)
    cell_w, cell_h, cols = 430, 242, 2
    for team_id, team_rows in sorted(by_team.items()):
        page_rows = (len(team_rows) + cols - 1) // cols
        sheet = Image.new("RGBA", (cell_w * cols, max(1, page_rows) * cell_h), (255, 255, 255, 255))
        draw = ImageDraw.Draw(sheet, "RGBA")
        for idx, row in enumerate(team_rows):
            x = (idx % cols) * cell_w
            y = (idx // cols) * cell_h
            draw_contact_cell(sheet, draw, row, metadata_by_athlete.get(clean(row.get("athlete_id")), {}), x, y, cell_w, cell_h)
        out = SHEET_DIR / f"{safe_slug(team_id)}_contact_sheet.jpg"
        sheet.convert("RGB").save(out, quality=90)
        sheets[team_id] = out.as_posix()
    return sheets


def build_metadata(rows: List[Mapping[str, str]]) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    metadata_rows: List[Dict[str, str]] = []
    for row in rows:
        paths, signal = build_variants(row)
        marker = project_path(row.get("approved_marker_path"))
        marker_payload = {}
        if marker.exists():
            try:
                marker_payload = json.loads(marker.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                marker_payload = {}
        score = int(signal.get("score", 0))
        status = "review_variant_ready" if score >= 70 and paths else "review_variant_needs_crop_review"
        metadata_rows.append(
            {
                "athlete_id": clean(row.get("athlete_id")),
                "athlete_name": clean(row.get("athlete_name")),
                "team_id": clean(row.get("team_id")),
                "source_headshot_path": clean(row.get("local_asset_path")),
                "source_approval_marker_path": clean(row.get("approved_marker_path")),
                "source_approved_at_utc": clean(marker_payload.get("approved_at_utc")),
                "source_evidence": clean(row.get("source_evidence")),
                "feed_variant_path": paths.get("photo_first_feed", ""),
                "story_variant_path": paths.get("photo_first_story", ""),
                "square_variant_path": paths.get("compact_square", ""),
                "recommended_review_variant_path": paths.get("photo_first_feed", ""),
                "variant_status": status,
                "crop_readiness_score": str(score),
                "crop_readiness_notes": clean(signal.get("notes")),
                "contact_sheet_path": "",
                "renderer_review_candidate": "true" if status == "review_variant_ready" else "false",
                "approval_scope": "review_only_derivative_from_approved_headshot",
                "review_only_policy": "derived_variant_does_not_approve_move_publish_or_mark_publish_ready",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    sheets = write_contact_sheets(rows, {row["athlete_id"]: row for row in metadata_rows})
    for item in metadata_rows:
        item["contact_sheet_path"] = sheets.get(clean(item.get("team_id")), "")
    return metadata_rows, sheets


def decision_rows(metadata_rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in metadata_rows:
        rows.append(
            {
                "athlete_id": clean(row.get("athlete_id")),
                "athlete_name": clean(row.get("athlete_name")),
                "team_id": clean(row.get("team_id")),
                "source_headshot_path": clean(row.get("source_headshot_path")),
                "contact_sheet_path": clean(row.get("contact_sheet_path")),
                "recommended_review_variant_path": clean(row.get("recommended_review_variant_path")),
                "allowed_decisions": "approve_variant_for_review_drafts|hold|revise_crop",
                "operator_decision": "",
                "identity_verified": "",
                "crop_choice": "",
                "operator_notes": "",
                "approval_scope": "review_only_derivative_from_approved_headshot",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    return rows


def manifest(metadata_rows: List[Mapping[str, str]], sheets: Mapping[str, str]) -> Dict[str, Any]:
    ready = sum(1 for row in metadata_rows if row.get("variant_status") == "review_variant_ready")
    needs_review = len(metadata_rows) - ready
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "review_only_onboarding_ready" if metadata_rows else "no_approved_headshots_found",
        "review_only": True,
        "source_rows": len(metadata_rows),
        "review_variant_ready": ready,
        "review_variant_needs_crop_review": needs_review,
        "contact_sheets": len(sheets),
        "metadata_csv": OUT_METADATA_CSV.as_posix(),
        "metadata_json": OUT_METADATA_JSON.as_posix(),
        "decision_template": OUT_DECISION_TEMPLATE.as_posix(),
        "contact_sheet_index": OUT_CONTACT_INDEX.as_posix(),
        "policy": {
            "paid_apis": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "canonical_headshots_unchanged": True,
        },
    }


def write_reports(metadata_rows: List[Dict[str, str]], sheets: Mapping[str, str], report: Mapping[str, Any]) -> None:
    by_team: Dict[str, int] = {}
    for row in metadata_rows:
        by_team[clean(row.get("team_id"))] = by_team.get(clean(row.get("team_id")), 0) + 1
    lines = [
        "# HSD Athlete Photo Onboarding v1",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        "",
        "## Policy",
        "",
        "- Review-only onboarding packet.",
        "- Uses only already-approved local headshots as source material.",
        "- Crop variants are derivative review assets; they do not approve, move, publish, or create a publish-ready lane.",
        "- Human review must confirm identity, crop, and source marker before any future production use.",
        "",
        "## Counts",
        "",
        f"- approved source headshots processed: {report.get('source_rows')}",
        f"- review variants ready: {report.get('review_variant_ready')}",
        f"- variants needing crop review: {report.get('review_variant_needs_crop_review')}",
        f"- contact sheets: {report.get('contact_sheets')}",
        "",
        "## Open Next",
        "",
        f"- Metadata CSV: `{OUT_METADATA_CSV.as_posix()}`",
        f"- Decision template: `{OUT_DECISION_TEMPLATE.as_posix()}`",
        f"- Contact sheet index: `{OUT_CONTACT_INDEX.as_posix()}`",
        "",
        "## Team Sheets",
        "",
    ]
    for team_id, path in sorted(sheets.items()):
        lines.append(f"- `{team_id}` ({by_team.get(team_id, 0)} athletes): `{path}`")
    write_text(OUT_REPORT, "\n".join(lines) + "\n")

    index_lines = [
        "# Athlete Photo Contact Sheet Index",
        "",
        "Open each contact sheet and verify identity/crop by eye before filling the decision template.",
        "",
    ]
    for team_id, path in sorted(sheets.items()):
        index_lines.append(f"- `{team_id}`: `{path}`")
    write_text(OUT_CONTACT_INDEX, "\n".join(index_lines) + "\n")


def metadata_json_payload(report: Mapping[str, Any], rows: List[Mapping[str, str]], sheets: Mapping[str, str]) -> Dict[str, Any]:
    return {
        "report": report,
        "sheets": sheets,
        "athletes": {clean(row.get("athlete_id")): dict(row) for row in rows},
        "rows": rows,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if Image is None:
        report = manifest([], {})
        report["status"] = "blocked_image_stack_unavailable"
        write_json(OUT_MANIFEST, report)
        write_text(OUT_REPORT, "# HSD Athlete Photo Onboarding v1\n\nPIL/Pillow is unavailable; variants were not generated.\n")
        print(json.dumps(report, indent=2))
        return 2

    rows = source_rows()
    metadata_rows, sheets = build_metadata(rows)
    report = manifest(metadata_rows, sheets)
    write_csv(OUT_METADATA_CSV, metadata_rows, METADATA_FIELDS)
    write_csv(OUT_DECISION_TEMPLATE, decision_rows(metadata_rows), DECISION_FIELDS)
    write_json(OUT_METADATA_JSON, metadata_json_payload(report, metadata_rows, sheets), indent=2)
    write_json(OUT_MANIFEST, report, indent=2)
    write_reports(metadata_rows, sheets, report)
    print(json.dumps({key: report[key] for key in ["version", "status", "source_rows", "review_variant_ready", "review_variant_needs_crop_review", "contact_sheets"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
