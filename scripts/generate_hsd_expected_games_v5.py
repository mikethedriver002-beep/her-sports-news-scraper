from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, run_output_dir, write_csv as write_run_csv, write_json, write_text

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

VERSION = "v5.2-free-public-expected-games-baseline"
OUTPUT_FILE = output_path("config/hsd_expected_games_v5.csv")
REPORT = output_path("expected_games_v5_report.md")
MANIFEST = output_path("expected_games_v5_manifest.json")

RESULTS_TIMEZONE = os.environ.get("HSD_TIMEZONE", "America/New_York")
LOOKBACK_DAYS = int(os.environ.get("HSD_LOOKBACK_DAYS", "1"))
LOOKAHEAD_DAYS = int(os.environ.get("HSD_LOOKAHEAD_DAYS", "1"))
REQUEST_SLEEP_SECONDS = float(os.environ.get("HSD_EXPECTED_GAMES_REQUEST_SLEEP_SECONDS", "0.15"))

MANUAL_SEED_FILES = [
    Path("config/hsd_expected_games_manual_seed.csv"),
    Path("config/manual_expected_games_seed.csv"),
    Path("data/expected_games/wnba_expected_games.csv"),
    Path("manual_expected_games.csv"),
]

FIELDS = [
    "date",
    "league",
    "sport",
    "home_team",
    "away_team",
    "expected_key",
    "source_name",
    "source_event_id",
    "source_url",
    "source_role",
]

ESPN_SCOREBOARD_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", clean(value).lower())).strip()


def local_date_from_iso(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if ZoneInfo is not None:
            dt = dt.astimezone(ZoneInfo(RESULTS_TIMEZONE))
        return dt.date().isoformat()
    except Exception:
        return value[:10]


def date_window() -> Tuple[List[str], List[str]]:
    if ZoneInfo is not None:
        today = datetime.now(ZoneInfo(RESULTS_TIMEZONE)).date()
    else:
        today = datetime.now(timezone.utc).date()
    iso_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]
    compact_dates = [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]
    return iso_dates, compact_dates


def key_for(sport: str, date: str, home: str, away: str) -> str:
    teams = sorted([norm(home), norm(away)])
    return "|".join([clean(sport), clean(date), teams[0], teams[1]])


def read_csv(path: Path) -> List[Dict[str, str]]:
    p = input_path(path)
    if not p.exists() or not p.is_file():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    write_run_csv(path, ({field: row.get(field, "") for field in FIELDS} for row in rows), FIELDS)


def row_from_game(date: str, home: str, away: str, source_name: str, source_event_id: str = "", source_url: str = "") -> Dict[str, str]:
    sport = "basketball"
    return {
        "date": clean(date),
        "league": "WNBA",
        "sport": sport,
        "home_team": clean(home),
        "away_team": clean(away),
        "expected_key": key_for(sport, date, home, away),
        "source_name": clean(source_name),
        "source_event_id": clean(source_event_id),
        "source_url": clean(source_url),
        "source_role": "external_expected_schedule_baseline",
    }


def rows_from_espn_payload(data: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for event in data.get("events") or []:
        event_id = clean(event.get("id"))
        start_utc = clean(event.get("date"))
        date_local = local_date_from_iso(start_utc)
        home = away = ""
        competitions = event.get("competitions") or []
        if competitions:
            for comp in competitions[0].get("competitors") or []:
                team = clean(((comp.get("team") or {}).get("displayName")))
                if clean(comp.get("homeAway")).lower() == "home":
                    home = team
                elif clean(comp.get("homeAway")).lower() == "away":
                    away = team
        if date_local and home and away:
            rows.append(
                row_from_game(
                    date_local,
                    home,
                    away,
                    "espn_wnba_public_schedule",
                    event_id,
                    f"https://www.espn.com/wnba/game/_/gameId/{event_id}" if event_id else "",
                )
            )
    return rows


def fetch_espn_expected(compact_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    rows: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    for compact in compact_dates:
        status = 0
        error = ""
        data: Dict[str, Any] = {}
        try:
            response = requests.get(
                ESPN_SCOREBOARD_ENDPOINT,
                params={"dates": compact},
                headers={"User-Agent": "HerSportsDailyExpectedGames/5.2"},
                timeout=30,
            )
            status = response.status_code
            response.raise_for_status()
            data = response.json() if isinstance(response.json(), dict) else {}
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        date_rows = rows_from_espn_payload(data)
        rows.extend(date_rows)
        health.append(
            {
                "source_name": "espn_wnba_public_schedule",
                "date": compact,
                "http_status": status,
                "ok": bool(status == 200 and not error),
                "events_found": len(data.get("events") or []) if isinstance(data, dict) else 0,
                "expected_rows_emitted": len(date_rows),
                "notes": error or "free public ESPN scoreboard schedule baseline ok",
            }
        )
        time.sleep(REQUEST_SLEEP_SECONDS)
    return rows, health


def manual_seed_rows() -> Tuple[List[Dict[str, str]], List[str]]:
    rows: List[Dict[str, str]] = []
    files_used: List[str] = []
    for configured_path in MANUAL_SEED_FILES:
        path = input_path(configured_path)
        raw_rows = read_csv(configured_path)
        if not raw_rows:
            continue
        files_used.append(path.as_posix())
        for raw in raw_rows:
            date = clean(raw.get("date") or raw.get("scheduled_date_local") or raw.get("event_date_local"))
            home = clean(raw.get("home_team") or raw.get("home_team_name"))
            away = clean(raw.get("away_team") or raw.get("away_team_name"))
            league = clean(raw.get("league") or "WNBA")
            if league.upper() != "WNBA" or not date or not home or not away:
                continue
            rows.append(
                row_from_game(
                    date,
                    home,
                    away,
                    "manual_reviewed_expected_seed",
                    clean(raw.get("source_event_id") or raw.get("event_id")),
                    clean(raw.get("source_url") or path.as_posix()),
                )
            )
    return rows, files_used


def dedupe_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        key = clean(row.get("expected_key"))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
    out.sort(key=lambda row: (row.get("date", ""), row.get("away_team", ""), row.get("home_team", "")))
    return out


def build_expected_games() -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    iso_dates, compact_dates = date_window()
    espn_rows, health = fetch_espn_expected(compact_dates)
    manual_rows, manual_files = manual_seed_rows()
    rows = dedupe_rows([*espn_rows, *manual_rows])
    source_names = sorted({row.get("source_name", "") for row in rows if clean(row.get("source_name"))})
    source_available = any(h.get("ok") for h in health) or bool(manual_rows)
    manifest = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "output_scope": "run_scoped" if run_output_dir() else "legacy_root",
        "run_output_dir": run_output_dir().as_posix() if run_output_dir() else "",
        "input_file": "free_public_espn_wnba_scoreboard",
        "input_source_type": "free_public_external_schedule_baseline",
        "observation_derived": False,
        "uses_source_observations": False,
        "output_file": OUTPUT_FILE.as_posix(),
        "date_window": iso_dates,
        "expected_games": len(rows),
        "espn_expected_games": len(espn_rows),
        "manual_seed_expected_games": len(manual_rows),
        "manual_seed_files_used": manual_files,
        "source_names": source_names,
        "source_available": source_available,
        "source_health": health,
        "free_only": True,
        "paid_sources_required": False,
        "network_used": True,
        "canonical_config_note": "When HSD_RUN_OUTPUT_DIR is set, config/hsd_expected_games_v5.csv is a run-folder review copy. Promote it to canonical config only after manual review.",
        "notes": "Expected games are generated from a free public schedule endpoint plus optional local manual reviewed seeds. They are not derived from source_observations.csv.",
    }
    return rows, manifest


def write_report(rows: List[Dict[str, str]], manifest: Dict[str, Any]) -> None:
    lines = [
        "# HSD Expected Games v5",
        "",
        f"Generated: `{manifest['generated_at_utc']}`",
        f"Version: `{manifest['version']}`",
        "",
        "## Source-truth role",
        "",
        "- Expected-games baseline is generated before the final Results Desk reconciliation pass.",
        "- The baseline is not derived from `source_observations.csv`.",
        "- Source role: free public schedule baseline plus optional local manual reviewed seed.",
        "",
        "## Counts",
        "",
        f"- expected games: `{manifest.get('expected_games')}`",
        f"- ESPN expected games: `{manifest.get('espn_expected_games')}`",
        f"- manual seed expected games: `{manifest.get('manual_seed_expected_games')}`",
        f"- source available: `{manifest.get('source_available')}`",
        "",
        "## Source health",
        "",
    ]
    for health in manifest.get("source_health") or []:
        lines.append(
            f"- {health.get('date')} | ok={health.get('ok')} | http={health.get('http_status')} | "
            f"events={health.get('events_found')} | emitted={health.get('expected_rows_emitted')} | {health.get('notes')}"
        )
    lines += ["", "## Games", ""]
    lines += [
        f"- {row['date']} | {row['away_team']} at {row['home_team']} | `{row['expected_key']}` | {row.get('source_name')}"
        for row in rows
    ] or ["No expected games were generated for the configured date window."]
    write_text(REPORT, "\n".join(lines) + "\n")


def main() -> None:
    rows, manifest = build_expected_games()
    write_csv(OUTPUT_FILE, rows)
    write_json(MANIFEST, manifest, sort_keys=True)
    write_report(rows, manifest)
    print(json.dumps({"expected_games": len(rows), "source_available": manifest.get("source_available")}, indent=2))


if __name__ == "__main__":
    main()
