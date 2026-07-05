from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_dream_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_dream_official_recaps_v1.csv"
)
EXCLUDED_FAMILIES = ("fever", "storm", "aces", "lynx", "mercury", "valkyries")


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_dream_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_dream_seed_csv_is_review_only_and_disjoint_source_family() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 4
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("dream.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_atlanta_dream_") for row in rows)
    assert all("atlanta_dream" in row["quarantine_target_hint"] for row in rows)
    assert all(not any(excluded in row["entity_id"] for excluded in EXCLUDED_FAMILIES) for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_dream_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v4"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v4"

    page_payloads = {
        "https://dream.wnba.com/news/dream-starts-the-season-2-0-with-a-win-in-dallas": """
            <html><head>
            <title>Dream Starts the Season 2-0 with a Win in Dallas</title>
            <meta property="og:title" content="Dream Starts the Season 2-0 with a Win in Dallas">
            <meta property="og:description" content="The Atlanta Dream dominated Dallas defensively in the fourth quarter.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661330/2026/05/Untitled-22.png">
            </head><body></body></html>
        """,
        "https://dream.wnba.com/news/dream-scores-a-win-in-reeses-return-to-chicago-howard-makes-history": """
            <html><head><title>Dream Scores a Win in Reese's Return to Chicago; Howard Makes History</title>
            <meta property="og:description" content="Atlanta Dream recap with official game action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661330/2026/06/Photo-6.11.png"></body></html>
        """,
        "https://dream.wnba.com/news/dream-falls-to-new-york-liberty-in-commissioners-cup-play": """
            <html><head><title>Dream Falls to New York Liberty in Commissioner's Cup Play</title>
            <meta property="og:description" content="Dream game recap with public action-photo context."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661330/2026/06/Rhyne-Howard.png"></body></html>
        """,
        "https://dream.wnba.com/news/dream-notches-first-ever-win-against-expansion-toronto-tempo": """
            <html><head><title>Dream Notches First-Ever Win Against Expansion Toronto Tempo</title>
            <meta property="og:description" content="Atlanta Dream game recap with transition action."></head>
            <body><img src="https://cdn.wnba.com/sites/1611661330/2026/06/thumb-300x78.jpg">
            <img src="https://cdn.wnba.com/sites/1611661330/2026/06/Story-Photo-6.14.png"></body></html>
        """,
        "https://dream.wnba.com/robots.txt": "User-agent: *\nAllow: /\n",
    }

    def fetcher(url: str):
        payload = page_payloads[url]
        return module.FetchedResponse(url=url, status=200, headers={"Content-Type": "text/html"}, body=payload.encode("utf-8"))

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_dream_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_dream_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_dream_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_dream_source_scout_ready"
    assert manifest["candidate_row_count"] == 4
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_recap_family"
    assert len(intake_rows) == 4
    assert len(board_rows) == 4
    assert {row["source_family_id"] for row in board_rows} == {"wnba_dream_official_game_recaps"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661330/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661330/2026/05/Untitled-22.png",
        "https://cdn.wnba.com/sites/1611661330/2026/06/Photo-6.11.png",
        "https://cdn.wnba.com/sites/1611661330/2026/06/Rhyne-Howard.png",
        "https://cdn.wnba.com/sites/1611661330/2026/06/Story-Photo-6.14.png",
    }
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in board_rows)
    assert all("-300x78." not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("matchup_or_recap_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 4
    assert "WNBA Dream Official Game Recap Source Scout V1" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 4
    assert deck_manifest["download_approved_default"] == "no"


def test_dream_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661330/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_dream_image_url("https://cdn.wnba.com/sites/1611661330/2026/06/thumb-300x78.jpg")
    assert not module.is_useful_dream_image_url("https://cdn.wnba.com/headshots/wnba/latest/260x190/1642822.png")
    assert module.is_useful_dream_image_url("https://cdn.wnba.com/sites/1611661330/2026/06/Story-Photo-6.14.png")
