from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_aces_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_aces_official_recaps_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_aces_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_aces_seed_csv_is_review_only_and_metadata_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("aces.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert "A'ja Wilson" in rows[0]["notes"]
    assert "review-only" in rows[0]["notes"].lower()


def test_aces_source_scout_builds_metadata_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_team_source_scout_v1"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_team_source_scout_v1"

    page_payloads = {
        "https://aces.wnba.com/news/game-recap-aja-wilson-hits-6k-career-points-in-101-91-las-vegas-victory-over-seattle": (
            200,
            """
            <html><head>
            <title>GAME RECAP: A'ja Wilson Hits 6K Career Points in 101-91 Las Vegas Victory Over Seattle</title>
            <meta property="og:title" content="GAME RECAP: A'ja Wilson Hits 6K Career Points in 101-91 Las Vegas Victory Over Seattle">
            <meta property="og:description" content="A'ja Wilson and Jackie Young combined for 63 points to help power the Aces.">
            <meta property="og:image" content="https://aces.wnba.com/images/aja-6k.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://aces.wnba.com/news/game-recap-aces-pull-out-nail-biting-100-97-victory-over-minnesota": (
            200,
            """
            <html><head>
            <title>GAME RECAP: Aces Pull Out Nail-Biting 100-97 Victory Over Minnesota</title>
            <meta property="og:title" content="GAME RECAP: Aces Pull Out Nail-Biting 100-97 Victory Over Minnesota">
            <meta property="og:description" content="A'ja Wilson finished with a 24-point, 10-rebound double-double in the Aces win.">
            <meta property="og:image" content="https://aces.wnba.com/images/minnesota-win.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://aces.wnba.com/news/game-recap-record-3-point-shooting-by-chelsea-gray-helps-aces-douse-fire-105-89": (
            200,
            """
            <html><head>
            <title>GAME RECAP: Record 3-Point Shooting by Chelsea Gray Helps Aces Douse Fire</title>
            <meta property="og:title" content="GAME RECAP: Record 3-Point Shooting by Chelsea Gray Helps Aces Douse Fire">
            <meta property="og:description" content="Chelsea Gray hit a franchise-record barrage from deep as Las Vegas beat Portland.">
            <meta property="og:image" content="https://aces.wnba.com/images/chelsea-gray-fire.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://aces.wnba.com/news/game-recap-las-vegas-lights-up-chicago-107-99": (
            200,
            """
            <html><head>
            <title>GAME RECAP: Aces Light Up the Sky 107-99</title>
            <meta property="og:title" content="GAME RECAP: Aces Light Up the Sky 107-99">
            <meta property="og:description" content="A'ja Wilson led the way and Jackie Young added secondary scoring for the Aces.">
            <meta property="og:image" content="https://aces.wnba.com/images/chicago-win.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://aces.wnba.com/news/game-recap-aces-unable-to-overcome-early-deficit-at-dallas-fall-96-66": (
            200,
            """
            <html><head>
            <title>Las Vegas Aces Unable to Overcome Early Deficit, Fall 96-66 at Dallas</title>
            <meta property="og:title" content="Las Vegas Aces Unable to Overcome Early Deficit, Fall 96-66 at Dallas">
            <meta property="og:description" content="Jewell Loyd led the Aces with a season-high 21 points.">
            <meta property="og:image" content="https://aces.wnba.com/images/jewell-loyd-dallas.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://aces.wnba.com/robots.txt": (403, "Forbidden"),
    }

    def fetcher(url: str):
        status, payload = page_payloads[url]
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        return module.FetchedResponse(url=url, status=status, headers={"Content-Type": "text/html"}, body=body)

    manifest = module.build_packet(
        seed_csv=SEED_CSV,
        output_dir=out_dir,
        latest_output_dir=latest_dir,
        fetcher=fetcher,
        sleep_fn=lambda _: None,
    )

    intake_rows = read_csv(out_dir / "wnba_aces_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_aces_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_aces_source_scout_report.md").read_text(encoding="utf-8")
    board_by_candidate = {row["candidate_queue_id"]: row for row in board_rows}

    assert manifest["status"] == "wnba_aces_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["robots_summary"] == "robots_txt_http_403_or_unavailable"
    assert manifest["auth_summary"] == "public_pages_reachable"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert board_by_candidate["WAFS001"]["source_family_id"] == "wnba_aces_official_recaps"
    assert board_by_candidate["WAFS001"]["candidate_quality_tier"] in {"A_primary_source_lead", "B_strong_source_lead"}
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Aces Source Scout V1" in report
    assert "Robots posture" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"
