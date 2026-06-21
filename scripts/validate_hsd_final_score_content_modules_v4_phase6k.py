from __future__ import annotations

"""Phase 6K compatibility entry point for the Final Score content-module gate."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_hsd_final_score_content_modules_v4 as base
import validate_hsd_template_renderer_v4_phase6k as renderer_gate

VERSION = "v1.1-phase6k-final-score-content-module-gate"
RENDERER_VERSION = "v4.6-phase6k-story-context-cta-polish"
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_v4_phase6k.json")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    manifest = base.read_json(base.MANIFEST)
    policy = base.read_json(POLICY)
    blockers: List[str] = []
    warnings: List[str] = []
    if manifest.get("version") != RENDERER_VERSION:
        blockers.append("renderer_not_phase6k_v4_6")

    minimum_score = base.as_float(policy.get("minimum_final_score_content_module_score") or 0.95)
    rows = [
        base.validate_row(item, minimum_score)
        for item in (manifest.get("items") or [])
        if base.clean(item.get("template_id")) in base.FINAL_TEMPLATES
    ]
    if not rows:
        blockers.append("no_final_score_rows")
    failed = [row for row in rows if row.get("validation_status") != "passed_content_module_validation"]
    if failed:
        blockers.append("final_score_content_module_failures_present")
    templates = {base.clean(row.get("template_id")) for row in rows}
    for template_id in ["hsd_game_recap_final_score_a", "hsd_game_recap_final_score_c_story"]:
        if template_id not in templates:
            blockers.append(f"missing_required_final_score_content_template:{template_id}")
    if "hsd_game_recap_final_score_b" not in templates:
        if renderer_gate.intentional_final_b_downgrade(manifest):
            warnings.append("final_score_b_not_rendered_intentional_verified_data_downgrade")
        else:
            blockers.append("final_score_b_missing_without_complete_downgrade_routing")

    status = "passed_final_score_content_modules" if not blockers else "blocked_final_score_content_modules"
    report: Dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "renderer_version": manifest.get("version"),
        "final_score_rows": len(rows),
        "passed_rows": len(rows) - len(failed),
        "failed_rows": len(failed),
        "minimum_content_module_score": minimum_score,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "rows": rows,
    }
    base.OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    base.write_csv(base.OUT_CSV, rows, base.FIELDS)
    base.build_contact_sheet(rows)
    lines = [
        "# HSD Phase 6K Final Score Content Module Gate",
        "",
        f"Status: `{status}`",
        f"Final-score rows: `{len(rows)}`",
        f"Passed rows: `{len(rows) - len(failed)}`",
        f"Failed rows: `{len(failed)}`",
        f"Minimum content-module score: `{minimum_score:.2f}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report["warnings"]] or ["- None"]
    base.OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["version", "status", "final_score_rows", "passed_rows", "failed_rows", "blockers", "warnings"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
