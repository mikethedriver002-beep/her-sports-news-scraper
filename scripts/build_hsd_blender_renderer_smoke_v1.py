from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - runtime fallback
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


VERSION = "hsd-blender-renderer-smoke-v1-review-only"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
SMOKE_BURN_IN_TEXT = "REVIEW ONLY - BLENDER SMOKE TEST"

class CommandResult:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def smoke_output_dir() -> Path:
    return output_path("blender_renderer_smoke")


def scene_payload_path() -> Path:
    return smoke_output_dir() / "scene_payload.json"


def blender_runner_path() -> Path:
    return smoke_output_dir() / "blender_runner.py"


def output_png_path() -> Path:
    return smoke_output_dir() / "blender_renderer_smoke_4x5.png"


def manifest_path() -> Path:
    return smoke_output_dir() / "blender_renderer_smoke_manifest.json"


def report_path() -> Path:
    return smoke_output_dir() / "blender_renderer_smoke_report.md"


def resolve_blender_executable(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.exists() else None
    if DEFAULT_BLENDER_EXECUTABLE.exists():
        return DEFAULT_BLENDER_EXECUTABLE
    fallback = shutil.which("blender")
    return Path(fallback) if fallback else None


def make_scene_payload() -> dict[str, Any]:
    return {
        "version": VERSION,
        "review_only": True,
        "artifact_only": True,
        "burn_in_text": SMOKE_BURN_IN_TEXT,
        "render": {
            "width": 1080,
            "height": 1350,
            "output_filename": output_png_path().name,
            "engine": "CYCLES",
            "samples": 8,
        },
        "palette": {
            "background": [11, 17, 29],
            "panel": [22, 31, 48],
            "accent": [243, 187, 82],
            "text": [247, 249, 252],
            "muted": [127, 140, 160],
        },
        "objects": [
            {"type": "plane", "name": "BackdropBand", "location": [0.0, 0.8, -1.55], "rotation_degrees": [90.0, 0.0, 0.0], "scale": [5.0, 1.0, 1.0]},
            {"type": "plane", "name": "Floor", "location": [0.0, 0.0, -2.65], "rotation_degrees": [0.0, 0.0, 0.0], "scale": [6.2, 6.2, 1.0]},
            {"type": "plane", "name": "BurnInBanner", "location": [0.0, 0.8, 2.15], "rotation_degrees": [90.0, 0.0, 0.0], "scale": [5.9, 0.42, 1.0]},
            {"type": "cube", "name": "LeftBlock", "location": [-1.95, 0.15, -0.15], "scale": [0.86, 0.46, 0.92]},
            {"type": "sphere", "name": "CenterOrb", "location": [0.0, 0.0, 0.2], "scale": [0.72, 0.72, 0.72]},
            {"type": "cylinder", "name": "RightColumn", "location": [1.95, -0.05, 0.25], "scale": [0.42, 0.42, 1.28]},
            {"type": "text", "name": "BurnIn", "body": SMOKE_BURN_IN_TEXT, "location": [0.0, 0.83, 2.15], "rotation_degrees": [90.0, 0.0, 0.0], "scale": [0.34, 0.34, 0.34]},
        ],
        "camera": {
            "location": [0.0, -7.9, 2.8],
            "target": [0.0, 0.0, -0.45],
            "lens": 42.0,
        },
        "lights": [
            {"type": "area", "location": [-2.4, -3.8, 4.6], "energy": 2200.0, "size": 5.5},
            {"type": "area", "location": [2.7, -2.7, 2.1], "energy": 1200.0, "size": 3.0},
            {"type": "sun", "rotation_degrees": [35.0, 0.0, 30.0], "energy": 1.5},
        ],
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
        "output_png_path": output_png_path.as_posix(),
        "review_only": True,
        "artifact_only": True,
        "publish_ready": False,
        "approval_state_change": False,
        "asset_downloads": False,
        "move_files": False,
        "publishing": False,
        "production_renderer_replacement": False,
        "render_exit_code": render_exit_code,
        "render_stdout": render_stdout,
        "render_stderr": render_stderr,
    }


def write_runner_script() -> Path:
    runner = textwrap.dedent(
        r'''
        from __future__ import annotations

        import argparse
        import json
        import math
        import sys
        from pathlib import Path

        import bpy
        import mathutils


        def argv_after_double_dash() -> list[str]:
            if "--" not in sys.argv:
                return []
            return sys.argv[sys.argv.index("--") + 1 :]


        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument("--scene-payload", required=True)
            parser.add_argument("--output-png", required=True)
            return parser.parse_args(argv_after_double_dash())


        def rgba(values: list[int] | tuple[int, ...], alpha: float = 1.0) -> tuple[float, float, float, float]:
            r, g, b = values
            return (r / 255.0, g / 255.0, b / 255.0, alpha)


        def clear_scene() -> None:
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete(use_global=False)
            for collection in list(bpy.data.collections):
                if collection.name == "Collection":
                    continue


        def set_world(payload: dict[str, object]) -> None:
            world = bpy.data.worlds.new("ReviewOnlyWorld")
            world.use_nodes = True
            scene = bpy.context.scene
            scene.world = world
            nodes = world.node_tree.nodes
            background = nodes.get("Background")
            if background is not None:
                palette = payload["palette"]  # type: ignore[index]
                background.inputs[0].default_value = rgba(palette["background"], 1.0)  # type: ignore[index]
                background.inputs[1].default_value = 0.55


        def setup_camera(payload: dict[str, object]) -> None:
            camera_payload = payload["camera"]  # type: ignore[index]
            bpy.ops.object.camera_add(location=tuple(camera_payload["location"]))  # type: ignore[index]
            camera = bpy.context.active_object
            camera.data.lens = float(camera_payload["lens"])  # type: ignore[index]
            target_payload = camera_payload["target"]  # type: ignore[index]
            target = bpy.data.objects.new("SmokeTarget", None)
            target.location = tuple(target_payload)
            bpy.context.collection.objects.link(target)
            constraint = camera.constraints.new(type="TRACK_TO")
            constraint.target = target
            constraint.track_axis = "TRACK_NEGATIVE_Z"
            constraint.up_axis = "UP_Y"
            bpy.context.scene.camera = camera


        def material_for(name: str, palette: dict[str, list[int]], *, emission: float = 0.0) -> bpy.types.Material:
            material = bpy.data.materials.new(name)
            material.use_nodes = True
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            principled = nodes.get("Principled BSDF")
            if principled is not None:
                principled.inputs["Base Color"].default_value = rgba(palette["panel"], 1.0)
                principled.inputs["Roughness"].default_value = 0.35
                principled.inputs["Metallic"].default_value = 0.12
                if emission > 0.0:
                    principled.inputs["Emission Color"].default_value = rgba(palette["accent"], 1.0)
                    principled.inputs["Emission Strength"].default_value = emission
            return material


        def apply_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
            if obj.data and hasattr(obj.data, "materials"):
                obj.data.materials.clear()
                obj.data.materials.append(material)


        def add_primitive(entry: dict[str, object], payload: dict[str, object]) -> None:
            palette = payload["palette"]  # type: ignore[index]
            obj_type = entry["type"]
            location = tuple(entry["location"])  # type: ignore[index]
            rotation = tuple(math.radians(float(v)) for v in entry.get("rotation_degrees", [0.0, 0.0, 0.0]))  # type: ignore[index]
            scale = tuple(entry.get("scale", [1.0, 1.0, 1.0]))  # type: ignore[index]
            if obj_type == "plane":
                bpy.ops.mesh.primitive_plane_add(location=location, rotation=rotation)
            elif obj_type == "cube":
                bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
            elif obj_type == "sphere":
                bpy.ops.mesh.primitive_uv_sphere_add(location=location, rotation=rotation)
            elif obj_type == "cylinder":
                bpy.ops.mesh.primitive_cylinder_add(location=location, rotation=rotation)
            elif obj_type == "text":
                bpy.ops.object.text_add(location=location, rotation=rotation)
            else:
                raise ValueError(f"Unsupported primitive type: {obj_type}")
            obj = bpy.context.active_object
            obj.scale = scale
            if obj_type == "text":
                obj.data.body = str(entry["body"])
                obj.data.size = 0.58
                obj.data.extrude = 0.03
                obj.data.bevel_depth = 0.01
                obj.data.align_x = "CENTER"
                obj.data.align_y = "CENTER"
                obj.data.resolution_u = 4
                obj.data.fill_mode = "FRONT"
                material = material_for("TextMaterial", palette, emission=8.0)
            elif obj_type == "plane":
                material = material_for(f"{entry['name']}Material", palette)
                material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
            elif obj_type == "sphere":
                material = material_for("OrbMaterial", palette, emission=0.8)
            elif obj_type == "cylinder":
                material = material_for("ColumnMaterial", palette)
            else:
                material = material_for(f"{entry['name']}Material", palette)
            apply_material(obj, material)


        def add_lights(payload: dict[str, object]) -> None:
            for light_payload in payload["lights"]:  # type: ignore[index]
                light_type = light_payload["type"]  # type: ignore[index]
                if light_type == "area":
                    bpy.ops.object.light_add(type="AREA", location=tuple(light_payload["location"]))  # type: ignore[index]
                    light = bpy.context.active_object
                    light.data.energy = float(light_payload["energy"])  # type: ignore[index]
                    light.data.shape = "RECTANGLE"
                    light.data.size = float(light_payload["size"])  # type: ignore[index]
                    light.data.size_y = float(light_payload["size"])  # type: ignore[index]
                elif light_type == "sun":
                    bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, 0.0))
                    light = bpy.context.active_object
                    light.rotation_euler = tuple(math.radians(float(v)) for v in light_payload["rotation_degrees"])  # type: ignore[index]
                    light.data.energy = float(light_payload["energy"])  # type: ignore[index]
                else:
                    raise ValueError(f"Unsupported light type: {light_type}")


        def configure_render(payload: dict[str, object], output_png: Path) -> None:
            scene = bpy.context.scene
            render = payload["render"]  # type: ignore[index]
            scene.render.engine = str(render["engine"])  # type: ignore[index]
            scene.render.resolution_x = int(render["width"])  # type: ignore[index]
            scene.render.resolution_y = int(render["height"])  # type: ignore[index]
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(output_png)
            scene.render.image_settings.file_format = "PNG"
            scene.render.image_settings.color_mode = "RGBA"
            scene.render.film_transparent = False
            scene.cycles.samples = int(render["samples"])  # type: ignore[index]
            scene.cycles.use_denoising = False


        def main() -> int:
            args = parse_args()
            payload = json.loads(Path(args.scene_payload).read_text(encoding="utf-8"))
            clear_scene()
            set_world(payload)
            setup_camera(payload)
            for entry in payload["objects"]:  # type: ignore[index]
                add_primitive(entry, payload)
            add_lights(payload)
            configure_render(payload, Path(args.output_png))
            bpy.ops.render.render(write_still=True)
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    ).strip() + "\n"
    return write_text(blender_runner_path(), runner)


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


def run_blender_render(blender_executable: Path, runner_path: Path, scene_payload_path: Path, output_png_path: Path) -> CommandResult:
    result = subprocess.run(
        [
            str(blender_executable),
            "--background",
            "--factory-startup",
            "--python",
            str(runner_path),
            "--",
            "--scene-payload",
            str(scene_payload_path),
            "--output-png",
            str(output_png_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return CommandResult(result.returncode, result.stdout, result.stderr)


def burn_in_font(size: int):
    if ImageFont is None:
        raise RuntimeError("Pillow is unavailable for burn-in text")
    for candidate in [Path("C:/Windows/Fonts/arialbd.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")]:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def apply_visible_burn_in(path: Path) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is unavailable for burn-in text")
    with Image.open(path) as source:
        image = source.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    banner_h = max(72, int(height * 0.06))
    draw.rectangle((0, height - banner_h, width, height), fill=(186, 24, 48, 235))
    draw.rectangle((0, 0, width, 8), fill=(186, 24, 48, 235))
    text_font = burn_in_font(max(30, int(height * 0.032)))
    bbox = draw.textbbox((0, 0), SMOKE_BURN_IN_TEXT, font=text_font, stroke_width=2)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((width - text_w) / 2, height - banner_h + (banner_h - text_h) / 2 - 3),
        SMOKE_BURN_IN_TEXT,
        font=text_font,
        fill=(255, 255, 255, 255),
        stroke_width=2,
        stroke_fill=(27, 32, 43, 255),
    )
    image.save(path, "PNG")


def write_report(status: str, message: str, manifest_path: Path, render_result: CommandResult | None = None) -> Path:
    lines = [
        "# HSD Blender Renderer Smoke Test v1",
        "",
        f"Status: `{status}`",
        "",
        f"- review_only: `true`",
        f"- artifact_only: `true`",
        f"- publish_ready: `false`",
        f"- approval_state_change: `false`",
        f"- asset_downloads: `false`",
        f"- move_files: `false`",
        f"- publishing: `false`",
        f"- production_renderer_replacement: `false`",
        "",
        message,
        "",
        f"Manifest: `{manifest_path.as_posix()}`",
    ]
    if render_result is not None:
        lines.extend(
            [
                "",
                "## Blender Output",
                "",
                f"- exit_code: `{render_result.returncode}`",
            ]
        )
        if render_result.stdout.strip():
            lines.extend(["", "### stdout", "", "```text", render_result.stdout.strip(), "```"])
        if render_result.stderr.strip():
            lines.extend(["", "### stderr", "", "```text", render_result.stderr.strip(), "```"])
    return write_text(report_path(), "\n".join(lines) + "\n")


def write_smoke_artifacts() -> Path:
    smoke_output_dir().mkdir(parents=True, exist_ok=True)
    return write_json(scene_payload_path(), make_scene_payload(), sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one review-only Blender smoke PNG from a generated local scene payload.")
    parser.add_argument("--blender-executable", default="", help="Optional Blender executable override.")
    args = parser.parse_args(argv)

    smoke_output_dir().mkdir(parents=True, exist_ok=True)
    scene_payload_path = write_smoke_artifacts()
    runner_path = write_runner_script()

    blender_executable = resolve_blender_executable(args.blender_executable or None)
    if blender_executable is None:
        manifest = build_manifest(
            blender_executable=None,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_renderer_smoke_blocked_missing_blender",
            render_exit_code=1,
        )
        write_json(manifest_path(), manifest, sort_keys=True)
        write_report("blocked", "Blender executable could not be resolved locally.", manifest_path())
        return 1

    try:
        blender_version = probe_blender_version(blender_executable)
    except Exception as exc:
        manifest = build_manifest(
            blender_executable=blender_executable,
            blender_version="unavailable",
            scene_payload_path=scene_payload_path,
            output_png_path=output_png_path(),
            status="blender_renderer_smoke_blocked_version_probe_failed",
            render_exit_code=1,
        )
        write_json(manifest_path(), manifest, sort_keys=True)
        write_report("blocked", f"Blender version probe failed: {exc}", manifest_path())
        return 1

    out_png = output_png_path()
    render_result = run_blender_render(blender_executable, runner_path, scene_payload_path, out_png)
    if render_result.returncode != 0 or not out_png.exists():
        manifest = build_manifest(
            blender_executable=blender_executable,
            blender_version=blender_version,
            scene_payload_path=scene_payload_path,
            output_png_path=out_png,
            status="blender_renderer_smoke_blocked_render_failed",
            render_exit_code=render_result.returncode,
            render_stdout=render_result.stdout,
            render_stderr=render_result.stderr,
        )
        write_json(manifest_path(), manifest, sort_keys=True)
        write_report("blocked", "Blender render did not complete successfully.", manifest_path(), render_result)
        return 1
    try:
        apply_visible_burn_in(out_png)
    except Exception as exc:
        manifest = build_manifest(
            blender_executable=blender_executable,
            blender_version=blender_version,
            scene_payload_path=scene_payload_path,
            output_png_path=out_png,
            status="blender_renderer_smoke_blocked_burn_in_failed",
            render_exit_code=1,
            render_stdout=render_result.stdout,
            render_stderr=f"{render_result.stderr}\nBurn-in failed: {exc}".strip(),
        )
        write_json(manifest_path(), manifest, sort_keys=True)
        write_report("blocked", f"Blender render completed but burn-in failed: {exc}", manifest_path(), render_result)
        return 1

    manifest = build_manifest(
        blender_executable=blender_executable,
        blender_version=blender_version,
        scene_payload_path=scene_payload_path,
        output_png_path=out_png,
        status="blender_renderer_smoke_rendered",
        render_exit_code=render_result.returncode,
        render_stdout=render_result.stdout,
        render_stderr=render_result.stderr,
    )
    write_json(manifest_path(), manifest, sort_keys=True)
    write_report("rendered", "Rendered exactly one review-only 4:5 PNG from a generated local scene payload.", manifest_path(), render_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
