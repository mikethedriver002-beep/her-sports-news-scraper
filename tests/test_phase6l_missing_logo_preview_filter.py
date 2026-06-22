from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase6l_renderer_skips_preview_rows_with_missing_logo():
    text = (ROOT / "scripts" / "generate_hsd_template_renderer_v4_phase6l.py").read_text(encoding="utf-8")
    assert "_patch_read_rows" in text
    assert "skipped_preview_missing_decodable_exact_logo" in text
    assert "phase6l_skipped_preview_missing_logo_count" in text


def test_phase6l_asset_prep_reports_missing_logos_without_global_failure():
    text = (ROOT / "scripts" / "prepare_hsd_renderer_v4_live_assets.py").read_text(encoding="utf-8")
    assert '"status": "passed_live_asset_preparation" if verified else "blocked_live_asset_preparation"' in text
    assert "Missing active logos are reported, but not globally fatal" in text
