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
    womens_soccer_rows = read_csv(root / "review_only_womens_soccer_action_photo_starter_intake.csv")
    external_research_rows = read_csv(root / "review_only_action_photo_external_research_source_map.csv")
    queue_rows = read_csv(root / "review_only_action_photo_candidate_queue_v1.csv")
    research_packet_rows = read_csv(root / "review_only_action_photo_candidate_research_packet_v1.csv")
    research_return_rows = read_csv(root / "review_only_action_photo_research_return_intake_v1.csv")
    research_bundle_rows = read_csv(root / "review_only_action_photo_research_run_bundle_v1.csv")
    preflight_rows = read_csv(root / "review_only_action_photo_quarantine_preflight_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_candidate_intake.json").read_text(encoding="utf-8"))
    entity_source_manifest = json.loads((root / "review_only_action_photo_sport_entity_source_map.json").read_text(encoding="utf-8"))
    womens_soccer_manifest = json.loads((root / "review_only_womens_soccer_action_photo_starter_intake.json").read_text(encoding="utf-8"))
    external_research_manifest = json.loads((root / "review_only_action_photo_external_research_source_map.json").read_text(encoding="utf-8"))
    queue_manifest = json.loads((root / "review_only_action_photo_candidate_queue_v1.json").read_text(encoding="utf-8"))
    research_packet_manifest = json.loads((root / "review_only_action_photo_candidate_research_packet_v1.json").read_text(encoding="utf-8"))
    research_return_manifest = json.loads((root / "review_only_action_photo_research_return_intake_v1.json").read_text(encoding="utf-8"))
    research_bundle_manifest = json.loads((root / "review_only_action_photo_research_run_bundle_v1.json").read_text(encoding="utf-8"))
    preflight_manifest = json.loads((root / "review_only_action_photo_quarantine_preflight_v1.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((root / "review_only_action_photo_candidate_taxonomy.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_candidate_intake.md").read_text(encoding="utf-8")
    taxonomy_md = (root / "review_only_action_photo_candidate_taxonomy.md").read_text(encoding="utf-8")
    checklist_md = (root / "review_only_action_photo_human_review_checklist.md").read_text(encoding="utf-8")
    source_map_md = (root / "review_only_action_photo_source_map_template.md").read_text(encoding="utf-8")
    entity_source_md = (root / "review_only_action_photo_sport_entity_source_map.md").read_text(encoding="utf-8")
    womens_soccer_md = (root / "review_only_womens_soccer_action_photo_starter_intake.md").read_text(encoding="utf-8")
    external_research_md = (root / "review_only_action_photo_external_research_source_map.md").read_text(encoding="utf-8")
    queue_md = (root / "review_only_action_photo_candidate_queue_v1.md").read_text(encoding="utf-8")
    research_packet_md = (root / "review_only_action_photo_candidate_research_packet_v1.md").read_text(encoding="utf-8")
    research_return_md = (root / "review_only_action_photo_research_return_intake_v1.md").read_text(encoding="utf-8")
    research_bundle_md = (root / "review_only_action_photo_research_run_bundle_v1.md").read_text(encoding="utf-8")
    preflight_md = (root / "review_only_action_photo_quarantine_preflight_v1.md").read_text(encoding="utf-8")

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
    assert manifest["womens_soccer_action_photo_starter_rows"] == 10
    assert manifest["womens_soccer_action_photo_starter_validation_issue_count"] == 0
    assert manifest["external_research_source_map_rows"] == 14
    assert manifest["external_research_source_map_validation_issue_count"] == 0
    assert manifest["action_photo_candidate_queue_rows"] == 10
    assert manifest["action_photo_candidate_queue_validation_issue_count"] == 0
    assert manifest["action_photo_candidate_research_packet_rows"] == 10
    assert manifest["action_photo_candidate_research_packet_validation_issue_count"] == 0
    assert manifest["action_photo_research_return_intake_rows"] == 10
    assert manifest["action_photo_research_return_intake_validation_issue_count"] == 0
    assert manifest["action_photo_research_run_bundle_rows"] == 5
    assert manifest["action_photo_research_run_bundle_validation_issue_count"] == 0
    assert manifest["action_photo_quarantine_preflight_rows"] == 10
    assert manifest["action_photo_quarantine_preflight_validation_issue_count"] == 0
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
    assert womens_soccer_manifest["status"] == "womens_soccer_action_photo_starter_ready"
    assert womens_soccer_manifest["starter_rows"] == 10
    assert womens_soccer_manifest["download_approved_yes_rows"] == 0
    assert womens_soccer_manifest["blank_source_url_rows"] == 10
    assert womens_soccer_manifest["blank_entity_id_rows"] == 10
    assert womens_soccer_manifest["blank_rights_class_rows"] == 10
    assert womens_soccer_manifest["blank_identity_confidence_rows"] == 10
    assert womens_soccer_manifest["blank_intended_review_only_use_rows"] == 10
    assert womens_soccer_manifest["review_only_rows"] == 10
    assert womens_soccer_manifest["publish_ready_rows"] == 0
    assert {"nwsl_first", "future_uswnt", "future_wsl_liga_f_arkema"} == set(womens_soccer_manifest["expansion_lanes"])
    assert {
        "official_league_gallery",
        "official_team_gallery",
        "verification_only_player_page",
        "editorial_wire",
        "reputable_newsroom_gallery",
        "official_social",
        "third_party_creator_public",
        "gray_area_public_lead",
        "official_federation_or_tournament",
    } == set(womens_soccer_manifest["source_categories"])
    womens_soccer_keys = {
        (row["league_or_entity"], row["team_or_scope"], row["source_category"], row["source_url_or_search_macro"])
        for row in womens_soccer_rows
    }
    assert len(womens_soccer_keys) == len(womens_soccer_rows)
    assert sum(1 for row in womens_soccer_rows if row["expansion_lane"] == "nwsl_first") == 8
    assert any(row["league_or_entity"] == "USWNT" for row in womens_soccer_rows)
    assert any(row["league_or_entity"] == "Europe top flight" for row in womens_soccer_rows)
    for row in womens_soccer_rows:
        assert row["sport"] == "soccer"
        assert row["source_category"] in taxonomy["source_categories"]
        assert row["source_url_or_search_macro"]
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["download_approved"] == "no"
        assert row["allowed_for_download_approved_yes"] == "false"
        assert row["manual_review_status"] == "not_reviewed"
        assert row["manual_reviewer"] == ""
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
        assert row["approval_state_change"] == "none"
        assert row["publish_action"] == "none_artifact_only"
        assert row["roster_truth_status"] == "not_asserted_manual_verification_required"
    assert "NWSL-first URL/evidence starter" in womens_soccer_md
    assert "does not fetch, download, approve, assert current roster truth" in womens_soccer_md
    assert "Keep generated local-download-law fields blank/no" in womens_soccer_md
    assert external_research_manifest["status"] == "action_photo_external_research_source_map_ready"
    assert external_research_manifest["source_map_rows"] == 14
    assert external_research_manifest["validation_issue_count"] == 0
    assert external_research_manifest["download_approved_yes_rows"] == 0
    assert external_research_manifest["blank_source_url_rows"] == 14
    assert external_research_manifest["blank_entity_id_rows"] == 14
    assert external_research_manifest["blank_rights_class_rows"] == 14
    assert external_research_manifest["blank_identity_confidence_rows"] == 14
    assert external_research_manifest["blank_intended_review_only_use_rows"] == 14
    assert external_research_manifest["review_only_rows"] == 14
    assert external_research_manifest["publish_ready_rows"] == 0
    assert external_research_manifest["source_family_ranked_rows"] == 14
    assert {
        "WNBA",
        "NWSL",
        "USWNT / U.S. Soccer",
        "NCAA Women Basketball",
        "NCAA Women Softball",
        "NCAA Women Volleyball",
        "NCAA Women Soccer",
        "WTA Tennis",
        "LPGA Golf",
        "PWHL / Women Hockey",
        "AUSL / Pro Softball",
        "AP Images Sports Portal",
        "Keith Allison Flickr legacy references",
        "Inside the Rink galleries",
    } == set(external_research_manifest["league_entities"])
    assert {
        "Getty Images Editorial Sports",
        "ISI Photos Archive",
        "NCAA Photos / Clarkson Creative",
        "AP Images Sports Portal",
        "Athletes Unlimited / AUSL Media Hub",
        "LPGA On-Site Media Hub",
        "WTA Corporate Match Notes",
        "Keith Allison Flickr Archive",
        "The Ice Garden Portfolio Network",
        "Inside the Rink Galleries",
    } <= {row["source_family_name"] for row in external_research_rows}
    external_keys = {
        (
            row["sport"],
            row["league_entity"],
            row["source_category"],
            row["source_domain"],
            row["likely_search_query_macro"],
        )
        for row in external_research_rows
    }
    assert len(external_keys) == len(external_research_rows)
    for row in external_research_rows:
        assert row["source_category"] in taxonomy["source_categories"]
        assert row["rights_posture_recommendation"] in taxonomy["rights_classes"]
        assert row["likely_search_query_macro"]
        assert row["identity_verification_anchor"]
        assert row["limitations_red_flags"]
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
        assert row["approval_state_change"] == "none"
        assert row["publish_action"] == "none_artifact_only"
    assert "fair-use operating assumption" in external_research_md
    assert "Rows are advisory URL/search leads only" in external_research_md
    assert "Official/player pages are identity anchors" in external_research_md
    assert queue_manifest["status"] == "action_photo_candidate_queue_ready"
    assert queue_manifest["queue_rows"] == 10
    assert queue_manifest["validation_issue_count"] == 0
    assert queue_manifest["download_approved_yes_rows"] == 0
    assert queue_manifest["blank_candidate_photo_url_rows"] == 10
    assert queue_manifest["blank_evidence_url_rows"] == 10
    assert queue_manifest["blank_evidence_summary_rows"] == 10
    assert queue_manifest["blank_identity_anchor_url_rows"] == 10
    assert queue_manifest["blank_source_url_rows"] == 10
    assert queue_manifest["blank_entity_id_rows"] == 10
    assert queue_manifest["blank_rights_class_rows"] == 10
    assert queue_manifest["blank_identity_confidence_rows"] == 10
    assert queue_manifest["blank_intended_review_only_use_rows"] == 10
    assert queue_manifest["review_only_rows"] == 10
    assert queue_manifest["publish_ready_rows"] == 0
    assert {
        "WNBA",
        "NWSL",
        "USWNT / U.S. Soccer",
        "NCAA Women Basketball",
        "NCAA Women Softball",
        "PWHL",
        "AUSL / Pro Softball",
        "WTA Tennis",
        "LPGA Golf",
    } <= set(queue_manifest["league_entities"])
    assert {
        "Getty Images Editorial Sports",
        "ISI Photos Archive",
        "NCAA Photos / Clarkson Creative",
        "Athletes Unlimited / AUSL Media Hub",
        "WTA / Getty",
        "LPGA / Getty",
    } <= set(queue_manifest["source_families"])
    assert len({row["candidate_queue_id"] for row in queue_rows}) == len(queue_rows)
    queue_keys = {
        (row["sport"], row["league_entity"], row["source_family"], row["source_category"], row["source_url_or_search_macro"])
        for row in queue_rows
    }
    assert len(queue_keys) == len(queue_rows)
    for row in queue_rows:
        assert row["candidate_queue_id"].startswith("APQ")
        assert row["target_entity_or_player"] == "operator_fill_player_or_team"
        assert row["source_category"] in taxonomy["source_categories"]
        assert row["rights_posture_metadata"] in taxonomy["rights_classes"]
        assert row["source_url_or_search_macro"]
        assert row["candidate_photo_url"] == ""
        assert row["evidence_url"] == ""
        assert row["evidence_summary"] == ""
        assert row["identity_anchor_url"] == ""
        assert row["download_approved"] == "no"
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/")
        assert row["manual_reviewer"] == ""
        assert row["manual_review_status"] == "not_reviewed"
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
    assert "Concrete candidate-research queue" in queue_md
    assert "Fill `candidate_photo_url`, `evidence_url`, `evidence_summary`, and `identity_anchor_url`" in queue_md
    assert "`download_approved=yes` remains human-edited only" in queue_md
    assert research_packet_manifest["status"] == "action_photo_candidate_research_packet_ready"
    assert research_packet_manifest["research_task_rows"] == 10
    assert research_packet_manifest["queue_rows_covered"] == 10
    assert research_packet_manifest["validation_issue_count"] == 0
    assert research_packet_manifest["download_approved_yes_rows"] == 0
    assert research_packet_manifest["blank_candidate_photo_url_rows"] == 10
    assert research_packet_manifest["blank_evidence_url_rows"] == 10
    assert research_packet_manifest["blank_evidence_summary_rows"] == 10
    assert research_packet_manifest["blank_identity_anchor_url_rows"] == 10
    assert research_packet_manifest["blank_source_url_rows"] == 10
    assert research_packet_manifest["blank_entity_id_rows"] == 10
    assert research_packet_manifest["blank_rights_class_rows"] == 10
    assert research_packet_manifest["blank_identity_confidence_rows"] == 10
    assert research_packet_manifest["blank_intended_review_only_use_rows"] == 10
    assert research_packet_manifest["blank_notes_rows"] == 10
    assert research_packet_manifest["operator_verify_required_yes_rows"] == 10
    assert research_packet_manifest["review_only_rows"] == 10
    assert research_packet_manifest["publish_ready_rows"] == 0
    assert set(research_packet_manifest["researcher_lanes"]) == {"chatgpt_pro", "gemini_pro", "manual_research"}
    assert set(research_packet_manifest["candidate_queue_ids"]) == {row["candidate_queue_id"] for row in queue_rows}
    expected_paste_back_schema = [
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
    assert research_packet_manifest["paste_back_schema"] == expected_paste_back_schema
    assert len({row["research_task_id"] for row in research_packet_rows}) == len(research_packet_rows)
    assert {row["candidate_queue_id"] for row in research_packet_rows} == {row["candidate_queue_id"] for row in queue_rows}
    for row in research_packet_rows:
        assert row["research_task_id"].startswith("APR")
        assert row["researcher_lane"] in {"chatgpt_pro", "gemini_pro", "manual_research"}
        assert row["candidate_queue_id"] in {queue_row["candidate_queue_id"] for queue_row in queue_rows}
        assert row["source_category"] in taxonomy["source_categories"]
        assert row["rights_posture_metadata"] in taxonomy["rights_classes"]
        assert "Return CSV in a code block" in row["copy_ready_prompt"]
        assert "candidate_queue_id,candidate_photo_url,evidence_url,evidence_summary,identity_anchor_url,source_url,entity_id,rights_class,identity_confidence,intended_review_only_use,notes,operator_verify_required" in row["copy_ready_prompt"]
        assert "Do not download images" in row["copy_ready_prompt"]
        assert "do not claim approval" in row["copy_ready_prompt"]
        assert "do not mark render-ready" in row["copy_ready_prompt"]
        assert row["paste_back_schema"] == ",".join(expected_paste_back_schema)
        assert row["candidate_photo_url"] == ""
        assert row["evidence_url"] == ""
        assert row["evidence_summary"] == ""
        assert row["identity_anchor_url"] == ""
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["notes"] == ""
        assert row["operator_verify_required"] == "yes"
        assert row["download_approved"] == "no"
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
    assert "What Mike Sends To ChatGPT/Gemini" in research_packet_md
    assert "What Mike Pastes Back" in research_packet_md
    assert "`download_approved=yes` remains human-edited only" in research_packet_md
    assert "Do not download images" in research_packet_md
    assert research_return_manifest["status"] == "action_photo_research_return_intake_ready"
    assert research_return_manifest["return_intake_rows"] == 10
    assert research_return_manifest["queue_rows_covered"] == 10
    assert research_return_manifest["validation_issue_count"] == 0
    assert research_return_manifest["rows_with_pasted_return_data"] == 0
    assert research_return_manifest["download_approved_yes_rows"] == 0
    assert research_return_manifest["blank_candidate_photo_url_rows"] == 10
    assert research_return_manifest["blank_evidence_url_rows"] == 10
    assert research_return_manifest["blank_evidence_summary_rows"] == 10
    assert research_return_manifest["blank_identity_anchor_url_rows"] == 10
    assert research_return_manifest["blank_source_url_rows"] == 10
    assert research_return_manifest["blank_entity_id_rows"] == 10
    assert research_return_manifest["blank_rights_class_rows"] == 10
    assert research_return_manifest["blank_identity_confidence_rows"] == 10
    assert research_return_manifest["blank_intended_review_only_use_rows"] == 10
    assert research_return_manifest["blank_notes_rows"] == 10
    assert research_return_manifest["operator_verify_required_yes_rows"] == 10
    assert research_return_manifest["manual_reviewer_blank_rows"] == 10
    assert research_return_manifest["manual_review_status_not_reviewed_rows"] == 10
    assert research_return_manifest["review_only_rows"] == 10
    assert research_return_manifest["publish_ready_rows"] == 0
    assert set(research_return_manifest["candidate_queue_ids"]) == {row["candidate_queue_id"] for row in queue_rows}
    assert len({row["candidate_queue_id"] for row in research_return_rows}) == len(research_return_rows)
    assert {row["candidate_queue_id"] for row in research_return_rows} == {row["candidate_queue_id"] for row in queue_rows}
    for row in research_return_rows:
        assert row["candidate_queue_id"].startswith("APQ")
        assert row["candidate_photo_url"] == ""
        assert row["evidence_url"] == ""
        assert row["evidence_summary"] == ""
        assert row["identity_anchor_url"] == ""
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["notes"] == ""
        assert row["operator_verify_required"] == "yes"
        assert row["manual_reviewer"] == ""
        assert row["manual_review_status"] == "not_reviewed"
        assert "Paste returned URL/evidence fields here" in row["manual_next_action"]
        assert row["download_approved"] == "no"
        assert row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/")
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
    assert "Review-Only Action Photo Research Return Intake" in research_return_md
    assert "What To Paste Back" in research_return_md
    assert "`download_approved=yes` remains human-edited only" in research_return_md
    assert "does not download images, approve assets, change approval state, or make anything render-ready" in research_return_md
    assert research_bundle_manifest["status"] == "action_photo_research_run_bundle_ready"
    assert research_bundle_manifest["bundle_steps"] == 5
    assert research_bundle_manifest["validation_issue_count"] == 0
    assert research_bundle_manifest["download_approved_yes_rows"] == 0
    assert research_bundle_manifest["review_only_rows"] == 5
    assert research_bundle_manifest["publish_ready_rows"] == 0
    assert research_bundle_manifest["emails_sent"] is False
    assert research_bundle_manifest["asset_downloads"] is False
    assert research_bundle_manifest["approval_state_change"] is False
    assert research_bundle_manifest["auto_publish"] is False
    assert research_bundle_manifest["paid_apis"] is False
    expected_bundle_paths = {
        "research_packet_md": "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md",
        "research_packet_csv": "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.csv",
        "research_packet_json": "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.json",
        "return_intake_md": "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.md",
        "return_intake_csv": "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv",
        "return_intake_json": "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.json",
    }
    assert set(research_bundle_manifest["artifact_paths"]) == set(expected_bundle_paths)
    for key, expected_suffix in expected_bundle_paths.items():
        assert research_bundle_manifest["artifact_paths"][key].endswith(expected_suffix)
    assert research_bundle_manifest["email_ready_subject"] == "Run HSD review-only action-photo research packet"
    assert "Do not download images" in research_bundle_manifest["email_ready_body"]
    assert "approve assets" in research_bundle_manifest["email_ready_body"]
    assert len({row["bundle_step_id"] for row in research_bundle_rows}) == len(research_bundle_rows)
    assert {row["operator_lane"] for row in research_bundle_rows} == {
        "chatgpt_pro",
        "gemini_pro",
        "manual_research",
        "paste_back_intake",
        "conductor_validation",
    }
    all_bundle_paths = set(research_bundle_manifest["artifact_paths"].values())
    for row in research_bundle_rows:
        assert row["bundle_step_id"].startswith("APRB")
        assert set(row["artifact_paths"].split("|")) == all_bundle_paths
        assert row["paste_back_location"] == research_bundle_manifest["artifact_paths"]["return_intake_csv"]
        assert row["copy_ready_instruction"]
        assert "download" in row["copy_ready_instruction"].lower() or "url/evidence" in row["copy_ready_instruction"].lower()
        assert row["next_conductor_action"]
        assert row["download_approved"] == "no"
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
    assert "Review-Only Action Photo Research Run Bundle" in research_bundle_md
    assert "Email-Ready Text" in research_bundle_md
    assert "Do not send email automatically from this lane" in research_bundle_md
    assert "Do not download or fetch image files" in research_bundle_md
    assert "After Mike pastes returned rows into the intake, validate pasted rows" in research_bundle_md
    assert preflight_manifest["status"] == "action_photo_quarantine_preflight_ready"
    assert preflight_manifest["preflight_rows"] == 10
    assert preflight_manifest["ready_for_human_download_decision_rows"] == 0
    assert preflight_manifest["lead_only_rows"] == 10
    assert preflight_manifest["validation_issue_count"] == 0
    assert preflight_manifest["download_approved_yes_rows"] == 0
    assert preflight_manifest["review_only_rows"] == 10
    assert preflight_manifest["publish_ready_rows"] == 0
    assert preflight_manifest["missing_required_field_counts"]["source_url"] == 10
    assert preflight_manifest["missing_required_field_counts"]["entity_id"] == 10
    assert preflight_manifest["missing_required_field_counts"]["rights_class"] == 10
    assert preflight_manifest["missing_required_field_counts"]["identity_confidence"] == 10
    assert preflight_manifest["missing_required_field_counts"]["intended_review_only_use"] == 10
    assert preflight_manifest["missing_required_field_counts"]["candidate_photo_url"] == 10
    assert preflight_manifest["missing_required_field_counts"]["evidence_url"] == 10
    assert preflight_manifest["missing_required_field_counts"]["identity_anchor_url"] == 10
    assert preflight_manifest["action_photo_status_counts"] == {"missing_candidate_photo_url": 10}
    assert preflight_manifest["identity_confidence_status_counts"] == {"identity_missing": 10}
    assert set(preflight_manifest["candidate_queue_ids"]) == {row["candidate_queue_id"] for row in queue_rows}
    assert len({row["preflight_id"] for row in preflight_rows}) == len(preflight_rows)
    assert {row["candidate_queue_id"] for row in preflight_rows} == {row["candidate_queue_id"] for row in research_return_rows}
    for row in preflight_rows:
        assert row["preflight_id"].startswith("APQP")
        assert row["candidate_queue_id"].startswith("APQ")
        assert row["candidate_photo_url"] == ""
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["evidence_url"] == ""
        assert row["identity_anchor_url"] == ""
        assert row["action_photo_check"] == "missing_candidate_photo_url"
        assert row["action_photo_status"] == "missing_candidate_photo_url"
        assert row["identity_confidence_status"] == "identity_missing"
        assert row["duplicate_candidate_key"] == "unique_or_unfilled"
        assert row["lead_status"] == "lead_only_research_return_missing"
        assert row["ready_for_human_download_decision"] == "no"
        assert row["download_approved"] == "no"
        assert row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/")
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
        assert "Run the research bundle" in row["manual_next_action"]
    assert "Review-Only Action Photo Quarantine Preflight" in preflight_md
    assert "Ready for human download decision" in preflight_md
    assert "does not download files, approve assets, write headshots" in preflight_md


def test_wnba_final_score_hero_targets_bridge_render_gap_without_downloads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_wnba_final_score_hero_action_photo_targets_v1.csv")
    manifest = json.loads((root / "review_only_wnba_final_score_hero_action_photo_targets_v1.json").read_text(encoding="utf-8"))
    top_manifest = json.loads((root / "review_only_action_photo_candidate_intake.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_wnba_final_score_hero_action_photo_targets_v1.md").read_text(encoding="utf-8")
    taxonomy = json.loads((root / "review_only_action_photo_candidate_taxonomy.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "wnba_final_score_hero_action_photo_targets_ready"
    assert manifest["target_rows"] == 6
    assert manifest["validation_issue_count"] == 0
    assert manifest["team"] == "Indiana Fever"
    assert manifest["player"] == "Kelsey Mitchell"
    assert manifest["render_gap"] == "renderer_revise_headshot_bridge_not_emotional_action_sports_moment"
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["blank_candidate_photo_url_rows"] == 6
    assert manifest["blank_evidence_url_rows"] == 6
    assert manifest["blank_evidence_summary_rows"] == 6
    assert manifest["blank_identity_anchor_url_rows"] == 6
    assert manifest["blank_source_url_rows"] == 6
    assert manifest["blank_entity_id_rows"] == 6
    assert manifest["blank_rights_class_rows"] == 6
    assert manifest["blank_identity_confidence_rows"] == 6
    assert manifest["blank_intended_review_only_use_rows"] == 6
    assert manifest["operator_verify_required_yes_rows"] == 6
    assert manifest["manual_reviewer_blank_rows"] == 6
    assert manifest["manual_review_status_not_reviewed_rows"] == 6
    assert manifest["review_only_rows"] == 6
    assert manifest["publish_ready_rows"] == 0
    assert top_manifest["wnba_final_score_hero_action_photo_target_rows"] == 6
    assert top_manifest["wnba_final_score_hero_action_photo_target_validation_issue_count"] == 0
    assert top_manifest["wnba_final_score_hero_action_photo_targets_csv"].endswith(
        "review_only_wnba_final_score_hero_action_photo_targets_v1.csv"
    )
    assert {
        "official_league_gallery",
        "editorial_wire",
        "reputable_newsroom_gallery",
        "official_social",
        "third_party_creator_public",
    } == set(manifest["source_categories"])
    assert {
        "driving_or_finish",
        "shooting_or_three_point_release",
        "celebration_or_final_buzzer_reaction",
        "team_context_or_teammate_celebration",
        "official_social_action_or_celebration_lead",
        "creator_public_action_lead_for_manual_review",
    } == set(manifest["target_moment_types"])
    assert len({row["target_id"] for row in rows}) == len(rows)
    keys = {
        (row["team"], row["player"], row["target_moment_type"], row["source_category"], row["source_url_or_search_macro"])
        for row in rows
    }
    assert len(keys) == len(rows)
    for row in rows:
        assert row["target_id"].startswith("WFSH")
        assert row["sport"] == "basketball"
        assert row["league_entity"] == "WNBA"
        assert row["team"] == "Indiana Fever"
        assert row["player"] == "Kelsey Mitchell"
        assert row["source_category"] in taxonomy["source_categories"]
        assert row["source_url_or_search_macro"]
        assert "headshot_bridge" in row["render_gap"]
        assert {"headshot", "media_day", "portrait", "static_pose"} <= set(row["low_value_cues"].split("|"))
        assert any(term in row["preferred_action_cues"] for term in ["game_action", "celebration", "driving", "shooting", "rebound", "block"])
        assert row["candidate_photo_url"] == ""
        assert row["evidence_url"] == ""
        assert row["evidence_summary"] == ""
        assert row["identity_anchor_url"] == ""
        assert row["source_url"] == ""
        assert row["entity_id"] == ""
        assert row["rights_class"] == ""
        assert row["identity_confidence"] == ""
        assert row["intended_review_only_use"] == ""
        assert row["operator_verify_required"] == "yes"
        assert row["download_approved"] == "no"
        assert row["quarantine_target_hint"].startswith("data/assets/quarantine/review_only_candidates/")
        assert row["manual_reviewer"] == ""
        assert row["manual_review_status"] == "not_reviewed"
        assert row["review_only"] == "true"
        assert row["publish_ready"] == "false"
    assert "headshot bridge" in markdown
    assert "media-day/headshot/portrait" in markdown
    assert "action/game/celebration/driving/shooting/rebound/block" in markdown
    assert "`download_approved=yes` remains human-edited only" in markdown
    assert "no row is render-ready" in markdown


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


def test_womens_soccer_action_photo_starter_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    invalid_rows = [
        {
            "starter_rank": "WSAP99",
            "sport": "soccer",
            "league_or_entity": "NWSL",
            "expansion_lane": "nwsl_first",
            "team_or_scope": "bad",
            "source_priority": "P0",
            "source_category": "free_web_image",
            "source_name": "unknown",
            "source_url_or_search_macro": '"athlete NWSL photo"',
            "source_domain": "",
            "evidence_use": "lead",
            "identity_anchor_use": "none",
            "rights_review_note": "none",
            "roster_truth_status": "asserted_current_roster",
            "source_url": "https://example.com/photo",
            "entity_id": "nwsl:player",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review",
            "download_approved": "yes",
            "allowed_for_download_approved_yes": "true",
            "manual_next_action": "download it",
            "review_only": "false",
            "publish_ready": "true",
            "approval_state_change": "approve",
            "publish_action": "publish",
        }
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_womens_soccer_starter_rows(invalid_rows)}

    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("source_url", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("entity_id", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("rights_class", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("identity_confidence", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("intended_review_only_use", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("download_approved", "generated_rows_must_not_approve_downloads") in issue_pairs
    assert ("allowed_for_download_approved_yes", "starter_rows_never_download_approved") in issue_pairs
    assert ("review_only", "starter_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "starter_rows_must_not_be_publish_ready") in issue_pairs
    assert ("approval_state_change", "starter_rows_must_not_change_approval_state") in issue_pairs
    assert ("publish_action", "starter_rows_must_not_publish") in issue_pairs
    assert ("roster_truth_status", "roster_truth_must_not_be_asserted") in issue_pairs


def test_external_research_source_map_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    invalid_rows = [
        {
            "sport": "Basketball",
            "league_entity": "WNBA",
            "official_gallery_url_or_macro": "https://example.com/gallery",
            "roster_player_directory_url_or_macro": "https://example.com/roster",
            "media_guide_stats_profile_url_or_macro": "",
            "editorial_wire_newsroom_sources": "https://example.com/wire",
            "official_social": "",
            "gray_area_public_creator_fan_surfaces": "",
            "source_category": "free_web_image",
            "source_domain": "example.com",
            "likely_search_query_macro": "player photo",
            "identity_verification_anchor": "https://example.com/roster",
            "rights_posture_recommendation": "reuse_ok",
            "limitations_red_flags": "none",
            "manual_next_action": "download it",
            "source_url": "https://example.com/photo",
            "entity_id": "wnba:player",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review",
            "download_approved": "yes",
            "review_only": "false",
            "publish_ready": "true",
            "approval_state_change": "approve",
            "publish_action": "publish",
        }
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_external_research_source_map_rows(invalid_rows)}

    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("rights_posture_recommendation", "invalid_rights_posture_recommendation") in issue_pairs
    assert ("source_url", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("entity_id", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("rights_class", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("identity_confidence", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("intended_review_only_use", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("download_approved", "generated_rows_must_not_approve_downloads") in issue_pairs
    assert ("review_only", "external_research_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "external_research_rows_must_not_be_publish_ready") in issue_pairs
    assert ("approval_state_change", "external_research_rows_must_not_change_approval_state") in issue_pairs
    assert ("publish_action", "external_research_rows_must_not_publish") in issue_pairs


def test_action_photo_candidate_queue_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    invalid_rows = [
        {
            "candidate_queue_id": "APQBAD",
            "sport": "basketball",
            "league_entity": "WNBA",
            "target_entity_or_player": "player",
            "source_family": "unknown",
            "source_category": "free_web_image",
            "source_url_or_search_macro": "player photo",
            "candidate_photo_url": "https://example.com/photo.jpg",
            "evidence_url": "https://example.com/evidence",
            "evidence_summary": "already found",
            "identity_anchor_url": "https://example.com/roster",
            "action_moment_type": "drive",
            "render_fit_potential": "high",
            "rights_posture_metadata": "reuse_ok",
            "fair_use_context_note": "fair use",
            "download_approved": "yes",
            "source_url": "https://example.com/photo.jpg",
            "entity_id": "wnba:player",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review",
            "quarantine_target_hint": "assets/not_quarantine.jpg",
            "manual_reviewer": "bot",
            "manual_review_status": "approved_for_download",
            "manual_next_action": "download it",
            "review_only": "false",
            "publish_ready": "true",
        }
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_action_photo_candidate_queue_rows(invalid_rows)}

    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("rights_posture_metadata", "invalid_rights_posture_metadata") in issue_pairs
    assert ("candidate_photo_url", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("evidence_url", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("evidence_summary", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("identity_anchor_url", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("manual_reviewer", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("source_url", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("entity_id", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("rights_class", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("identity_confidence", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("intended_review_only_use", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("download_approved", "generated_rows_must_not_approve_downloads") in issue_pairs
    assert ("quarantine_target_hint", "quarantine_hint_must_stay_in_review_only_root") in issue_pairs
    assert ("manual_review_status", "generated_queue_rows_must_start_not_reviewed") in issue_pairs
    assert ("review_only", "candidate_queue_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "candidate_queue_rows_must_not_be_publish_ready") in issue_pairs


def test_action_photo_research_packet_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    queue_rows = module.action_photo_candidate_queue_rows()
    invalid_rows = [
        {
            "research_task_id": "APRBAD",
            "researcher_lane": "auto_downloader",
            "candidate_queue_id": "APQ999",
            "sport": "basketball",
            "league_entity": "WNBA",
            "target_entity_or_player": "operator_fill_player_or_team",
            "source_family": "unknown",
            "source_category": "free_web_image",
            "source_url_or_search_macro": "player photo",
            "action_moment_type": "drive",
            "render_fit_potential": "high",
            "rights_posture_metadata": "reuse_ok",
            "copy_ready_prompt": "Find and download a photo.",
            "paste_back_schema": "candidate_queue_id,candidate_photo_url",
            "candidate_photo_url": "https://example.com/photo.jpg",
            "evidence_url": "https://example.com/evidence",
            "evidence_summary": "found it",
            "identity_anchor_url": "https://example.com/roster",
            "source_url": "https://example.com/photo.jpg",
            "entity_id": "wnba:player",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review",
            "notes": "ready",
            "operator_verify_required": "no",
            "download_approved": "yes",
            "manual_next_action": "publish",
            "review_only": "false",
            "publish_ready": "true",
        }
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_action_photo_research_packet_rows(invalid_rows, queue_rows)}

    assert ("candidate_queue_id", "candidate_queue_id_not_in_queue") in issue_pairs
    assert ("researcher_lane", "invalid_researcher_lane") in issue_pairs
    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("rights_posture_metadata", "invalid_rights_posture_metadata") in issue_pairs
    assert ("copy_ready_prompt", "copy_ready_prompt_missing_required_guardrail") in issue_pairs
    assert ("paste_back_schema", "paste_back_schema_mismatch") in issue_pairs
    assert ("candidate_photo_url", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("evidence_url", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("evidence_summary", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("identity_anchor_url", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("source_url", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("entity_id", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("rights_class", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("identity_confidence", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("intended_review_only_use", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("notes", "generated_research_result_field_must_stay_blank") in issue_pairs
    assert ("operator_verify_required", "operator_verify_required_must_default_yes") in issue_pairs
    assert ("download_approved", "generated_rows_must_not_approve_downloads") in issue_pairs
    assert ("review_only", "research_packet_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "research_packet_rows_must_not_be_publish_ready") in issue_pairs


def test_action_photo_research_return_intake_validator_allows_complete_human_return_row() -> None:
    module = load_module()
    queue_rows = module.action_photo_candidate_queue_rows()
    return_rows = module.action_photo_research_return_intake_rows(queue_rows)
    return_rows[0].update(
        {
            "candidate_photo_url": "https://example.com/photo-candidate-page",
            "evidence_url": "https://example.com/match-recap",
            "evidence_summary": "official recap confirms player and event context",
            "identity_anchor_url": "https://example.com/player-profile",
            "source_url": "https://example.com/photo-candidate-page",
            "entity_id": "wnba:operator_fill_player:apq001",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review_only_candidate_research_quarantine_decision_prep",
            "notes": "operator still needs source and identity verification",
            "operator_verify_required": "yes",
            "manual_reviewer": "operator_initials",
            "manual_review_status": "needs_operator_verify",
        }
    )

    assert module.validate_action_photo_research_return_intake_rows(return_rows, queue_rows) == []


def test_action_photo_research_return_intake_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    queue_rows = module.action_photo_candidate_queue_rows()
    invalid_rows = module.action_photo_research_return_intake_rows(queue_rows)
    invalid_rows[0].update(
        {
            "candidate_queue_id": "APQ999",
            "candidate_photo_url": "https://example.com/photo.jpg",
            "evidence_summary": "approved render-ready image",
            "download_approved": "yes",
            "quarantine_target_hint": "assets/not_quarantine.jpg",
            "operator_verify_required": "maybe",
            "manual_review_status": "approved",
            "review_only": "false",
            "publish_ready": "true",
        }
    )
    invalid_rows[1]["candidate_queue_id"] = invalid_rows[2]["candidate_queue_id"]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_action_photo_research_return_intake_rows(invalid_rows, queue_rows)}

    assert ("candidate_queue_id", "candidate_queue_id_not_in_queue") in issue_pairs
    assert ("candidate_queue_id", "duplicate_candidate_queue_id_in_return_intake") in issue_pairs
    assert ("evidence_url", "required_when_research_return_pasted") in issue_pairs
    assert ("source_url", "required_when_research_return_pasted") in issue_pairs
    assert ("identity_anchor_url", "required_when_research_return_pasted") in issue_pairs
    assert ("rights_class", "required_when_research_return_pasted") in issue_pairs
    assert ("identity_confidence", "required_when_research_return_pasted") in issue_pairs
    assert ("source_url", "required_when_download_approved_yes") in issue_pairs
    assert ("entity_id", "required_when_download_approved_yes") in issue_pairs
    assert ("rights_class", "required_when_download_approved_yes") in issue_pairs
    assert ("identity_confidence", "required_when_download_approved_yes") in issue_pairs
    assert ("intended_review_only_use", "required_when_download_approved_yes") in issue_pairs
    assert ("quarantine_target_hint", "quarantine_hint_must_stay_in_review_only_root") in issue_pairs
    assert ("operator_verify_required", "operator_verify_required_must_be_yes_no_or_blank") in issue_pairs
    assert ("manual_review_status", "invalid_manual_review_status") in issue_pairs
    assert ("evidence_summary", "approval_or_render_ready_language_not_allowed") in issue_pairs
    assert ("manual_review_status", "approval_or_render_ready_language_not_allowed") in issue_pairs
    assert ("review_only", "research_return_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "research_return_rows_must_not_be_publish_ready") in issue_pairs


def test_action_photo_research_run_bundle_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    expected_paths = module.research_run_bundle_artifact_paths().values()
    invalid_rows = [
        {
            "bundle_step_id": "APRBAD",
            "operator_lane": "",
            "task_scope": "bad",
            "artifact_paths": "data/asset_registry/action_photo_candidates/missing.md",
            "copy_ready_instruction": "send it",
            "paste_back_location": "data/asset_registry/action_photo_candidates/missing.csv",
            "next_conductor_action": "",
            "download_approved": "yes",
            "review_only": "false",
            "publish_ready": "true",
        },
        {
            "bundle_step_id": "APRBAD",
            "operator_lane": "manual_research",
            "task_scope": "duplicate",
            "artifact_paths": "|".join(expected_paths),
            "copy_ready_instruction": "Collect URL/evidence rows only and do not download.",
            "paste_back_location": "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv",
            "next_conductor_action": "validate",
            "download_approved": "no",
            "review_only": "true",
            "publish_ready": "false",
        },
    ]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_action_photo_research_run_bundle_rows(invalid_rows, expected_paths)}

    assert ("bundle_step_id", "duplicate_bundle_step_id") in issue_pairs
    assert ("operator_lane", "required_bundle_field_blank") in issue_pairs
    assert ("artifact_paths", "bundle_artifact_paths_mismatch") in issue_pairs
    assert ("paste_back_location", "paste_back_location_not_in_bundle_paths") in issue_pairs
    assert ("copy_ready_instruction", "bundle_instruction_missing_research_guardrail") in issue_pairs
    assert ("next_conductor_action", "required_bundle_field_blank") in issue_pairs
    assert ("download_approved", "bundle_rows_must_not_approve_downloads") in issue_pairs
    assert ("review_only", "bundle_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "bundle_rows_must_not_be_publish_ready") in issue_pairs


def test_action_photo_quarantine_preflight_marks_complete_human_return_ready_without_approval() -> None:
    module = load_module()
    return_rows = module.action_photo_research_return_intake_rows(module.action_photo_candidate_queue_rows())
    return_rows[0].update(
        {
            "candidate_photo_url": "https://example.com/game-action-photo",
            "evidence_url": "https://example.com/game-recap",
            "evidence_summary": "game action shows a drive and confirms event context",
            "identity_anchor_url": "https://example.com/player-profile",
            "source_url": "https://example.com/game-action-photo",
            "entity_id": "wnba:player:apq001",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review_only_action_photo_candidate_quarantine_decision_prep",
            "notes": "action frame with visible game context",
            "manual_review_status": "needs_operator_verify",
        }
    )

    preflight_rows = module.action_photo_quarantine_preflight_rows(return_rows)

    assert preflight_rows[0]["ready_for_human_download_decision"] == "yes"
    assert preflight_rows[0]["missing_required_fields"] == ""
    assert preflight_rows[0]["action_photo_status"] == "action_photo_candidate"
    assert preflight_rows[0]["identity_confidence_status"] == "identity_ready_for_human_review"
    assert preflight_rows[0]["download_approved"] == "no"
    assert module.validate_action_photo_quarantine_preflight_rows(preflight_rows, return_rows) == []


def test_action_photo_quarantine_preflight_blocks_duplicate_headshot_and_weak_identity() -> None:
    module = load_module()
    return_rows = module.action_photo_research_return_intake_rows(module.action_photo_candidate_queue_rows())
    for row in return_rows[:2]:
        row.update(
            {
                "candidate_photo_url": "https://example.com/same-roster-headshot",
                "evidence_url": "https://example.com/evidence",
                "evidence_summary": "roster portrait/headshot with no game action",
                "identity_anchor_url": "https://example.com/player-profile",
                "source_url": "https://example.com/same-roster-headshot",
                "entity_id": "wnba:duplicate",
                "rights_class": "official_review_needed",
                "identity_confidence": "weak",
                "intended_review_only_use": "review_only_candidate_research",
                "notes": "headshot only",
            }
        )

    preflight_rows = module.action_photo_quarantine_preflight_rows(return_rows)

    assert preflight_rows[0]["ready_for_human_download_decision"] == "no"
    assert preflight_rows[0]["duplicate_candidate_key"] == "duplicate_candidate_key"
    assert preflight_rows[0]["action_photo_status"] == "blocked_headshot_or_portrait_cue"
    assert preflight_rows[0]["identity_confidence_status"] == "identity_weak_or_stale_manual_verify"
    assert preflight_rows[1]["duplicate_candidate_key"] == "duplicate_candidate_key"
    assert module.validate_action_photo_quarantine_preflight_rows(preflight_rows, return_rows) == []


def test_action_photo_quarantine_preflight_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    return_rows = module.action_photo_research_return_intake_rows(module.action_photo_candidate_queue_rows())
    preflight_rows = module.action_photo_quarantine_preflight_rows(return_rows)
    preflight_rows[0].update(
        {
            "ready_for_human_download_decision": "yes",
            "missing_required_fields": "source_url",
            "download_approved": "yes",
            "quarantine_target_hint": "assets/not_quarantine.jpg",
            "review_only": "false",
            "publish_ready": "true",
        }
    )
    preflight_rows[1]["candidate_queue_id"] = preflight_rows[2]["candidate_queue_id"]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_action_photo_quarantine_preflight_rows(preflight_rows, return_rows)}

    assert ("ready_for_human_download_decision", "ready_row_has_missing_required_fields") in issue_pairs
    assert ("ready_for_human_download_decision", "ready_row_identity_not_strong_enough") in issue_pairs
    assert ("ready_for_human_download_decision", "ready_row_not_action_photo_candidate") in issue_pairs
    assert ("download_approved", "preflight_rows_must_not_approve_downloads") in issue_pairs
    assert ("quarantine_target_hint", "quarantine_hint_must_stay_in_review_only_root") in issue_pairs
    assert ("review_only", "preflight_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "preflight_rows_must_not_be_publish_ready") in issue_pairs
    assert ("candidate_queue_id", "duplicate_candidate_queue_id_in_preflight") in issue_pairs


def test_wnba_final_score_hero_target_validator_blocks_unsafe_rows() -> None:
    module = load_module()
    invalid_rows = module.wnba_final_score_hero_action_photo_target_rows()
    invalid_rows[0].update(
        {
            "source_category": "free_web_image",
            "preferred_action_cues": "portrait",
            "low_value_cues": "",
            "render_gap": "looks fine",
            "candidate_photo_url": "https://example.com/photo.jpg",
            "evidence_url": "https://example.com/evidence",
            "evidence_summary": "already found",
            "identity_anchor_url": "https://example.com/player",
            "source_url": "https://example.com/photo.jpg",
            "entity_id": "wnba:indiana_fever:kelsey_mitchell",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review",
            "operator_verify_required": "no",
            "download_approved": "yes",
            "quarantine_target_hint": "assets/not_quarantine.jpg",
            "manual_reviewer": "bot",
            "manual_review_status": "approved_for_download",
            "review_only": "false",
            "publish_ready": "true",
        }
    )
    invalid_rows[1]["target_id"] = invalid_rows[2]["target_id"]
    invalid_rows[3]["source_url_or_search_macro"] = invalid_rows[4]["source_url_or_search_macro"]
    invalid_rows[3]["target_moment_type"] = invalid_rows[4]["target_moment_type"]
    invalid_rows[3]["source_category"] = invalid_rows[4]["source_category"]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_wnba_final_score_hero_action_photo_target_rows(invalid_rows)}

    assert ("target_id", "duplicate_target_id") in issue_pairs
    assert ("source_url_or_search_macro", "duplicate_wnba_hero_target_key") in issue_pairs
    assert ("source_category", "invalid_controlled_vocabulary") in issue_pairs
    assert ("candidate_photo_url", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("evidence_url", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("evidence_summary", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("identity_anchor_url", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("manual_reviewer", "generated_manual_candidate_field_must_stay_blank") in issue_pairs
    assert ("source_url", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("entity_id", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("rights_class", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("identity_confidence", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("intended_review_only_use", "generated_local_download_law_field_must_stay_blank") in issue_pairs
    assert ("download_approved", "generated_rows_must_not_approve_downloads") in issue_pairs
    assert ("operator_verify_required", "operator_verify_required_must_default_yes") in issue_pairs
    assert ("manual_review_status", "generated_target_rows_must_start_not_reviewed") in issue_pairs
    assert ("quarantine_target_hint", "quarantine_hint_must_stay_in_review_only_root") in issue_pairs
    assert ("preferred_action_cues", "missing_action_hero_cues") in issue_pairs
    assert ("low_value_cues", "required_wnba_hero_target_field_blank") in issue_pairs
    assert ("low_value_cues", "missing_headshot_portrait_static_pose_cues") in issue_pairs
    assert ("render_gap", "render_gap_must_name_headshot_bridge") in issue_pairs
    assert ("review_only", "wnba_hero_target_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "wnba_hero_target_rows_must_not_be_publish_ready") in issue_pairs
