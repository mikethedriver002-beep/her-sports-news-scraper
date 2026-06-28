from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_womens_soccer_athlete_verification_queue_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_womens_soccer_athlete_verification_queue_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_womens_soccer_athlete_verification_queue_buckets_review_only_rows(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    root = tmp_path / "data/asset_registry/womens_soccer"
    write_csv(
        root / "womens_soccer_athlete_photo_operator_board.csv",
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "candidate_rows": "2",
                "official_roster_candidate_rows": "2",
                "starter_candidate_rows": "0",
                "local_candidate_files_present": "0",
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
            },
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "bay_fc",
                "team_name": "Bay FC",
                "candidate_rows": "1",
                "official_roster_candidate_rows": "1",
                "starter_candidate_rows": "0",
                "local_candidate_files_present": "0",
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
            },
            {
                "scope_id": "europe_top_flight",
                "league_id": "wsl_england",
                "team_id": "chelsea_women",
                "team_name": "Chelsea Women",
                "candidate_rows": "1",
                "official_roster_candidate_rows": "0",
                "starter_candidate_rows": "1",
                "local_candidate_files_present": "0",
                "manual_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "download_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_download_intake.csv",
            },
        ],
        [
            "scope_id",
            "league_id",
            "team_id",
            "team_name",
            "candidate_rows",
            "official_roster_candidate_rows",
            "starter_candidate_rows",
            "local_candidate_files_present",
            "manual_intake_file",
            "download_intake_file",
        ],
    )
    write_csv(
        root / "womens_soccer_athlete_photo_contact_sheet.csv",
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "local_candidate_exists": "false",
                "source_domain": "www.nwslsoccer.com",
            },
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "local_candidate_exists": "false",
                "source_domain": "www.nwslsoccer.com",
            },
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "bay_fc",
                "team_name": "Bay FC",
                "local_candidate_exists": "false",
                "source_domain": "www.nwslsoccer.com",
            },
            {
                "scope_id": "europe_top_flight",
                "league_id": "wsl_england",
                "team_id": "chelsea_women",
                "team_name": "Chelsea Women",
                "local_candidate_exists": "false",
                "source_domain": "www.chelseafc.com",
            },
        ],
        ["scope_id", "league_id", "team_id", "team_name", "local_candidate_exists", "source_domain"],
    )
    write_csv(
        root / "womens_soccer_athlete_photo_download_intake.csv",
        [
            {"league_id": "nwsl", "team_id": "angel_city_fc", "download_approved": "no"},
            {"league_id": "nwsl", "team_id": "angel_city_fc", "download_approved": "no"},
            {"league_id": "nwsl", "team_id": "bay_fc", "download_approved": "no"},
            {"league_id": "wsl_england", "team_id": "chelsea_women", "download_approved": "no"},
        ],
        ["league_id", "team_id", "download_approved"],
    )
    write_csv(
        root / "external_research/womens_soccer_external_research_intake_board.csv",
        [
            {
                "research_lane": "nwsl_correction_enrichment",
                "operator_bucket": "p0_nwsl_operator_verify_first",
                "league_id": "nwsl",
                "team_name": "angel_city_fc",
                "source_domain": "www.angelcity.com",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "nwsl_correction_enrichment",
                "operator_bucket": "p1_metadata_candidate_only",
                "league_id": "nwsl",
                "team_name": "bay_fc",
                "source_domain": "bayfc.com",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "europe_official_source_map",
                "operator_bucket": "europe_operator_verify_required",
                "league_id": "wsl_england",
                "team_name": "Chelsea Women",
                "source_domain": "www.chelseafc.com",
                "official_status": "official_team",
                "operator_verify_required": "yes",
            },
            {
                "research_lane": "europe_official_source_map",
                "operator_bucket": "europe_gray_area_manual_verification_only",
                "league_id": "wsl_england",
                "team_name": "Backup",
                "source_domain": "example.org",
                "official_status": "gray_area_public_source",
                "operator_verify_required": "yes",
            },
        ],
        [
            "research_lane",
            "operator_bucket",
            "league_id",
            "team_name",
            "source_domain",
            "official_status",
            "operator_verify_required",
        ],
    )
    module = load_module()

    assert module.main() == 0

    rows = read_csv(root / "womens_soccer_athlete_verification_queue.csv")
    manifest = json.loads((root / "womens_soccer_athlete_verification_queue.json").read_text(encoding="utf-8"))
    markdown = (root / "womens_soccer_athlete_verification_queue.md").read_text(encoding="utf-8")

    assert manifest["status"] == "athlete_verification_queue_ready"
    assert manifest["queue_rows"] == 3
    assert manifest["nwsl_team_rows"] == 2
    assert manifest["europe_league_rows"] == 1
    assert manifest["p0_nwsl_roster_verification_rows"] == 1
    assert manifest["gray_area_rows"] == 1
    assert manifest["missing_local_candidate_rows"] == 4
    assert manifest["download_approved_yes_rows"] == 0
    by_team = {row["team_id"]: row for row in rows}
    assert by_team["angel_city_fc"]["queue_bucket"] == "p0_nwsl_roster_verification_first"
    assert by_team["bay_fc"]["queue_bucket"] == "p1_nwsl_local_candidate_assets_missing"
    assert by_team["all_teams"]["queue_bucket"] == "p1_europe_gray_area_source_review"
    assert by_team["all_teams"]["render_readiness"] == "not_render_ready_source_candidate_only"
    for row in rows:
        assert row["review_only"] == "true"
        assert row["approval_state_change"] == "false"
        assert row["candidate_state_change"] == "false"
        assert row["asset_downloads"] == "false"
        assert row["headshot_writes"] == "false"
        assert row["approved_marker_writes"] == "false"
        assert row["publish_ready"] == "false"
        assert row["auto_approval"] == "false"
        assert row["auto_publish"] == "false"
        assert row["move_files"] == "false"
        assert row["paid_apis"] == "false"
    assert "does not download images" in markdown
    assert "Europe rows as source-map candidates only" in markdown
