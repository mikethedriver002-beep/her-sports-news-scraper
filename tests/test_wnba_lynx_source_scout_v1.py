from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_lynx_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_lynx_photo_galleries_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_lynx_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_lynx_seed_csv_is_review_only_and_gallery_first() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 5
    assert {row["source_type"] for row in rows} == {"official_team_gallery"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["identity_confidence"] == "medium" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all("lynx.wnba.com/news/" in row["source_page_url"] for row in rows)
    assert all(row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/minnesota_lynx/") for row in rows)
    assert "review-only" in rows[0]["notes"].lower()


def test_lynx_source_scout_builds_metadata_rows_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_next_v1"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_next_v1"

    page_payloads = {
        "https://lynx.wnba.com/news/lynx-pics-lynx-defeat-wings-08-22-23": (
            200,
            """
            <html><head>
            <title>Lynx Pics: Lynx Defeat Wings | 08.22.23</title>
            <meta property="og:title" content="Lynx Pics: Lynx Defeat Wings | 08.22.23">
            <meta property="og:description" content="The Minnesota Lynx defeated the Dallas Wings in a photo gallery packed with action shots and celebration frames.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661324/2023/08/GettyImages-1617633096-185x148.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://lynx.wnba.com/news/lynx-pics-lynx-victory-over-storm-06-27-23": (
            200,
            """
            <html><head>
            <title>Lynx Pics: Lynx Victory Over Storm | 06.27.23</title>
            <meta property="og:title" content="Lynx Pics: Lynx Victory Over Storm | 06.27.23">
            <meta property="og:description" content="Minnesota and Seattle collide in a public photo gallery featuring game action, transition defense, and bench reactions.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661324/2023/06/GettyImages-1259142576-185x148.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://lynx.wnba.com/news/lynx-pics-lynx-fall-to-aces-07-22-23": (
            200,
            """
            <html><head>
            <title>Lynx Pics: Lynx Fall To Aces | 07.22.23</title>
            <meta property="og:title" content="Lynx Pics: Lynx Fall To Aces | 07.22.23">
            <meta property="og:description" content="A matchup gallery with tight court action and strong body-margin potential for manual review.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661324/2023/07/GettyImages-1547945026-185x148.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://lynx.wnba.com/news/lynx-pics-lynx-victory-over-sun-07-30-23": (
            200,
            """
            <html><head>
            <title>Lynx Pics: Lynx Victory Over Sun | 07.30.23</title>
            <meta property="og:title" content="Lynx Pics: Lynx Victory Over Sun | 07.30.23">
            <meta property="og:description" content="A gallery built around fast-break action, rim pressure, and clean review-only photo evidence.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661324/2023/07/GettyImages-1565685337-1-185x148.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://lynx.wnba.com/news/lynx-pics-lynx-fall-to-dream-07-18-23": (
            200,
            """
            <html><head>
            <title>Lynx Pics: Lynx Fall To Dream | 07.18.23</title>
            <meta property="og:title" content="Lynx Pics: Lynx Fall To Dream | 07.18.23">
            <meta property="og:description" content="Photo gallery with public action frames and enough context to judge the subject without downloads.">
            <meta property="og:image" content="https://cdn.wnba.com/sites/1611661324/2023/07/GettyImages-1541236078-1-185x148.jpg">
            </head><body>body</body></html>
            """,
        ),
        "https://lynx.wnba.com/robots.txt": (403, "Forbidden"),
    }

    def fetcher(url: str):
        status, payload = page_payloads[url]
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        return module.FetchedResponse(url=url, status=status, headers={"Content-Type": "text/html"}, body=body)

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir, fetcher=fetcher, sleep_fn=lambda _: None)

    intake_rows = read_csv(out_dir / "wnba_lynx_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_lynx_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_lynx_source_scout_report.md").read_text(encoding="utf-8")
    board_by_candidate = {row["candidate_queue_id"]: row for row in board_rows}

    assert manifest["status"] == "wnba_lynx_source_scout_ready"
    assert manifest["candidate_row_count"] == 5
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["robots_summary"] == "robots_txt_http_403_or_unavailable"
    assert manifest["auth_summary"] == "public_pages_reachable"
    assert len(intake_rows) == 5
    assert len(board_rows) == 5
    assert board_by_candidate["WLGS001"]["source_family_id"] == "wnba_lynx_official_photo_galleries"
    assert board_by_candidate["WLGS001"]["candidate_quality_tier"] in {"A_primary_source_lead", "B_strong_source_lead"}
    assert board_by_candidate["WLGS001"]["candidate_image_url"].endswith("GettyImages-1617633096.jpg")
    assert board_by_candidate["WLGS001"]["candidate_risk_flags"] == "subject_context_not_explicit|thumbnail_url_promoted_to_high_res"
    assert all("-185x148." not in row["candidate_image_url"] for row in board_rows)
    assert all("-185x148." not in row["candidate_photo_url"] for row in intake_rows)
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 5
    assert "WNBA Lynx Photo Gallery Source Scout V1" in report
    assert "Robots posture" in report
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 5
    assert deck_manifest["download_approved_default"] == "no"
