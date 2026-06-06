
from __future__ import annotations

import csv
import json
import os
import re
import hashlib
import requests
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


VERSION = "v4.2"

RESULTS_TIMEZONE = os.environ.get("HSD_TIMEZONE", "America/New_York")
LOOKBACK_DAYS = int(os.environ.get("HSD_LOOKBACK_DAYS", "1"))
LOOKAHEAD_DAYS = int(os.environ.get("HSD_LOOKAHEAD_DAYS", "1"))
REQUEST_SLEEP_SECONDS = 0.25

OBSERVATIONS_FILE = "source_observations.csv"
RECONCILED_FILE = "reconciled_events.csv"
RESULTS_BOARD_FILE = "today_results_board.csv"
WOMENS_RESULTS_FILE = "today_womens_results.csv"
FINAL_RESULTS_FILE = "today_final_results.csv"
TOP_RESULTS_FILE = "top_womens_results.csv"
MANUAL_REVIEW_FILE = "manual_review_queue.csv"
SOURCE_HEALTH_FILE = "source_health_report.csv"
GRAPHICS_QUEUE_FILE = "results_graphics_queue.md"
RECOMMENDATIONS_FILE = "daily_results_recommendations.md"
HUB_FILE = "results_system_hub.md"
MANIFEST_FILE = "run_manifest.json"

WOMENS_TERMS = [
    "women", "women's", "womens", "female", "girls", "wnba", "nwsl", "pwhl",
    "lpga", "wta", "uswnt", "ncaa women", "ncaa women's", "softball",
    "feminine", "femenina", "femenino", "frauen", "damen", "w-league",
    "a-league women", "women super league", "women's super league",
    "liga mx femenil", "champions league women", "uefa women's", "uwcl",
    "national women's soccer league", "volleyball nations league women",
    "world cup women", "women world cup",
]

DRAW_ALLOWED_SPORTS = {"soccer", "rugby", "handball", "hockey"}

TIER_1_TERMS = [
    "wnba", "nwsl", "uswnt", "world cup", "women's world cup", "women world cup",
    "euro", "uefa women's", "uwcl", "volleyball nations league", "nations league",
    "ncaa championship", "ncaa tournament", "olympic", "olympics",
]

TIER_2_TERMS = [
    "women", "women's", "womens", "femenina", "femenil", "u23", "u21", "u20",
    "friendly", "qualification", "qualifiers", "cup", "league",
]

EDITORIAL_TERMS = {
    "wnba": 200,
    "nba w": 200,
    "nwsl": 120,
    "uswnt": 125,
    "world cup": 86,
    "volleyball nations league": 88,
    "ncaa": 90,
    "basketball": 78,
    "soccer": 76,
    "volleyball": 70,
    "rugby": 54,
    "handball": 50,
}

WNBA_LEAGUE_ALIASES = {
    "wnba", "nba w", "nba women", "women nba", "womens nba",
    "women's national basketball association", "womens national basketball association",
}

WNBA_TEAM_ROOTS = {
    "atlanta dream", "chicago sky", "connecticut sun", "dallas wings", "golden state valkyries",
    "indiana fever", "las vegas aces", "los angeles sparks", "minnesota lynx", "new york liberty",
    "phoenix mercury", "portland fire", "seattle storm", "washington mystics",
}

LOW_PRIORITY_LEAGUE_TERMS = {
    "nbl1", "lbf w", "seven's world series", "sevens world series", "state league",
    "regional", "u18", "u19", "u20 club", "u21 club",
}

PRODUCTS = [
    {"product": "basketball", "sport": "basketball", "label": "Basketball", "endpoint": "https://v1.basketball.api-sports.io/games"},
    {"product": "football", "sport": "soccer", "label": "Soccer", "endpoint": "https://v3.football.api-sports.io/fixtures"},
    {"product": "volleyball", "sport": "volleyball", "label": "Volleyball", "endpoint": "https://v1.volleyball.api-sports.io/games"},
    {"product": "rugby", "sport": "rugby", "label": "Rugby", "endpoint": "https://v1.rugby.api-sports.io/games"},
    {"product": "handball", "sport": "handball", "label": "Handball", "endpoint": "https://v1.handball.api-sports.io/games"},
    {"product": "hockey", "sport": "hockey", "label": "Hockey", "endpoint": "https://v1.hockey.api-sports.io/games"},
    {"product": "baseball", "sport": "baseball", "label": "Baseball", "endpoint": "https://v1.baseball.api-sports.io/games"},
]

OBS_FIELDS = [
    "run_id", "source_name", "source_priority", "source_event_id", "canonical_key",
    "sport_norm", "league_norm", "competition_id", "gender_scope", "scheduled_start_utc",
    "scheduled_date_local", "home_team_raw", "away_team_raw", "home_team_norm",
    "away_team_norm", "status_raw", "status_norm", "home_score", "away_score",
    "score_by_period_json", "team_stats_json", "player_stats_json", "top_performers_json",
    "source_url", "fetched_at_utc", "http_status", "parse_ok", "stale_rejected",
    "women_match_method", "raw_archive_path", "notes",
]

EVENT_FIELDS = [
    "run_id", "event_uid", "canonical_key", "selected_source", "source_count",
    "all_sources_json", "sport_norm", "league_norm", "gender_scope", "scheduled_start_utc",
    "scheduled_date_local", "home_team_norm", "away_team_norm", "home_team_display",
    "away_team_display", "final_score_display", "game_state", "status_norm",
    "home_score", "away_score", "winner", "loser", "outcome_type",
    "editorial_tier", "editorial_bucket", "content_action", "content_family",
    "posting_priority", "caption_seed", "score_by_period_json",
    "team_stats_json", "player_stats_json", "top_performers_json", "confidence",
    "confidence_reason_json", "score_conflict", "manual_review", "include_in_dashboard",
    "include_in_graphics", "editorial_rank", "graphics_headline", "graphics_subhead",
    "source_url", "source_priority",
]


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def low(value: Any) -> str:
    return clean(value).lower()


def slug(value: Any) -> str:
    s = low(value)
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_team(value: Any) -> str:
    s = slug(value)
    replacements = {
        "united states": "usa",
        "u s a": "usa",
        "us": "usa",
        "women": "w",
        "womens": "w",
        "women s": "w",
        "ladies": "w",
    }
    for src, dst in replacements.items():
        s = re.sub(rf"\b{re.escape(src)}\b", dst, s)
    return re.sub(r"\s+", " ", s).strip()


def is_wnba_league(league: Any, sport: Any = "") -> bool:
    s = slug(league)
    return clean(sport).lower() == "basketball" and s in {slug(x) for x in WNBA_LEAGUE_ALIASES}


def is_wnba_team_name(team: Any) -> bool:
    s = normalize_team(team)
    s_no_w = re.sub(r"\bw$", "", s).strip()
    return s_no_w in WNBA_TEAM_ROOTS


def normalize_league_name(league: Any, sport: Any = "") -> str:
    raw = clean(league)
    if is_wnba_league(raw, sport):
        return "WNBA"
    return raw or "Unknown League"


def normalize_team_for_context(team: Any, league: Any = "", sport: Any = "") -> str:
    s = normalize_team(team)
    if normalize_league_name(league, sport) == "WNBA" or is_wnba_team_name(team):
        s = re.sub(r"\bw$", "", s).strip()
    return s


def display_team_for_context(team: Any, league: Any = "", sport: Any = "") -> str:
    value = clean(team)
    if normalize_league_name(league, sport) == "WNBA" or is_wnba_team_name(value):
        value = re.sub(r"\s+W$", "", value).strip()
    return value


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def date_window() -> Tuple[List[str], List[str]]:
    if ZoneInfo is not None:
        today = datetime.now(ZoneInfo(RESULTS_TIMEZONE)).date()
    else:
        today = datetime.now(timezone.utc).date()
    iso_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]
    compact_dates = [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]
    return iso_dates, compact_dates


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


def normalize_status(value: Any) -> str:
    s = low(value)
    if any(x in s for x in ["finished", "match finished", "after fulltime", "after overtime", "final", "ft", "aet", "ended"]):
        return "final"
    if any(x in s for x in ["live", "in progress", "quarter", "half", "period", "set", "inning"]):
        return "live"
    if any(x in s for x in ["not started", "scheduled", "pre match", "pre-match", "time to be defined", "ns"]):
        return "scheduled"
    if any(x in s for x in ["postponed", "cancelled", "canceled", "suspended", "abandoned"]):
        return "not_played"
    return s or "unknown"


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if clean(value) == "":
            return default
        return int(float(str(value)))
    except Exception:
        return default


def score_present(home_score: Any, away_score: Any) -> bool:
    return clean(home_score) != "" and clean(away_score) != ""


def score_winner(home: str, away: str, home_score: Any, away_score: Any) -> Tuple[str, str]:
    h = safe_int(home_score)
    a = safe_int(away_score)
    if h is None or a is None:
        return "", ""
    if h > a:
        return clean(home), clean(away)
    if a > h:
        return clean(away), clean(home)
    return "", ""


def score_equal(home_score: Any, away_score: Any) -> bool:
    h = safe_int(home_score)
    a = safe_int(away_score)
    return h is not None and a is not None and h == a


def women_scope_and_method(*parts: Any) -> Tuple[str, str]:
    blob = " ".join(clean(p) for p in parts if clean(p))
    s = low(blob)
    if not s:
        return "unknown", "none"

    explicit_patterns = [
        r"\bwomen\b", r"\bwomen's\b", r"\bwomens\b", r"\bfemale\b", r"\bgirls\b",
        r"\bfemenina\b", r"\bfemenino\b", r"\bfeminine\b", r"\bfrauen\b", r"\bdamen\b",
    ]
    if any(re.search(p, s) for p in explicit_patterns):
        return "women", "league_name"
    if any(term in s for term in WOMENS_TERMS):
        return "women", "keyword"
    if re.search(r"\b[a-z]{2,}\s+w\b", s) or re.search(r"\bw\s+vs\b", s):
        return "women", "team_suffix"
    return "unknown", "none"


def canonical_key(sport: str, date_local: str, home: str, away: str, league: str = "") -> str:
    pair = sorted([
        normalize_team_for_context(home, league, sport),
        normalize_team_for_context(away, league, sport),
    ])
    return "|".join([clean(sport), clean(date_local), pair[0], pair[1]])


def api_sports_request(endpoint: str, key: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, int, str]:
    try:
        r = requests.get(endpoint, params=params, headers={"x-apisports-key": key}, timeout=30)
        status = r.status_code
        r.raise_for_status()
        return r.json(), status, ""
    except Exception as exc:
        try:
            return None, r.status_code, str(exc)
        except Exception:
            return None, 0, str(exc)


def parse_api_sports_event(run_id: str, product: Dict[str, str], event: Dict[str, Any], requested_date: str, http_status: int) -> Dict[str, str]:
    product_name = product["product"]
    sport = product["sport"]

    if product_name == "football":
        league = event.get("league") or {}
        teams = event.get("teams") or {}
        fixture = event.get("fixture") or {}
        goals = event.get("goals") or {}
        league_name = clean(league.get("name"))
        country = clean(league.get("country"))
        home = clean(((teams.get("home") or {}).get("name")))
        away = clean(((teams.get("away") or {}).get("name")))
        home_score = clean(goals.get("home"))
        away_score = clean(goals.get("away"))
        status_raw = clean(((fixture.get("status") or {}).get("long") or (fixture.get("status") or {}).get("short")))
        source_event_id = clean(fixture.get("id"))
        start_utc = clean(fixture.get("date"))
        score_periods = json.dumps({"goals": goals, "score": event.get("score") or {}}, ensure_ascii=False)
        source_url = product["endpoint"]
    else:
        league = event.get("league") or {}
        country_obj = event.get("country") or {}
        teams = event.get("teams") or {}
        status_obj = event.get("status") or {}
        scores = event.get("scores") or {}
        league_name = clean(league.get("name"))
        country = clean(country_obj.get("name"))
        home = clean(((teams.get("home") or {}).get("name")))
        away = clean(((teams.get("away") or {}).get("name")))
        status_raw = clean(status_obj.get("long") or status_obj.get("short"))
        source_event_id = clean(event.get("id"))
        start_utc = clean(event.get("date"))
        if isinstance(scores.get("home"), dict):
            home_score = clean((scores.get("home") or {}).get("total") or (scores.get("home") or {}).get("current"))
        else:
            home_score = clean(scores.get("home"))
        if isinstance(scores.get("away"), dict):
            away_score = clean((scores.get("away") or {}).get("total") or (scores.get("away") or {}).get("current"))
        else:
            away_score = clean(scores.get("away"))
        score_periods = json.dumps(scores, ensure_ascii=False)
        source_url = product["endpoint"]

    date_local = local_date_from_iso(start_utc) or requested_date
    league_norm = normalize_league_name(league_name, sport)
    home_display = display_team_for_context(home, league_norm, sport)
    away_display = display_team_for_context(away, league_norm, sport)
    gender_scope, method = women_scope_and_method(product["label"], league_norm, country, home, away)
    if league_norm == "WNBA":
        gender_scope, method = "women", "league_alias"

    return {
        "run_id": run_id,
        "source_name": "api_sports",
        "source_priority": "100",
        "source_event_id": source_event_id,
        "canonical_key": canonical_key(sport, date_local, home_display, away_display, league_norm),
        "sport_norm": sport,
        "league_norm": league_norm,
        "competition_id": country,
        "gender_scope": gender_scope,
        "scheduled_start_utc": start_utc,
        "scheduled_date_local": date_local,
        "home_team_raw": home_display,
        "away_team_raw": away_display,
        "home_team_norm": normalize_team_for_context(home_display, league_norm, sport),
        "away_team_norm": normalize_team_for_context(away_display, league_norm, sport),
        "status_raw": status_raw,
        "status_norm": normalize_status(status_raw),
        "home_score": home_score,
        "away_score": away_score,
        "score_by_period_json": score_periods,
        "team_stats_json": "",
        "player_stats_json": "",
        "top_performers_json": "",
        "source_url": source_url,
        "fetched_at_utc": iso_now(),
        "http_status": str(http_status),
        "parse_ok": "Yes",
        "stale_rejected": "No",
        "women_match_method": method,
        "raw_archive_path": "",
        "notes": f"requested_date={requested_date}; country={country}",
    }


def fetch_api_sports(run_id: str, iso_dates: List[str], api_key: str) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []

    if not api_key:
        health.append({
            "source_name": "api_sports",
            "sport_or_league": "all",
            "date": "",
            "http_status": 0,
            "ok": "No",
            "events_found": 0,
            "observations_emitted": 0,
            "stale_rejected": 0,
            "notes": "APISPORTS_KEY is not set.",
        })
        return observations, health

    for product in PRODUCTS:
        for date_iso in iso_dates:
            data, status, error = api_sports_request(product["endpoint"], api_key, {"date": date_iso})
            events = data.get("response") if isinstance(data, dict) else []
            events = events or []
            emitted = 0
            for event in events:
                try:
                    observations.append(parse_api_sports_event(run_id, product, event, date_iso, status))
                    emitted += 1
                except Exception as exc:
                    observations.append({
                        "run_id": run_id,
                        "source_name": "api_sports",
                        "source_priority": "100",
                        "source_event_id": "",
                        "canonical_key": f"parse_error|api_sports|{product['product']}|{date_iso}|{emitted}",
                        "sport_norm": product["sport"],
                        "league_norm": "Unknown League",
                        "competition_id": "",
                        "gender_scope": "unknown",
                        "scheduled_start_utc": "",
                        "scheduled_date_local": date_iso,
                        "home_team_raw": "",
                        "away_team_raw": "",
                        "home_team_norm": "",
                        "away_team_norm": "",
                        "status_raw": "",
                        "status_norm": "unknown",
                        "home_score": "",
                        "away_score": "",
                        "score_by_period_json": "",
                        "team_stats_json": "",
                        "player_stats_json": "",
                        "top_performers_json": "",
                        "source_url": product["endpoint"],
                        "fetched_at_utc": iso_now(),
                        "http_status": str(status),
                        "parse_ok": "No",
                        "stale_rejected": "No",
                        "women_match_method": "none",
                        "raw_archive_path": "",
                        "notes": f"Parse error: {exc}",
                    })

            health.append({
                "source_name": "api_sports",
                "sport_or_league": product["sport"],
                "date": date_iso,
                "http_status": status,
                "ok": "Yes" if status == 200 and not error else "No",
                "events_found": len(events),
                "observations_emitted": emitted,
                "stale_rejected": 0,
                "notes": error or "ok",
            })
            time.sleep(REQUEST_SLEEP_SECONDS)

    return observations, health


def fetch_espn_wnba(run_id: str, compact_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    endpoint = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"
    observations = []
    health = []

    for date_compact in compact_dates:
        try:
            r = requests.get(endpoint, params={"dates": date_compact}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            status = r.status_code
            r.raise_for_status()
            data = r.json()
            error = ""
        except Exception as exc:
            data = {}
            try:
                status = r.status_code
            except Exception:
                status = 0
            error = str(exc)

        events = data.get("events") if isinstance(data, dict) else []
        events = events or []
        emitted = 0

        for event in events:
            try:
                event_id = clean(event.get("id"))
                status_raw = clean((((event.get("status") or {}).get("type") or {}).get("detail")))
                start_utc = clean(event.get("date"))
                date_local = local_date_from_iso(start_utc)
                home = away = home_score = away_score = ""
                score_periods = {}
                comps = event.get("competitions") or []
                if comps:
                    for comp in comps[0].get("competitors") or []:
                        team = clean(((comp.get("team") or {}).get("displayName")))
                        score = clean(comp.get("score"))
                        if clean(comp.get("homeAway")).lower() == "home":
                            home, home_score = team, score
                        elif clean(comp.get("homeAway")).lower() == "away":
                            away, away_score = team, score
                        score_periods[team] = comp.get("linescores") or []

                observations.append({
                    "run_id": run_id,
                    "source_name": "espn_wnba",
                    "source_priority": "70",
                    "source_event_id": event_id,
                    "canonical_key": canonical_key("basketball", date_local, home, away, "WNBA"),
                    "sport_norm": "basketball",
                    "league_norm": "WNBA",
                    "competition_id": "USA",
                    "gender_scope": "women",
                    "scheduled_start_utc": start_utc,
                    "scheduled_date_local": date_local,
                    "home_team_raw": home,
                    "away_team_raw": away,
                    "home_team_norm": normalize_team_for_context(home, "WNBA", "basketball"),
                    "away_team_norm": normalize_team_for_context(away, "WNBA", "basketball"),
                    "status_raw": status_raw,
                    "status_norm": normalize_status(status_raw),
                    "home_score": home_score,
                    "away_score": away_score,
                    "score_by_period_json": json.dumps(score_periods, ensure_ascii=False),
                    "team_stats_json": "",
                    "player_stats_json": "",
                    "top_performers_json": "",
                    "source_url": f"https://www.espn.com/wnba/game/_/gameId/{event_id}",
                    "fetched_at_utc": iso_now(),
                    "http_status": str(status),
                    "parse_ok": "Yes",
                    "stale_rejected": "No",
                    "women_match_method": "explicit_league",
                    "raw_archive_path": "",
                    "notes": f"requested_date={date_compact}",
                })
                emitted += 1
            except Exception:
                pass

        health.append({
            "source_name": "espn_wnba",
            "sport_or_league": "WNBA",
            "date": date_compact,
            "http_status": status,
            "ok": "Yes" if status == 200 and not error else "No",
            "events_found": len(events),
            "observations_emitted": emitted,
            "stale_rejected": 0,
            "notes": error or "ok",
        })
        time.sleep(0.15)

    return observations, health


def bool_yes(value: Any) -> bool:
    return clean(value).lower() == "yes"


def source_priority(obs: Dict[str, str]) -> int:
    return int(obs.get("source_priority") or 0)


def complete_final(obs: Dict[str, str]) -> bool:
    return obs.get("status_norm") == "final" and score_present(obs.get("home_score"), obs.get("away_score"))


def score_signature(obs: Dict[str, str]) -> Tuple[Tuple[str, str], Tuple[str, str]] | Tuple[()]:
    if not score_present(obs.get("home_score"), obs.get("away_score")):
        return tuple()
    pairs = sorted([
        (clean(obs.get("home_team_norm")), clean(obs.get("home_score"))),
        (clean(obs.get("away_team_norm")), clean(obs.get("away_score"))),
    ])
    return tuple(pairs)  # type: ignore[return-value]


def draw_allowed(obs: Dict[str, str]) -> bool:
    return obs.get("sport_norm") in DRAW_ALLOWED_SPORTS


def outcome_type(obs: Dict[str, str], winner: str, loser: str) -> str:
    if obs.get("status_norm") != "final":
        return obs.get("status_norm") or "unknown"
    if winner and loser:
        return "win"
    if draw_allowed(obs) and score_equal(obs.get("home_score"), obs.get("away_score")):
        return "draw"
    if score_equal(obs.get("home_score"), obs.get("away_score")):
        return "tie_needs_review"
    return "unknown_final"


def base_confidence(chosen: Dict[str, str], group: List[Dict[str, str]], conflict: bool) -> Tuple[float, Dict[str, Any]]:
    base = {
        "api_sports": 0.72,
        "ncaa": 0.68,
        "espn_wnba": 0.55,
        "sofascore": 0.45,
        "thesportsdb": 0.30,
    }.get(chosen.get("source_name"), 0.25)

    reasons = {"base_source": chosen.get("source_name"), "base": base, "adjustments": []}
    score = base

    if chosen.get("status_norm") == "final":
        score += 0.10
        reasons["adjustments"].append(["final_state", 0.10])
    if score_present(chosen.get("home_score"), chosen.get("away_score")):
        score += 0.05
        reasons["adjustments"].append(["score_complete", 0.05])
    if clean(chosen.get("score_by_period_json")) not in ["", "{}", "[]", "null"]:
        score += 0.05
        reasons["adjustments"].append(["period_data_present", 0.05])

    chosen_score = score_signature(chosen)
    agreeing = {
        obs.get("source_name") for obs in group
        if obs.get("status_norm") == "final"
        and score_signature(obs) == chosen_score
        and score_present(obs.get("home_score"), obs.get("away_score"))
    }
    if len(agreeing) >= 2:
        score += 0.10
        reasons["adjustments"].append(["second_source_agrees", 0.10])

    if chosen.get("league_norm") == "WNBA" and any(obs.get("source_name") == "espn_wnba" for obs in group):
        score += 0.08
        reasons["adjustments"].append(["wnba_espn_backup_present", 0.08])

    if chosen.get("source_name") in {"sofascore", "thesportsdb"} and len(group) == 1 and chosen.get("status_norm") == "final":
        score -= 0.15
        reasons["adjustments"].append(["single_unofficial_source_penalty", -0.15])
    if conflict:
        score -= 0.30
        reasons["adjustments"].append(["score_conflict_penalty", -0.30])
    if chosen.get("gender_scope") == "women" and chosen.get("women_match_method") in {"keyword", "team_suffix"}:
        score -= 0.04
        reasons["adjustments"].append(["gender_inferred_small_penalty", -0.04])
    elif chosen.get("gender_scope") != "women":
        score -= 0.20
        reasons["adjustments"].append(["gender_unknown_penalty", -0.20])

    score = max(0.0, min(1.0, score))
    reasons["final_confidence"] = round(score, 3)
    return score, reasons


def editorial_tier(obs: Dict[str, str]) -> str:
    blob = " ".join([
        obs.get("sport_norm", ""), obs.get("league_norm", ""), obs.get("competition_id", ""),
        obs.get("home_team_raw", ""), obs.get("away_team_raw", ""), obs.get("notes", ""),
    ]).lower()

    if obs.get("league_norm") == "WNBA":
        return "Tier 1"
    if any(term in blob for term in LOW_PRIORITY_LEAGUE_TERMS):
        return "Tier 3"
    if any(term in blob for term in TIER_1_TERMS):
        return "Tier 1"
    if obs.get("sport_norm") in {"basketball", "soccer", "volleyball"} and any(term in blob for term in TIER_2_TERMS):
        return "Tier 2"
    if obs.get("sport_norm") in {"rugby", "handball", "hockey"} and any(term in blob for term in TIER_2_TERMS):
        return "Tier 3"
    return "Tier 3"


def editorial_rank(event: Dict[str, Any]) -> float:
    blob = " ".join([
        event.get("sport_norm", ""), event.get("league_norm", ""), event.get("home_team_norm", ""),
        event.get("away_team_norm", ""), event.get("graphics_headline", ""), event.get("graphics_subhead", ""),
    ]).lower()
    rank = float(event.get("confidence") or 0) * 100
    if event.get("status_norm") == "final":
        rank += 15
    for term, points in EDITORIAL_TERMS.items():
        if term in blob:
            rank += points / 3

    if event.get("league_norm") == "WNBA":
        rank += 70
    if event.get("editorial_tier") == "Tier 1":
        rank += 15
    elif event.get("editorial_tier") == "Tier 3":
        rank -= 8

    if event.get("manual_review"):
        rank -= 25
    if event.get("gender_scope") != "women":
        rank -= 100
    return max(0.0, round(rank, 1))


def content_action(tier: str, rank: float, include_graphics: bool, manual_review: bool) -> Tuple[str, str]:
    if manual_review:
        return "Manual Review", "Review Queue"
    if not include_graphics:
        if tier == "Tier 1" and rank >= 85:
            return "Watch", "Watchlist"
        return "Archive", "Archive Only"
    if tier == "Tier 1" and rank >= 120:
        return "Make First", "Must Post"
    if tier in {"Tier 1", "Tier 2"} and rank >= 100:
        return "Strong Maybe", "Strong Maybe"
    if rank >= 85:
        return "Watch", "Watchlist"
    return "Archive", "Archive Only"


def content_family_for(event: Dict[str, Any]) -> str:
    if event.get("league_norm") == "WNBA":
        return "Tonight in the W"
    if event.get("sport_norm") == "soccer" and "world cup" in low(event.get("league_norm")):
        return "Global Game Watch"
    if event.get("sport_norm") == "volleyball":
        return "Around Women’s Sports"
    if event.get("sport_norm") == "rugby":
        return "Around Women’s Sports"
    return "Results Desk"


def caption_seed_for(event: Dict[str, Any]) -> str:
    if event.get("outcome_type") == "draw":
        return f"{event.get('away_team_display')} and {event.get('home_team_display')} finished level, {event.get('away_score')}-{event.get('home_score')}."
    if event.get("winner") and event.get("loser"):
        return f"{event.get('winner')} defeated {event.get('loser')}, {event.get('final_score_display')}."
    return event.get("graphics_subhead", "")


def apply_global_editorial_buckets(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for event in events:
        event["content_family"] = content_family_for(event)
        event["caption_seed"] = caption_seed_for(event)
        event["posting_priority"] = "Archive Only"
        if event.get("manual_review"):
            event["content_action"] = "Manual Review"
            event["editorial_bucket"] = "Review Queue"
        else:
            event["content_action"] = "Archive"
            event["editorial_bucket"] = "Archive Only"

    ready = [e for e in events if e.get("include_in_graphics") and not e.get("manual_review")]
    ready.sort(key=lambda e: (-float(e.get("editorial_rank") or 0), e.get("scheduled_date_local", ""), e.get("sport_norm", "")))
    sections = [
        ("Must Post", "Make First", "P1", ready[:5]),
        ("Strong Maybe", "Strong Maybe", "P2", ready[5:15]),
        ("Watchlist", "Watch", "P3", ready[15:30]),
    ]
    for bucket, action, priority, items in sections:
        for event in items:
            event["editorial_bucket"] = bucket
            event["content_action"] = action
            event["posting_priority"] = priority
    return events


def reconcile(run_id: str, observations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, str]]] = {}
    for obs in observations:
        if obs.get("canonical_key", "").startswith("parse_error"):
            continue
        groups.setdefault(obs.get("canonical_key", ""), []).append(obs)

    events: List[Dict[str, Any]] = []

    for key, group in groups.items():
        valid = [o for o in group if bool_yes(o.get("parse_ok")) and not bool_yes(o.get("stale_rejected"))] or group
        valid.sort(key=source_priority, reverse=True)
        chosen = valid[0]
        for obs in valid:
            if complete_final(obs):
                chosen = obs
                break

        final_scores = {
            score_signature(obs)
            for obs in valid
            if obs.get("status_norm") == "final" and score_present(obs.get("home_score"), obs.get("away_score"))
        }
        conflict = len(final_scores) > 1
        winner, loser = score_winner(chosen.get("home_team_raw"), chosen.get("away_team_raw"), chosen.get("home_score"), chosen.get("away_score"))
        outcome = outcome_type(chosen, winner, loser)
        conf, reasons = base_confidence(chosen, valid, conflict)

        manual = False
        if conflict:
            manual = True
        if chosen.get("status_norm") == "final" and chosen.get("source_name") in {"sofascore", "thesportsdb"}:
            manual = True
        if chosen.get("gender_scope") != "women" and chosen.get("status_norm") == "final":
            manual = True
        if chosen.get("status_norm") == "final" and not winner and score_present(chosen.get("home_score"), chosen.get("away_score")) and outcome != "draw":
            manual = True

        include_dashboard = chosen.get("gender_scope") == "women" and conf >= 0.55
        include_graphics = chosen.get("gender_scope") == "women" and chosen.get("status_norm") == "final" and conf >= 0.85 and not manual
        tier = editorial_tier(chosen)

        home_display = display_team_for_context(chosen.get("home_team_raw"), chosen.get("league_norm"), chosen.get("sport_norm"))
        away_display = display_team_for_context(chosen.get("away_team_raw"), chosen.get("league_norm"), chosen.get("sport_norm"))
        final_score_display = f"{away_display} {chosen.get('away_score')} - {home_display} {chosen.get('home_score')}"

        if outcome == "win" and winner and loser:
            headline = f"{winner} beat {loser}"
            subhead = f"Final: {final_score_display}"
        elif outcome == "draw":
            scoreline = f"{chosen.get('away_score')}-{chosen.get('home_score')}"
            headline = f"{away_display} and {home_display} draw {scoreline}"
            subhead = f"Final: {final_score_display}"
        else:
            headline = f"{away_display} vs {home_display}".strip(" vs ")
            subhead = f"Status: {chosen.get('status_raw')}"

        event = {
            "run_id": run_id,
            "event_uid": stable_id(run_id, key),
            "canonical_key": key,
            "selected_source": chosen.get("source_name", ""),
            "source_count": len(valid),
            "all_sources_json": json.dumps(sorted({o.get("source_name") for o in valid}), ensure_ascii=False),
            "sport_norm": chosen.get("sport_norm", ""),
            "league_norm": chosen.get("league_norm", ""),
            "gender_scope": chosen.get("gender_scope", ""),
            "scheduled_start_utc": chosen.get("scheduled_start_utc", ""),
            "scheduled_date_local": chosen.get("scheduled_date_local", ""),
            "home_team_norm": chosen.get("home_team_norm", ""),
            "away_team_norm": chosen.get("away_team_norm", ""),
            "home_team_display": home_display,
            "away_team_display": away_display,
            "final_score_display": final_score_display,
            "game_state": chosen.get("status_norm", ""),
            "status_norm": chosen.get("status_norm", ""),
            "home_score": chosen.get("home_score", ""),
            "away_score": chosen.get("away_score", ""),
            "winner": winner,
            "loser": loser,
            "outcome_type": outcome,
            "editorial_tier": tier,
            "editorial_bucket": "",
            "content_action": "",
            "content_family": "",
            "posting_priority": "",
            "caption_seed": "",
            "score_by_period_json": chosen.get("score_by_period_json", ""),
            "team_stats_json": chosen.get("team_stats_json", ""),
            "player_stats_json": chosen.get("player_stats_json", ""),
            "top_performers_json": chosen.get("top_performers_json", ""),
            "confidence": conf,
            "confidence_reason_json": json.dumps(reasons, ensure_ascii=False),
            "score_conflict": conflict,
            "manual_review": manual,
            "include_in_dashboard": include_dashboard,
            "include_in_graphics": include_graphics,
            "editorial_rank": 0,
            "graphics_headline": headline,
            "graphics_subhead": subhead,
            "source_url": chosen.get("source_url", ""),
            "source_priority": int(chosen.get("source_priority") or 0),
        }
        event["editorial_rank"] = editorial_rank(event)
        event["content_action"], event["editorial_bucket"] = content_action(
            tier, event["editorial_rank"], include_graphics, manual
        )
        events.append(event)

    events.sort(key=lambda e: (e.get("gender_scope") != "women", e.get("status_norm") != "final", -float(e.get("editorial_rank", 0)), e.get("scheduled_date_local", "")))
    return apply_global_editorial_buckets(events)


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {}
            for k in fieldnames:
                v = row.get(k, "")
                if isinstance(v, bool):
                    v = "Yes" if v else "No"
                elif isinstance(v, float) and k == "confidence":
                    v = f"{v:.2f}"
                elif isinstance(v, float) and k == "editorial_rank":
                    v = f"{v:.1f}"
                out[k] = v
            writer.writerow(out)


def event_score_text(e: Dict[str, Any]) -> str:
    return e.get("final_score_display") or f"{e.get('away_team_display', e.get('away_team_norm'))} {e.get('away_score')} - {e.get('home_team_display', e.get('home_team_norm'))} {e.get('home_score')}"


def packet_block(idx: int, e: Dict[str, Any], section_name: str) -> List[str]:
    if e.get("outcome_type") == "draw":
        result_sentence = f"{e.get('away_team_display')} and {e.get('home_team_display')} finished level at {e.get('away_score')}-{e.get('home_score')}."
    else:
        result_sentence = f"{e.get('away_team_display')} vs {e.get('home_team_display')} finished {e.get('away_score')}-{e.get('home_score')}."

    return [
        f"## RESULT GRAPHIC {idx}: {e.get('graphics_headline')}",
        "",
        f"**Queue section:** {section_name}",
        f"**Sport:** {e.get('sport_norm')}",
        f"**League:** {e.get('league_norm')}",
        f"**Editorial tier:** {e.get('editorial_tier')}",
        f"**Editorial bucket:** {e.get('editorial_bucket')}",
        f"**Content action:** {e.get('content_action')}",
        f"**Content family:** {e.get('content_family')}",
        f"**Posting priority:** {e.get('posting_priority')}",
        f"**Template:** Postgame Result Card",
        f"**Selected source:** {e.get('selected_source')}",
        f"**All sources:** {e.get('all_sources_json')}",
        f"**Confidence:** {float(e.get('confidence') or 0):.2f}",
        f"**Manual review:** {'Yes' if e.get('manual_review') else 'No'}",
        f"**Editorial rank:** {float(e.get('editorial_rank') or 0):.1f}",
        f"**Outcome type:** {e.get('outcome_type')}",
        "",
        "### Verified result context",
        f"- Matchup: {e.get('away_team_display')} vs {e.get('home_team_display')}",
        f"- Final score: {event_score_text(e)}",
        f"- Winner: {e.get('winner')}",
        f"- Loser: {e.get('loser')}",
        f"- Outcome: {e.get('outcome_type')}",
        f"- Game status: {e.get('status_norm')}",
        f"- Date: {e.get('scheduled_date_local')}",
        f"- Source URL/API: {e.get('source_url')}",
        "",
        "### Production accuracy rules",
        "- Do not change the final score.",
        "- Do not invent top performer stats.",
        "- If player box-score data is not provided, make this a team/result graphic.",
        "- Use the established Her Sports Daily brand colors, font hierarchy, and top-left watermark.",
        "",
        "### Slide copy",
        f"**Slide 1 - Hook:** {e.get('graphics_headline')}",
        f"{e.get('graphics_subhead')}.",
        "",
        "**Slide 2 - Result:** What happened",
        result_sentence,
        "",
        "**Slide 3 - Context:** Why it matters",
        "This is part of today’s broader women’s sports results slate.",
        "",
        "**Slide 4 - CTA:** Your take?",
        "Follow Her Sports Daily for more verified women’s sports results.",
        "",
        "---",
        "",
    ]


def graphics_queue(events: List[Dict[str, Any]]) -> str:
    ready = [e for e in events if e.get("include_in_graphics")]
    ready.sort(key=lambda e: (-float(e.get("editorial_rank") or 0), e.get("sport_norm", ""), e.get("league_norm", "")))

    must_post = [e for e in ready if e.get("editorial_bucket") == "Must Post"][:5]
    used = {e.get("event_uid") for e in must_post}
    strong_maybe = [e for e in ready if e.get("event_uid") not in used and e.get("editorial_bucket") == "Strong Maybe"][:10]
    used.update(e.get("event_uid") for e in strong_maybe)
    watchlist = [e for e in ready if e.get("event_uid") not in used and e.get("editorial_bucket") == "Watchlist"][:15]
    archive_only_count = len([e for e in ready if e.get("editorial_bucket") == "Archive Only"])

    lines = [
        "# Her Sports Daily Results Graphics Queue v4.2",
        "",
        f"Generated: {iso_now()}",
        "",
        "This queue is intentionally capped and ranked for Her Sports Daily priorities.",
        "",
        "## Queue rules",
        "",
        "- Must Post: top 5 max.",
        "- Strong Maybe: next 10 max.",
        "- Watchlist: next 15 max.",
        "- Archive Only: counted but not packeted.",
        "- Draws are allowed for soccer/rugby/handball/hockey when the final score is tied.",
        "- Do not invent player stat lines. If no player data is provided, make a team-result graphic.",
        "",
        f"Archive-only valid graphics hidden from this queue: {archive_only_count}",
        "",
    ]

    if not ready:
        lines.append("No high-confidence final women's result graphics are ready right now.")
        return "\n".join(lines)

    idx = 1
    for section_name, section_events in [("MUST POST", must_post), ("STRONG MAYBE", strong_maybe), ("WATCHLIST", watchlist)]:
        lines.extend([f"# {section_name}", ""])
        if not section_events:
            lines.extend(["No items in this section.", ""])
            continue
        for event in section_events:
            lines.extend(packet_block(idx, event, section_name))
            idx += 1

    return "\n".join(lines)


def recommendations_md(events: List[Dict[str, Any]]) -> str:
    must = [e for e in events if e.get("editorial_bucket") == "Must Post"][:5]
    maybe = [e for e in events if e.get("editorial_bucket") == "Strong Maybe"][:10]
    watch = [e for e in events if e.get("editorial_bucket") == "Watchlist"][:15]
    review = [e for e in events if e.get("manual_review") and e.get("gender_scope") == "women"][:20]

    lines = [
        "# Her Sports Daily Daily Results Recommendations v4.2",
        "",
        "This file is the human-friendly editorial command center for results content.",
        "",
        "## Make First",
        "",
    ]

    if not must:
        lines.append("No Must Post result recommendations right now.")
    else:
        for idx, e in enumerate(must, 1):
            lines.append(f"{idx}. **{e.get('graphics_headline')}**")
            lines.append(f"   - {e.get('sport_norm')} | {e.get('league_norm')} | {e.get('content_family')} | confidence {float(e.get('confidence') or 0):.2f} | rank {float(e.get('editorial_rank') or 0):.1f}")
            lines.append(f"   - {e.get('graphics_subhead')}")
            lines.append(f"   - Caption seed: {e.get('caption_seed')}")
            lines.append("")

    lines.extend(["", "## Strong Maybe", ""])
    if not maybe:
        lines.append("No Strong Maybe items.")
    else:
        for idx, e in enumerate(maybe, 1):
            lines.append(f"{idx}. **{e.get('graphics_headline')}**")
            lines.append(f"   - {e.get('sport_norm')} | {e.get('league_norm')} | {e.get('content_family')} | confidence {float(e.get('confidence') or 0):.2f} | rank {float(e.get('editorial_rank') or 0):.1f}")
            lines.append(f"   - Caption seed: {e.get('caption_seed')}")
            lines.append("")

    lines.extend(["", "## Watchlist", ""])
    if not watch:
        lines.append("No Watchlist items.")
    else:
        for idx, e in enumerate(watch, 1):
            lines.append(f"{idx}. **{e.get('graphics_headline')}**")
            lines.append(f"   - {e.get('sport_norm')} | {e.get('league_norm')} | {e.get('content_family')} | confidence {float(e.get('confidence') or 0):.2f} | rank {float(e.get('editorial_rank') or 0):.1f}")
            lines.append(f"   - Caption seed: {e.get('caption_seed')}")
            lines.append("")

    lines.extend(["", "## Manual Review", ""])
    if not review:
        lines.append("No manual review items.")
    else:
        for idx, e in enumerate(review, 1):
            lines.append(f"{idx}. **{e.get('graphics_headline')}**")
            lines.append(f"   - Reason: manual review flagged. Outcome {e.get('outcome_type')}. Sources {e.get('all_sources_json')}.")
            lines.append("")

    lines.extend([
        "",
        "## Production reminder",
        "",
        "- Use `results_graphics_queue.md` for packets.",
        "- Do not invent player stats.",
        "- Draws are valid when outcome_type is `draw`.",
    ])
    return "\n".join(lines) + "\n"


def hub_md(run_id: str, events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], iso_dates: List[str]) -> str:
    women = [e for e in events if e.get("gender_scope") == "women"]
    finals = [e for e in women if e.get("status_norm") == "final"]
    graphics = [e for e in events if e.get("include_in_graphics")]
    review = [e for e in events if e.get("manual_review") and e.get("gender_scope") == "women"]
    by_source: Dict[str, int] = {}
    for obs in observations:
        by_source[obs.get("source_name", "")] = by_source.get(obs.get("source_name", ""), 0) + 1
    by_sport: Dict[str, int] = {}
    for e in women:
        by_sport[e.get("sport_norm", "")] = by_sport.get(e.get("sport_norm", ""), 0) + 1

    lines = [
        "# Her Sports Daily Results Desk v4.2 Hub",
        "",
        f"Run ID: `{run_id}`",
        f"Generated: `{iso_now()}`",
        f"Date window: `{', '.join(iso_dates)}`",
        "",
        "## Source strategy",
        "",
        "- API-Sports is the scoring backbone.",
        "- ESPN WNBA is backup/verification.",
        "- v4.2 adds WNBA reconciliation, WNBA-first ranking, league aliasing, and global queue buckets.",
        "",
        "## Run summary",
        "",
        f"- Raw source observations: {len(observations)}",
        f"- Reconciled events: {len(events)}",
        f"- Women's events surfaced: {len(women)}",
        f"- Women's finals: {len(finals)}",
        f"- Graphics-ready results: {len(graphics)}",
        f"- Manual review items: {len(review)}",
        f"- Must Post: {sum(1 for e in events if e.get('editorial_bucket') == 'Must Post')}",
        f"- Strong Maybe: {sum(1 for e in events if e.get('editorial_bucket') == 'Strong Maybe')}",
        f"- Watchlist: {sum(1 for e in events if e.get('editorial_bucket') == 'Watchlist')}",
        "",
        "## Observations by source",
        "",
    ]
    for source, count in sorted(by_source.items()):
        lines.append(f"- {source}: {count}")
    lines.extend(["", "## Women's events by sport", ""])
    for sport, count in sorted(by_sport.items()):
        lines.append(f"- {sport}: {count}")
    lines.extend([
        "",
        "## Graphics gate",
        "",
        "- `include_in_graphics` requires women-only, final, confidence >= 0.85, and manual_review = No.",
        "- v4.2 treats tied soccer/rugby/handball/hockey finals as draws, not errors.",
        "- The graphics queue is globally capped: 5 Must Post, 10 Strong Maybe, 15 Watchlist.",
        "- Player stats are never invented. If no box-score data exists, packet is a team-result graphic.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    iso_dates, compact_dates = date_window()
    sources = {s.strip().lower() for s in os.environ.get("HSD_RESULTS_SOURCES", "apisports,espn").split(",") if s.strip()}
    run_id = stable_id(iso_now(), ",".join(sorted(sources)))

    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []

    if "apisports" in sources:
        obs, h = fetch_api_sports(run_id, iso_dates, os.environ.get("APISPORTS_KEY", ""))
        observations.extend(obs)
        health.extend(h)

    if "espn" in sources or "espn_wnba" in sources:
        obs, h = fetch_espn_wnba(run_id, compact_dates)
        observations.extend(obs)
        health.extend(h)

    events = reconcile(run_id, observations)

    all_events = events
    womens = [e for e in events if e.get("gender_scope") == "women" and e.get("include_in_dashboard")]
    finals = [e for e in events if e.get("gender_scope") == "women" and e.get("status_norm") == "final" and float(e.get("confidence") or 0) >= 0.70]
    top = [e for e in events if e.get("gender_scope") == "women" and e.get("include_in_dashboard")][:50]
    review = [e for e in events if e.get("gender_scope") == "women" and e.get("manual_review")]

    write_csv(OBSERVATIONS_FILE, observations, OBS_FIELDS)
    write_csv(RECONCILED_FILE, events, EVENT_FIELDS)
    write_csv(RESULTS_BOARD_FILE, all_events, EVENT_FIELDS)
    write_csv(WOMENS_RESULTS_FILE, womens, EVENT_FIELDS)
    write_csv(FINAL_RESULTS_FILE, finals, EVENT_FIELDS)
    write_csv(TOP_RESULTS_FILE, top, EVENT_FIELDS)
    write_csv(MANUAL_REVIEW_FILE, review, EVENT_FIELDS)
    write_csv(SOURCE_HEALTH_FILE, health, ["source_name", "sport_or_league", "date", "http_status", "ok", "events_found", "observations_emitted", "stale_rejected", "notes"])

    Path(GRAPHICS_QUEUE_FILE).write_text(graphics_queue(events), encoding="utf-8")
    Path(RECOMMENDATIONS_FILE).write_text(recommendations_md(events), encoding="utf-8")
    Path(HUB_FILE).write_text(hub_md(run_id, events, observations, health, iso_dates), encoding="utf-8")

    manifest = {
        "version": VERSION,
        "run_id": run_id,
        "generated_at_utc": iso_now(),
        "sources": sorted(sources),
        "date_window": iso_dates,
        "counts": {
            "observations": len(observations),
            "reconciled_events": len(events),
            "women_events": len(womens),
            "final_women_events": len(finals),
            "manual_review": len(review),
            "graphics_ready": sum(1 for e in events if e.get("include_in_graphics")),
            "must_post": sum(1 for e in events if e.get("editorial_bucket") == "Must Post"),
            "strong_maybe": sum(1 for e in events if e.get("editorial_bucket") == "Strong Maybe"),
            "watchlist": sum(1 for e in events if e.get("editorial_bucket") == "Watchlist"),
        },
        "source_health": health,
    }
    Path(MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Created Results Desk v4.2 outputs")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
