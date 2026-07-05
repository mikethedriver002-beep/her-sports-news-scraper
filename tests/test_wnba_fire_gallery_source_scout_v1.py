from __future__ import annotations

import csv
import json
import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_fire_gallery_source_scout_v1.py"
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_fire_photo_gallery_v1.csv"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_fire_gallery_source_scout_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_fire_gallery_seed_csv_is_review_only_and_high_res_gallery_forward() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 4
    assert {row["source_type"] for row in rows} == {"official_team_gallery"}
    assert all(row["source_page_url"] == "https://fire.wnba.com/news/gallery-fire-vs-sky-5-9-2026" for row in rows)
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_review_needed" for row in rows)
    assert all(row["intended_review_only_use"] == "wnba_source_quality_metadata_only" for row in rows)
    assert all(row["candidate_image_url"].startswith("https://cdn.wnba.com/sites/1611661327/2026/05/") for row in rows)
    assert all("-185x148." not in row["candidate_image_url"] for row in rows)
    assert all("-260x190." not in row["candidate_image_url"] for row in rows)
    assert all("-300x78." not in row["candidate_image_url"] for row in rows)
    assert "review-only" in rows[0]["notes"].lower()
    assert rows[-1]["candidate_image_url"].endswith("PF_Home-Opener_news-card-1.png")


def test_fire_gallery_source_scout_builds_review_deck_and_latest_mirror(tmp_path: Path) -> None:
    module = load_module()
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v12"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v12"

    manifest = module.build_packet(seed_csv=SEED_CSV, output_dir=out_dir, latest_output_dir=latest_dir)

    intake_rows = read_csv(out_dir / "wnba_fire_gallery_source_scout_intake.csv")
    board_rows = read_csv(out_dir / "wnba_fire_gallery_source_scout_board.csv")
    latest_manifest = json.loads((latest_dir / "manifest.json").read_text(encoding="utf-8"))
    deck_manifest = json.loads((out_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "wnba_fire_gallery_source_scout_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_fire_gallery_source_scout_ready"
    assert manifest["candidate_row_count"] == 4
    assert manifest["deck_built"] is True
    assert manifest["latest_mirror_built"] is True
    assert manifest["thumbnail_suffix_count"] == 0
    assert manifest["high_res_gallery_frame_count"] == 3
    assert manifest["source_family_usefulness_verdict"] == "useful_high_res_official_gallery_family"
    assert len(intake_rows) == 4
    assert len(board_rows) == 4
    assert {row["source_family_id"] for row in board_rows} == {"wnba_portland_fire_photo_gallery"}
    assert all(row["download_approved"] == "no" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["review_only"] == "true" for row in board_rows)
    assert any("high_res_gallery_frame" in row["candidate_risk_flags"] for row in board_rows)
    assert any("branded_tile_not_action_frame" in row["candidate_risk_flags"] for row in board_rows)
    assert latest_manifest["latest_mirror_built"] is True
    assert latest_manifest["candidate_row_count"] == 4
    assert "WNBA Fire Gallery Source Scout V1" in report
    assert "thumbnail suffix count" in report.lower()
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["candidate_item_count"] == 4
    assert deck_manifest["download_approved_default"] == "no"

