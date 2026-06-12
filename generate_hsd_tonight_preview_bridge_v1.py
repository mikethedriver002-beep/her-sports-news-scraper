from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

VERSION = "hsd-tonight-preview-bridge-v3.2.9-bebe-ops-v2.8"

LOCAL_TZ = os.environ.get("HSD_LOCAL_TIMEZONE", "America/New_York")
INCLUDE_NEXT_DAY = os.environ.get("HSD_PREVIEW_ALLOW_NEXT_DAY", "0").strip().lower() in {"1", "true", "yes"}
REQUIRE_COMPLETE = os.environ.get("HSD_PREVIEW_REQUIRE_COMPLETE_SLATE", "1").strip().lower() not in {"0", "false", "no"}
FORCE_REBUILD = os.environ.get("HSD_FORCE_PREVIEW_REBUILD", "1").strip().lower() in {"1", "true", "yes"}
FOCUS_MAP_PATH = Path(os.environ.get("HSD_PREVIEW_FOCUS_MAP", "config/preview_focus_map.json"))

BUNDLE_FIELDS = [
    "bundle_rank", "bundle_id", "bundle_name", "bundle_type", "production_priority", "asset_type", "asset_shape", "slide_count",
    "content_family", "sports_mix", "source_items_count", "source_headlines", "caption_seed", "bundle_prompt", "accuracy_lock",
    "watermark_rule", "source_packet_ids_json", "event_date", "event_datetime", "result_date", "freshness_label", "freshness_source",
    "source_run_timestamp", "event_age_hours", "freshness_status", "freshness_decision", "source_event_dates_json"
]
GRAPHICS_FIELDS = [
    "post_rank", "post_slug", "post_title", "content_family", "asset_type", "asset_shape", "priority",
    "source_headline", "caption_seed", "event_date", "event_datetime", "freshness_status"
]
FOCUS_FIELDS = ["bundle_slug", "bundle_name", "team_name", "player_name", "priority", "status", "notes"]

TEAM_ALIASES = {
    "LA Sparks": "Los Angeles Sparks",
    "Los Angeles": "Los Angeles Sparks",
    "Los Angeles Spark": "Los Angeles Sparks",
    "Seattle": "Seattle Storm",
    "Connecticut": "Connecticut Sun",
    "New York": "New York Liberty",
    "Las Vegas": "Las Vegas Aces",
    "Phoenix": "Phoenix Mercury",
    "Indiana": "Indiana Fever",
    "Chicago": "Chicago Sky",
    "Atlanta": "Atlanta Dream",
    "Dallas": "Dallas Wings",
    "Dallas Wing": "Dallas Wings",
    "Minnesota": "Minnesota Lynx",
    "Washington": "Washington Mystics",
    "Washington Mystic": "Washington Mystics",
    "Golden State": "Golden State Valkyries",
    "Golden State Valkyrie": "Golden State Valkyries",
    "Toronto": "Toronto Tempo",
    "Portland": "Portland Fire",
}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-") or "bundle"


def sid(*parts: Any) -> str:
    return "bundle_" + hashlib.sha1("|".join(clean(p) for p in parts).encode()).hexdigest()[:14]


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def parse_dt(s: str) -> Optional[datetime]:
    s = clean(s).replace("Z", "+00:00")
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, 0, tzinfo=timezone.utc)
    return None


def local_zone():
    if ZoneInfo is None:
        return timezone.utc
    try:
        return ZoneInfo(LOCAL_TZ)
    except Exception:
        return timezone.utc


def target_date_local() -> str:
    raw = clean(os.environ.get("HSD_TARGET_DATE_LOCAL", ""))
    if raw:
        return raw
    return datetime.now(local_zone()).date().isoformat()


def normalize_team(name: str) -> str:
    name = clean(name).strip(" .,|")
    return TEAM_ALIASES.get(name, name)


def row_team(row: Dict[str, str], which: str) -> str:
    if which == "away":
        keys = ["away_team_display", "away_team_norm", "away_team", "team_away", "visitor_team"]
    else:
        keys = ["home_team_display", "home_team_norm", "home_team", "team_home", "host_team"]
    for key in keys:
        if clean(row.get(key)):
            return normalize_team(row.get(key, ""))

    text = clean(row.get("matchup") or row.get("graphics_headline") or row.get("headline") or row.get("canonical_key") or row.get("title"))
    for sep in [" at ", " vs. ", " vs ", " versus "]:
        if sep in text:
            a, h = text.split(sep, 1)
            return normalize_team(a if which == "away" else h)

    # Score display fallback: "Team A 0 - Team B 0".
    score_text = clean(row.get("score_display") or row.get("summary"))
    m = re.search(r"([A-Z][A-Za-z .'-]+?)\s+\d{1,3}\s*[-–]\s*([A-Z][A-Za-z .'-]+?)\s+\d{1,3}", score_text)
    if m:
        return normalize_team(m.group(1) if which == "away" else m.group(2))
    return ""


def row_league(row: Dict[str, str]) -> str:
    for key in ["league_norm", "league", "competition", "sport_league"]:
        if clean(row.get(key)):
            return clean(row.get(key))
    return ""


def row_state(row: Dict[str, str]) -> str:
    return clean(row.get("status_norm") or row.get("game_state") or row.get("status") or row.get("state"))


def row_kind(row: Dict[str, str]) -> str:
    return clean(row.get("row_kind") or row.get("content_type") or row.get("asset_type")).lower()


def row_event_dt(row: Dict[str, str]) -> Optional[datetime]:
    for key in ["scheduled_start_utc", "event_datetime", "scheduled_datetime_local", "start_time_utc", "game_datetime_utc"]:
        dt = parse_dt(row.get(key, ""))
        if dt:
            return dt
    # Parse common ESPN-style status strings such as "thu, june 11th at 9:00 pm edt".
    state = row_state(row)
    m = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)\b", state, flags=re.I)
    local_date = clean(row.get("scheduled_date_local") or row.get("event_date_local") or row.get("event_date") or row.get("game_date_local") or row.get("date_local"))
    if m and re.match(r"^20\d{2}-\d{2}-\d{2}$", local_date):
        hh = int(m.group(1))
        mm = int(m.group(2))
        ap = m.group(3).lower()
        if ap == "pm" and hh != 12:
            hh += 12
        if ap == "am" and hh == 12:
            hh = 0
        y, mo, d = [int(x) for x in local_date.split("-")]
        try:
            return datetime(y, mo, d, hh, mm, tzinfo=local_zone()).astimezone(timezone.utc)
        except Exception:
            pass
    return parse_dt(row.get("scheduled_date_local", "") or row.get("event_date", "") or row.get("event_date_local", ""))


def row_local_date(row: Dict[str, str]) -> str:
    for key in ["scheduled_date_local", "event_date_local", "event_date", "game_date_local", "date_local"]:
        val = clean(row.get(key))
        if re.match(r"^20\d{2}-\d{2}-\d{2}$", val):
            return val
    dt = row_event_dt(row)
    if not dt:
        return ""
    return dt.astimezone(local_zone()).date().isoformat()


def matchup(row: Dict[str, str]) -> str:
    away = row_team(row, "away")
    home = row_team(row, "home")
    if away and home:
        return f"{away} at {home}"
    for key in ["graphics_headline", "headline", "canonical_key", "matchup", "title"]:
        if clean(row.get(key)):
            return clean(row.get(key))
    return "Unknown Matchup"


def matchup_key(row: Dict[str, str]) -> str:
    m = matchup(row).lower()
    m = m.replace(" vs. ", " at ").replace(" vs ", " at ").replace(" versus ", " at ")
    m = re.sub(r"\s+", " ", m).strip()
    return m


def is_live_or_final(row: Dict[str, str]) -> bool:
    state = row_state(row).lower()
    if row_kind(row) == "result":
        return True
    if any(x in state for x in ["final", "completed", "live", "in progress", "halftime", "end of", "postponed", "cancelled"]):
        return True
    if clean(row.get("winner_team_name") or row.get("winner") or row.get("loser_team_name") or row.get("loser")):
        return True
    score = clean(row.get("score_display") or row.get("summary"))
    # A 0-0 schedule row is not live, but a nonzero score is.
    m = re.search(r"\b(\d{1,3})\s*[-–]\s*(\d{1,3})\b", score)
    if m and {m.group(1), m.group(2)} != {"0"}:
        return True
    return False


def is_upcoming_preview(row: Dict[str, str]) -> bool:
    if is_live_or_final(row):
        return False
    state = row_state(row).lower()
    if any(x in state for x in ["postponed", "cancelled"]):
        return False
    return True


def time_label(row: Dict[str, str]) -> str:
    state = row_state(row)
    m = re.search(r"\b\d{1,2}:\d{2}\s*(AM|PM|am|pm)\b(?:\s*[A-Z]{2,4})?", state)
    if m:
        return state
    dt = row_event_dt(row)
    if not dt:
        return "Time TBA"
    dt = dt.astimezone(local_zone())
    try:
        return dt.strftime("%-I:%M %p ET")
    except Exception:
        return dt.strftime("%I:%M %p ET").lstrip("0")


def load_focus_map() -> Dict[str, List[str]]:
    if not FOCUS_MAP_PATH.exists():
        return {}
    try:
        raw = json.loads(FOCUS_MAP_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    source = raw.get("WNBA", raw) if isinstance(raw, dict) else {}
    out: Dict[str, List[str]] = {}
    for team, players in source.items():
        if isinstance(players, list):
            out[normalize_team(team)] = [clean(x) for x in players if clean(x)]
    return out


def collect_candidate_rows() -> List[Dict[str, str]]:
    files = [
        "daily_slate_plan.csv",
        "results_contract_v2.csv",
        "reconciled_events.csv",
        "today_womens_results.csv",
        "top_womens_results.csv",
        "today_results_board.csv",
        "today_box_scores.csv",
    ]
    rows = []
    for fname in files:
        for row in read_csv(fname):
            row = dict(row)
            row["_source_file"] = fname
            rows.append(row)
    return rows


def choose_better(existing: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    def score(r: Dict[str, str]) -> int:
        s = 0
        if row_event_dt(r):
            s += 4
        if row_state(r):
            s += 2
        if row_kind(r) == "preview":
            s += 1
        if r.get("_source_file") == "results_contract_v2.csv":
            s += 1
        return s
    return new if score(new) > score(existing) else existing


def build_schedule_rows(rows: List[Dict[str, str]], tgt_date: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    full_same_day: Dict[str, Dict[str, str]] = {}
    included: Dict[str, Dict[str, str]] = {}

    for row in rows:
        if "WNBA" not in row_league(row).upper():
            continue
        local_date = row_local_date(row)
        if not local_date:
            continue
        key = f"{local_date}|{matchup_key(row)}"
        if local_date == tgt_date:
            if key in full_same_day:
                full_same_day[key] = choose_better(full_same_day[key], row)
            else:
                full_same_day[key] = row
            if is_upcoming_preview(row):
                if key in included:
                    included[key] = choose_better(included[key], row)
                else:
                    included[key] = row
        elif INCLUDE_NEXT_DAY:
            next_day = (datetime.fromisoformat(tgt_date).date() + timedelta(days=1)).isoformat()
            if local_date == next_day and is_upcoming_preview(row):
                if key in included:
                    included[key] = choose_better(included[key], row)
                else:
                    included[key] = row

    full = sorted(full_same_day.values(), key=lambda r: row_event_dt(r) or datetime.max.replace(tzinfo=timezone.utc))
    inc = sorted(included.values(), key=lambda r: row_event_dt(r) or datetime.max.replace(tzinfo=timezone.utc))
    started = [r for r in full if matchup_key(r) not in {matchup_key(x) for x in inc}]
    return inc, full, started


def number_word(n: int) -> str:
    return {0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}.get(n, str(n))


def main() -> None:
    tgt = target_date_local()
    existing = read_csv("studio_bundle_queue.csv")
    if existing and not FORCE_REBUILD:
        has_preview = any(clean(r.get("bundle_name") or r.get("content_family")).lower().startswith("tonight in the w") for r in existing)
        if has_preview:
            Path("studio_preview_build_v2_report.md").write_text(
                f"# HSD Tonight Preview Bridge v2.8\n\nExisting preview bundle already present for {tgt}. No rebuild performed.\n",
                encoding="utf-8",
            )
            print("Existing Tonight in the W preview bundle detected. Skipping rebuild.")
            return

    schedule, full_same_day, started_or_excluded = build_schedule_rows(collect_candidate_rows(), tgt)
    candidate_dates = sorted({row_local_date(r) for r in schedule})
    mixed_dates = len(candidate_dates) > 1
    full_count = len(full_same_day)
    included_count = len(schedule)
    preview_scope = "full_slate" if included_count == full_count else "remaining_slate" if included_count and full_count > included_count else "unknown"
    scope_headline = "Tonight in the W" if preview_scope == "full_slate" else "Still to Come in the W"
    scope_line = f"{number_word(included_count)} games. One night." if preview_scope == "full_slate" else f"{number_word(included_count)} games still to go."

    completeness_ok = True
    missing: List[str] = []
    if REQUIRE_COMPLETE and preview_scope == "full_slate":
        shown = {matchup_key(r) for r in schedule}
        missing = [matchup(r) for r in full_same_day if matchup_key(r) not in shown]
        completeness_ok = not missing

    schedule_lines = [f"{matchup(r)} - {time_label(r)}" for r in schedule]
    all_lines = [f"{matchup(r)} - {time_label(r)}" for r in full_same_day]
    started_lines = [f"{matchup(r)} - {time_label(r)}" for r in started_or_excluded]

    report = [
        "# HSD Tonight Preview Bridge v3.2.9 BeBe Ops v2.8",
        "",
        f"Target local date: {tgt}",
        f"Full target-date WNBA games found: {full_count}",
        f"Preview games included: {included_count}",
        f"Preview scope: {preview_scope}",
        f"Started/excluded same-day games: {len(started_or_excluded)}",
        f"Mixed dates detected: {'YES' if mixed_dates else 'NO'}",
        f"Completeness check: {'PASS' if completeness_ok else 'FAIL'}",
        "",
        "## Included games",
        *(f"- {line}" for line in schedule_lines),
    ]
    if started_lines:
        report += ["", "## Same-day games not included in preview because they appear started/live/final", *(f"- {line}" for line in started_lines)]
    if missing:
        report += ["", "## Missing games", *(f"- {m}" for m in missing)]
    Path("studio_preview_build_v2_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    Path("studio_preview_build_v2.json").write_text(json.dumps({
        "version": VERSION,
        "target_date_local": tgt,
        "full_target_date_count": full_count,
        "source_same_day_count": full_count,
        "included_count": included_count,
        "started_or_excluded_count": len(started_or_excluded),
        "preview_scope": preview_scope,
        "display_headline": scope_headline,
        "display_kicker": scope_line,
        "mixed_dates": mixed_dates,
        "completeness_ok": completeness_ok,
        "missing_games": missing,
        "games": [{"matchup": matchup(r), "event_date": row_local_date(r), "time_label": time_label(r)} for r in schedule],
        "all_target_date_games": [{"matchup": matchup(r), "event_date": row_local_date(r), "time_label": time_label(r), "state": row_state(r)} for r in full_same_day],
        "started_or_excluded_games": [{"matchup": matchup(r), "event_date": row_local_date(r), "time_label": time_label(r), "state": row_state(r)} for r in started_or_excluded],
    }, indent=2), encoding="utf-8")

    if not schedule:
        print("No WNBA preview games found for target date.")
        return
    if mixed_dates or not completeness_ok:
        print("Preview build blocked by mixed-date or completeness gate.")
        return

    focus_map = load_focus_map()
    focus_rows = []
    seen_focus = set()
    for row in schedule:
        for team in [row_team(row, "away"), row_team(row, "home")]:
            for priority, player in enumerate(focus_map.get(team, [])[:2], start=1):
                key = (team, player)
                if key in seen_focus:
                    continue
                seen_focus.add(key)
                focus_rows.append({
                    "bundle_slug": "tonight-in-the-w",
                    "bundle_name": scope_headline,
                    "team_name": team,
                    "player_name": player,
                    "priority": str(priority),
                    "status": "requested_preview_focus",
                    "notes": f"Auto focus for {team}",
                })
    write_csv("preview_player_focus.csv", focus_rows, FOCUS_FIELDS)

    first_dt = row_event_dt(schedule[0]) or datetime.now(timezone.utc)
    source_headlines = " | ".join(matchup(r) for r in schedule)
    caption_seed = scope_headline + ": " + " | ".join(schedule_lines)
    focus_text = "; ".join([f"{r['team_name']}: {r['player_name']}" for r in focus_rows]) or "Use approved player images if available for featured teams."

    slate_phrase = "the full target-date slate" if preview_scope == "full_slate" else "the remaining target-date slate only"
    prompt = (
        f"Create a premium Her Sports Daily 4-slide 1080x1350 carousel named {scope_headline}. "
        f"Use ONLY games scheduled for {tgt} that are listed in this prompt. Do not include tomorrow or any other date. "
        f"This is {slate_phrase}: exactly {included_count} game(s) are included and all must be represented. "
        "This must feel like premium women’s sports media, not a flat schedule board. Use bold editorial hierarchy, strong contrast, clean spacing, human energy, and modern social-first composition. Make the cover feel like an event, not a scoreboard. "
        "Use attached exact player/person images for featured matchups only when attached and exactly mapped to that player/team. If a safe player image is not attached, stay team-forward with exact attached logos and strong type. "
        f"Suggested player focus: {focus_text}. "
        "No game scores or postgame outcomes. No invented stats. No injuries, records, rankings, or quotes unless explicitly included. "
        f"Slide 1: premium cover with the {scope_headline} editorial hook. "
        "Slide 2: slate board with matchup cards and time/team hierarchy. "
        "Slide 3: player-watch or featured-matchup energy only if exact attached player images exist. "
        "Slide 4: CTA asking which matchup people are watching. "
        "Do not render workflow labels, QA labels, postgame labels, or internal production language. "
        "One HSD watermark only, top-left safe zone. "
        "Public-facing slate line: " + scope_line + " "
        "Games: " + " | ".join(schedule_lines)
    )

    bundle = {
        "bundle_rank": "1",
        "bundle_id": sid(VERSION, tgt, source_headlines, preview_scope),
        "bundle_name": scope_headline,
        "bundle_type": "wnba_preview_premium" if preview_scope == "full_slate" else "wnba_remaining_preview_premium",
        "production_priority": "POST FIRST",
        "asset_type": "4-slide carousel",
        "asset_shape": "1080x1350",
        "slide_count": "4",
        "content_family": "Tonight in the W",
        "sports_mix": "basketball",
        "source_items_count": str(included_count),
        "source_headlines": source_headlines,
        "caption_seed": caption_seed,
        "bundle_prompt": prompt,
        "accuracy_lock": f"Use only the listed {tgt} WNBA preview games. Represent all {included_count} listed game(s). Do not invent game scores, injuries, stats, or extra games. Do not mix dates.",
        "watermark_rule": "Use one compact HSD watermark/logo bug in the top-left safe zone.",
        "source_packet_ids_json": json.dumps([clean(r.get("event_uid") or matchup(r)) for r in schedule]),
        "event_date": tgt,
        "event_datetime": first_dt.isoformat(),
        "result_date": "",
        "freshness_label": "upcoming_schedule_same_day" if preview_scope == "full_slate" else "remaining_schedule_same_day",
        "freshness_source": "tonight_preview_bridge_v3.2.9",
        "source_run_timestamp": datetime.now(timezone.utc).isoformat(),
        "event_age_hours": "0.0",
        "freshness_status": "fresh_upcoming_schedule",
        "freshness_decision": "allow",
        "source_event_dates_json": json.dumps(sorted({row_local_date(r) for r in schedule})),
    }

    remaining = [r for r in existing if clean(r.get("content_family") or r.get("bundle_name")).lower() != "tonight in the w"]
    write_csv("studio_bundle_queue.csv", remaining + [bundle], BUNDLE_FIELDS)
    write_csv("studio_graphics_queue.csv", [{
        "post_rank": "1",
        "post_slug": "tonight-in-the-w",
        "post_title": scope_headline,
        "content_family": "Tonight in the W",
        "asset_type": "4-slide carousel",
        "asset_shape": "1080x1350",
        "priority": "POST FIRST",
        "source_headline": source_headlines,
        "caption_seed": caption_seed,
        "event_date": tgt,
        "event_datetime": first_dt.isoformat(),
        "freshness_status": "fresh_upcoming_schedule",
    }], GRAPHICS_FIELDS)

    player_focus_md = "\n".join(f"- {r['team_name']}: {r['player_name']}" for r in focus_rows) or "- Use approved player images if available."
    Path("studio_bundle_packets.md").write_text(
        f"""# HSD Studio Bundle Packets

## BUNDLE 1: {scope_headline}

Target date: {tgt}
Preview scope: {preview_scope}
Public slate line: {scope_line}

Source items: {source_headlines}

### Games
{chr(10).join(schedule_lines)}

### Caption seed
{caption_seed}

### Accuracy lock
{bundle['accuracy_lock']}

### Player focus
{player_focus_md}
""",
        encoding="utf-8",
    )
    Path("studio_bundle_prompts.md").write_text(
        f"""# HSD Studio Bundle Prompts

## {scope_headline}

```text
{prompt}
```
""",
        encoding="utf-8",
    )
    print(f"Created {scope_headline} bundle for {tgt} with {included_count} game(s); scope={preview_scope}.")


if __name__ == "__main__":
    main()
