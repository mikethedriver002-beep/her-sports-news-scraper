from __future__ import annotations

"""Phase 7/8A limited-handoff gate.

WNBA candidates continue through the Phase 6M live gate. Multi-sport review
cards remain review-only until each sport receives a dedicated source-truth and
handoff lane. Phase 8A may emit newer report names and hotfix renderer versions,
so this gate accepts Phase 7 and Phase 8A report contracts without weakening
generic-copy, duplicate-clause, or asset-safety validation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_hsd_live_post_ready_v4_phase6m as phase6m
from hsd_phase7_editorial_engine import clean

VERSION = "v2.2-phase8a-hotfix2-compatible-multisport-editorial-live-gate"
REPORT_JSON = Path("live_post_ready_v4_report.json")
REPORT_MD = Path("live_post_ready_v4_report.md")

REPORT_GROUPS = [
    {
        "label": "event_packets",
        "options": [
            ("phase7_event_packets_report.json", {"passed_phase7_event_packets"}),
        ],
    },
    {
        "label": "multisport_renderer",
        "options": [
            ("phase7_multisport_renderer_report.json", {"passed_phase7_multisport_renderer"}),
            ("phase8a_multisport_renderer_report.json", {"passed_phase7_multisport_renderer", "passed_phase8a_multisport_renderer"}),
        ],
    },
    {
        "label": "editorial_quality",
        "options": [
            ("phase7_editorial_quality_report.json", {"passed_phase7_editorial_quality"}),
            ("phase8a_editorial_quality_report.json", {"passed_phase8a_editorial_quality"}),
        ],
    },
]

EXTRA_FIELDS = [
    "phase7_effective_renderer_version",
    "phase7_editorial_version",
    "phase7_editorial_sport_id",
    "phase7_editorial_kind",
    "phase7_editorial_headline",
    "phase7_debate_question",
    "phase7_watch_title",
    "phase7_watch_body",
    "phase7_cta",
    "phase7_editorial_quality_status",
    "phase7_editorial_quality_score",
    "phase7_editorial_quality_reasons",
    "phase7_editorial_banned_count",
    "phase7_editorial_banned_tokens",
    "phase7_editorial_public_copy",
    "phase8a_effective_renderer_version",
    "phase8a_editorial_version",
    "phase8a_editorial_sport_id",
    "phase8a_editorial_kind",
    "phase8a_editorial_headline",
    "phase8a_debate_question",
    "phase8a_watch_title",
    "phase8a_watch_body",
    "phase8a_cta",
    "phase8a_editorial_quality_status",
    "phase8a_editorial_quality_score",
    "phase8a_editorial_quality_reasons",
    "phase8a_editorial_banned_count",
    "phase8a_editorial_banned_tokens",
    "phase8a_duplicate_clause_count",
    "phase8a_duplicate_clause_details",
    "phase8a_editorial_public_copy",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _phase_report_blockers(root: Path) -> Tuple[List[str], Dict[str, str]]:
    blockers: List[str] = []
    statuses: Dict[str, str] = {}
    for group in REPORT_GROUPS:
        group_label = clean(group.get("label"))
        matched = False
        present = False
        for name, allowed_statuses in group.get("options") or []:
            payload = read_json(root / name)
            status = clean(payload.get("status"))
            statuses[name] = status
            if not payload:
                continue
            present = True
            if status in allowed_statuses:
                matched = True
                break
            blockers.append(f"report_not_passed:{name}:{status or 'missing_status'}")
            blockers.extend(f"{name}:{value}" for value in payload.get("blockers") or [])
        if not present:
            option_names = ",".join(name for name, _ in group.get("options") or [])
            blockers.append(f"missing_report_group:{group_label}:{option_names}")
        elif not matched:
            blockers.append(f"no_passing_report_for_group:{group_label}")
    return blockers, statuses


def phase7_prereq_blockers(root: Path, mode: str) -> Tuple[List[str], Dict[str, str]]:
    blockers, statuses = phase6m.prereq_blockers(root, mode)
    phase_blockers, phase_statuses = _phase_report_blockers(root)
    blockers.extend(phase_blockers)
    statuses.update(phase_statuses)
    return sorted(set(blockers)), statuses


def _phase8a_passed(item: Dict[str, Any]) -> bool:
    status = clean(item.get("phase8a_editorial_quality_status"))
    if status:
        return status == "passed_phase8a_editorial_quality"
    return clean(item.get("phase7_editorial_quality_status")) == "passed_phase7_editorial_quality"


def _phase8a_banned_count(item: Dict[str, Any]) -> int:
    if clean(item.get("phase8a_editorial_banned_count")):
        return int(item.get("phase8a_editorial_banned_count") or 0)
    return int(item.get("phase7_editorial_banned_count") or 0)


def _phase8a_duplicate_count(item: Dict[str, Any]) -> int:
    if clean(item.get("phase8a_duplicate_clause_count")):
        return int(item.get("phase8a_duplicate_clause_count") or 0)
    return 0


def _renderer_version_ok(item: Dict[str, Any]) -> bool:
    phase8a_version = clean(item.get("phase8a_effective_renderer_version"))
    if phase8a_version and "phase8a" in phase8a_version and "editorial-language-fit-assets" in phase8a_version:
        return True
    return clean(item.get("phase7_effective_renderer_version")) == "v5.0-phase7-multisport-editorial-engine"


def installed_base() -> Any:
    base = phase6m.installed_base()
    for field in EXTRA_FIELDS:
        if field not in base.FIELDS:
            base.FIELDS.append(field)
    original_reasons = base.technical_reasons

    def technical_reasons(item: Dict[str, Any], policy: Dict[str, Any], mode: str, root: Path, source_truth: Dict[str, Any]) -> List[str]:
        reasons = list(original_reasons(item, policy, mode, root, source_truth))
        if clean(item.get("template_id")) == "hsd_tonight_in_the_w_a":
            if not _phase8a_passed(item):
                reasons.append("multisport_editorial_quality_not_passed")
            if _phase8a_banned_count(item) != 0:
                reasons.append("generic_editorial_copy_present")
            if _phase8a_duplicate_count(item) != 0:
                reasons.append("duplicate_editorial_clause_present")
            if not _renderer_version_ok(item):
                reasons.append("multisport_effective_renderer_missing")
        return sorted(set(reasons))

    base.technical_reasons = technical_reasons
    return base


def blocked_report(mode: str, blockers: List[str], statuses: Dict[str, str]) -> Dict[str, Any]:
    report = phase6m.blocked_report(mode, blockers, statuses)
    report.update(
        {
            "version": VERSION,
            "status": "blocked_multisport_live_prerequisites",
            "phase7_multisport_editorial_gate_active": True,
            "phase8a_editorial_gate_active": True,
            "phase7_cross_sport_handoff_allowed": False,
            "phase8a_cross_sport_handoff_allowed": False,
        }
    )
    return report


def write_report(root: Path, base: Any, report: Dict[str, Any]) -> None:
    phase6m.write_report(root, base, report)
    report["version"] = VERSION
    report["phase7_multisport_editorial_gate_active"] = True
    report["phase8a_editorial_gate_active"] = True
    report["phase7_cross_sport_handoff_allowed"] = False
    report["phase8a_cross_sport_handoff_allowed"] = False
    report["phase7_cross_sport_review_only"] = True
    report["phase8a_cross_sport_review_only"] = True
    report["production_cutover_allowed"] = False
    report["auto_publish_allowed"] = False
    report["human_visual_approval_required"] = True
    rows = [row for row in report.get("rows") or [] if isinstance(row, dict)]
    report["phase8a_tonight_candidate_count"] = sum(
        clean(row.get("template_id")) == "hsd_tonight_in_the_w_a"
        and clean(row.get("technical_status")) == "live_technical_candidate"
        for row in rows
    )
    report["phase8a_tonight_editorial_passed_count"] = sum(
        clean(row.get("template_id")) == "hsd_tonight_in_the_w_a"
        and _phase8a_passed(row)
        for row in rows
    )
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 7/8A Multi-Sport Editorial Live Gate",
        "",
        f"Mode: `{report.get('mode')}`",
        f"Status: `{report.get('status')}`",
        f"Rendered WNBA rows: `{report.get('rendered_rows', 0)}`",
        f"Technical candidates: `{report.get('technical_candidate_count', 0)}`",
        f"Tonight candidates: `{report.get('phase8a_tonight_candidate_count', report.get('phase7_tonight_candidate_count', 0))}`",
        f"Tonight editorial passed: `{report.get('phase8a_tonight_editorial_passed_count', report.get('phase7_tonight_editorial_passed_count', 0))}`",
        f"Approved live assets: `{report.get('approved_live_count', 0)}`",
        "Cross-sport cards: `review-only`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += [
        "",
        "Phase 8A permits no generic Tonight fallback copy. Non-WNBA review cards are generated and validated, but remain outside live handoff until their source-truth lanes are activated.",
    ]
    (root / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 7/8A limited operator handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    blockers, statuses = phase7_prereq_blockers(root, args.mode)
    base = installed_base()
    if blockers:
        report = blocked_report(args.mode, blockers, statuses)
    else:
        report = base.evaluate(root, args.mode)
        report["report_statuses"] = statuses
    write_report(root, base, report)
    print(
        json.dumps(
            {
                "version": VERSION,
                "mode": report.get("mode"),
                "status": report.get("status"),
                "rendered_rows": report.get("rendered_rows", 0),
                "technical_candidate_count": report.get("technical_candidate_count", 0),
                "phase8a_tonight_candidate_count": report.get("phase8a_tonight_candidate_count", 0),
                "approved_live_count": report.get("approved_live_count", 0),
                "blockers": report.get("blockers", []),
            },
            indent=2,
        )
    )
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
