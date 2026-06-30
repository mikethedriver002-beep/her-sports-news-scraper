from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_action_photo_to_renderer_bridge_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_action_photo_to_renderer_bridge_v1", SCRIPT)
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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_bridge_inputs(tmp_path: Path) -> None:
    action_root = tmp_path / "data/asset_registry/action_photo_candidates"
    handoff_root = tmp_path / "render_handoff_top_packet"
    action_root.mkdir(parents=True)
    handoff_root.mkdir(parents=True)
    (action_root / "review_only_action_photo_external_research_return_review_v1.md").write_text(
        "# External return review\n",
        encoding="utf-8",
    )
    write_csv(
        action_root / "review_only_action_photo_external_research_return_review_v1.csv",
        [
            {
                "review_id": "APER001",
                "candidate_queue_id": "APQ001",
                "external_return_present": "yes",
                "normalized_candidate_page_url": "https://source.example/game-gallery",
                "candidate_photo_url_direct_image_hold": "yes",
                "identity_vocabulary_mismatch": "yes",
                "candidate_ready_for_later_human_download_decision_review": "no",
                "download_approved": "no",
                "manual_next_action": "Use the source page lead; do not treat the direct image URL as source-page-safe.",
            }
        ],
        [
            "review_id",
            "candidate_queue_id",
            "external_return_present",
            "normalized_candidate_page_url",
            "candidate_photo_url_direct_image_hold",
            "identity_vocabulary_mismatch",
            "candidate_ready_for_later_human_download_decision_review",
            "download_approved",
            "manual_next_action",
        ],
    )
    write_json(
        action_root / "review_only_action_photo_external_research_return_review_v1.json",
        {
            "status": "action_photo_external_research_return_review_ready",
            "review_rows": 10,
            "external_return_rows": 8,
            "missing_external_return_rows": 2,
            "direct_image_url_hold_rows": 8,
            "identity_vocabulary_mismatch_rows": 8,
            "ready_for_later_human_download_decision_review_rows": 0,
            "generated_download_approval_rows": 0,
            "review_only": True,
            "source_fetching": False,
            "auto_source_enablement": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
            "approval_state_change": False,
            "publish_ready": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "paid_apis": False,
        },
    )
    write_json(
        action_root / "review_only_action_photo_research_return_import_review_v1.json",
        {
            "status": "action_photo_research_return_import_review_ready",
            "import_review_rows": 10,
            "rows_with_research_return_data": 0,
            "ready_for_later_human_download_decision_review_rows": 0,
            "human_intake_download_approved_yes_rows": 0,
            "generated_download_approved_yes_rows": 0,
            "source_fetching": False,
            "auto_source_enablement": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
        },
    )
    write_json(
        action_root / "review_only_action_photo_manual_research_bridge_v1.json",
        {
            "status": "action_photo_manual_research_bridge_ready",
            "bridge_rows": 2,
            "source_rows": 103,
            "shared_import_rows_with_data": 0,
            "candidate_ready_for_later_human_download_decision_review_rows": 0,
            "generated_download_approval_rows": 0,
            "source_fetching": False,
            "auto_source_enablement": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
        },
    )
    write_csv(
        action_root / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.csv",
        [
            {
                "triage_id": "APRUT01",
                "card_id": "APFAC01",
                "manual_priority": "P0_renderer_unblock_first_return",
                "manual_source_lead": "https://source.example/game-gallery",
                "manual_next_action": "Paste human-reviewed action-photo metadata into the shared return intake.",
                "candidate_ready_for_later_human_download_decision_review": "no",
                "download_approved": "no",
            }
        ],
        [
            "triage_id",
            "card_id",
            "manual_priority",
            "manual_source_lead",
            "manual_next_action",
            "candidate_ready_for_later_human_download_decision_review",
            "download_approved",
        ],
    )
    write_json(
        action_root / "review_only_action_photo_renderer_unblock_manual_return_triage_v1.json",
        {
            "status": "action_photo_renderer_unblock_manual_return_triage_ready",
            "triage_rows": 2,
            "renderer_candidate_status": "action_photo_candidate_status=not_available_to_renderer",
            "generated_ready_rows": 0,
            "generated_download_approval_rows": 0,
            "source_fetching": False,
            "auto_source_enablement": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
        },
    )
    write_json(
        action_root / "review_only_action_photo_quarantine_preflight_v1.json",
        {
            "status": "action_photo_quarantine_preflight_ready",
            "preflight_rows": 10,
            "ready_for_human_download_decision_rows": 0,
            "lead_only_rows": 10,
            "download_approved_yes_rows": 0,
            "human_intake_download_approved_yes_rows": 0,
            "generated_download_approved_yes_rows": 0,
            "missing_required_field_counts": {"source_url": 10},
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
        },
    )
    write_json(
        handoff_root / "handoff_manifest.json",
        {
            "handoff_status": "ready_for_manual_review",
            "packet": {
                "packet_id": "render_packet_001",
                "title": "Golden State Valkyries beat New York Liberty",
                "hero_asset_required": "approved_local_athlete_photo",
                "active_asset_stop_go": "hold_required_manual_asset_review",
                "active_logo_readiness_status": "hold_logo_review_required",
            },
            "guardrails": {
                "review_only": True,
                "auto_approval": False,
                "auto_render": False,
                "auto_publish": False,
                "asset_downloads": False,
                "file_movement": False,
                "paid_apis": False,
                "publish_ready_lane": False,
                "publishing": False,
            },
        },
    )


def test_to_renderer_bridge_rolls_up_action_photo_blockers_without_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    seed_bridge_inputs(tmp_path)
    module = load_module()

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_to_renderer_bridge_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_to_renderer_bridge_v1.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_to_renderer_bridge_v1.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_to_renderer_bridge_ready"
    assert manifest["bridge_rows"] == 1
    assert manifest["bridge_status"] == "action_photo_renderer_blocked_manual_gate"
    assert manifest["renderer_unblocked"] is False
    assert manifest["render_packet_title"] == "Golden State Valkyries beat New York Liberty"
    assert manifest["active_asset_stop_go"] == "hold_required_manual_asset_review"
    assert manifest["external_return_rows"] == 8
    assert manifest["external_missing_rows"] == 2
    assert manifest["external_direct_image_hold_rows"] == 8
    assert manifest["external_identity_vocab_mismatch_rows"] == 8
    assert manifest["external_ready_rows"] == 0
    assert manifest["external_generated_download_approval_rows"] == 0
    assert manifest["import_rows_with_data"] == 0
    assert manifest["import_ready_rows"] == 0
    assert manifest["manual_bridge_rows"] == 2
    assert manifest["manual_bridge_source_rows"] == 103
    assert manifest["renderer_unblock_triage_rows"] == 2
    assert manifest["quarantine_ready_rows"] == 0
    assert manifest["quarantine_lead_only_rows"] == 10
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["human_intake_download_approved_yes_rows"] == 0
    assert manifest["next_queue_id"] == "APQ001"
    assert manifest["next_review_id"] == "APER001"
    assert manifest["next_candidate_page_url"] == "https://source.example/game-gallery"
    assert manifest["operator_decision"] == "hold_renderer_action_photo_manual_gate"
    assert "external_return_direct_image_url_holds" in manifest["blocking_reasons"]
    assert "shared_return_intake_has_no_human_pasted_rows" in manifest["blocking_reasons"]
    assert "render_handoff_asset_stop_go_hold_required_manual_asset_review" in manifest["blocking_reasons"]
    assert manifest["source_fetching"] is False
    assert manifest["auto_source_enablement"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["auto_approval"] is False
    assert manifest["auto_publish"] is False
    assert manifest["move_files"] is False
    assert manifest["paid_apis"] is False
    assert rows[0]["bridge_id"] == "APRB001"
    assert rows[0]["renderer_unblocked"] == "no"
    assert rows[0]["download_approved_yes_rows"] == "0"
    assert rows[0]["human_intake_download_approved_yes_rows"] == "0"
    assert rows[0]["review_only"] == "true"
    assert "does not fetch sources, download images" in markdown
    assert "Start with APQ001/APER001" in markdown


def test_to_renderer_bridge_prefers_human_ready_preflight_row(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    seed_bridge_inputs(tmp_path)
    module = load_module()
    action_root = tmp_path / "data/asset_registry/action_photo_candidates"
    write_json(
        action_root / "review_only_action_photo_research_return_import_review_v1.json",
        {
            "status": "action_photo_research_return_import_review_ready",
            "import_review_rows": 10,
            "rows_with_research_return_data": 1,
            "ready_for_later_human_download_decision_review_rows": 1,
            "human_intake_download_approved_yes_rows": 0,
            "generated_download_approved_yes_rows": 0,
            "source_fetching": False,
            "auto_source_enablement": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
        },
    )
    write_json(
        action_root / "review_only_action_photo_quarantine_preflight_v1.json",
        {
            "status": "action_photo_quarantine_preflight_ready",
            "preflight_rows": 10,
            "ready_for_human_download_decision_rows": 1,
            "lead_only_rows": 9,
            "download_approved_yes_rows": 0,
            "human_intake_download_approved_yes_rows": 0,
            "generated_download_approved_yes_rows": 0,
            "missing_required_field_counts": {"source_url": 9},
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
        },
    )
    write_csv(
        action_root / "review_only_action_photo_quarantine_preflight_v1.csv",
        [
            {
                "preflight_id": "APQP001",
                "candidate_queue_id": "APQ001",
                "candidate_photo_url": "https://fever.wnba.com/news/action-photo-page",
                "ready_for_human_download_decision": "yes",
            }
        ],
        ["preflight_id", "candidate_queue_id", "candidate_photo_url", "ready_for_human_download_decision"],
    )

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    manifest = json.loads((root / "review_only_action_photo_to_renderer_bridge_v1.json").read_text(encoding="utf-8"))

    assert manifest["import_rows_with_data"] == 1
    assert manifest["import_ready_rows"] == 1
    assert manifest["quarantine_ready_rows"] == 1
    assert manifest["quarantine_lead_only_rows"] == 9
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["human_intake_download_approved_yes_rows"] == 0
    assert manifest["next_queue_id"] == "APQ001"
    assert manifest["next_review_id"] == "APQP001"
    assert manifest["next_candidate_page_url"] == "https://fever.wnba.com/news/action-photo-page"
    assert "shared_return_intake_has_no_human_pasted_rows" not in manifest["blocking_reasons"]
    assert "external_return_direct_image_url_holds" not in manifest["blocking_reasons"]
    assert "no_human_download_approved_rows" in manifest["blocking_reasons"]
    assert "separate human quarantine-download decision" in manifest["bridge_rows_detail"][0]["next_manual_action"]


def test_to_renderer_bridge_recognizes_human_intake_download_decision_without_generated_approval(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    seed_bridge_inputs(tmp_path)
    module = load_module()
    action_root = tmp_path / "data/asset_registry/action_photo_candidates"
    write_json(
        action_root / "review_only_action_photo_research_return_import_review_v1.json",
        {
            "status": "action_photo_research_return_import_review_ready",
            "import_review_rows": 10,
            "rows_with_research_return_data": 1,
            "ready_for_later_human_download_decision_review_rows": 1,
            "human_intake_download_approved_yes_rows": 1,
            "generated_download_approved_yes_rows": 0,
            "source_fetching": False,
            "auto_source_enablement": False,
            "asset_downloads": False,
            "headshot_writes": False,
            "approved_marker_writes": False,
        },
    )
    write_json(
        action_root / "review_only_action_photo_quarantine_preflight_v1.json",
        {
            "status": "action_photo_quarantine_preflight_ready",
            "preflight_rows": 10,
            "ready_for_human_download_decision_rows": 1,
            "lead_only_rows": 9,
            "download_approved_yes_rows": 0,
            "human_intake_download_approved_yes_rows": 1,
            "generated_download_approved_yes_rows": 0,
            "missing_required_field_counts": {"source_url": 9},
            "review_only": True,
            "asset_downloads": False,
            "approval_state_change": False,
            "publish_ready": False,
        },
    )
    write_csv(
        action_root / "review_only_action_photo_quarantine_preflight_v1.csv",
        [
            {
                "preflight_id": "APQP001",
                "candidate_queue_id": "APQ001",
                "candidate_photo_url": "https://fever.wnba.com/news/action-photo-page",
                "ready_for_human_download_decision": "yes",
            }
        ],
        ["preflight_id", "candidate_queue_id", "candidate_photo_url", "ready_for_human_download_decision"],
    )

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_to_renderer_bridge_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_to_renderer_bridge_v1.json").read_text(encoding="utf-8"))

    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["human_intake_download_approved_yes_rows"] == 1
    assert rows[0]["download_approved_yes_rows"] == "0"
    assert rows[0]["human_intake_download_approved_yes_rows"] == "1"
    assert "no_human_download_approved_rows" not in manifest["blocking_reasons"]
    assert "render_handoff_asset_stop_go_hold_required_manual_asset_review" in manifest["blocking_reasons"]
    assert "yes download flag" in manifest["bridge_rows_detail"][0]["next_manual_action"]
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False


def test_to_renderer_bridge_validator_blocks_guardrail_drift() -> None:
    module = load_module()
    row = {
        field: "false"
        for field in module.BRIDGE_FIELDS
    }
    row.update(
        {
            "bridge_id": "APRB001",
            "renderer_unblocked": "yes",
            "operator_decision": "publish_ready",
            "review_only": "false",
            "external_ready_rows": "1",
            "external_generated_download_approval_rows": "1",
            "download_approved_yes_rows": "1",
            "source_fetching": "true",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "approval_state_change": "approved",
            "publish_ready": "true",
            "paid_apis": "true",
        }
    )

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_rows([row])}

    assert ("operator_decision", "unblocked_bridge_can_only_allow_manual_renderer_recheck") in issue_pairs
    assert ("review_only", "bridge_must_remain_review_only") in issue_pairs
    assert ("external_ready_rows", "bridge_must_not_surface_external_ready_rows") in issue_pairs
    assert ("external_generated_download_approval_rows", "bridge_must_not_generate_download_approvals") in issue_pairs
    assert ("download_approved_yes_rows", "bridge_must_not_approve_downloads") in issue_pairs
    assert ("source_fetching", "guardrail_field_invalid") in issue_pairs
    assert ("asset_downloads", "guardrail_field_invalid") in issue_pairs
    assert ("headshot_writes", "guardrail_field_invalid") in issue_pairs
    assert ("approved_marker_writes", "guardrail_field_invalid") in issue_pairs
    assert ("approval_state_change", "guardrail_field_invalid") in issue_pairs
    assert ("publish_ready", "guardrail_field_invalid") in issue_pairs
    assert ("paid_apis", "guardrail_field_invalid") in issue_pairs
