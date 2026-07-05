from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_sun_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_sun_official_recaps_v1.csv"
)
EXCLUDED_TEAM_DOMAINS = ("fever", "storm", "aces", "lynx", "mercury", "valkyries", "dream", "mystics")


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_sun_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_sun_seed_csv_is_review_only_and_disjoint_source_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 4
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("sun.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_connecticut_sun_") for row in rows)
    assert all("connecticut_sun" in row["quarantine_target_hint"] for row in rows)
    assert all(not any(f"{excluded}.wnba.com" in row["source_page_url"] for excluded in EXCLUDED_TEAM_DOMAINS) for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_sun_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v6"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v6"

    page_payloads = {
        "https://sun.wnba.com/news/sun-fall-in-down-to-the-wire-battle-against-wings-86-83": """
            <html><head>
            <title>Sun Fall in Down-to-the-Wire Battle Against Wings, 86-83</title>
            <meta property="og:title" content="Sun Fall in Down-to-the-Wire Battle Against Wings, 86-83">
            <meta property="og:description" content="The Connecticut Sun battled Dallas in a late-game official recap.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661323/2026/07/GettyImages-2284502022-scaled.jpg">
            </head><body></body></html>
        """,
        "https://sun.wnba.com/news/sun-build-win-streak-over-mystics-wins-68-57": """
            <html><head><title>Sun Build Win Streak Over Mystics, Wins 68-57</title>
            <meta property="og:description" content="Connecticut Sun recap with official game action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661323/2026/06/GettyImages-2282983195-scaled.jpg"></body></html>
        """,
        "https://sun.wnba.com/news/sun-defeat-sky-92-63": """
            <html><head><title>Sun Defeat Sky, 92-63</title>
            <meta property="og:description" content="Sun game recap with public action-photo context."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661323/2026/07/GettyImages-2283823358-scaled.jpg"></body></html>
        """,
        "https://sun.wnba.com/news/sun-fall-to-tempo-101-97": """
            <html><head><title>Sun Fall to Tempo, 101-97</title>
            <meta property="og:description" content="Connecticut Sun game recap with transition action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661323/2026/06/thumb-300x78.jpg">
            <img src="https://cdn.wnba.com/sites/1611661323/2026/06/gettyimages-2283451777-594x594-1.jpg">
            <img src="https://cdn.wnba.com/sites/1611661323/2026/06/GettyImages-2282319277-scaled.jpg"></body></html>
        """,
        "https://sun.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_sun_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_sun_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_sun_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_sun_source_scout_ready"
    assert manifest["candidate_row_count"] == 4
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_recap_family"
    assert len(intake_rows) == 4
    assert len(board_rows) == 4
    assert {row["source_family_id"] for row in board_rows} == {"wnba_sun_official_game_recaps"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661323/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661323/2026/07/GettyImages-2284502022-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661323/2026/06/GettyImages-2282983195-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661323/2026/07/GettyImages-2283823358-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661323/2026/06/GettyImages-2282319277-scaled.jpg",
    }
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in board_rows)
    assert all("-300x78." not in row["candidate_image_url"] for row in board_rows)
    assert all("-594x594" not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("matchup_or_recap_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 4
    assert "WNBA Sun Official Game Recap Source Scout V1" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 4
    assert deck_manifest["download_approved_default"] == "no"


def test_sun_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661323/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_sun_image_url("https://cdn.wnba.com/sites/1611661323/2026/06/thumb-300x78.jpg")
    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661323/2026/06/gettyimages-2283451777-594x594-1.jpg")
    assert not module.is_useful_sun_image_url("https://cdn.wnba.com/sites/1611661323/2026/06/gettyimages-2283451777-594x594-1.jpg")
    assert not module.is_useful_sun_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_sun_image_url("https://cdn.wnba.com/sites/1611661323/2026/06/GettyImages-2282975494-1-scaled.jpg")
