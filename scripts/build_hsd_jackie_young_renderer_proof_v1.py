from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts import build_hsd_apcs114_visual_upgrade_v2 as base


VERSION = "hsd-jackie-young-renderer-proof-v1-review-only"
GENERATED_BY = "scripts/build_hsd_jackie_young_renderer_proof_v1.py"
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
DEFAULT_SOURCE_IMAGE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/las_vegas_aces/jackie_young/apcs039_operator_review.jpg"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/jackie_young_renderer_proof_v1")
RUNNER_NAME = "jackie_young_renderer_proof_runner.py"
SPECS_NAME = "jackie_young_renderer_proof_specs.json"
CONTACT_SHEET_NAME = "contact_sheet.png"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "visual_proof_report.md"
CSV_NAME = "manual_visual_review_intake.csv"
BURN_IN = "REVIEW ONLY - JACKIE YOUNG QUARANTINE PROOF"

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
            "proof_id": "proof_01_vertical_score_anchor",
            "proof_name": "Vertical Score Anchor",
            "filename": "proof_01_vertical_score_anchor.png",
            "texture_filename": "proof_01_vertical_score_anchor_texture.png",
            "crop_strategy": "apcs039_vertical_full_body_4x5_score_plane",
            "crop_center": [0.50, 0.52],
            "crop_zoom": 1.0,
            "texture_grade": {
                "brightness": 0.78,
                "contrast": 1.26,
                "color": 0.95,
                "sharpness": 1.08,
                "vignette": 0.32,
                "top_scrim": 0.18,
            },
            "composition_treatment_mode": "photo_plus_dark_score_plane_blender_depth",
            "visual_strength": "strongest_jackie_young_social_proof",
            "known_limit": "review_only_official_gallery_candidate_not_asset_approved",
            "accent_color": [200, 25, 50],
            "background_top": [6, 8, 13],
            "background_bottom": [14, 16, 22],
            "headline": "FINAL",
            "subhead": "ACES PRESSURE",
            "score": "YOUNG",
            "caption": "APCS039 / REVIEW ONLY",
            "photo_location": [-1.32, 0.48, 0.16],
            "photo_scale": [1.42, 1.0, 2.62],
            "photo_rotation_z": -0.5,
            "text_anchor_x": 0.92,
        },
        {
            "proof_id": "proof_02_clean_full_body_read",
            "proof_name": "Clean Full-Body Read",
            "filename": "proof_02_clean_full_body_read.png",
            "texture_filename": "proof_02_clean_full_body_read_texture.png",
            "crop_strategy": "apcs039_full_body_negative_space_read",
            "crop_center": [0.50, 0.50],
            "crop_zoom": 1.0,
            "texture_grade": {
                "brightness": 0.80,
                "contrast": 1.20,
                "color": 0.94,
                "sharpness": 1.08,
                "vignette": 0.28,
                "top_scrim": 0.12,
            },
            "composition_treatment_mode": "layered_news_card_photo_plane",
            "visual_strength": "best_source_read_and_crop_check",
            "known_limit": "official_gallery_download_only_no_asset_approval",
            "accent_color": [216, 190, 126],
            "background_top": [9, 11, 18],
            "background_bottom": [18, 19, 25],
            "headline": "SOURCE READ",
            "subhead": "FULL-BODY 4:5",
            "score": "APCS039",
            "caption": "NO APPROVAL / REVIEW ONLY",
            "photo_location": [1.18, 0.54, 0.05],
            "photo_scale": [1.32, 1.0, 2.58],
            "photo_rotation_z": 0.4,
            "text_anchor_x": -2.62,
        },
        {
            "proof_id": "proof_03_magazine_spotlight_shell",
            "proof_name": "Magazine Spotlight Shell",
            "filename": "proof_03_magazine_spotlight_shell.png",
            "texture_filename": "proof_03_magazine_spotlight_shell_texture.png",
            "crop_strategy": "apcs039_tighter_action_spotlight_shell",
            "crop_center": [0.50, 0.48],
            "crop_zoom": 1.08,
            "texture_grade": {
                "brightness": 0.76,
                "contrast": 1.30,
                "color": 0.92,
                "sharpness": 1.10,
                "vignette": 0.38,
                "top_scrim": 0.18,
            },
            "composition_treatment_mode": "minimal_magazine_stat_shell",
            "visual_strength": "premium_minimal_spotlight_route",
            "known_limit": "needs_manual_identity_and_crop_confirmation_before_any_asset_review",
            "accent_color": [182, 32, 46],
            "background_top": [7, 9, 15],
            "background_bottom": [15, 18, 26],
            "headline": "0",
            "subhead": "JACKIE YOUNG",
            "score": "OFFICIAL GALLERY TEST",
            "caption": "APCS039 / QUARANTINE",
            "photo_location": [1.26, 0.50, 0.02],
            "photo_scale": [1.30, 1.0, 2.54],
            "photo_rotation_z": -0.2,
            "text_anchor_x": -2.58,
        },
    ]


def prepare_specs(output_dir: Path, source_image: Path) -> list[dict[str, Any]]:
    texture_dir = output_dir / "review_only_render_textures"
    specs: list[dict[str, Any]] = []
    for spec in build_proof_specs():
        row = dict(spec)
        output_png = output_dir / row["filename"]
        texture_path = texture_dir / row["texture_filename"]
        texture_info = base.crop_texture(
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
                "source_image_sha256": base.sha256_file(source_image) if source_image.exists() else "",
                "texture_info": texture_info,
                "canvas": dict(base.CANVAS),
                "review_only": True,
                "burn_in_text": BURN_IN,
            }
        )
        specs.append(row)
    return specs


def build_runner_script() -> str:
    return (
        base.build_runner_script()
        .replace("APCS114UV", "JackieYoungUV")
        .replace("APCS114TextureMat", "JackieYoungTextureMat")
        .replace("REVIEW ONLY - APCS114 VISUAL UPGRADE", BURN_IN)
    )


def write_specs_file(output_dir: Path, specs: list[dict[str, Any]]) -> Path:
    return write_json(output_dir / SPECS_NAME, {"version": VERSION, "proof_specs": specs}, sort_keys=True)


def create_contact_sheet(output_dir: Path, specs: list[dict[str, Any]]) -> Path:
    if base.Image is None or base.ImageDraw is None:
        raise RuntimeError("Pillow is required to build the Jackie Young contact sheet")
    thumbs: list[Any] = []
    resample = getattr(getattr(base.Image, "Resampling", base.Image), "LANCZOS", 1)
    for spec in specs:
        with base.Image.open(spec["output_png_path"]) as image:
            thumbs.append(image.convert("RGB").resize((320, 400), resample))
    sheet = base.Image.new("RGB", (1080, 562), (12, 15, 21))
    draw = base.ImageDraw.Draw(sheet)
    font = base.load_font(22, bold=True)
    small = base.load_font(16, bold=False)
    draw.text((34, 24), "JACKIE YOUNG REVIEW-ONLY RENDERER PROOF V1", fill=(244, 246, 250), font=font)
    draw.text((34, 55), "APCS039 lead. Quarantine proof only. No asset approval. No publish-ready state.", fill=(190, 198, 210), font=small)
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
    return f"""# Jackie Young Renderer Proof V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet turns the Mike-approved Jackie Young APCS039 review-only quarantine candidate into three Blender-backed 1080x1350 proof renders. It is not asset approval, renderer approval, publish-ready output, or publishing.

## Visual Read

- Strongest proof target: `proof_01_vertical_score_anchor`, because APCS039 is already vertical and gives the best solo-player 4:5 foundation found so far.
- Source-read proof: `proof_02_clean_full_body_read`, because it checks whether the downloaded official-gallery image can survive a conservative 4:5 crop without hiding the body/action read.
- Riskier premium route: `proof_03_magazine_spotlight_shell`, because it tests whether a tighter editorial spotlight can carry the subject without falling back into APQ-style crop damage.
- Known limit: APCS039 is a review-only official-gallery candidate. Download approval is not asset approval.

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
    blender_version = base.probe_blender_version(blender_executable)
    render_result = base.RenderResult(99, "", "blender_executable_missing")
    if blender_executable:
        render_result = base.run_blender_render(blender_executable, runner_file, specs_file)

    missing_outputs = [spec["output_png_path"] for spec in specs if not Path(spec["output_png_path"]).exists()]
    traceback_present = "Traceback" in f"{render_result.stdout}\n{render_result.stderr}"
    if render_result.returncode != 0 or missing_outputs or traceback_present:
        status = "jackie_young_renderer_proof_blocked_render_failed"
        contact_sheet_path = ""
    else:
        status = "jackie_young_renderer_proof_ready"
        contact_sheet_path = create_contact_sheet(output_dir, specs).as_posix()

    proof_rows: list[dict[str, Any]] = []
    for spec in specs:
        output_png = Path(spec["output_png_path"])
        proof_rows.append(
            {
                "proof_id": spec["proof_id"],
                "proof_name": spec["proof_name"],
                "output_png_path": output_png.as_posix(),
                "dimensions": base.png_dimensions(output_png) if output_png.exists() else [],
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
        "source_image_sha256": base.sha256_file(source_image) if source_image.exists() else "",
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
        "strongest_proof_id": "proof_01_vertical_score_anchor",
        "review_only": True,
        "approved_marker_writes": False,
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    write_csv(output_dir / CSV_NAME, build_manual_rows(specs), CSV_FIELDS)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Jackie Young review-only Blender renderer proof packet.")
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
    return 0 if manifest["status"] == "jackie_young_renderer_proof_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
