from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "apply_hsd_wnba_athlete_photo_review_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("apply_hsd_wnba_athlete_photo_review_intake_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_apply_intake_updates_only_explicit_review_only_approval_metadata(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    module.INTAKE = Path("data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv")

    marker = tmp_path / "assets/leagues/wnba/athletes/new_york_liberty_test_player/headshot.png.approved"
    marker.parent.mkdir(parents=True)
    marker.write_text(
        json.dumps(
            {
                "approved_at_utc": "2026-06-16T00:00:00+00:00",
                "athlete_id": "new_york_liberty_test_player",
                "display_name": "Test Player",
                "team_id": "new_york_liberty",
                "provider_player_id": "123",
                "source_file": "outputs/latest/review_files/athlete_image_approval_pack/downloads/test.png",
                "decision_source": "default",
            }
        ),
        encoding="utf-8",
    )

    intake_rows = [
        {
            "athlete_id": "new_york_liberty_test_player",
            "athlete_name": "Test Player",
            "team_id": "new_york_liberty",
            "local_headshot_path": "assets/leagues/wnba/athletes/new_york_liberty_test_player/headshot.png",
            "approved_marker_path": marker.as_posix(),
            "provider_player_id": "123",
            "operator_decision": "approve_for_review_only_renderer_use",
            "identity_verified": "yes",
            "source_reviewed": "yes",
            "local_file_reviewed": "yes",
            "source_url_to_record": "https://www.wnba.com/player/123/test-player",
            "provider_player_id_verified": "yes",
            "reviewed_by": "Mike explicit sweep via Codex",
            "reviewed_at_local": "2026-06-26 18:31 local",
            "approval_scope": "review_only_renderer_athlete_photo_trust_manual_intake",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "asset_downloads": "false",
        },
        {
            "athlete_id": "golden_state_valkyries_needs_revise",
            "athlete_name": "Needs Revise",
            "team_id": "golden_state_valkyries",
            "operator_decision": "revise_asset",
            "registry_action": "hold_no_registry_change_find_replacement_image",
            "source_url_to_record": "https://example.com/replacement-candidate",
        },
    ]
    athlete_rows = [
        {
            "athlete_id": "new_york_liberty_test_player",
            "provider_player_id": "",
            "source_url": "https://liberty.wnba.com/roster",
            "last_verified_utc": "old",
            "notes": "official_roster_text_review_required",
        },
        {
            "athlete_id": "golden_state_valkyries_needs_revise",
            "provider_player_id": "",
            "source_url": "https://valkyries.wnba.com/roster",
            "last_verified_utc": "old",
            "notes": "official_roster_text_review_required",
        },
    ]
    image_rows = [
        {
            "athlete_id": "new_york_liberty_test_player",
            "image_type": "headshot",
            "provider_player_id": "",
            "source_note": "approved_marker_required",
            "last_verified_utc": "old",
        },
        {
            "athlete_id": "golden_state_valkyries_needs_revise",
            "image_type": "headshot",
            "provider_player_id": "",
            "source_note": "missing_review_required",
            "last_verified_utc": "old",
        },
    ]
    approved_rows = [
        {
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "123",
            "approved_file": "assets/leagues/wnba/athletes/new_york_liberty_test_player/headshot.png",
            "approved_marker": marker.as_posix(),
            "source_file": "outputs/latest/review_files/athlete_image_approval_pack/downloads/test.png",
            "approved_at_utc": "2026-06-16T00:00:00+00:00",
            "decision_source": "default",
        }
    ]
    match_review_rows = [
        {
            "athlete_id": "new_york_liberty_test_player",
            "provider_player_id": "123",
            "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/123.png",
            "match_method": "roster_order_name_to_headshot_order",
            "confidence": "0.72",
            "status": "needs_human_approval",
            "notes": "review_before_approval",
        },
        {
            "athlete_id": "golden_state_valkyries_needs_revise",
            "provider_player_id": "",
            "image_url": "",
            "match_method": "",
            "confidence": "",
            "status": "needs_human_approval",
            "notes": "review_before_approval",
        },
    ]

    report = module.apply_intake(
        intake_rows,
        athlete_rows,
        image_rows,
        approved_rows,
        match_review_rows,
        applied_at_utc="2026-06-26T22:31:00+00:00",
    )

    assert report["applied_review_only_metadata"] == 1
    assert report["revise_asset_rows"] == 1
    assert report["failed_rows"] == 0
    assert athlete_rows[0]["provider_player_id"] == "123"
    assert athlete_rows[0]["source_url"] == "https://www.wnba.com/player/123/test-player"
    assert athlete_rows[1]["provider_player_id"] == ""
    assert image_rows[0]["source_note"] == "human_sweep_review_only_source_verified"
    assert image_rows[1]["source_note"] == "missing_review_required"
    assert match_review_rows[0]["status"] == "human_verified_review_only"
    assert match_review_rows[0]["match_method"] == "human_verified_contact_sheet_review"
    assert match_review_rows[0]["confidence"] == "1.00"
    assert match_review_rows[1]["status"] == "needs_human_approval"
    assert approved_rows[0]["decision_source"] == module.DECISION_SOURCE
    assert approved_rows[0]["source_file"] == "https://www.wnba.com/player/123/test-player"
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["decision_source"] == module.DECISION_SOURCE
    assert payload["human_intake_file"] == "data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv"
    assert payload["review_only_policy"] == module.REVIEW_ONLY_POLICY


def test_apply_intake_rejects_guardrail_violations_before_metadata_changes(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)

    marker = tmp_path / "assets/leagues/wnba/athletes/test/headshot.png.approved"
    marker.parent.mkdir(parents=True)
    marker.write_text('{"decision_source":"default"}', encoding="utf-8")
    athlete_rows = [{"athlete_id": "test", "provider_player_id": "", "source_url": ""}]
    image_rows = [{"athlete_id": "test", "image_type": "headshot", "provider_player_id": "", "source_note": ""}]
    approved_rows = [
        {
            "athlete_id": "test",
            "approved_file": "assets/leagues/wnba/athletes/test/headshot.png",
            "approved_marker": marker.as_posix(),
            "decision_source": "default",
        }
    ]

    report = module.apply_intake(
        [
            {
                "athlete_id": "test",
                "athlete_name": "Test",
                "team_id": "new_york_liberty",
                "local_headshot_path": "assets/leagues/wnba/athletes/test/headshot.png",
                "approved_marker_path": marker.as_posix(),
                "provider_player_id": "123",
                "operator_decision": "approve_for_review_only_renderer_use",
                "identity_verified": "yes",
                "source_reviewed": "yes",
                "local_file_reviewed": "yes",
                "source_url_to_record": "https://www.wnba.com/player/123/test",
                "provider_player_id_verified": "yes",
                "publish_ready": "true",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        athlete_rows,
        image_rows,
        approved_rows,
        [],
        applied_at_utc="2026-06-26T22:31:00+00:00",
    )

    assert report["applied_review_only_metadata"] == 0
    assert report["failed_rows"] == 1
    assert "publish_ready_must_remain_false" in report["failed"][0]["status"]
    assert athlete_rows[0]["provider_player_id"] == ""
    assert approved_rows[0]["decision_source"] == "default"
