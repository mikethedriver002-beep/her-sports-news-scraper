from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v1.4-phase6k-final-score-story-handoff-live-gate"
PATCH_VERSION = "v4.6-phase6k-story-handoff-polish"
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "validate_hsd_live_post_ready_v4.py"
PHASE6K_POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_phase6k_v4.json")
STORY_TEMPLATE = "hsd_game_recap_final_score_c_story"
STORY_FIELDS = [
    "render_patch_version",
    "story_context_status",
    "story_context_score",
    "story_context_reasons",
    "story_context_mode",
    "story_context_copy",
    "story_cta_status",
    "story_cta_score",
    "story_cta_reasons",
    "story_cta_prompt",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def as_float(value: Any) -> float:
    try:
        return float(clean(value) or "0")
    except Exception:
        return 0.0


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("hsd_live_post_ready_phase6k_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load live gate: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_phase6k_gate(base: Any) -> Any:
    if getattr(base, "_HSD_PHASE6K_INSTALLED", False):
        return base

    original_technical_reasons = base.technical_reasons
    base.POLICY = PHASE6K_POLICY
    for field in STORY_FIELDS:
        if field not in base.FIELDS:
            base.FIELDS.append(field)

    def technical_reasons(
        item: Dict[str, Any],
        policy: Dict[str, Any],
        mode: str,
        root: Path,
        source_truth: Dict[str, Any],
    ) -> List[str]:
        reasons = list(original_technical_reasons(item, policy, mode, root, source_truth))
        if clean(item.get("template_id")) != STORY_TEMPLATE:
            return sorted(set(reasons))
        if not policy.get("phase6k_final_score_story_handoff_required", True):
            return sorted(set(reasons))

        if clean(item.get("render_patch_version")) != PATCH_VERSION:
            reasons.append("phase6k_story_patch_missing")
        context_min = as_float(policy.get("minimum_final_score_story_context_score") or 0.95)
        cta_min = as_float(policy.get("minimum_final_score_story_cta_score") or 0.95)
        if clean(item.get("story_context_status")) != "passed_final_score_story_context":
            reasons.append("final_score_story_context_not_passed")
        if as_float(item.get("story_context_score")) < context_min:
            reasons.append("final_score_story_context_score_below_minimum")
        if clean(item.get("story_cta_status")) != "passed_final_score_story_cta_hierarchy":
            reasons.append("final_score_story_cta_not_passed")
        if as_float(item.get("story_cta_score")) < cta_min:
            reasons.append("final_score_story_cta_score_below_minimum")

        rendered_copy = " ".join([
            clean(item.get("story_context_copy")),
            clean(item.get("story_cta_prompt")),
        ]).upper()
        for token in policy.get("final_score_story_forbidden_tokens") or []:
            token_upper = clean(token).upper()
            if token_upper and token_upper in rendered_copy:
                reasons.append(f"forbidden_final_score_story_copy:{token_upper}")
        prompt = clean(item.get("story_cta_prompt")).upper()
        generic = {clean(value).upper() for value in policy.get("final_score_story_generic_prompts") or [] if clean(value)}
        if not prompt:
            reasons.append("final_score_story_cta_prompt_missing")
        elif prompt in generic:
            reasons.append("final_score_story_cta_prompt_generic")
        return sorted(set(reasons))

    base.technical_reasons = technical_reasons
    base._HSD_PHASE6K_INSTALLED = True
    return base


def write_phase6k_report(base: Any, root: Path, report: Dict[str, Any]) -> None:
    report["version"] = VERSION
    report["phase6k_story_handoff_gate_active"] = True
    report["effective_renderer_version"] = PATCH_VERSION
    report["production_cutover_allowed"] = False
    report["auto_publish_allowed"] = False
    report["human_visual_approval_required"] = True
    base.write_report(root, report)

    md_path = root / base.REPORT_MD
    if md_path.exists():
        text = md_path.read_text(encoding="utf-8")
        text = text.replace(
            "# HSD Phase 6J Final-Score Content Module Live Gate",
            "# HSD Phase 6K Final Score Story Handoff Live Gate",
            1,
        )
        text += "\nPhase 6K additionally blocks Story renders containing unknown/TBA context copy or a non-matchup-specific CTA. Changed Story hashes still require fresh human approval.\n"
        md_path.write_text(text, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6K assets for limited HSD operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    base = install_phase6k_gate(load_base())
    report = base.evaluate(root, args.mode)
    write_phase6k_report(base, root, report)
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
