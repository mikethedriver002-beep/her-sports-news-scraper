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


def test_graphics_template_factory_and_law_files_are_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/generate_hsd_graphics_template_factory_v1.py")
    law = read("docs/HSD_GRAPHICS_LAW_V1.md")
    lpga_law = read("docs/HSD_GRAPHICS_LAW_V1_LPGA_GOLF.md")
    prompts = read("docs/HSD_GRAPHICS_TEMPLATE_MASTER_BATCH_PROMPTS_V1.md")
    assert "python scripts/generate_hsd_graphics_template_factory_v1.py" in workflow
    assert "outputs/latest/HSD_TEMPLATE_FACTORY/**" in workflow
    assert "v1.3-hsd-graphics-template-factory-with-render-map" in script
    assert "public_logo_rule.md" in script
    assert "config_graphics_snapshot" in script
    assert "render_mapping" in script
    assert "generate_hsd_template_render_map_v1.py" in script
    assert "HSD_GRAPHICS_LAW_V1" in script
    assert "official compact HSD watermark/bug only" in script
    assert "Do not use the full HSD + HER SPORTS DAILY lockup" in script
    assert "The renderer should become a compiler for approved templates" in script
    assert "HSD Graphics Law v1" in law
    assert "The renderer is a compiler, not a designer" in law
    assert "Variant A: Logo-first final score" in law
    assert "Variant B: Approved-player-photo final score" in law
    assert "Variant C: Story/Reels quick final" in law
    assert "Last Night in the W template law" in law
    assert "Daily Debrief template law" in law
    assert "Women’s Soccer / NWSL / USWNT template law" in law
    assert "Tennis / WTA template law" in law
    assert "LPGA / Golf template law" in lpga_law
    assert "Variant A: Winner / Champion Card" in lpga_law
    assert "Variant B: Leaderboard / Standings Update Card" in lpga_law
    assert "Variant C: Story / Vertical Golf Update" in lpga_law
    assert "official compact HSD badge only" in prompts
    assert "GAME RECAP / FINAL SCORE" in prompts
    assert "TONIGHT IN THE W" in prompts
    assert "LAST NIGHT IN THE W" in prompts
    assert "THE DAILY DEBRIEF" in prompts
    assert "LPGA / GOLF" in prompts


def test_template_specs_are_present_for_top_priorities() -> None:
    for path in [
        "config/graphics/brand_policy_v1.json",
        "config/graphics/template_registry_v1.json",
        "config/graphics/template_render_mapping_v1.json",
        "scripts/generate_hsd_template_render_map_v1.py",
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
    ]:
        assert Path(path).exists(), path


def test_template_render_mapping_is_review_only() -> None:
    config = read("config/graphics/template_render_mapping_v1.json")
    script = read("scripts/generate_hsd_template_render_map_v1.py")
    assert "hsd-template-render-mapping-v1" in config
    assert "production_auto_render_allowed" in config
    assert "false" in config.lower()
    assert "game_recap_final_score.a.v1" in config
    assert "game_recap_final_score.c.story.v1" in config
    assert "tonight_in_the_w.a.v1" in config
    assert "last_night_in_the_w.a.v1" in config
    assert "last_night_in_the_w.b.story.v1" in config
    assert "last_night_in_the_w.c.carousel.v1" in config
    assert "v1.0-hsd-template-render-map-review-only" in script
    assert "review-only render mapping" in script
    assert "outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping" in script
