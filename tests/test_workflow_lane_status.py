from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_workflow_lane_status_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_workflow_lane_status_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_builds_review_only_workflow_lane_status_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    assert module.main(["--skip-pr-lookup"]) == 0

    dashboard = tmp_path / "run" / "workflow_lane_status_dashboard.md"
    manifest = json.loads((tmp_path / "run" / "workflow_lane_status_dashboard.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((tmp_path / "run" / "workflow_lane_status_dashboard.csv").open(newline="", encoding="utf-8")))
    markdown = dashboard.read_text(encoding="utf-8")

    assert dashboard.exists()
    assert manifest["version"] == "hsd-workflow-lane-status-v1-review-only"
    assert manifest["status"] == "workflow_lane_status_ready"
    assert manifest["review_only"] is True
    assert manifest["paid_apis"] is False
    assert manifest["automatic_downloads"] is False
    assert manifest["auto_approval"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publishing"] is False
    assert manifest["publish_ready"] is False
    assert manifest["lane_count"] == 7
    assert {row["lane_id"] for row in rows} >= {"workflow_overhaul", "qa_release_readiness"}
    assert "Status: review-only conductor visibility artifact." in markdown
    assert "No automatic downloads." in markdown


def test_workflow_lane_status_applies_manual_intake_overlay(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    intake = tmp_path / "operator" / "inbox" / "workflow_lane_status_intake.csv"
    module = load_module()
    write_csv(
        intake,
        [
            {
                "lane_id": "renderer_quality",
                "status": "blocked_needs_human_visual_review",
                "branch": "codex/renderer-visual-lift",
                "pr": "https://github.com/example/hsd/pull/999",
                "owner": "renderer lane",
                "last_update_utc": "2026-06-28T12:00:00+00:00",
                "blocker": "waiting for Gemini critique",
                "next_action": "Send research packet, then choose one renderer polish PR.",
                "notes": "Do not continue without visual review.",
            }
        ],
        module.INTAKE_FIELDS,
    )

    payload = module.build_payload(module.parse_args(["--skip-pr-lookup"]))
    renderer = next(row for row in payload["lanes"] if row["lane_id"] == "renderer_quality")

    assert renderer["status"] == "blocked_needs_human_visual_review"
    assert renderer["status_tone"] == "blocked"
    assert renderer["branch"] == "codex/renderer-visual-lift"
    assert renderer["blocker"] == "waiting for Gemini critique"
    assert renderer["next_action"] == "Send research packet, then choose one renderer polish PR."
    assert payload["blocked_lane_count"] == 1


def test_local_runner_and_command_center_collect_workflow_lane_status() -> None:
    runner = (REPO / "scripts" / "hsd_local.ps1").read_text(encoding="utf-8")
    command_center = (REPO / "generate_hsd_operator_command_center_v2.py").read_text(encoding="utf-8")

    assert "scripts\\build_hsd_workflow_lane_status_v1.py" in runner
    assert "workflow_lane_status_dashboard.md" in runner
    assert "workflow_lane_status_dashboard.csv" in runner
    assert "workflow_lane_status_dashboard.json" in runner
    assert "(\"Decision\", \"Workflow lane status\", \"workflow_lane_status_dashboard.md\")" in command_center
