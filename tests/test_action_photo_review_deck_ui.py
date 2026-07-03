from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_review_deck_ui_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_review_deck_ui_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_board(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "board_id",
        "scout_candidate_id",
        "entity_id",
        "source_type",
        "source_url",
        "candidate_image_url",
        "image_alt",
        "source_domain",
        "visual_priority",
        "candidate_quality_tier",
        "score",
        "candidate_risk_flags",
        "face_likely_visible",
        "body_margin_likely",
        "four_by_five_crop_potential",
        "text_safe_negative_space",
        "identity_confidence",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "board_id": "APNB001",
                "scout_candidate_id": "APCS039",
                "entity_id": "wnba_las_vegas_aces_jackie_young",
                "source_type": "official_team_gallery",
                "source_url": "https://aces.example/gallery",
                "candidate_image_url": "https://cdn.example/apcs039.jpg",
                "image_alt": "Aces action",
                "source_domain": "aces.example",
                "visual_priority": "P1_visual_review_now",
                "candidate_quality_tier": "A_minus_manual_inspect",
                "score": "35",
                "candidate_risk_flags": "body_margin_unclear",
                "face_likely_visible": "likely",
                "body_margin_likely": "unclear",
                "four_by_five_crop_potential": "possible",
                "text_safe_negative_space": "possible",
                "identity_confidence": "high",
            }
        )


def write_manifest(path: Path, proof_png: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_image_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg",
        "proof_rows": [
            {
                "proof_id": "proof_01_vertical_score_anchor",
                "proof_name": "Vertical Score Anchor",
                "output_png_path": proof_png.as_posix(),
                "visual_strength": "strongest_jackie_young_social_proof",
                "known_limit": "download approval is not asset approval",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_review_deck_builds_candidate_and_proof_items(tmp_path: Path) -> None:
    module = load_module()
    board = tmp_path / "board.csv"
    proof = tmp_path / "proof.png"
    manifest = tmp_path / "manifest.json"
    output = tmp_path / "out"
    proof.write_bytes(b"not-used-by-generator")
    write_board(board)
    write_manifest(manifest, proof)

    payload = module.build_packet(board_csv=board, proof_manifest=manifest, output_dir=output, limit=10, head_commit="abc123")

    html = (output / "action_photo_review_deck.html").read_text(encoding="utf-8")
    rows = read_csv(output / "manual_decision_export_template.csv")
    manifest_json = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    assert payload["status"] == "action_photo_review_deck_ui_ready"
    assert manifest_json["version"] == "hsd-action-photo-review-deck-ui-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["candidate_item_count"] == 1
    assert manifest_json["renderer_proof_item_count"] == 1
    assert manifest_json["deck_item_count"] == 2
    assert manifest_json["download_approved_default"] == "no"
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False

    assert "Reject Wrong Person" in html
    assert "Reject Bad Crop" in html
    assert "Reject Group Photo" in html
    assert "Carry Forward" in html
    assert 'id="swipe-card"' in html
    assert "applySwipeDecision" in html
    assert "pointerdown" in html
    assert "pointermove" in html
    assert "ArrowLeft" in html
    assert "ArrowRight" in html
    assert "Clear Decision" in html
    assert 'id="progress-fill"' in html
    assert "Export Decision CSV" in html
    assert "Copy CSV" in html
    assert "Download CSV Again" in html
    assert 'id="csv-output"' in html
    assert 'id="export-status"' in html
    assert "buildCsvText" in html
    assert "showCsvFallback" in html
    assert "download_approved: \"no\"" in html
    assert "APCS039" in html
    assert "proof_01_vertical_score_anchor" in html

    assert len(rows) == 2
    assert all(row["operator_decision"] == "" for row in rows)
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
