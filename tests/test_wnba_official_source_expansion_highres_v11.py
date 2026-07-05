from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_official_source_expansion_highres_v11.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_playoffs_official_photo_galleries_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_official_source_expansion_highres_v11", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_playoffs_seed_csv_is_review_only_and_metadata_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_league_gallery"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_2025_playoffs_") for row in rows)
    assert all("wnba/league/2025_playoffs" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_playoffs_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v11"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v11"

    page_payloads = {
        "https://www.wnba.com/news/playoffs-photo-gallery-9-17-2025": """
            <html><head>
            <title>Photo Gallery: 2025 WNBA Playoffs, First Round (9/17/2025)</title>
            <meta property="og:title" content="Photo Gallery: 2025 WNBA Playoffs, First Round (9/17/2025)">
            <meta property="og:description" content="Check out the best photos from the First Round of the 2025 WNBA Playoffs presented by Google on September 17, 2025.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/09/POTN17.png">
            </head><body></body></html>
        """,
        "https://www.wnba.com/news/playoffs-photo-gallery-9-18-2025": """
            <html><head><title>Photo Gallery: 2025 WNBA Playoffs, First Round (9/18/2025)</title>
            <meta property="og:title" content="Photo Gallery: 2025 WNBA Playoffs, First Round (9/18/2025)">
            <meta property="og:description" content="Check out the best photos from the First Round of the 2025 WNBA Playoffs presented by Google on September 18, 2025.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/09/POTN919.png"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2025/09/POTN919.png"></body></html>
        """,
        "https://www.wnba.com/news/photo-gallery-2025-wnba-playoffs-semi-finals-9-21-2025": """
            <html><head><title>Photo Gallery: 2025 WNBA Playoffs, Semi-Finals (9/21/2025)</title>
            <meta property="og:title" content="Photo Gallery: 2025 WNBA Playoffs, Semi-Finals (9/21/2025)">
            <meta property="og:description" content="Check out the best photos from the Semi-Finals round of the 2025 WNBA Playoffs presented by Google on September 21, 2025.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/09/PONT921.png"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2025/09/PONT921.png"></body></html>
        """,
        "https://www.wnba.com/news/photo-gallery-2025-wnba-finals-game-one-10-3-2025": """
            <html><head><title>Photo Gallery: 2025 WNBA Finals - Game 1 (10/3/2025)</title>
            <meta property="og:title" content="Photo Gallery: 2025 WNBA Finals - Game 1 (10/3/2025)">
            <meta property="og:description" content="Check out the best photos from Game 1 of the 2025 WNBA Finals presented by YouTube TV on October 3, 2025.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/10/POTN103.png"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2025/10/POTN103.png"></body></html>
        """,
        "https://www.wnba.com/news/photo-gallery-2025-wnba-finals-game-four-10-10-2025": """
            <html><head><title>Photo Gallery: 2025 WNBA Finals - Game 4 (10/10/2025)</title>
            <meta property="og:title" content="Photo Gallery: 2025 WNBA Finals - Game 4 (10/10/2025)">
            <meta property="og:description" content="Check out the best photos from Game 4 of the 2025 WNBA Finals presented by YouTube TV on October 10, 2025.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/10/thumb-300x78.jpg"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2025/10/thumb-300x78.jpg"><img src="https://cdn.wnba.com/sites/4/2025/10/POTN1010.png"></body></html>
        """,
        "https://www.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_official_source_expansion_highres_v11_intake.csv")
    board_rows = read_csv(out_dir / "wnba_official_source_expansion_highres_v11_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_official_source_expansion_highres_v11_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_official_source_expansion_highres_v11_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "materially_action_photo_useful"
    assert manifest["thumbnail_suffix_count"] == 0
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_official_2025_playoffs_photo_galleries"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/4/2025/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/4/2025/09/POTN17.png",
        "https://cdn.wnba.com/sites/4/2025/09/POTN919.png",
        "https://cdn.wnba.com/sites/4/2025/09/PONT921.png",
        "https://cdn.wnba.com/sites/4/2025/10/POTN103.png",
        "https://cdn.wnba.com/sites/4/2025/10/POTN1010.png",
    }
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("matchup_or_recap_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Official Source Expansion Highres V11" in report
    assert "Thumbnail suffix count" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_playoffs_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661330/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_playoffs_image_url("https://cdn.wnba.com/sites/4/2025/10/thumb-300x78.jpg")
    assert not module.is_useful_playoffs_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_playoffs_image_url("https://cdn.wnba.com/sites/4/2025/10/POTN1010.png")
