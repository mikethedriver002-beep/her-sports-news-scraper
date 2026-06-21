from __future__ import annotations

"""Phase 6K wrapper for the existing visual fidelity gate.

Final Score B is conditional in live data. A missing B render is accepted only
when Renderer v4.6 recorded every B route as an intentional downgrade caused by
an incomplete verified player package. All image-comparison thresholds remain
unchanged.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_hsd_template_fidelity_v4 as base

VERSION = "v1.1-phase6k-conditional-template-fidelity-gate"
RENDER_MANIFEST_JSON = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
FINAL_B = "hsd_game_recap_final_score_b"


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def route_key(row: Dict[str, Any]) -> str:
    return clean(row.get("source_id") or row.get("headline"))


def intentional_final_b_downgrade(manifest: Dict[str, Any]) -> bool:
    raw = manifest.get("final_score_b_routing")
    if not isinstance(raw, list) or not raw or any(not isinstance(row, dict) for row in raw):
        return False
    rows = list(raw)
    expected = {
        route_key(item)
        for item in (manifest.get("items") or [])
        if isinstance(item, dict)
        and clean(item.get("template_id")) == "hsd_game_recap_final_score_a"
        and route_key(item)
    }
    keys = [route_key(row) for row in rows]
    coverage_ok = bool(expected) and all(keys) and len(keys) == len(set(keys)) and set(keys) == expected
    return coverage_ok and all(
        not bool(row.get("rendered"))
        and clean(row.get("route_decision")).startswith("downgraded_to_final_a_")
        for row in rows
    )


def adjust_report(report: Dict[str, Any], manifest: Dict[str, Any]) -> Dict[str, Any]:
    if FINAL_B not in set(report.get("missing_required_templates") or []):
        return report
    if not intentional_final_b_downgrade(manifest):
        return report

    missing = [value for value in report.get("missing_required_templates") or [] if value != FINAL_B]
    blockers = list(report.get("blockers") or [])
    if not missing:
        blockers = [value for value in blockers if value != "missing_required_phase6b_template_render"]
    warnings = list(report.get("warnings") or [])
    warnings.append("final_score_b_fidelity_not_applicable_intentional_verified-data_downgrade")
    report.update({
        "version": VERSION,
        "missing_required_templates": missing,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "final_score_b_fidelity_applicability": "not_applicable_intentional_downgrade",
        "status": "passed_fidelity_setup" if not blockers else "blocked_fidelity_setup",
        "strict_exit_code": 0 if not blockers else 2,
    })
    return report


def main(argv: List[str] | None = None) -> int:
    manifest = read_json(RENDER_MANIFEST_JSON)
    original_build_report = base.build_report

    def phase6k_build_report(rows, matrix):
        report = original_build_report(rows, matrix)
        report["version"] = VERSION
        report["renderer_version"] = manifest.get("version")
        return adjust_report(report, manifest)

    base.VERSION = VERSION
    base.build_report = phase6k_build_report
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
