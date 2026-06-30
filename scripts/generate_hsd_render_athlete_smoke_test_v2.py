from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_json

VERSION = "hsd-render-athlete-smoke-test-v2-p0-prototype"

os.environ.setdefault("HSD_RUN_OUTPUT_DIR", str(Path("outputs/local/latest/files").resolve()))

QUARANTINE_PHOTO = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg"
)
OUT_IMG = output_path("apq001_p0_prototype_draft.png")
OUT_JSON = output_path("apq001_p0_prototype_manifest.json")

COLOR_INK = (248, 250, 255, 255)
COLOR_DEEP = (13, 20, 35, 255)
COLOR_GOLD = (232, 186, 72, 255)
COLOR_MUTED = (93, 102, 118, 255)


def safe_font(font_path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def cover_resize(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    target_w, target_h = target_size
    scale = max(target_w / image.width, target_h / image.height)
    new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def main() -> int:
    print(f"[{VERSION}] starting review-only smoke test render")

    if not QUARANTINE_PHOTO.exists():
        print(f"Error: target review-only candidate missing at {QUARANTINE_PHOTO}")
        return 1

    try:
        source_image = Image.open(QUARANTINE_PHOTO).convert("RGBA")
        canvas = cover_resize(source_image, (1080, 1350))
    except Exception as exc:
        print(f"Fallback warning: image open failed ({exc}); using procedural canvas")
        canvas = Image.new("RGBA", (1080, 1350), COLOR_DEEP)

    draw = ImageDraw.Draw(canvas, "RGBA")

    font_display = safe_font("C:/Windows/Fonts/impact.ttf", 50)
    font_score = safe_font("C:/Windows/Fonts/impact.ttf", 124)
    font_context = safe_font("C:/Windows/Fonts/arialbd.ttf", 24)

    draw.text((60, 90), "WNBA FINAL", font=font_context, fill=COLOR_GOLD)
    draw.text(
        (60, 130),
        "FEVER TOPS SKY IN RECAP DRAFT",
        font=font_display,
        fill=COLOR_INK,
        stroke_width=2,
        stroke_fill=(0, 0, 0, 255),
    )

    wash_layer = Image.new("RGBA", (1080, 1350), (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash_layer, "RGBA")
    wash_draw.rectangle((60, 400, 1020, 680), fill=(0, 0, 0, 110))
    canvas.alpha_composite(wash_layer)

    draw.text((120, 440), "IND", font=font_display, fill=COLOR_INK)
    draw.text((360, 400), "84", font=font_score, fill=COLOR_INK, stroke_width=1, stroke_fill=(0, 0, 0, 255))
    draw.text((620, 440), "CHI", font=font_display, fill=COLOR_MUTED)
    draw.text((820, 400), "76", font=font_score, fill=COLOR_MUTED, stroke_width=1, stroke_fill=(0, 0, 0, 255))

    draw.line((60, 1100, 1020, 1100), fill=(248, 250, 255, 180), width=2)
    draw.text((60, 1120), "MATCHUP TAKEAWAY", font=font_context, fill=COLOR_GOLD)
    draw.text(
        (60, 1160),
        "Kelsey Mitchell led Indiana with 24 points shot from the field.",
        font=font_context,
        fill=COLOR_INK,
    )

    draw.rectangle((0, 1310, 1080, 1350), fill=(190, 39, 54, 238))
    draw.text((60, 1318), "REVIEW DRAFT ONLY - HUMAN CHECK REQUIRED", font=font_context, fill=COLOR_INK)

    OUT_IMG.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_IMG, "PNG")
    print(f"Layout preview saved: {OUT_IMG}")

    manifest_payload = {
        "version": VERSION,
        "source_asset_id": "APQ001",
        "resolved_critique_themes": [
            "score_rail_typography",
            "story_title_safe_zone",
            "open_caption_rail",
        ],
        "canvas_profile": "1080x1350_ig_feed_4x5",
        "guardrails": {
            "review_only": True,
            "publish_ready": False,
            "approval_state_change": False,
            "move_files": False,
        },
    }
    write_json(OUT_JSON, manifest_payload, sort_keys=True)
    print(f"Manifest metrics saved: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
