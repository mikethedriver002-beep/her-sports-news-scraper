from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_graphics_visual_rubric_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_graphics_visual_rubric_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, "PNG")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def seed_current_anchor(repo_root: Path) -> None:
    root = repo_root / "outputs" / "local" / "latest" / "files" / "render_handoff_top_packet"
    write_png(root / "draft_preview.png", (1080, 1350), (7, 10, 15))
    write_png(root / "review_drafts" / "draft_preview_ig_feed.png", (1080, 1350), (10, 14, 20))
    write_png(root / "review_drafts" / "draft_preview_story.png", (1080, 1920), (14, 16, 22))
    write_png(root / "review_drafts" / "draft_preview_square.png", (1080, 1080), (16, 18, 24))
    write_png(root / "review_drafts" / "draft_preview_visual_contact_sheet.png", (1080, 1350), (18, 20, 28))

    write_text(
        root / "README.md",
        "# HSD Top Render Handoff\n"
        "Review-only. Human visual review required. No publishing.\n",
    )
    write_text(
        root / "manual_renderer_prompt.md",
        "Photo-first performer. Approved local athlete photo. Verified player/stat context is present.\n",
    )
    write_text(
        root / "copy_sheet.md",
        "Headline and dek for the current WNBA handoff.\n",
    )
    write_csv(
        root / "copy_sheet.csv",
        [
            "packet_id",
            "headline",
            "dek",
            "visual_mode",
            "hero_asset_required",
            "template_fit_reason",
            "approval_gate",
        ],
        [
            {
                "packet_id": "render_prep_1_test",
                "headline": "WNBA Final",
                "dek": "Verified final.",
                "visual_mode": "photo_first_performer",
                "hero_asset_required": "approved_local_athlete_photo",
                "template_fit_reason": "Verified player/stat context is present.",
                "approval_gate": "human_visual_review_required_before_any_post",
            }
        ],
    )
    write_csv(
        root / "asset_checklist.csv",
        [
            "packet_id",
            "active_asset_stop_go",
            "asset_requirement",
            "active_logo_readiness_status",
            "active_athlete_identity_status",
            "renderer_fallback_cue",
            "manual_path",
            "decision",
        ],
        [
            {
                "packet_id": "render_prep_1_test",
                "active_asset_stop_go": "hold_required_manual_asset_review",
                "asset_requirement": "approved_local_athlete_photo",
                "active_logo_readiness_status": "hold_logo_review_required",
                "active_athlete_identity_status": "athlete_identity_not_flagged",
                "renderer_fallback_cue": "league_mark_slot_stays_review_only_until_manual_source_and_file_review",
                "manual_path": "manual_review_artifact_ready:news_fact_packets.csv",
                "decision": "operator_review_required",
            }
        ],
    )
    write_csv(
        root / "manual_logo_verification_intake.csv",
        [
            "intake_bridge_id",
            "packet_id",
            "priority",
            "asset_domain",
            "entity_id",
            "entity_name",
            "selected_template_blocking_status",
            "local_logo_path",
            "official_source_candidate",
            "current_unapproved_status",
            "source_policy_status",
            "evidence_gap_status",
            "manual_review_packet",
            "operator_copy_target",
            "required_manual_checks",
            "allowed_manual_outcomes",
            "operator_next_actions",
            "cannot_clear_automatically_because",
            "review_only",
            "approval_state_change",
            "publish_ready",
            "auto_approval",
            "auto_publish",
            "move_files",
            "paid_apis",
            "asset_downloads",
            "publishing",
        ],
        [
            {
                "intake_bridge_id": "bridge_1",
                "packet_id": "render_prep_1_test",
                "priority": "P2",
                "asset_domain": "league_logo",
                "entity_id": "WNBA",
                "entity_name": "WNBA",
                "selected_template_blocking_status": "not_blocking",
                "local_logo_path": "assets/leagues/wnba/logo.png",
                "official_source_candidate": "https://www.wnba.com/",
                "current_unapproved_status": "missing",
                "source_policy_status": "manual_review_required",
                "evidence_gap_status": "official_source_needed_review_only",
                "manual_review_packet": "data/asset_registry/wnba/wnba_league_mark_review_intake.csv",
                "operator_copy_target": "data/asset_registry/wnba/wnba_league_mark_review_intake.csv",
                "required_manual_checks": "verify_league_mark_for_review_only_renderer_use|hold_league_mark",
                "allowed_manual_outcomes": "mark_not_required_for_selected_template",
                "operator_next_actions": "inspect the packet and keep it review-only",
                "cannot_clear_automatically_because": "needs manual review",
                "review_only": "true",
                "approval_state_change": "false",
                "publish_ready": "false",
                "auto_approval": "false",
                "auto_publish": "false",
                "move_files": "false",
                "paid_apis": "false",
                "asset_downloads": "false",
                "publishing": "false",
            }
        ],
    )


def seed_stagey_family(repo_root: Path) -> None:
    root = repo_root / "outputs" / "local" / "latest" / "files" / "review_only_premium_social_archetypes"
    for name in [
        "archetype_01_score_final_editorial.png",
        "archetype_02_stat_player_spotlight_shell.png",
        "archetype_03_breaking_news_card.png",
        "contact_sheet.png",
    ]:
        write_png(root / name, (1080, 1350), (42, 42, 42))
    write_text(
        root / "visual_quality_report.md",
        "Stage heavy. Mockup-led. Shell panels. Gray floor. REVIEW ONLY - PREMIUM VISUAL ARCHETYPE.\n",
    )
    write_text(
        root / "README.md",
        "# Review-Only Premium Social Archetypes\n",
    )
    write_text(
        root / "archetype_specs.json",
        json.dumps(
            {
                "archetype_rows": [
                    {"composition_treatment_mode": "score_final_editorial_depth_stage"},
                    {"composition_treatment_mode": "stat_shell_safe_subject_stage"},
                    {"composition_treatment_mode": "breaking_news_editorial_stage"},
                ]
            },
            indent=2,
        ),
    )
    write_csv(
        root / "manual_visual_review_intake.csv",
        [
            "archetype_id",
            "archetype_name",
            "render_path",
            "composition_treatment_mode",
            "review_only",
            "prototype_only",
            "photo_dependency",
            "asset_downloads",
            "source_auto_enabled",
            "approval_state_change",
            "publish_ready",
            "publishing",
        ],
        [
            {
                "archetype_id": "score_final_editorial",
                "archetype_name": "Score Final Editorial",
                "render_path": "outputs/local/latest/files/review_only_premium_social_archetypes/archetype_01_score_final_editorial.png",
                "composition_treatment_mode": "score_final_editorial_depth_stage",
                "review_only": "true",
                "prototype_only": "true",
                "photo_dependency": "false",
                "asset_downloads": "false",
                "source_auto_enabled": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        ],
    )


def seed_jackie_families(repo_root: Path) -> None:
    renderer_root = repo_root / "outputs" / "local" / "latest" / "files" / "jackie_young_renderer_proof_v1"
    upgrade_root = repo_root / "outputs" / "local" / "latest" / "files" / "jackie_young_visual_upgrade_v2"
    for root in [renderer_root, upgrade_root]:
        for name in ["contact_sheet.png", "proof_01_vertical_score_anchor.png", "proof_02_clean_full_body_read.png"]:
            write_png(root / name, (1080, 1350), (60, 60, 60))
        if root is renderer_root:
            write_png(root / "proof_03_magazine_spotlight_shell.png", (1080, 1350), (60, 60, 60))
        else:
            write_png(root / "upgrade_01_score_command.png", (1080, 1350), (60, 60, 60))
            write_png(root / "upgrade_02_cover_spotlight.png", (1080, 1350), (60, 60, 60))
            write_png(root / "upgrade_03_wire_story_depth.png", (1080, 1350), (60, 60, 60))

    write_text(
        renderer_root / "visual_proof_report.md",
        "Review only. Quarantine proof only. Shell and spotlight routes still carry staged proof language.\n",
    )
    write_text(
        upgrade_root / "visual_upgrade_report.md",
        "Review only. Stronger contrast. Safer typography. Still not asset approval or publish-ready.\n",
    )
    write_csv(
        renderer_root / "manual_visual_review_intake.csv",
        ["proof_id", "proof_name", "render_path", "crop_strategy", "review_only", "asset_downloads", "approval_state_change", "publish_ready", "publishing"],
        [
            {
                "proof_id": "proof_01_vertical_score_anchor",
                "proof_name": "Vertical Score Anchor",
                "render_path": "outputs/local/latest/files/jackie_young_renderer_proof_v1/proof_01_vertical_score_anchor.png",
                "crop_strategy": "apcs039_vertical_full_body_4x5_score_plane",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        ],
    )
    write_csv(
        upgrade_root / "manual_visual_review_intake.csv",
        ["proof_id", "proof_name", "render_path", "crop_strategy", "review_only", "asset_downloads", "approval_state_change", "publish_ready", "publishing"],
        [
            {
                "proof_id": "upgrade_01_score_command",
                "proof_name": "Score Command",
                "render_path": "outputs/local/latest/files/jackie_young_visual_upgrade_v2/upgrade_01_score_command.png",
                "crop_strategy": "apcs039_vertical_full_body_score_command_safe_type",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        ],
    )
    write_text(
        upgrade_root / "manifest.json",
        json.dumps(
            {
                "version": "hsd-jackie-young-visual-upgrade-v2-review-only",
                "review_only": True,
                "asset_downloads": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            },
            indent=2,
        ),
    )
    write_text(
        renderer_root / "manifest.json",
        json.dumps(
            {
                "version": "hsd-jackie-young-renderer-proof-v1-review-only",
                "review_only": True,
                "asset_downloads": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            },
            indent=2,
        ),
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_builds_wnba_graphics_visual_rubric_packet(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_graphics_visual_rubric_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    seed_current_anchor(repo_root)
    seed_stagey_family(repo_root)
    seed_jackie_families(repo_root)

    assert module.main(["--head-commit", "abc123"]) == 0

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "wnba_graphics_visual_rubric.md").read_text(encoding="utf-8")
    readme = (run_dir / "README.md").read_text(encoding="utf-8")
    rows = read_csv(run_dir / "wnba_graphics_visual_rubric.csv")

    assert manifest["version"] == "hsd-wnba-graphics-visual-rubric-v1-review-only"
    assert manifest["status"] == "wnba_graphics_visual_rubric_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["family_count"] == 4
    assert manifest["present_family_count"] == 4
    assert manifest["rejected_family_count"] >= 3
    assert manifest["review_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["source_auto_enabled"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False
    assert manifest["paid_apis"] is False
    assert "photo_first_performer" in report
    assert "boxed-stage" in report
    assert "gray-panel" in report
    assert "Required Manual Fields" in report
    assert "Current WNBA source-led handoff" in readme

    current_row = next(row for row in rows if row["family_id"] == "current_wnba_source_led_handoff")
    premium_row = next(row for row in rows if row["family_id"] == "review_only_premium_social_archetypes")
    renderer_row = next(row for row in rows if row["family_id"] == "jackie_young_renderer_proof_v1")

    assert current_row["dimension_ok"] == "true"
    assert current_row["manual_fields_ok"] == "true"
    assert current_row["source_led_ok"] == "true"
    assert current_row["overall"] in {"flag", "pass"}
    assert premium_row["overall"] == "reject"
    assert "missing_manual_fields" in premium_row
    assert renderer_row["overall"] == "reject"
    assert "shell" in renderer_row["notes"]


def test_scores_stagey_families_as_rejects_with_missing_manual_fields(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    seed_stagey_family(repo_root)
    seed_jackie_families(repo_root)

    stagey = module.score_family(repo_root / "outputs" / "local" / "latest" / "files" / "review_only_premium_social_archetypes", module.SOURCE_FAMILIES[1])
    jackie = module.score_family(repo_root / "outputs" / "local" / "latest" / "files" / "jackie_young_visual_upgrade_v2", module.SOURCE_FAMILIES[3])

    assert stagey["dimension_ok"] is True
    assert stagey["manual_fields_ok"] is False
    assert stagey["overall"] == "reject"
    assert "packet_id" in stagey["missing_manual_fields"]
    assert jackie["manual_fields_ok"] is False
    assert jackie["overall"] == "reject"
    assert jackie["source_led_ok"] is False

