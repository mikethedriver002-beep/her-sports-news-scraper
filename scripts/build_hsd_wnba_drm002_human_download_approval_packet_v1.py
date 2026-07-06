from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-wnba-drm002-human-download-approval-packet-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_drm002_human_download_approval_packet_v1.py"
TARGET_CANDIDATE_ID = "DRM002"
DEFAULT_INTAKE_CSV = Path(
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
)
DEFAULT_PREFLIGHT_CSV = Path(
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_drm002_human_download_approval_packet_v1")
DEFAULT_LATEST_OUTPUT_DIR = Path("outputs/local/latest/files/wnba_drm002_human_download_approval_packet_v1")

CHECKLIST_FIELDS = [
    "check_id",
    "candidate_queue_id",
    "field_name",
    "current_value",
    "status",
    "operator_action",
]

REQUIRED_HUMAN_FIELDS = [
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "manual_reviewer",
    "quarantine_target_hint",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def find_row(rows: list[dict[str, str]], *, field: str, value: str) -> dict[str, str]:
    for row in rows:
        if clean(row.get(field)) == value:
            return row
    raise SystemExit(f"{value} not found in {field}")


def checklist_rows(intake_row: dict[str, str], preflight_row: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, field_name in enumerate(REQUIRED_HUMAN_FIELDS, start=1):
        current_value = clean(intake_row.get(field_name))
        rows.append(
            {
                "check_id": f"DRM002CHK{index:03d}",
                "candidate_queue_id": TARGET_CANDIDATE_ID,
                "field_name": field_name,
                "current_value": current_value,
                "status": "filled" if current_value else "missing",
                "operator_action": "verify_current_value_before_any_human_download_approval_edit",
            }
        )
    rows.extend(
        [
            {
                "check_id": "DRM002CHK900",
                "candidate_queue_id": TARGET_CANDIDATE_ID,
                "field_name": "action_photo_status",
                "current_value": clean(preflight_row.get("action_photo_status")),
                "status": "ready" if clean(preflight_row.get("action_photo_status")) == "action_photo_candidate" else "hold",
                "operator_action": "keep_as_game_action_candidate_only",
            },
            {
                "check_id": "DRM002CHK901",
                "candidate_queue_id": TARGET_CANDIDATE_ID,
                "field_name": "ready_for_human_download_decision",
                "current_value": clean(preflight_row.get("ready_for_human_download_decision")),
                "status": "ready" if clean(preflight_row.get("ready_for_human_download_decision")) == "yes" else "hold",
                "operator_action": "human_may_edit_authoritative_intake_row_only_if_quarantine_download_is_truly_next",
            },
            {
                "check_id": "DRM002CHK902",
                "candidate_queue_id": TARGET_CANDIDATE_ID,
                "field_name": "download_approved",
                "current_value": clean(intake_row.get("download_approved")),
                "status": "locked_no" if clean(intake_row.get("download_approved")) == "no" else "unexpected",
                "operator_action": "do_not_change_here_this_packet_is_review_only",
            },
        ]
    )
    return rows


def build_report(intake_row: dict[str, str], preflight_row: dict[str, str], manifest: dict[str, Any]) -> str:
    return f"""# WNBA DRM002 Human Download Approval Packet V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet is a review-only operator handoff for DRM002. It does not download files, change approval state, move assets, mark anything publish-ready, or publish.

## Current State

- Candidate queue id: `{TARGET_CANDIDATE_ID}`
- Action photo status: `{clean(preflight_row.get('action_photo_status'))}`
- Ready for human download decision: `{clean(preflight_row.get('ready_for_human_download_decision'))}`
- Download approved: `{clean(intake_row.get('download_approved'))}`
- Review only: `{clean(intake_row.get('review_only'))}`
- Publish ready: `{clean(intake_row.get('publish_ready'))}`

## Authoritative Row To Edit Later

- Intake CSV: `{manifest['authoritative_intake_csv']}`
- Candidate row status: `{clean(intake_row.get('manual_review_status'))}`
- Manual reviewer: `{clean(intake_row.get('manual_reviewer'))}`

## Blunt Next Step

- DRM002 is fully staged for a later human quarantine-download decision.
- The next human action is a deliberate edit to the authoritative intake row only.
- This packet is not download approval and not asset approval.
"""


def mirror_latest(output_dir: Path, latest_dir: Path) -> None:
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(output_dir, latest_dir)


def build_packet(
    *,
    intake_csv: Path,
    preflight_csv: Path,
    output_dir: Path,
    latest_output_dir: Path | None = None,
    head_commit: str = "",
) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    intake_row = find_row(read_csv_rows(intake_csv), field="candidate_queue_id", value=TARGET_CANDIDATE_ID)
    preflight_row = find_row(read_csv_rows(preflight_csv), field="candidate_queue_id", value=TARGET_CANDIDATE_ID)
    intake_packet_path = write_csv(output_dir / "drm002_authoritative_intake_row_snapshot.csv", [intake_row], list(intake_row.keys()))
    checklist_path = write_csv(output_dir / "drm002_human_download_approval_checklist.csv", checklist_rows(intake_row, preflight_row), CHECKLIST_FIELDS)
    manifest_path = output_dir / "manifest.json"
    report_path = output_dir / "drm002_human_download_approval_report.md"
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_drm002_human_download_approval_packet_ready",
        "repo_head": head_commit,
        "candidate_queue_id": TARGET_CANDIDATE_ID,
        "authoritative_intake_csv": intake_csv.as_posix(),
        "quarantine_preflight_csv": preflight_csv.as_posix(),
        "output_dir": output_dir.as_posix(),
        "intake_snapshot_csv": intake_packet_path.as_posix(),
        "checklist_csv": checklist_path.as_posix(),
        "report_path": report_path.as_posix(),
        "action_photo_status": clean(preflight_row.get("action_photo_status")),
        "ready_for_human_download_decision": clean(preflight_row.get("ready_for_human_download_decision")),
        "download_approved": clean(intake_row.get("download_approved")),
        "review_only": clean(intake_row.get("review_only")),
        "publish_ready": clean(intake_row.get("publish_ready")),
        "asset_downloads": False,
        "approval_state_change": False,
        "publishing": False,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(intake_row, preflight_row, manifest))
    if latest_output_dir:
        mirror_latest(output_dir, latest_output_dir.resolve(strict=False))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only DRM002 human download approval packet.")
    parser.add_argument("--intake-csv", default=DEFAULT_INTAKE_CSV.as_posix())
    parser.add_argument("--preflight-csv", default=DEFAULT_PREFLIGHT_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    parser.add_argument("--no-latest", action="store_true")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    latest = None if args.no_latest else resolve_path(args.latest_output_dir)
    manifest = build_packet(
        intake_csv=resolve_path(args.intake_csv),
        preflight_csv=resolve_path(args.preflight_csv),
        output_dir=resolve_output_dir(args.output_dir or None),
        latest_output_dir=latest,
        head_commit=args.head_commit,
    )
    print(json.dumps({"status": manifest["status"], "checklist_csv": manifest["checklist_csv"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
