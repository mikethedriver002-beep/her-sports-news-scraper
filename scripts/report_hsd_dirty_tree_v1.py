from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v1.0-dirty-tree-category-audit"
DEFAULT_OUTPUT_JSON = "dirty_tree_v1.json"
DEFAULT_OUTPUT_MD = "dirty_tree_v1.md"

GENERATED_DIR_PREFIXES = (
    "hsd_pipeline_lite_review/",
    "outputs/latest/",
    "dashboard/",
    "results_dashboard/",
    "run_history/",
    "results_run_history/",
    "launch_run_history/",
    "generated_graphics/",
    "graphics_chat_upload_pack/",
    "graphics_chat_upload_pack_zips/",
    "graphics_clean_prompts/",
    "manual_workflow_packets/",
    "manual_workflow_handoff_packs/",
    "ig_story_results_upload_pack/",
    "ig_story_results_upload_pack_zips/",
    "assignment_handoff_packets/",
    "assignment_handoff_zips/",
    "mermaid_assignment_compiled_packets/",
    "mermaid_assignment_final_packets/",
    "mermaid_compiled_packets/",
    "mermaid_director_compiled_packets/",
    "mermaid_quality_compiled_packets/",
    "rendered_handoff_graphics/",
    "rendered_handoff_zips/",
    "runs/",
)

ROOT_GENERATED_PREFIXES = (
    "assignment_",
    "bebe_",
    "breaking_news_queue",
    "content_director_",
    "contract_validation_",
    "daily_slate_",
    "final_score_story_guard_report",
    "graphics_",
    "ig_feed_",
    "ig_story_",
    "manual_workflow_",
    "mermaid_",
    "multisport_",
    "official_player_headshot_",
    "operator_",
    "player_asset_",
    "player_registry_",
    "player_image_",
    "rendered_handoff_",
    "rendered_slide_qa",
    "rumor_watch_queue",
    "social_rumor_",
    "source_registry_audit",
    "story_candidates_",
    "studio_",
    "threads_",
)

ROOT_GENERATED_EXACT = {
    "approved_graphics_assets.csv",
    "approved_graphics_assets.json",
    "asset_candidates_review.md",
    "caption_bank.md",
    "daily_results_recommendations.md",
    "dirty_tree_v1.json",
    "dirty_tree_v1.md",
    "discovery_sources_report.md",
    "first_comment_hooks.md",
    "generated_output_pollution_v1.json",
    "generated_output_pollution_v1.md",
    "hsd_current_run.json",
    "install_report.json",
    "install_report.md",
    "latest_news_sync_run_summary.md",
    "manual_story_inbox_report.md",
    "multi_post_daily_board.json",
    "multi_post_daily_board.md",
    "news_fact_packets.csv",
    "pipeline_stop_reason.md",
    "player_assets.csv",
    "player_assets.json",
    "post_slot_status.csv",
    "publish_guard_report.md",
    "render_integrity_report.md",
    "run_manifest.json",
    "source_health_report.csv",
    "top_womens_results.csv",
    "wnba_box_score_audit.csv",
    "wnba_box_score_summary.md",
}

SOURCE_PREFIXES = ("scripts/", "tests/", ".github/workflows/")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_git_status(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(repo_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return proc.stdout if proc.returncode == 0 else ""
    except Exception:
        return ""


def parse_status_line(line: str) -> Dict[str, str]:
    raw = line.rstrip("\n")
    status = raw[:2]
    path = raw[3:] if len(raw) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ")[-1]
    return {"raw": raw, "status": status, "path": path.replace("\\", "/")}


def classify_dirty_path(path: str) -> str:
    norm = path.replace("\\", "/").lstrip("./")
    base = norm.split("/")[-1]
    if norm.startswith("assets/leagues/wnba/athletes/") and norm.endswith(".approved"):
        return "asset_approval_marker_mutation"
    if norm.startswith("assets/leagues/wnba/teams/"):
        return "asset_team_logo_runtime_output"
    if norm.startswith("assets/"):
        return "asset_file_mutation"
    if norm.startswith("data/asset_registry/wnba/"):
        return "wnba_asset_registry_mutation"
    if norm == "config/hsd_expected_games_v5.csv":
        return "expected_games_config_runtime_output"
    if norm.startswith("config/"):
        return "config_mutation"
    if any(norm.startswith(prefix) for prefix in GENERATED_DIR_PREFIXES):
        return "generated_output_dir_or_archive"
    if base in ROOT_GENERATED_EXACT or any(base.startswith(prefix) for prefix in ROOT_GENERATED_PREFIXES):
        return "generated_root_handoff_or_report"
    if norm.endswith(".pyc") or "__pycache__/" in norm or norm.startswith("__pycache__/"):
        return "runtime_cache"
    if norm.startswith(SOURCE_PREFIXES) or norm.endswith(".py"):
        return "source_or_test_mutation"
    if "/" not in norm:
        return "unclassified_root_file"
    return "unclassified_other"


def build_report_from_status(status_text: str, repo_root: Path | None = None) -> Dict[str, Any]:
    rows = []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        row = parse_status_line(line)
        row["category"] = classify_dirty_path(row["path"])
        row["is_untracked"] = row["status"] == "??"
        row["is_deleted"] = "D" in row["status"]
        row["is_modified"] = "M" in row["status"]
        rows.append(row)
    category_counts = Counter(row["category"] for row in rows)
    status_counts = Counter(row["status"] for row in rows)
    by_category: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row["path"])
    source_rows = [row for row in rows if row["category"] == "source_or_test_mutation"]
    unclassified_rows = [row for row in rows if row["category"].startswith("unclassified")]
    generated_rows = [row for row in rows if row["category"] in {"generated_output_dir_or_archive", "generated_root_handoff_or_report", "runtime_cache"}]
    asset_rows = [row for row in rows if row["category"] in {"asset_approval_marker_mutation", "asset_team_logo_runtime_output", "asset_file_mutation", "wnba_asset_registry_mutation"}]
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "repo_root": repo_root.as_posix() if repo_root else "",
        "dirty": bool(rows),
        "dirty_entry_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "source_or_test_mutation_count": len(source_rows),
        "generated_dirty_count": len(generated_rows),
        "asset_or_registry_dirty_count": len(asset_rows),
        "unclassified_dirty_count": len(unclassified_rows),
        "rows": rows,
        "paths_by_category": {key: sorted(value) for key, value in sorted(by_category.items())},
        "publish_gate": "source_review_required" if source_rows or unclassified_rows else "classified_dirty_tree_only" if rows else "clean_tree",
        "human_summary": "Dirty tree is classified. Review source/unclassified counts first.",
    }


def build_report(repo_root: Path) -> Dict[str, Any]:
    return build_report_from_status(run_git_status(repo_root), repo_root=repo_root)


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# HSD Dirty Tree Audit v1",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Version: `{report.get('version')}`",
        f"Dirty: `{report.get('dirty')}`",
        f"Publish gate: `{report.get('publish_gate')}`",
        "",
        "## Summary",
        "",
        f"- Dirty entries: `{report.get('dirty_entry_count')}`",
        f"- Generated dirty entries: `{report.get('generated_dirty_count')}`",
        f"- Asset/registry dirty entries: `{report.get('asset_or_registry_dirty_count')}`",
        f"- Source/test dirty entries: `{report.get('source_or_test_mutation_count')}`",
        f"- Unclassified dirty entries: `{report.get('unclassified_dirty_count')}`",
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
    lines += ["", "## First paths by category", ""]
    by_category = report.get("paths_by_category") or {}
    for category, paths in by_category.items():
        lines.append(f"### {category}")
        for p in paths[:25]:
            lines.append(f"- `{p}`")
        if len(paths) > 25:
            lines.append(f"- ... `{len(paths) - 25}` more")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify current git dirty tree for HSD V4 hygiene.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--json", default=DEFAULT_OUTPUT_JSON, help="Output JSON path.")
    parser.add_argument("--md", default=DEFAULT_OUTPUT_MD, help="Output Markdown path.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero for source/unclassified dirty entries.")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    report = build_report(root)
    out_json = Path(args.json)
    out_md = Path(args.md)
    if not out_json.is_absolute():
        out_json = root / out_json
    if not out_md.is_absolute():
        out_md = root / out_md
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, out_md)
    print(json.dumps({
        "version": VERSION,
        "dirty_entry_count": report.get("dirty_entry_count"),
        "generated_dirty_count": report.get("generated_dirty_count"),
        "asset_or_registry_dirty_count": report.get("asset_or_registry_dirty_count"),
        "source_or_test_mutation_count": report.get("source_or_test_mutation_count"),
        "unclassified_dirty_count": report.get("unclassified_dirty_count"),
        "publish_gate": report.get("publish_gate"),
        "json": out_json.as_posix(),
        "md": out_md.as_posix(),
    }, indent=2))
    if args.strict and (report.get("source_or_test_mutation_count") or report.get("unclassified_dirty_count")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
