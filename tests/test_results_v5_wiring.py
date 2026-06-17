from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def test_independent_wnba_schedule_verifier_is_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/verify_hsd_wnba_schedule_independent_v5.py")
    assert "python scripts/verify_hsd_wnba_schedule_independent_v5.py" in workflow
    assert "independent_schedule_verification_v5.json" in workflow
    assert "v5.1-independent-wnba-schedule-verification-inconclusive-safe" in script
    assert "stats.wnba.com" in script
    assert "verification_inconclusive" in script


def test_multisport_review_modules_are_wired_and_review_only() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/generate_hsd_multisport_results_modules_v5.py")
    lite = read("generate_hsd_pipeline_review_lite_v1.py")
    assert "python scripts/generate_hsd_multisport_results_modules_v5.py" in workflow
    assert "v5.0-multisport-review-first" in script
    assert "review_only" in script
    assert "nwsl_soccer" in script
    assert "tennis_wta" in script
    assert "lpga_golf" in script
    assert "hsd-pipeline-review-lite-v3.8.0-results-v5-multisport-review" in lite


def test_template_law_and_top_priority_specs_exist() -> None:
    required_paths = [
        "docs/HSD_GRAPHICS_LAW_V1.md",
        "docs/HSD_GRAPHICS_LAW_V1_LPGA_GOLF.md",
        "docs/HSD_REALITY_CHECK_PROMPTS.md",
        "config/graphics/brand_policy_v1.json",
        "config/graphics/template_registry_v1.json",
        "config/graphics/template_render_mapping_v1.json",
        "scripts/generate_hsd_graphics_template_factory_v1.py",
        "scripts/generate_hsd_template_render_map_v1.py",
        "scripts/generate_hsd_template_renderer_v2.py",
        "scripts/generate_hsd_template_renderer_v2_5.py",
        "config/graphics/templates/game_recap_final_score_a_v1.json",
        "config/graphics/templates/game_recap_final_score_b_v1.json",
        "config/graphics/templates/game_recap_final_score_c_story_v1.json",
        "config/graphics/templates/tonight_in_the_w_a_v1.json",
        "config/graphics/templates/last_night_in_the_w_a_v1.json",
        "config/graphics/templates/last_night_in_the_w_b_story_v1.json",
        "config/graphics/templates/last_night_in_the_w_c_carousel_v1.json",
        "config/graphics/templates/daily_debrief_a_v1.json",
        "config/graphics/templates/daily_debrief_b_summary_v1.json",
        "config/graphics/templates/daily_debrief_c_story_v1.json",
        "config/graphics/templates/womens_soccer_match_story_a_v1.json",
        "config/graphics/templates/womens_soccer_match_story_b_v1.json",
        "config/graphics/templates/womens_soccer_match_story_c_story_v1.json",
        "config/graphics/templates/tennis_wta_result_a_v1.json",
        "config/graphics/templates/tennis_wta_result_b_v1.json",
        "config/graphics/templates/tennis_wta_result_c_story_v1.json",
        "config/graphics/templates/lpga_golf_winner_leaderboard_a_v1.json",
        "config/graphics/templates/lpga_golf_winner_leaderboard_b_v1.json",
        "config/graphics/templates/lpga_golf_winner_leaderboard_c_story_v1.json",
    ]
    for path in required_paths:
        assert Path(path).exists(), path


def test_template_renderer_v25_is_active_and_review_only() -> None:
    map_script = read("scripts/generate_hsd_template_render_map_v1.py")
    renderer = read("scripts/generate_hsd_template_renderer_v2_5.py")
    requirements = read("requirements.txt")
    assert "v1.3-hsd-template-render-map-v2-5-handoff" in map_script
    assert "scripts/generate_hsd_template_renderer_v2_5.py" in map_script
    assert "v2.5-hsd-quality-tonight-logo-integrity-review-only" in renderer
    assert "Template Renderer v2.5 compile proof" in renderer
    assert "verified registry logo loaded" in renderer
    assert "fallback_logo_warnings" in renderer
    assert "logo_panel" in renderer
    assert "WATCH POINT" in renderer
    assert "Human review required before publishing" in renderer
    assert "CairoSVG" in requirements


def test_quality_renderer_packaging_still_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    renderer = read("scripts/generate_hsd_quality_graphics_renderer_v1.py")
    zipper = read("scripts/package_hsd_quality_graphics_v1.py")
    assert "python scripts/generate_hsd_quality_graphics_renderer_v1.py" in workflow
    assert "python scripts/package_hsd_quality_graphics_v1.py" in workflow
    assert "outputs/latest/HSD_QUALITY_GRAPHICS/**" in workflow
    assert "v1.0-hsd-quality-graphics-renderer" in renderer
    assert "v1.0-package-hsd-quality-graphics" in zipper
