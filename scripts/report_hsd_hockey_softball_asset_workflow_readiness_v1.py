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
    write_csv(ACTION_QUEUE_CSV, action_rows, ACTION_QUEUE_FIELDS)
    write_json(ACTION_QUEUE_JSON, action_payload)
    write_text(ACTION_QUEUE_MD, render_action_queue(action_rows, generated_at))
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, render_report(report))
    print(json.dumps({"status": report["status"], "workflow_rows": totals["workflow_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
