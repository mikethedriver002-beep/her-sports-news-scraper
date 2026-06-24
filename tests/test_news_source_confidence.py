from __future__ import annotations

import importlib.util
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
