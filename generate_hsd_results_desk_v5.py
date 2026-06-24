from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

from hsd_run_io import input_path, output_path, write_json, write_text

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

VERSION = "v5.0-free-public-source-accuracy"
RESULTS_TIMEZONE = os.environ.get("HSD_TIMEZONE", "America/New_York")
LOOKBACK_DAYS = int(os.environ.get("HSD_LOOKBACK_DAYS", "1"))
LOOKAHEAD_DAYS = int(os.environ.get("HSD_LOOKAHEAD_DAYS", "1"))
REQUEST_SLEEP_SECONDS = 0.15

OBSERVATIONS_FILE = "source_observations.csv"
RECONCILED_FILE = "reconciled_events.csv"
RESULTS_BOARD_FILE = "today_results_board.csv"
WOMENS_RESULTS_FILE = "today_womens_results.csv"
FINAL_RESULTS_FILE = "today_final_results.csv"
TOP_RESULTS_FILE = "top_womens_results.csv"
MANUAL_REVIEW_FILE = "manual_review_queue.csv"
SOURCE_HEALTH_FILE = "source_health_report.csv"
BOX_SCORE_AUDIT_FILE = "wnba_box_score_audit.csv"
BOX_SCORE_SUMMARY_FILE = "wnba_box_score_summary.md"
GRAPHICS_QUEUE_FILE = "results_graphics_queue.md"
RECOMMENDATIONS_FILE = "daily_results_recommendations.md"
HUB_FILE = "results_system_hub.md"
MANIFEST_FILE = "run_manifest.json"

V5_MANIFEST = output_path("results_desk_v5_manifest.json")
V5_REPORT = output_path("results_desk_v5_report.md")
SOURCE_ACCURACY_JSON = output_path("source_accuracy_v5.json")
SOURCE_ACCURACY_MD = output_path("source_accuracy_v5.md")
DUPLICATE_AUDIT = output_path("duplicate_game_audit_v5.csv")
STALE_AUDIT = output_path("stale_source_audit_v5.csv")
MISSING_ALERT_JSON = output_path("missing_games_alert_v5.json")
MISSING_ALERT_MD = output_path("missing_games_alert_v5.md")
EXPECTED_GAMES = [Path("config/hsd_expected_games_v5.csv"), Path("data/expected_games/wnba_expected_games.csv"), Path("expected_games.csv")]

WNBA_TEAM_ROOTS = {
    "atlanta dream", "chicago sky", "connecticut sun", "dallas wings", "golden state valkyries",
    "indiana fever", "las vegas aces", "los angeles sparks", "minnesota lynx", "new york liberty",
    "phoenix mercury", "portland fire", "seattle storm", "toronto tempo", "washington mystics",
}

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

DUP_FIELDS = ["canonical_key", "source_count", "source_names", "score_variants", "date", "teams", "decision"]
STALE_FIELDS = ["source_name", "source_event_id", "canonical_key", "scheduled_date_local", "status_norm", "source_url", "reason"]
EXPECTED_FIELDS = ["date", "league", "home_team", "away_team", "expected_key", "matched", "matched_event_uid", "reason"]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def low(value: Any) -> str:
    return clean(value).lower()


def slug(value: Any) -> str:
    s = low(value).replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def now_iso() -> str:
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
    if any(x in s for x in ["finished", "match finished", "after fulltime", "after overtime", "final", "ft", "ended"]):
        return "final"
    if any(x in s for x in ["live", "in progress", "quarter", "half", "period"]):
        return "live"
    if any(x in s for x in ["not started", "scheduled", "pre match", "pre-match", "time to be defined"]):
        return "scheduled"
    if any(x in s for x in ["postponed", "cancelled", "canceled", "suspended", "abandoned"]):
        return "not_played"
    return s or "unknown"


def normalize_team(value: Any) -> str:
    s = slug(value)
    replacements = {"united states": "usa", "u s a": "usa", "women": "w", "womens": "w", "women s": "w"}
    for src, dst in replacements.items():
        s = re.sub(rf"\b{re.escape(src)}\b", dst, s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_team_for_context(team: Any, league: Any = "", sport: Any = "") -> str:
    s = normalize_team(team)
    if clean(league).upper() == "WNBA" or s in WNBA_TEAM_ROOTS:
        s = re.sub(r"\bw$", "", s).strip()
    return s


def canonical_key(sport: str, date_local: str, home: str, away: str, league: str = "") -> str:
    pair = sorted([normalize_team_for_context(home, league, sport), normalize_team_for_context(away, league, sport)])
    return "|".join([clean(sport), clean(date_local), pair[0], pair[1]])


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


def score_signature(obs: Dict[str, str]) -> str:
    if not score_present(obs.get("home_score"), obs.get("away_score")):
        return "no_score"
    pairs = sorted([(clean(obs.get("home_team_norm")), clean(obs.get("home_score"))), (clean(obs.get("away_team_norm")), clean(obs.get("away_score")))])
    return json.dumps(pairs, sort_keys=True)


def allowed_sources() -> List[str]:
    raw = os.environ.get("HSD_RESULTS_V5_SOURCES", "espn_wnba_public,manual_seed")
    allowed = {"espn_wnba_public", "manual_seed"}
    return [s for s in [x.strip().lower() for x in raw.split(",") if x.strip()] if s in allowed]


def fetch_espn_wnba(run_id: str, compact_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    endpoint = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"
    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    for date_compact in compact_dates:
        try:
            r = requests.get(endpoint, params={"dates": date_compact}, headers={"User-Agent": "HerSportsDailyResultsDesk/5.0"}, timeout=30)
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
                score_periods: Dict[str, Any] = {}
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
                    "source_name": "espn_wnba_public",
                    "source_priority": "95",
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
                    "fetched_at_utc": now_iso(),
                    "http_status": str(status),
                    "parse_ok": "Yes",
                    "stale_rejected": "No",
                    "women_match_method": "explicit_league",
                    "raw_archive_path": "",
                    "notes": f"requested_date={date_compact}; free public ESPN scoreboard endpoint",
                })
                emitted += 1
            except Exception:
                pass
        health.append({"source_name": "espn_wnba_public", "sport_or_league": "WNBA", "date": date_compact, "http_status": status, "ok": "Yes" if status == 200 and not error else "No", "events_found": len(events), "observations_emitted": emitted, "stale_rejected": 0, "notes": error or "free public ESPN scoreboard endpoint ok"})
        time.sleep(REQUEST_SLEEP_SECONDS)
    return observations, health


def read_csv(path: Path) -> List[Dict[str, str]]:
    path = input_path(path)
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def normalize_manual_seed_row(run_id: str, row: Dict[str, str], source_file: str) -> Dict[str, str] | None:
    league = clean(row.get("league") or "WNBA")
    sport = clean(row.get("sport") or "basketball")
    date = clean(row.get("scheduled_date_local") or row.get("event_date_local") or row.get("date"))
    home = clean(row.get("home_team") or row.get("home_team_name"))
    away = clean(row.get("away_team") or row.get("away_team_name"))
    if not date or not home or not away:
        return None
    status = normalize_status(row.get("status") or row.get("status_norm") or "scheduled")
    return {
        "run_id": run_id, "source_name": "manual_seed", "source_priority": "100", "source_event_id": clean(row.get("source_event_id") or row.get("event_id")),
        "canonical_key": canonical_key(sport, date, home, away, league), "sport_norm": sport, "league_norm": league, "competition_id": clean(row.get("competition_id") or "manual"),
        "gender_scope": clean(row.get("gender_scope") or "women"), "scheduled_start_utc": clean(row.get("scheduled_start_utc")), "scheduled_date_local": date,
        "home_team_raw": home, "away_team_raw": away, "home_team_norm": normalize_team_for_context(home, league, sport), "away_team_norm": normalize_team_for_context(away, league, sport),
        "status_raw": status, "status_norm": status, "home_score": clean(row.get("home_score") or row.get("score_home")), "away_score": clean(row.get("away_score") or row.get("score_away")),
        "score_by_period_json": clean(row.get("score_by_period_json")), "team_stats_json": clean(row.get("team_stats_json")), "player_stats_json": clean(row.get("player_stats_json")), "top_performers_json": clean(row.get("top_performers_json")),
        "source_url": clean(row.get("source_url") or source_file), "fetched_at_utc": now_iso(), "http_status": "0", "parse_ok": "Yes", "stale_rejected": "No", "women_match_method": "manual_seed", "raw_archive_path": source_file, "notes": "manual seed fallback; user/source reviewed",
    }


def load_manual_seed_observations(run_id: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in [Path("manual_results_seed.csv"), Path("data/manual_results_seed.csv"), Path("config/manual_results_seed.csv")]:
        for row in read_csv(path):
            obs = normalize_manual_seed_row(run_id, row, path.as_posix())
            if obs:
                rows.append(obs)
    return rows


def free_source_observations(run_id: str, compact_dates: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    observations: List[Dict[str, str]] = []
    health: List[Dict[str, Any]] = []
    sources = allowed_sources()
    if "espn_wnba_public" in sources:
        obs, h = fetch_espn_wnba(run_id, compact_dates)
        observations.extend(obs)
        health.extend(h)
    manual_rows = load_manual_seed_observations(run_id)
    if manual_rows:
        observations.extend(manual_rows)
        health.append({"source_name": "manual_seed", "sport_or_league": "all", "date": "", "http_status": 0, "ok": "Yes", "events_found": len(manual_rows), "observations_emitted": len(manual_rows), "stale_rejected": 0, "notes": "manual seed rows loaded from free local files"})
    elif "manual_seed" in sources:
        health.append({"source_name": "manual_seed", "sport_or_league": "all", "date": "", "http_status": 0, "ok": "Yes", "events_found": 0, "observations_emitted": 0, "stale_rejected": 0, "notes": "optional fallback; no manual seed file found"})
    return observations, health


def score_display(obs: Dict[str, str]) -> str:
    away, home, a, h = clean(obs.get("away_team_raw")), clean(obs.get("home_team_raw")), clean(obs.get("away_score")), clean(obs.get("home_score"))
    if away and home and a != "" and h != "":
        return f"{away} {a} · {home} {h}"
    return f"{away} at {home}".strip()


def headline_for(obs: Dict[str, str], winner: str, loser: str) -> str:
    if winner and loser:
        return f"{winner} beat {loser}"
    away, home = clean(obs.get("away_team_raw")), clean(obs.get("home_team_raw"))
    return f"{away} at {home}" if away and home else "WNBA result"


def confidence_for(chosen: Dict[str, str], group: List[Dict[str, str]], conflict: bool) -> Tuple[float, Dict[str, Any]]:
    score = 0.78 if chosen.get("source_name") == "espn_wnba_public" else 0.86 if chosen.get("source_name") == "manual_seed" else 0.50
    reasons: Dict[str, Any] = {"base_source": chosen.get("source_name"), "base": score, "adjustments": []}
    if chosen.get("status_norm") == "final":
        score += 0.08; reasons["adjustments"].append(["final_state", 0.08])
    if score_present(chosen.get("home_score"), chosen.get("away_score")):
        score += 0.06; reasons["adjustments"].append(["score_complete", 0.06])
    if len(group) >= 2 and not conflict:
        score += 0.08; reasons["adjustments"].append(["multi_source_same_key", 0.08])
    if conflict:
        score -= 0.30; reasons["adjustments"].append(["score_conflict", -0.30])
    score = max(0.0, min(1.0, score)); reasons["final_confidence"] = round(score, 3)
    return score, reasons


def apply_event_gates(event: Dict[str, Any]) -> None:
    rank = float(event.get("confidence") or 0) * 100
    if event.get("league_norm") == "WNBA":
        rank += 70
    if event.get("status_norm") == "final":
        rank += 15
    event["editorial_rank"] = round(rank, 1)
    if event.get("gender_scope") == "women" and event.get("status_norm") == "final" and not event.get("manual_review") and float(event.get("confidence") or 0) >= 0.82:
        event["include_in_graphics"] = True
        event["editorial_bucket"] = "Must Post" if event["editorial_rank"] >= 145 else "Strong Maybe" if event["editorial_rank"] >= 120 else "Watchlist"
        event["content_action"] = "Make First" if event["editorial_bucket"] == "Must Post" else event["editorial_bucket"]
        event["posting_priority"] = "P1" if event["editorial_bucket"] == "Must Post" else "P2" if event["editorial_bucket"] == "Strong Maybe" else "P3"
    elif event.get("gender_scope") == "women":
        event["editorial_bucket"] = "Watchlist"; event["content_action"] = "Watch"; event["posting_priority"] = "Review"


def reconcile(run_id: str, observations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for obs in observations:
        if clean(obs.get("canonical_key")):
            grouped[obs["canonical_key"]].append(obs)
    events: List[Dict[str, Any]] = []
    for key, group in grouped.items():
        group.sort(key=lambda r: int(r.get("source_priority") or 0), reverse=True)
        chosen = group[0]
        sigs = {score_signature(obs) for obs in group if score_signature(obs) != "no_score"}
        conflict = len(sigs) > 1
        winner, loser = score_winner(chosen.get("home_team_raw", ""), chosen.get("away_team_raw", ""), chosen.get("home_score"), chosen.get("away_score"))
        status = chosen.get("status_norm", "unknown")
        final_score_display = score_display(chosen)
        confidence, reasons = confidence_for(chosen, group, conflict)
        manual_review = conflict or chosen.get("gender_scope") != "women" or (status == "final" and not score_present(chosen.get("home_score"), chosen.get("away_score")))
        event = {"run_id": run_id, "event_uid": "event_" + stable_id(key), "canonical_key": key, "selected_source": chosen.get("source_name", ""), "source_count": len(group), "all_sources_json": json.dumps(sorted({obs.get("source_name", "") for obs in group}), ensure_ascii=False), "sport_norm": chosen.get("sport_norm", ""), "league_norm": chosen.get("league_norm", ""), "gender_scope": chosen.get("gender_scope", ""), "scheduled_start_utc": chosen.get("scheduled_start_utc", ""), "scheduled_date_local": chosen.get("scheduled_date_local", ""), "home_team_norm": chosen.get("home_team_norm", ""), "away_team_norm": chosen.get("away_team_norm", ""), "home_team_display": chosen.get("home_team_raw", ""), "away_team_display": chosen.get("away_team_raw", ""), "final_score_display": final_score_display, "game_state": status, "status_norm": status, "home_score": chosen.get("home_score", ""), "away_score": chosen.get("away_score", ""), "winner": winner, "loser": loser, "outcome_type": "win" if status == "final" and winner and loser else status, "editorial_tier": "Tier 1" if chosen.get("league_norm") == "WNBA" else "Tier 3", "editorial_bucket": "Archive Only", "content_action": "Archive", "content_family": "Tonight in the W" if chosen.get("league_norm") == "WNBA" else "Results Desk", "posting_priority": "Archive Only", "caption_seed": f"{winner} defeated {loser}, {final_score_display}." if winner and loser else final_score_display, "score_by_period_json": chosen.get("score_by_period_json", ""), "team_stats_json": chosen.get("team_stats_json", ""), "player_stats_json": chosen.get("player_stats_json", ""), "top_performers_json": chosen.get("top_performers_json", ""), "confidence": confidence, "confidence_reason_json": json.dumps(reasons, ensure_ascii=False), "score_conflict": conflict, "manual_review": manual_review, "include_in_dashboard": chosen.get("gender_scope") == "women", "include_in_graphics": False, "editorial_rank": 0.0, "graphics_headline": headline_for(chosen, winner, loser), "graphics_subhead": final_score_display, "source_url": chosen.get("source_url", ""), "source_priority": int(chosen.get("source_priority") or 0), "espn_event_id": chosen.get("source_event_id", "") if chosen.get("source_name") == "espn_wnba_public" else "", "slide_3_context": "This result is sourced from free public scoreboard data and remains human-review first."}
        apply_event_gates(event); events.append(event)
    events.sort(key=lambda e: (e.get("gender_scope") != "women", e.get("status_norm") != "final", -float(e.get("editorial_rank", 0)), e.get("scheduled_date_local", "")))
    return events


def apply_strict_date_window_gate(events: List[Dict[str, Any]], iso_dates: List[str]) -> List[Dict[str, Any]]:
    dates = set(iso_dates)
    for event in events:
        date = clean(event.get("scheduled_date_local"))
        status = "in_window" if date in dates else "missing_date" if not date else "outside_window"
        event["date_window_status"] = status; event["is_carryover"] = "No" if status == "in_window" else "Yes"
        if status != "in_window":
            event["include_in_graphics"] = False; event["content_action"] = "Archive"; event["editorial_bucket"] = "Archive Only"; event["posting_priority"] = "Archive Only"
    return events


def duplicate_audit(observations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for obs in observations:
        grouped[clean(obs.get("canonical_key")) or f"missing|{len(grouped)}"].append(obs)
    rows: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        scores = sorted(set(score_signature(obs) for obs in group)); sources = sorted(set(clean(obs.get("source_name")) for obs in group if clean(obs.get("source_name")))); first = group[0]
        rows.append({"canonical_key": key, "source_count": len(group), "source_names": ";".join(sources), "score_variants": " || ".join(scores), "date": first.get("scheduled_date_local", ""), "teams": f"{first.get('away_team_raw')} at {first.get('home_team_raw')}", "decision": "merge_same_score" if len(scores) == 1 else "manual_review_score_conflict"})
    return rows


def stale_audit(observations: List[Dict[str, str]], iso_dates: List[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []; dates = set(iso_dates)
    for obs in observations:
        date = clean(obs.get("scheduled_date_local"))
        if not date or date not in dates:
            obs["stale_rejected"] = "Yes"
            rows.append({"source_name": obs.get("source_name"), "source_event_id": obs.get("source_event_id"), "canonical_key": obs.get("canonical_key"), "scheduled_date_local": date, "status_norm": obs.get("status_norm"), "source_url": obs.get("source_url"), "reason": "missing_scheduled_date" if not date else f"outside_window:{date}"})
    return rows


def write_csv(path: str | Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    out = output_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore"); writer.writeheader()
        for row in rows:
            out: Dict[str, Any] = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, bool): value = "Yes" if value else "No"
                elif isinstance(value, float) and field in {"confidence", "editorial_rank"}: value = f"{value:.2f}" if field == "confidence" else f"{value:.1f}"
                out[field] = value
            writer.writerow(out)


def expected_game_rows() -> List[Dict[str, str]]:
    for path in EXPECTED_GAMES:
        rows = read_csv(path)
        if rows: return rows
    return []


def expected_key(row: Dict[str, str]) -> str:
    date = clean(row.get("date") or row.get("scheduled_date_local") or row.get("event_date_local")); league = clean(row.get("league") or "WNBA"); sport = clean(row.get("sport") or "basketball"); home = clean(row.get("home_team") or row.get("home_team_name")); away = clean(row.get("away_team") or row.get("away_team_name"))
    return canonical_key(sport, date, home, away, league) if date and home and away else ""


def missing_games_alert(expected_rows: List[Dict[str, str]], events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    event_by_key = {clean(e.get("canonical_key")): e for e in events if clean(e.get("canonical_key"))}; rows: List[Dict[str, str]] = []
    for row in expected_rows:
        key = expected_key(row); matched = key in event_by_key; event = event_by_key.get(key, {})
        rows.append({"date": clean(row.get("date") or row.get("scheduled_date_local") or row.get("event_date_local")), "league": clean(row.get("league") or "WNBA"), "home_team": clean(row.get("home_team") or row.get("home_team_name")), "away_team": clean(row.get("away_team") or row.get("away_team_name")), "expected_key": key, "matched": "Yes" if matched else "No", "matched_event_uid": clean(event.get("event_uid")), "reason": "matched" if matched else "missing_from_free_sources_or_outside_window"})
    summary = {"expected_fixture_file_present": bool(expected_rows), "expected_games": len(expected_rows), "matched": sum(1 for row in rows if row.get("matched") == "Yes"), "missing": sum(1 for row in rows if row.get("matched") == "No")}
    return rows, summary


def extract_espn_top_performers(summary: Dict[str, Any]) -> List[str]:
    candidates: List[Tuple[int, str]] = []
    for team_block in ((summary.get("boxscore") or {}).get("players") or []):
        team = clean(((team_block.get("team") or {}).get("displayName")))
        for stat_group in team_block.get("statistics") or []:
            labels = [clean(x) for x in (stat_group.get("labels") or [])]
            for athlete in stat_group.get("athletes") or []:
                name = clean(((athlete.get("athlete") or {}).get("displayName"))); values = athlete.get("stats") or []
                if not name: continue
                stat_map = {labels[i]: clean(values[i]) for i in range(min(len(labels), len(values)))}; score = 0; parts = []
                for key, mult in {"PTS": 1, "REB": 1, "AST": 1, "STL": 2, "BLK": 2}.items():
                    value = stat_map.get(key)
                    if value and value not in {"0", "0.0"}:
                        parts.append(f"{key} {value}")
                        try: score += int(float(value.split("-")[0])) * mult
                        except Exception: pass
                if parts: candidates.append((score, f"{name} ({team}): {', '.join(parts[:4])}"))
    candidates.sort(reverse=True, key=lambda x: x[0]); out: List[str] = []; seen: set[str] = set()
    for _, line in candidates:
        name = line.split(" (")[0]
        if name not in seen: seen.add(name); out.append(line)
        if len(out) >= 3: break
    return out


def audit_wnba_box_scores(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if low(os.environ.get("HSD_WNBA_BOX_AUDIT", "true")) in {"0", "false", "no"}: return []
    rows: List[Dict[str, Any]] = []
    for event in [e for e in events if e.get("league_norm") == "WNBA" and e.get("espn_event_id")][:10]:
        event_id = event.get("espn_event_id"); url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/summary"
        try:
            r = requests.get(url, params={"event": event_id}, headers={"User-Agent": "HerSportsDailyResultsDesk/5.0"}, timeout=30); status = r.status_code; r.raise_for_status(); performers = extract_espn_top_performers(r.json()); audit_status = "found" if performers else "summary_found_no_performers"
            if performers: event["box_score_top_performers"] = " | ".join(performers); event["slide_3_context"] = f"Box-score context available: {event['box_score_top_performers']}"
            rows.append({"event_uid": event.get("event_uid"), "espn_event_id": event_id, "graphics_headline": event.get("graphics_headline"), "league_norm": event.get("league_norm"), "http_status": status, "audit_status": audit_status, "top_performers": event.get("box_score_top_performers", ""), "source_url": f"https://www.espn.com/wnba/game/_/gameId/{event_id}", "notes": ""})
        except Exception as exc:
            rows.append({"event_uid": event.get("event_uid"), "espn_event_id": event_id, "graphics_headline": event.get("graphics_headline"), "league_norm": event.get("league_norm"), "http_status": 0, "audit_status": "error", "top_performers": "", "source_url": f"https://www.espn.com/wnba/game/_/gameId/{event_id}", "notes": str(exc)})
        time.sleep(REQUEST_SLEEP_SECONDS)
    return rows


def box_score_summary_md(rows: List[Dict[str, Any]]) -> str:
    lines = ["# WNBA Box-Score Enrichment Audit v5", "", f"Generated: {now_iso()}", ""]
    if not rows: lines.append("No WNBA box-score audit rows were produced."); return "\n".join(lines) + "\n"
    for idx, row in enumerate(rows, 1):
        lines.append(f"{idx}. **{row.get('graphics_headline')}**"); lines.append(f"   - ESPN event: {row.get('espn_event_id')}"); lines.append(f"   - Status: {row.get('audit_status')}")
        if row.get("top_performers"): lines.append(f"   - Top performers: {row.get('top_performers')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def graphics_queue(events: List[Dict[str, Any]]) -> str:
    ready = [e for e in events if e.get("include_in_graphics")]; ready.sort(key=lambda e: (-float(e.get("editorial_rank") or 0), e.get("scheduled_date_local", "")))
    lines = ["# Her Sports Daily Results Graphics Queue v5", "", f"Generated: {now_iso()}", "", "## Queue rules", "", "- Free/public sources only.", "- Do not invent player stats.", "- Auto-rendered graphics remain human-review only.", ""]
    if not ready: lines.append("No high-confidence final women's result graphics are ready right now."); return "\n".join(lines) + "\n"
    for idx, e in enumerate(ready[:20], 1):
        lines.extend([f"## RESULT GRAPHIC {idx}: {e.get('graphics_headline')}", "", f"**League:** {e.get('league_norm')}", f"**Selected source:** {e.get('selected_source')}", f"**Confidence:** {float(e.get('confidence') or 0):.2f}", f"**Final score:** {e.get('final_score_display')}", f"**Source:** {e.get('source_url')}", "", "### Accuracy rules", "- Do not change the final score.", "- Do not invent top performer stats.", "- Use official/approved assets only.", "", "---", ""])
    return "\n".join(lines) + "\n"


def recommendations_md(events: List[Dict[str, Any]]) -> str:
    ready = [e for e in events if e.get("include_in_dashboard")]; ready.sort(key=lambda e: (-float(e.get("editorial_rank") or 0), e.get("scheduled_date_local", "")))
    lines = ["# Her Sports Daily Daily Results Recommendations v5", "", "Free/public source accuracy layer. Human review before posting.", "", "## Top rows", ""]
    if not ready: lines.append("No women's result rows surfaced.")
    for idx, e in enumerate(ready[:30], 1):
        lines.append(f"{idx}. **{e.get('graphics_headline')}**"); lines.append(f"   - {e.get('league_norm')} | {e.get('status_norm')} | confidence {float(e.get('confidence') or 0):.2f} | {e.get('editorial_bucket')}"); lines.append(f"   - {e.get('graphics_subhead')}"); lines.append(f"   - Source: {e.get('source_url')}"); lines.append("")
    return "\n".join(lines) + "\n"


def source_accuracy(events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], duplicates: List[Dict[str, Any]], stale: List[Dict[str, Any]], expected_summary: Dict[str, Any]) -> Dict[str, Any]:
    women = [e for e in events if e.get("gender_scope") == "women"]; finals = [e for e in women if e.get("status_norm") == "final"]
    return {"version": VERSION, "generated_at_utc": now_iso(), "free_only": True, "paid_sources_required": False, "source_policy": "free public ESPN WNBA scoreboard plus optional local manual seed; no paid APIs required", "counts": {"observations": len(observations), "reconciled_events": len(events), "women_events": len(women), "women_finals": len(finals), "duplicate_groups": len(duplicates), "stale_observations": len(stale), "source_health_rows": len(health), **{f"expected_{k}": v for k, v in expected_summary.items()}}, "health": health, "risk_flags": {"stale_observations_present": bool(stale), "missing_expected_games_present": expected_summary.get("missing", 0) > 0, "expected_games_fixture_missing": not expected_summary.get("expected_fixture_file_present")}}


def write_source_accuracy_md(data: Dict[str, Any]) -> str:
    lines = ["# HSD Source Accuracy v5", "", f"Generated: `{data.get('generated_at_utc')}`", f"Version: `{VERSION}`", "", "## Source policy", "", "- Free/public sources only.", "- No paid sports data, paid search, paid scraping proxy, or LLM dependency is required.", "- Current source: public ESPN WNBA scoreboard endpoint plus optional local manual seed fallback.", "", "## Counts", ""]
    for key, value in data.get("counts", {}).items(): lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Risk flags", ""])
    for key, value in data.get("risk_flags", {}).items(): lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def missing_games_md(summary: Dict[str, Any], rows: List[Dict[str, str]]) -> str:
    lines = ["# Missing Games Alert v5", "", f"Generated: `{now_iso()}`", "", "## Summary", ""]
    for key, value in summary.items(): lines.append(f"- {key}: `{value}`")
    lines.append("")
    if not summary.get("expected_fixture_file_present"):
        lines.extend(["## Status", "", "No expected-games fixture file was found. V5 can audit source coverage and duplicates, but cannot prove complete slate coverage without an expected-games fixture.", "Add `config/hsd_expected_games_v5.csv` with columns `date,league,home_team,away_team` when testing a known slate."])
    elif summary.get("missing", 0):
        lines.extend(["## Missing", ""])
        for row in rows:
            if row.get("matched") == "No": lines.append(f"- {row.get('date')} | {row.get('league')} | {row.get('away_team')} at {row.get('home_team')} | {row.get('reason')}")
    else: lines.extend(["## Status", "", "All expected games matched current free-source observations."])
    return "\n".join(lines) + "\n"


def v5_hub_md(run_id: str, events: List[Dict[str, Any]], observations: List[Dict[str, str]], health: List[Dict[str, Any]], iso_dates: List[str]) -> str:
    women = [e for e in events if e.get("gender_scope") == "women"]; finals = [e for e in women if e.get("status_norm") == "final"]; graphics = [e for e in events if e.get("include_in_graphics")]; review = [e for e in events if e.get("manual_review") and e.get("gender_scope") == "women"]
    return "\n".join(["# Her Sports Daily Results Desk v5 Hub", "", f"Run ID: `{run_id}`", f"Generated: `{now_iso()}`", f"Date window: `{', '.join(iso_dates)}`", "", "## Source strategy", "", "- Free/public sources only.", "- Active source: ESPN public WNBA scoreboard endpoint.", "- Optional fallback: local/manual seed CSVs.", "- Paid API keys are not required and are not read by v5.", "", "## Run summary", "", f"- Raw source observations: {len(observations)}", f"- Reconciled events: {len(events)}", f"- Women's events surfaced: {len(women)}", f"- Women's finals: {len(finals)}", f"- Graphics-ready results: {len(graphics)}", f"- Manual review items: {len(review)}", "", "## Accuracy gates", "", "- Duplicate groups are written to `duplicate_game_audit_v5.csv`.", "- Stale/out-of-window observations are written to `stale_source_audit_v5.csv`.", "- Expected-game fixtures, when provided, are checked in `missing_games_alert_v5.*`.", "- No player stats are invented."]) + "\n"


def report_md(run_id: str, manifest: Dict[str, Any]) -> str:
    lines = ["# Her Sports Daily Results Desk v5", "", f"Run ID: `{run_id}`", f"Generated: `{manifest.get('generated_at_utc')}`", f"Version: `{VERSION}`", "", "## What v5 changes", "", "- Removes paid source reliance from the active Results Desk path.", "- Uses free/public WNBA scoreboard data plus manual seed fallback.", "- Keeps v4-compatible output filenames so existing contracts, story results, and graphics packs keep working.", "- Adds duplicate, stale-source, expected-game, and source-health audits.", "", "## Counts", ""]
    for key, value in manifest.get("counts", {}).items(): lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    iso_dates, compact_dates = date_window(); run_id = stable_id(now_iso(), VERSION, ",".join(allowed_sources()))
    observations, health = free_source_observations(run_id, compact_dates); stale_rows = stale_audit(observations, iso_dates); duplicate_rows = duplicate_audit(observations)
    events = apply_strict_date_window_gate(reconcile(run_id, observations), iso_dates); box_audit_rows = audit_wnba_box_scores(events)
    all_events = events; womens = [e for e in events if e.get("gender_scope") == "women" and e.get("include_in_dashboard")]; finals = [e for e in events if e.get("gender_scope") == "women" and e.get("status_norm") == "final" and float(e.get("confidence") or 0) >= 0.70]; top = womens[:50]; review = [e for e in events if e.get("gender_scope") == "women" and e.get("manual_review")]
    expected_rows, expected_summary = missing_games_alert(expected_game_rows(), events); accuracy = source_accuracy(events, observations, health, duplicate_rows, stale_rows, expected_summary)
    write_csv(OBSERVATIONS_FILE, observations, OBS_FIELDS); write_csv(RECONCILED_FILE, events, EVENT_FIELDS); write_csv(RESULTS_BOARD_FILE, all_events, EVENT_FIELDS); write_csv(WOMENS_RESULTS_FILE, womens, EVENT_FIELDS); write_csv(FINAL_RESULTS_FILE, finals, EVENT_FIELDS); write_csv(TOP_RESULTS_FILE, top, EVENT_FIELDS); write_csv(MANUAL_REVIEW_FILE, review, EVENT_FIELDS)
    write_csv(SOURCE_HEALTH_FILE, health, ["source_name", "sport_or_league", "date", "http_status", "ok", "events_found", "observations_emitted", "stale_rejected", "notes"]); write_csv(BOX_SCORE_AUDIT_FILE, box_audit_rows, ["event_uid", "espn_event_id", "graphics_headline", "league_norm", "http_status", "audit_status", "top_performers", "source_url", "notes"]); write_csv(DUPLICATE_AUDIT, duplicate_rows, DUP_FIELDS); write_csv(STALE_AUDIT, stale_rows, STALE_FIELDS); write_csv("missing_games_alert_v5.csv", expected_rows, EXPECTED_FIELDS)
    write_text(BOX_SCORE_SUMMARY_FILE, box_score_summary_md(box_audit_rows)); write_text(GRAPHICS_QUEUE_FILE, graphics_queue(events)); write_text(RECOMMENDATIONS_FILE, recommendations_md(events)); write_text(HUB_FILE, v5_hub_md(run_id, events, observations, health, iso_dates))
    write_json(SOURCE_ACCURACY_JSON, accuracy); write_text(SOURCE_ACCURACY_MD, write_source_accuracy_md(accuracy)); write_json(MISSING_ALERT_JSON, {"summary": expected_summary, "rows": expected_rows}); write_text(MISSING_ALERT_MD, missing_games_md(expected_summary, expected_rows))
    manifest = {"version": VERSION, "run_id": run_id, "generated_at_utc": now_iso(), "sources": allowed_sources(), "date_window": iso_dates, "free_only": True, "paid_sources_required": False, "counts": {"observations": len(observations), "reconciled_events": len(events), "women_events": len(womens), "final_women_events": len(finals), "manual_review": len(review), "graphics_ready": sum(1 for e in events if e.get("include_in_graphics")), "must_post": sum(1 for e in events if e.get("editorial_bucket") == "Must Post"), "strong_maybe": sum(1 for e in events if e.get("editorial_bucket") == "Strong Maybe"), "watchlist": sum(1 for e in events if e.get("editorial_bucket") == "Watchlist"), "carryover_archived": sum(1 for e in events if e.get("is_carryover") == "Yes"), "wnba_box_audit_rows": len(box_audit_rows), "duplicate_groups": len(duplicate_rows), "stale_observations": len(stale_rows), "expected_games": expected_summary.get("expected_games", 0), "missing_expected_games": expected_summary.get("missing", 0)}, "source_health": health, "v5_audit_files": {"source_accuracy": SOURCE_ACCURACY_JSON.as_posix(), "duplicates": DUPLICATE_AUDIT.as_posix(), "stale": STALE_AUDIT.as_posix(), "missing_games": MISSING_ALERT_JSON.as_posix()}}
    write_json(MANIFEST_FILE, manifest); write_json(V5_MANIFEST, manifest); write_text(V5_REPORT, report_md(run_id, manifest))
    print("Created Results Desk v5 outputs"); print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
