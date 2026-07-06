from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_official_source_expansion_highres_v14.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_2025_all_star_weekend_photo_suite_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_official_source_expansion_highres_v14", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_all_star_weekend_seed_csv_is_review_only_and_metadata_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 3
    assert {row["source_type"] for row in rows} == {"official_league_gallery"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_2025_all_star_") for row in rows)
    assert all("wnba/league/2025_all_star_weekend" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_all_star_weekend_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v14"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v14"

    page_payloads = {
        "https://www.wnba.com/news/2025-all-star-friday-night-photo-gallery": """
            <html><head>
            <title>Photo Gallery: 2025 All-Star Friday Night</title>
            <meta property="og:title" content="Photo Gallery: 2025 All-Star Friday Night">
            <meta property="og:description" content="Look back at some of the best moments from the 2025 STARRY 3-Point Contest and the Kia WNBA Skills Challenge.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/07/FEATUREIMAGE_-Recovered-1.png">
            </head><body><img src="https://cdn.wnba.com/sites/4/2025/07/FEATUREIMAGE_-Recovered-1.png"></body></html>
        """,
        "https://www.wnba.com/news/2025-all-star-orange-carpet-photo-gallery": """
            <html><head><title>Photo Gallery: 2025 WNBA All-Star Orange Carpet presented by Bumble</title>
            <meta property="og:title" content="Photo Gallery: 2025 WNBA All-Star Orange Carpet presented by Bumble">
            <meta property="og:description" content="Check out some of the best looks and moments of the night from the WNBA All-Star Orange Carpet presented by Bumble!">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/07/OrangeCarpetAllStar.png"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2025/07/OrangeCarpetAllStar.png"></body></html>
        """,
        "https://www.wnba.com/news/2025-all-star-roster-photo-gallery": """
            <html><head><title>Photo Gallery: 2025 AT&T WNBA All-Star Game Roster</title>
            <meta property="og:title" content="Photo Gallery: 2025 AT&T WNBA All-Star Game Roster">
            <meta property="og:description" content="Take a look at the players participating in the 2025 AT&T WNBA All-Star Game.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2025/07/AllStarGallery.png"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2025/07/AllStarGallery.png"></body></html>
        """,
        "https://www.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_official_source_expansion_highres_v14_intake.csv")
    board_rows = read_csv(out_dir / "wnba_official_source_expansion_highres_v14_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_official_source_expansion_highres_v14_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_official_source_expansion_highres_v14_ready"
    assert manifest["candidate_row_count"] == 3
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "materially_action_photo_useful"
    assert manifest["thumbnail_suffix_count"] == 0
    assert len(intake_rows) == 3
    assert len(board_rows) == 3
    assert {row["source_family_id"] for row in board_rows} == {"wnba_official_2025_all_star_weekend_photo_suite"}
    assert board_rows[0]["candidate_queue_id"] == "WAS001"
    assert board_rows[0]["source_url"] == "https://www.wnba.com/news/2025-all-star-friday-night-photo-gallery"
    assert board_rows[0]["candidate_quality_tier"] == "A_primary_source_lead"
    assert int(board_rows[0]["score"]) > int(board_rows[1]["score"])
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/4/2025/07/FEATUREIMAGE_-Recovered-1.png",
        "https://cdn.wnba.com/sites/4/2025/07/OrangeCarpetAllStar.png",
        "https://cdn.wnba.com/sites/4/2025/07/AllStarGallery.png",
    }
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/4/2025/07/") for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("event_scoped_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 3
    assert "WNBA Official Source Expansion Highres V14" in report
    assert "Thumbnail suffix count" in report
    assert "2025 All-Star weekend photo-suite" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 3
    assert deck_manifest["download_approved_default"] == "no"


def test_all_star_weekend_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661330/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_all_star_image_url("https://cdn.wnba.com/sites/4/2025/10/thumb-300x78.jpg")
    assert not module.is_useful_all_star_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_all_star_image_url("https://cdn.wnba.com/sites/4/2025/07/OrangeCarpetAllStar.png")
