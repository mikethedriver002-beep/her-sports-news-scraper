from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_action_photo_ranker_review_deck_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_action_photo_ranker_review_deck_v1", SCRIPT)
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


def ranker_row(candidate_id: str, *, tier: str, entity_id: str = "pwhl_minnesota_frost_kelly_pannek") -> dict[str, str]:
    return {
        "rank": candidate_id.removeprefix("APCS") or "1",
        "ranker_id": f"APSQ{candidate_id.removeprefix('APCS') or '001'}",
        "source_packet": "action_photo_source_quality_ranker_v1",
        "scout_candidate_id": candidate_id,
        "entity_id": entity_id,
        "source_type": "official_league_recap",
        "source_url": "https://www.thepwhl.com/en/news/fixture",
        "candidate_image_url": f"https://cdn.test/images/{candidate_id}_action.jpg",
        "image_alt": "Kelly Pannek scores during a playoff game.",
        "apparent_width": "",
        "apparent_height": "",
        "source_quality_score": "26",
        "source_quality_tier": tier,
        "source_quality_recommendation": "manual_visual_review",
        "fast_reject_reason": "",
        "positive_signals": "official_source; named_context_match",
        "risk_flags": "body_margin_unclear",
        "manual_decision_needed": "inspect_visual_card_then_reject_hold_or_carry_forward",
        "formal_intake_ready": "no",
        "face_likely_visible": "likely",
        "body_margin_likely": "unclear",
        "four_by_five_crop_potential": "possible",
        "text_safe_negative_space": "possible",
        "source_provenance_clarity": "clear",
        "identity_confidence": "medium",
        "download_approved": "no",
        "review_only": "true",
        "asset_downloads": "false",
        "approval_state_change": "none",
        "publish_ready": "false",
        "publishing": "false",
    }


def write_ranker_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_ranker_review_deck_builds_swipe_deck_from_prioritized_rows(tmp_path: Path) -> None:
    module = load_module()
    ranker_csv = tmp_path / "ranker.csv"
    output_dir = tmp_path / "out"
    write_ranker_csv(
        ranker_csv,
        [
            ranker_row("APCS008", tier="B_manual_review"),
            ranker_row("APCS009", tier="C_hold_backup"),
            ranker_row("APCS010", tier="D_fast_reject_or_low_priority"),
        ],
    )

    assert module.main(
        [
            "--ranker-csv",
            ranker_csv.as_posix(),
            "--output-dir",
            output_dir.as_posix(),
            "--head-commit",
            "abc123",
        ]
    ) == 0

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    rows = read_csv(output_dir / "manual_decision_export_template.csv")
    deck_input = read_csv(output_dir / "ranker_review_deck_input.csv")
    html = (output_dir / "action_photo_review_deck.html").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_review_deck_ui_ready"
    assert manifest["version_wrapper"] == "hsd-action-photo-ranker-review-deck-v1-review-only"
    assert manifest["source_packet"] == "action_photo_source_quality_ranker_v1"
    assert manifest["repo_head"] == "abc123"
    assert manifest["ranker_rows_read"] == 3
    assert manifest["review_now_rows_selected"] == 2
    assert manifest["candidate_item_count"] == 2
    assert manifest["download_approved_default"] == "no"
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False

    assert [row["scout_candidate_id"] for row in deck_input] == ["APCS008", "APCS009"]
    assert [row["visual_priority"] for row in deck_input] == [
        "P1_ranker_manual_review",
        "P2_ranker_hold_backup_review",
    ]
    assert len(rows) == 2
    assert rows[0]["candidate_id"] == "APCS008"
    assert rows[1]["candidate_id"] == "APCS009"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert "APCS008" in html
    assert "APCS009" in html
    assert "APCS010" not in html
    assert "id=\"swipe-card\"" in html
    assert "Export Decision CSV" in html


def test_ranker_review_deck_ignores_truthy_download_approval(tmp_path: Path) -> None:
    module = load_module()
    row = ranker_row("APCS008", tier="B_manual_review")
    row["download_approved"] = "yes"
    ranker_csv = tmp_path / "ranker.csv"
    write_ranker_csv(ranker_csv, [row])

    assert module.deck_input_rows(read_csv(ranker_csv), limit=10) == []


def test_ranker_review_deck_excludes_exported_manual_decisions_without_overmatching(tmp_path: Path) -> None:
    module = load_module()
    ranker_csv = tmp_path / "ranker.csv"
    decisions_csv = tmp_path / "manual_decisions.csv"
    output_dir = tmp_path / "out"
    excluded = ranker_row(
        "APCS008",
        tier="B_manual_review",
        entity_id="pwhl_minnesota_frost_kelly_pannek",
    )
    same_id_different_entity = ranker_row(
        "APCS008",
        tier="B_manual_review",
        entity_id="wnba_indiana_fever_kelsey_mitchell",
    )
    refill = ranker_row(
        "APCS009",
        tier="C_hold_backup",
        entity_id="nwsl_kansas_city_current_temwa_chawinga",
    )
    write_ranker_csv(ranker_csv, [excluded, same_id_different_entity, refill])
    write_csv(
        decisions_csv,
        [
            {
                "deck_item_id": "candidate_APCS008",
                "item_kind": "candidate_source",
                "candidate_id": "APCS008",
                "entity_id": "pwhl_minnesota_frost_kelly_pannek",
                "source_url": excluded["source_url"],
                "image_or_render_url": excluded["candidate_image_url"],
                "operator_decision": "reject_group_photo",
                "operator_notes": "",
                "manual_reviewer": "Mike",
                "reviewed_at_utc": "2026-07-03T18:41:15Z",
                "formal_intake_next_action": "",
                "review_only": "true",
                "download_approved": "no",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        ],
        [
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
        ],
    )

    assert module.main(
        [
            "--ranker-csv",
            ranker_csv.as_posix(),
            "--exclude-decisions-csv",
            decisions_csv.as_posix(),
            "--output-dir",
            output_dir.as_posix(),
            "--limit",
            "2",
            "--head-commit",
            "abc123",
        ]
    ) == 0

    deck_input = read_csv(output_dir / "ranker_review_deck_input.csv")
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (output_dir / "action_photo_review_deck_report.md").read_text(encoding="utf-8")

    assert [row["entity_id"] for row in deck_input] == [
        "wnba_indiana_fever_kelsey_mitchell",
        "nwsl_kansas_city_current_temwa_chawinga",
    ]
    assert manifest["decision_exclusion_keys_applied"] == 1
    assert manifest["ranker_rows_skipped_by_decision_exclusion"] == 1
    assert manifest["excluded_decision_csvs"] == [decisions_csv.resolve(strict=False).as_posix()]
    assert "Decision Exclusion" in report
    assert "Ranker rows skipped before deck refill: 1" in report
