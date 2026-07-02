from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "render_hsd_blender_apq_composition_variants_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_hsd_blender_apq_composition_variants_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (1080, 1350), color + (255,)).save(path, "PNG")


def write_right_focus_source_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((1000, 200, 1550, 800), fill=(220, 40, 50))
    image.save(path, "PNG")


def test_load_scene_context_degrades_without_sample_payload(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    scene_payload = repo_root / "outputs" / "local" / "latest" / "files" / "blender_apq_scene_payload_contract" / "sample_apq001_scene_payload.json"
    context = module.load_scene_context(scene_payload)

    assert context["scene_payload_present"] is False
    assert context["source_image_present"] is False
    assert context["scene_payload_status"] == "missing"
    assert str(context["source_image_path"]).endswith("apq001_review_only_candidate.jpg")


def test_build_variant_specs_carries_three_distinct_directions(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    scene_payload = repo_root / "outputs" / "local" / "latest" / "files" / "blender_apq_scene_payload_contract" / "sample_apq001_scene_payload.json"
    context = module.load_scene_context(scene_payload)
    specs = module.build_variant_specs(context)

    assert [spec["variant_id"] for spec in specs] == [
        "variant_01_photo_anchor",
        "variant_02_score_drama",
        "variant_03_clean_editorial",
    ]
    assert all(spec["source_image_present"] is False for spec in specs)
    assert all(spec["canvas"] == {"width": 1080, "height": 1350} for spec in specs)
    assert all(spec["burn_in_text"] == "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE" for spec in specs)
    assert all(spec["source_image_texture_attempted"] is False for spec in specs)
    assert all(spec["source_image_texture_loaded"] is False for spec in specs)
    assert all(spec["source_image_texture_mode"] == "pending" for spec in specs)
    assert [spec["burn_in_position_mode"] for spec in specs] == ["bottom_safe_footer_tag", "bottom_safe_footer_tag", "bottom_safe_footer_tag"]
    assert all(spec["source_photo_crop_mode"] == "fit_1080x1350_right_focus" for spec in specs)
    assert [spec["source_photo_focus_region"]["x"] for spec in specs] == [0.76, 0.75, 0.77]
    assert all(spec["source_photo_focus_region"]["y"] == 0.5 for spec in specs)
    assert [spec["subject_crop_balance_mode"] for spec in specs] == [
        "face_safe_open_balance",
        "score_weighted_center_balance",
        "editorial_face_open_balance",
    ]
    assert [spec["composition_treatment_mode"] for spec in specs] == [
        "full_photo_background_scrim",
        "score_forward_open_editorial",
        "clean_editorial_fullbleed",
    ]
    assert all(spec["burn_in_treatment_mode"] == "bottom_safe_footer_tag" for spec in specs)
    assert [spec["score_typography_treatment"] for spec in specs] == [
        "open_editorial_type",
        "score_drama_open_type",
        "open_editorial_type",
    ]
    assert specs[0]["photo_anchor_type_treatment_mode"] == "open_scrim_hierarchy"
    assert all(spec["photo_texture_render_layer_mode"] == "texture_front_no_frame_cover" for spec in specs)
    assert all(spec["review_only_derived_crop"] is False for spec in specs)
    assert all(spec["render_source_image_path"].endswith("apq001_review_only_candidate.jpg") for spec in specs)
    assert all(spec["layout_polish_checks"]["burn_in_inside_canvas"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["burn_in_off_primary_body"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["frame_clutter_reduced"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["score_panel_softened"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["split_panel_softened"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["photo_type_integration_improved"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["face_edge_clipping_reduced"] is True for spec in specs)
    assert all(spec["layout_polish_checks"]["text_kept_off_face"] is True for spec in specs)
    assert specs[0]["layout_polish_checks"]["typography_hierarchy_improved"] is True
    assert specs[0]["layout_polish_checks"]["split_panel_removed_or_minimized"] is True
    assert specs[0]["layout_polish_checks"]["full_photo_background_layer"] is True
    assert specs[0]["layout_polish_checks"]["photo_is_hero"] is True
    assert specs[0]["use_score_plate"] is False
    assert specs[1]["use_editorial_scrim"] is True


def test_build_runner_script_bakes_texture_loading_contract(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    scene_payload = repo_root / "outputs" / "local" / "latest" / "files" / "blender_apq_scene_payload_contract" / "sample_apq001_scene_payload.json"
    context = module.load_scene_context(scene_payload)
    specs = module.build_variant_specs(context)
    runner = module.build_runner_script(specs)

    assert "bpy.data.images.load" in runner
    assert "ShaderNodeTexImage" in runner
    assert "ShaderNodeBsdfPrincipled" in runner
    assert "PhotoBackgroundTexture" in runner
    assert module.TEXTURE_STATUS_PREFIX in runner
    assert ".texture_status.json" in runner


def test_main_writes_three_pngs_manifest_report_and_csv_with_stubbed_blender(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_composition_variants"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(out_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    fake_blender = tmp_path / "fake" / "blender.exe"
    fake_blender.parent.mkdir(parents=True, exist_ok=True)
    fake_blender.write_text("stub", encoding="utf-8")

    def fake_probe_blender_version(blender_executable: Path) -> str:
        assert blender_executable == fake_blender
        return "Blender 5.1.2"

    def fake_run_blender_render(blender_executable, runner_file, scene_payload_path, variant_id, output_png_path):
        assert blender_executable == fake_blender
        assert runner_file.exists()
        assert scene_payload_path.name == "sample_apq001_scene_payload.json"
        colors = {
            "variant_01_photo_anchor": (28, 34, 48),
            "variant_02_score_drama": (40, 18, 22),
            "variant_03_clean_editorial": (26, 30, 36),
        }
        write_png(output_png_path, colors[variant_id])
        status = {
            "source_image_texture_attempted": False,
            "source_image_texture_loaded": False,
            "source_image_texture_mode": "placeholder_missing_source",
            "source_image_texture_error": "",
        }
        stdout = f"variant={variant_id}\n{module.TEXTURE_STATUS_PREFIX}{json.dumps(status, sort_keys=True)}\n"
        return type("Result", (), {"returncode": 0, "stdout": stdout, "stderr": ""})()

    monkeypatch.setattr(module, "resolve_blender_executable", lambda explicit=None: fake_blender)
    monkeypatch.setattr(module, "probe_blender_version", fake_probe_blender_version)
    monkeypatch.setattr(module, "run_blender_render", fake_run_blender_render)

    assert module.main([]) == 0

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "variant_comparison_report.md").read_text(encoding="utf-8")
    rows = read_csv(out_dir / "manual_variant_review_intake.csv")
    contact_sheet = Image.open(out_dir / "contact_sheet.png")

    assert manifest["version"] == "hsd-blender-apq-composition-variants-v1-review-only"
    assert manifest["status"] == "blender_apq_composition_variants_ready"
    assert manifest["variant_count"] == 3
    assert manifest["output_dimensions"] == {"width": 1080, "height": 1350}
    assert manifest["scene_payload_present"] is False
    assert manifest["source_image_present"] is False
    assert manifest["source_image_texture_attempted"] is False
    assert manifest["source_image_texture_loaded"] is False
    assert manifest["source_image_texture_mode"] == "placeholder"
    assert manifest["review_only_derived_crop"] is False
    assert manifest["review_only_derived_crop_paths"] == []
    assert all(row["photo_texture_render_layer_mode"] == "texture_front_no_frame_cover" for row in manifest["variant_rows"])
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    assert manifest["asset_approved"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["download_performed"] is False
    assert manifest["source_auto_enabled"] is False
    assert manifest["image_edits"] is False
    assert manifest["move_files"] is False
    assert manifest["protected_asset_moves"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["production_renderer_replacement"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["auto_publish"] is False
    assert manifest["auto_approval"] is False
    assert all(code == 0 for code in manifest["render_exit_codes"].values())
    assert manifest["contact_sheet_created"] is True
    assert manifest["contact_sheet_path"].endswith("contact_sheet.png")
    assert manifest["contact_sheet_source_count"] == 3
    assert all(row["source_image_texture_attempted"] is False for row in manifest["variant_rows"])
    assert all(row["source_image_texture_loaded"] is False for row in manifest["variant_rows"])
    assert all(row["source_image_texture_mode"] == "placeholder_missing_source" for row in manifest["variant_rows"])
    assert all(row["placeholder_used"] is True for row in manifest["variant_rows"])
    assert all(row["burn_in_position_mode"] == "bottom_safe_footer_tag" for row in manifest["variant_rows"])
    assert all(row["burn_in_treatment_mode"] == "bottom_safe_footer_tag" for row in manifest["variant_rows"])
    assert all(row["source_photo_crop_mode"] == "fit_1080x1350_right_focus" for row in manifest["variant_rows"])
    assert manifest["variant_rows"][0]["photo_anchor_type_treatment_mode"] == "open_scrim_hierarchy"
    assert [row["source_photo_focus_region"]["x"] for row in manifest["variant_rows"]] == [0.76, 0.75, 0.77]
    assert [row["subject_crop_balance_mode"] for row in manifest["variant_rows"]] == [
        "face_safe_open_balance",
        "score_weighted_center_balance",
        "editorial_face_open_balance",
    ]
    assert [row["composition_treatment_mode"] for row in manifest["variant_rows"]] == [
        "full_photo_background_scrim",
        "score_forward_open_editorial",
        "clean_editorial_fullbleed",
    ]
    assert [row["score_typography_treatment"] for row in manifest["variant_rows"]] == [
        "open_editorial_type",
        "score_drama_open_type",
        "open_editorial_type",
    ]
    assert all(row["photo_texture_render_layer_mode"] == "texture_front_no_frame_cover" for row in manifest["variant_rows"])
    assert all(row["review_only_derived_crop"] is False for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["burn_in_inside_canvas"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["burn_in_off_primary_body"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["frame_clutter_reduced"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["score_panel_softened"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["split_panel_softened"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["photo_type_integration_improved"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["face_edge_clipping_reduced"] is True for row in manifest["variant_rows"])
    assert all(row["layout_polish_checks"]["text_kept_off_face"] is True for row in manifest["variant_rows"])
    assert manifest["variant_rows"][0]["layout_polish_checks"]["split_panel_removed_or_minimized"] is True
    assert manifest["variant_rows"][0]["layout_polish_checks"]["full_photo_background_layer"] is True

    for variant_id in ["variant_01_photo_anchor", "variant_02_score_drama", "variant_03_clean_editorial"]:
        assert (out_dir / f"{variant_id}.png").exists()
        with Image.open(out_dir / f"{variant_id}.png") as image:
            assert image.size == (1080, 1350)

    assert contact_sheet.size[0] > 1000
    assert contact_sheet.size[1] > 500
    assert "photo-first hero" in report
    assert "pause_for_external_visual_qa" in report
    assert "source image is missing" in report.lower()
    assert "Review-only derived crop mode" in report
    assert "Layout polish checks" in report
    assert [row["variant_id"] for row in rows] == [
        "variant_01_photo_anchor",
        "variant_02_score_drama",
        "variant_03_clean_editorial",
    ]
    assert all(row["operator_decision"] == "" for row in rows)
    assert all(row["operator_notes"] == "" for row in rows)


def test_derive_review_only_crop_path_creates_run_scoped_right_focus_crop(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    source = tmp_path / "source.png"
    write_right_focus_source_image(source)

    out_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_composition_variants"
    spec = {
        "variant_id": "variant_01_photo_anchor",
        "source_photo_crop_mode": "fit_1080x1350_right_focus",
        "source_photo_focus_region": {"x": 0.82, "y": 0.5},
    }

    crop_path, metadata = module.derive_review_only_crop_path(source, out_dir, spec)

    assert crop_path.parent == out_dir / "review_only_derived_crops"
    assert crop_path.exists()
    assert metadata["review_only_derived_crop"] is True
    assert metadata["source_photo_crop_mode"] == "fit_1080x1350_right_focus"
    assert metadata["source_photo_focus_region"] == {"x": 0.82, "y": 0.5}
    assert metadata["render_source_image_path"] == crop_path.as_posix()
    with Image.open(crop_path) as cropped:
        assert cropped.size == (1080, 1350)
