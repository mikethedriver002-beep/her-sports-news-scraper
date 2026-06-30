from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, read_csv, write_csv, write_json, write_text
from scripts.generate_hsd_action_photo_candidate_intake_v1 import (
    ACTION_PHOTO_QUARANTINE_PREFLIGHT_FIELDS,
    REQUIRED_DOWNLOAD_FIELDS,
    action_photo_quarantine_preflight_rows,
    clean,
    render_action_photo_quarantine_preflight,
    validate_action_photo_quarantine_preflight_rows,
)


VERSION = "hsd-action-photo-quarantine-preflight-v1-review-only"
GENERATED_AT_UTC = "2026-06-30T00:00:00+00:00"
ROOT = Path("data/asset_registry/action_photo_candidates")
IN_RESEARCH_RETURN_INTAKE_CSV = ROOT / "review_only_action_photo_research_return_intake_v1.csv"
OUT_QUARANTINE_PREFLIGHT_CSV = ROOT / "review_only_action_photo_quarantine_preflight_v1.csv"
OUT_QUARANTINE_PREFLIGHT_MD = ROOT / "review_only_action_photo_quarantine_preflight_v1.md"
OUT_QUARANTINE_PREFLIGHT_JSON = ROOT / "review_only_action_photo_quarantine_preflight_v1.json"


def missing_required_field_counts(rows: List[Mapping[str, str]]) -> Dict[str, int]:
    fields = REQUIRED_DOWNLOAD_FIELDS + ["candidate_photo_url", "evidence_url", "identity_anchor_url"]
    return {
        field: sum(1 for row in rows if field in clean(row.get("missing_required_fields")).split("|"))
        for field in fields
    }


def action_photo_status_counts(rows: List[Mapping[str, str]]) -> Dict[str, int]:
    statuses = sorted({clean(row.get("action_photo_status")) for row in rows if clean(row.get("action_photo_status"))})
    return {status: sum(1 for row in rows if clean(row.get("action_photo_status")) == status) for status in statuses}


def identity_confidence_status_counts(rows: List[Mapping[str, str]]) -> Dict[str, int]:
    statuses = sorted({clean(row.get("identity_confidence_status")) for row in rows if clean(row.get("identity_confidence_status"))})
    return {status: sum(1 for row in rows if clean(row.get("identity_confidence_status")) == status) for status in statuses}


def manifest(return_rows: List[Mapping[str, str]], preflight_rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> Dict[str, object]:
    return {
        "version": VERSION,
        "status": "action_photo_quarantine_preflight_ready" if not issues else "action_photo_quarantine_preflight_has_validation_issues",
        "generated_at_utc": GENERATED_AT_UTC,
        "source_intake_csv": IN_RESEARCH_RETURN_INTAKE_CSV.as_posix(),
        "resolved_source_intake_csv": input_path(IN_RESEARCH_RETURN_INTAKE_CSV).as_posix(),
        "preflight_rows": len(preflight_rows),
        "return_intake_rows": len(return_rows),
        "ready_for_human_download_decision_rows": sum(
            1 for row in preflight_rows if clean(row.get("ready_for_human_download_decision")) == "yes"
        ),
        "lead_only_rows": sum(1 for row in preflight_rows if clean(row.get("lead_status")) == "lead_only_research_return_missing"),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "candidate_queue_ids": sorted({clean(row.get("candidate_queue_id")) for row in preflight_rows if clean(row.get("candidate_queue_id"))}),
        "missing_required_field_counts": missing_required_field_counts(preflight_rows),
        "action_photo_status_counts": action_photo_status_counts(preflight_rows),
        "identity_confidence_status_counts": identity_confidence_status_counts(preflight_rows),
        "download_approved_yes_rows": sum(1 for row in preflight_rows if clean(row.get("download_approved")) == "yes"),
        "human_intake_download_approved_yes_rows": sum(1 for row in return_rows if clean(row.get("download_approved")) == "yes"),
        "generated_download_approved_yes_rows": sum(1 for row in preflight_rows if clean(row.get("download_approved")) == "yes"),
        "review_only_rows": sum(1 for row in preflight_rows if clean(row.get("review_only")) == "true"),
        "publish_ready_rows": sum(1 for row in preflight_rows if clean(row.get("publish_ready")) == "true"),
        "review_only": True,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "approval_state_change": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "worksheet_csv": OUT_QUARANTINE_PREFLIGHT_CSV.as_posix(),
        "worksheet_md": OUT_QUARANTINE_PREFLIGHT_MD.as_posix(),
        "worksheet_json": OUT_QUARANTINE_PREFLIGHT_JSON.as_posix(),
        "preflight_rows_detail": preflight_rows,
    }


def main() -> int:
    return_rows = read_csv(IN_RESEARCH_RETURN_INTAKE_CSV)
    preflight_rows = action_photo_quarantine_preflight_rows(return_rows)
    issues = validate_action_photo_quarantine_preflight_rows(preflight_rows, return_rows)
    write_csv(OUT_QUARANTINE_PREFLIGHT_CSV, preflight_rows, ACTION_PHOTO_QUARANTINE_PREFLIGHT_FIELDS)
    write_text(OUT_QUARANTINE_PREFLIGHT_MD, render_action_photo_quarantine_preflight(preflight_rows, issues, GENERATED_AT_UTC, return_rows))
    write_json(OUT_QUARANTINE_PREFLIGHT_JSON, manifest(return_rows, preflight_rows, issues))
    print(json.dumps({"version": VERSION, "status": "ok", "preflight_rows": len(preflight_rows), "validation_issue_count": len(issues)}, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
