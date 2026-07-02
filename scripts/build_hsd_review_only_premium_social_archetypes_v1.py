from __future__ import annotations

import argparse
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


VERSION = "hsd-review-only-premium-social-archetypes-v1"
GENERATED_BY = "scripts/build_hsd_review_only_premium_social_archetypes_v1.py"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
OUT_DIR_REL = Path("review_only_premium_social_archetypes")
RUNNER_NAME = "review_only_premium_social_archetypes_runner.py"
SPECS_NAME = "archetype_specs.json"
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_quality_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
README_NAME = "README.md"
CANVAS = {"width": 1080, "height": 1350}
BURN_IN = "REVIEW ONLY - PREMIUM VISUAL ARCHETYPE"

MANUAL_REVIEW_QUESTIONS = [
    "Which archetype has the highest near-term monetizable/social value?",
    "Which visual route should become the renderer baseline while photo sourcing is blocked?",
    "What is visually unacceptable before any publishing path?",
]

CSV_FIELDS = [
    "archetype_id",
    "archetype_name",
    "render_path",
    "composition_treatment_mode",
    "near_term_monetizable_value",
    "should_be_renderer_baseline",
    "visually_unacceptable_before_publishing",
    "operator_decision",
    "operator_notes",
    "review_only",
    "prototype_only",
    "photo_dependency",
    "asset_downloads",
    "source_auto_enabled",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "production_renderer_replacement": False,
    "source_auto_enabled": False,
}


class RenderResult:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def packet_root() -> Path:
    root = run_output_dir()
    if root:
        return root
    return repo_root() / "outputs" / "local" / "latest" / "files" / OUT_DIR_REL


def resolve_blender_executable(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.exists() else None
    return DEFAULT_BLENDER_EXECUTABLE if DEFAULT_BLENDER_EXECUTABLE.exists() else None


def load_font(size: int, *, bold: bool = False) -> Any:
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


def build_archetype_specs() -> list[dict[str, Any]]:
    return [
        {
            "archetype_id": "score_final_editorial",
            "archetype_name": "Score Final Editorial",
            "filename": "archetype_01_score_final_editorial.png",
            "composition_treatment_mode": "score_final_editorial_depth_stage",
            "layout_polish_checks": {
                "key_text_inside_canvas_intent": True,
                "key_text_edge_clipping_allowed": False,
                "secondary_text_on_dark_ground_intent": True,
            },
            "accent_color": [231, 190, 92],
            "support_color": [180, 191, 209],
            "background_top": [8, 11, 18],
            "background_bottom": [15, 23, 36],
            "glow_primary": [221, 176, 74],
            "glow_secondary": [49, 76, 129],
            "title": "FINAL",
            "kicker": "SCORE EDITORIAL",
            "score_left": "84",
            "score_right": "79",
            "team_left": "LIBERTY",
            "team_right": "ACES",
            "support_left": "FOURTH QUARTER CONTROL",
            "support_right": "LATE RUN FADES SHORT",
            "panel_title": "CLEAN SCORE HIERARCHY",
            "panel_lines": [
                "Procedural court depth and premium lighting",
                "make the score itself feel like the hero.",
            ],
            "self_critique": "Strongest near-term baseline. It feels materially richer than the APQ crop loop, though the scoreboard rhythm could still get bolder before any publishing path.",
            "manual_value_hint": "high",
        },
        {
            "archetype_id": "stat_player_spotlight_shell",
            "archetype_name": "Stat / Player Spotlight Shell",
            "filename": "archetype_02_stat_player_spotlight_shell.png",
            "composition_treatment_mode": "stat_shell_safe_subject_stage",
            "layout_polish_checks": {
                "key_text_inside_canvas_intent": True,
                "key_text_edge_clipping_allowed": False,
                "secondary_text_on_dark_ground_intent": True,
            },
            "accent_color": [255, 124, 144],
            "support_color": [189, 196, 214],
            "background_top": [17, 11, 20],
            "background_bottom": [25, 27, 44],
            "glow_primary": [140, 53, 62],
            "glow_secondary": [70, 90, 150],
            "title": "STAT / PLAYER SPOTLIGHT",
            "stat_number": "32",
            "stat_label": "POINTS",
            "support_line": "OVERSIZED STAT. ABSTRACT SUBJECT PLANE.",
            "safe_area_label": "SAFE IMAGE AREA",
            "self_critique": "Useful structure test, but still the weakest commercial card. The abstract subject plane has more depth now, yet it remains a future photo-shell rather than the lead HSD route.",
            "manual_value_hint": "medium",
        },
        {
            "archetype_id": "breaking_news_card",
            "archetype_name": "Breaking / News Card",
            "filename": "archetype_03_breaking_news_card.png",
            "composition_treatment_mode": "breaking_news_editorial_stage",
            "layout_polish_checks": {
                "key_text_inside_canvas_intent": True,
                "key_text_edge_clipping_allowed": False,
                "secondary_text_on_dark_ground_intent": True,
            },
            "accent_color": [255, 91, 61],
            "support_color": [188, 196, 210],
            "background_top": [7, 10, 18],
            "background_bottom": [26, 24, 33],
            "glow_primary": [124, 49, 37],
            "glow_secondary": [103, 89, 56],
            "badge": "BREAKING",
            "headline_lines": ["League Expansion", "Talks Shift Into", "Public View"],
            "body_lines": [
                "Text-first premium editorial card with strong",
                "contrast, clean pacing, and enough depth to",
                "feel monetizable even without athlete photography.",
            ],
            "footer_label": "BREAKING / NEWS CARD / NO PHOTO DEPENDENCY",
            "self_critique": "Most controlled and publish-adjacent text treatment. It is the safest companion renderer baseline if HSD needs premium news cards while photo sourcing is blocked.",
            "manual_value_hint": "high",
        },
    ]


def build_packet_specs(packet_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in build_archetype_specs():
        row = dict(base)
        row["output_png_path"] = (packet_dir / row["filename"]).as_posix()
        row["canvas"] = dict(CANVAS)
        row["review_only"] = True
        row["prototype_only"] = True
        row["photo_dependency"] = False
        row["burn_in_text"] = BURN_IN
        row["layout_polish_checks"] = dict(base.get("layout_polish_checks") or {})
        rows.append(row)
    return rows


def write_specs_file(packet_dir: Path, specs: list[dict[str, Any]]) -> Path:
    path = packet_dir / SPECS_NAME
    write_json(path, {"version": VERSION, "archetype_specs": specs}, sort_keys=True)
    return path


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

            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser()
                parser.add_argument("--specs-json", required=True)
                argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
                return parser.parse_args(argv)


            def clear_scene() -> None:
                bpy.ops.wm.read_factory_settings(use_empty=True)


            def choose_render_engine() -> str:
                scene = bpy.context.scene
                for candidate in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
                    try:
                        scene.render.engine = candidate
                        return candidate
                    except Exception:
                        continue
                return bpy.context.scene.render.engine


            def configure_render() -> None:
                scene = bpy.context.scene
                scene.render.engine = choose_render_engine()
                scene.render.resolution_x = 1080
                scene.render.resolution_y = 1350
                scene.render.resolution_percentage = 100
                scene.render.image_settings.file_format = "PNG"
                scene.render.film_transparent = False
                scene.display_settings.display_device = "sRGB"
                if scene.render.engine == "CYCLES":
                    scene.cycles.samples = 128
                    scene.cycles.use_denoising = True
                if hasattr(scene, "eevee"):
                    scene.eevee.taa_render_samples = 64
                scene.world = bpy.data.worlds.new("World")
                scene.world.use_nodes = True
                bg = scene.world.node_tree.nodes["Background"]
                bg.inputs[0].default_value = (0.010, 0.012, 0.020, 1.0)
                bg.inputs[1].default_value = 0.18


            def face_camera_rotation() -> tuple[float, float, float]:
                return (math.radians(90.0), 0.0, 0.0)


            def setup_camera() -> None:
                bpy.ops.object.camera_add(location=(0.0, -8.8, 0.10), rotation=(math.radians(90.0), 0.0, 0.0))
                camera = bpy.context.object
                camera.data.type = "ORTHO"
                camera.data.ortho_scale = 9.8
                bpy.context.scene.camera = camera


            def create_principled_material(name: str, color: tuple[float, float, float, float], *, roughness: float = 0.45, metallic: float = 0.0, emission_strength: float = 0.0) -> bpy.types.Material:
                material = bpy.data.materials.new(name=name)
                material.use_nodes = True
                nodes = material.node_tree.nodes
                principled = nodes.get("Principled BSDF")
                if principled is None:
                    principled = nodes.new("ShaderNodeBsdfPrincipled")
                principled.inputs["Base Color"].default_value = color
                principled.inputs["Roughness"].default_value = roughness
                principled.inputs["Metallic"].default_value = metallic
                if "Emission Color" in principled.inputs:
                    principled.inputs["Emission Color"].default_value = color
                if "Emission Strength" in principled.inputs:
                    principled.inputs["Emission Strength"].default_value = emission_strength
                return material


            def create_emission_material(name: str, color: tuple[float, float, float, float], strength: float) -> bpy.types.Material:
                material = bpy.data.materials.new(name=name)
                material.use_nodes = True
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                for node in list(nodes):
                    nodes.remove(node)
                emission = nodes.new("ShaderNodeEmission")
                output = nodes.new("ShaderNodeOutputMaterial")
                emission.inputs["Color"].default_value = color
                emission.inputs["Strength"].default_value = strength
                links.new(emission.outputs["Emission"], output.inputs["Surface"])
                return material


            def apply_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
                if obj.data.materials:
                    obj.data.materials[0] = material
                else:
                    obj.data.materials.append(material)


            def add_panel(
                name: str,
                location: tuple[float, float, float],
                scale: tuple[float, float, float],
                color: tuple[float, float, float, float],
                *,
                roughness: float = 0.4,
                metallic: float = 0.0,
                rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
                bevel_ratio: float = 0.03,
                bevel_segments: int = 3,
            ) -> bpy.types.Object:
                bpy.ops.mesh.primitive_cube_add(location=location, scale=scale, rotation=rotation)
                obj = bpy.context.object
                obj.name = name
                bevel = obj.modifiers.new(name="Bevel", type="BEVEL")
                bevel.width = min(scale[0], scale[2]) * bevel_ratio
                bevel.segments = bevel_segments
                apply_material(obj, create_principled_material(f"{name}Material", color, roughness=roughness, metallic=metallic))
                return obj


            def add_vertical_plane(name: str, location: tuple[float, float, float], scale: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
                bpy.ops.mesh.primitive_plane_add(location=location, rotation=face_camera_rotation(), scale=scale)
                obj = bpy.context.object
                obj.name = name
                apply_material(obj, material)
                return obj


            def add_line_bar(name: str, location: tuple[float, float, float], scale: tuple[float, float, float], color: tuple[float, float, float, float], *, emission_strength: float = 0.0) -> bpy.types.Object:
                material = create_principled_material(f"{name}Material", color, roughness=0.25, metallic=0.0, emission_strength=emission_strength)
                return add_panel(name, location, scale, color, roughness=0.25, metallic=0.0)


            def load_font_path(bold: bool) -> str:
                candidates = [
                    Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
                    Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
                    Path("C:/Windows/Fonts/bahnschrift.ttf"),
                ]
                for candidate in candidates:
                    if candidate.exists():
                        return str(candidate)
                return ""


            def add_text(
                name: str,
                text: str,
                location: tuple[float, float, float],
                size: float,
                color: tuple[float, float, float, float],
                *,
                bold: bool = True,
                align_x: str = "LEFT",
                emission_strength: float = 0.0,
                y_offset: float = 0.0,
            ) -> bpy.types.Object:
                bpy.ops.object.text_add(location=(location[0], location[1] + y_offset, location[2]), rotation=face_camera_rotation())
                obj = bpy.context.object
                obj.name = name
                obj.data.body = text
                obj.data.size = size
                obj.data.extrude = 0.0
                obj.data.bevel_depth = 0.0
                obj.data.align_x = align_x
                obj.data.align_y = "CENTER"
                font_path = load_font_path(bold)
                if font_path:
                    try:
                        obj.data.font = bpy.data.fonts.load(font_path)
                    except Exception:
                        pass
                apply_material(obj, create_principled_material(f"{name}Material", color, roughness=0.25, metallic=0.0, emission_strength=emission_strength))
                return obj


            def add_area_light(name: str, location: tuple[float, float, float], rotation: tuple[float, float, float], energy: float, color: tuple[float, float, float], size: float, size_y: float | None = None) -> bpy.types.Object:
                bpy.ops.object.light_add(type="AREA", location=location, rotation=rotation)
                light = bpy.context.object
                light.name = name
                light.data.energy = energy
                light.data.color = color
                light.data.shape = "RECTANGLE"
                light.data.size = size
                light.data.size_y = size if size_y is None else size_y
                return light


            def add_circle_arc(name: str, location: tuple[float, float, float], scale: tuple[float, float, float], color: tuple[float, float, float, float], *, thickness: float = 0.018) -> bpy.types.Object:
                bpy.ops.curve.primitive_bezier_circle_add(location=location, rotation=face_camera_rotation(), scale=scale)
                obj = bpy.context.object
                obj.name = name
                obj.data.bevel_depth = thickness
                obj.data.resolution_u = 32
                apply_material(obj, create_emission_material(f"{name}Material", color, 0.9))
                return obj


            def add_background(spec: dict[str, object]) -> None:
                top = tuple(float(v) / 255.0 for v in spec["background_top"]) + (1.0,)
                bottom = tuple(float(v) / 255.0 for v in spec["background_bottom"]) + (1.0,)
                primary_glow = tuple(float(v) / 255.0 for v in spec["glow_primary"]) + (1.0,)
                secondary_glow = tuple(float(v) / 255.0 for v in spec["glow_secondary"]) + (1.0,)

                add_vertical_plane(
                    "Backdrop",
                    location=(0.0, 2.8, 0.0),
                    scale=(4.8, 1.0, 6.2),
                    material=create_principled_material("BackdropMaterial", bottom, roughness=0.7),
                )
                add_vertical_plane(
                    "BackdropTop",
                    location=(0.0, 2.7, 1.6),
                    scale=(4.8, 1.0, 2.8),
                    material=create_principled_material("BackdropTopMaterial", top, roughness=0.8),
                )
                add_vertical_plane(
                    "GlowPrimary",
                    location=(0.0, 2.45, 1.1),
                    scale=(2.2, 1.0, 2.2),
                    material=create_emission_material("GlowPrimaryMaterial", primary_glow, 1.3),
                )
                add_vertical_plane(
                    "GlowSecondary",
                    location=(2.2, 2.35, -1.7),
                    scale=(1.6, 1.0, 1.6),
                    material=create_emission_material("GlowSecondaryMaterial", secondary_glow, 0.7),
                )
                add_panel(
                    "AtmosphereSlabLeft",
                    location=(-2.95, 1.68, 0.15),
                    scale=(0.16, 0.04, 3.75),
                    color=(0.06, 0.09, 0.15, 1.0),
                    roughness=0.5,
                    rotation=(math.radians(2.0), 0.0, math.radians(-5.0)),
                    bevel_ratio=0.01,
                    bevel_segments=2,
                )
                add_panel(
                    "AtmosphereSlabRight",
                    location=(3.05, 1.52, -0.2),
                    scale=(0.22, 0.04, 3.1),
                    color=(0.08, 0.09, 0.12, 1.0),
                    roughness=0.52,
                    rotation=(math.radians(-1.5), 0.0, math.radians(6.0)),
                    bevel_ratio=0.01,
                    bevel_segments=2,
                )
                add_panel(
                    "FloorStage",
                    location=(0.0, 1.98, -3.46),
                    scale=(4.5, 0.02, 0.34),
                    color=(0.10, 0.12, 0.18, 1.0),
                    roughness=0.6,
                    rotation=(math.radians(6.0), 0.0, 0.0),
                    bevel_ratio=0.008,
                    bevel_segments=2,
                )
                add_vertical_plane(
                    "FloorEdgeLight",
                    location=(0.0, 1.54, -3.16),
                    scale=(2.8, 1.0, 0.04),
                    material=create_emission_material("FloorEdgeLightMaterial", secondary_glow, 0.42),
                )
                add_area_light(
                    "TopLight",
                    location=(0.0, -2.6, 4.5),
                    rotation=(math.radians(73.0), 0.0, 0.0),
                    energy=2600,
                    color=(1.0, 0.97, 0.92),
                    size=6.2,
                    size_y=4.8,
                )
                add_area_light(
                    "RimLight",
                    location=(4.0, -2.0, 1.5),
                    rotation=(math.radians(88.0), 0.0, math.radians(-34.0)),
                    energy=1650,
                    color=(0.72, 0.79, 1.0),
                    size=2.4,
                    size_y=4.0,
                )
                add_area_light(
                    "AccentLight",
                    location=(-3.1, -1.6, 1.8),
                    rotation=(math.radians(92.0), 0.0, math.radians(28.0)),
                    energy=840,
                    color=(0.96, 0.86, 0.72),
                    size=1.8,
                    size_y=3.0,
                )


            def add_burn_in(text: str) -> None:
                add_panel(
                    "BurnInBand",
                    location=(0.0, 0.3, -3.2),
                    scale=(2.15, 0.06, 0.18),
                    color=(0.05, 0.07, 0.10, 1.0),
                    roughness=0.25,
                    metallic=0.02,
                    bevel_ratio=0.01,
                    bevel_segments=2,
                )
                add_text(
                    "BurnInText",
                    text,
                    location=(0.0, 0.18, -3.2),
                    size=0.19,
                    color=(0.93, 0.94, 0.97, 1.0),
                    bold=True,
                    align_x="CENTER",
                    emission_strength=0.12,
                )


            def build_score_final_editorial(spec: dict[str, object]) -> None:
                accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
                support = tuple(float(v) / 255.0 for v in spec["support_color"]) + (1.0,)
                add_panel("TopPill", (0.0, 0.55, 2.52), (3.05, 0.04, 0.18), (0.08, 0.10, 0.16, 1.0), roughness=0.18, bevel_ratio=0.012, bevel_segments=2)
                add_text("Title", str(spec["title"]), (-2.30, 0.18, 2.52), 0.38, (0.95, 0.96, 0.99, 1.0), bold=True)
                add_text("Kicker", str(spec["kicker"]), (2.34, 0.18, 2.54), 0.16, accent, bold=True, align_x="RIGHT")
                add_panel("ScoreCoreBlade", (0.34, 1.12, 0.34), (0.74, 0.03, 1.88), (0.58, 0.54, 0.42, 1.0), roughness=0.40, rotation=(0.0, 0.0, math.radians(1.2)), bevel_ratio=0.01, bevel_segments=2)
                add_panel("ScoreShadowBlade", (0.38, 1.30, -0.08), (0.92, 0.02, 2.24), (0.33, 0.38, 0.47, 1.0), roughness=0.66, rotation=(0.0, 0.0, math.radians(-0.6)), bevel_ratio=0.008, bevel_segments=2)
                add_text("ScoreLeft", str(spec["score_left"]), (-2.18, 0.08, 1.12), 1.28, (0.96, 0.97, 0.99, 1.0), bold=True)
                add_text("Dash", "-", (0.0, 0.02, 1.08), 0.86, accent, bold=True, align_x="CENTER")
                add_text("ScoreRight", str(spec["score_right"]), (1.24, 0.08, 1.12), 1.28, (0.96, 0.97, 0.99, 1.0), bold=True)
                add_text("TeamLeft", str(spec["team_left"]), (-2.36, 0.08, 0.04), 0.38, (0.96, 0.97, 0.99, 1.0), bold=True)
                add_text("TeamRight", str(spec["team_right"]), (1.54, 0.08, 0.04), 0.38, (0.96, 0.97, 0.99, 1.0), bold=True)
                add_text("SupportLeft", str(spec["support_left"]), (-2.36, 0.06, -0.28), 0.13, support, bold=False)
                add_text("SupportRight", str(spec["support_right"]), (1.54, 0.06, -0.28), 0.13, support, bold=False)
                add_panel("InsightPanel", (0.0, 0.82, -1.34), (2.86, 0.05, 0.60), (0.06, 0.09, 0.14, 1.0), roughness=0.24, rotation=(0.0, 0.0, math.radians(-0.8)), bevel_ratio=0.012, bevel_segments=2)
                add_text("PanelTitle", str(spec["panel_title"]), (-1.86, 0.16, -1.06), 0.24, (0.96, 0.97, 0.99, 1.0), bold=True)
                panel_lines = list(spec["panel_lines"])
                add_text("PanelLine1", str(panel_lines[0]), (-1.86, 0.15, -1.38), 0.15, (0.85, 0.88, 0.93, 1.0), bold=False)
                add_text("PanelLine2", str(panel_lines[1]), (-1.86, 0.15, -1.64), 0.15, (0.85, 0.88, 0.93, 1.0), bold=False)
                add_circle_arc("CourtArcOuter", (0.0, 1.35, -3.25), (4.2, 1.0, 1.7), accent, thickness=0.010)
                add_circle_arc("CourtArcInner", (0.0, 1.24, -2.84), (1.7, 1.0, 1.2), (0.75, 0.79, 0.88, 1.0), thickness=0.009)
                add_vertical_plane("CenterLine", (0.0, 1.10, -2.55), (0.01, 1.0, 1.2), create_emission_material("CenterLineMaterial", (1.0, 1.0, 1.0, 0.20), 0.25))


            def build_stat_player_spotlight_shell(spec: dict[str, object]) -> None:
                accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
                support = tuple(float(v) / 255.0 for v in spec["support_color"]) + (1.0,)
                add_text("Title", str(spec["title"]), (-1.98, 0.10, 2.38), 0.16, accent, bold=True)
                add_text("StatNumber", str(spec["stat_number"]), (-2.00, 0.04, 1.46), 1.46, (0.96, 0.97, 0.99, 1.0), bold=True)
                add_text("StatLabel", str(spec["stat_label"]), (-1.88, 0.02, 0.62), 0.42, (0.96, 0.97, 0.99, 1.0), bold=True)
                add_text("Support", str(spec["support_line"]), (-1.88, 0.02, -0.02), 0.12, support, bold=False)
                add_panel("SubjectBackPlate", (1.42, 1.04, 0.58), (0.92, 0.03, 1.40), (0.88, 0.83, 0.90, 1.0), roughness=0.5, rotation=(0.0, 0.0, math.radians(-1.8)), bevel_ratio=0.008, bevel_segments=2)
                add_panel("SubjectAccentPlate", (1.62, 0.94, 0.38), (0.98, 0.03, 1.00), (0.80, 0.60, 0.64, 1.0), roughness=0.42, rotation=(0.0, 0.0, math.radians(1.2)), bevel_ratio=0.008, bevel_segments=2)
                add_panel("SafeAreaFrame", (2.28, 0.98, 0.02), (0.82, 0.05, 1.62), (0.88, 0.89, 0.94, 1.0), roughness=0.22, rotation=(0.0, 0.0, math.radians(0.8)), bevel_ratio=0.014, bevel_segments=2)
                add_panel("SilhouetteOval", (2.30, 1.10, 0.16), (0.52, 0.02, 1.16), (0.40, 0.50, 0.68, 1.0), roughness=0.26, rotation=(0.0, 0.0, math.radians(3.4)), bevel_ratio=0.03, bevel_segments=3)
                add_panel("SilhouetteCore", (2.24, 1.02, -0.04), (0.62, 0.03, 0.86), (0.85, 0.82, 0.79, 1.0), roughness=0.36, rotation=(0.0, 0.0, math.radians(-1.8)), bevel_ratio=0.012, bevel_segments=2)
                add_panel("SubjectFootBlock", (2.54, 1.20, -1.60), (0.66, 0.03, 0.64), (0.62, 0.70, 0.82, 1.0), roughness=0.42, rotation=(0.0, 0.0, math.radians(-1.2)), bevel_ratio=0.008, bevel_segments=2)
                add_text("SafeAreaLabel", str(spec["safe_area_label"]), (2.24, 0.16, -1.48), 0.15, (0.94, 0.95, 0.98, 1.0), bold=True, align_x="CENTER")


            def build_breaking_news_card(spec: dict[str, object]) -> None:
                accent = tuple(float(v) / 255.0 for v in spec["accent_color"]) + (1.0,)
                support = tuple(float(v) / 255.0 for v in spec["support_color"]) + (1.0,)
                add_panel("Badge", (-2.00, 0.58, 2.46), (0.82, 0.04, 0.22), accent, roughness=0.16, bevel_ratio=0.012, bevel_segments=2)
                add_text("BadgeText", str(spec["badge"]), (-2.00, 0.14, 2.46), 0.26, (1.0, 1.0, 1.0, 1.0), bold=True, align_x="CENTER")
                add_panel("HeadlineCard", (0.18, 1.00, 0.80), (2.82, 0.05, 1.42), (0.05, 0.07, 0.11, 1.0), roughness=0.22, rotation=(0.0, 0.0, math.radians(-0.8)), bevel_ratio=0.012, bevel_segments=2)
                add_panel("GlowCard", (0.34, 1.18, 0.90), (2.54, 0.02, 1.24), (0.46, 0.56, 0.72, 1.0), roughness=0.40, rotation=(0.0, 0.0, math.radians(0.8)), bevel_ratio=0.008, bevel_segments=2)
                add_panel("AccentBar", (-2.56, 0.84, 0.60), (0.07, 0.03, 1.58), accent, roughness=0.26, bevel_ratio=0.008, bevel_segments=2)
                lines = list(spec["headline_lines"])
                add_text("Headline1", str(lines[0]), (-1.56, 0.12, 1.46), 0.52, (0.95, 0.96, 0.99, 1.0), bold=True)
                add_text("Headline2", str(lines[1]), (-1.56, 0.12, 1.00), 0.52, (0.95, 0.96, 0.99, 1.0), bold=True)
                add_text("Headline3", str(lines[2]), (-1.56, 0.12, 0.54), 0.52, (0.95, 0.96, 0.99, 1.0), bold=True)
                body_lines = list(spec["body_lines"])
                add_text("Body1", str(body_lines[0]), (-1.56, 0.10, -0.10), 0.16, support, bold=False)
                add_text("Body2", str(body_lines[1]), (-1.56, 0.10, -0.32), 0.16, support, bold=False)
                add_text("Body3", str(body_lines[2]), (-1.56, 0.10, -0.54), 0.16, support, bold=False)
                add_panel("FooterPill", (0.06, 0.78, -2.98), (2.10, 0.04, 0.12), (0.96, 0.96, 0.96, 1.0), roughness=0.20, bevel_ratio=0.01, bevel_segments=2)
                add_text("FooterLabel", str(spec["footer_label"]), (0.06, 0.14, -2.98), 0.10, (0.88, 0.75, 0.31, 1.0), bold=True, align_x="CENTER")


            def render_spec(spec: dict[str, object]) -> None:
                clear_scene()
                configure_render()
                setup_camera()
                add_background(spec)
                if spec["archetype_id"] == "score_final_editorial":
                    build_score_final_editorial(spec)
                elif spec["archetype_id"] == "stat_player_spotlight_shell":
                    build_stat_player_spotlight_shell(spec)
                else:
                    build_breaking_news_card(spec)
                add_burn_in(str(spec["burn_in_text"]))
                bpy.context.scene.render.filepath = str(spec["output_png_path"])
                bpy.ops.render.render(write_still=True)


            def main() -> int:
                args = parse_args()
                payload = json.loads(Path(args.specs_json).read_text(encoding="utf-8"))
                specs = payload.get("archetype_specs") if isinstance(payload, dict) else None
                if not isinstance(specs, list) or len(specs) != 3:
                    raise RuntimeError("expected exactly three archetype specs")
                for spec in specs:
                    render_spec(spec)
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            '''
        ).strip()
        + "\n"
    )


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


def run_blender_render(blender_executable: Path, runner_file: Path, specs_file: Path) -> RenderResult:
    result = subprocess.run(
        [
            str(blender_executable),
            "--background",
            "--factory-startup",
            "--python",
            str(runner_file),
            "--",
            "--specs-json",
            str(specs_file),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return RenderResult(result.returncode, result.stdout, result.stderr)


def verify_png_dimensions(path: Path) -> tuple[int, int]:
    if Image is None:
        raise RuntimeError("Pillow is unavailable for PNG verification")
    with Image.open(path) as image:
        return image.size


def build_contact_sheet(packet_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    contact_sheet_path = packet_dir / CONTACT_SHEET_NAME
    if Image is None or ImageDraw is None or ImageFont is None or ImageOps is None:
        return {"created": False, "path": "", "reason": "pillow_unavailable"}

    margin = 18
    card_w = 330
    card_h = 566
    thumb_box = (294, 368)
    canvas = Image.new("RGB", (1080, 680), (236, 239, 244))
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(30, bold=True)
    subtitle_font = load_font(16, bold=False)
    label_font = load_font(18, bold=True)
    body_font = load_font(14, bold=False)

    draw.rounded_rectangle((16, 18, 1064, 662), radius=26, fill=(242, 244, 248))
    draw.text((32, 32), "Review-Only Premium Social Archetypes", fill=(28, 32, 40), font=title_font)
    draw.text((32, 66), "Non-APQ visual architecture bypass while photo sourcing is blocked.", fill=(84, 96, 114), font=subtitle_font)

    for index, row in enumerate(rows):
        x0 = 32 + index * 340
        y0 = 92
        draw.rounded_rectangle((x0, y0, x0 + card_w, y0 + card_h), radius=22, fill=(255, 255, 255))
        with Image.open(Path(row["output_png_path"])) as source:
            thumb = ImageOps.fit(source.convert("RGB"), thumb_box, centering=(0.5, 0.2))
        canvas.paste(thumb, (x0, y0))
        draw.text((x0 + 18, y0 + 392), row["archetype_name"], fill=(31, 36, 44), font=label_font)
        critique_lines = textwrap.wrap(str(row["self_critique"]), width=37)[:5]
        y_text = y0 + 428
        for line in critique_lines:
            draw.text((x0 + 18, y_text), line, fill=(90, 99, 112), font=body_font)
            y_text += 16

    canvas.save(contact_sheet_path, "PNG")
    return {"created": True, "path": contact_sheet_path.as_posix(), "reason": ""}


def build_manual_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        output.append(
            {
                "archetype_id": row["archetype_id"],
                "archetype_name": row["archetype_name"],
                "render_path": row["output_png_path"],
                "composition_treatment_mode": row["composition_treatment_mode"],
                "near_term_monetizable_value": "",
                "should_be_renderer_baseline": "",
                "visually_unacceptable_before_publishing": "",
                "operator_decision": "",
                "operator_notes": "",
                "review_only": "true",
                "prototype_only": "true",
                "photo_dependency": "false",
                "asset_downloads": "false",
                "source_auto_enabled": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return output


def build_report(rows: list[dict[str, Any]], manifest_path: Path, blender_version: str) -> str:
    route_lines = "\n".join(
        [
            f"| `{row['archetype_id']}` | {row['composition_treatment_mode']} | `{row['output_png_path']}` |"
            for row in rows
        ]
    )
    critique_lines = "\n".join([f"- **{row['archetype_name']}**: {row['self_critique']}" for row in rows])
    return f"""# Review-Only Premium Social Archetypes

Status: `review_only_premium_social_archetypes_ready`
Version: `{VERSION}`
Blender: `{blender_version}`

This packet is a non-APQ visual architecture bypass while APQ waits for a better manually acquired review-only crop/source candidate. It uses Blender-backed procedural scene generation only: no APQ001 input, no downloaded photography, no paid APIs, no approvals, and no publishing state.

## Archetypes

| Archetype | Treatment | Output |
| --- | --- | --- |
{route_lines}

## Manual Review Questions

{chr(10).join(f"- {question}" for question in MANUAL_REVIEW_QUESTIONS)}

## Honest Self-Critique

{critique_lines}

## Blunt Recommendation

- `Score Final Editorial` should be the near-term renderer baseline if HSD needs the strongest premium score card right now.
- `Breaking / News Card` is the safest editorial companion route because it already feels close to a monetizable newsroom card without athlete photography.
- `Stat / Player Spotlight Shell` is useful, but only as architecture for later source-safe image integration rather than the first commercial baseline.

Manifest: `{manifest_path.as_posix()}`
"""


def build_readme(rows: list[dict[str, Any]]) -> str:
    names = ", ".join(row["archetype_name"] for row in rows)
    return f"""# Review-Only Premium Social Archetypes v1

This visual quality reset prototype is Blender-first and review-only.

Rendered routes:
- {names}

Why this exists:
- APQ layout work is paused while manual source/crop acquisition waits for a better candidate.
- This packet proves Blender can still move the HSD visual system forward without protected photos or downloads.

Guardrails:
- no APQ/protected photo input
- no downloads
- no approvals
- no publish-ready state
- no publishing
"""


def build_manifest(
    *,
    packet_dir: Path,
    runner_path: Path,
    specs_path: Path,
    report_path: Path,
    readme_path: Path,
    intake_path: Path,
    contact_sheet_info: dict[str, Any],
    rows: list[dict[str, Any]],
    blender_executable: Path,
    blender_version: str,
    render_result: RenderResult,
    repo_head: str,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "review_only_premium_social_archetypes_ready",
        "generated_at_utc": now_iso(),
        "generated_by": GENERATED_BY,
        "repo_head": repo_head,
        "packet_dir": packet_dir.as_posix(),
        "runner_path": runner_path.as_posix(),
        "specs_path": specs_path.as_posix(),
        "blender_executable": blender_executable.as_posix(),
        "blender_version": blender_version,
        "blender_first": True,
        "review_only": True,
        "prototype_only": True,
        "non_apq_visual_bypass": True,
        "photo_dependency": False,
        "production_renderer_replacement": False,
        "archetype_count": len(rows),
        "archetype_rows": rows,
        "contact_sheet_created": bool(contact_sheet_info.get("created")),
        "contact_sheet_path": str(contact_sheet_info.get("path") or ""),
        "report_path": report_path.as_posix(),
        "readme_path": readme_path.as_posix(),
        "manual_review_csv_path": intake_path.as_posix(),
        "manual_review_questions": list(MANUAL_REVIEW_QUESTIONS),
        "layout_safe_checks": {
            row["archetype_id"]: row.get("layout_polish_checks") or {}
            for row in rows
        },
        "render_exit_code": render_result.returncode,
        "render_stdout": render_result.stdout,
        "render_stderr": render_result.stderr,
        "traceback_present": "Traceback" in render_result.stdout or "Traceback" in render_result.stderr,
        **FALSE_GUARDRAILS,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Blender-first review-only premium social archetype packet.")
    parser.add_argument("--blender-executable", default="", help="Optional Blender executable override.")
    parser.add_argument("--head-commit", default="", help="Optional repo head commit for manifest evidence.")
    args = parser.parse_args(argv)

    packet_dir = packet_root()
    packet_dir.mkdir(parents=True, exist_ok=True)
    rows = build_packet_specs(packet_dir)
    specs_path = write_specs_file(packet_dir, rows)

    blender_executable = resolve_blender_executable(args.blender_executable or None)
    if blender_executable is None:
        raise RuntimeError("Blender executable could not be resolved locally.")
    blender_version = probe_blender_version(blender_executable)

    runner_path = packet_dir / RUNNER_NAME
    runner_path.write_text(build_runner_script(), encoding="utf-8")

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
        handle.write(build_runner_script())
        temp_runner = Path(handle.name)

    try:
        render_result = run_blender_render(blender_executable, temp_runner, specs_path)
    finally:
        try:
            temp_runner.unlink()
        except Exception:
            pass

    if render_result.returncode != 0:
        raise RuntimeError(render_result.stderr.strip() or render_result.stdout.strip() or "Blender render failed")

    for row in rows:
        output_path = Path(row["output_png_path"])
        if not output_path.exists():
            raise RuntimeError(f"Expected rendered PNG is missing: {output_path}")
        width, height = verify_png_dimensions(output_path)
        if (width, height) != (CANVAS["width"], CANVAS["height"]):
            raise RuntimeError(f"Unexpected PNG size for {output_path.name}: {width}x{height}")

    contact_sheet_info = build_contact_sheet(packet_dir, rows)
    if not contact_sheet_info.get("created"):
        raise RuntimeError(f"Contact sheet creation failed: {contact_sheet_info.get('reason')}")

    intake_path = packet_dir / CSV_NAME
    write_csv(intake_path, build_manual_rows(rows), fieldnames=CSV_FIELDS)
    readme_path = packet_dir / README_NAME
    write_text(readme_path, build_readme(rows))
    manifest_path = packet_dir / MANIFEST_NAME
    report_path = packet_dir / REPORT_NAME
    manifest = build_manifest(
        packet_dir=packet_dir,
        runner_path=runner_path,
        specs_path=specs_path,
        report_path=report_path,
        readme_path=readme_path,
        intake_path=intake_path,
        contact_sheet_info=contact_sheet_info,
        rows=rows,
        blender_executable=blender_executable,
        blender_version=blender_version,
        render_result=render_result,
        repo_head=args.head_commit.strip(),
    )
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(rows, manifest_path, blender_version))

    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "packet_dir": packet_dir.as_posix(),
                "blender_version": blender_version,
                "archetype_count": len(rows),
                "contact_sheet_created": bool(contact_sheet_info.get("created")),
                "review_only": True,
                "prototype_only": True,
                "photo_dependency": False,
                "asset_downloads": False,
                "source_auto_enabled": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
