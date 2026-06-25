from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from hsd_run_io import input_path, read_csv as read_run_csv, run_output_dir, write_csv as write_run_csv, write_json, write_text

VERSION = "hsd-source-registry-audit-bebe-v2.17-registry-patch-preview"
REGISTRY = "config/source_registry.json"
PROPOSALS = "operator/inbox/source_registry_proposals.csv"
VERIFICATION_LOG_INPUT = "operator/inbox/source_registry_verification_log.csv"
OUT_CSV = "source_registry_audit.csv"
OUT_COVERAGE_CSV = "source_coverage_map.csv"
OUT_INTAKE_CSV = "source_registry_intake_template.csv"
OUT_INTAKE_MD = "source_registry_intake_template.md"
OUT_PROPOSAL_CSV = "source_registry_proposal_review.csv"
OUT_PROPOSAL_MD = "source_registry_proposal_review.md"
OUT_PROPOSAL_DRAFT_CSV = "source_registry_proposal_draft.csv"
OUT_PROPOSAL_DRAFT_MD = "source_registry_proposal_draft.md"
OUT_PROPOSAL_PROMOTION_CHECKLIST_CSV = "source_registry_proposal_promotion_checklist.csv"
OUT_PROPOSAL_PROMOTION_CHECKLIST_MD = "source_registry_proposal_promotion_checklist.md"
OUT_REGISTRY_UPDATE_WORKSHEET_CSV = "source_registry_update_worksheet.csv"
OUT_REGISTRY_UPDATE_WORKSHEET_MD = "source_registry_update_worksheet.md"
OUT_REGISTRY_DIFF_REVIEW_CSV = "source_registry_diff_review.csv"
OUT_REGISTRY_DIFF_REVIEW_MD = "source_registry_diff_review.md"
OUT_SOURCE_VERIFICATION_LOG_CSV = "source_registry_verification_log.csv"
OUT_SOURCE_VERIFICATION_LOG_MD = "source_registry_verification_log.md"
OUT_REGISTRY_APPROVAL_PACKET_CSV = "source_registry_approval_packet.csv"
OUT_REGISTRY_APPROVAL_PACKET_MD = "source_registry_approval_packet.md"
OUT_REGISTRY_PATCH_PREVIEW_CSV = "source_registry_patch_preview.csv"
OUT_REGISTRY_PATCH_PREVIEW_MD = "source_registry_patch_preview.md"
OUT_PROPOSAL_PACK_READINESS_CSV = "source_proposal_pack_readiness.csv"
OUT_PROPOSAL_PACK_READINESS_MD = "source_proposal_pack_readiness.md"
OUT_PROPOSAL_PACKS_CSV = "source_proposal_packs.csv"
OUT_PROPOSAL_PACKS_MD = "source_proposal_packs.md"
OUT_WNBA_PACK_CSV = "wnba_source_proposal_pack.csv"
OUT_WNBA_PACK_MD = "wnba_source_proposal_pack.md"
OUT_NWSL_PACK_CSV = "nwsl_source_proposal_pack.csv"
OUT_NWSL_PACK_MD = "nwsl_source_proposal_pack.md"
OUT_LPGA_PACK_CSV = "lpga_source_proposal_pack.csv"
OUT_LPGA_PACK_MD = "lpga_source_proposal_pack.md"
OUT_PWHL_PACK_CSV = "pwhl_source_proposal_pack.csv"
OUT_PWHL_PACK_MD = "pwhl_source_proposal_pack.md"
OUT_MD = "source_registry_audit.md"
OUT_JSON = "source_registry_audit.json"

FIELDS = [
    "source_id", "source_type", "tier", "trust_band", "enabled", "sport_league", "automation_status",
    "publish_policy", "status", "issues", "urls_count", "domains_count",
]

GREEN_TIERS = {"official", "operator", "wire", "primary_media", "stats_provider"}
YELLOW_TIERS = {"social", "social_manual", "community", "discovery", "media_review"}
RED_TIERS = {"red", "prohibited"}

COVERAGE_FIELDS = [
    "coverage_key",
    "display_name",
    "official_sources",
    "team_sources",
    "wire_sources",
    "cross_check_sources",
    "coverage_status",
    "coverage_gap",
    "operator_next_step",
]

INTAKE_FIELDS = [
    "coverage_key",
    "display_name",
    "needed_source_type",
    "coverage_gap",
    "candidate_source_id",
    "candidate_source_name",
    "candidate_url",
    "candidate_domain",
    "source_type",
    "tier",
    "trust_band",
    "sport_league",
    "proposed_enabled",
    "automation_status",
    "publish_policy",
    "allowed_use",
    "operator_verification_status",
    "registry_action",
    "review_notes",
]

PROPOSAL_REVIEW_FIELDS = [
    "candidate_source_id",
    "candidate_source_name",
    "candidate_url",
    "candidate_domain",
    "sport_league",
    "source_type",
    "tier",
    "proposed_enabled",
    "review_status",
    "issue_count",
    "issues",
    "safety_flags",
    "recommendation",
    "registry_action",
]

SOURCE_PROPOSAL_PACK_FIELDS = [
    "pack_key",
    "pack_name",
    "candidate_group",
    "suggested_priority",
    *INTAKE_FIELDS,
    "source_basis",
    "registry_presence",
    "manual_review_note",
]

SOURCE_PROPOSAL_PACK_READINESS_FIELDS = [
    "pack_key",
    "pack_name",
    "display_name",
    "readiness_status",
    "readiness_label",
    "candidate_rows",
    "official_candidates",
    "cross_check_candidates",
    "duplicate_candidates",
    "freshness_check_candidates",
    "ready_candidates",
    "coverage_status",
    "coverage_gap",
    "review_cues",
    "next_step",
    "top_candidate_ids",
    "duplicate_candidate_ids",
    "output_csv",
    "output_md",
]

SOURCE_REGISTRY_PROPOSAL_DRAFT_FIELDS = [
    "draft_selection_status",
    "draft_action",
    "pack_key",
    "pack_name",
    "pack_readiness_status",
    "pack_readiness_label",
    "candidate_group",
    "suggested_priority",
    *INTAKE_FIELDS,
    "source_basis",
    "registry_presence",
    "readiness_warning",
    "duplicate_warning",
    "freshness_warning",
    "manual_review_note",
]

SOURCE_REGISTRY_PROPOSAL_PROMOTION_CHECKLIST_FIELDS = [
    "checklist_decision",
    "operator_step",
    "copy_allowed",
    "copy_target",
    "pack_key",
    "pack_name",
    "candidate_source_id",
    "candidate_source_name",
    "candidate_url",
    "candidate_domain",
    "source_type",
    "tier",
    "sport_league",
    "allowed_use",
    "registry_presence",
    "draft_selection_status",
    "draft_action",
    "duplicate_warning",
    "freshness_warning",
    "readiness_warning",
    "verification_checklist",
    "copy_instructions",
    "hold_reason",
    "discard_reason",
    "proposed_enabled",
    "registry_action",
    "automation_status",
    "publish_policy",
]

SOURCE_REGISTRY_UPDATE_WORKSHEET_FIELDS = [
    "worksheet_decision",
    "operator_step",
    "manual_edit_target",
    "manual_edit_allowed",
    "auto_edit_status",
    "pack_key",
    "pack_name",
    "source_id",
    "source_name",
    "candidate_url",
    "candidate_domain",
    "source_type",
    "tier",
    "trust_band",
    "sport_league",
    "allowed_use",
    "registry_presence",
    "checklist_decision",
    "checklist_copy_target",
    "verification_gate",
    "current_registry_state",
    "proposed_enabled",
    "proposed_automation_status",
    "proposed_publish_policy",
    "proposed_source_json",
    "before_after_diff",
    "rollback_note",
    "review_notes",
]

SOURCE_REGISTRY_DIFF_REVIEW_FIELDS = [
    "diff_review_status",
    "issue_count",
    "issues",
    "flags",
    "operator_step",
    "manual_edit_target",
    "source_id",
    "source_name",
    "candidate_url",
    "candidate_domain",
    "proposed_enabled",
    "proposed_trust_band",
    "proposed_automation_status",
    "proposed_publish_policy",
    "registry_source_id_match",
    "registry_url_match",
    "registry_domain_match",
    "worksheet_domain_match",
    "rollback_status",
    "proposed_json_status",
    "before_after_status",
    "auto_edit_status",
    "recommendation",
]

SOURCE_REGISTRY_VERIFICATION_LOG_FIELDS = [
    "verification_log_status",
    "operator_step",
    "source_id",
    "source_name",
    "candidate_url",
    "candidate_domain",
    "diff_review_status",
    "diff_flags",
    "diff_issues",
    "registry_domain_match",
    "worksheet_domain_match",
    "url_checked",
    "checked_at_local",
    "freshness_result",
    "duplicate_decision",
    "approval_outcome",
    "registry_edit_decision",
    "operator_name",
    "evidence_url",
    "operator_notes",
    "auto_edit_status",
    "publish_policy",
    "paid_api_policy",
    "registry_edit_status",
]

SOURCE_REGISTRY_APPROVAL_PACKET_FIELDS = [
    "approval_packet_status",
    "source_id",
    "source_name",
    "candidate_url",
    "candidate_domain",
    "manual_edit_target",
    "exact_proposed_source_json",
    "url_checked",
    "checked_at_local",
    "freshness_result",
    "duplicate_decision",
    "approval_outcome",
    "registry_edit_decision",
    "evidence_url",
    "operator_name",
    "operator_notes",
    "diff_review_status",
    "diff_flags",
    "diff_issues",
    "hold_reason",
    "approval_guardrails",
    "auto_edit_status",
    "publish_policy",
    "paid_api_policy",
    "registry_edit_status",
]

SOURCE_REGISTRY_PATCH_PREVIEW_FIELDS = [
    "patch_preview_status",
    "source_id",
    "source_name",
    "manual_edit_target",
    "registry_before_summary",
    "side_by_side_before",
    "side_by_side_after",
    "copy_paste_source_json",
    "copy_paste_patch_instructions",
    "rollback_instructions",
    "url_checked",
    "evidence_url",
    "freshness_result",
    "duplicate_decision",
    "approval_packet_status",
    "hold_reason",
    "preview_guardrails",
    "auto_edit_status",
    "publish_policy",
    "paid_api_policy",
    "registry_edit_status",
]

PWHL_SOURCE_CANDIDATES = [
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "missing official league/team source",
        "candidate_source_id": "pwhl_official_home",
        "candidate_source_name": "PWHL official site",
        "candidate_url": "https://www.thepwhl.com/en/",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; league_context; source_confirmation",
        "source_basis": "Free public league official site with team, schedule, standings, stats, and news navigation.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "missing official league/team source",
        "candidate_source_id": "pwhl_official_news",
        "candidate_source_name": "PWHL official news",
        "candidate_url": "https://www.thepwhl.com/en/news",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; source_confirmation; transaction_confirmation",
        "source_basis": "Free public official league news page for announcements and source confirmation.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "pwhl_official_scores",
        "candidate_source_name": "PWHL official scores",
        "candidate_url": "https://www.thepwhl.com/en/scores",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; scores; schedules; game_summaries",
        "source_basis": "Free public official scores page for manual final-score and schedule checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "pwhl_official_standings",
        "candidate_source_name": "PWHL official standings",
        "candidate_url": "https://www.thepwhl.com/en/stats/standings",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; standings; league_context",
        "source_basis": "Free public official standings page for table and context checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "pwhl_official_player_stats",
        "candidate_source_name": "PWHL official player stats",
        "candidate_url": "https://www.thepwhl.com/en/stats/player-stats",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; player_stats; league_context",
        "source_basis": "Free public official player stats page for context and stat checks.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_boston_fleet_team",
        "candidate_source_name": "Boston Fleet official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/boston-fleet",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_detroit_team",
        "candidate_source_name": "PWHL Detroit official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/detroit",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Detroit team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_hamilton_team",
        "candidate_source_name": "PWHL Hamilton official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/hamilton",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Hamilton team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_las_vegas_team",
        "candidate_source_name": "PWHL Las Vegas official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/las-vegas",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Las Vegas team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_minnesota_frost_team",
        "candidate_source_name": "Minnesota Frost official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/minnesota-frost",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_montreal_victoire_team",
        "candidate_source_name": "Montreal Victoire official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/montreal-victoire",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_new_york_sirens_team",
        "candidate_source_name": "New York Sirens official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/new-york-sirens",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_ottawa_charge_team",
        "candidate_source_name": "Ottawa Charge official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/ottawa-charge",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_san_jose_team",
        "candidate_source_name": "PWHL San Jose official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/san-jose",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for San Jose team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_seattle_torrent_team",
        "candidate_source_name": "Seattle Torrent official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/seattle-torrent",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Seattle team news and launch context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_toronto_sceptres_team",
        "candidate_source_name": "Toronto Sceptres official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/toronto-sceptres",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team page with team news and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "pwhl_vancouver_goldeneyes_team",
        "candidate_source_name": "Vancouver Goldeneyes official team page",
        "candidate_url": "https://www.thepwhl.com/en/teams/vancouver-goldeneyes",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team page for Vancouver team news and launch context.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "eliteprospects_pwhl_cross_check",
        "candidate_source_name": "Elite Prospects PWHL page",
        "candidate_url": "https://www.eliteprospects.com/league/pwhl-w",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; roster_context; standings_context",
        "source_basis": "Free public hockey database page for manual roster/stat cross-checking; not an official source.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "missing scoreboard/stat/cross-check source",
        "candidate_source_id": "hockeydb_pwhl_cross_check",
        "candidate_source_name": "HockeyDB PWHL season page",
        "candidate_url": "https://www.hockeydb.com/ihdb/stats/leagues/seasons/pwhl20242026.html",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; historical_scores; standings_context",
        "source_basis": "Free public hockey database season page for manual historical/stat cross-checking; not an official source.",
    },
]

WNBA_SOURCE_CANDIDATES = [
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official league/team source depth",
        "candidate_source_id": "wnba_official_home_review",
        "candidate_source_name": "WNBA official site",
        "candidate_url": "https://www.wnba.com/",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; league_context; source_confirmation",
        "source_basis": "Free public official league home for WNBA news, scores, standings, and team navigation.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official league/team source depth",
        "candidate_source_id": "wnba_official_news_review",
        "candidate_source_name": "WNBA official news",
        "candidate_url": "https://www.wnba.com/news",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; transaction_confirmation; source_confirmation",
        "source_basis": "Free public official news page for announcements, features, and league-confirmed updates.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official schedule/source depth",
        "candidate_source_id": "wnba_official_schedule_review",
        "candidate_source_name": "WNBA official schedule",
        "candidate_url": "https://www.wnba.com/schedule",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "schedule; scores; game_status; source_confirmation",
        "source_basis": "Free public official schedule and score page for manual slate and result checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "wnba_official_standings_review",
        "candidate_source_name": "WNBA official standings",
        "candidate_url": "https://www.wnba.com/standings",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; standings; playoff_context",
        "source_basis": "Free public official standings page for team table and playoff-context checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "wnba_official_stats_review",
        "candidate_source_name": "WNBA official stats",
        "candidate_url": "https://stats.wnba.com/",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; player_stats; team_stats; box_score_context",
        "source_basis": "Free public official stats hub for player, team, and box score context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "review team/club source depth",
        "candidate_source_id": "wnba_official_teams_index_review",
        "candidate_source_name": "WNBA official teams index",
        "candidate_url": "https://www.wnba.com/teams",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official WNBA team index with links to team profile, roster, and schedule pages.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "review expansion/team source depth",
        "candidate_source_id": "wnba_golden_state_valkyries_team_review",
        "candidate_source_name": "Golden State Valkyries official team site",
        "candidate_url": "https://valkyries.wnba.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team site for Valkyries team news, schedule, and roster review.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "review expansion/team source depth",
        "candidate_source_id": "wnba_portland_fire_team_review",
        "candidate_source_name": "Portland Fire official team site",
        "candidate_url": "https://fire.wnba.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team site for Portland Fire launch and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "review expansion/team source depth",
        "candidate_source_id": "wnba_toronto_tempo_team_review",
        "candidate_source_name": "Toronto Tempo official team site",
        "candidate_url": "https://tempo.wnba.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official expansion team site for Toronto Tempo launch and roster context.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "review high-interest team source depth",
        "candidate_source_id": "wnba_indiana_fever_team_review",
        "candidate_source_name": "Indiana Fever official team site",
        "candidate_url": "https://fever.wnba.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official team site for Fever team news, roster, and schedule review.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "espn_wnba_scoreboard_pack_review",
        "candidate_source_name": "ESPN WNBA scoreboard",
        "candidate_url": "https://www.espn.com/wnba/scoreboard",
        "source_type": "scoreboard_site",
        "tier": "primary_media",
        "allowed_use": "cross_check; scores; schedule; game_status",
        "source_basis": "Free public scoreboard for manual cross-checking; official WNBA sources win on conflict.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "cbs_wnba_scoreboard_cross_check",
        "candidate_source_name": "CBS Sports WNBA scoreboard",
        "candidate_url": "https://www.cbssports.com/wnba/scoreboard/",
        "source_type": "scoreboard_site",
        "tier": "primary_media",
        "allowed_use": "cross_check; scores; schedule; standings_context",
        "source_basis": "Free public sports media scoreboard for manual cross-checking; official WNBA sources win on conflict.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "fox_wnba_standings_cross_check",
        "candidate_source_name": "FOX Sports WNBA standings",
        "candidate_url": "https://www.foxsports.com/wnba/standings",
        "source_type": "scoreboard_site",
        "tier": "primary_media",
        "allowed_use": "cross_check; standings; team_context",
        "source_basis": "Free public sports media standings page for manual table cross-checking.",
    },
]

NWSL_SOURCE_CANDIDATES = [
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official league/team source depth",
        "candidate_source_id": "nwsl_official_home_review",
        "candidate_source_name": "NWSL official site",
        "candidate_url": "https://www.nwslsoccer.com/",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; league_context; source_confirmation",
        "source_basis": "Free public official league home for NWSL news, schedule, standings, teams, and stats navigation.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official league/team source depth",
        "candidate_source_id": "nwsl_official_news_review",
        "candidate_source_name": "NWSL official news",
        "candidate_url": "https://www.nwslsoccer.com/news",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; club_news; source_confirmation",
        "source_basis": "Free public official news page for league and club announcements.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official schedule/source depth",
        "candidate_source_id": "nwsl_official_schedule_review",
        "candidate_source_name": "NWSL official schedule",
        "candidate_url": "https://www.nwslsoccer.com/schedule",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "schedule; scores; match_status; source_confirmation",
        "source_basis": "Free public official schedule page for manual match and result checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "nwsl_official_standings_review",
        "candidate_source_name": "NWSL official standings",
        "candidate_url": "https://www.nwslsoccer.com/standings",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; standings; playoff_context",
        "source_basis": "Free public official standings page for table and playoff-context checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "nwsl_official_team_stats_review",
        "candidate_source_name": "NWSL official team stats",
        "candidate_url": "https://www.nwslsoccer.com/stats/teams",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; team_stats; match_context",
        "source_basis": "Free public official team stats page for performance-context checks.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P1",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_official_teams_index_review",
        "candidate_source_name": "NWSL official teams index",
        "candidate_url": "https://www.nwslsoccer.com/teams/index",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official NWSL teams index with official club links and roster/schedule paths.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_angel_city_team_review",
        "candidate_source_name": "Angel City FC official team site",
        "candidate_url": "https://www.angelcity.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_boston_legacy_team_review",
        "candidate_source_name": "Boston Legacy FC official team site",
        "candidate_url": "https://bostonlegacyfc.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_denver_summit_team_review",
        "candidate_source_name": "Denver Summit FC official team site",
        "candidate_url": "https://www.denversummitfc.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; expansion_team_context; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_kansas_city_current_team_review",
        "candidate_source_name": "Kansas City Current official team site",
        "candidate_url": "https://www.kansascitycurrent.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_gotham_team_review",
        "candidate_source_name": "Gotham FC official team site",
        "candidate_url": "https://www.gothamfc.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_portland_thorns_team_review",
        "candidate_source_name": "Portland Thorns official team site",
        "candidate_url": "https://www.thorns.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "team_official",
        "suggested_priority": "P2",
        "needed_source_type": "team_or_club",
        "coverage_gap": "missing team/club source",
        "candidate_source_id": "nwsl_washington_spirit_team_review",
        "candidate_source_name": "Washington Spirit official team site",
        "candidate_url": "https://washingtonspirit.com/",
        "source_type": "official_site_collection",
        "tier": "official",
        "allowed_use": "team_news; roster_confirmation; source_confirmation",
        "source_basis": "Free public official club site surfaced from the NWSL teams page.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "espn_nwsl_standings_cross_check",
        "candidate_source_name": "ESPN NWSL standings",
        "candidate_url": "https://www.espn.com/soccer/standings/_/league/usa.nwsl",
        "source_type": "scoreboard_site",
        "tier": "primary_media",
        "allowed_use": "cross_check; standings; match_context",
        "source_basis": "Free public sports media standings page for manual cross-checking; official NWSL sources win on conflict.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review scoreboard/stat/cross-check source depth",
        "candidate_source_id": "fox_nwsl_standings_cross_check",
        "candidate_source_name": "FOX Sports NWSL standings",
        "candidate_url": "https://www.foxsports.com/soccer/nwsl/standings",
        "source_type": "scoreboard_site",
        "tier": "primary_media",
        "allowed_use": "cross_check; standings; team_context",
        "source_basis": "Free public sports media standings page for manual table cross-checking.",
    },
]

LPGA_SOURCE_CANDIDATES = [
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official tournament/source depth",
        "candidate_source_id": "lpga_official_home_review",
        "candidate_source_name": "LPGA official site",
        "candidate_url": "https://www.lpga.com/",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; tournament_context; source_confirmation",
        "source_basis": "Free public official LPGA home for news, tournament, leaderboard, and player navigation.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official news/source depth",
        "candidate_source_id": "lpga_official_news_review",
        "candidate_source_name": "LPGA official news",
        "candidate_url": "https://www.lpga.com/news",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "official_news; player_context; tournament_context; source_confirmation",
        "source_basis": "Free public official news page for LPGA announcements and tournament context.",
    },
    {
        "candidate_group": "tournament_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official tournament/source depth",
        "candidate_source_id": "lpga_official_tournaments_review",
        "candidate_source_name": "LPGA official tournaments",
        "candidate_url": "https://www.lpga.com/tournaments",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "schedule; tournament_context; field_context; source_confirmation",
        "source_basis": "Free public official tournament schedule with event pages, venues, purses, and winners.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review leaderboard/stat/cross-check source depth",
        "candidate_source_id": "lpga_official_leaderboard_review",
        "candidate_source_name": "LPGA official leaderboard",
        "candidate_url": "https://www.lpga.com/leaderboard",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; leaderboard; scores; tournament_status",
        "source_basis": "Free public official leaderboard hub for manual tournament result checks.",
    },
    {
        "candidate_group": "league_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review player/stat/cross-check source depth",
        "candidate_source_id": "lpga_official_stats_review",
        "candidate_source_name": "LPGA official stats",
        "candidate_url": "https://www.lpga.com/statistics",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; player_stats; season_context",
        "source_basis": "Free public official statistics page for manual player and season-context checks.",
    },
    {
        "candidate_group": "league_official",
        "suggested_priority": "P2",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review player/source depth",
        "candidate_source_id": "lpga_athlete_directory_review",
        "candidate_source_name": "LPGA athlete directory",
        "candidate_url": "https://www.lpga.com/athletes/directory",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "player_context; identity_check; source_confirmation",
        "source_basis": "Free public official athlete directory for player identity and context review.",
    },
    {
        "candidate_group": "tournament_official",
        "suggested_priority": "P1",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official tournament/source depth",
        "candidate_source_id": "kpmg_womens_pga_leaderboard_review",
        "candidate_source_name": "KPMG Women's PGA Championship leaderboard",
        "candidate_url": "https://www.lpga.com/tournaments/kpmgwomenspgachampionship/leaderboard",
        "source_type": "scoreboard_site",
        "tier": "official",
        "allowed_use": "cross_check; leaderboard; tournament_status; major_context",
        "source_basis": "Free public LPGA event leaderboard for a current major tournament.",
    },
    {
        "candidate_group": "tournament_official",
        "suggested_priority": "P2",
        "needed_source_type": "official_or_team",
        "coverage_gap": "review official tournament/source depth",
        "candidate_source_id": "aig_womens_open_tournament_review",
        "candidate_source_name": "AIG Women's Open LPGA event page",
        "candidate_url": "https://www.lpga.com/tournaments/aigwomensopen",
        "source_type": "official_site",
        "tier": "official",
        "allowed_use": "tournament_context; field_context; source_confirmation",
        "source_basis": "Free public LPGA event page for a major tournament candidate.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P1",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review leaderboard/stat/cross-check source depth",
        "candidate_source_id": "espn_lpga_leaderboard_cross_check",
        "candidate_source_name": "ESPN LPGA leaderboard",
        "candidate_url": "https://www.espn.com/golf/leaderboard/_/tour/lpga",
        "source_type": "scoreboard_site",
        "tier": "primary_media",
        "allowed_use": "cross_check; leaderboard; tournament_status",
        "source_basis": "Free public sports media leaderboard for manual cross-checking; official LPGA source wins on conflict.",
    },
    {
        "candidate_group": "reputable_cross_check",
        "suggested_priority": "P2",
        "needed_source_type": "scoreboard_or_stats_cross_check",
        "coverage_gap": "review leaderboard/stat/cross-check source depth",
        "candidate_source_id": "flashscore_lpga_leaderboard_cross_check",
        "candidate_source_name": "Flashscore LPGA leaderboard",
        "candidate_url": "https://www.flashscoreusa.com/golf/lpga-tour/",
        "source_type": "scoreboard_site",
        "tier": "stats_provider",
        "allowed_use": "cross_check; leaderboard; final_results",
        "source_basis": "Free public live-score page for manual result cross-checking; official LPGA source wins on conflict.",
    },
]

SOURCE_PROPOSAL_PACKS = [
    {
        "pack_key": "wnba",
        "pack_name": "WNBA Source Proposal Pack",
        "display_name": "WNBA",
        "fallback_coverage_gap": "review official league/team and scoreboard source depth",
        "fallback_operator_next_step": "Use the pack to review additional free WNBA official, team, and cross-check candidates before changing the registry.",
        "description": "Guided free-source candidates for manual review of WNBA official, team, and cross-check coverage.",
        "output_csv": OUT_WNBA_PACK_CSV,
        "output_md": OUT_WNBA_PACK_MD,
        "candidates": WNBA_SOURCE_CANDIDATES,
        "group_order": ["league_official", "team_official", "league_cross_check", "reputable_cross_check"],
    },
    {
        "pack_key": "nwsl",
        "pack_name": "NWSL Source Proposal Pack",
        "display_name": "NWSL",
        "fallback_coverage_gap": "missing team/club source; missing scoreboard/stat/cross-check source",
        "fallback_operator_next_step": "Use the pack to review free NWSL official, club, and cross-check candidates before changing the registry.",
        "description": "Guided free-source candidates for manual review of NWSL official, club, and cross-check coverage.",
        "output_csv": OUT_NWSL_PACK_CSV,
        "output_md": OUT_NWSL_PACK_MD,
        "candidates": NWSL_SOURCE_CANDIDATES,
        "group_order": ["league_official", "team_official", "league_cross_check", "reputable_cross_check"],
    },
    {
        "pack_key": "lpga",
        "pack_name": "LPGA Source Proposal Pack",
        "display_name": "LPGA / golf",
        "fallback_coverage_gap": "missing scoreboard/stat/cross-check source",
        "fallback_operator_next_step": "Use the pack to review free LPGA official tournament, leaderboard, and cross-check candidates before changing the registry.",
        "description": "Guided free-source candidates for manual review of LPGA official, tournament, leaderboard, and cross-check coverage.",
        "output_csv": OUT_LPGA_PACK_CSV,
        "output_md": OUT_LPGA_PACK_MD,
        "candidates": LPGA_SOURCE_CANDIDATES,
        "group_order": ["league_official", "tournament_official", "league_cross_check", "reputable_cross_check"],
    },
    {
        "pack_key": "pwhl",
        "pack_name": "PWHL Source Proposal Pack",
        "display_name": "PWHL",
        "fallback_coverage_gap": "missing official league/team source; missing scoreboard/stat/cross-check source",
        "fallback_operator_next_step": "Add or monitor free PWHL league/team official pages before relying on wire-only hockey leads.",
        "description": "Guided free-source candidates for manual review of PWHL coverage gaps.",
        "output_csv": OUT_PWHL_PACK_CSV,
        "output_md": OUT_PWHL_PACK_MD,
        "candidates": PWHL_SOURCE_CANDIDATES,
        "group_order": ["league_official", "team_official", "league_cross_check", "reputable_cross_check"],
    },
]

COVERAGE_TARGETS = [
    {
        "key": "wnba",
        "name": "WNBA",
        "aliases": ["wnba"],
        "needs_team_source": True,
        "next_step": "Monitor WNBA league/team official pages plus AP/Reuters or scoreboard cross-checks.",
    },
    {
        "key": "wta",
        "name": "WTA / tennis",
        "aliases": ["wta", "tennis", "wimbledon"],
        "needs_team_source": False,
        "next_step": "Monitor WTA official news/tournament pages and add a second free wire or tournament source when needed.",
    },
    {
        "key": "nwsl",
        "name": "NWSL",
        "aliases": ["nwsl"],
        "needs_team_source": True,
        "next_step": "Monitor NWSL official news/schedule and add club-specific free sources when they become useful.",
    },
    {
        "key": "lpga",
        "name": "LPGA / golf",
        "aliases": ["lpga", "golf"],
        "needs_team_source": False,
        "next_step": "Monitor LPGA official tournament pages and wire context for result confirmation.",
    },
    {
        "key": "ncaa_softball",
        "name": "NCAA softball",
        "aliases": ["ncaa softball", "softball"],
        "needs_team_source": False,
        "next_step": "Monitor NCAA softball official pages and add event-specific public sources for championship weeks.",
    },
    {
        "key": "uswnt",
        "name": "USWNT",
        "aliases": ["uswnt", "us soccer"],
        "needs_team_source": False,
        "next_step": "Monitor US Soccer official pages plus FIFA/CONCACAF sources for international context.",
    },
    {
        "key": "volleyball",
        "name": "Volleyball / VNL",
        "aliases": ["volleyball", "vnl"],
        "needs_team_source": False,
        "next_step": "Monitor Volleyball World/VNL official pages and add event-specific public sources when useful.",
    },
    {
        "key": "pwhl",
        "name": "PWHL",
        "aliases": ["pwhl", "phwl"],
        "needs_team_source": True,
        "next_step": "Add or monitor free PWHL league/team official pages before relying on wire-only hockey leads.",
    },
]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def lower(v: Any) -> str:
    return clean(v).lower()


def read_json(path: str | Path) -> Dict[str, Any]:
    p = input_path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, FIELDS, extrasaction="ignore")


def write_coverage_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, COVERAGE_FIELDS, extrasaction="ignore")


def write_intake_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, INTAKE_FIELDS, extrasaction="ignore")


def write_proposal_review_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, PROPOSAL_REVIEW_FIELDS, extrasaction="ignore")


def write_source_registry_proposal_draft_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_PROPOSAL_DRAFT_FIELDS, extrasaction="ignore")


def write_source_registry_proposal_promotion_checklist_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_PROPOSAL_PROMOTION_CHECKLIST_FIELDS, extrasaction="ignore")


def write_source_registry_update_worksheet_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_UPDATE_WORKSHEET_FIELDS, extrasaction="ignore")


def write_source_registry_diff_review_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_DIFF_REVIEW_FIELDS, extrasaction="ignore")


def write_source_registry_verification_log_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_VERIFICATION_LOG_FIELDS, extrasaction="ignore")


def write_source_registry_approval_packet_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_APPROVAL_PACKET_FIELDS, extrasaction="ignore")


def write_source_registry_patch_preview_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_REGISTRY_PATCH_PREVIEW_FIELDS, extrasaction="ignore")


def write_source_proposal_pack_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_PROPOSAL_PACK_FIELDS, extrasaction="ignore")


def write_source_proposal_pack_readiness_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    write_run_csv(path, rows, SOURCE_PROPOSAL_PACK_READINESS_FIELDS, extrasaction="ignore")


def canonical_band(src: Dict[str, Any]) -> str:
    raw = clean(src.get("trust_band")).lower()
    tier = clean(src.get("tier")).lower()
    if "red" in raw or tier in RED_TIERS:
        return "red"
    if "green" in raw or tier in GREEN_TIERS:
        return "green"
    if "yellow" in raw or tier in YELLOW_TIERS:
        return "yellow"
    return "yellow"


def url_ok(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def split_tokens(value: Any) -> List[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    return [clean(item) for item in re.split(r"[;,]", clean(value)) if clean(item)]


def audit_source(src: Dict[str, Any], seen: set[str]) -> Dict[str, Any]:
    issues: List[str] = []
    sid = clean(src.get("source_id"))
    stype = clean(src.get("source_type"))
    tier = clean(src.get("tier"))
    band = canonical_band(src)
    urls = src.get("urls") or []
    domains = src.get("domains") or []
    enabled = bool(src.get("enabled"))

    if not sid:
        issues.append("missing source_id")
    elif sid in seen:
        issues.append("duplicate source_id")
    seen.add(sid)

    if not stype:
        issues.append("missing source_type")
    if not tier:
        issues.append("missing tier")
    if band == "red" and enabled:
        issues.append("red/prohibited source cannot be enabled")
    if stype in {"official_site", "scoreboard_site", "wire"} and not urls:
        issues.append("official/cross-check source should include urls")
    for url in urls:
        if not url_ok(clean(url)):
            issues.append(f"bad url: {url}")
            break
    if stype in {"official_site", "scoreboard_site", "wire", "official_site_collection"} and band != "green":
        issues.append("official/primary source should resolve to green trust band")
    if stype in {"reddit_public_json", "mastodon_public"} and enabled:
        issues.append("community/social discovery is enabled; keep disabled until weekly review")
    if not clean(src.get("publish_policy")):
        issues.append("missing publish_policy")
    if not clean(src.get("automation_status")):
        issues.append("missing automation_status")

    status = "PASS" if not issues else "REVIEW" if all("disabled" in x or "should include" in x or "missing automation" in x for x in issues) else "FAIL"
    return {
        "source_id": sid,
        "source_type": stype,
        "tier": tier,
        "trust_band": band,
        "enabled": "Yes" if enabled else "No",
        "sport_league": clean(src.get("sport_league")),
        "automation_status": clean(src.get("automation_status")),
        "publish_policy": clean(src.get("publish_policy")),
        "status": status,
        "issues": "; ".join(issues),
        "urls_count": len(urls),
        "domains_count": len(domains),
    }


def source_matches_target(src: Dict[str, Any], target: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            clean(src.get("source_id")),
            clean(src.get("source_type")),
            clean(src.get("sport_league")),
            " ".join(clean(item) for item in src.get("allowed_use", [])),
            clean(src.get("publish_policy")),
        ]
    ).lower()
    return any(alias in text for alias in target["aliases"])


def source_kind(src: Dict[str, Any]) -> str:
    stype = clean(src.get("source_type")).lower()
    tier = clean(src.get("tier")).lower()
    trust = clean(src.get("trust_band")).lower()
    allowed = " ".join(clean(item) for item in src.get("allowed_use", [])).lower()
    sid = clean(src.get("source_id")).lower()
    if "wire" in stype or tier == "wire":
        return "wire"
    if "team" in sid or "club" in allowed or "team_news" in allowed or "official_site_collection" in stype:
        return "team"
    if "official" in stype or tier == "official":
        return "official"
    if "scoreboard" in stype or "cross_check" in trust or "cross_check" in allowed:
        return "cross_check"
    return "other"


def build_coverage_map(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    enabled_green = [
        src
        for src in sources
        if isinstance(src, dict) and src.get("enabled") and canonical_band(src) == "green"
    ]
    all_wires = [src for src in enabled_green if source_kind(src) == "wire" and clean(src.get("sport_league")).lower() == "all"]
    rows: List[Dict[str, str]] = []
    for target in COVERAGE_TARGETS:
        matched = [src for src in enabled_green if source_matches_target(src, target)]
        official = sorted(clean(src.get("source_id")) for src in matched if source_kind(src) == "official")
        team = sorted(clean(src.get("source_id")) for src in matched if source_kind(src) == "team")
        wire = sorted({clean(src.get("source_id")) for src in matched if source_kind(src) == "wire"} | {clean(src.get("source_id")) for src in all_wires})
        cross = sorted(clean(src.get("source_id")) for src in matched if source_kind(src) == "cross_check")

        gaps: List[str] = []
        if not official and not team:
            gaps.append("missing official league/team source")
        elif target.get("needs_team_source") and not team:
            gaps.append("missing team/club source")
        if not wire:
            gaps.append("missing wire source")
        if not cross:
            gaps.append("missing scoreboard/stat/cross-check source")

        if not official and not team:
            status = "gap"
        elif target.get("needs_team_source") and not team:
            status = "watch"
        elif not wire or not cross:
            status = "watch"
        else:
            status = "covered"

        if gaps:
            next_step = target["next_step"]
        else:
            next_step = "Coverage is strong enough for normal manual review; keep monitoring existing free sources."

        rows.append(
            {
                "coverage_key": target["key"],
                "display_name": target["name"],
                "official_sources": "; ".join(official),
                "team_sources": "; ".join(team),
                "wire_sources": "; ".join(wire),
                "cross_check_sources": "; ".join(cross),
                "coverage_status": status,
                "coverage_gap": "; ".join(gaps) if gaps else "none",
                "operator_next_step": next_step,
            }
        )
    return rows


def intake_need_for_gap(gap: str) -> Dict[str, str] | None:
    if gap == "missing official league/team source":
        return {
            "needed_source_type": "official_or_team",
            "source_type": "official_site",
            "tier": "official",
            "allowed_use": "official_news; team_news; source_confirmation",
        }
    if gap == "missing team/club source":
        return {
            "needed_source_type": "team_or_club",
            "source_type": "official_site_collection",
            "tier": "official",
            "allowed_use": "team_news; roster_confirmation; source_confirmation",
        }
    if gap == "missing scoreboard/stat/cross-check source":
        return {
            "needed_source_type": "scoreboard_or_stats_cross_check",
            "source_type": "scoreboard_site",
            "tier": "stats_provider",
            "allowed_use": "cross_check; scores; schedules; standings",
        }
    if gap == "missing wire source":
        return {
            "needed_source_type": "free_wire_or_reputable_media",
            "source_type": "wire",
            "tier": "wire",
            "allowed_use": "second_source; context; source_confirmation",
        }
    return None


def build_intake_template(coverage_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for coverage in coverage_rows:
        if coverage.get("coverage_status") == "covered":
            continue
        gaps = [clean(gap) for gap in coverage.get("coverage_gap", "").split(";") if clean(gap) and clean(gap) != "none"]
        for gap in gaps:
            need = intake_need_for_gap(gap)
            if not need:
                continue
            rows.append(
                {
                    "coverage_key": coverage["coverage_key"],
                    "display_name": coverage["display_name"],
                    "needed_source_type": need["needed_source_type"],
                    "coverage_gap": gap,
                    "candidate_source_id": "",
                    "candidate_source_name": "",
                    "candidate_url": "",
                    "candidate_domain": "",
                    "source_type": need["source_type"],
                    "tier": need["tier"],
                    "trust_band": "green_candidate_after_operator_review",
                    "sport_league": coverage["display_name"],
                    "proposed_enabled": "No",
                    "automation_status": "disabled_manual_review_only",
                    "publish_policy": "proposal_only_not_publish_ready",
                    "allowed_use": need["allowed_use"],
                    "operator_verification_status": "unverified",
                    "registry_action": "proposal_only_do_not_import",
                    "review_notes": "Fill candidate fields only after checking the free public source manually.",
                }
            )
    return rows


def write_intake_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Intake Template",
        "",
        "Use this worksheet to propose free official, team, wire, or cross-check sources from coverage gaps.",
        "Rows are proposal-only and disabled by default. They do not update `config/source_registry.json`.",
        "",
        "## Guardrails",
        "",
        "- Free public sources only.",
        "- Keep `proposed_enabled` as `No` until a human review deliberately updates the source registry.",
        "- Social or gray-area sources remain discovery-only unless separately verified.",
        "- Do not add paywalled, login-only, private, or paid API sources.",
        "",
        "## Suggested rows",
        "",
    ]
    if not rows:
        lines.append("No open coverage gaps found.")
    else:
        for row in rows:
            lines.append(
                f"- {row['display_name']} | {row['needed_source_type']} | {row['coverage_gap']} | "
                f"{row['source_type']} | enabled: {row['proposed_enabled']} | action: {row['registry_action']}"
            )
    lines += ["", "See `source_registry_intake_template.csv` for the fillable worksheet.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def proposal_has_candidate(row: Dict[str, str]) -> bool:
    candidate_fields = [
        "candidate_source_id",
        "candidate_source_name",
        "candidate_url",
        "candidate_domain",
        "review_notes",
    ]
    return any(clean(row.get(field)) for field in candidate_fields)


def existing_registry_indexes(sources: List[Dict[str, Any]]) -> Dict[str, set[str]]:
    source_ids: set[str] = set()
    urls: set[str] = set()
    domains: set[str] = set()
    for src in sources:
        if not isinstance(src, dict):
            continue
        sid = lower(src.get("source_id"))
        if sid:
            source_ids.add(sid)
        for url in src.get("urls") or []:
            url_text = clean(url)
            if url_text:
                urls.add(url_text.lower().rstrip("/"))
                domain = domain_from_url(url_text)
                if domain:
                    domains.add(domain)
        for domain in src.get("domains") or []:
            domain_text = lower(domain).removeprefix("www.")
            if domain_text:
                domains.add(domain_text)
    return {"source_ids": source_ids, "urls": urls, "domains": domains}


def registry_presence_for_candidate(candidate: Dict[str, str], registry_indexes: Dict[str, set[str]]) -> str:
    sid = lower(candidate.get("candidate_source_id"))
    url = clean(candidate.get("candidate_url"))
    normalized_url = url.lower().rstrip("/")
    domain = domain_from_url(url)
    if sid and sid in registry_indexes["source_ids"]:
        return "source_id_already_exists"
    if normalized_url and normalized_url in registry_indexes["urls"]:
        return "url_already_exists"
    if domain and domain in registry_indexes["domains"]:
        return "domain_already_exists_check_duplicate"
    return "not_in_registry"


def proposal_pack_coverage_context(pack: Dict[str, Any], coverage_rows: List[Dict[str, str]]) -> Dict[str, str]:
    pack_key = clean(pack.get("pack_key"))
    for row in coverage_rows:
        if row.get("coverage_key") == pack_key:
            return row
    return {
        "coverage_key": pack_key,
        "display_name": clean(pack.get("display_name") or pack.get("pack_name")),
        "coverage_status": "gap",
        "coverage_gap": clean(pack.get("fallback_coverage_gap")) or "review current source coverage",
        "operator_next_step": clean(pack.get("fallback_operator_next_step")) or "Review free official/team/cross-check coverage manually.",
    }


def build_source_proposal_pack(sources: List[Dict[str, Any]], coverage_rows: List[Dict[str, str]], pack: Dict[str, Any]) -> List[Dict[str, str]]:
    registry_indexes = existing_registry_indexes(sources)
    coverage = proposal_pack_coverage_context(pack, coverage_rows)
    pack_key = clean(pack.get("pack_key"))
    pack_name = clean(pack.get("pack_name"))
    display_name = clean(pack.get("display_name") or coverage.get("display_name") or pack_name)
    current_gap = clean(coverage.get("coverage_gap")) or f"review current {display_name} coverage"
    current_status = clean(coverage.get("coverage_status")) or "review"
    rows: List[Dict[str, str]] = []
    for candidate in pack.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        url = clean(candidate.get("candidate_url"))
        presence = registry_presence_for_candidate(candidate, registry_indexes)
        note = (
            "Open and verify this free public page manually before copying it into "
            "`operator/inbox/source_registry_proposals.csv`. Keep proposed_enabled=No; "
            "this pack never updates config/source_registry.json."
        )
        if presence != "not_in_registry":
            note += f" Registry check: {presence}."
        rows.append(
            {
                "pack_key": pack_key,
                "pack_name": pack_name,
                "candidate_group": clean(candidate.get("candidate_group")),
                "suggested_priority": clean(candidate.get("suggested_priority")),
                "coverage_key": pack_key,
                "display_name": display_name,
                "needed_source_type": clean(candidate.get("needed_source_type")),
                "coverage_gap": clean(candidate.get("coverage_gap")) or current_gap,
                "candidate_source_id": clean(candidate.get("candidate_source_id")),
                "candidate_source_name": clean(candidate.get("candidate_source_name")),
                "candidate_url": url,
                "candidate_domain": domain_from_url(url),
                "source_type": clean(candidate.get("source_type")),
                "tier": clean(candidate.get("tier")),
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": display_name,
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": clean(candidate.get("allowed_use")),
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": f"Guided {display_name} pack candidate. Current coverage status: {current_status}; current gap: {current_gap}.",
                "source_basis": clean(candidate.get("source_basis")),
                "registry_presence": presence,
                "manual_review_note": note,
            }
        )
    return rows


def build_source_proposal_packs(sources: List[Dict[str, Any]], coverage_rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    return {
        clean(pack.get("pack_key")): build_source_proposal_pack(sources, coverage_rows, pack)
        for pack in SOURCE_PROPOSAL_PACKS
        if clean(pack.get("pack_key"))
    }


def source_proposal_pack_rows(pack_rows_by_key: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for pack in SOURCE_PROPOSAL_PACKS:
        rows.extend(pack_rows_by_key.get(clean(pack.get("pack_key")), []))
    return rows


def proposal_pack_group_is_official(row: Dict[str, str]) -> bool:
    group = clean(row.get("candidate_group"))
    return group.endswith("_official") or group in {"league_official", "team_official", "tournament_official"}


def build_source_proposal_pack_readiness(
    pack_rows_by_key: Dict[str, List[Dict[str, str]]],
    coverage_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    readiness_rows: List[Dict[str, str]] = []
    for pack in SOURCE_PROPOSAL_PACKS:
        key = clean(pack.get("pack_key"))
        rows = pack_rows_by_key.get(key, [])
        coverage = proposal_pack_coverage_context(pack, coverage_rows)
        official_rows = [row for row in rows if proposal_pack_group_is_official(row)]
        cross_check_rows = [row for row in rows if "cross_check" in row.get("candidate_group", "")]
        duplicate_rows = [
            row
            for row in rows
            if clean(row.get("registry_presence")) not in {"", "not_in_registry", "not_checked"}
        ]
        ready_rows = [
            row
            for row in rows
            if clean(row.get("registry_presence")) in {"", "not_in_registry", "not_checked"}
            and clean(row.get("proposed_enabled")).lower() == "no"
            and clean(row.get("registry_action")) == "proposal_only_do_not_import"
        ]
        missing_cues: List[str] = []
        if not rows:
            missing_cues.append("no guided candidates")
        if not official_rows:
            missing_cues.append("missing official/team/tournament candidate")
        if not cross_check_rows:
            missing_cues.append("missing cross-check candidate")

        if duplicate_rows:
            status = "needs_duplicate_review"
            label = "Duplicate review"
            next_step = "Review duplicate source IDs, URLs, or domains before copying any pack rows into manual proposals."
            review_cues = f"{len(duplicate_rows)} candidate(s) already resemble trusted registry coverage."
        elif missing_cues:
            status = "needs_source_freshness_check"
            label = "Freshness/source check"
            next_step = "Open candidate pages manually, confirm they are current free public sources, and add missing official or cross-check coverage before proposal."
            review_cues = "; ".join(missing_cues)
        else:
            status = "ready_for_registry_proposal"
            label = "Ready for proposal review"
            next_step = "Open top candidates manually for freshness, then copy selected rows into operator/inbox/source_registry_proposals.csv for deliberate review."
            review_cues = "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected."

        priority_rows = [row for row in ready_rows if clean(row.get("suggested_priority")) == "P1"] or ready_rows
        readiness_rows.append(
            {
                "pack_key": key,
                "pack_name": clean(pack.get("pack_name")),
                "display_name": clean(pack.get("display_name") or coverage.get("display_name") or pack.get("pack_name")),
                "readiness_status": status,
                "readiness_label": label,
                "candidate_rows": str(len(rows)),
                "official_candidates": str(len(official_rows)),
                "cross_check_candidates": str(len(cross_check_rows)),
                "duplicate_candidates": str(len(duplicate_rows)),
                "freshness_check_candidates": str(len(ready_rows)),
                "ready_candidates": str(len(ready_rows)),
                "coverage_status": clean(coverage.get("coverage_status")) or "review",
                "coverage_gap": clean(coverage.get("coverage_gap")) or "review current source coverage",
                "review_cues": review_cues,
                "next_step": next_step,
                "top_candidate_ids": "; ".join(row["candidate_source_id"] for row in priority_rows[:5]),
                "duplicate_candidate_ids": "; ".join(row["candidate_source_id"] for row in duplicate_rows[:5]),
                "output_csv": clean(pack.get("output_csv")),
                "output_md": clean(pack.get("output_md")),
            }
        )
    return readiness_rows


def write_source_proposal_pack_markdown(path: str | Path, rows: List[Dict[str, str]], coverage_rows: List[Dict[str, str]], pack: Dict[str, Any]) -> None:
    coverage = proposal_pack_coverage_context(pack, coverage_rows)
    pack_name = clean(pack.get("pack_name")) or "Source Proposal Pack"
    display_name = clean(pack.get("display_name")) or pack_name
    description = clean(pack.get("description")) or "Guided free-source candidates for manual review of source coverage gaps."
    lines = [
        f"# {pack_name}",
        "",
        description,
        "No rows are imported automatically, no sources are auto-enabled, and this pack does not publish anything.",
        "",
        "## Current Coverage",
        "",
        f"- status: {coverage.get('coverage_status') or 'review'}",
        f"- gap: {coverage.get('coverage_gap') or f'review current {display_name} coverage'}",
        f"- operator next step: {coverage.get('operator_next_step') or 'Review free official/team/cross-check coverage manually.'}",
        "",
        "## Guardrails",
        "",
        "- Free public pages only.",
        "- Open each candidate manually before proposing it.",
        "- Keep `proposed_enabled` as `No`.",
        "- Keep `registry_action` as `proposal_only_do_not_import`.",
        "- Do not use paid APIs, paywalled pages, login-only pages, private pages, auto-runs, or auto-publishing.",
        "",
        "## Candidate Rows",
        "",
    ]
    if not rows:
        lines.append("No proposal candidates were generated.")
    else:
        configured_groups = pack.get("group_order") if isinstance(pack.get("group_order"), list) else []
        row_groups = sorted({row.get("candidate_group") for row in rows if row.get("candidate_group")})
        for group in [*configured_groups, *[item for item in row_groups if item not in configured_groups]]:
            grouped = [row for row in rows if row.get("candidate_group") == group]
            if not grouped:
                continue
            lines += [f"### {group.replace('_', ' ').title()}", ""]
            for row in grouped:
                lines.append(
                    f"- {row['suggested_priority']} | {row['candidate_source_id']} | {row['candidate_source_name']} | "
                    f"{row['candidate_url']} | enabled: {row['proposed_enabled']} | action: {row['registry_action']} | "
                    f"registry: {row['registry_presence']}"
                )
            lines.append("")
    lines += [f"See `{pack.get('output_csv') or OUT_PROPOSAL_PACKS_CSV}` for copy-ready proposal rows.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def write_source_proposal_packs_markdown(path: str | Path, pack_rows_by_key: Dict[str, List[Dict[str, str]]], coverage_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Guided Source Proposal Packs",
        "",
        "Reusable free-source proposal packs for leagues with known coverage gaps.",
        "These packs are review guides only: no rows are imported automatically, no sources are auto-enabled, and nothing is published.",
        "",
        "## Guardrails",
        "",
        "- Free public pages only.",
        "- Keep `proposed_enabled` as `No`.",
        "- Keep `registry_action` as `proposal_only_do_not_import`.",
        "- Do not use paid APIs, paywalled pages, login-only pages, private pages, auto-runs, or auto-publishing.",
        "",
        "## Packs",
        "",
    ]
    if not pack_rows_by_key:
        lines.append("No guided source proposal packs are configured.")
    for pack in SOURCE_PROPOSAL_PACKS:
        key = clean(pack.get("pack_key"))
        rows = pack_rows_by_key.get(key, [])
        coverage = proposal_pack_coverage_context(pack, coverage_rows)
        official = sum(1 for row in rows if proposal_pack_group_is_official(row))
        cross_check = sum(1 for row in rows if "cross_check" in row.get("candidate_group", ""))
        lines += [
            f"### {clean(pack.get('pack_name')) or key}",
            "",
            f"- coverage status: {coverage.get('coverage_status') or 'review'}",
            f"- coverage gap: {coverage.get('coverage_gap') or 'review'}",
            f"- candidates: {len(rows)} total; {official} official/team; {cross_check} cross-check",
            f"- detailed report: `{pack.get('output_md') or ''}`",
            f"- detailed data: `{pack.get('output_csv') or ''}`",
            "",
        ]
        for row in rows[:6]:
            lines.append(
                f"- {row['suggested_priority']} | {row['candidate_group']} | {row['candidate_source_id']} | "
                f"{row['candidate_url']} | enabled: {row['proposed_enabled']} | action: {row['registry_action']}"
            )
        if len(rows) > 6:
            lines.append(f"- ... {len(rows) - 6} more candidates in the CSV.")
        lines.append("")
    lines += ["See `source_proposal_packs.csv` for every configured pack row.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def write_source_proposal_pack_readiness_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Guided Source Proposal Pack Readiness",
        "",
        "Operator-facing readiness cues for guided free-source packs.",
        "These cues do not enable sources, update the trusted registry, run automation, call paid APIs, or publish.",
        "",
        "## Guardrails",
        "",
        "- `ready_for_registry_proposal` means ready for manual proposal review, not ready to enable.",
        "- Open candidate pages manually for freshness before copying rows into `operator/inbox/source_registry_proposals.csv`.",
        "- Resolve duplicate, paid, login-only, social-only, and unsafe flags in the proposal review report before registry updates.",
        "",
    ]
    if not rows:
        lines.append("No guided source proposal pack readiness rows were generated.")
    else:
        lines += ["## Pack Readiness", ""]
        for row in rows:
            lines += [
                f"### {row['pack_name'] or row['display_name']}",
                "",
                f"- status: {row['readiness_status']} ({row['readiness_label']})",
                (
                    f"- candidates: {row['candidate_rows']} total; "
                    f"{row['official_candidates']} official/team/tournament; "
                    f"{row['cross_check_candidates']} cross-check; "
                    f"{row['duplicate_candidates']} duplicate review"
                ),
                f"- coverage: {row['coverage_status']} | {row['coverage_gap']}",
                f"- cues: {row['review_cues']}",
                f"- top candidates: {row['top_candidate_ids'] or 'none'}",
                f"- next step: {row['next_step']}",
                f"- details: `{row['output_md']}` / `{row['output_csv']}`",
                "",
            ]
    write_text(path, "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def split_semicolon_ids(value: str) -> List[str]:
    return [clean(item) for item in value.split(";") if clean(item)]


def build_source_registry_proposal_draft(
    pack_rows_by_key: Dict[str, List[Dict[str, str]]],
    readiness_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    draft_rows: List[Dict[str, str]] = []
    for readiness in readiness_rows:
        pack_key = clean(readiness.get("pack_key"))
        pack_rows = pack_rows_by_key.get(pack_key, [])
        by_id = {row["candidate_source_id"]: row for row in pack_rows if row.get("candidate_source_id")}
        selected_ids = split_semicolon_ids(clean(readiness.get("top_candidate_ids")))
        if not selected_ids:
            selected_ids = [
                row["candidate_source_id"]
                for row in pack_rows
                if clean(row.get("registry_presence")) in {"", "not_in_registry", "not_checked"}
            ][:5]

        status = clean(readiness.get("readiness_status")) or "review"
        duplicate_ids = clean(readiness.get("duplicate_candidate_ids"))
        if status == "ready_for_registry_proposal":
            draft_status = "ready_to_copy_after_freshness_check"
            draft_action = "manual_copy_to_inbox_after_freshness_check"
        elif status == "needs_duplicate_review":
            draft_status = "blocked_duplicate_review"
            draft_action = "hold_do_not_copy_until_duplicate_review"
        elif status == "needs_source_freshness_check":
            draft_status = "blocked_source_freshness_check"
            draft_action = "hold_do_not_copy_until_source_freshness_check"
        else:
            draft_status = "blocked_manual_review"
            draft_action = "hold_do_not_copy_until_manual_review"

        duplicate_warning = (
            f"Duplicate review required for pack; duplicate candidate IDs: {duplicate_ids}."
            if duplicate_ids
            else "No duplicate candidates detected in this pack."
        )
        freshness_warning = "Open this public page manually and confirm it is current before copying to the inbox."
        readiness_warning = clean(readiness.get("review_cues")) or "Review this pack manually before copying rows."

        for candidate_id in selected_ids[:5]:
            row = by_id.get(candidate_id)
            if not row:
                continue
            draft = {field: clean(row.get(field)) for field in INTAKE_FIELDS}
            draft.update(
                {
                    "draft_selection_status": draft_status,
                    "draft_action": draft_action,
                    "pack_key": pack_key,
                    "pack_name": clean(readiness.get("pack_name") or row.get("pack_name")),
                    "pack_readiness_status": status,
                    "pack_readiness_label": clean(readiness.get("readiness_label")),
                    "candidate_group": clean(row.get("candidate_group")),
                    "suggested_priority": clean(row.get("suggested_priority")),
                    "source_basis": clean(row.get("source_basis")),
                    "registry_presence": clean(row.get("registry_presence")) or "not_checked",
                    "readiness_warning": readiness_warning,
                    "duplicate_warning": duplicate_warning,
                    "freshness_warning": freshness_warning,
                    "manual_review_note": (
                        f"{clean(row.get('manual_review_note'))} "
                        "This is a draft row only; copying into operator/inbox/source_registry_proposals.csv is a manual operator decision."
                    ).strip(),
                }
            )
            draft["proposed_enabled"] = "No"
            draft["automation_status"] = "disabled_manual_review_only"
            draft["publish_policy"] = "proposal_only_not_publish_ready"
            draft["operator_verification_status"] = "unverified"
            draft["registry_action"] = "proposal_only_do_not_import"
            draft_rows.append(draft)
    return draft_rows


def write_source_registry_proposal_draft_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Proposal Draft",
        "",
        "Selected guided-pack rows for manual proposal drafting.",
        "This file is not the trusted registry and is not the live proposal inbox.",
        "",
        "## Guardrails",
        "",
        "- Review this draft before copying any row into `operator/inbox/source_registry_proposals.csv`.",
        "- Rows marked `blocked_*` are do-not-copy until the duplicate or freshness warning is resolved.",
        "- Keep `proposed_enabled` as `No` and `registry_action` as `proposal_only_do_not_import`.",
        "- No sources are enabled, no registry files are updated, no paid APIs are called, and nothing is published.",
        "",
        "## Draft Rows",
        "",
    ]
    if not rows:
        lines.append("No draft rows were generated. Review `source_proposal_pack_readiness.md` first.")
    else:
        for row in rows:
            lines.append(
                f"- **{row['draft_selection_status']}** | {row['pack_name']} | "
                f"{row['candidate_source_id']} | {row['candidate_url']} | action: {row['draft_action']} | "
                f"registry: {row['registry_presence']} | warning: {row['readiness_warning']}"
            )
    lines += ["", "Use `source_registry_proposal_draft.csv` for copy-ready field structure after manual review.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def proposal_draft_row_directly_duplicates(row: Dict[str, str]) -> bool:
    presence = clean(row.get("registry_presence"))
    return presence not in {"", "not_in_registry", "not_checked"}


def build_source_registry_proposal_promotion_checklist(draft_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    checklist_rows: List[Dict[str, str]] = []
    for row in draft_rows:
        direct_duplicate = proposal_draft_row_directly_duplicates(row)
        status = clean(row.get("draft_selection_status"))
        if status == "ready_to_copy_after_freshness_check":
            decision = "verify_then_copy"
            operator_step = "1_verify_public_page_then_2_copy_to_manual_inbox"
            copy_allowed = "Yes_after_manual_freshness_check"
            hold_reason = ""
            discard_reason = ""
            copy_instructions = (
                "After opening the public URL and confirming it is current/free/login-free, copy this row into "
                "`operator/inbox/source_registry_proposals.csv`; keep proposed_enabled=No and registry_action=proposal_only_do_not_import."
            )
        elif direct_duplicate:
            decision = "discard"
            operator_step = "discard_duplicate_candidate_do_not_copy"
            copy_allowed = "No"
            hold_reason = ""
            discard_reason = f"Candidate already resembles trusted registry coverage: {clean(row.get('registry_presence'))}."
            copy_instructions = "Do not copy this row into the manual proposal inbox unless the registry duplicate is proven false."
        else:
            decision = "hold"
            operator_step = "hold_until_warning_resolved"
            copy_allowed = "No"
            hold_reason = clean(row.get("duplicate_warning")) or clean(row.get("readiness_warning")) or "Resolve draft warning before copying."
            discard_reason = ""
            copy_instructions = "Hold this row in the draft until duplicate and freshness warnings are resolved."

        verification_checklist = " | ".join(
            [
                "open candidate_url manually",
                "confirm source is free public and does not require login",
                "confirm page is current enough for the intended use",
                "confirm source is not paid/API/private/social-only unless explicitly operator-verified",
                "keep proposed_enabled=No",
                "keep registry_action=proposal_only_do_not_import",
            ]
        )
        checklist_rows.append(
            {
                "checklist_decision": decision,
                "operator_step": operator_step,
                "copy_allowed": copy_allowed,
                "copy_target": "operator/inbox/source_registry_proposals.csv" if decision == "verify_then_copy" else "",
                "pack_key": clean(row.get("pack_key")),
                "pack_name": clean(row.get("pack_name")),
                "candidate_source_id": clean(row.get("candidate_source_id")),
                "candidate_source_name": clean(row.get("candidate_source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": clean(row.get("candidate_domain")),
                "source_type": clean(row.get("source_type")),
                "tier": clean(row.get("tier")),
                "sport_league": clean(row.get("sport_league")),
                "allowed_use": clean(row.get("allowed_use")),
                "registry_presence": clean(row.get("registry_presence")) or "not_checked",
                "draft_selection_status": status,
                "draft_action": clean(row.get("draft_action")),
                "duplicate_warning": clean(row.get("duplicate_warning")),
                "freshness_warning": clean(row.get("freshness_warning")),
                "readiness_warning": clean(row.get("readiness_warning")),
                "verification_checklist": verification_checklist,
                "copy_instructions": copy_instructions,
                "hold_reason": hold_reason,
                "discard_reason": discard_reason,
                "proposed_enabled": "No",
                "registry_action": "proposal_only_do_not_import",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
            }
        )
    return checklist_rows


def write_source_registry_proposal_promotion_checklist_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Proposal Promotion Checklist",
        "",
        "Manual operator checklist for draft source proposal rows before any trusted registry edit.",
        "This report does not copy rows, enable sources, update the registry, run automation, call paid APIs, or publish.",
        "",
        "## Summary",
        "",
        f"- verify then copy: {sum(1 for row in rows if row['checklist_decision'] == 'verify_then_copy')}",
        f"- hold: {sum(1 for row in rows if row['checklist_decision'] == 'hold')}",
        f"- discard: {sum(1 for row in rows if row['checklist_decision'] == 'discard')}",
        "",
        "## Guardrails",
        "",
        "- Copy only rows marked `verify_then_copy`, and only after manually opening the URL.",
        "- Hold rows marked `hold` until their duplicate or freshness warnings are resolved.",
        "- Discard rows marked `discard` unless a human proves the duplicate signal is wrong.",
        "- Keep `proposed_enabled=No` and `registry_action=proposal_only_do_not_import`.",
        "",
        "## Checklist Rows",
        "",
    ]
    if not rows:
        lines.append("No promotion checklist rows were generated.")
    else:
        for row in rows:
            reason = row.get("hold_reason") or row.get("discard_reason") or row.get("freshness_warning")
            lines.append(
                f"- **{row['checklist_decision']}** | {row['candidate_source_id']} | "
                f"{row['operator_step']} | copy: {row['copy_allowed']} | target: {row['copy_target'] or 'none'} | "
                f"reason: {reason}"
            )
    lines += ["", "Use `source_registry_proposal_promotion_checklist.csv` for the full field-level checklist.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def proposed_trust_band(row: Dict[str, str]) -> str:
    tier = lower(row.get("tier"))
    source_type = lower(row.get("source_type"))
    if tier in GREEN_TIERS or source_type in {"official_site", "official_site_collection", "scoreboard_site", "wire"}:
        return "green_after_operator_verification"
    return "yellow_manual_review"


def proposed_registry_source_json(row: Dict[str, str]) -> str:
    url = clean(row.get("candidate_url"))
    domain = clean(row.get("candidate_domain")) or domain_from_url(url)
    source = {
        "source_id": clean(row.get("candidate_source_id")),
        "source_type": clean(row.get("source_type")),
        "enabled": False,
        "tier": clean(row.get("tier")),
        "trust_band": proposed_trust_band(row),
        "sport_league": clean(row.get("sport_league")),
        "urls": [url] if url else [],
        "domains": [domain] if domain else [],
        "allowed_use": split_semicolon_ids(clean(row.get("allowed_use"))),
        "publish_policy": "not_publish_ready_until_operator_verifies_and_enables",
        "automation_status": "disabled_manual_review_only",
    }
    return json.dumps(source, sort_keys=True, separators=(",", ":"))


def build_source_registry_update_worksheet(checklist_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    worksheet_rows: List[Dict[str, str]] = []
    for row in checklist_rows:
        if clean(row.get("checklist_decision")) != "verify_then_copy":
            continue
        source_id = clean(row.get("candidate_source_id"))
        registry_presence = clean(row.get("registry_presence")) or "not_checked"
        proposed_json = proposed_registry_source_json(row)
        worksheet_rows.append(
            {
                "worksheet_decision": "manual_registry_plan_after_verification",
                "operator_step": "1_open_url_2_confirm_free_public_current_3_compare_json_4_edit_registry_manually_if_approved",
                "manual_edit_target": REGISTRY,
                "manual_edit_allowed": "Yes_only_after_operator_verification",
                "auto_edit_status": "not_performed_by_generator",
                "pack_key": clean(row.get("pack_key")),
                "pack_name": clean(row.get("pack_name")),
                "source_id": source_id,
                "source_name": clean(row.get("candidate_source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": clean(row.get("candidate_domain")),
                "source_type": clean(row.get("source_type")),
                "tier": clean(row.get("tier")),
                "trust_band": proposed_trust_band(row),
                "sport_league": clean(row.get("sport_league")),
                "allowed_use": clean(row.get("allowed_use")),
                "registry_presence": registry_presence,
                "checklist_decision": clean(row.get("checklist_decision")),
                "checklist_copy_target": clean(row.get("copy_target")),
                "verification_gate": (
                    "Operator must open the public URL, confirm it is free/login-free/current, "
                    "confirm it is not duplicate registry coverage, and confirm allowed_use before editing."
                ),
                "current_registry_state": (
                    f"Before: no approved trusted-registry object should be added for {source_id} until "
                    f"manual verification is complete. Current registry signal: {registry_presence}."
                ),
                "proposed_enabled": "False",
                "proposed_automation_status": "disabled_manual_review_only",
                "proposed_publish_policy": "not_publish_ready_until_operator_verifies_and_enables",
                "proposed_source_json": proposed_json,
                "before_after_diff": (
                    f"Before: no manual change from this generator. After manual approval only: append the disabled "
                    f"source object for {source_id} to config/source_registry.json sources[]."
                ),
                "rollback_note": (
                    f"If verification fails or the manual registry edit is wrong, remove the manually added "
                    f"sources[] object with source_id={source_id} and rerun review."
                ),
                "review_notes": (
                    "Review-only worksheet row. It does not edit the trusted registry, enable sources, run automation, "
                    "call paid APIs, or publish."
                ),
            }
        )
    return worksheet_rows


def write_source_registry_update_worksheet_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Update Worksheet",
        "",
        "Review-only registry change plan for checklist rows that are candidates for manual verification.",
        "This worksheet does not edit `config/source_registry.json`, enable sources, run automation, call paid APIs, or publish.",
        "",
        "## Summary",
        "",
        f"- worksheet rows: {len(rows)}",
        f"- manual edit target: `{REGISTRY}`",
        "- default proposed state: disabled/manual-review-only/not publish-ready",
        "",
        "## Operator Gates",
        "",
        "- Open each candidate URL manually.",
        "- Confirm the page is free, public, current, and login-free.",
        "- Confirm the row is not duplicate trusted-registry coverage.",
        "- Compare the proposed JSON before any hand edit.",
        "- Keep the proposed source disabled unless a later human review intentionally changes that.",
        "- Use the rollback note if the manual edit fails review.",
        "",
        "## Worksheet Rows",
        "",
    ]
    if not rows:
        lines.append("No registry update worksheet rows were generated. Work the promotion checklist first.")
    else:
        for row in rows:
            lines += [
                f"- **{row['source_id']}** | {row['source_name']} | {row['candidate_url']}",
                f"  - decision: {row['worksheet_decision']}",
                f"  - target: `{row['manual_edit_target']}` | edit: {row['manual_edit_allowed']} | auto: {row['auto_edit_status']}",
                f"  - before/after: {row['before_after_diff']}",
                f"  - rollback: {row['rollback_note']}",
            ]
    lines += ["", "Use `source_registry_update_worksheet.csv` for proposed JSON and field-level review.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def parse_proposed_source_json(value: str) -> tuple[Dict[str, Any], str]:
    try:
        parsed = json.loads(clean(value))
    except Exception:
        return {}, "invalid_json"
    if not isinstance(parsed, dict):
        return {}, "invalid_json"
    return parsed, "valid_json"


def proposed_source_domains(row: Dict[str, str], proposed: Dict[str, Any]) -> List[str]:
    domains = [lower(item).removeprefix("www.") for item in proposed.get("domains", []) if clean(item)]
    if not domains:
        candidate_domain = lower(row.get("candidate_domain")).removeprefix("www.")
        if candidate_domain:
            domains.append(candidate_domain)
    if not domains:
        domain = domain_from_url(clean(row.get("candidate_url")))
        if domain:
            domains.append(domain)
    return sorted(set(domains))


def proposed_source_urls(row: Dict[str, str], proposed: Dict[str, Any]) -> List[str]:
    urls = [clean(item).lower().rstrip("/") for item in proposed.get("urls", []) if clean(item)]
    if not urls and clean(row.get("candidate_url")):
        urls.append(clean(row.get("candidate_url")).lower().rstrip("/"))
    return sorted(set(urls))


def build_source_registry_diff_review(
    sources: List[Dict[str, Any]],
    worksheet_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    registry_indexes = existing_registry_indexes(sources)
    seen_ids: set[str] = set()
    seen_domains: set[str] = set()
    review_rows: List[Dict[str, str]] = []
    allowed_trust_bands = {"green_after_operator_verification", "yellow_manual_review"}
    for row in worksheet_rows:
        issues: List[str] = []
        flags: List[str] = []
        proposed, json_status = parse_proposed_source_json(clean(row.get("proposed_source_json")))
        source_id = lower(proposed.get("source_id") or row.get("source_id"))
        domains = proposed_source_domains(row, proposed)
        urls = proposed_source_urls(row, proposed)
        trust_band = clean(proposed.get("trust_band") or row.get("trust_band"))
        proposed_enabled = proposed.get("enabled")
        automation_status = clean(proposed.get("automation_status") or row.get("proposed_automation_status"))
        publish_policy = clean(proposed.get("publish_policy") or row.get("proposed_publish_policy"))
        rollback_note = lower(row.get("rollback_note"))
        before_after = lower(row.get("before_after_diff"))
        registry_source_id_match = "Yes" if source_id and source_id in registry_indexes["source_ids"] else "No"
        registry_url_matches = [url for url in urls if url in registry_indexes["urls"]]
        registry_domain_matches = [domain for domain in domains if domain in registry_indexes["domains"]]
        worksheet_domain_matches = [domain for domain in domains if domain in seen_domains]

        if json_status != "valid_json":
            issues.append("proposed_source_json is missing or invalid")
            flags.append("invalid_json")
        if not source_id:
            issues.append("missing proposed source_id")
            flags.append("missing_source_id")
        elif source_id in registry_indexes["source_ids"]:
            issues.append("duplicate source_id already exists in trusted registry")
            flags.append("duplicate_source_id")
        elif source_id in seen_ids:
            issues.append("duplicate source_id appears more than once in this worksheet")
            flags.append("duplicate_source_id")
        if source_id:
            seen_ids.add(source_id)

        if registry_url_matches:
            issues.append(f"duplicate URL already exists in trusted registry: {'; '.join(registry_url_matches)}")
            flags.append("duplicate_url")
        if registry_domain_matches:
            issues.append(f"candidate domain already exists in trusted registry: {'; '.join(registry_domain_matches)}")
            flags.append("duplicate_domain")
        if worksheet_domain_matches:
            issues.append(f"candidate domain is repeated inside this worksheet: {'; '.join(worksheet_domain_matches)}")
            flags.append("worksheet_domain_repeat")
        for domain in domains:
            seen_domains.add(domain)

        if proposed_enabled is not False or clean(row.get("proposed_enabled")) != "False":
            issues.append("proposed source must stay disabled before manual registry approval")
            flags.append("enabled_risk")
        if trust_band not in allowed_trust_bands:
            issues.append(f"risky or unexpected trust_band for manual proposal: {trust_band or 'missing'}")
            flags.append("risky_trust_band")
        if automation_status != "disabled_manual_review_only":
            issues.append("automation_status must remain disabled_manual_review_only")
            flags.append("automation_risk")
        if "not_publish_ready" not in publish_policy:
            issues.append("publish_policy must stay not publish-ready until operator verification")
            flags.append("publish_risk")
        if "remove" not in rollback_note or source_id not in rollback_note:
            issues.append("rollback note must say how to remove the proposed source_id")
            flags.append("missing_rollback")
        if "before" not in before_after or "after" not in before_after:
            issues.append("before/after diff note is missing before or after coverage")
            flags.append("missing_diff_note")
        if clean(row.get("auto_edit_status")) != "not_performed_by_generator":
            issues.append("auto edit status must be not_performed_by_generator")
            flags.append("auto_edit_risk")

        blocking_flags = {
            "invalid_json",
            "missing_source_id",
            "duplicate_source_id",
            "duplicate_url",
            "duplicate_domain",
            "enabled_risk",
            "risky_trust_band",
            "automation_risk",
            "publish_risk",
            "missing_rollback",
            "missing_diff_note",
            "auto_edit_risk",
        }
        if any(flag in blocking_flags for flag in flags):
            status = "HOLD"
            recommendation = "Do not manually edit the trusted registry until blocking diff issues are resolved."
        elif flags:
            status = "REVIEW"
            recommendation = "Review repeated worksheet coverage before any manual registry edit."
        else:
            status = "PASS"
            recommendation = "Structurally clean for human verification; still do not edit until the operator approves."

        review_rows.append(
            {
                "diff_review_status": status,
                "issue_count": str(len(issues)),
                "issues": "; ".join(issues) if issues else "none",
                "flags": "; ".join(sorted(set(flags))) if flags else "none",
                "operator_step": "review_diff_then_verify_url_before_manual_registry_edit",
                "manual_edit_target": clean(row.get("manual_edit_target")) or REGISTRY,
                "source_id": clean(row.get("source_id") or proposed.get("source_id")),
                "source_name": clean(row.get("source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": "; ".join(domains) if domains else clean(row.get("candidate_domain")),
                "proposed_enabled": clean(row.get("proposed_enabled")),
                "proposed_trust_band": trust_band,
                "proposed_automation_status": automation_status,
                "proposed_publish_policy": publish_policy,
                "registry_source_id_match": registry_source_id_match,
                "registry_url_match": "; ".join(registry_url_matches) if registry_url_matches else "No",
                "registry_domain_match": "; ".join(registry_domain_matches) if registry_domain_matches else "No",
                "worksheet_domain_match": "; ".join(worksheet_domain_matches) if worksheet_domain_matches else "No",
                "rollback_status": "present" if "missing_rollback" not in flags else "missing_or_incomplete",
                "proposed_json_status": json_status,
                "before_after_status": "present" if "missing_diff_note" not in flags else "missing_or_incomplete",
                "auto_edit_status": clean(row.get("auto_edit_status")),
                "recommendation": recommendation,
            }
        )
    return review_rows


def write_source_registry_diff_review_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Diff Review",
        "",
        "Read-only diff preflight for source registry worksheet rows before any human edits `config/source_registry.json`.",
        "This review compares proposed disabled source objects against the current trusted registry and does not edit files, enable sources, run automation, call paid APIs, or publish.",
        "",
        "## Summary",
        "",
        f"- pass: {sum(1 for row in rows if row['diff_review_status'] == 'PASS')}",
        f"- review: {sum(1 for row in rows if row['diff_review_status'] == 'REVIEW')}",
        f"- hold: {sum(1 for row in rows if row['diff_review_status'] == 'HOLD')}",
        "",
        "## Guardrails",
        "",
        "- HOLD rows must not be manually added to `config/source_registry.json`.",
        "- REVIEW rows need a human duplicate-domain judgment before any manual edit.",
        "- PASS rows still require manual URL verification and operator approval.",
        "- Keep proposed sources disabled/manual-review-only/not publish-ready.",
        "",
        "## Diff Rows",
        "",
    ]
    if not rows:
        lines.append("No diff review rows were generated. Work the registry update worksheet first.")
    else:
        for row in rows:
            lines.append(
                f"- **{row['diff_review_status']}** | {row['source_id']} | flags: {row['flags']} | "
                f"issues: {row['issues']} | recommendation: {row['recommendation']}"
            )
    lines += ["", "Use `source_registry_diff_review.csv` for field-level duplicate, trust, and rollback checks.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def manual_verification_rows_by_source_id(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {clean(row.get("source_id")): row for row in rows if clean(row.get("source_id"))}


def build_source_registry_verification_log(
    diff_review_rows: List[Dict[str, str]],
    manual_rows: List[Dict[str, str]] | None = None,
) -> List[Dict[str, str]]:
    manual_by_id = manual_verification_rows_by_source_id(manual_rows or [])
    log_rows: List[Dict[str, str]] = []
    for row in diff_review_rows:
        source_id = clean(row.get("source_id"))
        manual = manual_by_id.get(source_id, {})
        manual_has_outcome = bool(clean(manual.get("approval_outcome")) or clean(manual.get("freshness_result")) or clean(manual.get("duplicate_decision")))
        log_rows.append(
            {
                "verification_log_status": "operator_review_recorded" if manual_has_outcome else "operator_input_required",
                "operator_step": "open_url_record_freshness_duplicate_decision_and_approval_outcome",
                "source_id": source_id,
                "source_name": clean(row.get("source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": clean(row.get("candidate_domain")),
                "diff_review_status": clean(row.get("diff_review_status")),
                "diff_flags": clean(row.get("flags")),
                "diff_issues": clean(row.get("issues")),
                "registry_domain_match": clean(row.get("registry_domain_match")),
                "worksheet_domain_match": clean(row.get("worksheet_domain_match")),
                "url_checked": clean(manual.get("url_checked")),
                "checked_at_local": clean(manual.get("checked_at_local")),
                "freshness_result": clean(manual.get("freshness_result")),
                "duplicate_decision": clean(manual.get("duplicate_decision")),
                "approval_outcome": clean(manual.get("approval_outcome")),
                "registry_edit_decision": clean(manual.get("registry_edit_decision")),
                "operator_name": clean(manual.get("operator_name")),
                "evidence_url": clean(manual.get("evidence_url")),
                "operator_notes": clean(manual.get("operator_notes")),
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "verification_log_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        )
    return log_rows


def source_id_index(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {clean(row.get("source_id")): row for row in rows if clean(row.get("source_id"))}


def approval_packet_hold_reason(row: Dict[str, str]) -> str:
    reasons: List[str] = []
    if clean(row.get("diff_review_status")) == "HOLD":
        reasons.append("diff review is HOLD")
    if not clean(row.get("url_checked")):
        reasons.append("missing url_checked")
    if clean(row.get("freshness_result")) != "current":
        reasons.append("freshness_result is not current")
    if clean(row.get("duplicate_decision")) not in {"not_duplicate", "same_domain_ok"}:
        reasons.append("duplicate_decision is not approved")
    if not clean(row.get("evidence_url")):
        reasons.append("missing evidence_url")
    if clean(row.get("registry_edit_decision")) not in {"manual_edit_planned", "manual_edit_completed_by_operator"}:
        reasons.append("registry_edit_decision is not manual_edit_planned or manual_edit_completed_by_operator")
    return "; ".join(reasons) if reasons else "none"


def build_source_registry_approval_packet(
    verification_log_rows: List[Dict[str, str]],
    worksheet_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    worksheet_by_id = source_id_index(worksheet_rows)
    packet_rows: List[Dict[str, str]] = []
    for row in verification_log_rows:
        if clean(row.get("approval_outcome")) != "approved_for_manual_registry_edit":
            continue
        source_id = clean(row.get("source_id"))
        worksheet = worksheet_by_id.get(source_id, {})
        exact_json = clean(worksheet.get("proposed_source_json"))
        hold_reason = approval_packet_hold_reason(row)
        packet_rows.append(
            {
                "approval_packet_status": "ready_for_final_manual_review" if hold_reason == "none" else "hold_before_manual_registry_edit",
                "source_id": source_id,
                "source_name": clean(row.get("source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": clean(row.get("candidate_domain")),
                "manual_edit_target": clean(worksheet.get("manual_edit_target")) or REGISTRY,
                "exact_proposed_source_json": exact_json,
                "url_checked": clean(row.get("url_checked")),
                "checked_at_local": clean(row.get("checked_at_local")),
                "freshness_result": clean(row.get("freshness_result")),
                "duplicate_decision": clean(row.get("duplicate_decision")),
                "approval_outcome": clean(row.get("approval_outcome")),
                "registry_edit_decision": clean(row.get("registry_edit_decision")),
                "evidence_url": clean(row.get("evidence_url")),
                "operator_name": clean(row.get("operator_name")),
                "operator_notes": clean(row.get("operator_notes")),
                "diff_review_status": clean(row.get("diff_review_status")),
                "diff_flags": clean(row.get("diff_flags")),
                "diff_issues": clean(row.get("diff_issues")),
                "hold_reason": hold_reason,
                "approval_guardrails": "final_review_only_no_auto_edit_keep_disabled_until_manual_registry_review",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "approval_packet_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        )
    return packet_rows


def write_source_registry_approval_packet_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Approval Packet",
        "",
        "Final review packet for verification-log rows explicitly marked `approved_for_manual_registry_edit`.",
        "This packet does not edit `config/source_registry.json`, enable sources, run automation, call paid APIs, or publish.",
        "",
        "## Summary",
        "",
        f"- approved rows summarized: {len(rows)}",
        f"- ready for final manual review: {sum(1 for row in rows if row['approval_packet_status'] == 'ready_for_final_manual_review')}",
        f"- held before manual edit: {sum(1 for row in rows if row['approval_packet_status'] == 'hold_before_manual_registry_edit')}",
        "",
        "## Guardrails",
        "",
        "- Include only rows the operator marked `approved_for_manual_registry_edit`.",
        "- Treat `hold_before_manual_registry_edit` rows as blocked until the hold reason is resolved.",
        "- Use the exact JSON for final human comparison only; this generator never applies it.",
        "- Keep sources disabled until a deliberate human registry review changes that.",
        "",
        "## Approved Rows",
        "",
    ]
    if not rows:
        lines.append("No approved verification-log rows were found. Fill `operator/inbox/source_registry_verification_log.csv` before building an approval packet.")
    else:
        for row in rows:
            lines += [
                f"- **{row['approval_packet_status']}** | {row['source_id']} | {row['candidate_url']}",
                f"  - evidence: {row['evidence_url'] or 'missing'} | checked: {row['checked_at_local'] or 'missing'}",
                f"  - freshness: {row['freshness_result'] or 'missing'} | duplicate: {row['duplicate_decision'] or 'missing'}",
                f"  - hold reason: {row['hold_reason']}",
                f"  - exact JSON: `{row['exact_proposed_source_json']}`",
            ]
    lines += ["", "Use `source_registry_approval_packet.csv` for field-level final review.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def registry_source_by_id(sources: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {clean(src.get("source_id")): src for src in sources if isinstance(src, dict) and clean(src.get("source_id"))}


def compact_json(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def pretty_json(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, indent=2)


def build_source_registry_patch_preview(
    approval_packet_rows: List[Dict[str, str]],
    sources: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    registry_by_id = registry_source_by_id(sources)
    source_count = len([src for src in sources if isinstance(src, dict)])
    preview_rows: List[Dict[str, str]] = []
    for row in approval_packet_rows:
        if clean(row.get("approval_packet_status")) != "ready_for_final_manual_review":
            continue
        source_id = clean(row.get("source_id"))
        proposed, json_status = parse_proposed_source_json(clean(row.get("exact_proposed_source_json")))
        existing = registry_by_id.get(source_id)
        status = "ready_for_manual_copy_paste" if json_status == "valid_json" and not existing else "hold_before_manual_patch"
        existing_state = compact_json(existing) if existing else ""
        proposed_json = pretty_json(proposed) if json_status == "valid_json" else clean(row.get("exact_proposed_source_json"))
        before = (
            f"Existing sources[] object with source_id={source_id}: {existing_state}"
            if existing
            else f"No sources[] object with source_id={source_id} is present in the current trusted registry."
        )
        after = (
            f"Append this disabled source object to sources[] for source_id={source_id}: {compact_json(proposed)}"
            if json_status == "valid_json"
            else f"Cannot build after preview because exact_proposed_source_json is {json_status}."
        )
        hold_reason = "none"
        if json_status != "valid_json":
            hold_reason = "exact_proposed_source_json is invalid"
        elif existing:
            hold_reason = "source_id already exists in current registry"
        preview_rows.append(
            {
                "patch_preview_status": status,
                "source_id": source_id,
                "source_name": clean(row.get("source_name")),
                "manual_edit_target": clean(row.get("manual_edit_target")) or REGISTRY,
                "registry_before_summary": (
                    f"Current registry has {source_count} sources[] object(s). "
                    f"source_id={source_id} present: {'Yes' if existing else 'No'}."
                ),
                "side_by_side_before": before,
                "side_by_side_after": after,
                "copy_paste_source_json": proposed_json,
                "copy_paste_patch_instructions": (
                    f"Manual only: open {REGISTRY}, append the copy_paste_source_json object to sources[], "
                    "keep enabled=false and automation_status=disabled_manual_review_only, save, then rerun review."
                ),
                "rollback_instructions": (
                    f"If final review fails, manually remove the sources[] object with source_id={source_id} and rerun review."
                ),
                "url_checked": clean(row.get("url_checked")),
                "evidence_url": clean(row.get("evidence_url")),
                "freshness_result": clean(row.get("freshness_result")),
                "duplicate_decision": clean(row.get("duplicate_decision")),
                "approval_packet_status": clean(row.get("approval_packet_status")),
                "hold_reason": hold_reason,
                "preview_guardrails": "manual_copy_paste_preview_only_no_auto_edit_keep_disabled_until_human_registry_review",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "patch_preview_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        )
    return preview_rows


def write_source_registry_patch_preview_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Patch Preview",
        "",
        "Manual copy/paste preview for ready approval-packet rows only.",
        "This preview does not edit `config/source_registry.json`, enable sources, run automation, call paid APIs, or publish.",
        "",
        "## Summary",
        "",
        f"- patch preview rows: {len(rows)}",
        f"- ready for manual copy/paste: {sum(1 for row in rows if row['patch_preview_status'] == 'ready_for_manual_copy_paste')}",
        f"- held before manual patch: {sum(1 for row in rows if row['patch_preview_status'] == 'hold_before_manual_patch')}",
        "",
        "## Guardrails",
        "",
        "- Include only approval-packet rows marked `ready_for_final_manual_review`.",
        "- Treat this as copy/paste guidance for a human; this generator never applies the patch.",
        "- Keep every previewed source disabled until a deliberate human registry review changes that.",
        "- Rerun review after any human edit and use the rollback instruction if the edit fails review.",
        "",
        "## Patch Preview Rows",
        "",
    ]
    if not rows:
        lines.append("No ready approval-packet rows were found. Complete the verification log and approval packet first.")
    else:
        for row in rows:
            lines += [
                f"### {row['source_id']}",
                "",
                f"- status: {row['patch_preview_status']}",
                f"- target: `{row['manual_edit_target']}`",
                f"- evidence: {row['evidence_url'] or 'missing'}",
                f"- hold reason: {row['hold_reason']}",
                "",
                "| Before | After |",
                "| --- | --- |",
                f"| {row['side_by_side_before']} | {row['side_by_side_after']} |",
                "",
                "Copy/paste source JSON:",
                "",
                "```json",
                row["copy_paste_source_json"],
                "```",
                "",
                f"Instructions: {row['copy_paste_patch_instructions']}",
                f"Rollback: {row['rollback_instructions']}",
                "",
            ]
    lines += ["", "Use `source_registry_patch_preview.csv` for field-level final review.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def write_source_registry_verification_log_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Registry Verification Log",
        "",
        "Manual operator log for recording checks after the registry diff review and before any human registry edit.",
        "This log does not edit `config/source_registry.json`, enable sources, run automation, call paid APIs, or publish.",
        "",
        "## Summary",
        "",
        f"- log rows: {len(rows)}",
        f"- operator input required: {sum(1 for row in rows if row['verification_log_status'] == 'operator_input_required')}",
        "",
        "## Fill-In Fields",
        "",
        "- `url_checked`: paste the exact public URL opened.",
        "- `checked_at_local`: record the local date/time you checked it.",
        "- `freshness_result`: use `current`, `stale`, `unclear`, or `not_accessible`.",
        "- `duplicate_decision`: use `not_duplicate`, `same_domain_ok`, `duplicate_hold`, or `needs_review`.",
        "- `approval_outcome`: use `approved_for_manual_registry_edit`, `hold`, `discard`, or `needs_more_review`.",
        "- `registry_edit_decision`: use `no_edit_yet`, `manual_edit_planned`, or `manual_edit_completed_by_operator`.",
        "",
        "## Guardrails",
        "",
        "- Do not mark a row approved until the URL is free, public, current, and login-free.",
        "- Rows with diff-review HOLD should remain held until the blocking issue is resolved.",
        "- This log is evidence for a human decision; it is not imported into the trusted registry.",
        "- Keep paid APIs, private pages, auto-runs, and publishing out of this workflow.",
        "",
        "## Log Rows",
        "",
    ]
    if not rows:
        lines.append("No verification log rows were generated. Work the diff review first.")
    else:
        for row in rows:
            lines.append(
                f"- **{row['verification_log_status']}** | {row['source_id']} | "
                f"diff: {row['diff_review_status']} | flags: {row['diff_flags']} | "
                f"record URL/freshness/duplicate/approval outcome in the CSV."
            )
    lines += ["", "Use `source_registry_verification_log.csv` as the manual fill-in log.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def proposal_issue_flags(row: Dict[str, str], registry_indexes: Dict[str, set[str]], seen: set[str]) -> Dict[str, List[str]]:
    issues: List[str] = []
    flags: List[str] = []
    sid = lower(row.get("candidate_source_id"))
    url = clean(row.get("candidate_url"))
    normalized_url = url.lower().rstrip("/")
    domain = lower(row.get("candidate_domain")).removeprefix("www.") or domain_from_url(url)
    source_type = lower(row.get("source_type"))
    tier = lower(row.get("tier"))
    trust = lower(row.get("trust_band"))
    enabled = lower(row.get("proposed_enabled"))
    action = lower(row.get("registry_action"))
    text = " ".join(
        [
            lower(row.get("candidate_source_name")),
            lower(row.get("candidate_url")),
            lower(row.get("candidate_domain")),
            lower(row.get("publish_policy")),
            lower(row.get("allowed_use")),
            lower(row.get("review_notes")),
        ]
    )

    if not sid:
        issues.append("missing candidate_source_id")
        flags.append("incomplete")
    elif sid in registry_indexes["source_ids"]:
        issues.append("duplicate source_id already exists in trusted registry")
        flags.append("duplicate")
    elif sid in seen:
        issues.append("duplicate source_id inside proposal inbox")
        flags.append("duplicate")
    seen.add(sid)

    if not url:
        issues.append("missing candidate_url")
        flags.append("incomplete")
    elif not url_ok(url):
        issues.append("unsafe or invalid URL; only http/https public sources are allowed")
        flags.append("unsafe_url")
    elif normalized_url in registry_indexes["urls"]:
        issues.append("duplicate URL already exists in trusted registry")
        flags.append("duplicate")

    if domain and domain in registry_indexes["domains"]:
        issues.append("candidate domain already exists in trusted registry; confirm this is not duplicate coverage")
        flags.append("duplicate_domain")

    social_domains = {
        "instagram.com", "threads.net", "x.com", "twitter.com", "tiktok.com", "facebook.com",
        "reddit.com", "mastodon.social", "bsky.app", "youtube.com", "youtu.be",
    }
    if any(domain == item or domain.endswith(f".{item}") for item in social_domains) or "social" in source_type or tier.startswith("social"):
        issues.append("social-only source cannot be added as official/wire/cross-check registry coverage")
        flags.append("social_only")

    paid_tokens = ["paid api", "paid_api", "api key", "apikey", "subscription", "subscribe", "paywall", "pricing", "premium"]
    paid_domains = ["sportradar.com", "sportsdata.io", "statsperform.com", "rapidapi.com", "serpapi.com"]
    if any(token in text for token in paid_tokens) or any(domain == item or domain.endswith(f".{item}") for item in paid_domains):
        issues.append("paid, paywalled, or API-key source is not allowed for free-first intake")
        flags.append("paid_or_api")

    login_tokens = ["login", "log-in", "signin", "sign-in", "account", "auth", "members-only", "private"]
    if any(token in text for token in login_tokens):
        issues.append("login-only or private/account source is not allowed")
        flags.append("login_only")

    unsafe_domains = ["bet365.com", "draftkings.com", "fanduel.com", "prizepicks.com", "onlyfans.com", "patreon.com"]
    if any(domain == item or domain.endswith(f".{item}") for item in unsafe_domains):
        issues.append("unsafe or off-policy source domain")
        flags.append("unsafe_domain")

    if enabled in {"yes", "true", "1"}:
        issues.append("proposal attempts to enable source; keep proposed_enabled=No until registry review")
        flags.append("auto_enable_attempt")
    if action and action != "proposal_only_do_not_import":
        issues.append("registry_action must stay proposal_only_do_not_import before human registry update")
        flags.append("unsafe_registry_action")
    if "green" not in trust:
        issues.append("trust_band should remain green_candidate_after_operator_review for source proposals")
        flags.append("needs_trust_review")

    return {"issues": issues, "flags": flags}


def build_proposal_review(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    proposal_rows = [row for row in read_run_csv(PROPOSALS) if proposal_has_candidate(row)]
    registry_indexes = existing_registry_indexes(sources)
    seen: set[str] = set()
    review_rows: List[Dict[str, str]] = []
    for row in proposal_rows:
        result = proposal_issue_flags(row, registry_indexes, seen)
        issues = result["issues"]
        flags = sorted(set(result["flags"]))
        blocking = {"duplicate", "social_only", "paid_or_api", "login_only", "unsafe_url", "unsafe_domain", "auto_enable_attempt", "unsafe_registry_action"}
        if any(flag in blocking for flag in flags):
            status = "hold"
            recommendation = "Do not add to trusted source registry until the blocking issue is resolved."
        elif issues:
            status = "review"
            recommendation = "Manually review the proposal before any registry update."
        else:
            status = "ready_for_registry_review"
            recommendation = "Candidate may be considered for a deliberate manual registry update."
        review_rows.append(
            {
                "candidate_source_id": clean(row.get("candidate_source_id")),
                "candidate_source_name": clean(row.get("candidate_source_name")),
                "candidate_url": clean(row.get("candidate_url")),
                "candidate_domain": clean(row.get("candidate_domain")) or domain_from_url(clean(row.get("candidate_url"))),
                "sport_league": clean(row.get("sport_league") or row.get("display_name")),
                "source_type": clean(row.get("source_type")),
                "tier": clean(row.get("tier")),
                "proposed_enabled": clean(row.get("proposed_enabled")) or "No",
                "review_status": status,
                "issue_count": str(len(issues)),
                "issues": "; ".join(issues) if issues else "none",
                "safety_flags": "; ".join(flags) if flags else "none",
                "recommendation": recommendation,
                "registry_action": clean(row.get("registry_action")) or "proposal_only_do_not_import",
            }
        )
    return review_rows


def write_proposal_review_markdown(path: str | Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        "# HSD Source Proposal Review",
        "",
        "Reviews `operator/inbox/source_registry_proposals.csv` before any manual update to `config/source_registry.json`.",
        "The report flags duplicates, paid/API sources, login-only sources, social-only sources, and unsafe proposals.",
        "",
        "## Summary",
        "",
        f"- proposals reviewed: {len(rows)}",
        f"- hold: {sum(1 for row in rows if row['review_status'] == 'hold')}",
        f"- review: {sum(1 for row in rows if row['review_status'] == 'review')}",
        f"- ready for registry review: {sum(1 for row in rows if row['review_status'] == 'ready_for_registry_review')}",
        "",
        "## Proposal rows",
        "",
    ]
    if not rows:
        lines.append("No manual source proposals found. Add rows to `operator/inbox/source_registry_proposals.csv` when ready.")
    else:
        for row in rows:
            lines.append(
                f"- **{row['review_status']}** | {row['candidate_source_id'] or 'missing_id'} | "
                f"{row['candidate_url'] or 'missing_url'} | flags: {row['safety_flags']} | {row['issues']}"
            )
    lines += ["", "No rows are imported automatically. Update the trusted registry only after deliberate human review.", ""]
    write_text(path, "\n".join(lines), encoding="utf-8")


def main() -> None:
    raw = read_json(REGISTRY)
    sources = raw.get("sources", []) if isinstance(raw.get("sources", []), list) else []
    seen: set[str] = set()
    rows = [audit_source(src, seen) for src in sources if isinstance(src, dict)]
    coverage_rows = build_coverage_map(sources)
    intake_rows = build_intake_template(coverage_rows)
    proposal_review_rows = build_proposal_review(sources)
    proposal_pack_rows_by_key = build_source_proposal_packs(sources, coverage_rows)
    proposal_pack_rows = source_proposal_pack_rows(proposal_pack_rows_by_key)
    proposal_pack_readiness_rows = build_source_proposal_pack_readiness(proposal_pack_rows_by_key, coverage_rows)
    proposal_draft_rows = build_source_registry_proposal_draft(proposal_pack_rows_by_key, proposal_pack_readiness_rows)
    proposal_promotion_checklist_rows = build_source_registry_proposal_promotion_checklist(proposal_draft_rows)
    registry_update_worksheet_rows = build_source_registry_update_worksheet(proposal_promotion_checklist_rows)
    registry_diff_review_rows = build_source_registry_diff_review(sources, registry_update_worksheet_rows)
    manual_verification_log_rows = read_run_csv(VERIFICATION_LOG_INPUT)
    source_verification_log_rows = build_source_registry_verification_log(registry_diff_review_rows, manual_verification_log_rows)
    registry_approval_packet_rows = build_source_registry_approval_packet(source_verification_log_rows, registry_update_worksheet_rows)
    registry_patch_preview_rows = build_source_registry_patch_preview(registry_approval_packet_rows, sources)
    wnba_proposal_pack_rows = proposal_pack_rows_by_key.get("wnba", [])
    nwsl_proposal_pack_rows = proposal_pack_rows_by_key.get("nwsl", [])
    lpga_proposal_pack_rows = proposal_pack_rows_by_key.get("lpga", [])
    pwhl_proposal_pack_rows = proposal_pack_rows_by_key.get("pwhl", [])
    write_csv(OUT_CSV, rows)
    write_coverage_csv(OUT_COVERAGE_CSV, coverage_rows)
    write_intake_csv(OUT_INTAKE_CSV, intake_rows)
    write_intake_markdown(OUT_INTAKE_MD, intake_rows)
    write_proposal_review_csv(OUT_PROPOSAL_CSV, proposal_review_rows)
    write_proposal_review_markdown(OUT_PROPOSAL_MD, proposal_review_rows)
    write_source_registry_proposal_draft_csv(OUT_PROPOSAL_DRAFT_CSV, proposal_draft_rows)
    write_source_registry_proposal_draft_markdown(OUT_PROPOSAL_DRAFT_MD, proposal_draft_rows)
    write_source_registry_proposal_promotion_checklist_csv(OUT_PROPOSAL_PROMOTION_CHECKLIST_CSV, proposal_promotion_checklist_rows)
    write_source_registry_proposal_promotion_checklist_markdown(OUT_PROPOSAL_PROMOTION_CHECKLIST_MD, proposal_promotion_checklist_rows)
    write_source_registry_update_worksheet_csv(OUT_REGISTRY_UPDATE_WORKSHEET_CSV, registry_update_worksheet_rows)
    write_source_registry_update_worksheet_markdown(OUT_REGISTRY_UPDATE_WORKSHEET_MD, registry_update_worksheet_rows)
    write_source_registry_diff_review_csv(OUT_REGISTRY_DIFF_REVIEW_CSV, registry_diff_review_rows)
    write_source_registry_diff_review_markdown(OUT_REGISTRY_DIFF_REVIEW_MD, registry_diff_review_rows)
    write_source_registry_verification_log_csv(OUT_SOURCE_VERIFICATION_LOG_CSV, source_verification_log_rows)
    write_source_registry_verification_log_markdown(OUT_SOURCE_VERIFICATION_LOG_MD, source_verification_log_rows)
    write_source_registry_approval_packet_csv(OUT_REGISTRY_APPROVAL_PACKET_CSV, registry_approval_packet_rows)
    write_source_registry_approval_packet_markdown(OUT_REGISTRY_APPROVAL_PACKET_MD, registry_approval_packet_rows)
    write_source_registry_patch_preview_csv(OUT_REGISTRY_PATCH_PREVIEW_CSV, registry_patch_preview_rows)
    write_source_registry_patch_preview_markdown(OUT_REGISTRY_PATCH_PREVIEW_MD, registry_patch_preview_rows)
    write_source_proposal_pack_readiness_csv(OUT_PROPOSAL_PACK_READINESS_CSV, proposal_pack_readiness_rows)
    write_source_proposal_pack_readiness_markdown(OUT_PROPOSAL_PACK_READINESS_MD, proposal_pack_readiness_rows)
    write_source_proposal_pack_csv(OUT_PROPOSAL_PACKS_CSV, proposal_pack_rows)
    write_source_proposal_packs_markdown(OUT_PROPOSAL_PACKS_MD, proposal_pack_rows_by_key, coverage_rows)
    for pack in SOURCE_PROPOSAL_PACKS:
        pack_key = clean(pack.get("pack_key"))
        pack_rows = proposal_pack_rows_by_key.get(pack_key, [])
        if pack.get("output_csv"):
            write_source_proposal_pack_csv(pack["output_csv"], pack_rows)
        if pack.get("output_md"):
            write_source_proposal_pack_markdown(pack["output_md"], pack_rows, coverage_rows, pack)

    counts = {
        "sources": len(rows),
        "green": sum(1 for r in rows if r["trust_band"] == "green"),
        "yellow": sum(1 for r in rows if r["trust_band"] == "yellow"),
        "red": sum(1 for r in rows if r["trust_band"] == "red"),
        "pass": sum(1 for r in rows if r["status"] == "PASS"),
        "review": sum(1 for r in rows if r["status"] == "REVIEW"),
        "fail": sum(1 for r in rows if r["status"] == "FAIL"),
        "coverage_total": len(coverage_rows),
        "coverage_gap": sum(1 for r in coverage_rows if r["coverage_status"] == "gap"),
        "coverage_watch": sum(1 for r in coverage_rows if r["coverage_status"] == "watch"),
        "coverage_covered": sum(1 for r in coverage_rows if r["coverage_status"] == "covered"),
        "intake_template_rows": len(intake_rows),
        "proposal_review_rows": len(proposal_review_rows),
        "proposal_hold": sum(1 for r in proposal_review_rows if r["review_status"] == "hold"),
        "proposal_review": sum(1 for r in proposal_review_rows if r["review_status"] == "review"),
        "proposal_ready": sum(1 for r in proposal_review_rows if r["review_status"] == "ready_for_registry_review"),
        "proposal_pack_ready": sum(1 for r in proposal_pack_readiness_rows if r["readiness_status"] == "ready_for_registry_proposal"),
        "proposal_pack_duplicate_review": sum(1 for r in proposal_pack_readiness_rows if r["readiness_status"] == "needs_duplicate_review"),
        "proposal_pack_freshness_check": sum(1 for r in proposal_pack_readiness_rows if r["readiness_status"] == "needs_source_freshness_check"),
        "proposal_draft_rows": len(proposal_draft_rows),
        "proposal_draft_ready_to_copy": sum(1 for r in proposal_draft_rows if r["draft_selection_status"] == "ready_to_copy_after_freshness_check"),
        "proposal_draft_blocked": sum(1 for r in proposal_draft_rows if r["draft_selection_status"].startswith("blocked_")),
        "proposal_promotion_checklist_rows": len(proposal_promotion_checklist_rows),
        "proposal_promotion_verify_then_copy": sum(1 for r in proposal_promotion_checklist_rows if r["checklist_decision"] == "verify_then_copy"),
        "proposal_promotion_hold": sum(1 for r in proposal_promotion_checklist_rows if r["checklist_decision"] == "hold"),
        "proposal_promotion_discard": sum(1 for r in proposal_promotion_checklist_rows if r["checklist_decision"] == "discard"),
        "registry_update_worksheet_rows": len(registry_update_worksheet_rows),
        "registry_update_worksheet_disabled": sum(1 for r in registry_update_worksheet_rows if r["proposed_enabled"] == "False"),
        "registry_diff_review_rows": len(registry_diff_review_rows),
        "registry_diff_review_pass": sum(1 for r in registry_diff_review_rows if r["diff_review_status"] == "PASS"),
        "registry_diff_review_review": sum(1 for r in registry_diff_review_rows if r["diff_review_status"] == "REVIEW"),
        "registry_diff_review_hold": sum(1 for r in registry_diff_review_rows if r["diff_review_status"] == "HOLD"),
        "source_verification_log_rows": len(source_verification_log_rows),
        "source_verification_log_input_required": sum(1 for r in source_verification_log_rows if r["verification_log_status"] == "operator_input_required"),
        "source_verification_log_recorded": sum(1 for r in source_verification_log_rows if r["verification_log_status"] == "operator_review_recorded"),
        "registry_approval_packet_rows": len(registry_approval_packet_rows),
        "registry_approval_packet_ready": sum(1 for r in registry_approval_packet_rows if r["approval_packet_status"] == "ready_for_final_manual_review"),
        "registry_approval_packet_hold": sum(1 for r in registry_approval_packet_rows if r["approval_packet_status"] == "hold_before_manual_registry_edit"),
        "registry_patch_preview_rows": len(registry_patch_preview_rows),
        "registry_patch_preview_ready": sum(1 for r in registry_patch_preview_rows if r["patch_preview_status"] == "ready_for_manual_copy_paste"),
        "registry_patch_preview_hold": sum(1 for r in registry_patch_preview_rows if r["patch_preview_status"] == "hold_before_manual_patch"),
        "proposal_pack_leagues": len(proposal_pack_rows_by_key),
        "proposal_pack_rows": len(proposal_pack_rows),
        "proposal_pack_official": sum(1 for r in proposal_pack_rows if proposal_pack_group_is_official(r)),
        "proposal_pack_cross_check": sum(1 for r in proposal_pack_rows if "cross_check" in r["candidate_group"]),
        "wnba_proposal_pack_rows": len(wnba_proposal_pack_rows),
        "nwsl_proposal_pack_rows": len(nwsl_proposal_pack_rows),
        "lpga_proposal_pack_rows": len(lpga_proposal_pack_rows),
        "pwhl_proposal_pack_rows": len(pwhl_proposal_pack_rows),
        "pwhl_proposal_pack_official": sum(1 for r in pwhl_proposal_pack_rows if proposal_pack_group_is_official(r)),
        "pwhl_proposal_pack_cross_check": sum(1 for r in pwhl_proposal_pack_rows if "cross_check" in r["candidate_group"]),
    }
    run_dir = run_output_dir()
    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_scope": "run_scoped" if run_dir else "legacy_root",
        "output_dir": run_dir.as_posix() if run_dir else ".",
        "counts": counts,
        "registry_version": raw.get("registry_version", ""),
        "coverage_map": coverage_rows,
        "source_registry_intake_template": intake_rows,
        "source_registry_proposal_review": proposal_review_rows,
        "source_registry_proposal_draft": proposal_draft_rows,
        "source_registry_proposal_promotion_checklist": proposal_promotion_checklist_rows,
        "source_registry_update_worksheet": registry_update_worksheet_rows,
        "source_registry_diff_review": registry_diff_review_rows,
        "source_registry_verification_log": source_verification_log_rows,
        "source_registry_approval_packet": registry_approval_packet_rows,
        "source_registry_patch_preview": registry_patch_preview_rows,
        "source_proposal_pack_readiness": proposal_pack_readiness_rows,
        "source_proposal_packs": proposal_pack_rows,
        "source_proposal_pack_index": [
            {
                "pack_key": clean(pack.get("pack_key")),
                "pack_name": clean(pack.get("pack_name")),
                "rows": len(proposal_pack_rows_by_key.get(clean(pack.get("pack_key")), [])),
                "output_csv": clean(pack.get("output_csv")),
                "output_md": clean(pack.get("output_md")),
            }
            for pack in SOURCE_PROPOSAL_PACKS
        ],
        "wnba_source_proposal_pack": wnba_proposal_pack_rows,
        "nwsl_source_proposal_pack": nwsl_proposal_pack_rows,
        "lpga_source_proposal_pack": lpga_proposal_pack_rows,
        "pwhl_source_proposal_pack": pwhl_proposal_pack_rows,
    }
    write_json(OUT_JSON, manifest, indent=2)

    lines = [
        "# HSD Source Registry Audit",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Version: {VERSION}",
        f"Registry version: {raw.get('registry_version', '')}",
        "",
        f"- total sources: {counts['sources']}",
        f"- green: {counts['green']}",
        f"- yellow: {counts['yellow']}",
        f"- red: {counts['red']}",
        f"- pass: {counts['pass']}",
        f"- review: {counts['review']}",
        f"- fail: {counts['fail']}",
        f"- coverage gaps: {counts['coverage_gap']}",
        f"- coverage watch: {counts['coverage_watch']}",
        f"- coverage covered: {counts['coverage_covered']}",
        f"- source intake template rows: {counts['intake_template_rows']}",
        f"- source proposals reviewed: {counts['proposal_review_rows']}",
        f"- source proposals on hold: {counts['proposal_hold']}",
        f"- source packs ready for proposal review: {counts['proposal_pack_ready']}",
        f"- source packs needing duplicate review: {counts['proposal_pack_duplicate_review']}",
        f"- source packs needing freshness/source checks: {counts['proposal_pack_freshness_check']}",
        f"- source proposal draft rows: {counts['proposal_draft_rows']}",
        f"- source proposal draft ready-to-copy rows: {counts['proposal_draft_ready_to_copy']}",
        f"- source proposal draft blocked rows: {counts['proposal_draft_blocked']}",
        f"- source proposal checklist verify/copy rows: {counts['proposal_promotion_verify_then_copy']}",
        f"- source proposal checklist hold rows: {counts['proposal_promotion_hold']}",
        f"- source proposal checklist discard rows: {counts['proposal_promotion_discard']}",
        f"- source registry update worksheet rows: {counts['registry_update_worksheet_rows']}",
        f"- source registry diff review hold rows: {counts['registry_diff_review_hold']}",
        f"- source verification log rows: {counts['source_verification_log_rows']}",
        f"- source approval packet rows: {counts['registry_approval_packet_rows']}",
        f"- source registry patch preview rows: {counts['registry_patch_preview_rows']}",
        f"- guided proposal pack leagues: {counts['proposal_pack_leagues']}",
        f"- guided proposal pack rows: {counts['proposal_pack_rows']}",
        f"- PWHL proposal pack rows: {counts['pwhl_proposal_pack_rows']}",
        "",
        "## Green source decision",
        "",
    ]
    for item in raw.get("green_approved_decision", []):
        lines.append(f"- {item}")
    lines += ["", "## Source rows needing attention", ""]
    attention = [r for r in rows if r["status"] != "PASS"]
    if attention:
        for r in attention:
            lines.append(f"- **{r['status']}** | {r['source_id']} | {r['issues']}")
    else:
        lines.append("No source registry issues detected.")
    lines += ["", "## Coverage map", ""]
    for row in coverage_rows:
        lines.append(
            f"- **{row['coverage_status'].upper()}** | {row['display_name']} | "
            f"{row['coverage_gap']} | {row['operator_next_step']}"
        )
    lines += ["", "## Manual source intake template", ""]
    if intake_rows:
        lines.append("Proposal rows were created in `source_registry_intake_template.csv`.")
        for row in intake_rows:
            lines.append(
                f"- {row['display_name']} | {row['needed_source_type']} | {row['coverage_gap']} | "
                f"{row['registry_action']}"
            )
    else:
        lines.append("No source intake proposal rows were needed.")
    lines += ["", "## Manual source proposal review", ""]
    if proposal_review_rows:
        lines.append("Manual proposal rows were reviewed in `source_registry_proposal_review.csv`.")
        for row in proposal_review_rows:
            lines.append(
                f"- **{row['review_status']}** | {row['candidate_source_id'] or 'missing_id'} | "
                f"{row['safety_flags']} | {row['issues']}"
            )
    else:
        lines.append("No manual source proposals found in `operator/inbox/source_registry_proposals.csv`.")
    lines += ["", "## Guided source proposal packs", ""]
    lines.append("Guided free-source proposal candidates were created in `source_proposal_packs.csv` and `.md`.")
    lines.append("Pack-level readiness cues were created in `source_proposal_pack_readiness.csv` and `.md`.")
    lines.append("A manual proposal draft was created in `source_registry_proposal_draft.csv` and `.md`.")
    lines.append("A promotion checklist was created in `source_registry_proposal_promotion_checklist.csv` and `.md`.")
    lines.append("A review-only registry update worksheet was created in `source_registry_update_worksheet.csv` and `.md`.")
    lines.append("A read-only registry diff review was created in `source_registry_diff_review.csv` and `.md`.")
    lines.append("A manual source verification log was created in `source_registry_verification_log.csv` and `.md`.")
    lines.append("A manual registry approval packet was created in `source_registry_approval_packet.csv` and `.md`.")
    lines.append("A manual registry patch preview was created in `source_registry_patch_preview.csv` and `.md`.")
    lines.append("")
    if registry_patch_preview_rows:
        lines.append("### Manual registry patch preview")
        lines.append("")
        for row in registry_patch_preview_rows[:8]:
            lines.append(
                f"- **{row['patch_preview_status']}** | {row['source_id']} | "
                f"target: {row['manual_edit_target']} | hold: {row['hold_reason']}"
            )
        if len(registry_patch_preview_rows) > 8:
            lines.append(f"- ... {len(registry_patch_preview_rows) - 8} more patch preview rows in the CSV.")
        lines.append("")
    if registry_approval_packet_rows:
        lines.append("### Manual registry approval packet")
        lines.append("")
        for row in registry_approval_packet_rows[:8]:
            lines.append(
                f"- **{row['approval_packet_status']}** | {row['source_id']} | "
                f"evidence: {row['evidence_url'] or 'missing'} | hold: {row['hold_reason']}"
            )
        if len(registry_approval_packet_rows) > 8:
            lines.append(f"- ... {len(registry_approval_packet_rows) - 8} more approval packet rows in the CSV.")
        lines.append("")
    if source_verification_log_rows:
        lines.append("### Manual source verification log")
        lines.append("")
        for row in source_verification_log_rows[:8]:
            lines.append(
                f"- **{row['verification_log_status']}** | {row['source_id']} | "
                f"diff: {row['diff_review_status']} | record URL/freshness/duplicate/approval outcome"
            )
        if len(source_verification_log_rows) > 8:
            lines.append(f"- ... {len(source_verification_log_rows) - 8} more verification log rows in the CSV.")
        lines.append("")
    if registry_diff_review_rows:
        lines.append("### Manual registry diff review")
        lines.append("")
        for row in registry_diff_review_rows[:8]:
            lines.append(
                f"- **{row['diff_review_status']}** | {row['source_id']} | "
                f"flags: {row['flags']} | {row['recommendation']}"
            )
        if len(registry_diff_review_rows) > 8:
            lines.append(f"- ... {len(registry_diff_review_rows) - 8} more diff review rows in the CSV.")
        lines.append("")
    if registry_update_worksheet_rows:
        lines.append("### Manual registry update worksheet")
        lines.append("")
        for row in registry_update_worksheet_rows[:8]:
            lines.append(
                f"- **{row['worksheet_decision']}** | {row['source_id']} | "
                f"target: {row['manual_edit_target']} | enabled: {row['proposed_enabled']} | auto: {row['auto_edit_status']}"
            )
        if len(registry_update_worksheet_rows) > 8:
            lines.append(f"- ... {len(registry_update_worksheet_rows) - 8} more worksheet rows in the CSV.")
        lines.append("")
    if proposal_promotion_checklist_rows:
        lines.append("### Manual proposal promotion checklist")
        lines.append("")
        for row in proposal_promotion_checklist_rows[:8]:
            lines.append(
                f"- **{row['checklist_decision']}** | {row['candidate_source_id']} | "
                f"{row['operator_step']} | copy: {row['copy_allowed']}"
            )
        if len(proposal_promotion_checklist_rows) > 8:
            lines.append(f"- ... {len(proposal_promotion_checklist_rows) - 8} more checklist rows in the CSV.")
        lines.append("")
    if proposal_draft_rows:
        lines.append("### Manual proposal draft")
        lines.append("")
        for row in proposal_draft_rows[:8]:
            lines.append(
                f"- **{row['draft_selection_status']}** | {row['pack_name']} | "
                f"{row['candidate_source_id']} | {row['draft_action']} | {row['readiness_warning']}"
            )
        if len(proposal_draft_rows) > 8:
            lines.append(f"- ... {len(proposal_draft_rows) - 8} more draft rows in the CSV.")
        lines.append("")
    for row in proposal_pack_readiness_rows:
        lines.append(
            f"- **{row['pack_name'] or row['display_name']}** | {row['readiness_status']} | "
            f"{row['candidate_rows']} candidates | duplicates: {row['duplicate_candidates']} | "
            f"freshness checks: {row['freshness_check_candidates']} | {row['next_step']}"
        )
    lines.append("")
    for pack in SOURCE_PROPOSAL_PACKS:
        pack_key = clean(pack.get("pack_key"))
        pack_rows = proposal_pack_rows_by_key.get(pack_key, [])
        lines.append(
            f"- {clean(pack.get('pack_name'))} | rows: {len(pack_rows)} | "
            f"data: `{clean(pack.get('output_csv'))}` | report: `{clean(pack.get('output_md'))}`"
        )
        for row in pack_rows[:5]:
            lines.append(
                f"  - {row['suggested_priority']} | {row['candidate_group']} | {row['candidate_source_id']} | "
                f"{row['registry_action']} | enabled: {row['proposed_enabled']}"
            )
        if len(pack_rows) > 5:
            lines.append(f"  - ... {len(pack_rows) - 5} more candidates in the CSV.")
    lines += ["", "## Full registry audit", "", "See `source_registry_audit.csv` for every source.", ""]
    write_text(OUT_MD, "\n".join(lines), encoding="utf-8")
    print(json.dumps({"output_scope": manifest["output_scope"], **counts}, indent=2))


if __name__ == "__main__":
    main()
