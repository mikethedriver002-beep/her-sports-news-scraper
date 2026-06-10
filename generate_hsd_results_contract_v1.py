from __future__ import annotations
import csv, hashlib, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-results-contract-v3.0"
OUT_CSV = Path("results_contract_v2.csv")
OUT_JSONL = Path("results_contract_v2.jsonl")
OUT_REPORT = Path("results_contract_report.md")
OUT_DIR = None

FIELDS = [
    "run_id","event_id","row_kind","source_id","source_file","source_url","source_observed_at_utc","source_timezone",
    "scheduled_start_utc","completed_at_utc","sport","league","status","home_team_name","away_team_name",
    "winner_team_name","loser_team_name","score_home","score_away","score_display","event_date_local",
    "content_eligibility","freshness_reason","manual_review","headline","summary"
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

def parse_date(row: Dict[str, str]) -> str:
    for k in ["event_date","result_date","scheduled_date_local","game_date","date","event_datetime","scheduled_datetime_local","completed_at"]:
        v = clean(row.get(k))
        m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", v)
        if m:
            return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", v)
        if m:
            return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""

def event_id(row: Dict[str, str], source_file: str, event_date: str) -> str:
    blob = "|".join([
        event_date,
        clean(row.get("matchup") or row.get("event_name") or row.get("graphics_headline") or row.get("headline")),
        clean(row.get("winner") or row.get("winner_team_name")),
        clean(row.get("loser") or row.get("loser_team_name")),
        clean(row.get("final_score_display") or row.get("score_display")),
        source_file,
    ])
    return "event_" + hashlib.sha1(blob.encode()).hexdigest()[:14]

def row_kind(row: Dict[str, str]) -> str:
    status = clean(row.get("status_norm") or row.get("status")).lower()
    headline = clean(row.get("graphics_headline") or row.get("headline") or row.get("matchup")).lower()
    if "final" in status or "beat" in headline or clean(row.get("winner")):
        return "result"
    if " vs " in headline or " at " in headline or "scheduled" in status or "preview" in status:
        return "preview"
    return "news"

def normalize(row: Dict[str, str], source_file: str, run_id: str) -> Dict[str, str]:
    e_date = parse_date(row)
    kind = row_kind(row)
    headline = clean(row.get("graphics_headline") or row.get("headline") or row.get("matchup") or row.get("event_name"))
    score = clean(row.get("final_score_display") or row.get("score_display") or row.get("score"))
    eligibility = "eligible"
    reason = "normalized"
    manual_review = "No"
    if not e_date:
        eligibility = "blocked"
        reason = "missing_event_date"
        manual_review = "Yes"
    if kind == "news" and not headline:
        eligibility = "blocked"
        reason = "missing_headline"
        manual_review = "Yes"
    return {
        "run_id": run_id,
        "event_id": event_id(row, source_file, e_date),
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
        "score_display": score,
        "event_date_local": e_date,
        "content_eligibility": eligibility,
        "freshness_reason": reason,
        "manual_review": manual_review,
        "headline": headline,
        "summary": clean(row.get("caption_seed") or row.get("summary")),
    }

def main() -> None:
    current = read_current_run()
    run_id = current.get("run_id","local")
    rows = []
    for source_file in SOURCE_FILES:
        for r in read_csv(source_file):
            rows.append(normalize(r, source_file, run_id))
    # Dedupe by event_id, prefer eligible rows and top_womens_results
    priority = {"top_womens_results.csv": 0, "today_final_results.csv": 1, "today_womens_results.csv": 2, "reconciled_events.csv": 3}
    rows = sorted(rows, key=lambda r: (r["event_id"], 0 if r["content_eligibility"] == "eligible" else 1, priority.get(r["source_file"], 9)))
    by_event = {}
    for r in rows:
        by_event.setdefault(r["event_id"], r)
    rows = list(by_event.values())

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")
    eligible = sum(1 for r in rows if r["content_eligibility"] == "eligible")
    OUT_REPORT.write_text(
        "# HSD Results Contract v2 Report\n\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
        f"- rows: {len(rows)}\n"
        f"- eligible: {eligible}\n"
        f"- blocked: {len(rows)-eligible}\n\n"
        + "\n".join(f"- {r['content_eligibility']} | {r['row_kind']} | {r['event_date_local']} | {r['headline']}" for r in rows[:30]) + "\n",
        encoding="utf-8"
    )
    # Run scoped copy
    run_dir = Path(current.get("run_dir","."))
    if run_dir != Path("."):
        (run_dir / "results").mkdir(parents=True, exist_ok=True)
        for p in [OUT_CSV, OUT_JSONL, OUT_REPORT]:
            (run_dir / "results" / p.name).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"results_contract_rows": len(rows), "eligible": eligible}, indent=2))

if __name__ == "__main__":
    main()
