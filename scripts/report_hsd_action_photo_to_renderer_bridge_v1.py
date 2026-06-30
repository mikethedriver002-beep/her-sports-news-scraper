from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, read_csv, read_json, write_csv, write_json, write_text


VERSION = "hsd-action-photo-to-renderer-bridge-v1-review-only"
GENERATED_AT_UTC = "2026-06-30T00:00:00+00:00"
ROOT = Path("data/asset_registry/action_photo_candidates")
EXTERNAL_REVIEW_JSON = ROOT / "review_only_action_photo_external_research_return_review_v1.json"
EXTERNAL_REVIEW_CSV = ROOT / "review_only_action_photo_external_research_return_review_v1.csv"
IMPORT_REVIEW_JSON = ROOT / "review_only_action_photo_research_return_import_review_v1.json"
MANUAL_BRIDGE_JSON = ROOT / "review_only_action_photo_manual_research_bridge_v1.json"
RENDERER_TRIAGE_JSON = ROOT / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.json"
RENDERER_TRIAGE_CSV = ROOT / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.csv"
QUARANTINE_PREFLIGHT_JSON = ROOT / "review_only_action_photo_quarantine_preflight_v1.json"
QUARANTINE_PREFLIGHT_CSV = ROOT / "review_only_action_photo_quarantine_preflight_v1.csv"
HANDOFF_MANIFEST_JSON = Path("render_handoff_top_packet/handoff_manifest.json")
LATEST_HANDOFF_MANIFEST_JSON = Path("outputs/local/latest/files/render_handoff_top_packet/handoff_manifest.json")
OUT_MD = ROOT / "review_only_action_photo_to_renderer_bridge_v1.md"
OUT_CSV = ROOT / "review_only_action_photo_to_renderer_bridge_v1.csv"
OUT_JSON = ROOT / "review_only_action_photo_to_renderer_bridge_v1.json"
GUARDRAIL_FIELDS = [
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
BRIDGE_FIELDS = [
    "bridge_id",
    "bridge_status",
    "renderer_unblocked",
    "renderer_action_photo_status",
    "render_packet_id",
    "render_packet_title",
    "handoff_status",
    "hero_asset_required",
    "active_asset_stop_go",
    "active_logo_readiness_status",
    "external_review_rows",
    "external_return_rows",
    "external_missing_rows",
    "external_direct_image_hold_rows",
    "external_identity_vocab_mismatch_rows",
    "external_ready_rows",
    "external_generated_download_approval_rows",
    "import_review_rows",
    "import_rows_with_data",
    "import_ready_rows",
    "manual_bridge_rows",
    "manual_bridge_source_rows",
    "renderer_unblock_triage_rows",
    "quarantine_preflight_rows",
    "quarantine_ready_rows",
    "quarantine_lead_only_rows",
    "download_approved_yes_rows",
    "next_queue_id",
    "next_review_id",
    "next_candidate_page_url",
    "next_manual_action",
    "blocking_reasons",
    "operator_decision",
    "review_only",
    *GUARDRAIL_FIELDS,
]


def clean(value: object) -> str:
    return str(value or "").strip()


def as_int(value: object) -> int:
    try:
        return int(str(value).strip() or "0")
    except (TypeError, ValueError):
        return 0


def read_first_json(paths: Iterable[Path]) -> tuple[Dict[str, Any], str]:
    for path in paths:
        resolved = input_path(path)
        if resolved.exists():
            payload = read_json(path, {})
            if isinstance(payload, dict):
                return payload, path.as_posix()
    return {}, ""


def first_external_review_row(rows: List[Mapping[str, str]]) -> Mapping[str, str]:
    for row in rows:
        if clean(row.get("external_return_present")) == "yes":
            return row
    return rows[0] if rows else {}


def first_triage_row(rows: List[Mapping[str, str]]) -> Mapping[str, str]:
    for row in rows:
        if clean(row.get("manual_priority")) == "P0_renderer_unblock_first_return":
            return row
    return rows[0] if rows else {}


def first_ready_preflight_row(rows: List[Mapping[str, str]]) -> Mapping[str, str]:
    for row in rows:
        if clean(row.get("ready_for_human_download_decision")) == "yes":
            return row
    return {}


def handoff_packet(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    packet = manifest.get("packet")
    return packet if isinstance(packet, dict) else {}


def bridge_blocking_reasons(
    *,
    external_missing_rows: int,
    external_direct_image_hold_rows: int,
    external_identity_vocab_mismatch_rows: int,
    import_rows_with_data: int,
    import_ready_rows: int,
    quarantine_ready_rows: int,
    download_approved_yes_rows: int,
    active_asset_stop_go: str,
    hero_asset_required: str,
) -> List[str]:
    reasons: List[str] = []
    external_holds_are_active = quarantine_ready_rows == 0 and import_ready_rows == 0
    if external_holds_are_active and external_missing_rows:
        reasons.append("external_return_missing_rows")
    if external_holds_are_active and external_direct_image_hold_rows:
        reasons.append("external_return_direct_image_url_holds")
    if external_holds_are_active and external_identity_vocab_mismatch_rows:
        reasons.append("external_return_identity_vocabulary_holds")
    if import_rows_with_data == 0:
        reasons.append("shared_return_intake_has_no_human_pasted_rows")
    if import_ready_rows == 0:
        reasons.append("shared_import_review_has_no_ready_rows")
    if quarantine_ready_rows == 0:
        reasons.append("quarantine_preflight_has_no_ready_rows")
    if download_approved_yes_rows == 0:
        reasons.append("no_human_download_approved_rows")
    if active_asset_stop_go and active_asset_stop_go != "go_manual_asset_review_clear":
        reasons.append(f"render_handoff_asset_stop_go_{active_asset_stop_go}")
    if hero_asset_required and hero_asset_required != "approved_local_action_photo_candidate":
        reasons.append(f"renderer_hero_asset_required_{hero_asset_required}")
    return reasons


def bridge_row() -> Dict[str, str]:
    external_manifest = read_json(EXTERNAL_REVIEW_JSON, {})
    if not isinstance(external_manifest, dict):
        external_manifest = {}
    import_manifest = read_json(IMPORT_REVIEW_JSON, {})
    if not isinstance(import_manifest, dict):
        import_manifest = {}
    manual_manifest = read_json(MANUAL_BRIDGE_JSON, {})
    if not isinstance(manual_manifest, dict):
        manual_manifest = {}
    triage_manifest = read_json(RENDERER_TRIAGE_JSON, {})
    if not isinstance(triage_manifest, dict):
        triage_manifest = {}
    preflight_manifest = read_json(QUARANTINE_PREFLIGHT_JSON, {})
    if not isinstance(preflight_manifest, dict):
        preflight_manifest = {}
    handoff_manifest, handoff_manifest_path = read_first_json([HANDOFF_MANIFEST_JSON, LATEST_HANDOFF_MANIFEST_JSON])
    packet = handoff_packet(handoff_manifest)
    external_rows = read_csv(EXTERNAL_REVIEW_CSV)
    triage_rows = read_csv(RENDERER_TRIAGE_CSV)
    preflight_rows = read_csv(QUARANTINE_PREFLIGHT_CSV)
    external_first = first_external_review_row(external_rows)
    triage_first = first_triage_row(triage_rows)
    preflight_ready_first = first_ready_preflight_row(preflight_rows)

    external_missing_rows = as_int(external_manifest.get("missing_external_return_rows"))
    external_direct_image_hold_rows = as_int(external_manifest.get("direct_image_url_hold_rows"))
    external_identity_vocab_mismatch_rows = as_int(external_manifest.get("identity_vocabulary_mismatch_rows"))
    external_ready_rows = as_int(external_manifest.get("ready_for_later_human_download_decision_review_rows"))
    external_generated_download_approval_rows = as_int(external_manifest.get("generated_download_approval_rows"))
    import_rows_with_data = as_int(import_manifest.get("rows_with_research_return_data"))
    import_ready_rows = as_int(import_manifest.get("ready_for_later_human_download_decision_review_rows"))
    quarantine_ready_rows = as_int(preflight_manifest.get("ready_for_human_download_decision_rows"))
    download_approved_yes_rows = as_int(preflight_manifest.get("download_approved_yes_rows"))
    active_asset_stop_go = clean(packet.get("active_asset_stop_go"))
    hero_asset_required = clean(packet.get("hero_asset_required"))
    blocking_reasons = bridge_blocking_reasons(
        external_missing_rows=external_missing_rows,
        external_direct_image_hold_rows=external_direct_image_hold_rows,
        external_identity_vocab_mismatch_rows=external_identity_vocab_mismatch_rows,
        import_rows_with_data=import_rows_with_data,
        import_ready_rows=import_ready_rows,
        quarantine_ready_rows=quarantine_ready_rows,
        download_approved_yes_rows=download_approved_yes_rows,
        active_asset_stop_go=active_asset_stop_go,
        hero_asset_required=hero_asset_required,
    )
    renderer_unblocked = not blocking_reasons
    first_queue_id = clean(preflight_ready_first.get("candidate_queue_id")) or clean(external_first.get("candidate_queue_id")) or clean(triage_first.get("card_id"))
    first_review_id = clean(preflight_ready_first.get("preflight_id")) or clean(external_first.get("review_id")) or clean(triage_first.get("triage_id"))
    first_url = clean(preflight_ready_first.get("candidate_photo_url")) or clean(external_first.get("normalized_candidate_page_url")) or clean(triage_first.get("manual_source_lead"))
    if preflight_ready_first:
        next_action = (
            f"{first_queue_id}/{first_review_id} now has human-reviewed source, identity, rights, action-context, and use metadata. "
            "Next step is a separate human quarantine-download decision; keep download_approved=no until Mike explicitly edits the intake for quarantine-only download review."
        )
    elif first_queue_id:
        next_action = clean(external_first.get("manual_next_action")) or clean(triage_first.get("manual_next_action"))
        next_action = (
            f"Start with {first_queue_id}/{first_review_id}: {next_action} "
            "Then paste the human-reviewed source, identity, rights, action-context, and use metadata into the shared return intake; "
            "rerun import review, quarantine preflight, this bridge, and only then re-check renderer handoff."
        )
    else:
        next_action = (
            "Supply at least one human-reviewed action-photo return row, rerun import review and quarantine preflight, "
            "then re-check this renderer bridge."
        )
    return {
        "bridge_id": "APRB001",
        "bridge_status": "action_photo_renderer_blocked_manual_gate" if not renderer_unblocked else "action_photo_renderer_unblocked_for_manual_review",
        "renderer_unblocked": "yes" if renderer_unblocked else "no",
        "renderer_action_photo_status": "not_available_to_renderer" if not renderer_unblocked else "available_for_manual_renderer_review",
        "render_packet_id": clean(packet.get("packet_id")),
        "render_packet_title": clean(packet.get("title")),
        "handoff_status": clean(handoff_manifest.get("handoff_status")),
        "hero_asset_required": hero_asset_required,
        "active_asset_stop_go": active_asset_stop_go,
        "active_logo_readiness_status": clean(packet.get("active_logo_readiness_status")),
        "external_review_rows": str(as_int(external_manifest.get("review_rows"))),
        "external_return_rows": str(as_int(external_manifest.get("external_return_rows"))),
        "external_missing_rows": str(external_missing_rows),
        "external_direct_image_hold_rows": str(external_direct_image_hold_rows),
        "external_identity_vocab_mismatch_rows": str(external_identity_vocab_mismatch_rows),
        "external_ready_rows": str(external_ready_rows),
        "external_generated_download_approval_rows": str(external_generated_download_approval_rows),
        "import_review_rows": str(as_int(import_manifest.get("import_review_rows"))),
        "import_rows_with_data": str(import_rows_with_data),
        "import_ready_rows": str(import_ready_rows),
        "manual_bridge_rows": str(as_int(manual_manifest.get("bridge_rows"))),
        "manual_bridge_source_rows": str(as_int(manual_manifest.get("source_rows"))),
        "renderer_unblock_triage_rows": str(as_int(triage_manifest.get("triage_rows"))),
        "quarantine_preflight_rows": str(as_int(preflight_manifest.get("preflight_rows"))),
        "quarantine_ready_rows": str(quarantine_ready_rows),
        "quarantine_lead_only_rows": str(as_int(preflight_manifest.get("lead_only_rows"))),
        "download_approved_yes_rows": str(download_approved_yes_rows),
        "next_queue_id": first_queue_id,
        "next_review_id": first_review_id,
        "next_candidate_page_url": first_url,
        "next_manual_action": next_action,
        "blocking_reasons": "|".join(blocking_reasons),
        "operator_decision": "hold_renderer_action_photo_manual_gate" if not renderer_unblocked else "manual_renderer_recheck_allowed",
        "review_only": "true",
        "source_fetching": "false",
        "auto_source_enablement": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "_handoff_manifest_path": handoff_manifest_path,
    }


def validate_rows(rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if not clean(row.get("bridge_id")):
            issues.append({"row": str(index), "field": "bridge_id", "issue": "bridge_id_required"})
        renderer_unblocked = clean(row.get("renderer_unblocked"))
        operator_decision = clean(row.get("operator_decision"))
        if renderer_unblocked == "yes" and operator_decision != "manual_renderer_recheck_allowed":
            issues.append({"row": str(index), "field": "operator_decision", "issue": "unblocked_bridge_can_only_allow_manual_renderer_recheck"})
        if renderer_unblocked != "yes" and operator_decision != "hold_renderer_action_photo_manual_gate":
            issues.append({"row": str(index), "field": "operator_decision", "issue": "blocked_bridge_must_hold_until_human_gates_clear"})
        if clean(row.get("review_only")) != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "bridge_must_remain_review_only"})
        if as_int(row.get("external_ready_rows")) != 0:
            issues.append({"row": str(index), "field": "external_ready_rows", "issue": "bridge_must_not_surface_external_ready_rows"})
        if as_int(row.get("external_generated_download_approval_rows")) != 0:
            issues.append({"row": str(index), "field": "external_generated_download_approval_rows", "issue": "bridge_must_not_generate_download_approvals"})
        if as_int(row.get("download_approved_yes_rows")) != 0:
            issues.append({"row": str(index), "field": "download_approved_yes_rows", "issue": "bridge_must_not_approve_downloads"})
        for field in GUARDRAIL_FIELDS:
            if clean(row.get(field)) != "false":
                issues.append({"row": str(index), "field": field, "issue": "guardrail_field_invalid"})
    return issues


def render_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> str:
    row = rows[0] if rows else {}
    lines = [
        "# Review-Only Action Photo To Renderer Bridge v1",
        "",
        f"Generated: `{GENERATED_AT_UTC}`",
        "",
        "This bridge aggregates the external action-photo research return review, shared return import review, manual research bridge, renderer-unblock triage, quarantine preflight, and current top render handoff. It is artifact-only: it does not fetch sources, download images, approve candidates or assets, write headshots/cutouts/logos, create `.approved` markers, move files, enable sources, unblock renderer automatically, or publish.",
        "",
        "## Decision",
        "",
        f"- Bridge status: `{clean(row.get('bridge_status'))}`",
        f"- Renderer unblocked: `{clean(row.get('renderer_unblocked'))}`",
        f"- Operator decision: `{clean(row.get('operator_decision'))}`",
        f"- Render packet: `{clean(row.get('render_packet_title')) or 'missing'}`",
        f"- Active asset stop/go: `{clean(row.get('active_asset_stop_go')) or 'missing'}`",
        f"- Blocking reasons: `{clean(row.get('blocking_reasons')) or 'none'}`",
        "",
        "## Gate Rollup",
        "",
        f"- External returned/missing APQ rows: `{clean(row.get('external_return_rows'))}/{clean(row.get('external_missing_rows'))}`",
        f"- External direct-image/identity holds: `{clean(row.get('external_direct_image_hold_rows'))}/{clean(row.get('external_identity_vocab_mismatch_rows'))}`",
        f"- Shared import rows with data/ready rows: `{clean(row.get('import_rows_with_data'))}/{clean(row.get('import_ready_rows'))}`",
        f"- Manual bridge lanes/source rows: `{clean(row.get('manual_bridge_rows'))}/{clean(row.get('manual_bridge_source_rows'))}`",
        f"- Renderer triage rows: `{clean(row.get('renderer_unblock_triage_rows'))}`",
        f"- Quarantine ready/lead-only/download-approved rows: `{clean(row.get('quarantine_ready_rows'))}/{clean(row.get('quarantine_lead_only_rows'))}/{clean(row.get('download_approved_yes_rows'))}`",
        "",
        "## First Manual Action",
        "",
        f"- Queue/review: `{clean(row.get('next_queue_id')) or 'missing'}` / `{clean(row.get('next_review_id')) or 'missing'}`",
        f"- Candidate page lead: `{clean(row.get('next_candidate_page_url')) or 'missing'}`",
        f"- Next action: {clean(row.get('next_manual_action'))}",
        "",
        "## Validation",
        "",
        f"- Validation issues: `{len(issues)}`",
    ]
    if issues:
        lines += ["", "| Row | Field | Issue |", "| --- | --- | --- |"]
        for issue in issues:
            lines.append(f"| {clean(issue.get('row'))} | {clean(issue.get('field'))} | {clean(issue.get('issue'))} |")
    return "\n".join(lines) + "\n"


def manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> Dict[str, Any]:
    row = dict(rows[0]) if rows else {}
    handoff_manifest_path = clean(row.pop("_handoff_manifest_path", ""))
    return {
        "version": VERSION,
        "status": "action_photo_to_renderer_bridge_ready" if not issues else "action_photo_to_renderer_bridge_has_validation_issues",
        "generated_at_utc": GENERATED_AT_UTC,
        "bridge_rows": len(rows),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "handoff_manifest_path": handoff_manifest_path,
        "source_manifests": {
            "external_review": EXTERNAL_REVIEW_JSON.as_posix(),
            "import_review": IMPORT_REVIEW_JSON.as_posix(),
            "manual_bridge": MANUAL_BRIDGE_JSON.as_posix(),
            "renderer_unblock_triage": RENDERER_TRIAGE_JSON.as_posix(),
            "quarantine_preflight": QUARANTINE_PREFLIGHT_JSON.as_posix(),
            "render_handoff": handoff_manifest_path,
        },
        "bridge_status": clean(row.get("bridge_status")),
        "renderer_unblocked": clean(row.get("renderer_unblocked")) == "yes",
        "renderer_action_photo_status": clean(row.get("renderer_action_photo_status")),
        "render_packet_title": clean(row.get("render_packet_title")),
        "active_asset_stop_go": clean(row.get("active_asset_stop_go")),
        "external_review_rows": as_int(row.get("external_review_rows")),
        "external_return_rows": as_int(row.get("external_return_rows")),
        "external_missing_rows": as_int(row.get("external_missing_rows")),
        "external_direct_image_hold_rows": as_int(row.get("external_direct_image_hold_rows")),
        "external_identity_vocab_mismatch_rows": as_int(row.get("external_identity_vocab_mismatch_rows")),
        "external_ready_rows": as_int(row.get("external_ready_rows")),
        "external_generated_download_approval_rows": as_int(row.get("external_generated_download_approval_rows")),
        "import_review_rows": as_int(row.get("import_review_rows")),
        "import_rows_with_data": as_int(row.get("import_rows_with_data")),
        "import_ready_rows": as_int(row.get("import_ready_rows")),
        "manual_bridge_rows": as_int(row.get("manual_bridge_rows")),
        "manual_bridge_source_rows": as_int(row.get("manual_bridge_source_rows")),
        "renderer_unblock_triage_rows": as_int(row.get("renderer_unblock_triage_rows")),
        "quarantine_preflight_rows": as_int(row.get("quarantine_preflight_rows")),
        "quarantine_ready_rows": as_int(row.get("quarantine_ready_rows")),
        "quarantine_lead_only_rows": as_int(row.get("quarantine_lead_only_rows")),
        "download_approved_yes_rows": as_int(row.get("download_approved_yes_rows")),
        "next_queue_id": clean(row.get("next_queue_id")),
        "next_review_id": clean(row.get("next_review_id")),
        "next_candidate_page_url": clean(row.get("next_candidate_page_url")),
        "next_manual_action": clean(row.get("next_manual_action")),
        "blocking_reasons": [reason for reason in clean(row.get("blocking_reasons")).split("|") if reason],
        "operator_decision": clean(row.get("operator_decision")),
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
        "worksheet_md": OUT_MD.as_posix(),
        "worksheet_csv": OUT_CSV.as_posix(),
        "worksheet_json": OUT_JSON.as_posix(),
        "bridge_rows_detail": [row],
    }


def main() -> int:
    rows = [bridge_row()]
    issues = validate_rows(rows)
    write_csv(OUT_CSV, rows, BRIDGE_FIELDS, extrasaction="ignore")
    write_text(OUT_MD, render_markdown(rows, issues))
    write_json(OUT_JSON, manifest(rows, issues))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": "ok",
                "bridge_rows": len(rows),
                "bridge_status": rows[0]["bridge_status"],
                "renderer_unblocked": rows[0]["renderer_unblocked"],
                "validation_issue_count": len(issues),
            },
            indent=2,
        )
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
