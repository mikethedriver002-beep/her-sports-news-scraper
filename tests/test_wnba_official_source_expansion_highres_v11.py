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
    / "review_only_action_photo_candidate_scout_wnba_official_league_game_recap_highres_v11.csv"
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


def test_official_league_recap_seed_csv_is_review_only_and_disjoint_source_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_league_recap_video"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all(row["source_page_url"].startswith("https://www.wnba.com/watch/video/") for row in rows)
    assert all(row["entity_id"].startswith("wnba_league_game_recap_") for row in rows)
    assert all("wnba/league_game_recap" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_official_league_recap_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v11"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v11"

    page_payloads = {
        "https://www.wnba.com/watch/video/game-recap-portland-fire-77-seattle-storm-72-07-04-2026": """
            <html><head>
            <title>Game Recap: Portland Fire 77, Seattle Storm 72 (07/04/2026)</title>
            <meta property="og:title" content="Game Recap: Portland Fire 77, Seattle Storm 72 (07/04/2026)">
            <meta property="og:description" content="The Fire defeated the Storm 77-72. The Fire improve to 9-12 while the Storm fall to 5-17.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2026/07/pdx_sea_recap_070426_full.png">
            </head><body><img src="https://cdn.wnba.com/sites/4/2026/07/WNBA26_FGH_recap_16x9v4-28.jpg"></body></html>
        """,
        "https://www.wnba.com/watch/video/game-recap-las-vegas-aces-98-chicago-sky-90-07-03-2026": """
            <html><head>
            <title>Game Recap: Las Vegas Aces 98, Chicago Sky 90 (07/03/2026)</title>
            <meta property="og:title" content="Game Recap: Las Vegas Aces 98, Chicago Sky 90 (07/03/2026)">
            <meta property="og:description" content="The Aces defeated the Sky 98-90 in overtime. The Aces improve to 15-5 while the Sky fall to 6-14.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2026/07/chi_lva_recap_070326-full.png">
            </head><body><img src="https://cdn.wnba.com/sites/4/2026/07/640x360-30.png"></body></html>
        """,
        "https://www.wnba.com/watch/video/game-recap-new-york-liberty-99-minnesota-lynx-86-07-03-2026": """
            <html><head>
            <title>Game Recap: New York Liberty 99, Minnesota Lynx 86 (07/03/2026)</title>
            <meta property="og:title" content="Game Recap: New York Liberty 99, Minnesota Lynx 86 (07/03/2026)">
            <meta property="og:description" content="The Liberty defeated the Lynx 99-86. The Liberty improve to 13-8 while the Lynx fall to 15-5.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2026/07/min_nyl_recap_070326-full.png">
            </head><body><img src="https://cdn.wnba.com/sites/4/2026/07/18cf6be1-e1ef-4bfd-b010-3b2c5c63ba9d_0.jpg"></body></html>
        """,
        "https://www.wnba.com/watch/video/game-recap-golden-state-valkyries-88-atlanta-dream-83-07-04-2026": """
            <html><head>
            <title>Game Recap: Golden State Valkyries 88, Atlanta Dream 83 (07/04/2026)</title>
            <meta property="og:title" content="Game Recap: Golden State Valkyries 88, Atlanta Dream 83 (07/04/2026)">
            <meta property="og:description" content="The Golden State Valkyries ended the game on a 14-6 run to defeat the Atlanta Dream, 88-83.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2026/07/gsv_atl_recap_070426_full.png">
            </head><body><img src="https://cdn.wnba.com/sites/4/2026/07/WNBA26_FGH_recap_16x9v4-25.jpg"></body></html>
        """,
        "https://www.wnba.com/watch/video/game-recap-new-york-liberty-93-las-vegas-aces-85-06-30-2026": """
            <html><head>
            <title>Game Recap: New York Liberty 93, Las Vegas Aces 85 (06/30/2026)</title>
            <meta property="og:title" content="Game Recap: New York Liberty 93, Las Vegas Aces 85 (06/30/2026)">
            <meta property="og:description" content="The New York Liberty defeated the Las Vegas Aces, 93-85, to win the 2026 WNBA Commissioner's Cup Championship and finish a perfect 7-0 in the tourney.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/4/2026/06/lva_nyl_recap_063026-full.png">
            </head><body><img src="https://cdn.wnba.com/sites/4/2026/07/WNBA26_FGH_recap_16x9v4-30.png"></body></html>
        """,
        "https://www.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_official_league_game_recap_highres_v11_intake.csv")
    board_rows = read_csv(out_dir / "wnba_official_league_game_recap_highres_v11_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_official_league_game_recap_highres_v11_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_official_source_expansion_highres_v11_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_league_recap_family"
    assert manifest["thumbnail_suffix_count"] == 0
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_official_league_game_recap_highres"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/4/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/4/2026/07/pdx_sea_recap_070426_full.png",
        "https://cdn.wnba.com/sites/4/2026/07/chi_lva_recap_070326-full.png",
        "https://cdn.wnba.com/sites/4/2026/07/min_nyl_recap_070326-full.png",
        "https://cdn.wnba.com/sites/4/2026/07/gsv_atl_recap_070426_full.png",
        "https://cdn.wnba.com/sites/4/2026/06/lva_nyl_recap_063026-full.png",
    }
    assert all("-300x169." not in row["candidate_image_url"] for row in board_rows)
    assert all("-640x360." not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("source_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Official League Game Recap High-Res Source Scout V11" in report
    assert "Thumbnail suffix count" in report
    assert "Strengths" in report
    assert "Weaknesses" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_official_league_recap_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/4/2026/07/640x360-30.png")
    assert not module.is_useful_wnba_league_image_url("https://cdn.wnba.com/sites/4/2026/07/640x360-30.png")
    assert not module.is_useful_wnba_league_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_wnba_league_image_url("https://cdn.wnba.com/sites/4/2026/07/pdx_sea_recap_070426_full.png")
