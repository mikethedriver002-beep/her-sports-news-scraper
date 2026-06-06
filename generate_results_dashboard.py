
"""
Her Sports Daily Results Desk
-----------------------------

Purpose
- Build an accuracy-first results and box-score system for women's sports.
- Keep this separate from the broader news/story pipeline.
- Prefer structured scoreboard data over article context.

Phase 1 sports
- WNBA
- NCAA Women's Basketball
- NCAA Softball

Outputs
- today_results_board.csv
- today_box_scores.csv
- top_performers.csv
- results_graphics_queue.md
- results_dashboard_seed.csv
- results_system_hub.md
"""

from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailyResultsDesk/2.0; +https://github.com/)"
}

# ESPN scoreboard endpoints can return stale/latest available events when no date is supplied.
# To avoid old games appearing as current results, the Results Desk now queries an explicit
# date window around the current Eastern date.
RESULTS_TIMEZONE = "America/New_York"
LOOKBACK_DAYS = 1
LOOKAHEAD_DAYS = 1

RESULTS_BOARD_FILE = "today_results_board.csv"
BOX_SCORES_FILE = "today_box_scores.csv"
TOP_PERFORMERS_FILE = "top_performers.csv"
GRAPHICS_QUEUE_FILE = "results_graphics_queue.md"
DASHBOARD_SEED_FILE = "results_dashboard_seed.csv"
HUB_FILE = "results_system_hub.md"

SOURCES = [
    {
        "sport_group": "WNBA",
        "sport": "basketball",
        "league": "wnba",
        "label": "WNBA",
    },
    {
        "sport_group": "NCAA Women's Basketball",
        "sport": "basketball",
        "league": "womens-college-basketball",
        "label": "NCAA Women's Basketball",
    },
    {
        "sport_group": "NCAA Softball",
        "sport": "softball",
        "league": "college-softball",
        "label": "NCAA Softball",
    },
]


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except Exception:
        return default


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_local_date():
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo(RESULTS_TIMEZONE)).date()
    return datetime.now(timezone.utc).date()


def scoreboard_dates() -> List[str]:
    today = current_local_date()
    dates = []
    for offset in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1):
        dates.append((today + timedelta(days=offset)).strftime("%Y%m%d"))
    return dates


def status_bucket(status_name: str) -> str:
    s = clean(status_name).lower()
    if any(x in s for x in ["final", "postponed", "canceled"]):
        return "final" if "final" in s else "not_played"
    if any(x in s for x in ["in progress", "halftime", "end of", "live"]):
        return "live"
    return "upcoming"


def request_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.get(url, params=params or {}, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def scoreboard_url(sport: str, league: str) -> str:
    return f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"


def summary_url(sport: str, league: str) -> str:
    return f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary"


def get_scoreboard(source: Dict[str, str], date_string: str) -> Dict[str, Any]:
    return request_json(scoreboard_url(source["sport"], source["league"]), params={"dates": date_string})


def get_summary(source: Dict[str, str], event_id: str) -> Dict[str, Any]:
    return request_json(summary_url(source["sport"], source["league"]), params={"event": event_id})


def team_record_from_competitor(comp: Dict[str, Any]) -> str:
    records = comp.get("records") or []
    summaries = [clean(r.get("summary")) for r in records if clean(r.get("summary"))]
    return ", ".join(summaries)


def get_competitors(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    competitions = event.get("competitions") or []
    if not competitions:
        return []
    return competitions[0].get("competitors") or []


def split_home_away(competitors: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    home = {}
    away = {}
    for comp in competitors:
        if clean(comp.get("homeAway")).lower() == "home":
            home = comp
        elif clean(comp.get("homeAway")).lower() == "away":
            away = comp
    if not home and competitors:
        home = competitors[0]
    if not away and len(competitors) > 1:
        away = competitors[1]
    return home, away


def team_name(comp: Dict[str, Any]) -> str:
    team = comp.get("team") or {}
    return clean(team.get("displayName") or team.get("shortDisplayName") or team.get("name"))


def team_abbrev(comp: Dict[str, Any]) -> str:
    team = comp.get("team") or {}
    return clean(team.get("abbreviation") or team.get("shortDisplayName") or team.get("name"))


def team_logo(comp: Dict[str, Any]) -> str:
    team = comp.get("team") or {}
    logos = team.get("logos") or []
    if logos:
        return clean(logos[0].get("href"))
    return ""


def detect_winner(home: Dict[str, Any], away: Dict[str, Any]) -> Tuple[str, str]:
    home_name = team_name(home)
    away_name = team_name(away)
    home_score = safe_int(home.get("score"))
    away_score = safe_int(away.get("score"))

    if str(home.get("winner", "")).lower() == "true":
        return home_name, away_name
    if str(away.get("winner", "")).lower() == "true":
        return away_name, home_name
    if home_score > away_score:
        return home_name, away_name
    if away_score > home_score:
        return away_name, home_name
    return "", ""


def summarize_periods(event: Dict[str, Any]) -> str:
    competitions = event.get("competitions") or []
    if not competitions:
        return ""
    competitors = competitions[0].get("competitors") or []
    pieces = []
    for comp in competitors:
        periods = comp.get("linescores") or []
        values = []
        for period in periods:
            values.append(clean(period.get("displayValue") or period.get("value")))
        values = [v for v in values if v]
        if values:
            pieces.append(f"{team_abbrev(comp)}: {' | '.join(values)}")
    return " || ".join(pieces)


def performer_score(stat_map: Dict[str, str]) -> int:
    score = 0
    weights = {
        "PTS": 1, "REB": 1, "AST": 1, "STL": 2, "BLK": 2,
        "R": 1, "H": 2, "RBI": 2, "HR": 4, "SO": 2, "IP": 1,
    }
    for key, mult in weights.items():
        if key in stat_map:
            try:
                raw = str(stat_map[key]).split("-")[0]
                score += int(float(raw)) * mult
            except Exception:
                pass
    return score


def extract_top_performers_from_summary(summary: Dict[str, Any], source_label: str) -> List[Dict[str, str]]:
    boxscore = summary.get("boxscore") or {}
    players = boxscore.get("players") or []
    candidates = []

    for team_block in players:
        team = clean((team_block.get("team") or {}).get("displayName"))
        statistics = team_block.get("statistics") or []
        for stat_group in statistics:
            labels = stat_group.get("labels") or []
            athletes = stat_group.get("athletes") or []
            for athlete in athletes:
                name = clean((athlete.get("athlete") or {}).get("displayName"))
                values = athlete.get("stats") or []
                if not name or not values:
                    continue

                stat_map = {}
                for idx, label in enumerate(labels):
                    if idx < len(values):
                        stat_map[clean(label)] = clean(values[idx])

                preferred = ["PTS", "REB", "AST", "STL", "BLK", "FG", "3PT", "FT", "R", "H", "RBI", "HR", "SO", "IP", "BB"]
                parts = []
                for key in preferred:
                    if key in stat_map and stat_map[key] not in ["", "0", "0-0", ".000"]:
                        parts.append(f"{key} {stat_map[key]}")

                if not parts:
                    for key, value in stat_map.items():
                        if value and value not in ["0", "0-0", ".000"]:
                            parts.append(f"{key} {value}")
                        if len(parts) >= 4:
                            break

                if parts:
                    candidates.append({
                        "player_name": name,
                        "team": team,
                        "statline": ", ".join(parts[:5]),
                        "score": str(performer_score(stat_map)),
                        "source": source_label,
                    })

    candidates.sort(key=lambda x: safe_int(x.get("score"), 0), reverse=True)

    final = []
    seen = set()
    for candidate in candidates:
        identity = (candidate["player_name"], candidate["team"])
        if identity in seen:
            continue
        seen.add(identity)
        final.append(candidate)
        if len(final) >= 8:
            break
    return final


def confidence_for_game(status: str, summary_present: bool, performer_count: int) -> str:
    if status != "final":
        return "Medium"
    if summary_present and performer_count >= 2:
        return "High"
    if summary_present or performer_count >= 1:
        return "Medium"
    return "Low"


def manual_review_flag(confidence: str, status: str) -> str:
    if status != "final":
        return "Yes"
    return "No" if confidence == "High" else "Yes"


@dataclass
class GameRow:
    sport_group: str
    league_label: str
    event_id: str
    game_date_utc: str
    scoreboard_date: str
    status_detail: str
    status_bucket: str
    game_state: str
    source: str
    source_type: str
    confidence: str
    manual_review_flag: str
    matchup: str
    away_team: str
    away_abbrev: str
    away_score: str
    away_record: str
    away_logo: str
    home_team: str
    home_abbrev: str
    home_score: str
    home_record: str
    home_logo: str
    winner: str
    loser: str
    final_score: str
    period_summary: str
    venue: str
    headline: str
    primary_storyline: str
    top_performer_1: str
    top_performer_1_statline: str
    top_performer_2: str
    top_performer_2_statline: str
    result_graphic_ready: str
    source_url: str


def build_game_row(source: Dict[str, str], event: Dict[str, Any], summary: Optional[Dict[str, Any]], scoreboard_date: str) -> Tuple[GameRow, List[Dict[str, str]]]:
    competitors = get_competitors(event)
    home, away = split_home_away(competitors)
    home_name = team_name(home)
    away_name = team_name(away)
    home_score = clean(home.get("score"))
    away_score = clean(away.get("score"))
    winner, loser = detect_winner(home, away)

    event_id = clean(event.get("id"))
    status_detail = clean(((event.get("status") or {}).get("type") or {}).get("detail"))
    status_name = clean(((event.get("status") or {}).get("type") or {}).get("name"))
    bucket = status_bucket(status_name or status_detail)
    game_state = "Final" if bucket == "final" and "final" in status_detail.lower() else ("Live" if bucket == "live" else "Upcoming")
    venue = clean((((event.get("competitions") or [{}])[0].get("venue") or {}).get("fullName")))
    source_url = f"https://www.espn.com/{source['sport']}/game/_/gameId/{event_id}"
    period_summary = summarize_periods(event)

    top_performers = extract_top_performers_from_summary(summary or {}, source["label"]) if summary else []
    tp1_name = top_performers[0]["player_name"] if len(top_performers) > 0 else ""
    tp1_line = top_performers[0]["statline"] if len(top_performers) > 0 else ""
    tp2_name = top_performers[1]["player_name"] if len(top_performers) > 1 else ""
    tp2_line = top_performers[1]["statline"] if len(top_performers) > 1 else ""

    if bucket == "final" and winner and loser:
        headline = f"{winner} defeat {loser}"
        final_score = f"{away_name} {away_score} - {home_name} {home_score}"
    else:
        headline = f"{away_name} vs. {home_name}"
        final_score = f"{away_name} {away_score} - {home_name} {home_score}"

    storyline = "Final result verified from structured scoreboard data."
    if bucket == "live":
        storyline = "Game is live. Do not create a final result graphic yet."
    elif bucket == "upcoming":
        storyline = "Game has not started yet. Use only for watch or schedule coverage."
    elif tp1_name and tp1_line:
        storyline = f"{tp1_name} led the way with {tp1_line}."

    confidence = confidence_for_game(bucket, summary is not None, len(top_performers))
    review = manual_review_flag(confidence, bucket)
    graphic_ready = "Yes" if bucket == "final" and winner and loser and away_score and home_score else "No"

    row = GameRow(
        sport_group=source["sport_group"],
        league_label=source["label"],
        event_id=event_id,
        game_date_utc=clean(event.get("date")),
        scoreboard_date=scoreboard_date,
        status_detail=status_detail,
        status_bucket=bucket,
        game_state=game_state,
        source="ESPN public scoreboard/summary",
        source_type="structured scoreboard",
        confidence=confidence,
        manual_review_flag=review,
        matchup=f"{away_name} at {home_name}",
        away_team=away_name,
        away_abbrev=team_abbrev(away),
        away_score=away_score,
        away_record=team_record_from_competitor(away),
        away_logo=team_logo(away),
        home_team=home_name,
        home_abbrev=team_abbrev(home),
        home_score=home_score,
        home_record=team_record_from_competitor(home),
        home_logo=team_logo(home),
        winner=winner,
        loser=loser,
        final_score=final_score,
        period_summary=period_summary,
        venue=venue,
        headline=headline,
        primary_storyline=storyline,
        top_performer_1=tp1_name,
        top_performer_1_statline=tp1_line,
        top_performer_2=tp2_name,
        top_performer_2_statline=tp2_line,
        result_graphic_ready=graphic_ready,
        source_url=source_url,
    )
    return row, top_performers


def build_graphics_queue(game_rows: List[GameRow]) -> str:
    finals = [g for g in game_rows if g.result_graphic_ready == "Yes"]
    lines = [
        "# Her Sports Daily Results Graphics Queue",
        "",
        f"Generated: {iso_now()}",
        "",
        "Use these packets for accurate results and box-score-based postgame graphics.",
        "Only final games with structured score data are included below.",
        "",
    ]

    if not finals:
        lines.append("No final result graphics are ready right now.")
        return "\n".join(lines)

    for idx, g in enumerate(finals, start=1):
        decision = "Must Post" if g.league_label == "WNBA" else "Maybe Post"
        lines.extend([
            f"## RESULT GRAPHIC {idx}: {g.headline}",
            "",
            f"**League:** {g.league_label}",
            f"**Action:** Make if fresh and relevant",
            f"**Decision:** {decision}",
            f"**Template:** Postgame Result Card",
            f"**Timing:** Within 1 to 2 hours of final if still fresh",
            f"**Source type:** {g.source_type}",
            f"**Confidence:** {g.confidence}",
            f"**Manual review flag:** {g.manual_review_flag}",
            "",
            "### Verified result context",
            f"- Matchup: {g.matchup}",
            f"- Winner: {g.winner}",
            f"- Loser: {g.loser}",
            f"- Final score: {g.final_score}",
            f"- Game status: {g.status_detail}",
            f"- Venue: {g.venue}",
            f"- Top performer 1: {g.top_performer_1} | {g.top_performer_1_statline}",
            f"- Top performer 2: {g.top_performer_2} | {g.top_performer_2_statline}",
            f"- Period/inning summary: {g.period_summary}",
            f"- Source URL: {g.source_url}",
            "",
            "### Production accuracy rules",
            "- Do not change the final score.",
            "- Do not invent additional player stat lines.",
            "- If a top performer field is blank, do not fill it from memory.",
            "- Use one consistent Her Sports Daily watermark/logo bug in the top-left safe area.",
            "",
            "### Design direction",
            "Use the established Her Sports Daily editorial sports style, brand colors, font hierarchy, and top-left watermark treatment.",
            "",
            "### Slide copy",
            f"**Slide 1 - Hook:** {g.winner} beat {g.loser}",
            f"Final: {g.final_score}.",
            "",
            "**Slide 2 - Top performer:** Who led the way",
            (f"{g.top_performer_1} starred with {g.top_performer_1_statline}." if g.top_performer_1 else "Use only verified performer info from the result table."),
            "",
            "**Slide 3 - Secondary angle:** What stood out",
            g.primary_storyline,
            "",
            "**Slide 4 - CTA:** Your take?",
            "Follow Her Sports Daily for more verified results and box scores.",
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


def write_csv(path: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    game_rows: List[GameRow] = []
    performer_rows: List[Dict[str, str]] = []

    seen_events = set()
    date_window = scoreboard_dates()

    for source in SOURCES:
        for date_string in date_window:
            try:
                scoreboard = get_scoreboard(source, date_string)
            except Exception as exc:
                print(f"Failed scoreboard fetch for {source['label']} on {date_string}: {exc}")
                continue

            for event in scoreboard.get("events") or []:
                event_id = clean(event.get("id"))
                event_key = (source["label"], event_id)
                if not event_id or event_key in seen_events:
                    continue
                seen_events.add(event_key)

                summary = None
                try:
                    summary = get_summary(source, event_id)
                    time.sleep(0.15)
                except Exception:
                    summary = None

                game_row, performers = build_game_row(source, event, summary, date_string)
                game_rows.append(game_row)

                for rank, performer in enumerate(performers[:5], start=1):
                    performer_rows.append({
                        "event_id": game_row.event_id,
                        "league_label": game_row.league_label,
                        "matchup": game_row.matchup,
                        "game_state": game_row.game_state,
                        "winner": game_row.winner,
                        "final_score": game_row.final_score,
                        "performer_rank": str(rank),
                        "player_name": performer["player_name"],
                        "team": performer["team"],
                        "statline": performer["statline"],
                        "source": performer["source"],
                    })

    game_rows.sort(
        key=lambda g: (
            {"Yes": 0, "No": 1}.get(g.result_graphic_ready, 1),
            {"WNBA": 0, "NCAA Women's Basketball": 1, "NCAA Softball": 2}.get(g.league_label, 9),
            g.game_date_utc,
        )
    )

    game_dicts = [asdict(g) for g in game_rows]

    box_rows = []
    for g in game_rows:
        box_rows.append({
            "event_id": g.event_id,
            "league_label": g.league_label,
            "matchup": g.matchup,
            "game_state": g.game_state,
            "winner": g.winner,
            "loser": g.loser,
            "final_score": g.final_score,
            "top_performer_1": g.top_performer_1,
            "top_performer_1_statline": g.top_performer_1_statline,
            "top_performer_2": g.top_performer_2,
            "top_performer_2_statline": g.top_performer_2_statline,
            "period_summary": g.period_summary,
            "confidence": g.confidence,
            "manual_review_flag": g.manual_review_flag,
            "source_url": g.source_url,
        })

    top_performers = sorted(
        performer_rows,
        key=lambda x: (x["game_state"] != "Final", x["league_label"], x["performer_rank"])
    )

    write_csv(RESULTS_BOARD_FILE, game_dicts, list(GameRow.__annotations__.keys()))
    write_csv(
        BOX_SCORES_FILE,
        box_rows,
        [
            "event_id", "league_label", "matchup", "game_state", "winner", "loser", "final_score",
            "top_performer_1", "top_performer_1_statline", "top_performer_2", "top_performer_2_statline",
            "period_summary", "confidence", "manual_review_flag", "source_url",
        ],
    )
    write_csv(
        TOP_PERFORMERS_FILE,
        top_performers,
        [
            "event_id", "league_label", "matchup", "game_state", "winner", "final_score",
            "performer_rank", "player_name", "team", "statline", "source",
        ],
    )

    Path(GRAPHICS_QUEUE_FILE).write_text(build_graphics_queue(game_rows), encoding="utf-8")

    seed_rows = []
    for g in game_rows:
        seed_rows.append({
            "league_label": g.league_label,
            "scoreboard_date": g.scoreboard_date,
            "matchup": g.matchup,
            "game_state": g.game_state,
            "winner": g.winner,
            "loser": g.loser,
            "final_score": g.final_score,
            "headline": g.headline,
            "top_performer_1": g.top_performer_1,
            "top_performer_1_statline": g.top_performer_1_statline,
            "top_performer_2": g.top_performer_2,
            "top_performer_2_statline": g.top_performer_2_statline,
            "confidence": g.confidence,
            "result_graphic_ready": g.result_graphic_ready,
            "source_url": g.source_url,
        })
    write_csv(
        DASHBOARD_SEED_FILE,
        seed_rows,
        [
            "league_label", "scoreboard_date", "matchup", "game_state", "winner", "loser", "final_score", "headline",
            "top_performer_1", "top_performer_1_statline", "top_performer_2", "top_performer_2_statline",
            "confidence", "result_graphic_ready", "source_url",
        ],
    )

    final_count = sum(1 for g in game_rows if g.game_state == "Final")
    ready_count = sum(1 for g in game_rows if g.result_graphic_ready == "Yes")

    hub = f"""# Her Sports Daily Results Desk Hub

Generated: {iso_now()}

## What this system does
- Pulls structured women's sports results from scoreboard-style endpoints.
- Separates results and box scores from the broader news pipeline.
- Produces result-ready postgame graphic packets only for final games.

## Phase 1 coverage
- WNBA
- NCAA Women's Basketball
- NCAA Softball

## Output files
- `today_results_board.csv`
- `today_box_scores.csv`
- `top_performers.csv`
- `results_graphics_queue.md`
- `results_dashboard_seed.csv`

## Current run snapshot
- Date window queried: {", ".join(scoreboard_dates())}
- Games found: {len(game_rows)}
- Final games: {final_count}
- Result graphics ready: {ready_count}

## Accuracy rules
- Never infer a final score.
- Never invent a top performer stat line.
- If a game is not final, do not create a postgame result graphic.
- If confidence is not High, keep manual review enabled.
"""
    Path(HUB_FILE).write_text(hub, encoding="utf-8")

    print(f"Created {RESULTS_BOARD_FILE}")
    print(f"Created {BOX_SCORES_FILE}")
    print(f"Created {TOP_PERFORMERS_FILE}")
    print(f"Created {GRAPHICS_QUEUE_FILE}")
    print(f"Created {DASHBOARD_SEED_FILE}")
    print(f"Created {HUB_FILE}")


if __name__ == "__main__":
    main()
