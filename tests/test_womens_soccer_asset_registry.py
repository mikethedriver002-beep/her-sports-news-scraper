from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_hsd_womens_soccer_asset_registry_v1 import REQUIRED_NWSL_TEAMS, evaluate


def test_womens_soccer_registry_is_review_only_and_covers_nwsl() -> None:
    report = evaluate(ROOT)
    assert report["status"] == "passed_womens_soccer_review_scaffold"
    assert report["team_count"] == len(REQUIRED_NWSL_TEAMS)
    assert report["required_team_count"] == 16
    assert report["player_count"] == 0
    assert report["auto_download_allowed"] is False
    assert report["auto_approval_allowed"] is False
    assert report["render_enabled"] is False
    assert report["publish_ready"] is False
    assert not report["blockers"]
    assert "players_csv_header_only_manual_intake" in report["warnings"]


def test_womens_soccer_registry_does_not_wire_renders_or_paid_sources() -> None:
    base = ROOT / "data" / "asset_registry" / "womens_soccer" / "nwsl"
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(base.glob("*.csv")))
    forbidden = [
        ",true,approved",
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
