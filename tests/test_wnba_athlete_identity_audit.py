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


def test_identity_audit_accepts_human_contact_sheet_review_as_explicit_decision(tmp_path: Path) -> None:
    module = load_module()
    asset = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "new_york_liberty_test_player" / "headshot.png"
    make_png_like(asset)
    marker = make_marker(
        asset,
        source_file="https://www.wnba.com/player/123/test-player",
        decision_source="human_reviewed_wnba_athlete_photo_contact_sheet",
    )

    issues = module.audit_approved_assets(
        athlete_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "123",
            "source_url": "https://www.wnba.com/player/123/test-player",
        }],
        image_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "123",
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
            "source_file": "https://www.wnba.com/player/123/test-player",
            "decision_source": "human_reviewed_wnba_athlete_photo_contact_sheet",
        }],
        review_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "status": "human_verified_review_only",
            "confidence": "1.00",
            "provider_player_id": "123",
            "match_method": "human_verified_contact_sheet_review",
            "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/123.png",
        }],
        decision_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "decision": "",
            "approval_target_path": asset.as_posix(),
            "provider_player_id": "123",
        }],
    )

    codes = {row["issue_code"] for row in issues}

    assert "default_approval_requires_identity_recheck" not in codes
    assert "approved_asset_still_has_pending_match_review" not in codes
    assert "blank_per_row_approval_decision" not in codes
    assert "order_matched_headshot_requires_source_backed_identity_review" not in codes


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


def test_identity_audit_flags_order_match_and_source_provenance_risks(tmp_path: Path) -> None:
    module = load_module()
    asset = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "new_york_liberty_breanna_stewart" / "headshot.png"
    make_png_like(asset)
    marker = make_marker(
        asset,
        athlete_id="new_york_liberty_breanna_stewart",
        display_name="Breanna Stewart",
        team_id="new_york_liberty",
        provider_player_id="1630993",
        source_file="downloads/new_york_liberty_breanna_stewart__1630993.png",
        decision_source="approval_csv",
    )

    issues = module.audit_approved_assets(
        athlete_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "",
            "source_url": "https://example.com/roster",
        }],
        image_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "",
            "image_type": "headshot",
            "file_path": asset.as_posix(),
            "approved": "true",
        }],
        approved_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "1630993",
            "approved_file": asset.as_posix(),
            "approved_marker": marker.as_posix(),
            "source_file": "downloads/new_york_liberty_breanna_stewart__1630993.png",
            "decision_source": "approval_csv",
        }],
        review_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "status": "needs_human_approval",
            "confidence": "0.72",
            "provider_player_id": "1630993",
            "match_method": "roster_order_name_to_headshot_order",
            "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/1630993.png",
        }],
        decision_rows=[],
    )

    by_code = {row["issue_code"]: row for row in issues}

    assert "approved_asset_lacks_official_roster_source" in by_code
    assert "order_matched_headshot_requires_source_backed_identity_review" in by_code
    assert "missing_provider_player_id_in_image_registry" in by_code
    assert by_code["order_matched_headshot_requires_source_backed_identity_review"]["source_url"] == "https://example.com/roster"
    assert "roster_order_name_to_headshot_order" in by_code["order_matched_headshot_requires_source_backed_identity_review"]["source_provenance"]


def test_identity_audit_flags_provider_id_source_artifact_mismatch(tmp_path: Path) -> None:
    module = load_module()
    asset = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "new_york_liberty_test_player" / "headshot.png"
    make_png_like(asset)
    marker = make_marker(asset, provider_player_id="1234", source_file="downloads/new_york_liberty_test_player__9999.png")

    issues = module.audit_approved_assets(
        athlete_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "1234",
            "source_url": "https://liberty.wnba.com/roster",
        }],
        image_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "1234",
            "image_type": "headshot",
            "file_path": asset.as_posix(),
            "approved": "true",
        }],
        approved_rows=[{
            "athlete_id": "new_york_liberty_test_player",
            "display_name": "Test Player",
            "team_id": "new_york_liberty",
            "provider_player_id": "1234",
            "approved_file": asset.as_posix(),
            "approved_marker": marker.as_posix(),
            "source_file": "downloads/new_york_liberty_test_player__9999.png",
            "decision_source": "approval_csv",
        }],
        review_rows=[],
        decision_rows=[],
    )

    mismatch = [row for row in issues if row["issue_code"] == "provider_player_id_disagrees_with_source_artifact"]

    assert mismatch
    assert mismatch[0]["severity"] == "critical"
    assert "9999" in mismatch[0]["evidence"]


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


def test_identity_audit_coverage_summary_counts_source_and_provider_gaps() -> None:
    module = load_module()

    summary = module.coverage_summary(
        athlete_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "provider_player_id": "",
            "source_url": "https://liberty.wnba.com/roster",
        }],
        image_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "image_type": "headshot",
            "provider_player_id": "",
        }],
        approved_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "provider_player_id": "1630993",
            "decision_source": "default",
        }],
        review_rows=[{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "provider_player_id": "1630993",
            "match_method": "roster_order_name_to_headshot_order",
            "status": "needs_human_approval",
        }],
    )

    assert summary["approved_asset_rows"] == 1
    assert summary["approved_with_official_roster_source_url"] == 1
    assert summary["approved_missing_athlete_provider_player_id"] == 1
    assert summary["approved_missing_image_provider_player_id"] == 1
    assert summary["approved_with_order_match_review"] == 1
    assert summary["approved_with_pending_match_review"] == 1
    assert summary["approved_with_default_decision_source"] == 1


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
