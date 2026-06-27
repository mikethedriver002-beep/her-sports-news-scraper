from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_hsd_womens_soccer_asset_registry_v1 import (
    REQUIRED_ARKEMA_PREMIERE_LIGUE_TEAMS,
    REQUIRED_EUROPE_TOP_FLIGHT_LEAGUES,
    REQUIRED_FRAUEN_BUNDESLIGA_TEAMS,
    REQUIRED_LIGA_F_TEAMS,
    REQUIRED_NWSL_TEAMS,
    REQUIRED_SERIE_A_WOMEN_TEAMS,
    REQUIRED_WSL_TEAMS,
    evaluate,
)


def test_womens_soccer_registry_is_review_only_and_covers_nwsl() -> None:
    report = evaluate(ROOT)
    assert report["status"] == "passed_womens_soccer_review_scaffold"
    assert report["team_count"] == len(REQUIRED_NWSL_TEAMS)
    assert report["required_team_count"] == 16
    assert report["player_count"] == 0
    assert report["source_url_count"] == 87
    assert report["europe_top_flight_league_count"] == len(REQUIRED_EUROPE_TOP_FLIGHT_LEAGUES)
    assert report["europe_top_flight_required_league_count"] == 5
    assert report["europe_top_flight_wsl_team_count"] == len(REQUIRED_WSL_TEAMS)
    assert report["europe_top_flight_required_wsl_team_count"] == 12
    assert report["europe_top_flight_liga_f_team_count"] == len(REQUIRED_LIGA_F_TEAMS)
    assert report["europe_top_flight_required_liga_f_team_count"] == 16
    assert report["europe_top_flight_frauen_bundesliga_team_count"] == len(REQUIRED_FRAUEN_BUNDESLIGA_TEAMS)
    assert report["europe_top_flight_required_frauen_bundesliga_team_count"] == 14
    assert report["europe_top_flight_serie_a_women_team_count"] == len(REQUIRED_SERIE_A_WOMEN_TEAMS)
    assert report["europe_top_flight_required_serie_a_women_team_count"] == 12
    assert report["europe_top_flight_arkema_premiere_ligue_team_count"] == len(REQUIRED_ARKEMA_PREMIERE_LIGUE_TEAMS)
    assert report["europe_top_flight_required_arkema_premiere_ligue_team_count"] == 12
    assert report["europe_top_flight_pilot_team_count"] == len(REQUIRED_WSL_TEAMS) + len(REQUIRED_LIGA_F_TEAMS) + len(REQUIRED_FRAUEN_BUNDESLIGA_TEAMS) + len(REQUIRED_SERIE_A_WOMEN_TEAMS) + len(REQUIRED_ARKEMA_PREMIERE_LIGUE_TEAMS)
    assert report["europe_top_flight_player_count"] == 0
    assert report["europe_top_flight_source_url_count"] >= 211
    assert report["europe_top_flight_asset_slot_count"] == 72
    assert report["league_source_kind_count"] == report["required_league_source_kind_count"]
    assert report["required_team_source_kind_count"] == 5
    for team_id in REQUIRED_NWSL_TEAMS:
        assert report["team_source_coverage"][team_id] == [
            "logo_review_source",
            "nwsl_roster",
            "nwsl_schedule",
            "nwsl_team_detail",
            "team_site",
        ]
    assert report["auto_download_allowed"] is False
    assert report["auto_approval_allowed"] is False
    assert report["render_enabled"] is False
    assert report["publish_ready"] is False
    assert not report["blockers"]
    assert "players_csv_header_only_manual_intake" in report["warnings"]
    assert "europe_players_csv_header_only_manual_intake" in report["warnings"]
    assert "europe_team_logo_rows_require_human_review_before_approval" not in report["warnings"]


def test_womens_soccer_registry_does_not_wire_renders_or_paid_sources() -> None:
    base = ROOT / "data" / "asset_registry" / "womens_soccer"
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(base.glob("*/*.csv")))
    forbidden = [
        "render_enabled,true",
        "publish_ready,true",
        "paid_source,true",
        "auto_download_allowed,true",
        "auto_approval_allowed,true",
    ]
    for token in forbidden:
        assert token not in text
    assert "assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png" in text
    assert "https://www.nwslsoccer.com/teams/index" in text
    assert "https://www.wslfootball.com/" in text
    assert "london_city_lionesses" in text
    assert "west_ham_united_women" in text
    assert "https://www.laliga.com/en-GB/futbol-femenino" in text
    assert "fc_barcelona" in text
    assert "real_madrid_cf" in text
    assert "dux_logrono" in text
    assert "https://frauen-bundesliga.dfb.de/google-pixel-frauen-bundesliga/ergebnisse-und-tabelle/" in text
    assert "fc_bayern_munich_women" in text
    assert "vfl_wolfsburg_women" in text
    assert "union_berlin_women" in text
    assert "juventus_women" in text
    assert "as_roma_women" in text
    assert "ternana_women" in text
    assert "ol_lyonnes" in text
    assert "paris_saint_germain_women" in text
    assert "rc_strasbourg_alsace_women" in text
    assert "europe_top_flight/wsl_england/teams/arsenal_women/logo.png" in text
    assert "logo_review_source" in text
    assert "nwsl_roster" in text
    assert "nwsl_schedule" in text
    assert "nwslsoccer_team_uuid" in text
    assert "review_required,not_approved" in text
    assert "team_logo,approved,Mike" in text
    assert "team_identity,not_approved" in text
