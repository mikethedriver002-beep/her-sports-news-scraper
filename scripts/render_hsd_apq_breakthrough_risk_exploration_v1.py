from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir

try:
    from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
except Exception:  # pragma: no cover - runtime fallback
    Image = None  # type: ignore[assignment]
    ImageChops = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageEnhance = None  # type: ignore[assignment]
    ImageFilter = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-apq-breakthrough-risk-exploration-v1-review-only"
GENERATED_BY = "scripts/render_hsd_apq_breakthrough_risk_exploration_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/apq_breakthrough_risk_exploration_v1")
DEFAULT_SOURCE_IMAGE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg"
)
DEFAULT_BASELINE_IMAGE = Path("outputs/local/latest/files/blender_apq_composition_variants/variant_03_clean_editorial.png")
DEFAULT_BLENDER_EXECUTABLE = Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "report.md"
CONTACT_SHEET_NAME = "contact_sheet.png"
CSV_NAME = "manual_review_intake.csv"
OUTPUT_SIZE = (1080, 1350)
TEXT_COLOR = (246, 247, 249, 255)
SUBTLE_TEXT = (193, 198, 207, 255)
WATERMARK_TEXT = "REVIEW ONLY - APQ001 QUARANTINE BREAKTHROUGH"

FALSE_GUARDRAILS = {
    "approval_state_change": False,
    "asset_approved": False,
    "asset_downloads": False,
    "artifact_only": True,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "image_edits": False,
    "move_files": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "renderer_behavior_change": False,
    "production_renderer_replacement": False,
    "review_only": True,
    "source_auto_enabled": False,
}

VARIANT_SPECS: list[dict[str, Any]] = [
    {
        "variant_id": "experiment_01_jersey_texture_poster",
        "output_name": "experiment_01_jersey_texture_poster.png",
        "title": "Jersey Texture Poster",
        "visual_direction": "body-and-jersey-as-hero poster; the crop limitation becomes the point instead of the failure",
        "crop_box": (0.17, 0.36, 0.78, 1.0),
        "premium_viability": "yes_conditional",
        "meaningfully_better_than_v03": True,
        "rank": 1,
        "face_dependency_risk": "low",
        "blunt_verdict": "Strongest direction. The number and wordmark carry the frame, so the bad portrait crop stops being the center of attention.",
    },
    {
        "variant_id": "experiment_02_score_hero_atmosphere",
        "output_name": "experiment_02_score_hero_atmosphere.png",
        "title": "Score Hero Atmosphere",
        "visual_direction": "score-led poster with APQ001 reduced to atmosphere plus one sharp texture strip",
        "crop_box": (0.22, 0.28, 0.72, 1.0),
        "premium_viability": "borderline",
        "meaningfully_better_than_v03": True,
        "rank": 2,
        "face_dependency_risk": "low",
        "blunt_verdict": "More premium than v03, but it succeeds because the score takes over rather than because the photo itself becomes great.",
    },
    {
        "variant_id": "experiment_03_double_exposure_scrim",
        "output_name": "experiment_03_double_exposure_scrim.png",
        "title": "Double Exposure Scrim",
        "visual_direction": "shadow-heavy editorial treatment with APQ001 used as layered material rather than a portrait",
        "crop_box": (0.24, 0.24, 0.76, 0.95),
        "premium_viability": "maybe_but_soft",
        "meaningfully_better_than_v03": False,
        "rank": 3,
        "face_dependency_risk": "medium",
        "blunt_verdict": "Interesting, but it still reads like an elegant workaround. The composition gets moodier without fully becoming premium.",
    },
    {
        "variant_id": "experiment_04_material_plane_scene",
        "output_name": "experiment_04_material_plane_scene.png",
        "title": "Material Plane Scene",
        "visual_direction": "the wide photo becomes a floating scene object instead of a forced 4:5 portrait",
        "crop_box": (0.14, 0.16, 0.86, 0.96),
        "premium_viability": "no_wait_for_better_source",
        "meaningfully_better_than_v03": False,
        "rank": 4,
        "face_dependency_risk": "low",
        "blunt_verdict": "Conceptually honest, but the photo still lacks the drama to carry a premium scene object without stronger source material.",
    },
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.is_absolute() else repo_root() / candidate
    run_root = run_output_dir()
    return run_root if run_root is not None else repo_root() / DEFAULT_OUTPUT_DIR


def resolve_input_path(raw: str | None, default_rel: Path) -> Path:
    if raw:
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate
        return repo_root() / candidate
    return repo_root() / default_rel


def resolve_blender_executable(raw: str | None = None) -> Path | None:
    candidate = Path(raw) if raw else DEFAULT_BLENDER_EXECUTABLE
    return candidate if candidate.exists() else None


def probe_blender_version(blender_executable: Path | None) -> str:
    if blender_executable is None:
        return "unavailable"
    completed = subprocess.run(
        [str(blender_executable), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    first_line = (completed.stdout or completed.stderr).splitlines()
    return first_line[0].strip() if first_line else "unavailable"


def load_font(size: int, *, bold: bool = False):
    if ImageFont is None:
        raise RuntimeError("Pillow is unavailable")
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf") if bold else Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf") if bold else Path("C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def rounded_mask(size: tuple[int, int], radius: int) -> Any:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Any:
    base = Image.new("RGBA", size, top + (255,))
    draw = ImageDraw.Draw(base)
    for y in range(size[1]):
        mix = y / max(1, size[1] - 1)
        color = tuple(int(top[i] * (1 - mix) + bottom[i] * mix) for i in range(3))
        draw.line((0, y, size[0], y), fill=color + (255,))
    return base


def draw_text(
    canvas: Any,
    xy: tuple[int, int],
    text: str,
    *,
    size: int,
    fill: tuple[int, int, int, int] = TEXT_COLOR,
    bold: bool = False,
    spacing: int = 4,
    anchor: str | None = None,
) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.multiline_text(xy, text, font=load_font(size, bold=bold), fill=fill, spacing=spacing, anchor=anchor)


def fit_region(image: Any, box: tuple[float, float, float, float], size: tuple[int, int]) -> Any:
    width, height = image.size
    left = int(width * box[0])
    top = int(height * box[1])
    right = int(width * box[2])
    bottom = int(height * box[3])
    cropped = image.crop((left, top, right, bottom))
    return ImageOps.fit(cropped, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)).convert("RGBA")


def fit_full(image: Any, *, centering: tuple[float, float]) -> Any:
    return ImageOps.fit(image, OUTPUT_SIZE, method=Image.Resampling.LANCZOS, centering=centering).convert("RGBA")


def add_footer(canvas: Any, label: str) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = canvas.size
    draw.line((72, height - 162, width - 72, height - 162), fill=(255, 255, 255, 68), width=1)
    draw.text((72, height - 132), label.upper(), font=load_font(22, bold=True), fill=(245, 246, 248, 245))
    draw.text(
        (72, height - 92),
        "Premium review-only APQ study. No approvals, no downloads, no publish-ready state.",
        font=load_font(20, bold=False),
        fill=(204, 209, 218, 220),
    )
    draw.text((72, height - 48), WATERMARK_TEXT, font=load_font(18, bold=True), fill=(255, 255, 255, 110))
    canvas.alpha_composite(overlay)


def add_header(canvas: Any, eyebrow: str, headline: str, subhead: str) -> None:
    draw_text(canvas, (72, 64), eyebrow, size=20, fill=(207, 211, 220, 225), bold=True)
    draw_text(canvas, (72, 94), headline, size=64, bold=True)
    draw_text(canvas, (72, 206), subhead, size=28, fill=(213, 218, 227, 240))


def add_shadowed_card(canvas: Any, card: Any, xy: tuple[int, int], radius: int = 36, *, rotate: float = 0.0) -> None:
    framed = Image.new("RGBA", card.size, (0, 0, 0, 0))
    mask = rounded_mask(card.size, radius)
    framed.paste(card, (0, 0), mask)
    if rotate:
        framed = framed.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=True)
        mask = mask.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=True)
    shadow = Image.new("RGBA", framed.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 180), (0, 0), mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow, (xy[0] + 18, xy[1] + 22))
    canvas.alpha_composite(framed, xy)


def add_edge_fade(image: Any, *, reverse: bool = False) -> Any:
    fade = Image.new("L", image.size, 255)
    draw = ImageDraw.Draw(fade)
    for x in range(image.size[0]):
        mix = x / max(1, image.size[0] - 1)
        alpha = int(255 * (mix if reverse else 1 - mix))
        draw.line((x, 0, x, image.size[1]), fill=alpha)
    output = image.copy()
    output.putalpha(fade)
    return output


def add_review_band(canvas: Any, text: str, *, x: int, y: int, width: int) -> None:
    band = Image.new("RGBA", (width, 108), (22, 26, 36, 188))
    draw = ImageDraw.Draw(band)
    draw.rounded_rectangle((0, 0, width - 1, 107), radius=28, outline=(255, 255, 255, 36), width=1)
    draw.text((28, 20), text, font=load_font(24, bold=True), fill=(248, 248, 249, 245))
    canvas.alpha_composite(band, (x, y))


def render_experiment_01(source: Any, spec: dict[str, Any]) -> Any:
    canvas = vertical_gradient(OUTPUT_SIZE, (10, 13, 22), (31, 18, 22))
    bg = fit_full(source, centering=(0.60, 0.52)).filter(ImageFilter.GaussianBlur(22))
    bg = ImageEnhance.Brightness(bg).enhance(0.42)
    canvas = Image.blend(canvas, bg, 0.42)

    detail = fit_region(source, spec["crop_box"], (780, 1140))
    detail = ImageEnhance.Contrast(detail).enhance(1.16)
    detail = ImageEnhance.Sharpness(detail).enhance(1.18)
    detail = add_edge_fade(detail, reverse=True)
    canvas.alpha_composite(detail, (336, 120))

    overlay = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.text((68, 390), "22", font=load_font(332, bold=True), fill=(247, 191, 63, 96))
    draw.rectangle((72, 274, 78, 774), fill=(247, 191, 63, 255))
    canvas.alpha_composite(overlay)

    add_header(canvas, "APQ BREAKTHROUGH TEST 01", "Jersey\nTexture", "Use the number and wordmark as the premium focal signal.")
    add_review_band(canvas, "FINAL 82 - 79", x=72, y=740, width=356)
    draw_text(canvas, (72, 876), "The face is allowed to fall back.\nThe jersey carries the frame.", size=26, fill=(218, 223, 231, 230))
    add_footer(canvas, spec["title"])
    return canvas


def render_experiment_02(source: Any, spec: dict[str, Any]) -> Any:
    canvas = fit_full(source, centering=(0.66, 0.50)).filter(ImageFilter.GaussianBlur(18))
    canvas = ImageEnhance.Brightness(canvas).enhance(0.34)
    navy = Image.new("RGBA", OUTPUT_SIZE, (12, 16, 26, 184))
    canvas.alpha_composite(navy)

    strip = fit_region(source, spec["crop_box"], (318, 1088))
    strip = ImageEnhance.Contrast(strip).enhance(1.08)
    add_shadowed_card(canvas, strip, (690, 134), radius=24)

    draw = ImageDraw.Draw(canvas)
    draw.line((628, 150, 628, 1186), fill=(247, 194, 96, 255), width=3)
    add_header(canvas, "APQ BREAKTHROUGH TEST 02", "Score\nAtmosphere", "Treat APQ001 as mood plus one sharp stripe of material.")
    draw_text(canvas, (72, 368), "82", size=214, bold=True, fill=(252, 244, 229, 255))
    draw_text(canvas, (292, 388), "-", size=112, bold=True, fill=(241, 243, 247, 225))
    draw_text(canvas, (364, 368), "79", size=214, bold=True, fill=(241, 243, 247, 235))
    draw_text(canvas, (76, 606), "The score is the hero.\nThe photo only supplies live-sport texture.", size=28, fill=(213, 218, 228, 234))
    add_footer(canvas, spec["title"])
    return canvas


def render_experiment_03(source: Any, spec: dict[str, Any]) -> Any:
    base = fit_full(source, centering=(0.63, 0.44)).convert("L").convert("RGBA")
    tinted = ImageOps.colorize(base.convert("L"), black="#0b1018", white="#b0c0d8").convert("RGBA")
    tinted = ImageEnhance.Brightness(tinted).enhance(0.72)
    canvas = tinted.filter(ImageFilter.GaussianBlur(4))

    shadow = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 96))
    canvas.alpha_composite(shadow)

    detail = fit_region(source, spec["crop_box"], (520, 860))
    detail = ImageEnhance.Color(detail).enhance(0.82)
    detail = ImageEnhance.Contrast(detail).enhance(1.10)
    detail.putalpha(214)
    add_shadowed_card(canvas, detail, (484, 266), radius=34, rotate=-6.0)

    haze = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    haze_draw.ellipse((446, 178, 1110, 954), fill=(246, 194, 89, 28))
    haze_draw.rectangle((72, 308, 454, 910), fill=(9, 12, 20, 108))
    canvas.alpha_composite(haze)

    add_header(canvas, "APQ BREAKTHROUGH TEST 03", "Double\nExposure", "Atmosphere improves, but the result still leans workaround.")
    draw_text(canvas, (72, 454), "Shadow and scrim can hide the crop problem,\nbut they do not fully solve the weak source drama.", size=27, fill=(221, 225, 233, 234))
    add_footer(canvas, spec["title"])
    return canvas


def render_experiment_04(source: Any, spec: dict[str, Any]) -> Any:
    canvas = vertical_gradient(OUTPUT_SIZE, (15, 18, 25), (33, 37, 48))
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((688, -80, 1200, 420), fill=(247, 193, 75, 34))
    draw.ellipse((-120, 760, 520, 1440), fill=(132, 48, 62, 28))

    plane = ImageOps.fit(source, (908, 572), method=Image.Resampling.LANCZOS, centering=(0.60, 0.47)).convert("RGBA")
    plane = ImageEnhance.Color(plane).enhance(0.96)
    plane = plane.rotate(-7.5, resample=Image.Resampling.BICUBIC, expand=True)
    add_shadowed_card(canvas, plane, (118, 576), radius=30)

    inset = fit_region(source, spec["crop_box"], (216, 296))
    add_shadowed_card(canvas, inset, (796, 812), radius=26)

    add_header(canvas, "APQ BREAKTHROUGH TEST 04", "Material\nPlane", "Honest idea, but the source still does not feel premium enough on its own.")
    draw_text(canvas, (72, 386), "This treats the image like a design material plane,\nnot a forced portrait crop. The honesty helps.\nThe source quality ceiling still shows.", size=26, fill=(216, 221, 230, 232))
    add_footer(canvas, spec["title"])
    return canvas


def render_variant(source: Any, spec: dict[str, Any]) -> Any:
    if spec["variant_id"] == "experiment_01_jersey_texture_poster":
        return render_experiment_01(source, spec)
    if spec["variant_id"] == "experiment_02_score_hero_atmosphere":
        return render_experiment_02(source, spec)
    if spec["variant_id"] == "experiment_03_double_exposure_scrim":
        return render_experiment_03(source, spec)
    return render_experiment_04(source, spec)


def save_png(path: Path, image: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


def build_contact_sheet(
    packet_dir: Path,
    baseline_path: Path | None,
    baseline_present: bool,
    variant_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    tile_w = 340
    tile_h = 425
    cols = 3
    rows = 2
    canvas = Image.new("RGBA", (cols * 360 + 80, rows * 520 + 128), (18, 22, 31, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 18), "APQ Breakthrough Risk Exploration", font=load_font(22, bold=True), fill=(244, 245, 247, 245))
    draw.text(
        (24, 50),
        "Baseline plus four review-only experiments. The winner should hide the portrait-crop weakness rather than argue with it.",
        font=load_font(18, bold=False),
        fill=(198, 203, 211, 235),
    )

    tiles: list[dict[str, str]] = []
    if baseline_present and baseline_path is not None:
        tiles.append(
            {
                "label": "Baseline v03",
                "subtitle": "Old clean-editorial loop",
                "path": baseline_path.as_posix(),
                "verdict": "Reference only",
            }
        )
    for row in variant_rows:
        tiles.append(
            {
                "label": row["title"],
                "subtitle": row["visual_direction"],
                "path": row["output_path"],
                "verdict": row["blunt_verdict"],
            }
        )

    for index, tile in enumerate(tiles):
        x = 24 + (index % cols) * 360
        y = 92 + (index // cols) * 520
        frame = Image.new("RGBA", (tile_w + 20, tile_h + 88), (24, 29, 41, 255))
        frame_draw = ImageDraw.Draw(frame)
        frame_draw.rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=22, outline=(122, 132, 150, 96), width=1)
        with Image.open(tile["path"]) as opened:
            preview = ImageOps.fit(opened.convert("RGBA"), (tile_w, tile_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        frame.paste(preview, (10, 10))
        frame_draw.text((14, tile_h + 20), tile["label"], font=load_font(18, bold=True), fill=(244, 245, 247, 245))
        frame_draw.text((14, tile_h + 46), tile["subtitle"][:48], font=load_font(15, bold=False), fill=(200, 206, 214, 232))
        frame_draw.text((14, tile_h + 66), tile["verdict"][:72], font=load_font(14, bold=False), fill=(181, 189, 201, 220))
        canvas.alpha_composite(frame, (x, y))

    output_path = packet_dir / CONTACT_SHEET_NAME
    save_png(output_path, canvas)
    return {"path": output_path.as_posix(), "source_count": len(tiles), "size": list(canvas.size)}


def build_review_rows(variant_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in variant_rows:
        rows.append(
            {
                "variant_id": row["variant_id"],
                "title": row["title"],
                "premium_viability": row["premium_viability"],
                "meaningfully_better_than_v03": str(row["meaningfully_better_than_v03"]).lower(),
                "face_dependency_risk": row["face_dependency_risk"],
                "operator_decision": "",
                "operator_notes": "",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_report(
    manifest: dict[str, Any],
    variant_rows: list[dict[str, Any]],
    *,
    baseline_present: bool,
    source_size: tuple[int, int],
) -> str:
    strongest = variant_rows[0]
    verdict = "Conditional yes" if strongest["meaningfully_better_than_v03"] else "No"
    continue_call = (
        "Continue risky APQ treatment only in the jersey-texture direction."
        if strongest["variant_id"] == "experiment_01_jersey_texture_poster"
        else "Wait for a better source crop and route energy to non-APQ archetypes."
    )

    lines = [
        "# APQ Breakthrough Risk Exploration",
        "",
        f"Status: `{manifest['status']}`",
        f"Version: `{manifest['version']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "This run is review-only, quarantine-only, and artifact-only. It does not approve assets, download anything, change the production renderer, or create publish-ready outputs.",
        "",
        "## Source Reality",
        "",
        f"- APQ001 source image size: `{source_size[0]}x{source_size[1]}`",
        f"- Baseline v03 available for comparison: `{str(baseline_present).lower()}`",
        "- The source works better as jersey/body texture than as a premium face-led 4:5 portrait crop.",
        "- The portrait problem is structural: the wide frame gives us smile and shoulders, but not enough vertical authority for a clean editorial social crop.",
        "",
        "## Direct Answers",
        "",
        f"- Can APQ001 produce a visually premium social artifact without a better source crop? `{verdict}`. Only if we stop treating APQ001 like a face-safe portrait and let the jersey/number carry the design.",
        f"- Which risky direction is strongest? `{strongest['title']}`.",
        f"- Is it meaningfully better than the old v03 clean-editorial loop? `{str(strongest['meaningfully_better_than_v03']).lower()}`. The best experiment wins by avoiding the crop fight instead of exposing it.",
        f"- What should the conductor do next? `{continue_call}`",
        "",
        "## Variant Readout",
        "",
    ]
    for row in variant_rows:
        lines.extend(
            [
                f"### {row['title']}",
                "",
                f"- Direction: {row['visual_direction']}",
                f"- Premium viability: `{row['premium_viability']}`",
                f"- Meaningfully better than v03: `{str(row['meaningfully_better_than_v03']).lower()}`",
                f"- Face dependency risk: `{row['face_dependency_risk']}`",
                f"- Blunt verdict: {row['blunt_verdict']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommendation",
            "",
            "Do not spend more time trying to force APQ001 into a clean editorial portrait crop. If APQ must stay active before a better source arrives, keep it in the jersey-texture poster lane and treat everything else as evidence that the source ceiling is real.",
            "",
        ]
    )
    return "\n".join(lines)


def build_manifest(
    *,
    output_dir: Path,
    source_path: Path,
    baseline_path: Path | None,
    blender_executable: Path | None,
    blender_version: str,
    source_size: tuple[int, int],
    baseline_present: bool,
    variant_rows: list[dict[str, Any]],
    contact_sheet_info: dict[str, Any],
    review_csv_path: Path,
) -> dict[str, Any]:
    strongest = variant_rows[0]
    overall_answer = "conditional_yes" if strongest["meaningfully_better_than_v03"] else "wait_for_better_source"
    next_action = (
        "continue_risky_apq_treatment_with_jersey_texture_only"
        if strongest["variant_id"] == "experiment_01_jersey_texture_poster"
        else "route_effort_to_non_apq_archetypes"
    )
    payload = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "apq_breakthrough_risk_exploration_ready",
        "output_dir": output_dir.as_posix(),
        "source_image_path": source_path.as_posix(),
        "source_image_size": {"width": source_size[0], "height": source_size[1]},
        "baseline_image_path": baseline_path.as_posix() if baseline_path else "",
        "baseline_present": baseline_present,
        "blender_executable": blender_executable.as_posix() if blender_executable else "",
        "blender_version": blender_version,
        "renderer_strategy": "pil_only_review_only_breakthrough_prototypes_after_blender_behavior_inspection",
        "variant_count": len(variant_rows),
        "strongest_direction_id": strongest["variant_id"],
        "strongest_direction_title": strongest["title"],
        "overall_answer": overall_answer,
        "meaningfully_better_than_v03": strongest["meaningfully_better_than_v03"],
        "next_action": next_action,
        "review_csv_path": review_csv_path.as_posix(),
        "contact_sheet_path": contact_sheet_info["path"],
        "contact_sheet_source_count": contact_sheet_info["source_count"],
        "contact_sheet_size": contact_sheet_info["size"],
        "variant_rows": variant_rows,
    }
    payload.update(FALSE_GUARDRAILS)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render review-only APQ breakthrough exploration experiments.")
    parser.add_argument("--source-image", default="", help="Absolute or repo-relative APQ001 review-only source image path.")
    parser.add_argument("--baseline-image", default="", help="Optional baseline v03 PNG for contact-sheet comparison.")
    parser.add_argument("--output-dir", default="", help="Explicit run-scoped output directory override.")
    parser.add_argument("--blender-executable", default="", help="Optional Blender executable override for version probing only.")
    args = parser.parse_args(argv)

    if Image is None or ImageDraw is None or ImageOps is None:
        raise RuntimeError("Pillow is required for APQ breakthrough exploration rendering.")

    output_dir = resolve_output_dir(args.output_dir or None)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_path = resolve_input_path(args.source_image or None, DEFAULT_SOURCE_IMAGE)
    baseline_path = resolve_input_path(args.baseline_image or None, DEFAULT_BASELINE_IMAGE)
    baseline_present = baseline_path.exists()

    blender_executable = resolve_blender_executable(args.blender_executable or None)
    blender_version = probe_blender_version(blender_executable)

    with Image.open(source_path) as source_opened:
        source = source_opened.convert("RGB")
        source_size = source.size

        variant_rows: list[dict[str, Any]] = []
        for spec in sorted(VARIANT_SPECS, key=lambda row: int(row["rank"])):
            rendered = render_variant(source, spec)
            output_path = output_dir / spec["output_name"]
            save_png(output_path, rendered)
            variant_rows.append(
                {
                    "variant_id": spec["variant_id"],
                    "title": spec["title"],
                    "visual_direction": spec["visual_direction"],
                    "output_path": output_path.as_posix(),
                    "output_name": spec["output_name"],
                    "canvas": {"width": OUTPUT_SIZE[0], "height": OUTPUT_SIZE[1]},
                    "premium_viability": spec["premium_viability"],
                    "meaningfully_better_than_v03": spec["meaningfully_better_than_v03"],
                    "face_dependency_risk": spec["face_dependency_risk"],
                    "rank": spec["rank"],
                    "blunt_verdict": spec["blunt_verdict"],
                }
            )

    review_rows = build_review_rows(variant_rows)
    review_csv_path = output_dir / CSV_NAME
    write_csv(review_csv_path, review_rows)
    contact_sheet_info = build_contact_sheet(output_dir, baseline_path if baseline_present else None, baseline_present, variant_rows)
    manifest = build_manifest(
        output_dir=output_dir,
        source_path=source_path,
        baseline_path=baseline_path if baseline_present else None,
        blender_executable=blender_executable,
        blender_version=blender_version,
        source_size=source_size,
        baseline_present=baseline_present,
        variant_rows=variant_rows,
        contact_sheet_info=contact_sheet_info,
        review_csv_path=review_csv_path,
    )
    report = build_report(manifest, variant_rows, baseline_present=baseline_present, source_size=source_size)

    (output_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / REPORT_NAME).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
