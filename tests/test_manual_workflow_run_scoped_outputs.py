from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_manual_workflow_merge_v1.py"


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_manual_workflow_merge_writes_outputs_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    write_csv(
        work_dir / "operator" / "inbox" / "manual_workflow_inbox.csv",
        [
            {
                "manual_item_id": "manual-1",
                "status": "approved",
                "priority": "P1",
                "platform_targets": "IG Feed; Threads",
                "content_family": "Manual Feature",
                "story_type": "feature",
                "headline": "Run-scoped manual story",
                "angle": "Operator-approved free-source story.",
                "source_url": "https://example.com/source",
            }
        ],
        [
            "manual_item_id",
            "status",
            "priority",
            "platform_targets",
            "content_family",
            "story_type",
            "headline",
            "angle",
            "source_url",
        ],
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
    assert json.loads(proc.stdout)["output_scope"] == "run_scoped"
    assert (run_dir / "manual_workflow_handoff.md").exists()
    assert (run_dir / "manual_workflow_pack_status.csv").exists()
    assert (run_dir / "manual_workflow_content_packets.csv").exists()
    assert (run_dir / "manual_workflow_render_plans.json").exists()
    assert any((run_dir / "manual_workflow_handoff_packs").glob("*.zip"))
    assert any((run_dir / "manual_workflow_packets").iterdir())
    assert not (work_dir / "manual_workflow_handoff.md").exists()
    assert not (work_dir / "manual_workflow_handoff_packs").exists()


def test_manual_workflow_merge_preserves_legacy_root_output_when_env_unset(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env={**os.environ.copy(), "PYTHONPATH": str(REPO)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["output_scope"] == "legacy_root"
    assert (work_dir / "manual_workflow_handoff.md").exists()
    assert (work_dir / "manual_workflow_pack_status.csv").exists()
