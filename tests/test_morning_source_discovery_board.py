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
                "source_id": "reddit_womens_sports_discovery",
                "source_type": "reddit_public_json",
                "source_tier": "community",
                "source_trust_band": "yellow",
                "title": "Fan community lead",
                "source_url": "https://www.reddit.com/r/wnba/comments/example",
                "summary": "Interesting lead.",
                "publish_eligible": "No",
                "reason": "discovery only; needs green confirmation",
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
    assert promotions["Liberty beat Aces final score graphic"] == "studio_brief"
    assert promotions["WNBA announces a new broadcast partnership"] == "news_packet"
    assert promotions["Team site home page"] == "monitor_only"
    assert promotions["Scan team_social_manual_only"] == "monitor_only"
    assert {"manual_story_candidate", "studio_brief", "news_packet"} <= promotion_targets
    assert "monitor_only" not in promotion_targets
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
