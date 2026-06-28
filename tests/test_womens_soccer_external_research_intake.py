from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_womens_soccer_external_research_intake_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_womens_soccer_external_research_intake_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str], *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding=encoding) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_external_research_intake_generates_review_only_operator_board(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    root = tmp_path / "data/asset_registry/womens_soccer/external_research"
    nwsl_fields = [
        "issue_type",
        "team_id_or_name",
        "player_name_if_applicable",
        "current_value_if_known",
        "suggested_value",
        "source_priority",
        "source_type",
        "evidence_url",
        "source_domain",
        "official_status",
        "confidence",
        "operator_action",
        "notes",
    ]
    europe_fields = [
        "league_id",
        "league_name",
        "team_name",
        "source_priority",
        "source_type",
        "source_url",
        "roster_url_if_available",
        "player_profile_url_pattern_if_visible",
        "source_domain",
        "official_status",
        "rights_or_usage_note",
        "freshness_note",
        "confidence",
        "operator_verify_required",
        "citation_url",
    ]
    write_rows(
        root / "nwsl_correction_enrichment_report.csv",
        [
            {
                "issue_type": "stale_team_assignment_duplicate_identity",
                "team_id_or_name": "angel_city_fc",
                "player_name_if_applicable": "Alyssa Thompson",
                "current_value_if_known": "",
                "suggested_value": "verify official roster",
                "source_priority": "P0",
                "source_type": "official_team_roster",
                "evidence_url": "https://www.angelcity.com/club/roster",
                "source_domain": "www.angelcity.com",
                "official_status": "official_team",
                "confidence": "high",
                "operator_action": "verify_duplicate_identity",
                "notes": "Needs current official source review.",
            },
            {
                "issue_type": "source_domain_change_candidate",
                "team_id_or_name": "gotham_fc",
                "player_name_if_applicable": "Midge Purce",
                "current_value_if_known": "",
                "suggested_value": "new profile URL",
                "source_priority": "P1",
                "source_type": "official_team_profile",
                "evidence_url": "https://www.gothamfc.com/players",
                "source_domain": "www.gothamfc.com",
                "official_status": "official_team",
                "confidence": "high",
                "operator_action": "source_url_enrichment",
                "notes": "Metadata candidate only.",
            },
            {
                "issue_type": "gray_area_public_backup_candidate",
                "team_id_or_name": "gotham_fc",
                "player_name_if_applicable": "Sam Kerr",
                "current_value_if_known": "",
                "suggested_value": "gray-area lead",
                "source_priority": "P3",
                "source_type": "public_media",
                "evidence_url": "https://www.reuters.com/sports/soccer/example",
                "source_domain": "www.reuters.com",
                "official_status": "non_official_reputable_media",
                "confidence": "low",
                "operator_action": "park_gray_area_lead_for_manual_verification",
                "notes": "Not current official roster confirmation.",
            },
        ],
        nwsl_fields,
        encoding="utf-8-sig",
    )
    write_rows(
        root / "europe_official_source_map.csv",
        [
            {
                "league_id": "WSL",
                "league_name": "Women's Super League",
                "team_name": "Chelsea",
                "source_priority": "P0_OFFICIAL_CLUB_ROSTER",
                "source_type": "official_club_roster",
                "source_url": "https://www.chelseafc.com/en/teams/chelsea-women",
                "roster_url_if_available": "https://www.chelseafc.com/en/teams/chelsea-women",
                "player_profile_url_pattern_if_visible": "",
                "source_domain": "www.chelseafc.com",
                "official_status": "official_team",
                "rights_or_usage_note": "Official page metadata only.",
                "freshness_note": "Current roster page visible.",
                "confidence": "high",
                "operator_verify_required": "no",
                "citation_url": "https://www.chelseafc.com/en/teams/chelsea-women",
            },
            {
                "league_id": "Liga F",
                "league_name": "Liga F",
                "team_name": "Barcelona",
                "source_priority": "P0_OFFICIAL_LEAGUE_TEAM",
                "source_type": "official_league_team",
                "source_url": "https://www.ligaf.es/",
                "roster_url_if_available": "",
                "player_profile_url_pattern_if_visible": "",
                "source_domain": "www.ligaf.es",
                "official_status": "official_league",
                "rights_or_usage_note": "Official page metadata only.",
                "freshness_note": "Team page requires operator check.",
                "confidence": "medium",
                "operator_verify_required": "yes",
                "citation_url": "https://www.ligaf.es/",
            },
            {
                "league_id": "Arkema Premiere Ligue",
                "league_name": "Arkema Premiere Ligue",
                "team_name": "Lyon",
                "source_priority": "P2_PUBLIC_DATABASE_BACKUP",
                "source_type": "public_database",
                "source_url": "https://example.org/lyon",
                "roster_url_if_available": "",
                "player_profile_url_pattern_if_visible": "",
                "source_domain": "example.org",
                "official_status": "gray_area_public_source",
                "rights_or_usage_note": "Backup lead only.",
                "freshness_note": "Park for manual verification.",
                "confidence": "low_medium",
                "operator_verify_required": "yes",
                "citation_url": "https://example.org/lyon",
            },
        ],
        europe_fields,
    )
    module = load_module()

    assert module.main() == 0

    board = read_rows(root / "womens_soccer_external_research_intake_board.csv")
    manifest = json.loads((root / "womens_soccer_external_research_intake_board.json").read_text(encoding="utf-8"))
    markdown = (root / "womens_soccer_external_research_intake_board.md").read_text(encoding="utf-8")

    assert manifest["nwsl_rows"] == 3
    assert manifest["europe_rows"] == 3
    assert manifest["board_rows"] == 6
    assert manifest["operator_bucket_counts"] == {
        "europe_gray_area_manual_verification_only": 1,
        "europe_official_no_verify_metadata_candidate": 1,
        "europe_operator_verify_required": 1,
        "p0_nwsl_operator_verify_first": 1,
        "p1_metadata_candidate_only": 1,
        "p3_gray_area_manual_verification_only": 1,
    }
    assert manifest["sam_kerr_reuters_gray_area_only"] is True
    assert manifest["review_only"] is True
    for key in [
        "approval_state_change",
        "candidate_state_change",
        "asset_downloads",
        "headshot_writes",
        "approved_marker_writes",
        "publish_ready",
        "publishing",
        "paid_apis",
    ]:
        assert manifest[key] is False

    buckets = {(row["research_lane"], row["player_name"] or row["team_name"]): row for row in board}
    assert buckets[("nwsl_correction_enrichment", "Alyssa Thompson")]["operator_bucket"] == "p0_nwsl_operator_verify_first"
    assert buckets[("nwsl_correction_enrichment", "Midge Purce")]["operator_bucket"] == "p1_metadata_candidate_only"
    assert buckets[("nwsl_correction_enrichment", "Sam Kerr")]["operator_bucket"] == "p3_gray_area_manual_verification_only"
    assert buckets[("europe_official_source_map", "Chelsea")]["operator_bucket"] == "europe_official_no_verify_metadata_candidate"
    assert buckets[("europe_official_source_map", "Barcelona")]["operator_bucket"] == "europe_operator_verify_required"
    assert buckets[("europe_official_source_map", "Lyon")]["operator_bucket"] == "europe_gray_area_manual_verification_only"
    for row in board:
        assert row["review_only"] == "true"
        assert row["approval_state_change"] == "false"
        assert row["candidate_state_change"] == "false"
        assert row["asset_downloads"] == "false"
        assert row["headshot_writes"] == "false"
        assert row["approved_marker_writes"] == "false"
        assert row["publish_ready"] == "false"
        assert row["publishing"] == "false"
        assert row["paid_apis"] == "false"
    assert "does not download images" in markdown
    assert "Sam Kerr/Gotham Reuters row is not current official roster confirmation" in markdown
