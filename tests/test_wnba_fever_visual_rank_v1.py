from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_fever_visual_rank_v1.py"
SOURCE_SCOUT_SCRIPT = REPO / "scripts" / "build_hsd_wnba_fever_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_fever_official_galleries_and_recaps_v1.csv"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_source_scout(tmp_path: Path) -> Path:
    source_module = load_module(SOURCE_SCOUT_SCRIPT, "build_hsd_wnba_fever_source_scout_for_visual_rank_test")
    out_dir = tmp_path / "source_scout"
    page_payloads = {
        "https://fever.wnba.com/news/game-recap-fever-sparks-260627": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Dominate Sparks in 111-87 Win</title>
            <meta property="og:description" content="Monique Billings, Aliyah Boston, Ty Harris and Kelsey Mitchell score 15+ each en route to victory.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/06/DSC_3367.jpg">
            </head></html>
            """,
        ),
        "https://fever.wnba.com/news/game-recap-fever-mercury-260624": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Fall to Phoenix Mercury</title>
            <meta property="og:description" content="Kelsey Mitchell leads Fever with 30-point game.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/06/DSC_2798.jpg">
            </head></html>
            """,
        ),
        "https://fever.wnba.com/news/game-recap-fever-sparks-260513": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Earns First Win of 2026 Season</title>
            <meta property="og:description" content="Fever best Sparks on the road backed by 20+ scoring performances from Clark and Mitchell.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/05/GettyImages-2275547501.jpg">
            </head></html>
            """,
        ),
        "https://fever.wnba.com/news/game-recap-fever-sky-260611": (
            200,
            """
            <html><head>
            <title>Game Recap: Indiana Fever Defeat Chicago Sky in Overtime Thriller</title>
            <meta property="og:description" content="Aliyah Boston and Caitlin Clark become the first pair of teammates in WNBA history to record double-doubles with 30+ points.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/06/PSE_2958.jpg">
            </head></html>
            """,
        ),
        "https://fever.wnba.com/news/boston-mitchell-power-fever-to-win-over-expansion-fire": (
            200,
            """
            <html><head>
            <title>Boston, Mitchell Power Fever to Win over Expansion Fire</title>
            <meta property="og:description" content="Aliyah Boston scored the first bucket and Kelsey Mitchell scored the second in a runaway win.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661325/2026/05/2GettyImages-2276752024.jpg">
            </head></html>
            """,
        ),
        "https://fever.wnba.com/robots.txt": (403, "Forbidden"),
    }

    def fetcher(url: str):
        status, payload = page_payloads[url]
        body = payload.encode("utf-8")
        return source_module.FetchedResponse(url=url, status=status, headers={"Content-Type": "text/html"}, body=body)

    source_module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, fetcher=fetcher, sleep_fn=lambda _: None)
    return out_dir


def test_visual_rank_builds_review_only_board_from_fever_scout(tmp_path: Path) -> None:
    source_dir = build_source_scout(tmp_path)
    module = load_module(SCRIPT, "build_hsd_wnba_fever_visual_rank_v1")
    out_dir = tmp_path / "visual_rank"

    manifest = module.build_packet(
        board_csv=source_dir / "wnba_fever_source_scout_board.csv",
        intake_csv=source_dir / "wnba_fever_source_scout_intake.csv",
        output_dir=out_dir,
    )

    board_rows = read_csv(out_dir / "wnba_fever_visual_rank_board.csv")
    intake_rows = read_csv(out_dir / "wnba_fever_visual_rank_intake.csv")
    html = (out_dir / "wnba_fever_visual_rank_board.html").read_text(encoding="utf-8")
    report = (out_dir / "wnba_fever_visual_rank_report.md").read_text(encoding="utf-8")
    manifest_from_disk = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "wnba_fever_visual_rank_ready"
    assert manifest_from_disk["row_count"] == 5
    assert {row["candidate_queue_id"] for row in board_rows} == {"WFFS001", "WFFS002", "WFFS003", "WFFS004", "WFFS005"}
    assert {row["candidate_queue_id"] for row in board_rows[:2]} == {"WFFS001", "WFFS002"}
    assert {row["candidate_queue_id"] for row in intake_rows} == {"WFFS001", "WFFS002", "WFFS003", "WFFS004", "WFFS005"}
    assert all(row["download_approved"] == "no" for row in board_rows)
    assert all(row["review_only"] == "true" for row in board_rows)
    assert all(row["asset_downloads"] == "false" for row in board_rows)
    assert all(row["publish_ready"] == "false" for row in board_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert manifest_from_disk["guardrails"]["no_downloads"] is True
    assert "WNBA Fever Visual Rank Board" in report
    assert "WFFS002" in html
    assert "https://cdn.wnba.com/" in html
    assert "download_approved=yes" not in html


def test_visual_rank_requires_all_five_fever_rows(tmp_path: Path) -> None:
    module = load_module(SCRIPT, "build_hsd_wnba_fever_visual_rank_missing_rows_test")
    board_csv = tmp_path / "board.csv"
    intake_csv = tmp_path / "intake.csv"
    board_csv.write_text("candidate_queue_id\nWFFS001\n", encoding="utf-8")
    intake_csv.write_text("candidate_queue_id\nWFFS001\n", encoding="utf-8")

    try:
        module.build_packet(board_csv=board_csv, intake_csv=intake_csv, output_dir=tmp_path / "out")
    except ValueError as exc:
        assert "Missing required Fever rows" in str(exc)
        assert "WFFS002" in str(exc)
    else:
        raise AssertionError("Expected missing Fever rows to fail fast")
