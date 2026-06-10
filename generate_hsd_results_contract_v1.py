
from __future__ import annotations
import csv, hashlib, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-results-contract-v3.1-freshness-dedupe"
OUT_CSV = Path("results_contract_v2.csv")
OUT_JSONL = Path("results_contract_v2.jsonl")
OUT_REPORT = Path("results_contract_report.md")

FIELDS = [
    "run_id","event_id","row_kind","source_id","source_file","source_url","source_observed_at_utc","source_timezone",
    "scheduled_start_utc","completed_at_utc","sport","league","status","home_team_name","away_team_name",
    "winner_team_name","loser_team_name","score_home","score_away","score_display","event_date_local",
    "content_eligibility","freshness_reason","manual_review","headline","summary","event_age_hours","dedupe_key"
]
SOURCE_FILES = ["top_womens_results.csv","today_final_results.csv","today_womens_results.csv","reconciled_events.csv","today_results_board.csv","today_box_scores.csv"]

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def read_current_run() -> Dict[str, str]:
    p = Path("hsd_current_run.json")
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: pass
    return {"run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_local"), "run_dir": "."}

def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def parse_date_value(v: str) -> str:
    s = clean(v)
    if not s:
        return ""
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", s)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""

def parse_date(row: Dict[str, str]) -> str:
    for k in ["event_date","result_date","scheduled_date_local","game_date","date","event_datetime","scheduled_datetime_local","completed_at","start_time"]:
        d = parse_date_value(row.get(k, ""))
        if d:
            return d
    for k in ["headline","graphics_headline","matchup","event_name"]:
        d = parse_date_value(row.get(k, ""))
        if d:
            return d
    return ""

def date_to_dt(date_s: str) -> datetime | None:
    if not date_s:
        return None
    try:
        y,m,d = [int(x) for x in date_s.split("-")]
        return datetime(y,m,d,12,0,0,tzinfo=timezone.utc)
    except Exception:
        return None

def row_kind(row: Dict[str, str]) -> str:
    status = clean(row.get("status_norm") or row.get("status")).lower()
    headline = clean(row.get("graphics_headline") or row.get("headline") or row.get("matchup") or row.get("event_name")).lower()
    if "final" in status or "beat" in headline or clean(row.get("winner") or row.get("winner_team_name")):
        return "result"
    if " vs " in headline or " at " in headline or "scheduled" in status or "preview" in status:
        return "preview"
    return "news"

def norm_words(v: str) -> str:
    v = clean(v).lower()
    v = re.sub(r"[^a-z0-9]+", " ", v)
    return re.sub(r"\s+", " ", v).strip()

def headline_key(headline: str) -> str:
    h = norm_words(headline)
    h = re.sub(r"\b(wed|wednesday|thu|thursday|fri|friday|sat|saturday|sun|sunday|mon|monday|tue|tuesday)\b", "", h)
    h = re.sub(r"\b\d{1,2}\s?\d{0,2}\s?(am|pm|edt|est|et)?\b", "", h)
    return re.sub(r"\s+", " ", h).strip()

def make_dedupe_key(row: Dict[str,str], kind: str, event_date: str, headline: str) -> str:
    teams = [norm_words(row.get(k,"")) for k in ["home_team","home_team_name","away_team","away_team_name","winner","winner_team_name","loser","loser_team_name"] if clean(row.get(k,""))]
    core = "|".join(sorted(set(teams))) if teams else headline_key(headline)
    return f"{kind}|{event_date}|{core}"

def event_id_for(dedupe_key: str) -> str:
    return "event_" + hashlib.sha1(dedupe_key.encode()).hexdigest()[:14]

def eligibility_for(kind: str, event_date: str) -> tuple[str,str,str,float|str]:
    if not event_date:
        return "blocked", "missing_event_date", "Yes", ""
    dt = date_to_dt(event_date)
    if not dt:
        return "blocked", "bad_event_date", "Yes", ""
    now = datetime.now(timezone.utc)
    max_result = float(os.environ.get("HSD_MAX_RESULT_FRESH_HOURS","18"))
    lookahead = float(os.environ.get("HSD_PREVIEW_LOOKAHEAD_HOURS","30"))
    age = (now - dt).total_seconds()/3600.0
    if kind == "result":
        if age <= max_result:
            return "eligible", "fresh_result", "No", max(0, age)
        return "blocked", f"stale_result_{age:.1f}h", "No", max(0, age)
    if kind == "preview":
        hours_until = (dt - now).total_seconds()/3600.0
        if -6 <= hours_until <= lookahead:
            return "eligible", "fresh_upcoming_or_today_preview", "No", age
        return "blocked", f"preview_outside_window_{hours_until:.1f}h", "No", age
    return "review", "news_requires_review", "Yes", age

def normalize(row: Dict[str, str], source_file: str, run_id: str) -> Dict[str, str]:
    e_date = parse_date(row)
    kind = row_kind(row)
    headline = clean(row.get("graphics_headline") or row.get("headline") or row.get("matchup") or row.get("event_name"))
    dedupe = make_dedupe_key(row, kind, e_date, headline)
    eligibility, reason, review, age = eligibility_for(kind, e_date)
    return {
        "run_id": run_id,
        "event_id": event_id_for(dedupe),
        "row_kind": kind,
        "source_id": clean(row.get("source_id") or source_file.replace(".csv","")),
        "source_file": source_file,
        "source_url": clean(row.get("source_url") or row.get("selected_source")),
        "source_observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_timezone": clean(row.get("source_timezone") or "America/New_York"),
        "scheduled_start_utc": clean(row.get("scheduled_datetime_utc") or row.get("event_datetime")),
        "completed_at_utc": clean(row.get("completed_at_utc") or row.get("completed_at")),
        "sport": clean(row.get("sport_norm") or row.get("sport") or "basketball"),
        "league": clean(row.get("league_norm") or row.get("league") or "WNBA"),
        "status": clean(row.get("status_norm") or row.get("status")),
        "home_team_name": clean(row.get("home_team") or row.get("home_team_name")),
        "away_team_name": clean(row.get("away_team") or row.get("away_team_name")),
        "winner_team_name": clean(row.get("winner") or row.get("winner_team_name")),
        "loser_team_name": clean(row.get("loser") or row.get("loser_team_name")),
        "score_home": clean(row.get("score_home")),
        "score_away": clean(row.get("score_away")),
        "score_display": clean(row.get("final_score_display") or row.get("score_display") or row.get("score")),
        "event_date_local": e_date,
        "content_eligibility": eligibility,
        "freshness_reason": reason,
        "manual_review": review,
        "headline": headline,
        "summary": clean(row.get("caption_seed") or row.get("summary")),
        "event_age_hours": f"{age:.1f}" if isinstance(age, float) else "",
        "dedupe_key": dedupe,
    }

def source_priority(source_file: str) -> int:
    return {"top_womens_results.csv":0, "today_final_results.csv":1, "today_womens_results.csv":2, "reconciled_events.csv":3, "today_results_board.csv":4}.get(source_file, 9)

def main() -> None:
    current = read_current_run()
    run_id = current.get("run_id","local")
    all_rows = []
    for source_file in SOURCE_FILES:
        for r in read_csv(source_file):
            all_rows.append(normalize(r, source_file, run_id))
    all_rows = sorted(all_rows, key=lambda r: (0 if r["content_eligibility"] == "eligible" else 1, source_priority(r["source_file"])))
    by_key = {}
    for r in all_rows:
        by_key.setdefault(r["dedupe_key"], r)
    rows = sorted(by_key.values(), key=lambda r: (0 if r["content_eligibility"] == "eligible" else 1, r["row_kind"], r["event_date_local"], r["headline"]))
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")
    eligible = sum(1 for r in rows if r["content_eligibility"] == "eligible")
    lines = ["# HSD Results Contract v2 Report", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", f"Version: {VERSION}", "", f"- rows: {len(rows)}", f"- eligible: {eligible}", f"- blocked/review: {len(rows)-eligible}", ""]
    lines += [f"- {r['content_eligibility']} | {r['row_kind']} | {r['event_date_local'] or 'missing'} | {r['freshness_reason']} | {r['headline']}" for r in rows[:40]]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_dir = Path(current.get("run_dir","."))
    if run_dir != Path("."):
        (run_dir / "results").mkdir(parents=True, exist_ok=True)
        for p in [OUT_CSV, OUT_JSONL, OUT_REPORT]:
            (run_dir / "results" / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"results_contract_rows": len(rows), "eligible": eligible}, indent=2))

if __name__ == "__main__":
    main()
