from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "v1.3-phase6j-final-score-content-module-live-gate"
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_v4.json")
RENDER_MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
NEAR_REPORT = Path("near_post_ready_v4_report.json")
FIDELITY_REPORT = Path("template_fidelity_v4_report.json")
SOURCE_TRUTH = Path("v4_source_truth_guard.json")
ASSET_REPORT = Path("live_asset_preparation_v4_report.json")
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/live_post_ready")
LIVE_ROOT = Path("outputs/latest/HSD_LIVE_POST_READY")
REPORT_JSON = Path("live_post_ready_v4_report.json")
REPORT_MD = Path("live_post_ready_v4_report.md")
CANDIDATES_CSV = OUT_DIR / "live_post_ready_candidates_v4.csv"
BLOCKED_CSV = OUT_DIR / "live_post_ready_blocked_v4.csv"
APPROVED_CSV = OUT_DIR / "live_post_ready_approved_v4.csv"
DECISIONS_TEMPLATE = OUT_DIR / "live_visual_approval_decisions_template_v4.csv"
CONTACT_SHEET = OUT_DIR / "live_post_ready_contact_sheet_v4.jpg"
HANDOFF_MANIFEST = LIVE_ROOT / "live_post_ready_manifest_v4.csv"

FIELDS = [
    "live_approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256",
    "item_id", "source_id", "template_id", "platform", "variant", "module_mode", "headline",
    "output_path", "live_output_path", "technical_status", "technical_reasons", "fidelity_score",
    "team_logo_count", "team_logo_modes", "player_assets_used", "player_names", "player_asset_kind",
    "fixture_only_player_asset", "placeholder_layer_count", "zone_overflow_count", "mask_compliance_status",
    "near_post_ready_candidate", "review_only", "source_truth_status", "release_recommendation_status",
    "polish_reasons", "technical_fidelity_floor", "release_fidelity_threshold", "final_score_polish_status", "final_score_polish_score", "final_score_polish_reasons",
    "content_module_status", "content_module_score", "content_module_reasons", "content_module_mode",
    "content_module_title", "content_module_body", "content_module_stat_count", "content_module_prompt", "live_post_ready",
]
DECISION_FIELDS = ["live_approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256"]
ALLOWED_DECISIONS = {"approved", "rejected", "needs_fix", "hold", ""}


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def as_bool(value: Any) -> bool:
    return clean(value).lower() in {"true", "1", "yes", "y"}


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
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_is_fixture(source_id: str, item_id: str, policy: Dict[str, Any]) -> bool:
    values = [clean(source_id).lower(), clean(item_id).lower()]
    prefixes = [clean(value).lower() for value in policy.get("fixture_source_prefixes") or []]
    return any(any(value.startswith(prefix) for prefix in prefixes if prefix) for value in values if value)


def logo_modes(value: Any) -> List[str]:
    return [part.strip() for part in clean(value).split(";") if part.strip()]


def make_approval_id(item: Dict[str, Any], render_hash: str) -> str:
    seed = "|".join([
        clean(item.get("source_id")), clean(item.get("item_id")), clean(item.get("template_id")),
        clean(item.get("platform")), clean(item.get("module_mode")), render_hash,
    ])
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]


def merge_rows(root: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    manifest = read_json(root / RENDER_MANIFEST)
    near = read_json(root / NEAR_REPORT)
    fidelity = read_json(root / FIDELITY_REPORT)
    source_truth = read_json(root / SOURCE_TRUTH)
    near_map = {clean(row.get("item_id")): row for row in near.get("rows") or []}
    fidelity_map = {clean(row.get("item_id")): row for row in fidelity.get("rows") or []}
    rows: List[Dict[str, Any]] = []
    for raw in manifest.get("items") or []:
        item = dict(raw)
        item_id = clean(item.get("item_id"))
        item.update({key: value for key, value in near_map.get(item_id, {}).items() if key not in item or item.get(key) in {None, ""}})
        fidelity_row = fidelity_map.get(item_id, {})
        item["fidelity_score"] = fidelity_row.get("overall_score", item.get("fidelity_score", ""))
        item["mask_compliance_status"] = near_map.get(item_id, {}).get("mask_compliance_status", item.get("mask_compliance_status", ""))
        item["near_post_ready_candidate"] = near_map.get(item_id, {}).get("near_post_ready_candidate", item.get("near_post_ready_candidate", ""))
        rows.append(item)
    return rows, manifest, source_truth, read_json(root / ASSET_REPORT)


def technical_reasons(item: Dict[str, Any], policy: Dict[str, Any], mode: str, root: Path, source_truth: Dict[str, Any]) -> List[str]:
    reasons: List[str] = []
    source_id = clean(item.get("source_id"))
    item_id = clean(item.get("item_id"))
    fixture = source_is_fixture(source_id, item_id, policy)
    if fixture:
        reasons.append("fixture_or_test_source")
    if mode == "live_data":
        required_status = clean(policy.get("source_truth_pass_status"))
        if policy.get("source_truth_required_for_live_data") and clean(source_truth.get("status")) != required_status:
            reasons.append("source_truth_not_passed")
    output = root / clean(item.get("output_path"))
    if not output.exists():
        reasons.append("render_missing")
    if as_bool(item.get("fixture_only_player_asset")):
        reasons.append("fixture_only_player_asset")
    if as_int(item.get("placeholder_layer_count")) > int(policy.get("maximum_placeholder_layer_count", 0)):
        reasons.append("placeholder_layers_present")
    if as_int(item.get("zone_overflow_count")) > int(policy.get("maximum_zone_overflow_count", 0)):
        reasons.append("zone_overflow_present")
    if clean(item.get("mask_compliance_status")) != clean(policy.get("required_mask_status")):
        reasons.append("mask_compliance_not_passed")
    if not as_bool(item.get("near_post_ready_candidate")):
        reasons.append("near_post_ready_candidate_false")
    modes = logo_modes(item.get("team_logo_modes"))
    required_count = int(policy.get("required_team_logo_count", 2))
    allowed_modes = set(policy.get("allowed_team_logo_modes") or [])
    if len(modes) < required_count or as_int(item.get("team_logo_count")) < required_count:
        reasons.append("insufficient_exact_team_logos")
    if any(mode_value not in allowed_modes for mode_value in modes):
        reasons.append("text_or_unapproved_logo_fallback")
    module_mode = clean(item.get("module_mode")).lower()
    if module_mode in {clean(value).lower() for value in policy.get("player_modes") or []}:
        if as_int(item.get("player_assets_used")) < 1:
            reasons.append("player_mode_missing_real_player_asset")
        if as_bool(item.get("fixture_only_player_asset")):
            reasons.append("player_mode_uses_fixture_asset")
    template_id = clean(item.get("template_id"))
    if is_final_score_template(template_id) and policy.get("phase6j_final_score_content_modules_required", True):
        if clean(item.get("content_module_status")) != "passed_final_score_content_modules":
            reasons.append("final_score_content_module_not_passed")
        if as_float(item.get("content_module_score")) < as_float(policy.get("minimum_final_score_content_module_score") or 0.95):
            reasons.append("final_score_content_module_score_below_minimum")
        if template_id == "hsd_game_recap_final_score_b" and as_int(item.get("content_module_stat_count")) < 1:
            reasons.append("final_score_b_missing_verified_player_stats")
    release_threshold = as_float((policy.get("minimum_fidelity_by_template") or {}).get(template_id, 1.0))
    technical_floor = as_float((policy.get("technical_fidelity_floor_by_template") or {}).get(template_id, release_threshold))
    if as_float(item.get("fidelity_score")) < technical_floor:
        reasons.append(f"fidelity_below_technical_floor:{technical_floor:.3f}")
    combined_copy = " ".join([
        clean(item.get("headline")), clean(item.get("player_names")), clean(item.get("notes")),
    ]).upper()
    for token in policy.get("forbidden_live_copy_tokens") or []:
        token_upper = clean(token).upper()
        if token_upper and token_upper in combined_copy:
            reasons.append(f"forbidden_live_copy:{token_upper}")
    return sorted(set(reasons))


def is_final_score_template(template_id: str) -> bool:
    return template_id in {
        "hsd_game_recap_final_score_a",
        "hsd_game_recap_final_score_b",
        "hsd_game_recap_final_score_c_story",
    }


def final_score_polish_passes(item: Dict[str, Any], policy: Dict[str, Any]) -> bool:
    if not is_final_score_template(clean(item.get("template_id"))):
        return False
    status = clean(item.get("final_score_polish_status"))
    try:
        score = float(clean(item.get("final_score_polish_score")) or "0")
    except Exception:
        score = 0.0
    minimum = as_float(policy.get("minimum_final_score_polish_score") or 0.92)
    return status == "passed_final_score_template_polish" and score >= minimum


def fidelity_policy(item: Dict[str, Any], policy: Dict[str, Any]) -> Tuple[float, float, str, str]:
    template_id = clean(item.get("template_id"))
    release_threshold = as_float((policy.get("minimum_fidelity_by_template") or {}).get(template_id, 1.0))
    technical_floor = as_float((policy.get("technical_fidelity_floor_by_template") or {}).get(template_id, release_threshold))
    score = as_float(item.get("fidelity_score"))
    if score >= release_threshold:
        return technical_floor, release_threshold, "release_ready_recommended", ""
    content_pass = (
        clean(item.get("content_module_status")) == "passed_final_score_content_modules"
        and as_float(item.get("content_module_score")) >= as_float(policy.get("minimum_final_score_content_module_score") or 0.95)
    )
    if final_score_polish_passes(item, policy) and content_pass and policy.get("phase6j_final_score_content_modules_release_review", True):
        return technical_floor, release_threshold, "release_ready_recommended", f"phase6j_content_module_review:{score:.4f}_below_public_mockup_threshold:{release_threshold:.2f}"
    if score >= technical_floor:
        return technical_floor, release_threshold, "needs_visual_polish_before_handoff", f"fidelity_below_release_recommendation:{release_threshold:.2f}"
    return technical_floor, release_threshold, "blocked_below_technical_floor", f"fidelity_below_technical_floor:{technical_floor:.3f}"


def locate_decisions(root: Path, policy: Dict[str, Any]) -> Path:
    return root / clean(policy.get("live_decisions_path"))


def build_contact_sheet(root: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    columns = 2
    cell_w, cell_h = 540, 560
    header_h = 92
    sheet = Image.new("RGB", (columns * cell_w + 40, math.ceil(len(rows) / columns) * cell_h + header_h + 30), (239, 239, 239))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    font = ImageFont.truetype(font_path.as_posix(), 22) if font_path.exists() else ImageFont.load_default()
    small = ImageFont.truetype(font_path.as_posix(), 13) if font_path.exists() else ImageFont.load_default()
    draw.text((24, 20), "HSD Phase 6G Live Post-Ready Gate", fill=(15, 15, 15), font=font)
    draw.text((24, 56), "Fixture proofs and text-logo fallbacks are blocked from the live lane.", fill=(70, 70, 70), font=small)
    for index, row in enumerate(rows):
        col = index % columns
        row_index = index // columns
        x0 = 20 + col * cell_w
        y0 = header_h + row_index * cell_h
        path = root / clean(row.get("output_path"))
        if path.exists():
            image = Image.open(path).convert("RGB")
            image.thumbnail((500, 410), Image.Resampling.LANCZOS)
            sheet.paste(image, (x0 + (500 - image.width) // 2 + 10, y0 + 8))
        status = clean(row.get("technical_status"))
        color = (10, 110, 45) if status == "live_technical_candidate" else (155, 55, 25)
        draw.text((x0 + 10, y0 + 425), f"{index + 1}. {status}", fill=color, font=small)
        draw.text((x0 + 10, y0 + 450), f"{row.get('template_id')} • {row.get('platform')} • {row.get('module_mode')}", fill=(30, 30, 30), font=small)
        draw.text((x0 + 10, y0 + 472), clean(row.get("headline"))[:66], fill=(50, 50, 50), font=small)
        draw.text((x0 + 10, y0 + 494), f"logos={row.get('team_logo_count')} fidelity={row.get('fidelity_score')} source={row.get('source_id')}", fill=(70, 70, 70), font=small)
        reasons = clean(row.get("technical_reasons"))
        draw.text((x0 + 10, y0 + 516), reasons[:80] or "technical gate passed", fill=(95, 95, 95), font=small)
    output_path = root / CONTACT_SHEET
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=92)


def copy_live_outputs(root: Path, approved: List[Dict[str, Any]]) -> None:
    live_root = root / LIVE_ROOT
    if live_root.exists():
        shutil.rmtree(live_root)
    for row in approved:
        source = root / clean(row.get("output_path"))
        platform = clean(row.get("platform")) or "unknown"
        destination = live_root / platform / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        row["live_output_path"] = destination.relative_to(root).as_posix()
    write_csv(root / HANDOFF_MANIFEST, approved, FIELDS)


def evaluate(root: Path, mode: str) -> Dict[str, Any]:
    policy = read_json(root / POLICY)
    rows, manifest, source_truth, asset_report = merge_rows(root)
    candidates: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    for item in rows:
        output = root / clean(item.get("output_path"))
        render_hash = sha256(output) if output.exists() else ""
        reasons = technical_reasons(item, policy, mode, root, source_truth)
        technical_floor, release_threshold, release_status, polish_reason = fidelity_policy(item, policy)
        status = "live_technical_candidate" if not reasons else "blocked_live_candidate"
        row = {
            **item,
            "live_approval_id": make_approval_id(item, render_hash),
            "render_sha256": render_hash,
            "technical_status": status,
            "technical_reasons": ";".join(reasons),
            "source_truth_status": clean(source_truth.get("status")),
            "release_recommendation_status": release_status if status == "live_technical_candidate" else "not_release_ready",
            "polish_reasons": polish_reason if status == "live_technical_candidate" else "",
            "technical_fidelity_floor": f"{technical_floor:.3f}",
            "release_fidelity_threshold": f"{release_threshold:.3f}",
            "final_score_polish_status": clean(item.get("final_score_polish_status")),
            "final_score_polish_score": clean(item.get("final_score_polish_score")),
            "final_score_polish_reasons": clean(item.get("final_score_polish_reasons")),
            "content_module_status": clean(item.get("content_module_status")),
            "content_module_score": clean(item.get("content_module_score")),
            "content_module_reasons": clean(item.get("content_module_reasons")),
            "content_module_mode": clean(item.get("content_module_mode")),
            "content_module_title": clean(item.get("content_module_title")),
            "content_module_body": clean(item.get("content_module_body")),
            "content_module_stat_count": as_int(item.get("content_module_stat_count")),
            "content_module_prompt": clean(item.get("content_module_prompt")),
            "decision": "",
            "reviewer": "",
            "reviewed_at": "",
            "reason": "",
            "live_output_path": "",
            "live_post_ready": "false",
        }
        (candidates if status == "live_technical_candidate" else blocked).append(row)

    decisions_path = locate_decisions(root, policy)
    decision_rows = read_csv(decisions_path)
    decision_map = {clean(row.get("live_approval_id")): row for row in decision_rows if clean(row.get("live_approval_id"))}
    approved: List[Dict[str, Any]] = []
    decision_blockers: List[str] = []
    rejected_count = 0
    for row in candidates:
        decision = decision_map.get(clean(row.get("live_approval_id")))
        if not decision:
            continue
        value = clean(decision.get("decision")).lower()
        if value not in ALLOWED_DECISIONS:
            decision_blockers.append(f"invalid_decision:{row['live_approval_id']}:{value}")
            continue
        if clean(decision.get("render_sha256")) != clean(row.get("render_sha256")):
            decision_blockers.append(f"render_sha_mismatch:{row['live_approval_id']}")
            continue
        if value == "approved":
            if policy.get("release_recommendation_required_for_handoff", True) and clean(row.get("release_recommendation_status")) != "release_ready_recommended":
                decision_blockers.append(f"cannot_handoff_needs_visual_polish:{row['live_approval_id']}")
                continue
            merged = {**row, **decision, "decision": value, "live_post_ready": "true"}
            approved.append(merged)
        elif value in {"rejected", "needs_fix", "hold"}:
            rejected_count += 1

    all_rows = candidates + blocked
    write_csv(root / CANDIDATES_CSV, candidates, FIELDS)
    write_csv(root / BLOCKED_CSV, blocked, FIELDS)
    write_csv(root / APPROVED_CSV, approved, FIELDS)
    write_csv(root / DECISIONS_TEMPLATE, [
        {
            "live_approval_id": row["live_approval_id"],
            "decision": "",
            "reviewer": "",
            "reviewed_at": "",
            "reason": "",
            "render_sha256": row["render_sha256"],
        }
        for row in candidates
    ], DECISION_FIELDS)
    build_contact_sheet(root, all_rows)

    if mode == "fixture_audit":
        fixture_escape = [row for row in candidates if source_is_fixture(clean(row.get("source_id")), clean(row.get("item_id")), policy)]
        blockers = ["fixture_row_escaped_live_gate"] if fixture_escape else []
        status = "passed_fixture_separation_audit" if not blockers else "blocked_fixture_separation_audit"
        strict_exit = 0 if not blockers else 2
        approved = []
    else:
        blockers = list(decision_blockers)
        if not rows:
            status = "waiting_for_live_data"
            strict_exit = 0
        elif not candidates:
            status = "blocked_live_post_ready_technical_gate"
            strict_exit = 2
            blockers.append("no_live_technical_candidates")
        elif not decision_rows:
            status = "waiting_for_live_visual_approval"
            strict_exit = 0
        elif blockers:
            status = "blocked_live_visual_approval"
            strict_exit = 2
        elif approved:
            status = "live_post_ready_handoff_ready"
            strict_exit = 0
            copy_live_outputs(root, approved)
        else:
            status = "live_visual_approval_complete_no_approved_assets"
            strict_exit = 0

    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "status": status,
        "strict_exit_code": strict_exit,
        "renderer_version": clean(manifest.get("version")),
        "source_truth_status": clean(source_truth.get("status")),
        "asset_preparation_status": clean(asset_report.get("status")),
        "rendered_rows": len(rows),
        "technical_candidate_count": len(candidates),
        "release_ready_recommended_count": len([row for row in candidates if clean(row.get("release_recommendation_status")) == "release_ready_recommended"]),
        "needs_visual_polish_count": len([row for row in candidates if clean(row.get("release_recommendation_status")) == "needs_visual_polish_before_handoff"]),
        "technical_blocked_count": len(blocked),
        "decision_rows": len(decision_rows),
        "approved_live_count": len(approved),
        "rejected_or_hold_count": rejected_count,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "limited_live_operator_handoff_allowed": bool(mode == "live_data" and approved and not blockers),
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "human_visual_approval_required": True,
        "rows": all_rows,
        "outputs": {
            "candidates_csv": (root / CANDIDATES_CSV).as_posix(),
            "blocked_csv": (root / BLOCKED_CSV).as_posix(),
            "approved_csv": (root / APPROVED_CSV).as_posix(),
            "decisions_template_csv": (root / DECISIONS_TEMPLATE).as_posix(),
            "contact_sheet": (root / CONTACT_SHEET).as_posix(),
            "live_handoff_manifest": (root / HANDOFF_MANIFEST).as_posix(),
        },
    }
    return report


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 6J Final-Score Content Module Live Gate",
        "",
        f"Mode: `{report['mode']}`",
        f"Status: `{report['status']}`",
        f"Rendered rows: `{report['rendered_rows']}`",
        f"Technical candidates: `{report['technical_candidate_count']}`",
        f"Technical blocked: `{report['technical_blocked_count']}`",
        f"Approved live assets: `{report['approved_live_count']}`",
        f"Limited live operator handoff allowed: `{report['limited_live_operator_handoff_allowed']}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += [
        "",
        "## Meaning",
        "",
        "Fixture approvals remain proof-only. Live rows must use real source events, exact approved team logos, real player assets where applicable, passing masks, final-score structural polish, passing content modules, and a live render-hash approval.",
        "Even after the gate passes, outputs move only to a limited operator handoff folder. Nothing is auto-published.",
    ]
    (root / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Renderer v4 assets for live HSD operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = evaluate(root, args.mode)
    write_report(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": report["mode"],
        "status": report["status"],
        "rendered_rows": report["rendered_rows"],
        "technical_candidate_count": report["technical_candidate_count"],
        "technical_blocked_count": report["technical_blocked_count"],
        "approved_live_count": report["approved_live_count"],
        "blockers": report["blockers"],
    }, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
