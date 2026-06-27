from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prepare_hsd_hockey_softball_source_review_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_hsd_hockey_softball_source_review_intake_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_command_center_module():
    script = REPO / "generate_hsd_operator_command_center_v2.py"
    spec = importlib.util.spec_from_file_location("generate_hsd_operator_command_center_v2", script)
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def seed_sport(tmp_path: Path, sport: str, league_id: str, league_name: str, logo_source: str, roster_source: str) -> None:
    if sport == "womens_hockey":
        root = tmp_path / "data" / "asset_registry" / "womens_hockey"
        write_csv(
            root / "womens_hockey_logo_contact_sheet.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "entity_type": "team",
                    "entity_id": "test_team",
                    "display_name": "Test Team",
                    "asset_slot": "primary_logo",
                    "target_path": "assets/leagues/womens_hockey/pwhl/teams/test_team/logo.png",
                    "local_file_exists": "false",
                    "official_source_candidate": logo_source,
                    "source_tier": "official_candidate",
                    "manual_review_status": "review_required",
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                    "human_intake_file": "data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv",
                    "review_only": "true",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                }
            ],
            [
                "sport_family",
                "league_id",
                "entity_type",
                "entity_id",
                "display_name",
                "asset_slot",
                "target_path",
                "local_file_exists",
                "official_source_candidate",
                "source_tier",
                "manual_review_status",
                "allowed_decisions",
                "human_intake_file",
                "review_only",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
            ],
        )
        write_csv(
            root / "womens_hockey_logo_review_intake.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "entity_type": "team",
                    "entity_id": "test_team",
                    "display_name": "Test Team",
                    "asset_slot": "primary_logo",
                    "target_path": "assets/leagues/womens_hockey/pwhl/teams/test_team/logo.png",
                    "official_source_candidate": logo_source,
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                    "operator_decision": "operator_fill_required",
                    "source_reviewed": "operator_fill_required",
                    "identity_match": "operator_fill_required",
                    "source_url_to_record": "",
                    "registry_action": "",
                    "operator_notes": "",
                    "reviewed_by": "",
                    "reviewed_at_local": "",
                    "approval_scope": "",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                    "operator_priority": "P1",
                }
            ],
            [
                "sport_family",
                "league_id",
                "entity_type",
                "entity_id",
                "display_name",
                "asset_slot",
                "target_path",
                "official_source_candidate",
                "allowed_decisions",
                "operator_decision",
                "source_reviewed",
                "identity_match",
                "source_url_to_record",
                "registry_action",
                "operator_notes",
                "reviewed_by",
                "reviewed_at_local",
                "approval_scope",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
                "operator_priority",
            ],
        )
        write_csv(
            root / "womens_hockey_athlete_photo_contact_sheet.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "team_id": "test_team",
                    "team_name": "Test Team",
                    "player_id": "",
                    "display_name": "Test Player",
                    "candidate_id": "test_team_operator_add_candidate",
                    "candidate_status": "operator_add_candidate",
                    "source_url": roster_source,
                    "source_domain": "example.com",
                    "source_tier": "official_candidate",
                    "source_kind": "roster",
                    "photo_candidate_url": "",
                    "local_candidate_path": "assets/leagues/womens_hockey/pwhl/athletes/test_team/operator_add_candidate/headshot.png",
                    "local_candidate_exists": "false",
                    "approved_marker_path": "assets/leagues/womens_hockey/pwhl/athletes/test_team/operator_add_candidate/.approved",
                    "approved_marker_exists": "false",
                    "identity_review_status": "operator_add_identity_evidence",
                    "approval_status": "not_approved",
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_photo_candidate|hold_identity|revise_source_metadata",
                    "human_intake_file": "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv",
                    "team_review_board_path": "data/asset_registry/womens_hockey/athlete_photo_contact_sheets/test_team.md",
                    "review_only": "true",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                }
            ],
            [
                "sport_family",
                "league_id",
                "team_id",
                "team_name",
                "player_id",
                "display_name",
                "candidate_id",
                "candidate_status",
                "source_url",
                "source_domain",
                "source_tier",
                "source_kind",
                "photo_candidate_url",
                "local_candidate_path",
                "local_candidate_exists",
                "approved_marker_path",
                "approved_marker_exists",
                "identity_review_status",
                "approval_status",
                "allowed_decisions",
                "human_intake_file",
                "team_review_board_path",
                "review_only",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
            ],
        )
        write_csv(
            root / "womens_hockey_athlete_photo_review_intake.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "team_id": "test_team",
                    "team_name": "Test Team",
                    "player_id": "",
                    "display_name": "Test Player",
                    "candidate_id": "test_team_operator_add_candidate",
                    "local_candidate_path": "assets/leagues/womens_hockey/pwhl/athletes/test_team/operator_add_candidate/headshot.png",
                    "source_url": roster_source,
                    "photo_candidate_url": "",
                    "approval_status": "not_approved",
                    "identity_review_status": "operator_add_identity_evidence",
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_photo_candidate|hold_identity|revise_source_metadata",
                    "operator_decision": "operator_fill_required",
                    "identity_verified": "operator_fill_required",
                    "source_reviewed": "operator_fill_required",
                    "local_file_reviewed": "operator_fill_required",
                    "source_allowed_for_review_only": "operator_fill_required",
                    "rights_reviewed": "operator_fill_required",
                    "source_url_to_record": "",
                    "registry_action": "",
                    "operator_notes": "",
                    "reviewed_by": "",
                    "reviewed_at_local": "",
                    "approval_scope": "",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                    "operator_priority": "P1",
                }
            ],
            [
                "sport_family",
                "league_id",
                "team_id",
                "team_name",
                "player_id",
                "display_name",
                "candidate_id",
                "local_candidate_path",
                "source_url",
                "photo_candidate_url",
                "approval_status",
                "identity_review_status",
                "allowed_decisions",
                "operator_decision",
                "identity_verified",
                "source_reviewed",
                "local_file_reviewed",
                "source_allowed_for_review_only",
                "rights_reviewed",
                "source_url_to_record",
                "registry_action",
                "operator_notes",
                "reviewed_by",
                "reviewed_at_local",
                "approval_scope",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
                "operator_priority",
            ],
        )
    else:
        root = tmp_path / "data" / "asset_registry" / "softball"
        write_csv(
            root / "softball_logo_contact_sheet.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "entity_type": "team",
                    "entity_id": "test_team",
                    "display_name": "Test Team",
                    "asset_slot": "primary_logo",
                    "target_path": "assets/leagues/softball/ausl/teams/test_team/logo.png",
                    "local_file_exists": "false",
                    "official_source_candidate": logo_source,
                    "source_tier": "official_candidate",
                    "manual_review_status": "review_required",
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                    "human_intake_file": "data/asset_registry/softball/softball_logo_review_intake.csv",
                    "review_only": "true",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                }
            ],
            [
                "sport_family",
                "league_id",
                "entity_type",
                "entity_id",
                "display_name",
                "asset_slot",
                "target_path",
                "local_file_exists",
                "official_source_candidate",
                "source_tier",
                "manual_review_status",
                "allowed_decisions",
                "human_intake_file",
                "review_only",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
            ],
        )
        write_csv(
            root / "softball_logo_review_intake.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "entity_type": "team",
                    "entity_id": "test_team",
                    "display_name": "Test Team",
                    "asset_slot": "primary_logo",
                    "target_path": "assets/leagues/softball/ausl/teams/test_team/logo.png",
                    "official_source_candidate": logo_source,
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                    "operator_decision": "operator_fill_required",
                    "source_reviewed": "operator_fill_required",
                    "identity_match": "operator_fill_required",
                    "source_url_to_record": "",
                    "registry_action": "",
                    "operator_notes": "",
                    "reviewed_by": "",
                    "reviewed_at_local": "",
                    "approval_scope": "",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                    "operator_priority": "P1",
                }
            ],
            [
                "sport_family",
                "league_id",
                "entity_type",
                "entity_id",
                "display_name",
                "asset_slot",
                "target_path",
                "official_source_candidate",
                "allowed_decisions",
                "operator_decision",
                "source_reviewed",
                "identity_match",
                "source_url_to_record",
                "registry_action",
                "operator_notes",
                "reviewed_by",
                "reviewed_at_local",
                "approval_scope",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
                "operator_priority",
            ],
        )
        write_csv(
            root / "softball_athlete_photo_contact_sheet.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "team_id": "test_team",
                    "team_name": "Test Team",
                    "player_id": "",
                    "display_name": "Test Player",
                    "candidate_id": "test_team_operator_add_candidate",
                    "candidate_status": "operator_add_candidate",
                    "source_url": roster_source,
                    "source_domain": "example.com",
                    "source_tier": "official_candidate",
                    "source_kind": "roster",
                    "photo_candidate_url": "",
                    "local_candidate_path": "assets/leagues/softball/ausl/athletes/test_team/operator_add_candidate/headshot.png",
                    "local_candidate_exists": "false",
                    "approved_marker_path": "assets/leagues/softball/ausl/athletes/test_team/operator_add_candidate/.approved",
                    "approved_marker_exists": "false",
                    "identity_review_status": "operator_add_identity_evidence",
                    "approval_status": "not_approved",
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_photo_candidate|hold_identity|revise_source_metadata",
                    "human_intake_file": "data/asset_registry/softball/softball_athlete_photo_review_intake.csv",
                    "team_review_board_path": "data/asset_registry/softball/athlete_photo_contact_sheets/test_team.md",
                    "review_only": "true",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                }
            ],
            [
                "sport_family",
                "league_id",
                "team_id",
                "team_name",
                "player_id",
                "display_name",
                "candidate_id",
                "candidate_status",
                "source_url",
                "source_domain",
                "source_tier",
                "source_kind",
                "photo_candidate_url",
                "local_candidate_path",
                "local_candidate_exists",
                "approved_marker_path",
                "approved_marker_exists",
                "identity_review_status",
                "approval_status",
                "allowed_decisions",
                "human_intake_file",
                "team_review_board_path",
                "review_only",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
            ],
        )
        write_csv(
            root / "softball_athlete_photo_review_intake.csv",
            [
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "team_id": "test_team",
                    "team_name": "Test Team",
                    "player_id": "",
                    "display_name": "Test Player",
                    "candidate_id": "test_team_operator_add_candidate",
                    "local_candidate_path": "assets/leagues/softball/ausl/athletes/test_team/operator_add_candidate/headshot.png",
                    "source_url": roster_source,
                    "photo_candidate_url": "",
                    "approval_status": "not_approved",
                    "identity_review_status": "operator_add_identity_evidence",
                    "allowed_decisions": "approve_for_review_only_renderer_use|deny_photo_candidate|hold_identity|revise_source_metadata",
                    "operator_decision": "operator_fill_required",
                    "identity_verified": "operator_fill_required",
                    "source_reviewed": "operator_fill_required",
                    "local_file_reviewed": "operator_fill_required",
                    "source_allowed_for_review_only": "operator_fill_required",
                    "rights_reviewed": "operator_fill_required",
                    "source_url_to_record": "",
                    "registry_action": "",
                    "operator_notes": "",
                    "reviewed_by": "",
                    "reviewed_at_local": "",
                    "approval_scope": "",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                    "operator_priority": "P1",
                }
            ],
            [
                "sport_family",
                "league_id",
                "team_id",
                "team_name",
                "player_id",
                "display_name",
                "candidate_id",
                "local_candidate_path",
                "source_url",
                "photo_candidate_url",
                "approval_status",
                "identity_review_status",
                "allowed_decisions",
                "operator_decision",
                "identity_verified",
                "source_reviewed",
                "local_file_reviewed",
                "source_allowed_for_review_only",
                "rights_reviewed",
                "source_url_to_record",
                "registry_action",
                "operator_notes",
                "reviewed_by",
                "reviewed_at_local",
                "approval_scope",
                "publish_ready",
                "auto_approval",
                "auto_publish",
                "move_files",
                "paid_apis",
                "asset_downloads",
                "operator_priority",
            ],
        )


def test_hockey_softball_source_review_helper_prefills_intakes_and_walkthroughs(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    seed_sport(tmp_path, "womens_hockey", "pwhl", "Professional Women's Hockey League", "https://www.thepwhl.com/en/teams/test_team", "https://www.thepwhl.com/en/teams/test_team/roster")
    seed_sport(tmp_path, "softball", "ausl", "Athletes Unlimited Softball League", "https://theausl.com/test_team", "https://theausl.com/test_team/roster")
    monkeypatch.setattr(
        "sys.argv",
        [
            "prepare_hsd_hockey_softball_source_review_intake_v1.py",
            "--reviewed-by",
            "Mike",
            "--reviewed-at-local",
            "2026-06-27 10:00 local",
        ],
    )

    assert module.main() == 0

    report = json.loads((tmp_path / "data/asset_registry/hockey_softball_source_review_helper_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "hockey_softball_source_review_helper_ready"
    assert report["guardrails"] == {
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "headshot_png_writes": False,
        "approved_marker_writes": False,
        "publish_ready_movement": False,
        "publishing": False,
    }
    assert {row["sport_family"]: (row["logo_prepared_rows"], row["athlete_prepared_rows"]) for row in report["summaries"]} == {
        "womens_hockey": (1, 1),
        "softball": (1, 1),
    }

    hockey_logo = read_csv(tmp_path / "data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv")[0]
    hockey_athlete = read_csv(tmp_path / "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv")[0]
    softball_logo = read_csv(tmp_path / "data/asset_registry/softball/softball_logo_review_intake.csv")[0]
    softball_athlete = read_csv(tmp_path / "data/asset_registry/softball/softball_athlete_photo_review_intake.csv")[0]

    assert hockey_logo["operator_decision"] == "hold_for_more_evidence"
    assert hockey_logo["source_reviewed"] == "yes"
    assert hockey_logo["identity_match"] == "yes"
    assert hockey_logo["registry_action"] == "hold_no_registry_state_change_until_local_logo_asset_exists"
    assert hockey_logo["reviewed_by"] == "Mike"
    assert hockey_logo["operator_priority"] == "P1"
    assert hockey_logo["publish_ready"] == "false"
    assert softball_logo["operator_decision"] == "hold_for_more_evidence"
    assert softball_logo["source_reviewed"] == "yes"
    assert softball_logo["identity_match"] == "yes"
    assert softball_logo["registry_action"] == "hold_no_registry_state_change_until_local_logo_asset_exists"
    assert softball_logo["reviewed_by"] == "Mike"
    assert softball_logo["operator_priority"] == "P1"
    assert softball_logo["publish_ready"] == "false"

    assert hockey_athlete["operator_decision"] == "hold_identity"
    assert hockey_athlete["identity_verified"] == "yes"
    assert hockey_athlete["source_reviewed"] == "yes"
    assert hockey_athlete["local_file_reviewed"] == "no"
    assert hockey_athlete["source_allowed_for_review_only"] == "yes"
    assert hockey_athlete["rights_reviewed"] == "yes"
    assert hockey_athlete["registry_action"] == "hold_no_registry_state_change"
    assert hockey_athlete["reviewed_by"] == "Mike"
    assert hockey_athlete["operator_priority"] == "P1"
    assert softball_athlete["operator_decision"] == "hold_identity"
    assert softball_athlete["identity_verified"] == "yes"
    assert softball_athlete["source_reviewed"] == "yes"
    assert softball_athlete["local_file_reviewed"] == "no"
    assert softball_athlete["source_allowed_for_review_only"] == "yes"
    assert softball_athlete["rights_reviewed"] == "yes"
    assert softball_athlete["registry_action"] == "hold_no_registry_state_change"
    assert softball_athlete["reviewed_by"] == "Mike"
    assert softball_athlete["operator_priority"] == "P1"

    assert "Review Order" in (tmp_path / "data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md").read_text(encoding="utf-8")
    assert "Test Team" in (tmp_path / "data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md").read_text(encoding="utf-8")
    assert "Review Order" in (tmp_path / "data/asset_registry/softball/softball_review_walkthrough.md").read_text(encoding="utf-8")
    assert "Test Team" in (tmp_path / "data/asset_registry/softball/softball_review_walkthrough.md").read_text(encoding="utf-8")
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))


def test_command_center_surfaces_hockey_softball_source_review_helper(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    seed_sport(tmp_path, "womens_hockey", "pwhl", "Professional Women's Hockey League", "https://www.thepwhl.com/en/teams/test_team", "https://www.thepwhl.com/en/teams/test_team/roster")
    seed_sport(tmp_path, "softball", "ausl", "Athletes Unlimited Softball League", "https://theausl.com/test_team", "https://theausl.com/test_team/roster")
    monkeypatch.setattr(
        "sys.argv",
        [
            "prepare_hsd_hockey_softball_source_review_intake_v1.py",
            "--reviewed-by",
            "Mike",
            "--reviewed-at-local",
            "2026-06-27 10:00 local",
        ],
    )
    assert module.main() == 0

    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    command_center = load_command_center_module()
    panel = command_center.asset_availability_readiness_panel()

    assert panel["hockey_softball_source_review_helper_status"] == "hockey_softball_source_review_helper_ready"
    assert panel["hockey_softball_source_review_helper_freshness_status"] == "packet_ready"
    assert panel["womens_hockey_review_walkthrough_rows"] == 2
    assert panel["softball_review_walkthrough_rows"] == 2
    shortcut_labels = {shortcut["label"] for shortcut in panel["file_shortcuts"]}
    assert "Hockey/softball source review helper report" in shortcut_labels
    assert "Women's hockey review walkthrough" in shortcut_labels
    assert "Softball review walkthrough" in shortcut_labels
