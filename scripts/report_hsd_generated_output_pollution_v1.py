from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VERSION = "v1.0-generated-output-pollution-audit"
DEFAULT_OUTPUT_JSON = "generated_output_pollution_v1.json"
DEFAULT_OUTPUT_MD = "generated_output_pollution_v1.md"

SAFE_DELETE_DIR_PREFIXES = {
    "outputs/latest/": "generated_output_dir",
    "dashboard/": "legacy_dashboard_dir",
    "results_dashboard/": "legacy_results_dashboard_dir",
    "run_history/": "legacy_news_run_archive",
    "results_run_history/": "legacy_results_run_archive",
    "launch_run_history/": "legacy_launch_run_archive",
    "generated_graphics/": "generated_graphics_dir",
    "graphics_chat_upload_pack/": "generated_upload_pack",
    "graphics_chat_upload_pack_zips/": "generated_upload_pack",
    "graphics_clean_prompts/": "generated_prompt_dir",
    "manual_workflow_packets/": "generated_manual_workflow_dir",
    "manual_workflow_handoff_packs/": "generated_manual_workflow_dir",
    "ig_story_results_upload_pack/": "generated_story_upload_pack",
    "ig_story_results_upload_pack_zips/": "generated_story_upload_pack",
    "mermaid_compiled_packets/": "generated_mermaid_packets",
}

SAFE_DELETE_EXACT = {
    "hsd_pipeline_lite_review.zip": "run_artifact_zip",
    "hsd_quality_graphics.zip": "run_artifact_zip",
    "hsd_quality_graphics_manifest.csv": "run_artifact_manifest",
    "hsd_quality_graphics_report.md": "run_artifact_report",
    "hsd_quality_graphics_zip_manifest.json": "run_artifact_manifest",
    "repo_state_v3.json": "run_diagnostic_report",
    "repo_state_v3.md": "run_diagnostic_report",
    "v4_source_truth_guard.json": "run_diagnostic_report",
    "v4_source_truth_guard.md": "run_diagnostic_report",
    "generated_output_pollution_v1.json": "run_diagnostic_report",
    "generated_output_pollution_v1.md": "run_diagnostic_report",
    "expected_games_v5_manifest.json": "run_diagnostic_report",
    "expected_games_v5_report.md": "run_diagnostic_report",
    "independent_schedule_verification_v5.csv": "run_diagnostic_report",
    "independent_schedule_verification_v5.json": "run_diagnostic_report",
    "independent_schedule_verification_v5.md": "run_diagnostic_report",
    "multisport_results_observations_v5.csv": "run_diagnostic_report",
    "multisport_results_modules_v5.json": "run_diagnostic_report",
    "multisport_results_modules_v5.md": "run_diagnostic_report",
    "results_desk_v5_manifest.json": "run_diagnostic_report",
    "results_desk_v5_report.md": "run_diagnostic_report",
    "source_accuracy_v5.json": "run_diagnostic_report",
    "source_accuracy_v5.md": "run_diagnostic_report",
    "duplicate_game_audit_v5.csv": "run_diagnostic_report",
    "stale_source_audit_v5.csv": "run_diagnostic_report",
    "missing_games_alert_v5.csv": "run_diagnostic_report",
    "missing_games_alert_v5.json": "run_diagnostic_report",
    "missing_games_alert_v5.md": "run_diagnostic_report",
    "source_observations.csv": "run_data_extract",
    "reconciled_events.csv": "run_data_extract",
    "today_womens_results.csv": "run_data_extract",
    "today_final_results.csv": "run_data_extract",
    "results_contract_v2.csv": "run_data_extract",
    "results_contract_v2.jsonl": "run_data_extract",
    "results_contract_report.md": "run_data_extract",
    "today_results_board.csv": "legacy_results_output",
    "today_box_scores.csv": "legacy_results_output",
    "top_performers.csv": "legacy_results_output",
    "results_dashboard_seed.csv": "legacy_results_output",
    "results_graphics_queue.md": "legacy_results_output",
    "results_system_hub.md": "legacy_results_output",
    "latest_results_run_summary.md": "legacy_results_output",
    "womens_sports_articles.csv": "legacy_news_output",
    "daily_content_brief.csv": "legacy_news_output",
    "story_context_enriched.csv": "legacy_news_output",
    "daily_content_command_center.csv": "legacy_news_output",
    "tonight_in_the_w_package.csv": "legacy_news_output",
    "must_post_carousels.csv": "legacy_news_output",
    "story_poll_package.csv": "legacy_news_output",
    "caption_bank_v2.csv": "legacy_news_output",
    "reel_script_package.md": "legacy_news_output",
    "graphics_copy_package.md": "legacy_news_output",
    "hsd_daily_content_hub.md": "legacy_news_output",
    "hsd_publish_system_hub.md": "legacy_news_output",
    "hsd_graphics_system_hub.md": "legacy_news_output",
    "tonight_in_the_w_graphic_templates.csv": "legacy_news_output",
    "tonight_in_the_w_visual_specs.csv": "legacy_news_output",
    "post_template_mapper.csv": "legacy_news_output",
    "master_posting_dashboard.csv": "legacy_news_output",
    "ready_to_post_graphic_copy.csv": "legacy_news_output",
    "graphic_copy_rules.csv": "legacy_news_output",
    "daily_command_file.csv": "legacy_news_output",
    "image_generation_prompts.csv": "legacy_news_output",
    "today_graphics_queue.csv": "legacy_news_output",
    "today_graphics_queue.md": "legacy_news_output",
    "top_3_graphic_packets.md": "legacy_news_output",
    "latest_run_summary.md": "legacy_news_output",
}

REVIEW_REQUIRED_EXACT = {
    "config/hsd_expected_games_v5.csv": "generated_config_review_required",
}

CACHE_PATTERNS = ["*/__pycache__/*", "__pycache__/*", "*.pyc"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_git_ls_files(repo_root: Path) -> List[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(repo_root),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            return []
        return [p for p in proc.stdout.decode("utf-8", errors="replace").split("\0") if p]
    except Exception:
        return []


def classify_path(path: str) -> Dict[str, Any]:
    norm = path.replace("\\", "/").lstrip("./")
    if norm in REVIEW_REQUIRED_EXACT:
        return {
            "path": norm,
            "classification": "generated_review_required",
            "category": REVIEW_REQUIRED_EXACT[norm],
            "safe_delete_candidate": False,
            "reason": "Generated-like config file; keep until Phase 3 replaces expected-games source truth.",
        }
    if norm in SAFE_DELETE_EXACT:
        return {
            "path": norm,
            "classification": "tracked_generated_output",
            "category": SAFE_DELETE_EXACT[norm],
            "safe_delete_candidate": True,
            "reason": "Run output should be produced as an artifact, not committed to main.",
        }
    for prefix, category in SAFE_DELETE_DIR_PREFIXES.items():
        if norm.startswith(prefix):
            return {
                "path": norm,
                "classification": "tracked_generated_output",
                "category": category,
                "safe_delete_candidate": True,
                "reason": "Generated output directory should be artifact-only, not committed to main.",
            }
    for pattern in CACHE_PATTERNS:
        if fnmatch.fnmatch(norm, pattern):
            return {
                "path": norm,
                "classification": "runtime_cache",
                "category": "python_cache",
                "safe_delete_candidate": True,
                "reason": "Runtime cache should never be tracked.",
            }
    return {
        "path": norm,
        "classification": "source_or_reviewed_repo_file",
        "category": "not_generated_by_phase2c_rules",
        "safe_delete_candidate": False,
        "reason": "No Phase 2C generated-output rule matched this path.",
    }


def build_report_from_paths(paths: Iterable[str], repo_root: Path | None = None) -> Dict[str, Any]:
    rows = [classify_path(path) for path in sorted(set(paths))]
    generated_rows = [row for row in rows if row["classification"] in {"tracked_generated_output", "runtime_cache"}]
    review_rows = [row for row in rows if row["classification"] == "generated_review_required"]
    category_counts = Counter(row["category"] for row in generated_rows)
    delete_commands = [f"git rm -r -- {json.dumps(row['path'])}" for row in generated_rows[:250]]
    by_category: Dict[str, List[str]] = defaultdict(list)
    for row in generated_rows:
        by_category[row["category"]].append(row["path"])
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": repo_root.as_posix() if repo_root else "",
        "policy": {
            "artifact_only_outputs": True,
            "does_not_delete_files": True,
            "free_only": True,
            "network_used": False,
        },
        "tracked_file_count": len(rows),
        "tracked_generated_output_count": len(generated_rows),
        "review_required_generated_like_count": len(review_rows),
        "category_counts": dict(sorted(category_counts.items())),
        "safe_delete_candidates": generated_rows,
        "review_required_candidates": review_rows,
        "delete_plan_preview_limit": 250,
        "delete_plan_preview_commands": delete_commands,
        "generated_paths_by_category": {key: sorted(value) for key, value in sorted(by_category.items())},
        "status": "generated_output_cleanup_needed" if generated_rows else "clean_no_tracked_generated_outputs",
        "human_summary": (
            f"{len(generated_rows)} tracked generated/cache files matched Phase 2C cleanup rules. Review the delete plan before removing files."
            if generated_rows else "No tracked generated-output files matched Phase 2C cleanup rules."
        ),
    }


def build_report(repo_root: Path) -> Dict[str, Any]:
    paths = run_git_ls_files(repo_root)
    return build_report_from_paths(paths, repo_root=repo_root)


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# HSD Generated Output Pollution Audit v1",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Version: `{report.get('version')}`",
        f"Status: `{report.get('status')}`",
        "",
        "## Summary",
        "",
        f"- Tracked files scanned: `{report.get('tracked_file_count')}`",
        f"- Tracked generated-output candidates: `{report.get('tracked_generated_output_count')}`",
        f"- Review-required generated-like candidates: `{report.get('review_required_generated_like_count')}`",
        "",
        "## Category counts",
        "",
    ]
    counts = report.get("category_counts") or {}
    if counts:
        for category, count in counts.items():
            lines.append(f"- `{category}`: `{count}`")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Review-required candidates",
        "",
    ]
    review_rows = report.get("review_required_candidates") or []
    if review_rows:
        for row in review_rows:
            lines.append(f"- `{row.get('path')}` — {row.get('reason')}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Delete plan preview",
        "",
        "This script does not delete files. Review these commands before using them in a cleanup PR.",
        "",
        "```bash",
    ]
    for command in report.get("delete_plan_preview_commands") or []:
        lines.append(command)
    if not report.get("delete_plan_preview_commands"):
        lines.append("# No generated-output delete commands produced.")
    lines += ["```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit tracked generated output pollution in the HSD repo.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--json", default=DEFAULT_OUTPUT_JSON, help="Output JSON path.")
    parser.add_argument("--md", default=DEFAULT_OUTPUT_MD, help="Output Markdown path.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when tracked generated output is found.")
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    report = build_report(root)
    json_path = Path(args.json)
    md_path = Path(args.md)
    if not json_path.is_absolute():
        json_path = root / json_path
    if not md_path.is_absolute():
        md_path = root / md_path
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)

    print(json.dumps({
        "version": VERSION,
        "status": report.get("status"),
        "tracked_generated_output_count": report.get("tracked_generated_output_count"),
        "review_required_generated_like_count": report.get("review_required_generated_like_count"),
        "json": json_path.as_posix(),
        "md": md_path.as_posix(),
    }, indent=2))

    if args.strict and report.get("tracked_generated_output_count"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
