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


def test_hsd_quality_graphics_renderer_is_wired_and_packaged() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/generate_hsd_quality_graphics_renderer_v1.py")
    zipper = read("scripts/package_hsd_quality_graphics_v1.py")
    assert "python scripts/generate_hsd_quality_graphics_renderer_v1.py" in workflow
    assert "python scripts/package_hsd_quality_graphics_v1.py" in workflow
    assert "outputs/latest/HSD_QUALITY_GRAPHICS/**" in workflow
    assert "hsd_quality_graphics.zip" in workflow
    assert "hsd_quality_graphics_manifest.csv" in workflow
    assert "v1.0-hsd-quality-graphics-renderer" in script
    assert "v1.0-package-hsd-quality-graphics" in zipper
    assert "No player images, no fake athletes, no invented stats" in script
    assert "ig_feed" in script and "threads" in script and "stories" in script
    assert "results_contract_v2.csv" in script
    assert "daily_slate_plan.csv" in script


def test_graphics_template_factory_is_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/generate_hsd_graphics_template_factory_v1.py")
    assert "python scripts/generate_hsd_graphics_template_factory_v1.py" in workflow
    assert "outputs/latest/HSD_TEMPLATE_FACTORY/**" in workflow
    assert "v1.0-hsd-graphics-template-factory" in script
    assert "Tonight in the W" in script
    assert "Last Night in the W" in script
    assert "Game Recap / Final Score" in script
    assert "Daily Debrief" in script
    assert "Women’s Soccer / NWSL / USWNT" in script
    assert "LPGA / Golf" in script
    assert "Tennis / WTA" in script
    assert "The renderer should become a compiler for approved templates" in script
