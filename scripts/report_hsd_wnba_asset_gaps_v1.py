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
UPLOAD_CSV = ROOT / "logo_gap_upload_manifest.csv"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_upload_manifest(missing: List[Dict[str, str]]) -> None:
    fields = ["team_id", "team_name", "required_filename", "target_folder", "target_path", "upload_status"]
    rows = []
    for row in missing:
        target = row.get("recommended_path", "")
        folder = str(Path(target).parent) if target else ""
        rows.append({
            "team_id": row.get("team_id", ""),
            "team_name": row.get("team_name", ""),
            "required_filename": "logo.png",
            "target_folder": folder,
            "target_path": target,
            "upload_status": "needed",
        })
    with UPLOAD_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def next_action(missing: List[Dict[str, str]], validation: Dict[str, object]) -> str:
    operator_warnings = validation.get("operator_warnings") or []
    source_path_warnings = validation.get("source_path_metadata_warnings") or []
    if missing:
        return "upload each exact primary team logo as logo.png into its recommended folder path"
    if operator_warnings:
        return "review unapproved local logos and source evidence before any manual approval"
    if source_path_warnings:
        return "review source/path metadata warnings and confirm registry paths remain intentional"
    return "no missing WNBA team logo uploads required"


def main() -> None:
    missing = read_csv(MISSING_TEAM_LOGOS)
    validation = {}
    if VALIDATION_JSON.exists():
        try:
            validation = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
        except Exception:
            validation = {}
    write_upload_manifest(missing)
    operator_warnings = validation.get("operator_warnings") or []
    source_path_warnings = validation.get("source_path_metadata_warnings") or []
    report = {
        "version": "hsd-wnba-asset-gap-report-v1.1-logo-upload-pack",
        "generated_at_utc": now_iso(),
        "missing_team_logos": len(missing),
        "validation_status": validation.get("status", "unknown"),
        "operator_warnings": len(operator_warnings),
        "source_path_metadata_warnings": len(source_path_warnings),
        "logo_upload_manifest": UPLOAD_CSV.as_posix(),
        "next_action": next_action(missing, validation),
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
    lines += [
        "",
        "## Logo Gap Upload Pack",
        "",
        "Upload each missing logo as `logo.png` to the exact folder below. Do not rename the file differently. Do not use text-only fallback. Do not substitute another team logo.",
        "",
    ]
    if missing:
        for row in missing:
            target = row.get("recommended_path", "")
            lines.append(f"- `{target}`")
    else:
        lines.append("- None")
    lines += ["", "## Operator warnings", ""]
    if operator_warnings:
        for item in operator_warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines += ["", "## Source/path metadata warnings", ""]
    if source_path_warnings:
        for item in source_path_warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines += ["", "## Next action", "", f"- {report['next_action']}"]
    GAPS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
