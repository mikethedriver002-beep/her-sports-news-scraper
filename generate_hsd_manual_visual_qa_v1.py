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


VERSION = "hsd-manual-visual-qa-v1.13.0-premium-route-limit-cue"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
PREVIEW_NAME = "draft_preview.png"
EXPECTED_SIZE = (1080, 1350)
OUT_REPORT = output_path("manual_visual_qa_report.md")
OUT_MANIFEST = output_path("manual_visual_qa_manifest.json")
OUT_CHECKLIST = output_path("manual_visual_qa_checklist.csv")

Zone = Tuple[int, int, int, int]
TextZoneSpec = Tuple[Zone, float, float]
TEXT_ZONES: Dict[str, TextZoneSpec] = {
    "headline_text_zone": ((50, 118, 1030, 310), 0.18, 850.0),
    "score_team_text_zone": ((280, 420, 1030, 900), 0.08, 800.0),
    "context_text_zone": ((480, 770, 1030, 858), 0.025, 500.0),
    "lower_module_text_zone": ((55, 980, 1030, 1140), 0.025, 600.0),
}
PLAYER_LEDGER_ZONE: Zone = (70, 960, 1010, 1128)
DRAFT_MARK_ZONES: Dict[str, Tuple[Zone, float]] = {
    "top_draft_label_zone": ((710, 74, 1030, 150), 0.025),
    "footer_guardrail_zone": ((54, 1286, 1028, 1320), 0.120),
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


def first_present(*values: Any) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def parse_utc_timestamp(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def primary_format_option(renderer_manifest: Dict[str, Any]) -> Dict[str, Any]:
    formats = renderer_manifest.get("format_options") if isinstance(renderer_manifest.get("format_options"), list) else []
    primary = next((item for item in formats if isinstance(item, dict) and item.get("primary") is True), formats[0] if formats else {})
    return primary if isinstance(primary, dict) else {}


def contract_value(renderer_manifest: Dict[str, Any], key: str) -> str:
    content_module = renderer_manifest.get("content_module") if isinstance(renderer_manifest.get("content_module"), dict) else {}
    primary = primary_format_option(renderer_manifest)
    return clean(content_module.get(key)) or clean(primary.get(key))


def final_score_context(renderer_manifest: Dict[str, Any]) -> bool:
    selected_template = renderer_manifest.get("selected_template") if isinstance(renderer_manifest.get("selected_template"), dict) else {}
    format_options = renderer_manifest.get("format_options") if isinstance(renderer_manifest.get("format_options"), list) else []
    fields = [
        clean(selected_template.get("template_id")),
        clean(selected_template.get("template_family")),
        contract_value(renderer_manifest, "visual_mode"),
        contract_value(renderer_manifest, "athlete_photo_layout_mode"),
        contract_value(renderer_manifest, "score_lock_variant"),
    ]
    for row in format_options:
        if isinstance(row, dict):
            fields.extend(
                [
                    clean(row.get("visual_mode")),
                    clean(row.get("athlete_photo_layout_mode")),
                    clean(row.get("score_lock_variant")),
                    clean(row.get("athlete_photo_template_family")),
                ]
            )
    return any("final_score" in field or "premium_result" in field for field in fields)


def box_from_geometry(geometry: Dict[str, Any], key: str) -> Zone | None:
    raw = geometry.get(key)
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        return int(raw[0]), int(raw[1]), int(raw[2]), int(raw[3])
    except Exception:
        return None


def clamp_box(box: Zone, size: Tuple[int, int]) -> Zone:
    x, y, w, h = box
    max_w, max_h = size
    x = max(0, min(x, max_w))
    y = max(0, min(y, max_h))
    w = max(0, min(w, max_w - x))
    h = max(0, min(h, max_h - y))
    return x, y, w, h


def pil_crop_box(box: Zone) -> Tuple[int, int, int, int]:
    x, y, w, h = box
    return x, y, x + w, y + h


def box_clearance(a: Zone, b: Zone) -> int:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    dx = max(bx - (ax + aw), ax - (bx + bw), 0)
    dy = max(by - (ay + ah), ay - (by + bh), 0)
    if dx and dy:
        return min(dx, dy)
    if dx or dy:
        return max(dx, dy)
    overlap_x = min(ax + aw, bx + bw) - max(ax, bx)
    overlap_y = min(ay + ah, by + bh) - max(ay, by)
    return -min(overlap_x, overlap_y)


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


def add_preview_freshness_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any], handoff_manifest: Dict[str, Any]) -> None:
    packet = handoff_manifest.get("packet") if isinstance(handoff_manifest.get("packet"), dict) else {}
    renderer_packet_id = clean(renderer_manifest.get("packet_id"))
    handoff_packet_id = clean(packet.get("packet_id"))
    renderer_generated = parse_utc_timestamp(renderer_manifest.get("generated_at_utc"))
    handoff_generated = parse_utc_timestamp(handoff_manifest.get("generated_at_utc"))

    packet_matches = bool(renderer_packet_id and handoff_packet_id and renderer_packet_id == handoff_packet_id)
    if not renderer_packet_id or not handoff_packet_id:
        packet_matches = True

    if renderer_generated and handoff_generated:
        fresh_enough = renderer_generated >= handoff_generated
        passed = packet_matches and fresh_enough
        evidence = (
            f"renderer_packet={renderer_packet_id or 'not_recorded'}; handoff_packet={handoff_packet_id or 'not_recorded'}; "
            f"renderer_generated_at_utc={renderer_generated.isoformat()}; "
            f"handoff_generated_at_utc={handoff_generated.isoformat()}; "
            f"fresh_after_handoff={fresh_enough}."
        )
        add_check(checks, "preview_freshness_current_handoff", "Preview freshness vs current handoff", passed, evidence)
        return

    evidence = (
        f"renderer_packet={renderer_packet_id or 'not_recorded'}; handoff_packet={handoff_packet_id or 'not_recorded'}; "
        f"renderer_generated_at_utc={clean(renderer_manifest.get('generated_at_utc')) or 'not_recorded'}; "
        f"handoff_generated_at_utc={clean(handoff_manifest.get('generated_at_utc')) or 'not_recorded'}; "
        "timestamp comparison unavailable, so human review must confirm the preview belongs to the current handoff."
    )
    add_check(
        checks,
        "preview_freshness_current_handoff",
        "Preview freshness vs current handoff",
        packet_matches,
        evidence,
        result="pass_human_review_required" if packet_matches else "hold",
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


def add_photo_first_template_checks(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any], image: Any | None) -> None:
    primary = primary_format_option(renderer_manifest)
    mode = clean(primary.get("athlete_photo_layout_mode"))
    if mode != "photo_first_final_score":
        add_check(
            checks,
            "photo_first_template_readiness",
            "Photo-first template readiness",
            True,
            f"Primary render layout={mode or 'standard'}; photo-first crop and clearance checks are not required for this fallback.",
            result="pass_human_review_required",
        )
        return
    geometry = primary.get("photo_first_template_geometry") if isinstance(primary.get("photo_first_template_geometry"), dict) else {}
    if not geometry:
        add_check(
            checks,
            "photo_first_template_readiness",
            "Photo-first template readiness",
            False,
            "Primary render is photo_first_final_score, but no renderer geometry was provided for QA.",
        )
        return
    if image is None:
        add_check(
            checks,
            "photo_first_template_readiness",
            "Photo-first template readiness",
            False,
            "Primary render is photo_first_final_score, but the preview image was unavailable for crop and clearance QA.",
        )
        return

    stage = box_from_geometry(geometry, "photo_stage_box")
    face = box_from_geometry(geometry, "photo_face_focus_box")
    if not stage or not face:
        add_check(
            checks,
            "photo_first_template_readiness",
            "Photo-first template readiness",
            False,
            "Photo-first renderer geometry is missing photo_stage_box or photo_face_focus_box.",
        )
        return

    stage = clamp_box(stage, image.size)
    face = clamp_box(face, image.size)
    stage_signal = text_zone_signal(image, pil_crop_box(stage))
    stage_passed = stage_signal["variance"] >= 900.0 and stage_signal["bright_pixel_ratio"] >= 0.018 and stage_signal["dark_pixel_ratio"] >= 0.700
    add_check(
        checks,
        "photo_first_crop_signal",
        "Photo-first athlete crop signal",
        stage_passed,
        (
            f"layout={mode}; stage_box={stage}; luma avg {stage_signal['average_luma']:.1f}, "
            f"variance {stage_signal['variance']:.1f} (min 900.0), bright pixel ratio "
            f"{stage_signal['bright_pixel_ratio']:.3f} (min 0.018), dark pixel ratio "
            f"{stage_signal['dark_pixel_ratio']:.3f} (min 0.700)."
        ),
    )

    face_crop = image.crop(pil_crop_box(face)).convert("RGB")
    face_signal = text_zone_signal(image, pil_crop_box(face))
    face_edge = edge_contrast_ratio(face_crop)
    face_edge_min = 0.014
    face_passed = face_signal["variance"] >= 700.0 and face_signal["bright_pixel_ratio"] >= 0.015 and face_edge >= face_edge_min
    add_check(
        checks,
        "photo_first_face_visibility",
        "Photo-first face visibility signal",
        face_passed,
        (
            f"layout={mode}; face_focus_box={face}; luma avg {face_signal['average_luma']:.1f}, "
            f"variance {face_signal['variance']:.1f} (min 700.0), bright pixel ratio "
            f"{face_signal['bright_pixel_ratio']:.3f} (min 0.015), edge contrast "
            f"{face_edge:.3f} (min {face_edge_min:.3f}). Heuristic only; human eye review remains required."
        ),
    )

    boxes = {
        "photo_stage": stage,
        "winner_score": box_from_geometry(geometry, "winner_score_row_box"),
        "loser_score": box_from_geometry(geometry, "loser_score_row_box"),
        "score_context": box_from_geometry(geometry, "score_context_box"),
        "stat_strip": box_from_geometry(geometry, "stat_strip_box"),
        "matchup_angle": box_from_geometry(geometry, "matchup_angle_box"),
    }
    missing = [label for label, box in boxes.items() if box is None]
    if missing:
        add_check(
            checks,
            "photo_first_text_clearance",
            "Photo-first text and module clearance",
            False,
            f"Photo-first geometry is missing boxes: {', '.join(missing)}.",
        )
        return
    typed_boxes = {label: clamp_box(box, image.size) for label, box in boxes.items() if box is not None}
    pairs = [
        ("photo_stage", "winner_score"),
        ("photo_stage", "loser_score"),
        ("photo_stage", "stat_strip"),
        ("winner_score", "loser_score"),
        ("loser_score", "score_context"),
        ("score_context", "stat_strip"),
        ("stat_strip", "matchup_angle"),
    ]
    gaps = {f"{left}->{right}": box_clearance(typed_boxes[left], typed_boxes[right]) for left, right in pairs}
    minimum = int(geometry.get("minimum_clearance_px", 24) or 24)
    min_gap = min(gaps.values()) if gaps else 0
    add_check(
        checks,
        "photo_first_text_clearance",
        "Photo-first text and module clearance",
        min_gap >= minimum,
        f"minimum_clearance={min_gap}px (required {minimum}px); " + "; ".join(f"{key}={value}px" for key, value in gaps.items()),
    )


def add_premium_editorial_clutter_scan(
    checks: List[Dict[str, Any]],
    renderer_manifest: Dict[str, Any],
    image: Any | None,
    zone_scores: List[float],
    bright_scores: List[float],
) -> None:
    format_options = renderer_manifest.get("format_options") if isinstance(renderer_manifest.get("format_options"), list) else []
    visual_mode = clean(first_present(contract_value(renderer_manifest, "visual_mode"), renderer_manifest.get("visual_mode")))
    photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
    is_final_score_context = final_score_context(renderer_manifest)
    if not is_final_score_context:
        add_check(
            checks,
            "premium_editorial_clutter_scan",
            "Premium editorial clutter scan",
            True,
            (
                "Non-final-score or minimal metadata render; premium clutter scan stays as a manual eye-review cue. "
                "Operator should still hold or revise if the draft lacks a clear premium editorial hierarchy."
            ),
            result="pass_human_review_required",
        )
        return
    if image is None:
        add_check(
            checks,
            "premium_editorial_clutter_scan",
            "Premium editorial clutter scan",
            False,
            "Final-score metadata exists, but the preview image was unavailable for premium/clutter QA.",
        )
        return

    all_zones = TEXT_ZONES.values()
    average_dark_signal = mean(zone_scores) if zone_scores else 0.0
    average_bright_signal = mean(bright_scores) if bright_scores else 0.0
    zone_variances = [text_zone_signal(image, box)["variance"] for box, _, _ in all_zones]
    average_zone_variance = mean(zone_variances) if zone_variances else 0.0
    format_count = len([row for row in format_options if isinstance(row, dict) and clean(row.get("format_id"))])
    headline_signal = title_zone_signal(image, TEXT_ZONES["headline_text_zone"][0])
    passed = (
        headline_signal["fit_passed"]
        and headline_signal["contrast_passed"]
        and average_zone_variance <= 12000.0
        and average_dark_signal >= 0.020
        and average_bright_signal >= (0.035 if photo_layout_mode == "photo_first_final_score" else 0.070)
    )
    add_check(
        checks,
        "premium_editorial_clutter_scan",
        "Premium editorial clutter scan",
        passed,
        (
            f"final_score_context={is_final_score_context}; visual_mode={visual_mode or 'missing'}; "
            f"layout={photo_layout_mode or 'standard'}; format_count={format_count}; "
            f"title_fit={headline_signal['fit_passed']}; title_contrast={headline_signal['contrast_passed']}; "
            f"avg_text_variance={average_zone_variance:.1f} (max 12000.0); "
            f"avg_dark_signal={average_dark_signal:.3f}; avg_bright_signal={average_bright_signal:.3f}. "
            "Operator should hold or revise if the draft feels busy, cramped, ad-like, or lacks a clear premium editorial hierarchy."
        ),
        result="pass_human_review_required" if passed else "hold",
    )


def add_anti_dashboard_score_spine_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any]) -> None:
    visual_mode = clean(first_present(contract_value(renderer_manifest, "visual_mode"), renderer_manifest.get("visual_mode")))
    photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
    is_final_score_context = final_score_context(renderer_manifest)
    anti_dashboard_contract = contract_value(renderer_manifest, "anti_dashboard_contract")
    score_layout_contract = contract_value(renderer_manifest, "score_layout_contract")
    cues = clean(renderer_manifest.get("render_background_cues"))
    if not is_final_score_context:
        add_check(
            checks,
            "anti_dashboard_score_spine_review",
            "Anti-dashboard score-spine review cue",
            True,
            "Non-final-score render; anti-dashboard score-spine check remains a manual eye-review cue.",
            result="pass_human_review_required",
        )
        return

    passed = bool(
        anti_dashboard_contract
        and ("dashboard" in anti_dashboard_contract or "no_nested_cards" in anti_dashboard_contract)
        and "no_dashboard" in cues
        and ("spine" in score_layout_contract or visual_mode.startswith("photo_first"))
    )
    add_check(
        checks,
        "anti_dashboard_score_spine_review",
        "Anti-dashboard score-spine review cue",
        passed,
        (
            f"final_score_context={is_final_score_context}; visual_mode={visual_mode or 'missing'}; "
            f"layout={photo_layout_mode or 'standard'}; score_layout_contract={score_layout_contract or 'missing'}; "
            f"anti_dashboard_contract={anti_dashboard_contract or 'missing'}; "
            "operator must hold or revise if the score treatment reads like a dashboard card, boxed metric tile, row container, solid backing panel, fantasy-app module, or ad unit."
        ),
        result="pass_human_review_required" if passed else "hold",
    )


def add_lower_third_card_weight_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any], image: Any | None) -> None:
    visual_mode = clean(first_present(contract_value(renderer_manifest, "visual_mode"), renderer_manifest.get("visual_mode")))
    photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
    is_final_score_context = final_score_context(renderer_manifest)
    lower_third_contract = contract_value(renderer_manifest, "lower_third_contract")
    cues = clean(renderer_manifest.get("render_background_cues"))
    if not is_final_score_context:
        add_check(
            checks,
            "lower_third_card_weight_review",
            "Lower-third card-weight review cue",
            True,
            "Non-final-score render; lower-third card-weight check remains a manual eye-review cue.",
            result="pass_human_review_required",
        )
        return

    near_black_ratio = 0.0
    low_variance = False
    if image is not None:
        signal = text_zone_signal(image, TEXT_ZONES["lower_module_text_zone"][0])
        near_black_ratio = signal["dark_pixel_ratio"]
        low_variance = signal["variance"] < 800.0 and signal["bright_pixel_ratio"] < 0.040
    contract_ok = bool(
        lower_third_contract
        and ("rail" in lower_third_contract or "no_heavy" in lower_third_contract)
        and "lower_third_no_heavy_stat_cards" in cues
    )
    passed = contract_ok and not low_variance
    add_check(
        checks,
        "lower_third_card_weight_review",
        "Lower-third card-weight review cue",
        passed,
        (
            f"final_score_context={is_final_score_context}; visual_mode={visual_mode or 'missing'}; "
            f"layout={photo_layout_mode or 'standard'}; lower_third_contract={lower_third_contract or 'missing'}; "
            f"near_black_ratio={near_black_ratio:.3f}; low_variance_heavy_panel={low_variance}. "
            "Operator must hold or revise if the lower stat/caption block reads as a heavy card, dashboard module, solid lower-third box, or boxed lower-third."
        ),
        result="pass_human_review_required" if passed else "hold",
    )


def add_action_photo_readiness_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any]) -> None:
    visual_mode = clean(first_present(contract_value(renderer_manifest, "visual_mode"), renderer_manifest.get("visual_mode")))
    photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
    is_final_score_context = final_score_context(renderer_manifest)
    hero_mode = contract_value(renderer_manifest, "hero_image_mode")
    hero_source = contract_value(renderer_manifest, "hero_image_source_class")
    hero_contract = contract_value(renderer_manifest, "action_photo_hero_contract")
    candidate_status = contract_value(renderer_manifest, "action_photo_candidate_status")
    readiness_contract = contract_value(renderer_manifest, "action_photo_readiness_contract")
    slot_expectation = contract_value(renderer_manifest, "action_photo_slot_expectation")
    subject_metadata = contract_value(renderer_manifest, "action_photo_subject_metadata_required")
    crop_metadata = contract_value(renderer_manifest, "action_photo_crop_metadata_required")
    headshot_bridge = contract_value(renderer_manifest, "headshot_bridge_status")
    operator_cue = contract_value(renderer_manifest, "action_photo_operator_review_cue")
    if not is_final_score_context:
        add_check(
            checks,
            "action_photo_readiness_review",
            "Action-photo readiness review cue",
            True,
            "Non-final-score render; action-photo readiness remains a manual future-route cue.",
            result="pass_human_review_required",
        )
        return

    no_download_guardrail = "no_download" in (hero_contract + " " + slot_expectation) or "manually_cleared_local" in slot_expectation
    contract_ok = bool(
        readiness_contract
        and slot_expectation
        and subject_metadata
        and crop_metadata
        and "action_photo" in readiness_contract
        and no_download_guardrail
        and candidate_status in {"not_available_to_renderer", "pending_manual_action_photo_candidate"}
    )
    evidence = (
        f"final_score_context={is_final_score_context}; visual_mode={visual_mode or 'missing'}; "
        f"layout={photo_layout_mode or 'standard'}; hero_mode={hero_mode or 'missing'}; hero_source={hero_source or 'missing'}; "
        f"action_photo_contract={hero_contract or 'missing'}; candidate_status={candidate_status or 'missing'}; "
        f"readiness_contract={readiness_contract or 'missing'}; slot_expectation={slot_expectation or 'missing'}; "
        f"subject_metadata={subject_metadata or 'missing'}; crop_metadata={crop_metadata or 'missing'}; "
        f"headshot_bridge={headshot_bridge or 'missing'}. "
        f"{operator_cue or 'Headshot/no-photo fallback is review-draft acceptable only; premium final-score editorial needs a manually cleared action-photo candidate.'}"
    )
    add_check(
        checks,
        "action_photo_readiness_review",
        "Action-photo readiness review cue",
        contract_ok,
        evidence,
        result="pass_human_review_required" if contract_ok else "hold",
    )


def add_composition_balance_readiness_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any]) -> None:
    visual_mode = clean(first_present(contract_value(renderer_manifest, "visual_mode"), renderer_manifest.get("visual_mode")))
    photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
    is_final_score_context = final_score_context(renderer_manifest)
    headshot_bridge = contract_value(renderer_manifest, "headshot_bridge_status")
    composition_contract = contract_value(renderer_manifest, "composition_balance_contract")
    replacement_cue = contract_value(renderer_manifest, "action_photo_replacement_composition_cue")
    bridge_cue = contract_value(renderer_manifest, "headshot_bridge_composition_cue")
    balance_cue = contract_value(renderer_manifest, "lower_left_right_balance_review_cue")
    roster_risk_cue = contract_value(renderer_manifest, "roster_portrait_risk_cue")
    if not is_final_score_context:
        add_check(
            checks,
            "composition_balance_readiness_review",
            "Composition balance readiness cue",
            True,
            "Non-final-score render; composition balance readiness remains a manual eye-review cue.",
            result="pass_human_review_required",
        )
        return

    contract_ok = bool(
        composition_contract
        and replacement_cue
        and bridge_cue
        and balance_cue
        and roster_risk_cue
        and ("balance" in composition_contract or "replacement_lane" in composition_contract)
        and ("action" in replacement_cue or "action" in composition_contract)
        and ("roster" in roster_risk_cue or "roster" in bridge_cue)
    )
    evidence = (
        f"final_score_context={is_final_score_context}; visual_mode={visual_mode or 'missing'}; "
        f"layout={photo_layout_mode or 'standard'}; headshot_bridge={headshot_bridge or 'missing'}; "
        f"composition_contract={composition_contract or 'missing'}; replacement_cue={replacement_cue or 'missing'}; "
        f"bridge_cue={bridge_cue or 'missing'}; balance_cue={balance_cue or 'missing'}; "
        f"roster_portrait_risk={roster_risk_cue or 'missing'}. "
        "Operator must hold or revise if the headshot bridge reads as roster media, the lower-left/right weight feels flat, "
        "or the layout leaves no credible action-photo replacement lane."
    )
    add_check(
        checks,
        "composition_balance_readiness_review",
        "Composition balance readiness cue",
        contract_ok,
        evidence,
        result="pass_human_review_required" if contract_ok else "hold",
    )


def add_premium_editorial_route_limit_check(checks: List[Dict[str, Any]], renderer_manifest: Dict[str, Any]) -> None:
    visual_mode = clean(first_present(contract_value(renderer_manifest, "visual_mode"), renderer_manifest.get("visual_mode")))
    photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
    is_final_score_context = final_score_context(renderer_manifest)
    hero_source = contract_value(renderer_manifest, "hero_image_source_class")
    hero_mode = contract_value(renderer_manifest, "hero_image_mode")
    candidate_status = contract_value(renderer_manifest, "action_photo_candidate_status")
    readiness_contract = contract_value(renderer_manifest, "action_photo_readiness_contract")
    headshot_bridge = contract_value(renderer_manifest, "headshot_bridge_status")
    composition_contract = contract_value(renderer_manifest, "composition_balance_contract")
    roster_risk_cue = contract_value(renderer_manifest, "roster_portrait_risk_cue")
    if not is_final_score_context:
        add_check(
            checks,
            "premium_editorial_route_limit_review",
            "Premium final-score editorial route limit",
            True,
            "Non-final-score render; premium final-score route limit remains a manual future-route cue.",
            result="pass_human_review_required",
        )
        return

    draft_bridge_only = bool(
        visual_mode.startswith("no_photo")
        or "fallback" in visual_mode
        or "headshot" in hero_source
        or "headshot_bridge" in readiness_contract
        or "headshot" in headshot_bridge
        or candidate_status in {"not_available_to_renderer", "pending_manual_action_photo_candidate"}
    )
    premium_ready = bool(
        "action_photo" in readiness_contract
        and "action_photo" in composition_contract
        and candidate_status not in {"", "not_available_to_renderer", "pending_manual_action_photo_candidate"}
        and "headshot" not in hero_source
        and "no_local" not in hero_source
        and not visual_mode.startswith("no_photo")
    )
    evidence = (
        f"editorial_call={'PASS_ROUTE_READY' if premium_ready else 'REVISE_PREMIUM_FINAL_SCORE'}; "
        f"review_draft_acceptance={'acceptable_review_draft_only' if draft_bridge_only else 'manual_review_required'}; "
        f"visual_mode={visual_mode or 'missing'}; layout={photo_layout_mode or 'standard'}; "
        f"hero_source={hero_source or 'missing'}; hero_mode={hero_mode or 'missing'}; "
        f"candidate_status={candidate_status or 'missing'}; readiness_contract={readiness_contract or 'missing'}; "
        f"headshot_bridge={headshot_bridge or 'missing'}; composition_contract={composition_contract or 'missing'}; "
        f"roster_portrait_risk={roster_risk_cue or 'missing'}. "
        "Operator should mark revise/hold for premium sports editorial if the route is still logo/no-photo/headshot bridge, "
        "boxed-dashboard-like, or lacks a manually cleared action-photo candidate; do not treat review-draft acceptance as approval."
    )
    add_check(
        checks,
        "premium_editorial_route_limit_review",
        "Premium final-score editorial route limit",
        premium_ready,
        evidence,
        result="pass_human_review_required" if premium_ready else "hold",
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
            "- Stop if the single draft watermark is missing.",
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
                "Single draft watermark red marker",
                score >= threshold,
                f"Red marker ratio {score:.3f} in crop {box}; threshold {threshold:.3f}; review_only_diagnostic_watermark_lock=True.",
            )

        zone_scores: List[float] = []
        bright_scores: List[float] = []
        photo_layout_mode = primary_photo_layout_mode(renderer_manifest)
        renderer_cues = clean(renderer_manifest.get("render_background_cues"))
        for zone_id, (box, min_bright_ratio, min_variance) in TEXT_ZONES.items():
            signal = title_zone_signal(image, box) if zone_id == "headline_text_zone" else text_zone_signal(image, box)
            if (
                zone_id == "context_text_zone"
                and photo_layout_mode == "photo_first_final_score"
                and "photo_first_no_redundant_score_context" in renderer_cues
            ):
                passed = signal["bright_pixel_ratio"] <= 0.015 and signal["variance"] <= 1200.0
                add_check(
                    checks,
                    zone_id,
                    "Photo-first redundant score context removed",
                    passed,
                    "No public score-context copy expected for naked-score stage; luma avg {average_luma:.1f}, "
                    "variance {variance:.1f} (max 1200.0), bright pixel ratio {bright_pixel_ratio:.3f} "
                    "(max 0.015), dark pixel ratio {dark_pixel_ratio:.3f} in crop {box}; "
                    "layout={photo_layout_mode}.".format(
                        **signal,
                        box=box,
                        photo_layout_mode=photo_layout_mode or "standard",
                    ),
                )
                continue
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
                    if "photo_first_editorial_score_rails" in renderer_cues:
                        effective_min_bright_ratio = 0.035
                        label = "Photo-first editorial score-rail readable signal"
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
        add_photo_first_template_checks(checks, renderer_manifest, image)
        add_player_ledger_readability_check(checks, renderer_manifest, image)
        add_premium_editorial_clutter_scan(checks, renderer_manifest, image, zone_scores, bright_scores)
        add_anti_dashboard_score_spine_check(checks, renderer_manifest)
        add_lower_third_card_weight_check(checks, renderer_manifest, image)
        add_action_photo_readiness_check(checks, renderer_manifest)
        add_composition_balance_readiness_check(checks, renderer_manifest)
        add_premium_editorial_route_limit_check(checks, renderer_manifest)

        average_signal = mean(zone_scores) if zone_scores else 0.0
        average_bright_signal = mean(bright_scores) if bright_scores else 0.0
        min_average_bright_signal = 0.035 if photo_layout_mode == "photo_first_final_score" else 0.070
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
        add_photo_first_template_checks(checks, renderer_manifest, None)
        add_player_ledger_readability_check(checks, renderer_manifest, None)
        add_premium_editorial_clutter_scan(checks, renderer_manifest, None, [], [])
        add_anti_dashboard_score_spine_check(checks, renderer_manifest)
        add_lower_third_card_weight_check(checks, renderer_manifest, None)
        add_action_photo_readiness_check(checks, renderer_manifest)
        add_composition_balance_readiness_check(checks, renderer_manifest)
        add_premium_editorial_route_limit_check(checks, renderer_manifest)
    add_renderer_metadata_checks(checks, renderer_manifest)
    add_preview_freshness_check(checks, renderer_manifest, handoff_manifest)
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
