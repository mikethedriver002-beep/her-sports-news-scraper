from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_morning_source_discovery_board_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_morning_source_discovery_board_v1_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_morning_source_discovery_board_merges_review_safe_lanes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "source_registry.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "wnba_official_news",
                        "source_type": "official_site",
                        "enabled": True,
                        "tier": "official",
                        "trust_band": "green",
                        "sport_league": "WNBA",
                        "urls": ["https://www.wnba.com/news"],
                        "publish_policy": "green_official",
                        "automation_status": "manual_review_or_fetch_later",
                    },
                    {
                        "source_id": "ap_womens_sports_wire",
                        "source_type": "wire",
                        "enabled": True,
                        "tier": "wire",
                        "trust_band": "green",
                        "sport_league": "all",
                        "urls": ["https://apnews.com/hub/womens-sports"],
                        "publish_policy": "green_wire",
                        "automation_status": "manual_review_or_fetch_later",
                    },
                    {
                        "source_id": "team_social_manual_only",
                        "source_type": "social_manual_only",
                        "enabled": True,
                        "tier": "social_manual",
                        "trust_band": "yellow_to_green_if_official_account_and_operator_verified",
                        "sport_league": "all",
                        "domains": ["instagram.com", "threads.net", "x.com"],
                        "publish_policy": "requires official confirmation",
                        "automation_status": "manual_only",
                    },
                    {
                        "source_id": "private_login_paywall_scraping",
                        "source_type": "prohibited",
                        "enabled": False,
                        "tier": "red",
                        "trust_band": "red",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    write_csv(
        run_dir / "story_candidates_manual.csv",
        [
            {
                "input_type": "url",
                "source_url": "https://www.wnba.com/news/example",
                "title": "Liberty beat Aces final score graphic",
                "summary": "Manual official lead with a visual result angle.",
                "league": "WNBA",
                "risk_tier": "green_official_or_primary",
                "source_trust_band": "green",
                "publish_eligible": "Yes",
                "reason": "manual story eligible",
                "evidence_urls_json": "[\"https://www.wnba.com/news/example\"]",
            }
        ],
    )
    write_csv(
        run_dir / "story_candidates_discovery.csv",
        [
            {
                "source_id": "wnba_official_news",
                "source_type": "official_site",
                "source_tier": "official",
                "source_trust_band": "green",
                "title": "Liberty announce roster move before Aces game",
                "source_url": "https://www.wnba.com/news/liberty-roster-move",
                "canonical_url": "https://www.wnba.com/news/liberty-roster-move",
                "summary": "The Liberty announced a roster move before facing the Aces.",
                "publish_eligible": "Yes",
                "reason": "official source",
                "evidence_title": "Official Liberty roster move before Aces matchup",
                "evidence_published_at": "2026-06-24T09:00:00+00:00",
                "evidence_description": "The Liberty announced a roster move before facing the Aces.",
                "evidence_preview": "Official Liberty roster move before Aces matchup | 2026-06-24 | The Liberty announced a roster move before facing the Aces.",
                "evidence_source": "article_metadata",
                "lead_score": "6",
                "freshness_date": "2026-06-24",
                "freshness_label": "today",
                "freshness_source": "article_metadata",
                "freshness_score": "36",
                "urgency_score": "12",
                "quality_score": "88",
                "quality_reason": "fixture",
                "promotion_hint": "news_packet",
                "review_next_step": "Review the official article before drafting.",
            },
            {
                "source_id": "ap_womens_sports_wire",
                "source_type": "wire",
                "source_tier": "wire",
                "source_trust_band": "green",
                "title": "AP: Liberty roster move ahead of Aces matchup",
                "source_url": "https://apnews.com/article/liberty-aces-roster-move",
                "canonical_url": "https://apnews.com/article/liberty-aces-roster-move",
                "summary": "The Liberty made a roster move ahead of the Aces matchup.",
                "publish_eligible": "Yes",
                "reason": "wire source",
                "evidence_title": "Liberty roster move ahead of Aces matchup",
                "evidence_published_at": "2026-06-24T09:30:00+00:00",
                "evidence_description": "The Liberty made a roster move ahead of the Aces matchup.",
                "evidence_preview": "Liberty roster move ahead of Aces matchup | 2026-06-24 | The Liberty made a roster move ahead of the Aces matchup.",
                "evidence_source": "article_metadata",
                "lead_score": "6",
                "freshness_date": "2026-06-24",
                "freshness_label": "today",
                "freshness_source": "article_metadata",
                "freshness_score": "36",
                "urgency_score": "12",
                "quality_score": "84",
                "quality_reason": "fixture",
                "promotion_hint": "news_packet",
                "review_next_step": "Review the wire article before drafting.",
            },
            {
                "source_id": "reddit_womens_sports_discovery",
                "source_type": "reddit_public_json",
                "source_tier": "community",
                "source_trust_band": "yellow",
                "title": "Fan community lead",
                "source_url": "https://www.reddit.com/r/wnba/comments/example",
                "canonical_url": "https://www.reddit.com/r/wnba/comments/example",
                "summary": "Interesting lead.",
                "publish_eligible": "No",
                "reason": "discovery only; needs green confirmation",
                "evidence_title": "",
                "evidence_published_at": "",
                "evidence_description": "",
                "evidence_preview": "",
                "evidence_source": "",
                "lead_score": "",
                "freshness_date": "",
                "freshness_label": "",
                "freshness_source": "",
                "freshness_score": "",
                "urgency_score": "",
                "quality_score": "",
                "quality_reason": "",
                "promotion_hint": "",
                "review_next_step": "",
            }
        ],
    )
    write_csv(
        run_dir / "news_source_observations.csv",
        [
            {
                "candidate_id": "cand-1",
                "source_id": "wnba",
                "source_name": "WNBA official",
                "source_type": "official_league",
                "url": "https://www.wnba.com/",
                "fetch_status": "ok",
                "title": "WNBA",
                "description": "Official source",
                "usable_context": "Yes",
                "context_signal": "WNBA announces a new broadcast partnership",
                "source_trust_band": "green",
                "publish_use": "publish_grade",
            },
            {
                "candidate_id": "cand-1",
                "source_id": "espn_wnba",
                "source_name": "ESPN WNBA",
                "source_type": "scoreboard_backup",
                "url": "https://www.espn.com/wnba/scoreboard",
                "fetch_status": "ok",
                "title": "ESPN WNBA",
                "description": "Scoreboard",
                "usable_context": "Yes",
                "context_signal": "Scoreboard cross-check",
                "source_trust_band": "green_cross_check",
                "publish_use": "cross_check",
            },
            {
                "candidate_id": "cand-2",
                "source_id": "team_site",
                "source_name": "Team official site",
                "source_type": "official_team",
                "url": "https://example.wnba.com/",
                "fetch_status": "ok",
                "title": "Team site",
                "description": "Official team homepage",
                "usable_context": "Yes",
                "context_signal": "Team site home page",
                "source_trust_band": "green",
                "publish_use": "",
            },
        ],
    )

    module = load_module()
    payload = module.build_payload()
    module.write_outputs(payload)

    lanes = {row["lane"] for row in payload["rows"]}
    postures = {row["title"]: row["publish_posture"] for row in payload["rows"]}
    promotions = {row["title"]: row["promotion_recommendation"] for row in payload["rows"]}
    promotion_targets = {row["promotion_recommendation"] for row in payload["promotion_recommendations"]}
    assert {"manual_lead", "official_free", "wire", "free_cross_check", "social_discovery"} <= lanes
    assert postures["Fan community lead"] == "discovery_only"
    assert promotions["Fan community lead"] == "manual_story_candidate"
    assert promotions["Liberty announce roster move before Aces game"] == "news_packet"
    assert promotions["Liberty beat Aces final score graphic"] == "studio_brief"
    assert promotions["WNBA announces a new broadcast partnership"] == "news_packet"
    assert promotions["Team site home page"] == "monitor_only"
    assert promotions["Scan team_social_manual_only"] == "monitor_only"
    assert {"manual_story_candidate", "studio_brief", "news_packet"} <= promotion_targets
    assert "monitor_only" not in promotion_targets
    official_row = next(row for row in payload["rows"] if row["title"] == "Liberty announce roster move before Aces game")
    wire_row = next(row for row in payload["rows"] if row["title"] == "AP: Liberty roster move ahead of Aces matchup")
    assert official_row["story_opportunity_id"] == wire_row["story_opportunity_id"]
    assert official_row["story_opportunity_size"] == "2"
    assert "wnba_official_news" in official_row["story_opportunity_sources"]
    assert "ap_womens_sports_wire" in official_row["story_opportunity_sources"]
    cluster_promotions = [
        row
        for row in payload["promotion_recommendations"]
        if row["story_opportunity_id"] == official_row["story_opportunity_id"]
    ]
    assert len(cluster_promotions) == 1
    assert cluster_promotions[0]["story_opportunity_size"] == "2"
    assert "Grouped 2 related official/wire discovery leads" in cluster_promotions[0]["promotion_reason"]
    assert payload["counts"]["story_opportunities"] >= 1
    assert payload["counts"]["grouped_story_opportunities"] == 1
    assert payload["policy"]["promotion_mode"] == "manual_recommendation_only"
    assert all(row["publish_posture"] != "auto_publish" for row in payload["rows"])
    assert payload["policy"]["auto_publish_allowed"] is False
    assert payload["policy"]["paid_apis_required"] is False
    assert (run_dir / "morning_source_discovery_board.csv").exists()
    assert (run_dir / "morning_source_discovery_board.md").exists()
    assert (run_dir / "morning_source_discovery_board.json").exists()
    assert (run_dir / "morning_lead_promotion_recommendations.csv").exists()
    assert (run_dir / "morning_lead_promotion_recommendations.md").exists()
    assert (run_dir / "morning_lead_promotion_recommendations.json").exists()
    assert not (tmp_path / "morning_source_discovery_board.csv").exists()
    assert not (tmp_path / "morning_lead_promotion_recommendations.csv").exists()
