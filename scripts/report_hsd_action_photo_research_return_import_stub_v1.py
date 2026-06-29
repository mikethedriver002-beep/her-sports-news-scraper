from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, read_csv, write_csv, write_json, write_text


VERSION = "hsd-action-photo-research-return-import-stub-v1-review-only"
GENERATED_AT_UTC = "2026-06-28T00:00:00+00:00"
ROOT = Path("data/asset_registry/action_photo_candidates")
IN_RESEARCH_RETURN_INTAKE_CSV = ROOT / "review_only_action_photo_research_return_intake_v1.csv"
OUT_IMPORT_REVIEW_CSV = ROOT / "review_only_action_photo_research_return_import_review_v1.csv"
OUT_IMPORT_REVIEW_MD = ROOT / "review_only_action_photo_research_return_import_review_v1.md"
OUT_IMPORT_REVIEW_JSON = ROOT / "review_only_action_photo_research_return_import_review_v1.json"
QUARANTINE_ROOT = "data/assets/quarantine/review_only_candidates"
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
DOWNLOAD_REQUIRED_FIELDS = [
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
]
DOWNLOAD_READY_IDENTITY = {"strong_context", "confirmed_official"}
ACTION_BLOCKLIST_CUES = {"headshot", "portrait", "roster photo", "static pose"}
IMPORT_REVIEW_FIELDS = [
    "import_review_id",
    "candidate_queue_id",
    "source_row_number",
    "candidate_photo_url_present",
    "evidence_url_present",
    "evidence_summary_present",
    "identity_anchor_url_present",
    "source_url_present",
    "entity_id_present",
    "rights_class_present",
    "identity_confidence",
    "identity_confidence_status",
    "intended_review_only_use_present",
    "missing_required_fields",
    "research_return_data_present",
    "action_photo_status",
    "operator_verify_required",
    "manual_review_status",
    "human_intake_download_approved",
    "candidate_ready_for_later_human_download_decision_review",
    "candidate_review_bucket",
    "download_gate_note",
    "manual_next_action",
    "download_approved",
    "quarantine_root",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "publish_action",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def has_any_return_data(row: Mapping[str, str]) -> bool:
    return any(clean(row.get(field)) for field in REQUIRED_RETURN_FIELDS + ["notes", "manual_reviewer"])


def action_photo_status(row: Mapping[str, str]) -> str:
    text = " ".join(
        clean(row.get(field)).lower()
        for field in ["candidate_photo_url", "evidence_summary", "notes", "manual_review_status"]
    )
    if any(cue in text for cue in ACTION_BLOCKLIST_CUES):
        return "manual_hold_possible_headshot_or_static_image"
    if clean(row.get("candidate_photo_url")) and clean(row.get("evidence_summary")):
        return "candidate_action_context_present_manual_review"
    if clean(row.get("candidate_photo_url")):
        return "candidate_url_present_needs_action_evidence"
    return "candidate_url_missing"


def identity_confidence_status(identity_confidence: str) -> str:
    if identity_confidence in DOWNLOAD_READY_IDENTITY:
        return "identity_ready_for_human_review"
    if identity_confidence:
        return "identity_not_strong_enough_for_download_decision"
    return "identity_missing"


def import_review_bucket(*, has_return: bool, ready: bool, human_download_yes: bool, missing: List[str]) -> str:
    if human_download_yes and missing:
        return "human_download_approved_incomplete_hold"
    if human_download_yes and ready:
        return "human_download_approved_requires_quarantine_gate_review"
    if ready:
        return "ready_for_later_human_download_decision_review"
    if has_return:
        return "returned_needs_manual_field_fix"
    return "research_return_not_pasted_yet"


def manual_next_action(bucket: str, missing: List[str]) -> str:
    if bucket == "ready_for_later_human_download_decision_review":
        return "Review source, identity, rights, action fit, and crop/use suitability; only a later human intake edit can approve quarantine-only download review."
    if bucket == "human_download_approved_requires_quarantine_gate_review":
        return "Human intake download approval flag is marked yes; recheck quarantine gate metadata before any separate local candidate download step. This report does not download or approve assets."
    if bucket == "human_download_approved_incomplete_hold":
        return "Human intake download approval flag is marked yes but required metadata is incomplete; hold and fill missing fields before any quarantine-only download decision."
    if bucket == "returned_needs_manual_field_fix":
        return f"Fill missing required return fields: {'|'.join(missing)}. Then rerun this review-only import summary."
    return "Paste human-reviewed candidate URL, source URL, evidence, identity anchor, rights class, identity confidence, and intended review-only use into the research return intake."


def action_photo_research_return_import_review_rows(return_rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for index, row in enumerate(return_rows, start=1):
        normalized = {str(key): clean(value) for key, value in row.items()}
        missing = [field for field in REQUIRED_RETURN_FIELDS if not normalized.get(field)]
        identity = normalized.get("identity_confidence", "")
        identity_status = identity_confidence_status(identity)
        action_status = action_photo_status(normalized)
        has_return = has_any_return_data(normalized)
        ready = not missing and identity in DOWNLOAD_READY_IDENTITY and action_status == "candidate_action_context_present_manual_review"
        human_download_yes = normalized.get("download_approved", "").lower() == "yes"
        bucket = import_review_bucket(
            has_return=has_return,
            ready=ready,
            human_download_yes=human_download_yes,
            missing=missing,
        )
        rows.append(
            {
                "import_review_id": f"APIR{index:03d}",
                "candidate_queue_id": normalized.get("candidate_queue_id", ""),
                "source_row_number": str(index + 1),
                "candidate_photo_url_present": yes_no(bool(normalized.get("candidate_photo_url"))),
                "evidence_url_present": yes_no(bool(normalized.get("evidence_url"))),
                "evidence_summary_present": yes_no(bool(normalized.get("evidence_summary"))),
                "identity_anchor_url_present": yes_no(bool(normalized.get("identity_anchor_url"))),
                "source_url_present": yes_no(bool(normalized.get("source_url"))),
                "entity_id_present": yes_no(bool(normalized.get("entity_id"))),
                "rights_class_present": yes_no(bool(normalized.get("rights_class"))),
                "identity_confidence": identity,
                "identity_confidence_status": identity_status,
                "intended_review_only_use_present": yes_no(bool(normalized.get("intended_review_only_use"))),
                "missing_required_fields": "|".join(missing),
                "research_return_data_present": yes_no(has_return),
                "action_photo_status": action_status,
                "operator_verify_required": normalized.get("operator_verify_required", "yes") or "yes",
                "manual_review_status": normalized.get("manual_review_status", ""),
                "human_intake_download_approved": yes_no(human_download_yes),
                "candidate_ready_for_later_human_download_decision_review": yes_no(ready),
                "candidate_review_bucket": bucket,
                "download_gate_note": (
                    "Generated import review does not download files or approve assets; any later local file must remain quarantine-only."
                ),
                "manual_next_action": manual_next_action(bucket, missing),
                "download_approved": "no",
                "quarantine_root": QUARANTINE_ROOT,
                "review_only": "true",
                "publish_ready": "false",
                "approval_state_change": "none",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_action": "none_artifact_only",
            }
        )
    return rows


def validate_import_review_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen_ids = set()
    seen_queue_ids = set()
    yes_no_fields = [
        "candidate_photo_url_present",
        "evidence_url_present",
        "evidence_summary_present",
        "identity_anchor_url_present",
        "source_url_present",
        "entity_id_present",
        "rights_class_present",
        "intended_review_only_use_present",
        "research_return_data_present",
        "human_intake_download_approved",
        "candidate_ready_for_later_human_download_decision_review",
    ]
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in IMPORT_REVIEW_FIELDS}
        review_id = normalized["import_review_id"]
        queue_id = normalized["candidate_queue_id"]
        if not review_id:
            issues.append({"row": str(index), "field": "import_review_id", "issue": "required_import_review_id_blank"})
        elif review_id in seen_ids:
            issues.append({"row": str(index), "field": "import_review_id", "issue": "duplicate_import_review_id"})
        seen_ids.add(review_id)
        if not queue_id:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "required_candidate_queue_id_blank"})
        elif queue_id in seen_queue_ids:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "duplicate_candidate_queue_id"})
        seen_queue_ids.add(queue_id)
        for field in yes_no_fields:
            if normalized[field] not in {"yes", "no"}:
                issues.append({"row": str(index), "field": field, "issue": "yes_no_field_invalid"})
        if normalized["candidate_ready_for_later_human_download_decision_review"] == "yes" and normalized["missing_required_fields"]:
            issues.append({"row": str(index), "field": "missing_required_fields", "issue": "ready_row_has_missing_required_fields"})
        if normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_import_review_must_not_approve_downloads"})
        if normalized["quarantine_root"] != QUARANTINE_ROOT:
            issues.append({"row": str(index), "field": "quarantine_root", "issue": "quarantine_root_must_be_review_only_candidates"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "import_review_rows_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "import_review_rows_must_not_be_publish_ready"})
        if normalized["approval_state_change"] != "none":
            issues.append({"row": str(index), "field": "approval_state_change", "issue": "import_review_rows_must_not_change_approval_state"})
        for field in ["asset_downloads", "headshot_writes", "approved_marker_writes"]:
            if normalized[field] != "false":
                issues.append({"row": str(index), "field": field, "issue": "import_review_rows_must_not_write_assets_or_markers"})
        if normalized["publish_action"] != "none_artifact_only":
            issues.append({"row": str(index), "field": "publish_action", "issue": "import_review_rows_must_not_publish"})
    return issues


def render_import_review_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    bucket_counts: Dict[str, int] = {}
    for row in rows:
        bucket = clean(row.get("candidate_review_bucket"))
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    lines = [
        "# Review-Only Action Photo Research Return Import Review v1",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Reads the human-editable action-photo research return intake and summarizes pasted candidate/evidence readiness. This artifact does not fetch sources, download images, approve candidates or assets, write headshots, create `.approved` markers, move files, or publish.",
        "",
        "## Summary",
        "",
        f"- Source intake: `{IN_RESEARCH_RETURN_INTAKE_CSV.as_posix()}`",
        f"- Import review rows: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows with research return data: `{sum(1 for row in rows if clean(row.get('research_return_data_present')) == 'yes')}`",
        f"- Rows ready only for later human download-decision review: `{sum(1 for row in rows if clean(row.get('candidate_ready_for_later_human_download_decision_review')) == 'yes')}`",
        f"- Human-reported download approval rows: `{sum(1 for row in rows if clean(row.get('human_intake_download_approved')) == 'yes')}`",
        f"- Generated download approvals: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        "",
        "## Buckets",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(bucket_counts.items()))
    lines += [
        "",
        "## Preview",
        "",
        "| Import | Queue | Data? | Ready? | Human DL? | Missing | Bucket | Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {review_id} | {queue_id} | {data} | {ready} | {human_dl} | `{missing}` | {bucket} | {next_action} |".format(
                review_id=clean(row.get("import_review_id")),
                queue_id=clean(row.get("candidate_queue_id")),
                data=clean(row.get("research_return_data_present")),
                ready=clean(row.get("candidate_ready_for_later_human_download_decision_review")),
                human_dl=clean(row.get("human_intake_download_approved")),
                missing=clean(row.get("missing_required_fields")).replace("|", "/"),
                bucket=clean(row.get("candidate_review_bucket")),
                next_action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> Dict[str, object]:
    return {
        "version": VERSION,
        "status": "action_photo_research_return_import_review_ready" if not issues else "action_photo_research_return_import_review_has_validation_issues",
        "generated_at_utc": generated_at,
        "source_intake_csv": IN_RESEARCH_RETURN_INTAKE_CSV.as_posix(),
        "resolved_source_intake_csv": input_path(IN_RESEARCH_RETURN_INTAKE_CSV).as_posix(),
        "import_review_rows": len(rows),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "rows_with_research_return_data": sum(1 for row in rows if clean(row.get("research_return_data_present")) == "yes"),
        "ready_for_later_human_download_decision_review_rows": sum(
            1 for row in rows if clean(row.get("candidate_ready_for_later_human_download_decision_review")) == "yes"
        ),
        "human_intake_download_approved_yes_rows": sum(1 for row in rows if clean(row.get("human_intake_download_approved")) == "yes"),
        "generated_download_approved_yes_rows": sum(1 for row in rows if clean(row.get("download_approved")) == "yes"),
        "blank_source_url_rows": sum(1 for row in rows if clean(row.get("source_url_present")) == "no"),
        "blank_rights_class_rows": sum(1 for row in rows if clean(row.get("rights_class_present")) == "no"),
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
        "worksheet_csv": OUT_IMPORT_REVIEW_CSV.as_posix(),
        "worksheet_md": OUT_IMPORT_REVIEW_MD.as_posix(),
        "worksheet_json": OUT_IMPORT_REVIEW_JSON.as_posix(),
        "import_rows_detail": rows,
    }


def main() -> int:
    return_rows = read_csv(IN_RESEARCH_RETURN_INTAKE_CSV)
    review_rows = action_photo_research_return_import_review_rows(return_rows)
    issues = validate_import_review_rows(review_rows)
    write_csv(OUT_IMPORT_REVIEW_CSV, review_rows, IMPORT_REVIEW_FIELDS)
    write_text(OUT_IMPORT_REVIEW_MD, render_import_review_markdown(review_rows, issues, GENERATED_AT_UTC))
    write_json(OUT_IMPORT_REVIEW_JSON, manifest(review_rows, issues, GENERATED_AT_UTC))
    print(json.dumps({"version": VERSION, "status": "ok", "import_review_rows": len(review_rows), "validation_issue_count": len(issues)}, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
