from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-manual-decision-batch-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_manual_decision_batch_v1.py"
DEFAULT_DECISION_GLOB = "D:/HSD Testing/hsd_action_photo_review_deck_manual_decisions*.csv"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_manual_decision_batch_v1")

FORMAL_INTAKE_NAME = "formal_quarantine_download_intake_candidates.csv"
REJECTED_DECISIONS_NAME = "rejected_or_held_review_deck_decisions.csv"
NORMALIZED_DECISIONS_NAME = "normalized_review_deck_decisions.csv"
REPORT_NAME = "action_photo_manual_decision_batch_report.md"
MANIFEST_NAME = "manifest.json"

FORMAL_FIELDS = [
    "candidate_queue_id",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "notes",
    "operator_verify_required",
    "manual_reviewer",
    "manual_review_status",
    "manual_next_action",
    "download_approved",
    "quarantine_target_hint",
    "review_only",
    "publish_ready",
]

REJECTED_FIELDS = [
    "deck_item_id",
    "item_kind",
    "candidate_id",
    "entity_id",
    "operator_decision",
    "operator_notes",
    "manual_reviewer",
    "reviewed_at_utc",
    "source_url",
    "image_or_render_url",
    "review_only",
    "download_approved",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

NORMALIZED_FIELDS = [
    "source_decisions_csv",
    *REJECTED_FIELDS,
    "formal_intake_next_action",
]

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "headshot_writes": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
}

CARRY_FORWARD = "carry_forward_for_formal_intake"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def clean(value: Any) -> str:
    return str(value or "").strip()


def lower(value: Any) -> str:
    return clean(value).lower()


def truthy(value: Any) -> bool:
    return lower(value) in {"1", "true", "yes", "y"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def resolve_decision_paths(explicit: list[str], decision_glob: str) -> list[Path]:
    raw_paths = explicit or sorted(glob.glob(decision_glob))
    paths: list[Path] = []
    seen: set[str] = set()
    for raw in raw_paths:
        path = Path(raw)
        key = str(path.resolve(strict=False)).lower()
        if key not in seen:
            paths.append(path)
            seen.add(key)
    return paths


def normalize_row(row: dict[str, str], source_path: Path) -> dict[str, str]:
    normalized = {
        "source_decisions_csv": source_path.as_posix(),
        "deck_item_id": clean(row.get("deck_item_id")),
        "item_kind": clean(row.get("item_kind") or "candidate_source"),
        "candidate_id": clean(row.get("candidate_id") or row.get("scout_candidate_id")),
        "entity_id": clean(row.get("entity_id")),
        "operator_decision": clean(row.get("operator_decision") or row.get("decision")),
        "operator_notes": clean(row.get("operator_notes") or row.get("notes")),
        "manual_reviewer": clean(row.get("manual_reviewer")),
        "reviewed_at_utc": clean(row.get("reviewed_at_utc")),
        "source_url": clean(row.get("source_url") or row.get("evidence_url")),
        "image_or_render_url": clean(row.get("image_or_render_url") or row.get("candidate_image_url") or row.get("candidate_photo_url")),
        "review_only": "true",
        "download_approved": "no",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
        "formal_intake_next_action": clean(row.get("formal_intake_next_action")),
    }
    if not normalized["deck_item_id"] and normalized["candidate_id"]:
        normalized["deck_item_id"] = f"candidate_{normalized['candidate_id']}"
    return normalized


def decision_group_key(row: dict[str, str]) -> tuple[str, str]:
    return (
        lower(row.get("candidate_id")),
        lower(row.get("entity_id")),
    )


def source_rights_class(source_url: str) -> str:
    host = urlparse(source_url).netloc.lower()
    if not host:
        return "public_source_review_needed"
    if any(token in host for token in ("wnba.com", "thepwhl.com", "premierlacrosseleague.com", "auprosports.com", "wtatennis.com", "lpga.com", "lovb.com", "mlv.com", "unrivaled.basketball")):
        return "official_source_review_needed"
    return "public_source_review_needed"


def quarantine_hint(candidate_id: str, entity_id: str) -> str:
    safe_id = clean(candidate_id).lower() or "manual_decision_candidate"
    safe_entity = clean(entity_id).lower().replace(" ", "_") or "unknown_entity"
    return f"data/assets/quarantine/review_only_candidates/action_photo_candidates/manual_decision_batch/{safe_entity}/{safe_id}_operator_review.jpg"


def formal_row(row: dict[str, str]) -> dict[str, str]:
    notes = clean(row.get("operator_notes"))
    if notes:
        notes += "; "
    notes += "Carry-forward from manual review deck export; separate human download approval is still required."
    return {
        "candidate_queue_id": clean(row.get("candidate_id")),
        "candidate_photo_url": clean(row.get("image_or_render_url")),
        "evidence_url": clean(row.get("source_url")),
        "evidence_summary": "Manual carry-forward from review deck export. Identity and crop still require guarded formal intake review.",
        "identity_anchor_url": "",
        "source_url": clean(row.get("source_url")),
        "entity_id": clean(row.get("entity_id")),
        "rights_class": source_rights_class(clean(row.get("source_url"))),
        "identity_confidence": "operator_selected",
        "intended_review_only_use": "review_only_renderer_social_visual_testing",
        "notes": notes,
        "operator_verify_required": "yes",
        "manual_reviewer": clean(row.get("manual_reviewer")),
        "manual_review_status": "carried_forward_pending_formal_download_approval",
        "manual_next_action": "Human must make a separate affirmative download_approved=yes formal intake decision before any guarded quarantine-only download.",
        "download_approved": "no",
        "quarantine_target_hint": quarantine_hint(clean(row.get("candidate_id")), clean(row.get("entity_id"))),
        "review_only": "true",
        "publish_ready": "false",
    }


def invalid_guardrail(row: dict[str, str]) -> str:
    if truthy(row.get("download_approved")):
        return "download_approved_truthy_blocked"
    if truthy(row.get("asset_downloads")):
        return "asset_downloads_truthy_blocked"
    if truthy(row.get("approval_state_change")):
        return "approval_state_change_truthy_blocked"
    if truthy(row.get("publish_ready")):
        return "publish_ready_truthy_blocked"
    if truthy(row.get("publishing")):
        return "publishing_truthy_blocked"
    return ""


def build_report(manifest: dict[str, Any]) -> str:
    return f"""# Action Photo Manual Decision Batch V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet normalizes exported review-deck decisions into a durable review-only signal for the source-quality ranker. It does not approve downloads, download assets, approve assets, move assets, mark anything publish-ready, or publish.

## Outputs

- Normalized decisions: `{manifest['normalized_decisions_path']}`
- Formal carry-forward candidates: `{manifest['formal_intake_path']}`
- Rejected/held decisions for ranker suppression: `{manifest['rejected_decisions_path']}`
- Manifest: `{manifest['manifest_path']}`

## Counts

- Decision files read: `{manifest['decision_files_read']}`
- Raw decision rows read: `{manifest['raw_decision_rows_read']}`
- Latest decision rows: `{manifest['latest_decision_rows']}`
- Superseded older rows collapsed: `{manifest['superseded_decision_rows']}`
- Normalized valid rows: `{manifest['normalized_decision_rows']}`
- Carry-forward rows: `{manifest['formal_intake_rows']}`
- Rejected rows: `{manifest['reject_rows']}`
- Held rows: `{manifest['hold_rows']}`
- Invalid rows blocked: `{manifest['invalid_rows']}`

## Guardrails

- generated formal rows keep `download_approved=no`
- `review_only=true`
- `asset_downloads=false`
- `approval_state_change=false`
- `publish_ready=false`
- `publishing=false`
"""


def build_packet(*, decision_paths: list[Path], output_dir: Path, head_commit: str = "") -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    staged: list[tuple[dict[str, str], Path, int, int]] = []
    invalid: list[dict[str, str]] = []
    raw_count = 0
    for source_index, path in enumerate(decision_paths):
        rows = read_csv_rows(path)
        raw_count += len(rows)
        for row_index, source_row in enumerate(rows):
            source_path = path.resolve(strict=False)
            candidate_id = clean(source_row.get("candidate_id") or source_row.get("scout_candidate_id"))
            entity_id = clean(source_row.get("entity_id"))
            operator_decision = clean(source_row.get("operator_decision") or source_row.get("decision"))
            if not candidate_id or not entity_id or not operator_decision:
                row = normalize_row(source_row, source_path)
                invalid.append({**row, "validation_issues": "missing_candidate_entity_or_decision"})
                continue
            staged.append((source_row, source_path, source_index, row_index))

    latest_by_key: dict[tuple[str, str], tuple[dict[str, str], Path, int, int]] = {}
    for staged_row in staged:
        source_row, source_path, source_index, row_index = staged_row
        key = decision_group_key(source_row)
        existing = latest_by_key.get(key)
        if not existing:
            latest_by_key[key] = staged_row
            continue
        if (existing[2], existing[3]) <= (source_index, row_index):
            latest_by_key[key] = staged_row

    latest_rows = sorted(latest_by_key.values(), key=lambda row: (row[2], row[3]))
    normalized: list[dict[str, str]] = []

    formal: list[dict[str, str]] = []
    rejected_or_held: list[dict[str, str]] = []
    for source_row, source_path, _, _ in latest_rows:
        row = normalize_row(source_row, source_path)
        decision = lower(row.get("operator_decision"))
        issue = invalid_guardrail(source_row)
        if issue:
            invalid.append({**row, "validation_issues": issue})
            continue
        if decision == CARRY_FORWARD:
            if row["source_url"] and row["image_or_render_url"]:
                formal.append(formal_row(row))
                normalized.append(row)
            else:
                invalid.append({**row, "validation_issues": "carry_forward_missing_source_or_image_url"})
            continue
        normalized.append(row)
        rejected_or_held.append({field: row.get(field, "") for field in REJECTED_FIELDS})

    normalized_path = write_csv(output_dir / NORMALIZED_DECISIONS_NAME, normalized, NORMALIZED_FIELDS)
    formal_path = write_csv(output_dir / FORMAL_INTAKE_NAME, formal, FORMAL_FIELDS)
    rejected_path = write_csv(output_dir / REJECTED_DECISIONS_NAME, rejected_or_held, REJECTED_FIELDS)
    invalid_path = write_csv(output_dir / "invalid_review_deck_decisions.csv", invalid, NORMALIZED_FIELDS + ["validation_issues"])
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME

    reject_count = sum(1 for row in rejected_or_held if lower(row.get("operator_decision")).startswith("reject"))
    hold_count = sum(1 for row in rejected_or_held if lower(row.get("operator_decision")).startswith("hold"))
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_manual_decision_batch_ready",
        "repo_head": head_commit,
        "decision_paths": [path.resolve(strict=False).as_posix() for path in decision_paths],
        "output_dir": output_dir.as_posix(),
        "normalized_decisions_path": normalized_path.as_posix(),
        "formal_intake_path": formal_path.as_posix(),
        "rejected_decisions_path": rejected_path.as_posix(),
        "invalid_decisions_path": invalid_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "decision_files_read": len(decision_paths),
        "raw_decision_rows_read": raw_count,
        "latest_decision_rows": len(latest_rows),
        "superseded_decision_rows": max(0, len(staged) - len(latest_rows)),
        "normalized_decision_rows": len(normalized),
        "formal_intake_rows": len(formal),
        "rejected_or_held_rows": len(rejected_or_held),
        "reject_rows": reject_count,
        "hold_rows": hold_count,
        "invalid_rows": len(invalid),
        "download_approved_default": "no",
        "review_only": True,
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize exported review deck decision CSVs into ranker/adaptor signal.")
    parser.add_argument("--decisions-csv", action="append", default=[], help="Decision CSV path. Repeatable.")
    parser.add_argument("--decision-glob", default=DEFAULT_DECISION_GLOB)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = resolve_decision_paths(args.decisions_csv, args.decision_glob)
    manifest = build_packet(
        decision_paths=paths,
        output_dir=resolve_output_dir(args.output_dir or None),
        head_commit=args.head_commit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "decision_files_read": manifest["decision_files_read"],
                "latest_decision_rows": manifest["latest_decision_rows"],
                "formal_intake_rows": manifest["formal_intake_rows"],
                "reject_rows": manifest["reject_rows"],
                "hold_rows": manifest["hold_rows"],
                "invalid_rows": manifest["invalid_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
