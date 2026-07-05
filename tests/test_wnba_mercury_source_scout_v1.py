from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_mercury_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_mercury_game_galleries_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_mercury_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_mercury_seed_csv_is_review_only_and_disjoint_source_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_gallery"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("mercury.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_phoenix_mercury_") for row in rows)
    assert all("phoenix_mercury" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_mercury_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v2"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v2"

    page_payloads = {
        "https://mercury.wnba.com/news/mercury-at-fever-jun-24-2026": """
            <html><head>
            <title>Mercury at Fever | Jun. 24, 2026</title>
            <meta property="og:title" content="Mercury at Fever | Jun. 24, 2026">
            <meta property="og:description" content="Game Gallery Mercury at Fever. Mercury drives into the lane during the game.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2283192312-185x148.jpg">
            </head><body>
            <img src="https://cdn.wnba.com/sites/1611661317/2025/11/cropped-MercuryPrimary-1.png">
            <img src="https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2283192312-scaled.jpg">
            </body></html>
        """,
        "https://mercury.wnba.com/news/mercury-at-valkyries-jun-9-2026": """
            <html><head><title>Mercury at Valkyries | Jun. 9, 2026</title>
            <meta property="og:description" content="Game Gallery Mercury at Valkyries with public action frames."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2280206660-scaled.jpg"></body></html>
        """,
        "https://mercury.wnba.com/news/mercury-at-fire-jun-5-2026": """
            <html><head><title>Mercury at Fire | Jun. 5, 2026</title>
            <meta property="og:description" content="Game Gallery Mercury at Fire with transition action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2279426852-scaled.jpg"></body></html>
        """,
        "https://mercury.wnba.com/news/mercury-at-dream-may-24-2026": """
            <html><head><title>Mercury at Dream | May 24, 2026</title>
            <meta property="og:description" content="Game Gallery Mercury at Dream with review-only action-photo context."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661317/2026/05/GettyImages-2277527239-scaled.jpg"></body></html>
        """,
        "https://mercury.wnba.com/news/mercury-vs-sparks-may-21-2026": """
            <html><head><title>Mercury vs Sparks | May 21, 2026</title>
            <meta property="og:description" content="Game Gallery Mercury vs Sparks at PHX Arena."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661317/2026/05/GettyImages-2277590897-scaled.jpg"></body></html>
        """,
        "https://mercury.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_mercury_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_mercury_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_mercury_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_mercury_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_gallery_family"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_mercury_official_game_galleries"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661317/2026/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2283192312-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2280206660-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2279426852-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661317/2026/05/GettyImages-2277527239-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661317/2026/05/GettyImages-2277590897-scaled.jpg",
    }
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in board_rows)
    assert all("-320x180." not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("matchup_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Mercury Official Game Gallery Source Scout V1" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_mercury_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-1-185x148.jpg")
    assert not module.is_useful_mercury_image_url("https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-1-185x148.jpg")
    assert module.is_useful_mercury_image_url("https://cdn.wnba.com/sites/1611661317/2026/06/GettyImages-2283192312-scaled.jpg")
