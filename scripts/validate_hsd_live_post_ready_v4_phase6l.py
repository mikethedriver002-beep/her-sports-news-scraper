from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hsd_phase6l_editorial_language import PUBLIC_COPY_PASS, clean

VERSION = "v1.5-phase6l-editorial-language-live-gate"
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6k.py"
PHASE6L_POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_phase6l_v4.json")
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


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("hsd_live_post_ready_phase6l_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Phase 6K live gate: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_phase6l_gate(base: Any) -> Any:
    if getattr(base, "_HSD_PHASE6L_INSTALLED", False):
        return base
    phase6k_base = base.install_phase6k_gate(base.load_base())
    original_technical_reasons = phase6k_base.technical_reasons
    phase6k_base.POLICY = PHASE6L_POLICY
    for field in EXTRA_FIELDS:
        if field not in phase6k_base.FIELDS:
            phase6k_base.FIELDS.append(field)

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

    phase6k_base.technical_reasons = technical_reasons
    phase6k_base._HSD_PHASE6L_INSTALLED = True
    return phase6k_base


def write_phase6l_report(base: Any, root: Path, report: Dict[str, Any]) -> None:
    report["version"] = VERSION
    report["phase6l_public_copy_gate_active"] = True
    report["production_cutover_allowed"] = False
    report["auto_publish_allowed"] = False
    report["human_visual_approval_required"] = True
    base.write_report(root, report)
    md_path = root / base.REPORT_MD
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        text = text.replace("# HSD Phase 6K Final Score Story Handoff Live Gate", "# HSD Phase 6L Editorial Language Live Gate", 1)
        text += "\nPhase 6L additionally blocks final-score graphics with weak fallback public language.\n"
        md_path.write_text(text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6L assets for limited HSD operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    base = install_phase6l_gate(load_base())
    report = base.evaluate(root, args.mode)
    write_phase6l_report(base, root, report)
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
