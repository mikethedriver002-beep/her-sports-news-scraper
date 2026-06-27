from __future__ import annotations

import base64
import json
import os
import re
import shutil
import csv
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from hsd_run_io import input_path, output_path, write_json, write_text

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat
except Exception:  # pragma: no cover - validated by runtime status report
    Image = None
    ImageDraw = None
    ImageFilter = None
    ImageFont = None
    ImageStat = None


VERSION = "hsd-manual-review-renderer-v1.22.0-premium-editorial-backgrounds"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
OUT_DIR = output_path(HANDOFF_DIR_NAME)
OUT_PREVIEW = OUT_DIR / "draft_preview.png"
OUT_REVIEW_DRAFTS = OUT_DIR / "review_drafts"
OUT_REPORT = output_path("manual_review_renderer_report.md")
OUT_MANIFEST = output_path("manual_review_renderer_manifest.json")
PROJECT_ROOT = Path(__file__).resolve().parent
REFERENCE_PACK_ID = "templates_hsd_20260625"
REFERENCE_PACK_MANIFEST = PROJECT_ROOT / "config" / "graphics" / "v4" / "template_reference_packs_v1.json"
REFERENCE_SPEC_ROOT = PROJECT_ROOT / "config" / "graphics" / "v4" / "reference_specs" / REFERENCE_PACK_ID
REFERENCE_PUBLIC_ROOT = PROJECT_ROOT / "assets" / "graphics" / "v4" / "approved" / "public_mockups"
REFERENCE_LAYOUT_ROOT = PROJECT_ROOT / "assets" / "graphics" / "v4" / "approved" / "layout_references"
REFERENCE_BRAND_ROOT = PROJECT_ROOT / "assets" / "graphics" / "v4" / "approved" / "brand"
TEAM_ALIASES_CSV = PROJECT_ROOT / "data" / "asset_registry" / "wnba" / "team_aliases.csv"
TEAM_LOGOS_CSV = PROJECT_ROOT / "data" / "asset_registry" / "wnba" / "team_logos.csv"
TEAM_COLORS_CSV = PROJECT_ROOT / "data" / "asset_registry" / "wnba" / "teams.csv"
WNBA_ATHLETE_ROOT = PROJECT_ROOT / "assets" / "leagues" / "wnba" / "athletes"
ATHLETE_PHOTO_ONBOARDING_METADATA = "athlete_photo_onboarding/athlete_photo_onboarding_metadata.json"
ATHLETE_IDENTITY_AUDIT = "data/asset_registry/wnba/athlete_identity_audit.json"
ATHLETE_IDENTITY_RESOLUTION_INBOX = "operator/inbox/wnba_athlete_identity_resolution.csv"
RENDER_BACKGROUND_STYLE = "hsd_premium_sports_editorial_v4_dimensional"
RENDER_BACKGROUND_CUES = (
    "dimensional_hsd_ink_field,quiet_score_zones,subtle_stadium_light_sweep,"
    "team_accent_rim_light,soft_editorial_rule_grid,restrained_halftone_noise,"
    "review_only_brand_rails,generated_preview_qa"
)

FORMAT_SPECS = [
    {"format_id": "ig_feed_4x5", "filename": "draft_preview_ig_feed.png", "width": 1080, "height": 1350, "primary": True},
    {"format_id": "ig_story_9x16", "filename": "draft_preview_story.png", "width": 1080, "height": 1920, "primary": False},
    {"format_id": "square_feed_1x1", "filename": "draft_preview_square.png", "width": 1080, "height": 1080, "primary": False},
]

REFERENCE_FINAL_SCORE_FORMATS = {
    "ig_feed_4x5": {
        "reference_family_key": "wnba_final_score_tonight",
        "reference_template_id": "hsd_game_recap_final_score_a",
        "reference_spec_path": "config/graphics/v4/reference_specs/templates_hsd_20260625/wnba_final_score_tonight/hsd_game_recap_final_score_a.json",
        "reference_public_mockup_path": "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/01_game_recap_final_score_variant_A_public.png",
        "reference_layout_path": "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/02_game_recap_final_score_variant_A_layout_reference.png",
        "reference_exact_format_match": True,
        "reference_derivation": "exact_imported_reference_spec",
    },
    "ig_story_9x16": {
        "reference_family_key": "wnba_final_score_tonight",
        "reference_template_id": "hsd_game_recap_final_score_c_story",
        "reference_spec_path": "config/graphics/v4/reference_specs/templates_hsd_20260625/wnba_final_score_tonight/hsd_game_recap_final_score_c_story.json",
        "reference_public_mockup_path": "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/05_game_recap_final_score_variant_C_story_public.png",
        "reference_layout_path": "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/06_game_recap_final_score_variant_C_story_layout_reference.png",
        "reference_exact_format_match": True,
        "reference_derivation": "exact_imported_reference_spec",
    },
    "square_feed_1x1": {
        "reference_family_key": "wnba_final_score_tonight",
        "reference_template_id": "hsd_game_recap_final_score_a",
        "reference_spec_path": "config/graphics/v4/reference_specs/templates_hsd_20260625/wnba_final_score_tonight/hsd_game_recap_final_score_a.json",
        "reference_public_mockup_path": "assets/graphics/v4/approved/public_mockups/wnba_final_score_tonight/01_game_recap_final_score_variant_A_public.png",
        "reference_layout_path": "assets/graphics/v4/approved/layout_references/wnba_final_score_tonight/02_game_recap_final_score_variant_A_layout_reference.png",
        "reference_exact_format_match": False,
        "reference_derivation": "square_review_draft_derived_from_imported_4x5_layout",
    },
}

PALETTE = {
    "ink": (248, 250, 255),
    "deep": (13, 20, 35),
    "navy": (22, 48, 79),
    "blue": (35, 92, 148),
    "cyan": (54, 183, 196),
    "gold": (232, 186, 72),
    "paper": (248, 246, 241),
    "paper_2": (255, 255, 255),
    "line": (218, 222, 230),
    "muted": (93, 102, 118),
    "red": (190, 39, 54),
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split()).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def slug(value: Any) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", clean(value).lower())).strip("_")


def repo_root() -> Path:
    return Path.cwd().resolve()


def project_path(raw: Any) -> Path:
    path = Path(clean(raw))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def relative_project_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        return path.as_posix()


def read_json_file(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def input_handoff_candidates() -> List[Path]:
    candidates: List[Path] = []
    run_dir = os.environ.get("HSD_RUN_OUTPUT_DIR", "").strip()
    if run_dir:
        candidates.append(Path(run_dir) / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / HANDOFF_DIR_NAME)
    candidates.append(repo_root() / "outputs" / "local" / "latest" / "files" / HANDOFF_DIR_NAME)
    return candidates


def find_handoff_dir() -> Path | None:
    for candidate in input_handoff_candidates():
        if (candidate / "handoff_manifest.json").exists():
            return candidate
    return None


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


_ATHLETE_PHOTO_ONBOARDING_CACHE: Dict[str, Any] | None = None
_ATHLETE_IDENTITY_AUDIT_CACHE: Dict[str, Any] | None = None
_ATHLETE_IDENTITY_RESOLUTION_CACHE: List[Dict[str, str]] | None = None


def athlete_photo_onboarding_metadata() -> Dict[str, Dict[str, str]]:
    global _ATHLETE_PHOTO_ONBOARDING_CACHE
    if _ATHLETE_PHOTO_ONBOARDING_CACHE is None:
        path = input_path(ATHLETE_PHOTO_ONBOARDING_METADATA)
        payload = read_json(path) if path.exists() else {}
        athletes = payload.get("athletes") if isinstance(payload.get("athletes"), dict) else {}
        _ATHLETE_PHOTO_ONBOARDING_CACHE = {
            clean(key): value
            for key, value in athletes.items()
            if isinstance(value, dict)
        }
    return _ATHLETE_PHOTO_ONBOARDING_CACHE


def athlete_photo_onboarding_row(athlete_id: str, source_headshot_path: str) -> Dict[str, str]:
    row = athlete_photo_onboarding_metadata().get(clean(athlete_id), {})
    if not row:
        return {}
    if clean(row.get("source_headshot_path")) != clean(source_headshot_path):
        return {}
    if clean(row.get("variant_status")) != "review_variant_ready":
        return {}
    if clean(row.get("approval_scope")) != "review_only_derivative_from_approved_headshot":
        return {}
    return {str(key): clean(value) for key, value in row.items()}


def athlete_identity_audit_issues() -> Dict[str, List[Dict[str, str]]]:
    global _ATHLETE_IDENTITY_AUDIT_CACHE
    if _ATHLETE_IDENTITY_AUDIT_CACHE is None:
        path = input_path(ATHLETE_IDENTITY_AUDIT)
        payload = read_json(path) if path.exists() else {}
        issues = payload.get("issues") if isinstance(payload.get("issues"), list) else []
        grouped: Dict[str, List[Dict[str, str]]] = {}
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            athlete_id = clean(issue.get("athlete_id"))
            if athlete_id:
                grouped.setdefault(athlete_id, []).append({str(key): clean(value) for key, value in issue.items()})
        _ATHLETE_IDENTITY_AUDIT_CACHE = grouped
    return _ATHLETE_IDENTITY_AUDIT_CACHE


def athlete_identity_resolution_rows() -> List[Dict[str, str]]:
    global _ATHLETE_IDENTITY_RESOLUTION_CACHE
    if _ATHLETE_IDENTITY_RESOLUTION_CACHE is None:
        path = input_path(ATHLETE_IDENTITY_RESOLUTION_INBOX)
        _ATHLETE_IDENTITY_RESOLUTION_CACHE = read_csv(path) if path.exists() else []
    return _ATHLETE_IDENTITY_RESOLUTION_CACHE


def guardrail_false(row: Dict[str, str], field: str) -> bool:
    return clean(row.get(field)).lower() in {"", "0", "false", "no", "n"}


def athlete_identity_resolution(athlete_id: str, asset_path: str, provider_player_id: str) -> Dict[str, str]:
    matches = [
        row for row in athlete_identity_resolution_rows()
        if clean(row.get("athlete_id")) == clean(athlete_id)
    ]
    if asset_path:
        exact = [row for row in matches if clean(row.get("asset_path")) in {"", clean(asset_path)}]
        if exact:
            matches = exact
    if provider_player_id:
        exact_provider = [
            row for row in matches
            if clean(row.get("provider_player_id")) in {"", clean(provider_player_id)}
            or clean(row.get("backfill_provider_player_id")) in {"", clean(provider_player_id)}
        ]
        if exact_provider:
            matches = exact_provider
    if not matches:
        return {"resolution_status": "identity_resolution_missing"}

    row = matches[-1]
    decision = clean(row.get("operator_decision"))
    status = clean(row.get("issue_resolution_status"))
    evidence = clean(row.get("approved_source_url"))
    verified_identity = clean(row.get("identity_verified")).lower() == "yes"
    verified_provider = clean(row.get("provider_player_id_verified")).lower() == "yes" or bool(clean(row.get("backfill_provider_player_id")))
    named_operator = bool(clean(row.get("operator_name")))
    reviewed_at = bool(clean(row.get("reviewed_at_local")))
    notes = bool(clean(row.get("operator_notes")))
    guardrails_ok = all(guardrail_false(row, field) for field in ["publish_ready", "auto_approval", "auto_publish", "move_files", "paid_apis"])
    eligible = (
        decision == "identity_verified_approved_for_review_renders"
        and status in {"resolved", "closed_with_evidence", "identity_verified"}
        and verified_identity
        and verified_provider
        and bool(evidence)
        and named_operator
        and reviewed_at
        and notes
        and guardrails_ok
    )
    return {
        "resolution_status": "identity_resolution_cleared_for_review_renders" if eligible else "identity_resolution_not_cleared",
        "resolution_decision": decision,
        "issue_resolution_status": status,
        "resolution_evidence_url": evidence,
        "resolution_operator": clean(row.get("operator_name")),
        "resolution_reviewed_at_local": clean(row.get("reviewed_at_local")),
        "resolution_notes": clean(row.get("operator_notes")),
        "resolution_provider_player_id": clean(row.get("backfill_provider_player_id")) or clean(row.get("provider_player_id")),
        "resolution_source_file": ATHLETE_IDENTITY_RESOLUTION_INBOX,
    }


def athlete_identity_gate(
    athlete_id: str,
    *,
    asset_path: str,
    provider_player_id: str,
    marker_payload: Dict[str, Any],
) -> Dict[str, Any]:
    issues = athlete_identity_audit_issues().get(clean(athlete_id), [])
    high = [row for row in issues if clean(row.get("severity")) in {"critical", "high"}]
    codes = sorted({clean(row.get("issue_code")) for row in issues if clean(row.get("issue_code"))})
    resolution = athlete_identity_resolution(athlete_id, asset_path, provider_player_id)
    marker_default = clean(marker_payload.get("decision_source")) == "default"
    if (high or marker_default) and clean(resolution.get("resolution_status")) != "identity_resolution_cleared_for_review_renders":
        reason = "Identity audit has high-risk issue(s)." if high else "Approval marker uses default provenance."
        return {
            "status": "hold",
            "identity_review_status": "hold_identity_resolution_required",
            "identity_issue_count": str(len(issues) + (1 if marker_default and not issues else 0)),
            "identity_high_issue_count": str(len(high) + (1 if marker_default and not high else 0)),
            "identity_issue_codes": "|".join(codes + (["default_marker_provenance"] if marker_default and "default_marker_provenance" not in codes else [])),
            "identity_resolution_status": clean(resolution.get("resolution_status")),
            "identity_resolution_decision": clean(resolution.get("resolution_decision")),
            "identity_resolution_source_file": ATHLETE_IDENTITY_RESOLUTION_INBOX,
            "identity_resolution_evidence_url": clean(resolution.get("resolution_evidence_url")),
            "blocker": f"{reason} Add a source-backed row to {ATHLETE_IDENTITY_RESOLUTION_INBOX} before photo-first renderer use.",
        }
    return {
        "status": "clear",
        "identity_review_status": clean(resolution.get("resolution_status")) or ("identity_audit_clear_or_not_run" if not issues else "identity_resolution_cleared_for_review_renders"),
        "identity_issue_count": str(len(issues)),
        "identity_high_issue_count": str(len(high)),
        "identity_issue_codes": "|".join(codes),
        "identity_resolution_status": clean(resolution.get("resolution_status")),
        "identity_resolution_decision": clean(resolution.get("resolution_decision")),
        "identity_resolution_source_file": clean(resolution.get("resolution_source_file")),
        "identity_resolution_evidence_url": clean(resolution.get("resolution_evidence_url")),
        "identity_resolution_operator": clean(resolution.get("resolution_operator")),
        "identity_resolution_reviewed_at_local": clean(resolution.get("resolution_reviewed_at_local")),
    }


def read_csv(path: Path) -> List[Dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def copy_handoff_to_output(src: Path) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dest = OUT_DIR / item.name
        if item.resolve() == dest.resolve():
            continue
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


REFERENCE_FONT_CACHE: Dict[Tuple[str, int], Any] = {}


def font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def reference_font(role: str, size: int):
    if ImageFont is None:
        return None
    key = (role, size)
    if key in REFERENCE_FONT_CACHE:
        return REFERENCE_FONT_CACHE[key]
    candidates = {
        "display": [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialnb.ttf",
            "C:/Windows/Fonts/bahnschrift.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ],
        "score": [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialnb.ttf",
            "C:/Windows/Fonts/seguisb.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "context": [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/bahnschrift.ttf",
        ],
        "body": [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
    }
    for raw in candidates.get(role, candidates["body"]):
        try:
            path = Path(raw)
            if path.exists():
                REFERENCE_FONT_CACHE[key] = ImageFont.truetype(path.as_posix(), size)
                return REFERENCE_FONT_CACHE[key]
        except Exception:
            continue
    REFERENCE_FONT_CACHE[key] = font(size, role != "body")
    return REFERENCE_FONT_CACHE[key]


def resample_filter() -> Any:
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)


def text_size(draw: Any, text: str, fnt: Any) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), clean(text), font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def texture_patch(base: tuple[int, int, int], size: tuple[int, int], seed: int) -> Any:
    width, height = max(1, size[0]), max(1, size[1])
    randomizer = random.Random(seed)
    small = Image.new("RGB", (max(8, width // 7), max(8, height // 7)))
    pixels = []
    for _ in range(small.width * small.height):
        delta = randomizer.randint(-24, 24)
        pixels.append(tuple(max(0, min(255, channel + delta)) for channel in base))
    patch = small.resize((width, height), resample_filter())
    if ImageFilter is not None:
        patch = patch.filter(ImageFilter.GaussianBlur(0.35))
    return patch.convert("RGBA")


def rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(color[0]))),
        max(0, min(255, int(color[1]))),
        max(0, min(255, int(color[2]))),
    )


def hex_to_rgb(value: Any) -> tuple[int, int, int] | None:
    text = clean(value).lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", text):
        return None
    return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))


def logo_sampled_accent(logo: Any, fallback: tuple[int, int, int], fallback_source: str = "") -> tuple[tuple[int, int, int], str]:
    fallback_label = clean(fallback_source) or "fallback_hsd_accent"
    if logo is None:
        return fallback, f"{fallback_label}_no_logo_image"
    try:
        sample = logo.convert("RGBA")
        sample.thumbnail((96, 96), resample_filter())
        buckets: Dict[tuple[int, int, int], int] = {}
        for r, g, b, a in sample.getdata():
            if a < 64:
                continue
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            saturation = max(r, g, b) - min(r, g, b)
            if luma < 45 or luma > 238 or saturation < 24:
                continue
            bucket = (int(round(r / 24) * 24), int(round(g / 24) * 24), int(round(b / 24) * 24))
            score = 1 + int(saturation * 1.8) + (28 if 72 <= luma <= 205 else 0)
            buckets[bucket] = buckets.get(bucket, 0) + score
        if not buckets:
            return fallback, f"{fallback_label}_logo_no_distinct_color"
        color = max(buckets.items(), key=lambda item: item[1])[0]
        return tuple(max(35, min(232, channel)) for channel in color), "sampled_from_local_logo_review_asset"
    except Exception:
        return fallback, f"{fallback_label}_logo_sample_failed"


def logo_approval_cue(result: Dict[str, Any]) -> str:
    status = clean(result.get("status"))
    if status == "approved_logo":
        return "APPROVED LOGO"
    if "missing" in status:
        return "LOGO MISSING"
    return "LOGO REVIEW"


def enrich_logo_result(result: Dict[str, Any], fallback: tuple[int, int, int], fallback_source: str = "") -> Dict[str, Any]:
    accent, source = logo_sampled_accent(result.get("image"), fallback, fallback_source)
    result["team_accent_rgb"] = accent
    result["team_accent_hex"] = rgb_to_hex(accent)
    result["team_accent_source"] = source
    result["logo_approval_cue"] = logo_approval_cue(result)
    result["logo_review_required"] = result.get("approved") is not True
    return result


def draw_right_text(draw: Any, right: int, y: int, text: str, fnt: Any, fill: tuple[int, int, int]) -> None:
    width, _ = text_size(draw, text, fnt)
    draw.text((right - width, y), text, font=fnt, fill=fill)


def draw_rounded(draw: Any, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None, width: int = 1) -> None:
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    else:  # pragma: no cover - Pillow fallback
        draw.rectangle(box, fill=fill, outline=outline, width=width)


def draw_chip(draw: Any, x: int, y: int, label: str, fill: tuple[int, int, int], text_fill: tuple[int, int, int], size: int = 22) -> int:
    fnt = font(size, True)
    text_w, text_h = text_size(draw, label, fnt)
    pad_x = 18
    pad_y = 9
    draw_rounded(draw, (x, y, x + text_w + pad_x * 2, y + text_h + pad_y * 2), 8, fill)
    draw.text((x + pad_x, y + pad_y - 1), label, font=fnt, fill=text_fill)
    return x + text_w + pad_x * 2 + 10


def wrap_text(draw: Any, text: str, fnt: Any, max_width: int, max_lines: int) -> List[str]:
    words = clean(text).split()
    lines: List[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=fnt)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = trial
            continue
        lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if words and len(lines) == max_lines:
        consumed = " ".join(lines).split()
        if len(consumed) < len(words):
            lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def draw_text_block(draw: Any, xy: tuple[int, int], text: str, fnt: Any, fill: tuple[int, int, int], max_width: int, max_lines: int, line_gap: int) -> int:
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width, max_lines):
        draw.text((x, y), line, font=fnt, fill=fill)
        bbox = draw.textbbox((x, y), line, font=fnt)
        y = bbox[3] + line_gap
    return y


def choose_template(packet: Dict[str, Any]) -> Dict[str, str]:
    text = " ".join(
        clean(packet.get(key))
        for key in ["template_fit", "title", "copy_headline", "copy_dek", "renderer_family", "template_shape"]
    ).lower()
    if any(token in text for token in ["beat", "defeat", "final", "score", "result"]):
        return {
            "template_id": "hsd_game_recap_final_score_a",
            "template_family": "game_recap_final_score",
            "reference_pack_id": REFERENCE_PACK_ID,
            "reference_family_key": "wnba_final_score_tonight",
            "angle_label": "FINAL",
            "tone": "result",
        }
    if any(token in text for token in ["tonight", "preview", "matchup"]):
        return {
            "template_id": "hsd_matchup_preview_review_v1",
            "template_family": "matchup_preview_card",
            "angle_label": "TONIGHT",
            "tone": "preview",
        }
    return {
        "template_id": "hsd_news_fact_review_v1",
        "template_family": "news_fact_editorial_card",
        "angle_label": "NEWS",
        "tone": "news",
    }


def asset_slots(packet: Dict[str, Any], template: Dict[str, str]) -> List[Dict[str, str]]:
    requirement = clean(packet.get("asset_requirement")) or "No player asset required; use HSD brand treatment and verified source text only."
    asset_cue = clean(packet.get("asset_cue")) or "asset_review_not_required"
    slots = [
        {
            "slot_id": "primary_photo",
            "status": "not_required_for_review_draft" if "no player asset" in requirement.lower() else "operator_asset_review_required",
            "requirement": requirement,
        },
        {
            "slot_id": "brand_treatment",
            "status": "rendered_locally",
            "requirement": "HSD editorial treatment, draft watermark, and source-safe text only.",
        },
        {
            "slot_id": "source_evidence",
            "status": "manual_review_required",
            "requirement": clean(packet.get("source_artifact")) or "Open source proof before approval.",
        },
        {
            "slot_id": "asset_cue",
            "status": asset_cue,
            "requirement": "Asset readiness cue copied into the renderer manifest for operator review.",
        },
    ]
    score = parse_final_score(packet)
    if score and clean(template.get("reference_pack_id")) == REFERENCE_PACK_ID:
        stat_module = select_verified_stat_module(packet, score)
        if clean(stat_module.get("status")) in {"verified_player_stat_module", "verified_supporting_stat_module"}:
            photo = resolve_athlete_photo(
                clean(stat_module.get("player_name")),
                clean(stat_module.get("team")) or clean(score.get("winner")),
            )
            slots[0] = {
                "slot_id": "primary_photo",
                "status": clean(photo.get("status")),
                "requirement": clean(photo.get("requirement")),
                "asset_path": clean(photo.get("asset_path")),
                "approval_marker_path": clean(photo.get("approval_marker_path")),
                "player": clean(photo.get("player_name")),
                "team": clean(photo.get("team")),
                "team_id": clean(photo.get("team_id")),
                "athlete_id": clean(photo.get("athlete_id")),
                "photo_approval_cue": clean(photo.get("photo_approval_cue")),
                "photo_review_required": str(bool(photo.get("photo_review_required"))).lower(),
                "render_method": clean(photo.get("render_method")),
                "blocker": clean(photo.get("blocker")),
                "approval_policy": clean(photo.get("approval_policy")),
                "approved_at_utc": clean(photo.get("approved_at_utc")),
                "review_variant_status": clean(photo.get("review_variant_status")),
                "review_variant_feed_path": clean(photo.get("review_variant_feed_path")),
                "review_variant_story_path": clean(photo.get("review_variant_story_path")),
                "review_variant_square_path": clean(photo.get("review_variant_square_path")),
                "review_variant_metadata_source": clean(photo.get("review_variant_metadata_source")),
                "review_variant_policy": clean(photo.get("review_variant_policy")),
                "review_variant_crop_readiness_score": clean(photo.get("review_variant_crop_readiness_score")),
                "identity_review_status": clean(photo.get("identity_review_status")),
                "identity_issue_count": clean(photo.get("identity_issue_count")),
                "identity_high_issue_count": clean(photo.get("identity_high_issue_count")),
                "identity_issue_codes": clean(photo.get("identity_issue_codes")),
                "identity_resolution_status": clean(photo.get("identity_resolution_status")),
                "identity_resolution_decision": clean(photo.get("identity_resolution_decision")),
                "identity_resolution_source_file": clean(photo.get("identity_resolution_source_file")),
                "identity_resolution_evidence_url": clean(photo.get("identity_resolution_evidence_url")),
            }
        aliases, logos = team_registry()
        for slot_id, team_name in [("primary_team_logo", score.get("winner")), ("secondary_team_logo", score.get("loser"))]:
            fallback, fallback_source = team_registry_accent(
                clean(team_name),
                aliases,
                (247, 203, 84) if slot_id == "primary_team_logo" else (37, 99, 163),
            )
            result = load_team_logo(clean(team_name), aliases, logos)
            enriched = enrich_logo_result(result, fallback, fallback_source)
            status = clean(result.get("status")) or "logo_review_required"
            requirement_note = "Approved WNBA logo slot from Templates-hsd reference pack; do not invent or replace identity."
            if status != "approved_logo":
                requirement_note += " Human review must confirm this logo asset before any later production use."
            slots.append(
                {
                    "slot_id": slot_id,
                    "status": status,
                    "requirement": requirement_note,
                    "asset_path": clean(result.get("path")),
                    "blocker": clean(result.get("blocker")),
                    "render_method": clean(result.get("render_method")),
                    "team": clean(team_name),
                    "team_accent_hex": clean(enriched.get("team_accent_hex")),
                    "team_accent_source": clean(enriched.get("team_accent_source")),
                    "logo_approval_cue": clean(enriched.get("logo_approval_cue")),
                    "logo_review_required": str(bool(enriched.get("logo_review_required"))).lower(),
                }
            )
    return slots


def score_parts(packet: Dict[str, Any]) -> tuple[str, str]:
    headline = clean(packet.get("copy_headline")) or clean(packet.get("title"))
    dek = clean(packet.get("copy_dek"))
    text = f"{headline} {dek}"
    if "," in text and any(char.isdigit() for char in text):
        return headline, dek
    return headline, dek or "Verified update ready for operator review."


def parse_final_score(packet: Dict[str, Any]) -> Dict[str, str]:
    headline = clean(packet.get("copy_headline")) or clean(packet.get("title"))
    dek = clean(packet.get("copy_dek"))
    combined = f"{headline}. {dek}"
    score_match = re.search(r"([A-Z][A-Za-z .'-]+?)\s+(\d{2,3})\s*,\s*([A-Z][A-Za-z .'-]+?)\s+(\d{2,3})", combined)
    if not score_match:
        return {}
    team_a = clean(score_match.group(1))
    score_a = clean(score_match.group(2))
    team_b = clean(score_match.group(3))
    score_b = clean(score_match.group(4))
    try:
        winner = team_a if int(score_a) >= int(score_b) else team_b
        loser = team_b if winner == team_a else team_a
        winner_score = score_a if winner == team_a else score_b
        loser_score = score_b if winner == team_a else score_a
    except Exception:
        winner, loser, winner_score, loser_score = team_a, team_b, score_a, score_b
    verb = "beat"
    headline_match = re.search(r"(.+?)\s+(beat|defeated|tops|over)\s+(.+)", headline, re.IGNORECASE)
    if headline_match:
        winner = clean(headline_match.group(1))
        loser = clean(headline_match.group(3))
        verb = clean(headline_match.group(2)).lower()
    return {
        "winner": winner,
        "loser": loser,
        "winner_score": winner_score,
        "loser_score": loser_score,
        "verb": verb,
    }


def reference_pack_summary() -> Dict[str, Any]:
    manifest = read_json(REFERENCE_PACK_MANIFEST)
    packs = manifest.get("packs") if isinstance(manifest.get("packs"), list) else []
    pack = next((item for item in packs if isinstance(item, dict) and clean(item.get("pack_id")) == REFERENCE_PACK_ID), {})
    guardrails = pack.get("guardrails") if isinstance(pack.get("guardrails"), dict) else {}
    return {
        "pack_id": REFERENCE_PACK_ID,
        "status": clean(pack.get("status")) or clean(manifest.get("status")) or "reference_only",
        "purpose": clean(pack.get("purpose")) or "Canonical HSD visual quality references.",
        "renderer_cutover_allowed": bool(manifest.get("renderer_cutover_allowed")),
        "auto_render_allowed": bool(manifest.get("auto_render_allowed")),
        "auto_publish_allowed": bool(manifest.get("auto_publish_allowed")),
        "paid_api_required": bool(manifest.get("paid_api_required")),
        "guardrails": {
            "reference_only": guardrails.get("reference_only") is not False,
            "publish_ready": guardrails.get("publish_ready") is True,
            "auto_approval": guardrails.get("auto_approval") is True,
            "auto_render": guardrails.get("auto_render") is True,
            "auto_publish": guardrails.get("auto_publish") is True,
            "paid_apis": guardrails.get("paid_apis") is True,
        },
    }


def reference_for_format(format_spec: Dict[str, Any], template: Dict[str, str]) -> Dict[str, Any]:
    if clean(template.get("reference_pack_id")) != REFERENCE_PACK_ID:
        return {}
    reference = dict(REFERENCE_FINAL_SCORE_FORMATS.get(clean(format_spec.get("format_id")), {}))
    if not reference:
        return {}
    reference["reference_pack_id"] = REFERENCE_PACK_ID
    for key in ["reference_spec_path", "reference_public_mockup_path", "reference_layout_path"]:
        path = project_path(reference.get(key))
        reference[f"{key}_exists"] = path.exists()
    return reference


def load_reference_spec(reference: Dict[str, Any]) -> Dict[str, Any]:
    path = project_path(reference.get("reference_spec_path"))
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def zone_box(template_spec: Dict[str, Any], name: str) -> Tuple[int, int, int, int]:
    zones = template_spec.get("zones") if isinstance(template_spec.get("zones"), dict) else {}
    zone = zones.get(name) if isinstance(zones.get(name), dict) else {}
    return int(zone.get("x", 0)), int(zone.get("y", 0)), int(zone.get("w", 0)), int(zone.get("h", 0))


def draw_reference_text(
    image: Any,
    box: Tuple[int, int, int, int],
    text: str,
    role: str,
    start_size: int,
    min_size: int,
    fill: tuple[int, int, int],
    *,
    max_lines: int = 1,
    align: str = "left",
    uppercase: bool = True,
    stroke: int = 0,
    stroke_fill: tuple[int, int, int] = (0, 0, 0),
    line_gap: int = 5,
) -> int:
    if ImageDraw is None:
        return 0
    draw = ImageDraw.Draw(image)
    x, y, w, h = box
    prepared = clean(text).upper() if uppercase else clean(text)
    if not prepared:
        return 0
    chosen = reference_font(role, min_size)
    lines: List[str] = [prepared]
    for size in range(start_size, min_size - 1, -2):
        candidate = reference_font(role, size)
        candidate_lines = wrap_text(draw, prepared, candidate, w, max_lines)
        line_height = size + line_gap
        if candidate_lines and line_height * len(candidate_lines) <= h and all(text_size(draw, line, candidate)[0] <= w for line in candidate_lines):
            chosen = candidate
            lines = candidate_lines
            break
    line_height = getattr(chosen, "size", min_size) + line_gap
    total_h = line_height * len(lines)
    y_cursor = y + max(0, (h - total_h) // 2)
    overflow = 0
    for line in lines:
        line_w, _ = text_size(draw, line, chosen)
        if align == "center":
            x_cursor = x + (w - line_w) // 2
        elif align == "right":
            x_cursor = x + w - line_w
        else:
            x_cursor = x
        if x_cursor < x or x_cursor + line_w > x + w or y_cursor + line_height > y + h:
            overflow += 1
        if stroke:
            draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        else:
            draw.text((x_cursor + 2, y_cursor + 3), line, font=chosen, fill=(0, 0, 0))
        if role in {"display", "score", "context"} and Image is not None:
            mask = Image.new("L", image.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.text((x_cursor, y_cursor), line, font=chosen, fill=255)
            patch = texture_patch(fill, image.size, sum(ord(character) for character in f"{line}:{role}:{getattr(chosen, 'size', min_size)}"))
            image.alpha_composite(Image.composite(patch, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask))
            draw = ImageDraw.Draw(image)
            if stroke:
                draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
            else:
                draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill)
        elif not stroke:
            draw.text((x_cursor, y_cursor), line, font=chosen, fill=fill)
        y_cursor += line_height
    return overflow


def draw_reference_panel(image: Any, box: Tuple[int, int, int, int], outline: tuple[int, int, int], *, fill: tuple[int, int, int, int] = (2, 4, 9, 220), radius: int = 12, width: int = 2) -> None:
    x, y, w, h = box
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((x + 7, y + 10, x + w + 7, y + h + 10), radius=radius, fill=(0, 0, 0, 110))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=(*outline, 235), width=width)
    image.alpha_composite(layer)


def mix_rgb(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def draw_editorial_halftone(draw: Any, width: int, height: int, accent: tuple[int, int, int], *, seed: int) -> None:
    randomizer = random.Random(seed)
    for _ in range(90 if height > 1500 else 60):
        x = randomizer.randrange(0, width)
        y = randomizer.randrange(0, height)
        size = randomizer.randrange(1, 4)
        alpha = randomizer.randrange(7, 22)
        color = (*accent, alpha) if randomizer.random() < 0.24 else (248, 250, 255, alpha)
        draw.rectangle((x, y, x + size, y + size), fill=color)


def draw_soft_light_sweep(image: Any, points: List[Tuple[int, int]], color: tuple[int, int, int], alpha: int, blur: int) -> None:
    if Image is None or ImageDraw is None:
        return
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.polygon(points, fill=(*color, alpha))
    if ImageFilter is not None:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    image.alpha_composite(layer)


def draw_vignette(image: Any, strength: int = 92) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = image.size
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    band_count = 14
    for index in range(band_count):
        inset_x = int((width * 0.035) * index)
        inset_y = int((height * 0.030) * index)
        alpha = max(0, strength - index * 7)
        draw.rectangle((inset_x, inset_y, width - inset_x, height - inset_y), outline=(0, 0, 0, alpha), width=max(18, int(min(width, height) * 0.018)))
    if ImageFilter is not None:
        layer = layer.filter(ImageFilter.GaussianBlur(24))
    image.alpha_composite(layer)


def draw_reference_background(
    image: Any,
    tone: str = "final",
    primary_accent: tuple[int, int, int] | None = None,
    secondary_accent: tuple[int, int, int] | None = None,
    *,
    photo_first: bool = False,
) -> None:
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    primary = primary_accent or PALETTE["gold"]
    secondary = secondary_accent or PALETTE["blue"]
    base_top = (2, 4, 9)
    base_bottom = (11, 18, 32)
    for y in range(height):
        amount = y / max(1, height - 1)
        mid_tint = mix_rgb(primary, secondary, 0.42)
        base = mix_rgb(base_top, base_bottom, amount)
        if 0.18 < amount < 0.82:
            base = mix_rgb(base, mix_rgb(mid_tint, (3, 6, 13), 0.90), 0.14)
        draw.line((0, y, width, y), fill=(*base, 255))

    draw_soft_light_sweep(
        image,
        [(-90, int(height * 0.76)), (int(width * 0.28), int(height * 0.42)), (int(width * 0.62), height + 80), (-90, height + 80)],
        primary,
        70 if tone == "final" else 52,
        38,
    )
    draw_soft_light_sweep(
        image,
        [(int(width * 0.56), -90), (width + 90, -90), (width + 90, int(height * 0.54)), (int(width * 0.34), int(height * 0.24))],
        secondary,
        58 if tone == "final" else 42,
        46,
    )
    draw_soft_light_sweep(
        image,
        [(int(width * 0.10), int(height * 0.16)), (int(width * 0.94), int(height * 0.06)), (int(width * 0.82), int(height * 0.12)), (int(width * 0.14), int(height * 0.24))],
        (248, 250, 255),
        24,
        20,
    )

    rail_alpha = 24 if tone == "final" else 18
    for x in range(-height, width + height, 520):
        draw.line((x, height + 60, x + int(height * 0.66), -70), fill=(*primary, rail_alpha), width=1)
    for x in range(-height, width + height, 820):
        draw.line((x, height + 140, x + int(height * 0.52), -40), fill=(*secondary, 16), width=1)

    for y in [int(height * 0.12), int(height * 0.285), int(height * 0.74), int(height * 0.88)]:
        draw.line((30, y, width - 30, y), fill=(*primary, 22), width=1)
    for x in range(86, width, 170):
        draw.line((x, int(height * 0.18), x, int(height * 0.92)), fill=(248, 250, 255, 4), width=1)

    for index, word in enumerate(["HER SPORTS DAILY", "FINAL SCORE", "REVIEW DRAFT"]):
        text_y = int(height * (0.18 + index * 0.29))
        draw_reference_text(
            image,
            (width - 390, text_y, 330, 34),
            word,
            "context",
            21,
            12,
            (248, 250, 255, 22),
            max_lines=1,
            align="right",
        )

    draw.rectangle((0, 0, width, 10), fill=(*primary, 172))
    draw.rectangle((0, 10, width, 18), fill=(*secondary, 110))
    draw.rectangle((0, height - 78, width, height - 64), fill=(*primary, 146))
    draw.rectangle((0, height - 64, width, height - 58), fill=(*secondary, 98))

    if photo_first:
        draw_soft_light_sweep(
            image,
            [(34, int(height * 0.30)), (int(width * 0.52), int(height * 0.25)), (int(width * 0.45), int(height * 0.35)), (34, int(height * 0.40))],
            primary,
            60,
            18,
        )
        draw.line((54, int(height * 0.305), width - 54, int(height * 0.305)), fill=(*primary, 142), width=3)
        draw.line((54, int(height * 0.72), width - 54, int(height * 0.72)), fill=(*secondary, 104), width=2)
        draw.rectangle((0, int(height * 0.325), 12, int(height * 0.68)), fill=(*primary, 186))
        draw.rectangle((width - 12, int(height * 0.28), width, int(height * 0.62)), fill=(*secondary, 150))

    draw_editorial_halftone(draw, width, height, primary, seed=width * 17 + height * 31 + (11 if photo_first else 0))

    quiet = Image.new("RGBA", image.size, (0, 0, 0, 0))
    quiet_draw = ImageDraw.Draw(quiet, "RGBA")
    quiet_draw.rectangle((0, int(height * 0.105), width, int(height * 0.275)), fill=(0, 0, 0, 136))
    quiet_draw.rectangle((0, int(height * 0.300), width, int(height * 0.690)), fill=(0, 0, 0, 124 if photo_first else 118))
    quiet_draw.rectangle((0, int(height * 0.705), width, int(height * 0.910)), fill=(0, 0, 0, 106))
    image.alpha_composite(quiet)
    draw_vignette(image, 88 if photo_first else 78)

def draw_reference_badge(image: Any, template_spec: Dict[str, Any]) -> str:
    badge = template_spec.get("badge") if isinstance(template_spec.get("badge"), dict) else {}
    x = int(badge.get("x", 48))
    y = int(badge.get("y", 42))
    spec_w = int(badge.get("w", 80))
    spec_h = int(badge.get("h", 80))
    canvas_w, canvas_h = image.size
    target = max(spec_w, min(124, int(min(canvas_w, canvas_h) * 0.115)))
    w = h = target
    badge_path = REFERENCE_BRAND_ROOT / clean(badge.get("asset") or "official_hsd_badge_reference.png")
    if badge_path.exists():
        try:
            logo = Image.open(badge_path).convert("RGBA")
            bbox = logo.getbbox()
            if bbox:
                logo = logo.crop(bbox)
            logo.thumbnail((w, h), resample_filter())
            shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow, "RGBA")
            shadow_draw.rounded_rectangle((x + 4, y + 6, x + w + 4, y + h + 6), radius=10, fill=(0, 0, 0, 80))
            if ImageFilter is not None:
                shadow = shadow.filter(ImageFilter.GaussianBlur(3))
            image.alpha_composite(shadow)
            image.alpha_composite(logo, (x + (w - logo.width) // 2, y + (h - logo.height) // 2))
            return badge_path.relative_to(PROJECT_ROOT).as_posix()
        except Exception:
            pass
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((x, y, x + w, y + h), outline=(222, 161, 38, 255), width=3)
    draw_reference_text(image, (x + 8, y + 8, w - 16, h - 16), "HSD", "context", 28, 16, PALETTE["ink"], max_lines=1, align="center")
    return "badge_missing_text_fallback"


def draw_reference_guardrail(image: Any) -> None:
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    label = "DRAFT REVIEW ONLY - NOT APPROVED - NO AUTO-PUBLISH"
    pill_w = min(326, width - 760)
    if pill_w > 180:
        draw.rounded_rectangle((width - pill_w - 50, 76, width - 50, 122), radius=8, fill=(190, 39, 54, 232), outline=(241, 238, 229, 180), width=1)
        draw_reference_text(image, (width - pill_w - 38, 80, pill_w - 24, 36), "DRAFT REVIEW ONLY", "context", 19, 12, PALETTE["ink"], max_lines=1, align="center")
    strip_h = 64
    draw.rectangle((0, height - strip_h, width, height), fill=(190, 39, 54, 244))
    draw_reference_text(image, (24, height - strip_h + 12, width - 48, strip_h - 18), label, "context", 24, 14, PALETTE["ink"], max_lines=1, align="center")


def team_registry() -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    aliases: Dict[str, str] = {}
    for row in read_csv(TEAM_ALIASES_CSV):
        alias = clean(row.get("alias"))
        team_id = clean(row.get("team_id"))
        if alias and team_id:
            aliases[norm(alias)] = team_id
    logos: Dict[str, Dict[str, str]] = {}
    for row in read_csv(TEAM_LOGOS_CSV):
        team_id = clean(row.get("team_id"))
        if team_id:
            logos[team_id] = row
    return aliases, logos


def team_color_registry() -> Dict[str, Dict[str, Any]]:
    colors: Dict[str, Dict[str, Any]] = {}
    for row in read_csv(TEAM_COLORS_CSV):
        team_id = clean(row.get("team_id"))
        primary = hex_to_rgb(row.get("primary_hex") or row.get("primary_color_hex"))
        secondary = hex_to_rgb(row.get("secondary_hex") or row.get("secondary_color_hex"))
        if team_id and primary:
            colors[team_id] = {
                "primary_rgb": primary,
                "secondary_rgb": secondary,
                "primary_hex": rgb_to_hex(primary),
                "secondary_hex": rgb_to_hex(secondary) if secondary else "",
            }
    return colors


def resolve_team_id(team: str, aliases: Dict[str, str]) -> str:
    normalized = norm(team)
    if normalized in aliases:
        return aliases[normalized]
    for alias, team_id in aliases.items():
        if alias and (alias in normalized or normalized in alias):
            return team_id
    return ""


def team_registry_accent(team: str, aliases: Dict[str, str], fallback: tuple[int, int, int]) -> tuple[tuple[int, int, int], str]:
    team_id = resolve_team_id(team, aliases)
    colors = team_color_registry().get(team_id, {})
    accent = colors.get("primary_rgb")
    if isinstance(accent, tuple):
        return accent, "local_wnba_team_registry_primary_color"
    return fallback, "fallback_hsd_accent_no_team_color_registry"


def resolve_athlete_photo(player: str, team: str) -> Dict[str, Any]:
    player_name = clean(player)
    team_name = clean(team)
    if not player_name:
        return {
            "status": "athlete_photo_not_applicable",
            "photo_review_required": True,
            "photo_approval_cue": "NO PLAYER SELECTED",
            "requirement": "No verified player selected for an athlete photo slot.",
        }
    aliases, _ = team_registry()
    team_id = resolve_team_id(team_name, aliases) or slug(team_name)
    athlete_id = "_".join(part for part in [team_id, slug(player_name)] if part)
    athlete_dir = WNBA_ATHLETE_ROOT / athlete_id
    headshot = athlete_dir / "headshot.png"
    marker = athlete_dir / "headshot.png.approved"
    marker_payload = read_json_file(marker) if marker.exists() else {}
    marker_player = clean(marker_payload.get("display_name"))
    marker_team = clean(marker_payload.get("team_id"))
    provider_player_id = clean(marker_payload.get("provider_player_id"))
    marker_matches = bool(
        marker_payload
        and (not marker_player or norm(marker_player) == norm(player_name))
        and (not marker_team or marker_team == team_id)
    )
    base = {
        "athlete_id": athlete_id,
        "player_name": player_name,
        "team": team_name,
        "team_id": team_id,
        "asset_path": relative_project_path(headshot),
        "approval_marker_path": relative_project_path(marker),
        "approval_policy": clean(marker_payload.get("policy")) or "approved marker required before local render use",
        "approval_source_file": clean(marker_payload.get("source_file")),
        "approved_at_utc": clean(marker_payload.get("approved_at_utc")),
        "provider_player_id": provider_player_id,
        "requirement": "Use only approved local athlete headshot/cutout assets; missing or unapproved images stay review-only fallbacks.",
    }
    identity_gate = athlete_identity_gate(
        athlete_id,
        asset_path=relative_project_path(headshot),
        provider_player_id=provider_player_id,
        marker_payload=marker_payload,
    )
    base.update({
        "identity_review_status": clean(identity_gate.get("identity_review_status")),
        "identity_issue_count": clean(identity_gate.get("identity_issue_count")),
        "identity_high_issue_count": clean(identity_gate.get("identity_high_issue_count")),
        "identity_issue_codes": clean(identity_gate.get("identity_issue_codes")),
        "identity_resolution_status": clean(identity_gate.get("identity_resolution_status")),
        "identity_resolution_decision": clean(identity_gate.get("identity_resolution_decision")),
        "identity_resolution_source_file": clean(identity_gate.get("identity_resolution_source_file")),
        "identity_resolution_evidence_url": clean(identity_gate.get("identity_resolution_evidence_url")),
        "identity_resolution_operator": clean(identity_gate.get("identity_resolution_operator")),
        "identity_resolution_reviewed_at_local": clean(identity_gate.get("identity_resolution_reviewed_at_local")),
    })
    if headshot.exists() and marker.exists() and marker_matches and clean(identity_gate.get("status")) == "hold":
        return {
            **base,
            "status": "athlete_photo_identity_hold",
            "photo_review_required": True,
            "photo_approval_cue": "IDENTITY HOLD",
            "render_method": "safe_text_fallback_identity_hold",
            "review_variant_status": "blocked_by_identity_resolution",
            "review_variant_feed_path": "",
            "review_variant_story_path": "",
            "review_variant_square_path": "",
            "review_variant_metadata_source": ATHLETE_PHOTO_ONBOARDING_METADATA,
            "review_variant_policy": "identity_resolution_required_before_review_variant_use",
            "review_variant_crop_readiness_score": "",
            "blocker": clean(identity_gate.get("blocker")),
        }
    if headshot.exists() and marker.exists() and marker_matches:
        variant = athlete_photo_onboarding_row(athlete_id, relative_project_path(headshot))
        return {
            **base,
            "status": "approved_local_headshot",
            "photo_review_required": False,
            "photo_approval_cue": "APPROVED PHOTO",
            "render_method": "approved_local_png_with_marker",
            "review_variant_status": "review_variant_available" if variant else "not_generated",
            "review_variant_feed_path": clean(variant.get("feed_variant_path")),
            "review_variant_story_path": clean(variant.get("story_variant_path")),
            "review_variant_square_path": clean(variant.get("square_variant_path")),
            "review_variant_metadata_source": ATHLETE_PHOTO_ONBOARDING_METADATA if variant else "",
            "review_variant_policy": clean(variant.get("review_only_policy")),
            "review_variant_crop_readiness_score": clean(variant.get("crop_readiness_score")),
            "blocker": "",
        }
    if headshot.exists() and marker.exists() and not marker_matches:
        return {
            **base,
            "status": "athlete_photo_marker_mismatch",
            "photo_review_required": True,
            "photo_approval_cue": "PHOTO HOLD",
            "render_method": "safe_text_fallback",
            "blocker": "Approval marker does not match the selected player/team.",
        }
    if headshot.exists():
        return {
            **base,
            "status": "athlete_photo_unapproved",
            "photo_review_required": True,
            "photo_approval_cue": "PHOTO REVIEW",
            "render_method": "safe_text_fallback",
            "blocker": "Local headshot exists but the approved marker is missing.",
        }
    return {
        **base,
        "status": "athlete_photo_missing",
        "photo_review_required": True,
        "photo_approval_cue": "PHOTO MISSING",
        "render_method": "safe_text_fallback",
        "blocker": "No local athlete headshot found for the selected player/team.",
    }


def short_team(team: str) -> str:
    text = clean(team).upper()
    prefixes = [
        "GOLDEN STATE ",
        "LOS ANGELES ",
        "LAS VEGAS ",
        "NEW YORK ",
        "CONNECTICUT ",
        "WASHINGTON ",
        "MINNESOTA ",
        "SEATTLE ",
        "PHOENIX ",
        "INDIANA ",
        "ATLANTA ",
        "DALLAS ",
        "CHICAGO ",
    ]
    for prefix in prefixes:
        if text.startswith(prefix) and len(text) > len(prefix) + 3:
            return text[len(prefix):]
    return text


def score_margin(score: Dict[str, str]) -> int | None:
    try:
        return max(0, int(score.get("winner_score", "0")) - int(score.get("loser_score", "0")))
    except Exception:
        return None


def score_total(score: Dict[str, str]) -> int | None:
    try:
        return int(score.get("winner_score", "0")) + int(score.get("loser_score", "0"))
    except Exception:
        return None


def game_shape(score: Dict[str, str]) -> Dict[str, str]:
    margin = score_margin(score)
    if margin is None:
        return {
            "game_shape": "final_result",
            "game_shape_label": "FINAL RESULT",
            "angle_label": "SCOREBOARD FINAL",
            "prompt": "WHAT STOOD OUT FROM THE FINAL?",
        }
    if margin <= 3:
        return {
            "game_shape": "close_finish",
            "game_shape_label": "CLOSE FINISH",
            "angle_label": f"{short_team(score.get('winner'))} CLOSE FINISH",
            "prompt": "WHO MADE THE DIFFERENCE LATE?",
        }
    if margin <= 7:
        return {
            "game_shape": "late_separation",
            "game_shape_label": "LATE SEPARATION",
            "angle_label": f"{short_team(score.get('winner'))} +{margin} FINAL",
            "prompt": "WHERE DID THE GAME TURN?",
        }
    if margin <= 14:
        return {
            "game_shape": "clear_separation",
            "game_shape_label": "CLEAR SEPARATION",
            "angle_label": f"{short_team(score.get('winner'))} +{margin} FINAL",
            "prompt": f"WHAT FUELED {short_team(score.get('winner'))}'S SEPARATION?",
        }
    return {
        "game_shape": "statement_margin",
        "game_shape_label": "STATEMENT MARGIN",
        "angle_label": f"{short_team(score.get('winner'))} +{margin} FINAL",
        "prompt": f"HOW DID {short_team(score.get('winner'))} BUILD THE GAP?",
    }


def source_count(packet: Dict[str, Any]) -> str:
    text = " ".join(clean(packet.get(key)) for key in ["copy_context", "source_detail", "source_cue"])
    match = re.search(r"\b(\d+)\s+source", text, re.IGNORECASE)
    return clean(match.group(1)) if match else ""


def source_quality_label(packet: Dict[str, Any]) -> str:
    text = " ".join(clean(packet.get(key)) for key in ["copy_context", "source_detail", "source_cue"]).lower()
    if "publish_grade" in text or "publish grade" in text:
        return "PUBLISH-GRADE"
    if "confidence_ready" in text or "source_confidence_ready" in text:
        return "SOURCE CHECKED"
    return "SOURCE REVIEW"


def final_score_callouts(packet: Dict[str, Any], score: Dict[str, str]) -> List[Dict[str, str]]:
    callouts: List[Dict[str, str]] = []
    margin = score_margin(score)
    total = score_total(score)
    if margin is not None:
        callouts.append({"label": "MARGIN", "value": f"+{margin}"})
    if total is not None:
        callouts.append({"label": "TOTAL", "value": str(total)})
    count = source_count(packet)
    if count:
        callouts.append({"label": "SOURCES", "value": count})
    return callouts[:3]


def verified_stat_text(packet: Dict[str, Any]) -> str:
    return clean(
        packet.get("top_performers")
        or packet.get("verified_top_performers")
        or packet.get("player_stats")
        or packet.get("box_score_stats")
        or packet.get("stat_line")
    )


def parse_stat_pairs(value: str) -> List[Dict[str, str]]:
    stats: List[Dict[str, str]] = []
    seen: set[str] = set()
    for part in re.split(r",|\|", clean(value)):
        token = clean(part)
        match = re.search(r"\b(PTS|REB|AST|STL|BLK|MIN)\s+(\d+(?:\.\d+)?)\b", token, re.IGNORECASE)
        if not match:
            match = re.search(r"\b(\d+(?:\.\d+)?)\s+(PTS|REB|AST|STL|BLK|MIN)\b", token, re.IGNORECASE)
            if match:
                label, number = match.group(2).upper(), match.group(1)
            else:
                continue
        else:
            label, number = match.group(1).upper(), match.group(2)
        if label not in seen:
            seen.add(label)
            stats.append({"label": label, "value": number})
    return stats


def parse_verified_stat_performers(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = verified_stat_text(packet)
    if not raw:
        return []
    performers: List[Dict[str, Any]] = []
    for entry in [clean(item) for item in raw.split(";") if clean(item)]:
        match = re.match(r"(.+?)(?:\s+\(([^)]+)\))?\s*:\s*(.+)$", entry)
        if not match:
            continue
        name = clean(match.group(1))
        team = clean(match.group(2))
        stats = parse_stat_pairs(match.group(3))
        if name and stats:
            performers.append({"name": name, "team": team, "stats": stats, "source_text": entry})
    return performers


def stat_number(stats: List[Dict[str, str]], label: str) -> int:
    for item in stats:
        if clean(item.get("label")).upper() == label:
            try:
                return int(float(clean(item.get("value"))))
            except Exception:
                return 0
    return 0


def stat_module_strength(stats: List[Dict[str, str]]) -> str:
    pts = stat_number(stats, "PTS")
    reb = stat_number(stats, "REB")
    ast = stat_number(stats, "AST")
    stocks = stat_number(stats, "STL") + stat_number(stats, "BLK")
    if pts >= 15 or reb >= 8 or ast >= 7 or stocks >= 4:
        return "lead_ledger"
    if pts >= 10 or reb >= 6 or ast >= 5 or stocks >= 3:
        return "supporting_stat"
    return "low_stat_context"


def last_name(name: str) -> str:
    parts = clean(name).replace(".", "").split()
    return parts[-1].upper() if parts else ""


def select_verified_stat_module(packet: Dict[str, Any], score: Dict[str, str]) -> Dict[str, Any]:
    performers = parse_verified_stat_performers(packet)
    if not performers:
        return {"status": "fallback_game_edge_no_verified_stat_text"}
    winner_norm = norm(score.get("winner"))
    winner_short_norm = norm(short_team(score.get("winner", "")))
    preferred = [
        item for item in performers
        if norm(item.get("team")) and (norm(item.get("team")) in winner_norm or winner_short_norm in norm(item.get("team")))
    ]
    pool = preferred or performers
    selected = sorted(pool, key=lambda item: stat_number(item.get("stats", []), "PTS"), reverse=True)[0]
    stats = selected.get("stats", [])[:4]
    strength = stat_module_strength(stats)
    player = clean(selected.get("name"))
    team = clean(selected.get("team"))
    pts = stat_number(stats, "PTS")
    winner_short = short_team(score.get("winner", ""))
    loser_short = short_team(score.get("loser", ""))
    margin = score_margin(score)
    headline = f"{last_name(player)} LED {winner_short}" if player and winner_short else (f"{last_name(player)}: {pts} PTS" if pts else player.upper())
    stat_text = ", ".join(f"{item['value']} {item['label']}" for item in stats[:3])
    stat_line = " / ".join(f"{item['value']} {item['label']}" for item in stats[:3])
    team_text = f" ({short_team(team)})" if team else ""
    matchup_note = f"{winner_short} {score.get('winner_score')} - {loser_short} {score.get('loser_score')}"
    shape = game_shape(score)
    photo = resolve_athlete_photo(player, team or score.get("winner", ""))
    if margin is not None:
        matchup_note = f"{winner_short} +{margin} vs {loser_short}"
    if clean(shape.get("game_shape")) == "close_finish":
        headline = f"{last_name(player)} + CLOSE FINISH" if player else clean(shape.get("game_shape_label"))
    elif clean(shape.get("game_shape")) == "statement_margin":
        headline = f"{last_name(player)} + STATEMENT MARGIN" if player else clean(shape.get("game_shape_label"))
    if strength != "lead_ledger":
        headline = f"{last_name(player)} STAT NOTE" if player else "VERIFIED STAT NOTE"
    return {
        "status": "verified_player_stat_module" if strength == "lead_ledger" else "verified_supporting_stat_module",
        "eyebrow": "PLAYER LEDGER" if strength == "lead_ledger" else "STAT NOTE",
        "headline": headline,
        "body": f"{player}{team_text}: {stat_text}.",
        "editorial_line": f"{stat_line} in the {matchup_note} final." if strength == "lead_ledger" else f"Supporting stat context for the {matchup_note} final.",
        "matchup_note": matchup_note,
        "game_shape": clean(shape.get("game_shape")),
        "game_shape_label": clean(shape.get("game_shape_label")),
        "stat_strength": strength,
        "athlete_photo_status": clean(photo.get("status")),
        "athlete_photo_path": clean(photo.get("asset_path")),
        "athlete_photo_approval_marker_path": clean(photo.get("approval_marker_path")),
        "athlete_photo_approval_cue": clean(photo.get("photo_approval_cue")),
        "athlete_photo_review_required": bool(photo.get("photo_review_required")),
        "athlete_photo_blocker": clean(photo.get("blocker")),
        "athlete_photo_render_method": clean(photo.get("render_method")),
        "athlete_photo_policy": clean(photo.get("approval_policy")),
        "athlete_photo_approved_at_utc": clean(photo.get("approved_at_utc")),
        "athlete_photo_review_variant_status": clean(photo.get("review_variant_status")),
        "athlete_photo_review_variant_feed_path": clean(photo.get("review_variant_feed_path")),
        "athlete_photo_review_variant_story_path": clean(photo.get("review_variant_story_path")),
        "athlete_photo_review_variant_square_path": clean(photo.get("review_variant_square_path")),
        "athlete_photo_review_variant_metadata_source": clean(photo.get("review_variant_metadata_source")),
        "athlete_photo_review_variant_policy": clean(photo.get("review_variant_policy")),
        "athlete_photo_review_variant_crop_readiness_score": clean(photo.get("review_variant_crop_readiness_score")),
        "athlete_photo_identity_review_status": clean(photo.get("identity_review_status")),
        "athlete_photo_identity_issue_count": clean(photo.get("identity_issue_count")),
        "athlete_photo_identity_high_issue_count": clean(photo.get("identity_high_issue_count")),
        "athlete_photo_identity_issue_codes": clean(photo.get("identity_issue_codes")),
        "athlete_photo_identity_resolution_status": clean(photo.get("identity_resolution_status")),
        "athlete_photo_identity_resolution_decision": clean(photo.get("identity_resolution_decision")),
        "athlete_photo_identity_resolution_source_file": clean(photo.get("identity_resolution_source_file")),
        "athlete_photo_identity_resolution_evidence_url": clean(photo.get("identity_resolution_evidence_url")),
        "athlete_photo_layout_options": "photo_first_final_score,compact_headshot_chip,logo_first_fallback,safe_no_photo_fallback",
        "callouts": stats[:3],
        "player_name": player,
        "team": team,
        "source_text": clean(selected.get("source_text")),
        "stat_source_confidence": "verified_stat_text_ready_manual_crosscheck_required" if strength == "lead_ledger" else "verified_low_stat_context_manual_crosscheck_required",
        "stat_source_label": "Verified player/stat text available" if strength == "lead_ledger" else "Verified stat context available",
        "stat_review_cue": "Confirm the named performer and stat line against source proof before approval." if strength == "lead_ledger" else "Use this as supporting context only; do not make the player the lead unless source proof supports a stronger angle.",
    }


def game_edge_module(score: Dict[str, str]) -> Dict[str, str]:
    winner = clean(score.get("winner"))
    loser = clean(score.get("loser"))
    margin = score_margin(score)
    shape = game_shape(score)
    if margin is None:
        return {
            "eyebrow": "SCORE-DERIVED EDGE",
            "headline": "FINAL RESULT",
            "body": f"{winner} finished ahead of {loser}.",
            "game_shape": clean(shape.get("game_shape")),
            "game_shape_label": clean(shape.get("game_shape_label")),
        }
    if margin <= 3:
        headline = "DOWN TO THE WIRE"
        body = f"{short_team(winner)} finished {margin} point{'s' if margin != 1 else ''} clear of {short_team(loser)}."
    elif margin <= 7:
        headline = "LATE SEPARATION"
        body = f"{short_team(winner)} created a {margin}-point final margin over {short_team(loser)}."
    elif margin <= 14:
        headline = "CLEAR EDGE"
        body = f"{short_team(winner)} finished with a {margin}-point advantage over {short_team(loser)}."
    else:
        headline = "STATEMENT WIN"
        body = f"{short_team(winner)} closed with a {margin}-point victory over {short_team(loser)}."
    return {"eyebrow": "SCORE-DERIVED EDGE", "headline": headline, "body": body, "game_shape": clean(shape.get("game_shape")), "game_shape_label": clean(shape.get("game_shape_label"))}


def review_prompt(score: Dict[str, str]) -> str:
    return clean(game_shape(score).get("prompt")) or "WHAT STOOD OUT FROM THE FINAL?"


def scoreline_context(score: Dict[str, str]) -> str:
    winner = short_team(score.get("winner", ""))
    loser = short_team(score.get("loser", ""))
    margin = score_margin(score)
    total = score_total(score)
    parts = []
    if margin is not None:
        parts.append(f"{winner} +{margin} vs {loser}")
    else:
        parts.append(f"{winner} over {loser}")
    if total is not None:
        parts.append(f"{total} combined points")
    return "; ".join(parts)


def stat_line_for_microcopy(module: Dict[str, Any]) -> str:
    return " / ".join(
        f"{clean(item.get('value'))} {clean(item.get('label'))}"
        for item in (module.get("callouts") or [])[:3]
        if clean(item.get("value")) and clean(item.get("label"))
    )


def editorial_microcopy_variants(packet: Dict[str, Any], score: Dict[str, str], stat_module: Dict[str, Any]) -> List[Dict[str, str]]:
    winner = short_team(score.get("winner", ""))
    loser = short_team(score.get("loser", ""))
    margin = score_margin(score)
    total = score_total(score)
    source_label = source_quality_label(packet)
    shape = game_shape(score)
    shape_label = clean(shape.get("game_shape_label")) or "FINAL RESULT"
    variants: List[Dict[str, str]] = []
    margin_text = f"+{margin}" if margin is not None else "final-score"
    total_text = f"{total}-point total" if total is not None else "verified final"
    variants.append(
        {
            "variant_id": "scoreline_spine",
            "label": "Scoreline spine",
            "headline": clean(shape.get("angle_label")) or f"{winner} {margin_text} FINAL",
            "body": f"{shape_label}: {winner} over {loser}; anchor the angle to the {margin_text} margin and {total_text}.",
        }
    )
    if clean(stat_module.get("status")) in {"verified_player_stat_module", "verified_supporting_stat_module"}:
        player = clean(stat_module.get("player_name"))
        stat_line = stat_line_for_microcopy(stat_module)
        if clean(stat_module.get("status")) == "verified_player_stat_module":
            variants.append(
                {
                    "variant_id": "verified_player_ledger",
                    "label": "Verified player ledger",
                    "headline": f"{last_name(player)} + {shape_label}" if player else shape_label,
                    "body": f"{last_name(player).title()}'s verified {stat_line.replace(' / ', ', ')} frames the {shape_label.lower()}.",
                }
            )
        else:
            variants.append(
                {
                    "variant_id": "verified_supporting_stat_note",
                    "label": "Verified supporting stat note",
                    "headline": clean(shape.get("angle_label")) or f"{winner} {margin_text} FINAL",
                    "body": f"{last_name(player).title()}'s verified {stat_line.replace(' / ', ', ')} is supporting context; keep the main angle on the {shape_label.lower()}.",
                }
            )
    else:
        variants.append(
            {
                "variant_id": "score_only_hold",
                "label": "Score-only fallback",
                "headline": clean(shape.get("angle_label")) or f"{winner} SCOREBOARD EDGE",
                "body": f"No verified player stat line is available; keep this as a {shape_label.lower()} scoreline until source proof supports a named lead.",
            }
        )
    variants.append(
        {
            "variant_id": "operator_angle_check",
            "label": "Operator angle check",
            "headline": review_prompt(score),
            "body": f"{source_label} review: use this as the manual question, not an automated claim. Add the why only after the source packet supports it.",
        }
    )
    return variants


def selected_editorial_microcopy(packet: Dict[str, Any], score: Dict[str, str], stat_module: Dict[str, Any]) -> Dict[str, Any]:
    variants = editorial_microcopy_variants(packet, score, stat_module)
    status = clean(stat_module.get("status"))
    if status == "verified_player_stat_module":
        preferred_id = "verified_player_ledger"
    elif status == "verified_supporting_stat_module":
        preferred_id = "verified_supporting_stat_note"
    else:
        preferred_id = "score_only_hold"
    preferred = next((item for item in variants if item["variant_id"] == preferred_id), variants[0] if variants else {})
    context = scoreline_context(score)
    shape = game_shape(score)
    return {
        "status": "source_safe_editorial_microcopy_ready",
        "selected_variant_id": clean(preferred.get("variant_id")),
        "eyebrow": "MATCHUP ANGLE",
        "headline": clean(preferred.get("headline")),
        "body": clean(preferred.get("body")),
        "context": context,
        "game_shape": clean(shape.get("game_shape")),
        "game_shape_label": clean(shape.get("game_shape_label")),
        "review_cue": "Copy is score/stat-derived only; verify source proof before adding why/how claims.",
        "variants": variants,
    }


def logo_candidates(team_id: str, row: Dict[str, str]) -> List[Path]:
    candidates: List[Path] = []
    raw = clean(row.get("file_path"))
    if raw:
        candidates.append(project_path(raw))
    if team_id:
        base = PROJECT_ROOT / "assets" / "leagues" / "wnba" / "teams" / team_id
        candidates.extend([base / "logo.png", base / "logo.svg"])
    seen: set[str] = set()
    unique: List[Path] = []
    for path in candidates:
        key = path.as_posix().lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def rasterize_svg_with_local_browser(svg_path: Path, output_path: Path, size: int = 700) -> Dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"status": "blocked", "reason": f"playwright unavailable: {clean(exc)}"}
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        svg_payload = base64.b64encode(svg_path.read_bytes()).decode("ascii")
        svg_uri = f"data:image/svg+xml;base64,{svg_payload}"
        html_doc = f"""
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              html, body {{
                margin: 0;
                width: {size}px;
                height: {size}px;
                background: transparent;
                overflow: hidden;
              }}
              img {{
                width: {size}px;
                height: {size}px;
                object-fit: contain;
                display: block;
              }}
            </style>
          </head>
          <body><img alt="team logo" src={json.dumps(svg_uri)}></body>
        </html>
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=playwright.chromium.executable_path)
            page = browser.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
            page.set_content(html_doc, wait_until="load")
            page.locator("img").wait_for(state="visible", timeout=5000)
            page.screenshot(path=output_path.as_posix(), omit_background=True)
            browser.close()
        image = Image.open(output_path).convert("RGBA")
        if not image.getbbox():
            return {"status": "blocked", "reason": "local browser produced a blank SVG raster."}
        image.save(output_path)
        return {"status": "ok", "path": output_path.as_posix()}
    except Exception as exc:
        return {"status": "blocked", "reason": clean(exc)[:240]}


def load_team_logo(team: str, aliases: Dict[str, str], logos: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    team_id = resolve_team_id(team, aliases)
    row = logos.get(team_id, {})
    approved = clean(row.get("approved")).lower() == "true"
    found_svg_path = ""
    svg_blocker = ""
    for path in logo_candidates(team_id, row):
        if not path.exists():
            continue
        try:
            if path.suffix.lower() == ".svg":
                found_svg_path = path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else path.as_posix()
                import cairosvg

                cache = OUT_DIR / "logo_cache" / f"{team_id or norm(team)}.png"
                cache.parent.mkdir(parents=True, exist_ok=True)
                cairosvg.svg2png(url=path.as_posix(), write_to=cache.as_posix(), output_width=700, output_height=700)
                image = Image.open(cache).convert("RGBA")
                render_path = cache
                render_method = "cairosvg"
            else:
                image = Image.open(path).convert("RGBA")
                render_path = path
                render_method = "source_png"
            return {
                "image": image,
                "team_id": team_id,
                "path": path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else path.as_posix(),
                "render_path": render_path.as_posix(),
                "status": "approved_logo" if approved else "registry_logo_review_required",
                "approved": approved,
                "render_method": render_method,
            }
        except Exception as exc:
            if path.suffix.lower() == ".svg":
                svg_blocker = clean(exc)[:220]
            continue
    if found_svg_path:
        svg_path = project_path(found_svg_path)
        cache = OUT_DIR / "logo_cache" / f"{team_id or norm(team)}_browser.png"
        browser_result = rasterize_svg_with_local_browser(svg_path, cache)
        if browser_result.get("status") == "ok":
            try:
                return {
                    "image": Image.open(cache).convert("RGBA"),
                    "team_id": team_id,
                    "path": found_svg_path,
                    "render_path": cache.as_posix(),
                    "status": "approved_svg_logo_rasterized_for_review" if approved else "svg_logo_rasterized_review_required",
                    "approved": approved,
                    "render_method": "local_browser_svg_to_png",
                }
            except Exception as exc:
                svg_blocker = clean(exc)[:220]
        else:
            svg_blocker = clean(browser_result.get("reason")) or svg_blocker
        return {
            "image": None,
            "team_id": team_id,
            "path": found_svg_path,
            "render_path": "",
            "status": "approved_svg_logo_converter_unavailable" if approved else "svg_logo_converter_unavailable_review_required",
            "approved": approved,
            "blocker": svg_blocker or "SVG converter unavailable in local Python runtime.",
        }
    return {
        "image": None,
        "team_id": team_id,
        "path": "",
        "render_path": "",
        "status": "logo_missing_team_name_placeholder",
        "approved": False,
    }


def draw_team_logo_slot(image: Any, team: str, box: Tuple[int, int, int, int], aliases: Dict[str, str], logos: Dict[str, Dict[str, str]], accent: tuple[int, int, int], *, winner: bool = False) -> Dict[str, Any]:
    registry_accent, registry_accent_source = team_registry_accent(team, aliases, accent)
    result = enrich_logo_result(load_team_logo(team, aliases, logos), registry_accent, registry_accent_source)
    team_accent = result.get("team_accent_rgb") if isinstance(result.get("team_accent_rgb"), tuple) else accent
    approval_cue = clean(result.get("logo_approval_cue")) or "LOGO REVIEW"
    draw_reference_panel(image, box, team_accent, fill=(1, 2, 7, 226), radius=16, width=2)
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    sheen = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen, "RGBA")
    glow_alpha = 56 if winner else 32
    sheen_draw.ellipse(
        (x - int(w * 0.25), y - int(h * 0.30), x + int(w * 1.25), y + int(h * 1.20)),
        fill=(*team_accent, glow_alpha),
    )
    if ImageFilter is not None:
        sheen = sheen.filter(ImageFilter.GaussianBlur(max(18, min(w, h) // 6)))
    image.alpha_composite(sheen)
    draw.rounded_rectangle((x + 12, y + 12, x + w - 12, y + h - 12), radius=12, outline=(*team_accent, 88), width=1)
    draw.line((x + 22, y + h - 18, x + w - 22, y + h - 18), fill=(*team_accent, 172), width=2)
    logo = result.get("image")
    if logo is not None:
        logo = logo.copy()
        pad = max(26, min(w, h) // (5 if winner else 4))
        logo.thumbnail((w - pad, h - pad), resample_filter())
        logo_x = x + (w - logo.width) // 2
        logo_y = y + (h - logo.height) // 2
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow.alpha_composite(logo, (logo_x + 4, logo_y + 6))
        shadow_alpha = shadow.split()[-1].point(lambda value: min(96, int(value * 0.48)))
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow.putalpha(shadow_alpha)
        if ImageFilter is not None:
            shadow = shadow.filter(ImageFilter.GaussianBlur(5))
        image.alpha_composite(shadow)
        image.alpha_composite(logo, (logo_x, logo_y))
    else:
        draw_reference_text(image, (x + 18, y + 26, w - 36, h - 70), short_team(team), "context", 34, 18, team_accent, max_lines=2, align="center")
        draw_reference_text(image, (x + 18, y + h - 58, w - 36, 38), "LOGO REVIEW", "context", 18, 12, PALETTE["ink"], max_lines=1, align="center")
    cue_fill = (18, 26, 40, 224) if result.get("approved") else (190, 39, 54, 232)
    cue_outline = (*team_accent, 186) if result.get("approved") else (255, 255, 255, 135)
    cue_w = min(w - 28, max(108, int(w * 0.62)))
    cue_h = 22
    cue_x = x + (w - cue_w) // 2
    cue_y = y + h - cue_h - 18
    draw.rounded_rectangle((cue_x, cue_y, cue_x + cue_w, cue_y + cue_h), radius=6, fill=cue_fill, outline=cue_outline, width=1)
    draw_reference_text(image, (cue_x + 8, cue_y + 3, cue_w - 16, cue_h - 4), approval_cue, "context", 10, 8, PALETTE["ink"], max_lines=1, align="center")
    return {
        "team": clean(team),
        "team_id": clean(result.get("team_id")),
        "status": clean(result.get("status")),
        "approved": bool(result.get("approved")),
        "asset_path": clean(result.get("path")),
        "render_method": clean(result.get("render_method")),
        "team_accent_hex": clean(result.get("team_accent_hex")),
        "team_accent_source": clean(result.get("team_accent_source")),
        "logo_approval_cue": approval_cue,
        "logo_review_required": bool(result.get("logo_review_required")),
    }


def team_visual_profile(team: str, aliases: Dict[str, str], logos: Dict[str, Dict[str, str]], fallback: tuple[int, int, int]) -> Dict[str, Any]:
    registry_accent, registry_accent_source = team_registry_accent(team, aliases, fallback)
    result = enrich_logo_result(load_team_logo(team, aliases, logos), registry_accent, registry_accent_source)
    accent = result.get("team_accent_rgb") if isinstance(result.get("team_accent_rgb"), tuple) else fallback
    return {
        "team": clean(team),
        "team_id": clean(result.get("team_id")),
        "accent_rgb": accent,
        "accent_hex": clean(result.get("team_accent_hex")) or rgb_to_hex(accent),
        "accent_source": clean(result.get("team_accent_source")),
        "logo_status": clean(result.get("status")),
        "logo_approval_cue": clean(result.get("logo_approval_cue")),
        "logo_review_required": bool(result.get("logo_review_required")),
    }


def draw_review_chrome(draw: Any, width: int, height: int, template: Dict[str, str], format_label: str) -> None:
    red = PALETTE["red"]
    gold = PALETTE["gold"]
    blue = PALETTE["blue"]
    ink = PALETTE["ink"]
    draw.rectangle((0, 0, width, 24), fill=blue)
    draw.rectangle((0, 24, width, 34), fill=gold)
    draw_rounded(draw, (54, 70, width - 54, 146), 0, (255, 255, 255), PALETTE["line"], 2)
    draw.text((82, 88), "HER SPORTS DAILY", font=font(30, True), fill=(24, 28, 36))
    draw_right_text(draw, width - 82, 88, "DRAFT REVIEW ONLY", font(28, True), red)
    draw_chip(draw, 82, 162, template["angle_label"], gold, (19, 31, 49), 22)
    draw_chip(draw, 82 + 132, 162, format_label.upper(), (232, 239, 249), PALETTE["blue"], 20)
    draw.rectangle((54, height - 64, width - 54, height - 36), fill=red)
    draw.text((70, height - 62), "NOT APPROVED - NOT PUBLISH READY - AUTO-RENDER OFF - AUTO-PUBLISH OFF", font=font(20, True), fill=ink)


def draw_brand_pattern(draw: Any, width: int, height: int, tone: str) -> None:
    deep = PALETTE["deep"]
    navy = PALETTE["navy"]
    cyan = PALETTE["cyan"]
    gold = PALETTE["gold"]
    draw.rectangle((0, 0, width, height), fill=deep)
    draw.polygon([(width * 0.58, 0), (width, 0), (width, height * 0.42), (width * 0.42, height * 0.18)], fill=navy)
    draw.polygon([(0, height * 0.36), (width * 0.32, height * 0.16), (width * 0.58, height), (0, height)], fill=(18, 39, 65))
    accent = cyan if tone != "result" else gold
    for offset in range(-160, width, 210):
        draw.line((offset, height - 150, offset + 380, 120), fill=accent, width=3)
    for x in range(72, width, 168):
        draw.ellipse((x, height - 310, x + 9, height - 301), fill=(255, 255, 255))


def draw_center_text(draw: Any, center_x: int, y: int, text: str, fnt: Any, fill: tuple[int, int, int]) -> None:
    width, _ = text_size(draw, text, fnt)
    draw.text((center_x - width // 2, y), text, font=fnt, fill=fill)


def fit_text_font(draw: Any, text: str, max_width: int, start_size: int, min_size: int = 28, bold: bool = True) -> Any:
    size = start_size
    while size > min_size:
        fnt = font(size, bold)
        if text_size(draw, text, fnt)[0] <= max_width:
            return fnt
        size -= 3
    return font(min_size, bold)


def draw_score_panel(draw: Any, x: int, y: int, w: int, h: int, team: str, score: str, *, winner: bool) -> None:
    fill = PALETTE["deep"] if winner else (255, 255, 255)
    outline = PALETTE["gold"] if winner else PALETTE["line"]
    text_fill = PALETTE["ink"] if winner else (23, 27, 36)
    muted_fill = PALETTE["gold"] if winner else PALETTE["muted"]
    draw_rounded(draw, (x, y, x + w, y + h), 18, fill, outline, 3)
    draw.text((x + 30, y + 28), "WINNER" if winner else "FINAL", font=font(23, True), fill=muted_fill)
    team_font = fit_text_font(draw, team.upper(), w - 240, 42, 28, True)
    draw.text((x + 30, y + 76), team.upper(), font=team_font, fill=text_fill)
    score_font = font(96 if h >= 180 else 78, True)
    draw_right_text(draw, x + w - 30, y + 48, score, score_font, text_fill)


def square_reference_spec() -> Dict[str, Any]:
    return {
        "template_id": "hsd_game_recap_final_score_a_square_review_derivative",
        "family": "game_recap_final_score",
        "variant": "A-square-review-derivative",
        "format": "square_review",
        "canvas": {"width": 1080, "height": 1080},
        "badge": {"asset": "official_hsd_badge_reference.png", "x": 48, "y": 42, "w": 80, "h": 80},
        "zones": {
            "title": {"x": 60, "y": 116, "w": 960, "h": 132},
            "context_row": {"x": 60, "y": 282, "w": 960, "h": 58},
            "primary_logo_slot": {"x": 70, "y": 376, "w": 190, "h": 190},
            "primary_team": {"x": 292, "y": 386, "w": 330, "h": 92},
            "primary_score": {"x": 642, "y": 350, "w": 360, "h": 235},
            "secondary_logo_slot": {"x": 70, "y": 612, "w": 190, "h": 190},
            "secondary_team": {"x": 292, "y": 636, "w": 330, "h": 86},
            "secondary_score": {"x": 692, "y": 602, "w": 260, "h": 190},
            "key_performer": {"x": 60, "y": 820, "w": 960, "h": 82},
            "hook_takeaway": {"x": 60, "y": 918, "w": 960, "h": 82},
        },
    }


def format_reference_spec(format_spec: Dict[str, Any], reference: Dict[str, Any]) -> Dict[str, Any]:
    if clean(format_spec.get("format_id")) == "square_feed_1x1":
        return square_reference_spec()
    loaded = load_reference_spec(reference)
    canvas = loaded.get("canvas") if isinstance(loaded.get("canvas"), dict) else {}
    if int(canvas.get("width", 0)) == int(format_spec.get("width", 0)) and int(canvas.get("height", 0)) == int(format_spec.get("height", 0)):
        return loaded
    return loaded or square_reference_spec()


def draw_context_divider(image: Any, box: Tuple[int, int, int, int], text: str) -> None:
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line((x, y + h - 6, x + w, y + h - 6), fill=(222, 161, 38, 210), width=3)
    draw_reference_text(image, (x, y, w, h - 12), text, "context", 34, 18, (247, 203, 84), max_lines=1, align="left")
    draw_reference_text(image, (x, y, w, h - 12), "REVIEW DRAFT", "context", 24, 14, (241, 238, 229), max_lines=1, align="right")


def draw_final_score_reference_title(image: Any, template_spec: Dict[str, Any], format_id: str) -> None:
    if ImageDraw is None:
        return
    title_x, title_y, title_w, title_h = zone_box(template_spec, "title")
    badge = template_spec.get("badge") if isinstance(template_spec.get("badge"), dict) else {}
    badge_right = int(badge.get("x", 48)) + max(int(badge.get("w", 80)), min(124, int(min(image.size) * 0.115)))
    left = max(title_x, badge_right + 38)
    right = title_x + title_w
    width = max(360, right - left)
    is_square = format_id == "square_feed_1x1"
    is_story = format_id == "ig_story_9x16"
    y = title_y + (-4 if not is_square else 0)
    h = max(92, title_h - (28 if is_square else 18))
    if is_square:
        draw = ImageDraw.Draw(image, "RGBA")
        line_gap = 4
        first = "GAME RECAP"
        second = "FINAL SCORE"
        first_font = reference_font("display", 54)
        second_font = reference_font("display", 46)
        for first_size in range(54, 35, -2):
            candidate_first = reference_font("display", first_size)
            if text_size(draw, first, candidate_first)[0] <= width:
                first_font = candidate_first
                break
        for second_size in range(46, 31, -2):
            candidate_second = reference_font("display", second_size)
            if text_size(draw, second, candidate_second)[0] <= width:
                second_font = candidate_second
                break
        first_w, first_h = text_size(draw, first, first_font)
        second_w, second_h = text_size(draw, second, second_font)
        total_h = first_h + second_h + line_gap
        y_cursor = y + max(0, (h - total_h) // 2) - 1
        draw.text((left, y_cursor), first, font=first_font, fill=PALETTE["ink"], stroke_width=2, stroke_fill=(0, 0, 0))
        draw.text((left, y_cursor + first_h + line_gap), second, font=second_font, fill=PALETTE["gold"], stroke_width=2, stroke_fill=(0, 0, 0))
        draw.line((left + max(first_w, second_w) + 22, y_cursor + total_h - 8, right, y_cursor + total_h - 8), fill=(*PALETTE["gold"], 150), width=2)
        return
    if is_story:
        first, second, start, minimum = "QUICK FINAL", "SCORE", 84, 44
    else:
        first, second, start, minimum = "GAME RECAP", "FINAL SCORE", 80, 42
    gap = 14 if not is_square else 24
    draw = ImageDraw.Draw(image, "RGBA")
    chosen = font(minimum, True)
    first_size = text_size(draw, first, chosen)
    second_size = text_size(draw, second, chosen)
    for size in range(start, minimum - 1, -2):
        candidate = font(size, True)
        candidate_first = text_size(draw, first, candidate)
        candidate_second = text_size(draw, second, candidate)
        if candidate_first[0] + gap + candidate_second[0] <= width and max(candidate_first[1], candidate_second[1]) <= h:
            chosen = candidate
            first_size = candidate_first
            second_size = candidate_second
            break
    text_h = max(first_size[1], second_size[1])
    y_cursor = y + max(0, (h - text_h) // 2) - (8 if not is_square else 2)
    draw.text((left, y_cursor), first, font=chosen, fill=PALETTE["ink"], stroke_width=2, stroke_fill=(0, 0, 0))
    draw.text((left + first_size[0] + gap, y_cursor), second, font=chosen, fill=PALETTE["gold"], stroke_width=2, stroke_fill=(0, 0, 0))


def draw_module_callouts(image: Any, box: Tuple[int, int, int, int], callouts: List[Dict[str, str]], accent: tuple[int, int, int], *, compact: bool = False) -> int:
    if not callouts:
        return 0
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    if compact:
        chip_w = min(132, max(92, w // 5))
        chip_h = 34
        gap = 8
        start_x = x + w - (chip_w + gap) * min(2, len(callouts)) + gap
        for index, item in enumerate(callouts[:2]):
            cx = start_x + index * (chip_w + gap)
            draw.rounded_rectangle((cx, y + 10, cx + chip_w, y + 10 + chip_h), radius=8, fill=(2, 4, 9, 170), outline=(*accent, 142), width=1)
            value_font = reference_font("context", 18)
            label_font = reference_font("context", 10)
            draw.text((cx + 9, y + 13), clean(item.get("value")), font=value_font, fill=PALETTE["ink"])
            draw.text((cx + 52, y + 17), clean(item.get("label")), font=label_font, fill=accent)
        return (chip_w + gap) * min(2, len(callouts))
    callout_w = min(280, max(210, w // 4))
    card_w = max(78, (callout_w - 20) // max(1, min(3, len(callouts))))
    top = y + max(18, h - 72)
    for index, item in enumerate(callouts[:3]):
        cx = x + w - callout_w + index * (card_w + 8)
        draw.rounded_rectangle((cx, top, cx + card_w, min(y + h - 16, top + 58)), radius=10, fill=(2, 4, 9, 182), outline=(*accent, 150), width=1)
        value_font = reference_font("score", 24)
        label_font = reference_font("context", 10)
        value = clean(item.get("value"))
        label = clean(item.get("label"))
        value_w, _ = text_size(draw, value, value_font)
        label_w, _ = text_size(draw, label, label_font)
        draw.text((cx + (card_w - value_w) // 2, top + 5), value, font=value_font, fill=PALETTE["ink"])
        draw.text((cx + (card_w - label_w) // 2, top + 34), label, font=label_font, fill=accent)
    return callout_w


def draw_premium_stat_chips(image: Any, chip_box: Tuple[int, int, int, int], callouts: List[Dict[str, str]], accent: tuple[int, int, int], *, compact: bool = False) -> int:
    if not callouts:
        return 0
    x, y, w, h = chip_box
    draw = ImageDraw.Draw(image, "RGBA")
    count = min(3, len(callouts))
    gap = 8 if compact else 10
    chip_w = max(66 if compact else 82, (w - gap * (count - 1)) // count)
    chip_h = max(42 if compact else 68, min(h - 8, 48 if compact else 76))
    top = y + max(3, (h - chip_h) // 2)
    for index, item in enumerate(callouts[:count]):
        cx = x + index * (chip_w + gap)
        value = clean(item.get("value"))
        label = clean(item.get("label"))
        is_primary = index == 0
        fill = (232, 186, 72, 234) if is_primary else (2, 4, 9, 196)
        outline = (248, 250, 255, 210) if is_primary else (*accent, 172)
        value_fill = (3, 5, 10) if is_primary else PALETTE["ink"]
        label_fill = (3, 5, 10) if is_primary else accent
        draw.rounded_rectangle((cx + 3, top + 5, cx + chip_w + 3, top + chip_h + 5), radius=10, fill=(0, 0, 0, 90))
        draw.rounded_rectangle((cx, top, cx + chip_w, top + chip_h), radius=10, fill=fill, outline=outline, width=1)
        value_font = reference_font("score", 26 if compact else (38 if is_primary else 32))
        label_font = reference_font("context", 9 if compact else 12)
        value_w, _ = text_size(draw, value, value_font)
        label_w, _ = text_size(draw, label, label_font)
        value_y = top + (2 if compact else 3)
        label_y = top + chip_h - (17 if compact else 21)
        draw.text((cx + (chip_w - value_w) // 2, value_y), value, font=value_font, fill=value_fill)
        draw.text((cx + (chip_w - label_w) // 2, label_y), label, font=label_font, fill=label_fill)
    return w


def prepared_athlete_photo(path: Path, target_w: int, target_h: int, *, crop_square: bool = False) -> Any:
    photo = Image.open(path).convert("RGBA")
    bbox = photo.getbbox()
    if bbox:
        photo = photo.crop(bbox)
    if crop_square:
        size = min(photo.width, photo.height)
        left = max(0, (photo.width - size) // 2)
        top = max(0, int((photo.height - size) * 0.18))
        photo = photo.crop((left, top, left + size, top + size))
    scale = max(target_w / max(1, photo.width), target_h / max(1, photo.height)) if crop_square else min(target_w / max(1, photo.width), target_h / max(1, photo.height))
    photo = photo.resize((max(1, int(photo.width * scale)), max(1, int(photo.height * scale))), resample_filter())
    return photo


def prepared_athlete_photo_fill(path: Path, target_w: int, target_h: int) -> Any:
    photo = Image.open(path).convert("RGBA")
    bbox = photo.getbbox()
    if bbox:
        photo = photo.crop(bbox)
    scale = max(target_w / max(1, photo.width), target_h / max(1, photo.height))
    photo = photo.resize((max(1, int(photo.width * scale)), max(1, int(photo.height * scale))), resample_filter())
    if photo.width > target_w:
        left = max(0, (photo.width - target_w) // 2)
        photo = photo.crop((left, 0, left + target_w, photo.height))
    if photo.height > target_h:
        top = max(0, int((photo.height - target_h) * 0.18))
        photo = photo.crop((0, top, target_w, top + target_h))
    return photo


def prepared_athlete_photo_focus_fill(path: Path, target_w: int, target_h: int, *, focus_y: float = 0.42) -> Any:
    photo = Image.open(path).convert("RGBA")
    bbox = photo.getbbox()
    if bbox:
        photo = photo.crop(bbox)
    scale = max(target_w / max(1, photo.width), target_h / max(1, photo.height))
    photo = photo.resize((max(1, int(photo.width * scale)), max(1, int(photo.height * scale))), resample_filter())
    if photo.width > target_w:
        left = max(0, (photo.width - target_w) // 2)
        photo = photo.crop((left, 0, left + target_w, photo.height))
    if photo.height > target_h:
        desired_focus_y = int(photo.height * max(0.18, min(0.64, focus_y)))
        top = max(0, min(photo.height - target_h, desired_focus_y - int(target_h * 0.40)))
        photo = photo.crop((0, top, target_w, top + target_h))
    return photo


def draw_approved_athlete_photo_tile(image: Any, box: Tuple[int, int, int, int], module: Dict[str, Any], accent: tuple[int, int, int], *, compact: bool = False) -> Tuple[int, str]:
    if clean(module.get("athlete_photo_status")) != "approved_local_headshot":
        return 0, "safe_no_photo_fallback"
    path = athlete_photo_render_source_path(module, "compact_square")
    if path is None or not path.exists() or Image is None:
        return 0, "safe_no_photo_fallback"
    x, y, w, h = box
    try:
        if not compact and h >= 130:
            slot_w = min(190, max(150, int(w * 0.18)))
            slot_h = min(h + 42, 198)
            left = x + 18
            top = y + h - slot_h + 14
            photo = prepared_athlete_photo(path, slot_w - 18, slot_h - 24, crop_square=False)
            layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer, "RGBA")
            card = (left, y + 12, left + slot_w, y + h - 12)
            draw.rounded_rectangle((card[0] + 5, card[1] + 7, card[2] + 5, card[3] + 7), radius=18, fill=(0, 0, 0, 120))
            draw.rounded_rectangle(card, radius=18, fill=(2, 4, 9, 170), outline=(*accent, 245), width=2)
            draw.polygon(
                [(card[0] + 10, card[3] - 22), (card[2] - 10, card[3] - 50), (card[2] - 10, card[3] - 10), (card[0] + 10, card[3] - 10)],
                fill=(*accent, 62),
            )
            glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow, "RGBA")
            glow_draw.ellipse((left - 26, top - 22, left + slot_w + 22, top + slot_h + 18), fill=(*accent, 48))
            if ImageFilter is not None:
                glow = glow.filter(ImageFilter.GaussianBlur(18))
            layer.alpha_composite(glow)
            photo_x = left + max(0, (slot_w - photo.width) // 2)
            photo_y = top + max(0, (slot_h - photo.height) // 2)
            layer.alpha_composite(photo, (photo_x, photo_y))
            draw.rounded_rectangle(card, radius=18, outline=(*accent, 245), width=2)
            image.alpha_composite(layer)
            draw_reference_text(image, (left + 10, y + h - 33, slot_w - 20, 18), "APPROVED PHOTO", "context", 10, 7, PALETTE["ink"], max_lines=1, align="center")
            return slot_w + 36, "premium_headshot_left"

        size = max(44 if compact else 84, min(h - 20, 62 if compact else 112))
        left = x + (14 if compact else 22)
        top = y + max(8, (h - size) // 2)
        photo = prepared_athlete_photo(path, size, size, crop_square=True)
        crop_left = max(0, (photo.width - size) // 2)
        crop_top = max(0, (photo.height - size) // 2)
        photo = photo.crop((crop_left, crop_top, crop_left + size, crop_top + size))
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer, "RGBA")
        radius = 10 if compact else 14
        draw.rounded_rectangle((left + 4, top + 5, left + size + 4, top + size + 5), radius=radius, fill=(0, 0, 0, 110))
        draw.rounded_rectangle((left, top, left + size, top + size), radius=radius, fill=(1, 3, 8, 235), outline=(*accent, 230), width=2)
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, size, size), radius=radius - 2, fill=255)
        layer.paste(photo, (left, top), mask)
        draw.rounded_rectangle((left, top, left + size, top + size), radius=radius, outline=(*accent, 245), width=2)
        image.alpha_composite(layer)
        if not compact:
            draw_reference_text(image, (left, top + size - 19, size, 16), "APPROVED PHOTO", "context", 9, 7, PALETTE["ink"], max_lines=1, align="center")
        return size + (34 if compact else 42), "compact_headshot_chip"
    except Exception:
        return 0, "safe_no_photo_fallback"


def draw_verified_stat_reference_module(image: Any, box: Tuple[int, int, int, int], module: Dict[str, Any], accent: tuple[int, int, int]) -> None:
    x, y, w, h = box
    compact = h < 112
    draw_reference_panel(image, box, accent, fill=(2, 4, 9, 232), radius=16 if not compact else 12, width=2)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((x + 2, y + 2, x + 10, y + h - 2), fill=(*accent, 235))
    draw.line((x + 24, y + 38, x + w - 24, y + 38), fill=(*accent, 96), width=1)
    player = clean(module.get("player_name"))
    matchup = clean(module.get("matchup_note"))
    source_label = "VERIFIED STAT TEXT"
    photo_offset, photo_layout_mode = draw_approved_athlete_photo_tile(image, box, module, accent, compact=compact)
    module["athlete_photo_layout_mode"] = photo_layout_mode
    if compact:
        chip_w = min(210, max(148, w // 4))
        text_x = x + 24 + photo_offset
        text_w = max(260, w - chip_w - 62 - photo_offset)
        draw_premium_stat_chips(image, (x + w - chip_w - 20, y + 8, chip_w, h - 16), module.get("callouts") or [], accent, compact=True)
        draw_reference_text(image, (text_x, y + 8, text_w, 22), f"{clean(module.get('eyebrow'))} / {source_label}", "context", 15, 10, accent, max_lines=1)
        draw_reference_text(image, (text_x, y + 30, text_w, 32), clean(module.get("headline")), "display", 28, 17, PALETTE["ink"], max_lines=1)
        draw_reference_text(image, (text_x, y + 58, text_w, max(18, h - 60)), matchup or clean(module.get("body")), "body", 15, 10, (218, 226, 238), max_lines=1, uppercase=False)
        return

    chip_w = min(310, max(250, w // 3))
    text_x = x + 28 + photo_offset
    text_w = max(360, w - chip_w - 72 - photo_offset)
    pill_text = f"{source_label} / {matchup}" if matchup else source_label
    draw_reference_text(image, (text_x, y + 14, text_w, 24), clean(module.get("eyebrow")), "context", 22, 12, accent, max_lines=1)
    draw_reference_text(image, (text_x + 182, y + 15, max(90, text_w - 190), 22), pill_text, "context", 14, 9, (218, 226, 238), max_lines=1)
    draw_reference_text(image, (text_x, y + 46, text_w, 48), clean(module.get("headline")), "display", 42, 24, PALETTE["ink"], max_lines=1)
    editorial = clean(module.get("editorial_line")) or clean(module.get("body"))
    draw_reference_text(image, (text_x, y + 94, text_w, max(34, h - 98)), editorial, "body", 24, 13, (235, 239, 247), max_lines=2, uppercase=False)
    draw_premium_stat_chips(image, (x + w - chip_w - 22, y + 48, chip_w, h - 62), module.get("callouts") or [], accent, compact=False)
    if player:
        draw_reference_text(image, (x + w - chip_w - 22, y + 15, chip_w, 24), player, "context", 16, 10, accent, max_lines=1, align="center", uppercase=False)


def approved_athlete_photo_path(module: Dict[str, Any]) -> Path | None:
    if clean(module.get("athlete_photo_status")) != "approved_local_headshot":
        return None
    path = project_path(module.get("athlete_photo_path"))
    if not path.exists() or Image is None:
        return None
    return path


def photo_first_eligible(module: Dict[str, Any]) -> bool:
    if clean(module.get("athlete_photo_status")) != "approved_local_headshot":
        return False
    if clean(module.get("athlete_photo_identity_review_status")) == "hold_identity_resolution_required":
        return False
    if clean(module.get("athlete_photo_identity_resolution_status")) in {"identity_resolution_not_cleared", "resolution_incomplete_or_hold"}:
        return False
    if clean(module.get("athlete_photo_blocker")):
        return False
    return approved_athlete_photo_path(module) is not None


def athlete_photo_review_variant_path(module: Dict[str, Any], variant_id: str) -> Path | None:
    if clean(module.get("athlete_photo_status")) != "approved_local_headshot":
        return None
    if clean(module.get("athlete_photo_review_variant_status")) != "review_variant_available":
        return None
    if clean(module.get("athlete_photo_review_variant_policy")) != "derived_variant_does_not_approve_move_publish_or_mark_publish_ready":
        return None
    key = {
        "photo_first_story": "athlete_photo_review_variant_story_path",
        "compact_square": "athlete_photo_review_variant_square_path",
    }.get(variant_id, "athlete_photo_review_variant_feed_path")
    path = project_path(module.get(key))
    if not path.exists() or Image is None:
        return None
    return path


def athlete_photo_render_source_path(module: Dict[str, Any], variant_id: str) -> Path | None:
    return athlete_photo_review_variant_path(module, variant_id) or approved_athlete_photo_path(module)


def photo_first_layout_geometry(format_spec: Dict[str, Any]) -> Dict[str, Any]:
    width, height = int(format_spec.get("width", 1080)), int(format_spec.get("height", 1350))
    is_story = height > 1500
    if is_story:
        photo_box = [72, 505, 410, 710]
        score_top = 520
        score_h = 206
        stat_box = [72, 1246, 936, 168]
        hook_box = [72, 1440, 936, 172]
    else:
        photo_box = [58, 372, 408, 590]
        score_top = 398
        score_h = 176
        stat_box = [58, 990, 964, 132]
        hook_box = [58, 1148, 964, 112]
    score_x = photo_box[0] + photo_box[2] + 28
    score_w = width - score_x - photo_box[0]
    winner_row = [score_x, score_top, score_w, score_h]
    loser_row = [score_x, score_top + score_h + 24, score_w, score_h - 16]
    context_box = [score_x, score_top + score_h * 2 + 36, score_w, 54]
    return {
        "template_family": "approved_athlete_photo_final_score",
        "format_id": clean(format_spec.get("format_id")),
        "photo_stage_box": photo_box,
        "photo_face_focus_box": [photo_box[0] + 48, photo_box[1] + int(photo_box[3] * 0.34), photo_box[2] - 96, int(photo_box[3] * 0.32)],
        "winner_score_row_box": winner_row,
        "loser_score_row_box": loser_row,
        "score_context_box": context_box,
        "stat_strip_box": stat_box,
        "matchup_angle_box": hook_box,
        "minimum_clearance_px": 24,
        "text_clearance_policy": "photo-first stage, score lanes, stat strip, and matchup module must remain visually separated; human review still required.",
    }


def tuple_box(raw: List[int]) -> Tuple[int, int, int, int]:
    return int(raw[0]), int(raw[1]), int(raw[2]), int(raw[3])


def draw_photo_first_athlete_stage(image: Any, box: Tuple[int, int, int, int], module: Dict[str, Any], accent: tuple[int, int, int], focus_box: Tuple[int, int, int, int] | None = None) -> bool:
    _x, _y, _w, h = box
    variant_id = "photo_first_story" if h > 650 else "photo_first_feed"
    path = athlete_photo_render_source_path(module, variant_id)
    if path is None:
        return False
    x, y, w, h = box
    try:
        focus_y = 0.42
        if focus_box:
            _fx, fy, _fw, fh = focus_box
            focus_y = ((fy + fh / 2) - y) / max(1, h)
        photo = prepared_athlete_photo_focus_fill(path, w - 28, h - 72, focus_y=focus_y)
    except Exception:
        return False
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((x + 12, y + 14, x + w + 12, y + h + 14), radius=30, fill=(0, 0, 0, 130))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=30, fill=(2, 4, 9, 206), outline=(*accent, 230), width=3)
    draw.rectangle((x, y + 34, x + 10, y + h - 32), fill=(*accent, 206))
    draw.polygon([(x + 28, y + h - 152), (x + w - 20, y + h - 244), (x + w - 20, y + h - 20), (x + 28, y + h - 20)], fill=(*accent, 54))
    draw.polygon([(x + 44, y + 92), (x + w - 26, y + 36), (x + w - 26, y + 112), (x + 44, y + 166)], fill=(255, 255, 255, 12))
    draw.line((x + 30, y + 30, x + w - 28, y + 30), fill=(*accent, 176), width=3)
    draw.line((x + 30, y + h - 78, x + w - 28, y + h - 78), fill=(*accent, 104), width=2)
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((x - 80, y + 26, x + w + 80, y + h + 92), fill=(*accent, 50))
    if ImageFilter is not None:
        glow = glow.filter(ImageFilter.GaussianBlur(30))
    layer.alpha_composite(glow)
    photo_x = x + 14 + max(0, (w - 28 - photo.width) // 2)
    photo_y = y + h - photo.height - 42
    stage_photo = Image.new("RGBA", image.size, (0, 0, 0, 0))
    stage_photo.alpha_composite(photo, (photo_x, photo_y))
    stage_mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(stage_mask)
    mask_draw.rounded_rectangle((x + 14, y + 38, x + w - 14, y + h - 18), radius=22, fill=255)
    layer.alpha_composite(Image.composite(stage_photo, Image.new("RGBA", image.size, (0, 0, 0, 0)), stage_mask))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=26, outline=(*accent, 228), width=3)
    label_w = min(w - 42, 234)
    draw.rounded_rectangle((x + 22, y + h - 58, x + 22 + label_w, y + h - 20), radius=8, fill=(3, 5, 10, 232), outline=(248, 250, 255, 150), width=1)
    image.alpha_composite(layer)
    player = clean(module.get("player_name")) or "APPROVED ATHLETE"
    variant_label = "APPROVED SOURCE / REVIEW CROP" if clean(module.get("athlete_photo_review_variant_status")) == "review_variant_available" else "APPROVED PHOTO"
    draw_reference_text(image, (x + 36, y + 28, w - 72, 42), "PLAYER FOCUS", "context", 19, 10, accent, max_lines=1, align="left")
    draw_reference_text(image, (x + 36, y + 58, w - 72, 42), player, "context", 26, 14, PALETTE["ink"], max_lines=1, align="left", uppercase=False)
    draw_reference_text(image, (x + 30, y + h - 52, label_w - 16, 28), variant_label, "context", 13, 8, accent, max_lines=1, align="center")
    return True


def draw_photo_first_score_row(
    image: Any,
    box: Tuple[int, int, int, int],
    team: str,
    score_value: str,
    accent: tuple[int, int, int],
    aliases: Dict[str, str],
    logos: Dict[str, Dict[str, str]],
    *,
    winner: bool = False,
) -> None:
    x, y, w, h = box
    draw_reference_panel(image, box, accent, fill=(2, 4, 9, 226 if winner else 210), radius=18, width=2)
    draw = ImageDraw.Draw(image, "RGBA")
    label = "WINNER" if winner else "FINAL"
    label_w = 96 if winner else 74
    draw.rounded_rectangle((x + 20, y + 16, x + 20 + label_w, y + 42), radius=7, fill=(*accent, 230), outline=(248, 250, 255, 128), width=1)
    draw_reference_text(image, (x + 29, y + 19, label_w - 18, 20), label, "context", 12, 8, (2, 4, 9), max_lines=1, align="center")
    logo_size = min(h - 30, 104 if winner else 92)
    logo_box = (x + 22, y + (h - logo_size) // 2 + 10, logo_size, logo_size)
    draw_team_logo_slot(image, team, logo_box, aliases, logos, accent, winner=winner)
    draw_reference_text(image, (x + logo_size + 52, y + 48, max(220, w - logo_size - 232), h - 68), short_team(team), "context", 40 if winner else 34, 17, PALETTE["ink"] if winner else (216, 224, 238), max_lines=2, stroke=1, stroke_fill=(0, 0, 0))
    score_box = (x + w - 178, y - 6, 150, h + 14)
    draw.rounded_rectangle((score_box[0] - 14, y + 18, x + w - 18, y + h - 18), radius=18, fill=(255, 255, 255, 18), outline=(*accent, 92), width=1)
    draw_reference_text(image, score_box, score_value, "score", 114 if winner else 96, 52, PALETTE["ink"], max_lines=1, align="right", stroke=2, stroke_fill=(0, 0, 0))


def draw_photo_first_stat_strip(image: Any, box: Tuple[int, int, int, int], module: Dict[str, Any], accent: tuple[int, int, int]) -> None:
    x, y, w, h = box
    draw_reference_panel(image, box, accent, fill=(2, 4, 9, 232), radius=16, width=2)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((x + 2, y + 2, x + 11, y + h - 2), fill=(*accent, 238))
    chip_w = min(338, max(260, w // 3))
    draw_premium_stat_chips(image, (x + w - chip_w - 22, y + 18, chip_w, h - 36), module.get("callouts") or [], accent, compact=h < 132)
    player = clean(module.get("player_name"))
    source_label = "VERIFIED STAT TEXT"
    heading = clean(module.get("headline")) or (f"{last_name(player)} LEDGER" if player else "PLAYER LEDGER")
    text_w = max(390, w - chip_w - 72)
    draw_reference_text(image, (x + 28, y + 15, text_w, 24), f"PHOTO-FIRST / {source_label}", "context", 19, 11, accent, max_lines=1)
    draw_reference_text(image, (x + 28, y + 42, text_w, 46), heading, "display", 40, 22, PALETTE["ink"], max_lines=1)
    draw_reference_text(image, (x + 28, y + 88, text_w, max(34, h - 94)), clean(module.get("editorial_line")) or clean(module.get("body")), "body", 23, 13, (235, 239, 247), max_lines=2, uppercase=False)


def draw_photo_first_final_score_template(
    image: Any,
    packet: Dict[str, Any],
    template: Dict[str, str],
    format_spec: Dict[str, Any],
    score: Dict[str, str],
    reference: Dict[str, Any],
    stat_module: Dict[str, Any],
) -> bool:
    template_spec = format_reference_spec(format_spec, reference)
    width, height = int(format_spec["width"]), int(format_spec["height"])
    aliases, logos = team_registry()
    winner_profile = team_visual_profile(score["winner"], aliases, logos, (247, 203, 84))
    loser_profile = team_visual_profile(score["loser"], aliases, logos, (37, 99, 163))
    winner_accent = winner_profile["accent_rgb"]
    loser_accent = loser_profile["accent_rgb"]
    format_id = clean(format_spec.get("format_id"))
    is_story = height > 1500

    draw_reference_background(image, "final", winner_accent, loser_accent, photo_first=True)
    draw_reference_badge(image, template_spec)
    draw_final_score_reference_title(image, template_spec, format_id)
    draw_context_divider(image, zone_box(template_spec, "context_row"), "FINAL / WNBA / PHOTO-FIRST DRAFT")
    geometry = photo_first_layout_geometry(format_spec)
    photo_box = tuple_box(geometry["photo_stage_box"])
    focus_box = tuple_box(geometry["photo_face_focus_box"])
    winner_box = tuple_box(geometry["winner_score_row_box"])
    loser_box = tuple_box(geometry["loser_score_row_box"])
    context_box = tuple_box(geometry["score_context_box"])
    stat_box = tuple_box(geometry["stat_strip_box"])
    hook_box = tuple_box(geometry["matchup_angle_box"])

    photo_ok = draw_photo_first_athlete_stage(image, photo_box, stat_module, winner_accent, focus_box)
    if not photo_ok:
        return False

    draw_photo_first_score_row(image, winner_box, score["winner"], score["winner_score"], winner_accent, aliases, logos, winner=True)
    draw_photo_first_score_row(image, loser_box, score["loser"], score["loser_score"], loser_accent, aliases, logos, winner=False)

    total = score_total(score)
    context_parts = [clean(stat_module.get("matchup_note"))]
    if total is not None:
        context_parts.append(f"{total} pts")
    draw_reference_text(image, context_box, " / ".join([part for part in context_parts if part]), "context", 25 if is_story else 27, 13, winner_accent, max_lines=1)

    draw_photo_first_stat_strip(image, stat_box, stat_module, winner_accent)
    microcopy = selected_editorial_microcopy(packet, score, stat_module)
    prompt_body = f"{clean(microcopy.get('context'))}. {clean(microcopy.get('body'))}"
    draw_lower_reference_module(
        image,
        hook_box,
        clean(microcopy.get("eyebrow")) or "MATCHUP ANGLE",
        prompt_body,
        loser_accent,
        headline=clean(microcopy.get("headline")) or review_prompt(score),
    )
    draw_reference_guardrail(image)
    return True


def draw_lower_reference_module(image: Any, box: Tuple[int, int, int, int], eyebrow: str, body: str, accent: tuple[int, int, int], *, headline: str = "", callouts: List[Dict[str, str]] | None = None) -> None:
    x, y, w, h = box
    compact = h <= 122
    draw_reference_panel(image, box, accent, fill=(2, 4, 9, 218), radius=14, width=2)
    callout_w = draw_module_callouts(image, (x + 18, y, w - 36, h), callouts or [], accent, compact=compact)
    text_w = max(220, w - 48 - (callout_w if compact else min(callout_w + 10, w // 3)))
    draw_reference_text(image, (x + 24, y + 10, text_w, min(30 if compact else 34, h - 16)), eyebrow, "context", 20 if compact else 24, 12, accent, max_lines=1)
    body_top = y + (38 if compact else 48)
    if headline:
        draw_reference_text(
            image,
            (x + 24, body_top, text_w, min(34 if compact else 44, h - 42)),
            headline,
            "display",
            27 if compact else 38,
            16,
            PALETTE["ink"],
            max_lines=1,
        )
        body_top += 30 if compact else 48
    if compact and y + h - body_top < 24:
        return
    draw_reference_text(
        image,
        (x + 24, body_top, text_w, max(28, y + h - body_top - 14)),
        body,
        "body",
        18 if compact else 27,
        12 if compact else 14,
        PALETTE["ink"],
        max_lines=1 if compact else 2,
        uppercase=False,
    )


def draw_score_lanes(image: Any, template_spec: Dict[str, Any], primary_accent: tuple[int, int, int], secondary_accent: tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    lane_pairs = [
        ("primary_logo_slot", "primary_score", (3, 5, 10, 176), (*primary_accent, 198)),
        ("secondary_logo_slot", "secondary_score", (3, 5, 10, 168), (*secondary_accent, 185)),
    ]
    for logo_name, score_name, fill, accent in lane_pairs:
        lx, ly, lw, lh = zone_box(template_spec, logo_name)
        sx, sy, sw, sh = zone_box(template_spec, score_name)
        if not lw or not sw:
            continue
        x1 = max(30, min(lx, sx) - 12)
        y1 = max(0, min(ly, sy) + 12)
        x2 = min(image.size[0] - 30, max(lx + lw, sx + sw) + 10)
        y2 = min(image.size[1], max(ly + lh, sy + sh) - 10)
        lane_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        lane_draw = ImageDraw.Draw(lane_layer, "RGBA")
        lane_draw.rounded_rectangle((x1 + 8, y1 + 10, x2 + 8, y2 + 10), radius=22, fill=(0, 0, 0, 94))
        lane_draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=fill, outline=accent, width=2)
        lane_draw.rectangle((x1, y1 + 4, x1 + 12, y2 - 4), fill=accent)
        lane_draw.rounded_rectangle((x1 + 6, y1 + 6, x2 - 6, y1 + 42), radius=17, fill=(255, 255, 255, 10))
        lane_draw.line((x1 + max(190, lw + 28), y1 + 26, x1 + max(190, lw + 28), y2 - 24), fill=(255, 255, 255, 36), width=1)
        lane_draw.line((x1 + 22, y2 - 11, x2 - 22, y2 - 11), fill=accent, width=2)
        image.alpha_composite(lane_layer)


def draw_reference_final_score_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], format_spec: Dict[str, Any], score: Dict[str, str], reference: Dict[str, Any]) -> None:
    template_spec = format_reference_spec(format_spec, reference)
    width, height = int(format_spec["width"]), int(format_spec["height"])
    aliases, logos = team_registry()
    winner_profile = team_visual_profile(score["winner"], aliases, logos, (247, 203, 84))
    loser_profile = team_visual_profile(score["loser"], aliases, logos, (37, 99, 163))
    winner_accent = winner_profile["accent_rgb"]
    loser_accent = loser_profile["accent_rgb"]
    stat_module = select_verified_stat_module(packet, score)
    format_id = clean(format_spec.get("format_id"))
    if (
        format_id != "square_feed_1x1"
        and clean(stat_module.get("status")) in {"verified_player_stat_module", "verified_supporting_stat_module"}
        and photo_first_eligible(stat_module)
        and draw_photo_first_final_score_template(image, packet, template, format_spec, score, reference, stat_module)
    ):
        return

    draw_reference_background(image, "final", winner_accent, loser_accent)
    draw_reference_badge(image, template_spec)

    draw_final_score_reference_title(image, template_spec, format_id)

    context_box = zone_box(template_spec, "context_row")
    draw_context_divider(image, context_box, "FINAL / WNBA / SOURCE CHECKED")
    draw_score_lanes(image, template_spec, winner_accent, loser_accent)

    draw_team_logo_slot(image, score["winner"], zone_box(template_spec, "primary_logo_slot"), aliases, logos, winner_accent, winner=True)
    draw_team_logo_slot(image, score["loser"], zone_box(template_spec, "secondary_logo_slot"), aliases, logos, loser_accent, winner=False)

    primary_team_size = 54 if format_id == "square_feed_1x1" else 58
    secondary_team_size = 42 if format_id == "square_feed_1x1" else 46
    primary_score_size = 220 if format_id == "square_feed_1x1" else (238 if height <= 1350 else 254)
    secondary_score_size = 158 if format_id == "square_feed_1x1" else (176 if height <= 1350 else 188)
    draw_reference_text(image, zone_box(template_spec, "primary_team"), short_team(score["winner"]), "context", primary_team_size, 24, PALETTE["ink"], max_lines=2, stroke=1, stroke_fill=(0, 0, 0))
    draw_reference_text(image, zone_box(template_spec, "secondary_team"), short_team(score["loser"]), "context", secondary_team_size, 22, (204, 210, 222), max_lines=2, stroke=1, stroke_fill=(0, 0, 0))
    draw_reference_text(image, zone_box(template_spec, "primary_score"), score["winner_score"], "score", primary_score_size, 88, PALETTE["ink"], max_lines=1, align="right", stroke=3, stroke_fill=(0, 0, 0))
    draw_reference_text(image, zone_box(template_spec, "secondary_score"), score["loser_score"], "score", secondary_score_size, 72, PALETTE["ink"], max_lines=1, align="right", stroke=2, stroke_fill=(0, 0, 0))

    edge = game_edge_module(score)
    stat_status = clean(stat_module.get("status"))
    module = stat_module if stat_status in {"verified_player_stat_module", "verified_supporting_stat_module"} else edge
    callouts = stat_module.get("callouts") if stat_status in {"verified_player_stat_module", "verified_supporting_stat_module"} else final_score_callouts(packet, score)
    key_box = zone_box(template_spec, "key_performer")
    if stat_status in {"verified_player_stat_module", "verified_supporting_stat_module"}:
        draw_verified_stat_reference_module(image, key_box, stat_module, (247, 203, 84))
    else:
        draw_lower_reference_module(
            image,
            key_box,
            clean(module.get("eyebrow")) or "GAME EDGE",
            clean(module.get("body")),
            (247, 203, 84),
            headline=clean(module.get("headline")),
            callouts=callouts,
        )

    hook_name = "hook_question" if zone_box(template_spec, "hook_question") != (0, 0, 0, 0) else "hook_takeaway"
    hook_box = zone_box(template_spec, hook_name)
    dek = clean(packet.get("copy_dek"))
    if not dek:
        dek = f"Verified final: {score['winner']} {score['winner_score']}, {score['loser']} {score['loser_score']}."
    prompt = review_prompt(score)
    microcopy = selected_editorial_microcopy(packet, score, stat_module)
    prompt_body = clean(microcopy.get("body")) or dek
    source_body = f"{clean(microcopy.get('context'))}. {prompt_body}"
    draw_lower_reference_module(
        image,
        hook_box,
        clean(microcopy.get("eyebrow")) or "YOUR TAKE",
        source_body,
        (37, 99, 163),
        headline=clean(microcopy.get("headline")) or prompt,
    )

    draw_reference_guardrail(image)


def draw_final_score_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any], score: Dict[str, str]) -> None:
    width, height = spec["width"], spec["height"]
    reference = reference_for_format(spec, template)
    if reference:
        draw_reference_final_score_template(image, packet, template, spec, score, reference)
        return
    draw = ImageDraw.Draw(image)
    draw_brand_pattern(draw, width, height, "result")
    draw_review_chrome(draw, width, height, template, clean(spec["format_id"]).replace("_", " "))

    source = clean(packet.get("source_artifact")) or "source proof required"
    confidence = clean(packet.get("source_cue")) or "source review required"
    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Verified source review required."
    is_story = height > 1500
    is_square = height <= 1100

    content_top = 228
    content_bottom = height - 104
    left = 54
    right = width - 54
    card_h = content_bottom - content_top
    draw_rounded(draw, (left, content_top, right, content_bottom), 22, PALETTE["paper"], (255, 255, 255), 2)
    draw.rectangle((left, content_top, left + 22, content_bottom), fill=PALETTE["gold"])

    text_left = 92
    text_right = right - 48
    y = content_top + (58 if not is_square else 44)
    draw.text((text_left, y), "FINAL SCORE", font=font(32, True), fill=PALETTE["blue"])
    draw_right_text(draw, text_right, y, "VERIFIED", font(24, True), PALETTE["muted"])
    y += 60

    hero_font = font(64 if not is_square else 56, True)
    y = draw_text_block(draw, (text_left, y), f"{score['winner']} {score['verb']} {score['loser']}", hero_font, (22, 26, 36), text_right - text_left, 3, 10)
    y += 34

    panel_h = 178 if not is_square else 145
    gap = 18
    draw_score_panel(draw, text_left, y, text_right - text_left, panel_h, score["winner"], score["winner_score"], winner=True)
    y += panel_h + gap
    draw_score_panel(draw, text_left, y, text_right - text_left, panel_h, score["loser"], score["loser_score"], winner=False)
    y += panel_h + (42 if is_story else 30)

    if not is_square:
        note_h = min(260, content_bottom - y - 34)
        if note_h >= 110:
            draw_rounded(draw, (text_left, y, text_right, y + note_h), 0, (255, 255, 255), PALETTE["line"], 2)
            draw.text((text_left + 24, y + 24), "Review evidence", font=font(25, True), fill=(24, 28, 36))
            note_y = y + 70
            evidence = [
                f"Source: {source}",
                f"Confidence: {confidence}",
                f"Context: {context}",
            ]
            for item in evidence:
                note_y = draw_text_block(draw, (text_left + 24, note_y), item, font(22, False), PALETTE["muted"], text_right - text_left - 48, 1, 7)
                note_y += 2
            if is_story:
                callout_top = y + note_h + 56
                callout_bottom = min(content_bottom - 54, callout_top + 300)
                if callout_bottom - callout_top >= 220:
                    draw_rounded(draw, (text_left, callout_top, text_right, callout_bottom), 18, PALETTE["deep"], PALETTE["gold"], 3)
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 34, "FINAL", font(34, True), PALETTE["gold"])
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 86, f"{score['winner_score']} - {score['loser_score']}", font(124, True), PALETTE["ink"])
                    draw_center_text(draw, (text_left + text_right) // 2, callout_top + 226, "REVIEW ONLY DRAFT", font(25, True), PALETTE["gold"])
    else:
        chip_y = min(y, content_bottom - 74)
        draw_chip(draw, text_left, chip_y, f"SOURCE: {source}".upper(), (232, 239, 249), PALETTE["blue"], 19)
        draw_chip(draw, text_left + 320, chip_y, "REVIEW ONLY", PALETTE["gold"], (19, 31, 49), 19)


def content_module_summary(packet: Dict[str, Any], template: Dict[str, str]) -> Dict[str, Any]:
    score = parse_final_score(packet) if clean(template.get("tone")) == "result" else {}
    if not score:
        return {"content_module_mode": "not_final_score", "content_module_status": "not_applicable"}
    stat_module = select_verified_stat_module(packet, score)
    microcopy = selected_editorial_microcopy(packet, score, stat_module)
    if clean(stat_module.get("status")) in {"verified_player_stat_module", "verified_supporting_stat_module"}:
        return {
            "content_module_mode": "verified_player_stats",
            "content_module_status": clean(stat_module.get("status")),
            "content_module_title": clean(stat_module.get("headline")),
            "content_module_body": clean(stat_module.get("body")),
            "content_module_editorial_line": clean(stat_module.get("editorial_line")),
            "content_module_matchup_note": clean(stat_module.get("matchup_note")),
            "content_module_game_shape": clean(stat_module.get("game_shape")),
            "content_module_game_shape_label": clean(stat_module.get("game_shape_label")),
            "content_module_stat_strength": clean(stat_module.get("stat_strength")),
            "content_module_stat_count": str(len(stat_module.get("callouts") or [])),
            "content_module_player": clean(stat_module.get("player_name")),
            "content_module_source_text": clean(stat_module.get("source_text")),
            "athlete_photo_status": clean(stat_module.get("athlete_photo_status")),
            "athlete_photo_path": clean(stat_module.get("athlete_photo_path")),
            "athlete_photo_approval_marker_path": clean(stat_module.get("athlete_photo_approval_marker_path")),
            "athlete_photo_approval_cue": clean(stat_module.get("athlete_photo_approval_cue")),
            "athlete_photo_review_required": str(bool(stat_module.get("athlete_photo_review_required"))).lower(),
            "athlete_photo_blocker": clean(stat_module.get("athlete_photo_blocker")),
            "athlete_photo_render_method": clean(stat_module.get("athlete_photo_render_method")),
            "athlete_photo_policy": clean(stat_module.get("athlete_photo_policy")),
            "athlete_photo_approved_at_utc": clean(stat_module.get("athlete_photo_approved_at_utc")),
            "athlete_photo_review_variant_status": clean(stat_module.get("athlete_photo_review_variant_status")),
            "athlete_photo_review_variant_feed_path": clean(stat_module.get("athlete_photo_review_variant_feed_path")),
            "athlete_photo_review_variant_story_path": clean(stat_module.get("athlete_photo_review_variant_story_path")),
            "athlete_photo_review_variant_square_path": clean(stat_module.get("athlete_photo_review_variant_square_path")),
            "athlete_photo_review_variant_metadata_source": clean(stat_module.get("athlete_photo_review_variant_metadata_source")),
            "athlete_photo_review_variant_policy": clean(stat_module.get("athlete_photo_review_variant_policy")),
            "athlete_photo_review_variant_crop_readiness_score": clean(stat_module.get("athlete_photo_review_variant_crop_readiness_score")),
            "athlete_photo_identity_review_status": clean(stat_module.get("athlete_photo_identity_review_status")),
            "athlete_photo_identity_issue_count": clean(stat_module.get("athlete_photo_identity_issue_count")),
            "athlete_photo_identity_high_issue_count": clean(stat_module.get("athlete_photo_identity_high_issue_count")),
            "athlete_photo_identity_issue_codes": clean(stat_module.get("athlete_photo_identity_issue_codes")),
            "athlete_photo_identity_resolution_status": clean(stat_module.get("athlete_photo_identity_resolution_status")),
            "athlete_photo_identity_resolution_decision": clean(stat_module.get("athlete_photo_identity_resolution_decision")),
            "athlete_photo_identity_resolution_source_file": clean(stat_module.get("athlete_photo_identity_resolution_source_file")),
            "athlete_photo_identity_resolution_evidence_url": clean(stat_module.get("athlete_photo_identity_resolution_evidence_url")),
            "athlete_photo_layout_options": clean(stat_module.get("athlete_photo_layout_options")),
            "athlete_photo_template_family": "approved_athlete_photo_final_score"
            if clean(stat_module.get("athlete_photo_status")) == "approved_local_headshot"
            else "logo_first_final_score_fallback",
            "athlete_photo_template_policy": "Approved local athlete photo can become the main editorial visual only in review-only feed/story formats; square and unsafe cases keep compact or logo-first fallbacks.",
            "content_module_fallback_label": "",
            "stat_source_confidence": clean(stat_module.get("stat_source_confidence")),
            "stat_source_label": clean(stat_module.get("stat_source_label")),
            "stat_review_cue": clean(stat_module.get("stat_review_cue")),
            "editorial_microcopy_status": clean(microcopy.get("status")),
            "editorial_microcopy_variant": clean(microcopy.get("selected_variant_id")),
            "editorial_microcopy_headline": clean(microcopy.get("headline")),
            "editorial_microcopy_body": clean(microcopy.get("body")),
            "editorial_microcopy_context": clean(microcopy.get("context")),
            "editorial_microcopy_game_shape": clean(microcopy.get("game_shape")),
            "editorial_microcopy_game_shape_label": clean(microcopy.get("game_shape_label")),
            "editorial_microcopy_review_cue": clean(microcopy.get("review_cue")),
            "editorial_microcopy_variants": microcopy.get("variants") or [],
        }
    edge = game_edge_module(score)
    return {
        "content_module_mode": "game_edge_fallback",
        "content_module_status": clean(stat_module.get("status")) or "fallback_game_edge_no_verified_stat_text",
        "content_module_title": clean(edge.get("headline")),
        "content_module_body": clean(edge.get("body")),
        "content_module_game_shape": clean(edge.get("game_shape")),
        "content_module_game_shape_label": clean(edge.get("game_shape_label")),
        "content_module_stat_count": "0",
        "content_module_player": "",
        "content_module_source_text": "",
        "athlete_photo_status": "athlete_photo_not_applicable",
        "athlete_photo_approval_cue": "NO PLAYER SELECTED",
        "athlete_photo_review_required": "true",
        "athlete_photo_blocker": "No verified player/stat module selected for this final-score draft.",
        "athlete_photo_template_family": "logo_first_final_score_fallback",
        "athlete_photo_template_policy": "No approved player photo is available; keep logo-first score layout and manual review guardrails.",
        "content_module_fallback_label": clean(edge.get("eyebrow")) or "SCORE-DERIVED EDGE",
        "stat_source_confidence": "score_only_fallback_manual_context_required",
        "stat_source_label": "Score-derived fallback",
        "stat_review_cue": "No named performer stat text is available; hold if a player ledger is expected.",
        "editorial_microcopy_status": clean(microcopy.get("status")),
        "editorial_microcopy_variant": clean(microcopy.get("selected_variant_id")),
        "editorial_microcopy_headline": clean(microcopy.get("headline")),
        "editorial_microcopy_body": clean(microcopy.get("body")),
        "editorial_microcopy_context": clean(microcopy.get("context")),
        "editorial_microcopy_game_shape": clean(microcopy.get("game_shape")),
        "editorial_microcopy_game_shape_label": clean(microcopy.get("game_shape_label")),
        "editorial_microcopy_review_cue": clean(microcopy.get("review_cue")),
        "editorial_microcopy_variants": microcopy.get("variants") or [],
    }


def athlete_photo_layout_for_format(content_module: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, str]:
    if not photo_first_eligible(content_module):
        return {
            "athlete_photo_layout_mode": "safe_no_photo_fallback",
            "athlete_photo_layout_status": "photo_not_rendered",
            "athlete_photo_layout_detail": clean(content_module.get("athlete_photo_blocker")) or "Approved local athlete photo is not available for this format.",
            "athlete_photo_template_family": "logo_first_final_score_fallback",
        }
    if clean(spec.get("format_id")) == "square_feed_1x1" or int(spec.get("height", 0)) <= 1100:
        return {
            "athlete_photo_layout_mode": "compact_headshot_chip",
            "athlete_photo_layout_status": "approved_photo_compact_layout",
            "athlete_photo_layout_detail": "Approved local headshot uses a compact chip to preserve the square score layout.",
            "athlete_photo_template_family": "compact_athlete_photo_score_fallback",
        }
    return {
        "athlete_photo_layout_mode": "photo_first_final_score",
        "athlete_photo_layout_status": "approved_photo_first_template",
        "athlete_photo_layout_detail": "Approved local headshot becomes the main editorial visual with score lanes and verified stat modules kept review-only.",
        "athlete_photo_template_family": "approved_athlete_photo_final_score",
    }


def team_visual_profiles(packet: Dict[str, Any], template: Dict[str, str]) -> List[Dict[str, Any]]:
    score = parse_final_score(packet) if clean(template.get("tone")) == "result" else {}
    if not score:
        return []
    aliases, logos = team_registry()
    pairs = [
        ("winner", score.get("winner"), (247, 203, 84)),
        ("opponent", score.get("loser"), (37, 99, 163)),
    ]
    profiles: List[Dict[str, Any]] = []
    for role, team, fallback in pairs:
        profile = team_visual_profile(clean(team), aliases, logos, fallback)
        profiles.append(
            {
                "role": role,
                "team": profile["team"],
                "team_id": profile["team_id"],
                "team_accent_hex": profile["accent_hex"],
                "team_accent_source": profile["accent_source"],
                "logo_status": profile["logo_status"],
                "logo_approval_cue": profile["logo_approval_cue"],
                "logo_review_required": profile["logo_review_required"],
                "approval_policy": "team-color accent comes from local logo sampling or local team registry; does not approve logo, asset, or publish readiness",
            }
        )
    return profiles


def draw_primary_template(image: Any, packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any]) -> None:
    width, height = spec["width"], spec["height"]
    draw = ImageDraw.Draw(image)
    tone = template["tone"]
    parsed_score = parse_final_score(packet) if tone == "result" else {}
    if parsed_score:
        draw_final_score_template(image, packet, template, spec, parsed_score)
        return

    draw_brand_pattern(draw, width, height, tone)
    draw_review_chrome(draw, width, height, template, clean(spec["format_id"]).replace("_", " "))

    headline, dek = score_parts(packet)
    source = clean(packet.get("source_artifact")) or "source proof required"
    confidence = clean(packet.get("source_cue")) or "source review required"
    asset = clean(packet.get("asset_requirement")) or "No player asset required"
    context = clean(packet.get("copy_context")) or clean(packet.get("source_detail")) or "Manual source review required before any post."

    card_top = 214
    card_bottom = height - 96
    left = 54
    right = width - 54
    draw_rounded(draw, (left, card_top, right, card_bottom), 18, PALETTE["paper"], (255, 255, 255), 2)
    draw.rectangle((left, card_top, left + 20, card_bottom), fill=PALETTE["gold"] if tone == "result" else PALETTE["cyan"])

    text_left = 88
    text_right = right - 48
    y = card_top + 58
    draw.text((text_left, y), "REVIEW PREVIEW", font=font(28, True), fill=PALETTE["blue"])
    y += 58
    headline_font = font(76 if height >= 1350 else 62, True)
    y = draw_text_block(draw, (text_left, y), headline, headline_font, (23, 27, 36), text_right - text_left, 4, 12)
    y += 22
    draw.line((text_left, y, text_right, y), fill=(203, 206, 211), width=3)
    y += 34
    y = draw_text_block(draw, (text_left, y), dek, font(36 if height >= 1350 else 31, False), (28, 34, 46), text_right - text_left, 5, 10)

    if height >= 1260:
        module_top = max(y + 46, int(height * 0.69))
    else:
        module_top = max(y + 30, int(height * 0.62))
    module_bottom = card_bottom - 42
    draw_rounded(draw, (text_left, module_top, text_right, module_bottom), 0, (255, 255, 255), PALETTE["line"], 2)
    draw.text((text_left + 26, module_top + 26), "Manual render context", font=font(27, True), fill=(24, 28, 36))
    y = module_top + 80
    context_lines = [
        f"Template: {template['template_id']}",
        f"Source: {source}",
        f"Confidence: {confidence}",
        f"Assets: {asset}",
        f"Context: {context}",
    ]
    for item in context_lines:
        max_lines = 2 if item.startswith("Assets:") else 1
        text_font = font(21 if height >= 1350 else 19, False)
        y = draw_text_block(draw, (text_left + 26, y), item, text_font, PALETTE["muted"], text_right - text_left - 52, max_lines, 6)
        y += 3


def render_format(packet: Dict[str, Any], template: Dict[str, str], spec: Dict[str, Any]) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for manual review rendering.")
    image = Image.new("RGBA", (spec["width"], spec["height"]), (*PALETTE["deep"], 255))
    draw_primary_template(image, packet, template, spec)
    OUT_REVIEW_DRAFTS.mkdir(parents=True, exist_ok=True)
    output = OUT_REVIEW_DRAFTS / spec["filename"]
    image.save(output)
    if spec.get("primary"):
        image.save(OUT_PREVIEW)
    return output


def preview_title_crop_box(format_id: str, width: int, height: int) -> Tuple[int, int, int, int]:
    if format_id == "ig_story_9x16":
        return (72, 148, width - 72, min(height, 348))
    if format_id == "square_feed_1x1":
        return (48, 102, width - 48, min(height, 258))
    return (48, 110, width - 48, min(height, 304))


def preview_qa_for_path(path: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "format_id": clean(spec.get("format_id")),
        "path": path.as_posix(),
        "status": "preview_qa_not_run",
        "review_only": True,
        "publish_ready": False,
    }
    if Image is None or ImageStat is None:
        row["status"] = "preview_qa_unavailable_pillow_missing"
        return row
    try:
        image = Image.open(path).convert("RGBA")
        width, height = image.size
        alpha_bbox = image.getbbox()
        title_box = preview_title_crop_box(clean(spec.get("format_id")), width, height)
        title_crop = image.convert("L").crop(title_box)
        title_histogram = title_crop.histogram()
        title_total = max(1, sum(title_histogram))
        title_bright_ratio = sum(title_histogram[190:]) / title_total
        stat = ImageStat.Stat(image.convert("L"))
        luma_stddev = float(stat.stddev[0]) if stat.stddev else 0.0
        expected_w = int(spec.get("width", 0))
        expected_h = int(spec.get("height", 0))
        ok = bool(alpha_bbox) and width == expected_w and height == expected_h and title_bright_ratio >= 0.018 and luma_stddev >= 8.0
        row.update(
            {
                "status": "preview_qa_pass" if ok else "preview_qa_review_required",
                "width": width,
                "height": height,
                "expected_width": expected_w,
                "expected_height": expected_h,
                "nonblank_bbox": list(alpha_bbox) if alpha_bbox else [],
                "title_bright_ratio": round(title_bright_ratio, 4),
                "luma_stddev": round(luma_stddev, 2),
                "file_size_bytes": path.stat().st_size if path.exists() else 0,
                "qa_policy": "generated_preview_visibility_only_not_asset_approval_or_publish_readiness",
            }
        )
    except Exception as exc:
        row["status"] = "preview_qa_error"
        row["error"] = clean(exc)
    return row


def render_preview(packet: Dict[str, Any]) -> Dict[str, Any]:
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    template = choose_template(packet)
    content_module = content_module_summary(packet, template)
    outputs = []
    preview_qa = []
    for spec in FORMAT_SPECS:
        output = render_format(packet, template, spec)
        qa_row = preview_qa_for_path(output, spec)
        reference = reference_for_format(spec, template)
        row = {
            "format_id": spec["format_id"],
            "path": output.as_posix(),
            "width": spec["width"],
            "height": spec["height"],
            "primary": bool(spec.get("primary")),
            "review_only": True,
            "publish_ready": False,
        }
        if reference:
            row.update(reference)
        row.update(athlete_photo_layout_for_format(content_module, spec))
        row["render_background_style"] = RENDER_BACKGROUND_STYLE
        row["render_background_cues"] = RENDER_BACKGROUND_CUES
        row["preview_qa_status"] = clean(qa_row.get("status"))
        row["preview_qa_title_bright_ratio"] = qa_row.get("title_bright_ratio", "")
        row["preview_qa_luma_stddev"] = qa_row.get("luma_stddev", "")
        if clean(row.get("athlete_photo_layout_mode")) == "photo_first_final_score":
            row["photo_first_template_geometry"] = photo_first_layout_geometry(spec)
            row["photo_first_art_direction"] = (
                "premium_hsd_sports_editorial_photo_stage_with_team_accent_rim_light,"
                "balanced_score_rails,verified_stat_strip,and_review_only_guardrails"
            )
        outputs.append(row)
        preview_qa.append(qa_row)
    return {
        "template": template,
        "reference_pack": reference_pack_summary() if clean(template.get("reference_pack_id")) == REFERENCE_PACK_ID else {},
        "format_options": outputs,
        "asset_slots": asset_slots(packet, template),
        "content_module": content_module,
        "team_visual_profiles": team_visual_profiles(packet, template),
        "generated_preview_qa": preview_qa,
        "render_background_style": RENDER_BACKGROUND_STYLE,
        "render_background_cues": RENDER_BACKGROUND_CUES,
    }


def report_lines(status: str, manifest: Dict[str, Any], preview_path: str, reason: str = "", render_result: Dict[str, Any] | None = None) -> List[str]:
    packet = manifest.get("packet") if isinstance(manifest.get("packet"), dict) else {}
    render_result = render_result or {}
    template = render_result.get("template") if isinstance(render_result.get("template"), dict) else {}
    reference_pack = render_result.get("reference_pack") if isinstance(render_result.get("reference_pack"), dict) else {}
    formats = render_result.get("format_options") if isinstance(render_result.get("format_options"), list) else []
    preview_qa = render_result.get("generated_preview_qa") if isinstance(render_result.get("generated_preview_qa"), list) else []
    slots = render_result.get("asset_slots") if isinstance(render_result.get("asset_slots"), list) else []
    content_module = render_result.get("content_module") if isinstance(render_result.get("content_module"), dict) else {}
    team_profiles = render_result.get("team_visual_profiles") if isinstance(render_result.get("team_visual_profiles"), list) else []
    lines = [
        "# HSD Manual Review Renderer",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{status}`",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Guardrails",
        "",
        "- Manual-only mode.",
        "- Draft preview is for human review only.",
        "- Does not publish.",
        "- Does not approve the image.",
        "- Does not call paid APIs.",
        "- Does not move files into a publish-ready lane.",
        "",
        "## Output",
        "",
        f"- Preview: `{preview_path or 'not_created'}`",
        f"- Story: `{clean(packet.get('title')) or 'none'}`",
        f"- Template: `{clean(template.get('template_id')) or 'not_selected'}`",
        f"- Template family: `{clean(template.get('template_family')) or 'not_selected'}`",
        f"- Reference pack: `{clean(reference_pack.get('pack_id')) or 'not_used'}`",
        f"- Content module: `{clean(content_module.get('content_module_mode')) or 'not_selected'}` / `{clean(content_module.get('content_module_status')) or 'not_run'}`",
        f"- Game shape: `{clean(content_module.get('content_module_game_shape')) or clean(content_module.get('editorial_microcopy_game_shape')) or 'not_selected'}` / {clean(content_module.get('content_module_game_shape_label')) or clean(content_module.get('editorial_microcopy_game_shape_label')) or 'n/a'}",
        f"- Athlete photo: `{clean(content_module.get('athlete_photo_status')) or 'not_applicable'}` / {clean(content_module.get('athlete_photo_approval_cue')) or 'n/a'}",
        f"- Athlete identity: `{clean(content_module.get('athlete_photo_identity_review_status')) or 'not_applicable'}` / resolution=`{clean(content_module.get('athlete_photo_identity_resolution_status')) or 'not_recorded'}`",
        f"- Stat source confidence: `{clean(content_module.get('stat_source_confidence')) or 'not_applicable'}`",
        f"- Stat review cue: {clean(content_module.get('stat_review_cue')) or 'n/a'}",
        f"- Editorial microcopy: `{clean(content_module.get('editorial_microcopy_variant')) or 'not_selected'}` / {clean(content_module.get('editorial_microcopy_headline')) or 'n/a'}",
        f"- Editorial review cue: {clean(content_module.get('editorial_microcopy_review_cue')) or 'n/a'}",
        f"- Reason: {reason or 'n/a'}",
        "",
        "## Review Draft Formats",
        "",
    ]
    if formats:
        for item in formats:
            ref = clean(item.get("reference_template_id")) or "none"
            derivation = clean(item.get("reference_derivation")) or "not_reference_packed"
            photo_layout = clean(item.get("athlete_photo_layout_mode")) or "n/a"
            lines.append(
                f"- `{item.get('format_id')}` | `{item.get('width')}x{item.get('height')}` | `{item.get('path')}` | reference=`{ref}` | derivation=`{derivation}` | photo_layout=`{photo_layout}` | publish_ready=`false`"
            )
    else:
        lines.append("- none")
    lines += ["", "## Generated Preview QA", ""]
    if preview_qa:
        for item in preview_qa:
            lines.append(
                f"- `{clean(item.get('format_id'))}` | status=`{clean(item.get('status'))}` | title_bright_ratio=`{clean(item.get('title_bright_ratio'))}` | luma_stddev=`{clean(item.get('luma_stddev'))}` | publish_ready=`false`"
            )
    else:
        lines.append("- not_run")
    if formats:
        lines += ["", "## Reference Assets", ""]
        for item in formats:
            if not clean(item.get("reference_template_id")):
                continue
            lines.append(f"- `{item.get('format_id')}` spec: `{clean(item.get('reference_spec_path'))}`")
            lines.append(f"- `{item.get('format_id')}` public mockup: `{clean(item.get('reference_public_mockup_path'))}`")
            lines.append(f"- `{item.get('format_id')}` layout reference: `{clean(item.get('reference_layout_path'))}`")
    lines += ["", "## Asset Slots", ""]
    if slots:
        lines.extend(
            f"- `{item.get('slot_id')}` | `{item.get('status')}` | {clean(item.get('requirement'))}"
            for item in slots
        )
    else:
        lines.append("- none")
    lines += ["", "## Team Color And Logo Review Cues", ""]
    if team_profiles:
        for profile in team_profiles:
            lines.append(
                f"- `{clean(profile.get('role'))}` {clean(profile.get('team'))}: accent=`{clean(profile.get('team_accent_hex'))}` source=`{clean(profile.get('team_accent_source'))}` logo=`{clean(profile.get('logo_status'))}` cue=`{clean(profile.get('logo_approval_cue'))}` review_required=`{clean(profile.get('logo_review_required'))}`"
            )
    else:
        lines.append("- none")
    return [
        *lines,
    ]


def main() -> None:
    handoff = find_handoff_dir()
    if not handoff:
        manifest = {
            "version": VERSION,
            "status": "blocked_missing_handoff",
            "preview_path": "",
            "guardrails": {
                "manual_only": True,
                "review_only": True,
                "auto_render": False,
                "auto_publish": False,
                "approved": False,
                "paid_apis": False,
                "move_files": False,
                "publish_ready": False,
            },
        }
        write_json(OUT_MANIFEST, manifest)
        write_text(OUT_REPORT, "\n".join(report_lines("blocked_missing_handoff", {}, "", "render_handoff_top_packet/handoff_manifest.json was not found.")))
        print(json.dumps(manifest, indent=2))
        return

    copy_handoff_to_output(handoff)
    source_manifest = read_json(handoff / "handoff_manifest.json")
    packet = source_manifest.get("packet") if isinstance(source_manifest.get("packet"), dict) else {}
    status = "draft_preview_created"
    reason = ""
    preview = ""
    render_result: Dict[str, Any] = {"template": {}, "format_options": [], "asset_slots": []}
    try:
        render_result = render_preview(packet)
        preview = OUT_PREVIEW.as_posix()
    except Exception as exc:
        status = "blocked_preview_not_created"
        reason = str(exc)

    manifest = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_handoff_dir": handoff.as_posix(),
        "output_handoff_dir": OUT_DIR.as_posix(),
        "preview_path": preview,
        "packet_id": clean(packet.get("packet_id")),
        "title": clean(packet.get("title")),
        "source_artifact": clean(packet.get("source_artifact")),
        "source_cue": clean(packet.get("source_cue")),
        "source_detail": clean(packet.get("source_detail")),
        "copy_context": clean(packet.get("copy_context")),
        "renderer_mode": "template_driven_review_drafts",
        "selected_template": render_result.get("template", {}),
        "reference_pack": render_result.get("reference_pack", {}),
        "format_options": render_result.get("format_options", []),
        "generated_preview_qa": render_result.get("generated_preview_qa", []),
        "asset_slots": render_result.get("asset_slots", []),
        "content_module": render_result.get("content_module", {}),
        "team_visual_profiles": render_result.get("team_visual_profiles", []),
        "render_background_style": clean(render_result.get("render_background_style")) or RENDER_BACKGROUND_STYLE,
        "render_background_cues": clean(render_result.get("render_background_cues")) or RENDER_BACKGROUND_CUES,
        "guardrails": {
            "manual_only": True,
            "review_only": True,
            "auto_render": False,
            "auto_publish": False,
            "approved": False,
            "paid_apis": False,
            "move_files": False,
            "publish_ready": False,
        },
        "approval_status": "not_approved_human_review_required",
        "reason": reason,
    }
    write_json(OUT_MANIFEST, manifest)
    write_text(OUT_REPORT, "\n".join(report_lines(status, source_manifest, preview, reason, render_result)))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
