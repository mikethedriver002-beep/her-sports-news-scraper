from __future__ import annotations

"""Fail-closed Phase 6K wrapper for the limited live operator handoff gate."""

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_hsd_live_post_ready_v4 as base

VERSION = "v1.4-phase6k-story-context-cta-live-gate"
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_v4_phase6k.json")
PREREQUISITES: Dict[str, Tuple[Path, str]] = {
    "clean_plate": (Path("clean_plate_v4_report.json"), "passed_clean_plate_build"),
    "live_asset_preparation": (Path("live_asset_preparation_v4_report.json"), "passed_live_asset_preparation"),
    "renderer_validation": (Path("template_renderer_v4_validation_report.json"), "passed_renderer_v4_validation"),
    "fidelity": (Path("template_fidelity_v4_report.json"), "passed_fidelity_setup"),
    "near_post_ready": (Path("near_post_ready_v4_report.json"), "passed_near_post_ready_setup"),
    "final_score_content": (Path("final_score_content_modules_v4_report.json"), "passed_final_score_content_modules"),
    "story_context_cta": (Path("story_context_cta_v4_report.json"), "passed_story_context_cta"),
}
STORY_TEMPLATE = "hsd_game_recap_final_score_c_story"
APPROVED_CSV = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/live_post_ready/live_post_ready_approved_v4.csv")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def prerequisite_blockers(root: Path) -> Tuple[List[str], Dict[str, Any]]:
    blockers: List[str] = []
    evidence: Dict[str, Any] = {}
    for name, (relative_path, expected_status) in PREREQUISITES.items():
        report = read_json(root / relative_path)
        actual = str(report.get("status") or "")
        evidence[name] = {
            "path": relative_path.as_posix(),
            "expected_status": expected_status,
            "actual_status": actual,
            "strict_exit_code": report.get("strict_exit_code"),
            "blockers": report.get("blockers") or [],
        }
        if not report:
            blockers.append(f"missing_prerequisite_report:{name}")
        elif actual != expected_status:
            blockers.append(f"prerequisite_not_passed:{name}:{actual or 'missing_status'}")
    return sorted(set(blockers)), evidence


def current_decision_summary(root: Path, report: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize only decisions bound to the exact current candidate hashes."""
    policy = base.read_json(root / POLICY)
    decision_path = base.locate_decisions(root, policy)
    decisions = base.read_csv(decision_path)
    candidates = {
        base.clean(row.get("live_approval_id")): row
        for row in (report.get("rows") or [])
        if base.clean(row.get("technical_status")) == "live_technical_candidate"
        and base.clean(row.get("live_approval_id"))
    }
    hash_matched_ids = set()
    decided_ids = set()
    approved_ids = set()
    sha_mismatch_ids = set()
    valid_decisions = {"approved", "rejected", "needs_fix", "hold"}
    for decision in decisions:
        approval_id = base.clean(decision.get("live_approval_id"))
        candidate = candidates.get(approval_id)
        if not candidate:
            continue
        if base.clean(decision.get("render_sha256")) != base.clean(candidate.get("render_sha256")):
            sha_mismatch_ids.add(approval_id)
            continue
        hash_matched_ids.add(approval_id)
        value = base.clean(decision.get("decision")).lower()
        if value in valid_decisions:
            decided_ids.add(approval_id)
        if value == "approved":
            approved_ids.add(approval_id)
    return {
        "decision_path": decision_path.relative_to(root).as_posix() if decision_path.is_relative_to(root) else decision_path.as_posix(),
        "stored_decision_rows": len(decisions),
        "current_candidate_rows": len(candidates),
        "current_render_hash_match_rows": len(hash_matched_ids),
        "current_render_decision_rows": len(decided_ids),
        "current_render_approved_decision_rows": len(approved_ids),
        "current_render_blank_decision_rows": len(hash_matched_ids - decided_ids),
        "current_render_unreviewed_rows": max(0, len(candidates) - len(decided_ids)),
        "unmatched_prior_decision_rows": max(0, len(decisions) - len(hash_matched_ids) - len(sha_mismatch_ids)),
        "render_sha_mismatch_decision_rows": len(sha_mismatch_ids),
    }


def configure(root: Path) -> Tuple[List[str], Dict[str, Any]]:
    prereq_blockers, prereq_evidence = prerequisite_blockers(root)
    original_technical_reasons = base.technical_reasons

    def phase6k_technical_reasons(item, policy, mode, current_root, source_truth):
        reasons = list(original_technical_reasons(item, policy, mode, current_root, source_truth))
        if prereq_blockers:
            reasons.append("phase6k_prerequisite_gate_not_passed")
        rendered_copy = base.clean(item.get("rendered_copy"))
        if policy.get("rendered_copy_metadata_required", True) and not rendered_copy:
            reasons.append("rendered_copy_metadata_missing")
        if base.as_int(item.get("rendered_copy_placeholder_count")) > 0:
            reasons.append("rendered_copy_placeholder_present")
        if base.as_int(item.get("context_placeholder_count")) > 0:
            reasons.append("rendered_context_placeholder_present")
        upper_copy = rendered_copy.upper()
        for token in policy.get("forbidden_live_copy_tokens") or []:
            token_upper = base.clean(token).upper()
            if token_upper and token_upper in upper_copy:
                reasons.append(f"forbidden_rendered_copy:{token_upper}")
        if base.clean(item.get("template_id")) == STORY_TEMPLATE:
            if base.clean(item.get("story_cta_status")) != "passed_story_context_cta":
                reasons.append("story_context_cta_not_passed")
            if base.as_float(item.get("story_cta_score")) < base.as_float(policy.get("minimum_story_cta_score") or 0.95):
                reasons.append("story_cta_score_below_minimum")
            winner = base.clean(item.get("story_winner_short_name")).upper()
            prompt = base.clean(item.get("story_prompt")).upper()
            if not winner or winner not in prompt:
                reasons.append("story_prompt_not_matchup_specific")
            if base.clean(item.get("context_location_status")) not in {"verified", "omitted_missing"}:
                reasons.append("story_context_location_status_invalid")
        return sorted(set(reasons))

    base.VERSION = VERSION
    base.POLICY = POLICY
    for field in [
        "context_segments", "context_location_status", "context_placeholder_count",
        "rendered_copy", "rendered_copy_placeholder_count",
        "story_winner_short_name", "story_prompt", "story_cta_label",
        "story_cta_body", "story_cta_status", "story_cta_score",
    ]:
        if field not in base.FIELDS:
            base.FIELDS.append(field)
    base.technical_reasons = phase6k_technical_reasons
    return prereq_blockers, prereq_evidence


def clear_stale_live_outputs(root: Path) -> None:
    """Remove handoff files before every evaluation so blocked runs cannot re-export stale assets."""
    live_root = root / base.LIVE_ROOT
    if live_root.exists():
        shutil.rmtree(live_root)


def defer_incomplete_visual_review(
    root: Path,
    report: Dict[str, Any],
    decision_summary: Dict[str, Any],
    mode: str,
) -> bool:
    """Fail closed until every current technical candidate has a current-hash decision.

    Existing exact-hash approvals remain visible in ``decision_hash_summary``, but
    no handoff files or approved CSV rows are exported while any current candidate
    is still unreviewed. A non-strict review run can therefore finish and upload
    evidence, while a strict handoff-verification run fails until review is complete.
    """
    if mode != "live_data":
        return False
    if int(report.get("technical_candidate_count") or 0) < 1:
        return False
    if report.get("blockers"):
        return False
    unreviewed = int(decision_summary.get("current_render_unreviewed_rows") or 0)
    if unreviewed < 1:
        return False

    decided = int(decision_summary.get("current_render_decision_rows") or 0)
    report["status"] = (
        "waiting_for_live_visual_approval"
        if decided == 0
        else "waiting_for_remaining_live_visual_approval"
    )
    report["strict_exit_code"] = 2
    report["limited_live_operator_handoff_allowed"] = False
    report["handoff_deferred_until_current_candidate_review_complete"] = True
    report["deferred_current_hash_approval_count"] = int(
        decision_summary.get("current_render_approved_decision_rows") or 0
    )
    report["approved_live_count"] = 0
    for row in report.get("rows") or []:
        row["live_post_ready"] = "false"
        row["live_output_path"] = ""
    clear_stale_live_outputs(root)
    approved_csv = root / APPROVED_CSV
    approved_csv.parent.mkdir(parents=True, exist_ok=True)
    with approved_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=base.FIELDS, extrasaction="ignore")
        writer.writeheader()
    return True


def write_phase6k_markdown(root: Path, report: Dict[str, Any]) -> None:
    lines = [
        "# HSD Phase 6K Story Context + CTA Live Gate",
        "",
        f"Mode: `{report['mode']}`",
        f"Status: `{report['status']}`",
        f"Rendered rows: `{report['rendered_rows']}`",
        f"Technical candidates: `{report['technical_candidate_count']}`",
        f"Technical blocked: `{report['technical_blocked_count']}`",
        f"Approved live assets: `{report['approved_live_count']}`",
        f"Current-hash decisions: `{report.get('current_render_decision_rows', 0)}`",
        f"Unreviewed current candidates: `{report.get('current_render_unreviewed_rows', 0)}`",
        f"Current-hash approvals deferred pending complete review: `{report.get('deferred_current_hash_approval_count', 0)}`",
        f"Limited live operator handoff allowed: `{report['limited_live_operator_handoff_allowed']}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Prerequisite blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report.get("prerequisite_blockers") or []] or ["- None"]
    summary = report.get("decision_hash_summary") or {}
    lines += [
        "",
        "## Current render-hash decisions",
        "",
        f"Stored decision rows: `{summary.get('stored_decision_rows', 0)}`",
        f"Exact current-render hash matches: `{summary.get('current_render_hash_match_rows', 0)}`",
        f"Exact current-render decisions: `{summary.get('current_render_decision_rows', 0)}`",
        f"Blank current-render decision rows: `{summary.get('current_render_blank_decision_rows', 0)}`",
        f"Current candidates awaiting review: `{summary.get('current_render_unreviewed_rows', 0)}`",
        f"Prior unmatched decisions ignored: `{summary.get('unmatched_prior_decision_rows', 0)}`",
    ]
    lines += ["", "## Gate blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += [
        "",
        "## Meaning",
        "",
        "This gate is fail-closed. Renderer, fidelity, near-post-ready, content-module, and Story context/CTA reports must all pass before any asset can become a live technical candidate.",
        "Every approval remains bound to the exact new render SHA-256. Previous Phase 6H/6J approvals are not reused after a render changes.",
        "Nothing is auto-published and production cutover remains disabled.",
    ]
    (root / base.REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6K assets for limited live operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    prereq_blockers, prereq_evidence = configure(root)
    clear_stale_live_outputs(root)
    report = base.evaluate(root, args.mode)
    decision_summary = current_decision_summary(root, report)
    report["version"] = VERSION
    report["prerequisite_reports"] = prereq_evidence
    report["prerequisite_blockers"] = prereq_blockers
    report["decision_hash_summary"] = decision_summary
    report["current_render_decision_rows"] = decision_summary["current_render_decision_rows"]
    report["current_render_unreviewed_rows"] = decision_summary["current_render_unreviewed_rows"]
    report["unmatched_prior_decision_rows"] = decision_summary["unmatched_prior_decision_rows"]
    warnings = list(report.get("warnings") or [])
    if args.mode == "live_data" and decision_summary["unmatched_prior_decision_rows"]:
        warnings.append("prior_decisions_without_current_phase6k_hash_match_ignored")
    if args.mode == "live_data" and decision_summary["current_render_unreviewed_rows"]:
        warnings.append("current_phase6k_candidates_awaiting_visual_approval")
    report["warnings"] = sorted(set(warnings))
    if prereq_blockers:
        report["status"] = "blocked_phase6k_prerequisite_gate"
        report["strict_exit_code"] = 2
        report["approved_live_count"] = 0
        report["limited_live_operator_handoff_allowed"] = False
        report["blockers"] = sorted(set((report.get("blockers") or []) + prereq_blockers))
    else:
        defer_incomplete_visual_review(root, report, decision_summary, args.mode)
    report["production_cutover_allowed"] = False
    report["auto_publish_allowed"] = False
    (root / base.REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_phase6k_markdown(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": report["mode"],
        "status": report["status"],
        "rendered_rows": report["rendered_rows"],
        "technical_candidate_count": report["technical_candidate_count"],
        "technical_blocked_count": report["technical_blocked_count"],
        "approved_live_count": report["approved_live_count"],
        "current_render_decision_rows": report.get("current_render_decision_rows", 0),
        "current_render_unreviewed_rows": report.get("current_render_unreviewed_rows", 0),
        "prerequisite_blockers": prereq_blockers,
        "blockers": report["blockers"],
    }, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
