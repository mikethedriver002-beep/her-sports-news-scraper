from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_wnba_athlete_identity_closure_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_wnba_athlete_identity_closure_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_closure_rows_are_blank_manual_review_only() -> None:
    module = load_module()

    rows = module.build_closure_rows([{
        "severity": "high",
        "issue_code": "default_approval_requires_identity_recheck",
        "athlete_id": "atlanta_dream_test_player",
        "display_name": "Test Player",
        "team_id": "atlanta_dream",
        "provider_player_id": "123",
        "asset_path": "assets/leagues/wnba/athletes/atlanta_dream_test_player/headshot.png",
        "approved_marker_path": "assets/leagues/wnba/athletes/atlanta_dream_test_player/headshot.png.approved",
        "evidence": "decision_source=default",
        "recommendation": "Review by eye.",
    }])

    assert rows[0]["operator_closure_decision"] == ""
    assert rows[0]["manual_identity_verified"] == ""
    assert rows[0]["allowed_closure_decisions"] == "close_after_manual_identity_verification|keep_open|needs_registry_backfill|hold_asset|mark_false_positive"
    assert rows[0]["review_only_policy"] == module.REVIEW_ONLY_POLICY
    assert rows[0]["auto_approval"] == "false"
    assert rows[0]["publish_ready"] == "false"


def test_backfill_rows_propose_unambiguous_provider_id_without_applying() -> None:
    module = load_module()

    rows = module.build_backfill_rows(
        athlete_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "",
        }],
        image_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "",
            "image_type": "headshot",
        }],
        approved_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "123",
            "source_file": "outputs/latest/review_files/athlete_image_approval_pack/downloads/atlanta_dream/player__123.png",
        }],
        review_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "123",
            "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/123.png",
        }],
    )

    by_target = {row["target_csv"]: row for row in rows}

    assert by_target[module.ATHLETES.as_posix()]["proposed_value"] == "123"
    assert by_target[module.ATHLETE_IMAGES.as_posix()]["proposed_value"] == "123"
    assert all(row["backfill_status"] == "manual_review_required" for row in rows)
    assert all(row["operator_decision"] == "" for row in rows)
    assert all(row["auto_apply"] == "false" for row in rows)


def test_backfill_rows_hold_conflicting_provider_ids_for_manual_resolution() -> None:
    module = load_module()

    rows = module.build_backfill_rows(
        athlete_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "123",
        }],
        image_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "",
            "image_type": "headshot",
        }],
        approved_rows=[{
            "athlete_id": "atlanta_dream_test_player",
            "display_name": "Test Player",
            "team_id": "atlanta_dream",
            "provider_player_id": "999",
        }],
        review_rows=[],
    )

    assert rows
    assert {row["backfill_status"] for row in rows} == {"provider_id_conflict_manual_resolution"}
    assert all(row["proposed_value"] == "" for row in rows)
    assert all("123:" in row["candidate_sources"] and "999:" in row["candidate_sources"] for row in rows)


def test_closure_packet_main_writes_run_scoped_artifacts_without_registry_mutation(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    asset = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "atlanta_dream_test_player" / "headshot.png"
    marker = Path(asset.as_posix() + ".approved")
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"headshot-bytes")
    marker.write_text(json.dumps({
        "athlete_id": "atlanta_dream_test_player",
        "display_name": "Test Player",
        "team_id": "atlanta_dream",
        "provider_player_id": "123",
        "decision_source": "default",
    }), encoding="utf-8")

    registry = tmp_path / "data" / "asset_registry" / "wnba"
    athletes_csv = registry / "athletes.csv"
    athlete_images_csv = registry / "athlete_images.csv"
    approved_csv = registry / "athlete_image_approved_assets.csv"
    match_review_csv = registry / "athlete_image_match_review.csv"
    write_csv(athletes_csv, [{
        "athlete_id": "atlanta_dream_test_player",
        "league": "WNBA",
        "display_name": "Test Player",
        "team_id": "atlanta_dream",
        "provider_player_id": "",
        "status": "active_candidate",
        "source_url": "",
        "last_verified_utc": "",
        "notes": "",
    }], ["athlete_id", "league", "display_name", "team_id", "provider_player_id", "status", "source_url", "last_verified_utc", "notes"])
    write_csv(athlete_images_csv, [{
        "athlete_id": "atlanta_dream_test_player",
        "display_name": "Test Player",
        "team_id": "atlanta_dream",
        "provider_player_id": "",
        "image_type": "headshot",
        "file_path": asset.relative_to(tmp_path).as_posix(),
        "file_exists": "true",
        "approved": "true",
        "source_note": "approved_marker_required",
        "last_verified_utc": "",
    }], ["athlete_id", "display_name", "team_id", "provider_player_id", "image_type", "file_path", "file_exists", "approved", "source_note", "last_verified_utc"])
    write_csv(approved_csv, [{
        "athlete_id": "atlanta_dream_test_player",
        "display_name": "Test Player",
        "team_id": "atlanta_dream",
        "provider_player_id": "123",
        "approved_file": asset.relative_to(tmp_path).as_posix(),
        "approved_marker": marker.relative_to(tmp_path).as_posix(),
        "source_file": "outputs/latest/review_files/athlete_image_approval_pack/downloads/atlanta_dream/player__123.png",
        "approved_at_utc": "2026-06-25T00:00:00+00:00",
        "decision_source": "default",
    }], ["athlete_id", "display_name", "team_id", "provider_player_id", "approved_file", "approved_marker", "source_file", "approved_at_utc", "decision_source"])
    write_csv(match_review_csv, [{
        "team_id": "atlanta_dream",
        "athlete_id": "atlanta_dream_test_player",
        "display_name": "Test Player",
        "provider_player_id": "123",
        "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/123.png",
        "match_method": "fixture",
        "confidence": "0.72",
        "status": "needs_human_approval",
        "approval_target_path": asset.relative_to(tmp_path).as_posix(),
        "notes": "fixture",
    }], ["team_id", "athlete_id", "display_name", "provider_player_id", "image_url", "match_method", "confidence", "status", "approval_target_path", "notes"])
    before_athletes = athletes_csv.read_text(encoding="utf-8")
    before_images = athlete_images_csv.read_text(encoding="utf-8")

    assert module.main() == 0

    closure_path = run_dir / "data" / "asset_registry" / "wnba" / "athlete_identity_issue_closure_template.csv"
    backfill_path = run_dir / "data" / "asset_registry" / "wnba" / "athlete_identity_provider_id_backfill_template.csv"
    packet_path = run_dir / "data" / "asset_registry" / "wnba" / "athlete_identity_closure_packet.json"
    assert closure_path.exists()
    assert backfill_path.exists()
    assert packet_path.exists()
    assert not (tmp_path / "data" / "asset_registry" / "wnba" / "athlete_identity_issue_closure_template.csv").exists()

    closure_rows = read_csv(closure_path)
    backfill_rows = read_csv(backfill_path)
    manifest = json.loads(packet_path.read_text(encoding="utf-8"))

    assert closure_rows
    assert any(row["issue_code"] == "default_approval_requires_identity_recheck" for row in closure_rows)
    assert any(row["proposed_value"] == "123" and row["target_csv"].endswith("athletes.csv") for row in backfill_rows)
    assert manifest["report"]["policy"]["canonical_registries_unchanged"] is True
    assert athletes_csv.read_text(encoding="utf-8") == before_athletes
    assert athlete_images_csv.read_text(encoding="utf-8") == before_images
