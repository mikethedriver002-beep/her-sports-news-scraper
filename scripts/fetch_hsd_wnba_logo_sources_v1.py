from __future__ import annotations

import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path("data/asset_registry/wnba")
TEAMS = ROOT / "teams.csv"
SOURCES = ROOT / "logo_sources.csv"
REPORT_JSON = ROOT / "logo_fetch_report.json"
REPORT_MD = ROOT / "logo_fetch_report.md"

TEAM_FAVICON_CODES = {
    "atlanta_dream": "ATL",
    "chicago_sky": "CHI",
    "connecticut_sun": "CON",
    "indiana_fever": "IND",
    "new_york_liberty": "NYL",
    "toronto_tempo": "TOR",
    "washington_mystics": "WAS",
    "dallas_wings": "DAL",
    "golden_state_valkyries": "GSV",
    "las_vegas_aces": "LVA",
    "los_angeles_sparks": "LAS",
    "minnesota_lynx": "MIN",
    "phoenix_mercury": "PHX",
    "portland_fire": "POR",
    "seattle_storm": "SEA",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def download(url: str, target_path: Path, attempts: int = 2) -> Dict[str, Any]:
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HerSportsDailyAssetRegistry/1.2"})
            with urllib.request.urlopen(req, timeout=24) as resp:
                data = resp.read()
            if len(data) < 100:
                return {"status": "failed", "bytes": 0, "reason": "download too small"}
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(data)
            return {"status": "downloaded", "bytes": len(data), "reason": ""}
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            if attempt < attempts and ("429" in reason or "Too many" in reason):
                time.sleep(2.0 * attempt)
                continue
            return {"status": "failed", "bytes": 0, "reason": reason}
    return {"status": "failed", "bytes": 0, "reason": "unknown"}


def fallback_url(team_id: str) -> Optional[str]:
    code = TEAM_FAVICON_CODES.get(team_id)
    if not code:
        return None
    return f"https://cdn.wnba.com/static/next/teams/favicons/{code}/apple-touch-icon.png"


def complete_source_rows() -> List[Dict[str, str]]:
    """Return explicit logo sources plus synthesized official WNBA favicon fallbacks.

    V2 had only a partial logo_sources.csv, so missing teams could drift in/out based
    on ephemeral graphics upload packs. V3 keeps explicit source rows when available
    and synthesizes a free official WNBA favicon row for any team not listed.
    """
    rows = read_csv(SOURCES)
    by_team = {row.get("team_id", ""): row for row in rows if row.get("team_id")}
    for team in read_csv(TEAMS):
        team_id = team.get("team_id", "")
        if not team_id or team_id in by_team:
            continue
        fb = fallback_url(team_id)
        if not fb:
            continue
        by_team[team_id] = {
            "team_id": team_id,
            "team_name": team.get("team_name", team_id),
            "source_url": fb,
            "target_path": f"assets/leagues/wnba/teams/{team_id}/logo.png",
            "source_note": "synthesized_official_wnba_favicon_fallback",
        }
    ordered: List[Dict[str, str]] = []
    seen: set[str] = set()
    for team in read_csv(TEAMS):
        team_id = team.get("team_id", "")
        if team_id in by_team:
            ordered.append(by_team[team_id])
            seen.add(team_id)
    for row in rows:
        team_id = row.get("team_id", "")
        if team_id and team_id not in seen:
            ordered.append(row)
    return ordered


def fetch_one(row: Dict[str, str]) -> Dict[str, Any]:
    team_id = row.get("team_id", "")
    team_name = row.get("team_name", team_id)
    source_url = row.get("source_url", "")
    target_path = Path(row.get("target_path", ""))
    result: Dict[str, Any] = {
        "team_id": team_id,
        "team_name": team_name,
        "source_url": source_url,
        "target_path": target_path.as_posix(),
        "source_note": row.get("source_note", ""),
        "fallback_url": "",
        "fallback_target_path": "",
        "status": "unknown",
        "bytes": 0,
        "reason": "",
    }
    if not source_url or not target_path.as_posix():
        result.update({"status": "skipped", "reason": "missing source_url or target_path"})
        return result
    if target_path.exists() and target_path.stat().st_size > 100:
        result.update({"status": "exists", "bytes": target_path.stat().st_size})
        return result

    primary = download(source_url, target_path)
    if primary["status"] in {"downloaded", "exists"}:
        result.update(primary)
        return result

    # Fallback to official WNBA CDN team favicon. This is used only after the explicit
    # source fails and is written to the canonical team folder as logo.png.
    fb = fallback_url(team_id)
    if fb:
        fallback_path = Path(f"assets/leagues/wnba/teams/{team_id}/logo.png")
        result["fallback_url"] = fb
        result["fallback_target_path"] = fallback_path.as_posix()
        if fallback_path.exists() and fallback_path.stat().st_size > 100:
            result.update({"status": "exists_fallback", "bytes": fallback_path.stat().st_size, "reason": primary.get("reason", "")})
            return result
        fallback = download(fb, fallback_path, attempts=1)
        if fallback["status"] == "downloaded":
            result.update({"status": "downloaded_fallback", "bytes": fallback["bytes"], "reason": f"primary failed: {primary.get('reason', '')}"})
            return result
        result.update({"status": "failed", "reason": f"primary failed: {primary.get('reason', '')}; fallback failed: {fallback.get('reason', '')}"})
        return result

    result.update(primary)
    return result


def main() -> None:
    rows = complete_source_rows()
    results = [fetch_one(row) for row in rows]
    downloaded = len([r for r in results if r["status"] in {"downloaded", "downloaded_fallback"}])
    existing = len([r for r in results if r["status"] in {"exists", "exists_fallback"}])
    failed = len([r for r in results if r["status"] == "failed"])
    fallback_downloaded = len([r for r in results if r["status"] == "downloaded_fallback"])
    synthesized = len([r for r in rows if r.get("source_note") == "synthesized_official_wnba_favicon_fallback"])
    report = {
        "version": "hsd-wnba-logo-source-fetcher-v1.2-complete-source-rows",
        "generated_at_utc": now_iso(),
        "sources": len(rows),
        "synthesized_fallback_sources": synthesized,
        "downloaded": downloaded,
        "existing": existing,
        "failed": failed,
        "fallback_downloaded": fallback_downloaded,
        "results": results,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Logo Source Fetch Report",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Version: {report['version']}",
        "",
        "## Counts",
        "",
        f"- sources: {report['sources']}",
        f"- synthesized fallback sources: {synthesized}",
        f"- downloaded: {downloaded}",
        f"- existing: {existing}",
        f"- failed: {failed}",
        f"- fallback downloaded: {fallback_downloaded}",
        "",
        "## Results",
        "",
    ]
    for item in results:
        suffix = f" - {item['reason']}" if item.get("reason") else ""
        if item.get("fallback_url"):
            suffix += f" | fallback: {item.get('fallback_url')}"
        lines.append(f"- {item['team_name']}: {item['status']} -> `{item['target_path']}`{suffix}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(rows), "downloaded": downloaded, "existing": existing, "failed": failed, "fallback_downloaded": fallback_downloaded}, indent=2))


if __name__ == "__main__":
    main()
