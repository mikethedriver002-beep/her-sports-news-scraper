from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_wings_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_wings_official_recaps_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_wings_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_wings_seed_csv_is_review_only_and_highres_source_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("wings.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["entity_id"].startswith("wnba_dallas_wings_") for row in rows)
    assert all("dallas_wings" in row["quarantine_target_hint"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_wings_source_scout_builds_highres_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v7"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v7"

    page_payloads = {
        "https://wings.wnba.com/news/wings-start-road-trip-with-86-83-win-at-connecticut": (
            200,
            """
            <html><head>
            <title>Wings Start Road Trip with 86-83 Win at Connecticut</title>
            <meta property="og:title" content="Wings Start Road Trip with 86-83 Win at Connecticut">
            <meta property="og:description" content="Dallas opens the road trip with a public official recap and strong action-photo evidence.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661321/2026/07/GettyImages-2283826447-scaled.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://wings.wnba.com/news/wings-drop-home-game-to-lynx-85-77": (
            200,
            """
            <html><head>
            <title>Wings Drop Home Game to Lynx, 85-77</title>
            <meta property="og:title" content="Wings Drop Home Game to Lynx, 85-77">
            <meta property="og:description" content="Dallas Wings recap with a public high-resolution image for review-only scouting.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2283230020-scaled.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://wings.wnba.com/news/wings-drop-road-game-to-aces-99-85": (
            200,
            """
            <html><head>
            <title>Wings Drop Road Game to Aces, 99-85</title>
            <meta property="og:title" content="Wings Drop Road Game to Aces, 99-85">
            <meta property="og:description" content="The official page exposes a clean public CDN image without a thumbnail suffix.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2283490944-scaled.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://wings.wnba.com/news/wings-make-history-in-overtime-win-over-storm": (
            200,
            """
            <html><head>
            <title>Wings Make History in Overtime Win over Storm</title>
            <meta property="og:title" content="Wings Make History in Overtime Win over Storm">
            <meta property="og:description" content="Dallas Wings official recap with high-res match action and no approval-state changes.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2282342447-scaled.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://wings.wnba.com/news/wings-rally-to-defeat-sky-93-92": (
            200,
            """
            <html><head>
            <title>Wings Rally to Defeat Sky, 93-92</title>
            <meta property="og:title" content="Wings Rally to Defeat Sky, 93-92">
            <meta property="og:description" content="Dallas keeps a public recap with a reachable CDN image and strong crop potential.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2282055567-scaled.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://wings.wnba.com/robots.txt": (200, "User-agent: *\nAllow: /\n"),
    }

    def fetcher(url: str):
        status, payload = page_payloads[url]
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        return module.FetchedResponse(url=url, status=status, headers={"Content-Type": "text/html"}, body=body)

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_wings_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_wings_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_wings_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_wings_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_recap_family"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert {row["source_family_id"] for row in board_rows} == {"wnba_wings_official_game_recaps"}
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661321/2026/") for row in board_rows)
    assert {row["candidate_image_url"] for row in board_rows} == {
        "https://cdn.wnba.com/sites/1611661321/2026/07/GettyImages-2283826447-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2283230020-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2283490944-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2282342447-scaled.jpg",
        "https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2282055567-scaled.jpg",
    }
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["identity_confidence"] == "medium" for row in board_rows)
    assert all("matchup_level_identity_only" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Wings Official Game Recap Source Scout V1" in report
    assert "Robots posture" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"


def test_wings_image_filter_rejects_tiny_thumbnail_suffixes() -> None:
    module = load_module()

    assert module.is_tiny_thumbnail_url("https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-1-185x148.jpg")
    assert not module.is_useful_wings_image_url("https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-1-185x148.jpg")
    assert module.is_useful_wings_image_url("https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2282055567-scaled.jpg")
    assert module.canonical_image_url("https://cdn.wnba.com/sites/1611661321/2026/06/GettyImages-2282055567-scaled.jpg?foo=bar").endswith(
        "GettyImages-2282055567-scaled.jpg"
    )
