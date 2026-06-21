from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from PIL import Image, ImageDraw, ImageFont

VERSION = "v1.0-phase6j-final-score-content-module-gate"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_v4.json")
OUT_JSON = Path("final_score_content_modules_v4_report.json")
OUT_MD = Path("final_score_content_modules_v4_report.md")
OUT_CSV = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/content_modules/final_score_content_modules_v4_rows.csv")
CONTACT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/content_modules/final_score_content_modules_v4_contact_sheet.jpg")
FIELDS = [
    "item_id", "template_id", "platform", "headline", "output_path", "content_module_status",
    "content_module_score", "content_module_reasons", "content_module_mode", "content_module_title",
    "content_module_body", "content_module_stat_count", "content_module_prompt", "validation_status",
    "validation_reasons",
]
FINAL_TEMPLATES = {
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_b",
    "hsd_game_recap_final_score_c_story",
}
GENERIC_TOKENS = {
    "FINAL SCORE CONFIRMED",
    "FULL BOX SCORE REVIEW PENDING",
    "WHAT CHANGED THE GAME?",
}


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_float(value: Any) -> float:
    try:
        return float(clean(value) or "0")
    except Exception:
        return 0.0


def as_int(value: Any) -> int:
    try:
        return int(float(clean(value) or "0"))
    except Exception:
        return 0


def validate_row(item: Dict[str, Any], minimum_score: float) -> Dict[str, Any]:
    reasons: List[str] = []
    template_id = clean(item.get("template_id"))
    mode = clean(item.get("content_module_mode"))
    title = clean(item.get("content_module_title"))
    body = clean(item.get("content_module_body"))
    prompt = clean(item.get("content_module_prompt"))
    score = as_float(item.get("content_module_score"))
    stat_count = as_int(item.get("content_module_stat_count"))
    if clean(item.get("content_module_status")) != "passed_final_score_content_modules":
        reasons.append("renderer_content_module_not_passed")
    if score < minimum_score:
        reasons.append(f"content_module_score_below_minimum:{minimum_score:.2f}")
    if not mode:
        reasons.append("missing_content_module_mode")
    if not title:
        reasons.append("missing_content_module_title")
    if not body:
        reasons.append("missing_content_module_body")
    upper_body = body.upper()
    for token in GENERIC_TOKENS:
        if token in upper_body:
            reasons.append(f"generic_content_token:{token}")
    if template_id == "hsd_game_recap_final_score_a" and mode not in {"verified_player_stats", "game_edge"}:
        reasons.append("final_score_a_invalid_content_module_mode")
    if template_id == "hsd_game_recap_final_score_b":
        if mode != "verified_player_stats":
            reasons.append("final_score_b_requires_verified_player_stats_mode")
        if stat_count < 1:
            reasons.append("final_score_b_requires_verified_stat_count")
        if not clean(item.get("player_names")):
            reasons.append("final_score_b_requires_player_name")
    if template_id == "hsd_game_recap_final_score_c_story":
        if mode not in {"verified_player_stats", "game_edge"}:
            reasons.append("final_score_c_invalid_content_module_mode")
        if not prompt:
            reasons.append("final_score_c_missing_dynamic_prompt")
        if prompt.upper() == "WHAT CHANGED THE GAME?":
            reasons.append("final_score_c_generic_prompt")
    return {
        **item,
        "validation_status": "passed_content_module_validation" if not reasons else "blocked_content_module_validation",
        "validation_reasons": ";".join(sorted(set(reasons))),
    }


def load_font(size: int) -> ImageFont.ImageFont:
    for raw in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        path = Path(raw)
        if path.exists():
            return ImageFont.truetype(path.as_posix(), size=size)
    return ImageFont.load_default()


def build_contact_sheet(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    columns = 3
    cell_w, cell_h = 360, 510
    header_h = 82
    sheet = Image.new("RGB", (columns * cell_w + 30, math.ceil(len(rows) / columns) * cell_h + header_h + 20), (240, 240, 240))
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 20), "HSD Phase 6J Final Score Content Modules", fill=(15, 15, 15), font=load_font(24))
    draw.text((20, 52), "Empty performer bands, score-only takeaways, and unverified player-stat cards are blocked.", fill=(70, 70, 70), font=load_font(13))
    for index, row in enumerate(rows):
        col = index % columns
        row_index = index // columns
        x0 = 15 + col * cell_w
        y0 = header_h + row_index * cell_h
        path = Path(clean(row.get("output_path")))
        if path.exists():
            image = Image.open(path).convert("RGB")
            image.thumbnail((320, 400), Image.Resampling.LANCZOS)
            sheet.paste(image, (x0 + (320 - image.width) // 2 + 10, y0 + 4))
        status = clean(row.get("validation_status"))
        color = (10, 105, 45) if status == "passed_content_module_validation" else (160, 55, 25)
        draw.text((x0 + 10, y0 + 408), f"{index + 1}. {status}", fill=color, font=load_font(13))
        draw.text((x0 + 10, y0 + 430), f"{row.get('template_id')} • {row.get('platform')}", fill=(30, 30, 30), font=load_font(12))
        draw.text((x0 + 10, y0 + 451), f"{row.get('content_module_mode')} • {row.get('content_module_title')}", fill=(50, 50, 50), font=load_font(12))
        body = clean(row.get("content_module_body"))[:58]
        draw.text((x0 + 10, y0 + 472), body, fill=(75, 75, 75), font=load_font(11))
    CONTACT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT, quality=92)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    manifest = read_json(MANIFEST)
    policy = read_json(POLICY)
    blockers: List[str] = []
    warnings: List[str] = []
    if manifest.get("version") != "v4.5-phase6j-final-score-content-modules":
        blockers.append("renderer_not_phase6j_v4_5")
    minimum_score = as_float(policy.get("minimum_final_score_content_module_score") or 0.95)
    rows = [validate_row(item, minimum_score) for item in (manifest.get("items") or []) if clean(item.get("template_id")) in FINAL_TEMPLATES]
    if not rows:
        blockers.append("no_final_score_rows")
    failed = [row for row in rows if row.get("validation_status") != "passed_content_module_validation"]
    if failed:
        blockers.append("final_score_content_module_failures_present")
    templates = {clean(row.get("template_id")) for row in rows}
    for template_id in ["hsd_game_recap_final_score_a", "hsd_game_recap_final_score_c_story"]:
        if template_id not in templates:
            blockers.append(f"missing_required_final_score_content_template:{template_id}")
    if "hsd_game_recap_final_score_b" not in templates:
        warnings.append("final_score_b_not_rendered_no_verified_player_stats_available")
    status = "passed_final_score_content_modules" if not blockers else "blocked_final_score_content_modules"
    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "renderer_version": manifest.get("version"),
        "final_score_rows": len(rows),
        "passed_rows": len(rows) - len(failed),
        "failed_rows": len(failed),
        "minimum_content_module_score": minimum_score,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CSV, rows, FIELDS)
    build_contact_sheet(rows)
    lines = [
        "# HSD Phase 6J Final Score Content Module Gate",
        "",
        f"Status: `{status}`",
        f"Final-score rows: `{len(rows)}`",
        f"Passed rows: `{len(rows) - len(failed)}`",
        f"Failed rows: `{len(failed)}`",
        f"Minimum content-module score: `{minimum_score:.2f}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report["warnings"]] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": VERSION,
        "status": status,
        "final_score_rows": len(rows),
        "passed_rows": len(rows) - len(failed),
        "failed_rows": len(failed),
        "blockers": report["blockers"],
        "warnings": report["warnings"],
    }, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
