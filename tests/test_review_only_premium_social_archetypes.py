from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_review_only_premium_social_archetypes_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_review_only_premium_social_archetypes_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_build_archetype_specs_defines_three_blender_first_photo_free_routes() -> None:
    module = load_module()
    specs = module.build_archetype_specs()

    assert [spec["archetype_id"] for spec in specs] == [
        "score_final_editorial",
        "stat_player_spotlight_shell",
        "breaking_news_card",
    ]
    assert [spec["filename"] for spec in specs] == [
        "archetype_01_score_final_editorial.png",
        "archetype_02_stat_player_spotlight_shell.png",
        "archetype_03_breaking_news_card.png",
    ]
    assert all("composition_treatment_mode" in spec for spec in specs)
    assert all("self_critique" in spec for spec in specs)


def test_build_runner_script_describes_blender_backed_render_pipeline() -> None:
    module = load_module()
    runner = module.build_runner_script()

    assert 'parser.add_argument("--specs-json", required=True)' in runner
    assert 'for candidate in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")' in runner
    assert 'scene.render.resolution_x = 1080' in runner
    assert 'scene.render.resolution_y = 1350' in runner
    assert 'add_area_light(' in runner
    assert 'build_score_final_editorial(spec)' in runner
    assert 'build_stat_player_spotlight_shell(spec)' in runner
    assert 'build_breaking_news_card(spec)' in runner
    assert 'bpy.ops.render.render(write_still=True)' in runner
    assert 'REVIEW ONLY - PREMIUM VISUAL ARCHETYPE' not in runner


def test_main_writes_review_only_blender_packet_with_stubbed_render(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "review_only_premium_social_archetypes_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))

    def fake_run_blender_render(blender_executable: Path, runner_file: Path, specs_file: Path):
        payload = json.loads(specs_file.read_text(encoding="utf-8"))
        for row in payload["archetype_specs"]:
            image = Image.new("RGB", (1080, 1350), (24, 28, 36))
            image.save(Path(row["output_png_path"]), "PNG")
        return module.RenderResult(0, "stub blender render ok", "")

    monkeypatch.setattr(module, "resolve_blender_executable", lambda explicit=None: Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"))
    monkeypatch.setattr(module, "probe_blender_version", lambda blender_executable: "Blender 5.1.2")
    monkeypatch.setattr(module, "run_blender_render", fake_run_blender_render)

    assert module.main(["--head-commit", "abc123"]) == 0

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "visual_quality_report.md").read_text(encoding="utf-8")
    readme = (run_dir / "README.md").read_text(encoding="utf-8")
    rows = read_csv(run_dir / "manual_visual_review_intake.csv")

    assert manifest["version"] == "hsd-review-only-premium-social-archetypes-v1"
    assert manifest["status"] == "review_only_premium_social_archetypes_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["blender_first"] is True
    assert manifest["blender_version"] == "Blender 5.1.2"
    assert manifest["contact_sheet_created"] is True
    assert manifest["archetype_count"] == 3
    assert manifest["review_only"] is True
    assert manifest["prototype_only"] is True
    assert manifest["non_apq_visual_bypass"] is True
    assert manifest["photo_dependency"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["source_auto_enabled"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["production_renderer_replacement"] is False
    assert manifest["paid_apis"] is False
    assert manifest["traceback_present"] is False
    assert manifest["manual_review_questions"] == [
        "Which archetype has the highest near-term monetizable/social value?",
        "Which visual route should become the renderer baseline while photo sourcing is blocked?",
        "What is visually unacceptable before any publishing path?",
    ]

    for item in manifest["archetype_rows"]:
        image = Image.open(item["output_png_path"])
        assert image.size == (1080, 1350)
        assert item["review_only"] is True
        assert item["photo_dependency"] is False
        assert item["self_critique"]

    contact_sheet = Image.open(run_dir / "contact_sheet.png")
    assert contact_sheet.size == (1080, 562)

    assert "Blender-backed procedural scene generation only" in report
    assert "non-APQ visual architecture bypass" in report
    assert "Which archetype has the highest near-term monetizable/social value?" in report
    assert "Blunt Recommendation" in report
    assert "Blender-first" in readme

    assert len(rows) == 3
    assert [row["archetype_id"] for row in rows] == [
        "score_final_editorial",
        "stat_player_spotlight_shell",
        "breaking_news_card",
    ]
    assert all(row["review_only"] == "true" for row in rows)
    assert all(row["prototype_only"] == "true" for row in rows)
    assert all(row["photo_dependency"] == "false" for row in rows)
    assert all(row["asset_downloads"] == "false" for row in rows)
    assert all(row["source_auto_enabled"] == "false" for row in rows)
    assert all(row["approval_state_change"] == "false" for row in rows)
    assert all(row["publish_ready"] == "false" for row in rows)
    assert all(row["publishing"] == "false" for row in rows)
