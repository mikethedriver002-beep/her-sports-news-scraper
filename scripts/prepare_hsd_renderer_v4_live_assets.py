from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "v1.0-phase6g-live-asset-preparation"
TEAM_LOGOS = Path("data/asset_registry/wnba/team_logos.csv")
TEAMS = Path("data/asset_registry/wnba/teams.csv")
REPORT_JSON = Path("live_asset_preparation_v4_report.json")
REPORT_MD = Path("live_asset_preparation_v4_report.md")


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def run_script(path: str) -> Dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, path],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "script": path,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-3000:],
        "stderr_tail": completed.stderr[-3000:],
    }


def build_report(root: Path) -> Dict[str, Any]:
    original = Path.cwd()
    try:
        import os
        os.chdir(root)
        runs = [
            run_script("scripts/fetch_hsd_wnba_logo_sources_v1.py"),
            run_script("scripts/build_hsd_wnba_asset_registry_v1.py"),
        ]
        active_teams = {
            clean(row.get("team_id"))
            for row in read_csv(TEAMS)
            if clean(row.get("team_id")) and clean(row.get("active")).lower() in {"true", "1", "yes"}
        }
        rows = read_csv(TEAM_LOGOS)
        verified: List[str] = []
        missing: List[str] = []
        details: List[Dict[str, Any]] = []
        by_team = {clean(row.get("team_id")): row for row in rows if clean(row.get("team_id"))}
        for team_id in sorted(active_teams):
            row = by_team.get(team_id, {})
            path = Path(clean(row.get("file_path"))) if clean(row.get("file_path")) else Path("__missing__")
            approved = clean(row.get("approved")).lower() in {"true", "1", "yes"}
            exists = path.exists() and path.is_file() and path.stat().st_size > 100
            ok = approved and exists
            (verified if ok else missing).append(team_id)
            details.append({
                "team_id": team_id,
                "file_path": clean(row.get("file_path")),
                "approved": approved,
                "exists": exists,
                "bytes": path.stat().st_size if exists else 0,
                "status": "verified_exact_logo" if ok else "missing_or_unapproved_logo",
            })
        report = {
            "version": VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "passed_live_asset_preparation" if verified else "blocked_live_asset_preparation",
            "strict_exit_code": 0 if verified else 2,
            "active_team_count": len(active_teams),
            "verified_logo_count": len(verified),
            "missing_logo_count": len(missing),
            "verified_team_ids": verified,
            "missing_team_ids": missing,
            "all_active_logos_ready": bool(active_teams and not missing),
            "network_fetch_runs": runs,
            "rows": details,
            "free_only": True,
            "notes": "Missing unrelated teams are reported. The live post-ready gate separately requires exact logos for every team used in each candidate render.",
        }
        return report
    finally:
        import os
        os.chdir(original)


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# HSD Phase 6G Live Asset Preparation",
        "",
        f"Status: `{report['status']}`",
        f"Active teams: `{report['active_team_count']}`",
        f"Verified exact logos: `{report['verified_logo_count']}`",
        f"Missing/unapproved logos: `{report['missing_logo_count']}`",
        f"All active logos ready: `{report['all_active_logos_ready']}`",
        "",
        "## Missing teams",
        "",
    ]
    lines += [f"- `{team_id}`" for team_id in report["missing_team_ids"]] or ["- None"]
    lines += [
        "",
        "## Policy",
        "",
        "- Free public logo sources only.",
        "- The live gate requires approved exact logos for the teams actually used in a render.",
        "- Missing logos remain review-only and cannot enter the live post-ready lane.",
    ]
    (root / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare free exact WNBA assets for Renderer v4 live runs.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root)
    write_report(root, report)
    print(json.dumps({
        "version": VERSION,
        "status": report["status"],
        "verified_logo_count": report["verified_logo_count"],
        "missing_logo_count": report["missing_logo_count"],
        "all_active_logos_ready": report["all_active_logos_ready"],
    }, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
