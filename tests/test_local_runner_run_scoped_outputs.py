from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "hsd_local.ps1"
DOC = REPO / "LOCAL_DEVELOPMENT.md"


def test_local_runner_creates_run_scoped_output_context() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "function New-HsdRunContext" in text
    assert "outputs\\local\\$stamp" in text
    assert "generated_state" in text
    assert "generated_state_manifest.json" in text
    assert "local_run_manifest.json" in text
    assert "$env:HSD_LOCAL_RUN_ROOT" in text
    assert "$env:HSD_RUN_OUTPUT_DIR" in text
    assert '$env:HSD_OUTPUT_MODE = "run_scoped_local"' in text


def test_local_runner_archives_generated_state_before_root_restore() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    finally_block = text[text.index("    } finally {") : text.index("function Open-Dashboard")]

    assert "Copy-HsdGeneratedRunState $runContext $generatedBaseline" in finally_block
    assert "Collect-HsdArtifacts $runContext" in finally_block
    assert "Restore-GeneratedGitState $generatedBaseline" in finally_block
    assert finally_block.index("Copy-HsdGeneratedRunState") < finally_block.index("Collect-HsdArtifacts")
    assert finally_block.index("Collect-HsdArtifacts") < finally_block.index("Restore-GeneratedGitState")


def test_generated_state_quarantine_covers_daily_pipeline_outputs() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    required_pathspecs = [
        "operator_command_center.*",
        "publish_guard_report.*",
        "results_desk_v5_manifest.json",
        "news_fact_packets.csv",
        "studio_bundle_*",
        "bebe_*",
        "manual_workflow_*",
        "hsd_pipeline_lite_review/**",
        "outputs/latest/**",
        "assets/leagues/wnba/athletes/*/headshot.png",
        "config/hsd_expected_games_v5.csv",
    ]

    for pathspec in required_pathspecs:
        assert f'"{pathspec}"' in text


def test_local_run_manifest_preserves_free_manual_policy() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert 'output_mode = "run_scoped_local"' in text
    assert "manual_only = $true" in text
    assert "paid_apis_disabled = $true" in text
    assert '$env:HSD_PAID_APIS_DISABLED = "1"' in text
    assert '$env:HSD_SOURCE_COST_MODE = "free_first"' in text


def test_local_development_docs_describe_run_scoped_outputs() -> None:
    doc = DOC.read_text(encoding="utf-8")

    assert "outputs/local/<timestamp>/files/" in doc
    assert "outputs/local/<timestamp>/generated_state/" in doc
    assert "generated_state_manifest.json" in doc
    assert "-KeepGeneratedState" in doc
