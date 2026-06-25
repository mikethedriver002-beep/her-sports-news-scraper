from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple

from hsd_run_io import output_path, write_csv, write_json, write_text

try:
    from PIL import Image, ImageStat
except Exception:  # pragma: no cover - validated by runtime report
    Image = None
    ImageStat = None


VERSION = "hsd-manual-visual-qa-v1.4.0-photo-first-score-readability"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
PREVIEW_NAME = "draft_preview.png"
EXPECTED_SIZE = (1080, 1350)
OUT_REPORT = output_path("manual_visual_qa_report.md")
OUT_MANIFEST = output_path("manual_visual_qa_manifest.json")
OUT_CHECKLIST = output_path("manual_visual_qa_checklist.csv")

Zone = Tuple[int, int, int, int]
TextZoneSpec = Tuple[Zone, float, float]
TEXT_ZONES: Dict[str, TextZoneSpec] = {
    "headline_text_zone": ((50, 130, 1030, 285), 0.18, 850.0),
    "score_team_text_zone": ((280, 420, 1030, 900), 0.08, 800.0),
    "context_text_zone": ((55, 320, 1030, 405), 0.04, 650.0),
    "lower_module_text_zone": ((70, 960, 1010, 1268), 0.045, 700.0),
}
PLAYER_LEDGER_ZONE: Zone = (70, 960, 1010, 1128)
DRAFT_MARK_ZONES: Dict[str, Tuple[Zone, float]] = {
    "top_draft_label_zone": ((710, 74, 1030, 150), 0.025),
    "footer_guardrail_zone": ((54, 1288, 1028, 1318), 0.100),
}

CHECKLIST_FIELDS = [
    "check_id",
    "check_label",
    "qa_result",
    "operator_decision",
    "operator_notes",
    "evidence",
    "approval_policy",
]


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def repo_root() -> Path:
    return Path.cwd().resolve()


def input_candidates(relative: str) -> List[Path]:
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / relative)
    candidates.append(repo_root() / relative)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / relative)
    return candidates


def first_existing(relative: str) -> Path | None:
    for candidate in input_candidates(relative):
        if candidate.exists():
            return candidate
    return None


def read_json(path: Path | None) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def primary_photo_layout_mode(renderer_manifest: Dict[str, Any]) -> str:
    formats = renderer_manifest.get("format_options") if isinstance(renderer_manifest.get("format_options"), list) else []
    primary = next((item for item in formats if isinstance(item, dict) and item.get("primary") is True), formats[0] if formats else {})
    return clean(primary.get("athlete_photo_layout_mode")) if isinstance(primary, dict) else ""


def add_check(checks: List[Dict[str, Any]], check_id: str, label: str, passed: bool, evidence: str, *, result: str | None = None) -> None:
    checks.append(
        {
            "check_id": check_id,
            "check_label": label,
            "qa_result": result or ("pass" if passed else "hold"),
            "passed": bool(passed),
            "operator_decision": "operator_fill_required",
            "operator_notes": "",
            "evidence": evidence,
            "approval_policy": "manual approve/hold required; this report never approves or publishes",
        }
    )


def red_dominance(image: Any, box: Zone) -> float:
    crop = image.crop(box).convert("RGB")
    data = crop.tobytes()
    pixel_count = len(data) // 3
    if not pixel_count:
        return 0.0
    red_pixels = 0
    for idx in range(0, len(data), 3):
        r, g, b = data[idx], data[idx + 1], data[idx + 2]
        if r >= 145 and r > g * 1.45 and r > b * 1.25:
            red_pixels += 1
    return red_pixels / pixel_count


def text_zone_signal(image: Any, box: Zone) -> Dict[str, float]:
    crop = image.crop(box).convert("L")
    stat = ImageStat.Stat(crop)
    avg = float(stat.mean[0])
    variance = float(stat.var[0])
    data = crop.tobytes()
    darkish = sum(1 for value in data if value < 190)
    bright = sum(1 for value in data if value >= 190)
    dark_ratio = darkish / len(data) if data else 0.0
    bright_ratio = bright / len(data) if data else 0.0
    return {"average_luma": avg, "variance": variance, "dark_pixel_ratio": dark_ratio, "bright_pixel_ratio": bright_ratio}


def edge_contrast_ratio(crop: Any) -> float:
    gray = crop.convert("L")
    width, height = gray.size
    data = gray.tobytes()
    if width < 3 or height < 3 or not data:
        return 0.0
    edges = 0
    checks = 0
    for y in range(0, height, 2):
        row = y * width
        for x in range(0, width - 2, 2):
            if abs(data[row + x] - data[row + x + 2]) >= 55:
                edges += 1
            checks += 1
    for y in range(0, height - 2, 2):
        row = y * width
        next_row = (y + 2) * width
        for x in range(0, width, 2):
            if abs(data[row + x] - data[next_row + x]) >= 55:
                edges += 1
            checks += 1
    return edges / checks if checks else 0.0


def title_zone_signal(image: Any, box: Zone) -> Dict[str, Any]:
    crop = image.crop(box).convert("RGB")
    width, height = crop.size
    base = text_zone_signal(image, box)
    data = crop.tobytes()
    pixel_count = len(data) // 3
    if not pixel_count:
        return {
            **base,
            "style": "missing",
            "title_ink_ratio": 0.0,
            "white_ink_ratio": 0.0,
            "gold_ink_ratio": 0.0,
            "dark_ink_ratio": 0.0,
            "edge_contrast_ratio": 0.0,
            "dense_row_count": 0,
            "top_fit_margin": 0,
            "bottom_fit_margin": 0,
            "fit_passed": False,
            "contrast_passed": False,
        }

    light_style = base["average_luma"] >= 150
    foreground_rows: Dict[int, int] = {}
    white_pixels = 0
    gold_pixels = 0
    dark_pixels = 0
    for idx in range(0, len(data), 3):
        r, g, b = data[idx], data[idx + 1], data[idx + 2]
        y = (idx // 3) // width
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        white_ink = luma >= 180 and abs(r - g) < 60 and abs(g - b) < 80
        gold_ink = r >= 170 and g >= 125 and b <= 125 and r >= g >= b
        dark_ink = luma <= 115
        if white_ink:
            white_pixels += 1
        if gold_ink:
            gold_pixels += 1
        if dark_ink:
            dark_pixels += 1
        if (dark_ink if light_style else (white_ink or gold_ink)):
            foreground_rows[y] = foreground_rows.get(y, 0) + 1

    row_threshold = 0.012 if light_style else 0.120
    dense_rows = [row for row, count in foreground_rows.items() if count / width >= row_threshold]
    top_margin = min(dense_rows) if dense_rows else 0
    bottom_margin = height - 1 - max(dense_rows) if dense_rows else 0
    edge_ratio = edge_contrast_ratio(crop)
    white_ratio = white_pixels / pixel_count
    gold_ratio = gold_pixels / pixel_count
    dark_ratio = dark_pixels / pixel_count
    title_ink_ratio = dark_ratio if light_style else white_ratio + gold_ratio
    contrast_passed = (
        base["variance"] >= 850.0 and title_ink_ratio >= 0.015
        if light_style
        else base["variance"] >= 850.0 and title_ink_ratio >= 0.045 and edge_ratio >= 0.025
    )
    fit_passed = bool(dense_rows) if light_style else bool(dense_rows) and top_margin >= 4 and bottom_margin >= 8
    return {
        **base,
        "style": "legacy_light_title" if light_style else "reference_white_gold_title",
        "title_ink_ratio": title_ink_ratio,
        "white_ink_ratio": white_ratio,
        "gold_ink_ratio": gold_ratio,
        "dark_ink_ratio": dark_ratio,
        "edge_contrast_ratio": edge_ratio,
        "dense_row_count": len(dense_rows),
        "top_fit_margin": top_margin,
        "bottom_fit_margin": bottom_margin,
        "fit_passed": fit_passed,
        "contrast_passed": contrast_passed,
    }


def guardrail_checks(renderer_manifest: Dict[str, Any], handoff_manifest: Dict[str, Any]) -> Dict[str, bool]:
    guardrails = renderer_manifest.get("guardrails") if isinstance(renderer_manifest.get("guardrails"), dict) else {}
    handoff_guardrails = handoff_manifest.get("guardrails") if isinstance(handoff_manifest.get("guardrails"), dict) else {}
    return {
        "manual_only": guardrails.get("manual_only") is True,
        "review_only": guardrails.get("review_only") is True or handoff_guardrails.get("review_only") is True,
        "auto_render_off": guardrails.get("auto_render") is False and handoff_guardrails.get("auto_render") is False,
        "auto_publish_off": guardrails.get("auto_publish") is False and handoff_guardrails.get("auto_publish") is False,
        "not_approved": guardrails.get("approved") is False
        and clean(renderer_manifest.get("approval_status")) == "not_approved_human_review_required",
        "paid_apis_off": guardrails.get("paid_apis") is False and handoff_guardrails.get("paid_apis") is False,
    }


def manifest_path_exists(raw_path: Any) -> bool:
    text = clean(raw_path)
    if not text:
        return False
    path = Path(text)
    if path.is_absolute():
        return path.exists()
    return first_existing(text) is not None


def add_renderer_metadata_checks(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any]) -> None:
    selected_template = renderer_manifest.get("selected_template") if isinstance(renderer_manifest.get("selected_template"), dict) else {}
    reference_pack = renderer_manifest.get("reference_pack") if isinstance(renderer_manifest.get("reference_pack"), dict) else {}
    format_options = renderer_manifest.get("format_options") if isinstance(renderer_manifest.get("format_options"), list) else []
    asset_slots = renderer_manifest.get("asset_slots") if isinstance(renderer_manifest.get("asset_slots"), list) else []
    if not selected_template and not format_options and not asset_slots:
        add_check(
            checks,
            "renderer_metadata_available",
            "Renderer metadata available",
            True,
            "No template/format/asset metadata found; older or minimal review preview, so human review remains required.",
            result="pass_human_review_required",
        )
        return
    template_id = clean(selected_template.get("template_id"))
    family = clean(selected_template.get("template_family"))
    pack_id = clean(reference_pack.get("pack_id"))
    add_check(
        checks,
        "template_reference_metadata",
        "Template reference metadata",
        True,
        f"template={template_id or 'missing'}; family={family or 'missing'}; reference_pack={pack_id or 'missing'}.",
        result="pass_human_review_required",
    )

    if format_options:
        required_formats = {"ig_feed_4x5", "ig_story_9x16", "square_feed_1x1"}
        found_formats = {clean(row.get("format_id")) for row in format_options if isinstance(row, dict)}
        missing_formats = sorted(required_formats - found_formats)
        add_check(
            checks,
            "social_format_drafts_present",
            "Review draft social formats",
            not missing_formats,
            f"formats={','.join(sorted(found_formats)) or 'none'}; missing={','.join(missing_formats) or 'none'}.",
        )
    for row in format_options:
        if not isinstance(row, dict):
            continue
        format_id = clean(row.get("format_id")) or "unknown_format"
        render_exists = manifest_path_exists(row.get("path"))
        reference_ok = all(
            row.get(key) is True
            for key in [
                "reference_spec_path_exists",
                "reference_public_mockup_path_exists",
                "reference_layout_path_exists",
            ]
        )
        exact = row.get("reference_exact_format_match") is True
        result = "pass" if render_exists and reference_ok else "hold"
        if render_exists and reference_ok and not exact:
            result = "pass_human_review_required"
        add_check(
            checks,
            f"format_reference_{format_id}",
            f"{format_id} render/reference link",
            render_exists and reference_ok,
            (
                f"render_exists={render_exists}; reference_files={reference_ok}; "
                f"exact_reference_match={exact}; derivation={clean(row.get('reference_derivation')) or 'none'}."
            ),
            result=result,
        )

    logo_slots = [
        slot for slot in asset_slots
        if isinstance(slot, dict) and "team_logo" in clean(slot.get("slot_id"))
    ]
    missing = [slot for slot in logo_slots if "missing" in clean(slot.get("status")) or not clean(slot.get("asset_path"))]
    review = [slot for slot in logo_slots if clean(slot.get("status")) != "approved_logo"]
    detail = "; ".join(
        f"{clean(slot.get('team')) or clean(slot.get('slot_id'))}: {clean(slot.get('status')) or 'review'}"
        for slot in logo_slots
    )
    add_check(
        checks,
        "team_logo_review_status",
        "Team logo registry status",
        not missing,
        detail or "No team logo slots found.",
        result="pass_human_review_required" if review and not missing else ("pass" if logo_slots else "pass_human_review_required"),
    )

    final_score_template = family == "game_recap_final_score" or "final_score" in template_id
    add_check(
        checks,
        "final_score_content_module_review",
        "Final-score content module cue",
        True,
        (
            "Final-score draft should use SCORE-DERIVED EDGE, verified player-stat module, or matchup-specific YOUR TAKE copy; "
            "hold by eye if it falls back to internal source-confidence language or an unsupported player ledger."
            if final_score_template
            else "Non-final-score template; human copy review still required."
        ),
        result="pass_human_review_required",
    )


def add_player_ledger_readability_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any], image: Any | None) -> None:
    content_module = renderer_manifest.get("content_module") if isinstance(renderer_manifest.get("content_module"), dict) else {}
    mode = clean(content_module.get("content_module_mode"))
    status = clean(content_module.get("content_module_status"))
    confidence = clean(content_module.get("stat_source_confidence"))
    player = clean(content_module.get("content_module_player"))
    source_text = clean(content_module.get("content_module_source_text"))
    if mode != "verified_player_stats":
        add_check(
            checks,
            "player_ledger_readability",
            "Player ledger readability",
            True,
            (
                f"Player ledger not expected for content_module={mode or 'missing'}; "
                f"status={status or 'missing'}; fallback={clean(content_module.get('content_module_fallback_label')) or 'n/a'}."
            ),
            result="pass_human_review_required",
        )
        return
    if image is None:
        add_check(
            checks,
            "player_ledger_readability",
            "Player ledger readability",
            False,
            "Verified player-stat module metadata exists, but the preview image was unavailable for ledger-zone analysis.",
        )
        return
    signal = text_zone_signal(image, PLAYER_LEDGER_ZONE)
    passed = signal["variance"] >= 1200.0 and signal["bright_pixel_ratio"] >= 0.035 and signal["dark_pixel_ratio"] >= 0.700
    add_check(
        checks,
        "player_ledger_readability",
        "Player ledger readability",
        passed,
        (
            f"content_module={mode}; confidence={confidence or 'missing'}; player={player or 'missing'}; "
            f"source_text={source_text or 'missing'}; luma avg {signal['average_luma']:.1f}, "
            f"variance {signal['variance']:.1f}, bright pixel ratio {signal['bright_pixel_ratio']:.3f} "
            f"(min 0.035), dark pixel ratio {signal['dark_pixel_ratio']:.3f} (min 0.700) "
            f"in crop {PLAYER_LEDGER_ZONE}."
        ),
    )


def checklist_rows(checks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for check in checks:
        rows.append({field: clean(check.get(field)) for field in CHECKLIST_FIELDS})
    rows.extend(
        [
            {
                "check_id": "operator_visual_review",
                "check_label": "Human readable review",
                "qa_result": "human_required",
                "operator_decision": "operator_fill_required",
                "operator_notes": "",
                "evidence": "Open draft_preview.png and confirm headline, dek, context, watermark, and crop safety by eye.",
                "approval_policy": "Allowed decisions: approve_for_manual_next_step, hold, revise. No automatic approval.",
            },
            {
                "check_id": "operator_publish_guard",
                "check_label": "Publishing guard",
                "qa_result": "human_required",
                "operator_decision": "operator_fill_required",
                "operator_notes": "",
                "evidence": "Confirm the preview remains a draft and is not moved to a publish-ready lane.",
                "approval_policy": "This checklist is not a publishing instruction.",
            },
        ]
    )
    return rows


def report_lines(manifest: Dict[str, Any], checks: List[Dict[str, Any]], preview_path: Path | None) -> List[str]:
    fail_count = sum(1 for check in checks if not check.get("passed"))
    lines = [
        "# HSD Manual Visual QA Report",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{manifest['status']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "## Guardrails",
        "",
        "- Manual-only report.",
        "- Review-only draft preview check.",
        "- Does not approve the preview.",
        "- Does not publish or mark anything publish-ready.",
        "- Does not call paid APIs.",
        "",
        "## Preview",
        "",
        f"- File: `{preview_path.as_posix() if preview_path else 'missing'}`",
        f"- Dimensions: `{manifest.get('dimensions', {}).get('width', 0)}x{manifest.get('dimensions', {}).get('height', 0)}`",
        f"- Automated hold count: `{fail_count}`",
        "",
        "## Automated Checks",
        "",
    ]
    for check in checks:
        status = "PASS" if check.get("passed") else "HOLD"
        lines.append(f"- `{status}` {check['check_label']}: {check['evidence']}")
    lines.extend(
        [
            "",
            "## Human Approve/Hold Checklist",
            "",
            "Open `manual_visual_qa_checklist.csv` and fill `operator_decision` for each row.",
            "Use only `approve_for_manual_next_step`, `hold`, or `revise`; this generator never fills those decisions for you.",
            "",
            "## Stop/Go Rule",
            "",
            "- Stop if any automated check is HOLD.",
            "- Stop if the draft watermark or footer guardrail is missing.",
            "- Stop if the text is unreadable, cropped, misleading, or not source-safe.",
            "- Continue only after a human records the decision in a later manual approval intake.",
            "",
        ]
    )
    return lines


def main() -> None:
    preview_path = first_existing(f"{HANDOFF_DIR_NAME}/{PREVIEW_NAME}")
    renderer_manifest_path = first_existing("manual_review_renderer_manifest.json")
    handoff_manifest_path = first_existing(f"{HANDOFF_DIR_NAME}/handoff_manifest.json")
    renderer_manifest = read_json(renderer_manifest_path)
    handoff_manifest = read_json(handoff_manifest_path)
    checks: List[Dict[str, Any]] = []
    dimensions = {"width": 0, "height": 0}

    if Image is None or ImageStat is None:
        add_check(checks, "pillow_available", "Image analysis dependency", False, "Pillow is unavailable; visual QA could not inspect pixels.")
    elif not preview_path:
        add_check(checks, "preview_exists", "Draft preview exists", False, "render_handoff_top_packet/draft_preview.png was not found.")
    else:
        image = Image.open(preview_path).convert("RGB")
        dimensions = {"width": image.size[0], "height": image.size[1]}
        add_check(
            checks,
            "dimensions_1080x1350",
            "Expected draft dimensions",
            image.size == EXPECTED_SIZE,
            f"Found {image.size[0]}x{image.size[1]}; expected {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}.",
        )

        for zone_id, (box, threshold) in DRAFT_MARK_ZONES.items():
            score = red_dominance(image, box)
            add_check(
                checks,
                zone_id,
                "Draft watermark or footer guardrail red marker",
                score >= threshold,
                f"Red marker ratio {score:.3f} in crop {box}; threshold {threshold:.3f}.",
            )

        zone_scores: List[float] = []
        bright_scores: List[float] = []
        photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
        for zone_id, (box, min_bright_ratio, min_variance) in TEXT_ZONES.items():
            signal = title_zone_signal(image, box) if zone_id == "headline_text_zone" else text_zone_signal(image, box)
            zone_scores.append(signal["dark_pixel_ratio"])
            bright_scores.append(signal["bright_pixel_ratio"])
            if zone_id == "headline_text_zone":
                passed = bool(signal["contrast_passed"] and signal["fit_passed"])
                add_check(
                    checks,
                    zone_id,
                    "Title readable contrast and safe-zone fit",
                    passed,
                    (
                        "Style={style}; luma avg {average_luma:.1f}, variance {variance:.1f}; title ink ratio "
                        "{title_ink_ratio:.3f} (white {white_ink_ratio:.3f}, gold {gold_ink_ratio:.3f}, dark "
                        "{dark_ink_ratio:.3f}); edge contrast {edge_contrast_ratio:.3f}; dense title rows "
                        "{dense_row_count}; fit margins top={top_fit_margin}px bottom={bottom_fit_margin}px "
                        "in crop {box}."
                    ).format(**signal, box=box),
                )
            else:
                effective_min_bright_ratio = min_bright_ratio
                label = "Readable text zone signal"
                if zone_id == "score_team_text_zone" and photo_layout_mode == "photo_first_final_score":
                    effective_min_bright_ratio = 0.045
                    label = "Photo-first score/team readable signal"
                passed = signal["variance"] >= min_variance and signal["bright_pixel_ratio"] >= effective_min_bright_ratio
                add_check(
                    checks,
                    zone_id,
                    label,
                    passed,
                    "Luma avg {average_luma:.1f}, variance {variance:.1f}, bright pixel ratio {bright_pixel_ratio:.3f} "
                    "(min {min_bright_ratio:.3f}), dark pixel ratio {dark_pixel_ratio:.3f} in crop {box}; "
                    "layout={photo_layout_mode}.".format(
                        **signal,
                        min_bright_ratio=effective_min_bright_ratio,
                        box=box,
                        photo_layout_mode=photo_layout_mode or "standard",
                    ),
                )
        add_player_ledger_readability_check(checks, renderer_manifest, image)

        average_signal = mean(zone_scores) if zone_scores else 0.0
        average_bright_signal = mean(bright_scores) if bright_scores else 0.0
        min_average_bright_signal = 0.065 if photo_layout_mode == "photo_first_final_score" else 0.070
        overall_passed = average_signal >= 0.020 and average_bright_signal >= min_average_bright_signal
        add_check(
            checks,
            "overall_text_signal",
            "Overall readable text-zone signal",
            overall_passed,
            (
                f"Average dark pixel ratio across text zones {average_signal:.3f}; "
                f"average bright pixel ratio {average_bright_signal:.3f} "
                f"(min {min_average_bright_signal:.3f}); layout={photo_layout_mode or 'standard'}; this is a heuristic, not OCR."
            ),
            result="pass_human_review_required" if overall_passed else "hold",
        )

    guardrails = guardrail_checks(renderer_manifest, handoff_manifest)
    if Image is None or ImageStat is None or not preview_path:
        add_player_ledger_readability_check(checks, renderer_manifest, None)
    add_renderer_metadata_checks(checks, renderer_manifest)
    add_check(
        checks,
        "approval_guardrails",
        "Approval and publishing guardrails",
        all(guardrails.values()),
        "; ".join(f"{key}={value}" for key, value in guardrails.items()),
    )

    hold_count = sum(1 for check in checks if not check.get("passed"))
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "human_review_required" if hold_count == 0 else "hold_for_manual_review",
        "approval_status": "not_approved_human_review_required",
        "preview_path": preview_path.as_posix() if preview_path else "",
        "renderer_manifest_path": renderer_manifest_path.as_posix() if renderer_manifest_path else "",
        "handoff_manifest_path": handoff_manifest_path.as_posix() if handoff_manifest_path else "",
        "dimensions": dimensions,
        "summary": {
            "check_count": len(checks),
            "pass_count": len(checks) - hold_count,
            "hold_count": hold_count,
            "human_decision_required": True,
        },
        "checks": checks,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_approval": False,
            "auto_publish": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }
    write_json(OUT_MANIFEST, manifest)
    write_csv(OUT_CHECKLIST, checklist_rows(checks), CHECKLIST_FIELDS)
    write_text(OUT_REPORT, "\n".join(report_lines(manifest, checks, preview_path)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
