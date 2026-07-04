from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


REPO = Path(__file__).resolve().parents[1]
SEED_CSV = (
    REPO
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_official_source_expansion_v6.csv"
)
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_review_deck_official_source_expansion_v6.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_review_deck_official_source_expansion_v6", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_official_source_expansion_v6_seed_csv_is_review_only_and_honest_about_identity() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 6
    assert len({row["seed_id"] for row in rows}) == len(rows)
    assert {row["seed_id"] for row in rows} == {f"UCONNWBB{index:03d}" for index in range(1, 7)}

    for row in rows:
        assert urlparse(row["source_page_url"]).netloc == "uconnhuskies.com"
        assert row["source_type"] == "official_university_athletics_gallery"
        assert row["operator_fair_use_asserted"] == "yes"
        assert row["download_approved"] == "no"
        assert row["rights_class"] == "official_university_athletics_site"
        assert row["intended_review_only_use"] == "review_only_action_photo_candidate_scout"
        assert row["quarantine_target_hint"].startswith(
            "data/assets/quarantine/review_only_candidates/action_photo_candidates/uconn_wbb/"
        )

    named = {row["entity_id"]: row for row in rows if row["identity_confidence"] == "medium"}
    generic = {row["entity_id"]: row for row in rows if row["identity_confidence"] == "low"}

    assert set(named) == {"uconn_wbb_serah_williams_seton_hall", "uconn_wbb_st_johns_kelis_fisher"}
    assert set(generic) == {
        "uconn_wbb_notre_dame_gallery_action_001",
        "uconn_wbb_marquette_stock_fans",
        "uconn_wbb_georgetown_bench",
        "uconn_wbb_creighton_gallery_action",
    }
    assert "gallery" in generic["uconn_wbb_notre_dame_gallery_action_001"]["notes"].lower()
    assert "stock/fans" in generic["uconn_wbb_marquette_stock_fans"]["notes"].lower()
    assert "bench" in generic["uconn_wbb_georgetown_bench"]["notes"].lower()
    assert "generic" in generic["uconn_wbb_creighton_gallery_action"]["notes"].lower()


def write_official_expansion_v6_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "scout_candidate_id",
        "entity_id",
        "source_type",
        "source_url",
        "candidate_image_url",
        "image_alt",
        "source_domain",
        "identity_confidence",
        "face_likely_visible",
        "body_margin_likely",
        "four_by_five_crop_potential",
        "text_safe_negative_space",
        "download_approved",
        "review_only",
        "publish_ready",
        "asset_downloads",
        "approval_state_change",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "scout_candidate_id": "APCS001",
                "entity_id": "uconn_wbb_notre_dame_gallery_action_001",
                "source_type": "official_university_athletics_gallery",
                "source_url": "https://uconnhuskies.com/galleries/womens-basketball/wbb-vs-notre-dame/4695",
                "candidate_image_url": "https://uconnhuskies.com/images/2026/1/20/20260119_WBBvsNotreDame_02660.jpg",
                "image_alt": "WBB vs. Notre Dame Photo Gallery",
                "source_domain": "uconnhuskies.com",
                "identity_confidence": "low",
                "face_likely_visible": "likely",
                "body_margin_likely": "unclear",
                "four_by_five_crop_potential": "unlikely",
                "text_safe_negative_space": "likely",
                "download_approved": "no",
                "review_only": "true",
                "publish_ready": "false",
                "asset_downloads": "false",
                "approval_state_change": "false",
            }
        )


def test_official_source_expansion_v6_deck_wrapper_builds_review_only_decision_surface(tmp_path: Path) -> None:
    module = load_module()
    board_csv = tmp_path / "official_expansion_v6.csv"
    output_dir = tmp_path / "out"
    write_official_expansion_v6_csv(board_csv)

    assert module.main(
        [
            "--board-csv",
            board_csv.as_posix(),
            "--output-dir",
            output_dir.as_posix(),
            "--head-commit",
            "abc123",
        ]
    ) == 0

    html = (output_dir / "action_photo_review_deck.html").read_text(encoding="utf-8")
    rows = read_csv(output_dir / "manual_decision_export_template.csv")
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_review_deck_ui_ready"
    assert manifest["version_wrapper"] == "hsd-action-photo-review-deck-official-source-expansion-v6-review-only"
    assert manifest["source_packet"] == "action_photo_official_source_expansion_v6"
    assert manifest["repo_head"] == "abc123"
    assert manifest["candidate_item_count"] == 1
    assert manifest["renderer_proof_item_count"] == 0
    assert manifest["download_approved_default"] == "no"
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False

    assert "APCS001" in html
    assert "uconn_wbb_notre_dame_gallery_action_001" in html
    assert "Reject Wrong Person" in html
    assert "Reject Group Photo" in html
    assert "Carry Forward" in html

    assert len(rows) == 1
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["asset_downloads"] == "false"
