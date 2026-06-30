from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_action_photo_quarantine_preflight_v1.py"
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
    spec = importlib.util.spec_from_file_location("report_hsd_action_photo_quarantine_preflight_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
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
        "quarantine_target_hint": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/operator_fill_required.jpg",
        "review_only": "true",
        "publish_ready": "false",
    }


def test_quarantine_preflight_reads_human_intake_without_rewriting_it(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module = load_module()
    intake = tmp_path / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    complete = blank_return_row("APQ001")
    complete.update(
        {
            "candidate_photo_url": "https://fever.wnba.com/news/action-photo-page",
            "evidence_url": "https://fever.wnba.com/news/action-photo-page",
            "evidence_summary": "Official team recap has game action context with a visible action-photo lead.",
            "identity_anchor_url": "https://www.wnba.com/player/1642286/caitlin-clark",
            "source_url": "https://fever.wnba.com/news/action-photo-page",
            "entity_id": "wnba:caitlin-clark",
            "rights_class": "official_review_needed",
            "identity_confidence": "confirmed_official",
            "intended_review_only_use": "review_only_action_photo_candidate_quarantine_decision_prep",
            "notes": "Official Fever page verified by Mike; rights still manual-review only.",
            "manual_reviewer": "Mike",
            "manual_review_status": "ready_for_human_download_decision",
            "manual_next_action": "Mike recorded the download flag as yes for quarantine-only review; do not download from this preflight.",
            "download_approved": "yes",
        }
    )
    write_intake(intake, [complete, blank_return_row("APQ002")])
    intake_before = intake.read_text(encoding="utf-8")

    assert module.main() == 0

    root = tmp_path / "data/asset_registry/action_photo_candidates"
    rows = read_csv(root / "review_only_action_photo_quarantine_preflight_v1.csv")
    manifest = json.loads((root / "review_only_action_photo_quarantine_preflight_v1.json").read_text(encoding="utf-8"))
    markdown = (root / "review_only_action_photo_quarantine_preflight_v1.md").read_text(encoding="utf-8")

    assert intake.read_text(encoding="utf-8") == intake_before
    assert manifest["status"] == "action_photo_quarantine_preflight_ready"
    assert manifest["return_intake_rows"] == 2
    assert manifest["preflight_rows"] == 2
    assert manifest["ready_for_human_download_decision_rows"] == 1
    assert manifest["lead_only_rows"] == 1
    assert manifest["download_approved_yes_rows"] == 0
    assert manifest["human_intake_download_approved_yes_rows"] == 1
    assert manifest["generated_download_approved_yes_rows"] == 0
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
    assert rows[0]["candidate_queue_id"] == "APQ001"
    assert rows[0]["ready_for_human_download_decision"] == "yes"
    assert rows[0]["action_photo_status"] == "action_photo_candidate"
    assert rows[0]["identity_confidence_status"] == "identity_ready_for_human_review"
    assert rows[0]["download_approved"] == "no"
    assert "yes download flag" in rows[0]["manual_next_action"]
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[1]["lead_status"] == "lead_only_research_return_missing"
    assert "Human intake rows with a recorded yes download flag: `1`" in markdown
    assert "Generated preflight rows with a recorded yes download flag: `0`" in markdown
    assert "does not download files, approve assets" in markdown


def test_quarantine_preflight_validator_blocks_generated_guardrail_drift() -> None:
    module = load_module()
    row = {
        field: "ok"
        for field in module.ACTION_PHOTO_QUARANTINE_PREFLIGHT_FIELDS
    }
    row.update(
        {
            "preflight_id": "APQP001",
            "candidate_queue_id": "APQ001",
            "action_photo_check": "action_photo_candidate",
            "action_photo_status": "action_photo_candidate",
            "ready_for_human_download_decision": "yes",
            "missing_required_fields": "source_url",
            "duplicate_candidate_key": "unique_or_unfilled",
            "identity_confidence_status": "identity_missing",
            "download_approved": "yes",
            "quarantine_target_hint": "assets/not-quarantine/file.jpg",
            "review_only": "false",
            "publish_ready": "true",
        }
    )

    issue_pairs = {
        (issue["field"], issue["issue"])
        for issue in module.validate_action_photo_quarantine_preflight_rows([row], [blank_return_row("APQ001")])
    }

    assert ("download_approved", "preflight_rows_must_not_approve_downloads") in issue_pairs
    assert ("quarantine_target_hint", "quarantine_hint_must_stay_in_review_only_root") in issue_pairs
    assert ("review_only", "preflight_rows_must_remain_review_only") in issue_pairs
    assert ("publish_ready", "preflight_rows_must_not_be_publish_ready") in issue_pairs
    assert ("ready_for_human_download_decision", "ready_row_has_missing_required_fields") in issue_pairs
    assert ("ready_for_human_download_decision", "ready_row_identity_not_strong_enough") in issue_pairs
