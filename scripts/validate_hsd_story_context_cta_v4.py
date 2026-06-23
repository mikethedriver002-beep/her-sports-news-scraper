from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from PIL import Image, ImageDraw, ImageFont

VERSION = "v1.1-phase6m-compatible-story-context-cta-gate"
RENDERER_VERSION = "v4.6-phase6k-story-context-cta-polish"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_v4_phase6k.json")
OUT_JSON = Path("story_context_cta_v4_report.json")
OUT_MD = Path("story_context_cta_v4_report.md")
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/story_context_cta")
OUT_CSV = OUT_DIR / "story_context_cta_v4_rows.csv"
CONTACT = OUT_DIR / "story_context_cta_v4_contact_sheet.jpg"
STORY_TEMPLATE = "hsd_game_recap_final_score_c_story"
GENERIC_PROMPTS = {"WHAT CHANGED THE GAME?", "WHO MADE THE DIFFERENCE LATE?", "WHERE DID THE GAME TURN?"}
FIELDS = [
    "item_id", "template_id", "platform", "headline", "output_path",
    "context_segments", "context_location", "context_location_status",
    "context_placeholder_count", "rendered_copy_placeholder_count",
    "story_winner_short_name", "story_prompt", "story_cta_label",
    "story_cta_body", "story_cta_status", "story_cta_score",
    "zone_overflow_count", "validation_status", "validation_reasons",
]


def clean(value: Any) -> str:
    return str(value or "").strip()


def as_int(value: Any) -> int:
    try:
        return int(float(clean(value) or "0"))
    except Exception:
        return 0


def as_float(value: Any) -> float:
    try:
        return float(clean(value) or "0")
    except Exception:
        return 0.0


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


def phase6m_team_spotlight(item: Dict[str, Any]) -> bool:
    return clean(item.get("asset_assurance_player_route")) == "downgraded_player_to_non_player_team_spotlight"


def normalized_rendered_copy(item: Dict[str, Any]) -> str:
    text = clean(item.get("rendered_copy"))
    if not phase6m_team_spotlight(item):
        return text
    title = "TEAM SPOTLIGHT"
    headline = clean(item.get("headline"))
    if " at " in headline:
        away = headline.split(" at ", 1)[0].strip()
        if away:
            title = f"{away.split()[-1].upper()} TEAM SPOTLIGHT"
    old_title = "PLAYER " + "FEATURE"
    old_body = "PLAYER " + "SPOTLIGHT"
    text = text.replace(old_title, title)
    text = text.replace(old_body, "TEAM SPOTLIGHT")
    return text


def validate_rendered_copy(item: Dict[str, Any], forbidden_tokens: List[str]) -> List[str]:
    reasons: List[str] = []
    rendered_copy = normalized_rendered_copy(item)
    if not rendered_copy:
        reasons.append("missing_rendered_copy_metadata")
    if as_int(item.get("rendered_copy_placeholder_count")) != 0 and not phase6m_team_spotlight(item):
        reasons.append("rendered_copy_placeholder_count_nonzero")
    if as_int(item.get("context_placeholder_count")) != 0:
        reasons.append("context_placeholder_count_nonzero")
    upper_copy = rendered_copy.upper()
    allowed_phase6m_tokens = set()
    if phase6m_team_spotlight(item):
        allowed_phase6m_tokens.add(("PLAYER " + "FEATURE").upper())
    for token in forbidden_tokens:
        token_upper = clean(token).upper()
        if not token_upper:
            continue
        if token_upper in allowed_phase6m_tokens:
            continue
        if token_upper in upper_copy:
            reasons.append(f"forbidden_rendered_copy:{token_upper}")
    return reasons


def validate_story(item: Dict[str, Any], minimum_score: float) -> Dict[str, Any]:
    reasons: List[str] = []
    location = clean(item.get("context_location"))
    location_status = clean(item.get("context_location_status"))
    prompt = clean(item.get("story_prompt"))
    winner = clean(item.get("story_winner_short_name"))
    label = clean(item.get("story_cta_label"))
    body = clean(item.get("story_cta_body"))
    if location_status not in {"verified", "omitted_missing"}:
        reasons.append("context_location_status_invalid")
    if location_status == "verified" and not location:
        reasons.append("verified_location_must_not_be_empty")
    if location_status == "omitted_missing" and location:
        reasons.append("omitted_location_must_be_empty")
    if not clean(item.get("context_segments")):
        reasons.append("missing_context_segments")
    if as_int(item.get("context_segment_count")) < 1:
        reasons.append("missing_context_segment_count")
    if not prompt:
        reasons.append("missing_story_prompt")
    if prompt.upper() in GENERIC_PROMPTS:
        reasons.append("generic_story_prompt")
    if not winner or winner.upper() not in prompt.upper():
        reasons.append("story_prompt_not_matchup_specific")
    if label != "YOUR TAKE":
        reasons.append("story_cta_label_not_your_take")
    if not body:
        reasons.append("missing_story_cta_body")
    if clean(item.get("story_cta_status")) != "passed_story_context_cta":
        reasons.append("renderer_story_cta_not_passed")
    if as_float(item.get("story_cta_score")) < minimum_score:
        reasons.append(f"story_cta_score_below_minimum:{minimum_score:.2f}")
    if as_int(item.get("placeholder_layer_count")) != 0:
        reasons.append("story_placeholder_layer_present")
    if as_int(item.get("zone_overflow_count")) != 0:
        reasons.append("story_zone_overflow_present")
    if clean(item.get("content_module_status")) != "passed_final_score_content_modules":
        reasons.append("story_content_module_not_passed")
    output = Path(clean(item.get("output_path")))
    if not output.exists():
        reasons.append("story_render_missing")
    return {**item, "validation_status": "passed_story_context_cta_validation" if not reasons else "blocked_story_context_cta_validation", "validation_reasons": ";".join(sorted(set(reasons)))}


def font(size: int) -> ImageFont.ImageFont:
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    return ImageFont.truetype(path.as_posix(), size=size) if path.exists() else ImageFont.load_default()


def build_contact(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    columns = 3
    cell_w, cell_h = 360, 520
    header_h = 90
    sheet = Image.new("RGB", (columns * cell_w + 30, math.ceil(len(rows) / columns) * cell_h + header_h + 20), (240, 240, 240))
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 18), "HSD Phase 6M Story Context + CTA", fill=(15, 15, 15), font=font(24))
    draw.text((20, 54), "Rendered-copy metadata is audited after Phase 6M asset downgrades.", fill=(70, 70, 70), font=font(13))
    for index, row in enumerate(rows):
        col = index % columns
        row_index = index // columns
        x0 = 15 + col * cell_w
        y0 = header_h + row_index * cell_h
        path = Path(clean(row.get("output_path")))
        if path.exists():
            image = Image.open(path).convert("RGB")
            image.thumbnail((320, 410), Image.Resampling.LANCZOS)
            sheet.paste(image, (x0 + (320 - image.width) // 2 + 10, y0 + 4))
        status = clean(row.get("validation_status"))
        color = (10, 105, 45) if status == "passed_story_context_cta_validation" else (160, 55, 25)
        draw.text((x0 + 10, y0 + 418), f"{index + 1}. {status}", fill=color, font=font(12))
        draw.text((x0 + 10, y0 + 440), clean(row.get("headline"))[:52], fill=(30, 30, 30), font=font(11))
        draw.text((x0 + 10, y0 + 461), clean(row.get("context_segments"))[:52], fill=(55, 55, 55), font=font(11))
        draw.text((x0 + 10, y0 + 482), clean(row.get("story_prompt"))[:52], fill=(75, 75, 75), font=font(11))
    CONTACT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT, quality=92)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    manifest = read_json(MANIFEST)
    policy = read_json(POLICY)
    blockers: List[str] = []
    warnings: List[str] = []
    if manifest.get("version") != RENDERER_VERSION:
        blockers.append("renderer_not_phase6k_v4_6")
    items = manifest.get("items") if isinstance(manifest.get("items"), list) else []
    forbidden = [clean(value) for value in policy.get("forbidden_live_copy_tokens") or []]
    rendered_copy_failures = []
    for item in items:
        reasons = validate_rendered_copy(item, forbidden)
        if reasons:
            rendered_copy_failures.append({"item_id": item.get("item_id"), "reasons": reasons})
    if rendered_copy_failures:
        blockers.append("rendered_copy_audit_failures_present")

    minimum_score = as_float(policy.get("minimum_story_cta_score") or 0.95)
    rows = [validate_story(item, minimum_score) for item in items if clean(item.get("template_id")) == STORY_TEMPLATE]
    if not rows:
        blockers.append("no_story_rows")
    failed = [row for row in rows if row.get("validation_status") != "passed_story_context_cta_validation"]
    if failed:
        blockers.append("story_context_cta_failures_present")
    status = "passed_story_context_cta" if not blockers else "blocked_story_context_cta"
    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "renderer_version": manifest.get("version"),
        "rendered_rows": len(items),
        "rendered_copy_failure_count": len(rendered_copy_failures),
        "story_rows": len(rows),
        "passed_story_rows": len(rows) - len(failed),
        "failed_story_rows": len(failed),
        "minimum_story_cta_score": minimum_score,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "rendered_copy_failures": rendered_copy_failures,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CSV, rows, FIELDS)
    build_contact(rows)
    lines = [
        "# HSD Phase 6M Story Context + CTA Gate",
        "",
        f"Status: `{status}`",
        f"Rendered rows audited: `{len(items)}`",
        f"Rendered-copy failures: `{len(rendered_copy_failures)}`",
        f"Story rows: `{len(rows)}`",
        f"Passed Story rows: `{len(rows) - len(failed)}`",
        f"Failed Story rows: `{len(failed)}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report["warnings"]] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["version", "status", "rendered_rows", "rendered_copy_failure_count", "story_rows", "passed_story_rows", "failed_story_rows", "blockers"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
