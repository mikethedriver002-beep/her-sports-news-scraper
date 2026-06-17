from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_v4_source_truth_guard.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"


def load_guard_module():
    spec = importlib.util.spec_from_file_location("report_hsd_v4_source_truth_guard", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_v4_source_truth_guard_flags_observation_derived_expected_games(tmp_path: Path) -> None:
    module = load_guard_module()

    write_json(
        tmp_path / "expected_games_v5_manifest.json",
        {
            "version": "v5.0-expected-games-from-observations",
            "input_file": "source_observations.csv",
            "expected_games": 8,
        },
    )
    write_json(
        tmp_path / "missing_games_alert_v5.json",
        {"summary": {"expected_fixture_file_present": True, "expected_games": 8, "matched": 8, "missing": 0}, "rows": []},
    )
    write_json(
        tmp_path / "independent_schedule_verification_v5.json",
        {
            "version": "v5.1-independent-wnba-schedule-verification-inconclusive-safe",
            "expected_games": 8,
            "independent_games": 0,
            "matched": 0,
            "missing_from_independent": 0,
            "independent_source_unavailable": 8,
            "extra_in_independent": 0,
            "source_available": False,
            "verification_inconclusive": True,
        },
    )
    write_json(
        tmp_path / "source_accuracy_v5.json",
        {"counts": {"expected_expected_games": 8, "expected_matched": 8, "expected_missing": 0}},
    )
    write_json(
        tmp_path / "results_desk_v5_manifest.json",
        {"counts": {"expected_games": 8, "missing_expected_games": 0}},
    )

    report = module.build_report(tmp_path)

    assert report["status"] == "blocked_source_truth"
    assert report["publish_gate"] == "blocked_manual_review_required"
    assert "expected_games_baseline_is_observation_derived" in report["blockers"]
    assert "independent_schedule_verification_inconclusive" in report["blockers"]
    assert report["expected_games"]["internal_completeness_status"] == "internal_consistency_only"
    assert report["independent_schedule"]["independent_slate_status"] == "inconclusive"
    assert "missing_games_zero_is_internal_consistency_only" in report["warnings"]

    assert module.main(["--repo-root", str(tmp_path)]) == 0
    assert module.main(["--repo-root", str(tmp_path), "--strict"]) == 2
    assert (tmp_path / "v4_source_truth_guard.json").exists()
    assert (tmp_path / "v4_source_truth_guard.md").exists()


def test_v4_source_truth_guard_passes_when_external_expected_and_independent_match(tmp_path: Path) -> None:
    module = load_guard_module()

    write_json(
        tmp_path / "expected_games_v5_manifest.json",
        {
            "version": "v5.2-external-expected-games",
            "input_file": "free_public_independent_schedule.csv",
            "expected_games": 2,
        },
    )
    write_json(
        tmp_path / "missing_games_alert_v5.json",
        {"summary": {"expected_fixture_file_present": True, "expected_games": 2, "matched": 2, "missing": 0}, "rows": []},
    )
    write_json(
        tmp_path / "independent_schedule_verification_v5.json",
        {
            "version": "v5.1-independent-wnba-schedule-verification-inconclusive-safe",
            "expected_games": 2,
            "independent_games": 2,
            "matched": 2,
            "missing_from_independent": 0,
            "independent_source_unavailable": 0,
            "extra_in_independent": 0,
            "source_available": True,
            "verification_inconclusive": False,
        },
    )

    report = module.build_report(tmp_path)

    assert report["status"] == "passed_source_truth_guard"
    assert report["blockers"] == []
    assert report["independent_schedule"]["independent_slate_status"] == "verified"


def test_v4_source_truth_guard_is_wired_into_sanity_workflow() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "Run V4 source truth guard" in workflow
    assert "python scripts/report_hsd_v4_source_truth_guard.py --strict" in workflow
    assert "v4_source_truth_guard.json" in workflow
    assert "v4_source_truth_guard.md" in workflow
    assert "tests/test_v4_source_truth_guards.py" in workflow

    assert "v4.0-source-truth-guard" in script
    assert "expected_games_baseline_is_observation_derived" in script
    assert "independent_schedule_verification_inconclusive" in script
    assert "network_used_by_guard" in script
