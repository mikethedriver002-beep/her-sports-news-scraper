from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-review-deck-intake-adapter-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_review_deck_intake_adapter_v1.py"
DEFAULT_DECISIONS_CSV = Path("outputs/local/latest/files/action_photo_review_deck_ui_v1/manual_decision_export_template.csv")
DEFAULT_BOARD_CSV = Path("outputs/local/latest/files/action_photo_next_candidate_board/action_photo_next_candidate_board.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_review_deck_intake_adapter_v1")

FORMAL_INTAKE_NAME = "formal_quarantine_download_intake_candidates.csv"
REJECTED_DECISIONS_NAME = "rejected_or_held_review_deck_decisions.csv"
REPORT_NAME = "action_photo_review_deck_intake_adapter_report.md"
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
    return str(value or "").strip()


def yes_no_false(value: str) -> bool:
    return clean(value).lower() in {"no", "false", ""}


def board_by_candidate_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        candidate_id = clean(row.get("scout_candidate_id") or row.get("candidate_queue_id") or row.get("board_id"))
        if candidate_id:
            lookup[candidate_id] = row
    return lookup


def rights_class_for(row: dict[str, str]) -> str:
    source_type = clean(row.get("source_type")).lower()
    source_domain = clean(row.get("source_domain")).lower()
    if "official" in source_type or "wnba.com" in source_domain or "aces.wnba.com" in source_domain:
        return "official_team_site"
    return "public_source_review_needed"


def identity_anchor_for(entity_id: str) -> str:
    anchors = {
        "wnba_las_vegas_aces_jackie_young": "https://www.wnba.com/player/1629498/jackie-young/profile",
        "wnba_las_vegas_aces_jewell_loyd": "https://www.wnba.com/player/203825/jewell-loyd/profile",
    }
    return anchors.get(entity_id, "")


def quarantine_hint(candidate_id: str, entity_id: str) -> str:
    slug = entity_id.replace("wnba_las_vegas_aces_", "").replace("_", "-")
    safe_id = candidate_id.lower()
    if entity_id.startswith("wnba_las_vegas_aces_"):
        return f"data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/{slug}/{safe_id}_operator_review.jpg"
    return f"data/assets/quarantine/review_only_candidates/action_photo_candidates/review_deck/{safe_id}_operator_review.jpg"


def validate_decision_row(row: dict[str, str]) -> list[str]:
    issues: list[str] = []
    if clean(row.get("review_only")).lower() != "true":
        issues.append("review_only_must_be_true")
    if clean(row.get("download_approved")).lower() not in {"", "no"}:
        issues.append("exported_decision_must_not_download_approve")
    if clean(row.get("asset_downloads")).lower() not in {"", "false"}:
        issues.append("asset_downloads_must_be_false")
    if clean(row.get("approval_state_change")).lower() not in {"", "false"}:
        issues.append("approval_state_change_must_be_false")
    if clean(row.get("publish_ready")).lower() not in {"", "false"}:
        issues.append("publish_ready_must_be_false")
    if clean(row.get("publishing")).lower() not in {"", "false"}:
        issues.append("publishing_must_be_false")
    return issues


def formal_intake_rows(decisions: list[dict[str, str]], board_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    lookup = board_by_candidate_id(board_rows)
    formal: list[dict[str, str]] = []
    rejected_or_held: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []

    for row in decisions:
        issues = validate_decision_row(row)
        decision = clean(row.get("operator_decision"))
        item_kind = clean(row.get("item_kind"))
        candidate_id = clean(row.get("candidate_id"))
        entity_id = clean(row.get("entity_id"))
        if issues:
            invalid.append({**row, "validation_issues": "|".join(issues)})
            continue
        if decision != CARRY_FORWARD or item_kind != "candidate_source":
            if decision:
                rejected_or_held.append({field: row.get(field, "") for field in REJECTED_FIELDS})
            continue

        source = lookup.get(candidate_id, {})
        candidate_photo_url = clean(row.get("image_or_render_url") or source.get("candidate_image_url"))
        source_url = clean(row.get("source_url") or source.get("source_url"))
        identity_confidence = clean(source.get("identity_confidence") or "operator_selected")
        evidence_summary = clean(source.get("image_alt") or source.get("candidate_board_recommendation") or "Review deck carry-forward candidate.")
        if not candidate_id or not candidate_photo_url or not source_url or not entity_id:
            invalid.append({**row, "validation_issues": "missing_candidate_photo_source_or_entity"})
            continue

        formal.append(
            {
                "candidate_queue_id": candidate_id,
                "candidate_photo_url": candidate_photo_url,
                "evidence_url": source_url,
                "evidence_summary": f"Review deck carry-forward only. {evidence_summary}",
                "identity_anchor_url": identity_anchor_for(entity_id),
                "source_url": source_url,
                "entity_id": entity_id,
                "rights_class": rights_class_for(source),
                "identity_confidence": identity_confidence,
                "intended_review_only_use": "review_only_renderer_social_visual_testing",
                "notes": (
                    f"{clean(row.get('operator_notes'))}; "
                    if clean(row.get("operator_notes"))
                    else ""
                )
                + "Carry-forward from review deck; separate human download approval still required.",
                "operator_verify_required": "yes",
                "manual_reviewer": clean(row.get("manual_reviewer")),
                "manual_review_status": "carried_forward_pending_formal_download_approval",
                "manual_next_action": "If still desired, human must make a separate affirmative download decision before any guarded quarantine-only download.",
                "download_approved": "no",
                "quarantine_target_hint": quarantine_hint(candidate_id, entity_id),
                "review_only": "true",
                "publish_ready": "false",
            }
        )
    return formal, rejected_or_held, invalid


def build_report(manifest: dict[str, Any]) -> str:
    return f"""# Action Photo Review Deck Intake Adapter V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet converts exported review-deck decisions into a guarded formal-intake candidate surface. It does not approve downloads, download assets, approve assets, move assets, mark anything publish-ready, or publish.

## Outputs

- Formal intake candidates: `{manifest['formal_intake_path']}`
- Rejected/held decisions: `{manifest['rejected_decisions_path']}`
- Manifest: `{manifest['manifest_path']}`

## Counts

- Decision rows read: `{manifest['decision_rows_read']}`
- Carry-forward intake rows written: `{manifest['formal_intake_rows']}`
- Rejected/held rows written: `{manifest['rejected_or_held_rows']}`
- Invalid rows blocked: `{manifest['invalid_rows']}`

## Guardrails

- generated formal rows keep `download_approved=no`
- review_only=true
- asset_downloads=false
- approval_state_change=false
- publish_ready=false
- publishing=false
"""


def build_packet(*, decisions_csv: Path, board_csv: Path, output_dir: Path, head_commit: str = "") -> dict[str, Any]:
    decisions_csv = decisions_csv.resolve(strict=False)
    board_csv = board_csv.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    decisions = read_csv_rows(decisions_csv)
    board_rows = read_csv_rows(board_csv)
    formal, rejected_or_held, invalid = formal_intake_rows(decisions, board_rows)

    formal_path = write_csv(output_dir / FORMAL_INTAKE_NAME, formal, FORMAL_FIELDS)
    rejected_path = write_csv(output_dir / REJECTED_DECISIONS_NAME, rejected_or_held, REJECTED_FIELDS)
    invalid_path = write_csv(
        output_dir / "invalid_review_deck_decisions.csv",
        invalid,
        list(decisions[0].keys()) + ["validation_issues"] if decisions else ["validation_issues"],
    )
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_review_deck_intake_adapter_ready",
        "repo_head": head_commit,
        "decisions_csv": decisions_csv.as_posix(),
        "board_csv": board_csv.as_posix(),
        "output_dir": output_dir.as_posix(),
        "formal_intake_path": formal_path.as_posix(),
        "rejected_decisions_path": rejected_path.as_posix(),
        "invalid_decisions_path": invalid_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "decision_rows_read": len(decisions),
        "formal_intake_rows": len(formal),
        "rejected_or_held_rows": len(rejected_or_held),
        "invalid_rows": len(invalid),
        "formal_fields": FORMAL_FIELDS,
        "review_only": True,
        "download_approved_default": "no",
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert review-deck decisions into guarded formal-intake candidate rows.")
    parser.add_argument("--decisions-csv", default=DEFAULT_DECISIONS_CSV.as_posix())
    parser.add_argument("--board-csv", default=DEFAULT_BOARD_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        decisions_csv=resolve_path(args.decisions_csv),
        board_csv=resolve_path(args.board_csv),
        output_dir=resolve_output_dir(args.output_dir or None),
        head_commit=args.head_commit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "formal_intake_rows": manifest["formal_intake_rows"],
                "invalid_rows": manifest["invalid_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
