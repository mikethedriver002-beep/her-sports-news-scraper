from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DIRTY_SCRIPT = REPO / "scripts" / "report_hsd_dirty_tree_v1.py"
POLLUTION_SCRIPT = REPO / "scripts" / "report_hsd_generated_output_pollution_v1.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"
GITIGNORE = REPO / ".gitignore"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dirty_tree_classifier_separates_assets_generated_and_source() -> None:
    module = load_module(DIRTY_SCRIPT, "report_hsd_dirty_tree_v1")

    assert module.classify_dirty_path("assets/leagues/wnba/athletes/player/headshot.png.approved") == "asset_approval_marker_mutation"
    assert module.classify_dirty_path("data/asset_registry/wnba/team_logos.csv") == "wnba_asset_registry_mutation"
    assert module.classify_dirty_path("hsd_pipeline_lite_review/files/repo_state_v3.md") == "generated_output_dir_or_archive"
    assert module.classify_dirty_path("asset_run_history/2026-06-08/0352_UTC/graphics_qa_manifest.json") == "generated_output_dir_or_archive"
    assert module.classify_dirty_path("operator/inbox/manual_workflow_inbox_template_v1.csv") == "generated_output_dir_or_archive"
    assert module.classify_dirty_path("assignment_handoff_manifest.json") == "generated_root_handoff_or_report"
    assert module.classify_dirty_path("scripts/new_source.py") == "source_or_test_mutation"


def test_dirty_tree_report_counts_status_categories() -> None:
    module = load_module(DIRTY_SCRIPT, "report_hsd_dirty_tree_v1")
    status = """ M assets/leagues/wnba/athletes/player/headshot.png.approved
 M data/asset_registry/wnba/team_logos.csv
 D hsd_pipeline_lite_review/files/old.md
?? asset_run_history/2026-06-08/0352_UTC/graphics_qa_manifest.json
?? operator/inbox/social_rumor_inbox_template_v1.csv
?? assignment_handoff_manifest.json
 M scripts/source.py
?? mystery.tmp
"""
    report = module.build_report_from_status(status)

    assert report["dirty_entry_count"] == 8
    assert report["asset_or_registry_dirty_count"] == 2
    assert report["generated_dirty_count"] == 4
    assert report["source_or_test_mutation_count"] == 1
    assert report["unclassified_dirty_count"] == 1
    assert report["publish_gate"] == "source_review_required"


def test_pollution_classifier_knows_phase2e_and_phase2f_residual_outputs() -> None:
    module = load_module(POLLUTION_SCRIPT, "report_hsd_generated_output_pollution_v1")

    assert module.classify_path("hsd_pipeline_lite_review/files/repo_state_v3.md")["safe_delete_candidate"] is True
    assert module.classify_path("asset_run_history/2026-06-08/0352_UTC/graphics_qa_manifest.json")["safe_delete_candidate"] is True
    assert module.classify_path("operator/inbox/manual_workflow_inbox_template_v1.csv")["safe_delete_candidate"] is True
    assert module.classify_path("assignment_handoff_manifest.json")["safe_delete_candidate"] is True
    assert module.classify_path("studio_bundle_packets.md")["safe_delete_candidate"] is True
    assert module.classify_path("config/hsd_expected_games_v5.csv")["safe_delete_candidate"] is False
    assert module.classify_path("scripts/report_hsd_dirty_tree_v1.py")["classification"] == "source_or_reviewed_repo_file"


def test_phase2e_gitignore_covers_residual_outputs() -> None:
    text = GITIGNORE.read_text(encoding="utf-8")
    required_patterns = [
        "/hsd_pipeline_lite_review/",
        "/asset_run_history/",
        "/operator/inbox/",
        "/dirty_tree_v1.json",
        "/assignment_*.json",
        "/mermaid_*.md",
        "/studio_*.csv",
        "/rendered_handoff_zips/",
        "/runs/",
    ]
    for pattern in required_patterns:
        assert pattern in text


def test_phase2e_dirty_tree_audit_is_wired_into_sanity_workflow() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Run V4 dirty tree category audit" in workflow
    assert "python scripts/report_hsd_dirty_tree_v1.py" in workflow
    assert "dirty_tree_v1.json" in workflow
    assert "dirty_tree_v1.md" in workflow
    assert "tests/test_v4_phase2e_dirty_tree_hygiene.py" in workflow
