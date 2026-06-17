from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def test_template_renderer_v25_is_active_handoff() -> None:
    map_script = read("scripts/generate_hsd_template_render_map_v1.py")
    renderer = read("scripts/generate_hsd_template_renderer_v2_5.py")
    assert "v1.3-hsd-template-render-map-v2-5-handoff" in map_script
    assert "scripts/generate_hsd_template_renderer_v2_5.py" in map_script
    assert "v2.5-hsd-quality-tonight-logo-integrity-review-only" in renderer
    assert "Template Renderer v2.5 compile proof" in renderer
    assert "verified registry logo loaded" in renderer
    assert "warning_fallback" in renderer
    assert "logo_panel" in renderer
    assert "WATCH POINT" in renderer
    assert "HSD-template-renderer-v2.5" in renderer


def test_template_renderer_v25_outputs_review_artifacts() -> None:
    renderer = read("scripts/generate_hsd_template_renderer_v2_5.py")
    assert "outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v2" in renderer
    assert "hsd_template_renderer_v2_logo_audit.json" in renderer
    assert "hsd_template_renderer_v2_logo_audit.csv" in renderer
    assert "review_only" in renderer
    assert "Human review required before publishing" in renderer
