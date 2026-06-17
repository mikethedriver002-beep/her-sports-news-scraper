from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_generated_output_pollution_v1.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"
GITIGNORE = REPO / ".gitignore"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_generated_output_pollution_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_output_pollution_classifier_marks_artifacts_but_not_source() -> None:
    module = load_module()

    generated = module.classify_path("outputs/latest/HSD_TEMPLATE_FACTORY/foo.png")
    assert generated["classification"] == "tracked_generated_output"
    assert generated["safe_delete_candidate"] is True

    legacy = module.classify_path("run_history/2026-06-17/2227_UTC/womens_sports_articles.csv")
    assert legacy["classification"] == "tracked_generated_output"
    assert legacy["category"] == "legacy_news_run_archive"

    root_output = module.classify_path("caption_bank_v2.csv")
    assert root_output["classification"] == "tracked_generated_output"
    assert root_output["category"] == "legacy_news_output"

    review_required = module.classify_path("config/hsd_expected_games_v5.csv")
    assert review_required["classification"] == "generated_review_required"
    assert review_required["safe_delete_candidate"] is False

    source = module.classify_path("scripts/report_hsd_generated_output_pollution_v1.py")
    assert source["classification"] == "source_or_reviewed_repo_file"
    assert source["safe_delete_candidate"] is False


def test_generated_output_pollution_report_builds_delete_plan_preview() -> None:
    module = load_module()
    report = module.build_report_from_paths([
        "outputs/latest/foo.txt",
        "run_history/2026-06-17/foo.csv",
        "config/hsd_expected_games_v5.csv",
        "scripts/example.py",
    ])

    assert report["tracked_generated_output_count"] == 2
    assert report["review_required_generated_like_count"] == 1
    assert report["status"] == "generated_output_cleanup_needed"
    assert any("outputs/latest/foo.txt" in command for command in report["delete_plan_preview_commands"])
    assert all("config/hsd_expected_games_v5.csv" not in command for command in report["delete_plan_preview_commands"])


def test_phase2c_gitignore_blocks_new_generated_outputs() -> None:
    text = GITIGNORE.read_text(encoding="utf-8")
    required_patterns = [
        "/outputs/latest/",
        "/run_history/",
        "/results_run_history/",
        "/repo_state_v3.json",
        "/v4_source_truth_guard.json",
        "/generated_output_pollution_v1.json",
        "/womens_sports_articles.csv",
        "__pycache__/",
    ]
    for pattern in required_patterns:
        assert pattern in text


def test_phase2c_generated_output_audit_is_wired_into_sanity_workflow() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Run V4 generated output pollution audit" in workflow
    assert "python scripts/report_hsd_generated_output_pollution_v1.py" in workflow
    assert "generated_output_pollution_v1.json" in workflow
    assert "generated_output_pollution_v1.md" in workflow
    assert "tests/test_v4_phase2c_generated_output_control.py" in workflow
