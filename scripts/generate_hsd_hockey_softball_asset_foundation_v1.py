from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - reported in manifests
    Image = None
    ImageDraw = None
    ImageFont = None


VERSION = "hsd-hockey-softball-asset-foundation-v1-review-only"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_INDEX_MD = Path("data/asset_registry/hockey_softball_foundation_coverage_index.md")
COVERAGE_INDEX_CSV = Path("data/asset_registry/hockey_softball_foundation_coverage_index.csv")
COVERAGE_INDEX_JSON = Path("data/asset_registry/hockey_softball_foundation_coverage_index.json")

TEAM_FIELDS = [
    "league_id",
    "team_id",
    "team_name",
    "city",
    "country",
    "official_team_url",
    "official_roster_url",
    "manual_review_status",
    "render_enabled",
    "publish_ready",
]

SOURCE_FIELDS = [
    "entity_type",
    "entity_id",
    "source_kind",
    "source_url",
    "source_domain",
    "source_tier",
    "manual_review_status",
    "paid_source",
    "download_allowed",
    "approval_status",
    "notes",
]

ASSET_SLOT_FIELDS = [
    "entity_type",
    "entity_id",
    "league_id",
    "team_id",
    "asset_slot",
    "intended_use",
    "target_path",
    "source_url_required",
    "local_file_path",
    "file_exists",
    "approval_status",
    "render_enabled",
    "auto_download_allowed",
    "publish_ready",
    "notes",
]

APPROVAL_FIELDS = [
    "entity_type",
    "entity_id",
    "approval_scope",
    "approval_status",
    "approved_by",
    "approved_at_utc",
    "auto_approval_allowed",
    "render_enabled",
    "publish_ready",
    "notes",
]

PLAYER_FIELDS = [
    "league_id",
    "team_id",
    "player_id",
    "provider_player_id",
    "display_name",
    "roster_source_url",
    "manual_review_status",
    "approval_status",
    "notes",
]

COVERAGE_INDEX_FIELDS = [
    "sport_family",
    "league_id",
    "league_name",
    "team_rows",
    "source_rows",
    "logo_contact_rows",
    "logo_intake_rows",
    "athlete_candidate_rows",
    "athlete_intake_rows",
    "athlete_team_boards",
    "foundation_source_urls",
    "team_registry",
    "asset_slot_registry",
    "approval_registry",
    "logo_contact_sheet",
    "logo_review_intake",
    "athlete_contact_sheet",
    "athlete_review_intake",
    "athlete_contact_sheet_index",
    "source_review_helper",
    "workflow_readiness",
    "asset_review_action_queue",
    "batch_source_review_helper",
    "next_operator_action",
    "guardrail_note",
]

LOGO_CONTACT_FIELDS = [
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
]

LOGO_INTAKE_FIELDS = [
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
]

ATHLETE_FIELDS = [
    "sport_family",
    "league_id",
    "team_id",
    "team_name",
    "player_id",
    "display_name",
    "candidate_id",
    "candidate_rank",
    "candidate_status",
    "source_url",
    "source_domain",
    "source_tier",
    "source_platform",
    "source_kind",
    "candidate_method",
    "page_title",
    "canonical_url",
    "referring_roster_url",
    "photo_candidate_url",
    "local_candidate_path",
    "local_candidate_exists",
    "approved_marker_path",
    "approved_marker_exists",
    "identity_review_status",
    "approval_status",
    "license_hint",
    "rights_note",
    "attribution_text",
    "identity_evidence_notes",
    "identity_risk_flags",
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
]

ATHLETE_INTAKE_FIELDS = [
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
]

ATHLETE_SOURCE_CANDIDATE_SLOTS = [
    {
        "suffix": "roster_source_candidate_01",
        "display_name": "operator_add_player_from_team_roster",
        "candidate_status": "official_roster_source_review_slot",
        "source_kind": "roster_or_public_profile_candidate",
        "source_platform": "official_team_roster_page",
        "candidate_method": "manual_roster_source_slot_no_image_download",
        "page_title": "team roster source review",
        "identity_review_status": "source_review_ready_identity_not_filled",
        "identity_evidence_notes": "Operator can mark source_reviewed after opening the roster page; player identity and local file review must remain hold until a concrete athlete and local candidate asset exist.",
    },
    {
        "suffix": "team_profile_source_candidate_02",
        "display_name": "operator_add_player_from_team_profile_source",
        "candidate_status": "official_team_profile_source_review_slot",
        "source_kind": "team_profile_source_candidate",
        "source_platform": "official_team_page",
        "candidate_method": "manual_team_profile_source_slot_no_image_download",
        "page_title": "team profile source review",
        "identity_review_status": "source_review_ready_identity_not_filled",
        "identity_evidence_notes": "Operator can use the team page as context/source evidence; approval stays held until a named athlete and reviewed local candidate asset exist.",
    },
    {
        "suffix": "league_player_index_candidate_03",
        "display_name": "operator_add_player_from_league_player_index",
        "candidate_status": "official_league_player_index_review_slot",
        "source_kind": "league_player_index_candidate",
        "source_platform": "official_league_player_index",
        "candidate_method": "manual_league_player_index_slot_no_image_download",
        "page_title": "league player index source review",
        "identity_review_status": "source_review_ready_identity_not_filled",
        "identity_evidence_notes": "Operator can mark the source as reviewed after opening the league player index; identity and asset approval remain held until a named athlete row has local candidate evidence.",
    },
]


PWHL_TEAMS = [
    ("boston_fleet", "Boston Fleet", "Boston", "US", "https://www.thepwhl.com/en/teams/boston-fleet"),
    ("detroit", "PWHL Detroit", "Detroit", "US", "https://www.thepwhl.com/en/teams/detroit"),
    ("hamilton", "PWHL Hamilton", "Hamilton", "Canada", "https://www.thepwhl.com/en/teams/hamilton"),
    ("las_vegas", "PWHL Las Vegas", "Las Vegas", "US", "https://www.thepwhl.com/en/teams/las-vegas"),
    ("minnesota_frost", "Minnesota Frost", "Minnesota", "US", "https://www.thepwhl.com/en/teams/minnesota-frost"),
    ("montreal_victoire", "Montreal Victoire", "Montreal", "Canada", "https://www.thepwhl.com/en/teams/montreal-victoire"),
    ("new_york_sirens", "New York Sirens", "New York", "US", "https://www.thepwhl.com/en/teams/new-york-sirens"),
    ("ottawa_charge", "Ottawa Charge", "Ottawa", "Canada", "https://www.thepwhl.com/en/teams/ottawa-charge"),
    ("san_jose", "PWHL San Jose", "San Jose", "US", "https://www.thepwhl.com/en/teams/san-jose"),
    ("seattle_torrent", "Seattle Torrent", "Seattle", "US", "https://www.thepwhl.com/en/teams/seattle-torrent"),
    ("toronto_sceptres", "Toronto Sceptres", "Toronto", "Canada", "https://www.thepwhl.com/en/teams/toronto-sceptres"),
    ("vancouver_goldeneyes", "Vancouver Goldeneyes", "Vancouver", "Canada", "https://www.thepwhl.com/en/teams/vancouver-goldeneyes"),
]

AUSL_TEAMS = [
    ("carolina_blaze", "Carolina Blaze", "Durham", "US", "https://theausl.com/blaze/"),
    ("chicago_bandits", "Chicago Bandits", "Rosemont", "US", "https://theausl.com/bandits/"),
    ("oklahoma_city_spark", "Oklahoma City Spark", "Oklahoma City", "US", "https://theausl.com/spark/"),
    ("portland_cascade", "Portland Cascade", "Portland", "US", "https://theausl.com/cascade/"),
    ("texas_volts", "Texas Volts", "Austin", "US", "https://theausl.com/volts/"),
    ("utah_talons", "Utah Talons", "Salt Lake City", "US", "https://theausl.com/talons/"),
]

FOUNDATIONS = [
    {
        "sport_family": "womens_hockey",
        "league_id": "pwhl",
        "league_name": "Professional Women's Hockey League",
        "registry_root": Path("data/asset_registry/womens_hockey/pwhl"),
        "artifact_root": Path("data/asset_registry/womens_hockey"),
        "asset_root": "assets/leagues/womens_hockey/pwhl",
        "league_url": "https://www.thepwhl.com/en/",
        "teams_url": "https://www.thepwhl.com/en/",
        "players_url": "https://www.thepwhl.com/en/stats/player-stats",
        "teams": PWHL_TEAMS,
    },
    {
        "sport_family": "softball",
        "league_id": "ausl",
        "league_name": "Athletes Unlimited Softball League",
        "registry_root": Path("data/asset_registry/softball/ausl"),
        "artifact_root": Path("data/asset_registry/softball"),
        "asset_root": "assets/leagues/softball/ausl",
        "league_url": "https://theausl.com/",
        "teams_url": "https://theausl.com/",
        "players_url": "https://theausl.com/players/",
        "teams": AUSL_TEAMS,
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def source_domain(url: str) -> str:
    match = re.match(r"^https?://([^/]+)", clean(url))
    return match.group(1).lower() if match else ""


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def existing_by_key(rows: Iterable[Mapping[str, str]], key_fields: Iterable[str]) -> Dict[tuple[str, ...], Mapping[str, str]]:
    keys = list(key_fields)
    return {tuple(clean(row.get(key)) for key in keys): row for row in rows}


def protect_false(row: Dict[str, str]) -> Dict[str, str]:
    protected = dict(row)
    for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis", "asset_downloads"]:
        if field in protected:
            protected[field] = "false"
    return protected


def preserve_intake(
    path: Path,
    generated_rows: List[Dict[str, str]],
    fields: List[str],
    key_fields: List[str],
) -> List[Dict[str, str]]:
    existing = existing_by_key(read_csv(path), key_fields)
    output: List[Dict[str, str]] = []
    for row in generated_rows:
        key = tuple(clean(row.get(field)) for field in key_fields)
        merged = dict(row)
        old = existing.get(key)
        if old:
            for field, value in old.items():
                if field not in merged or field not in {
                    "publish_ready",
                    "auto_approval",
                    "auto_publish",
                    "move_files",
                    "paid_apis",
                    "asset_downloads",
                }:
                    merged[field] = clean(value)
        output.append(protect_false(merged))
    all_fields = list(fields)
    for old in existing.values():
        for field in old:
            if field not in all_fields:
                all_fields.append(field)
    return [{field: row.get(field, "") for field in all_fields} for row in output]


def build_registry_rows(foundation: Mapping[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    league_id = foundation["league_id"]
    league_url = foundation["league_url"]
    teams_url = foundation["teams_url"]
    players_url = foundation["players_url"]
    asset_root = foundation["asset_root"]
    teams = foundation["teams"]

    team_rows = [
        {
            "league_id": league_id,
            "team_id": team_id,
            "team_name": name,
            "city": city,
            "country": country,
            "official_team_url": url,
            "official_roster_url": f"{url.rstrip('/')}/roster",
            "manual_review_status": "review_required",
            "render_enabled": "false",
            "publish_ready": "false",
        }
        for team_id, name, city, country, url in teams
    ]

    source_rows = [
        {
            "entity_type": "league",
            "entity_id": league_id,
            "source_kind": "league_home",
            "source_url": league_url,
            "source_domain": source_domain(league_url),
            "source_tier": "official_candidate",
            "manual_review_status": "review_required",
            "paid_source": "false",
            "download_allowed": "false",
            "approval_status": "not_approved",
            "notes": "review-only league source candidate; no automatic fetch",
        },
        {
            "entity_type": "league",
            "entity_id": league_id,
            "source_kind": "teams_index",
            "source_url": teams_url,
            "source_domain": source_domain(teams_url),
            "source_tier": "official_candidate",
            "manual_review_status": "review_required",
            "paid_source": "false",
            "download_allowed": "false",
            "approval_status": "not_approved",
            "notes": "review-only team list source candidate; no automatic fetch",
        },
        {
            "entity_type": "league",
            "entity_id": league_id,
            "source_kind": "players_index",
            "source_url": players_url,
            "source_domain": source_domain(players_url),
            "source_tier": "official_candidate",
            "manual_review_status": "review_required",
            "paid_source": "false",
            "download_allowed": "false",
            "approval_status": "not_approved",
            "notes": "review-only athlete candidate source; no automatic fetch",
        },
    ]
    for team_id, _name, _city, _country, url in teams:
        source_rows.extend(
            [
                {
                    "entity_type": "team",
                    "entity_id": team_id,
                    "source_kind": "team_home",
                    "source_url": url,
                    "source_domain": source_domain(url),
                    "source_tier": "official_candidate",
                    "manual_review_status": "review_required",
                    "paid_source": "false",
                    "download_allowed": "false",
                    "approval_status": "not_approved",
                    "notes": "review-only team identity source candidate; no automatic fetch",
                },
                {
                    "entity_type": "team",
                    "entity_id": team_id,
                    "source_kind": "roster",
                    "source_url": f"{url.rstrip('/')}/roster",
                    "source_domain": source_domain(url),
                    "source_tier": "official_candidate",
                    "manual_review_status": "review_required",
                    "paid_source": "false",
                    "download_allowed": "false",
                    "approval_status": "not_approved",
                    "notes": "review-only athlete layer source candidate; operator verifies before adding players",
                },
                {
                    "entity_type": "team",
                    "entity_id": team_id,
                    "source_kind": "logo_review_source",
                    "source_url": url,
                    "source_domain": source_domain(url),
                    "source_tier": "official_candidate",
                    "manual_review_status": "review_required",
                    "paid_source": "false",
                    "download_allowed": "false",
                    "approval_status": "not_approved",
                    "notes": "operator may use page for visual logo evidence; no asset download by script",
                },
            ]
        )

    slot_rows = [
        {
            "entity_type": "league",
            "entity_id": league_id,
            "league_id": league_id,
            "team_id": "",
            "asset_slot": "league_mark",
            "intended_use": "league mark reference candidate",
            "target_path": f"{asset_root}/league_mark.png",
            "source_url_required": "true",
            "local_file_path": "",
            "file_exists": "false",
            "approval_status": "not_approved",
            "render_enabled": "false",
            "auto_download_allowed": "false",
            "publish_ready": "false",
            "notes": "review-only placeholder; no file write expected",
        }
    ]
    approval_rows = [
        {
            "entity_type": "league",
            "entity_id": league_id,
            "approval_scope": "league_mark",
            "approval_status": "not_approved",
            "approved_by": "",
            "approved_at_utc": "",
            "auto_approval_allowed": "false",
            "render_enabled": "false",
            "publish_ready": "false",
            "notes": "manual review required",
        }
    ]
    for team_id, _name, _city, _country, _url in teams:
        target = f"{asset_root}/teams/{team_id}/logo.png"
        slot_rows.append(
            {
                "entity_type": "team",
                "entity_id": team_id,
                "league_id": league_id,
                "team_id": team_id,
                "asset_slot": "primary_logo",
                "intended_use": "team logo reference candidate",
                "target_path": target,
                "source_url_required": "true",
                "local_file_path": "",
                "file_exists": "false",
                "approval_status": "not_approved",
                "render_enabled": "false",
                "auto_download_allowed": "false",
                "publish_ready": "false",
                "notes": "review-only placeholder; no file write expected",
            }
        )
        for scope in ["team_identity", "team_logo", "team_roster_source"]:
            approval_rows.append(
                {
                    "entity_type": "team",
                    "entity_id": team_id,
                    "approval_scope": scope,
                    "approval_status": "not_approved",
                    "approved_by": "",
                    "approved_at_utc": "",
                    "auto_approval_allowed": "false",
                    "render_enabled": "false",
                    "publish_ready": "false",
                    "notes": "manual review required",
                }
            )

    return {
        "teams": team_rows,
        "source_urls": source_rows,
        "asset_slots": slot_rows,
        "approval_status": approval_rows,
        "players": [],
    }


def team_lookup(foundation: Mapping[str, Any]) -> Dict[str, str]:
    return {team_id: name for team_id, name, *_rest in foundation["teams"]}


def source_lookup(rows: Iterable[Mapping[str, str]]) -> Dict[tuple[str, str, str], str]:
    return {
        (clean(row.get("entity_type")), clean(row.get("entity_id")), clean(row.get("source_kind"))): clean(row.get("source_url"))
        for row in rows
    }


def build_logo_contact_rows(foundation: Mapping[str, Any], registry: Mapping[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    sport = foundation["sport_family"]
    league_id = foundation["league_id"]
    artifact_root = foundation["artifact_root"]
    sources = source_lookup(registry["source_urls"])
    teams = team_lookup(foundation)
    rows = []
    for slot in registry["asset_slots"]:
        entity_type = slot["entity_type"]
        entity_id = slot["entity_id"]
        display_name = foundation["league_name"] if entity_type == "league" else teams.get(entity_id, entity_id)
        source_kind = "league_home" if entity_type == "league" else "logo_review_source"
        target_path = slot["target_path"]
        rows.append(
            {
                "sport_family": sport,
                "league_id": league_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "display_name": display_name,
                "asset_slot": slot["asset_slot"],
                "target_path": target_path,
                "local_file_exists": "true" if (PROJECT_ROOT / target_path).exists() else "false",
                "official_source_candidate": sources.get((entity_type, entity_id, source_kind), ""),
                "source_tier": "official_candidate",
                "manual_review_status": "review_required",
                "allowed_decisions": "approve_for_review_only_renderer_use|deny_logo_asset|hold_for_more_evidence|revise_source_metadata",
                "human_intake_file": f"{artifact_root.as_posix()}/{sport}_logo_review_intake.csv",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return rows


def build_logo_intake_rows(foundation: Mapping[str, Any], contact_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    path = output_path(foundation["artifact_root"] / f"{foundation['sport_family']}_logo_review_intake.csv")
    rows = []
    for row in contact_rows:
        rows.append(
            {
                "sport_family": row["sport_family"],
                "league_id": row["league_id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "display_name": row["display_name"],
                "asset_slot": row["asset_slot"],
                "target_path": row["target_path"],
                "official_source_candidate": row["official_source_candidate"],
                "allowed_decisions": row["allowed_decisions"],
                "operator_decision": "operator_fill_required",
                "source_reviewed": "operator_fill_required",
                "identity_match": "operator_fill_required",
                "source_url_to_record": "",
                "registry_action": "hold_no_registry_state_change",
                "operator_notes": "",
                "reviewed_by": "",
                "reviewed_at_local": "",
                "approval_scope": f"review_only_renderer_{row['sport_family']}_logo_trust_manual_intake",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return preserve_intake(path, rows, LOGO_INTAKE_FIELDS, ["sport_family", "entity_type", "entity_id", "asset_slot"])


def build_athlete_rows(foundation: Mapping[str, Any], registry: Mapping[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    sport = foundation["sport_family"]
    league_id = foundation["league_id"]
    artifact_root = foundation["artifact_root"].as_posix()
    source_rows = source_lookup(registry["source_urls"])
    rows = []
    for team_id, team_name, _city, _country, _url in foundation["teams"]:
        source_by_kind = {
            "roster_or_public_profile_candidate": source_rows.get(("team", team_id, "roster"), ""),
            "team_profile_source_candidate": source_rows.get(("team", team_id, "team_home"), ""),
            "league_player_index_candidate": foundation["players_url"],
        }
        for rank, slot in enumerate(ATHLETE_SOURCE_CANDIDATE_SLOTS, start=1):
            candidate_id = f"{team_id}_{slot['suffix']}"
            source_url = source_by_kind[slot["source_kind"]]
            rows.append(
                {
                    "sport_family": sport,
                    "league_id": league_id,
                    "team_id": team_id,
                    "team_name": team_name,
                    "player_id": "",
                    "display_name": slot["display_name"],
                    "candidate_id": candidate_id,
                    "candidate_rank": str(rank),
                    "candidate_status": slot["candidate_status"],
                    "source_url": source_url,
                    "source_domain": source_domain(source_url),
                    "source_tier": "official_candidate",
                    "source_platform": slot["source_platform"],
                    "source_kind": slot["source_kind"],
                    "candidate_method": slot["candidate_method"],
                    "page_title": f"{team_name} {slot['page_title']}",
                    "canonical_url": source_url,
                    "referring_roster_url": source_rows.get(("team", team_id, "roster"), ""),
                    "photo_candidate_url": "",
                    "local_candidate_path": f"{foundation['asset_root']}/athletes/{team_id}/{candidate_id}/headshot.png",
                    "local_candidate_exists": "false",
                    "approved_marker_path": f"{foundation['asset_root']}/athletes/{team_id}/{candidate_id}/.approved",
                    "approved_marker_exists": "false",
                    "identity_review_status": slot["identity_review_status"],
                    "approval_status": "not_approved",
                    "license_hint": "operator_rights_review_required",
                    "rights_note": "review_only_source_candidate; no image downloaded; no renderer approval",
                    "attribution_text": "",
                    "identity_evidence_notes": slot["identity_evidence_notes"],
                    "identity_risk_flags": "named_athlete_and_local_candidate_asset_missing",
                    "allowed_decisions": "hold_identity|revise_source_metadata|deny_photo_candidate",
                    "human_intake_file": f"{artifact_root}/{sport}_athlete_photo_review_intake.csv",
                    "team_review_board_path": f"{artifact_root}/athlete_photo_contact_sheets/{team_id}.md",
                    "review_only": "true",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                }
            )
    return rows


def build_athlete_intake_rows(foundation: Mapping[str, Any], athlete_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    path = output_path(foundation["artifact_root"] / f"{foundation['sport_family']}_athlete_photo_review_intake.csv")
    rows = []
    for row in athlete_rows:
        rows.append(
            {
                "sport_family": row["sport_family"],
                "league_id": row["league_id"],
                "team_id": row["team_id"],
                "team_name": row["team_name"],
                "player_id": row["player_id"],
                "display_name": row["display_name"],
                "candidate_id": row["candidate_id"],
                "local_candidate_path": row["local_candidate_path"],
                "source_url": row["source_url"],
                "photo_candidate_url": row["photo_candidate_url"],
                "approval_status": row["approval_status"],
                "identity_review_status": row["identity_review_status"],
                "allowed_decisions": row["allowed_decisions"],
                "operator_decision": "operator_fill_required",
                "identity_verified": "operator_fill_required",
                "source_reviewed": "operator_fill_required",
                "local_file_reviewed": "operator_fill_required",
                "source_allowed_for_review_only": "operator_fill_required",
                "rights_reviewed": "operator_fill_required",
                "source_url_to_record": "",
                "registry_action": "hold_no_registry_state_change",
                "operator_notes": "",
                "reviewed_by": "",
                "reviewed_at_local": "",
                "approval_scope": f"review_only_renderer_{row['sport_family']}_athlete_photo_trust_manual_intake",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return preserve_intake(path, rows, ATHLETE_INTAKE_FIELDS, ["sport_family", "team_id", "candidate_id"])


def font(size: int, bold: bool = False) -> Any:
    if ImageFont is None:
        return None
    try:
        name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def make_logo_contact_png(rows: List[Dict[str, str]], out: Path, title: str) -> str:
    if Image is None or ImageDraw is None:
        return ""
    cols = 3
    card_w, card_h = 360, 150
    margin = 28
    rows_count = (len(rows) + cols - 1) // cols
    width = margin * 2 + cols * card_w
    height = 120 + margin + rows_count * card_h
    image = Image.new("RGB", (width, height), (248, 249, 251))
    draw = ImageDraw.Draw(image)
    draw.text((margin, 28), title, fill=(20, 24, 31), font=font(26, True))
    draw.text((margin, 64), "Review-only source board. No downloads, approvals, publish movement, or asset writes.", fill=(77, 85, 99), font=font(15))
    for index, row in enumerate(rows):
        x = margin + (index % cols) * card_w
        y = 110 + (index // cols) * card_h
        draw.rounded_rectangle((x, y, x + card_w - 18, y + card_h - 18), radius=8, fill=(255, 255, 255), outline=(209, 213, 219))
        draw.rectangle((x + 18, y + 24, x + 86, y + 92), fill=(229, 231, 235), outline=(156, 163, 175))
        draw.text((x + 104, y + 24), row["display_name"][:32], fill=(17, 24, 39), font=font(16, True))
        draw.text((x + 104, y + 50), row["asset_slot"], fill=(55, 65, 81), font=font(13))
        draw.text((x + 104, y + 72), f"exists: {row['local_file_exists']}", fill=(107, 114, 128), font=font(12))
        draw.text((x + 18, y + 108), row["official_source_candidate"][:48], fill=(75, 85, 99), font=font(11))
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    return out.as_posix()


def render_logo_markdown(rows: List[Dict[str, str]], png_path: str, foundation: Mapping[str, Any], generated_at: str) -> str:
    lines = [
        f"# {foundation['league_name']} Logo Source Contact Sheet",
        "",
        "Review-only board for league/team logo source candidates.",
        "",
        f"- Generated: `{generated_at}`",
        f"- Rows: `{len(rows)}`",
        "- No downloads, no auto-approval, no publish-ready movement.",
        f"- Human intake: `{foundation['artifact_root'].as_posix()}/{foundation['sport_family']}_logo_review_intake.csv`",
    ]
    if png_path:
        lines.extend(["", f"![Logo contact sheet]({Path(png_path).name})"])
    lines.extend(["", "## Rows", ""])
    for row in rows:
        lines.append(f"- {row['display_name']} | {row['asset_slot']} | {row['official_source_candidate']}")
    return "\n".join(lines) + "\n"


def render_athlete_index(rows: List[Dict[str, str]], foundation: Mapping[str, Any], generated_at: str) -> str:
    lines = [
        f"# {foundation['league_name']} Athlete Photo Candidate Layer",
        "",
        "Review-only athlete candidate layer seeded from official roster, team-profile, and league player-index source candidates.",
        "",
        f"- Generated: `{generated_at}`",
        f"- Candidate rows: `{len(rows)}`",
        f"- Team boards: `{len({row['team_id'] for row in rows})}`",
        "- No downloads or approvals. `headshot.png` and `.approved` are proposed manual target paths only and are never written by this generator.",
        "- Source pages can be marked reviewed after a manual source sweep; player identity and registry approval stay held until a named athlete and local candidate asset exist.",
        f"- Human intake: `{foundation['artifact_root'].as_posix()}/{foundation['sport_family']}_athlete_photo_review_intake.csv`",
        "",
        "## Team Boards",
        "",
    ]
    seen = set()
    for row in rows:
        if row["team_id"] in seen:
            continue
        seen.add(row["team_id"])
        lines.append(f"- {row['team_name']} | [board]({row['team_review_board_path']}) | {row['source_url']}")
    return "\n".join(lines) + "\n"


def write_team_boards(rows: List[Dict[str, str]]) -> None:
    rows_by_board: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        rows_by_board.setdefault(row["team_review_board_path"], []).append(row)
    for board_path, team_rows in rows_by_board.items():
        first = team_rows[0]
        lines = [
            f"# {first['team_name']} Athlete Candidate Board",
            "",
            "Review-only source-candidate board for operator-supplied athlete/photo candidates.",
            "",
            f"- Candidate rows: `{len(team_rows)}`",
            "- Source review can confirm the roster/profile/index page was opened and relevant.",
            "- Identity review must stay held until the row names a concrete athlete and points to reviewed evidence.",
            "- Local file review must stay `no` until Mike manually supplies a candidate file.",
            "- Guardrails: no downloads, no auto-approval, no `.approved` markers, no publish-ready movement.",
            "",
            "## Candidate Rows",
            "",
        ]
        for index, row in enumerate(sorted(team_rows, key=lambda item: clean(item.get("candidate_rank"))), start=1):
            lines.extend(
                [
                    f"{index}. `{row['candidate_id']}` | {row['display_name']}",
                    f"   - Source kind: `{row['source_kind']}`",
                    f"   - Source candidate: `{row['source_url']}`",
                    f"   - Local candidate path: `{row['local_candidate_path']}`",
                    f"   - Approved marker path: `{row['approved_marker_path']}`",
                    f"   - Hold reason: {row['identity_evidence_notes']}",
                ]
            )
        lines.append("")
        write_text(board_path, "\n".join(lines))


def write_foundation(foundation: Mapping[str, Any], generated_at: str) -> Dict[str, Any]:
    registry = build_registry_rows(foundation)
    root = foundation["registry_root"]
    write_csv(root / "teams.csv", registry["teams"], TEAM_FIELDS)
    write_csv(root / "source_urls.csv", registry["source_urls"], SOURCE_FIELDS)
    write_csv(root / "asset_slots.csv", registry["asset_slots"], ASSET_SLOT_FIELDS)
    write_csv(root / "approval_status.csv", registry["approval_status"], APPROVAL_FIELDS)
    write_csv(root / "players.csv", registry["players"], PLAYER_FIELDS)

    logo_rows = build_logo_contact_rows(foundation, registry)
    logo_intake_rows = build_logo_intake_rows(foundation, logo_rows)
    athlete_rows = build_athlete_rows(foundation, registry)
    athlete_intake_rows = build_athlete_intake_rows(foundation, athlete_rows)
    write_team_boards(athlete_rows)

    artifact_root = foundation["artifact_root"]
    sport = foundation["sport_family"]
    logo_csv = artifact_root / f"{sport}_logo_contact_sheet.csv"
    logo_intake = artifact_root / f"{sport}_logo_review_intake.csv"
    logo_md = artifact_root / f"{sport}_logo_contact_sheet.md"
    logo_png = output_path(artifact_root / f"{sport}_logo_contact_sheet.png")
    logo_json = artifact_root / f"{sport}_logo_contact_sheet.json"
    athlete_csv = artifact_root / f"{sport}_athlete_photo_contact_sheet.csv"
    athlete_intake = artifact_root / f"{sport}_athlete_photo_review_intake.csv"
    athlete_index = artifact_root / f"{sport}_athlete_photo_contact_sheet_index.md"
    athlete_json = artifact_root / f"{sport}_athlete_photo_contact_sheet_manifest.json"

    write_csv(logo_csv, logo_rows, LOGO_CONTACT_FIELDS)
    write_csv(logo_intake, logo_intake_rows, list(logo_intake_rows[0].keys()) if logo_intake_rows else LOGO_INTAKE_FIELDS)
    png_path = make_logo_contact_png(logo_rows, logo_png, f"{foundation['league_name']} Logo Review")
    write_text(logo_md, render_logo_markdown(logo_rows, png_path, foundation, generated_at))
    write_json(
        logo_json,
        {
            "version": VERSION,
            "status": "logo_contact_sheet_ready",
            "sport_family": sport,
            "league_id": foundation["league_id"],
            "generated_at_utc": generated_at,
            "rows": len(logo_rows),
            "downloads_performed": False,
            "approvals_applied": False,
            "publish_ready": False,
            "logo_contact_sheet_csv": output_path(logo_csv).as_posix(),
            "logo_review_intake_csv": output_path(logo_intake).as_posix(),
            "logo_contact_sheet_md": output_path(logo_md).as_posix(),
            "logo_contact_sheet_png": png_path,
        },
    )

    write_csv(athlete_csv, athlete_rows, ATHLETE_FIELDS)
    write_csv(athlete_intake, athlete_intake_rows, list(athlete_intake_rows[0].keys()) if athlete_intake_rows else ATHLETE_INTAKE_FIELDS)
    write_text(athlete_index, render_athlete_index(athlete_rows, foundation, generated_at))
    write_json(
        athlete_json,
        {
            "version": VERSION,
            "status": "athlete_candidate_layer_ready",
            "sport_family": sport,
            "league_id": foundation["league_id"],
            "generated_at_utc": generated_at,
            "candidate_rows": len(athlete_rows),
            "team_boards": len({row["team_id"] for row in athlete_rows}),
            "source_review_slot_rows": sum(1 for row in athlete_rows if row["candidate_status"].endswith("_review_slot")),
            "starter_candidate_rows": sum(1 for row in athlete_rows if row["candidate_status"] == "operator_add_candidate"),
            "downloads_performed": False,
            "approvals_applied": False,
            "headshot_files_written": False,
            "approved_markers_created": False,
            "publish_ready": False,
            "athlete_contact_sheet_csv": output_path(athlete_csv).as_posix(),
            "athlete_review_intake_csv": output_path(athlete_intake).as_posix(),
            "athlete_contact_sheet_index": output_path(athlete_index).as_posix(),
        },
    )

    return {
        "sport_family": sport,
        "league_id": foundation["league_id"],
        "league_name": foundation["league_name"],
        "team_rows": len(registry["teams"]),
        "source_rows": len(registry["source_urls"]),
        "logo_rows": len(logo_rows),
        "logo_intake_rows": len(logo_intake_rows),
        "athlete_candidate_rows": len(athlete_rows),
        "athlete_intake_rows": len(athlete_intake_rows),
        "athlete_team_boards": len({row["team_id"] for row in athlete_rows}),
        "foundation_source_urls": output_path(root / "source_urls.csv").as_posix(),
        "team_registry": output_path(root / "teams.csv").as_posix(),
        "asset_slot_registry": output_path(root / "asset_slots.csv").as_posix(),
        "approval_registry": output_path(root / "approval_status.csv").as_posix(),
        "logo_contact_sheet": output_path(logo_csv).as_posix(),
        "logo_review_intake": output_path(logo_intake).as_posix(),
        "athlete_contact_sheet": output_path(athlete_csv).as_posix(),
        "athlete_review_intake": output_path(athlete_intake).as_posix(),
        "athlete_contact_sheet_index": output_path(athlete_index).as_posix(),
        "source_review_helper": "data/asset_registry/hockey_softball_source_review_helper_report.md",
        "workflow_readiness": "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md",
        "asset_review_action_queue": "data/asset_registry/hockey_softball_asset_review_action_queue.md",
        "batch_source_review_helper": "data/asset_registry/hockey_softball_batch_source_review_helper.md",
        "next_operator_action": "Open the source URLs registry, then the logo and athlete contact sheets; record only manual source-review notes in intake CSVs and keep approval state held.",
        "guardrail_note": "review-only; no downloads; no auto-approval; no approval-state change; no headshot or .approved marker writes; no publish-ready movement",
    }


def render_coverage_index(rows: List[Dict[str, str]], generated_at: str) -> str:
    lines = [
        "# Hockey/Softball Foundation Coverage Index",
        "",
        f"- Generated: `{generated_at}`",
        f"- Foundations: `{len(rows)}`",
        f"- Teams: `{sum(int(row['team_rows']) for row in rows)}`",
        f"- Source candidates: `{sum(int(row['source_rows']) for row in rows)}`",
        f"- Logo rows: `{sum(int(row['logo_contact_rows']) for row in rows)}`",
        f"- Athlete candidate rows: `{sum(int(row['athlete_candidate_rows']) for row in rows)}`",
        "- Guardrails: review-only, no paid APIs, no automatic downloads, no auto-approval, no approval-state changes, no headshot writes, no `.approved` markers, no publish-ready movement, no publishing.",
        "",
        "## How To Use",
        "",
        "1. Open the `foundation_source_urls` CSV for the sport and confirm the source candidate list.",
        "2. Open the logo and athlete contact sheets listed for that sport.",
        "3. Fill only the linked human intake CSVs after manual review.",
        "4. Keep approval, render, publish, local-file, `headshot.png`, and `.approved` state held until a separate human-edited intake explicitly supplies evidence.",
        "5. Use the action queue and batch source-review helper for row order after the foundation source list looks sane.",
        "",
        "## Foundations",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['league_name']} ({row['sport_family']})",
                "",
                f"- Source URL registry: `{row['foundation_source_urls']}`",
                f"- Team registry: `{row['team_registry']}`",
                f"- Asset slots: `{row['asset_slot_registry']}`",
                f"- Approval registry: `{row['approval_registry']}`",
                f"- Logo contact sheet: `{row['logo_contact_sheet']}`",
                f"- Logo intake: `{row['logo_review_intake']}`",
                f"- Athlete contact sheet: `{row['athlete_contact_sheet']}`",
                f"- Athlete intake: `{row['athlete_review_intake']}`",
                f"- Athlete index: `{row['athlete_contact_sheet_index']}`",
                f"- Counts: teams `{row['team_rows']}`, source rows `{row['source_rows']}`, logo rows `{row['logo_contact_rows']}`, athlete rows `{row['athlete_candidate_rows']}`, team boards `{row['athlete_team_boards']}`.",
                f"- Next operator action: {row['next_operator_action']}",
                f"- Guardrail note: {row['guardrail_note']}",
                "",
            ]
        )
    return "\n".join(lines)


def coverage_rows_from_summaries(summaries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for summary in summaries:
        row = {
            "sport_family": clean(summary.get("sport_family")),
            "league_id": clean(summary.get("league_id")),
            "league_name": clean(summary.get("league_name")),
            "team_rows": str(summary.get("team_rows", 0)),
            "source_rows": str(summary.get("source_rows", 0)),
            "logo_contact_rows": str(summary.get("logo_rows", 0)),
            "logo_intake_rows": str(summary.get("logo_intake_rows", 0)),
            "athlete_candidate_rows": str(summary.get("athlete_candidate_rows", 0)),
            "athlete_intake_rows": str(summary.get("athlete_intake_rows", 0)),
            "athlete_team_boards": str(summary.get("athlete_team_boards", 0)),
            "foundation_source_urls": clean(summary.get("foundation_source_urls")),
            "team_registry": clean(summary.get("team_registry")),
            "asset_slot_registry": clean(summary.get("asset_slot_registry")),
            "approval_registry": clean(summary.get("approval_registry")),
            "logo_contact_sheet": clean(summary.get("logo_contact_sheet")),
            "logo_review_intake": clean(summary.get("logo_review_intake")),
            "athlete_contact_sheet": clean(summary.get("athlete_contact_sheet")),
            "athlete_review_intake": clean(summary.get("athlete_review_intake")),
            "athlete_contact_sheet_index": clean(summary.get("athlete_contact_sheet_index")),
            "source_review_helper": clean(summary.get("source_review_helper")),
            "workflow_readiness": clean(summary.get("workflow_readiness")),
            "asset_review_action_queue": clean(summary.get("asset_review_action_queue")),
            "batch_source_review_helper": clean(summary.get("batch_source_review_helper")),
            "next_operator_action": clean(summary.get("next_operator_action")),
            "guardrail_note": clean(summary.get("guardrail_note")),
        }
        rows.append(row)
    return rows


def main() -> int:
    generated_at = now_iso()
    summaries = [write_foundation(foundation, generated_at) for foundation in FOUNDATIONS]
    coverage_rows = coverage_rows_from_summaries(summaries)
    report = {
        "version": VERSION,
        "status": "hockey_softball_asset_foundation_ready",
        "generated_at_utc": generated_at,
        "guardrails": {
            "paid_apis": False,
            "automatic_downloads": False,
            "auto_approval": False,
            "headshot_png_writes": False,
            "approved_marker_writes": False,
            "publish_ready_movement": False,
            "publishing": False,
        },
        "foundations": summaries,
        "coverage_index": {
            "status": "hockey_softball_foundation_coverage_index_ready",
            "md": COVERAGE_INDEX_MD.as_posix(),
            "csv": COVERAGE_INDEX_CSV.as_posix(),
            "json": COVERAGE_INDEX_JSON.as_posix(),
            "rows": len(coverage_rows),
            "source_rows": sum(int(row["source_rows"]) for row in coverage_rows),
            "logo_contact_rows": sum(int(row["logo_contact_rows"]) for row in coverage_rows),
            "athlete_candidate_rows": sum(int(row["athlete_candidate_rows"]) for row in coverage_rows),
        },
    }
    coverage_payload = {
        "version": VERSION,
        "status": "hockey_softball_foundation_coverage_index_ready",
        "generated_at_utc": generated_at,
        "guardrails": report["guardrails"],
        "rows": len(coverage_rows),
        "source_rows": sum(int(row["source_rows"]) for row in coverage_rows),
        "logo_contact_rows": sum(int(row["logo_contact_rows"]) for row in coverage_rows),
        "athlete_candidate_rows": sum(int(row["athlete_candidate_rows"]) for row in coverage_rows),
        "foundations": coverage_rows,
    }
    write_csv(COVERAGE_INDEX_CSV, coverage_rows, COVERAGE_INDEX_FIELDS)
    write_json(COVERAGE_INDEX_JSON, coverage_payload)
    write_text(COVERAGE_INDEX_MD, render_coverage_index(coverage_rows, generated_at))
    write_json("data/asset_registry/hockey_softball_asset_foundation_report.json", report)
    write_text(
        "data/asset_registry/hockey_softball_asset_foundation_report.md",
        "\n".join(
            [
                "# Hockey/Softball Asset Foundation Report",
                "",
                f"- Status: `{report['status']}`",
                f"- Generated: `{generated_at}`",
                "- Guardrails: no paid APIs, no automatic downloads, no auto-approval, no headshot writes, no `.approved` markers, no publish-ready movement.",
                "",
                "## Foundations",
                "",
                *[
                    f"- {row['sport_family']} / {row['league_id']}: teams={row['team_rows']}, source_rows={row['source_rows']}, logo_rows={row['logo_rows']}, athlete_candidates={row['athlete_candidate_rows']}, coverage=`{COVERAGE_INDEX_MD.as_posix()}`"
                    for row in summaries
                ],
                "",
                "## Operator Coverage Index",
                "",
                f"- Open first: `{COVERAGE_INDEX_MD.as_posix()}`",
                f"- Source rows: `{report['coverage_index']['source_rows']}`",
                f"- Logo contact rows: `{report['coverage_index']['logo_contact_rows']}`",
                f"- Athlete candidate rows: `{report['coverage_index']['athlete_candidate_rows']}`",
                "",
            ]
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
