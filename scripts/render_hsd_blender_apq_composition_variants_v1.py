from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys_path = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(sys_path))

from hsd_run_io import run_output_dir

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:  # pragma: no cover - Pillow is expected, but the packet should degrade cleanly.
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-blender-apq-composition-variants-v1-review-only"
SCHEMA_VERSION = "blender_apq_scene_payload_contract.v1"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
DEFAULT_SCENE_PAYLOAD = Path("outputs/local/latest/files/blender_apq_scene_payload_contract/sample_apq001_scene_payload.json")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/blender_apq_composition_variants")
DEFAULT_QUARANTINE_IMAGE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg"
)
RUNNER_NAME = "blender_apq_composition_variants_runner.py"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "variant_comparison_report.md"
CSV_NAME = "manual_variant_review_intake.csv"
CONTACT_SHEET_NAME = "contact_sheet.png"
SOURCE_BURN_IN_TEXT = "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE"
TEXTURE_STATUS_PREFIX = "HSD_TEXTURE_STATUS:"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "image_edits": False,
    "move_files": False,
    "paid_apis": False,
    "publish_ready": False,
    "publishing": False,
    "protected_asset_moves": False,
    "production_renderer_replacement": False,
    "renderer_behavior_change": False,
    "source_auto_enabled": False,
}

OUTPUT_DIMENSIONS = {"width": 1080, "height": 1350}

VARIANT_SPECS: list[dict[str, Any]] = [
    {
        "variant_id": "variant_01_photo_anchor",
        "output_name": "variant_01_photo_anchor.png",
        "visual_direction": "photo-first hero with open score typography",
        "photo_first_strength": "",
        "score_readability": "",
        "premium_editorial_feel": "",
        "burn_in_legibility": "",
        "background_color": [12, 15, 24],
        "accent_color": [240, 188, 66],
        "subtle_color": [195, 205, 224],
        "photo_frame": {"location": [-2.38, 0.15, 0.42], "scale": [2.42, 3.08, 1.0], "rotation_z": -1.2},
        "photo_title": {"line_1": "PHOTO FIRST", "line_2": "APQ001", "location": [1.04, 0.14, 1.64], "size": 0.42},
        "score_block": {"line_1": "OPEN SCORE", "line_2": "0 - 0", "location": [1.08, 0.12, 0.6], "size": 0.62},
        "support_lines": [
            {"text": "AIRY TYPOGRAPHY", "location": [1.08, 0.12, 0.14], "size": 0.21, "color": [228, 233, 245]},
            {"text": "NO DASHBOARD BOXES", "location": [1.08, 0.12, -0.14], "size": 0.18, "color": [168, 176, 191]},
        ],
        "use_score_plate": True,
        "use_editorial_scrim": True,
        "photo_visibility": "largest_and_most_emotional",
        "score_readability_note": "open_and_anchoring",
        "premium_editorial_note": "bold_photo_led",
    },
    {
        "variant_id": "variant_02_score_drama",
        "output_name": "variant_02_score_drama.png",
        "visual_direction": "score-led with stronger final-score hierarchy",
        "photo_first_strength": "",
        "score_readability": "",
        "premium_editorial_feel": "",
        "burn_in_legibility": "",
        "background_color": [10, 12, 18],
        "accent_color": [244, 96, 91],
        "subtle_color": [210, 214, 226],
        "photo_frame": {"location": [-2.58, -0.03, 0.15], "scale": [1.98, 2.62, 1.0], "rotation_z": -0.8},
        "photo_title": {"line_1": "SCORE DRAMA", "line_2": "APQ001", "location": [0.66, 0.12, 1.75], "size": 0.33},
        "score_block": {"line_1": "FINAL", "line_2": "0 - 0", "location": [0.56, 0.12, 0.82], "size": 0.82},
        "support_lines": [
            {"text": "PHOTOGRAPHY STILL VISIBLE", "location": [0.58, 0.12, 0.2], "size": 0.18, "color": [194, 200, 215]},
            {"text": "NO DASHBOARD BOXES", "location": [0.58, 0.12, -0.08], "size": 0.16, "color": [160, 166, 180]},
        ],
        "use_score_plate": False,
        "use_editorial_scrim": False,
        "photo_visibility": "visible_but_secondary",
        "score_readability_note": "strongest_hierarchy",
        "premium_editorial_note": "dramatic_and_sparse",
    },
    {
        "variant_id": "variant_03_clean_editorial",
        "output_name": "variant_03_clean_editorial.png",
        "visual_direction": "calmer premium magazine framing with lighter stat text",
        "photo_first_strength": "",
        "score_readability": "",
        "premium_editorial_feel": "",
        "burn_in_legibility": "",
        "background_color": [19, 21, 28],
        "accent_color": [230, 210, 157],
        "subtle_color": [194, 201, 214],
        "photo_frame": {"location": [-1.96, 0.15, 0.52], "scale": [1.9, 2.56, 1.0], "rotation_z": -1.0},
        "photo_title": {"line_1": "CLEAN EDITORIAL", "line_2": "APQ001", "location": [0.88, 0.12, 1.74], "size": 0.3},
        "score_block": {"line_1": "0 - 0", "line_2": "MAGAZINE TREATMENT", "location": [0.9, 0.12, 0.9], "size": 0.48},
        "support_lines": [
            {"text": "MORE NEGATIVE SPACE", "location": [0.9, 0.12, 0.28], "size": 0.16, "color": [198, 205, 217]},
            {"text": "LIGHTER STAT TEXT", "location": [0.9, 0.12, 0.0], "size": 0.14, "color": [150, 157, 171]},
        ],
        "use_score_plate": False,
        "use_editorial_scrim": True,
        "photo_visibility": "calm_and_luxurious",
        "score_readability_note": "soft_but_clear",
        "premium_editorial_note": "most_magazine_like",
    },
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_output_dir() -> Path:
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_scene_payload_path(explicit: str | None = None) -> Path:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.is_absolute() else repo_root() / candidate
    return repo_root() / DEFAULT_SCENE_PAYLOAD


def resolve_blender_executable(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.exists() else None
    return DEFAULT_BLENDER_EXECUTABLE if DEFAULT_BLENDER_EXECUTABLE.exists() else None


def safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolve_quarantine_image_path(scene_payload: dict[str, Any]) -> Path:
    payload_slot = scene_payload.get("action_photo_slot") if isinstance(scene_payload.get("action_photo_slot"), dict) else {}
    raw_path = str(payload_slot.get("quarantine_path") or "").strip()
    candidate = Path(raw_path) if raw_path else repo_root() / DEFAULT_QUARANTINE_IMAGE
    if not candidate.is_absolute():
        candidate = repo_root() / candidate

    quarantine_root = (repo_root() / "data/assets/quarantine/review_only_candidates").resolve(strict=False)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(quarantine_root)
    except ValueError:
        return (repo_root() / DEFAULT_QUARANTINE_IMAGE).resolve(strict=False)
    return resolved


def parse_texture_status(stdout: str, source_image_present: bool) -> dict[str, Any]:
    fallback_mode = "placeholder_missing_source" if not source_image_present else "placeholder_texture_status_unavailable"
    fallback = {
        "source_image_texture_attempted": bool(source_image_present),
        "source_image_texture_loaded": False,
        "source_image_texture_mode": fallback_mode,
        "source_image_texture_error": "",
    }
    for line in reversed(stdout.splitlines()):
        if not line.startswith(TEXTURE_STATUS_PREFIX):
            continue
        payload = line[len(TEXTURE_STATUS_PREFIX) :].strip()
        try:
            parsed = json.loads(payload)
        except Exception:
            return fallback
        if not isinstance(parsed, dict):
            return fallback
        merged = {**fallback, **parsed}
        merged["source_image_texture_attempted"] = bool(merged.get("source_image_texture_attempted"))
        merged["source_image_texture_loaded"] = bool(merged.get("source_image_texture_loaded"))
        merged["source_image_texture_mode"] = str(merged.get("source_image_texture_mode") or fallback_mode)
        merged["source_image_texture_error"] = str(merged.get("source_image_texture_error") or "")
        return merged
    return fallback


def read_texture_status_file(output_png_path: Path) -> dict[str, Any] | None:
    texture_status_path = output_png_path.with_suffix(".texture_status.json")
    if not texture_status_path.exists():
        return None
    try:
        payload = json.loads(texture_status_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    finally:
        try:
            texture_status_path.unlink()
        except Exception:
            pass
    if not isinstance(payload, dict):
        return None
    return {
        "source_image_texture_attempted": bool(payload.get("source_image_texture_attempted")),
        "source_image_texture_loaded": bool(payload.get("source_image_texture_loaded")),
        "source_image_texture_mode": str(payload.get("source_image_texture_mode") or ""),
        "source_image_texture_error": str(payload.get("source_image_texture_error") or ""),
    }


def write_json_file(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_text_file(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_csv_file(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def load_scene_context(scene_payload_path: Path) -> dict[str, Any]:
    payload_present = scene_payload_path.exists()
    payload = safe_load_json(scene_payload_path)
    payload_valid = bool(payload) or not payload_present
    source_image_path = resolve_quarantine_image_path(payload)
    source_image_present = source_image_path.exists()
    return {
        "scene_payload_present": payload_present,
        "scene_payload_valid": payload_valid,
        "scene_payload_status": "present" if payload_present and payload_valid else "missing",
        "source_image_path": source_image_path,
        "source_image_present": source_image_present,
        "source_image_source": "payload" if payload_present and payload else "default_placeholder",
        "scene_payload": payload,
    }


def build_variant_specs(scene_context: dict[str, Any]) -> list[dict[str, Any]]:
    source_image_path = scene_context["source_image_path"]
    source_image_present = bool(scene_context["source_image_present"])
    specs: list[dict[str, Any]] = []
    for index, base in enumerate(VARIANT_SPECS, start=1):
        specs.append(
            {
                **base,
                "variant_index": index,
                "source_image_path": source_image_path.as_posix(),
                "source_image_present": source_image_present,
                "canvas": dict(OUTPUT_DIMENSIONS),
                "burn_in_text": SOURCE_BURN_IN_TEXT,
                "render_exit_code": None,
                "render_stdout": "",
                "render_stderr": "",
                "output_png_path": "",
                "source_image_texture_attempted": source_image_present,
                "source_image_texture_loaded": False,
                "source_image_texture_mode": "pending",
                "source_image_texture_error": "",
                "placeholder_used": not source_image_present,
            }
        )
    return specs


def build_manual_rows(variant_specs: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in variant_specs:
        rows.append(
            {
                "variant_id": spec["variant_id"],
                "visual_direction": spec["visual_direction"],
                "photo_first_strength": "",
                "score_readability": "",
                "premium_editorial_feel": "",
                "burn_in_legibility": "",
                "operator_decision": "",
                "operator_notes": "",
            }
        )
    return rows


def build_report(payload: dict[str, Any]) -> str:
    variant_lines = "\n".join(
        [
            f"| `{row['variant_id']}` | {row['visual_direction']} | `{row['render_exit_code']}` | `{row['output_png_path']}` |"
            for row in payload["variant_rows"]
        ]
    )
    review_rows = "\n".join(
        [
            f"- `{row['variant_id']}`: {row['visual_direction']}."
            for row in payload["variant_rows"]
        ]
    )
    source_status = "present" if payload["source_image_present"] else "missing"
    texture_status = "loaded" if payload.get("source_image_texture_loaded") else "placeholder"
    recommendation = (
        "The photo-anchor variant should usually drive the next lane if the source image is usable, because it tests the most useful first-step composition."
        if payload["source_image_present"]
        else "The score-drama variant is the safest next-lane candidate here, because the source image is missing and the stronger hierarchy keeps the packet readable."
    )
    return f"""# APQ001 Blender Composition Variants

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is review-only, artifact-only, and quarantine-only. It creates exactly three 1080x1350 composition directions for APQ001 without changing the production renderer, downloading anything, moving files, or approving assets.

## Inputs

- Scene payload present: `{payload['scene_payload_present']}`
- Scene payload status: `{payload['scene_payload_status']}`
- Source image present: `{payload['source_image_present']}`
- Source image path: `{payload['source_image_path']}`
- Source image texture attempted: `{payload['source_image_texture_attempted']}`
- Source image texture loaded: `{payload['source_image_texture_loaded']}`
- Source image texture mode: `{payload['source_image_texture_mode']}`
- Blender version: `{payload['blender_version']}`

## Comparison

| Variant | Direction | Render exit | Output |
| --- | --- | ---: | --- |
{variant_lines}

## How To Review

{review_rows}

Use the manual intake CSV to record the next decision with one of:

- `continue_this_direction`
- `revise_this_direction`
- `reject_this_direction`
- `pause_for_external_visual_qa`

## Recommendation

{recommendation}

## Guardrails

{chr(10).join(f"- {key}={str(value).lower()}" for key, value in sorted(payload['guardrails'].items()))}

## Notes

- When the source image is missing locally, the renders use a clearly labeled placeholder instead of downloading or substituting another asset.
- The burn-in remains visible in-canvas for every variant.
- The variants intentionally explore photo-first, score-led, and editorial directions while staying review-only.
- Source image status for this run: `{source_status}`.
- Texture status for this run: `{texture_status}`.
"""


def build_contact_sheet(packet_dir: Path, variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    contact_sheet_path = packet_dir / CONTACT_SHEET_NAME
    if Image is None or ImageDraw is None or ImageFont is None or ImageOps is None:
        return {"created": False, "path": "", "reason": "pillow_unavailable", "source_count": len(variant_rows)}

    images: list[tuple[dict[str, Any], Any]] = []
    for row in variant_rows:
        try:
            image = Image.open(Path(row["output_png_path"])).convert("RGB")
        except Exception:
            continue
        images.append((row, image))

    if not images:
        return {"created": False, "path": "", "reason": "no_readable_images_found", "source_count": 0}

    margin = 24
    cell_w = 340
    cell_h = 520
    thumb_box = (300, 375)
    sheet_w = margin * 2 + cell_w * len(images)
    sheet_h = margin * 2 + cell_h
    canvas = Image.new("RGB", (sheet_w, sheet_h), (245, 246, 249))
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

    draw.text((margin, 12), "APQ001 Blender Composition Variants", fill=(22, 26, 36), font=title_font)
    draw.text(
        (margin, 32),
        "Review-only contact sheet. Compare photo-first strength, score hierarchy, editorial calm, and burn-in legibility.",
        fill=(60, 66, 79),
        font=body_font,
    )

    for index, (row, image) in enumerate(images):
        x0 = margin + index * cell_w
        y0 = margin + 60
        draw.rounded_rectangle((x0, y0, x0 + cell_w - 12, y0 + cell_h - 12), radius=18, fill=(255, 255, 255), outline=(203, 209, 219), width=2)
        thumb = ImageOps.contain(image, thumb_box)
        thumb_x = x0 + (cell_w - 12 - thumb.width) // 2
        thumb_y = y0 + 18
        canvas.paste(thumb, (thumb_x, thumb_y))
        label_y = y0 + 408
        draw.text((x0 + 18, label_y), row["variant_id"], fill=(20, 25, 36), font=title_font)
        draw.text((x0 + 18, label_y + 18), row["visual_direction"], fill=(68, 76, 88), font=body_font)
        draw.text((x0 + 18, label_y + 34), f"Exit code: {row['render_exit_code']}", fill=(68, 76, 88), font=body_font)

    draw.text(
        (margin, sheet_h - 22),
        "If the source image is absent, the photo slot is explicitly labeled as a placeholder.",
        fill=(62, 68, 80),
        font=body_font,
    )
    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(contact_sheet_path, "PNG")
    return {"created": True, "path": contact_sheet_path.as_posix(), "reason": "", "source_count": len(images)}


def build_manifest(
    *,
    blender_executable: Path | None,
    blender_version: str,
    scene_payload_path: Path,
    scene_context: dict[str, Any],
    variant_rows: list[dict[str, Any]],
    contact_sheet_info: dict[str, Any],
    report_path: Path,
    intake_path: Path,
    runner_path: Path,
) -> dict[str, Any]:
    source_image_present = bool(scene_context["source_image_present"])
    source_payload_present = bool(scene_context["scene_payload_present"])
    render_exit_codes = {row["variant_id"]: row["render_exit_code"] for row in variant_rows}
    source_image_texture_attempted = any(bool(row.get("source_image_texture_attempted")) for row in variant_rows)
    source_image_texture_loaded = all(bool(row.get("source_image_texture_loaded")) for row in variant_rows) if source_image_present else False
    return {
        "version": VERSION,
        "status": "blender_apq_composition_variants_ready" if all(code == 0 for code in render_exit_codes.values()) else "blender_apq_composition_variants_ready_with_render_warnings",
        "generated_at_utc": now_iso(),
        "generated_by": Path(__file__).name,
        "blender_executable": blender_executable.as_posix() if blender_executable else "",
        "blender_version": blender_version,
        "scene_payload_path": scene_payload_path.as_posix(),
        "scene_payload_present": source_payload_present,
        "scene_payload_status": scene_context["scene_payload_status"],
        "source_image_path": scene_context["source_image_path"].as_posix(),
        "source_image_present": source_image_present,
        "source_image_texture_attempted": source_image_texture_attempted,
        "source_image_texture_loaded": source_image_texture_loaded,
        "source_image_texture_mode": "loaded" if source_image_texture_loaded else "placeholder",
        "source_auto_enabled": False,
        "output_dir": resolve_output_dir().as_posix(),
        "manifest_path": (resolve_output_dir() / MANIFEST_NAME).as_posix(),
        "report_path": report_path.as_posix(),
        "manual_variant_review_intake_path": intake_path.as_posix(),
        "contact_sheet_path": contact_sheet_info["path"],
        "contact_sheet_created": contact_sheet_info["created"],
        "contact_sheet_source_count": contact_sheet_info["source_count"],
        "runner_script_path": runner_path.as_posix(),
        "output_dimensions": dict(OUTPUT_DIMENSIONS),
        "variant_count": len(variant_rows),
        "variant_rows": variant_rows,
        "render_exit_codes": render_exit_codes,
        "review_only": True,
        "artifact_only": True,
        "apq001_quarantine_only": True,
        "asset_approved": False,
        "approval_state_change": False,
        "asset_downloads": False,
        "download_performed": False,
        "image_edits": False,
        "move_files": False,
        "protected_asset_moves": False,
        "renderer_behavior_change": False,
        "production_renderer_replacement": False,
        "publish_ready": False,
        "publishing": False,
        "auto_publish": False,
        "auto_approval": False,
        "guardrails": dict(FALSE_GUARDRAILS),
    }


def build_runner_script(variant_specs: list[dict[str, Any]]) -> str:
    baked_specs = textwrap.indent(json.dumps(variant_specs, indent=2, sort_keys=True), "            ")
    return (
        textwrap.dedent(
            f'''
            from __future__ import annotations

            import argparse
            import json
            import math
            import sys
            from pathlib import Path

            import bpy

            BOLD_FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")
            BOLD_FONT = None
            TEXTURE_STATUS_PREFIX = {json.dumps(TEXTURE_STATUS_PREFIX)}
            BAKED_SPECS = json.loads(r"""{baked_specs}""")


            def argv_after_double_dash() -> list[str]:
                if "--" not in sys.argv:
                    return []
                return sys.argv[sys.argv.index("--") + 1 :]


            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser()
                parser.add_argument("--scene-payload", required=True)
                parser.add_argument("--variant-id", required=True)
                parser.add_argument("--output-png", required=True)
                return parser.parse_args(argv_after_double_dash())


            def bold_font():
                global BOLD_FONT
                if BOLD_FONT is not None:
                    return BOLD_FONT
                if BOLD_FONT_PATH.exists():
                    BOLD_FONT = bpy.data.fonts.load(BOLD_FONT_PATH.as_posix(), check_existing=True)
                else:
                    BOLD_FONT = bpy.data.fonts[0] if bpy.data.fonts else None
                return BOLD_FONT


            def rgba(values: list[int] | tuple[int, ...], alpha: float = 1.0) -> tuple[float, float, float, float]:
                r, g, b = values
                return (r / 255.0, g / 255.0, b / 255.0, alpha)


            def choose_render_engine() -> str:
                try:
                    enum_items = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
                    supported = {{item.identifier for item in enum_items}}
                except Exception:
                    supported = set()
                for candidate in ("CYCLES", "BLENDER_EEVEE"):
                    if candidate in supported:
                        return candidate
                return "CYCLES"


            def choose_cycles_denoiser(scene: bpy.types.Scene) -> str:
                try:
                    enum_items = scene.cycles.bl_rna.properties["denoiser"].enum_items
                    supported = {{item.identifier for item in enum_items}}
                except Exception:
                    supported = set()
                for candidate in ("OPENIMAGEDENOISE", "OPTIX", "NLM"):
                    if candidate in supported:
                        return candidate
                return ""


            def clear_scene() -> None:
                bpy.ops.object.select_all(action="SELECT")
                bpy.ops.object.delete(use_global=False)


            def set_world(background: list[int]) -> None:
                world = bpy.data.worlds.new("APQVariantWorld")
                world.use_nodes = True
                bpy.context.scene.world = world
                background_node = world.node_tree.nodes.get("Background")
                if background_node is not None:
                    background_node.inputs[0].default_value = rgba(background, 1.0)
                    background_node.inputs[1].default_value = 0.8


            def setup_camera(spec: dict[str, object]) -> None:
                camera_spec = spec.get("camera", {{}}) if isinstance(spec.get("camera"), dict) else {{}}
                location = tuple(camera_spec.get("location") or (0.0, -8.6, 2.0))
                ortho_scale = float(camera_spec.get("ortho_scale") or 8.0)
                target = tuple(camera_spec.get("target") or (0.0, 0.0, 0.85))
                bpy.ops.object.camera_add(location=location)
                camera = bpy.context.active_object
                camera.data.type = "ORTHO"
                camera.data.ortho_scale = ortho_scale
                target_obj = bpy.data.objects.new("APQVariantTarget", None)
                target_obj.location = target
                bpy.context.collection.objects.link(target_obj)
                constraint = camera.constraints.new(type="TRACK_TO")
                constraint.target = target_obj
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


            def make_photo_texture_material(name: str, image: bpy.types.Image) -> bpy.types.Material:
                material = bpy.data.materials.new(name)
                material.use_nodes = True
                material.blend_method = "BLEND"
                if hasattr(material, "shadow_method"):
                    material.shadow_method = "HASHED"
                nodes = material.node_tree.nodes
                links = material.node_tree.links
                for node in list(nodes):
                    nodes.remove(node)
                tex_coord = nodes.new("ShaderNodeTexCoord")
                mapping = nodes.new("ShaderNodeMapping")
                texture = nodes.new("ShaderNodeTexImage")
                principled = nodes.new("ShaderNodeBsdfPrincipled")
                output = nodes.new("ShaderNodeOutputMaterial")
                texture.image = image
                texture.interpolation = "Cubic"
                mapping.inputs["Rotation"].default_value[2] = math.pi
                links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
                links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
                links.new(texture.outputs["Color"], principled.inputs["Base Color"])
                if "Alpha" in texture.outputs and "Alpha" in principled.inputs:
                    links.new(texture.outputs["Alpha"], principled.inputs["Alpha"])
                if "Roughness" in principled.inputs:
                    principled.inputs["Roughness"].default_value = 0.78
                if "Specular IOR Level" in principled.inputs:
                    principled.inputs["Specular IOR Level"].default_value = 0.18
                links.new(principled.outputs["BSDF"], output.inputs["Surface"])
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
                align_x: str = "LEFT",
                extrude: float = 0.0,
                bevel: float = 0.0,
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
                material = make_material(f"{{label}}_Text", color, roughness=0.22, emission=4.0)
                apply_material(obj, material)
                return obj


            def add_photo_or_placeholder(spec: dict[str, object], source_photo_path: Path, source_image_present: bool) -> dict[str, object]:
                photo_frame = spec.get("photo_frame", {{}}) if isinstance(spec.get("photo_frame"), dict) else {{}}
                location = tuple(photo_frame.get("location") or (-2.3, 0.16, 0.32))
                scale = tuple(photo_frame.get("scale") or (2.2, 2.8, 1.0))
                rotation_z = math.radians(float(photo_frame.get("rotation_z") or -1.0))
                texture_status = {{
                    "source_image_texture_attempted": bool(source_image_present),
                    "source_image_texture_loaded": False,
                    "source_image_texture_mode": "placeholder_missing_source" if not source_image_present else "placeholder_texture_load_failed",
                    "source_image_texture_error": "",
                }}
                frame = add_plane(
                    "PhotoFrame",
                    location,
                    (math.radians(-90.0), 0.0, rotation_z),
                    scale,
                    make_material("PhotoFrameMaterial", tuple(spec.get("subtle_color") or [190, 198, 210]) + (1.0,), roughness=0.92, alpha=0.34),
                )
                frame.location = location
                if source_image_present and source_photo_path.exists():
                    try:
                        image = bpy.data.images.load(source_photo_path.as_posix(), check_existing=True)
                        image_size = tuple(getattr(image, "size", (0, 0)))
                        if not image_size[0] or not image_size[1]:
                            raise RuntimeError("loaded_image_has_no_dimensions")
                        photo_plane = add_plane(
                            "PhotoTexture",
                            (location[0], location[1] - 0.014, location[2]),
                            (math.radians(-90.0), 0.0, rotation_z),
                            (scale[0] * 0.92, scale[1] * 0.92, 1.0),
                            make_photo_texture_material("APQSourcePhotoMaterial", image),
                        )
                        photo_plane.location = (location[0], location[1] - 0.014, location[2])
                        texture_status["source_image_texture_loaded"] = True
                        texture_status["source_image_texture_mode"] = "loaded"
                    except Exception as exc:
                        texture_status["source_image_texture_error"] = str(exc)
                        placeholder = make_material("APQSourcePlaceholder", tuple(spec.get("accent_color") or [220, 120, 90]) + (1.0,), roughness=0.84, alpha=0.94)
                        apply_material(frame, placeholder)
                        add_text(
                            "SOURCE IMAGE\\nFAILED TO LOAD",
                            location=(location[0] - 0.62, location[1] + 0.1, location[2] + 0.95),
                            size=0.16,
                            color=(0.98, 0.97, 0.95, 1.0),
                        )
                        add_text(
                            "PLACEHOLDER ONLY",
                            location=(location[0] - 0.62, location[1] + 0.1, location[2] - 0.08),
                            size=0.12,
                            color=(0.98, 0.91, 0.79, 1.0),
                        )
                else:
                    placeholder = make_material("APQSourcePlaceholder", tuple(spec.get("accent_color") or [220, 120, 90]) + (1.0,), roughness=0.84, alpha=0.94)
                    apply_material(frame, placeholder)
                    add_text(
                        "SOURCE IMAGE\\nNOT PRESENT LOCALLY",
                        location=(location[0] - 0.62, location[1] + 0.1, location[2] + 0.95),
                        size=0.16,
                        color=(0.98, 0.97, 0.95, 1.0),
                    )
                    add_text(
                        "PLACEHOLDER ONLY",
                        location=(location[0] - 0.62, location[1] + 0.1, location[2] - 0.08),
                        size=0.12,
                        color=(0.98, 0.91, 0.79, 1.0),
                    )
                return texture_status


            def add_scene(spec: dict[str, object], source_photo_path: Path, source_image_present: bool) -> dict[str, object]:
                background = tuple(spec.get("background_color") or [13, 17, 24])
                accent = tuple(spec.get("accent_color") or [235, 189, 72])
                subtle = tuple(spec.get("subtle_color") or [201, 209, 222])
                set_world(list(background))
                bpy.ops.mesh.primitive_plane_add(location=(0.0, 1.95, -0.02), rotation=(math.radians(-90.0), 0.0, 0.0))
                backdrop = bpy.context.active_object
                backdrop.scale = (6.0, 4.8, 1.0)
                apply_material(backdrop, make_material("BackdropMaterial", rgba(list(background), 1.0), roughness=1.0))
                if spec.get("use_editorial_scrim"):
                    add_plane(
                        "EditorialScrim",
                        (1.88, 0.12, 0.96),
                        (math.radians(-90.0), 0.0, 0.0),
                        (2.52, 4.0, 1.0),
                        make_material("EditorialScrimMaterial", (0.03, 0.05, 0.08, 1.0), roughness=0.94, alpha=0.72),
                    )
                if spec.get("use_score_plate"):
                    add_plane(
                        "ScorePlate",
                        (1.58, 0.15, 0.12),
                        (math.radians(-90.0), 0.0, 0.0),
                        (1.58, 2.08, 1.0),
                        make_material("ScorePlateMaterial", (0.04, 0.05, 0.08, 1.0), roughness=0.84, alpha=0.62),
                    )
                add_plane(
                    "PhotoShadow",
                    (-2.24, 0.25, 0.28),
                    (math.radians(-90.0), 0.0, math.radians(-1.0)),
                    (2.44, 3.02, 1.0),
                    make_material("PhotoShadowMaterial", (0.01, 0.01, 0.02, 1.0), roughness=1.0, alpha=0.16),
                )
                texture_status = add_photo_or_placeholder(spec, source_photo_path, source_image_present)
                add_plane(
                    "AccentLine",
                    (-0.08, 0.08, 0.0),
                    (math.radians(-90.0), 0.0, 0.0),
                    (0.02, 2.86, 1.0),
                    make_material("AccentLineMaterial", rgba(list(accent), 1.0), roughness=0.2, emission=0.85),
                )
                photo_title = spec.get("photo_title", {{}}) if isinstance(spec.get("photo_title"), dict) else {{}}
                score_block = spec.get("score_block", {{}}) if isinstance(spec.get("score_block"), dict) else {{}}
                title_line_1 = str(photo_title.get("line_1") or "PHOTO FIRST")
                title_line_2 = str(photo_title.get("line_2") or "APQ001")
                title_location = tuple(photo_title.get("location") or (1.0, 0.12, 1.68))
                title_size = float(photo_title.get("size") or 0.34)
                add_text(title_line_1, location=title_location, size=title_size, color=(0.98, 0.98, 0.99, 1.0))
                add_text(title_line_2, location=(title_location[0] + 0.02, title_location[1], title_location[2] - 0.36), size=title_size * 0.8, color=rgba(list(accent), 1.0))
                score_line_1 = str(score_block.get("line_1") or "OPEN SCORE")
                score_line_2 = str(score_block.get("line_2") or "0 - 0")
                score_location = tuple(score_block.get("location") or (1.0, 0.12, 0.75))
                score_size = float(score_block.get("size") or 0.55)
                add_text(score_line_1, location=score_location, size=score_size * 0.72, color=(0.96, 0.96, 0.98, 1.0))
                add_text(score_line_2, location=(score_location[0], score_location[1], score_location[2] - 0.42), size=score_size, color=(0.98, 0.98, 0.99, 1.0))
                for line in spec.get("support_lines", []):
                    if not isinstance(line, dict):
                        continue
                    add_text(
                        str(line.get("text") or ""),
                        location=tuple(line.get("location") or (1.0, 0.12, 0.0)),
                        size=float(line.get("size") or 0.14),
                        color=rgba(list(line.get("color") or list(subtle)), 1.0),
                    )
                add_text(
                    spec["variant_id"].replace("_", " ").upper(),
                    location=(-4.2, 0.12, 2.05),
                    size=0.18,
                    color=rgba(list(accent), 1.0),
                )
                burn_text = spec.get("burn_in_text") or "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE"
                add_text(
                    str(burn_text),
                    location=(0.0, -0.12, -1.34),
                    size=0.24,
                    color=(0.98, 0.98, 0.98, 1.0),
                    align_x="CENTER",
                )
                return texture_status


            def add_lights(spec: dict[str, object]) -> None:
                accent = tuple(spec.get("accent_color") or [235, 189, 72])
                bpy.ops.object.light_add(type="AREA", location=(-3.0, -4.0, 4.3))
                key = bpy.context.active_object
                key.data.energy = 1800.0
                key.data.shape = "RECTANGLE"
                key.data.size = 5.4
                key.data.size_y = 3.6
                bpy.ops.object.light_add(type="AREA", location=(3.2, -3.0, 2.0))
                fill = bpy.context.active_object
                fill.data.energy = 640.0
                fill.data.shape = "RECTANGLE"
                fill.data.size = 3.0
                fill.data.size_y = 2.2
                bpy.ops.object.light_add(type="AREA", location=(0.8, 2.0, 3.8))
                top = bpy.context.active_object
                top.data.energy = 300.0
                top.data.shape = "RECTANGLE"
                top.data.size = 2.8
                top.data.size_y = 2.0
                bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, 0.0))
                sun = bpy.context.active_object
                sun.rotation_euler = (math.radians(30.0), 0.0, math.radians(-25.0))
                sun.data.energy = 0.8
                bpy.ops.object.light_add(type="AREA", location=(-1.8, 1.4, 2.2))
                accent_light = bpy.context.active_object
                accent_light.data.energy = 180.0
                accent_light.data.shape = "RECTANGLE"
                accent_light.data.size = 1.8
                accent_light.data.size_y = 1.2
                accent_light.color = rgba(list(accent), 1.0)


            def configure_render(output_png: Path) -> None:
                scene = bpy.context.scene
                scene.render.engine = choose_render_engine()
                scene.render.resolution_x = 1080
                scene.render.resolution_y = 1350
                scene.render.resolution_percentage = 100
                scene.render.filepath = output_png.as_posix()
                scene.render.image_settings.file_format = "PNG"
                scene.render.image_settings.color_mode = "RGBA"
                if hasattr(scene, "cycles"):
                    if hasattr(scene.cycles, "samples"):
                        scene.cycles.samples = 128
                    if hasattr(scene.cycles, "preview_samples"):
                        scene.cycles.preview_samples = 32
                    if hasattr(scene.cycles, "use_adaptive_sampling"):
                        scene.cycles.use_adaptive_sampling = True
                    if hasattr(scene.cycles, "adaptive_threshold"):
                        scene.cycles.adaptive_threshold = 0.01
                    if hasattr(scene.cycles, "use_denoising"):
                        scene.cycles.use_denoising = True
                    if hasattr(scene.cycles, "use_preview_denoising"):
                        scene.cycles.use_preview_denoising = True
                    denoiser = choose_cycles_denoiser(scene)
                    if denoiser and hasattr(scene.cycles, "denoiser"):
                        scene.cycles.denoiser = denoiser
                if hasattr(scene, "eevee"):
                    if hasattr(scene.eevee, "taa_render_samples"):
                        scene.eevee.taa_render_samples = 32
                    if hasattr(scene.eevee, "taa_samples"):
                        scene.eevee.taa_samples = 32
                    if hasattr(scene.eevee, "use_gtao"):
                        scene.eevee.use_gtao = False
                    if hasattr(scene.eevee, "use_bloom"):
                        scene.eevee.use_bloom = False
                if hasattr(scene.render, "dither_intensity"):
                    scene.render.dither_intensity = 0.0
                scene.render.film_transparent = False


            def main() -> int:
                args = parse_args()
                payload_path = Path(args.scene_payload)
                variant = next((item for item in BAKED_SPECS if item["variant_id"] == args.variant_id), None)
                if variant is None:
                    raise RuntimeError(f"Unknown variant id: {{args.variant_id}}")
                scene_payload = json.loads(payload_path.read_text(encoding="utf-8")) if payload_path.exists() else {{}}
                source_image_path = Path(str(variant.get("source_image_path") or ""))
                source_image_present = bool(variant.get("source_image_present")) and source_image_path.exists()

                clear_scene()
                set_world(list(variant.get("background_color") or [13, 17, 24]))
                setup_camera(variant)
                texture_status = add_scene(variant, source_image_path, source_image_present)
                add_lights(variant)
                configure_render(Path(args.output_png))
                texture_status_path = Path(args.output_png).with_suffix(".texture_status.json")
                texture_status_path.write_text(json.dumps(texture_status, indent=2, sort_keys=True), encoding="utf-8")
                print(f"{TEXTURE_STATUS_PREFIX}{{json.dumps(texture_status, sort_keys=True)}}")
                bpy.ops.render.render(write_still=True)
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            '''
        ).strip()
        + "\n"
    )


def write_runner_script(path: Path, variant_specs: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_runner_script(variant_specs), encoding="utf-8")
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
            "--scene-payload",
            str(scene_payload_path),
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


def write_placeholder_png(path: Path, spec: dict[str, Any], source_image_present: bool) -> None:
    if Image is None:
        path.write_bytes(b"")
        return
    canvas = Image.new("RGBA", (OUTPUT_DIMENSIONS["width"], OUTPUT_DIMENSIONS["height"]), tuple(spec["background_color"]) + (255,))
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default() if ImageFont else None
    body_font = ImageFont.load_default() if ImageFont else None
    accent = tuple(spec["accent_color"]) + (255,)
    subtle = tuple(spec["subtle_color"]) + (255,)

    variant_id = spec["variant_id"]
    draw.rectangle((60, 78, 1018, 1246), outline=accent, width=6)

    if variant_id == "variant_01_photo_anchor":
        frame = (98, 118, 596, 1046)
        photo = (140, 224, 554, 848)
        title = (660, 180)
        score = (660, 318)
        support = [(660, 406, "OPEN TYPOGRAPHY"), (660, 438, "PHOTO LEADS THE READ")]
    elif variant_id == "variant_02_score_drama":
        frame = (92, 118, 540, 1090)
        photo = (132, 236, 500, 860)
        title = (646, 170)
        score = (646, 282)
        support = [(646, 394, "FINAL-SCORE HIERARCHY"), (646, 426, "PHOTO STILL VISIBLE")]
    else:
        frame = (108, 118, 624, 1002)
        photo = (150, 232, 584, 828)
        title = (646, 172)
        score = (646, 322)
        support = [(646, 422, "NEGATIVE SPACE"), (646, 454, "LIGHTER STAT TEXT")]

    draw.rectangle(frame, fill=(28, 32, 44, 255), outline=accent, width=4)
    if source_image_present:
        draw.rectangle(photo, fill=(59, 64, 79, 255), outline=subtle, width=4)
        draw.text((photo[0] + 18, photo[1] + 16), "SOURCE IMAGE", fill=(252, 248, 242, 255), font=title_font)
    else:
        draw.rectangle(photo, fill=(59, 64, 79, 255), outline=accent, width=5)
        draw.line((photo[0] + 16, photo[1] + 14, photo[2] - 16, photo[3] - 14), fill=accent, width=8)
        draw.line((photo[2] - 16, photo[1] + 14, photo[0] + 16, photo[3] - 14), fill=accent, width=8)
        draw.text((photo[0] + 16, photo[3] + 10), "SOURCE IMAGE NOT PRESENT LOCALLY", fill=(247, 238, 223, 255), font=title_font)

    draw.text(title, variant_id.replace("_", " ").upper(), fill=(250, 248, 244, 255), font=title_font)
    draw.text((title[0], title[1] + 58), spec["visual_direction"], fill=(228, 233, 244, 255), font=body_font)
    draw.text(score, "0 - 0", fill=(252, 252, 252, 255), font=title_font)
    draw.text((score[0], score[1] + 58), "REVIEW ONLY - APQ001 QUARANTINE PROTOTYPE", fill=(252, 252, 252, 255), font=body_font)
    for x, y, text in support:
        draw.text((x, y), text, fill=(205, 211, 224, 255), font=body_font)
    canvas.save(path, "PNG")


def finalize_png(path: Path, fallback_spec: dict[str, Any], source_image_present: bool) -> None:
    if path.exists():
        return
    write_placeholder_png(path, fallback_spec, source_image_present)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render three review-only Blender/APQ composition variants.")
    parser.add_argument("--scene-payload", default="", help="Optional explicit path to the APQ001 scene payload sample.")
    parser.add_argument("--blender-executable", default="", help="Optional Blender executable override.")
    args = parser.parse_args(argv)

    output_dir = resolve_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    scene_payload_path = resolve_scene_payload_path(args.scene_payload or None)
    scene_context = load_scene_context(scene_payload_path)
    source_photo_path = scene_context["source_image_path"]
    variant_specs = build_variant_specs(scene_context)
    runner_path = output_dir / RUNNER_NAME
    write_runner_script(runner_path, variant_specs)

    blender_executable = resolve_blender_executable(args.blender_executable or None)
    blender_version = "unavailable"
    if blender_executable is not None:
        blender_version = probe_blender_version(blender_executable)

    variant_rows: list[dict[str, Any]] = []
    for spec in variant_specs:
        output_png_path = output_dir / spec["output_name"]
        if output_png_path.exists():
            output_png_path.unlink()
        result = None
        if blender_executable is not None and scene_payload_path.exists():
            result = run_blender_render(blender_executable, runner_path, scene_payload_path, spec["variant_id"], output_png_path)
        elif blender_executable is not None and not scene_payload_path.exists():
            result = run_blender_render(blender_executable, runner_path, scene_payload_path, spec["variant_id"], output_png_path)
        if result is None:
            write_placeholder_png(output_png_path, spec, bool(scene_context["source_image_present"]))
            render_exit_code = 0
            render_stdout = ""
            render_stderr = "blender_unavailable_or_skipped"
            texture_status = parse_texture_status(render_stdout, bool(scene_context["source_image_present"]))
        else:
            render_exit_code = int(result.returncode)
            render_stdout = result.stdout
            render_stderr = result.stderr
            texture_status = read_texture_status_file(output_png_path) or parse_texture_status(render_stdout, bool(scene_context["source_image_present"]))
            if render_exit_code != 0 or not output_png_path.exists():
                finalize_png(output_png_path, spec, bool(scene_context["source_image_present"]))
        spec = {
            **spec,
            "output_png_path": output_png_path.as_posix(),
            "render_exit_code": render_exit_code,
            "render_stdout": render_stdout,
            "render_stderr": render_stderr,
            **texture_status,
            "placeholder_used": not bool(texture_status.get("source_image_texture_loaded")),
        }
        variant_rows.append(spec)

    contact_sheet_info = build_contact_sheet(output_dir, variant_rows)
    report_path = output_dir / REPORT_NAME
    intake_path = output_dir / CSV_NAME
    manifest_path = output_dir / MANIFEST_NAME

    manual_rows = build_manual_rows(variant_rows)
    write_csv_file(
        intake_path,
        manual_rows,
        [
            "variant_id",
            "visual_direction",
            "photo_first_strength",
            "score_readability",
            "premium_editorial_feel",
            "burn_in_legibility",
            "operator_decision",
            "operator_notes",
        ],
    )

    manifest = build_manifest(
        blender_executable=blender_executable,
        blender_version=blender_version,
        scene_payload_path=scene_payload_path,
        scene_context=scene_context,
        variant_rows=variant_rows,
        contact_sheet_info=contact_sheet_info,
        report_path=report_path,
        intake_path=intake_path,
        runner_path=runner_path,
    )
    write_json_file(manifest_path, manifest)
    write_text_file(report_path, build_report({**manifest, "source_image_path": source_photo_path.as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
