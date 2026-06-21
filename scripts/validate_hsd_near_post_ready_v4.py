from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat

VERSION = "v1.1-phase6j-near-post-ready-gate"
CLEAN_REPORT = Path("clean_plate_v4_report.json")
RENDER_MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
FIDELITY_REPORT = Path("template_fidelity_v4_report.json")
OUT_JSON = Path("near_post_ready_v4_report.json")
OUT_MD = Path("near_post_ready_v4_report.md")
OUT_CSV = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/near_post_ready/near_post_ready_v4_rows.csv")
CONTACT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/near_post_ready/near_post_ready_v4_contact_sheet.jpg")
MASK_SHEET = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/near_post_ready/near_post_ready_v4_mask_compliance_sheet.jpg")
FIELDS = [
    "template_id", "platform", "module_mode", "headline", "output_path", "near_post_ready_candidate",
    "fixture_only_player_asset", "placeholder_layer_count", "zone_overflow_count", "inside_changed_ratio",
    "outside_changed_ratio", "outside_mean_delta", "clean_plate_hash_ok", "dynamic_mask_hash_ok",
    "mask_compliance_status", "reasons",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pixel_change_metrics(plate: Image.Image, render: Image.Image, mask: Image.Image) -> Tuple[float, float, float]:
    if plate.size != render.size or plate.size != mask.size:
        return 0.0, 1.0, 255.0
    diff = ImageChops.difference(plate.convert("RGB"), render.convert("RGB")).convert("L")
    diff_pixels = list(diff.get_flattened_data() if hasattr(diff, "get_flattened_data") else diff.getdata())
    mask_image = mask.convert("L")
    mask_pixels = list(mask_image.get_flattened_data() if hasattr(mask_image, "get_flattened_data") else mask_image.getdata())
    inside_total = outside_total = inside_changed = outside_changed = 0
    outside_values: List[int] = []
    for delta, marker in zip(diff_pixels, mask_pixels):
        if marker > 0:
            inside_total += 1
            if delta > 8:
                inside_changed += 1
        else:
            outside_total += 1
            outside_values.append(delta)
            if delta > 8:
                outside_changed += 1
    inside_ratio = inside_changed / max(1, inside_total)
    outside_ratio = outside_changed / max(1, outside_total)
    outside_mean = sum(outside_values) / max(1, len(outside_values))
    return inside_ratio, outside_ratio, outside_mean


def evaluate_item(item: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    output = Path(clean(item.get("output_path")))
    plate = Path(clean(item.get("clean_plate_path")))
    mask_path = Path(clean(item.get("dynamic_mask_path")))
    if not output.exists():
        reasons.append("missing_render")
    if not plate.exists():
        reasons.append("missing_clean_plate")
    if not mask_path.exists():
        reasons.append("missing_dynamic_mask")
    clean_hash_ok = plate.exists() and sha256(plate) == clean(item.get("clean_plate_sha256"))
    mask_hash_ok = mask_path.exists() and sha256(mask_path) == clean(item.get("dynamic_mask_sha256"))
    if not clean_hash_ok:
        reasons.append("clean_plate_hash_mismatch")
    if not mask_hash_ok:
        reasons.append("dynamic_mask_hash_mismatch")
    inside_ratio = 0.0
    outside_ratio = 1.0
    outside_mean = 255.0
    if output.exists() and plate.exists() and mask_path.exists():
        inside_ratio, outside_ratio, outside_mean = pixel_change_metrics(
            Image.open(plate).convert("RGB"),
            Image.open(output).convert("RGB"),
            Image.open(mask_path).convert("L"),
        )
    if inside_ratio < 0.015:
        reasons.append("dynamic_mask_not_repainted")
    if outside_ratio > 0.012:
        reasons.append("render_changes_outside_dynamic_mask")
    if outside_mean > 1.75:
        reasons.append("unmasked_mean_delta_too_high")
    if int(item.get("placeholder_layer_count") or 0) != 0:
        reasons.append("placeholder_layer_present")
    if int(item.get("zone_overflow_count") or 0) != 0:
        reasons.append("zone_overflow_present")
    fixture_only = clean(item.get("fixture_only_player_asset")) == "true"
    if fixture_only:
        reasons.append("fixture_only_player_asset_review")
    hard_reasons = [reason for reason in reasons if reason != "fixture_only_player_asset_review"]
    status = "passed_mask_compliance" if not hard_reasons else "blocked_mask_compliance"
    return {
        **item,
        "inside_changed_ratio": round(inside_ratio, 6),
        "outside_changed_ratio": round(outside_ratio, 6),
        "outside_mean_delta": round(outside_mean, 4),
        "clean_plate_hash_ok": clean_hash_ok,
        "dynamic_mask_hash_ok": mask_hash_ok,
        "mask_compliance_status": status,
        "reasons": ";".join(reasons),
    }


def build_sheet(rows: List[Dict[str, Any]], path: Path, mask_mode: bool) -> None:
    if not rows:
        return
    columns = 3
    cell_width, cell_height = 350, 470
    row_count = math.ceil(len(rows) / columns)
    sheet = Image.new("RGB", (columns * cell_width + 30, row_count * cell_height + 70), (242, 242, 242))
    draw = ImageDraw.Draw(sheet)
    title = "HSD Phase 6E Mask Compliance" if mask_mode else "HSD Phase 6E Near-Post-Ready Review"
    draw.text((20, 20), title, fill=(20, 20, 20), font=ImageFont.load_default())
    for index, row in enumerate(rows):
        output = Path(clean(row.get("output_path")))
        if not output.exists():
            continue
        render = Image.open(output).convert("RGB")
        if mask_mode:
            mask_path = Path(clean(row.get("dynamic_mask_path")))
            mask = Image.open(mask_path).convert("L") if mask_path.exists() else Image.new("L", render.size, 0)
            overlay = render.convert("RGBA")
            red = Image.new("RGBA", render.size, (255, 20, 20, 0))
            red.putalpha(mask.point(lambda pixel: 75 if pixel else 0))
            render = Image.alpha_composite(overlay, red).convert("RGB")
        render.thumbnail((310, 385), Image.Resampling.LANCZOS)
        column = index % columns
        row_index = index // columns
        x = 20 + column * cell_width + (310 - render.width) // 2
        y = 55 + row_index * cell_height
        sheet.paste(render, (x, y))
        label_x = 20 + column * cell_width
        draw.text((label_x, y + 395), f"{row.get('template_id')} • {row.get('module_mode')}", fill=(20, 20, 20), font=ImageFont.load_default())
        draw.text((label_x, y + 414), f"inside={row.get('inside_changed_ratio')} outside={row.get('outside_changed_ratio')}", fill=(70, 70, 70), font=ImageFont.load_default())
        draw.text((label_x, y + 433), f"{row.get('mask_compliance_status')} | near={row.get('near_post_ready_candidate')}", fill=(70, 70, 70), font=ImageFont.load_default())
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=92)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    clean_report = read_json(CLEAN_REPORT)
    manifest = read_json(RENDER_MANIFEST)
    fidelity = read_json(FIDELITY_REPORT)
    blockers: List[str] = []
    warnings: List[str] = []
    if clean_report.get("status") != "passed_clean_plate_build":
        blockers.append("clean_plate_build_not_passed")
    accepted_renderer_versions = {
        "v4.2-phase6e-clean-plate-near-post-ready",
        "v4.3-phase6h-targeted-fidelity-lift",
        "v4.4-phase6i-final-score-template-polish",
        "v4.5-phase6j-final-score-content-modules",
    }
    if manifest.get("version") not in accepted_renderer_versions:
        blockers.append("renderer_not_supported_phase6e_or_later")
    if fidelity and fidelity.get("status") != "passed_fidelity_setup":
        blockers.append("fidelity_setup_not_passed")
    rows = [evaluate_item(item) for item in (manifest.get("items") or [])]
    if not rows:
        blockers.append("no_renderer_items")
    hard_failed = [row for row in rows if row.get("mask_compliance_status") != "passed_mask_compliance"]
    if hard_failed:
        blockers.append("mask_compliance_failures_present")
    fixture_rows = [row for row in rows if clean(row.get("fixture_only_player_asset")) == "true"]
    if fixture_rows:
        warnings.append("fixture_only_player_variants_require_real_asset_before_approval")
    near_rows = [row for row in rows if clean(row.get("near_post_ready_candidate")) == "true" and row.get("mask_compliance_status") == "passed_mask_compliance"]
    if len(near_rows) < 5:
        blockers.append("insufficient_near_post_ready_candidates")
    expected_near_templates = {
        "hsd_tonight_in_the_w_a",
        "hsd_game_recap_final_score_a",
        "hsd_game_recap_final_score_c_story",
    }
    near_templates = {clean(row.get("template_id")) for row in near_rows}
    for template_id in expected_near_templates:
        if template_id not in near_templates:
            blockers.append(f"missing_near_post_ready_template:{template_id}")
    status = "passed_near_post_ready_setup" if not blockers else "blocked_near_post_ready_setup"
    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "cutover_allowed": False,
        "human_visual_approval_required": True,
        "rendered_rows": len(rows),
        "near_post_ready_candidates": len(near_rows),
        "fixture_only_review_rows": len(fixture_rows),
        "mask_compliance_failures": len(hard_failed),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CSV, rows, FIELDS)
    build_sheet(rows, CONTACT, False)
    build_sheet(rows, MASK_SHEET, True)
    lines = [
        "# HSD Phase 6J Near-Post-Ready Gate",
        "",
        f"Status: `{status}`",
        f"Rendered rows: `{len(rows)}`",
        f"Near-post-ready candidates: `{len(near_rows)}`",
        f"Fixture-only review rows: `{len(fixture_rows)}`",
        f"Cutover allowed: `{report['cutover_allowed']}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{blocker}`" for blocker in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{warning}`" for warning in report["warnings"]] or ["- None"]
    lines += ["", "## Policy", "", "Near-post-ready means clean-plate and mask compliance passed. Human visual approval is still mandatory before production cutover."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": VERSION,
        "status": status,
        "rendered_rows": len(rows),
        "near_post_ready_candidates": len(near_rows),
        "fixture_only_review_rows": len(fixture_rows),
        "blockers": report["blockers"],
        "warnings": report["warnings"],
    }, indent=2))
    return 2 if args.strict and blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
