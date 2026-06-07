from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

FILES = [
    "launch_command_center.md",
    "launch_daily_runbook.md",
    "launch_graphics_chat_brief.md",
    "launch_instagram_publish_queue.csv",
    "launch_caption_drafts.md",
    "launch_story_plan.md",
    "launch_quality_gate.csv",
    "launch_account_setup_checklist.md",
    "launch_7_day_content_calendar.md",
    "launch_operating_sop.md",
    "launch_manifest.json",
    "launch_dashboard/index.html",
    "launch_setup_error.md",
]


def row_count(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    with path.open(newline="", encoding="utf-8") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def main() -> None:
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H%M_UTC")
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    run_dir = Path("launch_run_history") / date / time
    latest = Path("launch_run_history") / "latest"
    for d in [run_dir, latest]:
        d.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []
    for name in FILES:
        src = Path(name)
        if not src.exists():
            missing.append(name)
            continue
        for target in [run_dir, latest]:
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        copied.append(name)

    counts = {name: row_count(Path(name)) for name in copied if name.endswith(".csv")}
    summary = [
        "# HSD Launch Control Run Summary",
        "",
        f"Run timestamp UTC: `{stamp}`",
        f"Archive folder: `{run_dir.as_posix()}`",
        "",
        "## Row counts",
        "",
    ]
    for k, v in counts.items():
        summary.append(f"- `{k}`: {v}")
    summary.extend(["", "## Archived files", ""])
    for f in copied:
        summary.append(f"- `{f}`")
    if missing:
        summary.extend(["", "## Missing optional files", ""])
        for f in missing:
            summary.append(f"- `{f}`")

    manifest = {
        "run_timestamp_utc": stamp,
        "archive_folder": run_dir.as_posix(),
        "latest_folder": latest.as_posix(),
        "copied_files": copied,
        "missing_files": missing,
        "row_counts": counts,
    }

    (run_dir / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (latest / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (latest / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    Path("latest_launch_run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    index = Path("launch_run_history") / "_index.md"
    if index.exists():
        existing = index.read_text(encoding="utf-8")
    else:
        existing = "# HSD Launch Control Run History\n\n| Run UTC | Archive Folder | Files |\n|---|---:|---:|\n"
    entry = f"| {stamp} | [Open archive]({run_dir.as_posix()}) | {len(copied)} files |\n"
    lines = existing.splitlines(keepends=True)
    updated = "".join(lines[:4]) + entry + "".join(lines[4:]) if len(lines) >= 4 else existing + entry
    index.write_text(updated, encoding="utf-8")

    print(f"Archived {len(copied)} launch files to {run_dir}")


if __name__ == "__main__":
    main()
