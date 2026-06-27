from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prepare_hsd_womens_soccer_logo_source_review_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_hsd_womens_soccer_logo_source_review_intake_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_source_review_intake_holds_rows_and_creates_dirs(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)

    contact_rows = [
        {
            "scope_id": "nwsl",
            "league_id": "nwsl",
            "entity_type": "team",
            "entity_id": "angel_city_fc",
            "display_name": "Angel City FC",
            "local_logo_path": "assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png",
            "current_source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/index",
            "official_source_candidate": "https://www.nwslsoccer.com/teams/angel-city-fc/index",
            "current_approval_status": "not_approved",
            "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
        },
        {
            "scope_id": "europe_top_flight",
            "league_id": "wsl_england",
            "entity_type": "team",
            "entity_id": "arsenal_women",
            "display_name": "Arsenal Women",
            "local_logo_path": "assets/leagues/womens_soccer/europe_top_flight/wsl_england/teams/arsenal_women/logo.png",
            "official_source_candidate": "https://www.arsenal.com/women",
            "current_approval_status": "not_approved",
            "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
        },
    ]

    rows, report = module.prepare_rows(
        contact_rows,
        [],
        groups=set(),
        scopes={"nwsl"},
        leagues=set(),
        reviewed_by="Mike",
        reviewed_at_local="2026-06-27 10:00 local",
        overwrite=False,
        create_dirs=True,
    )

    assert report["prepared_rows"] == 1
    assert report["created_local_logo_directories"] == 2
    assert report["approval_state_changed"] is False
    assert report["asset_files_created"] is False
    assert rows[0]["operator_decision"] == "hold_for_more_evidence"
    assert rows[0]["source_reviewed"] == "yes"
    assert rows[0]["identity_match"] == "yes"
    assert rows[0]["source_url_to_record"] == "https://www.nwslsoccer.com/teams/angel-city-fc/index"
    assert rows[0]["registry_action"] == "hold_no_registry_state_change_until_local_logo_asset_exists"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[1]["operator_decision"] == ""
    assert (tmp_path / "assets/leagues/womens_soccer/nwsl/teams/angel_city_fc").exists()
    assert (tmp_path / "assets/leagues/womens_soccer/europe_top_flight/wsl_england/teams/arsenal_women").exists()
    assert not (tmp_path / "assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png").exists()
