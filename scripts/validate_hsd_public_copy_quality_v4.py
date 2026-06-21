from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hsd_phase6l_editorial_language import PUBLIC_COPY_PASS, VERSION as LANGUAGE_VERSION
from hsd_phase6l_editorial_language import clean, validate_public_copy_fields

VERSION = "v1.0-phase6l-public-copy-quality-gate"
MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/hsd_template_renderer_v4_manifest.json")
POLICY = Path("config/graphics/v4/live_post_ready/live_post_ready_policy_phase6l_v4.json")
OUT_JSON = Path("public_copy_quality_v4_report.json")
OUT_MD = Path("public_copy_quality_v4_report.md")
OUT_CSV = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/public_copy_quality/public_copy_quality_v4_rows.csv")
CONTACT_NOTE = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4/public_copy_quality/README_PUBLIC_COPY_QUALITY.md")
FINAL_TEMPLATES = {
    "hsd_game_recap_final_score_a",
    "hsd_game_recap_final_score_b",
    "hsd_game_recap_final_score_c_story",
}
FIELDS = [
    "item_id", "template_id", "platform", "headline", "output_path",
    "editorial_headline", "editorial_body", "editorial_scoreline", "editorial_cta_prompt",
    "public_copy_quality_status", "public_copy_quality_score", "public_copy_banned_count",
    "public_copy_banned_tokens", "validation_status", "validation_reasons",
]


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_row(item: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    extra_patterns = policy.get("phase6l_public_copy_forbidden_patterns") or []
    computed = validate_public_copy_fields(item, extra_patterns=extra_patterns)
    status = clean(item.get("public_copy_quality_status")) or computed["public_copy_quality_status"]
    banned_count = int(item.get("public_copy_banned_count") or computed["public_copy_banned_count"] or 0)
    if status != PUBLIC_COPY_PASS:
        reasons.append("public_copy_quality_not_passed")
    if banned_count > 0:
        reasons.append("public_copy_contains_banned_phrase")
    for key in ["editorial_headline", "editorial_body", "editorial_cta_prompt"]:
        if not clean(item.get(key)):
            reasons.append(f"missing_{key}")
    if "survived the finish" in clean(item.get("public_copy")).lower():
        reasons.append("forbidden_survived_the_finish")
    return {
        **item,
        **computed,
        "validation_status": "passed_public_copy_validation" if not reasons else "blocked_public_copy_validation",
        "validation_reasons": ";".join(sorted(set(reasons))),
    }


def evaluate(root: Path) -> Dict[str, Any]:
    manifest = read_json(root / MANIFEST)
    policy = read_json(root / POLICY)
    rows = [
        validate_row(dict(item), policy)
        for item in manifest.get("items") or []
        if clean(item.get("template_id")) in FINAL_TEMPLATES
    ]
    blockers: List[str] = []
    if not manifest:
        blockers.append("renderer_manifest_missing")
    if manifest.get("version") != "v4.7-phase6l-editorial-language-polish":
        blockers.append("renderer_not_phase6l")
    if not rows:
        blockers.append("no_final_score_rows")
    failed = [row for row in rows if row.get("validation_status") != "passed_public_copy_validation"]
    if failed:
        blockers.append("public_copy_quality_failures_present")
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed_public_copy_quality" if not blockers else "blocked_public_copy_quality",
        "strict_exit_code": 0 if not blockers else 2,
        "language_version": LANGUAGE_VERSION,
        "rows": rows,
        "final_score_rows": len(rows),
        "failed_rows": len(failed),
        "blockers": sorted(set(blockers)),
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
    }


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / OUT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(root / OUT_CSV, report["rows"], FIELDS)
    lines = [
        "# HSD Phase 6L Public Copy Quality Gate",
        "",
        f"Status: `{report['status']}`",
        f"Final-score rows: `{report['final_score_rows']}`",
        f"Failed rows: `{report['failed_rows']}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report["blockers"]] or ["- None"]
    lines += ["", "## Policy", "", "Public copy must sound like HSD, not a score-safe fallback renderer.", ""]
    (root / OUT_MD).write_text("\n".join(lines), encoding="utf-8")
    (root / CONTACT_NOTE).parent.mkdir(parents=True, exist_ok=True)
    (root / CONTACT_NOTE).write_text("Open public_copy_quality_v4_rows.csv to review Phase 6L language decisions.\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = evaluate(root)
    write_report(root, report)
    print(json.dumps({key: report[key] for key in ["version", "status", "final_score_rows", "failed_rows", "blockers"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
