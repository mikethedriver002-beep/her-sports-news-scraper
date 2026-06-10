from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "hsd-results-contract-v2.2"

OUT_TOP = "top_womens_results.csv"
OUT_WOMENS = "today_womens_results.csv"
OUT_FINALS = "today_final_results.csv"
OUT_RECON = "reconciled_events.csv"
OUT_GATE = "results_freshness_gate.csv"
OUT_REPORT = "results_freshness_report.md"
OUT_MANIFEST = "results_freshness_manifest.json"
OUT_CONTRACT = "results_contract_report.md"

RESULT_FIELDS = [
    "graphics_headline","caption_seed","matchup","winner","loser","final_score_display",
    "sport_norm","league_norm","gender_scope","status_norm","manual_review","editorial_bucket",
    "content_action","posting_priority","confidence","editorial_rank","scheduled_date_local",
    "source_url","selected_source","all_sources_json","outcome_type","event_date","event_datetime"
]
GATE_FIELDS = ["source_file","headline","event_date","event_age_hours","status","date_source","row_type"]

SOURCE_FILES = [
    "top_womens_results.csv",
    "today_womens_results.csv",
    "today_final_results.csv",
    "reconciled_events.csv",
    "today_results_board.csv",
    "results_dashboard_seed.csv",
]

def now() -> datetime:
    return datetime.now(timezone.utc)

def iso_now() -> str:
    return now().isoformat()

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()



def local_eastern_to_utc(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    """Approximate US Eastern local time to UTC for schedule strings like 7:00 PM EDT.

    GitHub runners do not always have zoneinfo data issues, so this helper keeps
    the contract deterministic. March-November is treated as EDT (UTC-4), other
    months as EST (UTC-5). This is sufficient for sports slate freshness gating.
    """
    offset_hours = 4 if 3 <= month <= 11 else 5
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc) + timedelta(hours=offset_hours)


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
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
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def parse_dt(value: Any) -> Optional[datetime]:
    s = clean(value).replace("Z", "+00:00")
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?\b", s)
    if m:
        hh = int(m.group(4) or 12)
        mm = int(m.group(5) or 0)
        ss = int(m.group(6) or 0)
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), hh, mm, ss, tzinfo=timezone.utc)
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})(?:[ T](\d{1,2}):(\d{2}))?\b", s)
    if m:
        hh = int(m.group(4) or 12)
        mm = int(m.group(5) or 0)
        return datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)), hh, mm, tzinfo=timezone.utc)
    m = re.search(r"\b(jan|feb|mar|apr|may|jun|june|jul|july|aug|sep|sept|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+at\s+(\d{1,2}):(\d{2})\s*(am|pm))?(?:\s*(edt|est))?", s, re.I)
    if m:
        month_names = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"sep":9,"sept":9,"oct":10,"nov":11,"dec":12}
        y = now().year
        mo = month_names[m.group(1).lower()]
        d = int(m.group(2))
        hh = int(m.group(3) or 12)
        mi = int(m.group(4) or 0)
        ap = (m.group(5) or "").lower()
        tz = (m.group(6) or "").lower()
        if ap == "pm" and hh != 12: hh += 12
        if ap == "am" and hh == 12: hh = 0
        if tz in {"edt", "est"} or ap:
            return local_eastern_to_utc(y, mo, d, hh, mi)
        return datetime(y, mo, d, hh, mi, tzinfo=timezone.utc)
    return None

def first(row: Dict[str,str], keys: List[str]) -> str:
    for k in keys:
        if clean(row.get(k)):
            return clean(row.get(k))
    return ""

def normalize_row(row: Dict[str, str], source_file: str) -> Dict[str, str]:
    matchup = first(row, ["matchup","event_name","game","fixture","title","graphics_headline","headline"])
    home = first(row, ["home_team","home","team_home"])
    away = first(row, ["away_team","away","team_away"])
    if not matchup and home and away:
        matchup = f"{away} at {home}"
    winner = first(row, ["winner","winning_team"])
    loser = first(row, ["loser","losing_team"])
    score = first(row, ["final_score_display","score","final_score","result"])
    headline = first(row, ["graphics_headline","headline","title"])
    status = first(row, ["status_norm","status","game_status","event_status"]).lower()
    outcome = first(row, ["outcome_type","row_type","content_type"]).lower()
    if not headline:
        if winner and loser:
            headline = f"{winner} beat {loser}"
        elif matchup:
            headline = matchup
    if not outcome:
        outcome = "preview" if any(x in status for x in ["sched","upcoming","pre","not started"]) or ((" vs " in matchup.lower() or " at " in matchup.lower()) and not score) else "win"
    dt = None
    date_source = ""
    for k in ["event_datetime","event_date","result_date","scheduled_datetime_local","scheduled_date_local","game_datetime","game_date","date_utc","date","played_at","completed_at","start_time"]:
        dt = parse_dt(row.get(k))
        if dt:
            date_source = k
            break
    if not dt:
        for val in [matchup, headline, first(row, ["caption_seed","notes","time","start_time_display"])]:
            dt = parse_dt(val)
            if dt:
                date_source = "text_time"
                break
    event_date = dt.date().isoformat() if dt else ""
    event_datetime = dt.isoformat() if dt else ""

    sport = first(row, ["sport_norm","sport"]) or ("basketball" if re.search(r"wnba|fever|storm|sun|tempo|sparks|aces|lynx|wings|liberty|dream|sky|mercury", f"{matchup} {headline}", re.I) else "")
    league = first(row, ["league_norm","league"]) or ("WNBA" if sport == "basketball" else "")

    return {
        "graphics_headline": headline,
        "caption_seed": first(row, ["caption_seed","dek","summary"]) or headline,
        "matchup": matchup,
        "winner": winner,
        "loser": loser,
        "final_score_display": score,
        "sport_norm": sport,
        "league_norm": league,
        "gender_scope": first(row, ["gender_scope"]) or "women",
        "status_norm": status or ("scheduled" if outcome == "preview" else "final"),
        "manual_review": first(row, ["manual_review"]) or "No",
        "editorial_bucket": first(row, ["editorial_bucket"]) or ("Preview" if outcome == "preview" else "Must Post"),
        "content_action": first(row, ["content_action"]) or ("Preview Tonight" if outcome == "preview" else "Make First"),
        "posting_priority": first(row, ["posting_priority"]) or ("P1" if outcome != "archive" else "P3"),
        "confidence": first(row, ["confidence"]) or "1.0",
        "editorial_rank": first(row, ["editorial_rank"]) or "100",
        "scheduled_date_local": event_date,
        "source_url": first(row, ["source_url","url","link"]) or "results_desk",
        "selected_source": first(row, ["selected_source","source"]) or source_file,
        "all_sources_json": first(row, ["all_sources_json"]) or "[]",
        "outcome_type": outcome,
        "event_date": event_date,
        "event_datetime": event_datetime,
        "_date_source": date_source,
        "_source_file": source_file,
    }

def collect_source_rows() -> List[Dict[str,str]]:
    rows: List[Dict[str,str]] = []
    for fname in SOURCE_FILES:
        for r in read_csv(fname):
            n = normalize_row(r, fname)
            if clean(n.get("graphics_headline")) or clean(n.get("matchup")):
                rows.append(n)
    if not rows and Path("results_graphics_queue.md").exists():
        text = Path("results_graphics_queue.md").read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if re.search(r"\b(vs|at)\b", line, re.I):
                rows.append(normalize_row({"graphics_headline": clean(line), "matchup": clean(line), "status_norm": "scheduled"}, "results_graphics_queue.md"))
    out, seen = [], set()
    for r in rows:
        key = (r.get("graphics_headline","").lower(), r.get("event_date",""), r.get("_source_file",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def freshness_rows(rows: List[Dict[str,str]], max_hours: float) -> List[Dict[str,str]]:
    import os
    current = now()
    lookahead_hours = float(os.environ.get("HSD_PREVIEW_LOOKAHEAD_HOURS", "30"))
    out = []
    for r in rows:
        dt = parse_dt(r.get("event_datetime") or r.get("event_date"))
        status = "missing_event_date"
        age = ""
        if dt:
            age_f = (current - dt).total_seconds() / 3600.0
            age = f"{max(0.0, age_f):.1f}"
            if r.get("outcome_type") == "preview":
                # Allow upcoming schedules only inside the configured lookahead window,
                # and keep recently started schedules for max_hours.
                status = "fresh" if (-lookahead_hours <= age_f <= max_hours) else "stale"
            else:
                status = "fresh" if 0 <= age_f <= max_hours else "stale"
        out.append({
            "source_file": r.get("_source_file",""),
            "headline": r.get("graphics_headline",""),
            "event_date": r.get("event_date",""),
            "event_age_hours": age,
            "status": status,
            "date_source": r.get("_date_source",""),
            "row_type": r.get("outcome_type",""),
        })
    return out

def main() -> None:
    import os
    max_hours = float(os.environ.get("HSD_MAX_RESULT_FRESH_HOURS", "18"))
    rows = collect_source_rows()
    gate = freshness_rows(rows, max_hours)

    # Always overwrite the canonical contract files. No stale downstream CSVs.
    write_csv(OUT_TOP, rows, RESULT_FIELDS)
    write_csv(OUT_WOMENS, rows, RESULT_FIELDS)
    finals = [r for r in rows if r.get("outcome_type") != "preview" and clean(r.get("final_score_display"))]
    write_csv(OUT_FINALS, finals, RESULT_FIELDS)
    write_csv(OUT_RECON, rows, RESULT_FIELDS)
    write_csv(OUT_GATE, gate, GATE_FIELDS)

    fresh = [r for r in gate if r["status"] == "fresh"]
    stale = [r for r in gate if r["status"] == "stale"]
    missing = [r for r in gate if r["status"] == "missing_event_date"]

    lines = [
        "# HSD Results Freshness Gate v2.1",
        "",
        f"Generated: {iso_now()}",
        "",
        f"- result rows checked: {len(gate)}",
        f"- fresh rows: {len(fresh)}",
        f"- stale rows: {len(stale)}",
        f"- missing event date rows: {len(missing)}",
        f"- max result age hours: {max_hours}",
        "",
    ]
    if fresh:
        lines += ["## Fresh rows", ""] + [f"- {r['headline']} | {r['event_date']} | {r['event_age_hours']}h | {r['source_file']} | {r['row_type']}" for r in fresh[:25]] + [""]
    if stale:
        lines += ["## Stale rows", ""] + [f"- {r['headline']} | {r['event_date']} | {r['event_age_hours']}h | {r['source_file']} | {r['row_type']}" for r in stale[:25]] + [""]
    if missing:
        lines += ["## Missing event date rows", ""] + [f"- {r['headline']} | {r['source_file']}" for r in missing[:25]] + [""]
    Path(OUT_REPORT).write_text("\n".join(lines), encoding="utf-8")
    Path(OUT_CONTRACT).write_text(
        "# HSD Results Contract v2.1\n\n"
        f"Generated: {iso_now()}\n\n"
        f"- normalized_rows: {len(rows)}\n"
        f"- canonical_top_rows: {len(rows)}\n"
        f"- canonical_final_rows: {len(finals)}\n"
        f"- fresh_rows: {len(fresh)}\n"
        f"- stale_rows: {len(stale)}\n"
        f"- missing_date_rows: {len(missing)}\n\n"
        "This script normalizes whatever Results Desk emitted into the CSV contract expected by News Sync and Studio Bridge.\n",
        encoding="utf-8",
    )
    Path(OUT_MANIFEST).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": iso_now(),
        "counts": {
            "normalized_rows": len(rows),
            "fresh": len(fresh),
            "stale": len(stale),
            "missing_event_date": len(missing),
            "final_rows": len(finals),
        },
        "outputs": [OUT_TOP, OUT_WOMENS, OUT_FINALS, OUT_RECON, OUT_GATE, OUT_REPORT, OUT_CONTRACT],
    }, indent=2), encoding="utf-8")
    print(json.dumps({"normalized_rows": len(rows), "fresh": len(fresh), "stale": len(stale), "final_rows": len(finals)}, indent=2))

if __name__ == "__main__":
    main()
