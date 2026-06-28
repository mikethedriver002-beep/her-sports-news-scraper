from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

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


def next_decision_worksheet_rows(
    action_rows: list[Dict[str, str]],
    *,
    logo_limit: int = 6,
    athlete_limit: int = 6,
) -> list[Dict[str, str]]:
    logo_review_now = [
        row
        for row in action_rows
        if clean(row.get("asset_domain")) == "logo" and clean(row.get("current_source_reviewed")).lower() != "yes"
    ]
    logo_wait_rows = [
        row
        for row in action_rows
        if clean(row.get("asset_domain")) == "logo"
        and clean(row.get("current_source_reviewed")).lower() == "yes"
        and clean(row.get("local_asset_present")).lower() != "yes"
    ]
    logo_rows = logo_review_now[:logo_limit]
    if len(logo_rows) < logo_limit:
        logo_rows.extend(logo_wait_rows[: logo_limit - len(logo_rows)])
    athlete_rows = [
        row
        for row in action_rows
        if clean(row.get("asset_domain")) == "athlete_photo" and clean(row.get("current_source_reviewed")).lower() != "yes"
    ][:athlete_limit]
    selected: list[tuple[str, Dict[str, str]]] = []
    for row in logo_rows:
        if clean(row.get("current_source_reviewed")).lower() == "yes":
            selected.append(("logo_wait_for_local_asset_after_source_review", row))
        else:
            selected.append(("logo_source_identity_review", row))
    selected.extend(("athlete_source_only_review", row) for row in athlete_rows)
    rows: list[Dict[str, str]] = []
    for index, (section, row) in enumerate(selected, start=1):
        asset_domain = clean(row.get("asset_domain"))
        local_asset_present = clean(row.get("local_asset_present")) or "no"
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
                "local_asset_needed_later": "no" if local_asset_present.lower() == "yes" else "yes",
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
    lines = [
        "# Hockey/Softball Next Decision Worksheet",
        "",
        f"- Generated: `{generated_at}`",
        f"- Rows: `{len(rows)}`",
        f"- Logo decision rows: `{len(logo_rows)}`",
        f"- Athlete source-only rows: `{len(athlete_rows)}`",
        "- Guardrails: review-only worksheet, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` marker writes, no publish-ready movement, no publishing.",
        "",
        "## How To Use",
        "",
        "1. Open each `source_to_open` manually, then the linked `board_to_open` if context is needed.",
        "2. Use the worksheet CSV for the next human pass; every generated human-decision cell is intentionally blank.",
        "3. For logo rows, Mike may fill the listed source/identity fields after manual source review, but registry action stays hold-only until a local logo asset exists.",
        "4. For athlete rows, Mike may fill source/rights fields after opening the source page, but identity/local-file/approval fields stay blank or held until a named athlete and local candidate asset exist.",
        "5. Do not download assets, write headshots, create `.approved` markers, move files, or publish from this worksheet.",
        "",
        "## Next Decision Rows",
        "",
    ]
    if not rows:
        lines.append("- No next decision rows are available; rerun the workflow readiness generator after source candidates or local assets change.")
    for row in rows:
        lines.extend(
            [
                f"### {row['worksheet_order']} - {row['sport_label']} / {row['asset_domain']} / {row['display_name']}",
                "",
                f"- Section: `{row['worksheet_section']}`",
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
    write_csv(QUARANTINE_DOWNLOAD_INTAKE_CSV, quarantine_download_rows, QUARANTINE_DOWNLOAD_INTAKE_FIELDS)
    write_json(QUARANTINE_DOWNLOAD_INTAKE_JSON, quarantine_download_payload)
    write_text(QUARANTINE_DOWNLOAD_INTAKE_MD, render_quarantine_download_intake(quarantine_download_rows, generated_at))
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, render_report(report))
    print(json.dumps({"status": report["status"], "workflow_rows": totals["workflow_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
