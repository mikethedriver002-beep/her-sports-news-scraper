from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_action_photo_external_research_return_review_v1.py"
INTAKE_FIELDS = [
    "candidate_queue_id",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "notes",
    "operator_verify_required",
    "manual_reviewer",
    "manual_review_status",
    "manual_next_action",
    "download_approved",
    "quarantine_target_hint",
    "review_only",
    "publish_ready",
]
EXTERNAL_FIELDS = [
    "candidate_queue_id",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "notes",
    "operator_verify_required",
]


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_action_photo_external_research_return_review_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def blank_intake_row(queue_id: str) -> dict[str, str]:
    return {
        "candidate_queue_id": queue_id,
        "candidate_photo_url": "",
        "evidence_url": "",
        "evidence_summary": "",
        "identity_anchor_url": "",
        "source_url": "",
        "entity_id": "",
        "rights_class": "",
        "identity_confidence": "",
        "intended_review_only_use": "",
        "notes": "",
        "operator_verify_required": "yes",
        "manual_reviewer": "",
        "manual_review_status": "not_reviewed",
        "manual_next_action": "Paste human-reviewed source and evidence metadata.",
        "download_approved": "no",
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/apq/operator_fill_required.jpg",
        "review_only": "true",
        "publish_ready": "false",
    }


def supplied_return_row(queue_id: str, *, identity_confidence: str = "high") -> dict[str, str]:
    return {
        "candidate_queue_id": queue_id,
        "candidate_photo_url": "https://www.reuters.com/resizer/v2/example.jpg?width=1080",
        "evidence_url": f"https://example.test/evidence/{queue_id.lower()}",
        "evidence_summary": "Captioned action image with source-page evidence.",
        "identity_anchor_url": f"https://example.test/player/{queue_id.lower()}",
        "source_url": f"https://example.test/source/{queue_id.lower()}",
        "entity_id": f"entity:{queue_id.lower()}",
        "rights_class": "editorial_wire_rights_sensitive_manual_review",
        "identity_confidence": identity_confidence,
        "intended_review_only_use": "yes",
        "notes": "manual research return evidence lead only",
        "operator_verify_required": "yes",
    }


def test_external_return_review_holds_direct_images_and_identity_vocab_without_writing_intake(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()
    intake = tmp_path / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    external = tmp_path / "deep-research-report-md.md"
    monkeypatch.setenv("HSD_ACTION_PHOTO_EXTERNAL_RETURN_CSV", str(external))
    write_csv(intake, [blank_intake_row(f"APQ{index:03d}") for index in range(1, 5)], INTAKE_FIELDS)
    write_csv(
        external,
        [
            supplied_return_row("APQ001", identity_confidence="high"),
            supplied_return_row("APQ002", identity_confidence="medium_high"),
        ],
        EXTERNAL_FIELDS,
    )
    original_intake = intake.read_text(encoding="utf-8")

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_external_research_return_review_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_external_research_return_review_v1.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_external_research_return_review_v1.md").read_text(encoding="utf-8")

    assert intake.read_text(encoding="utf-8") == original_intake
    assert manifest["status"] == "action_photo_external_research_return_review_ready"
    assert manifest["review_rows"] == 4
    assert manifest["external_return_rows"] == 2
    assert manifest["missing_external_return_rows"] == 2
    assert manifest["missing_candidate_queue_ids"] == ["APQ003", "APQ004"]
    assert manifest["direct_image_url_hold_rows"] == 2
    assert manifest["identity_vocabulary_mismatch_rows"] == 2
    assert manifest["ready_for_later_human_download_decision_review_rows"] == 0
    assert manifest["generated_download_approval_rows"] == 0
    assert manifest["source_fetching"] is False
    assert manifest["auto_source_enablement"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert rows[0]["external_return_present"] == "yes"
    assert rows[0]["candidate_photo_url_direct_image_hold"] == "yes"
    assert rows[0]["normalized_candidate_page_url"] == "https://example.test/source/apq001"
    assert rows[0]["identity_confidence_status"] == "identity_vocabulary_requires_operator_normalization"
    assert rows[0]["candidate_ready_for_later_human_download_decision_review"] == "no"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_bucket"] == "external_return_direct_image_and_identity_vocab_hold"
    assert rows[2]["candidate_queue_id"] == "APQ003"
    assert rows[2]["external_return_present"] == "no"
    assert rows[2]["review_bucket"] == "external_return_missing"
    assert "does not write intake rows, fetch sources, download images" in markdown


def test_external_return_review_validator_blocks_guardrail_drift() -> None:
    module = load_module()
    rows = module.external_return_review_rows(
        [blank_intake_row("APQ001")],
        [supplied_return_row("APQ001", identity_confidence="confirmed_official")],
    )
    rows[0].update(
        {
            "candidate_ready_for_later_human_download_decision_review": "yes",
            "download_approved": "yes",
            "review_only": "false",
            "source_fetching": "true",
            "auto_source_enablement": "true",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "approval_state_change": "approved",
            "publish_ready": "true",
            "auto_approval": "true",
            "auto_publish": "true",
            "move_files": "true",
            "paid_apis": "true",
        }
    )

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_review_rows(rows)}

    assert ("candidate_ready_for_later_human_download_decision_review", "external_review_must_not_mark_ready") in issue_pairs
    assert ("download_approved", "external_review_must_not_approve_downloads") in issue_pairs
    assert ("review_only", "external_review_must_remain_review_only") in issue_pairs
    assert ("approval_state_change", "external_review_must_not_change_approval_state") in issue_pairs
    assert ("source_fetching", "external_review_guardrail_field_must_be_false") in issue_pairs
    assert ("asset_downloads", "external_review_guardrail_field_must_be_false") in issue_pairs
    assert ("headshot_writes", "external_review_guardrail_field_must_be_false") in issue_pairs
    assert ("approved_marker_writes", "external_review_guardrail_field_must_be_false") in issue_pairs
    assert ("publish_ready", "external_review_guardrail_field_must_be_false") in issue_pairs
    assert ("paid_apis", "external_review_guardrail_field_must_be_false") in issue_pairs
