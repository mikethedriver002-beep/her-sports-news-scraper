from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_hsd_identity_decision_live_writeback_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("identity_decision_verifier", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_command_center(files_dir: Path, rows: list[dict]) -> None:
    files_dir.mkdir(parents=True, exist_ok=True)
    (files_dir / "operator_command_center.html").write_text("<html></html>", encoding="utf-8")
    (files_dir / "operator_command_center.json").write_text(
        json.dumps({"athlete_photo_onboarding_panel": {"review_rows": rows}}),
        encoding="utf-8",
    )


def breanna_row() -> dict:
    return {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "athlete_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "featured": True,
        "source_headshot_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "identity_issue_codes": "approved_asset_still_has_pending_match_review",
        "identity_evidence": "match review requires source-backed decision",
        "identity_provider_candidate": "1630993",
        "identity_resolution_candidate": {
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "1630993",
            "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
            "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
            "highest_severity": "high",
            "issue_count": "1",
            "issue_codes": "approved_asset_still_has_pending_match_review",
            "audit_evidence": "match review requires source-backed decision",
            "recommended_operator_action": "verify_identity_and_backfill_provider_id_if_source_supported",
        },
    }


def test_verifier_posts_to_live_endpoint_and_restores_inbox(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    files_dir = tmp_path / "outputs" / "local" / "latest" / "files"
    write_command_center(files_dir, [breanna_row()])
    inbox = tmp_path / "operator" / "inbox" / "wnba_athlete_identity_resolution.csv"
    inbox.parent.mkdir(parents=True)
    original = ",".join(module.IDENTITY_RESOLUTION_FIELDS) + "\n"
    inbox.write_text(original, encoding="utf-8")
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path / "run" / "files"))

    result = module.run_verification(tmp_path, files_dir)
    json_path, md_path = module.write_report(result)

    assert result["status"] == "passed"
    assert result["diff_count"] == 0
    assert result["athlete_id"] == "new_york_liberty_breanna_stewart"
    assert result["inbox_restored"] is True
    assert inbox.read_text(encoding="utf-8") == original
    assert json_path.exists()
    assert md_path.exists()
    assert json_path.parent == tmp_path / "run" / "files"
    report_text = md_path.read_text(encoding="utf-8")
    assert "Diff count: `0`" in report_text
    assert "No auto-approval" in report_text


def test_verifier_requires_real_wnba_athlete_row(tmp_path: Path) -> None:
    module = load_module()
    files_dir = tmp_path / "outputs" / "local" / "latest" / "files"
    write_command_center(files_dir, [{"athlete_id": "", "team_id": ""}])

    try:
        module.run_verification(tmp_path, files_dir)
    except ValueError as exc:
        assert "No real WNBA athlete identity-resolution row" in str(exc)
    else:
        raise AssertionError("verifier should reject missing WNBA athlete rows")


def test_verifier_saved_row_matches_normalized_command_center_draft(tmp_path: Path) -> None:
    module = load_module()
    files_dir = tmp_path / "outputs" / "local" / "latest" / "files"
    row = breanna_row()
    write_command_center(files_dir, [row])
    expected = module.build_command_center_identity_row(row)
    result = module.run_verification(tmp_path, files_dir)

    assert result["status"] == "passed"
    assert result["diff_count"] == 0
    assert expected["issue_resolution_status"] == "identity_verified"
    assert expected["publish_ready"] == "false"
    assert expected["auto_publish"] == "false"
    assert expected["move_files"] == "false"
    assert expected["paid_apis"] == "false"
