from __future__ import annotations

import csv
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

import requests

VERSION = "v5.0-multisport-review-first"
TIMEZONE = "America/New_York"
LOOKBACK_DAYS = 1
LOOKAHEAD_DAYS = 1
OUT_CSV = Path("multisport_results_observations_v5.csv")
OUT_JSON = Path("multisport_results_modules_v5.json")
OUT_MD = Path("multisport_results_modules_v5.md")
FIELDS = ["module", "source_name", "date", "sport", "league", "event_name", "status", "home_or_player", "away_or_position", "score_or_result", "source_url", "review_status", "notes"]
MODULES = [
    {"module":"nwsl_soccer", "sport":"soccer", "league":"NWSL", "path":"sports/soccer/usa.nwsl/scoreboard", "source":"espn_public_nwsl"},
    {"module":"women_soccer", "sport":"soccer", "league":"women_soccer", "path":"sports/soccer/scoreboard", "source":"espn_public_soccer_review"},
    {"module":"tennis_wta", "sport":"tennis", "league":"WTA", "path":"sports/tennis/wta/scoreboard", "source":"espn_public_wta"},
    {"module":"lpga_golf", "sport":"golf", "league":"LPGA", "path":"sports/golf/lpga/scoreboard", "source":"espn_public_lpga"},
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def date_window() -> list[str]:
    if ZoneInfo is not None:
        today = datetime.now(ZoneInfo(TIMEZONE)).date()
    else:
        today = datetime.now(timezone.utc).date()
    return [(today + timedelta(days=i)).strftime("%Y%m%d") for i in range(-LOOKBACK_DAYS, LOOKAHEAD_DAYS + 1)]


def endpoint(path: str) -> str:
    return "https://site.api.espn.com/apis/site/v2/" + path


def fetch_json(url: str, params: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        r = requests.get(url, params=params, headers={"User-Agent":"HerSportsDailyMultiSport/5.0"}, timeout=20)
        status = r.status_code
        r.raise_for_status()
        data = r.json()
        return data, {"ok": True, "http_status": status, "notes": "ok"}
    except Exception as exc:
        return {}, {"ok": False, "http_status": locals().get("status", 0), "notes": f"{type(exc).__name__}: {exc}"}


def event_rows(module: dict[str, str], date_compact: str, data: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for event in data.get("events", []) or []:
        name = clean(event.get("name") or event.get("shortName"))
        status = clean((((event.get("status") or {}).get("type") or {}).get("description") or ((event.get("status") or {}).get("type") or {}).get("detail")))
        source_url = clean(event.get("links", [{}])[0].get("href") if event.get("links") else "")
        home = away = score = ""
        comps = event.get("competitions") or []
        if comps:
            for comp in comps[0].get("competitors") or []:
                team = clean(((comp.get("team") or {}).get("displayName") or (comp.get("athlete") or {}).get("displayName")))
                val = clean(comp.get("score") or comp.get("curatedRank") or comp.get("displayValue"))
                if clean(comp.get("homeAway")).lower() == "home":
                    home = team
                    score = f"{score} | {team} {val}" if val else score
                elif clean(comp.get("homeAway")).lower() == "away":
                    away = team
                    score = f"{score} | {team} {val}" if val else score
                elif team:
                    if not home:
                        home = team
                    elif not away:
                        away = team
        rows.append({"module":module["module"], "source_name":module["source"], "date":date_compact, "sport":module["sport"], "league":module["league"], "event_name":name, "status":status, "home_or_player":home, "away_or_position":away, "score_or_result":score.strip(" |"), "source_url":source_url, "review_status":"review_only", "notes":"multi-sport module output is not contract/publish eligible yet"})
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in FIELDS})


def report_md(summary: dict[str, Any], rows: list[dict[str, str]]) -> str:
    lines = ["# HSD Multi-Sport Results Modules v5", "", f"Generated: `{summary['generated_at_utc']}`", f"Version: `{summary['version']}`", "", "## Policy", "", "- Review-only lane.", "- Does not feed results_contract_v2.csv yet.", "- Use only after source-health and parsing are verified per sport.", "", "## Module health", ""]
    for item in summary["module_health"]:
        lines.append(f"- {item['module']} | {item['date']} | ok={item['ok']} | events={item['events_found']} | {item['notes']}")
    lines.extend(["", "## Observations", ""])
    if not rows:
        lines.append("No multi-sport observations were produced.")
    else:
        for row in rows[:80]:
            lines.append(f"- {row['module']} | {row['date']} | {row['event_name']} | {row['status']} | {row['home_or_player']} vs {row['away_or_position']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    rows: list[dict[str, str]] = []
    health: list[dict[str, Any]] = []
    for module in MODULES:
        url = endpoint(module["path"])
        for date in date_window():
            data, h = fetch_json(url, {"dates": date})
            module_rows = event_rows(module, date, data) if h["ok"] else []
            rows.extend(module_rows)
            health.append({"module": module["module"], "date": date, "ok": h["ok"], "http_status": h["http_status"], "events_found": len(module_rows), "notes": h["notes"]})
            time.sleep(0.1)
    summary = {"version": VERSION, "generated_at_utc": now_iso(), "review_only": True, "observations": len(rows), "module_health": health}
    write_csv(OUT_CSV, rows)
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    OUT_MD.write_text(report_md(summary, rows), encoding="utf-8")
    print(json.dumps({"multisport_observations": len(rows), "modules_checked": len(health)}, indent=2))


if __name__ == "__main__":
    main()
