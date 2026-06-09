from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

FILES = [
    "studio_fresh_packet_report.md",
    "studio_fresh_packet_gate.csv",
    "studio_command_center.md",
    "studio_graphics_queue.csv",
    "studio_bundle_queue.csv",
    "studio_bundle_packets.md",
    "studio_bundle_prompts.md",
    "studio_bundle_caption_bank.md",
    "studio_top_graphic_packets.md",
    "studio_image_prompts.md",
    "studio_caption_bank.md",
    "studio_accuracy_checklist.csv",
    "studio_manual_review_graphics.csv",
    "studio_post_schedule.md",
    "studio_brand_config.json",
    "studio_graphics_sop.json",
    "studio_manifest.json",
    "studio_dashboard/index.html",
    "brand_assets/hsd_watermark_bug.svg",
]


def row_count(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    with path.open(newline="", encoding="utf-8") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def main() -> None:
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    time = f"{now.strftime('%H%M%S_UTC')}_{__import__('os').environ.get('GITHUB_RUN_ID', 'local')}"
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    run_dir = Path("studio_run_history") / date / time
    latest = Path("studio_run_history") / "latest"
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
        "# HSD Studio Bridge v1.3 Run Summary",
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
        summary.extend(["", "## Missing files", ""])
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
    Path("latest_studio_run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    index = Path("studio_run_history") / "_index.md"
    if index.exists():
        existing = index.read_text(encoding="utf-8")
    else:
        existing = "# HSD Studio Bridge Run History\n\n| Run UTC | Archive Folder | Files |\n|---|---:|---:|\n"
    entry = f"| {stamp} | [Open archive]({run_dir.as_posix()}) | {len(copied)} files |\n"
    lines = existing.splitlines(keepends=True)
    updated = "".join(lines[:4]) + entry + "".join(lines[4:]) if len(lines) >= 4 else existing + entry
    index.write_text(updated, encoding="utf-8")

    print(f"Archived {len(copied)} studio files to {run_dir}")


if __name__ == "__main__":
    main()
