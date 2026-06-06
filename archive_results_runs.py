
"""
Her Sports Daily Results Run Archiver
-------------------------------------

Keeps the latest result files in the repo root and also saves each run under:
    results_run_history/YYYY-MM-DD/HHMM_UTC/
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

FILES_TO_ARCHIVE = [
    "today_results_board.csv",
    "today_box_scores.csv",
    "top_performers.csv",
    "results_graphics_queue.md",
    "results_dashboard_seed.csv",
    "results_system_hub.md",
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
    run_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []

    for file_name in FILES_TO_ARCHIVE:
        src = Path(file_name)
        if not src.exists():
            missing.append(file_name)
            continue
        dst = run_dir / file_name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(file_name)

    summary = [
        "# Her Sports Daily Results Run Summary",
        "",
        f"Run timestamp UTC: `{stamp}`",
        f"Archive folder: `{run_dir.as_posix()}`",
        "",
        "## Archived files",
        "",
    ]
    for item in copied:
        summary.append(f"- `{item}`")
    if missing:
        summary.extend(["", "## Missing files", ""])
        for item in missing:
            summary.append(f"- `{item}`")

    manifest = {
        "run_timestamp_utc": stamp,
        "archive_folder": run_dir.as_posix(),
        "copied_files": copied,
        "missing_files": missing,
        "row_counts": {name: row_count(Path(name)) for name in copied if name.endswith(".csv")},
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_sha": os.environ.get("GITHUB_SHA", ""),
    }

    (run_dir / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
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
