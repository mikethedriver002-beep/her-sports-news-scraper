from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, write_csv as write_run_csv, write_json, write_text

MISSING_TEAM_LOGOS = "data/asset_registry/wnba/missing_team_logos.csv"
VALIDATION_JSON = "data/asset_registry/wnba/asset_registry_validation.json"
GAPS_MD = "data/asset_registry/wnba/asset_gap_report.md"
GAPS_JSON = "data/asset_registry/wnba/asset_gap_report.json"
UPLOAD_CSV = "data/asset_registry/wnba/logo_gap_upload_manifest.csv"
UPLOAD_FIELDS = [
    "team_id",
    "team_name",
    "required_filename",
    "target_folder",
    "target_path",
    "upload_status",
    "decision_packet_id",
    "decision_packet_title",
    "decision_review_status",
    "allowed_decisions",
    "decision_primary_action",
    "decision_hold_cue",
    "decision_revise_cue",
    "renderer_fallback_cue",
    "decision_source_artifact",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_upload_manifest(missing: List[Dict[str, str]]) -> Path:
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
            "decision_packet_id": row.get("decision_packet_id", ""),
            "decision_packet_title": row.get("decision_packet_title", ""),
            "decision_review_status": row.get("decision_review_status", "operator_asset_decision_required"),
            "allowed_decisions": row.get("allowed_decisions", "supply_exact_logo_for_review|hold_logo_slot|revise_registry_metadata"),
            "decision_primary_action": row.get("decision_primary_action", "Supply the exact local team logo file, then manually review source evidence before renderer trust."),
            "decision_hold_cue": row.get("decision_hold_cue", "Hold the card if an exact local logo is missing, unverified, or not source-backed."),
            "decision_revise_cue": row.get("decision_revise_cue", "Revise registry metadata only after human evidence review."),
            "renderer_fallback_cue": row.get("renderer_fallback_cue", "Renderer fallback remains review-only until this missing exact logo is resolved."),
            "decision_source_artifact": row.get("decision_source_artifact", MISSING_TEAM_LOGOS),
            "publish_ready": row.get("publish_ready", "false"),
            "auto_approval": row.get("auto_approval", "false"),
            "auto_publish": row.get("auto_publish", "false"),
            "move_files": row.get("move_files", "false"),
            "paid_apis": row.get("paid_apis", "false"),
        })
    return write_run_csv(UPLOAD_CSV, rows, UPLOAD_FIELDS)


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
    validation_json = input_path(VALIDATION_JSON)
    if validation_json.exists():
        try:
            validation = json.loads(validation_json.read_text(encoding="utf-8"))
        except Exception:
            validation = {}
    upload_csv = write_upload_manifest(missing)
    operator_warnings = validation.get("operator_warnings") or []
    source_path_warnings = validation.get("source_path_metadata_warnings") or []
    report = {
        "version": "hsd-wnba-asset-gap-report-v1.1-logo-upload-pack",
        "generated_at_utc": now_iso(),
        "missing_team_logos": len(missing),
        "validation_status": validation.get("status", "unknown"),
        "operator_warnings": len(operator_warnings),
        "source_path_metadata_warnings": len(source_path_warnings),
        "logo_upload_manifest": upload_csv.as_posix(),
        "decision_packet_fields": UPLOAD_FIELDS,
        "decision_packet_count": len(missing),
        "next_action": next_action(missing, validation),
        "policy": {
            "review_only": True,
            "no_paid_apis": True,
            "no_asset_downloads": True,
            "no_auto_approval": True,
            "no_file_movement_into_publish_ready_lanes": True,
            "no_publishing": True,
        },
    }
    write_json(GAPS_JSON, report)
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
            lines.append(
                f"- `{target}` | packet `{row.get('decision_packet_id', '')}` | "
                f"decision `{row.get('decision_review_status', 'operator_asset_decision_required')}`"
            )
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
    lines += ["", "## Decision tab packet fields", ""]
    if missing:
        for row in missing:
            lines.append(
                f"- {row.get('decision_packet_title') or row.get('team_name')}: "
                f"{row.get('decision_primary_action') or 'manual review required'} "
                f"Fallback cue: {row.get('renderer_fallback_cue') or 'review-only hold'}"
            )
    else:
        lines.append("- None")
    write_text(GAPS_MD, "\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
