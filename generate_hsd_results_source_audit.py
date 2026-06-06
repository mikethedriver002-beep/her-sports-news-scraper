
"""
Her Sports Daily Results Source Audit v2
----------------------------------------

This is a better source audit for rebuilding Results Desk v3.

Fixes from v1:
- SofaScore: tests both api.sofascore.com and www.sofascore.com API paths with browser-like headers.
- TheSportsDB: fixes blank secret issue by falling back to public test key if THESPORTSDB_KEY is unset or empty.
- NCAA API: detects stale/default championship data and counts only date-matched events as usable.
- ESPN: keeps date-specific testing because it performed best for WNBA.
- Optional API-Sports remains available if APISPORTS_KEY is set.

Outputs:
- source_coverage_report.csv
- source_event_samples.csv
- source_audit_summary.md
- source_audit_raw.json
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

import requests


OUTPUT_REPORT = "source_coverage_report.csv"
OUTPUT_SAMPLES = "source_event_samples.csv"
OUTPUT_SUMMARY = "source_audit_summary.md"
OUTPUT_RAW = "source_audit_raw.json"

TIMEZONE = "America/New_York"
LOOKBACK_DAYS = 1
LOOKAHEAD_DAYS = 2
REQUEST_SLEEP_SECONDS = 0.35

BASIC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailySourceAudit/2.0; +https://github.com/)",
}

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
}

WOMENS_TERMS = [
    "women", "women's", "womens", "female", "girls", "wnba", "nwsl", "pwhl",
    "lpga", "wta", "uswnt", "ncaa women", "ncaa women's", "softball",
]

TARGET_TERMS = [
    "wnba", "ncaa", "women", "women's", "womens", "softball", "nwsl", "pwhl",
    "lpga", "wta", "volleyball", "soccer", "basketball", "hockey", "tennis",
]


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def low(value: Any) -> str:
    return clean(value).lower()


def today_local():
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo(TIMEZONE)).date()
    return datetime.now(timezone.utc).date()


def date_strings() -> List[Dict[str, str]]:
    today = today_local()
    out = []
    for offset in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1):
        d = today + timedelta(days=offset)
        out.append({
            "iso": d.strftime("%Y-%m-%d"),
            "compact": d.strftime("%Y%m%d"),
            "slash": d.strftime("%m/%d/%Y"),
            "sofa": d.strftime("%Y-%m-%d"),
        })
    return out


def request_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[Any], int, str]:
    try:
        response = requests.get(url, params=params or {}, headers=headers or BASIC_HEADERS, timeout=25)
        status = response.status_code
        response.raise_for_status()
        return response.json(), status, ""
    except Exception as exc:
        status = 0
        try:
            status = response.status_code
        except Exception:
            pass
        return None, status, str(exc)


def relevance_score(text: str, forced_womens: bool = False) -> int:
    if forced_womens:
        return 99
    s = low(text)
    score = 0
    score += 5 * sum(1 for term in WOMENS_TERMS if term in s)
    score += 2 * sum(1 for term in TARGET_TERMS if term in s)
    return score


def is_likely_womens_event(text: str, forced_womens: bool = False) -> bool:
    return relevance_score(text, forced_womens=forced_womens) >= 5


def normalize_mmddyyyy(value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%Y%m%d"]:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def ncaa_event_date(event: Dict[str, Any]) -> str:
    for key in ["startDate", "date", "gameDate", "contestDate"]:
        val = event.get(key)
        norm = normalize_mmddyyyy(clean(val))
        if norm:
            return norm
    return ""


def ncaa_event_matches_date(event: Dict[str, Any], date_iso: str) -> bool:
    event_date = ncaa_event_date(event)
    if not event_date:
        # If no date is provided, treat as unknown rather than fresh.
        return False
    return event_date == date_iso


def sample_join(samples: List[str], limit: int = 4) -> str:
    cleaned = []
    seen = set()
    for sample in samples:
        sample = clean(sample)
        if not sample or sample in seen:
            continue
        seen.add(sample)
        cleaned.append(sample)
        if len(cleaned) >= limit:
            break
    return " || ".join(cleaned)


def recommendation(source_name: str, events_found: int, likely_women: int, fresh_events: int = 0, status_code: int = 0) -> str:
    if events_found == 0:
        if status_code == 403 and "SofaScore" in source_name:
            return "Blocked in GitHub Actions"
        return "Do not use yet"
    if "SofaScore" in source_name:
        return "Discovery candidate only"
    if "ESPN" in source_name:
        return "Structured verification candidate"
    if "NCAA" in source_name:
        if fresh_events > 0:
            return "College verification candidate"
        return "Stale data risk, do not use yet"
    if "TheSportsDB" in source_name:
        return "Metadata/discovery candidate"
    if "API-Sports" in source_name:
        return "Paid/API-key candidate"
    return "Needs review"


def make_report_row(
    source_name: str,
    sport_or_league: str,
    date_label: str,
    endpoint: str,
    status_code: int,
    ok: bool,
    events_found: int,
    likely_womens_events: int,
    sample_events: List[str],
    capabilities: str,
    recommended_role: str,
    notes: str,
    raw_events_found: int = 0,
    stale_events_found: int = 0,
    date_matched_events: int = 0,
) -> Dict[str, str]:
    return {
        "source_name": source_name,
        "sport_or_league": sport_or_league,
        "date": date_label,
        "endpoint": endpoint,
        "http_status": str(status_code),
        "ok": "Yes" if ok else "No",
        "events_found": str(events_found),
        "raw_events_found": str(raw_events_found if raw_events_found else events_found),
        "date_matched_events": str(date_matched_events if date_matched_events else events_found),
        "stale_events_found": str(stale_events_found),
        "likely_womens_events": str(likely_womens_events),
        "women_relevance_score": str(sum(relevance_score(x) for x in sample_events)),
        "sample_events": sample_join(sample_events),
        "capabilities": capabilities,
        "recommended_role": recommended_role,
        "notes": notes,
    }


def event_sample_row(
    source_name: str,
    sport_or_league: str,
    date_label: str,
    event_name: str,
    status: str = "",
    score: str = "",
    tournament: str = "",
    event_id: str = "",
    source_url: str = "",
    likely_womens: bool = False,
    date_match: str = "",
    raw_note: str = "",
) -> Dict[str, str]:
    return {
        "source_name": source_name,
        "sport_or_league": sport_or_league,
        "date": date_label,
        "event_id": clean(event_id),
        "event_name": clean(event_name),
        "status": clean(status),
        "score": clean(score),
        "tournament": clean(tournament),
        "source_url": clean(source_url),
        "likely_womens": "Yes" if likely_womens else "No",
        "date_match": date_match,
        "raw_note": clean(raw_note),
    }


def audit_sofascore() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "SofaScore public endpoints"
    sports = ["basketball", "football", "tennis", "volleyball", "ice-hockey", "handball", "baseball"]

    # v2 tests both common host patterns.
    endpoint_templates = [
        "https://api.sofascore.com/api/v1/sport/{sport}/scheduled-events/{date}",
        "https://www.sofascore.com/api/v1/sport/{sport}/scheduled-events/{date}",
    ]

    report_rows = []
    sample_rows = []
    raw = {}

    for sport in sports:
        for d in date_strings():
            for template in endpoint_templates:
                endpoint = template.format(sport=sport, date=d["sofa"])
                data, status, error = request_json(endpoint, headers=BROWSER_HEADERS)
                time.sleep(REQUEST_SLEEP_SECONDS)

                events = []
                if isinstance(data, dict):
                    events = data.get("events") or []

                samples = []
                relevant = 0
                for event in events[:50]:
                    home = clean(((event.get("homeTeam") or {}).get("name")))
                    away = clean(((event.get("awayTeam") or {}).get("name")))
                    tournament = clean(((event.get("tournament") or {}).get("name")))
                    category = clean((((event.get("tournament") or {}).get("category") or {}).get("name")))
                    status_text = clean(((event.get("status") or {}).get("description") or (event.get("status") or {}).get("type")))
                    home_score = clean(((event.get("homeScore") or {}).get("current")))
                    away_score = clean(((event.get("awayScore") or {}).get("current")))
                    event_id = clean(event.get("id"))
                    name = f"{away} vs {home}" if away or home else clean(event.get("slug"))
                    full_text = " ".join([name, tournament, category, sport])
                    likely = is_likely_womens_event(full_text)
                    if likely:
                        relevant += 1
                    score = f"{away_score}-{home_score}" if away_score or home_score else ""
                    samples.append(f"{name} | {tournament} | {category} | {status_text} | {score}")
                    sample_rows.append(event_sample_row(
                        source_name, sport, d["iso"], name, status_text, score,
                        " | ".join([tournament, category]), event_id,
                        f"https://www.sofascore.com/event/{event_id}" if event_id else "",
                        likely_womens=likely,
                        date_match="Unknown",
                        raw_note="Unofficial endpoint. Discovery only unless verified elsewhere.",
                    ))

                raw[f"sofascore::{sport}::{d['iso']}::{endpoint}"] = {
                    "status": status,
                    "error": error,
                    "event_count": len(events),
                    "host_pattern": endpoint.split("/api/")[0],
                }

                report_rows.append(make_report_row(
                    source_name, sport, d["iso"], endpoint, status,
                    status == 200 and isinstance(data, dict), len(events), relevant, samples,
                    "Wide event discovery, live/final status, basic scores if accessible.",
                    recommendation(source_name, len(events), relevant, status_code=status),
                    error or "Tested scheduled-events endpoint with browser-like headers.",
                    raw_events_found=len(events),
                    date_matched_events=len(events),
                ))

    return report_rows, sample_rows, raw


def audit_espn() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "ESPN public scoreboard"
    leagues = [
        ("WNBA", "basketball", "wnba", True),
        ("NCAA Women's Basketball", "basketball", "womens-college-basketball", True),
        ("NCAA Softball", "softball", "college-softball", True),
        ("NWSL", "soccer", "usa.nwsl", True),
        ("NCAA Women's Volleyball", "volleyball", "womens-college-volleyball", True),
        ("NCAA Women's Soccer", "soccer", "womens-college-soccer", True),
    ]

    report_rows = []
    sample_rows = []
    raw = {}

    for label, sport, league, forced_womens in leagues:
        for d in date_strings():
            endpoint = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
            params = {"dates": d["compact"]}
            data, status, error = request_json(endpoint, params=params)
            time.sleep(REQUEST_SLEEP_SECONDS)

            events = data.get("events") if isinstance(data, dict) else []
            events = events or []
            samples = []
            relevant = 0
            for event in events:
                name = clean(event.get("name") or event.get("shortName"))
                status_text = clean((((event.get("status") or {}).get("type") or {}).get("detail")))
                event_id = clean(event.get("id"))
                comps = event.get("competitions") or []
                score = ""
                if comps:
                    teams = comps[0].get("competitors") or []
                    parts = []
                    for team in teams:
                        team_name = clean(((team.get("team") or {}).get("shortDisplayName") or (team.get("team") or {}).get("displayName")))
                        team_score = clean(team.get("score"))
                        if team_name or team_score:
                            parts.append(f"{team_name} {team_score}".strip())
                    score = " - ".join(parts)
                full_text = " ".join([label, name, sport, league])
                likely = is_likely_womens_event(full_text, forced_womens=forced_womens)
                if likely:
                    relevant += 1
                samples.append(f"{name} | {status_text} | {score}")
                sample_rows.append(event_sample_row(
                    source_name, label, d["iso"], name, status_text, score,
                    label, event_id,
                    f"https://www.espn.com/{sport}/game/_/gameId/{event_id}" if event_id else "",
                    likely_womens=likely,
                    date_match="Yes",
                    raw_note="Date-specific ESPN scoreboard response.",
                ))

            raw[f"espn::{label}::{d['iso']}"] = {
                "status": status,
                "error": error,
                "event_count": len(events),
                "keys": list(data.keys()) if isinstance(data, dict) else [],
            }

            report_rows.append(make_report_row(
                source_name, label, d["iso"], f"{endpoint}?dates={d['compact']}", status,
                status == 200 and isinstance(data, dict), len(events), relevant, samples,
                "Structured scoreboard, date-specific status, scores, and some summary/box score endpoints.",
                recommendation(source_name, len(events), relevant, status_code=status),
                error or "Date-specific scoreboard test.",
                raw_events_found=len(events),
                date_matched_events=len(events),
            ))

    return report_rows, sample_rows, raw


def extract_ncaa_events(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []

    # Many NCAA API responses store games under one of these paths.
    candidates = []
    for key in ["games", "events", "scoreboard", "data"]:
        val = data.get(key)
        if isinstance(val, list):
            candidates.extend([x for x in val if isinstance(x, dict)])
        elif isinstance(val, dict):
            for subkey in ["games", "events"]:
                subval = val.get(subkey)
                if isinstance(subval, list):
                    candidates.extend([x for x in subval if isinstance(x, dict)])

    # Sometimes the dict itself looks like a game.
    if not candidates and any(k in data for k in ["gameID", "gameId", "title", "away", "home"]):
        candidates.append(data)

    return candidates


def audit_ncaa_api() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "NCAA API / ncaa.com-derived"
    base = "https://ncaa-api.henrygd.me"

    sports = [
        ("DI Softball", "softball", "d1", True),
        ("DII Softball", "softball", "d2", True),
        ("DIII Softball", "softball", "d3", True),
        ("DI Women's Basketball", "basketball-women", "d1", True),
        ("DI Women's Volleyball", "volleyball-women", "d1", True),
        ("DI Women's Soccer", "soccer-women", "d1", True),
    ]

    endpoint_patterns = [
        "{base}/scoreboard/{sport}/{division}/{date_iso}",
        "{base}/scoreboard/{sport}/{division}/{date_compact}",
        "{base}/scoreboard/{division}/{sport}/{date_iso}",
        "{base}/game/scoreboard/{sport}/{division}/{date_iso}",
    ]

    report_rows = []
    sample_rows = []
    raw = {}

    for label, sport, division, forced_womens in sports:
        for d in date_strings():
            for pattern in endpoint_patterns:
                endpoint = pattern.format(base=base, sport=sport, division=division, date_iso=d["iso"], date_compact=d["compact"])
                data, status, error = request_json(endpoint)
                time.sleep(REQUEST_SLEEP_SECONDS)

                raw_events = extract_ncaa_events(data)
                fresh_events = []
                stale_events = []

                for event in raw_events:
                    if ncaa_event_matches_date(event, d["iso"]):
                        fresh_events.append(event)
                    else:
                        stale_events.append(event)

                samples = []
                relevant = 0
                for event in fresh_events[:30]:
                    away = event.get("away") or {}
                    home = event.get("home") or {}
                    away_name = clean(((away.get("names") or {}).get("short") or (away.get("names") or {}).get("full")))
                    home_name = clean(((home.get("names") or {}).get("short") or (home.get("names") or {}).get("full")))
                    away_score = clean(away.get("score"))
                    home_score = clean(home.get("score"))
                    title = clean(event.get("title") or f"{away_name} at {home_name}")
                    status_text = clean(event.get("gameState") or event.get("finalMessage") or event.get("currentPeriod"))
                    score = f"{away_name} {away_score} - {home_name} {home_score}".strip()
                    event_id = clean(event.get("gameID") or event.get("gameId") or event.get("id"))
                    full_text = " ".join([label, title, sport])
                    likely = is_likely_womens_event(full_text, forced_womens=forced_womens)
                    if likely:
                        relevant += 1
                    samples.append(f"{title} | {status_text} | {score}")
                    sample_rows.append(event_sample_row(
                        source_name, label, d["iso"], title, status_text, score,
                        label, event_id, endpoint,
                        likely_womens=likely,
                        date_match="Yes",
                        raw_note="Fresh date-matched NCAA API event.",
                    ))

                # Add one stale example so we know what was rejected.
                for event in stale_events[:2]:
                    title = clean(event.get("title") or json.dumps(event)[:100])
                    event_date = ncaa_event_date(event)
                    sample_rows.append(event_sample_row(
                        source_name, label, d["iso"], title,
                        clean(event.get("gameState") or event.get("finalMessage")),
                        "",
                        label,
                        clean(event.get("gameID") or event.get("gameId") or event.get("id")),
                        endpoint,
                        likely_womens=is_likely_womens_event(" ".join([label, title]), forced_womens=forced_womens),
                        date_match=f"No, event date {event_date or 'unknown'}",
                        raw_note="Rejected as stale/default NCAA API data.",
                    ))

                raw[f"ncaa::{label}::{d['iso']}::{endpoint}"] = {
                    "status": status,
                    "error": error,
                    "raw_event_count": len(raw_events),
                    "fresh_event_count": len(fresh_events),
                    "stale_event_count": len(stale_events),
                    "data_type": type(data).__name__,
                    "top_keys": list(data.keys()) if isinstance(data, dict) else [],
                }

                report_rows.append(make_report_row(
                    source_name, label, d["iso"], endpoint, status,
                    status == 200 and data is not None, len(fresh_events), relevant, samples,
                    "College scoreboard/game details if endpoint works and dates match. Strong NCAA candidate only when fresh.",
                    recommendation(source_name, len(fresh_events), relevant, fresh_events=len(fresh_events), status_code=status),
                    error or f"Raw events: {len(raw_events)}. Fresh/date-matched: {len(fresh_events)}. Stale rejected: {len(stale_events)}.",
                    raw_events_found=len(raw_events),
                    date_matched_events=len(fresh_events),
                    stale_events_found=len(stale_events),
                ))

    return report_rows, sample_rows, raw


def audit_thesportsdb() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "TheSportsDB public API"
    api_key = os.environ.get("THESPORTSDB_KEY") or "3"

    report_rows = []
    sample_rows = []
    raw = {}

    for d in date_strings():
        endpoint = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsday.php"
        data, status, error = request_json(endpoint, params={"d": d["iso"]})
        time.sleep(REQUEST_SLEEP_SECONDS)

        events = data.get("events") if isinstance(data, dict) else []
        events = events or []
        samples = []
        relevant = 0

        for event in events[:75]:
            name = clean(event.get("strEvent") or event.get("strFilename"))
            league = clean(event.get("strLeague"))
            sport = clean(event.get("strSport"))
            status_text = clean(event.get("strStatus"))
            home_score = clean(event.get("intHomeScore"))
            away_score = clean(event.get("intAwayScore"))
            score = f"{away_score}-{home_score}" if away_score or home_score else ""
            event_id = clean(event.get("idEvent"))
            full_text = " ".join([name, league, sport])
            likely = is_likely_womens_event(full_text)
            if likely:
                relevant += 1
            samples.append(f"{name} | {league} | {sport} | {score}")
            sample_rows.append(event_sample_row(
                source_name, sport or "All sports", d["iso"], name, status_text, score,
                league, event_id,
                f"https://www.thesportsdb.com/event/{event_id}" if event_id else "",
                likely_womens=likely,
                date_match="Unknown",
                raw_note="Broad public API eventday endpoint.",
            ))

        raw[f"thesportsdb::{d['iso']}"] = {
            "status": status,
            "error": error,
            "event_count": len(events),
            "api_key_used": "secret_or_public",
            "keys": list(data.keys()) if isinstance(data, dict) else [],
        }

        report_rows.append(make_report_row(
            source_name, "All sports", d["iso"], f"{endpoint}?d={d['iso']}", status,
            status == 200 and isinstance(data, dict), len(events), relevant, samples,
            "Broad event discovery, team/league metadata, scores when available.",
            recommendation(source_name, len(events), relevant, status_code=status),
            error or "Uses THESPORTSDB_KEY if set, otherwise public test key 3.",
            raw_events_found=len(events),
            date_matched_events=len(events),
        ))

    return report_rows, sample_rows, raw


def audit_api_sports_optional() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "API-Sports optional"
    key = os.environ.get("APISPORTS_KEY", "")
    if not key:
        row = make_report_row(
            source_name, "Optional paid/free-key APIs", "n/a", "APISPORTS_KEY not set",
            0, False, 0, 0, [], "Potential broad structured coverage if API key is available.",
            "Evaluate later with key", "Set APISPORTS_KEY in GitHub Secrets to test this source.",
        )
        return [row], [], {"enabled": False, "reason": "APISPORTS_KEY not set"}

    report_rows = []
    sample_rows = []
    raw = {}
    headers = {"x-apisports-key": key}

    # Test basketball first. Add more API-Sports products later if key proves useful.
    for d in date_strings():
        endpoint = "https://v1.basketball.api-sports.io/games"
        data, status, error = request_json(endpoint, params={"date": d["iso"]}, headers=headers)
        time.sleep(REQUEST_SLEEP_SECONDS)

        events = data.get("response") if isinstance(data, dict) else []
        events = events or []
        samples = []
        relevant = 0

        for event in events[:75]:
            league = clean(((event.get("league") or {}).get("name")))
            country = clean(((event.get("country") or {}).get("name")))
            teams = event.get("teams") or {}
            home = clean(((teams.get("home") or {}).get("name")))
            away = clean(((teams.get("away") or {}).get("name")))
            scores = event.get("scores") or {}
            home_score = clean(((scores.get("home") or {}).get("total")))
            away_score = clean(((scores.get("away") or {}).get("total")))
            status_text = clean(((event.get("status") or {}).get("long") or (event.get("status") or {}).get("short")))
            event_id = clean(event.get("id"))
            name = f"{away} vs {home}"
            score = f"{away_score}-{home_score}" if away_score or home_score else ""
            full_text = " ".join([name, league, country, "basketball"])
            likely = is_likely_womens_event(full_text)
            if likely:
                relevant += 1
            samples.append(f"{name} | {league} | {country} | {score}")
            sample_rows.append(event_sample_row(
                source_name, "Basketball", d["iso"], name, status_text, score,
                " | ".join([league, country]), event_id, endpoint,
                likely_womens=likely,
                date_match="Unknown",
                raw_note="API-Sports Basketball endpoint.",
            ))

        raw[f"apisports_basketball::{d['iso']}"] = {
            "status": status,
            "error": error,
            "event_count": len(events),
        }

        report_rows.append(make_report_row(
            source_name, "Basketball", d["iso"], f"{endpoint}?date={d['iso']}", status,
            status == 200 and isinstance(data, dict), len(events), relevant, samples,
            "Structured live scores/schedules with API key.",
            recommendation(source_name, len(events), relevant, status_code=status),
            error or "APISPORTS_KEY was set and basketball endpoint was tested.",
        ))

    return report_rows, sample_rows, raw


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(report_rows: List[Dict[str, str]]) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    by_source: Dict[str, Dict[str, int]] = {}

    for row in report_rows:
        source = row["source_name"]
        by_source.setdefault(source, {"tests": 0, "ok": 0, "events": 0, "raw": 0, "fresh": 0, "stale": 0, "women": 0})
        by_source[source]["tests"] += 1
        by_source[source]["ok"] += 1 if row["ok"] == "Yes" else 0
        by_source[source]["events"] += int(row["events_found"] or 0)
        by_source[source]["raw"] += int(row["raw_events_found"] or 0)
        by_source[source]["fresh"] += int(row["date_matched_events"] or 0)
        by_source[source]["stale"] += int(row["stale_events_found"] or 0)
        by_source[source]["women"] += int(row["likely_womens_events"] or 0)

    lines = [
        "# Her Sports Daily Results Source Audit v2",
        "",
        f"Generated: `{generated}`",
        "",
        "## Purpose",
        "",
        "This audit tests which sources are worth using for Results Desk v3.",
        "v2 specifically checks for blocked sources, stale/default college data, and blank API-key mistakes.",
        "",
        "## Date window tested",
        "",
        ", ".join(d["iso"] for d in date_strings()),
        "",
        "## Source summary",
        "",
        "| Source | Tests | Successful Tests | Usable Events | Raw Events | Date-Matched Events | Stale Events Rejected | Likely Women's Events |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for source, stats in sorted(by_source.items()):
        lines.append(
            f"| {source} | {stats['tests']} | {stats['ok']} | {stats['events']} | "
            f"{stats['raw']} | {stats['fresh']} | {stats['stale']} | {stats['women']} |"
        )

    lines.extend([
        "",
        "## Key interpretation rules",
        "",
        "- **Usable Events** is the count we should care about for Results Desk v3.",
        "- **Raw Events** may include stale/default events.",
        "- **Stale Events Rejected** is critical for NCAA sources because some endpoints return championship results regardless of query date.",
        "- SofaScore returning 403 means GitHub Actions cannot currently use that public endpoint directly.",
        "- API-Sports will only test if `APISPORTS_KEY` is set in GitHub Secrets.",
        "",
        "## Files created",
        "",
        f"- `{OUTPUT_REPORT}`",
        f"- `{OUTPUT_SAMPLES}`",
        f"- `{OUTPUT_RAW}`",
        "",
        "## Next build decision",
        "",
        "Use sources only if they return usable/date-matched events. Discovery sources can suggest games, but final result graphics still need structured or official verification.",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    all_report_rows: List[Dict[str, str]] = []
    all_sample_rows: List[Dict[str, str]] = []
    all_raw: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_window": date_strings(),
    }

    audits = [
        ("sofascore", audit_sofascore),
        ("espn", audit_espn),
        ("ncaa_api", audit_ncaa_api),
        ("thesportsdb", audit_thesportsdb),
        ("api_sports_optional", audit_api_sports_optional),
    ]

    for audit_name, audit_func in audits:
        print(f"Running audit: {audit_name}")
        try:
            report_rows, sample_rows, raw = audit_func()
        except Exception as exc:
            report_rows = [make_report_row(
                audit_name, "audit_failed", "n/a", "n/a", 0, False, 0, 0, [],
                "n/a", "Do not use yet", f"Audit failed: {exc}",
            )]
            sample_rows = []
            raw = {"error": str(exc)}

        all_report_rows.extend(report_rows)
        all_sample_rows.extend(sample_rows)
        all_raw[audit_name] = raw

    report_fields = [
        "source_name", "sport_or_league", "date", "endpoint", "http_status", "ok",
        "events_found", "raw_events_found", "date_matched_events", "stale_events_found",
        "likely_womens_events", "women_relevance_score", "sample_events",
        "capabilities", "recommended_role", "notes",
    ]
    sample_fields = [
        "source_name", "sport_or_league", "date", "event_id", "event_name",
        "status", "score", "tournament", "source_url", "likely_womens",
        "date_match", "raw_note",
    ]

    write_csv(OUTPUT_REPORT, all_report_rows, report_fields)
    write_csv(OUTPUT_SAMPLES, all_sample_rows, sample_fields)
    Path(OUTPUT_RAW).write_text(json.dumps(all_raw, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(OUTPUT_SUMMARY).write_text(summarize(all_report_rows), encoding="utf-8")

    print(f"Created {OUTPUT_REPORT}")
    print(f"Created {OUTPUT_SAMPLES}")
    print(f"Created {OUTPUT_SUMMARY}")
    print(f"Created {OUTPUT_RAW}")


if __name__ == "__main__":
    main()
