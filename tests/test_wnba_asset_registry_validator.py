from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "validate_hsd_wnba_asset_registry_v1.py"
GAP_SCRIPT = REPO / "scripts" / "report_hsd_wnba_asset_gaps_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_hsd_wnba_asset_registry_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_gap_module():
    spec = importlib.util.spec_from_file_location("report_hsd_wnba_asset_gaps_v1", GAP_SCRIPT)
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


def test_validator_treats_existing_unapproved_logo_as_operator_review(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data" / "asset_registry" / "wnba"
    logo_path = tmp_path / "assets" / "leagues" / "wnba" / "teams" / "atlanta_dream" / "logo.png"
    logo_path.parent.mkdir(parents=True)
    logo_path.write_bytes(b"exact-logo")

    write_csv(
        root / "teams.csv",
        [{"team_id": "atlanta_dream", "league": "WNBA", "team_name": "Atlanta Dream"}],
        ["team_id", "league", "team_name"],
    )
    write_csv(root / "team_aliases.csv", [], ["team_id", "alias"])
    write_csv(
        root / "team_logos.csv",
        [
            {
                "team_id": "atlanta_dream",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/atlanta_dream/logo.png",
                "file_exists": "true",
                "approved": "false",
                "required": "true",
                "last_verified_utc": "2026-06-25T00:00:00+00:00",
                "source_note": "local_png_exists_review_required_exact_logo",
            }
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"],
    )
    write_csv(
        root / "logo_sources.csv",
        [
            {
                "team_id": "atlanta_dream",
                "team_name": "Atlanta Dream",
                "source_url": "https://example.test/atlanta-dream-logo.png",
                "target_path": "assets/leagues/wnba/teams/atlanta_dream/logo.png",
                "source_note": "fixture_exact_logo_source",
            }
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )

    result, missing_rows = module.build_validation(root)

    assert result["review_only"] is True
    assert result["policy"]["no_auto_approval"] is True
    assert result["status"] == "operator_review"
    assert result["missing_required_team_logos"] == 0
    assert result["unapproved_required_team_logos"] == 1
    assert missing_rows == []
    assert "human review required" in result["operator_warnings"][0]


def test_validator_reports_true_missing_required_logo(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data" / "asset_registry" / "wnba"

    write_csv(
        root / "teams.csv",
        [{"team_id": "missing_team", "league": "WNBA", "team_name": "Missing Team"}],
        ["team_id", "league", "team_name"],
    )
    write_csv(root / "team_aliases.csv", [], ["team_id", "alias"])
    write_csv(
        root / "team_logos.csv",
        [
            {
                "team_id": "missing_team",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/missing_team/logo.png",
                "file_exists": "false",
                "approved": "false",
                "required": "true",
                "last_verified_utc": "2026-06-25T00:00:00+00:00",
                "source_note": "missing_required_exact_logo",
            }
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"],
    )
    write_csv(
        root / "logo_sources.csv",
        [
            {
                "team_id": "missing_team",
                "team_name": "Missing Team",
                "source_url": "https://example.test/missing-team-logo.png",
                "target_path": "assets/leagues/wnba/teams/missing_team/logo.png",
                "source_note": "fixture_exact_logo_source",
            }
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )

    result, missing_rows = module.build_validation(root)

    assert result["status"] == "needs_assets"
    assert result["missing_required_team_logos"] == 1
    assert result["unapproved_required_team_logos"] == 0
    assert len(missing_rows) == 1
    missing = missing_rows[0]
    assert missing["team_id"] == "missing_team"
    assert missing["team_name"] == "Missing Team"
    assert missing["required_asset"] == "primary_logo"
    assert missing["reason"] == "required exact team logo file not found"
    assert missing["recommended_path"] == "assets/leagues/wnba/teams/missing_team/logo.png"
    assert missing["decision_packet_id"] == "asset_logo_blocker_missing_team"
    assert missing["decision_review_status"] == "operator_asset_decision_required"
    assert missing["allowed_decisions"] == "supply_exact_logo_for_review|hold_logo_slot|revise_registry_metadata"
    assert missing["renderer_fallback_cue"].startswith("Renderer text/logo fallback remains review-only")
    assert missing["publish_ready"] == "false"
    assert result["missing_logo_decision_packets"] == 1


def test_validator_flags_duplicate_logo_bytes_and_source_path_drift(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data" / "asset_registry" / "wnba"
    teams = [
        {"team_id": "alpha_team", "league": "WNBA", "team_name": "Alpha Team"},
        {"team_id": "beta_team", "league": "WNBA", "team_name": "Beta Team"},
    ]
    for team in teams:
        logo_path = tmp_path / "assets" / "leagues" / "wnba" / "teams" / team["team_id"] / "logo.png"
        logo_path.parent.mkdir(parents=True)
        logo_path.write_bytes(b"same-logo-bytes")

    write_csv(root / "teams.csv", teams, ["team_id", "league", "team_name"])
    write_csv(root / "team_aliases.csv", [], ["team_id", "alias"])
    write_csv(
        root / "team_logos.csv",
        [
            {
                "team_id": team["team_id"],
                "asset_type": "primary_logo",
                "file_path": f"assets/leagues/wnba/teams/{team['team_id']}/logo.png",
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "last_verified_utc": "2026-06-25T00:00:00+00:00",
                "source_note": "fixture_approved",
            }
            for team in teams
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"],
    )
    write_csv(
        root / "logo_sources.csv",
        [
            {
                "team_id": "alpha_team",
                "team_name": "Alpha Team",
                "source_url": "https://example.test/alpha.svg",
                "target_path": "assets/leagues/wnba/teams/alpha_team/logo.svg",
                "source_note": "fixture_svg_source",
            },
            {
                "team_id": "beta_team",
                "team_name": "Beta Team",
                "source_url": "https://example.test/beta.png",
                "target_path": "assets/leagues/wnba/teams/beta_team/logo.png",
                "source_note": "fixture_png_source",
            },
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )

    result, missing_rows = module.build_validation(root)

    assert result["status"] == "pass"
    assert missing_rows == []
    assert any("duplicate logo file bytes across teams" in warning for warning in result["warnings"])
    assert any("alpha_team: source target_path differs" in warning for warning in result["source_path_metadata_warnings"])


def test_gap_report_preserves_missing_logo_decision_packet_fields(tmp_path: Path, monkeypatch) -> None:
    validator = load_module()
    gap = load_gap_module()
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "data" / "asset_registry" / "wnba"
    root.mkdir(parents=True)
    missing = {
        "team_id": "missing_team",
        "team_name": "Missing Team",
        "required_asset": "primary_logo",
        "reason": "required exact team logo file not found",
        "recommended_path": "assets/leagues/wnba/teams/missing_team/logo.png",
        **validator.missing_logo_decision_packet(
            "missing_team",
            "Missing Team",
            "assets/leagues/wnba/teams/missing_team/logo.png",
        ),
    }
    with (root / "missing_team_logos.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=validator.MISSING_LOGO_FIELDS)
        writer.writeheader()
        writer.writerow(missing)
    (root / "asset_registry_validation.json").write_text(
        json.dumps({"status": "needs_assets", "operator_warnings": [], "source_path_metadata_warnings": []}),
        encoding="utf-8",
    )

    gap.main()

    rows = list(csv.DictReader((root / "logo_gap_upload_manifest.csv").open(newline="", encoding="utf-8")))
    assert rows[0]["decision_packet_id"] == "asset_logo_blocker_missing_team"
    assert rows[0]["allowed_decisions"] == "supply_exact_logo_for_review|hold_logo_slot|revise_registry_metadata"
    assert rows[0]["renderer_fallback_cue"].startswith("Renderer text/logo fallback remains review-only")
    assert rows[0]["auto_publish"] == "false"
    report = json.loads((root / "asset_gap_report.json").read_text(encoding="utf-8"))
    assert report["decision_packet_count"] == 1
    assert report["policy"]["no_auto_approval"] is True
