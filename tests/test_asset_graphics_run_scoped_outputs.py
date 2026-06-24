from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_script(script: str, cwd: Path, run_dir: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "HSD_RUN_OUTPUT_DIR": str(run_dir),
            "HSD_ASSET_DOWNLOAD": "0",
            "HSD_PLAYER_IMAGE_FREE_SEARCH": "0",
            "HSD_PLAYER_IMAGE_REQUEST_SLEEP": "0",
            "PYTHONPATH": str(REPO),
        }
    )
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(REPO / script)],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_asset_graphics_scripts_are_wired_to_run_io() -> None:
    required = {
        "generate_hsd_asset_desk_v1.py": [
            "from hsd_run_io import",
            'OUT_APPROVED = output_path("data/assets/approved")',
            "canonical_asset_registry_note",
        ],
        "generate_hsd_player_image_assets_v1.py": [
            "from hsd_run_io import",
            'OUT_DIR = output_path("data/assets/player_images")',
            "run-scoped review copy",
        ],
        "generate_hsd_graphics_upload_pack_v1.py": [
            "from hsd_run_io import",
            'OUT_DIR = output_path("graphics_chat_upload_pack")',
            "canonical_asset_registry_note",
        ],
        "generate_hsd_graphics_qa_v1.py": [
            "from hsd_run_io import",
            'output_path("graphics_qa_dashboard")',
            '"output_scope": "run_scoped" if run_root else "legacy_root"',
        ],
    }

    for rel, needles in required.items():
        text = (REPO / rel).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"{needle!r} missing from {rel}"


def test_asset_desk_writes_review_registries_to_run_folder(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_csv(
        run_dir / "studio_bundle_queue.csv",
        [
            {
                "bundle_id": "bundle_test",
                "bundle_name": "Dallas Wings vs Los Angeles Sparks",
                "post_slug": "dallas-wings-vs-los-angeles-sparks",
                "bundle_type": "wnba_preview",
                "production_priority": "POST FIRST",
                "source_headlines": "Dallas Wings vs Los Angeles Sparks preview.",
                "caption_seed": "Dallas Wings vs Los Angeles Sparks",
                "accuracy_lock": "Dallas Wings vs Los Angeles Sparks.",
            }
        ],
        [
            "bundle_id",
            "bundle_name",
            "post_slug",
            "bundle_type",
            "production_priority",
            "source_headlines",
            "caption_seed",
            "accuracy_lock",
        ],
    )

    proc = run_script("generate_hsd_asset_desk_v1.py", tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    assert (run_dir / "approved_graphics_assets.csv").exists()
    assert (run_dir / "team_assets.csv").exists()
    assert (run_dir / "asset_candidates_review.md").exists()
    assert not (tmp_path / "approved_graphics_assets.csv").exists()
    manifest = json.loads((run_dir / "asset_desk_manifest.json").read_text(encoding="utf-8"))
    assert manifest["output_scope"] == "run_scoped"
    assert "Promote them to canonical project files only after manual review" in manifest["canonical_asset_registry_note"]


def test_player_image_sourcing_writes_review_updates_to_run_folder(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    write_csv(
        run_dir / "approved_graphics_assets.csv",
        [],
        [
            "approved_asset_id",
            "asset_id",
            "approved_variant",
            "entity_type",
            "entity_name",
            "source_url",
            "page_url",
            "master_path",
            "web_path",
            "rights_status",
            "approved_by",
            "approved_utc",
            "usage_scope",
            "notes",
        ],
    )
    write_csv(run_dir / "player_assets.csv", [], ["player_id", "sport", "league", "player_slug", "player_name", "headshot_asset_id", "status", "notes"])
    write_csv(run_dir / "studio_bundle_queue.csv", [], ["bundle_id", "bundle_name", "post_slug"])

    proc = run_script("generate_hsd_player_image_assets_v1.py", tmp_path, run_dir)

    assert proc.returncode == 0, proc.stderr
    assert (run_dir / "approved_graphics_assets.csv").exists()
    assert (run_dir / "approved_graphics_assets.json").exists()
    assert (run_dir / "player_assets.csv").exists()
    assert (run_dir / "player_image_requirements.csv").exists()
    assert (run_dir / "player_image_sourcing_report.md").exists()
    assert not (tmp_path / "player_image_requirements.csv").exists()
    report = (run_dir / "player_image_sourcing_report.md").read_text(encoding="utf-8")
    assert "updated approved/player asset tables are review copies" in report


def test_upload_pack_and_graphics_qa_use_run_scoped_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run" / "files"
    asset_path = run_dir / "data" / "assets" / "player_images" / "test-player.png"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"not-a-real-png-but-good-enough-for-pack-copy")

    write_csv(
        run_dir / "approved_graphics_assets.csv",
        [
            {
                "approved_asset_id": "appr_test_player",
                "asset_id": "ast_test_player",
                "approved_variant": "primary_player_photo_v1",
                "entity_type": "player",
                "entity_name": "Test Player",
                "source_url": "manual://test-player",
                "page_url": "manual://test-player",
                "master_path": "data/assets/player_images/test-player.png",
                "web_path": "data/assets/player_images/test-player.png",
                "rights_status": "manual_test_fixture",
                "approved_by": "pytest",
                "approved_utc": "2026-06-24T00:00:00+00:00",
                "usage_scope": "HSD social graphics",
                "notes": "fixture",
            }
        ],
        [
            "approved_asset_id",
            "asset_id",
            "approved_variant",
            "entity_type",
            "entity_name",
            "source_url",
            "page_url",
            "master_path",
            "web_path",
            "rights_status",
            "approved_by",
            "approved_utc",
            "usage_scope",
            "notes",
        ],
    )
    (run_dir / "studio_bundle_prompts_v2.md").write_text("## Test Bundle\nUse the attached player image.\n", encoding="utf-8")
    (run_dir / "studio_render_manifest_v2.json").write_text(
        json.dumps(
            {
                "bundles": [
                    {
                        "bundle_id": "bundle_test",
                        "post_slug": "test-bundle",
                        "bundle_name": "Test Bundle",
                        "template_name": "result_slide_v2",
                        "asset_ids": ["appr_test_player"],
                        "source_facts": {"accuracy_lock": "Test facts are locked."},
                        "all_layers": [{"layer_id": "hsd_watermark"}],
                        "render_path": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    pack_proc = run_script("generate_hsd_graphics_upload_pack_v1.py", tmp_path, run_dir)
    qa_proc = run_script("generate_hsd_graphics_qa_v1.py", tmp_path, run_dir)

    assert pack_proc.returncode == 0, pack_proc.stderr
    assert qa_proc.returncode == 0, qa_proc.stderr
    assert (run_dir / "graphics_chat_upload_pack" / "test-bundle" / "00_PROMPT_TO_PASTE.md").exists()
    assert (run_dir / "graphics_chat_upload_pack_zips" / "test-bundle_graphics_chat_upload_pack.zip").exists()
    assert (run_dir / "graphics_chat_upload_manifest.csv").exists()
    assert (run_dir / "graphics_upload_pack_status.csv").exists()
    assert (run_dir / "graphics_qa_results.csv").exists()
    assert (run_dir / "graphics_qa_manifest.json").exists()
    assert (run_dir / "graphics_qa_dashboard" / "index.html").exists()
    assert not (tmp_path / "graphics_chat_upload_pack").exists()
    assert not (tmp_path / "graphics_qa_results.csv").exists()

    upload_manifest = json.loads((run_dir / "graphics_chat_upload_manifest.json").read_text(encoding="utf-8"))
    qa_manifest = json.loads((run_dir / "graphics_qa_manifest.json").read_text(encoding="utf-8"))
    assert upload_manifest["output_scope"] == "run_scoped"
    assert qa_manifest["output_scope"] == "run_scoped"
