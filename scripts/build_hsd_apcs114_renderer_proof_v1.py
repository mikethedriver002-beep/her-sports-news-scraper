from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-apcs114-renderer-proof-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apcs114_renderer_proof_v1.py"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
DEFAULT_SOURCE_IMAGE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/nwsl/sophia_wilson/apcs114_operator_review.jpg"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/apcs114_renderer_proof_v1")
RUNNER_NAME = "apcs114_renderer_proof_runner.py"
SPECS_NAME = "apcs114_proof_specs.json"
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_proof_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
CANVAS = {"width": 1080, "height": 1350}
BURN_IN = "REVIEW ONLY - APCS114 QUARANTINE PROOF"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "headshot_writes": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
}

CSV_FIELDS = [
    "proof_id",
    "proof_name",
    "render_path",
    "crop_strategy",
    "composition_treatment_mode",
    "visual_strength",
    "known_limit",
    "operator_decision",
    "operator_notes",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


class RenderResult:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_source_image(explicit: str | None = None) -> Path:
    raw = Path(explicit) if explicit else DEFAULT_SOURCE_IMAGE
    return raw if raw.is_absolute() else repo_root() / raw


def resolve_blender_executable(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.exists() else None
    return DEFAULT_BLENDER_EXECUTABLE if DEFAULT_BLENDER_EXECUTABLE.exists() else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_blender_version(blender_executable: Path | None) -> str:
    if not blender_executable:
        return ""
    result = subprocess.run(
        [blender_executable.as_posix(), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return (result.stdout or result.stderr).splitlines()[0].strip() if (result.stdout or result.stderr) else ""


def build_proof_specs() -> list[dict[str, Any]]:
    return [
        {
            "proof_id": "proof_01_score_final_editorial",
            "proof_name": "Score Final Editorial",
            "filename": "proof_01_score_final_editorial.png",
            "texture_filename": "proof_01_score_final_editorial_texture.png",
            "crop_strategy": "center_right_4x5_face_body_balance",
            "crop_center": [0.64, 0.66],
            "crop_zoom": 1.72,
            "composition_treatment_mode": "photo_plus_dark_score_plane_blender_depth",
            "visual_strength": "strongest_score_social_candidate",
            "known_limit": "group_celebration_not_solo_hero",
            "accent_color": [236, 192, 87],
            "background_top": [7, 9, 15],
            "background_bottom": [16, 24, 37],
            "headline": "FINAL",
            "subhead": "THORNS HOLD THE MOMENT",
            "score": "2 - 1",
            "caption": "APCS114 / SOPHIA WILSON",
            "photo_location": [-1.46, 0.50, 0.22],
            "photo_scale": [1.88, 1.0, 2.78],
            "photo_rotation_z": -2.0,
            "text_anchor_x": 1.05,
        },
        {
            "proof_id": "proof_02_celebration_news_depth",
            "proof_name": "Celebration News Depth",
            "filename": "proof_02_celebration_news_depth.png",
            "texture_filename": "proof_02_celebration_news_depth_texture.png",
            "crop_strategy": "right_4x5_celebration_stack",
            "crop_center": [0.72, 0.66],
            "crop_zoom": 1.70,
            "composition_treatment_mode": "layered_news_card_photo_plane",
            "visual_strength": "best_news_celebration_route",
            "known_limit": "foreground_group_read_requires_manual_check",
            "accent_color": [255, 94, 74],
            "background_top": [9, 12, 20],
            "background_bottom": [27, 24, 34],
            "headline": "LATE GOAL",
            "subhead": "CELEBRATION FRAME",
            "score": "MATCHWEEK 5",
            "caption": "REVIEW-ONLY SOURCE TEST",
            "photo_location": [0.94, 0.58, 0.10],
            "photo_scale": [1.82, 1.0, 2.98],
            "photo_rotation_z": 1.4,
            "text_anchor_x": -2.45,
        },
        {
            "proof_id": "proof_03_clean_magazine_stat_shell",
            "proof_name": "Clean Magazine Stat Shell",
            "filename": "proof_03_clean_magazine_stat_shell.png",
            "texture_filename": "proof_03_clean_magazine_stat_shell_texture.png",
            "crop_strategy": "right_4x5_negative_space_stat_shell",
            "crop_center": [0.70, 0.64],
            "crop_zoom": 1.55,
            "composition_treatment_mode": "minimal_magazine_stat_shell",
            "visual_strength": "cleanest_editorial_baseline",
            "known_limit": "source_is_group_photo_not_isolated_player",
            "accent_color": [216, 202, 156],
            "background_top": [14, 16, 24],
            "background_bottom": [20, 24, 31],
            "headline": "32'",
            "subhead": "GAME-STATE FEATURE",
            "score": "RIGHT CROP STUDY",
            "caption": "TEXT-SAFE PLANE TEST",
            "photo_location": [1.36, 0.52, 0.02],
            "photo_scale": [1.54, 1.0, 2.56],
            "photo_rotation_z": -1.0,
            "text_anchor_x": -2.42,
        },
    ]


def crop_texture(source_image: Path, output_path: Path, center: list[float], zoom: float) -> dict[str, Any]:
    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow is required to prepare APCS114 review-only render textures")
    with Image.open(source_image) as source:
        rgb = source.convert("RGB")
        width, height = rgb.size
        target_ratio = CANVAS["width"] / CANVAS["height"]
        if width / height > target_ratio:
            base_height = height
            base_width = int(round(height * target_ratio))
        else:
            base_width = width
            base_height = int(round(width / target_ratio))
        zoom = max(1.0, float(zoom))
        crop_width = max(1, int(round(base_width / zoom)))
        crop_height = max(1, int(round(base_height / zoom)))
        center_x = int(round(width * float(center[0])))
        center_y = int(round(height * float(center[1])))
        left = max(0, min(width - crop_width, center_x - crop_width // 2))
        top = max(0, min(height - crop_height, center_y - crop_height // 2))
        crop = rgb.crop((left, top, left + crop_width, top + crop_height))
        fitted = crop.resize((CANVAS["width"], CANVAS["height"]), getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fitted.save(output_path, "PNG")
        return {
            "source_size": list(rgb.size),
            "texture_size": [CANVAS["width"], CANVAS["height"]],
            "crop_box": [left, top, left + crop_width, top + crop_height],
            "crop_zoom": zoom,
        }


def prepare_specs(output_dir: Path, source_image: Path) -> list[dict[str, Any]]:
    texture_dir = output_dir / "review_only_render_textures"
    specs: list[dict[str, Any]] = []
    for base in build_proof_specs():
        row = dict(base)
        output_png = output_dir / row["filename"]
        texture_path = texture_dir / row["texture_filename"]
        texture_info = crop_texture(source_image, texture_path, list(row["crop_center"]), float(row["crop_zoom"]))
        row.update(
            {
                "output_png_path": output_png.as_posix(),
                "texture_path": texture_path.as_posix(),
                "source_image_path": source_image.as_posix(),
                "source_image_present": source_image.exists(),
                "source_image_sha256": sha256_file(source_image) if source_image.exists() else "",
                "texture_info": texture_info,
                "canvas": dict(CANVAS),
                "review_only": True,
                "burn_in_text": BURN_IN,
            }
        )
        specs.append(row)
    return specs


def write_specs_file(output_dir: Path, specs: list[dict[str, Any]]) -> Path:
    return write_json(output_dir / SPECS_NAME, {"version": VERSION, "proof_specs": specs}, sort_keys=True)


def build_runner_script() -> str:
    return textwrap.dedent(
        r'''
        from __future__ import annotations

        import argparse
        import json
        import math
        import sys
        from pathlib import Path

        import bpy


        def parse_args() -> argparse.Namespace:
            parser = argparse.ArgumentParser()
            parser.add_argument("--specs-json", required=True)
            argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
            return parser.parse_args(argv)


        def clear_scene() -> None:
            bpy.ops.wm.read_factory_settings(use_empty=True)


        def choose_render_engine() -> str:
            scene = bpy.context.scene
            for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
                try:
                    scene.render.engine = candidate
                    return candidate
                except Exception:
                    continue
            return scene.render.engine


        def configure_render() -> None:
            scene = bpy.context.scene
            scene.render.engine = choose_render_engine()
            scene.render.resolution_x = 1080
            scene.render.resolution_y = 1350
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = "PNG"
            scene.render.film_transparent = False
            if scene.render.engine == "CYCLES":
                scene.cycles.samples = 96
                scene.cycles.use_denoising = True
            if hasattr(scene, "eevee"):
                scene.eevee.taa_render_samples = 64
            scene.world = bpy.data.worlds.new("World")
            scene.world.use_nodes = True
            bg = scene.world.node_tree.nodes["Background"]
            bg.inputs[0].default_value = (0.01, 0.012, 0.018, 1.0)
            bg.inputs[1].default_value = 0.20


        def face_camera_rotation() -> tuple[float, float, float]:
            return (math.radians(90.0), 0.0, 0.0)


        def setup_camera() -> None:
            bpy.ops.object.camera_add(location=(0.0, -8.6, 0.0), rotation=face_camera_rotation())
            camera = bpy.context.object
            camera.data.type = "ORTHO"
            camera.data.ortho_scale = 7.55
            bpy.context.scene.camera = camera


        def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.45, emission: float = 0.0) -> bpy.types.Material:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            principled = nodes.get("Principled BSDF")
            if principled is None:
                principled = nodes.new("ShaderNodeBsdfPrincipled")
            principled.inputs["Base Color"].default_value = color
            principled.inputs["Roughness"].default_value = roughness
            if "Emission Color" in principled.inputs:
                principled.inputs["Emission Color"].default_value = color
            if "Emission Strength" in principled.inputs:
                principled.inputs["Emission Strength"].default_value = emission
            return mat


        def image_material(name: str, image_path: str) -> bpy.types.Material:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            principled = nodes.get("Principled BSDF")
            if principled is None:
                principled = nodes.new("ShaderNodeBsdfPrincipled")
            coords = nodes.new("ShaderNodeTexCoord")
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = bpy.data.images.load(str(Path(image_path)), check_existing=True)
            links.new(coords.outputs["UV"], tex.inputs["Vector"])
            links.new(tex.outputs["Color"], principled.inputs["Base Color"])
            principled.inputs["Roughness"].default_value = 0.34
            return mat


        def apply(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
            obj.data.materials.append(mat)


        def add_panel(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], color: tuple[float, float, float, float], rot_z: float = 0.0, bevel: float = 0.018) -> bpy.types.Object:
            bpy.ops.mesh.primitive_cube_add(location=loc, scale=scale, rotation=(0.0, 0.0, math.radians(rot_z)))
            obj = bpy.context.object
            obj.name = name
            mod = obj.modifiers.new(name="SoftBevel", type="BEVEL")
            mod.width = min(scale[0], scale[2]) * bevel
            mod.segments = 3
            apply(obj, material(f"{name}Mat", color))
            return obj


        def add_plane(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], mat: bpy.types.Material, rot_z: float = 0.0) -> bpy.types.Object:
            # Mesh planes use X/Y for their visible surface before rotation; this helper accepts X/Z-style
            # visual dimensions so the call sites match the vertical stage coordinate system.
            bpy.ops.mesh.primitive_plane_add(location=loc, rotation=(math.radians(90.0), 0.0, math.radians(rot_z)), scale=(scale[0], scale[2], scale[1]))
            obj = bpy.context.object
            obj.name = name
            apply(obj, mat)
            return obj


        def add_image_plane(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], mat: bpy.types.Material, rot_z: float = 0.0) -> bpy.types.Object:
            sx = float(scale[0])
            sz = float(scale[2])
            radians = math.radians(rot_z)
            cos_v = math.cos(radians)
            sin_v = math.sin(radians)
            corners = [(-sx, -sz), (sx, -sz), (sx, sz), (-sx, sz)]
            verts = []
            for dx, dz in corners:
                verts.append((loc[0] + dx * cos_v - dz * sin_v, loc[1], loc[2] + dx * sin_v + dz * cos_v))
            mesh = bpy.data.meshes.new(f"{name}Mesh")
            mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
            mesh.update()
            uv = mesh.uv_layers.new(name="APCS114UV")
            for loop, coord in zip(uv.data, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
                loop.uv = coord
            obj = bpy.data.objects.new(name, mesh)
            bpy.context.collection.objects.link(obj)
            apply(obj, mat)
            return obj


        def font_path(bold: bool) -> str:
            candidates = [
                Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
                Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
                Path("C:/Windows/Fonts/bahnschrift.ttf"),
            ]
            for candidate in candidates:
                if candidate.exists():
                    return str(candidate)
            return ""


        def add_text(name: str, text: str, loc: tuple[float, float, float], size: float, color: tuple[float, float, float, float], bold: bool = True, align: str = "LEFT", emission: float = 0.0) -> bpy.types.Object:
            bpy.ops.object.text_add(location=loc, rotation=face_camera_rotation())
            obj = bpy.context.object
            obj.name = name
            obj.data.body = text
            obj.data.size = size
            obj.data.align_x = align
            obj.data.align_y = "CENTER"
            obj.data.extrude = 0.0
            fp = font_path(bold)
            if fp:
                try:
                    obj.data.font = bpy.data.fonts.load(fp, check_existing=True)
                except Exception:
                    pass
            apply(obj, material(f"{name}Mat", color, roughness=0.25, emission=emission))
            return obj


        def add_light(name: str, loc: tuple[float, float, float], energy: float, color: tuple[float, float, float], size: float, size_y: float) -> None:
            bpy.ops.object.light_add(type="AREA", location=loc, rotation=(math.radians(78.0), 0.0, 0.0))
            light = bpy.context.object
            light.name = name
            light.data.energy = energy
            light.data.color = color
            light.data.shape = "RECTANGLE"
            light.data.size = size
            light.data.size_y = size_y


        def add_background(spec: dict[str, object]) -> None:
            top = tuple(float(v) / 255.0 for v in spec["background_top"]) + (1.0,)
            bottom = tuple(float(v) / 255.0 for v in spec["background_bottom"]) + (1.0,)
            accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
            add_plane("Backdrop", (0.0, 2.8, 0.0), (4.4, 1.0, 3.8), material("BackdropMat", bottom, 0.75))
            add_plane("TopWash", (0.0, 2.7, 1.9), (4.4, 1.0, 1.8), material("TopWashMat", top, 0.8))
            add_plane("AccentGlow", (-2.0, 2.45, 1.2), (1.7, 1.0, 1.7), material("AccentGlowMat", accent, 0.55, 0.75))
            add_panel("FloorPlane", (0.0, 1.6, -3.15), (3.5, 0.025, 0.22), (0.09, 0.11, 0.16, 1.0), 0.0)
            add_panel("LeftDepthBlade", (-2.95, 1.1, -0.2), (0.10, 0.035, 3.05), (0.07, 0.09, 0.14, 1.0), -5.0)
            add_panel("RightDepthBlade", (2.95, 1.2, 0.2), (0.12, 0.035, 3.35), (0.09, 0.08, 0.12, 1.0), 4.0)
            add_light("KeySoftbox", (0.0, -3.5, 4.4), 2600, (1.0, 0.96, 0.90), 5.8, 4.4)
            add_light("CoolRim", (3.4, -2.4, 1.8), 1100, (0.70, 0.78, 1.0), 2.2, 3.4)


        def add_burn_in() -> None:
            add_panel("BurnInBand", (0.0, 0.28, -3.38), (2.20, 0.04, 0.14), (0.04, 0.055, 0.08, 1.0), 0.0)
            add_text("BurnIn", "REVIEW ONLY - APCS114 QUARANTINE PROOF", (0.0, 0.12, -3.38), 0.135, (0.92, 0.94, 0.98, 1.0), True, "CENTER", 0.05)


        def add_photo(spec: dict[str, object]) -> None:
            loc = tuple(float(v) for v in spec["photo_location"])
            scale = tuple(float(v) for v in spec["photo_scale"])
            rot = float(spec["photo_rotation_z"])
            add_panel("PhotoShadow", (loc[0] + 0.12, loc[1] + 0.32, loc[2] - 0.14), (scale[0] + 0.10, 0.035, scale[2] + 0.14), (0.01, 0.012, 0.018, 1.0), rot, 0.012)
            add_image_plane("PhotoTexture", loc, scale, image_material("APCS114TextureMat", str(spec["texture_path"])), rot)
            # Thin offset bars imply a physical print edge without covering the texture.
            add_panel("PhotoEdgeLeft", (loc[0] - scale[0] - 0.025, loc[1] + 0.02, loc[2]), (0.025, 0.012, scale[2] + 0.04), (0.88, 0.86, 0.78, 1.0), rot, 0.006)
            add_panel("PhotoEdgeRight", (loc[0] + scale[0] + 0.025, loc[1] + 0.02, loc[2]), (0.025, 0.012, scale[2] + 0.04), (0.88, 0.86, 0.78, 1.0), rot, 0.006)
            add_panel("PhotoEdgeTop", (loc[0], loc[1] + 0.02, loc[2] + scale[2] + 0.025), (scale[0] + 0.04, 0.012, 0.025), (0.88, 0.86, 0.78, 1.0), rot, 0.006)
            add_panel("PhotoEdgeBottom", (loc[0], loc[1] + 0.02, loc[2] - scale[2] - 0.025), (scale[0] + 0.04, 0.012, 0.025), (0.88, 0.86, 0.78, 1.0), rot, 0.006)


        def render_score_final(spec: dict[str, object]) -> None:
            accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
            x = float(spec["text_anchor_x"])
            add_panel("DarkTextPlane", (1.52, 0.62, 0.10), (1.10, 0.05, 2.55), (0.035, 0.045, 0.065, 1.0), 0.8)
            add_text("Headline", str(spec["headline"]), (x, 0.06, 2.34), 0.54, (0.96, 0.97, 0.99, 1.0), True, "LEFT")
            add_text("Subhead", str(spec["subhead"]), (x, 0.06, 1.88), 0.18, accent, True, "LEFT")
            add_text("Score", str(spec["score"]), (x, 0.05, 1.06), 0.78, (0.97, 0.96, 0.92, 1.0), True, "LEFT", 0.04)
            add_text("Caption", str(spec["caption"]), (x, 0.05, 0.28), 0.16, (0.76, 0.80, 0.88, 1.0), False, "LEFT")
            add_panel("LowerRule", (1.65, 0.56, -0.68), (0.92, 0.025, 0.025), accent, 0.0)


        def render_news_depth(spec: dict[str, object]) -> None:
            accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
            x = float(spec["text_anchor_x"])
            add_panel("BadgePlane", (-2.02, 0.58, 2.36), (0.70, 0.04, 0.22), accent, 0.0)
            add_text("Badge", "NEWS", (-2.02, 0.10, 2.36), 0.23, (1.0, 1.0, 1.0, 1.0), True, "CENTER")
            add_text("Headline", str(spec["headline"]), (x, 0.08, 1.50), 0.44, (0.96, 0.97, 0.99, 1.0), True, "LEFT")
            add_text("Subhead", str(spec["subhead"]), (x, 0.08, 1.08), 0.22, accent, True, "LEFT")
            add_text("Score", str(spec["score"]), (x, 0.08, 0.40), 0.32, (0.82, 0.86, 0.93, 1.0), True, "LEFT")
            add_text("Caption", str(spec["caption"]), (x, 0.08, -0.12), 0.14, (0.74, 0.78, 0.86, 1.0), False, "LEFT")


        def render_magazine(spec: dict[str, object]) -> None:
            accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
            x = float(spec["text_anchor_x"])
            add_text("Headline", str(spec["headline"]), (x, 0.08, 1.66), 1.18, (0.96, 0.96, 0.93, 1.0), True, "LEFT")
            add_text("Subhead", str(spec["subhead"]), (x, 0.08, 0.72), 0.24, accent, True, "LEFT")
            add_text("Score", str(spec["score"]), (x, 0.08, 0.22), 0.18, (0.80, 0.84, 0.90, 1.0), False, "LEFT")
            add_panel("MagazineRule", (-1.60, 0.54, -0.44), (0.84, 0.025, 0.025), accent, 0.0)
            add_text("Caption", str(spec["caption"]), (x, 0.08, -0.78), 0.15, (0.72, 0.76, 0.84, 1.0), False, "LEFT")


        def render_spec(spec: dict[str, object]) -> None:
            clear_scene()
            configure_render()
            setup_camera()
            add_background(spec)
            add_photo(spec)
            mode = str(spec["composition_treatment_mode"])
            if mode == "photo_plus_dark_score_plane_blender_depth":
                render_score_final(spec)
            elif mode == "layered_news_card_photo_plane":
                render_news_depth(spec)
            else:
                render_magazine(spec)
            add_burn_in()
            bpy.context.scene.render.filepath = str(spec["output_png_path"])
            bpy.ops.render.render(write_still=True)


        def main() -> int:
            args = parse_args()
            payload = json.loads(Path(args.specs_json).read_text(encoding="utf-8"))
            for spec in payload["proof_specs"]:
                render_spec(spec)
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    ).strip() + "\n"


def run_blender_render(blender_executable: Path, runner_file: Path, specs_file: Path) -> RenderResult:
    result = subprocess.run(
        [
            blender_executable.as_posix(),
            "--background",
            "--python",
            runner_file.as_posix(),
            "--",
            "--specs-json",
            specs_file.as_posix(),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return RenderResult(result.returncode, result.stdout, result.stderr)


def load_font(size: int, *, bold: bool = True) -> Any:
    if ImageFont is None:
        raise RuntimeError("Pillow ImageFont is unavailable")
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\seguisb.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\bahnschrift.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_contact_sheet(output_dir: Path, specs: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required to build the APCS114 contact sheet")
    thumbs: list[Any] = []
    for spec in specs:
        with Image.open(spec["output_png_path"]) as image:
            thumbs.append(image.convert("RGB").resize((320, 400), getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)))
    sheet = Image.new("RGB", (1080, 562), (12, 15, 21))
    draw = ImageDraw.Draw(sheet)
    font = load_font(22, bold=True)
    small = load_font(16, bold=False)
    draw.text((34, 24), "APCS114 REVIEW-ONLY RENDERER PROOFS", fill=(244, 246, 250), font=font)
    draw.text((34, 55), "No asset approval. No publish-ready state. Group celebration source.", fill=(190, 198, 210), font=small)
    x_positions = [36, 380, 724]
    for x, spec, thumb in zip(x_positions, specs, thumbs):
        sheet.paste(thumb, (x, 104))
        draw.text((x, 516), spec["proof_name"], fill=(238, 239, 242), font=small)
    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path, "PNG")
    return path


def png_dimensions(path: Path) -> list[int]:
    if Image is None:
        return []
    with Image.open(path) as image:
        return [int(image.size[0]), int(image.size[1])]


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            f"| `{row['proof_id']}` | {row['proof_name']} | {row['crop_strategy']} | {row['composition_treatment_mode']} | {row['known_limit']} |"
            for row in manifest["proof_rows"]
        ]
    )
    return f"""# APCS114 Renderer Proof V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet turns the APCS114 Sophia Wilson review-only quarantine candidate into three Blender-backed 1080x1350 proof renders. It is not asset approval, renderer approval, publish-ready output, or publishing.

## Visual Read

- Strongest proof: `proof_01_score_final_editorial` because it creates the clearest score/social composition with the group image protected on a textured photo plane.
- Useful alternate: `proof_02_celebration_news_depth` because it treats the group celebration as news context rather than pretending it is a solo hero.
- Clean baseline: `proof_03_clean_magazine_stat_shell` because it gives the best negative-space discipline, but it is less emotional.
- Known limit: APCS114 is still a group celebration frame. It is a better source-quality proof than the APQ crop loop, but not a clean solo player hero.

## Outputs

- Contact sheet: `{manifest['contact_sheet_path']}`
- Report: `{manifest['report_path']}`
- Manifest: `{manifest['manifest_path']}`

| Proof | Name | Crop | Treatment | Limit |
| --- | --- | --- | --- | --- |
{rows}

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- source_auto_enabled=false
- paid_apis=false
"""


def build_manual_rows(specs: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in specs:
        rows.append(
            {
                "proof_id": spec["proof_id"],
                "proof_name": spec["proof_name"],
                "render_path": spec["output_png_path"],
                "crop_strategy": spec["crop_strategy"],
                "composition_treatment_mode": spec["composition_treatment_mode"],
                "visual_strength": spec["visual_strength"],
                "known_limit": spec["known_limit"],
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return rows


def build_packet(*, source_image: Path, output_dir: Path, blender_executable: Path | None, head_commit: str = "") -> dict[str, Any]:
    source_image = source_image.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = prepare_specs(output_dir, source_image)
    specs_file = write_specs_file(output_dir, specs)
    runner_file = write_text(output_dir / RUNNER_NAME, build_runner_script())
    blender_version = probe_blender_version(blender_executable)
    render_result = RenderResult(99, "", "blender_executable_missing")
    if blender_executable:
        render_result = run_blender_render(blender_executable, runner_file, specs_file)

    missing_outputs = [spec["output_png_path"] for spec in specs if not Path(spec["output_png_path"]).exists()]
    traceback_present = "Traceback" in f"{render_result.stdout}\n{render_result.stderr}"
    if render_result.returncode != 0 or missing_outputs or traceback_present:
        status = "apcs114_renderer_proof_blocked_render_failed"
        contact_sheet_path = ""
    else:
        status = "apcs114_renderer_proof_ready"
        contact_sheet_path = create_contact_sheet(output_dir, specs).as_posix()

    proof_rows: list[dict[str, Any]] = []
    for spec in specs:
        output_png = Path(spec["output_png_path"])
        proof_rows.append(
            {
                "proof_id": spec["proof_id"],
                "proof_name": spec["proof_name"],
                "output_png_path": output_png.as_posix(),
                "dimensions": png_dimensions(output_png) if output_png.exists() else [],
                "texture_path": spec["texture_path"],
                "crop_strategy": spec["crop_strategy"],
                "composition_treatment_mode": spec["composition_treatment_mode"],
                "visual_strength": spec["visual_strength"],
                "known_limit": spec["known_limit"],
                "review_only": True,
            }
        )

    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": status,
        "repo_head": head_commit,
        "output_dir": output_dir.as_posix(),
        "source_image_path": source_image.as_posix(),
        "source_image_present": source_image.exists(),
        "source_image_sha256": sha256_file(source_image) if source_image.exists() else "",
        "blender_used": bool(blender_executable),
        "blender_version": blender_version,
        "render_exit_code": render_result.returncode,
        "traceback_present": traceback_present,
        "render_stdout_tail": render_result.stdout[-1600:],
        "render_stderr_tail": render_result.stderr[-1600:],
        "contact_sheet_path": contact_sheet_path,
        "manifest_path": manifest_path.as_posix(),
        "report_path": report_path.as_posix(),
        "proof_count": len(proof_rows),
        "proof_rows": proof_rows,
        "known_source_limit": "APCS114 is a group celebration image, not a solo hero.",
        "strongest_proof_id": "proof_01_score_final_editorial",
        "review_only": True,
        "approved_marker_writes": False,
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    write_csv(output_dir / CSV_NAME, build_manual_rows(specs), CSV_FIELDS)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build APCS114 review-only Blender renderer proof packet.")
    parser.add_argument("--source-image", default=DEFAULT_SOURCE_IMAGE.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--blender-executable", default="")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_image = resolve_source_image(args.source_image)
    output_dir = resolve_output_dir(args.output_dir or None)
    blender_executable = resolve_blender_executable(args.blender_executable or None)
    manifest = build_packet(
        source_image=source_image,
        output_dir=output_dir,
        blender_executable=blender_executable,
        head_commit=args.head_commit,
    )
    print(json.dumps({"version": VERSION, "status": manifest["status"], "proof_count": manifest["proof_count"]}, indent=2))
    return 0 if manifest["status"] == "apcs114_renderer_proof_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
