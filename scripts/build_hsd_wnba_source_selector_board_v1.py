from __future__ import annotations

import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:  # pragma: no cover - handled at runtime
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageOps = None


VERSION = "hsd-wnba-source-selector-board-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_source_selector_board_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_source_selector_board_v1"

SOURCE_ROWS: list[dict[str, str]] = [
    {
        "source_id": "apq001_review_only_candidate",
        "source_label": "APQ001 review-only candidate",
        "source_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg",
        "source_family": "apq001",
        "subject_hint": "WNBA review-only candidate",
    },
    {
        "source_id": "apcs033_operator_review",
        "source_label": "Jackie Young APCS033",
        "source_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs033_operator_review.jpg",
        "source_family": "jackie_young",
        "subject_hint": "Las Vegas Aces / Jackie Young",
    },
    {
        "source_id": "apcs038_operator_review",
        "source_label": "Jackie Young APCS038",
        "source_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs038_operator_review.jpg",
        "source_family": "jackie_young",
        "subject_hint": "Las Vegas Aces / Jackie Young",
    },
    {
        "source_id": "apcs039_operator_review",
        "source_label": "Jackie Young APCS039",
        "source_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg",
        "source_family": "jackie_young",
        "subject_hint": "Las Vegas Aces / Jackie Young",
    },
]

SOURCE_NOTES = {
    "apq001_review_only_candidate": {
        "crop_viability": "medium",
        "crop_reason": "Clean action frame, but the landscape ratio would need a heavier side crop for a 4:5 lead.",
    },
    "apcs033_operator_review": {
        "crop_viability": "high",
        "crop_reason": "Tight face-and-ball read with manageable crop headroom; strong backup if the lead needs a tighter mood.",
    },
    "apcs038_operator_review": {
        "crop_viability": "low",
        "crop_reason": "Big arena context is fun, but too much of the frame is background for a first-choice selector board.",
    },
    "apcs039_operator_review": {
        "crop_viability": "very_high",
        "crop_reason": "Portrait dribble frame keeps the subject dominant and gives the cleanest 4:5 crop path.",
    },
}

SOURCE_DIMENSION_HINTS = {
    "apq001_review_only_candidate": (2560, 1440),
    "apcs033_operator_review": (1080, 1920),
    "apcs038_operator_review": (1080, 1920),
    "apcs039_operator_review": (1080, 1920),
}

INTAKE_FIELDS = [
    "source_id",
    "source_label",
    "source_family",
    "subject_hint",
    "source_path",
    "source_exists",
    "width",
    "height",
    "aspect_ratio",
    "orientation",
    "target_crop_ratio",
    "crop_viability",
    "crop_viability_reason",
    "lead_rank",
    "recommended_lead_source",
    "manual_reviewer_notes",
    "review_only",
    "no_downloads",
    "no_source_discovery",
    "no_approvals",
    "no_publishing",
    "auto_approval",
    "auto_publish",
    "move_files",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def output_root() -> Path:
    raw = clean(os.environ.get("HSD_RUN_OUTPUT_DIR", ""))
    return Path(raw).resolve() if raw else DEFAULT_OUTPUT_DIR


def output_path(*parts: str) -> Path:
    return output_root().joinpath(*parts)


def load_font(size: int, *, bold: bool = False) -> Any:
    if ImageFont is None:
        return None
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf") if bold else Path("C:/Windows/Fonts/calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


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


def aspect_label(width: int, height: int) -> str:
    ratio = width / max(1, height)
    if ratio < 0.72:
        return "portrait"
    if ratio <= 1.15:
        return "square-ish"
    return "landscape"


def fit_image(path: Path, box_w: int, box_h: int) -> Any:
    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow is required for selector board rendering")
    with Image.open(path) as image:
        fitted = ImageOps.contain(image.convert("RGBA"), (box_w, box_h), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (box_w, box_h), (248, 250, 252, 255))
    canvas.alpha_composite(fitted, ((box_w - fitted.width) // 2, (box_h - fitted.height) // 2))
    return canvas


def image_dimensions(path: Path, source_id: str = "") -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except FileNotFoundError:
        if source_id in SOURCE_DIMENSION_HINTS:
            return SOURCE_DIMENSION_HINTS[source_id]
        raise


def crop_score(width: int, height: int, source_id: str) -> tuple[str, int]:
    ratio = width / max(1, height)
    target = 4 / 5
    ratio_distance = abs(math.log(max(ratio, 1e-6) / target, 2))
    score = int(round(max(0.0, 100.0 - ratio_distance * 38.0)))
    if source_id == "apcs039_operator_review":
        score += 12
    elif source_id == "apcs033_operator_review":
        score += 6
    elif source_id == "apq001_review_only_candidate":
        score += 0
    else:
        score -= 6
    return (("very_high" if score >= 90 else "high" if score >= 80 else "medium" if score >= 65 else "low"), max(0, min(100, score)))


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lead_rank, source in enumerate(SOURCE_ROWS, start=1):
        source_path = REPO_ROOT / source["source_path"]
        width, height = image_dimensions(source_path, source["source_id"])
        viability, score = crop_score(width, height, source["source_id"])
        note = SOURCE_NOTES[source["source_id"]]
        rows.append(
            {
                **source,
                "source_path": repo_rel(source_path),
                "source_exists": "true" if source_path.exists() else "false",
                "width": str(width),
                "height": str(height),
                "aspect_ratio": f"{width / max(1, height):.4f}",
                "orientation": aspect_label(width, height),
                "target_crop_ratio": "0.8000",
                "crop_viability": viability,
                "crop_viability_reason": note["crop_reason"],
                "crop_viability_score": str(score),
                "lead_rank": str(lead_rank),
                "recommended_lead_source": "yes" if source["source_id"] == "apcs039_operator_review" else "no",
                "manual_reviewer_notes": "",
                "review_only": "true",
                "no_downloads": "true",
                "no_source_discovery": "true",
                "no_approvals": "true",
                "no_publishing": "true",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
            }
        )
    return rows


def build_intake_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    intake: list[dict[str, str]] = []
    for row in rows:
        intake.append({field: clean(row.get(field)) for field in INTAKE_FIELDS})
    return intake


def draw_card(card: Any, row: dict[str, str]) -> None:
    if ImageDraw is None:
        raise RuntimeError("Pillow is required for selector board rendering")
    draw = ImageDraw.Draw(card)
    width, height = card.size
    pad = 20
    header_h = 78
    image_box = (pad, header_h, width - pad, height - 128)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=18, fill=(255, 255, 255), outline=(212, 220, 228), width=2)
    draw.text((pad, 18), row["source_label"], fill=(13, 20, 28), font=load_font(24, bold=True))
    lead_badge = "LEAD" if row["recommended_lead_source"] == "yes" else f"rank {row['lead_rank']}"
    draw.rounded_rectangle((width - 122, 18, width - 18, 52), radius=12, fill=(18, 118, 86) if row["recommended_lead_source"] == "yes" else (74, 83, 94))
    draw.text((width - 106, 25), lead_badge, fill=(255, 255, 255), font=load_font(15, bold=True))
    if row["source_exists"] == "true":
        try:
            card.paste(fit_image(REPO_ROOT / row["source_path"], image_box[2] - image_box[0], image_box[3] - image_box[1]), (image_box[0], image_box[1]), None)
        except Exception:
            draw.rectangle(image_box, fill=(236, 240, 244), outline=(180, 188, 196))
            draw.text((image_box[0] + 18, image_box[1] + 18), "render failed", fill=(130, 38, 38), font=load_font(16))
    else:
        draw.rectangle(image_box, fill=(236, 240, 244), outline=(180, 188, 196))
        draw.text((image_box[0] + 18, image_box[1] + 18), "missing source", fill=(130, 38, 38), font=load_font(16))

    body_font = load_font(15)
    tiny_font = load_font(13)
    text_x = pad
    base_y = height - 116
    text_lines = [
        f"{row['width']}x{row['height']} | aspect {row['aspect_ratio']} | {row['orientation']}",
        f"Crop viability: {row['crop_viability']} ({row['crop_viability_score']}/100)",
        f"Lead fit: {'yes' if row['recommended_lead_source'] == 'yes' else 'no'} | source: {row['source_path']}",
    ]
    for idx, text in enumerate(text_lines):
        font = body_font if idx < 2 else tiny_font
        draw.text((text_x, base_y + idx * 24), ellipsize(draw, text, font, width - pad * 2), fill=(55, 65, 75), font=font)


def make_thumbnails(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if Image is None:
        raise RuntimeError("Pillow is required for selector board rendering")
    thumb_dir = output_path("source_thumbnails")
    thumb_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, str]] = []
    for row in rows:
        card = Image.new("RGBA", (760, 560), (255, 255, 255, 255))
        draw_card(card, row)
        thumb_path = thumb_dir / f"{row['source_id']}.png"
        card.save(thumb_path)
        outputs.append({"source_id": row["source_id"], "thumbnail_path": thumb_path.as_posix()})
    return outputs


def make_contact_sheet(rows: list[dict[str, str]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for selector board rendering")
    cols = 2
    card_w, card_h = 760, 560
    margin = 28
    header_h = 110
    row_count = max(1, math.ceil(len(rows) / cols))
    sheet = Image.new(
        "RGBA",
        (margin * 2 + cols * card_w + (cols - 1) * 20, margin * 2 + header_h + row_count * card_h + (row_count - 1) * 20),
        (245, 248, 250, 255),
    )
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(28, bold=True)
    body_font = load_font(17)
    draw.text((margin, 22), "WNBA Source Selector Board", fill=(13, 20, 28), font=title_font)
    draw.text(
        (margin, 60),
        "Review-only local candidates. The board compares dimensions, crop viability, and the recommended lead source without downloading or approving anything.",
        fill=(73, 82, 92),
        font=body_font,
    )
    draw.text((margin, 88), f"Recommended lead source: {next(row['source_label'] for row in rows if row['recommended_lead_source'] == 'yes')}", fill=(18, 118, 86), font=body_font)
    for index, row in enumerate(rows):
        thumb_path = output_path("source_thumbnails", f"{row['source_id']}.png")
        with Image.open(thumb_path) as thumb:
            card = thumb.convert("RGBA")
        col = index % cols
        row_i = index // cols
        x = margin + col * (card_w + 20)
        y = margin + header_h + row_i * (card_h + 20)
        sheet.alpha_composite(card, (x, y))
    sheet_path = output_path("wnba_source_selector_contact_sheet.png")
    sheet.convert("RGB").save(sheet_path)
    return sheet_path


def render_board_markdown(rows: list[dict[str, str]], sheet_path: Path, generated_at: str) -> str:
    lead = next(row for row in rows if row["recommended_lead_source"] == "yes")
    lines = [
        "# WNBA Source Selector Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only selector board for local WNBA source candidates. It stays inside the quarantine set, uses no new downloads, and does not create approvals or a publish-ready lane.",
        "",
        f"![WNBA source selector board]({sheet_path.name})",
        "",
        "## Recommendation",
        "",
        f"- Recommended lead source: `{lead['source_label']}`",
        f"- Why: {lead['crop_viability_reason']}",
        f"- Target crop ratio: `4:5` (`{lead['target_crop_ratio']}`)",
        "",
        "## Candidate Rows",
        "",
        "| Source | Dimensions | Aspect | Crop viability | Lead | Path |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['source_label']} | {row['width']}x{row['height']} | {row['aspect_ratio']} ({row['orientation']}) | {row['crop_viability']} | {row['recommended_lead_source']} | `{row['source_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- asset_downloads=false",
            "- source_discovery_performed=false",
            "- approval_state_change=false",
            "- publishing=false",
            "- auto_approval=false",
            "- auto_publish=false",
            "- move_files=false",
        ]
    )
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    generated_at = now_iso()
    out_root = output_root()
    out_root.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    make_thumbnails(rows)
    sheet_path = make_contact_sheet(rows)
    intake_rows = build_intake_rows(rows)
    board_md = render_board_markdown(rows, sheet_path, generated_at)
    board_path = output_path("wnba_source_selector_board.md")
    board_path.write_text(board_md, encoding="utf-8")
    intake_path = output_path("manual_source_review_intake.csv")
    write_csv(intake_path, intake_rows, INTAKE_FIELDS)
    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": generated_at,
        "status": "wnba_source_selector_board_ready" if rows else "wnba_source_selector_board_empty",
        "review_only": True,
        "source_count": len(rows),
        "recommended_lead_source": next(row["source_id"] for row in rows if row["recommended_lead_source"] == "yes"),
        "contact_sheet_path": sheet_path.as_posix(),
        "board_path": board_path.as_posix(),
        "manual_source_review_intake_path": intake_path.as_posix(),
        "thumbnail_dir": output_path("source_thumbnails").as_posix(),
        "rows": rows,
        "guardrails": {
            "review_only": True,
            "no_downloads": True,
            "no_source_discovery": True,
            "no_approvals": True,
            "no_publishing": True,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
        },
    }
    manifest_path = output_path("manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "source_count": len(rows), "recommended_lead_source": manifest["recommended_lead_source"], "contact_sheet": sheet_path.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
