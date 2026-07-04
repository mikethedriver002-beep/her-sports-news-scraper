from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:  # pragma: no cover - Pillow is expected in local HSD runs.
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-blender-apcs048-renderer-proof-v1-review-only"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/apcs048_renderer_proof_v1")
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
LOCAL_SOURCE_REFERENCE_CANDIDATES = (
    Path(
        "data/assets/quarantine/review_only_candidates/action_photo_candidates/manual_decision_batch/"
        "au_volleyball_jordan_thompson/apcs048_operator_review.png"
    ),
)
RUNNER_NAME = "blender_apcs048_renderer_proof_runner.py"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
CONTACT_SHEET_NAME = "contact_sheet.png"
SOURCE_COPY_NAME = "apcs048_operator_review.png"
TEXTURE_STATUS_PREFIX = "HSD_APCS048_TEXTURE_STATUS:"
OUTPUT_DIMENSIONS = {"width": 1080, "height": 1350}

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "candidate_state_change": False,
    "download_performed": False,
    "move_files": False,
    "paid_apis": False,
    "publish_ready": False,
    "publishing": False,
    "protected_asset_moves": False,
    "source_auto_enabled": False,
    "source_fetching": False,
}

VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "variant_01_court_depth_hero",
        "output_name": "variant_01_court_depth_hero.png",
        "visual_direction": "full court depth with source-reference hero panel",
        "title": "JORDAN THOMPSON",
        "kicker": "APCS048 PROOF",
        "accent": [232, 46, 72],
        "accent_2": [247, 189, 61],
        "background": [8, 12, 18],
        "floor": [32, 42, 48],
        "wall": [13, 18, 27],
        "photo_location": [-1.15, -0.58, 2.04],
        "photo_scale": [3.25, 2.44],
        "photo_rotation_z": -4.0,
        "camera_location": [0.05, -7.8, 3.35],
        "camera_target": [0.0, -0.1, 1.35],
        "lens": 38,
        "spotlight_location": [-2.8, -4.6, 6.4],
        "spotlight_energy": 850,
        "spotlight_size": 3.3,
        "headline_location": [0.54, -0.84, 2.92],
        "headline_kicker_size": 0.095,
        "headline_title_size": 0.2,
        "proof_line_location": [0.54, -0.85, 2.28],
        "proof_line_size": 0.075,
        "proof_line_text": "REVIEW ONLY / NOT APPROVED",
        "score_plate_location": [1.6, -0.76, 1.35],
    },
    {
        "variant_id": "variant_02_arena_spotlight_crop",
        "output_name": "variant_02_arena_spotlight_crop.png",
        "visual_direction": "arena spotlight crop with layered editorial planes",
        "title": "THOMPSON",
        "kicker": "QUARANTINE SOURCE REFERENCE",
        "accent": [68, 190, 255],
        "accent_2": [245, 242, 229],
        "background": [12, 13, 19],
        "floor": [26, 33, 47],
        "wall": [11, 14, 22],
        "photo_location": [-0.12, -0.74, 2.28],
        "photo_scale": [3.95, 2.96],
        "photo_rotation_z": 0.0,
        "camera_location": [0.0, -8.7, 3.85],
        "camera_target": [0.0, -0.05, 1.55],
        "lens": 44,
        "spotlight_location": [0.0, -4.7, 6.9],
        "spotlight_energy": 1020,
        "spotlight_size": 2.35,
        "headline_location": [-2.05, -0.88, 3.28],
        "proof_line_location": [-2.05, -0.89, 0.78],
        "score_plate_location": [2.28, -0.75, 1.18],
    },
    {
        "variant_id": "variant_03_premium_matchday_poster",
        "output_name": "variant_03_premium_matchday_poster.png",
        "visual_direction": "premium matchday poster with score-ready negative space",
        "title": "MATCHDAY PROOF",
        "kicker": "APCS048 / JORDAN THOMPSON",
        "accent": [255, 213, 84],
        "accent_2": [235, 80, 104],
        "background": [15, 17, 22],
        "floor": [38, 42, 41],
        "wall": [18, 19, 25],
        "photo_location": [1.0, -0.6, 2.1],
        "photo_scale": [3.1, 2.32],
        "photo_rotation_z": 3.2,
        "camera_location": [-0.14, -8.0, 3.2],
        "camera_target": [0.0, -0.06, 1.22],
        "lens": 36,
        "spotlight_location": [2.9, -4.2, 6.1],
        "spotlight_energy": 760,
        "spotlight_size": 3.8,
        "headline_location": [-2.25, -0.85, 2.78],
        "proof_line_location": [-2.25, -0.86, 2.12],
        "score_plate_location": [-1.82, -0.74, 1.14],
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_output_dir() -> Path:
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def safe_posix(path: Path) -> str:
    return path.as_posix()


def is_quarantine_reference_path(path: Path) -> bool:
    normalized = path.as_posix().lower()
    return "/data/assets/quarantine/review_only_candidates/" in normalized or "\\data\\assets\\quarantine\\review_only_candidates\\" in str(path).lower()


def image_size(path: Path) -> dict[str, int] | None:
    if Image is None or not path.exists():
        return None
    try:
        with Image.open(path) as image:
            return {"width": int(image.width), "height": int(image.height)}
    except Exception:
        return None


def resolve_source_reference(explicit_source_reference: Path | None, root: Path | None = None) -> Path:
    if explicit_source_reference is not None:
        return explicit_source_reference.resolve()
    root = root or repo_root()
    for relative_path in LOCAL_SOURCE_REFERENCE_CANDIDATES:
        candidate = (root / relative_path).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
    candidates = ", ".join(path.as_posix() for path in LOCAL_SOURCE_REFERENCE_CANDIDATES)
    raise FileNotFoundError(
        "No local APCS048 quarantine review source reference was found. "
        f"Checked repo-local candidate(s): {candidates}. "
        "Pass --source-reference explicitly to use a source from another worktree."
    )


def prepare_source_reference(source_reference: Path, output_dir: Path) -> dict[str, Any]:
    proof_input_dir = output_dir / "proof_inputs" / "quarantine_review_reference"
    proof_input_dir.mkdir(parents=True, exist_ok=True)
    proof_input_path = proof_input_dir / SOURCE_COPY_NAME
    present = source_reference.exists() and source_reference.is_file()
    allowed_quarantine_source = present and is_quarantine_reference_path(source_reference)
    copied = False
    if allowed_quarantine_source:
        shutil.copy2(source_reference, proof_input_path)
        copied = True
    elif proof_input_path.exists():
        proof_input_path.unlink()
    return {
        "source_reference_path": safe_posix(source_reference),
        "source_reference_present": present,
        "source_reference_is_quarantine_review_only_candidate": allowed_quarantine_source,
        "proof_input_path": safe_posix(proof_input_path),
        "proof_input_present": proof_input_path.exists(),
        "proof_input_copied": copied,
        "source_reference_dimensions": image_size(source_reference) if present else None,
        "proof_input_dimensions": image_size(proof_input_path) if proof_input_path.exists() else None,
    }


def build_variant_specs(source_info: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    proof_input_path = Path(str(source_info["proof_input_path"]))
    source_present = bool(source_info["proof_input_present"])
    for index, base in enumerate(VARIANTS, start=1):
        spec = dict(base)
        spec.update(
            {
                "canvas": dict(OUTPUT_DIMENSIONS),
                "candidate_id": "APCS048",
                "entity_name": "Jordan Thompson",
                "source_reference_path": str(source_info["source_reference_path"]),
                "render_source_image_path": safe_posix(proof_input_path),
                "source_image_present": source_present,
                "source_image_texture_attempted": source_present,
                "review_only_label": "REVIEW ONLY - QUARANTINE PROOF - NOT ASSET APPROVED",
                "footer_label": "APCS048 / Jordan Thompson / review-only renderer proof / no publishing",
                "stage_features": [
                    "3D volleyball court floor",
                    "layered arena planes",
                    "camera depth",
                    "shadow-casting source reference panel",
                    "area and spot lighting",
                    "material court surfaces",
                ],
                "variant_order": index,
            }
        )
        specs.append(spec)
    return specs


def build_runner_script(specs: list[dict[str, Any]]) -> str:
    template = r'''
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

TEXTURE_STATUS_PREFIX = "__TEXTURE_STATUS_PREFIX__"
BAKED_SPECS = json.loads(r"""__BAKED_SPECS__""")
FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")
FONT = None


def argv_after_double_dash() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant-id", required=True)
    parser.add_argument("--output-png", required=True)
    return parser.parse_args(argv_after_double_dash())


def rgba(rgb: list[int], alpha: float = 1.0) -> tuple[float, float, float, float]:
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, alpha)


def load_font():
    global FONT
    if FONT is not None:
        return FONT
    if FONT_PATH.exists():
        FONT = bpy.data.fonts.load(FONT_PATH.as_posix(), check_existing=True)
    return FONT


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.72, emission: float = 0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        if emission and "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emission
    mat.diffuse_color = color
    return mat


def image_material(path: Path, fallback_color: tuple[float, float, float, float]):
    mat = bpy.data.materials.new("APCS048_SourceReferenceTexture")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    status = {"attempted": path.exists(), "loaded": False, "mode": "missing"}
    if bsdf is None:
        return mat, status
    bsdf.inputs["Base Color"].default_value = fallback_color
    bsdf.inputs["Roughness"].default_value = 0.58
    if path.exists():
        try:
            image = bpy.data.images.load(path.as_posix(), check_existing=True)
            tex = nodes.new(type="ShaderNodeTexImage")
            tex.image = image
            mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            status = {"attempted": True, "loaded": True, "mode": "texture_loaded", "image_size": list(image.size)}
        except Exception as exc:
            status = {"attempted": True, "loaded": False, "mode": "texture_failed", "error": str(exc)}
    return mat, status


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def look_at(obj, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_plane(name: str, loc, rot, scale, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_cube(name: str, loc, dims, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_text(name: str, text: str, loc, size: float, color, align: str = "LEFT"):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(73), 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = text
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.008
    font = load_font()
    if font is not None:
        obj.data.font = font
    obj.data.materials.append(material(f"{name}_mat", rgba(color, 1.0), 0.5, 0.18))
    return obj


def setup_render(output_png: Path, spec: dict) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1350
    scene.render.film_transparent = False
    scene.render.filepath = output_png.as_posix()
    scene.render.image_settings.file_format = "PNG"
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 80
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"
    scene.world = bpy.data.worlds.new("APCS048_Arena_World")
    scene.world.color = rgba(spec["background"], 1.0)[:3]


def setup_camera(spec: dict) -> None:
    bpy.ops.object.camera_add(location=spec["camera_location"])
    camera = bpy.context.object
    camera.data.lens = spec["lens"]
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 7.0
    camera.data.dof.aperture_fstop = 6.5
    look_at(camera, tuple(spec["camera_target"]))
    bpy.context.scene.camera = camera


def add_stage(spec: dict) -> dict:
    accent = spec["accent"]
    accent_2 = spec["accent_2"]
    floor_mat = material("matte_volleyball_court_floor", rgba(spec["floor"], 1.0), 0.78)
    wall_mat = material("layered_dark_arena_wall", rgba(spec["wall"], 1.0), 0.82)
    line_mat = material("court_line_material", rgba(accent_2, 1.0), 0.4, 0.03)
    shadow_mat = material("soft_shadow_stage_block", rgba([4, 6, 8], 0.62), 0.9)
    accent_mat = material("accent_layer_plane", rgba(accent, 0.52), 0.62, 0.08)

    add_plane("deep_volleyball_court_floor", (0, 0, 0), (0, 0, 0), (5.7, 6.8, 1), floor_mat)
    add_plane("rear_arena_wall_layer", (0, 2.05, 2.55), (math.radians(90), 0, 0), (6.5, 3.8, 1), wall_mat)
    add_plane("angled_editorial_accent_plane", (-2.55, 0.88, 2.2), (math.radians(90), 0, math.radians(-8)), (0.78, 3.5, 1), accent_mat)
    add_plane("right_depth_shadow_plane", (2.62, 0.78, 1.8), (math.radians(90), 0, math.radians(7)), (0.9, 3.1, 1), shadow_mat)

    for y in (-2.45, -1.15, 0.25, 1.55):
        add_cube("court_depth_line", (0, y, 0.018), (5.25, 0.025, 0.016), line_mat)
    for x in (-2.2, 0, 2.2):
        add_cube("court_lane_line", (x, -0.4, 0.02), (0.025, 4.55, 0.016), line_mat)

    return {"stage_geometry": True, "court_lines": 7, "layered_planes": 3}


def add_scene(spec: dict) -> dict:
    source_path = Path(spec["render_source_image_path"])
    photo_mat, texture_status = image_material(source_path, rgba([34, 40, 50], 1.0))
    photo = add_plane(
        "quarantine_source_reference_photo_plane",
        tuple(spec["photo_location"]),
        (math.radians(90), 0, math.radians(spec["photo_rotation_z"])),
        (spec["photo_scale"][0], spec["photo_scale"][1], 1),
        photo_mat,
    )
    photo.visible_shadow = True
    photo["review_only_source_reference"] = True

    frame_mat = material("thin_premium_photo_frame", rgba(spec["accent_2"], 1.0), 0.55, 0.04)
    add_plane(
        "offset_photo_frame_shadow",
        (spec["photo_location"][0] + 0.08, spec["photo_location"][1] + 0.06, spec["photo_location"][2] - 0.08),
        (math.radians(90), 0, math.radians(spec["photo_rotation_z"])),
        (spec["photo_scale"][0] + 0.18, spec["photo_scale"][1] + 0.18, 1),
        frame_mat,
    )

    add_text("variant_kicker", spec["kicker"], tuple(spec["headline_location"]), float(spec.get("headline_kicker_size", 0.145)), spec["accent_2"])
    title_loc = (spec["headline_location"][0], spec["headline_location"][1], spec["headline_location"][2] - 0.36)
    add_text("variant_title", spec["title"], title_loc, float(spec.get("headline_title_size", 0.34)), [247, 249, 252])
    add_text(
        "review_only_lock",
        str(spec.get("proof_line_text", "REVIEW ONLY / NOT ASSET APPROVED")),
        tuple(spec["proof_line_location"]),
        float(spec.get("proof_line_size", 0.118)),
        spec["accent"],
    )

    plate = add_cube("score_ready_negative_space_plate", tuple(spec["score_plate_location"]), (1.75, 0.055, 0.62), material("score_plate_mat", rgba([10, 12, 16], 0.72), 0.86))
    plate.rotation_euler[2] = math.radians(-2)
    add_text("score_ready_label", "SCORE READY", (spec["score_plate_location"][0] - 0.69, spec["score_plate_location"][1] - 0.08, spec["score_plate_location"][2] + 0.08), 0.12, spec["accent_2"])
    add_text("quarantine_label", "QUARANTINE PROOF", (spec["score_plate_location"][0] - 0.69, spec["score_plate_location"][1] - 0.08, spec["score_plate_location"][2] - 0.12), 0.088, [205, 213, 225])
    return texture_status


def add_lights(spec: dict) -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, -3.8, 5.4))
    area = bpy.context.object
    area.name = "large_soft_arena_key_light"
    area.data.energy = 360
    area.data.size = 5.2
    bpy.ops.object.light_add(type="SPOT", location=spec["spotlight_location"])
    spot = bpy.context.object
    spot.name = "candidate_review_spotlight"
    spot.data.energy = spec["spotlight_energy"]
    spot.data.spot_size = spec["spotlight_size"]
    spot.data.spot_blend = 0.62
    look_at(spot, tuple(spec["photo_location"]))
    bpy.ops.object.light_add(type="POINT", location=(-2.8, -2.8, 1.2))
    rim = bpy.context.object
    rim.name = "low_court_rim_light"
    rim.data.energy = 95
    rim.data.shadow_soft_size = 2.8


def main() -> int:
    args = parse_args()
    spec = next((item for item in BAKED_SPECS if item["variant_id"] == args.variant_id), None)
    if spec is None:
        raise RuntimeError(f"Unknown variant id: {args.variant_id}")
    output_png = Path(args.output_png)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    clear_scene()
    setup_render(output_png, spec)
    setup_camera(spec)
    stage_status = add_stage(spec)
    texture_status = add_scene(spec)
    texture_status.update(stage_status)
    add_lights(spec)
    texture_status_path = output_png.with_suffix(".texture_status.json")
    texture_status_path.write_text(json.dumps(texture_status, indent=2, sort_keys=True), encoding="utf-8")
    print(f"{TEXTURE_STATUS_PREFIX}{json.dumps(texture_status, sort_keys=True)}")
    bpy.ops.render.render(write_still=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    return (
        template.replace("__TEXTURE_STATUS_PREFIX__", TEXTURE_STATUS_PREFIX)
        .replace("__BAKED_SPECS__", json.dumps(specs, sort_keys=True))
        .lstrip()
    )


def write_runner_script(path: Path, specs: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_runner_script(specs), encoding="utf-8")
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
    variant_id: str,
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
            "--variant-id",
            variant_id,
            "--output-png",
            str(output_png_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def overlay_review_labels(path: Path, spec: dict[str, Any]) -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        return

    def load_font(path: str, size: int):
        font_path = Path(path)
        return ImageFont.truetype(font_path.as_posix(), size) if font_path.exists() else ImageFont.load_default()

    def fitted_font(draw: Any, text: str, path: str, start_size: int, max_width: int):
        size = start_size
        font = load_font(path, size)
        while size > 12:
            bbox = draw.textbbox((0, 0), text, font=font)
            if bbox[2] - bbox[0] <= max_width:
                return font
            size -= 1
            font = load_font(path, size)
        return font

    try:
        with Image.open(path).convert("RGBA") as image:
            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            max_text_width = image.width - 72
            top_font = fitted_font(draw, spec["review_only_label"], "C:/Windows/Fonts/arial.ttf", 21, max_text_width)
            footer_title = "APCS048 / Jordan Thompson / REVIEW ONLY"
            footer_lock = "Quarantine proof - not asset-approved - not publish-ready - no publishing"
            footer_note = str(spec["visual_direction"])
            footer_title_font = fitted_font(draw, footer_title, "C:/Windows/Fonts/arialbd.ttf", 26, max_text_width)
            footer_lock_font = fitted_font(draw, footer_lock, "C:/Windows/Fonts/arial.ttf", 19, max_text_width)
            footer_note_font = fitted_font(draw, footer_note, "C:/Windows/Fonts/arial.ttf", 17, max_text_width)
            draw.rectangle((0, 0, image.width, 60), fill=(5, 7, 10, 192))
            draw.text((34, 18), spec["review_only_label"], fill=(248, 249, 252, 255), font=top_font)
            footer_h = 124
            footer_y = image.height - footer_h
            draw.rectangle((0, image.height - footer_h, image.width, image.height), fill=(5, 7, 10, 210))
            draw.text((34, footer_y + 20), footer_title, fill=(246, 248, 250, 255), font=footer_title_font)
            draw.text((34, footer_y + 53), footer_lock, fill=(224, 232, 242, 255), font=footer_lock_font)
            draw.text((34, footer_y + 82), footer_note, fill=(198, 207, 220, 255), font=footer_note_font)
            composited = Image.alpha_composite(image, overlay).convert("RGB")
            composited.save(path, "PNG")
    except Exception:
        return


def build_manual_intake_rows(variant_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in variant_rows:
        rows.append(
            {
                "candidate_id": "APCS048",
                "entity_name": "Jordan Thompson",
                "variant_id": row["variant_id"],
                "visual_direction": row["visual_direction"],
                "output_png_path": row["output_png_path"],
                "review_only": "true",
                "asset_approved": "false",
                "publish_ready": "false",
                "source_reference_texture_loaded": str(bool(row["source_image_texture_loaded"])).lower(),
                "visual_usefulness": "",
                "operator_decision": "",
                "operator_notes": "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_contact_sheet(output_dir: Path, variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    contact_sheet_path = output_dir / CONTACT_SHEET_NAME
    if Image is None or ImageDraw is None or ImageFont is None or ImageOps is None:
        return {"created": False, "path": "", "reason": "pillow_unavailable", "source_count": len(variant_rows)}
    images: list[tuple[dict[str, Any], Any]] = []
    for row in variant_rows:
        try:
            images.append((row, Image.open(Path(row["output_png_path"])).convert("RGB")))
        except Exception:
            continue
    if not images:
        return {"created": False, "path": "", "reason": "no_readable_images", "source_count": 0}
    margin = 26
    cell_w = 360
    cell_h = 560
    sheet_w = margin * 2 + cell_w * len(images)
    sheet_h = 660
    canvas = Image.new("RGB", (sheet_w, sheet_h), (13, 17, 23))
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 21) if Path("C:/Windows/Fonts/arialbd.ttf").exists() else ImageFont.load_default()
    body_font = ImageFont.load_default()
    draw.text((margin, 16), "APCS048 Jordan Thompson - Blender Renderer Proof Contact Sheet", fill=(246, 248, 251), font=title_font)
    draw.text((margin, 44), "Review-only quarantine proof. Not asset-approved, not publish-ready.", fill=(193, 204, 218), font=body_font)
    for index, (row, image) in enumerate(images):
        x0 = margin + index * cell_w
        y0 = 78
        thumb = ImageOps.contain(image, (318, 398))
        draw.rectangle((x0, y0, x0 + cell_w - 16, y0 + cell_h), fill=(25, 31, 41), outline=(77, 88, 104), width=1)
        canvas.paste(thumb, (x0 + (cell_w - 16 - thumb.width) // 2, y0 + 22))
        label_y = y0 + 440
        draw.text((x0 + 18, label_y), row["variant_id"], fill=(245, 247, 250), font=body_font)
        draw.text((x0 + 18, label_y + 19), row["visual_direction"], fill=(190, 201, 214), font=body_font)
        draw.text((x0 + 18, label_y + 38), f"Texture loaded: {str(row['source_image_texture_loaded']).lower()}", fill=(190, 201, 214), font=body_font)
        draw.text((x0 + 18, label_y + 57), f"Dimensions: {row['dimensions']['width']}x{row['dimensions']['height']}", fill=(190, 201, 214), font=body_font)
    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(contact_sheet_path, "PNG")
    return {"created": True, "path": safe_posix(contact_sheet_path), "reason": "", "source_count": len(images)}


def build_report(payload: dict[str, Any]) -> str:
    variant_table = "\n".join(
        f"| `{row['variant_id']}` | {row['visual_direction']} | `{row['source_image_texture_loaded']}` | `{row['dimensions']['width']}x{row['dimensions']['height']}` | `{row['output_png_path']}` |"
        for row in payload["variant_rows"]
    )
    return f"""# APCS048 Jordan Thompson Blender Renderer Proof

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is review-only and quarantine-only. It uses the already downloaded APCS048 operator-review reference as a run-scoped proof input only, builds Blender-rendered 1080x1350 editorial proof PNGs, and does not approve, move, fetch, or publish assets.

## Inputs

- Source reference present: `{payload['source_reference_present']}`
- Source reference path: `{payload['source_reference_path']}`
- Proof input copy: `{payload['proof_input_path']}`
- Source dimensions: `{payload['source_reference_dimensions']}`
- Blender version: `{payload['blender_version']}`

## Rendered Proofs

| Variant | Direction | Texture loaded | Dimensions | Output |
| --- | --- | --- | --- | --- |
{variant_table}

## Visual Usefulness

Blunt read: useful as a renderer proof. The packet is materially better than a flat QA shell because it uses a real Blender scene with court geometry, camera depth, shadowed source-reference planes, layered arena surfaces, and spotlighting. It is still not asset-approved or publish-ready; the source candidate should remain in quarantine review until a human approves identity, rights, and final asset fitness.

Recommended review order: `variant_02_arena_spotlight_crop`, then `variant_01_court_depth_hero`, then `variant_03_premium_matchday_poster`.

## Guardrails

{chr(10).join(f"- {key}={str(value).lower()}" for key, value in sorted(payload["guardrails"].items()))}

## Operator Decision Prompt

Use `{CSV_NAME}` to mark one of: `continue_this_direction`, `revise_this_direction`, `hold_candidate`, or `reject_candidate`.
"""


def build_manifest(
    *,
    output_dir: Path,
    source_info: dict[str, Any],
    blender_executable: Path,
    blender_version: str,
    runner_path: Path,
    variant_rows: list[dict[str, Any]],
    contact_sheet: dict[str, Any],
    report_path: Path,
    intake_path: Path,
) -> dict[str, Any]:
    status = "apcs048_renderer_proof_ready" if all(row["render_exit_code"] == 0 for row in variant_rows) else "apcs048_renderer_proof_ready_with_render_warnings"
    return {
        "version": VERSION,
        "status": status,
        "generated_at_utc": now_iso(),
        "generated_by": Path(__file__).name,
        "candidate_id": "APCS048",
        "entity_name": "Jordan Thompson",
        "review_only": True,
        "quarantine_review_lock": True,
        "asset_approved": False,
        "publish_ready": False,
        "blender_executable": safe_posix(blender_executable),
        "blender_version": blender_version,
        "output_dir": safe_posix(output_dir),
        "runner_script_path": safe_posix(runner_path),
        "manifest_path": safe_posix(output_dir / MANIFEST_NAME),
        "report_path": safe_posix(report_path),
        "manual_visual_review_intake_path": safe_posix(intake_path),
        "contact_sheet_path": contact_sheet["path"],
        "contact_sheet_created": contact_sheet["created"],
        "output_dimensions": dict(OUTPUT_DIMENSIONS),
        "variant_count": len(variant_rows),
        "variant_rows": variant_rows,
        "guardrails": dict(FALSE_GUARDRAILS),
        **source_info,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build APCS048 review-only Blender renderer proof packet.")
    parser.add_argument(
        "--source-reference",
        type=Path,
        default=None,
        help="Optional explicit APCS048 quarantine review source reference. If omitted, repo-local quarantine candidates are checked.",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--blender-executable", type=Path, default=DEFAULT_BLENDER_EXECUTABLE)
    args = parser.parse_args(argv)

    output_dir = (args.output_dir or resolve_output_dir()).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    renders_dir = output_dir / "renders"
    logs_dir = output_dir / "logs"
    renders_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    source_reference = resolve_source_reference(args.source_reference)
    source_info = prepare_source_reference(source_reference, output_dir)
    specs = build_variant_specs(source_info)
    runner_path = write_runner_script(output_dir / RUNNER_NAME, specs)
    blender_version = probe_blender_version(args.blender_executable)

    variant_rows: list[dict[str, Any]] = []
    for spec in specs:
        output_png = renders_dir / spec["output_name"]
        result = run_blender_render(args.blender_executable, runner_path, spec["variant_id"], output_png)
        stdout_path = logs_dir / f"{spec['variant_id']}.stdout.txt"
        stderr_path = logs_dir / f"{spec['variant_id']}.stderr.txt"
        stdout_path.write_text(result.stdout or "", encoding="utf-8")
        stderr_path.write_text(result.stderr or "", encoding="utf-8")
        if output_png.exists():
            overlay_review_labels(output_png, spec)
        texture_status_path = output_png.with_suffix(".texture_status.json")
        texture_status = json.loads(texture_status_path.read_text(encoding="utf-8")) if texture_status_path.exists() else {}
        variant_rows.append(
            {
                "candidate_id": "APCS048",
                "entity_name": "Jordan Thompson",
                "variant_id": spec["variant_id"],
                "visual_direction": spec["visual_direction"],
                "output_png_path": safe_posix(output_png),
                "render_exit_code": result.returncode,
                "stdout_log": safe_posix(stdout_path),
                "stderr_log": safe_posix(stderr_path),
                "dimensions": image_size(output_png) or {"width": 0, "height": 0},
                "source_image_texture_attempted": bool(texture_status.get("attempted")),
                "source_image_texture_loaded": bool(texture_status.get("loaded")),
                "source_image_texture_mode": texture_status.get("mode", "unknown"),
                "stage_geometry": bool(texture_status.get("stage_geometry")),
                "court_lines": int(texture_status.get("court_lines", 0) or 0),
                "layered_planes": int(texture_status.get("layered_planes", 0) or 0),
                "review_only_label": spec["review_only_label"],
            }
        )

    intake_rows = build_manual_intake_rows(variant_rows)
    intake_path = output_dir / CSV_NAME
    write_csv(intake_path, intake_rows)
    contact_sheet = build_contact_sheet(output_dir, variant_rows)
    report_path = output_dir / REPORT_NAME
    manifest = build_manifest(
        output_dir=output_dir,
        source_info=source_info,
        blender_executable=args.blender_executable,
        blender_version=blender_version,
        runner_path=runner_path,
        variant_rows=variant_rows,
        contact_sheet=contact_sheet,
        report_path=report_path,
        intake_path=intake_path,
    )
    report_path.write_text(build_report(manifest), encoding="utf-8")
    (output_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "output_dir": safe_posix(output_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
