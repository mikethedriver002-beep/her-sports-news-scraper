from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "render_hsd_blender_apcs048_renderer_proof_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_hsd_blender_apcs048_renderer_proof_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_png(path: Path, size: tuple[int, int] = (926, 695)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (180, 40, 68)).save(path, "PNG")


def test_prepare_source_reference_copies_only_quarantine_source_to_proof_inputs(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "repo" / "data" / "assets" / "quarantine" / "review_only_candidates" / "action_photo_candidates" / "batch" / "apcs048_operator_review.png"
    write_png(source)
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "apcs048_renderer_proof_v1"

    info = module.prepare_source_reference(source, output_dir)

    assert info["source_reference_present"] is True
    assert info["source_reference_is_quarantine_review_only_candidate"] is True
    assert info["proof_input_copied"] is True
    assert info["proof_input_path"].endswith("outputs/local/tmp/apcs048_renderer_proof_v1/proof_inputs/quarantine_review_reference/apcs048_operator_review.png")
    assert Path(info["proof_input_path"]).exists()
    assert "approved" not in info["proof_input_path"].lower()


def test_prepare_source_reference_does_not_copy_non_quarantine_source(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "desktop" / "apcs048_operator_review.png"
    write_png(source)
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "apcs048_renderer_proof_v1"
    stale_proof_input = output_dir / "proof_inputs" / "quarantine_review_reference" / "apcs048_operator_review.png"
    write_png(stale_proof_input)

    info = module.prepare_source_reference(source, output_dir)

    assert info["source_reference_present"] is True
    assert info["source_reference_is_quarantine_review_only_candidate"] is False
    assert info["proof_input_copied"] is False
    assert not Path(info["proof_input_path"]).exists()


def test_resolve_source_reference_prefers_repo_local_quarantine_candidate(tmp_path: Path) -> None:
    module = load_module()
    source = (
        tmp_path
        / "repo"
        / "data"
        / "assets"
        / "quarantine"
        / "review_only_candidates"
        / "action_photo_candidates"
        / "manual_decision_batch"
        / "au_volleyball_jordan_thompson"
        / "apcs048_operator_review.png"
    )
    write_png(source)

    resolved = module.resolve_source_reference(None, tmp_path / "repo")

    assert resolved == source.resolve()


def test_resolve_source_reference_allows_explicit_other_worktree_source(tmp_path: Path) -> None:
    module = load_module()
    explicit = (
        tmp_path
        / "other-worktree"
        / "her-sports-news-scraper"
        / "data"
        / "assets"
        / "quarantine"
        / "review_only_candidates"
        / "action_photo_candidates"
        / "manual_decision_batch"
        / "au_volleyball_jordan_thompson"
        / "apcs048_operator_review.png"
    )
    write_png(explicit)

    resolved = module.resolve_source_reference(explicit, tmp_path / "repo")

    assert resolved == explicit.resolve()


def test_resolve_source_reference_requires_explicit_path_when_local_candidate_missing(tmp_path: Path) -> None:
    module = load_module()

    try:
        module.resolve_source_reference(None, tmp_path / "repo")
    except FileNotFoundError as exc:
        assert "Pass --source-reference explicitly" in str(exc)
        assert "data/assets/quarantine/review_only_candidates" in str(exc)
    else:
        raise AssertionError("resolve_source_reference should require an explicit source when local candidate is missing")


def test_build_variant_specs_locks_review_only_blender_stage_contract(tmp_path: Path) -> None:
    module = load_module()
    proof_input = tmp_path / "outputs" / "local" / "tmp" / "apcs048_renderer_proof_v1" / "proof_inputs" / "quarantine_review_reference" / "apcs048_operator_review.png"
    write_png(proof_input)
    specs = module.build_variant_specs(
        {
            "source_reference_path": str(tmp_path / "repo" / "data" / "assets" / "quarantine" / "review_only_candidates" / "x.png"),
            "proof_input_path": str(proof_input),
            "proof_input_present": True,
        }
    )

    assert [spec["variant_id"] for spec in specs] == [
        "variant_01_court_depth_hero",
        "variant_02_arena_spotlight_crop",
        "variant_03_premium_matchday_poster",
    ]
    assert all(spec["canvas"] == {"width": 1080, "height": 1350} for spec in specs)
    assert all(spec["candidate_id"] == "APCS048" for spec in specs)
    assert all(spec["entity_name"] == "Jordan Thompson" for spec in specs)
    assert all(spec["source_image_texture_attempted"] is True for spec in specs)
    assert all("REVIEW ONLY" in spec["review_only_label"] for spec in specs)
    assert all("NOT ASSET APPROVED" in spec["review_only_label"] for spec in specs)
    assert all("3D volleyball court floor" in spec["stage_features"] for spec in specs)
    assert all("shadow-casting source reference panel" in spec["stage_features"] for spec in specs)
    assert specs[0]["headline_title_size"] == 0.2
    assert specs[0]["proof_line_text"] == "REVIEW ONLY / NOT APPROVED"


def test_runner_script_contains_first_class_blender_scene_features(tmp_path: Path) -> None:
    module = load_module()
    specs = module.build_variant_specs(
        {
            "source_reference_path": "data/assets/quarantine/review_only_candidates/x.png",
            "proof_input_path": str(tmp_path / "proof_inputs" / "apcs048_operator_review.png"),
            "proof_input_present": True,
        }
    )
    runner = module.build_runner_script(specs)

    assert "bpy.ops.mesh.primitive_plane_add" in runner
    assert "deep_volleyball_court_floor" in runner
    assert "candidate_review_spotlight" in runner
    assert "quarantine_source_reference_photo_plane" in runner
    assert "bpy.data.images.load" in runner
    assert module.TEXTURE_STATUS_PREFIX in runner


def test_main_writes_manifest_report_csv_and_contact_sheet_with_stubbed_blender(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    source = tmp_path / "repo" / "data" / "assets" / "quarantine" / "review_only_candidates" / "action_photo_candidates" / "batch" / "apcs048_operator_review.png"
    write_png(source)
    out_dir = tmp_path / "outputs" / "local" / "tmp" / "apcs048_renderer_proof_v1"
    fake_blender = tmp_path / "fake" / "blender.exe"
    fake_blender.parent.mkdir(parents=True, exist_ok=True)
    fake_blender.write_text("stub", encoding="utf-8")

    def fake_probe_blender_version(blender_executable: Path) -> str:
        assert blender_executable == fake_blender
        return "Blender 5.1.2"

    def fake_run_blender_render(blender_executable: Path, runner_file: Path, variant_id: str, output_png_path: Path):
        assert blender_executable == fake_blender
        write_png(output_png_path, size=(1080, 1350))
        output_png_path.with_suffix(".texture_status.json").write_text(
            json.dumps(
                {
                    "attempted": True,
                    "loaded": True,
                    "mode": "texture_loaded",
                    "stage_geometry": True,
                    "court_lines": 7,
                    "layered_planes": 3,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(args=["blender"], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(module, "probe_blender_version", fake_probe_blender_version)
    monkeypatch.setattr(module, "run_blender_render", fake_run_blender_render)

    assert module.main(["--source-reference", str(source), "--output-dir", str(out_dir), "--blender-executable", str(fake_blender)]) == 0

    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (out_dir / "visual_report.md").read_text(encoding="utf-8")
    csv_text = (out_dir / "manual_visual_review_intake.csv").read_text(encoding="utf-8")

    assert manifest["status"] == "apcs048_renderer_proof_ready"
    assert manifest["review_only"] is True
    assert manifest["asset_approved"] is False
    assert manifest["publish_ready"] is False
    assert manifest["guardrails"]["asset_downloads"] is False
    assert manifest["guardrails"]["source_fetching"] is False
    assert manifest["proof_input_copied"] is True
    assert manifest["contact_sheet_created"] is True
    assert manifest["variant_count"] == 3
    assert all(row["dimensions"] == {"width": 1080, "height": 1350} for row in manifest["variant_rows"])
    assert all(row["source_image_texture_loaded"] is True for row in manifest["variant_rows"])
    assert "not asset-approved or publish-ready" in report
    assert "publish_ready" in csv_text
    assert "true" in csv_text
