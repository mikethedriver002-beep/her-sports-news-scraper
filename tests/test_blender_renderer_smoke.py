from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_blender_renderer_smoke_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_blender_renderer_smoke_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_make_scene_payload_is_review_only_and_4x5() -> None:
    module = load_module()
    payload = module.make_scene_payload()

    assert payload["version"] == "hsd-blender-renderer-smoke-v1-review-only"
    assert payload["review_only"] is True
    assert payload["artifact_only"] is True
    assert payload["burn_in_text"] == "REVIEW ONLY - BLENDER SMOKE TEST"
    assert payload["render"]["width"] == 1080
    assert payload["render"]["height"] == 1350
    assert payload["render"]["output_filename"] == "blender_renderer_smoke_4x5.png"
    assert payload["render"]["engine"] == "CYCLES"
    assert payload["render"]["samples"] == 8
    assert len(payload["objects"]) == 7
    assert payload["objects"][-1]["type"] == "text"
    assert payload["objects"][-1]["body"] == "REVIEW ONLY - BLENDER SMOKE TEST"


def test_build_manifest_uses_run_scoped_paths_and_guardrails(tmp_path: Path) -> None:
    module = load_module()
    scene = tmp_path / "run" / "files" / "blender_renderer_smoke" / "scene_payload.json"
    out = tmp_path / "run" / "files" / "blender_renderer_smoke" / "blender_renderer_smoke_4x5.png"

    manifest = module.build_manifest(
        blender_executable=Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"),
        blender_version="Blender 5.1.2",
        scene_payload_path=scene,
        output_png_path=out,
        status="blender_renderer_smoke_rendered",
        render_exit_code=0,
    )

    assert manifest["blender_executable"].endswith("Blender 5.1/blender.exe")
    assert manifest["blender_version"] == "Blender 5.1.2"
    assert manifest["scene_payload_path"].endswith("blender_renderer_smoke/scene_payload.json")
    assert manifest["output_png_path"].endswith("blender_renderer_smoke/blender_renderer_smoke_4x5.png")
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["publish_ready"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["move_files"] is False
    assert manifest["publishing"] is False
    assert manifest["production_renderer_replacement"] is False


def test_main_writes_blocked_manifest_when_blender_version_probe_fails(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "resolve_blender_executable", lambda explicit=None: Path(r"C:\fake\blender.exe"))
    monkeypatch.setattr(module, "probe_blender_version", lambda blender_executable: (_ for _ in ()).throw(RuntimeError("missing blender")))

    assert module.main([]) == 1

    manifest = json.loads((run_dir / "blender_renderer_smoke" / "blender_renderer_smoke_manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "blender_renderer_smoke" / "blender_renderer_smoke_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "blender_renderer_smoke_blocked_version_probe_failed"
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["publish_ready"] is False
    assert manifest["production_renderer_replacement"] is False
    assert "Blender version probe failed" in report


def test_main_writes_render_artifact_with_stubbed_success(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    fake_blender = tmp_path / "fake" / "blender.exe"
    fake_blender.parent.mkdir(parents=True)
    fake_blender.write_text("stub", encoding="utf-8")
    monkeypatch.setattr(module, "resolve_blender_executable", lambda explicit=None: fake_blender)
    monkeypatch.setattr(module, "probe_blender_version", lambda blender_executable: "Blender 5.1.2")

    def fake_run_blender_render(blender_executable, runner_path, scene_payload_path, output_png_path):
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (1080, 1350), (12, 18, 32, 255)).save(output_png_path, "PNG")
        return module.CommandResult(0, "render ok", "")

    monkeypatch.setattr(module, "run_blender_render", fake_run_blender_render)

    assert module.main([]) == 0

    out = run_dir / "blender_renderer_smoke"
    manifest = json.loads((out / "blender_renderer_smoke_manifest.json").read_text(encoding="utf-8"))
    payload = json.loads((out / "scene_payload.json").read_text(encoding="utf-8"))
    image = Image.open(out / "blender_renderer_smoke_4x5.png")
    report = (out / "blender_renderer_smoke_report.md").read_text(encoding="utf-8")

    assert manifest["status"] == "blender_renderer_smoke_rendered"
    assert manifest["blender_version"] == "Blender 5.1.2"
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["publish_ready"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["move_files"] is False
    assert manifest["publishing"] is False
    assert manifest["production_renderer_replacement"] is False
    assert Path(manifest["scene_payload_path"]).exists()
    assert Path(manifest["output_png_path"]).exists()
    assert payload["burn_in_text"] == "REVIEW ONLY - BLENDER SMOKE TEST"
    assert image.size == (1080, 1350)
    assert "Rendered exactly one review-only 4:5 PNG" in report
