from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VERSION = "v1.2-generated-output-pollution-audit-final-archive-hygiene"
DEFAULT_OUTPUT_JSON = "generated_output_pollution_v1.json"
DEFAULT_OUTPUT_MD = "generated_output_pollution_v1.md"

SAFE_DELETE_DIR_PREFIXES = {
    "hsd_pipeline_lite_review/": "pipeline_lite_review_artifact_dir",
    "outputs/latest/": "generated_output_dir",
    "dashboard/": "legacy_dashboard_dir",
    "results_dashboard/": "legacy_results_dashboard_dir",
    "run_history/": "legacy_news_run_archive",
    "results_run_history/": "legacy_results_run_archive",
    "launch_run_history/": "legacy_launch_run_archive",
    "asset_run_history/": "legacy_asset_run_archive",
    "generated_graphics/": "generated_graphics_dir",
    "graphics_chat_upload_pack/": "generated_upload_pack",
    "graphics_chat_upload_pack_zips/": "generated_upload_pack",
    "graphics_clean_prompts/": "generated_prompt_dir",
    "manual_workflow_packets/": "generated_manual_workflow_dir",
    "manual_workflow_handoff_packs/": "generated_manual_workflow_dir",
    "ig_story_results_upload_pack/": "generated_story_upload_pack",
    "ig_story_results_upload_pack_zips/": "generated_story_upload_pack",
    "mermaid_compiled_packets/": "generated_mermaid_packets",
    "assignment_handoff_packets/": "generated_assignment_packets",
    "assignment_handoff_zips/": "generated_assignment_packets",
    "mermaid_assignment_compiled_packets/": "generated_mermaid_assignment_packets",
    "mermaid_assignment_final_packets/": "generated_mermaid_assignment_packets",
    "mermaid_director_compiled_packets/": "generated_mermaid_director_packets",
    "mermaid_quality_compiled_packets/": "generated_mermaid_quality_packets",
    "mermaid_quality_compiled_packets_v2_2/": "generated_mermaid_quality_packets",
    "rendered_handoff_graphics/": "generated_rendered_handoff",
    "rendered_handoff_zips/": "generated_rendered_handoff",
    "runs/": "generated_run_archive",
    "operator/inbox/": "generated_operator_inbox",
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
    "dirty_tree_v1.json": "run_diagnostic_report",
    "dirty_tree_v1.md": "run_diagnostic_report",
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
    "run_manifest.json": "run_data_extract",
    "source_health_report.csv": "run_data_extract",
    "top_womens_results.csv": "run_data_extract",
    "wnba_box_score_audit.csv": "run_data_extract",
    "wnba_box_score_summary.md": "run_data_extract",
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
    "approved_graphics_assets.csv": "generated_asset_review_output",
    "approved_graphics_assets.json": "generated_asset_review_output",
    "asset_candidates_review.md": "generated_asset_review_output",
    "caption_bank.md": "generated_copy_queue",
    "daily_results_recommendations.md": "generated_results_recommendations",
    "first_comment_hooks.md": "generated_copy_queue",
    "latest_news_sync_run_summary.md": "generated_news_sync_output",
    "news_fact_packets.csv": "generated_news_sync_output",
    "operator_status.md": "generated_operator_status",
    "pipeline_stop_reason.md": "generated_operator_status",
    "player_assets.csv": "generated_player_asset_output",
    "player_assets.json": "generated_player_asset_output",
    "player_image_candidates.csv": "generated_player_asset_output",
    "player_image_fit_gate.csv": "generated_player_asset_output",
    "player_image_fit_report.md": "generated_player_asset_output",
    "player_image_requirements.csv": "generated_player_asset_output",
    "player_image_sourcing_report.md": "generated_player_asset_output",
    "post_slot_status.csv": "generated_queue_output",
    "publish_guard_report.md": "generated_publish_guard",
    "rendered_slide_qa.csv": "generated_render_qa",
    "rendered_slide_qa_manifest.json": "generated_render_qa",
    "rendered_slide_qa_report.md": "generated_render_qa",
    "studio_bundle_packets.md": "generated_studio_output",
    "studio_bundle_prompts.md": "generated_studio_output",
    "studio_bundle_queue.csv": "generated_studio_output",
    "studio_fresh_packet_report.md": "generated_studio_output",
    "studio_freshness_gate.csv": "generated_studio_output",
    "studio_freshness_report.md": "generated_studio_output",
    "studio_graphics_queue.csv": "generated_studio_output",
    "studio_stale_packet_queue.csv": "generated_studio_output",
    "threads_queue.csv": "generated_queue_output",
    "threads_queue_v2.csv": "generated_queue_output",
    "ig_feed_queue.csv": "generated_queue_output",
    "ig_feed_queue_v2.csv": "generated_queue_output",
    "ig_story_queue.csv": "generated_queue_output",
    "ig_story_queue_v2.csv": "generated_queue_output",
    "mermaid_content_slots_v2.csv": "generated_mermaid_output",
    "mermaid_master_content_board.md": "generated_mermaid_output",
    "mermaid_story_graph.csv": "generated_mermaid_output",
    "mermaid_upper_echelon_report.md": "generated_mermaid_output",
    "multi_post_daily_board.json": "generated_queue_output",
    "multi_post_daily_board.md": "generated_queue_output",
}

SAFE_DELETE_PATTERNS = {
    "assignment_*.csv": "generated_assignment_output",
    "assignment_*.json": "generated_assignment_output",
    "assignment_*.md": "generated_assignment_output",
    "bebe_*.csv": "generated_bebe_output",
    "bebe_*.json": "generated_bebe_output",
    "bebe_*.md": "generated_bebe_output",
    "breaking_news_queue*.csv": "generated_queue_output",
    "content_director_*.csv": "generated_content_director_output",
    "content_director_*.json": "generated_content_director_output",
    "content_director_*.md": "generated_content_director_output",
    "contract_validation_*.json": "generated_contract_validation_output",
    "contract_validation_*.md": "generated_contract_validation_output",
    "daily_slate_*.csv": "generated_daily_slate_output",
    "daily_slate_*.md": "generated_daily_slate_output",
    "final_score_story_guard_report.*": "generated_story_guard_output",
    "graphics_*.csv": "generated_graphics_output",
    "graphics_*.json": "generated_graphics_output",
    "graphics_*.md": "generated_graphics_output",
    "ig_feed_*.csv": "generated_queue_output",
    "ig_story_*.csv": "generated_queue_output",
    "ig_story_*.json": "generated_queue_output",
    "ig_story_*.md": "generated_queue_output",
    "install_report.*": "generated_install_report",
    "manual_workflow_*.csv": "generated_manual_workflow_output",
    "manual_workflow_*.json": "generated_manual_workflow_output",
    "manual_workflow_*.jsonl": "generated_manual_workflow_output",
    "manual_workflow_*.md": "generated_manual_workflow_output",
    "mermaid_*.csv": "generated_mermaid_output",
    "mermaid_*.json": "generated_mermaid_output",
    "mermaid_*.jsonl": "generated_mermaid_output",
    "mermaid_*.md": "generated_mermaid_output",
    "multisport_*.csv": "generated_multisport_output",
    "multisport_*.json": "generated_multisport_output",
    "multisport_*.md": "generated_multisport_output",
    "official_player_headshot_*.csv": "generated_player_asset_output",
    "official_player_headshot_*.md": "generated_player_asset_output",
    "operator_*.md": "generated_operator_output",
    "operator_*.json": "generated_operator_output",
    "operator_*.csv": "generated_operator_output",
    "player_asset_*.csv": "generated_player_asset_output",
    "player_registry_*.json": "generated_player_asset_output",
    "player_registry_*.md": "generated_player_asset_output",
    "player_assets.*": "generated_player_asset_output",
    "player_image_*.csv": "generated_player_asset_output",
    "player_image_*.md": "generated_player_asset_output",
    "publish_guard_report.*": "generated_publish_guard",
    "rendered_handoff_*.csv": "generated_rendered_handoff",
    "rendered_handoff_*.json": "generated_rendered_handoff",
    "rendered_handoff_*.md": "generated_rendered_handoff",
    "rendered_handoff_*.jpg": "generated_rendered_handoff",
    "rendered_slide_qa.*": "generated_render_qa",
    "rumor_watch_queue*.csv": "generated_queue_output",
    "social_rumor_*.csv": "generated_social_rumor_output",
    "social_rumor_*.json": "generated_social_rumor_output",
    "social_rumor_*.md": "generated_social_rumor_output",
    "source_registry_audit.*": "generated_source_registry_audit",
    "story_candidates_*.csv": "generated_story_candidates",
    "story_candidates_*.jsonl": "generated_story_candidates",
    "studio_*.csv": "generated_studio_output",
    "studio_*.md": "generated_studio_output",
    "threads_*.csv": "generated_queue_output",
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
    basename = norm.split("/")[-1]
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
                "reason": "Generated output/archive directory should be artifact-only, not committed to main.",
            }
    for pattern, category in SAFE_DELETE_PATTERNS.items():
        if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(norm, pattern):
            return {
                "path": norm,
                "classification": "tracked_generated_output",
                "category": category,
                "safe_delete_candidate": True,
                "reason": "Generated handoff/queue/report file should be artifact-only, not committed to main.",
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
        "category": "not_generated_by_phase2_cleanup_rules",
        "safe_delete_candidate": False,
        "reason": "No Phase 2 generated-output rule matched this path.",
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
            f"{len(generated_rows)} tracked generated/cache files matched Phase 2 cleanup rules. Review the delete plan before removing files."
            if generated_rows else "No tracked generated-output files matched Phase 2 cleanup rules."
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
