from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_womens_soccer_logo_contact_sheet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_womens_soccer_logo_contact_sheet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_logo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (160, 120), (255, 255, 255, 0))
    for x in range(32, 128):
        for y in range(24, 96):
            image.putpixel((x, y), (42, 116, 88, 255))
    image.save(path)


def test_womens_soccer_logo_contact_sheet_builds_review_only_board(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.PROJECT_ROOT = tmp_path
    module.OUT_MD = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_contact_sheet.md"
    module.OUT_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_contact_sheet.csv"
    module.OUT_PNG = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_contact_sheet.png"
    module.OUT_INTAKE = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_review_intake.csv"
    module.OUT_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_contact_sheet.json"
    module.OUT_WALKTHROUGH_MD = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_review_walkthrough.md"
    module.OUT_WALKTHROUGH_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_review_walkthrough.csv"
    module.OUT_WALKTHROUGH_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_logo_review_walkthrough.json"
    module.REGISTRY_SCOPES = ["nwsl", "europe_top_flight"]

    logo_path = tmp_path / "assets" / "leagues" / "womens_soccer" / "nwsl" / "teams" / "angel_city_fc" / "logo.png"
    make_logo(logo_path)
    root = tmp_path / "data" / "asset_registry" / "womens_soccer"
    write_csv(
        root / "nwsl" / "leagues.csv",
        [
            {
                "league_id": "nwsl",
                "league_name": "National Women's Soccer League",
                "country": "US",
                "official_url": "https://www.nwslsoccer.com/about-the-nwsl",
                "teams_url": "https://www.nwslsoccer.com/teams/index",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            }
        ],
        ["league_id", "league_name", "country", "official_url", "teams_url", "paid_source", "auto_download_allowed", "render_enabled"],
    )
    write_csv(
        root / "nwsl" / "teams.csv",
        [
            {
                "team_id": "angel_city_fc",
                "league_id": "nwsl",
                "team_name": "Angel City FC",
                "city": "Los Angeles",
                "team_site_url": "https://www.angelcity.com/",
                "manual_review_status": "review_required",
                "render_enabled": "false",
            }
        ],
        ["team_id", "league_id", "team_name", "city", "team_site_url", "manual_review_status", "render_enabled"],
    )
    write_csv(
        root / "nwsl" / "source_urls.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "source_kind": "logo_review_source",
                "source_url": "https://www.angelcity.com/",
                "source_domain": "www.angelcity.com",
                "source_tier": "official_candidate",
                "manual_review_status": "review_required",
                "paid_source": "false",
                "download_allowed": "false",
                "approval_status": "not_approved",
                "notes": "review only",
            }
        ],
        ["entity_type", "entity_id", "source_kind", "source_url", "source_domain", "source_tier", "manual_review_status", "paid_source", "download_allowed", "approval_status", "notes"],
    )
    write_csv(
        root / "nwsl" / "asset_slots.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "asset_slot": "primary_logo",
                "intended_use": "team identity reference",
                "target_path": "assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png",
                "source_url_required": "true",
                "local_file_path": "",
                "file_exists": "false",
                "approval_status": "not_approved",
                "render_enabled": "false",
                "auto_download_allowed": "false",
                "publish_ready": "false",
                "notes": "review only",
            }
        ],
        ["entity_type", "entity_id", "league_id", "team_id", "asset_slot", "intended_use", "target_path", "source_url_required", "local_file_path", "file_exists", "approval_status", "render_enabled", "auto_download_allowed", "publish_ready", "notes"],
    )
    write_csv(
        root / "nwsl" / "approval_status.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "approval_scope": "team_logo",
                "approval_status": "not_approved",
                "approved_by": "",
                "approved_at_utc": "",
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": "manual review required",
            }
        ],
        ["entity_type", "entity_id", "approval_scope", "approval_status", "approved_by", "approved_at_utc", "auto_approval_allowed", "render_enabled", "publish_ready", "notes"],
    )
    write_csv(
        root / "europe_top_flight" / "leagues.csv",
        [
            {
                "league_id": "wsl_england",
                "league_name": "Barclays Women's Super League",
                "country": "England",
                "official_url": "https://www.wslfootball.com/",
                "teams_url": "https://www.wslfootball.com/clubs/index",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            }
        ],
        ["league_id", "league_name", "country", "official_url", "teams_url", "paid_source", "auto_download_allowed", "render_enabled"],
    )
    write_csv(
        root / "europe_top_flight" / "teams.csv",
        [],
        ["team_id", "league_id", "team_name", "country", "team_site_url"],
    )
    write_csv(
        root / "europe_top_flight" / "source_urls.csv",
        [
            {
                "entity_type": "league",
                "entity_id": "wsl_england",
                "source_kind": "league_home",
                "source_url": "https://www.wslfootball.com/",
                "source_domain": "www.wslfootball.com",
                "source_tier": "official_candidate",
                "manual_review_status": "review_required",
                "paid_source": "false",
                "download_allowed": "false",
                "approval_status": "not_approved",
                "notes": "review only",
            }
        ],
        ["entity_type", "entity_id", "source_kind", "source_url", "source_domain", "source_tier", "manual_review_status", "paid_source", "download_allowed", "approval_status", "notes"],
    )
    write_csv(
        root / "europe_top_flight" / "asset_slots.csv",
        [
            {
                "entity_type": "league",
                "entity_id": "wsl_england",
                "league_id": "wsl_england",
                "team_id": "",
                "asset_slot": "league_mark",
                "intended_use": "league reference only",
                "target_path": "assets/leagues/womens_soccer/europe_top_flight/wsl_england/league_mark.png",
                "source_url_required": "true",
                "local_file_path": "",
                "file_exists": "false",
                "approval_status": "not_approved",
                "render_enabled": "false",
                "auto_download_allowed": "false",
                "publish_ready": "false",
                "notes": "review only",
            }
        ],
        ["entity_type", "entity_id", "league_id", "team_id", "asset_slot", "intended_use", "target_path", "source_url_required", "local_file_path", "file_exists", "approval_status", "render_enabled", "auto_download_allowed", "publish_ready", "notes"],
    )
    write_csv(
        root / "europe_top_flight" / "approval_status.csv",
        [
            {
                "entity_type": "league",
                "entity_id": "wsl_england",
                "approval_scope": "league_mark",
                "approval_status": "not_approved",
                "approved_by": "",
                "approved_at_utc": "",
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": "manual review required",
            }
        ],
        ["entity_type", "entity_id", "approval_scope", "approval_status", "approved_by", "approved_at_utc", "auto_approval_allowed", "render_enabled", "publish_ready", "notes"],
    )

    rows = module.build_rows()
    decisions = module.intake_rows(
        rows,
        {
            ("nwsl", "team", "angel_city_fc"): {
                "operator_decision": "hold_for_more_evidence",
                "source_reviewed": "yes",
                "identity_match": "yes",
                "source_url_to_record": "https://www.angelcity.com/",
                "registry_action": "hold_no_registry_state_change",
                "operator_notes": "Need full sweep",
                "reviewed_by": "Mike",
                "reviewed_at_local": "2026-06-26 20:00",
            }
        },
    )
    png_path, warnings = module.make_contact_sheet(rows, module.OUT_PNG)
    review_rows = module.walkthrough_rows(rows)
    walkthrough_md = module.render_walkthrough_markdown(rows, review_rows, "2026-06-26T20:00:00+00:00")

    assert warnings == []
    assert len(rows) == 2
    assert rows[0]["display_name"] == "Angel City FC"
    assert rows[0]["current_approval_status"] == "not_approved"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[1]["display_name"] == "Barclays Women's Super League"
    assert rows[1]["official_source_candidate"] == "https://www.wslfootball.com/"
    assert decisions[0]["operator_decision"] == "hold_for_more_evidence"
    assert decisions[0]["approval_scope"] == "review_only_renderer_womens_soccer_logo_trust_manual_intake"
    assert decisions[0]["publish_ready"] == "false"
    assert decisions[0]["move_files"] == "false"
    assert review_rows[0]["priority_group"] == "P0_NWSL_TEAM_LOGOS"
    assert review_rows[0]["recommended_operator_decision"] == "approve_for_review_only_renderer_use"
    assert review_rows[0]["approval_precondition"] == "local_asset_present_manual_source_identity_review_required"
    assert review_rows[0]["auto_approval"] == "false"
    assert review_rows[0]["asset_downloads"] == "false"
    assert review_rows[1]["priority_group"] == "P1_WSL_FOUNDATION"
    assert review_rows[1]["recommended_operator_decision"] == "hold_for_more_evidence"
    assert "Safest Non-WSL Europe Expansion" in walkthrough_md
    assert "Recommended order after Liga F" in walkthrough_md
    assert Path(png_path).exists()
