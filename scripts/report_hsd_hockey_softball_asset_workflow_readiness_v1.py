from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, read_csv, read_json, write_csv, write_json, write_text


VERSION = "hsd-hockey-softball-asset-workflow-readiness-v1-review-only"
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
REVIEW_TRIAGE_MD = Path("data/asset_registry/hockey_softball_asset_review_triage.md")
REVIEW_TRIAGE_CSV = Path("data/asset_registry/hockey_softball_asset_review_triage.csv")
REVIEW_TRIAGE_JSON = Path("data/asset_registry/hockey_softball_asset_review_triage.json")
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
    "source_priority_rows",
    "official_source_candidate_rows",
    "operator_verify_required_source_rows",
    "source_reviewed_waiting_for_local_asset_rows",
    "missing_local_candidate_asset_rows",
    "candidate_id_preview",
    "advisory_source_domains",
    "advisory_source_candidate_urls",
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
    return datetime.now(timezone.utc).isoformat()


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
        "- Review triage worksheet: `data/asset_registry/hockey_softball_asset_review_triage.md`",
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
        f"- Review triage rows: `{report['totals']['review_triage_rows']}`",
        f"- Review triage operator-verify source rows: `{report['totals']['review_triage_operator_verify_required_source_rows']}`",
        f"- Review triage download-approved yes rows: `{report['totals']['review_triage_download_approved_yes_rows']}`",
        f"- Review triage blank source_url rows: `{report['totals']['review_triage_blank_source_url_rows']}`",
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
        rows.append(
            {
                "triage_rank": "0",
                "primary_manual_action": primary,
                "action_flags": "|".join(flags),
                "sport_family": clean(first.get("sport_family")),
                "sport_label": clean(first.get("sport_label")),
                "league_name": clean(first.get("league_name")),
                "asset_domain": asset_domain,
                "candidate_entity_id": clean(first.get("candidate_entity_id")),
                "display_name": clean(first.get("display_name")),
                "source_priority_rows": str(len(grouped_rows)),
                "official_source_candidate_rows": str(len(official_sources)),
                "operator_verify_required_source_rows": str(len(operator_verify_sources)),
                "source_reviewed_waiting_for_local_asset_rows": str(len(source_reviewed_rows)),
                "missing_local_candidate_asset_rows": str(len(missing_local_rows)),
                "candidate_id_preview": preview_unique(grouped_rows, "candidate_id"),
                "advisory_source_domains": preview_unique(grouped_rows, "source_domain"),
                "advisory_source_candidate_urls": preview_unique(grouped_rows, "source_candidate_url"),
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
        "## Primary Manual Actions",
        "",
    ]
    lines.extend(f"- {action}: `{count}`" for action, count in sorted(action_counts.items()))
    lines.extend(
        [
            "",
            "## Safe Operator Path",
            "",
            "- Work `official_roster_team_source_check` rows first; they group official PWHL/AUSL roster/team source candidates by team.",
            "- Work logo rows as source-reviewed or source-check holds only; this worksheet does not approve logo identity or write local logo files.",
            "- Treat `advisory_source_candidate_urls` as evidence to open manually, not as download-law `source_url` values.",
            "- Keep `download_approved=no` and leave `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` blank in generated rows.",
            "- Do not download assets, write headshots/logos, create `.approved` markers, move files, or publish from this worksheet.",
            "",
            "## Worksheet Preview",
            "",
            "| Rank | Action | Sport | Asset | Entity | Source Rows | Verify Sources | Missing Local | Safe Next Action |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows[:38]:
        lines.append(
            "| {rank} | {action} | {sport} | {asset} | {entity} | {sources} | {verify} | {missing} | {safe_action} |".format(
                rank=clean(row.get("triage_rank")),
                action=clean(row.get("primary_manual_action")),
                sport=clean(row.get("sport_family")),
                asset=clean(row.get("asset_domain")),
                entity=clean(row.get("candidate_entity_id")).replace("|", "/"),
                sources=clean(row.get("source_priority_rows")),
                verify=clean(row.get("operator_verify_required_source_rows")),
                missing=clean(row.get("missing_local_candidate_asset_rows")),
                safe_action=clean(row.get("safe_next_action")).replace("|", "/"),
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
    review_triage = review_triage_rows(source_priority)
    review_triage_logo_rows = sum(1 for row in review_triage if clean(row.get("asset_domain")) == "logo")
    review_triage_athlete_rows = sum(1 for row in review_triage if clean(row.get("asset_domain")) == "athlete_photo")
    review_triage_download_approved_yes_rows = sum(1 for row in review_triage if clean(row.get("download_approved")).lower() == "yes")
    review_triage_blank_source_url_rows = sum(1 for row in review_triage if not clean(row.get("source_url")))
    review_triage_operator_verify_source_rows = sum(int(row["operator_verify_required_source_rows"]) for row in review_triage)
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
            "review_triage_rows": len(review_triage),
            "review_triage_logo_rows": review_triage_logo_rows,
            "review_triage_athlete_rows": review_triage_athlete_rows,
            "review_triage_operator_verify_required_source_rows": review_triage_operator_verify_source_rows,
            "review_triage_download_approved_yes_rows": review_triage_download_approved_yes_rows,
            "review_triage_blank_source_url_rows": review_triage_blank_source_url_rows,
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
    write_csv(REVIEW_TRIAGE_CSV, review_triage, REVIEW_TRIAGE_FIELDS)
    write_json(REVIEW_TRIAGE_JSON, review_triage_payload)
    write_text(REVIEW_TRIAGE_MD, render_review_triage(review_triage, generated_at))
    write_csv(QUARANTINE_DOWNLOAD_INTAKE_CSV, quarantine_download_rows, QUARANTINE_DOWNLOAD_INTAKE_FIELDS)
    write_json(QUARANTINE_DOWNLOAD_INTAKE_JSON, quarantine_download_payload)
    write_text(QUARANTINE_DOWNLOAD_INTAKE_MD, render_quarantine_download_intake(quarantine_download_rows, generated_at))
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, render_report(report))
    print(json.dumps({"status": report["status"], "workflow_rows": totals["workflow_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
