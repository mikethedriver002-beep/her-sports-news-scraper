from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_fever_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_fever_official_galleries_and_recaps_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_fever_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_fever_seed_csv_is_review_only_and_metadata_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_recap", "official_team_story"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "strong_context" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("fever.wnba.com/news/" in row["source_page_url"] for row in rows)


def test_fever_source_scout_builds_metadata_rows_and_review_deck(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_fever_source_scout_v1"

    page_payloads = {
        "https://fever.wnba.com/news/game-recap-fever-sparks-260627": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Dominate Sparks in 111-87 Win</title>
            <meta property="og:title" content="Game Recap: Indiana Fever Dominate Sparks in 111-87 Win">
            <meta property="og:description" content="Monique Billings, Aliyah Boston, Ty Harris and Kelsey Mitchell score 15+ each en route to victory.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/06/DSC_3367.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://fever.wnba.com/news/game-recap-fever-mercury-260624": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Fall to Phoenix Mercury</title>
            <meta property="og:title" content="Game Recap: Indiana Fever Fall to Phoenix Mercury">
            <meta property="og:description" content="Kelsey Mitchell leads Fever with 30-point game.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/06/DSC_2798.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://fever.wnba.com/news/game-recap-fever-sparks-260513": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Earns First Win of 2026 Season</title>
            <meta property="og:title" content="Game Recap: Indiana Fever Earns First Win of 2026 Season">
            <meta property="og:description" content="Fever best Sparks on the road backed by 20+ scoring performances from Clark and Mitchell.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/05/GettyImages-2275547501.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://fever.wnba.com/news/game-recap-fever-sky-260611": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Defeat Chicago Sky in Overtime Thriller</title>
            <meta property="og:title" content="Game Recap: Indiana Fever Defeat Chicago Sky in Overtime Thriller">
            <meta property="og:description" content="Aliyah Boston and Caitlin Clark become the first pair of teammates in WNBA history to record double-doubles with 30+ points.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/06/PSE_2958.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://fever.wnba.com/news/boston-mitchell-power-fever-to-win-over-expansion-fire": (
            200,
            """
            <html><head>
            <title>Boston, Mitchell Power Fever to Win over Expansion Fire</title>
            <meta property="og:title" content="Boston, Mitchell Power Fever to Win over Expansion Fire">
            <meta property="og:description" content="Aliyah Boston scored the first bucket and Kelsey Mitchell scored the second in a runaway win.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/05/2GettyImages-2276752024.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://fever.wnba.com/robots.txt": (403, "Forbidden"),
    }

    def fetcher(url: str):
        status, payload = page_payloads[url]
        if isinstance(payload, bytes):
            body = payload
        else:
            body = payload.encode("utf-8")
        return module.FetchedResponse(url=url, status=status, headers={"Content-Type": "text/html"}, body=body)

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_fever_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_fever_source_scout_board.csv")
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_fever_source_scout_report.md").read_text(encoding="utf-8")
    board_by_candidate = {row["candidate_queue_id"]: row for row in board_rows}

    assert manifest["status"] == "wnba_fever_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["robots_summary"] == "robots_txt_http_403_or_unavailable"
    assert manifest["auth_summary"] == "public_pages_reachable"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert board_by_candidate["WFFS001"]["source_family_id"] == "wnba_fever_official_galleries_and_recaps"
    assert board_by_candidate["WFFS001"]["candidate_quality_tier"] in {"A_primary_source_lead", "B_strong_source_lead"}
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert "WNBA Fever Source Scout V1" in report
    assert "Robots posture" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"
