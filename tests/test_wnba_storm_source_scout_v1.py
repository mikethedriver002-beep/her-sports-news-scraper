from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_storm_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_storm_official_recaps_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_storm_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_storm_seed_csv_is_review_only_and_metadata_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("storm.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert "Skylar Diggins" in rows[0]["notes"]
    assert "review-only" in rows[0]["notes"].lower()


def test_storm_source_scout_builds_metadata_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_next_v1"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_next_v1"

    page_payloads = {
        "https://storm.wnba.com/news/game-27-seattle-connecticut-101-85": (
            200,
            """
            <html><head>
            <title>Game 27: Seattle @ Connecticut, 101-85</title>
            <meta property="og:title" content="Game 27: Seattle @ Connecticut, 101-85">
            <meta property="og:description" content="Skylar Diggins logged 11 points, 11 assists and 12 rebounds for the first regular season triple-double of her career. Nneka Ogwumike poured in 26 points.">
            <meta property="og:image" content="https://storm.wnba.com/images/game27.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://storm.wnba.com/news/2025-wnba-playoffs-round-1-game-2-seattle-vs-las-vegas-86-83": (
            200,
            """
            <html><head>
            <title>2025 WNBA Playoffs: Round 1 Game 2: Seattle vs Las Vegas, 86-83</title>
            <meta property="og:title" content="2025 WNBA Playoffs: Round 1 Game 2: Seattle vs Las Vegas, 86-83">
            <meta property="og:description" content="Skylar Diggins finished with a playoff career high 26 points; Nneka Ogwumike had 24 points and 10 rebounds; Dominique Malonga posted a double-double; Erica Wheeler tallied 11 in the fourth.">
            <meta property="og:image" content="https://storm.wnba.com/images/playoffs-game2.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://storm.wnba.com/news/game-31-seattle-las-vegas-90-86": (
            200,
            """
            <html><head>
            <title>Game 31: Seattle @ Las Vegas, 90-86</title>
            <meta property="og:title" content="Game 31: Seattle @ Las Vegas, 90-86">
            <meta property="og:description" content="Dominique Malonga's first-year success continued as Seattle closed out another tight game in Las Vegas.">
            <meta property="og:image" content="https://storm.wnba.com/images/game31.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://storm.wnba.com/news/game-42-seattle-vs-los-angeles-91-85": (
            200,
            """
            <html><head>
            <title>Game 42: Seattle vs Los Angeles, 91-85</title>
            <meta property="og:title" content="Game 42: Seattle vs Los Angeles, 91-85">
            <meta property="og:description" content="Gabby Williams came up with two more steals for the Storm, helping Seattle win another close one.">
            <meta property="og:image" content="https://storm.wnba.com/images/game42.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://storm.wnba.com/news/game-7-storm-vs-aces-75-70": (
            200,
            """
            <html><head>
            <title>Game 7: Storm vs Aces, 75-70</title>
            <meta property="og:title" content="Game 7: Storm vs Aces, 75-70">
            <meta property="og:description" content="Erica Wheeler and the Storm kept the public recap image strong and the action context clear.">
            <meta property="og:image" content="https://storm.wnba.com/images/game7.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://storm.wnba.com/robots.txt": (403, "Forbidden"),
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

    intake_rows = read_csv(out_dir / "wnba_storm_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_storm_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_storm_source_scout_report.md").read_text(encoding="utf-8")
    board_by_candidate = {row["candidate_queue_id"]: row for row in board_rows}

    assert manifest["status"] == "wnba_storm_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["robots_summary"] == "robots_txt_http_403_or_unavailable"
    assert manifest["auth_summary"] == "public_pages_reachable"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert board_by_candidate["WSFS001"]["source_family_id"] == "wnba_storm_official_recaps"
    assert board_by_candidate["WSFS001"]["candidate_quality_tier"] in {"A_primary_source_lead", "B_strong_source_lead"}
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Storm Source Scout V1" in report
    assert "Robots posture" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"
