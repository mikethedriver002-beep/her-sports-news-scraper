from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from hsd_phase7_editorial_engine import SUPPORTED_SPORTS, clean, entity_short, read_json

VERSION = "v1.0-phase7-editorial-quality-gate"
POLICY = Path("config/graphics/v5/phase7/editorial_policy_v1.json")
WNBA_MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
MULTISPORT_MANIFEST = Path("outputs/latest/HSD_PHASE7_MULTISPORT/phase7_multisport_manifest.json")
EVENT_REPORT = Path("phase7_event_packets_report.json")
MULTISPORT_REPORT = Path("phase7_multisport_renderer_report.json")
OUT_JSON = Path("phase7_editorial_quality_report.json")
OUT_MD = Path("phase7_editorial_quality_report.md")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy(item: Mapping[str, Any]) -> str:
    return clean(item.get("phase7_editorial_public_copy") or item.get("public_copy") or item.get("rendered_copy"))


def _banned_hits(text: str, patterns: Iterable[Any]) -> List[str]:
    upper = clean(text).upper()
    return sorted({clean(pattern).upper() for pattern in patterns if clean(pattern) and clean(pattern).upper() in upper})


def _entity_specific(item: Mapping[str, Any], text: str) -> bool:
    upper = clean(text).upper()
    sport_id = clean(item.get("sport_id") or item.get("phase7_editorial_sport_id") or "wnba")
    values = [clean(item.get("primary_short")), clean(item.get("secondary_short"))]
    headline = clean(item.get("headline"))
    if headline:
        values.append(headline)
        for separator in [" at ", " beat ", " vs ", " v "]:
            if separator in headline.lower():
                parts = re.split(re.escape(separator), headline, maxsplit=1, flags=re.I)
                for part in parts:
                    values.extend([clean(part), entity_short(part, sport_id)])
                break
    for value in values:
        if value and value.upper() in upper:
            return True
    return False


def validate_item(item: Mapping[str, Any], patterns: Iterable[Any], source: str) -> Dict[str, Any]:
    reasons: List[str] = []
    public_copy = _copy(item)
    hits = _banned_hits(public_copy, patterns)
    if hits:
        reasons.append("generic_or_banned_phase7_copy")
    if not public_copy:
        reasons.append("missing_phase7_public_copy")
    if clean(item.get("phase7_editorial_quality_status")) != "passed_phase7_editorial_quality":
        reasons.append("phase7_editorial_quality_not_passed")
    if int(item.get("phase7_editorial_banned_count") or 0) != 0:
        reasons.append("phase7_editorial_banned_count_nonzero")
    kind = clean(item.get("phase7_editorial_kind") or item.get("kind") or item.get("module_mode")).lower()
    if kind in {"preview", "spotlight", "watch_point", "team_spotlight_fallback"} and not _entity_specific(item, public_copy):
        reasons.append("phase7_copy_not_matchup_specific")
    if source == "wnba" and clean(item.get("template_id")) == "hsd_tonight_in_the_w_a":
        if clean(item.get("phase7_effective_renderer_version")) != "v5.0-phase7-multisport-editorial-engine":
            reasons.append("phase7_effective_renderer_version_missing")
    return {
        "source": source,
        "item_id": clean(item.get("item_id") or item.get("event_id")),
        "sport_id": clean(item.get("sport_id") or item.get("phase7_editorial_sport_id") or ("wnba" if source == "wnba" else "")),
        "kind": kind,
        "headline": clean(item.get("headline") or item.get("editorial_headline")),
        "public_copy": public_copy,
        "banned_hits": ";".join(hits),
        "validation_status": "passed_phase7_editorial_validation" if not reasons else "blocked_phase7_editorial_validation",
        "validation_reasons": ";".join(sorted(set(reasons))),
        "fixture_only": bool(item.get("fixture_only")) if isinstance(item.get("fixture_only"), bool) else clean(item.get("fixture_only")).lower() == "true",
    }


def build_report(mode: str) -> Dict[str, Any]:
    policy = read_json(POLICY)
    wnba_manifest = read_json(WNBA_MANIFEST)
    multisport_manifest = read_json(MULTISPORT_MANIFEST)
    event_report = read_json(EVENT_REPORT)
    multisport_report = read_json(MULTISPORT_REPORT)
    blockers: List[str] = []
    warnings: List[str] = []

    if not policy:
        blockers.append("phase7_editorial_policy_missing")
    if not wnba_manifest:
        blockers.append("wnba_renderer_manifest_missing")
    elif wnba_manifest.get("phase7_multisport_editorial_engine") is not True:
        blockers.append("phase7_wnba_renderer_flag_missing")
    if clean(event_report.get("status")) != "passed_phase7_event_packets":
        blockers.append("phase7_event_packets_not_passed")
    if multisport_report and clean(multisport_report.get("status")) != "passed_phase7_multisport_renderer":
        blockers.append("phase7_multisport_renderer_not_passed")

    patterns = policy.get("global_banned_patterns") or []
    wnba_items = [
        item
        for item in wnba_manifest.get("items") or []
        if isinstance(item, dict) and clean(item.get("template_id")) == "hsd_tonight_in_the_w_a"
    ]
    multisport_items = [item for item in multisport_manifest.get("items") or [] if isinstance(item, dict)]
    rows = [validate_item(item, patterns, "wnba") for item in wnba_items]
    rows += [validate_item(item, patterns, "multisport") for item in multisport_items]

    failed = [row for row in rows if row["validation_status"] != "passed_phase7_editorial_validation"]
    if failed:
        blockers.append("phase7_editorial_validation_failures_present")
    if not wnba_items:
        blockers.append("no_phase7_wnba_tonight_rows")

    sport_counts = {sport_id: 0 for sport_id in sorted(SUPPORTED_SPORTS)}
    for row in rows:
        sport_id = clean(row.get("sport_id"))
        if sport_id in sport_counts:
            sport_counts[sport_id] += 1

    if mode == "fixture_audit":
        for sport_id, count in sport_counts.items():
            if count < 1:
                blockers.append(f"phase7_fixture_sport_missing:{sport_id}")
    else:
        fixture_escape = [row for row in rows if row.get("fixture_only")]
        if fixture_escape:
            blockers.append("phase7_fixture_rows_present_in_live_data")
        missing = [sport_id for sport_id in sorted(SUPPORTED_SPORTS - {"wnba"}) if sport_counts[sport_id] == 0]
        if missing:
            warnings.append("non_wnba_phase7_live_cards_not_present:" + ",".join(missing))

    status = "passed_phase7_editorial_quality" if not blockers else "blocked_phase7_editorial_quality"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "mode": mode,
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "validated_rows": len(rows),
        "passed_rows": len(rows) - len(failed),
        "failed_rows": len(failed),
        "wnba_tonight_rows": len(wnba_items),
        "multisport_rows": len(multisport_items),
        "sport_counts": sport_counts,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "human_visual_approval_required": True,
        "rows": rows,
    }


def write_report(report: Mapping[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 7 Editorial Quality Gate",
        "",
        f"Mode: `{report.get('mode')}`",
        f"Status: `{report.get('status')}`",
        f"Validated rows: `{report.get('validated_rows')}`",
        f"Passed rows: `{report.get('passed_rows')}`",
        f"Failed rows: `{report.get('failed_rows')}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Sports",
        "",
    ]
    for sport_id, count in (report.get("sport_counts") or {}).items():
        lines.append(f"- `{sport_id}`: `{count}`")
    lines += ["", "## Blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings") or []] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 7 sport-aware editorial copy.")
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.mode)
    write_report(report)
    print(json.dumps({key: report[key] for key in ["version", "mode", "status", "validated_rows", "passed_rows", "failed_rows", "sport_counts", "blockers", "warnings"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
