from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_csv, write_json, write_text


VERSION = "hsd-action-photo-candidate-intake-v1-review-only"
TEMPLATE_CREATED_AT_UTC = "2026-06-28T00:00:00+00:00"
ROOT = Path("data/asset_registry/action_photo_candidates")
OUT_CSV = output_path(ROOT / "review_only_action_photo_candidate_intake.csv")
OUT_MD = output_path(ROOT / "review_only_action_photo_candidate_intake.md")
OUT_JSON = output_path(ROOT / "review_only_action_photo_candidate_intake.json")
OUT_TAXONOMY_MD = output_path(ROOT / "review_only_action_photo_candidate_taxonomy.md")
OUT_TAXONOMY_JSON = output_path(ROOT / "review_only_action_photo_candidate_taxonomy.json")
OUT_CHECKLIST_MD = output_path(ROOT / "review_only_action_photo_human_review_checklist.md")
OUT_SOURCE_MAP_CSV = output_path(ROOT / "review_only_action_photo_source_map_template.csv")
OUT_SOURCE_MAP_MD = output_path(ROOT / "review_only_action_photo_source_map_template.md")
OUT_ENTITY_SOURCE_MAP_CSV = output_path(ROOT / "review_only_action_photo_sport_entity_source_map.csv")
OUT_ENTITY_SOURCE_MAP_MD = output_path(ROOT / "review_only_action_photo_sport_entity_source_map.md")
OUT_ENTITY_SOURCE_MAP_JSON = output_path(ROOT / "review_only_action_photo_sport_entity_source_map.json")
OUT_WOMENS_SOCCER_STARTER_CSV = output_path(ROOT / "review_only_womens_soccer_action_photo_starter_intake.csv")
OUT_WOMENS_SOCCER_STARTER_MD = output_path(ROOT / "review_only_womens_soccer_action_photo_starter_intake.md")
OUT_WOMENS_SOCCER_STARTER_JSON = output_path(ROOT / "review_only_womens_soccer_action_photo_starter_intake.json")
OUT_EXTERNAL_RESEARCH_SOURCE_MAP_CSV = output_path(ROOT / "review_only_action_photo_external_research_source_map.csv")
OUT_EXTERNAL_RESEARCH_SOURCE_MAP_MD = output_path(ROOT / "review_only_action_photo_external_research_source_map.md")
OUT_EXTERNAL_RESEARCH_SOURCE_MAP_JSON = output_path(ROOT / "review_only_action_photo_external_research_source_map.json")
OUT_CANDIDATE_QUEUE_CSV = output_path(ROOT / "review_only_action_photo_candidate_queue_v1.csv")
OUT_CANDIDATE_QUEUE_MD = output_path(ROOT / "review_only_action_photo_candidate_queue_v1.md")
OUT_CANDIDATE_QUEUE_JSON = output_path(ROOT / "review_only_action_photo_candidate_queue_v1.json")
OUT_RESEARCH_PACKET_CSV = output_path(ROOT / "review_only_action_photo_candidate_research_packet_v1.csv")
OUT_RESEARCH_PACKET_MD = output_path(ROOT / "review_only_action_photo_candidate_research_packet_v1.md")
OUT_RESEARCH_PACKET_JSON = output_path(ROOT / "review_only_action_photo_candidate_research_packet_v1.json")
OUT_RESEARCH_RETURN_INTAKE_CSV = output_path(ROOT / "review_only_action_photo_research_return_intake_v1.csv")
OUT_RESEARCH_RETURN_INTAKE_MD = output_path(ROOT / "review_only_action_photo_research_return_intake_v1.md")
OUT_RESEARCH_RETURN_INTAKE_JSON = output_path(ROOT / "review_only_action_photo_research_return_intake_v1.json")
QUARANTINE_ROOT = "data/assets/quarantine/review_only_candidates"
REQUIRED_DOWNLOAD_FIELDS = [
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
]
SOURCE_CATEGORIES = {
    "official_team_gallery": "Official team/club gallery, recap, or photo surface.",
    "official_league_gallery": "Official league gallery, recap, or photo surface.",
    "official_federation_or_tournament": "Official federation, tournament, NCAA, or championship photo surface.",
    "verification_only_player_page": "Roster, player profile, media guide, or stats page used only as an identity anchor.",
    "editorial_wire": "Getty, AP, Reuters, Imagn, or similar editorial marketplace lead.",
    "reputable_newsroom_gallery": "Reputable newsroom, local beat, regional broadcaster, or public media gallery.",
    "official_social": "Official athlete, team, league, federation, or tournament social post.",
    "third_party_creator_public": "Independent photographer, portfolio, Flickr, SmugMug, or creator-owned public lead.",
    "gray_area_public_lead": "Fan, repost, archive, forum, or weak-provenance public lead for parking only.",
}
RIGHTS_CLASSES = {
    "official_review_needed": "Official source found; no publish-ready rights are assumed.",
    "official_partner_licensed_manual_review": "Official surface using partner/licensed imagery such as Getty or similar.",
    "editorial_wire_rights_sensitive": "Editorial marketplace or wire source; licensing review is mandatory.",
    "newsroom_photo_rights_sensitive": "Newsroom or beat outlet image; rights/provenance review is mandatory.",
    "social_uncleared": "Social discovery lead; rights remain unclear.",
    "third_party_creator_uncleared": "Independent creator lead; provenance and permission remain unclear.",
    "gray_area_lead_only": "Weak chain of title; review-only lead, not a download candidate.",
    "reject_do_not_pursue": "Restricted, deceptive, missing provenance, or clearly unusable.",
}
IDENTITY_CONFIDENCE = {
    "confirmed_official": "Caption/source identity and official roster/player anchor match cleanly.",
    "strong_context": "Jersey, team, event, teammate/opponent context strongly align.",
    "probable": "Likely but incomplete identity match.",
    "weak": "Low-confidence match due to obstructed, old, low-res, or thin evidence.",
    "mismatch_or_unknown": "Conflicting details or insufficient evidence.",
}
MANUAL_REVIEW_STATUSES = {
    "not_reviewed": "Generated/default state; no human decision yet.",
    "pending_more_info": "Human needs more identity, event, rights, or source evidence.",
    "escalated_rights_review": "Needs specialized rights/licensing review.",
    "rejected": "Do not pursue this lead further.",
    "approved_for_download": "Human approved quarantine download only; not asset approval.",
}
BLOCKED_DOWNLOAD_RIGHTS = {
    "social_uncleared",
    "third_party_creator_uncleared",
    "gray_area_lead_only",
    "reject_do_not_pursue",
}
DOWNLOAD_READY_IDENTITY = {"strong_context", "confirmed_official"}
CREDIT_NOT_VISIBLE = "credit_not_visible_manual_review"
ENTITY_SOURCE_MAP_FIELDS = [
    "sport",
    "league_or_entity",
    "source_priority",
    "source_category",
    "source_name",
    "source_url_or_search_macro",
    "source_domain",
    "evidence_use",
    "rights_review_note",
    "identity_anchor_use",
    "allowed_for_download_approved_yes",
    "manual_next_action",
    "review_only",
    "publish_ready",
]
WOMENS_SOCCER_STARTER_FIELDS = [
    "starter_rank",
    "sport",
    "league_or_entity",
    "expansion_lane",
    "team_or_scope",
    "source_priority",
    "source_category",
    "source_name",
    "source_url_or_search_macro",
    "source_domain",
    "evidence_use",
    "identity_anchor_use",
    "rights_review_note",
    "roster_truth_status",
    "source_confidence",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "download_approved",
    "manual_review_status",
    "manual_reviewer",
    "reviewed_at_utc",
    "allowed_for_download_approved_yes",
    "manual_next_action",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "publish_action",
]
EXTERNAL_RESEARCH_SOURCE_MAP_FIELDS = [
    "sport",
    "league_entity",
    "official_gallery_url_or_macro",
    "roster_player_directory_url_or_macro",
    "media_guide_stats_profile_url_or_macro",
    "editorial_wire_newsroom_sources",
    "official_social",
    "gray_area_public_creator_fan_surfaces",
    "source_category",
    "source_domain",
    "likely_search_query_macro",
    "identity_verification_anchor",
    "rights_posture_recommendation",
    "limitations_red_flags",
    "manual_next_action",
    "source_family_rank",
    "source_family_name",
    "source_family_yield",
    "source_family_function",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "publish_action",
]
ACTION_PHOTO_QUEUE_FIELDS = [
    "candidate_queue_id",
    "sport",
    "league_entity",
    "target_entity_or_player",
    "source_family",
    "source_category",
    "source_url_or_search_macro",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "action_moment_type",
    "render_fit_potential",
    "rights_posture_metadata",
    "fair_use_context_note",
    "download_approved",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "quarantine_target_hint",
    "manual_reviewer",
    "manual_review_status",
    "manual_next_action",
    "review_only",
    "publish_ready",
]
RESEARCH_PACKET_RETURN_COLUMNS = [
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
ACTION_PHOTO_RESEARCH_PACKET_FIELDS = [
    "research_task_id",
    "researcher_lane",
    "candidate_queue_id",
    "sport",
    "league_entity",
    "target_entity_or_player",
    "source_family",
    "source_category",
    "source_url_or_search_macro",
    "action_moment_type",
    "render_fit_potential",
    "rights_posture_metadata",
    "copy_ready_prompt",
    "paste_back_schema",
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
    "download_approved",
    "manual_next_action",
    "review_only",
    "publish_ready",
]
ACTION_PHOTO_RESEARCH_RETURN_INTAKE_FIELDS = [
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

FIELDS = [
    "intake_rank",
    "intake_id",
    "created_at_utc",
    "created_by",
    "intake_status",
    "sport",
    "league",
    "team",
    "player",
    "event_context",
    "candidate_subject_type",
    "source_category",
    "entity_id",
    "source_url",
    "source_domain",
    "source_type",
    "source_name",
    "source_title",
    "source_caption",
    "photographer_credit",
    "competition",
    "event_name",
    "event_date",
    "team_or_country",
    "opponent_or_context",
    "athlete_name_claimed",
    "jersey_number_visible",
    "identity_evidence",
    "rights_class",
    "identity_confidence",
    "likely_action_type",
    "image_surface_type",
    "rights_notes",
    "manual_review_status",
    "manual_reviewer",
    "reviewed_at_utc",
    "duplicate_cluster_id",
    "red_flag_cues",
    "action_photo_relevance",
    "intended_review_only_use",
    "download_approved",
    "download_status",
    "quarantine_folder",
    "quarantine_target_hint",
    "required_if_download_approved",
    "manual_next_action",
    "approval_state_change",
    "approval_status",
    "publish_action",
    "research_prompt_note",
    "research_notes",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")
    return out or "operator_fill_required"


def source_domain(source_url: str) -> str:
    match = re.match(r"https?://([^/]+)", clean(source_url), re.IGNORECASE)
    return match.group(1).lower() if match else ""


def template_rows(generated_at: str) -> List[Dict[str, str]]:
    base = {
        "created_at_utc": generated_at,
        "created_by": "generator_review_only_template",
        "intake_status": "operator_fill_required",
        "sport": "",
        "league": "",
        "team": "",
        "player": "",
        "event_context": "",
        "candidate_subject_type": "action_photo",
        "entity_id": "",
        "source_url": "",
        "source_domain": "",
        "source_name": "",
        "source_title": "",
        "source_caption": "",
        "photographer_credit": "",
        "competition": "",
        "event_name": "",
        "event_date": "",
        "team_or_country": "",
        "opponent_or_context": "",
        "athlete_name_claimed": "",
        "jersey_number_visible": "",
        "identity_evidence": "",
        "rights_class": "",
        "identity_confidence": "",
        "likely_action_type": "",
        "image_surface_type": "",
        "rights_notes": "",
        "manual_review_status": "not_reviewed",
        "manual_reviewer": "",
        "reviewed_at_utc": "",
        "duplicate_cluster_id": "",
        "red_flag_cues": "",
        "action_photo_relevance": "",
        "intended_review_only_use": "",
        "download_approved": "no",
        "download_status": "not_requested",
        "quarantine_folder": QUARANTINE_ROOT,
        "required_if_download_approved": "download_approved|source_url|entity_id|rights_class|identity_confidence|intended_review_only_use|source_category|photographer_credit_or_credit_not_visible_manual_review|manual_reviewer",
        "manual_next_action": "Paste research-only source metadata, verify identity/rights/event context, and leave download_approved=no unless a human explicitly approves quarantine review.",
        "approval_state_change": "none",
        "approval_status": "not_approved",
        "publish_action": "none_artifact_only",
        "research_prompt_note": "Collect candidate URLs, source domains, rights class, player identity proof, event context, action relevance, and why useful for future render review; do not download images or claim approval.",
        "research_notes": "",
        "operator_notes": "",
        "reviewed_by": "",
        "reviewed_at_local": "",
        "review_only": "true",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "asset_downloads": "false",
        "headshot_writes": "false",
        "approved_marker_writes": "false",
    }
    source_templates = [
        ("official_team_gallery", "official team or club gallery/recap lead; still not approval"),
        ("official_league_gallery", "official league gallery/recap lead; still not approval"),
        ("editorial_wire", "Getty/AP/Reuters/Imagn editorial lead; rights-sensitive manual review only"),
        ("reputable_newsroom_gallery", "newsroom/local-beat public lead; rights-sensitive manual review only"),
        ("gray_area_public_lead", "gray-area public lead; park for manual review only"),
    ]
    rows: List[Dict[str, str]] = []
    for index, (source_category, note) in enumerate(source_templates, start=1):
        row = dict(base)
        row["intake_rank"] = f"AP{index:02d}"
        row["intake_id"] = f"review_only_action_photo_candidate_ap{index:02d}"
        row["source_category"] = source_category
        row["source_type"] = source_category
        row["research_notes"] = note
        row["quarantine_target_hint"] = f"{QUARANTINE_ROOT}/action_photo_candidates/operator_fill_required/{source_category}/operator_fill_required.jpg"
        rows.append(row)
    return rows


def normalize_row(row: Mapping[str, str]) -> Dict[str, str]:
    out = {field: clean(row.get(field)) for field in FIELDS}
    out["download_approved"] = clean(out.get("download_approved")).lower() or "no"
    out["download_status"] = out.get("download_status") or "not_requested"
    out["source_category"] = out.get("source_category") or out.get("source_type")
    out["source_type"] = out.get("source_type") or out.get("source_category")
    out["source_domain"] = out.get("source_domain") or source_domain(out.get("source_url", ""))
    out["quarantine_folder"] = out.get("quarantine_folder") or QUARANTINE_ROOT
    out["manual_review_status"] = out.get("manual_review_status") or "not_reviewed"
    if not out.get("quarantine_target_hint"):
        entity = slug(out.get("entity_id") or out.get("player") or out.get("team") or "operator_fill_required")
        source_category = slug(out.get("source_category") or out.get("source_type") or "source_candidate")
        out["quarantine_target_hint"] = f"{QUARANTINE_ROOT}/action_photo_candidates/{entity}/{source_category}/operator_fill_required.jpg"
    return out


def validate_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen = set()
    for index, raw in enumerate(rows, start=2):
        row = normalize_row(raw)
        key = (
            row.get("sport"),
            row.get("league"),
            row.get("team"),
            row.get("player"),
            row.get("event_context"),
            row.get("source_url"),
            row.get("source_category"),
        )
        if key in seen and any(key):
            issues.append({"row": str(index), "field": "source_url", "issue": "duplicate_action_photo_candidate_key"})
        seen.add(key)
        for field, allowed in [
            ("source_category", SOURCE_CATEGORIES),
            ("rights_class", RIGHTS_CLASSES),
            ("identity_confidence", IDENTITY_CONFIDENCE),
            ("manual_review_status", MANUAL_REVIEW_STATUSES),
        ]:
            if row.get(field) and row.get(field) not in allowed:
                issues.append({"row": str(index), "field": field, "issue": "invalid_controlled_vocabulary"})
        if row["download_approved"] == "yes":
            for field in REQUIRED_DOWNLOAD_FIELDS:
                if not row.get(field):
                    issues.append({"row": str(index), "field": field, "issue": "required_when_download_approved_yes"})
            if not row.get("source_category"):
                issues.append({"row": str(index), "field": "source_category", "issue": "required_when_download_approved_yes"})
            if not row.get("photographer_credit"):
                issues.append({"row": str(index), "field": "photographer_credit", "issue": "credit_required_when_download_approved_yes"})
            elif row["photographer_credit"] == CREDIT_NOT_VISIBLE and not row.get("rights_notes"):
                issues.append({"row": str(index), "field": "rights_notes", "issue": "required_when_credit_not_visible"})
            if not row.get("manual_reviewer"):
                issues.append({"row": str(index), "field": "manual_reviewer", "issue": "required_when_download_approved_yes"})
            if not row.get("quarantine_target_hint", "").startswith(QUARANTINE_ROOT + "/"):
                issues.append({"row": str(index), "field": "quarantine_target_hint", "issue": "download_target_must_stay_in_quarantine"})
            if row.get("rights_class") in BLOCKED_DOWNLOAD_RIGHTS:
                issues.append({"row": str(index), "field": "rights_class", "issue": "rights_class_blocks_download_approval"})
            if row.get("identity_confidence") not in DOWNLOAD_READY_IDENTITY:
                issues.append({"row": str(index), "field": "identity_confidence", "issue": "identity_confidence_too_low_for_download_approval"})
        elif row["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "must_be_no_or_human_yes"})
        for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis", "asset_downloads", "headshot_writes", "approved_marker_writes"]:
            if clean(row.get(field)).lower() == "true":
                issues.append({"row": str(index), "field": field, "issue": "guardrail_field_must_remain_false"})
        if row.get("approval_state_change") not in {"", "none"}:
            issues.append({"row": str(index), "field": "approval_state_change", "issue": "generated_intake_must_not_change_approval_state"})
        if row.get("publish_action") not in {"", "none_artifact_only"}:
            issues.append({"row": str(index), "field": "publish_action", "issue": "generated_intake_must_not_publish"})
    return issues


def render_markdown(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    source_counts: Dict[str, int] = {}
    for row in rows:
        category = clean(row.get("source_category")) or clean(row.get("source_type")) or "operator_fill_required"
        source_counts[category] = source_counts.get(category, 0) + 1
    lines = [
        "# Review-Only Action Photo Candidate Intake",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Human-editable intake for future action/moment photo candidates. This packet stores research metadata only. It does not download image files, approve assets, write headshots, create `.approved` markers, move files, publish, or create a publish-ready lane.",
        "",
        "Every discovered item is a candidate lead until a human verifies identity, source provenance, and rights posture.",
        "",
        "## Local Download Law",
        "",
        "- A future download is eligible only when a human-edited row has `download_approved=yes` plus `source_url`, `entity_id`, `rights_class`, `identity_confidence`, `intended_review_only_use`, `source_category`, photographer credit or `credit_not_visible_manual_review`, and `manual_reviewer` filled.",
        f"- Any future file must land under `{QUARANTINE_ROOT}/`.",
        "- Download approval is not asset approval; separate human visual/identity/rights approval is still required.",
        "- `social_uncleared`, `third_party_creator_uncleared`, `gray_area_lead_only`, and `reject_do_not_pursue` rows cannot be download-approved by this validator.",
        "- Generated rows default to `download_approved=no` and are not render-ready.",
        "",
        "## Deep Research Paste Note",
        "",
        "Ask ChatGPT Pro or Gemini to collect candidate URLs, source domains, source category, rights clues, player/team identity proof, event context, action relevance, credit lines, and why the moment would help future review renders. Do not ask it to download images, scrape photo files, fill approval fields, or claim publish readiness.",
        "",
        "## Summary",
        "",
        f"- Intake template rows: `{len(rows)}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')).lower() == 'yes')}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Quarantine root: `{QUARANTINE_ROOT}`",
        "",
        "## Source Categories",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(source_counts.items()))
    lines += [
        "",
        "## Board Preview",
        "",
        "| Rank | Source Category | Source Name | Sport | League | Team | Player | Source URL | Download Approved | Manual Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows[:20]:
        lines.append(
            "| {rank} | {source_category} | {source_name} | {sport} | {league} | {team} | {player} | {source_url} | {approved} | {action} |".format(
                rank=clean(row.get("intake_rank")),
                source_category=clean(row.get("source_category")),
                source_name=clean(row.get("source_name")).replace("|", "/"),
                sport=clean(row.get("sport")),
                league=clean(row.get("league")),
                team=clean(row.get("team")).replace("|", "/"),
                player=clean(row.get("player")).replace("|", "/"),
                source_url=clean(row.get("source_url")).replace("|", "%7C"),
                approved=clean(row.get("download_approved")),
                action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def taxonomy_payload() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "source_categories": SOURCE_CATEGORIES,
        "rights_classes": RIGHTS_CLASSES,
        "identity_confidence": IDENTITY_CONFIDENCE,
        "manual_review_statuses": MANUAL_REVIEW_STATUSES,
        "download_blocked_rights_classes": sorted(BLOCKED_DOWNLOAD_RIGHTS),
        "download_ready_identity_confidence": sorted(DOWNLOAD_READY_IDENTITY),
        "credit_not_visible_placeholder": CREDIT_NOT_VISIBLE,
        "guardrail": "URL-first, evidence-first, review-only candidate metadata; no downloads, approvals, or publish-ready claims.",
    }


def render_taxonomy(generated_at: str) -> str:
    lines = [
        "# Review-Only Action Photo Candidate Taxonomy",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Use these controlled vocabularies for URL-first/evidence-first action photo candidate rows. They classify review leads only; they do not grant download, asset approval, or render readiness.",
        "",
        "## Source Categories",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in SOURCE_CATEGORIES.items())
    lines += ["", "## Rights Classes", ""]
    lines.extend(f"- `{key}`: {value}" for key, value in RIGHTS_CLASSES.items())
    lines += ["", "## Identity Confidence", ""]
    lines.extend(f"- `{key}`: {value}" for key, value in IDENTITY_CONFIDENCE.items())
    lines += [
        "",
        "## Download-Approval Gate",
        "",
        f"- Required local-download-law fields: `{', '.join(REQUIRED_DOWNLOAD_FIELDS)}`.",
        "- Additional required human-review fields before `download_approved=yes`: `source_category`, `manual_reviewer`, and `photographer_credit` or `credit_not_visible_manual_review` with rights notes.",
        f"- Blocked rights classes for download approval: `{', '.join(sorted(BLOCKED_DOWNLOAD_RIGHTS))}`.",
        f"- Minimum identity confidence for download approval: `{', '.join(sorted(DOWNLOAD_READY_IDENTITY))}`.",
    ]
    return "\n".join(lines) + "\n"


def render_checklist(generated_at: str) -> str:
    steps = [
        "Verify the athlete identity against an official roster, player directory, federation page, media guide, or event anchor.",
        "Confirm the event name, date, season, team, opponent, and uniform context before trusting the lead.",
        "Capture the source URL, source domain, source title/caption, photographer or agency credit, and any visible license or rights clues.",
        "Assign the most conservative rights class; official source does not mean publish-ready rights.",
        "Reject or escalate restricted-access imagery, credential-only contexts, locker-room/corridor imagery, manipulations, or missing-provenance rows.",
        "Avoid video, broadcast, GIF, or footage-derived stills unless an explicit policy allows that source type.",
        "Check promo/commercial sensitivity before spending review time on editorial or rights-sensitive imagery.",
        "Assess render suitability only after identity and rights posture are credible.",
        "Cluster duplicates and near-duplicates so the same moment is not reviewed repeatedly.",
        "Record a disposition using `manual_review_status`, `manual_reviewer`, `reviewed_at_utc`, and notes; do not change asset approval state here.",
    ]
    red_flags = [
        "discoverability being mistaken for permission",
        "old uniform, transfer, loan, or national-team context being treated as current club context",
        "broadcast/video/social-video stills",
        "restricted-access or behind-the-scenes setting",
        "all-rights-reserved or purchase-license clues without a rights path",
        "AI-edited, composited, or suspiciously manipulated imagery",
        "source URL that lands on search results rather than a stable item page",
        "repost chain that hides the original source or credit",
    ]
    lines = [
        "# Review-Only Action Photo Human Review Checklist",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Work each row in this order: identity, event context, rights posture, suitability, then workflow disposition. The output is a review decision on a lead, not asset approval.",
        "",
        "## Review Steps",
        "",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    lines += ["", "## Red Flags", ""]
    lines.extend(f"- {flag}" for flag in red_flags)
    lines += [
        "",
        "## Hard Stop",
        "",
        "Do not download image files, approve assets, write headshots, create `.approved` markers, move files, publish, or claim render readiness from this checklist.",
    ]
    return "\n".join(lines) + "\n"


def source_map_rows() -> List[Dict[str, str]]:
    rows = [
        {
            "source_category": "official_team_gallery",
            "source_priority": "first",
            "source_examples": "team gallery, club recap, game photo page",
            "search_macro": '"[athlete] [team] site:[team-domain] gallery OR recap"',
            "collect_only": "canonical URL, source title, caption, event/date, credit line, identity clues",
            "do_not_collect": "image files, direct downloads, approval claims, render-ready claims",
            "rights_posture": "official_review_needed",
        },
        {
            "source_category": "official_league_gallery",
            "source_priority": "first",
            "source_examples": "WNBA/NWSL/league gallery or recap",
            "search_macro": '"[athlete] [league] site:[league-domain] gallery OR photos"',
            "collect_only": "canonical URL, event/date, caption, credit line, league context",
            "do_not_collect": "image files, scraping, automatic download approvals",
            "rights_posture": "official_review_needed",
        },
        {
            "source_category": "official_federation_or_tournament",
            "source_priority": "first",
            "source_examples": "federation, tournament, NCAA, championship photo surface",
            "search_macro": '"[athlete] [competition] site:[official-event-domain] photos"',
            "collect_only": "official URL, competition, event/date, caption, identity evidence",
            "do_not_collect": "footage stills unless explicitly allowed, downloads, approvals",
            "rights_posture": "official_review_needed",
        },
        {
            "source_category": "verification_only_player_page",
            "source_priority": "identity_anchor",
            "source_examples": "player profile, roster, stats page, media guide",
            "search_macro": '"[athlete] [team] roster player profile official"',
            "collect_only": "official identity URL, team, number, position, season context",
            "do_not_collect": "photo downloads or treating roster portraits as action candidates",
            "rights_posture": "verification_only",
        },
        {
            "source_category": "editorial_wire",
            "source_priority": "second",
            "source_examples": "Getty, AP, Reuters, Imagn",
            "search_macro": '"[athlete]" site:gettyimages.com OR site:newsroom.ap.org OR site:reutersconnect.com',
            "collect_only": "detail URL, caption, agency, photographer, event/date, license clues",
            "do_not_collect": "image files, preview downloads, licensed content reuse assumptions",
            "rights_posture": "editorial_wire_rights_sensitive",
        },
        {
            "source_category": "reputable_newsroom_gallery",
            "source_priority": "third",
            "source_examples": "local beat gallery, newsroom article, regional broadcaster gallery",
            "search_macro": '"[athlete] [team] photo gallery local news"',
            "collect_only": "article/gallery URL, outlet, caption, credit, event/date",
            "do_not_collect": "image files, screenshots, approval claims",
            "rights_posture": "newsroom_photo_rights_sensitive",
        },
        {
            "source_category": "official_social",
            "source_priority": "fourth",
            "source_examples": "official team, league, athlete, federation posts",
            "search_macro": '"[athlete] [team]" site:instagram.com/p/ OR site:x.com',
            "collect_only": "post URL, account, caption, event clues, source relationship",
            "do_not_collect": "social image files, video stills, platform downloads, rights clearance claims",
            "rights_posture": "social_uncleared",
        },
        {
            "source_category": "third_party_creator_public",
            "source_priority": "last",
            "source_examples": "independent photographer portfolio, Flickr, SmugMug",
            "search_macro": '"[athlete] [team] photographer gallery"',
            "collect_only": "creator URL, credit/owner, rights statement, event/date clues",
            "do_not_collect": "image files, reposts without original credit, permission assumptions",
            "rights_posture": "third_party_creator_uncleared",
        },
        {
            "source_category": "gray_area_public_lead",
            "source_priority": "park_only",
            "source_examples": "fan archive, forum, repost, weak-provenance public page",
            "search_macro": '"[athlete] [team] action photo"',
            "collect_only": "stable URL and why it may be useful for manual follow-up",
            "do_not_collect": "image files, approval fields, current-roster truth, render-ready claims",
            "rights_posture": "gray_area_lead_only",
        },
    ]
    return rows


def render_source_map(rows: List[Mapping[str, str]], generated_at: str) -> str:
    lines = [
        "# Review-Only Action Photo Source Map Template",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Use this template for ChatGPT Pro, Gemini, or manual research sweeps. Collect URLs and evidence only. Do not download image files, claim approval, fill `download_approved=yes`, or mark anything render-ready.",
        "",
        "| Source Category | Priority | Search Macro | Collect Only | Rights Posture |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {source_category} | {source_priority} | `{search_macro}` | {collect_only} | {rights_posture} |".format(
                source_category=clean(row.get("source_category")),
                source_priority=clean(row.get("source_priority")),
                search_macro=clean(row.get("search_macro")).replace("|", "/"),
                collect_only=clean(row.get("collect_only")).replace("|", "/"),
                rights_posture=clean(row.get("rights_posture")),
            )
        )
    return "\n".join(lines) + "\n"


def sport_entity_source_map_rows() -> List[Dict[str, str]]:
    default_action = (
        "Paste URL-only research leads into this board, then promote only verified page metadata into the action-photo intake; "
        "do not download images or mark anything approved."
    )
    rows = [
        {
            "sport": "basketball",
            "league_or_entity": "WNBA",
            "source_priority": "P0_official_league",
            "source_category": "official_league_gallery",
            "source_name": "WNBA official site",
            "source_url_or_search_macro": '"[athlete] [team] site:wnba.com gallery OR recap OR photos"',
            "source_domain": "wnba.com",
            "evidence_use": "event recap/gallery lead; current team/date context; caption clues",
            "rights_review_note": "official_review_needed; official surface is not publish-ready rights",
            "identity_anchor_use": "cross-check WNBA player profile, team roster, jersey, and box score context",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "basketball",
            "league_or_entity": "WNBA teams",
            "source_priority": "P0_official_team",
            "source_category": "official_team_gallery",
            "source_name": "WNBA team sites",
            "source_url_or_search_macro": '"[athlete] [team] site:[team].wnba.com gallery OR recap"',
            "source_domain": "team.wnba.com",
            "evidence_use": "team-owned game gallery/recap lead; player/team/event context",
            "rights_review_note": "official_review_needed; verify any partner photo credit",
            "identity_anchor_use": "team roster plus event recap and visible number/uniform",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "multi-sport",
            "league_or_entity": "official player pages / rosters",
            "source_priority": "P0_identity_anchor",
            "source_category": "verification_only_player_page",
            "source_name": "official player profile, roster, stats page, or media guide",
            "source_url_or_search_macro": '"[athlete] [team] official roster player profile media guide"',
            "source_domain": "operator_fill_required",
            "evidence_use": "identity anchor only; roster status, jersey, position, team, and season context",
            "rights_review_note": "verification_only; do not treat roster portraits as action-photo candidates",
            "identity_anchor_use": "use as the official corroboration URL before promoting an action-photo lead",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "soccer",
            "league_or_entity": "NWSL",
            "source_priority": "P0_official_league",
            "source_category": "official_league_gallery",
            "source_name": "NWSL official site",
            "source_url_or_search_macro": '"[athlete] [club] site:nwslsoccer.com photos OR gallery OR recap"',
            "source_domain": "nwslsoccer.com",
            "evidence_use": "match recap/gallery lead; league/team/date context",
            "rights_review_note": "official_review_needed; check partner photography credits",
            "identity_anchor_use": "NWSL roster/player page, club roster, match report, jersey context",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "soccer",
            "league_or_entity": "NWSL clubs",
            "source_priority": "P0_official_team",
            "source_category": "official_team_gallery",
            "source_name": "NWSL club sites",
            "source_url_or_search_macro": '"[athlete] [club] site:[club-domain] gallery OR recap OR photos"',
            "source_domain": "operator_fill_required",
            "evidence_use": "club gallery/recap source lead; current club and match context",
            "rights_review_note": "official_review_needed; respect club/media credential limits",
            "identity_anchor_use": "club roster, NWSL player page, match lineup, visible number",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "soccer",
            "league_or_entity": "USWNT",
            "source_priority": "P0_official_federation",
            "source_category": "official_federation_or_tournament",
            "source_name": "U.S. Soccer official site",
            "source_url_or_search_macro": '"[athlete] USWNT site:ussoccer.com gallery OR photos OR recap"',
            "source_domain": "ussoccer.com",
            "evidence_use": "national-team event lead; competition/date/caption context",
            "rights_review_note": "official_review_needed; federation content still needs rights review",
            "identity_anchor_use": "USWNT roster/player page, match report, uniform/number context",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "college basketball",
            "league_or_entity": "NCAA women's basketball",
            "source_priority": "P0_official_tournament_or_school",
            "source_category": "official_federation_or_tournament",
            "source_name": "NCAA and school athletics sites",
            "source_url_or_search_macro": '"[athlete] [school] women basketball gallery OR recap site:ncaa.com OR site:[school-athletics-domain]"',
            "source_domain": "ncaa.com|school-athletics-domain",
            "evidence_use": "school/NCAA gallery lead; game/tournament context and roster proof",
            "rights_review_note": "official_review_needed; NCAA/school event photography rights remain restricted",
            "identity_anchor_use": "school roster, NCAA stats, jersey number, event box score",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "college soccer",
            "league_or_entity": "NCAA women's soccer",
            "source_priority": "P0_official_school_or_tournament",
            "source_category": "official_federation_or_tournament",
            "source_name": "NCAA and school athletics sites",
            "source_url_or_search_macro": '"[athlete] [school] women soccer gallery OR recap site:ncaa.com OR site:[school-athletics-domain]"',
            "source_domain": "ncaa.com|school-athletics-domain",
            "evidence_use": "school/NCAA action lead; match/date/roster context",
            "rights_review_note": "official_review_needed; confirm school or NCAA rights notes",
            "identity_anchor_use": "school roster, match recap, jersey number, opponent context",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "softball",
            "league_or_entity": "NCAA softball",
            "source_priority": "P0_official_school_or_tournament",
            "source_category": "official_federation_or_tournament",
            "source_name": "NCAA and school athletics sites",
            "source_url_or_search_macro": '"[athlete] [school] softball gallery OR recap site:ncaa.com OR site:[school-athletics-domain]"',
            "source_domain": "ncaa.com|school-athletics-domain",
            "evidence_use": "game/championship gallery lead; batting/fielding action context",
            "rights_review_note": "official_review_needed; championship/school imagery is not auto-cleared",
            "identity_anchor_use": "school roster, number, position, game recap, opponent",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "softball",
            "league_or_entity": "pro softball / Athletes Unlimited",
            "source_priority": "P1_official_or_reputable",
            "source_category": "official_league_gallery",
            "source_name": "Pro softball league/operator sites",
            "source_url_or_search_macro": '"[athlete] softball gallery OR recap site:auprosports.com OR site:[league-domain]"',
            "source_domain": "auprosports.com|league-domain",
            "evidence_use": "pro softball action lead; current event and team/session context",
            "rights_review_note": "official_review_needed; verify league/operator photo terms",
            "identity_anchor_use": "league roster/profile, event page, jersey/context clues",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "tennis",
            "league_or_entity": "WTA / Grand Slam / tournament",
            "source_priority": "P0_official_tournament",
            "source_category": "official_federation_or_tournament",
            "source_name": "WTA and tournament sites",
            "source_url_or_search_macro": '"[athlete] site:wtatennis.com OR site:[tournament-domain] photos OR gallery"',
            "source_domain": "wtatennis.com|tournament-domain",
            "evidence_use": "tournament gallery/recap lead; match/date/action context",
            "rights_review_note": "official_review_needed or official_partner_licensed_manual_review if credited partner imagery",
            "identity_anchor_use": "WTA profile, draw/match page, tournament caption",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "golf",
            "league_or_entity": "LPGA / tournament",
            "source_priority": "P0_official_tournament",
            "source_category": "official_federation_or_tournament",
            "source_name": "LPGA and tournament sites",
            "source_url_or_search_macro": '"[athlete] site:lpga.com OR site:[tournament-domain] photos OR gallery"',
            "source_domain": "lpga.com|tournament-domain",
            "evidence_use": "tournament/article photo lead; round/date/context clues",
            "rights_review_note": "official_review_needed; partner photo credits may be rights-sensitive",
            "identity_anchor_use": "LPGA player profile, tournament leaderboard, caption/context",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "hockey",
            "league_or_entity": "PWHL",
            "source_priority": "P0_official_league_or_team",
            "source_category": "official_league_gallery",
            "source_name": "PWHL official and team sites",
            "source_url_or_search_macro": '"[athlete] PWHL [team] gallery OR recap site:thepwhl.com"',
            "source_domain": "thepwhl.com",
            "evidence_use": "league/team game gallery lead; player/team/date context",
            "rights_review_note": "official_review_needed; check league/team image terms and credit",
            "identity_anchor_use": "PWHL roster/profile, game recap, jersey number",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "hockey",
            "league_or_entity": "NCAA women's hockey",
            "source_priority": "P0_official_school_or_tournament",
            "source_category": "official_federation_or_tournament",
            "source_name": "NCAA and school athletics sites",
            "source_url_or_search_macro": '"[athlete] [school] women hockey gallery OR recap site:ncaa.com OR site:[school-athletics-domain]"',
            "source_domain": "ncaa.com|school-athletics-domain",
            "evidence_use": "school/NCAA hockey action lead; game/date/context",
            "rights_review_note": "official_review_needed; school/NCAA photo rights remain separate",
            "identity_anchor_use": "school roster, game recap, jersey number, position",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "multi-sport",
            "league_or_entity": "editorial wires",
            "source_priority": "P1_rights_sensitive",
            "source_category": "editorial_wire",
            "source_name": "Getty / AP / Reuters / Imagn",
            "source_url_or_search_macro": '"[athlete]" site:gettyimages.com OR site:newsroom.ap.org OR site:reutersconnect.com OR site:imagn.com',
            "source_domain": "gettyimages.com|newsroom.ap.org|reutersconnect.com|imagn.com",
            "evidence_use": "detail-page lead with caption, event, photographer/agency, and license clues",
            "rights_review_note": "editorial_wire_rights_sensitive; licensing review required before any human download approval",
            "identity_anchor_use": "caption plus official roster/profile/event anchor",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "multi-sport",
            "league_or_entity": "reputable newsrooms / local beat galleries",
            "source_priority": "P2_reputable_public",
            "source_category": "reputable_newsroom_gallery",
            "source_name": "newsrooms and local beat outlets",
            "source_url_or_search_macro": '"[athlete] [team] photo gallery local news OR sports desk"',
            "source_domain": "operator_fill_required",
            "evidence_use": "supplemental public action lead with caption/credit/context",
            "rights_review_note": "newsroom_photo_rights_sensitive; no reuse assumed",
            "identity_anchor_use": "news caption plus official roster/event page",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "multi-sport",
            "league_or_entity": "official social",
            "source_priority": "P3_social_discovery",
            "source_category": "official_social",
            "source_name": "official athlete/team/league social",
            "source_url_or_search_macro": '"[athlete] [team]" site:instagram.com/p/ OR site:x.com OR site:tiktok.com',
            "source_domain": "instagram.com|x.com|tiktok.com",
            "evidence_use": "current moment discovery lead; caption and account relationship only",
            "rights_review_note": "social_uncleared; discovery only, not a rights answer",
            "identity_anchor_use": "verified account context plus official roster/event anchor",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "multi-sport",
            "league_or_entity": "creator/public galleries",
            "source_priority": "P4_creator_public",
            "source_category": "third_party_creator_public",
            "source_name": "independent photographer / portfolio / Flickr / SmugMug",
            "source_url_or_search_macro": '"[athlete] [team] photographer gallery OR Flickr OR SmugMug"',
            "source_domain": "operator_fill_required",
            "evidence_use": "long-tail discovery lead; original creator/credit and event clues",
            "rights_review_note": "third_party_creator_uncleared; requires provenance and permission review",
            "identity_anchor_use": "creator caption plus official roster/event anchor",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": default_action,
            "review_only": "true",
            "publish_ready": "false",
        },
        {
            "sport": "multi-sport",
            "league_or_entity": "gray-area public leads",
            "source_priority": "P5_park_only",
            "source_category": "gray_area_public_lead",
            "source_name": "fan archives / reposts / forums / weak-provenance public pages",
            "source_url_or_search_macro": '"[athlete] [team] action photo"',
            "source_domain": "operator_fill_required",
            "evidence_use": "parking lot for possibly useful leads when official/editorial coverage is thin",
            "rights_review_note": "gray_area_lead_only; do not treat as official roster truth or download candidate",
            "identity_anchor_use": "must be corroborated against official roster/event source before intake promotion",
            "allowed_for_download_approved_yes": "false",
            "manual_next_action": "Park as advisory metadata only unless a human finds a stronger official/reputable source.",
            "review_only": "true",
            "publish_ready": "false",
        },
    ]
    return rows


def validate_entity_source_map_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen = set()
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in ENTITY_SOURCE_MAP_FIELDS}
        key = (
            normalized["sport"],
            normalized["league_or_entity"],
            normalized["source_category"],
            normalized["source_url_or_search_macro"],
        )
        if key in seen:
            issues.append({"row": str(index), "field": "source_url_or_search_macro", "issue": "duplicate_source_map_key"})
        seen.add(key)
        if normalized["source_category"] not in SOURCE_CATEGORIES:
            issues.append({"row": str(index), "field": "source_category", "issue": "invalid_controlled_vocabulary"})
        for field in ["sport", "league_or_entity", "source_priority", "source_name", "source_url_or_search_macro", "evidence_use", "rights_review_note", "identity_anchor_use", "manual_next_action"]:
            if not normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "required_source_map_field_blank"})
        if normalized["allowed_for_download_approved_yes"] != "false":
            issues.append({"row": str(index), "field": "allowed_for_download_approved_yes", "issue": "source_map_never_download_approved"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "source_map_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "source_map_must_not_be_publish_ready"})
    return issues


def render_entity_source_map(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    category_counts: Dict[str, int] = {}
    sport_counts: Dict[str, int] = {}
    for row in rows:
        category = clean(row.get("source_category"))
        sport = clean(row.get("sport"))
        category_counts[category] = category_counts.get(category, 0) + 1
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
    lines = [
        "# Review-Only Action Photo Sport/Entity Source Map",
        "",
        f"Generated: `{generated_at}`",
        "",
        "URL-first, evidence-first board for ChatGPT Pro, Gemini, and manual researchers. It tells researchers where to look for source leads; it does not fetch, download, approve, or publish image assets.",
        "",
        "## Operator Paste Note",
        "",
        "Paste research outputs back into this board as source URLs or search macros plus evidence notes. Only after a human verifies identity, source provenance, and rights posture should page metadata be copied into the action-photo intake. Keep `allowed_for_download_approved_yes=false` here; any future quarantine download still requires a separate human-edited intake row with the local-download-law fields filled.",
        "",
        "## Summary",
        "",
        f"- Source-map rows: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows allowed for `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('allowed_for_download_approved_yes')).lower() == 'true')}`",
        f"- Review-only rows: `{sum(1 for row in rows if clean(row.get('review_only')) == 'true')}`",
        f"- Publish-ready rows: `{sum(1 for row in rows if clean(row.get('publish_ready')) == 'true')}`",
        "",
        "## Sport Coverage",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(sport_counts.items()))
    lines += ["", "## Source Category Coverage", ""]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(category_counts.items()))
    lines += [
        "",
        "## Board Preview",
        "",
        "| Sport | League/Entity | Priority | Category | Source Name | URL/Search Macro | Evidence Use | Manual Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {sport} | {league_or_entity} | {source_priority} | {source_category} | {source_name} | `{macro}` | {evidence_use} | {manual_next_action} |".format(
                sport=clean(row.get("sport")),
                league_or_entity=clean(row.get("league_or_entity")).replace("|", "/"),
                source_priority=clean(row.get("source_priority")),
                source_category=clean(row.get("source_category")),
                source_name=clean(row.get("source_name")).replace("|", "/"),
                macro=clean(row.get("source_url_or_search_macro")).replace("|", "/"),
                evidence_use=clean(row.get("evidence_use")).replace("|", "/"),
                manual_next_action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def womens_soccer_starter_rows() -> List[Dict[str, str]]:
    default_action = (
        "Use this as a manual research prompt only; paste URLs/evidence after human review and keep download_approved=no. "
        "Do not assert roster truth, download images, or mark anything approved."
    )
    base = {
        "sport": "soccer",
        "source_url": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "download_approved": "no",
        "manual_review_status": "not_reviewed",
        "manual_reviewer": "",
        "reviewed_at_utc": "",
        "allowed_for_download_approved_yes": "false",
        "manual_next_action": default_action,
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "none",
        "publish_action": "none_artifact_only",
        "source_confidence": "manual_review_required",
        "roster_truth_status": "not_asserted_manual_verification_required",
    }
    row_specs = [
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "league",
            "source_priority": "P0_official_league",
            "source_category": "official_league_gallery",
            "source_name": "NWSL official site",
            "source_url_or_search_macro": '"[athlete] [club] site:nwslsoccer.com gallery OR photos OR recap"',
            "source_domain": "nwslsoccer.com",
            "evidence_use": "official league action lead; match/date/team context and caption clues",
            "identity_anchor_use": "cross-check NWSL player page, club roster, match report, jersey/uniform context",
            "rights_review_note": "official_review_needed; no publish-ready rights assumed",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "club_sites",
            "source_priority": "P0_official_team",
            "source_category": "official_team_gallery",
            "source_name": "NWSL club sites",
            "source_url_or_search_macro": '"[athlete] [club] site:[club-domain] gallery OR recap OR photos"',
            "source_domain": "operator_fill_required",
            "evidence_use": "club-owned gallery or recap lead; current club and match context",
            "identity_anchor_use": "club roster plus NWSL player page, lineup, visible number, and match context",
            "rights_review_note": "official_review_needed; respect club/media credential limits and partner photo credits",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "player_identity_anchor",
            "source_priority": "P0_identity_anchor",
            "source_category": "verification_only_player_page",
            "source_name": "NWSL and club roster/player pages",
            "source_url_or_search_macro": '"[athlete] [club] NWSL roster player profile official"',
            "source_domain": "nwslsoccer.com|club-domain",
            "evidence_use": "identity anchor only; roster status, number, position, current club, and season context",
            "identity_anchor_use": "use as required corroboration before treating any image lead as the claimed athlete",
            "rights_review_note": "verification_only; roster/headshot pages are not action-photo candidates",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "editorial_marketplaces",
            "source_priority": "P1_rights_sensitive",
            "source_category": "editorial_wire",
            "source_name": "Getty / AP / Reuters / Imagn",
            "source_url_or_search_macro": '"[athlete]" "[club]" NWSL site:gettyimages.com OR site:newsroom.ap.org OR site:reutersconnect.com OR site:imagn.com',
            "source_domain": "gettyimages.com|newsroom.ap.org|reutersconnect.com|imagn.com",
            "evidence_use": "rights-sensitive detail-page lead; caption, event, photographer/agency, and license clues",
            "identity_anchor_use": "caption plus official NWSL/club roster and match context",
            "rights_review_note": "editorial_wire_rights_sensitive; licensing review required before any later human download approval",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "reputable_newsrooms",
            "source_priority": "P2_reputable_public",
            "source_category": "reputable_newsroom_gallery",
            "source_name": "newsrooms and local beat outlets",
            "source_url_or_search_macro": '"[athlete] [club] NWSL photo gallery local news OR sports desk"',
            "source_domain": "operator_fill_required",
            "evidence_use": "supplemental public action lead with caption, credit, and match context",
            "identity_anchor_use": "news caption plus official roster/player page and match report",
            "rights_review_note": "newsroom_photo_rights_sensitive; no reuse assumed",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "official_social",
            "source_priority": "P3_social_discovery",
            "source_category": "official_social",
            "source_name": "official NWSL, club, and athlete social accounts",
            "source_url_or_search_macro": '"[athlete] [club] NWSL" site:instagram.com/p/ OR site:x.com OR site:tiktok.com',
            "source_domain": "instagram.com|x.com|tiktok.com",
            "evidence_use": "current moment discovery lead; account relationship, caption, and event clues",
            "identity_anchor_use": "verified account context plus official roster/player/event anchor",
            "rights_review_note": "social_uncleared; discovery only, not a rights answer",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "creator_public_galleries",
            "source_priority": "P4_creator_public",
            "source_category": "third_party_creator_public",
            "source_name": "independent photographers / portfolios / Flickr / SmugMug",
            "source_url_or_search_macro": '"[athlete] [club] NWSL photographer gallery OR Flickr OR SmugMug"',
            "source_domain": "operator_fill_required",
            "evidence_use": "long-tail discovery lead; original creator/credit and match clues",
            "identity_anchor_use": "creator caption plus official roster/player/event anchor",
            "rights_review_note": "third_party_creator_uncleared; provenance and permission review required",
        },
        {
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "gray_area_public_leads",
            "source_priority": "P5_park_only",
            "source_category": "gray_area_public_lead",
            "source_name": "fan archives / reposts / forums / weak-provenance public pages",
            "source_url_or_search_macro": '"[athlete] [club] NWSL action photo"',
            "source_domain": "operator_fill_required",
            "evidence_use": "parking lot for possibly useful leads when official/editorial coverage is thin",
            "identity_anchor_use": "must be corroborated against official roster/player and event sources",
            "rights_review_note": "gray_area_lead_only; not official roster truth and not a download candidate",
            "manual_next_action": "Park as advisory metadata only unless a human finds a stronger official/reputable source; do not download or approve.",
        },
        {
            "league_or_entity": "USWNT",
            "expansion_lane": "future_uswnt",
            "team_or_scope": "federation_official",
            "source_priority": "P0_official_federation",
            "source_category": "official_federation_or_tournament",
            "source_name": "U.S. Soccer official site",
            "source_url_or_search_macro": '"[athlete] USWNT site:ussoccer.com gallery OR photos OR recap"',
            "source_domain": "ussoccer.com",
            "evidence_use": "future federation action lead; national-team event/date/caption context",
            "identity_anchor_use": "USWNT roster/player page, match report, uniform/number context",
            "rights_review_note": "official_review_needed; federation content still requires rights review",
        },
        {
            "league_or_entity": "Europe top flight",
            "expansion_lane": "future_wsl_liga_f_arkema",
            "team_or_scope": "official_league_or_club",
            "source_priority": "P0_official_league_or_team",
            "source_category": "official_league_gallery",
            "source_name": "WSL / Liga F / Arkema / club official sites",
            "source_url_or_search_macro": '"[athlete] [club] WSL OR \"Liga F\" OR Arkema gallery OR recap official"',
            "source_domain": "operator_fill_required",
            "evidence_use": "future Europe action lead; league/club/match context only",
            "identity_anchor_use": "official league/club roster/player page before any intake promotion",
            "rights_review_note": "official_review_needed; source-candidate only and explicitly not render-ready",
        },
    ]
    rows: List[Dict[str, str]] = []
    for index, spec in enumerate(row_specs, start=1):
        row = {**base, **spec}
        row["starter_rank"] = f"WSAP{index:02d}"
        rows.append(row)
    return rows


def validate_womens_soccer_starter_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen = set()
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in WOMENS_SOCCER_STARTER_FIELDS}
        key = (
            normalized["league_or_entity"],
            normalized["team_or_scope"],
            normalized["source_category"],
            normalized["source_url_or_search_macro"],
        )
        if key in seen:
            issues.append({"row": str(index), "field": "source_url_or_search_macro", "issue": "duplicate_womens_soccer_starter_key"})
        seen.add(key)
        if normalized["source_category"] not in SOURCE_CATEGORIES:
            issues.append({"row": str(index), "field": "source_category", "issue": "invalid_controlled_vocabulary"})
        for field in ["starter_rank", "sport", "league_or_entity", "source_priority", "source_name", "source_url_or_search_macro", "evidence_use", "identity_anchor_use", "rights_review_note", "manual_next_action"]:
            if not normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "required_womens_soccer_starter_field_blank"})
        for field in REQUIRED_DOWNLOAD_FIELDS:
            if normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "generated_local_download_law_field_must_stay_blank"})
        if normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_rows_must_not_approve_downloads"})
        if normalized["allowed_for_download_approved_yes"] != "false":
            issues.append({"row": str(index), "field": "allowed_for_download_approved_yes", "issue": "starter_rows_never_download_approved"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "starter_rows_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "starter_rows_must_not_be_publish_ready"})
        if normalized["approval_state_change"] not in {"", "none"}:
            issues.append({"row": str(index), "field": "approval_state_change", "issue": "starter_rows_must_not_change_approval_state"})
        if normalized["publish_action"] not in {"", "none_artifact_only"}:
            issues.append({"row": str(index), "field": "publish_action", "issue": "starter_rows_must_not_publish"})
        if "asserted" in normalized["roster_truth_status"] and normalized["roster_truth_status"] != "not_asserted_manual_verification_required":
            issues.append({"row": str(index), "field": "roster_truth_status", "issue": "roster_truth_must_not_be_asserted"})
    return issues


def render_womens_soccer_starter(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    lane_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    for row in rows:
        lane = clean(row.get("expansion_lane"))
        category = clean(row.get("source_category"))
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
    lines = [
        "# Review-Only Women's Soccer Action Photo Starter Intake",
        "",
        f"Generated: `{generated_at}`",
        "",
        "NWSL-first URL/evidence starter for manual action-photo research. This artifact stores prompts and source leads only; it does not fetch, download, approve, assert current roster truth, write headshots, create `.approved` markers, publish, or create a publish-ready lane.",
        "",
        "## Operator Paste Note",
        "",
        "Use ChatGPT Pro, Gemini, or manual research to fill source URLs and evidence notes in a later human-edited row. Keep generated local-download-law fields blank/no here. Copy only verified page metadata into the main action-photo intake after identity, source provenance, and rights posture are manually checked.",
        "",
        "## Summary",
        "",
        f"- Starter rows: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        f"- Review-only rows: `{sum(1 for row in rows if clean(row.get('review_only')) == 'true')}`",
        f"- Publish-ready rows: `{sum(1 for row in rows if clean(row.get('publish_ready')) == 'true')}`",
        "",
        "## Expansion Lanes",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(lane_counts.items()))
    lines += ["", "## Source Categories", ""]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(category_counts.items()))
    lines += [
        "",
        "## Board Preview",
        "",
        "| Rank | League/Entity | Lane | Scope | Priority | Category | URL/Search Macro | Manual Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {rank} | {league} | {lane} | {scope} | {priority} | {category} | `{macro}` | {action} |".format(
                rank=clean(row.get("starter_rank")),
                league=clean(row.get("league_or_entity")).replace("|", "/"),
                lane=clean(row.get("expansion_lane")),
                scope=clean(row.get("team_or_scope")).replace("|", "/"),
                priority=clean(row.get("source_priority")),
                category=clean(row.get("source_category")),
                macro=clean(row.get("source_url_or_search_macro")).replace("|", "/"),
                action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def external_research_source_map_rows() -> List[Dict[str, str]]:
    default_action = (
        "Paste ChatGPT Pro, Gemini, or manual research results as URL/evidence leads only; "
        "do not download images, claim approval, assert current roster truth, or mark render-ready."
    )
    base = {
        "download_approved": "no",
        "source_url": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "review_only": "true",
        "publish_ready": "false",
        "approval_state_change": "none",
        "publish_action": "none_artifact_only",
        "manual_next_action": default_action,
    }
    rows = [
        {
            "sport": "Basketball",
            "league_entity": "WNBA",
            "official_gallery_url_or_macro": "https://www.wnba.com/photos",
            "roster_player_directory_url_or_macro": "https://www.wnba.com/players/roster-tracker",
            "media_guide_stats_profile_url_or_macro": "https://sky.wnba.com/chicago-sky-2026-media-central",
            "editorial_wire_newsroom_sources": "https://www.gettyimages.com/photos/wnba",
            "official_social": "https://x.com/WNBA",
            "gray_area_public_creator_fan_surfaces": "https://commons.wikimedia.org/wiki/File:Kelly_Miller_WNBA.jpg",
            "source_category": "editorial_wire",
            "source_domain": "gettyimages.com",
            "likely_search_query_macro": "{player_name} WNBA match action",
            "identity_verification_anchor": "https://www.wnba.com/players",
            "rights_posture_recommendation": "editorial_wire_rights_sensitive",
            "limitations_red_flags": "URL-only pointer; do not cache or persist images; verify active roster/team manually.",
            "source_family_rank": "1",
            "source_family_name": "Getty Images Editorial Sports",
            "source_family_yield": "Ultra-High",
            "source_family_function": "Verify active match-action photo existence in real time.",
        },
        {
            "sport": "Soccer",
            "league_entity": "NWSL",
            "official_gallery_url_or_macro": "https://www.nwslsoccer.com/photos",
            "roster_player_directory_url_or_macro": "https://www.nwslsoccer.com/stats/players/all",
            "media_guide_stats_profile_url_or_macro": "https://www.nwslsoccer.com/press/media-guides",
            "editorial_wire_newsroom_sources": "https://isiphotos.photoshelter.com/gallery-collection/C00002Y8lb20itTM",
            "official_social": "https://x.com/NWSL",
            "gray_area_public_creator_fan_surfaces": "https://www.alamy.com/stock-photo/nwsl.html",
            "source_category": "reputable_newsroom_gallery",
            "source_domain": "isiphotos.com",
            "likely_search_query_macro": "{player_name} NWSL soccer",
            "identity_verification_anchor": "https://fbref.com/en/comps/182/NWSL-Stats",
            "rights_posture_recommendation": "official_partner_licensed_manual_review",
            "limitations_red_flags": "ISI/specialist soccer coverage is a discovery lead; verify club, roster, and match date manually.",
            "source_family_rank": "2",
            "source_family_name": "ISI Photos Archive",
            "source_family_yield": "High",
            "source_family_function": "Check historical progression and current club matches for soccer players.",
        },
        {
            "sport": "Soccer",
            "league_entity": "USWNT / U.S. Soccer",
            "official_gallery_url_or_macro": "https://www.ussoccer.com/media-services/media-contacts",
            "roster_player_directory_url_or_macro": "https://www.ussoccer.com/teams/uswnt",
            "media_guide_stats_profile_url_or_macro": "https://www.ussoccer.com/media-services/media-contacts",
            "editorial_wire_newsroom_sources": "https://www.gettyimages.com/photos/nwsl-soccer",
            "official_social": "https://x.com/USWNT",
            "gray_area_public_creator_fan_surfaces": "https://isiphotos.photoshelter.com/gallery-collection/C00002Y8lb20itTM",
            "source_category": "official_federation_or_tournament",
            "source_domain": "ussoccer.com",
            "likely_search_query_macro": "{player_name} USWNT starting XI",
            "identity_verification_anchor": "https://www.ussoccer.com/teams/uswnt",
            "rights_posture_recommendation": "official_review_needed",
            "limitations_red_flags": "Federation/media-service surfaces are identity anchors and lead maps, not approval.",
            "source_family_rank": "2",
            "source_family_name": "ISI Photos Archive",
            "source_family_yield": "High",
            "source_family_function": "Cross-check national-team action leads with federation roster context.",
        },
        {
            "sport": "Basketball",
            "league_entity": "NCAA Women Basketball",
            "official_gallery_url_or_macro": "https://ncaaphotos.photoshelter.com/",
            "roster_player_directory_url_or_macro": "{school} women's basketball roster official",
            "media_guide_stats_profile_url_or_macro": "https://www.clarkson-creative.com/schwaberow",
            "editorial_wire_newsroom_sources": "http://fs.ncaa.org/Docs/PressArchive/2009/Announcements/20090210_ap_image_rls.html",
            "official_social": "https://x.com/NCAAWBB",
            "gray_area_public_creator_fan_surfaces": "https://www.flickr.com/photos/keithallison/",
            "source_category": "official_federation_or_tournament",
            "source_domain": "ncaaphotos.photoshelter.com",
            "likely_search_query_macro": "{player_name} NCAA March Madness basketball",
            "identity_verification_anchor": "{school} women's basketball roster official",
            "rights_posture_recommendation": "official_partner_licensed_manual_review",
            "limitations_red_flags": "Separate championship leads from school regular-season leads; verify athlete identity manually.",
            "source_family_rank": "3",
            "source_family_name": "NCAA Photos / Clarkson Creative",
            "source_family_yield": "High",
            "source_family_function": "Track championship tournament action sequences via keyword tags.",
        },
        {
            "sport": "Softball",
            "league_entity": "NCAA Women Softball",
            "official_gallery_url_or_macro": "https://ncaaphotos.photoshelter.com/",
            "roster_player_directory_url_or_macro": "{school} softball roster official",
            "media_guide_stats_profile_url_or_macro": "https://www.clarkson-creative.com/schwaberow",
            "editorial_wire_newsroom_sources": "http://fs.ncaa.org/Docs/PressArchive/2009/Announcements/20090210_ap_image_rls.html",
            "official_social": "https://x.com/NCAASoftball",
            "gray_area_public_creator_fan_surfaces": "https://www.flickr.com/photos/keithallison/",
            "source_category": "official_federation_or_tournament",
            "source_domain": "ncaaphotos.photoshelter.com",
            "likely_search_query_macro": "{player_name} Women College World Series softball",
            "identity_verification_anchor": "{school} softball roster official",
            "rights_posture_recommendation": "official_partner_licensed_manual_review",
            "limitations_red_flags": "Championship archives and school images are candidate leads until human verified.",
            "source_family_rank": "3",
            "source_family_name": "NCAA Photos / Clarkson Creative",
            "source_family_yield": "High",
            "source_family_function": "Track championship softball action sequences.",
        },
        {
            "sport": "Volleyball",
            "league_entity": "NCAA Women Volleyball",
            "official_gallery_url_or_macro": "https://ncaaphotos.photoshelter.com/",
            "roster_player_directory_url_or_macro": "{school} volleyball roster official",
            "media_guide_stats_profile_url_or_macro": "https://www.clarkson-creative.com/about-us",
            "editorial_wire_newsroom_sources": "http://fs.ncaa.org/Docs/PressArchive/2009/Announcements/20090210_ap_image_rls.html",
            "official_social": "https://x.com/NCAAVolleyball",
            "gray_area_public_creator_fan_surfaces": "https://www.flickr.com/photos/keithallison/",
            "source_category": "official_federation_or_tournament",
            "source_domain": "ncaaphotos.photoshelter.com",
            "likely_search_query_macro": "{player_name} NCAA volleyball championship",
            "identity_verification_anchor": "{school} volleyball roster official",
            "rights_posture_recommendation": "official_partner_licensed_manual_review",
            "limitations_red_flags": "Use player/school pages as identity anchors; photo leads remain advisory.",
            "source_family_rank": "3",
            "source_family_name": "NCAA Photos / Clarkson Creative",
            "source_family_yield": "High",
            "source_family_function": "Track championship volleyball action sequences.",
        },
        {
            "sport": "Soccer",
            "league_entity": "NCAA Women Soccer",
            "official_gallery_url_or_macro": "https://ncaaphotos.photoshelter.com/",
            "roster_player_directory_url_or_macro": "{school} women's soccer roster official",
            "media_guide_stats_profile_url_or_macro": "https://www.isiphotos.com/about",
            "editorial_wire_newsroom_sources": "http://fs.ncaa.org/Docs/PressArchive/2009/Announcements/20090210_ap_image_rls.html",
            "official_social": "https://x.com/NCAASoccer",
            "gray_area_public_creator_fan_surfaces": "https://www.isiphotos.com/all-collections",
            "source_category": "official_federation_or_tournament",
            "source_domain": "ncaaphotos.photoshelter.com",
            "likely_search_query_macro": "{player_name} NCAA women soccer college cup",
            "identity_verification_anchor": "{school} women's soccer roster official",
            "rights_posture_recommendation": "official_partner_licensed_manual_review",
            "limitations_red_flags": "NCAA/ISI overlap is a source-family clue only; verify player, school, and event manually.",
            "source_family_rank": "3",
            "source_family_name": "NCAA Photos / Clarkson Creative",
            "source_family_yield": "High",
            "source_family_function": "Track championship soccer action sequences.",
        },
        {
            "sport": "Tennis",
            "league_entity": "WTA Tennis",
            "official_gallery_url_or_macro": "https://www.wtatennis.com/media",
            "roster_player_directory_url_or_macro": "https://www.wtatennis.com/players-hub",
            "media_guide_stats_profile_url_or_macro": "https://www.wtatennis.com/news/1350286/wta-media-guide",
            "editorial_wire_newsroom_sources": "https://www.wtatennis.com/match-notes",
            "official_social": "https://x.com/WTA",
            "gray_area_public_creator_fan_surfaces": "https://www.flickr.com/photos/keithallison/",
            "source_category": "official_league_gallery",
            "source_domain": "wtatennis.com",
            "likely_search_query_macro": "{player_name} WTA match action",
            "identity_verification_anchor": "https://www.wtatennis.com/players-hub",
            "rights_posture_recommendation": "official_review_needed",
            "limitations_red_flags": "Use WTA as identity/match context; find action-photo leads separately.",
            "source_family_rank": "7",
            "source_family_name": "WTA Corporate Match Notes",
            "source_family_yield": "Medium",
            "source_family_function": "Sync tournament scheduling with candidate photo availability.",
        },
        {
            "sport": "Golf",
            "league_entity": "LPGA Golf",
            "official_gallery_url_or_macro": "https://media.lpga.com/",
            "roster_player_directory_url_or_macro": "https://www.lpga.com/athletes/directory",
            "media_guide_stats_profile_url_or_macro": "https://www.lpga.com/news-and-video",
            "editorial_wire_newsroom_sources": "https://www.gettyimages.com/photos/lpga",
            "official_social": "https://x.com/LPGA",
            "gray_area_public_creator_fan_surfaces": "https://commons.wikimedia.org/wiki/File:Michelle_Wie_-_Flickr_-_Keith_Allison_(3).jpg",
            "source_category": "official_league_gallery",
            "source_domain": "lpga.com",
            "likely_search_query_macro": "{player_name} LPGA swing",
            "identity_verification_anchor": "https://www.lpga.com/stats-and-rankings",
            "rights_posture_recommendation": "official_review_needed",
            "limitations_red_flags": "Use LPGA pages for identity, round, and tournament context; action leads remain advisory.",
            "source_family_rank": "6",
            "source_family_name": "LPGA On-Site Media Hub",
            "source_family_yield": "Medium",
            "source_family_function": "Review golf action/swing lead availability at major events.",
        },
        {
            "sport": "Hockey",
            "league_entity": "PWHL / Women Hockey",
            "official_gallery_url_or_macro": "https://www.thepwhl.com/en/sample-content/image-gallery",
            "roster_player_directory_url_or_macro": "https://www.thepwhl.com/en/teams/san-jose/roster-tracker",
            "media_guide_stats_profile_url_or_macro": "https://www.eliteprospects.com/league/pwhl-w",
            "editorial_wire_newsroom_sources": "https://www.gettyimages.com/photos/pwhl",
            "official_social": "https://x.com/thepwhlofficial",
            "gray_area_public_creator_fan_surfaces": "https://www.theixsports.com/the-ice-garden/multimedia/photography/film-photo-gallery-pwhl-boston-wins-semifinal-game-3/",
            "source_category": "editorial_wire",
            "source_domain": "gettyimages.com",
            "likely_search_query_macro": "{player_name} PWHL hockey game action",
            "identity_verification_anchor": "https://www.eliteprospects.com/league/pwhl-w",
            "rights_posture_recommendation": "editorial_wire_rights_sensitive",
            "limitations_red_flags": "Independent hockey galleries are creator leads; verify credit, event, and player manually.",
            "source_family_rank": "9",
            "source_family_name": "The Ice Garden Portfolio Network",
            "source_family_yield": "Medium-Low",
            "source_family_function": "Discover localized hockey images through credentialed independent creators.",
        },
        {
            "sport": "Softball",
            "league_entity": "AUSL / Pro Softball",
            "official_gallery_url_or_macro": "https://theausl.com/",
            "roster_player_directory_url_or_macro": "https://theausl.com/volts/roster/",
            "media_guide_stats_profile_url_or_macro": "https://theausl.com/",
            "editorial_wire_newsroom_sources": "https://www.gettyimages.com/photos/ausl-softball",
            "official_social": "https://x.com/theausl",
            "gray_area_public_creator_fan_surfaces": "https://www.jadehewittmedia.com/about",
            "source_category": "official_league_gallery",
            "source_domain": "theausl.com",
            "likely_search_query_macro": "{player_name} AUSL softball action",
            "identity_verification_anchor": "https://theausl.com/talons/news/utah-talons-2026-opening-day-roster/",
            "rights_posture_recommendation": "official_review_needed",
            "limitations_red_flags": "AUSL/Athletes Unlimited public imagery is a source lead and identity clue only.",
            "source_family_rank": "5",
            "source_family_name": "Athletes Unlimited / AUSL Media Hub",
            "source_family_yield": "Medium-High",
            "source_family_function": "Monitor narrative-focused professional softball imagery.",
        },
        {
            "sport": "Multi-sport",
            "league_entity": "AP Images Sports Portal",
            "official_gallery_url_or_macro": "operator_fill_required",
            "roster_player_directory_url_or_macro": "{league_or_school} roster/player profile official",
            "media_guide_stats_profile_url_or_macro": "{event} media guide stats official",
            "editorial_wire_newsroom_sources": "https://newsroom.ap.org/",
            "official_social": "operator_fill_required",
            "gray_area_public_creator_fan_surfaces": "operator_fill_required",
            "source_category": "editorial_wire",
            "source_domain": "newsroom.ap.org",
            "likely_search_query_macro": "{player_name} {team} photo AP Images",
            "identity_verification_anchor": "official roster/player profile plus event context",
            "rights_posture_recommendation": "editorial_wire_rights_sensitive",
            "limitations_red_flags": "National wire source-family clue only; do not fetch previews or assume rights.",
            "source_family_rank": "4",
            "source_family_name": "AP Images Sports Portal",
            "source_family_yield": "High",
            "source_family_function": "Cross-check national collegiate histories with commercial availability.",
        },
        {
            "sport": "Multi-sport",
            "league_entity": "Keith Allison Flickr legacy references",
            "official_gallery_url_or_macro": "operator_fill_required",
            "roster_player_directory_url_or_macro": "official player profile or historical roster",
            "media_guide_stats_profile_url_or_macro": "official stats/media guide where available",
            "editorial_wire_newsroom_sources": "operator_fill_required",
            "official_social": "operator_fill_required",
            "gray_area_public_creator_fan_surfaces": "https://www.flickr.com/photos/keithallison/",
            "source_category": "gray_area_public_lead",
            "source_domain": "flickr.com",
            "likely_search_query_macro": "{player_name} Keith Allison Flickr",
            "identity_verification_anchor": "official roster/player profile and event date context",
            "rights_posture_recommendation": "gray_area_lead_only",
            "limitations_red_flags": "Legacy/public creator references are discovery/identity clues only.",
            "source_family_rank": "8",
            "source_family_name": "Keith Allison Flickr Archive",
            "source_family_yield": "Medium",
            "source_family_function": "Find historical player profile references.",
        },
        {
            "sport": "Hockey",
            "league_entity": "Inside the Rink galleries",
            "official_gallery_url_or_macro": "operator_fill_required",
            "roster_player_directory_url_or_macro": "official PWHL/team roster or Elite Prospects",
            "media_guide_stats_profile_url_or_macro": "official game sheet or stats profile",
            "editorial_wire_newsroom_sources": "operator_fill_required",
            "official_social": "operator_fill_required",
            "gray_area_public_creator_fan_surfaces": "Inside the Rink galleries",
            "source_category": "third_party_creator_public",
            "source_domain": "insidetherink.com",
            "likely_search_query_macro": "{player_name} PWHL Inside the Rink gallery",
            "identity_verification_anchor": "official roster/player profile and game sheet",
            "rights_posture_recommendation": "third_party_creator_uncleared",
            "limitations_red_flags": "Regional creator galleries are useful lead surfaces, not rights or roster truth.",
            "source_family_rank": "10",
            "source_family_name": "Inside the Rink Galleries",
            "source_family_yield": "Low-Medium",
            "source_family_function": "Track regional game-by-game hockey player lineups.",
        },
    ]
    return [{**base, **row} for row in rows]


def validate_external_research_source_map_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen = set()
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in EXTERNAL_RESEARCH_SOURCE_MAP_FIELDS}
        key = (
            normalized["sport"],
            normalized["league_entity"],
            normalized["source_category"],
            normalized["source_domain"],
            normalized["likely_search_query_macro"],
        )
        if key in seen:
            issues.append({"row": str(index), "field": "likely_search_query_macro", "issue": "duplicate_external_research_source_map_key"})
        seen.add(key)
        if normalized["source_category"] not in SOURCE_CATEGORIES:
            issues.append({"row": str(index), "field": "source_category", "issue": "invalid_controlled_vocabulary"})
        if normalized["rights_posture_recommendation"] not in RIGHTS_CLASSES:
            issues.append({"row": str(index), "field": "rights_posture_recommendation", "issue": "invalid_rights_posture_recommendation"})
        for field in [
            "sport",
            "league_entity",
            "official_gallery_url_or_macro",
            "roster_player_directory_url_or_macro",
            "editorial_wire_newsroom_sources",
            "source_domain",
            "likely_search_query_macro",
            "identity_verification_anchor",
            "limitations_red_flags",
            "manual_next_action",
        ]:
            if not normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "required_external_research_field_blank"})
        for field in REQUIRED_DOWNLOAD_FIELDS:
            if normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "generated_local_download_law_field_must_stay_blank"})
        if normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_rows_must_not_approve_downloads"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "external_research_rows_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "external_research_rows_must_not_be_publish_ready"})
        if normalized["approval_state_change"] not in {"", "none"}:
            issues.append({"row": str(index), "field": "approval_state_change", "issue": "external_research_rows_must_not_change_approval_state"})
        if normalized["publish_action"] not in {"", "none_artifact_only"}:
            issues.append({"row": str(index), "field": "publish_action", "issue": "external_research_rows_must_not_publish"})
    return issues


def render_external_research_source_map(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    sport_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    for row in rows:
        sport = clean(row.get("sport"))
        category = clean(row.get("source_category"))
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
    ranked = sorted(
        [row for row in rows if clean(row.get("source_family_rank")).isdigit()],
        key=lambda row: int(clean(row.get("source_family_rank"))),
    )
    lines = [
        "# Review-Only Action Photo External Research Source Map",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Report-digested source-discovery map for action-photo candidate research. Legal-risk framing from the report is treated as non-blocking metadata under HSD's fair-use operating assumption; operational guardrails still apply. Rows are advisory URL/search leads only and are not approval, current roster truth, downloads, or render-ready state.",
        "",
        "## Operator Paste Note",
        "",
        "Paste ChatGPT Pro, Gemini, or manual research outputs as URL/evidence rows only. Official/player pages are identity anchors; wires, newsrooms, social, creator galleries, and gray-area public surfaces are candidate-photo discovery leads. Keep generated local-download-law fields blank/no unless a later human-edited intake row explicitly satisfies the quarantine-only download law.",
        "",
        "## Summary",
        "",
        f"- Source-map rows: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        f"- Review-only rows: `{sum(1 for row in rows if clean(row.get('review_only')) == 'true')}`",
        f"- Publish-ready rows: `{sum(1 for row in rows if clean(row.get('publish_ready')) == 'true')}`",
        "",
        "## Sport Coverage",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(sport_counts.items()))
    lines += ["", "## Source Category Coverage", ""]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(category_counts.items()))
    lines += ["", "## High-Yield Source Families", ""]
    for row in ranked:
        lines.append(
            "- {rank}. {name}: {target} / {yield_rating} / {function}".format(
                rank=clean(row.get("source_family_rank")),
                name=clean(row.get("source_family_name")),
                target=clean(row.get("league_entity")),
                yield_rating=clean(row.get("source_family_yield")),
                function=clean(row.get("source_family_function")),
            )
        )
    lines += [
        "",
        "## Board Preview",
        "",
        "| Sport | League/Entity | Category | Domain | Search Macro | Identity Anchor | Rights Metadata | Manual Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {sport} | {league} | {category} | {domain} | `{macro}` | {anchor} | {rights} | {action} |".format(
                sport=clean(row.get("sport")),
                league=clean(row.get("league_entity")).replace("|", "/"),
                category=clean(row.get("source_category")),
                domain=clean(row.get("source_domain")).replace("|", "/"),
                macro=clean(row.get("likely_search_query_macro")).replace("|", "/"),
                anchor=clean(row.get("identity_verification_anchor")).replace("|", "/"),
                rights=clean(row.get("rights_posture_recommendation")),
                action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def action_photo_candidate_queue_rows() -> List[Dict[str, str]]:
    default_action = (
        "Fill candidate_photo_url, evidence_url, evidence_summary, and identity_anchor_url after manual or "
        "ChatGPT/Gemini research; keep download_approved=no unless a later human-edited intake satisfies the quarantine law."
    )
    base = {
        "target_entity_or_player": "operator_fill_player_or_team",
        "candidate_photo_url": "",
        "evidence_url": "",
        "evidence_summary": "",
        "identity_anchor_url": "",
        "download_approved": "no",
        "source_url": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "manual_reviewer": "",
        "manual_review_status": "not_reviewed",
        "manual_next_action": default_action,
        "review_only": "true",
        "publish_ready": "false",
        "fair_use_context_note": "fair_use_assumption_for_research_queue_only_not_auto_approval_or_publish_ready",
    }
    row_specs = [
        ("APQ001", "basketball", "WNBA", "Getty Images Editorial Sports", "editorial_wire", "{player_name} WNBA match action site:gettyimages.com", "transition_drive|block|rebound|celebration", "high_action_fit_if_full_body_or_clean_face", "editorial_wire_rights_sensitive"),
        ("APQ002", "basketball", "WNBA", "WNBA official league/team galleries", "official_league_gallery", "{player_name} {team} site:wnba.com OR site:{team}.wnba.com photos OR gallery OR recap", "game_action|bench_reaction|celebration", "high_context_fit_if_captioned_current_event", "official_review_needed"),
        ("APQ003", "soccer", "NWSL", "ISI Photos Archive", "reputable_newsroom_gallery", "{player_name} {club} NWSL isiphotos photoshelter action", "dribble|shot|save|celebration", "high_action_fit_if_match_context_and_identity_anchor_are_clear", "newsroom_photo_rights_sensitive"),
        ("APQ004", "soccer", "USWNT / U.S. Soccer", "ISI Photos / U.S. Soccer", "official_federation_or_tournament", "{player_name} USWNT match action ISI Photos OR ussoccer photos", "national_team_action|goal_celebration|defensive_play", "high_fit_for_international_context_if roster_anchor_present", "official_review_needed"),
        ("APQ005", "basketball", "NCAA Women Basketball", "NCAA Photos / Clarkson Creative", "official_federation_or_tournament", "{player_name} NCAA March Madness basketball ncaaphotos photoshelter", "drive|jump_shot|celebration|defense", "medium_high_fit_if_school_and_event_are_current", "official_partner_licensed_manual_review"),
        ("APQ006", "softball", "NCAA Women Softball", "NCAA Photos / Clarkson Creative", "official_federation_or_tournament", "{player_name} Women College World Series softball ncaaphotos photoshelter", "swing|pitch|slide|fielding", "high_fit_if_action_shape_is_readable", "official_partner_licensed_manual_review"),
        ("APQ007", "hockey", "PWHL", "Getty / Ice Garden / Inside the Rink", "editorial_wire", "{player_name} PWHL game action Getty OR Ice Garden OR Inside the Rink gallery", "skate|shot|save|celebration", "medium_high_fit_if_face_or_number_is_clear", "editorial_wire_rights_sensitive"),
        ("APQ008", "softball", "AUSL / Pro Softball", "Athletes Unlimited / AUSL Media Hub", "official_league_gallery", "{player_name} AUSL softball action site:theausl.com OR Jade Hewitt", "swing|pitch|fielding|dugout_celebration", "high_fit_if official event context is clear", "official_review_needed"),
        ("APQ009", "tennis", "WTA Tennis", "WTA / Getty", "official_league_gallery", "{player_name} WTA match action site:wtatennis.com OR site:gettyimages.com", "serve|forehand|backhand|celebration", "high_fit_if ball/racket/body_line_clear", "official_review_needed"),
        ("APQ010", "golf", "LPGA Golf", "LPGA / Getty", "official_league_gallery", "{player_name} LPGA swing site:lpga.com OR site:gettyimages.com", "drive|approach|putt|celebration", "medium_fit_if pose is dynamic and athlete identity is anchored", "official_review_needed"),
    ]
    rows: List[Dict[str, str]] = []
    for queue_id, sport, league, family, category, macro, moment, fit, rights in row_specs:
        rows.append(
            {
                **base,
                "candidate_queue_id": queue_id,
                "sport": sport,
                "league_entity": league,
                "source_family": family,
                "source_category": category,
                "source_url_or_search_macro": macro,
                "action_moment_type": moment,
                "render_fit_potential": fit,
                "rights_posture_metadata": rights,
                "quarantine_target_hint": f"{QUARANTINE_ROOT}/action_photo_candidates/{slug(league)}/{queue_id.lower()}/operator_fill_required.jpg",
            }
        )
    return rows


def validate_action_photo_candidate_queue_rows(rows: Iterable[Mapping[str, str]]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    seen_ids = set()
    seen_keys = set()
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in ACTION_PHOTO_QUEUE_FIELDS}
        queue_id = normalized["candidate_queue_id"]
        if not queue_id:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "required_candidate_queue_id_blank"})
        elif queue_id in seen_ids:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "duplicate_candidate_queue_id"})
        seen_ids.add(queue_id)
        key = (
            normalized["sport"],
            normalized["league_entity"],
            normalized["source_family"],
            normalized["source_category"],
            normalized["source_url_or_search_macro"],
        )
        if key in seen_keys:
            issues.append({"row": str(index), "field": "source_url_or_search_macro", "issue": "duplicate_candidate_queue_key"})
        seen_keys.add(key)
        if normalized["source_category"] not in SOURCE_CATEGORIES:
            issues.append({"row": str(index), "field": "source_category", "issue": "invalid_controlled_vocabulary"})
        if normalized["rights_posture_metadata"] and normalized["rights_posture_metadata"] not in RIGHTS_CLASSES:
            issues.append({"row": str(index), "field": "rights_posture_metadata", "issue": "invalid_rights_posture_metadata"})
        for field in [
            "sport",
            "league_entity",
            "target_entity_or_player",
            "source_family",
            "source_url_or_search_macro",
            "action_moment_type",
            "render_fit_potential",
            "fair_use_context_note",
            "quarantine_target_hint",
            "manual_next_action",
        ]:
            if not normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "required_candidate_queue_field_blank"})
        for field in ["candidate_photo_url", "evidence_url", "evidence_summary", "identity_anchor_url", "manual_reviewer"]:
            if normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "generated_manual_candidate_field_must_stay_blank"})
        for field in REQUIRED_DOWNLOAD_FIELDS:
            if normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "generated_local_download_law_field_must_stay_blank"})
        if normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_rows_must_not_approve_downloads"})
        if not normalized["quarantine_target_hint"].startswith(QUARANTINE_ROOT + "/"):
            issues.append({"row": str(index), "field": "quarantine_target_hint", "issue": "quarantine_hint_must_stay_in_review_only_root"})
        if normalized["manual_review_status"] != "not_reviewed":
            issues.append({"row": str(index), "field": "manual_review_status", "issue": "generated_queue_rows_must_start_not_reviewed"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "candidate_queue_rows_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "candidate_queue_rows_must_not_be_publish_ready"})
    return issues


def render_action_photo_candidate_queue(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    sport_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    for row in rows:
        sport = clean(row.get("sport"))
        family = clean(row.get("source_family"))
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
        source_counts[family] = source_counts.get(family, 0) + 1
    lines = [
        "# Review-Only Action Photo Candidate Queue v1",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Concrete candidate-research queue seeded from the action-photo source maps. These rows are prompts for finding real action-photo candidate URLs and evidence; they do not download images, approve assets, assert roster truth, or make anything render-ready.",
        "",
        "## Operator Note",
        "",
        "Fill `candidate_photo_url`, `evidence_url`, `evidence_summary`, and `identity_anchor_url` after manual or ChatGPT/Gemini research. `download_approved=yes` remains human-edited only, requires `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use`, and any later file must land in quarantine. Asset approval and render-ready state remain separate.",
        "",
        "## Summary",
        "",
        f"- Queue rows: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        f"- Review-only rows: `{sum(1 for row in rows if clean(row.get('review_only')) == 'true')}`",
        f"- Publish-ready rows: `{sum(1 for row in rows if clean(row.get('publish_ready')) == 'true')}`",
        "",
        "## Sport Coverage",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(sport_counts.items()))
    lines += ["", "## Source Families", ""]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(source_counts.items()))
    lines += [
        "",
        "## Queue Preview",
        "",
        "| Queue ID | Sport | League/Entity | Source Family | Moment Type | Search Macro | Manual Next Action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {queue_id} | {sport} | {league} | {family} | {moment} | `{macro}` | {action} |".format(
                queue_id=clean(row.get("candidate_queue_id")),
                sport=clean(row.get("sport")),
                league=clean(row.get("league_entity")).replace("|", "/"),
                family=clean(row.get("source_family")).replace("|", "/"),
                moment=clean(row.get("action_moment_type")).replace("|", "/"),
                macro=clean(row.get("source_url_or_search_macro")).replace("|", "/"),
                action=clean(row.get("manual_next_action")).replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def research_lane_for_queue_row(row: Mapping[str, str]) -> str:
    category = clean(row.get("source_category"))
    rights = clean(row.get("rights_posture_metadata"))
    if category in {"official_league_gallery", "official_federation_or_tournament", "official_team_gallery"}:
        return "chatgpt_pro"
    if rights in {"official_partner_licensed_manual_review", "editorial_wire_rights_sensitive"}:
        return "manual_research"
    return "gemini_pro"


def prompt_for_research_task(row: Mapping[str, str], lane: str) -> str:
    lane_label = {
        "chatgpt_pro": "ChatGPT Pro",
        "gemini_pro": "Gemini Pro",
        "manual_research": "manual researcher",
    }[lane]
    return (
        f"You are a {lane_label} URL/evidence researcher for HSD review-only action-photo candidates. "
        f"Queue ID: {clean(row.get('candidate_queue_id'))}. Sport/entity: {clean(row.get('sport'))} / {clean(row.get('league_entity'))}. "
        f"Target: replace operator_fill_player_or_team with the player or team being researched. "
        f"Source family/category: {clean(row.get('source_family'))} / {clean(row.get('source_category'))}. "
        f"Search macro or source lead: {clean(row.get('source_url_or_search_macro'))}. "
        f"Look for action-photo candidate page URLs and separate identity/evidence anchors for {clean(row.get('action_moment_type'))}. "
        "Return CSV in a code block with exactly these columns: "
        + ",".join(RESEARCH_PACKET_RETURN_COLUMNS)
        + ". Use source_url as the candidate page/source page, not a downloaded file. "
        "Set operator_verify_required=yes when identity, rights posture, event context, or roster truth needs human confirmation. "
        "Do not download images, do not save files, do not claim approval, do not mark render-ready, and do not change download_approved."
    )


def action_photo_research_packet_rows(queue_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in queue_rows:
        lane = research_lane_for_queue_row(row)
        queue_id = clean(row.get("candidate_queue_id"))
        rows.append(
            {
                "research_task_id": f"APR{queue_id.removeprefix('APQ')}",
                "researcher_lane": lane,
                "candidate_queue_id": queue_id,
                "sport": clean(row.get("sport")),
                "league_entity": clean(row.get("league_entity")),
                "target_entity_or_player": clean(row.get("target_entity_or_player")),
                "source_family": clean(row.get("source_family")),
                "source_category": clean(row.get("source_category")),
                "source_url_or_search_macro": clean(row.get("source_url_or_search_macro")),
                "action_moment_type": clean(row.get("action_moment_type")),
                "render_fit_potential": clean(row.get("render_fit_potential")),
                "rights_posture_metadata": clean(row.get("rights_posture_metadata")),
                "copy_ready_prompt": prompt_for_research_task(row, lane),
                "paste_back_schema": ",".join(RESEARCH_PACKET_RETURN_COLUMNS),
                "candidate_photo_url": "",
                "evidence_url": "",
                "evidence_summary": "",
                "identity_anchor_url": "",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "notes": "",
                "operator_verify_required": "yes",
                "download_approved": "no",
                "manual_next_action": "Send the copy-ready prompt to ChatGPT Pro, Gemini Pro, or a manual researcher; paste returned CSV rows into a human review worksheet before any download decision.",
                "review_only": "true",
                "publish_ready": "false",
            }
        )
    return rows


def validate_action_photo_research_packet_rows(
    packet_rows: Iterable[Mapping[str, str]],
    queue_rows: Iterable[Mapping[str, str]],
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    queue_ids = {clean(row.get("candidate_queue_id")) for row in queue_rows}
    seen_task_ids = set()
    seen_queue_ids = set()
    valid_lanes = {"chatgpt_pro", "gemini_pro", "manual_research"}
    required_prompt_fragments = [
        "Return CSV in a code block",
        "candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required",
        "Do not download images",
        "do not claim approval",
        "do not mark render-ready",
    ]
    rows = list(packet_rows)
    for index, row in enumerate(rows, start=2):
        normalized = {field: clean(row.get(field)) for field in ACTION_PHOTO_RESEARCH_PACKET_FIELDS}
        task_id = normalized["research_task_id"]
        queue_id = normalized["candidate_queue_id"]
        if not task_id:
            issues.append({"row": str(index), "field": "research_task_id", "issue": "required_research_task_id_blank"})
        elif task_id in seen_task_ids:
            issues.append({"row": str(index), "field": "research_task_id", "issue": "duplicate_research_task_id"})
        seen_task_ids.add(task_id)
        if queue_id not in queue_ids:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "candidate_queue_id_not_in_queue"})
        if queue_id in seen_queue_ids:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "duplicate_candidate_queue_id_in_research_packet"})
        seen_queue_ids.add(queue_id)
        if normalized["researcher_lane"] not in valid_lanes:
            issues.append({"row": str(index), "field": "researcher_lane", "issue": "invalid_researcher_lane"})
        if normalized["source_category"] not in SOURCE_CATEGORIES:
            issues.append({"row": str(index), "field": "source_category", "issue": "invalid_controlled_vocabulary"})
        if normalized["rights_posture_metadata"] and normalized["rights_posture_metadata"] not in RIGHTS_CLASSES:
            issues.append({"row": str(index), "field": "rights_posture_metadata", "issue": "invalid_rights_posture_metadata"})
        for field in [
            "sport",
            "league_entity",
            "target_entity_or_player",
            "source_family",
            "source_url_or_search_macro",
            "action_moment_type",
            "render_fit_potential",
            "copy_ready_prompt",
            "paste_back_schema",
            "manual_next_action",
        ]:
            if not normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "required_research_packet_field_blank"})
        for fragment in required_prompt_fragments:
            if fragment not in normalized["copy_ready_prompt"]:
                issues.append({"row": str(index), "field": "copy_ready_prompt", "issue": "copy_ready_prompt_missing_required_guardrail"})
        if normalized["paste_back_schema"] != ",".join(RESEARCH_PACKET_RETURN_COLUMNS):
            issues.append({"row": str(index), "field": "paste_back_schema", "issue": "paste_back_schema_mismatch"})
        for field in ["candidate_photo_url", "evidence_url", "evidence_summary", "identity_anchor_url", "source_url", "entity_id", "rights_class", "identity_confidence", "intended_review_only_use", "notes"]:
            if normalized[field]:
                issues.append({"row": str(index), "field": field, "issue": "generated_research_result_field_must_stay_blank"})
        if normalized["operator_verify_required"] != "yes":
            issues.append({"row": str(index), "field": "operator_verify_required", "issue": "operator_verify_required_must_default_yes"})
        if normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "generated_rows_must_not_approve_downloads"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "research_packet_rows_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "research_packet_rows_must_not_be_publish_ready"})
    missing_ids = sorted(queue_ids - seen_queue_ids)
    for missing_id in missing_ids:
        issues.append({"row": "0", "field": "candidate_queue_id", "issue": f"queue_id_missing_from_research_packet:{missing_id}"})
    return issues


def render_action_photo_research_packet(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    lane_counts: Dict[str, int] = {}
    for row in rows:
        lane = clean(row.get("researcher_lane"))
        lane_counts[lane] = lane_counts.get(lane, 0) + 1
    schema = ",".join(RESEARCH_PACKET_RETURN_COLUMNS)
    lines = [
        "# Review-Only Action Photo Candidate Research Packet v1",
        "",
        f"Generated: `{generated_at}`",
        "",
        "This packet converts the action-photo candidate queue into copy-ready research tasks for Mike, ChatGPT Pro, Gemini Pro, and manual research. It is a bridge toward real candidate-photo URLs and evidence, not a download, approval, or render-ready workflow.",
        "",
        "## Local Download Law",
        "",
        "`download_approved=yes` remains human-edited only after `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` are filled. Any later download must land in `data/assets/quarantine/review_only_candidates/`. Download approval is not asset approval; approval and render-ready status remain separate.",
        "",
        "## What Mike Sends To ChatGPT/Gemini",
        "",
        "Send one task prompt at a time. Ask the researcher to return only URL/evidence rows in a CSV code block. They must not download images, save files, claim approval, assert current roster truth without an identity anchor, or mark anything render-ready.",
        "",
        "## What Mike Pastes Back",
        "",
        "Paste returned rows into a human review worksheet using exactly this schema:",
        "",
        "```csv",
        schema,
        "```",
        "",
        "## Summary",
        "",
        f"- Research tasks: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        f"- Review-only rows: `{sum(1 for row in rows if clean(row.get('review_only')) == 'true')}`",
        f"- Publish-ready rows: `{sum(1 for row in rows if clean(row.get('publish_ready')) == 'true')}`",
        "",
        "## Task Counts",
        "",
    ]
    lines.extend(f"- {lane}: `{count}`" for lane, count in sorted(lane_counts.items()))
    lines += ["", "## Copy-Ready Tasks", ""]
    for row in rows:
        lines.extend(
            [
                f"### {clean(row.get('research_task_id'))}: {clean(row.get('candidate_queue_id'))} - {clean(row.get('league_entity'))}",
                "",
                f"- Researcher lane: `{clean(row.get('researcher_lane'))}`",
                f"- Source family: `{clean(row.get('source_family'))}`",
                f"- Source macro: `{clean(row.get('source_url_or_search_macro'))}`",
                "",
                "```text",
                clean(row.get("copy_ready_prompt")),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def action_photo_research_return_intake_rows(queue_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in queue_rows:
        rows.append(
            {
                "candidate_queue_id": clean(row.get("candidate_queue_id")),
                "candidate_photo_url": "",
                "evidence_url": "",
                "evidence_summary": "",
                "identity_anchor_url": "",
                "source_url": "",
                "entity_id": "",
                "rights_class": "",
                "identity_confidence": "",
                "intended_review_only_use": "",
                "notes": "",
                "operator_verify_required": "yes",
                "manual_reviewer": "",
                "manual_review_status": "not_reviewed",
                "manual_next_action": "Paste returned URL/evidence fields here; keep download_approved=no until a human fills all local-download-law fields and any later file goes to quarantine.",
                "download_approved": "no",
                "quarantine_target_hint": clean(row.get("quarantine_target_hint")),
                "review_only": "true",
                "publish_ready": "false",
            }
        )
    return rows


def has_research_return_data(row: Mapping[str, str]) -> bool:
    return any(
        clean(row.get(field))
        for field in [
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
            "manual_reviewer",
        ]
    )


def validate_action_photo_research_return_intake_rows(
    rows: Iterable[Mapping[str, str]],
    queue_rows: Iterable[Mapping[str, str]],
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    queue_ids = {clean(row.get("candidate_queue_id")) for row in queue_rows}
    seen_queue_ids = set()
    blocked_language_terms = ["approved", "approval", "render-ready", "render ready", "publish-ready", "publish ready"]
    rows_list = list(rows)
    for index, row in enumerate(rows_list, start=2):
        normalized = {field: clean(row.get(field)) for field in ACTION_PHOTO_RESEARCH_RETURN_INTAKE_FIELDS}
        queue_id = normalized["candidate_queue_id"]
        if not queue_id:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "required_candidate_queue_id_blank"})
        elif queue_id not in queue_ids:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "candidate_queue_id_not_in_queue"})
        if queue_id in seen_queue_ids:
            issues.append({"row": str(index), "field": "candidate_queue_id", "issue": "duplicate_candidate_queue_id_in_return_intake"})
        seen_queue_ids.add(queue_id)
        if normalized["rights_class"] and normalized["rights_class"] not in RIGHTS_CLASSES:
            issues.append({"row": str(index), "field": "rights_class", "issue": "invalid_controlled_vocabulary"})
        if normalized["identity_confidence"] and normalized["identity_confidence"] not in IDENTITY_CONFIDENCE:
            issues.append({"row": str(index), "field": "identity_confidence", "issue": "invalid_controlled_vocabulary"})
        pasted_data = has_research_return_data(normalized)
        if pasted_data:
            for field in ["evidence_url", "source_url", "identity_anchor_url", "rights_class", "identity_confidence"]:
                if not normalized[field]:
                    issues.append({"row": str(index), "field": field, "issue": "required_when_research_return_pasted"})
        if normalized["download_approved"] == "yes":
            for field in REQUIRED_DOWNLOAD_FIELDS:
                if not normalized[field]:
                    issues.append({"row": str(index), "field": field, "issue": "required_when_download_approved_yes"})
        elif normalized["download_approved"] != "no":
            issues.append({"row": str(index), "field": "download_approved", "issue": "download_approved_must_be_no_or_human_yes"})
        if not normalized["quarantine_target_hint"].startswith(QUARANTINE_ROOT + "/"):
            issues.append({"row": str(index), "field": "quarantine_target_hint", "issue": "quarantine_hint_must_stay_in_review_only_root"})
        if normalized["operator_verify_required"] not in {"yes", "no", ""}:
            issues.append({"row": str(index), "field": "operator_verify_required", "issue": "operator_verify_required_must_be_yes_no_or_blank"})
        if normalized["manual_review_status"] not in {"not_reviewed", "needs_operator_verify", "ready_for_human_download_decision", "held_for_rights_or_identity", "rejected_do_not_pursue", ""}:
            issues.append({"row": str(index), "field": "manual_review_status", "issue": "invalid_manual_review_status"})
        if normalized["review_only"] != "true":
            issues.append({"row": str(index), "field": "review_only", "issue": "research_return_rows_must_remain_review_only"})
        if normalized["publish_ready"] != "false":
            issues.append({"row": str(index), "field": "publish_ready", "issue": "research_return_rows_must_not_be_publish_ready"})
        for field in ["evidence_summary", "intended_review_only_use", "notes", "manual_review_status"]:
            value = normalized[field].lower()
            if any(term in value for term in blocked_language_terms):
                issues.append({"row": str(index), "field": field, "issue": "approval_or_render_ready_language_not_allowed"})
    missing_ids = sorted(queue_ids - seen_queue_ids)
    for missing_id in missing_ids:
        issues.append({"row": "0", "field": "candidate_queue_id", "issue": f"queue_id_missing_from_return_intake:{missing_id}"})
    return issues


def render_action_photo_research_return_intake(rows: List[Mapping[str, str]], issues: List[Mapping[str, str]], generated_at: str) -> str:
    lines = [
        "# Review-Only Action Photo Research Return Intake v1",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Human-editable paste-back worksheet for URL/evidence rows returned from the action-photo research packet. This intake is the safe landing zone before any quarantine download decision; it does not download images, approve assets, change approval state, or make anything render-ready.",
        "",
        "## What To Paste Back",
        "",
        "Paste returned ChatGPT/Gemini/manual research values into `candidate_photo_url`, `evidence_url`, `evidence_summary`, `identity_anchor_url`, `source_url`, `entity_id`, `rights_class`, `identity_confidence`, `intended_review_only_use`, `notes`, and `operator_verify_required`. Leave generated rows blank until real research is returned.",
        "",
        "## Human-Only Law",
        "",
        "`download_approved=yes` remains human-edited only after `source_url`, `entity_id`, `rights_class`, `identity_confidence`, and `intended_review_only_use` are filled. Any later file must land in `data/assets/quarantine/review_only_candidates/`. Download approval is not asset approval, and render-ready status remains separate.",
        "",
        "## Validation Checks",
        "",
        "- Unknown or duplicate `candidate_queue_id`",
        "- Pasted return rows missing `evidence_url`, `source_url`, `identity_anchor_url`, `rights_class`, or `identity_confidence`",
        "- `download_approved=yes` without all local-download-law fields",
        "- `publish_ready=true`",
        "- Approval, publish-ready, or render-ready language in pasted notes/status fields",
        "",
        "## Summary",
        "",
        f"- Intake rows: `{len(rows)}`",
        f"- Validation issues: `{len(issues)}`",
        f"- Rows with pasted return data: `{sum(1 for row in rows if has_research_return_data(row))}`",
        f"- Rows with `download_approved=yes`: `{sum(1 for row in rows if clean(row.get('download_approved')) == 'yes')}`",
        f"- Review-only rows: `{sum(1 for row in rows if clean(row.get('review_only')) == 'true')}`",
        f"- Publish-ready rows: `{sum(1 for row in rows if clean(row.get('publish_ready')) == 'true')}`",
        "",
        "## Queue IDs",
        "",
    ]
    for row in rows:
        lines.append(f"- `{clean(row.get('candidate_queue_id'))}` -> {clean(row.get('manual_next_action'))}")
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = TEMPLATE_CREATED_AT_UTC
    rows = [normalize_row(row) for row in template_rows(generated_at)]
    issues = validate_rows(rows)
    source_rows = source_map_rows()
    entity_source_rows = sport_entity_source_map_rows()
    entity_source_issues = validate_entity_source_map_rows(entity_source_rows)
    womens_soccer_rows = womens_soccer_starter_rows()
    womens_soccer_issues = validate_womens_soccer_starter_rows(womens_soccer_rows)
    external_research_rows = external_research_source_map_rows()
    external_research_issues = validate_external_research_source_map_rows(external_research_rows)
    candidate_queue_rows = action_photo_candidate_queue_rows()
    candidate_queue_issues = validate_action_photo_candidate_queue_rows(candidate_queue_rows)
    research_packet_rows = action_photo_research_packet_rows(candidate_queue_rows)
    research_packet_issues = validate_action_photo_research_packet_rows(research_packet_rows, candidate_queue_rows)
    research_return_rows = action_photo_research_return_intake_rows(candidate_queue_rows)
    research_return_issues = validate_action_photo_research_return_intake_rows(research_return_rows, candidate_queue_rows)
    write_csv(OUT_CSV, rows, FIELDS)
    write_text(OUT_MD, render_markdown(rows, issues, generated_at))
    write_text(OUT_TAXONOMY_MD, render_taxonomy(generated_at))
    write_json(OUT_TAXONOMY_JSON, taxonomy_payload())
    write_text(OUT_CHECKLIST_MD, render_checklist(generated_at))
    write_csv(
        OUT_SOURCE_MAP_CSV,
        source_rows,
        ["source_category", "source_priority", "source_examples", "search_macro", "collect_only", "do_not_collect", "rights_posture"],
    )
    write_text(OUT_SOURCE_MAP_MD, render_source_map(source_rows, generated_at))
    write_csv(OUT_ENTITY_SOURCE_MAP_CSV, entity_source_rows, ENTITY_SOURCE_MAP_FIELDS)
    write_text(OUT_ENTITY_SOURCE_MAP_MD, render_entity_source_map(entity_source_rows, entity_source_issues, generated_at))
    write_json(
        OUT_ENTITY_SOURCE_MAP_JSON,
        {
            "version": VERSION,
            "status": "action_photo_sport_entity_source_map_ready" if not entity_source_issues else "action_photo_sport_entity_source_map_has_validation_issues",
            "generated_at_utc": generated_at,
            "source_map_rows": len(entity_source_rows),
            "validation_issue_count": len(entity_source_issues),
            "validation_issues": entity_source_issues,
            "source_categories": sorted({row["source_category"] for row in entity_source_rows}),
            "sports": sorted({row["sport"] for row in entity_source_rows}),
            "download_approved_yes_allowed_rows": sum(1 for row in entity_source_rows if row["allowed_for_download_approved_yes"] == "true"),
            "review_only_rows": sum(1 for row in entity_source_rows if row["review_only"] == "true"),
            "publish_ready_rows": sum(1 for row in entity_source_rows if row["publish_ready"] == "true"),
            "worksheet_csv": OUT_ENTITY_SOURCE_MAP_CSV.as_posix(),
            "worksheet_md": OUT_ENTITY_SOURCE_MAP_MD.as_posix(),
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_csv(OUT_WOMENS_SOCCER_STARTER_CSV, womens_soccer_rows, WOMENS_SOCCER_STARTER_FIELDS)
    write_text(OUT_WOMENS_SOCCER_STARTER_MD, render_womens_soccer_starter(womens_soccer_rows, womens_soccer_issues, generated_at))
    write_json(
        OUT_WOMENS_SOCCER_STARTER_JSON,
        {
            "version": VERSION,
            "status": "womens_soccer_action_photo_starter_ready" if not womens_soccer_issues else "womens_soccer_action_photo_starter_has_validation_issues",
            "generated_at_utc": generated_at,
            "starter_rows": len(womens_soccer_rows),
            "validation_issue_count": len(womens_soccer_issues),
            "validation_issues": womens_soccer_issues,
            "expansion_lanes": sorted({row["expansion_lane"] for row in womens_soccer_rows}),
            "source_categories": sorted({row["source_category"] for row in womens_soccer_rows}),
            "download_approved_yes_rows": sum(1 for row in womens_soccer_rows if row["download_approved"] == "yes"),
            "blank_source_url_rows": sum(1 for row in womens_soccer_rows if not row["source_url"]),
            "blank_entity_id_rows": sum(1 for row in womens_soccer_rows if not row["entity_id"]),
            "blank_rights_class_rows": sum(1 for row in womens_soccer_rows if not row["rights_class"]),
            "blank_identity_confidence_rows": sum(1 for row in womens_soccer_rows if not row["identity_confidence"]),
            "blank_intended_review_only_use_rows": sum(1 for row in womens_soccer_rows if not row["intended_review_only_use"]),
            "review_only_rows": sum(1 for row in womens_soccer_rows if row["review_only"] == "true"),
            "publish_ready_rows": sum(1 for row in womens_soccer_rows if row["publish_ready"] == "true"),
            "worksheet_csv": OUT_WOMENS_SOCCER_STARTER_CSV.as_posix(),
            "worksheet_md": OUT_WOMENS_SOCCER_STARTER_MD.as_posix(),
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_csv(OUT_EXTERNAL_RESEARCH_SOURCE_MAP_CSV, external_research_rows, EXTERNAL_RESEARCH_SOURCE_MAP_FIELDS)
    write_text(OUT_EXTERNAL_RESEARCH_SOURCE_MAP_MD, render_external_research_source_map(external_research_rows, external_research_issues, generated_at))
    write_json(
        OUT_EXTERNAL_RESEARCH_SOURCE_MAP_JSON,
        {
            "version": VERSION,
            "status": "action_photo_external_research_source_map_ready" if not external_research_issues else "action_photo_external_research_source_map_has_validation_issues",
            "generated_at_utc": generated_at,
            "source_map_rows": len(external_research_rows),
            "validation_issue_count": len(external_research_issues),
            "validation_issues": external_research_issues,
            "sports": sorted({row["sport"] for row in external_research_rows}),
            "league_entities": sorted({row["league_entity"] for row in external_research_rows}),
            "source_categories": sorted({row["source_category"] for row in external_research_rows}),
            "source_family_ranked_rows": sum(1 for row in external_research_rows if row["source_family_rank"]),
            "download_approved_yes_rows": sum(1 for row in external_research_rows if row["download_approved"] == "yes"),
            "blank_source_url_rows": sum(1 for row in external_research_rows if not row["source_url"]),
            "blank_entity_id_rows": sum(1 for row in external_research_rows if not row["entity_id"]),
            "blank_rights_class_rows": sum(1 for row in external_research_rows if not row["rights_class"]),
            "blank_identity_confidence_rows": sum(1 for row in external_research_rows if not row["identity_confidence"]),
            "blank_intended_review_only_use_rows": sum(1 for row in external_research_rows if not row["intended_review_only_use"]),
            "review_only_rows": sum(1 for row in external_research_rows if row["review_only"] == "true"),
            "publish_ready_rows": sum(1 for row in external_research_rows if row["publish_ready"] == "true"),
            "worksheet_csv": OUT_EXTERNAL_RESEARCH_SOURCE_MAP_CSV.as_posix(),
            "worksheet_md": OUT_EXTERNAL_RESEARCH_SOURCE_MAP_MD.as_posix(),
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_csv(OUT_CANDIDATE_QUEUE_CSV, candidate_queue_rows, ACTION_PHOTO_QUEUE_FIELDS)
    write_text(OUT_CANDIDATE_QUEUE_MD, render_action_photo_candidate_queue(candidate_queue_rows, candidate_queue_issues, generated_at))
    write_json(
        OUT_CANDIDATE_QUEUE_JSON,
        {
            "version": VERSION,
            "status": "action_photo_candidate_queue_ready" if not candidate_queue_issues else "action_photo_candidate_queue_has_validation_issues",
            "generated_at_utc": generated_at,
            "queue_rows": len(candidate_queue_rows),
            "validation_issue_count": len(candidate_queue_issues),
            "validation_issues": candidate_queue_issues,
            "sports": sorted({row["sport"] for row in candidate_queue_rows}),
            "league_entities": sorted({row["league_entity"] for row in candidate_queue_rows}),
            "source_families": sorted({row["source_family"] for row in candidate_queue_rows}),
            "download_approved_yes_rows": sum(1 for row in candidate_queue_rows if row["download_approved"] == "yes"),
            "blank_candidate_photo_url_rows": sum(1 for row in candidate_queue_rows if not row["candidate_photo_url"]),
            "blank_evidence_url_rows": sum(1 for row in candidate_queue_rows if not row["evidence_url"]),
            "blank_evidence_summary_rows": sum(1 for row in candidate_queue_rows if not row["evidence_summary"]),
            "blank_identity_anchor_url_rows": sum(1 for row in candidate_queue_rows if not row["identity_anchor_url"]),
            "blank_source_url_rows": sum(1 for row in candidate_queue_rows if not row["source_url"]),
            "blank_entity_id_rows": sum(1 for row in candidate_queue_rows if not row["entity_id"]),
            "blank_rights_class_rows": sum(1 for row in candidate_queue_rows if not row["rights_class"]),
            "blank_identity_confidence_rows": sum(1 for row in candidate_queue_rows if not row["identity_confidence"]),
            "blank_intended_review_only_use_rows": sum(1 for row in candidate_queue_rows if not row["intended_review_only_use"]),
            "review_only_rows": sum(1 for row in candidate_queue_rows if row["review_only"] == "true"),
            "publish_ready_rows": sum(1 for row in candidate_queue_rows if row["publish_ready"] == "true"),
            "worksheet_csv": OUT_CANDIDATE_QUEUE_CSV.as_posix(),
            "worksheet_md": OUT_CANDIDATE_QUEUE_MD.as_posix(),
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_csv(OUT_RESEARCH_PACKET_CSV, research_packet_rows, ACTION_PHOTO_RESEARCH_PACKET_FIELDS)
    write_text(OUT_RESEARCH_PACKET_MD, render_action_photo_research_packet(research_packet_rows, research_packet_issues, generated_at))
    write_json(
        OUT_RESEARCH_PACKET_JSON,
        {
            "version": VERSION,
            "status": "action_photo_candidate_research_packet_ready" if not research_packet_issues else "action_photo_candidate_research_packet_has_validation_issues",
            "generated_at_utc": generated_at,
            "research_task_rows": len(research_packet_rows),
            "queue_rows_covered": len({row["candidate_queue_id"] for row in research_packet_rows}),
            "validation_issue_count": len(research_packet_issues),
            "validation_issues": research_packet_issues,
            "researcher_lanes": sorted({row["researcher_lane"] for row in research_packet_rows}),
            "candidate_queue_ids": sorted({row["candidate_queue_id"] for row in research_packet_rows}),
            "paste_back_schema": RESEARCH_PACKET_RETURN_COLUMNS,
            "download_approved_yes_rows": sum(1 for row in research_packet_rows if row["download_approved"] == "yes"),
            "blank_candidate_photo_url_rows": sum(1 for row in research_packet_rows if not row["candidate_photo_url"]),
            "blank_evidence_url_rows": sum(1 for row in research_packet_rows if not row["evidence_url"]),
            "blank_evidence_summary_rows": sum(1 for row in research_packet_rows if not row["evidence_summary"]),
            "blank_identity_anchor_url_rows": sum(1 for row in research_packet_rows if not row["identity_anchor_url"]),
            "blank_source_url_rows": sum(1 for row in research_packet_rows if not row["source_url"]),
            "blank_entity_id_rows": sum(1 for row in research_packet_rows if not row["entity_id"]),
            "blank_rights_class_rows": sum(1 for row in research_packet_rows if not row["rights_class"]),
            "blank_identity_confidence_rows": sum(1 for row in research_packet_rows if not row["identity_confidence"]),
            "blank_intended_review_only_use_rows": sum(1 for row in research_packet_rows if not row["intended_review_only_use"]),
            "blank_notes_rows": sum(1 for row in research_packet_rows if not row["notes"]),
            "operator_verify_required_yes_rows": sum(1 for row in research_packet_rows if row["operator_verify_required"] == "yes"),
            "review_only_rows": sum(1 for row in research_packet_rows if row["review_only"] == "true"),
            "publish_ready_rows": sum(1 for row in research_packet_rows if row["publish_ready"] == "true"),
            "worksheet_csv": OUT_RESEARCH_PACKET_CSV.as_posix(),
            "worksheet_md": OUT_RESEARCH_PACKET_MD.as_posix(),
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_csv(OUT_RESEARCH_RETURN_INTAKE_CSV, research_return_rows, ACTION_PHOTO_RESEARCH_RETURN_INTAKE_FIELDS)
    write_text(OUT_RESEARCH_RETURN_INTAKE_MD, render_action_photo_research_return_intake(research_return_rows, research_return_issues, generated_at))
    write_json(
        OUT_RESEARCH_RETURN_INTAKE_JSON,
        {
            "version": VERSION,
            "status": "action_photo_research_return_intake_ready" if not research_return_issues else "action_photo_research_return_intake_has_validation_issues",
            "generated_at_utc": generated_at,
            "return_intake_rows": len(research_return_rows),
            "queue_rows_covered": len({row["candidate_queue_id"] for row in research_return_rows}),
            "validation_issue_count": len(research_return_issues),
            "validation_issues": research_return_issues,
            "candidate_queue_ids": sorted({row["candidate_queue_id"] for row in research_return_rows}),
            "rows_with_pasted_return_data": sum(1 for row in research_return_rows if has_research_return_data(row)),
            "download_approved_yes_rows": sum(1 for row in research_return_rows if row["download_approved"] == "yes"),
            "blank_candidate_photo_url_rows": sum(1 for row in research_return_rows if not row["candidate_photo_url"]),
            "blank_evidence_url_rows": sum(1 for row in research_return_rows if not row["evidence_url"]),
            "blank_evidence_summary_rows": sum(1 for row in research_return_rows if not row["evidence_summary"]),
            "blank_identity_anchor_url_rows": sum(1 for row in research_return_rows if not row["identity_anchor_url"]),
            "blank_source_url_rows": sum(1 for row in research_return_rows if not row["source_url"]),
            "blank_entity_id_rows": sum(1 for row in research_return_rows if not row["entity_id"]),
            "blank_rights_class_rows": sum(1 for row in research_return_rows if not row["rights_class"]),
            "blank_identity_confidence_rows": sum(1 for row in research_return_rows if not row["identity_confidence"]),
            "blank_intended_review_only_use_rows": sum(1 for row in research_return_rows if not row["intended_review_only_use"]),
            "blank_notes_rows": sum(1 for row in research_return_rows if not row["notes"]),
            "operator_verify_required_yes_rows": sum(1 for row in research_return_rows if row["operator_verify_required"] == "yes"),
            "manual_reviewer_blank_rows": sum(1 for row in research_return_rows if not row["manual_reviewer"]),
            "manual_review_status_not_reviewed_rows": sum(1 for row in research_return_rows if row["manual_review_status"] == "not_reviewed"),
            "review_only_rows": sum(1 for row in research_return_rows if row["review_only"] == "true"),
            "publish_ready_rows": sum(1 for row in research_return_rows if row["publish_ready"] == "true"),
            "worksheet_csv": OUT_RESEARCH_RETURN_INTAKE_CSV.as_posix(),
            "worksheet_md": OUT_RESEARCH_RETURN_INTAKE_MD.as_posix(),
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_json(
        OUT_JSON,
        {
            "version": VERSION,
            "status": "action_photo_candidate_intake_ready" if not issues and not entity_source_issues and not womens_soccer_issues and not external_research_issues and not candidate_queue_issues and not research_packet_issues and not research_return_issues else "action_photo_candidate_intake_has_validation_issues",
            "generated_at_utc": generated_at,
            "intake_rows": len(rows),
            "download_approved_yes_rows": sum(1 for row in rows if clean(row.get("download_approved")).lower() == "yes"),
            "blank_source_url_rows": sum(1 for row in rows if not clean(row.get("source_url"))),
            "quarantine_root": QUARANTINE_ROOT,
            "required_download_fields": REQUIRED_DOWNLOAD_FIELDS,
            "source_category_count": len(SOURCE_CATEGORIES),
            "rights_class_count": len(RIGHTS_CLASSES),
            "identity_confidence_count": len(IDENTITY_CONFIDENCE),
            "source_map_rows": len(source_rows),
            "sport_entity_source_map_rows": len(entity_source_rows),
            "sport_entity_source_map_validation_issue_count": len(entity_source_issues),
            "womens_soccer_action_photo_starter_rows": len(womens_soccer_rows),
            "womens_soccer_action_photo_starter_validation_issue_count": len(womens_soccer_issues),
            "external_research_source_map_rows": len(external_research_rows),
            "external_research_source_map_validation_issue_count": len(external_research_issues),
            "action_photo_candidate_queue_rows": len(candidate_queue_rows),
            "action_photo_candidate_queue_validation_issue_count": len(candidate_queue_issues),
            "action_photo_candidate_research_packet_rows": len(research_packet_rows),
            "action_photo_candidate_research_packet_validation_issue_count": len(research_packet_issues),
            "action_photo_research_return_intake_rows": len(research_return_rows),
            "action_photo_research_return_intake_validation_issue_count": len(research_return_issues),
            "validation_issue_count": len(issues) + len(entity_source_issues) + len(womens_soccer_issues) + len(external_research_issues) + len(candidate_queue_issues) + len(research_packet_issues) + len(research_return_issues),
            "validation_issues": issues,
            "worksheet_md": OUT_MD.as_posix(),
            "worksheet_csv": OUT_CSV.as_posix(),
            "taxonomy_md": OUT_TAXONOMY_MD.as_posix(),
            "taxonomy_json": OUT_TAXONOMY_JSON.as_posix(),
            "human_review_checklist_md": OUT_CHECKLIST_MD.as_posix(),
            "source_map_template_csv": OUT_SOURCE_MAP_CSV.as_posix(),
            "source_map_template_md": OUT_SOURCE_MAP_MD.as_posix(),
            "sport_entity_source_map_csv": OUT_ENTITY_SOURCE_MAP_CSV.as_posix(),
            "sport_entity_source_map_md": OUT_ENTITY_SOURCE_MAP_MD.as_posix(),
            "sport_entity_source_map_json": OUT_ENTITY_SOURCE_MAP_JSON.as_posix(),
            "womens_soccer_action_photo_starter_csv": OUT_WOMENS_SOCCER_STARTER_CSV.as_posix(),
            "womens_soccer_action_photo_starter_md": OUT_WOMENS_SOCCER_STARTER_MD.as_posix(),
            "womens_soccer_action_photo_starter_json": OUT_WOMENS_SOCCER_STARTER_JSON.as_posix(),
            "external_research_source_map_csv": OUT_EXTERNAL_RESEARCH_SOURCE_MAP_CSV.as_posix(),
            "external_research_source_map_md": OUT_EXTERNAL_RESEARCH_SOURCE_MAP_MD.as_posix(),
            "external_research_source_map_json": OUT_EXTERNAL_RESEARCH_SOURCE_MAP_JSON.as_posix(),
            "action_photo_candidate_queue_csv": OUT_CANDIDATE_QUEUE_CSV.as_posix(),
            "action_photo_candidate_queue_md": OUT_CANDIDATE_QUEUE_MD.as_posix(),
            "action_photo_candidate_queue_json": OUT_CANDIDATE_QUEUE_JSON.as_posix(),
            "action_photo_candidate_research_packet_csv": OUT_RESEARCH_PACKET_CSV.as_posix(),
            "action_photo_candidate_research_packet_md": OUT_RESEARCH_PACKET_MD.as_posix(),
            "action_photo_candidate_research_packet_json": OUT_RESEARCH_PACKET_JSON.as_posix(),
            "action_photo_research_return_intake_csv": OUT_RESEARCH_RETURN_INTAKE_CSV.as_posix(),
            "action_photo_research_return_intake_md": OUT_RESEARCH_RETURN_INTAKE_MD.as_posix(),
            "action_photo_research_return_intake_json": OUT_RESEARCH_RETURN_INTAKE_JSON.as_posix(),
            "review_only": True,
            "approval_state_change": False,
            "candidate_state_change": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    print(json.dumps({"version": VERSION, "status": "ok", "intake_rows": len(rows), "sport_entity_source_map_rows": len(entity_source_rows), "womens_soccer_action_photo_starter_rows": len(womens_soccer_rows), "external_research_source_map_rows": len(external_research_rows), "action_photo_candidate_queue_rows": len(candidate_queue_rows), "action_photo_candidate_research_packet_rows": len(research_packet_rows), "action_photo_research_return_intake_rows": len(research_return_rows), "validation_issue_count": len(issues) + len(entity_source_issues) + len(womens_soccer_issues) + len(external_research_issues) + len(candidate_queue_issues) + len(research_packet_issues) + len(research_return_issues), "csv": OUT_CSV.as_posix()}, indent=2))
    return 1 if issues or entity_source_issues or womens_soccer_issues or external_research_issues or candidate_queue_issues or research_packet_issues or research_return_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
