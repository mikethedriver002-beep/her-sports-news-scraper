from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DISCOVERY_SCRIPT = REPO / "ingest_hsd_discovery_sources_v1.py"
MANUAL_SCRIPT = REPO / "normalize_hsd_manual_story_inbox_v1.py"
BOARD_SCRIPT = REPO / "generate_hsd_morning_source_discovery_board_v1.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code


class FakeRequests:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.calls: list[str] = []

    def get(self, url: str, **_: Any) -> FakeResponse:
        self.calls.append(url)
        return FakeResponse(self.pages.get(url, "<html></html>"))


def write_registry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
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
                        "domains": ["wnba.com"],
                    },
                    {
                        "source_id": "ap_womens_sports_wire",
                        "source_type": "wire",
                        "enabled": True,
                        "tier": "wire",
                        "trust_band": "green",
                        "sport_league": "all",
                        "urls": ["https://apnews.com/hub/womens-sports"],
                        "domains": ["apnews.com"],
                    },
                    {
                        "source_id": "team_social_manual_only",
                        "source_type": "social_manual_only",
                        "enabled": True,
                        "tier": "social_manual",
                        "trust_band": "yellow_to_green_if_official_account_and_operator_verified",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def test_discovery_ingest_captures_free_public_and_social_leads(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setenv("HSD_DISCOVERY_ENABLE_FETCH", "true")
    monkeypatch.setenv("HSD_DISCOVERY_NOW_UTC", "2026-06-24T12:00:00+00:00")
    write_registry(tmp_path / "config" / "source_registry.json")
    write_csv(
        tmp_path / "operator" / "inbox" / "social_rumor_inbox.csv",
        [
            {
                "platform": "Threads",
                "source_url": "https://threads.net/@team/post/123",
                "source_handle": "@team",
                "claim_text": "Team account hints at injury update",
                "sport": "basketball",
                "league": "WNBA",
                "teams_people": "New York Liberty",
                "operator_notes": "Needs official confirmation.",
            }
        ],
    )

    discovery = load_module(DISCOVERY_SCRIPT, "discovery_intake_test")
    fake_requests = FakeRequests(
        {
            "https://www.wnba.com/news": """
                <html><body>
                  <a href="/news/liberty-announce-roster-move">Liberty announce roster move before Aces game</a>
                  <a href="/news/all-time-wnba-record-leaders">All-time WNBA record leaders</a>
                  <a href="/schedule">Schedule</a>
                </body></html>
            """,
            "https://www.wnba.com/news/liberty-announce-roster-move": """
                <html><head>
                  <meta property="og:title" content="Official Liberty roster move before Aces matchup" />
                  <meta name="description" content="The Liberty announced a roster move before their Aces game." />
                  <meta property="article:published_time" content="2026-06-24T09:00:00Z" />
                </head><body>Roster move story.</body></html>
            """,
            "https://www.wnba.com/news/all-time-wnba-record-leaders": """
                <html><head>
                  <meta property="og:title" content="All-time WNBA record leaders" />
                  <meta name="description" content="A historical reference page for WNBA record leaders." />
                  <time datetime="2025-06-01T12:00:00Z">June 1, 2025</time>
                </head><body>Evergreen record leaders.</body></html>
            """,
            "https://apnews.com/hub/womens-sports": """
                <html><body>
                  <a href="/article/womens-basketball-final-score">Sky beat Storm in final score thriller</a>
                  <a href="/about">About AP</a>
                </body></html>
            """,
            "https://apnews.com/article/womens-basketball-final-score": """
                <html><head>
                  <script type="application/ld+json">{"@type":"NewsArticle","headline":"AP final score: Sky beat Storm","description":"Chicago beat Seattle in a final score thriller with late-game shotmaking.","datePublished":"2026-06-23T18:30:00Z"}</script>
                </head><body>Final score story.</body></html>
            """,
        }
    )
    discovery.requests = fake_requests

    discovery.main()

    rows = read_csv(run_dir / "story_candidates_discovery.csv")
    by_title = {row["title"]: row for row in rows}

    assert by_title["Liberty announce roster move before Aces game"]["publish_eligible"] == "Yes"
    assert by_title["Liberty announce roster move before Aces game"]["lead_source"] == "free_public_page"
    assert by_title["Liberty announce roster move before Aces game"]["promotion_hint"] == "news_packet"
    assert by_title["Liberty announce roster move before Aces game"]["published_at"] == "2026-06-24T09:00:00+00:00"
    assert by_title["Liberty announce roster move before Aces game"]["summary"] == "The Liberty announced a roster move before their Aces game."
    assert by_title["Liberty announce roster move before Aces game"]["evidence_title"] == "Official Liberty roster move before Aces matchup"
    assert by_title["Liberty announce roster move before Aces game"]["evidence_published_at"] == "2026-06-24T09:00:00+00:00"
    assert by_title["Liberty announce roster move before Aces game"]["evidence_description"] == "The Liberty announced a roster move before their Aces game."
    assert by_title["Liberty announce roster move before Aces game"]["evidence_source"] == "article_metadata"
    assert "Official Liberty roster move before Aces matchup" in by_title["Liberty announce roster move before Aces game"]["evidence_preview"]
    assert by_title["Liberty announce roster move before Aces game"]["freshness_label"] == "today"
    assert by_title["Liberty announce roster move before Aces game"]["freshness_source"] == "article_metadata"
    assert int(by_title["Liberty announce roster move before Aces game"]["quality_score"]) >= 70
    assert by_title["Sky beat Storm in final score thriller"]["promotion_hint"] == "studio_brief"
    assert by_title["Sky beat Storm in final score thriller"]["published_at"] == "2026-06-23T18:30:00+00:00"
    assert by_title["Sky beat Storm in final score thriller"]["summary"] == "Chicago beat Seattle in a final score thriller with late-game shotmaking."
    assert by_title["Sky beat Storm in final score thriller"]["evidence_title"] == "AP final score: Sky beat Storm"
    assert by_title["Sky beat Storm in final score thriller"]["freshness_label"] == "last_48_hours"
    assert by_title["Sky beat Storm in final score thriller"]["freshness_source"] == "article_metadata"
    assert by_title["All-time WNBA record leaders"]["freshness_label"].endswith("evergreen_angle")
    assert int(by_title["Liberty announce roster move before Aces game"]["quality_score"]) > int(by_title["All-time WNBA record leaders"]["quality_score"])
    assert by_title["Team account hints at injury update"]["publish_eligible"] == "No"
    assert by_title["Team account hints at injury update"]["lead_source"] == "manual_social_inbox"
    assert not (tmp_path / "story_candidates_discovery.csv").exists()
    assert "https://www.wnba.com/news/liberty-announce-roster-move" in fake_requests.calls
    assert "https://apnews.com/article/womens-basketball-final-score" in fake_requests.calls

    report = (run_dir / "discovery_sources_report.md").read_text(encoding="utf-8")
    assert "- Article metadata dates found: 3" in report
    assert "- Article metadata previews found: 3" in report

    board = load_module(BOARD_SCRIPT, "morning_board_intake_test")
    payload = board.build_payload()
    board_rows = {row["title"]: row for row in payload["rows"]}
    promotions = {row["title"]: row["promotion_recommendation"] for row in payload["promotion_recommendations"]}

    assert board_rows["Liberty announce roster move before Aces game"]["freshness_source"] == "article_metadata"
    assert board_rows["Liberty announce roster move before Aces game"]["evidence_source"] == "article_metadata"
    assert "The Liberty announced a roster move" in board_rows["Liberty announce roster move before Aces game"]["evidence_preview"]
    assert board_rows["Liberty announce roster move before Aces game"]["story_opportunity_title"] == "Official Liberty roster move before Aces matchup"
    assert board_rows["Liberty announce roster move before Aces game"]["story_opportunity_angle"] == "Roster or transaction update"
    assert board_rows["Sky beat Storm in final score thriller"]["story_opportunity_angle"] == "Result or performance angle"
    assert promotions["Official Liberty roster move before Aces matchup"] == "news_packet"
    sky_promotion_title = next(title for title in promotions if "Sky" in title and "Storm" in title)
    assert promotions[sky_promotion_title] == "studio_brief"
    assert promotions["Team account hints at injury update"] == "manual_story_candidate"


def test_article_date_from_public_metadata_formats() -> None:
    discovery = load_module(DISCOVERY_SCRIPT, "discovery_metadata_test")

    metadata = discovery.article_metadata_from_html(
        """
        <html><head>
          <meta property="og:title" content="Official result story" />
          <meta property="og:description" content="A concise public metadata description." />
          <meta property="article:published_time" content="2026-06-24T09:30:00Z" />
        </head></html>
        """
    )
    assert metadata == {
        "title": "Official result story",
        "published_at": "2026-06-24T09:30:00+00:00",
        "description": "A concise public metadata description.",
    }
    assert discovery.article_evidence_preview(metadata) == "Official result story | 2026-06-24 | A concise public metadata description."
    assert (
        discovery.article_date_from_html('<meta property="article:published_time" content="2026-06-24T09:30:00Z">')
        == "2026-06-24T09:30:00+00:00"
    )
    json_ld = discovery.article_metadata_from_html(
        '<script type="application/ld+json">{"@type":"NewsArticle","headline":"JSON title","description":"JSON description","datePublished":"2026-06-23T18:00:00Z"}</script>'
    )
    assert json_ld["title"] == "JSON title"
    assert json_ld["description"] == "JSON description"
    assert json_ld["published_at"] == "2026-06-23T18:00:00+00:00"
    assert (
        discovery.article_date_from_html(
            '<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-06-23T18:00:00Z"}</script>'
        )
        == "2026-06-23T18:00:00+00:00"
    )
    assert discovery.article_date_from_html('<time datetime="2026-06-22T10:15:00Z">June 22</time>') == "2026-06-22T10:15:00+00:00"


def test_manual_story_normalizer_writes_run_scoped_intake(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    write_registry(tmp_path / "config" / "source_registry.json")
    write_csv(
        tmp_path / "operator" / "inbox" / "story_inbox.csv",
        [
            {
                "input_type": "url",
                "source_url": "https://www.wnba.com/news/example",
                "title": "WNBA announces broadcast partnership",
                "summary": "Official league story.",
                "sport": "basketball",
                "league": "WNBA",
                "verification_status": "verified_official",
                "status": "queued",
                "requires_second_source": "false",
                "evidence_urls_json": "[\"https://www.wnba.com/news/example\"]",
                "fact_lock_json": "[\"The league announced a broadcast partnership.\"]",
            }
        ],
    )

    manual = load_module(MANUAL_SCRIPT, "manual_intake_test")
    manual.main()

    rows = read_csv(run_dir / "story_candidates_manual.csv")
    assert rows[0]["publish_eligible"] == "Yes"
    assert rows[0]["source_trust_band"] == "green"
    assert (run_dir / "manual_story_inbox_report.md").exists()
    assert (run_dir / "story_candidates_manual.jsonl").exists()
    assert not (tmp_path / "story_candidates_manual.csv").exists()
