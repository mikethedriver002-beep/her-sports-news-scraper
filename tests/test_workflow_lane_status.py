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
    assert manifest["completed_lane_count"] == 0
    assert manifest["guardrail_warning_count"] == 0
    assert manifest["worktree_hint_lane_count"] == 0
    assert manifest["unreported_lane_count"] == 6
    assert manifest["heartbeat_lane_count"] == 1
    assert manifest["stale_lane_count"] == 0
    assert manifest["stale_lane_threshold_hours"] == 48
    assert manifest["workflow_overhaul_heartbeat"]["active"] is True
    assert manifest["workflow_overhaul_heartbeat"]["status"] == "heartbeat_visible_needs_conductor_check"
    assert manifest["workflow_overhaul_heartbeat"]["guardrails"]["review_only"] is True
    assert manifest["workflow_overhaul_heartbeat"]["guardrails"]["automatic_downloads"] is False
    assert {row["lane_id"] for row in rows} >= {"workflow_overhaul", "qa_release_readiness"}
    workflow = next(row for row in rows if row["lane_id"] == "workflow_overhaul")
    assert "status_source" in rows[0]
    assert "completed_merge_pr" in rows[0]
    assert "pending_thread" in rows[0]
    assert "heartbeat" in rows[0]
    assert "staleness_status" in rows[0]
    assert workflow["status"] == "heartbeat_visible_needs_conductor_check"
    assert workflow["status_source"] == "workflow_heartbeat"
    assert workflow["status_tone"] == "idle"
    assert workflow["heartbeat"] == "true"
    assert workflow["stale_lane_brake"] == "false"
    assert workflow["staleness_status"] == "not_applicable"
    assert "open PRs" in workflow["heartbeat_next_action"]
    assert "review_only" in rows[0]
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["approval_state_change"] == "false" for row in rows)
    assert "Status: review-only conductor visibility artifact." in markdown
    assert "No automatic downloads." in markdown
    assert "workflow_lane_status_intake.example.csv" in markdown
    assert "Pending thread" in markdown
    assert "best-effort worktree hints" in markdown
    assert "## Workflow Overhaul Heartbeat" in markdown
    assert "## Stale Lane Brake" in markdown
    assert "Active stale or missing-update lanes: `0`" in markdown
    assert "Continuous visibility heartbeat" in markdown
    assert "Do not fetch sources, download assets, approve assets" in markdown


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
                "pending_thread": "019f04ad-9680-7e83-a9c5-db1e36d52543",
                "owner": "renderer lane",
                "last_update_utc": "2026-06-28T12:00:00+00:00",
                "completed_merge_pr": "",
                "completed_merge_commit": "",
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
    assert renderer["pending_thread"] == "019f04ad-9680-7e83-a9c5-db1e36d52543"
    assert renderer["blocker"] == "waiting for Gemini critique"
    assert renderer["next_action"] == "Send research packet, then choose one renderer polish PR."
    assert payload["blocked_lane_count"] == 1


def test_workflow_lane_status_surfaces_completed_merge_rows_as_review_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    intake = tmp_path / "operator" / "inbox" / "workflow_lane_status_intake.csv"
    module = load_module()
    write_csv(
        intake,
        [
            {
                "lane_id": "workflow_overhaul",
                "status": "completed_merged",
                "branch": "codex/hsd-conductor-directive-brake",
                "pr": "https://github.com/example/hsd/pull/338",
                "owner": "conductor",
                "last_update_utc": "2026-06-29T07:06:55Z",
                "completed_merge_pr": "338",
                "completed_merge_commit": "3f69d86e",
                "blocker": "",
                "next_action": "Use immutable directive snapshots only.",
                "notes": "Completion row; not a live directive.",
                "review_only": "true",
                "paid_apis": "false",
                "source_fetching": "false",
                "automatic_downloads": "false",
                "auto_approval": "false",
                "approval_state_change": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        ],
        module.INTAKE_FIELDS,
    )

    payload = module.build_payload(module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup"]))
    workflow = next(row for row in payload["lanes"] if row["lane_id"] == "workflow_overhaul")

    assert workflow["status"] == "completed_merged"
    assert workflow["status_tone"] == "completed"
    assert workflow["branch"] == "codex/hsd-conductor-directive-brake"
    assert workflow["status_source"] == "manual_intake"
    assert workflow["completed_merge_pr"] == "338"
    assert workflow["completed_merge_commit"] == "3f69d86e"
    assert workflow["pending_thread"] == ""
    assert workflow["review_only"] == "true"
    assert workflow["paid_apis"] == "false"
    assert workflow["publish_ready"] == "false"
    assert workflow["approval_state_change"] == "false"
    assert workflow["guardrail_warnings"] == ""
    assert workflow["stale_lane_brake"] == "false"
    assert workflow["staleness_status"] == "not_applicable"
    assert payload["completed_lane_count"] == 1
    assert payload["stale_lane_count"] == 0
    assert payload["guardrail_warning_count"] == 0


def test_workflow_lane_status_flags_stale_active_manual_lane_without_state_change(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    intake = tmp_path / "operator" / "inbox" / "workflow_lane_status_intake.csv"
    module = load_module()
    row = {field: "" for field in module.INTAKE_FIELDS}
    row.update(
        {
            "lane_id": "workflow_overhaul",
            "status": "pr_open",
            "branch": "codex/workflow-old-lane",
            "pr": "https://github.com/example/hsd/pull/300",
            "owner": "workflow lane",
            "last_update_utc": "2026-06-26T00:00:00Z",
            "next_action": "Refresh current proof before continuing.",
            "review_only": "true",
            "paid_apis": "false",
            "source_fetching": "false",
            "automatic_downloads": "false",
            "auto_approval": "false",
            "approval_state_change": "false",
            "headshot_writes": "false",
            "approved_marker_writes": "false",
            "publish_ready": "false",
            "publishing": "false",
        }
    )
    write_csv(intake, [row], module.INTAKE_FIELDS)

    payload = module.build_payload(
        module.parse_args(
            [
                "--skip-pr-lookup",
                "--skip-worktree-lookup",
                "--as-of-utc",
                "2026-06-29T12:00:00Z",
            ]
        )
    )
    workflow = next(row for row in payload["lanes"] if row["lane_id"] == "workflow_overhaul")

    assert workflow["status"] == "pr_open"
    assert workflow["status_source"] == "manual_intake"
    assert workflow["staleness_status"] == "stale_lane_needs_conductor_check"
    assert workflow["stale_lane_brake"] == "true"
    assert workflow["stale_age_hours"] == "84.0"
    assert workflow["stale_warning"] == "last_update_utc_older_than_48h"
    assert workflow["review_only"] == "true"
    assert workflow["automatic_downloads"] == "false"
    assert workflow["auto_approval"] == "false"
    assert workflow["approval_state_change"] == "false"
    assert workflow["publish_ready"] == "false"
    assert payload["stale_lane_count"] == 1
    assert payload["paid_apis"] is False
    assert payload["automatic_downloads"] is False
    assert payload["publish_ready"] is False


def test_workflow_lane_status_flags_active_manual_lane_missing_update(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    intake = tmp_path / "operator" / "inbox" / "workflow_lane_status_intake.csv"
    module = load_module()
    row = {field: "" for field in module.INTAKE_FIELDS}
    row.update(
        {
            "lane_id": "qa_release_readiness",
            "status": "active_or_needs_conductor_check",
            "branch": "codex/qa-proof-refresh",
        }
    )
    write_csv(intake, [row], module.INTAKE_FIELDS)

    payload = module.build_payload(
        module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup", "--as-of-utc", "2026-06-29T12:00:00Z"])
    )
    qa = next(row for row in payload["lanes"] if row["lane_id"] == "qa_release_readiness")

    assert qa["staleness_status"] == "missing_last_update_needs_conductor_check"
    assert qa["stale_lane_brake"] == "true"
    assert qa["stale_warning"] == "manual_intake_active_without_last_update_utc"
    assert payload["stale_lane_count"] == 1


def test_workflow_lane_status_flags_truthy_guardrail_intake_without_enabling_behavior(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    intake = tmp_path / "operator" / "inbox" / "workflow_lane_status_intake.csv"
    module = load_module()
    row = {field: "" for field in module.INTAKE_FIELDS}
    row.update(
        {
            "lane_id": "qa_release_readiness",
            "status": "needs_human_guardrail_review",
            "publish_ready": "true",
            "auto_approval": "true",
            "approval_state_change": "true",
        }
    )
    write_csv(intake, [row], module.INTAKE_FIELDS)

    payload = module.build_payload(module.parse_args(["--skip-pr-lookup", "--skip-worktree-lookup"]))
    qa = next(row for row in payload["lanes"] if row["lane_id"] == "qa_release_readiness")

    assert qa["status"] == "needs_human_guardrail_review"
    assert qa["status_tone"] == "blocked"
    assert "publish_ready_expected_false_got_true" in qa["guardrail_warnings"]
    assert "auto_approval_expected_false_got_true" in qa["guardrail_warnings"]
    assert "approval_state_change_expected_false_got_true" in qa["guardrail_warnings"]
    assert payload["publish_ready"] is False
    assert payload["auto_approval"] is False
    assert payload["approval_state_change"] is False
    assert payload["guardrail_warning_count"] == 1


def test_workflow_lane_status_surfaces_pending_thread_without_pr(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run"))
    intake = tmp_path / "operator" / "inbox" / "workflow_lane_status_intake.csv"
    module = load_module()
    row = {field: "" for field in module.INTAKE_FIELDS}
    row.update(
        {
            "lane_id": "workflow_overhaul",
            "status": "active_pending_thread_needs_conductor_check",
            "pending_thread": "019f04ad-9680-7e83-a9c5-db1e36d52543",
            "next_action": "Inspect pending delegated thread before nudging another workflow packet.",
        }
    )
    write_csv(intake, [row], module.INTAKE_FIELDS)

    assert module.main(["--skip-pr-lookup", "--skip-worktree-lookup"]) == 0

    manifest = json.loads((tmp_path / "run" / "workflow_lane_status_dashboard.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((tmp_path / "run" / "workflow_lane_status_dashboard.csv").open(newline="", encoding="utf-8")))
    markdown = (tmp_path / "run" / "workflow_lane_status_dashboard.md").read_text(encoding="utf-8")
    workflow = next(row for row in rows if row["lane_id"] == "workflow_overhaul")

    assert workflow["status"] == "active_pending_thread_needs_conductor_check"
    assert workflow["status_source"] == "manual_intake"
    assert workflow["pending_thread"] == "019f04ad-9680-7e83-a9c5-db1e36d52543"
    assert workflow["pr"] == ""
    assert manifest["workflow_overhaul_heartbeat"]["active"] is False
    assert "019f04ad-9680-7e83-a9c5-db1e36d52543" in markdown
    assert "Use `pending_thread` for a delegated Codex thread id or URL" in markdown


def test_workflow_lane_status_example_intake_documents_recent_completed_merges() -> None:
    module = load_module()
    example = REPO / "operator" / "inbox" / "workflow_lane_status_intake.example.csv"
    rows = list(csv.DictReader(example.open(newline="", encoding="utf-8")))

    assert rows
    assert set(rows[0]) == set(module.INTAKE_FIELDS)
    assert {row["completed_merge_pr"] for row in rows} == {"336", "337", "338", "339", "340"}
    assert {row["status"] for row in rows} == {"completed_merged"}
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["paid_apis"] == "false" for row in rows)
    assert all(row["source_fetching"] == "false" for row in rows)
    assert all(row["automatic_downloads"] == "false" for row in rows)
    assert all(row["auto_approval"] == "false" for row in rows)
    assert all(row["approval_state_change"] == "false" for row in rows)
    assert all(row["headshot_writes"] == "false" for row in rows)
    assert all(row["approved_marker_writes"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["publishing"] == "false" for row in rows)


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
    assert workflow["heartbeat"] == "false"


def test_workflow_lane_status_ignores_merged_worktree_hints(tmp_path: Path, monkeypatch) -> None:
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
                "path": r"C:\Users\Mike\.codex\worktrees\34b9\her-sports-news-scraper",
                "branch": "codex/workflow-lane-status-hints",
                "head": "abcdef",
                "dirty": "false",
                "dirty_count": "0",
                "merged_to_main": "true",
            }
        ],
    )
    workflow = next(row for row in hinted_rows if row["lane_id"] == "workflow_overhaul")

    assert workflow["status"] == "heartbeat_visible_needs_conductor_check"
    assert workflow["status_source"] == "workflow_heartbeat"
    assert workflow["heartbeat"] == "true"
    assert workflow["branch"] == ""
    assert workflow["detected_worktree"] == ""


def test_workflow_lane_status_ignores_merged_pr_branch_hints(tmp_path: Path, monkeypatch) -> None:
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
                "path": r"C:\Users\Mike\.codex\worktrees\4db2\her-sports-news-scraper",
                "branch": "codex/renderer-editorial-lower-third-identifiers",
                "head": "498eca5",
                "dirty": "false",
                "dirty_count": "0",
                "merged_to_main": "false",
                "merged_pr": "true",
            }
        ],
    )
    renderer = next(row for row in hinted_rows if row["lane_id"] == "renderer_quality")

    assert renderer["status"] == "unreported"
    assert renderer["status_source"] == "default"
    assert renderer["branch"] == ""
    assert renderer["detected_worktree"] == ""


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
