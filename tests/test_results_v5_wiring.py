from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def test_independent_wnba_schedule_verifier_is_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/verify_hsd_wnba_schedule_independent_v5.py")
    assert "python scripts/verify_hsd_wnba_schedule_independent_v5.py" in workflow
    assert "independent_schedule_verification_v5.json" in workflow
    assert "independent_schedule_verification_v5.md" in workflow
    assert "v5.1-independent-wnba-schedule-verification-inconclusive-safe" in script
    assert "stats.wnba.com" in script
    assert "independent_source_unavailable" in script
    assert "verification_inconclusive" in script
    line = next(line for line in workflow.splitlines() if "verify_hsd_wnba_schedule_independent_v5.py" in line)
    assert line.index("generate_hsd_expected_games_v5.py") < line.index("verify_hsd_wnba_schedule_independent_v5.py")


def test_multisport_review_modules_are_wired_and_review_only() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/generate_hsd_multisport_results_modules_v5.py")
    lite = read("generate_hsd_pipeline_review_lite_v1.py")
    assert "python scripts/generate_hsd_multisport_results_modules_v5.py" in workflow
    assert "multisport_results_observations_v5.csv" in workflow
    assert "multisport_results_modules_v5.md" in workflow
    assert "v5.0-multisport-review-first" in script
    assert "review_only" in script
    assert "nwsl_soccer" in script
    assert "tennis_wta" in script
    assert "lpga_golf" in script
    assert "multisport_results_observations_v5.csv" in lite
    assert "hsd-pipeline-review-lite-v3.8.0-results-v5-multisport-review" in lite
