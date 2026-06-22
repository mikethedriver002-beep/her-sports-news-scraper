from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def core():
    return load_module(ROOT / "scripts" / "hsd_asset_assurance_core.py", "phase6m_core")


def test_missing_team_logo_generates_decodable_hsd_badge(tmp_path: Path):
    module = core()
    result = module.resolve_team_asset(
        sport_id="wnba",
        entity_id="test_team",
        display_name="Test Team",
        exact_path=None,
        output_root=tmp_path,
        primary_hex="#123456",
        secondary_hex="#010203",
    )
    assert result["resolution_mode"] == "hsd_team_badge"
    assert result["render_safe"] is True
    assert result["live_ready_pre_human"] is False
    assert result["requires_asset_visual_approval"] is True
    assert module.image_decodable(Path(result["resolved_path"]))


def test_decodable_exact_logo_remains_exact(tmp_path: Path):
    module = core()
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (128, 128), (20, 30, 40, 255)).save(logo)
    result = module.resolve_team_asset(
        sport_id="wnba",
        entity_id="exact_team",
        display_name="Exact Team",
        exact_path=logo,
        output_root=tmp_path / "out",
    )
    assert result["resolution_mode"] == "approved_logo"
    assert result["live_ready_pre_human"] is True


def test_undecodable_file_is_replaced_by_badge(tmp_path: Path):
    module = core()
    broken = tmp_path / "bad.png"
    broken.write_text("this is not an image", encoding="utf-8")
    result = module.resolve_team_asset(
        sport_id="nwsl",
        entity_id="broken_team",
        display_name="Broken Team",
        exact_path=broken,
        output_root=tmp_path / "out",
    )
    assert result["resolution_mode"] == "hsd_team_badge"
    assert module.image_decodable(Path(result["resolved_path"]))


def test_missing_player_routes_to_non_player_team_spotlight():
    module = core()
    result = module.resolve_player_asset(None, requested=True, team_name="Dallas Wings")
    assert result["resolution_mode"] == "team_spotlight_fallback"
    assert result["render_safe"] is True
    assert result["live_ready_pre_human"] is True
    assert "non_player" in result["reason"]


def test_fixture_player_stays_review_only(tmp_path: Path):
    module = core()
    image = tmp_path / "fixture.png"
    Image.new("RGB", (100, 100), (20, 20, 20)).save(image)
    result = module.resolve_player_asset(
        {"name": "Fixture Player", "path": image.as_posix(), "fixture_only": "true"},
        requested=True,
    )
    assert result["resolution_mode"] == "fixture_reference_asset"
    assert result["render_safe"] is True
    assert result["live_ready_pre_human"] is False


def test_assurance_item_allows_hash_review_badge_lane():
    module = core()
    result = module.assurance_from_item({
        "team_logo_modes": "approved_logo;hsd_team_badge",
        "team_logo_count": 1,
        "module_mode": "watch_point",
        "placeholder_layer_count": 0,
        "zone_overflow_count": 0,
        "fixture_only_player_asset": "false",
    })
    assert result["asset_render_safe"] == "true"
    assert result["asset_live_candidate_eligible"] == "true"
    assert result["asset_live_ready_pre_human"] == "false"
    assert result["asset_release_lane"] == "hsd_badge_review"


def test_assurance_item_accepts_team_spotlight_route():
    module = core()
    result = module.assurance_from_item({
        "team_logo_modes": "approved_logo;approved_logo",
        "module_mode": "team_spotlight_fallback",
        "requested_module_mode": "player",
        "asset_assurance_player_mode": "team_spotlight_fallback",
        "placeholder_layer_count": 0,
        "zone_overflow_count": 0,
        "fixture_only_player_asset": "false",
    })
    assert result["asset_render_safe"] == "true"
    assert result["asset_release_lane"] == "team_spotlight_review"
    assert result["asset_live_candidate_eligible"] == "true"


def test_multisport_catalog_has_required_coverage():
    catalog = json.loads((ROOT / "config" / "graphics" / "v4" / "asset_assurance" / "sports_catalog_v1.json").read_text(encoding="utf-8"))
    sport_ids = {row["sport_id"] for row in catalog["sports"]}
    assert {"wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"} <= sport_ids
    active = [row for row in catalog["sports"] if row["integration_status"] == "active_renderer"]
    assert [row["sport_id"] for row in active] == ["wnba"]
