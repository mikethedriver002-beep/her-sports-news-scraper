from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def test_independent_wnba_schedule_verifier_is_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/verify_hsd_wnba_schedule_independent_v5.py")
    assert "python scripts/verify_hsd_wnba_schedule_independent_v5.py" in workflow
    assert "independent_schedule_verification_v5.json" in workflow
    assert "independent_schedule_verification_v5.md" in workflow
    assert "v5.0-independent-wnba-schedule-verification" in script
    assert "stats.wnba.com" in script
    line = next(line for line in workflow.splitlines() if "verify_hsd_wnba_schedule_independent_v5.py" in line)
    assert line.index("generate_hsd_expected_games_v5.py") < line.index("verify_hsd_wnba_schedule_independent_v5.py")
