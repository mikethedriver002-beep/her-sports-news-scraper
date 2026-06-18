from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RENDERER = REPO / "scripts" / "generate_hsd_template_renderer_v3.py"
QUALITY_BUILDER = REPO / "scripts" / "build_hsd_quality_graphics_from_renderer_v3.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"


def test_renderer_v3_has_cinematic_dual_lanes() -> None:
    text = RENDERER.read_text(encoding="utf-8")
    assert "v3.1-cinematic-dual-player-lanes" in text
    assert '"logos_only"' in text
    assert '"with_players"' in text
    assert "always_render_logos_only" in text
    assert "with_players_requires_packaged_player_assets" in text
    assert "no_fake_people" in text
    assert "human_visual_approval_required" in text
    assert "hsd_template_renderer_v3_contact_sheet.jpg" in text


def test_quality_lane_is_built_from_renderer_v3() -> None:
    text = QUALITY_BUILDER.read_text(encoding="utf-8")
    assert "v1.0-quality-from-template-renderer-v3" in text
    assert "template_renderer_v3" in text
    assert '"variant"' in text
    assert '"player_assets_used"' in text
    assert '"renderer_source": "template_renderer_v3"' in text
    assert "HSD_QUALITY_GRAPHICS" in text


def test_phase5b_workflow_uses_v3_and_keeps_visual_qa() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "V5B cinematic renderer and quality outputs" in workflow
    assert "python scripts/generate_hsd_template_renderer_v3.py" in workflow
    assert "python scripts/build_hsd_quality_graphics_from_renderer_v3.py" in workflow
    assert "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v3/**" in workflow
    assert "Run V5 post-ready visual QA" in workflow
    assert "tests/test_phase5b_renderer_visual_upgrade.py" in workflow


def test_phase5b_remains_free_only() -> None:
    combined = RENDERER.read_text(encoding="utf-8") + QUALITY_BUILDER.read_text(encoding="utf-8")
    banned = ["openai", "anthropic", "serpapi", "brightdata", "scrapingbee", "paid_api"]
    for token in banned:
        assert token not in combined.lower()
