from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - reported in manifest
    Image = None
    ImageDraw = None
    ImageFont = None


VERSION = "hsd-womens-soccer-athlete-photo-contact-sheets-v1-review-only"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = Path("data/asset_registry/womens_soccer")
ACTIVE_SCOPES = ["nwsl", "europe_top_flight"]
LEAGUE_OPERATOR_ORDER = {
    "nwsl": 10,
    "wsl_england": 20,
    "liga_f_spain": 30,
    "frauen_bundesliga_germany": 40,
    "serie_a_women_italy": 50,
    "arkema_premiere_ligue_france": 60,
    "premiere_ligue_france": 60,
}
TEAM_SHEET_ROOT = Path("data/asset_registry/womens_soccer/athlete_photo_contact_sheets")
MAX_VISUAL_ROWS_PER_TEAM = 12
FONT_CACHE: Dict[Tuple[int, bool], Any] = {}

OUT_DIR = output_path("data/asset_registry/womens_soccer/athlete_photo_contact_sheets")
OUT_INDEX = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md")
OUT_CSV = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv")
OUT_INTAKE = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv")
OUT_JSON = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json")
CANDIDATES = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_candidates.csv")
OUT_OPERATOR_BOARD_MD = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md")
OUT_OPERATOR_BOARD_CSV = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.csv")
OUT_OPERATOR_BOARD_JSON = output_path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.json")

CANDIDATE_FIELDS = [
    "scope_id",
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
    "image_width",
    "image_height",
    "file_sha256",
    "license_hint",
    "rights_note",
    "attribution_text",
    "identity_evidence_notes",
    "team_context_match",
    "jersey_context_notes",
    "identity_risk_flags",
    "manual_review_status",
    "approval_status",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "notes",
]

CONTACT_FIELDS = [
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "player_id",
    "display_name",
    "candidate_id",
    "candidate_status",
    "registry_status",
    "local_candidate_path",
    "local_candidate_exists",
    "approved_marker_path",
    "approved_marker_exists",
    "current_approval_status",
    "identity_review_status",
    "source_url",
    "source_domain",
    "source_tier",
    "source_kind",
    "source_platform",
    "photo_candidate_url",
    "license_hint",
    "rights_note",
    "identity_evidence_notes",
    "identity_risk_flags",
    "allowed_decisions",
    "human_intake_file",
    "team_contact_sheet_path",
    "team_review_board_path",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]

INTAKE_FIELDS = [
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "player_id",
    "display_name",
    "candidate_id",
    "local_candidate_path",
    "source_url",
    "photo_candidate_url",
    "current_approval_status",
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

OPERATOR_BOARD_FIELDS = [
    "operator_rank",
    "scope_id",
    "league_id",
    "team_id",
    "team_name",
    "candidate_rows",
    "official_roster_candidate_rows",
    "starter_candidate_rows",
    "local_candidate_files_present",
    "source_domains",
    "highest_priority_source_tier",
    "manual_intake_file",
    "team_review_board_path",
    "team_contact_sheet_path",
    "operator_next_step",
    "expansion_phase",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: Any) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", clean(value).lower())).strip("_") or "unknown"


def source_domain(url: str) -> str:
    match = re.match(r"^https?://([^/]+)", clean(url))
    return match.group(1).lower() if match else ""


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def by_key(rows: Iterable[Mapping[str, str]], key: str) -> Dict[str, Mapping[str, str]]:
    return {clean(row.get(key)): row for row in rows if clean(row.get(key))}


def project_path(raw: Any) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_font(size: int, *, bold: bool = False) -> Any:
    cache_key = (size, bold)
    if cache_key in FONT_CACHE:
        return FONT_CACHE[cache_key]
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for raw in candidates:
        path = Path(raw)
        if path.exists():
            try:
                font = ImageFont.truetype(str(path), size)
                FONT_CACHE[cache_key] = font
                return font
            except Exception:
                pass
    font = ImageFont.load_default()
    FONT_CACHE[cache_key] = font
    return font


def team_contact_sheet_path(scope_id: str, team_id: str) -> str:
    return (TEAM_SHEET_ROOT / slug(scope_id) / f"{slug(team_id)}.png").as_posix()


def team_review_board_path(scope_id: str, team_id: str) -> str:
    return (TEAM_SHEET_ROOT / slug(scope_id) / f"{slug(team_id)}.md").as_posix()


def proposed_candidate_path(scope_id: str, league_id: str, team_id: str, player_id: str, candidate_id: str) -> str:
    player_slug = slug(player_id or "operator_fill_required")
    candidate_slug = slug(candidate_id or "candidate_001")
    root = Path("assets/leagues/womens_soccer") / slug(scope_id)
    if slug(league_id) and slug(league_id) != slug(scope_id):
        root /= slug(league_id)
    return (root / "teams" / slug(team_id) / "athletes" / player_slug / "review_candidates" / f"{candidate_slug}.png").as_posix()


def preferred_sources(scope: str) -> Dict[Tuple[str, str], str]:
    output: Dict[Tuple[str, str], str] = {}
    priority = ["roster", "nwsl_roster", "team_site", "players_index", "logo_review_source"]
    for row in read_csv(REGISTRY_ROOT / scope / "source_urls.csv"):
        entity_type = clean(row.get("entity_type"))
        entity_id = clean(row.get("entity_id"))
        source_kind = clean(row.get("source_kind"))
        source_url = clean(row.get("source_url"))
        if not source_url:
            continue
        key = (entity_type, entity_id)
        current_kind = output.get((entity_type, entity_id, "_kind"), "")
        if key not in output or (source_kind in priority and (current_kind not in priority or priority.index(source_kind) < priority.index(current_kind))):
            output[key] = source_url
            output[(entity_type, entity_id, "_kind")] = source_kind
    return output


def team_rows(scope: str) -> List[Dict[str, str]]:
    leagues = by_key(read_csv(REGISTRY_ROOT / scope / "leagues.csv"), "league_id")
    sources = preferred_sources(scope)
    rows: List[Dict[str, str]] = []
    for row in read_csv(REGISTRY_ROOT / scope / "teams.csv"):
        team_id = clean(row.get("team_id"))
        league_id = clean(row.get("league_id"))
        if not team_id or not league_id:
            continue
        league = leagues.get(league_id, {})
        rows.append(
            {
                "scope_id": scope,
                "league_id": league_id,
                "league_name": clean(league.get("league_name")) or league_id,
                "team_id": team_id,
                "team_name": clean(row.get("team_name")) or team_id,
                "team_source_url": clean(row.get("team_site_url")) or sources.get(("team", team_id), ""),
                "roster_source_url": sources.get(("team", team_id), "") or clean(row.get("team_site_url")),
            }
        )
    return sorted(rows, key=lambda item: (item["league_id"], item["team_name"]))


def player_rows(scope: str) -> List[Dict[str, str]]:
    teams = by_key(team_rows(scope), "team_id")
    rows: List[Dict[str, str]] = []
    for row in read_csv(REGISTRY_ROOT / scope / "players.csv"):
        team_id = clean(row.get("team_id"))
        player_id = clean(row.get("player_id"))
        display_name = clean(row.get("display_name"))
        if not team_id or not player_id or not display_name:
            continue
        team = teams.get(team_id, {})
        roster_source_url = clean(row.get("roster_source_url")) or clean(team.get("roster_source_url"))
        rows.append(
            {
                "scope_id": scope,
                "league_id": clean(row.get("league_id")) or clean(team.get("league_id")),
                "team_id": team_id,
                "team_name": clean(team.get("team_name")) or team_id,
                "player_id": player_id,
                "display_name": display_name,
                "provider_player_id": clean(row.get("provider_player_id")),
                "roster_source_url": roster_source_url,
                "status": clean(row.get("status")) or "active_roster_source_candidate",
                "manual_review_status": clean(row.get("manual_review_status")) or "identity_source_review_required",
                "asset_registry_status": clean(row.get("asset_registry_status")) or "candidate_layer_only_no_asset_write",
                "approval_status": clean(row.get("approval_status")) or "not_approved",
                "notes": clean(row.get("notes")),
            }
        )
    return sorted(rows, key=lambda item: (item["league_id"], item["team_name"], item["display_name"]))


def player_candidate_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for scope in ACTIVE_SCOPES:
        for index, player in enumerate(player_rows(scope), start=1):
            source_url = clean(player.get("roster_source_url"))
            player_id = clean(player.get("player_id"))
            candidate_id = f"{player['team_id']}_{slug(player['display_name'])}_official_roster_candidate"
            provider = clean(player.get("provider_player_id"))
            rows.append(
                {
                    "scope_id": player["scope_id"],
                    "league_id": player["league_id"],
                    "team_id": player["team_id"],
                    "team_name": player["team_name"],
                    "player_id": player_id,
                    "display_name": player["display_name"],
                    "candidate_id": candidate_id,
                    "candidate_rank": str(index),
                    "candidate_status": "official_roster_source_candidate",
                    "source_url": source_url,
                    "source_domain": source_domain(source_url),
                    "source_tier": "official_public_roster_metadata",
                    "source_platform": "nwsl_public_roster_api",
                    "source_kind": "roster_or_public_profile_candidate",
                    "candidate_method": "official_roster_metadata_no_image_download",
                    "page_title": f"{player['team_name']} roster",
                    "canonical_url": source_url,
                    "referring_roster_url": source_url,
                    "photo_candidate_url": source_url,
                    "local_candidate_path": proposed_candidate_path(player["scope_id"], player["league_id"], player["team_id"], player_id, candidate_id),
                    "local_candidate_exists": "false",
                    "image_width": "",
                    "image_height": "",
                    "file_sha256": "",
                    "license_hint": "operator_rights_review_required",
                    "rights_note": "review_only_fair_use_tolerant_candidate; roster metadata only; no image downloaded",
                    "attribution_text": "NWSL public roster metadata",
                    "identity_evidence_notes": f"Official roster metadata links {player['display_name']} to {player['team_name']}; provider={provider or 'missing'}; local image still required before approval.",
                    "team_context_match": "official_roster_team_match",
                    "jersey_context_notes": "",
                    "identity_risk_flags": "local_photo_missing_identity_review_required",
                    "manual_review_status": "source_candidate_ready_local_file_missing",
                    "approval_status": "not_approved",
                    "review_only": "true",
                    "publish_ready": "false",
                    "auto_approval": "false",
                    "auto_publish": "false",
                    "move_files": "false",
                    "paid_apis": "false",
                    "asset_downloads": "false",
                    "notes": clean(player.get("notes")) or "Seeded from official public NWSL roster metadata; no photo asset fetched.",
                }
            )
    return rows


def starter_candidate_row(team: Mapping[str, str]) -> Dict[str, str]:
    source_url = clean(team.get("roster_source_url")) or clean(team.get("team_source_url"))
    candidate_id = f"{team['team_id']}_operator_add_candidate"
    return {
        "scope_id": team["scope_id"],
        "league_id": team["league_id"],
        "team_id": team["team_id"],
        "team_name": team["team_name"],
        "player_id": "",
        "display_name": "operator_add_player_candidate",
        "candidate_id": candidate_id,
        "candidate_rank": "999",
        "candidate_status": "operator_add_candidate",
        "source_url": source_url,
        "source_domain": source_domain(source_url),
        "source_tier": "public_or_official_candidate",
        "source_platform": "manual_research",
        "source_kind": "roster_or_public_profile_candidate",
        "candidate_method": "manual_candidate_layer_placeholder",
        "page_title": f"{team['team_name']} roster source review",
        "canonical_url": source_url,
        "referring_roster_url": source_url,
        "photo_candidate_url": "",
        "local_candidate_path": proposed_candidate_path(team["scope_id"], team["league_id"], team["team_id"], "", candidate_id),
        "local_candidate_exists": "false",
        "image_width": "",
        "image_height": "",
        "file_sha256": "",
        "license_hint": "operator_review_required",
        "rights_note": "review_only_fair_use_tolerant_candidate; no renderer approval",
        "attribution_text": "",
        "identity_evidence_notes": "Add exact player name, current team evidence, and source URL before approval.",
        "team_context_match": "operator_fill_required",
        "jersey_context_notes": "",
        "identity_risk_flags": "missing_player_identity_candidate",
        "manual_review_status": "operator_fill_required",
        "approval_status": "not_approved",
        "review_only": "true",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "asset_downloads": "false",
        "notes": "Starter row only; replace with one row per athlete photo candidate.",
    }


def starter_candidate_rows(excluded_team_keys: set[Tuple[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for scope in ACTIVE_SCOPES:
        for team in team_rows(scope):
            key = (clean(team.get("scope_id")), clean(team.get("team_id")))
            if key not in excluded_team_keys:
                rows.append(starter_candidate_row(team))
    return rows


def generated_candidate_rows() -> List[Dict[str, str]]:
    roster_rows = player_candidate_rows()
    roster_team_keys = {(clean(row.get("scope_id")), clean(row.get("team_id"))) for row in roster_rows}
    return roster_rows + starter_candidate_rows(roster_team_keys)


def ensure_candidate_csv() -> List[Dict[str, str]]:
    existing_rows = read_csv(CANDIDATES)
    generated_rows = generated_candidate_rows()
    placeholder_only = bool(existing_rows) and all(
        clean(row.get("candidate_status")) == "operator_add_candidate"
        or clean(row.get("display_name")) == "operator_add_player_candidate"
        for row in existing_rows
    )
    if existing_rows and not generated_rows:
        return existing_rows
    generated_by_id = {clean(row.get("candidate_id")): row for row in generated_rows if clean(row.get("candidate_id"))}
    rows = list(generated_rows)
    if existing_rows and not placeholder_only:
        for row in existing_rows:
            candidate_id = clean(row.get("candidate_id"))
            if candidate_id and candidate_id not in generated_by_id:
                rows.append(row)
    write_csv(CANDIDATES, rows, CANDIDATE_FIELDS)
    return rows


def count_by_field(rows: Iterable[Mapping[str, str]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        key = clean(row.get(field)) or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def source_tier_priority(tier: str) -> int:
    order = {
        "official_public_roster_metadata": 0,
        "official_candidate": 1,
        "public_or_official_candidate": 2,
    }
    return order.get(clean(tier), 9)


def team_operator_priority_key(row: Mapping[str, str]) -> Tuple[int, str, str]:
    league_id = clean(row.get("league_id"))
    return (
        LEAGUE_OPERATOR_ORDER.get(league_id, 100),
        clean(row.get("team_name")).lower(),
        clean(row.get("team_id")),
    )


def operator_next_step(row: Mapping[str, str]) -> str:
    official_rows = as_int(row.get("official_roster_candidate_rows"))
    starter_rows = as_int(row.get("starter_candidate_rows"))
    local_files = as_int(row.get("local_candidate_files_present"))
    if official_rows:
        return "Review NWSL roster-sourced candidate rows first; add local candidate files only after human source and rights review."
    if starter_rows:
        return "Use the team board to add athlete names and source URLs manually; keep rows held until a local file is supplied and reviewed."
    if local_files:
        return "Compare local candidate files to the source rows manually before any review-only renderer trust decision."
    return "Hold this team in the candidate layer until a human adds a source-backed athlete row."


def expansion_phase(row: Mapping[str, str]) -> str:
    if clean(row.get("league_id")) == "nwsl":
        return "phase_1_nwsl_roster_metadata"
    return "phase_2_europe_top_flight_starter"


def as_int(value: Any) -> int:
    try:
        return int(clean(value))
    except Exception:
        return 0


def build_operator_board_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str], List[Mapping[str, str]]] = {}
    for row in rows:
        grouped.setdefault((clean(row.get("scope_id")), clean(row.get("team_id"))), []).append(row)

    summaries: List[Dict[str, str]] = []
    for (scope_id, team_id), team_rows_for_board in grouped.items():
        first = team_rows_for_board[0]
        source_domains = sorted({clean(row.get("source_domain")) for row in team_rows_for_board if clean(row.get("source_domain"))})
        source_tiers = sorted(
            {clean(row.get("source_tier")) for row in team_rows_for_board if clean(row.get("source_tier"))},
            key=source_tier_priority,
        )
        summary = {
            "operator_rank": "",
            "scope_id": scope_id,
            "league_id": clean(first.get("league_id")),
            "team_id": team_id,
            "team_name": clean(first.get("team_name")) or team_id,
            "candidate_rows": str(len(team_rows_for_board)),
            "official_roster_candidate_rows": str(sum(1 for row in team_rows_for_board if clean(row.get("candidate_status")) == "official_roster_source_candidate")),
            "starter_candidate_rows": str(sum(1 for row in team_rows_for_board if clean(row.get("candidate_status")) == "operator_add_candidate")),
            "local_candidate_files_present": str(sum(1 for row in team_rows_for_board if clean(row.get("local_candidate_exists")) == "true")),
            "source_domains": ";".join(source_domains),
            "highest_priority_source_tier": source_tiers[0] if source_tiers else "",
            "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
            "team_review_board_path": clean(first.get("team_review_board_path")),
            "team_contact_sheet_path": clean(first.get("team_contact_sheet_path")),
            "operator_next_step": "",
            "expansion_phase": "",
            "review_only": "true",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "asset_downloads": "false",
        }
        summary["operator_next_step"] = operator_next_step(summary)
        summary["expansion_phase"] = expansion_phase(summary)
        summaries.append(summary)

    summaries.sort(key=team_operator_priority_key)
    for index, row in enumerate(summaries, start=1):
        row["operator_rank"] = str(index)
    return summaries


def render_operator_board(rows: List[Mapping[str, str]], generated_at: str) -> str:
    total_candidates = sum(as_int(row.get("candidate_rows")) for row in rows)
    official_candidates = sum(as_int(row.get("official_roster_candidate_rows")) for row in rows)
    starter_candidates = sum(as_int(row.get("starter_candidate_rows")) for row in rows)
    local_files = sum(as_int(row.get("local_candidate_files_present")) for row in rows)
    league_counts: Dict[str, int] = {}
    for row in rows:
        league = clean(row.get("league_id")) or "unknown"
        league_counts[league] = league_counts.get(league, 0) + as_int(row.get("candidate_rows"))
    lines = [
        "# Women's Soccer Athlete Photo Operator Board",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only operator board for women's soccer athlete source candidates. It prioritizes NWSL roster-metadata rows first and keeps WSL, Liga F, Frauen-Bundesliga, Serie A Women, and Arkema expansion as manual starter rows until a human adds athlete/source evidence.",
        "",
        "No paid APIs, asset downloads, headshot writes, `.approved` marker writes, approval-state changes, publish-ready movement, or publishing are performed by this generator.",
        "",
        "## Summary",
        "",
        f"- Team boards: `{len(rows)}`",
        f"- Candidate rows: `{total_candidates}`",
        f"- Official roster candidate rows: `{official_candidates}`",
        f"- Starter rows needing operator input: `{starter_candidates}`",
        f"- Local candidate files present: `{local_files}`",
        "- Candidate CSV: `data/asset_registry/womens_soccer/womens_soccer_athlete_photo_candidates.csv`",
        "- Human intake CSV: `data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv`",
        "",
        "## League Candidate Counts",
        "",
    ]
    lines.extend(f"- {league}: `{count}`" for league, count in sorted(league_counts.items(), key=lambda item: (LEAGUE_OPERATOR_ORDER.get(item[0], 100), item[0])))
    lines += [
        "",
        "## NWSL First Queue",
        "",
    ]
    for row in rows:
        if clean(row.get("league_id")) != "nwsl":
            continue
        lines.append(
            f"- {row.get('operator_rank')}. {row.get('team_name')} | candidates={row.get('candidate_rows')} | official_roster={row.get('official_roster_candidate_rows')} | local_files={row.get('local_candidate_files_present')} | [board]({row.get('team_review_board_path')})"
        )
    lines += [
        "",
        "## Europe Expansion Queue",
        "",
    ]
    for row in rows:
        if clean(row.get("league_id")) == "nwsl":
            continue
        lines.append(
            f"- {row.get('operator_rank')}. {row.get('team_name')} ({row.get('league_id')}) | starter_rows={row.get('starter_candidate_rows')} | source_domains={row.get('source_domains') or 'operator_fill_required'} | next={row.get('operator_next_step')} | [board]({row.get('team_review_board_path')})"
        )
    return "\n".join(lines) + "\n"


def build_rows() -> List[Dict[str, str]]:
    candidates = ensure_candidate_csv()
    output: List[Dict[str, str]] = []
    for row in candidates:
        local_path = clean(row.get("local_candidate_path"))
        scope_id = clean(row.get("scope_id"))
        team_id = clean(row.get("team_id"))
        marker_path = f"{local_path}.approved" if local_path else ""
        output.append(
            {
                "scope_id": scope_id,
                "league_id": clean(row.get("league_id")),
                "team_id": team_id,
                "team_name": clean(row.get("team_name")) or team_id,
                "player_id": clean(row.get("player_id")),
                "display_name": clean(row.get("display_name")) or "operator_add_player_candidate",
                "candidate_id": clean(row.get("candidate_id")),
                "candidate_status": clean(row.get("candidate_status")) or "operator_add_candidate",
                "registry_status": "candidate_layer_only_no_player_registry_write",
                "local_candidate_path": local_path,
                "local_candidate_exists": str(project_path(local_path).exists()).lower() if local_path else "false",
                "approved_marker_path": marker_path,
                "approved_marker_exists": str(project_path(marker_path).exists()).lower() if marker_path else "false",
                "current_approval_status": clean(row.get("approval_status")) or "not_approved",
                "identity_review_status": clean(row.get("manual_review_status")) or "operator_fill_required",
                "source_url": clean(row.get("source_url")),
                "source_domain": clean(row.get("source_domain")) or source_domain(clean(row.get("source_url"))),
                "source_tier": clean(row.get("source_tier")),
                "source_kind": clean(row.get("source_kind")),
                "source_platform": clean(row.get("source_platform")),
                "photo_candidate_url": clean(row.get("photo_candidate_url")),
                "license_hint": clean(row.get("license_hint")),
                "rights_note": clean(row.get("rights_note")),
                "identity_evidence_notes": clean(row.get("identity_evidence_notes")),
                "identity_risk_flags": clean(row.get("identity_risk_flags")) or "identity_review_required",
                "allowed_decisions": "approve_for_review_only_renderer_use|hold_identity|deny_candidate|revise_source_metadata|request_better_candidate",
                "human_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "team_contact_sheet_path": team_contact_sheet_path(scope_id, team_id),
                "team_review_board_path": team_review_board_path(scope_id, team_id),
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
    return sorted(output, key=lambda item: (item["scope_id"], item["league_id"], item["team_name"], item["display_name"], item["candidate_id"]))


def existing_intake_rows() -> List[Dict[str, str]]:
    return read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv")


def existing_intake_by_candidate(rows: Iterable[Mapping[str, str]] | None = None) -> Dict[str, Mapping[str, str]]:
    return by_key(rows or existing_intake_rows(), "candidate_id")


def extended_fields(base_fields: List[str], rows: Iterable[Mapping[str, str]]) -> List[str]:
    fields = list(base_fields)
    seen = set(fields)
    for row in rows:
        for field in row.keys():
            if field and field not in seen:
                fields.append(field)
                seen.add(field)
    return fields


def intake_rows(rows: Iterable[Mapping[str, str]], existing: Mapping[str, Mapping[str, str]] | None = None) -> List[Dict[str, str]]:
    existing = existing or existing_intake_by_candidate()
    output: List[Dict[str, str]] = []
    for row in rows:
        prior = existing.get(clean(row.get("candidate_id")), {})
        merged = {field: clean(value) for field, value in prior.items() if field not in INTAKE_FIELDS}
        merged.update(
            {
                "scope_id": clean(row.get("scope_id")),
                "league_id": clean(row.get("league_id")),
                "team_id": clean(row.get("team_id")),
                "team_name": clean(row.get("team_name")),
                "player_id": clean(row.get("player_id")),
                "display_name": clean(row.get("display_name")),
                "candidate_id": clean(row.get("candidate_id")),
                "local_candidate_path": clean(row.get("local_candidate_path")),
                "source_url": clean(row.get("source_url")),
                "photo_candidate_url": clean(row.get("photo_candidate_url")),
                "current_approval_status": clean(row.get("current_approval_status")),
                "identity_review_status": clean(row.get("identity_review_status")),
                "allowed_decisions": clean(row.get("allowed_decisions")),
                "operator_decision": clean(prior.get("operator_decision")) or "operator_fill_required",
                "identity_verified": clean(prior.get("identity_verified")) or "operator_fill_required",
                "source_reviewed": clean(prior.get("source_reviewed")) or "operator_fill_required",
                "local_file_reviewed": clean(prior.get("local_file_reviewed")) or "operator_fill_required",
                "source_allowed_for_review_only": clean(prior.get("source_allowed_for_review_only")) or "operator_fill_required",
                "rights_reviewed": clean(prior.get("rights_reviewed")) or "operator_fill_required",
                "source_url_to_record": clean(prior.get("source_url_to_record")),
                "registry_action": clean(prior.get("registry_action")) or "candidate_layer_only_no_registry_state_change",
                "operator_notes": clean(prior.get("operator_notes")),
                "reviewed_by": clean(prior.get("reviewed_by")),
                "reviewed_at_local": clean(prior.get("reviewed_at_local")),
                "approval_scope": "review_only_renderer_womens_soccer_athlete_photo_trust_manual_intake",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        )
        output.append(merged)
    return output


def text_width(draw: Any, text: str, font: Any) -> int:
    if hasattr(draw, "textbbox"):
        box = draw.textbbox((0, 0), text, font=font)
        return int(box[2] - box[0])
    return int(draw.textlength(text, font=font))


def ellipsize(draw: Any, text: str, font: Any, max_width: int) -> str:
    value = clean(text)
    if not value:
        return ""
    if text_width(draw, value, font) <= max_width:
        return value
    suffix = "..."
    low, high = 0, len(value)
    best = ""
    while low <= high:
        mid = (low + high) // 2
        candidate = value[:mid].rstrip()
        if text_width(draw, candidate + suffix, font) <= max_width:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return (best + suffix) if best else suffix


def draw_candidate_card(sheet: Any, draw: Any, row: Mapping[str, str], x: int, y: int, card_w: int, card_h: int) -> None:
    font_name = load_font(20, bold=True)
    font_small = load_font(14)
    font_tiny = load_font(12)
    draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=10, fill=(255, 255, 255), outline=(212, 220, 228), width=2)
    local_path = project_path(row.get("local_candidate_path"))
    if local_path.exists() and Image is not None:
        try:
            image = Image.open(local_path).convert("RGBA")
            scale = min(116 / max(1, image.width), 96 / max(1, image.height))
            resized = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (116, 96), (255, 255, 255, 0))
            canvas.alpha_composite(resized, ((116 - resized.width) // 2, (96 - resized.height) // 2))
            sheet.paste(canvas, (x + 16, y + 42), canvas)
        except Exception:
            draw.rectangle((x + 16, y + 42, x + 132, y + 138), fill=(236, 240, 244), outline=(180, 188, 196))
            draw.text((x + 34, y + 82), "render failed", fill=(130, 38, 38), font=font_tiny)
    else:
        draw.rectangle((x + 16, y + 42, x + 132, y + 138), fill=(236, 240, 244), outline=(180, 188, 196))
        draw.text((x + 30, y + 78), "missing local", fill=(130, 38, 38), font=font_tiny)
        draw.text((x + 30, y + 96), "candidate", fill=(130, 38, 38), font=font_tiny)

    text_x = x + 150
    text_w = card_w - 166
    draw.text((x + 16, y + 14), ellipsize(draw, clean(row.get("display_name")), font_name, card_w - 32), fill=(12, 20, 28), font=font_name)
    draw.text((text_x, y + 46), ellipsize(draw, f"Status: {clean(row.get('identity_review_status'))}", font_small, text_w), fill=(154, 99, 0), font=font_small)
    draw.text((text_x, y + 68), ellipsize(draw, f"Risk: {clean(row.get('identity_risk_flags'))}", font_tiny, text_w), fill=(74, 83, 94), font=font_tiny)
    draw.text((text_x, y + 88), ellipsize(draw, f"Source: {clean(row.get('source_url'))}", font_tiny, text_w), fill=(74, 83, 94), font=font_tiny)
    draw.text((text_x, y + 108), ellipsize(draw, f"Photo: {clean(row.get('photo_candidate_url')) or 'operator fill required'}", font_tiny, text_w), fill=(74, 83, 94), font=font_tiny)
    draw.text((x + 16, y + 154), ellipsize(draw, f"Local candidate: {clean(row.get('local_candidate_path'))}", font_tiny, card_w - 32), fill=(74, 83, 94), font=font_tiny)
    draw.text((x + 16, y + 174), ellipsize(draw, "No downloads, no approval markers, no headshot.png writes.", font_tiny, card_w - 32), fill=(74, 83, 94), font=font_tiny)


def make_team_contact_sheet(scope_id: str, team_id: str, team_rows: List[Mapping[str, str]]) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    out_path = output_path(team_contact_sheet_path(scope_id, team_id))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if Image is None or ImageDraw is None:
        warnings.append(f"{team_id}:pillow_unavailable_contact_sheet_not_created")
        return out_path.as_posix(), warnings
    preview_rows = list(team_rows[:MAX_VISUAL_ROWS_PER_TEAM])
    hidden_rows = max(0, len(team_rows) - len(preview_rows))
    if hidden_rows:
        warnings.append(f"{team_id}:visual_preview_limited_to_{len(preview_rows)}_of_{len(team_rows)}_rows")
    cols = 2
    card_w, card_h = 650, 210
    margin = 28
    header_h = 116
    row_count = max(1, (len(preview_rows) + cols - 1) // cols)
    width = margin * 2 + cols * card_w + 18
    height = margin * 2 + header_h + row_count * (card_h + 18)
    image = Image.new("RGB", (width, height), (246, 248, 250))
    draw = ImageDraw.Draw(image)
    font_title = load_font(32, bold=True)
    font_body = load_font(16)
    team_name = clean(team_rows[0].get("team_name")) if team_rows else team_id
    draw.text((margin, 20), f"{team_name} athlete photo candidates", fill=(12, 20, 28), font=font_title)
    draw.text((margin, 58), "Review-only candidate board. Add public/fair-use-tolerant source leads in the CSV; no photo downloads here.", fill=(74, 83, 94), font=font_body)
    if hidden_rows:
        draw.text((margin, 82), f"Visual preview shows first {len(preview_rows)} of {len(team_rows)} rows; Markdown and CSV list every candidate.", fill=(154, 99, 0), font=font_body)
    for index, row in enumerate(preview_rows):
        col = index % cols
        row_i = index // cols
        x = margin + col * (card_w + 18)
        y = margin + header_h + row_i * (card_h + 18)
        draw_candidate_card(image, draw, row, x, y, card_w, card_h)
    image.save(out_path)
    return out_path.as_posix(), warnings


def render_team_board(team_rows: List[Mapping[str, str]], sheet_path: str, generated_at: str) -> str:
    team_name = clean(team_rows[0].get("team_name")) if team_rows else "Unknown team"
    lines = [
        f"# {team_name} Women's Soccer Athlete Photo Candidates",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only board. Candidate URLs may come from official, public, or fair-use-tolerant sources, but this packet does not download athlete photos, approve identities, write `headshot.png`, create `.approved` markers, move files, publish, or create a publish-ready lane.",
        "",
        f"![{team_name} athlete photo candidates]({Path(sheet_path).name})",
        "",
        "## Candidate Rows",
        "",
    ]
    if len(team_rows) > MAX_VISUAL_ROWS_PER_TEAM:
        lines += [
            f"Visual PNG preview shows the first `{MAX_VISUAL_ROWS_PER_TEAM}` rows only so the packet stays fast. This Markdown board and the CSV include all `{len(team_rows)}` candidates.",
            "",
        ]
    for row in team_rows:
        lines.append(
            f"- {row.get('display_name')} | candidate={row.get('candidate_id')} | local_exists={row.get('local_candidate_exists')} | "
            f"source={row.get('source_url') or 'operator_fill_required'} | photo={row.get('photo_candidate_url') or 'operator_fill_required'} | "
            f"risk={row.get('identity_risk_flags')}"
        )
    return "\n".join(lines) + "\n"


def render_index(rows: List[Mapping[str, str]], team_outputs: Mapping[str, Mapping[str, str]], generated_at: str) -> str:
    local_count = sum(1 for row in rows if clean(row.get("local_candidate_exists")) == "true")
    starter_count = sum(1 for row in rows if clean(row.get("candidate_status")) == "operator_add_candidate")
    scope_counts = count_by_field(rows, "scope_id")
    league_counts = count_by_field(rows, "league_id")
    lines = [
        "# Women's Soccer Athlete Photo Contact Sheets",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Review-only candidate layer for women's soccer athlete photos. It keeps the NWSL roster candidate layer and extends the same CSV/intake/team-board workflow to WSL, Liga F, Frauen-Bundesliga, Serie A Women, and Arkema Premiere Ligue starter rows.",
        "No downloads or approvals are performed by this generator.",
        "",
        "## Summary",
        "",
        f"- Candidate rows: `{len(rows)}`",
        f"- Team boards: `{len(team_outputs)}`",
        f"- Starter rows needing operator athlete names: `{starter_count}`",
        f"- Local candidate files present: `{local_count}`",
        "- Candidate CSV: `data/asset_registry/womens_soccer/womens_soccer_athlete_photo_candidates.csv`",
        "- Human intake CSV: `data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv`",
        "- Allowed decisions: `approve_for_review_only_renderer_use|hold_identity|deny_candidate|revise_source_metadata|request_better_candidate`",
        "- Guardrails: review_only=true; publish_ready=false; auto_approval=false; auto_publish=false; move_files=false; paid_apis=false; asset_downloads=false",
        "",
        "## Scope Counts",
        "",
    ]
    lines.extend(f"- {scope}: `{count}`" for scope, count in scope_counts.items())
    lines.extend(
        [
            "",
            "## League Counts",
            "",
        ]
    )
    lines.extend(f"- {league}: `{count}`" for league, count in league_counts.items())
    lines.extend(
        [
            "",
            "## Boards",
            "",
        ]
    )
    for key in sorted(team_outputs):
        info = team_outputs[key]
        lines.append(f"- {info.get('team_name')} | rows={info.get('rows')} | [board]({Path(info.get('board_path', '')).as_posix()}) | [contact sheet]({Path(info.get('sheet_path', '')).as_posix()})")
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_iso()
    rows = build_rows()
    prior_intake_rows = existing_intake_rows()
    existing = existing_intake_by_candidate(prior_intake_rows)
    decisions = intake_rows(rows, existing)
    team_outputs: Dict[str, Dict[str, str]] = {}
    warnings: List[str] = []
    grouped: Dict[Tuple[str, str], List[Mapping[str, str]]] = {}
    for row in rows:
        grouped.setdefault((clean(row.get("scope_id")), clean(row.get("team_id"))), []).append(row)
    for (scope_id, team_id), team_rows_for_board in sorted(grouped.items()):
        sheet_path, sheet_warnings = make_team_contact_sheet(scope_id, team_id, team_rows_for_board)
        warnings.extend(sheet_warnings)
        board_path = output_path(team_review_board_path(scope_id, team_id))
        write_text(board_path, render_team_board(team_rows_for_board, sheet_path, generated_at))
        team_outputs[f"{scope_id}:{team_id}"] = {
            "scope_id": scope_id,
            "team_id": team_id,
            "team_name": clean(team_rows_for_board[0].get("team_name")),
            "rows": str(len(team_rows_for_board)),
            "sheet_path": sheet_path,
            "board_path": board_path.as_posix(),
        }
    operator_board_rows = build_operator_board_rows(rows)
    write_csv(OUT_CSV, rows, CONTACT_FIELDS)
    write_csv(OUT_INTAKE, decisions, extended_fields(INTAKE_FIELDS, prior_intake_rows))
    write_csv(OUT_OPERATOR_BOARD_CSV, operator_board_rows, OPERATOR_BOARD_FIELDS)
    write_text(OUT_OPERATOR_BOARD_MD, render_operator_board(operator_board_rows, generated_at))
    write_text(OUT_INDEX, render_index(rows, team_outputs, generated_at))
    operator_board_manifest = {
        "version": VERSION,
        "status": "operator_board_ready",
        "generated_at_utc": generated_at,
        "operator_board_rows": len(operator_board_rows),
        "candidate_rows": len(rows),
        "official_roster_candidate_rows": sum(as_int(row.get("official_roster_candidate_rows")) for row in operator_board_rows),
        "starter_candidate_rows": sum(as_int(row.get("starter_candidate_rows")) for row in operator_board_rows),
        "local_candidate_files_present": sum(as_int(row.get("local_candidate_files_present")) for row in operator_board_rows),
        "operator_board_md": OUT_OPERATOR_BOARD_MD.as_posix(),
        "operator_board_csv": OUT_OPERATOR_BOARD_CSV.as_posix(),
        "candidate_csv": CANDIDATES.as_posix(),
        "intake_csv": OUT_INTAKE.as_posix(),
        "review_only": True,
        "downloads_performed": False,
        "approvals_applied": False,
        "headshot_files_written": False,
        "approved_markers_created": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
    }
    write_json(OUT_OPERATOR_BOARD_JSON, operator_board_manifest)
    manifest = {
        "version": VERSION,
        "status": "contact_sheets_ready",
        "generated_at_utc": generated_at,
        "candidate_rows": len(rows),
        "team_boards": len(team_outputs),
        "candidate_csv": CANDIDATES.as_posix(),
        "contact_sheet_csv": OUT_CSV.as_posix(),
        "intake_csv": OUT_INTAKE.as_posix(),
        "operator_board_md": OUT_OPERATOR_BOARD_MD.as_posix(),
        "operator_board_csv": OUT_OPERATOR_BOARD_CSV.as_posix(),
        "operator_board_json": OUT_OPERATOR_BOARD_JSON.as_posix(),
        "index": OUT_INDEX.as_posix(),
        "scope_counts": count_by_field(rows, "scope_id"),
        "league_counts": count_by_field(rows, "league_id"),
        "starter_candidate_rows": sum(1 for row in rows if clean(row.get("candidate_status")) == "operator_add_candidate"),
        "official_roster_candidate_rows": sum(1 for row in rows if clean(row.get("candidate_status")) == "official_roster_source_candidate"),
        "local_candidate_files_present": sum(1 for row in rows if clean(row.get("local_candidate_exists")) == "true"),
        "operator_board_rows": len(operator_board_rows),
        "warnings": warnings,
        "review_only": True,
        "downloads_performed": False,
        "approvals_applied": False,
        "headshot_files_written": False,
        "approved_markers_created": False,
        "publish_ready": False,
    }
    write_json(OUT_JSON, manifest)
    print(json.dumps({"version": VERSION, "status": manifest["status"], "candidate_rows": len(rows), "team_boards": len(team_outputs), "operator_board": OUT_OPERATOR_BOARD_MD.as_posix(), "index": OUT_INDEX.as_posix(), "intake": OUT_INTAKE.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
