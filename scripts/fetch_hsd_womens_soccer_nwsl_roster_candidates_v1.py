from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


VERSION = "hsd-womens-soccer-nwsl-roster-candidates-v1-review-only"
ROOT = Path("data/asset_registry/womens_soccer/nwsl")
TEAMS = ROOT / "teams.csv"
PLAYERS = ROOT / "players.csv"
REPORT_JSON = ROOT / "roster_candidate_fetch_report.json"
REPORT_MD = ROOT / "roster_candidate_fetch_report.md"
SEASON_ID = "nwsl::Football_Season::0b6761e4701749f593690c0f338da74c"

PLAYER_FIELDS = [
    "player_id",
    "league_id",
    "team_id",
    "display_name",
    "provider_player_id",
    "roster_source_url",
    "status",
    "manual_review_status",
    "asset_registry_status",
    "approval_status",
    "notes",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def team_uuid(nwsl_team_url: str) -> str:
    match = re.search(r"/teams/([^/]+)/", clean(nwsl_team_url))
    return match.group(1) if match else ""


def roster_api_url(team_id: str, season_id: str) -> str:
    team_token = f"nwsl::Football_Team::{team_id}"
    return (
        "https://api-sdp.nwslsoccer.com/v1/nwsl/football/teams/"
        + urllib.parse.quote(team_token, safe="")
        + "/roster?locale=en-US&seasonId="
        + urllib.parse.quote(season_id, safe="")
    )


def fetch_json(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HSD-review-only-roster-metadata/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def player_name(row: Dict[str, Any]) -> str:
    first = clean(row.get("mediaFirstName"))
    last = clean(row.get("mediaLastName"))
    return clean(f"{first} {last}") or clean(row.get("shortName")) or clean(row.get("displayName"))


def build_player_rows(teams: List[Dict[str, str]], *, season_id: str) -> tuple[List[Dict[str, str]], List[str]]:
    rows: List[Dict[str, str]] = []
    warnings: List[str] = []
    for team in teams:
        local_team_id = clean(team.get("team_id"))
        league_id = clean(team.get("league_id")) or "nwsl"
        roster_url = clean(team.get("nwsl_roster_url"))
        api_team_id = team_uuid(roster_url or clean(team.get("nwsl_team_url")))
        if not local_team_id or not api_team_id:
            warnings.append(f"{local_team_id or 'missing_team'}:missing_nwsl_team_uuid")
            continue
        api_url = roster_api_url(api_team_id, season_id)
        try:
            payload = fetch_json(api_url)
        except Exception as exc:
            warnings.append(f"{local_team_id}:roster_metadata_fetch_failed:{type(exc).__name__}")
            continue
        for player in payload.get("players") or []:
            name = player_name(player)
            player_id = clean(player.get("playerId"))
            if not name or not player_id:
                warnings.append(f"{local_team_id}:player_row_missing_identity")
                continue
            rows.append(
                {
                    "player_id": player_id,
                    "league_id": league_id,
                    "team_id": local_team_id,
                    "display_name": name,
                    "provider_player_id": clean(player.get("providerId")),
                    "roster_source_url": roster_url,
                    "status": clean(player.get("playerStatus")) or "Active",
                    "manual_review_status": "identity_source_review_required",
                    "asset_registry_status": "candidate_layer_only_no_asset_write",
                    "approval_status": "not_approved",
                    "notes": "Official public NWSL roster metadata only; no image download, no approval, no renderer enablement.",
                }
            )
    rows.sort(key=lambda item: (item["league_id"], item["team_id"], item["display_name"], item["player_id"]))
    return rows, warnings


def render_report(payload: Dict[str, Any]) -> str:
    lines = [
        "# NWSL Roster Candidate Fetch Report",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "",
        "Review-only roster metadata fetch. This records player identity/source candidate rows only. It does not download athlete photos, approve identities, write `headshot.png`, create `.approved` markers, move files, publish, or create a publish-ready lane.",
        "",
        "## Summary",
        "",
        f"- Status: `{payload['status']}`",
        f"- Teams checked: `{payload['teams_checked']}`",
        f"- Player rows written: `{payload['player_rows']}`",
        f"- Warnings: `{len(payload['warnings'])}`",
        f"- Output: `{payload['players_csv']}`",
        "",
        "## Guardrails",
        "",
    ]
    for key, value in payload["guardrails"].items():
        lines.append(f"- {key}: `{str(value).lower()}`")
    if payload["warnings"]:
        lines += ["", "## Warnings", ""]
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    return "\n".join(lines) + "\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch review-only NWSL roster metadata into women's soccer player candidates.")
    parser.add_argument("--season-id", default=SEASON_ID)
    args = parser.parse_args(argv)

    teams = read_csv(TEAMS)
    rows, warnings = build_player_rows(teams, season_id=args.season_id)
    write_csv(PLAYERS, rows, PLAYER_FIELDS)
    payload = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "roster_candidates_ready" if rows else "no_roster_candidates_written",
        "season_id": args.season_id,
        "teams_checked": len(teams),
        "player_rows": len(rows),
        "players_csv": PLAYERS.as_posix(),
        "warnings": warnings,
        "guardrails": {
            "review_only": True,
            "downloads_performed": False,
            "athlete_photo_downloads": False,
            "approvals_applied": False,
            "headshot_files_written": False,
            "approved_markers_created": False,
            "publish_ready": False,
            "auto_publish": False,
            "paid_apis": False,
        },
    }
    write_json(REPORT_JSON, payload)
    REPORT_MD.write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({"version": VERSION, "status": payload["status"], "player_rows": len(rows), "warnings": warnings}, indent=2))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
