from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "report_hsd_asset_availability_audit_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_hsd_asset_availability_audit_v1", SCRIPT)
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


def write_png(path: Path, size: tuple[int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (20, 40, 60, 255)).save(path)


def seed_template_mapping(root: Path) -> None:
    mapping = root / "config" / "graphics" / "template_render_mapping_v1.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text(
        json.dumps({"event_mappings": [{"league": "WNBA", "template_id": "game_recap_final_score.a.v1"}]}),
        encoding="utf-8",
    )


def seed_athletes(root: Path) -> None:
    registry = root / "data" / "asset_registry" / "wnba"
    write_csv(
        registry / "athletes.csv",
        [
            {"athlete_id": "approved_default", "league": "WNBA", "display_name": "Default Approved", "team_id": "approved_team"},
            {"athlete_id": "missing_player", "league": "WNBA", "display_name": "Missing Player", "team_id": "approved_team"},
            {"athlete_id": "small_player", "league": "WNBA", "display_name": "Small Player", "team_id": "approved_team"},
        ],
        ["athlete_id", "league", "display_name", "team_id"],
    )
    write_png(root / "assets" / "leagues" / "wnba" / "athletes" / "approved_default" / "headshot.png", (300, 220))
    approved_path = "assets/leagues/wnba/athletes/approved_default/headshot.png"
    Path(root / (approved_path + ".approved")).write_text("approved", encoding="utf-8")
    write_png(root / "assets" / "leagues" / "wnba" / "athletes" / "small_player" / "headshot.png", (120, 90))
    small_path = "assets/leagues/wnba/athletes/small_player/headshot.png"
    Path(root / (small_path + ".approved")).write_text("approved", encoding="utf-8")
    write_csv(
        registry / "athlete_images.csv",
        [
            {
                "athlete_id": "approved_default",
                "display_name": "Default Approved",
                "team_id": "approved_team",
                "provider_player_id": "1",
                "image_type": "headshot",
                "file_path": approved_path,
                "approved": "true",
                "source_note": "approved_marker_required",
            },
            {
                "athlete_id": "missing_player",
                "display_name": "Missing Player",
                "team_id": "approved_team",
                "provider_player_id": "2",
                "image_type": "headshot",
                "file_path": "assets/leagues/wnba/athletes/missing_player/headshot.png",
                "approved": "true",
                "source_note": "approved_marker_required",
            },
            {
                "athlete_id": "small_player",
                "display_name": "Small Player",
                "team_id": "approved_team",
                "provider_player_id": "3",
                "image_type": "headshot",
                "file_path": small_path,
                "approved": "true",
                "source_note": "approved_marker_required",
            },
        ],
        ["athlete_id", "display_name", "team_id", "provider_player_id", "image_type", "file_path", "approved", "source_note"],
    )
    write_csv(
        registry / "athlete_image_approved_assets.csv",
        [
            {
                "athlete_id": "approved_default",
                "approved_file": approved_path,
                "decision_source": "default",
                "source_file": "outputs/latest/review_files/downloads/default.png",
                "approved_at_utc": "2026-06-25T00:00:00+00:00",
            },
            {
                "athlete_id": "small_player",
                "approved_file": small_path,
                "decision_source": "human",
                "source_file": "review.png",
                "approved_at_utc": "2026-06-25T00:00:00+00:00",
            },
        ],
        ["athlete_id", "approved_file", "decision_source", "source_file", "approved_at_utc"],
    )
    write_csv(registry / "athlete_image_match_review.csv", [], ["athlete_id", "status", "image_url", "confidence"])


def seed_logos(root: Path) -> None:
    registry = root / "data" / "asset_registry" / "wnba"
    write_csv(
        registry / "teams.csv",
        [
            {"team_id": "approved_team", "league": "WNBA", "team_name": "Approved Team"},
            {"team_id": "broken_team", "league": "WNBA", "team_name": "Broken Team"},
        ],
        ["team_id", "league", "team_name"],
    )
    write_png(root / "assets" / "leagues" / "wnba" / "teams" / "approved_team" / "logo.png", (256, 256))
    broken_logo = root / "assets" / "leagues" / "wnba" / "teams" / "broken_team" / "logo.png"
    broken_logo.parent.mkdir(parents=True, exist_ok=True)
    broken_logo.write_text("not a png", encoding="utf-8")
    write_csv(
        registry / "team_logos.csv",
        [
            {
                "team_id": "approved_team",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/approved_team/logo.png",
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "source_note": "human_reviewed",
            },
            {
                "team_id": "broken_team",
                "asset_type": "primary_logo",
                "file_path": "assets/leagues/wnba/teams/broken_team/logo.png",
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "source_note": "blocked_source",
            },
        ],
        ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "source_note"],
    )
    write_csv(
        registry / "logo_sources.csv",
        [
            {
                "team_id": "approved_team",
                "team_name": "Approved Team",
                "source_url": "https://example.test/approved.svg",
                "target_path": "assets/leagues/wnba/teams/approved_team/logo.png",
                "source_note": "source_reviewed",
            },
            {
                "team_id": "broken_team",
                "team_name": "Broken Team",
                "source_url": "https://example.test/blocked-broken-logo.svg",
                "target_path": "assets/leagues/wnba/teams/broken_team/logo.png",
                "source_note": "blocked_source",
            },
        ],
        ["team_id", "team_name", "source_url", "target_path", "source_note"],
    )
    verified = root / "config" / "hsd_verified_logo_registry_v1.json"
    verified.parent.mkdir(parents=True, exist_ok=True)
    verified.write_text(
        json.dumps({"teams": {"Broken Team": {"blocked_url_substrings": ["blocked-broken-logo.svg"]}}}),
        encoding="utf-8",
    )


def seed_renderer_fallback(root: Path) -> None:
    out = root / "outputs" / "latest" / "HSD_TEMPLATE_FACTORY" / "template_renderer_v2"
    out.mkdir(parents=True, exist_ok=True)
    (out / "hsd_template_renderer_v2_logo_audit.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "team_id": "missing_logo_team",
                        "team": "Missing Logo Team",
                        "league": "WNBA",
                        "status": "warning_fallback",
                        "source": "fallback",
                        "path_or_url": "team_name_badge",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (out / "hsd_template_renderer_v2_manifest.json").write_text(
        json.dumps({"version": "renderer-test", "rendered_count": 1}),
        encoding="utf-8",
    )
    write_csv(
        root / "outputs" / "latest" / "HSD_ASSET_ASSURANCE" / "asset_assurance_v1_rows.csv",
        [
            {
                "item_id": "badge-review-1",
                "source_id": "badge_source",
                "headline": "Badge fallback review row",
                "asset_release_lane": "hsd_badge_review",
                "team_fallback_badge_count": "1",
                "asset_render_safe": "true",
                "asset_live_ready_pre_human": "false",
                "asset_fallback_review_cue": "HSD team badges are review-only stand-ins for missing or undecodable exact logos; they do not approve logo identity or create a publish-ready lane.",
            },
            {
                "item_id": "spotlight-review-1",
                "source_id": "spotlight_source",
                "headline": "Team spotlight fallback row",
                "asset_release_lane": "team_spotlight_review",
                "asset_assurance_player_mode": "team_spotlight_fallback",
                "asset_assurance_player_route": "downgraded_player_to_non_player_team_spotlight",
                "asset_fallback_review_cue": "Team spotlight fallback is a non-player review route when verified athlete assets are unavailable; it does not approve athlete identity or photo-first rendering.",
            },
            {
                "item_id": "fixture-review-1",
                "source_id": "fixture_source",
                "headline": "Fixture reference row",
                "asset_release_lane": "blocked",
                "asset_assurance_player_mode": "fixture_reference_asset",
                "fixture_only_player_asset": "true",
                "asset_fallback_review_cue": "Fixture reference assets remain review-only and must be replaced or manually verified before any athlete-photo trust.",
            },
        ],
        [
            "item_id",
            "source_id",
            "headline",
            "asset_release_lane",
            "team_fallback_badge_count",
            "asset_assurance_player_mode",
            "asset_assurance_player_route",
            "asset_render_safe",
            "asset_live_ready_pre_human",
            "fixture_only_player_asset",
            "asset_fallback_review_cue",
        ],
    )


def test_availability_audit_flags_assets_approvals_formats_and_renderer_fallbacks(tmp_path: Path) -> None:
    module = load_module()
    seed_template_mapping(tmp_path)
    seed_athletes(tmp_path)
    seed_logos(tmp_path)
    seed_renderer_fallback(tmp_path)

    report = module.build_audit(tmp_path)
    findings = {(row["finding"], row["entity_id"]) for row in report["findings"]}
    by_finding = {(row["finding"], row["entity_id"]): row for row in report["findings"]}

    assert report["review_only"] is True
    assert report["policy"]["no_auto_approval"] is True
    assert ("missing_local_player_asset", "missing_player") in findings
    assert ("suspicious_or_default_player_approval", "approved_default") in findings
    assert ("player_photo_dimension_problem", "small_player") in findings
    assert ("logo_format_problem", "broken_team") in findings
    assert ("suspicious_logo_source_or_approval", "broken_team") in findings
    assert ("renderer_active_logo_fallback", "missing_logo_team") in findings
    assert ("renderer_hsd_team_badge_review", "badge_source") in findings
    assert ("renderer_team_spotlight_fallback_review", "spotlight_source") in findings
    assert ("renderer_fixture_reference_asset_review", "fixture_source") in findings
    assert report["severity_counts"]["error"] >= 2
    suspicious_photo = by_finding[("suspicious_or_default_player_approval", "approved_default")]
    assert suspicious_photo["decision_lane"] == "wnba_athlete_identity_resolution"
    assert suspicious_photo["default_operator_decision"] == "hold_identity"
    assert suspicious_photo["identity_confidence"] == "identity_hold_default_or_suspicious_approval"
    assert suspicious_photo["asset_readiness"] == "blocked_until_identity_resolution"
    assert suspicious_photo["operator_copy_target"] == "operator/inbox/wnba_athlete_identity_resolution.csv"
    assert suspicious_photo["decision_packet_title"] == "Player photo blocker: Default Approved"
    assert suspicious_photo["allowed_operator_decisions"] == "verify_identity_for_review_renders|hold_identity|revise_asset"
    assert suspicious_photo["publish_ready"] == "false"
    broken_logo = by_finding[("suspicious_logo_source_or_approval", "broken_team")]
    assert broken_logo["decision_lane"] == "wnba_logo_review"
    assert broken_logo["source_confidence"] == "source_recheck_required"
    assert broken_logo["decision_packet_title"] == "WNBA team logo blocker: Broken Team"
    assert broken_logo["asset_readiness"] == "approved_file_source_blocked_hold"
    assert broken_logo["logo_readiness_status"] == "approved_file_source_blocked_hold"
    assert broken_logo["renderer_fallback_cue"] == "hold_renderer_logo_trust_until_source_recheck_closes"
    assert broken_logo["decision_hold_cue"].startswith("Hold if exact local logo evidence")
    renderer = by_finding[("renderer_active_logo_fallback", "missing_logo_team")]
    assert renderer["decision_lane"] == "renderer_fallback_review"
    assert renderer["default_operator_decision"] == "verify_renderer_fallback"
    assert renderer["decision_packet_title"] == "Renderer fallback review: Missing Logo Team"
    assert renderer["renderer_fallback_cue"] == "active_text_badge_fallback_review_only_hold_exact_logo_required"
    assert renderer["allowed_operator_decisions"] == "confirm_no_active_fallback|hold_render|revise_asset_registry"
    badge = by_finding[("renderer_hsd_team_badge_review", "badge_source")]
    assert badge["severity"] == "info"
    assert "review-only stand-ins" in badge["renderer_fallback_cue"]
    assert "publish-ready lane" in badge["renderer_fallback_cue"]
    spotlight = by_finding[("renderer_team_spotlight_fallback_review", "spotlight_source")]
    assert spotlight["severity"] == "info"
    assert "non-player review route" in spotlight["renderer_fallback_cue"]
    assert "does not approve athlete identity" in spotlight["renderer_fallback_cue"]
    fixture = by_finding[("renderer_fixture_reference_asset_review", "fixture_source")]
    assert fixture["severity"] == "info"
    assert "Fixture reference assets remain review-only" in fixture["renderer_fallback_cue"]


def test_availability_audit_main_writes_run_scoped_reports(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    seed_template_mapping(tmp_path)
    seed_athletes(tmp_path)
    seed_logos(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    assert module.main(["--root", str(tmp_path)]) == 0

    assert (run_dir / "data" / "asset_registry" / "asset_availability_audit.csv").exists()
    assert (run_dir / "data" / "asset_registry" / "asset_availability_audit.json").exists()
    assert (run_dir / "data" / "asset_registry" / "asset_availability_audit.md").exists()
    assert not (tmp_path / "data" / "asset_registry" / "asset_availability_audit.csv").exists()
