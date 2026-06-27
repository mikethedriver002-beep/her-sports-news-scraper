from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

VERSION = "v1.0-womens-soccer-asset-registry-review-only"
REGISTRY = Path("data/asset_registry/womens_soccer/nwsl")
EUROPE_REGISTRY = Path("data/asset_registry/womens_soccer/europe_top_flight")
OUT_JSON = REGISTRY / "review_scaffold_report.json"
OUT_MD = REGISTRY / "review_scaffold_report.md"

EXPECTED_FILES = {
    "leagues.csv": [
        "league_id",
        "league_name",
        "official_url",
        "teams_url",
        "paid_source",
        "auto_download_allowed",
        "render_enabled",
    ],
    "teams.csv": [
        "team_id",
        "league_id",
        "team_name",
        "team_site_url",
        "manual_review_status",
        "render_enabled",
    ],
    "players.csv": [
        "player_id",
        "league_id",
        "team_id",
        "display_name",
        "provider_player_id",
        "roster_source_url",
        "approval_status",
    ],
    "source_urls.csv": [
        "entity_type",
        "entity_id",
        "source_kind",
        "source_url",
        "source_domain",
        "paid_source",
        "download_allowed",
        "approval_status",
    ],
    "provider_ids.csv": [
        "entity_type",
        "entity_id",
        "provider",
        "provider_id",
        "source_url",
        "manual_review_status",
        "approval_status",
    ],
    "asset_slots.csv": [
        "entity_type",
        "entity_id",
        "asset_slot",
        "target_path",
        "file_exists",
        "approval_status",
        "render_enabled",
        "auto_download_allowed",
        "publish_ready",
    ],
    "approval_status.csv": [
        "entity_type",
        "entity_id",
        "approval_scope",
        "approval_status",
        "auto_approval_allowed",
        "render_enabled",
        "publish_ready",
    ],
}

REQUIRED_NWSL_TEAMS = {
    "angel_city_fc",
    "bay_fc",
    "boston_legacy_fc",
    "chicago_stars_fc",
    "denver_summit_fc",
    "houston_dash",
    "kansas_city_current",
    "gotham_fc",
    "north_carolina_courage",
    "orlando_pride",
    "portland_thorns_fc",
    "racing_louisville_fc",
    "san_diego_wave_fc",
    "seattle_reign",
    "utah_royals_fc",
    "washington_spirit",
}

FALSE_ONLY_FIELDS = {
    "paid_source",
    "download_allowed",
    "auto_download_allowed",
    "render_enabled",
    "publish_ready",
    "auto_approval_allowed",
}

NOT_APPROVED_FIELDS = {"approval_status"}

REQUIRED_LEAGUE_SOURCE_KINDS = {
    "league_about",
    "teams_index",
    "players_index",
    "schedule_regular_season",
    "standings_index",
    "team_stats_index",
    "player_stats_index",
}

REQUIRED_TEAM_SOURCE_KINDS = {
    "team_site",
    "nwsl_team_detail",
    "nwsl_roster",
    "nwsl_schedule",
    "logo_review_source",
}

REQUIRED_TEAM_APPROVAL_SCOPES = {
    "team_identity",
    "team_logo",
    "team_roster_source",
}

REQUIRED_EUROPE_TOP_FLIGHT_LEAGUES = {
    "wsl_england",
    "liga_f_spain",
    "frauen_bundesliga_germany",
    "premiere_ligue_france",
    "serie_a_women_italy",
}

REQUIRED_WSL_TEAMS = {
    "arsenal_women",
    "aston_villa_women",
    "brighton_hove_albion_women",
    "chelsea_women",
    "everton_women",
    "leicester_city_women",
    "liverpool_women",
    "london_city_lionesses",
    "manchester_city_women",
    "manchester_united_women",
    "tottenham_hotspur_women",
    "west_ham_united_women",
}

REQUIRED_LIGA_F_TEAMS = {
    "alhama_cf_elpozo",
    "athletic_club",
    "atletico_de_madrid",
    "costa_adeje_tenerife",
    "deportivo_abanca",
    "dux_logrono",
    "fc_badalona_women",
    "fc_barcelona",
    "granada_cf",
    "levante_ud",
    "madrid_cff",
    "rcd_espanyol_de_barcelona",
    "real_madrid_cf",
    "real_sociedad",
    "sd_eibar",
    "sevilla_fc",
}

REQUIRED_FRAUEN_BUNDESLIGA_TEAMS = {
    "bayer_04_leverkusen_women",
    "eintracht_frankfurt_women",
    "fc_bayern_munich_women",
    "fc_carl_zeiss_jena_women",
    "hamburger_sv_women",
    "rb_leipzig_women",
    "sc_freiburg_women",
    "sgs_essen",
    "sv_werder_bremen_women",
    "tsg_hoffenheim_women",
    "union_berlin_women",
    "vfl_wolfsburg_women",
    "1_fc_koln_women",
    "1_fc_nurnberg_women",
}

REQUIRED_SERIE_A_WOMEN_TEAMS = {
    "ac_milan_women",
    "as_roma_women",
    "como_women",
    "fc_internazionale_women",
    "fiorentina_women",
    "genoa_women",
    "juventus_women",
    "lazio_women",
    "napoli_femminile",
    "parma_women",
    "sassuolo_women",
    "ternana_women",
}


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def header(path: Path) -> List[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def row_identity(file_name: str, index: int, row: Dict[str, str]) -> str:
    entity_type = clean(row.get("entity_type"))
    entity_id = clean(row.get("entity_id") or row.get("team_id") or row.get("league_id") or row.get("player_id"))
    suffix = f":{entity_type}:{entity_id}" if entity_type or entity_id else f":row_{index + 1}"
    return f"{file_name}{suffix}"


def values(rows_by_file: Dict[str, List[Dict[str, str]]], file_name: str, field: str) -> Iterable[str]:
    for row in rows_by_file.get(file_name, []):
        yield clean(row.get(field))


def evaluate(root: Path) -> Dict[str, Any]:
    base = root / REGISTRY
    europe_base = root / EUROPE_REGISTRY
    blockers: List[str] = []
    warnings: List[str] = []
    rows_by_file: Dict[str, List[Dict[str, str]]] = {}
    headers_by_file: Dict[str, List[str]] = {}
    europe_rows_by_file: Dict[str, List[Dict[str, str]]] = {}

    for file_name, required_fields in EXPECTED_FILES.items():
        path = base / file_name
        if not path.exists():
            blockers.append(f"missing_registry_file:{file_name}")
            continue
        fields = header(path)
        headers_by_file[file_name] = fields
        rows = read_rows(path)
        rows_by_file[file_name] = rows
        missing = sorted(set(required_fields) - set(fields))
        for field in missing:
            blockers.append(f"missing_required_field:{file_name}:{field}")

    teams = set(values(rows_by_file, "teams.csv", "team_id"))
    missing_teams = sorted(REQUIRED_NWSL_TEAMS - teams)
    extra_teams = sorted(teams - REQUIRED_NWSL_TEAMS)
    for team_id in missing_teams:
        blockers.append(f"missing_required_nwsl_team:{team_id}")
    for team_id in extra_teams:
        warnings.append(f"extra_team_requires_manual_review:{team_id}")

    for file_name, rows in rows_by_file.items():
        for index, row in enumerate(rows):
            ident = row_identity(file_name, index, row)
            for field in FALSE_ONLY_FIELDS & set(row):
                value = clean(row.get(field)).lower()
                if value and value != "false":
                    blockers.append(f"unsafe_truthy_field:{ident}:{field}={value}")
            for field in NOT_APPROVED_FIELDS & set(row):
                value = clean(row.get(field)).lower()
                if value in {"approved", "true", "auto_approved", "render_approved"}:
                    blockers.append(f"approval_not_review_only:{ident}:{field}={value}")
            url_fields = [
                field
                for field in row
                if field.endswith("_url")
                or field
                in {
                    "source_url",
                    "official_url",
                    "teams_url",
                    "players_url",
                    "team_site_url",
                    "roster_source_url",
                }
            ]
            for url_field in url_fields:
                if url_field not in row:
                    continue
                value = clean(row.get(url_field))
                if value and not value.startswith("https://"):
                    blockers.append(f"non_https_source:{ident}:{url_field}")

    for file_name, required_fields in EXPECTED_FILES.items():
        path = europe_base / file_name
        if not path.exists():
            blockers.append(f"missing_europe_registry_file:{file_name}")
            continue
        fields = header(path)
        rows = read_rows(path)
        europe_rows_by_file[file_name] = rows
        missing = sorted(set(required_fields) - set(fields))
        for field in missing:
            blockers.append(f"missing_required_europe_field:{file_name}:{field}")
        for index, row in enumerate(rows):
            ident = f"europe_top_flight:{row_identity(file_name, index, row)}"
            for field in FALSE_ONLY_FIELDS & set(row):
                value = clean(row.get(field)).lower()
                if value and value != "false":
                    blockers.append(f"unsafe_truthy_field:{ident}:{field}={value}")
            for field in NOT_APPROVED_FIELDS & set(row):
                value = clean(row.get(field)).lower()
                if value in {"approved", "true", "auto_approved", "render_approved"}:
                    blockers.append(f"approval_not_review_only:{ident}:{field}={value}")
            url_fields = [
                field
                for field in row
                if field.endswith("_url")
                or field
                in {
                    "source_url",
                    "official_url",
                    "teams_url",
                    "players_url",
                    "team_site_url",
                    "roster_source_url",
                    "league_team_url",
                    "roster_url",
                    "schedule_url",
                    "logo_review_source_url",
                }
            ]
            for url_field in url_fields:
                value = clean(row.get(url_field))
                if value and not value.startswith("https://"):
                    blockers.append(f"non_https_source:{ident}:{url_field}")

    europe_leagues = set(values(europe_rows_by_file, "leagues.csv", "league_id"))
    for league_id in sorted(REQUIRED_EUROPE_TOP_FLIGHT_LEAGUES - europe_leagues):
        blockers.append(f"missing_required_europe_top_flight_league:{league_id}")

    europe_teams = set(values(europe_rows_by_file, "teams.csv", "team_id"))
    for team_id in sorted(REQUIRED_WSL_TEAMS - europe_teams):
        blockers.append(f"missing_required_wsl_team:{team_id}")
    for team_id in sorted(REQUIRED_LIGA_F_TEAMS - europe_teams):
        blockers.append(f"missing_required_liga_f_team:{team_id}")
    for team_id in sorted(REQUIRED_FRAUEN_BUNDESLIGA_TEAMS - europe_teams):
        blockers.append(f"missing_required_frauen_bundesliga_team:{team_id}")
    for team_id in sorted(REQUIRED_SERIE_A_WOMEN_TEAMS - europe_teams):
        blockers.append(f"missing_required_serie_a_women_team:{team_id}")

    europe_league_mark_rows = {
        clean(row.get("entity_id"))
        for row in europe_rows_by_file.get("asset_slots.csv", [])
        if clean(row.get("entity_type")) == "league" and clean(row.get("asset_slot")) == "league_mark"
    }
    for league_id in sorted(REQUIRED_EUROPE_TOP_FLIGHT_LEAGUES - europe_league_mark_rows):
        blockers.append(f"missing_europe_league_mark_slot:{league_id}")

    europe_team_logo_rows = {
        clean(row.get("entity_id"))
        for row in europe_rows_by_file.get("asset_slots.csv", [])
        if clean(row.get("entity_type")) == "team" and clean(row.get("asset_slot")) == "primary_logo"
    }
    for team_id in sorted(REQUIRED_WSL_TEAMS - europe_team_logo_rows):
        blockers.append(f"missing_wsl_team_logo_slot:{team_id}")
    for team_id in sorted(REQUIRED_LIGA_F_TEAMS - europe_team_logo_rows):
        blockers.append(f"missing_liga_f_team_logo_slot:{team_id}")
    for team_id in sorted(REQUIRED_FRAUEN_BUNDESLIGA_TEAMS - europe_team_logo_rows):
        blockers.append(f"missing_frauen_bundesliga_team_logo_slot:{team_id}")
    for team_id in sorted(REQUIRED_SERIE_A_WOMEN_TEAMS - europe_team_logo_rows):
        blockers.append(f"missing_serie_a_women_team_logo_slot:{team_id}")

    team_asset_rows = {
        clean(row.get("entity_id"))
        for row in rows_by_file.get("asset_slots.csv", [])
        if clean(row.get("entity_type")) == "team" and clean(row.get("asset_slot")) == "primary_logo"
    }
    for team_id in sorted(REQUIRED_NWSL_TEAMS - team_asset_rows):
        blockers.append(f"missing_primary_logo_slot:{team_id}")

    provider_team_rows = {
        clean(row.get("entity_id"))
        for row in rows_by_file.get("provider_ids.csv", [])
        if clean(row.get("entity_type")) == "team" and clean(row.get("provider")) == "hsd_manual_registry"
    }
    for team_id in sorted(REQUIRED_NWSL_TEAMS - provider_team_rows):
        blockers.append(f"missing_manual_provider_id:{team_id}")

    nwslsoccer_uuid_rows = {
        clean(row.get("entity_id")): clean(row.get("provider_id"))
        for row in rows_by_file.get("provider_ids.csv", [])
        if clean(row.get("entity_type")) == "team" and clean(row.get("provider")) == "nwslsoccer_team_uuid"
    }
    for team_id in sorted(REQUIRED_NWSL_TEAMS - set(nwslsoccer_uuid_rows)):
        blockers.append(f"missing_nwslsoccer_team_uuid:{team_id}")
    for team_id, provider_id in sorted(nwslsoccer_uuid_rows.items()):
        if team_id in REQUIRED_NWSL_TEAMS and not provider_id:
            blockers.append(f"blank_nwslsoccer_team_uuid:{team_id}")

    league_source_kinds = {
        clean(row.get("source_kind"))
        for row in rows_by_file.get("source_urls.csv", [])
        if clean(row.get("entity_type")) == "league" and clean(row.get("entity_id")) == "nwsl"
    }
    for source_kind in sorted(REQUIRED_LEAGUE_SOURCE_KINDS - league_source_kinds):
        blockers.append(f"missing_nwsl_league_source:{source_kind}")

    team_source_map: Dict[str, Set[str]] = {team_id: set() for team_id in REQUIRED_NWSL_TEAMS}
    for row in rows_by_file.get("source_urls.csv", []):
        if clean(row.get("entity_type")) != "team":
            continue
        team_id = clean(row.get("entity_id"))
        if team_id in team_source_map:
            team_source_map[team_id].add(clean(row.get("source_kind")))
    for team_id, source_kinds in sorted(team_source_map.items()):
        for source_kind in sorted(REQUIRED_TEAM_SOURCE_KINDS - source_kinds):
            blockers.append(f"missing_team_source:{team_id}:{source_kind}")

    team_approval_scope_map: Dict[str, Set[str]] = {team_id: set() for team_id in REQUIRED_NWSL_TEAMS}
    for row in rows_by_file.get("approval_status.csv", []):
        if clean(row.get("entity_type")) != "team":
            continue
        team_id = clean(row.get("entity_id"))
        if team_id in team_approval_scope_map:
            team_approval_scope_map[team_id].add(clean(row.get("approval_scope")))
    for team_id, scopes in sorted(team_approval_scope_map.items()):
        for scope in sorted(REQUIRED_TEAM_APPROVAL_SCOPES - scopes):
            blockers.append(f"missing_team_review_scope:{team_id}:{scope}")

    player_count = len(rows_by_file.get("players.csv", []))
    if player_count == 0:
        warnings.append("players_csv_header_only_manual_intake")
    europe_player_count = len(europe_rows_by_file.get("players.csv", []))
    if europe_player_count == 0:
        warnings.append("europe_players_csv_header_only_manual_intake")
    warnings.append("remaining_europe_team_rows_require_manual_expansion")

    status = "passed_womens_soccer_review_scaffold" if not blockers else "blocked_womens_soccer_review_scaffold"
    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "registry_path": REGISTRY.as_posix(),
        "expected_file_count": len(EXPECTED_FILES),
        "present_file_count": sum(1 for file_name in EXPECTED_FILES if (base / file_name).exists()),
        "required_team_count": len(REQUIRED_NWSL_TEAMS),
        "team_count": len(teams),
        "player_count": player_count,
        "europe_top_flight_required_league_count": len(REQUIRED_EUROPE_TOP_FLIGHT_LEAGUES),
        "europe_top_flight_league_count": len(europe_leagues),
        "europe_top_flight_required_pilot_team_count": len(REQUIRED_WSL_TEAMS),
        "europe_top_flight_required_wsl_team_count": len(REQUIRED_WSL_TEAMS),
        "europe_top_flight_pilot_team_count": len(europe_teams),
        "europe_top_flight_wsl_team_count": len(europe_teams & REQUIRED_WSL_TEAMS),
        "europe_top_flight_required_liga_f_team_count": len(REQUIRED_LIGA_F_TEAMS),
        "europe_top_flight_liga_f_team_count": len(europe_teams & REQUIRED_LIGA_F_TEAMS),
        "europe_top_flight_required_frauen_bundesliga_team_count": len(REQUIRED_FRAUEN_BUNDESLIGA_TEAMS),
        "europe_top_flight_frauen_bundesliga_team_count": len(europe_teams & REQUIRED_FRAUEN_BUNDESLIGA_TEAMS),
        "europe_top_flight_required_serie_a_women_team_count": len(REQUIRED_SERIE_A_WOMEN_TEAMS),
        "europe_top_flight_serie_a_women_team_count": len(europe_teams & REQUIRED_SERIE_A_WOMEN_TEAMS),
        "europe_top_flight_player_count": europe_player_count,
        "europe_top_flight_source_url_count": len(europe_rows_by_file.get("source_urls.csv", [])),
        "europe_top_flight_asset_slot_count": len(europe_rows_by_file.get("asset_slots.csv", [])),
        "source_url_count": len(rows_by_file.get("source_urls.csv", [])),
        "asset_slot_count": len(rows_by_file.get("asset_slots.csv", [])),
        "league_source_kind_count": len(league_source_kinds),
        "required_league_source_kind_count": len(REQUIRED_LEAGUE_SOURCE_KINDS),
        "required_team_source_kind_count": len(REQUIRED_TEAM_SOURCE_KINDS),
        "team_source_coverage": {
            team_id: sorted(source_kinds)
            for team_id, source_kinds in sorted(team_source_map.items())
        },
        "required_team_approval_scope_count": len(REQUIRED_TEAM_APPROVAL_SCOPES),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "review_only": True,
        "auto_download_allowed": False,
        "auto_approval_allowed": False,
        "render_enabled": False,
        "publish_ready": False,
    }


def write_report(root: Path, report: Dict[str, Any]) -> None:
    json_path = root / OUT_JSON
    md_path = root / OUT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# HSD Womens Soccer Asset Registry Review Scaffold",
        "",
        f"Status: `{report['status']}`",
        f"Required NWSL teams: `{report['team_count']}/{report['required_team_count']}`",
        f"Players: `{report['player_count']}`",
        f"Source URL rows: `{report['source_url_count']}`",
        f"Europe top-flight leagues: `{report['europe_top_flight_league_count']}/{report['europe_top_flight_required_league_count']}`",
        f"Europe WSL teams: `{report['europe_top_flight_wsl_team_count']}/{report['europe_top_flight_required_wsl_team_count']}`",
        f"Europe Liga F teams: `{report['europe_top_flight_liga_f_team_count']}/{report['europe_top_flight_required_liga_f_team_count']}`",
        f"Europe Frauen-Bundesliga teams: `{report['europe_top_flight_frauen_bundesliga_team_count']}/{report['europe_top_flight_required_frauen_bundesliga_team_count']}`",
        f"Europe Serie A Women teams: `{report['europe_top_flight_serie_a_women_team_count']}/{report['europe_top_flight_required_serie_a_women_team_count']}`",
        f"Europe source URL rows: `{report['europe_top_flight_source_url_count']}`",
        f"Europe asset slot rows: `{report['europe_top_flight_asset_slot_count']}`",
        f"League source kinds: `{report['league_source_kind_count']}/{report['required_league_source_kind_count']}`",
        f"Team source kinds required: `{report['required_team_source_kind_count']}`",
        f"Team review scopes required: `{report['required_team_approval_scope_count']}`",
        f"Asset slot rows: `{report['asset_slot_count']}`",
        "Review only: `true`",
        "Auto-download allowed: `false`",
        "Auto-approval allowed: `false`",
        "Render enabled: `false`",
        "Publish ready: `false`",
        "",
        "## Blockers",
        "",
    ]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += ["", "## Warnings", ""]
    lines += [f"- `{value}`" for value in report.get("warnings") or []] or ["- None"]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = evaluate(root)
    write_report(root, report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in [
                    "version",
                    "status",
                    "team_count",
                    "required_team_count",
                    "player_count",
                    "source_url_count",
                    "asset_slot_count",
                    "blockers",
                    "warnings",
                ]
            },
            indent=2,
        )
    )
    return int(report["strict_exit_code"]) if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
