from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, asdict, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

WOMEN_HINTS = {
    "women", "woman", "women's", "womens", "female", "girls", "ladies", "wnba", "ncaaw",
    "ncaa women", "ncaa women's", "nwsl", "pwhl", "wta", "lpga", "uswnt", "femenina",
    "femenino", "feminine", "frauen", "damen", "w-league", "a-league women", "liga mx femenil",
    "uwcl", "wsl", "women super league", "women's super league", "volleyball nations league women",
    "world cup women", "women world cup", "champions league women"
}

API_PRODUCTS = [
    {"product": "basketball", "sport": "basketball", "endpoint": "https://v1.basketball.api-sports.io/games"},
    {"product": "football", "sport": "soccer", "endpoint": "https://v3.football.api-sports.io/fixtures"},
    {"product": "volleyball", "sport": "volleyball", "endpoint": "https://v1.volleyball.api-sports.io/games"},
    {"product": "rugby", "sport": "rugby", "endpoint": "https://v1.rugby.api-sports.io/games"},
    {"product": "handball", "sport": "handball", "endpoint": "https://v1.handball.api-sports.io/games"},
    {"product": "hockey", "sport": "hockey", "endpoint": "https://v1.hockey.api-sports.io/games"},
    {"product": "baseball", "sport": "baseball", "endpoint": "https://v1.baseball.api-sports.io/games"},
]

SOURCE_PRIORITY = {"api_sports": 100, "ncaa": 90, "espn_wnba": 70, "sofascore": 50, "thesportsdb": 30}
BASE_WEIGHT = {"api_sports": 0.72, "ncaa": 0.68, "espn_wnba": 0.55, "sofascore": 0.45, "thesportsdb": 0.30}


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def low(value: Any) -> str:
    return clean(value).lower()


def slug(value: Any) -> str:
    s = low(value).replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_team(value: Any) -> str:
    s = slug(value)
    replacements = {"united states": "usa", "u s a": "usa", "women": "w", "womens": "w", "ladies": "w"}
    for src, dst in replacements.items():
        s = re.sub(rf"\b{re.escape(src)}\b", dst, s)
    return re.sub(r"\s+", " ", s).strip()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def date_window(timezone_name: str, lookback: int, lookahead: int) -> tuple[list[str], list[str]]:
    if ZoneInfo is not None:
        today = datetime.now(ZoneInfo(timezone_name)).date()
    else:
        today = datetime.utcnow().date()
    iso_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-lookback, lookahead + 1)]
    compact_dates = [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(-lookback, lookahead + 1)]
    return iso_dates, compact_dates


def local_date_from_iso(value: str, timezone_name: str = "America/New_York") -> str:
    value = clean(value)
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if ZoneInfo is not None:
            dt = dt.astimezone(ZoneInfo(timezone_name))
        return dt.date().isoformat()
    except Exception:
        return value[:10]


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def status_norm(value: Any) -> str:
    s = low(value)
    if any(x in s for x in ["finished", "match finished", "after fulltime", "after overtime", "final", "ft", "ended", "aet"]):
        return "final"
    if any(x in s for x in ["live", "in progress", "quarter", "half", "period", "set", "inning"]):
        return "live"
    if any(x in s for x in ["not started", "scheduled", "pre match", "pre-match", "time to be defined", "ns"]):
        return "scheduled"
    if any(x in s for x in ["postponed", "cancelled", "canceled", "suspended", "abandoned"]):
        return "not_played"
    return s or "unknown"


def women_scope_and_method(*parts: Any) -> tuple[str, str]:
    blob = " ".join(clean(p) for p in parts if clean(p))
    s = low(blob)
    if any(term in s for term in ["women", "women's", "womens", "female", "girls", "femenina", "femenino", "feminine", "frauen", "damen"]):
        return "women", "league_name"
    if any(term in s for term in WOMEN_HINTS):
        return "women", "keyword"
    if re.search(r"\b[a-z]{2,}\s+w\b", s) or re.search(r"\bw\s+vs\b", s):
        return "women", "team_suffix"
    return "unknown", "none"


def canonical_key(sport: str, date_local: str, home: str, away: str) -> str:
    h = normalize_team(home)
    a = normalize_team(away)
    pair = sorted([h, a])
    return "|".join([slug(sport) or "unknown", clean(date_local), pair[0], pair[1]])


def score_present(h: Any, a: Any) -> bool:
    return clean(h) != "" and clean(a) != ""


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if clean(value) == "":
            return default
        return int(float(str(value)))
    except Exception:
        return default


def winner_loser(home: str, away: str, home_score: Any, away_score: Any) -> tuple[str, str]:
    h = safe_int(home_score)
    a = safe_int(away_score)
    if h is None or a is None:
        return "", ""
    if h > a:
        return clean(home), clean(away)
    if a > h:
        return clean(away), clean(home)
    return "", ""


@dataclass
class Observation:
    run_id: str
    source_name: str
    source_priority: int
    source_event_id: str
    canonical_key: str
    sport_norm: str
    league_norm: str
    competition_id: str
    gender_scope: str
    scheduled_start_utc: str
    scheduled_date_local: str
    home_team_raw: str
    away_team_raw: str
    home_team_norm: str
    away_team_norm: str
    status_raw: str
    status_norm: str
    home_score: str
    away_score: str
    score_by_period_json: str
    team_stats_json: str
    player_stats_json: str
    top_performers_json: str
    source_url: str
    fetched_at_utc: str
    http_status: int
    parse_ok: bool
    stale_rejected: bool
    women_match_method: str
    raw_archive_path: str
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["parse_ok"] = "Yes" if self.parse_ok else "No"
        d["stale_rejected"] = "Yes" if self.stale_rejected else "No"
        return d


@dataclass
class Event:
    run_id: str
    event_uid: str
    canonical_key: str
    selected_source: str
    source_count: int
    all_sources_json: str
    sport_norm: str
    league_norm: str
    gender_scope: str
    scheduled_start_utc: str
    scheduled_date_local: str
    home_team_norm: str
    away_team_norm: str
    game_state: str
    status_norm: str
    home_score: str
    away_score: str
    winner: str
    loser: str
    score_by_period_json: str
    team_stats_json: str
    player_stats_json: str
    top_performers_json: str
    confidence: float
    confidence_reason_json: str
    score_conflict: bool
    manual_review: bool
    include_in_dashboard: bool
    include_in_graphics: bool
    editorial_rank: float
    graphics_headline: str
    graphics_subhead: str
    source_url: str
    source_priority: int

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = f"{self.confidence:.2f}"
        d["editorial_rank"] = f"{self.editorial_rank:.1f}"
        for key in ["score_conflict", "manual_review", "include_in_dashboard", "include_in_graphics"]:
            d[key] = "Yes" if getattr(self, key) else "No"
        return d


def api_request(endpoint: str, api_key: str, params: dict) -> tuple[dict | None, int, str]:
    try:
        r = requests.get(endpoint, params=params, headers={"x-apisports-key": api_key}, timeout=30)
        status = r.status_code
        r.raise_for_status()
        return r.json(), status, ""
    except Exception as exc:
        try:
            return None, r.status_code, str(exc)
        except Exception:
            return None, 0, str(exc)


def parse_api_event(run_id: str, product: dict, event: dict, requested_date: str, status_code: int) -> Observation:
    product_name = product["product"]
    sport = product["sport"]
    if product_name == "football":
        league = event.get("league") or {}
        teams = event.get("teams") or {}
        fixture = event.get("fixture") or {}
        goals = event.get("goals") or {}
        home = clean(((teams.get("home") or {}).get("name")))
        away = clean(((teams.get("away") or {}).get("name")))
        league_name = clean(league.get("name"))
        country = clean(league.get("country"))
        status_raw = clean(((fixture.get("status") or {}).get("long") or (fixture.get("status") or {}).get("short")))
        home_score = clean(goals.get("home"))
        away_score = clean(goals.get("away"))
        source_event_id = clean(fixture.get("id"))
        start_utc = clean(fixture.get("date"))
        score_json = json.dumps({"goals": goals, "score": event.get("score") or {}}, ensure_ascii=False)
    else:
        league = event.get("league") or {}
        country_obj = event.get("country") or {}
        teams = event.get("teams") or {}
        status_obj = event.get("status") or {}
        home = clean(((teams.get("home") or {}).get("name")))
        away = clean(((teams.get("away") or {}).get("name")))
        league_name = clean(league.get("name"))
        country = clean(country_obj.get("name"))
        status_raw = clean(status_obj.get("long") or status_obj.get("short"))
        source_event_id = clean(event.get("id"))
        start_utc = clean(event.get("date"))
        scores = event.get("scores") or {}
        home_score = away_score = ""
        if isinstance(scores, dict):
            home_block = scores.get("home")
            away_block = scores.get("away")
            home_score = clean((home_block or {}).get("total") or (home_block or {}).get("current")) if isinstance(home_block, dict) else clean(home_block)
            away_score = clean((away_block or {}).get("total") or (away_block or {}).get("current")) if isinstance(away_block, dict) else clean(away_block)
        score_json = json.dumps(scores, ensure_ascii=False)
    date_local = local_date_from_iso(start_utc) or requested_date
    gender, method = women_scope_and_method(league_name, country, sport, home, away)
    return Observation(
        run_id=run_id,
        source_name="api_sports",
        source_priority=100,
        source_event_id=source_event_id,
        canonical_key=canonical_key(sport, date_local, home, away),
        sport_norm=sport,
        league_norm=league_name or "Unknown League",
        competition_id=country,
        gender_scope=gender,
        scheduled_start_utc=start_utc,
        scheduled_date_local=date_local,
        home_team_raw=home,
        away_team_raw=away,
        home_team_norm=normalize_team(home),
        away_team_norm=normalize_team(away),
        status_raw=status_raw,
        status_norm=status_norm(status_raw),
        home_score=home_score,
        away_score=away_score,
        score_by_period_json=score_json,
        team_stats_json="",
        player_stats_json="",
        top_performers_json="",
        source_url=product["endpoint"],
        fetched_at_utc=iso_now(),
        http_status=status_code,
        parse_ok=True,
        stale_rejected=False,
        women_match_method=method,
        raw_archive_path="",
        notes=f"requested_date={requested_date}; country={country}",
    )


def fetch_apisports(run_id: str, dates: list[str], api_key: str) -> tuple[list[Observation], list[dict]]:
    observations, health = [], []
    if not api_key:
        return [], [{"source_name": "api_sports", "sport_or_league": "all", "date": "", "http_status": 0, "ok": "No", "events_found": 0, "observations_emitted": 0, "stale_rejected": 0, "notes": "APISPORTS_KEY missing"}]
    for product in API_PRODUCTS:
        for d in dates:
            data, status_code, error = api_request(product["endpoint"], api_key, {"date": d})
            events = data.get("response") if isinstance(data, dict) else []
            events = events or []
            emitted = 0
            for ev in events:
                try:
                    observations.append(parse_api_event(run_id, product, ev, d, status_code))
                    emitted += 1
                except Exception:
                    pass
            health.append({"source_name": "api_sports", "sport_or_league": product["sport"], "date": d, "http_status": status_code, "ok": "Yes" if status_code == 200 and not error else "No", "events_found": len(events), "observations_emitted": emitted, "stale_rejected": 0, "notes": error or "ok"})
            time.sleep(0.25)
    return observations, health


def http_json(url: str, params: dict | None = None) -> tuple[dict | None, int, str]:
    try:
        r = requests.get(url, params=params or {}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        status = r.status_code
        r.raise_for_status()
        return r.json(), status, ""
    except Exception as exc:
        try:
            return None, r.status_code, str(exc)
        except Exception:
            return None, 0, str(exc)


def fetch_espn_wnba(run_id: str, compact_dates: list[str]) -> tuple[list[Observation], list[dict]]:
    observations, health = [], []
    endpoint = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"
    for compact in compact_dates:
        data, status_code, error = http_json(endpoint, {"dates": compact})
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
                observations.append(Observation(run_id, "espn_wnba", 70, event_id, canonical_key("basketball", date_local, home, away), "basketball", "WNBA", "USA", "women", start_utc, date_local, home, away, normalize_team(home), normalize_team(away), status_raw, status_norm(status_raw), home_score, away_score, json.dumps(score_periods, ensure_ascii=False), "", "", "", f"https://www.espn.com/wnba/game/_/gameId/{event_id}", iso_now(), status_code, True, False, "explicit_league", "", f"requested_date={compact}"))
                emitted += 1
            except Exception:
                pass
        health.append({"source_name": "espn_wnba", "sport_or_league": "WNBA", "date": compact, "http_status": status_code, "ok": "Yes" if status_code == 200 and not error else "No", "events_found": len(events), "observations_emitted": emitted, "stale_rejected": 0, "notes": error or "ok"})
        time.sleep(0.15)
    return observations, health


def fetch_sofascore(run_id: str, dates: list[str]) -> tuple[list[Observation], list[dict]]:
    try:
        import asyncio
        from sofascore_wrapper.api import SofascoreAPI
    except Exception as exc:
        return [], [{"source_name": "sofascore", "sport_or_league": "all", "date": "", "http_status": 0, "ok": "No", "events_found": 0, "observations_emitted": 0, "stale_rejected": 0, "notes": f"optional import failed: {exc}"}]

    async def run() -> tuple[list[Observation], list[dict]]:
        observations, health = [], []
        api = SofascoreAPI()
        specs = [("basketball", "Basketball", "games_by_date"), ("tennis", "Tennis", "matches_by_date"), ("baseball", "Baseball", "matches_by_date"), ("football", "Football", "matches_by_date"), ("volleyball", "Volleyball", "matches_by_date")]
        try:
            for sport, class_name, method_name in specs:
                try:
                    module = __import__(f"sofascore_wrapper.{sport}", fromlist=[class_name])
                    client = getattr(module, class_name)(api)
                    method = getattr(client, method_name)
                except Exception as exc:
                    health.append({"source_name": "sofascore", "sport_or_league": sport, "date": "", "http_status": 0, "ok": "No", "events_found": 0, "observations_emitted": 0, "stale_rejected": 0, "notes": f"client init failed: {exc}"})
                    continue
                for d in dates:
                    try:
                        data = await method(date=d)
                        events = data.get("events") if isinstance(data, dict) else []
                        events = events or []
                        emitted = 0
                        for ev in events:
                            tournament = ev.get("tournament") or {}
                            unique = tournament.get("uniqueTournament") or {}
                            category = tournament.get("category") or {}
                            home_block = ev.get("homeTeam") or {}
                            away_block = ev.get("awayTeam") or {}
                            league = clean(unique.get("name") or tournament.get("name"))
                            country = clean(category.get("name"))
                            home = clean(home_block.get("name"))
                            away = clean(away_block.get("name"))
                            gender, method_found = women_scope_and_method(league, country, sport, home, away, home_block.get("gender"), away_block.get("gender"))
                            if gender != "women":
                                continue
                            event_id = clean(ev.get("id"))
                            status_raw = clean(((ev.get("status") or {}).get("description") or (ev.get("status") or {}).get("type")))
                            home_score = clean(((ev.get("homeScore") or {}).get("current")))
                            away_score = clean(((ev.get("awayScore") or {}).get("current")))
                            observations.append(Observation(run_id, "sofascore", 50, event_id, canonical_key(sport, d, home, away), sport, league or "Unknown League", country, "women", clean(ev.get("startTimestamp")), d, home, away, normalize_team(home), normalize_team(away), status_raw, status_norm(status_raw), home_score, away_score, json.dumps({"homeScore": ev.get("homeScore") or {}, "awayScore": ev.get("awayScore") or {}}, ensure_ascii=False), "", "", "", f"https://www.sofascore.com/event/{event_id}" if event_id else "", iso_now(), 200, True, False, method_found, "", "SofaScore optional discovery lane. Not scorer of record."))
                            emitted += 1
                        health.append({"source_name": "sofascore", "sport_or_league": sport, "date": d, "http_status": 200, "ok": "Yes", "events_found": len(events), "observations_emitted": emitted, "stale_rejected": 0, "notes": "ok"})
                    except Exception as exc:
                        health.append({"source_name": "sofascore", "sport_or_league": sport, "date": d, "http_status": 0, "ok": "No", "events_found": 0, "observations_emitted": 0, "stale_rejected": 0, "notes": f"fetch failed: {exc}"})
            return observations, health
        finally:
            try:
                await api.close()
            except Exception:
                pass
    return asyncio.run(run())


def choose_reconciled(run_id: str, key: str, group: list[Observation]) -> Event:
    valid = [o for o in group if o.parse_ok and not o.stale_rejected]
    if not valid:
        valid = group
    valid.sort(key=lambda o: o.source_priority, reverse=True)
    chosen = valid[0]
    for obs in valid:
        if obs.status_norm == "final" and score_present(obs.home_score, obs.away_score):
            chosen = obs
            break
    final_scores = {(o.home_score, o.away_score) for o in valid if o.status_norm == "final" and score_present(o.home_score, o.away_score)}
    conflict = len(final_scores) > 1
    conf, reasons = confidence(chosen, valid, conflict)
    win, lose = winner_loser(chosen.home_team_raw, chosen.away_team_raw, chosen.home_score, chosen.away_score)
    manual = conflict or (chosen.status_norm == "final" and chosen.source_name in {"sofascore", "thesportsdb"}) or (chosen.status_norm == "final" and not win and score_present(chosen.home_score, chosen.away_score)) or (chosen.gender_scope != "women" and chosen.status_norm == "final")
    include_dashboard = chosen.gender_scope == "women" and conf >= 0.55
    include_graphics = chosen.gender_scope == "women" and chosen.status_norm == "final" and conf >= 0.85 and not manual
    headline = f"{win} beat {lose}" if win and lose else f"{chosen.away_team_raw} vs {chosen.home_team_raw}".strip(" vs ")
    subhead = f"Final: {chosen.away_team_norm} {chosen.away_score} - {chosen.home_team_norm} {chosen.home_score}" if chosen.status_norm == "final" and score_present(chosen.home_score, chosen.away_score) else f"Status: {chosen.status_raw}"
    event = Event(run_id, stable_id(run_id, key), key, chosen.source_name, len(valid), json.dumps(sorted({o.source_name for o in valid}), ensure_ascii=False), chosen.sport_norm, chosen.league_norm, chosen.gender_scope, chosen.scheduled_start_utc, chosen.scheduled_date_local, chosen.home_team_norm, chosen.away_team_norm, chosen.status_norm, chosen.status_norm, chosen.home_score, chosen.away_score, win, lose, chosen.score_by_period_json, chosen.team_stats_json, chosen.player_stats_json, chosen.top_performers_json, conf, json.dumps(reasons, ensure_ascii=False), conflict, manual, include_dashboard, include_graphics, 0.0, headline, subhead, chosen.source_url, chosen.source_priority)
    event.editorial_rank = editorial_rank(event)
    return event


def confidence(chosen: Observation, group: list[Observation], conflict: bool) -> tuple[float, dict]:
    score = BASE_WEIGHT.get(chosen.source_name, 0.25)
    reasons = {"base_source": chosen.source_name, "base": score, "adjustments": []}
    def add(name, val):
        nonlocal score
        score += val
        reasons["adjustments"].append([name, val])
    if chosen.status_norm == "final": add("final_state", 0.10)
    if score_present(chosen.home_score, chosen.away_score): add("score_complete", 0.05)
    if clean(chosen.score_by_period_json) not in ["", "{}", "[]", "null"]: add("period_data_present", 0.05)
    chosen_score = (chosen.home_score, chosen.away_score)
    agreeing = {o.source_name for o in group if o.status_norm == "final" and score_present(o.home_score, o.away_score) and (o.home_score, o.away_score) == chosen_score}
    if len(agreeing) >= 2: add("second_source_agrees", 0.10)
    if len(agreeing) >= 3: add("third_source_agrees", 0.05)
    if chosen.home_team_norm and chosen.away_team_norm: add("team_match_quality", 0.04)
    if chosen.source_name in {"sofascore", "thesportsdb"} and len(group) == 1 and chosen.status_norm == "final": add("single_unofficial_source_penalty", -0.15)
    if chosen.source_name == "sofascore" and not any(o.source_name in {"api_sports", "ncaa", "espn_wnba"} for o in group): add("discovery_only_penalty", -0.20)
    if conflict: add("score_conflict_penalty", -0.30)
    if chosen.gender_scope == "women" and chosen.women_match_method in {"keyword", "team_suffix"}: add("gender_inferred_small_penalty", -0.04)
    elif chosen.gender_scope != "women": add("gender_unknown_penalty", -0.20)
    score = max(0.0, min(1.0, score))
    reasons["final_confidence"] = round(score, 3)
    return score, reasons


def editorial_rank(e: Event) -> float:
    blob = " ".join([e.sport_norm, e.league_norm, e.home_team_norm, e.away_team_norm, e.graphics_headline]).lower()
    rank = e.confidence * 100
    if e.status_norm == "final": rank += 15
    if "wnba" in blob: rank += 33
    if "nwsl" in blob or "uswnt" in blob: rank += 30
    if "world cup" in blob: rank += 28
    if "volleyball nations league" in blob: rank += 27
    if "ncaa" in blob: rank += 26
    if e.sport_norm == "basketball": rank += 12
    if e.sport_norm == "soccer": rank += 11
    if e.sport_norm == "volleyball": rank += 9
    if e.manual_review: rank -= 25
    if e.gender_scope != "women": rank -= 100
    return max(0, round(rank, 1))


def reconcile(run_id: str, observations: list[Observation]) -> list[Event]:
    buckets = defaultdict(list)
    for obs in observations:
        if obs.parse_ok:
            buckets[obs.canonical_key].append(obs)
    events = [choose_reconciled(run_id, key, rows) for key, rows in buckets.items()]
    events.sort(key=lambda e: (e.gender_scope != "women", e.status_norm != "final", -e.editorial_rank, e.scheduled_date_local))
    return events


def write_csv(path: str, rows: list[dict], fieldnames: list[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def build_graphics_queue(events: list[Event]) -> str:
    ready = [e for e in events if e.include_in_graphics]
    ready.sort(key=lambda e: -e.editorial_rank)
    lines = ["# Her Sports Daily Results Graphics Queue v4", "", f"Generated: {iso_now()}", "", "Only high-confidence final women's results are included.", "Do not invent player stat lines. If no player data is provided, make a team-result graphic.", ""]
    if not ready:
        lines.append("No high-confidence final women's result graphics are ready right now.")
        return "\n".join(lines)
    for idx, e in enumerate(ready[:25], 1):
        decision = "Must Post" if e.editorial_rank >= 120 else ("Maybe Post" if e.editorial_rank >= 95 else "Low Priority")
        lines.extend([f"## RESULT GRAPHIC {idx}: {e.graphics_headline}", "", f"**Sport:** {e.sport_norm}", f"**League:** {e.league_norm}", f"**Decision:** {decision}", "**Template:** Postgame Result Card", "**Timing:** Post within 1 to 2 hours if fresh", f"**Selected source:** {e.selected_source}", f"**All sources:** {e.all_sources_json}", f"**Confidence:** {e.confidence:.2f}", f"**Manual review:** {'Yes' if e.manual_review else 'No'}", f"**Editorial rank:** {e.editorial_rank:.1f}", "", "### Verified result context", f"- Matchup: {e.away_team_norm} vs {e.home_team_norm}", f"- Final score: {e.away_team_norm} {e.away_score} - {e.home_team_norm} {e.home_score}", f"- Winner: {e.winner}", f"- Loser: {e.loser}", f"- Game status: {e.status_norm}", f"- Date: {e.scheduled_date_local}", f"- Source URL/API: {e.source_url}", "", "### Production accuracy rules", "- Do not change the final score.", "- Do not invent top performer stats.", "- If player box-score data is not provided, make this a team/result graphic.", "- Use the established Her Sports Daily brand colors, font hierarchy, and top-left watermark.", "", "### Slide copy", f"**Slide 1 - Hook:** {e.graphics_headline}", f"{e.graphics_subhead}.", "", "**Slide 2 - Result:** What happened", f"{e.away_team_norm} vs {e.home_team_norm} finished {e.away_score}-{e.home_score}.", "", "**Slide 3 - Context:** Why it matters", "This is part of today’s broader women’s sports results slate.", "", "**Slide 4 - CTA:** Your take?", "Follow Her Sports Daily for more verified women’s sports results.", "", "---", ""])
    return "\n".join(lines)


def build_hub(run_id: str, observations: list[Observation], events: list[Event], health: list[dict], dates: list[str]) -> str:
    women = [e for e in events if e.gender_scope == "women"]
    finals = [e for e in women if e.status_norm == "final"]
    graphics = [e for e in events if e.include_in_graphics]
    review = [e for e in events if e.manual_review and e.gender_scope == "women"]
    by_source, by_sport = {}, {}
    for o in observations: by_source[o.source_name] = by_source.get(o.source_name, 0) + 1
    for e in women: by_sport[e.sport_norm] = by_sport.get(e.sport_norm, 0) + 1
    lines = ["# Her Sports Daily Results Desk v4 Hub", "", f"Run ID: `{run_id}`", f"Generated: `{iso_now()}`", f"Date window: `{', '.join(dates)}`", "", "## Source strategy", "", "- API-Sports is the scoring backbone.", "- ESPN WNBA is backup/verification.", "- NCAA is optional and stale-filtered.", "- SofaScore wrapper is optional discovery/enrichment only.", "", "## Run summary", "", f"- Raw source observations: {len(observations)}", f"- Reconciled events: {len(events)}", f"- Women's events surfaced: {len(women)}", f"- Women's finals: {len(finals)}", f"- Graphics-ready results: {len(graphics)}", f"- Manual review items: {len(review)}", "", "## Observations by source", ""]
    for k, v in sorted(by_source.items()): lines.append(f"- {k}: {v}")
    lines.extend(["", "## Women's events by sport", ""])
    for k, v in sorted(by_sport.items()): lines.append(f"- {k}: {v}")
    if not by_sport: lines.append("- No women's events.")
    lines.extend(["", "## Graphics gate", "", "- include_in_graphics requires women-only, final, confidence >= 0.85, and manual_review = No.", "- Player stats are never invented. If no box-score data exists, packet is a team-result graphic."])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default=os.environ.get("HSD_RESULTS_SOURCES", "apisports,espn"))
    parser.add_argument("--timezone", default=os.environ.get("HSD_TIMEZONE", "America/New_York"))
    parser.add_argument("--lookback-days", type=int, default=int(os.environ.get("HSD_LOOKBACK_DAYS", "1")))
    parser.add_argument("--lookahead-days", type=int, default=int(os.environ.get("HSD_LOOKAHEAD_DAYS", "1")))
    args = parser.parse_args()
    iso_dates, compact_dates = date_window(args.timezone, args.lookback_days, args.lookahead_days)
    run_id = stable_id(iso_now(), args.sources)
    sources = {s.strip().lower() for s in args.sources.split(",") if s.strip()}
    observations, health = [], []
    if "apisports" in sources:
        o, h = fetch_apisports(run_id, iso_dates, os.environ.get("APISPORTS_KEY", "")); observations += o; health += h
    if "espn" in sources or "espn_wnba" in sources:
        o, h = fetch_espn_wnba(run_id, compact_dates); observations += o; health += h
    if "sofascore" in sources or "sofa" in sources:
        o, h = fetch_sofascore(run_id, iso_dates); observations += o; health += h
    events = reconcile(run_id, observations)
    event_fields = [f.name for f in fields(Event)]
    obs_fields = [f.name for f in fields(Observation)]
    all_events = [e.to_dict() for e in events]
    womens = [e.to_dict() for e in events if e.gender_scope == "women" and e.include_in_dashboard]
    finals = [e.to_dict() for e in events if e.gender_scope == "women" and e.status_norm == "final" and e.confidence >= 0.70]
    top = [e.to_dict() for e in events if e.gender_scope == "women" and e.include_in_dashboard][:50]
    review = [e.to_dict() for e in events if e.gender_scope == "women" and e.manual_review]
    write_csv("source_observations.csv", [o.to_dict() for o in observations], obs_fields)
    write_csv("reconciled_events.csv", all_events, event_fields)
    write_csv("today_results_board.csv", all_events, event_fields)
    write_csv("today_womens_results.csv", womens, event_fields)
    write_csv("today_final_results.csv", finals, event_fields)
    write_csv("top_womens_results.csv", top, event_fields)
    write_csv("manual_review_queue.csv", review, event_fields)
    write_csv("source_health_report.csv", health, ["source_name", "sport_or_league", "date", "http_status", "ok", "events_found", "observations_emitted", "stale_rejected", "notes"])
    Path("results_graphics_queue.md").write_text(build_graphics_queue(events), encoding="utf-8")
    Path("results_system_hub.md").write_text(build_hub(run_id, observations, events, health, iso_dates), encoding="utf-8")
    manifest = {"run_id": run_id, "generated_at_utc": iso_now(), "sources": sorted(sources), "date_window": iso_dates, "counts": {"observations": len(observations), "reconciled_events": len(events), "women_events": len(womens), "final_women_events": len(finals), "manual_review": len(review), "graphics_ready": sum(1 for e in events if e.include_in_graphics)}, "source_health": health}
    Path("run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Created Results Desk v4 outputs")
    print(json.dumps(manifest["counts"], indent=2))

if __name__ == "__main__":
    main()
