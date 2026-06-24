from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_launch_control_v1.py"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def seed_studio_bundle_files(base: Path) -> None:
    write_csv(
        base / "studio_bundle_queue.csv",
        [
            {
                "bundle_id": "bundle-1",
                "production_priority": "POST FIRST",
                "bundle_name": "Tonight in the W",
                "bundle_type": "main_wnba_result",
                "asset_shape": "1080x1350",
                "slide_count": "4",
                "source_items_count": "2",
                "caption_seed": "New York Liberty closed strong in the fourth.",
                "source_headlines": "Liberty beat Aces",
            }
        ],
        [
            "bundle_id",
            "production_priority",
            "bundle_name",
            "bundle_type",
            "asset_shape",
            "slide_count",
            "source_items_count",
            "caption_seed",
            "source_headlines",
        ],
    )
    (base / "studio_bundle_packets.md").write_text(
        "# Studio Bundle Packets\n\n## Tonight in the W\nVerified bundle packet.",
        encoding="utf-8",
    )
    (base / "studio_bundle_caption_bank.md").write_text(
        "# Caption Bank\n\nNew York Liberty closed strong in the fourth.",
        encoding="utf-8",
    )
    (base / "studio_manifest.json").write_text(
        json.dumps({"version": "test-studio", "counts": {"studio_bundles_created": 1}}),
        encoding="utf-8",
    )


def stdout_json(proc: subprocess.CompletedProcess[str]) -> dict:
    start = proc.stdout.index("{")
    return json.loads(proc.stdout[start:])


def test_launch_control_writes_outputs_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    seed_studio_bundle_files(run_dir)

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
    payload = stdout_json(proc)
    assert payload["output_scope"] == "run_scoped"
    assert payload["bundles_read"] == 1
    assert payload["publish_queue_rows"] == 1
    assert (run_dir / "launch_command_center.md").exists()
    assert (run_dir / "launch_daily_runbook.md").exists()
    assert (run_dir / "launch_graphics_chat_brief.md").exists()
    assert (run_dir / "launch_instagram_publish_queue.csv").exists()
    assert (run_dir / "launch_quality_gate.csv").exists()
    assert (run_dir / "launch_7_day_performance_dashboard.md").exists()
    assert (run_dir / "launch_dashboard" / "index.html").exists()
    assert (run_dir / "launch_analytics_dashboard" / "index.html").exists()
    assert not (work_dir / "launch_command_center.md").exists()
    assert not (work_dir / "launch_dashboard").exists()

    manifest = json.loads((run_dir / "launch_manifest.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "run_scoped"
    assert manifest["counts"]["publish_queue_rows"] == 1


def test_launch_control_preserves_legacy_root_output_when_env_unset(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    seed_studio_bundle_files(work_dir)

    env = os.environ.copy()
    env.pop("HSD_RUN_OUTPUT_DIR", None)
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
    payload = stdout_json(proc)
    assert payload["output_scope"] == "legacy_root"
    assert (work_dir / "launch_command_center.md").exists()
    assert (work_dir / "launch_instagram_publish_queue.csv").exists()
    assert (work_dir / "launch_dashboard" / "index.html").exists()
    assert (work_dir / "launch_analytics_dashboard" / "index.html").exists()

    manifest = json.loads((work_dir / "launch_manifest.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "legacy_root"
