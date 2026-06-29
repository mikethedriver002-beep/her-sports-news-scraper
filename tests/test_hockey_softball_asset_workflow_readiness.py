from __future__ import annotations

import importlib.util
import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FOUNDATION_SCRIPT = REPO / "scripts" / "generate_hsd_hockey_softball_asset_foundation_v1.py"
HELPER_SCRIPT = REPO / "scripts" / "prepare_hsd_hockey_softball_source_review_intake_v1.py"
WORKFLOW_SCRIPT = REPO / "scripts" / "report_hsd_hockey_softball_asset_workflow_readiness_v1.py"


def load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_command_center_module():
    return load_module(REPO / "generate_hsd_operator_command_center_v2.py", "generate_hsd_operator_command_center_v2")


def seed_hockey_softball_review_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))

    foundation = load_module(FOUNDATION_SCRIPT, "generate_hsd_hockey_softball_asset_foundation_v1")
    foundation.PROJECT_ROOT = tmp_path
    assert foundation.main() == 0

    helper = load_module(HELPER_SCRIPT, "prepare_hsd_hockey_softball_source_review_intake_v1")
    monkeypatch.setattr(
        "sys.argv",
        [
            "prepare_hsd_hockey_softball_source_review_intake_v1.py",
            "--reviewed-by",
            "Mike",
            "--reviewed-at-local",
            "2026-06-27 11:00 local",
        ],
    )
    assert helper.main() == 0


def test_hockey_softball_asset_workflow_readiness_reports_review_only_clarity(tmp_path: Path, monkeypatch) -> None:
    seed_hockey_softball_review_packet(tmp_path, monkeypatch)
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")

    assert workflow.main() == 0

    report_path = tmp_path / "data/asset_registry/hockey_softball_asset_workflow_readiness_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "hockey_softball_asset_workflow_readiness_ready"
    assert report["guardrails"] == {
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "approval_state_changes": False,
        "headshot_png_writes": False,
        "approved_marker_writes": False,
        "publish_ready_movement": False,
        "publishing": False,
    }
    assert report["totals"]["workflow_rows"] == 74
    assert report["totals"]["logo_contact_rows"] == 20
    assert report["totals"]["athlete_candidate_rows"] == 54
    assert report["totals"]["proposed_headshot_path_refs"] == 54
    assert report["totals"]["proposed_approved_marker_path_refs"] == 54
    assert report["totals"]["local_candidate_files_present"] == 0
    assert report["totals"]["approved_marker_files_present"] == 0
    assert report["totals"]["unsafe_intake_rows"] == 0
    assert report["totals"]["action_queue_rows"] == 74
    assert report["totals"]["source_candidate_only_rows"] == 74
    assert report["totals"]["local_asset_present_rows"] == 0
    assert report["totals"]["batch_source_review_rows"] == 74
    assert report["totals"]["batch_source_review_now_rows"] == 54
    assert report["totals"]["batch_source_review_next_rows"] == 10
    assert report["totals"]["batch_source_review_local_asset_needed_later_rows"] == 74
    assert report["totals"]["next_decision_worksheet_rows"] == 74
    assert report["totals"]["next_decision_logo_rows"] == 20
    assert report["totals"]["next_decision_athlete_rows"] == 54
    assert report["totals"]["next_decision_missing_local_candidate_asset_rows"] == 74
    assert report["totals"]["next_decision_download_approved_yes_rows"] == 0
    assert report["totals"]["next_decision_blank_download_metadata_rows"] == 74
    assert report["totals"]["source_priority_rows"] == 74
    assert report["totals"]["source_priority_logo_rows"] == 20
    assert report["totals"]["source_priority_athlete_rows"] == 54
    assert report["totals"]["source_priority_operator_verify_required_rows"] == 54
    assert report["totals"]["source_priority_download_approved_yes_rows"] == 0
    assert report["totals"]["source_priority_blank_source_url_rows"] == 74
    assert report["totals"]["source_verification_checklist_rows"] == 18
    assert report["totals"]["source_verification_checklist_womens_hockey_rows"] == 12
    assert report["totals"]["source_verification_checklist_softball_rows"] == 6
    assert report["totals"]["source_verification_checklist_download_approved_yes_rows"] == 0
    assert report["totals"]["source_verification_checklist_blank_source_url_rows"] == 18
    assert report["totals"]["source_verification_checklist_blank_human_review_rows"] == 18
    assert report["totals"]["intake_readiness_summary_groups"] == 4
    assert report["totals"]["intake_readiness_rows_covered"] == 74
    assert report["totals"]["intake_readiness_logo_source_reviewed_rows"] == 20
    assert report["totals"]["intake_readiness_athlete_source_pending_rows"] == 54
    assert report["totals"]["intake_readiness_blank_human_metadata_rows"] == 54
    assert report["totals"]["intake_readiness_unsafe_guardrail_rows"] == 0
    assert report["totals"]["intake_readiness_download_approved_yes_rows"] == 0
    assert report["totals"]["intake_readiness_blank_source_url_rows"] == 4
    assert report["totals"]["source_map_rows"] == 12
    assert report["totals"]["source_map_womens_hockey_rows"] == 6
    assert report["totals"]["source_map_softball_rows"] == 6
    assert report["totals"]["source_map_official_free_public_rows"] == 6
    assert report["totals"]["source_map_download_approved_yes_rows"] == 0
    assert report["totals"]["source_map_allowed_for_download_approved_yes_rows"] == 0
    assert report["totals"]["source_map_blank_source_url_rows"] == 12
    assert report["totals"]["source_research_return_intake_rows"] == 8
    assert report["totals"]["source_research_return_intake_womens_hockey_rows"] == 4
    assert report["totals"]["source_research_return_intake_softball_rows"] == 4
    assert report["totals"]["source_research_return_intake_blank_operator_rows"] == 8
    assert report["totals"]["source_research_return_intake_download_approved_yes_rows"] == 0
    assert report["totals"]["review_triage_rows"] == 38
    assert report["totals"]["review_triage_logo_rows"] == 20
    assert report["totals"]["review_triage_athlete_rows"] == 18
    assert report["totals"]["review_triage_operator_verify_required_source_rows"] == 54
    assert report["totals"]["review_triage_download_approved_yes_rows"] == 0
    assert report["totals"]["review_triage_blank_source_url_rows"] == 38
    assert report["totals"]["asset_review_readiness_rows"] == 38
    assert report["totals"]["asset_review_readiness_logo_rows"] == 20
    assert report["totals"]["asset_review_readiness_athlete_rows"] == 18
    assert report["totals"]["asset_review_readiness_download_approved_yes_rows"] == 0
    assert report["totals"]["asset_review_readiness_blank_source_url_rows"] == 38
    assert report["totals"]["asset_review_readiness_source_identity_gap_rows"] == 38
    assert report["totals"]["asset_review_readiness_team_entity_check_rows"] == 38
    assert report["totals"]["asset_review_readiness_local_candidate_gap_rows"] == 38
    assert report["totals"]["manual_verification_focus_rows"] == 46
    assert report["totals"]["manual_verification_focus_p0_rows"] == 24
    assert report["totals"]["manual_verification_focus_p1_rows"] == 22
    assert report["totals"]["manual_verification_focus_asset_readiness_rows"] == 38
    assert report["totals"]["manual_verification_focus_source_map_rows"] == 8
    assert report["totals"]["manual_verification_focus_download_approved_yes_rows"] == 0
    assert report["totals"]["manual_verification_focus_blank_source_url_rows"] == 46
    assert report["totals"]["next_action_card_rows"] == 38
    assert report["totals"]["next_action_card_logo_rows"] == 20
    assert report["totals"]["next_action_card_athlete_rows"] == 18
    assert report["totals"]["next_action_card_download_approved_yes_rows"] == 0
    assert report["totals"]["next_action_card_blank_source_url_rows"] == 38
    assert report["totals"]["quarantine_download_intake_rows"] == 74
    assert report["totals"]["quarantine_download_logo_rows"] == 20
    assert report["totals"]["quarantine_download_athlete_rows"] == 54
    assert report["totals"]["quarantine_download_source_reviewed_rows"] == 20
    assert report["totals"]["quarantine_download_approved_yes_rows"] == 0
    assert report["action_queue"] == {
        "md": "data/asset_registry/hockey_softball_asset_review_action_queue.md",
        "csv": "data/asset_registry/hockey_softball_asset_review_action_queue.csv",
        "json": "data/asset_registry/hockey_softball_asset_review_action_queue.json",
        "rows": 74,
    }
    assert report["batch_source_review_helper"] == {
        "md": "data/asset_registry/hockey_softball_batch_source_review_helper.md",
        "csv": "data/asset_registry/hockey_softball_batch_source_review_helper.csv",
        "json": "data/asset_registry/hockey_softball_batch_source_review_helper.json",
        "rows": 74,
        "source_review_now_rows": 54,
        "next_rows": 10,
    }
    assert report["next_decision_worksheet"] == {
        "md": "data/asset_registry/hockey_softball_next_decision_worksheet.md",
        "csv": "data/asset_registry/hockey_softball_next_decision_worksheet.csv",
        "json": "data/asset_registry/hockey_softball_next_decision_worksheet.json",
        "rows": 74,
        "logo_rows": 20,
        "athlete_rows": 54,
        "missing_local_candidate_asset_rows": 74,
        "download_approved_yes_rows": 0,
        "blank_download_metadata_rows": 74,
    }
    assert report["source_priority_worksheet"] == {
        "md": "data/asset_registry/hockey_softball_source_priority_worksheet.md",
        "csv": "data/asset_registry/hockey_softball_source_priority_worksheet.csv",
        "json": "data/asset_registry/hockey_softball_source_priority_worksheet.json",
        "rows": 74,
        "logo_rows": 20,
        "athlete_rows": 54,
        "operator_verify_required_rows": 54,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 74,
    }
    assert report["source_verification_checklist"] == {
        "md": "data/asset_registry/hockey_softball_source_verification_checklist.md",
        "csv": "data/asset_registry/hockey_softball_source_verification_checklist.csv",
        "json": "data/asset_registry/hockey_softball_source_verification_checklist.json",
        "rows": 18,
        "womens_hockey_rows": 12,
        "softball_rows": 6,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 18,
        "blank_human_review_rows": 18,
    }
    assert report["intake_readiness_summary"] == {
        "md": "data/asset_registry/hockey_softball_intake_readiness_summary.md",
        "csv": "data/asset_registry/hockey_softball_intake_readiness_summary.csv",
        "json": "data/asset_registry/hockey_softball_intake_readiness_summary.json",
        "groups": 4,
        "rows_covered": 74,
        "logo_source_reviewed_rows": 20,
        "athlete_source_pending_rows": 54,
        "blank_human_review_metadata_rows": 54,
        "unsafe_guardrail_rows": 0,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 4,
    }
    assert report["source_map_board"] == {
        "md": "data/asset_registry/hockey_softball_source_map_board.md",
        "csv": "data/asset_registry/hockey_softball_source_map_board.csv",
        "json": "data/asset_registry/hockey_softball_source_map_board.json",
        "rows": 12,
        "womens_hockey_rows": 6,
        "softball_rows": 6,
        "official_free_public_rows": 6,
        "download_approved_yes_rows": 0,
        "allowed_for_download_approved_yes_rows": 0,
        "blank_source_url_rows": 12,
    }
    assert report["source_research_return_intake"] == {
        "md": "data/asset_registry/hockey_softball_source_research_return_intake.md",
        "csv": "data/asset_registry/hockey_softball_source_research_return_intake.csv",
        "json": "data/asset_registry/hockey_softball_source_research_return_intake.json",
        "rows": 8,
        "womens_hockey_rows": 4,
        "softball_rows": 4,
        "blank_operator_return_rows": 8,
        "download_approved_yes_rows": 0,
    }
    assert report["review_triage"] == {
        "md": "data/asset_registry/hockey_softball_asset_review_triage.md",
        "csv": "data/asset_registry/hockey_softball_asset_review_triage.csv",
        "json": "data/asset_registry/hockey_softball_asset_review_triage.json",
        "rows": 38,
        "logo_rows": 20,
        "athlete_rows": 18,
        "operator_verify_required_source_rows": 54,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 38,
    }
    assert report["asset_review_readiness"] == {
        "md": "data/asset_registry/hockey_softball_asset_review_readiness_board.md",
        "csv": "data/asset_registry/hockey_softball_asset_review_readiness_board.csv",
        "json": "data/asset_registry/hockey_softball_asset_review_readiness_board.json",
        "rows": 38,
        "logo_rows": 20,
        "athlete_rows": 18,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 38,
        "source_identity_gap_rows": 38,
        "team_entity_check_rows": 38,
        "local_candidate_gap_rows": 38,
    }
    assert report["manual_verification_focus"] == {
        "md": "data/asset_registry/hockey_softball_manual_verification_focus.md",
        "csv": "data/asset_registry/hockey_softball_manual_verification_focus.csv",
        "json": "data/asset_registry/hockey_softball_manual_verification_focus.json",
        "rows": 46,
        "p0_rows": 24,
        "p1_rows": 22,
        "asset_readiness_rows": 38,
        "source_map_rows": 8,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 46,
    }
    assert report["next_action_cards"] == {
        "md": "data/asset_registry/hockey_softball_asset_next_action_cards.md",
        "csv": "data/asset_registry/hockey_softball_asset_next_action_cards.csv",
        "json": "data/asset_registry/hockey_softball_asset_next_action_cards.json",
        "rows": 38,
        "logo_rows": 20,
        "athlete_rows": 18,
        "download_approved_yes_rows": 0,
        "blank_source_url_rows": 38,
    }
    assert report["quarantine_download_intake"] == {
        "md": "data/asset_registry/hockey_softball_quarantine_download_intake.md",
        "csv": "data/asset_registry/hockey_softball_quarantine_download_intake.csv",
        "json": "data/asset_registry/hockey_softball_quarantine_download_intake.json",
        "rows": 74,
        "logo_rows": 20,
        "athlete_rows": 54,
        "source_reviewed_rows": 20,
        "download_approved_yes_rows": 0,
        "quarantine_folder": "data/assets/quarantine/review_only_candidates",
    }

    action_queue_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_action_queue.json"
    action_queue = json.loads(action_queue_path.read_text(encoding="utf-8"))
    assert action_queue["status"] == "hockey_softball_asset_review_action_queue_ready"
    assert action_queue["rows"] == 74
    assert action_queue["source_candidate_only_rows"] == 74
    assert action_queue["local_asset_present_rows"] == 0
    athlete_row = next(row for row in action_queue["action_rows"] if row["asset_domain"] == "athlete_photo")
    assert athlete_row["review_state"] == "source_candidate_only_local_asset_missing"
    assert athlete_row["local_asset_present"] == "no"
    assert athlete_row["current_source_reviewed"] == "no"
    assert athlete_row["current_identity_status"] == "no"
    assert "reviewed_by; reviewed_at_local" in athlete_row["fields_to_keep_blank_until_review"]
    assert "identity_verified=no until named athlete evidence" in athlete_row["fields_that_must_remain_hold"]
    assert "fill only source-review fields" in athlete_row["next_human_action"]
    logo_row = next(row for row in action_queue["action_rows"] if row["asset_domain"] == "logo")
    assert logo_row["review_state"] == "source_candidate_only_local_logo_missing"
    assert logo_row["board_to_open"].endswith("_logo_contact_sheet.md")
    assert logo_row["intake_to_fill"].endswith("_logo_review_intake.csv")
    csv_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_action_queue.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 74
    assert list(csv_rows[0].keys()) == workflow.ACTION_QUEUE_FIELDS
    assert csv_rows[0]["fields_to_keep_blank_until_review"] == "reviewed_by; reviewed_at_local; source_url_to_record"
    batch_path = tmp_path / "data/asset_registry/hockey_softball_batch_source_review_helper.json"
    batch_helper = json.loads(batch_path.read_text(encoding="utf-8"))
    assert batch_helper["status"] == "hockey_softball_batch_source_review_helper_ready"
    assert batch_helper["rows"] == 74
    assert batch_helper["source_review_now_rows"] == 54
    assert batch_helper["local_asset_needed_later_rows"] == 74
    assert len(batch_helper["next_review_rows"]) == 10
    assert all(row["batch_bucket"] == "source_review_now" for row in batch_helper["next_review_rows"])
    assert all(row["asset_domain"] == "athlete_photo" for row in batch_helper["next_review_rows"])
    assert batch_helper["next_review_rows"][0]["batch_position"] == "next_01"
    assert "source_reviewed" in batch_helper["next_review_rows"][0]["fields_mike_can_fill_now"]
    assert "identity_verified" in batch_helper["next_review_rows"][0]["fields_to_keep_blank_or_held"]
    assert "headshot.png" in batch_helper["next_review_rows"][0]["do_not_touch"]
    batch_csv_path = tmp_path / "data/asset_registry/hockey_softball_batch_source_review_helper.csv"
    with batch_csv_path.open(newline="", encoding="utf-8") as handle:
        batch_csv_rows = list(csv.DictReader(handle))
    assert len(batch_csv_rows) == 74
    assert list(batch_csv_rows[0].keys()) == workflow.BATCH_SOURCE_REVIEW_FIELDS
    assert sum(1 for row in batch_csv_rows if row["batch_position"]) == 10
    worksheet_path = tmp_path / "data/asset_registry/hockey_softball_next_decision_worksheet.json"
    worksheet = json.loads(worksheet_path.read_text(encoding="utf-8"))
    assert worksheet["status"] == "hockey_softball_next_decision_worksheet_ready"
    assert worksheet["rows"] == 74
    assert worksheet["logo_rows"] == 20
    assert worksheet["athlete_rows"] == 54
    assert worksheet["first_action_bucket_counts"] == {
        "1_source_verification": 54,
        "2_missing_local_candidate_asset": 20,
    }
    assert worksheet["source_verification_bucket_counts"] == {
        "official_league_or_team_source_manual_verify": 54,
        "source_reviewed_waiting_for_local_asset": 20,
    }
    assert worksheet["missing_local_candidate_asset_rows"] == 74
    assert worksheet["download_approved_yes_rows"] == 0
    assert worksheet["blank_download_metadata_rows"] == 74
    assert worksheet["future_download_required_fields"] == [
        "download_approved",
        "source_url",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
    ]
    assert worksheet["quarantine_folder"] == "data/assets/quarantine/review_only_candidates"
    blank_fields = set(worksheet["blank_human_decision_fields"])
    assert {
        "operator_source_reviewed",
        "operator_source_allowed_for_review_only",
        "operator_identity_match",
        "operator_rights_reviewed",
        "operator_decision",
        "source_url_to_record",
        "operator_notes",
        "reviewed_by",
        "reviewed_at_local",
    } <= blank_fields
    assert all(row["local_asset_needed_later"] == "yes" for row in worksheet["worksheet_rows"])
    assert all(row["missing_local_candidate_asset"] == "yes" for row in worksheet["worksheet_rows"])
    assert all(row["download_approved"] == "no" for row in worksheet["worksheet_rows"])
    assert all(row["quarantine_folder"] == "data/assets/quarantine/review_only_candidates" for row in worksheet["worksheet_rows"])
    assert all(
        row["future_download_required_fields"]
        == "download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use"
        for row in worksheet["worksheet_rows"]
    )
    assert all(
        row[field] == ""
        for row in worksheet["worksheet_rows"]
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["guardrail_note"].startswith("review-only worksheet") for row in worksheet["worksheet_rows"])
    assert all(row[field] == "" for row in worksheet["worksheet_rows"] for field in blank_fields)
    assert {row["worksheet_section"] for row in worksheet["worksheet_rows"]} == {
        "logo_wait_for_local_asset_after_source_review",
        "athlete_source_only_review",
    }
    logo_worksheet_row = next(row for row in worksheet["worksheet_rows"] if row["asset_domain"] == "logo")
    athlete_worksheet_row = next(row for row in worksheet["worksheet_rows"] if row["asset_domain"] == "athlete_photo")
    assert athlete_worksheet_row["first_action_bucket"] == "1_source_verification"
    assert athlete_worksheet_row["source_verification_bucket"] == "official_league_or_team_source_manual_verify"
    assert athlete_worksheet_row["download_law_status"] == "future_quarantine_download_intake_required"
    assert logo_worksheet_row["first_action_bucket"] == "2_missing_local_candidate_asset"
    assert logo_worksheet_row["source_verification_bucket"] == "source_reviewed_waiting_for_local_asset"
    assert logo_worksheet_row["fields_mike_can_fill_now"].startswith("none; source and identity are already recorded")
    assert "do not restamp reviewed_by/reviewed_at_local" in logo_worksheet_row["fields_that_must_stay_blank"]
    assert "source_allowed_for_review_only" in athlete_worksheet_row["fields_mike_can_fill_now"]
    assert "identity_verified" in athlete_worksheet_row["fields_that_must_stay_blank"]
    assert "headshot.png" in athlete_worksheet_row["do_not_touch"]
    worksheet_csv_path = tmp_path / "data/asset_registry/hockey_softball_next_decision_worksheet.csv"
    with worksheet_csv_path.open(newline="", encoding="utf-8") as handle:
        worksheet_csv_rows = list(csv.DictReader(handle))
    assert len(worksheet_csv_rows) == 74
    assert list(worksheet_csv_rows[0].keys()) == workflow.NEXT_DECISION_WORKSHEET_FIELDS
    source_priority_path = tmp_path / "data/asset_registry/hockey_softball_source_priority_worksheet.json"
    source_priority = json.loads(source_priority_path.read_text(encoding="utf-8"))
    assert source_priority["status"] == "hockey_softball_source_priority_ready"
    assert source_priority["source_priority_rows"] == 74
    assert source_priority["logo_rows"] == 20
    assert source_priority["athlete_rows"] == 54
    assert source_priority["womens_hockey_rows"] == 49
    assert source_priority["softball_rows"] == 25
    assert source_priority["operator_verify_required_rows"] == 54
    assert source_priority["download_approved_yes_rows"] == 0
    assert source_priority["blank_source_url_rows"] == 74
    assert source_priority["source_review_bucket_counts"] == {
        "1_official_league_or_team_manual_verify": 54,
        "2_source_reviewed_waiting_for_local_asset": 20,
    }
    assert source_priority["review_only"] is True
    assert source_priority["asset_downloads"] is False
    assert source_priority["publish_ready"] is False
    source_rows = source_priority["source_priority_rows_detail"]
    assert len(source_rows) == 74
    assert source_rows[0]["sport_family"] == "womens_hockey"
    assert source_rows[0]["source_review_bucket"] == "1_official_league_or_team_manual_verify"
    assert source_rows[0]["source_candidate_url"]
    assert source_rows[0]["source_url"] == ""
    assert source_rows[0]["entity_id"] == ""
    assert all(row["source_candidate_url"] for row in source_rows)
    assert all(row["download_approved"] == "no" for row in source_rows)
    assert all(
        row[field] == ""
        for row in source_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["review_only"] == "true" for row in source_rows)
    assert all(row["asset_downloads"] == "false" for row in source_rows)
    assert all(row["approval_state_change"] == "false" for row in source_rows)
    assert all(row["publish_ready"] == "false" for row in source_rows)
    source_priority_csv_path = tmp_path / "data/asset_registry/hockey_softball_source_priority_worksheet.csv"
    with source_priority_csv_path.open(newline="", encoding="utf-8") as handle:
        source_priority_csv_rows = list(csv.DictReader(handle))
    assert len(source_priority_csv_rows) == 74
    assert list(source_priority_csv_rows[0].keys()) == workflow.SOURCE_PRIORITY_FIELDS
    source_verification_path = tmp_path / "data/asset_registry/hockey_softball_source_verification_checklist.json"
    source_verification = json.loads(source_verification_path.read_text(encoding="utf-8"))
    assert source_verification["status"] == "hockey_softball_source_verification_checklist_ready"
    assert source_verification["rows"] == 18
    assert source_verification["womens_hockey_rows"] == 12
    assert source_verification["softball_rows"] == 6
    assert source_verification["download_approved_yes_rows"] == 0
    assert source_verification["blank_source_url_rows"] == 18
    assert source_verification["blank_human_review_rows"] == 18
    verification_rows = source_verification["verification_rows_detail"]
    assert verification_rows[0]["verification_order"] == "SV01"
    assert verification_rows[0]["verification_bucket"] == "official_roster_team_source_check"
    assert verification_rows[0]["league_player_index_url"] == "https://www.thepwhl.com/en/stats/player-stats"
    assert verification_rows[0]["team_roster_url"].endswith("/roster")
    assert verification_rows[0]["team_profile_url"]
    assert verification_rows[0]["source_candidate_scope"] == "advisory_official_source_candidates_not_roster_truth_until_manual_confirmation"
    assert verification_rows[0]["roster_truth_status"] == "not_confirmed_by_generated_artifact"
    assert verification_rows[0]["review_board_to_open"] == "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md"
    assert verification_rows[0]["manual_intake_file_to_open"] == "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"
    assert all(row["download_approved"] == "no" for row in verification_rows)
    assert all(
        row[field] == ""
        for row in verification_rows
        for field in [
            "source_url",
            "entity_id",
            "rights_class",
            "identity_confidence",
            "intended_review_only_use",
            "operator_source_reviewed",
            "operator_source_allowed_for_review_only",
            "operator_identity_match",
            "operator_rights_reviewed",
        ]
    )
    assert all(row["review_only"] == "true" for row in verification_rows)
    assert all(row["asset_downloads"] == "false" for row in verification_rows)
    assert all(row["approval_state_change"] == "false" for row in verification_rows)
    source_verification_csv_path = tmp_path / "data/asset_registry/hockey_softball_source_verification_checklist.csv"
    with source_verification_csv_path.open(newline="", encoding="utf-8") as handle:
        source_verification_csv_rows = list(csv.DictReader(handle))
    assert len(source_verification_csv_rows) == 18
    assert list(source_verification_csv_rows[0].keys()) == workflow.SOURCE_VERIFICATION_CHECKLIST_FIELDS
    intake_readiness_path = tmp_path / "data/asset_registry/hockey_softball_intake_readiness_summary.json"
    intake_readiness = json.loads(intake_readiness_path.read_text(encoding="utf-8"))
    assert intake_readiness["status"] == "hockey_softball_intake_readiness_summary_ready"
    assert intake_readiness["groups"] == 4
    assert intake_readiness["rows_covered"] == 74
    assert intake_readiness["logo_source_reviewed_rows"] == 20
    assert intake_readiness["athlete_source_pending_rows"] == 54
    assert intake_readiness["blank_human_review_metadata_rows"] == 54
    assert intake_readiness["unsafe_guardrail_rows"] == 0
    assert intake_readiness["download_approved_yes_rows"] == 0
    assert intake_readiness["blank_source_url_rows"] == 4
    intake_rows = intake_readiness["summary_rows"]
    assert len(intake_rows) == 4
    assert intake_rows[0]["summary_order"] == "IR01"
    assert intake_rows[0]["asset_domain"] == "logo"
    assert intake_rows[0]["source_reviewed_yes_rows"] == "13"
    assert intake_rows[0]["render_feed_readiness"] == "source_review_recorded_waiting_for_local_logo_asset"
    assert intake_rows[1]["asset_domain"] == "athlete_photo"
    assert intake_rows[1]["source_reviewed_no_rows"] == "36"
    assert intake_rows[1]["blank_human_review_metadata_rows"] == "36"
    assert intake_rows[1]["render_feed_readiness"] == "source_and_identity_review_pending_waiting_for_named_local_athlete_asset"
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(
        row[field] == ""
        for row in intake_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["asset_downloads"] == "false" for row in intake_rows)
    assert all(row["approval_state_change"] == "false" for row in intake_rows)
    assert all(row["publish_ready"] == "false" for row in intake_rows)
    intake_readiness_csv_path = tmp_path / "data/asset_registry/hockey_softball_intake_readiness_summary.csv"
    with intake_readiness_csv_path.open(newline="", encoding="utf-8") as handle:
        intake_readiness_csv_rows = list(csv.DictReader(handle))
    assert len(intake_readiness_csv_rows) == 4
    assert list(intake_readiness_csv_rows[0].keys()) == workflow.INTAKE_READINESS_SUMMARY_FIELDS
    source_map_path = tmp_path / "data/asset_registry/hockey_softball_source_map_board.json"
    source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
    assert source_map["status"] == "hockey_softball_source_map_board_ready"
    assert source_map["rows"] == 12
    assert source_map["womens_hockey_rows"] == 6
    assert source_map["softball_rows"] == 6
    assert source_map["official_free_public_rows"] == 6
    assert source_map["download_approved_yes_rows"] == 0
    assert source_map["allowed_for_download_approved_yes_rows"] == 0
    assert source_map["blank_source_url_rows"] == 12
    source_map_rows = source_map["source_map_rows_detail"]
    assert len(source_map_rows) == 12
    assert source_map_rows[0]["source_map_order"] == "SM01"
    assert source_map_rows[0]["source_lane"] == "official_logo_league_team_pages"
    assert source_map_rows[0]["source_tier"] == "P0_OFFICIAL_FREE_PUBLIC"
    assert source_map_rows[1]["source_lane"] == "official_roster_team_player_pages"
    assert source_map_rows[1]["roster_truth_limit"] == "not_roster_truth_until_human_confirms_current_team_and_named_player"
    assert any(row["source_category"] == "gray_area_public_lead" for row in source_map_rows)
    assert any(row["source_category"] == "official_social" for row in source_map_rows)
    assert all(row["allowed_for_download_approved_yes"] == "false" for row in source_map_rows)
    assert all(row["download_approved"] == "no" for row in source_map_rows)
    assert all(
        row[field] == ""
        for row in source_map_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["review_only"] == "true" for row in source_map_rows)
    assert all(row["asset_downloads"] == "false" for row in source_map_rows)
    assert all(row["approval_state_change"] == "false" for row in source_map_rows)
    assert all(row["headshot_writes"] == "false" for row in source_map_rows)
    assert all(row["segmentation_writes"] == "false" for row in source_map_rows)
    assert all(row["publish_ready"] == "false" for row in source_map_rows)
    action_photo_map_rows = [row for row in source_map_rows if row["asset_domain"] == "action_photo"]
    assert len(action_photo_map_rows) == 8
    assert all(
        row["manual_return_intake_hint"] == "data/asset_registry/hockey_softball_source_research_return_intake.csv"
        for row in action_photo_map_rows
    )
    source_map_csv_path = tmp_path / "data/asset_registry/hockey_softball_source_map_board.csv"
    with source_map_csv_path.open(newline="", encoding="utf-8") as handle:
        source_map_csv_rows = list(csv.DictReader(handle))
    assert len(source_map_csv_rows) == 12
    assert list(source_map_csv_rows[0].keys()) == workflow.SOURCE_MAP_BOARD_FIELDS
    source_return_path = tmp_path / "data/asset_registry/hockey_softball_source_research_return_intake.json"
    source_return = json.loads(source_return_path.read_text(encoding="utf-8"))
    assert source_return["status"] == "hockey_softball_source_research_return_intake_ready"
    assert source_return["rows"] == 8
    assert source_return["womens_hockey_rows"] == 4
    assert source_return["softball_rows"] == 4
    assert source_return["blank_operator_return_rows"] == 8
    assert source_return["download_approved_yes_rows"] == 0
    assert source_return["blank_download_law_rows"] == 8
    assert source_return["asset_downloads"] is False
    assert source_return["approval_state_change"] is False
    assert source_return["publish_ready"] is False
    assert all(row["download_approved"] == "no" for row in source_return["return_rows_detail"])
    assert all(row["source_url"] == "" for row in source_return["return_rows_detail"])
    assert all(row["entity_id"] == "" for row in source_return["return_rows_detail"])
    assert all(row["rights_class"] == "" for row in source_return["return_rows_detail"])
    assert all(row["asset_downloads"] == "false" for row in source_return["return_rows_detail"])
    assert all(row["source_map_row_ref"].startswith("data/asset_registry/hockey_softball_source_map_board.csv#row=SM") for row in source_return["return_rows_detail"])
    source_return_csv_path = tmp_path / "data/asset_registry/hockey_softball_source_research_return_intake.csv"
    with source_return_csv_path.open(newline="", encoding="utf-8") as handle:
        source_return_csv_rows = list(csv.DictReader(handle))
    assert len(source_return_csv_rows) == 8
    assert list(source_return_csv_rows[0].keys()) == workflow.SOURCE_RESEARCH_RETURN_INTAKE_FIELDS
    triage_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_triage.json"
    triage = json.loads(triage_path.read_text(encoding="utf-8"))
    assert triage["status"] == "hockey_softball_asset_review_triage_ready"
    assert triage["triage_rows"] == 38
    assert triage["logo_rows"] == 20
    assert triage["athlete_rows"] == 18
    assert triage["womens_hockey_rows"] == 25
    assert triage["softball_rows"] == 13
    assert triage["operator_verify_required_source_rows"] == 54
    assert triage["download_approved_yes_rows"] == 0
    assert triage["blank_source_url_rows"] == 38
    assert triage["candidate_next_action_bucket_counts"] == {
        "local_logo_candidate_needed": 20,
        "official_roster_team_source_verify": 18,
    }
    assert triage["primary_manual_action_counts"] == {
        "official_roster_team_source_check": 18,
        "source_reviewed_waiting_for_local_asset": 20,
    }
    assert triage["review_only"] is True
    assert triage["asset_downloads"] is False
    assert triage["publish_ready"] is False
    triage_rows = triage["triage_rows_detail"]
    assert len(triage_rows) == 38
    assert triage_rows[0]["primary_manual_action"] == "official_roster_team_source_check"
    assert triage_rows[0]["candidate_next_action_bucket"] == "official_roster_team_source_verify"
    assert triage_rows[0]["source_tier"] == "P0_OFFICIAL_LEAGUE_OR_TEAM_SOURCE"
    assert triage_rows[0]["source_priority_rows"] == "3"
    assert triage_rows[0]["source_priority_rank_range"] == "1-3"
    assert triage_rows[0]["source_priority_csv_filter"] == "sport_family=womens_hockey;asset_domain=athlete_photo;candidate_entity_id=boston_fleet"
    assert triage_rows[0]["operator_verify_required_source_rows"] == "3"
    assert "identity_source_verification" in triage_rows[0]["action_flags"]
    assert triage_rows[0]["advisory_source_candidate_urls"]
    assert triage_rows[0]["review_board_to_open"] == "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md"
    assert triage_rows[0]["manual_intake_file_to_open"] == "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"
    assert triage_rows[0]["future_download_intake_file"] == "data/asset_registry/hockey_softball_quarantine_download_intake.csv"
    logo_triage_row = next(row for row in triage_rows if row["asset_domain"] == "logo")
    assert logo_triage_row["candidate_next_action_bucket"] == "local_logo_candidate_needed"
    assert logo_triage_row["review_board_to_open"].endswith("_logo_contact_sheet.md")
    assert logo_triage_row["manual_intake_file_to_open"].endswith("_logo_review_intake.csv")
    assert all(row["download_approved"] == "no" for row in triage_rows)
    assert all(
        row[field] == ""
        for row in triage_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["review_only"] == "true" for row in triage_rows)
    assert all(row["asset_downloads"] == "false" for row in triage_rows)
    assert all(row["approval_state_change"] == "false" for row in triage_rows)
    assert all(row["publish_ready"] == "false" for row in triage_rows)
    triage_csv_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_triage.csv"
    with triage_csv_path.open(newline="", encoding="utf-8") as handle:
        triage_csv_rows = list(csv.DictReader(handle))
    assert len(triage_csv_rows) == 38
    assert list(triage_csv_rows[0].keys()) == workflow.REVIEW_TRIAGE_FIELDS
    readiness_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_readiness_board.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    assert readiness["status"] == "hockey_softball_asset_review_readiness_ready"
    assert readiness["readiness_rows"] == 38
    assert readiness["logo_rows"] == 20
    assert readiness["athlete_rows"] == 18
    assert readiness["womens_hockey_rows"] == 25
    assert readiness["softball_rows"] == 13
    assert readiness["download_approved_yes_rows"] == 0
    assert readiness["blank_source_url_rows"] == 38
    assert readiness["source_identity_gap_rows"] == 38
    assert readiness["team_entity_check_rows"] == 38
    assert readiness["local_candidate_gap_rows"] == 38
    assert readiness["readiness_bucket_counts"] == {
        "local_logo_candidate_needed_before_logo_review": 20,
        "official_roster_source_verify_before_photo_review": 18,
    }
    readiness_rows = readiness["readiness_rows_detail"]
    assert readiness_rows[0]["asset_review_readiness_bucket"] == "official_roster_source_verify_before_photo_review"
    assert readiness_rows[0]["future_download_intake_status"] == "human_edited_intake_required_no_generated_authorization"
    assert readiness_rows[0]["source_identity_gap"] == "official_roster_or_team_source_not_manually_confirmed_for_named_photo_review"
    assert readiness_rows[0]["team_entity_name_check"].startswith("confirm_candidate_entity_id_matches_official_team_or_roster_context")
    assert readiness_rows[0]["local_candidate_asset_gap"] == "named_local_athlete_photo_candidate_missing"
    assert readiness_rows[0]["source_candidate_scope"] == "advisory_source_candidate_only_not_roster_truth_until_manual_official_confirmation"
    assert readiness_rows[0]["human_fields_to_fill_now"].startswith("after_manual_source_open_only:")
    assert "download_approved" in readiness_rows[0]["human_fields_to_keep_blank"]
    assert readiness_rows[0]["triage_row_ref"].startswith("data/asset_registry/hockey_softball_asset_review_triage.csv#row=")
    assert any(
        row["triage_row_ref"] == "data/asset_registry/hockey_softball_asset_review_triage.csv#row=1"
        for row in readiness_rows
    )
    assert readiness_rows[0]["source_priority_file"] == "data/asset_registry/hockey_softball_source_priority_worksheet.csv"
    assert all(row["download_approved"] == "no" for row in readiness_rows)
    assert all(row["team_entity_name_check"] for row in readiness_rows)
    assert all(row["local_candidate_asset_gap"] for row in readiness_rows)
    assert all(row["human_fields_to_keep_blank"] for row in readiness_rows)
    assert all(
        row[field] == ""
        for row in readiness_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["review_only"] == "true" for row in readiness_rows)
    assert all(row["asset_downloads"] == "false" for row in readiness_rows)
    assert all(row["approval_state_change"] == "false" for row in readiness_rows)
    assert all(row["publish_ready"] == "false" for row in readiness_rows)
    readiness_csv_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_readiness_board.csv"
    with readiness_csv_path.open(newline="", encoding="utf-8") as handle:
        readiness_csv_rows = list(csv.DictReader(handle))
    assert len(readiness_csv_rows) == 38
    assert list(readiness_csv_rows[0].keys()) == workflow.ASSET_REVIEW_READINESS_FIELDS
    focus_path = tmp_path / "data/asset_registry/hockey_softball_manual_verification_focus.json"
    focus = json.loads(focus_path.read_text(encoding="utf-8"))
    assert focus["status"] == "hockey_softball_manual_verification_focus_ready"
    assert focus["rows"] == 46
    assert focus["p0_rows"] == 24
    assert focus["p1_rows"] == 22
    assert focus["asset_readiness_rows"] == 38
    assert focus["source_map_rows"] == 8
    assert focus["download_approved_yes_rows"] == 0
    assert focus["blank_source_url_rows"] == 46
    assert focus["review_only"] is True
    assert focus["asset_downloads"] is False
    assert focus["publish_ready"] is False
    focus_rows = focus["focus_rows_detail"]
    assert focus_rows[0]["focus_rank"] == "VF01"
    assert focus_rows[0]["priority"] == "P0"
    assert focus_rows[0]["source_surface"] == "asset_review_readiness"
    assert focus_rows[0]["exact_row_ref"].startswith("data/asset_registry/hockey_softball_asset_review_readiness_board.csv#row=")
    assert "data/asset_registry/hockey_softball_source_priority_worksheet.csv#rank=" in focus_rows[0]["source_priority_row_ref_or_filter"]
    assert focus_rows[0]["open_first_file"].endswith("_athlete_photo_contact_sheet_index.md")
    assert focus_rows[0]["manual_intake_file_to_open"].endswith("_athlete_photo_review_intake.csv")
    assert "not render-ready" in focus_rows[0]["why_row_matters"]
    assert "source_and_identity_verification_required" in focus_rows[0]["evidence_or_candidate_blocker"]
    assert "do not download" in focus_rows[0]["do_not_do"]
    assert any(row["source_surface"] == "source_map_board" and row["priority"] == "P1" for row in focus_rows)
    assert all(row["download_approved"] == "no" for row in focus_rows)
    assert all(
        row[field] == ""
        for row in focus_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use"]
    )
    assert all(row["review_only"] == "true" for row in focus_rows)
    assert all(row["asset_downloads"] == "false" for row in focus_rows)
    assert all(row["approval_state_change"] == "false" for row in focus_rows)
    assert all(row["publish_ready"] == "false" for row in focus_rows)
    focus_csv_path = tmp_path / "data/asset_registry/hockey_softball_manual_verification_focus.csv"
    with focus_csv_path.open(newline="", encoding="utf-8") as handle:
        focus_csv_rows = list(csv.DictReader(handle))
    assert len(focus_csv_rows) == 46
    assert list(focus_csv_rows[0].keys()) == workflow.MANUAL_VERIFICATION_FOCUS_FIELDS
    cards_path = tmp_path / "data/asset_registry/hockey_softball_asset_next_action_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    assert cards["status"] == "hockey_softball_asset_next_action_cards_ready"
    assert cards["rows"] == 38
    assert cards["logo_rows"] == 20
    assert cards["athlete_rows"] == 18
    assert cards["womens_hockey_rows"] == 25
    assert cards["softball_rows"] == 13
    assert cards["download_approved_yes_rows"] == 0
    assert cards["blank_source_url_rows"] == 38
    assert cards["card_priority_counts"] == {
        "P0_source_identity_before_photo_review": 18,
        "P1_local_logo_candidate_before_logo_review": 20,
    }
    card_rows = cards["next_action_card_rows_detail"]
    assert card_rows[0]["card_rank"] == "NC01"
    assert card_rows[0]["card_priority"] == "P0_source_identity_before_photo_review"
    assert card_rows[0]["source_proof_placeholder"] == "blank_until_human_opens_source_or_review_board"
    assert card_rows[0]["official_profile_source_url_placeholder"] == "blank_until_human_records_official_profile_or_source_url"
    assert card_rows[0]["candidate_asset_photo_status"] == "candidate_photo_missing_named_local_asset_required"
    assert card_rows[0]["verification_status"] == "manual_official_source_verification_required"
    assert card_rows[0]["quarantine_download_eligibility_status"] == "not_eligible_generated_rows_no_download;human_edited_intake_required"
    assert card_rows[0]["readiness_row_ref"].startswith("data/asset_registry/hockey_softball_asset_review_readiness_board.csv#row=")
    assert card_rows[0]["source_priority_row_ref_or_filter"].startswith("data/asset_registry/hockey_softball_source_priority_worksheet.csv#rank=")
    assert all(row["download_approved"] == "no" for row in card_rows)
    assert all(
        row[field] == ""
        for row in card_rows
        for field in ["source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use", "operator_decision", "operator_notes"]
    )
    assert all(row["review_only"] == "true" for row in card_rows)
    assert all(row["asset_downloads"] == "false" for row in card_rows)
    assert all(row["approval_state_change"] == "false" for row in card_rows)
    assert all(row["publish_ready"] == "false" for row in card_rows)
    cards_csv_path = tmp_path / "data/asset_registry/hockey_softball_asset_next_action_cards.csv"
    with cards_csv_path.open(newline="", encoding="utf-8") as handle:
        card_csv_rows = list(csv.DictReader(handle))
    assert len(card_csv_rows) == 38
    assert list(card_csv_rows[0].keys()) == workflow.NEXT_ACTION_CARD_FIELDS
    download_path = tmp_path / "data/asset_registry/hockey_softball_quarantine_download_intake.json"
    download_manifest = json.loads(download_path.read_text(encoding="utf-8"))
    assert download_manifest["status"] == "hockey_softball_quarantine_download_intake_ready"
    assert download_manifest["rows"] == 74
    assert download_manifest["logo_rows"] == 20
    assert download_manifest["athlete_rows"] == 54
    assert download_manifest["source_reviewed_rows"] == 20
    assert download_manifest["download_approved_yes_rows"] == 0
    assert download_manifest["default_download_approved"] == "no"
    assert download_manifest["quarantine_folder"] == "data/assets/quarantine/review_only_candidates"
    assert {
        "download_approved=yes",
        "source_url",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
    } <= set(download_manifest["required_human_fields_for_future_download"])
    assert all(row["download_approved"] == "no" for row in download_manifest["download_rows"])
    assert all(row["download_status"] == "not_requested" for row in download_manifest["download_rows"])
    assert all(row["asset_downloads"] == "false" for row in download_manifest["download_rows"])
    assert all(row["publish_ready"] == "false" for row in download_manifest["download_rows"])
    assert all(row["auto_approval"] == "false" for row in download_manifest["download_rows"])
    assert all(row["move_files"] == "false" for row in download_manifest["download_rows"])
    assert all(row["quarantine_folder"] == "data/assets/quarantine/review_only_candidates" for row in download_manifest["download_rows"])
    assert all(row["proposed_quarantine_path"].startswith("data/assets/quarantine/review_only_candidates/") for row in download_manifest["download_rows"])
    assert all(row["operator_source_url"] == "" for row in download_manifest["download_rows"])
    download_csv_path = tmp_path / "data/asset_registry/hockey_softball_quarantine_download_intake.csv"
    with download_csv_path.open(newline="", encoding="utf-8") as handle:
        download_csv_rows = list(csv.DictReader(handle))
    assert len(download_csv_rows) == 74
    assert list(download_csv_rows[0].keys()) == workflow.QUARANTINE_DOWNLOAD_INTAKE_FIELDS

    hockey_board = (tmp_path / "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md").read_text(encoding="utf-8")
    softball_board = (tmp_path / "data/asset_registry/softball/softball_asset_workflow_board.md").read_text(encoding="utf-8")
    action_queue_board = (tmp_path / "data/asset_registry/hockey_softball_asset_review_action_queue.md").read_text(encoding="utf-8")
    batch_helper_board = (tmp_path / "data/asset_registry/hockey_softball_batch_source_review_helper.md").read_text(encoding="utf-8")
    next_decision_board = (tmp_path / "data/asset_registry/hockey_softball_next_decision_worksheet.md").read_text(encoding="utf-8")
    source_priority_board = (tmp_path / "data/asset_registry/hockey_softball_source_priority_worksheet.md").read_text(encoding="utf-8")
    source_map_board = (tmp_path / "data/asset_registry/hockey_softball_source_map_board.md").read_text(encoding="utf-8")
    source_verification_board = (tmp_path / "data/asset_registry/hockey_softball_source_verification_checklist.md").read_text(encoding="utf-8")
    intake_readiness_board = (tmp_path / "data/asset_registry/hockey_softball_intake_readiness_summary.md").read_text(encoding="utf-8")
    triage_board = (tmp_path / "data/asset_registry/hockey_softball_asset_review_triage.md").read_text(encoding="utf-8")
    readiness_board = (tmp_path / "data/asset_registry/hockey_softball_asset_review_readiness_board.md").read_text(encoding="utf-8")
    focus_board = (tmp_path / "data/asset_registry/hockey_softball_manual_verification_focus.md").read_text(encoding="utf-8")
    cards_board = (tmp_path / "data/asset_registry/hockey_softball_asset_next_action_cards.md").read_text(encoding="utf-8")
    download_board = (tmp_path / "data/asset_registry/hockey_softball_quarantine_download_intake.md").read_text(encoding="utf-8")
    assert "## How To Work This Queue" in action_queue_board
    assert "fields_to_keep_blank_until_review" in action_queue_board
    assert "no automatic downloads" in action_queue_board
    assert "## Next 10 Source-Review Rows" in batch_helper_board
    assert "Fields Mike can fill now" in batch_helper_board
    assert "Do not touch" in batch_helper_board
    assert "## Next Decision Rows" in next_decision_board
    assert "## First Action Buckets" in next_decision_board
    assert "1_source_verification" in next_decision_board
    assert "## Future Quarantine-Download Fields" in next_decision_board
    assert "source_url" in next_decision_board
    assert "every generated human-decision cell is intentionally blank" in next_decision_board
    assert "does not write back to logo or athlete review intake files" in next_decision_board
    assert "source_candidate_url` is advisory evidence" in source_priority_board
    assert "download-law `source_url` and `entity_id` fields remain blank" in source_priority_board
    assert "Do not copy `source_candidate_url` into download-law `source_url`" in source_priority_board
    assert "Hockey/Softball Source Map Board" in source_map_board
    assert "official/free public sources" in source_map_board
    assert "This board does not fetch source pages" in source_map_board
    assert "Do not copy a search macro into download-law `source_url`" in source_map_board
    assert "Official roster/team pages are identity anchors, not automatic roster truth" in source_map_board
    assert "Hockey/Softball Source Verification Checklist" in source_verification_board
    assert "league_player_index_url" in source_verification_board
    assert "not roster truth" in source_verification_board
    assert "generated local-download-law fields stay `download_approved=no`" in source_verification_board
    assert "Hockey/Softball Intake Readiness Summary" in intake_readiness_board
    assert "Logo groups are source-reviewed" in intake_readiness_board
    assert "Athlete groups are intentionally source/identity/local-file pending" in intake_readiness_board
    assert "Generated future download-law fields remain `download_approved=no`" in intake_readiness_board
    assert "Review-only operator triage worksheet" in triage_board
    assert "## Candidate Next-Action Buckets" in triage_board
    assert "advisory_source_candidate_urls" in triage_board
    assert "source_priority_csv_filter" in triage_board
    assert "review_board_to_open" in triage_board
    assert "generated local-download-law fields stay `download_approved=no`" in triage_board
    assert "Hockey/Softball Asset Review Readiness Board" in readiness_board
    assert "official_roster_source_verify_before_photo_review" in readiness_board
    assert "local_logo_candidate_needed_before_logo_review" in readiness_board
    assert "Generated local-download-law fields stay `download_approved=no`" in readiness_board
    assert "source_identity_gap" in readiness_board
    assert "human_fields_to_fill_now" in readiness_board
    assert "Hockey/Softball Manual Verification Focus" in focus_board
    assert "P0 rows: `24`" in focus_board
    assert "P1 rows: `22`" in focus_board
    assert "exact_row_ref" in focus_board
    assert "fields_to_keep_blank_or_no" in focus_board
    assert "does not fetch sources" in focus_board
    assert "Hockey/Softball Asset Next-Action Cards" in cards_board
    assert "source_proof_placeholder" in cards_board
    assert "official_profile_source_url_placeholder" in cards_board
    assert "Generated URL, decision, approval, and download-law fields stay blank/no/false" in cards_board
    assert "human_edited_intake_required" in cards_board
    assert "Default download_approved value: `no`" in download_board
    assert "quarantine-only local asset candidate step" in download_board
    assert "Do not download from this packet" in download_board
    assert "## Review Order" in hockey_board
    assert "## Next Human Action" in hockey_board
    assert "hockey_softball_asset_review_action_queue.md" in hockey_board
    assert "hockey_softball_batch_source_review_helper.md" in hockey_board
    assert "proposed manual target paths only" in hockey_board
    assert "PWHL San Jose" in hockey_board
    assert "Athletes Unlimited Softball League" in softball_board
    assert "proposed manual marker paths only" in softball_board
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))


def test_action_queue_source_only_count_uses_local_asset_presence() -> None:
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")
    rows = [
        {
            "sport_label": "Women's Hockey",
            "asset_domain": "athlete_photo",
            "display_name": "Marker-only row",
            "priority": "A01",
            "review_state": "approved_marker_present_manual_audit_required",
            "board_to_open": "team-board.md",
            "contact_sheet_to_open": "contact.csv",
            "intake_to_fill": "intake.csv",
            "source_url": "https://example.com/source",
            "local_asset_path": "assets/example/headshot.png",
            "local_asset_present": "no",
            "fields_to_fill_after_manual_review": "source_reviewed",
            "fields_to_keep_blank_until_review": "reviewed_by; reviewed_at_local",
            "fields_that_must_remain_hold": "identity_verified=no; publish_ready=false",
            "next_human_action": "Hold until a local asset exists.",
        }
    ]

    board = workflow.render_action_queue(rows, "2026-06-27T15:00:00+00:00")

    assert "- Source-candidate-only rows: `1`" in board
    assert "- Local asset present rows: `0`" in board


def test_batch_source_review_bucket_classifies_hold_paths() -> None:
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")
    base = {
        "source_url": "https://example.com/source",
        "local_asset_present": "no",
        "review_state": "source_candidate_only_local_asset_missing",
        "current_source_reviewed": "no",
    }

    assert workflow.batch_source_review_bucket(base) == "source_review_now"
    assert workflow.batch_source_review_bucket({**base, "current_source_reviewed": "yes"}) == "source_already_reviewed_wait_for_local_asset"
    assert workflow.batch_source_review_bucket({**base, "local_asset_present": "yes"}) == "local_asset_present_manual_identity_review"
    assert workflow.batch_source_review_bucket({**base, "review_state": "approved_marker_present_manual_audit_required"}) == "marker_present_manual_audit_required"
    assert workflow.batch_source_review_bucket({**base, "source_url": ""}) == "source_missing_hold"


def test_unsafe_intake_rows_flags_non_hold_or_truthy_guardrails() -> None:
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")

    assert workflow.unsafe_intake_rows(
        [
            {"registry_action": "hold_no_registry_state_change_until_local_asset_exists", "publish_ready": "false"},
            {"registry_action": "approve_asset", "publish_ready": "false"},
            {"registry_action": "hold_no_registry_state_change_until_local_asset_exists", "auto_publish": "yes"},
        ]
    ) == 2


def test_command_center_surfaces_hockey_softball_asset_workflow_readiness(tmp_path: Path, monkeypatch) -> None:
    seed_hockey_softball_review_packet(tmp_path, monkeypatch)
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")
    assert workflow.main() == 0

    command_center = load_command_center_module()
    panel = command_center.asset_availability_readiness_panel()

    assert panel["hockey_softball_asset_workflow_status"] == "hockey_softball_asset_workflow_readiness_ready"
    assert panel["hockey_softball_asset_workflow_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_workflow_rows"] == 74
    assert panel["hockey_softball_asset_review_action_queue_status"] == "hockey_softball_asset_review_action_queue_ready"
    assert panel["hockey_softball_asset_review_action_queue_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_review_action_queue_rows"] == 74
    assert panel["hockey_softball_asset_review_action_queue_source_candidate_only_rows"] == 74
    assert panel["hockey_softball_asset_review_action_queue_local_asset_present_rows"] == 0
    assert panel["hockey_softball_batch_source_review_status"] == "hockey_softball_batch_source_review_helper_ready"
    assert panel["hockey_softball_batch_source_review_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_batch_source_review_rows"] == 74
    assert panel["hockey_softball_batch_source_review_now_rows"] == 54
    assert panel["hockey_softball_batch_source_review_next_rows"] == 10
    assert panel["hockey_softball_batch_source_review_local_asset_needed_later_rows"] == 74
    assert panel["hockey_softball_next_decision_worksheet_status"] == "hockey_softball_next_decision_worksheet_ready"
    assert panel["hockey_softball_next_decision_worksheet_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_next_decision_worksheet_rows"] == 74
    assert panel["hockey_softball_next_decision_worksheet_logo_rows"] == 20
    assert panel["hockey_softball_next_decision_worksheet_athlete_rows"] == 54
    assert panel["hockey_softball_next_decision_worksheet_missing_local_rows"] == 74
    assert panel["hockey_softball_next_decision_worksheet_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_next_decision_worksheet_blank_download_metadata_rows"] == 74
    assert panel["hockey_softball_source_priority_status"] == "hockey_softball_source_priority_ready"
    assert panel["hockey_softball_source_priority_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_source_priority_rows"] == 74
    assert panel["hockey_softball_source_priority_logo_rows"] == 20
    assert panel["hockey_softball_source_priority_athlete_rows"] == 54
    assert panel["hockey_softball_source_priority_operator_verify_rows"] == 54
    assert panel["hockey_softball_source_priority_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_source_priority_blank_source_url_rows"] == 74
    assert panel["hockey_softball_source_verification_status"] == "hockey_softball_source_verification_checklist_ready"
    assert panel["hockey_softball_source_verification_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_source_verification_rows"] == 18
    assert panel["hockey_softball_source_verification_womens_hockey_rows"] == 12
    assert panel["hockey_softball_source_verification_softball_rows"] == 6
    assert panel["hockey_softball_source_verification_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_source_verification_blank_source_url_rows"] == 18
    assert panel["hockey_softball_source_verification_blank_human_review_rows"] == 18
    assert panel["hockey_softball_intake_readiness_status"] == "hockey_softball_intake_readiness_summary_ready"
    assert panel["hockey_softball_intake_readiness_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_intake_readiness_groups"] == 4
    assert panel["hockey_softball_intake_readiness_rows_covered"] == 74
    assert panel["hockey_softball_intake_readiness_logo_source_reviewed_rows"] == 20
    assert panel["hockey_softball_intake_readiness_athlete_source_pending_rows"] == 54
    assert panel["hockey_softball_intake_readiness_blank_human_review_metadata_rows"] == 54
    assert panel["hockey_softball_intake_readiness_unsafe_guardrail_rows"] == 0
    assert panel["hockey_softball_intake_readiness_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_source_map_status"] == "hockey_softball_source_map_board_ready"
    assert panel["hockey_softball_source_map_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_source_map_rows"] == 12
    assert panel["hockey_softball_source_map_womens_hockey_rows"] == 6
    assert panel["hockey_softball_source_map_softball_rows"] == 6
    assert panel["hockey_softball_source_map_official_free_public_rows"] == 6
    assert panel["hockey_softball_source_map_allowed_for_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_source_map_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_source_map_blank_source_url_rows"] == 12
    assert panel["hockey_softball_source_research_return_status"] == "hockey_softball_source_research_return_intake_ready"
    assert panel["hockey_softball_source_research_return_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_source_research_return_rows"] == 8
    assert panel["hockey_softball_source_research_return_womens_hockey_rows"] == 4
    assert panel["hockey_softball_source_research_return_softball_rows"] == 4
    assert panel["hockey_softball_source_research_return_blank_operator_rows"] == 8
    assert panel["hockey_softball_source_research_return_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_asset_review_triage_status"] == "hockey_softball_asset_review_triage_ready"
    assert panel["hockey_softball_asset_review_triage_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_review_triage_rows"] == 38
    assert panel["hockey_softball_asset_review_triage_logo_rows"] == 20
    assert panel["hockey_softball_asset_review_triage_athlete_rows"] == 18
    assert panel["hockey_softball_asset_review_triage_operator_verify_source_rows"] == 54
    assert panel["hockey_softball_asset_review_triage_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_asset_review_triage_blank_source_url_rows"] == 38
    assert panel["hockey_softball_asset_review_readiness_status"] == "hockey_softball_asset_review_readiness_ready"
    assert panel["hockey_softball_asset_review_readiness_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_review_readiness_rows"] == 38
    assert panel["hockey_softball_asset_review_readiness_logo_rows"] == 20
    assert panel["hockey_softball_asset_review_readiness_athlete_rows"] == 18
    assert panel["hockey_softball_asset_review_readiness_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_asset_review_readiness_blank_source_url_rows"] == 38
    assert panel["hockey_softball_asset_review_readiness_source_identity_gap_rows"] == 38
    assert panel["hockey_softball_asset_review_readiness_team_entity_check_rows"] == 38
    assert panel["hockey_softball_asset_review_readiness_local_candidate_gap_rows"] == 38
    assert panel["hockey_softball_manual_verification_focus_status"] == "hockey_softball_manual_verification_focus_ready"
    assert panel["hockey_softball_manual_verification_focus_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_manual_verification_focus_rows"] == 46
    assert panel["hockey_softball_manual_verification_focus_p0_rows"] == 24
    assert panel["hockey_softball_manual_verification_focus_p1_rows"] == 22
    assert panel["hockey_softball_manual_verification_focus_asset_readiness_rows"] == 38
    assert panel["hockey_softball_manual_verification_focus_source_map_rows"] == 8
    assert panel["hockey_softball_manual_verification_focus_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_manual_verification_focus_blank_source_url_rows"] == 46
    assert panel["hockey_softball_asset_next_action_cards_status"] == "hockey_softball_asset_next_action_cards_ready"
    assert panel["hockey_softball_asset_next_action_cards_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_next_action_cards_rows"] == 38
    assert panel["hockey_softball_asset_next_action_cards_logo_rows"] == 20
    assert panel["hockey_softball_asset_next_action_cards_athlete_rows"] == 18
    assert panel["hockey_softball_asset_next_action_cards_download_approved_yes_rows"] == 0
    assert panel["hockey_softball_asset_next_action_cards_blank_source_url_rows"] == 38
    assert panel["hockey_softball_quarantine_download_intake_status"] == "hockey_softball_quarantine_download_intake_ready"
    assert panel["hockey_softball_quarantine_download_intake_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_quarantine_download_intake_rows"] == 74
    assert panel["hockey_softball_quarantine_download_intake_logo_rows"] == 20
    assert panel["hockey_softball_quarantine_download_intake_athlete_rows"] == 54
    assert panel["hockey_softball_quarantine_download_approved_yes_rows"] == 0
    assert panel["womens_hockey_asset_workflow_rows"] == 49
    assert panel["softball_asset_workflow_rows"] == 25
    assert panel["womens_hockey_proposed_headshot_path_refs"] == 36
    assert panel["softball_proposed_headshot_path_refs"] == 18
    assert panel["womens_hockey_athlete_photo_source_review_slot_rows"] == 36
    assert panel["softball_athlete_photo_source_review_slot_rows"] == 18
    shortcut_labels = {shortcut["label"] for shortcut in panel["file_shortcuts"]}
    assert "Hockey/softball asset workflow readiness" in shortcut_labels
    assert "Hockey/softball asset review action queue" in shortcut_labels
    assert "Hockey/softball batch source review helper" in shortcut_labels
    assert "Hockey/softball next decision worksheet" in shortcut_labels
    assert "Hockey/softball next decision worksheet data" in shortcut_labels
    assert "Hockey/softball source priority worksheet" in shortcut_labels
    assert "Hockey/softball source priority worksheet data" in shortcut_labels
    assert "Hockey/softball source verification checklist" in shortcut_labels
    assert "Hockey/softball source verification checklist data" in shortcut_labels
    assert "Hockey/softball source verification checklist manifest" in shortcut_labels
    assert "Hockey/softball intake readiness summary" in shortcut_labels
    assert "Hockey/softball intake readiness summary data" in shortcut_labels
    assert "Hockey/softball intake readiness summary manifest" in shortcut_labels
    assert "Hockey/softball source map board" in shortcut_labels
    assert "Hockey/softball source map board data" in shortcut_labels
    assert "Hockey/softball source map board manifest" in shortcut_labels
    assert "Hockey/softball source research return intake" in shortcut_labels
    assert "Hockey/softball source research return data" in shortcut_labels
    assert "Hockey/softball source research return manifest" in shortcut_labels
    assert "Hockey/softball asset review triage" in shortcut_labels
    assert "Hockey/softball asset review triage data" in shortcut_labels
    assert "Hockey/softball asset review triage manifest" in shortcut_labels
    assert "Hockey/softball asset review readiness board" in shortcut_labels
    assert "Hockey/softball asset review readiness data" in shortcut_labels
    assert "Hockey/softball asset review readiness manifest" in shortcut_labels
    assert "Hockey/softball manual verification focus" in shortcut_labels
    assert "Hockey/softball manual verification focus data" in shortcut_labels
    assert "Hockey/softball manual verification focus manifest" in shortcut_labels
    assert "Hockey/softball asset next-action cards" in shortcut_labels
    assert "Hockey/softball asset next-action cards data" in shortcut_labels
    assert "Hockey/softball asset next-action cards manifest" in shortcut_labels
    assert "Hockey/softball quarantine download intake" in shortcut_labels
    assert "Hockey/softball quarantine download intake data" in shortcut_labels
    assert "Women's hockey asset workflow board" in shortcut_labels
    assert "Softball asset workflow board" in shortcut_labels


def test_command_center_tolerates_missing_or_empty_hockey_softball_asset_workflow_and_action_queue_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    command_center = load_command_center_module()

    missing_panel = command_center.asset_availability_readiness_panel()
    assert missing_panel["hockey_softball_asset_workflow_status"] == ""
    assert missing_panel["hockey_softball_asset_workflow_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_workflow_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_asset_review_action_queue_status"] == ""
    assert missing_panel["hockey_softball_asset_review_action_queue_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_review_action_queue_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_batch_source_review_status"] == ""
    assert missing_panel["hockey_softball_batch_source_review_generated_at"] == ""
    assert missing_panel["hockey_softball_batch_source_review_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_next_decision_worksheet_status"] == ""
    assert missing_panel["hockey_softball_next_decision_worksheet_generated_at"] == ""
    assert missing_panel["hockey_softball_next_decision_worksheet_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_source_priority_status"] == ""
    assert missing_panel["hockey_softball_source_priority_generated_at"] == ""
    assert missing_panel["hockey_softball_source_priority_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_source_verification_status"] == ""
    assert missing_panel["hockey_softball_source_verification_generated_at"] == ""
    assert missing_panel["hockey_softball_source_verification_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_intake_readiness_status"] == ""
    assert missing_panel["hockey_softball_intake_readiness_generated_at"] == ""
    assert missing_panel["hockey_softball_intake_readiness_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_source_map_status"] == ""
    assert missing_panel["hockey_softball_source_map_generated_at"] == ""
    assert missing_panel["hockey_softball_source_map_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_source_research_return_status"] == ""
    assert missing_panel["hockey_softball_source_research_return_generated_at"] == ""
    assert missing_panel["hockey_softball_source_research_return_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_asset_review_triage_status"] == ""
    assert missing_panel["hockey_softball_asset_review_triage_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_review_triage_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_asset_review_readiness_status"] == ""
    assert missing_panel["hockey_softball_asset_review_readiness_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_review_readiness_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_manual_verification_focus_status"] == ""
    assert missing_panel["hockey_softball_manual_verification_focus_generated_at"] == ""
    assert missing_panel["hockey_softball_manual_verification_focus_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_asset_next_action_cards_status"] == ""
    assert missing_panel["hockey_softball_asset_next_action_cards_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_next_action_cards_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_quarantine_download_intake_status"] == ""
    assert missing_panel["hockey_softball_quarantine_download_intake_generated_at"] == ""
    assert missing_panel["hockey_softball_quarantine_download_intake_freshness_status"] == "packet_missing"

    report_dir = tmp_path / "data" / "asset_registry"
    report_dir.mkdir(parents=True)
    (report_dir / "hockey_softball_asset_workflow_readiness_report.md").write_text("# Empty workflow\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_workflow_readiness_report.json").write_text(
        json.dumps({"status": "workflow_empty", "generated_at_utc": "2026-06-27T15:00:00+00:00", "summaries": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_asset_review_action_queue.md").write_text("# Empty action queue\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_review_action_queue.json").write_text(
        json.dumps({"status": "action_queue_empty", "generated_at_utc": "2026-06-27T15:05:00+00:00", "action_rows": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_batch_source_review_helper.md").write_text("# Empty batch helper\n", encoding="utf-8")
    (report_dir / "hockey_softball_batch_source_review_helper.json").write_text(
        json.dumps({"status": "batch_empty", "generated_at_utc": "2026-06-27T15:10:00+00:00", "batch_rows": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_next_decision_worksheet.md").write_text("# Empty worksheet\n", encoding="utf-8")
    (report_dir / "hockey_softball_next_decision_worksheet.json").write_text(
        json.dumps({"status": "worksheet_empty", "generated_at_utc": "2026-06-27T15:15:00+00:00", "worksheet_rows": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_source_priority_worksheet.md").write_text("# Empty source priority\n", encoding="utf-8")
    (report_dir / "hockey_softball_source_priority_worksheet.json").write_text(
        json.dumps({"status": "source_priority_empty", "generated_at_utc": "2026-06-27T15:18:00+00:00", "source_priority_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_source_verification_checklist.md").write_text("# Empty source verification\n", encoding="utf-8")
    (report_dir / "hockey_softball_source_verification_checklist.json").write_text(
        json.dumps({"status": "source_verification_empty", "generated_at_utc": "2026-06-27T15:18:30+00:00", "verification_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_intake_readiness_summary.md").write_text("# Empty intake readiness\n", encoding="utf-8")
    (report_dir / "hockey_softball_intake_readiness_summary.json").write_text(
        json.dumps({"status": "intake_readiness_empty", "generated_at_utc": "2026-06-27T15:18:45+00:00", "summary_rows": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_source_map_board.md").write_text("# Empty source map\n", encoding="utf-8")
    (report_dir / "hockey_softball_source_map_board.json").write_text(
        json.dumps({"status": "source_map_empty", "generated_at_utc": "2026-06-27T15:18:50+00:00", "source_map_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_source_research_return_intake.md").write_text("# Empty source return\n", encoding="utf-8")
    (report_dir / "hockey_softball_source_research_return_intake.json").write_text(
        json.dumps({"status": "source_return_empty", "generated_at_utc": "2026-06-27T15:18:55+00:00", "return_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_asset_review_triage.md").write_text("# Empty triage\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_review_triage.json").write_text(
        json.dumps({"status": "triage_empty", "generated_at_utc": "2026-06-27T15:19:00+00:00", "triage_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_asset_review_readiness_board.md").write_text("# Empty readiness\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_review_readiness_board.json").write_text(
        json.dumps({"status": "readiness_empty", "generated_at_utc": "2026-06-27T15:19:30+00:00", "readiness_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_manual_verification_focus.md").write_text("# Empty focus\n", encoding="utf-8")
    (report_dir / "hockey_softball_manual_verification_focus.json").write_text(
        json.dumps({"status": "focus_empty", "generated_at_utc": "2026-06-27T15:19:45+00:00", "focus_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_asset_next_action_cards.md").write_text("# Empty next-action cards\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_next_action_cards.json").write_text(
        json.dumps({"status": "cards_empty", "generated_at_utc": "2026-06-27T15:19:50+00:00", "next_action_card_rows_detail": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_quarantine_download_intake.md").write_text("# Empty download intake\n", encoding="utf-8")
    (report_dir / "hockey_softball_quarantine_download_intake.json").write_text(
        json.dumps({"status": "download_empty", "generated_at_utc": "2026-06-27T15:20:00+00:00", "download_rows": None}),
        encoding="utf-8",
    )

    empty_panel = command_center.asset_availability_readiness_panel()
    assert empty_panel["hockey_softball_asset_workflow_status"] == "workflow_empty"
    assert empty_panel["hockey_softball_asset_workflow_generated_at"] == "2026-06-27T15:00:00+00:00"
    assert empty_panel["hockey_softball_asset_workflow_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_review_action_queue_status"] == "action_queue_empty"
    assert empty_panel["hockey_softball_asset_review_action_queue_generated_at"] == "2026-06-27T15:05:00+00:00"
    assert empty_panel["hockey_softball_asset_review_action_queue_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_review_action_queue_rows"] == 0
    assert empty_panel["hockey_softball_batch_source_review_status"] == "batch_empty"
    assert empty_panel["hockey_softball_batch_source_review_generated_at"] == "2026-06-27T15:10:00+00:00"
    assert empty_panel["hockey_softball_batch_source_review_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_batch_source_review_rows"] == 0
    assert empty_panel["hockey_softball_next_decision_worksheet_status"] == "worksheet_empty"
    assert empty_panel["hockey_softball_next_decision_worksheet_generated_at"] == "2026-06-27T15:15:00+00:00"
    assert empty_panel["hockey_softball_next_decision_worksheet_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_next_decision_worksheet_rows"] == 0
    assert empty_panel["hockey_softball_source_priority_status"] == "source_priority_empty"
    assert empty_panel["hockey_softball_source_priority_generated_at"] == "2026-06-27T15:18:00+00:00"
    assert empty_panel["hockey_softball_source_priority_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_source_priority_rows"] == 0
    assert empty_panel["hockey_softball_source_verification_status"] == "source_verification_empty"
    assert empty_panel["hockey_softball_source_verification_generated_at"] == "2026-06-27T15:18:30+00:00"
    assert empty_panel["hockey_softball_source_verification_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_source_verification_rows"] == 0
    assert empty_panel["hockey_softball_intake_readiness_status"] == "intake_readiness_empty"
    assert empty_panel["hockey_softball_intake_readiness_generated_at"] == "2026-06-27T15:18:45+00:00"
    assert empty_panel["hockey_softball_intake_readiness_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_intake_readiness_groups"] == 0
    assert empty_panel["hockey_softball_source_map_status"] == "source_map_empty"
    assert empty_panel["hockey_softball_source_map_generated_at"] == "2026-06-27T15:18:50+00:00"
    assert empty_panel["hockey_softball_source_map_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_source_map_rows"] == 0
    assert empty_panel["hockey_softball_source_research_return_status"] == "source_return_empty"
    assert empty_panel["hockey_softball_source_research_return_generated_at"] == "2026-06-27T15:18:55+00:00"
    assert empty_panel["hockey_softball_source_research_return_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_source_research_return_rows"] == 0
    assert empty_panel["hockey_softball_asset_review_triage_status"] == "triage_empty"
    assert empty_panel["hockey_softball_asset_review_triage_generated_at"] == "2026-06-27T15:19:00+00:00"
    assert empty_panel["hockey_softball_asset_review_triage_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_review_triage_rows"] == 0
    assert empty_panel["hockey_softball_asset_review_readiness_status"] == "readiness_empty"
    assert empty_panel["hockey_softball_asset_review_readiness_generated_at"] == "2026-06-27T15:19:30+00:00"
    assert empty_panel["hockey_softball_asset_review_readiness_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_review_readiness_rows"] == 0
    assert empty_panel["hockey_softball_asset_review_readiness_source_identity_gap_rows"] == 0
    assert empty_panel["hockey_softball_asset_review_readiness_team_entity_check_rows"] == 0
    assert empty_panel["hockey_softball_asset_review_readiness_local_candidate_gap_rows"] == 0
    assert empty_panel["hockey_softball_manual_verification_focus_status"] == "focus_empty"
    assert empty_panel["hockey_softball_manual_verification_focus_generated_at"] == "2026-06-27T15:19:45+00:00"
    assert empty_panel["hockey_softball_manual_verification_focus_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_manual_verification_focus_rows"] == 0
    assert empty_panel["hockey_softball_manual_verification_focus_p0_rows"] == 0
    assert empty_panel["hockey_softball_manual_verification_focus_p1_rows"] == 0
    assert empty_panel["hockey_softball_asset_next_action_cards_status"] == "cards_empty"
    assert empty_panel["hockey_softball_asset_next_action_cards_generated_at"] == "2026-06-27T15:19:50+00:00"
    assert empty_panel["hockey_softball_asset_next_action_cards_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_next_action_cards_rows"] == 0
    assert empty_panel["hockey_softball_quarantine_download_intake_status"] == "download_empty"
    assert empty_panel["hockey_softball_quarantine_download_intake_generated_at"] == "2026-06-27T15:20:00+00:00"
    assert empty_panel["hockey_softball_quarantine_download_intake_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_quarantine_download_intake_rows"] == 0
