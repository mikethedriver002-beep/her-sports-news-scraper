from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text


VERSION = "hsd-womens-soccer-athlete-verification-queue-v1-review-only"
ROOT = Path("data/asset_registry/womens_soccer")
CONTACT_CSV = ROOT / "womens_soccer_athlete_photo_contact_sheet.csv"
OPERATOR_BOARD_CSV = ROOT / "womens_soccer_athlete_photo_operator_board.csv"
DOWNLOAD_INTAKE_CSV = ROOT / "womens_soccer_athlete_photo_download_intake.csv"
EXTERNAL_RESEARCH_CSV = ROOT / "external_research/womens_soccer_external_research_intake_board.csv"
OUT_MD = output_path(ROOT / "womens_soccer_athlete_verification_queue.md")
OUT_CSV = output_path(ROOT / "womens_soccer_athlete_verification_queue.csv")
OUT_JSON = output_path(ROOT / "womens_soccer_athlete_verification_queue.json")
OUT_NEXT_ACTIONS_MD = output_path(ROOT / "womens_soccer_athlete_verification_next_actions.md")
OUT_NEXT_ACTIONS_CSV = output_path(ROOT / "womens_soccer_athlete_verification_next_actions.csv")
OUT_NEXT_ACTIONS_JSON = output_path(ROOT / "womens_soccer_athlete_verification_next_actions.json")
OUT_SOURCE_PRIORITY_MD = output_path(ROOT / "womens_soccer_athlete_source_priority.md")
OUT_SOURCE_PRIORITY_CSV = output_path(ROOT / "womens_soccer_athlete_source_priority.csv")
OUT_SOURCE_PRIORITY_JSON = output_path(ROOT / "womens_soccer_athlete_source_priority.json")
OUT_REVIEW_TRIAGE_MD = output_path(ROOT / "womens_soccer_athlete_review_triage.md")
OUT_REVIEW_TRIAGE_CSV = output_path(ROOT / "womens_soccer_athlete_review_triage.csv")
OUT_REVIEW_TRIAGE_JSON = output_path(ROOT / "womens_soccer_athlete_review_triage.json")
OUT_CANDIDATE_ACTIONS_MD = output_path(ROOT / "womens_soccer_athlete_candidate_next_action_board.md")
OUT_CANDIDATE_ACTIONS_CSV = output_path(ROOT / "womens_soccer_athlete_candidate_next_action_board.csv")
OUT_CANDIDATE_ACTIONS_JSON = output_path(ROOT / "womens_soccer_athlete_candidate_next_action_board.json")
OUT_PHOTO_READINESS_MD = output_path(ROOT / "womens_soccer_athlete_photo_review_readiness_board.md")
OUT_PHOTO_READINESS_CSV = output_path(ROOT / "womens_soccer_athlete_photo_review_readiness_board.csv")
OUT_PHOTO_READINESS_JSON = output_path(ROOT / "womens_soccer_athlete_photo_review_readiness_board.json")
OUT_OPERATOR_FOCUS_MD = output_path(ROOT / "womens_soccer_athlete_operator_focus.md")
OUT_OPERATOR_FOCUS_CSV = output_path(ROOT / "womens_soccer_athlete_operator_focus.csv")
OUT_OPERATOR_FOCUS_JSON = output_path(ROOT / "womens_soccer_athlete_operator_focus.json")

LEAGUE_ORDER = {
    "nwsl": 10,
    "wsl_england": 20,
    "liga_f_spain": 30,
    "frauen_bundesliga_germany": 40,
    "serie_a_women_italy": 50,
    "arkema_premiere_ligue_france": 60,
}

FIELDS = [
    "queue_rank",
    "queue_bucket",
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "first_action_bucket",
    "candidate_rows",
    "official_roster_candidate_rows",
    "starter_candidate_rows",
    "local_candidate_files_present",
    "missing_local_candidate_rows",
    "download_intake_rows",
    "download_approved_yes_rows",
    "external_research_rows",
    "p0_external_rows",
    "p1_external_rows",
    "gray_area_rows",
    "official_external_rows",
    "non_official_external_rows",
    "operator_verify_required_rows",
    "source_domains",
    "source_status_mix",
    "source_verification_bucket",
    "roster_verification_status",
    "local_asset_blocker",
    "download_law_status",
    "future_download_required_fields",
    "render_readiness",
    "safe_next_action",
    "manual_intake_file",
    "download_intake_file",
    "research_board_file",
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

NEXT_ACTION_FIELDS = [
    "worksheet_rank",
    "queue_rank",
    "first_action_bucket",
    "source_verification_bucket",
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "queue_bucket",
    "p0_external_rows",
    "p1_external_rows",
    "gray_area_rows",
    "official_external_rows",
    "non_official_external_rows",
    "candidate_rows",
    "missing_local_candidate_rows",
    "download_intake_rows",
    "download_approved_yes_rows",
    "download_approved",
    "source_url",
    "candidate_entity_id",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "quarantine_folder",
    "operator_decision",
    "operator_notes",
    "safe_next_action",
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

SOURCE_PRIORITY_FIELDS = [
    "source_priority_rank",
    "source_review_bucket",
    "source_candidate_level",
    "research_lane",
    "scope_id",
    "league_id",
    "league_name",
    "team_id",
    "team_name",
    "player_name",
    "issue_type",
    "operator_action",
    "source_priority",
    "official_status",
    "confidence",
    "operator_verify_required",
    "source_domain",
    "candidate_entity_id",
    "source_candidate_url",
    "linked_queue_bucket",
    "linked_first_action_bucket",
    "linked_missing_local_candidate_rows",
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
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "queue_rank",
    "queue_bucket",
    "first_action_bucket",
    "candidate_rows",
    "missing_local_candidate_rows",
    "source_priority_rows",
    "official_source_candidate_rows",
    "operator_verify_required_source_rows",
    "gray_or_reputable_source_rows",
    "named_player_source_rows",
    "advisory_source_domains",
    "advisory_source_candidate_urls",
    "render_readiness",
    "safe_next_action",
    "download_approved",
    "source_url",
    "candidate_entity_id",
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

CANDIDATE_ACTION_FIELDS = [
    "candidate_action_rank",
    "manual_action_group",
    "source_tier",
    "research_lane",
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "player_name",
    "issue_type",
    "operator_action",
    "source_priority",
    "official_status",
    "confidence",
    "operator_verify_required",
    "source_domain",
    "source_candidate_url",
    "source_priority_row_ref",
    "source_priority_file",
    "triage_row_ref",
    "triage_file",
    "candidate_entity_id",
    "linked_queue_bucket",
    "render_readiness",
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

PHOTO_READINESS_FIELDS = [
    "photo_readiness_rank",
    "photo_review_readiness_bucket",
    "manual_action_group",
    "source_tier",
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "player_name",
    "operator_verify_required",
    "source_domain",
    "source_candidate_url",
    "candidate_action_row_ref",
    "candidate_action_file",
    "source_priority_row_ref",
    "source_priority_file",
    "triage_row_ref",
    "triage_file",
    "candidate_entity_id",
    "linked_queue_bucket",
    "render_readiness",
    "photo_asset_blocker",
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

OPERATOR_FOCUS_FIELDS = [
    "focus_rank",
    "focus_bucket",
    "focus_reason_flags",
    "priority_label",
    "manual_action_group",
    "source_tier",
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "player_name",
    "issue_type",
    "operator_action",
    "source_priority",
    "official_status",
    "confidence",
    "operator_verify_required",
    "source_domain",
    "source_candidate_url",
    "source_priority_row_ref",
    "triage_row_ref",
    "candidate_action_row_ref",
    "open_next_file",
    "open_next_row_ref",
    "why_row_matters",
    "next_manual_action",
    "do_not_do",
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


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any) -> str:
    text = clean(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def as_int(value: Any) -> int:
    try:
        return int(clean(value) or "0")
    except ValueError:
        return 0


def truthy(value: Any) -> bool:
    return clean(value).lower() in {"true", "1", "yes", "y"}


def count_by(rows: Iterable[Mapping[str, str]], field: str) -> Dict[str, int]:
    return dict(sorted(Counter(clean(row.get(field)) or "blank" for row in rows).items()))


def guardrails() -> Dict[str, str]:
    return {
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


def group_by(rows: Iterable[Mapping[str, str]], field: str) -> Dict[str, List[Mapping[str, str]]]:
    grouped: Dict[str, List[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(field))].append(row)
    return grouped


def external_for_nwsl_team(external_rows: List[Mapping[str, str]], team_id: str, team_name: str) -> List[Mapping[str, str]]:
    team_keys = {slug(team_id), slug(team_name)}
    matched: List[Mapping[str, str]] = []
    for row in external_rows:
        if clean(row.get("research_lane")) != "nwsl_correction_enrichment":
            continue
        row_team = clean(row.get("team_name"))
        row_key = slug(row_team)
        if row_key in team_keys or row_key in {f"{slug(team_name)}_fc", f"{slug(team_id)}_fc"}:
            matched.append(row)
    return matched


def external_for_league(external_rows: List[Mapping[str, str]], league_id: str) -> List[Mapping[str, str]]:
    return [
        row
        for row in external_rows
        if clean(row.get("research_lane")) == "europe_official_source_map" and clean(row.get("league_id")) == league_id
    ]


def source_domains(rows: Iterable[Mapping[str, str]]) -> str:
    domains = sorted({clean(row.get("source_domain")) for row in rows if clean(row.get("source_domain"))})
    return "|".join(domains)


def status_mix(rows: Iterable[Mapping[str, str]]) -> str:
    counts = count_by(rows, "official_status")
    return "|".join(f"{key}:{value}" for key, value in counts.items())


def source_bucket(official_rows: int, non_official_rows: int, gray_rows: int, source_domains_value: str) -> str:
    if gray_rows:
        return "gray_area_or_reputable_media_manual_verify"
    if non_official_rows:
        return "non_official_source_manual_verify"
    if official_rows:
        return "official_source_manual_verify"
    if source_domains_value:
        return "source_metadata_manual_verify"
    return "source_missing"


def download_law_status(download_approved_yes_rows: int, missing_local_rows: int) -> str:
    if download_approved_yes_rows:
        return "human_intake_yes_present_still_requires_separate_review_step"
    if missing_local_rows:
        return "future_quarantine_download_intake_required"
    return "download_not_needed_for_current_review_step"


def required_download_fields() -> str:
    return "download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use"


def first_action_for_queue(queue_bucket: str, source_verification_bucket: str, missing_local_rows: int) -> str:
    if queue_bucket == "p0_nwsl_roster_verification_first":
        return "1_roster_verification"
    if "gray_area" in source_verification_bucket or "non_official" in source_verification_bucket:
        return "2_source_verification_gray_or_reputable"
    if missing_local_rows:
        return "3_missing_local_candidate_asset"
    return "4_metadata_watch"


def source_candidate_level(row: Mapping[str, str]) -> str:
    bucket = clean(row.get("operator_bucket"))
    status = clean(row.get("official_status"))
    if "gray_area" in bucket or "gray_area" in status:
        return "gray_area_manual_verify"
    if status.startswith("official"):
        return "official_source_candidate"
    if "media" in status or "database" in status or "non_official" in status:
        return "reputable_or_public_backup_candidate"
    return "source_candidate_manual_review"


def source_review_bucket(row: Mapping[str, str]) -> str:
    lane = clean(row.get("research_lane"))
    bucket = clean(row.get("operator_bucket"))
    verify_required = clean(row.get("operator_verify_required")).lower() == "yes"
    level = source_candidate_level(row)
    if lane == "nwsl_correction_enrichment" and bucket == "p0_nwsl_operator_verify_first":
        return "1_nwsl_p0_roster_source_check"
    if level == "gray_area_manual_verify" or level == "reputable_or_public_backup_candidate":
        return "2_gray_area_or_reputable_manual_verify"
    if verify_required:
        return "3_operator_verify_required_official"
    if level == "official_source_candidate":
        return "4_official_metadata_candidate"
    return "5_metadata_candidate_watch"


def source_safe_next_action(row: Mapping[str, str], review_bucket: str) -> str:
    if review_bucket == "1_nwsl_p0_roster_source_check":
        return "Open the official NWSL/team source page and verify current roster metadata only; no candidate-state writeback."
    if review_bucket == "2_gray_area_or_reputable_manual_verify":
        return "Park as a manual source lead until an official roster/profile page confirms it; do not treat it as official."
    if review_bucket == "3_operator_verify_required_official":
        return "Open the official source page manually and confirm league/team/player identity before future intake."
    if review_bucket == "4_official_metadata_candidate":
        return "Use as source metadata candidate only; Europe rows remain not render-ready."
    return "Keep as source metadata watch; no downloads, approvals, or render readiness."


def source_team_scope(row: Mapping[str, str]) -> str:
    team_name = clean(row.get("team_name"))
    if clean(row.get("research_lane")) == "nwsl_correction_enrichment" and slug(team_name) in {"nwsl_all_teams", "nwsl_all_players"}:
        return "nwsl_league_index"
    return slug(team_name) or slug(row.get("league_id")) or "source_scope"


def join_unique(values: Iterable[str]) -> str:
    seen = []
    for value in values:
        cleaned = clean(value)
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return "; ".join(seen)


def merge_source_priority_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[tuple[str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            clean(row.get("league_id")).lower(),
            clean(row.get("candidate_entity_id")).lower(),
            clean(row.get("source_candidate_url")).lower(),
        )
        grouped[key].append(row)
    merged: List[Dict[str, str]] = []
    bucket_priority = {
        "1_nwsl_p0_roster_source_check": 10,
        "2_gray_area_or_reputable_manual_verify": 20,
        "3_operator_verify_required_official": 30,
        "4_official_metadata_candidate": 40,
        "5_metadata_candidate_watch": 50,
    }
    level_priority = {
        "gray_area_manual_verify": 10,
        "reputable_or_public_backup_candidate": 20,
        "official_source_candidate": 30,
        "source_candidate_manual_review": 40,
    }
    for grouped_rows in grouped.values():
        base = min(grouped_rows, key=lambda row: bucket_priority.get(clean(row.get("source_review_bucket")), 999)).copy()
        base["source_candidate_level"] = clean(
            min(grouped_rows, key=lambda row: level_priority.get(clean(row.get("source_candidate_level")), 999)).get("source_candidate_level")
        )
        verify_values = [clean(row.get("operator_verify_required")).lower() for row in grouped_rows]
        base["operator_verify_required"] = "yes" if "yes" in verify_values else join_unique(verify_values)
        base["team_name"] = join_unique(row.get("team_name", "") for row in grouped_rows)
        base["player_name"] = join_unique(row.get("player_name", "") for row in grouped_rows)
        base["issue_type"] = join_unique(row.get("issue_type", "") for row in grouped_rows)
        base["operator_action"] = join_unique(row.get("operator_action", "") for row in grouped_rows)
        base["source_priority"] = join_unique(row.get("source_priority", "") for row in grouped_rows)
        base["official_status"] = join_unique(row.get("official_status", "") for row in grouped_rows)
        base["confidence"] = join_unique(row.get("confidence", "") for row in grouped_rows)
        base["safe_next_action"] = source_safe_next_action(base, clean(base.get("source_review_bucket")))
        merged.append(base)
    return merged


def build_queue() -> List[Dict[str, str]]:
    contact_rows = read_csv(CONTACT_CSV)
    operator_rows = read_csv(OPERATOR_BOARD_CSV)
    download_rows = read_csv(DOWNLOAD_INTAKE_CSV)
    external_rows = read_csv(EXTERNAL_RESEARCH_CSV)
    contact_by_team = group_by(contact_rows, "team_id")
    download_by_team = group_by(download_rows, "team_id")
    rows: List[Dict[str, str]] = []

    for operator in operator_rows:
        scope_id = clean(operator.get("scope_id"))
        league_id = clean(operator.get("league_id"))
        team_id = clean(operator.get("team_id"))
        team_name = clean(operator.get("team_name"))
        candidate_rows = as_int(operator.get("candidate_rows"))
        official_rows = as_int(operator.get("official_roster_candidate_rows"))
        starter_rows = as_int(operator.get("starter_candidate_rows"))
        local_files = as_int(operator.get("local_candidate_files_present"))
        downloads = download_by_team.get(team_id, [])
        download_yes = sum(1 for row in downloads if clean(row.get("download_approved")).lower() == "yes")
        team_contact_rows = contact_by_team.get(team_id, [])
        missing_local = sum(1 for row in team_contact_rows if not truthy(row.get("local_candidate_exists")))
        matched_external = external_for_nwsl_team(external_rows, team_id, team_name) if scope_id == "nwsl" else []
        p0 = sum(1 for row in matched_external if clean(row.get("operator_bucket")) == "p0_nwsl_operator_verify_first")
        p1 = sum(1 for row in matched_external if clean(row.get("operator_bucket")) == "p1_metadata_candidate_only")
        gray = sum(1 for row in matched_external if "gray_area" in clean(row.get("operator_bucket")))
        official_external = sum(1 for row in matched_external if clean(row.get("official_status")).startswith("official"))
        non_official = len(matched_external) - official_external
        verify_required = sum(1 for row in matched_external if clean(row.get("operator_verify_required")).lower() == "yes")
        if scope_id == "nwsl" and p0:
            bucket = "p0_nwsl_roster_verification_first"
            roster_status = "external_research_p0_requires_manual_roster_check"
            safe_action = "Review current official NWSL/team roster metadata before any later human-edited candidate-state change."
        elif scope_id == "nwsl" and missing_local:
            bucket = "p1_nwsl_local_candidate_assets_missing"
            roster_status = "official_roster_metadata_candidate_present"
            safe_action = "Review source and rights fields, then use human-edited download intake before any quarantine candidate asset."
        else:
            bucket = "p2_nwsl_metadata_watch"
            roster_status = "metadata_review_watch"
            safe_action = "Keep candidate metadata review-only; no asset writeback."
        if scope_id != "nwsl":
            continue
        source_domains_value = source_domains(list(team_contact_rows) + matched_external)
        source_verification_value = source_bucket(official_external, non_official, gray, source_domains_value)
        first_action_value = first_action_for_queue(bucket, source_verification_value, missing_local)
        rows.append(
            {
                "queue_bucket": bucket,
                "scope_id": scope_id,
                "league_id": league_id,
                "team_id": team_id,
                "team_name": team_name,
                "first_action_bucket": first_action_value,
                "candidate_rows": str(candidate_rows),
                "official_roster_candidate_rows": str(official_rows),
                "starter_candidate_rows": str(starter_rows),
                "local_candidate_files_present": str(local_files),
                "missing_local_candidate_rows": str(missing_local),
                "download_intake_rows": str(len(downloads)),
                "download_approved_yes_rows": str(download_yes),
                "external_research_rows": str(len(matched_external)),
                "p0_external_rows": str(p0),
                "p1_external_rows": str(p1),
                "gray_area_rows": str(gray),
                "official_external_rows": str(official_external),
                "non_official_external_rows": str(non_official),
                "operator_verify_required_rows": str(verify_required),
                "source_domains": source_domains_value,
                "source_status_mix": status_mix(matched_external),
                "source_verification_bucket": source_verification_value,
                "roster_verification_status": roster_status,
                "local_asset_blocker": "local_candidate_assets_missing" if missing_local else "none",
                "download_law_status": download_law_status(download_yes, missing_local),
                "future_download_required_fields": required_download_fields(),
                "render_readiness": "not_render_ready_review_only",
                "safe_next_action": safe_action,
                "manual_intake_file": clean(operator.get("manual_intake_file")) or "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": clean(operator.get("download_intake_file")) or "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
                "research_board_file": EXTERNAL_RESEARCH_CSV.as_posix(),
                **guardrails(),
            }
        )

    operator_by_league = group_by([row for row in operator_rows if clean(row.get("scope_id")) == "europe_top_flight"], "league_id")
    for league_id in sorted(operator_by_league, key=lambda value: LEAGUE_ORDER.get(value, 999)):
        league_rows = operator_by_league[league_id]
        contact_league_rows = [row for row in contact_rows if clean(row.get("league_id")) == league_id]
        download_league_rows = [row for row in download_rows if clean(row.get("league_id")) == league_id]
        matched_external = external_for_league(external_rows, league_id)
        candidate_rows = sum(as_int(row.get("candidate_rows")) for row in league_rows)
        starter_rows = sum(as_int(row.get("starter_candidate_rows")) for row in league_rows)
        local_files = sum(as_int(row.get("local_candidate_files_present")) for row in league_rows)
        missing_local = sum(1 for row in contact_league_rows if not truthy(row.get("local_candidate_exists")))
        official_external = sum(1 for row in matched_external if clean(row.get("official_status")).startswith("official"))
        non_official = len(matched_external) - official_external
        gray = sum(1 for row in matched_external if "gray_area" in clean(row.get("operator_bucket")))
        verify_required = sum(1 for row in matched_external if clean(row.get("operator_verify_required")).lower() == "yes")
        no_verify = sum(1 for row in matched_external if clean(row.get("operator_bucket")) == "europe_official_no_verify_metadata_candidate")
        if gray:
            bucket = "p1_europe_gray_area_source_review"
            safe_action = "Park gray-area/non-official leads; verify official source pages before any player-level intake."
        elif verify_required:
            bucket = "p1_europe_operator_source_verify"
            safe_action = "Open the official league/team source pages manually before adding player-level candidates."
        else:
            bucket = "p2_europe_official_source_map_ready"
            safe_action = "Use as official source-map metadata for future player research only; not render-ready."
        source_domains_value = source_domains(contact_league_rows + matched_external)
        source_verification_value = source_bucket(official_external, non_official, gray, source_domains_value)
        missing_download_yes = sum(1 for row in download_league_rows if clean(row.get("download_approved")).lower() == "yes")
        rows.append(
            {
                "queue_bucket": bucket,
                "scope_id": "europe_top_flight",
                "league_id": league_id,
                "team_id": "all_teams",
                "team_name": league_id.replace("_", " ").title(),
                "first_action_bucket": first_action_for_queue(bucket, source_verification_value, missing_local),
                "candidate_rows": str(candidate_rows),
                "official_roster_candidate_rows": "0",
                "starter_candidate_rows": str(starter_rows),
                "local_candidate_files_present": str(local_files),
                "missing_local_candidate_rows": str(missing_local),
                "download_intake_rows": str(len(download_league_rows)),
                "download_approved_yes_rows": str(missing_download_yes),
                "external_research_rows": str(len(matched_external)),
                "p0_external_rows": "0",
                "p1_external_rows": str(no_verify + verify_required),
                "gray_area_rows": str(gray),
                "official_external_rows": str(official_external),
                "non_official_external_rows": str(non_official),
                "operator_verify_required_rows": str(verify_required),
                "source_domains": source_domains_value,
                "source_status_mix": status_mix(matched_external),
                "source_verification_bucket": source_verification_value,
                "roster_verification_status": "europe_source_map_review_required",
                "local_asset_blocker": "starter_placeholders_missing_local_assets" if missing_local else "none",
                "download_law_status": download_law_status(missing_download_yes, missing_local),
                "future_download_required_fields": required_download_fields(),
                "render_readiness": "not_render_ready_source_candidate_only",
                "safe_next_action": safe_action,
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
                "research_board_file": EXTERNAL_RESEARCH_CSV.as_posix(),
                **guardrails(),
            }
        )

    priority = {
        "p0_nwsl_roster_verification_first": 10,
        "p1_nwsl_local_candidate_assets_missing": 20,
        "p1_europe_gray_area_source_review": 30,
        "p1_europe_operator_source_verify": 40,
        "p2_europe_official_source_map_ready": 50,
        "p2_nwsl_metadata_watch": 60,
    }
    rows.sort(key=lambda row: (priority.get(row["queue_bucket"], 999), LEAGUE_ORDER.get(row["league_id"], 999), row["team_name"]))
    for index, row in enumerate(rows, start=1):
        row["queue_rank"] = str(index)
    return rows


def render_markdown(rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "queue_bucket")
    lines = [
        "# Women's Soccer Athlete Verification Queue",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only operator queue built from existing women's soccer athlete candidate rows, download-intake rows, and external research intake rows. It does not download images, approve assets, write `headshot.png`, create `.approved` markers, change current candidate state, move files into publish-ready lanes, publish, or use paid APIs.",
        "",
        "## Summary",
        "",
        f"- Queue rows: `{len(rows)}`",
        f"- NWSL team rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'nwsl')}`",
        f"- Europe league rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'europe_top_flight')}`",
        f"- P0 NWSL roster-verification rows: `{sum(1 for row in rows if clean(row.get('queue_bucket')) == 'p0_nwsl_roster_verification_first')}`",
        f"- Gray-area source rows: `{sum(as_int(row.get('gray_area_rows')) for row in rows)}`",
        f"- Missing local candidate asset rows: `{sum(as_int(row.get('missing_local_candidate_rows')) for row in rows)}`",
        f"- Download-approved yes rows: `{sum(as_int(row.get('download_approved_yes_rows')) for row in rows)}`",
        "",
        "## Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## Safe Operator Path",
        "",
        "- Work NWSL P0 roster-verification rows first.",
        "- Treat Europe rows as source-map candidates only; they are not render-ready.",
        "- Keep all download intake rows at `download_approved=no` unless a human edits the intake with the required quarantine fields.",
        "- Sam Kerr/Reuters and other gray-area leads remain parked for manual verification only.",
        "",
        "## Top Queue Rows",
        "",
        "| Rank | Bucket | Scope | League | Team | Candidates | External | Missing Local | Safe Next Action |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:25]:
        lines.append(
            "| {rank} | {bucket} | {scope} | {league} | {team} | {candidates} | {external} | {missing} | {action} |".format(
                rank=clean(row.get("queue_rank")),
                bucket=clean(row.get("queue_bucket")),
                scope=clean(row.get("scope_id")),
                league=clean(row.get("league_id")),
                team=clean(row.get("team_name")).replace("|", "/"),
                candidates=clean(row.get("candidate_rows")),
                external=clean(row.get("external_research_rows")),
                missing=clean(row.get("missing_local_candidate_rows")),
                action=clean(row.get("safe_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def next_action_rows(queue_rows: List[Mapping[str, str]], download_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    downloads_by_team = group_by(download_rows, "team_id")
    nwsl_rows = [row for row in queue_rows if clean(row.get("scope_id")) == "nwsl"]
    output: List[Dict[str, str]] = []
    for index, row in enumerate(nwsl_rows, start=1):
        team_downloads = downloads_by_team.get(clean(row.get("team_id")), [])
        quarantine_folder = clean(team_downloads[0].get("quarantine_folder")) if team_downloads else "data/assets/quarantine/review_only_candidates"
        output.append(
            {
                "worksheet_rank": str(index),
                "queue_rank": clean(row.get("queue_rank")),
                "first_action_bucket": clean(row.get("first_action_bucket")),
                "source_verification_bucket": clean(row.get("source_verification_bucket")),
                "scope_id": clean(row.get("scope_id")),
                "league_id": clean(row.get("league_id")),
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "queue_bucket": clean(row.get("queue_bucket")),
                "p0_external_rows": clean(row.get("p0_external_rows")),
                "p1_external_rows": clean(row.get("p1_external_rows")),
                "gray_area_rows": clean(row.get("gray_area_rows")),
                "official_external_rows": clean(row.get("official_external_rows")),
                "non_official_external_rows": clean(row.get("non_official_external_rows")),
                "candidate_rows": clean(row.get("candidate_rows")),
                "missing_local_candidate_rows": clean(row.get("missing_local_candidate_rows")),
                "download_intake_rows": clean(row.get("download_intake_rows")),
                "download_approved_yes_rows": clean(row.get("download_approved_yes_rows")),
                "download_approved": "no",
                "source_url": "",
                "candidate_entity_id": clean(row.get("team_id")),
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "quarantine_folder": quarantine_folder,
                "operator_decision": "",
                "operator_notes": "",
                "safe_next_action": clean(row.get("safe_next_action")),
                **guardrails(),
            }
        )
    return output


def render_next_actions(rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "first_action_bucket")
    lines = [
        "# Women's Soccer Athlete Verification Next Actions",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only NWSL-first worksheet for turning the verification queue into manual operator steps. Generated human-decision fields stay blank or `download_approved=no`; this artifact does not download, approve, publish, write headshots, create markers, or change candidate state.",
        "",
        "## Summary",
        "",
        f"- Worksheet rows: `{len(rows)}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Missing local candidate asset rows represented: `{sum(as_int(row.get('missing_local_candidate_rows')) for row in rows)}`",
        "",
        "## First Action Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## Local-Download Law Fields",
        "",
        "- Required future fields are present: `download_approved`, `source_url`, `entity_id`, `rights_class`, `identity_confidence`, `intended_review_only_use`.",
        "- Generated rows default to `download_approved=no` and leave human decision fields blank.",
        "- A separate human-edited intake and review step is still required before any quarantine-only download.",
        "",
        "## Worksheet Preview",
        "",
        "| Rank | Team | First Action | Source Check | Candidates | Missing Local | Download Approved | Safe Next Action |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows[:25]:
        lines.append(
            "| {rank} | {team} | {first_action} | {source_check} | {candidates} | {missing} | {download_approved} | {action} |".format(
                rank=clean(row.get("worksheet_rank")),
                team=clean(row.get("team_name")).replace("|", "/"),
                first_action=clean(row.get("first_action_bucket")),
                source_check=clean(row.get("source_verification_bucket")),
                candidates=clean(row.get("candidate_rows")),
                missing=clean(row.get("missing_local_candidate_rows")),
                download_approved=clean(row.get("download_approved")),
                action=clean(row.get("safe_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def source_priority_rows(queue_rows: List[Mapping[str, str]], external_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    queue_by_team = {clean(row.get("team_id")): row for row in queue_rows if clean(row.get("scope_id")) == "nwsl"}
    queue_by_league = {
        clean(row.get("league_id")): row
        for row in queue_rows
        if clean(row.get("scope_id")) == "europe_top_flight" and clean(row.get("team_id")) == "all_teams"
    }
    output: List[Dict[str, str]] = []
    for row in external_rows:
        lane = clean(row.get("research_lane"))
        league_id = clean(row.get("league_id"))
        team_name = clean(row.get("team_name"))
        scope_id = "nwsl" if lane == "nwsl_correction_enrichment" else "europe_top_flight"
        matched_queue: Mapping[str, str] = {}
        team_id = ""
        if scope_id == "nwsl":
            team_slug = slug(team_name)
            for candidate_team_id, queue_row in queue_by_team.items():
                queue_team_slug = slug(queue_row.get("team_name"))
                if team_slug in {slug(candidate_team_id), queue_team_slug, f"{queue_team_slug}_fc"}:
                    team_id = candidate_team_id
                    matched_queue = queue_row
                    break
            if not team_id:
                team_id = team_slug or "nwsl_source_scope"
        else:
            matched_queue = queue_by_league.get(league_id, {})
            team_id = slug(team_name) or "league_source_scope"
        review_bucket = source_review_bucket(row)
        output.append(
            {
                "source_priority_rank": "0",
                "source_review_bucket": review_bucket,
                "source_candidate_level": source_candidate_level(row),
                "research_lane": lane,
                "scope_id": scope_id,
                "league_id": league_id,
                "league_name": clean(row.get("league_name")),
                "team_id": team_id,
                "team_name": team_name,
                "player_name": clean(row.get("player_name")),
                "issue_type": clean(row.get("issue_type")),
                "operator_action": clean(row.get("operator_action")),
                "source_priority": clean(row.get("source_priority")),
                "official_status": clean(row.get("official_status")),
                "confidence": clean(row.get("confidence")),
                "operator_verify_required": clean(row.get("operator_verify_required")),
                "source_domain": clean(row.get("source_domain")),
                "candidate_entity_id": source_team_scope(row),
                "source_candidate_url": clean(row.get("source_url")),
                "linked_queue_bucket": clean(matched_queue.get("queue_bucket")),
                "linked_first_action_bucket": clean(matched_queue.get("first_action_bucket")),
                "linked_missing_local_candidate_rows": clean(matched_queue.get("missing_local_candidate_rows")),
                "render_readiness": "not_render_ready_source_candidate_only" if scope_id == "europe_top_flight" else "not_render_ready_review_only",
                "safe_next_action": source_safe_next_action(row, review_bucket),
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                **guardrails(),
            }
        )
    output = merge_source_priority_rows(output)
    priority = {
        "1_nwsl_p0_roster_source_check": 10,
        "2_gray_area_or_reputable_manual_verify": 20,
        "3_operator_verify_required_official": 30,
        "4_official_metadata_candidate": 40,
        "5_metadata_candidate_watch": 50,
    }
    output.sort(
        key=lambda row: (
            priority.get(row["source_review_bucket"], 999),
            LEAGUE_ORDER.get(row["league_id"], 999),
            clean(row.get("team_name")),
            clean(row.get("player_name")),
            clean(row.get("issue_type")),
        )
    )
    for index, row in enumerate(output, start=1):
        row["source_priority_rank"] = str(index)
    return output


def render_source_priority(rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "source_review_bucket")
    lines = [
        "# Women's Soccer Athlete Source Priority",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only source-candidate worksheet built from imported external research intake rows. It keeps source candidates separate from future download intake: `source_candidate_url` is advisory metadata, while the download-law `source_url` field remains blank and `download_approved=no` unless a human edits intake later.",
        "",
        "## Summary",
        "",
        f"- Source priority rows: `{len(rows)}`",
        f"- NWSL source rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'nwsl')}`",
        f"- Europe source rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'europe_top_flight')}`",
        f"- Operator-verify rows: `{sum(1 for row in rows if clean(row.get('operator_verify_required')).lower() == 'yes')}`",
        f"- Gray/reputable manual-verify rows: `{sum(1 for row in rows if clean(row.get('source_review_bucket')) == '2_gray_area_or_reputable_manual_verify')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        "",
        "## Source Review Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## Safe Operator Path",
        "",
        "- Work NWSL P0 roster/source checks first.",
        "- Treat gray-area and reputable-media/database rows as manual source leads only until official confirmation exists.",
        "- Keep Europe rows source-candidate-only and explicitly not render-ready.",
        "- Do not copy `source_candidate_url` into download-law `source_url` without a later human-edited intake row.",
        "",
        "## Worksheet Preview",
        "",
        "| Rank | Bucket | Scope | League | Team | Player | Source | Candidate URL | Safe Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:35]:
        lines.append(
            "| {rank} | {bucket} | {scope} | {league} | {team} | {player} | {domain} | {url} | {action} |".format(
                rank=clean(row.get("source_priority_rank")),
                bucket=clean(row.get("source_review_bucket")),
                scope=clean(row.get("scope_id")),
                league=clean(row.get("league_id")),
                team=clean(row.get("team_name")).replace("|", "/"),
                player=clean(row.get("player_name")).replace("|", "/"),
                domain=clean(row.get("source_domain")).replace("|", "/"),
                url=clean(row.get("source_candidate_url")).replace("|", "%7C"),
                action=clean(row.get("safe_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def source_rows_for_queue(row: Mapping[str, str], source_rows: List[Mapping[str, str]]) -> List[Mapping[str, str]]:
    scope_id = clean(row.get("scope_id"))
    league_id = clean(row.get("league_id"))
    team_id = clean(row.get("team_id"))
    if scope_id == "nwsl":
        return [
            source
            for source in source_rows
            if clean(source.get("scope_id")) == "nwsl"
            and (
                clean(source.get("team_id")) == team_id
                or clean(source.get("candidate_entity_id")) == team_id
            )
        ]
    return [
        source
        for source in source_rows
        if clean(source.get("scope_id")) == "europe_top_flight" and clean(source.get("league_id")) == league_id
    ]


def preview_values(rows: Iterable[Mapping[str, str]], field: str, limit: int = 5) -> str:
    values = []
    for row in rows:
        value = clean(row.get(field))
        if value and value not in values:
            values.append(value)
        if len(values) >= limit:
            break
    return " | ".join(values)


def triage_action_flags(row: Mapping[str, str], matched_sources: List[Mapping[str, str]]) -> List[str]:
    flags: List[str] = []
    if clean(row.get("queue_bucket")) == "p0_nwsl_roster_verification_first":
        flags.append("official_roster_check")
    if any(clean(source.get("player_name")) for source in matched_sources):
        flags.append("identity_verification")
    if any(clean(source.get("operator_verify_required")).lower() == "yes" for source in matched_sources):
        flags.append("source_candidate_review")
    if any(clean(source.get("source_review_bucket")) == "2_gray_area_or_reputable_manual_verify" for source in matched_sources) or as_int(row.get("gray_area_rows")):
        flags.append("gray_area_reputable_lead_review")
    if as_int(row.get("missing_local_candidate_rows")):
        flags.append("missing_local_asset")
        flags.append("future_quarantine_download_intake_prep")
    if not flags:
        flags.append("source_metadata_watch")
    return flags


def primary_manual_action(flags: List[str]) -> str:
    priority = [
        "official_roster_check",
        "gray_area_reputable_lead_review",
        "identity_verification",
        "source_candidate_review",
        "missing_local_asset",
        "future_quarantine_download_intake_prep",
        "source_metadata_watch",
    ]
    for flag in priority:
        if flag in flags:
            return flag
    return flags[0]


def triage_safe_next_action(primary: str, scope_id: str) -> str:
    if primary == "official_roster_check":
        return "Open official NWSL/team roster sources and verify current roster metadata only; no candidate-state writeback."
    if primary == "gray_area_reputable_lead_review":
        return "Review gray-area or reputable public leads as manual leads only; require official confirmation before current-roster use."
    if primary == "identity_verification":
        return "Verify named player identity against official source metadata before any future intake or asset work."
    if primary == "source_candidate_review":
        return "Open advisory source-candidate pages manually and classify source quality; keep Europe source-candidate-only."
    if primary == "missing_local_asset":
        return "Confirm missing local review assets and prepare human-edited quarantine intake only if a later download is approved."
    if primary == "future_quarantine_download_intake_prep":
        return "Prepare future human intake fields only; generated rows do not authorize downloads."
    if scope_id == "europe_top_flight":
        return "Keep Europe source-map rows as metadata candidates only; not render-ready."
    return "Keep as review-only metadata watch; no downloads, approvals, or publishing."


def review_triage_rows(queue_rows: List[Mapping[str, str]], source_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for row in queue_rows:
        matched_sources = source_rows_for_queue(row, source_rows)
        flags = triage_action_flags(row, matched_sources)
        primary = primary_manual_action(flags)
        official_sources = [
            source
            for source in matched_sources
            if clean(source.get("source_candidate_level")) == "official_source_candidate"
            or clean(source.get("official_status")).startswith("official")
        ]
        gray_sources = [
            source
            for source in matched_sources
            if clean(source.get("source_review_bucket")) == "2_gray_area_or_reputable_manual_verify"
        ]
        entity_id = clean(row.get("team_id")) if clean(row.get("team_id")) != "all_teams" else clean(row.get("league_id"))
        output.append(
            {
                "triage_rank": "0",
                "primary_manual_action": primary,
                "action_flags": "|".join(flags),
                "scope_id": clean(row.get("scope_id")),
                "league_id": clean(row.get("league_id")),
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "queue_rank": clean(row.get("queue_rank")),
                "queue_bucket": clean(row.get("queue_bucket")),
                "first_action_bucket": clean(row.get("first_action_bucket")),
                "candidate_rows": clean(row.get("candidate_rows")),
                "missing_local_candidate_rows": clean(row.get("missing_local_candidate_rows")),
                "source_priority_rows": str(len(matched_sources)),
                "official_source_candidate_rows": str(len(official_sources)),
                "operator_verify_required_source_rows": str(sum(1 for source in matched_sources if clean(source.get("operator_verify_required")).lower() == "yes")),
                "gray_or_reputable_source_rows": str(len(gray_sources)),
                "named_player_source_rows": str(sum(1 for source in matched_sources if clean(source.get("player_name")))),
                "advisory_source_domains": preview_values(matched_sources, "source_domain"),
                "advisory_source_candidate_urls": preview_values(matched_sources, "source_candidate_url", limit=3),
                "render_readiness": clean(row.get("render_readiness")),
                "safe_next_action": triage_safe_next_action(primary, clean(row.get("scope_id"))),
                "download_approved": "no",
                "source_url": "",
                "candidate_entity_id": entity_id,
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                **guardrails(),
            }
        )
    priority = {
        "official_roster_check": 10,
        "gray_area_reputable_lead_review": 20,
        "identity_verification": 30,
        "source_candidate_review": 40,
        "missing_local_asset": 50,
        "future_quarantine_download_intake_prep": 60,
        "source_metadata_watch": 70,
    }
    output.sort(
        key=lambda row: (
            priority.get(row["primary_manual_action"], 999),
            LEAGUE_ORDER.get(row["league_id"], 999),
            as_int(row.get("queue_rank")),
            clean(row.get("team_name")),
        )
    )
    for index, row in enumerate(output, start=1):
        row["triage_rank"] = str(index)
    return output


def render_review_triage(rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "primary_manual_action")
    lines = [
        "# Women's Soccer Athlete Review Triage",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only operator triage worksheet built from the verification queue and source-priority rows. Advisory source candidates remain in `advisory_source_candidate_urls`; generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "",
        "## Summary",
        "",
        f"- Triage rows: `{len(rows)}`",
        f"- NWSL rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'nwsl')}`",
        f"- Europe rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'europe_top_flight')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Primary Manual Actions",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## Safe Operator Path",
        "",
        "- Work official NWSL roster checks first.",
        "- Treat gray-area and reputable public leads as manual review leads only, never as official/current roster confirmation.",
        "- Keep Europe rows source-candidate-only and not render-ready unless a later human intake and local assets support them.",
        "- Do not copy advisory source candidates into download-law `source_url` without a later human-edited intake row.",
        "",
        "## Worksheet Preview",
        "",
        "| Rank | Action | Scope | League | Team | Sources | Named Players | Missing Local | Safe Next Action |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows[:35]:
        lines.append(
            "| {rank} | {action} | {scope} | {league} | {team} | {sources} | {players} | {missing} | {safe_action} |".format(
                rank=clean(row.get("triage_rank")),
                action=clean(row.get("primary_manual_action")),
                scope=clean(row.get("scope_id")),
                league=clean(row.get("league_id")),
                team=clean(row.get("team_name")).replace("|", "/"),
                sources=clean(row.get("source_priority_rows")),
                players=clean(row.get("named_player_source_rows")),
                missing=clean(row.get("missing_local_candidate_rows")),
                safe_action=clean(row.get("safe_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def candidate_source_tier(row: Mapping[str, str]) -> str:
    level = clean(row.get("source_candidate_level"))
    status = clean(row.get("official_status"))
    if level == "gray_area_manual_verify" or "gray_area" in status:
        return "gray_area_public_lead"
    if level == "reputable_or_public_backup_candidate" or "media" in status or "database" in status:
        return "reputable_public_backup"
    if status.startswith("official"):
        return "official_source_candidate"
    return "source_candidate_manual_review"


def candidate_manual_action_group(row: Mapping[str, str]) -> str:
    issue = clean(row.get("issue_type")).lower()
    bucket = clean(row.get("source_review_bucket"))
    if any(token in issue for token in ["duplicate", "transfer", "loan", "stale_team_assignment", "stale_player", "expired", "short_term"]):
        return "duplicate_transfer_check"
    if bucket == "2_gray_area_or_reputable_manual_verify":
        return "gray_area_reputable_media_lead"
    if any(token in issue for token in ["missing_player_profile", "player_profile_candidate_gap", "source_domain_change", "source_url_enrichment"]):
        return "official_page_missing_or_season_rollover_verify"
    if clean(row.get("operator_verify_required")).lower() == "yes" or bucket in {"1_nwsl_p0_roster_source_check", "3_operator_verify_required_official"}:
        return "roster_source_verify"
    if as_int(row.get("linked_missing_local_candidate_rows")):
        return "future_quarantine_download_intake_prep"
    return "source_candidate_review"


def candidate_next_manual_action(row: Mapping[str, str], group: str) -> str:
    if group == "duplicate_transfer_check":
        return "Compare official roster/transaction pages and reconcile duplicate, transfer, loan, stale, or short-term player metadata only."
    if group == "gray_area_reputable_media_lead":
        return "Park as review-only lead until an official team/league page confirms current roster or player identity."
    if group == "official_page_missing_or_season_rollover_verify":
        return "Open the official source page and verify whether roster/profile URL patterns changed before adding future intake."
    if group == "roster_source_verify":
        return "Open the official or advisory roster source manually and verify source quality before any future candidate-state writeback."
    if group == "future_quarantine_download_intake_prep":
        return "Prepare future human intake only; generated fields do not authorize quarantine download or asset approval."
    return "Review source metadata only; no download, approval, or render-ready action."


def candidate_action_rows(source_rows: List[Mapping[str, str]], triage_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    triage_by_key = {
        (clean(row.get("scope_id")), clean(row.get("league_id")), clean(row.get("team_id"))): row
        for row in triage_rows
    }
    output: List[Dict[str, str]] = []
    for source in source_rows:
        group = candidate_manual_action_group(source)
        triage = triage_by_key.get((clean(source.get("scope_id")), clean(source.get("league_id")), clean(source.get("team_id"))), {})
        if not triage and clean(source.get("scope_id")) == "europe_top_flight":
            triage = triage_by_key.get(("europe_top_flight", clean(source.get("league_id")), "all_teams"), {})
        output.append(
            {
                "candidate_action_rank": "0",
                "manual_action_group": group,
                "source_tier": candidate_source_tier(source),
                "research_lane": clean(source.get("research_lane")),
                "scope_id": clean(source.get("scope_id")),
                "league_id": clean(source.get("league_id")),
                "team_id": clean(source.get("team_id")),
                "team_name": clean(source.get("team_name")),
                "player_name": clean(source.get("player_name")),
                "issue_type": clean(source.get("issue_type")),
                "operator_action": clean(source.get("operator_action")),
                "source_priority": clean(source.get("source_priority")),
                "official_status": clean(source.get("official_status")),
                "confidence": clean(source.get("confidence")),
                "operator_verify_required": clean(source.get("operator_verify_required")),
                "source_domain": clean(source.get("source_domain")),
                "source_candidate_url": clean(source.get("source_candidate_url")),
                "source_priority_row_ref": f"{OUT_SOURCE_PRIORITY_CSV.as_posix()}#row={clean(source.get('source_priority_rank'))}",
                "source_priority_file": OUT_SOURCE_PRIORITY_CSV.as_posix(),
                "triage_row_ref": f"{OUT_REVIEW_TRIAGE_CSV.as_posix()}#row={clean(triage.get('triage_rank'))}" if clean(triage.get("triage_rank")) else "",
                "triage_file": OUT_REVIEW_TRIAGE_CSV.as_posix(),
                "candidate_entity_id": clean(source.get("candidate_entity_id")),
                "linked_queue_bucket": clean(source.get("linked_queue_bucket")),
                "render_readiness": clean(source.get("render_readiness")),
                "next_manual_action": candidate_next_manual_action(source, group),
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                **guardrails(),
            }
        )
    priority = {
        "roster_source_verify": 10,
        "gray_area_reputable_media_lead": 20,
        "official_page_missing_or_season_rollover_verify": 30,
        "duplicate_transfer_check": 40,
        "future_quarantine_download_intake_prep": 50,
        "source_candidate_review": 60,
    }
    output.sort(
        key=lambda row: (
            priority.get(row["manual_action_group"], 999),
            LEAGUE_ORDER.get(row["league_id"], 999),
            clean(row.get("team_name")),
            clean(row.get("player_name")),
            clean(row.get("source_candidate_url")),
        )
    )
    for index, row in enumerate(output, start=1):
        row["candidate_action_rank"] = str(index)
    return output


def render_candidate_actions(rows: List[Mapping[str, str]], generated_at: str) -> str:
    group_counts = count_by(rows, "manual_action_group")
    lines = [
        "# Women's Soccer Athlete Candidate Next-Action Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only board for turning source-priority rows into safe manual work. Advisory `source_candidate_url` values stay separate from generated local-download-law fields, which remain `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "`source_candidate_url` remains advisory metadata for operator review only; it is not a download approval or current-roster confirmation.",
        "",
        "## Summary",
        "",
        f"- Candidate action rows: `{len(rows)}`",
        f"- NWSL rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'nwsl')}`",
        f"- Europe rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'europe_top_flight')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Manual Action Groups",
        "",
    ]
    lines.extend(f"- {group}: `{count}`" for group, count in group_counts.items())
    lines += [
        "",
        "## Safe Operator Path",
        "",
        "- Treat non-official reputable and gray-area public sources as review leads only.",
        "- Use official team/league confirmation before any current-roster or candidate-state decision.",
        "- Keep all download-law fields blank/no unless a later human-edited intake explicitly authorizes quarantine review.",
        "",
        "## Board Preview",
        "",
        "| Rank | Action Group | Tier | League | Team | Player | Source | Source Row | Next Manual Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:40]:
        lines.append(
            "| {rank} | {group} | {tier} | {league} | {team} | {player} | {domain} | {source_ref} | {action} |".format(
                rank=clean(row.get("candidate_action_rank")),
                group=clean(row.get("manual_action_group")),
                tier=clean(row.get("source_tier")),
                league=clean(row.get("league_id")),
                team=clean(row.get("team_name")).replace("|", "/"),
                player=clean(row.get("player_name")).replace("|", "/"),
                domain=clean(row.get("source_domain")).replace("|", "/"),
                source_ref=clean(row.get("source_priority_row_ref")).replace("|", "%7C"),
                action=clean(row.get("next_manual_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def photo_readiness_bucket(row: Mapping[str, str]) -> str:
    group = clean(row.get("manual_action_group"))
    if group == "gray_area_reputable_media_lead":
        return "park_gray_area_lead_no_photo_use"
    if group == "duplicate_transfer_check":
        return "resolve_duplicate_transfer_before_photo_review"
    if group == "official_page_missing_or_season_rollover_verify":
        return "verify_official_page_before_photo_review"
    if group == "future_quarantine_download_intake_prep":
        return "future_quarantine_download_intake_prep"
    if group == "roster_source_verify" and clean(row.get("scope_id")) == "nwsl":
        return "nwsl_roster_verify_before_photo_review"
    if clean(row.get("scope_id")) == "europe_top_flight":
        return "europe_source_candidate_not_render_ready"
    return "source_candidate_review_before_photo_review"


def photo_asset_blocker(row: Mapping[str, str]) -> str:
    if clean(row.get("render_readiness")) == "not_render_ready_source_candidate_only":
        return "missing_local_candidate_or_human_intake_required"
    return clean(row.get("render_readiness")) or "manual_review_required"


def photo_readiness_next_action(row: Mapping[str, str], bucket: str) -> str:
    if bucket == "park_gray_area_lead_no_photo_use":
        return "Keep as research-only lead; require official roster or identity confirmation before any photo-review intake."
    if bucket == "resolve_duplicate_transfer_before_photo_review":
        return "Resolve duplicate, transfer, loan, stale, or short-term status against official sources before photo review."
    if bucket == "verify_official_page_before_photo_review":
        return "Verify the official roster/profile page or season-rollover URL before preparing manual photo-review intake."
    if bucket == "future_quarantine_download_intake_prep":
        return "Prepare future human-edited quarantine-download intake only; generated row does not authorize any download."
    if bucket == "nwsl_roster_verify_before_photo_review":
        return "Open official NWSL/team source, verify player/team identity, then create human photo-review intake if needed."
    if bucket == "europe_source_candidate_not_render_ready":
        return "Keep Europe row source-candidate-only until roster/source verification and local candidate intake are complete."
    return "Review source metadata and identity only; do not download, approve, or treat as render-ready."


def photo_readiness_rows(candidate_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for row in candidate_rows:
        bucket = photo_readiness_bucket(row)
        output.append(
            {
                "photo_readiness_rank": "0",
                "photo_review_readiness_bucket": bucket,
                "manual_action_group": clean(row.get("manual_action_group")),
                "source_tier": clean(row.get("source_tier")),
                "scope_id": clean(row.get("scope_id")),
                "league_id": clean(row.get("league_id")),
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "player_name": clean(row.get("player_name")),
                "operator_verify_required": clean(row.get("operator_verify_required")),
                "source_domain": clean(row.get("source_domain")),
                "source_candidate_url": clean(row.get("source_candidate_url")),
                "candidate_action_row_ref": f"{OUT_CANDIDATE_ACTIONS_CSV.as_posix()}#row={clean(row.get('candidate_action_rank'))}",
                "candidate_action_file": OUT_CANDIDATE_ACTIONS_CSV.as_posix(),
                "source_priority_row_ref": clean(row.get("source_priority_row_ref")),
                "source_priority_file": clean(row.get("source_priority_file")),
                "triage_row_ref": clean(row.get("triage_row_ref")),
                "triage_file": clean(row.get("triage_file")),
                "candidate_entity_id": clean(row.get("candidate_entity_id")),
                "linked_queue_bucket": clean(row.get("linked_queue_bucket")),
                "render_readiness": clean(row.get("render_readiness")),
                "photo_asset_blocker": photo_asset_blocker(row),
                "future_download_intake_status": "human_edited_intake_required_no_generated_authorization",
                "next_manual_action": photo_readiness_next_action(row, bucket),
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                **guardrails(),
            }
        )
    priority = {
        "nwsl_roster_verify_before_photo_review": 10,
        "resolve_duplicate_transfer_before_photo_review": 20,
        "verify_official_page_before_photo_review": 30,
        "park_gray_area_lead_no_photo_use": 40,
        "future_quarantine_download_intake_prep": 50,
        "europe_source_candidate_not_render_ready": 60,
        "source_candidate_review_before_photo_review": 70,
    }
    output.sort(
        key=lambda item: (
            priority.get(item["photo_review_readiness_bucket"], 999),
            LEAGUE_ORDER.get(item["league_id"], 999),
            clean(item.get("team_name")),
            clean(item.get("player_name")),
            clean(item.get("source_candidate_url")),
        )
    )
    for index, row in enumerate(output, start=1):
        row["photo_readiness_rank"] = str(index)
    return output


def render_photo_readiness(rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "photo_review_readiness_bucket")
    lines = [
        "# Women's Soccer Athlete Photo Review Readiness Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only board for deciding what must happen before a source-candidate row can become manual photo-review work. It does not download images, approve assets, write headshots, create `.approved` markers, move files, or publish.",
        "`source_candidate_url` remains advisory metadata. Generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "",
        "## Summary",
        "",
        f"- Photo readiness rows: `{len(rows)}`",
        f"- NWSL rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'nwsl')}`",
        f"- Europe rows: `{sum(1 for row in rows if clean(row.get('scope_id')) == 'europe_top_flight')}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Readiness Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## Safe Operator Path",
        "",
        "- Verify official roster/team/player identity before any photo-review intake.",
        "- Park gray-area, reputable-media, Getty/AP/Reuters/licensed/news/photo leads as research-only leads unless official confirmation exists.",
        "- Future quarantine-download intake requires a later human-edited row; generated rows do not authorize download or approval.",
        "",
        "## Board Preview",
        "",
        "| Rank | Readiness Bucket | League | Team | Player | Source | Candidate Row | Source Row | Next Manual Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:40]:
        lines.append(
            "| {rank} | {bucket} | {league} | {team} | {player} | {domain} | {candidate_ref} | {source_ref} | {action} |".format(
                rank=clean(row.get("photo_readiness_rank")),
                bucket=clean(row.get("photo_review_readiness_bucket")),
                league=clean(row.get("league_id")),
                team=clean(row.get("team_name")).replace("|", "/"),
                player=clean(row.get("player_name")).replace("|", "/"),
                domain=clean(row.get("source_domain")).replace("|", "/"),
                candidate_ref=clean(row.get("candidate_action_row_ref")).replace("|", "%7C"),
                source_ref=clean(row.get("source_priority_row_ref")).replace("|", "%7C"),
                action=clean(row.get("next_manual_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def operator_focus_reason_flags(row: Mapping[str, str]) -> List[str]:
    flags: List[str] = []
    priority = clean(row.get("source_priority")).upper()
    issue = clean(row.get("issue_type")).lower()
    group = clean(row.get("manual_action_group"))
    if priority.startswith("P0"):
        flags.append("p0_source_or_roster_row")
    if priority.startswith("P1"):
        flags.append("p1_source_or_roster_row")
    if group == "duplicate_transfer_check" or any(
        token in issue
        for token in [
            "duplicate",
            "transfer",
            "loan",
            "stale_team_assignment",
            "stale_player",
            "expired",
            "short_term",
        ]
    ):
        flags.append("duplicate_transfer_loan_stale_or_short_term_issue")
    if any(token in issue for token in ["missing_player_profile", "player_profile_candidate_gap", "profile"]):
        flags.append("profile_or_official_page_gap")
    if group == "gray_area_reputable_media_lead":
        flags.append("gray_area_or_reputable_lead")
    if group == "future_quarantine_download_intake_prep":
        flags.append("future_intake_prep_only")
    if clean(row.get("operator_verify_required")).lower() == "yes":
        flags.append("operator_verify_required")
    return flags


def operator_focus_bucket(row: Mapping[str, str], flags: List[str]) -> str:
    priority = clean(row.get("source_priority")).upper()
    group = clean(row.get("manual_action_group"))
    if "duplicate_transfer_loan_stale_or_short_term_issue" in flags:
        return "1_duplicate_transfer_loan_stale_profile_check"
    if priority.startswith("P0") or clean(row.get("linked_queue_bucket")) == "p0_nwsl_roster_verification_first":
        return "2_p0_roster_or_source_verify"
    if group == "official_page_missing_or_season_rollover_verify" or "profile_or_official_page_gap" in flags:
        return "3_profile_or_official_page_gap"
    if group == "gray_area_reputable_media_lead":
        return "4_gray_area_or_reputable_lead"
    if priority.startswith("P1"):
        return "5_p1_source_followup"
    if group == "future_quarantine_download_intake_prep":
        return "6_future_intake_prep_only"
    return "7_metadata_watch"


def operator_focus_why(row: Mapping[str, str], bucket: str) -> str:
    player = clean(row.get("player_name")) or "team/source row"
    team = clean(row.get("team_name")) or clean(row.get("team_id"))
    if bucket == "1_duplicate_transfer_loan_stale_profile_check":
        return f"{player} has duplicate, transfer, loan, stale-profile, expired, or short-term metadata signals for {team}; verify official current status before any photo-review work."
    if bucket == "2_p0_roster_or_source_verify":
        return f"{team} is a P0 roster/source verification row; open the source and triage refs before any candidate-state writeback."
    if bucket == "3_profile_or_official_page_gap":
        return f"{player} may need an official profile or season-rollover page check; confirm the current official page before future intake."
    if bucket == "4_gray_area_or_reputable_lead":
        return f"{player} is backed by gray-area or reputable public-source metadata; park it until official roster/profile confirmation exists."
    if bucket == "5_p1_source_followup":
        return f"{team} is a P1 source follow-up; verify the advisory source row before considering later manual intake."
    if bucket == "6_future_intake_prep_only":
        return f"{team} may need future human-edited intake, but this generated row does not authorize download or approval."
    return f"{team} remains metadata watch only; no asset or approval action is implied."


def operator_focus_rows(candidate_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for row in candidate_rows:
        flags = operator_focus_reason_flags(row)
        selection_flags = [flag for flag in flags if flag != "operator_verify_required"]
        if not selection_flags:
            continue
        bucket = operator_focus_bucket(row, flags)
        source_ref = clean(row.get("source_priority_row_ref"))
        triage_ref = clean(row.get("triage_row_ref"))
        open_ref = source_ref or triage_ref
        output.append(
            {
                "focus_rank": "0",
                "focus_bucket": bucket,
                "focus_reason_flags": "|".join(flags),
                "priority_label": clean(row.get("source_priority")) or clean(row.get("linked_queue_bucket")) or "manual_review",
                "manual_action_group": clean(row.get("manual_action_group")),
                "source_tier": clean(row.get("source_tier")),
                "scope_id": clean(row.get("scope_id")),
                "league_id": clean(row.get("league_id")),
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "player_name": clean(row.get("player_name")),
                "issue_type": clean(row.get("issue_type")),
                "operator_action": clean(row.get("operator_action")),
                "source_priority": clean(row.get("source_priority")),
                "official_status": clean(row.get("official_status")),
                "confidence": clean(row.get("confidence")),
                "operator_verify_required": clean(row.get("operator_verify_required")),
                "source_domain": clean(row.get("source_domain")),
                "source_candidate_url": clean(row.get("source_candidate_url")),
                "source_priority_row_ref": source_ref,
                "triage_row_ref": triage_ref,
                "candidate_action_row_ref": f"{OUT_CANDIDATE_ACTIONS_CSV.as_posix()}#row={clean(row.get('candidate_action_rank'))}",
                "open_next_file": clean(row.get("source_priority_file")) or clean(row.get("triage_file")),
                "open_next_row_ref": open_ref,
                "why_row_matters": operator_focus_why(row, bucket),
                "next_manual_action": clean(row.get("next_manual_action")),
                "do_not_do": "Do not download assets, write headshots, approve candidates, create .approved markers, move files, or publish from this generated row.",
                "download_approved": "no",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "operator_decision": "",
                "operator_notes": "",
                **guardrails(),
            }
        )
    priority = {
        "1_duplicate_transfer_loan_stale_profile_check": 10,
        "2_p0_roster_or_source_verify": 20,
        "3_profile_or_official_page_gap": 30,
        "4_gray_area_or_reputable_lead": 40,
        "5_p1_source_followup": 50,
        "6_future_intake_prep_only": 60,
        "7_metadata_watch": 70,
    }
    output.sort(
        key=lambda item: (
            priority.get(item["focus_bucket"], 999),
            LEAGUE_ORDER.get(item["league_id"], 999),
            clean(item.get("team_name")),
            clean(item.get("player_name")),
            clean(item.get("source_candidate_url")),
        )
    )
    for index, row in enumerate(output, start=1):
        row["focus_rank"] = str(index)
    return output


def render_operator_focus(rows: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts = count_by(rows, "focus_bucket")
    lines = [
        "# Women's Soccer Athlete Operator Focus",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only, artifact-only focus packet for the next manual verification actions. It compresses the source-priority, triage, and candidate-action boards into rows with exact refs to open next.",
        "`source_candidate_url` remains advisory metadata. Generated local-download-law fields stay `download_approved=no` with blank `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`.",
        "",
        "## Summary",
        "",
        f"- Focus rows: `{len(rows)}`",
        f"- P0 rows: `{sum(1 for row in rows if 'p0_source_or_roster_row' in clean(row.get('focus_reason_flags')).split('|'))}`",
        f"- P1 rows: `{sum(1 for row in rows if 'p1_source_or_roster_row' in clean(row.get('focus_reason_flags')).split('|'))}`",
        f"- Duplicate/transfer/loan/stale-profile rows: `{sum(1 for row in rows if 'duplicate_transfer_loan_stale_or_short_term_issue' in clean(row.get('focus_reason_flags')).split('|'))}`",
        f"- Profile/official-page-gap rows: `{sum(1 for row in rows if 'profile_or_official_page_gap' in clean(row.get('focus_reason_flags')).split('|'))}`",
        f"- Download-approved yes rows: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Blank download-law source_url rows: `{sum(1 for row in rows if not clean(row.get('source_url')))}`",
        "",
        "## Focus Buckets",
        "",
    ]
    lines.extend(f"- {bucket}: `{count}`" for bucket, count in bucket_counts.items())
    lines += [
        "",
        "## Safe Operator Path",
        "",
        "- Open `open_next_row_ref`, then the paired `triage_row_ref`, before touching any manual intake.",
        "- Use official roster/team/player pages to resolve duplicate, transfer, loan, stale-profile, and profile-gap rows.",
        "- Keep gray-area and reputable-source leads parked until official confirmation exists.",
        "- Do not download assets, write headshots, approve candidates, create `.approved` markers, move files, or publish from this packet.",
        "",
        "## Focus Preview",
        "",
        "| Rank | Bucket | Priority | Team | Player | Source Row | Triage Row | Why It Matters |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:50]:
        lines.append(
            "| {rank} | {bucket} | {priority} | {team} | {player} | {source_ref} | {triage_ref} | {why} |".format(
                rank=clean(row.get("focus_rank")),
                bucket=clean(row.get("focus_bucket")),
                priority=clean(row.get("priority_label")).replace("|", "/"),
                team=clean(row.get("team_name")).replace("|", "/"),
                player=clean(row.get("player_name")).replace("|", "/"),
                source_ref=clean(row.get("source_priority_row_ref")).replace("|", "%7C"),
                triage_ref=clean(row.get("triage_row_ref")).replace("|", "%7C"),
                why=clean(row.get("why_row_matters")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_iso()
    rows = build_queue()
    download_rows = read_csv(DOWNLOAD_INTAKE_CSV)
    external_rows = read_csv(EXTERNAL_RESEARCH_CSV)
    action_rows = next_action_rows(rows, download_rows)
    source_rows = source_priority_rows(rows, external_rows)
    triage_rows = review_triage_rows(rows, source_rows)
    candidate_rows = candidate_action_rows(source_rows, triage_rows)
    photo_readiness = photo_readiness_rows(candidate_rows)
    focus_rows = operator_focus_rows(candidate_rows)
    write_csv(OUT_CSV, rows, FIELDS)
    write_text(OUT_MD, render_markdown(rows, generated_at))
    write_csv(OUT_NEXT_ACTIONS_CSV, action_rows, NEXT_ACTION_FIELDS)
    write_text(OUT_NEXT_ACTIONS_MD, render_next_actions(action_rows, generated_at))
    write_csv(OUT_SOURCE_PRIORITY_CSV, source_rows, SOURCE_PRIORITY_FIELDS)
    write_text(OUT_SOURCE_PRIORITY_MD, render_source_priority(source_rows, generated_at))
    write_csv(OUT_REVIEW_TRIAGE_CSV, triage_rows, REVIEW_TRIAGE_FIELDS)
    write_text(OUT_REVIEW_TRIAGE_MD, render_review_triage(triage_rows, generated_at))
    write_csv(OUT_CANDIDATE_ACTIONS_CSV, candidate_rows, CANDIDATE_ACTION_FIELDS)
    write_text(OUT_CANDIDATE_ACTIONS_MD, render_candidate_actions(candidate_rows, generated_at))
    write_csv(OUT_PHOTO_READINESS_CSV, photo_readiness, PHOTO_READINESS_FIELDS)
    write_text(OUT_PHOTO_READINESS_MD, render_photo_readiness(photo_readiness, generated_at))
    write_csv(OUT_OPERATOR_FOCUS_CSV, focus_rows, OPERATOR_FOCUS_FIELDS)
    write_text(OUT_OPERATOR_FOCUS_MD, render_operator_focus(focus_rows, generated_at))
    manifest = {
        "version": VERSION,
        "status": "athlete_verification_queue_ready",
        "generated_at_utc": generated_at,
        "queue_rows": len(rows),
        "nwsl_team_rows": sum(1 for row in rows if clean(row.get("scope_id")) == "nwsl"),
        "europe_league_rows": sum(1 for row in rows if clean(row.get("scope_id")) == "europe_top_flight"),
        "queue_bucket_counts": count_by(rows, "queue_bucket"),
        "p0_nwsl_roster_verification_rows": sum(1 for row in rows if clean(row.get("queue_bucket")) == "p0_nwsl_roster_verification_first"),
        "gray_area_rows": sum(as_int(row.get("gray_area_rows")) for row in rows),
        "missing_local_candidate_rows": sum(as_int(row.get("missing_local_candidate_rows")) for row in rows),
        "download_approved_yes_rows": sum(as_int(row.get("download_approved_yes_rows")) for row in rows),
        "first_action_bucket_counts": count_by(rows, "first_action_bucket"),
        "source_verification_bucket_counts": count_by(rows, "source_verification_bucket"),
        "queue_md": OUT_MD.as_posix(),
        "queue_csv": OUT_CSV.as_posix(),
        "next_actions_md": OUT_NEXT_ACTIONS_MD.as_posix(),
        "next_actions_csv": OUT_NEXT_ACTIONS_CSV.as_posix(),
        "next_action_rows": len(action_rows),
        "next_action_download_approved_yes_rows": sum(1 for row in action_rows if clean(row.get("download_approved")).lower() == "yes"),
        "next_action_blank_source_url_rows": sum(1 for row in action_rows if not clean(row.get("source_url"))),
        "source_priority_md": OUT_SOURCE_PRIORITY_MD.as_posix(),
        "source_priority_csv": OUT_SOURCE_PRIORITY_CSV.as_posix(),
        "source_priority_rows": len(source_rows),
        "source_priority_operator_verify_required_rows": sum(1 for row in source_rows if clean(row.get("operator_verify_required")).lower() == "yes"),
        "source_priority_gray_or_reputable_rows": sum(1 for row in source_rows if clean(row.get("source_review_bucket")) == "2_gray_area_or_reputable_manual_verify"),
        "source_priority_download_approved_yes_rows": sum(1 for row in source_rows if clean(row.get("download_approved")).lower() == "yes"),
        "source_priority_blank_source_url_rows": sum(1 for row in source_rows if not clean(row.get("source_url"))),
        "review_triage_md": OUT_REVIEW_TRIAGE_MD.as_posix(),
        "review_triage_csv": OUT_REVIEW_TRIAGE_CSV.as_posix(),
        "review_triage_rows": len(triage_rows),
        "review_triage_download_approved_yes_rows": sum(1 for row in triage_rows if clean(row.get("download_approved")).lower() == "yes"),
        "review_triage_blank_source_url_rows": sum(1 for row in triage_rows if not clean(row.get("source_url"))),
        "review_triage_primary_action_counts": count_by(triage_rows, "primary_manual_action"),
        "candidate_next_action_md": OUT_CANDIDATE_ACTIONS_MD.as_posix(),
        "candidate_next_action_csv": OUT_CANDIDATE_ACTIONS_CSV.as_posix(),
        "candidate_next_action_rows": len(candidate_rows),
        "candidate_next_action_download_approved_yes_rows": sum(1 for row in candidate_rows if clean(row.get("download_approved")).lower() == "yes"),
        "candidate_next_action_blank_source_url_rows": sum(1 for row in candidate_rows if not clean(row.get("source_url"))),
        "candidate_next_action_manual_action_counts": count_by(candidate_rows, "manual_action_group"),
        "photo_review_readiness_md": OUT_PHOTO_READINESS_MD.as_posix(),
        "photo_review_readiness_csv": OUT_PHOTO_READINESS_CSV.as_posix(),
        "photo_review_readiness_rows": len(photo_readiness),
        "photo_review_readiness_download_approved_yes_rows": sum(1 for row in photo_readiness if clean(row.get("download_approved")).lower() == "yes"),
        "photo_review_readiness_blank_source_url_rows": sum(1 for row in photo_readiness if not clean(row.get("source_url"))),
        "photo_review_readiness_bucket_counts": count_by(photo_readiness, "photo_review_readiness_bucket"),
        "operator_focus_md": OUT_OPERATOR_FOCUS_MD.as_posix(),
        "operator_focus_csv": OUT_OPERATOR_FOCUS_CSV.as_posix(),
        "operator_focus_rows": len(focus_rows),
        "operator_focus_p0_rows": sum(1 for row in focus_rows if "p0_source_or_roster_row" in clean(row.get("focus_reason_flags")).split("|")),
        "operator_focus_p1_rows": sum(1 for row in focus_rows if "p1_source_or_roster_row" in clean(row.get("focus_reason_flags")).split("|")),
        "operator_focus_duplicate_transfer_loan_stale_rows": sum(
            1 for row in focus_rows if "duplicate_transfer_loan_stale_or_short_term_issue" in clean(row.get("focus_reason_flags")).split("|")
        ),
        "operator_focus_profile_gap_rows": sum(1 for row in focus_rows if "profile_or_official_page_gap" in clean(row.get("focus_reason_flags")).split("|")),
        "operator_focus_download_approved_yes_rows": sum(1 for row in focus_rows if clean(row.get("download_approved")).lower() == "yes"),
        "operator_focus_blank_source_url_rows": sum(1 for row in focus_rows if not clean(row.get("source_url"))),
        "operator_focus_bucket_counts": count_by(focus_rows, "focus_bucket"),
        "inputs": [CONTACT_CSV.as_posix(), OPERATOR_BOARD_CSV.as_posix(), DOWNLOAD_INTAKE_CSV.as_posix(), EXTERNAL_RESEARCH_CSV.as_posix()],
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
    }
    write_json(OUT_JSON, manifest)
    write_json(
        OUT_NEXT_ACTIONS_JSON,
        {
            "version": VERSION,
            "status": "athlete_verification_next_actions_ready",
            "generated_at_utc": generated_at,
            "worksheet_rows": len(action_rows),
            "download_approved_yes_rows": sum(1 for row in action_rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in action_rows if not clean(row.get("source_url"))),
            "first_action_bucket_counts": count_by(action_rows, "first_action_bucket"),
            "source_verification_bucket_counts": count_by(action_rows, "source_verification_bucket"),
            "worksheet_md": OUT_NEXT_ACTIONS_MD.as_posix(),
            "worksheet_csv": OUT_NEXT_ACTIONS_CSV.as_posix(),
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
        },
    )
    write_json(
        OUT_SOURCE_PRIORITY_JSON,
        {
            "version": VERSION,
            "status": "athlete_source_priority_ready",
            "generated_at_utc": generated_at,
            "source_priority_rows": len(source_rows),
            "nwsl_source_rows": sum(1 for row in source_rows if clean(row.get("scope_id")) == "nwsl"),
            "europe_source_rows": sum(1 for row in source_rows if clean(row.get("scope_id")) == "europe_top_flight"),
            "operator_verify_required_rows": sum(1 for row in source_rows if clean(row.get("operator_verify_required")).lower() == "yes"),
            "gray_or_reputable_manual_verify_rows": sum(1 for row in source_rows if clean(row.get("source_review_bucket")) == "2_gray_area_or_reputable_manual_verify"),
            "download_approved_yes_rows": sum(1 for row in source_rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in source_rows if not clean(row.get("source_url"))),
            "source_review_bucket_counts": count_by(source_rows, "source_review_bucket"),
            "source_candidate_level_counts": count_by(source_rows, "source_candidate_level"),
            "league_counts": count_by(source_rows, "league_id"),
            "worksheet_md": OUT_SOURCE_PRIORITY_MD.as_posix(),
            "worksheet_csv": OUT_SOURCE_PRIORITY_CSV.as_posix(),
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
        },
    )
    write_json(
        OUT_REVIEW_TRIAGE_JSON,
        {
            "version": VERSION,
            "status": "athlete_review_triage_ready",
            "generated_at_utc": generated_at,
            "triage_rows": len(triage_rows),
            "nwsl_rows": sum(1 for row in triage_rows if clean(row.get("scope_id")) == "nwsl"),
            "europe_rows": sum(1 for row in triage_rows if clean(row.get("scope_id")) == "europe_top_flight"),
            "download_approved_yes_rows": sum(1 for row in triage_rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in triage_rows if not clean(row.get("source_url"))),
            "blank_entity_id_rows": sum(1 for row in triage_rows if not clean(row.get("entity_id"))),
            "primary_manual_action_counts": count_by(triage_rows, "primary_manual_action"),
            "worksheet_md": OUT_REVIEW_TRIAGE_MD.as_posix(),
            "worksheet_csv": OUT_REVIEW_TRIAGE_CSV.as_posix(),
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
        },
    )
    write_json(
        OUT_CANDIDATE_ACTIONS_JSON,
        {
            "version": VERSION,
            "status": "athlete_candidate_next_actions_ready",
            "generated_at_utc": generated_at,
            "candidate_action_rows": len(candidate_rows),
            "nwsl_rows": sum(1 for row in candidate_rows if clean(row.get("scope_id")) == "nwsl"),
            "europe_rows": sum(1 for row in candidate_rows if clean(row.get("scope_id")) == "europe_top_flight"),
            "download_approved_yes_rows": sum(1 for row in candidate_rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in candidate_rows if not clean(row.get("source_url"))),
            "blank_entity_id_rows": sum(1 for row in candidate_rows if not clean(row.get("entity_id"))),
            "manual_action_group_counts": count_by(candidate_rows, "manual_action_group"),
            "source_tier_counts": count_by(candidate_rows, "source_tier"),
            "worksheet_md": OUT_CANDIDATE_ACTIONS_MD.as_posix(),
            "worksheet_csv": OUT_CANDIDATE_ACTIONS_CSV.as_posix(),
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
        },
    )
    write_json(
        OUT_PHOTO_READINESS_JSON,
        {
            "version": VERSION,
            "status": "athlete_photo_review_readiness_ready",
            "generated_at_utc": generated_at,
            "photo_readiness_rows": len(photo_readiness),
            "nwsl_rows": sum(1 for row in photo_readiness if clean(row.get("scope_id")) == "nwsl"),
            "europe_rows": sum(1 for row in photo_readiness if clean(row.get("scope_id")) == "europe_top_flight"),
            "download_approved_yes_rows": sum(1 for row in photo_readiness if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in photo_readiness if not clean(row.get("source_url"))),
            "blank_entity_id_rows": sum(1 for row in photo_readiness if not clean(row.get("entity_id"))),
            "readiness_bucket_counts": count_by(photo_readiness, "photo_review_readiness_bucket"),
            "worksheet_md": OUT_PHOTO_READINESS_MD.as_posix(),
            "worksheet_csv": OUT_PHOTO_READINESS_CSV.as_posix(),
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
        },
    )
    write_json(
        OUT_OPERATOR_FOCUS_JSON,
        {
            "version": VERSION,
            "status": "athlete_operator_focus_ready",
            "generated_at_utc": generated_at,
            "focus_rows": len(focus_rows),
            "p0_rows": sum(1 for row in focus_rows if "p0_source_or_roster_row" in clean(row.get("focus_reason_flags")).split("|")),
            "p1_rows": sum(1 for row in focus_rows if "p1_source_or_roster_row" in clean(row.get("focus_reason_flags")).split("|")),
            "duplicate_transfer_loan_stale_rows": sum(
                1 for row in focus_rows if "duplicate_transfer_loan_stale_or_short_term_issue" in clean(row.get("focus_reason_flags")).split("|")
            ),
            "profile_gap_rows": sum(1 for row in focus_rows if "profile_or_official_page_gap" in clean(row.get("focus_reason_flags")).split("|")),
            "download_approved_yes_rows": sum(1 for row in focus_rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in focus_rows if not clean(row.get("source_url"))),
            "focus_bucket_counts": count_by(focus_rows, "focus_bucket"),
            "worksheet_md": OUT_OPERATOR_FOCUS_MD.as_posix(),
            "worksheet_csv": OUT_OPERATOR_FOCUS_CSV.as_posix(),
            "source_priority_csv": OUT_SOURCE_PRIORITY_CSV.as_posix(),
            "triage_csv": OUT_REVIEW_TRIAGE_CSV.as_posix(),
            "candidate_action_csv": OUT_CANDIDATE_ACTIONS_CSV.as_posix(),
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
        },
    )
    print(json.dumps({"version": VERSION, "status": manifest["status"], "queue_rows": len(rows), "next_action_rows": len(action_rows), "source_priority_rows": len(source_rows), "review_triage_rows": len(triage_rows), "candidate_action_rows": len(candidate_rows), "photo_readiness_rows": len(photo_readiness), "operator_focus_rows": len(focus_rows), "queue": OUT_MD.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
