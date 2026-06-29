from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, read_csv, read_json, write_csv, write_json, write_text


VERSION = "hsd-hockey-softball-asset-workflow-readiness-v1-review-only"
TEMPLATE_GENERATED_AT_UTC = "2026-06-28T00:00:00+00:00"
REPORT_MD = Path("data/asset_registry/hockey_softball_asset_workflow_readiness_report.md")
REPORT_JSON = Path("data/asset_registry/hockey_softball_asset_workflow_readiness_report.json")
ACTION_QUEUE_MD = Path("data/asset_registry/hockey_softball_asset_review_action_queue.md")
ACTION_QUEUE_CSV = Path("data/asset_registry/hockey_softball_asset_review_action_queue.csv")
ACTION_QUEUE_JSON = Path("data/asset_registry/hockey_softball_asset_review_action_queue.json")
BATCH_SOURCE_REVIEW_MD = Path("data/asset_registry/hockey_softball_batch_source_review_helper.md")
BATCH_SOURCE_REVIEW_CSV = Path("data/asset_registry/hockey_softball_batch_source_review_helper.csv")
BATCH_SOURCE_REVIEW_JSON = Path("data/asset_registry/hockey_softball_batch_source_review_helper.json")
NEXT_DECISION_WORKSHEET_MD = Path("data/asset_registry/hockey_softball_next_decision_worksheet.md")
NEXT_DECISION_WORKSHEET_CSV = Path("data/asset_registry/hockey_softball_next_decision_worksheet.csv")
NEXT_DECISION_WORKSHEET_JSON = Path("data/asset_registry/hockey_softball_next_decision_worksheet.json")
SOURCE_PRIORITY_MD = Path("data/asset_registry/hockey_softball_source_priority_worksheet.md")
SOURCE_PRIORITY_CSV = Path("data/asset_registry/hockey_softball_source_priority_worksheet.csv")
SOURCE_PRIORITY_JSON = Path("data/asset_registry/hockey_softball_source_priority_worksheet.json")
SOURCE_VERIFICATION_CHECKLIST_MD = Path("data/asset_registry/hockey_softball_source_verification_checklist.md")
SOURCE_VERIFICATION_CHECKLIST_CSV = Path("data/asset_registry/hockey_softball_source_verification_checklist.csv")
SOURCE_VERIFICATION_CHECKLIST_JSON = Path("data/asset_registry/hockey_softball_source_verification_checklist.json")
INTAKE_READINESS_SUMMARY_MD = Path("data/asset_registry/hockey_softball_intake_readiness_summary.md")
INTAKE_READINESS_SUMMARY_CSV = Path("data/asset_registry/hockey_softball_intake_readiness_summary.csv")
INTAKE_READINESS_SUMMARY_JSON = Path("data/asset_registry/hockey_softball_intake_readiness_summary.json")
SOURCE_MAP_BOARD_MD = Path("data/asset_registry/hockey_softball_source_map_board.md")
SOURCE_MAP_BOARD_CSV = Path("data/asset_registry/hockey_softball_source_map_board.csv")
SOURCE_MAP_BOARD_JSON = Path("data/asset_registry/hockey_softball_source_map_board.json")
REVIEW_TRIAGE_MD = Path("data/asset_registry/hockey_softball_asset_review_triage.md")
REVIEW_TRIAGE_CSV = Path("data/asset_registry/hockey_softball_asset_review_triage.csv")
REVIEW_TRIAGE_JSON = Path("data/asset_registry/hockey_softball_asset_review_triage.json")
ASSET_REVIEW_READINESS_MD = Path("data/asset_registry/hockey_softball_asset_review_readiness_board.md")
ASSET_REVIEW_READINESS_CSV = Path("data/asset_registry/hockey_softball_asset_review_readiness_board.csv")
ASSET_REVIEW_READINESS_JSON = Path("data/asset_registry/hockey_softball_asset_review_readiness_board.json")
QUARANTINE_DOWNLOAD_INTAKE_MD = Path("data/asset_registry/hockey_softball_quarantine_download_intake.md")
QUARANTINE_DOWNLOAD_INTAKE_CSV = Path("data/asset_registry/hockey_softball_quarantine_download_intake.csv")
QUARANTINE_DOWNLOAD_INTAKE_JSON = Path("data/asset_registry/hockey_softball_quarantine_download_intake.json")
SANCTIONED_QUARANTINE_ROOT = Path("data/assets/quarantine/review_only_candidates")
CANONICAL_DOWNLOAD_INTAKE_PATH = Path("operator/inbox/review_only_asset_download_intake.csv")

ACTION_QUEUE_FIELDS = [
    "priority",
    "sport_family",
    "sport_label",
    "asset_domain",
    "entity_id",
    "display_name",
    "candidate_id",
    "review_state",
    "board_to_open",
    "contact_sheet_to_open",
    "intake_to_fill",
    "source_url",
    "local_asset_path",
    "local_asset_present",
    "current_source_reviewed",
    "current_identity_status",
    "fields_to_fill_after_manual_review",
    "fields_to_keep_blank_until_review",
    "fields_that_must_remain_hold",
    "next_human_action",
    "guardrail_note",
]

BATCH_SOURCE_REVIEW_FIELDS = [
    "review_order",
    "batch_position",
    "batch_bucket",
    "sport_family",
    "sport_label",
    "asset_domain",
    "display_name",
    "candidate_id",
    "review_state",
    "source_url",
    "evidence_to_open",
    "board_to_open",
    "intake_to_fill",
    "fields_mike_can_fill_now",
    "fields_to_keep_blank_or_held",
    "do_not_touch",
    "local_asset_present",
    "current_source_reviewed",
    "current_identity_status",
    "local_asset_needed_later",
    "guardrail_note",
]

NEXT_DECISION_WORKSHEET_FIELDS = [
    "worksheet_order",
    "worksheet_section",
    "sport_family",
    "sport_label",
    "asset_domain",
    "display_name",
    "candidate_id",
    "review_state",
    "first_action_bucket",
    "source_verification_bucket",
    "missing_local_candidate_asset",
    "download_law_status",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "quarantine_folder",
    "future_download_required_fields",
    "source_to_open",
    "board_to_open",
    "contact_sheet_to_open",
    "intake_to_fill",
    "intake_row_key",
    "fields_mike_can_fill_now",
    "fields_that_must_stay_blank",
    "fields_that_must_remain_hold",
    "operator_source_reviewed",
    "operator_source_allowed_for_review_only",
    "operator_identity_match",
    "operator_rights_reviewed",
    "operator_decision",
    "source_url_to_record",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "local_asset_present",
    "local_asset_needed_later",
    "do_not_touch",
    "guardrail_note",
]

SOURCE_PRIORITY_FIELDS = [
    "source_priority_rank",
    "source_review_bucket",
    "source_candidate_level",
    "sport_family",
    "sport_label",
    "league_name",
    "asset_domain",
    "candidate_entity_id",
    "display_name",
    "candidate_id",
    "operator_action",
    "source_priority",
    "official_status",
    "confidence",
    "operator_verify_required",
    "source_domain",
    "source_candidate_url",
    "linked_first_action_bucket",
    "linked_missing_local_candidate_asset",
    "linked_review_state",
    "render_readiness",
    "safe_next_action",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "operator_decision",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

SOURCE_VERIFICATION_CHECKLIST_FIELDS = [
    "verification_order",
    "sport_family",
    "sport_label",
    "league_name",
    "candidate_entity_id",
    "asset_domain",
    "verification_bucket",
    "league_player_index_url",
    "team_roster_url",
    "team_profile_url",
    "source_priority_rank_range",
    "source_priority_csv_filter",
    "source_priority_file",
    "review_board_to_open",
    "manual_intake_file_to_open",
    "official_source_domain",
    "source_candidate_scope",
    "source_identity_check",
    "roster_truth_status",
    "local_asset_gap",
    "human_fields_to_fill_now",
    "human_fields_to_keep_blank",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "operator_source_reviewed",
    "operator_source_allowed_for_review_only",
    "operator_identity_match",
    "operator_rights_reviewed",
    "operator_decision",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

INTAKE_READINESS_SUMMARY_FIELDS = [
    "summary_order",
    "sport_family",
    "sport_label",
    "league_name",
    "asset_domain",
    "intake_file",
    "review_board_to_open",
    "intake_rows",
    "source_reviewed_yes_rows",
    "source_reviewed_no_rows",
    "identity_confirmed_yes_rows",
    "identity_confirmed_no_rows",
    "rights_reviewed_yes_rows",
    "rights_reviewed_no_rows",
    "human_review_metadata_rows",
    "blank_human_review_metadata_rows",
    "source_url_to_record_blank_rows",
    "local_file_reviewed_yes_rows",
    "local_file_reviewed_no_rows",
    "registry_hold_rows",
    "unsafe_guardrail_rows",
    "render_feed_readiness",
    "primary_blocker",
    "next_operator_action",
    "fields_mike_can_fill_now",
    "fields_that_must_stay_blank",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

SOURCE_MAP_BOARD_FIELDS = [
    "source_map_order",
    "sport_family",
    "sport_label",
    "league_name",
    "source_lane",
    "asset_domain",
    "source_category",
    "source_tier",
    "source_type",
    "source_url_or_search_macro",
    "source_domain",
    "existing_source_priority_rows",
    "source_priority_filter",
    "evidence_use",
    "source_confidence",
    "operator_verify_required",
    "roster_truth_limit",
    "image_action_photo_fit",
    "known_limitations",
    "next_operator_action",
    "manual_return_intake_hint",
    "allowed_for_download_approved_yes",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "logo_writes",
    "segmentation_writes",
    "approved_marker_writes",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

REVIEW_TRIAGE_FIELDS = [
    "triage_rank",
    "primary_manual_action",
    "action_flags",
    "sport_family",
    "sport_label",
    "league_name",
    "asset_domain",
    "candidate_entity_id",
    "display_name",
    "candidate_next_action_bucket",
    "source_tier",
    "source_priority_rows",
    "source_priority_rank_range",
    "source_priority_csv_filter",
    "official_source_candidate_rows",
    "operator_verify_required_source_rows",
    "source_reviewed_waiting_for_local_asset_rows",
    "missing_local_candidate_asset_rows",
    "candidate_id_preview",
    "advisory_source_domains",
    "advisory_source_candidate_urls",
    "review_board_to_open",
    "manual_intake_file_to_open",
    "future_download_intake_file",
    "render_readiness",
    "safe_next_action",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "operator_decision",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

ASSET_REVIEW_READINESS_FIELDS = [
    "readiness_rank",
    "asset_review_readiness_bucket",
    "candidate_next_action_bucket",
    "sport_family",
    "sport_label",
    "league_name",
    "asset_domain",
    "candidate_entity_id",
    "source_tier",
    "source_domain",
    "advisory_source_candidate_urls",
    "triage_row_ref",
    "triage_file",
    "source_priority_rank_range",
    "source_priority_csv_filter",
    "source_priority_file",
    "review_board_to_open",
    "manual_intake_file_to_open",
    "future_download_intake_file",
    "render_readiness",
    "asset_review_blocker",
    "source_identity_gap",
    "team_entity_name_check",
    "local_candidate_asset_gap",
    "source_candidate_scope",
    "human_fields_to_fill_now",
    "human_fields_to_keep_blank",
    "future_download_intake_status",
    "next_manual_action",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "operator_decision",
    "operator_notes",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

QUARANTINE_DOWNLOAD_INTAKE_FIELDS = [
    "download_order",
    "download_bucket",
    "sport_family",
    "sport_label",
    "asset_domain",
    "entity_id",
    "display_name",
    "candidate_id",
    "source_url",
    "source_review_status",
    "identity_status",
    "local_asset_present",
    "download_approved",
    "download_status",
    "source_url_required_if_approved",
    "entity_id_required_if_approved",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "operator_source_url",
    "operator_entity_id",
    "operator_rights_class",
    "operator_identity_confidence",
    "operator_intended_review_only_use",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "quarantine_folder",
    "proposed_quarantine_path",
    "separate_approval_required",
    "approval_status",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "guardrail_note",
]

SPORTS = {
    "womens_hockey": {
        "sport_label": "Women's Hockey",
        "league_label": "Professional Women's Hockey League",
        "logo_contact_sheet": Path("data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv"),
        "logo_intake": Path("data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv"),
        "athlete_contact_sheet": Path("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv"),
        "athlete_intake": Path("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"),
        "athlete_manifest": Path("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_manifest.json"),
        "walkthrough": Path("data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md"),
        "workflow_board": Path("data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md"),
    },
    "softball": {
        "sport_label": "Softball",
        "league_label": "Athletes Unlimited Softball League",
        "logo_contact_sheet": Path("data/asset_registry/softball/softball_logo_contact_sheet.csv"),
        "logo_intake": Path("data/asset_registry/softball/softball_logo_review_intake.csv"),
        "athlete_contact_sheet": Path("data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv"),
        "athlete_intake": Path("data/asset_registry/softball/softball_athlete_photo_review_intake.csv"),
        "athlete_manifest": Path("data/asset_registry/softball/softball_athlete_photo_contact_sheet_manifest.json"),
        "walkthrough": Path("data/asset_registry/softball/softball_review_walkthrough.md"),
        "workflow_board": Path("data/asset_registry/softball/softball_asset_workflow_board.md"),
    },
}

GUARDRAILS = {
    "paid_apis": False,
    "automatic_downloads": False,
    "auto_approval": False,
    "approval_state_changes": False,
    "headshot_png_writes": False,
    "approved_marker_writes": False,
    "publish_ready_movement": False,
    "publishing": False,
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def generated_at_utc() -> str:
    return TEMPLATE_GENERATED_AT_UTC


def is_truthy(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def existing_count(paths: Iterable[str]) -> int:
    return sum(1 for path in paths if clean(path) and input_path(path).exists())


def unsafe_intake_rows(rows: Iterable[Mapping[str, str]]) -> int:
    unsafe = 0
    for row in rows:
        registry_action = clean(row.get("registry_action"))
        guardrail_true = any(
            is_truthy(row.get(field))
            for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis", "asset_downloads"]
        )
        if guardrail_true or (registry_action and not registry_action.startswith("hold_no_registry_state_change")):
            unsafe += 1
    return unsafe


def unique_values(rows: Iterable[Mapping[str, str]], field: str) -> list[str]:
    values = {clean(row.get(field)) for row in rows if clean(row.get(field))}
    return sorted(values)


def logo_intake_key(row: Mapping[str, str]) -> tuple[str, str, str, str]:
    return (
        clean(row.get("sport_family")),
        clean(row.get("entity_type")),
        clean(row.get("entity_id")),
        clean(row.get("asset_slot")),
    )


def athlete_intake_key(row: Mapping[str, str]) -> tuple[str, str, str, str]:
    return (
        clean(row.get("sport_family")),
        clean(row.get("team_id")),
        clean(row.get("candidate_id")),
        clean(row.get("player_id")),
    )


def bool_text(value: Any) -> str:
    return "yes" if is_truthy(value) else "no"


def slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")
    return text or "operator_fill_required"


def existing_quarantine_download_rows() -> list[Dict[str, str]]:
    return read_csv(QUARANTINE_DOWNLOAD_INTAKE_CSV)


def quarantine_download_key(row: Mapping[str, str]) -> tuple[str, str, str, str]:
    return (
        clean(row.get("sport_family")),
        clean(row.get("asset_domain")),
        clean(row.get("entity_id")),
        clean(row.get("candidate_id")),
    )


def existing_quarantine_download_by_key(rows: Iterable[Mapping[str, str]] | None = None) -> Dict[tuple[str, str, str, str], Mapping[str, str]]:
    return {quarantine_download_key(row): row for row in (rows or existing_quarantine_download_rows())}


def logo_action_rows(sport_key: str, sport: Mapping[str, Any], logo_rows: list[Dict[str, str]], logo_intake_rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    intake_by_key = {logo_intake_key(row): row for row in logo_intake_rows}
    rows: list[Dict[str, str]] = []
    for index, row in enumerate(logo_rows, start=1):
        intake = intake_by_key.get(logo_intake_key(row), {})
        local_present = is_truthy(row.get("local_file_exists"))
        rows.append(
            {
                "priority": f"L{index:02d}",
                "sport_family": sport_key,
                "sport_label": sport["sport_label"],
                "asset_domain": "logo",
                "entity_id": clean(row.get("entity_id")),
                "display_name": clean(row.get("display_name")),
                "candidate_id": clean(row.get("asset_slot")),
                "review_state": "local_logo_present_source_review_needed" if local_present else "source_candidate_only_local_logo_missing",
                "board_to_open": sport["logo_contact_sheet"].with_suffix(".md").as_posix(),
                "contact_sheet_to_open": sport["logo_contact_sheet"].as_posix(),
                "intake_to_fill": sport["logo_intake"].as_posix(),
                "source_url": clean(row.get("official_source_candidate")),
                "local_asset_path": clean(row.get("target_path")),
                "local_asset_present": bool_text(row.get("local_file_exists")),
                "current_source_reviewed": clean(intake.get("source_reviewed")) or "no",
                "current_identity_status": clean(intake.get("identity_match")) or "operator_fill_required",
                "fields_to_fill_after_manual_review": "operator_decision; source_reviewed; identity_match; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local",
                "fields_to_keep_blank_until_review": "reviewed_by; reviewed_at_local; source_url_to_record",
                "fields_that_must_remain_hold": "registry_action=hold_no_registry_state_change_until_local_logo_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false",
                "next_human_action": "Open the logo board/source page, compare mark identity, then fill the logo intake; keep registry action hold-only until a local logo asset is manually supplied and reviewed.",
                "guardrail_note": "review-only; no downloads; no approval-state change",
            }
        )
    return rows


def athlete_action_rows(
    sport_key: str,
    sport: Mapping[str, Any],
    athlete_rows: list[Dict[str, str]],
    athlete_intake_rows: list[Dict[str, str]],
) -> list[Dict[str, str]]:
    intake_by_key = {athlete_intake_key(row): row for row in athlete_intake_rows}
    rows: list[Dict[str, str]] = []
    for index, row in enumerate(athlete_rows, start=1):
        intake = intake_by_key.get(athlete_intake_key(row), {})
        local_present = is_truthy(row.get("local_candidate_exists"))
        marker_present = is_truthy(row.get("approved_marker_exists"))
        review_state = "local_candidate_asset_present_manual_review_required" if local_present else "source_candidate_only_local_asset_missing"
        if marker_present:
            review_state = "approved_marker_present_manual_audit_required"
        rows.append(
            {
                "priority": f"A{index:02d}",
                "sport_family": sport_key,
                "sport_label": sport["sport_label"],
                "asset_domain": "athlete_photo",
                "entity_id": clean(row.get("team_id")),
                "display_name": clean(row.get("display_name")),
                "candidate_id": clean(row.get("candidate_id")),
                "review_state": review_state,
                "board_to_open": clean(row.get("team_review_board_path")),
                "contact_sheet_to_open": sport["athlete_contact_sheet"].as_posix(),
                "intake_to_fill": sport["athlete_intake"].as_posix(),
                "source_url": clean(row.get("source_url")),
                "local_asset_path": clean(row.get("local_candidate_path")),
                "local_asset_present": bool_text(row.get("local_candidate_exists")),
                "current_source_reviewed": clean(intake.get("source_reviewed")) or "no",
                "current_identity_status": clean(intake.get("identity_verified")) or "no",
                "fields_to_fill_after_manual_review": "source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local",
                "fields_to_keep_blank_until_review": "source_url_to_record; reviewed_by; reviewed_at_local",
                "fields_that_must_remain_hold": "operator_decision=hold_identity; identity_verified=no until named athlete evidence; local_file_reviewed=no until local file exists; registry_action=hold_no_registry_state_change_until_local_candidate_asset_exists; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false",
                "next_human_action": "Open the team board/source URL, confirm source/rights posture, then fill only source-review fields in the athlete intake; keep identity/local-file/approval fields held until a named athlete and local candidate asset exist.",
                "guardrail_note": "review-only; source candidate only unless local asset exists; no headshot or marker writes",
            }
        )
    return rows


def summarize_sport(sport_key: str, sport: Mapping[str, Any], generated_at: str) -> Dict[str, Any]:
    logo_rows = read_csv(sport["logo_contact_sheet"])
    logo_intake_rows = read_csv(sport["logo_intake"])
    athlete_rows = read_csv(sport["athlete_contact_sheet"])
    athlete_intake_rows = read_csv(sport["athlete_intake"])
    athlete_manifest = read_json(sport["athlete_manifest"], {})

    local_candidate_paths = unique_values(athlete_rows, "local_candidate_path")
    approved_marker_paths = unique_values(athlete_rows, "approved_marker_path")
    team_board_paths = unique_values(athlete_rows, "team_review_board_path")
    team_board_count = (
        int(athlete_manifest.get("team_boards", 0))
        if isinstance(athlete_manifest, dict) and clean(athlete_manifest.get("team_boards")).isdigit()
        else len(team_board_paths)
    )
    local_candidate_files_present = existing_count(local_candidate_paths)
    approved_marker_files_present = existing_count(approved_marker_paths)
    logo_local_asset_rows = sum(1 for row in logo_rows if is_truthy(row.get("local_file_exists")))
    athlete_local_asset_rows = sum(1 for row in athlete_rows if is_truthy(row.get("local_candidate_exists")))

    summary = {
        "sport_family": sport_key,
        "sport_label": sport["sport_label"],
        "league_label": sport["league_label"],
        "status": "review_only_workflow_ready" if logo_rows or athlete_rows else "review_only_workflow_empty",
        "logo_contact_rows": len(logo_rows),
        "logo_intake_rows": len(logo_intake_rows),
        "athlete_candidate_rows": len(athlete_rows),
        "athlete_intake_rows": len(athlete_intake_rows),
        "athlete_team_boards": team_board_count,
        "team_board_paths": team_board_paths,
        "team_board_files_present": existing_count(team_board_paths),
        "logo_source_candidate_rows": sum(1 for row in logo_rows if clean(row.get("official_source_candidate"))),
        "athlete_source_candidate_rows": sum(1 for row in athlete_rows if clean(row.get("source_url"))),
        "source_candidate_only_rows": sum(1 for row in logo_rows if not is_truthy(row.get("local_file_exists"))) + sum(
            1 for row in athlete_rows if not is_truthy(row.get("local_candidate_exists"))
        ),
        "local_asset_present_rows": logo_local_asset_rows + athlete_local_asset_rows,
        "proposed_headshot_path_refs": sum(1 for path in local_candidate_paths if path.endswith("headshot.png")),
        "proposed_approved_marker_path_refs": sum(1 for path in approved_marker_paths if path.endswith(".approved")),
        "local_candidate_files_present": local_candidate_files_present,
        "approved_marker_files_present": approved_marker_files_present,
        "unsafe_logo_intake_rows": unsafe_intake_rows(logo_intake_rows),
        "unsafe_athlete_intake_rows": unsafe_intake_rows(athlete_intake_rows),
        "workflow_rows": len(logo_rows) + len(athlete_rows),
        "logo_contact_sheet": sport["logo_contact_sheet"].as_posix(),
        "logo_intake": sport["logo_intake"].as_posix(),
        "athlete_contact_sheet": sport["athlete_contact_sheet"].as_posix(),
        "athlete_intake": sport["athlete_intake"].as_posix(),
        "walkthrough": sport["walkthrough"].as_posix(),
        "workflow_board": sport["workflow_board"].as_posix(),
    }
    write_text(sport["workflow_board"], render_sport_board(summary, logo_rows, athlete_rows, generated_at))
    return summary


def render_sport_board(
    summary: Mapping[str, Any],
    logo_rows: list[Dict[str, str]],
    athlete_rows: list[Dict[str, str]],
    generated_at: str,
) -> str:
    lines = [
        f"# {summary['sport_label']} Asset Workflow Board",
        "",
        f"- Generated: `{generated_at}`",
        f"- League: `{summary['league_label']}`",
        f"- Status: `{summary['status']}`",
        "- Scope: review-only operator workflow board; it reads source/contact/intake artifacts and writes no assets.",
        "- Guardrails: no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` markers, no publish-ready movement, no publishing.",
        "",
        "## Next Human Action",
        "",
        "- Open `data/asset_registry/hockey_softball_asset_review_action_queue.md` first.",
        "- For a faster source-review sweep, open `data/asset_registry/hockey_softball_batch_source_review_helper.md` and work the next 10 `source_review_now` rows.",
        "- Work the queue top-to-bottom: open the listed board/contact sheet, then fill only the listed human-intake fields.",
        "- Source-candidate-only athlete rows keep identity/local-file/approval fields held until a named athlete and local candidate asset exist.",
        "",
        "## Review Order",
        "",
        f"1. Open `{summary['logo_contact_sheet']}` and compare logo candidates against source pages.",
        f"2. Record logo holds or source notes in `{summary['logo_intake']}`; keep registry actions hold-only until a human explicitly approves later.",
        f"3. Open `{summary['athlete_contact_sheet']}` and the team boards listed below.",
        f"4. Record athlete source and identity notes in `{summary['athlete_intake']}`; keep local-file review false until Mike manually supplies a candidate file.",
        f"5. Use `{summary['walkthrough']}` for row-by-row pacing when doing a batch review sweep.",
        "",
        "## Candidate Layer Clarity",
        "",
        "- `local_candidate_path` values are proposed manual target paths only; this report does not create `headshot.png` files.",
        "- `approved_marker_path` values are proposed manual marker paths only; this report does not create `.approved` markers.",
        f"- Proposed headshot path refs: `{summary['proposed_headshot_path_refs']}`; files currently present: `{summary['local_candidate_files_present']}`.",
        f"- Proposed `.approved` path refs: `{summary['proposed_approved_marker_path_refs']}`; markers currently present: `{summary['approved_marker_files_present']}`.",
        f"- Unsafe logo intake rows detected: `{summary['unsafe_logo_intake_rows']}`.",
        f"- Unsafe athlete intake rows detected: `{summary['unsafe_athlete_intake_rows']}`.",
        f"- Source-candidate-only rows: `{summary['source_candidate_only_rows']}`.",
        f"- Local asset present rows: `{summary['local_asset_present_rows']}`.",
        "",
        "## Logo Queue",
        "",
    ]
    for index, row in enumerate(logo_rows, start=1):
        lines.append(
            f"{index}. {clean(row.get('display_name'))} | {clean(row.get('asset_slot'))} | source={clean(row.get('official_source_candidate'))}"
        )
    lines.extend(["", "## Athlete Team Boards", ""])
    for index, row in enumerate(athlete_rows, start=1):
        lines.append(
            f"{index}. {clean(row.get('team_name'))} | board=`{clean(row.get('team_review_board_path'))}` | roster={clean(row.get('source_url'))}"
        )
    lines.append("")
    return "\n".join(lines)


def render_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Hockey/Softball Asset Workflow Readiness Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated: `{report['generated_at_utc']}`",
        "- Guardrails: no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` markers, no publish-ready movement, no publishing.",
        "",
        "## Open First",
        "",
        "- Foundation: `data/asset_registry/hockey_softball_asset_foundation_report.md`",
        "- Source review helper: `data/asset_registry/hockey_softball_source_review_helper_report.md`",
        "- Review action queue: `data/asset_registry/hockey_softball_asset_review_action_queue.md`",
        "- Batch source review helper: `data/asset_registry/hockey_softball_batch_source_review_helper.md`",
        "- Next decision worksheet: `data/asset_registry/hockey_softball_next_decision_worksheet.md`",
        "- Source priority worksheet: `data/asset_registry/hockey_softball_source_priority_worksheet.md`",
        "- Source verification checklist: `data/asset_registry/hockey_softball_source_verification_checklist.md`",
        "- Intake readiness summary: `data/asset_registry/hockey_softball_intake_readiness_summary.md`",
        "- Source map board: `data/asset_registry/hockey_softball_source_map_board.md`",
        "- Review triage worksheet: `data/asset_registry/hockey_softball_asset_review_triage.md`",
        "- Asset review readiness board: `data/asset_registry/hockey_softball_asset_review_readiness_board.md`",
        "- Quarantine download intake: `data/asset_registry/hockey_softball_quarantine_download_intake.md`",
        "- Women's hockey workflow board: `data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md`",
        "- Softball workflow board: `data/asset_registry/softball/softball_asset_workflow_board.md`",
        "",
        "## Review-Only Totals",
        "",
        f"- Workflow rows: `{report['totals']['workflow_rows']}`",
        f"- Logo contact rows: `{report['totals']['logo_contact_rows']}`",
        f"- Athlete candidate rows: `{report['totals']['athlete_candidate_rows']}`",
        f"- Proposed headshot path refs: `{report['totals']['proposed_headshot_path_refs']}`",
        f"- Proposed `.approved` path refs: `{report['totals']['proposed_approved_marker_path_refs']}`",
        f"- Local candidate files present: `{report['totals']['local_candidate_files_present']}`",
        f"- Approved markers present: `{report['totals']['approved_marker_files_present']}`",
        f"- Unsafe intake rows detected: `{report['totals']['unsafe_intake_rows']}`",
        f"- Action queue rows: `{report['totals']['action_queue_rows']}`",
        f"- Source-candidate-only rows: `{report['totals']['source_candidate_only_rows']}`",
        f"- Local asset present rows: `{report['totals']['local_asset_present_rows']}`",
        f"- Batch source-review helper rows: `{report['totals']['batch_source_review_rows']}`",
        f"- Source-reviewable now rows: `{report['totals']['batch_source_review_now_rows']}`",
        f"- Next batch rows: `{report['totals']['batch_source_review_next_rows']}`",
        f"- Local asset needed later rows: `{report['totals']['batch_source_review_local_asset_needed_later_rows']}`",
        f"- Next decision worksheet rows: `{report['totals']['next_decision_worksheet_rows']}`",
        f"- Next decision logo rows: `{report['totals']['next_decision_logo_rows']}`",
        f"- Next decision athlete rows: `{report['totals']['next_decision_athlete_rows']}`",
        f"- Next decision missing-local rows: `{report['totals']['next_decision_missing_local_candidate_asset_rows']}`",
        f"- Next decision download-approved yes rows: `{report['totals']['next_decision_download_approved_yes_rows']}`",
        f"- Next decision blank download-metadata rows: `{report['totals']['next_decision_blank_download_metadata_rows']}`",
        f"- Source priority rows: `{report['totals']['source_priority_rows']}`",
        f"- Source priority operator-verify rows: `{report['totals']['source_priority_operator_verify_required_rows']}`",
        f"- Source priority download-approved yes rows: `{report['totals']['source_priority_download_approved_yes_rows']}`",
        f"- Source priority blank source_url rows: `{report['totals']['source_priority_blank_source_url_rows']}`",
        f"- Source verification checklist rows: `{report['totals']['source_verification_checklist_rows']}`",
        f"- Source verification checklist blank source_url rows: `{report['totals']['source_verification_checklist_blank_source_url_rows']}`",
        f"- Intake readiness groups: `{report['totals']['intake_readiness_summary_groups']}`",
        f"- Intake readiness rows covered: `{report['totals']['intake_readiness_rows_covered']}`",
        f"- Intake readiness unsafe rows: `{report['totals']['intake_readiness_unsafe_guardrail_rows']}`",
        f"- Source map rows: `{report['totals']['source_map_rows']}`",
        f"- Source map download-approved yes rows: `{report['totals']['source_map_download_approved_yes_rows']}`",
        f"- Source map allowed-for-download rows: `{report['totals']['source_map_allowed_for_download_approved_yes_rows']}`",
        f"- Review triage rows: `{report['totals']['review_triage_rows']}`",
        f"- Review triage operator-verify source rows: `{report['totals']['review_triage_operator_verify_required_source_rows']}`",
        f"- Review triage download-approved yes rows: `{report['totals']['review_triage_download_approved_yes_rows']}`",
        f"- Review triage blank source_url rows: `{report['totals']['review_triage_blank_source_url_rows']}`",
        f"- Asset review readiness rows: `{report['totals']['asset_review_readiness_rows']}`",
        f"- Asset review readiness download-approved yes rows: `{report['totals']['asset_review_readiness_download_approved_yes_rows']}`",
        f"- Asset review readiness blank source_url rows: `{report['totals']['asset_review_readiness_blank_source_url_rows']}`",
        f"- Asset review readiness source/identity gap rows: `{report['totals']['asset_review_readiness_source_identity_gap_rows']}`",
        f"- Asset review readiness local candidate gap rows: `{report['totals']['asset_review_readiness_local_candidate_gap_rows']}`",
        f"- Quarantine download intake rows: `{report['totals']['quarantine_download_intake_rows']}`",
        f"- Quarantine download-approved yes rows: `{report['totals']['quarantine_download_approved_yes_rows']}`",
        "",
        "## Sport Boards",
        "",
    ]
    for row in report["summaries"]:
        lines.append(
            f"- {row['sport_label']} / {row['league_label']}: workflow_rows={row['workflow_rows']}, logo_rows={row['logo_contact_rows']}, athlete_rows={row['athlete_candidate_rows']}, board=`{row['workflow_board']}`"
        )
    lines.extend(
        [
            "",
            "## Operator Note",
            "",
            "This packet is intentionally observational. It makes the logo/contact-sheet/intake order visible and clarifies that athlete candidate paths are manual placeholders, not generated asset files.",
            "",
        ]
    )
    return "\n".join(lines)


def render_action_queue(action_rows: list[Dict[str, str]], generated_at: str) -> str:
    source_candidate_rows = sum(1 for row in action_rows if row["local_asset_present"] != "yes")
    local_asset_rows = sum(1 for row in action_rows if row["local_asset_present"] == "yes")
    lines = [
        "# Hockey/Softball Asset Review Action Queue",
        "",
        f"- Generated: `{generated_at}`",
        f"- Rows: `{len(action_rows)}`",
        f"- Source-candidate-only rows: `{source_candidate_rows}`",
        f"- Local asset present rows: `{local_asset_rows}`",
        "- Guardrails: review-only, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` marker writes, no publish-ready movement, no publishing.",
        "",
        "## How To Work This Queue",
        "",
        "1. Open the `board_to_open` path for the row.",
        "2. Compare the `source_url` and candidate context manually.",
        "3. Fill only the fields listed in `fields_to_fill_after_manual_review` inside `intake_to_fill`.",
        "4. Leave fields listed in `fields_to_keep_blank_until_review` blank until a human review happens.",
        "5. Keep every field listed in `fields_that_must_remain_hold` held unless a later explicit human-edited intake file supplies the missing evidence.",
        "",
        "## Queue",
        "",
    ]
    for index, row in enumerate(action_rows, start=1):
        lines.extend(
            [
                f"### {index}. {row['sport_label']} / {row['asset_domain']} / {row['display_name']}",
                "",
                f"- Priority: `{row['priority']}`",
                f"- Review state: `{row['review_state']}`",
                f"- Board: `{row['board_to_open']}`",
                f"- Contact sheet: `{row['contact_sheet_to_open']}`",
                f"- Intake: `{row['intake_to_fill']}`",
                f"- Source: `{row['source_url']}`",
                f"- Local asset: `{row['local_asset_path']}` (present: `{row['local_asset_present']}`)",
                f"- Fill after manual review: `{row['fields_to_fill_after_manual_review']}`",
                f"- Keep blank until review: `{row['fields_to_keep_blank_until_review']}`",
                f"- Must remain hold: `{row['fields_that_must_remain_hold']}`",
                f"- Next action: {row['next_human_action']}",
                "",
            ]
        )
    return "\n".join(lines)


def batch_source_review_bucket(row: Mapping[str, str]) -> str:
    if not clean(row.get("source_url")):
        return "source_missing_hold"
    if clean(row.get("local_asset_present")).lower() == "yes":
        return "local_asset_present_manual_identity_review"
    if clean(row.get("review_state")) == "approved_marker_present_manual_audit_required":
        return "marker_present_manual_audit_required"
    if clean(row.get("current_source_reviewed")).lower() != "yes":
        return "source_review_now"
    return "source_already_reviewed_wait_for_local_asset"


def batch_source_review_sort_key(row: Mapping[str, str]) -> tuple[int, str, str, str, str]:
    bucket_order = {
        "source_review_now": 0,
        "source_already_reviewed_wait_for_local_asset": 1,
        "local_asset_present_manual_identity_review": 2,
        "marker_present_manual_audit_required": 3,
        "source_missing_hold": 4,
    }
    bucket = batch_source_review_bucket(row)
    return (
        bucket_order.get(bucket, 9),
        clean(row.get("sport_family")),
        clean(row.get("asset_domain")),
        clean(row.get("entity_id")),
        clean(row.get("display_name")),
    )


def batch_source_review_rows(action_rows: list[Dict[str, str]], *, next_limit: int = 10) -> list[Dict[str, str]]:
    ranked_rows = sorted(action_rows, key=batch_source_review_sort_key)
    next_review_seen = 0
    rows: list[Dict[str, str]] = []
    for index, row in enumerate(ranked_rows, start=1):
        bucket = batch_source_review_bucket(row)
        batch_position = ""
        if bucket == "source_review_now" and next_review_seen < next_limit:
            next_review_seen += 1
            batch_position = f"next_{next_review_seen:02d}"
        fields_now = "none"
        fields_hold = clean(row.get("fields_that_must_remain_hold"))
        do_not_touch = "local asset files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads"
        if bucket == "source_review_now":
            fields_now = clean(row.get("fields_to_fill_after_manual_review"))
            fields_hold = clean(row.get("fields_that_must_remain_hold"))
            do_not_touch = (
                "operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; "
                "local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files"
            )
        elif bucket == "source_already_reviewed_wait_for_local_asset":
            fields_now = "none unless Mike is correcting a human-entered source review after reopening the source page"
            fields_hold = clean(row.get("fields_that_must_remain_hold"))
        elif bucket == "local_asset_present_manual_identity_review":
            fields_now = "none from this source-review batch; use a separate visual identity review before any approval-state change"
        elif bucket == "marker_present_manual_audit_required":
            fields_now = "none; investigate marker separately and keep approval state unchanged"
        elif bucket == "source_missing_hold":
            fields_hold = f"source_url_to_record; reviewed_by; reviewed_at_local; {clean(row.get('fields_that_must_remain_hold'))}"
        rows.append(
            {
                "review_order": str(index),
                "batch_position": batch_position,
                "batch_bucket": bucket,
                "sport_family": clean(row.get("sport_family")),
                "sport_label": clean(row.get("sport_label")),
                "asset_domain": clean(row.get("asset_domain")),
                "display_name": clean(row.get("display_name")),
                "candidate_id": clean(row.get("candidate_id")),
                "review_state": clean(row.get("review_state")),
                "source_url": clean(row.get("source_url")),
                "evidence_to_open": clean(row.get("source_url")),
                "board_to_open": clean(row.get("board_to_open")),
                "intake_to_fill": clean(row.get("intake_to_fill")),
                "fields_mike_can_fill_now": fields_now,
                "fields_to_keep_blank_or_held": fields_hold,
                "do_not_touch": do_not_touch,
                "local_asset_present": clean(row.get("local_asset_present")) or "no",
                "current_source_reviewed": clean(row.get("current_source_reviewed")) or "no",
                "current_identity_status": clean(row.get("current_identity_status")) or "no",
                "local_asset_needed_later": "no" if clean(row.get("local_asset_present")).lower() == "yes" else "yes",
                "guardrail_note": "review-only; no downloads; no approval-state changes; no headshot or marker writes",
            }
        )
    return rows


def next_decision_first_action_bucket(row: Mapping[str, str]) -> str:
    if not clean(row.get("source_url")):
        return "0_source_missing_hold"
    if clean(row.get("current_source_reviewed")).lower() != "yes":
        return "1_source_verification"
    if clean(row.get("local_asset_present")).lower() != "yes":
        return "2_missing_local_candidate_asset"
    return "3_local_asset_identity_review"


def next_decision_source_verification_bucket(row: Mapping[str, str]) -> str:
    source_url = clean(row.get("source_url")).lower()
    if not source_url:
        return "source_missing"
    if clean(row.get("current_source_reviewed")).lower() == "yes":
        return "source_reviewed_waiting_for_local_asset"
    if "thepwhl.com" in source_url or "theausl.com" in source_url:
        return "official_league_or_team_source_manual_verify"
    return "public_source_manual_verify"


def next_decision_download_law_status(row: Mapping[str, str]) -> str:
    if clean(row.get("local_asset_present")).lower() == "yes":
        return "download_not_needed_for_current_review_step"
    return "future_quarantine_download_intake_required"


def next_decision_sort_key(row: Mapping[str, str]) -> tuple[int, str, str, str, str]:
    bucket_order = {
        "0_source_missing_hold": 0,
        "1_source_verification": 1,
        "2_missing_local_candidate_asset": 2,
        "3_local_asset_identity_review": 3,
    }
    sport_order = {"womens_hockey": "0", "softball": "1"}
    first_action = next_decision_first_action_bucket(row)
    return (
        bucket_order.get(first_action, 9),
        sport_order.get(clean(row.get("sport_family")), "9"),
        clean(row.get("asset_domain")),
        clean(row.get("entity_id")),
        clean(row.get("candidate_id")),
    )


def next_decision_section(row: Mapping[str, str]) -> str:
    asset_domain = clean(row.get("asset_domain"))
    first_action = next_decision_first_action_bucket(row)
    if first_action == "0_source_missing_hold":
        return "source_missing_hold"
    if asset_domain == "logo" and first_action == "1_source_verification":
        return "logo_source_identity_review"
    if asset_domain == "logo":
        return "logo_wait_for_local_asset_after_source_review"
    if first_action == "1_source_verification":
        return "athlete_source_only_review"
    if first_action == "2_missing_local_candidate_asset":
        return "athlete_wait_for_local_asset_after_source_review"
    return "local_asset_identity_review"


def future_download_required_fields() -> str:
    return "download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use"


def next_decision_worksheet_rows(action_rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    selected = sorted(action_rows, key=next_decision_sort_key)
    rows: list[Dict[str, str]] = []
    for index, row in enumerate(selected, start=1):
        section = next_decision_section(row)
        asset_domain = clean(row.get("asset_domain"))
        local_asset_present = clean(row.get("local_asset_present")) or "no"
        first_action = next_decision_first_action_bucket(row)
        source_bucket = next_decision_source_verification_bucket(row)
        download_law = next_decision_download_law_status(row)
        missing_local = "no" if local_asset_present.lower() == "yes" else "yes"
        if asset_domain == "logo":
            if clean(row.get("current_source_reviewed")).lower() == "yes":
                fields_now = "none; source and identity are already recorded in the logo intake, so wait for a manually supplied local logo asset before any approval-state review"
                fields_blank = "generated worksheet cells stay blank; do not restamp reviewed_by/reviewed_at_local unless Mike is correcting the logo intake after reopening the source"
            else:
                fields_now = "operator_decision; source_reviewed; identity_match; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local"
                fields_blank = "generated worksheet cells stay blank until Mike manually opens the source; local asset path and registry action stay held until a local logo asset exists"
            do_not_touch = "local logo files; approval_status; registry_action; publish_ready; auto_approval; auto_publish; move_files; paid_apis; asset_downloads"
        else:
            fields_now = "source_reviewed; source_allowed_for_review_only; rights_reviewed; source_url_to_record; operator_notes; reviewed_by; reviewed_at_local"
            fields_blank = "operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; local_candidate_path; approved_marker_path until named athlete evidence and a local candidate asset exist"
            do_not_touch = (
                "operator_decision; identity_verified; local_file_reviewed; approval_status; registry_action; "
                "local_candidate_path; approved_marker_path; headshot.png; .approved; publish_ready; auto_approval; auto_publish; move_files"
            )
        rows.append(
            {
                "worksheet_order": f"ND{index:02d}",
                "worksheet_section": section,
                "sport_family": clean(row.get("sport_family")),
                "sport_label": clean(row.get("sport_label")),
                "asset_domain": asset_domain,
                "display_name": clean(row.get("display_name")),
                "candidate_id": clean(row.get("candidate_id")),
                "review_state": clean(row.get("review_state")),
                "first_action_bucket": first_action,
                "source_verification_bucket": source_bucket,
                "missing_local_candidate_asset": missing_local,
                "download_law_status": download_law,
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "quarantine_folder": SANCTIONED_QUARANTINE_ROOT.as_posix(),
                "future_download_required_fields": future_download_required_fields(),
                "source_to_open": clean(row.get("source_url")),
                "board_to_open": clean(row.get("board_to_open")),
                "contact_sheet_to_open": clean(row.get("contact_sheet_to_open")),
                "intake_to_fill": clean(row.get("intake_to_fill")),
                "intake_row_key": "; ".join(
                    part
                    for part in [
                        f"sport_family={clean(row.get('sport_family'))}",
                        f"entity_id={clean(row.get('entity_id'))}",
                        f"candidate_id={clean(row.get('candidate_id'))}",
                    ]
                    if not part.endswith("=")
                ),
                "fields_mike_can_fill_now": fields_now,
                "fields_that_must_stay_blank": fields_blank,
                "fields_that_must_remain_hold": clean(row.get("fields_that_must_remain_hold")),
                "operator_source_reviewed": "",
                "operator_source_allowed_for_review_only": "",
                "operator_identity_match": "",
                "operator_rights_reviewed": "",
                "operator_decision": "",
                "source_url_to_record": "",
                "operator_notes": "",
                "reviewed_by": "",
                "reviewed_at_local": "",
                "local_asset_present": local_asset_present,
                "local_asset_needed_later": missing_local,
                "do_not_touch": do_not_touch,
                "guardrail_note": "review-only worksheet; generated human-decision cells are blank; no downloads; no approval-state changes; no headshot or marker writes",
            }
        )
    return rows


def render_batch_source_review_helper(batch_rows: list[Dict[str, str]], generated_at: str, *, next_limit: int = 10) -> str:
    source_now = [row for row in batch_rows if row["batch_bucket"] == "source_review_now"]
    already_reviewed = [row for row in batch_rows if row["batch_bucket"] == "source_already_reviewed_wait_for_local_asset"]
    local_later = [row for row in batch_rows if row["local_asset_needed_later"] == "yes"]
    next_rows = [row for row in batch_rows if row["batch_position"]][:next_limit]
    lines = [
        "# Hockey/Softball Batch Source Review Helper",
        "",
        f"- Generated: `{generated_at}`",
        f"- Rows: `{len(batch_rows)}`",
        f"- Source-reviewable now: `{len(source_now)}`",
        f"- Already source-reviewed or waiting on local assets: `{len(already_reviewed)}`",
        f"- Local assets needed later: `{len(local_later)}`",
        f"- Next batch rows shown: `{len(next_rows)}`",
        "- Guardrails: review-only, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` marker writes, no publish-ready movement, no publishing.",
        "",
        "## Batch Rules",
        "",
        "1. Open each `evidence_to_open` URL manually.",
        "2. If the page is the expected official/team/roster/profile source, fill only `fields_mike_can_fill_now` in `intake_to_fill`.",
        "3. Keep every value in `fields_to_keep_blank_or_held` unchanged until visual identity/local asset review exists.",
        "4. Do not touch anything listed in `do_not_touch` during a source-review batch.",
        "5. Stop on any row where the source page is stale, missing, paywalled, ambiguous, or mismatched.",
        "",
        "## Next 10 Source-Review Rows",
        "",
    ]
    if not next_rows:
        lines.append("- No rows currently require batch source review. Keep the packet held until new source candidates or local assets exist.")
    for row in next_rows:
        lines.extend(
            [
                f"### {row['batch_position']} - {row['sport_label']} / {row['display_name']}",
                "",
                f"- Bucket: `{row['batch_bucket']}`",
                f"- Evidence source to open: `{row['evidence_to_open']}`",
                f"- Board: `{row['board_to_open']}`",
                f"- Intake to fill: `{row['intake_to_fill']}`",
                f"- Fields Mike can fill now: `{row['fields_mike_can_fill_now']}`",
                f"- Keep blank or held: `{row['fields_to_keep_blank_or_held']}`",
                f"- Do not touch: `{row['do_not_touch']}`",
                "",
            ]
        )
    lines.extend(["", "## Bucket Counts", ""])
    buckets = sorted({row["batch_bucket"] for row in batch_rows})
    for bucket in buckets:
        lines.append(f"- {bucket}: `{sum(1 for row in batch_rows if row['batch_bucket'] == bucket)}`")
    lines.extend(["", "## CSV Workflow", "", f"- Open `{BATCH_SOURCE_REVIEW_CSV.as_posix()}` and filter `batch_bucket=source_review_now` to continue past the first {next_limit} rows."])
    lines.append("- Keep `local_asset_needed_later=yes` rows out of visual identity or approval review until a human supplies a local candidate asset.")
    lines.append("")
    return "\n".join(lines)


def render_next_decision_worksheet(rows: list[Dict[str, str]], generated_at: str) -> str:
    logo_rows = [row for row in rows if row["asset_domain"] == "logo"]
    athlete_rows = [row for row in rows if row["asset_domain"] == "athlete_photo"]
    first_action_counts = Counter(row["first_action_bucket"] for row in rows)
    source_bucket_counts = Counter(row["source_verification_bucket"] for row in rows)
    missing_local_rows = [row for row in rows if row["missing_local_candidate_asset"] == "yes"]
    download_yes_rows = [row for row in rows if row["download_approved"] == "yes"]
    lines = [
        "# Hockey/Softball Next Decision Worksheet",
        "",
        f"- Generated: `{generated_at}`",
        f"- Rows: `{len(rows)}`",
        f"- Logo decision rows: `{len(logo_rows)}`",
        f"- Athlete source-only rows: `{len(athlete_rows)}`",
        f"- Missing local candidate asset rows: `{len(missing_local_rows)}`",
        f"- Download-approved yes rows: `{len(download_yes_rows)}`",
        "- Guardrails: review-only worksheet, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` marker writes, no publish-ready movement, no publishing.",
        "",
        "## How To Use",
        "",
        "1. Open each `source_to_open` manually, then the linked `board_to_open` if context is needed.",
        "2. Use the worksheet CSV for the next human pass; every generated human-decision cell is intentionally blank.",
        "3. Work `1_source_verification` rows first, then `2_missing_local_candidate_asset` rows that are already source-reviewed but still waiting for a local candidate asset.",
        "4. Future quarantine-download metadata fields default to `download_approved=no` or blank; Mike must fill them in a human-edited intake before any later quarantine-only download workflow can act.",
        "5. For logo rows, Mike may fill the listed source/identity fields after manual source review, but registry action stays hold-only until a local logo asset exists.",
        "6. For athlete rows, Mike may fill source/rights fields after opening the source page, but identity/local-file/approval fields stay blank or held until a named athlete and local candidate asset exist.",
        "7. Do not download assets, write headshots, create `.approved` markers, move files, or publish from this worksheet.",
        "",
        "## First Action Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in sorted(first_action_counts.items()))
    lines.extend(
        [
            "",
            "## Source Verification Buckets",
            "",
        ]
    )
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in sorted(source_bucket_counts.items()))
    lines.extend(
        [
            "",
            "## Future Quarantine-Download Fields",
            "",
            f"- Required future fields: `{future_download_required_fields()}`.",
            f"- Quarantine folder: `{SANCTIONED_QUARANTINE_ROOT.as_posix()}`.",
            "- Generated rows keep `download_approved=no`; `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` stay blank for human intake.",
            "- This worksheet does not trigger downloads and does not write quarantine files.",
        "",
        "## Next Decision Rows",
        "",
        ]
    )
    if not rows:
        lines.append("- No next decision rows are available; rerun the workflow readiness generator after source candidates or local assets change.")
    for row in rows:
        lines.extend(
            [
                f"### {row['worksheet_order']} - {row['sport_label']} / {row['asset_domain']} / {row['display_name']}",
                "",
                f"- Section: `{row['worksheet_section']}`",
                f"- First action: `{row['first_action_bucket']}`",
                f"- Source bucket: `{row['source_verification_bucket']}`",
                f"- Download law: `{row['download_law_status']}` (download_approved: `{row['download_approved']}`)",
                f"- Source to open: `{row['source_to_open']}`",
                f"- Board: `{row['board_to_open']}`",
                f"- Intake: `{row['intake_to_fill']}`",
                f"- Row key: `{row['intake_row_key']}`",
                f"- Mike can fill now after manual review: `{row['fields_mike_can_fill_now']}`",
                f"- Must stay blank: `{row['fields_that_must_stay_blank']}`",
                f"- Must remain hold: `{row['fields_that_must_remain_hold']}`",
                f"- Do not touch: `{row['do_not_touch']}`",
                "",
            ]
        )
    lines.extend(
        [
            "",
            "## CSV Reminder",
            "",
            f"- Worksheet CSV: `{NEXT_DECISION_WORKSHEET_CSV.as_posix()}`",
            "- Blank `operator_*`, `source_url_to_record`, `reviewed_by`, and `reviewed_at_local` cells are intentional generated blanks for Mike's manual pass.",
            "- This worksheet is advisory and does not write back to logo or athlete review intake files.",
            "",
        ]
    )
    return "\n".join(lines)


def source_domain(value: Any) -> str:
    parsed = urlparse(clean(value))
    return parsed.netloc.lower()


def source_priority_bucket(row: Mapping[str, str]) -> str:
    if not clean(row.get("source_url")):
        return "0_source_missing_hold"
    if clean(row.get("current_source_reviewed")).lower() == "yes":
        return "2_source_reviewed_waiting_for_local_asset"
    if source_domain(row.get("source_url")) in {"www.thepwhl.com", "thepwhl.com", "theausl.com", "www.theausl.com"}:
        return "1_official_league_or_team_manual_verify"
    return "3_public_source_manual_verify"


def source_candidate_level(row: Mapping[str, str]) -> str:
    asset_domain = clean(row.get("asset_domain"))
    candidate_id = clean(row.get("candidate_id")).lower()
    entity_id = clean(row.get("entity_id")).lower()
    if asset_domain == "logo" and candidate_id == "league_mark":
        return "league_logo_source_candidate"
    if asset_domain == "logo":
        return "team_logo_source_candidate"
    if "roster" in candidate_id:
        return "athlete_roster_source_candidate"
    if "profile" in candidate_id:
        return "athlete_team_profile_source_candidate"
    if "player_index" in candidate_id:
        return "athlete_league_player_index_source_candidate"
    return f"{asset_domain or 'asset'}_{entity_id or 'entity'}_source_candidate"


def source_priority_value(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "1_official_league_or_team_manual_verify":
        return "P0_OFFICIAL_LEAGUE_OR_TEAM_SOURCE"
    if bucket == "2_source_reviewed_waiting_for_local_asset":
        return "P1_SOURCE_REVIEWED_LOCAL_ASSET_MISSING"
    if bucket == "0_source_missing_hold":
        return "HOLD_SOURCE_MISSING"
    return "P2_PUBLIC_SOURCE_MANUAL_VERIFY"


def source_priority_safe_next_action(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "1_official_league_or_team_manual_verify":
        return "Open source_candidate_url manually; if it is the expected official league/team page, record source review only and keep download-law fields blank."
    if bucket == "2_source_reviewed_waiting_for_local_asset":
        return "Do not restamp source review unless correcting a human-entered row; wait for a human-supplied local candidate asset or future human-edited quarantine download intake."
    if bucket == "0_source_missing_hold":
        return "Hold until a public source candidate URL is added through a later review-only intake."
    return "Open source_candidate_url manually and treat it as advisory source evidence only; do not approve or download."


def source_priority_sort_key(row: Mapping[str, str]) -> tuple[int, str, str, str, str]:
    bucket_order = {
        "1_official_league_or_team_manual_verify": 0,
        "2_source_reviewed_waiting_for_local_asset": 1,
        "3_public_source_manual_verify": 2,
        "0_source_missing_hold": 3,
    }
    sport_order = {"womens_hockey": "0", "softball": "1"}
    return (
        bucket_order.get(clean(row.get("source_review_bucket")), 9),
        sport_order.get(clean(row.get("sport_family")), "9"),
        clean(row.get("asset_domain")),
        clean(row.get("candidate_entity_id")),
        clean(row.get("candidate_id")),
    )


def source_priority_rows(action_rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    for action_row in action_rows:
        bucket = source_priority_bucket(action_row)
        candidate_url = clean(action_row.get("source_url"))
        rows.append(
            {
                "source_priority_rank": "0",
                "source_review_bucket": bucket,
                "source_candidate_level": source_candidate_level(action_row),
                "sport_family": clean(action_row.get("sport_family")),
                "sport_label": clean(action_row.get("sport_label")),
                "league_name": SPORTS.get(clean(action_row.get("sport_family")), {}).get("league_label", ""),
                "asset_domain": clean(action_row.get("asset_domain")),
                "candidate_entity_id": clean(action_row.get("entity_id")),
                "display_name": clean(action_row.get("display_name")),
                "candidate_id": clean(action_row.get("candidate_id")),
                "operator_action": "manual_source_review_only",
                "source_priority": source_priority_value(action_row, bucket),
                "official_status": "official_league_or_team_candidate"
                if bucket in {"1_official_league_or_team_manual_verify", "2_source_reviewed_waiting_for_local_asset"}
                else "public_source_candidate",
                "confidence": "operator_verify_required" if bucket == "1_official_league_or_team_manual_verify" else "source_reviewed_waiting_for_local_asset",
                "operator_verify_required": "yes" if bucket == "1_official_league_or_team_manual_verify" else "no_unless_correcting",
                "source_domain": source_domain(candidate_url),
                "source_candidate_url": candidate_url,
                "linked_first_action_bucket": next_decision_first_action_bucket(action_row),
                "linked_missing_local_candidate_asset": "no" if clean(action_row.get("local_asset_present")).lower() == "yes" else "yes",
                "linked_review_state": clean(action_row.get("review_state")),
                "render_readiness": "not_render_ready_source_candidate_only",
                "safe_next_action": source_priority_safe_next_action(action_row, bucket),
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "approval_state_change": "false",
                "candidate_state_change": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    rows.sort(key=source_priority_sort_key)
    for index, row in enumerate(rows, start=1):
        row["source_priority_rank"] = str(index)
    return rows


def render_source_priority(rows: list[Dict[str, str]], generated_at: str) -> str:
    bucket_counts = Counter(row["source_review_bucket"] for row in rows)
    lines = [
        "# Hockey/Softball Source Priority Worksheet",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only source-candidate worksheet built from existing hockey/softball action rows. `source_candidate_url` is advisory evidence for manual review; the local-download-law `source_url` and `entity_id` fields remain blank and `download_approved=no` unless a later human-edited intake supplies the required metadata.",
        "",
        "## Summary",
        "",
        f"- Source priority rows: `{len(rows)}`",
        f"- Women's hockey rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'womens_hockey')}`",
        f"- Softball rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'softball')}`",
        f"- Operator-verify rows: `{sum(1 for row in rows if clean(row.get('operator_verify_required')).lower() == 'yes')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Source Review Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in sorted(bucket_counts.items()))
    lines.extend(
        [
            "",
            "## Safe Operator Path",
            "",
            "- Work `1_official_league_or_team_manual_verify` rows first; these are source-candidate URLs that still need a human source review.",
            "- Treat `source_candidate_url` as advisory source evidence only.",
            "- Do not copy `source_candidate_url` into download-law `source_url` without a later human-edited intake row.",
            "- Keep `download_approved=no` and leave `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` blank in generated rows.",
            "- This worksheet does not download files, approve assets, write headshots, create `.approved` markers, move files, or publish.",
            "",
            "## Worksheet Preview",
            "",
            "| Rank | Bucket | Sport | Asset | Entity | Candidate | Source | Safe Next Action |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows[:35]:
        lines.append(
            "| {rank} | {bucket} | {sport} | {asset} | {entity} | {candidate} | {url} | {action} |".format(
                rank=clean(row.get("source_priority_rank")),
                bucket=clean(row.get("source_review_bucket")),
                sport=clean(row.get("sport_family")),
                asset=clean(row.get("asset_domain")),
                entity=clean(row.get("candidate_entity_id")).replace("|", "/"),
                candidate=clean(row.get("candidate_id")).replace("|", "/"),
                url=clean(row.get("source_candidate_url")).replace("|", "%7C"),
                action=clean(row.get("safe_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def review_board_for_source_verification(sport_family: str) -> str:
    if sport_family == "womens_hockey":
        return "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md"
    if sport_family == "softball":
        return "data/asset_registry/softball/softball_athlete_photo_contact_sheet_index.md"
    return ""


def manual_intake_for_source_verification(sport_family: str) -> str:
    if sport_family == "womens_hockey":
        return "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"
    if sport_family == "softball":
        return "data/asset_registry/softball/softball_athlete_photo_review_intake.csv"
    return ""


def source_verification_checklist_rows(source_priority: list[Dict[str, str]]) -> list[Dict[str, str]]:
    grouped: dict[tuple[str, str], list[Dict[str, str]]] = {}
    for row in source_priority:
        if clean(row.get("asset_domain")) != "athlete_photo":
            continue
        if clean(row.get("source_review_bucket")) != "1_official_league_or_team_manual_verify":
            continue
        grouped.setdefault((clean(row.get("sport_family")), clean(row.get("candidate_entity_id"))), []).append(row)

    rows: list[Dict[str, str]] = []
    for (sport_family, entity_id), source_rows in sorted(grouped.items()):
        source_rows.sort(key=lambda item: int(clean(item.get("source_priority_rank")) or "0"))
        by_level = {clean(item.get("source_candidate_level")): clean(item.get("source_candidate_url")) for item in source_rows}
        ranks = [int(clean(item.get("source_priority_rank")) or "0") for item in source_rows]
        rank_range = f"{min(ranks)}-{max(ranks)}" if ranks else ""
        source_domains = sorted({clean(item.get("source_domain")) for item in source_rows if clean(item.get("source_domain"))})
        sport_label = clean(source_rows[0].get("sport_label")) if source_rows else ""
        league_name = clean(source_rows[0].get("league_name")) if source_rows else SPORTS.get(sport_family, {}).get("league_label", "")
        rows.append(
            {
                "verification_order": "0",
                "sport_family": sport_family,
                "sport_label": sport_label,
                "league_name": league_name,
                "candidate_entity_id": entity_id,
                "asset_domain": "athlete_photo",
                "verification_bucket": "official_roster_team_source_check",
                "league_player_index_url": by_level.get("athlete_league_player_index_source_candidate", ""),
                "team_roster_url": by_level.get("athlete_roster_source_candidate", ""),
                "team_profile_url": by_level.get("athlete_team_profile_source_candidate", ""),
                "source_priority_rank_range": rank_range,
                "source_priority_csv_filter": f"sport_family={sport_family};asset_domain=athlete_photo;candidate_entity_id={entity_id}",
                "source_priority_file": SOURCE_PRIORITY_CSV.as_posix(),
                "review_board_to_open": review_board_for_source_verification(sport_family),
                "manual_intake_file_to_open": manual_intake_for_source_verification(sport_family),
                "official_source_domain": ";".join(source_domains),
                "source_candidate_scope": "advisory_official_source_candidates_not_roster_truth_until_manual_confirmation",
                "source_identity_check": "confirm_team_or_roster_context_before_marking_source_reviewed",
                "roster_truth_status": "not_confirmed_by_generated_artifact",
                "local_asset_gap": "named_local_athlete_photo_candidate_missing",
                "human_fields_to_fill_now": "after_manual_source_open_only:source_reviewed;source_allowed_for_review_only;rights_reviewed;operator_notes",
                "human_fields_to_keep_blank": "download_approved;source_url;entity_id;rights_class;identity_confidence;intended_review_only_use;operator_decision;reviewed_by;reviewed_at_local",
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_source_reviewed": "",
                "operator_source_allowed_for_review_only": "",
                "operator_identity_match": "",
                "operator_rights_reviewed": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "approval_state_change": "false",
                "candidate_state_change": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    sport_order = {"womens_hockey": "0", "softball": "1"}
    rows.sort(key=lambda row: (sport_order.get(clean(row.get("sport_family")), "9"), clean(row.get("candidate_entity_id"))))
    for index, row in enumerate(rows, start=1):
        row["verification_order"] = f"SV{index:02d}"
    return rows


def render_source_verification_checklist(rows: list[Dict[str, str]], generated_at: str) -> str:
    lines = [
        "# Hockey/Softball Source Verification Checklist",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only checklist for opening the grouped official PWHL/AUSL source candidates behind athlete-photo review rows. It does not download images, approve assets, write headshots, create `.approved` markers, move files, or publish.",
        "Rows are source-candidate leads only. Official roster/team pages must be opened manually before any human marks source review fields; generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "",
        "## Summary",
        "",
        f"- Verification rows: `{len(rows)}`",
        f"- Women's hockey rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'womens_hockey')}`",
        f"- Softball rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'softball')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Operator Steps",
        "",
        "- Open `league_player_index_url`, `team_roster_url`, and `team_profile_url` manually where present.",
        "- Confirm the page is the expected official league/team context for `candidate_entity_id`; source candidates are not roster truth until manual confirmation.",
        "- If the source is valid, use `manual_intake_file_to_open` for human-entered source-review notes only.",
        "- Keep identity, local candidate, download-law, approval, and publish fields blank/held until a local candidate asset and separate human review exist.",
        "",
        "## Checklist Preview",
        "",
        "| Order | Sport | Entity | Source Ranks | League Index | Team Roster | Team Profile | Board | Intake | Fill Now | Keep Blank |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {order} | {sport} | {entity} | {ranks} | {league_url} | {roster_url} | {profile_url} | {board} | {intake} | {fill_now} | {keep_blank} |".format(
                order=clean(row.get("verification_order")),
                sport=clean(row.get("sport_family")),
                entity=clean(row.get("candidate_entity_id")).replace("|", "/"),
                ranks=clean(row.get("source_priority_rank_range")),
                league_url=clean(row.get("league_player_index_url")).replace("|", "/"),
                roster_url=clean(row.get("team_roster_url")).replace("|", "/"),
                profile_url=clean(row.get("team_profile_url")).replace("|", "/"),
                board=clean(row.get("review_board_to_open")).replace("|", "/"),
                intake=clean(row.get("manual_intake_file_to_open")).replace("|", "/"),
                fill_now=clean(row.get("human_fields_to_fill_now")).replace("|", "/"),
                keep_blank=clean(row.get("human_fields_to_keep_blank")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def intake_review_board(sport_family: str, asset_domain: str) -> str:
    if sport_family == "womens_hockey" and asset_domain == "logo":
        return "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md"
    if sport_family == "womens_hockey" and asset_domain == "athlete_photo":
        return "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md"
    if sport_family == "softball" and asset_domain == "logo":
        return "data/asset_registry/softball/softball_logo_contact_sheet.md"
    if sport_family == "softball" and asset_domain == "athlete_photo":
        return "data/asset_registry/softball/softball_athlete_photo_contact_sheet_index.md"
    return ""


def intake_identity_yes(row: Mapping[str, str], asset_domain: str) -> bool:
    if asset_domain == "logo":
        return clean(row.get("identity_match")).lower() == "yes"
    return clean(row.get("identity_verified")).lower() == "yes"


def intake_identity_no(row: Mapping[str, str], asset_domain: str) -> bool:
    if asset_domain == "logo":
        return clean(row.get("identity_match")).lower() != "yes"
    return clean(row.get("identity_verified")).lower() != "yes"


def intake_readiness_row(
    order: int,
    sport_key: str,
    sport: Mapping[str, Any],
    asset_domain: str,
    rows: list[Dict[str, str]],
    intake_file: Path,
) -> Dict[str, str]:
    source_yes = sum(1 for row in rows if clean(row.get("source_reviewed")).lower() == "yes")
    source_no = len(rows) - source_yes
    identity_yes = sum(1 for row in rows if intake_identity_yes(row, asset_domain))
    identity_no = sum(1 for row in rows if intake_identity_no(row, asset_domain))
    rights_yes = sum(1 for row in rows if clean(row.get("rights_reviewed")).lower() == "yes")
    rights_no = sum(1 for row in rows if "rights_reviewed" in row and clean(row.get("rights_reviewed")).lower() != "yes")
    human_metadata_rows = sum(1 for row in rows if clean(row.get("reviewed_by")) and clean(row.get("reviewed_at_local")))
    blank_metadata_rows = len(rows) - human_metadata_rows
    source_url_blank_rows = sum(1 for row in rows if not clean(row.get("source_url_to_record")))
    local_file_reviewed_yes = sum(1 for row in rows if clean(row.get("local_file_reviewed")).lower() == "yes")
    local_file_reviewed_no = sum(1 for row in rows if "local_file_reviewed" in row and clean(row.get("local_file_reviewed")).lower() != "yes")
    registry_hold_rows = sum(1 for row in rows if clean(row.get("registry_action")).startswith("hold_"))
    unsafe_rows = unsafe_intake_rows(rows)

    if asset_domain == "logo":
        readiness = "source_review_recorded_waiting_for_local_logo_asset"
        blocker = "local_logo_asset_missing_before_renderer_trust"
        action = "Open the logo contact sheet and intake; keep registry_action hold-only until a local logo candidate exists and a later explicit human approval is applied."
        fill_now = "none_if_source_and_identity_already_reviewed; otherwise revise operator_notes/source_url_to_record by human edit only"
        keep_blank = "download_approved;source_url;entity_id;rights_class;identity_confidence;intended_review_only_use"
    else:
        readiness = "source_and_identity_review_pending_waiting_for_named_local_athlete_asset"
        blocker = "named_athlete_identity_and_local_headshot_candidate_missing"
        action = "Open the source verification checklist and athlete contact sheet; after manual source-page review, fill source_reviewed/source_allowed_for_review_only/rights_reviewed only, leaving identity/local-file/approval fields held."
        fill_now = "after_manual_source_open_only:source_reviewed;source_allowed_for_review_only;rights_reviewed;operator_notes"
        keep_blank = "identity_verified;local_file_reviewed;source_url_to_record;reviewed_by;reviewed_at_local;download_approved;source_url;entity_id;rights_class;identity_confidence;intended_review_only_use"

    return {
        "summary_order": f"IR{order:02d}",
        "sport_family": sport_key,
        "sport_label": clean(sport.get("sport_label")),
        "league_name": clean(sport.get("league_label")),
        "asset_domain": asset_domain,
        "intake_file": intake_file.as_posix(),
        "review_board_to_open": intake_review_board(sport_key, asset_domain),
        "intake_rows": str(len(rows)),
        "source_reviewed_yes_rows": str(source_yes),
        "source_reviewed_no_rows": str(source_no),
        "identity_confirmed_yes_rows": str(identity_yes),
        "identity_confirmed_no_rows": str(identity_no),
        "rights_reviewed_yes_rows": str(rights_yes),
        "rights_reviewed_no_rows": str(rights_no),
        "human_review_metadata_rows": str(human_metadata_rows),
        "blank_human_review_metadata_rows": str(blank_metadata_rows),
        "source_url_to_record_blank_rows": str(source_url_blank_rows),
        "local_file_reviewed_yes_rows": str(local_file_reviewed_yes),
        "local_file_reviewed_no_rows": str(local_file_reviewed_no),
        "registry_hold_rows": str(registry_hold_rows),
        "unsafe_guardrail_rows": str(unsafe_rows),
        "render_feed_readiness": readiness,
        "primary_blocker": blocker,
        "next_operator_action": action,
        "fields_mike_can_fill_now": fill_now,
        "fields_that_must_stay_blank": keep_blank,
        "download_approved": "no",
        "source_url": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "review_only": "true",
        "approval_state_change": "false",
        "candidate_state_change": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def intake_readiness_summary_rows() -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    order = 1
    for sport_key, sport in SPORTS.items():
        rows.append(intake_readiness_row(order, sport_key, sport, "logo", read_csv(sport["logo_intake"]), sport["logo_intake"]))
        order += 1
        rows.append(intake_readiness_row(order, sport_key, sport, "athlete_photo", read_csv(sport["athlete_intake"]), sport["athlete_intake"]))
        order += 1
    return rows


def render_intake_readiness_summary(rows: list[Dict[str, str]], generated_at: str) -> str:
    lines = [
        "# Hockey/Softball Intake Readiness Summary",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only summary of the existing hockey/softball logo and athlete manual intake CSVs. It validates the intake posture for operator visibility only; it does not download images, approve assets, write headshots or logos, create `.approved` markers, move files, or publish.",
        "",
        "## Summary",
        "",
        f"- Intake groups: `{len(rows)}`",
        f"- Intake rows covered: `{sum(int(row['intake_rows']) for row in rows)}`",
        f"- Logo source-reviewed rows: `{sum(int(row['source_reviewed_yes_rows']) for row in rows if row['asset_domain'] == 'logo')}`",
        f"- Athlete source-pending rows: `{sum(int(row['source_reviewed_no_rows']) for row in rows if row['asset_domain'] == 'athlete_photo')}`",
        f"- Blank human-review metadata rows: `{sum(int(row['blank_human_review_metadata_rows']) for row in rows)}`",
        f"- Unsafe guardrail rows: `{sum(int(row['unsafe_guardrail_rows']) for row in rows)}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        "",
        "## Operator Path",
        "",
        "- Logo groups are source-reviewed, identity-confirmed, and still held because local logo candidate assets are missing.",
        "- Athlete groups are intentionally source/identity/local-file pending; use the source verification checklist before editing athlete intake rows.",
        "- Generated future download-law fields remain `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "- Keep approval, publish, movement, headshot/logo writes, and `.approved` marker fields false/held unless a later explicit human-edited intake workflow authorizes a separate step.",
        "",
        "## Intake Groups",
        "",
        "| Order | Sport | Asset | Rows | Source yes | Source no | Metadata blank | Unsafe | Readiness | Blocker |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {order} | {sport} | {asset} | {count} | {source_yes} | {source_no} | {metadata_blank} | {unsafe} | {readiness} | {blocker} |".format(
                order=clean(row.get("summary_order")),
                sport=clean(row.get("sport_family")),
                asset=clean(row.get("asset_domain")),
                count=clean(row.get("intake_rows")),
                source_yes=clean(row.get("source_reviewed_yes_rows")),
                source_no=clean(row.get("source_reviewed_no_rows")),
                metadata_blank=clean(row.get("blank_human_review_metadata_rows")),
                unsafe=clean(row.get("unsafe_guardrail_rows")),
                readiness=clean(row.get("render_feed_readiness")),
                blocker=clean(row.get("primary_blocker")),
            )
        )
    return "\n".join(lines) + "\n"


def source_map_static_lane(sport_family: str, lane: str) -> Dict[str, str]:
    if sport_family == "womens_hockey":
        values = {
            "official_action_photo_gallery_search": {
                "asset_domain": "action_photo",
                "source_category": "official_league_gallery",
                "source_tier": "P0_OFFICIAL_FREE_PUBLIC",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" PWHL "[team]" gallery OR recap site:thepwhl.com',
                "source_domain": "www.thepwhl.com",
                "evidence_use": "PWHL event/gallery lead; player/team/date context and official caption clues",
                "source_confidence": "medium_high_after_manual_url_review",
                "image_action_photo_fit": "potential_action_photo_candidate_discovery",
            },
            "reputable_news_editorial_search": {
                "asset_domain": "action_photo",
                "source_category": "editorial_wire_or_reputable_newsroom",
                "source_tier": "P1_RIGHTS_SENSITIVE_PUBLIC_REVIEW",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" PWHL game action Getty OR AP OR Reuters OR Imagn OR Ice Garden OR Inside the Rink',
                "source_domain": "gettyimages.com;apnews.com;reuters.com;imagn.com;theicegarden.com;insidetherink.com",
                "evidence_use": "caption/event/photographer/context lead only; rights-sensitive manual review required",
                "source_confidence": "medium_after_manual_source_review",
                "image_action_photo_fit": "potential_high_action_fit_if_identity_and_rights_are_clear",
            },
            "official_social_discovery": {
                "asset_domain": "action_photo",
                "source_category": "official_social",
                "source_tier": "P2_DISCOVERY_ONLY",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" PWHL "[team]" site:instagram.com OR site:x.com OR site:tiktok.com',
                "source_domain": "instagram.com;x.com;tiktok.com",
                "evidence_use": "official account discovery lead and caption context only",
                "source_confidence": "low_until_account_and_context_verified",
                "image_action_photo_fit": "discovery_only_not_download_or_approval",
            },
            "gray_area_public_parking_lot": {
                "asset_domain": "action_photo",
                "source_category": "gray_area_public_lead",
                "source_tier": "P5_PARK_ONLY",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" PWHL action photo public gallery',
                "source_domain": "operator_review_required",
                "evidence_use": "parking lot for possibly useful public leads when official/reputable coverage is thin",
                "source_confidence": "low_gray_area_lead_only",
                "image_action_photo_fit": "park_only_until_stronger_source_found",
            },
        }
    else:
        values = {
            "official_action_photo_gallery_search": {
                "asset_domain": "action_photo",
                "source_category": "official_league_gallery",
                "source_tier": "P0_OFFICIAL_FREE_PUBLIC",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" AUSL softball action gallery OR recap site:theausl.com OR site:auprosports.com',
                "source_domain": "theausl.com;auprosports.com",
                "evidence_use": "AUSL/Athletes Unlimited event-gallery lead; player/team/session context and caption clues",
                "source_confidence": "medium_high_after_manual_url_review",
                "image_action_photo_fit": "potential_action_photo_candidate_discovery",
            },
            "reputable_news_editorial_search": {
                "asset_domain": "action_photo",
                "source_category": "editorial_wire_or_reputable_newsroom",
                "source_tier": "P1_RIGHTS_SENSITIVE_PUBLIC_REVIEW",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" AUSL softball action Getty OR AP OR Reuters OR Imagn OR local sports gallery',
                "source_domain": "gettyimages.com;apnews.com;reuters.com;imagn.com;operator_review_required",
                "evidence_use": "caption/event/photographer/context lead only; rights-sensitive manual review required",
                "source_confidence": "medium_after_manual_source_review",
                "image_action_photo_fit": "potential_high_action_fit_if_identity_and_rights_are_clear",
            },
            "official_social_discovery": {
                "asset_domain": "action_photo",
                "source_category": "official_social",
                "source_tier": "P2_DISCOVERY_ONLY",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" AUSL softball site:instagram.com OR site:x.com OR site:tiktok.com',
                "source_domain": "instagram.com;x.com;tiktok.com",
                "evidence_use": "official account discovery lead and caption context only",
                "source_confidence": "low_until_account_and_context_verified",
                "image_action_photo_fit": "discovery_only_not_download_or_approval",
            },
            "gray_area_public_parking_lot": {
                "asset_domain": "action_photo",
                "source_category": "gray_area_public_lead",
                "source_tier": "P5_PARK_ONLY",
                "source_type": "search_macro",
                "source_url_or_search_macro": '"[athlete]" AUSL softball action photo public gallery',
                "source_domain": "operator_review_required",
                "evidence_use": "parking lot for possibly useful public leads when official/reputable coverage is thin",
                "source_confidence": "low_gray_area_lead_only",
                "image_action_photo_fit": "park_only_until_stronger_source_found",
            },
        }
    return values[lane]


def source_map_guardrail_fields() -> Dict[str, str]:
    return {
        "allowed_for_download_approved_yes": "false",
        "download_approved": "no",
        "source_url": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "review_only": "true",
        "approval_state_change": "false",
        "candidate_state_change": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "logo_writes": "false",
        "segmentation_writes": "false",
        "approved_marker_writes": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def source_map_board_rows(source_priority: list[Dict[str, str]]) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    order = 1
    for sport_family in ["womens_hockey", "softball"]:
        sport_rows = [row for row in source_priority if clean(row.get("sport_family")) == sport_family]
        sport_label = SPORTS[sport_family]["sport_label"]
        league_name = SPORTS[sport_family]["league_label"]
        logo_rows = [row for row in sport_rows if clean(row.get("asset_domain")) == "logo"]
        athlete_rows = [row for row in sport_rows if clean(row.get("asset_domain")) == "athlete_photo"]
        logo_domains = sorted({clean(row.get("source_domain")) for row in logo_rows if clean(row.get("source_domain"))})
        athlete_domains = sorted({clean(row.get("source_domain")) for row in athlete_rows if clean(row.get("source_domain"))})
        logo_url = clean(logo_rows[0].get("source_candidate_url")) if logo_rows else ""
        athlete_url = clean(athlete_rows[0].get("source_candidate_url")) if athlete_rows else ""
        rows.append(
            {
                "source_map_order": f"SM{order:02d}",
                "sport_family": sport_family,
                "sport_label": sport_label,
                "league_name": league_name,
                "source_lane": "official_logo_league_team_pages",
                "asset_domain": "logo",
                "source_category": "official_league_or_team_page",
                "source_tier": "P0_OFFICIAL_FREE_PUBLIC",
                "source_type": "existing_source_priority_rows",
                "source_url_or_search_macro": logo_url,
                "source_domain": ";".join(logo_domains),
                "existing_source_priority_rows": str(len(logo_rows)),
                "source_priority_filter": f"sport_family={sport_family};asset_domain=logo",
                "evidence_use": "league/team mark identity source candidate; not a local logo asset",
                "source_confidence": "high_after_manual_logo_source_review",
                "operator_verify_required": "yes",
                "roster_truth_limit": "logo_identity_only_not_roster_truth",
                "image_action_photo_fit": "not_action_photo",
                "known_limitations": "source page is not a downloadable asset and does not approve renderer trust without local candidate review",
                "next_operator_action": "Use logo contact sheet and intake readiness summary; keep registry hold-only until local logo candidate and separate human approval exist.",
                "manual_return_intake_hint": "data/asset_registry/hockey_softball_intake_readiness_summary.csv",
                **source_map_guardrail_fields(),
            }
        )
        order += 1
        rows.append(
            {
                "source_map_order": f"SM{order:02d}",
                "sport_family": sport_family,
                "sport_label": sport_label,
                "league_name": league_name,
                "source_lane": "official_roster_team_player_pages",
                "asset_domain": "athlete_photo",
                "source_category": "verification_only_player_or_roster_page",
                "source_tier": "P0_OFFICIAL_FREE_PUBLIC",
                "source_type": "existing_source_priority_rows",
                "source_url_or_search_macro": athlete_url,
                "source_domain": ";".join(athlete_domains),
                "existing_source_priority_rows": str(len(athlete_rows)),
                "source_priority_filter": f"sport_family={sport_family};asset_domain=athlete_photo",
                "evidence_use": "official roster/team/profile identity anchor; not roster truth until manual confirmation",
                "source_confidence": "high_for_identity_anchor_after_manual_review",
                "operator_verify_required": "yes",
                "roster_truth_limit": "not_roster_truth_until_human_confirms_current_team_and_named_player",
                "image_action_photo_fit": "identity_anchor_only",
                "known_limitations": "does not provide a local headshot/action-photo asset and does not approve identity or source rights automatically",
                "next_operator_action": "Open the source verification checklist; after manual source-page review, fill source-review fields only and keep identity/local-file approval held.",
                "manual_return_intake_hint": "data/asset_registry/hockey_softball_source_verification_checklist.csv",
                **source_map_guardrail_fields(),
            }
        )
        order += 1
        for lane in [
            "official_action_photo_gallery_search",
            "reputable_news_editorial_search",
            "official_social_discovery",
            "gray_area_public_parking_lot",
        ]:
            lane_values = source_map_static_lane(sport_family, lane)
            rows.append(
                {
                    "source_map_order": f"SM{order:02d}",
                    "sport_family": sport_family,
                    "sport_label": sport_label,
                    "league_name": league_name,
                    "source_lane": lane,
                    "existing_source_priority_rows": "0",
                    "source_priority_filter": "",
                    "operator_verify_required": "yes",
                    "roster_truth_limit": "advisory_discovery_not_roster_truth_or_approval",
                    "known_limitations": "URL/search lead only; no files may be downloaded and no render-feed trust changes from this board.",
                    "next_operator_action": "Paste URL/evidence leads into a future human-edited research return intake; keep download and approval fields blank/no.",
                    "manual_return_intake_hint": "future_human_edited_hockey_softball_source_research_return_intake",
                    **lane_values,
                    **source_map_guardrail_fields(),
                }
            )
            order += 1
    return rows


def render_source_map_board(rows: list[Dict[str, str]], generated_at: str) -> str:
    lines = [
        "# Hockey/Softball Source Map Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only H/S source-map board for PWHL/women's hockey and AUSL/softball asset/source candidate work. It separates official/free public sources, roster/team identity anchors, action-photo discovery lanes, reputable or rights-sensitive leads, official social discovery, and gray-area parking-lot leads.",
        "This board does not fetch source pages, download images, approve assets, write headshots/logos/cutouts, create `.approved` markers, move files, or publish.",
        "",
        "## Summary",
        "",
        f"- Source-map rows: `{len(rows)}`",
        f"- Women's hockey rows: `{sum(1 for row in rows if row['sport_family'] == 'womens_hockey')}`",
        f"- Softball rows: `{sum(1 for row in rows if row['sport_family'] == 'softball')}`",
        f"- Official/free public rows: `{sum(1 for row in rows if row['source_tier'] == 'P0_OFFICIAL_FREE_PUBLIC')}`",
        f"- Discovery/gray-area rows: `{sum(1 for row in rows if row['source_tier'] in {'P2_DISCOVERY_ONLY', 'P5_PARK_ONLY'})}`",
        f"- Rows allowed for download-approved yes: `{sum(1 for row in rows if row['allowed_for_download_approved_yes'] == 'true')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if row['download_approved'] == 'yes')}`",
        "",
        "## Operator Rules",
        "",
        "- Treat `source_url_or_search_macro` as advisory evidence or a manual search route only.",
        "- Do not copy a search macro into download-law `source_url`; that field stays blank here.",
        "- A future download remains possible only from a separate human-edited quarantine intake with `download_approved=yes` and all required local-download-law metadata filled.",
        "- Official roster/team pages are identity anchors, not automatic roster truth, photo approval, or render-feed trust.",
        "- Reputable/editorial/social/gray-area leads can help discovery, but they remain review-only until a human verifies identity, rights posture, event context, and source provenance.",
        "",
        "## Board Preview",
        "",
        "| Order | Sport | Lane | Asset | Category | Tier | Source/Search | Confidence | Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {order} | {sport} | {lane} | {asset} | {category} | {tier} | {source} | {confidence} | {action} |".format(
                order=clean(row.get("source_map_order")),
                sport=clean(row.get("sport_family")),
                lane=clean(row.get("source_lane")),
                asset=clean(row.get("asset_domain")),
                category=clean(row.get("source_category")),
                tier=clean(row.get("source_tier")),
                source=clean(row.get("source_url_or_search_macro")).replace("|", "/"),
                confidence=clean(row.get("source_confidence")),
                action=clean(row.get("next_operator_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def review_triage_group_key(row: Mapping[str, str]) -> tuple[str, str, str]:
    return (
        clean(row.get("sport_family")),
        clean(row.get("asset_domain")),
        clean(row.get("candidate_entity_id")),
    )


def preview_unique(rows: Iterable[Mapping[str, str]], field: str, limit: int = 3) -> str:
    values: list[str] = []
    for row in rows:
        value = clean(row.get(field))
        if value and value not in values:
            values.append(value)
    overflow = len(values) - limit
    preview = values[:limit]
    if overflow > 0:
        preview.append(f"+{overflow} more")
    return " | ".join(preview)


def review_triage_action_flags(rows: list[Mapping[str, str]]) -> list[str]:
    flags: list[str] = []
    asset_domain = clean(rows[0].get("asset_domain")) if rows else ""
    source_buckets = {clean(row.get("source_review_bucket")) for row in rows}
    if "1_official_league_or_team_manual_verify" in source_buckets:
        flags.append("official_team_logo_source_check" if asset_domain == "logo" else "official_roster_team_source_check")
    if any(clean(row.get("operator_verify_required")).lower() == "yes" for row in rows):
        flags.append("source_candidate_review")
        if asset_domain == "athlete_photo":
            flags.append("identity_source_verification")
    if "2_source_reviewed_waiting_for_local_asset" in source_buckets:
        flags.append("source_reviewed_waiting_for_local_asset")
    if any(clean(row.get("linked_missing_local_candidate_asset")).lower() == "yes" for row in rows):
        flags.append("missing_local_asset")
        flags.append("future_quarantine_download_intake_prep")
    if not flags:
        flags.append("source_metadata_watch")
    return flags


def review_triage_primary_action(flags: list[str]) -> str:
    priority = [
        "official_roster_team_source_check",
        "official_team_logo_source_check",
        "source_candidate_review",
        "identity_source_verification",
        "source_reviewed_waiting_for_local_asset",
        "missing_local_asset",
        "future_quarantine_download_intake_prep",
        "source_metadata_watch",
    ]
    for flag in priority:
        if flag in flags:
            return flag
    return flags[0]


def candidate_next_action_bucket(primary: str, asset_domain: str, flags: list[str]) -> str:
    if primary == "official_roster_team_source_check":
        return "official_roster_team_source_verify"
    if asset_domain == "logo" and "source_reviewed_waiting_for_local_asset" in flags:
        return "local_logo_candidate_needed"
    if asset_domain == "athlete_photo" and "missing_local_asset" in flags:
        return "local_athlete_candidate_needed"
    if "source_candidate_review" in flags:
        return "source_candidate_review"
    if "future_quarantine_download_intake_prep" in flags:
        return "future_quarantine_download_intake_prep"
    return "no_fix_audit"


def source_priority_rank_range(rows: list[Mapping[str, str]]) -> str:
    ranks = sorted(int(clean(row.get("source_priority_rank")) or "0") for row in rows if clean(row.get("source_priority_rank")).isdigit())
    if not ranks:
        return ""
    if len(ranks) == 1:
        return str(ranks[0])
    return f"{ranks[0]}-{ranks[-1]}"


def review_triage_file_paths(sport_family: str, asset_domain: str) -> tuple[str, str]:
    sport = SPORTS.get(sport_family, {})
    if asset_domain == "logo":
        return sport.get("logo_contact_sheet", Path("")).with_suffix(".md").as_posix(), sport.get("logo_intake", Path("")).as_posix()
    athlete_board = sport.get("athlete_contact_sheet", Path("")).with_name(f"{sport_family}_athlete_photo_contact_sheet_index.md")
    return athlete_board.as_posix(), sport.get("athlete_intake", Path("")).as_posix()


def review_triage_safe_next_action(primary: str, asset_domain: str) -> str:
    if primary == "official_roster_team_source_check":
        return "Open the official roster/team source candidates, mark source review only after manual verification, and keep identity/download fields blank."
    if primary == "official_team_logo_source_check":
        return "Open the official league/team logo source candidate and verify source quality only; no logo files are downloaded or approved."
    if primary == "source_candidate_review":
        return "Review advisory source_candidate_url values manually; record source-review evidence only and leave local-download-law fields blank."
    if primary == "identity_source_verification":
        return "Hold identity match until named local candidate assets exist; this row only confirms source evidence."
    if primary == "source_reviewed_waiting_for_local_asset":
        return "Do not restamp source review; wait for a human-supplied local candidate asset or later quarantine-download intake."
    if primary == "missing_local_asset":
        return "Confirm the local review asset is missing and prepare future human intake only if Mike later approves quarantine download metadata."
    if primary == "future_quarantine_download_intake_prep":
        return "Leave generated download-law fields blank/no; a later human-edited intake is required before any quarantine download tool can run."
    if asset_domain == "logo":
        return "Keep logo source metadata review-only; no logo approval or publish-ready movement."
    return "Keep as review-only source metadata; no downloads, approvals, headshot writes, or publishing."


def review_triage_sort_key(row: Mapping[str, str]) -> tuple[int, str, str, str]:
    action_order = {
        "official_roster_team_source_check": 0,
        "official_team_logo_source_check": 1,
        "source_candidate_review": 2,
        "identity_source_verification": 3,
        "source_reviewed_waiting_for_local_asset": 4,
        "missing_local_asset": 5,
        "future_quarantine_download_intake_prep": 6,
        "source_metadata_watch": 7,
    }
    sport_order = {"womens_hockey": "0", "softball": "1"}
    return (
        action_order.get(clean(row.get("primary_manual_action")), 99),
        sport_order.get(clean(row.get("sport_family")), "9"),
        clean(row.get("asset_domain")),
        clean(row.get("candidate_entity_id")),
    )


def review_triage_rows(source_rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[Dict[str, str]]] = {}
    for row in source_rows:
        grouped.setdefault(review_triage_group_key(row), []).append(row)

    rows: list[Dict[str, str]] = []
    for grouped_rows in grouped.values():
        first = grouped_rows[0]
        flags = review_triage_action_flags(grouped_rows)
        primary = review_triage_primary_action(flags)
        official_sources = [
            row
            for row in grouped_rows
            if clean(row.get("official_status")).startswith("official")
            or clean(row.get("source_review_bucket")) in {"1_official_league_or_team_manual_verify", "2_source_reviewed_waiting_for_local_asset"}
        ]
        operator_verify_sources = [row for row in grouped_rows if clean(row.get("operator_verify_required")).lower() == "yes"]
        source_reviewed_rows = [row for row in grouped_rows if clean(row.get("source_review_bucket")) == "2_source_reviewed_waiting_for_local_asset"]
        missing_local_rows = [row for row in grouped_rows if clean(row.get("linked_missing_local_candidate_asset")).lower() == "yes"]
        asset_domain = clean(first.get("asset_domain"))
        sport_family = clean(first.get("sport_family"))
        review_board_to_open, manual_intake_file_to_open = review_triage_file_paths(sport_family, asset_domain)
        bucket = candidate_next_action_bucket(primary, asset_domain, flags)
        rows.append(
            {
                "triage_rank": "0",
                "primary_manual_action": primary,
                "action_flags": "|".join(flags),
                "sport_family": sport_family,
                "sport_label": clean(first.get("sport_label")),
                "league_name": clean(first.get("league_name")),
                "asset_domain": asset_domain,
                "candidate_entity_id": clean(first.get("candidate_entity_id")),
                "display_name": clean(first.get("display_name")),
                "candidate_next_action_bucket": bucket,
                "source_tier": preview_unique(grouped_rows, "source_priority"),
                "source_priority_rows": str(len(grouped_rows)),
                "source_priority_rank_range": source_priority_rank_range(grouped_rows),
                "source_priority_csv_filter": "sport_family={sport};asset_domain={asset};candidate_entity_id={entity}".format(
                    sport=sport_family,
                    asset=asset_domain,
                    entity=clean(first.get("candidate_entity_id")),
                ),
                "official_source_candidate_rows": str(len(official_sources)),
                "operator_verify_required_source_rows": str(len(operator_verify_sources)),
                "source_reviewed_waiting_for_local_asset_rows": str(len(source_reviewed_rows)),
                "missing_local_candidate_asset_rows": str(len(missing_local_rows)),
                "candidate_id_preview": preview_unique(grouped_rows, "candidate_id"),
                "advisory_source_domains": preview_unique(grouped_rows, "source_domain"),
                "advisory_source_candidate_urls": preview_unique(grouped_rows, "source_candidate_url"),
                "review_board_to_open": review_board_to_open,
                "manual_intake_file_to_open": manual_intake_file_to_open,
                "future_download_intake_file": QUARANTINE_DOWNLOAD_INTAKE_CSV.as_posix(),
                "render_readiness": "not_render_ready_review_only",
                "safe_next_action": review_triage_safe_next_action(primary, asset_domain),
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "approval_state_change": "false",
                "candidate_state_change": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    rows.sort(key=review_triage_sort_key)
    for index, row in enumerate(rows, start=1):
        row["triage_rank"] = str(index)
    return rows


def render_review_triage(rows: list[Dict[str, str]], generated_at: str) -> str:
    action_counts = Counter(row["primary_manual_action"] for row in rows)
    bucket_counts = Counter(row["candidate_next_action_bucket"] for row in rows)
    lines = [
        "# Hockey/Softball Asset Review Triage",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only operator triage worksheet built from hockey/softball source-priority rows. Advisory source candidates remain in `advisory_source_candidate_urls`; generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "",
        "## Summary",
        "",
        f"- Triage rows: `{len(rows)}`",
        f"- Women's hockey rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'womens_hockey')}`",
        f"- Softball rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'softball')}`",
        f"- Logo rows: `{sum(1 for row in rows if clean(row.get('asset_domain')) == 'logo')}`",
        f"- Athlete rows: `{sum(1 for row in rows if clean(row.get('asset_domain')) == 'athlete_photo')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Candidate Next-Action Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in sorted(bucket_counts.items()))
    lines.extend(
        [
        "",
        "## Primary Manual Actions",
        "",
        ]
    )
    lines.extend(f"- {action}: `{count}`" for action, count in sorted(action_counts.items()))
    lines.extend(
        [
            "",
            "## Safe Operator Path",
            "",
            "- Work `official_roster_team_source_check` rows first; they group official PWHL/AUSL roster/team source candidates by team.",
            "- Work logo rows as source-reviewed or source-check holds only; this worksheet does not approve logo identity or write local logo files.",
            "- Treat `advisory_source_candidate_urls` as evidence to open manually, not as download-law `source_url` values.",
            "- Use `source_priority_csv_filter` to jump back to the exact source-priority source rows behind each triage row.",
            "- Open `review_board_to_open` for context and use `manual_intake_file_to_open` only for human-entered review notes.",
            "- Keep `download_approved=no` and leave `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` blank in generated rows.",
            "- Do not download assets, write headshots/logos, create `.approved` markers, move files, or publish from this worksheet.",
            "",
            "## Worksheet Preview",
            "",
            "| Rank | Bucket | Sport | Asset | Entity | Source Tier | Source Rows | Review Board | Manual Intake | Safe Next Action |",
            "| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in rows[:38]:
        lines.append(
            "| {rank} | {bucket} | {sport} | {asset} | {entity} | {tier} | {sources} | {board} | {intake} | {safe_action} |".format(
                rank=clean(row.get("triage_rank")),
                bucket=clean(row.get("candidate_next_action_bucket")),
                sport=clean(row.get("sport_family")),
                asset=clean(row.get("asset_domain")),
                entity=clean(row.get("candidate_entity_id")).replace("|", "/"),
                tier=clean(row.get("source_tier")).replace("|", "/"),
                sources=clean(row.get("source_priority_rows")),
                board=clean(row.get("review_board_to_open")).replace("|", "/"),
                intake=clean(row.get("manual_intake_file_to_open")).replace("|", "/"),
                safe_action=clean(row.get("safe_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def asset_review_readiness_bucket(row: Mapping[str, str]) -> str:
    bucket = clean(row.get("candidate_next_action_bucket"))
    asset_domain = clean(row.get("asset_domain"))
    if bucket == "official_roster_team_source_verify" and asset_domain == "athlete_photo":
        return "official_roster_source_verify_before_photo_review"
    if bucket == "local_logo_candidate_needed":
        return "local_logo_candidate_needed_before_logo_review"
    if bucket == "local_athlete_candidate_needed":
        return "local_athlete_candidate_needed_before_photo_review"
    if bucket == "future_quarantine_download_intake_prep":
        return "future_quarantine_download_intake_prep"
    return "no_fix_review_only_audit"


def asset_review_blocker(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "official_roster_source_verify_before_photo_review":
        return "source_and_identity_verification_required_before_local_photo_candidate"
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return "local_logo_candidate_missing_after_source_review"
    if bucket == "local_athlete_candidate_needed_before_photo_review":
        return "local_athlete_candidate_missing_after_source_review"
    if bucket == "future_quarantine_download_intake_prep":
        return "human_edited_quarantine_download_intake_required"
    return clean(row.get("render_readiness")) or "review_only_audit"


def asset_review_readiness_next_action(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "official_roster_source_verify_before_photo_review":
        return "Open review_board_to_open and advisory source URLs; verify roster/team source only, then keep photo identity and download-law fields blank until a local candidate exists."
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return "Open the logo contact sheet and manual intake file; wait for a human-supplied local logo candidate or later human-edited quarantine intake before logo review."
    if bucket == "local_athlete_candidate_needed_before_photo_review":
        return "Keep athlete photo review held until a named local candidate asset or later human-edited quarantine intake exists."
    if bucket == "future_quarantine_download_intake_prep":
        return "Prepare future quarantine intake metadata only if a human later approves it; generated rows do not authorize downloads."
    return "No fix required from this generated board; keep review-only guardrails and do not approve or publish."


def asset_review_source_identity_gap(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "official_roster_source_verify_before_photo_review":
        return "official_roster_or_team_source_not_manually_confirmed_for_named_photo_review"
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return "logo_source_metadata_reviewed_but_visual_logo_identity_not_reviewable_without_local_candidate"
    if bucket == "local_athlete_candidate_needed_before_photo_review":
        return "athlete_identity_not_reviewable_without_named_local_photo_candidate"
    if bucket == "future_quarantine_download_intake_prep":
        return "future_download_metadata_not_human_authorized"
    return "no_source_identity_gap_from_generated_board"


def asset_review_team_entity_check(row: Mapping[str, str], bucket: str) -> str:
    entity = clean(row.get("candidate_entity_id"))
    if bucket == "official_roster_source_verify_before_photo_review":
        return f"confirm_candidate_entity_id_matches_official_team_or_roster_context_before_marking_source_reviewed:{entity}"
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return f"confirm_local_logo_candidate_later_matches_entity_before_any_logo_identity_review:{entity}"
    return f"confirm_entity_context_before_any_future_manual_asset_action:{entity}"


def asset_review_local_candidate_gap(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "official_roster_source_verify_before_photo_review":
        return "named_local_athlete_photo_candidate_missing"
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return "local_logo_candidate_file_missing"
    if bucket == "local_athlete_candidate_needed_before_photo_review":
        return "named_local_athlete_photo_candidate_missing"
    if bucket == "future_quarantine_download_intake_prep":
        return "human_approved_quarantine_candidate_missing"
    return "no_local_candidate_gap_from_generated_board"


def asset_review_source_candidate_scope(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "official_roster_source_verify_before_photo_review":
        return "advisory_source_candidate_only_not_roster_truth_until_manual_official_confirmation"
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return "source_reviewed_metadata_only_not_visual_logo_approval"
    return "review_only_candidate_context_not_asset_approval"


def asset_review_fields_to_fill_now(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "official_roster_source_verify_before_photo_review":
        return "after_manual_source_open_only:source_reviewed;source_allowed_for_review_only;rights_reviewed;operator_notes"
    if bucket == "local_logo_candidate_needed_before_logo_review":
        return "none_from_generated_board;wait_for_human_local_logo_candidate_or_human_download_intake"
    if bucket == "local_athlete_candidate_needed_before_photo_review":
        return "none_from_generated_board;wait_for_named_local_photo_candidate_or_human_download_intake"
    if bucket == "future_quarantine_download_intake_prep":
        return "none_from_generated_board;future_download_fields_require_human_edited_intake"
    return "none_from_generated_board"


def asset_review_fields_to_keep_blank(row: Mapping[str, str], bucket: str) -> str:
    return (
        "download_approved;source_url;entity_id;rights_class;identity_confidence;"
        "intended_review_only_use;operator_decision;reviewed_by;reviewed_at_local"
    )


def asset_review_readiness_rows(triage_rows: list[Dict[str, str]]) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    for triage in triage_rows:
        bucket = asset_review_readiness_bucket(triage)
        rows.append(
            {
                "readiness_rank": "0",
                "asset_review_readiness_bucket": bucket,
                "candidate_next_action_bucket": clean(triage.get("candidate_next_action_bucket")),
                "sport_family": clean(triage.get("sport_family")),
                "sport_label": clean(triage.get("sport_label")),
                "league_name": clean(triage.get("league_name")),
                "asset_domain": clean(triage.get("asset_domain")),
                "candidate_entity_id": clean(triage.get("candidate_entity_id")),
                "source_tier": clean(triage.get("source_tier")),
                "source_domain": clean(triage.get("advisory_source_domains")),
                "advisory_source_candidate_urls": clean(triage.get("advisory_source_candidate_urls")),
                "triage_row_ref": f"{REVIEW_TRIAGE_CSV.as_posix()}#row={clean(triage.get('triage_rank'))}",
                "triage_file": REVIEW_TRIAGE_CSV.as_posix(),
                "source_priority_rank_range": clean(triage.get("source_priority_rank_range")),
                "source_priority_csv_filter": clean(triage.get("source_priority_csv_filter")),
                "source_priority_file": SOURCE_PRIORITY_CSV.as_posix(),
                "review_board_to_open": clean(triage.get("review_board_to_open")),
                "manual_intake_file_to_open": clean(triage.get("manual_intake_file_to_open")),
                "future_download_intake_file": clean(triage.get("future_download_intake_file")),
                "render_readiness": clean(triage.get("render_readiness")),
                "asset_review_blocker": asset_review_blocker(triage, bucket),
                "source_identity_gap": asset_review_source_identity_gap(triage, bucket),
                "team_entity_name_check": asset_review_team_entity_check(triage, bucket),
                "local_candidate_asset_gap": asset_review_local_candidate_gap(triage, bucket),
                "source_candidate_scope": asset_review_source_candidate_scope(triage, bucket),
                "human_fields_to_fill_now": asset_review_fields_to_fill_now(triage, bucket),
                "human_fields_to_keep_blank": asset_review_fields_to_keep_blank(triage, bucket),
                "future_download_intake_status": "human_edited_intake_required_no_generated_authorization",
                "next_manual_action": asset_review_readiness_next_action(triage, bucket),
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "approval_state_change": "false",
                "candidate_state_change": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    priority = {
        "official_roster_source_verify_before_photo_review": 10,
        "local_logo_candidate_needed_before_logo_review": 20,
        "local_athlete_candidate_needed_before_photo_review": 30,
        "future_quarantine_download_intake_prep": 40,
        "no_fix_review_only_audit": 90,
    }
    rows.sort(
        key=lambda row: (
            priority.get(row["asset_review_readiness_bucket"], 999),
            clean(row.get("sport_family")),
            clean(row.get("asset_domain")),
            clean(row.get("candidate_entity_id")),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["readiness_rank"] = str(index)
    return rows


def render_asset_review_readiness(rows: list[Dict[str, str]], generated_at: str) -> str:
    bucket_counts = Counter(row["asset_review_readiness_bucket"] for row in rows)
    source_identity_gap_rows = sum(
        1
        for row in rows
        if clean(row.get("source_identity_gap")) not in {"", "no_source_identity_gap_from_generated_board"}
    )
    local_candidate_gap_rows = sum(
        1
        for row in rows
        if clean(row.get("local_candidate_asset_gap")) not in {"", "no_local_candidate_gap_from_generated_board"}
    )
    lines = [
        "# Hockey/Softball Asset Review Readiness Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only board for deciding what must happen before hockey/softball source-candidate rows can become manual logo/photo review work. It does not download images, approve assets, write headshots or logos, create `.approved` markers, move files, or publish.",
        "`advisory_source_candidate_urls` remain evidence links to open manually. Generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "",
        "## Summary",
        "",
        f"- Readiness rows: `{len(rows)}`",
        f"- Women's hockey rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'womens_hockey')}`",
        f"- Softball rows: `{sum(1 for row in rows if clean(row.get('sport_family')) == 'softball')}`",
        f"- Athlete/photo rows: `{sum(1 for row in rows if clean(row.get('asset_domain')) == 'athlete_photo')}`",
        f"- Logo rows: `{sum(1 for row in rows if clean(row.get('asset_domain')) == 'logo')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        f"- Source/identity gap cue rows: `{source_identity_gap_rows}`",
        f"- Local candidate gap cue rows: `{local_candidate_gap_rows}`",
        "",
        "## Readiness Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in sorted(bucket_counts.items()))
    lines.extend(
        [
            "",
            "## Safe Operator Path",
            "",
            "- Verify official roster/team source rows before preparing any athlete photo review intake.",
            "- Treat broad public, reputable, licensed/news/photo, and gray-area links as review-only research leads unless official confirmation exists.",
            "- Use `review_board_to_open` for context and `manual_intake_file_to_open` only for human-entered review notes.",
            "- Use `source_identity_gap`, `team_entity_name_check`, and `local_candidate_asset_gap` to decide what blocks the row before touching intake fields.",
            "- Use `human_fields_to_fill_now` and `human_fields_to_keep_blank` so source review does not drift into identity, download, or approval state.",
            "- Future quarantine-download intake requires a later human-edited row; generated rows do not authorize download or approval.",
            "",
            "## Board Preview",
            "",
            "| Rank | Readiness Bucket | Sport | Asset | Entity | Triage Row | Board | Intake | Gap Cue | Team/Entity Check | Fill Now | Keep Blank | Next Manual Action |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows[:38]:
        lines.append(
            "| {rank} | {bucket} | {sport} | {asset} | {entity} | {triage_row} | {board} | {intake} | {gap} | {team_check} | {fill_now} | {keep_blank} | {action} |".format(
                rank=clean(row.get("readiness_rank")),
                bucket=clean(row.get("asset_review_readiness_bucket")),
                sport=clean(row.get("sport_family")),
                asset=clean(row.get("asset_domain")),
                entity=clean(row.get("candidate_entity_id")).replace("|", "/"),
                triage_row=clean(row.get("triage_row_ref")).replace("|", "/"),
                board=clean(row.get("review_board_to_open")).replace("|", "/"),
                intake=clean(row.get("manual_intake_file_to_open")).replace("|", "/"),
                gap=clean(row.get("source_identity_gap")).replace("|", "/"),
                team_check=clean(row.get("team_entity_name_check")).replace("|", "/"),
                fill_now=clean(row.get("human_fields_to_fill_now")).replace("|", "/"),
                keep_blank=clean(row.get("human_fields_to_keep_blank")).replace("|", "/"),
                action=clean(row.get("next_manual_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def proposed_quarantine_path(row: Mapping[str, str]) -> str:
    return (
        SANCTIONED_QUARANTINE_ROOT
        / clean(row.get("sport_family"))
        / clean(row.get("asset_domain"))
        / slug(row.get("entity_id"))
        / f"{slug(row.get('candidate_id') or row.get('display_name'))}.png"
    ).as_posix()


def quarantine_download_bucket(row: Mapping[str, str]) -> str:
    if clean(row.get("local_asset_present")).lower() == "yes":
        return "local_asset_present_no_download_needed"
    if clean(row.get("current_source_reviewed")).lower() == "yes":
        return "source_reviewed_waiting_for_human_download_intake"
    if clean(row.get("asset_domain")) == "athlete_photo":
        return "source_only_athlete_needs_manual_source_review_first"
    return "source_candidate_needs_manual_review_first"


def quarantine_download_intake_rows(
    action_rows: list[Dict[str, str]],
    existing: Mapping[tuple[str, str, str, str], Mapping[str, str]] | None = None,
) -> list[Dict[str, str]]:
    existing = existing or existing_quarantine_download_by_key()
    eligible_rows = [
        row
        for row in action_rows
        if clean(row.get("source_url")) and clean(row.get("local_asset_present")).lower() != "yes"
    ]
    rows: list[Dict[str, str]] = []
    for index, row in enumerate(eligible_rows, start=1):
        prior = existing.get(quarantine_download_key(row), {})
        download_approved = clean(prior.get("download_approved")) or "no"
        download_status = "human_approved_future_quarantine_candidate_pending_separate_tool" if download_approved.lower() == "yes" else "not_requested"
        rows.append(
            {
                "download_order": f"QD{index:02d}",
                "download_bucket": quarantine_download_bucket(row),
                "sport_family": clean(row.get("sport_family")),
                "sport_label": clean(row.get("sport_label")),
                "asset_domain": clean(row.get("asset_domain")),
                "entity_id": clean(row.get("entity_id")),
                "display_name": clean(row.get("display_name")),
                "candidate_id": clean(row.get("candidate_id")),
                "source_url": clean(prior.get("source_url")) or clean(row.get("source_url")),
                "source_review_status": clean(row.get("current_source_reviewed")) or "no",
                "identity_status": clean(row.get("current_identity_status")) or "no",
                "local_asset_present": clean(row.get("local_asset_present")) or "no",
                "download_approved": download_approved,
                "download_status": clean(prior.get("download_status")) or download_status,
                "source_url_required_if_approved": clean(prior.get("source_url")) or clean(row.get("source_url")),
                "entity_id_required_if_approved": clean(prior.get("entity_id_required_if_approved")) or clean(row.get("entity_id")),
                "rights_class": clean(prior.get("rights_class")) or "operator_rights_review_required",
                "identity_confidence": clean(prior.get("identity_confidence")) or "operator_fill_required",
                "intended_review_only_use": clean(prior.get("intended_review_only_use")) or "review_only_quarantine_candidate_check_not_renderer_approval",
                "operator_source_url": clean(prior.get("operator_source_url")),
                "operator_entity_id": clean(prior.get("operator_entity_id")),
                "operator_rights_class": clean(prior.get("operator_rights_class")),
                "operator_identity_confidence": clean(prior.get("operator_identity_confidence")),
                "operator_intended_review_only_use": clean(prior.get("operator_intended_review_only_use")),
                "operator_notes": clean(prior.get("operator_notes")),
                "reviewed_by": clean(prior.get("reviewed_by")),
                "reviewed_at_local": clean(prior.get("reviewed_at_local")),
                "quarantine_folder": SANCTIONED_QUARANTINE_ROOT.as_posix(),
                "proposed_quarantine_path": clean(prior.get("proposed_quarantine_path")) or proposed_quarantine_path(row),
                "separate_approval_required": "true",
                "approval_status": "not_approved",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
                "guardrail_note": "review-only future quarantine intake; generator does not download files or approve assets",
            }
        )
    return rows


def render_quarantine_download_intake(rows: list[Dict[str, str]], generated_at: str) -> str:
    approved_yes = sum(1 for row in rows if clean(row.get("download_approved")).lower() == "yes")
    bucket_counts = {bucket: sum(1 for row in rows if row["download_bucket"] == bucket) for bucket in sorted({row["download_bucket"] for row in rows})}
    lines = [
        "# Hockey/Softball Quarantine Download Intake",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only, human-edited intake for a future quarantine-only local asset candidate step. This generator does not download logos or athlete photos, write headshots, create `.approved` markers, approve identities, move files, publish, or create a publish-ready lane.",
        "",
        "A row is not eligible for any future quarantine download unless a human edits the CSV with `download_approved=yes`, source URL, entity ID, rights class, identity confidence, intended review-only use, and a separate approval step remains required after local review.",
        "",
        "## Summary",
        "",
        f"- Intake rows: `{len(rows)}`",
        f"- Rows with download_approved=yes: `{approved_yes}`",
        "- Default download_approved value: `no`",
        f"- Quarantine folder only: `{SANCTIONED_QUARANTINE_ROOT.as_posix()}`",
        f"- Download intake CSV: `{QUARANTINE_DOWNLOAD_INTAKE_CSV.as_posix()}`",
        f"- Policy canonical intake template: `{CANONICAL_DOWNLOAD_INTAKE_PATH.as_posix()}`",
        "",
        "## Buckets",
        "",
    ]
    if not bucket_counts:
        lines.append("- No future quarantine candidates are currently listed.")
    for bucket, count in bucket_counts.items():
        lines.append(f"- {bucket}: `{count}`")
    lines.extend(
        [
            "",
            "## Operator Rules",
            "",
            "1. Do not download from this packet.",
            "2. A future download tool may only consider human-edited rows where `download_approved=yes` and the required source, entity, rights, identity, and intended-use fields are complete.",
            "3. Any future file must land under `data/assets/quarantine/review_only_candidates/` and still requires separate visual identity and asset approval review.",
            "4. Keep `publish_ready`, `auto_approval`, `auto_publish`, `move_files`, `paid_apis`, and `asset_downloads` false in this generated intake.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    generated_at = generated_at_utc()
    summaries = [summarize_sport(sport_key, sport, generated_at) for sport_key, sport in SPORTS.items()]
    action_rows: list[Dict[str, str]] = []
    for sport_key, sport in SPORTS.items():
        logo_rows = read_csv(sport["logo_contact_sheet"])
        logo_intake_rows = read_csv(sport["logo_intake"])
        athlete_rows = read_csv(sport["athlete_contact_sheet"])
        athlete_intake_rows = read_csv(sport["athlete_intake"])
        action_rows.extend(logo_action_rows(sport_key, sport, logo_rows, logo_intake_rows))
        action_rows.extend(athlete_action_rows(sport_key, sport, athlete_rows, athlete_intake_rows))
    totals = {
        "workflow_rows": sum(int(row["workflow_rows"]) for row in summaries),
        "logo_contact_rows": sum(int(row["logo_contact_rows"]) for row in summaries),
        "logo_intake_rows": sum(int(row["logo_intake_rows"]) for row in summaries),
        "athlete_candidate_rows": sum(int(row["athlete_candidate_rows"]) for row in summaries),
        "athlete_intake_rows": sum(int(row["athlete_intake_rows"]) for row in summaries),
        "athlete_team_boards": sum(int(row["athlete_team_boards"]) for row in summaries),
        "proposed_headshot_path_refs": sum(int(row["proposed_headshot_path_refs"]) for row in summaries),
        "proposed_approved_marker_path_refs": sum(int(row["proposed_approved_marker_path_refs"]) for row in summaries),
        "local_candidate_files_present": sum(int(row["local_candidate_files_present"]) for row in summaries),
        "approved_marker_files_present": sum(int(row["approved_marker_files_present"]) for row in summaries),
        "unsafe_intake_rows": sum(int(row["unsafe_logo_intake_rows"]) + int(row["unsafe_athlete_intake_rows"]) for row in summaries),
        "source_candidate_only_rows": sum(int(row["source_candidate_only_rows"]) for row in summaries),
        "local_asset_present_rows": sum(int(row["local_asset_present_rows"]) for row in summaries),
        "action_queue_rows": len(action_rows),
    }
    batch_rows = batch_source_review_rows(action_rows)
    source_review_now_rows = sum(1 for row in batch_rows if row["batch_bucket"] == "source_review_now")
    batch_next_rows = sum(1 for row in batch_rows if row["batch_position"])
    local_asset_needed_later_rows = sum(1 for row in batch_rows if row["local_asset_needed_later"] == "yes")
    already_source_reviewed_rows = sum(1 for row in batch_rows if row["batch_bucket"] == "source_already_reviewed_wait_for_local_asset")
    totals.update(
        {
            "batch_source_review_rows": len(batch_rows),
            "batch_source_review_now_rows": source_review_now_rows,
            "batch_source_review_next_rows": batch_next_rows,
            "batch_source_review_local_asset_needed_later_rows": local_asset_needed_later_rows,
        }
    )
    next_decision_rows = next_decision_worksheet_rows(action_rows)
    next_decision_logo_rows = sum(1 for row in next_decision_rows if row["asset_domain"] == "logo")
    next_decision_athlete_rows = sum(1 for row in next_decision_rows if row["asset_domain"] == "athlete_photo")
    next_decision_first_action_counts = dict(sorted(Counter(row["first_action_bucket"] for row in next_decision_rows).items()))
    next_decision_source_verification_counts = dict(sorted(Counter(row["source_verification_bucket"] for row in next_decision_rows).items()))
    next_decision_missing_local_rows = sum(1 for row in next_decision_rows if row["missing_local_candidate_asset"] == "yes")
    next_decision_download_approved_yes_rows = sum(1 for row in next_decision_rows if row["download_approved"] == "yes")
    next_decision_blank_download_metadata_rows = sum(
        1
        for row in next_decision_rows
        if not clean(row.get("source_url"))
        and not clean(row.get("entity_id"))
        and not clean(row.get("rights_class"))
        and not clean(row.get("identity_confidence"))
        and not clean(row.get("intended_review_only_use"))
    )
    source_priority = source_priority_rows(action_rows)
    source_priority_operator_verify_rows = sum(1 for row in source_priority if clean(row.get("operator_verify_required")).lower() == "yes")
    source_priority_download_approved_yes_rows = sum(1 for row in source_priority if clean(row.get("download_approved")).lower() == "yes")
    source_priority_blank_source_url_rows = sum(1 for row in source_priority if not clean(row.get("source_url")))
    source_priority_athlete_rows = sum(1 for row in source_priority if clean(row.get("asset_domain")) == "athlete_photo")
    source_priority_logo_rows = sum(1 for row in source_priority if clean(row.get("asset_domain")) == "logo")
    source_map = source_map_board_rows(source_priority)
    source_map_download_approved_yes_rows = sum(1 for row in source_map if clean(row.get("download_approved")).lower() == "yes")
    source_map_allowed_for_download_yes_rows = sum(1 for row in source_map if clean(row.get("allowed_for_download_approved_yes")).lower() == "true")
    source_map_blank_source_url_rows = sum(1 for row in source_map if not clean(row.get("source_url")))
    source_map_official_free_public_rows = sum(1 for row in source_map if clean(row.get("source_tier")) == "P0_OFFICIAL_FREE_PUBLIC")
    source_verification_checklist = source_verification_checklist_rows(source_priority)
    source_verification_checklist_download_approved_yes_rows = sum(
        1 for row in source_verification_checklist if clean(row.get("download_approved")).lower() == "yes"
    )
    source_verification_checklist_blank_source_url_rows = sum(1 for row in source_verification_checklist if not clean(row.get("source_url")))
    source_verification_checklist_blank_human_review_rows = sum(
        1
        for row in source_verification_checklist
        if not clean(row.get("operator_source_reviewed"))
        and not clean(row.get("operator_source_allowed_for_review_only"))
        and not clean(row.get("operator_identity_match"))
        and not clean(row.get("operator_rights_reviewed"))
    )
    intake_readiness_summary = intake_readiness_summary_rows()
    intake_readiness_rows_covered = sum(int(row["intake_rows"]) for row in intake_readiness_summary)
    intake_readiness_logo_source_reviewed_rows = sum(
        int(row["source_reviewed_yes_rows"]) for row in intake_readiness_summary if clean(row.get("asset_domain")) == "logo"
    )
    intake_readiness_athlete_source_pending_rows = sum(
        int(row["source_reviewed_no_rows"]) for row in intake_readiness_summary if clean(row.get("asset_domain")) == "athlete_photo"
    )
    intake_readiness_blank_human_metadata_rows = sum(int(row["blank_human_review_metadata_rows"]) for row in intake_readiness_summary)
    intake_readiness_unsafe_guardrail_rows = sum(int(row["unsafe_guardrail_rows"]) for row in intake_readiness_summary)
    intake_readiness_download_approved_yes_rows = sum(
        1 for row in intake_readiness_summary if clean(row.get("download_approved")).lower() == "yes"
    )
    intake_readiness_blank_source_url_rows = sum(1 for row in intake_readiness_summary if not clean(row.get("source_url")))
    review_triage = review_triage_rows(source_priority)
    review_triage_logo_rows = sum(1 for row in review_triage if clean(row.get("asset_domain")) == "logo")
    review_triage_athlete_rows = sum(1 for row in review_triage if clean(row.get("asset_domain")) == "athlete_photo")
    review_triage_download_approved_yes_rows = sum(1 for row in review_triage if clean(row.get("download_approved")).lower() == "yes")
    review_triage_blank_source_url_rows = sum(1 for row in review_triage if not clean(row.get("source_url")))
    review_triage_operator_verify_source_rows = sum(int(row["operator_verify_required_source_rows"]) for row in review_triage)
    asset_review_readiness = asset_review_readiness_rows(review_triage)
    asset_review_readiness_logo_rows = sum(1 for row in asset_review_readiness if clean(row.get("asset_domain")) == "logo")
    asset_review_readiness_athlete_rows = sum(1 for row in asset_review_readiness if clean(row.get("asset_domain")) == "athlete_photo")
    asset_review_readiness_download_approved_yes_rows = sum(1 for row in asset_review_readiness if clean(row.get("download_approved")).lower() == "yes")
    asset_review_readiness_blank_source_url_rows = sum(1 for row in asset_review_readiness if not clean(row.get("source_url")))
    asset_review_readiness_source_identity_gap_rows = sum(
        1
        for row in asset_review_readiness
        if clean(row.get("source_identity_gap")) not in {"", "no_source_identity_gap_from_generated_board"}
    )
    asset_review_readiness_team_entity_check_rows = sum(1 for row in asset_review_readiness if clean(row.get("team_entity_name_check")))
    asset_review_readiness_local_candidate_gap_rows = sum(
        1
        for row in asset_review_readiness
        if clean(row.get("local_candidate_asset_gap")) not in {"", "no_local_candidate_gap_from_generated_board"}
    )
    quarantine_download_rows = quarantine_download_intake_rows(action_rows)
    quarantine_download_approved_yes_rows = sum(1 for row in quarantine_download_rows if clean(row.get("download_approved")).lower() == "yes")
    quarantine_download_source_reviewed_rows = sum(1 for row in quarantine_download_rows if clean(row.get("source_review_status")).lower() == "yes")
    quarantine_download_athlete_rows = sum(1 for row in quarantine_download_rows if clean(row.get("asset_domain")) == "athlete_photo")
    quarantine_download_logo_rows = sum(1 for row in quarantine_download_rows if clean(row.get("asset_domain")) == "logo")
    totals.update(
        {
            "next_decision_worksheet_rows": len(next_decision_rows),
            "next_decision_logo_rows": next_decision_logo_rows,
            "next_decision_athlete_rows": next_decision_athlete_rows,
            "next_decision_missing_local_candidate_asset_rows": next_decision_missing_local_rows,
            "next_decision_download_approved_yes_rows": next_decision_download_approved_yes_rows,
            "next_decision_blank_download_metadata_rows": next_decision_blank_download_metadata_rows,
            "source_priority_rows": len(source_priority),
            "source_priority_logo_rows": source_priority_logo_rows,
            "source_priority_athlete_rows": source_priority_athlete_rows,
            "source_priority_operator_verify_required_rows": source_priority_operator_verify_rows,
            "source_priority_download_approved_yes_rows": source_priority_download_approved_yes_rows,
            "source_priority_blank_source_url_rows": source_priority_blank_source_url_rows,
            "source_map_rows": len(source_map),
            "source_map_womens_hockey_rows": sum(1 for row in source_map if clean(row.get("sport_family")) == "womens_hockey"),
            "source_map_softball_rows": sum(1 for row in source_map if clean(row.get("sport_family")) == "softball"),
            "source_map_official_free_public_rows": source_map_official_free_public_rows,
            "source_map_download_approved_yes_rows": source_map_download_approved_yes_rows,
            "source_map_allowed_for_download_approved_yes_rows": source_map_allowed_for_download_yes_rows,
            "source_map_blank_source_url_rows": source_map_blank_source_url_rows,
            "source_verification_checklist_rows": len(source_verification_checklist),
            "source_verification_checklist_womens_hockey_rows": sum(
                1 for row in source_verification_checklist if clean(row.get("sport_family")) == "womens_hockey"
            ),
            "source_verification_checklist_softball_rows": sum(
                1 for row in source_verification_checklist if clean(row.get("sport_family")) == "softball"
            ),
            "source_verification_checklist_download_approved_yes_rows": source_verification_checklist_download_approved_yes_rows,
            "source_verification_checklist_blank_source_url_rows": source_verification_checklist_blank_source_url_rows,
            "source_verification_checklist_blank_human_review_rows": source_verification_checklist_blank_human_review_rows,
            "intake_readiness_summary_groups": len(intake_readiness_summary),
            "intake_readiness_rows_covered": intake_readiness_rows_covered,
            "intake_readiness_logo_source_reviewed_rows": intake_readiness_logo_source_reviewed_rows,
            "intake_readiness_athlete_source_pending_rows": intake_readiness_athlete_source_pending_rows,
            "intake_readiness_blank_human_metadata_rows": intake_readiness_blank_human_metadata_rows,
            "intake_readiness_unsafe_guardrail_rows": intake_readiness_unsafe_guardrail_rows,
            "intake_readiness_download_approved_yes_rows": intake_readiness_download_approved_yes_rows,
            "intake_readiness_blank_source_url_rows": intake_readiness_blank_source_url_rows,
            "review_triage_rows": len(review_triage),
            "review_triage_logo_rows": review_triage_logo_rows,
            "review_triage_athlete_rows": review_triage_athlete_rows,
            "review_triage_operator_verify_required_source_rows": review_triage_operator_verify_source_rows,
            "review_triage_download_approved_yes_rows": review_triage_download_approved_yes_rows,
            "review_triage_blank_source_url_rows": review_triage_blank_source_url_rows,
            "asset_review_readiness_rows": len(asset_review_readiness),
            "asset_review_readiness_logo_rows": asset_review_readiness_logo_rows,
            "asset_review_readiness_athlete_rows": asset_review_readiness_athlete_rows,
            "asset_review_readiness_download_approved_yes_rows": asset_review_readiness_download_approved_yes_rows,
            "asset_review_readiness_blank_source_url_rows": asset_review_readiness_blank_source_url_rows,
            "asset_review_readiness_source_identity_gap_rows": asset_review_readiness_source_identity_gap_rows,
            "asset_review_readiness_team_entity_check_rows": asset_review_readiness_team_entity_check_rows,
            "asset_review_readiness_local_candidate_gap_rows": asset_review_readiness_local_candidate_gap_rows,
            "quarantine_download_intake_rows": len(quarantine_download_rows),
            "quarantine_download_logo_rows": quarantine_download_logo_rows,
            "quarantine_download_athlete_rows": quarantine_download_athlete_rows,
            "quarantine_download_source_reviewed_rows": quarantine_download_source_reviewed_rows,
            "quarantine_download_approved_yes_rows": quarantine_download_approved_yes_rows,
        }
    )
    report = {
        "version": VERSION,
        "status": "hockey_softball_asset_workflow_readiness_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "totals": totals,
        "summaries": summaries,
        "action_queue": {
            "md": ACTION_QUEUE_MD.as_posix(),
            "csv": ACTION_QUEUE_CSV.as_posix(),
            "json": ACTION_QUEUE_JSON.as_posix(),
            "rows": len(action_rows),
        },
        "batch_source_review_helper": {
            "md": BATCH_SOURCE_REVIEW_MD.as_posix(),
            "csv": BATCH_SOURCE_REVIEW_CSV.as_posix(),
            "json": BATCH_SOURCE_REVIEW_JSON.as_posix(),
            "rows": len(batch_rows),
            "source_review_now_rows": source_review_now_rows,
            "next_rows": batch_next_rows,
        },
        "next_decision_worksheet": {
            "md": NEXT_DECISION_WORKSHEET_MD.as_posix(),
            "csv": NEXT_DECISION_WORKSHEET_CSV.as_posix(),
            "json": NEXT_DECISION_WORKSHEET_JSON.as_posix(),
            "rows": len(next_decision_rows),
            "logo_rows": next_decision_logo_rows,
            "athlete_rows": next_decision_athlete_rows,
            "missing_local_candidate_asset_rows": next_decision_missing_local_rows,
            "download_approved_yes_rows": next_decision_download_approved_yes_rows,
            "blank_download_metadata_rows": next_decision_blank_download_metadata_rows,
        },
        "source_priority_worksheet": {
            "md": SOURCE_PRIORITY_MD.as_posix(),
            "csv": SOURCE_PRIORITY_CSV.as_posix(),
            "json": SOURCE_PRIORITY_JSON.as_posix(),
            "rows": len(source_priority),
            "logo_rows": source_priority_logo_rows,
            "athlete_rows": source_priority_athlete_rows,
            "operator_verify_required_rows": source_priority_operator_verify_rows,
            "download_approved_yes_rows": source_priority_download_approved_yes_rows,
            "blank_source_url_rows": source_priority_blank_source_url_rows,
        },
        "source_map_board": {
            "md": SOURCE_MAP_BOARD_MD.as_posix(),
            "csv": SOURCE_MAP_BOARD_CSV.as_posix(),
            "json": SOURCE_MAP_BOARD_JSON.as_posix(),
            "rows": len(source_map),
            "womens_hockey_rows": sum(1 for row in source_map if clean(row.get("sport_family")) == "womens_hockey"),
            "softball_rows": sum(1 for row in source_map if clean(row.get("sport_family")) == "softball"),
            "official_free_public_rows": source_map_official_free_public_rows,
            "download_approved_yes_rows": source_map_download_approved_yes_rows,
            "allowed_for_download_approved_yes_rows": source_map_allowed_for_download_yes_rows,
            "blank_source_url_rows": source_map_blank_source_url_rows,
        },
        "source_verification_checklist": {
            "md": SOURCE_VERIFICATION_CHECKLIST_MD.as_posix(),
            "csv": SOURCE_VERIFICATION_CHECKLIST_CSV.as_posix(),
            "json": SOURCE_VERIFICATION_CHECKLIST_JSON.as_posix(),
            "rows": len(source_verification_checklist),
            "womens_hockey_rows": sum(1 for row in source_verification_checklist if clean(row.get("sport_family")) == "womens_hockey"),
            "softball_rows": sum(1 for row in source_verification_checklist if clean(row.get("sport_family")) == "softball"),
            "download_approved_yes_rows": source_verification_checklist_download_approved_yes_rows,
            "blank_source_url_rows": source_verification_checklist_blank_source_url_rows,
            "blank_human_review_rows": source_verification_checklist_blank_human_review_rows,
        },
        "intake_readiness_summary": {
            "md": INTAKE_READINESS_SUMMARY_MD.as_posix(),
            "csv": INTAKE_READINESS_SUMMARY_CSV.as_posix(),
            "json": INTAKE_READINESS_SUMMARY_JSON.as_posix(),
            "groups": len(intake_readiness_summary),
            "rows_covered": intake_readiness_rows_covered,
            "logo_source_reviewed_rows": intake_readiness_logo_source_reviewed_rows,
            "athlete_source_pending_rows": intake_readiness_athlete_source_pending_rows,
            "blank_human_review_metadata_rows": intake_readiness_blank_human_metadata_rows,
            "unsafe_guardrail_rows": intake_readiness_unsafe_guardrail_rows,
            "download_approved_yes_rows": intake_readiness_download_approved_yes_rows,
            "blank_source_url_rows": intake_readiness_blank_source_url_rows,
        },
        "review_triage": {
            "md": REVIEW_TRIAGE_MD.as_posix(),
            "csv": REVIEW_TRIAGE_CSV.as_posix(),
            "json": REVIEW_TRIAGE_JSON.as_posix(),
            "rows": len(review_triage),
            "logo_rows": review_triage_logo_rows,
            "athlete_rows": review_triage_athlete_rows,
            "operator_verify_required_source_rows": review_triage_operator_verify_source_rows,
            "download_approved_yes_rows": review_triage_download_approved_yes_rows,
            "blank_source_url_rows": review_triage_blank_source_url_rows,
        },
        "asset_review_readiness": {
            "md": ASSET_REVIEW_READINESS_MD.as_posix(),
            "csv": ASSET_REVIEW_READINESS_CSV.as_posix(),
            "json": ASSET_REVIEW_READINESS_JSON.as_posix(),
            "rows": len(asset_review_readiness),
            "logo_rows": asset_review_readiness_logo_rows,
            "athlete_rows": asset_review_readiness_athlete_rows,
            "download_approved_yes_rows": asset_review_readiness_download_approved_yes_rows,
            "blank_source_url_rows": asset_review_readiness_blank_source_url_rows,
            "source_identity_gap_rows": asset_review_readiness_source_identity_gap_rows,
            "team_entity_check_rows": asset_review_readiness_team_entity_check_rows,
            "local_candidate_gap_rows": asset_review_readiness_local_candidate_gap_rows,
        },
        "quarantine_download_intake": {
            "md": QUARANTINE_DOWNLOAD_INTAKE_MD.as_posix(),
            "csv": QUARANTINE_DOWNLOAD_INTAKE_CSV.as_posix(),
            "json": QUARANTINE_DOWNLOAD_INTAKE_JSON.as_posix(),
            "rows": len(quarantine_download_rows),
            "logo_rows": quarantine_download_logo_rows,
            "athlete_rows": quarantine_download_athlete_rows,
            "source_reviewed_rows": quarantine_download_source_reviewed_rows,
            "download_approved_yes_rows": quarantine_download_approved_yes_rows,
            "quarantine_folder": SANCTIONED_QUARANTINE_ROOT.as_posix(),
        },
    }
    action_payload = {
        "version": VERSION,
        "status": "hockey_softball_asset_review_action_queue_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "rows": len(action_rows),
        "source_candidate_only_rows": totals["source_candidate_only_rows"],
        "local_asset_present_rows": totals["local_asset_present_rows"],
        "action_rows": action_rows,
    }
    batch_payload = {
        "version": VERSION,
        "status": "hockey_softball_batch_source_review_helper_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "rows": len(batch_rows),
        "source_review_now_rows": source_review_now_rows,
        "already_source_reviewed_wait_for_local_asset_rows": already_source_reviewed_rows,
        "local_asset_needed_later_rows": local_asset_needed_later_rows,
        "next_review_rows": [row for row in batch_rows if row["batch_position"]],
        "batch_rows": batch_rows,
    }
    next_decision_payload = {
        "version": VERSION,
        "status": "hockey_softball_next_decision_worksheet_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "rows": len(next_decision_rows),
        "logo_rows": next_decision_logo_rows,
        "athlete_rows": next_decision_athlete_rows,
        "first_action_bucket_counts": next_decision_first_action_counts,
        "source_verification_bucket_counts": next_decision_source_verification_counts,
        "missing_local_candidate_asset_rows": next_decision_missing_local_rows,
        "download_approved_yes_rows": next_decision_download_approved_yes_rows,
        "blank_download_metadata_rows": next_decision_blank_download_metadata_rows,
        "future_download_required_fields": future_download_required_fields().split("|"),
        "quarantine_folder": SANCTIONED_QUARANTINE_ROOT.as_posix(),
        "blank_human_decision_fields": [
            "operator_source_reviewed",
            "operator_source_allowed_for_review_only",
            "operator_identity_match",
            "operator_rights_reviewed",
            "operator_decision",
            "source_url_to_record",
            "operator_notes",
            "reviewed_by",
            "reviewed_at_local",
        ],
        "worksheet_rows": next_decision_rows,
    }
    source_priority_payload = {
        "version": VERSION,
        "status": "hockey_softball_source_priority_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "source_priority_rows": len(source_priority),
        "logo_rows": source_priority_logo_rows,
        "athlete_rows": source_priority_athlete_rows,
        "womens_hockey_rows": sum(1 for row in source_priority if clean(row.get("sport_family")) == "womens_hockey"),
        "softball_rows": sum(1 for row in source_priority if clean(row.get("sport_family")) == "softball"),
        "operator_verify_required_rows": source_priority_operator_verify_rows,
        "download_approved_yes_rows": source_priority_download_approved_yes_rows,
        "blank_source_url_rows": source_priority_blank_source_url_rows,
        "source_review_bucket_counts": dict(sorted(Counter(row["source_review_bucket"] for row in source_priority).items())),
        "source_candidate_level_counts": dict(sorted(Counter(row["source_candidate_level"] for row in source_priority).items())),
        "worksheet_md": SOURCE_PRIORITY_MD.as_posix(),
        "worksheet_csv": SOURCE_PRIORITY_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "source_priority_rows_detail": source_priority,
    }
    source_map_payload = {
        "version": VERSION,
        "status": "hockey_softball_source_map_board_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "rows": len(source_map),
        "womens_hockey_rows": sum(1 for row in source_map if clean(row.get("sport_family")) == "womens_hockey"),
        "softball_rows": sum(1 for row in source_map if clean(row.get("sport_family")) == "softball"),
        "official_free_public_rows": source_map_official_free_public_rows,
        "download_approved_yes_rows": source_map_download_approved_yes_rows,
        "allowed_for_download_approved_yes_rows": source_map_allowed_for_download_yes_rows,
        "blank_source_url_rows": source_map_blank_source_url_rows,
        "worksheet_md": SOURCE_MAP_BOARD_MD.as_posix(),
        "worksheet_csv": SOURCE_MAP_BOARD_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "logo_writes": False,
        "segmentation_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "source_map_rows_detail": source_map,
    }
    source_verification_checklist_payload = {
        "version": VERSION,
        "status": "hockey_softball_source_verification_checklist_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "rows": len(source_verification_checklist),
        "womens_hockey_rows": sum(1 for row in source_verification_checklist if clean(row.get("sport_family")) == "womens_hockey"),
        "softball_rows": sum(1 for row in source_verification_checklist if clean(row.get("sport_family")) == "softball"),
        "download_approved_yes_rows": source_verification_checklist_download_approved_yes_rows,
        "blank_source_url_rows": source_verification_checklist_blank_source_url_rows,
        "blank_human_review_rows": source_verification_checklist_blank_human_review_rows,
        "worksheet_md": SOURCE_VERIFICATION_CHECKLIST_MD.as_posix(),
        "worksheet_csv": SOURCE_VERIFICATION_CHECKLIST_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "verification_rows_detail": source_verification_checklist,
    }
    intake_readiness_summary_payload = {
        "version": VERSION,
        "status": "hockey_softball_intake_readiness_summary_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "groups": len(intake_readiness_summary),
        "rows_covered": intake_readiness_rows_covered,
        "logo_source_reviewed_rows": intake_readiness_logo_source_reviewed_rows,
        "athlete_source_pending_rows": intake_readiness_athlete_source_pending_rows,
        "blank_human_review_metadata_rows": intake_readiness_blank_human_metadata_rows,
        "unsafe_guardrail_rows": intake_readiness_unsafe_guardrail_rows,
        "download_approved_yes_rows": intake_readiness_download_approved_yes_rows,
        "blank_source_url_rows": intake_readiness_blank_source_url_rows,
        "worksheet_md": INTAKE_READINESS_SUMMARY_MD.as_posix(),
        "worksheet_csv": INTAKE_READINESS_SUMMARY_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "summary_rows": intake_readiness_summary,
    }
    review_triage_payload = {
        "version": VERSION,
        "status": "hockey_softball_asset_review_triage_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "triage_rows": len(review_triage),
        "logo_rows": review_triage_logo_rows,
        "athlete_rows": review_triage_athlete_rows,
        "womens_hockey_rows": sum(1 for row in review_triage if clean(row.get("sport_family")) == "womens_hockey"),
        "softball_rows": sum(1 for row in review_triage if clean(row.get("sport_family")) == "softball"),
        "operator_verify_required_source_rows": review_triage_operator_verify_source_rows,
        "download_approved_yes_rows": review_triage_download_approved_yes_rows,
        "blank_source_url_rows": review_triage_blank_source_url_rows,
        "candidate_next_action_bucket_counts": dict(sorted(Counter(row["candidate_next_action_bucket"] for row in review_triage).items())),
        "primary_manual_action_counts": dict(sorted(Counter(row["primary_manual_action"] for row in review_triage).items())),
        "worksheet_md": REVIEW_TRIAGE_MD.as_posix(),
        "worksheet_csv": REVIEW_TRIAGE_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "triage_rows_detail": review_triage,
    }
    asset_review_readiness_payload = {
        "version": VERSION,
        "status": "hockey_softball_asset_review_readiness_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "readiness_rows": len(asset_review_readiness),
        "logo_rows": asset_review_readiness_logo_rows,
        "athlete_rows": asset_review_readiness_athlete_rows,
        "womens_hockey_rows": sum(1 for row in asset_review_readiness if clean(row.get("sport_family")) == "womens_hockey"),
        "softball_rows": sum(1 for row in asset_review_readiness if clean(row.get("sport_family")) == "softball"),
        "download_approved_yes_rows": asset_review_readiness_download_approved_yes_rows,
        "blank_source_url_rows": asset_review_readiness_blank_source_url_rows,
        "source_identity_gap_rows": asset_review_readiness_source_identity_gap_rows,
        "team_entity_check_rows": asset_review_readiness_team_entity_check_rows,
        "local_candidate_gap_rows": asset_review_readiness_local_candidate_gap_rows,
        "readiness_bucket_counts": dict(sorted(Counter(row["asset_review_readiness_bucket"] for row in asset_review_readiness).items())),
        "worksheet_md": ASSET_REVIEW_READINESS_MD.as_posix(),
        "worksheet_csv": ASSET_REVIEW_READINESS_CSV.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "readiness_rows_detail": asset_review_readiness,
    }
    quarantine_download_payload = {
        "version": VERSION,
        "status": "hockey_softball_quarantine_download_intake_ready",
        "generated_at_utc": generated_at,
        "guardrails": GUARDRAILS,
        "rows": len(quarantine_download_rows),
        "logo_rows": quarantine_download_logo_rows,
        "athlete_rows": quarantine_download_athlete_rows,
        "source_reviewed_rows": quarantine_download_source_reviewed_rows,
        "download_approved_yes_rows": quarantine_download_approved_yes_rows,
        "default_download_approved": "no",
        "quarantine_folder": SANCTIONED_QUARANTINE_ROOT.as_posix(),
        "canonical_download_intake": CANONICAL_DOWNLOAD_INTAKE_PATH.as_posix(),
        "required_human_fields_for_future_download": [
            "download_approved=yes",
            "source_url",
            "entity_id",
            "rights_class",
            "identity_confidence",
            "intended_review_only_use",
        ],
        "download_rows": quarantine_download_rows,
    }
    write_csv(ACTION_QUEUE_CSV, action_rows, ACTION_QUEUE_FIELDS)
    write_json(ACTION_QUEUE_JSON, action_payload)
    write_text(ACTION_QUEUE_MD, render_action_queue(action_rows, generated_at))
    write_csv(BATCH_SOURCE_REVIEW_CSV, batch_rows, BATCH_SOURCE_REVIEW_FIELDS)
    write_json(BATCH_SOURCE_REVIEW_JSON, batch_payload)
    write_text(BATCH_SOURCE_REVIEW_MD, render_batch_source_review_helper(batch_rows, generated_at))
    write_csv(NEXT_DECISION_WORKSHEET_CSV, next_decision_rows, NEXT_DECISION_WORKSHEET_FIELDS)
    write_json(NEXT_DECISION_WORKSHEET_JSON, next_decision_payload)
    write_text(NEXT_DECISION_WORKSHEET_MD, render_next_decision_worksheet(next_decision_rows, generated_at))
    write_csv(SOURCE_PRIORITY_CSV, source_priority, SOURCE_PRIORITY_FIELDS)
    write_json(SOURCE_PRIORITY_JSON, source_priority_payload)
    write_text(SOURCE_PRIORITY_MD, render_source_priority(source_priority, generated_at))
    write_csv(SOURCE_MAP_BOARD_CSV, source_map, SOURCE_MAP_BOARD_FIELDS)
    write_json(SOURCE_MAP_BOARD_JSON, source_map_payload)
    write_text(SOURCE_MAP_BOARD_MD, render_source_map_board(source_map, generated_at))
    write_csv(SOURCE_VERIFICATION_CHECKLIST_CSV, source_verification_checklist, SOURCE_VERIFICATION_CHECKLIST_FIELDS)
    write_json(SOURCE_VERIFICATION_CHECKLIST_JSON, source_verification_checklist_payload)
    write_text(SOURCE_VERIFICATION_CHECKLIST_MD, render_source_verification_checklist(source_verification_checklist, generated_at))
    write_csv(INTAKE_READINESS_SUMMARY_CSV, intake_readiness_summary, INTAKE_READINESS_SUMMARY_FIELDS)
    write_json(INTAKE_READINESS_SUMMARY_JSON, intake_readiness_summary_payload)
    write_text(INTAKE_READINESS_SUMMARY_MD, render_intake_readiness_summary(intake_readiness_summary, generated_at))
    write_csv(REVIEW_TRIAGE_CSV, review_triage, REVIEW_TRIAGE_FIELDS)
    write_json(REVIEW_TRIAGE_JSON, review_triage_payload)
    write_text(REVIEW_TRIAGE_MD, render_review_triage(review_triage, generated_at))
    write_csv(ASSET_REVIEW_READINESS_CSV, asset_review_readiness, ASSET_REVIEW_READINESS_FIELDS)
    write_json(ASSET_REVIEW_READINESS_JSON, asset_review_readiness_payload)
    write_text(ASSET_REVIEW_READINESS_MD, render_asset_review_readiness(asset_review_readiness, generated_at))
    write_csv(QUARANTINE_DOWNLOAD_INTAKE_CSV, quarantine_download_rows, QUARANTINE_DOWNLOAD_INTAKE_FIELDS)
    write_json(QUARANTINE_DOWNLOAD_INTAKE_JSON, quarantine_download_payload)
    write_text(QUARANTINE_DOWNLOAD_INTAKE_MD, render_quarantine_download_intake(quarantine_download_rows, generated_at))
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, render_report(report))
    print(json.dumps({"status": report["status"], "workflow_rows": totals["workflow_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
