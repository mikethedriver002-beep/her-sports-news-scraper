
from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

FILES_TO_ARCHIVE = [
    "source_observations.csv",
    "reconciled_events.csv",
    "today_results_board.csv",
    "today_womens_results.csv",
    "today_final_results.csv",
    "top_womens_results.csv",
    "manual_review_queue.csv",
    "source_health_report.csv",
    "wnba_box_score_audit.csv",
    "wnba_box_score_summary.md",
    "results_graphics_queue.md",
    "daily_results_recommendations.md",
    "results_system_hub.md",
    "run_manifest.json",
    "results_dashboard/index.html",
]


def row_count(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return max(0, sum(1 for _ in csv.reader(f)) - 1)
    except Exception:
        return 0


def main() -> None:
    now = datetime.now(timezone.utc)
    run_date = now.strftime("%Y-%m-%d")
    run_time = now.strftime("%H%M_UTC")
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    run_dir = Path("results_run_history") / run_date / run_time
    latest_dir = Path("results_run_history") / "latest"

    for d in [run_dir, latest_dir]:
        d.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []

    for file_name in FILES_TO_ARCHIVE:
        src = Path(file_name)
        if not src.exists():
            missing.append(file_name)
            continue
        for target in [run_dir, latest_dir]:
            dst = target / file_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copied.append(file_name)

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
        "# Her Sports Daily Results Desk v4.3 Run Summary",
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
    Path("latest_results_run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    index_path = Path("results_run_history") / "_index.md"
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
    else:
        existing = "# Her Sports Daily Results Run History\n\n| Run UTC | Archive Folder | Files |\n|---|---:|---:|\n"

    entry = f"| {stamp} | [Open archive]({run_dir.as_posix()}) | {len(copied)} files |\n"
    lines = existing.splitlines(keepends=True)
    if len(lines) >= 4:
        updated = "".join(lines[:4]) + entry + "".join(lines[4:])
    else:
        updated = existing + entry
    index_path.write_text(updated, encoding="utf-8")

    print(f"Archived {len(copied)} files to {run_dir}")


if __name__ == "__main__":
    main()
