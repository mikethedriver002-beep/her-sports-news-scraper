from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, UnidentifiedImageError

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


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def looks_like_svg(data: bytes) -> bool:
    head = data[:500].lstrip().lower()
    return head.startswith(b"<svg") or head.startswith(b"<?xml") and b"<svg" in head


def asset_decodable(path: Path) -> bool:
    if not path.exists() or not path.is_file() or path.stat().st_size <= 100:
        return False
    suffix = path.suffix.lower()
    try:
        if suffix == ".svg":
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "<svg" not in text:
                return False
            try:
                import cairosvg
                cairosvg.svg2png(url=path.as_posix(), bytestring=None, output_width=64, output_height=64)
            except TypeError:
                # Older cairosvg versions may not support this invocation. A real SVG
                # payload is still acceptable; renderer will convert it later.
                pass
            except Exception:
                return False
            return True
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.convert("RGBA")
        return True
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return False


def write_payload(data: bytes, target_path: Path) -> Dict[str, Any]:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if looks_like_svg(data) and target_path.suffix.lower() != ".svg":
            try:
                import cairosvg
                cairosvg.svg2png(bytestring=data, write_to=target_path.as_posix(), output_width=500, output_height=500)
            except Exception as exc:
                return {"status": "failed", "bytes": 0, "reason": f"svg conversion failed: {type(exc).__name__}: {exc}"}
        else:
            target_path.write_bytes(data)
        if not asset_decodable(target_path):
            try:
                target_path.unlink()
            except Exception:
                pass
            return {"status": "failed", "bytes": 0, "reason": "downloaded asset was not image-decodable"}
        return {"status": "downloaded", "bytes": target_path.stat().st_size, "reason": ""}
    except Exception as exc:
        return {"status": "failed", "bytes": 0, "reason": f"write failed: {type(exc).__name__}: {exc}"}


def download(url: str, target_path: Path, attempts: int = 2) -> Dict[str, Any]:
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HerSportsDailyAssetRegistry/1.3"})
            with urllib.request.urlopen(req, timeout=24) as resp:
                data = resp.read()
            if len(data) < 100:
                return {"status": "failed", "bytes": 0, "reason": "download too small"}
            result = write_payload(data, target_path)
            if result["status"] == "downloaded":
                return result
            if attempt < attempts:
                time.sleep(1.0 * attempt)
                continue
            return result
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
        "image_decodable": False,
    }
    if not source_url or not target_path.as_posix():
        result.update({"status": "skipped", "reason": "missing source_url or target_path"})
        return result
    if asset_decodable(target_path):
        result.update({"status": "exists", "bytes": target_path.stat().st_size, "image_decodable": True})
        return result
    if target_path.exists():
        result["reason"] = "existing target was not image-decodable; redownloading"
        try:
            target_path.unlink()
        except Exception:
            pass

    primary = download(source_url, target_path)
    if primary["status"] == "downloaded" and asset_decodable(target_path):
        result.update(primary)
        result["image_decodable"] = True
        return result

    fb = fallback_url(team_id)
    if fb:
        fallback_path = Path(f"assets/leagues/wnba/teams/{team_id}/logo.png")
        result["fallback_url"] = fb
        result["fallback_target_path"] = fallback_path.as_posix()
        if asset_decodable(fallback_path):
            result.update({"status": "exists_fallback", "bytes": fallback_path.stat().st_size, "reason": primary.get("reason", ""), "image_decodable": True})
            return result
        if fallback_path.exists():
            try:
                fallback_path.unlink()
            except Exception:
                pass
        fallback = download(fb, fallback_path, attempts=1)
        if fallback["status"] == "downloaded" and asset_decodable(fallback_path):
            result.update({"status": "downloaded_fallback", "bytes": fallback_path.stat().st_size, "reason": f"primary failed: {primary.get('reason', '')}", "image_decodable": True})
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
    undecodable = len([r for r in results if not r.get("image_decodable")])
    report = {
        "version": "hsd-wnba-logo-source-fetcher-v1.3-decodable-assets",
        "generated_at_utc": now_iso(),
        "sources": len(rows),
        "synthesized_fallback_sources": synthesized,
        "downloaded": downloaded,
        "existing": existing,
        "failed": failed,
        "fallback_downloaded": fallback_downloaded,
        "undecodable": undecodable,
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
        f"- undecodable after fetch: {undecodable}",
        "",
        "## Results",
        "",
    ]
    for item in results:
        suffix = f" - {item['reason']}" if item.get("reason") else ""
        if item.get("fallback_url"):
            suffix += f" | fallback: {item.get('fallback_url')}"
        lines.append(f"- {item['team_name']}: {item['status']} decodable={item.get('image_decodable')} -> `{item['target_path']}`{suffix}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(rows), "downloaded": downloaded, "existing": existing, "failed": failed, "fallback_downloaded": fallback_downloaded, "undecodable": undecodable}, indent=2))


if __name__ == "__main__":
    main()
