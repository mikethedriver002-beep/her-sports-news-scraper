from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_manual_decision_batch_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_manual_decision_batch_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_decisions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "deck_item_id": "candidate_APCS001",
                "item_kind": "candidate_source",
                "candidate_id": "APCS001",
                "entity_id": "wll_new_york_charging_madison_doucette",
                "source_url": "https://premierlacrosseleague.com/articles/example",
                "image_or_render_url": "https://cdn.example.com/madison-action.jpg",
                "operator_decision": "carry_forward_for_formal_intake",
                "operator_notes": "strong solo action",
                "manual_reviewer": "Mike",
                "reviewed_at_utc": "2026-07-03T00:00:00Z",
                "formal_intake_next_action": "prepare_separate_formal_quarantine_download_intake",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
        writer.writerow(
            {
                "deck_item_id": "candidate_APCS002",
                "item_kind": "candidate_source",
                "candidate_id": "APCS002",
                "entity_id": "wll_maryland_charm_sam_apuzzo",
                "source_url": "https://premierlacrosseleague.com/articles/example-2",
                "image_or_render_url": "https://cdn.example.com/group.jpg",
                "operator_decision": "reject_group_photo",
                "operator_notes": "group photo",
                "manual_reviewer": "Mike",
                "reviewed_at_utc": "2026-07-03T00:01:00Z",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )


def test_manual_decision_batch_keeps_carry_forward_review_only_and_rejects_ranker_ready(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "manual_decisions.csv"
    output_dir = tmp_path / "out"
    write_decisions(decisions)

    assert module.main(
        [
            "--decisions-csv",
            decisions.as_posix(),
            "--output-dir",
            output_dir.as_posix(),
            "--head-commit",
            "abc123",
        ]
    ) == 0

    formal = read_csv(output_dir / "formal_quarantine_download_intake_candidates.csv")
    rejected = read_csv(output_dir / "rejected_or_held_review_deck_decisions.csv")
    normalized = read_csv(output_dir / "normalized_review_deck_decisions.csv")
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "action_photo_manual_decision_batch_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_manual_decision_batch_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["decision_files_read"] == 1
    assert manifest["raw_decision_rows_read"] == 2
    assert manifest["formal_intake_rows"] == 1
    assert manifest["reject_rows"] == 1
    assert manifest["hold_rows"] == 0
    assert manifest["invalid_rows"] == 0
    assert manifest["download_approved_default"] == "no"
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False

    assert len(normalized) == 2
    assert formal[0]["candidate_queue_id"] == "APCS001"
    assert formal[0]["download_approved"] == "no"
    assert formal[0]["review_only"] == "true"
    assert formal[0]["publish_ready"] == "false"
    assert "separate human download approval" in formal[0]["notes"]
    assert rejected[0]["candidate_id"] == "APCS002"
    assert rejected[0]["operator_decision"] == "reject_group_photo"
    assert rejected[0]["download_approved"] == "no"
    assert "does not approve downloads" in report


def test_manual_decision_batch_blocks_truthy_download_approval(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "manual_decisions.csv"
    output_dir = tmp_path / "out"
    write_decisions(decisions)
    rows = read_csv(decisions)
    rows[0]["download_approved"] = "yes"
    with decisions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    module.build_packet(decision_paths=[decisions], output_dir=output_dir, head_commit="abc123")

    formal = read_csv(output_dir / "formal_quarantine_download_intake_candidates.csv")
    invalid = read_csv(output_dir / "invalid_review_deck_decisions.csv")
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert formal == []
    assert manifest["invalid_rows"] == 1
    assert invalid[0]["validation_issues"] == "download_approved_truthy_blocked"
