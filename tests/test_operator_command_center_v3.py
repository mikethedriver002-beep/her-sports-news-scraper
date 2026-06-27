from __future__ import annotations

import csv
import json
from pathlib import Path

import generate_hsd_operator_command_center_v2 as command_center

REPO = Path(__file__).resolve().parents[1]


def write_json(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload), encoding="utf-8")


def write_csv(path: str, rows: list[dict[str, str]]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_active_logo_readiness_matches_team_nicknames_and_audit_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    audit_dir = Path("data/asset_registry")
    audit_dir.mkdir(parents=True)
    write_json(
        "data/asset_registry/asset_availability_audit.json",
        {
            "findings": [
                {
                    "asset_domain": "team_logo",
                    "entity_name": "New York Liberty",
                    "entity_id": "new_york_liberty",
                    "finding": "logo_present_without_complete_approval",
                    "recommended_next_step": "human_review_required_before_renderer_logo_use",
                    "renderer_fallback_cue": "text_badge_or_placeholder_fallback_is_review_only_human_hold",
                }
            ]
        },
    )

    packet = {
        "title": "Liberty beat Aces",
        "asset_requirement": "Use exact local WNBA team logos from the registry.",
    }

    readiness = command_center.active_logo_readiness_for_packet(packet)
    assert readiness["active_logo_readiness_status"] == "hold_logo_review_required"
    assert "New York Liberty: logo_present_without_complete_approval" in readiness["active_logo_review_cues"]
    assert readiness["logo_review_artifact"] == "data/asset_registry/asset_availability_audit.csv"
    assert "review_only_human_hold" in readiness["renderer_fallback_cue"]
    assert command_center.active_logo_entity_matches("sky edge sun", "Chicago Sky", "chicago_sky")
    assert not command_center.active_logo_entity_matches("sunday preview", "Connecticut Sun", "connecticut_sun")


def test_asset_readiness_panel_surfaces_logo_contact_sheet(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    registry = Path("data/asset_registry/wnba")
    registry.mkdir(parents=True)
    write_json(
        "data/asset_registry/asset_availability_audit.json",
        {
            "status": "review_required",
            "finding_count": 1,
            "severity_counts": {"warning": 1},
            "asset_domain_counts": {"team_logo": 1},
            "finding_counts": {"logo_present_without_complete_approval": 1},
            "policy": {"no_auto_approval": True, "no_asset_downloads": True},
            "findings": [],
        },
    )
    write_csv_with_fields(
        "data/asset_registry/wnba/logo_review_packets.csv",
        [
            {
                "decision_packet_id": "asset_logo_review_atlanta_dream_unapproved_required_team_logo",
                "team_id": "atlanta_dream",
                "team_name": "Atlanta Dream",
                "issue_type": "unapproved_required_team_logo",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        [
            "decision_packet_id",
            "team_id",
            "team_name",
            "issue_type",
            "review_only",
            "publish_ready",
            "auto_approval",
            "auto_publish",
            "move_files",
            "paid_apis",
            "asset_downloads",
        ],
    )
    write_csv_with_fields(
        "data/asset_registry/wnba/wnba_team_logo_contact_sheet.csv",
        [
            {
                "team_id": "atlanta_dream",
                "team_name": "Atlanta Dream",
                "local_logo_path": "assets/leagues/wnba/teams/atlanta_dream/logo.png",
                "official_source_candidate": "https://www.wnba.com/team/atlanta-dream",
                "current_approval_status": "unapproved_review_required",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        [
            "team_id",
            "team_name",
            "local_logo_path",
            "official_source_candidate",
            "current_approval_status",
            "review_only",
            "publish_ready",
            "auto_approval",
            "auto_publish",
            "move_files",
            "paid_apis",
            "asset_downloads",
        ],
    )
    Path("data/asset_registry/wnba/wnba_team_logo_contact_sheet.md").write_text("# Contact sheet\n", encoding="utf-8")
    write_json(
        "data/asset_registry/wnba/wnba_team_logo_contact_sheet.json",
        {"status": "contact_sheet_ready", "team_rows": 1, "review_only": True},
    )

    panel = command_center.asset_availability_readiness_panel()
    html = command_center.render_asset_readiness_panel(panel)

    assert panel["logo_contact_sheet_rows"] == 1
    assert panel["logo_contact_sheet_status"] == "contact_sheet_ready"
    assert panel["logo_contact_sheet_freshness_status"] == "packet_ready"
    assert any(item["label"] == "WNBA team logo contact sheet" for item in panel["file_shortcuts"])
    assert any(item["label"] == "WNBA team logo review intake" for item in panel["file_shortcuts"])
    assert "Logo sweep rows" in html
    assert "Logo contact sheet packet freshness" in html


def test_asset_readiness_panel_surfaces_womens_soccer_logo_contact_sheet(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    registry = Path("data/asset_registry/womens_soccer")
    registry.mkdir(parents=True)
    write_json(
        "data/asset_registry/asset_availability_audit.json",
        {
            "status": "review_required",
            "finding_count": 0,
            "severity_counts": {},
            "asset_domain_counts": {},
            "finding_counts": {},
            "policy": {"no_auto_approval": True, "no_asset_downloads": True},
            "findings": [],
        },
    )
    write_csv_with_fields(
        "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.csv",
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "display_name": "Angel City FC",
                "local_logo_path": "assets/leagues/womens_soccer/nwsl/teams/angel_city_fc/logo.png",
                "official_source_candidate": "https://www.angelcity.com/",
                "current_approval_status": "not_approved",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            },
            {
                "scope_id": "europe_top_flight",
                "league_id": "wsl_england",
                "entity_type": "league",
                "entity_id": "wsl_england",
                "display_name": "Barclays Women's Super League",
                "local_logo_path": "assets/leagues/womens_soccer/europe_top_flight/wsl_england/league_mark.png",
                "official_source_candidate": "https://www.wslfootball.com/",
                "current_approval_status": "not_approved",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            },
        ],
        [
            "scope_id",
            "league_id",
            "entity_type",
            "entity_id",
            "display_name",
            "local_logo_path",
            "official_source_candidate",
            "current_approval_status",
            "review_only",
            "publish_ready",
            "auto_approval",
            "auto_publish",
            "move_files",
            "paid_apis",
            "asset_downloads",
        ],
    )
    Path("data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.md").write_text("# Contact sheet\n", encoding="utf-8")
    write_json(
        "data/asset_registry/womens_soccer/womens_soccer_logo_contact_sheet.json",
        {"status": "contact_sheet_ready", "row_count": 2, "review_only": True},
    )
    write_csv_with_fields(
        "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.csv",
        [
            {
                "review_rank": "1",
                "priority_group": "P0_NWSL_TEAM_LOGOS",
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "entity_type": "team",
                "entity_id": "angel_city_fc",
                "display_name": "Angel City FC",
                "current_approval_status": "not_approved",
                "logo_file_exists": "false",
                "approval_precondition": "local_asset_missing_source_only_review",
                "recommended_operator_decision": "hold_for_more_evidence",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "asset_downloads": "false",
            }
        ],
        [
            "review_rank",
            "priority_group",
            "scope_id",
            "league_id",
            "entity_type",
            "entity_id",
            "display_name",
            "current_approval_status",
            "logo_file_exists",
            "approval_precondition",
            "recommended_operator_decision",
            "review_only",
            "publish_ready",
            "auto_approval",
            "asset_downloads",
        ],
    )
    Path("data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.md").write_text("# Walkthrough\n", encoding="utf-8")
    write_json(
        "data/asset_registry/womens_soccer/womens_soccer_logo_review_walkthrough.json",
        {"status": "walkthrough_ready", "row_count": 1, "review_only": True},
    )
    write_csv_with_fields(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet.csv",
        [
            {
                "scope_id": "nwsl",
                "league_id": "nwsl",
                "team_id": "angel_city_fc",
                "team_name": "Angel City FC",
                "player_id": "",
                "display_name": "operator_add_player_candidate",
                "candidate_id": "angel_city_fc_operator_add_candidate",
                "candidate_status": "operator_add_candidate",
                "registry_status": "candidate_layer_only_no_player_registry_write",
                "local_candidate_path": "assets/leagues/womens_soccer/nwsl/nwsl/teams/angel_city_fc/athletes/operator_fill_required/review_candidates/angel_city_fc_operator_add_candidate.png",
                "local_candidate_exists": "false",
                "approved_marker_path": "",
                "approved_marker_exists": "false",
                "current_approval_status": "not_approved",
                "identity_review_status": "operator_fill_required",
                "source_url": "https://www.angelcity.com/club/roster",
                "source_domain": "www.angelcity.com",
                "source_tier": "public_or_official_candidate",
                "source_kind": "roster_or_public_profile_candidate",
                "source_platform": "manual_research",
                "photo_candidate_url": "",
                "license_hint": "operator_review_required",
                "rights_note": "review_only_fair_use_tolerant_candidate; no renderer approval",
                "identity_evidence_notes": "Add exact player name before approval.",
                "identity_risk_flags": "missing_player_identity_candidate",
                "allowed_decisions": "approve_for_review_only_renderer_use|hold_identity|deny_candidate|revise_source_metadata|request_better_candidate",
                "human_intake_file": "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_review_intake.csv",
                "team_contact_sheet_path": "data/asset_registry/womens_soccer/athlete_photo_contact_sheets/nwsl/angel_city_fc.png",
                "team_review_board_path": "data/asset_registry/womens_soccer/athlete_photo_contact_sheets/nwsl/angel_city_fc.md",
                "review_only": "true",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
            }
        ],
        [
            "scope_id",
            "league_id",
            "team_id",
            "team_name",
            "player_id",
            "display_name",
            "candidate_id",
            "candidate_status",
            "registry_status",
            "local_candidate_path",
            "local_candidate_exists",
            "approved_marker_path",
            "approved_marker_exists",
            "current_approval_status",
            "identity_review_status",
            "source_url",
            "source_domain",
            "source_tier",
            "source_kind",
            "source_platform",
            "photo_candidate_url",
            "license_hint",
            "rights_note",
            "identity_evidence_notes",
            "identity_risk_flags",
            "allowed_decisions",
            "human_intake_file",
            "team_contact_sheet_path",
            "team_review_board_path",
            "review_only",
            "publish_ready",
            "auto_approval",
            "auto_publish",
            "move_files",
            "paid_apis",
            "asset_downloads",
        ],
    )
    Path("data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_index.md").write_text("# Athlete sheets\n", encoding="utf-8")
    write_json(
        "data/asset_registry/womens_soccer/womens_soccer_athlete_photo_contact_sheet_manifest.json",
        {
            "status": "contact_sheets_ready",
            "generated_at_utc": "2026-06-26T20:00:00+00:00",
            "candidate_rows": 1,
            "team_boards": 1,
            "warnings": ["angel_city_fc:pillow_unavailable_contact_sheet_not_created"],
            "review_only": True,
            "downloads_performed": False,
            "approvals_applied": False,
        },
    )

    panel = command_center.asset_availability_readiness_panel()
    html = command_center.render_asset_readiness_panel(panel)

    assert panel["womens_soccer_logo_contact_sheet_rows"] == 2
    assert panel["womens_soccer_logo_contact_sheet_status"] == "contact_sheet_ready"
    assert panel["womens_soccer_logo_contact_sheet_freshness_status"] == "packet_ready"
    assert panel["womens_soccer_logo_review_walkthrough_rows"] == 1
    assert panel["womens_soccer_logo_review_walkthrough_status"] == "walkthrough_ready"
    assert panel["womens_soccer_logo_review_walkthrough_freshness_status"] == "packet_ready"
    assert panel["womens_soccer_athlete_photo_contact_sheet_rows"] == 1
    assert panel["womens_soccer_athlete_photo_contact_sheet_team_boards"] == 1
    assert panel["womens_soccer_athlete_photo_contact_sheet_status"] == "contact_sheets_ready"
    assert panel["womens_soccer_athlete_photo_contact_sheet_generated_at"] == "2026-06-26T20:00:00+00:00"
    assert panel["womens_soccer_athlete_photo_contact_sheet_warning_count"] == 1
    assert panel["womens_soccer_athlete_photo_contact_sheet_freshness_status"] == "packet_ready"
    assert any(item["label"] == "Women's soccer logo contact sheet" for item in panel["file_shortcuts"])
    assert any(item["label"] == "Women's soccer logo review intake" for item in panel["file_shortcuts"])
    assert any(item["label"] == "Women's soccer logo review walkthrough" for item in panel["file_shortcuts"])
    assert any(item["label"] == "Women's soccer athlete photo contact sheets" for item in panel["file_shortcuts"])
    assert any(item["label"] == "Women's soccer athlete photo contact sheet data" for item in panel["file_shortcuts"])
    assert any(item["label"] == "Women's soccer athlete photo review intake" for item in panel["file_shortcuts"])
    assert any(item["label"] == "Women's soccer athlete photo manifest" for item in panel["file_shortcuts"])
    assert "Soccer logo sweep rows" in html
    assert "Soccer review steps" in html
    assert "Soccer athlete candidates" in html
    assert "Soccer athlete boards" in html
    assert "Soccer athlete warnings" in html
    assert "Women&#x27;s soccer logo contact sheet packet freshness" in html
    assert "Women&#x27;s soccer logo review walkthrough packet freshness" in html
    assert "Women&#x27;s soccer athlete photo contact sheets packet freshness" in html


def test_active_athlete_identity_statuses_distinguish_hold_review_and_clear(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    packet_dir = Path("data/asset_registry/wnba")
    packet_dir.mkdir(parents=True)
    rows = [
        {
            "athlete_id": "new_york_liberty_breanna_stewart",
            "display_name": "Breanna Stewart",
            "identity_review_status": "hold_identity_review_required",
            "identity_hold": "true",
            "default_approval_present": "true",
            "review_required": "true",
            "hold_reason_codes": "approved_asset_still_has_pending_match_review|default_approval_requires_identity_recheck",
            "focused_evidence": "approved marker decision_source=default",
        },
        {
            "athlete_id": "new_york_liberty_sabrina_ionescu",
            "display_name": "Sabrina Ionescu",
            "identity_review_status": "manual_identity_review_required",
            "identity_hold": "false",
            "default_approval_present": "true",
            "review_required": "true",
            "hold_reason_codes": "default_approval_requires_identity_recheck",
            "focused_evidence": "manual review needed",
        },
    ]
    write_csv("data/asset_registry/wnba/athlete_identity_review_packet.csv", rows)

    hold = command_center.active_athlete_identity_for_packet({"top_performers": "Breanna Stewart: PTS 20"})
    review = command_center.active_athlete_identity_for_packet({"top_performers": "Sabrina Ionescu: PTS 16"})
    clear = command_center.active_athlete_identity_for_packet({"top_performers": "Jonquel Jones: REB 8"})

    assert hold["active_athlete_identity_status"] == "hold_identity_review_required"
    assert "Breanna Stewart: hold_identity_review_required" in hold["active_athlete_identity_cues"]
    assert review["active_athlete_identity_status"] == "athlete_identity_review_required"
    assert "Sabrina Ionescu: manual_identity_review_required" in review["active_athlete_identity_cues"]
    assert clear["active_athlete_identity_status"] == "athlete_identity_not_flagged"
    assert clear["athlete_identity_artifact"] == "data/asset_registry/wnba/athlete_identity_audit.csv"


def test_active_athlete_identity_includes_closure_packet_cues(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    packet_dir = Path("data/asset_registry/wnba")
    packet_dir.mkdir(parents=True)
    review_row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "identity_review_status": "hold_identity_review_required",
        "identity_hold": "true",
        "default_approval_present": "true",
        "review_required": "true",
        "hold_reason_codes": "approved_asset_still_has_pending_match_review",
        "focused_evidence": "approved marker decision_source=default",
        "provider_player_id": "1627668",
        "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
    }
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_review_packet.csv",
        [review_row],
        list(review_row.keys()),
    )
    write_json(
        "data/asset_registry/wnba/athlete_identity_closure_packet.json",
        {"report": {"status": "manual_identity_closure_ready", "closure_rows": 1, "backfill_rows": 1}},
    )
    closure_row = {
        "issue_key": "issue_high",
        "severity": "high",
        "issue_code": "approved_asset_still_has_pending_match_review",
        "athlete_id": "new_york_liberty_breanna_stewart",
        "operator_closure_decision": "",
    }
    backfill_row = {
        "backfill_key": "backfill_provider",
        "target_csv": "data/asset_registry/wnba/athletes.csv",
        "athlete_id": "new_york_liberty_breanna_stewart",
        "target_field": "provider_player_id",
        "proposed_value": "1627668",
        "backfill_status": "manual_review_required",
        "operator_decision": "",
    }
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_issue_closure_template.csv",
        [closure_row],
        list(closure_row.keys()),
    )
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv",
        [backfill_row],
        list(backfill_row.keys()),
    )

    packet = {
        "packet_id": "render_prep_test",
        "title": "Breanna Stewart powers Liberty",
        "top_performers": "Breanna Stewart: PTS 20",
        "asset_requirement": "Use exact local WNBA team logos from the registry; no invented identity, no text-logo fallback, no player asset required.",
    }
    identity = command_center.active_athlete_identity_for_packet(packet)
    packet.update(identity)
    active_queue_rows = command_center.active_asset_review_queue_rows(packet)
    active_queue_md = command_center.render_active_asset_review_queue(packet, active_queue_rows)

    assert identity["active_athlete_identity_status"] == "hold_identity_review_required"
    assert "closure_rows=1" in identity["active_athlete_identity_closure_cues"]
    assert "provider_backfill_rows=1" in identity["active_athlete_identity_closure_cues"]
    assert identity["athlete_identity_closure_artifact"] == "data/asset_registry/wnba/athlete_identity_closure_packet.md"
    assert identity["athlete_identity_backfill_artifact"] == "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv"
    assert active_queue_rows[0]["identity_closure_artifact"] == "data/asset_registry/wnba/athlete_identity_closure_packet.md"
    assert active_queue_rows[0]["identity_backfill_artifact"] == "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv"
    assert active_queue_rows[0]["provider_player_id"] == "1627668"
    assert active_queue_rows[0]["approved_marker_path"] == "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved"
    assert active_queue_rows[0]["selected_template_blocking_status"] == "not_blocking_selected_template_photo_not_required"
    assert active_queue_rows[0]["decision_lane"] == "wnba_athlete_identity_resolution"
    assert active_queue_rows[0]["default_operator_decision"] == "hold_identity"
    assert active_queue_rows[0]["asset_readiness"] == "blocked_until_identity_resolution"
    assert active_queue_rows[0]["identity_confidence"] == "identity_hold_default_or_suspicious_approval"
    assert "Evidence: approved marker decision_source=default" in active_queue_md
    assert "Selected template blocker: `not_blocking_selected_template_photo_not_required`" in active_queue_md
    assert "Decision lane: `wnba_athlete_identity_resolution`" in active_queue_md
    assert "Identity confidence: `identity_hold_default_or_suspicious_approval`" in active_queue_md
    assert "Provider player ID: `1627668`" in active_queue_md
    assert "Approved marker path: `assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved`" in active_queue_md
    assert "Identity closure packet: `data/asset_registry/wnba/athlete_identity_closure_packet.md`" in active_queue_md
    assert "Identity backfill packet: `data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv`" in active_queue_md


def test_manual_asset_source_board_derives_review_only_rows_from_active_queue(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    packet_dir = Path("data/asset_registry/wnba")
    packet_dir.mkdir(parents=True)
    logo_packet = {
        "packet_id": "logo_packet_new_york_liberty_unapproved",
        "decision_packet_title": "WNBA logo review: New York Liberty",
        "team_id": "new_york_liberty",
        "team_name": "New York Liberty",
        "issue_type": "unapproved_required_logo",
        "decision_review_status": "operator_logo_review_required",
        "source_url": "https://example.test/liberty-logo.png",
        "registered_path": "assets/leagues/wnba/logos/new_york_liberty/logo.png",
        "source_target_path": "assets/leagues/wnba/teams/new_york_liberty/logo.svg",
        "primary_action": "Review exact local logo source evidence before renderer trust.",
        "allowed_decisions": "verify_logo_for_review_renders|hold_logo_slot|revise_logo_source_metadata",
    }
    write_csv_with_fields(
        "data/asset_registry/wnba/logo_review_packets.csv",
        [logo_packet],
        list(logo_packet.keys()),
    )
    identity_row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "identity_review_status": "hold_identity_review_required",
        "identity_hold": "true",
        "default_approval_present": "true",
        "hold_reason_codes": "default_approval_requires_identity_recheck",
        "source_check_url": "https://www.wnba.com/player/1627668/breanna-stewart",
        "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "focused_evidence": "approved marker decision_source=default",
    }
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_review_packet.csv",
        [identity_row],
        list(identity_row.keys()),
    )
    write_json("data/asset_registry/asset_availability_audit.json", {"findings": []})

    packet = {
        "packet_id": "render_prep_test",
        "title": "New York Liberty beat Las Vegas Aces",
        "top_performers": "Breanna Stewart: PTS 20",
        "asset_requirement": "Use exact local WNBA team logos from the registry; no invented identity, no text-logo fallback, no player asset required.",
    }
    active_rows = command_center.active_asset_review_queue_rows(packet)
    board_rows = command_center.manual_asset_source_board_rows(active_rows)
    board_md = command_center.render_manual_asset_source_board(packet, board_rows)

    assert len(board_rows) == 2
    liberty = next(row for row in board_rows if row["entity_name"] == "New York Liberty")
    breanna = next(row for row in board_rows if row["entity_name"] == "Breanna Stewart")
    assert liberty["priority"] == "P0_selected_template_hold"
    assert liberty["official_source_candidate"] == "https://example.test/liberty-logo.png"
    assert liberty["manual_search_query"] == '"New York Liberty" official logo PNG WNBA'
    assert liberty["current_local_asset"] == "assets/leagues/wnba/logos/new_york_liberty/logo.png"
    assert breanna["priority"] == "P1_future_photo_first_hold"
    assert breanna["official_source_candidate"] == "https://www.wnba.com/player/1627668/breanna-stewart"
    assert breanna["manual_search_query"] == '"Breanna Stewart" new york liberty WNBA official player profile photo'
    assert all(row["review_only"] == "true" for row in board_rows)
    assert all(row["manual_approval_required"] == "true" for row in board_rows)
    assert all(row["publish_ready"] == "false" for row in board_rows)
    assert all(row["auto_approval"] == "false" for row in board_rows)
    assert all(row["asset_downloads"] == "false" for row in board_rows)
    assert "Legacy `D:\\Her Sports Daily` asset-index/DDG packets are reference shape only" in board_md
    assert "Priority: `P0_selected_template_hold`" in board_md
    assert "Manual search query: `\"Breanna Stewart\" new york liberty WNBA official player profile photo`" in board_md
    assert "asset_downloads=false" in board_md


def test_decision_stop_go_summary_separates_blockers_from_context_rows() -> None:
    packet = {
        "packet_id": "render_prep_test",
        "title": "New York Liberty beat Las Vegas Aces",
        "active_asset_stop_go": "hold_required_manual_asset_review",
    }
    active_rows = [
        {
            "entity_name": "New York Liberty",
            "asset_domain": "team_logo",
            "selected_template_blocking_status": "blocking_selected_template_logo_review",
        },
        {
            "entity_name": "Breanna Stewart",
            "asset_domain": "athlete_photo",
            "selected_template_blocking_status": "not_blocking_selected_template_photo_not_required",
        },
        {
            "entity_name": "WNBA",
            "asset_domain": "league_logo",
            "selected_template_blocking_status": "not_blocking_selected_template_league_mark_not_required",
        },
    ]
    source_rows = [{"entity_name": row["entity_name"]} for row in active_rows]

    summary = command_center.decision_stop_go_summary(packet, active_rows, source_rows)

    assert summary["panel_status"] == "hold_selected_template_manual_asset_review"
    assert summary["selected_template_blockers"] == 1
    assert summary["selected_template_entities"] == "New York Liberty"
    assert summary["future_photo_first_holds"] == 1
    assert summary["future_photo_first_entities"] == "Breanna Stewart"
    assert summary["league_mark_context_holds"] == 1
    assert summary["league_mark_context_entities"] == "WNBA"
    assert summary["source_board_rows"] == 3
    assert summary["active_queue_artifact"] == "render_handoff_top_packet/active_asset_review_queue.md"
    assert summary["manual_asset_source_board_artifact"] == "render_handoff_top_packet/manual_asset_source_board.md"
    assert summary["manual_league_mark_context_intake_artifact"] == "render_handoff_top_packet/manual_league_mark_context_intake.md"
    assert "no downloads" in summary["guardrail_summary"]
    assert "no auto-approval" in summary["guardrail_summary"]
    checklist = command_center.decision_review_order_checklist(summary)
    assert [row["title"] for row in checklist] == [
        "Open active asset queue",
        "Open Manual Asset Source Board",
        "Open Manual Logo Verification Intake Bridge",
        "Open Manual League-Mark Context Intake",
        "Open WNBA logo review catalog",
    ]
    assert checklist[0]["artifact"] == "render_handoff_top_packet/active_asset_review_queue.md"
    assert checklist[1]["artifact"] == "render_handoff_top_packet/manual_asset_source_board.md"
    assert checklist[2]["artifact"] == "render_handoff_top_packet/manual_logo_verification_intake.md"
    assert checklist[3]["artifact"] == "render_handoff_top_packet/manual_league_mark_context_intake.md"
    assert checklist[4]["artifact"] == "data/asset_registry/wnba/logo_review_catalog_report.md"
    assert all(row["review_only"] == "true" for row in checklist)
    assert all(row["approval_state_change"] == "false" for row in checklist)
    assert all(row["asset_downloads"] == "false" for row in checklist)
    assert all(row["publishing"] == "false" for row in checklist)


def test_active_asset_evidence_gap_fields_are_display_only(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    packet_dir = Path("data/asset_registry/wnba")
    packet_dir.mkdir(parents=True)
    write_csv(
        "data/asset_registry/wnba/logo_review_catalog.csv",
        [
            {
                "entity_type": "league_logo",
                "entity_id": "wnba_league_primary",
                "team_id": "",
                "display_name": "WNBA",
                "local_asset_path": "assets/leagues/wnba/logo.png",
                "file_exists": "false",
                "registry_approved": "false",
                "status": "missing",
                "official_source_url": "https://www.wnba.com/",
                "current_registry_source_url": "",
                "source_policy_status": "official_source_needed_review_only",
            },
            {
                "entity_type": "team_logo",
                "entity_id": "new_york_liberty",
                "team_id": "new_york_liberty",
                "display_name": "New York Liberty",
                "local_asset_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "file_exists": "true",
                "registry_approved": "false",
                "status": "local_file_unapproved_review_required",
                "official_source_url": "https://liberty.wnba.com/",
                "current_registry_source_url": "https://upload.wikimedia.org/new-york-liberty-logo.png",
                "source_policy_status": "non_official_registry_source_review_required",
            },
        ],
    )
    write_csv(
        "data/asset_registry/wnba/logo_review_packets.csv",
        [
            {
                "decision_packet_id": "logo_packet_new_york_liberty_unapproved",
                "team_id": "new_york_liberty",
                "team_name": "New York Liberty",
                "decision_review_status": "unapproved_review_required",
                "issue_type": "unapproved_required_logo",
                "registered_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "source_target_path": "assets/leagues/wnba/teams/new_york_liberty/logo.png",
                "source_url": "",
                "blocker_summary": "local PNG exists but source/approval needs human review",
                "primary_action": "human_review_required_before_renderer_logo_use",
            }
        ],
    )
    write_json(
        "data/asset_registry/asset_availability_audit.json",
        {
            "findings": [
                {
                    "review_packet_id": "asset_review_0605_league_logo_WNBA",
                    "asset_domain": "league_logo",
                    "entity_id": "WNBA",
                    "entity_name": "WNBA",
                    "finding": "missing_or_unregistered_logo_asset",
                    "approval_status": "missing",
                    "asset_path": "assets/leagues/wnba/logo.png",
                    "recommended_next_step": "supply_exact_local_logo_and_manual_registry_review",
                    "evidence": "png_exists=false; svg_exists=false; path_missing",
                }
            ]
        },
    )
    packet = {
        "packet_id": "render_prep_test",
        "title": "New York Liberty beat Las Vegas Aces",
        "asset_requirement": "Use exact local WNBA team logos from the registry; no player asset required.",
        "active_asset_stop_go": "hold_required_manual_asset_review",
    }

    active_rows = command_center.active_asset_review_queue_rows(packet)
    board_rows = command_center.manual_asset_source_board_rows(active_rows)
    intake_rows = command_center.manual_logo_verification_intake_rows(board_rows)
    league_mark_intake_rows = command_center.manual_league_mark_context_intake_rows(board_rows)
    summary = command_center.decision_stop_go_summary(packet, active_rows, board_rows)
    active_md = command_center.render_active_asset_review_queue(packet, active_rows)
    board_md = command_center.render_manual_asset_source_board(packet, board_rows)
    intake_md = command_center.render_manual_logo_verification_intake(packet, intake_rows)
    league_intake_md = command_center.render_manual_league_mark_context_intake(packet, league_mark_intake_rows)
    html = (
        command_center.render_decision_stop_go_summary_panel(summary)
        + command_center.render_manual_asset_source_board_panel(board_rows)
        + command_center.render_manual_logo_verification_intake_panel(intake_rows)
        + command_center.render_manual_league_mark_context_intake_panel(league_mark_intake_rows)
    )

    liberty_queue = next(row for row in active_rows if row["entity_name"] == "New York Liberty")
    assert liberty_queue["evidence_gap_status"] == "present_unapproved_legacy_source_review"
    assert liberty_queue["local_asset_state"] == "present_but_unapproved"
    assert liberty_queue["official_source_candidate"] == "https://liberty.wnba.com/"
    assert liberty_queue["current_registry_source"] == "https://upload.wikimedia.org/new-york-liberty-logo.png"
    assert "human-edited manual approval" in liberty_queue["cannot_clear_automatically_because"]
    wnba_queue = next(row for row in active_rows if row["entity_name"] == "WNBA")
    assert wnba_queue["selected_template_blocking_status"] == "not_blocking_selected_template_league_mark_not_required"
    assert wnba_queue["local_asset_state"] == "missing_or_unregistered"
    assert wnba_queue["official_source_candidate"] == "https://www.wnba.com/"
    assert wnba_queue["evidence_gap_status"] == "official_source_needed_review_only"
    assert wnba_queue["operator_copy_target"] == "data/asset_registry/wnba/wnba_league_mark_review_intake.csv"
    assert wnba_queue["primary_action"] == "fill_league_mark_context_intake_or_mark_not_required_for_selected_template"
    assert "mark_not_required_for_selected_template" in wnba_queue["allowed_decisions"]
    assert "league-mark context only" in wnba_queue["cannot_clear_automatically_because"]
    assert "New York Liberty: present_unapproved_legacy_source_review" in summary["selected_template_evidence_gaps"]
    assert "WNBA: official_source_needed_review_only" in summary["league_mark_evidence_gaps"]
    assert "Cannot clear automatically because: New York Liberty is selected-template blocking" in active_md
    assert "Evidence gap status: `present_unapproved_legacy_source_review`" in board_md
    assert "Current registry source: https://upload.wikimedia.org/new-york-liberty-logo.png" in board_md
    assert "Operator copy target: `data/asset_registry/wnba/wnba_league_mark_review_intake.csv`" in board_md
    assert len(intake_rows) == 1
    liberty_intake = intake_rows[0]
    assert liberty_intake["entity_name"] == "New York Liberty"
    assert liberty_intake["local_logo_path"] == "assets/leagues/wnba/teams/new_york_liberty/logo.png"
    assert liberty_intake["official_source_candidate"] == "https://liberty.wnba.com/"
    assert liberty_intake["current_legacy_registry_source"] == "https://upload.wikimedia.org/new-york-liberty-logo.png"
    assert liberty_intake["current_unapproved_status"] == "unapproved_review_required"
    assert liberty_intake["manual_intake_files"] == "data/asset_registry/wnba/team_logos.csv|data/asset_registry/wnba/logo_sources.csv"
    assert liberty_intake["approval_state_change"] == "false"
    assert liberty_intake["asset_downloads"] == "false"
    assert "Manual Logo Verification Intake Bridge" in intake_md
    assert "Human-edited manual intake files: `data/asset_registry/wnba/team_logos.csv|data/asset_registry/wnba/logo_sources.csv`" in intake_md
    assert len(league_mark_intake_rows) == 1
    wnba_intake = league_mark_intake_rows[0]
    assert wnba_intake["entity_name"] == "WNBA"
    assert wnba_intake["manual_intake_files"] == "data/asset_registry/wnba/wnba_league_mark_review_intake.csv"
    assert wnba_intake["template_requirement_rule"] == "non_blocking_until_selected_template_requires_league_mark"
    assert "mark_not_required_for_selected_template" in wnba_intake["allowed_manual_outcomes"]
    assert "Manual League-Mark Context Intake" in league_intake_md
    assert "optional/non-blocking unless the selected template explicitly requires it" in league_intake_md
    assert "Cannot clear automatically because" in html
    assert "Manual Logo Verification Intake Bridge" in html
    assert "Manual League-Mark Context Intake" in html
    assert "non-blocking unless required" in html
    assert all(row["publish_ready"] == "false" for row in active_rows)
    assert all(row["auto_approval"] == "false" for row in active_rows)
    assert all(row["asset_downloads"] == "false" for row in active_rows)
    assert all(row["publish_ready"] == "false" for row in board_rows)
    assert all(row["auto_approval"] == "false" for row in board_rows)
    assert all(row["asset_downloads"] == "false" for row in board_rows)


def test_selected_template_blocking_status_keeps_optional_league_mark_context() -> None:
    packet = {
        "asset_requirement": "Use exact local WNBA team logos from the registry; no invented identity, no text-logo fallback, no player asset required.",
    }
    league_context = command_center.selected_template_blocking_status(packet, {"asset_domain": "league_logo"})
    assert league_context["selected_template_blocking_status"] == "not_blocking_selected_template_league_mark_not_required"
    assert "team logo slots" in league_context["selected_template_blocking_reason"]

    league_required = command_center.selected_template_blocking_status({"asset_requirement": "league mark required"}, {"asset_domain": "league_logo"})
    assert league_required["selected_template_blocking_status"] == "blocking_selected_template_logo_review"


def test_command_center_generated_artifacts_point_to_current_output_when_latest_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    stale = Path("outputs/local/latest/files/render_handoff_top_packet")
    stale.mkdir(parents=True)
    (stale / "active_asset_review_queue.md").write_text("stale queue", encoding="utf-8")
    (stale / "active_asset_review_queue.csv").write_text("stale,queue\n", encoding="utf-8")
    (stale / "manual_asset_source_board.md").write_text("stale source board", encoding="utf-8")
    (stale / "manual_asset_source_board.csv").write_text("stale,source\n", encoding="utf-8")
    (stale / "manual_logo_verification_intake.md").write_text("stale logo intake", encoding="utf-8")
    (stale / "manual_logo_verification_intake.csv").write_text("stale,logo\n", encoding="utf-8")
    (stale / "manual_league_mark_context_intake.md").write_text("stale league mark intake", encoding="utf-8")
    (stale / "manual_league_mark_context_intake.csv").write_text("stale,league\n", encoding="utf-8")

    by_path = {row["path"]: row for row in command_center.artifact_entries()}

    md_artifact = by_path["render_handoff_top_packet/active_asset_review_queue.md"]
    csv_artifact = by_path["render_handoff_top_packet/active_asset_review_queue.csv"]
    board_md_artifact = by_path["render_handoff_top_packet/manual_asset_source_board.md"]
    board_csv_artifact = by_path["render_handoff_top_packet/manual_asset_source_board.csv"]
    intake_md_artifact = by_path["render_handoff_top_packet/manual_logo_verification_intake.md"]
    intake_csv_artifact = by_path["render_handoff_top_packet/manual_logo_verification_intake.csv"]
    league_md_artifact = by_path["render_handoff_top_packet/manual_league_mark_context_intake.md"]
    league_csv_artifact = by_path["render_handoff_top_packet/manual_league_mark_context_intake.csv"]
    assert md_artifact["status_detail"] == "Created with this command center run"
    assert csv_artifact["status_detail"] == "Created with this command center run"
    assert board_md_artifact["status_detail"] == "Created with this command center run"
    assert board_csv_artifact["status_detail"] == "Created with this command center run"
    assert intake_md_artifact["status_detail"] == "Created with this command center run"
    assert intake_csv_artifact["status_detail"] == "Created with this command center run"
    assert league_md_artifact["status_detail"] == "Created with this command center run"
    assert league_csv_artifact["status_detail"] == "Created with this command center run"
    assert md_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/active_asset_review_queue.md").as_posix()
    assert csv_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/active_asset_review_queue.csv").as_posix()
    assert board_md_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/manual_asset_source_board.md").as_posix()
    assert board_csv_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/manual_asset_source_board.csv").as_posix()
    assert intake_md_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/manual_logo_verification_intake.md").as_posix()
    assert intake_csv_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/manual_logo_verification_intake.csv").as_posix()
    assert league_md_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/manual_league_mark_context_intake.md").as_posix()
    assert league_csv_artifact["source_path"] == command_center.output_path("render_handoff_top_packet/manual_league_mark_context_intake.csv").as_posix()
    assert "latest" not in md_artifact["source_path"]


DECISION_FIELDS = [
    "decision_draft_id",
    "source_intake_id",
    "preview_path",
    "qa_status",
    "automated_hold_count",
    "allowed_decisions",
    "operator_decision",
    "operator_notes",
    "hold_reason",
    "revision_request",
    "operator_name",
    "reviewed_at_local",
    "required_evidence",
    "copy_target",
    "copy_instructions",
    "copy_status",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]

ATHLETE_PHOTO_DECISION_FIELDS = [
    "athlete_id",
    "athlete_name",
    "team_id",
    "source_headshot_path",
    "contact_sheet_path",
    "recommended_review_variant_path",
    "allowed_decisions",
    "operator_decision",
    "identity_verified",
    "crop_choice",
    "operator_notes",
    "approval_scope",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]


def write_csv_with_fields(path: str, rows: list[dict[str, str]], fields: list[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def seed_athlete_photo_onboarding_files() -> None:
    source = Path("assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png")
    marker = Path(source.as_posix() + ".approved")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"fake breanna headshot")
    marker.write_text(json.dumps({"approved_at_utc": "2026-06-25T00:00:00+00:00"}), encoding="utf-8")
    onboarding = Path("athlete_photo_onboarding")
    variant = onboarding / "variants" / "new_york_liberty" / "new_york_liberty_breanna_stewart__photo_first_feed.png"
    story = onboarding / "variants" / "new_york_liberty" / "new_york_liberty_breanna_stewart__photo_first_story.png"
    square = onboarding / "variants" / "new_york_liberty" / "new_york_liberty_breanna_stewart__compact_square.png"
    sheet = onboarding / "contact_sheets" / "new_york_liberty_contact_sheet.jpg"
    for path in [variant, story, square, sheet]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake athlete photo review image")
    row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "athlete_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "source_headshot_path": source.as_posix(),
        "source_approval_marker_path": marker.as_posix(),
        "source_approved_at_utc": "2026-06-25T00:00:00+00:00",
        "source_evidence": "approved_assets_registry",
        "feed_variant_path": variant.as_posix(),
        "story_variant_path": story.as_posix(),
        "square_variant_path": square.as_posix(),
        "recommended_review_variant_path": variant.as_posix(),
        "variant_status": "review_variant_ready",
        "crop_readiness_score": "100",
        "crop_readiness_notes": "Review crop generated; identity still requires human review.",
        "contact_sheet_path": sheet.as_posix(),
        "renderer_review_candidate": "true",
        "approval_scope": "review_only_derivative_from_approved_headshot",
        "review_only_policy": "derived_variant_does_not_approve_move_publish_or_mark_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    metadata_fields = list(row.keys())
    write_csv_with_fields((onboarding / "athlete_photo_onboarding_metadata.csv").as_posix(), [row], metadata_fields)
    write_json(
        (onboarding / "athlete_photo_onboarding_metadata.json").as_posix(),
        {
            "report": {"status": "review_only_onboarding_ready"},
            "athletes": {"new_york_liberty_breanna_stewart": row},
        },
    )
    write_csv_with_fields(
        (onboarding / "athlete_photo_onboarding_decision_template.csv").as_posix(),
        [{
            "athlete_id": "new_york_liberty_breanna_stewart",
            "athlete_name": "Breanna Stewart",
            "team_id": "new_york_liberty",
            "source_headshot_path": source.as_posix(),
            "contact_sheet_path": sheet.as_posix(),
            "recommended_review_variant_path": variant.as_posix(),
            "allowed_decisions": "approve_variant_for_review_drafts|hold|revise_crop",
            "operator_decision": "",
            "identity_verified": "",
            "crop_choice": "",
            "operator_notes": "",
            "approval_scope": "review_only_derivative_from_approved_headshot",
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
        }],
        ATHLETE_PHOTO_DECISION_FIELDS,
    )
    write_json(
        (onboarding / "athlete_photo_onboarding_manifest.json").as_posix(),
        {
            "status": "review_only_onboarding_ready",
            "source_rows": 1,
            "review_variant_ready": 1,
            "review_variant_needs_crop_review": 0,
            "contact_sheets": 1,
            "policy": {"auto_approval": False, "auto_publish": False, "move_files": False, "paid_apis": False},
        },
    )
    (onboarding / "athlete_photo_onboarding_report.md").write_text("# Athlete Photo Onboarding\n", encoding="utf-8")
    (onboarding / "athlete_photo_contact_sheet_index.md").write_text("# Contact Sheets\n", encoding="utf-8")

    audit_dir = Path("data/asset_registry/wnba")
    audit_dir.mkdir(parents=True, exist_ok=True)
    contact_sheet_dir = audit_dir / "athlete_photo_contact_sheets"
    contact_sheet_dir.mkdir(parents=True, exist_ok=True)
    (contact_sheet_dir / "new_york_liberty.png").write_bytes(b"fake team athlete contact sheet")
    (contact_sheet_dir / "new_york_liberty.md").write_text("# New York Liberty Athlete Photo Contact Sheet\n", encoding="utf-8")
    athlete_contact_row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "athlete_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "team_name": "New York Liberty",
        "conference": "Eastern",
        "local_headshot_path": source.as_posix(),
        "local_headshot_exists": "true",
        "approved_marker_path": marker.as_posix(),
        "approved_marker_exists": "true",
        "current_approval_status": "approved_marker_present_manual_source_recheck_required",
        "identity_review_status": "hold_identity_review_required",
        "provider_player_id": "1627668",
        "official_roster_page_candidate": "https://liberty.wnba.com/roster",
        "official_player_profile_candidate": "https://www.wnba.com/player/1627668/breanna-stewart",
        "official_roster_photo_candidate_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/1627668.png",
        "source_evidence": "approved marker decision_source=default",
        "crop_readiness_notes": "default_decision_source_manual_recheck_required",
        "allowed_decisions": "approve_for_review_only_renderer_use|hold_identity|revise_asset|revise_source_metadata",
        "human_intake_file": "data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv",
        "team_contact_sheet_path": "data/asset_registry/wnba/athlete_photo_contact_sheets/new_york_liberty.png",
        "team_review_board_path": "data/asset_registry/wnba/athlete_photo_contact_sheets/new_york_liberty.md",
        "review_only": "true",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "asset_downloads": "false",
    }
    write_csv_with_fields((audit_dir / "wnba_athlete_photo_contact_sheet.csv").as_posix(), [athlete_contact_row], list(athlete_contact_row.keys()))
    intake_row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "athlete_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "team_name": "New York Liberty",
        "local_headshot_path": source.as_posix(),
        "approved_marker_path": marker.as_posix(),
        "provider_player_id": "1627668",
        "official_roster_page_candidate": "https://liberty.wnba.com/roster",
        "official_player_profile_candidate": "https://www.wnba.com/player/1627668/breanna-stewart",
        "official_roster_photo_candidate_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/1627668.png",
        "current_approval_status": "approved_marker_present_manual_source_recheck_required",
        "identity_review_status": "hold_identity_review_required",
        "allowed_decisions": "approve_for_review_only_renderer_use|hold_identity|revise_asset|revise_source_metadata",
        "operator_decision": "operator_fill_required",
        "identity_verified": "operator_fill_required",
        "source_reviewed": "operator_fill_required",
        "local_file_reviewed": "operator_fill_required",
        "source_url_to_record": "",
        "provider_player_id_verified": "",
        "registry_action": "",
        "operator_notes": "",
        "reviewed_by": "",
        "reviewed_at_local": "",
        "approval_scope": "review_only_renderer_athlete_photo_trust_manual_intake",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "asset_downloads": "false",
    }
    write_csv_with_fields((audit_dir / "wnba_athlete_photo_review_intake.csv").as_posix(), [intake_row], list(intake_row.keys()))
    (audit_dir / "wnba_athlete_photo_contact_sheet_index.md").write_text("# WNBA Athlete Photo Contact Sheets\n", encoding="utf-8")
    write_json(
        (audit_dir / "wnba_athlete_photo_contact_sheet_manifest.json").as_posix(),
        {
            "status": "contact_sheets_ready",
            "athlete_rows": 1,
            "team_rows": 1,
            "local_headshots_present": 1,
            "review_only": True,
            "guardrails": {
                "publish_ready": False,
                "auto_approval": False,
                "auto_publish": False,
                "move_files": False,
                "paid_apis": False,
                "asset_downloads": False,
                "publishing": False,
            },
        },
    )
    issue = {
        "severity": "high",
        "issue_code": "approved_asset_still_has_pending_match_review",
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "provider_player_id": "1627668",
        "asset_path": source.as_posix(),
        "approved_marker_path": marker.as_posix(),
        "evidence": "match_review status=needs_human_approval; confidence=0.72",
        "recommendation": "Keep a per-athlete review note or decision row that closes the pending match-review state.",
        "review_only_policy": "audit_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
    }
    write_csv_with_fields((audit_dir / "athlete_identity_audit.csv").as_posix(), [issue], list(issue.keys()))
    write_json(
        (audit_dir / "athlete_identity_audit.json").as_posix(),
        {
            "report": {
                "status": "needs_identity_review",
                "issue_rows": 1,
                "severity_counts": {"high": 1},
            },
            "issues": [issue],
        },
    )
    packet = {
        "review_packet_id": "new_york_liberty_breanna_stewart",
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "provider_player_id": "1627668",
        "asset_path": source.as_posix(),
        "approved_marker_path": marker.as_posix(),
        "identity_review_status": "hold_identity_review_required",
        "review_required": "true",
        "identity_hold": "true",
        "default_approval_present": "true",
        "highest_severity": "high",
        "issue_count": "1",
        "hold_reason_codes": "approved_asset_still_has_pending_match_review|default_approval_requires_identity_recheck",
        "focused_evidence": "approved marker decision_source=default",
        "source_check_url": "https://www.wnba.com/player/1627668/breanna-stewart",
        "provider_player_page_hint": "https://www.wnba.com/player/1627668/breanna-stewart",
        "operator_review_steps": "open_asset_and_marker; compare_to_official_player_or_team_source; choose_hold_or_verified_review_only_decision",
        "allowed_decisions": "hold_identity|revise_asset|backfill_provider_id_only|identity_verified_approved_for_review_renders",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "review_only_policy": "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
    }
    write_csv_with_fields((audit_dir / "athlete_identity_review_packet.csv").as_posix(), [packet], list(packet.keys()))
    (audit_dir / "athlete_identity_audit.md").write_text("# WNBA Athlete Identity Audit\n", encoding="utf-8")


def seed_asset_availability_audit_files() -> None:
    registry_dir = Path("data/asset_registry")
    wnba_dir = registry_dir / "wnba"
    registry_dir.mkdir(parents=True, exist_ok=True)
    wnba_dir.mkdir(parents=True, exist_ok=True)
    findings = [
        {
            "severity": "warning",
            "asset_domain": "player_photo",
            "asset_kind": "headshot",
            "entity_type": "athlete",
            "entity_id": "new_york_liberty_breanna_stewart",
            "entity_name": "Breanna Stewart",
            "league": "WNBA",
            "finding": "suspicious_or_default_player_approval",
            "approval_status": "approved",
            "format_status": "valid_raster",
            "renderer_coverage": "review_only_manual_source_recheck_required: default_decision_source_manual_recheck_required",
            "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
            "evidence": "approved_assets_registry; decision_source=default; headshot_slot_requires_identity_and_crop_review",
            "recommended_next_step": "recheck_decision_source_source_file_and_approval_timestamp",
        },
        {
            "severity": "error",
            "asset_domain": "player_photo",
            "asset_kind": "cutout",
            "entity_type": "athlete",
            "entity_id": "new_york_liberty_breanna_stewart",
            "entity_name": "Breanna Stewart",
            "league": "WNBA",
            "finding": "missing_local_player_asset",
            "approval_status": "missing",
            "format_status": "missing_file",
            "renderer_coverage": "review_only_not_renderable_until_approved",
            "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/cutout.png",
            "evidence": "asset_file_missing; cutout_slot_requires_manual_crop_review",
            "recommended_next_step": "keep_photo_slot_disabled_until_asset_and_marker_are_reviewed",
        },
        {
            "severity": "warning",
            "asset_domain": "team_logo",
            "asset_kind": "primary_logo",
            "entity_type": "team",
            "entity_id": "new_york_liberty",
            "entity_name": "New York Liberty",
            "league": "WNBA",
            "finding": "logo_present_without_complete_approval",
            "approval_status": "review_required",
            "format_status": "valid_raster",
            "renderer_coverage": "available_review_only",
            "asset_path": "assets/leagues/wnba/logos/new_york_liberty/logo.png",
            "evidence": "approved logo marker missing; source review note pending",
            "recommended_next_step": "verify logo source, marker, and format before render trust",
        },
        {
            "severity": "error",
            "asset_domain": "league_logo",
            "asset_kind": "league_mark",
            "entity_type": "league",
            "entity_id": "wnba",
            "entity_name": "WNBA",
            "league": "WNBA",
            "finding": "missing_or_unregistered_logo_asset",
            "review_packet_id": "asset_review_0605_league_logo_WNBA",
            "decision_lane": "wnba_logo_review",
            "default_operator_decision": "hold_league_mark",
            "source_confidence": "source_missing_or_unregistered",
            "manual_approval_status": "manual_review_required",
            "asset_readiness": "optional_league_logo_file_missing_review_only",
            "allowed_operator_decisions": "verify_logo_for_review_renders|hold_logo_slot|revise_logo_source_metadata",
            "decision_primary_action": "supply_exact_local_logo_and_manual_registry_review",
            "manual_review_packet": "data/asset_registry/wnba/logo_review_catalog_report.md",
            "operator_copy_target": "operator/assets/brand_logos/README.md",
            "blocker_summary": "WNBA: missing league mark; default decision=hold_league_mark; readiness=optional_league_logo_file_missing_review_only",
            "approval_status": "missing",
            "format_status": "missing_file",
            "renderer_coverage": "review_only_not_renderable_until_approved",
            "asset_path": "assets/leagues/wnba/logos/league/wnba.png",
            "evidence": "league mark missing from local approved catalog",
            "recommended_next_step": "hold league logo slot until a local approved mark is registered",
        },
        {
            "severity": "info",
            "asset_domain": "renderer",
            "asset_kind": "fallback_guard",
            "entity_type": "renderer",
            "entity_id": "manual_review_renderer",
            "entity_name": "Manual review renderer",
            "league": "WNBA",
            "finding": "renderer_logo_audit_missing",
            "approval_status": "review_required",
            "format_status": "not_applicable",
            "renderer_coverage": "fallback_requires_operator_review",
            "renderer_fallback_cue": "HSD team badges are review-only stand-ins for missing or undecodable exact logos; they do not approve logo identity or create a publish-ready lane.",
            "asset_path": "generate_hsd_manual_review_renderer_v1.py",
            "evidence": "renderer fallback coverage audit not refreshed",
            "recommended_next_step": "rerun asset-audit and renderer QA before trusting fallback visuals",
        },
    ]
    write_json(
        (registry_dir / "asset_availability_audit.json").as_posix(),
        {
            "status": "review_required",
            "review_only": True,
            "generated_at_utc": "2026-06-25T12:00:00+00:00",
            "finding_count": len(findings),
            "severity_counts": {"error": 2, "warning": 2, "info": 1},
            "asset_domain_counts": {"player_photo": 2, "team_logo": 1, "league_logo": 1, "renderer": 1},
            "finding_counts": {
                "suspicious_or_default_player_approval": 1,
                "missing_local_player_asset": 1,
                "logo_present_without_complete_approval": 1,
                "missing_or_unregistered_logo_asset": 1,
                "renderer_logo_audit_missing": 1,
            },
            "policy": {
                "no_paid_apis": True,
                "no_asset_downloads": True,
                "no_auto_approval": True,
                "no_file_movement_into_publish_ready_lanes": True,
                "no_publishing": True,
            },
            "findings": findings,
        },
    )
    (registry_dir / "asset_availability_audit.md").write_text("# Asset Availability Audit\n", encoding="utf-8")
    write_csv_with_fields((registry_dir / "asset_availability_audit.csv").as_posix(), findings, list(findings[0].keys()))
    (registry_dir / "logo_asset_catalog.md").write_text("# Logo Asset Catalog\n", encoding="utf-8")
    (wnba_dir / "athlete_photo_catalog.md").write_text("# WNBA Athlete Photo Catalog\n", encoding="utf-8")
    (wnba_dir / "logo_review_catalog_report.md").write_text("# WNBA Logo Review Catalog\n", encoding="utf-8")
    logo_packet = {
        "packet_id": "logo_packet_new_york_liberty_unapproved",
        "decision_packet_title": "WNBA logo review: New York Liberty",
        "team_id": "new_york_liberty",
        "team_name": "New York Liberty",
        "issue_type": "unapproved_required_logo",
        "decision_review_status": "operator_logo_review_required",
        "source_url": "https://example.test/liberty-logo.png",
        "registered_path": "assets/leagues/wnba/logos/new_york_liberty/logo.png",
        "source_target_path": "assets/leagues/wnba/teams/new_york_liberty/logo.svg",
        "primary_action": "Review exact local logo source evidence before renderer trust.",
        "hold_cue": "Hold the logo slot until source and local file are manually checked.",
        "revise_cue": "Revise registry metadata only after human evidence review.",
        "renderer_fallback_cue": "Renderer fallback remains review-only while logo trust is held.",
        "allowed_decisions": "verify_logo_for_review_renders|hold_logo_slot|revise_logo_source_metadata",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    write_csv_with_fields((wnba_dir / "logo_review_packets.csv").as_posix(), [logo_packet], list(logo_packet.keys()))


def write_identity_resolution_inbox(**overrides: str) -> None:
    row = {
        "athlete_id": "new_york_liberty_breanna_stewart",
        "display_name": "Breanna Stewart",
        "team_id": "new_york_liberty",
        "provider_player_id": "1627668",
        "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
        "approved_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
        "highest_severity": "high",
        "issue_count": "1",
        "issue_codes": "approved_asset_still_has_pending_match_review",
        "audit_evidence": "match_review status=needs_human_approval; confidence=0.72",
        "recommended_operator_action": "verify_identity_and_backfill_provider_id_if_source_supported",
        "allowed_decisions": "identity_verified_approved_for_review_renders|hold_identity|revise_asset|backfill_provider_id_only",
        "operator_decision": "identity_verified_approved_for_review_renders",
        "identity_verified": "yes",
        "provider_player_id_verified": "yes",
        "approved_source_url": "https://www.wnba.com/player/1627668/breanna-stewart",
        "secondary_source_url": "https://liberty.wnba.com/roster/",
        "backfill_provider_player_id": "",
        "operator_notes": "Verified Breanna Stewart by official public source for review-only render eligibility.",
        "operator_name": "Test Operator",
        "reviewed_at_local": "2026-06-25T12:00:00",
        "issue_resolution_status": "identity_verified",
        "copy_target": "operator/inbox/wnba_athlete_identity_resolution.csv",
        "approval_scope": "review_only_identity_resolution_for_local_draft_renders",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "review_only_policy": "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
    }
    row.update(overrides)
    write_csv_with_fields("operator/inbox/wnba_athlete_identity_resolution.csv", [row], command_center.IDENTITY_RESOLUTION_FIELDS)


def seed_manual_visual_qa_decision_files() -> None:
    preview = Path("render_handoff_top_packet/draft_preview.png")
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_bytes(b"fake png for operator decision panel")
    review_drafts = preview.parent / "review_drafts"
    review_drafts.mkdir(parents=True, exist_ok=True)
    feed_preview = review_drafts / "draft_preview_ig_feed.png"
    story_preview = review_drafts / "draft_preview_story.png"
    square_preview = review_drafts / "draft_preview_square.png"
    for render_file in [feed_preview, story_preview, square_preview]:
        render_file.write_bytes(b"fake social render draft")
    reference_public = Path("assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/01_game_recap_final_score_variant_A_public.png")
    reference_layout = Path("assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/02_game_recap_final_score_variant_A_layout_reference.png")
    reference_story_public = Path("assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/05_game_recap_final_score_variant_C_story_public.png")
    reference_story_layout = Path("assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/06_game_recap_final_score_variant_C_story_layout_reference.png")
    for reference_file in [reference_public, reference_layout, reference_story_public, reference_story_layout]:
        reference_file.parent.mkdir(parents=True, exist_ok=True)
        reference_file.write_bytes(b"fake reference image")
    write_json(
        "manual_review_renderer_manifest.json",
        {
            "status": "draft_preview_created",
            "preview_path": preview.as_posix(),
            "source_artifact": "news_fact_packets.csv",
            "source_cue": "source_confidence_ready",
            "copy_context": "4 source(s); publish_grade.",
            "content_module": {
                "content_module_mode": "verified_player_stats",
                "content_module_status": "verified_player_stat_module",
                "content_module_title": "STEWART: 20 PTS",
                "content_module_body": "Breanna Stewart (LIBERTY): 20 PTS, 6 REB, 4 AST.",
                "content_module_stat_count": "3",
                "content_module_player": "Breanna Stewart",
                "content_module_source_text": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4",
                "athlete_photo_status": "approved_local_headshot",
                "athlete_photo_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
                "athlete_photo_approval_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
                "athlete_photo_approval_cue": "APPROVED PHOTO",
                "athlete_photo_review_required": "false",
                "stat_source_confidence": "verified_stat_text_ready_manual_crosscheck_required",
                "stat_source_label": "Verified player/stat text available",
                "stat_review_cue": "Confirm the named performer and stat line against source proof before approval.",
                "editorial_microcopy_headline": "STEWART + CLEAR SEPARATION",
                "editorial_microcopy_body": "Stewart's verified 20 PTS, 6 REB, 4 AST frames the clear separation.",
                "editorial_microcopy_review_cue": "Copy is score/stat-derived only; verify source proof before adding why/how claims.",
            },
            "format_options": [
                {
                    "format_id": "ig_feed_4x5",
                    "path": feed_preview.as_posix(),
                    "width": 1080,
                    "height": 1350,
                    "primary": True,
                    "review_only": True,
                    "publish_ready": False,
                    "reference_template_id": "hsd_game_recap_final_score_a",
                    "reference_exact_format_match": True,
                    "reference_derivation": "exact_imported_reference_spec",
                    "reference_public_mockup_path": reference_public.as_posix(),
                    "reference_layout_path": reference_layout.as_posix(),
                    "athlete_photo_layout_mode": "photo_first_final_score",
                    "athlete_photo_layout_status": "approved_photo_first_template",
                    "athlete_photo_layout_detail": "Approved local headshot becomes the main editorial visual with score lanes and verified stat modules kept review-only.",
                },
                {
                    "format_id": "ig_story_9x16",
                    "path": story_preview.as_posix(),
                    "width": 1080,
                    "height": 1920,
                    "primary": False,
                    "review_only": True,
                    "publish_ready": False,
                    "reference_template_id": "hsd_game_recap_final_score_c_story",
                    "reference_exact_format_match": True,
                    "reference_derivation": "exact_imported_reference_spec",
                    "reference_public_mockup_path": reference_story_public.as_posix(),
                    "reference_layout_path": reference_story_layout.as_posix(),
                    "athlete_photo_layout_mode": "photo_first_final_score",
                    "athlete_photo_layout_status": "approved_photo_first_template",
                    "athlete_photo_layout_detail": "Approved local headshot becomes the main editorial visual with score lanes and verified stat modules kept review-only.",
                },
                {
                    "format_id": "square_feed_1x1",
                    "path": square_preview.as_posix(),
                    "width": 1080,
                    "height": 1080,
                    "primary": False,
                    "review_only": True,
                    "publish_ready": False,
                    "reference_template_id": "hsd_game_recap_final_score_a",
                    "reference_exact_format_match": False,
                    "reference_derivation": "square_review_draft_derived_from_imported_4x5_layout",
                    "reference_public_mockup_path": reference_public.as_posix(),
                    "reference_layout_path": reference_layout.as_posix(),
                    "athlete_photo_layout_mode": "compact_headshot_chip",
                    "athlete_photo_layout_status": "approved_photo_compact_layout",
                    "athlete_photo_layout_detail": "Approved local headshot uses a compact chip to preserve the square score layout.",
                },
            ],
            "asset_slots": [
                {
                    "slot_id": "primary_photo",
                    "status": "approved_local_headshot",
                    "requirement": "Use only approved local athlete headshot/cutout assets; missing or unapproved images stay review-only fallbacks.",
                    "asset_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png",
                    "approval_marker_path": "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved",
                    "player": "Breanna Stewart",
                    "photo_approval_cue": "APPROVED PHOTO",
                    "photo_review_required": "false",
                },
                {
                    "slot_id": "source_evidence",
                    "status": "manual_review_required",
                    "requirement": "news_fact_packets.csv",
                },
                {
                    "slot_id": "primary_team_logo",
                    "status": "registry_logo_review_required",
                    "team": "New York Liberty",
                    "team_accent_hex": "#247CA8",
                    "team_accent_source": "sampled_from_local_logo_review_asset",
                    "logo_approval_cue": "LOGO REVIEW",
                    "logo_review_required": "true",
                    "requirement": "Human review must confirm this logo asset before later production use.",
                },
                {
                    "slot_id": "secondary_team_logo",
                    "status": "approved_logo",
                    "team": "Las Vegas Aces",
                    "team_accent_hex": "#C62838",
                    "team_accent_source": "sampled_from_local_logo_review_asset",
                    "logo_approval_cue": "APPROVED LOGO",
                    "logo_review_required": "false",
                    "requirement": "Approved WNBA logo slot.",
                },
            ],
            "guardrails": {"manual_only": True, "review_only": True, "auto_publish": False, "approved": False, "paid_apis": False},
        },
    )
    write_json(
        "render_visual_delta_manifest.json",
        {
            "status": "visual_delta_review_ready",
            "approval_status": "not_approved_human_review_required",
            "summary": {"comparison_count": 6, "warning_count": 1, "human_decision_required": True},
            "format_summaries": {
                "ig_feed_4x5": {
                    "format_id": "ig_feed_4x5",
                    "drift_band": "aligned_to_reference",
                    "comparison_status": "reference_aligned_review",
                    "reference_visual_delta_score": "92",
                    "worst_zone": "score_lane",
                    "warning_count": 0,
                    "warning_summary": "Reference comparison aligned enough for human review.",
                    "next_step": "Reference comparison looks aligned enough for human visual review; still not approved.",
                },
                "ig_story_9x16": {
                    "format_id": "ig_story_9x16",
                    "drift_band": "review_minor_drift",
                    "comparison_status": "manual_review_warning",
                    "reference_visual_delta_score": "84",
                    "worst_zone": "lower_modules",
                    "warning_count": 1,
                    "warning_summary": "layout: review_minor_drift (lower_modules)",
                    "next_step": "Compare draft, public mockup, and layout reference by eye before recording a manual decision.",
                },
                "square_feed_1x1": {
                    "format_id": "square_feed_1x1",
                    "drift_band": "manual_drift_warning",
                    "comparison_status": "manual_review_warning",
                    "reference_visual_delta_score": "73",
                    "worst_zone": "score_lane",
                    "warning_count": 1,
                    "warning_summary": "public_mockup: manual_drift_warning (score_lane)",
                    "next_step": "Hold or revise if the highlighted zones drift from the approved template intent.",
                },
            },
            "guardrails": {
                "manual_only": True,
                "review_only": True,
                "auto_approval": False,
                "auto_publish": False,
                "move_files": False,
                "publish_ready": False,
                "paid_apis": False,
            },
        },
    )
    Path("render_visual_delta_report.md").write_text("# Render visual delta\n", encoding="utf-8")
    write_csv(
        "render_visual_delta.csv",
        [
            {
                "format_id": "ig_feed_4x5",
                "reference_kind": "public_mockup",
                "drift_band": "aligned_to_reference",
                "reference_visual_delta_score": "92",
            }
        ],
    )
    write_json(
        "render_visual_revision_plan.json",
        {
            "status": "manual_revision_plan_ready",
            "approval_status": "not_approved_human_review_required",
            "summary": {
                "revision_count": 3,
                "revise_before_manual_next_step_count": 1,
                "inspect_before_decision_count": 1,
                "human_decision_required": True,
            },
            "revision_rows": [
                {
                    "format_id": "ig_feed_4x5",
                    "revision_priority": "reference_check_only",
                    "revision_status": "manual_reference_check",
                    "reference_visual_delta_score": "92",
                    "drift_band": "aligned_to_reference",
                    "worst_zone": "score_lane",
                    "revision_focus": "Score/team lane balance",
                    "specific_manual_revisions": "Confirm score lane against layout reference before deciding.",
                    "inspect_first": "Open draft, public mockup, and layout reference.",
                    "hold_or_revise_cue": "Open references and confirm by eye; no automated approval is implied.",
                    "approval_policy": "review-only manual guidance; does not approve, publish, move files, or mark publish-ready",
                },
                {
                    "format_id": "ig_story_9x16",
                    "revision_priority": "inspect_before_decision",
                    "revision_status": "manual_inspection_recommended",
                    "reference_visual_delta_score": "84",
                    "drift_band": "review_minor_drift",
                    "worst_zone": "lower_modules",
                    "revision_focus": "Lower module rhythm",
                    "specific_manual_revisions": "Compress lower module copy and check spacing.",
                    "inspect_first": "Open draft, public mockup, and layout reference.",
                    "hold_or_revise_cue": "Inspect the named zone before choosing approve, hold, or revise.",
                    "approval_policy": "review-only manual guidance; does not approve, publish, move files, or mark publish-ready",
                },
                {
                    "format_id": "square_feed_1x1",
                    "revision_priority": "revise_before_manual_next_step",
                    "revision_status": "manual_revision_recommended",
                    "reference_visual_delta_score": "73",
                    "drift_band": "manual_drift_warning",
                    "worst_zone": "score_lane",
                    "revision_focus": "Score/team lane balance",
                    "specific_manual_revisions": "Rebalance logo, team name, and score columns before deciding.",
                    "inspect_first": "Open draft, public mockup, and layout reference.",
                    "hold_or_revise_cue": "Hold or revise this draft if the named zone visibly drifts from the reference.",
                    "approval_policy": "review-only manual guidance; does not approve, publish, move files, or mark publish-ready",
                },
            ],
            "guardrails": {
                "manual_only": True,
                "review_only": True,
                "auto_approval": False,
                "auto_publish": False,
                "move_files": False,
                "publish_ready": False,
                "paid_apis": False,
            },
        },
    )
    Path("render_visual_revision_plan.md").write_text("# Render visual revision plan\n", encoding="utf-8")
    write_csv(
        "render_visual_revision_plan.csv",
        [
            {
                "format_id": "ig_feed_4x5",
                "revision_priority": "reference_check_only",
                "revision_focus": "Score/team lane balance",
            }
        ],
    )
    write_json(
        "manual_visual_qa_manifest.json",
        {
            "status": "human_review_required",
            "approval_status": "not_approved_human_review_required",
            "dimensions": {"width": 1080, "height": 1350},
            "summary": {"check_count": 8, "pass_count": 8, "hold_count": 0, "human_decision_required": True},
            "checks": [
                {
                    "check_id": "headline_text_zone",
                    "check_label": "Title readable contrast and safe-zone fit",
                    "qa_result": "pass",
                    "passed": True,
                    "evidence": "Style=reference_white_gold_title; title ink ratio 0.127; edge contrast 0.073; fit margins top=43px bottom=70px.",
                },
                {
                    "check_id": "score_team_text_zone",
                    "check_label": "Readable text zone signal",
                    "qa_result": "pass",
                    "passed": True,
                    "evidence": "Score/team text zone has enough contrast for manual review.",
                },
                {
                    "check_id": "team_logo_review_status",
                    "check_label": "Team logo registry status",
                    "qa_result": "pass_human_review_required",
                    "passed": True,
                    "evidence": "New York Liberty: registry_logo_review_required; Las Vegas Aces: approved_logo",
                },
                {
                    "check_id": "player_ledger_readability",
                    "check_label": "Player ledger readability",
                    "qa_result": "pass",
                    "passed": True,
                    "evidence": "content_module=verified_player_stats; confidence=verified_stat_text_ready_manual_crosscheck_required; player=Breanna Stewart.",
                },
                {
                    "check_id": "approval_guardrails",
                    "check_label": "Approval and publishing guardrails",
                    "qa_result": "pass",
                    "passed": True,
                    "evidence": "manual_only=True; auto_publish_off=True; paid_apis_off=True",
                },
            ],
        },
    )
    write_json(
        "manual_visual_qa_approval_intake.json",
        {"status": "ready_for_manual_decision", "approval_status": "not_approved_operator_input_required"},
    )
    draft = {
        "decision_draft_id": "decision_draft_manual_visual_qa_preview_1",
        "source_intake_id": "manual_visual_qa_preview_1",
        "preview_path": preview.as_posix(),
        "qa_status": "human_review_required",
        "automated_hold_count": "0",
        "allowed_decisions": "approve_for_manual_next_step|hold|revise",
        "operator_decision": "operator_fill_required",
        "operator_notes": "",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "required_evidence": "Open draft_preview.png plus manual_visual_qa_report.md.",
        "copy_target": "operator/inbox/manual_visual_qa_operator_decisions.csv",
        "copy_instructions": "Copy this row only after visual review.",
        "copy_status": "ready_for_operator_fill_after_opening_preview",
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    write_csv_with_fields("manual_visual_qa_operator_decision_draft.csv", [draft], DECISION_FIELDS)
    write_json("manual_visual_qa_operator_decision_draft.json", {"status": "draft_ready_for_operator_fill"})
    template_rows = []
    for decision in ["approve_for_manual_next_step", "hold", "revise"]:
        row = dict(draft)
        row["operator_decision"] = decision
        row["template_row_type"] = f"{decision}_example_copy_then_replace_placeholders"
        row["operator_notes"] = "REPLACE_WITH_OPERATOR_NOTES"
        row["operator_name"] = "REPLACE_WITH_OPERATOR_NAME"
        row["reviewed_at_local"] = "REPLACE_WITH_LOCAL_REVIEW_TIME"
        row["copy_status"] = "template_only_not_valid_until_placeholders_replaced"
        template_rows.append(row)
    write_csv_with_fields("manual_visual_qa_operator_decision_template.csv", template_rows, DECISION_FIELDS + ["template_row_type"])
    write_json("manual_visual_qa_operator_decision_template.json", {"status": "template_ready_copy_only"})
    intake_row = {
        "intake_id": "manual_visual_qa_preview_1",
        "decision_draft_id": draft["decision_draft_id"],
        "source_intake_id": draft["source_intake_id"],
        "preview_path": draft["preview_path"],
        "qa_status": draft["qa_status"],
        "automated_hold_count": "0",
        "operator_decision": "operator_fill_required",
        "validation_status": "awaiting_operator_decision",
        "validation_issue": "Copy a draft row into operator/inbox/manual_visual_qa_operator_decisions.csv, then fill approve_for_manual_next_step, hold, or revise with notes.",
        "operator_notes": "",
        "hold_reason": "",
        "revision_request": "",
        "operator_name": "",
        "reviewed_at_local": "",
        "approval_scope": "manual_next_step_only_not_publish_ready",
        "source_decision_path": "operator/inbox/manual_visual_qa_operator_decisions.csv",
        "source_draft_path": "manual_visual_qa_operator_decision_draft.csv",
        "source_qa_report_path": "manual_visual_qa_report.md",
        "copy_to_publish_lane": "false",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }
    write_csv("manual_visual_qa_operator_decision_intake.csv", [intake_row])
    write_json("manual_visual_qa_operator_decision_intake.json", {"status": "awaiting_operator_decision", "approval_status": "not_approved_validated_decision_only"})
    write_csv(
        "manual_post_approval_render_staging.csv",
        [
            {
                "intake_id": "manual_visual_qa_preview_1",
                "preview_path": draft["preview_path"],
                "operator_decision": "operator_fill_required",
                "staging_lane": "awaiting_operator_decision",
                "qa_status": "human_review_required",
                "automated_hold_count": "0",
                "next_safe_action": "Fill one operator decision row, then rerun render.",
                "blocked_reason": "Awaiting operator decision.",
                "move_files": "false",
                "copy_to_publish_lane": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "paid_apis": "false",
            }
        ],
    )
    write_json("manual_post_approval_render_staging.json", {"status": "review_only_staging_needs_operator_action"})
    Path("manual_visual_qa_report.md").write_text("# Manual visual QA\n", encoding="utf-8")
    Path("manual_visual_qa_operator_decision_walkthrough.md").write_text("# Walkthrough\n", encoding="utf-8")
    write_json("manual_visual_qa_operator_decision_inbox_starter.json", {"status": "starter_already_ready"})
    write_csv_with_fields("operator/inbox/manual_visual_qa_operator_decisions.csv", [], DECISION_FIELDS)
    seed_athlete_photo_onboarding_files()


def seed_daily_ops_files() -> None:
    write_json(
        "operator_status.json",
        {
            "overall": "NO-GO",
            "issues": [{"severity": "critical", "code": "no_content_ready", "detail": "No ready pack."}],
        },
    )
    write_json(
        "publish_guard_report.json",
        {
            "publish_mode": "artifact_only",
            "publish_allowed": False,
            "graphics_handoff_allowed": False,
            "preview_gate_status": "PASS",
            "rendered_qa_status": "not_run",
            "issues": [{"severity": "critical", "code": "no_content_ready", "detail": "No ready pack."}],
        },
    )
    write_json(
        "results_desk_v5_manifest.json",
        {
            "counts": {"women_events": 8, "graphics_ready": 1},
            "source_health": [
                {
                    "source_name": "espn_wnba_public",
                    "sport_or_league": "WNBA",
                    "date": "20260624",
                    "ok": "Yes",
                    "events_found": 4,
                    "notes": "free public source ok",
                }
            ],
        },
    )
    write_csv(
        "news_fact_packets.csv",
        [
            {
                "urgency": "P1",
                "headline": "New York Liberty beat Las Vegas Aces",
                "production_ready": "Yes",
                "caption_hard_fact": "Verified final: New York Liberty 87, Las Vegas Aces 76.",
                "source_count": "4",
                "source_confidence_score": "92",
                "source_confidence_tier": "publish_grade",
                "source_publish_grade": "publish_grade",
                "source_confidence_reason": "Results Desk final score; multiple usable free sources",
                "top_performers": "Breanna Stewart (New York Liberty): PTS 20, REB 6, AST 4; A'ja Wilson (Las Vegas Aces): PTS 16, REB 9, AST 5",
            }
        ],
    )
    write_csv(
        "studio_bundle_queue.csv",
        [
            {
                "production_priority": "POST FIRST",
                "bundle_name": "Tonight in the W",
                "bundle_type": "wnba_preview_premium",
                "asset_shape": "1080x1350",
                "freshness_decision": "allow",
                "source_headlines": "Phoenix Mercury at Indiana Fever",
            }
        ],
    )
    Path("bebe_posting_schedule_today.md").write_text(
        "\n".join(
            [
                "## Posting schedule",
                "",
                "| Time ET | Platform | Slot | Status | Recommended action | Artifact |",
                "|---|---|---|---|---|---|",
                "| 12:00 | IG Feed | Main post 1 | needs_assets | Build the post manually. | studio_bundle_queue.csv |",
            ]
        ),
        encoding="utf-8",
    )
    Path("operator_status.md").write_text("# Operator status\n", encoding="utf-8")
    Path("publish_guard_report.md").write_text("# Publish guard\n", encoding="utf-8")
    write_json(
        "source_registry_audit.json",
        {
            "counts": {"sources": 3, "pass": 2, "review": 1, "fail": 0},
            "output_scope": "run_scoped",
            "coverage_map": [
                {
                    "coverage_key": "wnba",
                    "display_name": "WNBA",
                    "official_sources": "wnba_official_news",
                    "team_sources": "wnba_team_official_pages",
                    "wire_sources": "ap_womens_sports_wire",
                    "cross_check_sources": "espn_wnba_scoreboard_cross_check",
                    "coverage_status": "covered",
                    "coverage_gap": "none",
                    "operator_next_step": "Coverage is strong enough for normal manual review; keep monitoring existing free sources.",
                },
                {
                    "coverage_key": "pwhl",
                    "display_name": "PWHL",
                    "official_sources": "",
                    "team_sources": "",
                    "wire_sources": "ap_womens_sports_wire; reuters_sports_wire",
                    "cross_check_sources": "",
                    "coverage_status": "gap",
                    "coverage_gap": "missing official league/team source; missing scoreboard/stat/cross-check source",
                    "operator_next_step": "Add or monitor free PWHL league/team official pages before relying on wire-only hockey leads.",
                },
            ],
        },
    )
    Path("source_registry_intake_template.md").write_text(
        "# Source registry intake template\n\nRows are proposal-only and disabled by default.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_intake_template.csv",
        [
            {
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "",
                "candidate_source_name": "",
                "candidate_url": "",
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
                "review_notes": "Fill candidate fields only after checking the free public source manually.",
            }
        ],
    )
    Path("source_registry_proposal_review.md").write_text(
        "# Source proposal review\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_proposal_review.csv",
        [
            {
                "candidate_source_id": "pwhl_instagram",
                "candidate_source_name": "PWHL Instagram",
                "candidate_url": "https://www.instagram.com/thepwhlofficial/",
                "candidate_domain": "instagram.com",
                "sport_league": "PWHL",
                "source_type": "official_site",
                "tier": "official",
                "proposed_enabled": "No",
                "review_status": "hold",
                "issue_count": "1",
                "issues": "social-only source cannot be added as official/wire/cross-check registry coverage",
                "safety_flags": "social_only",
                "recommendation": "Do not add to trusted source registry until the blocking issue is resolved.",
                "registry_action": "proposal_only_do_not_import",
            },
            {
                "candidate_source_id": "pwhl_official_site",
                "candidate_source_name": "PWHL official site",
                "candidate_url": "https://www.thepwhl.com/en/",
                "candidate_domain": "thepwhl.com",
                "sport_league": "PWHL",
                "source_type": "official_site",
                "tier": "official",
                "proposed_enabled": "No",
                "review_status": "ready_for_registry_review",
                "issue_count": "0",
                "issues": "none",
                "safety_flags": "none",
                "recommendation": "Candidate may be considered for a deliberate manual registry update.",
                "registry_action": "proposal_only_do_not_import",
            },
        ],
    )
    Path("pwhl_source_proposal_pack.md").write_text(
        "# PWHL Source Proposal Pack\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    write_csv(
        "pwhl_source_proposal_pack.csv",
        [
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_group": "league_official",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "pwhl_official_news",
                "candidate_source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news; source_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official league news page.",
                "registry_presence": "not_in_registry",
                "manual_review_note": "Open and verify manually before copying into proposals.",
            },
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_group": "team_official",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "team_or_club",
                "coverage_gap": "missing team/club source",
                "candidate_source_id": "pwhl_boston_fleet_team",
                "candidate_source_name": "Boston Fleet official team page",
                "candidate_url": "https://www.thepwhl.com/en/teams/boston-fleet",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site_collection",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "team_news; roster_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official team page.",
                "registry_presence": "not_in_registry",
                "manual_review_note": "Open and verify manually before copying into proposals.",
            },
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_group": "league_cross_check",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "scoreboard_or_stats_cross_check",
                "coverage_gap": "missing scoreboard/stat/cross-check source",
                "candidate_source_id": "pwhl_official_scores",
                "candidate_source_name": "PWHL official scores",
                "candidate_url": "https://www.thepwhl.com/en/scores",
                "candidate_domain": "thepwhl.com",
                "source_type": "scoreboard_site",
                "tier": "stats_provider",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "cross_check; scores; schedules",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official scores page.",
                "registry_presence": "not_in_registry",
                "manual_review_note": "Open and verify manually before copying into proposals.",
            },
        ],
    )
    Path("source_proposal_packs.md").write_text(
        "# HSD Guided Source Proposal Packs\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    Path("source_proposal_pack_readiness.md").write_text(
        "# HSD Guided Source Proposal Pack Readiness\n\nNo rows are imported automatically.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_proposal_pack_readiness.csv",
        [
            {
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "display_name": "PWHL",
                "readiness_status": "ready_for_registry_proposal",
                "readiness_label": "Ready for proposal review",
                "candidate_rows": "3",
                "official_candidates": "2",
                "cross_check_candidates": "1",
                "duplicate_candidates": "0",
                "freshness_check_candidates": "3",
                "ready_candidates": "3",
                "coverage_status": "gap",
                "coverage_gap": "missing official league/team source",
                "review_cues": "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected.",
                "next_step": "Open top candidates manually for freshness, then copy selected rows into operator/inbox/source_registry_proposals.csv for deliberate review.",
                "top_candidate_ids": "pwhl_official_news; pwhl_boston_fleet_team; pwhl_official_scores",
                "duplicate_candidate_ids": "",
                "output_csv": "pwhl_source_proposal_pack.csv",
                "output_md": "pwhl_source_proposal_pack.md",
            },
            {
                "pack_key": "wnba",
                "pack_name": "WNBA Source Proposal Pack",
                "display_name": "WNBA",
                "readiness_status": "needs_duplicate_review",
                "readiness_label": "Duplicate review",
                "candidate_rows": "13",
                "official_candidates": "8",
                "cross_check_candidates": "5",
                "duplicate_candidates": "1",
                "freshness_check_candidates": "12",
                "ready_candidates": "12",
                "coverage_status": "watch",
                "coverage_gap": "review official league/team source depth",
                "review_cues": "1 candidate already resembles trusted registry coverage.",
                "next_step": "Review duplicate source IDs, URLs, or domains before copying any pack rows into manual proposals.",
                "top_candidate_ids": "wnba_official_home_review; wnba_official_news_review",
                "duplicate_candidate_ids": "espn_wnba_scoreboard_pack_review",
                "output_csv": "wnba_source_proposal_pack.csv",
                "output_md": "wnba_source_proposal_pack.md",
            },
            {
                "pack_key": "lpga",
                "pack_name": "LPGA Source Proposal Pack",
                "display_name": "LPGA / golf",
                "readiness_status": "needs_source_freshness_check",
                "readiness_label": "Freshness/source check",
                "candidate_rows": "10",
                "official_candidates": "6",
                "cross_check_candidates": "0",
                "duplicate_candidates": "0",
                "freshness_check_candidates": "10",
                "ready_candidates": "10",
                "coverage_status": "watch",
                "coverage_gap": "review leaderboard/stat/cross-check source depth",
                "review_cues": "missing cross-check candidate",
                "next_step": "Open candidate pages manually, confirm they are current free public sources, and add missing official or cross-check coverage before proposal.",
                "top_candidate_ids": "lpga_official_home_review; lpga_official_tournaments_review",
                "duplicate_candidate_ids": "",
                "output_csv": "lpga_source_proposal_pack.csv",
                "output_md": "lpga_source_proposal_pack.md",
            },
        ],
    )
    Path("source_registry_proposal_draft.md").write_text(
        "# HSD Source Registry Proposal Draft\n\nThis file is not the live proposal inbox.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_proposal_draft.csv",
        [
            {
                "draft_selection_status": "ready_to_copy_after_freshness_check",
                "draft_action": "manual_copy_to_inbox_after_freshness_check",
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "pack_readiness_status": "ready_for_registry_proposal",
                "pack_readiness_label": "Ready for proposal review",
                "candidate_group": "league_official",
                "suggested_priority": "P1",
                "coverage_key": "pwhl",
                "display_name": "PWHL",
                "needed_source_type": "official_or_team",
                "coverage_gap": "missing official league/team source",
                "candidate_source_id": "pwhl_official_news",
                "candidate_source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "PWHL",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "official_news; source_confirmation",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided PWHL pack candidate.",
                "source_basis": "Free public official league news page.",
                "registry_presence": "not_in_registry",
                "readiness_warning": "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected.",
                "duplicate_warning": "No duplicate candidates detected in this pack.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "manual_review_note": "This is a draft row only.",
            },
            {
                "draft_selection_status": "blocked_duplicate_review",
                "draft_action": "hold_do_not_copy_until_duplicate_review",
                "pack_key": "wnba",
                "pack_name": "WNBA Source Proposal Pack",
                "pack_readiness_status": "needs_duplicate_review",
                "pack_readiness_label": "Duplicate review",
                "candidate_group": "reputable_cross_check",
                "suggested_priority": "P1",
                "coverage_key": "wnba",
                "display_name": "WNBA",
                "needed_source_type": "scoreboard_or_stats_cross_check",
                "coverage_gap": "review scoreboard/stat/cross-check source depth",
                "candidate_source_id": "espn_wnba_scoreboard_pack_review",
                "candidate_source_name": "ESPN WNBA scoreboard",
                "candidate_url": "https://www.espn.com/wnba/scoreboard",
                "candidate_domain": "espn.com",
                "source_type": "scoreboard_site",
                "tier": "primary_media",
                "trust_band": "green_candidate_after_operator_review",
                "sport_league": "WNBA",
                "proposed_enabled": "No",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
                "allowed_use": "cross_check; scores",
                "operator_verification_status": "unverified",
                "registry_action": "proposal_only_do_not_import",
                "review_notes": "Guided WNBA pack candidate.",
                "source_basis": "Free public scoreboard.",
                "registry_presence": "domain_already_exists_check_duplicate",
                "readiness_warning": "1 candidate already resembles trusted registry coverage.",
                "duplicate_warning": "Duplicate review required for pack; duplicate candidate IDs: espn_wnba_scoreboard_pack_review.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "manual_review_note": "This is a draft row only.",
            },
        ],
    )
    Path("source_registry_proposal_promotion_checklist.md").write_text(
        "# HSD Source Registry Proposal Promotion Checklist\n\nManual checklist.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_proposal_promotion_checklist.csv",
        [
            {
                "checklist_decision": "verify_then_copy",
                "operator_step": "1_verify_public_page_then_2_copy_to_manual_inbox",
                "copy_allowed": "Yes_after_manual_freshness_check",
                "copy_target": "operator/inbox/source_registry_proposals.csv",
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "candidate_source_id": "pwhl_official_news",
                "candidate_source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "sport_league": "PWHL",
                "allowed_use": "official_news; source_confirmation",
                "registry_presence": "not_in_registry",
                "draft_selection_status": "ready_to_copy_after_freshness_check",
                "draft_action": "manual_copy_to_inbox_after_freshness_check",
                "duplicate_warning": "No duplicate candidates detected in this pack.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "readiness_warning": "Balanced free official/team/tournament and cross-check candidates; no registry duplicates detected.",
                "verification_checklist": "open candidate_url manually | keep proposed_enabled=No",
                "copy_instructions": "After opening the URL, copy this row into operator/inbox/source_registry_proposals.csv.",
                "hold_reason": "",
                "discard_reason": "",
                "proposed_enabled": "No",
                "registry_action": "proposal_only_do_not_import",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
            },
            {
                "checklist_decision": "discard",
                "operator_step": "discard_duplicate_candidate_do_not_copy",
                "copy_allowed": "No",
                "copy_target": "",
                "pack_key": "wnba",
                "pack_name": "WNBA Source Proposal Pack",
                "candidate_source_id": "espn_wnba_scoreboard_pack_review",
                "candidate_source_name": "ESPN WNBA scoreboard",
                "candidate_url": "https://www.espn.com/wnba/scoreboard",
                "candidate_domain": "espn.com",
                "source_type": "scoreboard_site",
                "tier": "primary_media",
                "sport_league": "WNBA",
                "allowed_use": "cross_check; scores",
                "registry_presence": "domain_already_exists_check_duplicate",
                "draft_selection_status": "blocked_duplicate_review",
                "draft_action": "hold_do_not_copy_until_duplicate_review",
                "duplicate_warning": "Duplicate review required for pack; duplicate candidate IDs: espn_wnba_scoreboard_pack_review.",
                "freshness_warning": "Open this public page manually and confirm it is current before copying to the inbox.",
                "readiness_warning": "1 candidate already resembles trusted registry coverage.",
                "verification_checklist": "open candidate_url manually | keep proposed_enabled=No",
                "copy_instructions": "Do not copy this row into the manual proposal inbox unless the registry duplicate is proven false.",
                "hold_reason": "",
                "discard_reason": "Candidate already resembles trusted registry coverage: domain_already_exists_check_duplicate.",
                "proposed_enabled": "No",
                "registry_action": "proposal_only_do_not_import",
                "automation_status": "disabled_manual_review_only",
                "publish_policy": "proposal_only_not_publish_ready",
            },
        ],
    )
    Path("source_registry_update_worksheet.md").write_text(
        "# HSD Source Registry Update Worksheet\n\nReview-only registry change plan.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_update_worksheet.csv",
        [
            {
                "worksheet_decision": "manual_registry_plan_after_verification",
                "operator_step": "1_open_url_2_confirm_free_public_current_3_compare_json_4_edit_registry_manually_if_approved",
                "manual_edit_target": "config/source_registry.json",
                "manual_edit_allowed": "Yes_only_after_operator_verification",
                "auto_edit_status": "not_performed_by_generator",
                "pack_key": "pwhl",
                "pack_name": "PWHL Source Proposal Pack",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "source_type": "official_site",
                "tier": "official",
                "trust_band": "green_after_operator_verification",
                "sport_league": "PWHL",
                "allowed_use": "official_news; source_confirmation",
                "registry_presence": "not_in_registry",
                "checklist_decision": "verify_then_copy",
                "checklist_copy_target": "operator/inbox/source_registry_proposals.csv",
                "verification_gate": "Operator must open the public URL first.",
                "current_registry_state": "Before: no approved trusted-registry object should be added.",
                "proposed_enabled": "False",
                "proposed_automation_status": "disabled_manual_review_only",
                "proposed_publish_policy": "not_publish_ready_until_operator_verifies_and_enables",
                "proposed_source_json": "{\"enabled\":false,\"source_id\":\"pwhl_official_news\"}",
                "before_after_diff": "Before: no manual change from this generator. After manual approval only: append disabled source object.",
                "rollback_note": "If verification fails, remove the manually added sources[] object with source_id=pwhl_official_news.",
                "review_notes": "Review-only worksheet row.",
            }
        ],
    )
    Path("source_registry_diff_review.md").write_text(
        "# HSD Source Registry Diff Review\n\nRead-only diff preflight.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_diff_review.csv",
        [
            {
                "diff_review_status": "HOLD",
                "resolution_action": "HOLD",
                "resolution_label": "Hold for duplicate review",
                "resolution_reason": "The domain overlaps the trusted registry or another worksheet row; decide whether it is distinct coverage before verification.",
                "verification_log_instruction": "Before filling approval fields, compare the existing/domain-matched source and record same_domain_ok, hold, or discard in operator notes.",
                "issue_count": "1",
                "issues": "candidate domain already exists in trusted registry: thepwhl.com",
                "flags": "duplicate_domain",
                "operator_step": "review_diff_then_verify_url_before_manual_registry_edit",
                "manual_edit_target": "config/source_registry.json",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "proposed_enabled": "False",
                "proposed_trust_band": "green_after_operator_verification",
                "proposed_automation_status": "disabled_manual_review_only",
                "proposed_publish_policy": "not_publish_ready_until_operator_verifies_and_enables",
                "registry_source_id_match": "No",
                "registry_url_match": "No",
                "registry_domain_match": "thepwhl.com",
                "worksheet_domain_match": "No",
                "rollback_status": "present",
                "proposed_json_status": "valid_json",
                "before_after_status": "present",
                "auto_edit_status": "not_performed_by_generator",
                "recommendation": "Do not manually edit the trusted registry until blocking diff issues are resolved.",
            }
        ],
    )
    Path("source_registry_same_domain_resolution.md").write_text(
        "# HSD Source Registry Same-Domain Resolution\n\nManual same-domain review.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_same_domain_resolution.csv",
        [
            {
                "same_domain_resolution_status": "operator_input_required",
                "resolution_decision": "",
                "evidence_requirement": "Required: choose same_domain_ok, revise, discard, or hold; add evidence before approval.",
                "operator_step": "compare_existing_same_domain_source_then_mark_same_domain_ok_revise_or_discard",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "diff_review_status": "HOLD",
                "diff_resolution_action": "HOLD",
                "diff_flags": "duplicate_domain",
                "registry_domain_match": "thepwhl.com",
                "worksheet_domain_match": "No",
                "compared_existing_source_id": "",
                "compared_existing_url": "",
                "evidence_url": "",
                "checked_at_local": "",
                "operator_name": "",
                "operator_notes": "",
                "verification_log_instruction": "Before filling approval fields, compare the existing/domain-matched source and record same_domain_ok, hold, or discard in operator notes.",
                "approval_gate": "same_domain_ok_with_evidence_required_before_approval",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "same_domain_resolution_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        ],
    )
    Path("source_registry_verification_log.md").write_text(
        "# HSD Source Registry Verification Log\n\nManual fill-in log.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_verification_log.csv",
        [
            {
                "verification_log_status": "operator_input_required",
                "operator_step": "open_url_record_freshness_duplicate_decision_and_approval_outcome",
                "diff_resolution_action": "HOLD",
                "diff_resolution_instruction": "Resolve source_registry_same_domain_resolution.csv before filling approval fields in the verification log.",
                "same_domain_resolution_status": "operator_input_required",
                "same_domain_resolution_decision": "",
                "same_domain_evidence_url": "",
                "same_domain_compared_existing_source_id": "",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "diff_review_status": "HOLD",
                "diff_flags": "duplicate_domain",
                "diff_issues": "candidate domain already exists in trusted registry: thepwhl.com",
                "registry_domain_match": "thepwhl.com",
                "worksheet_domain_match": "No",
                "url_checked": "",
                "checked_at_local": "",
                "freshness_result": "",
                "duplicate_decision": "",
                "approval_outcome": "",
                "registry_edit_decision": "",
                "operator_name": "",
                "evidence_url": "",
                "operator_notes": "",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "verification_log_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        ],
    )
    Path("source_registry_approval_packet.md").write_text(
        "# HSD Source Registry Approval Packet\n\nFinal review packet.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_approval_packet.csv",
        [
            {
                "approval_packet_status": "hold_before_manual_registry_edit",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "candidate_url": "https://www.thepwhl.com/en/news",
                "candidate_domain": "thepwhl.com",
                "manual_edit_target": "config/source_registry.json",
                "exact_proposed_source_json": "{\"enabled\":false,\"source_id\":\"pwhl_official_news\"}",
                "url_checked": "https://www.thepwhl.com/en/news",
                "checked_at_local": "2026-06-24 09:00",
                "freshness_result": "unclear",
                "duplicate_decision": "needs_review",
                "approval_outcome": "approved_for_manual_registry_edit",
                "registry_edit_decision": "manual_edit_planned",
                "evidence_url": "https://www.thepwhl.com/en/news",
                "operator_name": "operator",
                "operator_notes": "Needs duplicate-domain review before final edit.",
                "diff_review_status": "HOLD",
                "diff_flags": "duplicate_domain",
                "diff_issues": "candidate domain already exists in trusted registry: thepwhl.com",
                "hold_reason": "diff review is HOLD; freshness_result is not current; duplicate_decision is not approved",
                "approval_guardrails": "final_review_only_no_auto_edit_keep_disabled_until_manual_registry_review",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "approval_packet_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        ],
    )
    Path("source_registry_patch_preview.md").write_text(
        "# HSD Source Registry Patch Preview\n\nManual copy/paste preview.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_patch_preview.csv",
        [
            {
                "patch_preview_status": "ready_for_manual_copy_paste",
                "source_id": "wnba_official_home_review",
                "source_name": "WNBA official site",
                "manual_edit_target": "config/source_registry.json",
                "registry_before_summary": "Current registry has 3 sources[] object(s). source_id=wnba_official_home_review present: No.",
                "side_by_side_before": "No sources[] object with source_id=wnba_official_home_review is present in the current trusted registry.",
                "side_by_side_after": "Append this disabled source object to sources[] for source_id=wnba_official_home_review: {\"enabled\":false,\"source_id\":\"wnba_official_home_review\"}",
                "copy_paste_source_json": "{\n  \"enabled\": false,\n  \"source_id\": \"wnba_official_home_review\"\n}",
                "copy_paste_patch_instructions": "Manual only: open config/source_registry.json, append the copy_paste_source_json object to sources[], keep enabled=false and automation_status=disabled_manual_review_only, save, then rerun review.",
                "rollback_instructions": "If final review fails, manually remove the sources[] object with source_id=wnba_official_home_review and rerun review.",
                "url_checked": "https://www.wnba.com/",
                "evidence_url": "https://www.wnba.com/",
                "freshness_result": "current",
                "duplicate_decision": "not_duplicate",
                "approval_packet_status": "ready_for_final_manual_review",
                "hold_reason": "none",
                "preview_guardrails": "manual_copy_paste_preview_only_no_auto_edit_keep_disabled_until_human_registry_review",
                "auto_edit_status": "not_performed_by_generator",
                "publish_policy": "patch_preview_only_not_publish_ready",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "registry_edit_status": "not_edited_by_generator",
            }
        ],
    )
    Path("source_registry_post_edit_validation.md").write_text(
        "# HSD Source Registry Post-Edit Validation\n\nRead-only validation.\n",
        encoding="utf-8",
    )
    write_csv(
        "source_registry_post_edit_validation.csv",
        [
            {
                "post_edit_validation_status": "validated_exact_match",
                "source_id": "wnba_official_home_review",
                "source_name": "WNBA official site",
                "manual_edit_target": "config/source_registry.json",
                "expected_source_json": "{\"enabled\":false,\"source_id\":\"wnba_official_home_review\"}",
                "actual_source_json": "{\"enabled\":false,\"source_id\":\"wnba_official_home_review\"}",
                "exact_match": "Yes",
                "drift_fields": "none",
                "unsafe_flags": "none",
                "enabled_status": "disabled",
                "automation_status_check": "pass",
                "publish_policy_check": "pass",
                "free_source_check": "pass",
                "approval_packet_status": "ready_for_final_manual_review",
                "patch_preview_status": "ready_for_manual_copy_paste",
                "evidence_url": "https://www.wnba.com/",
                "rollback_instructions": "Remove source_id=wnba_official_home_review.",
                "recommendation": "Registry row matches the approved preview and remains disabled/manual-review-only.",
                "validation_guardrails": "read_only_post_edit_validation_no_auto_fix_no_enable_no_publish",
                "auto_edit_status": "not_performed_by_generator",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "publish_policy": "validation_only_not_publish_ready",
                "registry_edit_status": "not_edited_by_generator",
            },
            {
                "post_edit_validation_status": "unsafe_hold",
                "source_id": "pwhl_official_news",
                "source_name": "PWHL official news",
                "manual_edit_target": "config/source_registry.json",
                "expected_source_json": "{\"enabled\":false,\"source_id\":\"pwhl_official_news\"}",
                "actual_source_json": "{\"enabled\":true,\"source_id\":\"pwhl_official_news\"}",
                "exact_match": "No",
                "drift_fields": "enabled; automation_status; publish_policy",
                "unsafe_flags": "enabled_not_false; automation_not_disabled_manual_review_only; publish_policy_not_review_only",
                "enabled_status": "unsafe_enabled_value=True",
                "automation_status_check": "review",
                "publish_policy_check": "review",
                "free_source_check": "pass",
                "approval_packet_status": "ready_for_final_manual_review",
                "patch_preview_status": "ready_for_manual_copy_paste",
                "evidence_url": "https://www.thepwhl.com/en/news",
                "rollback_instructions": "Remove source_id=pwhl_official_news.",
                "recommendation": "Hold this registry row until unsafe enablement, automation, paid/login, or publish-policy issue is fixed manually.",
                "validation_guardrails": "read_only_post_edit_validation_no_auto_fix_no_enable_no_publish",
                "auto_edit_status": "not_performed_by_generator",
                "paid_api_policy": "free_public_sources_only_no_paid_api",
                "publish_policy": "validation_only_not_publish_ready",
                "registry_edit_status": "not_edited_by_generator",
            },
        ],
    )
    Path("trusted_registry_operator_playbook.md").write_text(
        "# HSD Trusted Registry Operator Playbook\n\nStep-by-step human workflow with stop/go decisions and rollback steps.\n",
        encoding="utf-8",
    )
    Path("source_proposal_packs.csv").write_text(
        Path("pwhl_source_proposal_pack.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    Path("source_registry_audit.md").write_text("# Source registry audit\n", encoding="utf-8")
    write_csv(
        "morning_source_discovery_board.csv",
        [
            {
                "rank": "1",
                "lane": "social_discovery",
                "review_status": "needs_green_confirmation",
                "source_band": "yellow",
                "publish_posture": "discovery_only",
                "source_name": "team_social_manual_only",
                "source_type": "social_manual_only",
                "sport_league": "all",
                "title": "Public team social lead",
                "summary": "A public team account has a possible lead.",
                "source_url": "https://www.instagram.com/example",
                "evidence_title": "Official metadata title for public team lead",
                "evidence_published_at": "2026-06-10T12:00:00+00:00",
                "evidence_description": "A concise public metadata description for operator review.",
                "evidence_preview": "Official metadata title for public team lead | 2026-06-10 | A concise public metadata description for operator review.",
                "evidence_source": "article_metadata",
                "story_opportunity_id": "opp_fixture_cluster",
                "story_opportunity_title": "Public team social lead",
                "story_opportunity_size": "2",
                "story_opportunity_sources": "wnba_official_news; ap_womens_sports_wire",
                "story_opportunity_urls": "https://www.wnba.com/news/example; https://apnews.com/article/example",
                "story_opportunity_reason": "Grouped 2 related official/wire discovery leads from wnba_official_news, ap_womens_sports_wire.",
                "story_opportunity_angle": "Roster or transaction update",
                "story_opportunity_recommended_path": "news_packet",
                "story_opportunity_path_reason": "Factual roster, transaction, personnel, or league-structure signal belongs in a source-backed News packet.",
                "story_opportunity_confidence_tier": "needs_official_confirmation",
                "story_opportunity_source_coverage": "discovery_source_only",
                "story_opportunity_confirmation_cue": "needs_official_confirmation",
                "story_opportunity_asset_cue": "asset_not_required_for_news_packet",
                "story_opportunity_readiness_note": "Confirm this with an official, wire, primary, or operator-verified source before News or Studio work.",
                "story_opportunity_second_source_id": "wnba_official_news",
                "story_opportunity_second_source_url": "https://www.wnba.com/news",
                "story_opportunity_second_source_lane": "official_free",
                "story_opportunity_second_source_reason": "same league/sport lane; official news/roster confirmation",
                "story_opportunity_second_source_action": "Open wnba_official_news and confirm the same fact before drafting.",
                "source_artifact": "morning_source_discovery_board.csv",
                "next_action": "Use as a lead only; find official, wire, or primary confirmation before publishing.",
                "reason": "requires official confirmation",
                "candidate_id": "",
                "evidence_count": "0",
                "promotion_recommendation": "manual_story_candidate",
                "promotion_priority": "P3",
                "promotion_target": "story_candidates_manual.csv",
                "promotion_reason": "Discovery-only lead needs official confirmation.",
                "promotion_next_step": "Add or verify the lead in the manual story inbox with evidence URLs and locked facts.",
                "quality_score": "40",
                "freshness_label": "recent_30_days",
                "freshness_source": "article_metadata",
            }
        ],
    )
    Path("morning_source_discovery_board.md").write_text("# Morning source discovery\n", encoding="utf-8")
    write_csv(
        "morning_lead_promotion_recommendations.csv",
        [
            {
                "promotion_rank": "1",
                "rank": "1",
                "lane": "social_discovery",
                "review_status": "needs_green_confirmation",
                "source_band": "yellow",
                "publish_posture": "discovery_only",
                "source_name": "team_social_manual_only",
                "source_type": "social_manual_only",
                "sport_league": "all",
                "title": "Public team social lead",
                "summary": "A public team account has a possible lead.",
                "source_url": "https://www.instagram.com/example",
                "evidence_title": "Official metadata title for public team lead",
                "evidence_published_at": "2026-06-10T12:00:00+00:00",
                "evidence_description": "A concise public metadata description for operator review.",
                "evidence_preview": "Official metadata title for public team lead | 2026-06-10 | A concise public metadata description for operator review.",
                "evidence_source": "article_metadata",
                "story_opportunity_id": "opp_fixture_cluster",
                "story_opportunity_title": "Public team social lead",
                "story_opportunity_size": "2",
                "story_opportunity_sources": "wnba_official_news; ap_womens_sports_wire",
                "story_opportunity_urls": "https://www.wnba.com/news/example; https://apnews.com/article/example",
                "story_opportunity_reason": "Grouped 2 related official/wire discovery leads from wnba_official_news, ap_womens_sports_wire.",
                "story_opportunity_angle": "Roster or transaction update",
                "story_opportunity_recommended_path": "news_packet",
                "story_opportunity_path_reason": "Factual roster, transaction, personnel, or league-structure signal belongs in a source-backed News packet.",
                "story_opportunity_confidence_tier": "needs_official_confirmation",
                "story_opportunity_source_coverage": "discovery_source_only",
                "story_opportunity_confirmation_cue": "needs_official_confirmation",
                "story_opportunity_asset_cue": "asset_not_required_for_news_packet",
                "story_opportunity_readiness_note": "Confirm this with an official, wire, primary, or operator-verified source before News or Studio work.",
                "story_opportunity_second_source_id": "wnba_official_news",
                "story_opportunity_second_source_url": "https://www.wnba.com/news",
                "story_opportunity_second_source_lane": "official_free",
                "story_opportunity_second_source_reason": "same league/sport lane; official news/roster confirmation",
                "story_opportunity_second_source_action": "Open wnba_official_news and confirm the same fact before drafting.",
                "source_artifact": "morning_source_discovery_board.csv",
                "next_action": "Use as a lead only; find official, wire, or primary confirmation before publishing.",
                "reason": "requires official confirmation",
                "candidate_id": "",
                "evidence_count": "0",
                "promotion_recommendation": "manual_story_candidate",
                "promotion_priority": "P3",
                "promotion_target": "story_candidates_manual.csv",
                "promotion_reason": "Discovery-only lead needs official confirmation.",
                "promotion_next_step": "Add or verify the lead in the manual story inbox with evidence URLs and locked facts.",
                "quality_score": "40",
                "freshness_label": "recent_30_days",
                "freshness_source": "article_metadata",
            }
        ],
    )
    Path("morning_lead_promotion_recommendations.md").write_text("# Lead promotion recommendations\n", encoding="utf-8")
    Path("studio_bundle_queue.csv").touch()
    seed_asset_availability_audit_files()


def test_operator_command_center_builds_daily_ops_view(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    seed_manual_visual_qa_decision_files()

    payload = command_center.build_payload()
    html = command_center.render_html(payload)
    markdown = command_center.render_markdown(payload)

    assert payload["version"] == "hsd-operator-command-center-v3.84.0-athlete-photo-contact-sheets"
    assert payload["decision"]["automation"] == "OFF / artifact-only"
    assert payload["decision"]["free_source_mode"] == "Free public sources only"
    assert "no graphics upload pack is ready" in payload["decision"]["callout"]
    assert payload["briefing"]["best_candidate"] == "New York Liberty beat Las Vegas Aces"
    assert payload["briefing"]["studio_lane"] == "Tonight in the W"
    assert any(action["status"] == "Manual only" for action in payload["next_actions"])
    assert any(action["title"] == "Review source registry audit" for action in payload["next_actions"])
    assert any(action["title"] == "Build graphics pack for Tonight in the W" for action in payload["next_actions"])
    build_action = next(action for action in payload["next_actions"] if action["title"] == "Build graphics pack for Tonight in the W")
    assert build_action["status"] == "Build next"
    assert build_action["command"] == ".\\hsd.cmd run -Mode asset"
    assert any(action["title"] == "Propose free source coverage for PWHL" for action in payload["next_actions"])
    assert any(action["title"] == "Resolve unsafe source proposal: pwhl_instagram" for action in payload["next_actions"])
    assert any(action["title"] == "Promote source lead toward manual_story_candidate: Public team social lead" for action in payload["next_actions"])
    assert all(action["title"] != "no_content_ready" for action in payload["next_actions"])
    assert any(item["label"] == "Source registry" and item["value"] == "REVIEW" for item in payload["metrics"])
    assert any(item["label"] == "Publish-grade packets" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Discovery-only packets" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Morning source rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Story opportunities" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Grouped opportunities" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Publish-grade opportunities" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Needs source check" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Second-source suggestions" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source coverage gaps" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source coverage watch" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Source intake proposals" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source proposal holds" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source proposals ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Proposal draft rows" and item["value"] == "2" for item in payload["metrics"])
    assert any(item["label"] == "Proposal draft ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Proposal draft blocked" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Checklist verify/copy" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Checklist hold" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Checklist discard" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry worksheet rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Worksheet disabled plans" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry diff hold" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry diff review" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Registry diff pass" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Diff cues verify" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Diff cues revise" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Diff cues hold" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Diff cues discard" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Same-domain rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Same-domain needs decision" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Same-domain OK" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Same-domain revise/discard" and item["value"] == "0/0" for item in payload["metrics"])
    assert any(item["label"] == "Verification log rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Verification input needed" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Approval packet rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Approval packet ready" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Approval packet held" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Patch preview rows" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Patch preview ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Patch preview held" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Post-edit validations" and item["value"] == "2" for item in payload["metrics"])
    assert any(item["label"] == "Post-edit exact" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Post-edit issues" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Registry readiness" and item["value"] == "blocked_post_edit_validation" for item in payload["metrics"])
    assert any(item["label"] == "Source packs ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source packs duplicate review" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Source packs freshness check" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Guided source pack rows" and item["value"] == "3" for item in payload["metrics"])
    assert any(item["label"] == "PWHL proposal pack" and item["value"] == "3" for item in payload["metrics"])
    assert any(item["label"] == "Studio asset checks" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Gray/social leads" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Lead promotions" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "High-quality leads" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Fresh leads" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "News/Manual/Studio" and item["value"] == "0/1/0" for item in payload["metrics"])
    assert any(item["label"] == "Render readiness rows" and item["value"] == "2" for item in payload["metrics"])
    assert any(item["label"] == "Render-ready review" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Render prep candidates" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Render holds" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Render needs source" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Render needs asset" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Render prep packets" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Render packets ready" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Render handoff" and item["value"] == "ready_for_manual_review" for item in payload["metrics"])
    assert any(item["label"] == "Decision UI" and item["value"] == "awaiting_operator_decision" for item in payload["metrics"])
    assert any(item["label"] == "Decision inbox rows" and item["value"] == "0" for item in payload["metrics"])
    assert any(item["label"] == "Asset audit" and item["value"] == "review_required" for item in payload["metrics"])
    assert any(item["label"] == "Asset blockers" and item["value"] == "5" for item in payload["metrics"])
    assert any(item["label"] == "Asset errors/warnings" and item["value"] == "2/2" for item in payload["metrics"])
    assert any(item["label"] == "Default photo approvals" and item["value"] == "1" for item in payload["metrics"])
    assert payload["asset_readiness_panel"]["panel_status"] == "review_required"
    assert payload["asset_readiness_panel"]["finding_count"] == 5
    assert payload["asset_readiness_panel"]["logo_review_packet_rows"] == 1
    assert payload["asset_readiness_panel"]["logo_review_packet_unapproved_rows"] == 1
    assert payload["asset_readiness_panel"]["logo_review_packet_freshness_status"] == "packet_ready"
    assert "present with 1 row(s)" in payload["asset_readiness_panel"]["logo_review_packet_freshness_detail"]
    assert payload["asset_readiness_panel"]["top_findings"][0]["decision"] == "Verify identity"
    assert payload["asset_readiness_panel"]["top_findings"][0]["decision_lane"] == "wnba_athlete_identity_resolution"
    assert payload["asset_readiness_panel"]["top_findings"][0]["default_operator_decision"] == "hold_identity"
    assert payload["asset_readiness_panel"]["top_findings"][0]["identity_confidence"] == "identity_hold_default_or_suspicious_approval"
    assert payload["asset_readiness_panel"]["top_findings"][0]["asset_readiness"] == "review_only_manual_source_recheck_required: default_decision_source_manual_recheck_required"
    assert any(item["decision"] == "Verify logo" for item in payload["asset_readiness_panel"]["top_findings"])
    league_finding = next(item for item in payload["asset_readiness_panel"]["top_findings"] if item["decision"] == "Hold league mark")
    assert league_finding["decision_lane"] == "wnba_logo_review"
    assert league_finding["default_operator_decision"] == "hold_league_mark"
    assert league_finding["source_confidence"] == "source_missing_or_unregistered"
    assert league_finding["asset_readiness"] == "optional_league_logo_file_missing_review_only"
    assert league_finding["blocker_summary"] == "WNBA: missing league mark; default decision=hold_league_mark; readiness=optional_league_logo_file_missing_review_only"
    assert command_center.audit_decision_lane("league_logo", "missing_or_unregistered_logo_asset", "WOMENS_SOCCER") == "logo_review"
    assert any(item["decision"] == "Verify renderer fallback" for item in payload["asset_readiness_panel"]["top_findings"])
    assert "Asset readiness" in html
    assert "Highest-risk asset blockers" in html
    assert "Focused logo review packets" in html
    assert "WNBA logo review: New York Liberty" in html
    assert "Path check:" in html
    assert "assets/leagues/wnba/teams/new_york_liberty/logo.svg" in html
    assert "Renderer fallback remains review-only while logo trust is held." in html
    assert "HSD team badges are review-only stand-ins" in html
    assert "they do not approve logo identity or create a publish-ready lane" in html
    assert "review-only fallback status not recorded" not in html
    assert "Verify identity" in html
    assert "Hold league mark" in html
    assert "data/asset_registry/asset_availability_audit.md" in html
    assert "Asset Readiness Decision Desk" in markdown
    assert "review-only, no paid APIs, no asset downloads" in markdown
    assert "packet: wnba_athlete_identity_resolution / hold_identity / review_only_manual_source_recheck_required: default_decision_source_manual_recheck_required" in markdown
    assert "packet: wnba_logo_review / hold_league_mark / optional_league_logo_file_missing_review_only" in markdown
    assert "packet: manual_review / review_required / review_required" not in markdown
    assert "Logo review packets: 1 (1 unapproved / 0 source drift)" in markdown
    assert "Logo review packet freshness: packet_ready" in markdown
    assert "Logo packet: New York Liberty | unapproved_required_logo | WNBA logo review: New York Liberty" in markdown
    assert "registered=assets/leagues/wnba/logos/new_york_liberty/logo.png" in markdown
    assert "source=assets/leagues/wnba/teams/new_york_liberty/logo.svg" in markdown
    assert "fallback=Renderer fallback remains review-only while logo trust is held." in markdown
    assert "fallback: HSD team badges are review-only stand-ins for missing or undecodable exact logos; they do not approve logo identity or create a publish-ready lane." in markdown
    assert "review-only fallback status not recorded" not in markdown
    assert "Identity review packets: 1 (1 holds / 1 default approvals)" in markdown
    assert "Identity review packet freshness: packet_ready" in markdown
    assert "Athlete photo contact sheets packet freshness: packet_ready" in markdown
    assert "Athlete source boards: 1 team board(s) / 1 athlete row(s)" in markdown
    assert "Identity team queue: new_york_liberty | packets=1 | holds=1 | defaults=1 | high=1" in markdown
    assert "Identity packet: Breanna Stewart | new_york_liberty | hold_identity_review_required | hold=true | default=true" in markdown
    assert "reasons=approved_asset_still_has_pending_match_review|default_approval_requires_identity_recheck" in markdown
    assert "evidence=approved marker decision_source=default" in markdown
    assert "steps=open_asset_and_marker; compare_to_official_player_or_team_source; choose_hold_or_verified_review_only_decision" in markdown
    assert any(item["label"] == "Athlete photo review" and item["value"] == "hold_identity_review_required" for item in payload["metrics"])
    assert any(item["label"] == "Athlete photo variants" and item["value"] == "1/1" for item in payload["metrics"])
    assert any(item["label"] == "Athlete source boards" and item["value"] == "1/1" for item in payload["metrics"])
    assert payload["athlete_photo_onboarding_panel"]["identity_audit_status"] == "needs_identity_review"
    assert payload["athlete_photo_onboarding_panel"]["identity_resolution_status"] == "not_run"
    assert payload["athlete_photo_onboarding_panel"]["identity_review_packet_rows"] == 1
    assert payload["athlete_photo_onboarding_panel"]["identity_review_packet_hold_rows"] == 1
    assert payload["athlete_photo_onboarding_panel"]["identity_review_packet_default_rows"] == 1
    assert payload["athlete_photo_onboarding_panel"]["identity_review_packet_freshness_status"] == "packet_ready"
    assert "present with 1 row(s)" in payload["athlete_photo_onboarding_panel"]["identity_review_packet_freshness_detail"]
    assert payload["athlete_photo_onboarding_panel"]["athlete_contact_sheet_status"] == "contact_sheets_ready"
    assert payload["athlete_photo_onboarding_panel"]["athlete_contact_sheet_rows"] == 1
    assert payload["athlete_photo_onboarding_panel"]["athlete_contact_sheet_teams"] == 1
    assert payload["athlete_photo_onboarding_panel"]["athlete_contact_sheet_intake_rows"] == 1
    assert payload["athlete_photo_onboarding_panel"]["athlete_contact_sheet_freshness_status"] == "packet_ready"
    assert any(item["label"] == "WNBA athlete photo contact sheets" for item in payload["athlete_photo_onboarding_panel"]["file_shortcuts"])
    assert any(item["label"] == "WNBA athlete photo review intake" for item in payload["athlete_photo_onboarding_panel"]["file_shortcuts"])
    assert payload["athlete_photo_onboarding_panel"]["identity_review_packet_teams"][0] == {
        "team_id": "new_york_liberty",
        "packet_rows": "1",
        "identity_hold_rows": "1",
        "default_approval_rows": "1",
        "high_severity_rows": "1",
    }
    assert payload["athlete_photo_onboarding_panel"]["identity_resolution_inbox_rows"] == 0
    assert payload["athlete_photo_onboarding_panel"]["identity_closure_status"] == "not_run"
    assert payload["athlete_photo_onboarding_panel"]["review_rows"][0]["identity_review_status"] == "hold_identity_review_required"
    assert payload["athlete_photo_onboarding_panel"]["review_rows"][0]["identity_resolution_status"] == "resolution_not_recorded"
    assert payload["athlete_photo_onboarding_panel"]["review_rows"][0]["identity_issue_codes"] == "approved_asset_still_has_pending_match_review"
    assert payload["athlete_photo_onboarding_panel"]["review_rows"][0]["identity_candidate_status"] == "no_resolution_candidate"
    assert "Athlete photo onboarding" in html
    assert "Identity resolution" in html
    assert "Focused identity review packet" in html
    assert "Team packet queues" in html
    assert "identity team queue" in html
    assert "default approvals" in html
    assert "https://www.wnba.com/player/1627668/breanna-stewart" in html
    assert "Verify, hold, revise, or backfill" in html
    assert "operator/inbox/wnba_athlete_identity_resolution.csv" in html
    assert "Backfill-only rows do not clear photo-first rendering." in html
    assert ".\\hsd.cmd run -Mode identity-decision" in html
    assert "Local save mode is active" in html
    assert "Save identity row" in html
    assert "Identity audit says hold" in html
    assert "approved_asset_still_has_pending_match_review" in html
    assert "approved marker needs recheck" in html
    assert "Hold reasons:" in html
    assert "Evidence:" in html
    assert "Operator steps:" in html
    assert "approved marker decision_source=default" in html
    assert payload["briefing"]["source_state"] == "2 pass, 1 review, 0 fail across 3 sources."
    assert payload["source_coverage_map"][1]["name"] == "PWHL"
    assert payload["source_coverage_map"][1]["status"] == "gap"
    assert "PWHL league/team official pages" in payload["source_coverage_map"][1]["next_step"]
    assert payload["source_registry_intake_template"][0]["display_name"] == "PWHL"
    assert payload["source_registry_intake_template"][0]["proposed_enabled"] == "No"
    assert payload["source_registry_intake_template"][0]["registry_action"] == "proposal_only_do_not_import"
    assert payload["source_registry_proposal_review"][0]["candidate_source_id"] == "pwhl_instagram"
    assert payload["source_registry_proposal_review"][0]["review_status"] == "hold"
    assert payload["source_registry_proposal_review"][1]["review_status"] == "ready_for_registry_review"
    assert payload["source_registry_proposal_draft"][0]["draft_selection_status"] == "ready_to_copy_after_freshness_check"
    assert payload["source_registry_proposal_draft"][0]["draft_action"] == "manual_copy_to_inbox_after_freshness_check"
    assert payload["source_registry_proposal_draft"][0]["proposed_enabled"] == "No"
    assert payload["source_registry_proposal_draft"][1]["draft_selection_status"] == "blocked_duplicate_review"
    assert "Duplicate review required" in payload["source_registry_proposal_draft"][1]["duplicate_warning"]
    assert payload["source_registry_proposal_promotion_checklist"][0]["checklist_decision"] == "verify_then_copy"
    assert payload["source_registry_proposal_promotion_checklist"][0]["copy_allowed"] == "Yes_after_manual_freshness_check"
    assert payload["source_registry_proposal_promotion_checklist"][1]["checklist_decision"] == "discard"
    assert "trusted registry coverage" in payload["source_registry_proposal_promotion_checklist"][1]["discard_reason"]
    assert payload["source_registry_update_worksheet"][0]["worksheet_decision"] == "manual_registry_plan_after_verification"
    assert payload["source_registry_update_worksheet"][0]["manual_edit_target"] == "config/source_registry.json"
    assert payload["source_registry_update_worksheet"][0]["proposed_enabled"] == "False"
    assert payload["source_registry_update_worksheet"][0]["auto_edit_status"] == "not_performed_by_generator"
    assert "remove the manually added" in payload["source_registry_update_worksheet"][0]["rollback_note"]
    assert payload["source_registry_diff_review"][0]["diff_review_status"] == "HOLD"
    assert payload["source_registry_diff_review"][0]["resolution_action"] == "HOLD"
    assert payload["source_registry_diff_review"][0]["resolution_label"] == "Hold for duplicate review"
    assert "Before filling approval fields" in payload["source_registry_diff_review"][0]["verification_log_instruction"]
    assert payload["source_registry_diff_review"][0]["flags"] == "duplicate_domain"
    assert payload["source_registry_diff_review"][0]["registry_domain_match"] == "thepwhl.com"
    assert payload["source_registry_diff_review"][0]["rollback_status"] == "present"
    assert payload["source_registry_same_domain_resolution"][0]["same_domain_resolution_status"] == "operator_input_required"
    assert payload["source_registry_same_domain_resolution"][0]["approval_gate"] == "same_domain_ok_with_evidence_required_before_approval"
    assert "choose same_domain_ok" in payload["source_registry_same_domain_resolution"][0]["evidence_requirement"]
    assert payload["source_registry_verification_log"][0]["verification_log_status"] == "operator_input_required"
    assert payload["source_registry_verification_log"][0]["diff_resolution_action"] == "HOLD"
    assert "Resolve source_registry_same_domain_resolution.csv" in payload["source_registry_verification_log"][0]["diff_resolution_instruction"]
    assert payload["source_registry_verification_log"][0]["same_domain_resolution_status"] == "operator_input_required"
    assert payload["source_registry_verification_log"][0]["url_checked"] == ""
    assert payload["source_registry_verification_log"][0]["freshness_result"] == ""
    assert payload["source_registry_verification_log"][0]["duplicate_decision"] == ""
    assert payload["source_registry_verification_log"][0]["approval_outcome"] == ""
    assert payload["source_registry_verification_log"][0]["registry_edit_status"] == "not_edited_by_generator"
    assert payload["source_registry_approval_packet"][0]["approval_packet_status"] == "hold_before_manual_registry_edit"
    assert payload["source_registry_approval_packet"][0]["approval_outcome"] == "approved_for_manual_registry_edit"
    assert "diff review is HOLD" in payload["source_registry_approval_packet"][0]["hold_reason"]
    assert "pwhl_official_news" in payload["source_registry_approval_packet"][0]["exact_proposed_source_json"]
    assert payload["source_registry_approval_packet"][0]["registry_edit_status"] == "not_edited_by_generator"
    assert payload["source_registry_patch_preview"][0]["patch_preview_status"] == "ready_for_manual_copy_paste"
    assert payload["source_registry_patch_preview"][0]["source_id"] == "wnba_official_home_review"
    assert "source_id=wnba_official_home_review present: No" in payload["source_registry_patch_preview"][0]["registry_before_summary"]
    assert "append the copy_paste_source_json object to sources[]" in payload["source_registry_patch_preview"][0]["copy_paste_patch_instructions"]
    assert payload["source_registry_patch_preview"][0]["registry_edit_status"] == "not_edited_by_generator"
    assert payload["source_registry_post_edit_validation"][0]["post_edit_validation_status"] == "validated_exact_match"
    assert payload["source_registry_post_edit_validation"][0]["exact_match"] == "Yes"
    assert payload["source_registry_post_edit_validation"][1]["post_edit_validation_status"] == "unsafe_hold"
    assert "enabled_not_false" in payload["source_registry_post_edit_validation"][1]["unsafe_flags"]
    assert payload["source_registry_post_edit_validation"][1]["registry_edit_status"] == "not_edited_by_generator"
    assert payload["source_registry_readiness_summary"]["readiness_status"] == "blocked_post_edit_validation"
    assert payload["source_registry_readiness_summary"]["open_first_file"] == "source_registry_post_edit_validation.md"
    assert payload["source_registry_readiness_summary"]["support_file"] == "trusted_registry_operator_playbook.md"
    assert "Open source_registry_post_edit_validation.md first" in payload["source_registry_readiness_summary"]["next_safest_action"]
    assert "pwhl_official_news: unsafe_hold" in payload["source_registry_readiness_summary"]["blockers"]
    assert "enabled_not_false" in payload["source_registry_readiness_summary"]["blockers"]
    assert payload["source_registry_readiness_summary"]["focus_source_ids"] == "pwhl_official_news"
    assert payload["source_proposal_pack_readiness"][0]["pack_key"] == "pwhl"
    assert payload["source_proposal_pack_readiness"][0]["readiness_status"] == "ready_for_registry_proposal"
    assert payload["source_proposal_pack_readiness"][1]["readiness_status"] == "needs_duplicate_review"
    assert payload["source_proposal_pack_readiness"][2]["readiness_status"] == "needs_source_freshness_check"
    assert payload["source_proposal_packs"][0]["pack_key"] == "pwhl"
    assert payload["source_proposal_packs"][0]["candidate_source_id"] == "pwhl_official_news"
    assert payload["pwhl_source_proposal_pack"][0]["candidate_source_id"] == "pwhl_official_news"
    assert payload["pwhl_source_proposal_pack"][1]["candidate_source_id"] == "pwhl_boston_fleet_team"
    assert payload["pwhl_source_proposal_pack"][2]["candidate_source_id"] == "pwhl_official_scores"
    pwhl_action = next(action for action in payload["next_actions"] if action["title"] == "Propose free source coverage for PWHL")
    assert pwhl_action["artifact"] == "source_proposal_packs.csv"
    assert "guided PWHL Source Proposal Pack with 3 free official/team/cross-check candidates" in pwhl_action["detail"]
    draft_action = next(action for action in payload["next_actions"] if action["title"] == "Review manual source proposal draft")
    assert draft_action["artifact"] == "source_registry_proposal_draft.md"
    assert "1 draft row(s) are ready to copy" in draft_action["detail"]
    checklist_action = next(action for action in payload["next_actions"] if action["title"] == "Work source proposal promotion checklist")
    assert checklist_action["artifact"] == "source_registry_proposal_promotion_checklist.md"
    assert "1 row(s) are verify-then-copy candidates" in checklist_action["detail"]
    playbook_action = next(action for action in payload["next_actions"] if action["title"] == "Open trusted-registry operator playbook")
    assert playbook_action["artifact"] == "trusted_registry_operator_playbook.md"
    assert "step-by-step stop/go workflow" in playbook_action["detail"]
    assert "rollback steps" in playbook_action["detail"]
    worksheet_action = next(action for action in payload["next_actions"] if action["title"] == "Review trusted-registry update worksheet")
    assert worksheet_action["artifact"] == "source_registry_update_worksheet.md"
    assert "1 review-only registry plan row(s)" in worksheet_action["detail"]
    diff_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve trusted-registry diff review")
    assert diff_action["artifact"] == "source_registry_diff_review.md"
    assert "1 hold row(s)" in diff_action["detail"]
    assert "Do not hand-edit the registry" in diff_action["detail"]
    same_domain_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve same-domain source decisions")
    assert same_domain_action["artifact"] == "source_registry_same_domain_resolution.md"
    assert "1 need decision/evidence" in same_domain_action["detail"]
    verification_action = next(action for action in payload["next_actions"] if action["title"] == "Fill manual source verification log")
    assert verification_action["artifact"] == "source_registry_verification_log.md"
    assert "1 source row(s) need operator evidence" in verification_action["detail"]
    assert "URL checked, freshness result, duplicate decision" in verification_action["detail"]
    approval_action = next(action for action in payload["next_actions"] if action["title"] == "Review manual registry approval packet")
    assert approval_action["artifact"] == "source_registry_approval_packet.md"
    assert "0 ready row(s), 1 held row(s)" in approval_action["detail"]
    assert "review-only" in approval_action["detail"]
    patch_preview_action = next(action for action in payload["next_actions"] if action["title"] == "Review manual registry patch preview")
    assert patch_preview_action["artifact"] == "source_registry_patch_preview.md"
    assert "1 ready copy/paste row(s), 0 held row(s)" in patch_preview_action["detail"]
    assert "does not edit the trusted registry" in patch_preview_action["detail"]
    post_edit_action = next(action for action in payload["next_actions"] if action["title"] == "Review post-edit registry validation")
    assert post_edit_action["artifact"] == "source_registry_post_edit_validation.md"
    assert "1 exact match row(s), 1 issue row(s)" in post_edit_action["detail"]
    assert "Hold any drift" in post_edit_action["detail"]
    checklist_hold_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve held or discarded source checklist rows")
    assert checklist_hold_action["artifact"] == "source_registry_proposal_promotion_checklist.md"
    assert "1 discard row(s)" in checklist_hold_action["detail"]
    duplicate_pack_action = next(action for action in payload["next_actions"] if action["title"] == "Resolve duplicate cues in WNBA Source Proposal Pack")
    assert duplicate_pack_action["artifact"] == "source_proposal_pack_readiness.md"
    assert "espn_wnba_scoreboard_pack_review" in duplicate_pack_action["detail"]
    render_action = next(action for action in payload["next_actions"] if action["title"] == "Review render-ready story candidate: New York Liberty beat Las Vegas Aces")
    assert render_action["status"] == "Render ready"
    assert "Score 100/100" in render_action["detail"]
    assert "Source, format, and manual path cues are ready; active asset holds remain stop/go review cues." in render_action["detail"]
    assert "Source, asset, format, and manual path cues are ready" not in render_action["detail"]
    assert render_action["artifact"] == "news_fact_packets.csv"
    packet_action = next(action for action in payload["next_actions"] if action["title"] == "Open render prep packet: New York Liberty beat Las Vegas Aces")
    assert packet_action["status"] == "Render packet"
    assert packet_action["artifact"] == "render_prep_packets.md"
    assert "hsd_game_recap_final_score_a" in packet_action["detail"]
    handoff_action = next(action for action in payload["next_actions"] if action["title"] == "Open render handoff folder: New York Liberty beat Las Vegas Aces")
    assert handoff_action["status"] == "Render handoff"
    assert handoff_action["artifact"] == "render_handoff_top_packet/README.md"
    assert payload["render_readiness_queue"][0]["title"] == "New York Liberty beat Las Vegas Aces"
    assert payload["render_readiness_queue"][0]["band"] == "render_ready_review"
    assert payload["render_readiness_queue"][0]["score"] == "100"
    assert payload["render_readiness_queue"][0]["source_cue"] == "source_confidence_ready"
    assert payload["render_readiness_queue"][0]["asset_cue"] == "artifact_assets_ready_or_not_required"
    assert payload["render_readiness_queue"][0]["format_cue"] == "news_packet_format_fit"
    assert payload["render_readiness_queue"][0]["manual_path"] == "manual_review_artifact_ready:news_fact_packets.csv"
    assert payload["render_readiness_queue"][0]["blockers"] == "none"
    assert payload["render_readiness_queue"][0]["active_asset_stop_go"] == "hold_required_manual_asset_review"
    assert payload["render_readiness_queue"][0]["active_logo_readiness_status"] == "hold_logo_review_required"
    assert payload["render_readiness_queue"][0]["active_athlete_identity_status"] == "hold_identity_review_required"
    assert command_center.display_render_blockers(payload["render_readiness_queue"][0]) == "none for source/format/manual path; active asset holds remain"
    assert payload["render_readiness_queue"][1]["title"] == "Public team social lead"
    assert payload["render_readiness_queue"][1]["band"] == "hold_for_source_confirmation"
    assert payload["render_readiness_queue"][1]["blockers"] == "source confirmation required"
    assert payload["render_prep_packets"][0]["packet_status"] == "ready_for_manual_render_review"
    assert payload["render_prep_packets"][0]["template_fit"] == "hsd_game_recap_final_score_review"
    assert payload["render_prep_packets"][0]["selected_template_id"] == "hsd_game_recap_final_score_a"
    assert payload["render_prep_packets"][0]["template_family"] == "game_recap_final_score"
    assert payload["render_prep_packets"][0]["reference_pack_id"] == "templates_hsd_20260625"
    assert payload["render_prep_packets"][0]["template_shape"] == "IG feed 1080x1350 primary; story 1080x1920 and square review derivatives"
    assert payload["render_prep_packets"][0]["copy_headline"] == "New York Liberty beat Las Vegas Aces"
    assert "Verified final" in payload["render_prep_packets"][0]["copy_dek"]
    assert "Breanna Stewart" in payload["render_prep_packets"][0]["top_performers"]
    assert payload["render_prep_packets"][0]["stat_module_status"] == "verified_stat_text_available"
    assert payload["render_prep_packets"][0]["stat_source_confidence"] == "verified_stat_text_ready_manual_crosscheck_required"
    assert payload["render_prep_packets"][0]["stat_source_label"] == "Verified player/stat text available"
    assert "Confirm the named performer" in payload["render_prep_packets"][0]["stat_review_cue"]
    assert "exact local WNBA team logos" in payload["render_prep_packets"][0]["asset_requirement"]
    assert payload["render_prep_packets"][0]["active_logo_readiness_status"] == "hold_logo_review_required"
    assert "New York Liberty: unapproved_required_logo" in payload["render_prep_packets"][0]["active_logo_review_cues"]
    assert "WNBA: missing_or_unregistered_logo_asset" in payload["render_prep_packets"][0]["active_logo_review_cues"]
    assert payload["render_prep_packets"][0]["logo_review_artifact"] == "data/asset_registry/wnba/logo_review_packets.csv"
    assert "Renderer fallback remains review-only" in payload["render_prep_packets"][0]["renderer_fallback_cue"]
    assert payload["render_prep_packets"][0]["active_asset_stop_go"] == "hold_required_manual_asset_review"
    assert "source, format, and manual-path blockers are clear" in payload["render_prep_packets"][0]["manual_renderer_steps"]
    assert "active asset holds remain separate stop/go cues" in payload["render_prep_packets"][0]["manual_renderer_steps"]
    assert "Confirm active asset stop/go: hold_required_manual_asset_review." in payload["render_prep_packets"][0]["manual_renderer_steps"]
    assert "Confirm active logo readiness: hold_logo_review_required" in payload["render_prep_packets"][0]["manual_renderer_steps"]
    assert payload["render_prep_packets"][0]["active_athlete_identity_status"] == "hold_identity_review_required"
    assert "Breanna Stewart: hold_identity_review_required" in payload["render_prep_packets"][0]["active_athlete_identity_cues"]
    assert "default_approval_requires_identity_recheck" in payload["render_prep_packets"][0]["active_athlete_identity_cues"]
    assert payload["render_prep_packets"][0]["athlete_identity_artifact"] == "data/asset_registry/wnba/athlete_identity_review_packet.csv"
    assert "Confirm active athlete identity: hold_identity_review_required" in payload["render_prep_packets"][0]["manual_renderer_steps"]
    assert "Open news_fact_packets.csv" in payload["render_prep_packets"][0]["manual_renderer_steps"]
    assert payload["render_prep_packets"][0]["auto_render_status"] == "not_rendered_by_generator"
    assert payload["render_prep_packets"][0]["publish_policy"] == "review_only_not_publish_ready"
    assert payload["render_handoff_summary"]["handoff_status"] == "ready_for_manual_review"
    assert payload["render_handoff_summary"]["title"] == "New York Liberty beat Las Vegas Aces"
    assert payload["render_handoff_summary"]["active_asset_stop_go"] == "hold_required_manual_asset_review"
    assert payload["render_handoff_summary"]["readme"] == "render_handoff_top_packet/README.md"
    assert "render_handoff_top_packet/manual_renderer_prompt.md" in payload["render_handoff_summary"]["files"]
    assert payload["render_handoff_summary"]["guardrails"]["review_only"] is True
    assert payload["render_handoff_summary"]["guardrails"]["auto_approval"] is False
    assert payload["render_handoff_summary"]["guardrails"]["auto_render"] is False
    assert payload["render_handoff_summary"]["guardrails"]["auto_publish"] is False
    assert payload["render_handoff_summary"]["guardrails"]["asset_downloads"] is False
    assert payload["render_handoff_summary"]["guardrails"]["file_movement"] is False
    assert payload["render_handoff_summary"]["guardrails"]["paid_apis"] is False
    assert payload["render_handoff_summary"]["guardrails"]["publish_ready_lane"] is False
    assert payload["render_handoff_summary"]["guardrails"]["publishing"] is False
    assert any(
        item["label"] == "Decision stop/go"
        and item["value"] == "hold_selected_template_manual_asset_review"
        for item in payload["metrics"]
    )
    assert any(item["label"] == "Review-order checklist" and item["value"] == "5" for item in payload["metrics"])
    assert payload["decision_stop_go_summary"]["panel_status"] == "hold_selected_template_manual_asset_review"
    assert payload["decision_stop_go_summary"]["active_asset_stop_go"] == "hold_required_manual_asset_review"
    assert payload["decision_stop_go_summary"]["selected_template_blockers"] == 1
    assert payload["decision_stop_go_summary"]["selected_template_entities"] == "New York Liberty"
    assert payload["decision_stop_go_summary"]["future_photo_first_holds"] == 1
    assert payload["decision_stop_go_summary"]["future_photo_first_entities"] == "Breanna Stewart"
    assert payload["decision_stop_go_summary"]["league_mark_context_holds"] == 1
    assert payload["decision_stop_go_summary"]["league_mark_context_entities"] == "WNBA"
    assert payload["decision_stop_go_summary"]["active_queue_artifact"] == "render_handoff_top_packet/active_asset_review_queue.md"
    assert payload["decision_stop_go_summary"]["manual_asset_source_board_artifact"] == "render_handoff_top_packet/manual_asset_source_board.md"
    assert "no auto-approval" in payload["decision_stop_go_summary"]["guardrail_summary"]
    assert [row["title"] for row in payload["decision_review_order_checklist"]] == [
        "Open active asset queue",
        "Open Manual Asset Source Board",
        "Open Manual Logo Verification Intake Bridge",
        "Open Manual League-Mark Context Intake",
        "Open WNBA logo review catalog",
    ]
    assert payload["decision_review_order_checklist"][0]["artifact"] == "render_handoff_top_packet/active_asset_review_queue.md"
    assert payload["decision_review_order_checklist"][1]["artifact"] == "render_handoff_top_packet/manual_asset_source_board.md"
    assert payload["decision_review_order_checklist"][2]["artifact"] == "render_handoff_top_packet/manual_logo_verification_intake.md"
    assert payload["decision_review_order_checklist"][3]["artifact"] == "render_handoff_top_packet/manual_league_mark_context_intake.md"
    assert payload["decision_review_order_checklist"][4]["artifact"] == "data/asset_registry/wnba/logo_review_catalog_report.md"
    assert all(row["approval_state_change"] == "false" for row in payload["decision_review_order_checklist"])
    assert all(row["asset_downloads"] == "false" for row in payload["decision_review_order_checklist"])
    assert any(item["label"] == "Manual asset source board" and item["value"] == "3" for item in payload["metrics"])
    assert any(item["label"] == "Manual logo intake bridge" and item["value"] == "1" for item in payload["metrics"])
    assert any(item["label"] == "Manual league-mark intake bridge" and item["value"] == "1" for item in payload["metrics"])
    assert len(payload["manual_asset_source_board"]) == 3
    assert {row["entity_name"] for row in payload["manual_asset_source_board"]} == {"New York Liberty", "WNBA", "Breanna Stewart"}
    assert len(payload["manual_league_mark_context_intake"]) == 1
    wnba_league_intake = payload["manual_league_mark_context_intake"][0]
    assert wnba_league_intake["entity_name"] == "WNBA"
    assert wnba_league_intake["manual_intake_files"] == "data/asset_registry/wnba/wnba_league_mark_review_intake.csv"
    assert wnba_league_intake["template_requirement_rule"] == "non_blocking_until_selected_template_requires_league_mark"
    liberty_source = next(row for row in payload["manual_asset_source_board"] if row["entity_name"] == "New York Liberty")
    breanna_source = next(row for row in payload["manual_asset_source_board"] if row["entity_name"] == "Breanna Stewart")
    assert liberty_source["priority"] == "P0_selected_template_hold"
    assert liberty_source["official_source_candidate"] == "https://example.test/liberty-logo.png"
    assert liberty_source["manual_search_query"] == '"New York Liberty" official logo PNG WNBA'
    assert breanna_source["priority"] == "P1_future_photo_first_hold"
    assert breanna_source["official_source_candidate"] == "https://www.wnba.com/player/1627668/breanna-stewart"
    assert all(row["review_only"] == "true" for row in payload["manual_asset_source_board"])
    assert all(row["manual_approval_required"] == "true" for row in payload["manual_asset_source_board"])
    assert all(row["asset_downloads"] == "false" for row in payload["manual_asset_source_board"])
    assert len(payload["manual_logo_verification_intake"]) == 1
    liberty_intake = payload["manual_logo_verification_intake"][0]
    assert liberty_intake["entity_name"] == "New York Liberty"
    assert liberty_intake["local_logo_path"] == "assets/leagues/wnba/logos/new_york_liberty/logo.png"
    assert liberty_intake["official_source_candidate"] == "https://example.test/liberty-logo.png"
    assert liberty_intake["current_legacy_registry_source"] == "https://example.test/liberty-logo.png"
    assert liberty_intake["current_unapproved_status"] == "operator_logo_review_required"
    assert liberty_intake["manual_intake_files"] == "data/asset_registry/wnba/team_logos.csv|data/asset_registry/wnba/logo_sources.csv"
    assert liberty_intake["approval_state_change"] == "false"
    assert liberty_intake["asset_downloads"] == "false"
    assert payload["operator_decision_panel"]["qa_status"] == "human_review_required"
    assert payload["operator_decision_panel"]["validation_status"] == "awaiting_operator_decision"
    assert payload["operator_decision_panel"]["preview_exists"] is True
    assert payload["operator_decision_panel"]["inbox_exists"] is True
    assert payload["operator_decision_panel"]["inbox_rows"] == 0
    assert payload["operator_decision_panel"]["history_issue_count"] == 0
    assert [item["label"] for item in payload["operator_decision_panel"]["qa_cues"]][:2] == [
        "Title contrast and fit",
        "Score/team readability",
    ]
    assert payload["operator_decision_panel"]["qa_cues"][0]["tone"] == "good"
    assert "reference_white_gold_title" in payload["operator_decision_panel"]["qa_cues"][0]["evidence"]
    assert any(item["label"] == "Player ledger readability" for item in payload["operator_decision_panel"]["qa_cues"])
    assert [item["label"] for item in payload["operator_decision_panel"]["render_gallery"]] == ["Primary feed", "Story", "Square"]
    assert all(item["exists"] is True for item in payload["operator_decision_panel"]["render_gallery"])
    assert payload["operator_decision_panel"]["render_gallery"][1]["shape"] == "1080x1920"
    assert all(item["publish_ready"] == "false" for item in payload["operator_decision_panel"]["render_gallery"])
    assert all(item["auto_publish"] == "false" for item in payload["operator_decision_panel"]["render_gallery"])
    feed_gallery = payload["operator_decision_panel"]["render_gallery"][0]
    assert feed_gallery["template_status"] == "exact_reference_match"
    assert feed_gallery["reference_public_exists"] == "true"
    assert feed_gallery["reference_layout_exists"] == "true"
    assert "01_game_recap_final_score_variant_A_public.png" in feed_gallery["reference_public_href"]
    assert "02_game_recap_final_score_variant_A_layout_reference.png" in feed_gallery["reference_layout_href"]
    assert feed_gallery["logo_status"] == "logo_review_required"
    assert "New York Liberty: LOGO REVIEW" in feed_gallery["logo_detail"]
    assert "accent #247CA8" in feed_gallery["logo_detail"]
    assert "Las Vegas Aces: APPROVED LOGO" in feed_gallery["logo_detail"]
    assert feed_gallery["photo_status"] == "athlete_photo_ready"
    assert "APPROVED PHOTO" in feed_gallery["photo_summary"]
    assert "Breanna Stewart" in feed_gallery["photo_detail"]
    assert feed_gallery["photo_layout_mode"] == "photo_first_final_score"
    assert feed_gallery["photo_layout_status"] == "approved_photo_first_template"
    assert "main editorial visual" in feed_gallery["photo_layout_detail"]
    assert feed_gallery["source_status"] == "source_confidence_ready"
    assert feed_gallery["qa_cue_status"] == "qa_passed_manual_review_required"
    assert feed_gallery["visual_delta_status"] == "visual_delta_aligned_review"
    assert feed_gallery["visual_delta_score"] == "92"
    assert feed_gallery["revision_status"] == "manual_reference_check"
    assert feed_gallery["revision_focus"] == "Score/team lane balance"
    assert feed_gallery["stat_module_status"] == "verified_stat_text_ready_manual_crosscheck_required"
    assert "Verified player/stat text available" in feed_gallery["stat_module_summary"]
    assert "STEWART + CLEAR SEPARATION" in feed_gallery["stat_module_detail"]
    assert "score/stat-derived" in feed_gallery["stat_module_detail"]
    assert [cue["label"] for cue in feed_gallery["cue_rows"]] == ["Template", "Logos", "Photo", "Source", "Stats", "QA", "Visual delta", "Manual revision"]
    assert payload["operator_decision_panel"]["render_gallery"][2]["template_status"] == "derived_reference_review"
    assert payload["operator_decision_panel"]["render_gallery"][2]["photo_layout_mode"] == "compact_headshot_chip"
    assert payload["operator_decision_panel"]["render_gallery"][2]["visual_delta_status"] == "visual_delta_manual_warning"
    assert payload["operator_decision_panel"]["render_gallery"][2]["revision_status"] == "manual_revision_recommended"
    assert any(item["label"] == "QA report" and item["exists"] is True for item in payload["operator_decision_panel"]["file_shortcuts"])
    assert any(item["label"] == "Visual delta report" and item["exists"] is True for item in payload["operator_decision_panel"]["file_shortcuts"])
    assert any(item["label"] == "Revision plan" and item["exists"] is True for item in payload["operator_decision_panel"]["file_shortcuts"])
    assert any(item["label"] == "Decision inbox" and item["exists"] is True for item in payload["operator_decision_panel"]["file_shortcuts"])
    assert payload["operator_decision_panel"]["guardrails"]["auto_approval"] is False
    assert payload["operator_decision_panel"]["guardrails"]["auto_publish"] is False
    assert payload["source_discovery_board"][0]["title"] == "Public team social lead"
    assert payload["source_discovery_board"][0]["posture"] == "discovery_only"
    assert payload["source_discovery_board"][0]["freshness_source"] == "article_metadata"
    assert "Official metadata title for public team lead" in payload["source_discovery_board"][0]["detail"]
    assert payload["source_discovery_board"][0]["evidence_source"] == "article_metadata"
    assert payload["source_discovery_board"][0]["story_opportunity_size"] == "2"
    assert payload["source_discovery_board"][0]["story_opportunity_angle"] == "Roster or transaction update"
    assert payload["source_discovery_board"][0]["story_opportunity_recommended_path"] == "news_packet"
    assert payload["source_discovery_board"][0]["story_opportunity_confidence_tier"] == "needs_official_confirmation"
    assert payload["source_discovery_board"][0]["story_opportunity_source_coverage"] == "discovery_source_only"
    assert payload["source_discovery_board"][0]["story_opportunity_confirmation_cue"] == "needs_official_confirmation"
    assert payload["source_discovery_board"][0]["story_opportunity_asset_cue"] == "asset_not_required_for_news_packet"
    assert payload["source_discovery_board"][0]["story_opportunity_second_source_id"] == "wnba_official_news"
    assert payload["source_discovery_board"][0]["render_readiness_band"] == "hold_for_source_confirmation"
    assert payload["source_discovery_board"][0]["render_readiness_manual_path"] == "manual_review_artifact_ready:morning_source_discovery_board.csv"
    assert payload["lead_promotion_recommendations"][0]["recommendation"] == "manual_story_candidate"
    assert payload["lead_promotion_recommendations"][0]["freshness_source"] == "article_metadata"
    assert "A concise public metadata description" in payload["lead_promotion_recommendations"][0]["detail"]
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_sources"] == "wnba_official_news; ap_womens_sports_wire"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_angle"] == "Roster or transaction update"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_recommended_path"] == "news_packet"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_confidence_tier"] == "needs_official_confirmation"
    assert payload["lead_promotion_recommendations"][0]["story_opportunity_second_source_id"] == "wnba_official_news"
    assert payload["lead_promotion_recommendations"][0]["render_readiness_band"] == "hold_for_source_confirmation"
    assert payload["lead_promotion_recommendations"][0]["render_readiness_next_step"] == "Verify the second official, wire, or primary source before News, Studio, or render work."
    promote_action = next(action for action in payload["next_actions"] if action["title"] == "Promote source lead toward manual_story_candidate: Public team social lead")
    assert "needs_official_confirmation" in promote_action["detail"]
    assert "Suggested second source: wnba_official_news" in promote_action["detail"]
    news_candidate = next(item for item in payload["content_candidates"] if item["type"] == "News packet")
    assert news_candidate["source_grade"] == "publish_grade"
    assert news_candidate["source_score"] == "92"
    assert news_candidate["render_readiness_band"] == "render_ready_review"
    assert news_candidate["render_readiness_score"] == "100"
    artifact_by_path = {item["path"]: item for item in payload["artifacts"]}
    assert artifact_by_path["graphics_upload_pack_status.csv"]["run_command"] == ".\\hsd.cmd run -Mode asset"
    assert artifact_by_path["render_handoff_top_packet/draft_preview.png"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_handoff_top_packet/review_drafts/draft_preview_story.png"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_handoff_top_packet/review_drafts/draft_preview_square.png"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_review_renderer_report.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_visual_delta_report.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_visual_delta_manifest.json"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_visual_revision_plan.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["render_visual_revision_plan.json"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_report.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_checklist.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_approval_intake.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_approval_intake.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_draft.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_draft.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_template.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_template.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_intake.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_intake.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_post_approval_render_staging.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_post_approval_render_staging.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_walkthrough.md"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_walkthrough.csv"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_walkthrough.json"]["run_command"] == ".\\hsd.cmd run -Mode render"
    assert artifact_by_path["manual_visual_qa_operator_decision_inbox_starter.md"]["run_command"] == ".\\hsd.cmd run -Mode decision-inbox"
    assert artifact_by_path["manual_visual_qa_operator_decision_inbox_starter.csv"]["run_command"] == ".\\hsd.cmd run -Mode decision-inbox"
    assert artifact_by_path["manual_visual_qa_operator_decision_inbox_starter.json"]["run_command"] == ".\\hsd.cmd run -Mode decision-inbox"
    assert artifact_by_path["athlete_photo_onboarding/athlete_photo_onboarding_report.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py"
    assert artifact_by_path["athlete_photo_onboarding/athlete_photo_contact_sheet_index.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py"
    assert artifact_by_path["athlete_photo_onboarding/athlete_photo_onboarding_decision_template.csv"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_athlete_photo_onboarding_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/wnba_athlete_photo_contact_sheet_index.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_photo_contact_sheets_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/wnba_athlete_photo_review_intake.csv"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_photo_contact_sheets_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/athlete_identity_audit.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_wnba_athlete_identity_audit_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/athlete_identity_resolution_workflow.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/athlete_identity_review_packet.csv"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/athlete_identity_resolution_template.csv"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/athlete_identity_closure_packet.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_closure_packet_v1.py"
    assert artifact_by_path["data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\generate_hsd_wnba_athlete_identity_closure_packet_v1.py"
    assert artifact_by_path["identity_resolution_local_server.md"]["run_command"] == ".\\hsd.cmd run -Mode identity-decision"
    assert artifact_by_path["identity_resolution_local_server.json"]["run_command"] == ".\\hsd.cmd run -Mode identity-decision"
    assert artifact_by_path["identity_decision_live_writeback_verification.md"]["run_command"] == ".\\hsd.cmd run -Mode identity-decision-verify"
    assert artifact_by_path["identity_decision_live_writeback_verification.json"]["run_command"] == ".\\hsd.cmd run -Mode identity-decision-verify"
    assert artifact_by_path["data/asset_registry/asset_availability_audit.md"]["run_command"] == ".\\hsd.cmd run -Mode asset-audit"
    assert artifact_by_path["data/asset_registry/wnba/athlete_photo_catalog.md"]["run_command"] == ".\\hsd.cmd run -Mode asset-audit"
    assert artifact_by_path["data/asset_registry/wnba/logo_review_catalog_report.md"]["run_command"] == ".\\hsd.cmd run -Mode asset-audit"
    assert artifact_by_path["data/asset_registry/wnba/logo_review_packets.csv"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\validate_hsd_wnba_asset_registry_v1.py"
    assert artifact_by_path["data/asset_registry/logo_asset_catalog.md"]["run_command"] == ".\\.venv\\Scripts\\python.exe scripts\\report_hsd_logo_asset_catalog_v1.py"
    assert artifact_by_path["render_handoff_top_packet/active_asset_review_queue.md"]["status_detail"] == "Created with this command center run"
    assert artifact_by_path["render_handoff_top_packet/active_asset_review_queue.csv"]["status_detail"] == "Created with this command center run"
    assert artifact_by_path["results_dashboard/index.html"]["run_command"] == ".\\hsd.cmd run -Mode dashboards"
    assert artifact_by_path["source_registry_patch_preview.md"]["status_detail"] == "Ready to open"
    assert artifact_by_path["trusted_registry_operator_playbook.md"]["status_detail"] == "Ready to open"

    assert "HSD Daily Operator Command Center" in html
    assert 'data-tab-target="today"' in html
    assert 'data-tab-target="decision-panel"' in html
    assert 'data-tab-target="content"' in html
    assert 'data-tab-target="sources"' in html
    assert 'data-tab-target="safety"' in html
    assert 'data-tab-target="artifacts"' in html
    assert 'id="artifactSearch"' in html
    assert "Paid APIs and auto-publishing are off" in html
    assert "Run next" in html
    assert ".\\hsd.cmd run -Mode asset" in html
    assert ".\\hsd.cmd run -Mode render" in html
    assert "Next step" in html
    assert "publish_grade" in html
    assert "Public team social lead" in html
    assert "Official metadata title for public team lead" in html
    assert "A concise public metadata description for operator review." in html
    assert "opportunity: 2 source(s)" in html
    assert "angle: Roster or transaction update" in html
    assert "path: news_packet" in html
    assert "confidence: needs_official_confirmation" in html
    assert "coverage: discovery_source_only" in html
    assert "cue: needs_official_confirmation" in html
    assert "assets: asset_not_required_for_news_packet" in html
    assert "second source: wnba_official_news" in html
    assert "Source coverage map" in html
    assert "Source registry readiness" in html
    assert "blocked_post_edit_validation" in html
    assert "Open source_registry_post_edit_validation.md first" in html
    assert "pwhl_official_news: unsafe_hold" in html
    assert "Open next" in html
    assert "Source registry intake template" in html
    assert "Source registry diff review" in html
    assert "Hold for duplicate review" in html
    assert "Before filling approval fields" in html
    assert "Source registry same-domain resolution" in html
    assert "same_domain_ok_with_evidence_required_before_approval" in html
    assert "choose same_domain_ok" in html
    assert "duplicate_domain" in html
    assert "candidate domain already exists" in html
    assert "Source verification log" in html
    assert "follow diff review cue" not in html
    assert "operator_input_required" in html
    assert "operator fill-in" in html
    assert "Source registry approval packet" in html
    assert "hold_before_manual_registry_edit" in html
    assert "diff review is HOLD" in html
    assert "Source registry patch preview" in html
    assert "ready_for_manual_copy_paste" in html
    assert "wnba_official_home_review" in html
    assert "Source registry post-edit validation" in html
    assert "validated_exact_match" in html
    assert "unsafe_hold" in html
    assert "enabled_not_false" in html
    assert "Trusted registry operator playbook" in html
    assert "Source registry update worksheet" in html
    assert "manual_registry_plan_after_verification" in html
    assert "not_performed_by_generator" in html
    assert "remove the manually added" in html
    assert "Source proposal promotion checklist" in html
    assert "verify_then_copy" in html
    assert "discard_duplicate_candidate_do_not_copy" in html
    assert "Yes_after_manual_freshness_check" in html
    assert "Source proposal draft" in html
    assert "ready_to_copy_after_freshness_check" in html
    assert "blocked_duplicate_review" in html
    assert "manual_copy_to_inbox_after_freshness_check" in html
    assert "hold_do_not_copy_until_duplicate_review" in html
    assert "Guided source pack readiness" in html
    assert "ready_for_registry_proposal" in html
    assert "needs_duplicate_review" in html
    assert "needs_source_freshness_check" in html
    assert "espn_wnba_scoreboard_pack_review" in html
    assert "Guided source proposal packs" in html
    assert "PWHL Source Proposal Pack" in html
    assert "Source proposal review" in html
    assert "PWHL" in html
    assert "pwhl_official_scores" in html
    assert "pwhl_boston_fleet_team" in html
    assert "missing official league/team source" in html
    assert "proposal_only_do_not_import" in html
    assert "social-only source cannot be added" in html
    assert "wnba_official_news; ap_womens_sports_wire" in html
    assert "recent_30_days via article_metadata" in html
    assert "Lead promotion recommendations" in html
    assert "Render readiness" in html
    assert "Manual visual QA decision" in html
    assert "Primary draft preview" in html
    assert "Decision cockpit" in html
    assert "Inspect render" in html
    assert "Check evidence" in html
    assert "Record decision" in html
    assert "Visual delta warnings" in html
    assert "Manual decision controls" in html
    assert "Approve, hold, or revise" in html
    assert "Start here" in html
    assert "Use this dashboard for daily review" in html
    assert "Open Decision Desk" in html
    assert 'data-tab-jump="decision-panel"' in html
    assert "Secondary safety report" in html
    assert "Open guard report" in html
    assert "decisionCsvOutput" in html
    assert "decisionFieldWarnings" in html
    assert "Manual decision controls" in html
    assert "Decision history" in html
    assert "Open before deciding" in html
    assert "Visual QA cues" in html
    assert "Title contrast and fit" in html
    assert "title ink ratio" in html
    assert "Logo readiness" in html
    assert "Render gallery" in html
    assert "Public mockup" in html
    assert "Layout reference" in html
    assert "Primary feed" in html
    assert "Story" in html
    assert "Square" in html
    assert "review-only drafts" in html
    assert "publish ready: false" in html
    assert "QA report" in html
    assert "Source proof" in html
    assert "operatorDecision" in html
    assert "approve_for_manual_next_step" in html
    assert "Copy row" in html
    assert "file-backed manual approval" in html
    assert "manual_next_step_only_not_publish_ready" in html
    assert "operator/inbox/manual_visual_qa_operator_decisions.csv" in html
    assert "awaiting_operator_decision" in html
    assert "Render prep packets" in html
    assert "Top render handoff" in html
    assert "render_ready_review" in html
    assert "ready_for_manual_render_review" in html
    assert "hsd_game_recap_final_score_review" in html
    assert "human_visual_review_required_before_any_post" in html
    assert "render_handoff_top_packet/README.md" in html
    assert "Top render story draft" in html
    assert "Top render square draft" in html
    assert "manual_renderer_prompt.md" in html
    assert "hold_for_source_confirmation" in html
    assert "manual_review_artifact_ready:news_fact_packets.csv" in html
    assert "source_confidence_ready" in html
    assert "asset_not_required_for_news_packet" in html
    assert "Next actions" in markdown
    assert "Run: `.\\hsd.cmd run -Mode asset`." in markdown
    assert "Create with `.\\hsd.cmd run -Mode dashboards`" in markdown
    assert "source: publish_grade" in markdown
    assert "Manual Visual QA Decision UI" in markdown
    assert "Render gallery: Story | 1080x1920 | ready_for_visual_review" in markdown
    assert "file-backed manual approval" in markdown
    assert "awaiting_operator_decision" in markdown
    assert "History issues: 0" in markdown
    assert "Open: QA report" in markdown
    assert "Morning source discovery" in markdown
    assert "Source registry diff review" in markdown
    assert "cue: HOLD" in markdown
    assert "before log: Before filling approval fields" in markdown
    assert "Source registry same-domain resolution" in markdown
    assert "same_domain_ok_with_evidence_required_before_approval" in markdown
    assert "duplicate_domain" in markdown
    assert "candidate domain already exists" in markdown
    assert "Source verification log" in markdown
    assert "instruction: Resolve source_registry_same_domain_resolution.csv" in markdown
    assert "operator_input_required" in markdown
    assert "url_checked: operator fill-in" in markdown
    assert "Source registry approval packet" in markdown
    assert "hold_before_manual_registry_edit" in markdown
    assert "diff review is HOLD" in markdown
    assert "Source registry patch preview" in markdown
    assert "ready_for_manual_copy_paste" in markdown
    assert "wnba_official_home_review" in markdown
    assert "Source registry post-edit validation" in markdown
    assert "validated_exact_match" in markdown
    assert "unsafe_hold" in markdown
    assert "enabled_not_false" in markdown
    assert "trusted_registry_operator_playbook.md" in markdown
    assert "Source registry update worksheet" in markdown
    assert "manual_registry_plan_after_verification" in markdown
    assert "not_performed_by_generator" in markdown
    assert "Source proposal promotion checklist" in markdown
    assert "verify_then_copy" in markdown
    assert "discard" in markdown
    assert "Source proposal draft" in markdown
    assert "ready_to_copy_after_freshness_check" in markdown
    assert "Duplicate review required" in markdown
    assert "Guided source pack readiness" in markdown
    assert "needs_duplicate_review" in markdown
    assert "missing cross-check candidate" in markdown
    assert "opportunity: 2 source(s)" in markdown
    assert "angle: Roster or transaction update" in markdown
    assert "path: news_packet" in markdown
    assert "confidence: needs_official_confirmation" in markdown
    assert "coverage: discovery_source_only" in markdown
    assert "assets: asset_not_required_for_news_packet" in markdown
    assert "second source: wnba_official_news" in markdown
    assert "Source coverage map" in markdown
    assert "Source registry readiness" in markdown
    assert "Status: blocked_post_edit_validation" in markdown
    assert "Open first: source_registry_post_edit_validation.md" in markdown
    assert "pwhl_official_news: unsafe_hold" in markdown
    assert "Source registry intake template" in markdown
    assert "Guided source proposal packs" in markdown
    assert "PWHL Source Proposal Pack" in markdown
    assert "Source proposal review" in markdown
    assert "PWHL | gap" in markdown
    assert "pwhl_official_news" in markdown
    assert "pwhl_official_scores" in markdown
    assert "enabled: No | action: proposal_only_do_not_import" in markdown
    assert "pwhl_instagram | hold | flags: social_only" in markdown
    assert "PWHL league/team official pages" in markdown
    assert "preview: Official metadata title for public team lead" in markdown
    assert "recent_30_days via article_metadata" in markdown
    assert "Lead promotion recommendations" in markdown
    assert "Render readiness" in markdown
    assert "Render prep packets" in markdown
    assert "Top render handoff" in markdown
    assert "render_ready_review" in markdown
    assert "ready_for_manual_render_review" in markdown
    assert "hsd_game_recap_final_score_review" in markdown
    assert "render_handoff_top_packet/README.md" in markdown
    assert "hold_for_source_confirmation" in markdown
    assert "manual_review_artifact_ready:news_fact_packets.csv" in markdown
    assert "source confirmation required" in markdown
    assert "active logo: hold_logo_review_required" in markdown
    assert "New York Liberty: unapproved_required_logo" in markdown
    assert "active athlete: hold_identity_review_required" in markdown
    assert "active asset stop/go: hold_required_manual_asset_review" in markdown
    assert "Breanna Stewart: hold_identity_review_required" in markdown
    assert "blockers: none for source/format/manual path" in markdown
    assert "What blocks this render now?" in html
    assert "hold_selected_template_manual_asset_review" in html
    assert "Selected-template blockers" in html
    assert "Future photo-first holds" in html
    assert "League-mark context" in html
    assert "What Blocks This Render Now" in markdown
    assert "Selected-template blockers: 1 (New York Liberty)" in markdown
    assert "Future photo-first holds: 1 (Breanna Stewart)" in markdown
    assert "League-mark context: 1 (WNBA)" in markdown
    assert "Active queue: `render_handoff_top_packet/active_asset_review_queue.md`" in markdown
    assert "Manual source board: `render_handoff_top_packet/manual_asset_source_board.md`" in markdown
    assert "Guardrails: review-only; no downloads; no auto-approval; no file movement; no publishing; no publish-ready lane" in markdown
    assert "Open these in order" in html
    assert "Open active asset queue" in html
    assert "Open Manual Asset Source Board" in html
    assert "Open Manual Logo Verification Intake Bridge" in html
    assert "Open Manual League-Mark Context Intake" in html
    assert "Open WNBA logo review catalog" in html
    assert "render_handoff_top_packet/active_asset_review_queue.md" in html
    assert "render_handoff_top_packet/manual_asset_source_board.md" in html
    assert "render_handoff_top_packet/manual_logo_verification_intake.md" in html
    assert "render_handoff_top_packet/manual_league_mark_context_intake.md" in html
    assert "data/asset_registry/wnba/logo_review_catalog_report.md" in html
    assert "Open These In Order" in markdown
    assert "1. Open active asset queue" in markdown
    assert "2. Open Manual Asset Source Board" in markdown
    assert "3. Open Manual Logo Verification Intake Bridge" in markdown
    assert "4. Open Manual League-Mark Context Intake" in markdown
    assert "5. Open WNBA logo review catalog" in markdown
    assert "approval_change=false" in markdown
    assert "downloads=false" in markdown
    assert "Manual Asset Source Board" in html
    assert "Old HSD asset-index/DDG packet structure" in html
    assert "Manual Asset Source Board" in markdown
    assert "Manual Logo Verification Intake Bridge" in html
    assert "Manual Logo Verification Intake Bridge" in markdown
    assert "Manual League-Mark Context Intake" in html
    assert "Manual League-Mark Context Intake" in markdown
    assert "Source-board rows: 3" in markdown
    assert "Intake bridge rows: 1" in markdown
    assert "P0 selected-template holds: 1" in markdown
    assert "Future photo-first holds: 1" in markdown
    assert "Legacy reference: `D:\\Her Sports Daily` asset-index/DDG packet structure only; current board is review-only." in markdown
    assert "Source board row: P0_selected_template_hold | team_logo | New York Liberty" in markdown
    assert "downloads=false | approval=false | publish_ready=false" in markdown

    command_center.write_outputs(payload)
    assert Path("operator_command_center.html").exists()
    assert Path("operator_command_center.json").exists()
    assert Path("operator_command_center.md").exists()
    assert Path("render_prep_packets.md").exists()
    assert Path("render_prep_packets.csv").exists()
    assert Path("render_prep_packets.json").exists()
    assert Path("render_handoff_top_packet/README.md").exists()
    assert Path("render_handoff_top_packet/copy_sheet.md").exists()
    assert Path("render_handoff_top_packet/copy_sheet.csv").exists()
    assert Path("render_handoff_top_packet/asset_checklist.md").exists()
    assert Path("render_handoff_top_packet/asset_checklist.csv").exists()
    assert Path("render_handoff_top_packet/active_asset_review_queue.md").exists()
    assert Path("render_handoff_top_packet/active_asset_review_queue.csv").exists()
    assert Path("render_handoff_top_packet/manual_asset_source_board.md").exists()
    assert Path("render_handoff_top_packet/manual_asset_source_board.csv").exists()
    assert Path("render_handoff_top_packet/manual_logo_verification_intake.md").exists()
    assert Path("render_handoff_top_packet/manual_logo_verification_intake.csv").exists()
    assert Path("render_handoff_top_packet/manual_league_mark_context_intake.md").exists()
    assert Path("render_handoff_top_packet/manual_league_mark_context_intake.csv").exists()
    assert Path("render_handoff_top_packet/source_proof.md").exists()
    assert Path("render_handoff_top_packet/manual_renderer_prompt.md").exists()
    assert Path("render_handoff_top_packet/handoff_manifest.json").exists()
    readme = Path("render_handoff_top_packet/README.md").read_text(encoding="utf-8")
    assert "Active Review Holds" in readme
    assert "Logo readiness: `hold_logo_review_required`" in readme
    assert "Athlete identity: `hold_identity_review_required`" in readme
    assert "Active asset stop/go: `hold_required_manual_asset_review`" in readme
    assert "Active queue scope: `3` rows; selected-template blockers `1` (New York Liberty); future photo-first holds `1` (Breanna Stewart); league-mark context holds `1` (WNBA)." in readme
    assert "Breanna Stewart: hold_identity_review_required" in readme
    assert "do not approve assets or create a publish-ready lane" in readme
    assert "Selected-template scope: Player imagery is not required; athlete identity holds remain future photo-first review cues." in readme
    assert "5. `manual_logo_verification_intake.md`" in readme
    assert "6. `manual_league_mark_context_intake.md`" in readme
    active_queue = Path("render_handoff_top_packet/active_asset_review_queue.md").read_text(encoding="utf-8")
    assert "Active Asset Review Queue" in active_queue
    assert "## Summary" in active_queue
    assert "Total review rows: 3" in active_queue
    assert "Blocking selected template now: 1" in active_queue
    assert "Future photo-first holds: 1" in active_queue
    assert "League-mark context holds: 1" in active_queue
    assert "Blocking entities: New York Liberty" in active_queue
    assert "Future photo-first entities: Breanna Stewart" in active_queue
    assert "League-mark context entities: WNBA" in active_queue
    assert "Immediate manual path: clear the blocking selected-template rows first; future photo-first and league-mark context holds stay review-only." in active_queue
    assert "New York Liberty" in active_queue
    assert "Breanna Stewart" in active_queue
    assert "Evidence: Hold the logo slot until source and local file are manually checked." in active_queue
    assert "Evidence: approved marker decision_source=default" in active_queue
    assert "Review queue ID: `logo_packet_new_york_liberty_unapproved`" in active_queue
    assert "Review queue ID: `new_york_liberty_breanna_stewart`" in active_queue
    assert "Review queue ID: `asset_review_0605_league_logo_WNBA`" in active_queue
    assert "Review source: `data/asset_registry/wnba/logo_review_packets.csv`" in active_queue
    assert "Review source: `data/asset_registry/wnba/athlete_identity_review_packet.csv`" in active_queue
    assert "Review source: `data/asset_registry/asset_availability_audit.csv`" in active_queue
    assert "Review-only policy: logo_review_only_no_auto_approval_no_file_movement_no_publish_ready_lane" in active_queue
    assert "Review-only policy: manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane" in active_queue
    assert "Selected template blocker: `blocking_selected_template_logo_review`" in active_queue
    assert "Selected template blocker: `not_blocking_selected_template_league_mark_not_required`" in active_queue
    assert "Selected template blocker: `not_blocking_selected_template_photo_not_required`" in active_queue
    assert "Decision lane: `wnba_logo_review`" in active_queue
    assert "Source confidence: `source_missing_or_unregistered`" in active_queue
    assert "Manual approval status: `manual_review_required`" in active_queue
    assert "Asset readiness: `optional_league_logo_file_missing_review_only`" in active_queue
    assert "Blocker summary: WNBA: missing league mark" in active_queue
    assert "Manual review packet: `data/asset_registry/wnba/logo_review_catalog_report.md`" in active_queue
    assert "Operator copy target: `operator/assets/brand_logos/README.md`" in active_queue
    assert "Operator copy target: `data/asset_registry/wnba/wnba_league_mark_review_intake.csv`" in active_queue
    assert "Manual review packet: `data/asset_registry/wnba/athlete_identity_resolution_workflow.md`" in active_queue
    assert "Operator copy target: `operator/inbox/wnba_athlete_identity_resolution.csv`" in active_queue
    assert "Source check URL: https://example.test/liberty-logo.png" in active_queue
    assert "Provider player ID: `1627668`" in active_queue
    assert "Approved marker path: `assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved`" in active_queue
    assert "asset_downloads=false" in active_queue
    source_board = Path("render_handoff_top_packet/manual_asset_source_board.md").read_text(encoding="utf-8")
    assert "Manual Asset Source Board" in source_board
    assert "Legacy `D:\\Her Sports Daily` asset-index/DDG packets are reference shape only" in source_board
    assert "Official/free candidate: https://example.test/liberty-logo.png" in source_board
    assert "Official/free candidate: https://www.wnba.com/player/1627668/breanna-stewart" in source_board
    assert "Review order: clear P0 selected-template logo holds first" in source_board
    assert "asset_downloads=false" in source_board
    source_board_rows = list(csv.DictReader(Path("render_handoff_top_packet/manual_asset_source_board.csv").open(encoding="utf-8")))
    assert {row["entity_name"] for row in source_board_rows} == {"New York Liberty", "WNBA", "Breanna Stewart"}
    assert all(row["review_only"] == "true" for row in source_board_rows)
    assert all(row["manual_approval_required"] == "true" for row in source_board_rows)
    assert all(row["publish_ready"] == "false" for row in source_board_rows)
    assert all(row["auto_approval"] == "false" for row in source_board_rows)
    assert all(row["auto_publish"] == "false" for row in source_board_rows)
    assert all(row["move_files"] == "false" for row in source_board_rows)
    assert all(row["paid_apis"] == "false" for row in source_board_rows)
    assert all(row["asset_downloads"] == "false" for row in source_board_rows)
    logo_intake = Path("render_handoff_top_packet/manual_logo_verification_intake.md").read_text(encoding="utf-8")
    assert "Manual Logo Verification Intake Bridge" in logo_intake
    assert "Exact local logo path: `assets/leagues/wnba/logos/new_york_liberty/logo.png`" in logo_intake
    assert "Official source candidate: https://example.test/liberty-logo.png" in logo_intake
    assert "Current legacy registry source: https://example.test/liberty-logo.png" in logo_intake
    assert "Current unapproved status: `operator_logo_review_required`" in logo_intake
    assert "Human-edited manual intake files: `data/asset_registry/wnba/team_logos.csv|data/asset_registry/wnba/logo_sources.csv`" in logo_intake
    assert "approval_state_change=false" in logo_intake
    logo_intake_rows = list(csv.DictReader(Path("render_handoff_top_packet/manual_logo_verification_intake.csv").open(encoding="utf-8")))
    assert len(logo_intake_rows) == 1
    assert logo_intake_rows[0]["entity_name"] == "New York Liberty"
    assert logo_intake_rows[0]["approval_state_change"] == "false"
    assert logo_intake_rows[0]["asset_downloads"] == "false"
    league_intake = Path("render_handoff_top_packet/manual_league_mark_context_intake.md").read_text(encoding="utf-8")
    assert "Manual League-Mark Context Intake" in league_intake
    assert "Human-edited intake file: `data/asset_registry/wnba/wnba_league_mark_review_intake.csv`" in league_intake
    assert "Selected-template rule: keep WNBA league mark optional/non-blocking unless the selected template explicitly requires it." in league_intake
    assert "Template requirement rule: `non_blocking_until_selected_template_requires_league_mark`" in league_intake
    assert "approval_state_change=false" in league_intake
    league_intake_rows = list(csv.DictReader(Path("render_handoff_top_packet/manual_league_mark_context_intake.csv").open(encoding="utf-8")))
    assert len(league_intake_rows) == 1
    assert league_intake_rows[0]["entity_name"] == "WNBA"
    assert league_intake_rows[0]["manual_intake_files"] == "data/asset_registry/wnba/wnba_league_mark_review_intake.csv"
    assert league_intake_rows[0]["approval_state_change"] == "false"
    assert league_intake_rows[0]["asset_downloads"] == "false"
    active_queue_rows = list(csv.DictReader(Path("render_handoff_top_packet/active_asset_review_queue.csv").open(encoding="utf-8")))
    assert {row["entity_name"] for row in active_queue_rows} == {"New York Liberty", "WNBA", "Breanna Stewart"}
    liberty_queue = next(row for row in active_queue_rows if row["entity_name"] == "New York Liberty")
    assert liberty_queue["registered_path"] == "assets/leagues/wnba/logos/new_york_liberty/logo.png"
    assert liberty_queue["source_target_path"] == "assets/leagues/wnba/teams/new_york_liberty/logo.svg"
    assert liberty_queue["source_check_url"] == "https://example.test/liberty-logo.png"
    assert liberty_queue["manual_review_packet"] == "data/asset_registry/wnba/logo_review_catalog_report.md"
    assert liberty_queue["operator_copy_target"] == "operator/assets/brand_logos/README.md"
    assert liberty_queue["allowed_decisions"] == "verify_logo_for_review_renders|hold_logo_slot|revise_logo_source_metadata"
    breanna_queue = next(row for row in active_queue_rows if row["entity_name"] == "Breanna Stewart")
    assert breanna_queue["asset_path"] == "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png"
    assert breanna_queue["source_check_url"] == "https://www.wnba.com/player/1627668/breanna-stewart"
    assert breanna_queue["provider_player_id"] == "1627668"
    assert breanna_queue["approved_marker_path"] == "assets/leagues/wnba/athletes/new_york_liberty_breanna_stewart/headshot.png.approved"
    assert breanna_queue["manual_review_packet"] == "data/asset_registry/wnba/athlete_identity_resolution_workflow.md"
    assert breanna_queue["operator_copy_target"] == "operator/inbox/wnba_athlete_identity_resolution.csv"
    wnba_queue = next(row for row in active_queue_rows if row["entity_name"] == "WNBA")
    assert wnba_queue["review_queue_id"] == "asset_review_0605_league_logo_WNBA"
    assert wnba_queue["decision_lane"] == "wnba_logo_review"
    assert wnba_queue["default_operator_decision"] == "hold_league_mark"
    assert wnba_queue["source_confidence"] == "source_missing_or_unregistered"
    assert wnba_queue["manual_approval_status"] == "manual_review_required"
    assert wnba_queue["asset_readiness"] == "optional_league_logo_file_missing_review_only"
    assert wnba_queue["selected_template_blocking_status"] == "not_blocking_selected_template_league_mark_not_required"
    assert wnba_queue["blocker_summary"] == "WNBA: missing league mark; default decision=hold_league_mark; readiness=optional_league_logo_file_missing_review_only"
    assert wnba_queue["allowed_decisions"] == "verify_league_mark_for_review_only_renderer_use|hold_league_mark|mark_not_required_for_selected_template|revise_league_mark_source_metadata"
    assert wnba_queue["primary_action"] == "fill_league_mark_context_intake_or_mark_not_required_for_selected_template"
    assert wnba_queue["manual_review_packet"] == "data/asset_registry/wnba/logo_review_catalog_report.md"
    assert wnba_queue["operator_copy_target"] == "data/asset_registry/wnba/wnba_league_mark_review_intake.csv"
    assert wnba_queue["registered_path"] == "assets/leagues/wnba/logos/league/wnba.png"
    assert wnba_queue["source_target_path"] == "assets/leagues/wnba/logos/league/wnba.png"
    assert all(row["publish_ready"] == "false" for row in active_queue_rows)
    assert all(row["auto_approval"] == "false" for row in active_queue_rows)
    assert all(row["auto_publish"] == "false" for row in active_queue_rows)
    assert all(row["move_files"] == "false" for row in active_queue_rows)
    assert all(row["paid_apis"] == "false" for row in active_queue_rows)
    assert all(row["asset_downloads"] == "false" for row in active_queue_rows)
    assert "Manual Renderer Steps" in Path("render_prep_packets.md").read_text(encoding="utf-8")
    assert "Blockers: none for source/format/manual path; active asset holds remain" in Path("render_prep_packets.md").read_text(encoding="utf-8")
    assert "New York Liberty beat Las Vegas Aces" in Path("render_handoff_top_packet/copy_sheet.md").read_text(encoding="utf-8")
    asset_checklist = Path("render_handoff_top_packet/asset_checklist.md").read_text(encoding="utf-8")
    assert "exact local WNBA team logos" in asset_checklist
    assert "Selected-template scope: Player imagery is not required; athlete identity holds remain future photo-first review cues." in asset_checklist
    assert "Active logo readiness: `hold_logo_review_required`" in asset_checklist
    assert "Active asset stop/go: `hold_required_manual_asset_review`" in asset_checklist
    assert "New York Liberty: unapproved_required_logo" in asset_checklist
    assert "WNBA: missing_or_unregistered_logo_asset" in asset_checklist
    assert "Active athlete identity: `hold_identity_review_required`" in asset_checklist
    assert "Breanna Stewart: hold_identity_review_required" in asset_checklist
    assert "athlete_identity_review_packet.csv" in asset_checklist
    assert "Renderer fallback remains review-only" in asset_checklist
    assert "HOLD this selected-template render if required team logos, source proof, format fit, or manual-path evidence is uncertain." in asset_checklist
    assert "Keep future photo-first and optional league-mark issues review-only; they do not approve assets or create a publish-ready lane." in asset_checklist
    assert "HOLD if any team, player, league, source, crop, or identity asset is uncertain." not in asset_checklist
    assert "Open news_fact_packets.csv" in Path("render_handoff_top_packet/source_proof.md").read_text(encoding="utf-8")
    manual_prompt = Path("render_handoff_top_packet/manual_renderer_prompt.md").read_text(encoding="utf-8")
    assert "Use this prompt manually only" in manual_prompt
    assert "Active asset stop/go: hold_required_manual_asset_review" in manual_prompt
    assert "Selected-template scope: Player imagery is not required; athlete identity holds remain future photo-first review cues." in manual_prompt
    assert "Review order: clear selected-template blockers first; future photo-first and league-mark context holds stay review-only." in manual_prompt
    assert "Active logo readiness: hold_logo_review_required" in manual_prompt
    assert "Active athlete identity: hold_identity_review_required" in manual_prompt
    render_prep_manifest = json.loads(Path("render_prep_packets.json").read_text(encoding="utf-8"))
    assert render_prep_manifest["guardrails"]["auto_render"] is False
    assert render_prep_manifest["guardrails"]["auto_publish"] is False
    render_handoff_manifest = json.loads(Path("render_handoff_top_packet/handoff_manifest.json").read_text(encoding="utf-8"))
    assert render_handoff_manifest["packet"]["active_asset_stop_go"] == "hold_required_manual_asset_review"
    assert render_handoff_manifest["packet"]["raw_blockers"] == "none"
    assert render_handoff_manifest["packet"]["blockers"] == "none for source/format/manual path; active asset holds remain"
    assert render_handoff_manifest["guardrails"]["review_only"] is True
    assert render_handoff_manifest["guardrails"]["auto_approval"] is False
    assert render_handoff_manifest["guardrails"]["auto_render"] is False
    assert render_handoff_manifest["guardrails"]["auto_publish"] is False
    assert render_handoff_manifest["guardrails"]["asset_downloads"] is False
    assert render_handoff_manifest["guardrails"]["file_movement"] is False
    assert render_handoff_manifest["guardrails"]["paid_apis"] is False
    assert render_handoff_manifest["guardrails"]["publish_ready_lane"] is False
    assert render_handoff_manifest["guardrails"]["publishing"] is False
    assert render_handoff_manifest["packet"]["packet_id"] == payload["render_prep_packets"][0]["packet_id"]
    assert render_handoff_manifest["manual_asset_source_board"]["rows"] == 3
    assert render_handoff_manifest["manual_asset_source_board"]["review_only"] is True
    assert render_handoff_manifest["manual_asset_source_board"]["manual_approval_required"] is True
    assert render_handoff_manifest["manual_asset_source_board"]["asset_downloads"] is False
    assert render_handoff_manifest["manual_asset_source_board"]["auto_approval"] is False
    assert "manual_asset_source_board.md" in render_handoff_manifest["files"]
    assert render_handoff_manifest["manual_logo_verification_intake"]["rows"] == 1
    assert render_handoff_manifest["manual_logo_verification_intake"]["review_only"] is True
    assert render_handoff_manifest["manual_logo_verification_intake"]["approval_state_change"] is False
    assert render_handoff_manifest["manual_logo_verification_intake"]["asset_downloads"] is False
    assert render_handoff_manifest["manual_logo_verification_intake"]["auto_approval"] is False
    assert "manual_logo_verification_intake.md" in render_handoff_manifest["files"]
    assert render_handoff_manifest["manual_league_mark_context_intake"]["rows"] == 1
    assert render_handoff_manifest["manual_league_mark_context_intake"]["review_only"] is True
    assert render_handoff_manifest["manual_league_mark_context_intake"]["approval_state_change"] is False
    assert render_handoff_manifest["manual_league_mark_context_intake"]["asset_downloads"] is False
    assert render_handoff_manifest["manual_league_mark_context_intake"]["auto_approval"] is False
    assert render_handoff_manifest["manual_league_mark_context_intake"]["template_requirement_rule"] == "non_blocking_until_selected_template_requires_league_mark"
    assert "manual_league_mark_context_intake.md" in render_handoff_manifest["files"]


def test_operator_command_center_identity_resolution_requires_full_renderer_clearance_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    seed_manual_visual_qa_decision_files()
    write_identity_resolution_inbox(provider_player_id_verified="no", backfill_provider_player_id="", publish_ready="true")

    payload = command_center.build_payload()
    row = payload["athlete_photo_onboarding_panel"]["review_rows"][0]

    assert payload["athlete_photo_onboarding_panel"]["panel_status"] != "identity_resolution_cleared_review_only"
    assert row["identity_review_status"] == "hold_identity_review_required"
    assert row["identity_resolution_status"] == "resolution_incomplete_or_hold"
    assert row["identity_resolution_next_step"] == "Keep photo-first rendering held until evidence, operator, and resolution fields are complete."


def test_athlete_photo_panel_prioritizes_identity_packets_before_onboarding(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    packet = {
        "review_packet_id": "atlanta_dream_aaliyah_nye",
        "athlete_id": "atlanta_dream_aaliyah_nye",
        "display_name": "Aaliyah Nye",
        "team_id": "atlanta_dream",
        "provider_player_id": "1642801",
        "asset_path": "assets/leagues/wnba/athletes/atlanta_dream_aaliyah_nye/headshot.png",
        "approved_marker_path": "assets/leagues/wnba/athletes/atlanta_dream_aaliyah_nye/headshot.png.approved",
        "identity_review_status": "hold_identity_review_required",
        "review_required": "true",
        "identity_hold": "true",
        "default_approval_present": "true",
        "highest_severity": "high",
        "issue_count": "2",
        "hold_reason_codes": "default_approval_requires_identity_recheck",
        "focused_evidence": "approved marker decision_source=default",
        "source_check_url": "https://www.wnba.com/player/1642801/aaliyah-nye",
        "provider_player_page_hint": "https://www.wnba.com/player/1642801/aaliyah-nye",
        "operator_review_steps": "open_asset_and_marker; compare_to_official_player_or_team_source; choose_hold_or_verified_review_only_decision",
        "allowed_decisions": "hold_identity|revise_asset|backfill_provider_id_only|identity_verified_approved_for_review_renders",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
        "review_only_policy": "manual_identity_resolution_only_no_auto_approval_no_file_movement_no_publish_ready_lane",
    }
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_review_packet.csv",
        [packet],
        list(packet.keys()),
    )

    panel = command_center.athlete_photo_onboarding_panel({})

    assert panel["panel_status"] == "identity_resolution_required"
    assert panel["identity_review_packet_rows"] == 1
    assert panel["identity_review_packet_hold_rows"] == 1
    assert panel["identity_review_packet_default_rows"] == 1
    assert "athlete_identity_review_packet.csv" in panel["next_step"]


def test_command_center_surfaces_missing_asset_packet_freshness_cues(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/asset_registry").mkdir(parents=True)
    Path("data/asset_registry/wnba").mkdir(parents=True)
    write_json(
        "data/asset_registry/asset_availability_audit.json",
        {
            "status": "review_required",
            "finding_count": 1,
            "severity_counts": {"warning": 1},
            "asset_domain_counts": {"team_logo": 1},
            "finding_counts": {"logo_present_without_complete_approval": 1},
            "findings": [
                {
                    "asset_domain": "team_logo",
                    "entity_name": "New York Liberty",
                    "entity_id": "new_york_liberty",
                    "finding": "logo_present_without_complete_approval",
                    "recommended_next_step": "human_review_required_before_renderer_logo_use",
                    "renderer_fallback_cue": "review_only_logo_hold",
                }
            ],
            "policy": {
                "no_paid_apis": True,
                "no_asset_downloads": True,
                "no_auto_approval": True,
                "no_file_movement_into_publish_ready_lanes": True,
                "no_publishing": True,
            },
        },
    )

    asset_panel = command_center.asset_availability_readiness_panel()
    athlete_panel = command_center.athlete_photo_onboarding_panel({})
    asset_html = command_center.render_asset_readiness_panel(asset_panel)
    athlete_html = command_center.render_athlete_photo_onboarding_panel(athlete_panel)

    assert asset_panel["panel_status"] == "review_required"
    assert asset_panel["logo_review_packet_rows"] == 0
    assert asset_panel["logo_review_packet_freshness_status"] == "packet_missing"
    assert "active holds may still be visible" in asset_panel["logo_review_packet_freshness_detail"]
    assert "scripts\\validate_hsd_wnba_asset_registry_v1.py" in asset_panel["logo_review_packet_refresh_command"]
    assert "Logo review packet freshness" in asset_html
    assert "packet_missing" in asset_html

    assert athlete_panel["panel_status"] == "not_run"
    assert athlete_panel["identity_review_packet_rows"] == 0
    assert athlete_panel["identity_review_packet_freshness_status"] == "packet_missing"
    assert "active holds may still be visible" in athlete_panel["identity_review_packet_freshness_detail"]
    assert "scripts\\generate_hsd_wnba_athlete_identity_resolution_v1.py" in athlete_panel["identity_review_packet_refresh_command"]
    assert "Identity review packet freshness" in athlete_html
    assert "packet_missing" in athlete_html


def test_athlete_photo_panel_surfaces_identity_closure_packet_breakdown(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/asset_registry/wnba").mkdir(parents=True, exist_ok=True)
    closure_report = {
        "report": {
            "status": "manual_identity_closure_ready",
            "closure_rows": 2,
            "backfill_rows": 2,
        }
    }
    write_json("data/asset_registry/wnba/athlete_identity_closure_packet.json", closure_report)
    closure_rows = [
        {
            "issue_key": "issue_high",
            "severity": "high",
            "issue_code": "approved_asset_still_has_pending_match_review",
            "athlete_id": "atlanta_dream_aaliyah_nye",
            "display_name": "Aaliyah Nye",
            "team_id": "atlanta_dream",
            "operator_closure_decision": "",
            "review_only_policy": "manual_closure_packet_only_no_auto_approval_no_registry_write_no_file_movement_no_publish_ready_lane",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "publish_ready": "false",
        },
        {
            "issue_key": "issue_low",
            "severity": "low",
            "issue_code": "provider_id_missing_from_registry",
            "athlete_id": "atlanta_dream_aaliyah_nye",
            "display_name": "Aaliyah Nye",
            "team_id": "atlanta_dream",
            "operator_closure_decision": "",
            "review_only_policy": "manual_closure_packet_only_no_auto_approval_no_registry_write_no_file_movement_no_publish_ready_lane",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "publish_ready": "false",
        },
    ]
    backfill_rows = [
        {
            "backfill_key": "image_row",
            "target_csv": "data/asset_registry/wnba/athlete_images.csv",
            "athlete_id": "atlanta_dream_aaliyah_nye",
            "display_name": "Aaliyah Nye",
            "team_id": "atlanta_dream",
            "target_field": "provider_player_id",
            "proposed_value": "1642801",
            "backfill_status": "manual_review_required",
            "operator_decision": "",
            "review_only_policy": "manual_closure_packet_only_no_auto_approval_no_registry_write_no_file_movement_no_publish_ready_lane",
            "auto_apply": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "publish_ready": "false",
        },
        {
            "backfill_key": "athlete_row",
            "target_csv": "data/asset_registry/wnba/athletes.csv",
            "athlete_id": "atlanta_dream_aaliyah_nye",
            "display_name": "Aaliyah Nye",
            "team_id": "atlanta_dream",
            "target_field": "provider_player_id",
            "proposed_value": "1642801",
            "backfill_status": "manual_review_required",
            "operator_decision": "",
            "review_only_policy": "manual_closure_packet_only_no_auto_approval_no_registry_write_no_file_movement_no_publish_ready_lane",
            "auto_apply": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "publish_ready": "false",
        },
    ]
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_issue_closure_template.csv",
        closure_rows,
        list(closure_rows[0].keys()),
    )
    write_csv_with_fields(
        "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv",
        backfill_rows,
        list(backfill_rows[0].keys()),
    )

    panel = command_center.athlete_photo_onboarding_panel({})
    html = command_center.render_athlete_photo_onboarding_panel(panel)

    assert panel["identity_closure_status"] == "manual_identity_closure_ready"
    assert panel["identity_closure_rows"] == 2
    assert panel["identity_provider_backfill_rows"] == 2
    assert panel["identity_closure_high_rows"] == 1
    assert panel["identity_closure_blank_decisions"] == 2
    assert panel["identity_provider_backfill_manual_review_rows"] == 2
    assert panel["identity_provider_backfill_blank_decisions"] == 2
    assert panel["identity_closure_severity_counts"][0] == {"label": "high", "rows": "1"}
    assert panel["identity_provider_backfill_status_counts"][0] == {"label": "manual_review_required", "rows": "2"}
    assert "Identity closure/backfill packet" in html
    assert "Closure severity" in html
    assert "Backfill targets" in html
    assert "manual backfill rows" in html
    assert "review-only" in html


def test_operator_command_center_identity_resolution_clears_only_with_full_manual_guardrails(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    seed_manual_visual_qa_decision_files()
    write_identity_resolution_inbox()

    payload = command_center.build_payload()
    row = payload["athlete_photo_onboarding_panel"]["review_rows"][0]

    assert payload["athlete_photo_onboarding_panel"]["panel_status"] == "identity_resolution_cleared_review_only"
    assert payload["athlete_photo_onboarding_panel"]["next_step"] == "Renderer can use the photo for review drafts only; still complete visual QA before any next step."
    assert row["identity_review_status"] == "identity_resolution_cleared_for_review_renders"
    assert row["identity_review_tone"] == "good"
    assert row["identity_resolution_status"] == "resolution_cleared_for_review_renders"
    assert row["identity_resolution_next_step"] == "Renderer may use this photo only for review drafts."
    assert row["publish_ready"] == "false"
    assert row["auto_approval"] == "false"


def test_operator_decision_review_desk_flags_malformed_paste(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    seed_manual_visual_qa_decision_files()
    draft_lines = Path("manual_visual_qa_operator_decision_draft.csv").read_text(encoding="utf-8").splitlines()
    malformed_row = '"' + draft_lines[1].replace('"', '""') + '",' + ",".join([""] * (len(DECISION_FIELDS) - 1))
    Path("operator/inbox/manual_visual_qa_operator_decisions.csv").write_text(
        draft_lines[0] + "\n" + malformed_row + "\n",
        encoding="utf-8",
    )

    payload = command_center.build_payload()
    html = command_center.render_html(payload)
    markdown = command_center.render_markdown(payload)
    history = payload["operator_decision_panel"]["decision_history"]

    assert payload["operator_decision_panel"]["inbox_rows"] == 1
    assert payload["operator_decision_panel"]["history_issue_count"] == 1
    assert history[0]["row_status"] == "replace_row"
    assert history[0]["cue"] == "replace"
    assert "pasted as one quoted cell" in history[0]["validation_issue"]
    assert "copy a fresh row" in payload["operator_decision_panel"]["next_step"].lower()
    assert "replace_row" in html
    assert "Decision history" in html
    assert "Do not paste the header row" in html
    assert "History row 1: replace_row" in markdown


def test_operator_decision_review_desk_marks_valid_decision_no_action_needed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    seed_manual_visual_qa_decision_files()
    draft = next(csv.DictReader(Path("manual_visual_qa_operator_decision_draft.csv").open(newline="", encoding="utf-8")))
    draft["operator_decision"] = "approve_for_manual_next_step"
    draft["operator_notes"] = "Preview, QA report, copy sheet, and source proof reviewed."
    draft["operator_name"] = "Mike"
    draft["reviewed_at_local"] = "6/25/2026, 12:32:54 PM"
    write_csv_with_fields("operator/inbox/manual_visual_qa_operator_decisions.csv", [draft], DECISION_FIELDS)
    intake_row = {
        "decision_draft_id": draft["decision_draft_id"],
        "validation_status": "valid_operator_decision",
        "operator_decision": draft["operator_decision"],
        "operator_notes": draft["operator_notes"],
        "operator_name": draft["operator_name"],
        "reviewed_at_local": draft["reviewed_at_local"],
    }
    write_csv("manual_visual_qa_operator_decision_intake.csv", [intake_row])
    write_json("manual_visual_qa_operator_decision_intake.json", {"status": "valid_operator_decision_ready_for_staging"})

    payload = command_center.build_payload()
    html = command_center.render_html(payload)

    assert payload["operator_decision_panel"]["has_valid_decision"] is True
    assert payload["operator_decision_panel"]["history_issue_count"] == 0
    assert 'data-has-valid-decision="true"' in html
    assert "A valid inbox decision is already recorded" in html
    assert "Manual decision controls" in html


def test_operator_command_center_does_not_refresh_handoff_as_side_effect(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    Path("generate_hsd_mermaid_handoff_publisher_v2_6_1.py").write_text(
        "from pathlib import Path\nPath('unexpected_refresh_marker.txt').write_text('ran')\n",
        encoding="utf-8",
    )

    command_center.write_outputs(command_center.build_payload())

    assert not Path("unexpected_refresh_marker.txt").exists()


def test_operator_command_center_infers_legacy_packet_source_grade(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed_daily_ops_files()
    write_csv(
        "news_fact_packets.csv",
        [
            {
                "urgency": "P1",
                "headline": "New York Liberty beat Las Vegas Aces",
                "production_ready": "Yes",
                "caption_hard_fact": "Verified final: New York Liberty 87, Las Vegas Aces 76.",
                "source_count": "4",
                "primary_source_count": "2",
            }
        ],
    )

    payload = command_center.build_payload()

    assert any(item["label"] == "Publish-grade packets" and item["value"] == "1" for item in payload["metrics"])
    news_candidate = next(item for item in payload["content_candidates"] if item["type"] == "News packet")
    assert news_candidate["source_grade"] == "publish_grade"
    assert news_candidate["source_reason"] == "Legacy packet inferred from production-ready status and primary source count"


def test_local_runner_collects_daily_command_center_artifacts() -> None:
    runner = (REPO / "scripts" / "hsd_local.ps1").read_text(encoding="utf-8")
    assert "operator_command_center.html" in runner
    assert "operator_command_center.md" in runner
    assert "operator_command_center.json" in runner
    assert "render_prep_packets.md" in runner
    assert "render_prep_packets.csv" in runner
    assert "render_prep_packets.json" in runner
    assert "render_handoff_top_packet/README.md" in runner
    assert "render_handoff_top_packet/manual_renderer_prompt.md" in runner
    assert "render_handoff_top_packet/draft_preview.png" in runner
    assert "manual_review_renderer_report.md" in runner
    assert "manual_review_renderer_manifest.json" in runner
    assert "manual_visual_qa_report.md" in runner
    assert "manual_visual_qa_manifest.json" in runner
    assert "manual_visual_qa_checklist.csv" in runner
    assert "manual_visual_qa_approval_intake.md" in runner
    assert "manual_visual_qa_approval_intake.csv" in runner
    assert "manual_visual_qa_approval_intake.json" in runner
    assert "manual_visual_qa_operator_decision_draft.md" in runner
    assert "manual_visual_qa_operator_decision_draft.csv" in runner
    assert "manual_visual_qa_operator_decision_draft.json" in runner
    assert "manual_visual_qa_operator_decision_template.md" in runner
    assert "manual_visual_qa_operator_decision_template.csv" in runner
    assert "manual_visual_qa_operator_decision_template.json" in runner
    assert "manual_visual_qa_operator_decision_intake.md" in runner
    assert "manual_visual_qa_operator_decision_intake.csv" in runner
    assert "manual_visual_qa_operator_decision_intake.json" in runner
    assert "manual_post_approval_render_staging.md" in runner
    assert "manual_post_approval_render_staging.csv" in runner
    assert "manual_post_approval_render_staging.json" in runner
    assert "manual_visual_qa_operator_decision_walkthrough.md" in runner
    assert "manual_visual_qa_operator_decision_walkthrough.csv" in runner
    assert "manual_visual_qa_operator_decision_walkthrough.json" in runner
    assert "manual_visual_qa_operator_decision_inbox_starter.md" in runner
    assert "manual_visual_qa_operator_decision_inbox_starter.csv" in runner
    assert "manual_visual_qa_operator_decision_inbox_starter.json" in runner
    assert "bebe_posting_schedule_today.md" in runner
    assert "preview_bundle_quality_summary.csv" in runner
    assert "publish_guard_report.json" in runner
    assert "source_registry_audit.md" in runner
    assert "source_registry_audit.json" in runner
    assert "morning_source_discovery_board.md" in runner
    assert "morning_source_discovery_board.csv" in runner
    assert "morning_source_discovery_board.json" in runner
    assert "morning_lead_promotion_recommendations.md" in runner
    assert "morning_lead_promotion_recommendations.csv" in runner
    assert "morning_lead_promotion_recommendations.json" in runner
    assert "source_coverage_map.csv" in runner
    assert "source_registry_intake_template.md" in runner
    assert "source_registry_intake_template.csv" in runner
    assert "source_registry_proposal_review.md" in runner
    assert "source_registry_proposal_review.csv" in runner
    assert "source_registry_proposal_draft.md" in runner
    assert "source_registry_proposal_draft.csv" in runner
    assert "source_registry_proposal_promotion_checklist.md" in runner
    assert "source_registry_proposal_promotion_checklist.csv" in runner
    assert "source_registry_update_worksheet.md" in runner
    assert "source_registry_update_worksheet.csv" in runner
    assert "source_registry_diff_review.md" in runner
    assert "source_registry_diff_review.csv" in runner
    assert "source_registry_same_domain_resolution.md" in runner
    assert "source_registry_same_domain_resolution.csv" in runner
    assert "source_registry_verification_log.md" in runner
    assert "source_registry_verification_log.csv" in runner
    assert "source_registry_approval_packet.md" in runner
    assert "source_registry_approval_packet.csv" in runner
    assert "source_registry_patch_preview.md" in runner
    assert "source_registry_patch_preview.csv" in runner
    assert "source_registry_post_edit_validation.md" in runner
    assert "source_registry_post_edit_validation.csv" in runner
    assert "trusted_registry_operator_playbook.md" in runner
    assert "source_proposal_pack_readiness.md" in runner
    assert "source_proposal_pack_readiness.csv" in runner
    assert "source_proposal_packs.md" in runner
    assert "source_proposal_packs.csv" in runner
    assert "wnba_source_proposal_pack.md" in runner
    assert "wnba_source_proposal_pack.csv" in runner
    assert "nwsl_source_proposal_pack.md" in runner
    assert "nwsl_source_proposal_pack.csv" in runner
    assert "lpga_source_proposal_pack.md" in runner
    assert "lpga_source_proposal_pack.csv" in runner
    assert "pwhl_source_proposal_pack.md" in runner
    assert "pwhl_source_proposal_pack.csv" in runner
    assert "manual_workflow_handoff.md" in runner
    assert "manual_workflow_pack_status.csv" in runner
    assert "ig_story_results_queue.csv" in runner
    assert "ig_story_results_upload_pack_status.csv" in runner
    assert "final_score_story_guard_report.md" in runner
    assert "multi_post_daily_board.md" in runner
    assert "post_slot_status.csv" in runner
    assert "ig_feed_queue.csv" in runner
    assert "threads_queue.csv" in runner
    assert "launch_command_center.md" in runner
    assert "launch_instagram_publish_queue.csv" in runner
    assert "launch_quality_gate.csv" in runner
    assert "launch_manifest.json" in runner
    assert "results_dashboard/index.html" in runner
    assert "studio_dashboard/index.html" in runner
    command_center = (REPO / "generate_hsd_operator_command_center_v2.py").read_text(encoding="utf-8")
    assert "Results drill-down dashboard" in command_center
    assert "Studio drill-down dashboard" in command_center
