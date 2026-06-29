from __future__ import annotations

import csv
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from hsd_run_io import input_candidates, input_path, output_path, write_csv, write_json, write_text

VERSION = "hsd-operator-command-center-v3.87.0-premium-route-limit-cue"
OUT_HTML = output_path("operator_command_center.html")
OUT_MD = output_path("operator_command_center.md")
OUT_JSON = output_path("operator_command_center.json")
OUT_NEXT_ACTION_SYNTHESIS_MD = output_path("operator_next_action_synthesis.md")
OUT_NEXT_ACTION_SYNTHESIS_CSV = output_path("operator_next_action_synthesis.csv")
OUT_NEXT_ACTION_SYNTHESIS_JSON = output_path("operator_next_action_synthesis.json")
OUT_RENDER_PREP_MD = output_path("render_prep_packets.md")
OUT_RENDER_PREP_CSV = output_path("render_prep_packets.csv")
OUT_RENDER_PREP_JSON = output_path("render_prep_packets.json")
OUT_RENDER_HANDOFF_DIR = output_path("render_handoff_top_packet")
OUT_RENDER_HANDOFF_README = OUT_RENDER_HANDOFF_DIR / "README.md"
OUT_RENDER_HANDOFF_COPY = OUT_RENDER_HANDOFF_DIR / "copy_sheet.md"
OUT_RENDER_HANDOFF_COPY_CSV = OUT_RENDER_HANDOFF_DIR / "copy_sheet.csv"
OUT_RENDER_HANDOFF_ASSETS = OUT_RENDER_HANDOFF_DIR / "asset_checklist.md"
OUT_RENDER_HANDOFF_ASSETS_CSV = OUT_RENDER_HANDOFF_DIR / "asset_checklist.csv"
OUT_RENDER_HANDOFF_ACTIVE_ASSET_QUEUE = OUT_RENDER_HANDOFF_DIR / "active_asset_review_queue.md"
OUT_RENDER_HANDOFF_ACTIVE_ASSET_QUEUE_CSV = OUT_RENDER_HANDOFF_DIR / "active_asset_review_queue.csv"
OUT_RENDER_HANDOFF_MANUAL_ASSET_SOURCE_BOARD = OUT_RENDER_HANDOFF_DIR / "manual_asset_source_board.md"
OUT_RENDER_HANDOFF_MANUAL_ASSET_SOURCE_BOARD_CSV = OUT_RENDER_HANDOFF_DIR / "manual_asset_source_board.csv"
OUT_RENDER_HANDOFF_LOGO_VERIFICATION_INTAKE = OUT_RENDER_HANDOFF_DIR / "manual_logo_verification_intake.md"
OUT_RENDER_HANDOFF_LOGO_VERIFICATION_INTAKE_CSV = OUT_RENDER_HANDOFF_DIR / "manual_logo_verification_intake.csv"
OUT_RENDER_HANDOFF_LEAGUE_MARK_INTAKE = OUT_RENDER_HANDOFF_DIR / "manual_league_mark_context_intake.md"
OUT_RENDER_HANDOFF_LEAGUE_MARK_INTAKE_CSV = OUT_RENDER_HANDOFF_DIR / "manual_league_mark_context_intake.csv"
OUT_RENDER_HANDOFF_SOURCE_PROOF = OUT_RENDER_HANDOFF_DIR / "source_proof.md"
OUT_RENDER_HANDOFF_PROMPT = OUT_RENDER_HANDOFF_DIR / "manual_renderer_prompt.md"
OUT_RENDER_HANDOFF_MANIFEST = OUT_RENDER_HANDOFF_DIR / "handoff_manifest.json"
VOLATILE_RENDER_ARTIFACTS = {
    "manual_review_renderer_report.md",
    "manual_review_renderer_manifest.json",
    "render_visual_delta_report.md",
    "render_visual_delta.csv",
    "render_visual_delta_manifest.json",
    "render_visual_revision_plan.md",
    "render_visual_revision_plan.csv",
    "render_visual_revision_plan.json",
    "render_next_level_editorial_qa.md",
    "render_next_level_editorial_qa.csv",
    "render_next_level_editorial_qa.json",
    "manual_visual_qa_report.md",
    "manual_visual_qa_manifest.json",
    "manual_visual_qa_checklist.csv",
}

RENDER_PREP_FIELDS = [
    "packet_id",
    "packet_status",
    "render_rank",
    "render_readiness_score",
    "render_readiness_band",
    "title",
    "recommended_path",
    "template_fit",
    "selected_template_id",
    "template_family",
    "reference_pack_id",
    "template_shape",
    "renderer_family",
    "visual_mode",
    "hero_asset_required",
    "focal_entity_type",
    "score_lock_variant",
    "proof_strip_variant",
    "copy_unlock_state",
    "background_family",
    "template_fit_reason",
    "copy_headline",
    "copy_dek",
    "copy_context",
    "copy_suggested_title",
    "copy_suggested_dek",
    "copy_fit_cue",
    "copy_polish_note",
    "top_performers",
    "stat_module_status",
    "stat_source_confidence",
    "stat_source_label",
    "stat_review_cue",
    "source_artifact",
    "source_cue",
    "source_detail",
    "asset_requirement",
    "active_logo_readiness_status",
    "active_logo_review_cues",
    "logo_review_artifact",
    "active_athlete_identity_status",
    "active_athlete_identity_cues",
    "athlete_identity_artifact",
    "active_asset_stop_go",
    "active_athlete_identity_closure_cues",
    "athlete_identity_closure_artifact",
    "athlete_identity_backfill_artifact",
    "renderer_fallback_cue",
    "asset_cue",
    "format_cue",
    "manual_path",
    "manual_renderer_steps",
    "approval_gate",
    "auto_render_status",
    "publish_policy",
    "paid_api_policy",
    "blockers",
]

NEXT_ACTION_SYNTHESIS_FIELDS = [
    "rank",
    "lane",
    "manual_step",
    "primary_artifact",
    "primary_resolved_path",
    "companion_artifact",
    "companion_resolved_path",
    "operator_return_fields",
    "lane_detail",
    "guardrail_note",
    "artifact_status",
    "run_command",
]

ACTIVE_ASSET_REVIEW_QUEUE_FIELDS = [
    "review_queue_id",
    "packet_id",
    "asset_domain",
    "entity_type",
    "entity_id",
    "entity_name",
    "team_id",
    "review_source",
    "review_status",
    "issue_type",
    "registered_path",
    "source_target_path",
    "asset_path",
    "source_check_url",
    "provider_player_id",
    "approved_marker_path",
    "decision_lane",
    "default_operator_decision",
    "asset_readiness",
    "source_confidence",
    "identity_confidence",
    "manual_approval_status",
    "renderer_fallback_cue",
    "selected_template_blocking_status",
    "selected_template_blocking_reason",
    "evidence_gap_status",
    "local_asset_state",
    "official_source_candidate",
    "current_registry_source",
    "source_policy_status",
    "cannot_clear_automatically_because",
    "blocker_summary",
    "allowed_decisions",
    "primary_action",
    "evidence",
    "manual_review_packet",
    "operator_copy_target",
    "identity_closure_cues",
    "identity_closure_artifact",
    "identity_backfill_artifact",
    "review_only",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "review_only_policy",
]

MANUAL_ASSET_SOURCE_BOARD_FIELDS = [
    "source_board_id",
    "packet_id",
    "priority",
    "asset_domain",
    "entity_type",
    "entity_id",
    "entity_name",
    "team_id",
    "source_board_lane",
    "required_asset",
    "official_source_candidate",
    "free_source_candidate",
    "manual_search_query",
    "source_hint_url",
    "current_local_asset",
    "registry_source_target",
    "current_registry_source",
    "source_policy_status",
    "evidence_gap_status",
    "local_asset_state",
    "cannot_clear_automatically_because",
    "source_confidence",
    "identity_confidence",
    "manual_approval_status",
    "recommended_operator_action",
    "manual_review_packet",
    "operator_copy_target",
    "allowed_decisions",
    "legacy_reference_model",
    "review_only",
    "manual_approval_required",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
]

MANUAL_LOGO_VERIFICATION_INTAKE_FIELDS = [
    "intake_bridge_id",
    "packet_id",
    "priority",
    "asset_domain",
    "entity_id",
    "entity_name",
    "selected_template_blocking_status",
    "local_logo_path",
    "official_source_candidate",
    "current_legacy_registry_source",
    "current_unapproved_status",
    "source_policy_status",
    "evidence_gap_status",
    "manual_intake_files",
    "manual_intake_files_detail",
    "manual_review_packet",
    "operator_copy_target",
    "required_manual_checks",
    "allowed_manual_outcomes",
    "cannot_clear_automatically_because",
    "review_only",
    "approval_state_change",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "publishing",
]

MANUAL_LEAGUE_MARK_CONTEXT_INTAKE_FIELDS = [
    "league_mark_intake_id",
    "packet_id",
    "priority",
    "asset_domain",
    "entity_id",
    "entity_name",
    "selected_template_blocking_status",
    "selected_template_blocking_reason",
    "local_league_mark_path",
    "official_source_candidate",
    "current_registry_source",
    "current_approval_status",
    "source_policy_status",
    "evidence_gap_status",
    "manual_intake_files",
    "manual_intake_files_detail",
    "manual_review_packet",
    "operator_copy_target",
    "required_manual_checks",
    "allowed_manual_outcomes",
    "template_requirement_rule",
    "cannot_clear_automatically_because",
    "review_only",
    "approval_state_change",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "asset_downloads",
    "publishing",
]

COMMAND_CENTER_GENERATED_ARTIFACTS = {
    "operator_next_action_synthesis.md",
    "operator_next_action_synthesis.csv",
    "operator_next_action_synthesis.json",
    "render_handoff_top_packet/active_asset_review_queue.md",
    "render_handoff_top_packet/active_asset_review_queue.csv",
    "render_handoff_top_packet/manual_asset_source_board.md",
    "render_handoff_top_packet/manual_asset_source_board.csv",
    "render_handoff_top_packet/manual_logo_verification_intake.md",
    "render_handoff_top_packet/manual_logo_verification_intake.csv",
    "render_handoff_top_packet/manual_league_mark_context_intake.md",
    "render_handoff_top_packet/manual_league_mark_context_intake.csv",
}

MIRRORED_REVIEW_ARTIFACTS = [
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.png",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.csv",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.json",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.csv",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_candidates.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.json",
    "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md",
    "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv",
    "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.md",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.csv",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.json",
    "data/asset_registry/womens_soccer/external_research/nwsl_correction_enrichment_report.csv",
    "data/asset_registry/womens_soccer/external_research/europe_official_source_map.csv",
    "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.md",
    "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.csv",
    "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.json",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json",
    "data/asset_registry/womens_soccer/athlete_photo_contact_sheets",
    "data/asset_registry/womens_soccer/nwsl/players.csv",
    "data/asset_registry/womens_soccer/nwsl/roster_candidate_fetch_report.md",
    "data/asset_registry/womens_soccer/nwsl/roster_candidate_fetch_report.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_manifest_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_taxonomy.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_taxonomy.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_human_review_checklist.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_map_template.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_map_template.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_source_map.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_source_map.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_source_map.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.md",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.csv",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.json",
    "data/asset_registry/action_photo_candidates/review_only_womens_soccer_action_photo_starter_intake.md",
    "data/asset_registry/action_photo_candidates/review_only_womens_soccer_action_photo_starter_intake.csv",
    "data/asset_registry/action_photo_candidates/review_only_womens_soccer_action_photo_starter_intake.json",
    "action_photo_external_research_handoff_draft_copy.md",
    "action_photo_external_research_handoff_draft_copy.txt",
    "action_photo_external_research_handoff_draft_copy.json",
    "data/asset_registry/hockey_softball_asset_foundation_report.md",
    "data/asset_registry/hockey_softball_asset_foundation_report.json",
    "data/asset_registry/hockey_softball_foundation_coverage_index.md",
    "data/asset_registry/hockey_softball_foundation_coverage_index.csv",
    "data/asset_registry/hockey_softball_foundation_coverage_index.json",
    "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md",
    "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.png",
    "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv",
    "data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv",
    "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.json",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_manifest.json",
    "data/asset_registry/womens_hockey/athlete_photo_contact_sheets",
    "data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md",
    "data/asset_registry/softball/softball_logo_contact_sheet.md",
    "data/asset_registry/softball/softball_logo_contact_sheet.png",
    "data/asset_registry/softball/softball_logo_contact_sheet.csv",
    "data/asset_registry/softball/softball_logo_review_intake.csv",
    "data/asset_registry/softball/softball_logo_contact_sheet.json",
    "data/asset_registry/softball/softball_athlete_photo_contact_sheet_index.md",
    "data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv",
    "data/asset_registry/softball/softball_athlete_photo_review_intake.csv",
    "data/asset_registry/softball/softball_athlete_photo_contact_sheet_manifest.json",
    "data/asset_registry/softball/athlete_photo_contact_sheets",
    "data/asset_registry/softball/softball_review_walkthrough.md",
    "data/asset_registry/hockey_softball_source_review_helper_report.md",
    "data/asset_registry/hockey_softball_source_review_helper_report.json",
    "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md",
    "data/asset_registry/hockey_softball_asset_workflow_readiness_report.json",
    "data/asset_registry/hockey_softball_asset_review_action_queue.md",
    "data/asset_registry/hockey_softball_asset_review_action_queue.csv",
    "data/asset_registry/hockey_softball_asset_review_action_queue.json",
    "data/asset_registry/hockey_softball_batch_source_review_helper.md",
    "data/asset_registry/hockey_softball_batch_source_review_helper.csv",
    "data/asset_registry/hockey_softball_batch_source_review_helper.json",
    "data/asset_registry/hockey_softball_next_decision_worksheet.md",
    "data/asset_registry/hockey_softball_next_decision_worksheet.csv",
    "data/asset_registry/hockey_softball_next_decision_worksheet.json",
    "data/asset_registry/hockey_softball_source_priority_worksheet.md",
    "data/asset_registry/hockey_softball_source_priority_worksheet.csv",
    "data/asset_registry/hockey_softball_source_priority_worksheet.json",
    "data/asset_registry/hockey_softball_source_verification_checklist.md",
    "data/asset_registry/hockey_softball_source_verification_checklist.csv",
    "data/asset_registry/hockey_softball_source_verification_checklist.json",
    "data/asset_registry/hockey_softball_intake_readiness_summary.md",
    "data/asset_registry/hockey_softball_intake_readiness_summary.csv",
    "data/asset_registry/hockey_softball_intake_readiness_summary.json",
    "data/asset_registry/hockey_softball_source_map_board.md",
    "data/asset_registry/hockey_softball_source_map_board.csv",
    "data/asset_registry/hockey_softball_source_map_board.json",
    "data/asset_registry/hockey_softball_action_photo_research_handoff.md",
    "data/asset_registry/hockey_softball_action_photo_research_handoff.csv",
    "data/asset_registry/hockey_softball_action_photo_research_handoff.json",
    "data/asset_registry/hockey_softball_source_research_return_intake.md",
    "data/asset_registry/hockey_softball_source_research_return_intake.csv",
    "data/asset_registry/hockey_softball_source_research_return_intake.json",
    "data/asset_registry/hockey_softball_asset_review_triage.md",
    "data/asset_registry/hockey_softball_asset_review_triage.csv",
    "data/asset_registry/hockey_softball_asset_review_triage.json",
    "data/asset_registry/hockey_softball_asset_review_readiness_board.md",
    "data/asset_registry/hockey_softball_asset_review_readiness_board.csv",
    "data/asset_registry/hockey_softball_asset_review_readiness_board.json",
    "data/asset_registry/hockey_softball_manual_verification_focus.md",
    "data/asset_registry/hockey_softball_manual_verification_focus.csv",
    "data/asset_registry/hockey_softball_manual_verification_focus.json",
    "data/asset_registry/hockey_softball_asset_next_action_cards.md",
    "data/asset_registry/hockey_softball_asset_next_action_cards.csv",
    "data/asset_registry/hockey_softball_asset_next_action_cards.json",
    "data/asset_registry/hockey_softball_quarantine_download_intake.md",
    "data/asset_registry/hockey_softball_quarantine_download_intake.csv",
    "data/asset_registry/hockey_softball_quarantine_download_intake.json",
    "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md",
    "data/asset_registry/softball/softball_asset_workflow_board.md",
]

ARTIFACTS = [
    ("Decision", "Operator status", "operator_status.md"),
    ("Decision", "Workflow lane status", "workflow_lane_status_dashboard.md"),
    ("Decision", "Workflow lane status data", "workflow_lane_status_dashboard.csv"),
    ("Decision", "Workflow lane status manifest", "workflow_lane_status_dashboard.json"),
    ("Decision", "Workflow lane nudge synthesis", "workflow_lane_nudge_synthesis.md"),
    ("Decision", "Workflow lane nudge synthesis data", "workflow_lane_nudge_synthesis.csv"),
    ("Decision", "Workflow lane nudge synthesis manifest", "workflow_lane_nudge_synthesis.json"),
    ("Decision", "Conductor workspace audit", "conductor_workspace_audit.md"),
    ("Decision", "Conductor workspace audit data", "conductor_workspace_audit.csv"),
    ("Decision", "Conductor workspace audit manifest", "conductor_workspace_audit.json"),
    ("Decision", "Release-readiness guardrail rollup", "release_readiness_guardrail_rollup.md"),
    ("Decision", "Release-readiness guardrail rollup data", "release_readiness_guardrail_rollup.csv"),
    ("Decision", "Release-readiness guardrail rollup manifest", "release_readiness_guardrail_rollup.json"),
    ("Decision", "Publish guard", "publish_guard_report.md"),
    ("Decision", "BeBe daily ops plan", "bebe_daily_ops_plan.md"),
    ("Decision", "BeBe posting schedule", "bebe_posting_schedule_today.md"),
    ("Decision", "Operator next-action synthesis", "operator_next_action_synthesis.md"),
    ("Decision", "Operator next-action synthesis data", "operator_next_action_synthesis.csv"),
    ("Decision", "Operator next-action synthesis manifest", "operator_next_action_synthesis.json"),
    ("Decision", "Render prep packets", "render_prep_packets.md"),
    ("Decision", "Render prep packet data", "render_prep_packets.csv"),
    ("Decision", "Render prep packet manifest", "render_prep_packets.json"),
    ("Decision", "Top render handoff", "render_handoff_top_packet/README.md"),
    ("Decision", "Top render copy sheet", "render_handoff_top_packet/copy_sheet.md"),
    ("Decision", "Top render asset checklist", "render_handoff_top_packet/asset_checklist.md"),
    ("Decision", "Top render active asset review queue", "render_handoff_top_packet/active_asset_review_queue.md"),
    ("Decision", "Top render active asset review queue data", "render_handoff_top_packet/active_asset_review_queue.csv"),
    ("Decision", "Top render manual asset source board", "render_handoff_top_packet/manual_asset_source_board.md"),
    ("Decision", "Top render manual asset source board data", "render_handoff_top_packet/manual_asset_source_board.csv"),
    ("Decision", "Top render manual logo verification intake", "render_handoff_top_packet/manual_logo_verification_intake.md"),
    ("Decision", "Top render manual logo verification intake data", "render_handoff_top_packet/manual_logo_verification_intake.csv"),
    ("Decision", "Top render manual league-mark context intake", "render_handoff_top_packet/manual_league_mark_context_intake.md"),
    ("Decision", "Top render manual league-mark context intake data", "render_handoff_top_packet/manual_league_mark_context_intake.csv"),
    ("Decision", "Top render source proof", "render_handoff_top_packet/source_proof.md"),
    ("Decision", "Top render manual prompt", "render_handoff_top_packet/manual_renderer_prompt.md"),
    ("Decision", "Top render draft preview", "render_handoff_top_packet/draft_preview.png"),
    ("Decision", "Top render IG feed draft", "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png"),
    ("Decision", "Top render story draft", "render_handoff_top_packet/review_drafts/draft_preview_story.png"),
    ("Decision", "Top render square draft", "render_handoff_top_packet/review_drafts/draft_preview_square.png"),
    ("Decision", "Top render handoff manifest", "render_handoff_top_packet/handoff_manifest.json"),
    ("Decision", "Manual review renderer report", "manual_review_renderer_report.md"),
    ("Decision", "Manual review renderer manifest", "manual_review_renderer_manifest.json"),
    ("Decision", "Render visual delta report", "render_visual_delta_report.md"),
    ("Decision", "Render visual delta data", "render_visual_delta.csv"),
    ("Decision", "Render visual delta manifest", "render_visual_delta_manifest.json"),
    ("Decision", "Render visual revision plan", "render_visual_revision_plan.md"),
    ("Decision", "Render visual revision data", "render_visual_revision_plan.csv"),
    ("Decision", "Render visual revision manifest", "render_visual_revision_plan.json"),
    ("Decision", "Render next-level editorial QA", "render_next_level_editorial_qa.md"),
    ("Decision", "Render next-level editorial QA data", "render_next_level_editorial_qa.csv"),
    ("Decision", "Render next-level editorial QA manifest", "render_next_level_editorial_qa.json"),
    ("Decision", "Manual visual QA report", "manual_visual_qa_report.md"),
    ("Decision", "Manual visual QA manifest", "manual_visual_qa_manifest.json"),
    ("Decision", "Manual visual QA checklist", "manual_visual_qa_checklist.csv"),
    ("Decision", "Manual visual QA approval intake", "manual_visual_qa_approval_intake.md"),
    ("Decision", "Manual visual QA approval intake data", "manual_visual_qa_approval_intake.csv"),
    ("Decision", "Manual visual QA approval intake manifest", "manual_visual_qa_approval_intake.json"),
    ("Decision", "Manual visual QA operator decision draft", "manual_visual_qa_operator_decision_draft.md"),
    ("Decision", "Manual visual QA operator decision draft data", "manual_visual_qa_operator_decision_draft.csv"),
    ("Decision", "Manual visual QA operator decision draft manifest", "manual_visual_qa_operator_decision_draft.json"),
    ("Decision", "Manual visual QA operator decision template", "manual_visual_qa_operator_decision_template.md"),
    ("Decision", "Manual visual QA operator decision template data", "manual_visual_qa_operator_decision_template.csv"),
    ("Decision", "Manual visual QA operator decision template manifest", "manual_visual_qa_operator_decision_template.json"),
    ("Decision", "Manual visual QA operator decision intake", "manual_visual_qa_operator_decision_intake.md"),
    ("Decision", "Manual visual QA operator decision intake data", "manual_visual_qa_operator_decision_intake.csv"),
    ("Decision", "Manual visual QA operator decision intake manifest", "manual_visual_qa_operator_decision_intake.json"),
    ("Decision", "Manual post-approval render staging", "manual_post_approval_render_staging.md"),
    ("Decision", "Manual post-approval render staging data", "manual_post_approval_render_staging.csv"),
    ("Decision", "Manual post-approval render staging manifest", "manual_post_approval_render_staging.json"),
    ("Decision", "Manual operator decision walkthrough", "manual_visual_qa_operator_decision_walkthrough.md"),
    ("Decision", "Manual operator decision walkthrough data", "manual_visual_qa_operator_decision_walkthrough.csv"),
    ("Decision", "Manual operator decision walkthrough manifest", "manual_visual_qa_operator_decision_walkthrough.json"),
    ("Decision", "Manual operator decision inbox starter", "manual_visual_qa_operator_decision_inbox_starter.md"),
    ("Decision", "Manual operator decision inbox starter data", "manual_visual_qa_operator_decision_inbox_starter.csv"),
    ("Decision", "Manual operator decision inbox starter manifest", "manual_visual_qa_operator_decision_inbox_starter.json"),
    ("Sources", "Source registry audit", "source_registry_audit.md"),
    ("Sources", "Source registry audit data", "source_registry_audit.json"),
    ("Sources", "Source registry audit table", "source_registry_audit.csv"),
    ("Sources", "Source coverage map", "source_coverage_map.csv"),
    ("Sources", "Source registry intake guide", "source_registry_intake_template.md"),
    ("Sources", "Source registry intake template", "source_registry_intake_template.csv"),
    ("Sources", "Source proposal review", "source_registry_proposal_review.md"),
    ("Sources", "Source proposal review data", "source_registry_proposal_review.csv"),
    ("Sources", "Source proposal draft", "source_registry_proposal_draft.md"),
    ("Sources", "Source proposal draft data", "source_registry_proposal_draft.csv"),
    ("Sources", "Source proposal promotion checklist", "source_registry_proposal_promotion_checklist.md"),
    ("Sources", "Source proposal promotion checklist data", "source_registry_proposal_promotion_checklist.csv"),
    ("Sources", "Source registry update worksheet", "source_registry_update_worksheet.md"),
    ("Sources", "Source registry update worksheet data", "source_registry_update_worksheet.csv"),
    ("Sources", "Source registry diff review", "source_registry_diff_review.md"),
    ("Sources", "Source registry diff review data", "source_registry_diff_review.csv"),
    ("Sources", "Source registry same-domain resolution", "source_registry_same_domain_resolution.md"),
    ("Sources", "Source registry same-domain resolution data", "source_registry_same_domain_resolution.csv"),
    ("Sources", "Source verification log", "source_registry_verification_log.md"),
    ("Sources", "Source verification log data", "source_registry_verification_log.csv"),
    ("Sources", "Source registry approval packet", "source_registry_approval_packet.md"),
    ("Sources", "Source registry approval packet data", "source_registry_approval_packet.csv"),
    ("Sources", "Source registry patch preview", "source_registry_patch_preview.md"),
    ("Sources", "Source registry patch preview data", "source_registry_patch_preview.csv"),
    ("Sources", "Source registry post-edit validation", "source_registry_post_edit_validation.md"),
    ("Sources", "Source registry post-edit validation data", "source_registry_post_edit_validation.csv"),
    ("Sources", "Trusted registry operator playbook", "trusted_registry_operator_playbook.md"),
    ("Sources", "Guided source pack readiness", "source_proposal_pack_readiness.md"),
    ("Sources", "Guided source pack readiness data", "source_proposal_pack_readiness.csv"),
    ("Sources", "Guided source proposal packs", "source_proposal_packs.md"),
    ("Sources", "Guided source proposal pack data", "source_proposal_packs.csv"),
    ("Sources", "WNBA source proposal pack", "wnba_source_proposal_pack.md"),
    ("Sources", "WNBA source proposal pack data", "wnba_source_proposal_pack.csv"),
    ("Sources", "NWSL source proposal pack", "nwsl_source_proposal_pack.md"),
    ("Sources", "NWSL source proposal pack data", "nwsl_source_proposal_pack.csv"),
    ("Sources", "LPGA source proposal pack", "lpga_source_proposal_pack.md"),
    ("Sources", "LPGA source proposal pack data", "lpga_source_proposal_pack.csv"),
    ("Sources", "PWHL source proposal pack", "pwhl_source_proposal_pack.md"),
    ("Sources", "PWHL source proposal pack data", "pwhl_source_proposal_pack.csv"),
    ("Sources", "Manual story intake report", "manual_story_inbox_report.md"),
    ("Sources", "Manual story intake data", "story_candidates_manual.csv"),
    ("Sources", "Discovery intake report", "discovery_sources_report.md"),
    ("Sources", "Discovery intake data", "story_candidates_discovery.csv"),
    ("Sources", "Morning source discovery board", "morning_source_discovery_board.md"),
    ("Sources", "Morning source discovery data", "morning_source_discovery_board.csv"),
    ("Sources", "Morning source discovery manifest", "morning_source_discovery_board.json"),
    ("Sources", "Lead promotion recommendations", "morning_lead_promotion_recommendations.md"),
    ("Sources", "Lead promotion recommendation data", "morning_lead_promotion_recommendations.csv"),
    ("Sources", "Lead promotion recommendation manifest", "morning_lead_promotion_recommendations.json"),
    ("Results", "Results manifest", "results_desk_v5_manifest.json"),
    ("Results", "Results report", "results_desk_v5_report.md"),
    ("Results", "Game intelligence board", "game_intelligence_board_v1.md"),
    ("Results", "Game intelligence board data", "game_intelligence_board_v1.csv"),
    ("Results", "Game intelligence board manifest", "game_intelligence_board_v1.json"),
    ("Results", "Stats evidence gap board", "stats_evidence_gap_board_v1.md"),
    ("Results", "Stats evidence gap data", "stats_evidence_gap_board_v1.csv"),
    ("Results", "Stats evidence gap manifest", "stats_evidence_gap_board_v1.json"),
    ("Results", "Stats confirmation intake", "stats_confirmation_intake_v1.csv"),
    ("Results", "Game fact confirmation status", "game_fact_confirmation_status_v1.md"),
    ("Results", "Game fact confirmation status data", "game_fact_confirmation_status_v1.csv"),
    ("Results", "Game fact confirmation status manifest", "game_fact_confirmation_status_v1.json"),
    ("Results", "Game source confirmation next actions", "game_source_confirmation_next_action_v1.md"),
    ("Results", "Game source confirmation next action data", "game_source_confirmation_next_action_v1.csv"),
    ("Results", "Game source confirmation next action manifest", "game_source_confirmation_next_action_v1.json"),
    ("Results", "Game source research worksheet", "game_source_research_worksheet_v1.md"),
    ("Results", "Game source research worksheet data", "game_source_research_worksheet_v1.csv"),
    ("Results", "Game source research worksheet manifest", "game_source_research_worksheet_v1.json"),
    ("Results", "Game source confirmation return summary", "game_source_confirmation_return_summary_v1.md"),
    ("Results", "Game source confirmation return summary data", "game_source_confirmation_return_summary_v1.csv"),
    ("Results", "Game source confirmation return summary manifest", "game_source_confirmation_return_summary_v1.json"),
    ("Results", "Final score stat proof", "final_score_stat_proof_v1.md"),
    ("Results", "Final score stat proof data", "final_score_stat_proof_v1.csv"),
    ("Results", "Final score stat proof manifest", "final_score_stat_proof_v1.json"),
    ("Results", "Final score stat proof confirmation intake", "final_score_stat_proof_confirmation_intake_v1.csv"),
    ("Results", "Final score stat proof review walkthrough", "final_score_stat_proof_review_walkthrough_v1.md"),
    ("Results", "Final score stat proof review order data", "final_score_stat_proof_review_order_v1.csv"),
    ("Results", "Athlete render candidate board", "athlete_render_candidate_board_v1.md"),
    ("Results", "Athlete render candidate data", "athlete_render_candidate_board_v1.csv"),
    ("Results", "Athlete render candidate manifest", "athlete_render_candidate_board_v1.json"),
    ("Results", "Story proof card", "story_proof_card_v1.md"),
    ("Results", "Story proof card data", "story_proof_card_v1.csv"),
    ("Results", "Story proof card manifest", "story_proof_card_v1.json"),
    ("Results", "Source accuracy", "source_accuracy_v5.md"),
    ("Results", "Missing games alert", "missing_games_alert_v5.md"),
    ("Results", "Top women's results", "top_womens_results.csv"),
    ("Results", "Final results", "today_final_results.csv"),
    ("Results", "Results drill-down dashboard", "results_dashboard/index.html"),
    ("News", "News fact packets", "news_fact_packets.csv"),
    ("News", "News daily plan", "news_daily_plan.md"),
    ("News", "Breaking public signal queue", "breaking_public_signal_queue.md"),
    ("News", "Breaking public signal data", "breaking_public_signal_queue.csv"),
    ("News", "Breaking public signal manifest", "breaking_public_signal_manifest.json"),
    ("News", "Breaking confirmation intake", "breaking_public_signal_confirmation_intake.md"),
    ("News", "Breaking confirmation intake data", "breaking_public_signal_confirmation_intake.csv"),
    ("News", "Breaking public signal clusters", "breaking_public_signal_clusters.md"),
    ("News", "Breaking public signal cluster data", "breaking_public_signal_clusters.csv"),
    ("News", "Breaking public signal next actions", "breaking_public_signal_next_action_v1.md"),
    ("News", "Breaking public signal next action data", "breaking_public_signal_next_action_v1.csv"),
    ("News", "Breaking public signal next action manifest", "breaking_public_signal_next_action_v1.json"),
    ("News", "Breaking public signal return summary", "breaking_public_signal_return_summary_v1.md"),
    ("News", "Breaking public signal return summary data", "breaking_public_signal_return_summary_v1.csv"),
    ("News", "Breaking public signal return summary manifest", "breaking_public_signal_return_summary_v1.json"),
    ("News", "Game source confirmation bridge", "game_source_confirmation_bridge_v1.md"),
    ("News", "Game source confirmation bridge data", "game_source_confirmation_bridge_v1.csv"),
    ("News", "Game source confirmation bridge manifest", "game_source_confirmation_bridge_v1.json"),
    ("News", "News sync hub", "news_sync_hub.md"),
    ("Planning", "Multi-post daily board", "multi_post_daily_board.md"),
    ("Planning", "Post slot status", "post_slot_status.csv"),
    ("Planning", "IG feed queue", "ig_feed_queue.csv"),
    ("Planning", "IG story queue", "ig_story_queue.csv"),
    ("Planning", "Threads queue", "threads_queue.csv"),
    ("Planning", "Caption bank", "caption_bank.md"),
    ("Planning", "First comment hooks", "first_comment_hooks.md"),
    ("Launch", "Launch command center", "launch_command_center.md"),
    ("Launch", "Launch daily runbook", "launch_daily_runbook.md"),
    ("Launch", "Launch graphics brief", "launch_graphics_chat_brief.md"),
    ("Launch", "Launch publish queue", "launch_instagram_publish_queue.csv"),
    ("Launch", "Launch quality gate", "launch_quality_gate.csv"),
    ("Launch", "Launch operator checklist", "launch_daily_operator_checklist.md"),
    ("Launch", "Launch metrics input", "launch_metrics_manual_input.csv"),
    ("Launch", "Launch performance dashboard", "launch_7_day_performance_dashboard.md"),
    ("Launch", "Launch manifest", "launch_manifest.json"),
    ("Launch", "Launch dashboard", "launch_dashboard/index.html"),
    ("Launch", "Launch analytics dashboard", "launch_analytics_dashboard/index.html"),
    ("Studio", "Studio queue", "studio_bundle_queue.csv"),
    ("Studio", "Studio packets", "studio_bundle_packets.md"),
    ("Studio", "Studio drill-down dashboard", "studio_dashboard/index.html"),
    ("Studio", "Preview quality", "preview_bundle_quality.md"),
    ("Studio", "Preview player focus", "preview_player_focus.csv"),
    ("Graphics", "Graphics upload status", "graphics_upload_pack_status.csv"),
    ("Graphics", "Rendered slide QA", "rendered_slide_qa_report.md"),
    ("Graphics", "Final score story queue", "ig_story_results_queue.csv"),
    ("Graphics", "Final score story status", "ig_story_results_upload_pack_status.csv"),
    ("Graphics", "Final score story guard", "final_score_story_guard_report.md"),
    ("Graphics", "Manual workflow handoff", "manual_workflow_handoff.md"),
    ("Graphics", "Manual workflow pack status", "manual_workflow_pack_status.csv"),
    ("Graphics", "Athlete photo onboarding report", "athlete_photo_onboarding/athlete_photo_onboarding_report.md"),
    ("Graphics", "Athlete photo contact sheet index", "athlete_photo_onboarding/athlete_photo_contact_sheet_index.md"),
    ("Graphics", "Athlete photo onboarding metadata", "athlete_photo_onboarding/athlete_photo_onboarding_metadata.csv"),
    ("Graphics", "Athlete photo onboarding decisions", "athlete_photo_onboarding/athlete_photo_onboarding_decision_template.csv"),
    ("Graphics", "Athlete photo onboarding manifest", "athlete_photo_onboarding/athlete_photo_onboarding_manifest.json"),
    ("Graphics", "WNBA athlete identity audit", "data/asset_registry/wnba/athlete_identity_audit.md"),
    ("Graphics", "WNBA athlete identity audit data", "data/asset_registry/wnba/athlete_identity_audit.csv"),
    ("Graphics", "WNBA athlete identity resolution workflow", "data/asset_registry/wnba/athlete_identity_resolution_workflow.md"),
    ("Graphics", "WNBA athlete identity resolution candidates", "data/asset_registry/wnba/athlete_identity_resolution_candidates.csv"),
    ("Graphics", "WNBA athlete identity review packet", "data/asset_registry/wnba/athlete_identity_review_packet.csv"),
    ("Graphics", "WNBA athlete identity resolution template", "data/asset_registry/wnba/athlete_identity_resolution_template.csv"),
    ("Graphics", "WNBA athlete identity resolution manifest", "data/asset_registry/wnba/athlete_identity_resolution_manifest.json"),
    ("Graphics", "WNBA athlete identity closure packet", "data/asset_registry/wnba/athlete_identity_closure_packet.md"),
    ("Graphics", "WNBA athlete identity closure packet data", "data/asset_registry/wnba/athlete_identity_closure_packet.json"),
    ("Graphics", "WNBA athlete identity issue closure template", "data/asset_registry/wnba/athlete_identity_issue_closure_template.csv"),
    ("Graphics", "WNBA athlete provider ID backfill template", "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv"),
    ("Graphics", "WNBA identity local save server", "identity_resolution_local_server.md"),
    ("Graphics", "WNBA identity local save server data", "identity_resolution_local_server.json"),
    ("Graphics", "WNBA identity live writeback verifier", "identity_decision_live_writeback_verification.md"),
    ("Graphics", "WNBA identity live writeback verifier data", "identity_decision_live_writeback_verification.json"),
    ("Graphics", "Asset availability audit", "data/asset_registry/asset_availability_audit.md"),
    ("Graphics", "Asset availability audit data", "data/asset_registry/asset_availability_audit.csv"),
    ("Graphics", "Asset availability audit manifest", "data/asset_registry/asset_availability_audit.json"),
    ("Graphics", "WNBA athlete photo catalog", "data/asset_registry/wnba/athlete_photo_catalog.md"),
    ("Graphics", "WNBA athlete photo catalog data", "data/asset_registry/wnba/athlete_photo_catalog.csv"),
    ("Graphics", "WNBA athlete photo catalog manifest", "data/asset_registry/wnba/athlete_photo_catalog.json"),
    ("Graphics", "WNBA athlete photo contact sheet index", "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_index.md"),
    ("Graphics", "WNBA athlete photo contact sheet data", "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet.csv"),
    ("Graphics", "WNBA athlete photo review intake", "data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv"),
    ("Graphics", "WNBA athlete photo contact sheet manifest", "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_manifest.json"),
    ("Graphics", "WNBA logo review catalog", "data/asset_registry/wnba/logo_review_catalog_report.md"),
    ("Graphics", "WNBA logo review catalog data", "data/asset_registry/wnba/logo_review_catalog.csv"),
    ("Graphics", "WNBA logo review catalog manifest", "data/asset_registry/wnba/logo_review_catalog.json"),
    ("Graphics", "WNBA logo review packets", "data/asset_registry/wnba/logo_review_packets.csv"),
    ("Graphics", "WNBA team logo contact sheet", "data/asset_registry/wnba/wnba_team_logo_contact_sheet.md"),
    ("Graphics", "WNBA team logo contact sheet image", "data/asset_registry/wnba/wnba_team_logo_contact_sheet.png"),
    ("Graphics", "WNBA team logo contact sheet data", "data/asset_registry/wnba/wnba_team_logo_contact_sheet.csv"),
    ("Graphics", "WNBA team logo review intake", "data/asset_registry/wnba/wnba_team_logo_review_intake.csv"),
    ("Graphics", "WNBA team logo contact sheet manifest", "data/asset_registry/wnba/wnba_team_logo_contact_sheet.json"),
    ("Graphics", "Women's soccer logo contact sheet", "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md"),
    ("Graphics", "Women's soccer logo contact sheet image", "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.png"),
    ("Graphics", "Women's soccer logo contact sheet data", "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.csv"),
    ("Graphics", "Women's soccer logo review intake", "data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv"),
    ("Graphics", "Women's soccer logo contact sheet manifest", "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.json"),
    ("Graphics", "Women's soccer logo review walkthrough", "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md"),
    ("Graphics", "Women's soccer logo review walkthrough data", "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.csv"),
    ("Graphics", "Women's soccer logo review walkthrough manifest", "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.json"),
    ("Graphics", "Women's soccer athlete photo contact sheet index", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md"),
    ("Graphics", "Women's soccer athlete photo contact sheet data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv"),
    ("Graphics", "Women's soccer athlete photo review intake", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv"),
    ("Graphics", "Women's soccer athlete photo candidates", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_candidates.csv"),
    ("Graphics", "Women's soccer athlete operator board", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md"),
    ("Graphics", "Women's soccer athlete operator board data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.csv"),
    ("Graphics", "Women's soccer athlete operator board manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.json"),
    ("Graphics", "Women's soccer athlete photo download intake", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.md"),
    ("Graphics", "Women's soccer athlete photo download intake data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv"),
    ("Graphics", "Women's soccer athlete photo download intake manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.json"),
    ("Graphics", "Women's soccer athlete verification queue", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.md"),
    ("Graphics", "Women's soccer athlete verification queue data", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.csv"),
    ("Graphics", "Women's soccer athlete verification queue manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.json"),
    ("Graphics", "Women's soccer athlete verification next actions", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.md"),
    ("Graphics", "Women's soccer athlete verification next actions data", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.csv"),
    ("Graphics", "Women's soccer athlete verification next actions manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.json"),
    ("Graphics", "Women's soccer athlete source priority", "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.md"),
    ("Graphics", "Women's soccer athlete source priority data", "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.csv"),
    ("Graphics", "Women's soccer athlete source priority manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.json"),
    ("Graphics", "Women's soccer athlete review triage", "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.md"),
    ("Graphics", "Women's soccer athlete review triage data", "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.csv"),
    ("Graphics", "Women's soccer athlete review triage manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.json"),
    ("Graphics", "Women's soccer athlete candidate next-action board", "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md"),
    ("Graphics", "Women's soccer athlete candidate next-action board data", "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.csv"),
    ("Graphics", "Women's soccer athlete candidate next-action board manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.json"),
    ("Graphics", "Women's soccer athlete photo review readiness board", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md"),
    ("Graphics", "Women's soccer athlete photo review readiness board data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.csv"),
    ("Graphics", "Women's soccer athlete photo review readiness board manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.json"),
    ("Graphics", "Women's soccer athlete operator focus", "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md"),
    ("Graphics", "Women's soccer athlete operator focus data", "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.csv"),
    ("Graphics", "Women's soccer athlete operator focus manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.json"),
    ("Graphics", "Women's soccer action-photo research next", "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md"),
    ("Graphics", "Women's soccer action-photo research next data", "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv"),
    ("Graphics", "Women's soccer action-photo research next manifest", "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.json"),
    ("Graphics", "Women's soccer athlete expansion closure summary", "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.md"),
    ("Graphics", "Women's soccer athlete expansion closure summary data", "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.csv"),
    ("Graphics", "Women's soccer athlete expansion closure summary manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.json"),
    ("Graphics", "Women's soccer external research intake", "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.md"),
    ("Graphics", "Women's soccer external research intake data", "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.csv"),
    ("Graphics", "Women's soccer external research intake manifest", "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.json"),
    ("Graphics", "Women's soccer NWSL external research source", "data/asset_registry/womens_soccer/external_research/nwsl_correction_enrichment_report.csv"),
    ("Graphics", "Women's soccer Europe external research source", "data/asset_registry/womens_soccer/external_research/europe_official_source_map.csv"),
    ("Graphics", "Women's soccer athlete photo contact sheet manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json"),
    ("Graphics", "Women's soccer NWSL player registry", "data/asset_registry/womens_soccer/nwsl/players.csv"),
    ("Graphics", "Women's soccer NWSL roster candidate fetch report", "data/asset_registry/womens_soccer/nwsl/roster_candidate_fetch_report.md"),
    ("Graphics", "Women's soccer NWSL roster candidate fetch manifest", "data/asset_registry/womens_soccer/nwsl/roster_candidate_fetch_report.json"),
    ("Graphics", "Action-photo candidate intake", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.md"),
    ("Graphics", "Action-photo candidate intake data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.csv"),
    ("Graphics", "Action-photo candidate intake manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.json"),
    ("Graphics", "Action-photo candidate queue", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.md"),
    ("Graphics", "Action-photo candidate queue data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.csv"),
    ("Graphics", "Action-photo candidate queue manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.json"),
    ("Graphics", "Action-photo candidate operator worksheet", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.md"),
    ("Graphics", "Action-photo candidate operator worksheet data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.csv"),
    ("Graphics", "Action-photo candidate operator worksheet manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.json"),
    ("Graphics", "Action-photo research packet", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md"),
    ("Graphics", "Action-photo research packet data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.csv"),
    ("Graphics", "Action-photo research packet manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.json"),
    ("Graphics", "Action-photo research return intake", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.md"),
    ("Graphics", "Action-photo research return intake data", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"),
    ("Graphics", "Action-photo research return intake manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.json"),
    ("Graphics", "Action-photo research return paste worksheet", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.md"),
    ("Graphics", "Action-photo research return paste worksheet data", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.csv"),
    ("Graphics", "Action-photo research return paste worksheet manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.json"),
    ("Graphics", "Action-photo research run bundle", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.md"),
    ("Graphics", "Action-photo research run bundle data", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.csv"),
    ("Graphics", "Action-photo research run bundle manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.json"),
    ("Graphics", "Action-photo external research prompt", "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md"),
    ("Graphics", "Action-photo external research manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_manifest_v1.json"),
    ("Graphics", "Action-photo quarantine preflight", "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md"),
    ("Graphics", "Action-photo quarantine preflight data", "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.csv"),
    ("Graphics", "Action-photo quarantine preflight manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.json"),
    ("Graphics", "Action-photo research return summary board", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.md"),
    ("Graphics", "Action-photo research return summary board data", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.csv"),
    ("Graphics", "Action-photo research return summary board manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.json"),
    ("Graphics", "Action-photo candidate quality/fit board", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md"),
    ("Graphics", "Action-photo candidate quality/fit board data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.csv"),
    ("Graphics", "Action-photo candidate quality/fit board manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.json"),
    ("Graphics", "Action-photo quality/fit operator cue", "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md"),
    ("Graphics", "Action-photo quality/fit operator cue data", "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.csv"),
    ("Graphics", "Action-photo quality/fit operator cue manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.json"),
    ("Graphics", "Action-photo download decision queue", "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.md"),
    ("Graphics", "Action-photo download decision queue data", "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.csv"),
    ("Graphics", "Action-photo download decision queue manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.json"),
    ("Graphics", "WNBA hero action-photo targets", "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.md"),
    ("Graphics", "WNBA hero action-photo targets data", "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.csv"),
    ("Graphics", "WNBA hero action-photo targets manifest", "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.json"),
    ("Graphics", "Action-photo cutout readiness", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.md"),
    ("Graphics", "Action-photo cutout readiness data", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.csv"),
    ("Graphics", "Action-photo cutout readiness manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.json"),
    ("Graphics", "Action-photo candidate taxonomy", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_taxonomy.md"),
    ("Graphics", "Action-photo human review checklist", "data/asset_registry/action_photo_candidates/review_only_action_photo_human_review_checklist.md"),
    ("Graphics", "Action-photo source discovery board", "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.md"),
    ("Graphics", "Action-photo source discovery board data", "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.csv"),
    ("Graphics", "Action-photo source discovery board manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.json"),
    ("Graphics", "Action-photo manual source-hunt board", "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.md"),
    ("Graphics", "Action-photo manual source-hunt board data", "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.csv"),
    ("Graphics", "Action-photo manual source-hunt board manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.json"),
    ("Graphics", "Action-photo sport/entity source-map board", "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.md"),
    ("Graphics", "Action-photo sport/entity source-map board data", "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.csv"),
    ("Graphics", "Action-photo sport/entity source-map board manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.json"),
    ("Graphics", "Action-photo lead return schema", "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.md"),
    ("Graphics", "Action-photo lead return schema data", "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.csv"),
    ("Graphics", "Action-photo lead return schema manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.json"),
    ("Graphics", "Action-photo cutout scoring criteria", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.md"),
    ("Graphics", "Action-photo cutout scoring criteria data", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.csv"),
    ("Graphics", "Action-photo cutout scoring criteria manifest", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.json"),
    ("Graphics", "Action-photo external research bundle latest", "action_photo_external_research_bundle_latest.json"),
    ("Graphics", "Action-photo local handoff draft copy", "action_photo_external_research_handoff_draft_copy.md"),
    ("Graphics", "Action-photo local handoff draft copy text", "action_photo_external_research_handoff_draft_copy.txt"),
    ("Graphics", "Action-photo local handoff draft copy manifest", "action_photo_external_research_handoff_draft_copy.json"),
    ("Graphics", "Hockey/softball asset foundation report", "data/asset_registry/hockey_softball_asset_foundation_report.md"),
    ("Graphics", "Hockey/softball foundation coverage index", "data/asset_registry/hockey_softball_foundation_coverage_index.md"),
    ("Graphics", "Hockey/softball foundation coverage index data", "data/asset_registry/hockey_softball_foundation_coverage_index.csv"),
    ("Graphics", "Hockey/softball foundation coverage index manifest", "data/asset_registry/hockey_softball_foundation_coverage_index.json"),
    ("Graphics", "Women's hockey logo contact sheet", "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md"),
    ("Graphics", "Women's hockey logo review intake", "data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv"),
    ("Graphics", "Women's hockey athlete photo contact sheets", "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md"),
    ("Graphics", "Women's hockey athlete photo review intake", "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"),
    ("Graphics", "Women's hockey review walkthrough", "data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md"),
    ("Graphics", "Softball logo contact sheet", "data/asset_registry/softball/softball_logo_contact_sheet.md"),
    ("Graphics", "Softball logo review intake", "data/asset_registry/softball/softball_logo_review_intake.csv"),
    ("Graphics", "Softball athlete photo contact sheets", "data/asset_registry/softball/softball_athlete_photo_contact_sheet_index.md"),
    ("Graphics", "Softball athlete photo review intake", "data/asset_registry/softball/softball_athlete_photo_review_intake.csv"),
    ("Graphics", "Softball review walkthrough", "data/asset_registry/softball/softball_review_walkthrough.md"),
    ("Graphics", "Hockey/softball source review helper report", "data/asset_registry/hockey_softball_source_review_helper_report.md"),
    ("Graphics", "Hockey/softball asset workflow readiness", "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md"),
    ("Graphics", "Hockey/softball asset review action queue", "data/asset_registry/hockey_softball_asset_review_action_queue.md"),
    ("Graphics", "Hockey/softball asset review action queue data", "data/asset_registry/hockey_softball_asset_review_action_queue.csv"),
    ("Graphics", "Hockey/softball batch source review helper", "data/asset_registry/hockey_softball_batch_source_review_helper.md"),
    ("Graphics", "Hockey/softball batch source review helper data", "data/asset_registry/hockey_softball_batch_source_review_helper.csv"),
    ("Graphics", "Hockey/softball next decision worksheet", "data/asset_registry/hockey_softball_next_decision_worksheet.md"),
    ("Graphics", "Hockey/softball next decision worksheet data", "data/asset_registry/hockey_softball_next_decision_worksheet.csv"),
    ("Graphics", "Hockey/softball next decision worksheet manifest", "data/asset_registry/hockey_softball_next_decision_worksheet.json"),
    ("Graphics", "Hockey/softball source priority worksheet", "data/asset_registry/hockey_softball_source_priority_worksheet.md"),
    ("Graphics", "Hockey/softball source priority worksheet data", "data/asset_registry/hockey_softball_source_priority_worksheet.csv"),
    ("Graphics", "Hockey/softball source priority worksheet manifest", "data/asset_registry/hockey_softball_source_priority_worksheet.json"),
    ("Graphics", "Hockey/softball source verification checklist", "data/asset_registry/hockey_softball_source_verification_checklist.md"),
    ("Graphics", "Hockey/softball source verification checklist data", "data/asset_registry/hockey_softball_source_verification_checklist.csv"),
    ("Graphics", "Hockey/softball source verification checklist manifest", "data/asset_registry/hockey_softball_source_verification_checklist.json"),
    ("Graphics", "Hockey/softball intake readiness summary", "data/asset_registry/hockey_softball_intake_readiness_summary.md"),
    ("Graphics", "Hockey/softball intake readiness summary data", "data/asset_registry/hockey_softball_intake_readiness_summary.csv"),
    ("Graphics", "Hockey/softball intake readiness summary manifest", "data/asset_registry/hockey_softball_intake_readiness_summary.json"),
    ("Graphics", "Hockey/softball source map board", "data/asset_registry/hockey_softball_source_map_board.md"),
    ("Graphics", "Hockey/softball source map board data", "data/asset_registry/hockey_softball_source_map_board.csv"),
    ("Graphics", "Hockey/softball source map board manifest", "data/asset_registry/hockey_softball_source_map_board.json"),
    ("Graphics", "Hockey/softball action-photo research handoff", "data/asset_registry/hockey_softball_action_photo_research_handoff.md"),
    ("Graphics", "Hockey/softball action-photo research handoff data", "data/asset_registry/hockey_softball_action_photo_research_handoff.csv"),
    ("Graphics", "Hockey/softball action-photo research handoff manifest", "data/asset_registry/hockey_softball_action_photo_research_handoff.json"),
    ("Graphics", "Hockey/softball source research return intake", "data/asset_registry/hockey_softball_source_research_return_intake.md"),
    ("Graphics", "Hockey/softball source research return data", "data/asset_registry/hockey_softball_source_research_return_intake.csv"),
    ("Graphics", "Hockey/softball source research return manifest", "data/asset_registry/hockey_softball_source_research_return_intake.json"),
    ("Graphics", "Hockey/softball asset review triage", "data/asset_registry/hockey_softball_asset_review_triage.md"),
    ("Graphics", "Hockey/softball asset review triage data", "data/asset_registry/hockey_softball_asset_review_triage.csv"),
    ("Graphics", "Hockey/softball asset review triage manifest", "data/asset_registry/hockey_softball_asset_review_triage.json"),
    ("Graphics", "Hockey/softball asset review readiness board", "data/asset_registry/hockey_softball_asset_review_readiness_board.md"),
    ("Graphics", "Hockey/softball asset review readiness data", "data/asset_registry/hockey_softball_asset_review_readiness_board.csv"),
    ("Graphics", "Hockey/softball asset review readiness manifest", "data/asset_registry/hockey_softball_asset_review_readiness_board.json"),
    ("Graphics", "Hockey/softball manual verification focus", "data/asset_registry/hockey_softball_manual_verification_focus.md"),
    ("Graphics", "Hockey/softball manual verification focus data", "data/asset_registry/hockey_softball_manual_verification_focus.csv"),
    ("Graphics", "Hockey/softball manual verification focus manifest", "data/asset_registry/hockey_softball_manual_verification_focus.json"),
    ("Graphics", "Hockey/softball asset next-action cards", "data/asset_registry/hockey_softball_asset_next_action_cards.md"),
    ("Graphics", "Hockey/softball asset next-action cards data", "data/asset_registry/hockey_softball_asset_next_action_cards.csv"),
    ("Graphics", "Hockey/softball asset next-action cards manifest", "data/asset_registry/hockey_softball_asset_next_action_cards.json"),
    ("Graphics", "Hockey/softball quarantine download intake", "data/asset_registry/hockey_softball_quarantine_download_intake.md"),
    ("Graphics", "Hockey/softball quarantine download intake data", "data/asset_registry/hockey_softball_quarantine_download_intake.csv"),
    ("Graphics", "Hockey/softball quarantine download intake manifest", "data/asset_registry/hockey_softball_quarantine_download_intake.json"),
    ("Graphics", "Women's hockey asset workflow board", "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md"),
    ("Graphics", "Softball asset workflow board", "data/asset_registry/softball/softball_asset_workflow_board.md"),
    ("Graphics", "Logo asset catalog", "data/asset_registry/logo_asset_catalog.md"),
    ("Graphics", "Logo asset catalog data", "data/asset_registry/logo_asset_catalog.csv"),
    ("Review", "Lite review zip", "hsd_pipeline_lite_review.zip"),
]

RUN_COMMANDS = {
    "game_intelligence_board_v1.md": ".\\hsd.cmd run -Mode results",
    "game_intelligence_board_v1.csv": ".\\hsd.cmd run -Mode results",
    "game_intelligence_board_v1.json": ".\\hsd.cmd run -Mode results",
    "stats_evidence_gap_board_v1.md": ".\\hsd.cmd run -Mode results",
    "stats_evidence_gap_board_v1.csv": ".\\hsd.cmd run -Mode results",
    "stats_evidence_gap_board_v1.json": ".\\hsd.cmd run -Mode results",
    "stats_confirmation_intake_v1.csv": ".\\hsd.cmd run -Mode results",
    "game_fact_confirmation_status_v1.md": ".\\hsd.cmd run -Mode results",
    "game_fact_confirmation_status_v1.csv": ".\\hsd.cmd run -Mode results",
    "game_fact_confirmation_status_v1.json": ".\\hsd.cmd run -Mode results",
    "game_source_confirmation_next_action_v1.md": ".\\hsd.cmd run -Mode results",
    "game_source_confirmation_next_action_v1.csv": ".\\hsd.cmd run -Mode results",
    "game_source_confirmation_next_action_v1.json": ".\\hsd.cmd run -Mode results",
    "game_source_research_worksheet_v1.md": ".\\hsd.cmd run -Mode results",
    "game_source_research_worksheet_v1.csv": ".\\hsd.cmd run -Mode results",
    "game_source_research_worksheet_v1.json": ".\\hsd.cmd run -Mode results",
    "game_source_confirmation_return_summary_v1.md": ".\\hsd.cmd run -Mode results",
    "game_source_confirmation_return_summary_v1.csv": ".\\hsd.cmd run -Mode results",
    "game_source_confirmation_return_summary_v1.json": ".\\hsd.cmd run -Mode results",
    "final_score_stat_proof_v1.md": ".\\hsd.cmd run -Mode results",
    "final_score_stat_proof_v1.csv": ".\\hsd.cmd run -Mode results",
    "final_score_stat_proof_v1.json": ".\\hsd.cmd run -Mode results",
    "final_score_stat_proof_confirmation_intake_v1.csv": ".\\hsd.cmd run -Mode results",
    "final_score_stat_proof_review_walkthrough_v1.md": ".\\hsd.cmd run -Mode results",
    "final_score_stat_proof_review_order_v1.csv": ".\\hsd.cmd run -Mode results",
    "athlete_render_candidate_board_v1.md": ".\\hsd.cmd run -Mode results",
    "athlete_render_candidate_board_v1.csv": ".\\hsd.cmd run -Mode results",
    "athlete_render_candidate_board_v1.json": ".\\hsd.cmd run -Mode results",
    "story_proof_card_v1.md": ".\\hsd.cmd run -Mode results",
    "story_proof_card_v1.csv": ".\\hsd.cmd run -Mode results",
    "story_proof_card_v1.json": ".\\hsd.cmd run -Mode results",
    "news_fact_packets.csv": ".\\hsd.cmd run -Mode news",
    "news_daily_plan.md": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_queue.md": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_queue.csv": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_manifest.json": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_confirmation_intake.md": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_confirmation_intake.csv": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_clusters.md": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_clusters.csv": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_next_action_v1.md": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_next_action_v1.csv": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_next_action_v1.json": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_return_summary_v1.md": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_return_summary_v1.csv": ".\\hsd.cmd run -Mode news",
    "breaking_public_signal_return_summary_v1.json": ".\\hsd.cmd run -Mode news",
    "game_source_confirmation_bridge_v1.md": ".\\hsd.cmd run -Mode news",
    "game_source_confirmation_bridge_v1.csv": ".\\hsd.cmd run -Mode news",
    "game_source_confirmation_bridge_v1.json": ".\\hsd.cmd run -Mode news",
    "news_sync_hub.md": ".\\hsd.cmd run -Mode news",
    "results_dashboard/index.html": ".\\hsd.cmd run -Mode dashboards",
    "studio_dashboard/index.html": ".\\hsd.cmd run -Mode dashboards",
    "graphics_upload_pack_status.csv": ".\\hsd.cmd run -Mode asset",
    "rendered_slide_qa_report.md": ".\\hsd.cmd run -Mode asset",
    "ig_story_results_queue.csv": ".\\hsd.cmd run -Mode stories",
    "ig_story_results_upload_pack_status.csv": ".\\hsd.cmd run -Mode stories",
    "final_score_story_guard_report.md": ".\\hsd.cmd run -Mode stories",
    "manual_workflow_handoff.md": ".\\hsd.cmd run -Mode handoff",
    "manual_workflow_pack_status.csv": ".\\hsd.cmd run -Mode handoff",
    "athlete_photo_onboarding/athlete_photo_onboarding_report.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py",
    "athlete_photo_onboarding/athlete_photo_contact_sheet_index.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py",
    "athlete_photo_onboarding/athlete_photo_onboarding_metadata.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py",
    "athlete_photo_onboarding/athlete_photo_onboarding_decision_template.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py",
    "athlete_photo_onboarding/athlete_photo_onboarding_manifest.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py",
    "data/asset_registry/wnba/athlete_identity_audit.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_wnba_athlete_identity_audit_v1.py",
    "data/asset_registry/wnba/athlete_identity_audit.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_wnba_athlete_identity_audit_v1.py",
    "data/asset_registry/wnba/athlete_identity_resolution_workflow.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py",
    "data/asset_registry/wnba/athlete_identity_resolution_candidates.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py",
    "data/asset_registry/wnba/athlete_identity_review_packet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py",
    "data/asset_registry/wnba/athlete_identity_resolution_template.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py",
    "data/asset_registry/wnba/athlete_identity_resolution_manifest.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py",
    "data/asset_registry/wnba/athlete_identity_closure_packet.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_closure_packet_v1.py",
    "data/asset_registry/wnba/athlete_identity_closure_packet.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_closure_packet_v1.py",
    "data/asset_registry/wnba/athlete_identity_issue_closure_template.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_closure_packet_v1.py",
    "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_closure_packet_v1.py",
    "identity_resolution_local_server.md": ".\\hsd.cmd run -Mode identity-decision",
    "identity_resolution_local_server.json": ".\\hsd.cmd run -Mode identity-decision",
    "identity_decision_live_writeback_verification.md": ".\\hsd.cmd run -Mode identity-decision-verify",
    "identity_decision_live_writeback_verification.json": ".\\hsd.cmd run -Mode identity-decision-verify",
    "data/asset_registry/asset_availability_audit.md": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/asset_availability_audit.csv": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/asset_availability_audit.json": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/athlete_photo_catalog.md": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/athlete_photo_catalog.csv": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/athlete_photo_catalog.json": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_index.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_manifest.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/wnba/logo_review_catalog_report.md": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/logo_review_catalog.csv": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/logo_review_catalog.json": ".\\hsd.cmd run -Mode asset-audit",
    "data/asset_registry/wnba/logo_review_packets.csv": ".\\.venv\\Scripts\\python.exe scripts\\validate_hsd_wnba_asset_registry_v1.py",
    "data/asset_registry/wnba/wnba_team_logo_contact_sheet.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_logo_contact_sheet_v1.py",
    "data/asset_registry/wnba/wnba_team_logo_contact_sheet.png": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_logo_contact_sheet_v1.py",
    "data/asset_registry/wnba/wnba_team_logo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_logo_contact_sheet_v1.py",
    "data/asset_registry/wnba/wnba_team_logo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_logo_contact_sheet_v1.py",
    "data/asset_registry/wnba/wnba_team_logo_contact_sheet.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.png": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_logo_contact_sheet_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_candidates.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_verification_queue_v1.py",
    "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_external_research_intake_v1.py",
    "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_external_research_intake_v1.py",
    "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_external_research_intake_v1.py",
    "data/asset_registry/womens_soccer/external_research/nwsl_correction_enrichment_report.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_external_research_intake_v1.py",
    "data/asset_registry/womens_soccer/external_research/europe_official_source_map.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_external_research_intake_v1.py",
    "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_womens_soccer_athlete_photo_contact_sheets_v1.py",
    "data/asset_registry/womens_soccer/nwsl/players.csv": ".\\.venv\\Scripts\\python.exe scripts\\fetch_hsd_womens_soccer_nwsl_roster_candidates_v1.py",
    "data/asset_registry/womens_soccer/nwsl/roster_candidate_fetch_report.md": ".\\.venv\\Scripts\\python.exe scripts\\fetch_hsd_womens_soccer_nwsl_roster_candidates_v1.py",
    "data/asset_registry/womens_soccer/nwsl/roster_candidate_fetch_report.json": ".\\.venv\\Scripts\\python.exe scripts\\fetch_hsd_womens_soccer_nwsl_roster_candidates_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_queue_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_manifest_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_summary_board_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_taxonomy.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_human_review_checklist.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_candidate_intake_v1.py",
    "action_photo_external_research_handoff_draft_copy.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_handoff_draft_copy_v1.py",
    "action_photo_external_research_handoff_draft_copy.txt": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_handoff_draft_copy_v1.py",
    "action_photo_external_research_handoff_draft_copy.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_action_photo_handoff_draft_copy_v1.py",
    "data/asset_registry/hockey_softball_asset_foundation_report.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/hockey_softball_foundation_coverage_index.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/hockey_softball_foundation_coverage_index.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/hockey_softball_foundation_coverage_index.json": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_logo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/softball/softball_logo_contact_sheet.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/softball/softball_logo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/softball/softball_logo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/softball/softball_athlete_photo_contact_sheet_index.md": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/softball/softball_athlete_photo_review_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_hockey_softball_asset_foundation_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md": ".\\.venv\\Scripts\\python.exe scripts\\prepare_hsd_hockey_softball_source_review_intake_v1.py",
    "data/asset_registry/softball/softball_review_walkthrough.md": ".\\.venv\\Scripts\\python.exe scripts\\prepare_hsd_hockey_softball_source_review_intake_v1.py",
    "data/asset_registry/hockey_softball_source_review_helper_report.md": ".\\.venv\\Scripts\\python.exe scripts\\prepare_hsd_hockey_softball_source_review_intake_v1.py",
    "data/asset_registry/hockey_softball_source_review_helper_report.json": ".\\.venv\\Scripts\\python.exe scripts\\prepare_hsd_hockey_softball_source_review_intake_v1.py",
    "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_workflow_readiness_report.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_action_queue.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_action_queue.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_action_queue.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_batch_source_review_helper.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_batch_source_review_helper.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_batch_source_review_helper.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_next_decision_worksheet.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_next_decision_worksheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_next_decision_worksheet.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_priority_worksheet.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_priority_worksheet.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_priority_worksheet.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_verification_checklist.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_verification_checklist.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_verification_checklist.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_intake_readiness_summary.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_intake_readiness_summary.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_intake_readiness_summary.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_map_board.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_map_board.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_map_board.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_action_photo_research_handoff.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_action_photo_research_handoff.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_action_photo_research_handoff.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_research_return_intake.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_research_return_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_source_research_return_intake.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_triage.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_triage.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_triage.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_readiness_board.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_readiness_board.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_review_readiness_board.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_manual_verification_focus.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_manual_verification_focus.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_manual_verification_focus.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_next_action_cards.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_next_action_cards.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_asset_next_action_cards.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_quarantine_download_intake.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_quarantine_download_intake.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/hockey_softball_quarantine_download_intake.json": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/softball/softball_asset_workflow_board.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_hockey_softball_asset_workflow_readiness_v1.py",
    "data/asset_registry/logo_asset_catalog.md": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_logo_asset_catalog_v1.py",
    "data/asset_registry/logo_asset_catalog.csv": ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_logo_asset_catalog_v1.py",
    "multi_post_daily_board.md": ".\\hsd.cmd run -Mode posts",
    "post_slot_status.csv": ".\\hsd.cmd run -Mode posts",
    "ig_feed_queue.csv": ".\\hsd.cmd run -Mode posts",
    "ig_story_queue.csv": ".\\hsd.cmd run -Mode posts",
    "threads_queue.csv": ".\\hsd.cmd run -Mode posts",
    "caption_bank.md": ".\\hsd.cmd run -Mode posts",
    "first_comment_hooks.md": ".\\hsd.cmd run -Mode posts",
    "manual_story_inbox_report.md": ".\\hsd.cmd run -Mode review",
    "story_candidates_manual.csv": ".\\hsd.cmd run -Mode review",
    "discovery_sources_report.md": ".\\hsd.cmd run -Mode review",
    "story_candidates_discovery.csv": ".\\hsd.cmd run -Mode review",
    "morning_source_discovery_board.md": ".\\hsd.cmd run -Mode review",
    "morning_source_discovery_board.csv": ".\\hsd.cmd run -Mode review",
    "morning_source_discovery_board.json": ".\\hsd.cmd run -Mode review",
    "morning_lead_promotion_recommendations.md": ".\\hsd.cmd run -Mode review",
    "morning_lead_promotion_recommendations.csv": ".\\hsd.cmd run -Mode review",
    "morning_lead_promotion_recommendations.json": ".\\hsd.cmd run -Mode review",
    "render_handoff_top_packet/draft_preview.png": ".\\hsd.cmd run -Mode render",
    "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png": ".\\hsd.cmd run -Mode render",
    "render_handoff_top_packet/review_drafts/draft_preview_story.png": ".\\hsd.cmd run -Mode render",
    "render_handoff_top_packet/review_drafts/draft_preview_square.png": ".\\hsd.cmd run -Mode render",
    "manual_review_renderer_report.md": ".\\hsd.cmd run -Mode render",
    "manual_review_renderer_manifest.json": ".\\hsd.cmd run -Mode render",
    "render_visual_delta_report.md": ".\\hsd.cmd run -Mode render",
    "render_visual_delta.csv": ".\\hsd.cmd run -Mode render",
    "render_visual_delta_manifest.json": ".\\hsd.cmd run -Mode render",
    "render_visual_revision_plan.md": ".\\hsd.cmd run -Mode render",
    "render_visual_revision_plan.csv": ".\\hsd.cmd run -Mode render",
    "render_visual_revision_plan.json": ".\\hsd.cmd run -Mode render",
    "render_next_level_editorial_qa.md": ".\\hsd.cmd run -Mode render",
    "render_next_level_editorial_qa.csv": ".\\hsd.cmd run -Mode render",
    "render_next_level_editorial_qa.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_report.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_manifest.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_checklist.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_approval_intake.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_approval_intake.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_approval_intake.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_draft.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_draft.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_draft.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_template.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_template.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_template.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_intake.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_intake.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_intake.json": ".\\hsd.cmd run -Mode render",
    "manual_post_approval_render_staging.md": ".\\hsd.cmd run -Mode render",
    "manual_post_approval_render_staging.csv": ".\\hsd.cmd run -Mode render",
    "manual_post_approval_render_staging.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_walkthrough.md": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_walkthrough.csv": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_walkthrough.json": ".\\hsd.cmd run -Mode render",
    "manual_visual_qa_operator_decision_inbox_starter.md": ".\\hsd.cmd run -Mode decision-inbox",
    "manual_visual_qa_operator_decision_inbox_starter.csv": ".\\hsd.cmd run -Mode decision-inbox",
    "manual_visual_qa_operator_decision_inbox_starter.json": ".\\hsd.cmd run -Mode decision-inbox",
    "source_registry_intake_template.md": ".\\hsd.cmd run -Mode review",
    "source_registry_intake_template.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_review.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_review.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_draft.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_draft.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_promotion_checklist.md": ".\\hsd.cmd run -Mode review",
    "source_registry_proposal_promotion_checklist.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_update_worksheet.md": ".\\hsd.cmd run -Mode review",
    "source_registry_update_worksheet.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_diff_review.md": ".\\hsd.cmd run -Mode review",
    "source_registry_diff_review.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_same_domain_resolution.md": ".\\hsd.cmd run -Mode review",
    "source_registry_same_domain_resolution.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_verification_log.md": ".\\hsd.cmd run -Mode review",
    "source_registry_verification_log.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_approval_packet.md": ".\\hsd.cmd run -Mode review",
    "source_registry_approval_packet.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_patch_preview.md": ".\\hsd.cmd run -Mode review",
    "source_registry_patch_preview.csv": ".\\hsd.cmd run -Mode review",
    "source_registry_post_edit_validation.md": ".\\hsd.cmd run -Mode review",
    "source_registry_post_edit_validation.csv": ".\\hsd.cmd run -Mode review",
    "trusted_registry_operator_playbook.md": ".\\hsd.cmd run -Mode review",
    "source_proposal_pack_readiness.md": ".\\hsd.cmd run -Mode review",
    "source_proposal_pack_readiness.csv": ".\\hsd.cmd run -Mode review",
    "source_proposal_packs.md": ".\\hsd.cmd run -Mode review",
    "source_proposal_packs.csv": ".\\hsd.cmd run -Mode review",
    "wnba_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "wnba_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "nwsl_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "nwsl_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "lpga_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "lpga_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "pwhl_source_proposal_pack.md": ".\\hsd.cmd run -Mode review",
    "pwhl_source_proposal_pack.csv": ".\\hsd.cmd run -Mode review",
    "launch_daily_runbook.md": ".\\hsd.cmd run -Mode launch",
    "launch_graphics_chat_brief.md": ".\\hsd.cmd run -Mode launch",
    "launch_daily_operator_checklist.md": ".\\hsd.cmd run -Mode launch",
    "launch_7_day_performance_dashboard.md": ".\\hsd.cmd run -Mode launch",
    "launch_manifest.json": ".\\hsd.cmd run -Mode launch",
    "launch_dashboard/index.html": ".\\hsd.cmd run -Mode launch",
    "launch_analytics_dashboard/index.html": ".\\hsd.cmd run -Mode launch",
}


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def local_latest_path(path: str | Path) -> Path:
    return Path.cwd() / "outputs" / "local" / "latest" / "files" / Path(path)


def mirror_review_artifacts_to_output() -> None:
    output_root = output_path(".").resolve()
    cwd = Path.cwd().resolve()
    if output_root == cwd:
        return
    for raw_path in MIRRORED_REVIEW_ARTIFACTS:
        source = Path(raw_path)
        if not source.exists():
            continue
        destination = output_path(raw_path)
        try:
            if source.resolve() == destination.resolve():
                continue
        except Exception:
            pass
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)


def find_existing_input(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p

    candidates: List[Path] = []
    run_root = output_path(".").resolve()
    cwd = Path.cwd().resolve()
    if run_root != cwd:
        candidates.append(run_root / p)
    latest = local_latest_path(path)
    candidates.append(latest)
    candidates.extend(input_candidates(path))

    deduped: List[Path] = []
    seen = set()
    for candidate in candidates:
        key = candidate.as_posix()
        if key not in seen:
            seen.add(key)
            deduped.append(candidate)
    for candidate in deduped:
        if candidate.exists():
            return candidate
    return deduped[0]


def href_for_path(path: str) -> str:
    found = find_existing_input(path)
    current_output = output_path(".").resolve()
    try:
        return found.resolve().relative_to(current_output).as_posix()
    except Exception:
        try:
            return found.resolve().as_uri()
        except Exception:
            return found.as_posix()


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "ready"}


def read_text(path: str, max_chars: int | None = None) -> str:
    p = find_existing_input(path)
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars] if max_chars else text


def read_json(path: str) -> Dict[str, Any]:
    p = find_existing_input(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_csv(path: str) -> List[Dict[str, str]]:
    p = find_existing_input(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def first_present(*values: Any, default: str = "") -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return default


def short(text: str, limit: int = 180) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def status_tone(value: Any) -> str:
    text = clean(value).lower()
    if not text:
        return "neutral"
    if any(token in text for token in ["pass", "ready", "ok", "allow", "yes", "true", "complete", "high"]):
        return "good"
    if any(token in text for token in ["fail", "blocked", "missing", "error", "no-go", "false", "critical", "hold"]):
        return "bad"
    if any(token in text for token in ["review", "pending", "not_run", "not created", "not_created", "draft", "needed"]):
        return "warn"
    return "neutral"


def display_bool(value: Any) -> str:
    return "Yes" if yes(value) else "No"


def as_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def packet_source_confidence(row: Dict[str, Any]) -> Dict[str, str]:
    explicit_grade = first_present(row.get("source_publish_grade"), row.get("source_confidence_tier"))
    if explicit_grade:
        return {
            "source_grade": explicit_grade,
            "source_score": clean(row.get("source_confidence_score")),
            "source_reason": short(clean(row.get("source_confidence_reason")), 160),
        }

    source_count = as_int(row.get("source_count"))
    primary_count = as_int(row.get("primary_source_count"))
    if yes(row.get("production_ready")) and primary_count:
        grade = "publish_grade"
        reason = "Legacy packet inferred from production-ready status and primary source count"
    elif yes(row.get("production_ready")) and source_count >= 2:
        grade = "review_before_publish"
        reason = "Legacy packet inferred from production-ready status and multiple sources"
    elif source_count:
        grade = "discovery_only"
        reason = "Legacy packet has source depth but no confidence fields"
    else:
        grade = "not_scored"
        reason = "No source confidence fields found"

    return {"source_grade": grade, "source_score": "", "source_reason": reason}


def split_tokens(value: Any) -> List[str]:
    text = clean(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"[;,|]", text) if part.strip()]


def clamp_score(score: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, score))


def render_readiness_band(score: int, blockers: List[str]) -> str:
    if blockers:
        if any("source" in blocker or "confirmation" in blocker for blocker in blockers):
            return "hold_for_source_confirmation"
        if any("asset" in blocker for blocker in blockers):
            return "hold_for_asset_review"
        return "hold_before_render"
    if score >= 85:
        return "render_ready_review"
    if score >= 65:
        return "render_prep_candidate"
    if score >= 45:
        return "needs_operator_review"
    return "hold_before_render"


def display_render_blockers(row: Mapping[str, Any]) -> str:
    blockers = clean(row.get("blockers"))
    if blockers and blockers != "none":
        return blockers
    active_logo = clean(row.get("active_logo_readiness_status"))
    active_athlete = clean(row.get("active_athlete_identity_status"))
    if active_logo.startswith("hold_") or active_athlete.startswith("hold_"):
        return "none for source/format/manual path; active asset holds remain"
    return "none for source/format/manual path"


def active_asset_stop_go(row: Mapping[str, Any]) -> str:
    active_logo = clean(row.get("active_logo_readiness_status"))
    active_athlete = clean(row.get("active_athlete_identity_status"))
    if active_logo.startswith("hold_") or active_athlete.startswith("hold_"):
        return "hold_required_manual_asset_review"
    if active_logo and active_logo != "logo_review_not_flagged":
        return "manual_asset_review_required"
    if active_athlete and active_athlete != "athlete_identity_not_flagged":
        return "manual_asset_review_required"
    return "clear_no_active_asset_holds"


def score_render_readiness(
    row: Dict[str, str],
    *,
    item_type: str,
    headline: str,
    artifact: str,
    artifact_exists: Dict[str, bool] | None = None,
) -> Dict[str, str]:
    artifact_exists = artifact_exists or {}
    score = 0
    blockers: List[str] = []

    source_grade = clean(first_present(row.get("source_grade"), row.get("story_opportunity_confidence_tier")))
    source_coverage = clean(row.get("story_opportunity_source_coverage"))
    confirmation = clean(row.get("story_opportunity_confirmation_cue"))
    source_count = as_int(row.get("source_count")) or len(split_tokens(row.get("story_opportunity_sources")))
    second_source = clean(first_present(row.get("story_opportunity_second_source_id"), row.get("story_opportunity_second_source_lane")))

    if source_grade in {"publish_grade", "publish_grade_candidate"}:
        score += 35
        source_cue = "source_confidence_ready"
    elif source_grade in {"review_before_publish", "needs_official_confirmation"}:
        score += 18
        source_cue = "source_confirmation_needed"
    elif source_grade in {"discovery_only", "discovery_source_only"} or source_coverage == "discovery_source_only":
        score += 8
        source_cue = "discovery_only_source"
    elif source_count >= 2:
        score += 22
        source_cue = "source_depth_present"
    else:
        score += 6
        source_cue = "source_confidence_missing"

    if source_count >= 2:
        score += 6
    if second_source and second_source != "n/a":
        score += 4
    if confirmation in {"needs_second_source", "needs_official_confirmation"}:
        blockers.append("source confirmation required")
        score = min(score, 24)
    elif confirmation in {"already_covered", "official_confirmed", "source_confidence_ready"}:
        score += 5

    asset_cue = clean(row.get("story_opportunity_asset_cue"))
    status = clean(row.get("status")).lower()
    if asset_cue in {"asset_not_required_for_news_packet", "asset_ready", "assets_ready"}:
        score += 25
        asset_readiness = asset_cue
    elif asset_cue == "asset_check_required_before_studio":
        score += 8
        blockers.append("asset review required")
        asset_readiness = asset_cue
    elif status in {"ready", "graphics ready", "allow"}:
        score += 22
        asset_readiness = "artifact_assets_ready_or_not_required"
    elif item_type.lower().startswith("news"):
        score += 20
        asset_readiness = "asset_not_required_for_news_packet"
    else:
        score += 10
        asset_readiness = "asset_readiness_review"

    recommended_path = clean(first_present(row.get("story_opportunity_recommended_path"), row.get("recommendation"), item_type))
    path_token = re.sub(r"[^a-z0-9]+", "_", recommended_path.lower()).strip("_")
    if recommended_path in {"news_packet", "manual_story_candidate", "studio_brief", "News packet", "Final result"}:
        score += 20
        format_fit = f"{path_token}_format_fit"
    elif recommended_path:
        score += 12
        format_fit = f"{path_token}_needs_format_review"
    else:
        score += 5
        format_fit = "format_path_missing"

    manual_path_exists = bool(artifact and artifact_exists.get(artifact, input_path(artifact).exists()))
    if manual_path_exists:
        score += 20
        manual_path = f"manual_review_artifact_ready:{artifact}"
    elif artifact:
        score += 8
        manual_path = f"create_manual_artifact:{artifact}"
        blockers.append("manual render path artifact missing")
    else:
        manual_path = "manual_render_path_missing"
        blockers.append("manual render path missing")

    if "source confirmation required" in blockers:
        score = min(score, 55)
    if "asset review required" in blockers:
        score = min(score, 70)
    if "manual render path artifact missing" in blockers or "manual render path missing" in blockers:
        score = min(score, 60)
    score = clamp_score(score)
    band = render_readiness_band(score, blockers)
    next_step = "Open the artifact, confirm facts visually, then prepare a manual render; publishing stays off."
    if "source confirmation required" in blockers:
        next_step = "Verify the second official, wire, or primary source before News, Studio, or render work."
    elif "asset review required" in blockers:
        next_step = "Confirm the asset path, crop, and identity before render prep."
    elif "manual render path artifact missing" in blockers:
        next_step = "Create the missing manual artifact before render prep."
    elif band == "render_prep_candidate":
        next_step = "Review the remaining cues, then move this into manual render prep."

    return {
        "render_readiness_score": str(score),
        "render_readiness_band": band,
        "render_readiness_source_cue": source_cue,
        "render_readiness_asset_cue": asset_readiness,
        "render_readiness_format_cue": format_fit,
        "render_readiness_manual_path": manual_path,
        "render_readiness_blockers": "; ".join(blockers) if blockers else "none",
        "render_readiness_next_step": next_step,
    }


def parse_markdown_table(path: str) -> List[Dict[str, str]]:
    text = read_text(path)
    rows: List[Dict[str, str]] = []
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return rows
    headers = [clean(cell) for cell in lines[0].strip("|").split("|")]
    for line in lines[2:]:
        cells = [clean(cell) for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def artifact_entries() -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for group, title, path in ARTIFACTS:
        p = find_existing_input(path)
        generated_this_run = path in COMMAND_CENTER_GENERATED_ARTIFACTS
        exists = p.exists() or generated_this_run
        source_path = output_path(path).as_posix() if generated_this_run else p.as_posix() if p.exists() else ""
        snippet = ""
        if generated_this_run:
            snippet = "Generated by this command center run."
        elif path in VOLATILE_RENDER_ARTIFACTS and p.exists():
            snippet = "Renderer artifact is volatile; open the linked file for the current review-only report."
        elif p.suffix.lower() in {".csv", ".json", ".md", ".txt"}:
            snippet = short(read_text(path, 480), 260)
        elif p.exists():
            snippet = f"Binary artifact ({p.stat().st_size} bytes)"
        entries.append(
            {
                "group": group,
                "title": title,
                "path": path,
                "exists": exists,
                "size": p.stat().st_size if p.exists() and p.is_file() else 0,
                "snippet": snippet,
                "run_command": RUN_COMMANDS.get(path, ""),
                "status_detail": "Created with this command center run" if generated_this_run else "Ready to open" if p.exists() else missing_artifact_detail(path),
                "source_path": source_path,
            }
        )
    entries.extend(action_photo_bundle_artifact_entries())
    return entries


def action_photo_bundle_artifact_entries() -> List[Dict[str, Any]]:
    latest_path = find_existing_input("action_photo_external_research_bundle_latest.json")
    if not latest_path.exists():
        return []

    try:
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    output_root = output_path(".").resolve()
    dynamic_paths = [
        ("Graphics", "Action-photo external research bundle README", latest.get("readme_path")),
        ("Graphics", "Action-photo external research bundle packet manifest", latest.get("manifest_path")),
    ]
    entries: List[Dict[str, Any]] = []
    for group, title, raw_path in dynamic_paths:
        raw = clean(raw_path)
        if not raw:
            continue
        p = Path(raw)
        if not p.exists():
            continue
        try:
            display_path = p.resolve().relative_to(output_root).as_posix()
        except ValueError:
            continue
        snippet = short(p.read_text(encoding="utf-8"), 260) if p.suffix.lower() in {".json", ".md", ".txt"} else ""
        entries.append(
            {
                "group": group,
                "title": title,
                "path": display_path,
                "exists": True,
                "size": p.stat().st_size if p.is_file() else 0,
                "snippet": snippet,
                "run_command": ".\\.venv\\Scripts\\python.exe scripts\\build_hsd_action_photo_research_bundle_v1.py",
                "status_detail": "Ready to open",
                "source_path": p.as_posix(),
            }
        )
    return entries


def file_shortcut(label: str, path: str, purpose: str) -> Dict[str, Any]:
    found = find_existing_input(path)
    return {
        "label": label,
        "path": path,
        "purpose": purpose,
        "exists": found.exists(),
        "href": href_for_path(path) if found.exists() else "",
        "source_path": found.as_posix() if found.exists() else "",
    }


def asset_audit_severity_rank(value: Any) -> int:
    return {"error": 0, "warning": 1, "info": 2}.get(clean(value).lower(), 3)


def asset_audit_finding_rank(row: Dict[str, Any]) -> int:
    finding = clean(row.get("finding"))
    if finding == "suspicious_or_default_player_approval":
        return 0
    if finding == "logo_present_without_complete_approval":
        return 1
    if finding == "suspicious_logo_source_or_approval":
        return 2
    if finding == "missing_or_unregistered_logo_asset":
        return 3
    if finding == "renderer_active_logo_fallback":
        return 4
    if finding in {"renderer_hsd_team_badge_review", "renderer_team_spotlight_fallback_review", "renderer_fixture_reference_asset_review"}:
        return 5
    if finding == "renderer_logo_audit_missing":
        return 6
    if finding == "missing_local_player_asset":
        return 7
    if "format" in finding or "dimension" in finding:
        return 8
    return 9


def asset_audit_decision_guidance(row: Dict[str, Any]) -> Dict[str, str]:
    finding = clean(row.get("finding"))
    domain = clean(row.get("asset_domain"))
    if finding == "suspicious_or_default_player_approval":
        return {
            "decision": "Verify identity",
            "tone": "warn",
            "manual_action": "Verify the athlete against official/free source evidence before allowing photo-first review renders.",
            "hold_cue": "Hold the image if identity, source, or provider ID is not source-backed.",
            "revise_cue": "Revise the local asset if the crop, player identity, or source file does not match.",
            "open_path": "data/asset_registry/wnba/athlete_photo_catalog.md",
        }
    if domain == "player_photo":
        return {
            "decision": "Hold photo slot",
            "tone": "bad",
            "manual_action": "Keep this athlete photo slot disabled until a reviewed local asset and approval marker exist.",
            "hold_cue": "Hold if the file is missing, unreadable, or crop identity is not proven.",
            "revise_cue": "Revise by adding a review-only candidate through the asset onboarding workflow.",
            "open_path": "data/asset_registry/wnba/athlete_photo_catalog.md",
        }
    if finding == "suspicious_logo_source_or_approval":
        return {
            "decision": "Revise source",
            "tone": "warn",
            "manual_action": "Replace or reverify the logo source against official/free team or league pages.",
            "hold_cue": "Hold renderer trust while the source is blocked, stale, or non-official.",
            "revise_cue": "Revise the registry source row after manual evidence review.",
            "open_path": "data/asset_registry/wnba/logo_review_catalog_report.md",
        }
    if domain == "team_logo":
        return {
            "decision": "Verify logo",
            "tone": "warn",
            "manual_action": "Compare the local team logo against official/free source evidence before renderer trust.",
            "hold_cue": "Hold if approval is incomplete or source evidence is not official enough.",
            "revise_cue": "Revise local/source metadata before using the mark in branded renders.",
            "open_path": "data/asset_registry/wnba/logo_review_catalog_report.md",
        }
    if domain == "league_logo":
        return {
            "decision": "Hold league mark",
            "tone": "bad",
            "manual_action": "Add a review-only league mark source and local slot before any template depends on it.",
            "hold_cue": "Hold if the league mark is missing or unregistered.",
            "revise_cue": "Revise by proposing official/free league mark evidence, not by inventing a mark.",
            "open_path": "data/asset_registry/wnba/logo_review_catalog_report.md",
        }
    if domain == "renderer":
        fallback_cue = clean(row.get("renderer_fallback_cue"))
        return {
            "decision": "Verify renderer fallback",
            "tone": "neutral" if clean(row.get("severity")) == "info" else "warn",
            "manual_action": fallback_cue or "Run a local render/status pass to confirm whether active fallback badges are still present.",
            "hold_cue": fallback_cue or "Hold if a template is using text badges where exact approved assets are required.",
            "revise_cue": "Revise the asset registry or template mapping only after source-backed review.",
            "open_path": "data/asset_registry/asset_availability_audit.md",
        }
    return {
        "decision": "Review manually",
        "tone": status_tone(row.get("severity")),
        "manual_action": clean(row.get("recommended_next_step")) or "Review this asset finding before render work.",
        "hold_cue": "Hold if source, identity, crop, format, or approval evidence is incomplete.",
        "revise_cue": "Revise the source or local asset metadata through review-only workflows.",
        "open_path": "data/asset_registry/asset_availability_audit.md",
    }


def normalize_asset_audit_finding(row: Dict[str, Any], rank: int) -> Dict[str, str]:
    guidance = asset_audit_decision_guidance(row)
    open_path = guidance["open_path"]
    domain = clean(row.get("asset_domain")) or "unknown"
    finding = clean(row.get("finding")) or "review_required"
    entity_name = clean(row.get("entity_name")) or clean(row.get("entity_id")) or "Unknown asset"
    default_decision = clean(row.get("default_operator_decision")) or audit_default_operator_decision(domain, finding)
    readiness = audit_asset_readiness(row) or "manual_review_required"
    source_confidence = clean(row.get("source_confidence"))
    if not source_confidence and domain in {"team_logo", "league_logo"} and "missing" in finding:
        source_confidence = "source_missing_or_unregistered"
    identity_confidence = clean(row.get("identity_confidence"))
    if not identity_confidence and domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        identity_confidence = "identity_hold_default_or_suspicious_approval"
    blocker_summary = clean(row.get("blocker_summary")) or f"{entity_name}: {finding}; default decision={default_decision}; readiness={readiness}"
    return {
        "rank": str(rank),
        "asset_domain": domain,
        "league": clean(row.get("league")),
        "entity_type": clean(row.get("entity_type")),
        "entity_id": clean(row.get("entity_id")),
        "entity_name": entity_name,
        "asset_kind": clean(row.get("asset_kind")),
        "asset_path": clean(row.get("asset_path")),
        "finding": finding,
        "severity": clean(row.get("severity")) or "review",
        "approval_status": clean(row.get("approval_status")),
        "format_status": clean(row.get("format_status")),
        "dimension_status": clean(row.get("dimension_status")),
        "renderer_coverage": clean(row.get("renderer_coverage")),
        "review_packet_id": clean(row.get("review_packet_id")),
        "decision_lane": clean(row.get("decision_lane")) or audit_decision_lane(domain, finding, clean(row.get("league"))),
        "default_operator_decision": default_decision,
        "source_confidence": source_confidence,
        "identity_confidence": identity_confidence,
        "manual_approval_status": clean(row.get("manual_approval_status")) or clean(row.get("approval_status")) or "manual_review_required",
        "asset_readiness": readiness,
        "renderer_fallback_cue": clean(row.get("renderer_fallback_cue")),
        "operator_copy_target": clean(row.get("operator_copy_target")),
        "manual_review_packet": clean(row.get("manual_review_packet")),
        "blocker_summary": blocker_summary,
        "recommended_next_step": clean(row.get("recommended_next_step")) or guidance["manual_action"],
        "evidence": short(clean(row.get("evidence")), 260),
        "decision": guidance["decision"],
        "tone": guidance["tone"],
        "manual_action": guidance["manual_action"],
        "hold_cue": guidance["hold_cue"],
        "revise_cue": guidance["revise_cue"],
        "open_path": open_path,
        "open_href": href_for_path(open_path) if find_existing_input(open_path).exists() else "",
    }


def top_asset_audit_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    sorted_findings = sorted(
        findings,
        key=lambda row: (
            asset_audit_severity_rank(row.get("severity")),
            asset_audit_finding_rank(row),
            clean(row.get("asset_domain")),
            clean(row.get("entity_name")),
            clean(row.get("asset_kind")),
        ),
    )
    selected: List[Dict[str, str]] = []
    used_keys = set()
    lanes = [
        ("player_photo", "suspicious_or_default_player_approval"),
        ("player_photo", ""),
        ("team_logo", ""),
        ("league_logo", ""),
        ("renderer", ""),
    ]
    for domain, preferred_finding in lanes:
        for row in sorted_findings:
            if clean(row.get("asset_domain")) != domain:
                continue
            if preferred_finding and clean(row.get("finding")) != preferred_finding:
                continue
            key = (clean(row.get("asset_domain")), clean(row.get("entity_id")), clean(row.get("finding")), clean(row.get("asset_kind")))
            if key in used_keys:
                continue
            used_keys.add(key)
            selected.append(normalize_asset_audit_finding(row, len(selected) + 1))
            break
    if len(selected) < 8:
        for row in sorted_findings:
            key = (clean(row.get("asset_domain")), clean(row.get("entity_id")), clean(row.get("finding")), clean(row.get("asset_kind")))
            if key in used_keys:
                continue
            used_keys.add(key)
            selected.append(normalize_asset_audit_finding(row, len(selected) + 1))
            if len(selected) >= 8:
                break
    return selected


def logo_review_packet_rows(rows: Iterable[Dict[str, str]], *, limit: int = 8) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for row in rows:
        packet_id = clean(row.get("packet_id")) or clean(row.get("decision_packet_id"))
        team_id = clean(row.get("team_id"))
        issue_type = clean(row.get("issue_type")) or clean(row.get("decision_review_status"))
        if not (packet_id or team_id or issue_type):
            continue
        item = {str(key): clean(value) for key, value in row.items()}
        item["packet_id"] = packet_id or f"logo_packet_{team_id or len(normalized) + 1}"
        item["issue_type"] = issue_type or "logo_review_required"
        normalized.append(item)
    return sorted(
        normalized,
        key=lambda row: (
            0 if "unapproved" in clean(row.get("issue_type")) else 1,
            clean(row.get("team_name")) or clean(row.get("team_id")),
            clean(row.get("packet_id")),
        ),
    )[:limit]


def packet_freshness_cue(path: str, rows: int, run_command: str, *, context: str) -> Dict[str, str]:
    exists = find_existing_input(path).exists()
    if exists and rows > 0:
        return {
            "path": path,
            "status": "packet_ready",
            "detail": f"{context} packet is present with {rows} row(s).",
            "run_command": run_command,
        }
    if rows > 0:
        return {
            "path": path,
            "status": "packet_missing",
            "detail": f"{context} packet has {rows} manifest row(s), but the clickable packet file is missing; rerun the packet generator.",
            "run_command": run_command,
        }
    if exists:
        return {
            "path": path,
            "status": "packet_empty",
            "detail": f"{context} packet is present but has 0 row(s); use the catalog/audit rows for context or rerun the packet generator if holds are active.",
            "run_command": run_command,
        }
    return {
        "path": path,
        "status": "packet_missing",
        "detail": f"{context} packet is missing in this snapshot; active holds may still be visible from the latest audit or render prep. Run the listed refresh command to refresh review packets.",
        "run_command": run_command,
    }


def packet_freshness_markdown(cue: Mapping[str, str], label: str) -> str:
    command = clean(cue.get("run_command"))
    return (
        f"- {label} packet freshness: {cue.get('status') or 'unknown'} | "
        f"{cue.get('detail') or 'refresh packet before trusting counts'}"
        f"{' | refresh: `' + command + '`' if command else ''}"
    )


def packet_freshness_html(panel: Mapping[str, Any], prefix: str, label: str) -> str:
    status = clean(panel.get(f"{prefix}_freshness_status")) or "packet_unknown"
    detail = clean(panel.get(f"{prefix}_freshness_detail")) or "Refresh packet before trusting packet counts."
    command = clean(panel.get(f"{prefix}_refresh_command"))
    tone = "good" if status == "packet_ready" else "warn" if status in {"packet_missing", "packet_empty"} else "neutral"
    command_line = f"<code>{html.escape(command)}</code>" if command else ""
    return f"""
      <div class="packet-freshness-cue">
        <div class="row-kicker">{html.escape(label)} packet freshness {pill(status, tone)}</div>
        <p>{html.escape(detail)}</p>
        {command_line}
      </div>
    """


def hockey_softball_helper_summary_rows(manifest: Mapping[str, Any] | None) -> int:
    if not isinstance(manifest, dict):
        return 0
    summaries = manifest.get("summaries")
    if not isinstance(summaries, list):
        return 0
    return sum(
        as_int(row.get("logo_contact_rows")) + as_int(row.get("athlete_contact_rows"))
        for row in summaries
        if isinstance(row, dict)
    )


def hockey_softball_workflow_summary_rows(manifest: Mapping[str, Any] | None) -> int:
    if not isinstance(manifest, dict):
        return 0
    totals = manifest.get("totals")
    if isinstance(totals, dict):
        return as_int(totals.get("workflow_rows"))
    summaries = manifest.get("summaries")
    if not isinstance(summaries, list):
        return 0
    return sum(as_int(row.get("workflow_rows")) for row in summaries if isinstance(row, dict))


def hockey_softball_workflow_sport_summary(manifest: Mapping[str, Any] | None, sport_family: str) -> Dict[str, Any]:
    if not isinstance(manifest, dict):
        return {}
    summaries = manifest.get("summaries")
    if not isinstance(summaries, list):
        return {}
    for row in summaries:
        if isinstance(row, dict) and clean(row.get("sport_family")) == sport_family:
            return dict(row)
    return {}


def asset_availability_readiness_panel() -> Dict[str, Any]:
    audit = read_json("data/asset_registry/asset_availability_audit.json")
    logo_packet_rows = read_csv("data/asset_registry/wnba/logo_review_packets.csv")
    logo_contact_manifest = read_json("data/asset_registry/wnba/wnba_team_logo_contact_sheet.json")
    logo_contact_rows = read_csv("data/asset_registry/wnba/wnba_team_logo_contact_sheet.csv")
    womens_soccer_logo_contact_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.json")
    womens_soccer_logo_contact_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.csv")
    womens_soccer_logo_walkthrough_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.json")
    womens_soccer_logo_walkthrough_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.csv")
    womens_soccer_athlete_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json")
    womens_soccer_athlete_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv")
    womens_soccer_athlete_operator_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.json")
    womens_soccer_athlete_operator_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.csv")
    womens_soccer_athlete_download_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.json")
    womens_soccer_athlete_download_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv")
    womens_soccer_athlete_verification_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.json")
    womens_soccer_athlete_verification_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.csv")
    womens_soccer_athlete_next_actions_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.json")
    womens_soccer_athlete_next_actions_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.csv")
    womens_soccer_athlete_source_priority_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.json")
    womens_soccer_athlete_source_priority_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.csv")
    womens_soccer_athlete_review_triage_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.json")
    womens_soccer_athlete_review_triage_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.csv")
    womens_soccer_athlete_candidate_actions_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.json")
    womens_soccer_athlete_candidate_actions_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.csv")
    womens_soccer_athlete_photo_readiness_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.json")
    womens_soccer_athlete_photo_readiness_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.csv")
    womens_soccer_athlete_operator_focus_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.json")
    womens_soccer_athlete_operator_focus_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.csv")
    womens_soccer_action_photo_research_next_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.json")
    womens_soccer_action_photo_research_next_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv")
    womens_soccer_athlete_closure_manifest = read_json("data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.json")
    womens_soccer_athlete_closure_rows = read_csv("data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.csv")
    womens_soccer_external_research_manifest = read_json("data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.json")
    womens_soccer_external_research_rows = read_csv("data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.csv")
    action_photo_intake_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.json")
    action_photo_source_map_board_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.json")
    action_photo_manual_source_hunt_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.json")
    action_photo_operator_worksheet_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.json")
    action_photo_research_return_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.json")
    action_photo_research_return_paste_worksheet_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.json")
    action_photo_research_bundle_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.json")
    action_photo_preflight_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.json")
    action_photo_quality_fit_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.json")
    action_photo_quality_fit_operator_cue_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.json")
    action_photo_download_decision_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.json")
    action_photo_hero_targets_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.json")
    action_photo_cutout_readiness_manifest = read_json("data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.json")
    hockey_softball_manifest = read_json("data/asset_registry/hockey_softball_asset_foundation_report.json")
    womens_hockey_logo_rows = read_csv("data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.csv")
    womens_hockey_athlete_manifest = read_json("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_manifest.json")
    womens_hockey_athlete_rows = read_csv("data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet.csv")
    softball_logo_rows = read_csv("data/asset_registry/softball/softball_logo_contact_sheet.csv")
    softball_athlete_manifest = read_json("data/asset_registry/softball/softball_athlete_photo_contact_sheet_manifest.json")
    softball_athlete_rows = read_csv("data/asset_registry/softball/softball_athlete_photo_contact_sheet.csv")
    hockey_softball_helper_manifest = read_json("data/asset_registry/hockey_softball_source_review_helper_report.json")
    hockey_softball_coverage_manifest = read_json("data/asset_registry/hockey_softball_foundation_coverage_index.json")
    hockey_softball_workflow_manifest = read_json("data/asset_registry/hockey_softball_asset_workflow_readiness_report.json")
    hockey_softball_action_queue_manifest = read_json("data/asset_registry/hockey_softball_asset_review_action_queue.json")
    hockey_softball_batch_source_review_manifest = read_json("data/asset_registry/hockey_softball_batch_source_review_helper.json")
    hockey_softball_next_decision_manifest = read_json("data/asset_registry/hockey_softball_next_decision_worksheet.json")
    hockey_softball_source_priority_manifest = read_json("data/asset_registry/hockey_softball_source_priority_worksheet.json")
    hockey_softball_source_verification_manifest = read_json("data/asset_registry/hockey_softball_source_verification_checklist.json")
    hockey_softball_intake_readiness_manifest = read_json("data/asset_registry/hockey_softball_intake_readiness_summary.json")
    hockey_softball_source_map_manifest = read_json("data/asset_registry/hockey_softball_source_map_board.json")
    hockey_softball_action_photo_handoff_manifest = read_json("data/asset_registry/hockey_softball_action_photo_research_handoff.json")
    hockey_softball_source_research_return_manifest = read_json("data/asset_registry/hockey_softball_source_research_return_intake.json")
    hockey_softball_review_triage_manifest = read_json("data/asset_registry/hockey_softball_asset_review_triage.json")
    hockey_softball_asset_readiness_manifest = read_json("data/asset_registry/hockey_softball_asset_review_readiness_board.json")
    hockey_softball_manual_focus_manifest = read_json("data/asset_registry/hockey_softball_manual_verification_focus.json")
    hockey_softball_next_action_cards_manifest = read_json("data/asset_registry/hockey_softball_asset_next_action_cards.json")
    hockey_softball_quarantine_download_manifest = read_json("data/asset_registry/hockey_softball_quarantine_download_intake.json")
    logo_contact_cue = packet_freshness_cue(
        "data/asset_registry/wnba/wnba_team_logo_contact_sheet.md",
        len(logo_contact_rows),
        RUN_COMMANDS["data/asset_registry/wnba/wnba_team_logo_contact_sheet.md"],
        context="WNBA team logo contact sheet",
    )
    womens_soccer_logo_contact_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md",
        len(womens_soccer_logo_contact_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md"],
        context="women's soccer logo contact sheet",
    )
    womens_soccer_logo_walkthrough_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md",
        len(womens_soccer_logo_walkthrough_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md"],
        context="women's soccer logo review walkthrough",
    )
    womens_soccer_athlete_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md",
        len(womens_soccer_athlete_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md"],
        context="women's soccer athlete photo contact sheets",
    )
    womens_soccer_athlete_operator_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md",
        len(womens_soccer_athlete_operator_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md"],
        context="women's soccer athlete operator board",
    )
    womens_soccer_athlete_download_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.md",
        len(womens_soccer_athlete_download_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.md"],
        context="women's soccer athlete photo download intake",
    )
    womens_soccer_athlete_verification_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.md",
        len(womens_soccer_athlete_verification_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.md"],
        context="women's soccer athlete verification queue",
    )
    womens_soccer_athlete_next_actions_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.md",
        len(womens_soccer_athlete_next_actions_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.md"],
        context="women's soccer athlete verification next actions",
    )
    womens_soccer_athlete_source_priority_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.md",
        len(womens_soccer_athlete_source_priority_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.md"],
        context="women's soccer athlete source priority",
    )
    womens_soccer_athlete_review_triage_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.md",
        len(womens_soccer_athlete_review_triage_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.md"],
        context="women's soccer athlete review triage",
    )
    womens_soccer_athlete_candidate_actions_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md",
        len(womens_soccer_athlete_candidate_actions_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md"],
        context="women's soccer athlete candidate next-action board",
    )
    womens_soccer_athlete_photo_readiness_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md",
        len(womens_soccer_athlete_photo_readiness_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md"],
        context="women's soccer athlete photo review readiness board",
    )
    womens_soccer_athlete_operator_focus_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md",
        len(womens_soccer_athlete_operator_focus_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md"],
        context="women's soccer athlete operator focus",
    )
    womens_soccer_action_photo_research_next_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md",
        len(womens_soccer_action_photo_research_next_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md"],
        context="women's soccer action-photo research next",
    )
    womens_soccer_athlete_closure_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.md",
        len(womens_soccer_athlete_closure_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.md"],
        context="women's soccer athlete expansion closure summary",
    )
    womens_soccer_external_research_cue = packet_freshness_cue(
        "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.md",
        len(womens_soccer_external_research_rows),
        RUN_COMMANDS["data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.md"],
        context="women's soccer external research intake",
    )
    action_photo_research_bundle_steps = as_int(action_photo_research_bundle_manifest.get("bundle_steps")) if isinstance(action_photo_research_bundle_manifest, dict) else 0
    action_photo_research_bundle_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.md",
        action_photo_research_bundle_steps,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.md"],
        context="action-photo research run bundle",
    )
    action_photo_research_return_paste_worksheet_rows = as_int(action_photo_research_return_paste_worksheet_manifest.get("paste_worksheet_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0
    action_photo_research_return_paste_worksheet_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.md",
        action_photo_research_return_paste_worksheet_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.md"],
        context="action-photo research return paste worksheet",
    )
    action_photo_manual_source_hunt_rows = as_int(action_photo_manual_source_hunt_manifest.get("source_hunt_rows")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else 0
    action_photo_manual_source_hunt_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.md",
        action_photo_manual_source_hunt_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.md"],
        context="action-photo manual source-hunt board",
    )
    action_photo_preflight_rows = as_int(action_photo_preflight_manifest.get("preflight_rows")) if isinstance(action_photo_preflight_manifest, dict) else 0
    action_photo_preflight_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md",
        action_photo_preflight_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md"],
        context="action-photo quarantine preflight",
    )
    action_photo_quality_fit_rows = as_int(action_photo_quality_fit_manifest.get("quality_fit_rows")) if isinstance(action_photo_quality_fit_manifest, dict) else 0
    action_photo_quality_fit_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md",
        action_photo_quality_fit_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md"],
        context="action-photo candidate quality/fit board",
    )
    action_photo_quality_fit_operator_cue_rows = as_int(action_photo_quality_fit_operator_cue_manifest.get("operator_cue_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0
    action_photo_quality_fit_operator_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md",
        action_photo_quality_fit_operator_cue_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md"],
        context="action-photo quality/fit operator cue",
    )
    action_photo_hero_target_rows = as_int(action_photo_hero_targets_manifest.get("target_rows")) if isinstance(action_photo_hero_targets_manifest, dict) else 0
    action_photo_hero_targets_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.md",
        action_photo_hero_target_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.md"],
        context="WNBA hero action-photo targets",
    )
    action_photo_cutout_readiness_rows = as_int(action_photo_cutout_readiness_manifest.get("cutout_readiness_rows")) if isinstance(action_photo_cutout_readiness_manifest, dict) else 0
    action_photo_cutout_readiness_cue = packet_freshness_cue(
        "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.md",
        action_photo_cutout_readiness_rows,
        RUN_COMMANDS["data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.md"],
        context="action-photo cutout readiness",
    )
    hockey_softball_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_asset_foundation_report.md",
        len(womens_hockey_logo_rows) + len(womens_hockey_athlete_rows) + len(softball_logo_rows) + len(softball_athlete_rows),
        RUN_COMMANDS["data/asset_registry/hockey_softball_asset_foundation_report.md"],
        context="hockey/softball asset foundation",
    )
    hockey_softball_helper_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_source_review_helper_report.md",
        hockey_softball_helper_summary_rows(hockey_softball_helper_manifest),
        RUN_COMMANDS["data/asset_registry/hockey_softball_source_review_helper_report.md"],
        context="hockey/softball source review helper",
    )
    hockey_softball_coverage_rows = as_int(hockey_softball_coverage_manifest.get("rows")) if isinstance(hockey_softball_coverage_manifest, dict) else 0
    hockey_softball_coverage_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_foundation_coverage_index.md",
        hockey_softball_coverage_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_foundation_coverage_index.md"],
        context="hockey/softball foundation coverage index",
    )
    hockey_softball_workflow_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md",
        hockey_softball_workflow_summary_rows(hockey_softball_workflow_manifest),
        RUN_COMMANDS["data/asset_registry/hockey_softball_asset_workflow_readiness_report.md"],
        context="hockey/softball asset workflow readiness",
    )
    hockey_softball_action_queue_rows = as_int(hockey_softball_action_queue_manifest.get("rows")) if isinstance(hockey_softball_action_queue_manifest, dict) else 0
    hockey_softball_action_queue_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_asset_review_action_queue.md",
        hockey_softball_action_queue_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_asset_review_action_queue.md"],
        context="hockey/softball asset review action queue",
    )
    hockey_softball_batch_source_review_rows = as_int(hockey_softball_batch_source_review_manifest.get("rows")) if isinstance(hockey_softball_batch_source_review_manifest, dict) else 0
    hockey_softball_batch_source_review_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_batch_source_review_helper.md",
        hockey_softball_batch_source_review_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_batch_source_review_helper.md"],
        context="hockey/softball batch source review helper",
    )
    hockey_softball_next_decision_rows = as_int(hockey_softball_next_decision_manifest.get("rows")) if isinstance(hockey_softball_next_decision_manifest, dict) else 0
    hockey_softball_next_decision_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_next_decision_worksheet.md",
        hockey_softball_next_decision_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_next_decision_worksheet.md"],
        context="hockey/softball next decision worksheet",
    )
    hockey_softball_source_priority_rows = as_int(hockey_softball_source_priority_manifest.get("source_priority_rows")) if isinstance(hockey_softball_source_priority_manifest, dict) else 0
    hockey_softball_source_priority_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_source_priority_worksheet.md",
        hockey_softball_source_priority_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_source_priority_worksheet.md"],
        context="hockey/softball source priority worksheet",
    )
    hockey_softball_source_verification_rows = as_int(hockey_softball_source_verification_manifest.get("rows")) if isinstance(hockey_softball_source_verification_manifest, dict) else 0
    hockey_softball_source_verification_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_source_verification_checklist.md",
        hockey_softball_source_verification_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_source_verification_checklist.md"],
        context="hockey/softball source verification checklist",
    )
    hockey_softball_intake_readiness_groups = as_int(hockey_softball_intake_readiness_manifest.get("groups")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0
    hockey_softball_intake_readiness_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_intake_readiness_summary.md",
        hockey_softball_intake_readiness_groups,
        RUN_COMMANDS["data/asset_registry/hockey_softball_intake_readiness_summary.md"],
        context="hockey/softball intake readiness summary",
    )
    hockey_softball_source_map_rows = as_int(hockey_softball_source_map_manifest.get("rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0
    hockey_softball_source_map_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_source_map_board.md",
        hockey_softball_source_map_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_source_map_board.md"],
        context="hockey/softball source map board",
    )
    hockey_softball_action_photo_handoff_rows = as_int(hockey_softball_action_photo_handoff_manifest.get("rows")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else 0
    hockey_softball_action_photo_handoff_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_action_photo_research_handoff.md",
        hockey_softball_action_photo_handoff_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_action_photo_research_handoff.md"],
        context="hockey/softball action-photo research handoff",
    )
    hockey_softball_source_research_return_rows = as_int(hockey_softball_source_research_return_manifest.get("rows")) if isinstance(hockey_softball_source_research_return_manifest, dict) else 0
    hockey_softball_source_research_return_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_source_research_return_intake.md",
        hockey_softball_source_research_return_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_source_research_return_intake.md"],
        context="hockey/softball source research return intake",
    )
    hockey_softball_review_triage_rows = as_int(hockey_softball_review_triage_manifest.get("triage_rows")) if isinstance(hockey_softball_review_triage_manifest, dict) else 0
    hockey_softball_review_triage_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_asset_review_triage.md",
        hockey_softball_review_triage_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_asset_review_triage.md"],
        context="hockey/softball asset review triage",
    )
    hockey_softball_asset_readiness_rows = as_int(hockey_softball_asset_readiness_manifest.get("readiness_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0
    hockey_softball_asset_readiness_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_asset_review_readiness_board.md",
        hockey_softball_asset_readiness_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_asset_review_readiness_board.md"],
        context="hockey/softball asset review readiness board",
    )
    hockey_softball_manual_focus_rows = as_int(hockey_softball_manual_focus_manifest.get("rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0
    hockey_softball_manual_focus_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_manual_verification_focus.md",
        hockey_softball_manual_focus_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_manual_verification_focus.md"],
        context="hockey/softball manual verification focus",
    )
    hockey_softball_next_action_card_rows = as_int(hockey_softball_next_action_cards_manifest.get("rows")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else 0
    hockey_softball_next_action_cards_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_asset_next_action_cards.md",
        hockey_softball_next_action_card_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_asset_next_action_cards.md"],
        context="hockey/softball asset next-action cards",
    )
    hockey_softball_quarantine_download_rows = as_int(hockey_softball_quarantine_download_manifest.get("rows")) if isinstance(hockey_softball_quarantine_download_manifest, dict) else 0
    hockey_softball_quarantine_download_cue = packet_freshness_cue(
        "data/asset_registry/hockey_softball_quarantine_download_intake.md",
        hockey_softball_quarantine_download_rows,
        RUN_COMMANDS["data/asset_registry/hockey_softball_quarantine_download_intake.md"],
        context="hockey/softball quarantine download intake",
    )
    womens_hockey_workflow_summary = hockey_softball_workflow_sport_summary(hockey_softball_workflow_manifest, "womens_hockey")
    softball_workflow_summary = hockey_softball_workflow_sport_summary(hockey_softball_workflow_manifest, "softball")
    logo_packets = logo_review_packet_rows(logo_packet_rows)
    logo_packet_cue = packet_freshness_cue(
        "data/asset_registry/wnba/logo_review_packets.csv",
        len(logo_packet_rows),
        RUN_COMMANDS["data/asset_registry/wnba/logo_review_packets.csv"],
        context="WNBA logo review",
    )
    findings = audit.get("findings") if isinstance(audit.get("findings"), list) else []
    severity_counts = audit.get("severity_counts") if isinstance(audit.get("severity_counts"), dict) else {}
    domain_counts = audit.get("asset_domain_counts") if isinstance(audit.get("asset_domain_counts"), dict) else {}
    finding_counts = audit.get("finding_counts") if isinstance(audit.get("finding_counts"), dict) else {}
    policy = audit.get("policy") if isinstance(audit.get("policy"), dict) else {}
    top_findings = top_asset_audit_findings(findings)
    audit_exists = find_existing_input("data/asset_registry/asset_availability_audit.json").exists()
    status = clean(audit.get("status")) if audit_exists else "not_run"
    next_step = "Run .\\hsd.cmd run -Mode asset-audit before trusting athlete photos, team logos, league marks, or renderer fallbacks."
    if top_findings:
        first = top_findings[0]
        next_step = f"{first.get('decision')}: {first.get('manual_action')}"
    elif status in {"pass", "passed"}:
        next_step = "No asset availability blockers found in the latest audit; still keep manual visual review before any next step."
    return {
        "panel_status": status,
        "generated_at_utc": clean(audit.get("generated_at_utc")),
        "finding_count": as_int(audit.get("finding_count")),
        "error_count": as_int(severity_counts.get("error")),
        "warning_count": as_int(severity_counts.get("warning")),
        "info_count": as_int(severity_counts.get("info")),
        "player_photo_findings": as_int(domain_counts.get("player_photo")),
        "team_logo_findings": as_int(domain_counts.get("team_logo")),
        "league_logo_findings": as_int(domain_counts.get("league_logo")),
        "renderer_findings": as_int(domain_counts.get("renderer")),
        "default_player_approval_findings": as_int(finding_counts.get("suspicious_or_default_player_approval")),
        "missing_player_asset_findings": as_int(finding_counts.get("missing_local_player_asset")),
        "team_logo_hold_findings": as_int(finding_counts.get("logo_present_without_complete_approval")) + as_int(finding_counts.get("suspicious_logo_source_or_approval")),
        "league_mark_hold_findings": as_int(finding_counts.get("missing_or_unregistered_logo_asset")),
        "renderer_fallback_findings": (
            as_int(finding_counts.get("renderer_active_logo_fallback"))
            + as_int(finding_counts.get("renderer_logo_audit_missing"))
            + as_int(finding_counts.get("renderer_hsd_team_badge_review"))
            + as_int(finding_counts.get("renderer_team_spotlight_fallback_review"))
            + as_int(finding_counts.get("renderer_fixture_reference_asset_review"))
        ),
        "logo_review_packet_rows": len(logo_packet_rows),
        "logo_review_packet_unapproved_rows": sum(1 for row in logo_packet_rows if "unapproved" in clean(row.get("issue_type")).lower()),
        "logo_review_packet_source_drift_rows": sum(1 for row in logo_packet_rows if "source" in clean(row.get("issue_type")).lower() or "drift" in clean(row.get("issue_type")).lower()),
        "logo_review_packet_freshness_status": logo_packet_cue["status"],
        "logo_review_packet_freshness_detail": logo_packet_cue["detail"],
        "logo_review_packet_refresh_command": logo_packet_cue["run_command"],
        "logo_contact_sheet_status": clean(logo_contact_manifest.get("status")) if isinstance(logo_contact_manifest, dict) else "",
        "logo_contact_sheet_rows": len(logo_contact_rows),
        "logo_contact_sheet_freshness_status": logo_contact_cue["status"],
        "logo_contact_sheet_freshness_detail": logo_contact_cue["detail"],
        "logo_contact_sheet_refresh_command": logo_contact_cue["run_command"],
        "womens_soccer_logo_contact_sheet_status": clean(womens_soccer_logo_contact_manifest.get("status")) if isinstance(womens_soccer_logo_contact_manifest, dict) else "",
        "womens_soccer_logo_contact_sheet_rows": len(womens_soccer_logo_contact_rows),
        "womens_soccer_logo_contact_sheet_freshness_status": womens_soccer_logo_contact_cue["status"],
        "womens_soccer_logo_contact_sheet_freshness_detail": womens_soccer_logo_contact_cue["detail"],
        "womens_soccer_logo_contact_sheet_refresh_command": womens_soccer_logo_contact_cue["run_command"],
        "womens_soccer_logo_review_walkthrough_status": clean(womens_soccer_logo_walkthrough_manifest.get("status")) if isinstance(womens_soccer_logo_walkthrough_manifest, dict) else "",
        "womens_soccer_logo_review_walkthrough_rows": len(womens_soccer_logo_walkthrough_rows),
        "womens_soccer_logo_review_walkthrough_freshness_status": womens_soccer_logo_walkthrough_cue["status"],
        "womens_soccer_logo_review_walkthrough_freshness_detail": womens_soccer_logo_walkthrough_cue["detail"],
        "womens_soccer_logo_review_walkthrough_refresh_command": womens_soccer_logo_walkthrough_cue["run_command"],
        "womens_soccer_athlete_photo_contact_sheet_status": clean(womens_soccer_athlete_manifest.get("status")) if isinstance(womens_soccer_athlete_manifest, dict) else "",
        "womens_soccer_athlete_photo_contact_sheet_rows": len(womens_soccer_athlete_rows),
        "womens_soccer_athlete_photo_contact_sheet_team_boards": as_int(womens_soccer_athlete_manifest.get("team_boards")) if isinstance(womens_soccer_athlete_manifest, dict) else 0,
        "womens_soccer_athlete_photo_starter_candidate_rows": as_int(womens_soccer_athlete_manifest.get("starter_candidate_rows")) if isinstance(womens_soccer_athlete_manifest, dict) else 0,
        "womens_soccer_athlete_photo_contact_sheet_generated_at": clean(womens_soccer_athlete_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_manifest, dict) else "",
        "womens_soccer_athlete_photo_contact_sheet_warning_count": len(womens_soccer_athlete_manifest.get("warnings", [])) if isinstance(womens_soccer_athlete_manifest, dict) and isinstance(womens_soccer_athlete_manifest.get("warnings"), list) else 0,
        "womens_soccer_athlete_photo_official_roster_candidate_rows": as_int(womens_soccer_athlete_manifest.get("official_roster_candidate_rows")) if isinstance(womens_soccer_athlete_manifest, dict) else sum(1 for row in womens_soccer_athlete_rows if clean(row.get("candidate_status")) == "official_roster_source_candidate"),
        "womens_soccer_athlete_photo_local_candidate_files_present": as_int(womens_soccer_athlete_manifest.get("local_candidate_files_present")) if isinstance(womens_soccer_athlete_manifest, dict) else sum(1 for row in womens_soccer_athlete_rows if clean(row.get("local_candidate_exists")) == "true"),
        "womens_soccer_athlete_photo_contact_sheet_freshness_status": womens_soccer_athlete_cue["status"],
        "womens_soccer_athlete_photo_contact_sheet_freshness_detail": womens_soccer_athlete_cue["detail"],
        "womens_soccer_athlete_photo_contact_sheet_refresh_command": womens_soccer_athlete_cue["run_command"],
        "womens_soccer_athlete_operator_board_status": clean(womens_soccer_athlete_operator_manifest.get("status")) if isinstance(womens_soccer_athlete_operator_manifest, dict) else "",
        "womens_soccer_athlete_operator_board_rows": len(womens_soccer_athlete_operator_rows),
        "womens_soccer_athlete_operator_board_generated_at": clean(womens_soccer_athlete_operator_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_operator_manifest, dict) else "",
        "womens_soccer_athlete_operator_board_official_roster_candidate_rows": as_int(womens_soccer_athlete_operator_manifest.get("official_roster_candidate_rows")) if isinstance(womens_soccer_athlete_operator_manifest, dict) else 0,
        "womens_soccer_athlete_operator_board_starter_candidate_rows": as_int(womens_soccer_athlete_operator_manifest.get("starter_candidate_rows")) if isinstance(womens_soccer_athlete_operator_manifest, dict) else 0,
        "womens_soccer_athlete_operator_board_local_candidate_files_present": as_int(womens_soccer_athlete_operator_manifest.get("local_candidate_files_present")) if isinstance(womens_soccer_athlete_operator_manifest, dict) else 0,
        "womens_soccer_athlete_operator_board_freshness_status": womens_soccer_athlete_operator_cue["status"],
        "womens_soccer_athlete_operator_board_freshness_detail": womens_soccer_athlete_operator_cue["detail"],
        "womens_soccer_athlete_operator_board_refresh_command": womens_soccer_athlete_operator_cue["run_command"],
        "womens_soccer_athlete_download_intake_status": clean(womens_soccer_athlete_download_manifest.get("status")) if isinstance(womens_soccer_athlete_download_manifest, dict) else "",
        "womens_soccer_athlete_download_intake_rows": len(womens_soccer_athlete_download_rows),
        "womens_soccer_athlete_download_approved_yes_rows": as_int(womens_soccer_athlete_download_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_download_manifest, dict) else sum(1 for row in womens_soccer_athlete_download_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_download_intake_generated_at": clean(womens_soccer_athlete_download_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_download_manifest, dict) else "",
        "womens_soccer_athlete_download_intake_freshness_status": womens_soccer_athlete_download_cue["status"],
        "womens_soccer_athlete_download_intake_freshness_detail": womens_soccer_athlete_download_cue["detail"],
        "womens_soccer_athlete_download_intake_refresh_command": womens_soccer_athlete_download_cue["run_command"],
        "womens_soccer_athlete_verification_queue_status": clean(womens_soccer_athlete_verification_manifest.get("status")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else "",
        "womens_soccer_athlete_verification_queue_rows": len(womens_soccer_athlete_verification_rows),
        "womens_soccer_athlete_verification_queue_nwsl_rows": as_int(womens_soccer_athlete_verification_manifest.get("nwsl_team_rows")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else sum(1 for row in womens_soccer_athlete_verification_rows if clean(row.get("scope_id")) == "nwsl"),
        "womens_soccer_athlete_verification_queue_europe_rows": as_int(womens_soccer_athlete_verification_manifest.get("europe_league_rows")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else sum(1 for row in womens_soccer_athlete_verification_rows if clean(row.get("scope_id")) == "europe_top_flight"),
        "womens_soccer_athlete_verification_queue_p0_nwsl_rows": as_int(womens_soccer_athlete_verification_manifest.get("p0_nwsl_roster_verification_rows")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else sum(1 for row in womens_soccer_athlete_verification_rows if clean(row.get("queue_bucket")) == "p0_nwsl_roster_verification_first"),
        "womens_soccer_athlete_verification_queue_gray_area_rows": as_int(womens_soccer_athlete_verification_manifest.get("gray_area_rows")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else sum(as_int(row.get("gray_area_rows")) for row in womens_soccer_athlete_verification_rows),
        "womens_soccer_athlete_verification_queue_missing_local_candidate_rows": as_int(womens_soccer_athlete_verification_manifest.get("missing_local_candidate_rows")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else sum(as_int(row.get("missing_local_candidate_rows")) for row in womens_soccer_athlete_verification_rows),
        "womens_soccer_athlete_verification_queue_generated_at": clean(womens_soccer_athlete_verification_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_verification_manifest, dict) else "",
        "womens_soccer_athlete_verification_queue_freshness_status": womens_soccer_athlete_verification_cue["status"],
        "womens_soccer_athlete_verification_queue_freshness_detail": womens_soccer_athlete_verification_cue["detail"],
        "womens_soccer_athlete_verification_queue_refresh_command": womens_soccer_athlete_verification_cue["run_command"],
        "womens_soccer_athlete_next_actions_status": clean(womens_soccer_athlete_next_actions_manifest.get("status")) if isinstance(womens_soccer_athlete_next_actions_manifest, dict) else "",
        "womens_soccer_athlete_next_actions_rows": len(womens_soccer_athlete_next_actions_rows),
        "womens_soccer_athlete_next_actions_download_approved_yes_rows": as_int(womens_soccer_athlete_next_actions_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_next_actions_manifest, dict) else sum(1 for row in womens_soccer_athlete_next_actions_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_next_actions_blank_source_url_rows": as_int(womens_soccer_athlete_next_actions_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_next_actions_manifest, dict) else sum(1 for row in womens_soccer_athlete_next_actions_rows if not clean(row.get("source_url"))),
        "womens_soccer_athlete_next_actions_generated_at": clean(womens_soccer_athlete_next_actions_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_next_actions_manifest, dict) else "",
        "womens_soccer_athlete_next_actions_freshness_status": womens_soccer_athlete_next_actions_cue["status"],
        "womens_soccer_athlete_next_actions_freshness_detail": womens_soccer_athlete_next_actions_cue["detail"],
        "womens_soccer_athlete_next_actions_refresh_command": womens_soccer_athlete_next_actions_cue["run_command"],
        "womens_soccer_athlete_source_priority_status": clean(womens_soccer_athlete_source_priority_manifest.get("status")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else "",
        "womens_soccer_athlete_source_priority_rows": len(womens_soccer_athlete_source_priority_rows),
        "womens_soccer_athlete_source_priority_nwsl_rows": as_int(womens_soccer_athlete_source_priority_manifest.get("nwsl_source_rows")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else sum(1 for row in womens_soccer_athlete_source_priority_rows if clean(row.get("scope_id")) == "nwsl"),
        "womens_soccer_athlete_source_priority_europe_rows": as_int(womens_soccer_athlete_source_priority_manifest.get("europe_source_rows")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else sum(1 for row in womens_soccer_athlete_source_priority_rows if clean(row.get("scope_id")) == "europe_top_flight"),
        "womens_soccer_athlete_source_priority_verify_rows": as_int(womens_soccer_athlete_source_priority_manifest.get("operator_verify_required_rows")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else sum(1 for row in womens_soccer_athlete_source_priority_rows if clean(row.get("operator_verify_required")).lower() == "yes"),
        "womens_soccer_athlete_source_priority_gray_rows": as_int(womens_soccer_athlete_source_priority_manifest.get("gray_or_reputable_manual_verify_rows")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else sum(1 for row in womens_soccer_athlete_source_priority_rows if clean(row.get("source_review_bucket")) == "2_gray_area_or_reputable_manual_verify"),
        "womens_soccer_athlete_source_priority_download_approved_yes_rows": as_int(womens_soccer_athlete_source_priority_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else sum(1 for row in womens_soccer_athlete_source_priority_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_source_priority_blank_source_url_rows": as_int(womens_soccer_athlete_source_priority_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else sum(1 for row in womens_soccer_athlete_source_priority_rows if not clean(row.get("source_url"))),
        "womens_soccer_athlete_source_priority_generated_at": clean(womens_soccer_athlete_source_priority_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_source_priority_manifest, dict) else "",
        "womens_soccer_athlete_source_priority_freshness_status": womens_soccer_athlete_source_priority_cue["status"],
        "womens_soccer_athlete_source_priority_freshness_detail": womens_soccer_athlete_source_priority_cue["detail"],
        "womens_soccer_athlete_source_priority_refresh_command": womens_soccer_athlete_source_priority_cue["run_command"],
        "womens_soccer_athlete_review_triage_status": clean(womens_soccer_athlete_review_triage_manifest.get("status")) if isinstance(womens_soccer_athlete_review_triage_manifest, dict) else "",
        "womens_soccer_athlete_review_triage_rows": len(womens_soccer_athlete_review_triage_rows),
        "womens_soccer_athlete_review_triage_nwsl_rows": as_int(womens_soccer_athlete_review_triage_manifest.get("nwsl_rows")) if isinstance(womens_soccer_athlete_review_triage_manifest, dict) else sum(1 for row in womens_soccer_athlete_review_triage_rows if clean(row.get("scope_id")) == "nwsl"),
        "womens_soccer_athlete_review_triage_europe_rows": as_int(womens_soccer_athlete_review_triage_manifest.get("europe_rows")) if isinstance(womens_soccer_athlete_review_triage_manifest, dict) else sum(1 for row in womens_soccer_athlete_review_triage_rows if clean(row.get("scope_id")) == "europe_top_flight"),
        "womens_soccer_athlete_review_triage_download_approved_yes_rows": as_int(womens_soccer_athlete_review_triage_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_review_triage_manifest, dict) else sum(1 for row in womens_soccer_athlete_review_triage_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_review_triage_blank_source_url_rows": as_int(womens_soccer_athlete_review_triage_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_review_triage_manifest, dict) else sum(1 for row in womens_soccer_athlete_review_triage_rows if not clean(row.get("source_url"))),
        "womens_soccer_athlete_review_triage_generated_at": clean(womens_soccer_athlete_review_triage_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_review_triage_manifest, dict) else "",
        "womens_soccer_athlete_review_triage_freshness_status": womens_soccer_athlete_review_triage_cue["status"],
        "womens_soccer_athlete_review_triage_freshness_detail": womens_soccer_athlete_review_triage_cue["detail"],
        "womens_soccer_athlete_review_triage_refresh_command": womens_soccer_athlete_review_triage_cue["run_command"],
        "womens_soccer_athlete_candidate_actions_status": clean(womens_soccer_athlete_candidate_actions_manifest.get("status")) if isinstance(womens_soccer_athlete_candidate_actions_manifest, dict) else "",
        "womens_soccer_athlete_candidate_actions_rows": len(womens_soccer_athlete_candidate_actions_rows),
        "womens_soccer_athlete_candidate_actions_nwsl_rows": as_int(womens_soccer_athlete_candidate_actions_manifest.get("nwsl_rows")) if isinstance(womens_soccer_athlete_candidate_actions_manifest, dict) else sum(1 for row in womens_soccer_athlete_candidate_actions_rows if clean(row.get("scope_id")) == "nwsl"),
        "womens_soccer_athlete_candidate_actions_europe_rows": as_int(womens_soccer_athlete_candidate_actions_manifest.get("europe_rows")) if isinstance(womens_soccer_athlete_candidate_actions_manifest, dict) else sum(1 for row in womens_soccer_athlete_candidate_actions_rows if clean(row.get("scope_id")) == "europe_top_flight"),
        "womens_soccer_athlete_candidate_actions_download_approved_yes_rows": as_int(womens_soccer_athlete_candidate_actions_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_candidate_actions_manifest, dict) else sum(1 for row in womens_soccer_athlete_candidate_actions_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_candidate_actions_blank_source_url_rows": as_int(womens_soccer_athlete_candidate_actions_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_candidate_actions_manifest, dict) else sum(1 for row in womens_soccer_athlete_candidate_actions_rows if not clean(row.get("source_url"))),
        "womens_soccer_athlete_candidate_actions_generated_at": clean(womens_soccer_athlete_candidate_actions_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_candidate_actions_manifest, dict) else "",
        "womens_soccer_athlete_candidate_actions_freshness_status": womens_soccer_athlete_candidate_actions_cue["status"],
        "womens_soccer_athlete_candidate_actions_freshness_detail": womens_soccer_athlete_candidate_actions_cue["detail"],
        "womens_soccer_athlete_candidate_actions_refresh_command": womens_soccer_athlete_candidate_actions_cue["run_command"],
        "womens_soccer_athlete_photo_readiness_status": clean(womens_soccer_athlete_photo_readiness_manifest.get("status")) if isinstance(womens_soccer_athlete_photo_readiness_manifest, dict) else "",
        "womens_soccer_athlete_photo_readiness_rows": len(womens_soccer_athlete_photo_readiness_rows),
        "womens_soccer_athlete_photo_readiness_nwsl_rows": as_int(womens_soccer_athlete_photo_readiness_manifest.get("nwsl_rows")) if isinstance(womens_soccer_athlete_photo_readiness_manifest, dict) else sum(1 for row in womens_soccer_athlete_photo_readiness_rows if clean(row.get("scope_id")) == "nwsl"),
        "womens_soccer_athlete_photo_readiness_europe_rows": as_int(womens_soccer_athlete_photo_readiness_manifest.get("europe_rows")) if isinstance(womens_soccer_athlete_photo_readiness_manifest, dict) else sum(1 for row in womens_soccer_athlete_photo_readiness_rows if clean(row.get("scope_id")) == "europe_top_flight"),
        "womens_soccer_athlete_photo_readiness_download_approved_yes_rows": as_int(womens_soccer_athlete_photo_readiness_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_photo_readiness_manifest, dict) else sum(1 for row in womens_soccer_athlete_photo_readiness_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_photo_readiness_blank_source_url_rows": as_int(womens_soccer_athlete_photo_readiness_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_photo_readiness_manifest, dict) else sum(1 for row in womens_soccer_athlete_photo_readiness_rows if not clean(row.get("source_url"))),
        "womens_soccer_athlete_photo_readiness_generated_at": clean(womens_soccer_athlete_photo_readiness_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_photo_readiness_manifest, dict) else "",
        "womens_soccer_athlete_photo_readiness_freshness_status": womens_soccer_athlete_photo_readiness_cue["status"],
        "womens_soccer_athlete_photo_readiness_freshness_detail": womens_soccer_athlete_photo_readiness_cue["detail"],
        "womens_soccer_athlete_photo_readiness_refresh_command": womens_soccer_athlete_photo_readiness_cue["run_command"],
        "womens_soccer_athlete_operator_focus_status": clean(womens_soccer_athlete_operator_focus_manifest.get("status")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else "",
        "womens_soccer_athlete_operator_focus_rows": len(womens_soccer_athlete_operator_focus_rows),
        "womens_soccer_athlete_operator_focus_p0_rows": as_int(womens_soccer_athlete_operator_focus_manifest.get("p0_rows")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else sum(1 for row in womens_soccer_athlete_operator_focus_rows if "p0_source_or_roster_row" in clean(row.get("focus_reason_flags")).split("|")),
        "womens_soccer_athlete_operator_focus_identity_manual_verification_rows": as_int(womens_soccer_athlete_operator_focus_manifest.get("identity_manual_verification_rows")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else sum(1 for row in womens_soccer_athlete_operator_focus_rows if "manual_verification_required" in clean(row.get("identity_verification_status")) or "conflict_requires_manual_resolution" in clean(row.get("identity_verification_status"))),
        "womens_soccer_athlete_operator_focus_blank_official_profile_url_rows": as_int(womens_soccer_athlete_operator_focus_manifest.get("blank_official_profile_url_rows")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else sum(1 for row in womens_soccer_athlete_operator_focus_rows if not clean(row.get("official_profile_url"))),
        "womens_soccer_athlete_operator_focus_action_photo_no_selected_candidate_rows": as_int(womens_soccer_athlete_operator_focus_manifest.get("action_photo_no_selected_candidate_rows")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else sum(1 for row in womens_soccer_athlete_operator_focus_rows if "no_candidate_selected" in clean(row.get("action_photo_candidate_status")) or "no_action_photo_selection" in clean(row.get("action_photo_candidate_status"))),
        "womens_soccer_athlete_operator_focus_download_approved_yes_rows": as_int(womens_soccer_athlete_operator_focus_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else sum(1 for row in womens_soccer_athlete_operator_focus_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_athlete_operator_focus_blank_source_url_rows": as_int(womens_soccer_athlete_operator_focus_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else sum(1 for row in womens_soccer_athlete_operator_focus_rows if not clean(row.get("source_url"))),
        "womens_soccer_athlete_operator_focus_generated_at": clean(womens_soccer_athlete_operator_focus_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_operator_focus_manifest, dict) else "",
        "womens_soccer_athlete_operator_focus_freshness_status": womens_soccer_athlete_operator_focus_cue["status"],
        "womens_soccer_athlete_operator_focus_freshness_detail": womens_soccer_athlete_operator_focus_cue["detail"],
        "womens_soccer_athlete_operator_focus_refresh_command": womens_soccer_athlete_operator_focus_cue["run_command"],
        "womens_soccer_action_photo_research_next_status": clean(womens_soccer_action_photo_research_next_manifest.get("status")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else "",
        "womens_soccer_action_photo_research_next_rows": as_int(womens_soccer_action_photo_research_next_manifest.get("research_next_rows")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else len(womens_soccer_action_photo_research_next_rows),
        "womens_soccer_action_photo_research_next_validation_issues": as_int(womens_soccer_action_photo_research_next_manifest.get("validation_issue_count")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else 0,
        "womens_soccer_action_photo_research_next_download_approved_yes_rows": as_int(womens_soccer_action_photo_research_next_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else sum(1 for row in womens_soccer_action_photo_research_next_rows if clean(row.get("download_approved")).lower() == "yes"),
        "womens_soccer_action_photo_research_next_candidate_ready_rows": as_int(womens_soccer_action_photo_research_next_manifest.get("candidate_ready_for_later_human_download_decision_review_rows")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else sum(1 for row in womens_soccer_action_photo_research_next_rows if clean(row.get("candidate_ready_for_later_human_download_decision_review")).lower() == "yes"),
        "womens_soccer_action_photo_research_next_blank_source_url_rows": as_int(womens_soccer_action_photo_research_next_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else sum(1 for row in womens_soccer_action_photo_research_next_rows if not clean(row.get("source_url"))),
        "womens_soccer_action_photo_research_next_blank_rights_class_rows": as_int(womens_soccer_action_photo_research_next_manifest.get("blank_rights_class_rows")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else sum(1 for row in womens_soccer_action_photo_research_next_rows if not clean(row.get("rights_class"))),
        "womens_soccer_action_photo_research_next_blank_identity_confidence_rows": as_int(womens_soccer_action_photo_research_next_manifest.get("blank_identity_confidence_rows")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else sum(1 for row in womens_soccer_action_photo_research_next_rows if not clean(row.get("identity_confidence"))),
        "womens_soccer_action_photo_research_next_generated_at": clean(womens_soccer_action_photo_research_next_manifest.get("generated_at_utc")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else "",
        "womens_soccer_action_photo_research_next_asset_downloads": bool(womens_soccer_action_photo_research_next_manifest.get("asset_downloads")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else False,
        "womens_soccer_action_photo_research_next_headshot_writes": bool(womens_soccer_action_photo_research_next_manifest.get("headshot_writes")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else False,
        "womens_soccer_action_photo_research_next_approved_marker_writes": bool(womens_soccer_action_photo_research_next_manifest.get("approved_marker_writes")) if isinstance(womens_soccer_action_photo_research_next_manifest, dict) else False,
        "womens_soccer_action_photo_research_next_freshness_status": womens_soccer_action_photo_research_next_cue["status"],
        "womens_soccer_action_photo_research_next_freshness_detail": womens_soccer_action_photo_research_next_cue["detail"],
        "womens_soccer_action_photo_research_next_refresh_command": womens_soccer_action_photo_research_next_cue["run_command"],
        "womens_soccer_athlete_closure_status": clean(womens_soccer_athlete_closure_manifest.get("status")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else "",
        "womens_soccer_athlete_closure_rows": len(womens_soccer_athlete_closure_rows),
        "womens_soccer_athlete_closure_total_referenced_rows": as_int(womens_soccer_athlete_closure_manifest.get("total_referenced_rows")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else sum(as_int(row.get("row_count")) for row in womens_soccer_athlete_closure_rows),
        "womens_soccer_athlete_closure_p0_or_verify_rows": as_int(womens_soccer_athlete_closure_manifest.get("p0_or_verify_rows")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else sum(as_int(row.get("p0_or_verify_rows")) for row in womens_soccer_athlete_closure_rows),
        "womens_soccer_athlete_closure_gray_area_rows": as_int(womens_soccer_athlete_closure_manifest.get("gray_area_rows")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else sum(as_int(row.get("gray_area_rows")) for row in womens_soccer_athlete_closure_rows),
        "womens_soccer_athlete_closure_blank_source_url_rows": as_int(womens_soccer_athlete_closure_manifest.get("blank_source_url_rows")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else sum(as_int(row.get("blank_source_url_rows")) for row in womens_soccer_athlete_closure_rows),
        "womens_soccer_athlete_closure_download_approved_yes_rows": as_int(womens_soccer_athlete_closure_manifest.get("download_approved_yes_rows")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else sum(as_int(row.get("download_approved_yes_rows")) for row in womens_soccer_athlete_closure_rows),
        "womens_soccer_athlete_closure_generated_at": clean(womens_soccer_athlete_closure_manifest.get("generated_at_utc")) if isinstance(womens_soccer_athlete_closure_manifest, dict) else "",
        "womens_soccer_athlete_closure_freshness_status": womens_soccer_athlete_closure_cue["status"],
        "womens_soccer_athlete_closure_freshness_detail": womens_soccer_athlete_closure_cue["detail"],
        "womens_soccer_athlete_closure_refresh_command": womens_soccer_athlete_closure_cue["run_command"],
        "womens_soccer_external_research_status": clean(womens_soccer_external_research_manifest.get("status")) if isinstance(womens_soccer_external_research_manifest, dict) else "",
        "womens_soccer_external_research_rows": len(womens_soccer_external_research_rows),
        "womens_soccer_external_research_nwsl_rows": as_int(womens_soccer_external_research_manifest.get("nwsl_rows")) if isinstance(womens_soccer_external_research_manifest, dict) else sum(1 for row in womens_soccer_external_research_rows if clean(row.get("research_lane")) == "nwsl_correction_enrichment"),
        "womens_soccer_external_research_europe_rows": as_int(womens_soccer_external_research_manifest.get("europe_rows")) if isinstance(womens_soccer_external_research_manifest, dict) else sum(1 for row in womens_soccer_external_research_rows if clean(row.get("research_lane")) == "europe_official_source_map"),
        "womens_soccer_external_research_p0_nwsl_rows": as_int(womens_soccer_external_research_manifest.get("operator_bucket_counts", {}).get("p0_nwsl_operator_verify_first")) if isinstance(womens_soccer_external_research_manifest, dict) and isinstance(womens_soccer_external_research_manifest.get("operator_bucket_counts"), dict) else sum(1 for row in womens_soccer_external_research_rows if clean(row.get("operator_bucket")) == "p0_nwsl_operator_verify_first"),
        "womens_soccer_external_research_gray_area_rows": as_int(womens_soccer_external_research_manifest.get("gray_area_rows")) if isinstance(womens_soccer_external_research_manifest, dict) else sum(1 for row in womens_soccer_external_research_rows if "gray_area" in clean(row.get("operator_bucket"))),
        "womens_soccer_external_research_sam_kerr_gray_area_only": bool(womens_soccer_external_research_manifest.get("sam_kerr_reuters_gray_area_only")) if isinstance(womens_soccer_external_research_manifest, dict) else False,
        "womens_soccer_external_research_generated_at": clean(womens_soccer_external_research_manifest.get("generated_at_utc")) if isinstance(womens_soccer_external_research_manifest, dict) else "",
        "womens_soccer_external_research_freshness_status": womens_soccer_external_research_cue["status"],
        "womens_soccer_external_research_freshness_detail": womens_soccer_external_research_cue["detail"],
        "womens_soccer_external_research_refresh_command": womens_soccer_external_research_cue["run_command"],
        "action_photo_candidate_intake_status": clean(action_photo_intake_manifest.get("status")) if isinstance(action_photo_intake_manifest, dict) else "",
        "action_photo_candidate_intake_generated_at": clean(action_photo_intake_manifest.get("generated_at_utc")) if isinstance(action_photo_intake_manifest, dict) else "",
        "action_photo_candidate_intake_rows": as_int(action_photo_intake_manifest.get("intake_rows")) if isinstance(action_photo_intake_manifest, dict) else 0,
        "action_photo_candidate_queue_rows": as_int(action_photo_intake_manifest.get("action_photo_candidate_queue_rows")) if isinstance(action_photo_intake_manifest, dict) else 0,
        "action_photo_source_map_board_status": clean(action_photo_source_map_board_manifest.get("status")) if isinstance(action_photo_source_map_board_manifest, dict) else "",
        "action_photo_source_map_board_generated_at": clean(action_photo_source_map_board_manifest.get("generated_at_utc")) if isinstance(action_photo_source_map_board_manifest, dict) else "",
        "action_photo_source_map_board_rows": as_int(action_photo_source_map_board_manifest.get("board_rows")) if isinstance(action_photo_source_map_board_manifest, dict) else 0,
        "action_photo_source_map_board_blank_operator_decision_rows": as_int(action_photo_source_map_board_manifest.get("blank_operator_decision_rows")) if isinstance(action_photo_source_map_board_manifest, dict) else 0,
        "action_photo_source_map_board_blank_source_url_rows": as_int(action_photo_source_map_board_manifest.get("blank_source_url_rows")) if isinstance(action_photo_source_map_board_manifest, dict) else 0,
        "action_photo_source_map_board_download_approved_yes_rows": as_int(action_photo_source_map_board_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_source_map_board_manifest, dict) else 0,
        "action_photo_source_map_board_asset_downloads": bool(action_photo_source_map_board_manifest.get("asset_downloads")) if isinstance(action_photo_source_map_board_manifest, dict) else False,
        "action_photo_source_map_board_source_fetching": bool(action_photo_source_map_board_manifest.get("source_fetching")) if isinstance(action_photo_source_map_board_manifest, dict) else False,
        "action_photo_source_map_board_auto_source_enablement": bool(action_photo_source_map_board_manifest.get("auto_source_enablement")) if isinstance(action_photo_source_map_board_manifest, dict) else False,
        "action_photo_source_map_board_auto_approval": bool(action_photo_source_map_board_manifest.get("auto_approval")) if isinstance(action_photo_source_map_board_manifest, dict) else False,
        "action_photo_manual_source_hunt_status": clean(action_photo_manual_source_hunt_manifest.get("status")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else "",
        "action_photo_manual_source_hunt_generated_at": clean(action_photo_manual_source_hunt_manifest.get("generated_at_utc")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else "",
        "action_photo_manual_source_hunt_rows": action_photo_manual_source_hunt_rows,
        "action_photo_manual_source_hunt_blank_source_url_rows": as_int(action_photo_manual_source_hunt_manifest.get("blank_source_url_rows")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else 0,
        "action_photo_manual_source_hunt_download_approved_yes_rows": as_int(action_photo_manual_source_hunt_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else 0,
        "action_photo_manual_source_hunt_asset_downloads": bool(action_photo_manual_source_hunt_manifest.get("asset_downloads")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else False,
        "action_photo_manual_source_hunt_source_fetching": bool(action_photo_manual_source_hunt_manifest.get("source_fetching")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else False,
        "action_photo_manual_source_hunt_auto_source_enablement": bool(action_photo_manual_source_hunt_manifest.get("auto_source_enablement")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else False,
        "action_photo_manual_source_hunt_auto_approval": bool(action_photo_manual_source_hunt_manifest.get("auto_approval")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else False,
        "action_photo_manual_source_hunt_headshot_writes": bool(action_photo_manual_source_hunt_manifest.get("headshot_writes")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else False,
        "action_photo_manual_source_hunt_approved_marker_writes": bool(action_photo_manual_source_hunt_manifest.get("approved_marker_writes")) if isinstance(action_photo_manual_source_hunt_manifest, dict) else False,
        "action_photo_operator_worksheet_status": clean(action_photo_operator_worksheet_manifest.get("status")) if isinstance(action_photo_operator_worksheet_manifest, dict) else "",
        "action_photo_operator_worksheet_generated_at": clean(action_photo_operator_worksheet_manifest.get("generated_at_utc")) if isinstance(action_photo_operator_worksheet_manifest, dict) else "",
        "action_photo_operator_worksheet_rows": as_int(action_photo_operator_worksheet_manifest.get("worksheet_rows")) if isinstance(action_photo_operator_worksheet_manifest, dict) else 0,
        "action_photo_operator_worksheet_download_approved_yes_rows": as_int(action_photo_operator_worksheet_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_operator_worksheet_manifest, dict) else 0,
        "action_photo_operator_worksheet_blank_candidate_url_rows": as_int(action_photo_operator_worksheet_manifest.get("blank_candidate_url_rows")) if isinstance(action_photo_operator_worksheet_manifest, dict) else 0,
        "action_photo_operator_worksheet_blank_source_url_rows": as_int(action_photo_operator_worksheet_manifest.get("blank_source_url_rows")) if isinstance(action_photo_operator_worksheet_manifest, dict) else 0,
        "action_photo_operator_worksheet_blank_reviewer_decision_rows": as_int(action_photo_operator_worksheet_manifest.get("blank_reviewer_decision_rows")) if isinstance(action_photo_operator_worksheet_manifest, dict) else 0,
        "action_photo_operator_worksheet_not_in_quarantine_rows": as_int(action_photo_operator_worksheet_manifest.get("not_in_quarantine_rows")) if isinstance(action_photo_operator_worksheet_manifest, dict) else 0,
        "action_photo_operator_worksheet_asset_downloads": bool(action_photo_operator_worksheet_manifest.get("asset_downloads")) if isinstance(action_photo_operator_worksheet_manifest, dict) else False,
        "action_photo_operator_worksheet_headshot_writes": bool(action_photo_operator_worksheet_manifest.get("headshot_writes")) if isinstance(action_photo_operator_worksheet_manifest, dict) else False,
        "action_photo_operator_worksheet_approved_marker_writes": bool(action_photo_operator_worksheet_manifest.get("approved_marker_writes")) if isinstance(action_photo_operator_worksheet_manifest, dict) else False,
        "action_photo_research_packet_rows": as_int(action_photo_intake_manifest.get("action_photo_candidate_research_packet_rows")) if isinstance(action_photo_intake_manifest, dict) else 0,
        "action_photo_research_return_intake_rows": as_int(action_photo_intake_manifest.get("action_photo_research_return_intake_rows")) if isinstance(action_photo_intake_manifest, dict) else 0,
        "action_photo_research_return_status": clean(action_photo_research_return_manifest.get("status")) if isinstance(action_photo_research_return_manifest, dict) else "",
        "action_photo_research_return_generated_at": clean(action_photo_research_return_manifest.get("generated_at_utc")) if isinstance(action_photo_research_return_manifest, dict) else "",
        "action_photo_research_return_rows_with_pasted_data": as_int(action_photo_research_return_manifest.get("rows_with_pasted_return_data")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_validation_issues": as_int(action_photo_research_return_manifest.get("validation_issue_count")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_blank_candidate_photo_url_rows": as_int(action_photo_research_return_manifest.get("blank_candidate_photo_url_rows")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_blank_source_url_rows": as_int(action_photo_research_return_manifest.get("blank_source_url_rows")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_blank_rights_class_rows": as_int(action_photo_research_return_manifest.get("blank_rights_class_rows")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_operator_verify_required_yes_rows": as_int(action_photo_research_return_manifest.get("operator_verify_required_yes_rows")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_download_approved_yes_rows": as_int(action_photo_research_return_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_research_return_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_status": clean(action_photo_research_return_paste_worksheet_manifest.get("status")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else "",
        "action_photo_research_return_paste_worksheet_generated_at": clean(action_photo_research_return_paste_worksheet_manifest.get("generated_at_utc")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else "",
        "action_photo_research_return_paste_worksheet_rows": action_photo_research_return_paste_worksheet_rows,
        "action_photo_research_return_paste_worksheet_ready_rows": as_int(action_photo_research_return_paste_worksheet_manifest.get("candidate_ready_for_later_human_download_decision_review_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_blank_candidate_photo_url_rows": as_int(action_photo_research_return_paste_worksheet_manifest.get("blank_candidate_photo_url_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_blank_source_url_rows": as_int(action_photo_research_return_paste_worksheet_manifest.get("blank_source_url_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_blank_rights_class_rows": as_int(action_photo_research_return_paste_worksheet_manifest.get("blank_rights_class_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_blank_identity_confidence_rows": as_int(action_photo_research_return_paste_worksheet_manifest.get("blank_identity_confidence_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_download_approved_yes_rows": as_int(action_photo_research_return_paste_worksheet_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else 0,
        "action_photo_research_return_paste_worksheet_asset_downloads": bool(action_photo_research_return_paste_worksheet_manifest.get("asset_downloads")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else False,
        "action_photo_research_return_paste_worksheet_headshot_writes": bool(action_photo_research_return_paste_worksheet_manifest.get("headshot_writes")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else False,
        "action_photo_research_return_paste_worksheet_approved_marker_writes": bool(action_photo_research_return_paste_worksheet_manifest.get("approved_marker_writes")) if isinstance(action_photo_research_return_paste_worksheet_manifest, dict) else False,
        "action_photo_research_run_bundle_status": clean(action_photo_research_bundle_manifest.get("status")) if isinstance(action_photo_research_bundle_manifest, dict) else "",
        "action_photo_research_run_bundle_generated_at": clean(action_photo_research_bundle_manifest.get("generated_at_utc")) if isinstance(action_photo_research_bundle_manifest, dict) else "",
        "action_photo_research_run_bundle_rows": action_photo_research_bundle_steps,
        "action_photo_research_run_bundle_download_approved_yes_rows": as_int(action_photo_research_bundle_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_research_bundle_manifest, dict) else 0,
        "action_photo_quarantine_preflight_status": clean(action_photo_preflight_manifest.get("status")) if isinstance(action_photo_preflight_manifest, dict) else "",
        "action_photo_quarantine_preflight_generated_at": clean(action_photo_preflight_manifest.get("generated_at_utc")) if isinstance(action_photo_preflight_manifest, dict) else "",
        "action_photo_quarantine_preflight_rows": action_photo_preflight_rows,
        "action_photo_quarantine_preflight_ready_for_human_download_decision_rows": as_int(action_photo_preflight_manifest.get("ready_for_human_download_decision_rows")) if isinstance(action_photo_preflight_manifest, dict) else 0,
        "action_photo_quarantine_preflight_lead_only_rows": as_int(action_photo_preflight_manifest.get("lead_only_rows")) if isinstance(action_photo_preflight_manifest, dict) else 0,
        "action_photo_quarantine_preflight_download_approved_yes_rows": as_int(action_photo_preflight_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_preflight_manifest, dict) else 0,
        "action_photo_quarantine_preflight_missing_source_url_rows": as_int(action_photo_preflight_manifest.get("missing_required_field_counts", {}).get("source_url")) if isinstance(action_photo_preflight_manifest, dict) and isinstance(action_photo_preflight_manifest.get("missing_required_field_counts"), dict) else 0,
        "action_photo_quality_fit_status": clean(action_photo_quality_fit_manifest.get("status")) if isinstance(action_photo_quality_fit_manifest, dict) else "",
        "action_photo_quality_fit_generated_at": clean(action_photo_quality_fit_manifest.get("generated_at_utc")) if isinstance(action_photo_quality_fit_manifest, dict) else "",
        "action_photo_quality_fit_rows": action_photo_quality_fit_rows,
        "action_photo_quality_fit_source_url_present_rows": as_int(action_photo_quality_fit_manifest.get("source_url_present_rows")) if isinstance(action_photo_quality_fit_manifest, dict) else 0,
        "action_photo_quality_fit_rights_class_present_rows": as_int(action_photo_quality_fit_manifest.get("rights_class_present_rows")) if isinstance(action_photo_quality_fit_manifest, dict) else 0,
        "action_photo_quality_fit_ready_for_human_download_decision_rows": as_int(action_photo_quality_fit_manifest.get("ready_for_human_download_decision_rows")) if isinstance(action_photo_quality_fit_manifest, dict) else 0,
        "action_photo_quality_fit_download_approved_yes_rows": as_int(action_photo_quality_fit_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_quality_fit_manifest, dict) else 0,
        "action_photo_quality_fit_validation_issues": as_int(action_photo_quality_fit_manifest.get("validation_issue_count")) if isinstance(action_photo_quality_fit_manifest, dict) else 0,
        "action_photo_quality_fit_asset_downloads": bool(action_photo_quality_fit_manifest.get("asset_downloads")) if isinstance(action_photo_quality_fit_manifest, dict) else False,
        "action_photo_quality_fit_headshot_writes": bool(action_photo_quality_fit_manifest.get("headshot_writes")) if isinstance(action_photo_quality_fit_manifest, dict) else False,
        "action_photo_quality_fit_approved_marker_writes": bool(action_photo_quality_fit_manifest.get("approved_marker_writes")) if isinstance(action_photo_quality_fit_manifest, dict) else False,
        "action_photo_quality_fit_operator_cue_status": clean(action_photo_quality_fit_operator_cue_manifest.get("status")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else "",
        "action_photo_quality_fit_operator_cue_generated_at": clean(action_photo_quality_fit_operator_cue_manifest.get("generated_at_utc")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else "",
        "action_photo_quality_fit_operator_cue_rows": action_photo_quality_fit_operator_cue_rows,
        "action_photo_quality_fit_operator_cue_source_url_missing_rows": as_int(action_photo_quality_fit_operator_cue_manifest.get("source_url_missing_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0,
        "action_photo_quality_fit_operator_cue_rights_class_missing_rows": as_int(action_photo_quality_fit_operator_cue_manifest.get("rights_class_missing_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0,
        "action_photo_quality_fit_operator_cue_identity_metadata_missing_rows": as_int(action_photo_quality_fit_operator_cue_manifest.get("identity_metadata_missing_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0,
        "action_photo_quality_fit_operator_cue_action_metadata_missing_rows": as_int(action_photo_quality_fit_operator_cue_manifest.get("action_metadata_missing_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0,
        "action_photo_quality_fit_operator_cue_crop_metadata_missing_rows": as_int(action_photo_quality_fit_operator_cue_manifest.get("crop_metadata_missing_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0,
        "action_photo_quality_fit_operator_cue_eligible_rows": as_int(action_photo_quality_fit_operator_cue_manifest.get("download_decision_review_eligible_rows")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else 0,
        "action_photo_quality_fit_operator_cue_asset_downloads": bool(action_photo_quality_fit_operator_cue_manifest.get("asset_downloads")) if isinstance(action_photo_quality_fit_operator_cue_manifest, dict) else False,
        "action_photo_download_decision_status": clean(action_photo_download_decision_manifest.get("status")) if isinstance(action_photo_download_decision_manifest, dict) else "",
        "action_photo_download_decision_generated_at": clean(action_photo_download_decision_manifest.get("generated_at_utc")) if isinstance(action_photo_download_decision_manifest, dict) else "",
        "action_photo_download_decision_rows": as_int(action_photo_download_decision_manifest.get("decision_rows")) if isinstance(action_photo_download_decision_manifest, dict) else 0,
        "action_photo_download_decision_ready_rows": as_int(action_photo_download_decision_manifest.get("ready_for_human_download_decision_rows")) if isinstance(action_photo_download_decision_manifest, dict) else 0,
        "action_photo_download_decision_download_approved_yes_rows": as_int(action_photo_download_decision_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_download_decision_manifest, dict) else 0,
        "action_photo_download_decision_blank_human_rows": as_int(action_photo_download_decision_manifest.get("blank_human_download_decision_rows")) if isinstance(action_photo_download_decision_manifest, dict) else 0,
        "action_photo_download_decision_asset_downloads": bool(action_photo_download_decision_manifest.get("asset_downloads")) if isinstance(action_photo_download_decision_manifest, dict) else False,
        "action_photo_download_decision_approved_marker_writes": bool(action_photo_download_decision_manifest.get("approved_marker_writes")) if isinstance(action_photo_download_decision_manifest, dict) else False,
        "action_photo_hero_targets_status": clean(action_photo_hero_targets_manifest.get("status")) if isinstance(action_photo_hero_targets_manifest, dict) else "",
        "action_photo_hero_targets_generated_at": clean(action_photo_hero_targets_manifest.get("generated_at_utc")) if isinstance(action_photo_hero_targets_manifest, dict) else "",
        "action_photo_hero_targets_rows": action_photo_hero_target_rows,
        "action_photo_hero_targets_download_approved_yes_rows": as_int(action_photo_hero_targets_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_hero_targets_manifest, dict) else 0,
        "action_photo_hero_targets_blank_source_url_rows": as_int(action_photo_hero_targets_manifest.get("blank_source_url_rows")) if isinstance(action_photo_hero_targets_manifest, dict) else 0,
        "action_photo_hero_targets_blank_candidate_photo_url_rows": as_int(action_photo_hero_targets_manifest.get("blank_candidate_photo_url_rows")) if isinstance(action_photo_hero_targets_manifest, dict) else 0,
        "action_photo_hero_targets_operator_verify_required_yes_rows": as_int(action_photo_hero_targets_manifest.get("operator_verify_required_yes_rows")) if isinstance(action_photo_hero_targets_manifest, dict) else 0,
        "action_photo_cutout_readiness_status": clean(action_photo_cutout_readiness_manifest.get("status")) if isinstance(action_photo_cutout_readiness_manifest, dict) else "",
        "action_photo_cutout_readiness_generated_at": clean(action_photo_cutout_readiness_manifest.get("generated_at_utc")) if isinstance(action_photo_cutout_readiness_manifest, dict) else "",
        "action_photo_cutout_readiness_rows": action_photo_cutout_readiness_rows,
        "action_photo_cutout_readiness_download_approved_yes_rows": as_int(action_photo_cutout_readiness_manifest.get("download_approved_yes_rows")) if isinstance(action_photo_cutout_readiness_manifest, dict) else 0,
        "action_photo_cutout_readiness_blank_source_url_rows": as_int(action_photo_cutout_readiness_manifest.get("blank_source_url_rows")) if isinstance(action_photo_cutout_readiness_manifest, dict) else 0,
        "action_photo_cutout_readiness_blank_candidate_photo_url_rows": as_int(action_photo_cutout_readiness_manifest.get("blank_candidate_photo_url_rows")) if isinstance(action_photo_cutout_readiness_manifest, dict) else 0,
        "action_photo_cutout_readiness_blank_cutout_work_required_rows": as_int(action_photo_cutout_readiness_manifest.get("blank_cutout_work_required_rows")) if isinstance(action_photo_cutout_readiness_manifest, dict) else 0,
        "action_photo_cutout_readiness_blank_transparent_background_rows": as_int(action_photo_cutout_readiness_manifest.get("blank_transparent_background_candidate_rows")) if isinstance(action_photo_cutout_readiness_manifest, dict) else 0,
        "action_photo_cutout_readiness_segmentation": bool(action_photo_cutout_readiness_manifest.get("segmentation")) if isinstance(action_photo_cutout_readiness_manifest, dict) else False,
        "action_photo_cutout_readiness_background_removal": bool(action_photo_cutout_readiness_manifest.get("background_removal")) if isinstance(action_photo_cutout_readiness_manifest, dict) else False,
        "action_photo_cutout_readiness_cutout_file_writes": bool(action_photo_cutout_readiness_manifest.get("cutout_file_writes")) if isinstance(action_photo_cutout_readiness_manifest, dict) else False,
        "action_photo_research_run_bundle_freshness_status": action_photo_research_bundle_cue["status"],
        "action_photo_research_run_bundle_freshness_detail": action_photo_research_bundle_cue["detail"],
        "action_photo_research_run_bundle_refresh_command": action_photo_research_bundle_cue["run_command"],
        "action_photo_research_return_paste_worksheet_freshness_status": action_photo_research_return_paste_worksheet_cue["status"],
        "action_photo_research_return_paste_worksheet_freshness_detail": action_photo_research_return_paste_worksheet_cue["detail"],
        "action_photo_research_return_paste_worksheet_refresh_command": action_photo_research_return_paste_worksheet_cue["run_command"],
        "action_photo_manual_source_hunt_freshness_status": action_photo_manual_source_hunt_cue["status"],
        "action_photo_manual_source_hunt_freshness_detail": action_photo_manual_source_hunt_cue["detail"],
        "action_photo_manual_source_hunt_refresh_command": action_photo_manual_source_hunt_cue["run_command"],
        "action_photo_quarantine_preflight_freshness_status": action_photo_preflight_cue["status"],
        "action_photo_quarantine_preflight_freshness_detail": action_photo_preflight_cue["detail"],
        "action_photo_quarantine_preflight_refresh_command": action_photo_preflight_cue["run_command"],
        "action_photo_quality_fit_freshness_status": action_photo_quality_fit_cue["status"],
        "action_photo_quality_fit_freshness_detail": action_photo_quality_fit_cue["detail"],
        "action_photo_quality_fit_refresh_command": action_photo_quality_fit_cue["run_command"],
        "action_photo_quality_fit_operator_cue_freshness_status": action_photo_quality_fit_operator_cue["status"],
        "action_photo_quality_fit_operator_cue_freshness_detail": action_photo_quality_fit_operator_cue["detail"],
        "action_photo_quality_fit_operator_cue_refresh_command": action_photo_quality_fit_operator_cue["run_command"],
        "action_photo_hero_targets_freshness_status": action_photo_hero_targets_cue["status"],
        "action_photo_hero_targets_freshness_detail": action_photo_hero_targets_cue["detail"],
        "action_photo_hero_targets_refresh_command": action_photo_hero_targets_cue["run_command"],
        "action_photo_cutout_readiness_freshness_status": action_photo_cutout_readiness_cue["status"],
        "action_photo_cutout_readiness_freshness_detail": action_photo_cutout_readiness_cue["detail"],
        "action_photo_cutout_readiness_refresh_command": action_photo_cutout_readiness_cue["run_command"],
        "hockey_softball_asset_foundation_status": clean(hockey_softball_manifest.get("status")) if isinstance(hockey_softball_manifest, dict) else "",
        "hockey_softball_asset_foundation_generated_at": clean(hockey_softball_manifest.get("generated_at_utc")) if isinstance(hockey_softball_manifest, dict) else "",
        "hockey_softball_foundation_coverage_status": clean(hockey_softball_coverage_manifest.get("status")) if isinstance(hockey_softball_coverage_manifest, dict) else "",
        "hockey_softball_foundation_coverage_generated_at": clean(hockey_softball_coverage_manifest.get("generated_at_utc")) if isinstance(hockey_softball_coverage_manifest, dict) else "",
        "hockey_softball_foundation_coverage_rows": hockey_softball_coverage_rows,
        "hockey_softball_foundation_coverage_source_rows": as_int(hockey_softball_coverage_manifest.get("source_rows")) if isinstance(hockey_softball_coverage_manifest, dict) else 0,
        "hockey_softball_foundation_coverage_logo_contact_rows": as_int(hockey_softball_coverage_manifest.get("logo_contact_rows")) if isinstance(hockey_softball_coverage_manifest, dict) else 0,
        "hockey_softball_foundation_coverage_athlete_candidate_rows": as_int(hockey_softball_coverage_manifest.get("athlete_candidate_rows")) if isinstance(hockey_softball_coverage_manifest, dict) else 0,
        "hockey_softball_source_review_helper_status": clean(hockey_softball_helper_manifest.get("status")) if isinstance(hockey_softball_helper_manifest, dict) else "",
        "hockey_softball_source_review_helper_generated_at": clean(hockey_softball_helper_manifest.get("generated_at_local")) if isinstance(hockey_softball_helper_manifest, dict) else "",
        "hockey_softball_asset_workflow_status": clean(hockey_softball_workflow_manifest.get("status")) if isinstance(hockey_softball_workflow_manifest, dict) else "",
        "hockey_softball_asset_workflow_generated_at": clean(hockey_softball_workflow_manifest.get("generated_at_utc")) if isinstance(hockey_softball_workflow_manifest, dict) else "",
        "hockey_softball_asset_workflow_rows": hockey_softball_workflow_summary_rows(hockey_softball_workflow_manifest),
        "hockey_softball_asset_review_action_queue_status": clean(hockey_softball_action_queue_manifest.get("status")) if isinstance(hockey_softball_action_queue_manifest, dict) else "",
        "hockey_softball_asset_review_action_queue_generated_at": clean(hockey_softball_action_queue_manifest.get("generated_at_utc")) if isinstance(hockey_softball_action_queue_manifest, dict) else "",
        "hockey_softball_asset_review_action_queue_rows": hockey_softball_action_queue_rows,
        "hockey_softball_asset_review_action_queue_source_candidate_only_rows": as_int(hockey_softball_action_queue_manifest.get("source_candidate_only_rows")) if isinstance(hockey_softball_action_queue_manifest, dict) else 0,
        "hockey_softball_asset_review_action_queue_local_asset_present_rows": as_int(hockey_softball_action_queue_manifest.get("local_asset_present_rows")) if isinstance(hockey_softball_action_queue_manifest, dict) else 0,
        "hockey_softball_batch_source_review_status": clean(hockey_softball_batch_source_review_manifest.get("status")) if isinstance(hockey_softball_batch_source_review_manifest, dict) else "",
        "hockey_softball_batch_source_review_generated_at": clean(hockey_softball_batch_source_review_manifest.get("generated_at_utc")) if isinstance(hockey_softball_batch_source_review_manifest, dict) else "",
        "hockey_softball_batch_source_review_rows": hockey_softball_batch_source_review_rows,
        "hockey_softball_batch_source_review_now_rows": as_int(hockey_softball_batch_source_review_manifest.get("source_review_now_rows")) if isinstance(hockey_softball_batch_source_review_manifest, dict) else 0,
        "hockey_softball_batch_source_review_next_rows": len(hockey_softball_batch_source_review_manifest.get("next_review_rows", [])) if isinstance(hockey_softball_batch_source_review_manifest, dict) and isinstance(hockey_softball_batch_source_review_manifest.get("next_review_rows"), list) else 0,
        "hockey_softball_batch_source_review_local_asset_needed_later_rows": as_int(hockey_softball_batch_source_review_manifest.get("local_asset_needed_later_rows")) if isinstance(hockey_softball_batch_source_review_manifest, dict) else 0,
        "hockey_softball_next_decision_worksheet_status": clean(hockey_softball_next_decision_manifest.get("status")) if isinstance(hockey_softball_next_decision_manifest, dict) else "",
        "hockey_softball_next_decision_worksheet_generated_at": clean(hockey_softball_next_decision_manifest.get("generated_at_utc")) if isinstance(hockey_softball_next_decision_manifest, dict) else "",
        "hockey_softball_next_decision_worksheet_rows": hockey_softball_next_decision_rows,
        "hockey_softball_next_decision_worksheet_logo_rows": as_int(hockey_softball_next_decision_manifest.get("logo_rows")) if isinstance(hockey_softball_next_decision_manifest, dict) else 0,
        "hockey_softball_next_decision_worksheet_athlete_rows": as_int(hockey_softball_next_decision_manifest.get("athlete_rows")) if isinstance(hockey_softball_next_decision_manifest, dict) else 0,
        "hockey_softball_next_decision_worksheet_missing_local_rows": as_int(hockey_softball_next_decision_manifest.get("missing_local_candidate_asset_rows")) if isinstance(hockey_softball_next_decision_manifest, dict) else 0,
        "hockey_softball_next_decision_worksheet_download_approved_yes_rows": as_int(hockey_softball_next_decision_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_next_decision_manifest, dict) else 0,
        "hockey_softball_next_decision_worksheet_blank_download_metadata_rows": as_int(hockey_softball_next_decision_manifest.get("blank_download_metadata_rows")) if isinstance(hockey_softball_next_decision_manifest, dict) else 0,
        "hockey_softball_source_priority_status": clean(hockey_softball_source_priority_manifest.get("status")) if isinstance(hockey_softball_source_priority_manifest, dict) else "",
        "hockey_softball_source_priority_generated_at": clean(hockey_softball_source_priority_manifest.get("generated_at_utc")) if isinstance(hockey_softball_source_priority_manifest, dict) else "",
        "hockey_softball_source_priority_rows": hockey_softball_source_priority_rows,
        "hockey_softball_source_priority_logo_rows": as_int(hockey_softball_source_priority_manifest.get("logo_rows")) if isinstance(hockey_softball_source_priority_manifest, dict) else 0,
        "hockey_softball_source_priority_athlete_rows": as_int(hockey_softball_source_priority_manifest.get("athlete_rows")) if isinstance(hockey_softball_source_priority_manifest, dict) else 0,
        "hockey_softball_source_priority_operator_verify_rows": as_int(hockey_softball_source_priority_manifest.get("operator_verify_required_rows")) if isinstance(hockey_softball_source_priority_manifest, dict) else 0,
        "hockey_softball_source_priority_download_approved_yes_rows": as_int(hockey_softball_source_priority_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_source_priority_manifest, dict) else 0,
        "hockey_softball_source_priority_blank_source_url_rows": as_int(hockey_softball_source_priority_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_source_priority_manifest, dict) else 0,
        "hockey_softball_source_verification_status": clean(hockey_softball_source_verification_manifest.get("status")) if isinstance(hockey_softball_source_verification_manifest, dict) else "",
        "hockey_softball_source_verification_generated_at": clean(hockey_softball_source_verification_manifest.get("generated_at_utc")) if isinstance(hockey_softball_source_verification_manifest, dict) else "",
        "hockey_softball_source_verification_rows": hockey_softball_source_verification_rows,
        "hockey_softball_source_verification_womens_hockey_rows": as_int(hockey_softball_source_verification_manifest.get("womens_hockey_rows")) if isinstance(hockey_softball_source_verification_manifest, dict) else 0,
        "hockey_softball_source_verification_softball_rows": as_int(hockey_softball_source_verification_manifest.get("softball_rows")) if isinstance(hockey_softball_source_verification_manifest, dict) else 0,
        "hockey_softball_source_verification_download_approved_yes_rows": as_int(hockey_softball_source_verification_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_source_verification_manifest, dict) else 0,
        "hockey_softball_source_verification_blank_source_url_rows": as_int(hockey_softball_source_verification_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_source_verification_manifest, dict) else 0,
        "hockey_softball_source_verification_blank_human_review_rows": as_int(hockey_softball_source_verification_manifest.get("blank_human_review_rows")) if isinstance(hockey_softball_source_verification_manifest, dict) else 0,
        "hockey_softball_intake_readiness_status": clean(hockey_softball_intake_readiness_manifest.get("status")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else "",
        "hockey_softball_intake_readiness_generated_at": clean(hockey_softball_intake_readiness_manifest.get("generated_at_utc")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else "",
        "hockey_softball_intake_readiness_groups": hockey_softball_intake_readiness_groups,
        "hockey_softball_intake_readiness_rows_covered": as_int(hockey_softball_intake_readiness_manifest.get("rows_covered")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0,
        "hockey_softball_intake_readiness_logo_source_reviewed_rows": as_int(hockey_softball_intake_readiness_manifest.get("logo_source_reviewed_rows")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0,
        "hockey_softball_intake_readiness_athlete_source_pending_rows": as_int(hockey_softball_intake_readiness_manifest.get("athlete_source_pending_rows")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0,
        "hockey_softball_intake_readiness_blank_human_review_metadata_rows": as_int(hockey_softball_intake_readiness_manifest.get("blank_human_review_metadata_rows")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0,
        "hockey_softball_intake_readiness_unsafe_guardrail_rows": as_int(hockey_softball_intake_readiness_manifest.get("unsafe_guardrail_rows")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0,
        "hockey_softball_intake_readiness_download_approved_yes_rows": as_int(hockey_softball_intake_readiness_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_intake_readiness_manifest, dict) else 0,
        "hockey_softball_source_map_status": clean(hockey_softball_source_map_manifest.get("status")) if isinstance(hockey_softball_source_map_manifest, dict) else "",
        "hockey_softball_source_map_generated_at": clean(hockey_softball_source_map_manifest.get("generated_at_utc")) if isinstance(hockey_softball_source_map_manifest, dict) else "",
        "hockey_softball_source_map_rows": hockey_softball_source_map_rows,
        "hockey_softball_source_map_womens_hockey_rows": as_int(hockey_softball_source_map_manifest.get("womens_hockey_rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0,
        "hockey_softball_source_map_softball_rows": as_int(hockey_softball_source_map_manifest.get("softball_rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0,
        "hockey_softball_source_map_official_free_public_rows": as_int(hockey_softball_source_map_manifest.get("official_free_public_rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0,
        "hockey_softball_source_map_download_approved_yes_rows": as_int(hockey_softball_source_map_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0,
        "hockey_softball_source_map_allowed_for_download_approved_yes_rows": as_int(hockey_softball_source_map_manifest.get("allowed_for_download_approved_yes_rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0,
        "hockey_softball_source_map_blank_source_url_rows": as_int(hockey_softball_source_map_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_source_map_manifest, dict) else 0,
        "hockey_softball_action_photo_handoff_status": clean(hockey_softball_action_photo_handoff_manifest.get("status")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else "",
        "hockey_softball_action_photo_handoff_generated_at": clean(hockey_softball_action_photo_handoff_manifest.get("generated_at_utc")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else "",
        "hockey_softball_action_photo_handoff_rows": hockey_softball_action_photo_handoff_rows,
        "hockey_softball_action_photo_handoff_womens_hockey_rows": as_int(hockey_softball_action_photo_handoff_manifest.get("womens_hockey_rows")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else 0,
        "hockey_softball_action_photo_handoff_softball_rows": as_int(hockey_softball_action_photo_handoff_manifest.get("softball_rows")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else 0,
        "hockey_softball_action_photo_handoff_download_approved_yes_rows": as_int(hockey_softball_action_photo_handoff_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else 0,
        "hockey_softball_action_photo_handoff_ready_rows": as_int(hockey_softball_action_photo_handoff_manifest.get("later_human_download_decision_review_eligible_rows")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else 0,
        "hockey_softball_action_photo_handoff_blank_source_url_rows": as_int(hockey_softball_action_photo_handoff_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else 0,
        "hockey_softball_action_photo_handoff_asset_downloads": bool(hockey_softball_action_photo_handoff_manifest.get("asset_downloads")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else False,
        "hockey_softball_action_photo_handoff_headshot_writes": bool(hockey_softball_action_photo_handoff_manifest.get("headshot_writes")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else False,
        "hockey_softball_action_photo_handoff_approved_marker_writes": bool(hockey_softball_action_photo_handoff_manifest.get("approved_marker_writes")) if isinstance(hockey_softball_action_photo_handoff_manifest, dict) else False,
        "hockey_softball_source_research_return_status": clean(hockey_softball_source_research_return_manifest.get("status")) if isinstance(hockey_softball_source_research_return_manifest, dict) else "",
        "hockey_softball_source_research_return_generated_at": clean(hockey_softball_source_research_return_manifest.get("generated_at_utc")) if isinstance(hockey_softball_source_research_return_manifest, dict) else "",
        "hockey_softball_source_research_return_rows": hockey_softball_source_research_return_rows,
        "hockey_softball_source_research_return_womens_hockey_rows": as_int(hockey_softball_source_research_return_manifest.get("womens_hockey_rows")) if isinstance(hockey_softball_source_research_return_manifest, dict) else 0,
        "hockey_softball_source_research_return_softball_rows": as_int(hockey_softball_source_research_return_manifest.get("softball_rows")) if isinstance(hockey_softball_source_research_return_manifest, dict) else 0,
        "hockey_softball_source_research_return_blank_operator_rows": as_int(hockey_softball_source_research_return_manifest.get("blank_operator_return_rows")) if isinstance(hockey_softball_source_research_return_manifest, dict) else 0,
        "hockey_softball_source_research_return_download_approved_yes_rows": as_int(hockey_softball_source_research_return_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_source_research_return_manifest, dict) else 0,
        "hockey_softball_asset_review_triage_status": clean(hockey_softball_review_triage_manifest.get("status")) if isinstance(hockey_softball_review_triage_manifest, dict) else "",
        "hockey_softball_asset_review_triage_generated_at": clean(hockey_softball_review_triage_manifest.get("generated_at_utc")) if isinstance(hockey_softball_review_triage_manifest, dict) else "",
        "hockey_softball_asset_review_triage_rows": hockey_softball_review_triage_rows,
        "hockey_softball_asset_review_triage_logo_rows": as_int(hockey_softball_review_triage_manifest.get("logo_rows")) if isinstance(hockey_softball_review_triage_manifest, dict) else 0,
        "hockey_softball_asset_review_triage_athlete_rows": as_int(hockey_softball_review_triage_manifest.get("athlete_rows")) if isinstance(hockey_softball_review_triage_manifest, dict) else 0,
        "hockey_softball_asset_review_triage_operator_verify_source_rows": as_int(hockey_softball_review_triage_manifest.get("operator_verify_required_source_rows")) if isinstance(hockey_softball_review_triage_manifest, dict) else 0,
        "hockey_softball_asset_review_triage_download_approved_yes_rows": as_int(hockey_softball_review_triage_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_review_triage_manifest, dict) else 0,
        "hockey_softball_asset_review_triage_blank_source_url_rows": as_int(hockey_softball_review_triage_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_review_triage_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_status": clean(hockey_softball_asset_readiness_manifest.get("status")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else "",
        "hockey_softball_asset_review_readiness_generated_at": clean(hockey_softball_asset_readiness_manifest.get("generated_at_utc")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else "",
        "hockey_softball_asset_review_readiness_rows": hockey_softball_asset_readiness_rows,
        "hockey_softball_asset_review_readiness_logo_rows": as_int(hockey_softball_asset_readiness_manifest.get("logo_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_athlete_rows": as_int(hockey_softball_asset_readiness_manifest.get("athlete_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_download_approved_yes_rows": as_int(hockey_softball_asset_readiness_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_blank_source_url_rows": as_int(hockey_softball_asset_readiness_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_source_identity_gap_rows": as_int(hockey_softball_asset_readiness_manifest.get("source_identity_gap_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_team_entity_check_rows": as_int(hockey_softball_asset_readiness_manifest.get("team_entity_check_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_asset_review_readiness_local_candidate_gap_rows": as_int(hockey_softball_asset_readiness_manifest.get("local_candidate_gap_rows")) if isinstance(hockey_softball_asset_readiness_manifest, dict) else 0,
        "hockey_softball_manual_verification_focus_status": clean(hockey_softball_manual_focus_manifest.get("status")) if isinstance(hockey_softball_manual_focus_manifest, dict) else "",
        "hockey_softball_manual_verification_focus_generated_at": clean(hockey_softball_manual_focus_manifest.get("generated_at_utc")) if isinstance(hockey_softball_manual_focus_manifest, dict) else "",
        "hockey_softball_manual_verification_focus_rows": hockey_softball_manual_focus_rows,
        "hockey_softball_manual_verification_focus_p0_rows": as_int(hockey_softball_manual_focus_manifest.get("p0_rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0,
        "hockey_softball_manual_verification_focus_p1_rows": as_int(hockey_softball_manual_focus_manifest.get("p1_rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0,
        "hockey_softball_manual_verification_focus_asset_readiness_rows": as_int(hockey_softball_manual_focus_manifest.get("asset_readiness_rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0,
        "hockey_softball_manual_verification_focus_source_map_rows": as_int(hockey_softball_manual_focus_manifest.get("source_map_rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0,
        "hockey_softball_manual_verification_focus_download_approved_yes_rows": as_int(hockey_softball_manual_focus_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0,
        "hockey_softball_manual_verification_focus_blank_source_url_rows": as_int(hockey_softball_manual_focus_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_manual_focus_manifest, dict) else 0,
        "hockey_softball_asset_next_action_cards_status": clean(hockey_softball_next_action_cards_manifest.get("status")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else "",
        "hockey_softball_asset_next_action_cards_generated_at": clean(hockey_softball_next_action_cards_manifest.get("generated_at_utc")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else "",
        "hockey_softball_asset_next_action_cards_rows": hockey_softball_next_action_card_rows,
        "hockey_softball_asset_next_action_cards_logo_rows": as_int(hockey_softball_next_action_cards_manifest.get("logo_rows")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else 0,
        "hockey_softball_asset_next_action_cards_athlete_rows": as_int(hockey_softball_next_action_cards_manifest.get("athlete_rows")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else 0,
        "hockey_softball_asset_next_action_cards_download_approved_yes_rows": as_int(hockey_softball_next_action_cards_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else 0,
        "hockey_softball_asset_next_action_cards_blank_source_url_rows": as_int(hockey_softball_next_action_cards_manifest.get("blank_source_url_rows")) if isinstance(hockey_softball_next_action_cards_manifest, dict) else 0,
        "hockey_softball_quarantine_download_intake_status": clean(hockey_softball_quarantine_download_manifest.get("status")) if isinstance(hockey_softball_quarantine_download_manifest, dict) else "",
        "hockey_softball_quarantine_download_intake_generated_at": clean(hockey_softball_quarantine_download_manifest.get("generated_at_utc")) if isinstance(hockey_softball_quarantine_download_manifest, dict) else "",
        "hockey_softball_quarantine_download_intake_rows": hockey_softball_quarantine_download_rows,
        "hockey_softball_quarantine_download_intake_logo_rows": as_int(hockey_softball_quarantine_download_manifest.get("logo_rows")) if isinstance(hockey_softball_quarantine_download_manifest, dict) else 0,
        "hockey_softball_quarantine_download_intake_athlete_rows": as_int(hockey_softball_quarantine_download_manifest.get("athlete_rows")) if isinstance(hockey_softball_quarantine_download_manifest, dict) else 0,
        "hockey_softball_quarantine_download_approved_yes_rows": as_int(hockey_softball_quarantine_download_manifest.get("download_approved_yes_rows")) if isinstance(hockey_softball_quarantine_download_manifest, dict) else 0,
        "womens_hockey_logo_contact_sheet_rows": len(womens_hockey_logo_rows),
        "womens_hockey_athlete_photo_contact_sheet_rows": len(womens_hockey_athlete_rows),
        "womens_hockey_athlete_photo_contact_sheet_team_boards": as_int(womens_hockey_athlete_manifest.get("team_boards")) if isinstance(womens_hockey_athlete_manifest, dict) else 0,
        "womens_hockey_athlete_photo_source_review_slot_rows": as_int(womens_hockey_athlete_manifest.get("source_review_slot_rows")) if isinstance(womens_hockey_athlete_manifest, dict) else 0,
        "womens_hockey_review_walkthrough_rows": len(womens_hockey_logo_rows) + len(womens_hockey_athlete_rows),
        "womens_hockey_asset_workflow_rows": as_int(womens_hockey_workflow_summary.get("workflow_rows")),
        "womens_hockey_proposed_headshot_path_refs": as_int(womens_hockey_workflow_summary.get("proposed_headshot_path_refs")),
        "womens_hockey_proposed_approved_marker_path_refs": as_int(womens_hockey_workflow_summary.get("proposed_approved_marker_path_refs")),
        "softball_logo_contact_sheet_rows": len(softball_logo_rows),
        "softball_athlete_photo_contact_sheet_rows": len(softball_athlete_rows),
        "softball_athlete_photo_contact_sheet_team_boards": as_int(softball_athlete_manifest.get("team_boards")) if isinstance(softball_athlete_manifest, dict) else 0,
        "softball_athlete_photo_source_review_slot_rows": as_int(softball_athlete_manifest.get("source_review_slot_rows")) if isinstance(softball_athlete_manifest, dict) else 0,
        "softball_review_walkthrough_rows": len(softball_logo_rows) + len(softball_athlete_rows),
        "softball_asset_workflow_rows": as_int(softball_workflow_summary.get("workflow_rows")),
        "softball_proposed_headshot_path_refs": as_int(softball_workflow_summary.get("proposed_headshot_path_refs")),
        "softball_proposed_approved_marker_path_refs": as_int(softball_workflow_summary.get("proposed_approved_marker_path_refs")),
        "hockey_softball_asset_foundation_freshness_status": hockey_softball_cue["status"],
        "hockey_softball_asset_foundation_freshness_detail": hockey_softball_cue["detail"],
        "hockey_softball_asset_foundation_refresh_command": hockey_softball_cue["run_command"],
        "hockey_softball_foundation_coverage_freshness_status": hockey_softball_coverage_cue["status"],
        "hockey_softball_foundation_coverage_freshness_detail": hockey_softball_coverage_cue["detail"],
        "hockey_softball_foundation_coverage_refresh_command": hockey_softball_coverage_cue["run_command"],
        "hockey_softball_source_review_helper_freshness_status": hockey_softball_helper_cue["status"],
        "hockey_softball_source_review_helper_freshness_detail": hockey_softball_helper_cue["detail"],
        "hockey_softball_source_review_helper_refresh_command": hockey_softball_helper_cue["run_command"],
        "hockey_softball_asset_workflow_freshness_status": hockey_softball_workflow_cue["status"],
        "hockey_softball_asset_workflow_freshness_detail": hockey_softball_workflow_cue["detail"],
        "hockey_softball_asset_workflow_refresh_command": hockey_softball_workflow_cue["run_command"],
        "hockey_softball_asset_review_action_queue_freshness_status": hockey_softball_action_queue_cue["status"],
        "hockey_softball_asset_review_action_queue_freshness_detail": hockey_softball_action_queue_cue["detail"],
        "hockey_softball_asset_review_action_queue_refresh_command": hockey_softball_action_queue_cue["run_command"],
        "hockey_softball_batch_source_review_freshness_status": hockey_softball_batch_source_review_cue["status"],
        "hockey_softball_batch_source_review_freshness_detail": hockey_softball_batch_source_review_cue["detail"],
        "hockey_softball_batch_source_review_refresh_command": hockey_softball_batch_source_review_cue["run_command"],
        "hockey_softball_next_decision_worksheet_freshness_status": hockey_softball_next_decision_cue["status"],
        "hockey_softball_next_decision_worksheet_freshness_detail": hockey_softball_next_decision_cue["detail"],
        "hockey_softball_next_decision_worksheet_refresh_command": hockey_softball_next_decision_cue["run_command"],
        "hockey_softball_source_priority_freshness_status": hockey_softball_source_priority_cue["status"],
        "hockey_softball_source_priority_freshness_detail": hockey_softball_source_priority_cue["detail"],
        "hockey_softball_source_priority_refresh_command": hockey_softball_source_priority_cue["run_command"],
        "hockey_softball_source_verification_freshness_status": hockey_softball_source_verification_cue["status"],
        "hockey_softball_source_verification_freshness_detail": hockey_softball_source_verification_cue["detail"],
        "hockey_softball_source_verification_refresh_command": hockey_softball_source_verification_cue["run_command"],
        "hockey_softball_intake_readiness_freshness_status": hockey_softball_intake_readiness_cue["status"],
        "hockey_softball_intake_readiness_freshness_detail": hockey_softball_intake_readiness_cue["detail"],
        "hockey_softball_intake_readiness_refresh_command": hockey_softball_intake_readiness_cue["run_command"],
        "hockey_softball_source_map_freshness_status": hockey_softball_source_map_cue["status"],
        "hockey_softball_source_map_freshness_detail": hockey_softball_source_map_cue["detail"],
        "hockey_softball_source_map_refresh_command": hockey_softball_source_map_cue["run_command"],
        "hockey_softball_action_photo_handoff_freshness_status": hockey_softball_action_photo_handoff_cue["status"],
        "hockey_softball_action_photo_handoff_freshness_detail": hockey_softball_action_photo_handoff_cue["detail"],
        "hockey_softball_action_photo_handoff_refresh_command": hockey_softball_action_photo_handoff_cue["run_command"],
        "hockey_softball_source_research_return_freshness_status": hockey_softball_source_research_return_cue["status"],
        "hockey_softball_source_research_return_freshness_detail": hockey_softball_source_research_return_cue["detail"],
        "hockey_softball_source_research_return_refresh_command": hockey_softball_source_research_return_cue["run_command"],
        "hockey_softball_asset_review_triage_freshness_status": hockey_softball_review_triage_cue["status"],
        "hockey_softball_asset_review_triage_freshness_detail": hockey_softball_review_triage_cue["detail"],
        "hockey_softball_asset_review_triage_refresh_command": hockey_softball_review_triage_cue["run_command"],
        "hockey_softball_asset_review_readiness_freshness_status": hockey_softball_asset_readiness_cue["status"],
        "hockey_softball_asset_review_readiness_freshness_detail": hockey_softball_asset_readiness_cue["detail"],
        "hockey_softball_asset_review_readiness_refresh_command": hockey_softball_asset_readiness_cue["run_command"],
        "hockey_softball_manual_verification_focus_freshness_status": hockey_softball_manual_focus_cue["status"],
        "hockey_softball_manual_verification_focus_freshness_detail": hockey_softball_manual_focus_cue["detail"],
        "hockey_softball_manual_verification_focus_refresh_command": hockey_softball_manual_focus_cue["run_command"],
        "hockey_softball_asset_next_action_cards_freshness_status": hockey_softball_next_action_cards_cue["status"],
        "hockey_softball_asset_next_action_cards_freshness_detail": hockey_softball_next_action_cards_cue["detail"],
        "hockey_softball_asset_next_action_cards_refresh_command": hockey_softball_next_action_cards_cue["run_command"],
        "hockey_softball_quarantine_download_intake_freshness_status": hockey_softball_quarantine_download_cue["status"],
        "hockey_softball_quarantine_download_intake_freshness_detail": hockey_softball_quarantine_download_cue["detail"],
        "hockey_softball_quarantine_download_intake_refresh_command": hockey_softball_quarantine_download_cue["run_command"],
        "logo_review_packets": logo_packets,
        "top_findings": top_findings,
        "next_step": next_step,
        "policy": {
            "no_paid_apis": bool(policy.get("no_paid_apis", True)),
            "no_asset_downloads": bool(policy.get("no_asset_downloads", True)),
            "no_auto_approval": bool(policy.get("no_auto_approval", True)),
            "no_file_movement_into_publish_ready_lanes": bool(policy.get("no_file_movement_into_publish_ready_lanes", True)),
            "no_publishing": bool(policy.get("no_publishing", True)),
            "does_not_change_renderer_behavior": bool(policy.get("does_not_change_renderer_behavior", True)),
        },
        "file_shortcuts": [
            file_shortcut("Asset availability audit", "data/asset_registry/asset_availability_audit.md", "Start here for highest-risk asset blockers and operator next steps."),
            file_shortcut("Asset availability data", "data/asset_registry/asset_availability_audit.csv", "Filter all asset findings by domain, severity, entity, and finding type."),
            file_shortcut("WNBA athlete photo catalog", "data/asset_registry/wnba/athlete_photo_catalog.md", "Review photo source, identity, crop, and approval readiness."),
            file_shortcut("WNBA logo review catalog", "data/asset_registry/wnba/logo_review_catalog_report.md", "Review team logo source trust, approval holds, and missing league marks."),
            file_shortcut("WNBA logo review packets", "data/asset_registry/wnba/logo_review_packets.csv", "Review unapproved logos and source path drift rows before renderer trust."),
            file_shortcut("WNBA team logo contact sheet", "data/asset_registry/wnba/wnba_team_logo_contact_sheet.md", "Open every active WNBA logo in one sweep-review board."),
            file_shortcut("WNBA team logo review intake", "data/asset_registry/wnba/wnba_team_logo_review_intake.csv", "Human-edited approve/deny/hold worksheet; this generator does not apply decisions."),
            file_shortcut("Women's soccer logo contact sheet", "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md", "Review NWSL team logos and European top-flight league mark source candidates in one sweep board."),
            file_shortcut("Women's soccer logo review intake", "data/asset_registry/womens_soccer/womens_soccer_logo_review_intake.csv", "Human-edited approve/deny/hold worksheet; this generator does not apply decisions."),
            file_shortcut("Women's soccer logo review walkthrough", "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md", "Open the prioritized review order before filling the human intake worksheet."),
            file_shortcut("Women's soccer athlete photo contact sheets", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md", "Review NWSL and European top-flight athlete photo candidate placeholders and public-source candidate rows by team."),
            file_shortcut("Women's soccer athlete photo contact sheet data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv", "Machine-readable review-only athlete photo candidate rows."),
            file_shortcut("Women's soccer athlete photo review intake", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv", "Human-edited athlete photo candidate decisions; this generator does not download or approve photos."),
            file_shortcut("Women's soccer athlete operator board", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.md", "NWSL-first review queue plus European starter placeholders, source domains, and safe next actions."),
            file_shortcut("Women's soccer athlete operator board data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.csv", "Machine-readable team-level NWSL-first operator queue."),
            file_shortcut("Women's soccer athlete operator board manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_operator_board.json", "Freshness and guardrail metadata for the NWSL-first athlete operator board."),
            file_shortcut("Women's soccer athlete photo download intake", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.md", "Review-only future quarantine-download gate; every generated row defaults to download_approved=no."),
            file_shortcut("Women's soccer athlete photo download intake data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv", "Human-edited source URL, entity ID, rights class, identity confidence, intended use, and download_approved worksheet."),
            file_shortcut("Women's soccer athlete verification queue", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.md", "NWSL-first roster/source verification queue with Europe source-candidate-only league rows."),
            file_shortcut("Women's soccer athlete verification queue data", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.csv", "Machine-readable operator queue for roster verification, source quality, and missing local candidate asset blockers."),
            file_shortcut("Women's soccer athlete verification queue manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_queue.json", "Freshness, counts, and guardrail metadata for the athlete verification queue."),
            file_shortcut("Women's soccer athlete verification next actions", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.md", "NWSL-first worksheet with first-action buckets and future download-law fields left blank/no for human review."),
            file_shortcut("Women's soccer athlete verification next actions data", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.csv", "Machine-readable NWSL-first operator worksheet; no download, approval, or candidate-state writeback."),
            file_shortcut("Women's soccer athlete verification next actions manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_verification_next_actions.json", "Freshness, counts, and guardrail metadata for the NWSL-first next-action worksheet."),
            file_shortcut("Women's soccer athlete source priority", "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.md", "NWSL-first and Europe source-candidate worksheet sorted by source verification priority; no download or approval writeback."),
            file_shortcut("Women's soccer athlete source priority data", "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.csv", "Machine-readable source candidate worksheet with future download-law fields kept blank/no for human review."),
            file_shortcut("Women's soccer athlete source priority manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_source_priority.json", "Freshness, counts, and guardrail metadata for the source-priority worksheet."),
            file_shortcut("Women's soccer athlete review triage", "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.md", "Manual action triage worksheet combining verification queue and source-priority rows; no download, approval, or publish writeback."),
            file_shortcut("Women's soccer athlete review triage data", "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.csv", "Machine-readable triage worksheet with advisory source candidates and blank/no future download-law fields."),
            file_shortcut("Women's soccer athlete review triage manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_review_triage.json", "Freshness, counts, and guardrail metadata for the review triage worksheet."),
            file_shortcut("Women's soccer athlete candidate next-action board", "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.md", "Source-candidate action board grouped by manual work type; review-only and no download/approval writeback."),
            file_shortcut("Women's soccer athlete candidate next-action board data", "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.csv", "Machine-readable candidate next-action board with exact source row refs and blank/no download-law fields."),
            file_shortcut("Women's soccer athlete candidate next-action board manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_candidate_next_action_board.json", "Freshness, counts, and guardrail metadata for the candidate next-action board."),
            file_shortcut("Women's soccer athlete photo review readiness board", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.md", "Photo-readiness next-action board for manual roster/source/identity work before future candidate photo review; review-only and no downloads."),
            file_shortcut("Women's soccer athlete photo review readiness board data", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.csv", "Machine-readable photo-readiness board with exact row refs and blank/no download-law fields."),
            file_shortcut("Women's soccer athlete photo review readiness board manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_readiness_board.json", "Freshness, counts, and guardrail metadata for the photo-readiness board."),
            file_shortcut("Women's soccer athlete operator focus", "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md", "Priority athlete/source focus board with identity, proof, profile URL, photo, and action-photo review-only statuses."),
            file_shortcut("Women's soccer athlete operator focus data", "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.csv", "Machine-readable focus rows with exact refs and blank/no profile, source, download, and decision placeholders."),
            file_shortcut("Women's soccer athlete operator focus manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.json", "Freshness, status counts, and guardrail metadata for the operator focus board."),
            file_shortcut("Women's soccer action-photo research next", "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.md", "Manual next-research bridge from athlete focus rows to action-photo research return paste fields; review-only and no downloads."),
            file_shortcut("Women's soccer action-photo research next data", "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv", "Machine-readable candidate-page, evidence, identity-anchor, rights, and use metadata prompts with blank/no generated defaults."),
            file_shortcut("Women's soccer action-photo research next manifest", "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.json", "Status, missing-field counts, and guardrail metadata for the action-photo research-next board."),
            file_shortcut("Women's soccer athlete expansion closure summary", "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.md", "Latest-artifact collection that tells the operator what to open first and proves no downloads, approvals, headshots, markers, or publish-ready movement."),
            file_shortcut("Women's soccer athlete expansion closure summary data", "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.csv", "Machine-readable closure rows with referenced artifact counts, manual next actions, and review-only guardrails."),
            file_shortcut("Women's soccer athlete expansion closure summary manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_expansion_closure_summary.json", "Freshness, count, and guardrail metadata for the closure summary."),
            file_shortcut("Women's soccer external research intake", "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.md", "Advisory NWSL correction/enrichment and Europe source-map rows for source metadata review only."),
            file_shortcut("Women's soccer external research intake data", "data/asset_registry/womens_soccer/external_research/womens_soccer_external_research_intake_board.csv", "Machine-readable operator buckets for external research rows; no candidate-state or approval writeback."),
            file_shortcut("Women's soccer NWSL external research source", "data/asset_registry/womens_soccer/external_research/nwsl_correction_enrichment_report.csv", "Raw advisory NWSL correction/enrichment research from ChatGPT Pro."),
            file_shortcut("Women's soccer Europe external research source", "data/asset_registry/womens_soccer/external_research/europe_official_source_map.csv", "Raw advisory European official-source map from ChatGPT Pro."),
            file_shortcut("Women's soccer athlete photo manifest", "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json", "Freshness, warning, and guardrail metadata for the athlete photo contact-sheet packet."),
            file_shortcut("Action-photo candidate intake", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_intake.md", "Review-only local-download-law starter; generated rows remain blank/no until human return fields exist."),
            file_shortcut("Action-photo source discovery board", "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.md", "Review-only source-discovery queue for official/public/newsroom/manual leads; no source fetching, downloads, enablement, approvals, or publishing."),
            file_shortcut("Action-photo source discovery data", "data/asset_registry/action_photo_candidates/review_only_action_photo_source_discovery_board_v1.csv", "Machine-readable discovery rows with blank/no operator return fields and exact paste-back targets."),
            file_shortcut("Action-photo manual source-hunt board", "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.md", "Copy/paste-friendly manual source-hunt rows with next search queries, identity anchors, candidate page needs, and exact research-return paste fields."),
            file_shortcut("Action-photo manual source-hunt data", "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_source_hunt_board_v1.csv", "Machine-readable source-hunt rows; generated source/download fields stay blank/no and no fetching, downloads, approvals, or publishing occur."),
            file_shortcut("Action-photo sport/entity source-map board", "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.md", "Review-only WNBA/NWSL/USWNT/NCAA/tennis/golf discovery board with official/public/newsroom/social/manual lanes; operator fields stay blank/no."),
            file_shortcut("Action-photo sport/entity source-map data", "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.csv", "Machine-readable source-map board; no fetching, downloads, source enablement, approvals, or publish-ready state."),
            file_shortcut("Action-photo candidate operator worksheet", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.md", "Manual candidate URL, source/right/context, event/date, crop/use-case, reviewer decision, and next-action worksheet; no downloads or approvals."),
            file_shortcut("Action-photo candidate operator worksheet data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_operator_worksheet_v1.csv", "Machine-readable operator worksheet; generated candidate/download/reviewer fields remain blank/no."),
            file_shortcut("Action-photo research packet", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md", "Manual research prompts and source leads only; no image downloads, approvals, or render-ready state."),
            file_shortcut("Action-photo lead return schema", "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.md", "Paste-back schema for action-photo research returns; generated fields stay blank and operator verification remains required."),
            file_shortcut("Action-photo lead return schema data", "data/asset_registry/action_photo_candidates/review_only_action_photo_lead_return_schema_v1.csv", "Machine-readable return fields and validation notes for manual research leads; no approval or download authorization."),
            file_shortcut("Action-photo research run bundle", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_run_bundle_v1.md", "Operator glue for running/pasting the research packet; artifact-only and does not send email or download images."),
            file_shortcut("Action-photo external research bundle latest", "action_photo_external_research_bundle_latest.json", "Latest local bundle manifest for uploading exact review-only action-photo research artifacts; no sending, downloads, approvals, or publishing."),
            file_shortcut("Action-photo local handoff draft copy", "action_photo_external_research_handoff_draft_copy.md", "Paste-ready local email/ChatGPT/Gemini copy for the latest bundle; does not send email or create Gmail drafts."),
            file_shortcut("Action-photo local handoff draft copy manifest", "action_photo_external_research_handoff_draft_copy.json", "Structured subject/body/path/guardrail manifest for the local draft-copy artifact; no Gmail payload or send action."),
            file_shortcut("Action-photo research return intake", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv", "Human-edited paste-back target for source_url/entity_id/rights/identity fields before any quarantine decision."),
            file_shortcut("Action-photo research return paste worksheet", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.md", "Copy/paste helper that shows sport/entity/source context, exact return fields, and missing fields before later human download-decision review."),
            file_shortcut("Action-photo research return paste worksheet data", "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_paste_worksheet_v1.csv", "Machine-readable paste worksheet; generated download fields remain no and no asset writes occur."),
            file_shortcut("Action-photo cutout scoring criteria", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.md", "Manual scoring criteria for future cutout review; no segmentation, background removal, downloads, approvals, or publish-ready state."),
            file_shortcut("Action-photo cutout scoring criteria data", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_scoring_criteria_v1.csv", "Machine-readable cutout scoring fields; generated source/download fields stay blank/no."),
            file_shortcut("Action-photo quarantine preflight", "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md", "Preflight gate showing whether human-return rows are ready for download decision; generated rows remain lead-only."),
            file_shortcut("Action-photo quarantine preflight data", "data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.csv", "Machine-readable preflight; 0 ready rows means no human download decision should happen yet."),
            file_shortcut("Action-photo candidate quality/fit board", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.md", "Review-only quality/fit triage for returned candidate URLs: source, rights, identity, action moment, crop/use suitability, and download eligibility."),
            file_shortcut("Action-photo candidate quality/fit data", "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_quality_fit_board_v1.csv", "Machine-readable quality/fit rows; generated download eligibility remains no/not eligible unless later human-edited intake is complete."),
            file_shortcut("Action-photo quality/fit operator cue", "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.md", "Tiny operator cue for the next manual fields after research returns land; no downloads, approvals, source fetching, or asset writes."),
            file_shortcut("Action-photo quality/fit operator cue data", "data/asset_registry/action_photo_candidates/review_only_action_photo_quality_fit_operator_cue_v1.csv", "Machine-readable missing-field and graduation-gate cues derived from the quality/fit board."),
            file_shortcut("Action-photo download decision queue", "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.md", "Human decision queue for quarantine-only candidate downloads; generated rows keep download_approved=no and do not approve assets."),
            file_shortcut("Action-photo download decision data", "data/asset_registry/action_photo_candidates/review_only_action_photo_download_decision_queue_v1.csv", "Machine-readable decision rows listing required human edits and the review-only quarantine destination."),
            file_shortcut("WNBA hero action-photo targets", "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.md", "Kelsey Mitchell/Fever target board for manual hero-photo research only; generated source and download-law fields stay blank/no."),
            file_shortcut("WNBA hero action-photo targets data", "data/asset_registry/action_photo_candidates/review_only_wnba_final_score_hero_action_photo_targets_v1.csv", "Machine-readable target rows; no source fetching, downloads, approvals, or publish-ready state."),
            file_shortcut("Action-photo cutout readiness", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.md", "Manual cutout-readiness worksheet; no segmentation, background removal, or cutout file writes."),
            file_shortcut("Action-photo cutout readiness data", "data/asset_registry/action_photo_candidates/review_only_action_photo_cutout_readiness_v1.csv", "Machine-readable cutout worksheet with generated cutout/source/download fields blank/no."),
            file_shortcut("Hockey/softball foundation report", "data/asset_registry/hockey_softball_asset_foundation_report.md", "Review PWHL and AUSL source-candidate scaffold counts and guardrails."),
            file_shortcut("Hockey/softball foundation coverage index", "data/asset_registry/hockey_softball_foundation_coverage_index.md", "Open one compact index of source URL registries, contact sheets, intakes, athlete layers, and hold-only guardrails."),
            file_shortcut("Hockey/softball foundation coverage manifest", "data/asset_registry/hockey_softball_foundation_coverage_index.json", "Structured counts and freshness data for the hockey/softball foundation coverage index."),
            file_shortcut("Hockey/softball source review helper report", "data/asset_registry/hockey_softball_source_review_helper_report.md", "Review batch source-review prep counts and safety notes for the hockey and softball packets."),
            file_shortcut("Hockey/softball asset workflow readiness", "data/asset_registry/hockey_softball_asset_workflow_readiness_report.md", "Open the logo/contact-sheet/intake review order and athlete candidate path clarity board."),
            file_shortcut("Hockey/softball asset review action queue", "data/asset_registry/hockey_softball_asset_review_action_queue.md", "Start here for exact board, contact sheet, intake CSV, fields to fill, fields to leave blank, and hold-only fields."),
            file_shortcut("Hockey/softball batch source review helper", "data/asset_registry/hockey_softball_batch_source_review_helper.md", "Open the next 10 source-reviewable rows, evidence URLs, intake fields to fill, and fields that must stay held."),
            file_shortcut("Hockey/softball next decision worksheet", "data/asset_registry/hockey_softball_next_decision_worksheet.md", "Compact blank-cell worksheet for the next logo identity/source rows and athlete source-only rows."),
            file_shortcut("Hockey/softball next decision worksheet data", "data/asset_registry/hockey_softball_next_decision_worksheet.csv", "Machine-readable next-decision worksheet; generated human-decision cells remain blank."),
            file_shortcut("Hockey/softball source priority worksheet", "data/asset_registry/hockey_softball_source_priority_worksheet.md", "Review-only source-candidate priority worksheet; advisory source_candidate_url stays separate from blank download-law fields."),
            file_shortcut("Hockey/softball source priority worksheet data", "data/asset_registry/hockey_softball_source_priority_worksheet.csv", "Machine-readable source priority worksheet with source_url/entity_id blank and download_approved=no in generated rows."),
            file_shortcut("Hockey/softball source priority worksheet manifest", "data/asset_registry/hockey_softball_source_priority_worksheet.json", "Freshness, counts, and guardrail metadata for the hockey/softball source priority worksheet."),
            file_shortcut("Hockey/softball source verification checklist", "data/asset_registry/hockey_softball_source_verification_checklist.md", "Grouped PWHL/AUSL athlete source URLs to open manually before source-review intake notes."),
            file_shortcut("Hockey/softball source verification checklist data", "data/asset_registry/hockey_softball_source_verification_checklist.csv", "Machine-readable grouped source checklist; generated human-review and download-law fields remain blank/no."),
            file_shortcut("Hockey/softball source verification checklist manifest", "data/asset_registry/hockey_softball_source_verification_checklist.json", "Freshness, counts, and guardrail metadata for the hockey/softball source verification checklist."),
            file_shortcut("Hockey/softball intake readiness summary", "data/asset_registry/hockey_softball_intake_readiness_summary.md", "Summarizes existing H/S logo and athlete intake posture before any render-feed trust or local candidate work."),
            file_shortcut("Hockey/softball intake readiness summary data", "data/asset_registry/hockey_softball_intake_readiness_summary.csv", "Machine-readable intake readiness groups; generated download-law fields remain blank/no."),
            file_shortcut("Hockey/softball intake readiness summary manifest", "data/asset_registry/hockey_softball_intake_readiness_summary.json", "Freshness, counts, and guardrail metadata for H/S intake readiness."),
            file_shortcut("Hockey/softball source map board", "data/asset_registry/hockey_softball_source_map_board.md", "H/S official, reputable, social, gray-area, roster, and action-photo discovery source lanes; review-only and no downloads."),
            file_shortcut("Hockey/softball source map board data", "data/asset_registry/hockey_softball_source_map_board.csv", "Machine-readable H/S source map; generated download-law fields remain blank/no."),
            file_shortcut("Hockey/softball source map board manifest", "data/asset_registry/hockey_softball_source_map_board.json", "Freshness, counts, and guardrail metadata for the H/S source map board."),
            file_shortcut("Hockey/softball action-photo research handoff", "data/asset_registry/hockey_softball_action_photo_research_handoff.md", "Bridge from H/S source-return rows to the shared action-photo research return intake; candidate-ready still means later human download-decision review only."),
            file_shortcut("Hockey/softball action-photo research handoff data", "data/asset_registry/hockey_softball_action_photo_research_handoff.csv", "Machine-readable handoff rows with candidate-page/evidence/identity-anchor needs; generated download-law fields stay blank/no."),
            file_shortcut("Hockey/softball action-photo research handoff manifest", "data/asset_registry/hockey_softball_action_photo_research_handoff.json", "Freshness, missing-field, and guardrail counts for the H/S action-photo research handoff."),
            file_shortcut("Hockey/softball source research return intake", "data/asset_registry/hockey_softball_source_research_return_intake.md", "Human-edited paste-back target for action-photo source leads from the H/S source map; no downloads or approvals."),
            file_shortcut("Hockey/softball source research return data", "data/asset_registry/hockey_softball_source_research_return_intake.csv", "Machine-readable H/S action-photo source return rows; generated download-law fields stay blank/no."),
            file_shortcut("Hockey/softball source research return manifest", "data/asset_registry/hockey_softball_source_research_return_intake.json", "Freshness, blank-return counts, and guardrail metadata for the H/S source research return intake."),
            file_shortcut("Hockey/softball asset review triage", "data/asset_registry/hockey_softball_asset_review_triage.md", "Grouped next-action triage for hockey/softball logo and athlete source candidates; generated download-law fields remain blank/no."),
            file_shortcut("Hockey/softball asset review triage data", "data/asset_registry/hockey_softball_asset_review_triage.csv", "Machine-readable triage worksheet grouped by sport, asset domain, and entity for faster manual review."),
            file_shortcut("Hockey/softball asset review triage manifest", "data/asset_registry/hockey_softball_asset_review_triage.json", "Freshness, counts, and guardrail metadata for the hockey/softball asset review triage worksheet."),
            file_shortcut("Hockey/softball asset review readiness board", "data/asset_registry/hockey_softball_asset_review_readiness_board.md", "Review-only readiness board showing blockers before H/S photo or logo review work."),
            file_shortcut("Hockey/softball asset review readiness data", "data/asset_registry/hockey_softball_asset_review_readiness_board.csv", "Machine-readable readiness board; generated download-law fields remain blank/no."),
            file_shortcut("Hockey/softball asset review readiness manifest", "data/asset_registry/hockey_softball_asset_review_readiness_board.json", "Freshness, counts, and guardrail metadata for the H/S asset review readiness board."),
            file_shortcut("Hockey/softball manual verification focus", "data/asset_registry/hockey_softball_manual_verification_focus.md", "Focused P0/P1 manual verification board with exact row refs, source gaps, blockers, and safe next actions."),
            file_shortcut("Hockey/softball manual verification focus data", "data/asset_registry/hockey_softball_manual_verification_focus.csv", "Machine-readable P0/P1 focus board; generated download-law fields remain blank/no."),
            file_shortcut("Hockey/softball manual verification focus manifest", "data/asset_registry/hockey_softball_manual_verification_focus.json", "Freshness, counts, and guardrail metadata for the H/S manual verification focus board."),
            file_shortcut("Hockey/softball asset next-action cards", "data/asset_registry/hockey_softball_asset_next_action_cards.md", "Compact review-only cards with sport/entity, source proof placeholders, candidate status, verification status, and safe next manual action."),
            file_shortcut("Hockey/softball asset next-action cards data", "data/asset_registry/hockey_softball_asset_next_action_cards.csv", "Machine-readable next-action cards; generated URL/decision/approval/download fields remain blank/no."),
            file_shortcut("Hockey/softball asset next-action cards manifest", "data/asset_registry/hockey_softball_asset_next_action_cards.json", "Freshness, counts, and guardrail metadata for the H/S asset next-action cards."),
            file_shortcut("Hockey/softball quarantine download intake", "data/asset_registry/hockey_softball_quarantine_download_intake.md", "Human-edited future quarantine-download gate; generated rows default to download_approved=no."),
            file_shortcut("Hockey/softball quarantine download intake data", "data/asset_registry/hockey_softball_quarantine_download_intake.csv", "Machine-readable future download gate; no downloads occur from this packet."),
            file_shortcut("Women's hockey logo contact sheet", "data/asset_registry/womens_hockey/womens_hockey_logo_contact_sheet.md", "Review PWHL league/team logo source candidates before filling manual intake."),
            file_shortcut("Women's hockey athlete contact sheets", "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_contact_sheet_index.md", "Review PWHL athlete candidate placeholders by team; no photos are downloaded."),
            file_shortcut("Women's hockey review walkthrough", "data/asset_registry/womens_hockey/womens_hockey_review_walkthrough.md", "Open the hockey logo and athlete review order before touching the intake CSVs."),
            file_shortcut("Women's hockey asset workflow board", "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md", "Review PWHL logo/intake/athlete board order and manual candidate path notes."),
            file_shortcut("Softball logo contact sheet", "data/asset_registry/softball/softball_logo_contact_sheet.md", "Review AUSL league/team logo source candidates before filling manual intake."),
            file_shortcut("Softball athlete contact sheets", "data/asset_registry/softball/softball_athlete_photo_contact_sheet_index.md", "Review AUSL athlete candidate placeholders by team; no photos are downloaded."),
            file_shortcut("Softball review walkthrough", "data/asset_registry/softball/softball_review_walkthrough.md", "Open the softball logo and athlete review order before touching the intake CSVs."),
            file_shortcut("Softball asset workflow board", "data/asset_registry/softball/softball_asset_workflow_board.md", "Review AUSL logo/intake/athlete board order and manual candidate path notes."),
            file_shortcut("Logo asset catalog", "data/asset_registry/logo_asset_catalog.md", "Cross-check logo approval status and source policy."),
        ],
    }


def render_slot_summary(asset_slots: List[Dict[str, Any]]) -> Dict[str, str]:
    logo_slots = [
        slot
        for slot in asset_slots
        if isinstance(slot, dict) and "team_logo" in clean(slot.get("slot_id"))
    ]
    if not logo_slots:
        return {
            "status": "logo_not_required",
            "summary": "Logos: not required",
            "detail": "No team logo slots found for this draft.",
            "tone": "neutral",
        }
    approved = [slot for slot in logo_slots if clean(slot.get("status")) == "approved_logo"]
    review = [slot for slot in logo_slots if clean(slot.get("status")) != "approved_logo"]
    detail_parts = []
    for slot in logo_slots:
        team = clean(slot.get("team")) or clean(slot.get("slot_id"))
        status = clean(slot.get("status")) or "review"
        cue = clean(slot.get("logo_approval_cue")) or ("APPROVED LOGO" if status == "approved_logo" else "LOGO REVIEW")
        accent = clean(slot.get("team_accent_hex"))
        accent_source = clean(slot.get("team_accent_source"))
        accent_note = f", accent {accent}" if accent else ""
        source_note = f" from {accent_source}" if accent_source else ""
        detail_parts.append(f"{team}: {cue} ({status}{accent_note}{source_note})")
    if review:
        status = "logo_review_required"
        tone = "warn"
    else:
        status = "logos_ready"
        tone = "good"
    return {
        "status": status,
        "summary": f"Logos: {len(approved)} approved / {len(review)} review",
        "detail": short("; ".join(detail_parts), 180),
        "tone": tone,
    }


def photo_asset_summary(renderer: Dict[str, Any], asset_slots: List[Dict[str, Any]]) -> Dict[str, str]:
    content = renderer.get("content_module") if isinstance(renderer.get("content_module"), dict) else {}
    slot = next(
        (
            item
            for item in asset_slots
            if isinstance(item, dict) and clean(item.get("slot_id")) == "primary_photo"
        ),
        {},
    )
    status = clean(slot.get("status")) or clean(content.get("athlete_photo_status"))
    cue = clean(slot.get("photo_approval_cue")) or clean(content.get("athlete_photo_approval_cue"))
    player = clean(slot.get("player")) or clean(content.get("content_module_player"))
    path = clean(slot.get("asset_path")) or clean(content.get("athlete_photo_path"))
    marker = clean(slot.get("approval_marker_path")) or clean(content.get("athlete_photo_approval_marker_path"))
    blocker = clean(slot.get("blocker")) or clean(content.get("athlete_photo_blocker"))
    variant_status = clean(slot.get("review_variant_status")) or clean(content.get("athlete_photo_review_variant_status"))
    variant_score = clean(slot.get("review_variant_crop_readiness_score")) or clean(content.get("athlete_photo_review_variant_crop_readiness_score"))
    variant_note = f"review crop {variant_score}/100" if variant_status == "review_variant_available" and variant_score else ("review crop available" if variant_status == "review_variant_available" else "")
    if status == "approved_local_headshot":
        return {
            "status": "athlete_photo_ready",
            "summary": f"Photo: {cue or 'approved'}" + (f" / {variant_note}" if variant_note else ""),
            "detail": short(" | ".join(part for part in [player, path, marker, variant_note] if part), 220),
            "tone": "good",
        }
    if status in {"not_required_for_review_draft", "athlete_photo_not_applicable", ""}:
        return {
            "status": "athlete_photo_not_required",
            "summary": "Photo: not required",
            "detail": blocker or "No approved player-photo slot is required for this draft.",
            "tone": "neutral",
        }
    return {
        "status": status or "athlete_photo_review_required",
        "summary": f"Photo: {cue or 'review required'}",
        "detail": short(" | ".join(part for part in [player, blocker, path, marker] if part), 220),
        "tone": "warn",
    }


def source_review_summary(renderer: Dict[str, Any], asset_slots: List[Dict[str, Any]]) -> Dict[str, str]:
    source_cue = clean(renderer.get("source_cue"))
    artifact = clean(renderer.get("source_artifact"))
    detail = clean(renderer.get("copy_context")) or clean(renderer.get("source_detail"))
    source_slot = next(
        (
            slot
            for slot in asset_slots
            if isinstance(slot, dict) and clean(slot.get("slot_id")) == "source_evidence"
        ),
        {},
    )
    if not artifact:
        artifact = clean(source_slot.get("requirement")) or "source proof required"
    if source_cue in {"source_confidence_ready", "source_ready", "publish_grade"}:
        status = "source_confidence_ready"
        tone = "good"
        summary = "Source: confidence ready"
    elif artifact:
        status = "source_review_required"
        tone = "warn"
        summary = "Source: proof review required"
    else:
        status = "source_missing"
        tone = "bad"
        summary = "Source: missing"
    return {
        "status": status,
        "summary": summary,
        "detail": short(f"{artifact}. {detail}".strip(), 180),
        "tone": tone,
    }


def stat_module_review_summary(renderer: Dict[str, Any]) -> Dict[str, str]:
    content = renderer.get("content_module") if isinstance(renderer.get("content_module"), dict) else {}
    mode = clean(content.get("content_module_mode"))
    confidence = clean(content.get("stat_source_confidence"))
    label = clean(content.get("stat_source_label"))
    cue = clean(content.get("stat_review_cue"))
    player = clean(content.get("content_module_player"))
    source_text = clean(content.get("content_module_source_text"))
    microcopy = " ".join(
        part
        for part in [
            clean(content.get("editorial_microcopy_headline")),
            clean(content.get("editorial_microcopy_body")),
            clean(content.get("editorial_microcopy_review_cue")),
        ]
        if part
    )
    if mode == "verified_player_stats":
        return {
            "status": confidence or "verified_stat_text_ready_manual_crosscheck_required",
            "summary": f"Stats: {label or 'player ledger ready'}",
            "detail": short(" | ".join(part for part in [player, source_text, microcopy, cue] if part), 260),
            "tone": "good",
        }
    if mode == "game_edge_fallback":
        fallback = clean(content.get("content_module_fallback_label")) or "Score-derived fallback"
        return {
            "status": confidence or "score_only_fallback_manual_context_required",
            "summary": f"Stats: {fallback}",
            "detail": short(" | ".join(part for part in [microcopy, cue] if part) or "No named performer stats available; review source proof before using player-ledger treatment.", 260),
            "tone": "warn",
        }
    return {
        "status": "stat_module_not_applicable",
        "summary": "Stats: not applicable",
        "detail": "No final-score player/stat module metadata found.",
        "tone": "neutral",
    }


def qa_review_summary(qa: Dict[str, Any], draft: Dict[str, str]) -> Dict[str, str]:
    qa_summary = qa.get("summary", {}) if isinstance(qa.get("summary"), dict) else {}
    pass_count = clean(qa_summary.get("pass_count")) or "0"
    check_count = clean(qa_summary.get("check_count")) or "0"
    hold_count = clean(first_present(draft.get("automated_hold_count"), qa_summary.get("hold_count"), default="0"))
    status = "qa_passed_manual_review_required" if hold_count in {"", "0"} and check_count != "0" else "qa_hold_or_not_run"
    tone = "good" if status == "qa_passed_manual_review_required" else "warn"
    return {
        "status": status,
        "summary": f"QA: {pass_count}/{check_count} checks",
        "detail": f"{hold_count or '0'} automated hold(s); human review still required.",
        "tone": tone,
    }


def visual_delta_summary(delta: Dict[str, Any], format_id: str) -> Dict[str, str]:
    summaries = delta.get("format_summaries") if isinstance(delta.get("format_summaries"), dict) else {}
    summary = summaries.get(format_id) if isinstance(summaries.get(format_id), dict) else {}
    if not delta:
        return {
            "status": "visual_delta_not_run",
            "summary": "Delta: not scored",
            "detail": "Run render mode to compare draft against public mockup and layout reference.",
            "tone": "warn",
        }
    band = clean(summary.get("drift_band"))
    score = clean(summary.get("reference_visual_delta_score")) or "0"
    if not summary:
        return {
            "status": "visual_delta_missing_format",
            "summary": "Delta: missing",
            "detail": f"No visual-delta row found for {format_id}.",
            "tone": "warn",
        }
    if band == "aligned_to_reference":
        tone = "good"
        status = "visual_delta_aligned_review"
        label = f"Delta: {score}/100"
    elif band == "review_minor_drift":
        tone = "warn"
        status = "visual_delta_review_minor_drift"
        label = f"Delta: {score}/100 review"
    else:
        tone = "bad"
        status = "visual_delta_manual_warning"
        label = f"Delta: {score}/100 warning"
    return {
        "status": status,
        "summary": label,
        "detail": short(clean(summary.get("warning_summary")) or clean(summary.get("next_step")), 180),
        "tone": tone,
        "score": score,
        "band": band or "not_scored",
        "worst_zone": clean(summary.get("worst_zone")),
    }


def visual_revision_summary(revision_plan: Dict[str, Any], format_id: str) -> Dict[str, str]:
    rows = revision_plan.get("revision_rows") if isinstance(revision_plan.get("revision_rows"), list) else []
    row = next(
        (item for item in rows if isinstance(item, dict) and clean(item.get("format_id")) == format_id),
        {},
    )
    if not revision_plan:
        return {
            "status": "revision_plan_not_run",
            "summary": "Revision: not planned",
            "detail": "Run render mode to create manual revision guidance.",
            "tone": "warn",
        }
    if not row:
        return {
            "status": "revision_plan_missing_format",
            "summary": "Revision: missing",
            "detail": f"No manual revision row found for {format_id}.",
            "tone": "warn",
        }
    priority = clean(row.get("revision_priority"))
    if priority == "revise_before_manual_next_step":
        tone = "bad"
        status = "manual_revision_recommended"
        summary = "Revision: recommended"
    elif priority == "inspect_before_decision":
        tone = "warn"
        status = "manual_inspection_recommended"
        summary = "Revision: inspect first"
    else:
        tone = "good"
        status = "manual_reference_check"
        summary = "Revision: reference check"
    detail = " | ".join(
        part
        for part in [
            clean(row.get("revision_focus")),
            clean(row.get("specific_manual_revisions")),
        ]
        if part
    )
    return {
        "status": status,
        "summary": summary,
        "detail": short(detail, 220),
        "tone": tone,
        "priority": priority,
        "focus": clean(row.get("revision_focus")),
        "manual_revisions": clean(row.get("specific_manual_revisions")),
        "hold_or_revise_cue": clean(row.get("hold_or_revise_cue")),
    }


def reference_review_summary(option: Dict[str, Any]) -> Dict[str, str]:
    template = clean(option.get("reference_template_id"))
    exact = option.get("reference_exact_format_match") is True
    if template and exact:
        return {
            "status": "exact_reference_match",
            "summary": "Template: exact reference",
            "detail": template,
            "tone": "good",
        }
    if template:
        return {
            "status": "derived_reference_review",
            "summary": "Template: derived review crop",
            "detail": clean(option.get("reference_derivation")) or template,
            "tone": "warn",
        }
    return {
        "status": "reference_not_linked",
        "summary": "Template: not linked",
        "detail": "No reference-pack template metadata found.",
        "tone": "bad",
    }


def reference_mockup_summary(option: Dict[str, Any]) -> Dict[str, str]:
    public_path = clean(option.get("reference_public_mockup_path"))
    layout_path = clean(option.get("reference_layout_path"))
    found_public = find_existing_input(public_path) if public_path else Path("")
    found_layout = find_existing_input(layout_path) if layout_path else Path("")
    if public_path and found_public.exists():
        return {
            "path": public_path,
            "href": href_for_path(public_path),
            "exists": "true",
            "label": "Reference mockup",
            "detail": "Approved public mockup from Templates-hsd.",
        }
    if layout_path and found_layout.exists():
        return {
            "path": layout_path,
            "href": href_for_path(layout_path),
            "exists": "true",
            "label": "Layout reference",
            "detail": "Approved layout reference from Templates-hsd.",
        }
    return {
        "path": public_path or layout_path,
        "href": "",
        "exists": "false",
        "label": "Reference missing",
        "detail": "No local reference thumbnail found.",
    }


def reference_asset_summary(option: Dict[str, Any], key: str, label: str, detail: str) -> Dict[str, str]:
    path = clean(option.get(key))
    found = find_existing_input(path) if path else Path("")
    return {
        "path": path,
        "href": href_for_path(path) if path and found.exists() else "",
        "exists": "true" if path and found.exists() else "false",
        "label": label if path and found.exists() else f"{label} missing",
        "detail": detail if path and found.exists() else f"No local {label.lower()} found.",
    }


def build_render_gallery(
    renderer: Dict[str, Any],
    qa: Dict[str, Any],
    delta: Dict[str, Any],
    revision_plan: Dict[str, Any],
    draft: Dict[str, str],
) -> List[Dict[str, Any]]:
    format_options = renderer.get("format_options", [])
    if not isinstance(format_options, list):
        format_options = []
    by_format = {
        clean(row.get("format_id")): row
        for row in format_options
        if isinstance(row, dict) and clean(row.get("format_id"))
    }
    gallery_specs = [
        {
            "format_id": "ig_feed_4x5",
            "label": "Primary feed",
            "path": "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
            "fallback_path": "render_handoff_top_packet/draft_preview.png",
            "shape": "1080x1350",
            "fit_note": "Best for the main IG feed review.",
        },
        {
            "format_id": "ig_story_9x16",
            "label": "Story",
            "path": "render_handoff_top_packet/review_drafts/draft_preview_story.png",
            "fallback_path": "",
            "shape": "1080x1920",
            "fit_note": "Use for story-safe vertical review.",
        },
        {
            "format_id": "square_feed_1x1",
            "label": "Square",
            "path": "render_handoff_top_packet/review_drafts/draft_preview_square.png",
            "fallback_path": "",
            "shape": "1080x1080",
            "fit_note": "Use when a tighter square crop is needed.",
        },
    ]
    qa_summary = qa.get("summary", {}) if isinstance(qa.get("summary"), dict) else {}
    asset_slots = renderer.get("asset_slots", [])
    if not isinstance(asset_slots, list):
        asset_slots = []
    logo_summary = render_slot_summary(asset_slots)
    photo_summary = photo_asset_summary(renderer, asset_slots)
    source_summary = source_review_summary(renderer, asset_slots)
    qa_summary_cue = qa_review_summary(qa, draft)
    stat_summary = stat_module_review_summary(renderer)
    asset_note = "Review asset checklist before approval."
    if asset_slots:
        slot_summaries = [
            f"{clean(slot.get('slot_id'))}: {clean(slot.get('status'))}"
            for slot in asset_slots
            if isinstance(slot, dict) and clean(slot.get("slot_id"))
        ]
        if slot_summaries:
            asset_note = "; ".join(slot_summaries[:3])
    out: List[Dict[str, Any]] = []
    for spec in gallery_specs:
        option = by_format.get(spec["format_id"], {})
        path = spec["path"]
        found = find_existing_input(path)
        if not found.exists() and spec.get("fallback_path"):
            fallback = find_existing_input(spec["fallback_path"])
            if fallback.exists():
                path = spec["fallback_path"]
                found = fallback
        width = clean(option.get("width")) or spec["shape"].split("x")[0]
        height = clean(option.get("height")) or spec["shape"].split("x")[-1]
        exists = found.exists()
        reference_template = clean(option.get("reference_template_id"))
        reference_derivation = clean(option.get("reference_derivation"))
        if reference_template:
            reference_note = f"Reference: {reference_template} ({reference_derivation or 'reference linked'})"
        else:
            reference_note = "Reference: not linked"
        reference_summary = reference_review_summary(option)
        delta_summary = visual_delta_summary(delta, spec["format_id"])
        revision_summary = visual_revision_summary(revision_plan, spec["format_id"])
        mockup_summary = reference_mockup_summary(option)
        public_summary = reference_asset_summary(option, "reference_public_mockup_path", "Public mockup", "Approved public mockup from Templates-hsd.")
        layout_summary = reference_asset_summary(option, "reference_layout_path", "Layout reference", "Approved layout reference from Templates-hsd.")
        out.append(
            {
                "format_id": spec["format_id"],
                "label": spec["label"],
                "shape": f"{width}x{height}",
                "fit_note": spec["fit_note"],
                "path": path,
                "exists": exists,
                "href": href_for_path(path) if exists else "",
                "review_status": "ready_for_visual_review" if exists else "missing_render",
                "qa_status": clean(first_present(qa.get("status"), draft.get("qa_status"), default="not_run")),
                "qa_summary": f"{clean(qa_summary.get('pass_count')) or '0'}/{clean(qa_summary.get('check_count')) or '0'} QA checks passed",
                "asset_note": asset_note,
                "reference_template": reference_template,
                "reference_note": reference_note,
                "reference_spec_path": clean(option.get("reference_spec_path")),
                "reference_public_mockup_path": clean(option.get("reference_public_mockup_path")),
                "reference_layout_path": clean(option.get("reference_layout_path")),
                "reference_exact_format_match": "true" if option.get("reference_exact_format_match") is True else "false",
                "reference_mockup_href": mockup_summary["href"],
                "reference_mockup_path": mockup_summary["path"],
                "reference_mockup_exists": mockup_summary["exists"],
                "reference_mockup_label": mockup_summary["label"],
                "reference_mockup_detail": mockup_summary["detail"],
                "reference_public_href": public_summary["href"],
                "reference_public_exists": public_summary["exists"],
                "reference_public_label": public_summary["label"],
                "reference_public_detail": public_summary["detail"],
                "reference_layout_href": layout_summary["href"],
                "reference_layout_exists": layout_summary["exists"],
                "reference_layout_label": layout_summary["label"],
                "reference_layout_detail": layout_summary["detail"],
                "logo_status": logo_summary["status"],
                "logo_summary": logo_summary["summary"],
                "logo_detail": logo_summary["detail"],
                "photo_status": photo_summary["status"],
                "photo_summary": photo_summary["summary"],
                "photo_detail": photo_summary["detail"],
                "photo_layout_mode": clean(option.get("athlete_photo_layout_mode")),
                "photo_layout_status": clean(option.get("athlete_photo_layout_status")),
                "photo_layout_detail": clean(option.get("athlete_photo_layout_detail")),
                "visual_mode": clean(option.get("visual_mode")),
                "hero_asset_required": clean(option.get("hero_asset_required")),
                "focal_entity_type": clean(option.get("focal_entity_type")),
                "score_lock_variant": clean(option.get("score_lock_variant")),
                "proof_strip_variant": clean(option.get("proof_strip_variant")),
                "copy_unlock_state": clean(option.get("copy_unlock_state")),
                "background_family": clean(option.get("background_family")),
                "template_fit_reason": clean(option.get("template_fit_reason")),
                "source_status": source_summary["status"],
                "source_summary": source_summary["summary"],
                "source_detail": source_summary["detail"],
                "qa_cue_status": qa_summary_cue["status"],
                "qa_cue_summary": qa_summary_cue["summary"],
                "qa_cue_detail": qa_summary_cue["detail"],
                "stat_module_status": stat_summary["status"],
                "stat_module_summary": stat_summary["summary"],
                "stat_module_detail": stat_summary["detail"],
                "visual_delta_status": delta_summary["status"],
                "visual_delta_summary": delta_summary["summary"],
                "visual_delta_detail": delta_summary["detail"],
                "visual_delta_score": delta_summary.get("score", ""),
                "visual_delta_band": delta_summary.get("band", ""),
                "visual_delta_worst_zone": delta_summary.get("worst_zone", ""),
                "visual_delta_tone": delta_summary.get("tone", "warn"),
                "revision_status": revision_summary["status"],
                "revision_summary": revision_summary["summary"],
                "revision_detail": revision_summary["detail"],
                "revision_tone": revision_summary.get("tone", "warn"),
                "revision_priority": revision_summary.get("priority", ""),
                "revision_focus": revision_summary.get("focus", ""),
                "revision_manual_revisions": revision_summary.get("manual_revisions", ""),
                "revision_hold_or_revise_cue": revision_summary.get("hold_or_revise_cue", ""),
                "template_status": reference_summary["status"],
                "template_summary": reference_summary["summary"],
                "template_detail": reference_summary["detail"],
                "cue_rows": [
                    {"label": "Template", **reference_summary},
                    {"label": "Logos", **logo_summary},
                    {"label": "Photo", **photo_summary},
                    {"label": "Source", **source_summary},
                    {"label": "Stats", **stat_summary},
                    {"label": "QA", **qa_summary_cue},
                    {"label": "Visual delta", **delta_summary},
                    {"label": "Manual revision", **revision_summary},
                ],
                "approval_scope": "manual_next_step_only_not_publish_ready",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
            }
        )
    return out


def malformed_single_cell_paste(row: Dict[str, str]) -> bool:
    draft_id = clean(row.get("decision_draft_id"))
    return bool(draft_id and "," in draft_id and not clean(row.get("source_intake_id")))


def decision_row_status(row: Dict[str, str], draft: Dict[str, Any]) -> Dict[str, Any]:
    expected_draft_id = clean(draft.get("decision_draft_id"))
    expected_source_id = clean(draft.get("source_intake_id"))
    draft_id = clean(row.get("decision_draft_id"))
    source_id = clean(row.get("source_intake_id"))
    decision = clean(row.get("operator_decision"))
    warnings: List[str] = []
    cue = "verify"

    if malformed_single_cell_paste(row):
        warnings.append("This row appears pasted as one quoted cell. Replace it with a fresh copied row pasted as plain CSV below the inbox header.")
        cue = "replace"
    if expected_draft_id and draft_id != expected_draft_id:
        warnings.append("Decision draft ID does not exactly match the latest generated draft.")
        cue = "replace"
    if expected_source_id and source_id and source_id != expected_source_id:
        warnings.append("Source intake ID does not match the latest generated draft.")
        cue = "replace"
    if decision not in {"approve_for_manual_next_step", "hold", "revise"}:
        warnings.append("Decision must be approve_for_manual_next_step, hold, or revise.")
        cue = "revise" if cue != "replace" else cue
    if not clean(row.get("operator_notes")):
        warnings.append("Operator notes are required.")
        cue = "revise" if cue == "verify" else cue
    if not clean(row.get("operator_name")):
        warnings.append("Operator name is required.")
        cue = "revise" if cue == "verify" else cue
    if not clean(row.get("reviewed_at_local")):
        warnings.append("Reviewed-at time is required.")
        cue = "revise" if cue == "verify" else cue
    if decision == "hold" and not clean(row.get("hold_reason")):
        warnings.append("Hold decisions need a hold reason.")
        cue = "revise" if cue != "replace" else cue
    if decision == "revise" and not clean(row.get("revision_request")):
        warnings.append("Revise decisions need a revision request.")
        cue = "revise" if cue != "replace" else cue
    for guardrail in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis"]:
        if clean(row.get(guardrail)).lower() not in {"", "false", "0", "no"}:
            warnings.append(f"{guardrail} must remain false.")
            cue = "hold" if cue != "replace" else cue

    if not warnings:
        cue = "verify"
        status = "ready_for_render_validation"
        next_step = "Rerun .\\hsd.cmd run -Mode render so the file-backed intake can validate this row."
    elif cue == "replace":
        status = "replace_row"
        next_step = "Delete or replace this inbox row, copy a fresh row from the Decision tab, paste below the header, then rerun render."
    elif cue == "hold":
        status = "hold"
        next_step = "Hold this row until unsafe guardrail values are corrected."
    else:
        status = "revise_row"
        next_step = "Fill the missing fields in the panel, copy the row again, paste below the inbox header, then rerun render."

    return {
        "status": status,
        "cue": cue,
        "warnings": warnings,
        "warning_count": len(warnings),
        "next_step": next_step,
    }


def build_decision_history(
    inbox_rows: List[Dict[str, str]],
    intake_rows: List[Dict[str, str]],
    draft: Dict[str, Any],
) -> List[Dict[str, Any]]:
    intake_by_draft = {clean(row.get("decision_draft_id")): row for row in intake_rows if clean(row.get("decision_draft_id"))}
    history: List[Dict[str, Any]] = []
    for index, row in enumerate(inbox_rows, start=1):
        status = decision_row_status(row, draft)
        draft_id = clean(row.get("decision_draft_id"))
        intake = intake_by_draft.get(draft_id, {})
        validation_status = clean(intake.get("validation_status"))
        validation_issue = clean(intake.get("validation_issue"))
        if not validation_status and status["status"] != "ready_for_render_validation":
            validation_status = status["status"]
        history.append(
            {
                "row_number": index,
                "decision_draft_id": short(draft_id, 96),
                "source_intake_id": short(clean(row.get("source_intake_id")), 72),
                "operator_decision": clean(row.get("operator_decision")) or "missing",
                "operator_name": clean(row.get("operator_name")) or "missing",
                "reviewed_at_local": clean(row.get("reviewed_at_local")) or "missing",
                "validation_status": validation_status or "needs_render_validation",
                "validation_issue": validation_issue or "; ".join(status["warnings"]) or status["next_step"],
                "cue": status["cue"],
                "row_status": status["status"],
                "warning_count": status["warning_count"],
                "next_step": status["next_step"],
            }
        )
    return history


def build_visual_qa_cues(qa: Dict[str, Any]) -> List[Dict[str, str]]:
    checks = qa.get("checks") if isinstance(qa.get("checks"), list) else []
    wanted = [
        "premium_editorial_route_limit_review",
        "premium_editorial_clutter_scan",
        "headline_text_zone",
        "score_team_text_zone",
        "context_text_zone",
        "lower_module_text_zone",
        "player_ledger_readability",
        "team_logo_review_status",
        "approval_guardrails",
    ]
    labels = {
        "premium_editorial_route_limit_review": "Premium route limit",
        "premium_editorial_clutter_scan": "Premium editorial clutter scan",
        "headline_text_zone": "Title contrast and fit",
        "score_team_text_zone": "Score/team readability",
        "context_text_zone": "Context row readability",
        "lower_module_text_zone": "Lower-module readability",
        "player_ledger_readability": "Player ledger readability",
        "team_logo_review_status": "Logo readiness",
        "approval_guardrails": "Approval guardrails",
    }
    by_id = {clean(row.get("check_id")): row for row in checks if isinstance(row, dict)}
    cues: List[Dict[str, str]] = []
    for check_id in wanted:
        row = by_id.get(check_id)
        if not row:
            continue
        result = clean(row.get("qa_result")) or ("pass" if row.get("passed") else "hold")
        passed = row.get("passed") is True or result.startswith("pass")
        cues.append(
            {
                "check_id": check_id,
                "label": labels.get(check_id, clean(row.get("check_label")) or check_id),
                "result": result,
                "tone": "good" if passed else "warn",
                "evidence": short(clean(row.get("evidence")), 260),
            }
        )
    return cues


def operator_decision_ui_panel() -> Dict[str, Any]:
    renderer = read_json("manual_review_renderer_manifest.json")
    delta = read_json("render_visual_delta_manifest.json")
    revision_plan = read_json("render_visual_revision_plan.json")
    qa = read_json("manual_visual_qa_manifest.json")
    approval = read_json("manual_visual_qa_approval_intake.json")
    draft_rows = read_csv("manual_visual_qa_operator_decision_draft.csv")
    template_rows = read_csv("manual_visual_qa_operator_decision_template.csv")
    intake = read_json("manual_visual_qa_operator_decision_intake.json")
    intake_rows = read_csv("manual_visual_qa_operator_decision_intake.csv")
    staging_rows = read_csv("manual_post_approval_render_staging.csv")
    starter = read_json("manual_visual_qa_operator_decision_inbox_starter.json")
    inbox_rows = read_csv("operator/inbox/manual_visual_qa_operator_decisions.csv")
    draft = draft_rows[0] if draft_rows else {}
    intake_row = intake_rows[0] if intake_rows else {}
    staging = staging_rows[0] if staging_rows else {}
    history = build_decision_history(inbox_rows, intake_rows, draft)
    invalid_history = [row for row in history if row.get("cue") in {"replace", "revise", "hold"} or str(row.get("validation_status", "")).startswith("invalid")]
    valid_history = [row for row in history if row.get("validation_status") == "valid_operator_decision" or row.get("row_status") == "ready_for_render_validation"]
    preview_relative = "render_handoff_top_packet/draft_preview.png"
    preview_file = find_existing_input(preview_relative)
    preview_src = href_for_path(preview_relative) if preview_file.exists() else clean(first_present(draft.get("preview_path"), renderer.get("preview_path")))
    qa_summary = qa.get("summary", {}) if isinstance(qa.get("summary"), dict) else {}
    dimensions = qa.get("dimensions", {}) if isinstance(qa.get("dimensions"), dict) else {}
    template_choices = [
        {
            "decision": clean(row.get("operator_decision")),
            "row_type": clean(row.get("template_row_type")),
            "copy_status": clean(row.get("copy_status")),
        }
        for row in template_rows
    ]
    status = clean(first_present(intake.get("status"), intake_row.get("validation_status"), draft.get("copy_status"), default="not_ready"))
    if invalid_history:
        next_step = clean(invalid_history[0].get("next_step")) or "Fix the latest inbox row, then rerun .\\hsd.cmd run -Mode render."
    elif not draft_rows:
        next_step = "Run .\\hsd.cmd run -Mode render to create the draft and QA reports."
    elif not find_existing_input("operator/inbox/manual_visual_qa_operator_decisions.csv").exists():
        next_step = "Run .\\hsd.cmd run -Mode decision-inbox to create the local inbox shell."
    elif not inbox_rows:
        next_step = "Use the panel controls to build one row, copy it into the local inbox, then rerun render."
    else:
        next_step = clean(staging.get("next_safe_action")) or "Rerun .\\hsd.cmd run -Mode render to validate the local inbox."
    return {
        "panel_status": status,
        "preview_src": preview_src,
        "preview_exists": preview_file.exists(),
        "preview_path": preview_file.as_posix() if preview_file.exists() else clean(first_present(draft.get("preview_path"), renderer.get("preview_path"))),
        "renderer_status": clean(renderer.get("status")),
        "qa_status": clean(first_present(qa.get("status"), draft.get("qa_status"), intake_row.get("qa_status"))),
        "approval_status": clean(first_present(qa.get("approval_status"), approval.get("approval_status"), intake.get("approval_status"), default="not_approved")),
        "automated_hold_count": clean(first_present(draft.get("automated_hold_count"), intake_row.get("automated_hold_count"), qa_summary.get("hold_count"), default="0")),
        "qa_pass_count": clean(qa_summary.get("pass_count")),
        "qa_check_count": clean(qa_summary.get("check_count")),
        "qa_cues": build_visual_qa_cues(qa),
        "dimensions": f"{clean(dimensions.get('width')) or '0'}x{clean(dimensions.get('height')) or '0'}",
        "decision_draft": draft,
        "render_gallery": build_render_gallery(renderer, qa, delta, revision_plan, draft),
        "template_choices": template_choices,
        "file_shortcuts": [
            file_shortcut("Draft preview", "render_handoff_top_packet/draft_preview.png", "Open the rendered image before making any decision."),
            file_shortcut("Visual delta report", "render_visual_delta_report.md", "Review mockup/layout drift warnings before deciding."),
            file_shortcut("Visual delta data", "render_visual_delta.csv", "See per-format public mockup and layout comparison scores."),
            file_shortcut("Revision plan", "render_visual_revision_plan.md", "Use the worst-zone guidance to decide what to revise manually."),
            file_shortcut("Revision plan data", "render_visual_revision_plan.csv", "Review per-format manual revision recommendations."),
            file_shortcut("Next-level editorial QA", "render_next_level_editorial_qa.md", "Check premium blockers and the action-photo return path before another renderer pass."),
            file_shortcut("Next-level editorial QA data", "render_next_level_editorial_qa.csv", "Review per-gate blockers, evidence, and manual return paths."),
            file_shortcut("QA report", "manual_visual_qa_report.md", "Read visual QA findings and guardrails."),
            file_shortcut("QA checklist", "manual_visual_qa_checklist.csv", "Check pass/hold rows behind the QA summary."),
            file_shortcut("Copy sheet", "render_handoff_top_packet/copy_sheet.md", "Confirm the visible copy and source-safe summary."),
            file_shortcut("Source proof", "render_handoff_top_packet/source_proof.md", "Confirm the source artifact used for the draft."),
            file_shortcut("Decision draft CSV", "manual_visual_qa_operator_decision_draft.csv", "Use this as the generated row contract."),
            file_shortcut("Decision template CSV", "manual_visual_qa_operator_decision_template.csv", "Copy-only examples for approve, hold, or revise."),
            file_shortcut("Decision inbox", "operator/inbox/manual_visual_qa_operator_decisions.csv", "Paste the final operator row below the header."),
            file_shortcut("Decision intake", "manual_visual_qa_operator_decision_intake.csv", "See validation results after rerunning render."),
            file_shortcut("Staging report", "manual_post_approval_render_staging.csv", "Review the next-step staging lane after validation."),
        ],
        "decision_history": history,
        "history_issue_count": len(invalid_history),
        "has_valid_decision": bool(valid_history) and not invalid_history,
        "valid_decision_summary": valid_history[0] if valid_history else {},
        "intake_status": clean(intake.get("status")),
        "validation_status": clean(intake_row.get("validation_status")),
        "validation_issue": clean(intake_row.get("validation_issue")),
        "staging_lane": clean(staging.get("staging_lane")),
        "staging_next_safe_action": clean(staging.get("next_safe_action")),
        "inbox_path": "operator/inbox/manual_visual_qa_operator_decisions.csv",
        "inbox_exists": find_existing_input("operator/inbox/manual_visual_qa_operator_decisions.csv").exists(),
        "inbox_rows": len(inbox_rows),
        "starter_status": clean(starter.get("status")),
        "next_step": next_step,
        "guardrails": {
            "file_backed_manual_approval": True,
            "writes_in_browser": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "copy_to_publish_lane": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }


def athlete_photo_score_tone(row: Dict[str, str]) -> str:
    score = as_int(row.get("crop_readiness_score"))
    status = clean(row.get("variant_status"))
    if status != "review_variant_ready":
        return "warn"
    if score >= 90:
        return "good"
    if score >= 70:
        return "neutral"
    return "warn"


def athlete_identity_audit_by_athlete(payload: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    issues = payload.get("issues") if isinstance(payload.get("issues"), list) else []
    out: Dict[str, List[Dict[str, str]]] = {}
    for issue_row in issues:
        if not isinstance(issue_row, dict):
            continue
        athlete_id = clean(issue_row.get("athlete_id"))
        if athlete_id:
            out.setdefault(athlete_id, []).append({str(key): clean(value) for key, value in issue_row.items()})
    return out


def athlete_identity_audit_summary(athlete_id: str, audit_by_athlete: Dict[str, List[Dict[str, str]]]) -> Dict[str, str]:
    issues = audit_by_athlete.get(clean(athlete_id), [])
    if not issues:
        return {
            "identity_review_status": "identity_audit_clear_or_not_run",
            "identity_review_tone": "warn",
            "identity_issue_count": "0",
            "identity_high_issue_count": "0",
            "identity_issue_codes": "",
            "identity_evidence": "No per-athlete audit issue found in the latest run; still verify identity by eye.",
        }
    high = [row for row in issues if clean(row.get("severity")) in {"critical", "high"}]
    codes = sorted({clean(row.get("issue_code")) for row in issues if clean(row.get("issue_code"))})
    evidence = "; ".join(short(clean(row.get("evidence")), 90) for row in issues[:3] if clean(row.get("evidence")))
    if high:
        status = "hold_identity_review_required"
        tone = "bad" if any(clean(row.get("severity")) == "critical" for row in high) else "warn"
    else:
        status = "identity_review_required"
        tone = "warn"
    return {
        "identity_review_status": status,
        "identity_review_tone": tone,
        "identity_issue_count": str(len(issues)),
        "identity_high_issue_count": str(len(high)),
        "identity_issue_codes": ", ".join(codes[:4]),
        "identity_evidence": evidence or "Audit issue present; review the athlete identity audit.",
    }


def athlete_identity_resolution_by_athlete(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        if athlete_id:
            out[athlete_id] = {str(key): clean(value) for key, value in row.items()}
    return out


def identity_guardrail_false(row: Dict[str, str], field: str) -> bool:
    return clean(row.get(field)).lower() in {"", "0", "false", "no", "n"}


def identity_resolution_is_cleared(row: Dict[str, str]) -> bool:
    decision = clean(row.get("operator_decision"))
    status = clean(row.get("issue_resolution_status"))
    verified_identity = clean(row.get("identity_verified")).lower() == "yes"
    verified_provider = clean(row.get("provider_player_id_verified")).lower() == "yes" or bool(clean(row.get("backfill_provider_player_id")))
    return (
        decision == "identity_verified_approved_for_review_renders"
        and status in {"resolved", "closed_with_evidence", "identity_verified"}
        and verified_identity
        and verified_provider
        and bool(clean(row.get("approved_source_url")))
        and bool(clean(row.get("operator_name")))
        and bool(clean(row.get("reviewed_at_local")))
        and bool(clean(row.get("operator_notes")))
        and all(identity_guardrail_false(row, field) for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis"])
    )


def athlete_identity_candidates_by_athlete(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        if athlete_id and athlete_id not in out:
            out[athlete_id] = {str(key): clean(value) for key, value in row.items()}
    return out


def athlete_identity_backfills_by_athlete(rows: Iterable[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        if athlete_id:
            out.setdefault(athlete_id, []).append({str(key): clean(value) for key, value in row.items()})
    return out


def athlete_identity_review_packet_rows(rows: Iterable[Dict[str, str]], *, limit: int = 8) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        if not athlete_id:
            continue
        normalized.append({str(key): clean(value) for key, value in row.items()})
    return sorted(
        normalized,
        key=lambda row: (
            clean(row.get("identity_hold")).lower() != "true",
            clean(row.get("default_approval_present")).lower() != "true",
            clean(row.get("team_id")),
            clean(row.get("display_name")),
            clean(row.get("athlete_id")),
        ),
    )[:limit]


def athlete_identity_review_packet_team_summary(rows: Iterable[Dict[str, str]], *, limit: int = 12) -> List[Dict[str, str]]:
    teams: Dict[str, Dict[str, int]] = {}
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        team_id = clean(row.get("team_id")) or "unknown_team"
        if not athlete_id:
            continue
        summary = teams.setdefault(team_id, {"rows": 0, "holds": 0, "defaults": 0, "high": 0})
        summary["rows"] += 1
        if clean(row.get("identity_hold")).lower() == "true":
            summary["holds"] += 1
        if clean(row.get("default_approval_present")).lower() == "true":
            summary["defaults"] += 1
        if clean(row.get("highest_severity")).lower() in {"critical", "high"}:
            summary["high"] += 1
    ranked = sorted(
        teams.items(),
        key=lambda item: (-item[1]["holds"], -item[1]["defaults"], -item[1]["high"], item[0]),
    )
    return [
        {
            "team_id": team_id,
            "packet_rows": str(values["rows"]),
            "identity_hold_rows": str(values["holds"]),
            "default_approval_rows": str(values["defaults"]),
            "high_severity_rows": str(values["high"]),
        }
        for team_id, values in ranked[:limit]
    ]


def ranked_field_counts(rows: Iterable[Dict[str, str]], field: str, *, limit: int = 6, fallback: str = "unknown") -> List[Dict[str, str]]:
    counts: Dict[str, int] = {}
    for row in rows:
        label = clean(row.get(field)) or fallback
        counts[label] = counts.get(label, 0) + 1
    return [
        {"label": label, "rows": str(count)}
        for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def athlete_identity_closure_summary(
    closure_rows: Iterable[Dict[str, str]],
    backfill_rows: Iterable[Dict[str, str]],
) -> Dict[str, Any]:
    closures = [dict(row) for row in closure_rows]
    backfills = [dict(row) for row in backfill_rows]
    high_rows = sum(1 for row in closures if clean(row.get("severity")).lower() in {"critical", "high"})
    blank_closure_decisions = sum(1 for row in closures if not clean(row.get("operator_closure_decision")))
    manual_backfill_rows = sum(1 for row in backfills if clean(row.get("backfill_status")).lower() == "manual_review_required")
    blank_backfill_decisions = sum(1 for row in backfills if not clean(row.get("operator_decision")))
    if closures:
        next_step = "Open the issue closure template, handle high-severity rows first, and keep blank rows held until evidence is recorded."
    elif backfills:
        next_step = "Open the provider ID backfill template only after identity proof exists; these rows do not clear photo-first rendering."
    else:
        next_step = "Run the identity closure packet generator after athlete identity audit packets exist."
    return {
        "identity_closure_high_rows": high_rows,
        "identity_closure_blank_decisions": blank_closure_decisions,
        "identity_provider_backfill_manual_review_rows": manual_backfill_rows,
        "identity_provider_backfill_blank_decisions": blank_backfill_decisions,
        "identity_closure_severity_counts": ranked_field_counts(closures, "severity"),
        "identity_closure_issue_counts": ranked_field_counts(closures, "issue_code"),
        "identity_provider_backfill_status_counts": ranked_field_counts(backfills, "backfill_status"),
        "identity_provider_backfill_target_counts": ranked_field_counts(backfills, "target_csv"),
        "identity_closure_next_step": next_step,
    }


def athlete_identity_candidate_summary(
    athlete_id: str,
    candidate_by_athlete: Dict[str, Dict[str, str]],
    backfills_by_athlete: Dict[str, List[Dict[str, str]]],
) -> Dict[str, Any]:
    candidate = dict(candidate_by_athlete.get(clean(athlete_id), {}))
    backfills = [dict(row) for row in backfills_by_athlete.get(clean(athlete_id), [])[:4]]
    proposed_ids = [
        clean(row.get("proposed_value"))
        for row in backfills
        if clean(row.get("target_field")) == "provider_player_id" and clean(row.get("proposed_value"))
    ]
    provider_candidate = clean(candidate.get("provider_player_id")) or (proposed_ids[0] if proposed_ids else "")
    candidate_status = "no_resolution_candidate"
    if candidate:
        candidate_status = "hold_until_source_backed_decision"
        if clean(candidate.get("highest_severity")) not in {"critical", "high"}:
            candidate_status = "candidate_ready"
    return {
        "identity_candidate_status": candidate_status,
        "identity_resolution_candidate": candidate,
        "identity_provider_backfill_rows": backfills,
        "identity_provider_candidate": provider_candidate,
        "identity_provider_backfill_summary": "; ".join(
            f"{clean(row.get('target_csv'))}:{clean(row.get('target_field'))}->{clean(row.get('proposed_value'))}"
            for row in backfills[:3]
            if clean(row.get("proposed_value"))
        ),
    }


def athlete_identity_resolution_summary(athlete_id: str, rows_by_athlete: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    row = rows_by_athlete.get(clean(athlete_id), {})
    if not row:
        return {
            "identity_resolution_status": "resolution_not_recorded",
            "identity_resolution_tone": "warn",
            "identity_resolution_decision": "",
            "identity_resolution_evidence_url": "",
            "identity_resolution_next_step": "Fill a source-backed row in operator/inbox/wnba_athlete_identity_resolution.csv before renderer photo use.",
        }
    decision = clean(row.get("operator_decision"))
    evidence = clean(row.get("approved_source_url"))
    cleared = identity_resolution_is_cleared(row)
    tone = "good" if cleared else "bad" if decision in {"hold_identity", "revise_asset"} else "warn"
    review_status = "identity_resolution_cleared_for_review_renders" if cleared else ""
    review_tone = "good" if cleared else ""
    next_step = "Renderer may use this photo only for review drafts." if cleared else "Keep photo-first rendering held until evidence, operator, and resolution fields are complete."
    if decision == "hold_identity":
        next_step = "Identity remains held by operator decision; photo-first rendering stays blocked."
    elif decision == "revise_asset":
        next_step = "Asset revision is required before this athlete photo can be reconsidered."
    elif decision == "backfill_provider_id_only":
        next_step = "Provider ID backfill is recorded, but identity is still held until a verified source-backed decision is saved."
    return {
        "identity_resolution_status": "resolution_cleared_for_review_renders" if cleared else "resolution_incomplete_or_hold",
        "identity_resolution_tone": tone,
        "identity_resolution_decision": decision,
        "identity_resolution_evidence_url": evidence,
        "identity_resolution_next_step": next_step,
        "identity_resolution_operator": clean(row.get("operator_name")),
        "identity_resolution_reviewed_at_local": clean(row.get("reviewed_at_local")),
        "identity_resolution_review_status": review_status,
        "identity_resolution_review_tone": review_tone,
    }


def athlete_photo_onboarding_row_payload(
    row: Dict[str, str],
    audit_by_athlete: Dict[str, List[Dict[str, str]]],
    resolution_by_athlete: Dict[str, Dict[str, str]],
    candidate_by_athlete: Dict[str, Dict[str, str]],
    backfills_by_athlete: Dict[str, List[Dict[str, str]]],
    *,
    featured: bool = False,
) -> Dict[str, Any]:
    athlete_id = clean(row.get("athlete_id"))
    team_id = clean(row.get("team_id"))
    contact_sheet_path = clean(row.get("contact_sheet_path"))
    recommended_path = clean(row.get("recommended_review_variant_path"))
    source_path = clean(row.get("source_headshot_path"))
    audit = athlete_identity_audit_summary(athlete_id, audit_by_athlete)
    resolution = athlete_identity_resolution_summary(athlete_id, resolution_by_athlete)
    if clean(resolution.get("identity_resolution_review_status")) == "identity_resolution_cleared_for_review_renders":
        audit["identity_review_status"] = "identity_resolution_cleared_for_review_renders"
        audit["identity_review_tone"] = "good"
    return {
        "athlete_id": athlete_id,
        "athlete_name": clean(row.get("athlete_name")) or athlete_id.replace("_", " ").title(),
        "team_id": team_id,
        "source_headshot_path": source_path,
        "source_headshot_href": href_for_path(source_path) if source_path and find_existing_input(source_path).exists() else "",
        "contact_sheet_path": contact_sheet_path,
        "contact_sheet_href": href_for_path(contact_sheet_path) if contact_sheet_path and find_existing_input(contact_sheet_path).exists() else "",
        "feed_variant_path": clean(row.get("feed_variant_path")),
        "feed_variant_href": href_for_path(row.get("feed_variant_path", "")) if clean(row.get("feed_variant_path")) and Path(clean(row.get("feed_variant_path"))).exists() else "",
        "story_variant_path": clean(row.get("story_variant_path")),
        "story_variant_href": href_for_path(row.get("story_variant_path", "")) if clean(row.get("story_variant_path")) and Path(clean(row.get("story_variant_path"))).exists() else "",
        "square_variant_path": clean(row.get("square_variant_path")),
        "square_variant_href": href_for_path(row.get("square_variant_path", "")) if clean(row.get("square_variant_path")) and Path(clean(row.get("square_variant_path"))).exists() else "",
        "recommended_review_variant_path": recommended_path,
        "recommended_review_variant_href": href_for_path(recommended_path) if recommended_path and Path(recommended_path).exists() else "",
        "variant_status": clean(row.get("variant_status")) or "not_generated",
        "crop_readiness_score": clean(row.get("crop_readiness_score")) or "0",
        "crop_readiness_notes": clean(row.get("crop_readiness_notes")) or "Identity still requires human review.",
        "renderer_review_candidate": clean(row.get("renderer_review_candidate")),
        "approval_scope": clean(row.get("approval_scope")) or "review_only_derivative_from_approved_headshot",
        "review_only_policy": clean(row.get("review_only_policy")) or "derived_variant_does_not_approve_move_publish_or_mark_publish_ready",
        "publish_ready": clean(row.get("publish_ready")) or "false",
        "auto_approval": clean(row.get("auto_approval")) or "false",
        "auto_publish": clean(row.get("auto_publish")) or "false",
        "move_files": clean(row.get("move_files")) or "false",
        "paid_apis": clean(row.get("paid_apis")) or "false",
        "featured": featured,
        "tone": athlete_photo_score_tone(row),
        **audit,
        **resolution,
        **athlete_identity_candidate_summary(athlete_id, candidate_by_athlete, backfills_by_athlete),
        "decision_cue": "Verify the athlete by eye against trusted source evidence before using this crop in a render.",
    }


def athlete_photo_onboarding_panel(renderer: Dict[str, Any]) -> Dict[str, Any]:
    manifest = read_json("athlete_photo_onboarding/athlete_photo_onboarding_manifest.json")
    metadata_json = read_json("athlete_photo_onboarding/athlete_photo_onboarding_metadata.json")
    metadata_rows = read_csv("athlete_photo_onboarding/athlete_photo_onboarding_metadata.csv")
    decision_rows = read_csv("athlete_photo_onboarding/athlete_photo_onboarding_decision_template.csv")
    identity_audit = read_json("data/asset_registry/wnba/athlete_identity_audit.json")
    identity_resolution = read_json("data/asset_registry/wnba/athlete_identity_resolution_manifest.json")
    identity_resolution_report = identity_resolution.get("report") if isinstance(identity_resolution.get("report"), dict) else {}
    identity_closure_packet = read_json("data/asset_registry/wnba/athlete_identity_closure_packet.json")
    identity_closure_report = identity_closure_packet.get("report") if isinstance(identity_closure_packet.get("report"), dict) else {}
    identity_resolution_rows = read_csv("operator/inbox/wnba_athlete_identity_resolution.csv")
    identity_resolution_by_id = athlete_identity_resolution_by_athlete(identity_resolution_rows)
    identity_candidate_rows = read_csv("data/asset_registry/wnba/athlete_identity_resolution_candidates.csv")
    identity_review_packet_rows = read_csv("data/asset_registry/wnba/athlete_identity_review_packet.csv")
    identity_review_packets = athlete_identity_review_packet_rows(identity_review_packet_rows)
    identity_review_packet_teams = athlete_identity_review_packet_team_summary(identity_review_packet_rows)
    identity_packet_cue = packet_freshness_cue(
        "data/asset_registry/wnba/athlete_identity_review_packet.csv",
        len(identity_review_packet_rows),
        RUN_COMMANDS["data/asset_registry/wnba/athlete_identity_review_packet.csv"],
        context="WNBA athlete identity review",
    )
    athlete_contact_manifest = read_json("data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_manifest.json")
    athlete_contact_rows = read_csv("data/asset_registry/wnba/wnba_athlete_photo_contact_sheet.csv")
    athlete_contact_intake_rows = read_csv("data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv")
    athlete_contact_cue = packet_freshness_cue(
        "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet.csv",
        len(athlete_contact_rows),
        RUN_COMMANDS["data/asset_registry/wnba/wnba_athlete_photo_contact_sheet.csv"],
        context="WNBA athlete photo contact sheet",
    )
    identity_candidate_by_id = athlete_identity_candidates_by_athlete(identity_candidate_rows)
    identity_backfill_rows = read_csv("data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv")
    identity_backfills_by_id = athlete_identity_backfills_by_athlete(identity_backfill_rows)
    identity_closure_rows = read_csv("data/asset_registry/wnba/athlete_identity_issue_closure_template.csv")
    identity_closure_summary_payload = athlete_identity_closure_summary(identity_closure_rows, identity_backfill_rows)
    identity_audit_report = identity_audit.get("report") if isinstance(identity_audit.get("report"), dict) else {}
    identity_audit_by_id = athlete_identity_audit_by_athlete(identity_audit)
    athletes_payload = metadata_json.get("athletes") if isinstance(metadata_json.get("athletes"), dict) else {}
    if athletes_payload and not metadata_rows:
        metadata_rows = [dict(row) for row in athletes_payload.values() if isinstance(row, dict)]

    content_module = renderer.get("content_module") if isinstance(renderer.get("content_module"), dict) else {}
    featured_id = clean(content_module.get("athlete_photo_athlete_id"))
    featured_name = clean(content_module.get("player_name"))
    featured_source_path = clean(content_module.get("athlete_photo_path"))
    if not featured_id and featured_name:
        featured_id = clean(re.sub(r"[^a-z0-9]+", "_", featured_name.lower())).strip("_")

    ordered: List[Dict[str, str]] = []
    seen: set[str] = set()
    featured_row_id = ""
    for row in metadata_rows:
        athlete_id = clean(row.get("athlete_id"))
        if not athlete_id:
            continue
        source_matches = featured_source_path and clean(row.get("source_headshot_path")) == featured_source_path
        id_matches = featured_id and (athlete_id == featured_id or athlete_id.endswith(featured_id) or featured_id.endswith(athlete_id))
        if source_matches or id_matches:
            ordered.insert(0, row)
            seen.add(athlete_id)
            featured_row_id = athlete_id
        elif athlete_id not in seen:
            ordered.append(row)
            seen.add(athlete_id)

    if featured_id and not featured_row_id and (not ordered or clean(ordered[0].get("athlete_id")) != featured_id):
        for row in metadata_rows:
            if clean(row.get("athlete_id")).endswith(featured_id) or featured_id.endswith(clean(row.get("athlete_id"))):
                ordered = [row] + [item for item in ordered if clean(item.get("athlete_id")) != clean(row.get("athlete_id"))]
                featured_row_id = clean(row.get("athlete_id"))
                break

    review_rows = [
        athlete_photo_onboarding_row_payload(
            row,
            identity_audit_by_id,
            identity_resolution_by_id,
            identity_candidate_by_id,
            identity_backfills_by_id,
            featured=(index == 0 and bool(featured_row_id)),
        )
        for index, row in enumerate(ordered[:24])
    ]
    source_rows = as_int(manifest.get("source_rows")) or len(metadata_rows)
    ready_rows = as_int(manifest.get("review_variant_ready")) or sum(1 for row in metadata_rows if clean(row.get("variant_status")) == "review_variant_ready")
    needs_review = as_int(manifest.get("review_variant_needs_crop_review")) or max(0, source_rows - ready_rows)
    contact_sheets = as_int(manifest.get("contact_sheets")) or len({clean(row.get("contact_sheet_path")) for row in metadata_rows if clean(row.get("contact_sheet_path"))})
    if not metadata_rows:
        if identity_review_packet_rows:
            panel_status = "identity_resolution_required"
            next_step = "Open data/asset_registry/wnba/athlete_identity_review_packet.csv and resolve hold-first default/suspicious athlete-photo rows before photo-first renders."
        else:
            panel_status = "not_run"
            next_step = "Run .\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py to create review-only contact sheets."
    elif featured_row_id and review_rows:
        if clean(review_rows[0].get("identity_resolution_status")) == "resolution_cleared_for_review_renders":
            panel_status = "identity_resolution_cleared_review_only"
            next_step = "Renderer can use the photo for review drafts only; still complete visual QA before any next step."
        elif clean(review_rows[0].get("identity_review_status")).startswith("hold_"):
            panel_status = "hold_identity_review_required"
            next_step = "Hold this athlete crop until the identity audit issue is resolved with human evidence in the operator identity inbox."
        else:
            panel_status = "identity_review_required"
            next_step = "Open the contact sheet and source headshot, then record approve, hold, or revise with identity notes."
    else:
        panel_status = "review_queue_ready"
        next_step = "Choose an athlete row, verify identity and crop by eye, then copy a review-only decision row."
    return {
        "panel_status": panel_status,
        "manifest_status": clean(manifest.get("status")) or "not_run",
        "source_rows": source_rows,
        "review_variant_ready": ready_rows,
        "review_variant_needs_crop_review": needs_review,
        "contact_sheets": contact_sheets,
        "decision_template_rows": len(decision_rows),
        "identity_audit_status": clean(identity_audit_report.get("status")) or "not_run",
        "identity_audit_issue_rows": as_int(identity_audit_report.get("issue_rows")),
        "identity_audit_high_rows": as_int((identity_audit_report.get("severity_counts") or {}).get("high")) if isinstance(identity_audit_report.get("severity_counts"), dict) else 0,
        "identity_audit_critical_rows": as_int((identity_audit_report.get("severity_counts") or {}).get("critical")) if isinstance(identity_audit_report.get("severity_counts"), dict) else 0,
        "identity_resolution_status": clean(identity_resolution_report.get("status")) or "not_run",
        "identity_resolution_candidate_rows": as_int(identity_resolution_report.get("candidate_rows")),
        "identity_review_packet_rows": len(identity_review_packet_rows),
        "identity_review_packet_hold_rows": sum(1 for row in identity_review_packet_rows if clean(row.get("identity_hold")).lower() == "true"),
        "identity_review_packet_default_rows": sum(1 for row in identity_review_packet_rows if clean(row.get("default_approval_present")).lower() == "true"),
        "identity_review_packet_freshness_status": identity_packet_cue["status"],
        "identity_review_packet_freshness_detail": identity_packet_cue["detail"],
        "identity_review_packet_refresh_command": identity_packet_cue["run_command"],
        "athlete_contact_sheet_status": clean(athlete_contact_manifest.get("status")) or "not_run",
        "athlete_contact_sheet_rows": as_int(athlete_contact_manifest.get("athlete_rows")) or len(athlete_contact_rows),
        "athlete_contact_sheet_teams": as_int(athlete_contact_manifest.get("team_rows")),
        "athlete_contact_sheet_local_headshots": as_int(athlete_contact_manifest.get("local_headshots_present")),
        "athlete_contact_sheet_intake_rows": len(athlete_contact_intake_rows),
        "athlete_contact_sheet_freshness_status": athlete_contact_cue["status"],
        "athlete_contact_sheet_freshness_detail": athlete_contact_cue["detail"],
        "athlete_contact_sheet_refresh_command": athlete_contact_cue["run_command"],
        "identity_review_packets": identity_review_packets,
        "identity_review_packet_teams": identity_review_packet_teams,
        "identity_resolution_inbox_rows": len(identity_resolution_rows),
        "identity_closure_status": clean(identity_closure_report.get("status")) or "not_run",
        "identity_closure_rows": as_int(identity_closure_report.get("closure_rows")) or len(identity_closure_rows),
        "identity_provider_backfill_rows": as_int(identity_closure_report.get("backfill_rows")) or len(identity_backfill_rows),
        **identity_closure_summary_payload,
        "featured_athlete_id": featured_id,
        "featured_athlete_name": featured_name,
        "review_rows": review_rows,
        "file_shortcuts": [
            file_shortcut("Onboarding report", "athlete_photo_onboarding/athlete_photo_onboarding_report.md", "Read the generated review-only onboarding summary."),
            file_shortcut("Contact sheet index", "athlete_photo_onboarding/athlete_photo_contact_sheet_index.md", "Open team contact sheets before choosing any crop."),
            file_shortcut("Metadata CSV", "athlete_photo_onboarding/athlete_photo_onboarding_metadata.csv", "Review crop scores, source paths, and policy fields."),
            file_shortcut("Decision template CSV", "athlete_photo_onboarding/athlete_photo_onboarding_decision_template.csv", "Use this as the copy-safe row contract."),
            file_shortcut("Manifest", "athlete_photo_onboarding/athlete_photo_onboarding_manifest.json", "Check the generated run status and guardrails."),
            file_shortcut("WNBA identity audit", "data/asset_registry/wnba/athlete_identity_audit.md", "Review identity provenance risks before trusting any athlete crop."),
            file_shortcut("WNBA athlete photo contact sheets", "data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_index.md", "Open per-team local headshot boards with official roster/profile source candidates."),
            file_shortcut("WNBA athlete photo review intake", "data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv", "Human-edited approve/hold/revise worksheet; this generator does not apply decisions."),
            file_shortcut("WNBA identity audit data", "data/asset_registry/wnba/athlete_identity_audit.csv", "See per-athlete identity issue rows and evidence."),
            file_shortcut("Identity resolution workflow", "data/asset_registry/wnba/athlete_identity_resolution_workflow.md", "Follow the manual steps to close or hold identity issues."),
            file_shortcut("Identity review packet", "data/asset_registry/wnba/athlete_identity_review_packet.csv", "Start here for hold-first default/suspicious athlete-photo review rows."),
            file_shortcut("Identity resolution template", "data/asset_registry/wnba/athlete_identity_resolution_template.csv", "Copy rows from here into the operator inbox after source verification."),
            file_shortcut("Identity resolution inbox", "operator/inbox/wnba_athlete_identity_resolution.csv", "Human-filled source evidence row; renderer reads this file only."),
            file_shortcut("Identity closure packet", "data/asset_registry/wnba/athlete_identity_closure_packet.md", "Use this deeper worksheet to close audit rows and plan provider ID backfills."),
            file_shortcut("Issue closure template", "data/asset_registry/wnba/athlete_identity_issue_closure_template.csv", "Review-only closure rows; does not edit the registry."),
            file_shortcut("Provider ID backfill template", "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv", "Manual provider-ID edit plan only after identity proof."),
        ],
        "next_step": next_step,
        "guardrails": {
            "review_only": True,
            "identity_human_verification_required": True,
            "writes_in_browser": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "paid_apis": False,
        },
    }


def missing_artifact_detail(path: str) -> str:
    command = RUN_COMMANDS.get(path, "")
    if command:
        return f"Create with `{command}`"
    return "Not created in this run"


def source_health(manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    health = manifest.get("source_health", [])
    if not isinstance(health, list):
        return []
    out: List[Dict[str, str]] = []
    for row in health:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "source": clean(row.get("source_name")),
                "league": clean(row.get("sport_or_league")),
                "date": clean(row.get("date")),
                "ok": clean(row.get("ok")),
                "events": clean(row.get("events_found")),
                "notes": clean(row.get("notes")),
            }
        )
    return out


def source_coverage_map(source_registry: Dict[str, Any]) -> List[Dict[str, str]]:
    coverage = source_registry.get("coverage_map", [])
    if not isinstance(coverage, list):
        return []
    out: List[Dict[str, str]] = []
    for row in coverage:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "key": clean(row.get("coverage_key")),
                "name": clean(row.get("display_name")),
                "status": clean(row.get("coverage_status")) or "review",
                "official": clean(row.get("official_sources")),
                "team": clean(row.get("team_sources")),
                "wire": clean(row.get("wire_sources")),
                "cross_check": clean(row.get("cross_check_sources")),
                "gap": clean(row.get("coverage_gap")),
                "next_step": clean(row.get("operator_next_step")),
            }
        )
    return out


def content_candidates() -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    for row in read_csv("news_fact_packets.csv")[:8]:
        source_confidence = packet_source_confidence(row)
        candidate = {
            "type": "News packet",
            "priority": first_present(row.get("urgency"), row.get("publish_recommendation"), default="Review"),
            "headline": first_present(row.get("headline"), row.get("dek")),
            "status": "Ready" if clean(row.get("production_ready")).lower() == "yes" else "Review",
            "detail": short(first_present(row.get("caption_hard_fact"), row.get("brief_120w"), row.get("dek")), 210),
            "artifact": "news_fact_packets.csv",
            "source_count": clean(row.get("source_count")),
            **source_confidence,
        }
        candidate.update(
            score_render_readiness(
                candidate,
                item_type="News packet",
                headline=candidate["headline"],
                artifact=candidate["artifact"],
            )
        )
        candidates.append(
            candidate
        )
    for row in read_csv("today_final_results.csv")[:6]:
        candidate = {
            "type": "Final result",
            "priority": first_present(row.get("posting_priority"), row.get("editorial_bucket"), default="Review"),
            "headline": first_present(row.get("graphics_headline"), row.get("caption_seed")),
            "status": "Graphics ready" if clean(row.get("include_in_graphics")).lower() == "yes" else "Review",
            "detail": short(first_present(row.get("graphics_subhead"), row.get("final_score_display"), row.get("caption_seed")), 210),
            "artifact": "today_final_results.csv",
            "source_count": clean(row.get("source_count")),
            "source_grade": "publish_grade" if clean(row.get("manual_review")).lower() != "true" and clean(row.get("manual_review")).lower() != "yes" else "review_before_publish",
            "source_score": clean(row.get("confidence")),
            "source_reason": short(clean(row.get("confidence_reason_json")), 160),
        }
        candidate.update(
            score_render_readiness(
                candidate,
                item_type="Final result",
                headline=candidate["headline"],
                artifact=candidate["artifact"],
            )
        )
        candidates.append(
            candidate
        )
    return candidates


def source_discovery_board() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("morning_source_discovery_board.csv"):
        item = {
            "rank": clean(row.get("rank")),
            "lane": first_present(row.get("lane"), default="source_review"),
            "status": first_present(row.get("review_status"), default="review"),
            "posture": first_present(row.get("publish_posture"), default="discovery_only"),
            "band": first_present(row.get("source_band"), default="yellow"),
            "source": first_present(row.get("source_name"), row.get("source_type"), default="Unknown source"),
            "title": first_present(row.get("title"), row.get("source_url"), default="Untitled source lead"),
            "detail": short(first_present(row.get("evidence_preview"), row.get("summary"), row.get("reason"), row.get("next_action")), 260),
            "next_action": short(clean(row.get("next_action")), 180),
            "artifact": first_present(row.get("source_artifact"), default="morning_source_discovery_board.csv"),
            "url": clean(row.get("source_url")),
            "evidence_title": clean(row.get("evidence_title")),
            "evidence_published_at": clean(row.get("evidence_published_at")),
            "evidence_description": short(clean(row.get("evidence_description")), 260),
            "evidence_preview": short(clean(row.get("evidence_preview")), 260),
            "evidence_source": clean(row.get("evidence_source")),
            "story_opportunity_id": clean(row.get("story_opportunity_id")),
            "story_opportunity_title": clean(row.get("story_opportunity_title")),
            "story_opportunity_size": clean(row.get("story_opportunity_size")),
            "story_opportunity_sources": clean(row.get("story_opportunity_sources")),
            "story_opportunity_urls": clean(row.get("story_opportunity_urls")),
            "story_opportunity_reason": short(clean(row.get("story_opportunity_reason")), 220),
            "story_opportunity_angle": clean(row.get("story_opportunity_angle")),
            "story_opportunity_recommended_path": clean(row.get("story_opportunity_recommended_path")),
            "story_opportunity_path_reason": short(clean(row.get("story_opportunity_path_reason")), 220),
            "story_opportunity_confidence_tier": clean(row.get("story_opportunity_confidence_tier")),
            "story_opportunity_source_coverage": clean(row.get("story_opportunity_source_coverage")),
            "story_opportunity_confirmation_cue": clean(row.get("story_opportunity_confirmation_cue")),
            "story_opportunity_asset_cue": clean(row.get("story_opportunity_asset_cue")),
            "story_opportunity_readiness_note": short(clean(row.get("story_opportunity_readiness_note")), 220),
            "story_opportunity_second_source_id": clean(row.get("story_opportunity_second_source_id")),
            "story_opportunity_second_source_url": clean(row.get("story_opportunity_second_source_url")),
            "story_opportunity_second_source_lane": clean(row.get("story_opportunity_second_source_lane")),
            "story_opportunity_second_source_reason": short(clean(row.get("story_opportunity_second_source_reason")), 220),
            "story_opportunity_second_source_action": short(clean(row.get("story_opportunity_second_source_action")), 220),
            "promotion": first_present(row.get("promotion_recommendation"), default="monitor_only"),
            "promotion_priority": first_present(row.get("promotion_priority"), default="P4"),
            "promotion_target": clean(row.get("promotion_target")),
            "promotion_next_step": short(clean(row.get("promotion_next_step")), 180),
            "quality_score": clean(row.get("quality_score")),
            "freshness_label": clean(row.get("freshness_label")),
            "freshness_source": clean(row.get("freshness_source")),
            "freshness_score": clean(row.get("freshness_score")),
            "quality_reason": short(clean(row.get("quality_reason")), 190),
        }
        item.update(
            score_render_readiness(
                item,
                item_type="Story opportunity",
                headline=item["title"],
                artifact=item["artifact"],
            )
        )
        rows.append(item)
    rows.extend(breaking_public_signal_board_rows())
    return rows


def breaking_public_signal_board_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    clusters_by_candidate: Dict[str, Dict[str, str]] = {}
    next_actions_by_candidate: Dict[str, Dict[str, str]] = {}
    for cluster in read_csv("breaking_public_signal_clusters.csv"):
        for candidate_id in clean(cluster.get("candidate_ids")).split(";"):
            candidate_id = clean(candidate_id)
            if candidate_id and candidate_id not in clusters_by_candidate:
                clusters_by_candidate[candidate_id] = cluster
    next_actions_by_cluster_id = {
        clean(row.get("cluster_id")): row
        for row in read_csv("breaking_public_signal_next_action_v1.csv")
        if clean(row.get("cluster_id"))
    }
    for candidate_id, cluster in clusters_by_candidate.items():
        next_action_row = next_actions_by_cluster_id.get(clean(cluster.get("cluster_id")))
        if next_action_row:
            next_actions_by_candidate[candidate_id] = next_action_row
    for index, row in enumerate(read_csv("breaking_public_signal_queue.csv")[:8], 1):
        signal_status = clean(row.get("public_signal_status"))
        urgent_band = clean(row.get("urgency_band"))
        if signal_status != "candidate_public_signal_review_only" and urgent_band not in {"P0_breaking_review", "P1_urgent_review"}:
            continue
        title = first_present(row.get("headline"), default="Untitled breaking/public-signal review")
        cluster = clusters_by_candidate.get(clean(row.get("candidate_id")), {})
        next_action_row = next_actions_by_candidate.get(clean(row.get("candidate_id")), {})
        breaking_next_action_priority = clean(next_action_row.get("review_priority"))
        breaking_next_action_operator = clean(next_action_row.get("operator_next_action"))
        breaking_next_action_cue = clean(next_action_row.get("official_reputable_gray_area_cue"))
        breaking_next_action_why_urgent = clean(next_action_row.get("why_story_looks_urgent"))
        breaking_next_action_source_confidence = clean(next_action_row.get("source_confidence_tier"))
        breaking_next_action_source_reason = clean(next_action_row.get("source_confidence_reason"))
        breaking_next_action_signal_time = clean(next_action_row.get("signal_timestamp_utc"))
        breaking_next_action_retrieval = clean(next_action_row.get("retrieval_method"))
        breaking_next_action_signal_type = clean(next_action_row.get("public_signal_type"))
        breaking_next_action_limitations = clean(next_action_row.get("public_signal_limitations_cue"))
        breaking_next_action_confirmation_gap = clean(next_action_row.get("confirmation_gap"))
        breaking_next_action_manual_artifact = clean(next_action_row.get("manual_confirmation_artifact"))
        breaking_next_action_manual_row = clean(next_action_row.get("manual_confirmation_row_ref"))
        breaking_next_action_manual_target = clean(next_action_row.get("manual_confirmation_target"))
        breaking_next_action_return_fields = clean(next_action_row.get("manual_return_fields_to_complete"))
        breaking_next_action_return_guardrail = clean(next_action_row.get("manual_return_guardrail_cue"))
        breaking_next_action_return_blank_status = ""
        if breaking_next_action_return_fields:
            blank_return_fields = [
                field
                for field in [
                    "manual_return_operator_checked_url",
                    "manual_return_operator_confirmation_result",
                    "manual_return_operator_confirmed_at_utc",
                    "manual_return_operator_notes",
                ]
                if not clean(next_action_row.get(field))
            ]
            breaking_next_action_return_blank_status = f"manual_return_blank_fields={len(blank_return_fields)}/4"
        evidence_status = clean(cluster.get("matching_official_evidence_status"))
        evidence_artifacts = clean(cluster.get("matching_official_evidence_artifacts"))
        exact_next = clean(cluster.get("exact_source_or_intake_row_to_open"))
        confirmation_gap = clean(cluster.get("manual_confirmation_gap"))
        proof_status = clean(cluster.get("score_stat_proof_status"))
        proof_artifacts = clean(cluster.get("score_stat_proof_artifacts"))
        proof_urls = clean(cluster.get("score_stat_proof_source_urls"))
        proof_cue = clean(cluster.get("score_stat_manual_confirmation_cue"))
        proof_next = clean(cluster.get("exact_score_stat_proof_row_or_source_to_open"))
        human_next = clean(cluster.get("exact_human_confirmation_next_action"))
        breaking_confirmation_target = clean(cluster.get("breaking_claim_confirmation_target"))
        score_confirmation_status = clean(cluster.get("score_stat_confirmation_status"))
        score_confirmation_target = clean(cluster.get("score_proof_confirmation_target"))
        named_confirmation_targets = clean(cluster.get("named_player_stat_proof_confirmation_targets"))
        proof_examples = clean(cluster.get("named_player_stat_proof_examples"))
        review_order_status = clean(cluster.get("score_stat_review_order_status"))
        review_order_target = clean(cluster.get("first_score_stat_review_order_target"))
        review_walkthrough = clean(cluster.get("score_stat_review_walkthrough_target"))
        review_walkthrough_next = clean(cluster.get("exact_review_walkthrough_next_action"))
        ladder_status = clean(cluster.get("corroboration_ladder_status"))
        ladder_summary = clean(cluster.get("corroboration_ladder_summary"))
        official_corroboration = clean(cluster.get("official_source_corroboration"))
        reputable_corroboration = clean(cluster.get("reputable_source_corroboration"))
        public_corroboration = clean(cluster.get("public_signal_corroboration"))
        missing_confirmation_cue = clean(cluster.get("missing_confirmation_cue"))
        ladder_urls = clean(cluster.get("corroboration_evidence_urls"))
        urgency_review_reason = clean(cluster.get("urgency_review_reason"))
        proof_readiness_status = clean(cluster.get("source_proof_readiness_status"))
        proof_readiness_summary = clean(cluster.get("source_proof_readiness_summary"))
        proof_readiness_next = clean(cluster.get("source_proof_readiness_next_action"))
        story_proof_target = clean(cluster.get("story_proof_card_target"))
        game_fact_target = clean(cluster.get("game_fact_confirmation_target"))
        verification_priority_status = clean(cluster.get("verification_priority_status"))
        verification_priority_summary = clean(cluster.get("verification_priority_summary"))
        verification_priority_target = clean(cluster.get("verification_priority_target"))
        verification_priority_next = clean(cluster.get("verification_priority_next_action"))
        public_signal_limitations = clean(cluster.get("public_signal_limitations_cue"))
        game_source_tier = clean(cluster.get("game_source_confirmation_tier"))
        game_source_tier_limitations = clean(cluster.get("game_source_confirmation_limitations"))
        game_source_tier_cue = clean(cluster.get("game_source_confirmation_tier_cue"))
        game_source_freshness_status = clean(cluster.get("game_source_freshness_status"))
        game_source_freshness_age = clean(cluster.get("game_source_freshness_age_minutes"))
        game_source_retrieved_at = clean(cluster.get("game_source_retrieved_at_utc"))
        game_source_freshness_note = clean(cluster.get("game_source_freshness_note"))
        game_source_freshness_cue = clean(cluster.get("game_source_freshness_cue"))
        compact_ladder_note = ""
        if ladder_status or missing_confirmation_cue:
            compact_ladder_note = (
                f"Corroboration ladder: {ladder_status or 'review'}; "
                f"{missing_confirmation_cue or 'human confirmation required in intake'}."
            )
        coverage_summary = first_present(proof_readiness_summary, ladder_summary)
        if proof_readiness_summary and ladder_summary:
            coverage_summary = f"{proof_readiness_summary} | {ladder_summary}"
        if game_source_tier or game_source_tier_cue:
            tier_summary = f"game_source_tier={game_source_tier or 'review'}; {game_source_tier_cue or game_source_tier_limitations}"
            coverage_summary = f"{coverage_summary} | {tier_summary}" if coverage_summary else tier_summary
        if game_source_freshness_status or game_source_freshness_cue:
            freshness_bits = [
                f"game_source_freshness={game_source_freshness_status or 'review'}",
                f"retrieved_at={game_source_retrieved_at}" if game_source_retrieved_at else "",
                f"age_minutes={game_source_freshness_age}" if game_source_freshness_age else "",
                game_source_freshness_cue or game_source_freshness_note,
            ]
            freshness_summary = "; ".join(bit for bit in freshness_bits if bit)
            coverage_summary = f"{coverage_summary} | {freshness_summary}" if coverage_summary else freshness_summary
        if breaking_next_action_priority or breaking_next_action_cue:
            next_action_bits = [
                f"breaking_next_action={breaking_next_action_priority or 'review'}",
                breaking_next_action_cue,
                f"domain={clean(next_action_row.get('source_domain_lead'))}" if clean(next_action_row.get("source_domain_lead")) else "",
                f"source_confidence={breaking_next_action_source_confidence}" if breaking_next_action_source_confidence else "",
                f"public_signal_type={breaking_next_action_signal_type}" if breaking_next_action_signal_type else "",
                f"retrieval={breaking_next_action_retrieval}" if breaking_next_action_retrieval else "",
                f"signal_time={breaking_next_action_signal_time}" if breaking_next_action_signal_time else "",
                f"manual_row={breaking_next_action_manual_artifact} {breaking_next_action_manual_row}".strip() if breaking_next_action_manual_artifact or breaking_next_action_manual_row else "",
                f"manual_return_fields={breaking_next_action_return_fields}" if breaking_next_action_return_fields else "",
                breaking_next_action_return_blank_status,
                breaking_next_action_return_guardrail,
            ]
            next_action_summary = "; ".join(bit for bit in next_action_bits if bit)
            coverage_summary = f"{coverage_summary} | {next_action_summary}" if coverage_summary else next_action_summary
        compact_human_next = ""
        if human_next:
            compact_human_next = "Confirm breaking: {breaking}; score: {score}; named stats: {named}.".format(
                breaking=first_present(breaking_confirmation_target, default="breaking_public_signal_confirmation_intake.csv"),
                score=first_present(score_confirmation_target, default="final_score_stat_proof_confirmation_intake_v1.csv score proof row"),
                named=first_present(named_confirmation_targets, default="final_score_stat_proof_confirmation_intake_v1.csv named stat proof rows"),
            )
        compact_walkthrough_next = ""
        if review_walkthrough or review_order_target or review_walkthrough_next:
            review_order_match = re.search(r"review_order=[^;]+", review_order_target)
            compact_review_target = (
                review_order_match.group(0)
                if review_order_match
                else "matching review-order row"
            )
            score_proof_match = re.search(r"proof_id=([^;\s]+)", score_confirmation_target)
            score_record_target = (
                f"proof_id={score_proof_match.group(1)} in final_score_stat_proof_confirmation_intake_v1.csv"
                if score_proof_match
                else first_present(score_confirmation_target, default="score proof row in final_score_stat_proof_confirmation_intake_v1.csv")
            )
            compact_walkthrough_next = "Open {walkthrough}; start {target}; record score {score_target}; named stats in listed intake rows.".format(
                walkthrough=first_present(review_walkthrough, default="final_score_stat_proof_review_walkthrough_v1.md"),
                target=compact_review_target,
                score_target=score_record_target,
            )
        source_domains = clean(row.get("source_domains"))
        public_summary = clean(row.get("public_signal_summary"))
        why_urgent = clean(row.get("why_urgent"))
        item = {
            "rank": f"B{index}",
            "lane": "social_discovery" if signal_status == "candidate_public_signal_review_only" else "breaking_news_review",
            "status": "review_only",
            "posture": "discovery_only",
            "band": "yellow",
            "source": "Breaking/public signal queue",
            "title": title,
            "detail": short(first_present(verification_priority_summary, urgency_review_reason, proof_readiness_summary, ladder_summary, review_walkthrough_next, human_next, proof_cue, breaking_next_action_confirmation_gap, confirmation_gap, public_summary, why_urgent), 260),
            "next_action": short(
                first_present(breaking_next_action_operator, verification_priority_next, proof_readiness_next, compact_walkthrough_next, compact_human_next, human_next, proof_next, exact_next, default="Open breaking_public_signal_clusters.md, then fill breaking_public_signal_confirmation_intake.csv with the confirmation check."),
                180,
            ),
            "artifact": "breaking_public_signal_queue.csv",
            "url": "",
            "evidence_title": title,
            "evidence_published_at": clean(row.get("signal_timestamp_utc")),
            "evidence_description": short(first_present(breaking_next_action_limitations, public_signal_limitations, public_corroboration, public_summary), 260),
            "evidence_preview": short(first_present(breaking_next_action_why_urgent, breaking_next_action_source_reason, verification_priority_status, verification_priority_summary, game_source_freshness_cue, game_source_tier_cue, proof_readiness_status, proof_readiness_summary, ladder_status, ladder_summary, review_order_status, score_confirmation_status, proof_status, proof_examples, evidence_status, why_urgent), 260),
            "evidence_source": first_present(proof_artifacts, evidence_artifacts, default="breaking_public_signal_queue.csv"),
            "story_opportunity_id": clean(row.get("candidate_id")),
            "story_opportunity_title": title,
            "story_opportunity_size": clean(row.get("public_signal_count")),
            "story_opportunity_sources": source_domains,
            "story_opportunity_urls": first_present(ladder_urls, proof_urls, cluster.get("matching_official_evidence_urls"), row.get("source_urls")),
            "story_opportunity_reason": short(first_present(breaking_next_action_why_urgent, verification_priority_summary, urgency_review_reason, proof_readiness_summary, ladder_summary, why_urgent), 220),
            "story_opportunity_angle": first_present(verification_priority_status, proof_readiness_status, ladder_status, urgent_band),
            "story_opportunity_recommended_path": "manual_story_candidate",
            "story_opportunity_path_reason": "Breaking/public signal is review-only until the confirmation intake records official, wire, primary, or operator-verified evidence.",
            "story_opportunity_confidence_tier": first_present(ladder_status, default="discovery_only"),
            "story_opportunity_source_coverage": first_present(coverage_summary, proof_status, evidence_status, default="discovery_source_only"),
            "story_opportunity_confirmation_cue": first_present(verification_priority_status, missing_confirmation_cue, default="needs_official_confirmation"),
            "story_opportunity_asset_cue": "asset_not_required_for_news_packet",
            "story_opportunity_readiness_note": short(first_present(verification_priority_next, proof_readiness_next, compact_ladder_note, ladder_summary, compact_walkthrough_next, review_walkthrough_next, compact_human_next, human_next, proof_cue, breaking_next_action_confirmation_gap, confirmation_gap, row.get("limitations")), 220),
            "story_opportunity_second_source_id": "",
            "story_opportunity_second_source_url": first_present(breaking_next_action_manual_target, verification_priority_target, story_proof_target, game_fact_target, ladder_urls, review_order_target, score_confirmation_target, named_confirmation_targets, proof_urls, cluster.get("matching_official_evidence_urls"), default=""),
            "story_opportunity_second_source_lane": "official_or_wire_confirmation_required",
            "story_opportunity_second_source_reason": first_present(breaking_next_action_priority, breaking_next_action_source_confidence, verification_priority_status, game_source_freshness_status, game_source_tier, proof_readiness_status, official_corroboration, reputable_corroboration, review_order_status, score_confirmation_status, proof_status, evidence_status, default="Public/community signal cannot confirm a breaking story by itself."),
            "story_opportunity_second_source_action": first_present(breaking_next_action_operator, verification_priority_next, game_source_freshness_cue, proof_readiness_next, review_walkthrough_next, human_next, proof_next, exact_next, default="Fill breaking_public_signal_confirmation_intake.csv with official, wire, primary, or operator-verified confirmation before any story path."),
            "promotion": "monitor_only",
            "promotion_priority": urgent_band,
            "promotion_target": "breaking_public_signal_clusters.csv",
            "promotion_next_step": short(first_present(row.get("human_review_cue"), default="Keep monitoring; do not publish from public signal alone."), 180),
            "quality_score": clean(row.get("breaking_score")),
            "freshness_label": "signal_and_game_source_timestamp",
            "freshness_source": first_present(game_source_retrieved_at, row.get("signal_timestamp_utc")),
            "freshness_score": first_present(game_source_freshness_status, row.get("freshness_status")),
            "quality_reason": short(why_urgent, 190),
            "manual_review_required": clean(row.get("manual_review_required")) or "true",
            "review_only": clean(row.get("review_only")) or "true",
            "publish_ready": clean(row.get("publish_ready")) or "false",
            "auto_publish": clean(row.get("auto_publish")) or "false",
        }
        item.update(
            score_render_readiness(
                item,
                item_type="Story opportunity",
                headline=item["title"],
                artifact=item["artifact"],
            )
        )
        rows.append(item)
    return rows


def lead_promotion_recommendations() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("morning_lead_promotion_recommendations.csv"):
        item = {
            "rank": clean(row.get("promotion_rank")),
            "priority": first_present(row.get("promotion_priority"), default="P?"),
            "recommendation": first_present(row.get("promotion_recommendation"), default="review"),
            "title": first_present(row.get("story_opportunity_title"), row.get("title"), row.get("source_url"), default="Untitled lead"),
            "status": first_present(row.get("review_status"), default="review"),
            "lane": first_present(row.get("lane"), default="source_review"),
            "target": first_present(row.get("promotion_target"), default="morning_source_discovery_board.csv"),
            "detail": short(first_present(row.get("evidence_preview"), row.get("summary"), row.get("reason")), 260),
            "reason": short(clean(row.get("promotion_reason")), 190),
            "next_step": short(clean(row.get("promotion_next_step")), 190),
            "evidence_title": clean(row.get("evidence_title")),
            "evidence_published_at": clean(row.get("evidence_published_at")),
            "evidence_description": short(clean(row.get("evidence_description")), 260),
            "evidence_preview": short(clean(row.get("evidence_preview")), 260),
            "evidence_source": clean(row.get("evidence_source")),
            "story_opportunity_id": clean(row.get("story_opportunity_id")),
            "story_opportunity_title": clean(row.get("story_opportunity_title")),
            "story_opportunity_size": clean(row.get("story_opportunity_size")),
            "story_opportunity_sources": clean(row.get("story_opportunity_sources")),
            "story_opportunity_urls": clean(row.get("story_opportunity_urls")),
            "story_opportunity_reason": short(clean(row.get("story_opportunity_reason")), 220),
            "story_opportunity_angle": clean(row.get("story_opportunity_angle")),
            "story_opportunity_recommended_path": clean(row.get("story_opportunity_recommended_path")),
            "story_opportunity_path_reason": short(clean(row.get("story_opportunity_path_reason")), 220),
            "story_opportunity_confidence_tier": clean(row.get("story_opportunity_confidence_tier")),
            "story_opportunity_source_coverage": clean(row.get("story_opportunity_source_coverage")),
            "story_opportunity_confirmation_cue": clean(row.get("story_opportunity_confirmation_cue")),
            "story_opportunity_asset_cue": clean(row.get("story_opportunity_asset_cue")),
            "story_opportunity_readiness_note": short(clean(row.get("story_opportunity_readiness_note")), 220),
            "story_opportunity_second_source_id": clean(row.get("story_opportunity_second_source_id")),
            "story_opportunity_second_source_url": clean(row.get("story_opportunity_second_source_url")),
            "story_opportunity_second_source_lane": clean(row.get("story_opportunity_second_source_lane")),
            "story_opportunity_second_source_reason": short(clean(row.get("story_opportunity_second_source_reason")), 220),
            "story_opportunity_second_source_action": short(clean(row.get("story_opportunity_second_source_action")), 220),
            "quality_score": clean(row.get("quality_score")),
            "freshness_label": clean(row.get("freshness_label")),
            "freshness_source": clean(row.get("freshness_source")),
            "freshness_score": clean(row.get("freshness_score")),
            "quality_reason": short(clean(row.get("quality_reason")), 190),
            "artifact": "morning_lead_promotion_recommendations.csv",
        }
        item.update(
            score_render_readiness(
                item,
                item_type="Story opportunity",
                headline=item["title"],
                artifact=item["artifact"],
            )
        )
        rows.append(item)
    return rows


def studio_queue() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv("studio_bundle_queue.csv")[:8]:
        rows.append(
            {
                "priority": first_present(row.get("production_priority"), row.get("bundle_rank"), default="Review"),
                "name": first_present(row.get("bundle_name"), row.get("content_family"), default="Untitled bundle"),
                "type": first_present(row.get("bundle_type"), row.get("asset_type")),
                "shape": first_present(row.get("asset_shape"), row.get("slide_count")),
                "status": first_present(row.get("freshness_decision"), row.get("freshness_status"), default="Review"),
                "detail": short(first_present(row.get("source_headlines"), row.get("caption_seed")), 260),
                "artifact": "studio_bundle_queue.csv",
            }
        )
    return rows


def render_readiness_queue(
    candidates: List[Dict[str, str]],
    promotions: List[Dict[str, str]],
    source_board: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen: set[str] = set()

    def add_row(row: Dict[str, str], source: str, title_key: str = "headline") -> None:
        title = first_present(row.get(title_key), row.get("title"), row.get("story_opportunity_title"), default="Untitled candidate")
        key = first_present(row.get("story_opportunity_id"), title, source)
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "rank": "",
                "source": source,
                "title": title,
                "recommended_path": first_present(
                    row.get("story_opportunity_recommended_path"),
                    row.get("recommendation"),
                    row.get("type"),
                    default="review",
                ),
                "score": clean(row.get("render_readiness_score")),
                "band": clean(row.get("render_readiness_band")),
                "source_cue": clean(row.get("render_readiness_source_cue")),
                "asset_cue": clean(row.get("render_readiness_asset_cue")),
                "format_cue": clean(row.get("render_readiness_format_cue")),
                "manual_path": clean(row.get("render_readiness_manual_path")),
                "blockers": clean(row.get("render_readiness_blockers")) or "none",
                "next_step": clean(row.get("render_readiness_next_step")),
                "artifact": first_present(row.get("artifact"), row.get("target"), default="operator_command_center.md"),
            }
        )

    for row in candidates:
        add_row(row, row.get("type") or "Content candidate")
    for row in promotions:
        add_row(row, "Lead promotion", title_key="title")
    for row in source_board:
        if row.get("story_opportunity_id") and row.get("story_opportunity_id") not in seen:
            add_row(row, "Source discovery", title_key="title")

    rows.sort(key=lambda item: (-as_int(item.get("score")), item.get("title", "")))
    for index, row in enumerate(rows[:12], 1):
        row["rank"] = str(index)
    return rows[:12]


def packet_slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-")
    return slug[:70] or "untitled-render-candidate"


def template_fit_for_path(path: str, source: str) -> Dict[str, str]:
    token = clean(path).lower()
    source_token = clean(source).lower()
    if token == "news_packet" or source_token == "news packet":
        return {
            "template_fit": "news_fact_card_review",
            "template_shape": "IG feed 1080x1350; Threads crop-safe summary",
            "asset_requirement": "No player asset required; use HSD brand treatment and verified source text only.",
            "renderer_family": "news_or_quality_graphics_manual_review",
        }
    if token == "studio_brief":
        return {
            "template_fit": "studio_brief_card_review",
            "template_shape": "IG feed 1080x1350 or carousel cover",
            "asset_requirement": "Confirm exact league/team/player assets before render prep; no text-logo fallback.",
            "renderer_family": "studio_bundle_manual_review",
        }
    if token == "manual_story_candidate":
        return {
            "template_fit": "manual_story_candidate_card_review",
            "template_shape": "IG feed 1080x1350 or IG story 1080x1920 after editor chooses angle",
            "asset_requirement": "Use brand-only treatment until a verified exact image or logo is approved.",
            "renderer_family": "manual_story_workflow_review",
        }
    if token == "final result" or source_token == "final result":
        return {
            "template_fit": "final_score_result_card_review",
            "template_shape": "IG story 1080x1920 or feed 1080x1350",
            "asset_requirement": "Use exact team logos from approved local registry; no placeholder badges.",
            "renderer_family": "final_score_story_manual_review",
        }
    return {
        "template_fit": "operator_review_card",
        "template_shape": "Choose feed 1080x1350 unless the operator marks story-first.",
        "asset_requirement": "Operator must decide whether verified assets are required before render prep.",
        "renderer_family": "manual_review_only",
    }


def looks_like_final_score(enriched: Dict[str, str], row: Dict[str, str]) -> bool:
    combined = " ".join(
        clean(value)
        for value in [
            row.get("title"),
            row.get("recommended_path"),
            row.get("source"),
            enriched.get("copy_headline"),
            enriched.get("copy_dek"),
            enriched.get("copy_context"),
        ]
    ).lower()
    return bool(
        re.search(r"\b(final|beat|beats|defeat|defeats|top|tops)\b", combined)
        and re.search(r"\b\d{2,3}\b.*\b\d{2,3}\b", combined)
    )


def stat_source_fields(top_performers: str) -> Dict[str, str]:
    if clean(top_performers):
        return {
            "stat_module_status": "verified_stat_text_available",
            "stat_source_confidence": "verified_stat_text_ready_manual_crosscheck_required",
            "stat_source_label": "Verified player/stat text available",
            "stat_review_cue": "Confirm the named performer and stat line against source proof before approval.",
        }
    return {
        "stat_module_status": "no_verified_stat_text",
        "stat_source_confidence": "score_only_fallback_manual_context_required",
        "stat_source_label": "Score-derived fallback",
        "stat_review_cue": "No named performer stat text is available; hold if a player ledger is expected.",
    }


def breaking_cluster_player_angle_signal(
    *,
    title: str,
    candidate_id: str,
    payload: Dict[str, Any],
) -> Dict[str, str]:
    title = clean(title)
    candidate_id = clean(candidate_id)
    for cluster in payload.get("breaking_public_signal_clusters", []):
        examples = clean(cluster.get("named_player_stat_proof_examples"))
        if not examples:
            continue
        proof_sources = first_present(
            cluster.get("score_stat_proof_source_urls"),
            cluster.get("matching_official_evidence_urls"),
        )
        if not proof_sources:
            continue
        proof_status = clean(cluster.get("score_stat_proof_status"))
        review_status = clean(cluster.get("score_stat_review_order_status"))
        first_review_target = clean(cluster.get("first_score_stat_review_order_target"))
        proof_artifact_ready = (
            find_existing_input("final_score_stat_proof_v1.csv").exists()
            or "final_score_stat_proof_v1.csv proof_id=" in clean(cluster.get("score_stat_proof_artifacts"))
        )
        review_order_ready = (
            find_existing_input("final_score_stat_proof_review_order_v1.csv").exists()
            or (
                review_status == "review_order_rows_present_operator_follow_walkthrough"
                and bool(first_review_target)
            )
        )
        if not proof_artifact_ready or not review_order_ready:
            continue
        cluster_candidate_ids = {clean(value) for value in clean(cluster.get("candidate_ids")).split(";") if clean(value)}
        title_matches = clean(cluster.get("cluster_headline")) == title
        candidate_matches = candidate_id and candidate_id in cluster_candidate_ids
        if not title_matches and not candidate_matches:
            continue
        walkthrough = clean(cluster.get("score_stat_review_walkthrough_target"))
        proof_text = examples.replace(" | ", "; ")
        return {
            "top_performers": proof_text,
            "stat_module_status": "named_player_stat_proof_text_available",
            "stat_source_confidence": "cluster_named_player_proof_ready_manual_crosscheck_required",
            "stat_source_label": "Named-player proof from breaking/public-signal cluster",
            "stat_review_cue": (
                "Player-led render angle is available from breaking_public_signal_clusters.csv; "
                f"status={proof_status or 'review'}; review_order={review_status or 'missing'}; "
                f"open {walkthrough or 'final_score_stat_proof_review_walkthrough_v1.md'}"
                f"{' and start at ' + first_review_target if first_review_target else ''} before approval."
            ),
            "source_detail": (
                "Named-player stat proof surfaced from breaking_public_signal_clusters.csv; "
                "manual source and intake confirmation still required before editorial or render approval."
            ),
        }
    return {}


def final_score_template_fit() -> Dict[str, str]:
    return {
        "template_fit": "hsd_game_recap_final_score_review",
        "selected_template_id": "hsd_game_recap_final_score_a",
        "template_family": "game_recap_final_score",
        "reference_pack_id": "templates_hsd_20260625",
        "template_shape": "IG feed 1080x1350 primary; story 1080x1920 and square review derivatives",
        "asset_requirement": "Use exact local WNBA team logos from the registry; no invented identity, no text-logo fallback, no player asset required.",
        "renderer_family": "templates_hsd_final_score_manual_review",
    }


def render_visual_mode_contract(enriched: Dict[str, str], fit: Dict[str, str]) -> Dict[str, str]:
    stat_status = clean(enriched.get("stat_module_status"))
    top_performers = clean(enriched.get("top_performers"))
    template_family = clean(fit.get("template_family"))
    if template_family == "game_recap_final_score" and top_performers and stat_status != "no_verified_stat_text":
        return {
            "visual_mode": "photo_first_performer",
            "hero_asset_required": "approved_local_athlete_photo",
            "focal_entity_type": "athlete",
            "score_lock_variant": "final_score_locked_photo_first",
            "proof_strip_variant": "player_stat_proof_strip",
            "copy_unlock_state": "verified_stat_copy_locked_manual_review",
            "background_family": "hsd_premium_sports_editorial",
            "template_fit_reason": "Verified player/stat context is present; renderer should attempt review-only photo-first performer routing with approved local athlete asset gates.",
            "asset_requirement": "Use exact local WNBA team logos plus approved local athlete headshot/cutout for the verified performer; no downloads, no invented identity, no asset approval changes.",
        }
    if template_family == "game_recap_final_score":
        return {
            "visual_mode": "no_photo_premium_result",
            "hero_asset_required": "approved_local_athlete_photo_missing",
            "focal_entity_type": "team_matchup",
            "score_lock_variant": "final_score_locked_logo_first",
            "proof_strip_variant": "score_edge_only",
            "copy_unlock_state": "score_only_copy_locked_manual_review",
            "background_family": "hsd_premium_sports_editorial",
            "template_fit_reason": "No verified player/stat context in handoff; renderer must use no-photo premium result fallback or visibly block athlete-led rendering with missing fields.",
        }
    return {
        "visual_mode": "manual_review_template",
        "hero_asset_required": "operator_review",
        "focal_entity_type": "story",
        "score_lock_variant": "not_final_score",
        "proof_strip_variant": "source_check_only",
        "copy_unlock_state": "manual_copy_locked_review",
        "background_family": "hsd_premium_sports_editorial",
        "template_fit_reason": clean(fit.get("template_fit")) or "Manual renderer route selected from source/format fit.",
    }


def no_mid_word_trim(value: Any, limit: int) -> str:
    text = clean(value)
    if len(text) <= limit:
        return text
    trimmed = text[:limit].rstrip(" ,.;:!?-")
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip(" ,.;:!?-")
    return trimmed


def final_score_copy_polish(enriched: Dict[str, str], row: Dict[str, str], fit: Dict[str, str]) -> Dict[str, str]:
    headline = clean(enriched.get("copy_headline")) or clean(row.get("title"))
    dek = clean(enriched.get("copy_dek"))
    if clean(fit.get("template_family")) != "game_recap_final_score":
        return {
            "copy_suggested_title": no_mid_word_trim(headline, 58),
            "copy_suggested_dek": no_mid_word_trim(dek, 118),
            "copy_fit_cue": "Keep the visible headline under 58 characters and the dek under 118; tighten before manual render if either wraps awkwardly.",
            "copy_polish_note": "Use source-backed verbs and remove generic filler before visual review.",
        }

    scoreline = ""
    score_match = re.search(r"([A-Z][A-Za-z .'-]+)\s+(\d{2,3})\s*,\s*([A-Z][A-Za-z .'-]+)\s+(\d{2,3})", dek)
    if score_match:
        winner, winner_score, loser, loser_score = [clean(item) for item in score_match.groups()]
        winner_short = winner.split()[-1].upper()
        loser_short = loser.split()[-1].upper()
        scoreline = f"{winner_short} {winner_score}, {loser_short} {loser_score}"
    return {
        "copy_suggested_title": no_mid_word_trim(headline.replace(" beat ", " over "), 46),
        "copy_suggested_dek": no_mid_word_trim(scoreline or dek, 96),
        "copy_fit_cue": "Final-score fit: title <=46 chars, dek <=96 chars; lead with the result, then let verified stat text or source proof add the why.",
        "copy_polish_note": "Avoid generic 'final read' language; use score-first wording until a verified player/stat module supports a sharper angle.",
    }


def enrich_render_row(row: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, str]:
    title = clean(row.get("title"))
    for packet in payload.get("news_fact_packets", []):
        if clean(packet.get("headline")) == title:
            cluster_angle = breaking_cluster_player_angle_signal(
                title=title,
                candidate_id=packet.get("candidate_id", ""),
                payload=payload,
            )
            top_performers = clean(packet.get("top_performers")) or clean(cluster_angle.get("top_performers"))
            stat_fields = cluster_angle if clean(cluster_angle.get("top_performers")) and not clean(packet.get("top_performers")) else stat_source_fields(top_performers)
            return {
                "copy_headline": title,
                "copy_dek": clean(packet.get("caption_hard_fact")) or clean(packet.get("dek")),
                "copy_context": (
                    f"{clean(packet.get('source_count')) or '0'} source(s); "
                    f"{clean(packet.get('source_publish_grade')) or clean(packet.get('source_confidence_tier')) or 'not_scored'}"
                    f"{' score ' + clean(packet.get('source_confidence_score')) if clean(packet.get('source_confidence_score')) else ''}."
                ),
                "source_detail": first_present(
                    cluster_angle.get("source_detail"),
                    packet.get("source_confidence_reason"),
                    packet.get("rights_safe_note"),
                ),
                "top_performers": top_performers,
                **stat_fields,
            }
    for candidate in payload.get("content_candidates", []):
        if clean(candidate.get("headline")) == title:
            cluster_angle = breaking_cluster_player_angle_signal(
                title=title,
                candidate_id=candidate.get("candidate_id", ""),
                payload=payload,
            )
            top_performers = clean(candidate.get("top_performers")) or clean(cluster_angle.get("top_performers"))
            stat_fields = cluster_angle if clean(cluster_angle.get("top_performers")) and not clean(candidate.get("top_performers")) else stat_source_fields(top_performers)
            return {
                "copy_headline": title,
                "copy_dek": clean(candidate.get("detail")),
                "copy_context": (
                    f"{clean(candidate.get('source_count')) or '0'} source(s); "
                    f"{clean(candidate.get('source_grade')) or 'not_scored'}"
                    f"{' score ' + clean(candidate.get('source_score')) if clean(candidate.get('source_score')) else ''}."
                ),
                "source_detail": first_present(cluster_angle.get("source_detail"), candidate.get("source_reason")),
                "top_performers": top_performers,
                **stat_fields,
            }
    for lead in payload.get("lead_promotion_recommendations", []):
        if clean(lead.get("title")) == title:
            return {
                "copy_headline": title,
                "copy_dek": clean(lead.get("detail")),
                "copy_context": (
                    f"Angle: {clean(lead.get('story_opportunity_angle')) or 'review'}; "
                    f"sources: {clean(lead.get('story_opportunity_sources')) or 'review'}."
                ),
                "source_detail": clean(lead.get("story_opportunity_reason")),
                "top_performers": "",
                **stat_source_fields(""),
            }
    for lead in payload.get("source_discovery_board", []):
        if clean(lead.get("title")) == title:
            cluster_angle = breaking_cluster_player_angle_signal(
                title=title,
                candidate_id=lead.get("story_opportunity_id", ""),
                payload=payload,
            )
            top_performers = clean(cluster_angle.get("top_performers"))
            stat_fields = cluster_angle if top_performers else stat_source_fields("")
            return {
                "copy_headline": title,
                "copy_dek": clean(lead.get("detail")),
                "copy_context": (
                    f"Discovery lane: {clean(lead.get('lane')) or 'review'}; "
                    f"posture: {clean(lead.get('posture')) or 'review'}."
                ),
                "source_detail": first_present(cluster_angle.get("source_detail"), lead.get("story_opportunity_reason")),
                "top_performers": top_performers,
                **stat_fields,
            }
    return {"copy_headline": title, "copy_dek": "", "copy_context": "", "source_detail": "", "top_performers": "", **stat_source_fields("")}


def manual_renderer_steps(packet: Dict[str, str]) -> str:
    template_label = clean(packet.get("selected_template_id")) or clean(packet.get("template_fit"))
    active_logo_cues = (clean(packet.get("active_logo_review_cues")) or "no active logo hold cue recorded").replace(" | ", "; ").replace("|", ";")
    active_athlete_cues = (clean(packet.get("active_athlete_identity_cues")) or "no active athlete identity hold cue recorded").replace(" | ", "; ").replace("|", ";")
    steps = [
        f"Open {packet.get('source_artifact')} and confirm the source/copy fields match this packet.",
        "Open operator_command_center.html and confirm source, format, and manual-path blockers are clear; active asset holds remain separate stop/go cues.",
        f"Confirm active asset stop/go: {clean(packet.get('active_asset_stop_go')) or 'clear_no_active_asset_holds'}.",
        f"Use {template_label} at {packet.get('template_shape')}.",
        f"Confirm asset requirement: {packet.get('asset_requirement')}",
        f"Confirm copy fit: {clean(packet.get('copy_fit_cue')) or 'Tighten headline/dek before manual render if they wrap awkwardly.'}",
        f"Confirm active logo readiness: {clean(packet.get('active_logo_readiness_status')) or 'logo_review_not_flagged'}; {active_logo_cues}",
        f"Confirm active athlete identity: {clean(packet.get('active_athlete_identity_status')) or 'athlete_identity_not_flagged'}; {active_athlete_cues}",
        "Compare the draft against the linked Templates-hsd reference mockup/layout before recording any decision.",
        "Prepare the graphic manually in the renderer or design tool; do not auto-post or auto-publish.",
        "After visual review, record the decision in the normal manual QA or approval artifact before any human posting.",
    ]
    return " | ".join(steps)


def split_manual_renderer_steps(value: Any) -> List[str]:
    return [step.strip() for step in clean(value).split(" | ") if step.strip()]


def active_logo_packet_text(packet: Dict[str, str]) -> str:
    return " ".join(
        clean(packet.get(key))
        for key in ["title", "copy_headline", "copy_dek", "top_performers", "asset_requirement", "template_family", "renderer_family"]
    ).lower()


def active_logo_entity_aliases(entity_name: str, entity_id: str) -> List[str]:
    aliases: List[str] = []
    name = clean(entity_name).lower()
    ident = clean(entity_id).replace("_", " ").lower()
    for value in [name, ident]:
        if value and value not in aliases:
            aliases.append(value)
        parts = re.findall(r"[a-z0-9]+", value)
        if len(parts) >= 2 and parts[-1] not in aliases:
            aliases.append(parts[-1])
    return aliases


def active_logo_entity_matches(packet_text: str, entity_name: str, entity_id: str) -> bool:
    return any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", packet_text) for alias in active_logo_entity_aliases(entity_name, entity_id))


def selected_template_blocking_status(packet: Dict[str, str], row: Dict[str, str]) -> Dict[str, str]:
    requirement = clean(packet.get("asset_requirement")).lower()
    domain = clean(row.get("asset_domain"))
    if domain == "team_logo":
        return {
            "selected_template_blocking_status": "blocking_selected_template_logo_review",
            "selected_template_blocking_reason": "Selected final-score template requires exact WNBA logo review before renderer trust.",
        }
    if domain == "league_logo":
        if "league mark required" in requirement or "league logo required" in requirement:
            return {
                "selected_template_blocking_status": "blocking_selected_template_logo_review",
                "selected_template_blocking_reason": "Selected template explicitly requires an exact league mark before renderer trust.",
            }
        return {
            "selected_template_blocking_status": "not_blocking_selected_template_league_mark_not_required",
            "selected_template_blocking_reason": "Selected final-score template uses team logo slots; keep the league mark hold as review-only context for future branded templates.",
        }
    if domain == "athlete_photo":
        if "no player asset required" in requirement:
            return {
                "selected_template_blocking_status": "not_blocking_selected_template_photo_not_required",
                "selected_template_blocking_reason": "Selected final-score template does not require player imagery; keep identity hold for future photo-first renders.",
            }
        return {
            "selected_template_blocking_status": "blocking_selected_template_identity_review",
            "selected_template_blocking_reason": "Selected template may use athlete imagery; identity must be source-backed before renderer trust.",
        }
    return {
        "selected_template_blocking_status": "review_only_context_required",
        "selected_template_blocking_reason": "Review-only asset cue requires a human stop/go decision before renderer trust.",
    }


def audit_decision_lane(domain: str, finding: str = "", league: str = "") -> str:
    if domain in {"team_logo", "league_logo"}:
        return "wnba_logo_review" if clean(league).upper() in {"", "WNBA"} else "logo_review"
    if domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "wnba_athlete_identity_resolution"
    if domain == "player_photo":
        return "wnba_athlete_photo_onboarding"
    return "asset_manual_review"


def audit_default_operator_decision(domain: str, finding: str) -> str:
    if domain == "league_logo":
        return "hold_league_mark"
    if domain == "team_logo":
        return "hold_or_verify_logo"
    if domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "hold_identity"
    if domain == "player_photo":
        return "hold_photo_slot"
    return "hold_asset_slot"


def audit_asset_readiness(item: Dict[str, Any]) -> str:
    return clean(first_present(item.get("asset_readiness"), item.get("logo_readiness_status"), item.get("renderer_coverage"), item.get("finding")))


def active_logo_readiness_for_packet(packet: Dict[str, str]) -> Dict[str, str]:
    packet_text = active_logo_packet_text(packet)
    cues: List[str] = []
    fallback_cues: List[str] = []
    audit_cue_found = False
    logo_packet_cue_found = False
    audit = read_json("data/asset_registry/asset_availability_audit.json")
    findings = audit.get("findings") if isinstance(audit.get("findings"), list) else []
    for item in findings:
        domain = clean(item.get("asset_domain"))
        if domain not in {"team_logo", "league_logo"}:
            continue
        entity_name = clean(item.get("entity_name")) or clean(item.get("entity_id"))
        entity_id = clean(item.get("entity_id"))
        league_mark = domain == "league_logo" and clean(item.get("entity_id")).lower() == "wnba" and "wnba" in packet_text
        if not league_mark and not active_logo_entity_matches(packet_text, entity_name, entity_id):
            continue
        cue = (
            f"{entity_name}: {clean(item.get('finding')) or 'logo_review_required'}; "
            f"{clean(item.get('recommended_next_step')) or clean(item.get('decision_primary_action')) or 'manual logo review required'}"
        )
        if cue not in cues:
            cues.append(cue)
            audit_cue_found = True
        fallback = clean(item.get("renderer_fallback_cue"))
        if fallback and fallback not in fallback_cues:
            fallback_cues.append(fallback)
    for item in read_csv("data/asset_registry/wnba/logo_review_packets.csv"):
        team_name = clean(item.get("team_name")) or clean(item.get("team_id"))
        team_id = clean(item.get("team_id"))
        if not active_logo_entity_matches(packet_text, team_name, team_id):
            continue
        cue = (
            f"{team_name}: {clean(item.get('issue_type')) or 'logo_review_required'}; "
            f"{clean(item.get('primary_action')) or clean(item.get('decision_primary_action')) or 'manual logo review required'}"
        )
        if cue not in cues:
            cues.append(cue)
            logo_packet_cue_found = True
        fallback = clean(item.get("renderer_fallback_cue"))
        if fallback and fallback not in fallback_cues:
            fallback_cues.append(fallback)
    status = "hold_logo_review_required" if cues else "logo_review_not_flagged"
    if logo_packet_cue_found:
        artifact = "data/asset_registry/wnba/logo_review_packets.csv"
    elif audit_cue_found:
        artifact = "data/asset_registry/asset_availability_audit.csv"
    else:
        artifact = "data/asset_registry/asset_availability_audit.csv"
    return {
        "active_logo_readiness_status": status,
        "active_logo_review_cues": " | ".join(cues[:6]),
        "logo_review_artifact": artifact,
        "renderer_fallback_cue": " | ".join(fallback_cues[:4]),
    }


def active_athlete_packet_text(packet: Dict[str, str]) -> str:
    return " ".join(
        clean(packet.get(key))
        for key in ["title", "copy_headline", "copy_dek", "top_performers", "asset_requirement", "template_family", "renderer_family"]
    ).lower()


def active_athlete_identity_matches(packet_text: str, athlete_name: str, athlete_id: str) -> bool:
    aliases = [clean(athlete_name).lower()]
    ident = clean(athlete_id).replace("_", " ").lower()
    if ident and ident not in aliases:
        aliases.append(ident)
    return any(alias and re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", packet_text) for alias in aliases)


def active_athlete_identity_closure_cues() -> Dict[str, str]:
    closure_packet = read_json("data/asset_registry/wnba/athlete_identity_closure_packet.json")
    report = closure_packet.get("report") if isinstance(closure_packet.get("report"), dict) else {}
    closure_rows = read_csv("data/asset_registry/wnba/athlete_identity_issue_closure_template.csv")
    backfill_rows = read_csv("data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv")
    closure_count = as_int(report.get("closure_rows")) or len(closure_rows)
    backfill_count = as_int(report.get("backfill_rows")) or len(backfill_rows)
    if not closure_count and not backfill_count:
        return {
            "active_athlete_identity_closure_cues": "",
            "athlete_identity_closure_artifact": "",
            "athlete_identity_backfill_artifact": "",
        }
    status = clean(report.get("status")) or "manual_identity_closure_ready"
    high_rows = sum(1 for row in closure_rows if clean(row.get("severity")).lower() in {"critical", "high"})
    blank_closures = sum(1 for row in closure_rows if not clean(row.get("operator_closure_decision")))
    manual_backfills = sum(1 for row in backfill_rows if clean(row.get("backfill_status")).lower() == "manual_review_required")
    blank_backfills = sum(1 for row in backfill_rows if not clean(row.get("operator_decision")))
    return {
        "active_athlete_identity_closure_cues": (
            f"{status}; closure_rows={closure_count}; high_or_critical={high_rows}; "
            f"blank_closure_decisions={blank_closures}; provider_backfill_rows={backfill_count}; "
            f"manual_backfill_review={manual_backfills}; blank_backfill_decisions={blank_backfills}"
        ),
        "athlete_identity_closure_artifact": "data/asset_registry/wnba/athlete_identity_closure_packet.md",
        "athlete_identity_backfill_artifact": "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv",
    }


def active_athlete_identity_for_packet(packet: Dict[str, str]) -> Dict[str, str]:
    packet_text = active_athlete_packet_text(packet)
    cues: List[str] = []
    hold_cue_found = False
    for row in read_csv("data/asset_registry/wnba/athlete_identity_review_packet.csv"):
        athlete_id = clean(row.get("athlete_id"))
        display_name = clean(row.get("display_name")) or clean(row.get("athlete_name")) or athlete_id.replace("_", " ").title()
        if not active_athlete_identity_matches(packet_text, display_name, athlete_id):
            continue
        hold = clean(row.get("identity_hold")).lower() == "true"
        default_approval = clean(row.get("default_approval_present")).lower() == "true"
        review_required = clean(row.get("review_required")).lower() == "true"
        if not (hold or default_approval or review_required):
            continue
        status = clean(row.get("identity_review_status")) or "identity_review_required"
        if hold or status.startswith("hold_"):
            hold_cue_found = True
        reasons = clean(row.get("hold_reason_codes")) or clean(row.get("issue_codes")) or "manual identity review required"
        evidence = clean(row.get("focused_evidence")) or clean(row.get("source_check_url")) or clean(row.get("provider_player_page_hint"))
        cue = f"{display_name}: {status}; {reasons}"
        if evidence:
            cue = f"{cue}; evidence={evidence}"
        if cue not in cues:
            cues.append(cue)
    if hold_cue_found:
        status = "hold_identity_review_required"
    elif cues:
        status = "athlete_identity_review_required"
    else:
        status = "athlete_identity_not_flagged"
    out = {
        "active_athlete_identity_status": status,
        "active_athlete_identity_cues": " | ".join(cues[:6]),
        "athlete_identity_artifact": "data/asset_registry/wnba/athlete_identity_review_packet.csv" if cues else "data/asset_registry/wnba/athlete_identity_audit.csv",
    }
    if cues:
        out.update(active_athlete_identity_closure_cues())
    return out


def build_render_prep_packets(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    packets: List[Dict[str, str]] = []
    for row in payload.get("render_readiness_queue", []):
        band = clean(row.get("band"))
        blockers = clean(row.get("blockers"))
        if band.startswith("hold_") or blockers not in {"", "none"}:
            continue
        enriched = enrich_render_row(row, payload)
        fit = template_fit_for_path(row.get("recommended_path", ""), row.get("source", ""))
        if looks_like_final_score(enriched, row):
            fit = final_score_template_fit()
        copy_polish = final_score_copy_polish(enriched, row, fit)
        visual_contract = render_visual_mode_contract(enriched, fit)
        asset_requirement = clean(visual_contract.get("asset_requirement")) or clean(fit.get("asset_requirement"))
        packet = {
            "packet_id": f"render_prep_{clean(row.get('rank')) or len(packets) + 1}_{packet_slug(row.get('title'))}",
            "packet_status": "ready_for_manual_render_review" if band == "render_ready_review" else "review_before_manual_render",
            "render_rank": clean(row.get("rank")),
            "render_readiness_score": clean(row.get("score")),
            "render_readiness_band": band,
            "title": clean(row.get("title")),
            "recommended_path": clean(row.get("recommended_path")),
            "source_artifact": clean(row.get("artifact")),
            "source_cue": clean(row.get("source_cue")),
            "asset_cue": clean(row.get("asset_cue")),
            "format_cue": clean(row.get("format_cue")),
            "manual_path": clean(row.get("manual_path")),
            "blockers": blockers or "none",
            "copy_headline": enriched["copy_headline"],
            "copy_dek": enriched["copy_dek"],
            "copy_context": enriched["copy_context"],
            **copy_polish,
            "top_performers": clean(enriched.get("top_performers")),
            "stat_module_status": clean(enriched.get("stat_module_status")) or "no_verified_stat_text",
            "stat_source_confidence": clean(enriched.get("stat_source_confidence")),
            "stat_source_label": clean(enriched.get("stat_source_label")),
            "stat_review_cue": clean(enriched.get("stat_review_cue")),
            "source_detail": enriched["source_detail"],
            "selected_template_id": "",
            "template_family": "",
            "reference_pack_id": "",
            **fit,
            **{key: value for key, value in visual_contract.items() if key != "asset_requirement"},
            "asset_requirement": asset_requirement,
            "active_logo_readiness_status": "",
            "active_logo_review_cues": "",
            "logo_review_artifact": "",
            "active_athlete_identity_status": "",
            "active_athlete_identity_cues": "",
            "athlete_identity_artifact": "",
            "active_asset_stop_go": "",
            "active_athlete_identity_closure_cues": "",
            "athlete_identity_closure_artifact": "",
            "athlete_identity_backfill_artifact": "",
            "renderer_fallback_cue": "",
            "manual_renderer_steps": "",
            "approval_gate": "human_visual_review_required_before_any_post",
            "auto_render_status": "not_rendered_by_generator",
            "publish_policy": "review_only_not_publish_ready",
            "paid_api_policy": "free_public_sources_only_no_paid_api",
        }
        packet.update(active_logo_readiness_for_packet(packet))
        packet.update(active_athlete_identity_for_packet(packet))
        packet["active_asset_stop_go"] = active_asset_stop_go(packet)
        packet["manual_renderer_steps"] = manual_renderer_steps(packet)
        packets.append(packet)
    return packets


def attach_render_prep_active_cues(render_queue: List[Dict[str, str]], render_prep_packets: List[Dict[str, str]]) -> None:
    prep_by_title = {clean(packet.get("title")): packet for packet in render_prep_packets}
    cue_fields = [
        "active_asset_stop_go",
        "active_logo_readiness_status",
        "active_athlete_identity_status",
    ]
    for row in render_queue:
        packet = prep_by_title.get(clean(row.get("title")))
        if not packet:
            continue
        for field in cue_fields:
            value = clean(packet.get(field))
            if value and not clean(row.get(field)):
                row[field] = value


def build_render_handoff_summary(render_prep_packets: List[Dict[str, str]]) -> Dict[str, Any]:
    if not render_prep_packets:
        return {
            "handoff_status": "no_render_prep_packet",
            "packet_id": "",
            "title": "",
            "folder": "render_handoff_top_packet",
            "readme": "render_handoff_top_packet/README.md",
            "files": [],
            "guardrails": {
                "review_only": True,
                "auto_approval": False,
                "auto_render": False,
                "auto_publish": False,
                "asset_downloads": False,
                "file_movement": False,
                "paid_apis": False,
                "publish_ready_lane": False,
                "publishing": False,
            },
        }
    packet = render_prep_packets[0]
    return {
        "handoff_status": "ready_for_manual_review",
        "packet_id": packet.get("packet_id", ""),
        "title": packet.get("title", ""),
        "active_asset_stop_go": packet.get("active_asset_stop_go", ""),
        "visual_mode": packet.get("visual_mode", ""),
        "hero_asset_required": packet.get("hero_asset_required", ""),
        "focal_entity_type": packet.get("focal_entity_type", ""),
        "score_lock_variant": packet.get("score_lock_variant", ""),
        "proof_strip_variant": packet.get("proof_strip_variant", ""),
        "copy_unlock_state": packet.get("copy_unlock_state", ""),
        "background_family": packet.get("background_family", ""),
        "template_fit_reason": packet.get("template_fit_reason", ""),
        "folder": "render_handoff_top_packet",
        "readme": "render_handoff_top_packet/README.md",
        "files": [
            "render_handoff_top_packet/README.md",
            "render_handoff_top_packet/copy_sheet.md",
            "render_handoff_top_packet/copy_sheet.csv",
            "render_handoff_top_packet/asset_checklist.md",
            "render_handoff_top_packet/asset_checklist.csv",
            "render_handoff_top_packet/active_asset_review_queue.md",
            "render_handoff_top_packet/active_asset_review_queue.csv",
            "render_handoff_top_packet/manual_asset_source_board.md",
            "render_handoff_top_packet/manual_asset_source_board.csv",
            "render_handoff_top_packet/manual_logo_verification_intake.md",
            "render_handoff_top_packet/manual_logo_verification_intake.csv",
            "render_handoff_top_packet/source_proof.md",
            "render_handoff_top_packet/manual_renderer_prompt.md",
            "render_handoff_top_packet/handoff_manifest.json",
        ],
        "guardrails": {
            "review_only": True,
            "auto_approval": False,
            "auto_render": False,
            "auto_publish": False,
            "asset_downloads": False,
            "file_movement": False,
            "paid_apis": False,
            "publish_ready_lane": False,
            "publishing": False,
        },
    }


def render_handoff_readme(payload: Dict[str, Any], packet: Dict[str, str] | None) -> str:
    if not packet:
        return "\n".join(
            [
                "# HSD Top Render Handoff",
                "",
                f"Generated: {payload['generated_at_utc']}",
                f"Command center version: {payload['version']}",
                "",
                "No render prep packet cleared the review gates for a top-packet handoff.",
                "",
                "Guardrails: review-only, no auto-rendering, no paid APIs, no auto-publishing.",
            "",
        ]
    )
    active_logo_status = clean(packet.get("active_logo_readiness_status")) or "logo_review_not_flagged"
    active_athlete_status = clean(packet.get("active_athlete_identity_status")) or "athlete_identity_not_flagged"
    active_asset_rows = active_asset_review_queue_rows(packet)
    blocking_rows = [row for row in active_asset_rows if clean(row.get("selected_template_blocking_status")).startswith("blocking_selected_template")]
    future_photo_rows = [row for row in active_asset_rows if clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_photo_not_required"]
    league_context_rows = [row for row in active_asset_rows if clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_league_mark_not_required"]
    return "\n".join(
        [
            "# HSD Top Render Handoff",
            "",
            f"Generated: {payload['generated_at_utc']}",
            f"Command center version: {payload['version']}",
            "",
            f"Packet: `{clean(packet.get('packet_id'))}`",
            f"Story: {clean(packet.get('title'))}",
            f"Status: `{clean(packet.get('packet_status'))}`",
            f"Readiness: `{clean(packet.get('render_readiness_score'))}/100` / `{clean(packet.get('render_readiness_band'))}`",
            f"Active asset stop/go: `{clean(packet.get('active_asset_stop_go')) or 'clear_no_active_asset_holds'}`",
            "",
            "## Active Review Holds",
            "",
            f"- Logo readiness: `{active_logo_status}`",
            f"- Logo cues: {clean(packet.get('active_logo_review_cues')) or 'none recorded'}",
            f"- Logo artifact: `{clean(packet.get('logo_review_artifact')) or 'data/asset_registry/asset_availability_audit.csv'}`",
            f"- Athlete identity: `{active_athlete_status}`",
            f"- Athlete identity cues: {clean(packet.get('active_athlete_identity_cues')) or 'none recorded'}",
            f"- Athlete identity artifact: `{clean(packet.get('athlete_identity_artifact')) or 'data/asset_registry/wnba/athlete_identity_audit.csv'}`",
            f"- Active asset stop/go: `{clean(packet.get('active_asset_stop_go')) or 'clear_no_active_asset_holds'}`",
            f"- Visual mode: `{clean(packet.get('visual_mode')) or 'manual_review_template'}`",
            f"- Hero asset required: `{clean(packet.get('hero_asset_required')) or 'operator_review'}`",
            f"- Focal entity: `{clean(packet.get('focal_entity_type')) or 'story'}`",
            f"- Template fit reason: {clean(packet.get('template_fit_reason')) or 'n/a'}",
            f"- Active queue scope: `{len(active_asset_rows)}` rows; selected-template blockers `{len(blocking_rows)}` ({active_queue_entity_list(blocking_rows)}); future photo-first holds `{len(future_photo_rows)}` ({active_queue_entity_list(future_photo_rows)}); league-mark context holds `{len(league_context_rows)}` ({active_queue_entity_list(league_context_rows)}).",
            (
                "- Selected-template scope: Player imagery is not required; athlete identity holds remain future photo-first review cues."
                if clean(packet.get("visual_mode")) == "no_photo_premium_result"
                else "- Selected-template scope: Resolve active athlete identity holds before any photo-first renderer use."
            ),
            f"- Athlete identity closure cues: {clean(packet.get('active_athlete_identity_closure_cues')) or 'none recorded'}",
            f"- Athlete identity closure packet: `{clean(packet.get('athlete_identity_closure_artifact')) or 'not generated'}`",
            f"- Athlete identity backfill packet: `{clean(packet.get('athlete_identity_backfill_artifact')) or 'not generated'}`",
            "- Treat these as stop/go review cues only; they do not approve assets or create a publish-ready lane.",
            "",
            "## Open These Files",
            "",
            "1. `copy_sheet.md`",
            "2. `asset_checklist.md`",
            "3. `active_asset_review_queue.md`",
            "4. `manual_asset_source_board.md`",
            "5. `manual_logo_verification_intake.md`",
            "6. `manual_league_mark_context_intake.md`",
            "7. `source_proof.md`",
            "8. `manual_renderer_prompt.md`",
            "9. `handoff_manifest.json`",
            "",
            "## Guardrails",
            "",
            "- Review-only handoff.",
            "- Does not render files.",
            "- Does not publish.",
            "- Does not call paid APIs.",
            "- Human visual review is required before any post.",
            "",
        ]
    )


def render_handoff_copy_sheet(packet: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Render Copy Sheet",
            "",
            f"- Headline: {clean(packet.get('copy_headline'))}",
            f"- Dek: {clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
            f"- Suggested title fit: {clean(packet.get('copy_suggested_title')) or clean(packet.get('copy_headline'))}",
            f"- Suggested dek fit: {clean(packet.get('copy_suggested_dek')) or clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
            f"- Fit cue: {clean(packet.get('copy_fit_cue')) or 'Tighten headline/dek before manual render if they wrap awkwardly.'}",
            f"- Polish note: {clean(packet.get('copy_polish_note')) or 'Use source-backed verbs and remove generic filler before visual review.'}",
            f"- Context: {clean(packet.get('copy_context')) or 'Operator fill-in after source review.'}",
            f"- Verified performer/stat text: {clean(packet.get('top_performers')) or 'none provided'}",
            f"- Stat module status: `{clean(packet.get('stat_module_status')) or 'no_verified_stat_text'}`",
            f"- Stat source confidence: `{clean(packet.get('stat_source_confidence')) or 'not_scored'}`",
            f"- Stat source label: {clean(packet.get('stat_source_label')) or 'n/a'}",
            f"- Stat review cue: {clean(packet.get('stat_review_cue')) or 'n/a'}",
            f"- Recommended path: `{clean(packet.get('recommended_path'))}`",
            f"- Template fit: `{clean(packet.get('template_fit'))}`",
            f"- Selected template: `{clean(packet.get('selected_template_id')) or 'operator_review'}`",
            f"- Template family: `{clean(packet.get('template_family')) or 'manual_review'}`",
            f"- Reference pack: `{clean(packet.get('reference_pack_id')) or 'none'}`",
            f"- Template shape: `{clean(packet.get('template_shape'))}`",
            f"- Visual mode: `{clean(packet.get('visual_mode')) or 'manual_review_template'}`",
            f"- Hero asset required: `{clean(packet.get('hero_asset_required')) or 'operator_review'}`",
            f"- Focal entity: `{clean(packet.get('focal_entity_type')) or 'story'}`",
            f"- Score lock: `{clean(packet.get('score_lock_variant')) or 'not_final_score'}`",
            f"- Proof strip: `{clean(packet.get('proof_strip_variant')) or 'source_check_only'}`",
            f"- Copy unlock: `{clean(packet.get('copy_unlock_state')) or 'manual_copy_locked_review'}`",
            f"- Background family: `{clean(packet.get('background_family')) or 'hsd_premium_sports_editorial'}`",
            f"- Template fit reason: {clean(packet.get('template_fit_reason')) or 'n/a'}",
            f"- Approval gate: `{clean(packet.get('approval_gate'))}`",
            "",
            "Copy is not approved for publishing until source proof and human visual review are complete.",
            "",
        ]
    )


def render_handoff_asset_checklist(packet: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Render Asset Checklist",
            "",
            f"- Asset cue: `{clean(packet.get('asset_cue'))}`",
            f"- Active asset stop/go: `{clean(packet.get('active_asset_stop_go')) or 'clear_no_active_asset_holds'}`",
            f"- Asset requirement: {clean(packet.get('asset_requirement'))}",
            f"- Visual mode: `{clean(packet.get('visual_mode')) or 'manual_review_template'}`",
            f"- Hero asset required: `{clean(packet.get('hero_asset_required')) or 'operator_review'}`",
            f"- Focal entity: `{clean(packet.get('focal_entity_type')) or 'story'}`",
            f"- Template fit reason: {clean(packet.get('template_fit_reason')) or 'n/a'}",
            (
                "- Selected-template scope: Player imagery is not required; athlete identity holds remain future photo-first review cues."
                if clean(packet.get("visual_mode")) == "no_photo_premium_result"
                else "- Selected-template scope: Resolve active athlete identity holds before any photo-first renderer use."
            ),
            f"- Active logo readiness: `{clean(packet.get('active_logo_readiness_status')) or 'logo_review_not_flagged'}`",
            f"- Active logo review cues: {clean(packet.get('active_logo_review_cues')) or 'none recorded'}",
            f"- Logo review artifact: `{clean(packet.get('logo_review_artifact')) or 'data/asset_registry/asset_availability_audit.csv'}`",
            f"- Active athlete identity: `{clean(packet.get('active_athlete_identity_status')) or 'athlete_identity_not_flagged'}`",
            f"- Active athlete identity cues: {clean(packet.get('active_athlete_identity_cues')) or 'none recorded'}",
            f"- Athlete identity artifact: `{clean(packet.get('athlete_identity_artifact')) or 'data/asset_registry/wnba/athlete_identity_audit.csv'}`",
            f"- Athlete identity closure cues: {clean(packet.get('active_athlete_identity_closure_cues')) or 'none recorded'}",
            f"- Athlete identity closure packet: `{clean(packet.get('athlete_identity_closure_artifact')) or 'not generated'}`",
            f"- Athlete identity backfill packet: `{clean(packet.get('athlete_identity_backfill_artifact')) or 'not generated'}`",
            f"- Renderer fallback cue: {clean(packet.get('renderer_fallback_cue')) or 'none recorded'}",
            f"- Manual path: `{clean(packet.get('manual_path'))}`",
            f"- Renderer family: `{clean(packet.get('renderer_family'))}`",
            "",
            "## Stop/Go",
            "",
            "- GO only if exact required logos/images are approved or the packet explicitly says no player asset is required.",
            "- HOLD this selected-template render if required team logos, source proof, format fit, or manual-path evidence is uncertain.",
            "- Keep future photo-first and optional league-mark issues review-only; they do not approve assets or create a publish-ready lane.",
            "- Do not use text-logo fallback for public graphics.",
            "",
        ]
    )


def logo_review_catalog_lookup() -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}
    for item in read_csv("data/asset_registry/wnba/logo_review_catalog.csv"):
        normalized = {key: clean(value) for key, value in item.items()}
        keys = {
            clean(normalized.get("entity_id")).lower(),
            clean(normalized.get("team_id")).lower(),
            clean(normalized.get("display_name")).lower(),
        }
        for key in keys:
            if key and key not in lookup:
                lookup[key] = normalized
    return lookup


def logo_review_catalog_row(row: Mapping[str, str], lookup: Mapping[str, Dict[str, str]]) -> Dict[str, str]:
    for value in (
        clean(row.get("entity_id")).lower(),
        clean(row.get("team_id")).lower(),
        clean(row.get("entity_name")).lower(),
    ):
        if value and value in lookup:
            return lookup[value]
    return {}


def local_asset_state(row: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    status = clean(catalog_row.get("status"))
    file_exists = clean(catalog_row.get("file_exists")).lower()
    approved = clean(catalog_row.get("registry_approved")).lower()
    manual_status = clean(row.get("manual_approval_status")).lower()
    source_confidence = clean(row.get("source_confidence")).lower()
    issue = clean(row.get("issue_type")).lower()
    if status:
        if "unapproved" in status or (file_exists == "true" and approved == "false"):
            return "present_but_unapproved"
        if "missing" in status or file_exists == "false":
            return "missing_or_unregistered"
        return status
    if "unapproved" in manual_status:
        return "present_but_unapproved"
    if "missing" in manual_status or "missing" in source_confidence or "missing" in issue:
        return "missing_or_unregistered"
    if clean(row.get("asset_path")) or clean(row.get("registered_path")):
        return "present_manual_review_required"
    return "manual_review_required"


def evidence_gap_status(row: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    source_policy = clean(catalog_row.get("source_policy_status")).lower()
    asset_state = local_asset_state(row, catalog_row)
    blocking_status = clean(row.get("selected_template_blocking_status"))
    if "non_official" in source_policy:
        return "present_unapproved_legacy_source_review"
    if "official_source_needed" in source_policy:
        return "official_source_needed_review_only"
    if blocking_status == "not_blocking_selected_template_league_mark_not_required":
        return "league_mark_context_missing_or_unregistered"
    if asset_state == "present_but_unapproved":
        return "present_but_unapproved"
    if asset_state == "missing_or_unregistered":
        return "missing_or_unregistered"
    if clean(row.get("source_check_url")):
        return "source_hint_present_manual_review_required"
    return "manual_evidence_review_required"


def current_registry_source(row: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    return (
        clean(catalog_row.get("current_registry_source_url"))
        or clean(row.get("source_check_url"))
        or "missing"
    )


def official_logo_source_candidate(row: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    return clean(catalog_row.get("official_source_url")) or manual_asset_source_candidate(dict(row))


def cannot_clear_automatically_reason(row: Mapping[str, str], catalog_row: Mapping[str, str]) -> str:
    name = clean(row.get("entity_name")) or clean(row.get("entity_id")) or "asset"
    blocking_status = clean(row.get("selected_template_blocking_status"))
    source_policy = clean(catalog_row.get("source_policy_status"))
    asset_state = local_asset_state(row, catalog_row)
    manual_status = clean(row.get("manual_approval_status")) or "manual_review_required"
    if blocking_status.startswith("blocking_selected_template"):
        return (
            f"{name} is selected-template blocking; local/source evidence and a human-edited manual approval "
            f"must be resolved first (asset_state={asset_state}; manual_approval_status={manual_status}; "
            f"source_policy={source_policy or 'manual_review_required'})."
        )
    if blocking_status == "not_blocking_selected_template_league_mark_not_required":
        return (
            f"{name} is league-mark context only for this packet; it stays review-only unless a template "
            f"explicitly requires a league mark (asset_state={asset_state}; manual_approval_status={manual_status})."
        )
    return (
        f"{name} requires manual evidence review before any renderer trust change "
        f"(asset_state={asset_state}; manual_approval_status={manual_status})."
    )


def add_asset_evidence_gap_fields(row: Dict[str, str], lookup: Mapping[str, Dict[str, str]]) -> Dict[str, str]:
    catalog_row = logo_review_catalog_row(row, lookup) if clean(row.get("asset_domain")) in {"team_logo", "league_logo"} else {}
    enriched = dict(row)
    enriched["official_source_candidate"] = (
        official_logo_source_candidate(row, catalog_row)
        if clean(row.get("asset_domain")) in {"team_logo", "league_logo"}
        else manual_asset_source_candidate(row)
    )
    enriched["current_registry_source"] = (
        current_registry_source(row, catalog_row)
        if clean(row.get("asset_domain")) in {"team_logo", "league_logo"}
        else clean(row.get("source_check_url")) or "manual_identity_source_required"
    )
    enriched["source_policy_status"] = clean(catalog_row.get("source_policy_status")) or "manual_review_required"
    enriched["local_asset_state"] = (
        local_asset_state(row, catalog_row)
        if clean(row.get("asset_domain")) in {"team_logo", "league_logo"}
        else "identity_review_required"
    )
    enriched["evidence_gap_status"] = (
        evidence_gap_status(row, catalog_row)
        if clean(row.get("asset_domain")) in {"team_logo", "league_logo"}
        else clean(row.get("identity_confidence")) or "manual_identity_review_required"
    )
    enriched["cannot_clear_automatically_because"] = cannot_clear_automatically_reason(row, catalog_row)
    if (
        clean(row.get("asset_domain")) == "league_logo"
        and clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_league_mark_not_required"
    ):
        enriched["allowed_decisions"] = (
            "verify_league_mark_for_review_only_renderer_use|hold_league_mark|"
            "mark_not_required_for_selected_template|revise_league_mark_source_metadata"
        )
        enriched["primary_action"] = "fill_league_mark_context_intake_or_mark_not_required_for_selected_template"
        enriched["operator_copy_target"] = "data/asset_registry/wnba/wnba_league_mark_review_intake.csv"
    return enriched


def active_asset_review_queue_rows(packet: Dict[str, str] | None) -> List[Dict[str, str]]:
    if not packet:
        return []
    packet_id = clean(packet.get("packet_id"))
    packet_text = active_logo_packet_text(packet)
    rows: List[Dict[str, str]] = []
    seen: set[str] = set()
    matched_logo_team_ids: set[str] = set()
    logo_catalog = logo_review_catalog_lookup()

    def add_row(row: Dict[str, str]) -> None:
        key = clean(row.get("review_queue_id"))
        if not key or key in seen:
            return
        seen.add(key)
        enriched = dict(row)
        for field, value in selected_template_blocking_status(packet, enriched).items():
            if not clean(enriched.get(field)):
                enriched[field] = value
        enriched = add_asset_evidence_gap_fields(enriched, logo_catalog)
        rows.append({field: clean(enriched.get(field)) for field in ACTIVE_ASSET_REVIEW_QUEUE_FIELDS})

    for item in read_csv("data/asset_registry/wnba/logo_review_packets.csv"):
        team_name = clean(item.get("team_name")) or clean(item.get("team_id"))
        team_id = clean(item.get("team_id"))
        if not active_logo_entity_matches(packet_text, team_name, team_id):
            continue
        matched_logo_team_ids.add(team_id)
        add_row(
            {
                "review_queue_id": clean(item.get("decision_packet_id")) or clean(item.get("packet_id")) or f"active_logo_{team_id}",
                "packet_id": packet_id,
                "asset_domain": "team_logo",
                "entity_type": "team",
                "entity_id": team_id,
                "entity_name": team_name,
                "team_id": team_id,
                "review_source": "data/asset_registry/wnba/logo_review_packets.csv",
                "review_status": clean(item.get("decision_review_status")) or clean(item.get("issue_type")) or "logo_review_required",
                "issue_type": clean(item.get("issue_type")),
                "registered_path": clean(item.get("registered_path")),
                "source_target_path": clean(item.get("source_target_path")),
                "asset_path": clean(item.get("registered_path")),
                "source_check_url": clean(item.get("source_url")),
                "decision_lane": "wnba_logo_review",
                "default_operator_decision": "hold_logo_slot",
                "asset_readiness": "local_logo_manual_review_required",
                "source_confidence": "source_url_present_manual_review_required" if clean(item.get("source_url")) else "source_missing_or_unregistered",
                "manual_approval_status": clean(item.get("decision_review_status")) or "manual_review_required",
                "renderer_fallback_cue": clean(item.get("renderer_fallback_cue")),
                "blocker_summary": clean(item.get("blocker_summary")) or clean(item.get("issue_summary")) or clean(item.get("hold_cue")),
                "allowed_decisions": clean(item.get("allowed_decisions")) or "approve_after_manual_review|hold_logo_slot|revise_registry_metadata",
                "primary_action": clean(item.get("primary_action")) or clean(item.get("hold_cue")),
                "evidence": clean(item.get("issue_summary")) or clean(item.get("hold_cue")),
                "manual_review_packet": clean(item.get("manual_review_packet")) or "data/asset_registry/wnba/logo_review_catalog_report.md",
                "operator_copy_target": clean(item.get("operator_copy_target")) or "operator/assets/brand_logos/README.md",
                "review_only": clean(item.get("review_only")) or "true",
                "publish_ready": clean(item.get("publish_ready")) or "false",
                "auto_approval": clean(item.get("auto_approval")) or "false",
                "auto_publish": clean(item.get("auto_publish")) or "false",
                "move_files": clean(item.get("move_files")) or "false",
                "paid_apis": clean(item.get("paid_apis")) or "false",
                "asset_downloads": clean(item.get("asset_downloads")) or "false",
                "review_only_policy": "logo_review_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
            }
        )

    audit = read_json("data/asset_registry/asset_availability_audit.json")
    findings = audit.get("findings") if isinstance(audit.get("findings"), list) else []
    for item in findings:
        domain = clean(item.get("asset_domain"))
        if domain not in {"team_logo", "league_logo"}:
            continue
        entity_id = clean(item.get("entity_id"))
        entity_name = clean(item.get("entity_name")) or entity_id
        league_mark = domain == "league_logo" and entity_id.lower() == "wnba" and "wnba" in packet_text
        if not league_mark and not active_logo_entity_matches(packet_text, entity_name, entity_id):
            continue
        if domain == "team_logo" and entity_id in matched_logo_team_ids:
            continue
        asset_path = clean(item.get("asset_path"))
        source_target_path = clean(item.get("source_target_path")) or clean(item.get("source_path")) or asset_path
        add_row(
            {
                "review_queue_id": clean(item.get("review_packet_id")) or f"active_{domain}_{entity_id}_{clean(item.get('finding')) or 'review'}",
                "packet_id": packet_id,
                "asset_domain": domain,
                "entity_type": clean(item.get("entity_type")) or ("league" if domain == "league_logo" else "team"),
                "entity_id": entity_id,
                "entity_name": entity_name,
                "team_id": "" if domain == "league_logo" else entity_id,
                "review_source": "data/asset_registry/asset_availability_audit.csv",
                "review_status": clean(item.get("finding")) or "asset_review_required",
                "issue_type": clean(item.get("finding")),
                "registered_path": clean(item.get("registered_path")) or asset_path,
                "source_target_path": source_target_path,
                "asset_path": asset_path,
                "decision_lane": clean(item.get("decision_lane")) or audit_decision_lane(domain, clean(item.get("finding")), clean(item.get("league"))),
                "default_operator_decision": clean(item.get("default_operator_decision")) or audit_default_operator_decision(domain, clean(item.get("finding"))),
                "asset_readiness": audit_asset_readiness(item),
                "source_confidence": clean(item.get("source_confidence")) or ("source_missing_or_unregistered" if domain in {"team_logo", "league_logo"} and "missing" in clean(item.get("finding")) else ""),
                "identity_confidence": clean(item.get("identity_confidence")),
                "manual_approval_status": clean(item.get("manual_approval_status")) or clean(item.get("approval_status")),
                "renderer_fallback_cue": clean(item.get("renderer_fallback_cue")),
                "blocker_summary": clean(item.get("blocker_summary")) or f"{entity_name}: {clean(item.get('finding')) or 'asset_review_required'}; default decision={clean(item.get('default_operator_decision')) or audit_default_operator_decision(domain, clean(item.get('finding')))}; readiness={audit_asset_readiness(item) or 'manual_review_required'}",
                "allowed_decisions": clean(item.get("allowed_operator_decisions")) or "hold_asset_slot|request_exact_logo_evidence|revise_registry_metadata",
                "primary_action": clean(item.get("decision_primary_action")) or clean(item.get("recommended_next_step")) or "manual asset review required",
                "evidence": clean(item.get("evidence")),
                "manual_review_packet": clean(item.get("manual_review_packet")) or "data/asset_registry/wnba/logo_review_catalog_report.md",
                "operator_copy_target": clean(item.get("operator_copy_target")) or "operator/assets/brand_logos/README.md",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
                "review_only_policy": "asset_audit_review_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
            }
        )

    for item in read_csv("data/asset_registry/wnba/athlete_identity_review_packet.csv"):
        athlete_id = clean(item.get("athlete_id"))
        display_name = clean(item.get("display_name")) or clean(item.get("athlete_name")) or athlete_id.replace("_", " ").title()
        if not active_athlete_identity_matches(active_athlete_packet_text(packet), display_name, athlete_id):
            continue
        add_row(
            {
                "review_queue_id": clean(item.get("review_packet_id")) or f"active_athlete_{athlete_id}",
                "packet_id": packet_id,
                "asset_domain": "athlete_photo",
                "entity_type": "athlete",
                "entity_id": athlete_id,
                "entity_name": display_name,
                "team_id": clean(item.get("team_id")),
                "review_source": "data/asset_registry/wnba/athlete_identity_review_packet.csv",
                "review_status": clean(item.get("identity_review_status")) or "identity_review_required",
                "issue_type": clean(item.get("hold_reason_codes")),
                "asset_path": clean(item.get("asset_path")),
                "source_check_url": clean(item.get("source_check_url")) or clean(item.get("provider_player_page_hint")),
                "provider_player_id": clean(item.get("provider_player_id")),
                "approved_marker_path": clean(item.get("approved_marker_path")),
                "decision_lane": "wnba_athlete_identity_resolution",
                "default_operator_decision": "hold_identity",
                "asset_readiness": "blocked_until_identity_resolution",
                "identity_confidence": "identity_hold_default_or_suspicious_approval" if clean(item.get("identity_hold")).lower() == "true" or clean(item.get("default_approval_present")).lower() == "true" else clean(item.get("highest_severity")),
                "manual_approval_status": clean(item.get("identity_review_status")) or "manual_review_required",
                "blocker_summary": clean(item.get("blocker_summary")) or clean(item.get("hold_reason_codes")) or clean(item.get("focused_evidence")),
                "allowed_decisions": clean(item.get("allowed_decisions")) or "hold_identity|revise_asset|backfill_provider_id_only|identity_verified_approved_for_review_renders",
                "primary_action": clean(item.get("operator_review_steps")) or "manual identity review required",
                "evidence": clean(item.get("focused_evidence")),
                "identity_closure_cues": clean(packet.get("active_athlete_identity_closure_cues")),
                "identity_closure_artifact": clean(packet.get("athlete_identity_closure_artifact")),
                "identity_backfill_artifact": clean(packet.get("athlete_identity_backfill_artifact")),
                "manual_review_packet": clean(item.get("manual_review_packet")) or "data/asset_registry/wnba/athlete_identity_resolution_workflow.md",
                "operator_copy_target": clean(item.get("operator_copy_target")) or "operator/inbox/wnba_athlete_identity_resolution.csv",
                "review_only": "true",
                "publish_ready": clean(item.get("publish_ready")) or "false",
                "auto_approval": clean(item.get("auto_approval")) or "false",
                "auto_publish": clean(item.get("auto_publish")) or "false",
                "move_files": clean(item.get("move_files")) or "false",
                "paid_apis": clean(item.get("paid_apis")) or "false",
                "asset_downloads": "false",
                "review_only_policy": clean(item.get("review_only_policy")) or "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
            }
        )
    return rows


def active_queue_entity_list(rows: List[Dict[str, str]], *, limit: int = 6) -> str:
    names = [clean(row.get("entity_name")) or clean(row.get("entity_id")) for row in rows]
    names = [name for name in names if name]
    if not names:
        return "none"
    if len(names) <= limit:
        return " | ".join(names)
    return " | ".join(names[:limit]) + f" | +{len(names) - limit} more"


def active_queue_evidence_gap_list(rows: List[Dict[str, str]], *, limit: int = 4) -> str:
    parts: List[str] = []
    for row in rows:
        name = clean(row.get("entity_name")) or clean(row.get("entity_id"))
        status = clean(row.get("evidence_gap_status")) or "manual_evidence_review_required"
        reason = clean(row.get("cannot_clear_automatically_because"))
        if not name:
            continue
        parts.append(f"{name}: {status}; {reason}" if reason else f"{name}: {status}")
    if not parts:
        return "none"
    if len(parts) <= limit:
        return " | ".join(parts)
    return " | ".join(parts[:limit]) + f" | +{len(parts) - limit} more"


def manual_asset_source_priority(row: Dict[str, str]) -> str:
    blocking_status = clean(row.get("selected_template_blocking_status"))
    if blocking_status.startswith("blocking_selected_template"):
        return "P0_selected_template_hold"
    if blocking_status == "not_blocking_selected_template_photo_not_required":
        return "P1_future_photo_first_hold"
    if blocking_status == "not_blocking_selected_template_league_mark_not_required":
        return "P2_league_mark_context"
    return "P3_manual_asset_review"


def manual_asset_required_label(row: Dict[str, str]) -> str:
    domain = clean(row.get("asset_domain"))
    name = clean(row.get("entity_name")) or clean(row.get("entity_id"))
    if domain == "athlete_photo":
        return f"Verified athlete photo identity evidence for {name}"
    if domain == "league_logo":
        return f"Exact official league mark evidence for {name}"
    if domain == "team_logo":
        return f"Exact official team logo evidence for {name}"
    return f"Manual asset evidence for {name}"


def manual_asset_source_candidate(row: Dict[str, str]) -> str:
    source_url = clean(row.get("source_check_url"))
    if source_url:
        return source_url
    domain = clean(row.get("asset_domain"))
    name = clean(row.get("entity_name")) or clean(row.get("entity_id"))
    team_id = clean(row.get("team_id"))
    if domain == "athlete_photo":
        team = f" / {team_id}" if team_id else ""
        return f"Official WNBA or team roster/profile page for {name}{team}; manual lookup only"
    if domain == "league_logo":
        return "Official WNBA brand, media, or league page; manual lookup only"
    if domain == "team_logo":
        return f"Official {name} team site, media guide, or WNBA team page; manual lookup only"
    return "Official/free public source candidate; manual lookup only"


def manual_asset_free_source_candidate(row: Dict[str, str]) -> str:
    domain = clean(row.get("asset_domain"))
    if domain == "athlete_photo":
        return "Free public official roster/profile evidence; do not download or approve from this board"
    if domain in {"team_logo", "league_logo"}:
        return "Free public official logo/source evidence; do not download or move files from this board"
    return "Free public source evidence only; no paid APIs and no automatic downloads"


def manual_asset_search_query(row: Dict[str, str]) -> str:
    name = clean(row.get("entity_name")) or clean(row.get("entity_id"))
    team = clean(row.get("team_id"))
    domain = clean(row.get("asset_domain"))
    if domain == "athlete_photo":
        team_part = f" {team.replace('_', ' ')}" if team else ""
        return f'"{name}"{team_part} WNBA official player profile photo'
    if domain == "league_logo":
        return '"WNBA" official logo PNG brand'
    if domain == "team_logo":
        return f'"{name}" official logo PNG WNBA'
    return f'"{name}" official source evidence'


def manual_asset_source_board_rows(active_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for index, row in enumerate(active_rows, 1):
        board_row = {
            "source_board_id": f"manual_asset_source_{index:03d}_{clean(row.get('review_queue_id')) or clean(row.get('entity_id'))}",
            "packet_id": clean(row.get("packet_id")),
            "priority": manual_asset_source_priority(row),
            "asset_domain": clean(row.get("asset_domain")),
            "entity_type": clean(row.get("entity_type")),
            "entity_id": clean(row.get("entity_id")),
            "entity_name": clean(row.get("entity_name")),
            "team_id": clean(row.get("team_id")),
            "source_board_lane": clean(row.get("decision_lane")) or "manual_asset_review",
            "required_asset": manual_asset_required_label(row),
            "official_source_candidate": clean(row.get("official_source_candidate")) or manual_asset_source_candidate(row),
            "free_source_candidate": manual_asset_free_source_candidate(row),
            "manual_search_query": manual_asset_search_query(row),
            "source_hint_url": clean(row.get("source_check_url")),
            "current_local_asset": clean(row.get("asset_path")) or clean(row.get("registered_path")),
            "registry_source_target": clean(row.get("source_target_path")) or clean(row.get("registered_path")),
            "current_registry_source": clean(row.get("current_registry_source")) or "missing",
            "source_policy_status": clean(row.get("source_policy_status")) or "manual_review_required",
            "evidence_gap_status": clean(row.get("evidence_gap_status")) or "manual_evidence_review_required",
            "local_asset_state": clean(row.get("local_asset_state")) or "manual_review_required",
            "cannot_clear_automatically_because": clean(row.get("cannot_clear_automatically_because"))
            or "Manual evidence review is required before any renderer trust change.",
            "source_confidence": clean(row.get("source_confidence")),
            "identity_confidence": clean(row.get("identity_confidence")),
            "manual_approval_status": clean(row.get("manual_approval_status")) or "manual_review_required",
            "recommended_operator_action": clean(row.get("primary_action")) or "manual source review required",
            "manual_review_packet": clean(row.get("manual_review_packet")),
            "operator_copy_target": clean(row.get("operator_copy_target")),
            "allowed_decisions": clean(row.get("allowed_decisions")),
            "legacy_reference_model": "D:/Her Sports Daily asset-index/DDG packet shape used as reference only",
            "review_only": "true",
            "manual_approval_required": "true",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "asset_downloads": "false",
        }
        rows.append({field: clean(board_row.get(field)) for field in MANUAL_ASSET_SOURCE_BOARD_FIELDS})
    return rows


def manual_logo_verification_intake_rows(source_board_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for index, row in enumerate(source_board_rows, 1):
        if clean(row.get("priority")) != "P0_selected_template_hold" or clean(row.get("asset_domain")) != "team_logo":
            continue
        entity_id = clean(row.get("entity_id"))
        entity_name = clean(row.get("entity_name")) or entity_id
        intake_row = {
            "intake_bridge_id": f"manual_logo_intake_{index:03d}_{entity_id or re.sub(r'[^a-z0-9]+', '_', entity_name.lower()).strip('_')}",
            "packet_id": clean(row.get("packet_id")),
            "priority": clean(row.get("priority")),
            "asset_domain": clean(row.get("asset_domain")),
            "entity_id": entity_id,
            "entity_name": entity_name,
            "selected_template_blocking_status": "blocking_selected_template_logo_review",
            "local_logo_path": clean(row.get("current_local_asset")),
            "official_source_candidate": clean(row.get("official_source_candidate")),
            "current_legacy_registry_source": clean(row.get("current_registry_source")) or "missing",
            "current_unapproved_status": clean(row.get("manual_approval_status")) or "unapproved_review_required",
            "source_policy_status": clean(row.get("source_policy_status")) or clean(row.get("evidence_gap_status")),
            "evidence_gap_status": clean(row.get("evidence_gap_status")),
            "manual_intake_files": "data/asset_registry/wnba/team_logos.csv|data/asset_registry/wnba/logo_sources.csv",
            "manual_intake_files_detail": (
                "Human operator verifies the local logo against the official source, then manually edits "
                "team_logos.csv approval fields and logo_sources.csv source metadata if evidence supports it."
            ),
            "manual_review_packet": clean(row.get("manual_review_packet")) or "data/asset_registry/wnba/logo_review_catalog_report.md",
            "operator_copy_target": clean(row.get("operator_copy_target")) or "operator/assets/brand_logos/README.md",
            "required_manual_checks": (
                "confirm exact local logo path exists; compare logo to official Liberty/WNBA source; confirm current "
                "legacy registry source; decide whether manual registry edit is justified"
            ),
            "allowed_manual_outcomes": "hold_logo_slot|revise_logo_source_metadata|human_edit_registry_after_review",
            "cannot_clear_automatically_because": clean(row.get("cannot_clear_automatically_because")),
            "review_only": "true",
            "approval_state_change": "false",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "asset_downloads": "false",
            "publishing": "false",
        }
        rows.append({field: clean(intake_row.get(field)) for field in MANUAL_LOGO_VERIFICATION_INTAKE_FIELDS})
    return rows


def manual_league_mark_context_intake_rows(source_board_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for index, row in enumerate(source_board_rows, 1):
        if clean(row.get("priority")) != "P2_league_mark_context" or clean(row.get("asset_domain")) != "league_logo":
            continue
        entity_id = clean(row.get("entity_id")) or "WNBA"
        entity_name = clean(row.get("entity_name")) or entity_id
        intake_row = {
            "league_mark_intake_id": f"manual_league_mark_intake_{index:03d}_{entity_id.lower()}",
            "packet_id": clean(row.get("packet_id")),
            "priority": clean(row.get("priority")),
            "asset_domain": clean(row.get("asset_domain")),
            "entity_id": entity_id,
            "entity_name": entity_name,
            "selected_template_blocking_status": clean(row.get("selected_template_blocking_status"))
            or "not_blocking_selected_template_league_mark_not_required",
            "selected_template_blocking_reason": (
                "Current selected final-score template uses team logo slots; the WNBA league mark remains optional "
                "review-only context unless a future selected template explicitly requires a league mark."
            ),
            "local_league_mark_path": clean(row.get("current_local_asset")) or "assets/leagues/wnba/logo.png",
            "official_source_candidate": clean(row.get("official_source_candidate")) or "https://www.wnba.com/",
            "current_registry_source": clean(row.get("current_registry_source")) or "missing",
            "current_approval_status": clean(row.get("manual_approval_status")) or "manual_review_required",
            "source_policy_status": clean(row.get("source_policy_status")) or "official_source_needed_review_only",
            "evidence_gap_status": clean(row.get("evidence_gap_status")) or "official_source_needed_review_only",
            "manual_intake_files": "data/asset_registry/wnba/wnba_league_mark_review_intake.csv",
            "manual_intake_files_detail": (
                "Human operator records whether the WNBA league mark is verified, held, not required for the "
                "selected template, or needs source metadata revision. This generator does not apply the decision."
            ),
            "manual_review_packet": clean(row.get("manual_review_packet")) or "data/asset_registry/wnba/logo_review_catalog_report.md",
            "operator_copy_target": clean(row.get("operator_copy_target")) or "operator/assets/brand_logos/README.md",
            "required_manual_checks": (
                "confirm the selected template actually requires a league mark; if yes, verify an exact local WNBA "
                "mark path and official/free source evidence before any later registry edit"
            ),
            "allowed_manual_outcomes": (
                "verify_league_mark_for_review_only_renderer_use|hold_league_mark|"
                "mark_not_required_for_selected_template|revise_league_mark_source_metadata"
            ),
            "template_requirement_rule": "non_blocking_until_selected_template_requires_league_mark",
            "cannot_clear_automatically_because": clean(row.get("cannot_clear_automatically_because"))
            or "The WNBA league mark needs human source/file review before any renderer trust change.",
            "review_only": "true",
            "approval_state_change": "false",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "asset_downloads": "false",
            "publishing": "false",
        }
        rows.append({field: clean(intake_row.get(field)) for field in MANUAL_LEAGUE_MARK_CONTEXT_INTAKE_FIELDS})
    return rows


def decision_stop_go_summary(
    packet: Dict[str, str] | None,
    active_rows: List[Dict[str, str]],
    source_board_rows: List[Dict[str, str]],
) -> Dict[str, Any]:
    blocking_rows = [
        row
        for row in active_rows
        if clean(row.get("selected_template_blocking_status")).startswith("blocking_selected_template")
    ]
    future_photo_rows = [
        row
        for row in active_rows
        if clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_photo_not_required"
    ]
    league_context_rows = [
        row
        for row in active_rows
        if clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_league_mark_not_required"
    ]
    if blocking_rows:
        status = "hold_selected_template_manual_asset_review"
        status_tone = "warn"
        next_step = "Clear selected-template blockers first; future photo-first and league-mark context rows stay review-only."
    elif future_photo_rows or league_context_rows:
        status = "manual_context_review_only"
        status_tone = "neutral"
        next_step = "No selected-template asset blocker is active; keep context rows review-only until a future template requires them."
    else:
        status = "clear_no_active_asset_holds"
        status_tone = "good"
        next_step = "No active asset stop/go rows were matched for the top render packet."
    return {
        "panel_status": status,
        "status_tone": status_tone,
        "packet_id": clean(packet.get("packet_id")) if packet else "",
        "title": clean(packet.get("title")) if packet else "No active render packet",
        "active_asset_stop_go": clean(packet.get("active_asset_stop_go")) if packet else "clear_no_active_asset_holds",
        "selected_template_blockers": len(blocking_rows),
        "selected_template_entities": active_queue_entity_list(blocking_rows),
        "selected_template_evidence_gaps": active_queue_evidence_gap_list(blocking_rows),
        "future_photo_first_holds": len(future_photo_rows),
        "future_photo_first_entities": active_queue_entity_list(future_photo_rows),
        "league_mark_context_holds": len(league_context_rows),
        "league_mark_context_entities": active_queue_entity_list(league_context_rows),
        "league_mark_evidence_gaps": active_queue_evidence_gap_list(league_context_rows),
        "active_queue_rows": len(active_rows),
        "source_board_rows": len(source_board_rows),
        "active_queue_artifact": "render_handoff_top_packet/active_asset_review_queue.md",
        "manual_asset_source_board_artifact": "render_handoff_top_packet/manual_asset_source_board.md",
        "manual_logo_verification_intake_artifact": "render_handoff_top_packet/manual_logo_verification_intake.md",
        "manual_league_mark_context_intake_artifact": "render_handoff_top_packet/manual_league_mark_context_intake.md",
        "next_step": next_step,
        "guardrail_summary": "review-only; no downloads; no auto-approval; no file movement; no publishing; no publish-ready lane",
    }


def decision_review_order_checklist(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    def add_step(rank: int, title: str, artifact: str, reason: str, action: str) -> None:
        rows.append(
            {
                "rank": str(rank),
                "title": title,
                "artifact": artifact,
                "reason": reason,
                "operator_action": action,
                "review_only": "true",
                "approval_state_change": "false",
                "asset_downloads": "false",
                "auto_approval": "false",
                "file_movement": "false",
                "publishing": "false",
            }
        )

    selected_count = as_int(summary.get("selected_template_blockers"))
    future_count = as_int(summary.get("future_photo_first_holds"))
    league_count = as_int(summary.get("league_mark_context_holds"))
    active_count = as_int(summary.get("active_queue_rows"))
    source_board_count = as_int(summary.get("source_board_rows"))
    if active_count:
        add_step(
            1,
            "Open active asset queue",
            clean(summary.get("active_queue_artifact")) or "render_handoff_top_packet/active_asset_review_queue.md",
            f"Confirm selected-template blockers ({summary.get('selected_template_entities') or 'none'}), future photo-first holds ({summary.get('future_photo_first_entities') or 'none'}), and league-mark context ({summary.get('league_mark_context_entities') or 'none'}).",
            "Read the stop/go row labels before deciding whether the render stays held.",
        )
    if source_board_count:
        add_step(
            len(rows) + 1,
            "Open Manual Asset Source Board",
            clean(summary.get("manual_asset_source_board_artifact")) or "render_handoff_top_packet/manual_asset_source_board.md",
            "Review official/free source candidates for the active hold rows without downloading or approving assets.",
            "Use it as manual evidence guidance only; do not copy files or change approval state.",
        )
    if selected_count:
        add_step(
            len(rows) + 1,
            "Open Manual Logo Verification Intake Bridge",
            clean(summary.get("manual_logo_verification_intake_artifact")) or "render_handoff_top_packet/manual_logo_verification_intake.md",
            "Use the intake bridge to see the exact local logo path, official source candidate, current legacy source, and human-edited registry files.",
            "Keep it review-only; only a human-edited registry update can clear the selected-template logo blocker.",
        )
    if league_count:
        add_step(
            len(rows) + 1,
            "Open Manual League-Mark Context Intake",
            clean(summary.get("manual_league_mark_context_intake_artifact"))
            or "render_handoff_top_packet/manual_league_mark_context_intake.md",
            "Use the league-mark intake to decide whether WNBA is verified for review-only use, held, or simply not required by the selected template.",
            "Keep it display/manual only; no asset is approved unless a human later edits the league-mark intake and registry files.",
        )
    if selected_count or league_count:
        add_step(
            len(rows) + 1,
            "Open WNBA logo review catalog",
            "data/asset_registry/wnba/logo_review_catalog_report.md",
            "Logo review is the current selected-template path, with optional league-mark context tracked separately.",
            "Check source trust, exact local path, and manual review notes before any renderer trust change.",
        )
    if future_count and not selected_count:
        add_step(
            len(rows) + 1,
            "Open athlete identity workflow",
            "data/asset_registry/wnba/athlete_identity_resolution_workflow.md",
            "Future photo-first rows are active context, not selected-template blockers.",
            "Keep photo-first use held until human identity review is complete.",
        )
    if not rows:
        add_step(
            1,
            "No active asset review rows",
            clean(summary.get("active_queue_artifact")) or "render_handoff_top_packet/active_asset_review_queue.md",
            "No active selected-template, photo-first, or league-mark rows were matched.",
            "Continue normal manual source and visual QA review.",
        )
    return rows


def render_manual_asset_source_board(packet: Dict[str, str] | None, rows: List[Dict[str, str]]) -> str:
    lines = [
        "# Manual Asset Source Board",
        "",
        f"Packet: `{clean(packet.get('packet_id')) if packet else ''}`",
        f"Story: {clean(packet.get('title')) if packet else 'No active render packet'}",
        "",
        "Review-only source board for active WNBA logo and athlete identity holds. Legacy `D:\\Her Sports Daily` asset-index/DDG packets are reference shape only; this board does not copy, download, approve, move, publish, or create a publish-ready lane.",
        "",
        "## Guardrails",
        "",
        "- review_only=true",
        "- manual_approval_required=true",
        "- publish_ready=false",
        "- auto_approval=false",
        "- auto_publish=false",
        "- move_files=false",
        "- paid_apis=false",
        "- asset_downloads=false",
        "",
    ]
    if not rows:
        lines += ["No active WNBA logo or athlete identity holds were available for source-board rows.", ""]
        return "\n".join(lines)
    lines += [
        "## Summary",
        "",
        f"- Source-board rows: {len(rows)}",
        f"- P0 selected-template holds: {sum(1 for row in rows if clean(row.get('priority')) == 'P0_selected_template_hold')}",
        f"- Future photo-first holds: {sum(1 for row in rows if clean(row.get('priority')) == 'P1_future_photo_first_hold')}",
        f"- League-mark context rows: {sum(1 for row in rows if clean(row.get('priority')) == 'P2_league_mark_context')}",
        "- Review order: clear P0 selected-template logo holds first; keep future photo-first and league-mark rows review-only.",
        "",
        "## Rows",
        "",
    ]
    for index, row in enumerate(rows, 1):
        lines += [
            f"### {index}. {clean(row.get('entity_name')) or clean(row.get('entity_id'))}",
            "",
            f"- Priority: `{clean(row.get('priority'))}`",
            f"- Lane: `{clean(row.get('source_board_lane'))}`",
            f"- Required asset: {clean(row.get('required_asset'))}",
            f"- Official/free candidate: {clean(row.get('official_source_candidate'))}",
            f"- Manual search query: `{clean(row.get('manual_search_query'))}`",
            f"- Source hint URL: {clean(row.get('source_hint_url')) or 'n/a'}",
            f"- Current local asset: `{clean(row.get('current_local_asset')) or 'n/a'}`",
            f"- Registry/source target: `{clean(row.get('registry_source_target')) or 'n/a'}`",
            f"- Current registry source: {clean(row.get('current_registry_source')) or 'missing'}",
            f"- Source policy status: `{clean(row.get('source_policy_status')) or 'manual_review_required'}`",
            f"- Evidence gap status: `{clean(row.get('evidence_gap_status')) or 'manual_evidence_review_required'}`",
            f"- Local asset state: `{clean(row.get('local_asset_state')) or 'manual_review_required'}`",
            f"- Cannot clear automatically because: {clean(row.get('cannot_clear_automatically_because')) or 'Manual evidence review is required before any renderer trust change.'}",
            f"- Source confidence: `{clean(row.get('source_confidence')) or 'manual_review_required'}`",
            f"- Identity confidence: `{clean(row.get('identity_confidence')) or 'n/a'}`",
            f"- Manual approval status: `{clean(row.get('manual_approval_status'))}`",
            f"- Recommended operator action: {clean(row.get('recommended_operator_action'))}",
            f"- Manual review packet: `{clean(row.get('manual_review_packet')) or 'n/a'}`",
            f"- Operator copy target: `{clean(row.get('operator_copy_target')) or 'n/a'}`",
            f"- Allowed decisions: `{clean(row.get('allowed_decisions'))}`",
            f"- Legacy reference: {clean(row.get('legacy_reference_model'))}",
            f"- Guardrails: review_only={clean(row.get('review_only'))}; manual_approval_required={clean(row.get('manual_approval_required'))}; publish_ready={clean(row.get('publish_ready'))}; auto_approval={clean(row.get('auto_approval'))}; auto_publish={clean(row.get('auto_publish'))}; move_files={clean(row.get('move_files'))}; paid_apis={clean(row.get('paid_apis'))}; asset_downloads={clean(row.get('asset_downloads'))}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_manual_logo_verification_intake(packet: Dict[str, str] | None, rows: List[Dict[str, str]]) -> str:
    lines = [
        "# Manual Logo Verification Intake Bridge",
        "",
        f"Packet: `{clean(packet.get('packet_id')) if packet else ''}`",
        f"Story: {clean(packet.get('title')) if packet else 'No active render packet'}",
        "",
        "Review-only bridge for selected-template team logo blockers. This file does not approve assets, download files, move files, publish, or create a publish-ready lane.",
        "",
        "## Guardrails",
        "",
        "- review_only=true",
        "- approval_state_change=false",
        "- publish_ready=false",
        "- auto_approval=false",
        "- auto_publish=false",
        "- move_files=false",
        "- paid_apis=false",
        "- asset_downloads=false",
        "- publishing=false",
        "",
    ]
    if not rows:
        lines += ["No selected-template team logo intake bridge rows were available.", ""]
        return "\n".join(lines)
    lines += [
        "## Summary",
        "",
        f"- Intake bridge rows: {len(rows)}",
        "- Human-edited intake files: `data/asset_registry/wnba/team_logos.csv`; `data/asset_registry/wnba/logo_sources.csv`",
        "- Use this as review guidance only. The operator must make any registry edits manually after source review.",
        "",
        "## Rows",
        "",
    ]
    for index, row in enumerate(rows, 1):
        lines += [
            f"### {index}. {clean(row.get('entity_name')) or clean(row.get('entity_id'))}",
            "",
            f"- Selected-template blocker: `{clean(row.get('selected_template_blocking_status'))}`",
            f"- Exact local logo path: `{clean(row.get('local_logo_path')) or 'missing'}`",
            f"- Official source candidate: {clean(row.get('official_source_candidate')) or 'manual lookup required'}",
            f"- Current legacy registry source: {clean(row.get('current_legacy_registry_source')) or 'missing'}",
            f"- Current unapproved status: `{clean(row.get('current_unapproved_status'))}`",
            f"- Source policy status: `{clean(row.get('source_policy_status'))}`",
            f"- Evidence gap status: `{clean(row.get('evidence_gap_status'))}`",
            f"- Human-edited manual intake files: `{clean(row.get('manual_intake_files'))}`",
            f"- Manual intake detail: {clean(row.get('manual_intake_files_detail'))}",
            f"- Manual review packet: `{clean(row.get('manual_review_packet'))}`",
            f"- Operator copy target: `{clean(row.get('operator_copy_target'))}`",
            f"- Required manual checks: {clean(row.get('required_manual_checks'))}",
            f"- Allowed manual outcomes: `{clean(row.get('allowed_manual_outcomes'))}`",
            f"- Cannot clear automatically because: {clean(row.get('cannot_clear_automatically_because'))}",
            f"- Guardrails: review_only={clean(row.get('review_only'))}; approval_state_change={clean(row.get('approval_state_change'))}; publish_ready={clean(row.get('publish_ready'))}; auto_approval={clean(row.get('auto_approval'))}; auto_publish={clean(row.get('auto_publish'))}; move_files={clean(row.get('move_files'))}; paid_apis={clean(row.get('paid_apis'))}; asset_downloads={clean(row.get('asset_downloads'))}; publishing={clean(row.get('publishing'))}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_manual_league_mark_context_intake(packet: Dict[str, str] | None, rows: List[Dict[str, str]]) -> str:
    lines = [
        "# Manual League-Mark Context Intake",
        "",
        f"Packet: `{clean(packet.get('packet_id')) if packet else ''}`",
        f"Story: {clean(packet.get('title')) if packet else 'No active render packet'}",
        "",
        "Review-only bridge for optional WNBA league-mark context. This file does not approve assets, download files, move files, publish, or create a publish-ready lane.",
        "",
        "## Guardrails",
        "",
        "- review_only=true",
        "- approval_state_change=false",
        "- publish_ready=false",
        "- auto_approval=false",
        "- auto_publish=false",
        "- move_files=false",
        "- paid_apis=false",
        "- asset_downloads=false",
        "- publishing=false",
        "",
    ]
    if not rows:
        lines += ["No league-mark context intake rows were available.", ""]
        return "\n".join(lines)
    lines += [
        "## Summary",
        "",
        f"- Intake bridge rows: {len(rows)}",
        "- Human-edited intake file: `data/asset_registry/wnba/wnba_league_mark_review_intake.csv`",
        "- Selected-template rule: keep WNBA league mark optional/non-blocking unless the selected template explicitly requires it.",
        "- Use this as review guidance only. The operator must make any registry edits manually after source and local-file review.",
        "",
        "## Rows",
        "",
    ]
    for index, row in enumerate(rows, 1):
        lines += [
            f"### {index}. {clean(row.get('entity_name')) or clean(row.get('entity_id'))}",
            "",
            f"- League-mark status: `{clean(row.get('selected_template_blocking_status'))}`",
            f"- Selected-template rule: {clean(row.get('selected_template_blocking_reason'))}",
            f"- Local league-mark path: `{clean(row.get('local_league_mark_path')) or 'missing'}`",
            f"- Official source candidate: {clean(row.get('official_source_candidate')) or 'manual lookup required'}",
            f"- Current registry source: {clean(row.get('current_registry_source')) or 'missing'}",
            f"- Current approval status: `{clean(row.get('current_approval_status'))}`",
            f"- Source policy status: `{clean(row.get('source_policy_status'))}`",
            f"- Evidence gap status: `{clean(row.get('evidence_gap_status'))}`",
            f"- Human-edited manual intake file: `{clean(row.get('manual_intake_files'))}`",
            f"- Manual intake detail: {clean(row.get('manual_intake_files_detail'))}",
            f"- Manual review packet: `{clean(row.get('manual_review_packet'))}`",
            f"- Operator copy target: `{clean(row.get('operator_copy_target'))}`",
            f"- Required manual checks: {clean(row.get('required_manual_checks'))}",
            f"- Allowed manual outcomes: `{clean(row.get('allowed_manual_outcomes'))}`",
            f"- Template requirement rule: `{clean(row.get('template_requirement_rule'))}`",
            f"- Cannot clear automatically because: {clean(row.get('cannot_clear_automatically_because'))}",
            f"- Guardrails: review_only={clean(row.get('review_only'))}; approval_state_change={clean(row.get('approval_state_change'))}; publish_ready={clean(row.get('publish_ready'))}; auto_approval={clean(row.get('auto_approval'))}; auto_publish={clean(row.get('auto_publish'))}; move_files={clean(row.get('move_files'))}; paid_apis={clean(row.get('paid_apis'))}; asset_downloads={clean(row.get('asset_downloads'))}; publishing={clean(row.get('publishing'))}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_active_asset_review_queue(packet: Dict[str, str] | None, rows: List[Dict[str, str]]) -> str:
    lines = [
        "# Active Asset Review Queue",
        "",
        f"Packet: `{clean(packet.get('packet_id')) if packet else ''}`",
        f"Story: {clean(packet.get('title')) if packet else 'No active render packet'}",
        "",
        "Review-only queue for assets named by the top render handoff. These rows do not approve assets, download files, move files, publish, or create a publish-ready lane.",
        "",
    ]
    if not rows:
        lines += ["No active logo or athlete identity review rows were matched.", ""]
        return "\n".join(lines)
    blocking_rows = [row for row in rows if clean(row.get("selected_template_blocking_status")).startswith("blocking_selected_template")]
    future_photo_rows = [row for row in rows if clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_photo_not_required"]
    league_context_rows = [row for row in rows if clean(row.get("selected_template_blocking_status")) == "not_blocking_selected_template_league_mark_not_required"]
    lines += [
        "## Summary",
        "",
        f"- Total review rows: {len(rows)}",
        f"- Blocking selected template now: {len(blocking_rows)}",
        f"- Future photo-first holds: {len(future_photo_rows)}",
        f"- League-mark context holds: {len(league_context_rows)}",
        f"- Blocking entities: {active_queue_entity_list(blocking_rows)}",
        f"- Future photo-first entities: {active_queue_entity_list(future_photo_rows)}",
        f"- League-mark context entities: {active_queue_entity_list(league_context_rows)}",
        "- Immediate manual path: clear the blocking selected-template rows first; future photo-first and league-mark context holds stay review-only.",
        "",
        "## Rows",
        "",
    ]
    for index, row in enumerate(rows, 1):
        evidence_lines: List[str] = []
        evidence = clean(row.get("evidence"))
        if evidence:
            evidence_lines.append(f"- Evidence: {short(evidence, 260)}")
        packet_target_lines: List[str] = []
        if clean(row.get("manual_review_packet")):
            packet_target_lines.append(f"- Manual review packet: `{clean(row.get('manual_review_packet'))}`")
        if clean(row.get("operator_copy_target")):
            packet_target_lines.append(f"- Operator copy target: `{clean(row.get('operator_copy_target'))}`")
        decision_metadata_lines: List[str] = []
        if clean(row.get("selected_template_blocking_status")):
            decision_metadata_lines.append(
                f"- Selected template blocker: `{clean(row.get('selected_template_blocking_status'))}` - {clean(row.get('selected_template_blocking_reason'))}"
            )
        for label, field in [
            ("Decision lane", "decision_lane"),
            ("Default operator decision", "default_operator_decision"),
            ("Asset readiness", "asset_readiness"),
            ("Source confidence", "source_confidence"),
            ("Identity confidence", "identity_confidence"),
            ("Manual approval status", "manual_approval_status"),
            ("Renderer fallback cue", "renderer_fallback_cue"),
        ]:
            if clean(row.get(field)):
                decision_metadata_lines.append(f"- {label}: `{clean(row.get(field))}`")
        if clean(row.get("blocker_summary")):
            decision_metadata_lines.append(f"- Blocker summary: {short(clean(row.get('blocker_summary')), 260)}")
        identity_detail_lines: List[str] = []
        if clean(row.get("provider_player_id")):
            identity_detail_lines.append(f"- Provider player ID: `{clean(row.get('provider_player_id'))}`")
        if clean(row.get("approved_marker_path")):
            identity_detail_lines.append(f"- Approved marker path: `{clean(row.get('approved_marker_path'))}`")
        closure_lines: List[str] = []
        if clean(row.get("identity_closure_cues")):
            closure_lines.append(f"- Identity closure cues: {clean(row.get('identity_closure_cues'))}")
        if clean(row.get("identity_closure_artifact")):
            closure_lines.append(f"- Identity closure packet: `{clean(row.get('identity_closure_artifact'))}`")
        if clean(row.get("identity_backfill_artifact")):
            closure_lines.append(f"- Identity backfill packet: `{clean(row.get('identity_backfill_artifact'))}`")
        lines += [
            f"### {index}. {clean(row.get('entity_name')) or clean(row.get('entity_id'))}",
            "",
            f"- Domain: `{clean(row.get('asset_domain'))}`",
            f"- Status: `{clean(row.get('review_status'))}`",
            f"- Review queue ID: `{clean(row.get('review_queue_id')) or 'n/a'}`",
            f"- Review source: `{clean(row.get('review_source')) or 'n/a'}`",
            f"- Issue: {clean(row.get('issue_type')) or 'review required'}",
            f"- Registered path: `{clean(row.get('registered_path')) or 'n/a'}`",
            f"- Source target path: `{clean(row.get('source_target_path')) or 'n/a'}`",
            f"- Asset path: `{clean(row.get('asset_path')) or 'n/a'}`",
            f"- Source check URL: {clean(row.get('source_check_url')) or 'n/a'}",
            f"- Official source candidate: {clean(row.get('official_source_candidate')) or 'manual lookup required'}",
            f"- Current registry source: {clean(row.get('current_registry_source')) or 'missing'}",
            f"- Evidence gap status: `{clean(row.get('evidence_gap_status')) or 'manual_evidence_review_required'}`",
            f"- Local asset state: `{clean(row.get('local_asset_state')) or 'manual_review_required'}`",
            f"- Cannot clear automatically because: {clean(row.get('cannot_clear_automatically_because')) or 'Manual evidence review is required before any renderer trust change.'}",
            f"- Allowed decisions: `{clean(row.get('allowed_decisions'))}`",
            f"- Primary action: {clean(row.get('primary_action')) or 'manual review required'}",
            *evidence_lines,
            *packet_target_lines,
            *decision_metadata_lines,
            *identity_detail_lines,
            *closure_lines,
            f"- Review-only policy: {clean(row.get('review_only_policy')) or 'review_only_no_auto_approval_no_file_movement_no_publish_ready_lane'}",
            f"- Guardrails: review_only={clean(row.get('review_only'))}; publish_ready={clean(row.get('publish_ready'))}; auto_approval={clean(row.get('auto_approval'))}; auto_publish={clean(row.get('auto_publish'))}; move_files={clean(row.get('move_files'))}; paid_apis={clean(row.get('paid_apis'))}; asset_downloads={clean(row.get('asset_downloads'))}",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def render_handoff_source_proof(packet: Dict[str, str]) -> str:
    return "\n".join(
        [
            "# Render Source Proof",
            "",
            f"- Source artifact: `{clean(packet.get('source_artifact'))}`",
            f"- Source cue: `{clean(packet.get('source_cue'))}`",
            f"- Source detail: {clean(packet.get('source_detail')) or 'n/a'}",
            f"- Source/copy context: {clean(packet.get('copy_context')) or 'n/a'}",
            f"- Performer/stat evidence: {clean(packet.get('top_performers')) or 'none provided'}",
            f"- Stat source confidence: `{clean(packet.get('stat_source_confidence')) or 'not_scored'}`",
            f"- Stat review cue: {clean(packet.get('stat_review_cue')) or 'n/a'}",
            f"- Paid API policy: `{clean(packet.get('paid_api_policy'))}`",
            "",
            "## Required Human Check",
            "",
            f"1. Open {clean(packet.get('source_artifact'))} manually.",
            "2. Confirm the headline, dek, and context match verified source facts.",
            "3. Hold the render if a second source, official confirmation, or source timestamp is missing.",
            "",
        ]
    )


def render_manual_renderer_prompt(packet: Dict[str, str]) -> str:
    steps = split_manual_renderer_steps(packet.get("manual_renderer_steps"))
    lines = [
        "# Manual Renderer Prompt",
        "",
        "Use this prompt manually only. Do not auto-render, auto-post, or publish.",
        "",
        "## Brief",
        "",
        f"Create a review-only HSD graphic for: {clean(packet.get('title'))}",
        "",
        "## Copy",
        "",
        f"- Headline: {clean(packet.get('copy_headline'))}",
        f"- Dek: {clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
        f"- Suggested title fit: {clean(packet.get('copy_suggested_title')) or clean(packet.get('copy_headline'))}",
        f"- Suggested dek fit: {clean(packet.get('copy_suggested_dek')) or clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
        f"- Fit cue: {clean(packet.get('copy_fit_cue')) or 'Tighten headline/dek before manual render if they wrap awkwardly.'}",
        f"- Polish note: {clean(packet.get('copy_polish_note')) or 'Use source-backed verbs and remove generic filler before visual review.'}",
        f"- Context: {clean(packet.get('copy_context')) or 'Operator fill-in after source review.'}",
        f"- Verified performer/stat text: {clean(packet.get('top_performers')) or 'none provided'}",
        f"- Stat source confidence: {clean(packet.get('stat_source_confidence')) or 'not_scored'}",
        f"- Stat review cue: {clean(packet.get('stat_review_cue')) or 'n/a'}",
        "",
        "## Format",
        "",
        f"- Template fit: {clean(packet.get('template_fit'))}",
        f"- Selected template: {clean(packet.get('selected_template_id')) or 'operator_review'}",
        f"- Template family: {clean(packet.get('template_family')) or 'manual_review'}",
        f"- Reference pack: {clean(packet.get('reference_pack_id')) or 'none'}",
        f"- Shape: {clean(packet.get('template_shape'))}",
        f"- Renderer family: {clean(packet.get('renderer_family'))}",
        f"- Visual mode: {clean(packet.get('visual_mode')) or 'manual_review_template'}",
        f"- Focal entity: {clean(packet.get('focal_entity_type')) or 'story'}",
        f"- Hero asset required: {clean(packet.get('hero_asset_required')) or 'operator_review'}",
        f"- Score lock: {clean(packet.get('score_lock_variant')) or 'not_final_score'}",
        f"- Proof strip: {clean(packet.get('proof_strip_variant')) or 'source_check_only'}",
        f"- Copy unlock: {clean(packet.get('copy_unlock_state')) or 'manual_copy_locked_review'}",
        f"- Background family: {clean(packet.get('background_family')) or 'hsd_premium_sports_editorial'}",
        f"- Template fit reason: {clean(packet.get('template_fit_reason')) or 'n/a'}",
        "",
        "## Assets",
        "",
        f"- {clean(packet.get('asset_requirement'))}",
        f"- Active asset stop/go: {clean(packet.get('active_asset_stop_go')) or 'clear_no_active_asset_holds'}",
        (
            "- Selected-template scope: Player imagery is not required; athlete identity holds remain future photo-first review cues."
            if clean(packet.get("visual_mode")) == "no_photo_premium_result"
            else "- Selected-template scope: Resolve active athlete identity holds before any photo-first renderer use."
        ),
        "- Review order: clear selected-template blockers first; future photo-first and league-mark context holds stay review-only.",
        f"- Active logo readiness: {clean(packet.get('active_logo_readiness_status')) or 'logo_review_not_flagged'}",
        f"- Active logo review cues: {clean(packet.get('active_logo_review_cues')) or 'none recorded'}",
        f"- Active athlete identity: {clean(packet.get('active_athlete_identity_status')) or 'athlete_identity_not_flagged'}",
        f"- Active athlete identity cues: {clean(packet.get('active_athlete_identity_cues')) or 'none recorded'}",
        f"- Athlete identity closure cues: {clean(packet.get('active_athlete_identity_closure_cues')) or 'none recorded'}",
        f"- Athlete identity closure packet: {clean(packet.get('athlete_identity_closure_artifact')) or 'not generated'}",
        f"- Athlete identity backfill packet: {clean(packet.get('athlete_identity_backfill_artifact')) or 'not generated'}",
        f"- Renderer fallback cue: {clean(packet.get('renderer_fallback_cue')) or 'none recorded'}",
        "",
        "## Steps",
        "",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(steps, 1))
    lines += [
        "",
        "## Guardrail",
        "",
        "Output is for human visual review only. Nothing in this folder is publish-ready by itself.",
        "",
    ]
    return "\n".join(lines)


def write_render_handoff_outputs(payload: Dict[str, Any]) -> None:
    packets = payload.get("render_prep_packets", [])
    packet = packets[0] if packets else None
    manifest_packet = dict(packet) if packet else {}
    if manifest_packet:
        manifest_packet["raw_blockers"] = clean(packet.get("blockers")) or "none"
        manifest_packet["blockers"] = display_render_blockers(packet)
    manifest_active_asset_rows = active_asset_review_queue_rows(packet) if packet else []
    manifest_manual_source_rows = manual_asset_source_board_rows(manifest_active_asset_rows)
    manifest_logo_intake_rows = manual_logo_verification_intake_rows(manifest_manual_source_rows)
    manifest_league_mark_intake_rows = manual_league_mark_context_intake_rows(manifest_manual_source_rows)
    write_text(OUT_RENDER_HANDOFF_README, render_handoff_readme(payload, packet))
    manifest = {
        "version": payload["version"],
        "generated_at_utc": payload["generated_at_utc"],
        "handoff_status": "ready_for_manual_review" if packet else "no_render_prep_packet",
        "folder": "render_handoff_top_packet",
        "guardrails": {
            "review_only": True,
            "auto_approval": False,
            "auto_render": False,
            "auto_publish": False,
            "asset_downloads": False,
            "file_movement": False,
            "paid_apis": False,
            "publish_ready_lane": False,
            "publishing": False,
        },
        "packet": manifest_packet,
        "manual_asset_source_board": {
            "rows": len(manifest_manual_source_rows),
            "review_only": True,
            "manual_approval_required": True,
            "asset_downloads": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
            "publish_ready": False,
            "artifact": "manual_asset_source_board.md",
            "data_artifact": "manual_asset_source_board.csv",
            "legacy_reference_model": "D:/Her Sports Daily asset-index/DDG packet shape used as reference only",
        },
        "manual_logo_verification_intake": {
            "rows": len(manifest_logo_intake_rows),
            "review_only": True,
            "approval_state_change": False,
            "asset_downloads": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
            "publish_ready": False,
            "publishing": False,
            "artifact": "manual_logo_verification_intake.md",
            "data_artifact": "manual_logo_verification_intake.csv",
            "human_intake_files": [
                "data/asset_registry/wnba/team_logos.csv",
                "data/asset_registry/wnba/logo_sources.csv",
            ],
        },
        "manual_league_mark_context_intake": {
            "rows": len(manifest_league_mark_intake_rows),
            "review_only": True,
            "approval_state_change": False,
            "asset_downloads": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
            "publish_ready": False,
            "publishing": False,
            "artifact": "manual_league_mark_context_intake.md",
            "data_artifact": "manual_league_mark_context_intake.csv",
            "human_intake_files": [
                "data/asset_registry/wnba/wnba_league_mark_review_intake.csv",
            ],
            "template_requirement_rule": "non_blocking_until_selected_template_requires_league_mark",
        },
        "files": [
            "README.md",
            "copy_sheet.md",
            "copy_sheet.csv",
            "asset_checklist.md",
            "asset_checklist.csv",
            "active_asset_review_queue.md",
            "active_asset_review_queue.csv",
            "manual_asset_source_board.md",
            "manual_asset_source_board.csv",
            "manual_logo_verification_intake.md",
            "manual_logo_verification_intake.csv",
            "manual_league_mark_context_intake.md",
            "manual_league_mark_context_intake.csv",
            "source_proof.md",
            "manual_renderer_prompt.md",
            "handoff_manifest.json",
        ],
    }
    existing_manifest_path = find_existing_input("render_handoff_top_packet/handoff_manifest.json")
    existing_manifest = read_json("render_handoff_top_packet/handoff_manifest.json") if existing_manifest_path.exists() else {}
    existing_packet = existing_manifest.get("packet") if isinstance(existing_manifest, dict) else {}
    if (
        isinstance(existing_packet, dict)
        and json.dumps(existing_packet, sort_keys=True, default=str) == json.dumps(manifest_packet, sort_keys=True, default=str)
        and clean(existing_manifest.get("generated_at_utc"))
    ):
        manifest["generated_at_utc"] = clean(existing_manifest.get("generated_at_utc"))
    if packet:
        write_text(OUT_RENDER_HANDOFF_COPY, render_handoff_copy_sheet(packet))
        write_csv(
            OUT_RENDER_HANDOFF_COPY_CSV,
            [
                {
                    "packet_id": packet.get("packet_id"),
                    "headline": packet.get("copy_headline"),
                    "dek": packet.get("copy_dek"),
                    "context": packet.get("copy_context"),
                    "suggested_title": packet.get("copy_suggested_title"),
                    "suggested_dek": packet.get("copy_suggested_dek"),
                    "fit_cue": packet.get("copy_fit_cue"),
                    "polish_note": packet.get("copy_polish_note"),
                    "top_performers": packet.get("top_performers"),
                    "stat_module_status": packet.get("stat_module_status"),
                    "stat_source_confidence": packet.get("stat_source_confidence"),
                    "stat_source_label": packet.get("stat_source_label"),
                    "stat_review_cue": packet.get("stat_review_cue"),
                    "template_fit": packet.get("template_fit"),
                    "selected_template_id": packet.get("selected_template_id"),
                    "template_family": packet.get("template_family"),
                    "reference_pack_id": packet.get("reference_pack_id"),
                    "template_shape": packet.get("template_shape"),
                    "visual_mode": packet.get("visual_mode"),
                    "hero_asset_required": packet.get("hero_asset_required"),
                    "focal_entity_type": packet.get("focal_entity_type"),
                    "score_lock_variant": packet.get("score_lock_variant"),
                    "proof_strip_variant": packet.get("proof_strip_variant"),
                    "copy_unlock_state": packet.get("copy_unlock_state"),
                    "background_family": packet.get("background_family"),
                    "template_fit_reason": packet.get("template_fit_reason"),
                    "approval_gate": packet.get("approval_gate"),
                }
            ],
            [
                "packet_id",
                "headline",
                "dek",
                "context",
                "suggested_title",
                "suggested_dek",
                "fit_cue",
                "polish_note",
                "top_performers",
                "stat_module_status",
                "stat_source_confidence",
                "stat_source_label",
                "stat_review_cue",
                "template_fit",
                "selected_template_id",
                "template_family",
                "reference_pack_id",
                "template_shape",
                "visual_mode",
                "hero_asset_required",
                "focal_entity_type",
                "score_lock_variant",
                "proof_strip_variant",
                "copy_unlock_state",
                "background_family",
                "template_fit_reason",
                "approval_gate",
            ],
        )
        write_text(OUT_RENDER_HANDOFF_ASSETS, render_handoff_asset_checklist(packet))
        write_csv(
            OUT_RENDER_HANDOFF_ASSETS_CSV,
            [
                {
                    "packet_id": packet.get("packet_id"),
                    "asset_cue": packet.get("asset_cue"),
                    "active_asset_stop_go": packet.get("active_asset_stop_go"),
                    "asset_requirement": packet.get("asset_requirement"),
                    "active_logo_readiness_status": packet.get("active_logo_readiness_status"),
                    "active_logo_review_cues": packet.get("active_logo_review_cues"),
                    "logo_review_artifact": packet.get("logo_review_artifact"),
                    "active_athlete_identity_status": packet.get("active_athlete_identity_status"),
                    "active_athlete_identity_cues": packet.get("active_athlete_identity_cues"),
                    "athlete_identity_artifact": packet.get("athlete_identity_artifact"),
                    "active_athlete_identity_closure_cues": packet.get("active_athlete_identity_closure_cues"),
                    "athlete_identity_closure_artifact": packet.get("athlete_identity_closure_artifact"),
                    "athlete_identity_backfill_artifact": packet.get("athlete_identity_backfill_artifact"),
                    "renderer_fallback_cue": packet.get("renderer_fallback_cue"),
                    "manual_path": packet.get("manual_path"),
                    "renderer_family": packet.get("renderer_family"),
                    "visual_mode": packet.get("visual_mode"),
                    "hero_asset_required": packet.get("hero_asset_required"),
                    "focal_entity_type": packet.get("focal_entity_type"),
                    "score_lock_variant": packet.get("score_lock_variant"),
                    "proof_strip_variant": packet.get("proof_strip_variant"),
                    "copy_unlock_state": packet.get("copy_unlock_state"),
                    "background_family": packet.get("background_family"),
                    "template_fit_reason": packet.get("template_fit_reason"),
                    "decision": "operator_review_required",
                }
            ],
            [
                "packet_id",
                "asset_cue",
                "active_asset_stop_go",
                "asset_requirement",
                "active_logo_readiness_status",
                "active_logo_review_cues",
                "logo_review_artifact",
                "active_athlete_identity_status",
                "active_athlete_identity_cues",
                "athlete_identity_artifact",
                "active_athlete_identity_closure_cues",
                "athlete_identity_closure_artifact",
                "athlete_identity_backfill_artifact",
                "renderer_fallback_cue",
                "manual_path",
                "renderer_family",
                "visual_mode",
                "hero_asset_required",
                "focal_entity_type",
                "score_lock_variant",
                "proof_strip_variant",
                "copy_unlock_state",
                "background_family",
                "template_fit_reason",
                "decision",
            ],
        )
        active_asset_rows = manifest_active_asset_rows
        manual_asset_source_rows = manifest_manual_source_rows
        manual_logo_intake_rows = manifest_logo_intake_rows
        manual_league_mark_intake_rows = manifest_league_mark_intake_rows
        write_text(OUT_RENDER_HANDOFF_ACTIVE_ASSET_QUEUE, render_active_asset_review_queue(packet, active_asset_rows))
        write_csv(OUT_RENDER_HANDOFF_ACTIVE_ASSET_QUEUE_CSV, active_asset_rows, ACTIVE_ASSET_REVIEW_QUEUE_FIELDS)
        write_text(OUT_RENDER_HANDOFF_MANUAL_ASSET_SOURCE_BOARD, render_manual_asset_source_board(packet, manual_asset_source_rows))
        write_csv(OUT_RENDER_HANDOFF_MANUAL_ASSET_SOURCE_BOARD_CSV, manual_asset_source_rows, MANUAL_ASSET_SOURCE_BOARD_FIELDS)
        write_text(OUT_RENDER_HANDOFF_LOGO_VERIFICATION_INTAKE, render_manual_logo_verification_intake(packet, manual_logo_intake_rows))
        write_csv(OUT_RENDER_HANDOFF_LOGO_VERIFICATION_INTAKE_CSV, manual_logo_intake_rows, MANUAL_LOGO_VERIFICATION_INTAKE_FIELDS)
        write_text(OUT_RENDER_HANDOFF_LEAGUE_MARK_INTAKE, render_manual_league_mark_context_intake(packet, manual_league_mark_intake_rows))
        write_csv(OUT_RENDER_HANDOFF_LEAGUE_MARK_INTAKE_CSV, manual_league_mark_intake_rows, MANUAL_LEAGUE_MARK_CONTEXT_INTAKE_FIELDS)
        write_text(OUT_RENDER_HANDOFF_SOURCE_PROOF, render_handoff_source_proof(packet))
        write_text(OUT_RENDER_HANDOFF_PROMPT, render_manual_renderer_prompt(packet))
    else:
        write_text(OUT_RENDER_HANDOFF_ACTIVE_ASSET_QUEUE, render_active_asset_review_queue(None, []))
        write_csv(OUT_RENDER_HANDOFF_ACTIVE_ASSET_QUEUE_CSV, [], ACTIVE_ASSET_REVIEW_QUEUE_FIELDS)
        write_text(OUT_RENDER_HANDOFF_MANUAL_ASSET_SOURCE_BOARD, render_manual_asset_source_board(None, []))
        write_csv(OUT_RENDER_HANDOFF_MANUAL_ASSET_SOURCE_BOARD_CSV, [], MANUAL_ASSET_SOURCE_BOARD_FIELDS)
        write_text(OUT_RENDER_HANDOFF_LOGO_VERIFICATION_INTAKE, render_manual_logo_verification_intake(None, []))
        write_csv(OUT_RENDER_HANDOFF_LOGO_VERIFICATION_INTAKE_CSV, [], MANUAL_LOGO_VERIFICATION_INTAKE_FIELDS)
        write_text(OUT_RENDER_HANDOFF_LEAGUE_MARK_INTAKE, render_manual_league_mark_context_intake(None, []))
        write_csv(OUT_RENDER_HANDOFF_LEAGUE_MARK_INTAKE_CSV, [], MANUAL_LEAGUE_MARK_CONTEXT_INTAKE_FIELDS)
    write_json(OUT_RENDER_HANDOFF_MANIFEST, manifest)


def schedule_rows() -> List[Dict[str, str]]:
    rows = parse_markdown_table("bebe_posting_schedule_today.md")
    normalized: List[Dict[str, str]] = []
    for row in rows[:12]:
        normalized.append(
            {
                "time": first_present(row.get("Time ET"), row.get("Time")),
                "platform": first_present(row.get("Platform")),
                "slot": first_present(row.get("Slot")),
                "status": first_present(row.get("Status"), default="operator_action"),
                "action": first_present(row.get("Recommended action"), row.get("Action")),
                "artifact": first_present(row.get("Artifact")),
            }
        )
    return normalized


def build_next_actions(
    operator: Dict[str, Any],
    guard: Dict[str, Any],
    candidates: List[Dict[str, str]],
    studio: List[Dict[str, str]],
    render_queue: List[Dict[str, str]],
    render_prep_packets: List[Dict[str, str]],
    render_handoff_summary: Dict[str, Any],
    source_board: List[Dict[str, str]],
    promotions: List[Dict[str, str]],
    coverage_map: List[Dict[str, str]],
    proposal_review: List[Dict[str, str]],
    source_proposal_draft: List[Dict[str, str]],
    source_proposal_promotion_checklist: List[Dict[str, str]],
    source_registry_update_worksheet: List[Dict[str, str]],
    source_registry_diff_review: List[Dict[str, str]],
    source_registry_same_domain_resolution: List[Dict[str, str]],
    source_registry_verification_log: List[Dict[str, str]],
    source_registry_approval_packet: List[Dict[str, str]],
    source_registry_patch_preview: List[Dict[str, str]],
    source_registry_post_edit_validation: List[Dict[str, str]],
    source_proposal_pack_readiness: List[Dict[str, str]],
    source_proposal_packs: List[Dict[str, str]],
    artifacts: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    artifact_exists = {row["path"]: bool(row["exists"]) for row in artifacts}
    artifact_commands = {row["path"]: clean(row.get("run_command")) for row in artifacts}
    actions: List[Dict[str, str]] = []
    issues = operator.get("issues") or guard.get("issues") or []
    critical = [issue for issue in issues if clean(issue.get("severity")).lower() == "critical"] if isinstance(issues, list) else []

    def add_action(status: str, owner: str, title: str, detail: str, artifact: str, command: str = "") -> None:
        if not title or any(existing.get("title") == title for existing in actions):
            return
        actions.append(
            {
                "rank": str(len(actions) + 1),
                "status": status,
                "owner": owner,
                "title": title,
                "detail": detail,
                "artifact": artifact,
                "command": command,
            }
        )

    if studio and not artifact_exists.get("graphics_upload_pack_status.csv"):
        command = artifact_commands.get("graphics_upload_pack_status.csv") or RUN_COMMANDS["graphics_upload_pack_status.csv"]
        add_action(
            "Build next",
            "Graphics",
            f"Build graphics pack for {studio[0]['name']}",
            (
                "This is the fastest unblocker: the publish guard has no ready graphics upload pack. "
                f"Use the top Studio bundle: {studio[0]['detail']}"
            ),
            "studio_bundle_queue.csv",
            command,
        )

    ready_candidates = [item for item in candidates if item.get("status") in {"Ready", "Graphics ready"}]
    if ready_candidates:
        item = ready_candidates[0]
        source_note = f"{item.get('source_count') or '0'} source(s)" if item.get("source_count") else "source count not reported"
        grade_note = f"Source grade: {item.get('source_grade') or 'not_scored'}"
        if item.get("source_score"):
            grade_note += f" ({item['source_score']})"
        add_action(
            "Editorial check",
            "Editor",
            f"Review top candidate: {item['headline']}",
            f"{item['detail']} Confirm facts, headline, and source posture before it becomes a manual post. {source_note}. {grade_note}.",
            item["artifact"],
        )

    if promotions:
        promo = promotions[0]
        freshness_note = f"{promo.get('freshness_label') or 'undated'}"
        if promo.get("freshness_source"):
            freshness_note += f" via {promo['freshness_source']}"
        evidence_note = f"{promo.get('detail')}. " if promo.get("detail") else ""
        opportunity_note = ""
        if as_int(promo.get("story_opportunity_size")) > 1:
            opportunity_note = (
                f"Grouped opportunity with {promo.get('story_opportunity_size')} related official/wire leads "
                f"from {promo.get('story_opportunity_sources')}. "
            )
        angle_note = ""
        if promo.get("story_opportunity_angle") or promo.get("story_opportunity_recommended_path"):
            angle_note = (
                f"Angle: {promo.get('story_opportunity_angle') or 'review'}; "
                f"path: {promo.get('story_opportunity_recommended_path') or promo.get('recommendation')}. "
            )
        readiness_bits = [
            promo.get("story_opportunity_confidence_tier"),
            promo.get("story_opportunity_source_coverage"),
            promo.get("story_opportunity_confirmation_cue"),
            promo.get("story_opportunity_asset_cue"),
        ]
        readiness_note = " / ".join(bit for bit in readiness_bits if bit)
        if readiness_note:
            readiness_note = f"Readiness: {readiness_note}. "
        if promo.get("story_opportunity_readiness_note"):
            readiness_note += f"{promo['story_opportunity_readiness_note']} "
        second_source_note = ""
        if promo.get("story_opportunity_second_source_id"):
            second_source_note = (
                f"Suggested second source: {promo['story_opportunity_second_source_id']} "
                f"({promo.get('story_opportunity_second_source_lane') or 'source_review'}). "
            )
        elif promo.get("story_opportunity_second_source_lane") == "already_covered":
            second_source_note = "Second-source status: already covered by distinct free sources. "
        add_action(
            "Lead promotion",
            "Editor",
            f"Promote source lead toward {promo['recommendation']}: {promo['title']}",
            f"{promo['priority']} / {promo['lane']} / quality {promo.get('quality_score') or 'n/a'} / {freshness_note}. {opportunity_note}{angle_note}{readiness_note}{second_source_note}{evidence_note}{promo.get('next_step') or promo.get('reason')}",
            promo["artifact"],
        )

    if render_queue:
        prep_by_title = {clean(packet.get("title")): packet for packet in render_prep_packets}
        ready_render_rows = [row for row in render_queue if row.get("band") == "render_ready_review"]
        blocked_render_rows = [row for row in render_queue if row.get("band", "").startswith("hold_")]
        prep_render_rows = [row for row in render_queue if row.get("band") == "render_prep_candidate"]
        if ready_render_rows:
            row = ready_render_rows[0]
            packet = prep_by_title.get(clean(row.get("title")), {})
            stop_go = clean(packet.get("active_asset_stop_go"))
            readiness_detail = "Source, asset, format, and manual path cues are ready for human review."
            if stop_go.startswith("hold_"):
                readiness_detail = "Source, format, and manual path cues are ready; active asset holds remain stop/go review cues."
            add_action(
                "Render ready",
                "Editor",
                f"Review render-ready story candidate: {row['title']}",
                (
                    f"Score {row.get('score')}/100. {readiness_detail} "
                    f"{row.get('next_step')}"
                ),
                row.get("artifact") or "operator_command_center.md",
            )
        elif blocked_render_rows:
            row = blocked_render_rows[0]
            add_action(
                "Render hold",
                "Editor",
                f"Clear render-readiness blocker: {row['title']}",
                f"Score {row.get('score')}/100; blockers: {row.get('blockers')}. {row.get('next_step')}",
                row.get("artifact") or "operator_command_center.md",
            )
        elif prep_render_rows:
            row = prep_render_rows[0]
            add_action(
                "Render prep",
                "Editor",
                f"Prepare render candidate: {row['title']}",
                f"Score {row.get('score')}/100. {row.get('next_step')}",
                row.get("artifact") or "operator_command_center.md",
            )

    if render_prep_packets:
        packet = render_prep_packets[0]
        add_action(
            "Render packet",
            "Editor",
            f"Open render prep packet: {packet['title']}",
            (
                f"{packet.get('packet_status')} at score {packet.get('render_readiness_score')}/100. "
                f"Template: {packet.get('selected_template_id') or packet.get('template_fit')} / {packet.get('template_shape')}. "
                "Use the packet steps for manual render prep only; publishing remains off."
            ),
            "render_prep_packets.md",
        )

    if render_handoff_summary.get("handoff_status") == "ready_for_manual_review":
        add_action(
            "Render handoff",
            "Editor",
            f"Open render handoff folder: {render_handoff_summary.get('title')}",
            (
                "Use the copy sheet, asset checklist, source proof, and manual renderer prompt as a review-only handoff. "
                "It does not render or publish anything."
            ),
            "render_handoff_top_packet/README.md",
        )

    coverage_gaps = [row for row in coverage_map if row.get("status") == "gap"]
    proposal_holds = [row for row in proposal_review if row.get("review_status") == "hold"]
    checklist_verify_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "verify_then_copy"]
    checklist_hold_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "hold"]
    checklist_discard_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "discard"]
    registry_update_rows = [row for row in source_registry_update_worksheet if row.get("worksheet_decision") == "manual_registry_plan_after_verification"]
    registry_diff_hold_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "HOLD"]
    registry_diff_review_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "REVIEW"]
    same_domain_input_rows = [
        row
        for row in source_registry_same_domain_resolution
        if row.get("same_domain_resolution_status") in {"operator_input_required", "evidence_incomplete", "held_by_operator"}
    ]
    same_domain_resolved_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "same_domain_ok_evidence_ready"]
    same_domain_revise_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "revise_before_verification"]
    same_domain_discard_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "discard_before_verification"]
    verification_input_rows = [row for row in source_registry_verification_log if row.get("verification_log_status") == "operator_input_required"]
    approval_packet_ready_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "ready_for_final_manual_review"]
    approval_packet_hold_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "hold_before_manual_registry_edit"]
    patch_preview_ready_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "ready_for_manual_copy_paste"]
    patch_preview_hold_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "hold_before_manual_patch"]
    post_edit_exact_rows = [row for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") == "validated_exact_match"]
    post_edit_issue_rows = [
        row
        for row in source_registry_post_edit_validation
        if row.get("post_edit_validation_status") in {"missing_manual_edit", "drift_review_required", "unsafe_hold"}
    ]
    ready_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status") == "ready_to_copy_after_freshness_check"]
    blocked_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status", "").startswith("blocked_")]
    duplicate_pack_reviews = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_duplicate_review"]
    freshness_pack_reviews = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_source_freshness_check"]
    ready_pack_reviews = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "ready_for_registry_proposal"]
    if proposal_holds:
        held = proposal_holds[0]
        add_action(
            "Source hold",
            "Research",
            f"Resolve unsafe source proposal: {held.get('candidate_source_id') or 'missing source id'}",
            f"{held.get('safety_flags') or 'proposal issue'}; {held.get('issues') or 'Review before registry update.'}",
            "source_registry_proposal_review.md",
        )

    if checklist_verify_rows:
        row = checklist_verify_rows[0]
        add_action(
            "Promotion checklist",
            "Research",
            "Work source proposal promotion checklist",
            (
                f"{len(checklist_verify_rows)} row(s) are verify-then-copy candidates. "
                f"Start with {row.get('candidate_source_id')}: {row.get('operator_step')}. "
                "Open the URL manually before copying anything into the proposal inbox."
            ),
            "source_registry_proposal_promotion_checklist.md",
        )

    if checklist_hold_rows or checklist_discard_rows:
        row = (checklist_hold_rows + checklist_discard_rows)[0]
        add_action(
            "Checklist hold",
            "Research",
            "Resolve held or discarded source checklist rows",
            (
                f"{len(checklist_hold_rows)} hold row(s), {len(checklist_discard_rows)} discard row(s). "
                f"First item: {row.get('candidate_source_id')} / {row.get('checklist_decision')}."
            ),
            "source_registry_proposal_promotion_checklist.md",
        )

    if registry_update_rows or approval_packet_ready_rows or patch_preview_ready_rows or post_edit_issue_rows:
        add_action(
            "Playbook",
            "Research",
            "Open trusted-registry operator playbook",
            (
                "Use the step-by-step stop/go workflow before any manual registry edit. "
                "It lists exact files to open, approval gates, and rollback steps."
            ),
            "trusted_registry_operator_playbook.md",
        )

    if registry_update_rows:
        row = registry_update_rows[0]
        add_action(
            "Registry worksheet",
            "Research",
            "Review trusted-registry update worksheet",
            (
                f"{len(registry_update_rows)} review-only registry plan row(s). "
                f"Start with {row.get('source_id')}: compare proposed JSON, verify the public URL, "
                "and hand-edit config/source_registry.json only after approval."
            ),
            "source_registry_update_worksheet.md",
        )

    if registry_diff_hold_rows or registry_diff_review_rows:
        row = (registry_diff_hold_rows + registry_diff_review_rows)[0]
        add_action(
            "Registry diff",
            "Research",
            "Resolve trusted-registry diff review",
            (
                f"{len(registry_diff_hold_rows)} hold row(s), {len(registry_diff_review_rows)} review row(s). "
                f"Start with {row.get('source_id')}: {row.get('issues') or row.get('recommendation')}. "
                "Do not hand-edit the registry until this review is clear."
            ),
            "source_registry_diff_review.md",
        )

    if same_domain_input_rows or same_domain_revise_rows or same_domain_discard_rows:
        row = (same_domain_input_rows + same_domain_revise_rows + same_domain_discard_rows)[0]
        add_action(
            "Same-domain review",
            "Research",
            "Resolve same-domain source decisions",
            (
                f"{len(same_domain_input_rows)} need decision/evidence, "
                f"{len(same_domain_revise_rows)} revise, {len(same_domain_discard_rows)} discard, "
                f"{len(same_domain_resolved_rows)} same-domain OK. "
                f"Start with {row.get('source_id')}: {row.get('evidence_requirement') or row.get('verification_log_instruction')}. "
                "Do this before filling approval fields in the verification log."
            ),
            "source_registry_same_domain_resolution.md",
        )

    if verification_input_rows:
        row = verification_input_rows[0]
        add_action(
            "Verification log",
            "Research",
            "Fill manual source verification log",
            (
                f"{len(verification_input_rows)} source row(s) need operator evidence. "
                f"Start with {row.get('source_id')}: record URL checked, freshness result, "
                "duplicate decision, and approval/hold outcome before any registry edit."
            ),
            "source_registry_verification_log.md",
        )

    if approval_packet_ready_rows or approval_packet_hold_rows:
        row = (approval_packet_hold_rows + approval_packet_ready_rows)[0]
        add_action(
            "Approval packet",
            "Research",
            "Review manual registry approval packet",
            (
                f"{len(approval_packet_ready_rows)} ready row(s), {len(approval_packet_hold_rows)} held row(s). "
                f"Start with {row.get('source_id')}: {row.get('hold_reason') or 'final JSON and evidence review required'}. "
                "This packet is review-only and does not edit the trusted registry."
            ),
            "source_registry_approval_packet.md",
        )

    if patch_preview_ready_rows or patch_preview_hold_rows:
        row = (patch_preview_hold_rows + patch_preview_ready_rows)[0]
        add_action(
            "Patch preview",
            "Research",
            "Review manual registry patch preview",
            (
                f"{len(patch_preview_ready_rows)} ready copy/paste row(s), {len(patch_preview_hold_rows)} held row(s). "
                f"Start with {row.get('source_id')}: {row.get('hold_reason') or 'compare before/after and copy manually only'}. "
                "This preview does not edit the trusted registry."
            ),
            "source_registry_patch_preview.md",
        )

    if post_edit_exact_rows or post_edit_issue_rows:
        row = (post_edit_issue_rows + post_edit_exact_rows)[0]
        add_action(
            "Post-edit check",
            "Research",
            "Review post-edit registry validation",
            (
                f"{len(post_edit_exact_rows)} exact match row(s), {len(post_edit_issue_rows)} issue row(s). "
                f"Start with {row.get('source_id')}: {row.get('post_edit_validation_status')}. "
                "Hold any drift, unsafe enablement, paid/login signal, automation, or publish-policy issue."
            ),
            "source_registry_post_edit_validation.md",
        )

    if ready_draft_rows:
        row = ready_draft_rows[0]
        add_action(
            "Proposal draft",
            "Research",
            "Review manual source proposal draft",
            (
                f"{len(ready_draft_rows)} draft row(s) are ready to copy only after manual freshness review. "
                f"Start with {row.get('candidate_source_id')}: {row.get('freshness_warning') or 'Open the page manually first.'} "
                "Do not enable sources or edit the trusted registry from this draft."
            ),
            "source_registry_proposal_draft.md",
        )

    if blocked_draft_rows and not proposal_holds:
        row = blocked_draft_rows[0]
        add_action(
            "Draft hold",
            "Research",
            "Review blocked source proposal draft rows",
            (
                f"{len(blocked_draft_rows)} draft row(s) are held by duplicate or freshness warnings. "
                f"First held row: {row.get('candidate_source_id')} / {row.get('draft_action')}."
            ),
            "source_registry_proposal_draft.md",
        )

    if duplicate_pack_reviews:
        pack = duplicate_pack_reviews[0]
        add_action(
            "Pack duplicate review",
            "Research",
            f"Resolve duplicate cues in {pack.get('pack_name') or pack.get('display_name')}",
            (
                f"{pack.get('review_cues') or 'Duplicate source cues detected.'} "
                f"Duplicates: {pack.get('duplicate_candidate_ids') or 'see readiness report'}. "
                "Do not copy duplicate candidates into proposals until the registry match is reviewed."
            ),
            "source_proposal_pack_readiness.md",
        )
    elif freshness_pack_reviews:
        pack = freshness_pack_reviews[0]
        add_action(
            "Pack freshness check",
            "Research",
            f"Freshness-check {pack.get('pack_name') or pack.get('display_name')}",
            (
                f"{pack.get('review_cues') or 'Source freshness check needed.'} "
                f"Open top candidates manually: {pack.get('top_candidate_ids') or 'see readiness report'}. "
                "Keep every row disabled and proposal-only."
            ),
            "source_proposal_pack_readiness.md",
        )
    elif ready_pack_reviews and not coverage_gaps:
        pack = ready_pack_reviews[0]
        add_action(
            "Pack proposal review",
            "Research",
            f"Review ready source pack: {pack.get('pack_name') or pack.get('display_name')}",
            (
                f"{pack.get('review_cues') or 'Pack is ready for manual proposal review.'} "
                f"Open top candidates for freshness: {pack.get('top_candidate_ids') or 'see readiness report'}. "
                "Copy only selected rows into the manual proposal inbox after review."
            ),
            "source_proposal_pack_readiness.md",
        )

    if coverage_gaps:
        gap = coverage_gaps[0]
        pack_rows = [
            row
            for row in source_proposal_packs
            if row.get("pack_key") == gap.get("key") or row.get("coverage_key") == gap.get("key")
        ]
        pack_count = len(pack_rows)
        pack_name = first_present(pack_rows[0].get("pack_name") if pack_rows else "", default=f"{gap['name']} source proposal pack")
        artifact = "source_proposal_packs.csv" if pack_count else "source_registry_intake_template.csv"
        pack_note = (
            f"Use the guided {pack_name} with {pack_count} free official/team/cross-check candidates; "
            if pack_count
            else "Use the intake template; "
        )
        add_action(
            "Source gap",
            "Research",
            f"Propose free source coverage for {gap['name']}",
            (
                f"{gap.get('gap') or 'coverage gap'}; "
                f"{gap.get('next_step') or 'Add a free official, team, wire, or reputable cross-check source manually.'} "
                f"{pack_note}proposals stay disabled until the registry is deliberately reviewed."
            ),
            artifact,
        )

    source_leads = [
        row
        for row in source_board
        if row.get("status") in {"editor_review", "needs_green_confirmation", "verify_with_primary"}
        and row.get("artifact") != "config/source_registry.json"
    ]
    if source_leads:
        lead = source_leads[0]
        add_action(
            "Source review",
            "Research",
            f"Review morning source lead: {lead['title']}",
            (
                f"{lead['lane']} / {lead['posture']}. "
                f"{lead.get('story_opportunity_reason') + ' ' if lead.get('story_opportunity_reason') else ''}"
                f"{'Angle: ' + lead.get('story_opportunity_angle') + '. ' if lead.get('story_opportunity_angle') else ''}"
                f"{'Readiness: ' + lead.get('story_opportunity_confidence_tier') + ' / ' + lead.get('story_opportunity_source_coverage') + ' / ' + lead.get('story_opportunity_confirmation_cue') + '. ' if lead.get('story_opportunity_confidence_tier') else ''}"
                f"{'Suggested second source: ' + lead.get('story_opportunity_second_source_id') + '. ' if lead.get('story_opportunity_second_source_id') else ''}"
                f"{lead.get('detail') or ''} {lead.get('next_action') or ''}"
            ).strip(),
            lead["artifact"],
        )
    elif source_board:
        lead = source_board[0]
        add_action(
            "Research scan",
            "Research",
            "Scan the morning source board",
            f"Start with {lead['source']}: {lead.get('detail') or lead.get('next_action')}",
            "morning_source_discovery_board.md",
        )

    if (candidates or studio) and (
        not artifact_exists.get("results_dashboard/index.html") or not artifact_exists.get("studio_dashboard/index.html")
    ):
        add_action(
            "Optional drill-down",
            "Operator",
            "Create Results and Studio drill-down dashboards",
            "Use this when you want the close-up Results/Studio pages behind the daily command center.",
            "results_desk_v5_report.md",
            RUN_COMMANDS["results_dashboard/index.html"],
        )

    if ready_candidates and not artifact_exists.get("multi_post_daily_board.md"):
        add_action(
            "Plan slots",
            "Operator",
            "Build the multi-post board after content is chosen",
            "Turns reviewed candidates and handoff/story artifacts into IG Feed, IG Stories, and Threads queues.",
            "news_fact_packets.csv",
            RUN_COMMANDS["multi_post_daily_board.md"],
        )

    handled_issue_codes = {"no_content_ready"} if studio or ready_candidates else set()
    for issue in critical:
        code = clean(issue.get("code"))
        if code in handled_issue_codes:
            continue
        detail = first_present(issue.get("detail"), issue.get("headline"), default="Open the operator status report and resolve the blocker.")
        title = "Create or refresh content inputs" if code == "no_content_ready" else first_present(code, default="Resolve blocking issue")
        command = ".\\hsd.cmd run -Mode full" if code == "no_content_ready" else ""
        add_action("Blocked", "Operator", title, detail, "operator_status.md", command)

    rendered_status = clean(guard.get("rendered_qa_status")).lower()
    if rendered_status in {"", "not_run"}:
        if artifact_exists.get("graphics_upload_pack_status.csv"):
            add_action(
                "QA pending",
                "Operator",
                "Run rendered-slide QA before posting",
                "Rendered graphics need source, crop, and copy checks before any manual post.",
                "rendered_slide_qa_report.md",
                artifact_commands.get("rendered_slide_qa_report.md"),
            )
        else:
            add_action(
                "Waiting",
                "Operator",
                "Run rendered-slide QA after graphics exist",
                "This is not runnable yet; first build or review the graphics pack.",
                "rendered_slide_qa_report.md",
            )

    if not yes(guard.get("publish_allowed")):
        add_action(
            "Manual only",
            "Publisher",
            "Keep publishing off",
            "Use artifacts for review and manual posting only. No auto-publishing path is enabled.",
            "publish_guard_report.md",
        )

    return trim_actions(actions)


def metric(label: str, value: Any, detail: str = "") -> Dict[str, str]:
    text = clean(value)
    return {"label": label, "value": text, "detail": clean(detail), "tone": status_tone(text)}


def source_registry_status(counts: Dict[str, Any]) -> str:
    total = as_int(counts.get("sources"))
    if not total:
        return "not_run"
    fail = as_int(counts.get("fail"))
    review = as_int(counts.get("review"))
    if fail:
        return "FAIL"
    if review:
        return "REVIEW"
    return "PASS"


def release_readiness_evidence_panel() -> Dict[str, Any]:
    manifest = read_json("release_readiness_guardrail_rollup.json")
    if not manifest:
        return {
            "status": "not_created",
            "blocker_count": 0,
            "latest_scan_status": "not_run",
            "latest_scan_files_checked": 0,
            "latest_scan_violations": 0,
            "conductor_status": "not_run",
            "conductor_collision_blockers": 0,
            "missing_inputs": ["release_readiness_guardrail_rollup"],
            "checks": [],
            "next_step": "Run the local review stage to create release_readiness_guardrail_rollup.md before release review.",
        }
    latest = manifest.get("latest_artifact_scan", {}) if isinstance(manifest.get("latest_artifact_scan"), dict) else {}
    conductor = manifest.get("conductor_workspace_audit", {}) if isinstance(manifest.get("conductor_workspace_audit"), dict) else {}
    workflow = manifest.get("workflow_lane_status", {}) if isinstance(manifest.get("workflow_lane_status"), dict) else {}
    checks = manifest.get("checks", []) if isinstance(manifest.get("checks"), list) else []
    blocker_count = as_int(manifest.get("blocker_count"))
    missing_inputs = manifest.get("missing_inputs", []) if isinstance(manifest.get("missing_inputs"), list) else []
    if blocker_count:
        next_step = "Stop release review and fix the blocked evidence row before continuing."
    elif missing_inputs:
        next_step = "Generate the missing evidence inputs, then rerun the release-readiness rollup."
    else:
        next_step = "Use the rollup as review evidence with the conductor audit and deterministic guardrail check."
    return {
        "status": clean(manifest.get("status")) or "unknown",
        "blocker_count": blocker_count,
        "latest_scan_status": clean(latest.get("status")) or "not_run",
        "latest_scan_files_checked": as_int(latest.get("scan_files_checked")),
        "latest_scan_violations": as_int(latest.get("violation_count")),
        "conductor_status": clean(conductor.get("status")) or "not_run",
        "conductor_collision_blockers": as_int(conductor.get("collision_blocker_count")),
        "workflow_status": clean(workflow.get("status")) or "not_run",
        "workflow_stale_lanes": as_int(workflow.get("stale_lane_count")),
        "workflow_restart_needed": as_int(workflow.get("restart_needed_lane_count")),
        "workflow_lifecycle_actions": as_int(workflow.get("lifecycle_action_lane_count")),
        "missing_inputs": missing_inputs,
        "checks": checks,
        "next_step": next_step,
    }


def source_registry_detail(counts: Dict[str, Any]) -> str:
    total = as_int(counts.get("sources"))
    if not total:
        return "No source registry audit found."
    return (
        f"{as_int(counts.get('pass'))} pass, "
        f"{as_int(counts.get('review'))} review, "
        f"{as_int(counts.get('fail'))} fail across {total} sources."
    )


def summarize_source_ids(rows: Iterable[Dict[str, str]], key: str = "source_id", limit: int = 4) -> str:
    values = [clean(row.get(key)) for row in rows if clean(row.get(key))]
    if not values:
        return "none"
    shown = values[:limit]
    suffix = f" +{len(values) - limit} more" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def build_source_registry_readiness_summary(
    coverage_map: List[Dict[str, str]],
    source_proposal_draft: List[Dict[str, str]],
    source_proposal_promotion_checklist: List[Dict[str, str]],
    source_registry_update_worksheet: List[Dict[str, str]],
    source_registry_diff_review: List[Dict[str, str]],
    source_registry_same_domain_resolution: List[Dict[str, str]],
    source_registry_verification_log: List[Dict[str, str]],
    source_registry_approval_packet: List[Dict[str, str]],
    source_registry_patch_preview: List[Dict[str, str]],
    source_registry_post_edit_validation: List[Dict[str, str]],
    source_proposal_pack_readiness: List[Dict[str, str]],
) -> Dict[str, str]:
    coverage_gaps = [row for row in coverage_map if row.get("status") == "gap"]
    ready_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status") == "ready_to_copy_after_freshness_check"]
    blocked_draft_rows = [row for row in source_proposal_draft if row.get("draft_selection_status", "").startswith("blocked_")]
    checklist_verify_rows = [row for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "verify_then_copy"]
    checklist_hold_rows = [
        row
        for row in source_proposal_promotion_checklist
        if row.get("checklist_decision") in {"hold", "discard"}
    ]
    worksheet_rows = [row for row in source_registry_update_worksheet if row.get("worksheet_decision") == "manual_registry_plan_after_verification"]
    diff_hold_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "HOLD"]
    diff_review_rows = [row for row in source_registry_diff_review if row.get("diff_review_status") == "REVIEW"]
    same_domain_input_rows = [
        row
        for row in source_registry_same_domain_resolution
        if row.get("same_domain_resolution_status") in {"operator_input_required", "evidence_incomplete", "held_by_operator"}
    ]
    same_domain_revise_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "revise_before_verification"]
    same_domain_discard_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "discard_before_verification"]
    same_domain_ok_rows = [row for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "same_domain_ok_evidence_ready"]
    verification_rows = [row for row in source_registry_verification_log if row.get("verification_log_status") == "operator_input_required"]
    approval_ready_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "ready_for_final_manual_review"]
    approval_hold_rows = [row for row in source_registry_approval_packet if row.get("approval_packet_status") == "hold_before_manual_registry_edit"]
    patch_ready_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "ready_for_manual_copy_paste"]
    patch_hold_rows = [row for row in source_registry_patch_preview if row.get("patch_preview_status") == "hold_before_manual_patch"]
    post_edit_exact_rows = [row for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") == "validated_exact_match"]
    post_edit_issue_rows = [
        row
        for row in source_registry_post_edit_validation
        if row.get("post_edit_validation_status") in {"missing_manual_edit", "drift_review_required", "unsafe_hold"}
    ]
    duplicate_pack_rows = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_duplicate_review"]
    freshness_pack_rows = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_source_freshness_check"]
    ready_pack_rows = [row for row in source_proposal_pack_readiness if row.get("readiness_status") == "ready_for_registry_proposal"]

    summary = {
        "readiness_status": "ready_to_start",
        "next_safest_action": "Open the trusted-registry operator playbook and start at the first incomplete stop/go gate.",
        "blockers": "none",
        "open_first_file": "trusted_registry_operator_playbook.md",
        "support_file": "trusted_registry_operator_playbook.md",
        "focus_source_ids": "none",
        "rollup": "No active manual registry change rows found.",
        "guardrail": "Manual review only; keep proposed sources disabled; no paid APIs, auto-runs, auto-enabling, or publishing.",
    }

    def set_summary(
        status: str,
        action: str,
        blockers: str,
        open_first_file: str,
        rows: List[Dict[str, str]],
        rollup: str,
        focus_key: str = "source_id",
    ) -> Dict[str, str]:
        summary.update(
            {
                "readiness_status": status,
                "next_safest_action": action,
                "blockers": blockers or "none",
                "open_first_file": open_first_file,
                "focus_source_ids": summarize_source_ids(rows, key=focus_key),
                "rollup": rollup,
            }
        )
        return summary

    if post_edit_issue_rows:
        blocker_bits = [
            f"{clean(row.get('source_id'))}: {clean(row.get('post_edit_validation_status'))}"
            f"{' (' + clean(row.get('unsafe_flags')) + ')' if clean(row.get('unsafe_flags')) else ''}"
            for row in post_edit_issue_rows[:4]
        ]
        return set_summary(
            "blocked_post_edit_validation",
            "Open source_registry_post_edit_validation.md first and hold unsafe or drifted rows before trusting any registry edit.",
            "; ".join(blocker_bits),
            "source_registry_post_edit_validation.md",
            post_edit_issue_rows,
            f"{len(post_edit_issue_rows)} post-edit issue row(s), {len(post_edit_exact_rows)} exact match row(s).",
        )
    if patch_hold_rows:
        return set_summary(
            "blocked_patch_preview",
            "Open source_registry_patch_preview.md and resolve held patch rows before any manual copy/paste registry edit.",
            f"{len(patch_hold_rows)} held patch preview row(s): {summarize_source_ids(patch_hold_rows)}",
            "source_registry_patch_preview.md",
            patch_hold_rows,
            f"{len(patch_ready_rows)} ready patch row(s), {len(patch_hold_rows)} held row(s).",
        )
    if approval_hold_rows:
        return set_summary(
            "blocked_approval_packet",
            "Open source_registry_approval_packet.md and clear held approval rows before preparing a registry patch.",
            f"{len(approval_hold_rows)} held approval row(s): {summarize_source_ids(approval_hold_rows)}",
            "source_registry_approval_packet.md",
            approval_hold_rows,
            f"{len(approval_ready_rows)} ready approval row(s), {len(approval_hold_rows)} held row(s).",
        )
    if diff_hold_rows or diff_review_rows:
        rows = diff_hold_rows + diff_review_rows
        resolution_counts = {
            action: sum(1 for row in rows if clean(row.get("resolution_action")) == action)
            for action in ["VERIFY", "REVISE", "HOLD", "DISCARD"]
        }
        resolution_rollup = ", ".join(
            f"{action.lower()} {count}"
            for action, count in resolution_counts.items()
            if count
        ) or "resolution cues not available"
        return set_summary(
            "blocked_diff_review",
            "Open source_registry_same_domain_resolution.md for HOLD rows, then follow VERIFY, REVISE, HOLD, or DISCARD cues before filling the verification log.",
            f"{len(diff_hold_rows)} hold row(s), {len(diff_review_rows)} review row(s): {summarize_source_ids(rows)}",
            "source_registry_same_domain_resolution.md" if same_domain_input_rows or same_domain_revise_rows or same_domain_discard_rows else "source_registry_diff_review.md",
            rows,
            f"{len(diff_hold_rows)} hold row(s), {len(diff_review_rows)} review row(s) before verification can be trusted; {resolution_rollup}; same-domain ok {len(same_domain_ok_rows)}, needs decision {len(same_domain_input_rows)}, revise {len(same_domain_revise_rows)}, discard {len(same_domain_discard_rows)}.",
        )
    if verification_rows:
        return set_summary(
            "needs_operator_evidence",
            "Open source_registry_verification_log.csv and record URL checked, freshness, duplicate decision, and approval/hold outcome.",
            f"{len(verification_rows)} row(s) still need operator evidence: {summarize_source_ids(verification_rows)}",
            "source_registry_verification_log.csv",
            verification_rows,
            f"{len(verification_rows)} manual verification row(s) need human evidence before approval.",
        )
    if patch_ready_rows:
        return set_summary(
            "ready_for_manual_patch_preview",
            "Open source_registry_patch_preview.md, compare the side-by-side preview, then copy/paste manually only if the playbook stop/go checks pass.",
            "none",
            "source_registry_patch_preview.md",
            patch_ready_rows,
            f"{len(patch_ready_rows)} patch preview row(s) ready for final manual copy/paste review.",
        )
    if approval_ready_rows:
        return set_summary(
            "ready_for_final_approval_review",
            "Open source_registry_approval_packet.md and review the exact disabled JSON plus evidence before creating a patch preview.",
            "none",
            "source_registry_approval_packet.md",
            approval_ready_rows,
            f"{len(approval_ready_rows)} approved row(s) ready for final manual review.",
        )
    if worksheet_rows:
        return set_summary(
            "worksheet_review_needed",
            "Open source_registry_update_worksheet.md and review disabled proposed source objects, before/after notes, and rollback coverage.",
            "none",
            "source_registry_update_worksheet.md",
            worksheet_rows,
            f"{len(worksheet_rows)} review-only registry worksheet row(s) are waiting.",
        )
    if checklist_verify_rows:
        return set_summary(
            "proposal_checklist_ready",
            "Open source_registry_proposal_promotion_checklist.md and verify ready rows manually before copying selected rows to the proposal inbox.",
            f"{len(checklist_hold_rows)} held/discarded checklist row(s)" if checklist_hold_rows else "none",
            "source_registry_proposal_promotion_checklist.md",
            checklist_verify_rows,
            f"{len(checklist_verify_rows)} verify-then-copy row(s), {len(checklist_hold_rows)} held/discarded row(s).",
        )
    if ready_draft_rows:
        return set_summary(
            "proposal_draft_ready",
            "Open source_registry_proposal_draft.md and freshness-check ready draft rows before using the promotion checklist.",
            f"{len(blocked_draft_rows)} blocked draft row(s)" if blocked_draft_rows else "none",
            "source_registry_proposal_draft.md",
            ready_draft_rows,
            f"{len(ready_draft_rows)} draft row(s) ready after freshness check, {len(blocked_draft_rows)} blocked row(s).",
        )
    if duplicate_pack_rows:
        return set_summary(
            "pack_duplicate_review_needed",
            "Open source_proposal_pack_readiness.md and resolve duplicate cues before promoting any pack rows.",
            f"{len(duplicate_pack_rows)} pack(s) need duplicate review.",
            "source_proposal_pack_readiness.md",
            duplicate_pack_rows,
            f"{len(ready_pack_rows)} ready pack(s), {len(duplicate_pack_rows)} duplicate-review pack(s), {len(freshness_pack_rows)} freshness-check pack(s).",
            focus_key="pack_key",
        )
    if freshness_pack_rows:
        return set_summary(
            "pack_freshness_check_needed",
            "Open source_proposal_pack_readiness.md and manually freshness-check top candidates before proposal drafting.",
            f"{len(freshness_pack_rows)} pack(s) need source freshness checks.",
            "source_proposal_pack_readiness.md",
            freshness_pack_rows,
            f"{len(ready_pack_rows)} ready pack(s), {len(freshness_pack_rows)} freshness-check pack(s).",
            focus_key="pack_key",
        )
    if coverage_gaps:
        return set_summary(
            "coverage_gap_intake_needed",
            "Open source_coverage_map.csv to choose the next free official, team, wire, or cross-check source gap for proposal intake.",
            f"{len(coverage_gaps)} coverage gap(s): {summarize_source_ids(coverage_gaps, key='key')}",
            "source_coverage_map.csv",
            coverage_gaps,
            f"{len(coverage_gaps)} source coverage gap(s) still need proposal intake.",
            focus_key="key",
        )
    return summary


def decision_callout(
    overall: str,
    guard: Dict[str, Any],
    candidates: List[Dict[str, str]],
    studio: List[Dict[str, str]],
    artifacts: List[Dict[str, Any]],
    source_registry_counts: Dict[str, Any],
) -> str:
    artifact_exists = {row["path"]: bool(row["exists"]) for row in artifacts}
    source_status = source_registry_status(source_registry_counts)
    if as_int(source_registry_counts.get("fail")):
        return "Hold: source registry has failing sources. Review source health before choosing a post."
    if not artifact_exists.get("graphics_upload_pack_status.csv") and studio:
        return f"{overall}: source registry is {source_status}, but no graphics upload pack is ready. Build the top Studio pack before handoff or posting."
    if candidates and not yes(guard.get("publish_allowed")):
        return f"{overall}: content candidates exist, but publishing remains artifact-only and manual review is still required."
    if yes(guard.get("graphics_handoff_allowed")):
        return "Graphics handoff is allowed for review, but publishing stays manual until rendered QA and operator approval."
    return "Manual review required before any post leaves the system."


def trim_actions(actions: List[Dict[str, str]], limit: int = 24) -> List[Dict[str, str]]:
    trimmed = list(actions)
    for status in ["Waiting", "Plan slots", "Optional drill-down"]:
        if len(trimmed) <= limit:
            break
        for index, action in enumerate(trimmed):
            if action.get("status") == status:
                del trimmed[index]
                break
    if len(trimmed) > limit:
        manual = [action for action in trimmed if action.get("status") == "Manual only"]
        trimmed = trimmed[:limit]
        if manual and all(action.get("status") != "Manual only" for action in trimmed):
            trimmed[-1] = manual[0]
    for index, action in enumerate(trimmed, 1):
        action["rank"] = str(index)
    return trimmed


def next_action_synthesis_row(
    rank: int,
    lane: str,
    manual_step: str,
    primary_artifact: str,
    companion_artifact: str,
    operator_return_fields: str,
    guardrail_note: str,
    lane_detail: str = "",
) -> Dict[str, str]:
    primary_path = find_existing_input(primary_artifact)
    companion_path = find_existing_input(companion_artifact)
    return {
        "rank": str(rank),
        "lane": lane,
        "manual_step": manual_step,
        "primary_artifact": primary_artifact,
        "primary_resolved_path": primary_path.as_posix() if primary_path.exists() else "",
        "companion_artifact": companion_artifact,
        "companion_resolved_path": companion_path.as_posix() if companion_path.exists() else "",
        "operator_return_fields": operator_return_fields,
        "lane_detail": lane_detail,
        "guardrail_note": guardrail_note,
        "artifact_status": "ready_to_open" if primary_path.exists() else "missing_or_not_generated",
        "run_command": RUN_COMMANDS.get(primary_artifact, ""),
    }


def game_source_confirmation_return_lane_detail() -> str:
    payload = read_json("game_source_confirmation_return_summary_v1.json")
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if not isinstance(summary, dict) or not summary:
        return "Return summary not generated yet; run Results to create missing official URL/status counts."
    return (
        f"rows={summary.get('rows', 0)}; "
        f"missing_official_url={summary.get('missing_official_url', 0)}; "
        f"missing_confirmation_status={summary.get('missing_confirmation_status', 0)}; "
        f"ready_for_operator_review={summary.get('operator_return_ready_for_review', 0)}"
    )


def build_operator_next_action_synthesis() -> List[Dict[str, str]]:
    guardrail = "Review-only and artifact-only; no source fetching, downloads, source enablement, approvals, publish-ready movement, or publishing."
    return [
        next_action_synthesis_row(
            1,
            "Render review",
            "Open the top render handoff, inspect drafts/source proof/copy fit, then record a manual approve/hold/revise decision only in the operator decision intake.",
            "render_handoff_top_packet/README.md",
            "render_handoff_top_packet/manual_renderer_prompt.md",
            "operator_decision, operator_notes, operator_name, reviewed_at_local",
            guardrail,
        ),
        next_action_synthesis_row(
            2,
            "Action-photo research handoff",
            "Open the local handoff draft and latest bundle manifest, then manually paste the packet into the chosen external research surface if Mike wants a research run.",
            "action_photo_external_research_handoff_draft_copy.md",
            "action_photo_external_research_bundle_latest.json",
            "researcher_notes, source_url, entity_id, rights_class, identity_confidence, intended_review_only_use",
            guardrail,
        ),
        next_action_synthesis_row(
            3,
            "Game-source confirmation returns",
            "Fill the game source research worksheet from manual official/public checks before any result/story proof is trusted downstream.",
            "game_source_confirmation_return_summary_v1.csv",
            "game_source_research_worksheet_v1.csv",
            "operator_found_official_url, operator_confirmation_status, operator_notes, checked_at_local",
            guardrail,
            game_source_confirmation_return_lane_detail(),
        ),
        next_action_synthesis_row(
            4,
            "Breaking/public-signal returns",
            "Use the breaking/public-signal next-action board to choose rows, then paste manual confirmation details into the confirmation intake.",
            "breaking_public_signal_next_action_v1.md",
            "breaking_public_signal_confirmation_intake.csv",
            "operator_checked_url, operator_confirmation_result, operator_confidence, operator_notes",
            guardrail,
        ),
        next_action_synthesis_row(
            5,
            "Women's soccer action-photo helpers",
            "Open the women's soccer starter intake/focus boards and fill only human-researched source or identity notes for future review-only candidates.",
            "data/asset_registry/action_photo_candidates/review_only_womens_soccer_action_photo_starter_intake.md",
            "data/asset_registry/womens_soccer/womens_soccer_athlete_operator_focus.md",
            "source_url, entity_id, rights_class, identity_confidence, intended_review_only_use, reviewer_notes",
            guardrail,
        ),
        next_action_synthesis_row(
            6,
            "Hockey/softball source returns",
            "Open the H/S source return intake after manual PWHL/AUSL source review and paste only source leads or verification notes.",
            "data/asset_registry/hockey_softball_source_research_return_intake.csv",
            "data/asset_registry/hockey_softball_source_map_board.md",
            "source_url, entity_id, rights_class, identity_confidence, intended_review_only_use, download_approved",
            guardrail,
        ),
    ]


def build_payload() -> Dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    operator = read_json("operator_status.json")
    guard = read_json("publish_guard_report.json")
    manifest = read_json("results_desk_v5_manifest.json")
    source_registry = read_json("source_registry_audit.json")
    ops = read_json("bebe_daily_ops_status.json")
    handoff = read_json("assignment_handoff_publisher_manifest.json")
    render = read_json("rendered_slide_qa_manifest.json")
    artifacts = artifact_entries()
    candidates = content_candidates()
    news_packets = read_csv("news_fact_packets.csv")
    breaking_clusters = read_csv("breaking_public_signal_clusters.csv")
    source_board = source_discovery_board()
    promotions = lead_promotion_recommendations()
    studio = studio_queue()
    schedule = schedule_rows()
    render_queue = render_readiness_queue(candidates, promotions, source_board)
    render_prep_packets = build_render_prep_packets(
        {
            "content_candidates": candidates,
            "lead_promotion_recommendations": promotions,
            "source_discovery_board": source_board,
            "render_readiness_queue": render_queue,
            "news_fact_packets": news_packets,
            "breaking_public_signal_clusters": breaking_clusters,
        }
    )
    attach_render_prep_active_cues(render_queue, render_prep_packets)
    render_handoff_summary = build_render_handoff_summary(render_prep_packets)
    top_render_packet = render_prep_packets[0] if render_prep_packets else None
    active_asset_rows = active_asset_review_queue_rows(top_render_packet) if top_render_packet else []
    manual_asset_source_board = manual_asset_source_board_rows(active_asset_rows)
    manual_logo_verification_intake = manual_logo_verification_intake_rows(manual_asset_source_board)
    manual_league_mark_context_intake = manual_league_mark_context_intake_rows(manual_asset_source_board)
    stop_go_summary = decision_stop_go_summary(top_render_packet, active_asset_rows, manual_asset_source_board)
    review_order_checklist = decision_review_order_checklist(stop_go_summary)
    operator_decision_panel = operator_decision_ui_panel()
    asset_readiness_panel = asset_availability_readiness_panel()
    release_readiness_panel = release_readiness_evidence_panel()
    athlete_photo_panel = athlete_photo_onboarding_panel(read_json("manual_review_renderer_manifest.json"))
    coverage_map = source_coverage_map(source_registry)
    source_intake_rows = read_csv("source_registry_intake_template.csv")
    source_proposal_review = read_csv("source_registry_proposal_review.csv")
    source_proposal_draft = read_csv("source_registry_proposal_draft.csv")
    source_proposal_promotion_checklist = read_csv("source_registry_proposal_promotion_checklist.csv")
    source_registry_update_worksheet = read_csv("source_registry_update_worksheet.csv")
    source_registry_diff_review = read_csv("source_registry_diff_review.csv")
    source_registry_same_domain_resolution = read_csv("source_registry_same_domain_resolution.csv")
    source_registry_verification_log = read_csv("source_registry_verification_log.csv")
    source_registry_approval_packet = read_csv("source_registry_approval_packet.csv")
    source_registry_patch_preview = read_csv("source_registry_patch_preview.csv")
    source_registry_post_edit_validation = read_csv("source_registry_post_edit_validation.csv")
    source_proposal_pack_readiness = read_csv("source_proposal_pack_readiness.csv")
    source_proposal_packs = read_csv("source_proposal_packs.csv")
    wnba_source_proposal_pack = read_csv("wnba_source_proposal_pack.csv")
    nwsl_source_proposal_pack = read_csv("nwsl_source_proposal_pack.csv")
    lpga_source_proposal_pack = read_csv("lpga_source_proposal_pack.csv")
    pwhl_source_proposal_pack = read_csv("pwhl_source_proposal_pack.csv")
    if not source_proposal_packs:
        source_proposal_packs = (
            wnba_source_proposal_pack
            + nwsl_source_proposal_pack
            + lpga_source_proposal_pack
            + pwhl_source_proposal_pack
        )
    counts = manifest.get("counts", {}) if isinstance(manifest.get("counts"), dict) else {}
    source_registry_counts = source_registry.get("counts", {}) if isinstance(source_registry.get("counts"), dict) else {}
    handoff_counts = handoff.get("counts", {}) if isinstance(handoff.get("counts"), dict) else {}
    render_counts = render.get("counts", {}) if isinstance(render.get("counts"), dict) else {}
    source_registry_readiness_summary = build_source_registry_readiness_summary(
        coverage_map,
        source_proposal_draft,
        source_proposal_promotion_checklist,
        source_registry_update_worksheet,
        source_registry_diff_review,
        source_registry_same_domain_resolution,
        source_registry_verification_log,
        source_registry_approval_packet,
        source_registry_patch_preview,
        source_registry_post_edit_validation,
        source_proposal_pack_readiness,
    )

    decision = {
        "overall": first_present(operator.get("overall"), default="NO-GO"),
        "publish_allowed": bool(guard.get("publish_allowed")),
        "graphics_handoff_allowed": bool(guard.get("graphics_handoff_allowed")),
        "publish_mode": first_present(guard.get("publish_mode"), default="artifact_only"),
        "automation": "OFF / artifact-only",
        "free_source_mode": "Free public sources only",
    }
    decision["callout"] = decision_callout(decision["overall"], guard, candidates, studio, artifacts, source_registry_counts)
    story_opportunity_ids = {row.get("story_opportunity_id") for row in source_board if row.get("story_opportunity_id")}
    grouped_story_opportunities = {
        row.get("story_opportunity_id")
        for row in source_board
        if row.get("story_opportunity_id") and as_int(row.get("story_opportunity_size")) > 1
    }
    opportunity_representatives = {
        row.get("story_opportunity_id"): row
        for row in source_board
        if row.get("story_opportunity_id") and row.get("story_opportunity_id") not in {""}
    }
    metrics = [
        metric("Current call", decision["overall"]),
        metric("Publish allowed", display_bool(decision["publish_allowed"])),
        metric("Graphics handoff", display_bool(decision["graphics_handoff_allowed"])),
        metric("Preview gate", first_present(guard.get("preview_gate_status"), default="not_run")),
        metric("Graphics pack", "ready" if input_path("graphics_upload_pack_status.csv").exists() else "not_created"),
        metric("Rendered QA", first_present(guard.get("rendered_qa_status"), render_counts.get("decision"), default="not_run")),
        metric("Women's events", counts.get("women_events", "0")),
        metric("Graphics-ready results", counts.get("graphics_ready", "0")),
        metric("News packets", len(news_packets)),
        metric("Publish-grade packets", sum(1 for row in news_packets if packet_source_confidence(row)["source_grade"] == "publish_grade")),
        metric("Discovery-only packets", sum(1 for row in news_packets if packet_source_confidence(row)["source_grade"] == "discovery_only")),
        metric("Morning source rows", len(source_board)),
        metric("Story opportunities", len(story_opportunity_ids)),
        metric("Grouped opportunities", len(grouped_story_opportunities)),
        metric(
            "Publish-grade opportunities",
            sum(1 for row in opportunity_representatives.values() if row.get("story_opportunity_confidence_tier") == "publish_grade_candidate"),
        ),
        metric(
            "Needs source check",
            sum(
                1
                for row in opportunity_representatives.values()
                if row.get("story_opportunity_confirmation_cue") in {"needs_second_source", "needs_official_confirmation"}
            ),
        ),
        metric(
            "Second-source suggestions",
            sum(1 for row in opportunity_representatives.values() if row.get("story_opportunity_second_source_id")),
        ),
        metric("Source coverage gaps", sum(1 for row in coverage_map if row.get("status") == "gap")),
        metric("Source coverage watch", sum(1 for row in coverage_map if row.get("status") == "watch")),
        metric("Source intake proposals", len(source_intake_rows)),
        metric("Source proposal holds", sum(1 for row in source_proposal_review if row.get("review_status") == "hold")),
        metric("Source proposals ready", sum(1 for row in source_proposal_review if row.get("review_status") == "ready_for_registry_review")),
        metric("Proposal draft rows", len(source_proposal_draft)),
        metric("Proposal draft ready", sum(1 for row in source_proposal_draft if row.get("draft_selection_status") == "ready_to_copy_after_freshness_check")),
        metric("Proposal draft blocked", sum(1 for row in source_proposal_draft if row.get("draft_selection_status", "").startswith("blocked_"))),
        metric("Checklist verify/copy", sum(1 for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "verify_then_copy")),
        metric("Checklist hold", sum(1 for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "hold")),
        metric("Checklist discard", sum(1 for row in source_proposal_promotion_checklist if row.get("checklist_decision") == "discard")),
        metric("Registry worksheet rows", len(source_registry_update_worksheet)),
        metric("Worksheet disabled plans", sum(1 for row in source_registry_update_worksheet if row.get("proposed_enabled") == "False")),
        metric("Registry diff hold", sum(1 for row in source_registry_diff_review if row.get("diff_review_status") == "HOLD")),
        metric("Registry diff review", sum(1 for row in source_registry_diff_review if row.get("diff_review_status") == "REVIEW")),
        metric("Registry diff pass", sum(1 for row in source_registry_diff_review if row.get("diff_review_status") == "PASS")),
        metric("Diff cues verify", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "VERIFY")),
        metric("Diff cues revise", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "REVISE")),
        metric("Diff cues hold", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "HOLD")),
        metric("Diff cues discard", sum(1 for row in source_registry_diff_review if row.get("resolution_action") == "DISCARD")),
        metric("Same-domain rows", len(source_registry_same_domain_resolution)),
        metric("Same-domain needs decision", sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") in {"operator_input_required", "evidence_incomplete", "held_by_operator"})),
        metric("Same-domain OK", sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "same_domain_ok_evidence_ready")),
        metric("Same-domain revise/discard", "/".join([
            str(sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "revise_before_verification")),
            str(sum(1 for row in source_registry_same_domain_resolution if row.get("same_domain_resolution_status") == "discard_before_verification")),
        ])),
        metric("Verification log rows", len(source_registry_verification_log)),
        metric("Verification input needed", sum(1 for row in source_registry_verification_log if row.get("verification_log_status") == "operator_input_required")),
        metric("Approval packet rows", len(source_registry_approval_packet)),
        metric("Approval packet ready", sum(1 for row in source_registry_approval_packet if row.get("approval_packet_status") == "ready_for_final_manual_review")),
        metric("Approval packet held", sum(1 for row in source_registry_approval_packet if row.get("approval_packet_status") == "hold_before_manual_registry_edit")),
        metric("Patch preview rows", len(source_registry_patch_preview)),
        metric("Patch preview ready", sum(1 for row in source_registry_patch_preview if row.get("patch_preview_status") == "ready_for_manual_copy_paste")),
        metric("Patch preview held", sum(1 for row in source_registry_patch_preview if row.get("patch_preview_status") == "hold_before_manual_patch")),
        metric("Post-edit validations", len(source_registry_post_edit_validation)),
        metric("Post-edit exact", sum(1 for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") == "validated_exact_match")),
        metric("Post-edit issues", sum(1 for row in source_registry_post_edit_validation if row.get("post_edit_validation_status") in {"missing_manual_edit", "drift_review_required", "unsafe_hold"})),
        metric("Registry readiness", source_registry_readiness_summary["readiness_status"], source_registry_readiness_summary["blockers"]),
        metric("Source packs ready", sum(1 for row in source_proposal_pack_readiness if row.get("readiness_status") == "ready_for_registry_proposal")),
        metric("Source packs duplicate review", sum(1 for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_duplicate_review")),
        metric("Source packs freshness check", sum(1 for row in source_proposal_pack_readiness if row.get("readiness_status") == "needs_source_freshness_check")),
        metric("Guided source pack rows", len(source_proposal_packs)),
        metric("WNBA proposal pack", len(wnba_source_proposal_pack)),
        metric("NWSL proposal pack", len(nwsl_source_proposal_pack)),
        metric("LPGA proposal pack", len(lpga_source_proposal_pack)),
        metric("PWHL proposal pack", len(pwhl_source_proposal_pack)),
        metric(
            "Studio asset checks",
            sum(1 for row in opportunity_representatives.values() if row.get("story_opportunity_asset_cue") == "asset_check_required_before_studio"),
        ),
        metric("Gray/social leads", sum(1 for row in source_board if row.get("lane") in {"gray_area_review", "social_discovery"})),
        metric("Lead promotions", len(promotions)),
        metric("High-quality leads", sum(1 for row in promotions if as_int(row.get("quality_score")) >= 70)),
        metric("Fresh leads", sum(1 for row in promotions if row.get("freshness_label") in {"today", "last_48_hours"})),
        metric("News/Manual/Studio", "/".join([
            str(sum(1 for row in promotions if row.get("recommendation") == "news_packet")),
            str(sum(1 for row in promotions if row.get("recommendation") == "manual_story_candidate")),
            str(sum(1 for row in promotions if row.get("recommendation") == "studio_brief")),
        ])),
        metric("Render readiness rows", len(render_queue)),
        metric("Render-ready review", sum(1 for row in render_queue if row.get("band") == "render_ready_review")),
        metric("Render prep candidates", sum(1 for row in render_queue if row.get("band") == "render_prep_candidate")),
        metric("Render holds", sum(1 for row in render_queue if row.get("band", "").startswith("hold_"))),
        metric("Render needs source", sum(1 for row in render_queue if "source" in row.get("blockers", ""))),
        metric("Render needs asset", sum(1 for row in render_queue if "asset" in row.get("blockers", ""))),
        metric("Render prep packets", len(render_prep_packets)),
        metric("Render packets ready", sum(1 for row in render_prep_packets if row.get("packet_status") == "ready_for_manual_render_review")),
        metric("Render handoff", render_handoff_summary.get("handoff_status", "not_created")),
        metric("Decision stop/go", stop_go_summary["panel_status"], stop_go_summary["next_step"]),
        metric("Review-order checklist", len(review_order_checklist)),
        metric("Manual asset source board", len(manual_asset_source_board)),
        metric("Manual logo intake bridge", len(manual_logo_verification_intake)),
        metric("Manual league-mark intake bridge", len(manual_league_mark_context_intake)),
        metric("Decision UI", operator_decision_panel["panel_status"], operator_decision_panel["next_step"]),
        metric("Decision inbox rows", operator_decision_panel["inbox_rows"]),
        metric("Release readiness", release_readiness_panel["status"], release_readiness_panel["next_step"]),
        metric("Release blockers", release_readiness_panel["blocker_count"]),
        metric("Latest guardrail scan", release_readiness_panel["latest_scan_status"], f"files={release_readiness_panel['latest_scan_files_checked']}; violations={release_readiness_panel['latest_scan_violations']}"),
        metric("Asset audit", asset_readiness_panel["panel_status"], asset_readiness_panel["next_step"]),
        metric("Asset blockers", asset_readiness_panel["finding_count"]),
        metric("Asset errors/warnings", f"{asset_readiness_panel['error_count']}/{asset_readiness_panel['warning_count']}"),
        metric("Default photo approvals", asset_readiness_panel["default_player_approval_findings"]),
        metric("Athlete photo review", athlete_photo_panel["panel_status"], athlete_photo_panel["next_step"]),
        metric("Athlete photo variants", f"{athlete_photo_panel['review_variant_ready']}/{athlete_photo_panel['source_rows']}"),
        metric("Athlete contact sheets", athlete_photo_panel["contact_sheets"]),
        metric("Athlete source boards", f"{athlete_photo_panel['athlete_contact_sheet_teams']}/{athlete_photo_panel['athlete_contact_sheet_rows']}"),
        metric("Studio bundles", len(studio)),
        metric("Handoff packets", handoff_counts.get("handoff_packets") or "0"),
        metric("Source registry", source_registry_status(source_registry_counts), source_registry_detail(source_registry_counts)),
        metric("Day type", first_present(ops.get("day_type"), default="normal_day")),
    ]
    next_actions = build_next_actions(
        operator,
        guard,
        candidates,
        studio,
        render_queue,
        render_prep_packets,
        render_handoff_summary,
        source_board,
        promotions,
        coverage_map,
        source_proposal_review,
        source_proposal_draft,
        source_proposal_promotion_checklist,
        source_registry_update_worksheet,
        source_registry_diff_review,
        source_registry_same_domain_resolution,
        source_registry_verification_log,
        source_registry_approval_packet,
        source_registry_patch_preview,
        source_registry_post_edit_validation,
        source_proposal_pack_readiness,
        source_proposal_packs,
        artifacts,
    )
    if as_int(source_registry_counts.get("fail")) or as_int(source_registry_counts.get("review")):
        next_actions.insert(
            0,
            {
                "rank": "1",
                "status": "Source review",
                "owner": "Operator",
                "title": "Review source registry audit",
                "detail": source_registry_detail(source_registry_counts),
                "artifact": "source_registry_audit.md",
            },
        )
        next_actions = trim_actions(next_actions)
    source_rows = source_health(manifest)
    source_state = source_registry_detail(source_registry_counts) if source_registry_counts else f"{sum(1 for row in source_rows if clean(row.get('ok')).lower() == 'yes')} source check(s) OK"
    briefing = {
        "best_candidate": candidates[0]["headline"] if candidates else "No content candidate found",
        "studio_lane": studio[0]["name"] if studio else "No studio bundle found",
        "source_state": source_state,
        "next_manual_move": next_actions[0]["title"] if next_actions else "Review local artifacts",
    }
    operator_next_action_synthesis = build_operator_next_action_synthesis()

    return {
        "version": VERSION,
        "generated_at_utc": generated_at,
        "decision": decision,
        "briefing": briefing,
        "metrics": metrics,
        "next_actions": next_actions,
        "operator_next_action_synthesis": operator_next_action_synthesis,
        "schedule": schedule,
        "content_candidates": candidates,
        "render_readiness_queue": render_queue,
        "render_prep_packets": render_prep_packets,
        "render_handoff_summary": render_handoff_summary,
        "decision_stop_go_summary": stop_go_summary,
        "decision_review_order_checklist": review_order_checklist,
        "manual_asset_source_board": manual_asset_source_board,
        "manual_logo_verification_intake": manual_logo_verification_intake,
        "manual_league_mark_context_intake": manual_league_mark_context_intake,
        "operator_decision_panel": operator_decision_panel,
        "asset_readiness_panel": asset_readiness_panel,
        "release_readiness_panel": release_readiness_panel,
        "athlete_photo_onboarding_panel": athlete_photo_panel,
        "breaking_public_signal_clusters": breaking_clusters,
        "source_discovery_board": source_board,
        "lead_promotion_recommendations": promotions,
        "source_coverage_map": coverage_map,
        "source_registry_intake_template": source_intake_rows,
        "source_registry_proposal_review": source_proposal_review,
        "source_registry_proposal_draft": source_proposal_draft,
        "source_registry_proposal_promotion_checklist": source_proposal_promotion_checklist,
        "source_registry_update_worksheet": source_registry_update_worksheet,
        "source_registry_diff_review": source_registry_diff_review,
        "source_registry_same_domain_resolution": source_registry_same_domain_resolution,
        "source_registry_verification_log": source_registry_verification_log,
        "source_registry_approval_packet": source_registry_approval_packet,
        "source_registry_patch_preview": source_registry_patch_preview,
        "source_registry_post_edit_validation": source_registry_post_edit_validation,
        "source_registry_readiness_summary": source_registry_readiness_summary,
        "source_proposal_pack_readiness": source_proposal_pack_readiness,
        "source_proposal_packs": source_proposal_packs,
        "wnba_source_proposal_pack": wnba_source_proposal_pack,
        "nwsl_source_proposal_pack": nwsl_source_proposal_pack,
        "lpga_source_proposal_pack": lpga_source_proposal_pack,
        "pwhl_source_proposal_pack": pwhl_source_proposal_pack,
        "studio_queue": studio,
        "source_health": source_rows,
        "issues": operator.get("issues") or guard.get("issues") or [],
        "artifacts": artifacts,
        "counts": counts,
    }


def pill(value: Any, tone: str | None = None) -> str:
    text = clean(value)
    return f'<span class="pill {html.escape(tone or status_tone(text))}">{html.escape(text)}</span>'


def open_link(path: str, label: str = "Open") -> str:
    if not path or not find_existing_input(path).exists():
        return '<span class="muted">Missing</span>'
    return f'<a class="tool-link" href="{html.escape(href_for_path(path))}">{html.escape(label)}</a>'


def command_hint(command: str) -> str:
    command = clean(command)
    if not command:
        return ""
    return f'<div class="command-line"><span>Run next</span><code>{html.escape(command)}</code></div>'


def render_release_readiness_checks(rows: Iterable[Dict[str, Any]]) -> str:
    rendered: List[str] = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{html.escape(clean(row.get('check_id')))}</td>"
            f"<td>{pill(row.get('status'))}</td>"
            f"<td>{html.escape(clean(row.get('detail')))}</td>"
            f"<td><code>{html.escape(clean(row.get('evidence')))}</code></td>"
            f"<td>{html.escape(clean(row.get('operator_next_step')))}</td>"
            "</tr>"
        )
    if not rendered:
        return '<tr><td colspan="5" class="empty">Release-readiness rollup has not been generated yet.</td></tr>'
    return "".join(rendered)


def render_release_readiness_panel(panel: Dict[str, Any]) -> str:
    missing = ", ".join(clean(item) for item in panel.get("missing_inputs", []) if clean(item)) or "none"
    return f"""
      <div class="panel" style="margin-bottom:16px">
        <div class="section-heading">
          <div>
            <span class="row-kicker">Release-readiness evidence</span>
            <h2>Guardrail rollup</h2>
            <p class="muted">Review-only visibility across deterministic guardrails, latest generated artifacts, and conductor collision brakes.</p>
          </div>
          {open_link('release_readiness_guardrail_rollup.md', 'Open rollup')}
        </div>
        <div class="safety-strip">
          {pill(panel.get('status'))}
          {pill('blockers: ' + clean(panel.get('blocker_count')), 'bad' if as_int(panel.get('blocker_count')) else 'good')}
          {pill('latest scan: ' + clean(panel.get('latest_scan_status')))}
          {pill('conductor: ' + clean(panel.get('conductor_status')))}
          {pill('workflow stale: ' + clean(panel.get('workflow_stale_lanes')), 'bad' if as_int(panel.get('workflow_stale_lanes')) else 'good')}
        </div>
        <p class="muted" style="margin-top:10px">{html.escape(clean(panel.get('next_step')))}</p>
        <p class="muted" style="margin-top:6px">Latest files checked: <code>{as_int(panel.get('latest_scan_files_checked'))}</code>; violations: <code>{as_int(panel.get('latest_scan_violations'))}</code>; missing inputs: <code>{html.escape(missing)}</code>.</p>
        <p class="muted" style="margin-top:6px">Workflow lane status: <code>{html.escape(clean(panel.get('workflow_status')))}</code>; stale brakes: <code>{as_int(panel.get('workflow_stale_lanes'))}</code>; restart-needed: <code>{as_int(panel.get('workflow_restart_needed'))}</code>; lifecycle actions: <code>{as_int(panel.get('workflow_lifecycle_actions'))}</code>.</p>
        <div class="table-wrap" style="margin-top:12px">
          <table>
            <thead><tr><th>Check</th><th>Status</th><th>Detail</th><th>Evidence</th><th>Next step</th></tr></thead>
            <tbody>{render_release_readiness_checks(panel.get('checks', []))}</tbody>
          </table>
        </div>
      </div>
    """


def artifact_tool(row: Dict[str, Any]) -> str:
    if row.get("exists"):
        return open_link(row["path"])
    command = clean(row.get("run_command"))
    if command:
        return f'<code>{html.escape(command)}</code>'
    return '<span class="muted">Missing</span>'


def render_action_rows(actions: Iterable[Dict[str, str]]) -> str:
    rows = []
    for action in actions:
        rows.append(
            f"""
            <article class="action-row">
              <div class="rank">{html.escape(action['rank'])}</div>
              <div>
                <div class="row-kicker">{html.escape(action['owner'])} {pill(action['status'])}</div>
                <h3>{html.escape(action['title'])}</h3>
                <p>{html.escape(action['detail'])}</p>
                {command_hint(action.get('command', ''))}
              </div>
              <div class="row-tool">{open_link(action.get('artifact', ''))}</div>
            </article>
            """
        )
    return "".join(rows) or '<p class="empty">No next actions found.</p>'


def render_next_action_synthesis(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        status_tone_value = "good" if row.get("artifact_status") == "ready_to_open" else "neutral"
        cards.append(
            f"""
            <article class="action-row">
              <div class="rank">{html.escape(row['rank'])}</div>
              <div>
                <div class="row-kicker">{html.escape(row['lane'])} {pill(row.get('artifact_status'), status_tone_value)}</div>
                <h3>{html.escape(row['manual_step'])}</h3>
                <p><strong>Return fields:</strong> {html.escape(row.get('operator_return_fields', ''))}</p>
                <p><strong>Lane detail:</strong> {html.escape(row.get('lane_detail') or 'Open the linked artifact for current counts.')}</p>
                <p><strong>Resolved local path:</strong> {html.escape(row.get('primary_resolved_path') or 'missing_or_not_generated')}</p>
                <p>{html.escape(row.get('guardrail_note', 'Review-only.'))}</p>
                {command_hint(row.get('run_command', ''))}
              </div>
              <div class="row-tool">
                {open_link(row.get('primary_artifact', ''))}
                <small>{html.escape(row.get('primary_artifact', ''))}</small>
                {open_link(row.get('companion_artifact', ''), 'Companion')}
              </div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No synthesized next actions found.</p>'


def render_source_registry_readiness_summary(summary: Dict[str, str]) -> str:
    open_first = clean(summary.get("open_first_file"))
    support_file = clean(summary.get("support_file")) or "trusted_registry_operator_playbook.md"
    return f"""
    <article class="content-row">
      <div>
        <div class="row-kicker">Source registry readiness {pill(summary.get('readiness_status') or 'review')}</div>
        <h3>{html.escape(clean(summary.get('next_safest_action')) or 'Open the trusted-registry operator playbook.')}</h3>
        <p><strong>Blockers:</strong> {html.escape(clean(summary.get('blockers')) or 'none')}</p>
        <p><strong>Focus:</strong> {html.escape(clean(summary.get('focus_source_ids')) or 'none')}</p>
        <small>{html.escape(clean(summary.get('rollup')) or 'No registry readiness rollup found.')} {html.escape(clean(summary.get('guardrail')) or '')}</small>
      </div>
      <div class="row-tool">
        {open_link(open_first, 'Open next')}
        <div style="margin-top:8px">{open_link(support_file, 'Playbook')}</div>
      </div>
    </article>
    """


def render_schedule(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(row['time'])}</td>
              <td>{html.escape(row['platform'])}</td>
              <td>{html.escape(row['slot'])}</td>
              <td>{pill(row['status'])}</td>
              <td>{html.escape(row['action'])}</td>
              <td>{open_link(row['artifact']) if row['artifact'] else '<span class="muted">-</span>'}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="6" class="empty">No posting schedule found.</td></tr>'


def render_content(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        readiness = (
            f"render: {html.escape(row.get('render_readiness_score') or 'n/a')}/100"
            f" / {html.escape(row.get('render_readiness_band') or 'not_scored')}"
            f" / source: {html.escape(row.get('render_readiness_source_cue') or 'n/a')}"
            f" / assets: {html.escape(row.get('render_readiness_asset_cue') or 'n/a')}"
            f" / format: {html.escape(row.get('render_readiness_format_cue') or 'n/a')}"
            f" / path: {html.escape(row.get('render_readiness_manual_path') or 'n/a')}"
        )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row['type'])} {pill(row['priority'])} {pill(row['status'])}</div>
                <h3>{html.escape(row['headline'])}</h3>
                <p>{html.escape(row['detail'])}</p>
                <small>{html.escape(row.get('source_count') or '0')} source(s) / {html.escape(row.get('source_grade') or 'not_scored')} {f"({html.escape(row.get('source_score') or '')})" if row.get('source_score') else ""} / {readiness}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No content candidates found.</p>'


def render_render_readiness(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('rank')))}</td>
              <td>{pill(row.get('band') or 'not_scored')}</td>
              <td>{html.escape(clean(row.get('score')) or '0')}</td>
              <td>{html.escape(clean(row.get('title')))}</td>
              <td>{html.escape(clean(row.get('recommended_path')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_cue')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('asset_cue')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('format_cue')) or 'n/a')}</td>
              <td>{html.escape(clean(row.get('manual_path')) or 'n/a')}</td>
              <td>{html.escape(display_render_blockers(row))}</td>
              <td>{html.escape(clean(row.get('next_step')))}</td>
              <td>{open_link(clean(row.get('artifact')))}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="12" class="empty">No render-readiness candidates found.</td></tr>'


def render_render_prep_packets(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        selected_template = clean(row.get("selected_template_id")) or clean(row.get("template_fit")) or "operator_review"
        template_meta = " / ".join(
            part
            for part in [
                f"fit: {clean(row.get('template_fit'))}" if clean(row.get("template_fit")) else "",
                f"pack: {clean(row.get('reference_pack_id'))}" if clean(row.get("reference_pack_id")) else "",
            ]
            if part
        )
        body.append(
            f"""
            <tr>
              <td>{pill(row.get('packet_status') or 'review')}</td>
              <td>{html.escape(clean(row.get('render_readiness_score')) or '0')}</td>
              <td>{html.escape(clean(row.get('title')))}</td>
              <td><strong>{html.escape(selected_template)}</strong>{f'<small class="cell-detail">{html.escape(template_meta)}</small>' if template_meta else ''}</td>
              <td>{html.escape(clean(row.get('template_shape')))}</td>
              <td>{html.escape(clean(row.get('copy_headline')))}</td>
              <td>{html.escape(clean(row.get('asset_requirement')))}</td>
              <td>{html.escape(clean(row.get('manual_renderer_steps')))}</td>
              <td>{html.escape(clean(row.get('approval_gate')))}</td>
              <td>{open_link('render_prep_packets.md', 'Open packet')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="10" class="empty">No render-prep packets cleared review gates.</td></tr>'


def render_render_handoff_summary(summary: Dict[str, Any]) -> str:
    files = summary.get("files") or []
    file_links = " ".join(open_link(clean(path), Path(clean(path)).name) for path in files[:6])
    return f"""
    <article class="content-row">
      <div>
        <div class="row-kicker">Render handoff {pill(summary.get('handoff_status') or 'not_created')}</div>
        <h3>{html.escape(clean(summary.get('title')) or 'No top render handoff ready')}</h3>
        <p>Review-only folder: <code>{html.escape(clean(summary.get('folder')) or 'render_handoff_top_packet')}</code>. Use copy sheet, asset checklist, source proof, and manual renderer prompt before any human visual review.</p>
        <small>Guardrails: no paid APIs / no auto-runs / no auto-rendering / no publishing.</small>
      </div>
      <div class="row-tool">
        {open_link(clean(summary.get('readme')) or 'render_handoff_top_packet/README.md', 'Open folder')}
        <div style="margin-top:8px">{file_links}</div>
      </div>
    </article>
    """


def render_decision_stop_go_summary_panel(summary: Dict[str, Any]) -> str:
    tone = clean(summary.get("status_tone")) or "warn"
    return f"""
      <div class="decision-desk-section stop-go-summary-card">
        <div class="decision-cockpit-card asset-readiness-cockpit">
          <div class="decision-cockpit-head">
            <div>
              <span class="row-kicker">What blocks this render now?</span>
              <strong>{html.escape(clean(summary.get('panel_status')) or 'not_run')}</strong>
              <p>{html.escape(clean(summary.get('next_step')))}</p>
            </div>
            <div class="decision-cockpit-actions">
              {pill(clean(summary.get('active_asset_stop_go')) or 'clear_no_active_asset_holds', tone)}
              {pill('review-only')}
              {pill('publish-ready: false')}
            </div>
          </div>
          <div class="decision-status-grid">
            <div><span>Selected-template blockers</span><strong>{html.escape(str(summary.get('selected_template_blockers', 0)))}</strong><small>{html.escape(clean(summary.get('selected_template_entities')) or 'none')}</small></div>
            <div><span>Future photo-first holds</span><strong>{html.escape(str(summary.get('future_photo_first_holds', 0)))}</strong><small>{html.escape(clean(summary.get('future_photo_first_entities')) or 'none')}</small></div>
            <div><span>League-mark context</span><strong>{html.escape(str(summary.get('league_mark_context_holds', 0)))}</strong><small>{html.escape(clean(summary.get('league_mark_context_entities')) or 'none')}</small></div>
            <div><span>Source-board rows</span><strong>{html.escape(str(summary.get('source_board_rows', 0)))}</strong><small>manual source evidence only</small></div>
          </div>
          <div class="asset-blocker-actions">
            {open_link(clean(summary.get('active_queue_artifact')) or 'render_handoff_top_packet/active_asset_review_queue.md', 'Open active queue')}
            {open_link(clean(summary.get('manual_asset_source_board_artifact')) or 'render_handoff_top_packet/manual_asset_source_board.md', 'Open source board')}
            {pill('no downloads')}
            {pill('no auto-approval')}
            {pill('no publishing')}
          </div>
          <div class="asset-guidance-grid">
            <div><span>Selected-template evidence gap</span><strong>{html.escape(short(clean(summary.get('selected_template_evidence_gaps')) or 'none', 220))}</strong></div>
            <div><span>League-mark context evidence gap</span><strong>{html.escape(short(clean(summary.get('league_mark_evidence_gaps')) or 'none', 220))}</strong></div>
          </div>
          <p class="muted">{html.escape(clean(summary.get('guardrail_summary')))}</p>
        </div>
      </div>
    """


def render_decision_review_order_checklist(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        artifact = clean(row.get("artifact"))
        body.append(
            f"""
            <article class="asset-blocker-card review-order-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">step {html.escape(clean(row.get('rank')) or '-')} / review-only</span>
                  <strong>{html.escape(clean(row.get('title')))}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill('no approval change', 'good')}
                  {pill('no downloads', 'good')}
                </div>
              </div>
              <p>{html.escape(short(clean(row.get('reason')), 190))}</p>
              <p class="muted">{html.escape(short(clean(row.get('operator_action')), 190))}</p>
              <code>{html.escape(artifact)}</code>
              <div class="asset-blocker-actions">
                {open_link(artifact, 'Open')}
                {pill('review-only')}
                {pill('publish-ready: false')}
                {pill('auto-approval: false')}
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No review-order checklist rows found.</p>'


def render_decision_review_order_panel(rows: Iterable[Dict[str, str]]) -> str:
    checklist = list(rows)
    return f"""
      <div class="decision-desk-section review-order-checklist">
        <div class="row-kicker">Open these in order {pill(str(len(checklist)) + ' steps')} {pill('display-only')} {pill('review-only')}</div>
        <p class="muted">Ordered review path for the current stop/go state. These links do not approve assets, download files, move files, publish, or create a publish-ready lane.</p>
        <div class="asset-blocker-grid">
          {render_decision_review_order_checklist(checklist)}
        </div>
      </div>
    """


def render_manual_asset_source_board_cards(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        source_hint = clean(row.get("source_hint_url"))
        source_link = f'<a class="tool-link" href="{html.escape(source_hint)}">Source hint</a>' if source_hint else '<span class="muted">Manual lookup</span>'
        board_link = open_link("render_handoff_top_packet/manual_asset_source_board.md", "Open board")
        body.append(
            f"""
            <article class="asset-blocker-card manual-source-board-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">{html.escape(clean(row.get('priority')))} / {html.escape(clean(row.get('asset_domain')))}</span>
                  <strong>{html.escape(clean(row.get('entity_name')) or clean(row.get('entity_id')))}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill(clean(row.get('manual_approval_status')) or 'manual_review_required', 'warn')}
                  {pill('review-only')}
                </div>
              </div>
              <p>{html.escape(short(clean(row.get('required_asset')), 180))}</p>
              <div class="asset-guidance-grid">
                <div><span>Official/free source</span><strong>{html.escape(short(clean(row.get('official_source_candidate')), 135))}</strong></div>
                <div><span>Current registry source</span><strong>{html.escape(short(clean(row.get('current_registry_source')) or 'missing', 135))}</strong></div>
                <div><span>Search</span><strong>{html.escape(short(clean(row.get('manual_search_query')), 135))}</strong></div>
                <div><span>Local asset</span><strong>{html.escape(short(clean(row.get('current_local_asset')) or 'missing', 135))}</strong></div>
                <div><span>Asset state</span><strong>{html.escape(short(clean(row.get('local_asset_state')) or 'manual_review_required', 135))}</strong></div>
                <div><span>Evidence gap</span><strong>{html.escape(short(clean(row.get('evidence_gap_status')) or 'manual_evidence_review_required', 135))}</strong></div>
                <div><span>Action</span><strong>{html.escape(short(clean(row.get('recommended_operator_action')), 135))}</strong></div>
              </div>
              <p class="muted"><strong>Cannot clear automatically because:</strong> {html.escape(short(clean(row.get('cannot_clear_automatically_because')) or 'Manual evidence review is required before any renderer trust change.', 220))}</p>
              <p class="muted">{html.escape(short(clean(row.get('free_source_candidate')), 180))}</p>
              <p class="muted">Legacy reference only: {html.escape(short(clean(row.get('legacy_reference_model')), 150))}</p>
              <div class="asset-blocker-actions">
                {source_link}
                {board_link}
                {pill('no downloads')}
                {pill('no auto-approval')}
                {pill('publish-ready: false')}
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No active manual asset source-board rows found.</p>'


def render_manual_asset_source_board_panel(rows: Iterable[Dict[str, str]]) -> str:
    board_rows = list(rows)
    p0 = sum(1 for row in board_rows if clean(row.get("priority")) == "P0_selected_template_hold")
    future = sum(1 for row in board_rows if clean(row.get("priority")) == "P1_future_photo_first_hold")
    league = sum(1 for row in board_rows if clean(row.get("priority")) == "P2_league_mark_context")
    return f"""
      <div class="decision-desk-section">
        <div class="row-kicker">Manual Asset Source Board {pill(str(len(board_rows)) + ' rows')} {pill(str(p0) + ' selected-template holds')} {pill(str(future) + ' future photo-first')} {pill(str(league) + ' league context')}</div>
        <p class="muted">Old HSD asset-index/DDG packet structure, rebuilt as current review-only source guidance. Nothing here downloads, approves, moves, publishes, or creates a publish-ready lane.</p>
        <div class="asset-blocker-grid">
          {render_manual_asset_source_board_cards(board_rows)}
        </div>
      </div>
    """


def render_manual_logo_verification_intake_cards(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        intake_link = open_link("render_handoff_top_packet/manual_logo_verification_intake.md", "Open intake")
        body.append(
            f"""
            <article class="asset-blocker-card manual-logo-intake-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">{html.escape(clean(row.get('priority')))} / selected-template logo</span>
                  <strong>{html.escape(clean(row.get('entity_name')) or clean(row.get('entity_id')))}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill(clean(row.get('current_unapproved_status')) or 'unapproved_review_required', 'warn')}
                  {pill('approval change: false', 'good')}
                </div>
              </div>
              <div class="asset-guidance-grid">
                <div><span>Exact local logo path</span><strong>{html.escape(short(clean(row.get('local_logo_path')) or 'missing', 135))}</strong></div>
                <div><span>Official source candidate</span><strong>{html.escape(short(clean(row.get('official_source_candidate')) or 'manual lookup required', 135))}</strong></div>
                <div><span>Current legacy source</span><strong>{html.escape(short(clean(row.get('current_legacy_registry_source')) or 'missing', 135))}</strong></div>
                <div><span>Human-edited files</span><strong>{html.escape(short(clean(row.get('manual_intake_files')), 160))}</strong></div>
              </div>
              <p class="muted"><strong>Required manual checks:</strong> {html.escape(short(clean(row.get('required_manual_checks')), 220))}</p>
              <p class="muted"><strong>Cannot clear automatically because:</strong> {html.escape(short(clean(row.get('cannot_clear_automatically_because')), 220))}</p>
              <div class="asset-blocker-actions">
                {intake_link}
                {open_link(clean(row.get('manual_review_packet')) or 'data/asset_registry/wnba/logo_review_catalog_report.md', 'Open review packet')}
                {pill('no downloads')}
                {pill('no auto-approval')}
                {pill('publish-ready: false')}
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No selected-template logo intake bridge rows found.</p>'


def render_manual_logo_verification_intake_panel(rows: Iterable[Dict[str, str]]) -> str:
    intake_rows = list(rows)
    return f"""
      <div class="decision-desk-section">
        <div class="row-kicker">Manual Logo Verification Intake Bridge {pill(str(len(intake_rows)) + ' rows')} {pill('review-only')} {pill('approval change: false')}</div>
        <p class="muted">Human verification path for selected-template logo blockers. This only points to exact evidence and human-edited intake files; it does not approve assets or change registry state.</p>
        <div class="asset-blocker-grid">
          {render_manual_logo_verification_intake_cards(intake_rows)}
        </div>
      </div>
    """


def render_manual_league_mark_context_intake_cards(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        intake_link = open_link("render_handoff_top_packet/manual_league_mark_context_intake.md", "Open intake")
        body.append(
            f"""
            <article class="asset-blocker-card manual-league-mark-intake-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">{html.escape(clean(row.get('priority')))} / optional league mark</span>
                  <strong>{html.escape(clean(row.get('entity_name')) or clean(row.get('entity_id')))}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill(clean(row.get('current_approval_status')) or 'manual_review_required', 'warn')}
                  {pill('non-blocking unless required', 'good')}
                </div>
              </div>
              <div class="asset-guidance-grid">
                <div><span>Local league-mark path</span><strong>{html.escape(short(clean(row.get('local_league_mark_path')) or 'missing', 135))}</strong></div>
                <div><span>Official source candidate</span><strong>{html.escape(short(clean(row.get('official_source_candidate')) or 'manual lookup required', 135))}</strong></div>
                <div><span>Current registry source</span><strong>{html.escape(short(clean(row.get('current_registry_source')) or 'missing', 135))}</strong></div>
                <div><span>Human-edited intake</span><strong>{html.escape(short(clean(row.get('manual_intake_files')), 160))}</strong></div>
                <div><span>Template rule</span><strong>{html.escape(short(clean(row.get('template_requirement_rule')), 135))}</strong></div>
                <div><span>Evidence gap</span><strong>{html.escape(short(clean(row.get('evidence_gap_status')) or 'manual_evidence_review_required', 135))}</strong></div>
              </div>
              <p class="muted"><strong>Selected-template rule:</strong> {html.escape(short(clean(row.get('selected_template_blocking_reason')), 220))}</p>
              <p class="muted"><strong>Required manual checks:</strong> {html.escape(short(clean(row.get('required_manual_checks')), 220))}</p>
              <p class="muted"><strong>Cannot clear automatically because:</strong> {html.escape(short(clean(row.get('cannot_clear_automatically_because')), 220))}</p>
              <div class="asset-blocker-actions">
                {intake_link}
                {open_link(clean(row.get('manual_review_packet')) or 'data/asset_registry/wnba/logo_review_catalog_report.md', 'Open logo catalog')}
                {pill('no downloads')}
                {pill('no auto-approval')}
                {pill('publish-ready: false')}
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No league-mark context intake rows found.</p>'


def render_manual_league_mark_context_intake_panel(rows: Iterable[Dict[str, str]]) -> str:
    intake_rows = list(rows)
    return f"""
      <div class="decision-desk-section">
        <div class="row-kicker">Manual League-Mark Context Intake {pill(str(len(intake_rows)) + ' rows')} {pill('optional unless required')} {pill('approval change: false')}</div>
        <p class="muted">Human review path for WNBA league-mark context. If a selected template does not require a league mark, this remains non-blocking review-only context.</p>
        <div class="asset-blocker-grid">
          {render_manual_league_mark_context_intake_cards(intake_rows)}
        </div>
      </div>
    """


def render_studio(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row['priority'])} {pill(row['status'])}</div>
                <h3>{html.escape(row['name'])}</h3>
                <p>{html.escape(row['detail'])}</p>
                <small>{html.escape(row['type'])} / {html.escape(row['shape'])}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No studio bundles found.</p>'


def render_source_discovery(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        detail = html.escape(row.get("detail") or "")
        next_action = html.escape(row.get("next_action") or "")
        detail_html = f"<p>{detail}</p>" if detail else ""
        next_html = f"<p>Next: {next_action}</p>" if next_action and next_action != detail else ""
        opportunity_note = ""
        if row.get("story_opportunity_id"):
            opportunity_note = (
                f" / opportunity: {html.escape(row.get('story_opportunity_size') or '1')} source(s)"
                f" from {html.escape(row.get('story_opportunity_sources') or row.get('source') or '')}"
            )
        angle_note = ""
        if row.get("story_opportunity_angle") or row.get("story_opportunity_recommended_path"):
            angle_note = (
                f" / angle: {html.escape(row.get('story_opportunity_angle') or 'review')}"
                f" / path: {html.escape(row.get('story_opportunity_recommended_path') or row.get('promotion') or 'review')}"
            )
        readiness_note = ""
        if row.get("story_opportunity_confidence_tier") or row.get("story_opportunity_source_coverage"):
            readiness_note = (
                f" / confidence: {html.escape(row.get('story_opportunity_confidence_tier') or 'review')}"
                f" / coverage: {html.escape(row.get('story_opportunity_source_coverage') or 'n/a')}"
                f" / cue: {html.escape(row.get('story_opportunity_confirmation_cue') or 'n/a')}"
                f" / assets: {html.escape(row.get('story_opportunity_asset_cue') or 'n/a')}"
            )
        second_source_note = ""
        if row.get("story_opportunity_second_source_id") or row.get("story_opportunity_second_source_lane"):
            second_source_note = (
                f" / second source: {html.escape(row.get('story_opportunity_second_source_id') or row.get('story_opportunity_second_source_lane') or 'n/a')}"
            )
        render_note = (
            f" / render: {html.escape(row.get('render_readiness_score') or 'n/a')}/100"
            f" / {html.escape(row.get('render_readiness_band') or 'not_scored')}"
            f" / path: {html.escape(row.get('render_readiness_manual_path') or 'n/a')}"
        )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row.get('rank') or '-')} {pill(row['lane'])} {pill(row['status'])} {pill(row['posture'])}</div>
                <h3>{html.escape(row['title'])}</h3>
                {detail_html}
                {next_html}
                <small>{html.escape(row.get('source') or '')} / {html.escape(row.get('band') or '')} / promote: {html.escape(row.get('promotion') or 'monitor_only')} / quality: {html.escape(row.get('quality_score') or 'n/a')} / {html.escape(row.get('freshness_label') or 'undated')}{' via ' + html.escape(row.get('freshness_source') or '') if row.get('freshness_source') else ''}{opportunity_note}{angle_note}{readiness_note}{second_source_note}{render_note}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No morning source rows found.</p>'


def render_lead_promotions(rows: Iterable[Dict[str, str]]) -> str:
    cards = []
    for row in rows:
        detail = html.escape(row.get("detail") or "")
        next_step = html.escape(row.get("next_step") or row.get("reason") or "")
        detail_html = f"<p>{detail}</p>" if detail else ""
        next_html = f"<p>Next: {next_step}</p>" if next_step and next_step != detail else ""
        opportunity_note = ""
        if row.get("story_opportunity_id"):
            opportunity_note = (
                f" / opportunity: {html.escape(row.get('story_opportunity_size') or '1')} source(s)"
                f" from {html.escape(row.get('story_opportunity_sources') or '')}"
            )
        angle_note = ""
        if row.get("story_opportunity_angle") or row.get("story_opportunity_recommended_path"):
            angle_note = (
                f" / angle: {html.escape(row.get('story_opportunity_angle') or 'review')}"
                f" / path: {html.escape(row.get('story_opportunity_recommended_path') or row.get('recommendation') or 'review')}"
            )
        readiness_note = ""
        if row.get("story_opportunity_confidence_tier") or row.get("story_opportunity_source_coverage"):
            readiness_note = (
                f" / confidence: {html.escape(row.get('story_opportunity_confidence_tier') or 'review')}"
                f" / coverage: {html.escape(row.get('story_opportunity_source_coverage') or 'n/a')}"
                f" / cue: {html.escape(row.get('story_opportunity_confirmation_cue') or 'n/a')}"
                f" / assets: {html.escape(row.get('story_opportunity_asset_cue') or 'n/a')}"
            )
        second_source_note = ""
        if row.get("story_opportunity_second_source_id") or row.get("story_opportunity_second_source_lane"):
            second_source_note = (
                f" / second source: {html.escape(row.get('story_opportunity_second_source_id') or row.get('story_opportunity_second_source_lane') or 'n/a')}"
            )
        render_note = (
            f" / render: {html.escape(row.get('render_readiness_score') or 'n/a')}/100"
            f" / {html.escape(row.get('render_readiness_band') or 'not_scored')}"
            f" / path: {html.escape(row.get('render_readiness_manual_path') or 'n/a')}"
        )
        cards.append(
            f"""
            <article class="content-row">
              <div>
                <div class="row-kicker">{html.escape(row.get('rank') or '-')} {pill(row['priority'])} {pill(row['recommendation'])}</div>
                <h3>{html.escape(row['title'])}</h3>
                {detail_html}
                {next_html}
                <small>{html.escape(row.get('lane') or '')} / target: {html.escape(row.get('target') or '')} / quality: {html.escape(row.get('quality_score') or 'n/a')} / {html.escape(row.get('freshness_label') or 'undated')}{' via ' + html.escape(row.get('freshness_source') or '') if row.get('freshness_source') else ''}{opportunity_note}{angle_note}{readiness_note}{second_source_note}{render_note}</small>
              </div>
              <div>{open_link(row['artifact'])}</div>
            </article>
            """
        )
    return "".join(cards) or '<p class="empty">No lead promotion recommendations found.</p>'


def render_source_coverage(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(row['name'])}</td>
              <td>{pill(row['status'])}</td>
              <td>{html.escape(row.get('official') or '-')}</td>
              <td>{html.escape(row.get('team') or '-')}</td>
              <td>{html.escape(row.get('wire') or '-')}</td>
              <td>{html.escape(row.get('cross_check') or '-')}</td>
              <td>{html.escape(row.get('gap') or 'none')}</td>
              <td>{html.escape(row.get('next_step') or '')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="8" class="empty">No source coverage map found.</td></tr>'


def render_source_intake(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('display_name')))}</td>
              <td>{html.escape(clean(row.get('needed_source_type')))}</td>
              <td>{html.escape(clean(row.get('coverage_gap')))}</td>
              <td>{html.escape(clean(row.get('source_type')))}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')))}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="7" class="empty">No source intake proposals found.</td></tr>'


def render_source_proposal_packs(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('pack_name')) or clean(row.get('display_name')))}</td>
              <td>{html.escape(clean(row.get('candidate_group')))}</td>
              <td>{html.escape(clean(row.get('suggested_priority')))}</td>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_source_name')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')) or 'proposal_only_do_not_import')}</td>
              <td>{html.escape(clean(row.get('registry_presence')) or 'not_checked')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No guided source proposal packs found.</td></tr>'


def render_source_proposal_pack_readiness(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('pack_name')) or clean(row.get('display_name')))}</td>
              <td>{pill(clean(row.get('readiness_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('candidate_rows')) or '0')}</td>
              <td>{html.escape(clean(row.get('official_candidates')) or '0')}</td>
              <td>{html.escape(clean(row.get('cross_check_candidates')) or '0')}</td>
              <td>{html.escape(clean(row.get('duplicate_candidates')) or '0')}</td>
              <td>{html.escape(clean(row.get('review_cues')) or '-')}</td>
              <td>{html.escape(clean(row.get('top_candidate_ids')) or '-')}</td>
              <td>{html.escape(clean(row.get('next_step')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source pack readiness cues found.</td></tr>'


def render_source_proposal_draft(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('draft_selection_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('pack_name')) or clean(row.get('display_name')))}</td>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('draft_action')) or '-')}</td>
              <td>{html.escape(clean(row.get('duplicate_warning')) or '-')}</td>
              <td>{html.escape(clean(row.get('freshness_warning')) or '-')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')) or 'proposal_only_do_not_import')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source proposal draft rows found.</td></tr>'


def render_source_proposal_promotion_checklist(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        reason = clean(row.get("hold_reason")) or clean(row.get("discard_reason")) or clean(row.get("freshness_warning"))
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('checklist_decision')) or 'review')}</td>
              <td>{html.escape(clean(row.get('operator_step')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('copy_allowed')) or 'No')}</td>
              <td>{html.escape(clean(row.get('copy_target')) or '-')}</td>
              <td>{html.escape(reason or '-')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_action')) or 'proposal_only_do_not_import')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source proposal promotion checklist rows found.</td></tr>'


def render_source_registry_update_worksheet(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('worksheet_decision')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('manual_edit_target')) or 'config/source_registry.json')}</td>
              <td>{html.escape(clean(row.get('manual_edit_allowed')) or 'manual review only')}</td>
              <td>{html.escape(clean(row.get('proposed_enabled')) or 'False')}</td>
              <td>{html.escape(clean(row.get('auto_edit_status')) or 'not_performed_by_generator')}</td>
              <td>{html.escape(clean(row.get('before_after_diff')) or '-')}</td>
              <td>{html.escape(clean(row.get('rollback_note')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No source registry update worksheet rows found.</td></tr>'


def render_source_registry_diff_review(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        instruction = clean(row.get("verification_log_instruction")) or clean(row.get("recommendation")) or "-"
        label = clean(row.get("resolution_label"))
        instruction_text = f"{label}: {instruction}" if label else instruction
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('diff_review_status')) or 'review')}</td>
              <td>{pill(clean(row.get('resolution_action')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_domain')) or '-')}</td>
              <td>{html.escape(clean(row.get('flags')) or 'none')}</td>
              <td>{html.escape(clean(row.get('issues')) or 'none')}</td>
              <td>{html.escape(clean(row.get('registry_source_id_match')) or 'No')}</td>
              <td>{html.escape(clean(row.get('registry_domain_match')) or 'No')}</td>
              <td>{html.escape(clean(row.get('rollback_status')) or '-')}</td>
              <td>{html.escape(instruction_text)}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="10" class="empty">No source registry diff review rows found.</td></tr>'


def render_source_registry_same_domain_resolution(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('same_domain_resolution_status')) or 'operator_input_required')}</td>
              <td>{html.escape(clean(row.get('resolution_decision')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_domain')) or '-')}</td>
              <td>{html.escape(clean(row.get('registry_domain_match')) or clean(row.get('worksheet_domain_match')) or '-')}</td>
              <td>{html.escape(clean(row.get('compared_existing_source_id')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('evidence_url')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('evidence_requirement')) or '-')}</td>
              <td>{html.escape(clean(row.get('approval_gate')) or '-')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No same-domain resolution rows found.</td></tr>'


def render_source_registry_verification_log(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('verification_log_status')) or 'operator_input_required')}</td>
              <td>{pill(clean(row.get('diff_resolution_action')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('diff_review_status')) or '-')}</td>
              <td>{html.escape(clean(row.get('diff_resolution_instruction')) or 'follow diff review cue')}</td>
              <td>{html.escape(clean(row.get('url_checked')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('freshness_result')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('duplicate_decision')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('approval_outcome')) or 'operator fill-in')}</td>
              <td>{html.escape(clean(row.get('registry_edit_status')) or 'not_edited_by_generator')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="11" class="empty">No source verification log rows found.</td></tr>'


def render_source_registry_approval_packet(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        exact_json = clean(row.get("exact_proposed_source_json"))
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('approval_packet_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('evidence_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('freshness_result')) or '-')}</td>
              <td>{html.escape(clean(row.get('duplicate_decision')) or '-')}</td>
              <td>{html.escape(clean(row.get('hold_reason')) or 'none')}</td>
              <td>{html.escape(exact_json[:160] + ('...' if len(exact_json) > 160 else ''))}</td>
              <td>{html.escape(clean(row.get('registry_edit_status')) or 'not_edited_by_generator')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No approved source verification rows found.</td></tr>'


def render_source_registry_patch_preview(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        source_json = clean(row.get("copy_paste_source_json"))
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('patch_preview_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('manual_edit_target')) or '-')}</td>
              <td>{html.escape(clean(row.get('registry_before_summary')) or '-')}</td>
              <td>{html.escape(clean(row.get('evidence_url')) or '-')}</td>
              <td>{html.escape(clean(row.get('hold_reason')) or 'none')}</td>
              <td>{html.escape(source_json[:180] + ('...' if len(source_json) > 180 else ''))}</td>
              <td>{html.escape(clean(row.get('registry_edit_status')) or 'not_edited_by_generator')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="8" class="empty">No ready registry patch preview rows found.</td></tr>'


def render_source_registry_post_edit_validation(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{pill(clean(row.get('post_edit_validation_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('exact_match')) or '-')}</td>
              <td>{html.escape(clean(row.get('enabled_status')) or '-')}</td>
              <td>{html.escape(clean(row.get('automation_status_check')) or '-')}</td>
              <td>{html.escape(clean(row.get('publish_policy_check')) or '-')}</td>
              <td>{html.escape(clean(row.get('free_source_check')) or '-')}</td>
              <td>{html.escape(clean(row.get('drift_fields')) or 'none')}</td>
              <td>{html.escape(clean(row.get('unsafe_flags')) or 'none')}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="9" class="empty">No post-edit validation rows found.</td></tr>'


def render_source_proposal_review(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(clean(row.get('candidate_source_id')) or '-')}</td>
              <td>{html.escape(clean(row.get('candidate_url')) or '-')}</td>
              <td>{pill(clean(row.get('review_status')) or 'review')}</td>
              <td>{html.escape(clean(row.get('safety_flags')) or 'none')}</td>
              <td>{html.escape(clean(row.get('issues')) or 'none')}</td>
              <td>{html.escape(clean(row.get('recommendation')))}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="6" class="empty">No manual source proposal rows found.</td></tr>'


def render_sources(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <tr>
              <td>{html.escape(row['source'])}</td>
              <td>{html.escape(row['league'])}</td>
              <td>{html.escape(row['date'])}</td>
              <td>{pill(row['ok'])}</td>
              <td>{html.escape(row['events'])}</td>
              <td>{html.escape(row['notes'])}</td>
            </tr>
            """
        )
    return "".join(body) or '<tr><td colspan="6" class="empty">No source health rows found.</td></tr>'


DECISION_UI_FIELDS = [
    "decision_draft_id",
    "source_intake_id",
    "preview_path",
    "qa_status",
    "automated_hold_count",
    "allowed_decisions",
    "operator_decision",
    "operator_notes",
    "hold_reason",
    "revision_request",
    "operator_name",
    "reviewed_at_local",
    "required_evidence",
    "copy_target",
    "copy_instructions",
    "copy_status",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

ATHLETE_PHOTO_DECISION_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "source_headshot_path",
    "contact_sheet_path",
    "recommended_review_variant_path",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "crop_choice",
    "operator_notes",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

IDENTITY_RESOLUTION_FIELDS = [
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


def render_decision_shortcuts(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        if row.get("exists"):
            action = f'<a class="tool-link" href="{html.escape(clean(row.get("href")))}">Open</a>'
            state = pill("found", "good")
        else:
            action = '<span class="muted">Missing</span>'
            state = pill("missing", "warn")
        body.append(
            f"""
            <article class="decision-link-card">
              <div>
                <strong>{html.escape(clean(row.get('label')))}</strong>
                <p>{html.escape(clean(row.get('purpose')))}</p>
                <code>{html.escape(clean(row.get('path')))}</code>
              </div>
              <div>{state}{action}</div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No linked decision files found.</p>'


def render_decision_history(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        cue = clean(row.get("cue")) or "verify"
        tone = {"replace": "bad", "revise": "warn", "hold": "bad", "verify": "neutral"}.get(cue, "neutral")
        body.append(
            f"""
            <tr>
              <td>{html.escape(str(row.get('row_number') or '-'))}</td>
              <td>{pill(clean(row.get('row_status')) or 'review', tone)}</td>
              <td>{html.escape(clean(row.get('operator_decision')))}</td>
              <td>{html.escape(clean(row.get('operator_name')))}</td>
              <td>{html.escape(clean(row.get('reviewed_at_local')))}</td>
              <td>{html.escape(clean(row.get('validation_status')))}</td>
              <td>{html.escape(short(clean(row.get('validation_issue')), 180))}</td>
              <td>{html.escape(short(clean(row.get('next_step')), 180))}</td>
            </tr>
            """
        )
    if not body:
        return '<p class="empty">No local inbox decision rows yet.</p>'
    return f"""
      <div class="table-wrap decision-history-table">
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Cue</th>
              <th>Decision</th>
              <th>Operator</th>
              <th>Reviewed</th>
              <th>Validation</th>
              <th>Issue</th>
              <th>Next</th>
            </tr>
          </thead>
          <tbody>{''.join(body)}</tbody>
        </table>
      </div>
    """


def render_decision_render_gallery(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        exists = bool(row.get("exists"))
        cue_rows = row.get("cue_rows") if isinstance(row.get("cue_rows"), list) else []
        cue_html = []
        for cue in cue_rows:
            if not isinstance(cue, dict):
                continue
            cue_html.append(
                f"""
                <div class="render-cue render-cue-{html.escape(clean(cue.get('tone')) or 'neutral')}">
                  <span>{html.escape(clean(cue.get('label')))}</span>
                  <strong>{html.escape(clean(cue.get('summary')))}</strong>
                  <p>{html.escape(short(clean(cue.get('detail')), 110))}</p>
                </div>
                """
            )
        preview = (
            f'<a href="{html.escape(clean(row.get("href")))}"><img src="{html.escape(clean(row.get("href")))}" alt="{html.escape(clean(row.get("label")))} render draft"></a>'
            if exists
            else '<div class="render-gallery-missing">Missing render</div>'
        )
        reference_exists = clean(row.get("reference_mockup_exists")) == "true" and clean(row.get("reference_mockup_href"))
        public_exists = clean(row.get("reference_public_exists")) == "true" and clean(row.get("reference_public_href"))
        layout_exists = clean(row.get("reference_layout_exists")) == "true" and clean(row.get("reference_layout_href"))
        public_preview = (
            f'<a href="{html.escape(clean(row.get("reference_public_href")))}"><img src="{html.escape(clean(row.get("reference_public_href")))}" alt="{html.escape(clean(row.get("label")))} public mockup"></a>'
            if public_exists
            else '<div class="render-gallery-missing">Public mockup missing</div>'
        )
        layout_preview = (
            f'<a href="{html.escape(clean(row.get("reference_layout_href")))}"><img src="{html.escape(clean(row.get("reference_layout_href")))}" alt="{html.escape(clean(row.get("label")))} layout reference"></a>'
            if layout_exists
            else '<div class="render-gallery-missing">Layout reference missing</div>'
        )
        action = (
            f'<a class="tool-link" href="{html.escape(clean(row.get("href")))}">Open</a>'
            if exists
            else '<span class="muted">Run render mode</span>'
        )
        reference_action = (
            f'<a class="tool-link" href="{html.escape(clean(row.get("reference_mockup_href")))}">Open ref</a>'
            if reference_exists
            else '<span class="muted">Reference missing</span>'
        )
        body.append(
            f"""
            <article class="render-gallery-card">
              <div class="render-comparison-grid">
                <div>
                  <span>Draft</span>
                  <div class="render-gallery-frame {html.escape(clean(row.get('format_id')))}">{preview}</div>
                </div>
                <div>
                  <span>{html.escape(clean(row.get('reference_public_label')) or 'Public mockup')}</span>
                  <div class="render-gallery-frame render-reference-frame {html.escape(clean(row.get('format_id')))}">{public_preview}</div>
                </div>
                <div>
                  <span>{html.escape(clean(row.get('reference_layout_label')) or 'Layout reference')}</span>
                  <div class="render-gallery-frame render-reference-frame {html.escape(clean(row.get('format_id')))}">{layout_preview}</div>
                </div>
              </div>
              <div class="render-gallery-meta">
                <div>
                  <strong>{html.escape(clean(row.get('label')))}</strong>
                  <p>{html.escape(clean(row.get('fit_note')))}</p>
                </div>
                <div class="render-gallery-actions">{action}{reference_action}</div>
              </div>
              <div class="render-gallery-facts">
                {pill(clean(row.get('review_status')) or 'review')}
                {pill(clean(row.get('shape')))}
                {pill('reference exact: ' + (clean(row.get('reference_exact_format_match')) or 'false'))}
                {pill('mode: ' + (clean(row.get('visual_mode')) or 'n/a'), 'good' if clean(row.get('visual_mode')).startswith('photo_first') else 'neutral')}
                {pill('photo layout: ' + (clean(row.get('photo_layout_mode')) or 'n/a'), 'good' if clean(row.get('photo_layout_status')) in {'approved_photo_premium_layout', 'approved_photo_first_template', 'approved_photo_first_square_template', 'approved_photo_compact_layout'} else 'neutral')}
                {pill('focal: ' + (clean(row.get('focal_entity_type')) or 'n/a'), 'good' if clean(row.get('focal_entity_type')) == 'athlete' else 'neutral')}
                {pill(clean(row.get('visual_delta_summary')) or 'Delta: not scored', clean(row.get('visual_delta_tone')) or 'warn')}
                {pill(clean(row.get('revision_summary')) or 'Revision: not planned', clean(row.get('revision_tone')) or 'warn')}
                {pill('publish ready: false')}
              </div>
              <div class="render-cue-grid">{''.join(cue_html)}</div>
              <p class="render-gallery-note">{html.escape(clean(row.get('reference_note')))}</p>
              <p class="render-gallery-note">Photo layout: {html.escape(clean(row.get('photo_layout_detail')) or 'No photo layout cue found.')}</p>
              <p class="render-gallery-note">{html.escape(clean(row.get('reference_public_detail')))} {html.escape(clean(row.get('reference_layout_detail')))}</p>
              <p class="render-gallery-note">{html.escape(clean(row.get('revision_focus')))}: {html.escape(short(clean(row.get('revision_manual_revisions')), 190))}</p>
              <p class="render-gallery-note">{html.escape(clean(row.get('qa_summary')))}. {html.escape(short(clean(row.get('asset_note')), 150))}</p>
              <code>{html.escape(clean(row.get('path')))}</code>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No render draft formats found yet.</p>'


def render_visual_qa_cues(rows: Iterable[Dict[str, str]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <article class="qa-cue-card">
              <div>
                <strong>{html.escape(clean(row.get('label')))}</strong>
                <p>{html.escape(clean(row.get('evidence')))}</p>
              </div>
              {pill(clean(row.get('result')) or 'review', clean(row.get('tone')) or 'neutral')}
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No visual QA cues found yet. Open the QA report from the file links.</p>'


def render_visual_delta_cues(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        score = clean(row.get("visual_delta_score")) or "not scored"
        band = clean(row.get("visual_delta_band")) or "not_scored"
        focus = clean(row.get("revision_focus")) or clean(row.get("worst_zone")) or "Manual review"
        summary = clean(row.get("visual_delta_summary")) or band
        detail = clean(row.get("revision_manual_revisions")) or clean(row.get("revision_status")) or clean(row.get("visual_delta_status"))
        tone = clean(row.get("visual_delta_tone")) or clean(row.get("revision_tone")) or "warn"
        body.append(
            f"""
            <article class="delta-cue-card delta-cue-{html.escape(tone)}">
              <div>
                <span>{html.escape(clean(row.get('label')) or 'Format')}</span>
                <strong>{html.escape(score)}</strong>
              </div>
              <div>
                <b>{html.escape(summary)}</b>
                <p>{html.escape(focus)}: {html.escape(short(detail, 150))}</p>
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No visual delta cues found yet.</p>'


def render_operator_decision_panel(panel: Dict[str, Any]) -> str:
    draft = panel.get("decision_draft", {}) if isinstance(panel.get("decision_draft"), dict) else {}
    draft_json = html.escape(json.dumps(draft), quote=True)
    fields_json = html.escape(json.dumps(DECISION_UI_FIELDS), quote=True)
    has_valid_decision = "true" if panel.get("has_valid_decision") else "false"
    preview = clean(panel.get("preview_src"))
    preview_html = (
        f'<img class="decision-preview-img" src="{html.escape(preview)}" alt="Draft preview for manual visual QA decision">'
        if preview
        else '<div class="decision-preview-missing">Preview missing</div>'
    )
    choices = panel.get("template_choices", [])
    if not choices:
        choices = [
            {"decision": "hold", "row_type": "hold", "copy_status": "copy_safe"},
            {"decision": "revise", "row_type": "revise", "copy_status": "copy_safe"},
            {"decision": "approve_for_manual_next_step", "row_type": "approve", "copy_status": "copy_safe"},
        ]
    decision_order = {"hold": 0, "revise": 1, "approve_for_manual_next_step": 2}
    choices = sorted(choices, key=lambda choice: decision_order.get(clean(choice.get("decision")), 99))
    choice_html = []
    for choice in choices:
        decision = clean(choice.get("decision"))
        if decision not in {"approve_for_manual_next_step", "hold", "revise"}:
            continue
        label = {
            "approve_for_manual_next_step": "Approve for manual next step only",
            "hold": "Hold",
            "revise": "Revise",
        }[decision]
        choice_html.append(
            f"""
            <label class="decision-option">
              <input type="radio" name="operatorDecision" value="{html.escape(decision)}" {'checked' if decision == 'hold' else ''}>
              <span>{html.escape(label)}</span>
            </label>
            """
        )
    inbox_command = command_hint(".\\hsd.cmd run -Mode decision-inbox") if not panel.get("inbox_exists") else ""
    render_command = command_hint(".\\hsd.cmd run -Mode render")
    return f"""
      <div class="decision-ui" data-decision-draft="{draft_json}" data-decision-fields="{fields_json}" data-has-valid-decision="{has_valid_decision}">
        <div class="decision-preview-column">
          <div class="decision-preview-header">
            <div>
              <span class="row-kicker">Primary draft preview</span>
              <strong>Inspect the image first</strong>
            </div>
            {pill('not approved', 'warn')}
          </div>
          <div class="decision-preview">
            {preview_html}
          </div>
          <div class="decision-preview-footer">
            {pill('review-only draft')}
            {pill('manual decision required', 'warn')}
            {pill('publish-ready: false')}
          </div>
        </div>
        <div class="decision-workbench">
          <div class="decision-cockpit-card">
            <div class="decision-cockpit-head">
              <div>
                <span class="row-kicker">Decision cockpit</span>
                <strong>{html.escape(clean(panel.get('panel_status')) or 'not_ready')}</strong>
                <p>{html.escape(clean(panel.get('validation_issue')) or clean(panel.get('next_step')) or 'Manual review required.')}</p>
              </div>
              <div class="decision-cockpit-actions">
                {pill(panel.get('qa_status') or 'not_ready')}
                {pill(panel.get('validation_status') or panel.get('intake_status') or 'awaiting')}
              </div>
            </div>
            <div class="decision-status-grid">
              <div><span>QA checks</span><strong>{html.escape(clean(panel.get('qa_pass_count')) or '0')}/{html.escape(clean(panel.get('qa_check_count')) or '0')}</strong></div>
              <div><span>Automated holds</span><strong>{html.escape(clean(panel.get('automated_hold_count')) or '0')}</strong></div>
              <div><span>Inbox rows</span><strong>{html.escape(str(panel.get('inbox_rows', 0)))}</strong></div>
              <div><span>Approval state</span>{pill(panel.get('approval_status') or 'not_approved')}</div>
            </div>
            <div class="review-flow">
              <div><span>1</span><strong>Inspect render</strong><p>Open the draft and compare reference drift.</p></div>
              <div><span>2</span><strong>Check evidence</strong><p>Review QA cues, source proof, and logo readiness.</p></div>
              <div><span>3</span><strong>Record decision</strong><p>Use hold, revise, or approve for manual next step only without moving files.</p></div>
            </div>
            <small>{html.escape(clean(panel.get('next_step')))}</small>
          </div>
          <div class="decision-signal-grid">
            <div class="decision-desk-section">
              <div class="row-kicker">Visual QA cues {pill((clean(panel.get('qa_pass_count')) or '0') + '/' + (clean(panel.get('qa_check_count')) or '0') + ' passed', 'good' if clean(panel.get('automated_hold_count')) == '0' else 'warn')} {pill('manual review still required')}</div>
              <div class="qa-cue-grid">
                {render_visual_qa_cues(panel.get('qa_cues', []))}
              </div>
            </div>
            <div class="decision-desk-section">
              <div class="row-kicker">Visual delta warnings {pill('compare by eye')}</div>
              <div class="delta-cue-grid">
                {render_visual_delta_cues(panel.get('render_gallery', []))}
              </div>
            </div>
          </div>
          <div class="decision-desk-section">
            <div class="row-kicker">Render gallery {pill('review-only drafts')} {pill('no publish-ready lane')}</div>
            <div class="render-gallery-grid">
              {render_decision_render_gallery(panel.get('render_gallery', []))}
            </div>
          </div>
          <div class="decision-desk-section">
            <div class="row-kicker">Open before deciding</div>
            <div class="decision-link-grid">
              {render_decision_shortcuts(panel.get('file_shortcuts', []))}
            </div>
          </div>
          <div class="decision-action-card">
            <div class="row-kicker">Manual decision controls <span id="decisionReadyBadge" class="pill warn">Optional</span></div>
            <ul id="decisionFieldWarnings" class="decision-warning-list"></ul>
            <form class="decision-form">
              <fieldset class="decision-options">
                <legend>Hold, revise, or approve for manual next step only</legend>
                {''.join(choice_html)}
              </fieldset>
              <label>Operator notes<textarea id="operatorNotes" rows="3" required placeholder="What did you verify by eye?"></textarea></label>
              <div class="decision-form-grid">
                <label>Hold reason<input id="holdReason" type="text" placeholder="Required for hold"></label>
                <label>Revision request<input id="revisionRequest" type="text" placeholder="Required for revise"></label>
              </div>
              <div class="decision-form-grid">
                <label>Operator name<input id="operatorName" type="text" required placeholder="Your name"></label>
                <label>Reviewed at<input id="reviewedAtLocal" type="text" required></label>
              </div>
            </form>
            <div class="decision-copy-box">
              <div class="row-kicker">Copy-safe CSV row</div>
              <textarea id="decisionCsvOutput" rows="5" readonly></textarea>
              <div class="decision-button-row">
                <button class="tool-link" type="button" id="copyDecisionRow">Copy row</button>
                <span class="muted" id="decisionCopyStatus">Paste the copied row below the header in {html.escape(panel.get('inbox_path'))}. Do not paste the header row.</span>
              </div>
            </div>
          </div>
          <div class="decision-desk-section">
            <div class="row-kicker">Decision history {pill(str(panel.get('inbox_rows', 0)) + ' inbox row(s)')} {pill(str(panel.get('history_issue_count', 0)) + ' issue(s)', 'warn' if panel.get('history_issue_count') else 'good')}</div>
            {render_decision_history(panel.get('decision_history', []))}
          </div>
          <div class="safety-strip">
            {pill('file-backed manual approval', 'good')}
            {pill('auto-approval off')}
            {pill('publishing off')}
            {pill('no file movement')}
            {pill('paid APIs off', 'good')}
          </div>
          {inbox_command}
          {render_command}
        </div>
      </div>
    """


def asset_blocker_approval_pill(row: Dict[str, Any]) -> str:
    approval_status = clean(row.get("approval_status")) or "approval_review"
    review_fields = " ".join(
        clean(row.get(field))
        for field in (
            "finding",
            "asset_readiness",
            "renderer_coverage",
            "blocker_summary",
            "evidence",
            "recommended_next_step",
        )
    ).lower()
    needs_recheck = (
        approval_status.lower() == "approved"
        and (
            "review_only_manual_source_recheck_required" in review_fields
            or "suspicious_or_default_player_approval" in review_fields
            or "decision_source=default" in review_fields
            or "default_decision_source_manual_recheck_required" in review_fields
        )
    )
    if needs_recheck:
        return pill("approved marker needs recheck", "warn")
    return pill(approval_status)


def render_asset_blocker_cards(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        href = clean(row.get("open_href"))
        open_link_html = f'<a class="tool-link" href="{html.escape(href)}">Open</a>' if href else '<span class="muted">Missing report</span>'
        fallback_cue = clean(row.get("renderer_fallback_cue"))
        fallback_line = (
            f'<p class="muted"><strong>Fallback cue:</strong> {html.escape(short(fallback_cue, 190))}</p>'
            if fallback_cue
            else ""
        )
        body.append(
            f"""
            <article class="asset-blocker-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">{html.escape(clean(row.get('asset_domain')))} / {html.escape(clean(row.get('asset_kind')) or clean(row.get('entity_type')))}</span>
                  <strong>{html.escape(clean(row.get('entity_name')))}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill(clean(row.get('severity')) or 'review', status_tone(row.get('severity')))}
                  {pill(clean(row.get('decision')) or 'review', clean(row.get('tone')) or 'warn')}
                </div>
              </div>
              <p>{html.escape(short(clean(row.get('finding')).replace('_', ' '), 120))}</p>
              <div class="asset-guidance-grid">
                <div><span>Verify</span><strong>{html.escape(short(clean(row.get('manual_action')), 130))}</strong></div>
                <div><span>Hold</span><strong>{html.escape(short(clean(row.get('hold_cue')), 130))}</strong></div>
                <div><span>Revise</span><strong>{html.escape(short(clean(row.get('revise_cue')), 130))}</strong></div>
                <div><span>Packet</span><strong>{html.escape(short(clean(row.get('default_operator_decision')) or clean(row.get('decision_lane')) or 'manual_review_required', 130))}</strong></div>
              </div>
              <code>{html.escape(short(clean(row.get('asset_path')), 110))}</code>
              <p class="muted">{html.escape(short(clean(row.get('blocker_summary')) or clean(row.get('asset_readiness')), 190))}</p>
              <p class="muted">{html.escape(short(clean(row.get('evidence')), 190))}</p>
              {fallback_line}
              <div class="asset-blocker-actions">
                {open_link_html}
                {asset_blocker_approval_pill(row)}
                {pill(clean(row.get('format_status')) or 'format_review')}
                {pill(clean(row.get('renderer_coverage')) or 'renderer_review')}
                {pill(clean(row.get('asset_readiness')) or 'asset_review')}
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No asset blockers found in the latest audit.</p>'


def render_logo_review_packet_cards(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        title = clean(row.get("decision_packet_title")) or clean(row.get("packet_title")) or f"WNBA logo review: {clean(row.get('team_name')) or clean(row.get('team_id'))}"
        registered_path = clean(row.get("registered_path")) or clean(row.get("registered_logo_path")) or clean(row.get("local_logo_path")) or clean(row.get("recommended_path"))
        source_path = clean(row.get("source_target_path")) or clean(row.get("source_path")) or clean(row.get("target_path"))
        primary_action = clean(row.get("primary_action")) or clean(row.get("decision_primary_action"))
        hold_cue = clean(row.get("hold_cue")) or clean(row.get("decision_hold_cue"))
        revise_cue = clean(row.get("revise_cue")) or clean(row.get("decision_revise_cue"))
        body.append(
            f"""
            <article class="asset-blocker-card logo-packet-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">{html.escape(clean(row.get('issue_type')) or 'logo_review_required')} / {html.escape(clean(row.get('team_id')) or 'wnba')}</span>
                  <strong>{html.escape(title)}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill(clean(row.get('decision_review_status')) or 'operator_review')}
                  {pill('review-only')}
                </div>
              </div>
              <p>{html.escape(short(primary_action or 'Review logo source evidence before renderer trust.', 180))}</p>
              <p><strong>Path check:</strong> registered={html.escape(short(registered_path or 'missing', 90))} / source={html.escape(short(source_path or 'missing', 90))}</p>
              <div class="asset-guidance-grid">
                <div><span>Hold</span><strong>{html.escape(short(hold_cue or 'Hold logo slot until exact source and local file are reviewed.', 130))}</strong></div>
                <div><span>Revise</span><strong>{html.escape(short(revise_cue or 'Revise registry metadata only after manual evidence review.', 130))}</strong></div>
                <div><span>Fallback</span><strong>{html.escape(short(clean(row.get('renderer_fallback_cue')) or 'Renderer fallback remains review-only.', 130))}</strong></div>
                <div><span>Decisions</span><strong>{html.escape(short(clean(row.get('allowed_decisions')) or 'verify_logo_for_review_renders|hold_logo_slot|revise_logo_source_metadata', 130))}</strong></div>
              </div>
              <code>{html.escape(short(registered_path or 'registered path missing', 120))}</code>
              <p class="muted">{html.escape(short('source target: ' + (source_path or 'missing'), 180))}</p>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No focused logo review packets found. Run the WNBA asset registry validator.</p>'


def render_asset_readiness_panel(panel: Dict[str, Any]) -> str:
    policy = panel.get("policy") if isinstance(panel.get("policy"), dict) else {}
    status_t = "good" if clean(panel.get("panel_status")) in {"pass", "passed"} else "warn" if clean(panel.get("panel_status")) == "review_required" else "neutral"
    return f"""
      <div class="asset-readiness-desk">
        <div class="decision-cockpit-card asset-readiness-cockpit">
          <div class="decision-cockpit-head">
            <div>
              <span class="row-kicker">Asset readiness</span>
              <strong>{html.escape(clean(panel.get('panel_status')) or 'not_run')}</strong>
              <p>{html.escape(clean(panel.get('next_step')))}</p>
            </div>
            <div class="decision-cockpit-actions">
              {pill('asset-audit', status_t)}
              {pill('review-only')}
              {pill('publish-ready: false')}
            </div>
          </div>
          <div class="decision-status-grid">
            <div><span>Total findings</span><strong>{html.escape(str(panel.get('finding_count', 0)))}</strong></div>
            <div><span>Errors / warnings</span><strong>{html.escape(str(panel.get('error_count', 0)))}/{html.escape(str(panel.get('warning_count', 0)))}</strong></div>
            <div><span>Player-photo findings</span><strong>{html.escape(str(panel.get('player_photo_findings', 0)))}</strong></div>
            <div><span>Team logo findings</span><strong>{html.escape(str(panel.get('team_logo_findings', 0)))}</strong></div>
            <div><span>League mark findings</span><strong>{html.escape(str(panel.get('league_logo_findings', 0)))}</strong></div>
            <div><span>Renderer findings</span><strong>{html.escape(str(panel.get('renderer_findings', 0)))}</strong></div>
            <div><span>Default photo approvals</span><strong>{html.escape(str(panel.get('default_player_approval_findings', 0)))}</strong></div>
            <div><span>Missing player assets</span><strong>{html.escape(str(panel.get('missing_player_asset_findings', 0)))}</strong></div>
            <div><span>Logo review packets</span><strong>{html.escape(str(panel.get('logo_review_packet_rows', 0)))}</strong></div>
            <div><span>Logo sweep rows</span><strong>{html.escape(str(panel.get('logo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Soccer logo sweep rows</span><strong>{html.escape(str(panel.get('womens_soccer_logo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Soccer review steps</span><strong>{html.escape(str(panel.get('womens_soccer_logo_review_walkthrough_rows', 0)))}</strong></div>
            <div><span>Soccer athlete candidates</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Soccer roster rows</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_official_roster_candidate_rows', 0)))}</strong></div>
            <div><span>Soccer athlete boards</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_contact_sheet_team_boards', 0)))}</strong></div>
            <div><span>Soccer starter rows</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_starter_candidate_rows', 0)))}</strong></div>
            <div><span>Soccer local files</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_local_candidate_files_present', 0)))}</strong></div>
            <div><span>Soccer athlete warnings</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_contact_sheet_warning_count', 0)))}</strong></div>
            <div><span>Soccer operator board</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_operator_board_rows', 0)))}</strong></div>
            <div><span>Soccer download intake</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_download_intake_rows', 0)))}</strong></div>
            <div><span>Soccer download yes</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Soccer verify queue</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_verification_queue_rows', 0)))}</strong></div>
            <div><span>Soccer verify NWSL</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_verification_queue_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer verify Europe</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_verification_queue_europe_rows', 0)))}</strong></div>
            <div><span>Soccer verify P0</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_verification_queue_p0_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer verify local gaps</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_verification_queue_missing_local_candidate_rows', 0)))}</strong></div>
            <div><span>Soccer next actions</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_next_actions_rows', 0)))}</strong></div>
            <div><span>Soccer next-action yes</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_next_actions_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Soccer next-action blanks</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_next_actions_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Soccer source priority</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_source_priority_rows', 0)))}</strong></div>
            <div><span>Soccer source verify</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_source_priority_verify_rows', 0)))}</strong></div>
            <div><span>Soccer source gray</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_source_priority_gray_rows', 0)))}</strong></div>
            <div><span>Soccer triage rows</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_review_triage_rows', 0)))}</strong></div>
            <div><span>Soccer triage NWSL</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_review_triage_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer triage blanks</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_review_triage_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Soccer candidate actions</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_candidate_actions_rows', 0)))}</strong></div>
            <div><span>Soccer candidate NWSL</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_candidate_actions_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer candidate blanks</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_candidate_actions_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Soccer photo readiness</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_readiness_rows', 0)))}</strong></div>
            <div><span>Soccer photo NWSL</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_readiness_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer photo blanks</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_photo_readiness_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Soccer focus rows</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_operator_focus_rows', 0)))}</strong></div>
            <div><span>Soccer focus P0</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_operator_focus_p0_rows', 0)))}</strong></div>
            <div><span>Soccer focus identity</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_operator_focus_identity_manual_verification_rows', 0)))}</strong></div>
            <div><span>Soccer action-photo next</span><strong>{html.escape(str(panel.get('womens_soccer_action_photo_research_next_rows', 0)))}</strong></div>
            <div><span>Soccer AP source blanks</span><strong>{html.escape(str(panel.get('womens_soccer_action_photo_research_next_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Soccer AP dl yes</span><strong>{html.escape(str(panel.get('womens_soccer_action_photo_research_next_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Soccer AP ready</span><strong>{html.escape(str(panel.get('womens_soccer_action_photo_research_next_candidate_ready_rows', 0)))}</strong></div>
            <div><span>Soccer closure rows</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_closure_rows', 0)))}</strong></div>
            <div><span>Soccer closure refs</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_closure_total_referenced_rows', 0)))}</strong></div>
            <div><span>Soccer closure dl yes</span><strong>{html.escape(str(panel.get('womens_soccer_athlete_closure_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Soccer research rows</span><strong>{html.escape(str(panel.get('womens_soccer_external_research_rows', 0)))}</strong></div>
            <div><span>Soccer research NWSL</span><strong>{html.escape(str(panel.get('womens_soccer_external_research_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer research Europe</span><strong>{html.escape(str(panel.get('womens_soccer_external_research_europe_rows', 0)))}</strong></div>
            <div><span>Soccer research P0</span><strong>{html.escape(str(panel.get('womens_soccer_external_research_p0_nwsl_rows', 0)))}</strong></div>
            <div><span>Soccer gray-area leads</span><strong>{html.escape(str(panel.get('womens_soccer_external_research_gray_area_rows', 0)))}</strong></div>
            <div><span>Action-photo intake</span><strong>{html.escape(str(panel.get('action_photo_candidate_intake_rows', 0)))}</strong></div>
            <div><span>Source-map board</span><strong>{html.escape(str(panel.get('action_photo_source_map_board_rows', 0)))}</strong></div>
            <div><span>Source-map blanks</span><strong>{html.escape(str(panel.get('action_photo_source_map_board_blank_operator_decision_rows', 0)))}</strong></div>
            <div><span>Source-map dl yes</span><strong>{html.escape(str(panel.get('action_photo_source_map_board_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Source-map fetch/approve</span><strong>{html.escape(str(panel.get('action_photo_source_map_board_source_fetching', False)).lower())}/{html.escape(str(panel.get('action_photo_source_map_board_auto_approval', False)).lower())}</strong></div>
            <div><span>Source-hunt rows</span><strong>{html.escape(str(panel.get('action_photo_manual_source_hunt_rows', 0)))}</strong></div>
            <div><span>Source-hunt blanks</span><strong>{html.escape(str(panel.get('action_photo_manual_source_hunt_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Source-hunt dl yes</span><strong>{html.escape(str(panel.get('action_photo_manual_source_hunt_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Source-hunt fetch</span><strong>{html.escape(str(panel.get('action_photo_manual_source_hunt_source_fetching', False)).lower())}</strong></div>
            <div><span>Action-photo worksheet</span><strong>{html.escape(str(panel.get('action_photo_operator_worksheet_rows', 0)))}</strong></div>
            <div><span>Worksheet URL blanks</span><strong>{html.escape(str(panel.get('action_photo_operator_worksheet_blank_candidate_url_rows', 0)))}</strong></div>
            <div><span>Worksheet reviewer blanks</span><strong>{html.escape(str(panel.get('action_photo_operator_worksheet_blank_reviewer_decision_rows', 0)))}</strong></div>
            <div><span>Worksheet dl yes</span><strong>{html.escape(str(panel.get('action_photo_operator_worksheet_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Worksheet writes</span><strong>{html.escape(str(panel.get('action_photo_operator_worksheet_asset_downloads', False)).lower())}/{html.escape(str(panel.get('action_photo_operator_worksheet_headshot_writes', False)).lower())}/{html.escape(str(panel.get('action_photo_operator_worksheet_approved_marker_writes', False)).lower())}</strong></div>
            <div><span>Action-photo research</span><strong>{html.escape(str(panel.get('action_photo_research_packet_rows', 0)))}</strong></div>
            <div><span>Research returns pasted</span><strong>{html.escape(str(panel.get('action_photo_research_return_rows_with_pasted_data', 0)))}</strong></div>
            <div><span>Return URL blanks</span><strong>{html.escape(str(panel.get('action_photo_research_return_blank_candidate_photo_url_rows', 0)))}</strong></div>
            <div><span>Return source blanks</span><strong>{html.escape(str(panel.get('action_photo_research_return_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Return rights blanks</span><strong>{html.escape(str(panel.get('action_photo_research_return_blank_rights_class_rows', 0)))}</strong></div>
            <div><span>Return dl yes</span><strong>{html.escape(str(panel.get('action_photo_research_return_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Paste worksheet rows</span><strong>{html.escape(str(panel.get('action_photo_research_return_paste_worksheet_rows', 0)))}</strong></div>
            <div><span>Paste ready review</span><strong>{html.escape(str(panel.get('action_photo_research_return_paste_worksheet_ready_rows', 0)))}</strong></div>
            <div><span>Paste missing src</span><strong>{html.escape(str(panel.get('action_photo_research_return_paste_worksheet_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Action-photo bundle</span><strong>{html.escape(str(panel.get('action_photo_research_run_bundle_rows', 0)))}</strong></div>
            <div><span>Action-photo preflight</span><strong>{html.escape(str(panel.get('action_photo_quarantine_preflight_rows', 0)))}</strong></div>
            <div><span>Action-photo ready dl</span><strong>{html.escape(str(panel.get('action_photo_quarantine_preflight_ready_for_human_download_decision_rows', 0)))}</strong></div>
            <div><span>Action-photo dl yes</span><strong>{html.escape(str(panel.get('action_photo_quarantine_preflight_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>Quality/fit rows</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_rows', 0)))}</strong></div>
            <div><span>Quality source yes</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_source_url_present_rows', 0)))}</strong></div>
            <div><span>Quality ready dl</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_ready_for_human_download_decision_rows', 0)))}</strong></div>
            <div><span>Quality writes</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_asset_downloads', False)).lower())}/{html.escape(str(panel.get('action_photo_quality_fit_headshot_writes', False)).lower())}/{html.escape(str(panel.get('action_photo_quality_fit_approved_marker_writes', False)).lower())}</strong></div>
            <div><span>Operator cue rows</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_operator_cue_rows', 0)))}</strong></div>
            <div><span>Cue missing src</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_operator_cue_source_url_missing_rows', 0)))}</strong></div>
            <div><span>Cue missing identity</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_operator_cue_identity_metadata_missing_rows', 0)))}</strong></div>
            <div><span>Cue eligible review</span><strong>{html.escape(str(panel.get('action_photo_quality_fit_operator_cue_eligible_rows', 0)))}</strong></div>
            <div><span>Decision queue</span><strong>{html.escape(str(panel.get('action_photo_download_decision_rows', 0)))}</strong></div>
            <div><span>Decision ready</span><strong>{html.escape(str(panel.get('action_photo_download_decision_ready_rows', 0)))}</strong></div>
            <div><span>Decision dl yes</span><strong>{html.escape(str(panel.get('action_photo_download_decision_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>WNBA hero targets</span><strong>{html.escape(str(panel.get('action_photo_hero_targets_rows', 0)))}</strong></div>
            <div><span>Hero target blanks</span><strong>{html.escape(str(panel.get('action_photo_hero_targets_blank_source_url_rows', 0)))}</strong></div>
            <div><span>Cutout worksheet</span><strong>{html.escape(str(panel.get('action_photo_cutout_readiness_rows', 0)))}</strong></div>
            <div><span>Cutout blanks</span><strong>{html.escape(str(panel.get('action_photo_cutout_readiness_blank_cutout_work_required_rows', 0)))}</strong></div>
            <div><span>Cutout writes</span><strong>{html.escape(str(panel.get('action_photo_cutout_readiness_cutout_file_writes', False)).lower())}</strong></div>
            <div><span>H/S coverage rows</span><strong>{html.escape(str(panel.get('hockey_softball_foundation_coverage_rows', 0)))}</strong></div>
            <div><span>H/S source rows</span><strong>{html.escape(str(panel.get('hockey_softball_foundation_coverage_source_rows', 0)))}</strong></div>
            <div><span>Hockey logo rows</span><strong>{html.escape(str(panel.get('womens_hockey_logo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Hockey athlete candidates</span><strong>{html.escape(str(panel.get('womens_hockey_athlete_photo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Hockey source slots</span><strong>{html.escape(str(panel.get('womens_hockey_athlete_photo_source_review_slot_rows', 0)))}</strong></div>
            <div><span>Hockey walkthrough rows</span><strong>{html.escape(str(panel.get('womens_hockey_review_walkthrough_rows', 0)))}</strong></div>
            <div><span>Hockey workflow rows</span><strong>{html.escape(str(panel.get('womens_hockey_asset_workflow_rows', 0)))}</strong></div>
            <div><span>Softball logo rows</span><strong>{html.escape(str(panel.get('softball_logo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Softball athlete candidates</span><strong>{html.escape(str(panel.get('softball_athlete_photo_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Softball source slots</span><strong>{html.escape(str(panel.get('softball_athlete_photo_source_review_slot_rows', 0)))}</strong></div>
            <div><span>Softball walkthrough rows</span><strong>{html.escape(str(panel.get('softball_review_walkthrough_rows', 0)))}</strong></div>
            <div><span>Softball workflow rows</span><strong>{html.escape(str(panel.get('softball_asset_workflow_rows', 0)))}</strong></div>
            <div><span>H/S action queue</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_action_queue_rows', 0)))}</strong></div>
            <div><span>H/S source-only</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_action_queue_source_candidate_only_rows', 0)))}</strong></div>
            <div><span>H/S local assets</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_action_queue_local_asset_present_rows', 0)))}</strong></div>
            <div><span>H/S batch helper</span><strong>{html.escape(str(panel.get('hockey_softball_batch_source_review_rows', 0)))}</strong></div>
            <div><span>H/S review now</span><strong>{html.escape(str(panel.get('hockey_softball_batch_source_review_now_rows', 0)))}</strong></div>
            <div><span>H/S next 10</span><strong>{html.escape(str(panel.get('hockey_softball_batch_source_review_next_rows', 0)))}</strong></div>
            <div><span>H/S worksheet</span><strong>{html.escape(str(panel.get('hockey_softball_next_decision_worksheet_rows', 0)))}</strong></div>
            <div><span>H/S worksheet logos</span><strong>{html.escape(str(panel.get('hockey_softball_next_decision_worksheet_logo_rows', 0)))}</strong></div>
            <div><span>H/S worksheet athletes</span><strong>{html.escape(str(panel.get('hockey_softball_next_decision_worksheet_athlete_rows', 0)))}</strong></div>
            <div><span>H/S worksheet missing local</span><strong>{html.escape(str(panel.get('hockey_softball_next_decision_worksheet_missing_local_rows', 0)))}</strong></div>
            <div><span>H/S worksheet dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_next_decision_worksheet_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S worksheet blank dl fields</span><strong>{html.escape(str(panel.get('hockey_softball_next_decision_worksheet_blank_download_metadata_rows', 0)))}</strong></div>
            <div><span>H/S source priority</span><strong>{html.escape(str(panel.get('hockey_softball_source_priority_rows', 0)))}</strong></div>
            <div><span>H/S source verify</span><strong>{html.escape(str(panel.get('hockey_softball_source_priority_operator_verify_rows', 0)))}</strong></div>
            <div><span>H/S source dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_source_priority_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S source checklist</span><strong>{html.escape(str(panel.get('hockey_softball_source_verification_rows', 0)))}</strong></div>
            <div><span>H/S checklist blanks</span><strong>{html.escape(str(panel.get('hockey_softball_source_verification_blank_source_url_rows', 0)))}</strong></div>
            <div><span>H/S intake groups</span><strong>{html.escape(str(panel.get('hockey_softball_intake_readiness_groups', 0)))}</strong></div>
            <div><span>H/S intake rows</span><strong>{html.escape(str(panel.get('hockey_softball_intake_readiness_rows_covered', 0)))}</strong></div>
            <div><span>H/S intake unsafe</span><strong>{html.escape(str(panel.get('hockey_softball_intake_readiness_unsafe_guardrail_rows', 0)))}</strong></div>
            <div><span>H/S source map</span><strong>{html.escape(str(panel.get('hockey_softball_source_map_rows', 0)))}</strong></div>
            <div><span>H/S source map official</span><strong>{html.escape(str(panel.get('hockey_softball_source_map_official_free_public_rows', 0)))}</strong></div>
            <div><span>H/S source map dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_source_map_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S AP handoff</span><strong>{html.escape(str(panel.get('hockey_softball_action_photo_handoff_rows', 0)))}</strong></div>
            <div><span>H/S AP ready</span><strong>{html.escape(str(panel.get('hockey_softball_action_photo_handoff_ready_rows', 0)))}</strong></div>
            <div><span>H/S AP dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_action_photo_handoff_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S research return</span><strong>{html.escape(str(panel.get('hockey_softball_source_research_return_rows', 0)))}</strong></div>
            <div><span>H/S return dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_source_research_return_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S triage rows</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_triage_rows', 0)))}</strong></div>
            <div><span>H/S triage verify src</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_triage_operator_verify_source_rows', 0)))}</strong></div>
            <div><span>H/S triage dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_triage_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S readiness rows</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_readiness_rows', 0)))}</strong></div>
            <div><span>H/S readiness blanks</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_readiness_blank_source_url_rows', 0)))}</strong></div>
            <div><span>H/S readiness gaps</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_readiness_source_identity_gap_rows', 0)))}</strong></div>
            <div><span>H/S local gaps</span><strong>{html.escape(str(panel.get('hockey_softball_asset_review_readiness_local_candidate_gap_rows', 0)))}</strong></div>
            <div><span>H/S focus P0</span><strong>{html.escape(str(panel.get('hockey_softball_manual_verification_focus_p0_rows', 0)))}</strong></div>
            <div><span>H/S focus P1</span><strong>{html.escape(str(panel.get('hockey_softball_manual_verification_focus_p1_rows', 0)))}</strong></div>
            <div><span>H/S focus dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_manual_verification_focus_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S action cards</span><strong>{html.escape(str(panel.get('hockey_softball_asset_next_action_cards_rows', 0)))}</strong></div>
            <div><span>H/S card blanks</span><strong>{html.escape(str(panel.get('hockey_softball_asset_next_action_cards_blank_source_url_rows', 0)))}</strong></div>
            <div><span>H/S card dl yes</span><strong>{html.escape(str(panel.get('hockey_softball_asset_next_action_cards_download_approved_yes_rows', 0)))}</strong></div>
            <div><span>H/S download gate</span><strong>{html.escape(str(panel.get('hockey_softball_quarantine_download_intake_rows', 0)))}</strong></div>
            <div><span>H/S download yes</span><strong>{html.escape(str(panel.get('hockey_softball_quarantine_download_approved_yes_rows', 0)))}</strong></div>
          </div>
          {packet_freshness_html(panel, 'logo_review_packet', 'Logo review')}
          {packet_freshness_html(panel, 'logo_contact_sheet', 'Logo contact sheet')}
          {packet_freshness_html(panel, 'womens_soccer_logo_contact_sheet', "Women's soccer logo contact sheet")}
          {packet_freshness_html(panel, 'womens_soccer_logo_review_walkthrough', "Women's soccer logo review walkthrough")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_photo_contact_sheet', "Women's soccer athlete photo contact sheets")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_operator_board', "Women's soccer athlete operator board")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_download_intake', "Women's soccer athlete photo download intake")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_verification_queue', "Women's soccer athlete verification queue")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_next_actions', "Women's soccer athlete verification next actions")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_source_priority', "Women's soccer athlete source priority")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_review_triage', "Women's soccer athlete review triage")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_candidate_actions', "Women's soccer athlete candidate next-action board")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_photo_readiness', "Women's soccer athlete photo review readiness board")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_operator_focus', "Women's soccer athlete operator focus")}
          {packet_freshness_html(panel, 'womens_soccer_action_photo_research_next', "Women's soccer action-photo research next")}
          {packet_freshness_html(panel, 'womens_soccer_athlete_closure', "Women's soccer athlete expansion closure summary")}
          {packet_freshness_html(panel, 'womens_soccer_external_research', "Women's soccer external research intake")}
          {packet_freshness_html(panel, 'action_photo_research_run_bundle', "Action-photo research run bundle")}
          {packet_freshness_html(panel, 'action_photo_research_return_paste_worksheet', "Action-photo research return paste worksheet")}
          {packet_freshness_html(panel, 'action_photo_manual_source_hunt', "Action-photo manual source-hunt board")}
          {packet_freshness_html(panel, 'action_photo_quarantine_preflight', "Action-photo quarantine preflight")}
          {packet_freshness_html(panel, 'action_photo_quality_fit', "Action-photo candidate quality/fit board")}
          {packet_freshness_html(panel, 'action_photo_quality_fit_operator_cue', "Action-photo quality/fit operator cue")}
          {packet_freshness_html(panel, 'action_photo_hero_targets', "WNBA hero action-photo targets")}
          {packet_freshness_html(panel, 'action_photo_cutout_readiness', "Action-photo cutout readiness")}
          {packet_freshness_html(panel, 'hockey_softball_asset_foundation', "Hockey/softball asset foundation")}
          {packet_freshness_html(panel, 'hockey_softball_foundation_coverage', "Hockey/softball foundation coverage index")}
          {packet_freshness_html(panel, 'hockey_softball_source_review_helper', "Hockey/softball source review helper")}
          {packet_freshness_html(panel, 'hockey_softball_asset_workflow', "Hockey/softball asset workflow readiness")}
          {packet_freshness_html(panel, 'hockey_softball_asset_review_action_queue', "Hockey/softball asset review action queue")}
          {packet_freshness_html(panel, 'hockey_softball_batch_source_review', "Hockey/softball batch source review helper")}
          {packet_freshness_html(panel, 'hockey_softball_next_decision_worksheet', "Hockey/softball next decision worksheet")}
          {packet_freshness_html(panel, 'hockey_softball_source_priority', "Hockey/softball source priority worksheet")}
          {packet_freshness_html(panel, 'hockey_softball_source_verification', "Hockey/softball source verification checklist")}
          {packet_freshness_html(panel, 'hockey_softball_intake_readiness', "Hockey/softball intake readiness summary")}
          {packet_freshness_html(panel, 'hockey_softball_source_map', "Hockey/softball source map board")}
          {packet_freshness_html(panel, 'hockey_softball_action_photo_handoff', "Hockey/softball action-photo research handoff")}
          {packet_freshness_html(panel, 'hockey_softball_source_research_return', "Hockey/softball source research return intake")}
          {packet_freshness_html(panel, 'hockey_softball_asset_review_triage', "Hockey/softball asset review triage")}
          {packet_freshness_html(panel, 'hockey_softball_asset_review_readiness', "Hockey/softball asset review readiness board")}
          {packet_freshness_html(panel, 'hockey_softball_manual_verification_focus', "Hockey/softball manual verification focus")}
          {packet_freshness_html(panel, 'hockey_softball_asset_next_action_cards', "Hockey/softball asset next-action cards")}
          {packet_freshness_html(panel, 'hockey_softball_quarantine_download_intake', "Hockey/softball quarantine download intake")}
          <div class="review-flow">
            <div><span>1</span><strong>Verify</strong><p>Open the linked audit/catalog row and compare source evidence manually.</p></div>
            <div><span>2</span><strong>Hold</strong><p>Keep assets out of render trust when source, identity, approval, or format evidence is incomplete.</p></div>
            <div><span>3</span><strong>Revise</strong><p>Use review-only asset workflows to fix source metadata or local asset slots.</p></div>
          </div>
        </div>
        <div class="decision-desk-section">
          <div class="row-kicker">Highest-risk asset blockers {pill(str(len(panel.get('top_findings', []))) + ' shown')} {pill('manual guidance only')}</div>
          <div class="asset-blocker-grid">
            {render_asset_blocker_cards(panel.get('top_findings', []))}
          </div>
        </div>
        <div class="decision-desk-section">
          <div class="row-kicker">Focused logo review packets {pill(str(len(panel.get('logo_review_packets', []))) + ' shown')} {pill(str(panel.get('logo_review_packet_unapproved_rows', 0)) + ' unapproved')} {pill(str(panel.get('logo_review_packet_source_drift_rows', 0)) + ' source drift')}</div>
          <div class="asset-blocker-grid">
            {render_logo_review_packet_cards(panel.get('logo_review_packets', []))}
          </div>
        </div>
        <div class="decision-desk-section">
          <div class="row-kicker">Asset review files {pill('open before render trust')}</div>
          <div class="decision-link-grid">
            {render_decision_shortcuts(panel.get('file_shortcuts', []))}
          </div>
        </div>
        <div class="safety-strip">
          {pill('paid APIs off', 'good' if policy.get('no_paid_apis', True) else 'bad')}
          {pill('asset downloads off', 'good' if policy.get('no_asset_downloads', True) else 'bad')}
          {pill('auto-approval off', 'good' if policy.get('no_auto_approval', True) else 'bad')}
          {pill('no file movement', 'good' if policy.get('no_file_movement_into_publish_ready_lanes', True) else 'bad')}
          {pill('publishing off', 'good' if policy.get('no_publishing', True) else 'bad')}
        </div>
      </div>
    """


def render_athlete_photo_cards(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for index, row in enumerate(rows):
        athlete_id = clean(row.get("athlete_id"))
        recommended_href = clean(row.get("recommended_review_variant_href"))
        source_href = clean(row.get("source_headshot_href"))
        sheet_href = clean(row.get("contact_sheet_href"))
        preview = (
            f'<img src="{html.escape(recommended_href)}" alt="{html.escape(clean(row.get("athlete_name")))} recommended review crop">'
            if recommended_href
            else '<div class="athlete-photo-missing">Crop missing</div>'
        )
        source_link = f'<a class="tool-link" href="{html.escape(source_href)}">Source</a>' if source_href else '<span class="muted">Source missing</span>'
        sheet_link = f'<a class="tool-link" href="{html.escape(sheet_href)}">Sheet</a>' if sheet_href else '<span class="muted">Sheet missing</span>'
        variant_link = f'<a class="tool-link" href="{html.escape(recommended_href)}">Crop</a>' if recommended_href else '<span class="muted">Crop missing</span>'
        featured = pill("current render athlete", "warn") if row.get("featured") else ""
        body.append(
            f"""
            <article class="athlete-photo-card" data-athlete-card="{html.escape(athlete_id)}">
              <label class="athlete-photo-select">
                <input type="radio" name="athletePhotoRow" value="{html.escape(athlete_id)}" {'checked' if index == 0 else ''}>
                <span>Select</span>
              </label>
              <div class="athlete-photo-thumb">{preview}</div>
              <div class="athlete-photo-meta">
                <div>
                  <strong>{html.escape(clean(row.get('athlete_name')))}</strong>
                  <p>{html.escape(clean(row.get('team_id')))}</p>
                </div>
                <div class="athlete-photo-badges">
                  {featured}
                  {pill(clean(row.get('identity_review_status')) or 'identity_review_required', clean(row.get('identity_review_tone')) or 'warn')}
                  {pill(clean(row.get('identity_resolution_status')) or 'resolution_not_recorded', clean(row.get('identity_resolution_tone')) or 'warn')}
                  {pill(clean(row.get('identity_candidate_status')) or 'identity_candidate_missing', 'warn' if clean(row.get('identity_candidate_status')) != 'candidate_ready' else 'good')}
                  {pill('provider ' + (clean(row.get('identity_provider_candidate')) or 'missing'), 'good' if clean(row.get('identity_provider_candidate')) else 'warn')}
                  {pill('crop ' + (clean(row.get('crop_readiness_score')) or '0') + '/100', clean(row.get('tone')) or 'neutral')}
                  {pill(clean(row.get('variant_status')) or 'review')}
                </div>
                <p>{html.escape(short(clean(row.get('decision_cue')), 170))}</p>
                <p>{html.escape(short(clean(row.get('identity_resolution_next_step')), 190))}</p>
                <p>{html.escape(short(clean(row.get('identity_issue_codes')) or clean(row.get('identity_evidence')), 190))}</p>
                <p>{html.escape(short(clean(row.get('identity_provider_backfill_summary')) or 'Provider-ID backfill requires manual source evidence.', 190))}</p>
                <code>{html.escape(clean(row.get('source_headshot_path')))}</code>
                <div class="athlete-photo-actions">{source_link}{sheet_link}{variant_link}</div>
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No athlete photo onboarding rows found. Run the onboarding generator first.</p>'


def render_identity_review_packet_cards(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        source_url = clean(row.get("source_check_url")) or clean(row.get("provider_player_page_hint"))
        source_link = f'<a class="tool-link" href="{html.escape(source_url)}">Source hint</a>' if source_url else '<span class="muted">No source hint</span>'
        body.append(
            f"""
            <article class="identity-packet-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">{html.escape(clean(row.get('team_id')) or 'wnba')} / {html.escape(clean(row.get('identity_review_status')) or 'identity_review')}</span>
                  <strong>{html.escape(clean(row.get('display_name')) or clean(row.get('athlete_id')))}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill('hold' if clean(row.get('identity_hold')).lower() == 'true' else 'review', 'warn')}
                  {pill('default approval' if clean(row.get('default_approval_present')).lower() == 'true' else 'source review')}
                </div>
              </div>
              <p><strong>Hold reasons:</strong> {html.escape(short(clean(row.get('hold_reason_codes')) or 'manual_identity_review_required', 190))}</p>
              <p><strong>Evidence:</strong> {html.escape(short(clean(row.get('focused_evidence')) or source_url or 'source evidence required before review renders', 190))}</p>
              <p><strong>Operator steps:</strong> {html.escape(short(clean(row.get('operator_review_steps')) or 'open_asset_and_marker; compare_to_source; record_hold_or_verified_decision', 190))}</p>
              <code>{html.escape(short(clean(row.get('asset_path')), 120))}</code>
              <div class="asset-blocker-actions">
                {source_link}
                {pill(clean(row.get('allowed_decisions')) or 'hold_identity|revise_asset')}
                {pill('publish-ready: false')}
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No focused identity review packet rows found. Run the identity resolution generator after the identity audit.</p>'


def render_identity_closure_summary_cards(panel: Dict[str, Any]) -> str:
    groups = [
        ("Closure severity", panel.get("identity_closure_severity_counts", [])),
        ("Closure issue types", panel.get("identity_closure_issue_counts", [])),
        ("Backfill status", panel.get("identity_provider_backfill_status_counts", [])),
        ("Backfill targets", panel.get("identity_provider_backfill_target_counts", [])),
    ]
    body: List[str] = []
    for title, rows in groups:
        if not isinstance(rows, list) or not rows:
            continue
        chips = "".join(
            f"<li><strong>{html.escape(short(clean(row.get('label')) or 'unknown', 58))}</strong><span>{html.escape(str(row.get('rows', 0)))} row(s)</span></li>"
            for row in rows[:6]
            if isinstance(row, dict)
        )
        body.append(
            f"""
            <article class="identity-packet-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">closure packet summary</span>
                  <strong>{html.escape(title)}</strong>
                </div>
                {pill('review-only')}
              </div>
              <ul class="asset-detail-list">{chips}</ul>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No identity closure/backfill packet summaries found.</p>'


def render_identity_review_team_queue(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            f"""
            <article class="asset-blocker-card identity-team-queue-card">
              <div class="asset-blocker-head">
                <div>
                  <span class="row-kicker">identity team queue</span>
                  <strong>{html.escape(clean(row.get('team_id')) or 'unknown_team')}</strong>
                </div>
                <div class="asset-blocker-badges">
                  {pill(str(row.get('identity_hold_rows', 0)) + ' holds', 'warn')}
                  {pill(str(row.get('default_approval_rows', 0)) + ' defaults', 'warn')}
                </div>
              </div>
              <div class="asset-guidance-grid">
                <div><span>Packets</span><strong>{html.escape(str(row.get('packet_rows', 0)))}</strong></div>
                <div><span>High severity</span><strong>{html.escape(str(row.get('high_severity_rows', 0)))}</strong></div>
                <div><span>Action</span><strong>Review source evidence before photo-first renders</strong></div>
                <div><span>Lane</span><strong>review-only identity resolution</strong></div>
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No team-level identity packet queue rows found.</p>'


def render_athlete_photo_onboarding_panel(panel: Dict[str, Any]) -> str:
    rows = panel.get("review_rows", []) if isinstance(panel.get("review_rows"), list) else []
    identity_packets = panel.get("identity_review_packets", []) if isinstance(panel.get("identity_review_packets"), list) else []
    identity_team_queue = panel.get("identity_review_packet_teams", []) if isinstance(panel.get("identity_review_packet_teams"), list) else []
    rows_json = html.escape(json.dumps(rows), quote=True)
    fields_json = html.escape(json.dumps(ATHLETE_PHOTO_DECISION_FIELDS), quote=True)
    identity_fields_json = html.escape(json.dumps(IDENTITY_RESOLUTION_FIELDS), quote=True)
    featured_name = clean(panel.get("featured_athlete_name")) or clean(panel.get("featured_athlete_id")) or "No current athlete"
    identity_decision_command = ".\\hsd.cmd run -Mode identity-decision"
    identity_decision_hint = command_hint(identity_decision_command)
    return f"""
      <div class="athlete-photo-desk" data-athlete-photo-rows="{rows_json}" data-athlete-photo-fields="{fields_json}" data-identity-resolution-fields="{identity_fields_json}">
        <div class="decision-cockpit-card athlete-photo-cockpit">
          <div class="decision-cockpit-head">
            <div>
              <span class="row-kicker">Athlete photo onboarding</span>
              <strong>{html.escape(clean(panel.get('panel_status')) or 'not_run')}</strong>
              <p>{html.escape(clean(panel.get('next_step')))}</p>
            </div>
            <div class="decision-cockpit-actions">
              {pill(clean(panel.get('manifest_status')) or 'not_run')}
              {pill('identity audit: ' + (clean(panel.get('identity_audit_status')) or 'not_run'), 'warn' if clean(panel.get('identity_audit_status')) != 'pass' else 'good')}
              {pill('resolution: ' + (clean(panel.get('identity_resolution_status')) or 'not_run'), 'good' if clean(panel.get('identity_resolution_status')) == 'no_audit_issues_found' else 'warn')}
              {pill('publish-ready: false')}
            </div>
          </div>
          <div class="decision-status-grid">
            <div><span>Current render athlete</span><strong>{html.escape(featured_name)}</strong></div>
            <div><span>Review variants</span><strong>{html.escape(str(panel.get('review_variant_ready', 0)))}/{html.escape(str(panel.get('source_rows', 0)))}</strong></div>
            <div><span>Crop review holds</span><strong>{html.escape(str(panel.get('review_variant_needs_crop_review', 0)))}</strong></div>
            <div><span>Identity audit issues</span><strong>{html.escape(str(panel.get('identity_audit_issue_rows', 0)))}</strong></div>
            <div><span>Resolution candidates</span><strong>{html.escape(str(panel.get('identity_resolution_candidate_rows', 0)))}</strong></div>
            <div><span>Identity packet holds</span><strong>{html.escape(str(panel.get('identity_review_packet_hold_rows', 0)))}/{html.escape(str(panel.get('identity_review_packet_rows', 0)))}</strong></div>
            <div><span>Athlete source boards</span><strong>{html.escape(str(panel.get('athlete_contact_sheet_teams', 0)))}/{html.escape(str(panel.get('athlete_contact_sheet_rows', 0)))}</strong></div>
            <div><span>Photo review intake rows</span><strong>{html.escape(str(panel.get('athlete_contact_sheet_intake_rows', 0)))}</strong></div>
            <div><span>Resolution inbox rows</span><strong>{html.escape(str(panel.get('identity_resolution_inbox_rows', 0)))}</strong></div>
            <div><span>Closure/backfill rows</span><strong>{html.escape(str(panel.get('identity_closure_rows', 0)))}/{html.escape(str(panel.get('identity_provider_backfill_rows', 0)))}</strong></div>
            <div><span>Closure high rows</span><strong>{html.escape(str(panel.get('identity_closure_high_rows', 0)))}</strong></div>
            <div><span>Blank closure/backfill decisions</span><strong>{html.escape(str(panel.get('identity_closure_blank_decisions', 0)))}/{html.escape(str(panel.get('identity_provider_backfill_blank_decisions', 0)))}</strong></div>
          </div>
          {packet_freshness_html(panel, 'identity_review_packet', 'Identity review')}
          {packet_freshness_html(panel, 'athlete_contact_sheet', 'Athlete photo contact sheets')}
          <div class="review-flow">
            <div><span>1</span><strong>Open source</strong><p>Compare source headshot and contact sheet by eye.</p></div>
            <div><span>2</span><strong>Verify identity</strong><p>Crop score is not identity proof; wrong-person risk must be held.</p></div>
            <div><span>3</span><strong>Copy decision</strong><p>Prepare a review-only row without approving or moving files.</p></div>
          </div>
        </div>
        <div class="decision-desk-section">
          <div class="row-kicker">Onboarding files {pill('open before deciding')}</div>
          <div class="decision-link-grid">
            {render_decision_shortcuts(panel.get('file_shortcuts', []))}
          </div>
        </div>
        <div class="decision-desk-section">
          <div class="row-kicker">Identity closure/backfill packet {pill(clean(panel.get('identity_closure_status')) or 'not_run')} {pill(str(panel.get('identity_provider_backfill_manual_review_rows', 0)) + ' manual backfill rows')}</div>
          <p class="muted">{html.escape(clean(panel.get('identity_closure_next_step')))}</p>
          <div class="identity-packet-grid">
            {render_identity_closure_summary_cards(panel)}
          </div>
        </div>
        <div class="decision-desk-section">
          <div class="row-kicker">Focused identity review packet {pill(str(len(identity_packets)) + ' shown')} {pill(str(panel.get('identity_review_packet_default_rows', 0)) + ' default approvals')}</div>
          <div class="row-kicker">Team packet queues {pill(str(len(identity_team_queue)) + ' teams shown')} {pill('review-only')}</div>
          <div class="identity-packet-grid">
            {render_identity_review_team_queue(identity_team_queue)}
          </div>
          <div class="identity-packet-grid">
            {render_identity_review_packet_cards(identity_packets)}
          </div>
        </div>
        <div class="athlete-photo-layout">
          <div class="athlete-photo-list">
            <div class="row-kicker">Review queue {pill(str(len(rows)) + ' shown')} {pill('all manual')}</div>
            {render_athlete_photo_cards(rows)}
          </div>
          <div class="athlete-photo-action-card">
            <div class="row-kicker">Prepare athlete-photo decision <span id="athletePhotoReadyBadge" class="pill warn">Identity required</span></div>
            <div class="athlete-photo-selected" id="athletePhotoSelectedSummary">Select a row to prepare a decision.</div>
            <ul id="athletePhotoWarnings" class="decision-warning-list"></ul>
            <form class="decision-form">
              <fieldset class="decision-options">
                <legend>Approve, hold, or revise crop</legend>
                <label class="decision-option"><input type="radio" name="athletePhotoDecision" value="approve_variant_for_review_drafts"><span>Approve review crop</span></label>
                <label class="decision-option"><input type="radio" name="athletePhotoDecision" value="hold" checked><span>Hold</span></label>
                <label class="decision-option"><input type="radio" name="athletePhotoDecision" value="revise_crop"><span>Revise crop</span></label>
              </fieldset>
              <div class="decision-form-grid">
                <label>Identity verified
                  <select id="athletePhotoIdentityVerified">
                    <option value="">Choose after visual check</option>
                    <option value="yes">Yes, verified by eye</option>
                    <option value="no">No / not sure</option>
                  </select>
                </label>
                <label>Crop choice
                  <select id="athletePhotoCropChoice">
                    <option value="recommended_review_variant">Recommended crop</option>
                    <option value="photo_first_feed">Feed crop</option>
                    <option value="photo_first_story">Story crop</option>
                    <option value="compact_square">Square crop</option>
                    <option value="hold_no_crop">Hold, no crop</option>
                  </select>
                </label>
              </div>
              <label>Operator notes<textarea id="athletePhotoNotes" rows="3" required placeholder="What source/contact sheet did you compare? If this looks wrong, say who/what failed."></textarea></label>
            </form>
            <div class="decision-copy-box">
              <div class="row-kicker">Copy-safe onboarding CSV row</div>
              <textarea id="athletePhotoCsvOutput" rows="5" readonly></textarea>
              <div class="decision-button-row">
                <button class="tool-link" type="button" id="copyAthletePhotoRow">Copy row</button>
                <span class="muted" id="athletePhotoCopyStatus">Paste into a manual copy of the athlete-photo decision template. Do not edit generated files directly.</span>
              </div>
            </div>
            <div class="decision-desk-section">
              <div class="row-kicker">Identity resolution <span id="identityResolutionReadyBadge" class="pill warn">Source evidence required</span></div>
              <div class="athlete-photo-selected" id="identityResolutionSelectedSummary">Select a row to prepare identity evidence.</div>
              <p class="muted" id="identityWritebackMode">File-opened dashboard is copy-safe. Run {html.escape(identity_decision_command)} to open localhost save mode.</p>
              <ul id="identityResolutionWarnings" class="decision-warning-list"></ul>
              <form class="decision-form">
                <fieldset class="decision-options">
                  <legend>Verify, hold, revise, or backfill</legend>
                  <label class="decision-option"><input type="radio" name="identityResolutionDecision" value="identity_verified_approved_for_review_renders"><span>Verify</span></label>
                  <label class="decision-option"><input type="radio" name="identityResolutionDecision" value="hold_identity" checked><span>Hold</span></label>
                  <label class="decision-option"><input type="radio" name="identityResolutionDecision" value="revise_asset"><span>Revise</span></label>
                  <label class="decision-option"><input type="radio" name="identityResolutionDecision" value="backfill_provider_id_only"><span>Backfill ID</span></label>
                </fieldset>
                <div class="decision-form-grid">
                  <label>Identity verified
                    <select id="identityResolutionVerified">
                      <option value="">Choose after source check</option>
                      <option value="yes">Yes, source-backed</option>
                      <option value="no">No / hold</option>
                    </select>
                  </label>
                  <label>Provider ID verified
                    <select id="identityProviderVerified">
                      <option value="">Choose after source check</option>
                      <option value="yes">Yes, provider/source backed</option>
                      <option value="no">No / unknown</option>
                    </select>
                  </label>
                </div>
                <label>Approved source URL<input id="identityApprovedSourceUrl" type="url" placeholder="Free official/team/reputable public URL checked by eye"></label>
                <label>Secondary source URL<input id="identitySecondarySourceUrl" type="url" placeholder="Optional cross-check URL"></label>
                <div class="decision-form-grid">
                  <label>Backfill provider player ID<input id="identityBackfillProviderId" type="text" placeholder="Only if source-backed"></label>
                  <label>Operator name<input id="identityOperatorName" type="text" placeholder="Your name"></label>
                </div>
                <label>Reviewed at<input id="identityReviewedAtLocal" type="text"></label>
                <label>Identity notes<textarea id="identityResolutionNotes" rows="3" placeholder="Who did you compare, what source did you use, and why approve/hold/revise/backfill?"></textarea></label>
              </form>
              <div class="decision-copy-box">
                <div class="row-kicker">Copy-safe identity resolution CSV row</div>
                <textarea id="identityResolutionCsvOutput" rows="5" readonly></textarea>
                <div class="decision-button-row">
                  <button class="tool-link" type="button" id="copyIdentityResolutionRow">Copy identity row</button>
                  <span class="muted" id="identityResolutionCopyStatus">Paste below the header in operator/inbox/wnba_athlete_identity_resolution.csv. Backfill-only rows do not clear photo-first rendering.</span>
                </div>
              </div>
              {identity_decision_hint}
            </div>
            <div class="safety-strip">
              {pill('review-only derivative', 'good')}
              {pill('identity human-check required', 'warn')}
              {pill('auto-approval off')}
              {pill('no file movement')}
              {pill('publishing off')}
              {pill('paid APIs off', 'good')}
            </div>
          </div>
        </div>
      </div>
    """


def render_issues(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for issue in rows:
        body.append(
            f"""
            <article class="issue-row">
              <div>{pill(clean(issue.get('severity')) or 'review')}</div>
              <div>
                <h3>{html.escape(clean(issue.get('code')) or 'Review note')}</h3>
                <p>{html.escape(first_present(issue.get('detail'), issue.get('headline')))}</p>
              </div>
            </article>
            """
        )
    return "".join(body) or '<p class="empty">No blocking issues reported.</p>'


def render_artifacts(rows: Iterable[Dict[str, Any]]) -> str:
    body = []
    for row in rows:
        search_text = " ".join([row["group"], row["title"], row["path"], clean(row.get("run_command")), clean(row.get("status_detail"))])
        body.append(
            f"""
            <tr data-artifact-row data-group="{html.escape(row['group'].lower())}" data-search="{html.escape(search_text.lower())}">
              <td>{html.escape(row['group'])}</td>
              <td>{html.escape(row['title'])}</td>
              <td><code>{html.escape(row['path'])}</code></td>
              <td>{pill('found' if row['exists'] else 'missing')}</td>
              <td>{html.escape(clean(row.get('status_detail')))}</td>
              <td>{artifact_tool(row)}</td>
            </tr>
            """
        )
    return "".join(body)


def render_html(payload: Dict[str, Any]) -> str:
    decision = payload["decision"]
    metrics = "".join(
        f"""
        <section class="metric {html.escape(item['tone'])}">
          <span>{html.escape(item['label'])}</span>
          <strong>{html.escape(item['value'])}</strong>
          {f"<small>{html.escape(item['detail'])}</small>" if item.get("detail") else ""}
        </section>
        """
        for item in payload["metrics"]
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>HSD Daily Operator Command Center</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --ink:#171719;
      --muted:#696b73;
      --line:#dedfe6;
      --paper:#ffffff;
      --wash:#f4f5f8;
      --green:#1f7a4d;
      --green-bg:#dff5e8;
      --red:#9c211a;
      --red-bg:#fde2df;
      --amber:#806400;
      --amber-bg:#fff0b8;
      --blue:#255f9f;
      --blue-bg:#e2effc;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--wash); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif; line-height:1.45; }}
    header {{ background:#171719; color:#fff; padding:24px 28px; border-bottom:5px solid #f0c84b; }}
    header h1 {{ margin:0; font-size:28px; line-height:1.1; letter-spacing:0; }}
    header p {{ margin:8px 0 0; color:#d9d9df; max-width:900px; overflow-wrap:anywhere; }}
    main {{ max-width:1320px; margin:0 auto; padding:22px 24px 48px; }}
    h2 {{ margin:0 0 12px; font-size:20px; }}
    h3 {{ margin:4px 0 6px; font-size:16px; }}
    p {{ margin:0; }}
    code {{ background:#eceef4; padding:2px 5px; border-radius:4px; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:10px 8px; vertical-align:top; }}
    th {{ color:#555861; font-size:12px; text-transform:uppercase; }}
    .top-grid {{ display:grid; grid-template-columns:1.15fr .85fr; gap:16px; align-items:stretch; }}
    .panel {{ background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 1px 2px rgba(20,20,30,.05); min-width:0; }}
    .decision {{ display:grid; gap:14px; grid-template-columns:1fr auto; }}
    .decision-call strong {{ display:block; font-size:34px; line-height:1; margin:8px 0; }}
    .home-header {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:14px; align-items:center; background:#fff; border:1px solid var(--line); border-left:6px solid #f0c84b; border-radius:8px; padding:14px 16px; margin-bottom:14px; }}
    .home-header h2 {{ margin:2px 0 4px; font-size:22px; }}
    .home-header p {{ color:#4f535c; max-width:850px; }}
    .home-actions {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }}
    .primary-tab-jump {{ border:0; border-radius:7px; background:#171719; color:#fff; padding:11px 14px; font-weight:900; cursor:pointer; }}
    .secondary-artifact-link {{ color:#4f535c; font-size:12px; font-weight:800; text-align:right; }}
    .secondary-artifact-link a {{ margin-top:5px; }}
    .safety-strip {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
    .brief-list {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-top:18px; }}
    .brief-list div {{ border-top:1px solid var(--line); padding-top:10px; }}
    .brief-list span {{ display:block; color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; }}
    .brief-list strong {{ display:block; margin-top:4px; font-size:14px; line-height:1.35; overflow-wrap:anywhere; }}
    .metric-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin:16px 0; }}
    .metric {{ background:#fff; border:1px solid var(--line); border-left:5px solid #aeb2bd; border-radius:8px; padding:12px; min-height:78px; }}
    .metric span {{ display:block; color:#5e616a; font-size:12px; font-weight:700; text-transform:uppercase; }}
    .metric strong {{ display:block; margin-top:5px; font-size:19px; overflow-wrap:anywhere; }}
    .metric.good {{ border-left-color:var(--green); }}
    .metric.bad {{ border-left-color:var(--red); }}
    .metric.warn {{ border-left-color:#d7a900; }}
    .metric.neutral {{ border-left-color:var(--blue); }}
    .tabs {{ display:flex; gap:6px; flex-wrap:wrap; margin:14px 0; }}
    .tab-button {{ border:1px solid var(--line); background:#fff; border-radius:6px; padding:9px 12px; font-weight:700; cursor:pointer; }}
    .tab-button[aria-selected="true"] {{ background:#171719; color:white; border-color:#171719; }}
    .tab-panel {{ display:none; }}
    .tab-panel.active {{ display:block; }}
    .section-heading {{ display:flex; justify-content:space-between; gap:12px; align-items:start; margin-bottom:12px; flex-wrap:wrap; }}
    .section-heading h2 {{ margin-bottom:4px; }}
    .action-list,.content-list,.issue-list {{ display:grid; gap:10px; }}
    .action-row,.content-row,.issue-row {{ display:grid; grid-template-columns:auto minmax(0,1fr) auto; gap:12px; align-items:start; background:#fff; border:1px solid var(--line); border-radius:8px; padding:12px; min-width:0; }}
    .content-row,.issue-row {{ grid-template-columns:1fr auto; }}
    .action-row > *,.content-row > *,.issue-row > * {{ min-width:0; }}
    .rank {{ width:32px; height:32px; border-radius:50%; background:#171719; color:#fff; display:grid; place-items:center; font-weight:800; }}
    .row-kicker {{ color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; display:flex; gap:6px; align-items:center; flex-wrap:wrap; }}
    .row-tool {{ align-self:center; display:grid; gap:6px; justify-items:start; }}
    .row-tool small {{ color:var(--muted); overflow-wrap:anywhere; max-width:220px; }}
    .command-line {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-top:9px; color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; }}
    .command-line code {{ text-transform:none; font-weight:700; overflow-wrap:anywhere; }}
    .pill {{ display:inline-block; border-radius:999px; padding:3px 8px; font-size:12px; font-weight:800; background:#eceef4; color:#333640; }}
    .pill.good {{ background:var(--green-bg); color:var(--green); }}
    .pill.bad {{ background:var(--red-bg); color:var(--red); }}
    .pill.warn {{ background:var(--amber-bg); color:var(--amber); }}
    .pill.neutral {{ background:var(--blue-bg); color:var(--blue); }}
    .tool-link {{ display:inline-block; border:1px solid #c8cbd4; border-radius:6px; padding:7px 10px; color:#171719; text-decoration:none; font-weight:800; background:#fff; }}
    .tool-link:hover {{ border-color:#171719; }}
    .muted,.empty {{ color:var(--muted); }}
    .cell-detail {{ color:var(--muted); display:block; font-size:11px; font-weight:700; line-height:1.25; margin-top:3px; }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .artifact-toolbar {{ display:flex; gap:10px; align-items:center; margin-bottom:12px; flex-wrap:wrap; }}
    .artifact-toolbar input {{ min-width:280px; flex:1; border:1px solid var(--line); border-radius:6px; padding:10px 12px; font:inherit; }}
    .artifact-toolbar select {{ border:1px solid var(--line); border-radius:6px; padding:10px 12px; font:inherit; background:#fff; }}
    .table-wrap {{ overflow:auto; background:#fff; border:1px solid var(--line); border-radius:8px; max-width:100%; }}
    .decision-ui {{ display:grid; grid-template-columns:minmax(300px,.78fr) minmax(0,1.22fr); gap:16px; align-items:start; }}
    .decision-preview-column {{ display:grid; gap:10px; position:sticky; top:12px; align-self:start; }}
    .decision-preview-header {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:start; background:#fff; border:1px solid var(--line); border-radius:8px; padding:10px; }}
    .decision-preview-header strong {{ display:block; font-size:17px; margin-top:2px; }}
    .decision-preview {{ background:#111; border:1px solid var(--line); border-radius:8px; overflow:hidden; min-height:360px; display:grid; place-items:center; }}
    .decision-preview-img {{ width:100%; max-height:720px; object-fit:contain; display:block; background:#111; }}
    .decision-preview-missing {{ color:#fff; font-weight:800; }}
    .decision-preview-footer {{ display:flex; gap:6px; flex-wrap:wrap; }}
    .decision-workbench {{ display:grid; gap:12px; min-width:0; }}
    .decision-cockpit-card {{ display:grid; gap:12px; background:#fff; border:1px solid var(--line); border-left:6px solid #f0c84b; border-radius:8px; padding:12px; min-width:0; }}
    .decision-cockpit-head {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; align-items:start; }}
    .decision-cockpit-head strong {{ display:block; font-size:18px; margin:2px 0 4px; }}
    .decision-cockpit-head p,.decision-cockpit-card small {{ color:#5e616a; }}
    .decision-cockpit-actions {{ display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }}
    .decision-status-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }}
    .decision-status-grid div {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; min-width:0; }}
    .decision-status-grid span {{ display:block; color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; margin-bottom:5px; }}
    .decision-status-grid strong {{ display:block; font-size:18px; overflow-wrap:anywhere; }}
    .review-flow {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }}
    .review-flow div {{ border:1px solid #e5d493; background:#fff9df; border-radius:8px; padding:9px; min-width:0; }}
    .review-flow span {{ width:22px; height:22px; border-radius:999px; display:inline-grid; place-items:center; background:#171719; color:#fff; font-weight:900; font-size:12px; }}
    .review-flow strong {{ display:block; margin-top:6px; font-size:13px; }}
    .review-flow p {{ color:#5e616a; font-size:12px; line-height:1.3; margin-top:2px; }}
    .decision-signal-grid {{ display:grid; grid-template-columns:minmax(0,1.05fr) minmax(280px,.95fr); gap:12px; align-items:start; }}
    .decision-desk-section {{ display:grid; gap:8px; border-top:1px solid var(--line); padding-top:12px; min-width:0; }}
    .decision-link-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }}
    .decision-link-card {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:start; border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; min-width:0; }}
    .decision-link-card strong {{ display:block; font-size:13px; }}
    .decision-link-card p {{ color:#5e616a; font-size:12px; margin:3px 0 6px; }}
    .decision-link-card code {{ display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .decision-link-card > div:last-child {{ display:flex; gap:6px; align-items:center; flex-wrap:wrap; justify-content:flex-end; }}
    .render-gallery-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }}
    .render-gallery-card {{ border:1px solid var(--line); border-radius:8px; background:#fff; padding:10px; display:grid; gap:8px; min-width:0; }}
    .render-comparison-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; align-items:stretch; }}
    .render-comparison-grid span {{ color:#5e616a; display:block; font-size:10px; font-weight:900; letter-spacing:0; margin-bottom:4px; text-transform:uppercase; }}
    .render-gallery-frame {{ background:#111823; border:1px solid #242b38; border-radius:7px; min-height:260px; display:grid; place-items:center; overflow:hidden; }}
    .render-gallery-frame.ig_story_9x16 {{ min-height:330px; }}
    .render-reference-frame {{ background:#f5f6f8; border-color:#d8dbe3; }}
    .render-gallery-frame img {{ width:100%; height:100%; max-height:430px; object-fit:contain; display:block; }}
    .render-gallery-missing {{ color:#fff; font-weight:800; padding:28px 12px; text-align:center; }}
    .render-gallery-meta {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; align-items:start; }}
    .render-gallery-actions {{ display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }}
    .render-gallery-meta strong {{ display:block; font-size:14px; }}
    .render-gallery-meta p,.render-gallery-note {{ color:#5e616a; font-size:12px; margin-top:3px; }}
    .render-gallery-facts {{ display:flex; gap:6px; flex-wrap:wrap; }}
    .render-cue-grid {{ display:grid; gap:6px; grid-template-columns:1fr; }}
    .render-cue {{ border:1px solid var(--line); border-left-width:4px; border-radius:7px; padding:7px 8px; background:#fff; min-width:0; }}
    .render-cue span {{ color:#5e616a; display:block; font-size:10px; font-weight:900; text-transform:uppercase; }}
    .render-cue strong {{ color:#151922; display:block; font-size:12px; line-height:1.2; margin-top:2px; }}
    .render-cue p {{ color:#5e616a; font-size:11px; line-height:1.25; margin-top:3px; }}
    .render-cue-good {{ border-left-color:#16a34a; background:#f4fbf7; }}
    .render-cue-warn {{ border-left-color:#d39c08; background:#fff9df; }}
    .render-cue-bad {{ border-left-color:#c02637; background:#fff1f2; }}
    .render-cue-neutral {{ border-left-color:#6b7280; background:#f7f8fb; }}
    .render-gallery-card code {{ display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .qa-cue-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }}
    .qa-cue-card {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:start; border:1px solid var(--line); border-radius:8px; background:#fff; padding:10px; min-width:0; }}
    .qa-cue-card strong {{ display:block; font-size:13px; }}
    .qa-cue-card p {{ color:#5e616a; font-size:12px; line-height:1.3; margin-top:4px; overflow-wrap:anywhere; }}
    .delta-cue-grid {{ display:grid; gap:8px; }}
    .delta-cue-card {{ display:grid; grid-template-columns:76px minmax(0,1fr); gap:10px; border:1px solid var(--line); border-left-width:5px; border-radius:8px; background:#fff; padding:10px; min-width:0; }}
    .delta-cue-card span {{ color:#5e616a; display:block; font-size:10px; font-weight:900; text-transform:uppercase; }}
    .delta-cue-card strong {{ display:block; font-size:22px; line-height:1.05; margin-top:3px; }}
    .delta-cue-card b {{ display:block; font-size:13px; }}
    .delta-cue-card p {{ color:#5e616a; font-size:12px; line-height:1.3; margin-top:3px; }}
    .delta-cue-good {{ border-left-color:#16a34a; background:#f7fcf9; }}
    .delta-cue-warn {{ border-left-color:#d39c08; background:#fffaf0; }}
    .delta-cue-bad {{ border-left-color:#c02637; background:#fff5f6; }}
    .delta-cue-neutral {{ border-left-color:#6b7280; background:#f8f9fb; }}
    .decision-action-card {{ display:grid; gap:10px; border:1px solid var(--line); border-left:6px solid #171719; border-radius:8px; background:#fff; padding:12px; min-width:0; }}
    .decision-warning-list {{ margin:0; padding:0; display:grid; gap:6px; list-style:none; }}
    .decision-warning-list li {{ border:1px solid #ecd58a; background:#fff7d7; border-radius:6px; padding:8px 10px; color:#5d4800; font-weight:700; }}
    .decision-warning-list li.good {{ border-color:#b9dfc8; background:var(--green-bg); color:var(--green); }}
    .decision-history-table {{ max-height:260px; }}
    .decision-history-table td {{ font-size:13px; }}
    .decision-form {{ display:grid; gap:10px; }}
    .decision-form label {{ display:grid; gap:5px; color:#3f424b; font-size:13px; font-weight:800; }}
    .decision-form textarea,.decision-form input,.decision-copy-box textarea {{ width:100%; border:1px solid var(--line); border-radius:6px; padding:10px 12px; font:inherit; background:#fff; color:var(--ink); resize:vertical; }}
    .decision-form-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .decision-options {{ border:0; padding:0; margin:0; display:flex; gap:8px; flex-wrap:wrap; }}
    .decision-options legend {{ color:#5e616a; font-size:12px; font-weight:800; text-transform:uppercase; margin-bottom:6px; }}
    .decision-option {{ display:inline-flex !important; grid-template-columns:auto auto; align-items:center; gap:6px !important; border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:#fff; cursor:pointer; }}
    .decision-option input {{ width:auto; }}
    .decision-copy-box {{ display:grid; gap:8px; border-top:1px solid var(--line); padding-top:12px; }}
    .decision-button-row {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; }}
    .asset-readiness-desk {{ display:grid; gap:12px; margin-bottom:18px; padding-bottom:18px; border-bottom:2px solid #eceef4; }}
    .asset-readiness-cockpit {{ border-left-color:#171719; }}
    .asset-blocker-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
    .asset-blocker-card {{ display:grid; gap:8px; border:1px solid var(--line); border-radius:8px; background:#fff; padding:10px; min-width:0; }}
    .asset-blocker-head {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; align-items:start; }}
    .asset-blocker-head strong {{ display:block; font-size:15px; overflow-wrap:anywhere; }}
    .asset-blocker-badges,.asset-blocker-actions {{ display:flex; gap:6px; flex-wrap:wrap; justify-content:flex-end; }}
    .asset-blocker-card p {{ color:#5e616a; font-size:12px; line-height:1.35; overflow-wrap:anywhere; }}
    .asset-blocker-card code {{ display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .asset-guidance-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:6px; }}
    .asset-guidance-grid div {{ border:1px solid #e5d493; background:#fff9df; border-radius:6px; padding:8px; min-width:0; }}
    .asset-guidance-grid span {{ display:block; color:#5e616a; font-size:11px; font-weight:900; text-transform:uppercase; margin-bottom:4px; }}
    .asset-guidance-grid strong {{ display:block; font-size:12px; line-height:1.25; overflow-wrap:anywhere; }}
    .athlete-photo-desk {{ display:grid; gap:12px; margin-bottom:18px; padding-bottom:18px; border-bottom:2px solid #eceef4; }}
    .athlete-photo-cockpit {{ border-left-color:#94dbc9; }}
    .athlete-photo-layout {{ display:grid; grid-template-columns:minmax(0,1.15fr) minmax(340px,.85fr); gap:12px; align-items:start; }}
    .athlete-photo-list {{ display:grid; gap:8px; min-width:0; max-height:920px; overflow:auto; padding-right:4px; }}
    .athlete-photo-card {{ display:grid; grid-template-columns:auto 130px minmax(0,1fr); gap:10px; align-items:start; border:1px solid var(--line); border-radius:8px; background:#fff; padding:10px; min-width:0; }}
    .athlete-photo-card:has(input:checked) {{ border-color:#171719; box-shadow:0 0 0 2px rgba(23,23,25,.08); }}
    .athlete-photo-select {{ display:flex !important; align-items:center; gap:6px !important; font-size:12px !important; color:#333640 !important; }}
    .athlete-photo-select input {{ width:auto; }}
    .athlete-photo-thumb {{ background:#07101c; border:1px solid #242b38; border-radius:7px; width:130px; height:162px; display:grid; place-items:center; overflow:hidden; }}
    .athlete-photo-thumb img {{ width:100%; height:100%; object-fit:contain; display:block; }}
    .athlete-photo-missing {{ color:#fff; font-weight:800; text-align:center; padding:8px; }}
    .athlete-photo-meta {{ display:grid; gap:6px; min-width:0; }}
    .athlete-photo-meta strong {{ display:block; font-size:15px; }}
    .athlete-photo-meta p {{ color:#5e616a; font-size:12px; overflow-wrap:anywhere; }}
    .athlete-photo-meta code {{ display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .athlete-photo-badges,.athlete-photo-actions {{ display:flex; gap:6px; flex-wrap:wrap; }}
    .athlete-photo-action-card {{ display:grid; gap:10px; border:1px solid var(--line); border-left:6px solid #94dbc9; border-radius:8px; background:#fff; padding:12px; min-width:0; position:sticky; top:12px; }}
    .athlete-photo-selected {{ border:1px solid #d6efe8; background:#f3fbf8; border-radius:7px; padding:10px; font-size:13px; font-weight:800; color:#165b4a; overflow-wrap:anywhere; }}
    .identity-packet-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }}
    .identity-packet-card {{ display:grid; gap:8px; border:1px solid var(--line); border-left:5px solid #d7a900; border-radius:8px; background:#fff; padding:10px; min-width:0; }}
    .identity-packet-card p {{ color:#5e616a; font-size:12px; line-height:1.35; overflow-wrap:anywhere; }}
    .identity-packet-card code {{ display:block; max-width:100%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .decision-form select {{ width:100%; border:1px solid var(--line); border-radius:6px; padding:10px 12px; font:inherit; background:#fff; color:var(--ink); }}
    @media (max-width: 900px) {{
      header {{ padding:20px; }}
      main {{ padding:16px; }}
      .top-grid,.two-col,.decision-ui,.athlete-photo-layout {{ grid-template-columns:1fr; }}
      .decision-preview-column,.athlete-photo-action-card {{ position:static; }}
      .home-header {{ grid-template-columns:1fr; }}
      .home-actions {{ justify-content:flex-start; }}
      .render-gallery-grid {{ grid-template-columns:1fr; }}
      .render-comparison-grid {{ grid-template-columns:1fr; }}
      .decision-cockpit-head,.decision-signal-grid,.review-flow {{ grid-template-columns:1fr; }}
      .qa-cue-grid {{ grid-template-columns:1fr; }}
      .asset-blocker-grid {{ grid-template-columns:1fr; }}
      .identity-packet-grid {{ grid-template-columns:1fr; }}
      .decision-link-grid {{ grid-template-columns:1fr; }}
      .decision {{ grid-template-columns:1fr; }}
      .metric-grid,.decision-status-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      .brief-list {{ grid-template-columns:1fr; }}
      .action-row,.content-row,.issue-row {{ grid-template-columns:1fr; }}
      .rank {{ width:28px; height:28px; }}
    }}
    @media (max-width: 560px) {{
      .metric-grid,.decision-status-grid,.decision-form-grid {{ grid-template-columns:1fr; }}
      .asset-guidance-grid {{ grid-template-columns:1fr; }}
      .athlete-photo-card {{ grid-template-columns:1fr; }}
      .athlete-photo-thumb {{ width:100%; height:220px; }}
      header h1 {{ font-size:23px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>HSD Daily Operator Command Center</h1>
    <p>Generated {html.escape(payload['generated_at_utc'])}. Local/manual operation is the default. Paid APIs and auto-publishing are off.</p>
  </header>
  <main>
    <section class="home-header" aria-label="Start here">
      <div>
        <span class="row-kicker">Start here</span>
        <h2>Use this dashboard for daily review. Use guard reports only as safety evidence.</h2>
        <p>The Decision tab is the render review desk. It contains the draft previews, visual QA cues, reference drift warnings, and manual approve/hold/revise controls.</p>
      </div>
      <div class="home-actions">
        <button class="primary-tab-jump" type="button" data-tab-jump="decision-panel">Open Decision Desk</button>
        <button class="tool-link" type="button" data-tab-jump="artifacts">Open Artifact List</button>
      </div>
    </section>

    <section class="top-grid">
      <div class="panel decision">
        <div class="decision-call">
          <span class="row-kicker">Current call</span>
          <strong>{html.escape(decision['overall'])}</strong>
          <p>{html.escape(decision['callout'])}</p>
          <div class="safety-strip">
            {pill(decision['free_source_mode'], 'good')}
            {pill(f"Publish allowed: {display_bool(decision['publish_allowed'])}")}
            {pill(f"Graphics handoff: {display_bool(decision['graphics_handoff_allowed'])}")}
            {pill(decision['automation'])}
          </div>
          <div class="brief-list">
            <div><span>Best candidate</span><strong>{html.escape(payload['briefing']['best_candidate'])}</strong></div>
            <div><span>Studio lane</span><strong>{html.escape(payload['briefing']['studio_lane'])}</strong></div>
            <div><span>Source state</span><strong>{html.escape(payload['briefing']['source_state'])}</strong></div>
            <div><span>Next manual move</span><strong>{html.escape(payload['briefing']['next_manual_move'])}</strong></div>
          </div>
        </div>
        <div class="secondary-artifact-link">
          <span>Secondary safety report</span>
          {open_link('publish_guard_report.md', 'Open guard report')}
        </div>
      </div>
      <div class="panel">
        <h2>Top next actions</h2>
        <div class="action-list">{render_action_rows(payload['next_actions'][:3])}</div>
      </div>
    </section>

    <section class="panel" aria-label="Operator next-action synthesis">
      <div class="section-heading">
        <div>
          <span class="row-kicker">Unified manual checklist</span>
          <h2>Operator next-action synthesis</h2>
          <p class="muted">One review-only path across render review, research handoff, source confirmations, public-signal returns, women's soccer helpers, and hockey/softball source returns.</p>
        </div>
        {open_link('operator_next_action_synthesis.md', 'Open checklist')}
      </div>
      <div class="action-list">{render_next_action_synthesis(payload.get('operator_next_action_synthesis', []))}</div>
    </section>

    <section class="metric-grid">{metrics}</section>

    <nav class="tabs" aria-label="Command center views">
      <button class="tab-button" type="button" data-tab-target="today" aria-selected="true">Today</button>
      <button class="tab-button" type="button" data-tab-target="decision-panel" aria-selected="false">Decision</button>
      <button class="tab-button" type="button" data-tab-target="content" aria-selected="false">Content</button>
      <button class="tab-button" type="button" data-tab-target="sources" aria-selected="false">Sources</button>
      <button class="tab-button" type="button" data-tab-target="safety" aria-selected="false">Safety</button>
      <button class="tab-button" type="button" data-tab-target="artifacts" aria-selected="false">Artifacts</button>
    </nav>

    <section id="today" class="tab-panel active">
      <div class="two-col">
        <div class="panel">
          <h2>Action queue</h2>
          <div class="action-list">{render_action_rows(payload['next_actions'])}</div>
        </div>
        <div class="panel">
          <h2>Posting schedule</h2>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Time ET</th><th>Platform</th><th>Slot</th><th>Status</th><th>Action</th><th>Artifact</th></tr></thead>
              <tbody>{render_schedule(payload['schedule'])}</tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <section id="decision-panel" class="tab-panel">
      <div class="panel">
        <h2>Decision desk</h2>
        {render_decision_stop_go_summary_panel(payload.get('decision_stop_go_summary', {}))}
        {render_decision_review_order_panel(payload.get('decision_review_order_checklist', []))}
        {render_asset_readiness_panel(payload['asset_readiness_panel'])}
        {render_manual_asset_source_board_panel(payload.get('manual_asset_source_board', []))}
        {render_manual_logo_verification_intake_panel(payload.get('manual_logo_verification_intake', []))}
        {render_manual_league_mark_context_intake_panel(payload.get('manual_league_mark_context_intake', []))}
        {render_athlete_photo_onboarding_panel(payload['athlete_photo_onboarding_panel'])}
        <h2>Manual visual QA decision</h2>
        {render_operator_decision_panel(payload['operator_decision_panel'])}
      </div>
    </section>

    <section id="content" class="tab-panel">
      <div class="panel" style="margin-bottom:16px">
        <h2>Render readiness</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Rank</th><th>Band</th><th>Score</th><th>Story</th><th>Path</th><th>Source</th><th>Assets</th><th>Format</th><th>Manual path</th><th>Blockers</th><th>Next step</th><th>Open</th></tr></thead>
            <tbody>{render_render_readiness(payload['render_readiness_queue'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-bottom:16px">
        <h2>Render prep packets</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Score</th><th>Story</th><th>Template</th><th>Shape</th><th>Copy headline</th><th>Assets</th><th>Manual steps</th><th>Gate</th><th>Open</th></tr></thead>
            <tbody>{render_render_prep_packets(payload['render_prep_packets'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-bottom:16px">
        <h2>Top render handoff</h2>
        <div class="content-list">{render_render_handoff_summary(payload['render_handoff_summary'])}</div>
      </div>
      <div class="two-col">
        <div class="panel">
          <h2>Content candidates</h2>
          <div class="content-list">{render_content(payload['content_candidates'])}</div>
        </div>
        <div class="panel">
          <h2>Studio queue</h2>
          <div class="content-list">{render_studio(payload['studio_queue'])}</div>
        </div>
      </div>
    </section>

    <section id="sources" class="tab-panel">
      <div class="two-col">
        <div class="panel">
          <h2>Lead promotion recommendations</h2>
          <div class="content-list">{render_lead_promotions(payload['lead_promotion_recommendations'])}</div>
        </div>
        <div class="panel">
          <h2>Morning source discovery</h2>
          <div class="content-list">{render_source_discovery(payload['source_discovery_board'])}</div>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry readiness</h2>
        <div class="content-list">{render_source_registry_readiness_summary(payload['source_registry_readiness_summary'])}</div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source coverage map</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>League</th><th>Status</th><th>Official</th><th>Team</th><th>Wire</th><th>Cross-check</th><th>Gap</th><th>Next step</th></tr></thead>
            <tbody>{render_source_coverage(payload['source_coverage_map'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry intake template</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>League</th><th>Need</th><th>Gap</th><th>Type</th><th>Enabled</th><th>Action</th><th>Candidate URL</th></tr></thead>
            <tbody>{render_source_intake(payload['source_registry_intake_template'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry diff review</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Cue</th><th>Source ID</th><th>Domain</th><th>Flags</th><th>Issues</th><th>ID match</th><th>Domain match</th><th>Rollback</th><th>Before verification log</th></tr></thead>
            <tbody>{render_source_registry_diff_review(payload['source_registry_diff_review'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry same-domain resolution</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Decision</th><th>Source ID</th><th>Domain</th><th>Match</th><th>Compared source</th><th>Evidence</th><th>Requirement</th><th>Gate</th></tr></thead>
            <tbody>{render_source_registry_same_domain_resolution(payload['source_registry_same_domain_resolution'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source verification log</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Cue</th><th>Source ID</th><th>URL</th><th>Diff</th><th>Instruction</th><th>URL checked</th><th>Freshness</th><th>Duplicate decision</th><th>Approval outcome</th><th>Registry edit</th></tr></thead>
            <tbody>{render_source_registry_verification_log(payload['source_registry_verification_log'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry approval packet</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Source ID</th><th>URL</th><th>Evidence</th><th>Freshness</th><th>Duplicate</th><th>Hold reason</th><th>Exact JSON</th><th>Registry edit</th></tr></thead>
            <tbody>{render_source_registry_approval_packet(payload['source_registry_approval_packet'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry patch preview</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Source ID</th><th>Target</th><th>Before</th><th>Evidence</th><th>Hold reason</th><th>Copy JSON</th><th>Registry edit</th></tr></thead>
            <tbody>{render_source_registry_patch_preview(payload['source_registry_patch_preview'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry post-edit validation</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Source ID</th><th>Exact</th><th>Enabled</th><th>Automation</th><th>Publish</th><th>Free</th><th>Drift</th><th>Unsafe</th></tr></thead>
            <tbody>{render_source_registry_post_edit_validation(payload['source_registry_post_edit_validation'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source registry update worksheet</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Decision</th><th>Source ID</th><th>URL</th><th>Manual target</th><th>Edit allowed</th><th>Enabled</th><th>Auto edit</th><th>Before/after</th><th>Rollback</th></tr></thead>
            <tbody>{render_source_registry_update_worksheet(payload['source_registry_update_worksheet'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source proposal promotion checklist</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Decision</th><th>Operator step</th><th>Source ID</th><th>URL</th><th>Copy allowed</th><th>Copy target</th><th>Reason</th><th>Enabled</th><th>Registry action</th></tr></thead>
            <tbody>{render_source_proposal_promotion_checklist(payload['source_registry_proposal_promotion_checklist'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source proposal draft</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Pack</th><th>Source ID</th><th>URL</th><th>Draft action</th><th>Duplicate warning</th><th>Freshness warning</th><th>Enabled</th><th>Registry action</th></tr></thead>
            <tbody>{render_source_proposal_draft(payload['source_registry_proposal_draft'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Guided source pack readiness</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pack</th><th>Status</th><th>Rows</th><th>Official</th><th>Cross-check</th><th>Duplicates</th><th>Cues</th><th>Top candidates</th><th>Next step</th></tr></thead>
            <tbody>{render_source_proposal_pack_readiness(payload['source_proposal_pack_readiness'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Guided source proposal packs</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pack</th><th>Group</th><th>Priority</th><th>Source ID</th><th>Name</th><th>URL</th><th>Enabled</th><th>Action</th><th>Registry</th></tr></thead>
            <tbody>{render_source_proposal_packs(payload['source_proposal_packs'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source proposal review</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Candidate</th><th>URL</th><th>Status</th><th>Flags</th><th>Issues</th><th>Recommendation</th></tr></thead>
            <tbody>{render_source_proposal_review(payload['source_registry_proposal_review'])}</tbody>
          </table>
        </div>
      </div>
      <div class="panel" style="margin-top:16px">
        <h2>Source health</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Source</th><th>League</th><th>Date</th><th>OK</th><th>Events</th><th>Notes</th></tr></thead>
            <tbody>{render_sources(payload['source_health'])}</tbody>
          </table>
        </div>
      </div>
    </section>

    <section id="safety" class="tab-panel">
      {render_release_readiness_panel(payload.get('release_readiness_panel', {}))}
      <div class="two-col">
        <div class="panel">
          <h2>Blocks and review notes</h2>
          <div class="issue-list">{render_issues(payload['issues'])}</div>
        </div>
        <div class="panel">
          <h2>Source health</h2>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Source</th><th>League</th><th>Date</th><th>OK</th><th>Events</th><th>Notes</th></tr></thead>
              <tbody>{render_sources(payload['source_health'])}</tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <section id="artifacts" class="tab-panel">
      <div class="panel">
        <h2>Artifact desk</h2>
        <div class="artifact-toolbar">
          <input id="artifactSearch" type="search" placeholder="Filter artifacts">
          <select id="artifactGroup" aria-label="Artifact group">
            <option value="">All groups</option>
            <option value="decision">Decision</option>
            <option value="results">Results</option>
            <option value="news">News</option>
            <option value="studio">Studio</option>
            <option value="graphics">Graphics</option>
            <option value="review">Review</option>
          </select>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Group</th><th>Artifact</th><th>Path</th><th>Status</th><th>Next step</th><th>Open</th></tr></thead>
            <tbody>{render_artifacts(payload['artifacts'])}</tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
  <script>
    const buttons = Array.from(document.querySelectorAll("[data-tab-target]"));
    const jumps = Array.from(document.querySelectorAll("[data-tab-jump]"));
    const panels = Array.from(document.querySelectorAll(".tab-panel"));
    function activateTab(target) {{
      const selectedButton = buttons.find((button) => button.getAttribute("data-tab-target") === target);
      buttons.forEach((b) => b.setAttribute("aria-selected", String(b === selectedButton)));
        panels.forEach((panel) => panel.classList.toggle("active", panel.id === target));
      if (selectedButton) selectedButton.scrollIntoView({{ block: "nearest" }});
    }}
    buttons.forEach((button) => {{
      button.addEventListener("click", () => {{
        activateTab(button.getAttribute("data-tab-target"));
      }});
    }});
    jumps.forEach((button) => {{
      button.addEventListener("click", () => {{
        activateTab(button.getAttribute("data-tab-jump"));
      }});
    }});
    const search = document.getElementById("artifactSearch");
    const group = document.getElementById("artifactGroup");
    const rows = Array.from(document.querySelectorAll("[data-artifact-row]"));
    function filterArtifacts() {{
      const q = (search.value || "").trim().toLowerCase();
      const g = (group.value || "").trim().toLowerCase();
      rows.forEach((row) => {{
        const text = row.getAttribute("data-search") || "";
        const rowGroup = row.getAttribute("data-group") || "";
        row.style.display = (!q || text.includes(q)) && (!g || rowGroup === g) ? "" : "none";
      }});
    }}
    search.addEventListener("input", filterArtifacts);
    group.addEventListener("change", filterArtifacts);
    const decisionPanel = document.querySelector(".decision-ui");
    if (decisionPanel) {{
      const draft = JSON.parse(decisionPanel.getAttribute("data-decision-draft") || "{{}}");
      const fields = JSON.parse(decisionPanel.getAttribute("data-decision-fields") || "[]");
      const hasValidDecision = decisionPanel.getAttribute("data-has-valid-decision") === "true";
      let replacementTouched = false;
      const output = document.getElementById("decisionCsvOutput");
      const notes = document.getElementById("operatorNotes");
      const holdReason = document.getElementById("holdReason");
      const revisionRequest = document.getElementById("revisionRequest");
      const operatorName = document.getElementById("operatorName");
      const reviewedAt = document.getElementById("reviewedAtLocal");
      const copyButton = document.getElementById("copyDecisionRow");
      const copyStatus = document.getElementById("decisionCopyStatus");
      const warningList = document.getElementById("decisionFieldWarnings");
      const readyBadge = document.getElementById("decisionReadyBadge");
      if (reviewedAt && !reviewedAt.value) {{
        reviewedAt.value = new Date().toLocaleString();
      }}
      function csvCell(value) {{
        const text = String(value || "");
        return /[",\\n\\r]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
      }}
      function selectedDecision() {{
        const checked = document.querySelector('input[name="operatorDecision"]:checked');
        return checked ? checked.value : "hold";
      }}
      function replacementFormHasInput() {{
        return Boolean(
          notes.value.trim() ||
          holdReason.value.trim() ||
          revisionRequest.value.trim() ||
          operatorName.value.trim()
        );
      }}
      function currentWarnings() {{
        if (hasValidDecision && !replacementTouched && !replacementFormHasInput()) return [];
        const decision = selectedDecision();
        const warnings = [];
        if (!notes.value.trim()) warnings.push("Add operator notes describing what you checked by eye.");
        if (!operatorName.value.trim()) warnings.push("Add the operator name before copying.");
        if (!reviewedAt.value.trim()) warnings.push("Keep a reviewed-at time on the row.");
        if (decision === "hold" && !holdReason.value.trim()) warnings.push("Hold needs a hold reason.");
        if (decision === "revise" && !revisionRequest.value.trim()) warnings.push("Revise needs a revision request.");
        return warnings;
      }}
      function renderWarnings() {{
        if (!warningList || !readyBadge) return [];
        const warnings = currentWarnings();
        warningList.innerHTML = "";
        if (hasValidDecision && !replacementTouched && !replacementFormHasInput()) {{
          const item = document.createElement("li");
          item.className = "good";
          item.textContent = "A valid inbox decision is already recorded. Use this form only if you want to replace that decision.";
          warningList.appendChild(item);
          readyBadge.textContent = "No action needed";
          readyBadge.className = "pill good";
          return warnings;
        }}
        if (!warnings.length) {{
          const item = document.createElement("li");
          item.className = "good";
          item.textContent = "Ready to copy after you have opened the preview, QA report, copy sheet, and source proof.";
          warningList.appendChild(item);
          readyBadge.textContent = "Ready to copy";
          readyBadge.className = "pill good";
          return warnings;
        }}
        warnings.forEach((warning) => {{
          const item = document.createElement("li");
          item.textContent = warning;
          warningList.appendChild(item);
        }});
        readyBadge.textContent = warnings.length + " missing";
        readyBadge.className = "pill warn";
        return warnings;
      }}
      function buildDecisionRow() {{
        const decision = selectedDecision();
        const row = Object.assign({{}}, draft);
        row.operator_decision = decision;
        row.operator_notes = notes.value.trim();
        row.hold_reason = decision === "hold" ? holdReason.value.trim() : "";
        row.revision_request = decision === "revise" ? revisionRequest.value.trim() : "";
        row.operator_name = operatorName.value.trim();
        row.reviewed_at_local = reviewedAt.value.trim();
        row.copy_target = "operator/inbox/manual_visual_qa_operator_decisions.csv";
        row.approval_scope = "manual_next_step_only_not_publish_ready";
        row.publish_ready = "false";
        row.auto_approval = "false";
        row.auto_publish = "false";
        row.move_files = "false";
        row.paid_apis = "false";
        const header = fields.join(",");
        const values = fields.map((field) => csvCell(row[field]));
        output.value = header + "\\n" + values.join(",");
        renderWarnings();
      }}
      [notes, holdReason, revisionRequest, operatorName, reviewedAt].forEach((el) => {{
        if (el) el.addEventListener("input", () => {{
          replacementTouched = true;
          buildDecisionRow();
        }});
      }});
      document.querySelectorAll('input[name="operatorDecision"]').forEach((el) => el.addEventListener("change", () => {{
        replacementTouched = true;
        buildDecisionRow();
      }}));
      if (copyButton) {{
        copyButton.addEventListener("click", async () => {{
          replacementTouched = true;
          buildDecisionRow();
          const warnings = currentWarnings();
          if (warnings.length) {{
            copyStatus.textContent = "Fill the missing fields before copying a decision row.";
            return;
          }}
          try {{
            await navigator.clipboard.writeText(output.value.split("\\n").slice(1).join("\\n"));
            copyStatus.textContent = "Row copied. Paste below the header in operator/inbox/manual_visual_qa_operator_decisions.csv, then rerun render.";
          }} catch (err) {{
            output.focus();
            output.select();
            copyStatus.textContent = "Copy only the data row from the text box, then paste below the inbox header.";
          }}
        }});
      }}
      buildDecisionRow();
    }}
    const athletePhotoDesk = document.querySelector(".athlete-photo-desk");
    if (athletePhotoDesk) {{
      const rows = JSON.parse(athletePhotoDesk.getAttribute("data-athlete-photo-rows") || "[]");
      const fields = JSON.parse(athletePhotoDesk.getAttribute("data-athlete-photo-fields") || "[]");
      const output = document.getElementById("athletePhotoCsvOutput");
      const notes = document.getElementById("athletePhotoNotes");
      const identity = document.getElementById("athletePhotoIdentityVerified");
      const cropChoice = document.getElementById("athletePhotoCropChoice");
      const copyButton = document.getElementById("copyAthletePhotoRow");
      const copyStatus = document.getElementById("athletePhotoCopyStatus");
      const warningList = document.getElementById("athletePhotoWarnings");
      const readyBadge = document.getElementById("athletePhotoReadyBadge");
      const selectedSummary = document.getElementById("athletePhotoSelectedSummary");
      const identityFields = JSON.parse(athletePhotoDesk.getAttribute("data-identity-resolution-fields") || "[]");
      const identityOutput = document.getElementById("identityResolutionCsvOutput");
      const identityResolutionNotes = document.getElementById("identityResolutionNotes");
      const identityResolutionVerified = document.getElementById("identityResolutionVerified");
      const identityProviderVerified = document.getElementById("identityProviderVerified");
      const identityApprovedSourceUrl = document.getElementById("identityApprovedSourceUrl");
      const identitySecondarySourceUrl = document.getElementById("identitySecondarySourceUrl");
      const identityBackfillProviderId = document.getElementById("identityBackfillProviderId");
      const identityOperatorName = document.getElementById("identityOperatorName");
      const identityReviewedAtLocal = document.getElementById("identityReviewedAtLocal");
      const identityCopyButton = document.getElementById("copyIdentityResolutionRow");
      const identityCopyStatus = document.getElementById("identityResolutionCopyStatus");
      const identityWarningList = document.getElementById("identityResolutionWarnings");
      const identityReadyBadge = document.getElementById("identityResolutionReadyBadge");
      const identitySelectedSummary = document.getElementById("identityResolutionSelectedSummary");
      const identityWritebackMode = document.getElementById("identityWritebackMode");
      const identityWritebackEnabled = window.location.protocol === "http:" && ["127.0.0.1", "localhost"].includes(window.location.hostname);
      if (identityReviewedAtLocal && !identityReviewedAtLocal.value) {{
        identityReviewedAtLocal.value = new Date().toLocaleString();
      }}
      if (identityCopyButton && identityWritebackEnabled) {{
        identityCopyButton.textContent = "Save identity row";
      }}
      if (identityWritebackMode) {{
        identityWritebackMode.textContent = identityWritebackEnabled
          ? "Local save mode is active. Saving writes only to operator/inbox/wnba_athlete_identity_resolution.csv."
          : "File-opened dashboard is copy-safe. Run .\\hsd.cmd run -Mode identity-decision to open localhost save mode.";
      }}
      function csvCell(value) {{
        const text = String(value || "");
        return /[",\\n\\r]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
      }}
      function selectedAthleteRow() {{
        const checked = document.querySelector('input[name="athletePhotoRow"]:checked');
        const id = checked ? checked.value : "";
        return rows.find((row) => row.athlete_id === id) || rows[0] || {{}};
      }}
      function selectedPhotoDecision() {{
        const checked = document.querySelector('input[name="athletePhotoDecision"]:checked');
        return checked ? checked.value : "hold";
      }}
      function selectedIdentityDecision() {{
        const checked = document.querySelector('input[name="identityResolutionDecision"]:checked');
        return checked ? checked.value : "hold_identity";
      }}
      function athleteWarnings(row) {{
        const decision = selectedPhotoDecision();
        const warnings = [];
        if (!row.athlete_id) warnings.push("No athlete onboarding row is selected.");
        if (!identity.value) warnings.push("Choose whether identity was verified by eye.");
        if (String(row.identity_review_status || "").startsWith("hold_") && decision === "approve_variant_for_review_drafts") warnings.push("Identity audit says hold; resolve the audit issue before approving this crop for future review drafts.");
        if (decision === "approve_variant_for_review_drafts" && identity.value !== "yes") warnings.push("Approval for review drafts requires identity_verified = yes.");
        if (decision === "approve_variant_for_review_drafts" && String(row.variant_status || "") !== "review_variant_ready") warnings.push("Only review_variant_ready crops can be approved for future review drafts.");
        if (decision === "approve_variant_for_review_drafts" && Number(row.crop_readiness_score || 0) < 70) warnings.push("Crop score is below the review-ready threshold.");
        if (!notes.value.trim()) warnings.push("Add operator notes naming what source/contact sheet you checked.");
        if (decision === "revise_crop" && cropChoice.value === "hold_no_crop") warnings.push("Choose the crop that needs revision, or use Hold.");
        if (decision === "hold" && identity.value === "yes" && !notes.value.toLowerCase().includes("hold")) warnings.push("Hold is selected; notes should explain the hold reason.");
        return warnings;
      }}
      function renderAthleteWarnings(row) {{
        const warnings = athleteWarnings(row);
        warningList.innerHTML = "";
        if (!warnings.length) {{
          const item = document.createElement("li");
          item.className = "good";
          item.textContent = "Ready to copy a review-only athlete-photo decision row. This does not approve publishing or move files.";
          warningList.appendChild(item);
          readyBadge.textContent = "Ready to copy";
          readyBadge.className = "pill good";
          return warnings;
        }}
        warnings.forEach((warning) => {{
          const item = document.createElement("li");
          item.textContent = warning;
          warningList.appendChild(item);
        }});
        readyBadge.textContent = warnings.length + " missing";
        readyBadge.className = "pill warn";
        return warnings;
      }}
      function identityCandidate(row) {{
        const candidate = row.identity_resolution_candidate || {{}};
        if (candidate.athlete_id) return candidate;
        return {{
          athlete_id: row.athlete_id || "",
          display_name: row.athlete_name || "",
          team_id: row.team_id || "",
          provider_player_id: row.identity_provider_candidate || "",
          asset_path: row.source_headshot_path || "",
          approved_marker_path: "",
          highest_severity: row.identity_review_status || "review",
          issue_count: row.identity_issue_count || "",
          issue_codes: row.identity_issue_codes || "",
          audit_evidence: row.identity_evidence || "",
          recommended_operator_action: "manual_identity_resolution_required",
          allowed_decisions: "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only",
          copy_target: "operator/inbox/wnba_athlete_identity_resolution.csv",
          approval_scope: "review_only_identity_resolution_for_local_draft_renders",
          publish_ready: "false",
          auto_approval: "false",
          auto_publish: "false",
          move_files: "false",
          paid_apis: "false",
          review_only_policy: "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane"
        }};
      }}
      function identityStatusForDecision(decision) {{
        if (decision === "identity_verified_approved_for_review_renders") return "identity_verified";
        if (decision === "backfill_provider_id_only") return "provider_id_backfill_ready_identity_still_held";
        if (decision === "revise_asset") return "needs_asset_revision";
        return "held_for_identity_review";
      }}
      function identityWarnings(row) {{
        const decision = selectedIdentityDecision();
        const candidate = identityCandidate(row);
        const warnings = [];
        const sourceUrl = (identityApprovedSourceUrl.value || "").trim();
        const notesValue = (identityResolutionNotes.value || "").trim();
        const providerValue = (identityBackfillProviderId.value || "").trim() || (row.identity_provider_candidate || "");
        if (!row.athlete_id) warnings.push("Select an athlete row before preparing identity evidence.");
        if (!candidate.athlete_id) warnings.push("No identity-resolution candidate exists for this athlete.");
        if (!identityOperatorName.value.trim()) warnings.push("Add the operator name.");
        if (!identityReviewedAtLocal.value.trim()) warnings.push("Keep a reviewed-at time.");
        if (!notesValue) warnings.push("Add source-backed identity notes.");
        if (decision === "identity_verified_approved_for_review_renders") {{
          if (identityResolutionVerified.value !== "yes") warnings.push("Verify requires identity_verified = yes.");
          if (identityProviderVerified.value !== "yes" && !providerValue) warnings.push("Verify requires provider ID verification or a source-backed backfill ID.");
          if (!sourceUrl) warnings.push("Verify requires an approved source URL.");
        }}
        if (decision === "backfill_provider_id_only") {{
          if (!providerValue) warnings.push("Backfill ID requires a provider player ID.");
          if (!sourceUrl) warnings.push("Backfill ID requires the public source URL used to verify the ID.");
        }}
        if (decision === "hold_identity" && !notesValue.toLowerCase().includes("hold")) warnings.push("Hold notes should explain why identity remains held.");
        if (decision === "revise_asset" && !notesValue.toLowerCase().includes("revise")) warnings.push("Revise notes should explain what asset/source needs replacement.");
        return warnings;
      }}
      function renderIdentityWarnings(row) {{
        const warnings = identityWarnings(row);
        if (!identityWarningList || !identityReadyBadge) return warnings;
        identityWarningList.innerHTML = "";
        if (!warnings.length) {{
          const item = document.createElement("li");
          item.className = "good";
          item.textContent = selectedIdentityDecision() === "backfill_provider_id_only"
            ? "Ready to copy a provider-ID backfill row. This keeps photo-first rendering held."
            : "Ready to copy a source-backed identity row. Renderer still waits until the inbox file is saved and rerun.";
          identityWarningList.appendChild(item);
          identityReadyBadge.textContent = "Ready to copy";
          identityReadyBadge.className = "pill good";
          return warnings;
        }}
        warnings.forEach((warning) => {{
          const item = document.createElement("li");
          item.textContent = warning;
          identityWarningList.appendChild(item);
        }});
        identityReadyBadge.textContent = warnings.length + " missing";
        identityReadyBadge.className = "pill warn";
        return warnings;
      }}
      function buildAthletePhotoRow() {{
        const row = selectedAthleteRow();
        if (selectedSummary) {{
          selectedSummary.textContent = row.athlete_id
            ? `${{row.athlete_name}} / ${{row.team_id}} / crop ${{row.crop_readiness_score || "0"}}/100 / ${{row.variant_status || "review"}} / ${{row.identity_review_status || "identity review"}}`
            : "No athlete selected.";
        }}
        const out = {{}};
        fields.forEach((field) => out[field] = row[field] || "");
        out.allowed_decisions = "approve_variant_for_review_drafts|hold|revise_crop";
        out.operator_decision = selectedPhotoDecision();
        out.identity_verified = identity.value || "";
        out.crop_choice = cropChoice.value || "recommended_review_variant";
        out.operator_notes = notes.value.trim();
        out.approval_scope = "review_only_derivative_from_approved_headshot";
        out.publish_ready = "false";
        out.auto_approval = "false";
        out.auto_publish = "false";
        out.move_files = "false";
        out.paid_apis = "false";
        output.value = fields.join(",") + "\\n" + fields.map((field) => csvCell(out[field])).join(",");
        renderAthleteWarnings(row);
        buildIdentityResolutionRow();
      }}
      function buildIdentityResolutionRow() {{
        const row = selectedAthleteRow();
        const candidate = identityCandidate(row);
        const decision = selectedIdentityDecision();
        if (identitySelectedSummary) {{
          identitySelectedSummary.textContent = row.athlete_id
            ? `${{row.athlete_name}} / ${{row.team_id}} / ${{candidate.highest_severity || "review"}} / issues ${{candidate.issue_count || row.identity_issue_count || "0"}} / provider ${{(identityBackfillProviderId.value || row.identity_provider_candidate || candidate.provider_player_id || "missing")}}`
            : "No athlete selected.";
        }}
        if (identityBackfillProviderId && !identityBackfillProviderId.value && (row.identity_provider_candidate || candidate.provider_player_id)) {{
          identityBackfillProviderId.value = row.identity_provider_candidate || candidate.provider_player_id || "";
        }}
        const out = {{}};
        identityFields.forEach((field) => out[field] = candidate[field] || "");
        out.athlete_id = candidate.athlete_id || row.athlete_id || "";
        out.display_name = candidate.display_name || row.athlete_name || "";
        out.team_id = candidate.team_id || row.team_id || "";
        out.provider_player_id = candidate.provider_player_id || row.identity_provider_candidate || "";
        out.asset_path = candidate.asset_path || row.source_headshot_path || "";
        out.issue_codes = candidate.issue_codes || row.identity_issue_codes || "";
        out.audit_evidence = candidate.audit_evidence || row.identity_evidence || "";
        out.allowed_decisions = "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only";
        out.operator_decision = decision;
        out.identity_verified = identityResolutionVerified.value || "";
        out.provider_player_id_verified = identityProviderVerified.value || "";
        out.approved_source_url = identityApprovedSourceUrl.value.trim();
        out.secondary_source_url = identitySecondarySourceUrl.value.trim();
        out.backfill_provider_player_id = identityBackfillProviderId.value.trim();
        out.operator_notes = identityResolutionNotes.value.trim();
        out.operator_name = identityOperatorName.value.trim();
        out.reviewed_at_local = identityReviewedAtLocal.value.trim();
        out.issue_resolution_status = identityStatusForDecision(decision);
        out.copy_target = "operator/inbox/wnba_athlete_identity_resolution.csv";
        out.approval_scope = "review_only_identity_resolution_for_local_draft_renders";
        out.publish_ready = "false";
        out.auto_approval = "false";
        out.auto_publish = "false";
        out.move_files = "false";
        out.paid_apis = "false";
        out.review_only_policy = "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane";
        if (identityOutput) {{
          identityOutput.value = identityFields.join(",") + "\\n" + identityFields.map((field) => csvCell(out[field])).join(",");
        }}
        renderIdentityWarnings(row);
        return out;
      }}
      document.querySelectorAll('input[name="athletePhotoRow"], input[name="athletePhotoDecision"]').forEach((el) => {{
        el.addEventListener("change", buildAthletePhotoRow);
      }});
      document.querySelectorAll('input[name="identityResolutionDecision"]').forEach((el) => {{
        el.addEventListener("change", buildIdentityResolutionRow);
      }});
      [notes, identity, cropChoice].forEach((el) => {{
        if (el) el.addEventListener("input", buildAthletePhotoRow);
        if (el) el.addEventListener("change", buildAthletePhotoRow);
      }});
      [identityResolutionNotes, identityResolutionVerified, identityProviderVerified, identityApprovedSourceUrl, identitySecondarySourceUrl, identityBackfillProviderId, identityOperatorName, identityReviewedAtLocal].forEach((el) => {{
        if (el) el.addEventListener("input", buildIdentityResolutionRow);
        if (el) el.addEventListener("change", buildIdentityResolutionRow);
      }});
      if (copyButton) {{
        copyButton.addEventListener("click", async () => {{
          buildAthletePhotoRow();
          const warnings = athleteWarnings(selectedAthleteRow());
          if (warnings.length) {{
            copyStatus.textContent = "Resolve the missing identity/crop fields before copying.";
            return;
          }}
          try {{
            await navigator.clipboard.writeText(output.value.split("\\n").slice(1).join("\\n"));
            copyStatus.textContent = "Row copied. Paste into a manual copy of the athlete-photo decision template; no generated file was edited.";
          }} catch (err) {{
            output.focus();
            output.select();
            copyStatus.textContent = "Copy only the data row from the text box. Do not copy the header.";
          }}
        }});
      }}
      if (identityCopyButton) {{
        identityCopyButton.addEventListener("click", async () => {{
          const out = buildIdentityResolutionRow();
          const warnings = identityWarnings(selectedAthleteRow());
          if (warnings.length) {{
            identityCopyStatus.textContent = identityWritebackEnabled
              ? "Resolve the missing source-backed identity fields before saving."
              : "Resolve the missing source-backed identity fields before copying.";
            return;
          }}
          if (identityWritebackEnabled) {{
            try {{
              const response = await fetch("/api/identity-resolution", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ row: out }})
              }});
              const payload = await response.json();
              if (!response.ok || !payload.ok) {{
                identityCopyStatus.textContent = (payload.warnings || [payload.status || "Save failed"]).join(" ");
                return;
              }}
              identityCopyStatus.textContent = `Saved to ${{payload.inbox_path}}. Rows: ${{payload.rows_after}}. Rerun render to refresh identity gates.`;
              return;
            }} catch (err) {{
              identityCopyStatus.textContent = "Local save failed. Keep this localhost tab open and make sure identity-decision mode is still running.";
              return;
            }}
          }}
          try {{
            await navigator.clipboard.writeText(identityOutput.value.split("\\n").slice(1).join("\\n"));
            identityCopyStatus.textContent = "Identity row copied. Paste below the header in operator/inbox/wnba_athlete_identity_resolution.csv, then rerun render.";
          }} catch (err) {{
            identityOutput.focus();
            identityOutput.select();
            identityCopyStatus.textContent = "Copy only the data row from the text box. Do not copy the header.";
          }}
        }});
      }}
      buildAthletePhotoRow();
    }}
  </script>
</body>
</html>
"""
    return html_doc


def asset_blocker_markdown_line(item: Dict[str, Any]) -> str:
    fallback = clean(item.get("renderer_fallback_cue"))
    fallback_part = f" | fallback: {fallback}" if fallback else ""
    return (
        f"- Asset blocker: {item.get('asset_domain')} | {item.get('severity')} | {item.get('decision')} | "
        f"{item.get('entity_name')} | {item.get('finding')} | {item.get('asset_path')}{fallback_part} | "
        f"next: {item.get('manual_action')} | packet: {item.get('decision_lane') or 'manual_review'} / "
        f"{item.get('default_operator_decision') or 'review_required'} / {item.get('asset_readiness') or 'review_required'}"
    )


def render_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# HSD Daily Operator Command Center",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Version: {payload['version']}",
        "",
        "## Decision",
        "",
        f"- Current call: {payload['decision']['overall']}",
        f"- Publish allowed: {display_bool(payload['decision']['publish_allowed'])}",
        f"- Graphics handoff allowed: {display_bool(payload['decision']['graphics_handoff_allowed'])}",
        f"- Automation: {payload['decision']['automation']}",
        f"- Source mode: {payload['decision']['free_source_mode']}",
        "",
        "## Next actions",
        "",
    ]
    lines.extend(
        (
            f"{action['rank']}. [{action['status']}] {action['title']} - {action['detail']} "
            f"({action['artifact']})"
            f"{' Run: `' + action['command'] + '`.' if action.get('command') else ''}"
        )
        for action in payload["next_actions"]
    )
    lines += [
        "",
        "## Operator next-action synthesis",
        "",
        "- Review-only and artifact-only; this checklist does not fetch sources, download assets, approve anything, move files, or publish.",
    ]
    lines.extend(
        (
            f"{row['rank']}. {row['lane']} - {row['manual_step']} | "
            f"open: `{row['primary_artifact']}` | companion: `{row['companion_artifact']}` | "
            f"resolved: `{row.get('primary_resolved_path') or 'missing_or_not_generated'}` | "
            f"return fields: {row['operator_return_fields']} | status: {row['artifact_status']}"
        )
        for row in payload.get("operator_next_action_synthesis", [])
    )
    release_panel = payload.get("release_readiness_panel", {})
    lines += [
        "",
        "## Release-readiness evidence",
        "",
        f"- Status: {release_panel.get('status') or 'not_created'}",
        f"- Blockers: {release_panel.get('blocker_count', 0)}",
        f"- Latest guardrail scan: {release_panel.get('latest_scan_status') or 'not_run'}; files checked: {release_panel.get('latest_scan_files_checked', 0)}; violations: {release_panel.get('latest_scan_violations', 0)}",
        f"- Conductor audit: {release_panel.get('conductor_status') or 'not_run'}; collision blockers: {release_panel.get('conductor_collision_blockers', 0)}",
        f"- Workflow lane status: {release_panel.get('workflow_status') or 'not_run'}; stale brakes: {release_panel.get('workflow_stale_lanes', 0)}; restart-needed: {release_panel.get('workflow_restart_needed', 0)}; lifecycle actions: {release_panel.get('workflow_lifecycle_actions', 0)}",
        f"- Next step: {release_panel.get('next_step') or 'Run the release-readiness rollup before release review.'}",
        "- Artifact: `release_readiness_guardrail_rollup.md`",
    ]
    lines += ["", "## Render readiness", ""]
    lines.extend(
        f"- {item.get('rank') or '-'} | {item.get('band') or 'not_scored'} | score: {item.get('score') or '0'} | {item.get('title') or 'Untitled candidate'} | path: {item.get('recommended_path') or 'review'} | source: {item.get('source_cue') or 'n/a'} | assets: {item.get('asset_cue') or 'n/a'} | format: {item.get('format_cue') or 'n/a'} | manual: {item.get('manual_path') or 'n/a'} | blockers: {display_render_blockers(item)} | next: {item.get('next_step') or 'review manually'}"
        for item in payload["render_readiness_queue"]
    )
    lines += ["", "## Render prep packets", ""]
    lines.extend(
        f"- {item.get('packet_status') or 'review'} | score: {item.get('render_readiness_score') or '0'} | {item.get('title') or 'Untitled'} | template: {item.get('selected_template_id') or item.get('template_fit') or 'review'} | fit: {item.get('template_fit') or 'review'} | shape: {item.get('template_shape') or 'review'} | active asset stop/go: {item.get('active_asset_stop_go') or 'clear_no_active_asset_holds'} | active logo: {item.get('active_logo_readiness_status') or 'logo_review_not_flagged'} | logo cues: {item.get('active_logo_review_cues') or 'none'} | active athlete: {item.get('active_athlete_identity_status') or 'athlete_identity_not_flagged'} | athlete cues: {item.get('active_athlete_identity_cues') or 'none'} | closure cues: {item.get('active_athlete_identity_closure_cues') or 'none'} | artifact: render_prep_packets.md | gate: {item.get('approval_gate') or 'human review'}"
        for item in payload["render_prep_packets"]
    )
    stop_go = payload.get("decision_stop_go_summary", {})
    lines += [
        "",
        "## What Blocks This Render Now",
        "",
        f"- Status: {stop_go.get('panel_status') or 'not_run'}",
        f"- Active asset stop/go: {stop_go.get('active_asset_stop_go') or 'clear_no_active_asset_holds'}",
        f"- Selected-template blockers: {stop_go.get('selected_template_blockers', 0)} ({stop_go.get('selected_template_entities') or 'none'})",
        f"- Selected-template evidence gap: {stop_go.get('selected_template_evidence_gaps') or 'none'}",
        f"- Future photo-first holds: {stop_go.get('future_photo_first_holds', 0)} ({stop_go.get('future_photo_first_entities') or 'none'})",
        f"- League-mark context: {stop_go.get('league_mark_context_holds', 0)} ({stop_go.get('league_mark_context_entities') or 'none'})",
        f"- League-mark evidence gap: {stop_go.get('league_mark_evidence_gaps') or 'none'}",
        f"- Active queue: `{stop_go.get('active_queue_artifact') or 'render_handoff_top_packet/active_asset_review_queue.md'}`",
        f"- Manual source board: `{stop_go.get('manual_asset_source_board_artifact') or 'render_handoff_top_packet/manual_asset_source_board.md'}`",
        f"- Next safe action: {stop_go.get('next_step') or 'review manually'}",
        f"- Guardrails: {stop_go.get('guardrail_summary') or 'review-only'}",
    ]
    review_order = payload.get("decision_review_order_checklist", [])
    lines += [
        "",
        "## Open These In Order",
        "",
        "- This checklist is display-only and review-only; it does not approve assets or move files.",
    ]
    lines.extend(
        f"{item.get('rank')}. {item.get('title')} - {item.get('reason')} | artifact: `{item.get('artifact')}` | action: {item.get('operator_action')} | approval_change={item.get('approval_state_change')} | downloads={item.get('asset_downloads')} | publishing={item.get('publishing')}"
        for item in review_order
    )
    asset_panel = payload["asset_readiness_panel"]
    lines += [
        "",
        "## Asset Readiness Decision Desk",
        "",
        f"- Panel status: {asset_panel.get('panel_status') or 'not_run'}",
        f"- Findings: {asset_panel.get('finding_count', 0)} ({asset_panel.get('error_count', 0)} errors / {asset_panel.get('warning_count', 0)} warnings)",
        f"- Player-photo findings: {asset_panel.get('player_photo_findings', 0)}",
        f"- Team logo findings: {asset_panel.get('team_logo_findings', 0)}",
        f"- League mark findings: {asset_panel.get('league_logo_findings', 0)}",
        f"- Renderer findings: {asset_panel.get('renderer_findings', 0)}",
        f"- Logo review packets: {asset_panel.get('logo_review_packet_rows', 0)} ({asset_panel.get('logo_review_packet_unapproved_rows', 0)} unapproved / {asset_panel.get('logo_review_packet_source_drift_rows', 0)} source drift)",
        f"- Logo contact sheet rows: {asset_panel.get('logo_contact_sheet_rows', 0)}",
        f"- Women's soccer logo contact sheet rows: {asset_panel.get('womens_soccer_logo_contact_sheet_rows', 0)}",
        f"- Women's soccer logo review walkthrough rows: {asset_panel.get('womens_soccer_logo_review_walkthrough_rows', 0)}",
        f"- Women's soccer athlete photo candidate rows: {asset_panel.get('womens_soccer_athlete_photo_contact_sheet_rows', 0)}",
        f"- Women's soccer athlete official roster rows: {asset_panel.get('womens_soccer_athlete_photo_official_roster_candidate_rows', 0)}",
        f"- Women's soccer athlete photo team boards: {asset_panel.get('womens_soccer_athlete_photo_contact_sheet_team_boards', 0)}",
        f"- Women's soccer athlete starter rows: {asset_panel.get('womens_soccer_athlete_photo_starter_candidate_rows', 0)}",
        f"- Women's soccer athlete local candidate files present: {asset_panel.get('womens_soccer_athlete_photo_local_candidate_files_present', 0)}",
        f"- Women's soccer athlete photo packet generated: {asset_panel.get('womens_soccer_athlete_photo_contact_sheet_generated_at') or 'missing'}",
        f"- Women's soccer athlete photo warnings: {asset_panel.get('womens_soccer_athlete_photo_contact_sheet_warning_count', 0)}",
        f"- Women's soccer athlete operator board rows: {asset_panel.get('womens_soccer_athlete_operator_board_rows', 0)}",
        f"- Women's soccer athlete operator board generated: {asset_panel.get('womens_soccer_athlete_operator_board_generated_at') or 'missing'}",
        f"- Women's soccer athlete download intake rows: {asset_panel.get('womens_soccer_athlete_download_intake_rows', 0)}",
        f"- Women's soccer athlete download-approved yes rows: {asset_panel.get('womens_soccer_athlete_download_approved_yes_rows', 0)}",
        f"- Women's soccer athlete download intake generated: {asset_panel.get('womens_soccer_athlete_download_intake_generated_at') or 'missing'}",
        f"- Women's soccer athlete verification queue rows: {asset_panel.get('womens_soccer_athlete_verification_queue_rows', 0)}",
        f"- Women's soccer athlete verification queue NWSL rows: {asset_panel.get('womens_soccer_athlete_verification_queue_nwsl_rows', 0)}",
        f"- Women's soccer athlete verification queue Europe rows: {asset_panel.get('womens_soccer_athlete_verification_queue_europe_rows', 0)}",
        f"- Women's soccer athlete verification queue P0 NWSL rows: {asset_panel.get('womens_soccer_athlete_verification_queue_p0_nwsl_rows', 0)}",
        f"- Women's soccer athlete verification queue missing local candidate rows: {asset_panel.get('womens_soccer_athlete_verification_queue_missing_local_candidate_rows', 0)}",
        f"- Women's soccer athlete verification queue generated: {asset_panel.get('womens_soccer_athlete_verification_queue_generated_at') or 'missing'}",
        f"- Women's soccer athlete verification next-action rows: {asset_panel.get('womens_soccer_athlete_next_actions_rows', 0)}",
        f"- Women's soccer athlete verification next-action download-approved yes rows: {asset_panel.get('womens_soccer_athlete_next_actions_download_approved_yes_rows', 0)}",
        f"- Women's soccer athlete verification next-action blank source-url rows: {asset_panel.get('womens_soccer_athlete_next_actions_blank_source_url_rows', 0)}",
        f"- Women's soccer athlete verification next-action generated: {asset_panel.get('womens_soccer_athlete_next_actions_generated_at') or 'missing'}",
        f"- Women's soccer athlete source-priority rows: {asset_panel.get('womens_soccer_athlete_source_priority_rows', 0)}",
        f"- Women's soccer athlete source-priority NWSL rows: {asset_panel.get('womens_soccer_athlete_source_priority_nwsl_rows', 0)}",
        f"- Women's soccer athlete source-priority Europe rows: {asset_panel.get('womens_soccer_athlete_source_priority_europe_rows', 0)}",
        f"- Women's soccer athlete source-priority verify rows: {asset_panel.get('womens_soccer_athlete_source_priority_verify_rows', 0)}",
        f"- Women's soccer athlete source-priority gray/reputable rows: {asset_panel.get('womens_soccer_athlete_source_priority_gray_rows', 0)}",
        f"- Women's soccer athlete source-priority generated: {asset_panel.get('womens_soccer_athlete_source_priority_generated_at') or 'missing'}",
        f"- Women's soccer athlete review triage rows: {asset_panel.get('womens_soccer_athlete_review_triage_rows', 0)}",
        f"- Women's soccer athlete review triage NWSL rows: {asset_panel.get('womens_soccer_athlete_review_triage_nwsl_rows', 0)}",
        f"- Women's soccer athlete review triage Europe rows: {asset_panel.get('womens_soccer_athlete_review_triage_europe_rows', 0)}",
        f"- Women's soccer athlete review triage download-approved yes rows: {asset_panel.get('womens_soccer_athlete_review_triage_download_approved_yes_rows', 0)}",
        f"- Women's soccer athlete review triage blank source-url rows: {asset_panel.get('womens_soccer_athlete_review_triage_blank_source_url_rows', 0)}",
        f"- Women's soccer athlete review triage generated: {asset_panel.get('womens_soccer_athlete_review_triage_generated_at') or 'missing'}",
        f"- Women's soccer athlete candidate next-action rows: {asset_panel.get('womens_soccer_athlete_candidate_actions_rows', 0)}",
        f"- Women's soccer athlete candidate next-action NWSL rows: {asset_panel.get('womens_soccer_athlete_candidate_actions_nwsl_rows', 0)}",
        f"- Women's soccer athlete candidate next-action Europe rows: {asset_panel.get('womens_soccer_athlete_candidate_actions_europe_rows', 0)}",
        f"- Women's soccer athlete candidate next-action download-approved yes rows: {asset_panel.get('womens_soccer_athlete_candidate_actions_download_approved_yes_rows', 0)}",
        f"- Women's soccer athlete candidate next-action blank source-url rows: {asset_panel.get('womens_soccer_athlete_candidate_actions_blank_source_url_rows', 0)}",
        f"- Women's soccer athlete candidate next-action generated: {asset_panel.get('womens_soccer_athlete_candidate_actions_generated_at') or 'missing'}",
        f"- Women's soccer athlete photo readiness rows: {asset_panel.get('womens_soccer_athlete_photo_readiness_rows', 0)}",
        f"- Women's soccer athlete photo readiness NWSL rows: {asset_panel.get('womens_soccer_athlete_photo_readiness_nwsl_rows', 0)}",
        f"- Women's soccer athlete photo readiness Europe rows: {asset_panel.get('womens_soccer_athlete_photo_readiness_europe_rows', 0)}",
        f"- Women's soccer athlete photo readiness download-approved yes rows: {asset_panel.get('womens_soccer_athlete_photo_readiness_download_approved_yes_rows', 0)}",
        f"- Women's soccer athlete photo readiness blank source-url rows: {asset_panel.get('womens_soccer_athlete_photo_readiness_blank_source_url_rows', 0)}",
        f"- Women's soccer athlete photo readiness generated: {asset_panel.get('womens_soccer_athlete_photo_readiness_generated_at') or 'missing'}",
        f"- Women's soccer athlete operator focus rows: {asset_panel.get('womens_soccer_athlete_operator_focus_rows', 0)}",
        f"- Women's soccer athlete operator focus P0 rows: {asset_panel.get('womens_soccer_athlete_operator_focus_p0_rows', 0)}",
        f"- Women's soccer athlete operator focus identity manual-verification rows: {asset_panel.get('womens_soccer_athlete_operator_focus_identity_manual_verification_rows', 0)}",
        f"- Women's soccer athlete operator focus generated: {asset_panel.get('womens_soccer_athlete_operator_focus_generated_at') or 'missing'}",
        f"- Women's soccer action-photo research-next rows: {asset_panel.get('womens_soccer_action_photo_research_next_rows', 0)}",
        f"- Women's soccer action-photo research-next blank source_url rows: {asset_panel.get('womens_soccer_action_photo_research_next_blank_source_url_rows', 0)}",
        f"- Women's soccer action-photo research-next blank rights/identity rows: {asset_panel.get('womens_soccer_action_photo_research_next_blank_rights_class_rows', 0)}/{asset_panel.get('womens_soccer_action_photo_research_next_blank_identity_confidence_rows', 0)}",
        f"- Women's soccer action-photo research-next download-approved yes rows: {asset_panel.get('womens_soccer_action_photo_research_next_download_approved_yes_rows', 0)}",
        f"- Women's soccer action-photo research-next candidate-ready rows: {asset_panel.get('womens_soccer_action_photo_research_next_candidate_ready_rows', 0)}",
        f"- Women's soccer action-photo research-next asset/headshot/marker writes: {asset_panel.get('womens_soccer_action_photo_research_next_asset_downloads', False)}/{asset_panel.get('womens_soccer_action_photo_research_next_headshot_writes', False)}/{asset_panel.get('womens_soccer_action_photo_research_next_approved_marker_writes', False)}",
        f"- Women's soccer action-photo research-next generated: {asset_panel.get('womens_soccer_action_photo_research_next_generated_at') or 'missing'}",
        f"- Women's soccer athlete closure summary rows: {asset_panel.get('womens_soccer_athlete_closure_rows', 0)}",
        f"- Women's soccer athlete closure referenced rows: {asset_panel.get('womens_soccer_athlete_closure_total_referenced_rows', 0)}",
        f"- Women's soccer athlete closure P0/verify rows: {asset_panel.get('womens_soccer_athlete_closure_p0_or_verify_rows', 0)}",
        f"- Women's soccer athlete closure gray-area rows: {asset_panel.get('womens_soccer_athlete_closure_gray_area_rows', 0)}",
        f"- Women's soccer athlete closure download-approved yes rows: {asset_panel.get('womens_soccer_athlete_closure_download_approved_yes_rows', 0)}",
        f"- Women's soccer athlete closure generated: {asset_panel.get('womens_soccer_athlete_closure_generated_at') or 'missing'}",
        f"- Women's soccer external research rows: {asset_panel.get('womens_soccer_external_research_rows', 0)}",
        f"- Women's soccer external research NWSL rows: {asset_panel.get('womens_soccer_external_research_nwsl_rows', 0)}",
        f"- Women's soccer external research Europe rows: {asset_panel.get('womens_soccer_external_research_europe_rows', 0)}",
        f"- Women's soccer external research P0 NWSL rows: {asset_panel.get('womens_soccer_external_research_p0_nwsl_rows', 0)}",
        f"- Women's soccer external research gray-area rows: {asset_panel.get('womens_soccer_external_research_gray_area_rows', 0)}",
        f"- Women's soccer external research Sam Kerr gray-area only: {asset_panel.get('womens_soccer_external_research_sam_kerr_gray_area_only', False)}",
        f"- Women's soccer external research generated: {asset_panel.get('womens_soccer_external_research_generated_at') or 'missing'}",
        f"- Action-photo candidate intake rows: {asset_panel.get('action_photo_candidate_intake_rows', 0)}",
        f"- Action-photo candidate queue rows: {asset_panel.get('action_photo_candidate_queue_rows', 0)}",
        f"- Action-photo sport/entity source-map board rows: {asset_panel.get('action_photo_source_map_board_rows', 0)}",
        f"- Action-photo sport/entity source-map blank operator-decision rows: {asset_panel.get('action_photo_source_map_board_blank_operator_decision_rows', 0)}",
        f"- Action-photo sport/entity source-map download-approved yes rows: {asset_panel.get('action_photo_source_map_board_download_approved_yes_rows', 0)}",
        f"- Action-photo sport/entity source-map fetch/auto-enable/auto-approve: {asset_panel.get('action_photo_source_map_board_source_fetching', False)}/{asset_panel.get('action_photo_source_map_board_auto_source_enablement', False)}/{asset_panel.get('action_photo_source_map_board_auto_approval', False)}",
        f"- Action-photo sport/entity source-map generated: {asset_panel.get('action_photo_source_map_board_generated_at') or 'missing'}",
        f"- Action-photo manual source-hunt rows: {asset_panel.get('action_photo_manual_source_hunt_rows', 0)}",
        f"- Action-photo manual source-hunt blank source_url rows: {asset_panel.get('action_photo_manual_source_hunt_blank_source_url_rows', 0)}",
        f"- Action-photo manual source-hunt download-approved yes rows: {asset_panel.get('action_photo_manual_source_hunt_download_approved_yes_rows', 0)}",
        f"- Action-photo manual source-hunt fetch/auto-enable/auto-approve: {asset_panel.get('action_photo_manual_source_hunt_source_fetching', False)}/{asset_panel.get('action_photo_manual_source_hunt_auto_source_enablement', False)}/{asset_panel.get('action_photo_manual_source_hunt_auto_approval', False)}",
        f"- Action-photo manual source-hunt asset/headshot/marker writes: {asset_panel.get('action_photo_manual_source_hunt_asset_downloads', False)}/{asset_panel.get('action_photo_manual_source_hunt_headshot_writes', False)}/{asset_panel.get('action_photo_manual_source_hunt_approved_marker_writes', False)}",
        f"- Action-photo manual source-hunt generated: {asset_panel.get('action_photo_manual_source_hunt_generated_at') or 'missing'}",
        f"- Action-photo operator worksheet rows: {asset_panel.get('action_photo_operator_worksheet_rows', 0)}",
        f"- Action-photo operator worksheet blank candidate-url rows: {asset_panel.get('action_photo_operator_worksheet_blank_candidate_url_rows', 0)}",
        f"- Action-photo operator worksheet blank source-url rows: {asset_panel.get('action_photo_operator_worksheet_blank_source_url_rows', 0)}",
        f"- Action-photo operator worksheet blank reviewer-decision rows: {asset_panel.get('action_photo_operator_worksheet_blank_reviewer_decision_rows', 0)}",
        f"- Action-photo operator worksheet download-approved yes rows: {asset_panel.get('action_photo_operator_worksheet_download_approved_yes_rows', 0)}",
        f"- Action-photo operator worksheet not-in-quarantine rows: {asset_panel.get('action_photo_operator_worksheet_not_in_quarantine_rows', 0)}",
        f"- Action-photo operator worksheet asset/headshot/marker writes: {asset_panel.get('action_photo_operator_worksheet_asset_downloads', False)}/{asset_panel.get('action_photo_operator_worksheet_headshot_writes', False)}/{asset_panel.get('action_photo_operator_worksheet_approved_marker_writes', False)}",
        f"- Action-photo operator worksheet generated: {asset_panel.get('action_photo_operator_worksheet_generated_at') or 'missing'}",
        f"- Action-photo research packet rows: {asset_panel.get('action_photo_research_packet_rows', 0)}",
        f"- Action-photo research return intake rows: {asset_panel.get('action_photo_research_return_intake_rows', 0)}",
        f"- Action-photo research return pasted rows: {asset_panel.get('action_photo_research_return_rows_with_pasted_data', 0)}",
        f"- Action-photo research return validation issues: {asset_panel.get('action_photo_research_return_validation_issues', 0)}",
        f"- Action-photo research return blank candidate-photo-url rows: {asset_panel.get('action_photo_research_return_blank_candidate_photo_url_rows', 0)}",
        f"- Action-photo research return blank source_url rows: {asset_panel.get('action_photo_research_return_blank_source_url_rows', 0)}",
        f"- Action-photo research return blank rights_class rows: {asset_panel.get('action_photo_research_return_blank_rights_class_rows', 0)}",
        f"- Action-photo research return operator-verify rows: {asset_panel.get('action_photo_research_return_operator_verify_required_yes_rows', 0)}",
        f"- Action-photo research return download-approved yes rows: {asset_panel.get('action_photo_research_return_download_approved_yes_rows', 0)}",
        f"- Action-photo research return generated: {asset_panel.get('action_photo_research_return_generated_at') or 'missing'}",
        f"- Action-photo research return paste worksheet rows: {asset_panel.get('action_photo_research_return_paste_worksheet_rows', 0)}",
        f"- Action-photo research return paste worksheet candidate-ready rows: {asset_panel.get('action_photo_research_return_paste_worksheet_ready_rows', 0)}",
        f"- Action-photo research return paste worksheet blank source_url rows: {asset_panel.get('action_photo_research_return_paste_worksheet_blank_source_url_rows', 0)}",
        f"- Action-photo research return paste worksheet download-approved yes rows: {asset_panel.get('action_photo_research_return_paste_worksheet_download_approved_yes_rows', 0)}",
        f"- Action-photo research return paste worksheet asset/headshot/marker writes: {asset_panel.get('action_photo_research_return_paste_worksheet_asset_downloads', False)}/{asset_panel.get('action_photo_research_return_paste_worksheet_headshot_writes', False)}/{asset_panel.get('action_photo_research_return_paste_worksheet_approved_marker_writes', False)}",
        f"- Action-photo research return paste worksheet generated: {asset_panel.get('action_photo_research_return_paste_worksheet_generated_at') or 'missing'}",
        f"- Action-photo research run bundle rows: {asset_panel.get('action_photo_research_run_bundle_rows', 0)}",
        f"- Action-photo research run bundle download-approved yes rows: {asset_panel.get('action_photo_research_run_bundle_download_approved_yes_rows', 0)}",
        f"- Action-photo research run bundle generated: {asset_panel.get('action_photo_research_run_bundle_generated_at') or 'missing'}",
        f"- Action-photo quarantine preflight rows: {asset_panel.get('action_photo_quarantine_preflight_rows', 0)}",
        f"- Action-photo quarantine ready-for-human-download-decision rows: {asset_panel.get('action_photo_quarantine_preflight_ready_for_human_download_decision_rows', 0)}",
        f"- Action-photo quarantine lead-only rows: {asset_panel.get('action_photo_quarantine_preflight_lead_only_rows', 0)}",
        f"- Action-photo quarantine download-approved yes rows: {asset_panel.get('action_photo_quarantine_preflight_download_approved_yes_rows', 0)}",
        f"- Action-photo quarantine missing source_url rows: {asset_panel.get('action_photo_quarantine_preflight_missing_source_url_rows', 0)}",
        f"- Action-photo quarantine preflight generated: {asset_panel.get('action_photo_quarantine_preflight_generated_at') or 'missing'}",
        f"- Action-photo quality/fit board rows: {asset_panel.get('action_photo_quality_fit_rows', 0)}",
        f"- Action-photo quality/fit source_url present rows: {asset_panel.get('action_photo_quality_fit_source_url_present_rows', 0)}",
        f"- Action-photo quality/fit rights_class present rows: {asset_panel.get('action_photo_quality_fit_rights_class_present_rows', 0)}",
        f"- Action-photo quality/fit ready-for-human-download-decision rows: {asset_panel.get('action_photo_quality_fit_ready_for_human_download_decision_rows', 0)}",
        f"- Action-photo quality/fit download-approved yes rows: {asset_panel.get('action_photo_quality_fit_download_approved_yes_rows', 0)}",
        f"- Action-photo quality/fit asset/headshot/marker writes: {asset_panel.get('action_photo_quality_fit_asset_downloads', False)}/{asset_panel.get('action_photo_quality_fit_headshot_writes', False)}/{asset_panel.get('action_photo_quality_fit_approved_marker_writes', False)}",
        f"- Action-photo quality/fit generated: {asset_panel.get('action_photo_quality_fit_generated_at') or 'missing'}",
        f"- Action-photo quality/fit operator cue rows: {asset_panel.get('action_photo_quality_fit_operator_cue_rows', 0)}",
        f"- Action-photo quality/fit operator cue missing source_url rows: {asset_panel.get('action_photo_quality_fit_operator_cue_source_url_missing_rows', 0)}",
        f"- Action-photo quality/fit operator cue missing identity rows: {asset_panel.get('action_photo_quality_fit_operator_cue_identity_metadata_missing_rows', 0)}",
        f"- Action-photo quality/fit operator cue missing action/crop rows: {asset_panel.get('action_photo_quality_fit_operator_cue_action_metadata_missing_rows', 0)}/{asset_panel.get('action_photo_quality_fit_operator_cue_crop_metadata_missing_rows', 0)}",
        f"- Action-photo quality/fit operator cue eligible rows: {asset_panel.get('action_photo_quality_fit_operator_cue_eligible_rows', 0)}",
        f"- Action-photo quality/fit operator cue generated downloads: {asset_panel.get('action_photo_quality_fit_operator_cue_asset_downloads', False)}",
        f"- Action-photo quality/fit operator cue generated: {asset_panel.get('action_photo_quality_fit_operator_cue_generated_at') or 'missing'}",
        f"- Action-photo download decision queue rows: {asset_panel.get('action_photo_download_decision_rows', 0)}",
        f"- Action-photo download decision ready rows: {asset_panel.get('action_photo_download_decision_ready_rows', 0)}",
        f"- Action-photo download decision download-approved yes rows: {asset_panel.get('action_photo_download_decision_download_approved_yes_rows', 0)}",
        f"- Action-photo download decision generated asset/marker writes: {asset_panel.get('action_photo_download_decision_asset_downloads', False)}/{asset_panel.get('action_photo_download_decision_approved_marker_writes', False)}",
        f"- Action-photo download decision generated: {asset_panel.get('action_photo_download_decision_generated_at') or 'missing'}",
        f"- WNBA hero action-photo target rows: {asset_panel.get('action_photo_hero_targets_rows', 0)}",
        f"- WNBA hero action-photo target download-approved yes rows: {asset_panel.get('action_photo_hero_targets_download_approved_yes_rows', 0)}",
        f"- WNBA hero action-photo target blank source_url rows: {asset_panel.get('action_photo_hero_targets_blank_source_url_rows', 0)}",
        f"- WNBA hero action-photo target blank candidate-photo-url rows: {asset_panel.get('action_photo_hero_targets_blank_candidate_photo_url_rows', 0)}",
        f"- WNBA hero action-photo target operator-verify rows: {asset_panel.get('action_photo_hero_targets_operator_verify_required_yes_rows', 0)}",
        f"- WNBA hero action-photo targets generated: {asset_panel.get('action_photo_hero_targets_generated_at') or 'missing'}",
        f"- Action-photo cutout readiness rows: {asset_panel.get('action_photo_cutout_readiness_rows', 0)}",
        f"- Action-photo cutout readiness download-approved yes rows: {asset_panel.get('action_photo_cutout_readiness_download_approved_yes_rows', 0)}",
        f"- Action-photo cutout readiness blank source_url rows: {asset_panel.get('action_photo_cutout_readiness_blank_source_url_rows', 0)}",
        f"- Action-photo cutout readiness blank candidate-photo-url rows: {asset_panel.get('action_photo_cutout_readiness_blank_candidate_photo_url_rows', 0)}",
        f"- Action-photo cutout readiness blank cutout-work rows: {asset_panel.get('action_photo_cutout_readiness_blank_cutout_work_required_rows', 0)}",
        f"- Action-photo cutout readiness segmentation: {asset_panel.get('action_photo_cutout_readiness_segmentation', False)}",
        f"- Action-photo cutout readiness background removal: {asset_panel.get('action_photo_cutout_readiness_background_removal', False)}",
        f"- Action-photo cutout readiness cutout file writes: {asset_panel.get('action_photo_cutout_readiness_cutout_file_writes', False)}",
        f"- Action-photo cutout readiness generated: {asset_panel.get('action_photo_cutout_readiness_generated_at') or 'missing'}",
        f"- Women's hockey logo contact sheet rows: {asset_panel.get('womens_hockey_logo_contact_sheet_rows', 0)}",
        f"- Women's hockey athlete photo candidate rows: {asset_panel.get('womens_hockey_athlete_photo_contact_sheet_rows', 0)}",
        f"- Women's hockey athlete source-review slot rows: {asset_panel.get('womens_hockey_athlete_photo_source_review_slot_rows', 0)}",
        f"- Women's hockey walkthrough rows: {asset_panel.get('womens_hockey_review_walkthrough_rows', 0)}",
        f"- Women's hockey workflow rows: {asset_panel.get('womens_hockey_asset_workflow_rows', 0)}",
        f"- Women's hockey proposed headshot path refs: {asset_panel.get('womens_hockey_proposed_headshot_path_refs', 0)}",
        f"- Softball logo contact sheet rows: {asset_panel.get('softball_logo_contact_sheet_rows', 0)}",
        f"- Softball athlete photo candidate rows: {asset_panel.get('softball_athlete_photo_contact_sheet_rows', 0)}",
        f"- Softball athlete source-review slot rows: {asset_panel.get('softball_athlete_photo_source_review_slot_rows', 0)}",
        f"- Softball walkthrough rows: {asset_panel.get('softball_review_walkthrough_rows', 0)}",
        f"- Softball workflow rows: {asset_panel.get('softball_asset_workflow_rows', 0)}",
        f"- Softball proposed headshot path refs: {asset_panel.get('softball_proposed_headshot_path_refs', 0)}",
        f"- Hockey/softball asset foundation generated: {asset_panel.get('hockey_softball_asset_foundation_generated_at') or 'missing'}",
        f"- Hockey/softball foundation coverage rows: {asset_panel.get('hockey_softball_foundation_coverage_rows', 0)}",
        f"- Hockey/softball foundation source rows: {asset_panel.get('hockey_softball_foundation_coverage_source_rows', 0)}",
        f"- Hockey/softball foundation logo contact rows: {asset_panel.get('hockey_softball_foundation_coverage_logo_contact_rows', 0)}",
        f"- Hockey/softball foundation athlete candidate rows: {asset_panel.get('hockey_softball_foundation_coverage_athlete_candidate_rows', 0)}",
        f"- Hockey/softball foundation coverage generated: {asset_panel.get('hockey_softball_foundation_coverage_generated_at') or 'missing'}",
        f"- Hockey/softball source review helper generated: {asset_panel.get('hockey_softball_source_review_helper_generated_at') or 'missing'}",
        f"- Hockey/softball asset workflow generated: {asset_panel.get('hockey_softball_asset_workflow_generated_at') or 'missing'}",
        f"- Hockey/softball asset review action queue rows: {asset_panel.get('hockey_softball_asset_review_action_queue_rows', 0)}",
        f"- Hockey/softball source-candidate-only rows: {asset_panel.get('hockey_softball_asset_review_action_queue_source_candidate_only_rows', 0)}",
        f"- Hockey/softball local asset present rows: {asset_panel.get('hockey_softball_asset_review_action_queue_local_asset_present_rows', 0)}",
        f"- Hockey/softball asset review action queue generated: {asset_panel.get('hockey_softball_asset_review_action_queue_generated_at') or 'missing'}",
        f"- Hockey/softball batch source review helper rows: {asset_panel.get('hockey_softball_batch_source_review_rows', 0)}",
        f"- Hockey/softball source-review-now rows: {asset_panel.get('hockey_softball_batch_source_review_now_rows', 0)}",
        f"- Hockey/softball next batch rows: {asset_panel.get('hockey_softball_batch_source_review_next_rows', 0)}",
        f"- Hockey/softball local asset needed later rows: {asset_panel.get('hockey_softball_batch_source_review_local_asset_needed_later_rows', 0)}",
        f"- Hockey/softball batch source review helper generated: {asset_panel.get('hockey_softball_batch_source_review_generated_at') or 'missing'}",
        f"- Hockey/softball next decision worksheet rows: {asset_panel.get('hockey_softball_next_decision_worksheet_rows', 0)}",
        f"- Hockey/softball next decision logo rows: {asset_panel.get('hockey_softball_next_decision_worksheet_logo_rows', 0)}",
        f"- Hockey/softball next decision athlete rows: {asset_panel.get('hockey_softball_next_decision_worksheet_athlete_rows', 0)}",
        f"- Hockey/softball next decision missing-local rows: {asset_panel.get('hockey_softball_next_decision_worksheet_missing_local_rows', 0)}",
        f"- Hockey/softball next decision download-approved yes rows: {asset_panel.get('hockey_softball_next_decision_worksheet_download_approved_yes_rows', 0)}",
        f"- Hockey/softball next decision blank download-metadata rows: {asset_panel.get('hockey_softball_next_decision_worksheet_blank_download_metadata_rows', 0)}",
        f"- Hockey/softball next decision worksheet generated: {asset_panel.get('hockey_softball_next_decision_worksheet_generated_at') or 'missing'}",
        f"- Hockey/softball source priority rows: {asset_panel.get('hockey_softball_source_priority_rows', 0)}",
        f"- Hockey/softball source priority operator-verify rows: {asset_panel.get('hockey_softball_source_priority_operator_verify_rows', 0)}",
        f"- Hockey/softball source priority download-approved yes rows: {asset_panel.get('hockey_softball_source_priority_download_approved_yes_rows', 0)}",
        f"- Hockey/softball source priority blank source_url rows: {asset_panel.get('hockey_softball_source_priority_blank_source_url_rows', 0)}",
        f"- Hockey/softball source priority generated: {asset_panel.get('hockey_softball_source_priority_generated_at') or 'missing'}",
        f"- Hockey/softball source verification checklist rows: {asset_panel.get('hockey_softball_source_verification_rows', 0)}",
        f"- Hockey/softball source verification hockey rows: {asset_panel.get('hockey_softball_source_verification_womens_hockey_rows', 0)}",
        f"- Hockey/softball source verification softball rows: {asset_panel.get('hockey_softball_source_verification_softball_rows', 0)}",
        f"- Hockey/softball source verification download-approved yes rows: {asset_panel.get('hockey_softball_source_verification_download_approved_yes_rows', 0)}",
        f"- Hockey/softball source verification blank source_url rows: {asset_panel.get('hockey_softball_source_verification_blank_source_url_rows', 0)}",
        f"- Hockey/softball source verification blank human-review rows: {asset_panel.get('hockey_softball_source_verification_blank_human_review_rows', 0)}",
        f"- Hockey/softball source verification generated: {asset_panel.get('hockey_softball_source_verification_generated_at') or 'missing'}",
        f"- Hockey/softball intake readiness groups: {asset_panel.get('hockey_softball_intake_readiness_groups', 0)}",
        f"- Hockey/softball intake readiness rows covered: {asset_panel.get('hockey_softball_intake_readiness_rows_covered', 0)}",
        f"- Hockey/softball intake readiness logo source-reviewed rows: {asset_panel.get('hockey_softball_intake_readiness_logo_source_reviewed_rows', 0)}",
        f"- Hockey/softball intake readiness athlete source-pending rows: {asset_panel.get('hockey_softball_intake_readiness_athlete_source_pending_rows', 0)}",
        f"- Hockey/softball intake readiness blank human-review metadata rows: {asset_panel.get('hockey_softball_intake_readiness_blank_human_review_metadata_rows', 0)}",
        f"- Hockey/softball intake readiness unsafe guardrail rows: {asset_panel.get('hockey_softball_intake_readiness_unsafe_guardrail_rows', 0)}",
        f"- Hockey/softball intake readiness download-approved yes rows: {asset_panel.get('hockey_softball_intake_readiness_download_approved_yes_rows', 0)}",
        f"- Hockey/softball intake readiness generated: {asset_panel.get('hockey_softball_intake_readiness_generated_at') or 'missing'}",
        f"- Hockey/softball source map rows: {asset_panel.get('hockey_softball_source_map_rows', 0)}",
        f"- Hockey/softball source map hockey rows: {asset_panel.get('hockey_softball_source_map_womens_hockey_rows', 0)}",
        f"- Hockey/softball source map softball rows: {asset_panel.get('hockey_softball_source_map_softball_rows', 0)}",
        f"- Hockey/softball source map official/free rows: {asset_panel.get('hockey_softball_source_map_official_free_public_rows', 0)}",
        f"- Hockey/softball source map allowed-for-download rows: {asset_panel.get('hockey_softball_source_map_allowed_for_download_approved_yes_rows', 0)}",
        f"- Hockey/softball source map download-approved yes rows: {asset_panel.get('hockey_softball_source_map_download_approved_yes_rows', 0)}",
        f"- Hockey/softball source map blank source_url rows: {asset_panel.get('hockey_softball_source_map_blank_source_url_rows', 0)}",
        f"- Hockey/softball source map generated: {asset_panel.get('hockey_softball_source_map_generated_at') or 'missing'}",
        f"- Hockey/softball action-photo handoff rows: {asset_panel.get('hockey_softball_action_photo_handoff_rows', 0)}",
        f"- Hockey/softball action-photo handoff blank source_url rows: {asset_panel.get('hockey_softball_action_photo_handoff_blank_source_url_rows', 0)}",
        f"- Hockey/softball action-photo handoff download-approved yes rows: {asset_panel.get('hockey_softball_action_photo_handoff_download_approved_yes_rows', 0)}",
        f"- Hockey/softball action-photo handoff later human download-decision rows: {asset_panel.get('hockey_softball_action_photo_handoff_ready_rows', 0)}",
        f"- Hockey/softball action-photo handoff asset/headshot/marker writes: {asset_panel.get('hockey_softball_action_photo_handoff_asset_downloads', False)}/{asset_panel.get('hockey_softball_action_photo_handoff_headshot_writes', False)}/{asset_panel.get('hockey_softball_action_photo_handoff_approved_marker_writes', False)}",
        f"- Hockey/softball action-photo handoff generated: {asset_panel.get('hockey_softball_action_photo_handoff_generated_at') or 'missing'}",
        f"- Hockey/softball source research return rows: {asset_panel.get('hockey_softball_source_research_return_rows', 0)}",
        f"- Hockey/softball source research return blank operator rows: {asset_panel.get('hockey_softball_source_research_return_blank_operator_rows', 0)}",
        f"- Hockey/softball source research return download-approved yes rows: {asset_panel.get('hockey_softball_source_research_return_download_approved_yes_rows', 0)}",
        f"- Hockey/softball source research return generated: {asset_panel.get('hockey_softball_source_research_return_generated_at') or 'missing'}",
        f"- Hockey/softball asset review triage rows: {asset_panel.get('hockey_softball_asset_review_triage_rows', 0)}",
        f"- Hockey/softball asset review triage logo rows: {asset_panel.get('hockey_softball_asset_review_triage_logo_rows', 0)}",
        f"- Hockey/softball asset review triage athlete rows: {asset_panel.get('hockey_softball_asset_review_triage_athlete_rows', 0)}",
        f"- Hockey/softball asset review triage operator-verify source rows: {asset_panel.get('hockey_softball_asset_review_triage_operator_verify_source_rows', 0)}",
        f"- Hockey/softball asset review triage download-approved yes rows: {asset_panel.get('hockey_softball_asset_review_triage_download_approved_yes_rows', 0)}",
        f"- Hockey/softball asset review triage blank source_url rows: {asset_panel.get('hockey_softball_asset_review_triage_blank_source_url_rows', 0)}",
        f"- Hockey/softball asset review triage generated: {asset_panel.get('hockey_softball_asset_review_triage_generated_at') or 'missing'}",
        f"- Hockey/softball asset review readiness rows: {asset_panel.get('hockey_softball_asset_review_readiness_rows', 0)}",
        f"- Hockey/softball asset review readiness logo rows: {asset_panel.get('hockey_softball_asset_review_readiness_logo_rows', 0)}",
        f"- Hockey/softball asset review readiness athlete rows: {asset_panel.get('hockey_softball_asset_review_readiness_athlete_rows', 0)}",
        f"- Hockey/softball asset review readiness download-approved yes rows: {asset_panel.get('hockey_softball_asset_review_readiness_download_approved_yes_rows', 0)}",
        f"- Hockey/softball asset review readiness blank source_url rows: {asset_panel.get('hockey_softball_asset_review_readiness_blank_source_url_rows', 0)}",
        f"- Hockey/softball asset review readiness source/identity gap rows: {asset_panel.get('hockey_softball_asset_review_readiness_source_identity_gap_rows', 0)}",
        f"- Hockey/softball asset review readiness team/entity check rows: {asset_panel.get('hockey_softball_asset_review_readiness_team_entity_check_rows', 0)}",
        f"- Hockey/softball asset review readiness local candidate gap rows: {asset_panel.get('hockey_softball_asset_review_readiness_local_candidate_gap_rows', 0)}",
        f"- Hockey/softball asset review readiness generated: {asset_panel.get('hockey_softball_asset_review_readiness_generated_at') or 'missing'}",
        f"- Hockey/softball manual verification focus rows: {asset_panel.get('hockey_softball_manual_verification_focus_rows', 0)}",
        f"- Hockey/softball manual verification focus P0 rows: {asset_panel.get('hockey_softball_manual_verification_focus_p0_rows', 0)}",
        f"- Hockey/softball manual verification focus P1 rows: {asset_panel.get('hockey_softball_manual_verification_focus_p1_rows', 0)}",
        f"- Hockey/softball manual verification focus asset-readiness rows: {asset_panel.get('hockey_softball_manual_verification_focus_asset_readiness_rows', 0)}",
        f"- Hockey/softball manual verification focus source-map rows: {asset_panel.get('hockey_softball_manual_verification_focus_source_map_rows', 0)}",
        f"- Hockey/softball manual verification focus download-approved yes rows: {asset_panel.get('hockey_softball_manual_verification_focus_download_approved_yes_rows', 0)}",
        f"- Hockey/softball manual verification focus generated: {asset_panel.get('hockey_softball_manual_verification_focus_generated_at') or 'missing'}",
        f"- Hockey/softball asset next-action card rows: {asset_panel.get('hockey_softball_asset_next_action_cards_rows', 0)}",
        f"- Hockey/softball asset next-action card logo rows: {asset_panel.get('hockey_softball_asset_next_action_cards_logo_rows', 0)}",
        f"- Hockey/softball asset next-action card athlete rows: {asset_panel.get('hockey_softball_asset_next_action_cards_athlete_rows', 0)}",
        f"- Hockey/softball asset next-action card download-approved yes rows: {asset_panel.get('hockey_softball_asset_next_action_cards_download_approved_yes_rows', 0)}",
        f"- Hockey/softball asset next-action card blank source_url rows: {asset_panel.get('hockey_softball_asset_next_action_cards_blank_source_url_rows', 0)}",
        f"- Hockey/softball asset next-action cards generated: {asset_panel.get('hockey_softball_asset_next_action_cards_generated_at') or 'missing'}",
        f"- Hockey/softball quarantine download intake rows: {asset_panel.get('hockey_softball_quarantine_download_intake_rows', 0)}",
        f"- Hockey/softball quarantine download logo rows: {asset_panel.get('hockey_softball_quarantine_download_intake_logo_rows', 0)}",
        f"- Hockey/softball quarantine download athlete rows: {asset_panel.get('hockey_softball_quarantine_download_intake_athlete_rows', 0)}",
        f"- Hockey/softball quarantine download-approved yes rows: {asset_panel.get('hockey_softball_quarantine_download_approved_yes_rows', 0)}",
        f"- Hockey/softball quarantine download intake generated: {asset_panel.get('hockey_softball_quarantine_download_intake_generated_at') or 'missing'}",
        packet_freshness_markdown(
            {
                "status": asset_panel.get("logo_review_packet_freshness_status"),
                "detail": asset_panel.get("logo_review_packet_freshness_detail"),
                "run_command": asset_panel.get("logo_review_packet_refresh_command"),
            },
            "Logo review",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("logo_contact_sheet_freshness_status"),
                "detail": asset_panel.get("logo_contact_sheet_freshness_detail"),
                "run_command": asset_panel.get("logo_contact_sheet_refresh_command"),
            },
            "Logo contact sheet",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_logo_contact_sheet_freshness_status"),
                "detail": asset_panel.get("womens_soccer_logo_contact_sheet_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_logo_contact_sheet_refresh_command"),
            },
            "Women's soccer logo contact sheet",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_logo_review_walkthrough_freshness_status"),
                "detail": asset_panel.get("womens_soccer_logo_review_walkthrough_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_logo_review_walkthrough_refresh_command"),
            },
            "Women's soccer logo review walkthrough",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_photo_contact_sheet_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_photo_contact_sheet_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_photo_contact_sheet_refresh_command"),
            },
            "Women's soccer athlete photo contact sheets",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_operator_board_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_operator_board_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_operator_board_refresh_command"),
            },
            "Women's soccer athlete operator board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_download_intake_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_download_intake_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_download_intake_refresh_command"),
            },
            "Women's soccer athlete photo download intake",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_verification_queue_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_verification_queue_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_verification_queue_refresh_command"),
            },
            "Women's soccer athlete verification queue",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_next_actions_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_next_actions_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_next_actions_refresh_command"),
            },
            "Women's soccer athlete verification next actions",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_source_priority_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_source_priority_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_source_priority_refresh_command"),
            },
            "Women's soccer athlete source priority",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_review_triage_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_review_triage_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_review_triage_refresh_command"),
            },
            "Women's soccer athlete review triage",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_candidate_actions_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_candidate_actions_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_candidate_actions_refresh_command"),
            },
            "Women's soccer athlete candidate next-action board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_photo_readiness_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_photo_readiness_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_photo_readiness_refresh_command"),
            },
            "Women's soccer athlete photo review readiness board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_operator_focus_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_operator_focus_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_operator_focus_refresh_command"),
            },
            "Women's soccer athlete operator focus",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_action_photo_research_next_freshness_status"),
                "detail": asset_panel.get("womens_soccer_action_photo_research_next_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_action_photo_research_next_refresh_command"),
            },
            "Women's soccer action-photo research next",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_athlete_closure_freshness_status"),
                "detail": asset_panel.get("womens_soccer_athlete_closure_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_athlete_closure_refresh_command"),
            },
            "Women's soccer athlete expansion closure summary",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("womens_soccer_external_research_freshness_status"),
                "detail": asset_panel.get("womens_soccer_external_research_freshness_detail"),
                "run_command": asset_panel.get("womens_soccer_external_research_refresh_command"),
            },
            "Women's soccer external research intake",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_research_run_bundle_freshness_status"),
                "detail": asset_panel.get("action_photo_research_run_bundle_freshness_detail"),
                "run_command": asset_panel.get("action_photo_research_run_bundle_refresh_command"),
            },
            "Action-photo research run bundle",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_research_return_paste_worksheet_freshness_status"),
                "detail": asset_panel.get("action_photo_research_return_paste_worksheet_freshness_detail"),
                "run_command": asset_panel.get("action_photo_research_return_paste_worksheet_refresh_command"),
            },
            "Action-photo research return paste worksheet",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_manual_source_hunt_freshness_status"),
                "detail": asset_panel.get("action_photo_manual_source_hunt_freshness_detail"),
                "run_command": asset_panel.get("action_photo_manual_source_hunt_refresh_command"),
            },
            "Action-photo manual source-hunt board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_quarantine_preflight_freshness_status"),
                "detail": asset_panel.get("action_photo_quarantine_preflight_freshness_detail"),
                "run_command": asset_panel.get("action_photo_quarantine_preflight_refresh_command"),
            },
            "Action-photo quarantine preflight",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_quality_fit_freshness_status"),
                "detail": asset_panel.get("action_photo_quality_fit_freshness_detail"),
                "run_command": asset_panel.get("action_photo_quality_fit_refresh_command"),
            },
            "Action-photo candidate quality/fit board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_quality_fit_operator_cue_freshness_status"),
                "detail": asset_panel.get("action_photo_quality_fit_operator_cue_freshness_detail"),
                "run_command": asset_panel.get("action_photo_quality_fit_operator_cue_refresh_command"),
            },
            "Action-photo quality/fit operator cue",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_hero_targets_freshness_status"),
                "detail": asset_panel.get("action_photo_hero_targets_freshness_detail"),
                "run_command": asset_panel.get("action_photo_hero_targets_refresh_command"),
            },
            "WNBA hero action-photo targets",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("action_photo_cutout_readiness_freshness_status"),
                "detail": asset_panel.get("action_photo_cutout_readiness_freshness_detail"),
                "run_command": asset_panel.get("action_photo_cutout_readiness_refresh_command"),
            },
            "Action-photo cutout readiness",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_asset_foundation_freshness_status"),
                "detail": asset_panel.get("hockey_softball_asset_foundation_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_asset_foundation_refresh_command"),
            },
            "Hockey/softball asset foundation",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_foundation_coverage_freshness_status"),
                "detail": asset_panel.get("hockey_softball_foundation_coverage_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_foundation_coverage_refresh_command"),
            },
            "Hockey/softball foundation coverage index",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_source_review_helper_freshness_status"),
                "detail": asset_panel.get("hockey_softball_source_review_helper_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_source_review_helper_refresh_command"),
            },
            "Hockey/softball source review helper",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_asset_workflow_freshness_status"),
                "detail": asset_panel.get("hockey_softball_asset_workflow_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_asset_workflow_refresh_command"),
            },
            "Hockey/softball asset workflow readiness",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_asset_review_action_queue_freshness_status"),
                "detail": asset_panel.get("hockey_softball_asset_review_action_queue_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_asset_review_action_queue_refresh_command"),
            },
            "Hockey/softball asset review action queue",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_batch_source_review_freshness_status"),
                "detail": asset_panel.get("hockey_softball_batch_source_review_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_batch_source_review_refresh_command"),
            },
            "Hockey/softball batch source review helper",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_next_decision_worksheet_freshness_status"),
                "detail": asset_panel.get("hockey_softball_next_decision_worksheet_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_next_decision_worksheet_refresh_command"),
            },
            "Hockey/softball next decision worksheet",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_source_priority_freshness_status"),
                "detail": asset_panel.get("hockey_softball_source_priority_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_source_priority_refresh_command"),
            },
            "Hockey/softball source priority worksheet",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_source_verification_freshness_status"),
                "detail": asset_panel.get("hockey_softball_source_verification_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_source_verification_refresh_command"),
            },
            "Hockey/softball source verification checklist",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_intake_readiness_freshness_status"),
                "detail": asset_panel.get("hockey_softball_intake_readiness_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_intake_readiness_refresh_command"),
            },
            "Hockey/softball intake readiness summary",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_source_map_freshness_status"),
                "detail": asset_panel.get("hockey_softball_source_map_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_source_map_refresh_command"),
            },
            "Hockey/softball source map board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_action_photo_handoff_freshness_status"),
                "detail": asset_panel.get("hockey_softball_action_photo_handoff_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_action_photo_handoff_refresh_command"),
            },
            "Hockey/softball action-photo research handoff",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_source_research_return_freshness_status"),
                "detail": asset_panel.get("hockey_softball_source_research_return_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_source_research_return_refresh_command"),
            },
            "Hockey/softball source research return intake",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_asset_review_triage_freshness_status"),
                "detail": asset_panel.get("hockey_softball_asset_review_triage_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_asset_review_triage_refresh_command"),
            },
            "Hockey/softball asset review triage",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_asset_review_readiness_freshness_status"),
                "detail": asset_panel.get("hockey_softball_asset_review_readiness_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_asset_review_readiness_refresh_command"),
            },
            "Hockey/softball asset review readiness board",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_manual_verification_focus_freshness_status"),
                "detail": asset_panel.get("hockey_softball_manual_verification_focus_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_manual_verification_focus_refresh_command"),
            },
            "Hockey/softball manual verification focus",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_asset_next_action_cards_freshness_status"),
                "detail": asset_panel.get("hockey_softball_asset_next_action_cards_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_asset_next_action_cards_refresh_command"),
            },
            "Hockey/softball asset next-action cards",
        ),
        packet_freshness_markdown(
            {
                "status": asset_panel.get("hockey_softball_quarantine_download_intake_freshness_status"),
                "detail": asset_panel.get("hockey_softball_quarantine_download_intake_freshness_detail"),
                "run_command": asset_panel.get("hockey_softball_quarantine_download_intake_refresh_command"),
            },
            "Hockey/softball quarantine download intake",
        ),
        f"- Next safe action: {asset_panel.get('next_step')}",
        "- Guardrails: review-only, no paid APIs, no asset downloads, no auto-approval, no file movement, no publishing, no publish-ready lane.",
    ]
    lines.extend(
        asset_blocker_markdown_line(item)
        for item in asset_panel.get("top_findings", [])[:8]
    )
    lines.extend(
        f"- Logo packet: {item.get('team_name') or item.get('team_id')} | {item.get('issue_type') or 'logo_review_required'} | {item.get('decision_packet_title') or item.get('packet_id')} | registered={item.get('registered_path') or item.get('registered_logo_path') or item.get('local_logo_path') or item.get('recommended_path') or 'missing'} | source={item.get('source_target_path') or item.get('source_path') or item.get('target_path') or 'missing'} | fallback={item.get('renderer_fallback_cue') or 'Renderer fallback remains review-only.'} | next: {item.get('primary_action') or item.get('decision_primary_action') or 'manual logo review required'}"
        for item in asset_panel.get("logo_review_packets", [])[:8]
    )
    source_board = payload.get("manual_asset_source_board", [])
    lines += [
        "",
        "## Manual Asset Source Board",
        "",
        f"- Source-board rows: {len(source_board)}",
        f"- P0 selected-template holds: {sum(1 for item in source_board if clean(item.get('priority')) == 'P0_selected_template_hold')}",
        f"- Future photo-first holds: {sum(1 for item in source_board if clean(item.get('priority')) == 'P1_future_photo_first_hold')}",
        f"- League-mark context rows: {sum(1 for item in source_board if clean(item.get('priority')) == 'P2_league_mark_context')}",
        "- Legacy reference: `D:\\Her Sports Daily` asset-index/DDG packet structure only; current board is review-only.",
        "- Guardrails: no downloads, no auto-approval, no file movement, no publishing, no publish-ready lane.",
    ]
    lines.extend(
        f"- Source board row: {item.get('priority')} | {item.get('asset_domain')} | {item.get('entity_name') or item.get('entity_id')} | required={item.get('required_asset')} | source={item.get('official_source_candidate')} | current_registry_source={item.get('current_registry_source') or 'missing'} | evidence_gap={item.get('evidence_gap_status') or 'manual_evidence_review_required'} | local_state={item.get('local_asset_state') or 'manual_review_required'} | cannot_clear={item.get('cannot_clear_automatically_because') or 'manual evidence review required'} | query={item.get('manual_search_query')} | local={item.get('current_local_asset') or 'missing'} | packet={item.get('manual_review_packet') or 'n/a'} | copy={item.get('operator_copy_target') or 'n/a'} | downloads={item.get('asset_downloads')} | approval={item.get('auto_approval')} | publish_ready={item.get('publish_ready')}"
        for item in source_board[:8]
    )
    logo_intake = payload.get("manual_logo_verification_intake", [])
    lines += [
        "",
        "## Manual Logo Verification Intake Bridge",
        "",
        f"- Intake bridge rows: {len(logo_intake)}",
        "- Artifact: `render_handoff_top_packet/manual_logo_verification_intake.md`",
        "- Data: `render_handoff_top_packet/manual_logo_verification_intake.csv`",
        "- Guardrails: review-only, approval_state_change=false, no downloads, no auto-approval, no file movement, no publishing, no publish-ready lane.",
    ]
    lines.extend(
        f"- Logo intake row: {item.get('entity_name') or item.get('entity_id')} | local={item.get('local_logo_path') or 'missing'} | official={item.get('official_source_candidate') or 'manual lookup required'} | current_legacy_source={item.get('current_legacy_registry_source') or 'missing'} | status={item.get('current_unapproved_status') or 'manual_review_required'} | human_files={item.get('manual_intake_files')} | approval_change={item.get('approval_state_change')} | downloads={item.get('asset_downloads')} | publish_ready={item.get('publish_ready')}"
        for item in logo_intake[:8]
    )
    league_mark_intake = payload.get("manual_league_mark_context_intake", [])
    lines += [
        "",
        "## Manual League-Mark Context Intake",
        "",
        f"- Intake bridge rows: {len(league_mark_intake)}",
        "- Artifact: `render_handoff_top_packet/manual_league_mark_context_intake.md`",
        "- Data: `render_handoff_top_packet/manual_league_mark_context_intake.csv`",
        "- Human-edited intake file: `data/asset_registry/wnba/wnba_league_mark_review_intake.csv`",
        "- Selected-template rule: WNBA league mark is optional/non-blocking unless the selected template explicitly requires it.",
        "- Guardrails: review-only, approval_state_change=false, no downloads, no auto-approval, no file movement, no publishing, no publish-ready lane.",
    ]
    lines.extend(
        f"- League-mark intake row: {item.get('entity_name') or item.get('entity_id')} | local={item.get('local_league_mark_path') or 'missing'} | official={item.get('official_source_candidate') or 'manual lookup required'} | current_registry_source={item.get('current_registry_source') or 'missing'} | status={item.get('current_approval_status') or 'manual_review_required'} | template_rule={item.get('template_requirement_rule')} | human_file={item.get('manual_intake_files')} | approval_change={item.get('approval_state_change')} | downloads={item.get('asset_downloads')} | publish_ready={item.get('publish_ready')}"
        for item in league_mark_intake[:8]
    )
    athlete_photo_panel = payload["athlete_photo_onboarding_panel"]
    lines += [
        "",
        "## Athlete Photo Onboarding Decision Desk",
        "",
        f"- Panel status: {athlete_photo_panel.get('panel_status') or 'not_run'}",
        f"- Manifest status: {athlete_photo_panel.get('manifest_status') or 'not_run'}",
        f"- Review variants: {athlete_photo_panel.get('review_variant_ready', 0)}/{athlete_photo_panel.get('source_rows', 0)}",
        f"- Contact sheets: {athlete_photo_panel.get('contact_sheets', 0)}",
        f"- Athlete source boards: {athlete_photo_panel.get('athlete_contact_sheet_teams', 0)} team board(s) / {athlete_photo_panel.get('athlete_contact_sheet_rows', 0)} athlete row(s)",
        f"- Athlete source board intake rows: {athlete_photo_panel.get('athlete_contact_sheet_intake_rows', 0)}",
        f"- Identity audit: {athlete_photo_panel.get('identity_audit_status') or 'not_run'} ({athlete_photo_panel.get('identity_audit_issue_rows', 0)} issue row(s))",
        f"- Identity resolution: {athlete_photo_panel.get('identity_resolution_status') or 'not_run'} ({athlete_photo_panel.get('identity_resolution_inbox_rows', 0)} inbox row(s))",
        f"- Identity review packets: {athlete_photo_panel.get('identity_review_packet_rows', 0)} ({athlete_photo_panel.get('identity_review_packet_hold_rows', 0)} holds / {athlete_photo_panel.get('identity_review_packet_default_rows', 0)} default approvals)",
        packet_freshness_markdown(
            {
                "status": athlete_photo_panel.get("identity_review_packet_freshness_status"),
                "detail": athlete_photo_panel.get("identity_review_packet_freshness_detail"),
                "run_command": athlete_photo_panel.get("identity_review_packet_refresh_command"),
            },
            "Identity review",
        ),
        packet_freshness_markdown(
            {
                "status": athlete_photo_panel.get("athlete_contact_sheet_freshness_status"),
                "detail": athlete_photo_panel.get("athlete_contact_sheet_freshness_detail"),
                "run_command": athlete_photo_panel.get("athlete_contact_sheet_refresh_command"),
            },
            "Athlete photo contact sheets",
        ),
        f"- Closure/backfill: {athlete_photo_panel.get('identity_closure_status') or 'not_run'} ({athlete_photo_panel.get('identity_closure_rows', 0)}/{athlete_photo_panel.get('identity_provider_backfill_rows', 0)} row(s))",
        f"- Closure detail: high/critical={athlete_photo_panel.get('identity_closure_high_rows', 0)} | blank closure decisions={athlete_photo_panel.get('identity_closure_blank_decisions', 0)} | manual backfill review={athlete_photo_panel.get('identity_provider_backfill_manual_review_rows', 0)} | blank backfill decisions={athlete_photo_panel.get('identity_provider_backfill_blank_decisions', 0)}",
        f"- Closure next safe action: {athlete_photo_panel.get('identity_closure_next_step') or 'Open the manual closure packet only after source evidence review.'}",
        f"- Featured athlete: {athlete_photo_panel.get('featured_athlete_name') or athlete_photo_panel.get('featured_athlete_id') or 'none'}",
        f"- Next safe action: {athlete_photo_panel.get('next_step')}",
        "- Guardrails: review-only, identity human-check required, no auto-approval, no publishing, no file movement, no paid APIs.",
    ]
    lines.extend(
        f"- Closure severity: {item.get('label') or 'unknown'}={item.get('rows') or 0}"
        for item in athlete_photo_panel.get("identity_closure_severity_counts", [])[:6]
    )
    lines.extend(
        f"- Closure issue: {item.get('label') or 'unknown'}={item.get('rows') or 0}"
        for item in athlete_photo_panel.get("identity_closure_issue_counts", [])[:6]
    )
    lines.extend(
        f"- Provider backfill status: {item.get('label') or 'unknown'}={item.get('rows') or 0}"
        for item in athlete_photo_panel.get("identity_provider_backfill_status_counts", [])[:6]
    )
    lines.extend(
        f"- Provider backfill target: {item.get('label') or 'unknown'}={item.get('rows') or 0}"
        for item in athlete_photo_panel.get("identity_provider_backfill_target_counts", [])[:6]
    )
    lines.extend(
        f"- Identity team queue: {item.get('team_id') or 'unknown_team'} | packets={item.get('packet_rows') or 0} | holds={item.get('identity_hold_rows') or 0} | defaults={item.get('default_approval_rows') or 0} | high={item.get('high_severity_rows') or 0}"
        for item in athlete_photo_panel.get("identity_review_packet_teams", [])[:12]
    )
    lines.extend(
        f"- Identity packet: {item.get('display_name') or item.get('athlete_id')} | {item.get('team_id')} | {item.get('identity_review_status')} | hold={item.get('identity_hold')} | default={item.get('default_approval_present')} | reasons={item.get('hold_reason_codes') or 'manual_identity_review_required'} | evidence={item.get('focused_evidence') or 'source evidence required'} | steps={item.get('operator_review_steps') or 'open_asset_and_marker; compare_to_source; record_decision'} | source={item.get('source_check_url') or item.get('provider_player_page_hint') or 'missing'}"
        for item in athlete_photo_panel.get("identity_review_packets", [])[:8]
    )
    lines.extend(
        f"- Athlete row: {item.get('athlete_name')} | {item.get('team_id')} | crop {item.get('crop_readiness_score')}/100 | {item.get('identity_review_status')} | issues: {item.get('identity_issue_codes') or 'none'} | {item.get('recommended_review_variant_path')}"
        for item in athlete_photo_panel.get("review_rows", [])[:8]
    )
    decision_panel = payload["operator_decision_panel"]
    lines += [
        "",
        "## Manual Visual QA Decision UI",
        "",
        f"- Panel status: {decision_panel.get('panel_status') or 'not_ready'}",
        f"- QA status: {decision_panel.get('qa_status') or 'not_ready'}",
        f"- Validation: {decision_panel.get('validation_status') or decision_panel.get('intake_status') or 'awaiting'}",
        f"- Preview: {decision_panel.get('preview_path') or 'missing'}",
        f"- Inbox: {decision_panel.get('inbox_path')} ({decision_panel.get('inbox_rows')} row(s))",
        f"- History issues: {decision_panel.get('history_issue_count', 0)}",
        f"- Next safe action: {decision_panel.get('next_step')}",
        "- Guardrails: file-backed manual approval, no auto-approval, no publishing, no file movement, no paid APIs.",
    ]
    lines.extend(
        f"- Render gallery: {item.get('label')} | {item.get('shape')} | {item.get('review_status')} | delta={item.get('visual_delta_score') or '0'} ({item.get('visual_delta_band') or 'not_scored'}) | revision={item.get('revision_priority') or 'not_planned'} | focus={item.get('revision_focus') or 'n/a'} | {item.get('path')} | publish_ready={item.get('publish_ready')}"
        for item in decision_panel.get("render_gallery", [])
    )
    lines.extend(
        f"- Open: {item.get('label')} -> {item.get('path')} ({'found' if item.get('exists') else 'missing'})"
        for item in decision_panel.get("file_shortcuts", [])
    )
    lines.extend(
        f"- History row {item.get('row_number')}: {item.get('row_status')} | {item.get('operator_decision')} | {item.get('validation_status')} | next: {item.get('next_step')}"
        for item in decision_panel.get("decision_history", [])
    )
    handoff = payload["render_handoff_summary"]
    lines += ["", "## Top render handoff", ""]
    lines.extend(
        [
            f"- Status: {clean(handoff.get('handoff_status')) or 'not_created'}",
            f"- Story: {clean(handoff.get('title')) or 'none'}",
            f"- Folder: {clean(handoff.get('folder')) or 'render_handoff_top_packet'}",
            f"- Open first: {clean(handoff.get('readme')) or 'render_handoff_top_packet/README.md'}",
            "- Guardrails: review-only, no paid APIs, no auto-runs, no auto-rendering, no publishing.",
        ]
    )
    lines += ["", "## Content candidates", ""]
    lines.extend(
        f"- {item['type']} | {item['priority']} | {item['headline']} | {item['status']} | source: {item.get('source_grade') or 'not_scored'} | render: {item.get('render_readiness_score') or 'n/a'}/100 | {item.get('render_readiness_band') or 'not_scored'} | manual: {item.get('render_readiness_manual_path') or 'n/a'}"
        for item in payload["content_candidates"]
    )
    lines += ["", "## Lead promotion recommendations", ""]
    lines.extend(
        f"- {item['rank']} | {item['priority']} | {item['recommendation']} | quality: {item.get('quality_score') or 'n/a'} | {item.get('freshness_label') or 'undated'}{(' via ' + item.get('freshness_source')) if item.get('freshness_source') else ''} | opportunity: {item.get('story_opportunity_size') or '1'} source(s) | angle: {item.get('story_opportunity_angle') or 'review'} | path: {item.get('story_opportunity_recommended_path') or item.get('recommendation') or 'review'} | confidence: {item.get('story_opportunity_confidence_tier') or 'review'} | coverage: {item.get('story_opportunity_source_coverage') or 'n/a'} | cue: {item.get('story_opportunity_confirmation_cue') or 'n/a'} | assets: {item.get('story_opportunity_asset_cue') or 'n/a'} | second source: {item.get('story_opportunity_second_source_id') or item.get('story_opportunity_second_source_lane') or 'n/a'} | render: {item.get('render_readiness_score') or 'n/a'}/100 | {item.get('render_readiness_band') or 'not_scored'} | manual: {item.get('render_readiness_manual_path') or 'n/a'} | {item['title']} | preview: {item.get('detail') or 'n/a'} | target: {item['target']} | {item.get('next_step') or item.get('reason')}"
        for item in payload["lead_promotion_recommendations"]
    )
    lines += ["", "## Morning source discovery", ""]
    lines.extend(
        f"- {item['rank']} | {item['lane']} | quality: {item.get('quality_score') or 'n/a'} | {item.get('freshness_label') or 'undated'}{(' via ' + item.get('freshness_source')) if item.get('freshness_source') else ''} | opportunity: {item.get('story_opportunity_size') or 'n/a'} | angle: {item.get('story_opportunity_angle') or 'n/a'} | path: {item.get('story_opportunity_recommended_path') or item.get('promotion') or 'review'} | confidence: {item.get('story_opportunity_confidence_tier') or 'n/a'} | coverage: {item.get('story_opportunity_source_coverage') or 'n/a'} | cue: {item.get('story_opportunity_confirmation_cue') or 'n/a'} | assets: {item.get('story_opportunity_asset_cue') or 'n/a'} | second source: {item.get('story_opportunity_second_source_id') or item.get('story_opportunity_second_source_lane') or 'n/a'} | render: {item.get('render_readiness_score') or 'n/a'}/100 | {item.get('render_readiness_band') or 'not_scored'} | manual: {item.get('render_readiness_manual_path') or 'n/a'} | {item['title']} | preview: {item.get('detail') or 'n/a'} | {item['status']} | {item['posture']} | {item.get('next_action') or item.get('detail')}"
        for item in payload["source_discovery_board"]
    )
    readiness = payload["source_registry_readiness_summary"]
    lines += ["", "## Source registry readiness", ""]
    lines.extend(
        [
            f"- Status: {clean(readiness.get('readiness_status')) or 'review'}",
            f"- Next safest action: {clean(readiness.get('next_safest_action'))}",
            f"- Blockers: {clean(readiness.get('blockers')) or 'none'}",
            f"- Open first: {clean(readiness.get('open_first_file')) or 'trusted_registry_operator_playbook.md'}",
            f"- Playbook: {clean(readiness.get('support_file')) or 'trusted_registry_operator_playbook.md'}",
            f"- Focus: {clean(readiness.get('focus_source_ids')) or 'none'}",
            f"- Guardrail: {clean(readiness.get('guardrail'))}",
        ]
    )
    lines += ["", "## Source coverage map", ""]
    lines.extend(
        f"- {item['name']} | {item['status']} | official: {item.get('official') or 'none'} | team: {item.get('team') or 'none'} | wire: {item.get('wire') or 'none'} | cross-check: {item.get('cross_check') or 'none'} | gap: {item.get('gap') or 'none'} | {item.get('next_step') or ''}"
        for item in payload["source_coverage_map"]
    )
    lines += ["", "## Source registry intake template", ""]
    lines.extend(
        f"- {clean(item.get('display_name'))} | {clean(item.get('needed_source_type'))} | {clean(item.get('coverage_gap'))} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | action: {clean(item.get('registry_action'))}"
        for item in payload["source_registry_intake_template"]
    )
    lines += ["", "## Source registry diff review", ""]
    lines.extend(
        f"- {clean(item.get('diff_review_status')) or 'review'} | cue: {clean(item.get('resolution_action')) or 'review'} | {clean(item.get('resolution_label')) or 'Review'} | {clean(item.get('source_id'))} | flags: {clean(item.get('flags')) or 'none'} | issues: {clean(item.get('issues')) or 'none'} | registry domain: {clean(item.get('registry_domain_match')) or 'No'} | worksheet domain: {clean(item.get('worksheet_domain_match')) or 'No'} | rollback: {clean(item.get('rollback_status')) or 'missing'} | before log: {clean(item.get('verification_log_instruction')) or clean(item.get('recommendation')) or 'review before edit'}"
        for item in payload["source_registry_diff_review"]
    )
    lines += ["", "## Source registry same-domain resolution", ""]
    lines.extend(
        f"- {clean(item.get('same_domain_resolution_status')) or 'operator_input_required'} | decision: {clean(item.get('resolution_decision')) or 'operator fill-in'} | {clean(item.get('source_id'))} | domain: {clean(item.get('candidate_domain')) or 'n/a'} | compared: {clean(item.get('compared_existing_source_id')) or clean(item.get('compared_existing_url')) or 'operator fill-in'} | evidence: {clean(item.get('evidence_url')) or 'operator fill-in'} | gate: {clean(item.get('approval_gate')) or 'same_domain_ok_with_evidence_required_before_approval'}"
        for item in payload["source_registry_same_domain_resolution"]
    )
    lines += ["", "## Source verification log", ""]
    lines.extend(
        f"- {clean(item.get('verification_log_status')) or 'operator_input_required'} | cue: {clean(item.get('diff_resolution_action')) or 'review'} | {clean(item.get('source_id'))} | diff: {clean(item.get('diff_review_status')) or 'review'} | instruction: {clean(item.get('diff_resolution_instruction')) or 'follow diff review cue'} | url_checked: {clean(item.get('url_checked')) or 'operator fill-in'} | freshness: {clean(item.get('freshness_result')) or 'operator fill-in'} | duplicate: {clean(item.get('duplicate_decision')) or 'operator fill-in'} | outcome: {clean(item.get('approval_outcome')) or 'operator fill-in'} | registry: {clean(item.get('registry_edit_status')) or 'not_edited_by_generator'}"
        for item in payload["source_registry_verification_log"]
    )
    lines += ["", "## Source registry approval packet", ""]
    lines.extend(
        f"- {clean(item.get('approval_packet_status')) or 'review'} | {clean(item.get('source_id'))} | evidence: {clean(item.get('evidence_url')) or 'missing'} | freshness: {clean(item.get('freshness_result')) or 'missing'} | duplicate: {clean(item.get('duplicate_decision')) or 'missing'} | hold: {clean(item.get('hold_reason')) or 'none'} | registry: {clean(item.get('registry_edit_status')) or 'not_edited_by_generator'}"
        for item in payload["source_registry_approval_packet"]
    )
    lines += ["", "## Source registry patch preview", ""]
    lines.extend(
        f"- {clean(item.get('patch_preview_status')) or 'review'} | {clean(item.get('source_id'))} | target: {clean(item.get('manual_edit_target')) or 'config/source_registry.json'} | hold: {clean(item.get('hold_reason')) or 'none'} | evidence: {clean(item.get('evidence_url')) or 'missing'} | registry: {clean(item.get('registry_edit_status')) or 'not_edited_by_generator'}"
        for item in payload["source_registry_patch_preview"]
    )
    lines += ["", "## Source registry post-edit validation", ""]
    lines.extend(
        f"- {clean(item.get('post_edit_validation_status')) or 'review'} | {clean(item.get('source_id'))} | exact: {clean(item.get('exact_match')) or 'No'} | enabled: {clean(item.get('enabled_status')) or 'missing'} | drift: {clean(item.get('drift_fields')) or 'none'} | unsafe: {clean(item.get('unsafe_flags')) or 'none'}"
        for item in payload["source_registry_post_edit_validation"]
    )
    lines += ["", "## Source registry update worksheet", ""]
    lines.extend(
        f"- {clean(item.get('worksheet_decision')) or 'review'} | {clean(item.get('source_id'))} | target: {clean(item.get('manual_edit_target')) or 'config/source_registry.json'} | edit: {clean(item.get('manual_edit_allowed')) or 'manual review only'} | enabled: {clean(item.get('proposed_enabled')) or 'False'} | auto: {clean(item.get('auto_edit_status')) or 'not_performed_by_generator'} | rollback: {clean(item.get('rollback_note')) or 'remove manual source object if review fails'}"
        for item in payload["source_registry_update_worksheet"]
    )
    lines += ["", "## Source proposal promotion checklist", ""]
    lines.extend(
        f"- {clean(item.get('checklist_decision')) or 'review'} | {clean(item.get('candidate_source_id'))} | step: {clean(item.get('operator_step')) or 'review'} | copy: {clean(item.get('copy_allowed')) or 'No'} | target: {clean(item.get('copy_target')) or 'none'} | reason: {clean(item.get('hold_reason')) or clean(item.get('discard_reason')) or clean(item.get('freshness_warning')) or 'manual review'} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | registry: {clean(item.get('registry_action')) or 'proposal_only_do_not_import'}"
        for item in payload["source_registry_proposal_promotion_checklist"]
    )
    lines += ["", "## Source proposal draft", ""]
    lines.extend(
        f"- {clean(item.get('draft_selection_status')) or 'review'} | {clean(item.get('pack_name')) or clean(item.get('display_name'))} | {clean(item.get('candidate_source_id'))} | action: {clean(item.get('draft_action'))} | duplicate: {clean(item.get('duplicate_warning')) or 'none'} | freshness: {clean(item.get('freshness_warning')) or 'open manually'} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | registry: {clean(item.get('registry_action')) or 'proposal_only_do_not_import'}"
        for item in payload["source_registry_proposal_draft"]
    )
    lines += ["", "## Guided source pack readiness", ""]
    lines.extend(
        f"- {clean(item.get('pack_name')) or clean(item.get('display_name'))} | {clean(item.get('readiness_status')) or 'review'} | rows: {clean(item.get('candidate_rows')) or '0'} | official: {clean(item.get('official_candidates')) or '0'} | cross-check: {clean(item.get('cross_check_candidates')) or '0'} | duplicates: {clean(item.get('duplicate_candidates')) or '0'} | cues: {clean(item.get('review_cues')) or 'none'} | top: {clean(item.get('top_candidate_ids')) or 'none'} | next: {clean(item.get('next_step')) or 'review manually'}"
        for item in payload["source_proposal_pack_readiness"]
    )
    lines += ["", "## Guided source proposal packs", ""]
    lines.extend(
        f"- {clean(item.get('pack_name')) or clean(item.get('display_name'))} | {clean(item.get('suggested_priority'))} | {clean(item.get('candidate_group'))} | {clean(item.get('candidate_source_id'))} | {clean(item.get('candidate_url'))} | enabled: {clean(item.get('proposed_enabled')) or 'No'} | action: {clean(item.get('registry_action')) or 'proposal_only_do_not_import'} | registry: {clean(item.get('registry_presence')) or 'not_checked'}"
        for item in payload["source_proposal_packs"]
    )
    lines += ["", "## Source proposal review", ""]
    lines.extend(
        f"- {clean(item.get('candidate_source_id')) or 'missing_id'} | {clean(item.get('review_status')) or 'review'} | flags: {clean(item.get('safety_flags')) or 'none'} | {clean(item.get('issues')) or 'none'}"
        for item in payload["source_registry_proposal_review"]
    )
    lines += ["", "## Studio queue", ""]
    lines.extend(f"- {item['priority']} | {item['name']} | {item['status']} | {item['detail']}" for item in payload["studio_queue"])
    lines += ["", "## Artifacts", ""]
    lines.extend(
        (
            f"- [{'found' if item['exists'] else 'missing'}] `{item['path']}` - {item['title']}"
            f"{' - ' + item['status_detail'] if item.get('status_detail') else ''}"
        )
        for item in payload["artifacts"]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_render_prep_packets_markdown(payload: Dict[str, Any]) -> str:
    packets = payload.get("render_prep_packets", [])
    lines = [
        "# HSD Render Prep Packets",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Command center version: {payload['version']}",
        "",
        "## Guardrails",
        "",
        "- Review-only packet. It does not render files.",
        "- Publishing remains off.",
        "- Paid APIs remain disabled.",
        "- Human visual review is required before any post.",
        "",
        "## Summary",
        "",
        f"- Packet rows: {len(packets)}",
        f"- Ready for manual render review: {sum(1 for row in packets if row.get('packet_status') == 'ready_for_manual_render_review')}",
        "",
    ]
    if not packets:
        lines += [
            "## No Packets",
            "",
            "No render-ready or render-prep candidates cleared the source, asset, format, and manual-path gates.",
            "",
        ]
        return "\n".join(lines).rstrip() + "\n"

    for index, packet in enumerate(packets, 1):
        steps = split_manual_renderer_steps(packet.get("manual_renderer_steps"))
        lines += [
            f"## Packet {index}: {clean(packet.get('title'))}",
            "",
            f"- Packet ID: `{clean(packet.get('packet_id'))}`",
            f"- Status: `{clean(packet.get('packet_status'))}`",
            f"- Readiness: `{clean(packet.get('render_readiness_score'))}/100` / `{clean(packet.get('render_readiness_band'))}`",
            f"- Blockers: {display_render_blockers(packet)}",
            f"- Recommended path: `{clean(packet.get('recommended_path'))}`",
            f"- Source artifact: `{clean(packet.get('source_artifact'))}`",
            f"- Template fit: `{clean(packet.get('template_fit'))}`",
            f"- Selected template: `{clean(packet.get('selected_template_id')) or 'operator_review'}`",
            f"- Template family: `{clean(packet.get('template_family')) or 'manual_review'}`",
            f"- Reference pack: `{clean(packet.get('reference_pack_id')) or 'none'}`",
            f"- Template shape: `{clean(packet.get('template_shape'))}`",
            f"- Renderer family: `{clean(packet.get('renderer_family'))}`",
            f"- Visual mode: `{clean(packet.get('visual_mode')) or 'manual_review_template'}`",
            f"- Focal entity: `{clean(packet.get('focal_entity_type')) or 'story'}`",
            f"- Hero asset required: `{clean(packet.get('hero_asset_required')) or 'operator_review'}`",
            f"- Score lock: `{clean(packet.get('score_lock_variant')) or 'not_final_score'}`",
            f"- Proof strip: `{clean(packet.get('proof_strip_variant')) or 'source_check_only'}`",
            f"- Copy unlock: `{clean(packet.get('copy_unlock_state')) or 'manual_copy_locked_review'}`",
            f"- Background family: `{clean(packet.get('background_family')) or 'hsd_premium_sports_editorial'}`",
            f"- Template fit reason: {clean(packet.get('template_fit_reason')) or 'n/a'}",
            f"- Asset requirement: {clean(packet.get('asset_requirement'))}",
            f"- Active asset stop/go: `{clean(packet.get('active_asset_stop_go')) or 'clear_no_active_asset_holds'}`",
            f"- Active logo readiness: `{clean(packet.get('active_logo_readiness_status')) or 'logo_review_not_flagged'}`",
            f"- Active logo review cues: {clean(packet.get('active_logo_review_cues')) or 'none recorded'}",
            f"- Logo review artifact: `{clean(packet.get('logo_review_artifact')) or 'data/asset_registry/asset_availability_audit.csv'}`",
            f"- Active athlete identity: `{clean(packet.get('active_athlete_identity_status')) or 'athlete_identity_not_flagged'}`",
            f"- Active athlete identity cues: {clean(packet.get('active_athlete_identity_cues')) or 'none recorded'}",
            f"- Athlete identity artifact: `{clean(packet.get('athlete_identity_artifact')) or 'data/asset_registry/wnba/athlete_identity_audit.csv'}`",
            f"- Athlete identity closure cues: {clean(packet.get('active_athlete_identity_closure_cues')) or 'none recorded'}",
            f"- Athlete identity closure packet: `{clean(packet.get('athlete_identity_closure_artifact')) or 'not generated'}`",
            f"- Athlete identity backfill packet: `{clean(packet.get('athlete_identity_backfill_artifact')) or 'not generated'}`",
            f"- Renderer fallback cue: {clean(packet.get('renderer_fallback_cue')) or 'none recorded'}",
            f"- Approval gate: `{clean(packet.get('approval_gate'))}`",
            f"- Auto-render status: `{clean(packet.get('auto_render_status'))}`",
            f"- Publish policy: `{clean(packet.get('publish_policy'))}`",
            "",
            "### Copy Fields",
            "",
            f"- Headline: {clean(packet.get('copy_headline'))}",
            f"- Dek: {clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
            f"- Suggested title fit: {clean(packet.get('copy_suggested_title')) or clean(packet.get('copy_headline'))}",
            f"- Suggested dek fit: {clean(packet.get('copy_suggested_dek')) or clean(packet.get('copy_dek')) or 'Operator fill-in after source review.'}",
            f"- Fit cue: {clean(packet.get('copy_fit_cue')) or 'Tighten headline/dek before manual render if they wrap awkwardly.'}",
            f"- Polish note: {clean(packet.get('copy_polish_note')) or 'Use source-backed verbs and remove generic filler before visual review.'}",
            f"- Context: {clean(packet.get('copy_context')) or 'Operator fill-in after source review.'}",
            f"- Source detail: {clean(packet.get('source_detail')) or 'n/a'}",
            "",
            "### Manual Renderer Steps",
            "",
        ]
        lines.extend(f"{step_index}. {step}" for step_index, step in enumerate(steps, 1))
        lines += ["", "---", ""]
    return "\n".join(lines).rstrip() + "\n"


def render_operator_next_action_synthesis_markdown(payload: Dict[str, Any]) -> str:
    rows = payload.get("operator_next_action_synthesis", [])
    lines = [
        "# HSD Operator Next-Action Synthesis",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Version: {payload['version']}",
        "",
        "Review-only and artifact-only. This checklist does not fetch sources, download assets, enable sources, approve assets/stories, move files into publish-ready lanes, or publish.",
        "",
        "## Checklist",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['rank']}. {row['lane']}",
                "",
                f"- Manual step: {row['manual_step']}",
                f"- Open first: `{row['primary_artifact']}`",
                f"- Resolved local path: `{row.get('primary_resolved_path') or 'missing_or_not_generated'}`",
                f"- Companion: `{row['companion_artifact']}`",
                f"- Companion resolved path: `{row.get('companion_resolved_path') or 'missing_or_not_generated'}`",
                f"- Return fields: {row['operator_return_fields']}",
                f"- Lane detail: {row.get('lane_detail') or 'Open the linked artifact for current counts.'}",
                f"- Status: {row['artifact_status']}",
                f"- Refresh command: `{row['run_command']}`" if row.get("run_command") else "- Refresh command: not required",
                f"- Guardrails: {row['guardrail_note']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_operator_next_action_synthesis_outputs(payload: Dict[str, Any]) -> None:
    rows = payload.get("operator_next_action_synthesis", [])
    write_csv(OUT_NEXT_ACTION_SYNTHESIS_CSV, rows, NEXT_ACTION_SYNTHESIS_FIELDS)
    write_json(
        OUT_NEXT_ACTION_SYNTHESIS_JSON,
        {
            "version": payload["version"],
            "generated_at_utc": payload["generated_at_utc"],
            "guardrails": {
                "review_only": True,
                "artifact_only": True,
                "paid_apis": False,
                "source_fetching": False,
                "automatic_downloads": False,
                "source_auto_enablement": False,
                "auto_approval": False,
                "publish_ready_movement": False,
                "publishing": False,
            },
            "counts": {
                "rows": len(rows),
                "ready_to_open": sum(1 for row in rows if row.get("artifact_status") == "ready_to_open"),
            },
            "rows": rows,
        },
    )
    write_text(OUT_NEXT_ACTION_SYNTHESIS_MD, render_operator_next_action_synthesis_markdown(payload))


def write_render_prep_outputs(payload: Dict[str, Any]) -> None:
    packets = payload.get("render_prep_packets", [])
    write_csv(OUT_RENDER_PREP_CSV, packets, RENDER_PREP_FIELDS)
    write_json(
        OUT_RENDER_PREP_JSON,
        {
            "version": payload["version"],
            "generated_at_utc": payload["generated_at_utc"],
            "guardrails": {
                "review_only": True,
                "auto_render": False,
                "auto_publish": False,
                "paid_apis": False,
            },
            "counts": {
                "packets": len(packets),
                "ready_for_manual_render_review": sum(
                    1 for row in packets if row.get("packet_status") == "ready_for_manual_render_review"
                ),
            },
            "packets": packets,
        },
    )
    write_text(OUT_RENDER_PREP_MD, render_render_prep_packets_markdown(payload))


def write_outputs(payload: Dict[str, Any]) -> None:
    write_operator_next_action_synthesis_outputs(payload)
    write_render_prep_outputs(payload)
    write_render_handoff_outputs(payload)
    write_json(OUT_JSON, payload)
    write_text(OUT_MD, render_markdown(payload))
    write_text(OUT_HTML, render_html(payload))


def main() -> None:
    mirror_review_artifacts_to_output()
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps({"version": VERSION, "html": OUT_HTML.as_posix(), "actions": len(payload["next_actions"])}, indent=2))


if __name__ == "__main__":
    main()
