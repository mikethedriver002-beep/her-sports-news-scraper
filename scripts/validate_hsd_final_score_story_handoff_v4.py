from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v1.0-phase6k-final-score-story-handoff-gate"
PATCH_VERSION = "v4.6-phase6k-story-handoff-polish"
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_phase6k_v4.json")
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
OUT_JSON = Path("final_score_story_handoff_v4_report.json")
OUT_MD = Path("final_score_story_handoff_v4_report.md")
STORY_TEMPLATE = "hsd_game_recap_final_score_c_story"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def number(value: Any) -> float:
    try:
        return float(clean(value) or "0")
    except Exception:
        return 0.0


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def item_reasons(item: Dict[str, Any], policy: Dict[str, Any], root: Path) -> List[str]:
    reasons: List[str] = []
    if not (root / clean(item.get("output_path"))).exists():
        reasons.append("missing_story_render")
    if clean(item.get("render_patch_version")) != PATCH_VERSION:
        reasons.append("phase6k_story_patch_missing")
    if clean(item.get("story_context_status")) != "passed_final_score_story_context":
        reasons.append("story_context_not_passed")
    if number(item.get("story_context_score")) < number(policy.get("minimum_final_score_story_context_score") or 0.95):
        reasons.append("story_context_score_below_minimum")
    if clean(item.get("story_cta_status")) != "passed_final_score_story_cta_hierarchy":
        reasons.append("story_cta_not_passed")
    if number(item.get("story_cta_score")) < number(policy.get("minimum_final_score_story_cta_score") or 0.95):
        reasons.append("story_cta_score_below_minimum")

    context = clean(item.get("story_context_copy")).upper()
    prompt = clean(item.get("story_cta_prompt")).upper()
    if not context:
        reasons.append("missing_story_context_copy")
    if not prompt:
        reasons.append("missing_story_cta_prompt")
    for token in policy.get("final_score_story_forbidden_tokens") or []:
        token_upper = clean(token).upper()
        if token_upper and token_upper in f"{context} {prompt}":
            reasons.append(f"forbidden_story_copy:{token_upper}")
    generic = {clean(value).upper() for value in policy.get("final_score_story_generic_prompts") or [] if clean(value)}
    if prompt in generic:
        reasons.append("generic_story_cta_prompt")
    if clean(item.get("content_module_status")) != "passed_final_score_content_modules":
        reasons.append("content_module_not_passed")
    if clean(item.get("final_score_polish_status")) != "passed_final_score_template_polish":
        reasons.append("template_polish_not_passed")
    if int(number(item.get("zone_overflow_count"))) != 0:
        reasons.append("story_zone_overflow_present")
    return sorted(set(reasons))


def evaluate(root: Path) -> Dict[str, Any]:
    manifest = read_json(root / MANIFEST)
    policy = read_json(root / POLICY)
    items = [dict(item) for item in manifest.get("items") or [] if clean(item.get("template_id")) == STORY_TEMPLATE]
    rows: List[Dict[str, Any]] = []
    for item in items:
        reasons = item_reasons(item, policy, root)
        rows.append({
            **item,
            "story_handoff_status": "passed_final_score_story_handoff" if not reasons else "needs_final_score_story_handoff",
            "story_handoff_reasons": ";".join(reasons),
        })

    blockers: List[str] = []
    if not manifest:
        blockers.append("renderer_manifest_missing")
    if not policy:
        blockers.append("phase6k_story_policy_missing")
    if manifest.get("effective_renderer_version") != PATCH_VERSION:
        blockers.append("effective_renderer_not_phase6k")
    if not rows:
        blockers.append("no_final_score_story_rows")
    if any(row["story_handoff_reasons"] for row in rows):
        blockers.append("story_handoff_failures_present")
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed_final_score_story_handoff" if not blockers else "needs_final_score_story_handoff",
        "strict_exit_code": 0 if not blockers else 2,
        "story_rows": len(rows),
        "passed_story_rows": sum(not row["story_handoff_reasons"] for row in rows),
        "human_visual_approval_required": True,
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "blockers": sorted(set(blockers)),
        "rows": rows,
    }


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / OUT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 6K Final Score Story Handoff Gate",
        "",
        f"Status: `{report['status']}`",
        f"Story rows: `{report['story_rows']}`",
        f"Passed: `{report['passed_story_rows']}`",
        "Human visual approval required: `true`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "Changed Story renders still require a new visual decision bound to the exact SHA-256.", ""]
    (root / OUT_MD).write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = evaluate(root)
    write_report(root, report)
    print(json.dumps({key: report[key] for key in ["version", "status", "story_rows", "blockers"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
