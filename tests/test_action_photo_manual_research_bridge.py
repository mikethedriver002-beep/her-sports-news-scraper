from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_action_photo_manual_research_bridge_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_action_photo_manual_research_bridge_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def seed_bridge_inputs(tmp_path: Path) -> None:
    action_root = tmp_path / "data/asset_registry/action_photo_candidates"
    soccer_root = tmp_path / "data/asset_registry/womens_soccer"
    hs_root = tmp_path / "data/asset_registry"
    action_root.mkdir(parents=True)
    soccer_root.mkdir(parents=True)
    hs_root.mkdir(parents=True, exist_ok=True)

    write_csv(
        soccer_root / "womens_soccer_action_photo_research_next.csv",
        [
            {
                "research_next_rank": "1",
                "source_candidate_url": "https://club.example/match-recap",
                "source_url": "",
                "rights_class": "",
                "identity_confidence": "",
                "candidate_ready_for_later_human_download_decision_review": "no",
                "download_approved": "no",
            },
            {
                "research_next_rank": "2",
                "source_candidate_url": "https://league.example/gallery",
                "source_url": "",
                "rights_class": "",
                "identity_confidence": "",
                "candidate_ready_for_later_human_download_decision_review": "no",
                "download_approved": "no",
            },
        ],
        [
            "research_next_rank",
            "source_candidate_url",
            "source_url",
            "rights_class",
            "identity_confidence",
            "candidate_ready_for_later_human_download_decision_review",
            "download_approved",
        ],
    )
    (soccer_root / "womens_soccer_action_photo_research_next.md").write_text("# Soccer AP next\n", encoding="utf-8")
    (soccer_root / "womens_soccer_action_photo_research_next.json").write_text(
        json.dumps(
            {
                "status": "womens_soccer_action_photo_research_next_ready",
                "research_next_rows": 2,
                "blank_source_url_rows": 2,
                "blank_rights_class_rows": 2,
                "blank_identity_confidence_rows": 2,
                "candidate_ready_for_later_human_download_decision_review_rows": 0,
            }
        ),
        encoding="utf-8",
    )
    write_csv(
        hs_root / "hockey_softball_action_photo_research_handoff.csv",
        [
            {
                "handoff_rank": "AH01",
                "source_search_macro": '"[athlete]" PWHL gallery',
                "source_url": "",
                "rights_class": "",
                "identity_confidence": "",
                "later_human_download_decision_review_eligible": "no",
                "download_approved": "no",
            }
        ],
        [
            "handoff_rank",
            "source_search_macro",
            "source_url",
            "rights_class",
            "identity_confidence",
            "later_human_download_decision_review_eligible",
            "download_approved",
        ],
    )
    (hs_root / "hockey_softball_action_photo_research_handoff.md").write_text("# H/S AP handoff\n", encoding="utf-8")
    (hs_root / "hockey_softball_action_photo_research_handoff.json").write_text(
        json.dumps(
            {
                "status": "hockey_softball_action_photo_research_handoff_ready",
                "rows": 1,
                "blank_source_url_rows": 1,
                "blank_rights_class_rows": 1,
                "blank_identity_confidence_rows": 1,
                "later_human_download_decision_review_eligible_rows": 0,
            }
        ),
        encoding="utf-8",
    )
    (action_root / "review_only_action_photo_research_return_import_review_v1.md").write_text("# Import review\n", encoding="utf-8")
    (action_root / "review_only_action_photo_research_return_import_review_v1.json").write_text(
        json.dumps(
            {
                "status": "action_photo_research_return_import_review_ready",
                "import_review_rows": 10,
                "rows_with_research_return_data": 0,
                "ready_for_later_human_download_decision_review_rows": 0,
            }
        ),
        encoding="utf-8",
    )


def test_manual_research_bridge_summarizes_existing_lanes_without_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    seed_bridge_inputs(tmp_path)
    module = load_module()

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_manual_research_bridge_v1.csv")
    card_rows = read_csv(root / "review_only_action_photo_manual_first_action_cards_v1.csv")
    checklist_rows = read_csv(root / "review_only_action_photo_manual_return_evidence_checklist_v1.csv")
    triage_rows = read_csv(root / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_manual_research_bridge_v1.json").read_text(encoding="utf-8"))
    cards_manifest = json.loads((root / "review_only_action_photo_manual_first_action_cards_v1.json").read_text(encoding="utf-8"))
    checklist_manifest = json.loads((root / "review_only_action_photo_manual_return_evidence_checklist_v1.json").read_text(encoding="utf-8"))
    triage_manifest = json.loads((root / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_manual_research_bridge_v1.md").read_text(encoding="utf-8")
    cards_markdown = (root / "review_only_action_photo_manual_first_action_cards_v1.md").read_text(encoding="utf-8")
    checklist_markdown = (root / "review_only_action_photo_manual_return_evidence_checklist_v1.md").read_text(encoding="utf-8")
    triage_markdown = (root / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_manual_research_bridge_ready"
    assert manifest["bridge_rows"] == 2
    assert manifest["source_rows"] == 3
    assert manifest["womens_soccer_source_rows"] == 2
    assert manifest["hockey_softball_source_rows"] == 1
    assert manifest["shared_import_review_rows"] == 10
    assert manifest["shared_import_rows_with_data"] == 0
    assert manifest["generated_download_approval_rows"] == 0
    assert manifest["first_action_cards_md"] == "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_first_action_cards_v1.md"
    assert manifest["return_evidence_checklist_md"] == "data/asset_registry/action_photo_candidates/review_only_action_photo_manual_return_evidence_checklist_v1.md"
    assert manifest["renderer_unblock_triage_md"] == "data/asset_registry/action_photo_candidates/review_only_action_photo_renderer_unblock_manual_return_triage_v1.md"
    assert manifest["source_fetching"] is False
    assert manifest["auto_source_enablement"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert [row["bridge_lane"] for row in rows] == ["women_soccer_action_photo", "hockey_softball_action_photo"]
    assert all(row["download_approved"] == "no" for row in rows)
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["source_fetching"] == "false" for row in rows)
    assert rows[0]["first_manual_source_lead"] == "https://club.example/match-recap"
    assert cards_manifest["status"] == "action_photo_manual_first_action_cards_ready"
    assert cards_manifest["first_action_cards"] == 2
    assert cards_manifest["validation_issue_count"] == 0
    assert cards_manifest["generated_download_approval_rows"] == 0
    assert cards_manifest["source_fetching"] is False
    assert cards_manifest["auto_source_enablement"] is False
    assert cards_manifest["asset_downloads"] is False
    assert cards_manifest["headshot_writes"] is False
    assert cards_manifest["approved_marker_writes"] is False
    assert cards_manifest["publish_ready"] is False
    assert [row["card_id"] for row in card_rows] == ["APFAC01", "APFAC02"]
    assert card_rows[0]["bridge_lane"] == "women_soccer_action_photo"
    assert card_rows[0]["open_source_row_ref"] == "data/asset_registry/womens_soccer/womens_soccer_action_photo_research_next.csv#row=2"
    assert card_rows[0]["manual_source_lead"] == "https://club.example/match-recap"
    assert card_rows[0]["paste_target_csv"] == "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    assert card_rows[0]["download_approved"] == "no"
    assert card_rows[0]["source_fetching"] == "false"
    assert card_rows[0]["auto_source_enablement"] == "false"
    assert card_rows[0]["asset_downloads"] == "false"
    assert "shared research return intake" in markdown
    assert "does not fetch sources, download images" in markdown
    assert "Run after paste" in cards_markdown
    assert "does not fetch sources, download images" in cards_markdown
    assert checklist_manifest["status"] == "action_photo_manual_return_evidence_checklist_ready"
    assert checklist_manifest["checklist_rows"] == 2
    assert checklist_manifest["generated_ready_rows"] == 0
    assert checklist_manifest["generated_download_approval_rows"] == 0
    assert checklist_manifest["source_fetching"] is False
    assert checklist_manifest["auto_source_enablement"] is False
    assert checklist_manifest["asset_downloads"] is False
    assert checklist_manifest["headshot_writes"] is False
    assert checklist_manifest["approved_marker_writes"] is False
    assert checklist_manifest["publish_ready"] is False
    assert [row["checklist_id"] for row in checklist_rows] == ["APFEC01", "APFEC02"]
    assert [row["card_id"] for row in checklist_rows] == ["APFAC01", "APFAC02"]
    assert checklist_rows[0]["candidate_ready_for_later_human_download_decision_review"] == "no"
    assert checklist_rows[0]["download_approved"] == "no"
    assert checklist_rows[0]["source_fetching"] == "false"
    assert checklist_rows[0]["asset_downloads"] == "false"
    assert "does not fetch sources, inspect URLs, download images" in checklist_markdown
    assert "Missing until human paste" in checklist_markdown
    assert triage_manifest["status"] == "action_photo_renderer_unblock_manual_return_triage_ready"
    assert triage_manifest["triage_rows"] == 2
    assert triage_manifest["renderer_candidate_status"] == "action_photo_candidate_status=not_available_to_renderer"
    assert triage_manifest["generated_ready_rows"] == 0
    assert triage_manifest["generated_download_approval_rows"] == 0
    assert triage_manifest["source_fetching"] is False
    assert triage_manifest["auto_source_enablement"] is False
    assert triage_manifest["asset_downloads"] is False
    assert triage_manifest["headshot_writes"] is False
    assert triage_manifest["approved_marker_writes"] is False
    assert triage_manifest["publish_ready"] is False
    assert [row["triage_id"] for row in triage_rows] == ["APRUT01", "APRUT02"]
    assert [row["card_id"] for row in triage_rows] == ["APFAC01", "APFAC02"]
    assert triage_rows[0]["manual_priority"] == "P0_renderer_unblock_first_return"
    assert triage_rows[0]["candidate_ready_for_later_human_download_decision_review"] == "no"
    assert triage_rows[0]["download_approved"] == "no"
    assert triage_rows[0]["source_fetching"] == "false"
    assert triage_rows[0]["asset_downloads"] == "false"
    assert "blocked_action_photo_return_needed" in triage_markdown
    assert "does not fetch sources, inspect URLs, download images" in triage_markdown


def test_manual_research_bridge_validator_blocks_guardrail_drift() -> None:
    module = load_module()
    rows = [
        {
            field: "false"
            for field in module.BRIDGE_FIELDS
        }
    ]
    rows[0].update(
        {
            "bridge_rank": "01",
            "source_board_md": "data/asset_registry/example.md",
            "download_approved": "approve",
            "review_only": "false",
            "source_fetching": "true",
            "auto_source_enablement": "true",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "publish_ready": "true",
        }
    )

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_rows(rows)}

    assert ("download_approved", "generated_bridge_must_not_approve_downloads") in issue_pairs
    assert ("review_only", "guardrail_field_invalid") in issue_pairs
    assert ("source_fetching", "guardrail_field_invalid") in issue_pairs
    assert ("auto_source_enablement", "guardrail_field_invalid") in issue_pairs
    assert ("asset_downloads", "guardrail_field_invalid") in issue_pairs
    assert ("headshot_writes", "guardrail_field_invalid") in issue_pairs
    assert ("approved_marker_writes", "guardrail_field_invalid") in issue_pairs
    assert ("publish_ready", "guardrail_field_invalid") in issue_pairs

    card_rows = [
        {
            field: "false"
            for field in module.FIRST_ACTION_CARD_FIELDS
        }
    ]
    card_rows[0].update(
        {
            "card_id": "APFAC01",
            "open_source_row_ref": "data/asset_registry/example.csv#row=2",
            "download_approved": "approve",
            "review_only": "false",
            "source_fetching": "true",
            "auto_source_enablement": "true",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "publish_ready": "true",
        }
    )
    card_issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_first_action_cards(card_rows)}

    assert ("download_approved", "generated_card_must_not_approve_downloads") in card_issue_pairs
    assert ("review_only", "guardrail_field_invalid") in card_issue_pairs
    assert ("source_fetching", "guardrail_field_invalid") in card_issue_pairs
    assert ("auto_source_enablement", "guardrail_field_invalid") in card_issue_pairs
    assert ("asset_downloads", "guardrail_field_invalid") in card_issue_pairs
    assert ("headshot_writes", "guardrail_field_invalid") in card_issue_pairs
    assert ("approved_marker_writes", "guardrail_field_invalid") in card_issue_pairs
    assert ("publish_ready", "guardrail_field_invalid") in card_issue_pairs

    checklist_rows = [
        {
            field: "false"
            for field in module.RETURN_EVIDENCE_CHECKLIST_FIELDS
        }
    ]
    checklist_rows[0].update(
        {
            "checklist_id": "APFEC01",
            "card_id": "APFAC01",
            "candidate_ready_for_later_human_download_decision_review": "yes",
            "download_approved": "approve",
            "review_only": "false",
            "source_fetching": "true",
            "auto_source_enablement": "true",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "publish_ready": "true",
        }
    )
    checklist_issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_return_evidence_checklist(checklist_rows)}

    assert (
        "candidate_ready_for_later_human_download_decision_review",
        "generated_checklist_must_not_mark_ready",
    ) in checklist_issue_pairs
    assert ("download_approved", "generated_checklist_must_not_approve_downloads") in checklist_issue_pairs
    assert ("review_only", "guardrail_field_invalid") in checklist_issue_pairs
    assert ("source_fetching", "guardrail_field_invalid") in checklist_issue_pairs
    assert ("auto_source_enablement", "guardrail_field_invalid") in checklist_issue_pairs
    assert ("asset_downloads", "guardrail_field_invalid") in checklist_issue_pairs
    assert ("headshot_writes", "guardrail_field_invalid") in checklist_issue_pairs
    assert ("approved_marker_writes", "guardrail_field_invalid") in checklist_issue_pairs
    assert ("publish_ready", "guardrail_field_invalid") in checklist_issue_pairs

    triage_rows = [
        {
            field: "false"
            for field in module.RENDERER_UNBLOCK_TRIAGE_FIELDS
        }
    ]
    triage_rows[0].update(
        {
            "triage_id": "APRUT01",
            "card_id": "APFAC01",
            "open_source_row_ref": "data/asset_registry/example.csv#row=2",
            "fields_required_before_later_gate_review": "source_url|entity_id|rights_class|identity_confidence|intended_review_only_use",
            "candidate_ready_for_later_human_download_decision_review": "yes",
            "download_approved": "approve",
            "review_only": "false",
            "source_fetching": "true",
            "auto_source_enablement": "true",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "publish_ready": "true",
        }
    )
    triage_issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_renderer_unblock_triage(triage_rows)}

    assert (
        "candidate_ready_for_later_human_download_decision_review",
        "generated_triage_must_not_mark_ready",
    ) in triage_issue_pairs
    assert ("download_approved", "generated_triage_must_not_approve_downloads") in triage_issue_pairs
    assert ("review_only", "guardrail_field_invalid") in triage_issue_pairs
    assert ("source_fetching", "guardrail_field_invalid") in triage_issue_pairs
    assert ("auto_source_enablement", "guardrail_field_invalid") in triage_issue_pairs
    assert ("asset_downloads", "guardrail_field_invalid") in triage_issue_pairs
    assert ("headshot_writes", "guardrail_field_invalid") in triage_issue_pairs
    assert ("approved_marker_writes", "guardrail_field_invalid") in triage_issue_pairs
    assert ("publish_ready", "guardrail_field_invalid") in triage_issue_pairs
