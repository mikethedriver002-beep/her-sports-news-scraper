from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = REPO / "scripts" / "merge_hsd_v4_guard_into_repo_state.py"
LOGO_SCRIPT = REPO / "scripts" / "report_hsd_template_renderer_logo_status_v1.py"
SANITY_WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"
LEGACY_WORKFLOWS = [
    REPO / ".github" / "workflows" / "results-desk.yml",
    REPO / ".github" / "workflows" / "news-scraper.yml",
    REPO / ".github" / "workflows" / "results-source-audit.yml",
]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_v4_guard_merges_into_repo_state_outputs(tmp_path: Path) -> None:
    module = load_module(BRIDGE_SCRIPT, "merge_hsd_v4_guard_into_repo_state")

    write_json(tmp_path / "repo_state_v3.json", {"overall_sanity": {"needs_review": False}})
    (tmp_path / "repo_state_v3.md").write_text(
        "# HSD Repo State + Pipeline Sanity Audit v3\n\n## Overall sanity\n- needs_review: `False`\n",
        encoding="utf-8",
    )
    write_json(
        tmp_path / "v4_source_truth_guard.json",
        {
            "version": "v4.0-source-truth-guard",
            "status": "blocked_source_truth",
            "publish_gate": "blocked_manual_review_required",
            "blockers": ["expected_games_baseline_is_observation_derived"],
            "warnings": ["missing_games_zero_is_internal_consistency_only"],
            "expected_games": {"internal_completeness_status": "internal_consistency_only"},
            "independent_schedule": {"independent_slate_status": "inconclusive", "source_available": False, "verification_inconclusive": True},
        },
    )

    assert module.main(["--repo-root", str(tmp_path)]) == 0
    merged = json.loads((tmp_path / "repo_state_v3.json").read_text(encoding="utf-8"))
    assert merged["overall_sanity"]["needs_review"] is True
    assert merged["overall_sanity"]["source_truth_blocker_count"] == 1
    assert merged["v4_source_truth_guard"]["guard_status"] == "blocked_source_truth"

    md = (tmp_path / "repo_state_v3.md").read_text(encoding="utf-8")
    assert "- needs_review: `True`" in md
    assert "## V4 source truth guard" in md
    assert "expected_games_baseline_is_observation_derived" in md


def test_template_renderer_logo_status_separates_recoverable_warning_from_active_fallback(tmp_path: Path) -> None:
    module = load_module(LOGO_SCRIPT, "report_hsd_template_renderer_logo_status_v1")

    audit = tmp_path / "logo_audit.json"
    manifest = tmp_path / "manifest.json"
    write_json(
        audit,
        {
            "rows": [
                {"team": "Washington Mystics", "team_id": "washington_mystics", "source": "local_registry", "path_or_url": "assets/logo.png", "status": "warning_fallback", "note": "local missing"},
                {"team": "Washington Mystics", "team_id": "washington_mystics", "source": "verified_remote", "path_or_url": "https://example.test/logo.svg", "status": "loaded", "note": "verified registry logo loaded"},
                {"team": "Missing Team", "team_id": "missing_team", "source": "fallback", "path_or_url": "team_name_badge", "status": "warning_fallback", "note": "real logo unavailable"},
            ]
        },
    )
    write_json(manifest, {"version": "v2.5-test", "rendered_count": 2})

    report = module.build_report(audit, manifest)
    assert report["logo_warning_rows"] == 2
    assert report["recoverable_logo_warnings"] == 1
    assert report["active_logo_fallbacks"] == 1
    assert report["effective_publish_status"] == "blocked_active_logo_fallback"
    assert "washington_mystics" in report["recoverable_warning_teams"]
    assert "missing_team" in report["active_fallback_teams"]


def test_phase2b_sanity_workflow_wiring() -> None:
    workflow = SANITY_WORKFLOW.read_text(encoding="utf-8")
    assert "renderer logo status audit" in workflow
    assert "python scripts/report_hsd_template_renderer_logo_status_v1.py" in workflow
    assert "Merge V4 guard into repo-state audit" in workflow
    assert "python scripts/merge_hsd_v4_guard_into_repo_state.py" in workflow
    assert "tests/test_v4_phase2b_repo_state_and_logo_status.py" in workflow


def test_legacy_auto_commit_workflows_are_quarantined() -> None:
    for path in LEGACY_WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        assert "workflow_dispatch:" in text, path
        assert "schedule:" not in text, path
        assert "\n  push:" not in text and "\npush:" not in text, path
        assert "git push" not in text, path
        assert "git commit" not in text, path
        assert "contents: read" in text, path
