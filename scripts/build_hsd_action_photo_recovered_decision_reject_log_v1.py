from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-recovered-decision-reject-log-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_recovered_decision_reject_log_v1.py"
DEFAULT_INPUT_CSV = Path(
    "data/asset_registry/action_photo_candidates/review_only_recovered_decision_visual_triage_rejections_v1.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_recovered_decision_reject_log_v1")

CSV_NAME = "recovered_decision_reject_log.csv"
REPORT_NAME = "recovered_decision_reject_log_report.md"
MANIFEST_NAME = "manifest.json"

OUTPUT_FIELDS = [
    "candidate_id",
    "entity_id",
    "identity_read",
    "image_type",
    "face_visibility",
    "body_margin_4x5",
    "text_overlay_space",
    "visual_strength",
    "decision",
    "reject_category",
    "notes",
    "manual_next_action",
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repo_root() / candidate


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing manual reject CSV: {path}")
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def reject_category(row: Mapping[str, str]) -> str:
    decision = clean(row.get("decision")).lower()
    image_type = clean(row.get("image_type")).lower()
    body_margin = clean(row.get("body_margin_4x5")).lower()
    text_space = clean(row.get("text_overlay_space")).lower()
    if "bad_crop" in decision or body_margin in {"weak", "fails"} or text_space in {"weak", "fails"}:
        return "reject_bad_crop_or_layout_fit"
    if "bad_source" in image_type:
        return "reject_bad_source_asset"
    return "reject_manual_visual_quality"


def validate_row(row: Mapping[str, str]) -> list[str]:
    issues: list[str] = []
    if not clean(row.get("candidate_id")):
        issues.append("missing_candidate_id")
    if not clean(row.get("entity_id")):
        issues.append("missing_entity_id")
    if not clean(row.get("decision")).lower().startswith("reject"):
        issues.append("decision_must_be_reject")
    if clean(row.get("review_only")).lower() != "true":
        issues.append("review_only_must_be_true")
    if clean(row.get("download_approved")).lower() != "no":
        issues.append("download_approved_must_remain_no")
    if clean(row.get("asset_downloads")).lower() != "false":
        issues.append("asset_downloads_must_be_false")
    if clean(row.get("approval_state_change")).lower() not in {"none", "false"}:
        issues.append("approval_state_change_must_be_none_or_false")
    if clean(row.get("publish_ready")).lower() != "false":
        issues.append("publish_ready_must_be_false")
    if clean(row.get("publishing")).lower() != "false":
        issues.append("publishing_must_be_false")
    return issues


def normalized_rows(rows: list[Mapping[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    accepted: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []
    for row in rows:
        issues = validate_row(row)
        if issues:
            invalid.append({**{field: clean(row.get(field)) for field in OUTPUT_FIELDS}, "validation_issues": "|".join(issues)})
            continue
        accepted.append(
            {
                "candidate_id": clean(row.get("candidate_id")),
                "entity_id": clean(row.get("entity_id")),
                "identity_read": clean(row.get("identity_read")),
                "image_type": clean(row.get("image_type")),
                "face_visibility": clean(row.get("face_visibility")),
                "body_margin_4x5": clean(row.get("body_margin_4x5")),
                "text_overlay_space": clean(row.get("text_overlay_space")),
                "visual_strength": clean(row.get("visual_strength")),
                "decision": clean(row.get("decision")),
                "reject_category": reject_category(row),
                "notes": clean(row.get("notes")),
                "manual_next_action": "closed_rejected_do_not_download_or_formal_intake",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "none",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return accepted, invalid


def render_report(rows: list[Mapping[str, str]], invalid: list[Mapping[str, str]], manifest: Mapping[str, object]) -> str:
    lines = [
        "# Recovered Decision Reject Log V1",
        "",
        "This packet records Mike's manual visual triage rejections for recovered review-deck carry-forward candidates. It closes these rows as review-only rejects and does not download, approve, move, mark publish-ready, or publish anything.",
        "",
        f"- Version: `{VERSION}`",
        f"- Source decisions: `{manifest['source_reject_csv']}`",
        f"- Rejected rows: `{len(rows)}`",
        f"- Invalid rows: `{len(invalid)}`",
        "",
        "## Rejections",
        "",
        "| Candidate | Entity | Decision | Category | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {candidate} | {entity} | {decision} | {category} | {notes} |".format(
                candidate=clean(row.get("candidate_id")),
                entity=clean(row.get("entity_id")),
                decision=clean(row.get("decision")),
                category=clean(row.get("reject_category")),
                notes=clean(row.get("notes")).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- download_approved=no",
            "- asset_downloads=false",
            "- approval_state_change=none",
            "- publish_ready=false",
            "- publishing=false",
        ]
    )
    return "\n".join(lines) + "\n"


def build_packet(*, input_csv: Path, output_dir: Path, head_commit: str = "") -> dict[str, object]:
    resolved_input = resolve_path(input_csv)
    out_dir = resolve_output_dir(str(output_dir))
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, invalid = normalized_rows(read_csv_rows(resolved_input))
    csv_path = write_csv(out_dir / CSV_NAME, rows, OUTPUT_FIELDS)
    invalid_path = write_csv(
        out_dir / "invalid_recovered_decision_reject_rows.csv",
        invalid,
        OUTPUT_FIELDS + ["validation_issues"],
    )
    manifest_path = out_dir / MANIFEST_NAME
    report_path = out_dir / REPORT_NAME
    manifest: dict[str, object] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "recovered_decision_reject_log_ready",
        "repo_head": head_commit,
        "source_reject_csv": resolved_input.as_posix(),
        "output_dir": out_dir.as_posix(),
        "reject_log_csv": csv_path.as_posix(),
        "invalid_rows_csv": invalid_path.as_posix(),
        "report_path": report_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "input_rows": len(rows) + len(invalid),
        "rejected_rows": len(rows),
        "invalid_rows": len(invalid),
        "closed_candidate_ids": [clean(row.get("candidate_id")) for row in rows],
        "review_only": True,
        "download_approved_default": "no",
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, render_report(rows, invalid, manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only reject log for recovered decision triage rows.")
    parser.add_argument("--input-csv", default=DEFAULT_INPUT_CSV.as_posix())
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR.as_posix())
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        input_csv=Path(args.input_csv),
        output_dir=Path(args.output_dir),
        head_commit=args.head_commit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "rejected_rows": manifest["rejected_rows"],
                "invalid_rows": manifest["invalid_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
