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


VERSION = "hsd-manual-visual-qa-v1.0.0-review-only"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
PREVIEW_NAME = "draft_preview.png"
EXPECTED_SIZE = (1080, 1350)
OUT_REPORT = output_path("manual_visual_qa_report.md")
OUT_MANIFEST = output_path("manual_visual_qa_manifest.json")
OUT_CHECKLIST = output_path("manual_visual_qa_checklist.csv")

Zone = Tuple[int, int, int, int]
TEXT_ZONES: Dict[str, Zone] = {
    "headline_text_zone": (60, 240, 1020, 500),
    "dek_text_zone": (60, 500, 1020, 700),
    "context_text_zone": (60, 930, 1020, 1268),
}
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
    dark_ratio = darkish / len(data) if data else 0.0
    return {"average_luma": avg, "variance": variance, "dark_pixel_ratio": dark_ratio}


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
            "Final-score draft should use GAME EDGE, verified player-stat module, or matchup-specific YOUR TAKE copy; "
            "hold by eye if it falls back to internal source-confidence language."
            if final_score_template
            else "Non-final-score template; human copy review still required."
        ),
        result="pass_human_review_required",
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
        for zone_id, box in TEXT_ZONES.items():
            signal = text_zone_signal(image, box)
            zone_scores.append(signal["dark_pixel_ratio"])
            passed = signal["variance"] >= 60.0 and signal["dark_pixel_ratio"] >= 0.015
            add_check(
                checks,
                zone_id,
                "Readable text zone signal",
                passed,
                "Luma avg {average_luma:.1f}, variance {variance:.1f}, dark pixel ratio {dark_pixel_ratio:.3f} in crop {box}.".format(
                    **signal,
                    box=box,
                ),
            )
        average_signal = mean(zone_scores) if zone_scores else 0.0
        add_check(
            checks,
            "overall_text_signal",
            "Overall readable text-zone signal",
            average_signal >= 0.020,
            f"Average dark pixel ratio across text zones {average_signal:.3f}; this is a heuristic, not OCR.",
            result="pass_human_review_required" if average_signal >= 0.020 else "hold",
        )

    guardrails = guardrail_checks(renderer_manifest, handoff_manifest)
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
