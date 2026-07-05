from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_unified_swipe_deck_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_unified_swipe_deck_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_row(candidate: str, entity: str, family: str, image_url: str, score: str = "99") -> dict[str, str]:
    return {
        "board_rank": "1",
        "candidate_queue_id": candidate,
        "seed_id": candidate.replace("FS", ""),
        "entity_id": entity,
        "source_type": "official_team_recap",
        "source_url": f"https://example.com/{candidate.lower()}",
        "candidate_image_url": image_url,
        "image_alt": f"{entity} action frame",
        "source_domain": "example.com",
        "source_family_id": family,
        "visual_rank_score": score,
        "score": score,
        "candidate_quality_tier": "A_primary_source_lead",
        "source_scout_tier": "A_primary_source_lead",
        "identity_confidence": "strong_context",
        "source_provenance_clarity": "clear",
        "candidate_risk_flags": "none",
        "face_likely_visible": "possible",
        "body_margin_likely": "possible",
        "four_by_five_crop_potential": "possible",
        "text_safe_negative_space": "possible",
        "manual_next_action": "manual inspect only",
        "download_approved": "no",
        "review_only": "true",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
        "notes": "review-only WNBA test row",
    }


def write_latest_inputs(root: Path) -> None:
    write_csv(
        root / "wnba_fever_visual_rank_v1" / "wnba_fever_visual_rank_board.csv",
        [
            source_row(
                "WFFS001",
                "indiana_fever_kelsey_mitchell",
                "wnba_fever_official_galleries_and_recaps",
                "https://cdn.wnba.com/fever.jpg",
                "100",
            )
        ],
    )
    write_csv(
        root / "wnba_storm_visual_rank_v1" / "wnba_storm_visual_rank_board.csv",
        [
            source_row(
                "WSFS001",
                "wnba_seattle_storm_skylar_diggins",
                "wnba_storm_official_recaps",
                "https://cdn.wnba.com/storm.jpg",
                "99",
            )
        ],
    )
    write_csv(
        root / "wnba_official_team_source_scout_v1" / "wnba_aces_source_scout_board.csv",
        [
            source_row(
                "WAFS001",
                "wnba_las_vegas_aces_aja_wilson",
                "wnba_aces_official_recaps",
                "https://cdn.wnba.com/aces.jpg",
                "98",
            )
        ],
    )


def test_unified_swipe_deck_builds_single_tinder_surface(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "outputs" / "local" / "latest" / "files"
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_unified_swipe_deck_v1"
    latest_output_dir = tmp_path / "latest_mirror" / "wnba_unified_swipe_deck_v1"
    write_latest_inputs(latest_root)

    manifest = module.build_packet(
        latest_files_root=latest_root,
        output_dir=output_dir,
        latest_output_dir=latest_output_dir,
    )

    combined_rows = read_csv(output_dir / "wnba_unified_swipe_deck_input.csv")
    decision_rows = read_csv(output_dir / "review_deck" / "manual_decision_export_template.csv")
    deck_manifest = json.loads((output_dir / "review_deck" / "manifest.json").read_text(encoding="utf-8"))
    latest_manifest = json.loads((latest_output_dir / "manifest.json").read_text(encoding="utf-8"))
    html = (output_dir / "review_deck" / "action_photo_review_deck.html").read_text(encoding="utf-8")
    report = (output_dir / "wnba_unified_swipe_deck_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "wnba_unified_swipe_deck_ready"
    assert manifest["deck_item_count"] == 3
    assert manifest["candidate_item_count"] == 3
    assert manifest["renderer_proof_item_count"] == 0
    assert manifest["latest_mirror_built"] is True
    assert manifest["download_approved"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["source_counts"] == {
        "wnba_fever_visual_rank": 1,
        "wnba_storm_visual_rank": 1,
        "wnba_aces_source_scout": 1,
    }
    assert latest_manifest["latest_mirror_built"] is True
    assert deck_manifest["status"] == "action_photo_review_deck_ui_ready"
    assert deck_manifest["deck_item_count"] == 3
    assert deck_manifest["download_approved_default"] == "no"
    assert [row["candidate_queue_id"] for row in combined_rows] == ["WFFS001", "WSFS001", "WAFS001"]
    assert all(row["download_approved"] == "no" for row in combined_rows)
    assert all(row["review_only"] == "true" for row in combined_rows)
    assert all(row["publish_ready"] == "false" for row in combined_rows)
    assert all(row["download_approved"] == "no" for row in decision_rows)
    assert all(row["review_only"] == "true" for row in decision_rows)
    assert "swipe-card" in html
    assert "pointerdown" in html
    assert "ArrowLeft" in html
    assert "ArrowRight" in html
    assert "Export Decision CSV" in html
    assert "WFFS001" in html and "WSFS001" in html and "WAFS001" in html
    forbidden_download_flag = "download_approved" + "=" + "yes"
    assert forbidden_download_flag not in html
    assert "Tinder-style manual review surface" in report


def test_unified_swipe_deck_fails_without_rows(tmp_path: Path) -> None:
    module = load_module()
    try:
        module.build_packet(
            latest_files_root=tmp_path / "missing",
            output_dir=tmp_path / "out",
            latest_output_dir=None,
        )
    except ValueError as exc:
        assert "No WNBA rows found" in str(exc)
    else:
        raise AssertionError("Expected missing WNBA rows to fail fast")
