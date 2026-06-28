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
    source_map_rows = read_csv(root / "review_only_action_photo_source_map_template.csv")
    entity_source_rows = read_csv(root / "review_only_action_photo_sport_entity_source_map.csv")
    manifest = json.loads((root / "review_only_action_photo_candidate_intake.json").read_text(encoding="utf-8"))
    entity_source_manifest = json.loads((root / "review_only_action_photo_sport_entity_source_map.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((root / "review_only_action_photo_candidate_taxonomy.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_candidate_intake.md").read_text(encoding="utf-8")
    taxonomy_md = (root / "review_only_action_photo_candidate_taxonomy.md").read_text(encoding="utf-8")
    checklist_md = (root / "review_only_action_photo_human_review_checklist.md").read_text(encoding="utf-8")
    source_map_md = (root / "review_only_action_photo_source_map_template.md").read_text(encoding="utf-8")
    entity_source_md = (root / "review_only_action_photo_sport_entity_source_map.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_candidate_intake_ready"
    assert manifest["intake_rows"] == 5
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["blank_source_url_rows"] == 5
    assert manifest["source_category_count"] == 9
    assert manifest["rights_class_count"] == 8
    assert manifest["identity_confidence_count"] == 5
    assert manifest["source_map_rows"] == 9
    assert manifest["sport_entity_source_map_rows"] == 19
    assert manifest["sport_entity_source_map_validation_issue_count"] == 0
    assert manifest["validation_issue_count"] == 0
    assert manifest["quarantine_root"] == "data/assets/quarantine/review_only_candidates"
    assert set(manifest["required_download_fields"]) >= {
        "source_url",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
    }
    assert {row["source_category"] for row in rows} == {
        "official_team_gallery",
        "official_league_gallery",
        "editorial_wire",
        "reputable_newsroom_gallery",
        "gray_area_public_lead",
    }
    for row in rows:
        assert row["source_type"] == row["source_category"]
        assert row["intake_id"].startswith("review_only_action_photo_candidate_")
        assert row["created_at_utc"]
        assert row["created_by"] == "generator_review_only_template"
        assert row["source_name"] == ""
        assert row["photographer_credit"] == ""
        assert row["manual_review_status"] == "not_reviewed"
        assert row["manual_reviewer"] == ""
        assert row["reviewed_at_utc"] == ""
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
    assert "Every discovered item is a candidate lead" in markdown
    assert "editorial_wire" in taxonomy["source_categories"]
    assert "gray_area_lead_only" in taxonomy["download_blocked_rights_classes"]
    assert "confirmed_official" in taxonomy["download_ready_identity_confidence"]
    assert "official_social" in taxonomy_md
    assert "Avoid video, broadcast, GIF" in checklist_md
    assert "Do not download image files" in checklist_md
    assert {row["source_category"] for row in source_map_rows} == set(taxonomy["source_categories"])
    assert "Collect URLs and evidence only" in source_map_md
    assert "Do not download image files" in source_map_md
    assert entity_source_manifest["status"] == "action_photo_sport_entity_source_map_ready"
    assert entity_source_manifest["source_map_rows"] == 19
    assert entity_source_manifest["download_approved_yes_allowed_rows"] == 0
    assert entity_source_manifest["review_only_rows"] == 19
    assert entity_source_manifest["publish_ready_rows"] == 0
    assert set(entity_source_manifest["source_categories"]) == set(taxonomy["source_categories"])
    assert {"basketball", "soccer", "college basketball", "college soccer", "softball", "tennis", "golf", "hockey", "multi-sport"} <= set(entity_source_manifest["sports"])
    assert "WNBA" in {row["league_or_entity"] for row in entity_source_rows}
    assert "NWSL" in {row["league_or_entity"] for row in entity_source_rows}
    assert "USWNT" in {row["league_or_entity"] for row in entity_source_rows}
    assert "NCAA women's basketball" in {row["league_or_entity"] for row in entity_source_rows}
    assert "NCAA women's soccer" in {row["league_or_entity"] for row in entity_source_rows}
    assert "NCAA softball" in {row["league_or_entity"] for row in entity_source_rows}
    assert "WTA / Grand Slam / tournament" in {row["league_or_entity"] for row in entity_source_rows}
    assert "LPGA / tournament" in {row["league_or_entity"] for row in entity_source_rows}
    assert "PWHL" in {row["league_or_entity"] for row in entity_source_rows}
    entity_keys = {
        (row["sport"], row["league_or_entity"], row["source_category"], row["source_url_or_search_macro"])
        for row in entity_source_rows
    }
    assert len(entity_keys) == len(entity_source_rows)
    for row in entity_source_rows:
        assert row["source_category"] in taxonomy["source_categories"]
        assert row["source_url_or_search_macro"]
        assert row["allowed_for_download_approved_yes"] == "false"
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
        assert "download" not in row["manual_next_action"].lower() or "do not download" in row["manual_next_action"].lower()
    assert "ChatGPT Pro, Gemini, and manual researchers" in entity_source_md
    assert "does not fetch, download, approve, or publish image assets" in entity_source_md
    assert "Keep `allowed_for_download_approved_yes=false`" in entity_source_md


def test_action_photo_candidate_intake_validator_blocks_unsafe_yes_rows() -> None:
    module = load_module()
    invalid_rows = [
        {
            "download_approved": "yes",
            "source_url": "",
            "entity_id": "",
            "source_category": "",
            "rights_class": "social_uncleared",
            "identity_confidence": "probable",
            "photographer_credit": "",
            "manual_reviewer": "",
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
    assert ("source_category", "required_when_download_approved_yes") in issue_pairs
    assert ("photographer_credit", "credit_required_when_download_approved_yes") in issue_pairs
    assert ("manual_reviewer", "required_when_download_approved_yes") in issue_pairs
    assert ("intended_review_only_use", "required_when_download_approved_yes") in issue_pairs
    assert ("quarantine_target_hint", "download_target_must_stay_in_quarantine") in issue_pairs
    assert ("rights_class", "rights_class_blocks_download_approval") in issue_pairs
    assert ("identity_confidence", "identity_confidence_too_low_for_download_approval") in issue_pairs
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
            "source_category": "official_team_gallery",
            "source_url": "https://example.com/photo-page",
            "entity_id": "wnba:new_york_liberty:breanna_stewart:action_photo",
            "photographer_credit": "credit_not_visible_manual_review",
            "rights_notes": "credit not visible; manual reviewer confirmed source page still qualifies for quarantine review",
            "manual_reviewer": "operator_initials",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
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


def test_action_photo_candidate_intake_validator_blocks_invalid_taxonomy_values() -> None:
    module = load_module()
    invalid_rows = [
        {
            "download_approved": "no",
            "source_category": "free_web_image",
            "rights_class": "reuse_ok",
            "identity_confidence": "sure",
            "manual_review_status": "approved",
        }
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_rows(invalid_rows)}

    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("rights_class", "invalid_controlled_vocabulary") in issue_pairs
    assert ("identity_confidence", "invalid_controlled_vocabulary") in issue_pairs
    assert ("manual_review_status", "invalid_controlled_vocabulary") in issue_pairs


def test_action_photo_sport_entity_source_map_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    invalid_rows = [
        {
            "sport": "basketball",
            "league_or_entity": "WNBA",
            "source_priority": "P0",
            "source_category": "free_web_image",
            "source_name": "unknown",
            "source_url_or_search_macro": '"athlete action photo"',
            "source_domain": "",
            "evidence_use": "lead",
            "rights_review_note": "none",
            "identity_anchor_use": "none",
            "allowed_for_download_approved_yes": "true",
            "manual_next_action": "download it",
            "review_only": "false",
            "publish_ready": "true",
        }
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_entity_source_map_rows(invalid_rows)}

    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("allowed_for_download_approved_yes", "source_map_never_download_approved") in issue_pairs
    assert ("review_only", "source_map_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "source_map_must_not_be_publish_ready") in issue_pairs
