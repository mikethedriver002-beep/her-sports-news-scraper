from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_run_output_migration_v1.py"
DOC = REPO / "docs" / "HSD_RUN_OUTPUT_MIGRATION_AUDIT.md"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_run_output_migration_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_output_migration_audit_records_asset_graphics_batch_as_run_aware() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    asset_scripts = {
        "generate_hsd_asset_desk_v1.py",
        "generate_hsd_player_image_assets_v1.py",
        "generate_hsd_graphics_upload_pack_v1.py",
        "generate_hsd_graphics_qa_v1.py",
    }
    pending_batch = {row["script"] for row in report["prioritized_batches"]["batch_1_asset_graphics"]}
    run_aware = {row["script"] for row in report["prioritized_batches"]["already_run_scoped"]}

    assert pending_batch.isdisjoint(asset_scripts)
    assert asset_scripts <= run_aware
    assert report["policy"]["free_source_policy_unchanged"] is True
    assert report["policy"]["manual_only_default"] is True
    assert report["policy"]["workflow_changes_required"] is False
    assert report["policy"]["paid_api_changes_required"] is False
    assert "canonical asset registry" in report["asset_stage_caution"]


def test_run_output_migration_audit_keeps_migrated_daily_chain_out_of_legacy_batches() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    legacy = {
        row["script"]
        for key in ["batch_1_asset_graphics", "batch_2_support_dashboards", "batch_3_legacy_scraper"]
        for row in report["prioritized_batches"][key]
    }

    migrated = {
        "generate_hsd_results_desk_v5.py",
        "generate_hsd_news_sync_v1.py",
        "generate_hsd_studio_bridge_v1.py",
        "generate_hsd_tonight_preview_bridge_v1.py",
        "generate_hsd_preview_quality_gate_v1.py",
        "publish_hsd_guard_v1.py",
        "generate_hsd_operator_status_v1.py",
        "generate_hsd_bebe_daily_ops_plan_v2.py",
        "generate_hsd_operator_command_center_v2.py",
        "generate_hsd_pipeline_review_lite_v1.py",
    }

    assert migrated.isdisjoint(legacy)


def test_run_output_migration_audit_records_results_news_support_as_run_aware() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    support_scripts = {
        "scripts/generate_hsd_expected_games_v5.py",
        "scripts/verify_hsd_wnba_schedule_independent_v5.py",
        "generate_news_dashboard_v1.py",
    }
    pending_batch = {row["script"] for row in report["prioritized_batches"]["batch_2_support_dashboards"]}
    run_aware = {row["script"] for row in report["prioritized_batches"]["already_run_scoped"]}

    assert pending_batch.isdisjoint(support_scripts)
    assert support_scripts <= run_aware


def test_run_output_migration_audit_records_legacy_scraper_retirement() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    runner_scripts = {row["script"] for row in report["runner_scripts"]}
    md = module.render_md(report)

    assert report["prioritized_batches"]["batch_3_legacy_scraper"] == []
    assert report["legacy_scraper_retirement"]["active_local_mode"] is False
    assert report["legacy_scraper_retirement"]["decision"] == "retired_from_active_local_workflow"
    assert "womens_sports_scraper.py" not in runner_scripts
    assert "legacy scraper retired from active local modes" in md


def test_run_output_migration_audit_drops_manual_workflow_merge_from_legacy_writers() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    large_legacy = {row["script"] for row in report["large_non_runner_legacy_writers"]}
    run_aware = {row["script"] for row in report["prioritized_batches"]["already_run_scoped"]}
    text = (REPO / "generate_hsd_manual_workflow_merge_v1.py").read_text(encoding="utf-8")

    assert "generate_hsd_manual_workflow_merge_v1.py" not in large_legacy
    assert "generate_hsd_manual_workflow_merge_v1.py" in run_aware
    assert "from hsd_run_io import" in text
    assert 'OUT_DIR = output_path("manual_workflow_packets")' in text


def test_run_output_migration_audit_drops_final_score_stories_from_legacy_writers() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    large_legacy = {row["script"] for row in report["large_non_runner_legacy_writers"]}
    run_aware = {row["script"] for row in report["prioritized_batches"]["already_run_scoped"]}
    text = (REPO / "generate_hsd_final_score_stories_v1.py").read_text(encoding="utf-8")

    assert "generate_hsd_final_score_stories_v1.py" not in large_legacy
    assert "generate_hsd_final_score_stories_v1.py" in run_aware
    assert "from hsd_run_io import" in text
    assert 'OUT_PACK_DIR = output_path("ig_story_results_upload_pack")' in text


def test_run_output_migration_audit_records_multi_post_desk_as_run_aware() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    large_legacy = {row["script"] for row in report["large_non_runner_legacy_writers"]}
    run_aware = {row["script"] for row in report["prioritized_batches"]["already_run_scoped"]}
    text = (REPO / "generate_hsd_multi_post_desk_v1.py").read_text(encoding="utf-8")

    assert "generate_hsd_multi_post_desk_v1.py" not in large_legacy
    assert "generate_hsd_multi_post_desk_v1.py" in run_aware
    assert "from hsd_run_io import" in text
    assert 'OUT_BOARD_MD = "multi_post_daily_board.md"' in text


def test_run_output_migration_audit_records_launch_control_as_run_aware() -> None:
    module = load_module()
    report = module.build_audit(REPO)
    large_legacy = {row["script"] for row in report["large_non_runner_legacy_writers"]}
    run_aware = {row["script"] for row in report["prioritized_batches"]["already_run_scoped"]}
    text = (REPO / "generate_hsd_launch_control_v1.py").read_text(encoding="utf-8")

    assert "generate_hsd_launch_control_v1.py" not in large_legacy
    assert "generate_hsd_launch_control_v1.py" in run_aware
    assert "from hsd_run_io import" in text
    assert 'OUT_COMMAND_CENTER = "launch_command_center.md"' in text
    assert '"output_scope": "run_scoped" if run_dir else "legacy_root"' in text


def test_run_output_migration_doc_records_priority_and_guardrails() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "Batch 1 asset/graphics and Batch 2 Results/News support migrations are complete." in text
    assert "generate_hsd_graphics_upload_pack_v1.py" in text
    assert "scripts/generate_hsd_expected_games_v5.py" in text
    assert "Batch 3 is retired from the active local workflow instead of migrated." in text
    assert "generate_hsd_manual_workflow_merge_v1.py" in text
    assert "explicit `handoff` mode" in text
    assert "generate_hsd_final_score_stories_v1.py" in text
    assert "explicit `stories` mode" in text
    assert "generate_hsd_multi_post_desk_v1.py" in text
    assert "explicit `posts` mode" in text
    assert "generate_hsd_launch_control_v1.py" in text
    assert "explicit `launch` mode" in text
    assert "generate_hsd_source_registry_audit_v2.py" in text
    assert "source registry status" in text
    assert "generate_hsd_dashboard.py" in text
    assert "compatibility entrypoint" in text
    assert "womens_sports_scraper.py" in text
    assert "Paid APIs are not part of this migration." in text
    assert "No auto-publishing or workflow automation should be added." in text
    assert "HSD_RUN_OUTPUT_DIR" in text


def test_run_output_migration_audit_writes_to_run_folder_when_env_set(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-files"
    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(REPO),
            "--output-json",
            "audit.json",
            "--output-md",
            "audit.md",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert (run_dir / "audit.json").exists()
    assert (run_dir / "audit.md").exists()
    assert not (tmp_path / "audit.json").exists()
    payload = json.loads((run_dir / "audit.json").read_text(encoding="utf-8"))
    assert payload["version"] == "v1.0-run-output-migration-audit"
