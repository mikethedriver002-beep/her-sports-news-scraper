from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1", SCRIPT)
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


def test_womens_soccer_athlete_photo_contact_sheets_seed_nwsl_without_downloads(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.PROJECT_ROOT = tmp_path
    module.REGISTRY_ROOT = Path("data/asset_registry/womens_soccer")
    module.OUT_DIR = tmp_path / "data" / "asset_registry" / "womens_soccer" / "athlete_photo_contact_sheets"
    module.OUT_INDEX = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet_index.md"
    module.OUT_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet.csv"
    module.OUT_INTAKE = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_review_intake.csv"
    module.OUT_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet_manifest.json"
    module.CANDIDATES = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_candidates.csv"
    module.OUT_OPERATOR_BOARD_MD = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_operator_board.md"
    module.OUT_OPERATOR_BOARD_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_operator_board.csv"
    module.OUT_OPERATOR_BOARD_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_operator_board.json"
    module.OUT_DOWNLOAD_INTAKE_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_download_intake.csv"
    module.OUT_DOWNLOAD_INTAKE_MD = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_download_intake.md"
    module.OUT_DOWNLOAD_INTAKE_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_download_intake.json"

    root = tmp_path / "data" / "asset_registry" / "womens_soccer" / "nwsl"
    write_csv(
        root / "leagues.csv",
        [
            {
                "league_id": "nwsl",
                "league_name": "National Women's Soccer League",
                "official_url": "https://www.nwslsoccer.com/",
                "teams_url": "https://www.nwslsoccer.com/teams/index",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            }
        ],
        ["league_id", "league_name", "official_url", "teams_url", "paid_source", "auto_download_allowed", "render_enabled"],
    )
    write_csv(
        root / "teams.csv",
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
        root / "source_urls.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "source_kind": "nwsl_roster",
                "source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "source_domain": "www.nwslsoccer.com",
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

    assert module.main() == 0
    rows = list(csv.DictReader(module.OUT_CSV.open(newline="", encoding="utf-8")))
    intake = list(csv.DictReader(module.OUT_INTAKE.open(newline="", encoding="utf-8")))
    download_intake = list(csv.DictReader(module.OUT_DOWNLOAD_INTAKE_CSV.open(newline="", encoding="utf-8")))
    candidates = list(csv.DictReader(module.CANDIDATES.open(newline="", encoding="utf-8")))

    assert len(rows) == 1
    assert len(intake) == 1
    assert len(download_intake) == 1
    assert len(candidates) == 1
    assert rows[0]["team_name"] == "Angel City FC"
    assert rows[0]["display_name"] == "operator_add_player_candidate"
    assert rows[0]["local_candidate_exists"] == "false"
    assert rows[0]["approved_marker_exists"] == "false"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["source_candidate_class"] == "manual_starter_placeholder"
    assert rows[0]["rights_class"] == "operator_rights_review_required"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["separate_approval_required"] == "true"
    assert intake[0]["operator_decision"] == "operator_fill_required"
    assert intake[0]["source_allowed_for_review_only"] == "operator_fill_required"
    assert download_intake[0]["download_approved"] == "no"
    assert download_intake[0]["download_status"] == "not_requested"
    assert download_intake[0]["operator_source_url"] == "operator_fill_required"
    assert download_intake[0]["operator_rights_class"] == "operator_fill_required"
    assert download_intake[0]["approval_status"] == "not_approved"
    assert download_intake[0]["asset_downloads"] == "false"
    assert download_intake[0]["quarantine_folder"] == "data/assets/quarantine/review_only_candidates"
    assert "data/assets/quarantine/review_only_candidates/womens_soccer/athlete_photo_candidates" in download_intake[0]["proposed_quarantine_path"]
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))
    assert module.OUT_INDEX.exists()
    assert module.OUT_JSON.exists()
    assert module.OUT_OPERATOR_BOARD_MD.exists()
    assert module.OUT_OPERATOR_BOARD_CSV.exists()
    assert module.OUT_OPERATOR_BOARD_JSON.exists()
    assert module.OUT_DOWNLOAD_INTAKE_MD.exists()
    assert module.OUT_DOWNLOAD_INTAKE_JSON.exists()
    assert "No downloads or approvals" in module.OUT_INDEX.read_text(encoding="utf-8")
    assert "Default download_approved value: `no`" in module.OUT_DOWNLOAD_INTAKE_MD.read_text(encoding="utf-8")
    operator_board_text = module.OUT_OPERATOR_BOARD_MD.read_text(encoding="utf-8")
    operator_rows = list(csv.DictReader(module.OUT_OPERATOR_BOARD_CSV.open(newline="", encoding="utf-8")))
    operator_manifest = json.loads(module.OUT_OPERATOR_BOARD_JSON.read_text(encoding="utf-8"))
    assert "NWSL First Queue" in operator_board_text
    assert "No paid APIs" in operator_board_text
    assert operator_rows[0]["league_id"] == "nwsl"
    assert operator_rows[0]["review_only"] == "true"
    assert operator_rows[0]["publish_ready"] == "false"
    assert operator_rows[0]["asset_downloads"] == "false"
    assert operator_rows[0]["download_intake_file"] == "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv"
    assert operator_rows[0]["download_intake_rows"] == "1"
    assert operator_manifest["status"] == "operator_board_ready"
    assert operator_manifest["operator_board_rows"] == 1
    assert operator_manifest["downloads_performed"] is False
    assert operator_manifest["approvals_applied"] is False
    assert operator_manifest["headshot_files_written"] is False
    assert operator_manifest["approved_markers_created"] is False
    download_manifest = json.loads(module.OUT_DOWNLOAD_INTAKE_JSON.read_text(encoding="utf-8"))
    assert download_manifest["status"] == "download_intake_ready"
    assert download_manifest["download_intake_rows"] == 1
    assert download_manifest["download_approved_yes_rows"] == 0
    assert download_manifest["downloads_performed"] is False
    assert download_manifest["separate_approval_required"] is True
    manifest = json.loads(module.OUT_JSON.read_text(encoding="utf-8"))
    assert manifest["version"] == module.VERSION
    assert manifest["status"] == "contact_sheets_ready"
    assert manifest["candidate_rows"] == 1
    assert manifest["team_boards"] == 1
    assert manifest["downloads_performed"] is False
    assert manifest["approvals_applied"] is False
    assert manifest["headshot_files_written"] is False
    assert manifest["approved_markers_created"] is False
    assert manifest["publish_ready"] is False
    assert manifest["candidate_csv"] == module.CANDIDATES.as_posix()
    assert manifest["contact_sheet_csv"] == module.OUT_CSV.as_posix()
    assert manifest["intake_csv"] == module.OUT_INTAKE.as_posix()
    assert manifest["download_intake_csv"] == module.OUT_DOWNLOAD_INTAKE_CSV.as_posix()
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["operator_board_md"] == module.OUT_OPERATOR_BOARD_MD.as_posix()
    assert manifest["operator_board_rows"] == 1
    assert Path(rows[0]["team_review_board_path"]).exists()
    if module.Image is not None:
        assert Path(rows[0]["team_contact_sheet_path"]).exists()

    preserved_intake = dict(intake[0])
    preserved_intake["operator_decision"] = "hold_identity"
    preserved_intake["operator_notes"] = "Reviewed Pena source; keep held for now."
    preserved_intake["publish_ready"] = "true"
    preserved_intake["auto_approval"] = "true"
    preserved_intake["operator_priority"] = "P1"
    preserved_intake["source_language_note"] = "Espana"
    write_csv(module.OUT_INTAKE, [preserved_intake], module.INTAKE_FIELDS + ["operator_priority", "source_language_note"])
    preserved_download_intake = dict(download_intake[0])
    preserved_download_intake["download_approved"] = "yes"
    preserved_download_intake["source_url"] = "https://example.test/human-reviewed-source"
    preserved_download_intake["rights_class"] = "human_reviewed_public_source_candidate"
    preserved_download_intake["identity_confidence"] = "human_confirmed_team_and_name"
    preserved_download_intake["intended_review_only_use"] = "review_only_quarantine_candidate_check"
    preserved_download_intake["operator_source_url"] = "https://example.test/player-photo"
    preserved_download_intake["operator_rights_class"] = "operator_reviewed_public_source"
    preserved_download_intake["operator_identity_confidence"] = "operator_confirmed_identity"
    preserved_download_intake["operator_intended_review_only_use"] = "review_only_local_candidate_check"
    preserved_download_intake["operator_notes"] = "Human-edited future quarantine gate."
    preserved_download_intake["publish_ready"] = "true"
    preserved_download_intake["auto_approval"] = "true"
    preserved_download_intake["download_priority"] = "P0"
    reordered_download_fields = ["download_priority"] + list(reversed(module.DOWNLOAD_INTAKE_FIELDS))
    with module.OUT_DOWNLOAD_INTAKE_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=reordered_download_fields)
        writer.writeheader()
        writer.writerow(preserved_download_intake)

    assert module.main() == 0
    rerun_intake = list(csv.DictReader(module.OUT_INTAKE.open(newline="", encoding="utf-8-sig")))
    rerun_download_intake = list(csv.DictReader(module.OUT_DOWNLOAD_INTAKE_CSV.open(newline="", encoding="utf-8-sig")))
    assert rerun_intake[0]["operator_decision"] == "hold_identity"
    assert rerun_intake[0]["operator_notes"] == "Reviewed Pena source; keep held for now."
    assert rerun_intake[0]["operator_priority"] == "P1"
    assert rerun_intake[0]["source_language_note"] == "Espana"
    assert rerun_intake[0]["publish_ready"] == "false"
    assert rerun_intake[0]["auto_approval"] == "false"
    assert rerun_download_intake[0]["download_approved"] == "yes"
    assert rerun_download_intake[0]["source_url"] == "https://example.test/human-reviewed-source"
    assert rerun_download_intake[0]["rights_class"] == "human_reviewed_public_source_candidate"
    assert rerun_download_intake[0]["identity_confidence"] == "human_confirmed_team_and_name"
    assert rerun_download_intake[0]["intended_review_only_use"] == "review_only_quarantine_candidate_check"
    assert rerun_download_intake[0]["operator_source_url"] == "https://example.test/player-photo"
    assert rerun_download_intake[0]["operator_notes"] == "Human-edited future quarantine gate."
    assert rerun_download_intake[0]["download_priority"] == "P0"
    assert rerun_download_intake[0]["publish_ready"] == "false"
    assert rerun_download_intake[0]["auto_approval"] == "false"
    assert rerun_download_intake[0]["asset_downloads"] == "false"


def test_womens_soccer_athlete_photo_contact_sheets_expand_roster_rows_without_slow_full_png(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.PROJECT_ROOT = tmp_path
    module.REGISTRY_ROOT = Path("data/asset_registry/womens_soccer")
    module.TEAM_SHEET_ROOT = Path("data/asset_registry/womens_soccer/athlete_photo_contact_sheets")
    module.MAX_VISUAL_ROWS_PER_TEAM = 2
    module.OUT_DIR = tmp_path / "data" / "asset_registry" / "womens_soccer" / "athlete_photo_contact_sheets"
    module.OUT_INDEX = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet_index.md"
    module.OUT_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet.csv"
    module.OUT_INTAKE = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_review_intake.csv"
    module.OUT_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet_manifest.json"
    module.CANDIDATES = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_candidates.csv"

    root = tmp_path / "data" / "asset_registry" / "womens_soccer" / "nwsl"
    write_csv(
        root / "leagues.csv",
        [
            {
                "league_id": "nwsl",
                "league_name": "National Women's Soccer League",
                "official_url": "https://www.nwslsoccer.com/",
                "teams_url": "https://www.nwslsoccer.com/teams/index",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            }
        ],
        ["league_id", "league_name", "official_url", "teams_url", "paid_source", "auto_download_allowed", "render_enabled"],
    )
    write_csv(
        root / "teams.csv",
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
        root / "source_urls.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "source_kind": "nwsl_roster",
                "source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "source_domain": "www.nwslsoccer.com",
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
        root / "players.csv",
        [
            {
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "player_id": "angel_city_fc_player_001",
                "provider_player_id": "1001",
                "display_name": "Alyssa Thompson",
                "roster_source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "manual_review_status": "identity_source_review_required",
                "approval_status": "not_approved",
            },
            {
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "player_id": "angel_city_fc_player_002",
                "provider_player_id": "1002",
                "display_name": "Claire Emslie",
                "roster_source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "manual_review_status": "identity_source_review_required",
                "approval_status": "not_approved",
            },
            {
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "player_id": "angel_city_fc_player_003",
                "provider_player_id": "1003",
                "display_name": "Sydney Leroux",
                "roster_source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "manual_review_status": "identity_source_review_required",
                "approval_status": "not_approved",
            },
        ],
        [
            "league_id",
            "team_id",
            "player_id",
            "provider_player_id",
            "display_name",
            "roster_source_url",
            "manual_review_status",
            "approval_status",
        ],
    )
    write_csv(
        module.CANDIDATES,
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "player_id": "",
                "display_name": "operator_add_player_candidate",
                "candidate_id": "angel_city_fc_operator_add_candidate",
                "candidate_status": "operator_add_candidate",
            }
        ],
        module.CANDIDATE_FIELDS,
    )

    assert module.main() == 0
    rows = list(csv.DictReader(module.OUT_CSV.open(newline="", encoding="utf-8")))
    candidates = list(csv.DictReader(module.CANDIDATES.open(newline="", encoding="utf-8")))
    manifest = json.loads(module.OUT_JSON.read_text(encoding="utf-8"))
    operator_rows = list(csv.DictReader(module.OUT_OPERATOR_BOARD_CSV.open(newline="", encoding="utf-8")))
    board_text = (tmp_path / "data/asset_registry/womens_soccer/athlete_photo_contact_sheets/nwsl/angel_city_fc.md").read_text(encoding="utf-8")

    assert len(rows) == 3
    assert len(candidates) == 3
    assert {row["display_name"] for row in rows} == {"Alyssa Thompson", "Claire Emslie", "Sydney Leroux"}
    assert all(row["candidate_status"] == "official_roster_source_candidate" for row in rows)
    assert all("/nwsl/nwsl/" not in row["local_candidate_path"] for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["auto_approval"] == "false" for row in rows)
    assert rows[0]["team_contact_sheet_path"] == "data/asset_registry/womens_soccer/athlete_photo_contact_sheets/nwsl/angel_city_fc.png"
    assert manifest["candidate_rows"] == 3
    assert manifest["team_boards"] == 1
    assert manifest["official_roster_candidate_rows"] == 3
    assert manifest["operator_board_rows"] == 1
    assert operator_rows[0]["official_roster_candidate_rows"] == "3"
    assert operator_rows[0]["starter_candidate_rows"] == "0"
    assert "NWSL roster-sourced candidate rows first" in operator_rows[0]["operator_next_step"]
    assert manifest["warnings"] == ["angel_city_fc:visual_preview_limited_to_2_of_3_rows"]
    assert "Visual PNG preview shows the first `2` rows only" in board_text
    assert "Sydney Leroux" in board_text
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))


def test_womens_soccer_athlete_photo_contact_sheets_adds_europe_top_flight_starter_rows(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.PROJECT_ROOT = tmp_path
    module.REGISTRY_ROOT = Path("data/asset_registry/womens_soccer")
    module.TEAM_SHEET_ROOT = Path("data/asset_registry/womens_soccer/athlete_photo_contact_sheets")
    module.OUT_DIR = tmp_path / "data" / "asset_registry" / "womens_soccer" / "athlete_photo_contact_sheets"
    module.OUT_INDEX = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet_index.md"
    module.OUT_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet.csv"
    module.OUT_INTAKE = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_review_intake.csv"
    module.OUT_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_contact_sheet_manifest.json"
    module.CANDIDATES = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_candidates.csv"
    module.OUT_OPERATOR_BOARD_MD = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_operator_board.md"
    module.OUT_OPERATOR_BOARD_CSV = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_operator_board.csv"
    module.OUT_OPERATOR_BOARD_JSON = tmp_path / "data" / "asset_registry" / "womens_soccer" / "womens_soccer_athlete_photo_operator_board.json"

    nwsl = tmp_path / "data" / "asset_registry" / "womens_soccer" / "nwsl"
    write_csv(
        nwsl / "leagues.csv",
        [
            {
                "league_id": "nwsl",
                "league_name": "National Women's Soccer League",
                "official_url": "https://www.nwslsoccer.com/",
                "teams_url": "https://www.nwslsoccer.com/teams/index",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            }
        ],
        ["league_id", "league_name", "official_url", "teams_url", "paid_source", "auto_download_allowed", "render_enabled"],
    )
    write_csv(
        nwsl / "teams.csv",
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
        nwsl / "source_urls.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "source_kind": "nwsl_roster",
                "source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "source_domain": "www.nwslsoccer.com",
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
        nwsl / "players.csv",
        [
            {
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "player_id": "angel_city_fc_player_001",
                "provider_player_id": "1001",
                "display_name": "Alyssa Thompson",
                "roster_source_url": "https://www.nwslsoccer.com/teams/angel-city-fc/roster",
                "manual_review_status": "identity_source_review_required",
                "approval_status": "not_approved",
            }
        ],
        [
            "league_id",
            "team_id",
            "player_id",
            "provider_player_id",
            "display_name",
            "roster_source_url",
            "manual_review_status",
            "approval_status",
        ],
    )

    europe = tmp_path / "data" / "asset_registry" / "womens_soccer" / "europe_top_flight"
    write_csv(
        europe / "leagues.csv",
        [
            {
                "league_id": "wsl_england",
                "league_name": "Barclays Women's Super League",
                "official_url": "https://www.wslfootball.com/",
                "teams_url": "https://www.wslfootball.com/clubs/index",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            },
            {
                "league_id": "liga_f_spain",
                "league_name": "Liga F",
                "official_url": "https://www.laliga.com/en-GB/futbol-femenino",
                "teams_url": "https://www.laliga.com/en-GB/futbol-femenino",
                "paid_source": "false",
                "auto_download_allowed": "false",
                "render_enabled": "false",
            },
        ],
        ["league_id", "league_name", "official_url", "teams_url", "paid_source", "auto_download_allowed", "render_enabled"],
    )
    write_csv(
        europe / "teams.csv",
        [
            {
                "team_id": "arsenal_women",
                "league_id": "wsl_england",
                "team_name": "Arsenal Women",
                "team_site_url": "https://www.arsenal.com/women",
                "roster_url": "https://www.arsenal.com/women/players",
                "manual_review_status": "review_required",
                "render_enabled": "false",
            },
            {
                "team_id": "barcelona_femeni",
                "league_id": "liga_f_spain",
                "team_name": "FC Barcelona Femeni",
                "team_site_url": "https://www.fcbarcelona.com/en/football/womens-football",
                "roster_url": "https://www.fcbarcelona.com/en/football/womens-football/players",
                "manual_review_status": "review_required",
                "render_enabled": "false",
            },
        ],
        ["team_id", "league_id", "team_name", "team_site_url", "roster_url", "manual_review_status", "render_enabled"],
    )
    write_csv(
        europe / "source_urls.csv",
        [
            {
                "entity_type": "team",
                "entity_id": "arsenal_women",
                "source_kind": "roster",
                "source_url": "https://www.arsenal.com/women/players",
                "source_domain": "www.arsenal.com",
                "source_tier": "official_candidate",
                "manual_review_status": "review_required",
                "paid_source": "false",
                "download_allowed": "false",
                "approval_status": "not_approved",
                "notes": "review only",
            },
            {
                "entity_type": "team",
                "entity_id": "barcelona_femeni",
                "source_kind": "roster",
                "source_url": "https://www.fcbarcelona.com/en/football/womens-football/players",
                "source_domain": "www.fcbarcelona.com",
                "source_tier": "official_candidate",
                "manual_review_status": "review_required",
                "paid_source": "false",
                "download_allowed": "false",
                "approval_status": "not_approved",
                "notes": "review only",
            },
        ],
        ["entity_type", "entity_id", "source_kind", "source_url", "source_domain", "source_tier", "manual_review_status", "paid_source", "download_allowed", "approval_status", "notes"],
    )
    write_csv(
        europe / "players.csv",
        [],
        ["player_id", "league_id", "team_id", "display_name", "provider_player_id", "roster_source_url", "status", "manual_review_status", "asset_registry_status", "approval_status", "notes"],
    )

    assert module.main() == 0
    rows = list(csv.DictReader(module.OUT_CSV.open(newline="", encoding="utf-8")))
    intake = list(csv.DictReader(module.OUT_INTAKE.open(newline="", encoding="utf-8")))
    manifest = json.loads(module.OUT_JSON.read_text(encoding="utf-8"))
    index_text = module.OUT_INDEX.read_text(encoding="utf-8")
    operator_board_text = module.OUT_OPERATOR_BOARD_MD.read_text(encoding="utf-8")
    operator_rows = list(csv.DictReader(module.OUT_OPERATOR_BOARD_CSV.open(newline="", encoding="utf-8")))
    europe_rows = [row for row in rows if row["scope_id"] == "europe_top_flight"]

    assert len(rows) == 3
    assert len(intake) == 3
    assert len(europe_rows) == 2
    assert {row["league_id"] for row in europe_rows} == {"wsl_england", "liga_f_spain"}
    assert all(row["candidate_status"] == "operator_add_candidate" for row in europe_rows)
    assert all(row["display_name"] == "operator_add_player_candidate" for row in europe_rows)
    assert all(row["review_only"] == "true" for row in europe_rows)
    assert all(row["publish_ready"] == "false" for row in europe_rows)
    assert all(row["auto_approval"] == "false" for row in europe_rows)
    assert all(row["asset_downloads"] == "false" for row in europe_rows)
    assert any("/europe_top_flight/wsl_england/teams/arsenal_women/" in row["local_candidate_path"] for row in europe_rows)
    assert Path("data/asset_registry/womens_soccer/athlete_photo_contact_sheets/europe_top_flight/arsenal_women.md").exists()
    assert manifest["candidate_rows"] == 3
    assert manifest["team_boards"] == 3
    assert manifest["scope_counts"] == {"europe_top_flight": 2, "nwsl": 1}
    assert manifest["league_counts"] == {"liga_f_spain": 1, "nwsl": 1, "wsl_england": 1}
    assert manifest["starter_candidate_rows"] == 2
    assert manifest["official_roster_candidate_rows"] == 1
    assert manifest["operator_board_rows"] == 3
    assert [row["league_id"] for row in operator_rows] == ["nwsl", "wsl_england", "liga_f_spain"]
    assert "Europe Expansion Queue" in operator_board_text
    assert "starter_rows=1" in operator_board_text
    assert "Scope Counts" in index_text
    assert "wsl_england" in index_text
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))
