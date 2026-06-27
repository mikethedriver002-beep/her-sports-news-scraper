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
    candidates = list(csv.DictReader(module.CANDIDATES.open(newline="", encoding="utf-8")))

    assert len(rows) == 1
    assert len(intake) == 1
    assert len(candidates) == 1
    assert rows[0]["team_name"] == "Angel City FC"
    assert rows[0]["display_name"] == "operator_add_player_candidate"
    assert rows[0]["local_candidate_exists"] == "false"
    assert rows[0]["approved_marker_exists"] == "false"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert intake[0]["operator_decision"] == "operator_fill_required"
    assert intake[0]["source_allowed_for_review_only"] == "operator_fill_required"
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))
    assert module.OUT_INDEX.exists()
    assert module.OUT_JSON.exists()
    assert "No downloads or approvals" in module.OUT_INDEX.read_text(encoding="utf-8")
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

    assert module.main() == 0
    rerun_intake = list(csv.DictReader(module.OUT_INTAKE.open(newline="", encoding="utf-8-sig")))
    assert rerun_intake[0]["operator_decision"] == "hold_identity"
    assert rerun_intake[0]["operator_notes"] == "Reviewed Pena source; keep held for now."
    assert rerun_intake[0]["operator_priority"] == "P1"
    assert rerun_intake[0]["source_language_note"] == "Espana"
    assert rerun_intake[0]["publish_ready"] == "false"
    assert rerun_intake[0]["auto_approval"] == "false"
