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
    candidate["graphics_headline"] = "Breaking: Liberty announce star guard injury"
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
    news_manifest = run_dir / "news_sync_manifest.json"
    assert queue.exists()
    assert report.exists()
    assert signal_manifest.exists()
    assert confirmation_csv.exists()
    assert confirmation_md.exists()
    rows = list(csv.DictReader(queue.open(newline="", encoding="utf-8")))
    confirmation_rows = list(csv.DictReader(confirmation_csv.open(newline="", encoding="utf-8")))
    assert rows
    assert confirmation_rows
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
    assert any(row["headline"] == "Breaking: Liberty announce star guard injury update" for row in rows)
    signal_payload = json.loads(signal_manifest.read_text(encoding="utf-8"))
    news_payload = json.loads(news_manifest.read_text(encoding="utf-8"))
    assert signal_payload["review_only"] is True
    assert signal_payload["publish_ready"] is False
    assert signal_payload["counts"]["rows"] == len(rows)
    assert signal_payload["counts"]["confirmation_intake_rows"] == len(confirmation_rows)
    assert "breaking_public_signal_queue.csv" in news_payload["outputs"]
    assert "breaking_public_signal_confirmation_intake.csv" in news_payload["outputs"]
    assert news_payload["counts"]["breaking_public_signal_rows"] == len(rows)
    assert news_payload["counts"]["breaking_public_signal_review_only"] == len(rows)
    assert news_payload["counts"]["breaking_confirmation_intake_rows"] == len(confirmation_rows)
