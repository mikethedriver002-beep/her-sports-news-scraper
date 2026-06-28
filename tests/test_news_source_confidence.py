from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_news_sync_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_news_sync_v1_source_confidence", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_candidate() -> dict:
    return {
        "candidate_id": "candidate-1",
        "queue_section": "MUST POST",
        "sport": "basketball",
        "league": "WNBA",
        "editorial_bucket": "Must Post",
        "graphics_headline": "Liberty beat Aces",
        "graphics_subhead": "Liberty 87, Aces 76",
        "final_score": "Liberty 87 - Aces 76",
        "winner": "Liberty",
        "loser": "Aces",
        "outcome_type": "win",
        "event_date": "2026-06-24",
        "event_date_confidence": "exact_from_results_record",
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_results_desk_final_scores_are_publish_grade_source_facts() -> None:
    module = load_module()
    candidate = base_candidate()
    candidate["result_record_source"] = "top_womens_results.csv"

    packet = module.build_fact_packet(candidate, [], {}, module.angle_rules_defaults(), "run-1")

    assert packet["source_publish_grade"] == "publish_grade"
    assert packet["source_confidence_tier"] == "publish_grade"
    assert int(packet["source_confidence_score"]) >= 70
    assert "Results Desk final score" in packet["source_confidence_reason"]
    assert packet["manual_review"] == "No"
    assert packet["production_ready"] == "Yes"


def test_discovery_only_sources_hold_packet_for_editor_review() -> None:
    module = load_module()
    candidate = base_candidate()
    observations = [
        {
            "usable_context": "Yes",
            "publish_use": "discovery_only",
            "source_type": "social_manual",
            "url": "https://example.com/social-post",
            "context_signal": "Public social lead only",
        }
    ]

    packet = module.build_fact_packet(candidate, observations, {}, module.angle_rules_defaults(), "run-1")

    assert packet["source_publish_grade"] == "discovery_only"
    assert packet["source_confidence_tier"] == "discovery_only"
    assert packet["manual_review"] == "Yes"
    assert packet["production_ready"] == "No"
    assert "source_confidence_discovery_only" in packet["review_flags"]


def test_legacy_observations_infer_publish_use_from_source_type() -> None:
    module = load_module()
    candidate = base_candidate()
    observations = [
        {
            "usable_context": "Yes",
            "source_type": "official_league",
            "url": "https://www.wnba.com/",
            "context_signal": "Official league source available",
        }
    ]

    packet = module.build_fact_packet(candidate, observations, {}, module.angle_rules_defaults(), "run-1")

    assert packet["source_publish_grade"] == "publish_grade"
    assert packet["source_confidence_tier"] == "publish_grade"
    assert packet["production_ready"] == "Yes"


def test_source_trust_bands_separate_publish_sources_from_leads() -> None:
    module = load_module()

    assert module.source_trust_band("official_league") == "green"
    assert module.publish_use_for_source("official_league") == "publish_grade"
    assert module.source_trust_band("wire_context") == "green"
    assert module.publish_use_for_source("wire_context") == "publish_grade"
    assert module.source_trust_band("scoreboard_backup") == "green_cross_check"
    assert module.publish_use_for_source("scoreboard_backup") == "cross_check"
    assert module.source_trust_band("mainstream_context") == "green_cross_check"
    assert module.publish_use_for_source("social_manual") == "discovery_only"
    assert module.publish_use_for_source("private_paid_feed") == "blocked"


def test_default_registry_keeps_free_official_coverage_available() -> None:
    module = load_module()
    registry = module.merge_source_registry({})
    source_ids = {source["source_id"] for source in registry["sources"]}

    assert {
        "ap_womens_sports",
        "reuters_sports",
        "wta_official",
        "lpga_official",
        "ncaa_softball_official",
        "us_soccer_uswnt",
    } <= source_ids
    assert {
        "atlanta dream",
        "chicago sky",
        "connecticut sun",
        "dallas wings",
        "golden state valkyries",
        "indiana fever",
        "las vegas aces",
        "los angeles sparks",
        "minnesota lynx",
        "new york liberty",
        "phoenix mercury",
        "portland fire",
        "seattle storm",
        "toronto tempo",
        "washington mystics",
    } <= set(registry["team_sources"])


def test_breaking_public_signal_rows_are_review_only_and_source_backed() -> None:
    module = load_module()
    candidate = base_candidate()
    candidate["graphics_headline"] = "Breaking: New York Liberty beat Las Vegas Aces after injury update"
    observations = [
        {
            "usable_context": "Yes",
            "publish_use": "publish_grade",
            "source_type": "official_team",
            "url": "https://liberty.wnba.com/news/injury-update",
            "domain": "liberty.wnba.com",
            "context_signal": "Official team source available",
        },
        {
            "usable_context": "Partial",
            "publish_use": "discovery_only",
            "source_type": "community_public",
            "url": "https://example.com/public-thread",
            "domain": "example.com",
            "context_signal": "Public community discussion needs review",
        },
    ]

    packet = module.build_fact_packet(candidate, observations, {}, module.angle_rules_defaults(), "run-1")
    rows = module.build_breaking_public_signal_rows([packet], {packet["candidate_id"]: observations}, "run-1")
    row = rows[0]

    assert row["urgency_band"] in {"P0_breaking_review", "P1_urgent_review"}
    assert row["public_signal_status"] == "candidate_public_signal_review_only"
    assert row["public_signal_confidence"] == "low"
    assert row["manual_review_required"] == "true"
    assert row["review_only"] == "true"
    assert row["publish_ready"] == "false"
    assert row["auto_publish"] == "false"
    assert row["auto_source_enablement"] == "false"
    assert row["approval_state_change"] == "false"
    assert "no paid API" in row["limitations"]
    assert "liberty.wnba.com" in row["source_domains"]

    intake = module.breaking_confirmation_intake_rows(rows)
    intake_row = intake[0]
    assert intake_row["confirmation_status"] == "operator_input_required"
    assert intake_row["required_confirmation_type"] == "operator_verify_primary_or_official_source"
    assert "official news confirmation" in intake_row["official_source_search_hint"]
    assert intake_row["operator_checked_url"] == ""
    assert intake_row["review_only"] == "true"
    assert intake_row["publish_ready"] == "false"
    assert intake_row["auto_publish"] == "false"
    assert intake_row["auto_source_enablement"] == "false"

    duplicate = dict(row)
    duplicate["candidate_id"] = "candidate-2"
    duplicate["source_domains"] = "espn.com"
    duplicate["source_urls"] = "[\"https://www.espn.com/wnba/story/_/id/test\"]"
    duplicate["public_signal_count"] = "1"
    game_rows = [
        {
            "row_id": "event-liberty-aces",
            "status": "final",
            "recap_candidate": "Yes",
            "home_team": "New York Liberty",
            "away_team": "Las Vegas Aces",
            "final_score": "Las Vegas Aces 80 - New York Liberty 88",
            "selected_source": "espn_wnba_public",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/401000001",
            "source_domain": "www.espn.com",
        }
    ]
    proof_rows = [
        {
            "proof_id": "proof-final-liberty",
            "event_uid": "event-liberty-aces",
            "matchup": "Las Vegas Aces at New York Liberty",
            "fact_type": "final_score",
            "fact_value": "Las Vegas Aces 80 - New York Liberty 88",
            "proof_status": "score_source_backed_operator_verify",
            "manual_box_score_confirmation_needed": "No",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/401000001",
            "evidence_artifact_row": "stats_evidence_gap_board_v1.csv event_uid=event-liberty-aces",
            "exact_next_file_or_intake": "Open final_score_stat_proof_v1.csv proof_id=proof-final-liberty; then verify the source URL.",
        },
        {
            "proof_id": "proof-player-liberty",
            "event_uid": "event-liberty-aces",
            "matchup": "Las Vegas Aces at New York Liberty",
            "fact_type": "named_player_stat_line",
            "fact_value": "Sabrina Ionescu (New York Liberty): PTS 24, AST 8",
            "named_player": "Sabrina Ionescu",
            "proof_status": "named_stat_line_source_backed_operator_verify",
            "manual_box_score_confirmation_needed": "No",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/401000001",
            "evidence_artifact_row": "stats_evidence_gap_board_v1.csv event_uid=event-liberty-aces; top_performers item 1",
            "exact_next_file_or_intake": "Open final_score_stat_proof_v1.csv proof_id=proof-player-liberty; then verify the named player stat line.",
        },
    ]
    proof_confirmation_rows = [
        {
            "proof_id": "proof-final-liberty",
            "fact_type": "final_score",
            "operator_checked_source_url": "",
            "operator_confirmation_status": "",
        },
        {
            "proof_id": "proof-player-liberty",
            "fact_type": "named_player_stat_line",
            "operator_checked_source_url": "",
            "operator_confirmation_status": "",
        },
    ]
    proof_review_order_rows = [
        {
            "review_order": "1",
            "review_phase": "2_final_score_source_check",
            "fact_type": "final_score",
            "proof_row_to_open": "final_score_stat_proof_v1.csv proof_id=proof-final-liberty",
            "intake_row_to_record": "final_score_stat_proof_confirmation_intake_v1.csv proof_id=proof-final-liberty",
        },
        {
            "review_order": "2",
            "review_phase": "3_named_player_stat_source_check",
            "fact_type": "named_player_stat_line",
            "proof_row_to_open": "final_score_stat_proof_v1.csv proof_id=proof-player-liberty",
            "intake_row_to_record": "final_score_stat_proof_confirmation_intake_v1.csv proof_id=proof-player-liberty",
        },
    ]
    game_fact_confirmation_rows = [
        {
            "event_uid": "event-liberty-aces",
            "overall_confirmation_status": "source_confirmed_operator_verify_before_use",
            "source_confirmation_tier": "single_free_public_scoreboard_operator_verify",
            "source_confirmation_limitations": "Single ESPN public scoreboard row; not a paid API, but not a human approval or publish-ready confirmation.",
            "source_domain": "www.espn.com",
            "retrieved_at_utc": "2026-06-28T12:01:53+00:00",
            "source_freshness_status": "evidence_fresh_under_3h_operator_verify",
            "source_freshness_age_minutes": "42",
            "source_freshness_note": "Evidence was retrieved within 3 hours; operator still verifies source facts before use.",
            "recap_render_readiness": "athlete_led_manual_render_candidate",
            "story_proof_card_row_to_open": "story_proof_card_v1.csv event_id=event-liberty-aces; candidate_id=story-card-liberty",
            "exact_next_file_or_intake": "Open game_fact_confirmation_status_v1.csv event_uid=event-liberty-aces; then open story_proof_card_v1.csv event_id=event-liberty-aces; candidate_id=story-card-liberty.",
        },
    ]
    story_proof_card_rows = [
        {
            "candidate_id": "story-card-liberty",
            "candidate_rank": "1",
            "event_id": "event-liberty-aces",
            "proof_status": "proof_card_ready_for_manual_review",
            "copy_unlock_level": "score_and_named_stat_copy_review_ready",
            "renderability_state": "athlete_led_manual_render_candidate",
            "athlete_name": "Sabrina Ionescu",
            "manual_intake_path": "final_score_stat_proof_confirmation_intake_v1.csv proof_id=proof-player-liberty",
            "source_confirmation_cue": "free_public_box_score_stat_source_present_operator_verify",
            "game_fact_row": "game_fact_confirmation_status_v1.csv event_uid=event-liberty-aces",
            "smallest_next_action": "Open story_proof_card_v1.md, verify the official source URL, record the check in the manual intake row.",
        },
    ]
    clusters = module.breaking_signal_cluster_rows(
        [row, duplicate],
        packets=[packet],
        game_rows=game_rows,
        proof_rows=proof_rows,
        proof_confirmation_rows=proof_confirmation_rows,
        proof_review_order_rows=proof_review_order_rows,
        game_fact_confirmation_rows=game_fact_confirmation_rows,
        story_proof_card_rows=story_proof_card_rows,
        intake_rows=intake,
    )
    cluster = clusters[0]
    assert cluster["story_count"] == "2"
    assert cluster["source_diversity"] == "multi_domain"
    assert cluster["source_domain_count"] == "3"
    assert cluster["public_signal_count"] == "2"
    assert cluster["official_confirmation_status"] == "official_or_primary_signal_present_operator_verify"
    assert cluster["matching_official_evidence_status"] == "matching_news_and_free_result_evidence_operator_verify"
    assert cluster["matching_official_evidence_count"] == "2"
    assert "news_fact_packets.csv candidate_id=" in cluster["matching_official_evidence_artifacts"]
    assert "game_intelligence_board_v1.csv row_id=event-liberty-aces" in cluster["matching_official_evidence_artifacts"]
    assert cluster["corroboration_ladder_status"] == "official_and_reputable_artifact_cues_present_operator_verify"
    assert "official=present_operator_verify" in cluster["corroboration_ladder_summary"]
    assert "reputable_free=present_operator_verify" in cluster["corroboration_ladder_summary"]
    assert cluster["public_signal_corroboration"] == "public_or_community_signal_present_review_only_count=2_confidence=medium"
    assert cluster["missing_confirmation_cue"] == "human_confirmation_still_required_in_breaking_public_signal_confirmation_intake"
    assert "liberty.wnba.com" in cluster["official_source_corroboration"]
    assert "espn.com" in cluster["reputable_source_corroboration"]
    assert "https://www.espn.com/wnba/game/_/gameId/401000001" in cluster["corroboration_evidence_urls"]
    assert "Why now: P" in cluster["urgency_review_reason"]
    assert "story_proof_card_ready_operator_verify" in cluster["urgency_review_reason"]
    assert cluster["source_proof_readiness_status"] == "story_proof_card_ready_operator_verify"
    assert "proof_card_ready_for_manual_review" in cluster["source_proof_readiness_summary"]
    assert "Sabrina Ionescu" in cluster["source_proof_readiness_summary"]
    assert "game_source_tier=single_free_public_scoreboard_operator_verify" in cluster["source_proof_readiness_summary"]
    assert "story_proof_card_v1.csv event_id=event-liberty-aces" in cluster["story_proof_card_target"]
    assert cluster["game_fact_confirmation_target"] == "game_fact_confirmation_status_v1.csv event_uid=event-liberty-aces"
    assert cluster["source_proof_readiness_next_action"].startswith("Open story_proof_card_v1.md")
    assert cluster["game_source_confirmation_tier"] == "single_free_public_scoreboard_operator_verify"
    assert "not a human approval or publish-ready confirmation" in cluster["game_source_confirmation_limitations"]
    assert cluster["game_source_confirmation_tier_target"] == "game_fact_confirmation_status_v1.csv event_uid=event-liberty-aces"
    assert "not official, multi-source, human-approved, or publish-ready confirmation" in cluster["game_source_confirmation_tier_cue"]
    assert cluster["game_source_freshness_status"] == "evidence_fresh_under_3h_operator_verify"
    assert cluster["game_source_freshness_age_minutes"] == "42"
    assert cluster["game_source_retrieved_at_utc"] == "2026-06-28T12:01:53+00:00"
    assert "retrieved within 3 hours" in cluster["game_source_freshness_note"]
    assert cluster["game_source_freshness_target"] == "game_fact_confirmation_status_v1.csv event_uid=event-liberty-aces"
    assert "Fresh enough for review triage" in cluster["game_source_freshness_cue"]
    assert cluster["verification_priority_status"] == "manual_confirmation_intake_first"
    assert "source_class_support official=present_operator_verify" in cluster["verification_priority_summary"]
    assert "game_source_tier=single_free_public_scoreboard_operator_verify" in cluster["verification_priority_summary"]
    assert "game_source_freshness=evidence_fresh_under_3h_operator_verify" in cluster["verification_priority_summary"]
    assert "source_tier_limit=single_free_public_scoreboard_operator_verify" in cluster["verification_priority_summary"]
    assert "source_freshness_limit=evidence_fresh_under_3h_operator_verify" in cluster["verification_priority_summary"]
    assert cluster["verification_priority_target"].startswith("breaking_public_signal_confirmation_intake.csv")
    assert cluster["verification_priority_next_action"].startswith("Open breaking_public_signal_confirmation_intake.csv")
    assert "Public/community signal is review-only discovery context count=2 confidence=medium" in cluster["public_signal_limitations_cue"]
    assert "breaking_public_signal_confirmation_intake.csv confirmation_id=" in cluster["exact_source_or_intake_row_to_open"]
    assert "operator must still verify" in cluster["manual_confirmation_gap"].lower()
    assert cluster["score_stat_proof_status"] == "score_and_named_player_stat_proof_present_operator_verify"
    assert cluster["named_player_stat_proof_count"] == "1"
    assert "Sabrina Ionescu" in cluster["named_player_stat_proof_examples"]
    assert "final_score_stat_proof_v1.csv proof_id=proof-player-liberty" in cluster["exact_score_stat_proof_row_or_source_to_open"]
    assert "stats_evidence_gap_board_v1.csv event_uid=event-liberty-aces" in cluster["score_stat_proof_artifacts"]
    assert "breaking_public_signal_confirmation_intake.csv confirmation_id=" in cluster["breaking_claim_confirmation_target"]
    assert cluster["score_proof_confirmation_target"] == "final_score_stat_proof_confirmation_intake_v1.csv proof_id=proof-final-liberty"
    assert cluster["named_player_stat_proof_confirmation_targets"] == "final_score_stat_proof_confirmation_intake_v1.csv proof_id=proof-player-liberty"
    assert cluster["score_stat_confirmation_status"] == "operator_input_required_in_score_stat_proof_confirmation_intake"
    assert "operator_checked_source_url plus operator_confirmation_status" in cluster["exact_human_confirmation_next_action"]
    assert "final-score proof" in cluster["exact_human_confirmation_next_action"]
    assert "named-player stat proof" in cluster["exact_human_confirmation_next_action"]
    assert cluster["score_stat_review_order_status"] == "review_order_rows_present_operator_follow_walkthrough"
    assert cluster["score_stat_review_walkthrough_target"] == "final_score_stat_proof_review_walkthrough_v1.md"
    assert "final_score_stat_proof_review_order_v1.csv review_order=1" in cluster["first_score_stat_review_order_target"]
    assert "proof-final-liberty" in cluster["first_score_stat_review_order_target"]
    assert "review_order=2" in cluster["score_stat_review_order_targets"]
    assert "final_score_stat_proof_review_walkthrough_v1.md" in cluster["exact_review_walkthrough_next_action"]
    assert "final_score_stat_proof_confirmation_intake_v1.csv" in cluster["exact_review_walkthrough_next_action"]
    assert "breaking_public_signal_confirmation_intake.csv" in cluster["exact_manual_next_action"]
    assert cluster["review_only"] == "true"
    assert cluster["publish_ready"] == "false"
    assert cluster["auto_publish"] == "false"
    assert cluster["auto_source_enablement"] == "false"

    partial_cluster = module.breaking_signal_cluster_rows(
        [duplicate],
        packets=[],
        game_rows=game_rows,
        proof_rows=proof_rows,
        proof_confirmation_rows=proof_confirmation_rows,
        proof_review_order_rows=proof_review_order_rows,
        game_fact_confirmation_rows=game_fact_confirmation_rows,
        story_proof_card_rows=story_proof_card_rows,
        intake_rows=intake,
    )[0]
    assert partial_cluster["corroboration_ladder_status"] == "partial_corroboration_operator_verify"
    assert partial_cluster["official_source_corroboration"] == "missing_official_source_operator_add_to_intake"
    assert partial_cluster["verification_priority_status"] == "official_source_confirmation_first"
    assert partial_cluster["game_source_confirmation_tier"] == "single_free_public_scoreboard_operator_verify"
    assert partial_cluster["game_source_freshness_status"] == "evidence_fresh_under_3h_operator_verify"
    assert partial_cluster["verification_priority_target"] == "breaking_public_signal_confirmation_intake.csv candidate_id=candidate-2"
    assert "official team/league, wire, primary, or operator-checked source URL" in partial_cluster["verification_priority_next_action"]
    assert "Public/community signal is review-only discovery context count=1 confidence=low" in partial_cluster["public_signal_limitations_cue"]

    stale_game_fact_confirmation_rows = [dict(game_fact_confirmation_rows[0])]
    stale_game_fact_confirmation_rows[0]["source_freshness_status"] = "evidence_stale_over_24h_manual_check"
    stale_game_fact_confirmation_rows[0]["source_freshness_age_minutes"] = "1800"
    stale_game_fact_confirmation_rows[0]["source_freshness_note"] = "Evidence is older than 24 hours; re-open the source before use."
    stale_cluster = module.breaking_signal_cluster_rows(
        [duplicate],
        packets=[],
        game_rows=game_rows,
        proof_rows=proof_rows,
        proof_confirmation_rows=proof_confirmation_rows,
        proof_review_order_rows=proof_review_order_rows,
        game_fact_confirmation_rows=stale_game_fact_confirmation_rows,
        story_proof_card_rows=story_proof_card_rows,
        intake_rows=intake,
    )[0]
    assert stale_cluster["verification_priority_status"] == "source_freshness_recheck_first"
    assert stale_cluster["verification_priority_target"] == "game_fact_confirmation_status_v1.csv event_uid=event-liberty-aces"
    assert "re-check the source URL timestamp/recency" in stale_cluster["verification_priority_next_action"]
    assert "evidence_stale_over_24h_manual_check" in stale_cluster["game_source_freshness_cue"]

    missing_proof_cluster = module.breaking_signal_cluster_rows([row], packets=[packet], game_rows=[], proof_rows=[], proof_confirmation_rows=[], intake_rows=intake)[0]
    assert missing_proof_cluster["score_stat_proof_status"] == "no_matching_score_stat_proof_operator_confirmation_required"
    assert "No matching final-score/stat proof row found" in missing_proof_cluster["score_stat_manual_confirmation_cue"]
    assert "final_score_stat_proof_v1.csv" in missing_proof_cluster["exact_score_stat_proof_row_or_source_to_open"]
    assert missing_proof_cluster["score_stat_confirmation_status"] == "no_score_stat_proof_to_confirm"
    assert "No final-score proof confirmation target matched" in missing_proof_cluster["exact_human_confirmation_next_action"]
    assert missing_proof_cluster["score_stat_review_order_status"] == "no_score_stat_proof_to_order"
    assert "final_score_stat_proof_review_walkthrough_v1.md" in missing_proof_cluster["exact_review_walkthrough_next_action"]
    assert missing_proof_cluster["verification_priority_status"] == "source_proof_readiness_gap_first"


def test_box_score_top_performers_match_the_same_game() -> None:
    module = load_module()
    box_text = """# WNBA Box-Score Enrichment Audit v5

1. **Connecticut Sun beat Washington Mystics**
   - ESPN event: 401857024
   - Status: found
   - Top performers: Olivia Nelson-Ododa (Connecticut Sun): PTS 12, REB 9 | Kiki Iriafen (Washington Mystics): PTS 11, REB 14

2. **Chicago Sky beat Portland Fire**
   - ESPN event: 401857025
   - Status: found
   - Top performers: Kamilla Cardoso (Chicago Sky): PTS 30, REB 8 | Sydney Taylor (Chicago Sky): PTS 29, REB 3
"""
    box_map = module.parse_box_score_summary(box_text)
    candidate = base_candidate()
    candidate.update(
        {
            "graphics_headline": "Chicago Sky beat Portland Fire",
            "matchup": "Chicago Sky vs Portland Fire",
            "winner": "Chicago Sky",
            "loser": "Portland Fire",
            "final_score": "Chicago Sky 92 - Portland Fire 85",
        }
    )

    top_performers = module.find_top_performers(candidate, box_map)

    assert "Kamilla Cardoso" in top_performers
    assert "Olivia Nelson-Ododa" not in top_performers


def test_box_score_top_performers_require_both_candidate_teams() -> None:
    module = load_module()
    box_map = module.parse_box_score_summary(
        """1. **Connecticut Sun beat Washington Mystics**
   - ESPN event: 401857024
   - Status: found
   - Top performers: Olivia Nelson-Ododa (Connecticut Sun): PTS 12, REB 9 | Kiki Iriafen (Washington Mystics): PTS 11, REB 14
"""
    )
    candidate = base_candidate()
    candidate.update(
        {
            "graphics_headline": "Portland Fire at Washington Mystics",
            "matchup": "Portland Fire at Washington Mystics",
            "winner": "",
            "loser": "",
            "final_score": "",
        }
    )

    assert module.find_top_performers(candidate, box_map) == ""


def test_game_source_confirmation_bridge_links_game_stats_and_cluster_rows() -> None:
    module = load_module()
    game_rows = [
        {
            "row_id": "event-sky-fire",
            "game_date": "2026-06-26",
            "league": "WNBA",
            "home_team": "Chicago Sky",
            "away_team": "Portland Fire",
            "status": "final",
            "final_score": "Portland Fire 94 - Chicago Sky 124",
            "recap_candidate": "Yes",
            "selected_source": "espn_wnba_public",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/401857025",
            "source_domain": "www.espn.com",
        }
    ]
    stats_rows = [
        {
            "event_uid": "event-sky-fire",
            "stats_evidence_status": "confirmed_free_public_box_score",
            "confirmation_source_url": "https://www.espn.com/wnba/game/_/gameId/401857025",
            "top_performers": "Kamilla Cardoso (Chicago Sky): PTS 30, REB 8",
        }
    ]
    packets = [
        {
            "candidate_id": "candidate-sky",
            "headline": "Chicago Sky beat Portland Fire",
            "source_urls_json": "[\"https://sky.wnba.com/news/recap\"]",
        }
    ]
    clusters = [
        {
            "cluster_id": "signal-cluster-sky",
            "cluster_headline": "Chicago Sky beat Portland Fire",
            "candidate_ids": "candidate-sky",
            "matching_official_evidence_status": "matching_news_and_free_result_evidence_operator_verify",
            "matching_official_evidence_artifacts": "news_fact_packets.csv candidate_id=candidate-sky; game_intelligence_board_v1.csv row_id=event-sky-fire",
            "matching_official_evidence_urls": "[\"https://sky.wnba.com/news/recap\", \"https://www.espn.com/wnba/game/_/gameId/401857025\"]",
        }
    ]

    rows = module.game_source_confirmation_bridge_rows(
        run_id="run-1",
        game_rows=game_rows,
        stats_rows=stats_rows,
        cluster_rows=clusters,
        packets=packets,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["game_row_ref"] == "row_id=event-sky-fire"
    assert row["stats_row_ref"] == "event_uid=event-sky-fire"
    assert row["cluster_row_ref"] == "cluster_id=signal-cluster-sky"
    assert row["news_packet_ref"] == "candidate_id=candidate-sky"
    assert row["official_free_game_evidence_status"] == "official_or_free_game_evidence_present_operator_verify"
    assert row["stats_evidence_status"] == "confirmed_free_public_box_score"
    assert row["cross_signal_status"] == "matching_news_and_free_result_evidence_operator_verify"
    assert "game_intelligence_board_v1.csv row_id=event-sky-fire" in row["exact_next_row_or_source_to_open"]
    assert "stats_evidence_gap_board_v1.csv event_uid=event-sky-fire" in row["exact_next_row_or_source_to_open"]
    assert "breaking_public_signal_clusters.csv cluster_id=signal-cluster-sky" in row["exact_next_row_or_source_to_open"]
    assert "final_score_stat_proof_confirmation_intake_v1.csv" in row["exact_next_row_or_source_to_open"]
    assert "final_score_stat_proof_confirmation_intake_v1.csv for final score and named-player stat proof" in row["operator_confirmation_target"]
    source_urls = json.loads(row["news_or_cluster_source_urls"])
    assert source_urls == list(dict.fromkeys(source_urls))
    assert source_urls.count("https://sky.wnba.com/news/recap") == 1
    assert row["manual_confirmation_needed"] == "true"
    assert row["review_only"] == "true"
    assert row["publish_ready"] == "false"
    assert row["auto_publish"] == "false"
    assert row["auto_source_enablement"] == "false"
    assert row["approval_state_change"] == "false"


def test_news_sync_prefers_latest_local_results_over_stale_root(tmp_path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HSD_RUN_OUTPUT_DIR", raising=False)
    latest = tmp_path / "outputs" / "local" / "latest" / "files"
    latest.mkdir(parents=True)
    (tmp_path / "top_womens_results.csv").write_text("headline\nstale-root\n", encoding="utf-8")
    (latest / "top_womens_results.csv").write_text("headline\nfresh-latest\n", encoding="utf-8")

    resolved, text = module.resolve_input("top_womens_results.csv")

    assert resolved.resolve() == latest / "top_womens_results.csv"
    assert "fresh-latest" in text


def test_news_sync_writes_run_scoped_breaking_public_signal_artifacts(tmp_path, monkeypatch) -> None:
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setenv("HSD_NEWS_ENABLE_FETCH", "false")
    write_csv(
        run_dir / "top_womens_results.csv",
        [
            {
                "gender_scope": "women",
                "status_norm": "final",
                "final_score_display": "New York Liberty 88 - Las Vegas Aces 80",
                "graphics_headline": "Breaking: Liberty announce star guard injury update",
                "caption_seed": "Liberty beat Aces after injury update",
                "sport_norm": "basketball",
                "league_norm": "WNBA",
                "editorial_bucket": "Must Post",
                "content_action": "Make First",
                "editorial_rank": "99",
                "outcome_type": "win",
                "winner": "New York Liberty",
                "loser": "Las Vegas Aces",
                "matchup": "New York Liberty vs Las Vegas Aces",
                "scheduled_date_local": "2026-06-26",
                "source_url": "https://liberty.wnba.com/news/injury-update",
                "manual_review": "No",
            }
        ],
        [
            "gender_scope",
            "status_norm",
            "final_score_display",
            "graphics_headline",
            "caption_seed",
            "sport_norm",
            "league_norm",
            "editorial_bucket",
            "content_action",
            "editorial_rank",
            "outcome_type",
            "winner",
            "loser",
            "matchup",
            "scheduled_date_local",
            "source_url",
            "manual_review",
        ],
    )
    module = load_module()

    module.main()

    queue = run_dir / "breaking_public_signal_queue.csv"
    report = run_dir / "breaking_public_signal_queue.md"
    signal_manifest = run_dir / "breaking_public_signal_manifest.json"
    confirmation_csv = run_dir / "breaking_public_signal_confirmation_intake.csv"
    confirmation_md = run_dir / "breaking_public_signal_confirmation_intake.md"
    clusters_csv = run_dir / "breaking_public_signal_clusters.csv"
    clusters_md = run_dir / "breaking_public_signal_clusters.md"
    bridge_csv = run_dir / "game_source_confirmation_bridge_v1.csv"
    bridge_md = run_dir / "game_source_confirmation_bridge_v1.md"
    bridge_json = run_dir / "game_source_confirmation_bridge_v1.json"
    news_manifest = run_dir / "news_sync_manifest.json"
    assert queue.exists()
    assert report.exists()
    assert signal_manifest.exists()
    assert confirmation_csv.exists()
    assert confirmation_md.exists()
    assert clusters_csv.exists()
    assert clusters_md.exists()
    assert bridge_csv.exists()
    assert bridge_md.exists()
    assert bridge_json.exists()
    rows = list(csv.DictReader(queue.open(newline="", encoding="utf-8")))
    confirmation_rows = list(csv.DictReader(confirmation_csv.open(newline="", encoding="utf-8")))
    cluster_rows = list(csv.DictReader(clusters_csv.open(newline="", encoding="utf-8")))
    bridge_rows = list(csv.DictReader(bridge_csv.open(newline="", encoding="utf-8")))
    assert rows
    assert confirmation_rows
    assert cluster_rows
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["auto_publish"] == "false" for row in rows)
    assert all(row["auto_source_enablement"] == "false" for row in rows)
    assert all(row["confirmation_status"] == "operator_input_required" for row in confirmation_rows)
    assert all(row["operator_checked_url"] == "" for row in confirmation_rows)
    assert all(row["review_only"] == "true" for row in confirmation_rows)
    assert all(row["publish_ready"] == "false" for row in confirmation_rows)
    assert all(row["auto_publish"] == "false" for row in confirmation_rows)
    assert all(row["auto_source_enablement"] == "false" for row in confirmation_rows)
    assert all(row["review_only"] == "true" for row in cluster_rows)
    assert all(row["publish_ready"] == "false" for row in cluster_rows)
    assert all(row["auto_publish"] == "false" for row in cluster_rows)
    assert all(row["auto_source_enablement"] == "false" for row in cluster_rows)
    assert all(row["review_only"] == "true" for row in bridge_rows)
    assert all(row["publish_ready"] == "false" for row in bridge_rows)
    assert all(row["auto_publish"] == "false" for row in bridge_rows)
    assert all(row["auto_source_enablement"] == "false" for row in bridge_rows)
    assert any(row["headline"] == "Breaking: Liberty announce star guard injury update" for row in rows)
    signal_payload = json.loads(signal_manifest.read_text(encoding="utf-8"))
    news_payload = json.loads(news_manifest.read_text(encoding="utf-8"))
    assert signal_payload["review_only"] is True
    assert signal_payload["publish_ready"] is False
    assert signal_payload["counts"]["rows"] == len(rows)
    assert signal_payload["counts"]["confirmation_intake_rows"] == len(confirmation_rows)
    assert signal_payload["counts"]["cluster_rows"] == len(cluster_rows)
    assert "breaking_public_signal_queue.csv" in news_payload["outputs"]
    assert "breaking_public_signal_confirmation_intake.csv" in news_payload["outputs"]
    assert "breaking_public_signal_clusters.csv" in news_payload["outputs"]
    assert "game_source_confirmation_bridge_v1.csv" in news_payload["outputs"]
    assert news_payload["counts"]["breaking_public_signal_rows"] == len(rows)
    assert news_payload["counts"]["breaking_public_signal_review_only"] == len(rows)
    assert news_payload["counts"]["breaking_confirmation_intake_rows"] == len(confirmation_rows)
    assert news_payload["counts"]["breaking_signal_cluster_rows"] == len(cluster_rows)
    assert news_payload["counts"]["game_source_confirmation_bridge_rows"] == len(bridge_rows)
