from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "fetch_hsd_womens_soccer_nwsl_roster_candidates_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_hsd_womens_soccer_nwsl_roster_candidates_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_nwsl_roster_candidate_builder_records_metadata_without_assets(monkeypatch) -> None:
    module = load_module()

    def fake_fetch_json(url: str) -> dict:
        assert "roster" in url
        return {
            "players": [
                {
                    "playerId": "nwsl::Football_Player::angel-001",
                    "providerId": "1001",
                    "mediaFirstName": "Alyssa",
                    "mediaLastName": "Thompson",
                    "playerStatus": "Active",
                },
                {
                    "playerId": "nwsl::Football_Player::angel-002",
                    "providerId": "1002",
                    "displayName": "Claire Emslie",
                    "playerStatus": "Active",
                },
            ]
        }

    monkeypatch.setattr(module, "fetch_json", fake_fetch_json)
    rows, warnings = module.build_player_rows(
        [
            {
                "team_id": "angel_city_fc",
                "league_id": "nwsl",
                "nwsl_roster_url": "https://www.nwslsoccer.com/teams/nwsl::Football_Team::angel-city/roster",
            }
        ],
        season_id="season-test",
    )

    assert warnings == []
    assert len(rows) == 2
    assert rows[0]["team_id"] == "angel_city_fc"
    assert rows[0]["display_name"] == "Alyssa Thompson"
    assert rows[0]["manual_review_status"] == "identity_source_review_required"
    assert rows[0]["asset_registry_status"] == "candidate_layer_only_no_asset_write"
    assert rows[0]["approval_status"] == "not_approved"
    assert "no image download" in rows[0]["notes"]
