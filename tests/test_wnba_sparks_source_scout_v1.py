from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_sparks_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_sparks_official_recaps_highres_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_sparks_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_sparks_seed_csv_is_review_only_and_highres_official_recap_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("sparks.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_los_angeles_sparks_") for row in rows)
    assert all("los_angeles_sparks" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_sparks_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v9"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v9"

    page_payloads = {
        "https://sparks.wnba.com/news/aces-vs-sparks-home-opener-game-recap": """
            <html><head>
            <title>Aces vs. Sparks - Home Opener Game Recap</title>
            <meta property="og:title" content="Aces vs. Sparks - Home Opener Game Recap">
            <meta property="og:description" content="The Sparks opened at home against the Aces in a public high-res action recap.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661320/2026/05/GettyImages-2275527959.jpg">
            </head><body>body</body></html>
        """,
        "https://sparks.wnba.com/news/sparks-win-ot-thriller-behind-historic-plumformance-june-13-game-recap": """
            <html><head>
            <title>Sparks Win OT Thriller Behind Historic Plumformance - June 13 Game Recap</title>
            <meta property="og:title" content="Sparks Win OT Thriller Behind Historic Plumformance - June 13 Game Recap">
            <meta property="og:description" content="Los Angeles and Phoenix met in a public recap with an action-forward feature image.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661320/2026/06/DSC08093.jpg">
            </head><body>body</body></html>
        """,
        "https://sparks.wnba.com/news/game-recap-vs-sky-6-29": """
            <html><head>
            <title>Game Recap vs Sky - 6/29</title>
            <meta property="og:title" content="Game Recap vs Sky - 6/29">
            <meta property="og:description" content="A public Sparks recap with a clean high-res CDN image.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661320/2025/06/GettyImages-2222789991-scaled.jpg">
            </head><body>body</body></html>
        """,
        "https://sparks.wnba.com/news/game-recap-july-13-vs-connecticut-sun": """
            <html><head>
            <title>Game Recap - July 13 vs. Connecticut Sun</title>
            <meta property="og:title" content="Game Recap - July 13 vs. Connecticut Sun">
            <meta property="og:description" content="The Sparks and Sun meet in a public action recap.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661320/2025/07/GettyImages-2224973675-1-scaled.jpg">
            </head><body>body</body></html>
        """,
        "https://sparks.wnba.com/news/june-9-sparks-vs-valkyries-recap": """
            <html><head>
            <title>June 9 Sparks vs. Valkyries Recap</title>
            <meta property="og:title" content="June 9 Sparks vs. Valkyries Recap">
            <meta property="og:description" content="The Sparks and Valkyries play out a public recap with a strong lead image.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661320/2025/06/GettyImages-2218863939-scaled.jpg">
            </head><body><img src="https://cdn.wnba.com/sites/1611661320/2025/06/thumb-300x78.jpg"></body></html>
        """,
        "https://sparks.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_sparks_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_sparks_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_sparks_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_sparks_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_recap_family"
    assert manifest["thumbnail_suffix_count"] == 0
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_sparks_official_game_recaps_highres"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661320/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661320/2026/05/GettyImages-2275527959.jpg",
        "https://cdn.wnba.com/sites/1611661320/2026/06/DSC08093.jpg",
        "https://cdn.wnba.com/sites/1611661320/2025/06/GettyImages-2222789991-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661320/2025/07/GettyImages-2224973675-1-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661320/2025/06/GettyImages-2218863939-scaled.jpg",
    }
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in board_rows)
    assert all("-300x78." not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("matchup_or_recap_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Sparks Official Game Recap Source Scout V1" in report
    assert "Thumbnail suffix count" in report
    assert "Strengths" in report
    assert "Weaknesses" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_sparks_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661320/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_sparks_image_url("https://cdn.wnba.com/sites/1611661320/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_sparks_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_sparks_image_url("https://cdn.wnba.com/sites/1611661320/2026/06/DSC08093.jpg")
