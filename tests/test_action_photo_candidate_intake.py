from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_action_photo_candidate_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_action_photo_candidate_intake_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_action_photo_candidate_intake_defaults_review_only_and_blank_no(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_candidate_intake.csv")
    manifest = json.loads((root / "review_only_action_photo_candidate_intake.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_candidate_intake.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_candidate_intake_ready"
    assert manifest["intake_rows"] == 3
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["blank_source_url_rows"] == 3
    assert manifest["validation_issue_count"] == 0
    assert manifest["quarantine_root"] == "data/assets/quarantine/review_only_candidates"
    assert set(manifest["required_download_fields"]) >= {
        "source_url",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
    }
    assert {row["source_type"] for row in rows} == {
        "official_or_league_public_page",
        "reputable_media_or_wire_lead",
        "gray_area_public_lead",
    }
    for row in rows:
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["quarantine_folder"] == "data/assets/quarantine/review_only_candidates"
        assert row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/")
        assert row["approval_state_change"] == "none"
        assert row["approval_status"] == "not_approved"
        assert row["publish_action"] == "none_artifact_only"
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
        assert row["auto_approval"] == "false"
        assert row["asset_downloads"] == "false"
        assert row["headshot_writes"] == "false"
        assert row["approved_marker_writes"] == "false"
    assert "Human-editable intake" in markdown
    assert "download_approved=yes" in markdown
    assert "Do not ask it to download images" in markdown
    assert "Download approval is not asset approval" in markdown


def test_action_photo_candidate_intake_validator_blocks_unsafe_yes_rows() -> None:
    module = load_module()
    invalid_rows = [
        {
            "download_approved": "yes",
            "source_url": "",
            "entity_id": "",
            "rights_class": "",
            "identity_confidence": "",
            "intended_review_only_use": "",
            "quarantine_target_hint": "assets/leagues/wnba/not_quarantine.jpg",
            "publish_ready": "true",
            "approval_state_change": "approve",
            "publish_action": "publish",
        }
    ]

    issues = module.validate_rows(invalid_rows)
    issue_pairs = {(issue["field"], issue["issue"]) for issue in issues}

    assert ("source_url", "required_when_download_approved_yes") in issue_pairs
    assert ("entity_id", "required_when_download_approved_yes") in issue_pairs
    assert ("rights_class", "required_when_download_approved_yes") in issue_pairs
    assert ("identity_confidence", "required_when_download_approved_yes") in issue_pairs
    assert ("intended_review_only_use", "required_when_download_approved_yes") in issue_pairs
    assert ("quarantine_target_hint", "download_target_must_stay_in_quarantine") in issue_pairs
    assert ("publish_ready", "guardrail_field_must_remain_false") in issue_pairs
    assert ("approval_state_change", "generated_intake_must_not_change_approval_state") in issue_pairs
    assert ("publish_action", "generated_intake_must_not_publish") in issue_pairs


def test_action_photo_candidate_intake_validator_allows_complete_human_quarantine_yes_row() -> None:
    module = load_module()
    valid_rows = [
        {
            "sport": "basketball",
            "league": "wnba",
            "team": "New York Liberty",
            "player": "Breanna Stewart",
            "event_context": "operator supplied public game moment",
            "source_url": "https://example.com/photo-page",
            "entity_id": "wnba:new_york_liberty:breanna_stewart:action_photo",
            "rights_class": "operator_rights_review_required",
            "identity_confidence": "operator_verified_high",
            "intended_review_only_use": "review_only_candidate_research_not_renderer_approval",
            "download_approved": "yes",
            "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/new_york_liberty/breanna_stewart/example.jpg",
            "approval_state_change": "none",
            "publish_action": "none_artifact_only",
            "publish_ready": "false",
            "auto_approval": "false",
            "asset_downloads": "false",
        }
    ]

    assert module.validate_rows(valid_rows) == []
