from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_womens_soccer_athlete_verification_queue_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_womens_soccer_athlete_verification_queue_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_womens_soccer_athlete_verification_queue_buckets_review_only_rows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    root = tmp_path / "data/asset_registry/womens_soccer"
    write_csv(
        root / "womens_soccer_athlete_photo_operator_board.csv",
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "candidate_rows": "2",
                "official_roster_candidate_rows": "2",
                "starter_candidate_rows": "0",
                "local_candidate_files_present": "0",
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
            },
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "bay_fc",
                "team_name": "Bay FC",
                "candidate_rows": "1",
                "official_roster_candidate_rows": "1",
                "starter_candidate_rows": "0",
                "local_candidate_files_present": "0",
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
            },
            {
                "scope_id": "europe_top_flight",
                "league_id": "wsl_england",
                "team_id": "chelsea_women",
                "team_name": "Chelsea Women",
                "candidate_rows": "1",
                "official_roster_candidate_rows": "0",
                "starter_candidate_rows": "1",
                "local_candidate_files_present": "0",
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
            },
        ],
        [
            "scope_id",
            "league_id",
            "team_id",
            "team_name",
            "candidate_rows",
            "official_roster_candidate_rows",
            "starter_candidate_rows",
            "local_candidate_files_present",
            "manual_intake_file",
            "download_intake_file",
        ],
    )
    write_csv(
        root / "womens_soccer_athlete_photo_contact_sheet.csv",
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "local_candidate_exists": "false",
                "source_domain": "www.nwslsoccer.com",
            },
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "local_candidate_exists": "false",
                "source_domain": "www.nwslsoccer.com",
            },
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "bay_fc",
                "team_name": "Bay FC",
                "local_candidate_exists": "false",
                "source_domain": "www.nwslsoccer.com",
            },
            {
                "scope_id": "europe_top_flight",
                "league_id": "wsl_england",
                "team_id": "chelsea_women",
                "team_name": "Chelsea Women",
                "local_candidate_exists": "false",
                "source_domain": "www.chelseafc.com",
            },
        ],
        ["scope_id", "league_id", "team_id", "team_name", "local_candidate_exists", "source_domain"],
    )
    write_csv(
        root / "womens_soccer_athlete_photo_download_intake.csv",
        [
            {"league_id": "nwsl", "team_id": "angel_city_fc", "download_approved": "no"},
            {"league_id": "nwsl", "team_id": "angel_city_fc", "download_approved": "no"},
            {"league_id": "nwsl", "team_id": "bay_fc", "download_approved": "no"},
            {"league_id": "wsl_england", "team_id": "chelsea_women", "download_approved": "no"},
        ],
        ["league_id", "team_id", "download_approved"],
    )
    write_csv(
        root / "external_research/womens_soccer_external_research_intake_board.csv",
        [
            {
                "research_lane": "nwsl_correction_enrichment",
                "operator_bucket": "p0_nwsl_operator_verify_first",
                "league_id": "nwsl",
                "team_name": "angel_city_fc",
                "player_name": "Angel Player",
                "issue_type": "roster_verify",
                "source_domain": "www.angelcity.com",
                "source_url": "https://www.angelcity.com/club/roster",
                "source_priority": "P0",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "nwsl_correction_enrichment",
                "operator_bucket": "p1_metadata_candidate_only",
                "league_id": "nwsl",
                "team_name": "bay_fc",
                "player_name": "Bay Player",
                "issue_type": "source_verify",
                "source_domain": "bayfc.com",
                "source_url": "https://bayfc.com/roster",
                "source_priority": "P1",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "europe_official_source_map",
                "operator_bucket": "europe_operator_verify_required",
                "league_id": "wsl_england",
                "team_name": "Chelsea Women",
                "player_name": "",
                "issue_type": "official_roster",
                "source_domain": "www.chelseafc.com",
                "source_url": "https://www.chelseafc.com/en/teams/women",
                "source_priority": "P0_OFFICIAL_CLUB_ROSTER",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "europe_official_source_map",
                "operator_bucket": "europe_operator_verify_required",
                "league_id": "wsl_england",
                "team_name": "Chelsea Women",
                "player_name": "Chelsea Player",
                "issue_type": "duplicate_same_source_page",
                "source_domain": "www.chelseafc.com",
                "source_url": "https://www.chelseafc.com/en/teams/women",
                "source_priority": "P0_OFFICIAL_CLUB_ROSTER",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "europe_official_source_map",
                "operator_bucket": "europe_gray_area_manual_verification_only",
                "league_id": "wsl_england",
                "team_name": "Backup",
                "player_name": "",
                "issue_type": "gray_area_backup",
                "source_domain": "example.org",
                "source_url": "https://example.org/wsl",
                "source_priority": "P1_GRAY_AREA",
                "official_status": "gray_area_public_source",
                "operator_verify_required": "yes",
            },
        ],
        [
            "research_lane",
            "operator_bucket",
            "league_id",
            "team_name",
            "player_name",
            "issue_type",
            "source_domain",
            "source_url",
            "source_priority",
            "official_status",
            "operator_verify_required",
        ],
    )
    module = load_module()

    assert module.main() == 0

    rows = read_csv(root / "womens_soccer_athlete_verification_queue.csv")
    manifest = json.loads((root / "womens_soccer_athlete_verification_queue.json").read_text(encoding="utf-8"))
    markdown = (root / "womens_soccer_athlete_verification_queue.md").read_text(encoding="utf-8")
    worksheet = read_csv(root / "womens_soccer_athlete_verification_next_actions.csv")
    worksheet_manifest = json.loads((root / "womens_soccer_athlete_verification_next_actions.json").read_text(encoding="utf-8"))
    worksheet_markdown = (root / "womens_soccer_athlete_verification_next_actions.md").read_text(encoding="utf-8")
    source_rows = read_csv(root / "womens_soccer_athlete_source_priority.csv")
    source_manifest = json.loads((root / "womens_soccer_athlete_source_priority.json").read_text(encoding="utf-8"))
    source_markdown = (root / "womens_soccer_athlete_source_priority.md").read_text(encoding="utf-8")
    triage_rows = read_csv(root / "womens_soccer_athlete_review_triage.csv")
    triage_manifest = json.loads((root / "womens_soccer_athlete_review_triage.json").read_text(encoding="utf-8"))
    triage_markdown = (root / "womens_soccer_athlete_review_triage.md").read_text(encoding="utf-8")
    candidate_rows = read_csv(root / "womens_soccer_athlete_candidate_next_action_board.csv")
    candidate_manifest = json.loads((root / "womens_soccer_athlete_candidate_next_action_board.json").read_text(encoding="utf-8"))
    candidate_markdown = (root / "womens_soccer_athlete_candidate_next_action_board.md").read_text(encoding="utf-8")
    photo_rows = read_csv(root / "womens_soccer_athlete_photo_review_readiness_board.csv")
    photo_manifest = json.loads((root / "womens_soccer_athlete_photo_review_readiness_board.json").read_text(encoding="utf-8"))
    photo_markdown = (root / "womens_soccer_athlete_photo_review_readiness_board.md").read_text(encoding="utf-8")
    focus_rows = read_csv(root / "womens_soccer_athlete_operator_focus.csv")
    focus_manifest = json.loads((root / "womens_soccer_athlete_operator_focus.json").read_text(encoding="utf-8"))
    focus_markdown = (root / "womens_soccer_athlete_operator_focus.md").read_text(encoding="utf-8")

    assert manifest["status"] == "athlete_verification_queue_ready"
    assert manifest["queue_rows"] == 3
    assert manifest["nwsl_team_rows"] == 2
    assert manifest["europe_league_rows"] == 1
    assert manifest["p0_nwsl_roster_verification_rows"] == 1
    assert manifest["gray_area_rows"] == 1
    assert manifest["missing_local_candidate_rows"] == 4
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["first_action_bucket_counts"] == {
        "1_roster_verification": 1,
        "2_source_verification_gray_or_reputable": 1,
        "3_missing_local_candidate_asset": 1,
    }
    assert manifest["next_action_rows"] == 2
    assert manifest["next_action_download_approved_yes_rows"] == 0
    assert manifest["next_action_blank_source_url_rows"] == 2
    assert manifest["source_priority_rows"] == 4
    assert manifest["source_priority_operator_verify_required_rows"] == 4
    assert manifest["source_priority_gray_or_reputable_rows"] == 1
    assert manifest["source_priority_download_approved_yes_rows"] == 0
    assert manifest["source_priority_blank_source_url_rows"] == 4
    assert manifest["review_triage_rows"] == 3
    assert manifest["review_triage_download_approved_yes_rows"] == 0
    assert manifest["review_triage_blank_source_url_rows"] == 3
    assert manifest["review_triage_primary_action_counts"] == {
        "gray_area_reputable_lead_review": 1,
        "identity_verification": 1,
        "official_roster_check": 1,
    }
    assert manifest["candidate_next_action_rows"] == 4
    assert manifest["candidate_next_action_download_approved_yes_rows"] == 0
    assert manifest["candidate_next_action_blank_source_url_rows"] == 4
    assert manifest["candidate_next_action_manual_action_counts"] == {
        "duplicate_transfer_check": 1,
        "gray_area_reputable_media_lead": 1,
        "roster_source_verify": 2,
    }
    assert manifest["photo_review_readiness_rows"] == 4
    assert manifest["photo_review_readiness_download_approved_yes_rows"] == 0
    assert manifest["photo_review_readiness_blank_source_url_rows"] == 4
    assert manifest["photo_review_readiness_bucket_counts"] == {
        "nwsl_roster_verify_before_photo_review": 2,
        "park_gray_area_lead_no_photo_use": 1,
        "resolve_duplicate_transfer_before_photo_review": 1,
    }
    assert manifest["operator_focus_rows"] == 4
    assert manifest["operator_focus_p0_rows"] == 2
    assert manifest["operator_focus_p1_rows"] == 2
    assert manifest["operator_focus_duplicate_transfer_loan_stale_rows"] == 1
    assert manifest["operator_focus_profile_gap_rows"] == 0
    assert manifest["operator_focus_download_approved_yes_rows"] == 0
    assert manifest["operator_focus_blank_source_url_rows"] == 4
    assert manifest["operator_focus_bucket_counts"] == {
        "1_duplicate_transfer_loan_stale_profile_check": 1,
        "2_p0_roster_or_source_verify": 1,
        "4_gray_area_or_reputable_lead": 1,
        "5_p1_source_followup": 1,
    }
    by_team = {row["team_id"]: row for row in rows}
    assert by_team["angel_city_fc"]["queue_bucket"] == "p0_nwsl_roster_verification_first"
    assert by_team["angel_city_fc"]["first_action_bucket"] == "1_roster_verification"
    assert by_team["angel_city_fc"]["source_verification_bucket"] == "official_source_manual_verify"
    assert by_team["angel_city_fc"]["download_law_status"] == "future_quarantine_download_intake_required"
    assert by_team["bay_fc"]["queue_bucket"] == "p1_nwsl_local_candidate_assets_missing"
    assert by_team["bay_fc"]["first_action_bucket"] == "3_missing_local_candidate_asset"
    assert by_team["all_teams"]["queue_bucket"] == "p1_europe_gray_area_source_review"
    assert by_team["all_teams"]["first_action_bucket"] == "2_source_verification_gray_or_reputable"
    assert by_team["all_teams"]["render_readiness"] == "not_render_ready_source_candidate_only"
    for row in rows:
        assert row["review_only"] == "true"
        assert row["approval_state_change"] == "false"
        assert row["candidate_state_change"] == "false"
        assert row["asset_downloads"] == "false"
        assert row["headshot_writes"] == "false"
        assert row["approved_marker_writes"] == "false"
        assert row["publish_ready"] == "false"
        assert row["auto_approval"] == "false"
        assert row["auto_publish"] == "false"
        assert row["move_files"] == "false"
        assert row["paid_apis"] == "false"
    assert "does not download images" in markdown
    assert "Europe rows as source-map candidates only" in markdown
    assert worksheet_manifest["status"] == "athlete_verification_next_actions_ready"
    assert worksheet_manifest["worksheet_rows"] == 2
    assert worksheet_manifest["download_approved_yes_rows"] == 0
    assert worksheet_manifest["blank_source_url_rows"] == 2
    assert [row["team_id"] for row in worksheet] == ["angel_city_fc", "bay_fc"]
    for row in worksheet:
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["candidate_entity_id"]
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["operator_decision"] == ""
        assert row["asset_downloads"] == "false"
        assert row["approval_state_change"] == "false"
    assert "Generated rows default to `download_approved=no`" in worksheet_markdown
    assert source_manifest["status"] == "athlete_source_priority_ready"
    assert source_manifest["source_priority_rows"] == 4
    assert source_manifest["nwsl_source_rows"] == 2
    assert source_manifest["europe_source_rows"] == 2
    assert source_manifest["operator_verify_required_rows"] == 4
    assert source_manifest["gray_or_reputable_manual_verify_rows"] == 1
    assert source_manifest["download_approved_yes_rows"] == 0
    assert source_manifest["blank_source_url_rows"] == 4
    assert source_manifest["source_review_bucket_counts"] == {
        "1_nwsl_p0_roster_source_check": 1,
        "2_gray_area_or_reputable_manual_verify": 1,
        "3_operator_verify_required_official": 2,
    }
    assert len(
        {
            (
                row["league_id"],
                row["candidate_entity_id"],
                row["source_candidate_url"],
            )
            for row in source_rows
        }
    ) == len(source_rows)
    assert [row["source_review_bucket"] for row in source_rows] == [
        "1_nwsl_p0_roster_source_check",
        "2_gray_area_or_reputable_manual_verify",
        "3_operator_verify_required_official",
        "3_operator_verify_required_official",
    ]
    for row in source_rows:
        assert row["source_candidate_url"]
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["candidate_entity_id"]
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["operator_decision"] == ""
        assert row["review_only"] == "true"
        assert row["asset_downloads"] == "false"
        assert row["approval_state_change"] == "false"
        assert row["publish_ready"] == "false"
    assert source_rows[0]["team_id"] == "angel_city_fc"
    assert source_rows[0]["source_priority"] == "P0"
    assert source_rows[0]["linked_queue_bucket"] == "p0_nwsl_roster_verification_first"
    assert source_rows[1]["render_readiness"] == "not_render_ready_source_candidate_only"
    chelsea_row = next(row for row in source_rows if row["team_name"] == "Chelsea Women")
    assert chelsea_row["player_name"] == "Chelsea Player"
    assert "official_roster" in chelsea_row["issue_type"]
    assert "duplicate_same_source_page" in chelsea_row["issue_type"]
    assert "source_candidate_url` is advisory metadata" in source_markdown
    assert "download-law `source_url` field remains blank" in source_markdown
    assert triage_manifest["status"] == "athlete_review_triage_ready"
    assert triage_manifest["triage_rows"] == 3
    assert triage_manifest["nwsl_rows"] == 2
    assert triage_manifest["europe_rows"] == 1
    assert triage_manifest["download_approved_yes_rows"] == 0
    assert triage_manifest["blank_source_url_rows"] == 3
    assert triage_manifest["blank_entity_id_rows"] == 3
    assert triage_manifest["primary_manual_action_counts"] == {
        "gray_area_reputable_lead_review": 1,
        "identity_verification": 1,
        "official_roster_check": 1,
    }
    assert [row["primary_manual_action"] for row in triage_rows] == [
        "official_roster_check",
        "gray_area_reputable_lead_review",
        "identity_verification",
    ]
    assert len({(row["scope_id"], row["league_id"], row["team_id"]) for row in triage_rows}) == len(triage_rows)
    by_triage_team = {row["team_id"]: row for row in triage_rows}
    assert by_triage_team["angel_city_fc"]["action_flags"].startswith("official_roster_check")
    assert "identity_verification" in by_triage_team["bay_fc"]["action_flags"]
    assert "future_quarantine_download_intake_prep" in by_triage_team["bay_fc"]["action_flags"]
    assert "gray_area_reputable_lead_review" in by_triage_team["all_teams"]["action_flags"]
    for row in triage_rows:
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["candidate_entity_id"]
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["review_only"] == "true"
        assert row["asset_downloads"] == "false"
        assert row["approval_state_change"] == "false"
        assert row["publish_ready"] == "false"
    assert "Review-only operator triage worksheet" in triage_markdown
    assert "generated local-download-law fields stay `download_approved=no`" in triage_markdown
    assert candidate_manifest["status"] == "athlete_candidate_next_actions_ready"
    assert candidate_manifest["candidate_action_rows"] == 4
    assert candidate_manifest["nwsl_rows"] == 2
    assert candidate_manifest["europe_rows"] == 2
    assert candidate_manifest["download_approved_yes_rows"] == 0
    assert candidate_manifest["blank_source_url_rows"] == 4
    assert candidate_manifest["blank_entity_id_rows"] == 4
    assert candidate_manifest["manual_action_group_counts"] == {
        "duplicate_transfer_check": 1,
        "gray_area_reputable_media_lead": 1,
        "roster_source_verify": 2,
    }
    assert [row["manual_action_group"] for row in candidate_rows] == [
        "roster_source_verify",
        "roster_source_verify",
        "gray_area_reputable_media_lead",
        "duplicate_transfer_check",
    ]
    assert len(
        {
            (
                row["manual_action_group"],
                row["league_id"],
                row["candidate_entity_id"],
                row["source_candidate_url"],
            )
            for row in candidate_rows
        }
    ) == len(candidate_rows)
    for row in candidate_rows:
        assert row["source_candidate_url"]
        assert "womens_soccer_athlete_source_priority.csv#row=" in row["source_priority_row_ref"]
        assert "womens_soccer_athlete_review_triage.csv#row=" in row["triage_row_ref"]
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["review_only"] == "true"
        assert row["asset_downloads"] == "false"
        assert row["approval_state_change"] == "false"
        assert row["publish_ready"] == "false"
    assert "Review-only board" in candidate_markdown
    assert "`source_candidate_url` remains advisory metadata" in candidate_markdown
    assert photo_manifest["status"] == "athlete_photo_review_readiness_ready"
    assert photo_manifest["photo_readiness_rows"] == 4
    assert photo_manifest["nwsl_rows"] == 2
    assert photo_manifest["europe_rows"] == 2
    assert photo_manifest["download_approved_yes_rows"] == 0
    assert photo_manifest["blank_source_url_rows"] == 4
    assert photo_manifest["blank_entity_id_rows"] == 4
    assert photo_manifest["readiness_bucket_counts"] == {
        "nwsl_roster_verify_before_photo_review": 2,
        "park_gray_area_lead_no_photo_use": 1,
        "resolve_duplicate_transfer_before_photo_review": 1,
    }
    assert [row["photo_review_readiness_bucket"] for row in photo_rows] == [
        "nwsl_roster_verify_before_photo_review",
        "nwsl_roster_verify_before_photo_review",
        "resolve_duplicate_transfer_before_photo_review",
        "park_gray_area_lead_no_photo_use",
    ]
    assert len(
        {
            (
                row["photo_review_readiness_bucket"],
                row["league_id"],
                row["candidate_entity_id"],
                row["source_candidate_url"],
            )
            for row in photo_rows
        }
    ) == len(photo_rows)
    for row in photo_rows:
        assert row["source_candidate_url"]
        assert "womens_soccer_athlete_candidate_next_action_board.csv#row=" in row["candidate_action_row_ref"]
        assert "womens_soccer_athlete_source_priority.csv#row=" in row["source_priority_row_ref"]
        assert row["future_download_intake_status"] == "human_edited_intake_required_no_generated_authorization"
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["review_only"] == "true"
        assert row["asset_downloads"] == "false"
        assert row["approval_state_change"] == "false"
        assert row["publish_ready"] == "false"
    assert "Photo Review Readiness Board" in photo_markdown
    assert "Generated local-download-law fields stay `download_approved=no`" in photo_markdown
    assert focus_manifest["status"] == "athlete_operator_focus_ready"
    assert focus_manifest["focus_rows"] == 4
    assert focus_manifest["p0_rows"] == 2
    assert focus_manifest["p1_rows"] == 2
    assert focus_manifest["duplicate_transfer_loan_stale_rows"] == 1
    assert focus_manifest["profile_gap_rows"] == 0
    assert focus_manifest["download_approved_yes_rows"] == 0
    assert focus_manifest["blank_source_url_rows"] == 4
    assert focus_manifest["focus_bucket_counts"] == {
        "1_duplicate_transfer_loan_stale_profile_check": 1,
        "2_p0_roster_or_source_verify": 1,
        "4_gray_area_or_reputable_lead": 1,
        "5_p1_source_followup": 1,
    }
    assert [row["focus_bucket"] for row in focus_rows] == [
        "1_duplicate_transfer_loan_stale_profile_check",
        "2_p0_roster_or_source_verify",
        "4_gray_area_or_reputable_lead",
        "5_p1_source_followup",
    ]
    for row in focus_rows:
        assert "womens_soccer_athlete_source_priority.csv#row=" in row["open_next_row_ref"]
        assert "womens_soccer_athlete_source_priority.csv#row=" in row["source_priority_row_ref"]
        assert "womens_soccer_athlete_candidate_next_action_board.csv#row=" in row["candidate_action_row_ref"]
        assert row["why_row_matters"]
        assert "Do not download assets" in row["do_not_do"]
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["review_only"] == "true"
        assert row["asset_downloads"] == "false"
        assert row["approval_state_change"] == "false"
        assert row["publish_ready"] == "false"
    duplicate_focus = focus_rows[0]
    assert duplicate_focus["player_name"] == "Chelsea Player"
    assert "duplicate_transfer_loan_stale_or_short_term_issue" in duplicate_focus["focus_reason_flags"]
    assert "triage_row_ref" in focus_markdown
    assert "Do not download assets" in focus_markdown
