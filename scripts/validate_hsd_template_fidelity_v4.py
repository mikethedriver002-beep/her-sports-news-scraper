from __future__ import annotations

import argparse
import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

VERSION = "v1.0-phase6c-template-fidelity-gate"
MATRIX = Path("config/graphics/v4/fidelity/template_fidelity_matrix_v4.json")
RENDERER_ROOT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4")
RENDER_MANIFEST_CSV = RENDERER_ROOT / "hsd_template_renderer_v4_manifest.csv"
REPORT_JSON = Path("template_fidelity_v4_report.json")
REPORT_MD = Path("template_fidelity_v4_report.md")
FIDELITY_DIR = RENDERER_ROOT / "fidelity"
CONTACT_SHEET = FIDELITY_DIR / "template_fidelity_v4_contact_sheet.jpg"
DIFF_SHEET = FIDELITY_DIR / "template_fidelity_v4_diff_sheet.jpg"
COMPARISON_DIR = FIDELITY_DIR / "comparisons"
CSV_REPORT = FIDELITY_DIR / "template_fidelity_v4_rows.csv"

ROW_FIELDS = [
    "template_id", "platform", "headline", "render_path", "baseline_path", "layout_reference_path",
    "dimensions_ok", "structure_score", "tone_score", "edge_similarity", "dark_ratio_delta",
    "palette_distance", "overall_score", "fidelity_status", "reasons", "comparison_path", "diff_path"
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "item"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def resolve_path(raw: str) -> Path:
    path = Path(clean(raw))
    if path.exists():
        return path
    return Path.cwd() / path


def open_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def fit_to(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    if image.size == size:
        return image.convert("RGB")
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def gray_thumb(image: Image.Image, size: Tuple[int, int] = (96, 96)) -> Image.Image:
    return image.convert("L").resize(size, Image.Resampling.BILINEAR)


def mean_abs_diff(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a, b).convert("L")
    return float(ImageStat.Stat(diff).mean[0])


def tone_score(render: Image.Image, baseline: Image.Image) -> float:
    diff = mean_abs_diff(gray_thumb(render), gray_thumb(baseline))
    return max(0.0, min(1.0, 1.0 - diff / 255.0))


def edge_hist(image: Image.Image, grid: int = 12) -> List[float]:
    edge = image.convert("L").filter(ImageFilter.FIND_EDGES).resize((grid, grid), Image.Resampling.BILINEAR)
    pixels = [float(p) for p in edge.getdata()]
    total = sum(pixels) or 1.0
    return [p / total for p in pixels]


def edge_similarity(render: Image.Image, baseline: Image.Image) -> float:
    a = edge_hist(render)
    b = edge_hist(baseline)
    return max(0.0, min(1.0, sum(min(x, y) for x, y in zip(a, b))))


def dark_ratio(image: Image.Image) -> float:
    thumb = image.convert("L").resize((128, 128), Image.Resampling.BILINEAR)
    data = list(thumb.getdata())
    return sum(1 for p in data if p < 85) / max(1, len(data))


def dominant_colors(image: Image.Image, colors: int = 8) -> List[Tuple[int, int, int]]:
    small = image.convert("RGB").resize((96, 96), Image.Resampling.BILINEAR)
    quantized = small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    ranked = quantized.getcolors(96 * 96) or []
    ranked.sort(reverse=True)
    return [color for _count, color in ranked[:colors]]


def color_distance(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def palette_distance(render: Image.Image, baseline: Image.Image) -> float:
    render_colors = dominant_colors(render)
    baseline_colors = dominant_colors(baseline)
    if not render_colors or not baseline_colors:
        return 999.0
    distances = [min(color_distance(rc, bc) for bc in baseline_colors) for rc in render_colors[:5]]
    return sum(distances) / len(distances)


def structure_score(render: Image.Image, baseline: Image.Image) -> float:
    tone = tone_score(render, baseline)
    edge = edge_similarity(render, baseline)
    dark_delta = abs(dark_ratio(render) - dark_ratio(baseline))
    palette = palette_distance(render, baseline)
    palette_component = max(0.0, 1.0 - palette / 255.0)
    dark_component = max(0.0, 1.0 - dark_delta)
    return max(0.0, min(1.0, edge * 0.45 + tone * 0.20 + palette_component * 0.20 + dark_component * 0.15))


def diff_image(render: Image.Image, baseline: Image.Image) -> Image.Image:
    diff = ImageChops.difference(render.convert("RGB"), baseline.convert("RGB"))
    enhanced = diff.convert("L").point(lambda p: min(255, int(p * 2.5)))
    return Image.merge("RGB", (enhanced, enhanced.point(lambda p: int(p * 0.25)), enhanced.point(lambda p: int(p * 0.1))))


def label(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str) -> None:
    font = ImageFont.load_default()
    x, y = xy
    draw.rectangle((x - 4, y - 2, x + len(text) * 7 + 6, y + 15), fill=(5, 7, 12))
    draw.text((x, y), text, fill=(255, 255, 255), font=font)


def make_comparison(render: Image.Image, baseline: Image.Image, diff: Image.Image, title: str, path: Path) -> None:
    thumb_h = 460 if render.height > render.width else 380
    target_w = 300
    pieces = []
    for im in [baseline, render, diff]:
        thumb = ImageOps.contain(im.convert("RGB"), (target_w, thumb_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (target_w, thumb_h), (18, 20, 30))
        canvas.paste(thumb, ((target_w - thumb.width) // 2, (thumb_h - thumb.height) // 2))
        pieces.append(canvas)
    out = Image.new("RGB", (target_w * 3 + 60, thumb_h + 96), (8, 10, 16))
    draw = ImageDraw.Draw(out)
    draw.text((24, 16), title[:92], fill=(255, 255, 255), font=ImageFont.load_default())
    for idx, piece in enumerate(pieces):
        x = 20 + idx * (target_w + 10)
        out.paste(piece, (x, 58))
    label(draw, (30, 64), "APPROVED BASELINE")
    label(draw, (340, 64), "RENDER V4")
    label(draw, (650, 64), "DIFF")
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, quality=92)


def sheet(rows: List[Dict[str, Any]], key: str, path: Path, title: str) -> None:
    images = []
    for row in rows:
        p = Path(clean(row.get(key)))
        if p.exists():
            images.append((row, p))
    if not images:
        return
    cols = 2
    cell_w = 520
    cell_h = 430
    width = cols * cell_w + 50
    height = 90 + math.ceil(len(images) / cols) * cell_h
    out = Image.new("RGB", (width, height), (8, 10, 16))
    draw = ImageDraw.Draw(out)
    draw.text((24, 24), title, fill=(255, 255, 255), font=ImageFont.load_default())
    for idx, (row, p) in enumerate(images):
        col = idx % cols
        line = idx // cols
        x = 24 + col * cell_w
        y = 72 + line * cell_h
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((480, 340), Image.Resampling.LANCZOS)
            out.paste(im, (x + (480 - im.width) // 2, y))
        except Exception:
            pass
        text = f"{row.get('template_id')} | {row.get('platform')} | {row.get('fidelity_status')} | {row.get('overall_score')}"
        draw.text((x, y + 350), text[:74], fill=(225, 230, 240), font=ImageFont.load_default())
        draw.text((x, y + 370), clean(row.get("headline"))[:74], fill=(170, 178, 194), font=ImageFont.load_default())
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, quality=92)


def evaluate_row(row: Dict[str, str], template_info: Dict[str, Any], matrix: Dict[str, Any]) -> Dict[str, Any]:
    render_path = resolve_path(row.get("output_path") or row.get("render_path") or "")
    baseline_path = resolve_path(template_info.get("baseline", ""))
    layout_path = resolve_path(template_info.get("layout_reference", ""))
    reasons: List[str] = []
    if not render_path.exists():
        reasons.append("render_missing")
    if not baseline_path.exists():
        reasons.append("baseline_missing")
    if not layout_path.exists():
        reasons.append("layout_reference_missing")
    if reasons:
        return {**row, "render_path": render_path.as_posix(), "baseline_path": baseline_path.as_posix(), "layout_reference_path": layout_path.as_posix(), "dimensions_ok": False, "structure_score": 0, "tone_score": 0, "edge_similarity": 0, "dark_ratio_delta": 1, "palette_distance": 999, "overall_score": 0, "fidelity_status": "blocked_missing_input", "reasons": ";".join(reasons), "comparison_path": "", "diff_path": ""}
    render = open_rgb(render_path)
    baseline = fit_to(open_rgb(baseline_path), render.size)
    dimensions_ok = render.size == baseline.size
    tone = tone_score(render, baseline)
    edge = edge_similarity(render, baseline)
    dark_delta = abs(dark_ratio(render) - dark_ratio(baseline))
    palette = palette_distance(render, baseline)
    structure = structure_score(render, baseline)
    overall = structure
    thresholds = matrix.get("thresholds", {})
    if not dimensions_ok:
        reasons.append("dimension_mismatch")
    if structure < float(thresholds.get("minimum_structure_score", 0.38)):
        reasons.append("structure_score_below_threshold")
    if tone < float(thresholds.get("minimum_tone_score", 0.40)):
        reasons.append("tone_score_below_threshold")
    if edge < float(thresholds.get("minimum_edge_similarity", 0.30)):
        reasons.append("edge_similarity_below_threshold")
    if dark_delta > float(thresholds.get("maximum_dark_ratio_delta", 0.38)):
        reasons.append("dark_ratio_delta_above_threshold")
    if palette > float(thresholds.get("maximum_palette_distance", 150.0)):
        reasons.append("palette_distance_above_threshold")
    template_id = clean(row.get("template_id"))
    platform = clean(row.get("platform"))
    headline = clean(row.get("headline"))
    comparison_path = COMPARISON_DIR / f"{slug(template_id)}_{slug(platform)}_{slug(headline)}_comparison.jpg"
    diff_path = COMPARISON_DIR / f"{slug(template_id)}_{slug(platform)}_{slug(headline)}_diff.jpg"
    diff = diff_image(render, baseline)
    make_comparison(render, baseline, diff, f"{template_id} | {platform} | {headline}", comparison_path)
    diff.save(diff_path, quality=92)
    status = "passed_fidelity_gate" if not reasons else "fidelity_review_required"
    return {**row, "render_path": render_path.as_posix(), "baseline_path": baseline_path.as_posix(), "layout_reference_path": layout_path.as_posix(), "dimensions_ok": dimensions_ok, "structure_score": round(structure, 4), "tone_score": round(tone, 4), "edge_similarity": round(edge, 4), "dark_ratio_delta": round(dark_delta, 4), "palette_distance": round(palette, 2), "overall_score": round(overall, 4), "fidelity_status": status, "reasons": ";".join(reasons), "comparison_path": comparison_path.as_posix(), "diff_path": diff_path.as_posix()}


def build_report(rows: List[Dict[str, Any]], matrix: Dict[str, Any]) -> Dict[str, Any]:
    blockers: List[str] = []
    if not rows:
        blockers.append("no_renderer_v4_rows")
    missing_required = []
    required_templates = [tid for tid, data in matrix.get("templates", {}).items() if data.get("phase6b_required")]
    rendered_templates = {clean(row.get("template_id")) for row in rows}
    for template_id in required_templates:
        if template_id not in rendered_templates:
            missing_required.append(template_id)
    if missing_required:
        blockers.append("missing_required_phase6b_template_render")
    hard_blocked = [row for row in rows if row.get("fidelity_status") == "blocked_missing_input"]
    if hard_blocked:
        blockers.append("missing_render_or_baseline_input")
    passed = [row for row in rows if row.get("fidelity_status") == "passed_fidelity_gate"]
    review = [row for row in rows if row.get("fidelity_status") == "fidelity_review_required"]
    production_ready = [row for row in rows if float(row.get("overall_score") or 0) >= float(matrix.get("thresholds", {}).get("production_cutover_minimum_overall_score", 0.72))]
    status = "passed_fidelity_setup" if not blockers else "blocked_fidelity_setup"
    return {"version": VERSION, "generated_at_utc": now_iso(), "status": status, "strict_exit_code": 0 if not blockers else 2, "cutover_allowed": False, "blockers": blockers, "warnings": ["fidelity_review_required_outputs_present"] if review else [], "template_count": len(set(clean(row.get("template_id")) for row in rows)), "rendered_rows": len(rows), "passed_fidelity_gate": len(passed), "fidelity_review_required": len(review), "production_cutover_threshold_met": len(production_ready), "missing_required_templates": missing_required, "thresholds": matrix.get("thresholds", {}), "rows": rows}


def write_markdown(report: Dict[str, Any]) -> None:
    lines = ["# HSD Template Fidelity Gate v4", "", f"Generated: `{report['generated_at_utc']}`", f"Version: `{report['version']}`", f"Status: `{report['status']}`", f"Cutover allowed: `{report['cutover_allowed']}`", "", "## Counts", "", f"- Rendered rows: `{report['rendered_rows']}`", f"- Template count: `{report['template_count']}`", f"- Passed fidelity gate: `{report['passed_fidelity_gate']}`", f"- Needs review: `{report['fidelity_review_required']}`", f"- Production threshold met: `{report['production_cutover_threshold_met']}`", "", "## Blockers", ""]
    lines += [f"- `{b}`" for b in report.get("blockers", [])] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{w}`" for w in report.get("warnings", [])] or ["- None"]
    lines += ["", "## Rows", ""]
    for row in report.get("rows", []):
        lines.append(f"- `{row.get('template_id')}` | `{row.get('platform')}` | score `{row.get('overall_score')}` | `{row.get('fidelity_status')}` | {row.get('reasons') or 'ok'}")
    lines += ["", "## Policy", "", "This gate establishes visual baselines and review evidence. It does not permit production cutover by itself."]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    matrix = read_json(MATRIX)
    template_map = matrix.get("templates", {}) if isinstance(matrix.get("templates"), dict) else {}
    manifest_rows = read_csv(RENDER_MANIFEST_CSV)
    evaluated: List[Dict[str, Any]] = []
    for row in manifest_rows:
        template_id = clean(row.get("template_id"))
        template_info = template_map.get(template_id, {})
        if not template_info:
            evaluated.append({**row, "fidelity_status": "blocked_missing_input", "reasons": "template_missing_from_fidelity_matrix"})
            continue
        evaluated.append(evaluate_row(row, template_info, matrix))
    write_csv(CSV_REPORT, evaluated, ROW_FIELDS)
    sheet(evaluated, "comparison_path", CONTACT_SHEET, "HSD Phase 6C Template Fidelity Comparisons")
    sheet(evaluated, "diff_path", DIFF_SHEET, "HSD Phase 6C Template Fidelity Diffs")
    report = build_report(evaluated, matrix)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print(json.dumps({"version": VERSION, "status": report["status"], "rendered_rows": report["rendered_rows"], "passed_fidelity_gate": report["passed_fidelity_gate"], "review_required": report["fidelity_review_required"], "blockers": report["blockers"]}, indent=2))
    return 2 if args.strict and report.get("blockers") else 0


if __name__ == "__main__":
    raise SystemExit(main())
