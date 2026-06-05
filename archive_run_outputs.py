"""
Her Sports Daily Run Archive
----------------------------

Purpose:
Keep the live/latest files in the repo root while also saving every workflow run
to a timestamped run_history folder so earlier runs are not overwritten.

Creates:
    run_history/YYYY-MM-DD/HHMM_UTC/
        important output files from that run
        run_manifest.json
        run_summary.md

Also updates:
    run_history/_index.md
    latest_run_summary.md

No external packages required.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


# Archive only the files that are actually useful for reviewing/producing content.
# The root/latest versions still remain in place and will be overwritten on each run.
FILES_TO_ARCHIVE = [
    "womens_sports_articles.csv",
    "daily_content_brief.csv",
    "story_context_enriched.csv",

    # Daily decision and production files
    "master_posting_dashboard.csv",
    "daily_command_file.csv",
    "today_graphics_queue.md",
    "today_graphics_queue.csv",
    "top_3_graphic_packets.md",
    "dashboard/index.html",

    # Useful creative files
    "ready_to_post_graphic_copy.csv",
    "caption_bank_v2.csv",
    "reel_script_package.md",
    "image_generation_prompts.csv",

    # Summary hubs
    "hsd_daily_content_hub.md",
    "hsd_publish_system_hub.md",
    "hsd_graphics_system_hub.md",
]


def safe_count_csv(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        return max(0, len(rows) - 1)
    except Exception:
        return 0


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def summarize_run(run_dir: Path, copied_files: List[str], missing_files: List[str], run_timestamp: str) -> str:
    dashboard_rows = read_csv_rows(Path("master_posting_dashboard.csv"))
    brief_rows = read_csv_rows(Path("daily_content_brief.csv"))
    context_rows = read_csv_rows(Path("story_context_enriched.csv"))

    top_posts = []
    for row in dashboard_rows[:5]:
        headline = row.get("headline", "")
        decision = row.get("editorial_decision", "")
        order = row.get("posting_order", "")
        template = row.get("template_name", "")
        top_posts.append(f"{order}. **{decision}** | {headline} | `{template}`")

    if not top_posts:
        for row in brief_rows[:5]:
            headline = row.get("headline", "")
            decision = row.get("editorial_decision", "")
            rank = row.get("rank", "")
            story_type = row.get("story_type", "")
            top_posts.append(f"{rank}. **{decision}** | {headline} | `{story_type}`")

    context_flags = []
    for row in context_rows:
        if str(row.get("manual_review_flag", "")).lower() == "yes":
            context_flags.append(row.get("headline", ""))

    lines = [
        "# Her Sports Daily Run Summary",
        "",
        f"Run timestamp UTC: `{run_timestamp}`",
        f"Archive folder: `{run_dir.as_posix()}`",
        "",
        "## Top posts",
        "",
    ]

    if top_posts:
        lines.extend(top_posts)
    else:
        lines.append("No top posts found.")

    lines.extend([
        "",
        "## Context review flags",
        "",
    ])

    if context_flags:
        for item in context_flags[:10]:
            lines.append(f"- {item}")
    else:
        lines.append("No manual review flags found in story_context_enriched.csv.")

    lines.extend([
        "",
        "## Archived files",
        "",
    ])

    for file_name in copied_files:
        lines.append(f"- `{file_name}`")

    if missing_files:
        lines.extend([
            "",
            "## Missing files",
            "",
        ])
        for file_name in missing_files:
            lines.append(f"- `{file_name}`")

    return "\n".join(lines) + "\n"


def update_index(run_timestamp: str, run_dir: Path, copied_files: List[str]) -> None:
    index_path = Path("run_history") / "_index.md"
    index_path.parent.mkdir(exist_ok=True)

    entry = (
        f"| {run_timestamp} | "
        f"[Open archive]({run_dir.as_posix()}) | "
        f"{len(copied_files)} files |\n"
    )

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
    else:
        existing = (
            "# Her Sports Daily Run History\n\n"
            "| Run UTC | Archive Folder | Files |\n"
            "|---|---:|---:|\n"
        )

    # Add newest entry below table header.
    lines = existing.splitlines(keepends=True)
    if len(lines) >= 4 and lines[0].startswith("# Her Sports Daily Run History"):
        updated = "".join(lines[:4]) + entry + "".join(lines[4:])
    else:
        updated = (
            "# Her Sports Daily Run History\n\n"
            "| Run UTC | Archive Folder | Files |\n"
            "|---|---:|---:|\n"
            + entry
            + "\n"
            + existing
        )

    index_path.write_text(updated, encoding="utf-8")


def main() -> None:
    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    run_time = now.strftime("%H%M_UTC")
    run_timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    run_dir = Path("run_history") / run_date / run_time
    run_dir.mkdir(parents=True, exist_ok=True)

    copied_files: List[str] = []
    missing_files: List[str] = []

    for file_name in FILES_TO_ARCHIVE:
        source = Path(file_name)

        if not source.exists():
            missing_files.append(file_name)
            continue

        destination = run_dir / file_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied_files.append(file_name)

    manifest = {
        "run_timestamp_utc": run_timestamp,
        "run_date": run_date,
        "run_time": run_time,
        "archive_folder": run_dir.as_posix(),
        "copied_files": copied_files,
        "missing_files": missing_files,
        "row_counts": {
            file_name: safe_count_csv(Path(file_name))
            for file_name in copied_files
            if file_name.endswith(".csv")
        },
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
        "github_sha": os.environ.get("GITHUB_SHA", ""),
    }

    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    summary = summarize_run(run_dir, copied_files, missing_files, run_timestamp)
    (run_dir / "run_summary.md").write_text(summary, encoding="utf-8")
    Path("latest_run_summary.md").write_text(summary, encoding="utf-8")

    update_index(run_timestamp, run_dir, copied_files)

    print(f"Archived {len(copied_files)} files to {run_dir}")
    if missing_files:
        print(f"Missing {len(missing_files)} optional files: {', '.join(missing_files)}")


if __name__ == "__main__":
    main()
