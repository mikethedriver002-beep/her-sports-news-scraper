from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, output_path, write_csv, write_json

AUDIT_JSON = "data/asset_registry/wnba/athlete_identity_audit.json"
OUT_MD = "data/asset_registry/wnba/athlete_identity_resolution_workflow.md"
OUT_CANDIDATES = "data/asset_registry/wnba/athlete_identity_resolution_candidates.csv"
OUT_TEMPLATE = "data/asset_registry/wnba/athlete_identity_resolution_template.csv"
OUT_MANIFEST = "data/asset_registry/wnba/athlete_identity_resolution_manifest.json"
OPERATOR_INBOX = "operator/inbox/wnba_athlete_identity_resolution.csv"

VERSION = "hsd-wnba-athlete-identity-resolution-v1-review-only"
POLICY = "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane"

FIELDS = [
    "athlete_id",
    "display_name",
    "team_id",
    "provider_player_id",
    "asset_path",
    "approved_marker_path",
    "highest_severity",
    "issue_count",
    "issue_codes",
    "audit_evidence",
    "recommended_operator_action",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "provider_player_id_verified",
    "approved_source_url",
    "secondary_source_url",
    "backfill_provider_player_id",
    "operator_notes",
    "operator_name",
    "reviewed_at_local",
    "issue_resolution_status",
    "copy_target",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "review_only_policy",
]

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str) -> Dict[str, Any]:
    found = input_path(path)
    if not found.exists():
        return {}
    try:
        return json.loads(found.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def summarize_issues(issues: Iterable[Mapping[str, Any]]) -> List[Dict[str, str]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for issue in issues:
        athlete_id = clean(issue.get("athlete_id"))
        if athlete_id:
            grouped.setdefault(athlete_id, []).append(issue)

    rows: List[Dict[str, str]] = []
    for athlete_id, athlete_issues in grouped.items():
        ordered = sorted(
            athlete_issues,
            key=lambda row: (
                SEVERITY_RANK.get(clean(row.get("severity")), 9),
                clean(row.get("issue_code")),
            ),
        )
        first = ordered[0]
        severities = [clean(row.get("severity")) for row in ordered if clean(row.get("severity"))]
        highest = sorted(severities, key=lambda value: SEVERITY_RANK.get(value, 9))[0] if severities else "review"
        codes = sorted({clean(row.get("issue_code")) for row in ordered if clean(row.get("issue_code"))})
        provider_ids = [clean(row.get("provider_player_id")) for row in ordered if clean(row.get("provider_player_id"))]
        action = "hold_until_identity_source_confirms_player_and_asset"
        if any(code in {"missing_provider_player_id_in_image_registry", "blank_per_row_approval_decision"} for code in codes):
            action = "verify_identity_and_backfill_provider_id_if_source_supported"
        if highest == "critical":
            action = "hold_and_reconcile_identity_conflict_before_renderer_use"
        rows.append(
            {
                "athlete_id": athlete_id,
                "display_name": clean(first.get("display_name")),
                "team_id": clean(first.get("team_id")),
                "provider_player_id": provider_ids[0] if provider_ids else "",
                "asset_path": clean(first.get("asset_path")),
                "approved_marker_path": clean(first.get("approved_marker_path")),
                "highest_severity": highest,
                "issue_count": str(len(ordered)),
                "issue_codes": "|".join(codes),
                "audit_evidence": " ; ".join(clean(row.get("evidence")) for row in ordered[:3] if clean(row.get("evidence"))),
                "recommended_operator_action": action,
                "allowed_decisions": "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only",
                "operator_decision": "",
                "identity_verified": "",
                "provider_player_id_verified": "",
                "approved_source_url": "",
                "secondary_source_url": "",
                "backfill_provider_player_id": "",
                "operator_notes": "",
                "operator_name": "",
                "reviewed_at_local": "",
                "issue_resolution_status": "",
                "copy_target": OPERATOR_INBOX,
                "approval_scope": "review_only_identity_resolution_for_local_draft_renders",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "review_only_policy": POLICY,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            SEVERITY_RANK.get(row["highest_severity"], 9),
            row["team_id"],
            row["display_name"],
            row["athlete_id"],
        ),
    )


def template_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if rows:
        return rows
    return [
        {
            field: ""
            for field in FIELDS
        }
    ]


def write_markdown(path: Path, report: Mapping[str, Any], rows: List[Mapping[str, str]]) -> None:
    lines = [
        "# HSD WNBA Athlete Identity Resolution Workflow v1",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        f"Status: **{report.get('status')}**",
        "",
        "## Policy",
        "",
        "- Review-only identity resolution workflow.",
        "- This does not approve, reject, move, fetch, publish, or mark athlete photos publish-ready.",
        "- Renderer eligibility can be restored only from a human-filled operator inbox row with source evidence.",
        "",
        "## Operator Inbox",
        "",
        f"- Copy reviewed rows into `{OPERATOR_INBOX}`.",
        "- Use `identity_verified_approved_for_review_renders` only after checking a trusted player/source page by eye.",
        "- Use `hold_identity` when the person, team, provider ID, or source proof is uncertain.",
        "- Use `revise_asset` when the row appears to be the wrong image or wrong crop.",
        "- Use `backfill_provider_id_only` when the photo should remain held but the provider ID can be source-backed.",
        "",
        "## Required Evidence For Renderer Eligibility",
        "",
        "- `identity_verified=yes`",
        "- `provider_player_id_verified=yes` or a clearly filled `backfill_provider_player_id`",
        "- `approved_source_url` from a free official/team/reputable public source",
        "- `operator_name`, `reviewed_at_local`, and `operator_notes` filled",
        "- all guardrail columns remain false",
        "",
        "## Priority Rows",
        "",
    ]
    if rows:
        for row in rows[:60]:
            lines.append(
                f"- {row.get('highest_severity')} | {row.get('display_name') or row.get('athlete_id')} | "
                f"{row.get('team_id')} | `{row.get('issue_codes')}` | action: {row.get('recommended_operator_action')}"
            )
        if len(rows) > 60:
            lines.append(f"- ...and {len(rows) - 60} more row(s) in the CSV.")
    else:
        lines.append("- No audit issue rows found. Re-run the identity audit first if this seems wrong.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(rows: List[Mapping[str, str]]) -> Dict[str, Any]:
    severity_counts: Dict[str, int] = {}
    for row in rows:
        severity = clean(row.get("highest_severity")) or "review"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    status = "resolution_queue_ready" if rows else "no_audit_issues_found"
    if severity_counts.get("critical"):
        status = "critical_identity_resolution_required"
    elif severity_counts.get("high"):
        status = "identity_resolution_required"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": status,
        "candidate_rows": len(rows),
        "severity_counts": dict(sorted(severity_counts.items())),
        "workflow_md": output_path(OUT_MD).as_posix(),
        "candidates_csv": output_path(OUT_CANDIDATES).as_posix(),
        "template_csv": output_path(OUT_TEMPLATE).as_posix(),
        "operator_inbox": OPERATOR_INBOX,
        "review_only": True,
        "policy": POLICY,
        "guardrails": {
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }


def main() -> None:
    audit = read_json(AUDIT_JSON)
    issues = audit.get("issues") if isinstance(audit.get("issues"), list) else []
    rows = summarize_issues([issue for issue in issues if isinstance(issue, dict)])
    report = build_report(rows)
    write_csv(OUT_CANDIDATES, rows, FIELDS)
    write_csv(OUT_TEMPLATE, template_rows(rows), FIELDS)
    write_json(OUT_MANIFEST, {"report": report, "rows": rows}, indent=2)
    write_markdown(output_path(OUT_MD), report, rows)
    print(json.dumps({"version": VERSION, "status": report["status"], "candidate_rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
