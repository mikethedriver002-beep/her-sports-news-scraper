from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "render_hsd_blender_apq_4x5_prototype_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("render_hsd_blender_apq_4x5_prototype_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_make_scene_payload_reflects_contract_sample_and_review_only_context(tmp_path: Path) -> None:
    module = load_module()
    sample = tmp_path / "sample_apq001_scene_payload.json"
    write_json(
        sample,
        {
            "schema_version": "blender_apq_scene_payload_contract.v1",
            "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
            "source_context": {
                "source_family": "apq001_action_photo_composition_review",
                "apq_candidate_id": "APQ001",
                "quarantine_only": True,
                "quarantine_root": "data/assets/quarantine/review_only_candidates",
            },
            "action_photo_slot": {
                "quarantine_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg",
                "asset_approved": False,
                "rights_class": "unknown",
                "identity_confidence": "unreviewed",
                "intended_review_only_use": "review_only_blender_prototype",
            },
            "blender_scene": {
                "renderer_invocation": "not_in_scope_contract_only",
                "render_engine_hint": "CYCLES",
                "source_smoke_payload_path": "outputs/local/latest/files/blender_renderer_smoke/scene_payload.json",
            },
            "burn_in": {
                "required": True,
                "text": "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE",
                "placement": "visible bottom-band or equivalent watermark on every review render",
            },
        },
    )

    payload = module.make_scene_payload(sample)

    assert payload["version"] == "hsd-blender-apq-4x5-prototype-v1-review-only"
    assert payload["schema_version"] == "blender_apq_scene_payload_contract.v1"
    assert payload["review_only"] is True
    assert payload["apq001_quarantine_only"] is True
    assert payload["approved_input"] is False
    assert payload["canvas"]["width"] == 1080
    assert payload["canvas"]["height"] == 1350
    assert payload["canvas"]["aspect_ratio"] == "4:5"
    assert payload["source_payload_schema_version"] == "blender_apq_scene_payload_contract.v1"
    assert payload["source_context"]["apq_candidate_id"] == "APQ001"
    assert payload["source_context"]["quarantine_only"] is True
    assert payload["action_photo_slot"]["quarantine_path"].startswith("data/assets/quarantine/review_only_candidates/")
    assert payload["action_photo_slot"]["asset_approved"] is False
    assert payload["blender_scene"]["renderer_invocation"] == "not_in_scope_contract_only"
    assert payload["burn_in"]["required"] is True
    assert payload["burn_in"]["text"] == "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE"
    assert payload["review_only_guardrails"]["publish_ready"] is False
    assert payload["review_only_guardrails"]["auto_publish"] is False
    assert payload["review_only_guardrails"]["production_renderer_replacement"] is False


def test_build_manifest_contains_required_review_only_false_fields(tmp_path: Path) -> None:
    module = load_module()
    scene = tmp_path / "outputs" / "local" / "latest" / "files" / "blender_apq_scene_payload_contract" / "sample_apq001_scene_payload.json"
    out = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_4x5_prototype" / "blender_apq_4x5_prototype_4x5.png"

    manifest = module.build_manifest(
        blender_executable=Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"),
        blender_version="Blender 5.1.0",
        scene_payload_path=scene,
        output_png_path=out,
        status="blender_apq_4x5_prototype_rendered",
        render_exit_code=0,
    )

    assert manifest["blender_executable"].endswith("Blender 5.1/blender.exe")
    assert manifest["blender_version"] == "Blender 5.1.0"
    assert manifest["scene_payload_path"].endswith("blender_apq_scene_payload_contract/sample_apq001_scene_payload.json")
    assert manifest["output_png_path"].endswith("blender_apq_4x5_prototype/blender_apq_4x5_prototype_4x5.png")
    assert manifest["review_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    assert manifest["approved_input"] is False
    assert manifest["publish_ready"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["download_performed"] is False
    assert manifest["move_files"] is False
    assert manifest["protected_asset_moves"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["production_renderer_replacement"] is False
    assert manifest["publishing"] is False
    assert manifest["auto_publish"] is False
    assert manifest["auto_approval"] is False


def test_main_writes_one_png_and_manifest_with_stubbed_blender(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    run_root = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_4x5_prototype"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_root))

    scene_payload = tmp_path / "outputs" / "local" / "latest" / "files" / "blender_apq_scene_payload_contract" / "sample_apq001_scene_payload.json"
    write_json(
        scene_payload,
        {
            "schema_version": "blender_apq_scene_payload_contract.v1",
            "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
            "source_context": {"source_family": "apq001_action_photo_composition_review", "apq_candidate_id": "APQ001", "quarantine_only": True, "quarantine_root": "data/assets/quarantine/review_only_candidates"},
            "action_photo_slot": {"quarantine_path": "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg", "asset_approved": False},
            "blender_scene": {"renderer_invocation": "not_in_scope_contract_only", "render_engine_hint": "CYCLES"},
            "burn_in": {"required": True, "text": "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE", "placement": "visible bottom-band or equivalent watermark on every review render"},
        },
    )

    fake_blender = tmp_path / "fake" / "blender.exe"
    fake_blender.parent.mkdir(parents=True)
    fake_blender.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(module, "resolve_scene_payload_path", lambda explicit=None: scene_payload)
    monkeypatch.setattr(module, "resolve_blender_executable", lambda explicit=None: fake_blender)
    monkeypatch.setattr(module, "probe_blender_version", lambda blender_executable: "Blender 5.1.0")

    def fake_run_blender_render(blender_executable, runner_file, scene_payload_path, output_png_path):
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (1080, 1350), (13, 18, 31, 255)).save(output_png_path, "PNG")
        return type("Result", (), {"returncode": 0, "stdout": "render ok", "stderr": ""})()

    monkeypatch.setattr(module, "run_blender_render", fake_run_blender_render)

    assert module.main([]) == 0

    manifest = json.loads((run_root / "blender_apq_4x5_prototype_manifest.json").read_text(encoding="utf-8"))
    image = Image.open(run_root / "blender_apq_4x5_prototype_4x5.png")

    assert image.size == (1080, 1350)
    assert manifest["status"] == "blender_apq_4x5_prototype_rendered"
    assert manifest["review_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    assert manifest["approved_input"] is False
    assert manifest["publish_ready"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["download_performed"] is False
    assert manifest["move_files"] is False
    assert manifest["protected_asset_moves"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["production_renderer_replacement"] is False
    assert manifest["publishing"] is False
    assert manifest["auto_publish"] is False
    assert manifest["auto_approval"] is False
    assert manifest["source_payload_schema_version"] == "blender_apq_scene_payload_contract.v1"
