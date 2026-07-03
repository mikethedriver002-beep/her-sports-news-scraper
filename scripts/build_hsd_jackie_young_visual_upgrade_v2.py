from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts import build_hsd_jackie_young_renderer_proof_v1 as v1


VERSION = "hsd-jackie-young-visual-upgrade-v2-review-only"
GENERATED_BY = "scripts/build_hsd_jackie_young_visual_upgrade_v2.py"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
DEFAULT_SOURCE_IMAGE = v1.DEFAULT_SOURCE_IMAGE
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/jackie_young_visual_upgrade_v2")
RUNNER_NAME = "jackie_young_visual_upgrade_v2_runner.py"
SPECS_NAME = "jackie_young_visual_upgrade_v2_specs.json"
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_upgrade_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
BURN_IN = "REVIEW ONLY - JACKIE YOUNG VISUAL UPGRADE V2"

FALSE_GUARDRAILS = dict(v1.FALSE_GUARDRAILS)
CSV_FIELDS = list(v1.CSV_FIELDS)


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


def build_proof_specs() -> list[dict[str, Any]]:
    return [
        {
            "proof_id": "upgrade_01_score_command",
            "proof_name": "Score Command",
            "filename": "upgrade_01_score_command.png",
            "texture_filename": "upgrade_01_score_command_texture.png",
            "crop_strategy": "apcs039_vertical_full_body_score_command_safe_type",
            "crop_center": [0.50, 0.515],
            "crop_zoom": 1.0,
            "texture_grade": {
                "brightness": 0.72,
                "contrast": 1.38,
                "color": 0.98,
                "sharpness": 1.12,
                "vignette": 0.42,
                "top_scrim": 0.22,
            },
            "composition_treatment_mode": "photo_plus_dark_score_plane_blender_depth",
            "visual_strength": "strongest_premium_score_anchor",
            "known_limit": "review_only_official_gallery_candidate_not_asset_approved",
            "accent_color": [214, 32, 54],
            "background_top": [4, 6, 11],
            "background_bottom": [10, 12, 18],
            "headline": "FINAL",
            "subhead": "LAS VEGAS",
            "score": "YOUNG",
            "caption": "APCS039 / QUARANTINE",
            "photo_location": [-1.42, 0.52, 0.12],
            "photo_scale": [1.52, 1.0, 2.76],
            "photo_rotation_z": -0.9,
            "text_anchor_x": 0.94,
        },
        {
            "proof_id": "upgrade_02_cover_spotlight",
            "proof_name": "Cover Spotlight",
            "filename": "upgrade_02_cover_spotlight.png",
            "texture_filename": "upgrade_02_cover_spotlight_texture.png",
            "crop_strategy": "apcs039_cover_spotlight_full_body",
            "crop_center": [0.50, 0.49],
            "crop_zoom": 1.04,
            "texture_grade": {
                "brightness": 0.74,
                "contrast": 1.34,
                "color": 0.94,
                "sharpness": 1.12,
                "vignette": 0.44,
                "top_scrim": 0.20,
            },
            "composition_treatment_mode": "minimal_magazine_stat_shell",
            "visual_strength": "best_premium_cover_route",
            "known_limit": "needs_manual_crop_confirmation_before_any_asset_review",
            "accent_color": [220, 190, 132],
            "background_top": [6, 8, 13],
            "background_bottom": [13, 16, 24],
            "headline": "0",
            "subhead": "JACKIE YOUNG",
            "score": "FULL-BODY SOURCE",
            "caption": "REVIEW ONLY / APCS039",
            "photo_location": [1.22, 0.52, 0.04],
            "photo_scale": [1.34, 1.0, 2.62],
            "photo_rotation_z": -0.3,
            "text_anchor_x": -2.58,
        },
        {
            "proof_id": "upgrade_03_wire_story_depth",
            "proof_name": "Wire Story Depth",
            "filename": "upgrade_03_wire_story_depth.png",
            "texture_filename": "upgrade_03_wire_story_depth_texture.png",
            "crop_strategy": "apcs039_story_depth_action_read",
            "crop_center": [0.50, 0.505],
            "crop_zoom": 1.0,
            "texture_grade": {
                "brightness": 0.76,
                "contrast": 1.24,
                "color": 0.92,
                "sharpness": 1.08,
                "vignette": 0.34,
                "top_scrim": 0.16,
            },
            "composition_treatment_mode": "layered_news_card_photo_plane",
            "visual_strength": "best_story_card_route",
            "known_limit": "review_only_download_candidate_not_publish_ready",
            "accent_color": [212, 56, 72],
            "background_top": [8, 10, 16],
            "background_bottom": [17, 18, 25],
            "headline": "ACES RUN",
            "subhead": "ACTION FRAME",
            "score": "APCS039",
            "caption": "NO APPROVAL / REVIEW ONLY",
            "photo_location": [1.18, 0.56, 0.08],
            "photo_scale": [1.34, 1.0, 2.68],
            "photo_rotation_z": 0.7,
            "text_anchor_x": -2.62,
        },
    ]


def prepare_specs(output_dir: Path, source_image: Path) -> list[dict[str, Any]]:
    texture_dir = output_dir / "review_only_render_textures"
    specs: list[dict[str, Any]] = []
    for spec in build_proof_specs():
        row = dict(spec)
        output_png = output_dir / row["filename"]
        texture_path = texture_dir / row["texture_filename"]
        texture_info = v1.base.crop_texture(
            source_image,
            texture_path,
            list(row["crop_center"]),
            float(row["crop_zoom"]),
            dict(row.get("texture_grade", {})),
        )
        row.update(
            {
                "output_png_path": output_png.as_posix(),
                "texture_path": texture_path.as_posix(),
                "source_image_path": source_image.as_posix(),
                "source_image_present": source_image.exists(),
                "source_image_sha256": v1.base.sha256_file(source_image) if source_image.exists() else "",
                "texture_info": texture_info,
                "canvas": dict(v1.base.CANVAS),
                "review_only": True,
                "burn_in_text": BURN_IN,
            }
        )
        specs.append(row)
    return specs


def build_runner_script() -> str:
    return v1.build_runner_script().replace(
        "REVIEW ONLY - JACKIE YOUNG QUARANTINE PROOF",
        BURN_IN,
    )


def write_specs_file(output_dir: Path, specs: list[dict[str, Any]]) -> Path:
    return write_json(output_dir / SPECS_NAME, {"version": VERSION, "proof_specs": specs}, sort_keys=True)


def create_contact_sheet(output_dir: Path, specs: list[dict[str, Any]]) -> Path:
    if v1.base.Image is None or v1.base.ImageDraw is None:
        raise RuntimeError("Pillow is required to build the Jackie Young v2 contact sheet")
    thumbs: list[Any] = []
    resample = getattr(getattr(v1.base.Image, "Resampling", v1.base.Image), "LANCZOS", 1)
    for spec in specs:
        with v1.base.Image.open(spec["output_png_path"]) as image:
            thumbs.append(image.convert("RGB").resize((320, 400), resample))
    sheet = v1.base.Image.new("RGB", (1080, 562), (10, 13, 19))
    draw = v1.base.ImageDraw.Draw(sheet)
    font = v1.base.load_font(22, bold=True)
    small = v1.base.load_font(16, bold=False)
    draw.text((34, 24), "JACKIE YOUNG REVIEW-ONLY VISUAL UPGRADE V2", fill=(244, 246, 250), font=font)
    draw.text((34, 55), "APCS039 lead. Stronger Blender proof routes. No asset approval. No publish-ready state.", fill=(190, 198, 210), font=small)
    x_positions = [36, 380, 724]
    for x, spec, thumb in zip(x_positions, specs, thumbs):
        sheet.paste(thumb, (x, 104))
        draw.text((x, 516), spec["proof_name"], fill=(238, 239, 242), font=small)
    path = output_dir / CONTACT_SHEET_NAME
    sheet.save(path, "PNG")
    return path


def build_report(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            f"| `{row['proof_id']}` | {row['proof_name']} | {row['crop_strategy']} | {row['composition_treatment_mode']} | {row['known_limit']} |"
            for row in manifest["proof_rows"]
        ]
    )
    return f"""# Jackie Young Visual Upgrade V2

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet pushes the APCS039 Jackie Young review-only quarantine candidate beyond the first proof with stronger contrast, safer typography, and more deliberate Blender-backed social treatments. It is not asset approval, renderer approval, publish-ready output, or publishing.

## Visual Read

- Lead route: `upgrade_01_score_command`, designed to keep APCS039's solo full-body read while making the right-side type plane feel more intentional.
- Premium alternate: `upgrade_02_cover_spotlight`, a cleaner magazine route that should be compared directly with the v1 score anchor.
- Story route: `upgrade_03_wire_story_depth`, a lower-risk news card proof for source/context checking.
- Known limit: APCS039 remains a review-only official-gallery candidate. Download approval is not asset approval.

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
    blender_version = v1.base.probe_blender_version(blender_executable)
    render_result = v1.base.RenderResult(99, "", "blender_executable_missing")
    if blender_executable:
        render_result = v1.base.run_blender_render(blender_executable, runner_file, specs_file)

    missing_outputs = [spec["output_png_path"] for spec in specs if not Path(spec["output_png_path"]).exists()]
    traceback_present = "Traceback" in f"{render_result.stdout}\n{render_result.stderr}"
    if render_result.returncode != 0 or missing_outputs or traceback_present:
        status = "jackie_young_visual_upgrade_blocked_render_failed"
        contact_sheet_path = ""
    else:
        status = "jackie_young_visual_upgrade_ready"
        contact_sheet_path = create_contact_sheet(output_dir, specs).as_posix()

    proof_rows: list[dict[str, Any]] = []
    for spec in specs:
        output_png = Path(spec["output_png_path"])
        proof_rows.append(
            {
                "proof_id": spec["proof_id"],
                "proof_name": spec["proof_name"],
                "output_png_path": output_png.as_posix(),
                "dimensions": v1.base.png_dimensions(output_png) if output_png.exists() else [],
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
        "source_image_sha256": v1.base.sha256_file(source_image) if source_image.exists() else "",
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
        "known_source_limit": "APCS039 is a review-only official-gallery candidate; download approval is not asset approval.",
        "strongest_proof_id": "upgrade_01_score_command",
        "review_only": True,
        "approved_marker_writes": False,
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    write_csv(output_dir / CSV_NAME, build_manual_rows(specs), CSV_FIELDS)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Jackie Young review-only Blender visual upgrade v2 packet.")
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
    return 0 if manifest["status"] == "jackie_young_visual_upgrade_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
