import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8", errors="replace")


def load_results_desk():
    path = REPO / "generate_hsd_results_desk_v5.py"
    spec = importlib.util.spec_from_file_location("generate_hsd_results_desk_v5_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_independent_wnba_schedule_verifier_is_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/verify_hsd_wnba_schedule_independent_v5.py")
    assert "python scripts/verify_hsd_wnba_schedule_independent_v5.py" in workflow
    assert "independent_schedule_verification_v5.json" in workflow
    assert "v5.2-multi-source-wnba-schedule-verification" in script
    assert "stats.wnba.com" in script
    assert "espn_wnba_public_scoreboard_verify" in script
    assert "verification_inconclusive" in script


def test_multisport_review_modules_are_wired_and_review_only() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    script = read("scripts/generate_hsd_multisport_results_modules_v5.py")
    lite = read("generate_hsd_pipeline_review_lite_v1.py")
    assert "python scripts/generate_hsd_multisport_results_modules_v5.py" in workflow
    assert "v5.0-multisport-review-first" in script
    assert "review_only" in script
    assert "nwsl_soccer" in script
    assert "tennis_wta" in script
    assert "lpga_golf" in script
    assert "hsd-pipeline-review-lite-v3.8.0-results-v5-multisport-review" in lite


def test_game_intelligence_board_is_review_only_and_source_backed() -> None:
    module = load_results_desk()
    event = {
        "event_uid": "event_1",
        "canonical_key": "basketball|2026-06-24|indiana fever|new york liberty",
        "selected_source": "espn_wnba_public",
        "source_count": 1,
        "sport_norm": "basketball",
        "league_norm": "WNBA",
        "gender_scope": "women",
        "scheduled_date_local": "2026-06-24",
        "home_team_display": "New York Liberty",
        "away_team_display": "Indiana Fever",
        "final_score_display": "Indiana Fever 88 - New York Liberty 84",
        "status_norm": "final",
        "home_score": "84",
        "away_score": "88",
        "include_in_graphics": True,
        "manual_review": False,
        "score_conflict": False,
        "confidence": 0.92,
        "confidence_reason_json": '{"base_source":"espn_wnba_public","final_confidence":0.92,"adjustments":[["final_state",0.08]]}',
        "source_url": "https://www.espn.com/wnba/game/_/gameId/401",
        "box_score_top_performers": "",
    }
    upcoming_event = {
        **event,
        "event_uid": "event_2",
        "canonical_key": "basketball|2026-06-25|atlanta dream|chicago sky",
        "scheduled_date_local": "2026-06-25",
        "home_team_display": "Chicago Sky",
        "away_team_display": "Atlanta Dream",
        "final_score_display": "Atlanta Dream at Chicago Sky",
        "status_norm": module.normalize_status("Sat, June 27th at 8:00 PM EDT"),
        "home_score": "",
        "away_score": "",
        "include_in_graphics": False,
        "confidence": 0.84,
        "source_url": "https://www.espn.com/wnba/game/_/gameId/402",
        "box_score_top_performers": "",
    }
    live_event = {
        **upcoming_event,
        "event_uid": "event_3",
        "canonical_key": "basketball|2026-06-25|connecticut sun|washington mystics",
        "home_team_display": "Connecticut Sun",
        "away_team_display": "Washington Mystics",
        "status_norm": "live",
        "home_score": "N/A",
        "away_score": "88",
        "source_url": "https://www.espn.com/wnba/game/_/gameId/403",
    }
    capped_event = {
        **event,
        "event_uid": "event_4",
        "canonical_key": "basketball|2026-06-25|dallas wings|las vegas aces",
        "home_team_display": "Las Vegas Aces",
        "away_team_display": "Dallas Wings",
        "box_score_audit_status": "not_audited_sample_cap",
        "source_url": "https://www.espn.com/wnba/game/_/gameId/404",
    }
    observations = [
        {
            "canonical_key": event["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-24T12:00:00+00:00",
        },
        {
            "canonical_key": upcoming_event["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-25T12:00:00+00:00",
        },
        {
            "canonical_key": live_event["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-25T13:00:00+00:00",
        },
        {
            "canonical_key": capped_event["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-25T14:00:00+00:00",
        }
    ]
    expected_rows = [
        {
            "date": "2026-06-24",
            "league": "WNBA",
            "sport": "basketball",
            "home_team": "Chicago Sky",
            "away_team": "Atlanta Dream",
            "expected_key": "basketball|2026-06-24|atlanta dream|chicago sky",
            "source_name": "manual_reviewed_expected_seed",
            "source_url": "manual_expected_games.csv",
            "matched": "No",
            "reason": "missing_from_free_sources_or_outside_window",
        },
        {
            "date": "2099-06-24",
            "league": "WNBA",
            "sport": "basketball",
            "home_team": "Seattle Storm",
            "away_team": "Phoenix Mercury",
            "expected_key": "basketball|2099-06-24|phoenix mercury|seattle storm",
            "source_name": "manual_reviewed_expected_seed",
            "source_url": "manual_expected_games.csv",
            "matched": "No",
            "reason": "missing_from_free_sources_or_outside_window",
        }
    ]

    rows = module.game_intelligence_rows([event, upcoming_event, live_event, capped_event], observations, expected_rows)
    by_type = {row["row_type"]: row for row in rows}

    recap = by_type["recap_candidate"]
    assert recap["review_only"] == "Yes"
    assert recap["publish_action"] == "none_artifact_only"
    assert recap["approval_state_change"] == "none"
    assert recap["source_domain"] == "www.espn.com"
    assert recap["retrieved_at_utc"] == "2026-06-24T12:00:00+00:00"
    assert recap["stats_context_status"] == "missing_free_box_score_context"
    assert "box_score_or_top_performer_context" in recap["missing_evidence"]
    assert recap["manual_review_status"] == "review_only_recap_candidate"

    missing = by_type["missing_expected_game"]
    assert missing["attention_bucket"] == "missing_source_evidence"
    assert missing["manual_review_status"] == "manual_review_required_missing_source_evidence"
    assert missing["source_confidence"] == "0.00"

    upcoming = by_type["upcoming_game"]
    assert upcoming["status"] == "scheduled"
    assert upcoming["stats_context_status"] == "not_expected_pre_game"

    live = by_type["live_game"]
    assert live["attention_bucket"] == "live_watch"
    assert live["row_type"] == "live_game"

    capped = [row for row in rows if row["row_id"] == "event_4"][0]
    assert capped["stats_context_status"] == "box_score_not_checked_sample_cap"
    assert "box_score_audit_limit" in capped["missing_evidence"]

    future_missing = [row for row in rows if row["game_date"] == "2099-06-24"][0]
    assert "scheduled_game_observation" in future_missing["missing_evidence"]
    assert "final_score" not in future_missing["missing_evidence"]

    summary = module.game_intelligence_summary(rows)
    assert summary["final_results"] == 2
    assert summary["recap_candidates"] == 2
    assert summary["upcoming_games"] == 1
    assert summary["live_games"] == 1

    report = module.game_intelligence_report_md(module.game_intelligence_summary(rows * 41), rows * 41)
    assert "Showing first 80 of" in report


def test_game_intelligence_board_artifacts_are_wired_for_operator_visibility() -> None:
    results = read("generate_hsd_results_desk_v5.py")
    command_center = read("generate_hsd_operator_command_center_v2.py")
    lite = read("generate_hsd_pipeline_review_lite_v1.py")
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")

    for artifact in [
        "game_intelligence_board_v1.csv",
        "game_intelligence_board_v1.md",
        "game_intelligence_board_v1.json",
        "stats_evidence_gap_board_v1.csv",
        "stats_evidence_gap_board_v1.md",
        "stats_evidence_gap_board_v1.json",
        "stats_confirmation_intake_v1.csv",
        "game_fact_confirmation_status_v1.csv",
        "game_fact_confirmation_status_v1.md",
        "game_fact_confirmation_status_v1.json",
        "final_score_stat_proof_v1.csv",
        "final_score_stat_proof_v1.md",
        "final_score_stat_proof_v1.json",
        "final_score_stat_proof_confirmation_intake_v1.csv",
        "final_score_stat_proof_review_walkthrough_v1.md",
        "final_score_stat_proof_review_order_v1.csv",
        "athlete_render_candidate_board_v1.csv",
        "athlete_render_candidate_board_v1.md",
        "athlete_render_candidate_board_v1.json",
        "story_proof_card_v1.csv",
        "story_proof_card_v1.md",
        "story_proof_card_v1.json",
    ]:
        assert artifact in results
        assert artifact in command_center
        assert artifact in lite
        assert artifact in workflow


def test_game_fact_confirmation_status_board_points_to_exact_review_paths() -> None:
    module = load_results_desk()
    intelligence_rows = [
        {
            "row_id": "event_confirmed",
            "row_type": "recap_candidate",
            "attention_bucket": "recap_candidate",
            "game_date": "2026-06-24",
            "league": "WNBA",
            "sport": "basketball",
            "home_team": "New York Liberty",
            "away_team": "Indiana Fever",
            "status": "final",
            "final_score": "Indiana Fever 88 - New York Liberty 84",
            "recap_candidate": "Yes",
            "source_confidence": "0.92",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/401",
            "source_domain": "www.espn.com",
            "missing_evidence": "none",
            "retrieved_at_utc": "2026-06-24T12:00:00+00:00",
        },
        {
            "row_id": "event_scheduled",
            "row_type": "upcoming_game",
            "attention_bucket": "upcoming_game",
            "game_date": "2026-06-25",
            "league": "WNBA",
            "sport": "basketball",
            "home_team": "Chicago Sky",
            "away_team": "Atlanta Dream",
            "status": "scheduled",
            "final_score": "Atlanta Dream at Chicago Sky",
            "recap_candidate": "No",
            "source_confidence": "0.84",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/402",
            "source_domain": "www.espn.com",
            "missing_evidence": "none",
        },
        {
            "row_id": "expected_missing",
            "row_type": "missing_expected_game",
            "attention_bucket": "missing_source_evidence",
            "game_date": "2026-06-24",
            "league": "WNBA",
            "sport": "basketball",
            "home_team": "Las Vegas Aces",
            "away_team": "Dallas Wings",
            "status": "missing_from_free_sources_or_outside_window",
            "final_score": "",
            "recap_candidate": "No",
            "source_confidence": "0.00",
            "source_url": "manual_expected_games.csv",
            "source_domain": "",
            "missing_evidence": "free_source_observation_match; final_score; stats_context",
        },
    ]
    stats_rows = [
        {
            "event_uid": "event_confirmed",
            "stats_evidence_status": "confirmed_free_public_box_score",
            "manual_confirmation_needed": "No",
            "confirmation_source_url": "https://www.espn.com/wnba/game/_/gameId/401",
        }
    ]

    rows = module.game_fact_confirmation_status_rows(intelligence_rows, stats_rows)
    by_id = {row["event_uid"]: row for row in rows}

    confirmed = by_id["event_confirmed"]
    assert confirmed["schedule_fact_status"] == "schedule_source_confirmed_free_public_operator_verify"
    assert confirmed["result_fact_status"] == "final_score_source_confirmed_free_public_operator_verify"
    assert confirmed["stats_fact_status"] == "stats_source_confirmed_free_public_operator_verify"
    assert confirmed["overall_confirmation_status"] == "source_confirmed_operator_verify_before_use"
    assert confirmed["missing_confirmation"] == "none"
    assert "game_intelligence_board_v1.csv row_id=event_confirmed" in confirmed["exact_next_file_or_intake"]
    assert "stats_evidence_gap_board_v1.csv event_uid=event_confirmed" in confirmed["exact_next_file_or_intake"]
    assert confirmed["review_only"] == "Yes"
    assert confirmed["approval_state_change"] == "none"
    assert confirmed["publish_action"] == "none_artifact_only"

    scheduled = by_id["event_scheduled"]
    assert scheduled["result_fact_status"] == "not_final_result_pending"
    assert scheduled["stats_fact_status"] == "not_final_stats_optional"
    assert scheduled["overall_confirmation_status"] == "schedule_confirmed_result_pending"

    missing = by_id["expected_missing"]
    assert missing["overall_confirmation_status"] == "manual_verification_required"
    assert "schedule_source" in missing["missing_confirmation"]
    assert "missing_games_alert_v5.csv" in missing["exact_next_file_or_intake"]
    assert missing["manual_review_required"] == "Yes"

    summary = module.game_fact_confirmation_status_summary(rows)
    assert summary["rows"] == 3
    assert summary["manual_verification_required"] == 1
    report = module.game_fact_confirmation_status_report_md(summary, rows)
    assert "Rows Needing Manual Verification" in report
    assert "No paid APIs" in report


def test_final_score_stat_proof_splits_named_player_stat_lines() -> None:
    module = load_results_desk()
    stats_rows = [
        {
            "event_uid": "event_confirmed",
            "game_date": "2026-06-24",
            "league": "WNBA",
            "matchup": "Indiana Fever at New York Liberty",
            "status": "final",
            "recap_candidate": "Yes",
            "final_score": "Indiana Fever 88 - New York Liberty 84",
            "stats_evidence_status": "confirmed_free_public_box_score",
            "top_performers": "Player One (Indiana Fever): PTS 24, REB 8 | Player Two (New York Liberty): PTS 20, AST 7",
            "confirmation_source_url": "https://www.espn.com/wnba/game/_/gameId/401",
            "confirmation_source_domain": "www.espn.com",
            "source_confidence": "0.92",
        },
        {
            "event_uid": "event_missing",
            "game_date": "2026-06-24",
            "league": "WNBA",
            "matchup": "Dallas Wings at Las Vegas Aces",
            "status": "final",
            "recap_candidate": "Yes",
            "final_score": "Dallas Wings 72 - Las Vegas Aces 80",
            "stats_evidence_status": "missing_box_score_or_top_performer_context",
            "top_performers": "",
            "confirmation_source_url": "https://www.espn.com/wnba/game/_/gameId/402",
            "confirmation_source_domain": "www.espn.com",
            "source_confidence": "0.84",
        },
    ]

    rows = module.final_score_stat_proof_rows(stats_rows)
    confirmed_rows = [row for row in rows if row["event_uid"] == "event_confirmed"]
    missing_rows = [row for row in rows if row["event_uid"] == "event_missing"]

    assert len(confirmed_rows) == 3
    score = [row for row in confirmed_rows if row["fact_type"] == "final_score"][0]
    assert score["proof_status"] == "score_source_backed_operator_verify"
    assert score["manual_box_score_confirmation_needed"] == "No"

    stat_rows = [row for row in confirmed_rows if row["fact_type"] == "named_player_stat_line"]
    assert {row["named_player"] for row in stat_rows} == {"Player One", "Player Two"}
    assert {row["player_team"] for row in stat_rows} == {"Indiana Fever", "New York Liberty"}
    assert all(row["proof_status"] == "named_stat_line_source_backed_operator_verify" for row in stat_rows)
    assert all("stats_evidence_gap_board_v1.csv event_uid=event_confirmed" in row["exact_next_file_or_intake"] for row in stat_rows)
    assert all(row["operator_note_path"].startswith("final_score_stat_proof_confirmation_intake_v1.csv proof_id=") for row in confirmed_rows)
    assert all(row["review_only"] == "Yes" for row in rows)
    assert all(row["approval_state_change"] == "none" for row in rows)
    assert all(row["publish_action"] == "none_artifact_only" for row in rows)

    assert len(missing_rows) == 2
    missing_stat = [row for row in missing_rows if row["fact_type"] == "named_player_stat_line"][0]
    assert missing_stat["proof_status"] == "named_stat_line_missing_manual_box_score_confirmation_required"
    assert missing_stat["manual_box_score_confirmation_needed"] == "Yes"
    assert "stats_confirmation_intake_v1.csv" in missing_stat["exact_next_file_or_intake"]

    confirmation_rows = module.final_score_stat_proof_confirmation_rows(rows)
    assert len(confirmation_rows) == len(rows)
    by_proof = {row["proof_id"]: row for row in confirmation_rows}
    assert set(by_proof) == {row["proof_id"] for row in rows}
    assert all(row["operator_checked_source_url"] == "" for row in confirmation_rows)
    assert all(row["operator_confirmation_status"] == "" for row in confirmation_rows)
    assert all(row["operator_notes"] == "" for row in confirmation_rows)
    assert all(row["review_only"] == "Yes" for row in confirmation_rows)
    assert all(row["approval_state_change"] == "none" for row in confirmation_rows)
    assert all(row["publish_action"] == "none_artifact_only" for row in confirmation_rows)
    assert "Verify final score" in by_proof[score["proof_id"]]["operator_review_task"]
    assert "Verify named player" in by_proof[stat_rows[0]["proof_id"]]["operator_review_task"]

    review_rows = module.final_score_stat_proof_review_order_rows(rows)
    assert len(review_rows) == len(rows)
    assert review_rows[0]["review_phase"] == "1_manual_box_score_gap"
    missing_review = [row for row in review_rows if row["event_uid"] == "event_missing" and row["fact_type"] == "named_player_stat_line"][0]
    player_one_review = [row for row in review_rows if row["named_player"] == "Player One"][0]
    score_review = [row for row in review_rows if row["event_uid"] == "event_confirmed" and row["fact_type"] == "final_score"][0]
    assert missing_review["source_confirmation_cue"] == "free_public_box_score_stat_source_needed_manual_check"
    assert player_one_review["player_team"] == "Indiana Fever"
    assert player_one_review["stat_line"] == "PTS 24, REB 8"
    assert player_one_review["source_confirmation_cue"] == "free_public_box_score_stat_source_present_operator_verify"
    assert score_review["source_confirmation_cue"] == "free_public_final_score_source_present_operator_verify"
    assert all(row["proof_row_to_open"].startswith("final_score_stat_proof_v1.csv proof_id=") for row in review_rows)
    assert all(row["intake_row_to_record"].startswith("final_score_stat_proof_confirmation_intake_v1.csv proof_id=") for row in review_rows)
    assert all(row["story_proof_card_row_to_open"].startswith("story_proof_card_v1.csv event_id=") for row in review_rows)
    assert all("operator_confirmation_status" in row["operator_decision_fields"] for row in review_rows)
    assert all(row["review_only"] == "Yes" for row in review_rows)
    assert all(row["approval_state_change"] == "none" for row in review_rows)
    assert all(row["publish_action"] == "none_artifact_only" for row in review_rows)
    walkthrough = module.final_score_stat_proof_review_walkthrough_md(review_rows)
    assert "Review Order" in walkthrough
    assert "final_score_stat_proof_confirmation_intake_v1.csv" in walkthrough
    assert "does not approve anything" in walkthrough

    catalog_rows = [
        {
            "athlete_id": "indiana_fever_player_one",
            "athlete_name": "Player One",
            "team_id": "indiana_fever",
            "asset_kind": "headshot",
            "local_asset_path": "assets/leagues/wnba/athletes/indiana_fever_player_one/headshot.png",
            "file_exists": "true",
            "approved_marker_path": "assets/leagues/wnba/athletes/indiana_fever_player_one/headshot.png.approved",
            "approved_marker_exists": "true",
            "source_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/1.png",
        },
        {
            "athlete_id": "new_york_liberty_player_two",
            "athlete_name": "Player Two",
            "team_id": "new_york_liberty",
            "asset_kind": "headshot",
            "local_asset_path": "assets/leagues/wnba/athletes/new_york_liberty_player_two/headshot.png",
            "file_exists": "false",
            "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_player_two/headshot.png.approved",
            "approved_marker_exists": "false",
            "source_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/2.png",
        },
    ]
    candidate_rows = module.athlete_render_candidate_rows(rows, review_rows, catalog_rows, check_paths=False)
    assert len(candidate_rows) == 2
    ready = candidate_rows[0]
    blocked = candidate_rows[1]
    assert ready["candidate_status"] == "athlete_render_candidate_ready_for_manual_review"
    assert ready["athlete_name"] == "Player One"
    assert ready["local_athlete_image_path"].endswith("headshot.png")
    assert ready["proof_row_to_open"].startswith("final_score_stat_proof_v1.csv proof_id=")
    assert ready["intake_row_to_record"].startswith("final_score_stat_proof_confirmation_intake_v1.csv proof_id=")
    assert "athlete_image=" in ready["exact_renderer_handoff_fields"]
    assert ready["story_proof_card_row_to_open"].startswith("story_proof_card_v1.csv event_id=event_confirmed")
    assert ready["operator_checked_source_url"] == ""
    assert ready["operator_asset_review_notes"] == ""
    assert ready["review_only"] == "Yes"
    assert ready["approval_state_change"] == "none"
    assert ready["publish_action"] == "none_artifact_only"
    assert ready["auto_approval"] == "No"
    assert ready["asset_downloads"] == "No"
    assert ready["publish_ready"] == "No"
    assert blocked["candidate_status"] == "athlete_render_candidate_blocked_manual_review_required"
    assert "local_athlete_image_file_missing" in blocked["missing_blockers"]
    candidate_summary = module.athlete_render_candidate_summary(candidate_rows)
    assert candidate_summary["ready_for_manual_review"] == 1
    candidate_report = module.athlete_render_candidate_report_md(candidate_summary, candidate_rows)
    assert "Athlete Render Candidate Board" in candidate_report
    assert "No paid APIs" in candidate_report

    fact_rows = [
        {
            "event_uid": "event_confirmed",
            "game_date": "2026-06-24",
            "matchup": "Indiana Fever at New York Liberty",
            "schedule_fact_status": "schedule_source_confirmed_free_public_operator_verify",
            "result_fact_status": "final_score_source_confirmed_free_public_operator_verify",
            "stats_fact_status": "stats_source_confirmed_free_public_operator_verify",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/401",
            "source_domain": "www.espn.com",
            "stats_source_url": "https://www.espn.com/wnba/game/_/gameId/401",
        },
        {
            "event_uid": "event_missing",
            "game_date": "2026-06-24",
            "matchup": "Dallas Wings at Las Vegas Aces",
            "schedule_fact_status": "schedule_source_confirmed_free_public_operator_verify",
            "result_fact_status": "final_score_source_confirmed_free_public_operator_verify",
            "stats_fact_status": "missing_box_score_or_top_performer_context",
            "source_url": "https://www.espn.com/wnba/game/_/gameId/402",
            "source_domain": "www.espn.com",
            "stats_source_url": "",
        },
    ]
    proof_cards = module.story_proof_card_rows(fact_rows, rows, review_rows, candidate_rows)
    assert len(proof_cards) == 2
    proof_card = proof_cards[0]
    assert proof_card["event_id"] == "event_confirmed"
    assert proof_card["proof_status"] == "proof_card_ready_for_manual_review"
    assert proof_card["renderability_state"] == "athlete_led_manual_render_candidate"
    assert proof_card["copy_unlock_level"] == "score_and_named_stat_copy_review_ready"
    assert proof_card["asset_unlock_state"] == "approved_local_athlete_photo_available"
    assert proof_card["athlete_name"] == "Player One"
    assert proof_card["named_stat_proof"] == "PTS 24, REB 8"
    assert proof_card["official_source_url"] == "https://www.espn.com/wnba/game/_/gameId/401"
    assert proof_card["named_stat_proof_row"].startswith("final_score_stat_proof_v1.csv proof_id=")
    assert proof_card["final_score_review_order_row"].startswith("final_score_stat_proof_review_order_v1.csv review_order=")
    assert proof_card["named_stat_review_order_row"].startswith("final_score_stat_proof_review_order_v1.csv review_order=")
    assert proof_card["source_confirmation_cue"] == "free_public_box_score_stat_source_present_operator_verify"
    assert proof_card["manual_intake_path"].startswith("final_score_stat_proof_confirmation_intake_v1.csv proof_id=")
    assert proof_card["operator_checked_source_url"] == ""
    assert proof_card["operator_notes"] == ""
    assert proof_card["review_only"] == "Yes"
    assert proof_card["approval_state_change"] == "none"
    assert proof_card["auto_approval"] == "No"
    assert proof_card["publish_action"] == "none_artifact_only"
    assert proof_card["publish_ready"] == "No"
    assert proof_card["asset_downloads"] == "No"
    assert "download_approval_is_not_asset_approval" in proof_card["asset_download_policy"]
    assert proof_card["asset_approval_state_change"] == "none"
    assert proof_card["source_enablement"] == "none_existing_local_artifacts_only"
    blocked_card = [card for card in proof_cards if card["event_id"] == "event_missing"][0]
    assert blocked_card["proof_status"] == "proof_card_needs_human_confirmation"
    assert "athlete_render_candidate_missing" in blocked_card["missing_blockers"]
    proof_summary = module.story_proof_card_summary(proof_cards)
    assert proof_summary["athlete_led_manual_render_candidates"] == 1
    proof_report = module.story_proof_card_report_md(proof_summary, proof_cards)
    assert "Story Proof Card" in proof_report
    assert "automatic downloads" in proof_report

    summary = module.final_score_stat_proof_summary(rows)
    assert summary["final_score_rows"] == 2
    assert summary["named_player_stat_rows"] == 3
    assert summary["manual_box_score_confirmation_needed"] == 1
    report = module.final_score_stat_proof_report_md(summary, rows)
    assert "Manual Box-Score Confirmation Needed" in report
    assert "No paid APIs" in report


def test_stats_evidence_gap_board_and_confirmation_intake_are_review_only() -> None:
    module = load_results_desk()
    base = {
        "scheduled_date_local": "2026-06-24",
        "league_norm": "WNBA",
        "sport_norm": "basketball",
        "status_norm": "final",
        "home_team_display": "New York Liberty",
        "away_team_display": "Indiana Fever",
        "final_score_display": "Indiana Fever 88 - New York Liberty 84",
        "include_in_graphics": True,
        "selected_source": "espn_wnba_public",
        "confidence": 0.92,
        "source_url": "https://www.espn.com/wnba/game/_/gameId/401",
    }
    confirmed = {
        **base,
        "event_uid": "event_confirmed",
        "canonical_key": "basketball|2026-06-24|indiana fever|new york liberty",
        "box_score_audit_status": "found",
        "box_score_top_performers": "Player One (Indiana Fever): PTS 24, REB 8",
    }
    capped = {
        **base,
        "event_uid": "event_capped",
        "canonical_key": "basketball|2026-06-24|atlanta dream|chicago sky",
        "home_team_display": "Chicago Sky",
        "away_team_display": "Atlanta Dream",
        "source_url": "https://www.espn.com/wnba/game/_/gameId/402",
        "box_score_audit_status": "not_audited_sample_cap",
        "box_score_top_performers": "",
    }
    missing = {
        **base,
        "event_uid": "event_missing",
        "canonical_key": "basketball|2026-06-24|dallas wings|las vegas aces",
        "home_team_display": "Las Vegas Aces",
        "away_team_display": "Dallas Wings",
        "source_url": "https://www.espn.com/wnba/game/_/gameId/403",
        "box_score_audit_status": "summary_found_no_performers",
        "box_score_top_performers": "",
    }
    scheduled = {
        **base,
        "event_uid": "event_scheduled",
        "canonical_key": "basketball|2026-06-25|phoenix mercury|seattle storm",
        "status_norm": "scheduled",
        "include_in_graphics": False,
        "box_score_top_performers": "",
    }
    observations = [
        {
            "canonical_key": confirmed["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-24T12:00:00+00:00",
        },
        {
            "canonical_key": capped["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-24T13:00:00+00:00",
        },
        {
            "canonical_key": missing["canonical_key"],
            "source_name": "espn_wnba_public",
            "source_priority": "95",
            "fetched_at_utc": "2026-06-24T14:00:00+00:00",
        },
    ]

    rows, intake = module.stats_evidence_gap_rows([confirmed, capped, missing, scheduled], observations)
    by_id = {row["event_uid"]: row for row in rows}

    assert set(by_id) == {"event_confirmed", "event_capped", "event_missing"}
    assert by_id["event_confirmed"]["stats_evidence_status"] == "confirmed_free_public_box_score"
    assert by_id["event_confirmed"]["manual_confirmation_needed"] == "No"
    assert by_id["event_confirmed"]["top_performers"] == "Player One (Indiana Fever): PTS 24, REB 8"
    assert by_id["event_confirmed"]["review_only"] == "Yes"
    assert by_id["event_confirmed"]["approval_state_change"] == "none"
    assert by_id["event_confirmed"]["publish_action"] == "none_artifact_only"

    assert by_id["event_capped"]["stats_evidence_status"] == "box_score_audit_capped"
    assert by_id["event_capped"]["manual_confirmation_needed"] == "Yes"
    assert by_id["event_capped"]["missing_stat_evidence"] == "box_score_audit_not_run_for_this_row"
    assert by_id["event_missing"]["stats_evidence_status"] == "box_score_summary_no_performers"
    assert by_id["event_missing"]["manual_confirmation_needed"] == "Yes"
    assert by_id["event_missing"]["missing_stat_evidence"] == "top_performer_context"

    assert [row["event_uid"] for row in intake] == ["event_capped", "event_missing"]
    assert all(row["operator_checked_url"] == "" for row in intake)
    assert all(row["operator_confirmation_status"] == "" for row in intake)
    assert all(row["review_only"] == "Yes" for row in intake)

    summary = module.stats_evidence_gap_summary(rows, intake)
    assert summary["rows"] == 3
    assert summary["confirmed_free_public_box_score"] == 1
    assert summary["manual_confirmation_rows"] == 2
    report = module.stats_evidence_gap_report_md(summary, rows, intake)
    assert "Manual Confirmation Needed" in report
    assert "No paid APIs" in report


def test_template_law_and_top_priority_specs_exist() -> None:
    required_paths = [
        "docs/HSD_GRAPHICS_LAW_V1.md",
        "docs/HSD_GRAPHICS_LAW_V1_LPGA_GOLF.md",
        "docs/HSD_REALITY_CHECK_PROMPTS.md",
        "config/graphics/brand_policy_v1.json",
        "config/graphics/template_registry_v1.json",
        "config/graphics/template_render_mapping_v1.json",
        "scripts/generate_hsd_graphics_template_factory_v1.py",
        "scripts/generate_hsd_template_render_map_v1.py",
        "scripts/generate_hsd_template_renderer_v2.py",
        "scripts/generate_hsd_template_renderer_v2_5.py",
        "config/graphics/templates/game_recap_final_score_a_v1.json",
        "config/graphics/templates/game_recap_final_score_b_v1.json",
        "config/graphics/templates/game_recap_final_score_c_story_v1.json",
        "config/graphics/templates/tonight_in_the_w_a_v1.json",
        "config/graphics/templates/last_night_in_the_w_a_v1.json",
        "config/graphics/templates/last_night_in_the_w_b_story_v1.json",
        "config/graphics/templates/last_night_in_the_w_c_carousel_v1.json",
        "config/graphics/templates/daily_debrief_a_v1.json",
        "config/graphics/templates/daily_debrief_b_summary_v1.json",
        "config/graphics/templates/daily_debrief_c_story_v1.json",
        "config/graphics/templates/womens_soccer_match_story_a_v1.json",
        "config/graphics/templates/womens_soccer_match_story_b_v1.json",
        "config/graphics/templates/womens_soccer_match_story_c_story_v1.json",
        "config/graphics/templates/tennis_wta_result_a_v1.json",
        "config/graphics/templates/tennis_wta_result_b_v1.json",
        "config/graphics/templates/tennis_wta_result_c_story_v1.json",
        "config/graphics/templates/lpga_golf_winner_leaderboard_a_v1.json",
        "config/graphics/templates/lpga_golf_winner_leaderboard_b_v1.json",
        "config/graphics/templates/lpga_golf_winner_leaderboard_c_story_v1.json",
    ]
    for path in required_paths:
        assert Path(path).exists(), path


def test_template_renderer_v25_is_active_and_review_only() -> None:
    map_script = read("scripts/generate_hsd_template_render_map_v1.py")
    renderer = read("scripts/generate_hsd_template_renderer_v2_5.py")
    requirements = read("requirements.txt")
    assert "v1.3-hsd-template-render-map-v2-5-handoff" in map_script
    assert "scripts/generate_hsd_template_renderer_v2_5.py" in map_script
    assert "v2.5-hsd-quality-tonight-logo-integrity-review-only" in renderer
    assert "Template Renderer v2.5 compile proof" in renderer
    assert "verified registry logo loaded" in renderer
    assert "fallback_logo_warnings" in renderer
    assert "logo_panel" in renderer
    assert "WATCH POINT" in renderer
    assert "Human review required before publishing" in renderer
    assert "CairoSVG" in requirements


def test_quality_renderer_packaging_still_wired() -> None:
    workflow = read(".github/workflows/hsd-v3-repo-state-sanity.yml")
    renderer = read("scripts/generate_hsd_quality_graphics_renderer_v1.py")
    zipper = read("scripts/package_hsd_quality_graphics_v1.py")
    assert "python scripts/generate_hsd_quality_graphics_renderer_v1.py" in workflow
    assert "python scripts/package_hsd_quality_graphics_v1.py" in workflow
    assert "outputs/latest/HSD_QUALITY_GRAPHICS/**" in workflow
    assert "v1.0-hsd-quality-graphics-renderer" in renderer
    assert "v1.0-package-hsd-quality-graphics" in zipper
