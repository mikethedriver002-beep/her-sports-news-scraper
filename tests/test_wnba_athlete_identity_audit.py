from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_wnba_athlete_identity_audit_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_wnba_athlete_identity_audit_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_png_like(path: Path, payload: bytes = b"headshot-bytes") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def make_marker(path: Path, **overrides: str) -> Path:
    marker = Path(path.as_posix() + ".approved")
    payload = {
        "approved_at_utc": "2026-06-25T00:00:00+00:00",
        "athlete_id": "new_york_liberty_test_player",
        "display_name": "Test Player",
        "team_id": "new_york_liberty",
        "provider_player_id": "123",
        "source_file": "outputs/latest/review_files/athlete_image_approval_pack/downloads/new_york_liberty/test.png",
        "decision_source": "default",
        "policy": "human_reviewed_contact_sheet_then_approved",
    }
    payload.update(overrides)
    marker.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return marker


def test_identity_audit_flags_default_pending_and_blank_decision(tmp_path: Path) -> None:
    module = load_module()
    asset = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "new_york_liberty_test_player" / "headshot.png"
    make_png_like(asset)
    marker = make_marker(asset)

    issues = module.audit_approved_assets(
        athlete_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "",
        }],
        image_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "",
            "image_type": "headshot",
            "file_path": asset.as_posix(),
            "approved": "true",
        }],
        approved_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "123",
            "approved_file": asset.as_posix(),
            "approved_marker": marker.as_posix(),
            "decision_source": "default",
        }],
        review_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "status": "needs_human_approval",
            "confidence": "0.72",
            "provider_player_id": "123",
        }],
        decision_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "decision": "",
            "approval_target_path": asset.as_posix(),
            "provider_player_id": "123",
        }],
    )

    codes = {row["issue_code"] for row in issues}

    assert "default_approval_requires_identity_recheck" in codes
    assert "approved_asset_still_has_pending_match_review" in codes
    assert "blank_per_row_approval_decision" in codes
    assert "missing_provider_player_id_in_image_registry" in codes
    assert all(row["review_only_policy"] == module.REVIEW_ONLY_POLICY for row in issues)


def test_identity_audit_flags_marker_identity_mismatch(tmp_path: Path) -> None:
    module = load_module()
    asset = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "new_york_liberty_test_player" / "headshot.png"
    make_png_like(asset)
    marker = make_marker(asset, athlete_id="new_york_liberty_other_player")

    issues = module.audit_approved_assets(
        athlete_rows=[],
        image_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "image_type": "headshot",
            "file_path": asset.as_posix(),
            "approved": "true",
        }],
        approved_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "123",
            "approved_file": asset.as_posix(),
            "approved_marker": marker.as_posix(),
            "decision_source": "approval_csv",
        }],
        review_rows=[],
        decision_rows=[],
    )

    mismatch = [row for row in issues if row["issue_code"] == "approved_marker_identity_mismatch"]

    assert mismatch
    assert mismatch[0]["severity"] == "critical"
    assert "athlete_id" in mismatch[0]["evidence"]


def test_identity_audit_flags_duplicate_provider_and_hash(tmp_path: Path) -> None:
    module = load_module()
    first = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "team_one_player_one" / "headshot.png"
    second = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "team_two_player_two" / "headshot.png"
    make_png_like(first, b"same-image")
    make_png_like(second, b"same-image")
    first_marker = make_marker(first, athlete_id="team_one_player_one", display_name="Player One", team_id="team_one")
    second_marker = make_marker(second, athlete_id="team_two_player_two", display_name="Player Two", team_id="team_two")

    approved_rows = [
        {
            "athlete_id": "team_one_player_one",
            "display_name": "Player One",
            "team_id": "team_one",
            "provider_player_id": "999",
            "approved_file": first.as_posix(),
            "approved_marker": first_marker.as_posix(),
            "decision_source": "approval_csv",
        },
        {
            "athlete_id": "team_two_player_two",
            "display_name": "Player Two",
            "team_id": "team_two",
            "provider_player_id": "999",
            "approved_file": second.as_posix(),
            "approved_marker": second_marker.as_posix(),
            "decision_source": "approval_csv",
        },
    ]

    issues = module.audit_approved_assets(
        athlete_rows=[],
        image_rows=[
            {"athlete_id": "team_one_player_one", "image_type": "headshot", "file_path": first.as_posix(), "approved": "true"},
            {"athlete_id": "team_two_player_two", "image_type": "headshot", "file_path": second.as_posix(), "approved": "true"},
        ],
        approved_rows=approved_rows,
        review_rows=[],
        decision_rows=[],
    )
    codes = {row["issue_code"] for row in issues}

    assert "provider_player_id_reused_across_athletes" in codes
    assert "exact_duplicate_approved_headshot_hash" in codes


def test_identity_audit_main_writes_to_run_folder(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    module.main()

    assert (run_dir / "data" / "asset_registry" / "wnba" / "athlete_identity_audit.csv").exists()
    assert (run_dir / "data" / "asset_registry" / "wnba" / "athlete_identity_audit.json").exists()
    assert (run_dir / "data" / "asset_registry" / "wnba" / "athlete_identity_audit.md").exists()
    assert not (tmp_path / "data" / "asset_registry" / "wnba" / "athlete_identity_audit.csv").exists()
