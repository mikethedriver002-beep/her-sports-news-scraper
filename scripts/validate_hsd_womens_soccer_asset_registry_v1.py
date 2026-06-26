from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VERSION = "v1.0-womens-soccer-asset-registry-review-only"
REGISTRY = Path("data/asset_registry/womens_soccer/nwsl")
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
    blockers: List[str] = []
    warnings: List[str] = []
    rows_by_file: Dict[str, List[Dict[str, str]]] = {}
    headers_by_file: Dict[str, List[str]] = {}

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
            for url_field in ["source_url", "official_url", "teams_url", "players_url", "team_site_url", "roster_source_url"]:
                if url_field not in row:
                    continue
                value = clean(row.get(url_field))
                if value and not value.startswith("https://"):
                    blockers.append(f"non_https_source:{ident}:{url_field}")

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

    player_count = len(rows_by_file.get("players.csv", []))
    if player_count == 0:
        warnings.append("players_csv_header_only_manual_intake")

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
        "source_url_count": len(rows_by_file.get("source_urls.csv", [])),
        "asset_slot_count": len(rows_by_file.get("asset_slots.csv", [])),
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
