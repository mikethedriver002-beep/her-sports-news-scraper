from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_official_source_expansion_highres_v13.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_2019_all_star_photo_suite_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_official_source_expansion_highres_v13", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_all_star_seed_csv_is_review_only_and_metadata_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 6
    assert {row["source_type"] for row in rows} == {"official_league_gallery"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_2019_all_star_") for row in rows)
    assert all("wnba/league/2019_all_star" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_all_star_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v13"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v13"

    page_payloads = {
        "https://www.wnba.com/news/att-wnba-all-star-2019-game-action-photos": """
            <html><head>
            <title>AT&T WNBA All-Star 2019: Game Action Photos</title>
            <meta property="og:title" content="AT&T WNBA All-Star 2019: Game Action Photos">
            <meta property="og:description" content="Check out the best images from the WNBA All-Star Game as Team Wilson beat Team Delle Donne.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2019/07/griner-dunk-game-action-850-190727.jpg">
            </head><body></body></html>
        """,
        "https://www.wnba.com/news/att-wnba-all-star-2019-pregame-photos": """
            <html><head><title>AT&T WNBA All-Star 2019: Pregame Photos</title>
            <meta property="og:title" content="AT&T WNBA All-Star 2019: Pregame Photos">
            <meta property="og:description" content="Check out the best images from prior to tip off, including player introduction, official team photos, entertainers and more.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2019/07/deshields-intro-pregame-850-190727.jpg"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2019/07/deshields-intro-pregame-850-190727.jpg"></body></html>
        """,
        "https://www.wnba.com/news/att-wnba-all-star-2019-courtside-photos": """
            <html><head><title>AT&T WNBA All-Star 2019: Courtside Photos</title>
            <meta property="og:title" content="AT&T WNBA All-Star 2019: Courtside Photos">
            <meta property="og:description" content="Check out the best images from off the court at AT&T WNBA All-Star 2019, including star sightings, fan interactions and halftime performance moments.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2019/07/aja-kobe-courtside-850-190727.jpg"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2019/07/aja-kobe-courtside-850-190727.jpg"></body></html>
        """,
        "https://www.wnba.com/news/att-wnba-all-star-2019-postgame-photos": """
            <html><head><title>AT&T WNBA All-Star 2019: Postgame Photos</title>
            <meta property="og:title" content="AT&T WNBA All-Star 2019: Postgame Photos">
            <meta property="og:description" content="The best images from Erica Wheeler's MVP presentation, press conference and photo shoot.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2019/07/wheeler-mvp-postgame-850-190727.jpg"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2019/07/wheeler-mvp-postgame-850-190727.jpg"></body></html>
        """,
        "https://www.wnba.com/news/2019-wnba-all-star-skills-challenge": """
            <html><head><title>2019 WNBA All-Star Skills Challenge</title>
            <meta property="og:title" content="2019 WNBA All-Star Skills Challenge">
            <meta property="og:description" content="Chicago's Diamond DeShields defeated Connecticut's Jonquel Jones in the finals of the Skills Challenge at AT&T WNBA All-Star Friday Night.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2019/07/thumb-300x78.jpg"></head>
            <body>
            <img src="https://cdn.wnba.com/sites/4/2019/07/thumb-300x78.jpg">
            <img src="https://cdn.wnba.com/sites/4/2019/07/deshields-skills-gallery-850.jpg">
            </body></html>
        """,
        "https://www.wnba.com/news/2019-wnba-three-point-contest-presented-by-mtn-dew": """
            <html><head><title>2019 WNBA Three-Point Contest</title>
            <meta property="og:title" content="2019 WNBA Three-Point Contest">
            <meta property="og:description" content="Connecticut's Shekinna Stricklen edged out Las Vegas' Kayla McBride to win the 2019 WNBA Three-Point Contest presented by MTN DEW.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2019/07/stricken-3pt-gallery-850.jpg"></head>
            <body><img src="https://cdn.wnba.com/sites/4/2019/07/stricken-3pt-gallery-850.jpg"></body></html>
        """,
        "https://www.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_official_source_expansion_highres_v13_intake.csv")
    board_rows = read_csv(out_dir / "wnba_official_source_expansion_highres_v13_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_official_source_expansion_highres_v13_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_official_source_expansion_highres_v13_ready"
    assert manifest["candidate_row_count"] == 6
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "materially_action_photo_useful"
    assert manifest["thumbnail_suffix_count"] == 0
    assert len(intake_rows) == 6
    assert len(board_rows) == 6
    assert {row["source_family_id"] for row in board_rows} == {"wnba_official_2019_all_star_photo_suite"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/4/2019/07/") for row in board_rows)
    assert "thumb-300x78.jpg" not in {row["candidate_image_url"] for row in board_rows}
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("event_scoped_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 6
    assert "WNBA Official Source Expansion Highres V13" in report
    assert "Thumbnail suffix count" in report
    assert "2019 All-Star photo-suite" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 6
    assert deck_manifest["download_approved_default"] == "no"


def test_all_star_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661330/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_all_star_image_url("https://cdn.wnba.com/sites/4/2025/10/thumb-300x78.jpg")
    assert not module.is_useful_all_star_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_all_star_image_url("https://cdn.wnba.com/sites/4/2019/07/griner-dunk-game-action-850-190727.jpg")
