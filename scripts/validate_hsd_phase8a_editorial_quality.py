from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hsd_phase8a_editorial_engine import VERSION as EDITORIAL_VERSION, clean, editorial_quality, generate_editorial, read_json, similarity

VERSION = "v1.0-phase8a-editorial-fit-quality-gate"
MANIFESTS = [
    Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json"),
    Path("outputs/latest/HSD_PHASE8A_MULTISPORT/phase8a_multisport_manifest.json"),
    Path("outputs/latest/HSD_PHASE7_MULTISPORT/phase7_multisport_manifest.json"),
]
POLICY = Path("config/graphics/v5/phase8a/phrase_library_v1.json")
OUT_JSON = Path("phase8a_editorial_quality_report.json")
OUT_MD = Path("phase8a_editorial_quality_report.md")
OUT_CSV = Path("outputs/latest/HSD_PHASE8A/phase8a_editorial_quality_rows.csv")

FIELDS = ["item_id", "sport_id", "template_id", "headline", "phase8a_editorial_quality_status", "phase8a_editorial_quality_reasons", "phase8a_editorial_banned_count", "phase8a_duplicate_clause_count", "phase8a_duplicate_clause_details", "fit_safe_status"]


def read_items() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in MANIFESTS:
        payload = read_json(path)
        for item in payload.get("items") or []:
            if isinstance(item, dict):
                rows.append({**item, "_manifest_path": path.as_posix()})
    return rows


def phrase_banned_count(row: Mapping[str, Any], library: Mapping[str, Any]) -> int:
    combined = " | ".join(clean(row.get(field)) for field in ["rendered_copy", "public_copy", "phase8a_editorial_public_copy", "phase7_editorial_public_copy", "debate_question", "watch_title", "watch_body", "cta"])
    upper = combined.upper()
    return sum(1 for token in library.get("global_banned_patterns") or [] if clean(token).upper() in upper)


def duplicate_count(row: Mapping[str, Any], threshold: float) -> int:
    values = [clean(row.get(field)) for field in ["phase8a_debate_question", "phase8a_watch_title", "phase8a_watch_body", "phase8a_cta", "debate_question", "watch_title", "watch_body", "cta"] if clean(row.get(field))]
    count = 0
    for i, left in enumerate(values):
        for right in values[i + 1:]:
            if min(len(set(left.upper().split())), len(set(right.upper().split()))) >= 4 and similarity(left, right) >= threshold:
                count += 1
    return count


def fit_safe(row: Mapping[str, Any], library: Mapping[str, Any]) -> bool:
    limits = ((library.get("fit_limits") or {}).get("renderer_tonight") or {})
    if clean(row.get("template_id")) != "hsd_tonight_in_the_w_a":
        limits = ((library.get("fit_limits") or {}).get("review_card") or {})
    field_map = {"debate_question": "phase8a_debate_question", "watch_title": "phase8a_watch_title", "watch_body": "phase8a_watch_body", "cta": "phase8a_cta", "editorial_headline": "phase8a_editorial_headline"}
    for field, phase_field in field_map.items():
        limit = int(limits.get(field) or 0)
        value = clean(row.get(phase_field) or row.get(field))
        if limit and value and len(value) > limit:
            return False
    return True


def validate_row(row: Dict[str, Any], library: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    banned = int(row.get("phase8a_editorial_banned_count") or 0) if clean(row.get("phase8a_editorial_banned_count")) else phrase_banned_count(row, library)
    dupes = int(row.get("phase8a_duplicate_clause_count") or 0) if clean(row.get("phase8a_duplicate_clause_count")) else duplicate_count(row, float(library.get("duplicate_similarity_threshold") or 0.62))
    if banned:
        reasons.append("generic_or_banned_editorial_copy")
    if dupes:
        reasons.append("duplicate_editorial_clause")
    if not fit_safe(row, library):
        reasons.append("fit_safe_limit_exceeded")
    if clean(row.get("phase8a_editorial_quality_status")) and clean(row.get("phase8a_editorial_quality_status")) != "passed_phase8a_editorial_quality":
        reasons.append("phase8a_engine_quality_not_passed")
    status = "passed_phase8a_editorial_quality" if not reasons else "blocked_phase8a_editorial_quality"
    return {
        "item_id": clean(row.get("item_id") or row.get("event_id")),
        "sport_id": clean(row.get("sport_id") or row.get("phase8a_editorial_sport_id") or row.get("phase7_editorial_sport_id") or "wnba"),
        "template_id": clean(row.get("template_id")),
        "headline": clean(row.get("headline") or row.get("editorial_headline") or row.get("phase8a_editorial_headline")),
        "phase8a_editorial_quality_status": status,
        "phase8a_editorial_quality_reasons": ";".join(sorted(set(reasons))),
        "phase8a_editorial_banned_count": banned,
        "phase8a_duplicate_clause_count": dupes,
        "phase8a_duplicate_clause_details": clean(row.get("phase8a_duplicate_clause_details")),
        "fit_safe_status": "fit_safe" if "fit_safe_limit_exceeded" not in reasons else "blocked_fit_unsafe",
    }


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def build_report(mode: str) -> Dict[str, Any]:
    library = read_json(POLICY)
    rows = [validate_row(row, library) for row in read_items()]
    failures = [row for row in rows if row["phase8a_editorial_quality_status"] != "passed_phase8a_editorial_quality"]
    blockers: List[str] = []
    warnings: List[str] = []
    if not rows:
        blockers.append("no_phase8a_editorial_rows")
    if failures:
        blockers.append("phase8a_editorial_failures_present")
    sport_counts = {sport: sum(clean(row.get("sport_id")) == sport for row in rows) for sport in sorted({clean(row.get("sport_id")) for row in rows if clean(row.get("sport_id"))})}
    status = "passed_phase8a_editorial_quality" if not blockers else "blocked_phase8a_editorial_quality"
    return {"version": VERSION, "editorial_version": EDITORIAL_VERSION, "mode": mode, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": status, "strict_exit_code": 0 if not blockers else 2, "validated_rows": len(rows), "passed_rows": len(rows) - len(failures), "failed_rows": len(failures), "sport_counts": sport_counts, "blockers": sorted(set(blockers)), "warnings": warnings, "rows": rows}


def write_report(report: Mapping[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")
    write_csv(OUT_CSV, report.get("rows") or [])
    lines = ["# HSD Phase 8A Editorial Fit Quality Gate", "", f"Mode: `{report.get('mode')}`", f"Status: `{report.get('status')}`", f"Rows: `{report.get('validated_rows')}`", f"Passed: `{report.get('passed_rows')}`", f"Failed: `{report.get('failed_rows')}`", "", "## Blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.mode)
    write_report(report)
    print(json.dumps({key: report[key] for key in ["version", "mode", "status", "validated_rows", "passed_rows", "failed_rows", "sport_counts", "blockers"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0

if __name__ == "__main__":
    raise SystemExit(main())
