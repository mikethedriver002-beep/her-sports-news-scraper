from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_wnba_athlete_photo_contact_sheets_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_wnba_athlete_photo_contact_sheets_v1", SCRIPT)
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


def make_headshot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (260, 190), (255, 255, 255, 0))
    for x in range(80, 180):
        for y in range(24, 156):
            image.putpixel((x, y), (98, 185, 172, 255))
    image.save(path)
    Path(path.as_posix() + ".approved").write_text("approved=true\n", encoding="utf-8")


def test_wnba_athlete_photo_contact_sheets_are_review_only_team_boards(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.PROJECT_ROOT = tmp_path
    module.OUT_DIR = tmp_path / "data" / "asset_registry" / "wnba" / "athlete_photo_contact_sheets"
    module.OUT_INDEX = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_athlete_photo_contact_sheet_index.md"
    module.OUT_CSV = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_athlete_photo_contact_sheet.csv"
    module.OUT_INTAKE = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_athlete_photo_review_intake.csv"
    module.OUT_JSON = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_athlete_photo_contact_sheet_manifest.json"

    headshot_path = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "new_york_liberty_breanna_stewart" / "headshot.png"
    make_headshot(headshot_path)
    root = tmp_path / "data" / "asset_registry" / "wnba"
    write_csv(
        root / "teams.csv",
        [
            {
                "team_id": "new_york_liberty",
                "league": "WNBA",
                "team_name": "New York Liberty",
                "city": "New York",
                "nickname": "Liberty",
                "slug": "new_york_liberty",
                "conference": "Eastern",
                "active": "true",
                "primary_hex": "62B9AC",
                "secondary_hex": "082435",
            }
        ],
        ["team_id", "league", "team_name", "city", "nickname", "slug", "conference", "active", "primary_hex", "secondary_hex"],
    )
    write_csv(
        root / "athlete_sources.csv",
        [
            {
                "team_id": "new_york_liberty",
                "team_name": "New York Liberty",
                "roster_url": "https://liberty.wnba.com/roster",
                "source_note": "official_team_subdomain_roster_ok",
            }
        ],
        ["team_id", "team_name", "roster_url", "source_note"],
    )
    write_csv(
        root / "athlete_photo_catalog.csv",
        [
            {
                "athlete_id": "new_york_liberty_breanna_stewart",
                "athlete_name": "Breanna Stewart",
                "team_id": "new_york_liberty",
                "league": "WNBA",
                "provider_player_id": "1630993",
                "source_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/1630993.png",
                "identity_confidence": "0.72",
                "asset_kind": "headshot",
                "local_asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
                "file_exists": "true",
                "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
                "approved_marker_exists": "true",
                "status": "approved",
                "approval_status": "approved_marker_present_manual_source_recheck_required",
                "identity_review_status": "manual_source_recheck_required",
                "missing_asset_reason": "",
                "source_evidence": "approved_assets_registry; decision_source=default",
                "crop_readiness_notes": "default_decision_source_manual_recheck_required",
                "render_template_uses": "photo_first",
                "review_only_policy": "catalog_only_no_auto_approval_no_file_movement",
            }
        ],
        [
            "athlete_id",
            "athlete_name",
            "team_id",
            "league",
            "provider_player_id",
            "source_url",
            "identity_confidence",
            "asset_kind",
            "local_asset_path",
            "file_exists",
            "approved_marker_path",
            "approved_marker_exists",
            "status",
            "approval_status",
            "identity_review_status",
            "missing_asset_reason",
            "source_evidence",
            "crop_readiness_notes",
            "render_template_uses",
            "review_only_policy",
        ],
    )

    rows = module.build_rows()
    decisions = module.intake_rows(rows)
    sheet_path, warnings = module.make_team_contact_sheet("new_york_liberty", rows)
    board = module.render_team_board("new_york_liberty", rows, sheet_path, "2026-06-26T22:00:00+00:00")
    index = module.render_index(rows, {"new_york_liberty": {"team_name": "New York Liberty", "rows": "1", "sheet_path": "data/asset_registry/wnba/athlete_photo_contact_sheets/new_york_liberty.png", "board_path": "data/asset_registry/wnba/athlete_photo_contact_sheets/new_york_liberty.md"}}, "2026-06-26T22:00:00+00:00")

    assert warnings == []
    assert len(rows) == 1
    assert rows[0]["athlete_name"] == "Breanna Stewart"
    assert rows[0]["local_headshot_exists"] == "true"
    assert rows[0]["approved_marker_exists"] == "true"
    assert rows[0]["official_roster_page_candidate"] == "https://liberty.wnba.com/roster"
    assert rows[0]["official_player_profile_candidate"] == "https://www.wnba.com/player/1630993/breanna-stewart"
    assert rows[0]["official_roster_photo_candidate_url"] == "https://cdn.wnba.com/headshots/wnba/latest/260x190/1630993.png"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert Path(sheet_path).exists()
    assert decisions[0]["operator_decision"] == "operator_fill_required"
    assert decisions[0]["identity_verified"] == "operator_fill_required"
    assert decisions[0]["approval_scope"] == "review_only_renderer_athlete_photo_trust_manual_intake"
    assert decisions[0]["publish_ready"] == "false"
    assert decisions[0]["move_files"] == "false"
    assert "does not download official photos" in board
    assert "Human-edited intake CSV" in index
