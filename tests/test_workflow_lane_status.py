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
    assert module.main(["--skip-pr-lookup", "--skip-worktree-lookup"]) == 0

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
    assert manifest["worktree_hint_lane_count"] == 0
    assert {row["lane_id"] for row in rows} >= {"workflow_overhaul", "qa_release_readiness"}
    assert "status_source" in rows[0]
    assert "Status: review-only conductor visibility artifact." in markdown
    assert "No automatic downloads." in markdown
    assert "best-effort worktree hints" in markdown


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

    payload = module.build_payload(module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup"]))
    renderer = next(row for row in payload["lanes"] if row["lane_id"] == "renderer_quality")

    assert renderer["status"] == "blocked_needs_human_visual_review"
    assert renderer["status_tone"] == "blocked"
    assert renderer["branch"] == "codex/renderer-visual-lift"
    assert renderer["blocker"] == "waiting for Gemini critique"
    assert renderer["next_action"] == "Send research packet, then choose one renderer polish PR."
    assert payload["blocked_lane_count"] == 1


def test_workflow_lane_status_uses_worktree_branch_hints_without_manual_intake(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    payload = module.build_payload(
        module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup"])
    )
    hinted_rows = module.lane_rows(
        [],
        [],
        payload["git_state"],
        [
            {
                "path": r"C:\Users\Mike\.codex\worktrees\abcd\her-sports-news-scraper",
                "branch": "codex/renderer-lower-third-polish",
                "head": "123456",
                "dirty": "false",
                "dirty_count": "0",
            }
        ],
    )
    renderer = next(row for row in hinted_rows if row["lane_id"] == "renderer_quality")

    assert renderer["status"] == "worktree_branch_detected_needs_conductor_check"
    assert renderer["status_tone"] == "active"
    assert renderer["status_source"] == "worktree_hint"
    assert renderer["branch"] == "codex/renderer-lower-third-polish"
    assert renderer["detected_worktree"].endswith(r"abcd\her-sports-news-scraper")
    assert "dirty=false" in renderer["notes"]


def test_workflow_lane_status_links_open_pr_from_worktree_hint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    payload = module.build_payload(
        module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup"])
    )
    hinted_rows = module.lane_rows(
        [],
        [
            {
                "number": "328",
                "title": "Add research alert draft helper",
                "branch": "codex/workflow-research-alert-draft",
                "state": "draft",
                "url": "https://github.com/example/hsd/pull/328",
            }
        ],
        payload["git_state"],
        [
            {
                "path": r"C:\Users\Mike\.codex\worktrees\34b9\her-sports-news-scraper",
                "branch": "codex/workflow-research-alert-draft",
                "head": "abcdef",
                "dirty": "false",
                "dirty_count": "0",
            }
        ],
    )
    workflow = next(row for row in hinted_rows if row["lane_id"] == "workflow_overhaul")

    assert workflow["status"] == "pr_open_from_worktree_hint"
    assert workflow["pr"] == "https://github.com/example/hsd/pull/328"
    assert workflow["status_source"] == "worktree_hint"


def test_workflow_lane_status_prefers_asset_lane_for_hockey_softball_source_map(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))

    module = load_module()
    payload = module.build_payload(
        module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup"])
    )
    hinted_rows = module.lane_rows(
        [],
        [],
        payload["git_state"],
        [
            {
                "path": r"C:\Users\Mike\.codex\worktrees\0e0d\her-sports-news-scraper",
                "branch": "codex/hockey-softball-source-map-readiness",
                "head": "fedcba",
                "dirty": "false",
                "dirty_count": "0",
            }
        ],
    )
    asset = next(row for row in hinted_rows if row["lane_id"] == "asset_registry_contact_sheets")
    qa = next(row for row in hinted_rows if row["lane_id"] == "qa_release_readiness")

    assert asset["status_source"] == "worktree_hint"
    assert asset["branch"] == "codex/hockey-softball-source-map-readiness"
    assert qa["status"] == "unreported"


def test_local_runner_and_command_center_collect_workflow_lane_status() -> None:
    runner = (REPO / "scripts" / "hsd_local.ps1").read_text(encoding="utf-8")
    command_center = (REPO / "generate_hsd_operator_command_center_v2.py").read_text(encoding="utf-8")

    assert "scripts\\build_hsd_workflow_lane_status_v1.py" in runner
    assert "workflow_lane_status_dashboard.md" in runner
    assert "workflow_lane_status_dashboard.csv" in runner
    assert "workflow_lane_status_dashboard.json" in runner
    assert "(\"Decision\", \"Workflow lane status\", \"workflow_lane_status_dashboard.md\")" in command_center
