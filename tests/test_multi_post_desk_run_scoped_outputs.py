from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_multi_post_desk_v1.py"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "slots": [
                    {"slot_id": "threads_morning_board", "slot_name": "Morning Threads board", "platform": "Threads", "window_et": "9:00 AM"},
                    {"slot_id": "ig_feed_noon", "slot_name": "Noon IG feed", "platform": "IG Feed", "window_et": "12:00 PM"},
                    {"slot_id": "ig_story_results", "slot_name": "IG Stories results/update lane", "platform": "IG Stories", "window_et": "10:30 AM"},
                ]
            }
        ),
        encoding="utf-8",
    )


def test_multi_post_desk_writes_outputs_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    write_config(work_dir / "config" / "hsd_multi_post_slots_v1.json")
    write_csv(
        run_dir / "manual_workflow_content_packets.csv",
        [
            {
                "packet_id": "packet-feed",
                "priority": "P1",
                "platform_targets": "IG Feed; Threads",
                "story_type": "feature",
                "content_family": "Manual Feature",
                "headline": "Run-scoped feed story",
                "content_readiness": "ready_with_review",
                "source_type": "manual_workflow_inbox_csv",
            }
        ],
        ["packet_id", "priority", "platform_targets", "story_type", "content_family", "headline", "content_readiness", "source_type"],
    )
    write_csv(
        run_dir / "ig_story_results_upload_pack_status.csv",
        [
            {
                "story_id": "story-1",
                "story_slug": "last-night-in-the-w",
                "upload_pack_status": "ready_with_review",
                "zip_path": "ig_story_results_upload_pack_zips/last-night-in-the-w.zip",
            }
        ],
        ["story_id", "story_slug", "upload_pack_status", "zip_path"],
    )
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["output_scope"] == "run_scoped"
    assert payload["slot_count"] == 3
    assert payload["ig_feed_queue_count"] == 1
    assert payload["ig_story_queue_count"] == 1
    assert payload["threads_queue_count"] == 1
    assert (run_dir / "multi_post_daily_board.md").exists()
    assert (run_dir / "multi_post_daily_board.json").exists()
    assert (run_dir / "post_slot_status.csv").exists()
    assert (run_dir / "ig_feed_queue.csv").exists()
    assert (run_dir / "ig_story_queue.csv").exists()
    assert (run_dir / "threads_queue.csv").exists()
    assert (run_dir / "caption_bank.md").exists()
    assert (run_dir / "first_comment_hooks.md").exists()
    assert not (work_dir / "multi_post_daily_board.md").exists()
    manifest = json.loads((run_dir / "multi_post_daily_board.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "run_scoped"


def test_multi_post_desk_preserves_legacy_root_output_when_env_unset(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    write_config(work_dir / "config" / "hsd_multi_post_slots_v1.json")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["output_scope"] == "legacy_root"
    assert (work_dir / "multi_post_daily_board.md").exists()
    assert (work_dir / "multi_post_daily_board.json").exists()
