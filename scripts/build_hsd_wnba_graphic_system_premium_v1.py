from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
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
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, UnidentifiedImageError
except Exception:  # pragma: no cover - handled at runtime
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageEnhance = None  # type: ignore[assignment]
    ImageFilter = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]
    UnidentifiedImageError = Exception  # type: ignore[assignment]


VERSION = "hsd-wnba-graphic-system-premium-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_graphic_system_premium_v1.py"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "local" / "tmp" / "wnba_graphic_system_premium_v1"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")

OUT_DIR_REL = Path("wnba_graphic_system_premium_v1")
OUT_MANIFEST_REL = OUT_DIR_REL / "manifest.json"
OUT_REPORT_REL = OUT_DIR_REL / "visual_report.md"
OUT_INTAKE_REL = OUT_DIR_REL / "manual_visual_review_intake.csv"
OUT_RUBRIC_REL = OUT_DIR_REL / "blunt_visual_rubric.md"
OUT_CONTACT_SHEET_REL = OUT_DIR_REL / "contact_sheet.png"

CANVAS = (1080, 1350)
CONTACT_SHEET = (1080, 1560)
REVIEW_BURN_IN = "REVIEW ONLY - WNBA GRAPHIC SYSTEM PROOF V1"

FALSE_GUARDRAILS = {
    "review_only": True,
    "artifact_only": True,
    "asset_downloads": False,
    "download_performed": False,
    "approval_state_change": False,
    "approved_marker_writes": False,
    "asset_approved": False,
    "auto_approval": False,
    "auto_publish": False,
    "move_files": False,
    "paid_apis": False,
    "publish_ready": False,
    "publishing": False,
    "protected_asset_moves": False,
    "source_auto_enabled": False,
    "renderer_behavior_change": False,
}

CSV_FIELDS = [
    "proof_id",
    "proof_name",
    "source_asset_id",
    "source_image_path",
    "render_mode",
    "layout_mode",
    "crop_center_x",
    "crop_center_y",
    "crop_zoom",
    "output_png_path",
    "visual_strength",
    "known_limit",
    "boxed_stage_rejected",
    "operator_decision",
    "operator_notes",
    "review_only",
    "artifact_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

SOURCE_APQ001 = Path("data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg")
SOURCE_APCS038 = Path("data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs038_operator_review.jpg")
SOURCE_APCS039 = Path("data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg")

PROOF_SPECS: list[dict[str, Any]] = [
    {
        "proof_id": "wnba_score_command_blender",
        "proof_name": "Score Command",
        "source_asset_id": "APCS039",
        "source_image_path": SOURCE_APCS039.as_posix(),
        "render_mode": "blender",
        "layout_mode": "score_command",
        "crop_center": [0.52, 0.48],
        "crop_zoom": 1.03,
        "accent": [229, 52, 69],
        "headline": "FINAL",
        "subhead": "JACKIE YOUNG",
        "body": "APCS039 REVIEW-ONLY ACTION READ",
        "footer": "premium score plane, no stage box",
        "visual_strength": "strongest_premium_score_anchor",
        "known_limit": "review_only_official_gallery_candidate_not_asset_approved",
    },
    {
        "proof_id": "wnba_clean_editorial_blender",
        "proof_name": "Clean Editorial",
        "source_asset_id": "APCS039",
        "source_image_path": SOURCE_APCS039.as_posix(),
        "render_mode": "blender",
        "layout_mode": "clean_editorial",
        "crop_center": [0.53, 0.50],
        "crop_zoom": 1.08,
        "accent": [234, 202, 136],
        "headline": "JACKIE YOUNG",
        "subhead": "CLEAN EDITORIAL",
        "body": "APCS039 / SOURCE-LED HIERARCHY",
        "footer": "less box, more athlete",
        "visual_strength": "best_premium_cover_route",
        "known_limit": "needs_manual_crop_confirmation_before_any_asset_review",
    },
    {
        "proof_id": "wnba_wire_story_depth",
        "proof_name": "Wire Story Depth",
        "source_asset_id": "APCS039",
        "source_image_path": SOURCE_APCS039.as_posix(),
        "render_mode": "pillow",
        "layout_mode": "wire_story_depth",
        "crop_center": [0.56, 0.50],
        "crop_zoom": 1.06,
        "accent": [120, 196, 255],
        "headline": "NEWS",
        "subhead": "ACTION FRAME",
        "body": "APCS039 STORY DEPTH",
        "footer": "news rail, more depth, less clutter",
        "visual_strength": "best_story_card_route",
        "known_limit": "review_only_source_still_needs_manual_context_check",
    },
    {
        "proof_id": "wnba_clean_editorial_apq001",
        "proof_name": "APQ001 Clean Editorial",
        "source_asset_id": "APQ001",
        "source_image_path": SOURCE_APQ001.as_posix(),
        "render_mode": "pillow",
        "layout_mode": "apq001_clean_editorial",
        "crop_center": [0.53, 0.52],
        "crop_zoom": 1.05,
        "accent": [222, 196, 114],
        "headline": "APQ001",
        "subhead": "CLEAN EDITORIAL",
        "body": "REVIEW-ONLY SOURCE READ",
        "footer": "safer geometry, no toy mockup",
        "visual_strength": "best_face_safe_editorial_baseline",
        "known_limit": "landscape_source_requires_crop_reduction_for_4x5",
    },
    {
        "proof_id": "wnba_wide_action_read",
        "proof_name": "Wide Action Read",
        "source_asset_id": "APCS038",
        "source_image_path": SOURCE_APCS038.as_posix(),
        "render_mode": "pillow",
        "layout_mode": "wide_action_read",
        "crop_center": [0.58, 0.52],
        "crop_zoom": 1.08,
        "accent": [84, 186, 232],
        "headline": "WIDE",
        "subhead": "ACTION READ",
        "body": "APCS038 / SYSTEM CHECK",
        "footer": "best context board, still review-only",
        "visual_strength": "best_contextual_action_route",
        "known_limit": "wide_source_competes_with_text_until_scrim_is_exact",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return ROOT


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_blender_executable(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.exists() else None
    return DEFAULT_BLENDER_EXECUTABLE if DEFAULT_BLENDER_EXECUTABLE.exists() else None


def load_font(size: int, *, bold: bool = True):
    if ImageFont is None:
        raise RuntimeError("Pillow is unavailable")
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/seguisb.ttf") if bold else Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/bahnschrift.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def text_box(draw: Any, text: str, font: Any) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def fit_font(draw: Any, text: str, max_width: int, *, start_size: int, bold: bool = True) -> Any:
    size = start_size
    while size >= 12:
        font = load_font(size, bold=bold)
        if text_box(draw, text, font)[0] <= max_width:
            return font
        size -= 1
    return load_font(12, bold=bold)


def draw_safe_text(draw: Any, text: str, box: tuple[int, int, int, int], *, start_size: int, bold: bool, fill: tuple[int, int, int, int], align: str = "left") -> Any:
    x1, y1, x2, y2 = box
    font = fit_font(draw, text, x2 - x1, start_size=start_size, bold=bold)
    width, height = text_box(draw, text, font)
    x = x1
    if align == "center":
        x = x1 + max(0, (x2 - x1 - width) // 2)
    elif align == "right":
        x = x2 - width
    draw.text((x, y1 + max(0, (y2 - y1 - height) // 2)), text, font=font, fill=fill)
    return font


def crop_to_ratio(source: Any, target_size: tuple[int, int], center: tuple[float, float], zoom: float) -> Any:
    if ImageOps is None:
        raise RuntimeError("Pillow is unavailable")
    width, height = source.size
    target_ratio = target_size[0] / target_size[1]
    source_ratio = width / height
    zoom = max(1.0, float(zoom))
    if source_ratio > target_ratio:
        base_height = height
        base_width = int(round(height * target_ratio))
    else:
        base_width = width
        base_height = int(round(width / target_ratio))
    crop_width = max(1, int(round(base_width / zoom)))
    crop_height = max(1, int(round(base_height / zoom)))
    center_x = int(round(width * float(center[0])))
    center_y = int(round(height * float(center[1])))
    left = max(0, min(width - crop_width, center_x - crop_width // 2))
    top = max(0, min(height - crop_height, center_y - crop_height // 2))
    crop = source.crop((left, top, left + crop_width, top + crop_height))
    return ImageOps.fit(crop, target_size, method=Image.Resampling.LANCZOS)


def apply_grade(image: Any, *, brightness: float, contrast: float, color: float, sharpness: float, blur: float = 0.0) -> Any:
    if ImageEnhance is None or ImageFilter is None:
        raise RuntimeError("Pillow is unavailable")
    graded = ImageEnhance.Brightness(image).enhance(brightness)
    graded = ImageEnhance.Contrast(graded).enhance(contrast)
    graded = ImageEnhance.Color(graded).enhance(color)
    graded = ImageEnhance.Sharpness(graded).enhance(sharpness)
    if blur > 0:
        graded = graded.filter(ImageFilter.GaussianBlur(radius=blur))
    return graded


def gradient_overlay(size: tuple[int, int], left_alpha: int, right_alpha: int) -> Any:
    if Image is None:
        raise RuntimeError("Pillow is unavailable")
    width, height = size
    gradient = Image.new("L", (width, 1))
    gradient.putdata([
        int(round(left_alpha + (right_alpha - left_alpha) * (x / max(1, width - 1))))
        for x in range(width)
    ])
    gradient = gradient.resize((width, height))
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay.putalpha(gradient)
    return overlay


def vignette_overlay(size: tuple[int, int], strength: float = 0.3) -> Any:
    if Image is None:
        raise RuntimeError("Pillow is unavailable")
    width, height = size
    mask = Image.new("L", size, 0)
    cx = width * 0.52
    cy = height * 0.48
    max_distance = math.sqrt(max(cx, width - cx) ** 2 + max(cy, height - cy) ** 2)
    pixels = []
    for y in range(height):
        for x in range(width):
            distance = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max_distance
            value = max(0.0, min(1.0, (distance - 0.35) / 0.65))
            pixels.append(int(round(255 * strength * value)))
    mask.putdata(pixels)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    overlay.putalpha(mask)
    return overlay


def open_source(path: Path) -> tuple[Any | None, dict[str, Any]]:
    if Image is None:
        return None, {"present": False, "readable": False, "reason": "pillow_unavailable"}
    if not path.exists():
        return None, {"present": False, "readable": False, "reason": "missing"}
    try:
        with Image.open(path) as image:
            loaded = image.convert("RGB")
            return loaded, {"present": True, "readable": True, "size": list(loaded.size)}
    except (UnidentifiedImageError, OSError):
        return None, {"present": True, "readable": False, "reason": "unreadable"}


def prepare_texture(source: Any, spec: dict[str, Any], texture_path: Path) -> Any:
    photo = crop_to_ratio(source, CANVAS, (float(spec["crop_center"][0]), float(spec["crop_center"][1])), float(spec["crop_zoom"]))
    photo = apply_grade(photo, brightness=1.02, contrast=1.18, color=0.96, sharpness=1.08)
    texture_path.parent.mkdir(parents=True, exist_ok=True)
    photo.save(texture_path, "PNG")
    return photo


def render_pillow_layout(spec: dict[str, Any], source_image: Path, out_path: Path) -> dict[str, Any]:
    source, source_meta = open_source(source_image)
    if source is None:
        return {"status": "missing_source", "source_meta": source_meta}
    if Image is None or ImageDraw is None:
        return {"status": "pillow_unavailable", "source_meta": source_meta}

    photo = prepare_texture(source, spec, out_path.parent / "pillow_textures" / f"{spec['proof_id']}.png").convert("RGBA")
    backdrop = apply_grade(photo.copy().convert("RGB"), brightness=0.48, contrast=1.08, color=0.72, sharpness=0.92, blur=12.0).convert("RGBA")
    canvas = backdrop
    draw = ImageDraw.Draw(canvas)
    accent = tuple(int(v) for v in spec["accent"]) + (255,)
    ivory = (246, 242, 232, 255)
    cool = (215, 222, 232, 255)
    layout = spec["layout_mode"]

    canvas.alpha_composite(photo)
    canvas.alpha_composite(gradient_overlay(CANVAS, 12, 170))
    canvas.alpha_composite(vignette_overlay(CANVAS, 0.24))

    if layout == "wire_story_depth":
        draw.rectangle((0, 0, 460, 1350), fill=(8, 11, 16, 160))
        draw_safe_text(draw, "NEWS", (84, 146, 220, 198), start_size=28, bold=True, fill=accent)
        draw_safe_text(draw, spec["headline"], (84, 228, 404, 308), start_size=68, bold=True, fill=ivory)
        draw_safe_text(draw, spec["subhead"], (84, 322, 408, 372), start_size=34, bold=True, fill=accent)
        draw_safe_text(draw, spec["body"], (84, 394, 420, 470), start_size=24, bold=False, fill=cool)
        draw.text((84, 524), spec["source_asset_id"], font=load_font(60, bold=True), fill=(255, 255, 255, 228))
        draw_safe_text(draw, spec["footer"], (84, 1106, 420, 1150), start_size=18, bold=False, fill=(180, 188, 199, 255))
        draw.line((84, 494, 366, 494), fill=accent, width=3)
    elif layout == "apq001_clean_editorial":
        draw.rectangle((678, 0, 1080, 1350), fill=(9, 13, 18, 164))
        draw.rectangle((0, 1060, 1080, 1350), fill=(10, 14, 20, 150))
        draw_safe_text(draw, spec["headline"], (708, 132, 986, 238), start_size=90, bold=True, fill=ivory)
        draw_safe_text(draw, spec["subhead"], (708, 258, 986, 312), start_size=34, bold=True, fill=accent)
        draw_safe_text(draw, spec["body"], (708, 332, 986, 414), start_size=24, bold=False, fill=cool)
        draw.text((708, 448), "FACE-SAFE EDITORIAL BASELINE", font=load_font(20, bold=False), fill=(189, 196, 206, 255))
        draw.text((708, 506), spec["source_asset_id"], font=load_font(64, bold=True), fill=(255, 255, 255, 230))
        draw_safe_text(draw, spec["footer"], (708, 1118, 986, 1166), start_size=18, bold=False, fill=(176, 184, 194, 255))
        draw.line((708, 318, 946, 318), fill=accent, width=3)
    elif layout == "wide_action_read":
        draw.rectangle((0, 1036, 1080, 1350), fill=(11, 15, 20, 160))
        draw.rectangle((0, 0, 352, 1350), fill=(8, 11, 16, 120))
        draw.text((84, 92), spec["source_asset_id"], font=load_font(42, bold=True), fill=(255, 255, 255, 236))
        draw_safe_text(draw, spec["headline"], (84, 1072, 320, 1162), start_size=76, bold=True, fill=ivory)
        draw_safe_text(draw, spec["subhead"], (332, 1078, 660, 1134), start_size=36, bold=True, fill=accent)
        draw_safe_text(draw, spec["body"], (84, 1160, 720, 1216), start_size=24, bold=False, fill=cool)
        draw_safe_text(draw, spec["footer"], (84, 1222, 820, 1268), start_size=18, bold=False, fill=(190, 197, 207, 255))
        draw.line((84, 1010, 396, 1010), fill=accent, width=3)
    else:
        draw.rectangle((0, 1040, 1080, 1350), fill=(11, 15, 20, 160))
        draw.text((84, 92), spec["source_asset_id"], font=load_font(42, bold=True), fill=(255, 255, 255, 236))
        draw_safe_text(draw, spec["headline"], (84, 1072, 320, 1162), start_size=72, bold=True, fill=ivory)
        draw_safe_text(draw, spec["subhead"], (332, 1078, 660, 1134), start_size=36, bold=True, fill=accent)
        draw_safe_text(draw, spec["body"], (84, 1160, 720, 1216), start_size=24, bold=False, fill=cool)
        draw_safe_text(draw, spec["footer"], (84, 1222, 820, 1268), start_size=18, bold=False, fill=(190, 197, 207, 255))
        draw.line((84, 1010, 396, 1010), fill=accent, width=3)

    draw.text((40, 1302), REVIEW_BURN_IN, font=load_font(18, bold=True), fill=(255, 255, 255, 86))
    draw.text((742, 1302), "review only / no approvals / no publish", font=load_font(16, bold=False), fill=(218, 221, 227, 94))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "PNG")
    return {"status": "ready", "source_meta": source_meta, "texture_path": (out_path.parent / "pillow_textures" / f"{spec['proof_id']}.png").as_posix()}


def build_blender_runner_script() -> str:
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


        def choose_engine() -> str:
            scene = bpy.context.scene
            for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
                try:
                    scene.render.engine = candidate
                    return candidate
                except Exception:
                    continue
            return scene.render.engine


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
            nodes.clear()
            output = nodes.new("ShaderNodeOutputMaterial")
            coords = nodes.new("ShaderNodeTexCoord")
            tex = nodes.new("ShaderNodeTexImage")
            emission = nodes.new("ShaderNodeEmission")
            tex.image = bpy.data.images.load(str(Path(image_path)), check_existing=True)
            links.new(coords.outputs["UV"], tex.inputs["Vector"])
            links.new(tex.outputs["Color"], emission.inputs["Color"])
            emission.inputs["Strength"].default_value = 1.0
            links.new(emission.outputs["Emission"], output.inputs["Surface"])
            return mat


        def add_image_plane(image_path: str) -> None:
            # Use an explicit X/Z screen-space mesh. Blender primitive plane scaling is easy
            # to misread after rotation; this keeps the source image truly full-frame.
            width = 5.84
            height = 7.30
            verts = [
                (-width / 2.0, 0.0, -height / 2.0),
                (width / 2.0, 0.0, -height / 2.0),
                (width / 2.0, 0.0, height / 2.0),
                (-width / 2.0, 0.0, height / 2.0),
            ]
            mesh = bpy.data.meshes.new("PhotoPlaneMesh")
            mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
            mesh.update()
            uv_layer = mesh.uv_layers.new(name="UVMap")
            uv_values = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
            for loop_index, uv in zip(mesh.polygons[0].loop_indices, uv_values):
                uv_layer.data[loop_index].uv = uv
            obj = bpy.data.objects.new("PhotoPlane", mesh)
            bpy.context.collection.objects.link(obj)
            obj.data.materials.append(image_material("PhotoMat", image_path))


        def add_box(name: str, loc: tuple[float, float, float], scale: tuple[float, float, float], color: tuple[float, float, float, float], bevel: float = 0.02) -> None:
            bpy.ops.mesh.primitive_cube_add(location=loc, scale=scale)
            obj = bpy.context.object
            obj.name = name
            mod = obj.modifiers.new(name="Bevel", type="BEVEL")
            mod.width = min(scale[0], scale[2]) * bevel
            mod.segments = 3
            obj.data.materials.append(material(f"{name}Mat", color, roughness=0.62))


        def add_text(name: str, text: str, loc: tuple[float, float, float], size: float, color: tuple[float, float, float, float], bold: bool = True, align: str = "LEFT") -> None:
            bpy.ops.object.text_add(location=loc, rotation=(0.0, 0.0, 0.0))
            obj = bpy.context.object
            obj.name = name
            obj.data.body = text
            obj.data.size = size
            obj.data.align_x = align
            obj.data.extrude = 0.0
            fp = font_path(bold)
            if fp:
                try:
                    obj.data.font = bpy.data.fonts.load(fp, check_existing=True)
                except Exception:
                    pass
            obj.data.materials.append(material(f"{name}Mat", color, roughness=0.22, emission=0.08))


        def add_light(name: str, loc: tuple[float, float, float], energy: float, color: tuple[float, float, float], size: float, size_y: float) -> None:
            bpy.ops.object.light_add(type="AREA", location=loc, rotation=(math.radians(78.0), 0.0, 0.0))
            light = bpy.context.object
            light.name = name
            light.data.energy = energy
            light.data.color = color
            light.data.shape = "RECTANGLE"
            light.data.size = size
            light.data.size_y = size_y


        def configure_render() -> None:
            scene = bpy.context.scene
            scene.render.engine = choose_engine()
            scene.render.resolution_x = 1080
            scene.render.resolution_y = 1350
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = "PNG"
            scene.render.film_transparent = False
            if scene.render.engine == "CYCLES":
                scene.cycles.samples = 64
                scene.cycles.use_denoising = True
            if hasattr(scene, "eevee"):
                scene.eevee.taa_render_samples = 32
            scene.world = bpy.data.worlds.new("World")
            scene.world.use_nodes = True
            bg = scene.world.node_tree.nodes["Background"]
            bg.inputs[0].default_value = (0.01, 0.012, 0.018, 1.0)
            bg.inputs[1].default_value = 0.18


        def setup_camera() -> None:
            bpy.ops.object.camera_add(location=(0.0, 0.0, 7.5), rotation=(0.0, 0.0, 0.0))
            camera = bpy.context.object
            camera.data.type = "ORTHO"
            camera.data.ortho_scale = 7.25
            bpy.context.scene.camera = camera


        def add_scene_blocks(spec: dict[str, object]) -> None:
            accent = tuple(float(v) / 255.0 for v in spec["accent"]) + (1.0,)
            mode = str(spec["layout_mode"])
            if mode == "score_command":
                add_box("RightBand", (2.55, 0.0, 0.03), (0.62, 2.8, 0.06), (0.05, 0.07, 0.10, 1.0))
                add_box("ScoreBand", (1.95, -2.50, 0.02), (1.55, 0.14, 0.03), accent)
                add_text("Headline", str(spec["headline"]), (2.06, 2.10, 0.12), 0.62, (0.96, 0.97, 0.99, 1.0), True, "LEFT")
                add_text("Subhead", str(spec["subhead"]), (2.06, 1.58, 0.12), 0.20, accent, True, "LEFT")
                add_text("Body", str(spec["body"]), (2.06, 1.04, 0.12), 0.15, (0.86, 0.90, 0.96, 1.0), False, "LEFT")
                add_text("Source", str(spec["source_asset_id"]), (2.06, 0.45, 0.12), 0.32, (0.98, 0.98, 0.98, 1.0), True, "LEFT")
            else:
                add_box("RightPanel", (2.42, 0.0, 0.02), (0.44, 2.75, 0.06), (0.06, 0.08, 0.11, 1.0))
                add_box("BottomBand", (0.0, -2.48, 0.02), (2.00, 0.16, 0.03), (0.05, 0.06, 0.08, 1.0))
                add_text("Headline", str(spec["headline"]), (2.02, 2.02, 0.12), 0.50, (0.96, 0.97, 0.99, 1.0), True, "LEFT")
                add_text("Subhead", str(spec["subhead"]), (2.02, 1.50, 0.12), 0.18, accent, True, "LEFT")
                add_text("Body", str(spec["body"]), (2.02, 1.00, 0.12), 0.13, (0.86, 0.90, 0.96, 1.0), False, "LEFT")
                add_text("Footer", str(spec["footer"]), (2.02, 0.42, 0.12), 0.12, (0.78, 0.82, 0.88, 1.0), False, "LEFT")


        def render_spec(spec: dict[str, object]) -> None:
            clear_scene()
            configure_render()
            setup_camera()
            add_image_plane(str(spec["texture_path"]))
            add_scene_blocks(spec)
            add_light("Key", (-2.8, -3.0, 4.4), 1800, (1.0, 0.96, 0.90), 5.8, 4.2)
            add_light("Rim", (2.6, -2.4, 2.2), 900, (0.70, 0.82, 1.0), 2.2, 3.2)
            add_light("Fill", (0.0, -1.8, 1.0), 450, (0.88, 0.92, 1.0), 4.0, 2.4)
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
    output = (result.stdout or result.stderr).splitlines()
    return output[0].strip() if output else ""


def composite_blender_overlay_on_photo(texture_path: Path, render_path: Path) -> None:
    if Image is None:
        raise RuntimeError("Pillow is unavailable")
    if not texture_path.exists() or not render_path.exists():
        return
    with Image.open(texture_path) as texture_image, Image.open(render_path) as overlay_image:
        base = texture_image.convert("RGBA")
        overlay = overlay_image.convert("RGBA")
        if overlay.size != base.size:
            overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)
        grayscale = overlay.convert("L")
        alpha = grayscale.point(lambda value: 0 if value < 28 else min(224, int(value * 1.45)))
        overlay.putalpha(alpha)
        base.alpha_composite(overlay)
        base.convert("RGB").save(render_path, "PNG")


def render_blender_layout(spec: dict[str, Any], source_image: Path, out_path: Path, blender_executable: Path) -> dict[str, Any]:
    source, source_meta = open_source(source_image)
    if source is None:
        return {"status": "missing_source", "source_meta": source_meta}
    if Image is None:
        return {"status": "pillow_unavailable", "source_meta": source_meta}

    texture_path = out_path.parent / "blender_textures" / f"{spec['proof_id']}_texture.png"
    photo = prepare_texture(source, spec, texture_path)
    specs_json = out_path.parent / "blender_specs" / f"{spec['proof_id']}.json"
    runner_path = out_path.parent / "blender_runner.py"
    specs_json.parent.mkdir(parents=True, exist_ok=True)
    runner_path.write_text(build_blender_runner_script(), encoding="utf-8")
    payload = {
        "proof_specs": [
            {
                **spec,
                "texture_path": texture_path.as_posix(),
                "output_png_path": out_path.as_posix(),
            }
        ]
    }
    specs_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = subprocess.run(
        [
            blender_executable.as_posix(),
            "--background",
            "--python",
            runner_path.as_posix(),
            "--",
            "--specs-json",
            specs_json.as_posix(),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    status = "ready" if result.returncode == 0 and out_path.exists() else "render_failed"
    if status == "ready":
        composite_blender_overlay_on_photo(texture_path, out_path)
    return {
        "status": status,
        "source_meta": source_meta,
        "texture_path": texture_path.as_posix(),
        "returncode": result.returncode,
        "stdout_tail": (result.stdout or "")[-1200:],
        "stderr_tail": (result.stderr or "")[-1200:],
        "texture_dimensions": list(photo.size),
    }


def create_contact_sheet(output_dir: Path, proof_rows: list[dict[str, Any]]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is unavailable")
    thumb_w, thumb_h = 320, 410
    canvas = Image.new("RGB", CONTACT_SHEET, (11, 14, 20))
    draw = ImageDraw.Draw(canvas)
    draw.text((34, 28), "WNBA GRAPHIC SYSTEM PROOF PACKET", font=load_font(28, bold=True), fill=(248, 249, 251))
    draw.text(
        (34, 62),
        "Existing local WNBA review-only assets only. Blender is used only where it improves the final look.",
        font=load_font(17, bold=False),
        fill=(186, 193, 204),
    )
    cols = 3
    gap_x = 24
    gap_y = 24
    left = 34
    top = 110
    label_h = 70
    for index, row in enumerate(proof_rows):
        col = index % cols
        row_i = index // cols
        x = left + col * (thumb_w + gap_x)
        y = top + row_i * (thumb_h + label_h + gap_y)
        tile = Image.new("RGB", (thumb_w, thumb_h), (15, 19, 26))
        try:
            with Image.open(row["output_png_path"]) as image:
                thumb = ImageOps.fit(image.convert("RGB"), (thumb_w, thumb_h), method=Image.Resampling.LANCZOS)
                tile.paste(thumb, (0, 0))
        except Exception:
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.rectangle((0, 0, thumb_w - 1, thumb_h - 1), outline=(90, 96, 106), width=2)
            tile_draw.text((24, 164), "missing preview", font=load_font(20, bold=True), fill=(220, 96, 100))
        canvas.paste(tile, (x, y))
        draw.rectangle((x, y, x + thumb_w, y + thumb_h), outline=(220, 228, 236), width=1)
        draw.text((x, y + thumb_h + 10), row["proof_name"], font=load_font(18, bold=True), fill=(242, 244, 247))
        draw.text(
            (x, y + thumb_h + 36),
            f"{row['source_asset_id']} / {row['render_mode']} / {row['layout_mode']}",
            font=load_font(13, bold=False),
            fill=(178, 185, 195),
        )
    out_path = output_dir / OUT_CONTACT_SHEET_REL.name
    canvas.save(out_path, "PNG")
    return out_path


def blunt_rubric_text() -> str:
    return """# WNBA Graphic System Rubric

This is review-only. It exists to judge whether the visual system got better, not to approve, publish, or normalize any asset.

## Keep

- Flat editorial hierarchy with one clear subject anchor.
- Strong crop confidence and visible basketball energy.
- Clean negative space for score, headline, or story read.
- Subtle burn-in only, never loud compliance wallpaper.

## Reject

- The failed #527 boxed-stage look.
- Gray floor toy mockups.
- Floating perspective panels that feel like a showroom.
- Dense stacked cards that bury the athlete.
- Compliance copy that overwhelms the image.

## Pass / Fail

- Pass if the image feels like sports editorial first and system demo second.
- Fail if the layout looks staged, padded, or miniature.
- Fail if the subject, ball, or face loses authority to the design.
- Fail if the typography becomes the main event.
"""


def build_intake_rows(proof_specs: list[dict[str, Any]], output_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in proof_specs:
        rows.append(
            {
                "proof_id": spec["proof_id"],
                "proof_name": spec["proof_name"],
                "source_asset_id": spec["source_asset_id"],
                "source_image_path": spec["source_image_path"],
                "render_mode": spec["render_mode"],
                "layout_mode": spec["layout_mode"],
                "crop_center_x": f"{float(spec['crop_center'][0]):.3f}",
                "crop_center_y": f"{float(spec['crop_center'][1]):.3f}",
                "crop_zoom": f"{float(spec['crop_zoom']):.2f}",
                "output_png_path": (output_dir / f"{spec['proof_id']}.png").as_posix(),
                "visual_strength": spec["visual_strength"],
                "known_limit": spec["known_limit"],
                "boxed_stage_rejected": "true",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return rows


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            f"| `{row['proof_id']}` | {row['proof_name']} | {row['source_asset_id']} | {row['render_mode']} | {row['layout_mode']} | {row['known_limit']} |"
            for row in manifest["proof_rows"]
        ]
    )
    blender_note = (
        "Blender did not materially improve the final look here. The Blender-backed proofs are useful comparison studies, but they still drift toward the boxed-stage family the brief rejects."
        if manifest.get("blender_available")
        else "Blender was not available, so the packet stayed in the flat composite lane."
    )
    return f"""# WNBA Graphic System Premium V1

Status: `{manifest['status']}`
Version: `{manifest['version']}`

This packet is a review-only WNBA graphics system proof built from existing local assets only. It is source-led, full-bleed or near-full-bleed, and explicitly rejects the failed boxed-stage render family.

## Read

- Strongest Blender comparison score route: `wnba_score_command_blender`
- Strongest Blender comparison editorial route: `wnba_clean_editorial_blender`
- Best overall visual result: `wnba_wide_action_read`
- Strongest non-Blender source check: `wnba_wire_story_depth`
- Strongest face-safe baseline: `wnba_clean_editorial_apq001`
- Strongest wide-action survival test: `wnba_wide_action_read`

## Blender Judgment

{blender_note}

## Outputs

- Contact sheet: `{manifest['contact_sheet_path']}`
- Report: `{manifest['report_path']}`
- Manifest: `{manifest['manifest_path']}`
- Rubric: `{manifest['rubric_path']}`
- Intake CSV: `{manifest['manual_visual_review_intake_path']}`

| Proof | Name | Source | Render | Layout | Limit |
| --- | --- | --- | --- | --- | --- |
{rows}

## Guardrails

- review_only=true
- artifact_only=true
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- source_auto_enabled=false
- paid_apis=false

## Visual Verdict

The system is useful if the athlete stays dominant and the typography feels like a supporting layer. It fails if it starts looking like a miniature showroom, a gray-floor stage, or a conference mockup.

Bluntly: the non-Blender composite is the better-looking path in this packet. The Blender routes are retained for comparison and transparency, not because they beat the source-led flat composite.
"""


def maybe_mirror_to_latest(output_dir: Path) -> Path | None:
    mirror_dir = repo_root() / "outputs" / "local" / "latest" / "files" / output_dir.name
    mirror_dir.parent.mkdir(parents=True, exist_ok=True)
    if mirror_dir.exists():
        shutil.rmtree(mirror_dir)
    shutil.copytree(output_dir, mirror_dir)
    return mirror_dir


def build_packet(*, output_dir: Path, blender_executable: Path | None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    proof_rows: list[dict[str, Any]] = []
    validation_issues: list[str] = []
    blender_used = False
    blender_version = probe_blender_version(blender_executable)

    for spec in PROOF_SPECS:
        source_path = Path(spec["source_image_path"])
        output_png = output_dir / f"{spec['proof_id']}.png"
        if spec["render_mode"] == "blender" and blender_executable:
            render_info = render_blender_layout(spec, source_path, output_png, blender_executable)
            blender_used = blender_used or render_info.get("status") == "ready"
        else:
            render_info = render_pillow_layout(spec, source_path, output_png)
        if render_info.get("status") != "ready":
            validation_issues.append(f"{spec['proof_id']}: {render_info.get('status')}")
        proof_rows.append(
            {
                "proof_id": spec["proof_id"],
                "proof_name": spec["proof_name"],
                "output_png_path": output_png.as_posix(),
                "dimensions": list(CANVAS) if output_png.exists() else [],
                "source_asset_id": spec["source_asset_id"],
                "source_image_path": spec["source_image_path"],
                "render_mode": spec["render_mode"],
                "layout_mode": spec["layout_mode"],
                "visual_strength": spec["visual_strength"],
                "known_limit": spec["known_limit"],
                "review_only": True,
            }
        )

    contact_sheet_path = create_contact_sheet(output_dir, proof_rows) if not validation_issues else output_dir / OUT_CONTACT_SHEET_REL.name
    intake_rows = build_intake_rows(PROOF_SPECS, output_dir)
    write_csv(output_dir / OUT_INTAKE_REL.name, intake_rows, CSV_FIELDS)
    write_text(output_dir / OUT_RUBRIC_REL.name, blunt_rubric_text())

    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_graphic_system_premium_ready" if not validation_issues else "wnba_graphic_system_premium_blocked",
        "output_dir": output_dir.as_posix(),
        "contact_sheet_path": contact_sheet_path.as_posix() if contact_sheet_path else "",
        "report_path": (output_dir / OUT_REPORT_REL.name).as_posix(),
        "manifest_path": (output_dir / OUT_MANIFEST_REL.name).as_posix(),
        "rubric_path": (output_dir / OUT_RUBRIC_REL.name).as_posix(),
        "manual_visual_review_intake_path": (output_dir / OUT_INTAKE_REL.name).as_posix(),
        "proof_count": len(proof_rows),
        "proof_rows": proof_rows,
        "source_count": len({spec["source_asset_id"] for spec in PROOF_SPECS}),
        "source_paths": sorted({spec["source_image_path"] for spec in PROOF_SPECS}),
        "blender_available": bool(blender_executable),
        "blender_used": blender_used,
        "blender_version": blender_version,
        "blender_backed_proof_count": sum(1 for spec in PROOF_SPECS if spec["render_mode"] == "blender"),
        "review_only": True,
        "artifact_only": True,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
        "source_auto_enabled": False,
        "paid_apis": False,
        "validation_issue_count": len(validation_issues),
        "validation_issues": validation_issues,
        "boxed_stage_rejected": True,
        **FALSE_GUARDRAILS,
    }

    write_json(output_dir / OUT_MANIFEST_REL.name, manifest, sort_keys=True)
    write_text(output_dir / OUT_REPORT_REL.name, build_report(manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only WNBA graphic system proof packet.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--blender-executable", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None).resolve()
    blender_executable = resolve_blender_executable(args.blender_executable or None)
    manifest = build_packet(output_dir=output_dir, blender_executable=blender_executable)
    maybe_mirror_to_latest(output_dir)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "proof_count": manifest["proof_count"],
                "validation_issue_count": manifest["validation_issue_count"],
                "blender_used": manifest["blender_used"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if manifest["validation_issue_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
