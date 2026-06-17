from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v4.0-source-truth-guard"
DEFAULT_OUTPUT_JSON = "v4_source_truth_guard.json"
DEFAULT_OUTPUT_MD = "v4_source_truth_guard.md"

EXPECTED_MANIFEST = "expected_games_v5_manifest.json"
MISSING_ALERT = "missing_games_alert_v5.json"
INDEPENDENT_VERIFICATION = "independent_schedule_verification_v5.json"
SOURCE_ACCURACY = "source_accuracy_v5.json"
RESULTS_MANIFEST = "results_desk_v5_manifest.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {"_non_object": data}
    except Exception as exc:
        return {"_json_error": f"{type(exc).__name__}: {exc}"}


def is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return clean(value).lower() in {"1", "true", "yes", "y"}


def is_observation_derived_expected_manifest(manifest: Dict[str, Any]) -> bool:
    version = clean(manifest.get("version")).lower()
    input_file = clean(manifest.get("input_file")).lower()
    return "from-observations" in version or input_file == "source_observations.csv"


def count_from(mapping: Dict[str, Any], *keys: str) -> int:
    for key in keys:
        try:
            value = mapping.get(key)
            if value is not None and clean(value) != "":
                return int(float(str(value)))
        except Exception:
            continue
    return 0


def build_report(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()

    expected_manifest = read_json(repo_root / EXPECTED_MANIFEST)
    missing_alert = read_json(repo_root / MISSING_ALERT)
    independent = read_json(repo_root / INDEPENDENT_VERIFICATION)
    source_accuracy = read_json(repo_root / SOURCE_ACCURACY)
    results_manifest = read_json(repo_root / RESULTS_MANIFEST)

    expected_summary = missing_alert.get("summary") if isinstance(missing_alert.get("summary"), dict) else {}
    source_counts = source_accuracy.get("counts") if isinstance(source_accuracy.get("counts"), dict) else {}
    result_counts = results_manifest.get("counts") if isinstance(results_manifest.get("counts"), dict) else {}

    blockers: List[str] = []
    warnings: List[str] = []
    notes: List[str] = []

    expected_manifest_exists = bool(expected_manifest)
    missing_alert_exists = bool(missing_alert)
    independent_exists = bool(independent)

    expected_is_observation_derived = is_observation_derived_expected_manifest(expected_manifest)
    expected_games = count_from(expected_summary, "expected_games") or count_from(expected_manifest, "expected_games") or count_from(result_counts, "expected_games")
    missing_games = count_from(expected_summary, "missing") or count_from(result_counts, "missing_expected_games")
    matched_games = count_from(expected_summary, "matched")

    independent_games = count_from(independent, "independent_games")
    independent_matched = count_from(independent, "matched")
    independent_missing = count_from(independent, "missing_from_independent")
    independent_unavailable = count_from(independent, "independent_source_unavailable")
    independent_extra = count_from(independent, "extra_in_independent")
    independent_source_available = is_truthy(independent.get("source_available"))
    verification_inconclusive = is_truthy(independent.get("verification_inconclusive"))

    if not expected_manifest_exists:
        blockers.append("expected_games_manifest_missing")
    if not missing_alert_exists:
        blockers.append("missing_games_alert_missing")
    if not independent_exists:
        blockers.append("independent_schedule_verification_missing")

    if expected_is_observation_derived:
        blockers.append("expected_games_baseline_is_observation_derived")
        warnings.append("missing_games_zero_is_internal_consistency_only")
        warnings.append("source_accuracy_expected_counts_are_not_independent_slate_verification")

    if verification_inconclusive or not independent_source_available:
        blockers.append("independent_schedule_verification_inconclusive")

    if expected_games and independent_source_available and independent_matched < expected_games:
        blockers.append("independent_schedule_match_count_below_expected")

    if independent_missing:
        blockers.append("games_missing_from_independent_schedule_source")

    if independent_extra:
        warnings.append("independent_schedule_has_extra_games_review_required")

    if not expected_is_observation_derived and expected_manifest_exists:
        notes.append("expected-games manifest is not labeled as observation-derived")
    if missing_games == 0 and expected_is_observation_derived:
        notes.append("missing_games_alert matched every expected row, but the expected rows came from observed data")

    internal_completeness_status = (
        "internal_consistency_only"
        if expected_is_observation_derived
        else "external_expected_fixture_or_manual_review"
    )
    independent_slate_status = (
        "verified"
        if independent_source_available and not verification_inconclusive and expected_games and independent_matched >= expected_games and independent_missing == 0
        else "inconclusive"
        if verification_inconclusive or not independent_source_available
        else "mismatch_review_required"
    )

    status = "blocked_source_truth" if blockers else "passed_source_truth_guard"

    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": repo_root.as_posix(),
        "status": status,
        "review_only": True,
        "free_only": True,
        "policy": {
            "no_paid_apis": True,
            "no_paid_data_feeds": True,
            "no_paid_scraping_services": True,
            "no_paid_proxies": True,
            "no_paid_llm_dependencies": True,
            "network_used_by_guard": False,
        },
        "files": {
            "expected_manifest": EXPECTED_MANIFEST,
            "missing_alert": MISSING_ALERT,
            "independent_verification": INDEPENDENT_VERIFICATION,
            "source_accuracy": SOURCE_ACCURACY,
            "results_manifest": RESULTS_MANIFEST,
        },
        "expected_games": {
            "manifest_exists": expected_manifest_exists,
            "manifest_version": expected_manifest.get("version"),
            "input_file": expected_manifest.get("input_file"),
            "observation_derived": expected_is_observation_derived,
            "expected_games": expected_games,
            "matched": matched_games,
            "missing": missing_games,
            "internal_completeness_status": internal_completeness_status,
        },
        "independent_schedule": {
            "report_exists": independent_exists,
            "version": independent.get("version"),
            "source_available": independent_source_available,
            "verification_inconclusive": verification_inconclusive,
            "expected_games": count_from(independent, "expected_games"),
            "independent_games": independent_games,
            "matched": independent_matched,
            "missing_from_independent": independent_missing,
            "independent_source_unavailable": independent_unavailable,
            "extra_in_independent": independent_extra,
            "independent_slate_status": independent_slate_status,
        },
        "source_accuracy_counts": source_counts,
        "results_manifest_counts": result_counts,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "notes": notes,
        "publish_gate": "blocked_manual_review_required" if blockers else "artifact_review_allowed",
        "strict_exit_code": 2 if blockers else 0,
        "human_summary": (
            "Do not treat missing_games_alert_v5 as independent slate verification."
            if blockers
            else "Source-truth guard passed."
        ),
    }


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    expected = report.get("expected_games", {})
    independent = report.get("independent_schedule", {})
    lines: List[str] = []
    lines.append("# HSD V4 Source Truth Guard")
    lines.append("")
    lines.append(f"Generated: `{report.get('generated_at_utc')}`")
    lines.append(f"Version: `{report.get('version')}`")
    lines.append(f"Status: `{report.get('status')}`")
    lines.append(f"Publish gate: `{report.get('publish_gate')}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    if report.get("blockers"):
        lines.append("Source-truth blockers are present. Do not treat the run as independently slate-verified.")
    else:
        lines.append("No source-truth blockers detected by this guard.")
    lines.append("")
    lines.append("## Expected-games baseline")
    lines.append("")
    lines.append(f"- Manifest version: `{expected.get('manifest_version')}`")
    lines.append(f"- Input file: `{expected.get('input_file')}`")
    lines.append(f"- Observation-derived: `{expected.get('observation_derived')}`")
    lines.append(f"- Expected games: `{expected.get('expected_games')}`")
    lines.append(f"- Matched: `{expected.get('matched')}`")
    lines.append(f"- Missing: `{expected.get('missing')}`")
    lines.append(f"- Internal completeness status: `{expected.get('internal_completeness_status')}`")
    lines.append("")
    lines.append("## Independent schedule verification")
    lines.append("")
    lines.append(f"- Report exists: `{independent.get('report_exists')}`")
    lines.append(f"- Source available: `{independent.get('source_available')}`")
    lines.append(f"- Verification inconclusive: `{independent.get('verification_inconclusive')}`")
    lines.append(f"- Independent games: `{independent.get('independent_games')}`")
    lines.append(f"- Matched: `{independent.get('matched')}`")
    lines.append(f"- Missing from independent: `{independent.get('missing_from_independent')}`")
    lines.append(f"- Independent source unavailable: `{independent.get('independent_source_unavailable')}`")
    lines.append(f"- Extra in independent: `{independent.get('extra_in_independent')}`")
    lines.append(f"- Independent slate status: `{independent.get('independent_slate_status')}`")
    lines.append("")
    lines.append("## Blockers")
    lines.append("")
    for blocker in report.get("blockers") or []:
        lines.append(f"- `{blocker}`")
    if not report.get("blockers"):
        lines.append("- None")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    for warning in report.get("warnings") or []:
        lines.append(f"- `{warning}`")
    if not report.get("warnings"):
        lines.append("- None")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in report.get("notes") or []:
        lines.append(f"- {note}")
    if not report.get("notes"):
        lines.append("- None")
    lines.append("")
    lines.append("## Policy")
    lines.append("")
    lines.append("- Free-only guard: no paid APIs, no paid data feeds, no paid scraping services, no paid proxies, no paid LLM dependencies.")
    lines.append("- This guard does not use the network.")
    lines.append("- This guard is diagnostic. It does not rewrite scraper outputs.")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build HSD V4 source-truth guard report.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--json", default=DEFAULT_OUTPUT_JSON, help="Output JSON path, relative to repo root unless absolute.")
    parser.add_argument("--md", default=DEFAULT_OUTPUT_MD, help="Output Markdown path, relative to repo root unless absolute.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when source-truth blockers are present.")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    report = build_report(root)

    json_path = Path(args.json)
    if not json_path.is_absolute():
        json_path = root / json_path
    md_path = Path(args.md)
    if not md_path.is_absolute():
        md_path = root / md_path

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)

    print(json.dumps({
        "version": VERSION,
        "status": report.get("status"),
        "publish_gate": report.get("publish_gate"),
        "blockers": report.get("blockers"),
        "warnings": report.get("warnings"),
        "json": json_path.as_posix(),
        "md": md_path.as_posix(),
    }, indent=2))

    if args.strict and report.get("blockers"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
