from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_liberty_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_liberty_official_highres_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_liberty_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_liberty_seed_csv_is_review_only_and_highres_official_news_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_story", "official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("liberty.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_new_york_liberty_") for row in rows)
    assert all("new_york_liberty" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_liberty_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v10"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v10"

    page_payloads = {
        "https://liberty.wnba.com/news/new-york-liberty-sign-anneli-maley": """
            <html><head>
            <title>New York Liberty Sign Anneli Maley</title>
            <meta property="og:title" content="New York Liberty Sign Anneli Maley">
            <meta property="og:description" content="The New York Liberty have signed forward Anneli Maley to a developmental player contract.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661313/2026/05/1920x1080-1.jpg">
            </head><body>body</body></html>
        """,
        "https://liberty.wnba.com/news/new-york-liberty-sign-alexandra-fowler": """
            <html><head>
            <title>New York Liberty Sign Alexandra Fowler</title>
            <meta property="og:title" content="New York Liberty Sign Alexandra Fowler">
            <meta property="og:description" content="The New York Liberty have signed Australian forward Alexandra Fowler.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661313/2026/05/NYL26_WELCOME_FOWLER-1920x1080-1.jpg">
            </head><body>body</body></html>
        """,
        "https://liberty.wnba.com/news/new-york-liberty-sign-pauline-astier": """
            <html><head>
            <title>New York Liberty Sign Pauline Astier</title>
            <meta property="og:title" content="New York Liberty Sign Pauline Astier">
            <meta property="og:description" content="The New York Liberty have signed guard Pauline Astier.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661313/2026/04/NYL26_WELCOMESIGNED_PAULINE_ASTIER1920x1080.jpg">
            </head><body>body</body></html>
        """,
        "https://liberty.wnba.com/news/new-york-liberty-unveil-court-origins-retro-uniform": """
            <html><head>
            <title>New York Liberty Unveil Court Origins Retro Uniform</title>
            <meta property="og:title" content="New York Liberty Unveil Court Origins Retro Uniform">
            <meta property="og:description" content="The Nike New York Liberty Court Origins Edition uniform will debut at Barclays Center.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661313/2026/04/NYL26_COURTORIGINS-LAUNCH_1920x1080_1.jpg">
            </head><body>body</body></html>
        """,
        "https://liberty.wnba.com/news/libs-abroad-january-2026-recap": """
            <html><head>
            <title>Libs Abroad January 2026 Recap</title>
            <meta property="og:title" content="Libs Abroad January 2026 Recap">
            <meta property="og:description" content="The New York Liberty recap overseas action with a public high-res banner image.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661313/2026/01/NYL25_LIBSABROAD_RECAP-BANNER1920x1080.jpg">
            </head><body><img src="https://cdn.wnba.com/sites/1611661313/2025/06/thumb-300x78.jpg"></body></html>
        """,
        "https://liberty.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_liberty_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_liberty_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_liberty_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_liberty_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_news_and_recap_family"
    assert manifest["thumbnail_suffix_count"] == 0
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_new_york_liberty_official_highres_news_and_recaps"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661313/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661313/2026/05/1920x1080-1.jpg",
        "https://cdn.wnba.com/sites/1611661313/2026/05/NYL26_WELCOME_FOWLER-1920x1080-1.jpg",
        "https://cdn.wnba.com/sites/1611661313/2026/04/NYL26_WELCOMESIGNED_PAULINE_ASTIER1920x1080.jpg",
        "https://cdn.wnba.com/sites/1611661313/2026/04/NYL26_COURTORIGINS-LAUNCH_1920x1080_1.jpg",
        "https://cdn.wnba.com/sites/1611661313/2026/01/NYL25_LIBSABROAD_RECAP-BANNER1920x1080.jpg",
    }
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in board_rows)
    assert all("-300x78." not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("source_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA New York Liberty Official High-Res News and Recap Source Scout V1" in report
    assert "Thumbnail suffix count" in report
    assert "Strengths" in report
    assert "Weaknesses" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_liberty_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661313/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_liberty_image_url("https://cdn.wnba.com/sites/1611661313/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_liberty_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_liberty_image_url("https://cdn.wnba.com/sites/1611661313/2026/06/NYL26_TRAININGCAMP_1920x1080.jpg")
