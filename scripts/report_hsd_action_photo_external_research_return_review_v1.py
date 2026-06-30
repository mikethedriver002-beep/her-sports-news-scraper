from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, read_csv, write_csv, write_json, write_text


VERSION = "hsd-action-photo-external-research-return-review-v1-review-only"
GENERATED_AT_UTC = "2026-06-30T00:00:00+00:00"
ROOT = Path("data/asset_registry/action_photo_candidates")
IN_RESEARCH_RETURN_INTAKE_CSV = ROOT / "review_only_action_photo_research_return_intake_v1.csv"
DEFAULT_EXTERNAL_RETURN_CSV = Path(r"C:\Users\Mike\Desktop\deep-research-report-md.md")
OUT_CSV = ROOT / "review_only_action_photo_external_research_return_review_v1.csv"
OUT_MD = ROOT / "review_only_action_photo_external_research_return_review_v1.md"
OUT_JSON = ROOT / "review_only_action_photo_external_research_return_review_v1.json"
DOWNLOAD_READY_IDENTITY = {"strong_context", "confirmed_official"}
REQUIRED_RETURN_FIELDS = [
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
]
EXTERNAL_RETURN_FIELDS = [
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
]
REVIEW_FIELDS = [
    "review_id",
    "candidate_queue_id",
    "expected_in_shared_intake",
    "external_return_present",
    "external_row_number",
    "candidate_photo_url_present",
    "candidate_photo_url_direct_image_hold",
    "normalized_candidate_page_url",
    "evidence_url_present",
    "source_url_present",
    "entity_id_present",
    "rights_class_present",
    "identity_confidence",
    "identity_confidence_status",
    "identity_vocabulary_mismatch",
    "identity_anchor_url_present",
    "intended_review_only_use_present",
    "missing_required_fields",
    "candidate_ready_for_later_human_download_decision_review",
    "download_approved",
    "manual_review_status",
    "review_bucket",
    "manual_next_action",
    "review_only",
    "source_fetching",
    "auto_source_enablement",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "approval_state_change",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def external_return_path() -> Path:
    configured = clean(os.environ.get("HSD_ACTION_PHOTO_EXTERNAL_RETURN_CSV"))
    return Path(configured) if configured else DEFAULT_EXTERNAL_RETURN_CSV


def direct_image_or_hotlink_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    host = parsed.netloc.lower()
    if path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return True
    direct_host_cues = ("cdn.", "images.", "cloudfront.net", "sidearmdev.com")
    direct_path_cues = ("/resizer/", "/resize", "resize?")
    return any(cue in host for cue in direct_host_cues) or any(cue in path for cue in direct_path_cues)


def identity_confidence_status(identity_confidence: str) -> str:
    if identity_confidence in DOWNLOAD_READY_IDENTITY:
        return "identity_ready_for_human_review"
    if identity_confidence:
        return "identity_vocabulary_requires_operator_normalization"
    return "identity_missing"


def normalized_candidate_page_url(row: Mapping[str, str], direct_image_hold: bool) -> str:
    if direct_image_hold:
        return clean(row.get("source_url")) or clean(row.get("evidence_url"))
    return clean(row.get("candidate_photo_url")) or clean(row.get("source_url")) or clean(row.get("evidence_url"))


def external_rows_by_queue_id(rows: Iterable[Mapping[str, str]]) -> Dict[str, Dict[str, str]]:
    indexed: Dict[str, Dict[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in EXTERNAL_RETURN_FIELDS}
        queue_id = normalized.get("candidate_queue_id", "")
        if queue_id and queue_id not in indexed:
            normalized["external_row_number"] = str(row_number)
            indexed[queue_id] = normalized
    return indexed


def review_bucket(*, external_present: bool, direct_image_hold: bool, identity_mismatch: bool, missing: List[str]) -> str:
    if not external_present:
        return "external_return_missing"
    if missing:
        return "external_return_missing_required_fields"
    if direct_image_hold and identity_mismatch:
        return "external_return_direct_image_and_identity_vocab_hold"
    if direct_image_hold:
        return "external_return_direct_image_url_hold"
    if identity_mismatch:
        return "external_return_identity_vocab_hold"
    return "external_return_needs_human_review"


def manual_next_action(bucket: str, normalized_url: str) -> str:
    if bucket == "external_return_missing":
        return "Ask the research operator to supply this APQ row before any import-review or quarantine-decision work."
    if bucket == "external_return_missing_required_fields":
        return "Fill missing source/evidence/entity/rights/identity/use fields in a human-reviewed intake row; keep generated defaults no."
    if bucket == "external_return_direct_image_and_identity_vocab_hold":
        return f"Use the source/evidence page URL as the candidate page lead ({normalized_url}); do not treat the direct image URL as safe, and normalize identity confidence only after operator verification."
    if bucket == "external_return_direct_image_url_hold":
        return f"Use the source/evidence page URL as the candidate page lead ({normalized_url}); do not paste direct image binaries into a gate as source-page-safe URLs."
    if bucket == "external_return_identity_vocab_hold":
        return "Operator must map identity confidence to the controlled vocabulary only after confirming the identity anchor."
    return "Review source, identity, rights, action fit, and crop/use suitability before any later human download-decision review."


def external_return_review_rows(
    expected_intake_rows: Iterable[Mapping[str, str]],
    supplied_return_rows: Iterable[Mapping[str, str]],
) -> List[Dict[str, str]]:
    supplied_by_id = external_rows_by_queue_id(supplied_return_rows)
    rows: List[Dict[str, str]] = []
    for index, intake_row in enumerate(expected_intake_rows, start=1):
        queue_id = clean(intake_row.get("candidate_queue_id"))
        supplied = supplied_by_id.get(queue_id, {})
        external_present = bool(supplied)
        missing = [field for field in REQUIRED_RETURN_FIELDS if not clean(supplied.get(field))]
        candidate_url = clean(supplied.get("candidate_photo_url"))
        direct_image_hold = bool(candidate_url) and direct_image_or_hotlink_url(candidate_url)
        identity = clean(supplied.get("identity_confidence"))
        identity_status = identity_confidence_status(identity)
        identity_mismatch = bool(identity) and identity not in DOWNLOAD_READY_IDENTITY
        normalized_url = normalized_candidate_page_url(supplied, direct_image_hold)
        bucket = review_bucket(
            external_present=external_present,
            direct_image_hold=direct_image_hold,
            identity_mismatch=identity_mismatch,
            missing=missing,
        )
        rows.append(
            {
                "review_id": f"APER{index:03d}",
                "candidate_queue_id": queue_id,
                "expected_in_shared_intake": "yes",
                "external_return_present": yes_no(external_present),
                "external_row_number": clean(supplied.get("external_row_number")),
                "candidate_photo_url_present": yes_no(bool(candidate_url)),
                "candidate_photo_url_direct_image_hold": yes_no(direct_image_hold),
                "normalized_candidate_page_url": normalized_url,
                "evidence_url_present": yes_no(bool(clean(supplied.get("evidence_url")))),
                "source_url_present": yes_no(bool(clean(supplied.get("source_url")))),
                "entity_id_present": yes_no(bool(clean(supplied.get("entity_id")))),
                "rights_class_present": yes_no(bool(clean(supplied.get("rights_class")))),
                "identity_confidence": identity,
                "identity_confidence_status": identity_status,
                "identity_vocabulary_mismatch": yes_no(identity_mismatch),
                "identity_anchor_url_present": yes_no(bool(clean(supplied.get("identity_anchor_url")))),
                "intended_review_only_use_present": yes_no(bool(clean(supplied.get("intended_review_only_use")))),
                "missing_required_fields": "|".join(missing),
                "candidate_ready_for_later_human_download_decision_review": "no",
                "download_approved": "no",
                "manual_review_status": "external_return_review_only_hold",
                "review_bucket": bucket,
                "manual_next_action": manual_next_action(bucket, normalized_url),
                "review_only": "true",
                "source_fetching": "false",
                "auto_source_enablement": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "approval_state_change": "none",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    return rows


def validate_review_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen_ids = set()
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in REVIEW_FIELDS}
        review_id = normalized["review_id"]
        if not review_id:
            issues.append({"row": str(index), "field": "review_id", "issue": "required_review_id_blank"})
        elif review_id in seen_ids:
            issues.append({"row": str(index), "field": "review_id", "issue": "duplicate_review_id"})
        seen_ids.add(review_id)
        if normalized["candidate_ready_for_later_human_download_decision_review"] != "no":
            issues.append({"row": str(index), "field": "candidate_ready_for_later_human_download_decision_review", "issue": "external_review_must_not_mark_ready"})
        if normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "external_review_must_not_approve_downloads"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "external_review_must_remain_review_only"})
        if normalized["approval_state_change"] != "none":
            issues.append({"row": str(index), "field": "approval_state_change", "issue": "external_review_must_not_change_approval_state"})
        for field in [
            "source_fetching",
            "auto_source_enablement",
            "asset_downloads",
            "headshot_writes",
            "approved_marker_writes",
            "publish_ready",
            "auto_approval",
            "auto_publish",
            "move_files",
            "paid_apis",
        ]:
            if normalized[field] != "false":
                issues.append({"row": str(index), "field": field, "issue": "external_review_guardrail_field_must_be_false"})
    return issues


def render_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str, external_csv: Path) -> str:
    bucket_counts: Dict[str, int] = {}
    for row in rows:
        bucket = clean(row.get("review_bucket"))
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    lines = [
        "# Review-Only Action Photo External Research Return Review v1",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Reviews Mike's supplied external action-photo research return CSV against the shared action-photo return intake. This artifact does not write intake rows, fetch sources, download images, approve candidates or assets, write headshots/cutouts/logos, create `.approved` markers, move files, enable sources, or publish.",
        "",
        "## Summary",
        "",
        f"- External return CSV: `{external_csv}`",
        f"- Shared intake CSV: `{IN_RESEARCH_RETURN_INTAKE_CSV.as_posix()}`",
        f"- Expected APQ rows: `{len(rows)}`",
        f"- External returned rows: `{sum(1 for row in rows if clean(row.get('external_return_present')) == 'yes')}`",
        f"- Missing external APQ rows: `{sum(1 for row in rows if clean(row.get('external_return_present')) == 'no')}`",
        f"- Direct image / hotlink candidate URL holds: `{sum(1 for row in rows if clean(row.get('candidate_photo_url_direct_image_hold')) == 'yes')}`",
        f"- Identity vocabulary mismatch rows: `{sum(1 for row in rows if clean(row.get('identity_vocabulary_mismatch')) == 'yes')}`",
        f"- Rows ready only for later human download-decision review: `{sum(1 for row in rows if clean(row.get('candidate_ready_for_later_human_download_decision_review')) == 'yes')}`",
        f"- Generated download approvals: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        f"- Validation issues: `{len(issues)}`",
        "",
        "## Buckets",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(bucket_counts.items()))
    lines += [
        "",
        "## Review Rows",
        "",
        "| Review | Queue | Returned? | Direct Image Hold | Identity | Missing | Bucket | Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {review_id} | {queue_id} | {returned} | {direct} | {identity} | `{missing}` | {bucket} | {next_action} |".format(
                review_id=clean(row.get("review_id")),
                queue_id=clean(row.get("candidate_queue_id")),
                returned=clean(row.get("external_return_present")),
                direct=clean(row.get("candidate_photo_url_direct_image_hold")),
                identity=clean(row.get("identity_confidence_status")),
                missing=clean(row.get("missing_required_fields")).replace("|", "/"),
                bucket=clean(row.get("review_bucket")),
                next_action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str, external_csv: Path) -> Dict[str, object]:
    return {
        "version": VERSION,
        "status": "action_photo_external_research_return_review_ready" if not issues else "action_photo_external_research_return_review_has_validation_issues",
        "generated_at_utc": generated_at,
        "external_return_csv": str(external_csv),
        "external_return_csv_exists": external_csv.exists(),
        "source_intake_csv": IN_RESEARCH_RETURN_INTAKE_CSV.as_posix(),
        "resolved_source_intake_csv": input_path(IN_RESEARCH_RETURN_INTAKE_CSV).as_posix(),
        "review_rows": len(rows),
        "external_return_rows": sum(1 for row in rows if clean(row.get("external_return_present")) == "yes"),
        "missing_external_return_rows": sum(1 for row in rows if clean(row.get("external_return_present")) == "no"),
        "missing_candidate_queue_ids": [
            clean(row.get("candidate_queue_id"))
            for row in rows
            if clean(row.get("external_return_present")) == "no"
        ],
        "direct_image_url_hold_rows": sum(1 for row in rows if clean(row.get("candidate_photo_url_direct_image_hold")) == "yes"),
        "identity_vocabulary_mismatch_rows": sum(1 for row in rows if clean(row.get("identity_vocabulary_mismatch")) == "yes"),
        "ready_for_later_human_download_decision_review_rows": sum(
            1 for row in rows if clean(row.get("candidate_ready_for_later_human_download_decision_review")) == "yes"
        ),
        "generated_download_approval_rows": sum(1 for row in rows if clean(row.get("download_approved")) == "yes"),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
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
        "worksheet_csv": OUT_CSV.as_posix(),
        "worksheet_md": OUT_MD.as_posix(),
        "worksheet_json": OUT_JSON.as_posix(),
        "review_rows_detail": rows,
    }


def main() -> int:
    external_csv = external_return_path()
    expected_rows = read_csv(IN_RESEARCH_RETURN_INTAKE_CSV)
    supplied_rows = read_csv(external_csv) if external_csv.exists() else []
    review_rows = external_return_review_rows(expected_rows, supplied_rows)
    issues = validate_review_rows(review_rows)
    write_csv(OUT_CSV, review_rows, REVIEW_FIELDS)
    write_text(OUT_MD, render_markdown(review_rows, issues, GENERATED_AT_UTC, external_csv))
    write_json(OUT_JSON, manifest(review_rows, issues, GENERATED_AT_UTC, external_csv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": "ok",
                "review_rows": len(review_rows),
                "external_return_rows": sum(1 for row in review_rows if clean(row.get("external_return_present")) == "yes"),
                "validation_issue_count": len(issues),
            },
            indent=2,
        )
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
