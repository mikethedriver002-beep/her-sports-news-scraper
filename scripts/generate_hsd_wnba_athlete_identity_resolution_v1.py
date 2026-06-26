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
OUT_REVIEW_PACKET = "data/asset_registry/wnba/athlete_identity_review_packet.csv"
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

HOLD_FIRST_ISSUE_CODES = {
    "approved_marker_identity_mismatch",
    "approved_asset_file_missing",
    "approved_marker_missing",
    "provider_player_id_disagrees_with_source_artifact",
    "provider_player_id_reused_across_athletes",
    "exact_duplicate_approved_headshot_hash",
    "default_approval_requires_identity_recheck",
    "approved_asset_still_has_pending_match_review",
    "order_matched_headshot_requires_source_backed_identity_review",
    "approved_asset_lacks_official_roster_source",
}

DEFAULT_APPROVAL_ISSUE_CODES = {
    "default_approval_requires_identity_recheck",
    "blank_per_row_approval_decision",
}

REVIEW_PACKET_FIELDS = [
    "review_packet_id",
    "athlete_id",
    "display_name",
    "team_id",
    "provider_player_id",
    "asset_path",
    "approved_marker_path",
    "identity_review_status",
    "review_required",
    "identity_hold",
    "default_approval_present",
    "highest_severity",
    "issue_count",
    "hold_reason_codes",
    "focused_evidence",
    "source_check_url",
    "provider_player_page_hint",
    "operator_review_steps",
    "allowed_decisions",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "review_only_policy",
]


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


def wnba_player_page_hint(provider_player_id: str, display_name: str) -> str:
    provider_player_id = clean(provider_player_id)
    if not provider_player_id:
        return ""
    slug = re.sub(r"[^a-z0-9]+", "-", clean(display_name).lower()).strip("-")
    return f"https://www.wnba.com/player/{provider_player_id}/{slug}" if slug else f"https://www.wnba.com/player/{provider_player_id}"


def first_url_from_evidence(evidence: str) -> str:
    match = re.search(r"https?://[^\s;,]+", evidence)
    return match.group(0) if match else ""


def recommended_action_for(highest: str, codes: set[str]) -> str:
    if highest == "critical":
        return "hold_and_reconcile_identity_conflict_before_renderer_use"
    if codes & HOLD_FIRST_ISSUE_CODES:
        return "hold_identity_review_required_before_any_photo_renderer_use"
    if codes & {"missing_provider_player_id_in_image_registry", "blank_per_row_approval_decision"}:
        return "verify_identity_and_backfill_provider_id_if_source_supported"
    return "manual_identity_resolution_required"


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
        action = recommended_action_for(highest, set(codes))
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


def review_packet_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    packet_rows: List[Dict[str, str]] = []
    for row in rows:
        codes = {code for code in clean(row.get("issue_codes")).split("|") if code}
        default_approval = bool(codes & DEFAULT_APPROVAL_ISSUE_CODES)
        identity_hold = bool(codes & HOLD_FIRST_ISSUE_CODES) or clean(row.get("highest_severity")) == "critical"
        evidence = clean(row.get("audit_evidence"))
        source_check_url = first_url_from_evidence(evidence) or wnba_player_page_hint(
            clean(row.get("provider_player_id")),
            clean(row.get("display_name")),
        )
        packet_rows.append({
            "review_packet_id": clean(row.get("athlete_id")),
            "athlete_id": clean(row.get("athlete_id")),
            "display_name": clean(row.get("display_name")),
            "team_id": clean(row.get("team_id")),
            "provider_player_id": clean(row.get("provider_player_id")),
            "asset_path": clean(row.get("asset_path")),
            "approved_marker_path": clean(row.get("approved_marker_path")),
            "identity_review_status": "hold_identity_review_required" if identity_hold else "manual_identity_review_required",
            "review_required": "true",
            "identity_hold": "true" if identity_hold else "false",
            "default_approval_present": "true" if default_approval else "false",
            "highest_severity": clean(row.get("highest_severity")),
            "issue_count": clean(row.get("issue_count")),
            "hold_reason_codes": "|".join(sorted(codes & HOLD_FIRST_ISSUE_CODES)) or clean(row.get("issue_codes")),
            "focused_evidence": evidence,
            "source_check_url": source_check_url,
            "provider_player_page_hint": wnba_player_page_hint(
                clean(row.get("provider_player_id")),
                clean(row.get("display_name")),
            ),
            "operator_review_steps": "open_asset_and_marker; compare_to_official_player_or_team_source; choose_hold_or_verified_review_only_decision",
            "allowed_decisions": "hold_identity|revise_asset|backfill_provider_id_only|identity_verified_approved_for_review_renders",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "review_only_policy": POLICY,
        })
    return sorted(
        packet_rows,
        key=lambda row: (
            row["identity_hold"] != "true",
            row["default_approval_present"] != "true",
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


def write_markdown(path: Path, report: Mapping[str, Any], rows: List[Mapping[str, str]], packet_rows: List[Mapping[str, str]]) -> None:
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
        f"- Start with `{report.get('review_packet_csv')}` for hold-first identity review cues.",
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
        "## Focused Review Packet",
        "",
        f"- packet rows: {len(packet_rows)}",
        f"- identity hold rows: {report.get('identity_hold_rows')}",
        f"- default approval rows: {report.get('default_approval_rows')}",
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
    identity_hold_rows = 0
    default_approval_rows = 0
    for row in rows:
        severity = clean(row.get("highest_severity")) or "review"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        codes = {code for code in clean(row.get("issue_codes")).split("|") if code}
        if codes & HOLD_FIRST_ISSUE_CODES or severity == "critical":
            identity_hold_rows += 1
        if codes & DEFAULT_APPROVAL_ISSUE_CODES:
            default_approval_rows += 1
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
        "identity_hold_rows": identity_hold_rows,
        "default_approval_rows": default_approval_rows,
        "severity_counts": dict(sorted(severity_counts.items())),
        "workflow_md": output_path(OUT_MD).as_posix(),
        "candidates_csv": output_path(OUT_CANDIDATES).as_posix(),
        "review_packet_csv": output_path(OUT_REVIEW_PACKET).as_posix(),
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
    packet_rows = review_packet_rows(rows)
    report = build_report(rows)
    write_csv(OUT_CANDIDATES, rows, FIELDS)
    write_csv(OUT_REVIEW_PACKET, packet_rows, REVIEW_PACKET_FIELDS)
    write_csv(OUT_TEMPLATE, template_rows(rows), FIELDS)
    write_json(OUT_MANIFEST, {"report": report, "rows": rows, "review_packet_rows": packet_rows}, indent=2)
    write_markdown(output_path(OUT_MD), report, rows, packet_rows)
    print(json.dumps({
        "version": VERSION,
        "status": report["status"],
        "candidate_rows": len(rows),
        "identity_hold_rows": report["identity_hold_rows"],
        "default_approval_rows": report["default_approval_rows"],
    }, indent=2))


if __name__ == "__main__":
    main()
