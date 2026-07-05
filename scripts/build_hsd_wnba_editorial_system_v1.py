from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except Exception:  # pragma: no cover - Pillow is expected locally
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFilter = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


VERSION = "hsd-wnba-editorial-system-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_editorial_system_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_editorial_system_v1"
CANVAS = (1080, 1350)
CONTACT_SHEET = (1080, 1560)
REVIEW_ONLY_BURN_IN = "REVIEW ONLY - WNBA EDITORIAL SYSTEM V1"

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
}

CSV_FIELDS = [
    "route_id",
    "route_name",
    "athlete_name",
    "team_name",
    "source_path",
    "render_path",
    "layout_mode",
    "keep_or_kill",
    "visual_strength",
    "source_fit",
    "recommendation",
    "review_only",
    "artifact_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

SOURCE_SPECS: list[dict[str, Any]] = [
    {
        "route_id": "route_01_jackie_monograph",
        "route_name": "Jackie Monograph",
        "athlete_name": "Jackie Young",
        "team_name": "Las Vegas Aces",
        "source_id": "jackie_young_headshot",
        "source_path": "assets/leagues/wnba/athletes/las_vegas_aces_jackie_young/headshot.png",
        "layout_mode": "monograph_hero",
        "keep_or_kill": "keep",
        "visual_strength": "highest_authority_and_best_APCS039_replacement",
        "source_fit": "strong",
        "recommendation": "carry_forward_baseline",
        "top_color": (10, 11, 16),
        "bottom_color": (32, 11, 16),
        "floor_color": (18, 17, 21),
        "accent_color": (231, 53, 74),
        "headline_lines": ["JACKIE", "YOUNG"],
        "headline_size": 168,
        "headline_box": (48, 150, 880),
        "headline_align": "left",
        "hero_box": (178, 160, 720, 560),
        "hero_scale_bias": 1.04,
        "headline_note": "LAS VEGAS / THE W NEEDS HEAT",
        "deck": "A clean monograph route with real silhouette overlap and no rigid stage.",
        "footer": "premium editorial, not broadcast chrome",
    },
    {
        "route_id": "route_02_kelsey_left_drive",
        "route_name": "Kelsey Left Drive",
        "athlete_name": "Kelsey Mitchell",
        "team_name": "Indiana Fever",
        "source_id": "kelsey_mitchell_headshot",
        "source_path": "assets/leagues/wnba/athletes/indiana_fever_kelsey_mitchell/headshot.png",
        "layout_mode": "left_drive_editorial",
        "keep_or_kill": "kill",
        "visual_strength": "useful_but_less_premium_than_route_01",
        "source_fit": "strong",
        "recommendation": "backup_only",
        "top_color": (14, 18, 34),
        "bottom_color": (46, 35, 14),
        "floor_color": (20, 23, 31),
        "accent_color": (245, 195, 68),
        "headline_lines": ["KELSEY", "MITCHELL"],
        "headline_size": 150,
        "headline_box": (58, 170, 700),
        "headline_align": "left",
        "hero_box": (336, 188, 650, 520),
        "hero_scale_bias": 1.00,
        "headline_note": "INDIANA / LATE RUN PRESSURE",
        "deck": "The strongest alternative if we want more open left-side type and a warmer finish.",
        "footer": "court line remains clean to the bottom edge",
    },
    {
        "route_id": "route_03_sabrina_luxury_cover",
        "route_name": "Sabrina Luxury Cover",
        "athlete_name": "Sabrina Ionescu",
        "team_name": "New York Liberty",
        "source_id": "sabrina_ionescu_headshot",
        "source_path": "assets/leagues/wnba/athletes/new_york_liberty_sabrina_ionescu/headshot.png",
        "layout_mode": "luxury_cover_editorial",
        "keep_or_kill": "keep",
        "visual_strength": "premium_magazine_route_with_best_negative_space",
        "source_fit": "strong",
        "recommendation": "backup_candidate",
        "top_color": (8, 16, 20),
        "bottom_color": (8, 46, 49),
        "floor_color": (13, 21, 24),
        "accent_color": (105, 214, 205),
        "headline_lines": ["NEW", "YORK"],
        "headline_size": 180,
        "headline_box": (48, 122, 930),
        "headline_align": "left",
        "hero_box": (148, 156, 760, 560),
        "hero_scale_bias": 1.02,
        "headline_note": "LIBERTY / CLEANER THAN A TEMPLATE",
        "deck": "A quieter luxury cover route that lets the portrait do the heavy lifting.",
        "footer": "silhouette overlap, no fake UI",
    },
    {
        "route_id": "route_04_rhyne_press_run",
        "route_name": "Rhyne Press Run",
        "athlete_name": "Rhyne Howard",
        "team_name": "Atlanta Dream",
        "source_id": "rhyne_howard_headshot",
        "source_path": "assets/leagues/wnba/athletes/atlanta_dream_rhyne_howard/headshot.png",
        "layout_mode": "press_run_editorial",
        "keep_or_kill": "kill",
        "visual_strength": "good_energy_but_not_as_premium_as_the_top_two",
        "source_fit": "strong",
        "recommendation": "stress_test_only",
        "top_color": (10, 11, 14),
        "bottom_color": (35, 14, 12),
        "floor_color": (20, 17, 17),
        "accent_color": (212, 84, 70),
        "headline_lines": ["PRESS", "RUN"],
        "headline_size": 190,
        "headline_box": (52, 150, 840),
        "headline_align": "left",
        "hero_box": (72, 184, 770, 550),
        "hero_scale_bias": 1.03,
        "headline_note": "ATLANTA / HARD EDGE, NO CHROME",
        "deck": "The most aggressive route in the packet, but still a notch below the premium winners.",
        "footer": "court perspective stays crisp",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return REPO_ROOT


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def git_head_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return ""
    return clean(result.stdout)


def load_font(size: int, *, role: str = "display") -> Any:
    if ImageFont is None:
        raise RuntimeError("Pillow is unavailable")
    role_map = {
        "display": [
            Path("C:/Windows/Fonts/impact.ttf"),
            Path("C:/Windows/Fonts/AGENCYB.TTF"),
            Path("C:/Windows/Fonts/bahnschrift.ttf"),
        ],
        "serif": [
            Path("C:/Windows/Fonts/timesbd.ttf"),
            Path("C:/Windows/Fonts/georgiab.ttf"),
            Path("C:/Windows/Fonts/times.ttf"),
        ],
        "body": [
            Path("C:/Windows/Fonts/RobotoCondensed.ttc"),
            Path("C:/Windows/Fonts/Arialbd.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ],
    }
    candidates = role_map.get(role, role_map["display"])
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(candidate.as_posix(), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def text_size(draw: Any, text: str, font: Any) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
    return int(box[2] - box[0]), int(box[3] - box[1])


def fit_font(draw: Any, lines: list[str], max_width: int, *, start_size: int, role: str = "display") -> Any:
    size = start_size
    sample = [clean(line) for line in lines if clean(line)]
    if not sample:
        return load_font(start_size, role=role)
    while size >= 18:
        font = load_font(size, role=role)
        widest = max((text_size(draw, line, font)[0] for line in sample), default=0)
        if widest <= max_width:
            return font
        size -= 2
    return load_font(18, role=role)


def blend_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def make_vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Any:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is unavailable")
    canvas = Image.new("RGBA", size, (*top, 255))
    draw = ImageDraw.Draw(canvas)
    width, height = size
    for y in range(height):
        t = y / max(1, height - 1)
        draw.line((0, y, width, y), fill=(*blend_color(top, bottom, t), 255))
    return canvas


def add_radial_glow(base: Any, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> Any:
    if Image is None or ImageDraw is None or ImageFilter is None:
        raise RuntimeError("Pillow is unavailable")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(max(8, radius // 3)))
    return Image.alpha_composite(base, overlay)


def add_floor_perspective(base: Any, spec: dict[str, Any]) -> Any:
    if Image is None or ImageDraw is None or ImageFilter is None:
        raise RuntimeError("Pillow is unavailable")
    width, height = base.size
    horizon = int(height * 0.72)
    floor = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(floor)
    floor_fill = (*tuple(spec["floor_color"]), 238)
    draw.polygon([(0, horizon), (width, horizon), (width, height), (0, height)], fill=floor_fill)
    draw.line((0, horizon, width, horizon), fill=(235, 235, 235, 44), width=2)
    vanishing_x = width // 2
    vanishing_y = horizon - 126
    for x in (0.14, 0.32, 0.5, 0.68, 0.86):
        bottom_x = int(width * x)
        draw.line((bottom_x, height, vanishing_x, vanishing_y), fill=(*spec["accent_color"], 58), width=2)
    for frac in (0.14, 0.28, 0.43, 0.61, 0.8):
        y = int(horizon + (height - horizon) * frac)
        left = int(vanishing_x - (width * 0.44) * frac)
        right = int(vanishing_x + (width * 0.44) * frac)
        draw.line((left, y, right, y), fill=(255, 255, 255, 22), width=1)
    floor = floor.filter(ImageFilter.GaussianBlur(0.2))
    return Image.alpha_composite(base, floor)


def paste_cutout(base: Any, source: Any, box: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    if Image is None or ImageOps is None or ImageFilter is None:
        raise RuntimeError("Pillow is unavailable")
    x, y, width, height = box
    fitted = ImageOps.contain(source.convert("RGBA"), (width, height), method=Image.Resampling.LANCZOS)
    if fitted.width > width or fitted.height > height:
        fitted = ImageOps.contain(fitted, (width, height), method=Image.Resampling.LANCZOS)

    alpha = fitted.getchannel("A")
    shadow = Image.new("RGBA", fitted.size, (*accent, 0))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    shadow_offset = (x + 12, y + 18)
    base.alpha_composite(shadow, shadow_offset)

    halo = Image.new("RGBA", fitted.size, (*accent, 0))
    halo.putalpha(alpha)
    halo = halo.filter(ImageFilter.GaussianBlur(28))
    base.alpha_composite(halo, (x - 4, y - 6))

    base.alpha_composite(fitted, (x, y))


def draw_headline(draw: Any, spec: dict[str, Any]) -> None:
    x, y, max_width = spec["headline_box"]
    lines = [clean(line) for line in spec["headline_lines"]]
    font = fit_font(draw, lines, max_width, start_size=int(spec["headline_size"]), role="display")
    line_gap = -12
    cursor_y = y
    for line in lines:
        line_width, line_height = text_size(draw, line, font)
        if spec.get("headline_align") == "center":
            line_x = x + max(0, (max_width - line_width) // 2)
        elif spec.get("headline_align") == "right":
            line_x = x + max_width - line_width
        else:
            line_x = x
        draw.text(
            (line_x, cursor_y),
            line,
            font=font,
            fill=(245, 244, 240, 235),
            stroke_width=6,
            stroke_fill=(8, 8, 10, 220),
        )
        cursor_y += line_height + line_gap


def draw_support_copy(draw: Any, spec: dict[str, Any]) -> None:
    kicker_font = load_font(26, role="serif")
    footer_font = load_font(19, role="body")
    accent = (*spec["accent_color"], 255)
    draw.text((50, 72), "WNBA / REVIEW ONLY", font=footer_font, fill=(232, 235, 241, 190))
    draw.text((50, 104), spec["headline_note"], font=kicker_font, fill=accent, stroke_width=2, stroke_fill=(0, 0, 0, 180))
    body_text = spec["deck"]
    fitted = load_font(24, role="body")
    while True:
        try:
            current_size = int(getattr(fitted, "size", 24))
        except Exception:
            current_size = 24
        if current_size <= 18 or text_size(draw, body_text, fitted)[0] <= 980:
            break
        fitted = load_font(current_size - 1, role="body")
    draw.text((50, 1164), body_text, font=fitted, fill=(228, 231, 237, 210))
    draw.text((50, 1210), spec["footer"], font=footer_font, fill=(200, 206, 216, 175))
    draw.text((50, 1270), REVIEW_ONLY_BURN_IN, font=footer_font, fill=(180, 186, 196, 150))


def render_variant(spec: dict[str, Any], output_path: Path) -> dict[str, Any]:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is unavailable")
    source_path = repo_root() / spec["source_path"]
    if not source_path.exists():
        raise FileNotFoundError(f"Missing local WNBA source asset: {source_path}")
    with Image.open(source_path) as source:
        source_rgba = source.convert("RGBA")

    canvas = make_vertical_gradient(CANVAS, spec["top_color"], spec["bottom_color"])
    canvas = add_radial_glow(canvas, (CANVAS[0] // 2, int(CANVAS[1] * 0.24)), 320, spec["accent_color"], 110)
    canvas = add_radial_glow(canvas, (int(CANVAS[0] * 0.5), int(CANVAS[1] * 0.74)), 260, spec["accent_color"], 70)
    canvas = add_floor_perspective(canvas, spec)

    overlay = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_headline(draw, spec)

    if spec["layout_mode"] == "monograph_hero":
        draw.text((50, 888), "THE W NEEDS HEAT", font=load_font(24, role="serif"), fill=(*spec["accent_color"], 245))
    elif spec["layout_mode"] == "left_drive_editorial":
        draw.text((50, 912), "INSTANT PRESSURE", font=load_font(24, role="serif"), fill=(*spec["accent_color"], 235))
    elif spec["layout_mode"] == "luxury_cover_editorial":
        draw.text((50, 900), "LUXURY COVER CUT", font=load_font(24, role="serif"), fill=(*spec["accent_color"], 235))
    else:
        draw.text((50, 906), "HARD EDGE / NO CHROME", font=load_font(24, role="serif"), fill=(*spec["accent_color"], 235))

    canvas = Image.alpha_composite(canvas, overlay)
    paste_cutout(canvas, source_rgba, tuple(spec["hero_box"]), spec["accent_color"])

    draw = ImageDraw.Draw(canvas)
    draw_support_copy(draw, spec)
    small_font = load_font(18, role="body")
    draw.text((50, 1115), spec["route_name"], font=small_font, fill=(235, 238, 243, 200))
    draw.text((50, 1138), spec["athlete_name"], font=load_font(21, role="serif"), fill=(245, 245, 242, 235))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return {
        "route_id": spec["route_id"],
        "route_name": spec["route_name"],
        "athlete_name": spec["athlete_name"],
        "team_name": spec["team_name"],
        "source_id": spec["source_id"],
        "source_path": source_path.as_posix(),
        "render_path": output_path.as_posix(),
        "dimensions": [CANVAS[0], CANVAS[1]],
        "keep_or_kill": spec["keep_or_kill"],
        "visual_strength": spec["visual_strength"],
        "source_fit": spec["source_fit"],
        "recommendation": spec["recommendation"],
        "layout_mode": spec["layout_mode"],
    }


def build_contact_sheet(rows: list[dict[str, Any]], output_path: Path) -> None:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is unavailable")
    sheet = Image.new("RGBA", CONTACT_SHEET, (8, 10, 14, 255))
    draw = ImageDraw.Draw(sheet)
    margin = 38
    gap = 28
    cell_w = (CONTACT_SHEET[0] - margin * 2 - gap) // 2
    cell_h = (CONTACT_SHEET[1] - 230 - margin * 2 - gap) // 2
    thumb_w = cell_w
    thumb_h = cell_h - 72
    caption_font = load_font(18, role="body")
    title_font = load_font(28, role="display")
    draw.text((margin, 24), "WNBA EDITORIAL SYSTEM / CONTACT SHEET", font=title_font, fill=(244, 245, 247, 245))
    draw.text((margin, 72), "Keep the routes that feel premium. Kill the ones that still smell like scaffolding.", font=caption_font, fill=(196, 201, 210, 215))
    for index, row in enumerate(rows):
        col = index % 2
        row_idx = index // 2
        x = margin + col * (cell_w + gap)
        y = 132 + row_idx * (cell_h + gap)
        with Image.open(row["render_path"]) as image:
            thumb = ImageOps.contain(image.convert("RGBA"), (thumb_w, thumb_h), method=Image.Resampling.LANCZOS)
        card = Image.new("RGBA", (cell_w, cell_h), (18, 20, 28, 255))
        card.alpha_composite(thumb, ((cell_w - thumb.width) // 2, 0))
        card_draw = ImageDraw.Draw(card)
        verdict_fill = (126, 220, 170, 255) if row["keep_or_kill"] == "keep" else (241, 121, 109, 255)
        card_draw.text((14, cell_h - 56), f"{row['route_name']}  -  {row['keep_or_kill'].upper()}", font=caption_font, fill=verdict_fill)
        card_draw.text((14, cell_h - 30), row["athlete_name"], font=caption_font, fill=(230, 233, 239, 210))
        sheet.alpha_composite(card, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def build_packet(*, output_dir: Path | None = None, head_commit: str | None = None) -> dict[str, Any]:
    if Image is None:
        raise RuntimeError("Pillow is required for this packet")
    out_dir = output_dir or resolve_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    routes: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        render_path = out_dir / f"{spec['route_id']}.png"
        routes.append(render_variant(spec, render_path))

    contact_sheet_path = out_dir / "contact_sheet.png"
    build_contact_sheet(routes, contact_sheet_path)

    keep_count = sum(1 for route in routes if route["keep_or_kill"] == "keep")
    kill_count = sum(1 for route in routes if route["keep_or_kill"] == "kill")
    best_route = next((route for route in routes if route["route_id"] == "route_01_jackie_monograph"), routes[0])
    report_lines = [
        "# WNBA Editorial System Review",
        "",
        "Blunt verdict: APCS039 is dead as a visual family and was not used.",
        "The quarantine action-photo folder in this checkout is empty, so the system is anchored on local WNBA headshots instead.",
        "",
        "## Keep",
        f"- {routes[0]['route_id']}: {routes[0]['route_name']}",
        f"- {routes[2]['route_id']}: {routes[2]['route_name']}",
        "",
        "## Kill",
        f"- {routes[1]['route_id']}: {routes[1]['route_name']}",
        f"- {routes[3]['route_id']}: {routes[3]['route_name']}",
        "",
        "## Recommendation",
        "- Carry forward `route_01_jackie_monograph` as the baseline.",
        "- `route_03_sabrina_luxury_cover` is the only backup route that feels premium enough to stay in the conversation.",
        "- If a real local WNBA review-only action asset shows up later, rerun the system on that source instead of forcing APCS039 back to life.",
        "",
        "## Source Notes",
        "- Source assets used: local WNBA headshots only.",
        "- No downloads, approvals, marker writes, or publish-state changes were performed.",
    ]
    report_path = out_dir / "visual_report.md"
    write_text(report_path, "\n".join(report_lines))

    intake_rows = [
        {
            "route_id": row["route_id"],
            "route_name": row["route_name"],
            "athlete_name": row["athlete_name"],
            "team_name": row["team_name"],
            "source_path": row["source_path"],
            "render_path": row["render_path"],
            "layout_mode": row["layout_mode"],
            "keep_or_kill": row["keep_or_kill"],
            "visual_strength": row["visual_strength"],
            "source_fit": row["source_fit"],
            "recommendation": row["recommendation"],
            "review_only": "true",
            "artifact_only": "true",
            "asset_downloads": "false",
            "approval_state_change": "false",
            "publish_ready": "false",
            "publishing": "false",
        }
        for row in routes
    ]
    csv_path = out_dir / "manual_visual_review_intake.csv"
    write_csv(csv_path, intake_rows, CSV_FIELDS)

    manifest = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "repo_head": head_commit or git_head_commit(),
        "status": "wnba_editorial_system_ready",
        "review_only": True,
        "artifact_only": True,
        "source_mode": "local_wnba_headshots_only",
        "source_policy_note": "quarantine_action_photo_folder_was_empty_in_this_checkout",
        "route_count": len(routes),
        "keep_count": keep_count,
        "kill_count": kill_count,
        "best_route_id": best_route["route_id"],
        "best_route_name": best_route["route_name"],
        "best_source_id": best_route["source_id"],
        "best_source_path": best_route["source_path"],
        "recommendation": "carry_forward_route_01_jackie_monograph",
        "routes": routes,
        "outputs": {
            "manifest": (out_dir / "manifest.json").as_posix(),
            "visual_report": report_path.as_posix(),
            "manual_visual_review_intake": csv_path.as_posix(),
            "contact_sheet": contact_sheet_path.as_posix(),
        },
        "guardrails": FALSE_GUARDRAILS,
    }
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the WNBA editorial system review-only packet.")
    parser.add_argument("--output-dir", default="", help="Optional output directory override.")
    parser.add_argument("--head-commit", default="", help="Optional repo commit to record in the manifest.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_packet(
        output_dir=Path(args.output_dir) if args.output_dir else None,
        head_commit=args.head_commit or None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
