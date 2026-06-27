from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple


ROOT = Path("data/asset_registry/womens_soccer")
CONTACT_SHEET = ROOT / "womens_soccer_logo_contact_sheet.csv"
INTAKE = ROOT / "womens_soccer_logo_review_intake.csv"
REPORT_JSON = ROOT / "womens_soccer_logo_review_intake_apply_report.json"
REPORT_MD = ROOT / "womens_soccer_logo_review_intake_apply_report.md"

APPROVE_DECISION = "approve_for_review_only_renderer_use"
DECISION_SOURCE = "human_reviewed_womens_soccer_logo_contact_sheet"
REVIEW_ONLY_POLICY = "manual_intake_only_no_auto_approval_no_publish_ready_lane"
GUARDRAIL_FIELDS = [
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]
APPROVAL_FIELDS = [
    "entity_type",
    "entity_id",
    "approval_scope",
    "approval_status",
    "approved_by",
    "approved_at_utc",
    "auto_approval_allowed",
    "render_enabled",
    "publish_ready",
    "notes",
]
ASSET_SLOT_FIELDS = [
    "entity_type",
    "entity_id",
    "league_id",
    "team_id",
    "asset_slot",
    "intended_use",
    "target_path",
    "source_url_required",
    "local_file_path",
    "file_exists",
    "approval_status",
    "render_enabled",
    "auto_download_allowed",
    "publish_ready",
    "notes",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def truthy_yes(value: Any) -> bool:
    return clean(value).lower() in {"yes", "y", "true", "1"}


def false_flag(value: Any) -> bool:
    return clean(value).lower() in {"", "false", "0", "no", "n"}


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def merged_fields(existing_fields: Iterable[str], required_fields: Iterable[str]) -> List[str]:
    output: List[str] = []
    for field in list(existing_fields) + list(required_fields):
        if field and field not in output:
            output.append(field)
    return output


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def approval_scope_for(row: Mapping[str, str]) -> str:
    return "league_mark" if clean(row.get("entity_type")) == "league" else "team_logo"


def slot_key(row: Mapping[str, str]) -> Tuple[str, str, str]:
    return clean(row.get("entity_type")), clean(row.get("entity_id")), clean(row.get("asset_slot"))


def approval_key(row: Mapping[str, str], scope: str | None = None) -> Tuple[str, str, str]:
    return clean(row.get("entity_type")), clean(row.get("entity_id")), clean(scope or row.get("approval_scope"))


def contact_key(row: Mapping[str, str]) -> Tuple[str, str, str]:
    return clean(row.get("scope_id")), clean(row.get("entity_type")), clean(row.get("entity_id"))


def explicit_approval_ready(row: Mapping[str, str]) -> tuple[bool, List[str]]:
    problems: List[str] = []
    if clean(row.get("operator_decision")) != APPROVE_DECISION:
        problems.append("operator_decision_not_approve")
    for field in ["source_reviewed", "identity_match"]:
        if not truthy_yes(row.get(field)):
            problems.append(f"{field}_not_yes")
    for field in GUARDRAIL_FIELDS:
        if not false_flag(row.get(field)):
            problems.append(f"{field}_must_remain_false")
    if not clean(row.get("source_url_to_record")):
        problems.append("source_url_to_record_missing")
    local_path = clean(row.get("local_logo_path"))
    if not local_path:
        problems.append("local_logo_path_missing")
    elif not Path(local_path).exists():
        problems.append("local_logo_path_missing_on_disk")
    return not problems, problems


def approved_intake_rows(rows: Iterable[Mapping[str, str]]) -> List[Mapping[str, str]]:
    return [row for row in rows if clean(row.get("operator_decision")) == APPROVE_DECISION]


def apply_intake(
    contact_rows: List[Dict[str, str]],
    intake_rows: List[Dict[str, str]],
    asset_slots_by_scope: Mapping[str, List[Dict[str, str]]],
    approval_rows_by_scope: Mapping[str, List[Dict[str, str]]],
    *,
    applied_at_utc: str,
) -> Dict[str, Any]:
    contact_by_key = {contact_key(row): row for row in contact_rows}
    applied: List[Dict[str, str]] = []
    failed: List[Dict[str, str]] = []

    slot_indexes = {
        scope: {slot_key(row): row for row in rows}
        for scope, rows in asset_slots_by_scope.items()
    }
    approval_indexes = {
        scope: {approval_key(row): row for row in rows}
        for scope, rows in approval_rows_by_scope.items()
    }

    for row in approved_intake_rows(intake_rows):
        scope_id = clean(row.get("scope_id"))
        entity_type = clean(row.get("entity_type"))
        entity_id = clean(row.get("entity_id"))
        key = contact_key(row)
        contact = contact_by_key.get(key)
        ready, problems = explicit_approval_ready(row)
        if not contact:
            problems.append("contact_sheet_row_missing")
        if scope_id not in asset_slots_by_scope or scope_id not in approval_rows_by_scope:
            problems.append("registry_scope_missing")
        if problems:
            failed.append(
                {
                    "scope_id": scope_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "display_name": clean(row.get("display_name")),
                    "status": "|".join(problems),
                }
            )
            continue

        asset_slot = clean(contact.get("asset_slot"))
        approval_scope = approval_scope_for(row)
        slot = slot_indexes[scope_id].get((entity_type, entity_id, asset_slot))
        if not slot:
            failed.append(
                {
                    "scope_id": scope_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "display_name": clean(row.get("display_name")),
                    "status": "asset_slot_row_missing",
                }
            )
            continue

        approval = approval_indexes[scope_id].get((entity_type, entity_id, approval_scope))
        if not approval:
            approval = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "approval_scope": approval_scope,
                "approval_status": "not_approved",
                "approved_by": "",
                "approved_at_utc": "",
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": "Added by human logo contact sheet approval apply bridge",
            }
            approval_rows_by_scope[scope_id].append(approval)
            approval_indexes[scope_id][(entity_type, entity_id, approval_scope)] = approval

        local_path = clean(row.get("local_logo_path"))
        approval.update(
            {
                "approval_status": "approved",
                "approved_by": clean(row.get("reviewed_by")) or "Mike",
                "approved_at_utc": applied_at_utc,
                "auto_approval_allowed": "false",
                "render_enabled": "false",
                "publish_ready": "false",
                "notes": (
                    "Human-approved for review-only renderer logo/mark use from women soccer logo contact sheet; "
                    f"source={clean(row.get('source_url_to_record'))}; "
                    f"decision_source={DECISION_SOURCE}; policy={REVIEW_ONLY_POLICY}"
                ),
            }
        )
        slot.update(
            {
                "local_file_path": local_path,
                "file_exists": "true",
                "approval_status": "approved",
                "render_enabled": "false",
                "auto_download_allowed": "false",
                "publish_ready": "false",
                "notes": (
                    "Human-approved local candidate for review-only logo/mark use; "
                    "no render enablement, publishing, file movement, or publish-ready lane"
                ),
            }
        )
        applied.append(
            {
                "scope_id": scope_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "display_name": clean(row.get("display_name")),
                "approval_scope": approval_scope,
                "local_logo_path": local_path,
                "status": "applied_review_only_logo_metadata",
            }
        )

    return {
        "version": "hsd-womens-soccer-logo-review-intake-apply-v1",
        "generated_at_utc": applied_at_utc,
        "review_only": True,
        "policy": REVIEW_ONLY_POLICY,
        "intake_rows": len(intake_rows),
        "approved_intake_rows": len(approved_intake_rows(intake_rows)),
        "applied_review_only_metadata": len(applied),
        "failed_rows": len(failed),
        "applied_rows": applied,
        "failed": failed,
        "guardrails": {
            "paid_apis": False,
            "asset_downloads": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "render_enabled": False,
        },
    }


def write_report_md(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# Women's Soccer Logo Review Intake Apply Report",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        "",
        "Review-only metadata application from the human-edited women's soccer logo intake CSV.",
        "",
        "## Counts",
        "",
        f"- intake rows: `{report.get('intake_rows')}`",
        f"- approved intake rows: `{report.get('approved_intake_rows')}`",
        f"- applied review-only metadata rows: `{report.get('applied_review_only_metadata')}`",
        f"- failed rows: `{report.get('failed_rows')}`",
        "",
        "## Guardrails",
        "",
        "- No automatic approval occurred; this applies explicit human intake decisions only.",
        "- No logo file was downloaded, copied, moved, published, render-enabled, or made publish-ready.",
        "- `auto_approval_allowed`, `render_enabled`, and `publish_ready` remain false in registry rows.",
        "",
        "## Applied Rows",
        "",
    ]
    for row in report.get("applied_rows", []):
        lines.append(
            f"- {row.get('display_name')} | {row.get('approval_scope')} | {row.get('local_logo_path')}"
        )
    if report.get("failed"):
        lines.extend(["", "## Failed Rows", ""])
        for row in report.get("failed", []):
            lines.append(f"- {row.get('display_name')} | {row.get('status')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    contact_rows, _ = read_csv(CONTACT_SHEET)
    intake_rows, _ = read_csv(INTAKE)
    scopes = sorted({clean(row.get("scope_id")) for row in contact_rows if clean(row.get("scope_id"))})
    asset_slots_by_scope: Dict[str, List[Dict[str, str]]] = {}
    approval_rows_by_scope: Dict[str, List[Dict[str, str]]] = {}
    asset_fields_by_scope: Dict[str, List[str]] = {}
    approval_fields_by_scope: Dict[str, List[str]] = {}
    for scope in scopes:
        asset_slots_by_scope[scope], asset_fields_by_scope[scope] = read_csv(ROOT / scope / "asset_slots.csv")
        approval_rows_by_scope[scope], approval_fields_by_scope[scope] = read_csv(ROOT / scope / "approval_status.csv")

    applied_at_utc = now_iso()
    report = apply_intake(
        contact_rows,
        intake_rows,
        asset_slots_by_scope,
        approval_rows_by_scope,
        applied_at_utc=applied_at_utc,
    )
    for scope in scopes:
        write_csv(
            ROOT / scope / "asset_slots.csv",
            asset_slots_by_scope[scope],
            merged_fields(asset_fields_by_scope.get(scope, []), ASSET_SLOT_FIELDS),
        )
        write_csv(
            ROOT / scope / "approval_status.csv",
            approval_rows_by_scope[scope],
            merged_fields(approval_fields_by_scope.get(scope, []), APPROVAL_FIELDS),
        )
    write_json(REPORT_JSON, report)
    write_report_md(REPORT_MD, report)
    print(json.dumps(report, indent=2, sort_keys=False))
    return 0 if report.get("failed_rows") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
