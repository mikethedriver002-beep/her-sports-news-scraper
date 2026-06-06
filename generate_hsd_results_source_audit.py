
"""
Her Sports Daily Results Source Audit
-------------------------------------

Purpose:
Test which score/result sources are actually useful for women's sports before
rebuilding the Results Desk v3.

This is NOT the final results scraper.
This is a source discovery / coverage tester.

It creates:
- source_coverage_report.csv
- source_event_samples.csv
- source_audit_summary.md
- source_audit_raw.json

Sources tested:
- SofaScore public HTTP endpoints, unofficial, wide coverage
- ESPN public scoreboard endpoints, structured but narrow
- NCAA API / NCAA.com-derived endpoints, college-focused
- TheSportsDB public API, broad metadata/discovery
- API-Sports optional tests, only if APISPORTS_KEY is set

Accuracy philosophy:
- A source audit is allowed to discover possible games.
- A final result graphic still requires official or structured verification.
- This script records source role recommendations, not final publishing decisions.
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailySourceAudit/1.0; +https://github.com/)"
}


WOMENS_TERMS = [
    "women", "women's", "womens", "female", "girls", "wnba", "nwsl", "pwhl",
    "lpga", "wta", "uswnt", "ncaa women", "ncaa women's", "feminine",
]

TARGET_TERMS = [
    "wnba", "ncaa", "women", "women's", "womens", "softball", "nwsl", "pwhl",
    "lpga", "wta", "volleyball", "soccer", "basketball", "hockey", "tennis",
]

TIER_NOTES = {
    "Discovery": "Good for finding games/events, but needs verification before graphic use.",
    "Verification": "Can be used to verify score/status when structured and current.",
    "Box Score": "May provide player/team stats for graphic packets.",
    "Metadata": "Useful for league/team IDs, names, schedules, or logos.",
}


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
            "sofa": d.strftime("%Y-%m-%d"),
        })
    return out


def request_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[Any], int, str]:
    try:
        response = requests.get(url, params=params or {}, headers=headers or HEADERS, timeout=25)
        status = response.status_code
        text = response.text[:300]
        response.raise_for_status()
        return response.json(), status, ""
    except Exception as exc:
        return None, 0 if "response" not in locals() else response.status_code, str(exc)


def relevance_score(text: str) -> int:
    s = low(text)
    score = 0
    score += 5 * sum(1 for term in WOMENS_TERMS if term in s)
    score += 2 * sum(1 for term in TARGET_TERMS if term in s)
    return score


def is_likely_womens_event(text: str) -> bool:
    return relevance_score(text) >= 5


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


def classify_recommendation(events_found: int, relevant_events: int, has_box: bool, source_name: str) -> str:
    if events_found == 0:
        return "Do not use yet"
    if "SofaScore" in source_name and relevant_events > 0:
        return "Strong discovery candidate"
    if "NCAA" in source_name and events_found > 0:
        return "College verification candidate"
    if "ESPN" in source_name and events_found > 0:
        return "Structured verification candidate"
    if "TheSportsDB" in source_name and events_found > 0:
        return "Metadata/discovery candidate"
    if has_box:
        return "Box score candidate"
    return "Needs review"


def make_report_row(
    source_name: str,
    sport_or_league: str,
    date_label: str,
    endpoint: str,
    status_code: int,
    ok: bool,
    events_found: int,
    relevant_events: int,
    sample_events: List[str],
    capabilities: str,
    recommended_role: str,
    notes: str,
) -> Dict[str, str]:
    return {
        "source_name": source_name,
        "sport_or_league": sport_or_league,
        "date": date_label,
        "endpoint": endpoint,
        "http_status": str(status_code),
        "ok": "Yes" if ok else "No",
        "events_found": str(events_found),
        "likely_womens_events": str(relevant_events),
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
    raw_note: str = "",
) -> Dict[str, str]:
    return {
        "source_name": source_name,
        "sport_or_league": sport_or_league,
        "date": date_label,
        "event_id": event_id,
        "event_name": clean(event_name),
        "status": clean(status),
        "score": clean(score),
        "tournament": clean(tournament),
        "source_url": clean(source_url),
        "likely_womens": "Yes" if is_likely_womens_event(" ".join([event_name, tournament])) else "No",
        "raw_note": clean(raw_note),
    }


def audit_sofascore() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    """
    SofaScore public HTTP endpoints are unofficial for our purposes.
    This tests the broad scheduled-events endpoint by sport/date.

    Common pattern:
    https://api.sofascore.com/api/v1/sport/{sport}/scheduled-events/{YYYY-MM-DD}
    """
    source_name = "SofaScore public endpoints"
    sports = [
        "basketball", "football", "tennis", "volleyball", "ice-hockey",
        "handball", "cricket", "rugby", "baseball",
    ]

    report_rows = []
    sample_rows = []
    raw = {}

    for sport in sports:
        for d in date_strings():
            endpoint = f"https://api.sofascore.com/api/v1/sport/{sport}/scheduled-events/{d['sofa']}"
            data, status, error = request_json(endpoint)
            time.sleep(REQUEST_SLEEP_SECONDS)

            events = []
            if isinstance(data, dict):
                events = data.get("events") or []
            raw_key = f"sofascore::{sport}::{d['iso']}"
            raw[raw_key] = {
                "status": status,
                "error": error,
                "event_count": len(events),
                "first_event_keys": list(events[0].keys()) if events else [],
            }

            samples = []
            relevant_count = 0
            for event in events:
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
                if is_likely_womens_event(full_text):
                    relevant_count += 1
                if len(samples) < 10:
                    samples.append(f"{name} | {tournament} | {category} | {status_text}")
                if len(sample_rows) < 1000:
                    score = f"{away_score}-{home_score}" if away_score or home_score else ""
                    sample_rows.append(event_sample_row(
                        source_name, sport, d["iso"], name, status_text, score,
                        " | ".join([tournament, category]), event_id,
                        f"https://www.sofascore.com/event/{event_id}" if event_id else "",
                        "Unofficial endpoint. Use as discovery unless verified elsewhere.",
                    ))

            has_box = False
            report_rows.append(make_report_row(
                source_name=source_name,
                sport_or_league=sport,
                date_label=d["iso"],
                endpoint=endpoint,
                status_code=status,
                ok=status == 200 and isinstance(data, dict),
                events_found=len(events),
                relevant_events=relevant_count,
                sample_events=samples,
                capabilities="Wide event discovery, live/final status, basic score. Box stats may require event-specific endpoints.",
                recommended_role=classify_recommendation(len(events), relevant_count, has_box, source_name),
                notes=error or "Tested scheduled-events endpoint. Treat as unofficial and rate-limit carefully.",
            ))

    return report_rows, sample_rows, raw


def audit_espn() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "ESPN public scoreboard"
    leagues = [
        ("WNBA", "basketball", "wnba"),
        ("NCAA Women's Basketball", "basketball", "womens-college-basketball"),
        ("NCAA Softball", "softball", "college-softball"),
        ("NWSL", "soccer", "usa.nwsl"),
        ("NCAA Women's Volleyball", "volleyball", "womens-college-volleyball"),
        ("NCAA Women's Soccer", "soccer", "womens-college-soccer"),
    ]

    report_rows = []
    sample_rows = []
    raw = {}

    for label, sport, league in leagues:
        for d in date_strings():
            endpoint = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
            params = {"dates": d["compact"]}
            data, status, error = request_json(endpoint, params=params)
            time.sleep(REQUEST_SLEEP_SECONDS)

            events = []
            if isinstance(data, dict):
                events = data.get("events") or []

            raw_key = f"espn::{label}::{d['iso']}"
            raw[raw_key] = {
                "status": status,
                "error": error,
                "event_count": len(events),
                "keys": list(data.keys()) if isinstance(data, dict) else [],
            }

            samples = []
            relevant_count = 0
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
                        t = clean(((team.get("team") or {}).get("shortDisplayName") or (team.get("team") or {}).get("displayName")))
                        s = clean(team.get("score"))
                        if t or s:
                            parts.append(f"{t} {s}".strip())
                    score = " - ".join(parts)
                full_text = " ".join([label, name, sport, league])
                if is_likely_womens_event(full_text):
                    relevant_count += 1
                if len(samples) < 10:
                    samples.append(f"{name} | {status_text} | {score}")
                sample_rows.append(event_sample_row(
                    source_name, label, d["iso"], name, status_text, score,
                    label, event_id,
                    f"https://www.espn.com/{sport}/game/_/gameId/{event_id}" if event_id else "",
                    "Structured ESPN scoreboard response.",
                ))

            report_rows.append(make_report_row(
                source_name=source_name,
                sport_or_league=label,
                date_label=d["iso"],
                endpoint=f"{endpoint}?dates={d['compact']}",
                status_code=status,
                ok=status == 200 and isinstance(data, dict),
                events_found=len(events),
                relevant_events=relevant_count,
                sample_events=samples,
                capabilities="Structured scoreboard, status, scores, some summary/box score endpoints.",
                recommended_role=classify_recommendation(len(events), relevant_count, True, source_name),
                notes=error or "Date-specific scoreboard test.",
            ))

    return report_rows, sample_rows, raw


def audit_ncaa_api() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    """
    NCAA API is a community/open-source API returning consumable ncaa.com data.
    Its exact sport/division endpoint shape can evolve, so this audit tries
    multiple candidate endpoint patterns.
    """
    source_name = "NCAA API / ncaa.com-derived"
    base = "https://ncaa-api.henrygd.me"
    candidates = []
    sports = [
        ("DI Softball", "softball", "d1"),
        ("DII Softball", "softball", "d2"),
        ("DIII Softball", "softball", "d3"),
        ("DI Women's Basketball", "basketball-women", "d1"),
        ("DI Women's Volleyball", "volleyball-women", "d1"),
        ("DI Women's Soccer", "soccer-women", "d1"),
    ]

    for label, sport, division in sports:
        for d in date_strings():
            candidates.extend([
                (label, d["iso"], f"{base}/scoreboard/{sport}/{division}/{d['iso']}"),
                (label, d["iso"], f"{base}/scoreboard/{sport}/{division}/{d['compact']}"),
                (label, d["iso"], f"{base}/scoreboard/{division}/{sport}/{d['iso']}"),
                (label, d["iso"], f"{base}/game/scoreboard/{sport}/{division}/{d['iso']}"),
            ])

    report_rows = []
    sample_rows = []
    raw = {}

    for label, date_label, endpoint in candidates:
        data, status, error = request_json(endpoint)
        time.sleep(REQUEST_SLEEP_SECONDS)

        # Extract events flexibly.
        events = []
        if isinstance(data, dict):
            for key in ["games", "events", "scoreboard", "data"]:
                val = data.get(key)
                if isinstance(val, list):
                    events = val
                    break
                if isinstance(val, dict):
                    for subkey in ["games", "events"]:
                        if isinstance(val.get(subkey), list):
                            events = val.get(subkey)
                            break
                if events:
                    break
        elif isinstance(data, list):
            events = data

        raw_key = f"ncaa::{label}::{date_label}::{endpoint}"
        raw[raw_key] = {
            "status": status,
            "error": error,
            "event_count": len(events),
            "data_type": type(data).__name__,
            "top_keys": list(data.keys()) if isinstance(data, dict) else [],
        }

        samples = []
        relevant_count = 0
        for event in events[:20]:
            if isinstance(event, dict):
                name = clean(event.get("title") or event.get("game") or event.get("name") or event.get("contestName") or json.dumps(event)[:120])
                status_text = clean(event.get("gameState") or event.get("status") or event.get("gameStatus"))
                score = clean(event.get("score") or event.get("gameScore"))
                event_id = clean(event.get("gameID") or event.get("gameId") or event.get("id"))
            else:
                name = clean(event)
                status_text = ""
                score = ""
                event_id = ""

            full_text = " ".join([label, name])
            if is_likely_womens_event(full_text):
                relevant_count += 1
            samples.append(f"{name} | {status_text} | {score}")
            sample_rows.append(event_sample_row(
                source_name, label, date_label, name, status_text, score,
                label, event_id, endpoint,
                "Candidate NCAA API endpoint.",
            ))

        report_rows.append(make_report_row(
            source_name=source_name,
            sport_or_league=label,
            date_label=date_label,
            endpoint=endpoint,
            status_code=status,
            ok=status == 200 and data is not None,
            events_found=len(events),
            relevant_events=relevant_count,
            sample_events=samples,
            capabilities="College scoreboard/game details if endpoint works. Good verification candidate for NCAA sports.",
            recommended_role=classify_recommendation(len(events), relevant_count, True, source_name),
            notes=error or "Candidate endpoint tested.",
        ))

    return report_rows, sample_rows, raw


def audit_thesportsdb() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "TheSportsDB public API"
    api_key = os.environ.get("THESPORTSDB_KEY", "3")  # 3 is the public test key historically used by docs/examples.
    report_rows = []
    sample_rows = []
    raw = {}

    for d in date_strings():
        endpoint = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsday.php"
        params = {"d": d["iso"]}
        data, status, error = request_json(endpoint, params=params)
        time.sleep(REQUEST_SLEEP_SECONDS)

        events = []
        if isinstance(data, dict):
            events = data.get("events") or []
        raw_key = f"thesportsdb::{d['iso']}"
        raw[raw_key] = {
            "status": status,
            "error": error,
            "event_count": len(events),
            "keys": list(data.keys()) if isinstance(data, dict) else [],
        }

        samples = []
        relevant_count = 0
        for event in events[:50]:
            name = clean(event.get("strEvent") or event.get("strFilename"))
            league = clean(event.get("strLeague"))
            sport = clean(event.get("strSport"))
            status_text = clean(event.get("strStatus"))
            home_score = clean(event.get("intHomeScore"))
            away_score = clean(event.get("intAwayScore"))
            score = f"{away_score}-{home_score}" if away_score or home_score else ""
            event_id = clean(event.get("idEvent"))
            full_text = " ".join([name, league, sport])
            if is_likely_womens_event(full_text):
                relevant_count += 1
            samples.append(f"{name} | {league} | {sport} | {score}")
            sample_rows.append(event_sample_row(
                source_name, sport or "All sports", d["iso"], name, status_text, score,
                league, event_id,
                f"https://www.thesportsdb.com/event/{event_id}" if event_id else "",
                "Broad public API eventday endpoint.",
            ))

        report_rows.append(make_report_row(
            source_name=source_name,
            sport_or_league="All sports",
            date_label=d["iso"],
            endpoint=f"{endpoint}?d={d['iso']}",
            status_code=status,
            ok=status == 200 and isinstance(data, dict),
            events_found=len(events),
            relevant_events=relevant_count,
            sample_events=samples,
            capabilities="Broad event discovery, team/league metadata, scores when available.",
            recommended_role=classify_recommendation(len(events), relevant_count, False, source_name),
            notes=error or "Uses THESPORTSDB_KEY env var if set, otherwise public key 3.",
        ))

    return report_rows, sample_rows, raw


def audit_api_sports_optional() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    source_name = "API-Sports optional"
    key = os.environ.get("APISPORTS_KEY", "")
    if not key:
        row = make_report_row(
            source_name=source_name,
            sport_or_league="Optional paid/free-key APIs",
            date_label="n/a",
            endpoint="APISPORTS_KEY not set",
            status_code=0,
            ok=False,
            events_found=0,
            relevant_events=0,
            sample_events=[],
            capabilities="Potential broad structured coverage if API key is available.",
            recommended_role="Evaluate later with key",
            notes="Set APISPORTS_KEY in GitHub Secrets to test this source.",
        )
        return [row], [], {"api_sports": {"enabled": False, "reason": "APISPORTS_KEY not set"}}

    report_rows = []
    sample_rows = []
    raw = {}

    # Basketball endpoint example from API-Basketball.
    headers = {"x-apisports-key": key}
    for d in date_strings():
        endpoint = "https://v1.basketball.api-sports.io/games"
        params = {"date": d["iso"]}
        data, status, error = request_json(endpoint, params=params, headers=headers)
        time.sleep(REQUEST_SLEEP_SECONDS)

        events = []
        if isinstance(data, dict):
            events = data.get("response") or []

        raw_key = f"apisports_basketball::{d['iso']}"
        raw[raw_key] = {
            "status": status,
            "error": error,
            "event_count": len(events),
            "keys": list(data.keys()) if isinstance(data, dict) else [],
        }

        samples = []
        relevant_count = 0
        for event in events[:50]:
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
            if is_likely_womens_event(full_text):
                relevant_count += 1
            samples.append(f"{name} | {league} | {country} | {score}")
            sample_rows.append(event_sample_row(
                source_name, "Basketball", d["iso"], name, status_text, score,
                " | ".join([league, country]), event_id, endpoint,
                "API-Sports Basketball test.",
            ))

        report_rows.append(make_report_row(
            source_name=source_name,
            sport_or_league="Basketball",
            date_label=d["iso"],
            endpoint=f"{endpoint}?date={d['iso']}",
            status_code=status,
            ok=status == 200 and isinstance(data, dict),
            events_found=len(events),
            relevant_events=relevant_count,
            sample_events=samples,
            capabilities="Structured live scores/schedules with API key.",
            recommended_role=classify_recommendation(len(events), relevant_count, True, source_name),
            notes=error or "APISPORTS_KEY was set and basketball endpoint was tested.",
        ))

    return report_rows, sample_rows, raw


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(report_rows: List[Dict[str, str]], sample_rows: List[Dict[str, str]]) -> str:
    generated = datetime.now(timezone.utc).isoformat()

    by_source: Dict[str, Dict[str, int]] = {}
    for row in report_rows:
        source = row["source_name"]
        by_source.setdefault(source, {"tests": 0, "ok": 0, "events": 0, "women": 0})
        by_source[source]["tests"] += 1
        by_source[source]["ok"] += 1 if row["ok"] == "Yes" else 0
        by_source[source]["events"] += int(row["events_found"] or 0)
        by_source[source]["women"] += int(row["likely_womens_events"] or 0)

    lines = [
        "# Her Sports Daily Results Source Audit",
        "",
        f"Generated: `{generated}`",
        "",
        "## Purpose",
        "",
        "This audit tests which sources are worth using for the next Results Desk rebuild.",
        "It does not decide what to post. It measures source coverage, event access, women's-sports relevance, and possible role.",
        "",
        "## Date window tested",
        "",
        ", ".join(d["iso"] for d in date_strings()),
        "",
        "## Source summary",
        "",
        "| Source | Tests | Successful Tests | Events Found | Likely Women's Events |",
        "|---|---:|---:|---:|---:|",
    ]

    for source, stats in sorted(by_source.items()):
        lines.append(f"| {source} | {stats['tests']} | {stats['ok']} | {stats['events']} | {stats['women']} |")

    lines.extend([
        "",
        "## How to read this",
        "",
        "- **Events Found** means the endpoint returned events. It does not mean the source is ready for final graphics.",
        "- **Likely Women's Events** is a keyword-based signal, not a final truth label.",
        "- **Recommended Role** in the CSV tells us whether a source looks better for discovery, verification, box scores, or metadata.",
        "",
        "## Next build decision",
        "",
        "Use the highest-coverage discovery source to find events, then verify final scores with official or structured sources.",
        "For result graphics, do not use one unofficial source alone unless it is clearly structured and later verified.",
        "",
        "## Files created",
        "",
        f"- `{OUTPUT_REPORT}`",
        f"- `{OUTPUT_SAMPLES}`",
        f"- `{OUTPUT_RAW}`",
        "",
        "## Early recommendation",
        "",
        "If SofaScore returns broad event coverage in this audit, use it as a discovery layer.",
        "If NCAA API returns college sport events, use it as the NCAA verification layer.",
        "Keep ESPN as a secondary structured source, not the whole Results Desk.",
        "Use API-Sports only if an API key is available and coverage is clearly better.",
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
                source_name=audit_name,
                sport_or_league="audit_failed",
                date_label="n/a",
                endpoint="n/a",
                status_code=0,
                ok=False,
                events_found=0,
                relevant_events=0,
                sample_events=[],
                capabilities="n/a",
                recommended_role="Do not use yet",
                notes=f"Audit failed: {exc}",
            )]
            sample_rows = []
            raw = {"error": str(exc)}

        all_report_rows.extend(report_rows)
        all_sample_rows.extend(sample_rows)
        all_raw[audit_name] = raw

    report_fields = [
        "source_name", "sport_or_league", "date", "endpoint", "http_status", "ok",
        "events_found", "likely_womens_events", "women_relevance_score",
        "sample_events", "capabilities", "recommended_role", "notes",
    ]
    sample_fields = [
        "source_name", "sport_or_league", "date", "event_id", "event_name",
        "status", "score", "tournament", "source_url", "likely_womens", "raw_note",
    ]

    write_csv(OUTPUT_REPORT, all_report_rows, report_fields)
    write_csv(OUTPUT_SAMPLES, all_sample_rows, sample_fields)
    Path(OUTPUT_RAW).write_text(json.dumps(all_raw, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(OUTPUT_SUMMARY).write_text(summarize(all_report_rows, all_sample_rows), encoding="utf-8")

    print(f"Created {OUTPUT_REPORT}")
    print(f"Created {OUTPUT_SAMPLES}")
    print(f"Created {OUTPUT_SUMMARY}")
    print(f"Created {OUTPUT_RAW}")


if __name__ == "__main__":
    main()
