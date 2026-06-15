from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path("data/asset_registry/wnba")
MISSING_TEAM_LOGOS = ROOT / "missing_team_logos.csv"
VALIDATION_JSON = ROOT / "asset_registry_validation.json"
GAPS_MD = ROOT / "asset_gap_report.md"
GAPS_JSON = ROOT / "asset_gap_report.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> None:
    missing = read_csv(MISSING_TEAM_LOGOS)
    validation = {}
    if VALIDATION_JSON.exists():
        try:
            validation = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
        except Exception:
            validation = {}
    report = {
        "version": "hsd-wnba-asset-gap-report-v1",
        "generated_at_utc": now_iso(),
        "missing_team_logos": len(missing),
        "validation_status": validation.get("status", "unknown"),
        "next_action": "add exact primary logos for every missing team before team-led WNBA graphics are allowed",
    }
    GAPS_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Asset Gap Report",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Validation status: **{report['validation_status']}**",
        "",
        "## Missing required team logos",
        "",
    ]
    if missing:
        for row in missing:
            lines.append(f"- {row.get('team_name')} -> `{row.get('recommended_path')}`")
    else:
        lines.append("- None")
    lines += ["", "## Next action", "", f"- {report['next_action']}"]
    GAPS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
