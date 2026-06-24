from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_source_registry_audit_v2.py"


def write_registry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "registry_version": "test-registry",
                "green_approved_decision": ["Use official scoreboards for publish-ready facts."],
                "sources": [
                    {
                        "source_id": "espn_wnba_public",
                        "source_type": "scoreboard_site",
                        "tier": "official",
                        "trust_band": "green",
                        "enabled": True,
                        "sport_league": "WNBA",
                        "automation_status": "manual_or_fetch_allowed",
                        "publish_policy": "publish_ready_after_cross_check",
                        "urls": ["https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"],
                    },
                    {
                        "source_id": "social_tip",
                        "source_type": "mastodon_public",
                        "tier": "social",
                        "trust_band": "yellow",
                        "enabled": True,
                        "sport_league": "Women sports",
                        "automation_status": "manual_review",
                        "publish_policy": "discovery_only",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def stdout_json(proc: subprocess.CompletedProcess[str]) -> dict:
    start = proc.stdout.index("{")
    return json.loads(proc.stdout[start:])


def test_source_registry_audit_writes_outputs_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    write_registry(work_dir / "config" / "source_registry.json")

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
    assert payload["sources"] == 2
    assert payload["review"] == 1
    assert payload["fail"] == 0
    assert (run_dir / "source_registry_audit.csv").exists()
    assert (run_dir / "source_coverage_map.csv").exists()
    assert (run_dir / "source_registry_audit.md").exists()
    assert (run_dir / "source_registry_audit.json").exists()
    assert not (work_dir / "source_registry_audit.csv").exists()
    assert not (work_dir / "source_registry_audit.md").exists()

    manifest = json.loads((run_dir / "source_registry_audit.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "run_scoped"
    assert manifest["registry_version"] == "test-registry"
    assert manifest["counts"]["coverage_total"] >= 1
    assert any(row["coverage_key"] == "pwhl" and row["coverage_status"] == "gap" for row in manifest["coverage_map"])
    report = (run_dir / "source_registry_audit.md").read_text(encoding="utf-8")
    assert "## Coverage map" in report
    assert "PWHL" in report


def test_source_registry_audit_preserves_legacy_root_output_when_env_unset(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    write_registry(work_dir / "config" / "source_registry.json")

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
    assert (work_dir / "source_registry_audit.csv").exists()
    assert (work_dir / "source_coverage_map.csv").exists()
    assert (work_dir / "source_registry_audit.md").exists()
    assert (work_dir / "source_registry_audit.json").exists()
