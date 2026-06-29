from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_action_photo_research_return_import_stub_v1.py"
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


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_action_photo_research_return_import_stub_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_intake(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INTAKE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def blank_return_row(queue_id: str) -> dict[str, str]:
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
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/apq001/operator_fill_required.jpg",
        "review_only": "true",
        "publish_ready": "false",
    }


def test_import_stub_reads_blank_return_intake_without_downloads(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()
    intake = tmp_path / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    write_intake(intake, [blank_return_row("APQ001"), blank_return_row("APQ002")])

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_research_return_import_review_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_research_return_import_review_v1.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_research_return_import_review_v1.md").read_text(encoding="utf-8")

    assert manifest["status"] == "action_photo_research_return_import_review_ready"
    assert manifest["import_review_rows"] == 2
    assert manifest["rows_with_research_return_data"] == 0
    assert manifest["ready_for_later_human_download_decision_review_rows"] == 0
    assert manifest["human_intake_download_approved_yes_rows"] == 0
    assert manifest["generated_download_approved_yes_rows"] == 0
    assert manifest["blank_source_url_rows"] == 2
    assert manifest["blank_rights_class_rows"] == 2
    assert manifest["source_fetching"] is False
    assert manifest["auto_source_enablement"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert len(rows) == 2
    assert list(rows[0].keys()) == module.IMPORT_REVIEW_FIELDS
    assert rows[0]["research_return_data_present"] == "no"
    assert rows[0]["candidate_ready_for_later_human_download_decision_review"] == "no"
    assert rows[0]["candidate_review_bucket"] == "research_return_not_pasted_yet"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["asset_downloads"] == "false"
    assert "does not fetch sources, download images" in markdown


def test_import_stub_marks_complete_human_return_ready_without_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()
    intake = tmp_path / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    complete = blank_return_row("APQ001")
    complete.update(
        {
            "candidate_photo_url": "https://example.com/action-photo-page",
            "evidence_url": "https://example.com/game-recap",
            "evidence_summary": "driving layup in game action with event context",
            "identity_anchor_url": "https://example.com/player-profile",
            "source_url": "https://example.com/action-photo-page",
            "entity_id": "wnba:player:apq001",
            "rights_class": "official_review_needed",
            "identity_confidence": "strong_context",
            "intended_review_only_use": "review_only_action_photo_candidate_quarantine_decision_prep",
            "notes": "manual research return pasted",
        }
    )
    write_intake(intake, [complete])

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_research_return_import_review_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_research_return_import_review_v1.json").read_text(encoding="utf-8"))

    assert manifest["rows_with_research_return_data"] == 1
    assert manifest["ready_for_later_human_download_decision_review_rows"] == 1
    assert manifest["human_intake_download_approved_yes_rows"] == 0
    assert manifest["generated_download_approved_yes_rows"] == 0
    assert rows[0]["research_return_data_present"] == "yes"
    assert rows[0]["candidate_ready_for_later_human_download_decision_review"] == "yes"
    assert rows[0]["candidate_review_bucket"] == "ready_for_later_human_download_decision_review"
    assert rows[0]["missing_required_fields"] == ""
    assert rows[0]["identity_confidence_status"] == "identity_ready_for_human_review"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["approved_marker_writes"] == "false"


def test_import_stub_surfaces_human_download_yes_as_gate_review_not_generated_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()
    intake = tmp_path / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    incomplete = blank_return_row("APQ001")
    incomplete.update({"download_approved": "yes", "source_url": "https://example.com/source"})
    write_intake(intake, [incomplete])

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_research_return_import_review_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_research_return_import_review_v1.json").read_text(encoding="utf-8"))

    assert manifest["human_intake_download_approved_yes_rows"] == 1
    assert manifest["generated_download_approved_yes_rows"] == 0
    assert rows[0]["human_intake_download_approved"] == "yes"
    assert rows[0]["candidate_review_bucket"] == "human_download_approved_incomplete_hold"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["asset_downloads"] == "false"
    assert "hold and fill missing fields" in rows[0]["manual_next_action"]


def test_import_review_validator_blocks_unsafe_generated_rows() -> None:
    module = load_module()
    rows = module.action_photo_research_return_import_review_rows([blank_return_row("APQ001"), blank_return_row("APQ002")])
    rows[0].update(
        {
            "candidate_ready_for_later_human_download_decision_review": "yes",
            "download_approved": "yes",
            "quarantine_root": "assets/not_quarantine",
            "review_only": "false",
            "publish_ready": "true",
            "approval_state_change": "approved",
            "asset_downloads": "true",
            "headshot_writes": "true",
            "approved_marker_writes": "true",
            "publish_action": "publish",
        }
    )
    rows[1]["import_review_id"] = rows[0]["import_review_id"]
    rows[1]["candidate_queue_id"] = rows[0]["candidate_queue_id"]

    issue_pairs = {(issue["field"], issue["issue"]) for issue in module.validate_import_review_rows(rows)}

    assert ("import_review_id", "duplicate_import_review_id") in issue_pairs
    assert ("candidate_queue_id", "duplicate_candidate_queue_id") in issue_pairs
    assert ("missing_required_fields", "ready_row_has_missing_required_fields") in issue_pairs
    assert ("download_approved", "generated_import_review_must_not_approve_downloads") in issue_pairs
    assert ("quarantine_root", "quarantine_root_must_be_review_only_candidates") in issue_pairs
    assert ("review_only", "import_review_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "import_review_rows_must_not_be_publish_ready") in issue_pairs
    assert ("approval_state_change", "import_review_rows_must_not_change_approval_state") in issue_pairs
    assert ("asset_downloads", "import_review_rows_must_not_write_assets_or_markers") in issue_pairs
    assert ("headshot_writes", "import_review_rows_must_not_write_assets_or_markers") in issue_pairs
    assert ("approved_marker_writes", "import_review_rows_must_not_write_assets_or_markers") in issue_pairs
    assert ("publish_action", "import_review_rows_must_not_publish") in issue_pairs
