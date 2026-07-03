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


def decision_row(
    candidate_id: str,
    entity_id: str,
    source_url: str,
    image_or_render_url: str,
    operator_decision: str,
    reviewed_at_utc: str,
    *,
    deck_item_id: str | None = None,
    operator_notes: str = "",
    formal_intake_next_action: str = "",
) -> dict[str, str]:
    return {
        "deck_item_id": deck_item_id or f"candidate_{candidate_id}",
        "item_kind": "candidate_source",
        "candidate_id": candidate_id,
        "entity_id": entity_id,
        "source_url": source_url,
        "image_or_render_url": image_or_render_url,
        "operator_decision": operator_decision,
        "operator_notes": operator_notes,
        "manual_reviewer": "Mike",
        "reviewed_at_utc": reviewed_at_utc,
        "formal_intake_next_action": formal_intake_next_action,
        "review_only": "true",
        "download_approved": "no",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
    }


def write_decisions(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_manual_decision_batch_keeps_carry_forward_review_only_and_rejects_ranker_ready(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "manual_decisions.csv"
    output_dir = tmp_path / "out"
    write_decisions(
        decisions,
        [
            decision_row(
                "APCS001",
                "wll_new_york_charging_madison_doucette",
                "https://premierlacrosseleague.com/articles/example",
                "https://cdn.example.com/madison-action.jpg",
                "carry_forward_for_formal_intake",
                "2026-07-03T00:00:00Z",
                operator_notes="strong solo action",
                formal_intake_next_action="prepare_separate_formal_quarantine_download_intake",
            ),
            decision_row(
                "APCS002",
                "wll_maryland_charm_sam_apuzzo",
                "https://premierlacrosseleague.com/articles/example-2",
                "https://cdn.example.com/group.jpg",
                "reject_group_photo",
                "2026-07-03T00:01:00Z",
                operator_notes="group photo",
            ),
        ],
    )

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
    assert manifest["latest_decision_rows"] == 2
    assert manifest["superseded_decision_rows"] == 0
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


def test_manual_decision_batch_keeps_latest_decision_per_candidate_entity_across_exports(tmp_path: Path) -> None:
    module = load_module()
    output_dir = tmp_path / "out"
    dec_v13 = tmp_path / "manual_decisions_v13.csv"
    dec_v14 = tmp_path / "manual_decisions_v14.csv"
    dec_v15 = tmp_path / "manual_decisions_v15.csv"

    write_decisions(
        dec_v13,
        [
            decision_row(
                "APCS001",
                "wll_new_york_charging_madison_doucette",
                "https://premierlacrosseleague.com/articles/madison-doucette",
                "https://cdn.example.com/madison-action.jpg",
                "reject_wrong_person",
                "2026-07-03T00:00:00Z",
            ),
            decision_row(
                "APCS002",
                "wnba_indiana_fever_kelsey_mitchell",
                "https://wnba.com/news/kelsey-mitchell-feature",
                "https://cdn.example.com/kelsey-carry.jpg",
                "carry_forward_for_formal_intake",
                "2026-07-03T00:01:00Z",
                formal_intake_next_action="prepare_separate_formal_quarantine_download_intake",
            ),
            decision_row(
                "APCS003",
                "wll_maryland_charm_sam_apuzzo",
                "https://premierlacrosseleague.com/articles/sam-apuzzo",
                "https://cdn.example.com/sam-crop.jpg",
                "reject_bad_crop",
                "2026-07-03T00:02:00Z",
            ),
        ],
    )
    write_decisions(
        dec_v14,
        [
            decision_row(
                "APCS001",
                "wll_new_york_charging_madison_doucette",
                "https://premierlacrosseleague.com/articles/madison-doucette",
                "https://cdn.example.com/madison-action.jpg",
                "hold_manual_check",
                "2026-07-03T01:00:00Z",
            ),
            decision_row(
                "APCS002",
                "wnba_indiana_fever_kelsey_mitchell",
                "https://wnba.com/news/kelsey-mitchell-feature",
                "https://cdn.example.com/kelsey-carry.jpg",
                "reject_group_photo",
                "2026-07-03T01:01:00Z",
            ),
            decision_row(
                "APCS003",
                "wll_maryland_charm_sam_apuzzo",
                "https://premierlacrosseleague.com/articles/sam-apuzzo",
                "https://cdn.example.com/sam-crop.jpg",
                "reject_group_photo",
                "2026-07-03T01:02:00Z",
            ),
        ],
    )
    write_decisions(
        dec_v15,
        [
            decision_row(
                "APCS001",
                "wll_new_york_charging_madison_doucette",
                "https://premierlacrosseleague.com/articles/madison-doucette",
                "https://cdn.example.com/madison-action.jpg",
                "carry_forward_for_formal_intake",
                "2026-07-03T02:00:00Z",
                formal_intake_next_action="prepare_separate_formal_quarantine_download_intake",
            ),
            decision_row(
                "APCS002",
                "wnba_indiana_fever_kelsey_mitchell",
                "https://wnba.com/news/kelsey-mitchell-feature",
                "https://cdn.example.com/kelsey-carry.jpg",
                "reject_wrong_person",
                "2026-07-03T02:01:00Z",
            ),
            decision_row(
                "APCS003",
                "wll_maryland_charm_sam_apuzzo",
                "https://premierlacrosseleague.com/articles/sam-apuzzo",
                "https://cdn.example.com/sam-crop.jpg",
                "hold_manual_check",
                "2026-07-03T02:02:00Z",
            ),
        ],
    )

    assert module.main(
        [
            "--decisions-csv",
            dec_v13.as_posix(),
            "--decisions-csv",
            dec_v14.as_posix(),
            "--decisions-csv",
            dec_v15.as_posix(),
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

    assert manifest["decision_files_read"] == 3
    assert manifest["raw_decision_rows_read"] == 9
    assert manifest["latest_decision_rows"] == 3
    assert manifest["superseded_decision_rows"] == 6
    assert manifest["formal_intake_rows"] == 1
    assert manifest["reject_rows"] == 1
    assert manifest["hold_rows"] == 1
    assert manifest["invalid_rows"] == 0
    assert [row["candidate_queue_id"] for row in formal] == ["APCS001"]
    assert [row["candidate_id"] for row in rejected] == ["APCS002", "APCS003"]
    assert [row["operator_decision"] for row in rejected] == ["reject_wrong_person", "hold_manual_check"]
    assert [row["candidate_id"] for row in normalized] == ["APCS001", "APCS002", "APCS003"]
    assert normalized[0]["operator_decision"] == "carry_forward_for_formal_intake"
    assert normalized[1]["operator_decision"] == "reject_wrong_person"
    assert normalized[2]["operator_decision"] == "hold_manual_check"


def test_manual_decision_batch_blocks_truthy_download_approval(tmp_path: Path) -> None:
    module = load_module()
    decisions = tmp_path / "manual_decisions.csv"
    output_dir = tmp_path / "out"
    write_decisions(decisions, [decision_row(
        "APCS001",
        "wll_new_york_charging_madison_doucette",
        "https://premierlacrosseleague.com/articles/example",
        "https://cdn.example.com/madison-action.jpg",
        "carry_forward_for_formal_intake",
        "2026-07-03T00:00:00Z",
        operator_notes="strong solo action",
        formal_intake_next_action="prepare_separate_formal_quarantine_download_intake",
    ), decision_row(
        "APCS002",
        "wll_maryland_charm_sam_apuzzo",
        "https://premierlacrosseleague.com/articles/example-2",
        "https://cdn.example.com/group.jpg",
        "reject_group_photo",
        "2026-07-03T00:01:00Z",
        operator_notes="group photo",
    )])
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
