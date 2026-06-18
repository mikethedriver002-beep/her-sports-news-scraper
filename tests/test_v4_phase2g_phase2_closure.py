from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_phase2_closure_v1.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("hsd_phase2_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase2g_protects_source_and_config_from_root_wildcards() -> None:
    module = load_module()
    assert module.classify_tracked(
        "config/graphics_rendered_qa_policy_v2.json", set()
    ) is None
    assert module.classify_tracked("studio_bridge_v1_3_notes.md", set()) is None
    assert module.classify_tracked(
        "config/hsd_expected_games_v5.csv", set()
    ) is None


def test_phase2g_covers_generated_directories_and_root_outputs() -> None:
    module = load_module()
    cases = {
        "studio_run_history/2026-06-10/run.md": "generated_top_level",
        "news_run_history/2026-06-10/run.md": "generated_top_level",
        "studio_dashboard/index.html": "generated_top_level",
        "asset_desk_dashboard/index.html": "generated_top_level",
        "visual_upgrade_dashboard/index.html": "generated_top_level",
        "operator/inbox/template.csv": "generated_prefix",
        "team_assets.csv": "generated_root_exact",
        "launch_integration_points.csv": "generated_root_exact",
        "graphics_production_specs.json": "generated_root_exact",
    }
    for path, expected in cases.items():
        assert module.classify_tracked(path, set()) == expected


def test_phase2g_extracts_static_root_write_targets(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    script = tmp_path / "generator.py"
    script.write_text(
        'write_csv("new_output.csv", [], [])\n'
        'Path("new_report.md").write_text("Generated: 2026-06-18")\n'
        'Path("config/source_policy.json").write_text("{}")\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    outputs = module.extract_static_outputs(["generator.py"])
    assert "new_output.csv" in outputs
    assert "new_report.md" in outputs
    assert "config/source_policy.json" not in outputs
    assert module.classify_tracked(
        "new_output.csv", outputs
    ) == "static_write_target"


def test_phase2g_dirty_tree_blocks_source_but_not_asset_runtime() -> None:
    module = load_module()
    assert module.classify_dirty("scripts/source.py") == "source_test_workflow"
    assert module.classify_dirty(
        "config/source_policy.json"
    ) == "config_source"
    assert module.classify_dirty(
        "data/asset_registry/wnba/team_logos.csv"
    ) == "asset_registry_runtime"
    assert module.classify_dirty(
        "assets/leagues/wnba/athletes/a/headshot.png.approved"
    ) == "asset_runtime"


def test_phase2g_workflow_is_wired_for_strict_closure() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "Run V4 Phase 2 closure gate" in workflow
    assert (
        "python scripts/report_hsd_phase2_closure_v1.py --audit --strict"
        in workflow
    )
    assert "tests/test_v4_phase2g_phase2_closure.py" in workflow
    assert "phase2_closure_v1.json" in workflow
    assert "phase2_closure_v1.md" in workflow


def test_phase2g_script_self_test() -> None:
    module = load_module()
    assert module.self_test() == 0
