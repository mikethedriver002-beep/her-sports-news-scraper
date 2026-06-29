from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_release_readiness_rollup_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_release_readiness_rollup_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_release_readiness_rollup_writes_review_only_false_guardrail_fields(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run"
    scan_dir = tmp_path / "latest"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    (run_dir).mkdir()
    (run_dir / "conductor_workspace_audit.json").write_text(
        json.dumps({"status": "passed", "collision_blocker_count": 0, "workspace_hash": "abc123"}),
        encoding="utf-8",
    )
    write_csv(
        scan_dir / "operator_board.csv",
        [
            {
                "row_id": "release-readiness-safe",
                "review_only": "true",
                "publish_ready": "false",
                "auto_publish": "false",
                "paid_apis": "false",
                "source_fetching": "false",
                "asset_downloads": "false",
                "automatic_downloads": "false",
                "auto_approval": "false",
                "approval_state_change": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publishing": "false",
            }
        ],
    )

    module = load_module()
    assert module.main(["--scan-dir", str(scan_dir)]) == 0

    manifest = json.loads((run_dir / "release_readiness_guardrail_rollup.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((run_dir / "release_readiness_guardrail_rollup.csv").open(newline="", encoding="utf-8")))
    markdown = (run_dir / "release_readiness_guardrail_rollup.md").read_text(encoding="utf-8")

    assert manifest["version"] == "hsd-release-readiness-rollup-v1-review-only"
    assert manifest["status"] == "passed"
    assert manifest["review_only"] is True
    assert manifest["blocker_count"] == 0
    assert manifest["latest_artifact_scan"]["scan_files_checked"] == 1
    assert manifest["latest_artifact_scan"]["violation_count"] == 0
    assert manifest["guardrails"]["paid_apis"] is False
    assert manifest["guardrails"]["source_fetching"] is False
    assert manifest["guardrails"]["asset_downloads"] is False
    assert manifest["guardrails"]["automatic_downloads"] is False
    assert manifest["guardrails"]["auto_approval"] is False
    assert manifest["guardrails"]["approval_state_change"] is False
    assert manifest["guardrails"]["headshot_writes"] is False
    assert manifest["guardrails"]["approved_marker_writes"] is False
    assert manifest["guardrails"]["publish_ready"] is False
    assert manifest["guardrails"]["publishing"] is False
    assert {row["check_id"] for row in rows} >= {
        "deterministic_guardrail_config",
        "latest_artifact_guardrail_scan",
        "conductor_workspace_audit",
        "hard_release_guardrail_posture",
    }
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["auto_publish"] == "false" for row in rows)
    assert all(row["source_fetching"] == "false" for row in rows)
    assert all(row["automatic_downloads"] == "false" for row in rows)
    assert all(row["auto_approval"] == "false" for row in rows)
    assert "Status: review-only release-readiness evidence artifact." in markdown
    assert "No publish-ready lane or movement." in markdown


def test_release_readiness_rollup_defaults_to_active_run_output_dir(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    run_dir.mkdir()
    (run_dir / "conductor_workspace_audit.json").write_text(
        json.dumps({"status": "passed", "collision_blocker_count": 0, "workspace_hash": "abc123"}),
        encoding="utf-8",
    )
    write_csv(
        run_dir / "safe_review_board.csv",
        [
            {
                "row_id": "current-run-safe",
                "publish_ready": "false",
                "auto_publish": "false",
                "paid_apis": "false",
                "source_fetching": "false",
                "asset_downloads": "false",
                "automatic_downloads": "false",
                "auto_approval": "false",
                "approval_state_change": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publishing": "false",
            }
        ],
    )

    module = load_module()
    assert module.main([]) == 0

    manifest = json.loads((run_dir / "release_readiness_guardrail_rollup.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "passed"
    assert manifest["missing_inputs"] == []
    assert manifest["latest_artifact_scan"]["status"] == "passed"
    assert manifest["latest_artifact_scan"]["scan_files_checked"] >= 2
    assert manifest["latest_artifact_scan"]["scan_dir"] == run_dir.as_posix()


def test_release_readiness_rollup_blocks_truthy_generated_artifact_guardrail_fields(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run"
    scan_dir = tmp_path / "latest"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    (run_dir).mkdir()
    (run_dir / "conductor_workspace_audit.json").write_text(
        json.dumps({"status": "passed", "collision_blocker_count": 0, "workspace_hash": "abc123"}),
        encoding="utf-8",
    )
    write_csv(
        scan_dir / "unsafe_board.csv",
        [
            {
                "row_id": "unsafe",
                "source_fetching": "true",
                "publish_ready": "false",
                "auto_approval": "false",
            }
        ],
    )

    module = load_module()
    payload = module.build_payload(str(scan_dir))

    assert payload["status"] == "blocked"
    assert payload["blocker_count"] == 1
    assert payload["latest_artifact_scan"]["violations"][0]["code"] == "truthy_guardrail_csv"
    scan_row = next(row for row in payload["checks"] if row["check_id"] == "latest_artifact_guardrail_scan")
    assert scan_row["status"] == "blocked"
