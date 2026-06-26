from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "serve_hsd_identity_resolution_ui_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("identity_resolution_local_server", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_row() -> dict[str, str]:
    return {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "provider_player_id": "1627668",
        "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "approved_marker_path": "",
        "highest_severity": "high",
        "issue_count": "1",
        "issue_codes": "order_matched_headshot_requires_source_backed_identity_review",
        "audit_evidence": "official roster checked",
        "recommended_operator_action": "manual_identity_resolution_required",
        "allowed_decisions": "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only",
        "operator_decision": "identity_verified_approved_for_review_renders",
        "identity_verified": "yes",
        "provider_player_id_verified": "yes",
        "approved_source_url": "https://liberty.wnba.com/roster/",
        "secondary_source_url": "",
        "backfill_provider_player_id": "",
        "operator_notes": "Checked the official roster by eye.",
        "operator_name": "Mike",
        "reviewed_at_local": "2026-06-26 10:00:00",
        "issue_resolution_status": "",
        "copy_target": "operator/inbox/wnba_athlete_identity_resolution.csv",
        "approval_scope": "review_only_identity_resolution_for_local_draft_renders",
        "publish_ready": "true",
        "auto_approval": "true",
        "auto_publish": "true",
        "move_files": "true",
        "paid_apis": "true",
        "review_only_policy": "",
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_append_identity_row_writes_header_and_forces_manual_guardrails(tmp_path: Path) -> None:
    module = load_module()

    result = module.append_identity_row(tmp_path, valid_row())

    assert result["ok"] is True
    assert result["status"] == "identity_row_saved"
    inbox = tmp_path / module.INBOX_PATH
    assert inbox.exists()
    header = inbox.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == module.IDENTITY_RESOLUTION_FIELDS
    rows = read_rows(inbox)
    assert len(rows) == 1
    row = rows[0]
    assert row["issue_resolution_status"] == "identity_verified"
    assert row["copy_target"] == "operator/inbox/wnba_athlete_identity_resolution.csv"
    assert row["approval_scope"] == "review_only_identity_resolution_for_local_draft_renders"
    assert row["review_only_policy"] == "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane"
    for field in module.FALSE_FIELDS:
        assert row[field] == "false"


def test_append_identity_row_rejects_verified_decision_without_source(tmp_path: Path) -> None:
    module = load_module()
    row = valid_row()
    row["approved_source_url"] = ""

    result = module.append_identity_row(tmp_path, row)

    assert result["ok"] is False
    assert result["status"] == "validation_failed"
    assert "Verify requires approved_source_url." in result["warnings"]
    assert not (tmp_path / module.INBOX_PATH).exists()


def test_backfill_only_keeps_identity_held_until_manual_review(tmp_path: Path) -> None:
    module = load_module()
    row = valid_row()
    row["operator_decision"] = "backfill_provider_id_only"
    row["identity_verified"] = "no"
    row["provider_player_id_verified"] = "no"
    row["backfill_provider_player_id"] = "1627668"

    result = module.append_identity_row(tmp_path, row)

    assert result["ok"] is True
    rows = read_rows(tmp_path / module.INBOX_PATH)
    assert rows[0]["operator_decision"] == "backfill_provider_id_only"
    assert rows[0]["issue_resolution_status"] == "provider_id_backfill_ready_identity_still_held"
    assert rows[0]["publish_ready"] == "false"


def test_latest_files_dir_prefers_run_scoped_latest_command_center(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    files_dir = tmp_path / "outputs" / "local" / "latest" / "files"
    files_dir.mkdir(parents=True)
    (files_dir / "operator_command_center.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert module.latest_files_dir(tmp_path) == files_dir.resolve()
