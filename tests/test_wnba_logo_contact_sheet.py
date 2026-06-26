from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_wnba_logo_contact_sheet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_wnba_logo_contact_sheet_v1", SCRIPT)
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
    image = Image.new("RGBA", (180, 120), (255, 255, 255, 0))
    for x in range(30, 150):
        for y in range(24, 96):
            image.putpixel((x, y), (98, 185, 172, 255))
    image.save(path)


def test_wnba_logo_contact_sheet_builds_review_only_sweep_board(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.PROJECT_ROOT = tmp_path
    module.OUT_MD = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_team_logo_contact_sheet.md"
    module.OUT_CSV = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_team_logo_contact_sheet.csv"
    module.OUT_PNG = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_team_logo_contact_sheet.png"
    module.OUT_INTAKE = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_team_logo_review_intake.csv"
    module.OUT_JSON = tmp_path / "data" / "asset_registry" / "wnba" / "wnba_team_logo_contact_sheet.json"

    logo_path = tmp_path / "assets" / "leagues" / "wnba" / "teams" / "new_york_liberty" / "logo.png"
    make_logo(logo_path)
    wnba_root = tmp_path / "data" / "asset_registry" / "wnba"
    write_csv(
        wnba_root / "teams.csv",
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
        wnba_root / "team_logos.csv",
        [
            {
                "team_id": "new_york_liberty",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "last_verified_utc": "2026-06-26T20:14:57+00:00",
                "source_note": "human_reviewed_official_team_source_for_review_only_renderer_use",
            }
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"],
    )
    write_csv(
        wnba_root / "logo_sources.csv",
        [
            {
                "team_id": "new_york_liberty",
                "team_name": "New York Liberty",
                "source_url": "https://liberty.wnba.com/",
                "target_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "source_note": "human_reviewed_official_team_source_for_review_only_renderer_use",
            }
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )
    write_csv(
        tmp_path / "data" / "asset_registry" / "logo_asset_catalog.csv",
        [
            {
                "league": "WNBA",
                "entity_type": "team_logo",
                "team_id": "new_york_liberty",
                "team_name": "New York Liberty",
                "local_logo_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "png_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "approval_status": "approved",
                "required": "true",
                "source_url": "https://liberty.wnba.com/",
                "source_note": "human_reviewed_official_team_source_for_review_only_renderer_use",
                "source_trust_status": "registered_source_policy_no_block_match",
                "logo_readiness_status": "exact_logo_ready_for_review_renderer",
                "renderer_fallback_cue": "renderer_may_use_exact_local_logo_after_normal_visual_qa",
                "operator_action": "catalog_only_no_action",
            }
        ],
        [
            "league",
            "entity_type",
            "team_id",
            "team_name",
            "local_logo_path",
            "png_path",
            "approval_status",
            "required",
            "source_url",
            "source_note",
            "source_trust_status",
            "logo_readiness_status",
            "renderer_fallback_cue",
            "operator_action",
        ],
    )

    rows = module.build_rows()
    decisions = module.intake_rows(
        rows,
        {
            "new_york_liberty": {
                "operator_decision": "approve_for_review_only_renderer_use",
                "source_reviewed": "yes",
                "identity_match": "yes",
                "source_url_to_record": "https://www.wnba.com/team/new-york-liberty",
                "registry_action": "confirm_existing_approval_update_source_metadata",
                "operator_notes": "Mike approved from contact sheet",
                "reviewed_by": "Mike",
                "reviewed_at_local": "2026-06-26 16:50",
            }
        },
    )
    png_path, warnings = module.make_contact_sheet(rows, module.OUT_PNG)

    assert warnings == []
    assert len(rows) == 1
    assert rows[0]["team_name"] == "New York Liberty"
    assert rows[0]["current_approval_status"] == "approved"
    assert rows[0]["current_source_url"] == "https://liberty.wnba.com/"
    assert rows[0]["official_source_candidate"] == "https://www.wnba.com/team/new-york-liberty"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert Path(png_path).exists()
    assert decisions[0]["operator_decision"] == "approve_for_review_only_renderer_use"
    assert decisions[0]["source_reviewed"] == "yes"
    assert decisions[0]["identity_match"] == "yes"
    assert decisions[0]["registry_action"] == "confirm_existing_approval_update_source_metadata"
    assert decisions[0]["reviewed_by"] == "Mike"
    assert decisions[0]["allowed_decisions"] == "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata"
    assert decisions[0]["approval_scope"] == "review_only_renderer_logo_trust_manual_intake"
    assert decisions[0]["publish_ready"] == "false"
    assert decisions[0]["move_files"] == "false"
