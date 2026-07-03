from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_review_deck_intake_adapter_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_review_deck_intake_adapter_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


DECISION_FIELDS = [
    "deck_item_id",
    "item_kind",
    "candidate_id",
    "entity_id",
    "source_url",
    "image_or_render_url",
    "operator_decision",
    "operator_notes",
    "manual_reviewer",
    "reviewed_at_utc",
    "formal_intake_next_action",
    "review_only",
    "download_approved",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

BOARD_FIELDS = [
    "board_id",
    "scout_candidate_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "source_domain",
    "candidate_board_recommendation",
    "identity_confidence",
]


def decision_row(**overrides: str) -> dict[str, str]:
    row = {
        "deck_item_id": "candidate_APCS039",
        "item_kind": "candidate_source",
        "candidate_id": "APCS039",
        "entity_id": "wnba_las_vegas_aces_jackie_young",
        "source_url": "https://aces.wnba.com/news/gallery-aces-sparks-6-2-2026",
        "image_or_render_url": "https://cdn.wnba.com/sites/1611661319/2026/06/20260602_Young_Tyler-Ross_NBAE_26.jpg",
        "operator_decision": "carry_forward_for_formal_intake",
        "operator_notes": "best vertical source",
        "manual_reviewer": "Mike",
        "reviewed_at_utc": "2026-07-03T13:00:00Z",
        "formal_intake_next_action": "",
        "review_only": "true",
        "download_approved": "no",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
    }
    row.update(overrides)
    return row


def board_row() -> dict[str, str]:
    return {
        "board_id": "APNB003",
        "scout_candidate_id": "APCS039",
        "entity_id": "wnba_las_vegas_aces_jackie_young",
        "source_type": "official_team_gallery",
        "source_url": "https://aces.wnba.com/news/gallery-aces-sparks-6-2-2026",
        "candidate_image_url": "https://cdn.wnba.com/sites/1611661319/2026/06/20260602_Young_Tyler-Ross_NBAE_26.jpg",
        "image_alt": "Aces 79, Sparks 69",
        "source_domain": "aces.wnba.com",
        "candidate_board_recommendation": "manual inspect",
        "identity_confidence": "high",
    }


def test_adapter_converts_carry_forward_to_formal_intake_without_download_approval(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "decisions.csv"
    board = tmp_path / "board.csv"
    output = tmp_path / "out"
    write_csv(decisions, [decision_row()], DECISION_FIELDS)
    write_csv(board, [board_row()], BOARD_FIELDS)

    manifest = module.build_packet(decisions_csv=decisions, board_csv=board, output_dir=output, head_commit="abc123")
    manifest_json = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    rows = read_csv(output / "formal_quarantine_download_intake_candidates.csv")
    rejected = read_csv(output / "rejected_or_held_review_deck_decisions.csv")

    assert manifest["status"] == "action_photo_review_deck_intake_adapter_ready"
    assert manifest_json["version"] == "hsd-action-photo-review-deck-intake-adapter-v1-review-only"
    assert manifest_json["repo_head"] == "abc123"
    assert manifest_json["formal_intake_rows"] == 1
    assert manifest_json["rejected_or_held_rows"] == 0
    assert manifest_json["invalid_rows"] == 0
    assert manifest_json["download_approved_default"] == "no"
    assert manifest_json["asset_downloads"] is False
    assert manifest_json["approval_state_change"] is False
    assert manifest_json["publish_ready"] is False
    assert manifest_json["publishing"] is False

    assert len(rows) == 1
    row = rows[0]
    assert row["candidate_queue_id"] == "APCS039"
    assert row["download_approved"] == "no"
    assert row["review_only"] == "true"
    assert row["publish_ready"] == "false"
    assert row["rights_class"] == "official_team_site"
    assert row["identity_confidence"] == "high"
    assert row["identity_anchor_url"].endswith("/jackie-young/profile")
    assert row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/")
    assert "separate human download approval" in row["notes"]
    assert rejected == []


def test_adapter_keeps_rejections_out_of_formal_intake(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "decisions.csv"
    board = tmp_path / "board.csv"
    output = tmp_path / "out"
    write_csv(decisions, [decision_row(operator_decision="reject_wrong_person", candidate_id="APCS088")], DECISION_FIELDS)
    write_csv(board, [board_row()], BOARD_FIELDS)

    module.build_packet(decisions_csv=decisions, board_csv=board, output_dir=output)
    rows = read_csv(output / "formal_quarantine_download_intake_candidates.csv")
    rejected = read_csv(output / "rejected_or_held_review_deck_decisions.csv")

    assert rows == []
    assert len(rejected) == 1
    assert rejected[0]["operator_decision"] == "reject_wrong_person"
    assert rejected[0]["download_approved"] == "no"


def test_adapter_blocks_truthy_download_approval_from_export(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "decisions.csv"
    board = tmp_path / "board.csv"
    output = tmp_path / "out"
    write_csv(decisions, [decision_row(download_approved="yes")], DECISION_FIELDS)
    write_csv(board, [board_row()], BOARD_FIELDS)

    module.build_packet(decisions_csv=decisions, board_csv=board, output_dir=output)
    rows = read_csv(output / "formal_quarantine_download_intake_candidates.csv")
    invalid = read_csv(output / "invalid_review_deck_decisions.csv")

    assert rows == []
    assert len(invalid) == 1
    assert "exported_decision_must_not_download_approve" in invalid[0]["validation_issues"]
