from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json
from scripts.build_hsd_action_photo_remote_visual_triage_v1 import (
    build_packet as build_remote_triage_packet,
)


VERSION = "hsd-action-photo-recovered-decision-visual-triage-v1-review-only"
DEFAULT_FORMAL_INTAKE_CSV = Path(
    "outputs/local/tmp/action_photo_review_deck_recovered_decisions/intake_adapter/formal_quarantine_download_intake_candidates.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_recovered_decision_visual_triage_v1")

REMOTE_TRIAGE_INPUT_FIELDS = [
    "scout_candidate_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "credit_byline",
    "fetch_status",
    "manual_review_status",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "source_provenance_clarity",
    "download_approved",
    "review_only",
    "publish_ready",
    "asset_downloads",
    "approval_state_change",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Missing recovered formal intake CSV: {resolved}")
    with resolved.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def remote_input_rows(formal_rows: list[Mapping[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in formal_rows:
        if clean(row.get("download_approved")).lower() not in {"", "no"}:
            raise ValueError("Recovered visual triage input must not contain download_approved=yes rows")
        candidate_id = clean(row.get("candidate_queue_id"))
        candidate_image_url = clean(row.get("candidate_photo_url"))
        source_url = clean(row.get("source_url") or row.get("evidence_url"))
        entity_id = clean(row.get("entity_id"))
        if not candidate_id or not candidate_image_url or not source_url or not entity_id:
            continue
        rows.append(
            {
                "scout_candidate_id": candidate_id,
                "entity_id": entity_id,
                "source_type": clean(row.get("rights_class") or "official_source_review_needed"),
                "source_url": source_url,
                "candidate_image_url": candidate_image_url,
                "image_alt": clean(row.get("evidence_summary") or "Recovered carry-forward candidate for visual triage."),
                "credit_byline": "",
                "fetch_status": "candidate_metadata_extracted",
                "manual_review_status": clean(row.get("manual_review_status") or "carried_forward_pending_visual_triage"),
                "face_likely_visible": "possible",
                "body_margin_likely": "possible",
                "four_by_five_crop_potential": "possible",
                "text_safe_negative_space": "possible",
                "source_provenance_clarity": "clear",
                "download_approved": "no",
                "review_only": "true",
                "publish_ready": "false",
                "asset_downloads": "false",
                "approval_state_change": "false",
            }
        )
    return rows


def build_packet(*, formal_intake_csv: Path, output_dir: Path, limit: int) -> dict[str, object]:
    resolved_formal = input_path(formal_intake_csv)
    out_dir = output_path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    converted_input_path = out_dir / "recovered_carry_forward_remote_visual_triage_input.csv"
    rows = remote_input_rows(read_csv_rows(formal_intake_csv))
    write_csv(converted_input_path, rows, REMOTE_TRIAGE_INPUT_FIELDS)
    manifest = build_remote_triage_packet(input_csv=converted_input_path, output_dir=out_dir, limit=max(1, limit))
    manifest.update(
        {
            "version_wrapper": VERSION,
            "source_formal_intake_csv": resolved_formal.as_posix(),
            "converted_input_csv": converted_input_path.as_posix(),
            "carry_forward_rows": len(rows),
            "download_approved_default": "no",
        }
    )
    write_json(out_dir / "manifest.json", manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a remote visual triage board from recovered review-deck carry-forward decisions."
    )
    parser.add_argument("--formal-intake-csv", default=DEFAULT_FORMAL_INTAKE_CSV.as_posix())
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR.as_posix())
    parser.add_argument("--limit", type=int, default=12)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        formal_intake_csv=Path(args.formal_intake_csv),
        output_dir=Path(args.output_dir),
        limit=args.limit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "carry_forward_rows": manifest["carry_forward_rows"],
                "triage_rows": manifest["triage_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
