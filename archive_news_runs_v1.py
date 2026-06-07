from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

FILES_TO_ARCHIVE = [
    "news_input_status_report.csv",
    "news_setup_error.md",
    "news_candidate_queue.csv",
    "news_source_observations.csv",
    "news_fact_packets.csv",
    "news_brief_queue.md",
    "news_social_packets.md",
    "news_graphics_handoff.md",
    "news_daily_plan.md",
    "news_manual_review_queue.csv",
    "news_sync_hub.md",
    "news_sync_manifest.json",
    "news_dashboard/index.html",
]


def row_count(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    with path.open(newline="", encoding="utf-8") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def main() -> None:
    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    run_time = now.strftime("%H%M_UTC")
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    run_dir = Path("news_run_history") / run_date / run_time
    latest_dir = Path("news_run_history") / "latest"
    for d in [run_dir, latest_dir]:
        d.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []
    for name in FILES_TO_ARCHIVE:
        src = Path(name)
        if not src.exists():
            missing.append(name)
            continue
        for target in [run_dir, latest_dir]:
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copied.append(name)

    row_counts = {name: row_count(Path(name)) for name in copied if name.endswith(".csv")}
    manifest = {
        "run_timestamp_utc": stamp,
        "archive_folder": run_dir.as_posix(),
        "latest_folder": latest_dir.as_posix(),
        "copied_files": copied,
        "missing_files": missing,
        "row_counts": row_counts,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_sha": os.environ.get("GITHUB_SHA", ""),
    }

    summary = [
        "# Her Sports Daily News Sync v1.4 Run Summary",
        "",
        f"Run timestamp UTC: `{stamp}`",
        f"Archive folder: `{run_dir.as_posix()}`",
        "",
        "## Row counts",
        "",
    ]
    for name, count in row_counts.items():
        summary.append(f"- `{name}`: {count}")
    summary.extend(["", "## Archived files", ""])
    for item in copied:
        summary.append(f"- `{item}`")
    if missing:
        summary.extend(["", "## Missing files", ""])
        for item in missing:
            summary.append(f"- `{item}`")

    (run_dir / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (latest_dir / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (latest_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    Path("latest_news_sync_run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    index = Path("news_run_history") / "_index.md"
    if index.exists():
        existing = index.read_text(encoding="utf-8")
    else:
        existing = "# Her Sports Daily News Sync Run History\n\n| Run UTC | Archive Folder | Files |\n|---|---:|---:|\n"
    entry = f"| {stamp} | [Open archive]({run_dir.as_posix()}) | {len(copied)} files |\n"
    lines = existing.splitlines(keepends=True)
    updated = "".join(lines[:4]) + entry + "".join(lines[4:]) if len(lines) >= 4 else existing + entry
    index.write_text(updated, encoding="utf-8")

    print(f"Archived {len(copied)} files to {run_dir}")


if __name__ == "__main__":
    main()
