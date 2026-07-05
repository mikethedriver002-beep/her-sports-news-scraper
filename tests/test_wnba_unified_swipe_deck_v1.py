from __future__ import annotations

import base64
import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_unified_swipe_deck_v1.py"
EMPTY_MANUAL_DECISION_FIELDS = [
    "candidate_id",
    "entity_id",
    "operator_decision",
    "review_only",
    "download_approved",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

MINI_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/qK0AAAAASUVORK5CYII="
)


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


def write_board_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def write_empty_manual_decisions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EMPTY_MANUAL_DECISION_FIELDS)
        writer.writeheader()


def write_manual_decisions(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EMPTY_MANUAL_DECISION_FIELDS)
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


def write_latest_inputs(root: Path, image_url: str) -> None:
    write_board_csv(
        root / "wnba_fever_visual_rank_v1" / "wnba_fever_visual_rank_board.csv",
        [
            source_row(
                "WFFS001",
                "indiana_fever_kelsey_mitchell",
                "wnba_fever_official_galleries_and_recaps",
                image_url,
                "100",
            )
        ],
    )
    write_board_csv(
        root / "wnba_storm_visual_rank_v1" / "wnba_storm_visual_rank_board.csv",
        [
            source_row(
                "WSFS001",
                "wnba_seattle_storm_skylar_diggins",
                "wnba_storm_official_recaps",
                image_url,
                "99",
            )
        ],
    )
    write_board_csv(
        root / "wnba_official_team_source_scout_v1" / "wnba_aces_source_scout_board.csv",
        [
            source_row(
                "WAFS001",
                "wnba_las_vegas_aces_aja_wilson",
                "wnba_aces_official_recaps",
                image_url,
                "98",
            )
        ],
    )


def test_unified_swipe_deck_caches_file_uri_previews_and_preserves_provenance(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "latest" / "files"
    output_dir = tmp_path / "out"
    latest_output_dir = tmp_path / "mirror" / "wnba_unified_swipe_deck_v1"
    manual_decisions = tmp_path / "manual_decisions" / "normalized_review_deck_decisions.csv"
    image_path = tmp_path / "preview source.png"
    image_path.write_bytes(MINI_PNG_BYTES)
    write_latest_inputs(latest_root, image_path.as_uri())
    write_empty_manual_decisions(manual_decisions)

    module.build_packet(
        latest_files_root=latest_root,
        output_dir=output_dir,
        latest_output_dir=latest_output_dir,
        manual_decisions_csv=manual_decisions,
        preview_fetcher=module.fetch_preview_bytes,
    )

    rows = read_csv(output_dir / "wnba_unified_swipe_deck_input.csv")
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "wnba_unified_swipe_deck_report.md").read_text(encoding="utf-8")

    assert module.fetch_preview_bytes(image_path.as_uri()) == MINI_PNG_BYTES
    assert manifest["preview_cache_only"] is True
    assert manifest["candidate_downloads"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["download_approved"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["deck_item_count"] == 3
    assert manifest["suppressed_reviewed_candidates"] == 0
    assert manifest["latest_mirror_built"] is True
    assert manifest["latest_mirror_errors"] == []
    assert rows[0]["candidate_image_remote_url"].startswith("file:///")
    assert rows[0]["candidate_image_url"].startswith("file:///")
    assert rows[0]["preview_cache_status"] == "cached"
    assert rows[0]["preview_cache_only"] == "true"
    assert rows[0]["candidate_downloads"] == "false"
    assert Path(rows[0]["preview_cache_path"]).exists()
    assert "preview_cache_only=true" in report
    assert "No WNBA swipe cards remain" not in (output_dir / "review_deck" / "action_photo_review_deck.html").read_text(encoding="utf-8")


def test_unified_swipe_deck_suppresses_exact_reviewed_candidate_entity_pairs(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "latest" / "files"
    output_dir = tmp_path / "out"
    manual_decisions = tmp_path / "manual_decisions" / "normalized_review_deck_decisions.csv"
    image_path = tmp_path / "source.png"
    image_path.write_bytes(MINI_PNG_BYTES)

    write_board_csv(
        latest_root / "wnba_fever_visual_rank_v1" / "wnba_fever_visual_rank_board.csv",
        [
            source_row(
                "WFFS010",
                "indiana_fever_kelsey_mitchell",
                "wnba_fever_official_galleries_and_recaps",
                image_path.as_uri(),
                "100",
            ),
            source_row(
                "WFFS010",
                "indiana_fever_abby_myers",
                "wnba_fever_official_galleries_and_recaps",
                image_path.as_uri(),
                "99",
            ),
        ],
    )
    write_manual_decisions(
        manual_decisions,
        [
            {
                "candidate_id": "WFFS010",
                "entity_id": "indiana_fever_kelsey_mitchell",
                "operator_decision": "reject_wrong_person",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        ],
    )

    manifest = module.build_packet(
        latest_files_root=latest_root,
        output_dir=output_dir,
        latest_output_dir=None,
        manual_decisions_csv=manual_decisions,
        preview_fetcher=module.fetch_preview_bytes,
    )

    rows = read_csv(output_dir / "wnba_unified_swipe_deck_input.csv")
    deck_html = (output_dir / "review_deck" / "action_photo_review_deck.html").read_text(encoding="utf-8")

    assert manifest["deck_item_count"] == 1
    assert manifest["suppressed_reviewed_candidates"] == 1
    assert len(rows) == 1
    assert rows[0]["candidate_queue_id"] == "WFFS010"
    assert rows[0]["entity_id"] == "indiana_fever_abby_myers"
    assert rows[0]["candidate_image_remote_url"].startswith("file:///")
    assert rows[0]["candidate_image_url"].startswith("file:///")
    assert "WFFS010" in deck_html
    assert "indiana_fever_kelsey_mitchell" not in deck_html


def test_unified_swipe_deck_creates_empty_deck_after_full_suppression(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "latest" / "files"
    output_dir = tmp_path / "out"
    manual_decisions = tmp_path / "manual_decisions" / "normalized_review_deck_decisions.csv"
    image_path = tmp_path / "empty deck.png"
    image_path.write_bytes(MINI_PNG_BYTES)
    write_latest_inputs(latest_root, image_path.as_uri())
    write_manual_decisions(
        manual_decisions,
        [
            {
                "candidate_id": "WFFS001",
                "entity_id": "indiana_fever_kelsey_mitchell",
                "operator_decision": "reject_wrong_person",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            },
            {
                "candidate_id": "WSFS001",
                "entity_id": "wnba_seattle_storm_skylar_diggins",
                "operator_decision": "hold_manual_check",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            },
            {
                "candidate_id": "WAFS001",
                "entity_id": "wnba_las_vegas_aces_aja_wilson",
                "operator_decision": "carry_forward_for_formal_intake",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            },
        ],
    )

    manifest = module.build_packet(
        latest_files_root=latest_root,
        output_dir=output_dir,
        latest_output_dir=None,
        manual_decisions_csv=manual_decisions,
        preview_fetcher=module.fetch_preview_bytes,
    )

    html = (output_dir / "review_deck" / "action_photo_review_deck.html").read_text(encoding="utf-8")
    report = (output_dir / "wnba_unified_swipe_deck_report.md").read_text(encoding="utf-8")
    decision_rows = read_csv(output_dir / "review_deck" / "manual_decision_export_template.csv")

    assert manifest["deck_item_count"] == 0
    assert manifest["candidate_item_count"] == 0
    assert manifest["suppressed_reviewed_candidates"] == 3
    assert "No WNBA swipe cards remain" in html
    assert "empty review deck" in report.lower()
    assert decision_rows == []


def test_unified_swipe_deck_uses_explicit_latest_inputs_in_isolation(tmp_path: Path) -> None:
    module = load_module()
    latest_root = tmp_path / "isolated" / "latest" / "files"
    output_dir = tmp_path / "out"
    latest_output_dir = tmp_path / "mirror" / "wnba_unified_swipe_deck_v1"
    manual_decisions = tmp_path / "isolated_manual" / "normalized_review_deck_decisions.csv"
    image_path = tmp_path / "isolation.png"
    image_path.write_bytes(MINI_PNG_BYTES)
    write_latest_inputs(latest_root, image_path.as_uri())
    write_empty_manual_decisions(manual_decisions)

    manifest = module.build_packet(
        latest_files_root=latest_root,
        output_dir=output_dir,
        latest_output_dir=latest_output_dir,
        manual_decisions_csv=manual_decisions,
        preview_fetcher=module.fetch_preview_bytes,
    )

    assert manifest["latest_files_root"] == latest_root.resolve(strict=False).as_posix()
    assert manifest["manual_decisions_csv"] == manual_decisions.resolve(strict=False).as_posix()
    assert all(path.startswith(latest_root.resolve(strict=False).as_posix()) for path in manifest["source_paths"].values())
    assert manifest["latest_mirror_built"] is True
    assert manifest["latest_mirror_errors"] == []
