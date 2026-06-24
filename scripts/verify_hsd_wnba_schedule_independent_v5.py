from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, run_output_dir, write_csv as write_run_csv, write_json, write_text

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

VERSION = "v5.2-multi-source-wnba-schedule-verification"
EXPECTED = Path("config/hsd_expected_games_v5.csv")
OUT_CSV = output_path("independent_schedule_verification_v5.csv")
OUT_JSON = output_path("independent_schedule_verification_v5.json")
OUT_MD = output_path("independent_schedule_verification_v5.md")
RESULTS_TIMEZONE = os.environ.get("HSD_TIMEZONE", "America/New_York")
REQUEST_SLEEP_SECONDS = float(os.environ.get("HSD_INDEPENDENT_VERIFY_SLEEP_SECONDS", "0.15"))
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("HSD_INDEPENDENT_VERIFY_TIMEOUT_SECONDS", "12"))

ABBR = {
    "ATL": "Atlanta Dream",
    "CHI": "Chicago Sky",
    "CON": "Connecticut Sun",
    "DAL": "Dallas Wings",
    "GSV": "Golden State Valkyries",
    "IND": "Indiana Fever",
    "LVA": "Las Vegas Aces",
    "LAS": "Los Angeles Sparks",
    "MIN": "Minnesota Lynx",
    "NYL": "New York Liberty",
    "PHX": "Phoenix Mercury",
    "POR": "Portland Fire",
    "SEA": "Seattle Storm",
    "TOR": "Toronto Tempo",
    "WAS": "Washington Mystics",
}

FIELDS = [
    "date",
    "home_team",
    "away_team",
    "expected_key",
    "independent_key",
    "status",
    "source_event_id",
    "verification_source",
    "source_role",
    "notes",
]

WNBA_STATS_ENDPOINT = "https://stats.wnba.com/stats/scoreboardv2"
ESPN_SCOREBOARD_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def norm(v: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", clean(v).lower())).strip()


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


def key_for(date: str, home: str, away: str) -> str:
    pair = sorted([norm(home), norm(away)])
    return "|".join(["basketball", clean(date), pair[0], pair[1]])


def read_rows(path: Path) -> List[Dict[str, str]]:
    p = input_path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    write_run_csv(path, ({field: row.get(field, "") for field in FIELDS} for row in rows), FIELDS)


def mmddyyyy(date: str) -> str:
    y, m, d = clean(date).split("-")
    return f"{m}/{d}/{y}"


def compact_yyyymmdd(date: str) -> str:
    return clean(date).replace("-", "")


def result_sets(data: Dict[str, Any]) -> Dict[str, Any]:
    return {clean(x.get("name")): x for x in data.get("resultSets", []) if clean(x.get("name"))}


def as_dict(headers: List[str], row: List[Any]) -> Dict[str, Any]:
    return {headers[i]: row[i] for i in range(min(len(headers), len(row)))}


def split_gamecode(code: str) -> Tuple[str, str]:
    suffix = clean(code).split("/")[-1].upper()
    for away in sorted(ABBR, key=len, reverse=True):
        if suffix.startswith(away):
            home = suffix[len(away):]
            if home in ABBR:
                return ABBR[away], ABBR[home]
    return "", ""


def verification_row(date: str, home: str, away: str, source: str, source_event_id: str = "", notes: str = "") -> Dict[str, str]:
    key = key_for(date, home, away)
    return {
        "date": clean(date),
        "home_team": clean(home),
        "away_team": clean(away),
        "expected_key": key,
        "independent_key": key,
        "status": "independent_seen",
        "source_event_id": clean(source_event_id),
        "verification_source": clean(source),
        "source_role": "free_public_schedule_verifier",
        "notes": clean(notes),
    }


def source_health(source_name: str, date: str, ok: bool, http_status: int, events: int, emitted: int, notes: str) -> Dict[str, Any]:
    return {
        "source_name": source_name,
        "date": date,
        "ok": bool(ok),
        "http_status": http_status,
        "events": events,
        "emitted": emitted,
        "notes": notes,
    }


def fetch_wnba_stats_date(date: str) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    params = {"DayOffset": "0", "GameDate": mmddyyyy(date), "LeagueID": "10"}
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.wnba.com/"}
    status = 0
    try:
        response = requests.get(WNBA_STATS_ENDPOINT, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        status = response.status_code
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return [], source_health("wnba_stats_scoreboardv2", date, False, status, 0, 0, f"{type(exc).__name__}: {exc}")
    game_header = result_sets(data).get("GameHeader") or {}
    headers_list = game_header.get("headers") or []
    rows: List[Dict[str, str]] = []
    for raw in game_header.get("rowSet") or []:
        item = as_dict(headers_list, raw)
        away, home = split_gamecode(clean(item.get("GAMECODE")))
        date_est = clean(item.get("GAME_DATE_EST"))[:10] or date
        if away and home:
            rows.append(verification_row(date_est, home, away, "wnba_stats_scoreboardv2", clean(item.get("GAME_ID")), "WNBA Stats scoreboardv2"))
    return rows, source_health("wnba_stats_scoreboardv2", date, True, status, len(game_header.get("rowSet") or []), len(rows), "ok")


def fetch_espn_scoreboard_date(date: str) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    status = 0
    try:
        response = requests.get(
            ESPN_SCOREBOARD_ENDPOINT,
            params={"dates": compact_yyyymmdd(date)},
            headers={"User-Agent": "HerSportsDailyIndependentVerifier/5.2"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        status = response.status_code
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return [], source_health("espn_wnba_public_scoreboard_verify", date, False, status, 0, 0, f"{type(exc).__name__}: {exc}")
    events = data.get("events") if isinstance(data, dict) else []
    events = events or []
    rows: List[Dict[str, str]] = []
    for event in events:
        event_id = clean(event.get("id"))
        date_local = local_date_from_iso(clean(event.get("date"))) or date
        home = away = ""
        competitions = event.get("competitions") or []
        if competitions:
            for competitor in competitions[0].get("competitors") or []:
                team = clean(((competitor.get("team") or {}).get("displayName")))
                if clean(competitor.get("homeAway")).lower() == "home":
                    home = team
                elif clean(competitor.get("homeAway")).lower() == "away":
                    away = team
        if home and away:
            rows.append(verification_row(date_local, home, away, "espn_wnba_public_scoreboard_verify", event_id, "ESPN public scoreboard verifier"))
    return rows, source_health("espn_wnba_public_scoreboard_verify", date, True, status, len(events), len(rows), "ok")


def fetch_all_sources(dates: Iterable[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    independent: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    for date in sorted(set(clean(d) for d in dates if clean(d))):
        for fetcher in [fetch_wnba_stats_date, fetch_espn_scoreboard_date]:
            rows, h = fetcher(date)
            independent.extend(rows)
            health.append(h)
            time.sleep(REQUEST_SLEEP_SECONDS)
    return independent, health


def available_dates_by_source(health: List[Dict[str, Any]]) -> Dict[str, set[str]]:
    out: Dict[str, set[str]] = {}
    for row in health:
        if row.get("ok"):
            out.setdefault(clean(row.get("source_name")), set()).add(clean(row.get("date")))
    return out


def verify_expected_against_sources(expected: List[Dict[str, str]], independent: List[Dict[str, str]], health: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    by_key: Dict[str, Dict[str, str]] = {}
    sources_by_key: Dict[str, set[str]] = {}
    for row in independent:
        key = clean(row.get("independent_key") or row.get("expected_key"))
        if not key:
            continue
        by_key.setdefault(key, row)
        sources_by_key.setdefault(key, set()).add(clean(row.get("verification_source")))
    expected_keys = {clean(row.get("expected_key")) for row in expected if clean(row.get("expected_key"))}
    ok_dates = {clean(h.get("date")) for h in health if h.get("ok")}
    out: List[Dict[str, Any]] = []
    for row in expected:
        key = clean(row.get("expected_key"))
        date = clean(row.get("date"))
        found = by_key.get(key)
        if found:
            status = "matched"
            notes = f"matched by {', '.join(sorted(sources_by_key.get(key, set())))}"
            independent_key = clean(found.get("independent_key"))
            event_id = clean(found.get("source_event_id"))
            source = ";".join(sorted(sources_by_key.get(key, set())))
            role = "free_public_schedule_verifier"
        elif date not in ok_dates:
            status = "independent_source_unavailable"
            notes = "no verifier source available for this date"
            independent_key = event_id = source = role = ""
        else:
            status = "missing_from_independent"
            notes = "not found in available verifier source"
            independent_key = event_id = source = role = ""
        out.append(
            {
                "date": row.get("date"),
                "home_team": row.get("home_team"),
                "away_team": row.get("away_team"),
                "expected_key": key,
                "independent_key": independent_key,
                "status": status,
                "source_event_id": event_id,
                "verification_source": source,
                "source_role": role,
                "notes": notes,
            }
        )
    for row in independent:
        key = clean(row.get("independent_key") or row.get("expected_key"))
        if key and key not in expected_keys:
            extra = dict(row)
            extra["status"] = "extra_in_independent"
            out.append(extra)
    available_sources = sorted({clean(h.get("source_name")) for h in health if h.get("ok")})
    emitted_sources = sorted({clean(row.get("verification_source")) for row in independent if clean(row.get("verification_source"))})
    expected_games = len(expected)
    matched = sum(1 for row in out if row.get("status") == "matched")
    missing = sum(1 for row in out if row.get("status") == "missing_from_independent")
    unavailable = sum(1 for row in out if row.get("status") == "independent_source_unavailable")
    extra = sum(1 for row in out if row.get("status") == "extra_in_independent")
    source_available = bool(available_sources and independent)
    verification_inconclusive = not source_available
    summary = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "output_scope": "run_scoped" if run_output_dir() else "legacy_root",
        "run_output_dir": run_output_dir().as_posix() if run_output_dir() else "",
        "expected_games": expected_games,
        "independent_games": len({clean(row.get("independent_key") or row.get("expected_key")) for row in independent if clean(row.get("independent_key") or row.get("expected_key"))}),
        "matched": matched,
        "missing_from_independent": missing,
        "independent_source_unavailable": unavailable,
        "extra_in_independent": extra,
        "source_available": source_available,
        "verification_inconclusive": verification_inconclusive,
        "available_sources": available_sources,
        "emitted_sources": emitted_sources,
        "health": health,
        "source_dates": {source: sorted(dates) for source, dates in available_dates_by_source(health).items()},
        "policy": {
            "free_only": True,
            "paid_sources_required": False,
            "sources_attempted": ["wnba_stats_scoreboardv2", "espn_wnba_public_scoreboard_verify"],
            "source_role": "schedule verification, not expected-baseline generation",
        },
    }
    return out, summary


def verify() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    expected = read_rows(EXPECTED)
    dates = sorted({clean(row.get("date")) for row in expected if clean(row.get("date"))})
    independent, health = fetch_all_sources(dates)
    return verify_expected_against_sources(expected, independent, health)


def report(summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Independent WNBA Schedule Verification v5",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Version: `{summary['version']}`",
        "",
        "## Counts",
        "",
    ]
    for key in [
        "expected_games",
        "independent_games",
        "matched",
        "missing_from_independent",
        "independent_source_unavailable",
        "extra_in_independent",
        "source_available",
        "verification_inconclusive",
    ]:
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines += ["", "## Sources", ""]
    lines.append(f"- Available sources: `{', '.join(summary.get('available_sources') or []) or 'None'}`")
    lines.append(f"- Emitted sources: `{', '.join(summary.get('emitted_sources') or []) or 'None'}`")
    bad = [row for row in rows if row.get("status") != "matched"]
    lines += ["", "## Mismatches / inconclusive rows", ""]
    lines += ["- None"] if not bad else [f"- {row['status']} | {row.get('date')} | {row.get('away_team')} at {row.get('home_team')} | {row.get('verification_source', '')}" for row in bad]
    lines += ["", "## Source health", ""]
    for h in summary.get("health", []):
        lines.append(
            f"- {h.get('source_name')} | {h.get('date')} | ok={h.get('ok')} | "
            f"http={h.get('http_status')} | events={h.get('events')} | emitted={h.get('emitted')} | {h.get('notes')}"
        )
    lines += ["", "## Policy", "", "- Free public sources only.", "- No paid API, paid feed, paid proxy, scraping service, or LLM dependency."]
    return "\n".join(lines) + "\n"


def main() -> None:
    rows, summary = verify()
    write_rows(OUT_CSV, rows)
    write_json(OUT_JSON, summary, sort_keys=True)
    write_text(OUT_MD, report(summary, rows))
    print(
        json.dumps(
            {
                "matched": summary["matched"],
                "missing": summary["missing_from_independent"],
                "inconclusive": summary["independent_source_unavailable"],
                "extra": summary["extra_in_independent"],
                "available_sources": summary.get("available_sources"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
