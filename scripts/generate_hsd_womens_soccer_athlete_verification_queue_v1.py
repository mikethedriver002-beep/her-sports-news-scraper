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
                "entity_id": clean(row.get("team_id")),
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


def main() -> int:
    generated_at = now_iso()
    rows = build_queue()
    download_rows = read_csv(DOWNLOAD_INTAKE_CSV)
    action_rows = next_action_rows(rows, download_rows)
    write_csv(OUT_CSV, rows, FIELDS)
    write_text(OUT_MD, render_markdown(rows, generated_at))
    write_csv(OUT_NEXT_ACTIONS_CSV, action_rows, NEXT_ACTION_FIELDS)
    write_text(OUT_NEXT_ACTIONS_MD, render_next_actions(action_rows, generated_at))
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
    print(json.dumps({"version": VERSION, "status": manifest["status"], "queue_rows": len(rows), "next_action_rows": len(action_rows), "queue": OUT_MD.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
