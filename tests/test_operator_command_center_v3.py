from __future__ import annotations

import csv
import json
from pathlib import Path

import generate_hsd_operator_command_center_v2 as command_center

REPO = Path(__file__).resolve().parents[1]


def write_json(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload), encoding="utf-8")


def write_csv(path: str, rows: list[dict[str, str]]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def seed_daily_ops_files() -> None:
    write_json(
        "operator_status.json",
        {
            "overall": "NO-GO",
            "issues": [{"severity": "critical", "code": "no_content_ready", "detail": "No ready pack."}],
        },
    )
    write_json(
        "publish_guard_report.json",
        {
            "publish_mode": "artifact_only",
            "publish_allowed": False,
            "graphics_handoff_allowed": False,
            "preview_gate_status": "PASS",
            "rendered_qa_status": "not_run",
            "issues": [{"severity": "critical", "code": "no_content_ready", "detail": "No ready pack."}],
        },
    )
    write_json(
        "results_desk_v5_manifest.json",
        {
            "counts": {"women_events": 8, "graphics_ready": 1},
            "source_health": [
                {
                    "source_name": "espn_wnba_public",
                    "sport_or_league": "WNBA",
                    "date": "20260624",
                    "ok": "Yes",
                    "events_found": 4,
                    "notes": "free public source ok",
                }
            ],
        },
    )
    write_csv(
        "news_fact_packets.csv",
        [
            {
                "urgency": "P1",
                "headline": "New York Liberty beat Las Vegas Aces",
                "production_ready": "Yes",
                "caption_hard_fact": "Verified final: New York Liberty 87, Las Vegas Aces 76.",
                "source_count": "4",
                "source_confidence_score": "92",
                "source_confidence_tier": "publish_grade",
                "source_publish_grade": "publish_grade",
                "source_confidence_reason": "Results Desk final score; multiple usable free sources",
            }
        ],
    )
    write_csv(
        "studio_bundle_queue.csv",
        [
            {
                "production_priority": "POST FIRST",
                "bundle_name": "Tonight in the W",
                "bundle_type": "wnba_preview_premium",
                "asset_shape": "1080x1350",
                "freshness_decision": "allow",
                "source_headlines": "Phoenix Mercury at Indiana Fever",
            }
        ],
    )
    Path("bebe_posting_schedule_today.md").write_text(
        "\n".join(
            [
                "## Posting schedule",
                "",
                "| Time ET | Platform | Slot | Status | Recommended action | Artifact |",
                "|---|---|---|---|---|---|",
                "| 12:00 | IG Feed | Main post 1 | needs_assets | Build the post manually. | studio_bundle_queue.csv |",
            ]
        ),
        encoding="utf-8",
    )
    Path("operator_status.md").write_text("# Operator status\n", encoding="utf-8")
    Path("publish_guard_report.md").write_text("# Publish guard\n", encoding="utf-8")
    write_json(
        "source_registry_audit.json",
        {
            "counts": {"sources": 3, "pass": 2, "review": 1, "fail": 0},
            "output_scope": "run_scoped",
            "coverage_map": [
                {
                    "coverage_key": "wnba",
                    "display_name": "WNBA",
                    "official_sources": "wnba_official_news",
                    "team_sources": "wnba_team_official_pages",
                    "wire_sources": "ap_womens_sports_wire",
                    "cross_check_sources": "espn_wnba_scoreboard_cross_check",
                    "coverage_status": "covered",
                    "coverage_gap": "none",
                    "operator_next_step": "Coverage is strong enough for normal manual review; keep monitoring existing free sources.",
                },
                {
                    "coverage_key": "pwhl",
                    "display_name": "PWHL",
                    "official_sources": "",
                    "team_sources": "",
                    "wire_sources": "ap_womens_sports_wire; reuters_sports_wire",
                    "cross_check_sources": "",
                    "coverage_status": "gap",
                    "coverage_gap": "missing official league/team source; missing scoreboard/stat/cross-check source",
                    "operator_next_step": "Add or monitor free PWHL league/team official pages before relying on wire-only hockey leads.",
                },
            ],
        },
    )
    Path("source_registry_intake_template.md").write_text(
        "# Source registry intake template\n\nRows are proposal-only and disabled by default.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_intake_template.csv",
        [
            {
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "",
                "candidate_source_name": "",
                "candidate_url": "",
                "candidate_domain": "",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news; team_news; source_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Fill candidate fields only after checking the free public source manually.",
            }
        ],
    )
    Path("source_registry_proposal_review.md").write_text(
        "# Source proposal review\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_proposal_review.csv",
        [
            {
                "candidate_source_id": "pwhl_instagram",
                "candidate_source_name": "PWHL Instagram",
                "candidate_url": "https://www.instagram.com/thepwhlofficial/",
                "candidate_domain": "instagram.com",
                "sport_league": "PWHL",
                "source_type": "official_site",
                "tier": "official",
                "proposed_enabled": "No",
                "review_status": "hold",
                "issue_count": "1",
                "issues": "social-only source cannot be added as official/wire/cross-check registry coverage",
                "safety_flags": "social_only",
                "recommendation": "Do not add to trusted source registry until the blocking issue is resolved.",
                "registry_action": "proposal_only_do_not_import",
            },
            {
                "candidate_source_id": "pwhl_official_site",
                "candidate_source_name": "PWHL official site",
                "candidate_url": "https://www.thepwhl.com/en/",
                "candidate_domain": "thepwhl.com",
                "sport_league": "PWHL",
                "source_type": "official_site",
                "tier": "official",
                "proposed_enabled": "No",
                "review_status": "ready_for_registry_review",
                "issue_count": "0",
                "issues": "none",
                "safety_flags": "none",
                "recommendation": "Candidate may be considered for a deliberate manual registry update.",
                "registry_action": "proposal_only_do_not_import",
            },
        ],
    )
    Path("pwhl_source_proposal_pack.md").write_text(
        "# PWHL Source Proposal Pack\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    write_csv(
        "pwhl_source_proposal_pack.csv",
        [
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_group": "league_official",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "pwhl_official_news",
                "candidate_source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news; source_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official league news page.",
                "registry_presence": "not_in_registry",
                "manual_review_note": "Open and verify manually before copying into proposals.",
            },
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_group": "team_official",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "team_or_club",
                "coverage_gap": "missing team/club source",
                "candidate_source_id": "pwhl_boston_fleet_team",
                "candidate_source_name": "Boston Fleet official team page",
                "candidate_url": "https://www.thepwhl.com/en/teams/boston-fleet",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site_collection",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "team_news; roster_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official team page.",
                "registry_presence": "not_in_registry",
                "manual_review_note": "Open and verify manually before copying into proposals.",
            },
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_group": "league_cross_check",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "scoreboard_or_stats_cross_check",
                "coverage_gap": "missing scoreboard/stat/cross-check source",
                "candidate_source_id": "pwhl_official_scores",
                "candidate_source_name": "PWHL official scores",
                "candidate_url": "https://www.thepwhl.com/en/scores",
                "candidate_domain": "thepwhl.com",
                "source_type": "scoreboard_site",
                "tier": "stats_provider",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "cross_check; scores; schedules",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official scores page.",
                "registry_presence": "not_in_registry",
                "manual_review_note": "Open and verify manually before copying into proposals.",
            },
        ],
    )
    Path("source_proposal_packs.md").write_text(
        "# HSD Guided Source Proposal Packs\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    Path("source_proposal_pack_readiness.md").write_text(
        "# HSD Guided Source Proposal Pack Readiness\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_proposal_pack_readiness.csv",
        [
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "display_name": "PWHL",
                "readiness_status": "ready_for_registry_proposal",
                "readiness_label": "Ready for proposal review",
                "candidate_rows": "3",
                "official_candidates": "2",
                "cross_check_candidates": "1",
                "duplicate_candidates": "0",
                "freshness_check_candidates": "3",
                "ready_candidates": "3",
                "coverage_status": "gap",
                "coverage_gap": "missing official league/team source",
                "review_cues": "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected.",
                "next_step": "Open top candidates manually for freshness, then copy selected rows into operator/inbox/source_registry_proposals.csv for deliberate review.",
                "top_candidate_ids": "pwhl_official_news; pwhl_boston_fleet_team; pwhl_official_scores",
                "duplicate_candidate_ids": "",
                "output_csv": "pwhl_source_proposal_pack.csv",
                "output_md": "pwhl_source_proposal_pack.md",
            },
            {
                "pack_key": "wnba",
                "pack_name": "WNBA Source Proposal Pack",
                "display_name": "WNBA",
                "readiness_status": "needs_duplicate_review",
                "readiness_label": "Duplicate review",
                "candidate_rows": "13",
                "official_candidates": "8",
                "cross_check_candidates": "5",
                "duplicate_candidates": "1",
                "freshness_check_candidates": "12",
                "ready_candidates": "12",
                "coverage_status": "watch",
                "coverage_gap": "review official league/team source depth",
                "review_cues": "1 candidate already resembles trusted registry coverage.",
                "next_step": "Review duplicate source IDs, URLs, or domains before copying any pack rows into manual proposals.",
                "top_candidate_ids": "wnba_official_home_review; wnba_official_news_review",
                "duplicate_candidate_ids": "espn_wnba_scoreboard_pack_review",
                "output_csv": "wnba_source_proposal_pack.csv",
                "output_md": "wnba_source_proposal_pack.md",
            },
            {
                "pack_key": "lpga",
                "pack_name": "LPGA Source Proposal Pack",
                "display_name": "LPGA / golf",
                "readiness_status": "needs_source_freshness_check",
                "readiness_label": "Freshness/source check",
                "candidate_rows": "10",
                "official_candidates": "6",
                "cross_check_candidates": "0",
                "duplicate_candidates": "0",
                "freshness_check_candidates": "10",
                "ready_candidates": "10",
                "coverage_status": "watch",
                "coverage_gap": "review leaderboard/stat/cross-check source depth",
                "review_cues": "missing cross-check candidate",
                "next_step": "Open candidate pages manually, confirm they are current free public sources, and add missing official or cross-check coverage before proposal.",
                "top_candidate_ids": "lpga_official_home_review; lpga_official_tournaments_review",
                "duplicate_candidate_ids": "",
                "output_csv": "lpga_source_proposal_pack.csv",
                "output_md": "lpga_source_proposal_pack.md",
            },
        ],
    )
    Path("source_registry_proposal_draft.md").write_text(
        "# HSD Source Registry Proposal Draft\n\nThis file is not the live proposal inbox.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_proposal_draft.csv",
        [
            {
                "draft_selection_status": "ready_to_copy_after_freshness_check",
                "draft_action": "manual_copy_to_inbox_after_freshness_check",
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "pack_readiness_status": "ready_for_registry_proposal",
                "pack_readiness_label": "Ready for proposal review",
                "candidate_group": "league_official",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "pwhl_official_news",
                "candidate_source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news; source_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official league news page.",
                "registry_presence": "not_in_registry",
                "readiness_warning": "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected.",
                "duplicate_warning": "No duplicate candidates detected in this pack.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "manual_review_note": "This is a draft row only.",
            },
            {
                "draft_selection_status": "blocked_duplicate_review",
                "draft_action": "hold_do_not_copy_until_duplicate_review",
                "pack_key": "wnba",
                "pack_name": "WNBA Source Proposal Pack",
                "pack_readiness_status": "needs_duplicate_review",
                "pack_readiness_label": "Duplicate review",
                "candidate_group": "reputable_cross_check",
                "suggested_priority": "P1",
                "coverage_key": "wnba",
                "display_name": "WNBA",
                "needed_source_type": "scoreboard_or_stats_cross_check",
                "coverage_gap": "review scoreboard/stat/cross-check source depth",
                "candidate_source_id": "espn_wnba_scoreboard_pack_review",
                "candidate_source_name": "ESPN WNBA scoreboard",
                "candidate_url": "https://www.espn.com/wnba/scoreboard",
                "candidate_domain": "espn.com",
                "source_type": "scoreboard_site",
                "tier": "primary_media",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "WNBA",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "cross_check; scores",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided WNBA pack candidate.",
                "source_basis": "Free public scoreboard.",
                "registry_presence": "domain_already_exists_check_duplicate",
                "readiness_warning": "1 candidate already resembles trusted registry coverage.",
                "duplicate_warning": "Duplicate review required for pack; duplicate candidate IDs: espn_wnba_scoreboard_pack_review.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "manual_review_note": "This is a draft row only.",
            },
        ],
    )
    Path("source_registry_proposal_promotion_checklist.md").write_text(
        "# HSD Source Registry Proposal Promotion Checklist\n\nManual checklist.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_proposal_promotion_checklist.csv",
        [
            {
                "checklist_decision": "verify_then_copy",
                "operator_step": "1_verify_public_page_then_2_copy_to_manual_inbox",
                "copy_allowed": "Yes_after_manual_freshness_check",
                "copy_target": "operator/inbox/source_registry_proposals.csv",
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_source_id": "pwhl_official_news",
                "candidate_source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "sport_league": "PWHL",
                "allowed_use": "official_news; source_confirmation",
                "registry_presence": "not_in_registry",
                "draft_selection_status": "ready_to_copy_after_freshness_check",
                "draft_action": "manual_copy_to_inbox_after_freshness_check",
                "duplicate_warning": "No duplicate candidates detected in this pack.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "readiness_warning": "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected.",
                "verification_checklist": "open candidate_url manually | keep proposed_enabled=No",
                "copy_instructions": "After opening the URL, copy this row into operator/inbox/source_registry_proposals.csv.",
                "hold_reason": "",
                "discard_reason": "",
                "proposed_enabled": "No",
                "registry_action": "proposal_only_do_not_import",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
            },
            {
                "checklist_decision": "discard",
                "operator_step": "discard_duplicate_candidate_do_not_copy",
                "copy_allowed": "No",
                "copy_target": "",
                "pack_key": "wnba",
                "pack_name": "WNBA Source Proposal Pack",
                "candidate_source_id": "espn_wnba_scoreboard_pack_review",
                "candidate_source_name": "ESPN WNBA scoreboard",
                "candidate_url": "https://www.espn.com/wnba/scoreboard",
                "candidate_domain": "espn.com",
                "source_type": "scoreboard_site",
                "tier": "primary_media",
                "sport_league": "WNBA",
                "allowed_use": "cross_check; scores",
                "registry_presence": "domain_already_exists_check_duplicate",
                "draft_selection_status": "blocked_duplicate_review",
                "draft_action": "hold_do_not_copy_until_duplicate_review",
                "duplicate_warning": "Duplicate review required for pack; duplicate candidate IDs: espn_wnba_scoreboard_pack_review.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "readiness_warning": "1 candidate already resembles trusted registry coverage.",
                "verification_checklist": "open candidate_url manually | keep proposed_enabled=No",
                "copy_instructions": "Do not copy this row into the manual proposal inbox unless the registry duplicate is proven false.",
                "hold_reason": "",
                "discard_reason": "Candidate already resembles trusted registry coverage: domain_already_exists_check_duplicate.",
                "proposed_enabled": "No",
                "registry_action": "proposal_only_do_not_import",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
            },
        ],
    )
    Path("source_registry_update_worksheet.md").write_text(
        "# HSD Source Registry Update Worksheet\n\nReview-only registry change plan.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_update_worksheet.csv",
        [
            {
                "worksheet_decision": "manual_registry_plan_after_verification",
                "operator_step": "1_open_url_2_confirm_free_public_current_3_compare_json_4_edit_registry_manually_if_approved",
                "manual_edit_target": "config/source_registry.json",
                "manual_edit_allowed": "Yes_only_after_operator_verification",
                "auto_edit_status": "not_performed_by_generator",
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_after_operator_verification",
                "sport_league": "PWHL",
                "allowed_use": "official_news; source_confirmation",
                "registry_presence": "not_in_registry",
                "checklist_decision": "verify_then_copy",
                "checklist_copy_target": "operator/inbox/source_registry_proposals.csv",
                "verification_gate": "Operator must open the public URL first.",
                "current_registry_state": "Before: no approved trusted-registry object should be added.",
                "proposed_enabled": "False",
                "proposed_automation_status": "disabled_manual_review_only",
                "proposed_publish_policy": "not_publish_ready_until_operator_verifies_and_enables",
                "proposed_source_json": "{\"enabled\":false,\"source_id\":\"pwhl_official_news\"}",
                "before_after_diff": "Before: no manual change from this generator. After manual approval only: append disabled source object.",
                "rollback_note": "If verification fails, remove the manually added sources[] object with source_id=pwhl_official_news.",
                "review_notes": "Review-only worksheet row.",
            }
        ],
    )
    Path("source_registry_diff_review.md").write_text(
        "# HSD Source Registry Diff Review\n\nRead-only diff preflight.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_diff_review.csv",
        [
            {
                "diff_review_status": "HOLD",
                "issue_count": "1",
                "issues": "candidate domain already exists in trusted registry: thepwhl.com",
                "flags": "duplicate_domain",
                "operator_step": "review_diff_then_verify_url_before_manual_registry_edit",
                "manual_edit_target": "config/source_registry.json",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "proposed_enabled": "False",
                "proposed_trust_band": "green_after_operator_verification",
                "proposed_automation_status": "disabled_manual_review_only",
                "proposed_publish_policy": "not_publish_ready_until_operator_verifies_and_enables",
                "registry_source_id_match": "No",
                "registry_url_match": "No",
                "registry_domain_match": "thepwhl.com",
                "worksheet_domain_match": "No",
                "rollback_status": "present",
                "proposed_json_status": "valid_json",
                "before_after_status": "present",
                "auto_edit_status": "not_performed_by_generator",
                "recommendation": "Do not manually edit the trusted registry until blocking diff issues are resolved.",
            }
        ],
    )
    Path("source_registry_verification_log.md").write_text(
        "# HSD Source Registry Verification Log\n\nManual fill-in log.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_verification_log.csv",
        [
            {
                "verification_log_status": "operator_input_required",
                "operator_step": "open_url_record_freshness_duplicate_decision_and_approval_outcome",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "diff_review_status": "HOLD",
                "diff_flags": "duplicate_domain",
                "diff_issues": "candidate domain already exists in trusted registry: thepwhl.com",
                "registry_domain_match": "thepwhl.com",
                "worksheet_domain_match": "No",
                "url_checked": "",
                "checked_at_local": "",
                "freshness_result": "",
                "duplicate_decision": "",
                "approval_outcome": "",
                "registry_edit_decision": "",
                "operator_name": "",
                "evidence_url": "",
                "operator_notes": "",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "verification_log_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        ],
    )
    Path("source_proposal_packs.csv").write_text(
        Path("pwhl_source_proposal_pack.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    Path("source_registry_audit.md").write_text("# Source registry audit\n", encoding="utf-8")
    write_csv(
        "morning_source_discovery_board.csv",
        [
            {
                "rank": "1",
                "lane": "social_discovery",
                "review_status": "needs_green_confirmation",
                "source_band": "yellow",
                "publish_posture": "discovery_only",
                "source_name": "team_social_manual_only",
                "source_type": "social_manual_only",
                "sport_league": "all",
                "title": "Public team social lead",
                "summary": "A public team account has a possible lead.",
                "source_url": "https://www.instagram.com/example",
                "evidence_title": "Official metadata title for public team lead",
                "evidence_published_at": "2026-06-10T12:00:00+00:00",
                "evidence_description": "A concise public metadata description for operator review.",
                "evidence_preview": "Official metadata title for public team lead | 2026-06-10 | A concise public metadata description for operator review.",
                "evidence_source": "article_metadata",
                "story_opportunity_id": "opp_fixture_cluster",
                "story_opportunity_title": "Public team social lead",
                "story_opportunity_size": "2",
                "story_opportunity_sources": "wnba_official_news; ap_womens_sports_wire",
                "story_opportunity_urls": "https://www.wnba.com/news/example; https://apnews.com/article/example",
                "story_opportunity_reason": "Grouped 2 related official/wire discovery leads from wnba_official_news, ap_womens_sports_wire.",
                "story_opportunity_angle": "Roster or transaction update",
                "story_opportunity_recommended_path": "news_packet",
                "story_opportunity_path_reason": "Factual roster, transaction, personnel, or league-structure signal belongs in a source-backed News packet.",
                "story_opportunity_confidence_tier": "needs_official_confirmation",
                "story_opportunity_source_coverage": "discovery_source_only",
                "story_opportunity_confirmation_cue": "needs_official_confirmation",
                "story_opportunity_asset_cue": "asset_not_required_for_news_packet",
                "story_opportunity_readiness_note": "Confirm this with an official, wire, primary, or operator-verified source before News or Studio work.",
                "story_opportunity_second_source_id": "wnba_official_news",
                "story_opportunity_second_source_url": "https://www.wnba.com/news",
                "story_opportunity_second_source_lane": "official_free",
                "story_opportunity_second_source_reason": "same league/sport lane; official news/roster confirmation",
                "story_opportunity_second_source_action": "Open wnba_official_news and confirm the same fact before drafting.",
                "source_artifact": "morning_source_discovery_board.csv",
                "next_action": "Use as a lead only; find official, wire, or primary confirmation before publishing.",
                "reason": "requires official confirmation",
                "candidate_id": "",
                "evidence_count": "0",
                "promotion_recommendation": "manual_story_candidate",
                "promotion_priority": "P3",
                "promotion_target": "story_candidates_manual.csv",
                "promotion_reason": "Discovery-only lead needs official confirmation.",
                "promotion_next_step": "Add or verify the lead in the manual story inbox with evidence URLs and locked facts.",
                "quality_score": "40",
                "freshness_label": "recent_30_days",
                "freshness_source": "article_metadata",
            }
        ],
    )
    Path("morning_source_discovery_board.md").write_text("# Morning source discovery\n", encoding="utf-8")
    write_csv(
        "morning_lead_promotion_recommendations.csv",
        [
            {
                "promotion_rank": "1",
                "rank": "1",
                "lane": "social_discovery",
                "review_status": "needs_green_confirmation",
                "source_band": "yellow",
                "publish_posture": "discovery_only",
                "source_name": "team_social_manual_only",
                "source_type": "social_manual_only",
                "sport_league": "all",
                "title": "Public team social lead",
                "summary": "A public team account has a possible lead.",
                "source_url": "https://www.instagram.com/example",
                "evidence_title": "Official metadata title for public team lead",
                "evidence_published_at": "2026-06-10T12:00:00+00:00",
                "evidence_description": "A concise public metadata description for operator review.",
                "evidence_preview": "Official metadata title for public team lead | 2026-06-10 | A concise public metadata description for operator review.",
                "evidence_source": "article_metadata",
                "story_opportunity_id": "opp_fixture_cluster",
                "story_opportunity_title": "Public team social lead",
                "story_opportunity_size": "2",
                "story_opportunity_sources": "wnba_official_news; ap_womens_sports_wire",
                "story_opportunity_urls": "https://www.wnba.com/news/example; https://apnews.com/article/example",
                "story_opportunity_reason": "Grouped 2 related official/wire discovery leads from wnba_official_news, ap_womens_sports_wire.",
                "story_opportunity_angle": "Roster or transaction update",
                "story_opportunity_recommended_path": "news_packet",
                "story_opportunity_path_reason": "Factual roster, transaction, personnel, or league-structure signal belongs in a source-backed News packet.",
                "story_opportunity_confidence_tier": "needs_official_confirmation",
                "story_opportunity_source_coverage": "discovery_source_only",
                "story_opportunity_confirmation_cue": "needs_official_confirmation",
                "story_opportunity_asset_cue": "asset_not_required_for_news_packet",
                "story_opportunity_readiness_note": "Confirm this with an official, wire, primary, or operator-verified source before News or Studio work.",
                "story_opportunity_second_source_id": "wnba_official_news",
                "story_opportunity_second_source_url": "https://www.wnba.com/news",
                "story_opportunity_second_source_lane": "official_free",
                "story_opportunity_second_source_reason": "same league/sport lane; official news/roster confirmation",
                "story_opportunity_second_source_action": "Open wnba_official_news and confirm the same fact before drafting.",
                "source_artifact": "morning_source_discovery_board.csv",
                "next_action": "Use as a lead only; find official, wire, or primary confirmation before publishing.",
                "reason": "requires official confirmation",
                "candidate_id": "",
                "evidence_count": "0",
                "promotion_recommendation": "manual_story_candidate",
                "promotion_priority": "P3",
                "promotion_target": "story_candidates_manual.csv",
                "promotion_reason": "Discovery-only lead needs official confirmation.",
                "promotion_next_step": "Add or verify the lead in the manual story inbox with evidence URLs and locked facts.",
                "quality_score": "40",
                "freshness_label": "recent_30_days",
                "freshness_source": "article_metadata",
            }
        ],
    )
    Path("morning_lead_promotion_recommendations.md").write_text("# Lead promotion recommendations\n", encoding="utf-8")
    Path("studio_bundle_queue.csv").touch()


def test_operator_command_center_builds_daily_ops_view(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()

    payload = command_center.build_payload()
    html = command_center.render_html(payload)
    markdown = command_center.render_markdown(payload)

    assert payload["version"] == "hsd-operator-command-center-v3.21.0-source-verification-log"
    assert payload["decision"]["automation"] == "OFF / artifact-only"
    assert payload["decision"]["free_source_mode"] == "Free public sources only"
    assert "no graphics upload pack is ready" in payload["decision"]["callout"]
    assert payload["briefing"]["best_candidate"] == "New York Liberty beat Las Vegas Aces"
    assert payload["briefing"]["studio_lane"] == "Tonight in the W"
    assert any(action["status"] == "Manual only" for action in payload["next_actions"])
    assert any(action["title"] == "Review source registry audit" for action in payload["next_actions"])
    assert any(action["title"] == "Build graphics pack for Tonight in the W" for action in payload["next_actions"])
    build_action = next(action for action in payload["next_actions"] if action["title"] == "Build graphics pack for Tonight in the W")
    assert build_action["status"] == "Build next"
    assert build_action["command"] == ".\\hsd.cmd run -Mode asset"
    assert any(action["title"] == "Propose free source coverage for PWHL" for action in payload["next_actions"])
    assert any(action["title"] == "Resolve unsafe source proposal: pwhl_instagram" for action in payload["next_actions"])
    assert any(action["title"] == "Promote source lead toward manual_story_candidate: Public team social lead" for action in payload["next_actions"])
    assert all(action["title"] != "no_content_ready" for action in payload["next_actions"])
    assert any(item["label"] == "Source registry" and item["value"] == "REVIEW" for item in payload["metrics"])
    assert any(item["label"] == "Publish-grade packets" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Discovery-only packets" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Morning source rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Story opportunities" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Grouped opportunities" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Publish-grade opportunities" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Needs source check" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Second-source suggestions" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source coverage gaps" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source coverage watch" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Source intake proposals" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source proposal holds" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source proposals ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Proposal draft rows" and item["value"] == "2" for item in payload["metrics"])
    assert any(item["label"] == "Proposal draft ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Proposal draft blocked" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Checklist verify/copy" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Checklist hold" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Checklist discard" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry worksheet rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Worksheet disabled plans" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry diff hold" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry diff review" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Registry diff pass" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Verification log rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Verification input needed" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source packs ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source packs duplicate review" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source packs freshness check" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Guided source pack rows" and item["value"] == "3" for item in payload["metrics"])
    assert any(item["label"] == "PWHL proposal pack" and item["value"] == "3" for item in payload["metrics"])
    assert any(item["label"] == "Studio asset checks" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Gray/social leads" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Lead promotions" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "High-quality leads" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Fresh leads" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "News/Manual/Studio" and item["value"] == "0/1/0" for item in payload["metrics"])
    assert payload["briefing"]["source_state"] == "2 pass, 1 review, 0 fail across 3 sources."
    assert payload["source_coverage_map"][1]["name"] == "PWHL"
    assert payload["source_coverage_map"][1]["status"] == "gap"
    assert "PWHL league/team official pages" in payload["source_coverage_map"][1]["next_step"]
    assert payload["source_registry_intake_template"][0]["display_name"] == "PWHL"
    assert payload["source_registry_intake_template"][0]["proposed_enabled"] == "No"
    assert payload["source_registry_intake_template"][0]["registry_action"] == "proposal_only_do_not_import"
    assert payload["source_registry_proposal_review"][0]["candidate_source_id"] == "pwhl_instagram"
    assert payload["source_registry_proposal_review"][0]["review_status"] == "hold"
    assert payload["source_registry_proposal_review"][1]["review_status"] == "ready_for_registry_review"
    assert payload["source_registry_proposal_draft"][0]["draft_selection_status"] == "ready_to_copy_after_freshness_check"
    assert payload["source_registry_proposal_draft"][0]["draft_action"] == "manual_copy_to_inbox_after_freshness_check"
    assert payload["source_registry_proposal_draft"][0]["proposed_enabled"] == "No"
    assert payload["source_registry_proposal_draft"][1]["draft_selection_status"] == "blocked_duplicate_review"
    assert "Duplicate review required" in payload["source_registry_proposal_draft"][1]["duplicate_warning"]
    assert payload["source_registry_proposal_promotion_checklist"][0]["checklist_decision"] == "verify_then_copy"
    assert payload["source_registry_proposal_promotion_checklist"][0]["copy_allowed"] == "Yes_after_manual_freshness_check"
    assert payload["source_registry_proposal_promotion_checklist"][1]["checklist_decision"] == "discard"
    assert "trusted registry coverage" in payload["source_registry_proposal_promotion_checklist"][1]["discard_reason"]
    assert payload["source_registry_update_worksheet"][0]["worksheet_decision"] == "manual_registry_plan_after_verification"
    assert payload["source_registry_update_worksheet"][0]["manual_edit_target"] == "config/source_registry.json"
    assert payload["source_registry_update_worksheet"][0]["proposed_enabled"] == "False"
    assert payload["source_registry_update_worksheet"][0]["auto_edit_status"] == "not_performed_by_generator"
    assert "remove the manually added" in payload["source_registry_update_worksheet"][0]["rollback_note"]
    assert payload["source_registry_diff_review"][0]["diff_review_status"] == "HOLD"
    assert payload["source_registry_diff_review"][0]["flags"] == "duplicate_domain"
    assert payload["source_registry_diff_review"][0]["registry_domain_match"] == "thepwhl.com"
    assert payload["source_registry_diff_review"][0]["rollback_status"] == "present"
    assert payload["source_registry_verification_log"][0]["verification_log_status"] == "operator_input_required"
    assert payload["source_registry_verification_log"][0]["url_checked"] == ""
    assert payload["source_registry_verification_log"][0]["freshness_result"] == ""
    assert payload["source_registry_verification_log"][0]["duplicate_decision"] == ""
    assert payload["source_registry_verification_log"][0]["approval_outcome"] == ""
    assert payload["source_registry_verification_log"][0]["registry_edit_status"] == "not_edited_by_generator"
    assert payload["source_proposal_pack_readiness"][0]["pack_key"] == "pwhl"
    assert payload["source_proposal_pack_readiness"][0]["readiness_status"] == "ready_for_registry_proposal"
    assert payload["source_proposal_pack_readiness"][1]["readiness_status"] == "needs_duplicate_review"
    assert payload["source_proposal_pack_readiness"][2]["readiness_status"] == "needs_source_freshness_check"
    assert payload["source_proposal_packs"][0]["pack_key"] == "pwhl"
    assert payload["source_proposal_packs"][0]["candidate_source_id"] == "pwhl_official_news"
    assert payload["pwhl_source_proposal_pack"][0]["candidate_source_id"] == "pwhl_official_news"
    assert payload["pwhl_source_proposal_pack"][1]["candidate_source_id"] == "pwhl_boston_fleet_team"
    assert payload["pwhl_source_proposal_pack"][2]["candidate_source_id"] == "pwhl_official_scores"
    pwhl_action = next(action for action in payload["next_actions"] if action["title"] == "Propose free source coverage for PWHL")
    assert pwhl_action["artifact"] == "source_proposal_packs.csv"
    assert "guided PWHL Source Proposal Pack with 3 free official/team/cross-check candidates" in pwhl_action["detail"]
    draft_action = next(action for action in payload["next_actions"] if action["title"] == "Review manual source proposal draft")
    assert draft_action["artifact"] == "source_registry_proposal_draft.md"
    assert "1 draft row(s) are ready to copy" in draft_action["detail"]
    checklist_action = next(action for action in payload["next_actions"] if action["title"] == "Work source proposal promotion checklist")
    assert checklist_action["artifact"] == "source_registry_proposal_promotion_checklist.md"
    assert "1 row(s) are verify-then-copy candidates" in checklist_action["detail"]
    worksheet_action = next(action for action in payload["next_actions"] if action["title"] == "Review trusted-registry update worksheet")
    assert worksheet_action["artifact"] == "source_registry_update_worksheet.md"
    assert "1 review-only registry plan row(s)" in worksheet_action["detail"]
    diff_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve trusted-registry diff review")
    assert diff_action["artifact"] == "source_registry_diff_review.md"
    assert "1 hold row(s)" in diff_action["detail"]
    assert "Do not hand-edit the registry" in diff_action["detail"]
    verification_action = next(action for action in payload["next_actions"] if action["title"] == "Fill manual source verification log")
    assert verification_action["artifact"] == "source_registry_verification_log.md"
    assert "1 source row(s) need operator evidence" in verification_action["detail"]
    assert "URL checked, freshness result, duplicate decision" in verification_action["detail"]
    checklist_hold_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve held or discarded source checklist rows")
    assert checklist_hold_action["artifact"] == "source_registry_proposal_promotion_checklist.md"
    assert "1 discard row(s)" in checklist_hold_action["detail"]
    duplicate_pack_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve duplicate cues in WNBA Source Proposal Pack")
    assert duplicate_pack_action["artifact"] == "source_proposal_pack_readiness.md"
    assert "espn_wnba_scoreboard_pack_review" in duplicate_pack_action["detail"]
    assert payload["source_discovery_board"][0]["title"] == "Public team social lead"
    assert payload["source_discovery_board"][0]["posture"] == "discovery_only"
    assert payload["source_discovery_board"][0]["freshness_source"] == "article_metadata"
    assert "Official metadata title for public team lead" in payload["source_discovery_board"][0]["detail"]
    assert payload["source_discovery_board"][0]["evidence_source"] == "article_metadata"
    assert payload["source_discovery_board"][0]["story_opportunity_size"] == "2"
    assert payload["source_discovery_board"][0]["story_opportunity_angle"] == "Roster or transaction update"
    assert payload["source_discovery_board"][0]["story_opportunity_recommended_path"] == "news_packet"
    assert payload["source_discovery_board"][0]["story_opportunity_confidence_tier"] == "needs_official_confirmation"
    assert payload["source_discovery_board"][0]["story_opportunity_source_coverage"] == "discovery_source_only"
    assert payload["source_discovery_board"][0]["story_opportunity_confirmation_cue"] == "needs_official_confirmation"
    assert payload["source_discovery_board"][0]["story_opportunity_asset_cue"] == "asset_not_required_for_news_packet"
    assert payload["source_discovery_board"][0]["story_opportunity_second_source_id"] == "wnba_official_news"
    assert payload["lead_promotion_recommendations"][0]["recommendation"] == "manual_story_candidate"
    assert payload["lead_promotion_recommendations"][0]["freshness_source"] == "article_metadata"
    assert "A concise public metadata description" in payload["lead_promotion_recommendations"][0]["detail"]
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_sources"] == "wnba_official_news; ap_womens_sports_wire"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_angle"] == "Roster or transaction update"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_recommended_path"] == "news_packet"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_confidence_tier"] == "needs_official_confirmation"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_second_source_id"] == "wnba_official_news"
    promote_action = next(action for action in payload["next_actions"] if action["title"] == "Promote source lead toward manual_story_candidate: Public team social lead")
    assert "needs_official_confirmation" in promote_action["detail"]
    assert "Suggested second source: wnba_official_news" in promote_action["detail"]
    news_candidate = next(item for item in payload["content_candidates"] if item["type"] == "News packet")
    assert news_candidate["source_grade"] == "publish_grade"
    assert news_candidate["source_score"] == "92"
    artifact_by_path = {item["path"]: item for item in payload["artifacts"]}
    assert artifact_by_path["graphics_upload_pack_status.csv"]["run_command"] == ".\\hsd.cmd run -Mode asset"
    assert artifact_by_path["results_dashboard/index.html"]["run_command"] == ".\\hsd.cmd run -Mode dashboards"

    assert "HSD Daily Operator Command Center" in html
    assert 'data-tab-target="today"' in html
    assert 'data-tab-target="content"' in html
    assert 'data-tab-target="sources"' in html
    assert 'data-tab-target="safety"' in html
    assert 'data-tab-target="artifacts"' in html
    assert 'id="artifactSearch"' in html
    assert "Paid APIs and auto-publishing are off" in html
    assert "Run next" in html
    assert ".\\hsd.cmd run -Mode asset" in html
    assert "Next step" in html
    assert "publish_grade" in html
    assert "Public team social lead" in html
    assert "Official metadata title for public team lead" in html
    assert "A concise public metadata description for operator review." in html
    assert "opportunity: 2 source(s)" in html
    assert "angle: Roster or transaction update" in html
    assert "path: news_packet" in html
    assert "confidence: needs_official_confirmation" in html
    assert "coverage: discovery_source_only" in html
    assert "cue: needs_official_confirmation" in html
    assert "assets: asset_not_required_for_news_packet" in html
    assert "second source: wnba_official_news" in html
    assert "Source coverage map" in html
    assert "Source registry intake template" in html
    assert "Source registry diff review" in html
    assert "duplicate_domain" in html
    assert "candidate domain already exists" in html
    assert "Source verification log" in html
    assert "operator_input_required" in html
    assert "operator fill-in" in html
    assert "Source registry update worksheet" in html
    assert "manual_registry_plan_after_verification" in html
    assert "not_performed_by_generator" in html
    assert "remove the manually added" in html
    assert "Source proposal promotion checklist" in html
    assert "verify_then_copy" in html
    assert "discard_duplicate_candidate_do_not_copy" in html
    assert "Yes_after_manual_freshness_check" in html
    assert "Source proposal draft" in html
    assert "ready_to_copy_after_freshness_check" in html
    assert "blocked_duplicate_review" in html
    assert "manual_copy_to_inbox_after_freshness_check" in html
    assert "hold_do_not_copy_until_duplicate_review" in html
    assert "Guided source pack readiness" in html
    assert "ready_for_registry_proposal" in html
    assert "needs_duplicate_review" in html
    assert "needs_source_freshness_check" in html
    assert "espn_wnba_scoreboard_pack_review" in html
    assert "Guided source proposal packs" in html
    assert "PWHL Source Proposal Pack" in html
    assert "Source proposal review" in html
    assert "PWHL" in html
    assert "pwhl_official_scores" in html
    assert "pwhl_boston_fleet_team" in html
    assert "missing official league/team source" in html
    assert "proposal_only_do_not_import" in html
    assert "social-only source cannot be added" in html
    assert "wnba_official_news; ap_womens_sports_wire" in html
    assert "recent_30_days via article_metadata" in html
    assert "Lead promotion recommendations" in html
    assert "Next actions" in markdown
    assert "Run: `.\\hsd.cmd run -Mode asset`." in markdown
    assert "Create with `.\\hsd.cmd run -Mode dashboards`" in markdown
    assert "source: publish_grade" in markdown
    assert "Morning source discovery" in markdown
    assert "Source registry diff review" in markdown
    assert "duplicate_domain" in markdown
    assert "candidate domain already exists" in markdown
    assert "Source verification log" in markdown
    assert "operator_input_required" in markdown
    assert "url_checked: operator fill-in" in markdown
    assert "Source registry update worksheet" in markdown
    assert "manual_registry_plan_after_verification" in markdown
    assert "not_performed_by_generator" in markdown
    assert "Source proposal promotion checklist" in markdown
    assert "verify_then_copy" in markdown
    assert "discard" in markdown
    assert "Source proposal draft" in markdown
    assert "ready_to_copy_after_freshness_check" in markdown
    assert "Duplicate review required" in markdown
    assert "Guided source pack readiness" in markdown
    assert "needs_duplicate_review" in markdown
    assert "missing cross-check candidate" in markdown
    assert "opportunity: 2 source(s)" in markdown
    assert "angle: Roster or transaction update" in markdown
    assert "path: news_packet" in markdown
    assert "confidence: needs_official_confirmation" in markdown
    assert "coverage: discovery_source_only" in markdown
    assert "assets: asset_not_required_for_news_packet" in markdown
    assert "second source: wnba_official_news" in markdown
    assert "Source coverage map" in markdown
    assert "Source registry intake template" in markdown
    assert "Guided source proposal packs" in markdown
    assert "PWHL Source Proposal Pack" in markdown
    assert "Source proposal review" in markdown
    assert "PWHL | gap" in markdown
    assert "pwhl_official_news" in markdown
    assert "pwhl_official_scores" in markdown
    assert "enabled: No | action: proposal_only_do_not_import" in markdown
    assert "pwhl_instagram | hold | flags: social_only" in markdown
    assert "PWHL league/team official pages" in markdown
    assert "preview: Official metadata title for public team lead" in markdown
    assert "recent_30_days via article_metadata" in markdown
    assert "Lead promotion recommendations" in markdown

    command_center.write_outputs(payload)
    assert Path("operator_command_center.html").exists()
    assert Path("operator_command_center.json").exists()
    assert Path("operator_command_center.md").exists()


def test_operator_command_center_does_not_refresh_handoff_as_side_effect(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    Path("generate_hsd_mermaid_handoff_publisher_v2_6_1.py").write_text(
        "from pathlib import Path\nPath('unexpected_refresh_marker.txt').write_text('ran')\n",
        encoding="utf-8",
    )

    command_center.write_outputs(command_center.build_payload())

    assert not Path("unexpected_refresh_marker.txt").exists()


def test_operator_command_center_infers_legacy_packet_source_grade(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    write_csv(
        "news_fact_packets.csv",
        [
            {
                "urgency": "P1",
                "headline": "New York Liberty beat Las Vegas Aces",
                "production_ready": "Yes",
                "caption_hard_fact": "Verified final: New York Liberty 87, Las Vegas Aces 76.",
                "source_count": "4",
                "primary_source_count": "2",
            }
        ],
    )

    payload = command_center.build_payload()

    assert any(item["label"] == "Publish-grade packets" and item["value"] == "1" for item in payload["metrics"])
    news_candidate = next(item for item in payload["content_candidates"] if item["type"] == "News packet")
    assert news_candidate["source_grade"] == "publish_grade"
    assert news_candidate["source_reason"] == "Legacy packet inferred from production-ready status and primary source count"


def test_local_runner_collects_daily_command_center_artifacts() -> None:
    runner = (REPO / "scripts" / "hsd_local.ps1").read_text(encoding="utf-8")
    assert "operator_command_center.html" in runner
    assert "operator_command_center.md" in runner
    assert "operator_command_center.json" in runner
    assert "bebe_posting_schedule_today.md" in runner
    assert "preview_bundle_quality_summary.csv" in runner
    assert "publish_guard_report.json" in runner
    assert "source_registry_audit.md" in runner
    assert "source_registry_audit.json" in runner
    assert "morning_source_discovery_board.md" in runner
    assert "morning_source_discovery_board.csv" in runner
    assert "morning_source_discovery_board.json" in runner
    assert "morning_lead_promotion_recommendations.md" in runner
    assert "morning_lead_promotion_recommendations.csv" in runner
    assert "morning_lead_promotion_recommendations.json" in runner
    assert "source_coverage_map.csv" in runner
    assert "source_registry_intake_template.md" in runner
    assert "source_registry_intake_template.csv" in runner
    assert "source_registry_proposal_review.md" in runner
    assert "source_registry_proposal_review.csv" in runner
    assert "source_registry_proposal_draft.md" in runner
    assert "source_registry_proposal_draft.csv" in runner
    assert "source_registry_proposal_promotion_checklist.md" in runner
    assert "source_registry_proposal_promotion_checklist.csv" in runner
    assert "source_registry_update_worksheet.md" in runner
    assert "source_registry_update_worksheet.csv" in runner
    assert "source_registry_diff_review.md" in runner
    assert "source_registry_diff_review.csv" in runner
    assert "source_registry_verification_log.md" in runner
    assert "source_registry_verification_log.csv" in runner
    assert "source_proposal_pack_readiness.md" in runner
    assert "source_proposal_pack_readiness.csv" in runner
    assert "source_proposal_packs.md" in runner
    assert "source_proposal_packs.csv" in runner
    assert "wnba_source_proposal_pack.md" in runner
    assert "wnba_source_proposal_pack.csv" in runner
    assert "nwsl_source_proposal_pack.md" in runner
    assert "nwsl_source_proposal_pack.csv" in runner
    assert "lpga_source_proposal_pack.md" in runner
    assert "lpga_source_proposal_pack.csv" in runner
    assert "pwhl_source_proposal_pack.md" in runner
    assert "pwhl_source_proposal_pack.csv" in runner
    assert "manual_workflow_handoff.md" in runner
    assert "manual_workflow_pack_status.csv" in runner
    assert "ig_story_results_queue.csv" in runner
    assert "ig_story_results_upload_pack_status.csv" in runner
    assert "final_score_story_guard_report.md" in runner
    assert "multi_post_daily_board.md" in runner
    assert "post_slot_status.csv" in runner
    assert "ig_feed_queue.csv" in runner
    assert "threads_queue.csv" in runner
    assert "launch_command_center.md" in runner
    assert "launch_instagram_publish_queue.csv" in runner
    assert "launch_quality_gate.csv" in runner
    assert "launch_manifest.json" in runner
    assert "results_dashboard/index.html" in runner
    assert "studio_dashboard/index.html" in runner
    command_center = (REPO / "generate_hsd_operator_command_center_v2.py").read_text(encoding="utf-8")
    assert "Results drill-down dashboard" in command_center
    assert "Studio drill-down dashboard" in command_center
