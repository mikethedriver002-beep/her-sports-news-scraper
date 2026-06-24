from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_dashboard.py"
RUNNER = REPO / "scripts" / "hsd_local.ps1"
DOC = REPO / "docs" / "HSD_LEGACY_DASHBOARD_AUDIT.md"


def stdout_json(proc: subprocess.CompletedProcess[str]) -> dict:
    start = proc.stdout.index("{")
    return json.loads(proc.stdout[start:])


def test_legacy_dashboard_replacement_writes_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    run_dir.mkdir(parents=True)
    (run_dir / "operator_command_center.html").write_text("<html>Command center</html>", encoding="utf-8")

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
    assert payload["status"] == "replaced_by_operator_command_center"
    assert payload["output_scope"] == "run_scoped"
    assert payload["replacement_exists"] is True
    assert (run_dir / "dashboard" / "index.html").exists()
    assert (run_dir / "legacy_dashboard_replacement.md").exists()
    assert (run_dir / "legacy_dashboard_replacement.json").exists()
    assert not (work_dir / "dashboard").exists()
    assert not (work_dir / "legacy_dashboard_replacement.md").exists()
    assert "operator_command_center.html" in (run_dir / "dashboard" / "index.html").read_text(encoding="utf-8")


def test_legacy_dashboard_replacement_preserves_direct_legacy_output(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    (work_dir / "operator_command_center.html").write_text("<html>Command center</html>", encoding="utf-8")

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
    assert (work_dir / "dashboard" / "index.html").exists()
    assert (work_dir / "legacy_dashboard_replacement.md").exists()
    assert (work_dir / "legacy_dashboard_replacement.json").exists()


def test_legacy_dashboard_is_replaced_by_command_center_not_local_default() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    assert "generate_hsd_dashboard.py" not in runner
    assert "replaced_by_operator_command_center" in script
    assert "operator_command_center.html" in script
    assert "The daily operator home base is `operator_command_center.html`." in doc
