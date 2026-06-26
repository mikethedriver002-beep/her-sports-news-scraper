from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_logo_asset_catalog_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_logo_asset_catalog_v1", SCRIPT)
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


def test_logo_asset_catalog_is_review_only_and_reports_formats(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)

    registry_root = tmp_path / "data" / "asset_registry"
    league_root = registry_root / "wnba"
    mapping = tmp_path / "config" / "graphics" / "template_render_mapping_v1.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text(
        json.dumps(
            {
                "event_mappings": [
                    {"league": "WNBA", "template_id": "game_recap_final_score.a.v1"},
                    {"league": "NWSL", "template_id": "womens_soccer_match_story.a.v1"},
                ],
                "batch_mappings": [
                    {"name": "last_night_in_the_w_feed_threads", "template_id": "last_night_in_the_w.a.v1"},
                ],
            }
        ),
        encoding="utf-8",
    )

    write_csv(
        league_root / "teams.csv",
        [
            {"team_id": "approved_team", "league": "WNBA", "team_name": "Approved Team"},
            {"team_id": "review_team", "league": "WNBA", "team_name": "Review Team"},
            {"team_id": "missing_team", "league": "WNBA", "team_name": "Missing Team"},
        ],
        ["team_id", "league", "team_name"],
    )
    write_csv(
        league_root / "team_logos.csv",
        [
            {
                "team_id": "approved_team",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/approved_team/logo.png",
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "last_verified_utc": "2026-06-25T00:00:00+00:00",
                "source_note": "test_approved",
            },
            {
                "team_id": "review_team",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/review_team/logo.png",
                "file_exists": "true",
                "approved": "false",
                "required": "true",
                "last_verified_utc": "2026-06-25T00:00:00+00:00",
                "source_note": "test_review",
            },
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"],
    )
    write_csv(
        league_root / "logo_sources.csv",
        [
            {
                "team_id": "approved_team",
                "team_name": "Approved Team",
                "source_url": "https://example.test/approved.svg",
                "target_path": "assets/leagues/wnba/teams/approved_team/logo.png",
                "source_note": "test_source",
            }
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )

    (tmp_path / "assets" / "leagues" / "wnba" / "teams" / "approved_team").mkdir(parents=True)
    (tmp_path / "assets" / "leagues" / "wnba" / "teams" / "approved_team" / "logo.png").write_bytes(b"png")
    (tmp_path / "assets" / "leagues" / "wnba" / "teams" / "approved_team" / "logo.svg").write_text("<svg />", encoding="utf-8")
    (tmp_path / "assets" / "leagues" / "wnba" / "teams" / "review_team").mkdir(parents=True)
    (tmp_path / "assets" / "leagues" / "wnba" / "teams" / "review_team" / "logo.png").write_bytes(b"png")

    report = module.build_catalog(registry_root, mapping)
    rows = {row["team_id"] or row["entity_type"]: row for row in report["rows"]}

    assert report["review_only"] is True
    assert report["policy"]["no_auto_approval"] is True
    assert rows["approved_team"]["approval_status"] == "approved"
    assert rows["approved_team"]["png_exists"] == "true"
    assert rows["approved_team"]["svg_exists"] == "true"
    assert rows["approved_team"]["source_trust_status"] == "source_policy_not_registered_review_required"
    assert rows["approved_team"]["operator_action"] == "manual_source_recheck_required_before_operator_trust"
    assert rows["review_team"]["approval_status"] == "unapproved_review_required"
    assert rows["review_team"]["fallback_status"] == "fallback_review_only_human_hold"
    assert rows["missing_team"]["approval_status"] == "not_registered"
    assert rows["missing_team"]["operator_action"] == "add_manual_registry_row_after_evidence_review"
    assert rows["league_logo"]["entity_type"] == "league_logo"
    assert rows["league_logo"]["approval_status"] == "missing"
    assert rows["approved_team"]["render_template_ids"] == "game_recap_final_score.a.v1;last_night_in_the_w.a.v1"


def test_logo_asset_catalog_flags_verified_registry_blocked_sources(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)

    league_root = tmp_path / "data" / "asset_registry" / "wnba"
    verified = tmp_path / "config" / "hsd_verified_logo_registry_v1.json"
    verified.parent.mkdir(parents=True, exist_ok=True)
    verified.write_text(
        json.dumps(
            {
                "teams": {
                    "Portland Fire": {
                        "league": "WNBA",
                        "blocked_url_substrings": ["wikipedia/en/c/cf/Portland_Fire_logo.svg"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    write_csv(
        league_root / "teams.csv",
        [{"team_id": "portland_fire", "league": "WNBA", "team_name": "Portland Fire"}],
        ["team_id", "league", "team_name"],
    )
    write_csv(
        league_root / "team_logos.csv",
        [
            {
                "team_id": "portland_fire",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/portland_fire/logo.png",
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "last_verified_utc": "2026-06-25T00:00:00+00:00",
                "source_note": "test_approved_but_stale_source",
            }
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"],
    )
    write_csv(
        league_root / "logo_sources.csv",
        [
            {
                "team_id": "portland_fire",
                "team_name": "Portland Fire",
                "source_url": "https://upload.wikimedia.org/wikipedia/en/c/cf/Portland_Fire_logo.svg",
                "target_path": "assets/leagues/wnba/teams/portland_fire/logo.svg",
                "source_note": "legacy_source_should_be_flagged",
            }
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )
    logo_dir = tmp_path / "assets" / "leagues" / "wnba" / "teams" / "portland_fire"
    logo_dir.mkdir(parents=True)
    (logo_dir / "logo.png").write_bytes(b"png")

    report = module.build_catalog(tmp_path / "data" / "asset_registry", tmp_path / "missing_mapping.json", verified)
    rows = {row["team_id"] or row["entity_type"]: row for row in report["rows"]}
    portland = rows["portland_fire"]

    assert portland["approval_status"] == "approved"
    assert portland["source_trust_status"] == "blocked_stale_source_review_required"
    assert portland["verified_registry_status"] == "blocked_source_url_match"
    assert portland["blocked_url_match"] == "wikipedia/en/c/cf/Portland_Fire_logo.svg"
    assert portland["operator_action"] == "replace_or_reverify_blocked_source_before_manual_approval"
    assert report["source_trust_status_counts"]["blocked_stale_source_review_required"] == 1


def test_logo_asset_catalog_main_writes_reports_to_run_folder(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    assert module.main([]) == 0

    assert (run_dir / "data" / "asset_registry" / "logo_asset_catalog.csv").exists()
    assert (run_dir / "data" / "asset_registry" / "logo_asset_catalog.json").exists()
    assert (run_dir / "data" / "asset_registry" / "logo_asset_catalog.md").exists()
    assert not (tmp_path / "data" / "asset_registry" / "logo_asset_catalog.csv").exists()
