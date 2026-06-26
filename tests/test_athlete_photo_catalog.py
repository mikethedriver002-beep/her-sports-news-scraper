from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import report_hsd_athlete_photo_catalog_v1 as catalog
from report_hsd_athlete_photo_catalog_v1 import build_catalog, discover_render_template_uses


def test_catalog_requires_file_marker_and_registry_approval(tmp_path):
    headshot = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "dallas_wings_test_player" / "headshot.png"
    headshot.parent.mkdir(parents=True)
    headshot.write_bytes(b"not-a-real-image-but-present")
    marker = Path(headshot.as_posix() + ".approved")
    marker.write_text("approved by test", encoding="utf-8")

    rows = build_catalog(
        athlete_rows=[{"athlete_id": "dallas_wings_test_player", "league": "WNBA", "display_name": "Test Player", "team_id": "dallas_wings"}],
        image_rows=[{
            "athlete_id": "dallas_wings_test_player",
            "display_name": "Test Player",
            "team_id": "dallas_wings",
            "provider_player_id": "123",
            "image_type": "headshot",
            "file_path": headshot.as_posix(),
            "approved": "true",
            "source_note": "approved_marker_required",
        }],
        approved_rows=[{
            "athlete_id": "dallas_wings_test_player",
            "approved_file": headshot.as_posix(),
            "decision_source": "human",
            "source_file": "review.png",
            "approved_at_utc": "now",
        }],
        review_rows=[{"athlete_id": "dallas_wings_test_player", "status": "needs_human_approval", "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/123.png"}],
        template_uses=["Final Score With Player Photo (approved_player_photo_slot)"],
    )

    assert rows[0]["status"] == "approved"
    assert rows[0]["approved_marker_exists"] == "true"
    assert "Final Score With Player Photo" in rows[0]["render_template_uses"]
    assert rows[0]["review_only_policy"] == "catalog_only_no_auto_approval_no_file_movement"


def test_catalog_blocks_render_use_for_default_approval_provenance(tmp_path):
    headshot = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "dallas_wings_test_player" / "headshot.png"
    headshot.parent.mkdir(parents=True)
    headshot.write_bytes(b"present-default-sourced-headshot")
    Path(headshot.as_posix() + ".approved").write_text("approved by test", encoding="utf-8")

    rows = build_catalog(
        athlete_rows=[{"athlete_id": "dallas_wings_test_player", "league": "WNBA", "display_name": "Test Player", "team_id": "dallas_wings"}],
        image_rows=[{
            "athlete_id": "dallas_wings_test_player",
            "display_name": "Test Player",
            "team_id": "dallas_wings",
            "provider_player_id": "123",
            "image_type": "headshot",
            "file_path": headshot.as_posix(),
            "approved": "true",
            "source_note": "approved_marker_required",
        }],
        approved_rows=[{
            "athlete_id": "dallas_wings_test_player",
            "approved_file": headshot.as_posix(),
            "decision_source": "default",
            "source_file": "outputs/latest/review_files/athlete_image_approval_pack/downloads/test.png",
            "approved_at_utc": "2026-06-25T00:00:00+00:00",
        }],
        review_rows=[],
        template_uses=["Final Score With Player Photo (approved_player_photo_slot)"],
    )

    assert rows[0]["status"] == "approved"
    assert rows[0]["render_template_uses"].startswith("review_only_manual_source_recheck_required")
    assert "default_decision_source_manual_recheck_required" in rows[0]["render_template_uses"]
    assert "default_decision_source_manual_recheck_required" in rows[0]["crop_readiness_notes"]


def test_catalog_keeps_file_without_marker_unapproved(tmp_path):
    headshot = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "dallas_wings_test_player" / "headshot.png"
    headshot.parent.mkdir(parents=True)
    headshot.write_bytes(b"present-but-not-approved")

    rows = build_catalog(
        athlete_rows=[{"athlete_id": "dallas_wings_test_player", "league": "WNBA", "display_name": "Test Player", "team_id": "dallas_wings"}],
        image_rows=[{
            "athlete_id": "dallas_wings_test_player",
            "display_name": "Test Player",
            "team_id": "dallas_wings",
            "provider_player_id": "123",
            "image_type": "headshot",
            "file_path": headshot.as_posix(),
            "approved": "true",
            "source_note": "approved_marker_required",
        }],
        approved_rows=[],
        review_rows=[{"athlete_id": "dallas_wings_test_player", "status": "needs_human_approval", "image_url": "https://cdn.wnba.com/headshots/wnba/latest/260x190/123.png", "confidence": "0.72"}],
        template_uses=["Final Score With Player Photo (approved_player_photo_slot)"],
    )

    assert rows[0]["status"] == "unapproved"
    assert rows[0]["approved_marker_exists"] == "false"
    assert rows[0]["render_template_uses"] == "review_only_not_renderable_until_approved"
    assert "registry_says_approved_but_marker_missing" in rows[0]["crop_readiness_notes"]
    assert "match_review_registry" in rows[0]["source_evidence"]


def test_catalog_does_not_apply_headshot_evidence_to_missing_cutout(tmp_path):
    headshot = tmp_path / "assets" / "leagues" / "wnba" / "athletes" / "dallas_wings_test_player" / "headshot.png"
    cutout = headshot.parent / "cutout.png"
    headshot.parent.mkdir(parents=True)
    headshot.write_bytes(b"present")
    Path(headshot.as_posix() + ".approved").write_text("approved by test", encoding="utf-8")

    rows = build_catalog(
        athlete_rows=[{"athlete_id": "dallas_wings_test_player", "league": "WNBA", "display_name": "Test Player", "team_id": "dallas_wings"}],
        image_rows=[
            {
                "athlete_id": "dallas_wings_test_player",
                "display_name": "Test Player",
                "team_id": "dallas_wings",
                "image_type": "headshot",
                "file_path": headshot.as_posix(),
                "approved": "true",
                "source_note": "approved_marker_required",
            },
            {
                "athlete_id": "dallas_wings_test_player",
                "display_name": "Test Player",
                "team_id": "dallas_wings",
                "image_type": "cutout",
                "file_path": cutout.as_posix(),
                "approved": "false",
                "source_note": "missing_review_required",
            },
        ],
        approved_rows=[{"athlete_id": "dallas_wings_test_player", "approved_file": headshot.as_posix(), "decision_source": "human"}],
        review_rows=[],
        template_uses=["Final Score With Player Photo (approved_player_photo_slot)"],
    )

    cutout_row = [row for row in rows if row["asset_kind"] == "cutout"][0]
    assert cutout_row["status"] == "missing"
    assert cutout_row["source_evidence"] == "athlete_images_registry; source_note=missing_review_required"


def test_template_discovery_finds_player_and_image_slots(tmp_path):
    doc = tmp_path / "source_docs" / "template.md"
    doc.parent.mkdir()
    doc.write_text(
        "# Example Template\n\nUse approved_player_photo_slot and APPROVED IMAGE SLOT only.\n",
        encoding="utf-8",
    )

    uses = discover_render_template_uses(doc.parent)

    assert any("approved_player_photo_slot" in item for item in uses)
    assert any("approved_image_slot" in item for item in uses)


def test_catalog_schema_documents_review_only_statuses():
    schema = json.loads((ROOT / "contracts" / "athlete_photo_catalog_v1.schema.json").read_text(encoding="utf-8"))
    row_props = schema["properties"]["rows"]["items"]["properties"]

    assert schema["properties"]["report"]["properties"]["review_only"]["const"] is True
    assert row_props["status"]["enum"] == ["approved", "unapproved", "missing"]
    assert row_props["review_only_policy"]["const"] == "catalog_only_no_auto_approval_no_file_movement"


def test_catalog_main_writes_reports_to_run_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    catalog.main()

    assert (run_dir / "data" / "asset_registry" / "wnba" / "athlete_photo_catalog.csv").exists()
    assert (run_dir / "data" / "asset_registry" / "wnba" / "athlete_photo_catalog.json").exists()
    assert (run_dir / "data" / "asset_registry" / "wnba" / "athlete_photo_catalog.md").exists()
    assert not (tmp_path / "data" / "asset_registry" / "wnba" / "athlete_photo_catalog.csv").exists()
