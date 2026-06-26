from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hsd_asset_assurance_core import RENDER_SAFE_TEAM_MODES, clean, split_modes

VERSION = "v1.8-phase6m-asset-assurance-live-gate"
ROOT = Path(__file__).resolve().parents[1]
PHASE6L_GATE = ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6l.py"
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_phase6m_v4.json")
REPORT_JSON = Path("live_post_ready_v4_report.json")
REPORT_MD = Path("live_post_ready_v4_report.md")
REQUIRED_REPORTS = {
    "asset_assurance_preflight_v1_report.json": "passed_asset_assurance_preflight",
    "asset_assurance_v1_report.json": "passed_asset_assurance",
    "template_renderer_v4_validation_report.json": "passed_renderer_v4_validation",
    "template_fidelity_v4_report.json": "passed_fidelity_setup",
    "near_post_ready_v4_report.json": "passed_near_post_ready_setup",
    "final_score_content_modules_v4_report.json": "passed_final_score_content_modules",
    "story_context_cta_v4_report.json": "passed_story_context_cta",
    "public_copy_quality_v4_report.json": "passed_public_copy_quality",
}
LIVE_ONLY_REPORTS = {
    "v4_source_truth_guard.json": "passed_source_truth_guard",
}
EXTRA_FIELDS = [
    "asset_assurance_status",
    "asset_assurance_reasons",
    "asset_render_safe",
    "asset_live_candidate_eligible",
    "asset_live_ready_pre_human",
    "asset_requires_visual_approval",
    "asset_release_lane",
    "asset_fallback_review_cue",
    "team_asset_count",
    "team_exact_logo_count",
    "team_fallback_badge_count",
    "asset_assurance_player_mode",
    "asset_assurance_player_route",
    "requested_module_mode",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prereq_blockers(root: Path, mode: str) -> Tuple[List[str], Dict[str, str]]:
    requirements = dict(REQUIRED_REPORTS)
    if mode == "live_data":
        requirements.update(LIVE_ONLY_REPORTS)
    blockers: List[str] = []
    statuses: Dict[str, str] = {}
    for name, expected in requirements.items():
        payload = read_json(root / name)
        status = clean(payload.get("status"))
        statuses[name] = status
        if not payload:
            blockers.append(f"missing_report:{name}")
        elif status != expected:
            blockers.append(f"report_not_passed:{name}:{status or 'missing_status'}")
            blockers.extend(f"{name}:{value}" for value in payload.get("blockers") or [])
    return sorted(set(blockers)), statuses


def installed_base() -> Any:
    phase6l = load_module(PHASE6L_GATE, "hsd_phase6l_live_gate_for_phase6m")
    base = phase6l.install_phase6l_gate(phase6l.phase6k_live_gate())
    base.POLICY = POLICY
    for field in EXTRA_FIELDS:
        if field not in base.FIELDS:
            base.FIELDS.append(field)
    original_technical_reasons = base.technical_reasons
    original_fidelity_policy = base.fidelity_policy

    def technical_reasons(item: Dict[str, Any], policy: Dict[str, Any], mode: str, root: Path, source_truth: Dict[str, Any]) -> List[str]:
        reasons = list(original_technical_reasons(item, policy, mode, root, source_truth))
        render_safe = clean(item.get("asset_render_safe")) == "true"
        eligible = clean(item.get("asset_live_candidate_eligible")) == "true"
        lane = clean(item.get("asset_release_lane"))
        modes = split_modes(item.get("team_logo_modes"))
        assurance_modes_ok = len(modes) >= 2 and all(value in RENDER_SAFE_TEAM_MODES for value in modes)
        if render_safe and assurance_modes_ok and lane in {"hsd_badge_review", "team_spotlight_review", "exact_assets"}:
            reasons = [
                value for value in reasons
                if value not in {"insufficient_exact_team_logos", "text_or_unapproved_logo_fallback"}
            ]
        if not render_safe:
            reasons.append("phase6m_asset_not_render_safe")
        if not eligible:
            reasons.append("phase6m_asset_not_live_candidate_eligible")
        return sorted(set(reasons))

    def fidelity_policy(item: Dict[str, Any], policy: Dict[str, Any]):
        technical_floor, release_threshold, status, reason = original_fidelity_policy(item, policy)
        lane = clean(item.get("asset_release_lane"))
        if lane == "hsd_badge_review" and status != "blocked_below_technical_floor":
            return (
                technical_floor,
                release_threshold,
                "release_ready_recommended",
                "phase6m_hsd_badge_requires_explicit_hash_bound_human_approval",
            )
        if lane == "team_spotlight_review" and status != "blocked_below_technical_floor":
            return (
                technical_floor,
                release_threshold,
                "release_ready_recommended",
                "phase6m_non_player_team_spotlight_requires_hash_bound_human_approval",
            )
        return technical_floor, release_threshold, status, reason

    base.technical_reasons = technical_reasons
    base.fidelity_policy = fidelity_policy
    return base


def blocked_report(mode: str, blockers: List[str], statuses: Dict[str, str]) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "mode": mode,
        "status": "blocked_phase6m_live_prerequisites",
        "strict_exit_code": 2,
        "rendered_rows": 0,
        "technical_candidate_count": 0,
        "technical_blocked_count": 0,
        "approved_live_count": 0,
        "release_ready_recommended_count": 0,
        "needs_visual_polish_count": 0,
        "blockers": blockers,
        "warnings": [],
        "report_statuses": statuses,
        "phase6m_asset_assurance_gate_active": True,
        "limited_live_operator_handoff_allowed": False,
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "human_visual_approval_required": True,
        "rows": [],
    }


def write_report(root: Path, base: Any, report: Dict[str, Any]) -> None:
    if hasattr(base, "write_report"):
        base.write_report(root, report)
    else:
        (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    report["version"] = VERSION
    report["phase6m_asset_assurance_gate_active"] = True
    report["production_cutover_allowed"] = False
    report["auto_publish_allowed"] = False
    report["human_visual_approval_required"] = True
    rows = [row for row in report.get("rows") or [] if isinstance(row, dict)]
    report["hsd_badge_candidate_count"] = sum(clean(row.get("asset_release_lane")) == "hsd_badge_review" and clean(row.get("technical_status")) == "live_technical_candidate" for row in rows)
    report["team_spotlight_candidate_count"] = sum(clean(row.get("asset_release_lane")) == "team_spotlight_review" and clean(row.get("technical_status")) == "live_technical_candidate" for row in rows)
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md = root / REPORT_MD
    text = md.read_text(encoding="utf-8") if md.exists() else "# HSD Phase 6M Asset Assurance Live Gate\n"
    if not text.startswith("# HSD Phase 6M"):
        text = text.replace("# HSD Phase 6J Final-Score Content Module Live Gate", "# HSD Phase 6M Asset Assurance Live Gate", 1)
        text = text.replace("# HSD Phase 6L Editorial Language Live Gate", "# HSD Phase 6M Asset Assurance Live Gate", 1)
    text += (
        "\nPhase 6M keeps every row render-safe. HSD team badges and non-player TEAM SPOTLIGHT fallbacks may enter exact-hash human review, but production cutover and auto-publish remain disabled.\n"
    )
    md.write_text(text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6M assets for limited HSD operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    blockers, statuses = prereq_blockers(root, args.mode)
    base = installed_base()
    if blockers:
        report = blocked_report(args.mode, blockers, statuses)
    else:
        report = base.evaluate(root, args.mode)
        report["report_statuses"] = statuses
    write_report(root, base, report)
    print(json.dumps({
        "version": VERSION,
        "mode": report.get("mode"),
        "status": report.get("status"),
        "rendered_rows": report.get("rendered_rows", 0),
        "technical_candidate_count": report.get("technical_candidate_count", 0),
        "technical_blocked_count": report.get("technical_blocked_count", 0),
        "hsd_badge_candidate_count": report.get("hsd_badge_candidate_count", 0),
        "team_spotlight_candidate_count": report.get("team_spotlight_candidate_count", 0),
        "approved_live_count": report.get("approved_live_count", 0),
        "blockers": report.get("blockers", []),
    }, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
