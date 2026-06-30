from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import read_csv, read_json, write_csv, write_json, write_text


VERSION = "hsd-action-photo-manual-research-bridge-v1-review-only"
GENERATED_AT_UTC = "2026-06-29T00:00:00+00:00"
ROOT = Path("data/asset_registry/action_photo_candidates")
OUT_BRIDGE_MD = ROOT / "review_only_action_photo_manual_research_bridge_v1.md"
OUT_BRIDGE_CSV = ROOT / "review_only_action_photo_manual_research_bridge_v1.csv"
OUT_BRIDGE_JSON = ROOT / "review_only_action_photo_manual_research_bridge_v1.json"
OUT_FIRST_ACTION_CARDS_MD = ROOT / "review_only_action_photo_manual_first_action_cards_v1.md"
OUT_FIRST_ACTION_CARDS_CSV = ROOT / "review_only_action_photo_manual_first_action_cards_v1.csv"
OUT_FIRST_ACTION_CARDS_JSON = ROOT / "review_only_action_photo_manual_first_action_cards_v1.json"
OUT_RETURN_EVIDENCE_CHECKLIST_MD = ROOT / "review_only_action_photo_manual_return_evidence_checklist_v1.md"
OUT_RETURN_EVIDENCE_CHECKLIST_CSV = ROOT / "review_only_action_photo_manual_return_evidence_checklist_v1.csv"
OUT_RETURN_EVIDENCE_CHECKLIST_JSON = ROOT / "review_only_action_photo_manual_return_evidence_checklist_v1.json"
WOMENS_SOCCER_NEXT_MD = Path("data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md")
WOMENS_SOCCER_NEXT_CSV = Path("data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv")
WOMENS_SOCCER_NEXT_JSON = Path("data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.json")
HOCKEY_SOFTBALL_HANDOFF_MD = Path("data/asset_registry/hockey_softball_action_photo_research_handoff.md")
HOCKEY_SOFTBALL_HANDOFF_CSV = Path("data/asset_registry/hockey_softball_action_photo_research_handoff.csv")
HOCKEY_SOFTBALL_HANDOFF_JSON = Path("data/asset_registry/hockey_softball_action_photo_research_handoff.json")
ACTION_PHOTO_RETURN_INTAKE_CSV = ROOT / "review_only_action_photo_research_return_intake_v1.csv"
IMPORT_REVIEW_MD = ROOT / "review_only_action_photo_research_return_import_review_v1.md"
IMPORT_REVIEW_JSON = ROOT / "review_only_action_photo_research_return_import_review_v1.json"
FIELDS_TO_PASTE_NEXT = (
    "candidate_photo_url|evidence_url|evidence_summary|identity_anchor_url|source_url|"
    "entity_id|rights_class|identity_confidence|intended_review_only_use|operator_verify_required"
)
BRIDGE_FIELDS = [
    "bridge_rank",
    "bridge_lane",
    "source_scope",
    "source_board_md",
    "source_board_csv",
    "source_rows",
    "blank_source_url_rows",
    "blank_rights_class_rows",
    "blank_identity_confidence_rows",
    "candidate_ready_for_later_human_download_decision_review_rows",
    "shared_import_review_rows",
    "shared_import_rows_with_data",
    "shared_import_ready_rows",
    "shared_research_return_intake_file",
    "shared_import_review_file",
    "first_row_ref",
    "first_manual_source_lead",
    "fields_to_paste_next",
    "manual_first_action",
    "guardrail_note",
    "download_approved",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
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
]
FIRST_ACTION_CARD_FIELDS = [
    "card_id",
    "bridge_lane",
    "manual_priority",
    "source_scope",
    "open_source_board_md",
    "open_source_row_ref",
    "manual_source_lead",
    "paste_target_csv",
    "run_after_paste",
    "fields_to_fill",
    "fields_to_keep_blank_until_human_gate",
    "identity_evidence_needed",
    "rights_evidence_needed",
    "action_context_needed",
    "quarantine_gate_cue",
    "manual_next_action",
    "download_approved",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
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
]
RETURN_EVIDENCE_CHECKLIST_FIELDS = [
    "checklist_id",
    "card_id",
    "bridge_lane",
    "manual_priority",
    "source_scope",
    "open_source_row_ref",
    "manual_source_lead",
    "paste_target_csv",
    "run_after_paste",
    "candidate_url_check",
    "source_url_check",
    "evidence_url_check",
    "evidence_summary_check",
    "identity_anchor_check",
    "entity_id_check",
    "rights_class_check",
    "identity_confidence_check",
    "action_context_check",
    "crop_use_suitability_check",
    "intended_review_only_use_check",
    "operator_verify_check",
    "missing_until_human_paste",
    "keep_blank_until_human_gate",
    "candidate_ready_for_later_human_download_decision_review",
    "download_approved",
    "review_only",
    "approval_state_change",
    "candidate_state_change",
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
]


def clean(value: object) -> str:
    return str(value or "").strip()


def as_int(value: object) -> int:
    try:
        return int(str(value).strip() or "0")
    except (TypeError, ValueError):
        return 0


def is_yes(value: object) -> bool:
    return clean(value).lower() == ("y" + "es")


def first_nonblank(*values: object) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def row_ref(path: Path, row_number: int) -> str:
    return f"{path.as_posix()}#row={row_number}"


def shared_import_counts() -> Dict[str, int]:
    manifest = read_json(IMPORT_REVIEW_JSON, {})
    if not isinstance(manifest, dict):
        return {"rows": 0, "rows_with_data": 0, "ready_rows": 0}
    return {
        "rows": as_int(manifest.get("import_review_rows")),
        "rows_with_data": as_int(manifest.get("rows_with_research_return_data")),
        "ready_rows": as_int(manifest.get("ready_for_later_human_download_decision_review_rows")),
    }


def women_soccer_bridge_row(import_counts: Mapping[str, int]) -> Dict[str, str]:
    manifest = read_json(WOMENS_SOCCER_NEXT_JSON, {})
    rows = read_csv(WOMENS_SOCCER_NEXT_CSV)
    sample = rows[0] if rows else {}
    source_rows = as_int(manifest.get("research_next_rows")) if isinstance(manifest, dict) else len(rows)
    return bridge_row(
        bridge_rank="01",
        bridge_lane="women_soccer_action_photo",
        source_scope="NWSL/USWNT/europe_top_flight athlete action-photo leads",
        source_board_md=WOMENS_SOCCER_NEXT_MD,
        source_board_csv=WOMENS_SOCCER_NEXT_CSV,
        source_rows=source_rows,
        blank_source_url_rows=as_int(manifest.get("blank_source_url_rows")) if isinstance(manifest, dict) else count_blank(rows, "source_url"),
        blank_rights_class_rows=as_int(manifest.get("blank_rights_class_rows")) if isinstance(manifest, dict) else count_blank(rows, "rights_class"),
        blank_identity_confidence_rows=as_int(manifest.get("blank_identity_confidence_rows")) if isinstance(manifest, dict) else count_blank(rows, "identity_confidence"),
        ready_rows=as_int(manifest.get("candidate_ready_for_later_human_download_decision_review_rows")) if isinstance(manifest, dict) else count_ready(rows),
        first_row_ref=row_ref(WOMENS_SOCCER_NEXT_CSV, 2) if rows else "",
        first_manual_source_lead=first_nonblank(sample.get("source_candidate_url"), sample.get("source_domain")),
        manual_first_action=(
            "Open the women's soccer action-photo research-next board, choose the first row with a usable manual source lead, "
            "then paste human-reviewed candidate/evidence/source/identity metadata into the shared action-photo return intake."
        ),
        import_counts=import_counts,
    )


def hockey_softball_bridge_row(import_counts: Mapping[str, int]) -> Dict[str, str]:
    manifest = read_json(HOCKEY_SOFTBALL_HANDOFF_JSON, {})
    rows = read_csv(HOCKEY_SOFTBALL_HANDOFF_CSV)
    sample = rows[0] if rows else {}
    source_rows = as_int(manifest.get("rows")) if isinstance(manifest, dict) else len(rows)
    return bridge_row(
        bridge_rank="02",
        bridge_lane="hockey_softball_action_photo",
        source_scope="PWHL/AUSL manual action-photo source handoff",
        source_board_md=HOCKEY_SOFTBALL_HANDOFF_MD,
        source_board_csv=HOCKEY_SOFTBALL_HANDOFF_CSV,
        source_rows=source_rows,
        blank_source_url_rows=as_int(manifest.get("blank_source_url_rows")) if isinstance(manifest, dict) else count_blank(rows, "source_url"),
        blank_rights_class_rows=as_int(manifest.get("blank_rights_class_rows")) if isinstance(manifest, dict) else count_blank(rows, "rights_class"),
        blank_identity_confidence_rows=as_int(manifest.get("blank_identity_confidence_rows")) if isinstance(manifest, dict) else count_blank(rows, "identity_confidence"),
        ready_rows=as_int(manifest.get("later_human_download_decision_review_eligible_rows")) if isinstance(manifest, dict) else count_ready(rows),
        first_row_ref=row_ref(HOCKEY_SOFTBALL_HANDOFF_CSV, 2) if rows else "",
        first_manual_source_lead=first_nonblank(sample.get("source_search_macro"), sample.get("source_lane")),
        manual_first_action=(
            "Open the hockey/softball action-photo handoff row and its source-map ref, collect candidate/evidence/source/identity metadata manually, "
            "then paste the completed human-reviewed return into the shared action-photo return intake."
        ),
        import_counts=import_counts,
    )


def count_blank(rows: List[Mapping[str, str]], field: str) -> int:
    return sum(1 for row in rows if not clean(row.get(field)))


def count_ready(rows: List[Mapping[str, str]]) -> int:
    return sum(1 for row in rows if clean(row.get("candidate_ready_for_later_human_download_decision_review")).lower() == "yes")


def bridge_row(
    *,
    bridge_rank: str,
    bridge_lane: str,
    source_scope: str,
    source_board_md: Path,
    source_board_csv: Path,
    source_rows: int,
    blank_source_url_rows: int,
    blank_rights_class_rows: int,
    blank_identity_confidence_rows: int,
    ready_rows: int,
    first_row_ref: str,
    first_manual_source_lead: str,
    manual_first_action: str,
    import_counts: Mapping[str, int],
) -> Dict[str, str]:
    return {
        "bridge_rank": bridge_rank,
        "bridge_lane": bridge_lane,
        "source_scope": source_scope,
        "source_board_md": source_board_md.as_posix(),
        "source_board_csv": source_board_csv.as_posix(),
        "source_rows": str(source_rows),
        "blank_source_url_rows": str(blank_source_url_rows),
        "blank_rights_class_rows": str(blank_rights_class_rows),
        "blank_identity_confidence_rows": str(blank_identity_confidence_rows),
        "candidate_ready_for_later_human_download_decision_review_rows": str(ready_rows),
        "shared_import_review_rows": str(as_int(import_counts.get("rows"))),
        "shared_import_rows_with_data": str(as_int(import_counts.get("rows_with_data"))),
        "shared_import_ready_rows": str(as_int(import_counts.get("ready_rows"))),
        "shared_research_return_intake_file": ACTION_PHOTO_RETURN_INTAKE_CSV.as_posix(),
        "shared_import_review_file": IMPORT_REVIEW_MD.as_posix(),
        "first_row_ref": first_row_ref,
        "first_manual_source_lead": first_manual_source_lead,
        "fields_to_paste_next": FIELDS_TO_PASTE_NEXT,
        "manual_first_action": manual_first_action,
        "guardrail_note": "Review-only manual bridge; no source fetching, downloads, approvals, asset writes, marker writes, file movement, or publishing.",
        "download_approved": "no",
        "review_only": "true",
        "approval_state_change": "false",
        "candidate_state_change": "false",
        "source_fetching": "false",
        "auto_source_enablement": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def bridge_rows() -> List[Dict[str, str]]:
    import_counts = shared_import_counts()
    return [women_soccer_bridge_row(import_counts), hockey_softball_bridge_row(import_counts)]


def validate_rows(rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if not clean(row.get("bridge_rank")):
            issues.append({"row": str(index), "field": "bridge_rank", "issue": "bridge_rank_required"})
        if not clean(row.get("source_board_md")):
            issues.append({"row": str(index), "field": "source_board_md", "issue": "source_board_required"})
        if clean(row.get("download_approved")) != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_bridge_must_not_approve_downloads"})
        for field in [
            "review_only",
            "approval_state_change",
            "candidate_state_change",
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
            expected = "true" if field == "review_only" else "false"
            if clean(row.get(field)) != expected:
                issues.append({"row": str(index), "field": field, "issue": "guardrail_field_invalid"})
    return issues


def first_action_card_rows(rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        lane = clean(row.get("bridge_lane"))
        cards.append(
            {
                "card_id": f"APFAC{index:02d}",
                "bridge_lane": lane,
                "manual_priority": "P0_first_manual_return",
                "source_scope": clean(row.get("source_scope")),
                "open_source_board_md": clean(row.get("source_board_md")),
                "open_source_row_ref": clean(row.get("first_row_ref")),
                "manual_source_lead": clean(row.get("first_manual_source_lead")),
                "paste_target_csv": ACTION_PHOTO_RETURN_INTAKE_CSV.as_posix(),
                "run_after_paste": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_action_photo_research_return_import_stub_v1.py",
                "fields_to_fill": FIELDS_TO_PASTE_NEXT,
                "fields_to_keep_blank_until_human_gate": "download_approved|quarantine_target_hint|operator_decision|operator_notes",
                "identity_evidence_needed": "identity anchor page or official roster/profile plus source caption/event context",
                "rights_evidence_needed": "rights_class must be a conservative review category from human source review, not clearance",
                "action_context_needed": "candidate page or evidence page must show game/action context, not headshot/roster-only use",
                "quarantine_gate_cue": "Only a later human-edited intake row with all required metadata can reach quarantine-only download decision review; this card does not download or approve.",
                "manual_next_action": clean(row.get("manual_first_action")),
                "download_approved": "no",
                "review_only": "true",
                "approval_state_change": "false",
                "candidate_state_change": "false",
                "source_fetching": "false",
                "auto_source_enablement": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    return cards


def validate_first_action_cards(rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if not clean(row.get("card_id")):
            issues.append({"row": str(index), "field": "card_id", "issue": "card_id_required"})
        if not clean(row.get("open_source_row_ref")):
            issues.append({"row": str(index), "field": "open_source_row_ref", "issue": "source_row_ref_required"})
        if clean(row.get("download_approved")) != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_card_must_not_approve_downloads"})
        for field in [
            "review_only",
            "approval_state_change",
            "candidate_state_change",
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
            expected = "true" if field == "review_only" else "false"
            if clean(row.get(field)) != expected:
                issues.append({"row": str(index), "field": field, "issue": "guardrail_field_invalid"})
    return issues


def return_evidence_checklist_rows(card_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for index, card in enumerate(card_rows, start=1):
        rows.append(
            {
                "checklist_id": f"APFEC{index:02d}",
                "card_id": clean(card.get("card_id")),
                "bridge_lane": clean(card.get("bridge_lane")),
                "manual_priority": clean(card.get("manual_priority")),
                "source_scope": clean(card.get("source_scope")),
                "open_source_row_ref": clean(card.get("open_source_row_ref")),
                "manual_source_lead": clean(card.get("manual_source_lead")),
                "paste_target_csv": ACTION_PHOTO_RETURN_INTAKE_CSV.as_posix(),
                "run_after_paste": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_action_photo_research_return_import_stub_v1.py",
                "candidate_url_check": "human_paste_candidate_page_or_candidate_url_only_after_manual_review",
                "source_url_check": "human_paste_source_url_from reviewed page; leave blank until verified",
                "evidence_url_check": "human_paste_evidence_page_url_with caption/event/source context",
                "evidence_summary_check": "human_summarize action moment, teams/event, jersey/player context, and why it is not headshot-only",
                "identity_anchor_check": "human_paste official roster/profile or equivalent identity anchor",
                "entity_id_check": "human_paste matching entity_id from current registry/intake row",
                "rights_class_check": "human_select conservative review category; this is not clearance",
                "identity_confidence_check": "human_set strong_context or equivalent only when source/evidence supports identity",
                "action_context_check": "human_confirm game/action context and reject static/headshot-only candidates",
                "crop_use_suitability_check": "human_note whether crop/composition can support future review-only render testing",
                "intended_review_only_use_check": "human_paste intended review-only use before any later gate review",
                "operator_verify_check": "operator verification should stay required until a human completes source, identity, rights, and action/crop checks",
                "missing_until_human_paste": FIELDS_TO_PASTE_NEXT,
                "keep_blank_until_human_gate": "download_approved|quarantine_target_hint|operator_decision|operator_notes",
                "candidate_ready_for_later_human_download_decision_review": "no",
                "download_approved": "no",
                "review_only": "true",
                "approval_state_change": "false",
                "candidate_state_change": "false",
                "source_fetching": "false",
                "auto_source_enablement": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    return rows


def validate_return_evidence_checklist(rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        if not clean(row.get("checklist_id")):
            issues.append({"row": str(index), "field": "checklist_id", "issue": "checklist_id_required"})
        if not clean(row.get("card_id")):
            issues.append({"row": str(index), "field": "card_id", "issue": "card_id_required"})
        if clean(row.get("candidate_ready_for_later_human_download_decision_review")) != "no":
            issues.append({"row": str(index), "field": "candidate_ready_for_later_human_download_decision_review", "issue": "generated_checklist_must_not_mark_ready"})
        if clean(row.get("download_approved")) != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_checklist_must_not_approve_downloads"})
        for field in [
            "review_only",
            "approval_state_change",
            "candidate_state_change",
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
            expected = "true" if field == "review_only" else "false"
            if clean(row.get(field)) != expected:
                issues.append({"row": str(index), "field": field, "issue": "guardrail_field_invalid"})
    return issues


def render_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> str:
    source_rows = sum(as_int(row.get("source_rows")) for row in rows)
    ready_rows = sum(as_int(row.get("candidate_ready_for_later_human_download_decision_review_rows")) for row in rows)
    import_rows = as_int(rows[0].get("shared_import_review_rows")) if rows else 0
    import_rows_with_data = as_int(rows[0].get("shared_import_rows_with_data")) if rows else 0
    lines = [
        "# Review-Only Action Photo Manual Research Bridge v1",
        "",
        f"Generated: `{GENERATED_AT_UTC}`",
        "",
        "This bridge connects the existing women's soccer and hockey/softball action-photo boards to the shared research return intake. It is artifact-only: it does not fetch sources, download images, approve candidates/assets, write headshots, create marker files, move files, or publish.",
        "",
        "## Summary",
        "",
        f"- Bridge lanes: `{len(rows)}`",
        f"- Source lead rows to work manually: `{source_rows}`",
        f"- Shared import review rows: `{import_rows}`",
        f"- Shared import rows with pasted data: `{import_rows_with_data}`",
        f"- Rows ready only for later human download-decision review: `{ready_rows}`",
        f"- Generated download approvals: `{generated_download_approval_rows(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        "",
        "## Manual Bridge",
        "",
        "| Rank | Lane | Source Rows | Blank Source | Blank Rights | Blank Identity | Import Data | First Row | Manual First Action |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {rank} | {lane} | {source_rows} | {blank_source} | {blank_rights} | {blank_identity} | {import_data} | `{first_ref}` | {action} |".format(
                rank=clean(row.get("bridge_rank")),
                lane=clean(row.get("bridge_lane")),
                source_rows=clean(row.get("source_rows")),
                blank_source=clean(row.get("blank_source_url_rows")),
                blank_rights=clean(row.get("blank_rights_class_rows")),
                blank_identity=clean(row.get("blank_identity_confidence_rows")),
                import_data=clean(row.get("shared_import_rows_with_data")),
                first_ref=clean(row.get("first_row_ref")),
                action=clean(row.get("manual_first_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def render_first_action_cards_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> str:
    lines = [
        "# Review-Only Action Photo Manual First-Action Cards v1",
        "",
        f"Generated: `{GENERATED_AT_UTC}`",
        "",
        "These cards turn the bridge rows into the next two manual actions. This artifact does not fetch sources, download images, approve candidates/assets, write headshots, create marker files, move files, or publish.",
        "",
        "## Summary",
        "",
        f"- First-action cards: `{len(rows)}`",
        f"- Generated download approvals: `{generated_download_approval_rows(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        "",
        "## Cards",
        "",
    ]
    for row in rows:
        lines += [
            f"### {clean(row.get('card_id'))} - {clean(row.get('bridge_lane'))}",
            "",
            f"- Open source row: `{clean(row.get('open_source_row_ref'))}`",
            f"- Manual source lead: `{clean(row.get('manual_source_lead'))}`",
            f"- Paste target: `{clean(row.get('paste_target_csv'))}`",
            f"- Fields to fill: `{clean(row.get('fields_to_fill'))}`",
            f"- Keep blank until human gate: `{clean(row.get('fields_to_keep_blank_until_human_gate'))}`",
            f"- Run after paste: `{clean(row.get('run_after_paste'))}`",
            f"- Identity evidence needed: {clean(row.get('identity_evidence_needed'))}",
            f"- Rights evidence needed: {clean(row.get('rights_evidence_needed'))}",
            f"- Action context needed: {clean(row.get('action_context_needed'))}",
            f"- Quarantine gate cue: {clean(row.get('quarantine_gate_cue'))}",
            f"- Manual next action: {clean(row.get('manual_next_action'))}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_return_evidence_checklist_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> str:
    lines = [
        "# Review-Only Action Photo Manual Return Evidence Checklist v1",
        "",
        f"Generated: `{GENERATED_AT_UTC}`",
        "",
        "This checklist is keyed to APFAC manual first-action cards and tells the operator what to verify before pasting a candidate return. It does not fetch sources, inspect URLs, download images, approve candidates/assets, write headshots, create marker files, move files, or publish.",
        "",
        "## Summary",
        "",
        f"- Checklist rows: `{len(rows)}`",
        f"- Generated ready rows: `{sum(1 for row in rows if clean(row.get('candidate_ready_for_later_human_download_decision_review')) == ('y' + 'es'))}`",
        f"- Generated download approvals: `{generated_download_approval_rows(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        "",
        "## Checklist",
        "",
    ]
    for row in rows:
        lines += [
            f"### {clean(row.get('checklist_id'))} - {clean(row.get('card_id'))}",
            "",
            f"- Source row: `{clean(row.get('open_source_row_ref'))}`",
            f"- Manual source lead: `{clean(row.get('manual_source_lead'))}`",
            f"- Paste target: `{clean(row.get('paste_target_csv'))}`",
            f"- Candidate/source/evidence checks: `{clean(row.get('candidate_url_check'))}` / `{clean(row.get('source_url_check'))}` / `{clean(row.get('evidence_url_check'))}`",
            f"- Identity checks: `{clean(row.get('identity_anchor_check'))}` / `{clean(row.get('entity_id_check'))}` / `{clean(row.get('identity_confidence_check'))}`",
            f"- Rights check: `{clean(row.get('rights_class_check'))}`",
            f"- Action/crop checks: `{clean(row.get('action_context_check'))}` / `{clean(row.get('crop_use_suitability_check'))}`",
            f"- Missing until human paste: `{clean(row.get('missing_until_human_paste'))}`",
            f"- Keep blank until human gate: `{clean(row.get('keep_blank_until_human_gate'))}`",
            f"- Run after paste: `{clean(row.get('run_after_paste'))}`",
            "",
        ]
    return "\n".join(lines) + "\n"


def generated_download_approval_rows(rows: List[Mapping[str, str]]) -> int:
    return sum(1 for row in rows if is_yes(row.get("download_approved")))


def manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "status": "action_photo_manual_research_bridge_ready" if not issues else "action_photo_manual_research_bridge_has_validation_issues",
        "generated_at_utc": GENERATED_AT_UTC,
        "bridge_rows": len(rows),
        "source_rows": sum(as_int(row.get("source_rows")) for row in rows),
        "womens_soccer_source_rows": as_int(rows[0].get("source_rows")) if rows else 0,
        "hockey_softball_source_rows": as_int(rows[1].get("source_rows")) if len(rows) > 1 else 0,
        "shared_import_review_rows": as_int(rows[0].get("shared_import_review_rows")) if rows else 0,
        "shared_import_rows_with_data": as_int(rows[0].get("shared_import_rows_with_data")) if rows else 0,
        "shared_import_ready_rows": as_int(rows[0].get("shared_import_ready_rows")) if rows else 0,
        "candidate_ready_for_later_human_download_decision_review_rows": sum(
            as_int(row.get("candidate_ready_for_later_human_download_decision_review_rows")) for row in rows
        ),
        "generated_download_approval_rows": generated_download_approval_rows(rows),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "shared_research_return_intake_file": ACTION_PHOTO_RETURN_INTAKE_CSV.as_posix(),
        "shared_import_review_file": IMPORT_REVIEW_MD.as_posix(),
        "worksheet_md": OUT_BRIDGE_MD.as_posix(),
        "worksheet_csv": OUT_BRIDGE_CSV.as_posix(),
        "worksheet_json": OUT_BRIDGE_JSON.as_posix(),
        "first_action_cards_md": OUT_FIRST_ACTION_CARDS_MD.as_posix(),
        "first_action_cards_csv": OUT_FIRST_ACTION_CARDS_CSV.as_posix(),
        "first_action_cards_json": OUT_FIRST_ACTION_CARDS_JSON.as_posix(),
        "return_evidence_checklist_md": OUT_RETURN_EVIDENCE_CHECKLIST_MD.as_posix(),
        "return_evidence_checklist_csv": OUT_RETURN_EVIDENCE_CHECKLIST_CSV.as_posix(),
        "return_evidence_checklist_json": OUT_RETURN_EVIDENCE_CHECKLIST_JSON.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "bridge_rows_detail": rows,
    }


def first_action_cards_manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "status": "action_photo_manual_first_action_cards_ready" if not issues else "action_photo_manual_first_action_cards_have_validation_issues",
        "generated_at_utc": GENERATED_AT_UTC,
        "first_action_cards": len(rows),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "generated_download_approval_rows": generated_download_approval_rows(rows),
        "shared_research_return_intake_file": ACTION_PHOTO_RETURN_INTAKE_CSV.as_posix(),
        "shared_import_review_file": IMPORT_REVIEW_MD.as_posix(),
        "run_after_paste": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_action_photo_research_return_import_stub_v1.py",
        "worksheet_md": OUT_FIRST_ACTION_CARDS_MD.as_posix(),
        "worksheet_csv": OUT_FIRST_ACTION_CARDS_CSV.as_posix(),
        "worksheet_json": OUT_FIRST_ACTION_CARDS_JSON.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "first_action_cards_detail": rows,
    }


def return_evidence_checklist_manifest(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]]) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "status": "action_photo_manual_return_evidence_checklist_ready" if not issues else "action_photo_manual_return_evidence_checklist_has_validation_issues",
        "generated_at_utc": GENERATED_AT_UTC,
        "checklist_rows": len(rows),
        "validation_issue_count": len(issues),
        "validation_issues": issues,
        "generated_ready_rows": sum(
            1 for row in rows if clean(row.get("candidate_ready_for_later_human_download_decision_review")) == ("y" + "es")
        ),
        "generated_download_approval_rows": generated_download_approval_rows(rows),
        "shared_research_return_intake_file": ACTION_PHOTO_RETURN_INTAKE_CSV.as_posix(),
        "shared_import_review_file": IMPORT_REVIEW_MD.as_posix(),
        "run_after_paste": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_action_photo_research_return_import_stub_v1.py",
        "worksheet_md": OUT_RETURN_EVIDENCE_CHECKLIST_MD.as_posix(),
        "worksheet_csv": OUT_RETURN_EVIDENCE_CHECKLIST_CSV.as_posix(),
        "worksheet_json": OUT_RETURN_EVIDENCE_CHECKLIST_JSON.as_posix(),
        "review_only": True,
        "approval_state_change": False,
        "candidate_state_change": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_approval": False,
        "auto_publish": False,
        "move_files": False,
        "paid_apis": False,
        "checklist_detail": rows,
    }


def main() -> int:
    rows = bridge_rows()
    issues = validate_rows(rows)
    card_rows = first_action_card_rows(rows)
    card_issues = validate_first_action_cards(card_rows)
    checklist_rows = return_evidence_checklist_rows(card_rows)
    checklist_issues = validate_return_evidence_checklist(checklist_rows)
    write_csv(OUT_BRIDGE_CSV, rows, BRIDGE_FIELDS)
    write_text(OUT_BRIDGE_MD, render_markdown(rows, issues))
    write_json(OUT_BRIDGE_JSON, manifest(rows, issues))
    write_csv(OUT_FIRST_ACTION_CARDS_CSV, card_rows, FIRST_ACTION_CARD_FIELDS)
    write_text(OUT_FIRST_ACTION_CARDS_MD, render_first_action_cards_markdown(card_rows, card_issues))
    write_json(OUT_FIRST_ACTION_CARDS_JSON, first_action_cards_manifest(card_rows, card_issues))
    write_csv(OUT_RETURN_EVIDENCE_CHECKLIST_CSV, checklist_rows, RETURN_EVIDENCE_CHECKLIST_FIELDS)
    write_text(OUT_RETURN_EVIDENCE_CHECKLIST_MD, render_return_evidence_checklist_markdown(checklist_rows, checklist_issues))
    write_json(OUT_RETURN_EVIDENCE_CHECKLIST_JSON, return_evidence_checklist_manifest(checklist_rows, checklist_issues))
    total_issues = len(issues) + len(card_issues) + len(checklist_issues)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": "ok",
                "bridge_rows": len(rows),
                "first_action_cards": len(card_rows),
                "return_evidence_checklist_rows": len(checklist_rows),
                "validation_issue_count": total_issues,
            },
            indent=2,
        )
    )
    return 1 if total_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
