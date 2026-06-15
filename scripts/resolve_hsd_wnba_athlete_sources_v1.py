from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("data/asset_registry/wnba")
TEAMS = ROOT / "teams.csv"
ATHLETE_SOURCES = ROOT / "athlete_sources.csv"
REPORT_JSON = ROOT / "athlete_source_resolver_report.json"
REPORT_MD = ROOT / "athlete_source_resolver_report.md"

TEAM_SUBDOMAINS = {
    "atlanta_dream": "dream",
    "chicago_sky": "sky",
    "connecticut_sun": "sun",
    "indiana_fever": "fever",
    "new_york_liberty": "liberty",
    "toronto_tempo": "tempo",
    "washington_mystics": "mystics",
    "dallas_wings": "wings",
    "golden_state_valkyries": "valkyries",
    "las_vegas_aces": "aces",
    "los_angeles_sparks": "sparks",
    "minnesota_lynx": "lynx",
    "phoenix_mercury": "mercury",
    "portland_fire": "fire",
    "seattle_storm": "storm",
}

FIELDS = ["team_id", "team_name", "roster_url", "source_note"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def check_url(url: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"url": url, "status": "unknown", "http_ok": False, "has_roster_marker": False, "reason": ""}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HerSportsDailyAthleteSourceResolver/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read(240000)
            result["status_code"] = getattr(resp, "status", 200)
        text = raw.decode("utf-8", errors="replace")
        result["http_ok"] = True
        result["has_roster_marker"] = ("Roster" in text and "Team Roster" in text) or "player" in text.lower()
        result["status"] = "ok" if result["has_roster_marker"] else "needs_review"
        if not result["has_roster_marker"]:
            result["reason"] = "url fetched but roster markers not found"
    except Exception as exc:
        result["status"] = "failed"
        result["reason"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    teams = read_csv(TEAMS)
    rows: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []
    for team in teams:
        team_id = team.get("team_id", "")
        team_name = team.get("team_name", "")
        sub = TEAM_SUBDOMAINS.get(team_id)
        if not sub:
            url = ""
            status = {"team_id": team_id, "team_name": team_name, "url": "", "status": "failed", "reason": "missing subdomain mapping"}
        else:
            url = f"https://{sub}.wnba.com/roster"
            status = check_url(url)
            status.update({"team_id": team_id, "team_name": team_name})
        rows.append({"team_id": team_id, "team_name": team_name, "roster_url": url, "source_note": f"official_team_subdomain_roster_{status.get('status')}"})
        checks.append(status)
    write_csv(ATHLETE_SOURCES, rows, FIELDS)
    ok = len([c for c in checks if c.get("status") == "ok"])
    failed = len([c for c in checks if c.get("status") == "failed"])
    review = len([c for c in checks if c.get("status") == "needs_review"])
    report = {
        "version": "hsd-wnba-athlete-source-resolver-v1",
        "generated_at_utc": now_iso(),
        "sources": len(rows),
        "ok": ok,
        "needs_review": review,
        "failed": failed,
        "source_file": ATHLETE_SOURCES.as_posix(),
        "checks": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Athlete Source Resolver v1",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Counts",
        "",
        f"- sources: {report['sources']}",
        f"- ok: {ok}",
        f"- needs_review: {review}",
        f"- failed: {failed}",
        "",
        "## Sources",
        "",
    ]
    for item in checks:
        reason = f" - {item.get('reason')}" if item.get("reason") else ""
        lines.append(f"- {item.get('team_name')}: {item.get('status')} -> `{item.get('url')}`{reason}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(rows), "ok": ok, "needs_review": review, "failed": failed}, indent=2))


if __name__ == "__main__":
    main()
