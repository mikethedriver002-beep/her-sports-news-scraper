from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Tuple

from hsd_run_io import output_path, write_csv, write_json, write_text

try:
    from PIL import Image, ImageChops, ImageFilter, ImageStat
except Exception:  # pragma: no cover - surfaced in manifest
    Image = None
    ImageChops = None
    ImageFilter = None
    ImageStat = None


VERSION = "hsd-render-visual-delta-v1.1.0-manual-revision-plan"
PROJECT_ROOT = Path(__file__).resolve().parent
OUT_MD = output_path("render_visual_delta_report.md")
OUT_CSV = output_path("render_visual_delta.csv")
OUT_JSON = output_path("render_visual_delta_manifest.json")
OUT_REVISION_MD = output_path("render_visual_revision_plan.md")
OUT_REVISION_CSV = output_path("render_visual_revision_plan.csv")
OUT_REVISION_JSON = output_path("render_visual_revision_plan.json")

CSV_FIELDS = [
    "format_id",
    "reference_kind",
    "drift_band",
    "comparison_status",
    "draft_path",
    "reference_path",
    "reference_exists",
    "reference_exact_format_match",
    "reference_visual_delta_score",
    "overall_delta",
    "edge_delta",
    "structure_delta",
    "worst_zone",
    "zone_warnings",
    "next_step",
    "approval_policy",
]

REVISION_FIELDS = [
    "format_id",
    "revision_priority",
    "revision_status",
    "reference_visual_delta_score",
    "drift_band",
    "worst_zone",
    "revision_focus",
    "specific_manual_revisions",
    "inspect_first",
    "hold_or_revise_cue",
    "approval_policy",
]

Zone = Tuple[int, int, int, int]

FALLBACK_ZONES = {
    "ig_feed_4x5": {
        "title": (0.055, 0.090, 0.945, 0.215),
        "context_row": (0.055, 0.245, 0.945, 0.300),
        "score_lane": (0.050, 0.315, 0.950, 0.700),
        "lower_modules": (0.055, 0.710, 0.945, 0.955),
        "footer_guardrail": (0.050, 0.955, 0.950, 0.985),
    },
    "ig_story_9x16": {
        "title": (0.070, 0.080, 0.930, 0.180),
        "context_row": (0.070, 0.195, 0.930, 0.245),
        "score_lane": (0.070, 0.255, 0.930, 0.595),
        "lower_modules": (0.070, 0.635, 0.930, 0.870),
        "footer_guardrail": (0.050, 0.940, 0.950, 0.980),
    },
    "square_feed_1x1": {
        "title": (0.055, 0.110, 0.945, 0.285),
        "context_row": (0.055, 0.300, 0.945, 0.365),
        "score_lane": (0.050, 0.385, 0.950, 0.780),
        "lower_modules": (0.055, 0.790, 0.945, 0.935),
        "footer_guardrail": (0.050, 0.935, 0.950, 0.985),
    },
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def repo_root() -> Path:
    return PROJECT_ROOT


def input_candidates(relative: str | Path) -> List[Path]:
    path = Path(relative)
    if path.is_absolute():
        return [path]
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / path)
    candidates.append(Path.cwd() / path)
    candidates.append(repo_root() / path)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / path)
    return candidates


def first_existing(relative: Any) -> Path | None:
    text = clean(relative)
    if not text:
        return None
    for candidate in input_candidates(text):
        if candidate.exists():
            return candidate
    return input_candidates(text)[0]


def read_json(path: Any) -> Dict[str, Any]:
    candidate = first_existing(path)
    if not candidate or not candidate.exists():
        return {}
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8", errors="replace"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def ratio_box(image_size: Tuple[int, int], ratios: Tuple[float, float, float, float]) -> Zone:
    width, height = image_size
    left = max(0, min(width - 1, int(width * ratios[0])))
    top = max(0, min(height - 1, int(height * ratios[1])))
    right = max(left + 1, min(width, int(width * ratios[2])))
    bottom = max(top + 1, min(height, int(height * ratios[3])))
    return left, top, right, bottom


def spec_zone_boxes(spec: Dict[str, Any], image_size: Tuple[int, int], format_id: str) -> Dict[str, Zone]:
    zones = spec.get("zones") if isinstance(spec.get("zones"), dict) else {}
    canvas = spec.get("canvas") if isinstance(spec.get("canvas"), dict) else {}
    canvas_w = float(canvas.get("width") or image_size[0])
    canvas_h = float(canvas.get("height") or image_size[1])
    sx = image_size[0] / canvas_w if canvas_w else 1.0
    sy = image_size[1] / canvas_h if canvas_h else 1.0

    def scaled_box(names: Iterable[str]) -> Zone | None:
        boxes: List[Zone] = []
        for name in names:
            raw = zones.get(name) if isinstance(zones.get(name), dict) else {}
            if not raw:
                continue
            x = int(float(raw.get("x", 0)) * sx)
            y = int(float(raw.get("y", 0)) * sy)
            w = int(float(raw.get("w", 0)) * sx)
            h = int(float(raw.get("h", 0)) * sy)
            boxes.append((x, y, x + w, y + h))
        if not boxes:
            return None
        left = max(0, min(box[0] for box in boxes))
        top = max(0, min(box[1] for box in boxes))
        right = min(image_size[0], max(box[2] for box in boxes))
        bottom = min(image_size[1], max(box[3] for box in boxes))
        return (left, top, max(left + 1, right), max(top + 1, bottom))

    mapped = {
        "title": scaled_box(["title"]),
        "context_row": scaled_box(["context_row"]),
        "score_lane": scaled_box(["primary_logo_slot", "primary_team", "primary_score", "secondary_logo_slot", "secondary_team", "secondary_score"]),
        "lower_modules": scaled_box(["key_performer", "hook_takeaway", "hook_question"]),
    }
    fallback = FALLBACK_ZONES.get(format_id, FALLBACK_ZONES["ig_feed_4x5"])
    return {
        key: value if value else ratio_box(image_size, fallback[key])
        for key, value in mapped.items()
        if key in fallback
    } | {"footer_guardrail": ratio_box(image_size, fallback["footer_guardrail"])}


def mean_abs_delta(left: Any, right: Any) -> float:
    diff = ImageChops.difference(left.convert("RGB"), right.convert("RGB"))
    stat = ImageStat.Stat(diff)
    return mean(stat.mean) / 255.0


def edge_delta(left: Any, right: Any) -> float:
    left_edges = left.convert("L").filter(ImageFilter.FIND_EDGES)
    right_edges = right.convert("L").filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(ImageChops.difference(left_edges, right_edges)).mean[0]) / 255.0


def bright_ratio(image: Any) -> float:
    gray = image.convert("L")
    data = gray.tobytes()
    return sum(1 for value in data if value >= 190) / len(data) if data else 0.0


def zone_delta(draft: Any, reference: Any, box: Zone) -> float:
    draft_crop = draft.crop(box)
    reference_crop = reference.crop(box)
    color = mean_abs_delta(draft_crop, reference_crop)
    edge = edge_delta(draft_crop, reference_crop)
    bright = abs(bright_ratio(draft_crop) - bright_ratio(reference_crop))
    return (color * 0.50) + (edge * 0.35) + (bright * 0.15)


def drift_band(overall: float, edge: float, structure: float, reference_kind: str, exact: bool) -> str:
    score = visual_delta_score(overall, edge, structure, reference_kind, exact)
    if score >= 90:
        return "aligned_to_reference"
    if score >= 80:
        return "review_minor_drift"
    return "manual_drift_warning"


def visual_delta_score(overall: float, edge: float, structure: float, reference_kind: str, exact: bool) -> int:
    tolerance_bonus = 5 if reference_kind == "layout" else 0
    exact_bonus = 3 if exact else -3
    penalty = int(round((overall * 35) + (edge * 25) + (structure * 40)))
    return max(0, min(100, 100 - penalty + tolerance_bonus + exact_bonus))


def compare_to_reference(option: Dict[str, Any], reference_kind: str) -> Dict[str, Any]:
    format_id = clean(option.get("format_id")) or "unknown_format"
    reference_key = "reference_public_mockup_path" if reference_kind == "public_mockup" else "reference_layout_path"
    draft_path = first_existing(option.get("path"))
    reference_path = first_existing(option.get(reference_key))
    exact = option.get("reference_exact_format_match") is True

    base = {
        "format_id": format_id,
        "reference_kind": reference_kind,
        "draft_path": clean(option.get("path")),
        "reference_path": clean(option.get(reference_key)),
        "reference_exists": bool(reference_path and reference_path.exists()),
        "reference_exact_format_match": exact,
        "approval_policy": "review-only warning; does not approve, publish, move files, or mark publish-ready",
    }
    if Image is None or ImageChops is None or ImageFilter is None or ImageStat is None:
        return {
            **base,
            "drift_band": "not_scored_dependency_missing",
            "comparison_status": "manual_review_required",
            "reference_visual_delta_score": "0",
            "overall_delta": "",
            "edge_delta": "",
            "structure_delta": "",
            "worst_zone": "not_scored",
            "zone_warnings": "Pillow image analysis unavailable.",
            "next_step": "Open draft and references manually before any decision.",
        }
    if not draft_path or not draft_path.exists():
        return {
            **base,
            "drift_band": "not_scored_missing_draft",
            "comparison_status": "manual_review_required",
            "reference_visual_delta_score": "0",
            "overall_delta": "",
            "edge_delta": "",
            "structure_delta": "",
            "worst_zone": "missing_draft",
            "zone_warnings": "Draft image missing.",
            "next_step": "Run .\\hsd.cmd run -Mode render, then review visual delta again.",
        }
    if not reference_path or not reference_path.exists():
        return {
            **base,
            "drift_band": "not_scored_missing_reference",
            "comparison_status": "manual_review_required",
            "reference_visual_delta_score": "0",
            "overall_delta": "",
            "edge_delta": "",
            "structure_delta": "",
            "worst_zone": "missing_reference",
            "zone_warnings": f"{reference_kind} reference image missing.",
            "next_step": "Open the draft manually; reference-pack comparison is unavailable.",
        }

    draft = Image.open(draft_path).convert("RGB")
    reference = Image.open(reference_path).convert("RGB")
    if reference.size != draft.size:
        reference = reference.resize(draft.size)
    spec = read_json(option.get("reference_spec_path"))
    zones = spec_zone_boxes(spec, draft.size, format_id)
    zone_scores = {zone_id: zone_delta(draft, reference, box) for zone_id, box in zones.items()}
    overall = mean_abs_delta(draft, reference)
    edges = edge_delta(draft, reference)
    structure = mean(zone_scores.values()) if zone_scores else overall
    worst_zone = max(zone_scores.items(), key=lambda item: item[1])[0] if zone_scores else "overall"
    warning_zones = [zone_id for zone_id, score in zone_scores.items() if score >= 0.315]
    band = drift_band(overall, edges, structure, reference_kind, exact)
    score = visual_delta_score(overall, edges, structure, reference_kind, exact)
    status = "reference_aligned_review" if band == "aligned_to_reference" else "manual_review_warning"
    if band == "review_minor_drift":
        next_step = "Compare draft, public mockup, and layout reference by eye before recording a manual decision."
    elif band == "manual_drift_warning":
        next_step = "Hold or revise if the highlighted zones drift from the approved template intent."
    else:
        next_step = "Reference comparison looks aligned enough for human visual review; still not approved."
    return {
        **base,
        "drift_band": band,
        "comparison_status": status,
        "reference_visual_delta_score": str(score),
        "overall_delta": f"{overall:.3f}",
        "edge_delta": f"{edges:.3f}",
        "structure_delta": f"{structure:.3f}",
        "worst_zone": worst_zone,
        "zone_warnings": ", ".join(warning_zones) or "none",
        "next_step": next_step,
        "zone_scores": {key: f"{value:.3f}" for key, value in zone_scores.items()},
    }


def summarize_format(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    order = {"manual_drift_warning": 3, "review_minor_drift": 2, "aligned_to_reference": 1}
    scored = [row for row in rows if clean(row.get("format_id"))]
    if not scored:
        return {}
    worst = max(scored, key=lambda row: order.get(clean(row.get("drift_band")), 4))
    warnings = [
        f"{row['reference_kind']}: {row['drift_band']} ({row['worst_zone']})"
        for row in scored
        if clean(row.get("drift_band")) != "aligned_to_reference"
    ]
    return {
        "format_id": clean(worst.get("format_id")),
        "drift_band": clean(worst.get("drift_band")),
        "comparison_status": clean(worst.get("comparison_status")),
        "reference_visual_delta_score": clean(worst.get("reference_visual_delta_score")),
        "worst_zone": clean(worst.get("worst_zone")),
        "warning_count": len(warnings),
        "warning_summary": "; ".join(warnings) or "Reference comparison aligned enough for human review.",
        "next_step": clean(worst.get("next_step")),
    }


def zone_revision_focus(zone: str, format_id: str) -> Dict[str, str]:
    if zone == "title":
        return {
            "revision_focus": "Title hierarchy and safe-zone fit",
            "specific_manual_revisions": (
                "Compare headline placement against the public mockup; tighten line breaks, reduce title scale by 4-8% if it crowds the top, "
                "and keep the headline inside the approved title block before changing any other module."
            ),
        }
    if zone == "score_lane":
        return {
            "revision_focus": "Score/team lane balance",
            "specific_manual_revisions": (
                "Rebalance logo, team name, and score columns against the layout reference; keep scores dominant, align team labels to the "
                "same baseline, and preserve enough gap between logo slots and score panels."
            ),
        }
    if zone == "context_row":
        return {
            "revision_focus": "Context row spacing",
            "specific_manual_revisions": (
                "Shorten context copy, keep it on one clean row where possible, and restore the vertical gap between title and score lane."
            ),
        }
    if zone == "lower_modules":
        return {
            "revision_focus": "Lower module rhythm",
            "specific_manual_revisions": (
                "Compress GAME EDGE/YOUR TAKE copy, align module headers to the reference grid, and keep the lower cards from pushing into the footer guardrail."
            ),
        }
    if zone == "footer_guardrail":
        return {
            "revision_focus": "Draft footer and guardrail strip",
            "specific_manual_revisions": (
                "Verify the red draft footer remains visible, uncropped, and separated from content; do not remove draft-only guardrails."
            ),
        }
    if format_id == "square_feed_1x1":
        return {
            "revision_focus": "Square crop derivation",
            "specific_manual_revisions": (
                "Treat square as a derived crop; compare against both 4x5 references, then manually rebalance title and score lane for the shorter canvas."
            ),
        }
    return {
        "revision_focus": "Template alignment review",
        "specific_manual_revisions": (
            "Open the draft beside the public mockup and layout reference; adjust the most visibly drifted block before recording a decision."
        ),
    }


def revision_priority(score: str, band: str) -> str:
    try:
        numeric = int(score)
    except Exception:
        numeric = 0
    if band.startswith("not_scored") or numeric < 80:
        return "revise_before_manual_next_step"
    if numeric < 90:
        return "inspect_before_decision"
    return "reference_check_only"


def build_revision_plan(summaries: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for format_id in ["ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"]:
        summary = summaries.get(format_id, {})
        if not summary:
            continue
        score = clean(summary.get("reference_visual_delta_score")) or "0"
        band = clean(summary.get("drift_band")) or "not_scored"
        zone = clean(summary.get("worst_zone")) or "overall"
        focus = zone_revision_focus(zone, format_id)
        priority = revision_priority(score, band)
        if priority == "reference_check_only":
            cue = "Open references and confirm by eye; no automated approval is implied."
            status = "manual_reference_check"
        elif priority == "inspect_before_decision":
            cue = "Inspect the named zone before choosing approve, hold, or revise."
            status = "manual_inspection_recommended"
        else:
            cue = "Hold or revise this draft if the named zone visibly drifts from the reference."
            status = "manual_revision_recommended"
        rows.append(
            {
                "format_id": format_id,
                "revision_priority": priority,
                "revision_status": status,
                "reference_visual_delta_score": score,
                "drift_band": band,
                "worst_zone": zone,
                "revision_focus": focus["revision_focus"],
                "specific_manual_revisions": focus["specific_manual_revisions"],
                "inspect_first": (
                    "Open draft, public mockup, layout reference, then compare the named zone before changing copy or assets."
                ),
                "hold_or_revise_cue": cue,
                "approval_policy": "review-only manual guidance; does not approve, publish, move files, or mark publish-ready",
            }
        )
    return rows


def report_lines(manifest: Dict[str, Any], rows: List[Dict[str, Any]]) -> List[str]:
    lines = [
        "# HSD Render Visual Delta Report",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Guardrails",
        "",
        "- Review-only reference comparison.",
        "- Does not approve drafts.",
        "- Does not publish, move files, or create a publish-ready lane.",
        "- Does not call paid APIs.",
        "",
        "## Comparisons",
        "",
    ]
    if not rows:
        lines.append("- No render format options found.")
        return lines
    for row in rows:
        lines.append(
            f"- `{row['format_id']}` vs `{row['reference_kind']}`: `{row['drift_band']}` "
            f"score={row.get('reference_visual_delta_score') or '0'} "
            f"overall={row['overall_delta'] or 'n/a'} edge={row['edge_delta'] or 'n/a'} "
            f"structure={row['structure_delta'] or 'n/a'} worst_zone=`{row['worst_zone']}` "
            f"warnings={row['zone_warnings'] or 'none'}."
        )
    lines.extend(
        [
            "",
            "## Stop/Go Cue",
            "",
            "Use this report as a warning layer only. If drift is visible in the draft, hold or revise in the manual Decision tab.",
        ]
    )
    return lines


def revision_report_lines(manifest: Dict[str, Any], rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "# HSD Render Visual Revision Plan",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Guardrails",
        "",
        "- Manual revision guidance only.",
        "- Does not approve drafts.",
        "- Does not publish, move files, or create a publish-ready lane.",
        "- Does not call paid APIs.",
        "",
        "## Recommended Manual Revisions",
        "",
    ]
    if not rows:
        lines.append("- No revision rows found. Run render mode after creating draft renders.")
        return lines
    for row in rows:
        lines.extend(
            [
                f"### {row['format_id']}",
                "",
                f"- Priority: `{row['revision_priority']}`",
                f"- Score: `{row['reference_visual_delta_score']}/100`",
                f"- Drift band: `{row['drift_band']}`",
                f"- Worst zone: `{row['worst_zone']}`",
                f"- Focus: {row['revision_focus']}",
                f"- Manual revision: {row['specific_manual_revisions']}",
                f"- Inspect first: {row['inspect_first']}",
                f"- Cue: {row['hold_or_revise_cue']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Stop/Go Cue",
            "",
            "Use this plan to decide whether to revise the draft manually. It is not an approval, staging, movement, or publishing instruction.",
        ]
    )
    return lines


def main() -> None:
    renderer = read_json("manual_review_renderer_manifest.json")
    options = renderer.get("format_options") if isinstance(renderer.get("format_options"), list) else []
    rows: List[Dict[str, Any]] = []
    for option in options:
        if not isinstance(option, dict):
            continue
        rows.append(compare_to_reference(option, "public_mockup"))
        rows.append(compare_to_reference(option, "layout"))

    summaries: Dict[str, Dict[str, Any]] = {}
    for format_id in sorted({clean(row.get("format_id")) for row in rows if clean(row.get("format_id"))}):
        summaries[format_id] = summarize_format([row for row in rows if clean(row.get("format_id")) == format_id])
    warning_count = sum(1 for row in rows if clean(row.get("drift_band")) not in {"", "aligned_to_reference"})
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "visual_delta_review_ready" if rows else "visual_delta_not_scored",
        "approval_status": "not_approved_human_review_required",
        "summary": {
            "comparison_count": len(rows),
            "warning_count": warning_count,
            "human_decision_required": True,
        },
        "format_summaries": summaries,
        "comparisons": rows,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    revision_rows = build_revision_plan(summaries)
    revision_manifest = {
        "version": VERSION,
        "generated_at_utc": manifest["generated_at_utc"],
        "status": "manual_revision_plan_ready" if revision_rows else "manual_revision_plan_not_scored",
        "approval_status": "not_approved_human_review_required",
        "summary": {
            "revision_count": len(revision_rows),
            "revise_before_manual_next_step_count": sum(
                1 for row in revision_rows if row["revision_priority"] == "revise_before_manual_next_step"
            ),
            "inspect_before_decision_count": sum(
                1 for row in revision_rows if row["revision_priority"] == "inspect_before_decision"
            ),
            "human_decision_required": True,
        },
        "revision_rows": revision_rows,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_json(OUT_JSON, manifest)
    write_csv(OUT_CSV, rows, CSV_FIELDS)
    write_text(OUT_MD, "\n".join(report_lines(manifest, rows)))
    write_json(OUT_REVISION_JSON, revision_manifest)
    write_csv(OUT_REVISION_CSV, revision_rows, REVISION_FIELDS)
    write_text(OUT_REVISION_MD, "\n".join(revision_report_lines(revision_manifest, revision_rows)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
