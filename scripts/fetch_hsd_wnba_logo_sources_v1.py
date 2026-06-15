from __future__ import annotations

import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SOURCES = Path("data/asset_registry/wnba/logo_sources.csv")
REPORT_JSON = Path("data/asset_registry/wnba/logo_fetch_report.json")
REPORT_MD = Path("data/asset_registry/wnba/logo_fetch_report.md")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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
    try:
        req = urllib.request.Request(source_url, headers={"User-Agent": "HerSportsDailyAssetRegistry/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) < 100:
            result.update({"status": "failed", "reason": "download too small"})
            return result
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        result.update({"status": "downloaded", "bytes": len(data)})
        return result
    except Exception as exc:
        result.update({"status": "failed", "reason": f"{type(exc).__name__}: {exc}"})
        return result


def main() -> None:
    rows = read_csv(SOURCES)
    results = [fetch_one(row) for row in rows]
    downloaded = len([r for r in results if r["status"] == "downloaded"])
    existing = len([r for r in results if r["status"] == "exists"])
    failed = len([r for r in results if r["status"] == "failed"])
    report = {
        "version": "hsd-wnba-logo-source-fetcher-v1",
        "generated_at_utc": now_iso(),
        "sources": len(rows),
        "downloaded": downloaded,
        "existing": existing,
        "failed": failed,
        "results": results,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Logo Source Fetch Report",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Counts",
        "",
        f"- sources: {report['sources']}",
        f"- downloaded: {downloaded}",
        f"- existing: {existing}",
        f"- failed: {failed}",
        "",
        "## Results",
        "",
    ]
    for item in results:
        suffix = f" - {item['reason']}" if item.get("reason") else ""
        lines.append(f"- {item['team_name']}: {item['status']} -> `{item['target_path']}`{suffix}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": downloaded, "existing": existing, "failed": failed}, indent=2))


if __name__ == "__main__":
    main()
