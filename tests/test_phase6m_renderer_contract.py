from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase6m_renderer_restores_rows_and_has_safe_fallback_routes():
    text = (ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6m.py").read_text(encoding="utf-8")
    assert 'phase6l._ORIGINALS.get("base_read_rows")' in text
    assert "hsd_team_badge" in text
    assert "team_spotlight_fallback" in text
    assert "downgraded_player_to_non_player_team_spotlight" in text
    assert "phase6m_input_rows_skipped_for_assets" in text
    assert "asset_fallback_review_cue" in text


def test_phase6m_live_gate_keeps_hash_bound_human_review():
    text = (ROOT / "scripts" / "validate_hsd_live_post_ready_v4_phase6m.py").read_text(encoding="utf-8")
    assert "phase6m_hsd_badge_requires_explicit_hash_bound_human_approval" in text
    assert "production_cutover_allowed" in text
    assert "auto_publish_allowed" in text
    assert "asset_live_candidate_eligible" in text
    assert "asset_fallback_review_cue" in text


def test_phase6m_asset_assurance_report_surfaces_fallback_review_cues():
    text = (ROOT / "scripts" / "validate_hsd_asset_assurance_v1.py").read_text(encoding="utf-8")
    assert "asset_fallback_review_cue" in text
    assert "Fallback Review Cues" in text
    assert "Human asset review remains required" in text


def test_phase6m_policy_keeps_publish_safeties_closed():
    policy = json.loads((ROOT / "config" / "graphics" / "v4" / "live_post_ready" / "live_post_ready_policy_phase6m_v4.json").read_text(encoding="utf-8"))
    assert policy["phase6m_asset_assurance_required"] is True
    assert policy["phase6m_hsd_badge_candidate_allowed"] is True
    assert policy["human_visual_approval_required"] is True
    assert policy["production_cutover_allowed"] is False
    assert policy["auto_publish_allowed"] is False


def test_phase6m_workflow_runs_asset_preflight_and_post_render_gate():
    workflow = (ROOT / ".github" / "workflows" / "hsd-v4-phase6m-asset-assurance-core.yml").read_text(encoding="utf-8")
    assert "build_hsd_asset_assurance_v1.py" in workflow
    assert "generate_hsd_template_renderer_v4_phase6m.py" in workflow
    assert "validate_hsd_asset_assurance_v1.py" in workflow
    assert "validate_hsd_live_post_ready_v4_phase6m.py" in workflow
    assert "outputs/latest/HSD_ASSET_ASSURANCE/**" in workflow


def test_phase6m_is_multisport_core_not_wnba_only():
    doc = (ROOT / "docs" / "HSD_PHASE6M_ASSET_ASSURANCE_CORE.md").read_text(encoding="utf-8")
    for label in ["WNBA", "NWSL", "USWNT", "tennis", "LPGA", "softball", "volleyball"]:
        assert label.lower() in doc.lower()
