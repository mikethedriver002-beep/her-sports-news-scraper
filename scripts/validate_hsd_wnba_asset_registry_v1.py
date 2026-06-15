from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("data/asset_registry/wnba")
TEAMS = ROOT / "teams.csv"
ALIASES = ROOT / "team_aliases.csv"
TEAM_LOGOS = ROOT / "team_logos.csv"
MISSING_TEAM_LOGOS = ROOT / "missing_team_logos.csv"
REPORT_MD = ROOT / "asset_registry_validation_report.md"
REPORT_JSON = ROOT / "asset_registry_validation.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> None:
    teams = read_csv(TEAMS)
    aliases = read_csv(ALIASES)
    logos = read_csv(TEAM_LOGOS)
    issues: List[str] = []
    warnings: List[str] = []
    team_ids = {row.get("team_id", "") for row in teams}
    logo_ids = {row.get("team_id", "") for row in logos}
    alias_ids = {row.get("team_id", "") for row in aliases}
    if not teams:
        issues.append("teams.csv is empty or missing")
    if team_ids - logo_ids:
        issues.append("missing logo rows for: " + ", ".join(sorted(team_ids - logo_ids)))
    if alias_ids - team_ids:
        issues.append("aliases reference unknown teams: " + ", ".join(sorted(alias_ids - team_ids)))
    missing_required = []
    for row in logos:
        if row.get("required") == "true" and row.get("file_exists") != "true":
            missing_required.append(row.get("team_id", ""))
        p = Path(row.get("file_path", ""))
        if row.get("file_exists") == "true" and not p.exists():
            issues.append(f"registered logo path does not exist: {p}")
    missing_rows = [{"team_id": tid, "team_name": next((t.get("team_name", tid) for t in teams if t.get("team_id") == tid), tid), "required_asset": "primary_logo", "reason": "required exact team logo file not found", "recommended_path": f"assets/leagues/wnba/teams/{tid}/logo.png"} for tid in missing_required]
    with MISSING_TEAM_LOGOS.open("w", newline="", encoding="utf-8") as f:
        fields = ["team_id", "team_name", "required_asset", "reason", "recommended_path"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(missing_rows)
    status = "pass" if not issues else "fail"
    if missing_required:
        status = "needs_assets"
    result = {
        "version": "hsd-wnba-asset-registry-validator-v1",
        "generated_at_utc": now_iso(),
        "status": status,
        "teams": len(teams),
        "aliases": len(aliases),
        "logo_rows": len(logos),
        "missing_required_team_logos": len(missing_required),
        "issues": issues,
        "warnings": warnings,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = ["# HSD WNBA Asset Registry Validation", "", f"Generated: {result['generated_at_utc']}", f"Status: **{status}**", "", "## Counts", "", f"- teams: {result['teams']}", f"- aliases: {result['aliases']}", f"- logo rows: {result['logo_rows']}", f"- missing required team logos: {result['missing_required_team_logos']}", "", "## Issues", ""]
    lines += [f"- {item}" for item in issues] if issues else ["- None"]
    lines += ["", "## Missing required logos", ""]
    lines += [f"- {row['team_name']} -> `{row['recommended_path']}`" for row in missing_rows] if missing_rows else ["- None"]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
