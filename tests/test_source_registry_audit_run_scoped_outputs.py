from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "generate_hsd_source_registry_audit_v2.py"


def write_registry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "registry_version": "test-registry",
                "green_approved_decision": ["Use official scoreboards for publish-ready facts."],
                "sources": [
                    {
                        "source_id": "espn_wnba_public",
                        "source_type": "scoreboard_site",
                        "tier": "official",
                        "trust_band": "green",
                        "enabled": True,
                        "sport_league": "WNBA",
                        "automation_status": "manual_or_fetch_allowed",
                        "publish_policy": "publish_ready_after_cross_check",
                        "urls": ["https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard"],
                    },
                    {
                        "source_id": "social_tip",
                        "source_type": "mastodon_public",
                        "tier": "social",
                        "trust_band": "yellow",
                        "enabled": True,
                        "sport_league": "Women sports",
                        "automation_status": "manual_review",
                        "publish_policy": "discovery_only",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_source_proposals(path: Path) -> None:
    write_csv(
        path,
        [
            {
                "coverage_key": "wnba",
                "display_name": "WNBA",
                "needed_source_type": "scoreboard_or_stats_cross_check",
                "coverage_gap": "missing scoreboard/stat/cross-check source",
                "candidate_source_id": "espn_wnba_public",
                "candidate_source_name": "Duplicate ESPN WNBA source",
                "candidate_url": "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard",
                "candidate_domain": "",
                "source_type": "scoreboard_site",
                "tier": "stats_provider",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "WNBA",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "cross_check; scores",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Duplicate test row.",
            },
            {
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "pwhl_instagram",
                "candidate_source_name": "PWHL Instagram",
                "candidate_url": "https://www.instagram.com/thepwhlofficial/",
                "candidate_domain": "",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Social account should not become trusted registry coverage.",
            },
            {
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "scoreboard_or_stats_cross_check",
                "coverage_gap": "missing scoreboard/stat/cross-check source",
                "candidate_source_id": "pwhl_paid_api",
                "candidate_source_name": "Paid API",
                "candidate_url": "https://api.sportsdata.io/v3/pwhl/scores/json",
                "candidate_domain": "",
                "source_type": "scoreboard_site",
                "tier": "stats_provider",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "Yes",
                "automation_status": "manual_review",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "cross_check",
                "operator_verification_status": "unverified",
                "registry_action": "import_to_registry",
                "review_notes": "Requires paid API key and account login.",
            },
            {
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "pwhl_official_site",
                "candidate_source_name": "PWHL official site",
                "candidate_url": "https://www.thepwhl.com/en/",
                "candidate_domain": "",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news; team_news; source_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Free public official candidate for human review.",
            },
        ],
    )


def stdout_json(proc: subprocess.CompletedProcess[str]) -> dict:
    start = proc.stdout.index("{")
    return json.loads(proc.stdout[start:])


def test_source_registry_audit_writes_outputs_to_run_folder(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    run_dir = tmp_path / "run" / "files"
    work_dir.mkdir()
    write_registry(work_dir / "config" / "source_registry.json")
    write_source_proposals(work_dir / "operator" / "inbox" / "source_registry_proposals.csv")

    env = os.environ.copy()
    env["HSD_RUN_OUTPUT_DIR"] = str(run_dir)
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = stdout_json(proc)
    assert payload["output_scope"] == "run_scoped"
    assert payload["sources"] == 2
    assert payload["review"] == 1
    assert payload["fail"] == 0
    assert (run_dir / "source_registry_audit.csv").exists()
    assert (run_dir / "source_coverage_map.csv").exists()
    assert (run_dir / "source_registry_intake_template.csv").exists()
    assert (run_dir / "source_registry_intake_template.md").exists()
    assert (run_dir / "source_registry_proposal_review.csv").exists()
    assert (run_dir / "source_registry_proposal_review.md").exists()
    assert (run_dir / "source_proposal_packs.csv").exists()
    assert (run_dir / "source_proposal_packs.md").exists()
    assert (run_dir / "wnba_source_proposal_pack.csv").exists()
    assert (run_dir / "wnba_source_proposal_pack.md").exists()
    assert (run_dir / "nwsl_source_proposal_pack.csv").exists()
    assert (run_dir / "nwsl_source_proposal_pack.md").exists()
    assert (run_dir / "lpga_source_proposal_pack.csv").exists()
    assert (run_dir / "lpga_source_proposal_pack.md").exists()
    assert (run_dir / "pwhl_source_proposal_pack.csv").exists()
    assert (run_dir / "pwhl_source_proposal_pack.md").exists()
    assert (run_dir / "source_registry_audit.md").exists()
    assert (run_dir / "source_registry_audit.json").exists()
    assert not (work_dir / "source_registry_audit.csv").exists()
    assert not (work_dir / "source_registry_audit.md").exists()

    manifest = json.loads((run_dir / "source_registry_audit.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "run_scoped"
    assert manifest["registry_version"] == "test-registry"
    assert manifest["counts"]["coverage_total"] >= 1
    assert manifest["counts"]["intake_template_rows"] >= 1
    assert manifest["counts"]["proposal_review_rows"] == 4
    assert manifest["counts"]["proposal_hold"] == 3
    assert manifest["counts"]["proposal_ready"] == 1
    assert manifest["counts"]["proposal_pack_leagues"] == 4
    assert manifest["counts"]["proposal_pack_rows"] == 57
    assert manifest["counts"]["proposal_pack_official"] == 39
    assert manifest["counts"]["proposal_pack_cross_check"] == 18
    assert manifest["counts"]["wnba_proposal_pack_rows"] == 13
    assert manifest["counts"]["nwsl_proposal_pack_rows"] == 15
    assert manifest["counts"]["lpga_proposal_pack_rows"] == 10
    assert manifest["counts"]["pwhl_proposal_pack_rows"] == 19
    assert manifest["counts"]["pwhl_proposal_pack_official"] == 14
    assert manifest["counts"]["pwhl_proposal_pack_cross_check"] == 5
    assert any(row["coverage_key"] == "pwhl" and row["coverage_status"] == "gap" for row in manifest["coverage_map"])
    intake_rows = manifest["source_registry_intake_template"]
    assert any(row["coverage_key"] == "pwhl" and row["proposed_enabled"] == "No" for row in intake_rows)
    assert all(row["registry_action"] == "proposal_only_do_not_import" for row in intake_rows)
    intake_csv = (run_dir / "source_registry_intake_template.csv").read_text(encoding="utf-8")
    assert "proposal_only_not_publish_ready" in intake_csv
    intake_md = (run_dir / "source_registry_intake_template.md").read_text(encoding="utf-8")
    assert "Rows are proposal-only and disabled by default" in intake_md
    proposal_review = read_csv(run_dir / "source_registry_proposal_review.csv")
    by_id = {row["candidate_source_id"]: row for row in proposal_review}
    assert by_id["espn_wnba_public"]["review_status"] == "hold"
    assert "duplicate" in by_id["espn_wnba_public"]["safety_flags"]
    assert by_id["pwhl_instagram"]["review_status"] == "hold"
    assert "social_only" in by_id["pwhl_instagram"]["safety_flags"]
    assert by_id["pwhl_paid_api"]["review_status"] == "hold"
    assert "paid_or_api" in by_id["pwhl_paid_api"]["safety_flags"]
    assert "login_only" in by_id["pwhl_paid_api"]["safety_flags"]
    assert "auto_enable_attempt" in by_id["pwhl_paid_api"]["safety_flags"]
    assert by_id["pwhl_official_site"]["review_status"] == "ready_for_registry_review"
    proposal_md = (run_dir / "source_registry_proposal_review.md").read_text(encoding="utf-8")
    assert "paid/API sources" in proposal_md
    assert "No rows are imported automatically" in proposal_md
    proposal_packs = read_csv(run_dir / "source_proposal_packs.csv")
    assert len(proposal_packs) == 57
    assert proposal_packs[0]["pack_key"] == "wnba"
    assert proposal_packs[0]["pack_name"] == "WNBA Source Proposal Pack"
    proposal_pack_ids = {row["candidate_source_id"] for row in proposal_packs}
    assert "wnba_official_teams_index_review" in proposal_pack_ids
    assert "nwsl_official_teams_index_review" in proposal_pack_ids
    assert "lpga_official_tournaments_review" in proposal_pack_ids
    assert "pwhl_official_home" in proposal_pack_ids
    proposal_packs_md = (run_dir / "source_proposal_packs.md").read_text(encoding="utf-8")
    assert "HSD Guided Source Proposal Packs" in proposal_packs_md
    assert "WNBA Source Proposal Pack" in proposal_packs_md
    assert "NWSL Source Proposal Pack" in proposal_packs_md
    assert "LPGA Source Proposal Pack" in proposal_packs_md
    assert "PWHL Source Proposal Pack" in proposal_packs_md
    wnba_pack = read_csv(run_dir / "wnba_source_proposal_pack.csv")
    assert len(wnba_pack) == 13
    wnba_by_id = {row["candidate_source_id"]: row for row in wnba_pack}
    assert wnba_by_id["wnba_toronto_tempo_team_review"]["candidate_url"] == "https://tempo.wnba.com/"
    assert wnba_by_id["espn_wnba_scoreboard_pack_review"]["candidate_domain"] == "espn.com"
    assert all(row["pack_key"] == "wnba" for row in wnba_pack)
    assert all(row["proposed_enabled"] == "No" for row in wnba_pack)
    nwsl_pack = read_csv(run_dir / "nwsl_source_proposal_pack.csv")
    assert len(nwsl_pack) == 15
    nwsl_by_id = {row["candidate_source_id"]: row for row in nwsl_pack}
    assert nwsl_by_id["nwsl_boston_legacy_team_review"]["candidate_url"] == "https://bostonlegacyfc.com/"
    assert nwsl_by_id["espn_nwsl_standings_cross_check"]["candidate_domain"] == "espn.com"
    assert all(row["pack_key"] == "nwsl" for row in nwsl_pack)
    assert all(row["registry_action"] == "proposal_only_do_not_import" for row in nwsl_pack)
    lpga_pack = read_csv(run_dir / "lpga_source_proposal_pack.csv")
    assert len(lpga_pack) == 10
    lpga_by_id = {row["candidate_source_id"]: row for row in lpga_pack}
    assert lpga_by_id["lpga_official_tournaments_review"]["candidate_url"] == "https://www.lpga.com/tournaments"
    assert lpga_by_id["kpmg_womens_pga_leaderboard_review"]["candidate_domain"] == "lpga.com"
    assert all(row["pack_key"] == "lpga" for row in lpga_pack)
    assert all(row["publish_policy"] == "proposal_only_not_publish_ready" for row in lpga_pack)
    pwhl_pack = read_csv(run_dir / "pwhl_source_proposal_pack.csv")
    assert len(pwhl_pack) == 19
    pwhl_by_id = {row["candidate_source_id"]: row for row in pwhl_pack}
    assert pwhl_by_id["pwhl_official_news"]["candidate_url"] == "https://www.thepwhl.com/en/news"
    assert pwhl_by_id["pwhl_boston_fleet_team"]["candidate_url"] == "https://www.thepwhl.com/en/teams/boston-fleet"
    assert pwhl_by_id["pwhl_official_scores"]["candidate_group"] == "league_cross_check"
    assert pwhl_by_id["eliteprospects_pwhl_cross_check"]["candidate_domain"] == "eliteprospects.com"
    assert pwhl_by_id["hockeydb_pwhl_cross_check"]["candidate_domain"] == "hockeydb.com"
    assert all(row["proposed_enabled"] == "No" for row in pwhl_pack)
    assert all(row["registry_action"] == "proposal_only_do_not_import" for row in pwhl_pack)
    assert all(row["publish_policy"] == "proposal_only_not_publish_ready" for row in pwhl_pack)
    assert all(row["pack_key"] == "pwhl" for row in pwhl_pack)
    assert manifest["wnba_source_proposal_pack"][0]["candidate_source_id"] == "wnba_official_home_review"
    assert manifest["nwsl_source_proposal_pack"][0]["candidate_source_id"] == "nwsl_official_home_review"
    assert manifest["lpga_source_proposal_pack"][0]["candidate_source_id"] == "lpga_official_home_review"
    assert manifest["pwhl_source_proposal_pack"][0]["candidate_source_id"] == "pwhl_official_home"
    assert manifest["source_proposal_packs"][0]["candidate_source_id"] == "wnba_official_home_review"
    assert [row["pack_key"] for row in manifest["source_proposal_pack_index"]] == ["wnba", "nwsl", "lpga", "pwhl"]
    assert [row["rows"] for row in manifest["source_proposal_pack_index"]] == [13, 15, 10, 19]
    wnba_pack_md = (run_dir / "wnba_source_proposal_pack.md").read_text(encoding="utf-8")
    assert "WNBA Source Proposal Pack" in wnba_pack_md
    assert "wnba_toronto_tempo_team_review" in wnba_pack_md
    nwsl_pack_md = (run_dir / "nwsl_source_proposal_pack.md").read_text(encoding="utf-8")
    assert "NWSL Source Proposal Pack" in nwsl_pack_md
    assert "nwsl_boston_legacy_team_review" in nwsl_pack_md
    lpga_pack_md = (run_dir / "lpga_source_proposal_pack.md").read_text(encoding="utf-8")
    assert "LPGA Source Proposal Pack" in lpga_pack_md
    assert "kpmg_womens_pga_leaderboard_review" in lpga_pack_md
    pwhl_pack_md = (run_dir / "pwhl_source_proposal_pack.md").read_text(encoding="utf-8")
    assert "PWHL Source Proposal Pack" in pwhl_pack_md
    assert "No rows are imported automatically" in pwhl_pack_md
    assert "pwhl_vancouver_goldeneyes_team" in pwhl_pack_md
    report = (run_dir / "source_registry_audit.md").read_text(encoding="utf-8")
    assert "## Coverage map" in report
    assert "## Manual source intake template" in report
    assert "## Manual source proposal review" in report
    assert "## Guided source proposal packs" in report
    assert "PWHL" in report


def test_source_registry_audit_preserves_legacy_root_output_when_env_unset(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    write_registry(work_dir / "config" / "source_registry.json")

    env = os.environ.copy()
    env.pop("HSD_RUN_OUTPUT_DIR", None)
    env["PYTHONPATH"] = str(REPO)

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=work_dir,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = stdout_json(proc)
    assert payload["output_scope"] == "legacy_root"
    assert (work_dir / "source_registry_audit.csv").exists()
    assert (work_dir / "source_coverage_map.csv").exists()
    assert (work_dir / "source_registry_intake_template.csv").exists()
    assert (work_dir / "source_registry_intake_template.md").exists()
    assert (work_dir / "source_registry_proposal_review.csv").exists()
    assert (work_dir / "source_registry_proposal_review.md").exists()
    assert (work_dir / "source_proposal_packs.csv").exists()
    assert (work_dir / "source_proposal_packs.md").exists()
    assert (work_dir / "wnba_source_proposal_pack.csv").exists()
    assert (work_dir / "wnba_source_proposal_pack.md").exists()
    assert (work_dir / "nwsl_source_proposal_pack.csv").exists()
    assert (work_dir / "nwsl_source_proposal_pack.md").exists()
    assert (work_dir / "lpga_source_proposal_pack.csv").exists()
    assert (work_dir / "lpga_source_proposal_pack.md").exists()
    assert (work_dir / "pwhl_source_proposal_pack.csv").exists()
    assert (work_dir / "pwhl_source_proposal_pack.md").exists()
    assert (work_dir / "source_registry_audit.md").exists()
    assert (work_dir / "source_registry_audit.json").exists()
