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


def main() -> int:
    generated_at = TEMPLATE_CREATED_AT_UTC
    rows = [normalize_row(row) for row in template_rows(generated_at)]
    issues = validate_rows(rows)
    source_rows = source_map_rows()
    entity_source_rows = sport_entity_source_map_rows()
    entity_source_issues = validate_entity_source_map_rows(entity_source_rows)
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
    write_json(
        OUT_JSON,
        {
            "version": VERSION,
            "status": "action_photo_candidate_intake_ready" if not issues and not entity_source_issues else "action_photo_candidate_intake_has_validation_issues",
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
            "validation_issue_count": len(issues) + len(entity_source_issues),
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
    print(json.dumps({"version": VERSION, "status": "ok", "intake_rows": len(rows), "sport_entity_source_map_rows": len(entity_source_rows), "validation_issue_count": len(issues) + len(entity_source_issues), "csv": OUT_CSV.as_posix()}, indent=2))
    return 1 if issues or entity_source_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
