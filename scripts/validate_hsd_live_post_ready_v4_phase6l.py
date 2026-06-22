from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hsd_phase6l_editorial_language import PUBLIC_COPY_PASS, clean

VERSION = "v1.7-phase6l-live-gate-import-and-prereq-fail-closed"
ROOT = Path(__file__).resolve().parents[1]
PHASE6K_GATE_PATH = ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py"
RAW_GATE_PATH = ROOT / "scripts" / "validate_hsd_live_post_ready_v4.py"
PHASE6L_POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_phase6l_v4.json")
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
REPORT_JSON = Path("live_post_ready_v4_report.json")
REPORT_MD = Path("live_post_ready_v4_report.md")
FINAL_TEMPLATES = {
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_b",
    "hsd_game_recap_final_score_c_story",
}
EXTRA_FIELDS = [
    "editorial_language_version",
    "editorial_headline",
    "editorial_body",
    "editorial_scoreline",
    "editorial_cta_prompt",
    "editorial_margin_band",
    "public_copy_quality_status",
    "public_copy_quality_score",
    "public_copy_banned_count",
    "public_copy_banned_tokens",
]
REQUIRED_FIXTURE_REPORTS = {
    "template_renderer_v4_validation_report.json": "passed_renderer_v4_validation",
    "template_fidelity_v4_report.json": "passed_fidelity_setup",
    "near_post_ready_v4_report.json": "passed_near_post_ready_setup",
    "final_score_content_modules_v4_report.json": "passed_final_score_content_modules",
    "story_context_cta_v4_report.json": "passed_story_context_cta",
    "public_copy_quality_v4_report.json": "passed_public_copy_quality",
}
REQUIRED_LIVE_REPORTS = {
    "v4_source_truth_guard.json": "passed_source_truth_guard",
    "live_asset_preparation_v4_report.json": "passed_live_asset_preparation",
    "template_renderer_v4_validation_report.json": "passed_renderer_v4_validation",
    "template_fidelity_v4_report.json": "passed_fidelity_setup",
    "near_post_ready_v4_report.json": "passed_near_post_ready_setup",
    "final_score_content_modules_v4_report.json": "passed_final_score_content_modules",
    "story_context_cta_v4_report.json": "passed_story_context_cta",
    "public_copy_quality_v4_report.json": "passed_public_copy_quality",
}


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


def phase6k_live_gate() -> Any:
    """Return the installed Phase 6K live gate module.

    Hotfix 3 exposed that the wrapper was fragile: in some workflow contexts the
    loaded module behaved like the raw gate and did not expose install_phase6k_gate.
    This loader accepts either shape and fails closed only when neither shape has
    the expected evaluate/write_report API.
    """
    phase6k = load_module(PHASE6K_GATE_PATH, "hsd_phase6k_live_gate_for_phase6l")
    if hasattr(phase6k, "install_phase6k_gate") and hasattr(phase6k, "load_base"):
        return phase6k.install_phase6k_gate(phase6k.load_base())
    if hasattr(phase6k, "evaluate") and hasattr(phase6k, "write_report"):
        return phase6k
    raw = load_module(RAW_GATE_PATH, "hsd_raw_live_gate_for_phase6l")
    if hasattr(raw, "evaluate") and hasattr(raw, "write_report"):
        return raw
    raise RuntimeError("Unable to resolve a compatible live-post-ready gate module")


def install_phase6l_gate(base: Any) -> Any:
    if getattr(base, "_HSD_PHASE6L_INSTALLED", False):
        return base
    original_technical_reasons = base.technical_reasons
    base.POLICY = PHASE6L_POLICY
    for field in EXTRA_FIELDS:
        if field not in base.FIELDS:
            base.FIELDS.append(field)

    def technical_reasons(item: Dict[str, Any], policy: Dict[str, Any], mode: str, root: Path, source_truth: Dict[str, Any]) -> List[str]:
        reasons = list(original_technical_reasons(item, policy, mode, root, source_truth))
        if clean(item.get("template_id")) in FINAL_TEMPLATES and policy.get("phase6l_public_copy_quality_required", True):
            if clean(item.get("public_copy_quality_status")) != PUBLIC_COPY_PASS:
                reasons.append("phase6l_public_copy_quality_not_passed")
            if int(float(clean(item.get("public_copy_banned_count")) or "0")) > 0:
                reasons.append("phase6l_public_copy_contains_banned_phrase")
            if not clean(item.get("editorial_headline")):
                reasons.append("phase6l_editorial_headline_missing")
        return sorted(set(reasons))

    base.technical_reasons = technical_reasons
    base._HSD_PHASE6L_INSTALLED = True
    return base


def _report_status_blockers(root: Path, required: Dict[str, str]) -> Tuple[List[str], Dict[str, str], Dict[str, Any]]:
    blockers: List[str] = []
    statuses: Dict[str, str] = {}
    detail: Dict[str, Any] = {}
    for name, expected in required.items():
        payload = read_json(root / name)
        status = clean(payload.get("status"))
        statuses[name] = status
        detail[name] = {
            "status": status,
            "blockers": payload.get("blockers") or [],
            "warnings": payload.get("warnings") or [],
        }
        if not payload:
            blockers.append(f"missing_report:{name}")
        elif status != expected:
            blockers.append(f"report_not_passed:{name}:{status or 'missing_status'}")
            for blocker in payload.get("blockers") or []:
                blockers.append(f"{name}:{blocker}")
    return blockers, statuses, detail


def _manifest_checks(root: Path) -> Tuple[List[str], Dict[str, Any]]:
    blockers: List[str] = []
    manifest = read_json(root / MANIFEST)
    items = [item for item in manifest.get("items") or [] if isinstance(item, dict)]
    if not manifest:
        blockers.append("renderer_manifest_missing")
        return blockers, manifest
    if manifest.get("phase6l_editorial_language") is not True:
        blockers.append("phase6l_editorial_language_flag_missing")
    if manifest.get("public_copy_quality_required") is not True:
        blockers.append("phase6l_public_copy_quality_required_flag_missing")
    if int(manifest.get("public_copy_blocked_rows") or 0) != 0:
        blockers.append("phase6l_public_copy_blocked_rows_present")
    final_rows = [row for row in items if clean(row.get("template_id")) in FINAL_TEMPLATES]
    if not final_rows:
        blockers.append("phase6l_no_final_score_rows")
    for row in final_rows:
        ident = f"{clean(row.get('template_id'))}:{clean(row.get('platform'))}:{clean(row.get('module_mode'))}"
        if clean(row.get("public_copy_quality_status")) != PUBLIC_COPY_PASS:
            blockers.append(f"phase6l_public_copy_not_passed:{ident}")
        if int(row.get("public_copy_banned_count") or 0) != 0:
            blockers.append(f"phase6l_public_copy_banned_phrase:{ident}")
        if not clean(row.get("editorial_headline")):
            blockers.append(f"phase6l_editorial_headline_missing:{ident}")
    return blockers, manifest


def _base_report(root: Path, mode: str, status: str, blockers: List[str], rendered_rows: int, statuses: Dict[str, str], details: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "rendered_rows": rendered_rows,
        "technical_candidate_count": 0,
        "technical_blocked_count": rendered_rows,
        "approved_live_count": 0,
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "phase6l_public_copy_gate_active": True,
        "limited_live_operator_handoff_allowed": False,
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "human_visual_approval_required": True,
        "report_statuses": statuses,
        "report_details": details,
    }


def evaluate_fixture_audit(root: Path) -> Dict[str, Any]:
    report_blockers, statuses, details = _report_status_blockers(root, REQUIRED_FIXTURE_REPORTS)
    manifest_blockers, manifest = _manifest_checks(root)
    blockers = report_blockers + manifest_blockers
    rendered_rows = len(manifest.get("items") or []) if isinstance(manifest.get("items"), list) else 0
    report = _base_report(
        root,
        "fixture_audit",
        "passed_phase6l_fixture_quality_audit" if not blockers else "blocked_phase6l_fixture_quality_audit",
        blockers,
        rendered_rows,
        statuses,
        details,
    )
    report["warnings"] = ["fixture_audit_skips_live_handoff_export; live_data still uses the hardened Phase 6K/6L handoff gate"]
    return report


def evaluate_live_prereqs(root: Path) -> Optional[Dict[str, Any]]:
    report_blockers, statuses, details = _report_status_blockers(root, REQUIRED_LIVE_REPORTS)
    manifest_blockers, manifest = _manifest_checks(root)
    blockers = report_blockers + manifest_blockers
    if not blockers:
        return None
    rendered_rows = len(manifest.get("items") or []) if isinstance(manifest.get("items"), list) else 0
    return _base_report(root, "live_data", "blocked_phase6l_live_prerequisites", blockers, rendered_rows, statuses, details)


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 6L Editorial Language Live Gate",
        "",
        f"Mode: `{report['mode']}`",
        f"Status: `{report['status']}`",
        f"Rendered rows: `{report.get('rendered_rows', 0)}`",
        f"Technical candidates: `{report.get('technical_candidate_count', 0)}`",
        f"Technical blocked: `{report.get('technical_blocked_count', 0)}`",
        f"Approved live assets: `{report.get('approved_live_count', 0)}`",
        f"Limited live operator handoff allowed: `{report.get('limited_live_operator_handoff_allowed', False)}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "Human visual approval required: `true`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report.get("blockers", [])] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings", [])] or ["- None"]
    lines += ["", "Phase 6L blocks final-score graphics with weak fallback public language and fails closed when upstream reports are blocked.", ""]
    (root / REPORT_MD).write_text("\n".join(lines), encoding="utf-8")


def run_live_data(root: Path, mode: str) -> Dict[str, Any]:
    prereq_report = evaluate_live_prereqs(root)
    if prereq_report is not None:
        return prereq_report
    base = install_phase6l_gate(phase6k_live_gate())
    report = base.evaluate(root, mode)
    report["version"] = VERSION
    report["phase6l_public_copy_gate_active"] = True
    report["production_cutover_allowed"] = False
    report["auto_publish_allowed"] = False
    report["human_visual_approval_required"] = True
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6L assets for limited HSD operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.mode == "fixture_audit":
            report = evaluate_fixture_audit(root)
        else:
            report = run_live_data(root, args.mode)
    except Exception as exc:
        report = {
            "version": VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "status": "blocked_phase6l_live_gate_exception",
            "strict_exit_code": 2,
            "rendered_rows": 0,
            "technical_candidate_count": 0,
            "technical_blocked_count": 0,
            "approved_live_count": 0,
            "blockers": [f"phase6l_live_gate_exception:{type(exc).__name__}:{exc}"],
            "warnings": [],
            "limited_live_operator_handoff_allowed": False,
            "production_cutover_allowed": False,
            "auto_publish_allowed": False,
            "human_visual_approval_required": True,
        }
    write_report(root, report)
    print(json.dumps({
        "version": VERSION,
        "mode": report["mode"],
        "status": report["status"],
        "rendered_rows": report.get("rendered_rows", 0),
        "technical_candidate_count": report.get("technical_candidate_count", 0),
        "technical_blocked_count": report.get("technical_blocked_count", 0),
        "approved_live_count": report.get("approved_live_count", 0),
        "blockers": report.get("blockers", []),
    }, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
