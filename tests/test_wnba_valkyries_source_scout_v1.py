from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_valkyries_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_valkyries_official_recaps_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_valkyries_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_valkyries_seed_csv_is_review_only_and_disjoint_source_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("valkyries.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_golden_state_valkyries_") for row in rows)
    assert all("golden_state_valkyries" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_valkyries_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v3"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v3"

    page_payloads = {
        "https://valkyries.wnba.com/news/gameday-recap-20260510": """
            <html><head>
            <title>Second Quarter Surge Leads Valkyries Over Mercury in Home Opener</title>
            <meta property="og:title" content="Second Quarter Surge Leads Valkyries Over Mercury in Home Opener">
            <meta property="og:description" content="The Golden State Valkyries defeated the Phoenix Mercury in a home opener recap with game action.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661331/2026/05/20260510-Janelle-Salaun-1280.png">
            </head><body></body></html>
        """,
        "https://valkyries.wnba.com/news/gameday-recap-20260508": """
            <html><head><title>Valkyries Defeat Seattle Storm by Double Digits</title>
            <meta property="og:description" content="Golden State Valkyries victory recap with road game action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661331/2026/05/20260508-GSV-SEA-Kaitlyn-Chen-1280.png"></body></html>
        """,
        "https://valkyries.wnba.com/news/gameday-recap-20260615": """
            <html><head><title>Wire-to-Wire Victory Over Sparks</title>
            <meta property="og:description" content="Valkyries recap with in-game feature image."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661331/2026/06/580x150-300x78.jpg">
            <img src="https://cdn.wnba.com/sites/1611661331/2026/06/feat-image-in-game-20260615.png"></body></html>
        """,
        "https://valkyries.wnba.com/news/gameday-recap-20260628": """
            <html><head><title>Wire-to-Wire Win Over Liberty</title>
            <meta property="og:description" content="Valkyries recap with feature image and public game action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661331/2026/06/feat-image-ceci-20260628.png"></body></html>
        """,
        "https://valkyries.wnba.com/news/gameday-recap-20250521": """
            <html><head><title>Veronica Burton Career Night Leads Valkyries to First Win</title>
            <meta property="og:description" content="Valkyries first win recap with public action-photo context."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661331/2025/05/20250521-Veronica-Burton-1280.png"></body></html>
        """,
        "https://valkyries.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_valkyries_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_valkyries_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_valkyries_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_valkyries_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_recap_family"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_valkyries_official_game_recaps"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661331/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661331/2026/05/20260510-Janelle-Salaun-1280.png",
        "https://cdn.wnba.com/sites/1611661331/2026/05/20260508-GSV-SEA-Kaitlyn-Chen-1280.png",
        "https://cdn.wnba.com/sites/1611661331/2026/06/feat-image-in-game-20260615.png",
        "https://cdn.wnba.com/sites/1611661331/2026/06/feat-image-ceci-20260628.png",
        "https://cdn.wnba.com/sites/1611661331/2025/05/20250521-Veronica-Burton-1280.png",
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
    assert "WNBA Valkyries Official Game Recap Source Scout V1" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_valkyries_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661331/2026/06/580x150-300x78.jpg")
    assert not module.is_useful_valkyries_image_url("https://cdn.wnba.com/sites/1611661331/2026/06/580x150-300x78.jpg")
    assert not module.is_useful_valkyries_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_valkyries_image_url("https://cdn.wnba.com/sites/1611661331/2026/05/20260510-Janelle-Salaun-1280.png")
