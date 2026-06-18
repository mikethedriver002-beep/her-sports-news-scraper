from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "v1.0-production-readiness-gate"
DEFAULT_JSON = "production_readiness_v1.json"
DEFAULT_MD = "production_readiness_v1.md"
DEFAULT_POST_READY_CSV = "post_ready_assets_v1.csv"
DEFAULT_REVIEW_ONLY_CSV = "review_only_assets_v1.csv"
DEFAULT_OPERATOR_BRIEF = "daily_operator_brief_v1.md"

SOURCE_TRUTH = Path("v4_source_truth_guard.json")
RESULTS_MANIFEST = Path("results_desk_v5_manifest.json")
SOURCE_ACCURACY = Path("source_accuracy_v5.json")
MISSING_GAMES = Path("missing_games_alert_v5.json")
QUALITY_MANIFEST = Path("hsd_quality_graphics_manifest.csv")
POST_READY_COPY = Path("outputs/latest/production_graphics_director/copy_director/post_ready_copy.md")
VARIANT_MANIFEST = Path("outputs/latest/production_graphics_director/graphics_variant_packs/variant_manifest.csv")
RENDERER_MANIFEST = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_manifest.json")
LOGO_STATUS = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2/hsd_template_renderer_v2_logo_status.json")

POST_FIELDS = [
    "headline",
    "platform",
    "row_kind",
    "output_path",
    "width",
    "height",
    "readiness_status",
    "manual_visual_review_required",
    "copy_found",
    "notes",
]
REVIEW_FIELDS = [
    "headline",
    "platform",
    "row_kind",
    "output_path",
    "width",
    "height",
    "readiness_status",
    "reasons",
    "notes",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def low(value: Any) -> str:
    return clean(value).lower()


def slug_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", low(value)).strip()


def read_json(repo_root: Path, rel: Path) -> Dict[str, Any]:
    path = repo_root / rel
    if not path.exists() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {"_non_object": data}
    except Exception as exc:
        return {"_json_error": f"{type(exc).__name__}: {exc}"}


def read_csv(repo_root: Path, rel: Path) -> List[Dict[str, str]]:
    path = repo_root / rel
    if not path.exists() or not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return clean(value).lower() in {"1", "true", "yes", "y"}


def count_from(mapping: Dict[str, Any], *keys: str) -> int:
    for key in keys:
        try:
            value = mapping.get(key)
            if value is not None and clean(value) != "":
                return int(float(str(value)))
        except Exception:
            continue
    return 0


def expected_dimensions(platform: str) -> Tuple[int, int]:
    platform_l = low(platform)
    if "stor" in platform_l:
        return 1080, 1920
    return 1080, 1350


def copy_contains_headline(copy_text: str, headline: str) -> bool:
    if not clean(headline):
        return False
    return slug_text(headline) in slug_text(copy_text)


def source_truth_passed(source_truth: Dict[str, Any]) -> bool:
    return clean(source_truth.get("status")) == "passed_source_truth_guard" and not source_truth.get("blockers")


def collect_global_blockers(
    repo_root: Path,
    source_truth: Dict[str, Any],
    source_accuracy: Dict[str, Any],
    quality_rows: List[Dict[str, str]],
    logo_status: Dict[str, Any],
    post_ready_copy_exists: bool,
) -> List[str]:
    blockers: List[str] = []
    if not source_truth:
        blockers.append("source_truth_guard_missing")
    elif not source_truth_passed(source_truth):
        blockers.append("source_truth_guard_not_passed")

    counts = source_accuracy.get("counts") if isinstance(source_accuracy.get("counts"), dict) else {}
    if count_from(counts, "expected_missing", "expected_expected_missing", "missing_expected_games") > 0:
        blockers.append("missing_expected_games_present")
    if count_from(counts, "stale_observations") > 0:
        blockers.append("stale_observations_present")
    if count_from(counts, "duplicate_groups") > 0:
        blockers.append("duplicate_groups_present")

    if not quality_rows:
        blockers.append("quality_graphics_manifest_missing_or_empty")
    if count_from(logo_status, "active_logo_fallbacks") > 0:
        blockers.append("active_logo_fallbacks_present")
    if not post_ready_copy_exists:
        blockers.append("post_ready_copy_missing")

    return sorted(set(blockers))


def classify_quality_row(repo_root: Path, row: Dict[str, str], copy_text: str) -> Dict[str, Any]:
    reasons: List[str] = []
    platform = clean(row.get("platform"))
    width = count_from(row, "width")
    height = count_from(row, "height")
    exp_w, exp_h = expected_dimensions(platform)
    output_path = clean(row.get("output_path"))
    headline = clean(row.get("headline"))
    status = low(row.get("status"))
    if status != "rendered":
        reasons.append("not_rendered")
    if width != exp_w or height != exp_h:
        reasons.append(f"invalid_dimensions_expected_{exp_w}x{exp_h}")
    if not output_path or not (repo_root / output_path).exists():
        reasons.append("output_file_missing")
    if not headline:
        reasons.append("headline_missing")
    if clean(row.get("used_home_logo")).lower() != "yes" or clean(row.get("used_away_logo")).lower() != "yes":
        reasons.append("both_team_logos_not_confirmed")
    copy_found = copy_contains_headline(copy_text, headline)
    if not copy_found:
        reasons.append("post_ready_copy_not_found")
    readiness_status = "post_ready_candidate" if not reasons else "review_only"
    return {
        "headline": headline,
        "platform": platform,
        "row_kind": clean(row.get("row_kind")),
        "output_path": output_path,
        "width": str(width or clean(row.get("width"))),
        "height": str(height or clean(row.get("height"))),
        "readiness_status": readiness_status,
        "manual_visual_review_required": "Yes",
        "copy_found": "Yes" if copy_found else "No",
        "reasons": ";".join(reasons),
        "notes": clean(row.get("notes")) or "HSD production readiness gate v1",
    }


def classify_variant_rows(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    counts = Counter(clean(row.get("status")) or "unknown" for row in rows)
    with_players = [row for row in rows if clean(row.get("variant")) == "with_players"]
    review_required = [
        row for row in rows
        if clean(row.get("status")) != "ready" or "review" in low(row.get("player_mode")) or clean(row.get("variant")) == "with_players"
    ]
    return {
        "variant_rows": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "with_players_rows": len(with_players),
        "review_required_rows": len(review_required),
    }


def build_report(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    source_truth = read_json(repo_root, SOURCE_TRUTH)
    results_manifest = read_json(repo_root, RESULTS_MANIFEST)
    source_accuracy = read_json(repo_root, SOURCE_ACCURACY)
    missing_games = read_json(repo_root, MISSING_GAMES)
    logo_status = read_json(repo_root, LOGO_STATUS)
    renderer_manifest = read_json(repo_root, RENDERER_MANIFEST)
    quality_rows = read_csv(repo_root, QUALITY_MANIFEST)
    variant_rows = read_csv(repo_root, VARIANT_MANIFEST)
    copy_path = repo_root / POST_READY_COPY
    copy_text = copy_path.read_text(encoding="utf-8", errors="replace") if copy_path.exists() else ""
    global_blockers = collect_global_blockers(repo_root, source_truth, source_accuracy, quality_rows, logo_status, bool(copy_text))
    classified = [classify_quality_row(repo_root, row, copy_text) for row in quality_rows]
    post_ready = [row for row in classified if row["readiness_status"] == "post_ready_candidate"]
    review_only = [row for row in classified if row["readiness_status"] != "post_ready_candidate"]
    if quality_rows and not post_ready:
        global_blockers.append("no_post_ready_candidates_after_quality_gate")
    counts = source_accuracy.get("counts") if isinstance(source_accuracy.get("counts"), dict) else {}
    variant_summary = classify_variant_rows(variant_rows)
    warnings: List[str] = []
    if truthy(renderer_manifest.get("review_only")):
        warnings.append("template_renderer_outputs_remain_review_only")
    if review_only:
        warnings.append("some_quality_graphics_require_review")
    if variant_summary.get("review_required_rows"):
        warnings.append("variant_packs_include_review_required_items")
    status = "blocked" if global_blockers else "production_review_ready"
    publish_gate = "blocked_manual_review_required" if global_blockers else "human_visual_review_required_before_post"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": repo_root.as_posix(),
        "status": status,
        "publish_gate": publish_gate,
        "strict_exit_code": 2 if global_blockers else 0,
        "blockers": sorted(set(global_blockers)),
        "warnings": sorted(set(warnings)),
        "policy": {
            "free_only": True,
            "artifact_only": True,
            "auto_publish": False,
            "manual_visual_review_required": True,
            "no_player_images_required_for_post_ready": True,
            "post_ready_definition": "source-truth passed, rendered file exists, platform dimensions match, both team logos confirmed, and copy is present",
        },
        "source_truth": {
            "status": source_truth.get("status"),
            "blockers": source_truth.get("blockers", []),
            "warnings": source_truth.get("warnings", []),
        },
        "source_accuracy_counts": counts,
        "results_manifest_counts": results_manifest.get("counts", {}),
        "missing_games_summary": missing_games.get("summary", {}),
        "logo_status": {
            "effective_publish_status": logo_status.get("effective_publish_status"),
            "active_logo_fallbacks": count_from(logo_status, "active_logo_fallbacks"),
            "recoverable_logo_warnings": count_from(logo_status, "recoverable_logo_warnings"),
            "rendered_count": count_from(logo_status, "rendered_count"),
        },
        "renderer": {
            "version": renderer_manifest.get("version"),
            "review_only": truthy(renderer_manifest.get("review_only")),
            "rendered_count": count_from(renderer_manifest, "rendered_count"),
            "fallback_logo_warnings": count_from(renderer_manifest, "fallback_logo_warnings"),
        },
        "quality_graphics": {
            "rows": len(quality_rows),
            "post_ready_candidates": len(post_ready),
            "review_only": len(review_only),
        },
        "variant_packs": variant_summary,
        "post_ready_assets": post_ready,
        "review_only_assets": review_only,
    }


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# HSD Production Readiness Gate v1",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Version: `{report.get('version')}`",
        f"Status: `{report.get('status')}`",
        f"Publish gate: `{report.get('publish_gate')}`",
        "",
        "## Verdict",
        "",
    ]
    if report.get("blockers"):
        lines.append("Production readiness blockers are present. Do not treat any asset as post-ready.")
    else:
        lines.append("Production readiness gate passed for post-ready candidates. Human visual review is still required before posting.")
    lines += ["", "## Counts", ""]
    q = report.get("quality_graphics", {})
    lines.append(f"- Quality graphics rows: `{q.get('rows')}`")
    lines.append(f"- Post-ready candidates: `{q.get('post_ready_candidates')}`")
    lines.append(f"- Review-only assets: `{q.get('review_only')}`")
    lines += ["", "## Blockers", ""]
    lines += [f"- `{b}`" for b in report.get("blockers", [])] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{w}`" for w in report.get("warnings", [])] or ["- None"]
    lines += ["", "## Post-ready candidates", ""]
    for row in report.get("post_ready_assets", [])[:25]:
        lines.append(f"- `{row.get('platform')}` | {row.get('headline')} | `{row.get('output_path')}`")
    if not report.get("post_ready_assets"):
        lines.append("- None")
    lines += ["", "## Review-only assets", ""]
    for row in report.get("review_only_assets", [])[:40]:
        lines.append(f"- `{row.get('platform')}` | {row.get('headline')} | `{row.get('reasons')}`")
    if not report.get("review_only_assets"):
        lines.append("- None")
    lines += ["", "## Policy", ""]
    lines.append("- This gate does not auto-publish.")
    lines.append("- Post-ready means ready for final human visual review, not automatically approved for posting.")
    lines.append("- Player-image variants remain review-only unless separately approved.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_operator_brief(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# HSD Daily Operator Brief",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Production readiness: `{report.get('status')}`",
        f"Publish gate: `{report.get('publish_gate')}`",
        "",
        "## What to do",
        "",
    ]
    if report.get("blockers"):
        lines.append("Do not post from this run. Resolve blockers first.")
    elif report.get("post_ready_assets"):
        lines.append("Use the post-ready candidates below for final human visual review. Do not use review-only assets as public posts.")
    else:
        lines.append("No post-ready candidates were produced. Review-only assets may be useful for diagnosis.")
    lines += ["", "## Post-ready candidate queue", ""]
    for idx, row in enumerate(report.get("post_ready_assets", [])[:20], 1):
        lines.append(f"{idx}. **{row.get('headline')}**")
        lines.append(f"   - Platform: `{row.get('platform')}`")
        lines.append(f"   - File: `{row.get('output_path')}`")
        lines.append("   - Final check: visual QA, caption copy, and platform fit.")
        lines.append("")
    if not report.get("post_ready_assets"):
        lines.append("- None")
    lines += ["", "## Keep review-only", ""]
    reasons = Counter()
    for row in report.get("review_only_assets", []):
        for reason in clean(row.get("reasons")).split(";"):
            if reason:
                reasons[reason] += 1
    for reason, count in reasons.most_common():
        lines.append(f"- `{reason}`: `{count}`")
    if not reasons:
        lines.append("- None")
    lines += ["", "## Source and logo status", ""]
    lines.append(f"- Source truth: `{(report.get('source_truth') or {}).get('status')}`")
    lines.append(f"- Active logo fallbacks: `{(report.get('logo_status') or {}).get('active_logo_fallbacks')}`")
    lines.append(f"- Renderer review-only: `{(report.get('renderer') or {}).get('review_only')}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build HSD production readiness gate report.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--json", default=DEFAULT_JSON)
    parser.add_argument("--md", default=DEFAULT_MD)
    parser.add_argument("--post-ready-csv", default=DEFAULT_POST_READY_CSV)
    parser.add_argument("--review-only-csv", default=DEFAULT_REVIEW_ONLY_CSV)
    parser.add_argument("--operator-brief", default=DEFAULT_OPERATOR_BRIEF)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when production readiness blockers exist.")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    report = build_report(root)

    out_json = root / args.json if not Path(args.json).is_absolute() else Path(args.json)
    out_md = root / args.md if not Path(args.md).is_absolute() else Path(args.md)
    out_post = root / args.post_ready_csv if not Path(args.post_ready_csv).is_absolute() else Path(args.post_ready_csv)
    out_review = root / args.review_only_csv if not Path(args.review_only_csv).is_absolute() else Path(args.review_only_csv)
    out_brief = root / args.operator_brief if not Path(args.operator_brief).is_absolute() else Path(args.operator_brief)

    out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, out_md)
    write_csv(out_post, report.get("post_ready_assets", []), POST_FIELDS)
    write_csv(out_review, report.get("review_only_assets", []), REVIEW_FIELDS)
    write_operator_brief(report, out_brief)

    print(json.dumps({
        "version": VERSION,
        "status": report.get("status"),
        "publish_gate": report.get("publish_gate"),
        "blockers": report.get("blockers"),
        "post_ready_candidates": report.get("quality_graphics", {}).get("post_ready_candidates"),
        "review_only": report.get("quality_graphics", {}).get("review_only"),
        "json": out_json.as_posix(),
        "operator_brief": out_brief.as_posix(),
    }, indent=2))

    if args.strict and report.get("blockers"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
