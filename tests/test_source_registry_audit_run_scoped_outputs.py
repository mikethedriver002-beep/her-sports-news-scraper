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


def write_source_verification_log(path: Path) -> None:
    write_csv(
        path,
        [
            {
                "verification_log_status": "operator_review_recorded",
                "operator_step": "open_url_record_freshness_duplicate_decision_and_approval_outcome",
                "source_id": "wnba_official_home_review",
                "source_name": "WNBA official site",
                "candidate_url": "https://www.wnba.com/",
                "candidate_domain": "wnba.com",
                "diff_review_status": "PASS",
                "diff_flags": "none",
                "diff_issues": "none",
                "registry_domain_match": "No",
                "worksheet_domain_match": "No",
                "url_checked": "https://www.wnba.com/",
                "checked_at_local": "2026-06-24 09:00",
                "freshness_result": "current",
                "duplicate_decision": "not_duplicate",
                "approval_outcome": "approved_for_manual_registry_edit",
                "registry_edit_decision": "manual_edit_planned",
                "operator_name": "operator",
                "evidence_url": "https://www.wnba.com/",
                "operator_notes": "Verified free public official homepage.",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "verification_log_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
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
    write_source_verification_log(work_dir / "operator" / "inbox" / "source_registry_verification_log.csv")

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
    assert (run_dir / "source_registry_proposal_draft.csv").exists()
    assert (run_dir / "source_registry_proposal_draft.md").exists()
    assert (run_dir / "source_registry_proposal_promotion_checklist.csv").exists()
    assert (run_dir / "source_registry_proposal_promotion_checklist.md").exists()
    assert (run_dir / "source_registry_update_worksheet.csv").exists()
    assert (run_dir / "source_registry_update_worksheet.md").exists()
    assert (run_dir / "source_registry_diff_review.csv").exists()
    assert (run_dir / "source_registry_diff_review.md").exists()
    assert (run_dir / "source_registry_verification_log.csv").exists()
    assert (run_dir / "source_registry_verification_log.md").exists()
    assert (run_dir / "source_registry_approval_packet.csv").exists()
    assert (run_dir / "source_registry_approval_packet.md").exists()
    assert (run_dir / "source_proposal_pack_readiness.csv").exists()
    assert (run_dir / "source_proposal_pack_readiness.md").exists()
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
    assert manifest["counts"]["proposal_pack_ready"] == 4
    assert manifest["counts"]["proposal_pack_duplicate_review"] == 0
    assert manifest["counts"]["proposal_pack_freshness_check"] == 0
    assert manifest["counts"]["proposal_draft_rows"] == 20
    assert manifest["counts"]["proposal_draft_ready_to_copy"] == 20
    assert manifest["counts"]["proposal_draft_blocked"] == 0
    assert manifest["counts"]["proposal_promotion_checklist_rows"] == 20
    assert manifest["counts"]["proposal_promotion_verify_then_copy"] == 20
    assert manifest["counts"]["proposal_promotion_hold"] == 0
    assert manifest["counts"]["proposal_promotion_discard"] == 0
    assert manifest["counts"]["registry_update_worksheet_rows"] == 20
    assert manifest["counts"]["registry_update_worksheet_disabled"] == 20
    assert manifest["counts"]["registry_diff_review_rows"] == 20
    assert manifest["counts"]["registry_diff_review_hold"] == 0
    assert manifest["counts"]["registry_diff_review_review"] >= 1
    assert manifest["counts"]["registry_diff_review_pass"] >= 1
    assert manifest["counts"]["source_verification_log_rows"] == 20
    assert manifest["counts"]["source_verification_log_input_required"] == 19
    assert manifest["counts"]["source_verification_log_recorded"] == 1
    assert manifest["counts"]["registry_approval_packet_rows"] == 1
    assert manifest["counts"]["registry_approval_packet_ready"] == 1
    assert manifest["counts"]["registry_approval_packet_hold"] == 0
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
    proposal_draft = read_csv(run_dir / "source_registry_proposal_draft.csv")
    assert len(proposal_draft) == 20
    assert proposal_draft[0]["draft_selection_status"] == "ready_to_copy_after_freshness_check"
    assert proposal_draft[0]["draft_action"] == "manual_copy_to_inbox_after_freshness_check"
    assert proposal_draft[0]["proposed_enabled"] == "No"
    assert proposal_draft[0]["registry_action"] == "proposal_only_do_not_import"
    assert "Open this public page manually" in proposal_draft[0]["freshness_warning"]
    assert "No duplicate candidates detected" in proposal_draft[0]["duplicate_warning"]
    assert all(row["operator_verification_status"] == "unverified" for row in proposal_draft)
    proposal_draft_md = (run_dir / "source_registry_proposal_draft.md").read_text(encoding="utf-8")
    assert "Source Registry Proposal Draft" in proposal_draft_md
    assert "not the live proposal inbox" in proposal_draft_md
    promotion_checklist = read_csv(run_dir / "source_registry_proposal_promotion_checklist.csv")
    assert len(promotion_checklist) == 20
    assert promotion_checklist[0]["checklist_decision"] == "verify_then_copy"
    assert promotion_checklist[0]["copy_allowed"] == "Yes_after_manual_freshness_check"
    assert promotion_checklist[0]["copy_target"] == "operator/inbox/source_registry_proposals.csv"
    assert promotion_checklist[0]["proposed_enabled"] == "No"
    assert promotion_checklist[0]["registry_action"] == "proposal_only_do_not_import"
    assert "open candidate_url manually" in promotion_checklist[0]["verification_checklist"]
    assert "copy this row into" in promotion_checklist[0]["copy_instructions"]
    promotion_checklist_md = (run_dir / "source_registry_proposal_promotion_checklist.md").read_text(encoding="utf-8")
    assert "Promotion Checklist" in promotion_checklist_md
    assert "verify then copy: 20" in promotion_checklist_md
    registry_update_worksheet = read_csv(run_dir / "source_registry_update_worksheet.csv")
    assert len(registry_update_worksheet) == 20
    assert registry_update_worksheet[0]["worksheet_decision"] == "manual_registry_plan_after_verification"
    assert registry_update_worksheet[0]["manual_edit_target"] == "config/source_registry.json"
    assert registry_update_worksheet[0]["manual_edit_allowed"] == "Yes_only_after_operator_verification"
    assert registry_update_worksheet[0]["auto_edit_status"] == "not_performed_by_generator"
    assert registry_update_worksheet[0]["proposed_enabled"] == "False"
    assert registry_update_worksheet[0]["proposed_automation_status"] == "disabled_manual_review_only"
    assert "wnba_official_home_review" in registry_update_worksheet[0]["proposed_source_json"]
    assert "Before: no manual change from this generator" in registry_update_worksheet[0]["before_after_diff"]
    assert "remove the manually added" in registry_update_worksheet[0]["rollback_note"]
    registry_update_worksheet_md = (run_dir / "source_registry_update_worksheet.md").read_text(encoding="utf-8")
    assert "Source Registry Update Worksheet" in registry_update_worksheet_md
    assert "does not edit `config/source_registry.json`" in registry_update_worksheet_md
    registry_diff_review = read_csv(run_dir / "source_registry_diff_review.csv")
    assert len(registry_diff_review) == 20
    assert registry_diff_review[0]["diff_review_status"] == "PASS"
    assert registry_diff_review[0]["source_id"] == "wnba_official_home_review"
    assert registry_diff_review[0]["proposed_enabled"] == "False"
    assert registry_diff_review[0]["proposed_json_status"] == "valid_json"
    assert registry_diff_review[0]["rollback_status"] == "present"
    assert registry_diff_review[0]["registry_source_id_match"] == "No"
    assert any(row["diff_review_status"] == "REVIEW" for row in registry_diff_review)
    assert any("worksheet_domain_repeat" in row["flags"] for row in registry_diff_review)
    registry_diff_review_md = (run_dir / "source_registry_diff_review.md").read_text(encoding="utf-8")
    assert "Source Registry Diff Review" in registry_diff_review_md
    assert "does not edit files" in registry_diff_review_md
    verification_log = read_csv(run_dir / "source_registry_verification_log.csv")
    assert len(verification_log) == 20
    assert verification_log[0]["source_id"] == "wnba_official_home_review"
    assert verification_log[0]["diff_review_status"] == "PASS"
    approved_log = next(row for row in verification_log if row["source_id"] == "wnba_official_home_review")
    assert approved_log["verification_log_status"] == "operator_review_recorded"
    assert approved_log["url_checked"] == "https://www.wnba.com/"
    assert approved_log["freshness_result"] == "current"
    assert approved_log["duplicate_decision"] == "not_duplicate"
    assert approved_log["approval_outcome"] == "approved_for_manual_registry_edit"
    assert any(row["verification_log_status"] == "operator_input_required" for row in verification_log)
    assert verification_log[0]["auto_edit_status"] == "not_performed_by_generator"
    assert verification_log[0]["registry_edit_status"] == "not_edited_by_generator"
    verification_log_md = (run_dir / "source_registry_verification_log.md").read_text(encoding="utf-8")
    assert "Source Registry Verification Log" in verification_log_md
    assert "url_checked" in verification_log_md
    approval_packet = read_csv(run_dir / "source_registry_approval_packet.csv")
    assert len(approval_packet) == 1
    assert approval_packet[0]["approval_packet_status"] == "ready_for_final_manual_review"
    assert approval_packet[0]["source_id"] == "wnba_official_home_review"
    assert approval_packet[0]["evidence_url"] == "https://www.wnba.com/"
    assert approval_packet[0]["hold_reason"] == "none"
    assert "wnba_official_home_review" in approval_packet[0]["exact_proposed_source_json"]
    assert approval_packet[0]["registry_edit_status"] == "not_edited_by_generator"
    approval_packet_md = (run_dir / "source_registry_approval_packet.md").read_text(encoding="utf-8")
    assert "Source Registry Approval Packet" in approval_packet_md
    assert "approved rows summarized: 1" in approval_packet_md
    pack_readiness = read_csv(run_dir / "source_proposal_pack_readiness.csv")
    assert len(pack_readiness) == 4
    readiness_by_key = {row["pack_key"]: row for row in pack_readiness}
    assert readiness_by_key["wnba"]["readiness_status"] == "ready_for_registry_proposal"
    assert readiness_by_key["wnba"]["official_candidates"] == "8"
    assert readiness_by_key["wnba"]["cross_check_candidates"] == "5"
    assert "wnba_official_home_review" in readiness_by_key["wnba"]["top_candidate_ids"]
    assert readiness_by_key["nwsl"]["readiness_status"] == "ready_for_registry_proposal"
    assert readiness_by_key["lpga"]["readiness_status"] == "ready_for_registry_proposal"
    assert readiness_by_key["pwhl"]["readiness_status"] == "ready_for_registry_proposal"
    assert all(row["duplicate_candidates"] == "0" for row in pack_readiness)
    pack_readiness_md = (run_dir / "source_proposal_pack_readiness.md").read_text(encoding="utf-8")
    assert "Guided Source Proposal Pack Readiness" in pack_readiness_md
    assert "ready_for_registry_proposal" in pack_readiness_md
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
    assert manifest["source_registry_proposal_draft"][0]["candidate_source_id"] == "wnba_official_home_review"
    assert manifest["source_registry_proposal_draft"][0]["draft_action"] == "manual_copy_to_inbox_after_freshness_check"
    assert manifest["source_registry_proposal_promotion_checklist"][0]["candidate_source_id"] == "wnba_official_home_review"
    assert manifest["source_registry_proposal_promotion_checklist"][0]["checklist_decision"] == "verify_then_copy"
    assert manifest["source_registry_update_worksheet"][0]["source_id"] == "wnba_official_home_review"
    assert manifest["source_registry_update_worksheet"][0]["auto_edit_status"] == "not_performed_by_generator"
    assert manifest["source_registry_diff_review"][0]["source_id"] == "wnba_official_home_review"
    assert manifest["source_registry_diff_review"][0]["diff_review_status"] == "PASS"
    assert manifest["source_registry_verification_log"][0]["source_id"] == "wnba_official_home_review"
    assert manifest["source_registry_verification_log"][0]["verification_log_status"] == "operator_review_recorded"
    assert manifest["source_registry_approval_packet"][0]["source_id"] == "wnba_official_home_review"
    assert manifest["source_registry_approval_packet"][0]["approval_packet_status"] == "ready_for_final_manual_review"
    assert manifest["source_proposal_pack_readiness"][0]["pack_key"] == "wnba"
    assert manifest["source_proposal_pack_readiness"][0]["readiness_status"] == "ready_for_registry_proposal"
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
    assert "source_registry_proposal_draft.csv" in report
    assert "source_registry_proposal_promotion_checklist.csv" in report
    assert "source_registry_update_worksheet.csv" in report
    assert "source_registry_diff_review.csv" in report
    assert "source_registry_verification_log.csv" in report
    assert "source_registry_approval_packet.csv" in report
    assert "source_proposal_pack_readiness.csv" in report
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
    assert (work_dir / "source_registry_proposal_draft.csv").exists()
    assert (work_dir / "source_registry_proposal_draft.md").exists()
    assert (work_dir / "source_registry_proposal_promotion_checklist.csv").exists()
    assert (work_dir / "source_registry_proposal_promotion_checklist.md").exists()
    assert (work_dir / "source_registry_update_worksheet.csv").exists()
    assert (work_dir / "source_registry_update_worksheet.md").exists()
    assert (work_dir / "source_registry_diff_review.csv").exists()
    assert (work_dir / "source_registry_diff_review.md").exists()
    assert (work_dir / "source_registry_verification_log.csv").exists()
    assert (work_dir / "source_registry_verification_log.md").exists()
    assert (work_dir / "source_registry_approval_packet.csv").exists()
    assert (work_dir / "source_registry_approval_packet.md").exists()
    assert (work_dir / "source_proposal_pack_readiness.csv").exists()
    assert (work_dir / "source_proposal_pack_readiness.md").exists()
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
