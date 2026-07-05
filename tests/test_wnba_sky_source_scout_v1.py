from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_sky_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_sky_game_day_highlights_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_sky_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_sky_seed_csv_is_review_only_and_highres_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_highlight_gallery"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "strong_context" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("sky.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(
        row["quarantine_target_hint"].startswith(
            "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/chicago_sky/"
        )
        for row in rows
    )
    assert "review-only" in rows[0]["notes"].lower()


def test_sky_source_scout_builds_metadata_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v8"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v8"

    page_payloads = {
        "https://sky.wnba.com/news/chicago-sky-vs-portland-fire-6-26-game-day-highlights-presented-by-demesmin-dover": (
            200,
            """
            <html><head>
            <title>Chicago Sky vs. Portland Fire, 6/26 Game Day Highlights Presented By Demesmin & Dover</title>
            <meta property="og:title" content="Chicago Sky vs. Portland Fire, 6/26 Game Day Highlights Presented By Demesmin & Dover">
            <meta property="og:description" content="The Chicago Sky hosted the Portland Fire in a public game-day highlights gallery with court action and bench reaction.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661329/2026/06/Q1-11-1.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://sky.wnba.com/news/chicago-sky-vs-indiana-fever-6-11-game-day-highlights-presented-by-demesmin-dover": (
            200,
            """
            <html><head>
            <title>Chicago Sky vs. Indiana Fever, 6/11 Game Day Highlights Presented By Demesmin & Dover</title>
            <meta property="og:title" content="Chicago Sky vs. Indiana Fever, 6/11 Game Day Highlights Presented By Demesmin & Dover">
            <meta property="og:description" content="A public official Sky highlights page with matchup context and strong body-margin review potential.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661329/2026/06/Q2-1-1.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://sky.wnba.com/news/chicago-sky-vs-phoenix-mercury-game-day-highlights-presented-by-demesmin-dover": (
            200,
            """
            <html><head>
            <title>Chicago Sky vs. Phoenix Mercury Game Day Highlights Presented By Demesmin & Dover</title>
            <meta property="og:title" content="Chicago Sky vs. Phoenix Mercury Game Day Highlights Presented By Demesmin & Dover">
            <meta property="og:description" content="Public game-day highlights from the official Chicago Sky news page, with usable action-photo evidence.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661329/2026/06/Q2-3.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://sky.wnba.com/news/chicago-sky-vs-washington-mystics-6-2-game-day-highlights-presented-by-demesmin-dover": (
            200,
            """
            <html><head>
            <title>Chicago Sky vs. Washington Mystics, 6/2 Game Day Highlights Presented By Demesmin & Dover</title>
            <meta property="og:title" content="Chicago Sky vs. Washington Mystics, 6/2 Game Day Highlights Presented By Demesmin & Dover">
            <meta property="og:description" content="Official Sky matchup highlights with a public CDN image and enough context for manual review.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661329/2026/06/0MD_6381_2-1024x576.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://sky.wnba.com/news/chicago-sky-vs-atlanta-dream-preseason-game-day-highlights-presented-by-demesmin-dover": (
            200,
            """
            <html><head>
            <title>Chicago Sky vs. Atlanta Dream Preseason Game Day Highlights Presented By Demesmin & Dover</title>
            <meta property="og:title" content="Chicago Sky vs. Atlanta Dream Preseason Game Day Highlights Presented By Demesmin & Dover">
            <meta property="og:description" content="Official preseason highlights from the Chicago Sky with review-only source quality metadata.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661329/2026/05/Game4.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://sky.wnba.com/robots.txt": (403, "Forbidden"),
    }

    def fetcher(url: str):
        status, payload = page_payloads[url]
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        return module.FetchedResponse(url=url, status=status, headers={"Content-Type": "text/html"}, body=body)

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_sky_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_sky_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_sky_source_scout_report.md").read_text(encoding="utf-8")
    board_by_candidate = {row["candidate_queue_id"]: row for row in board_rows}

    assert manifest["status"] == "wnba_sky_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["robots_summary"] == "robots_txt_http_403_or_unavailable"
    assert manifest["auth_summary"] == "public_pages_reachable"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert board_by_candidate["WSKY001"]["source_family_id"] == "wnba_chicago_sky_official_game_day_highlights"
    assert board_by_candidate["WSKY001"]["candidate_quality_tier"] in {"A_primary_source_lead", "B_strong_source_lead"}
    assert board_by_candidate["WSKY001"]["candidate_image_url"].startswith("https://cdn.wnba.com/")
    assert all(
        not any(suffix in row["candidate_image_url"] for suffix in ("-185x148", "-260x190", "-320x180"))
        for row in board_rows
    )
    assert all(
        not any(suffix in row["candidate_photo_url"] for suffix in ("-185x148", "-260x190", "-320x180"))
        for row in intake_rows
    )
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Chicago Sky High-Resolution Source Scout V1" in report
    assert "Thumbnail suffix hits: `0`" in report
    assert "Strengths" in report
    assert "Weaknesses" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"
