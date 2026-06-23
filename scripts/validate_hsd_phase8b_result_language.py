from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hsd_phase8b_result_language import clean, generate_result_editorial, validate_result_editorial, VERSION as ENGINE_VERSION

VERSION = "v1.0-phase8b-result-language-gate"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
REPORT_JSON = Path("phase8b_result_language_report.json")
REPORT_MD = Path("phase8b_result_language_report.md")


def read_manifest() -> List[Dict[str, Any]]:
    if not MANIFEST.exists():
        return []
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [item for item in payload.get("items") or [] if isinstance(item, dict)]


def validate(mode: str) -> Dict[str, Any]:
    rows = []
    blockers: List[str] = []
    for item in read_manifest():
        if not clean(item.get("template_id")).startswith("hsd_game_recap_final_score"):
            continue
        ed = {k: item.get(k) for k in item.keys() if k.startswith("phase8b_")}
        if not clean(ed.get("phase8b_result_public_copy")):
            ed = generate_result_editorial(item)
        reasons = validate_result_editorial(ed)
        status = "passed_phase8b_result_language" if not reasons else "blocked_phase8b_result_language"
        row = {
            "item_id": clean(item.get("item_id")),
            "headline": clean(item.get("headline")),
            "platform": clean(item.get("platform")),
            "template_id": clean(item.get("template_id")),
            "phase8b_result_language_status": status,
            "phase8b_result_language_reasons": ";".join(reasons),
            "phase8b_result_public_copy": clean(ed.get("phase8b_result_public_copy")),
        }
        rows.append(row)
        blockers.extend(f"{row['item_id']}:{reason}" for reason in reasons)
    if not rows:
        blockers.append("no_final_score_rows_found")
    return {
        "version": VERSION,
        "engine_version": ENGINE_VERSION,
        "mode": mode,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed_phase8b_result_language" if not blockers else "blocked_phase8b_result_language",
        "strict_exit_code": 0 if not blockers else 2,
        "validated_rows": len(rows),
        "passed_rows": sum(r["phase8b_result_language_status"] == "passed_phase8b_result_language" for r in rows),
        "failed_rows": sum(r["phase8b_result_language_status"] != "passed_phase8b_result_language" for r in rows),
        "blockers": sorted(set(blockers)),
        "rows": rows,
    }


def write_report(report: Dict[str, Any]) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 8B Result Language Gate",
        "",
        f"Mode: `{report.get('mode')}`",
        f"Status: `{report.get('status')}`",
        f"Rows: `{report.get('validated_rows')}`",
        f"Passed: `{report.get('passed_rows')}`",
        f"Failed: `{report.get('failed_rows')}`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{b}`" for b in report.get("blockers") or []] or ["- None"]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fixture_audit", "live_data"], default="fixture_audit")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    report = validate(args.mode)
    write_report(report)
    print(json.dumps({k: report[k] for k in ["version", "mode", "status", "validated_rows", "passed_rows", "failed_rows", "blockers"]}, indent=2))
    return int(report.get("strict_exit_code") or 0) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
