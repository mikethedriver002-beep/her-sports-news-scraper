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
    / "review_only_action_photo_candidate_scout_official_source_expansion_v7.csv"
)
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_review_deck_official_source_expansion_v7.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_review_deck_official_source_expansion_v7", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_official_source_expansion_v7_seed_csv_is_review_only_and_purdue_soccer_official() -> None:
    rows = read_csv(SEED_CSV)

    assert len(rows) == 6
    assert len({row["seed_id"] for row in rows}) == len(rows)
    assert {row["source_type"] for row in rows} == {"official_team_recap"}
    assert {urlparse(row["source_page_url"]).netloc for row in rows} == {"purduesports.com"}
    assert all(row["operator_fair_use_asserted"] == "yes" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["rights_class"] == "official_school_athletics_site" for row in rows)
    assert all(row["intended_review_only_use"] == "review_only_action_photo_candidate_scout" for row in rows)
    assert all(
        row["quarantine_target_hint"].startswith(
            "data/assets/quarantine/review_only_candidates/action_photo_candidates/purdue_wsoc/"
        )
        for row in rows
    )
    assert any(row["identity_confidence"] == "medium" for row in rows)
    assert any(row["identity_confidence"] == "low" for row in rows)
    assert "named Megan Santa Cruz" in rows[0]["notes"]
    assert "review-only" in rows[0]["notes"].lower()


def write_official_expansion_v7_csv(path: Path) -> None:
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
                "entity_id": "purdue_wsoc_oregon_home_megan_santa_cruz",
                "source_type": "official_team_recap",
                "source_url": "https://purduesports.com/news/2025/08/29/soccer-wins-3-0-vs-oregon",
                "candidate_image_url": "https://purduesports.com/imgproxy/SEhpd0Bh_P35IBtHDM0dbwSnGjqEV3WIuafkGYLU_h0/rs:fit:1980:0:0:0/g:ce:0:0/q:90/aHR0cHM6Ly9zdG9yYWdlLmdvb2dsZWFwaXMuY29tL3B1cmR1ZXNwb3J0cy1jb20tcHJvZC8yMDI1LzEwLzAzL2R0WDdIaGpSb29VMFFTT2VPWG9obE9iaFEwZ1VnMTlZME5Vcm1nbEkuanBn.jpg",
                "image_alt": "Megan Santa Cruz is seen at the Purdue Women's Soccer match versus Oregon on Thursday, September 25th.",
                "source_domain": "purduesports.com",
                "identity_confidence": "medium",
                "face_likely_visible": "likely",
                "body_margin_likely": "possible",
                "four_by_five_crop_potential": "possible",
                "text_safe_negative_space": "likely",
                "download_approved": "no",
                "review_only": "true",
                "publish_ready": "false",
                "asset_downloads": "false",
                "approval_state_change": "false",
            }
        )


def test_official_source_expansion_v7_deck_wrapper_builds_review_only_decision_surface(tmp_path: Path) -> None:
    module = load_module()
    board_csv = tmp_path / "official_expansion_v7.csv"
    output_dir = tmp_path / "out"
    write_official_expansion_v7_csv(board_csv)

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
    assert manifest["version_wrapper"] == "hsd-action-photo-review-deck-official-source-expansion-v7-review-only"
    assert manifest["source_packet"] == "action_photo_official_source_expansion_v7"
    assert manifest["repo_head"] == "abc123"
    assert manifest["candidate_item_count"] == 1
    assert manifest["renderer_proof_item_count"] == 0
    assert manifest["download_approved_default"] == "no"
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False

    assert "APCS001" in html
    assert "purdue_wsoc_oregon_home_megan_santa_cruz" in html
    assert "Reject Wrong Person" in html
    assert "Reject Group Photo" in html
    assert "Carry Forward" in html

    assert len(rows) == 1
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["asset_downloads"] == "false"
