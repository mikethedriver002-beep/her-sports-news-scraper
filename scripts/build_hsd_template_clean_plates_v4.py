from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageStat

VERSION = "v1.0-phase6e-clean-plate-builder"
RECIPES = Path("config/graphics/v4/clean_plates/clean_plate_recipes_v4.json")
REPORT_JSON = Path("clean_plate_v4_report.json")
REPORT_MD = Path("clean_plate_v4_report.md")
CONTACT_SHEET = Path("clean_plate_v4_contact_sheet.jpg")


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def dark_texture(source: Image.Image, size: Tuple[int, int], seed: int) -> Image.Image:
    width, height = size
    base = ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(24))
    base = ImageEnhance.Brightness(base).enhance(0.18)
    base = ImageEnhance.Color(base).enhance(0.45)
    randomizer = random.Random(seed)
    noise_small = Image.new("L", (max(8, width // 8), max(8, height // 8)))
    noise_small.putdata([randomizer.randint(5, 42) for _ in range(noise_small.width * noise_small.height)])
    noise = noise_small.resize(size, Image.Resampling.BICUBIC)
    warm = ImageOps.colorize(noise, black=(1, 2, 4), white=(48, 38, 22))
    patch = Image.blend(base, warm, 0.42)
    fine = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(fine, "RGBA")
    for _ in range(max(24, width * height // 1100)):
        x = randomizer.randrange(width)
        y = randomizer.randrange(height)
        value = randomizer.randrange(22, 72)
        draw.point((x, y), fill=(value, value - 4, max(0, value - 14), randomizer.randrange(9, 24)))
    patch = Image.alpha_composite(patch.convert("RGBA"), fine)
    return patch.convert("RGB")


def rect_tuple(value: Iterable[Any]) -> Tuple[int, int, int, int]:
    x, y, width, height = [int(v) for v in value]
    return x, y, width, height


def mean_delta(a: Image.Image, b: Image.Image, mask: Image.Image) -> float:
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L")
    stat = ImageStat.Stat(diff, mask=mask.convert("L"))
    return float(stat.mean[0]) if stat.mean else 0.0


def build_plate(template_id: str, recipe: Dict[str, Any], output_root: Path, mask_root: Path) -> Dict[str, Any]:
    source_path = Path(clean(recipe.get("source")))
    if not source_path.exists():
        return {"template_id": template_id, "status": "blocked_missing_source", "source": source_path.as_posix()}
    source = Image.open(source_path).convert("RGB")
    plate = source.copy()
    mask = Image.new("L", source.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    for index, region in enumerate(recipe.get("regions") or []):
        x, y, width, height = rect_tuple(region.get("rect") or [])
        if width <= 0 or height <= 0:
            continue
        if x < 0 or y < 0 or x + width > source.width or y + height > source.height:
            raise ValueError(f"Region outside canvas: {template_id}:{region.get('name')}:{x},{y},{width},{height}")
        patch = dark_texture(source, (width, height), seed=sum(ord(c) for c in f"{template_id}:{index}"))
        plate.paste(patch, (x, y))
        mask_draw.rectangle((x, y, x + width - 1, y + height - 1), fill=255)
    output_root.mkdir(parents=True, exist_ok=True)
    mask_root.mkdir(parents=True, exist_ok=True)
    plate_path = output_root / f"{template_id}_clean_plate.png"
    mask_path = mask_root / f"{template_id}_dynamic_mask.png"
    plate.save(plate_path, format="PNG", optimize=True)
    mask.save(mask_path, format="PNG", optimize=True)
    total = source.width * source.height
    white = mask.histogram()[255]
    inverse = ImageOps.invert(mask)
    return {
        "template_id": template_id,
        "status": "built_clean_plate",
        "source_path": source_path.as_posix(),
        "clean_plate_path": plate_path.as_posix(),
        "dynamic_mask_path": mask_path.as_posix(),
        "source_sha256": sha256(source_path),
        "clean_plate_sha256": sha256(plate_path),
        "dynamic_mask_sha256": sha256(mask_path),
        "width": source.width,
        "height": source.height,
        "region_count": len(recipe.get("regions") or []),
        "mask_coverage_ratio": round(white / max(1, total), 6),
        "mean_delta_inside_mask": round(mean_delta(source, plate, mask), 4),
        "mean_delta_outside_mask": round(mean_delta(source, plate, inverse), 4),
        "regions": recipe.get("regions") or [],
    }


def build_contact(rows: List[Dict[str, Any]]) -> None:
    valid = [row for row in rows if row.get("status") == "built_clean_plate"]
    if not valid:
        return
    cell_w, cell_h = 720, 500
    sheet = Image.new("RGB", (cell_w * 2, 70 + cell_h * len(valid)), (242, 242, 242))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 20), "HSD Phase 6E Clean Plates — Source / Mask / Clean Plate", fill=(20, 20, 20))
    for index, row in enumerate(valid):
        source = Image.open(row["source_path"]).convert("RGB")
        plate = Image.open(row["clean_plate_path"]).convert("RGB")
        mask = Image.open(row["dynamic_mask_path"]).convert("L")
        overlay = source.convert("RGBA")
        red = Image.new("RGBA", source.size, (255, 30, 30, 0))
        red.putalpha(mask.point(lambda p: 105 if p else 0))
        overlay = Image.alpha_composite(overlay, red).convert("RGB")
        left = ImageOps.contain(overlay, (330, 420), Image.Resampling.LANCZOS)
        right = ImageOps.contain(plate, (330, 420), Image.Resampling.LANCZOS)
        y = 70 + index * cell_h
        sheet.paste(left, (20 + (330 - left.width) // 2, y + 20))
        sheet.paste(right, (370 + (330 - right.width) // 2, y + 20))
        draw.text((20, y + 450), f"{row['template_id']} | mask {row['mask_coverage_ratio']:.1%}", fill=(25, 25, 25))
        draw.text((370, y + 450), f"inside Δ {row['mean_delta_inside_mask']} | outside Δ {row['mean_delta_outside_mask']}", fill=(25, 25, 25))
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET, quality=92)


def build_all() -> Dict[str, Any]:
    recipes = read_json(RECIPES)
    output_root = Path(clean(recipes.get("output_root")))
    mask_root = Path(clean(recipes.get("mask_root")))
    rows: List[Dict[str, Any]] = []
    blockers: List[str] = []
    for template_id, recipe in sorted((recipes.get("templates") or {}).items()):
        try:
            row = build_plate(template_id, recipe, output_root, mask_root)
        except Exception as exc:
            row = {"template_id": template_id, "status": "blocked_build_error", "error": f"{type(exc).__name__}: {exc}"}
        rows.append(row)
        if row.get("status") != "built_clean_plate":
            blockers.append(f"clean_plate_failed:{template_id}:{row.get('status')}")
            continue
        coverage = float(row.get("mask_coverage_ratio") or 0)
        if not 0.08 <= coverage <= 0.80:
            blockers.append(f"mask_coverage_out_of_range:{template_id}:{coverage}")
        if float(row.get("mean_delta_inside_mask") or 0) < 4.0:
            blockers.append(f"placeholder_erasure_too_small:{template_id}")
        if float(row.get("mean_delta_outside_mask") or 0) > 0.05:
            blockers.append(f"unmasked_plate_changed:{template_id}")
    build_contact(rows)
    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed_clean_plate_build" if not blockers else "blocked_clean_plate_build",
        "strict_exit_code": 0 if not blockers else 2,
        "template_count": len(rows),
        "blockers": blockers,
        "rows": rows,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 6E Clean Plate Build",
        "",
        f"Status: `{report['status']}`",
        f"Templates: `{len(rows)}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{item}`" for item in blockers] or ["- None"]
    lines += ["", "## Plates", ""]
    for row in rows:
        lines.append(
            f"- `{row.get('template_id')}` | `{row.get('status')}` | mask `{row.get('mask_coverage_ratio')}` | "
            f"inside Δ `{row.get('mean_delta_inside_mask')}` | outside Δ `{row.get('mean_delta_outside_mask')}`"
        )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_all()
    print(json.dumps({
        "version": VERSION,
        "status": report["status"],
        "template_count": report["template_count"],
        "blockers": report["blockers"],
    }, indent=2))
    return 2 if args.strict and report.get("blockers") else 0


if __name__ == "__main__":
    raise SystemExit(main())
