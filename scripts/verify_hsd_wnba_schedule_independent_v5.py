from __future__ import annotations

import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

VERSION = "v5.0-independent-wnba-schedule-verification"
EXPECTED = Path("config/hsd_expected_games_v5.csv")
OUT_CSV = Path("independent_schedule_verification_v5.csv")
OUT_JSON = Path("independent_schedule_verification_v5.json")
OUT_MD = Path("independent_schedule_verification_v5.md")
ABBR = {"ATL":"Atlanta Dream","CHI":"Chicago Sky","CON":"Connecticut Sun","DAL":"Dallas Wings","GSV":"Golden State Valkyries","IND":"Indiana Fever","LVA":"Las Vegas Aces","LAS":"Los Angeles Sparks","MIN":"Minnesota Lynx","NYL":"New York Liberty","PHX":"Phoenix Mercury","POR":"Portland Fire","SEA":"Seattle Storm","TOR":"Toronto Tempo","WAS":"Washington Mystics"}
FIELDS = ["date","home_team","away_team","expected_key","independent_key","status","source_event_id","notes"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def norm(v: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", clean(v).lower())).strip()


def key_for(date: str, home: str, away: str) -> str:
    pair = sorted([norm(home), norm(away)])
    return "|".join(["basketball", clean(date), pair[0], pair[1]])


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def endpoint() -> str:
    return "https://" + "stats.wnba.com" + "/stats/" + "scoreboardv2"


def md(date: str) -> str:
    y, m, d = date.split("-")
    return f"{m}/{d}/{y}"


def sets(data: dict[str, Any]) -> dict[str, Any]:
    return {clean(x.get("name")): x for x in data.get("resultSets", []) if clean(x.get("name"))}


def as_dict(headers: list[str], row: list[Any]) -> dict[str, Any]:
    return {headers[i]: row[i] for i in range(min(len(headers), len(row)))}


def split_code(code: str) -> tuple[str, str]:
    suffix = clean(code).split("/")[-1].upper()
    for away in sorted(ABBR, key=len, reverse=True):
        if suffix.startswith(away):
            home = suffix[len(away):]
            if home in ABBR:
                return ABBR[away], ABBR[home]
    return "", ""


def fetch_date(date: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    params = {"DayOffset":"0", "GameDate":md(date), "LeagueID":"10"}
    headers = {"User-Agent":"Mozilla/5.0", "Accept":"application/json", "Referer":"https://www.wnba.com/"}
    try:
        r = requests.get(endpoint(), params=params, headers=headers, timeout=20)
        status = r.status_code
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        return [], {"date": date, "ok": False, "http_status": locals().get("status", 0), "events": 0, "notes": f"{type(exc).__name__}: {exc}"}
    game_header = sets(data).get("GameHeader") or {}
    headers_list = game_header.get("headers") or []
    out = []
    for raw in game_header.get("rowSet") or []:
        row = as_dict(headers_list, raw)
        away, home = split_code(clean(row.get("GAMECODE")))
        if away and home:
            date_est = clean(row.get("GAME_DATE_EST"))[:10] or date
            key = key_for(date_est, home, away)
            out.append({"date":date_est,"home_team":home,"away_team":away,"expected_key":key,"independent_key":key,"status":"independent_seen","source_event_id":clean(row.get("GAME_ID")),"notes":"official stats scoreboard"})
    return out, {"date": date, "ok": True, "http_status": status, "events": len(out), "notes":"ok"}


def verify() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected = read_rows(EXPECTED)
    dates = sorted({clean(r.get("date")) for r in expected if clean(r.get("date"))})
    independent, health = [], []
    for date in dates:
        rows, h = fetch_date(date)
        independent.extend(rows); health.append(h)
    by_key = {r["independent_key"]: r for r in independent}
    expected_keys = {r.get("expected_key") for r in expected}
    out = []
    for r in expected:
        key = clean(r.get("expected_key"))
        found = by_key.get(key)
        out.append({"date":r.get("date"),"home_team":r.get("home_team"),"away_team":r.get("away_team"),"expected_key":key,"independent_key":found.get("independent_key","") if found else "","status":"matched" if found else "missing_from_independent","source_event_id":found.get("source_event_id","") if found else "","notes":found.get("notes","") if found else "not found"})
    for r in independent:
        if r["independent_key"] not in expected_keys:
            r2 = dict(r); r2["status"] = "extra_in_independent"; out.append(r2)
    summary = {"version":VERSION,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"expected_games":len(expected),"independent_games":len(independent),"matched":sum(1 for r in out if r.get("status")=="matched"),"missing_from_independent":sum(1 for r in out if r.get("status")=="missing_from_independent"),"extra_in_independent":sum(1 for r in out if r.get("status")=="extra_in_independent"),"source_available":any(h.get("ok") for h in health),"health":health}
    return out, summary


def report(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = ["# Independent WNBA Schedule Verification v5", "", f"Generated: `{summary['generated_at_utc']}`", "", "## Counts", ""]
    for k in ["expected_games","independent_games","matched","missing_from_independent","extra_in_independent","source_available"]:
        lines.append(f"- {k}: `{summary.get(k)}`")
    bad = [r for r in rows if r.get("status") != "matched"]
    lines += ["", "## Mismatches", ""] + (["- None"] if not bad else [f"- {r['status']} | {r.get('date')} | {r.get('away_team')} at {r.get('home_team')}" for r in bad])
    return "\n".join(lines) + "\n"


def main() -> None:
    rows, summary = verify()
    write_rows(OUT_CSV, rows)
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    OUT_MD.write_text(report(summary, rows), encoding="utf-8")
    print(json.dumps({"matched":summary["matched"], "missing":summary["missing_from_independent"], "extra":summary["extra_in_independent"]}, indent=2))


if __name__ == "__main__":
    main()
