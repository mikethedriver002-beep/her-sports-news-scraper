from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase7_wrapper_preserves_phase6m_and_patches_underlying_renderer():
    text = (ROOT / "scripts" / "generate_hsd_template_renderer_v5_phase7.py").read_text(encoding="utf-8")
    assert "import generate_hsd_template_renderer_v4_phase6m as phase6m" in text
    assert 'phase6m._ORIGINALS["render_tonight"] = _editorial_underlying_render' in text
    assert "v5.0-phase7-multisport-editorial-engine" in text
    assert "phase7_editorial_quality_status" in text
    assert "auto_publish" not in text.lower() or "auto-publish blocks remain active" in text


def test_live_gate_requires_phase7_reports_and_keeps_cross_sport_review_only():
    text = (ROOT / "scripts" / "validate_hsd_live_post_ready_v5_phase7.py").read_text(encoding="utf-8")
    assert "phase7_event_packets_report.json" in text
    assert "phase7_multisport_renderer_report.json" in text
    assert "phase7_editorial_quality_report.json" in text
    assert '"phase7_cross_sport_handoff_allowed": False' in text
    assert 'report["production_cutover_allowed"] = False' in text
    assert 'report["auto_publish_allowed"] = False' in text
