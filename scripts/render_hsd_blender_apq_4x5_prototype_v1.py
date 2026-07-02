from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir

try:
    from PIL import Image
except Exception:  # pragma: no cover - runtime fallback
    Image = None  # type: ignore[assignment]


VERSION = "hsd-blender-apq-4x5-prototype-v1-review-only"
SCHEMA_VERSION = "blender_apq_scene_payload_contract.v1"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
DEFAULT_SCENE_PAYLOAD = Path("outputs/local/latest/files/blender_apq_scene_payload_contract/sample_apq001_scene_payload.json")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/blender_apq_4x5_prototype")
PNG_NAME = "blender_apq_4x5_prototype_4x5.png"
MANIFEST_NAME = "blender_apq_4x5_prototype_manifest.json"
RUNNER_NAME = "blender_apq_4x5_prototype_runner.py"
BURN_IN_TEXT = "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE"
QUARANTINE_ROOT_REL = Path("data/assets/quarantine/review_only_candidates")

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "move_files": False,
    "paid_apis": False,
    "publish_ready": False,
    "publishing": False,
    "protected_asset_moves": False,
    "production_renderer_replacement": False,
    "renderer_behavior_change": False,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir() -> Path:
    root = run_output_dir()
    return root if root is not None else DEFAULT_OUTPUT_DIR


def resolve_scene_payload_path(explicit: str | None = None) -> Path:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.is_absolute() else (repo_root() / candidate)
    return repo_root() / DEFAULT_SCENE_PAYLOAD


def quarantine_root() -> Path:
    return repo_root() / QUARANTINE_ROOT_REL


def resolve_quarantine_photo_path(scene_payload_path: Path) -> Path:
    payload = json.loads(scene_payload_path.read_text(encoding="utf-8"))
    action_photo_slot = payload.get("action_photo_slot") if isinstance(payload.get("action_photo_slot"), dict) else {}
    raw_path = str(action_photo_slot.get("quarantine_path") or "").strip()
    if not raw_path:
        raise ValueError("scene payload is missing action_photo_slot.quarantine_path")

    candidate = Path(raw_path)
    resolved = candidate if candidate.is_absolute() else (repo_root() / candidate)
    resolved = resolved.resolve(strict=False)

    root = quarantine_root().resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("action_photo_slot.quarantine_path must stay under data/assets/quarantine/review_only_candidates/") from exc

    return resolved


def resolve_blender_executable(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.exists() else None
    return DEFAULT_BLENDER_EXECUTABLE if DEFAULT_BLENDER_EXECUTABLE.exists() else None


def output_png_path() -> Path:
    return resolve_output_dir() / PNG_NAME


def manifest_path() -> Path:
    return resolve_output_dir() / MANIFEST_NAME


def runner_path() -> Path:
    return resolve_output_dir() / RUNNER_NAME


def write_json_file(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def make_scene_payload(scene_payload_path: Path) -> dict[str, Any]:
    payload = json.loads(scene_payload_path.read_text(encoding="utf-8"))
    source_context = payload.get("source_context") if isinstance(payload.get("source_context"), dict) else {}
    action_photo_slot = payload.get("action_photo_slot") if isinstance(payload.get("action_photo_slot"), dict) else {}
    blender_scene = payload.get("blender_scene") if isinstance(payload.get("blender_scene"), dict) else {}
    burn_in = payload.get("burn_in") if isinstance(payload.get("burn_in"), dict) else {}
    canvas = payload.get("canvas") if isinstance(payload.get("canvas"), dict) else {}

    return {
        "version": VERSION,
        "schema_version": str(payload.get("schema_version") or SCHEMA_VERSION),
        "review_only": True,
        "apq001_quarantine_only": True,
        "approved_input": False,
        "canvas": {
            "width": int(canvas.get("width") or 1080),
            "height": int(canvas.get("height") or 1350),
            "aspect_ratio": str(canvas.get("aspect_ratio") or "4:5"),
        },
        "source_payload_path": scene_payload_path.as_posix(),
        "source_payload_schema_version": str(payload.get("schema_version") or SCHEMA_VERSION),
        "source_context": {
            "source_family": str(source_context.get("source_family") or "apq001_action_photo_composition_review"),
            "apq_candidate_id": str(source_context.get("apq_candidate_id") or "APQ001"),
            "quarantine_only": bool(source_context.get("quarantine_only", True)),
            "quarantine_root": str(source_context.get("quarantine_root") or "data/assets/quarantine/review_only_candidates"),
        },
        "action_photo_slot": {
            "quarantine_path": str(action_photo_slot.get("quarantine_path") or ""),
            "asset_approved": bool(action_photo_slot.get("asset_approved", False)),
            "rights_class": str(action_photo_slot.get("rights_class") or ""),
            "identity_confidence": str(action_photo_slot.get("identity_confidence") or ""),
            "intended_review_only_use": str(action_photo_slot.get("intended_review_only_use") or ""),
        },
        "blender_scene": {
            "renderer_invocation": str(blender_scene.get("renderer_invocation") or "contract_to_prototype_render"),
            "render_engine_hint": str(blender_scene.get("render_engine_hint") or "CYCLES"),
            "source_smoke_payload_path": str(blender_scene.get("source_smoke_payload_path") or ""),
        },
        "burn_in": {
            "required": bool(burn_in.get("required", True)),
            "text": str(burn_in.get("text") or BURN_IN_TEXT),
            "placement": str(burn_in.get("placement") or "bottom band watermark"),
        },
        "review_only_guardrails": dict(FALSE_GUARDRAILS),
    }


def build_manifest(
    *,
    blender_executable: Path | None,
    blender_version: str,
    scene_payload_path: Path,
    output_png_path: Path,
    status: str,
    render_exit_code: int,
    render_stdout: str = "",
    render_stderr: str = "",
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": status,
        "blender_executable": blender_executable.as_posix() if blender_executable else "",
        "blender_version": blender_version,
        "scene_payload_path": scene_payload_path.as_posix(),
        "source_payload_schema_version": SCHEMA_VERSION,
        "output_png_path": output_png_path.as_posix(),
        "review_only": True,
        "apq001_quarantine_only": True,
        "approved_input": False,
        "publish_ready": False,
        "approval_state_change": False,
        "asset_downloads": False,
        "download_performed": False,
        "move_files": False,
        "protected_asset_moves": False,
        "renderer_behavior_change": False,
        "production_renderer_replacement": False,
        "publishing": False,
        "auto_publish": False,
        "auto_approval": False,
        "render_exit_code": render_exit_code,
        "render_stdout": render_stdout,
        "render_stderr": render_stderr,
    }


def build_runner_script() -> str:
    return (
        textwrap.dedent(
            r'''
            from __future__ import annotations

            import argparse
            import json
            import math
            import sys
            from pathlib import Path

            import bpy
            BURN_IN_TEXT = "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE"
            BOLD_FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")
            BOLD_FONT = None


            def argv_after_double_dash() -> list[str]:
                if "--" not in sys.argv:
                    return []
                return sys.argv[sys.argv.index("--") + 1 :]


            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser()
                parser.add_argument("--scene-payload", required=True)
                parser.add_argument("--quarantine-photo-path", required=True)
                parser.add_argument("--output-png", required=True)
                return parser.parse_args(argv_after_double_dash())


            def rgba(values: list[int] | tuple[int, ...], alpha: float = 1.0) -> tuple[float, float, float, float]:
                r, g, b = values
                return (r / 255.0, g / 255.0, b / 255.0, alpha)


            def bold_font():
                global BOLD_FONT
                if BOLD_FONT is not None:
                    return BOLD_FONT
                if BOLD_FONT_PATH.exists():
                    BOLD_FONT = bpy.data.fonts.load(BOLD_FONT_PATH.as_posix(), check_existing=True)
                else:
                    BOLD_FONT = bpy.data.fonts[0] if bpy.data.fonts else None
                return BOLD_FONT


            def clear_scene() -> None:
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete(use_global=False)


            def set_world() -> None:
                world = bpy.data.worlds.new("APQPrototypeWorld")
                world.use_nodes = True
                scene = bpy.context.scene
                scene.world = world
                background = world.node_tree.nodes.get("Background")
                if background is not None:
                    background.inputs[0].default_value = (0.03, 0.04, 0.07, 1.0)
                    background.inputs[1].default_value = 0.85


            def setup_camera() -> None:
                bpy.ops.object.camera_add(location=(0.0, -8.9, 1.95))
                camera = bpy.context.active_object
                camera.data.type = "ORTHO"
                camera.data.ortho_scale = 8.0
                target = bpy.data.objects.new("APQTarget", None)
                target.location = (0.0, 0.0, 0.75)
                bpy.context.collection.objects.link(target)
                constraint = camera.constraints.new(type="TRACK_TO")
                constraint.target = target
                constraint.track_axis = "TRACK_NEGATIVE_Z"
                constraint.up_axis = "UP_Y"
                bpy.context.scene.camera = camera


            def make_material(name: str, color: tuple[float, float, float, float], *, roughness: float = 0.45, alpha: float = 1.0, emission: float = 0.0) -> bpy.types.Material:
                material = bpy.data.materials.new(name)
                material.use_nodes = True
                material.blend_method = "BLEND" if alpha < 1.0 else "OPAQUE"
                nodes = material.node_tree.nodes
                principled = nodes.get("Principled BSDF")
                if principled is not None:
                    principled.inputs["Base Color"].default_value = color
                    principled.inputs["Roughness"].default_value = roughness
                    principled.inputs["Alpha"].default_value = alpha
                    if emission > 0.0:
                        if "Emission Color" in principled.inputs:
                            principled.inputs["Emission Color"].default_value = color
                        if "Emission Strength" in principled.inputs:
                            principled.inputs["Emission Strength"].default_value = emission
                        elif "Emission" in principled.inputs:
                            principled.inputs["Emission"].default_value = color
                return material


            def apply_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
                if obj.data and hasattr(obj.data, "materials"):
                    obj.data.materials.clear()
                    obj.data.materials.append(material)


            def add_plane(name: str, location: tuple[float, float, float], rotation: tuple[float, float, float], scale: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
                bpy.ops.mesh.primitive_plane_add(location=location, rotation=rotation)
                obj = bpy.context.active_object
                obj.name = name
                obj.scale = scale
                apply_material(obj, material)
                return obj


            def add_text(
                label: str,
                *,
                location: tuple[float, float, float],
                size: float,
                color: tuple[float, float, float, float],
                rotation: tuple[float, float, float] = (math.radians(90.0), 0.0, 0.0),
                extrude: float = 0.03,
                bevel: float = 0.008,
                align_x: str = "LEFT",
            ) -> bpy.types.Object:
                bpy.ops.object.text_add(location=location, rotation=rotation)
                obj = bpy.context.active_object
                obj.data.body = label
                obj.data.size = size
                obj.data.extrude = extrude
                obj.data.bevel_depth = bevel
                obj.data.align_x = align_x
                obj.data.resolution_u = 5
                obj.data.fill_mode = "BOTH"
                font = bold_font()
                if font is not None:
                    obj.data.font = font
                material = make_material(f"{label}_Text", color, roughness=0.22, emission=4.0)
                apply_material(obj, material)
                return obj


            def add_photo_plane(photo_path: Path) -> None:
                bpy.ops.mesh.primitive_plane_add(location=(-2.3, 0.25, 0.4), rotation=(math.radians(-90.0), 0.0, math.radians(-3.0)))
                obj = bpy.context.active_object
                obj.scale = (1.85, 2.35, 1.0)
                if photo_path.exists():
                    image = bpy.data.images.load(photo_path.as_posix(), check_existing=True)
                    material = bpy.data.materials.new("APQPhotoMaterial")
                    material.use_nodes = True
                    material.blend_method = "OPAQUE"
                    nodes = material.node_tree.nodes
                    links = material.node_tree.links
                    for node in list(nodes):
                        nodes.remove(node)
                    coords = nodes.new("ShaderNodeTexCoord")
                    mapping = nodes.new("ShaderNodeMapping")
                    texture = nodes.new("ShaderNodeTexImage")
                    texture.image = image
                    texture.interpolation = "Smart"
                    texture.projection = "FLAT"
                    principled = nodes.new("ShaderNodeBsdfPrincipled")
                    output = nodes.new("ShaderNodeOutputMaterial")
                    mapping.inputs["Rotation"].default_value[2] = math.pi
                    links.new(coords.outputs["UV"], mapping.inputs["Vector"])
                    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
                    links.new(texture.outputs["Color"], principled.inputs["Base Color"])
                    links.new(texture.outputs["Alpha"], principled.inputs["Alpha"])
                    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
                    principled.inputs["Roughness"].default_value = 0.35
                    if "Specular IOR Level" in principled.inputs:
                        principled.inputs["Specular IOR Level"].default_value = 0.35
                    elif "Specular" in principled.inputs:
                        principled.inputs["Specular"].default_value = 0.35
                    apply_material(obj, material)
                else:
                    material = make_material("APQPhotoPlaceholder", (0.07, 0.09, 0.14, 1.0), roughness=0.82)
                    apply_material(obj, material)
                add_text(
                    "REVIEW-ONLY PHOTO SLOT",
                    location=(-3.55, 0.14, 1.74),
                    size=0.19,
                    color=(0.94, 0.95, 0.98, 1.0),
                )
                add_text(
                    "APQ001 QUARANTINE REFERENCE",
                    location=(-3.55, 0.14, 1.46),
                    size=0.12,
                    color=(0.72, 0.77, 0.86, 1.0),
                )
                add_text(
                    "NO APPROVAL / NO MOVES",
                    location=(-3.55, 0.14, -1.04),
                    size=0.12,
                    color=(0.9, 0.57, 0.62, 1.0),
                )


            def add_scene(payload: dict[str, object]) -> None:
                source_context = payload.get("source_context") if isinstance(payload.get("source_context"), dict) else {}
                action_photo_slot = payload.get("action_photo_slot") if isinstance(payload.get("action_photo_slot"), dict) else {}
                burn_in = payload.get("burn_in") if isinstance(payload.get("burn_in"), dict) else {}
                photo_path = Path(str(payload.get("__quarantine_photo_path") or ""))
                photo_exists = photo_path.exists()

                backdrop = add_plane(
                    "Backdrop",
                    (0.0, 1.9, 0.0),
                    (math.radians(-90.0), 0.0, 0.0),
                    (5.9, 4.6, 1.0),
                    make_material("BackdropMaterial", (0.04, 0.05, 0.08, 1.0), roughness=1.0),
                )
                backdrop.location = (0.0, 2.0, -0.02)

                add_plane(
                    "EditorialScrim",
                    (1.9, 0.14, 0.95),
                    (math.radians(-90.0), 0.0, 0.0),
                    (2.4, 3.95, 1.0),
                    make_material("ScrimMaterial", (0.01, 0.02, 0.03, 1.0), roughness=0.92, alpha=0.82),
                )
                add_plane(
                    "BottomBand",
                    (0.0, -0.08, -1.62),
                    (math.radians(-90.0), 0.0, 0.0),
                    (5.8, 0.42, 1.0),
                    make_material("BottomBandMaterial", (0.82, 0.12, 0.18, 1.0), roughness=0.82),
                )

                add_photo_plane(photo_path)

                bpy.ops.mesh.primitive_plane_add(location=(2.05, 0.16, 0.2), rotation=(math.radians(-90.0), 0.0, 0.0))
                stat_plate = bpy.context.active_object
                stat_plate.scale = (2.05, 2.15, 1.0)
                apply_material(stat_plate, make_material("StatPlateMaterial", (0.03, 0.04, 0.07, 1.0), roughness=0.88, alpha=0.72))

                add_text("FINAL", location=(1.72, 0.10, 1.6), size=1.5, color=(0.98, 0.98, 0.98, 1.0))
                add_text("APQ001", location=(1.78, 0.08, 1.05), size=0.72, color=(0.92, 0.72, 0.28, 1.0))
                add_text("0 - 0", location=(1.78, 0.12, 0.58), size=1.2, color=(0.97, 0.97, 0.98, 1.0))
                add_text("STAT LINE", location=(1.78, 0.11, 0.1), size=0.56, color=(0.73, 0.79, 0.88, 1.0))
                add_text(
                    "QUARANTINE REVIEW CONTEXT",
                    location=(1.78, 0.08, -0.24),
                    size=0.34,
                    color=(0.58, 0.63, 0.72, 1.0),
                )

                if not photo_exists:
                    add_text(
                        "APQ001 SOURCE IMAGE NOT PRESENT LOCALLY",
                        location=(-2.9, 0.12, -0.82),
                        size=0.19,
                        color=(0.95, 0.95, 0.96, 1.0),
                    )

                burn_band_text = str(burn_in.get("text") or BURN_IN_TEXT)
                add_text(
                    burn_band_text,
                    location=(0.0, -0.16, -1.42),
                    size=0.62,
                    color=(0.98, 0.98, 0.98, 1.0),
                    align_x="CENTER",
                    extrude=0.0,
                    bevel=0.0,
                )

                add_text(
                    str(source_context.get("apq_candidate_id") or "APQ001"),
                    location=(-4.35, 0.12, 1.92),
                    size=0.24,
                    color=(0.93, 0.7, 0.22, 1.0),
                )


            def add_lights() -> None:
                bpy.ops.object.light_add(type="AREA", location=(-3.0, -4.0, 4.4))
                key = bpy.context.active_object
                key.data.energy = 2200.0
                key.data.shape = "RECTANGLE"
                key.data.size = 5.2
                key.data.size_y = 3.6

                bpy.ops.object.light_add(type="AREA", location=(3.2, -3.0, 2.1))
                fill = bpy.context.active_object
                fill.data.energy = 1050.0
                fill.data.shape = "RECTANGLE"
                fill.data.size = 3.0
                fill.data.size_y = 2.4

                bpy.ops.object.light_add(type="AREA", location=(0.8, 2.0, 3.6))
                top = bpy.context.active_object
                top.data.energy = 450.0
                top.data.shape = "RECTANGLE"
                top.data.size = 2.8
                top.data.size_y = 2.0

                bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, 0.0))
                sun = bpy.context.active_object
                sun.rotation_euler = (math.radians(30.0), 0.0, math.radians(-25.0))
                sun.data.energy = 1.0


            def configure_render(output_png: Path) -> None:
                scene = bpy.context.scene
                scene.render.engine = "BLENDER_EEVEE_NEXT"
                scene.render.resolution_x = 1080
                scene.render.resolution_y = 1350
                scene.render.resolution_percentage = 100
                scene.render.filepath = output_png.as_posix()
                scene.render.image_settings.file_format = "PNG"
                scene.render.image_settings.color_mode = "RGBA"
                if hasattr(scene, "eevee"):
                    if hasattr(scene.eevee, "taa_render_samples"):
                        scene.eevee.taa_render_samples = 1
                    if hasattr(scene.eevee, "taa_samples"):
                        scene.eevee.taa_samples = 1
                    if hasattr(scene.eevee, "use_gtao"):
                        scene.eevee.use_gtao = False
                    if hasattr(scene.eevee, "use_bloom"):
                        scene.eevee.use_bloom = False
                scene.render.film_transparent = False


            def main() -> int:
                args = parse_args()
                payload = json.loads(Path(args.scene_payload).read_text(encoding="utf-8"))
                payload["__quarantine_photo_path"] = str(Path(args.quarantine_photo_path))
                if int(payload.get("canvas", {}).get("width", 0)) != 1080 or int(payload.get("canvas", {}).get("height", 0)) != 1350:
                    raise RuntimeError("scene payload must remain 1080x1350")

                clear_scene()
                set_world()
                setup_camera()
                add_scene(payload)
                add_lights()
                configure_render(Path(args.output_png))
                bpy.ops.render.render(write_still=True)
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            '''
        ).strip()
        + "\n"
    )


def write_runner_script() -> Path:
    path = runner_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_runner_script(), encoding="utf-8")
    return path


def probe_blender_version(blender_executable: Path) -> str:
    result = subprocess.run(
        [str(blender_executable), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Blender version probe failed")
    return (result.stdout or result.stderr).strip().splitlines()[0]


def run_blender_render(
    blender_executable: Path,
    runner_file: Path,
    scene_payload_path: Path,
    quarantine_photo_path: Path,
    output_png_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(blender_executable),
            "--background",
            "--factory-startup",
            "--python",
            str(runner_file),
            "--",
            "--scene-payload",
            str(scene_payload_path),
            "--quarantine-photo-path",
            str(quarantine_photo_path),
            "--output-png",
            str(output_png_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def verify_png_dimensions(path: Path) -> tuple[int, int]:
    if Image is None:
        raise RuntimeError("Pillow is unavailable for PNG verification")
    with Image.open(path) as image:
        return image.size


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one review-only 4:5 Blender prototype PNG from the APQ001 contract sample.")
    parser.add_argument("--scene-payload", default="", help="Optional explicit path to the APQ001 scene payload sample.")
    parser.add_argument("--blender-executable", default="", help="Optional Blender executable override.")
    args = parser.parse_args(argv)

    output_dir = resolve_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    scene_payload_path = resolve_scene_payload_path(args.scene_payload or None)
    if not scene_payload_path.exists():
        manifest = build_manifest(
            blender_executable=None,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_apq_4x5_prototype_blocked_missing_scene_payload",
            render_exit_code=1,
        )
        write_json_file(manifest_path(), manifest)
        return 1

    prototype_payload = make_scene_payload(scene_payload_path)
    if prototype_payload["canvas"]["width"] != 1080 or prototype_payload["canvas"]["height"] != 1350:
        manifest = build_manifest(
            blender_executable=None,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_apq_4x5_prototype_blocked_invalid_canvas",
            render_exit_code=1,
        )
        write_json_file(manifest_path(), manifest)
        return 1

    try:
        quarantine_photo_path = resolve_quarantine_photo_path(scene_payload_path)
    except Exception as exc:
        manifest = build_manifest(
            blender_executable=None,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_apq_4x5_prototype_blocked_invalid_quarantine_path",
            render_exit_code=1,
            render_stderr=str(exc),
        )
        write_json_file(manifest_path(), manifest)
        return 1

    blender_executable = resolve_blender_executable(args.blender_executable or None)
    if blender_executable is None:
        manifest = build_manifest(
            blender_executable=None,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_apq_4x5_prototype_blocked_missing_blender",
            render_exit_code=1,
        )
        write_json_file(manifest_path(), manifest)
        return 1

    try:
        blender_version = probe_blender_version(blender_executable)
    except Exception as exc:
        manifest = build_manifest(
            blender_executable=blender_executable,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_apq_4x5_prototype_blocked_version_probe_failed",
            render_exit_code=1,
            render_stderr=str(exc),
        )
        write_json_file(manifest_path(), manifest)
        return 1

    runner_file: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
            handle.write(build_runner_script())
            runner_file = Path(handle.name)

        render_result = run_blender_render(
            blender_executable,
            runner_file,
            scene_payload_path,
            quarantine_photo_path,
            output_png_path(),
        )
        if render_result.returncode != 0 or not output_png_path().exists():
            manifest = build_manifest(
                blender_executable=blender_executable,
                blender_version=blender_version,
                scene_payload_path=scene_payload_path,
                output_png_path=output_png_path(),
                status="blender_apq_4x5_prototype_blocked_render_failed",
                render_exit_code=render_result.returncode,
                render_stdout=render_result.stdout,
                render_stderr=render_result.stderr,
            )
            write_json_file(manifest_path(), manifest)
            return 1

        png_width, png_height = verify_png_dimensions(output_png_path())
        if png_width != 1080 or png_height != 1350:
            manifest = build_manifest(
                blender_executable=blender_executable,
                blender_version=blender_version,
                scene_payload_path=scene_payload_path,
                output_png_path=output_png_path(),
                status="blender_apq_4x5_prototype_blocked_unexpected_png_size",
                render_exit_code=1,
                render_stdout=render_result.stdout,
                render_stderr=render_result.stderr,
            )
            write_json_file(manifest_path(), manifest)
            return 1

        manifest = build_manifest(
            blender_executable=blender_executable,
            blender_version=blender_version,
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_apq_4x5_prototype_rendered",
            render_exit_code=render_result.returncode,
            render_stdout=render_result.stdout,
            render_stderr=render_result.stderr,
        )
        write_json_file(manifest_path(), manifest)
        return 0
    finally:
        if runner_file is not None and runner_file.exists():
            runner_file.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
