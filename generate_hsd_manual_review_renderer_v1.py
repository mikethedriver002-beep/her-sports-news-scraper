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


VERSION = "hsd-manual-review-renderer-v1.61.0-open-score-rails"
HANDOFF_DIR_NAME = "render_handoff_top_packet"
OUT_DIR = output_path(HANDOFF_DIR_NAME)
OUT_PREVIEW = OUT_DIR / "draft_preview.png"
OUT_REVIEW_DRAFTS = OUT_DIR / "review_drafts"
OUT_REPORT = output_path("manual_review_renderer_report.md")
OUT_MANIFEST = output_path("manual_review_renderer_manifest.json")
OUT_VISUAL_COMPARISON_BOARD = output_path("manual_review_renderer_visual_comparison_board.md")
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
FINAL_SCORE_STAT_PROOF_CSV = "final_score_stat_proof_v1.csv"
RENDER_BACKGROUND_STYLE = "hsd_premium_sports_editorial_v28_open_score_rails"
RENDER_BACKGROUND_FAMILY = "hsd_premium_sports_editorial"
RENDER_BACKGROUND_CUES = (
    "dimensional_hsd_ink_field,quiet_score_zones,subtle_stadium_light_sweep,"
    "team_accent_rim_light,soft_editorial_rule_grid,restrained_halftone_noise,"
    "review_only_brand_rails,logo_first_score_atmosphere,logo_first_atmospheric_score_wash,sports_editorial_depth_markers,"
    "square_compact_review_footer,square_context_score_hierarchy,proof_artifact_athlete_led_bridge,"
    "square_athlete_focal_panel,photo_first_focal_depth_stage,photo_first_score_lock_slab,"
    "photo_first_editorial_nameplate,photo_first_portrait_spotlight,photo_first_score_type_lockup,"
    "photo_first_context_score_rail,photo_first_subject_glow_bridge,photo_first_soft_focal_frame,"
    "photo_first_athlete_primary_focal_contract,photo_first_premium_score_stage,"
    "photo_first_editorial_stage_depth,photo_first_score_type_grid_polish,photo_first_type_scale,"
    "photo_first_athlete_visual_cap,photo_first_editorial_score_rails,"
    "photo_first_subtle_logo_identifiers,compact_square_photo_footer,"
    "photo_first_integrated_stat_band,photo_first_context_stage_bridge,"
    "photo_first_open_score_lockup,photo_first_soft_athlete_stage,"
    "photo_first_editorial_focal_corridor,photo_first_calm_background_zones,"
    "photo_first_unboxed_score_rails,photo_first_soft_photo_stage_mask,"
    "photo_first_action_photo_hero_contract,photo_first_naked_score_typography,"
    "photo_first_no_redundant_score_context,photo_first_borderless_hero_stage,"
    "photo_first_blueprint_depth_layers,photo_first_procedural_court_grain,"
    "photo_first_asymmetric_score_treatment,photo_first_hero_cutout_contract,"
    "photo_first_safe_zone_enforced,photo_first_oversized_emblem_atmosphere,"
    "photo_first_editorial_team_identifiers,photo_first_lower_third_caption_strip,"
    "photo_first_quiet_review_marker,photo_first_score_stage_wash,"
    "photo_first_action_photo_stage_bridge,photo_first_editorial_depth_bridge,"
    "photo_first_open_lower_caption_rail,photo_first_quiet_badge_pin,"
    "logo_first_editorial_score_spine,logo_first_no_dashboard_card_panels,score_rows_typography_over_wash,"
    "lower_third_editorial_rail,lower_third_no_heavy_stat_cards,reduced_lower_rail_panel_weight,"
    "soft_review_wash,open_manual_context_rail,"
    "action_photo_readiness_visual_qa,headshot_bridge_review_draft_only,"
    "premium_final_score_action_photo_required,composition_balance_visual_qa,"
    "headshot_bridge_not_roster_portrait,action_photo_replacement_balance_ready,"
    "borderless_score_text_treatment,lower_rail_open_editorial_treatment,"
    "softened_wireframe_texture,dashboard_panel_risk_visual_qa,"
    "lower_third_box_risk_visual_qa,roster_headshot_risk_visual_qa,"
    "anti_dashboard_visual_qa,stat_proof_rail,generated_preview_qa"
)
REVIEW_DRAFT_PILL_LABEL = "REVIEW DRAFT ONLY"
REVIEW_DRAFT_FOOTER_LABEL = "REVIEW DRAFT ONLY - HUMAN CHECK REQUIRED"
REVIEW_WATERMARK_CONTRACT = "permanent_top_and_footer_review_only_diagnostic_lock"
PUBLIC_RENDER_BANNED_CANVAS_PHRASES = [
    "PHOTO-FIRST / STAT PROOF CHECK",
    "MATCHUP ANGLE",
    "STAT PROOF CHECK",
    "STAT CONFIDENCE",
    "IDENTITY CONFIDENCE",
    "SOURCE CONFIDENCE",
    "RENDER ELIGIBLE",
    "STATEMENT MARGIN",
    "GAME RECAP FINAL SCORE",
    "PHOTO-FIRST DRAFT",
    "ASSET READY",
    "HUMAN CHECK REQUIRED",
    "LOGO CHECK",
    "LOGO REVIEW",
]
PHOTO_FIRST_ATHLETE_MAX_VISUAL_SHARE = 0.40
PHOTO_FIRST_SAFE_ZONES = {
    "default": {"top": 90, "bottom": 90, "left": 60, "right": 60},
    "ig_feed_4x5": {"top": 90, "bottom": 90, "left": 60, "right": 60},
    "square_feed_1x1": {"top": 90, "bottom": 90, "left": 60, "right": 60},
    "ig_story_9x16": {"top": 120, "bottom": 140, "left": 60, "right": 60},
}
PHOTO_FIRST_SCORE_ASYMMETRY_CONTRACT = {
    "winner_score_scale": 1.0,
    "loser_score_scale": 0.52,
    "winner_team_scale": 1.0,
    "loser_team_scale": 0.56,
    "loser_opacity": 0.65,
}
PHOTO_FIRST_FINAL_SCORE_ACTIVE_TYPE_LEVELS = ("label", "headline", "score", "support")
PHOTO_FIRST_FINAL_SCORE_TYPE_SCALE = {
    "kicker": {
        "level": "label",
        "font": "context",
        "size": 38,
        "square_size": 30,
        "min": 20,
        "square_min": 18,
        "stroke": 0,
    },
    "headline": {
        "level": "headline",
        "font": "display",
        "size": 50,
        "story_size": 46,
        "square_size": 35,
        "min": 24,
        "stroke": 1,
    },
    "team": {
        "level": "support",
        "font": "display",
        "winner_size": 50,
        "winner_compact_size": 38,
        "size": 28,
        "compact_size": 23,
        "min": 17,
        "compact_min": 13,
        "stroke": 0,
    },
    "score": {
        "level": "score",
        "font": "score",
        "winner_size": 124,
        "size": 62,
        "compact_size": 54,
        "min": 46,
        "compact_min": 46,
        "stroke": 0,
    },
    "chip_label": {
        "level": "label",
        "font": "context",
        "size": 13,
        "compact_size": 11,
        "min": 9,
        "stroke": 0,
    },
    "context_rail": {
        "level": "support",
        "font": "context",
        "size": 24,
        "compact_size": 22,
        "min": 12,
        "stroke": 0,
    },
    "athlete_line": {
        "level": "support",
        "font": "display",
        "size": 32,
        "compact_size": 25,
        "min": 17,
        "stroke": 0,
    },
    "stat": {
        "level": "support",
        "font": "context",
        "size": 28,
        "compact_size": 21,
        "min": 14,
        "stroke": 0,
    },
    "review_marker": {
        "level": "label",
        "font": "context",
        "size": 15,
        "min": 10,
        "stroke": 0,
    },
}

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
        pixels = sample.tobytes()
        for index in range(0, len(pixels), 4):
            r, g, b, a = pixels[index], pixels[index + 1], pixels[index + 2], pixels[index + 3]
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


def draw_sports_editorial_depth_markers(
    image: Any,
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
    *,
    photo_first: bool = False,
) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = image.size
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    gold = PALETTE["gold"]
    horizon_y = int(height * (0.720 if photo_first else 0.735))

    for offset in range(-220, width + 180, 34):
        alpha = (15 if offset % 68 == 0 else 8) if photo_first else (24 if offset % 68 == 0 else 13)
        draw.line((offset, height + 30, offset + int(width * 0.52), horizon_y), fill=(*gold, alpha), width=1)
    for offset in range(-160, width + 220, 42):
        draw.line((offset, int(height * 0.245), offset + int(width * 0.34), int(height * 0.050)), fill=(*secondary, 7 if photo_first else 12), width=1)

    glow_y = int(height * (0.718 if photo_first else 0.760))
    draw.ellipse(
        (int(width * 0.05), glow_y - 34, int(width * 0.47), glow_y + 34),
        fill=(*primary, 24 if photo_first else 28),
    )
    draw.ellipse(
        (int(width * 0.50), glow_y - 30, int(width * 0.94), glow_y + 30),
        fill=(*secondary, 20 if photo_first else 24),
    )
    draw.line((54, glow_y, width - 54, glow_y), fill=(*gold, 50 if photo_first else 84), width=1 if photo_first else 2)
    draw.line((74, glow_y + 7, width - 74, glow_y + 7), fill=(248, 250, 255, 10 if photo_first else 18), width=1)

    randomizer = random.Random(width * 23 + height * 19 + (97 if photo_first else 31))
    for side in (0, 1):
        cluster_x = int(width * (0.08 if side == 0 else 0.92))
        cluster_y = int(height * (0.34 if side == 0 else 0.23))
        for _ in range(32 if photo_first else 44):
            spread_x = randomizer.randrange(0, max(48, int(width * 0.14)))
            spread_y = randomizer.randrange(0, max(60, int(height * 0.16)))
            x = cluster_x + (-spread_x if side == 0 else spread_x)
            y = cluster_y + spread_y
            size = randomizer.randrange(1, 3)
            draw.rectangle((x, y, x + size, y + size), fill=(*gold, randomizer.randrange(9, 25) if photo_first else randomizer.randrange(18, 46)))

    if ImageFilter is not None:
        glow = layer.filter(ImageFilter.GaussianBlur(10))
        image.alpha_composite(glow)
    image.alpha_composite(layer)


def draw_photo_first_editorial_focal_corridor(image: Any) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = image.size
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle(
        (int(width * 0.035), int(height * 0.275), int(width * 0.970), int(height * 0.780)),
        radius=34,
        fill=(1, 4, 11, 58),
    )
    draw.rounded_rectangle(
        (int(width * 0.380), int(height * 0.300), int(width * 0.965), int(height * 0.655)),
        radius=28,
        fill=(1, 3, 9, 66),
    )
    draw.polygon(
        [
            (int(width * 0.020), int(height * 0.340)),
            (int(width * 0.385), int(height * 0.265)),
            (int(width * 0.470), int(height * 0.710)),
            (int(width * 0.050), int(height * 0.790)),
        ],
        fill=(2, 6, 14, 42),
    )
    draw.polygon(
        [
            (int(width * 0.420), int(height * 0.395)),
            (int(width * 0.965), int(height * 0.360)),
            (int(width * 0.900), int(height * 0.610)),
            (int(width * 0.405), int(height * 0.665)),
        ],
        fill=(6, 9, 16, 42),
    )
    if ImageFilter is not None:
        layer = layer.filter(ImageFilter.GaussianBlur(10))
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


def draw_photo_first_procedural_texture(image: Any, primary: tuple[int, int, int], secondary: tuple[int, int, int]) -> None:
    if ImageDraw is None:
        return
    width, height = image.size
    rng = random.Random(width * 43 + height * 29)
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    horizon = int(height * 0.71)
    for offset in range(-width, width * 2, 42):
        alpha = 16 if offset % 126 == 0 else 8
        draw.line((offset, horizon + 70, offset + int(width * 0.42), horizon - 42), fill=(*primary, alpha), width=1)
    for y in range(horizon - 54, min(height, horizon + 178), 18):
        alpha = 11 if (y // 18) % 3 else 20
        draw.line((42, y, width - 42, y + rng.randrange(-5, 6)), fill=(*primary, alpha), width=1)
    for _ in range(180 if height > 1500 else 128):
        x = rng.randrange(0, width)
        y = rng.randrange(int(height * 0.22), min(height, int(height * 0.90)))
        size = rng.randrange(1, 4)
        color = primary if rng.random() < 0.78 else secondary
        alpha = rng.randrange(7, 24) if color == primary else rng.randrange(3, 12)
        draw.rectangle((x, y, x + size, y + size), fill=(*color, alpha))
    draw.polygon(
        [
            (0, int(height * 0.35)),
            (int(width * 0.62), int(height * 0.30)),
            (width, int(height * 0.45)),
            (width, int(height * 0.73)),
            (int(width * 0.14), int(height * 0.68)),
        ],
        fill=(*primary, 12),
    )
    draw.polygon(
        [
            (int(width * 0.54), int(height * 0.26)),
            (width, int(height * 0.34)),
            (width, int(height * 0.62)),
            (int(width * 0.66), int(height * 0.56)),
        ],
        fill=(*secondary, 8),
    )
    if ImageFilter is not None:
        layer = layer.filter(ImageFilter.GaussianBlur(0.25))
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
        (44 if photo_first else 70) if tone == "final" else 52,
        38,
    )
    draw_soft_light_sweep(
        image,
        [(int(width * 0.56), -90), (width + 90, -90), (width + 90, int(height * 0.54)), (int(width * 0.34), int(height * 0.24))],
        secondary,
        (36 if photo_first else 58) if tone == "final" else 42,
        46,
    )
    draw_soft_light_sweep(
        image,
        [(int(width * 0.10), int(height * 0.16)), (int(width * 0.94), int(height * 0.06)), (int(width * 0.82), int(height * 0.12)), (int(width * 0.14), int(height * 0.24))],
        (248, 250, 255),
        16 if photo_first else 24,
        20,
    )
    draw_sports_editorial_depth_markers(image, primary, secondary, photo_first=photo_first)
    if photo_first:
        draw_photo_first_editorial_focal_corridor(image)
        draw_photo_first_procedural_texture(image, primary, secondary)

    rail_alpha = (12 if photo_first else 24) if tone == "final" else 18
    for x in range(-height, width + height, 520):
        draw.line((x, height + 60, x + int(height * 0.66), -70), fill=(*primary, rail_alpha), width=1)
    for x in range(-height, width + height, 820):
        draw.line((x, height + 140, x + int(height * 0.52), -40), fill=(*secondary, 8 if photo_first else 16), width=1)

    for y in [int(height * 0.12), int(height * 0.285), int(height * 0.74), int(height * 0.88)]:
        draw.line((30, y, width - 30, y), fill=(*primary, 10 if photo_first else 22), width=1)
    for x in range(86, width, 170):
        draw.line((x, int(height * 0.18), x, int(height * 0.92)), fill=(248, 250, 255, 4), width=1)

    background_words = ["HER SPORTS DAILY"] if photo_first else ["HER SPORTS DAILY", "FINAL SCORE", "REVIEW DRAFT"]
    for index, word in enumerate(background_words):
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


def draw_reference_guardrail(image: Any, *, compact_footer: bool = False) -> None:
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    pill_w = min(174, width - 850)
    if pill_w > 142:
        marker_type = photo_first_type_spec("review_marker")
        left = width - pill_w - 50
        top = 84
        right = width - 50
        bottom = 110
        draw.rounded_rectangle((left, top, right, bottom), radius=5, fill=(6, 9, 16, 136), outline=(241, 238, 229, 44), width=1)
        draw.rectangle((left, top, left + 26, bottom), fill=(150, 35, 48, 164))
        draw.line((left + 24, top + 4, right - 10, top + 4), fill=(*PALETTE["gold"], 70), width=1)
        draw_reference_text(
            image,
            (left + 30, 87, pill_w - 42, 18),
            "Review Draft Only",
            marker_type["font"],
            min(marker_type["resolved_size"], 14),
            marker_type["resolved_min"],
            (235, 239, 247),
            max_lines=1,
            align="center",
            uppercase=False,
            stroke=marker_type["stroke"],
        )
    footer_h = 24 if compact_footer else 28
    footer_top = height - (48 if compact_footer else 64)
    footer_bottom = footer_top + footer_h
    draw.rectangle((54, footer_top, width - 54, footer_bottom), fill=(*PALETTE["red"], 238))
    draw_reference_text(
        image,
        (70, footer_top + 2, width - 140, footer_h - 2),
        REVIEW_DRAFT_FOOTER_LABEL,
        "context",
        20 if not compact_footer else 17,
        12,
        PALETTE["ink"],
        max_lines=1,
        align="left",
    )


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
        "PORTLAND ",
    ]
    for prefix in prefixes:
        if text.startswith(prefix) and len(text) >= len(prefix) + 3:
            return text[len(prefix):]
    return text


def team_monogram(team: str) -> str:
    words = [part for part in clean(team).upper().replace("-", " ").split() if part]
    if not words:
        return "HSD"
    if len(words) == 1:
        return words[0][:3]
    return "".join(word[0] for word in words[:3])


def team_city_name(team: str) -> str:
    team_text = clean(team)
    if not team_text:
        return ""
    team_short = short_team(team_text).lower()
    team_full = team_text.lower()
    for row in read_csv(TEAM_COLORS_CSV):
        if clean(row.get("league")).upper() != "WNBA":
            continue
        names = {
            clean(row.get("team_name")).lower(),
            clean(row.get("nickname")).lower(),
            clean(row.get("slug")).replace("_", " ").lower(),
        }
        if team_full in names or team_short == clean(row.get("nickname")).lower():
            return clean(row.get("city"))
    parts = team_text.split()
    if len(parts) > 1:
        return " ".join(parts[:-1])
    return team_text


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


def public_stat_line(callouts: List[Dict[str, str]]) -> str:
    parts = [
        f"{clean(item.get('value'))} {clean(item.get('label')).upper()}".strip()
        for item in callouts[:3]
        if clean(item.get("value")) and clean(item.get("label"))
    ]
    return " / ".join(parts)


def photo_first_public_canvas_copy(score: Dict[str, str], stat_module: Dict[str, Any]) -> Dict[str, str]:
    winner = short_team(score.get("winner", "")).title()
    loser = short_team(score.get("loser", "")).title()
    winner_score = clean(score.get("winner_score"))
    loser_score = clean(score.get("loser_score"))
    player = clean(stat_module.get("player_name"))
    callouts = stat_module.get("callouts") if isinstance(stat_module.get("callouts"), list) else []
    pts = next((clean(item.get("value")) for item in callouts if clean(item.get("label")).upper() == "PTS"), "")
    city = team_city_name(score.get("winner", ""))
    if player and pts and city:
        athlete_line = f"{player} led {city} with {pts} points."
    elif player and pts:
        athlete_line = f"{player} finished with {pts} points."
    elif player:
        athlete_line = f"{player} led the final-score story."
    else:
        athlete_line = f"{winner} closed out the final." if winner else "Final score confirmed."
    stat_line = public_stat_line(callouts)
    scoreline = f"{winner} beat {loser}, {winner_score}-{loser_score}".strip(" ,-")
    compact_scoreline = f"{winner} {winner_score}, {loser} {loser_score}".strip(" ,")
    return {
        "kicker": "WNBA FINAL",
        "result_line": scoreline,
        "compact_scoreline": compact_scoreline,
        "athlete_line": athlete_line,
        "stat_line": stat_line,
        "review_marker": "Review Draft Only",
    }


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
        return "SOURCE-READY"
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


def proof_artifact_stat_performers(packet: Dict[str, Any], score: Dict[str, str]) -> List[Dict[str, Any]]:
    winner = clean(score.get("winner"))
    loser = clean(score.get("loser"))
    if not winner or not loser:
        return []
    winner_norm = norm(winner)
    loser_norm = norm(loser)
    candidates: List[Dict[str, Any]] = []
    for row in read_csv(input_path(FINAL_SCORE_STAT_PROOF_CSV)):
        if clean(row.get("fact_type")) != "named_player_stat_line":
            continue
        if clean(row.get("recap_candidate")).lower() not in {"yes", "true", "1"}:
            continue
        if clean(row.get("review_only")).lower() not in {"yes", "true", "1"}:
            continue
        if clean(row.get("publish_action")).lower() not in {"", "none", "none_artifact_only"}:
            continue
        matchup_norm = norm(row.get("matchup"))
        if winner_norm not in matchup_norm or loser_norm not in matchup_norm:
            continue
        stats = parse_stat_pairs(row.get("stat_line") or row.get("fact_value"))
        player = clean(row.get("named_player"))
        team = clean(row.get("player_team"))
        if player and team and stats:
            candidates.append(
                {
                    "name": player,
                    "team": team,
                    "stats": stats,
                    "source_text": clean(row.get("fact_value")) or f"{player} ({team}): {clean(row.get('stat_line'))}",
                    "proof_id": clean(row.get("proof_id")),
                    "proof_source": FINAL_SCORE_STAT_PROOF_CSV,
                    "proof_status": clean(row.get("proof_status")),
                    "proof_review_only": clean(row.get("review_only")),
                    "proof_source_url": clean(row.get("source_url")),
                    "proof_source_domain": clean(row.get("source_domain")),
                    "proof_operator_note_path": clean(row.get("operator_note_path")),
                    "proof_limitations": clean(row.get("limitations")),
                }
            )
    return candidates


def athlete_led_missing_fields(packet: Dict[str, Any], stat_module: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if not verified_stat_text(packet) and not clean(stat_module.get("proof_source")):
        missing.append("athlete_name")
        missing.append("verified stat/story context")
    elif not clean(stat_module.get("player_name")):
        missing.append("athlete_name")
    photo_status = clean(stat_module.get("athlete_photo_status")) or clean(stat_module.get("status"))
    if photo_status != "approved_local_headshot":
        missing.append("approved local image/cutout path")
    return list(dict.fromkeys(missing))


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
    proof_bridge_used = False
    if not performers:
        performers = proof_artifact_stat_performers(packet, score)
        proof_bridge_used = bool(performers)
    if not performers:
        return {
            "status": "fallback_game_edge_no_verified_stat_text",
            "athlete_led_render_status": "athlete_led_blocked_missing_verified_player_context",
            "athlete_led_missing_fields": "athlete_name, approved local image/cutout path, verified stat/story context",
            "athlete_led_blocker": (
                "No athlete-led preview produced: handoff lacks athlete_name/top_performers, "
                "approved local image/cutout path, and verified stat/story context."
            ),
        }
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
    matchup_note = f"{winner_short} {score.get('winner_score')}, {loser_short} {score.get('loser_score')}"
    shape = game_shape(score)
    photo = resolve_athlete_photo(player, team or score.get("winner", ""))
    if clean(shape.get("game_shape")) == "close_finish":
        headline = f"{last_name(player)} + CLOSE FINISH" if player else clean(shape.get("game_shape_label"))
    elif clean(shape.get("game_shape")) == "statement_margin":
        headline = f"{last_name(player)} + STATEMENT MARGIN" if player else clean(shape.get("game_shape_label"))
    if strength != "lead_ledger":
        headline = f"{last_name(player)} STAT NOTE" if player else "VERIFIED STAT NOTE"
    athlete_led_ready = clean(photo.get("status")) == "approved_local_headshot" and strength == "lead_ledger"
    proof_source = clean(selected.get("proof_source"))
    return {
        "status": "verified_player_stat_module" if strength == "lead_ledger" else "verified_supporting_stat_module",
        "eyebrow": "PLAYER LEDGER" if strength == "lead_ledger" else "STAT NOTE",
        "headline": headline,
        "body": f"{player}{team_text}: {stat_text}.",
        "editorial_line": f"{stat_line} in the {matchup_note} final." if strength == "lead_ledger" else f"Supporting stat context from the {matchup_note} final.",
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
        "athlete_photo_layout_options": "photo_first_final_score,square_photo_first_score_panel,compact_headshot_chip,logo_first_fallback,safe_no_photo_fallback",
        "callouts": stats[:3],
        "player_name": player,
        "team": team,
        "source_text": clean(selected.get("source_text")),
        "proof_artifact_bridge_used": str(bool(proof_bridge_used)).lower(),
        "proof_id": clean(selected.get("proof_id")),
        "proof_source": proof_source,
        "proof_status": clean(selected.get("proof_status")),
        "proof_review_only": clean(selected.get("proof_review_only")),
        "proof_source_url": clean(selected.get("proof_source_url")),
        "proof_source_domain": clean(selected.get("proof_source_domain")),
        "proof_operator_note_path": clean(selected.get("proof_operator_note_path")),
        "proof_limitations": clean(selected.get("proof_limitations")),
        "athlete_led_render_status": "athlete_led_review_preview_ready" if athlete_led_ready else "athlete_led_blocked_missing_approved_photo_or_lead_stat",
        "athlete_led_missing_fields": ", ".join(athlete_led_missing_fields(packet, {**photo, "player_name": player, "proof_source": proof_source})),
        "athlete_led_blocker": "" if athlete_led_ready else (clean(photo.get("blocker")) or "Athlete-led preview needs a lead verified stat and approved local athlete image."),
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
            "headline": "FINAL BOARD",
            "body": f"{short_team(winner)} finished ahead; keep the why on hold until source proof supports it.",
            "game_shape": clean(shape.get("game_shape")),
            "game_shape_label": clean(shape.get("game_shape_label")),
        }
    if margin <= 3:
        headline = "LAST-SWING FINAL"
        body = f"{short_team(winner)} held the final possession window against {short_team(loser)}."
    elif margin <= 7:
        headline = "LATE SEPARATION"
        body = f"{short_team(winner)} created just enough late separation to make {short_team(loser)} chase."
    elif margin <= 14:
        headline = "CONTROL WINDOW"
        body = f"{short_team(winner)} turned the final margin into the story."
    else:
        headline = "NO-CHASE FINAL"
        body = f"{short_team(winner)} built the gap early enough that {short_team(loser)} never found the counter."
    return {"eyebrow": "SCORE-DERIVED EDGE", "headline": headline, "body": body, "game_shape": clean(shape.get("game_shape")), "game_shape_label": clean(shape.get("game_shape_label"))}


def review_prompt(score: Dict[str, str]) -> str:
    return clean(game_shape(score).get("prompt")) or "WHAT STOOD OUT FROM THE FINAL?"


def scoreline_context(score: Dict[str, str]) -> str:
    winner = short_team(score.get("winner", ""))
    loser = short_team(score.get("loser", ""))
    margin = score_margin(score)
    total = score_total(score)
    winner_score = clean(score.get("winner_score"))
    loser_score = clean(score.get("loser_score"))
    parts = [f"{winner} {winner_score}, {loser} {loser_score}" if winner_score and loser_score else f"{winner} over {loser}"]
    if margin is not None:
        parts.append(f"+{margin} margin")
    if total is not None:
        parts.append(f"{total} total points")
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
    source_label = source_quality_label(packet)
    shape = game_shape(score)
    shape_label = clean(shape.get("game_shape_label")) or "FINAL RESULT"
    variants: List[Dict[str, str]] = []
    margin_text = f"+{margin}" if margin is not None else "final-score"
    variants.append(
        {
            "variant_id": "scoreline_spine",
            "label": "Scoreline spine",
            "headline": clean(shape.get("angle_label")) or f"{winner} {margin_text} FINAL",
            "body": f"{scoreline_context(score)}. Keep the angle on the {shape_label.lower()} until source proof supports more.",
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
                    "body": f"{last_name(player).title()} added {stat_line.replace(' / ', ', ')} in the {shape_label.lower()}: {scoreline_context(score).lower()}.",
                }
            )
        else:
            variants.append(
                {
                    "variant_id": "verified_supporting_stat_note",
                    "label": "Verified supporting stat note",
                    "headline": clean(shape.get("angle_label")) or f"{winner} {margin_text} FINAL",
                    "body": f"{last_name(player).title()}'s {stat_line.replace(' / ', ', ')} stays as supporting context; keep the main angle on the {shape_label.lower()}.",
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
            "body": f"{source_label}: hold this as an editor question until the source packet supports the why.",
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


def draw_team_logo_slot(
    image: Any,
    team: str,
    box: Tuple[int, int, int, int],
    aliases: Dict[str, str],
    logos: Dict[str, Dict[str, str]],
    accent: tuple[int, int, int],
    *,
    winner: bool = False,
    treatment: str = "slot",
) -> Dict[str, Any]:
    registry_accent, registry_accent_source = team_registry_accent(team, aliases, accent)
    result = enrich_logo_result(load_team_logo(team, aliases, logos), registry_accent, registry_accent_source)
    team_accent = result.get("team_accent_rgb") if isinstance(result.get("team_accent_rgb"), tuple) else accent
    approval_cue = clean(result.get("logo_approval_cue")) or "LOGO REVIEW"
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    sheen = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen, "RGBA")
    editorial_identifier = clean(treatment) == "editorial_identifier"
    glow_alpha = (52 if winner else 18) if editorial_identifier else (42 if winner else 24)
    sheen_draw.ellipse(
        (x - int(w * (0.46 if editorial_identifier else 0.38)), y - int(h * (0.50 if editorial_identifier else 0.42)), x + int(w * (1.46 if editorial_identifier else 1.36)), y + int(h * (1.38 if editorial_identifier else 1.30))),
        fill=(*team_accent, glow_alpha),
    )
    if ImageFilter is not None:
        sheen = sheen.filter(ImageFilter.GaussianBlur(max(18, min(w, h) // 5)))
    image.alpha_composite(sheen)
    if editorial_identifier:
        draw.ellipse((x - 4, y - 4, x + w + 4, y + h + 4), outline=(*team_accent, 58 if winner else 34), width=1)
        draw.line((x + 2, y + h + 5, x + w - 2, y + h + 5), fill=(*team_accent, 102 if winner else 54), width=1)
    else:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=(2, 4, 9, 58), outline=(*team_accent, 72), width=1)
        draw.line((x + 16, y + h - 9, x + w - 16, y + h - 9), fill=(*team_accent, 118), width=2)
    logo = result.get("image")
    if logo is not None:
        logo = logo.copy()
        pad = max(8 if editorial_identifier else 18, min(w, h) // (9 if editorial_identifier and winner else 7 if editorial_identifier else 6 if winner else 5))
        logo.thumbnail((w - pad, h - pad), resample_filter())
        logo_x = x + (w - logo.width) // 2
        logo_y = y + (h - logo.height) // 2
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow.alpha_composite(logo, (logo_x + 3, logo_y + 4))
        shadow_alpha = shadow.split()[-1].point(lambda value: min(72, int(value * 0.34)))
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow.putalpha(shadow_alpha)
        if ImageFilter is not None:
            shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        image.alpha_composite(shadow)
        image.alpha_composite(logo, (logo_x, logo_y))
    else:
        draw_reference_text(image, (x + 10, y + 16, w - 20, h - 28), team_monogram(team), "context", 29, 16, team_accent, max_lines=1, align="center")
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
        "logo_treatment": "editorial_identifier" if editorial_identifier else "slot",
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
    draw_right_text(draw, width - 82, 88, REVIEW_DRAFT_PILL_LABEL, font(28, True), red)
    draw_chip(draw, 82, 162, template["angle_label"], gold, (19, 31, 49), 22)
    draw_chip(draw, 82 + 132, 162, format_label.upper(), (232, 239, 249), PALETTE["blue"], 20)
    draw.rectangle((54, height - 64, width - 54, height - 36), fill=red)
    draw.text((70, height - 62), REVIEW_DRAFT_FOOTER_LABEL, font=font(20, True), fill=ink)


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
            "key_performer": {"x": 60, "y": 808, "w": 960, "h": 100},
            "hook_takeaway": {"x": 60, "y": 922, "w": 960, "h": 92},
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
    draw.line((x, y + h - 12, x + w, y + h - 12), fill=(248, 250, 255, 216), width=2)
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
        center_x = left + width // 2
        y_cursor = y + max(0, (h - total_h) // 2) - 1
        first_x = center_x - first_w // 2
        second_x = center_x - second_w // 2
        block_w = max(first_w, second_w)
        draw.text((first_x, y_cursor), first, font=first_font, fill=PALETTE["ink"], stroke_width=2, stroke_fill=(0, 0, 0))
        draw.text((second_x, y_cursor + first_h + line_gap), second, font=second_font, fill=PALETTE["gold"], stroke_width=2, stroke_fill=(0, 0, 0))
        line_left = center_x - block_w // 2
        line_right = center_x + block_w // 2
        draw.line((line_left, y_cursor + total_h - 8, line_right, y_cursor + total_h - 8), fill=(*PALETTE["gold"], 140), width=2)
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


def draw_photo_first_public_header(image: Any, template_spec: Dict[str, Any], format_id: str, canvas_copy: Dict[str, str]) -> None:
    if ImageDraw is None:
        return
    title_x, title_y, title_w, title_h = zone_box(template_spec, "title")
    badge = template_spec.get("badge") if isinstance(template_spec.get("badge"), dict) else {}
    badge_right = int(badge.get("x", 48)) + max(int(badge.get("w", 80)), min(124, int(min(image.size) * 0.115)))
    left = max(title_x, badge_right + 40)
    width = max(360, title_x + title_w - left)
    is_square = format_id == "square_feed_1x1"
    kicker_type = photo_first_type_spec("kicker", square=is_square)
    headline_type = photo_first_type_spec("headline", square=is_square, story=format_id == "ig_story_9x16")
    result_y = title_y + (54 if not is_square else 48)
    draw = ImageDraw.Draw(image, "RGBA")
    draw_reference_text(
        image,
        (left, title_y + (4 if not is_square else 0), width, 42),
        clean(canvas_copy.get("kicker")) or "WNBA FINAL",
        kicker_type["font"],
        kicker_type["resolved_size"],
        kicker_type["resolved_min"],
        PALETTE["gold"],
        max_lines=1,
        align="left",
        stroke=kicker_type["stroke"],
    )
    draw_reference_text(
        image,
        (left, result_y, width, max(42, title_h - 50)),
        clean(canvas_copy.get("result_line")),
        headline_type["font"],
        headline_type["resolved_size"],
        headline_type["resolved_min"],
        PALETTE["ink"],
        max_lines=2 if is_square else 1,
        align="left",
        uppercase=False,
        stroke=headline_type["stroke"],
        stroke_fill=(0, 0, 0),
    )


def draw_module_callouts(image: Any, box: Tuple[int, int, int, int], callouts: List[Dict[str, str]], accent: tuple[int, int, int], *, compact: bool = False) -> int:
    if not callouts:
        return 0
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    if compact:
        chip_w = min(126, max(86, w // 5))
        chip_h = 30
        gap = 8
        start_x = x + w - (chip_w + gap) * min(2, len(callouts)) + gap
        for index, item in enumerate(callouts[:2]):
            cx = start_x + index * (chip_w + gap)
            draw.line((cx, y + 14, cx + chip_w, y + 10), fill=(*accent, 118), width=2)
            draw.line((cx, y + 10 + chip_h, cx + chip_w - 14, y + 10 + chip_h), fill=(248, 250, 255, 42), width=1)
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
        value_font = reference_font("score", 24)
        label_font = reference_font("context", 10)
        value = clean(item.get("value"))
        label = clean(item.get("label"))
        value_w, _ = text_size(draw, value, value_font)
        label_w, _ = text_size(draw, label, label_font)
        draw.line((cx + 4, top + 2, cx + card_w - 8, top - 4), fill=(*accent, 132), width=2)
        draw.line((cx + 4, top + 54, cx + card_w - 12, top + 50), fill=(248, 250, 255, 38), width=1)
        draw.rectangle((cx, top + 9, cx + 4, top + 45), fill=(*accent, 118 if index == 0 else 76))
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
        value_fill = PALETTE["gold"] if is_primary else PALETTE["ink"]
        label_fill = (235, 239, 247) if is_primary else accent
        draw.line((cx + 5, top + 4, cx + chip_w - 8, top - 2), fill=(*accent, 154 if is_primary else 92), width=2 if is_primary else 1)
        draw.line((cx + 5, top + chip_h - 5, cx + chip_w - 16, top + chip_h - 10), fill=(248, 250, 255, 40), width=1)
        draw.rectangle((cx, top + 9, cx + 5, top + chip_h - 12), fill=(*accent, 136 if is_primary else 82))
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
            draw_reference_text(image, (left + 10, y + h - 33, slot_w - 20, 18), "PHOTO CHECK", "context", 10, 7, PALETTE["ink"], max_lines=1, align="center")
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
            draw_reference_text(image, (left, top + size - 19, size, 16), "PHOTO CHECK", "context", 9, 7, PALETTE["ink"], max_lines=1, align="center")
        return size + (34 if compact else 42), "compact_headshot_chip"
    except Exception:
        return 0, "safe_no_photo_fallback"


def draw_stat_proof_rail(image: Any, box: Tuple[int, int, int, int], accent: tuple[int, int, int], *, compact: bool = False) -> None:
    if Image is None or ImageDraw is None:
        return
    x, y, w, h = box
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    rail_h = 5 if compact else 7
    split_x = x + int(w * 0.72)
    draw.rounded_rectangle((x + 12, y + 6, split_x, y + 6 + rail_h), radius=rail_h // 2, fill=(*accent, 214))
    draw.rounded_rectangle((split_x - 4, y + 6, x + w - 12, y + 6 + rail_h), radius=rail_h // 2, fill=(247, 203, 84, 190))
    draw.rectangle((x + 2, y + 2, x + 10, y + h - 2), fill=(*accent, 224))
    draw.rectangle((x + 10, y + 2, x + 14, y + h - 2), fill=(247, 203, 84, 164))
    image.alpha_composite(layer)


def draw_verified_stat_reference_module(image: Any, box: Tuple[int, int, int, int], module: Dict[str, Any], accent: tuple[int, int, int]) -> None:
    x, y, w, h = box
    compact = h < 112
    draw = ImageDraw.Draw(image, "RGBA")
    rail = Image.new("RGBA", image.size, (0, 0, 0, 0))
    rail_draw = ImageDraw.Draw(rail, "RGBA")
    rail_draw.polygon(
        [(x + 8, y + 14), (x + w - 16, y + 2), (x + w - 34, y + h - 12), (x + 18, y + h + 4)],
        fill=(1, 3, 8, 72 if compact else 82),
    )
    rail_draw.polygon(
        [(x + 18, y + 6), (x + int(w * 0.70), y - 4), (x + int(w * 0.48), y + h - 8), (x + 8, y + h)],
        fill=(*accent, 26 if compact else 34),
    )
    rail_draw.line((x + 20, y + 8, x + w - 32, y - 4), fill=(*accent, 112), width=2)
    rail_draw.line((x + 20, y + h - 11, x + w - 46, y + h - 22), fill=(248, 250, 255, 34), width=1)
    if ImageFilter is not None:
        glow = rail.filter(ImageFilter.GaussianBlur(10))
        image.alpha_composite(glow)
    image.alpha_composite(rail)
    draw_stat_proof_rail(image, box, accent, compact=compact)
    draw.line((x + 24, y + 38, x + w - 24, y + 30), fill=(*accent, 76), width=1)
    player = clean(module.get("player_name"))
    matchup = clean(module.get("matchup_note"))
    source_label = "STAT PROOF CHECK"
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


def photo_first_type_spec(key: str, *, compact: bool = False, square: bool = False, story: bool = False, winner: bool = False) -> Dict[str, Any]:
    spec = dict(PHOTO_FIRST_FINAL_SCORE_TYPE_SCALE.get(key, {}))
    if not spec:
        return {"level": "support", "font": "context", "size": 18, "min": 12, "stroke": 0}
    size = spec.get("size", 18)
    if winner and compact and spec.get("winner_compact_size"):
        size = spec.get("winner_compact_size")
    elif winner and spec.get("winner_size"):
        size = spec.get("winner_size")
    elif story and spec.get("story_size"):
        size = spec.get("story_size")
    elif compact and spec.get("compact_size"):
        size = spec.get("compact_size")
    elif square and spec.get("square_size"):
        size = spec.get("square_size")
    min_size = spec.get("min", 12)
    if compact and spec.get("compact_min"):
        min_size = spec.get("compact_min")
    elif square and spec.get("square_min"):
        min_size = spec.get("square_min")
    spec["resolved_size"] = int(size)
    spec["resolved_min"] = int(min_size)
    spec["stroke"] = int(spec.get("stroke", 0))
    return spec


def box_area(box: List[int]) -> int:
    return max(0, int(box[2])) * max(0, int(box[3]))


def photo_first_stage_bbox(geometry: Dict[str, Any]) -> List[int]:
    boxes = [
        geometry["photo_stage_box"],
        geometry["winner_score_row_box"],
        geometry["loser_score_row_box"],
        geometry["score_context_box"],
        geometry["stat_strip_box"],
    ]
    left = min(int(box[0]) for box in boxes)
    top = min(int(box[1]) for box in boxes)
    right = max(int(box[0]) + int(box[2]) for box in boxes)
    bottom = max(int(box[1]) + int(box[3]) for box in boxes)
    return [left, top, right - left, bottom - top]


def photo_first_athlete_visual_contract(geometry: Dict[str, Any]) -> Dict[str, Any]:
    stage_box = photo_first_stage_bbox(geometry)
    stage_area = max(1, box_area(stage_box))
    photo_area = box_area(geometry["photo_stage_box"])
    visual_share = round(photo_area / stage_area, 3)
    return {
        "athlete_visual_max_share": PHOTO_FIRST_ATHLETE_MAX_VISUAL_SHARE,
        "athlete_visual_share": visual_share,
        "athlete_visual_status": "athlete_supports_result" if visual_share <= PHOTO_FIRST_ATHLETE_MAX_VISUAL_SHARE else "athlete_over_cap_manual_review",
        "athlete_visual_stage_box": stage_box,
        "athlete_visual_policy": "final-score photo-first cards keep the person image under 40 percent of the active result stage so score and headline remain dominant.",
    }


def photo_first_safe_zone_contract(format_spec: Dict[str, Any], geometry: Dict[str, Any]) -> Dict[str, Any]:
    width, height = int(format_spec.get("width", 1080)), int(format_spec.get("height", 1350))
    format_id = clean(format_spec.get("format_id"))
    safe = dict(PHOTO_FIRST_SAFE_ZONES.get(format_id, PHOTO_FIRST_SAFE_ZONES["default"]))
    safe_box = [safe["left"], safe["top"], width - safe["left"] - safe["right"], height - safe["top"] - safe["bottom"]]
    critical_keys = ["winner_score_row_box", "loser_score_row_box", "score_context_box", "stat_strip_box", "matchup_angle_box"]
    violations: List[str] = []
    left, top, safe_w, safe_h = safe_box
    right, bottom = left + safe_w, top + safe_h
    for key in critical_keys:
        box = geometry.get(key)
        if not isinstance(box, list) or len(box) != 4:
            violations.append(f"{key}:missing")
            continue
        x, y, w, h = [int(value) for value in box]
        if x < left or y < top or x + w > right or y + h > bottom:
            violations.append(key)
    photo = geometry.get("photo_stage_box") if isinstance(geometry.get("photo_stage_box"), list) else [0, 0, 0, 0]
    hero_bleed = max(0, int(safe["left"]) - int(photo[0]))
    return {
        "safe_zone_px": safe,
        "safe_zone_box": safe_box,
        "safe_zone_status": "critical_content_inside_safe_zone" if not violations else "safe_zone_hold_manual_review",
        "safe_zone_violations": ",".join(violations) if violations else "none",
        "hero_grid_break_bleed_allowed": True,
        "hero_left_bleed_px": hero_bleed,
        "safe_zone_policy": "Critical score/stat/support modules stay inside safe zones; hero imagery may intentionally bleed for editorial composition.",
    }


def hero_asset_alpha_mode(path: Path | None) -> str:
    if path is None or Image is None or not path.exists():
        return "no_local_hero_asset"
    try:
        with Image.open(path) as handle:
            if "A" not in handle.convert("RGBA").getbands():
                return "opaque_rectangular_headshot"
            alpha = handle.convert("RGBA").getchannel("A")
            extrema = alpha.getextrema()
            if extrema and extrema[0] < 245:
                return "transparent_cutout_alpha_present"
    except Exception:
        return "hero_asset_alpha_unreadable"
    return "opaque_rectangular_headshot"


def hero_cutout_mode_contract(module: Dict[str, Any]) -> Dict[str, str]:
    variant_id = "photo_first_story"
    path = athlete_photo_render_source_path(module, variant_id) or athlete_photo_render_source_path(module, "photo_first_feed")
    alpha_mode = hero_asset_alpha_mode(path)
    if alpha_mode == "transparent_cutout_alpha_present":
        silhouette_mode = "local_transparent_cutout_grid_breaking"
        readiness = "cutout_ready_review_only_local_asset"
    elif alpha_mode == "no_local_hero_asset":
        silhouette_mode = "no_local_person_image"
        readiness = "cutout_not_available_no_download"
    else:
        silhouette_mode = "headshot_bridge_rectangular_source"
        readiness = "headshot_bridge_cutout_not_available"
    return {
        "hero_silhouette_mode": silhouette_mode,
        "hero_cutout_readiness": readiness,
        "hero_alpha_mode": alpha_mode,
        "grid_breaking_hero_contract": "transparent_local_cutout_may_break_grid; rectangular headshot stays a review-only bridge with no segmentation and no downloads",
    }


def photo_first_blueprint_depth_contract(geometry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "depth_layer_contract": "ghost_score_emblem_stage_wash_and_lower_third_bridge_layers_keep_critical_text_clear",
        "depth_layer_order": "background_texture,score_stage_wash,editorial_depth_bridge,ghost_score,decorative_emblem,hero,score,stat",
        "procedural_texture_contract": "local_code_generated_court_grain_stadium_light_score_stage_wash_and_grit_no_external_assets",
        "team_color_weighting": "winner_palette_dominant_loser_palette_localized_subdued",
        "score_asymmetry_contract": PHOTO_FIRST_SCORE_ASYMMETRY_CONTRACT,
        "ghost_score_anchor_box": geometry.get("photo_stage_box", []),
    }


def photo_first_layout_geometry(format_spec: Dict[str, Any]) -> Dict[str, Any]:
    width, height = int(format_spec.get("width", 1080)), int(format_spec.get("height", 1350))
    format_id = clean(format_spec.get("format_id"))
    is_story = height > 1500
    is_square = format_id == "square_feed_1x1" or height <= 1100
    if is_square:
        photo_box = [48, 350, 356, 374]
        score_top = 360
        score_h = 124
        score_gap = 20
        stat_box = [60, 740, 960, 64]
        hook_box = [60, 838, 960, 94]
        context_extra_gap = 34
    elif is_story:
        photo_box = [56, 520, 456, 684]
        score_top = 520
        score_h = 206
        score_gap = 24
        stat_box = [72, 1248, 936, 104]
        hook_box = [72, 1392, 936, 132]
        context_extra_gap = 48
    else:
        photo_box = [48, 370, 452, 580]
        score_top = 398
        score_h = 176
        score_gap = 24
        stat_box = [60, 994, 960, 84]
        hook_box = [60, 1118, 960, 104]
        context_extra_gap = 48
    score_x = photo_box[0] + photo_box[2] + 24
    score_w = width - score_x - PHOTO_FIRST_SAFE_ZONES.get(format_id, PHOTO_FIRST_SAFE_ZONES["default"])["right"]
    winner_row = [score_x, score_top, score_w, score_h]
    loser_row = [score_x, score_top + score_h + score_gap, score_w, score_h - 16]
    context_box = [score_x, score_top + score_h * 2 + context_extra_gap, score_w, 54]
    geometry = {
        "template_family": "approved_athlete_photo_final_score",
        "format_id": format_id,
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
    geometry.update(photo_first_athlete_visual_contract(geometry))
    geometry.update(photo_first_safe_zone_contract(format_spec, geometry))
    geometry.update(photo_first_blueprint_depth_contract(geometry))
    return geometry


def tuple_box(raw: List[int]) -> Tuple[int, int, int, int]:
    return int(raw[0]), int(raw[1]), int(raw[2]), int(raw[3])


def draw_photo_first_focal_depth_stage(
    image: Any,
    geometry: Dict[str, Any],
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = image.size
    photo = tuple_box(geometry["photo_stage_box"])
    winner = tuple_box(geometry["winner_score_row_box"])
    loser = tuple_box(geometry["loser_score_row_box"])
    stat = tuple_box(geometry["stat_strip_box"])
    hook = tuple_box(geometry["matchup_angle_box"])

    px, py, pw, ph = photo
    wx, wy, ww, wh = winner
    _lx, ly, _lw, lh = loser
    sx, sy, sw, sh = stat
    hx, hy, hw, hh = hook
    stage_left = max(0, min(px, sx, hx) - 24)
    stage_right = min(width, max(wx + ww, sx + sw, hx + hw) + 24)
    stage_top = max(0, min(py, wy) - 46)
    stage_bottom = min(height, max(py + ph, hy + hh) + 28)

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle(
        (stage_left, stage_top, stage_right, stage_bottom),
        radius=34,
        fill=(0, 0, 0, 14),
    )
    draw.polygon(
        [
            (stage_left + 18, stage_top + int((stage_bottom - stage_top) * 0.18)),
            (px + pw + 86, stage_top + 18),
            (stage_right - 34, stage_bottom - 54),
            (stage_left + 44, stage_bottom - 12),
        ],
        fill=(*primary, 12),
    )
    draw.polygon(
        [
            (px + pw - 24, stage_top + 8),
            (stage_right - 10, stage_top + 42),
            (stage_right - 42, ly + lh + 38),
            (px + pw + 20, ly + lh + 12),
        ],
        fill=(*secondary, 9),
    )
    draw.polygon(
        [
            (px + int(pw * 0.72), py + int(ph * 0.18)),
            (wx + int(ww * 0.56), wy - 18),
            (wx + int(ww * 0.88), ly + lh + 20),
            (px + int(pw * 0.70), py + int(ph * 0.92)),
        ],
        fill=(*primary, 16),
    )
    draw.polygon(
        [
            (px + int(pw * 0.62), py + int(ph * 0.36)),
            (wx + int(ww * 0.44), wy + int(wh * 0.22)),
            (wx + int(ww * 0.82), ly + int(lh * 0.78)),
            (px + int(pw * 0.58), py + int(ph * 0.76)),
        ],
        fill=(*PALETTE["gold"], 13),
    )
    draw.polygon(
        [
            (px + int(pw * 0.36), py + int(ph * 0.10)),
            (stage_right - 18, wy - 8),
            (stage_right - 42, ly + lh + 40),
            (px + int(pw * 0.30), py + int(ph * 0.90)),
        ],
        fill=(*primary, 8),
    )
    draw.polygon(
        [
            (px + int(pw * 0.48), py + int(ph * 0.22)),
            (stage_right - 86, wy + int(wh * 0.20)),
            (stage_right - 110, sy + 24),
            (px + int(pw * 0.54), sy + 8),
        ],
        fill=(*secondary, 7),
    )
    draw.ellipse(
        (px + int(pw * 0.46), wy - 42, stage_right + 54, ly + lh + 54),
        fill=(248, 250, 255, 7),
    )
    for offset in range(-80, stage_right - stage_left + 160, 46):
        draw.line(
            (
                stage_left + offset,
                sy - 142,
                stage_left + offset + int((stage_bottom - stage_top) * 0.42),
                sy + 18,
            ),
            fill=(*PALETTE["gold"], 10 if offset % 92 else 18),
            width=1,
        )
    draw.rectangle((px - 5, py + 22, px + 7, py + ph - 28), fill=(*primary, 66))
    draw.rectangle((wx - 5, wy + 20, wx + 5, wy + wh - 20), fill=(*primary, 50))
    draw.rectangle((wx - 5, ly + 18, wx + 5, ly + lh - 18), fill=(*secondary, 56))
    draw.line((stage_left + 48, sy - 16, stage_right - 48, sy - 16), fill=(*PALETTE["gold"], 58), width=1)
    draw.line((stage_left + 72, sy - 7, stage_right - 72, sy - 7), fill=(248, 250, 255, 10), width=1)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((px - 110, py - 96, px + pw + 152, py + ph + 132), fill=(*primary, 48))
    glow_draw.ellipse((px + 28, py + int(ph * 0.12), px + pw + 88, py + int(ph * 0.76)), fill=(248, 250, 255, 18))
    glow_draw.ellipse((px + int(pw * 0.40), py + int(ph * 0.28), wx + int(ww * 0.84), ly + lh + 62), fill=(*primary, 30))
    glow_draw.ellipse((px + int(pw * 0.56), py + int(ph * 0.40), wx + int(ww * 0.92), ly + lh + 90), fill=(*PALETTE["gold"], 24))
    glow_draw.ellipse((wx - 96, wy - 70, wx + ww + 70, ly + lh + 96), fill=(*secondary, 22))
    glow_draw.ellipse((sx + int(sw * 0.40), sy - 42, sx + sw + 80, sy + sh + 76), fill=(*PALETTE["gold"], 18))
    glow_draw.ellipse((px + int(pw * 0.28), wy - 80, stage_right + 90, sy + 74), fill=(*primary, 20))
    glow_draw.ellipse((px + int(pw * 0.52), wy + 20, stage_right + 120, sy + 110), fill=(*secondary, 14))
    if ImageFilter is not None:
        glow = glow.filter(ImageFilter.GaussianBlur(34))
        layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    image.alpha_composite(glow)
    image.alpha_composite(layer)


def draw_photo_first_editorial_depth_bridge(
    image: Any,
    geometry: Dict[str, Any],
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = image.size
    photo = tuple_box(geometry["photo_stage_box"])
    winner = tuple_box(geometry["winner_score_row_box"])
    loser = tuple_box(geometry["loser_score_row_box"])
    stat = tuple_box(geometry["stat_strip_box"])
    hook = tuple_box(geometry["matchup_angle_box"])

    px, py, pw, ph = photo
    wx, wy, ww, wh = winner
    lx, ly, lw, lh = loser
    sx, sy, sw, _sh = stat
    hx, hy, hw, hh = hook
    stage_left = max(0, min(px, sx, hx) - 18)
    stage_right = min(width, max(wx + ww, sx + sw, hx + hw) + 18)
    score_bottom = ly + lh
    lower_top = max(score_bottom + 18, sy - 34)
    lower_bottom = min(height, hy + hh + 22)

    bridge = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(bridge, "RGBA")
    draw.line((wx - 14, wy - 8, min(width - 48, wx + ww - 24), wy - 18), fill=(*primary, 30), width=1)
    draw.line((wx + 4, score_bottom + 12, min(width - 54, wx + ww - 42), score_bottom + 2), fill=(*secondary, 22), width=1)
    draw.polygon(
        [
            (px + int(pw * 0.68), py + int(ph * 0.30)),
            (wx + int(ww * 0.20), wy - 8),
            (wx + int(ww * 0.52), score_bottom + 28),
            (px + int(pw * 0.58), py + int(ph * 0.88)),
        ],
        fill=(*primary, 22),
    )
    draw.polygon(
        [
            (px + int(pw * 0.78), py + int(ph * 0.42)),
            (wx + int(ww * 0.44), wy + int(wh * 0.22)),
            (wx + int(ww * 0.86), score_bottom + 12),
            (sx + int(sw * 0.64), sy + 14),
            (sx + int(sw * 0.16), sy + 2),
        ],
        fill=(*secondary, 18),
    )
    draw.polygon(
        [
            (stage_left + 8, lower_top + 14),
            (stage_right - 30, lower_top - 2),
            (stage_right - 12, lower_bottom - 22),
            (stage_left + 22, lower_bottom + 3),
        ],
        fill=(1, 3, 8, 12),
    )
    draw.polygon(
        [
            (sx + 20, sy - 10),
            (sx + sw - 40, sy - 26),
            (hx + hw - 18, lower_bottom - 10),
            (hx + 16, lower_bottom + 4),
        ],
        fill=(*primary, 14),
    )
    draw.line((sx + 34, sy - 10, sx + sw - 40, sy - 18), fill=(*PALETTE["gold"], 68), width=2)
    draw.line((hx + 28, hy - 10, hx + hw - 40, hy - 14), fill=(*secondary, 30), width=1)
    draw.rectangle((stage_left + 4, lower_top + 24, stage_left + 7, lower_bottom - 24), fill=(*primary, 42))
    draw.line((stage_left + 24, lower_top + 8, stage_right - 44, lower_top - 2), fill=(*PALETTE["gold"], 42), width=1)
    draw.line((wx - 8, wy + wh - 8, wx + ww - 44, wy + wh - 8), fill=(*primary, 28), width=1)
    draw.line((lx + 10, ly + lh - 10, lx + lw - 54, ly + lh - 10), fill=(*secondary, 20), width=1)

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((sx - 100, sy - 76, sx + sw + 110, lower_bottom + 58), fill=(*PALETTE["gold"], 18))
    glow_draw.ellipse((wx - 62, wy - 62, wx + ww + 72, score_bottom + 74), fill=(*primary, 18))
    if ImageFilter is not None:
        glow = glow.filter(ImageFilter.GaussianBlur(30))
        bridge = bridge.filter(ImageFilter.GaussianBlur(0.45))
    image.alpha_composite(glow)
    image.alpha_composite(bridge)


def draw_photo_first_blueprint_depth_layers(
    image: Any,
    geometry: Dict[str, Any],
    score: Dict[str, str],
    winner_profile: Dict[str, Any],
    loser_profile: Dict[str, Any],
    aliases: Dict[str, str],
    logos: Dict[str, Dict[str, str]],
) -> None:
    if Image is None or ImageDraw is None:
        return
    width, height = image.size
    photo = tuple_box(geometry["photo_stage_box"])
    winner = tuple_box(geometry["winner_score_row_box"])
    loser = tuple_box(geometry["loser_score_row_box"])
    primary = winner_profile["accent_rgb"] if isinstance(winner_profile.get("accent_rgb"), tuple) else PALETTE["gold"]
    secondary = loser_profile["accent_rgb"] if isinstance(loser_profile.get("accent_rgb"), tuple) else PALETTE["blue"]
    px, py, pw, ph = photo
    wx, wy, ww, wh = winner
    lx, ly, lw, lh = loser

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    winner_font = reference_font("score", 230 if height <= 1350 else 260)
    loser_font = reference_font("score", 128 if height <= 1350 else 152)
    team_font = reference_font("display", 82 if height <= 1350 else 96)
    winner_score = clean(score.get("winner_score"))
    loser_score = clean(score.get("loser_score"))
    if winner_score:
        draw.text((max(12, px + int(pw * 0.18)), py + int(ph * 0.03)), winner_score, font=winner_font, fill=(*primary, 34))
        draw.text((px + int(pw * 0.42), py + int(ph * 0.30)), winner_score, font=winner_font, fill=(248, 250, 255, 13))
    winner_word = short_team(clean(score.get("winner")))
    if winner_word:
        draw.text((max(10, px + int(pw * 0.05)), py + int(ph * 0.58)), winner_word, font=team_font, fill=(*primary, 28))
    if loser_score:
        draw.text((lx + int(lw * 0.58), ly + int(lh * 0.08)), loser_score, font=loser_font, fill=(*secondary, 18))

    logo_result = enrich_logo_result(load_team_logo(clean(score.get("winner")), aliases, logos), primary, "winner_decorative_emblem")
    logo = logo_result.get("image")
    if logo is not None:
        mark = logo.copy()
        mark.thumbnail((300 if height <= 1350 else 360, 300 if height <= 1350 else 360), resample_filter())
        alpha = mark.split()[-1].point(lambda value: min(34, int(value * 0.16)))
        mark.putalpha(alpha)
        layer.alpha_composite(mark, (min(width - 96, wx + int(ww * 0.58)), max(0, wy - int(mark.height * 0.36))))

    draw.line((wx - 22, wy + int(wh * 0.46), wx + ww - 18, wy + int(wh * 0.46)), fill=(*primary, 36), width=2)
    draw.line((lx + 8, ly + int(lh * 0.55), lx + lw - 28, ly + int(lh * 0.55)), fill=(*secondary, 24), width=1)
    if ImageFilter is not None:
        layer = layer.filter(ImageFilter.GaussianBlur(0.35))
    image.alpha_composite(layer)


def photo_first_score_team_text_box(box: Tuple[int, int, int, int], *, winner: bool = False) -> Tuple[int, int, int, int]:
    x, y, w, h = box
    logo_size = min(h - 54, 76 if winner else 66)
    score_box = photo_first_score_slab_box(box, winner=winner)
    text_x = x + logo_size + (50 if h > 130 else 44)
    score_gap = 34 if h > 130 else 28
    text_w = max(112, min(max(112, w - logo_size - 248), score_box[0] - text_x - score_gap))
    return (text_x, y + (50 if h > 130 else 42), text_w, h - (68 if h > 130 else 58))


def photo_first_score_slab_box(box: Tuple[int, int, int, int], *, winner: bool = False) -> Tuple[int, int, int, int]:
    x, y, w, h = box
    compact = h <= 130
    if winner:
        slab_w = min(226 if not compact else 176, max(150 if compact else 184, int(w * (0.350 if compact else 0.365))))
    else:
        slab_w = min(160 if not compact else 132, max(116 if compact else 132, int(w * (0.240 if compact else 0.255))))
    inset_y = 22 if not compact else 15
    right_inset = 28 if not compact else 26
    return (x + w - slab_w - right_inset, y + inset_y, slab_w, h - inset_y * 2)


def photo_first_score_digit_cell_box(score_box: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    sx, sy, sw, sh = score_box
    inset_x = 18 if sh > 84 else 13
    inset_y = 10
    return (sx + inset_x, sy + inset_y, sx + sw - 10, sy + sh - inset_y)


def photo_first_stage_caption(module: Dict[str, Any]) -> str:
    callouts = module.get("callouts") if isinstance(module.get("callouts"), list) else []
    parts = [
        f"{clean(item.get('value'))} {clean(item.get('label')).upper()}".strip()
        for item in callouts
        if isinstance(item, dict) and clean(item.get("value")) and clean(item.get("label"))
    ]
    if parts:
        return " / ".join(parts[:2])
    if clean(module.get("athlete_photo_review_variant_status")) == "review_variant_available":
        return "SOURCE PHOTO / REVIEW CROP"
    return "REVIEW-ONLY PHOTO"


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
        photo = prepared_athlete_photo_focus_fill(path, w + 12, h - 36, focus_y=focus_y)
        if ImageFilter is not None:
            photo = photo.filter(ImageFilter.UnsharpMask(radius=1.1, percent=170, threshold=2))
    except Exception:
        return False
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((x + 24, y + 52, x + w + 16, y + h + 18), radius=34, fill=(0, 0, 0, 16))
    draw.rectangle((x + 1, y + 104, x + 3, y + h - 92), fill=(*accent, 34))
    draw.polygon([(x + 16, y + h - 172), (x + w - 2, y + h - 318), (x + w - 2, y + h - 8), (x + 16, y + h - 8)], fill=(*accent, 16))
    draw.polygon([(x + 30, y + 86), (x + w - 4, y + 10), (x + w - 6, y + 128), (x + 30, y + 190)], fill=(255, 255, 255, 10))
    draw.polygon([(x + 24, y + 24), (x + w - 18, y + 24), (x + w - 92, y + 54), (x + 44, y + 62)], fill=(*PALETTE["gold"], 20))
    draw.line((x + 48, y + 34, x + w - 54, y + 28), fill=(*accent, 26), width=1)
    draw.line((x + 48, y + h - 70, x + w - 58, y + h - 74), fill=(*accent, 22), width=1)
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((x - 126, y - 38, x + w + 138, y + h + 132), fill=(*accent, 60))
    glow_draw.ellipse((x - 8, y + 48, x + w + 34, y + int(h * 0.78)), fill=(248, 250, 255, 34))
    glow_draw.ellipse((x + 18, y + h - 256, x + w + 82, y + h + 64), fill=(*PALETTE["gold"], 26))
    glow_draw.ellipse((x - 44, y + int(h * 0.18), x + w + 28, y + int(h * 0.62)), fill=(*PALETTE["gold"], 16))
    if ImageFilter is not None:
        glow = glow.filter(ImageFilter.GaussianBlur(38))
    layer.alpha_composite(glow)
    photo_x = x - 6
    photo_y = y + h - photo.height - 16
    stage_photo = Image.new("RGBA", image.size, (0, 0, 0, 0))
    stage_photo.alpha_composite(photo, (photo_x, photo_y))
    stage_mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(stage_mask)
    mask_draw.rounded_rectangle((x + 2, y + 20, x + w - 2, y + h - 8), radius=12, fill=255)
    layer.alpha_composite(Image.composite(stage_photo, Image.new("RGBA", image.size, (0, 0, 0, 0)), stage_mask))
    draw.arc((x - 42, y + 20, x + w + 50, y + h + 82), start=198, end=300, fill=(*PALETTE["gold"], 48), width=1)
    draw.arc((x - 22, y + 44, x + w + 28, y + h + 48), start=208, end=290, fill=(248, 250, 255, 12), width=1)
    draw.line((x + w - 22, y + 116, x + w - 22, y + h - 172), fill=(*PALETTE["gold"], 22), width=1)
    draw.line((x + 20, y + 54, x + min(x + 152, x + w - 34), y + 42), fill=(248, 250, 255, 32), width=1)
    draw.line((x + max(170, int(w * 0.46)), y + h - 88, x + w - 28, y + h - 88), fill=(*PALETTE["gold"], 42), width=1)
    image.alpha_composite(layer)
    player = clean(module.get("player_name")) or "APPROVED ATHLETE"
    draw_reference_text(image, (x + 34, y + 42, w - 72, 32), player, "context", 21, 13, (230, 236, 246), max_lines=1, align="left", uppercase=False)
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
    compact = h <= 130
    draw = ImageDraw.Draw(image, "RGBA")
    rail_shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(rail_shadow, "RGBA")
    shadow_draw.polygon(
        [
            (x + 4, y + h - 36),
            (x + w - 38, y + h - 58),
            (x + w + 4, y + h - 4),
            (x + 18, y + h + 3),
        ],
        fill=(0, 0, 0, 3 if winner else 1),
    )
    if ImageFilter is not None:
        rail_shadow = rail_shadow.filter(ImageFilter.GaussianBlur(12))
    image.alpha_composite(rail_shadow)
    draw.line((x + 2, y + h - 30, x + w - 34, y + h - 30), fill=(*accent, 38 if winner else 18), width=2 if winner else 1)
    draw.line((x + 1, y + 40, x + 1, y + h - 40), fill=(*accent, 50 if winner else 20), width=2 if winner else 1)
    logo_size = min(h - 46, 86 if winner else 58)
    logo_box = (x + 32, y + (h - logo_size) // 2 + (18 if not compact else 14), logo_size, logo_size)
    draw_team_logo_slot(image, team, logo_box, aliases, logos, accent, winner=winner, treatment="editorial_identifier")
    score_box = photo_first_score_slab_box(box, winner=winner)
    team_text_box = photo_first_score_team_text_box(box, winner=winner)
    team_type = photo_first_type_spec("team", compact=compact, winner=winner)
    draw_reference_text(
        image,
        team_text_box,
        short_team(team),
        team_type["font"],
        team_type["resolved_size"],
        team_type["resolved_min"],
        PALETTE["ink"] if winner else (170, 180, 194),
        max_lines=2,
        stroke=team_type["stroke"],
    )

    sx, sy, sw, sh = score_box
    score_glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(score_glow, "RGBA")
    glow_draw.ellipse((sx - 42, sy - 28, sx + sw + 48, sy + sh + 30), fill=(*accent, 18 if winner else 6))
    if ImageFilter is not None:
        score_glow = score_glow.filter(ImageFilter.GaussianBlur(15))
    image.alpha_composite(score_glow)
    draw.line((sx + 8, sy + 14, sx + 8, sy + sh - 14), fill=(*accent, 58 if winner else 24), width=2)
    draw.line((sx + 24, sy + sh - 8, sx + sw - 12, sy + sh - 8), fill=(*accent, 24 if winner else 12), width=1)
    draw.line((sx + 36, sy + 8, sx + sw - 24, sy + 8), fill=(248, 250, 255, 54 if winner else 24), width=1)
    cell = photo_first_score_digit_cell_box(score_box)
    score_type = photo_first_type_spec("score", compact=compact, winner=winner)
    score_size = min(score_type["resolved_size"] + (12 if winner else 4), max(58, int((cell[2] - cell[0]) * 0.92)), max(58, int((cell[3] - cell[1]) * 1.02)))
    min_score_size = score_type["resolved_min"]
    draw_reference_text(
        image,
        (cell[0] + 3, cell[1] - 2, cell[2] - cell[0] - 6, cell[3] - cell[1] + 3),
        score_value,
        score_type["font"],
        score_size,
        min_score_size,
        PALETTE["ink"] if winner else (178, 184, 194),
        max_lines=1,
        align="right",
        stroke=1,
        stroke_fill=(0, 0, 0),
    )


def draw_photo_first_score_context_rail(
    image: Any,
    box: Tuple[int, int, int, int],
    text: str,
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
) -> None:
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow, "RGBA")
    shadow_draw.polygon(
        [(x + 4, y + h - 14), (x + w - 18, y + 9), (x + w + 4, y + h - 4), (x + 14, y + h + 6)],
        fill=(0, 0, 0, 12),
    )
    if ImageFilter is not None:
        shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    image.alpha_composite(shadow)
    draw.line((x + 28, y + 13, x + w - 34, y + 8), fill=(*PALETTE["gold"], 26), width=1)
    draw.line((x + 7, y + 19, x + 7, y + h - 19), fill=(*primary, 96), width=2)
    draw.line((x + 30, y + 13, x + w - 30, y + 13), fill=(*PALETTE["gold"], 30), width=1)
    context_type = photo_first_type_spec("context_rail", compact=h <= 54)
    draw_reference_text(
        image,
        (x + 22, y + 9, w - 44, h - 16),
        text,
        context_type["font"],
        context_type["resolved_size"],
        context_type["resolved_min"],
        PALETTE["ink"],
        max_lines=1,
        stroke=context_type["stroke"],
    )


def photo_first_score_context_text(score: Dict[str, str], stat_module: Dict[str, Any]) -> str:
    return ""


def draw_photo_first_score_bridge_accent(
    image: Any,
    box: Tuple[int, int, int, int],
    primary: tuple[int, int, int],
    secondary: tuple[int, int, int],
) -> None:
    x, y, w, h = box
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line((x + 10, y + h // 2, x + w - 10, y + h // 2), fill=(*PALETTE["gold"], 46), width=1)
    draw.line((x + 10, y + h // 2 + 5, x + int(w * 0.62), y + h // 2 + 5), fill=(*primary, 36), width=1)
    draw.line((x + int(w * 0.72), y + h // 2 - 5, x + w - 10, y + h // 2 - 5), fill=(*secondary, 34), width=1)


def draw_photo_first_stat_strip(image: Any, box: Tuple[int, int, int, int], module: Dict[str, Any], accent: tuple[int, int, int], canvas_copy: Dict[str, str] | None = None) -> None:
    x, y, w, h = box
    compact = h <= 104
    draw = ImageDraw.Draw(image, "RGBA")
    wash = Image.new("RGBA", image.size, (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash, "RGBA")
    wash_draw.polygon(
        [
            (x + 12, y + 24),
            (x + w - 18, y + 4),
            (x + w - 24, y + h - 10),
            (x + 20, y + h + 6),
        ],
        fill=(0, 0, 0, 8),
    )
    wash_draw.polygon(
        [
            (x + int(w * 0.18), y + 10),
            (x + w - 28, y + 20),
            (x + int(w * 0.86), y + h - 2),
            (x + 34, y + h - 4),
        ],
        fill=(*accent, 7),
    )
    if ImageFilter is not None:
        wash = wash.filter(ImageFilter.GaussianBlur(6))
    image.alpha_composite(wash)
    band = Image.new("RGBA", image.size, (0, 0, 0, 0))
    band_draw = ImageDraw.Draw(band, "RGBA")
    band_draw.line((x + 34, y + 12, x + w - 44, y + 5), fill=(*PALETTE["gold"], 62), width=2)
    band_draw.line((x + 40, y + h - 10, x + int(x + w * 0.46), y + h - 15), fill=(248, 250, 255, 12), width=1)
    band_draw.line((x + 16, y + 20, x + 16, y + h - 20), fill=(*accent, 62), width=1)
    image.alpha_composite(band)
    player = clean(module.get("player_name"))
    copy = canvas_copy or {}
    athlete_line = clean(copy.get("athlete_line")) or clean(module.get("body")) or (f"{last_name(player).title()} led the final." if player else "Final score confirmed.")
    stat_line = clean(copy.get("stat_line")) or public_stat_line(module.get("callouts") or [])
    athlete_type = photo_first_type_spec("athlete_line", compact=compact)
    stat_type = photo_first_type_spec("stat", compact=compact)
    if compact:
        caption = f"{last_name(player).title()}: {stat_line}" if player and stat_line else (stat_line or athlete_line)
        draw_reference_text(
            image,
            (x + 32, y + max(15, h // 2 - 15), w - 64, 34),
            caption,
            stat_type["font"],
            max(stat_type["resolved_size"], athlete_type["resolved_min"]),
            stat_type["resolved_min"],
            PALETTE["ink"],
            max_lines=1,
            uppercase=False,
            stroke=stat_type["stroke"],
        )
        return
    draw_reference_text(
        image,
        (x + 32, y + (20 if not compact else 15), w - 64, 40 if not compact else 30),
        athlete_line,
        athlete_type["font"],
        athlete_type["resolved_size"],
        athlete_type["resolved_min"],
        PALETTE["ink"],
        max_lines=1 if compact else 2,
        uppercase=False,
        stroke=athlete_type["stroke"],
    )
    draw_reference_text(
        image,
        (x + 32, y + (64 if not compact else 45), w - 64, 32 if not compact else 24),
        stat_line,
        stat_type["font"],
        stat_type["resolved_size"],
        stat_type["resolved_min"],
        PALETTE["gold"],
        max_lines=1,
        uppercase=False,
        stroke=stat_type["stroke"],
    )


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

    geometry = photo_first_layout_geometry(format_spec)
    draw_reference_background(image, "final", winner_accent, loser_accent, photo_first=True)
    draw_photo_first_focal_depth_stage(image, geometry, winner_accent, loser_accent)
    draw_photo_first_editorial_depth_bridge(image, geometry, winner_accent, loser_accent)
    draw_photo_first_blueprint_depth_layers(image, geometry, score, winner_profile, loser_profile, aliases, logos)
    draw_reference_badge(image, template_spec)
    canvas_copy = photo_first_public_canvas_copy(score, stat_module)
    draw_photo_first_public_header(image, template_spec, format_id, canvas_copy)
    photo_box = tuple_box(geometry["photo_stage_box"])
    focus_box = tuple_box(geometry["photo_face_focus_box"])
    winner_box = tuple_box(geometry["winner_score_row_box"])
    loser_box = tuple_box(geometry["loser_score_row_box"])
    context_box = tuple_box(geometry["score_context_box"])
    stat_box = tuple_box(geometry["stat_strip_box"])

    photo_ok = draw_photo_first_athlete_stage(image, photo_box, stat_module, winner_accent, focus_box)
    if not photo_ok:
        return False

    draw_photo_first_score_row(image, winner_box, score["winner"], score["winner_score"], winner_accent, aliases, logos, winner=True)
    draw_photo_first_score_row(image, loser_box, score["loser"], score["loser_score"], loser_accent, aliases, logos, winner=False)

    score_bridge_text = photo_first_score_context_text(score, stat_module)
    if score_bridge_text:
        draw_photo_first_score_context_rail(image, context_box, score_bridge_text, winner_accent, loser_accent)
    else:
        draw_photo_first_score_bridge_accent(image, context_box, winner_accent, loser_accent)

    draw_photo_first_stat_strip(image, stat_box, stat_module, winner_accent, canvas_copy)
    draw_reference_guardrail(image, compact_footer=format_id == "square_feed_1x1")
    return True


def draw_lower_reference_module(image: Any, box: Tuple[int, int, int, int], eyebrow: str, body: str, accent: tuple[int, int, int], *, headline: str = "", callouts: List[Dict[str, str]] | None = None) -> None:
    x, y, w, h = box
    compact = h <= 122
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer, "RGBA")
    layer_draw.polygon(
        [(x + 10, y + 14), (x + w - 18, y + 2), (x + w - 38, y + h - 10), (x + 18, y + h + 4)],
        fill=(1, 3, 8, 34 if compact else 40),
    )
    layer_draw.polygon(
        [(x + 20, y + 6), (x + int(w * 0.72), y - 5), (x + int(w * 0.48), y + h - 8), (x + 8, y + h)],
        fill=(*accent, 17 if compact else 22),
    )
    layer_draw.line((x + 20, y + 8, x + w - 28, y - 5), fill=(*accent, 78), width=1)
    layer_draw.line((x + 20, y + h - 10, x + w - 42, y + h - 22), fill=(248, 250, 255, 18), width=1)
    layer_draw.line((x + 5, y + 20, x + 5, y + h - 18), fill=(*accent, 58), width=2)
    if ImageFilter is not None:
        image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(12)))
    image.alpha_composite(layer)
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
        body_top += 24 if compact else 48
    body_h = y + h - body_top - (10 if compact else 14)
    if compact and body_h < 18:
        return
    draw_reference_text(
        image,
        (x + 24, body_top, text_w, max(18, body_h) if compact else max(28, body_h)),
        body,
        "body",
        18 if compact else 27,
        11 if compact else 14,
        PALETTE["ink"],
        max_lines=1 if compact else 2,
        uppercase=False,
    )


def draw_score_lanes(image: Any, template_spec: Dict[str, Any], primary_accent: tuple[int, int, int], secondary_accent: tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    lane_pairs = [
        ("primary_logo_slot", "primary_score", primary_accent, True),
        ("secondary_logo_slot", "secondary_score", secondary_accent, False),
    ]
    for logo_name, score_name, accent, winner in lane_pairs:
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
        lane_draw.polygon(
            [(x1 + 8, y1 + 2), (x2 - 28, y1 + 2), (x2 - 4, y2 - 10), (x1 + 36, y2 - 10)],
            fill=(0, 0, 0, 36 if winner else 24),
        )
        lane_draw.polygon(
            [(x1 + 26, y1 + 8), (x2 - 18, y1 + 8), (x2 - 52, y2 - 18), (x1 + 6, y2 - 18)],
            fill=(*accent, 15 if winner else 10),
        )
        lane_draw.line((x1 + 10, y1 + 4, x2 - 24, y1 + 4), fill=(*accent, 108 if winner else 70), width=2 if winner else 1)
        lane_draw.line((x1 + 30, y2 - 16, x2 - 18, y2 - 16), fill=(*accent, 78 if winner else 48), width=1)
        lane_draw.line((x1 + max(190, lw + 28), y1 + 20, x1 + max(190, lw + 28), y2 - 28), fill=(255, 255, 255, 18), width=1)
        lane_draw.line((x2 - max(248, sw + 24), y1 + 18, x2 - 20, y1 + 18), fill=(255, 255, 255, 14), width=1)
        lane_draw.line((x1 + 2, y1 + 12, x1 + 2, y2 - 22), fill=(*accent, 78 if winner else 48), width=2)
        lane_draw.line((x2 - 6, y1 + 34, x2 - 6, y2 - 50), fill=(255, 255, 255, 16 if winner else 10), width=1)
        if ImageFilter is not None:
            glow = lane_layer.filter(ImageFilter.GaussianBlur(16))
            image.alpha_composite(glow)
        image.alpha_composite(lane_layer)


def draw_logo_first_score_atmosphere(image: Any, template_spec: Dict[str, Any], primary_accent: tuple[int, int, int], secondary_accent: tuple[int, int, int]) -> None:
    if Image is None or ImageDraw is None:
        return
    boxes = [
        zone_box(template_spec, "primary_logo_slot"),
        zone_box(template_spec, "primary_score"),
        zone_box(template_spec, "secondary_logo_slot"),
        zone_box(template_spec, "secondary_score"),
    ]
    active = [box for box in boxes if box[2] and box[3]]
    if not active:
        return
    x1 = max(28, min(box[0] for box in active) - 34)
    y1 = max(0, min(box[1] for box in active) - 36)
    x2 = min(image.size[0] - 28, max(box[0] + box[2] for box in active) + 30)
    y2 = min(image.size[1], max(box[1] + box[3] for box in active) + 34)

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.polygon(
        [(x1, y1 + 18), (x2 - 28, y1), (x2, y2 - 24), (x1 + 22, y2)],
        fill=(1, 3, 8, 30),
    )
    draw.polygon(
        [(x1, y1 + 8), (x1 + int((x2 - x1) * 0.58), y1 + 8), (x1 + int((x2 - x1) * 0.34), y2 - 4), (x1, y2 - 4)],
        fill=(*primary_accent, 22),
    )
    draw.polygon(
        [(x2, y1 + 16), (x2 - int((x2 - x1) * 0.50), y1 + 16), (x2 - int((x2 - x1) * 0.22), y2), (x2, y2)],
        fill=(*secondary_accent, 18),
    )
    draw.line((x1 + 4, y1 + 16, x1 + 4, y2 - 16), fill=(*primary_accent, 58), width=3)
    draw.line((x1 + 18, y1 + int((y2 - y1) * 0.48), x2 - 14, y1 + int((y2 - y1) * 0.48)), fill=(*secondary_accent, 42), width=1)
    draw.line((x1 + 26, y1 + 18, x2 - 26, y1 + 2), fill=(255, 255, 255, 28), width=1)
    draw.line((x1 + 26, y2 - 4, x2 - 26, y2 - 18), fill=(255, 255, 255, 20), width=1)
    if ImageFilter is not None:
        glow = layer.filter(ImageFilter.GaussianBlur(22))
        image.alpha_composite(glow)
    image.alpha_composite(layer)


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
        clean(stat_module.get("status")) in {"verified_player_stat_module", "verified_supporting_stat_module"}
        and photo_first_eligible(stat_module)
        and draw_photo_first_final_score_template(image, packet, template, format_spec, score, reference, stat_module)
    ):
        return

    draw_reference_background(image, "final", winner_accent, loser_accent)
    draw_reference_badge(image, template_spec)

    draw_final_score_reference_title(image, template_spec, format_id)

    context_box = zone_box(template_spec, "context_row")
    draw_logo_first_score_atmosphere(image, template_spec, winner_accent, loser_accent)
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

    draw_reference_guardrail(image, compact_footer=format_id == "square_feed_1x1")


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
        summary = {
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
            "proof_artifact_bridge_used": clean(stat_module.get("proof_artifact_bridge_used")),
            "proof_id": clean(stat_module.get("proof_id")),
            "proof_source": clean(stat_module.get("proof_source")),
            "proof_status": clean(stat_module.get("proof_status")),
            "proof_review_only": clean(stat_module.get("proof_review_only")),
            "proof_source_url": clean(stat_module.get("proof_source_url")),
            "proof_source_domain": clean(stat_module.get("proof_source_domain")),
            "proof_operator_note_path": clean(stat_module.get("proof_operator_note_path")),
            "proof_limitations": clean(stat_module.get("proof_limitations")),
            "athlete_led_render_status": clean(stat_module.get("athlete_led_render_status")),
            "athlete_led_missing_fields": clean(stat_module.get("athlete_led_missing_fields")),
            "athlete_led_blocker": clean(stat_module.get("athlete_led_blocker")),
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
        summary.update(visual_mode_contract(summary))
        return summary
    edge = game_edge_module(score)
    summary = {
        "content_module_mode": "game_edge_fallback",
        "content_module_status": clean(stat_module.get("status")) or "fallback_game_edge_no_verified_stat_text",
        "content_module_title": clean(edge.get("headline")),
        "content_module_body": clean(edge.get("body")),
        "content_module_game_shape": clean(edge.get("game_shape")),
        "content_module_game_shape_label": clean(edge.get("game_shape_label")),
        "content_module_stat_count": "0",
        "content_module_player": "",
        "content_module_source_text": "",
        "proof_artifact_bridge_used": clean(stat_module.get("proof_artifact_bridge_used")) or "false",
        "proof_source": clean(stat_module.get("proof_source")),
        "athlete_led_render_status": clean(stat_module.get("athlete_led_render_status")) or "athlete_led_blocked_missing_verified_player_context",
        "athlete_led_missing_fields": clean(stat_module.get("athlete_led_missing_fields")) or "athlete_name, approved local image/cutout path, verified stat/story context",
        "athlete_led_blocker": clean(stat_module.get("athlete_led_blocker")) or "No athlete-led preview produced: handoff lacks athlete_name/top_performers, approved local image/cutout path, and verified stat/story context.",
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
    summary.update(visual_mode_contract(summary))
    return summary


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
            "athlete_photo_layout_mode": "square_photo_first_score_panel",
            "athlete_photo_layout_status": "approved_photo_first_square_template",
            "athlete_photo_layout_detail": "Approved local headshot becomes a square-native focal panel with compact score rails and proof module.",
            "athlete_photo_template_family": "approved_square_athlete_photo_final_score",
        }
    return {
        "athlete_photo_layout_mode": "photo_first_final_score",
        "athlete_photo_layout_status": "approved_photo_first_template",
        "athlete_photo_layout_detail": "Approved local headshot becomes the main editorial visual with score lanes and verified stat modules kept review-only.",
        "athlete_photo_template_family": "approved_athlete_photo_final_score",
    }


def visual_mode_contract(content_module: Dict[str, Any], layout: Dict[str, str] | None = None) -> Dict[str, str]:
    layout = layout or {}
    layout_mode = clean(layout.get("athlete_photo_layout_mode"))
    status = clean(content_module.get("content_module_status"))
    player = clean(content_module.get("content_module_player"))
    missing = clean(content_module.get("athlete_led_missing_fields"))
    photo_ready = photo_first_eligible(content_module)
    is_player_stat = status == "verified_player_stat_module"
    is_supporting_stat = status == "verified_supporting_stat_module"
    visual_mode = "no_photo_premium_result"
    focal_entity_type = "team_matchup"
    hero_asset_required = "approved_local_athlete_photo_missing"
    score_lock_variant = "final_score_locked_logo_first"
    proof_strip_variant = "score_edge_only"
    copy_unlock_state = "score_only_copy_locked_manual_review"
    focal_priority = "non_athlete_fallback"
    athlete_focal_contract = "logo_score_fallback_not_athlete_led"
    fallback_comparison_status = "fallback_active_label_no_athlete_photo"
    fallback_comparison_note = "No athlete/person focal frame rendered; hold if the handoff expected an athlete-led result or if the score treatment reads like a dashboard card."
    score_layout_contract = "logo_first_borderless_editorial_score_spine_no_dashboard_panels"
    anti_dashboard_contract = "open_score_spine_no_nested_cards_no_metric_tiles"
    anti_dashboard_review_cue = "Hold or revise if the no-photo fallback reads as a dashboard card, boxed scoreboard row, solid backing panel, or ad unit instead of a premium sports editorial plate."
    lower_third_contract = "editorial_stat_rail_open_no_heavy_card_container"
    lower_third_review_cue = "Hold or revise if lower stat/caption treatment reads as a card, dashboard module, solid lower-third box, or heavy boxed lower-third."
    hero_image_mode = "logo_score_fallback_no_person_image"
    hero_image_source_class = "no_local_hero_image"
    action_photo_hero_contract = "manual_review_action_photo_not_available_no_download"
    action_photo_candidate_status = "not_available_to_renderer"
    action_photo_readiness_contract = "review_draft_ok_premium_final_score_needs_action_photo_candidate"
    action_photo_slot_expectation = "future_local_action_photo_candidate_only_after_manual_intake_no_download"
    action_photo_subject_metadata_required = "entity_id,athlete_name,team,rights_class,identity_confidence,intended_review_only_use"
    action_photo_crop_metadata_required = "subject_bbox_or_focus_zone,full_body_or_in_game_context,crop_safety,background_clearance,score_text_clearance"
    action_photo_operator_review_cue = (
        "No action-photo candidate is available to the renderer; this logo/headshot fallback may be reviewed as a draft, "
        "but premium final-score editorial needs a manually cleared action-photo candidate with subject and crop metadata."
    )
    headshot_bridge_status = "not_in_use_no_local_person_image"
    composition_balance_contract = "logo_score_fallback_balance_action_photo_slot_reserved"
    action_photo_replacement_composition_cue = (
        "Keep right-side score spine and lower rail readable while reserving a left-side action-photo lane for a future "
        "manually cleared in-game candidate."
    )
    headshot_bridge_composition_cue = "No headshot bridge is rendered; hold if the fallback still feels like a roster or profile card."
    lower_left_right_balance_review_cue = (
        "Hold or revise if the lower rail overweights one corner, flattens editorial tension, or leaves no believable action-photo replacement lane."
    )
    roster_portrait_risk_cue = (
        "Review as fallback only; premium final-score editorial should not resolve as a static roster portrait or profile-card composition."
    )
    hero_silhouette_mode = "no_local_person_image"
    hero_cutout_readiness = "cutout_not_available_no_download"
    hero_alpha_mode = "no_local_hero_asset"
    grid_breaking_hero_contract = "transparent_local_cutout_may_break_grid; no image downloads or segmentation"
    template_fit_reason = clean(content_module.get("athlete_led_blocker")) or "No approved player photo and verified player stat context; renderer holds photo-first route."
    if photo_ready and player and (is_player_stat or is_supporting_stat):
        cutout_contract = hero_cutout_mode_contract(content_module)
        visual_mode = "photo_first_performer" if is_player_stat else "photo_first_result"
        focal_entity_type = "athlete"
        hero_asset_required = "approved_local_athlete_photo"
        score_lock_variant = "final_score_locked_photo_first"
        proof_strip_variant = "player_stat_proof_strip" if is_player_stat else "supporting_stat_proof_strip"
        copy_unlock_state = "verified_stat_copy_locked_manual_review" if is_player_stat else "supporting_stat_copy_locked_manual_review"
        focal_priority = "athlete_primary"
        athlete_focal_contract = "approved_or_review_local_person_image_primary"
        fallback_comparison_status = "fallback_not_used_athlete_preview_ready"
        fallback_comparison_note = "Photo-first athlete/person frame is the primary editorial focal point; logo-only fallback should appear only when the handoff loses photo/stat eligibility."
        score_layout_contract = "photo_first_borderless_score_typography_clearance_locked"
        anti_dashboard_contract = "photo_first_borderless_score_text_no_row_panels_no_dashboard_widgets"
        anti_dashboard_review_cue = "Hold or revise if the photo-first score rails become boxed widgets, row containers, solid backing panels, or compete with the athlete focal point."
        lower_third_contract = "photo_first_open_stat_caption_rail_no_boxed_panel"
        lower_third_review_cue = "Hold or revise if the lower stat strip becomes a heavy panel, solid lower-third box, or competes with the athlete/score hierarchy."
        hero_image_mode = "approved_headshot_bridge_action_photo_ready"
        hero_image_source_class = "approved_local_headshot_bridge"
        hero_silhouette_mode = clean(cutout_contract.get("hero_silhouette_mode"))
        hero_cutout_readiness = clean(cutout_contract.get("hero_cutout_readiness"))
        hero_alpha_mode = clean(cutout_contract.get("hero_alpha_mode"))
        grid_breaking_hero_contract = clean(cutout_contract.get("grid_breaking_hero_contract"))
        action_photo_hero_contract = "manual_review_action_photo_can_replace_headshot_when_local_approved"
        action_photo_candidate_status = "pending_manual_action_photo_candidate"
        action_photo_readiness_contract = "headshot_bridge_review_draft_ok_action_photo_candidate_required_for_premium_final_score"
        action_photo_slot_expectation = "replace_headshot_bridge_with_manually_cleared_local_action_photo_candidate"
        action_photo_subject_metadata_required = "entity_id,athlete_name,team,rights_class,identity_confidence,intended_review_only_use,source_attribution"
        action_photo_crop_metadata_required = "subject_bbox_or_focus_zone,action_context,limb_clearance,face_visibility,score_text_clearance,safe_crop_notes"
        action_photo_operator_review_cue = (
            "Approved local headshot may bridge review drafts only; hold premium final-score editorial until a manually cleared "
            "action-photo candidate proves subject identity, rights class, action context, and crop/text clearance."
        )
        headshot_bridge_status = "approved_local_headshot_review_draft_only_not_premium_final_score"
        composition_balance_contract = "headshot_bridge_not_roster_portrait_action_photo_replacement_lane_reserved"
        action_photo_replacement_composition_cue = (
            "Treat the headshot as a temporary bridge: preserve score/stat tension and a replacement lane for an action-photo crop "
            "without letting the portrait dominate like roster media."
        )
        headshot_bridge_composition_cue = (
            "Hold or revise if the headshot bridge reads as a roster portrait, ID badge, or profile-card hero instead of a temporary review-draft bridge."
        )
        lower_left_right_balance_review_cue = (
            "Check that the athlete/photo side, score spine, and lower rail create diagonal editorial tension; hold if the bottom block feels heavier than the action/photo lane."
        )
        roster_portrait_risk_cue = (
            "Headshot bridge is review-draft-only and must stay visually subordinate to the future action-photo route."
        )
        template_fit_reason = "Verified player/stat context plus approved local athlete photo enables review-only photo-first result routing."
        if layout_mode == "square_photo_first_score_panel":
            visual_mode = "photo_first_performer_square" if is_player_stat else "photo_first_result_square"
            score_lock_variant = "final_score_locked_square_photo_panel"
        elif layout_mode == "photo_first_final_score":
            score_lock_variant = "final_score_locked_photo_first"
    elif missing:
        template_fit_reason = f"Photo-first route blocked; missing {missing}."
    return {
        "visual_mode": visual_mode,
        "hero_asset_required": hero_asset_required,
        "focal_entity_type": focal_entity_type,
        "score_lock_variant": score_lock_variant,
        "proof_strip_variant": proof_strip_variant,
        "copy_unlock_state": copy_unlock_state,
        "focal_priority": focal_priority,
        "athlete_focal_contract": athlete_focal_contract,
        "fallback_comparison_status": fallback_comparison_status,
        "fallback_comparison_note": fallback_comparison_note,
        "score_layout_contract": score_layout_contract,
        "anti_dashboard_contract": anti_dashboard_contract,
        "anti_dashboard_review_cue": anti_dashboard_review_cue,
        "lower_third_contract": lower_third_contract,
        "lower_third_review_cue": lower_third_review_cue,
        "background_family": RENDER_BACKGROUND_FAMILY,
        "hero_image_mode": hero_image_mode,
        "hero_image_source_class": hero_image_source_class,
        "hero_silhouette_mode": hero_silhouette_mode,
        "hero_cutout_readiness": hero_cutout_readiness,
        "hero_alpha_mode": hero_alpha_mode,
        "grid_breaking_hero_contract": grid_breaking_hero_contract,
        "action_photo_hero_contract": action_photo_hero_contract,
        "action_photo_candidate_status": action_photo_candidate_status,
        "action_photo_readiness_contract": action_photo_readiness_contract,
        "action_photo_slot_expectation": action_photo_slot_expectation,
        "action_photo_subject_metadata_required": action_photo_subject_metadata_required,
        "action_photo_crop_metadata_required": action_photo_crop_metadata_required,
        "action_photo_operator_review_cue": action_photo_operator_review_cue,
        "headshot_bridge_status": headshot_bridge_status,
        "composition_balance_contract": composition_balance_contract,
        "action_photo_replacement_composition_cue": action_photo_replacement_composition_cue,
        "headshot_bridge_composition_cue": headshot_bridge_composition_cue,
        "lower_left_right_balance_review_cue": lower_left_right_balance_review_cue,
        "roster_portrait_risk_cue": roster_portrait_risk_cue,
        "template_fit_reason": template_fit_reason,
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
    wash = Image.new("RGBA", image.size, (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash, "RGBA")
    accent = PALETTE["gold"] if tone == "result" else PALETTE["cyan"]
    wash_draw.rounded_rectangle((left + 16, card_top + 22, right + 10, card_bottom + 18), radius=26, fill=(0, 0, 0, 24))
    wash_draw.rounded_rectangle((left, card_top, right, card_bottom), radius=22, fill=(*PALETTE["paper"], 255), outline=(255, 255, 255, 58), width=1)
    image.alpha_composite(wash)
    draw = ImageDraw.Draw(image)
    draw_rounded(draw, (left, card_top + 28, left + 10, card_bottom - 28), 5, accent)

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
    draw.line((text_left, module_top, text_right, module_top), fill=(*accent, 186), width=3)
    draw.line((text_left, module_top + 10, text_left, module_bottom - 6), fill=(*accent, 134), width=2)
    draw.text((text_left + 22, module_top + 24), "Manual render context", font=font(27, True), fill=(24, 28, 36))
    y = module_top + 78
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
        y = draw_text_block(draw, (text_left + 22, y), item, text_font, PALETTE["muted"], text_right - text_left - 44, max_lines, 6)
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


def red_marker_ratio(image: Any, box: Tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = box
    crop = image.convert("RGB").crop((max(0, x1), max(0, y1), min(image.size[0], x2), min(image.size[1], y2)))
    data = crop.tobytes()
    if not data:
        return 0.0
    red_pixels = 0
    total = max(1, len(data) // 3)
    for index in range(0, len(data), 3):
        r, g, b = data[index], data[index + 1], data[index + 2]
        if r >= 120 and g <= 95 and b <= 110:
            red_pixels += 1
    return red_pixels / total


def preview_watermark_boxes(width: int, height: int) -> Dict[str, Tuple[int, int, int, int]]:
    return {
        "top": (max(0, width - 390), 58, width - 38, 158),
        "footer": (40, max(0, height - 78), width - 40, height - 22),
    }


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
        watermark_boxes = preview_watermark_boxes(width, height)
        top_watermark_ratio = red_marker_ratio(image, watermark_boxes["top"])
        footer_watermark_ratio = red_marker_ratio(image, watermark_boxes["footer"])
        watermark_ok = top_watermark_ratio >= 0.003 and footer_watermark_ratio >= 0.120
        ok = bool(alpha_bbox) and width == expected_w and height == expected_h and title_bright_ratio >= 0.018 and luma_stddev >= 8.0 and watermark_ok
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
                "review_watermark_contract": REVIEW_WATERMARK_CONTRACT,
                "review_watermark_status": "watermark_lock_pass" if watermark_ok else "watermark_lock_review_required",
                "top_watermark_red_ratio": round(top_watermark_ratio, 4),
                "footer_watermark_red_ratio": round(footer_watermark_ratio, 4),
                "file_size_bytes": path.stat().st_size if path.exists() else 0,
                "qa_policy": "generated_preview_visibility_only_not_asset_approval_or_publish_readiness",
            }
        )
    except Exception as exc:
        row["status"] = "preview_qa_error"
        row["error"] = clean(exc)
    return row


def visual_comparison_row(format_row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "format_id": clean(format_row.get("format_id")),
        "path": clean(format_row.get("path")),
        "dimensions": f"{clean(format_row.get('width'))}x{clean(format_row.get('height'))}",
        "visual_mode": clean(format_row.get("visual_mode")) or "not_selected",
        "photo_layout": clean(format_row.get("athlete_photo_layout_mode")) or "not_selected",
        "background_style": clean(format_row.get("render_background_style")) or RENDER_BACKGROUND_STYLE,
        "hero_asset_required": clean(format_row.get("hero_asset_required")) or "not_recorded",
        "hero_image_mode": clean(format_row.get("hero_image_mode")) or "not_recorded",
        "hero_image_source_class": clean(format_row.get("hero_image_source_class")) or "not_recorded",
        "action_photo_hero_contract": clean(format_row.get("action_photo_hero_contract")) or "not_recorded",
        "action_photo_candidate_status": clean(format_row.get("action_photo_candidate_status")) or "not_recorded",
        "action_photo_readiness_contract": clean(format_row.get("action_photo_readiness_contract")) or "not_recorded",
        "action_photo_slot_expectation": clean(format_row.get("action_photo_slot_expectation")) or "not_recorded",
        "action_photo_subject_metadata_required": clean(format_row.get("action_photo_subject_metadata_required")) or "not_recorded",
        "action_photo_crop_metadata_required": clean(format_row.get("action_photo_crop_metadata_required")) or "not_recorded",
        "action_photo_operator_review_cue": clean(format_row.get("action_photo_operator_review_cue")) or "not_recorded",
        "headshot_bridge_status": clean(format_row.get("headshot_bridge_status")) or "not_recorded",
        "composition_balance_contract": clean(format_row.get("composition_balance_contract")) or "not_recorded",
        "action_photo_replacement_composition_cue": clean(format_row.get("action_photo_replacement_composition_cue")) or "not_recorded",
        "headshot_bridge_composition_cue": clean(format_row.get("headshot_bridge_composition_cue")) or "not_recorded",
        "lower_left_right_balance_review_cue": clean(format_row.get("lower_left_right_balance_review_cue")) or "not_recorded",
        "roster_portrait_risk_cue": clean(format_row.get("roster_portrait_risk_cue")) or "not_recorded",
        "focal_entity_type": clean(format_row.get("focal_entity_type")) or "not_recorded",
        "focal_priority": clean(format_row.get("focal_priority")) or "not_recorded",
        "athlete_focal_contract": clean(format_row.get("athlete_focal_contract")) or "not_recorded",
        "fallback_comparison_status": clean(format_row.get("fallback_comparison_status")) or "not_recorded",
        "score_layout_contract": clean(format_row.get("score_layout_contract")) or "not_recorded",
        "anti_dashboard_contract": clean(format_row.get("anti_dashboard_contract")) or "not_recorded",
        "anti_dashboard_review_cue": clean(format_row.get("anti_dashboard_review_cue")) or "not_recorded",
        "lower_third_contract": clean(format_row.get("lower_third_contract")) or "not_recorded",
        "lower_third_review_cue": clean(format_row.get("lower_third_review_cue")) or "not_recorded",
        "automated_qa_status": clean(format_row.get("preview_qa_status")) or "preview_qa_not_run",
        "reference_public_mockup_path": clean(format_row.get("reference_public_mockup_path")) or "not_reference_packed",
        "reference_layout_path": clean(format_row.get("reference_layout_path")) or "not_reference_packed",
        "reference_derivation": clean(format_row.get("reference_derivation")) or "not_reference_packed",
        "review_only": True,
        "publish_ready": False,
    }


def visual_comparison_next_step(content_module: Dict[str, Any]) -> str:
    if clean(content_module.get("visual_mode")).startswith("photo_first"):
        return (
            "Open the contact sheet first, compare athlete focal point, score hierarchy, stat strip, and square crop against "
            "the reference mockup/layout paths, verify the score rail does not read like a dashboard widget, confirm the headshot bridge is review-draft-only, "
            "then record approve/hold/revise in the manual visual QA intake."
        )
    return (
        "Open the contact sheet first, confirm the no-photo fallback is intentional, compare score hierarchy and reference "
        "paths, then hold if an athlete-led action-photo candidate should be required for premium final-score editorial or if the score treatment reads like a dashboard card."
    )


def write_visual_comparison_contact_sheet(rows: List[Dict[str, Any]], content_module: Dict[str, Any], contact_path: Path) -> Dict[str, Any]:
    result = {
        "status": "visual_comparison_contact_sheet_not_created",
        "path": contact_path.as_posix(),
        "review_only": True,
        "publish_ready": False,
    }
    if Image is None or ImageDraw is None:
        result["status"] = "visual_comparison_contact_sheet_unavailable_pillow_missing"
        return result

    contact_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 2400, 1600
    canvas = Image.new("RGBA", (width, height), (8, 13, 24, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, height), fill=(7, 12, 22, 255))
    draw.rectangle((0, 0, width, 170), fill=(12, 26, 44, 255))
    draw.rectangle((0, height - 86, width, height), fill=(145, 24, 38, 255))
    draw.text((70, 48), "HSD RENDERER VISUAL COMPARISON", font=font(44, True), fill=PALETTE["ink"])
    draw_right_text(draw, width - 70, 54, "REVIEW-ONLY QA BOARD", font(30, True), PALETTE["gold"])
    subtitle = (
        f"Mode: {clean(content_module.get('visual_mode')) or 'not_selected'} | "
        f"Hero: {clean(content_module.get('hero_asset_required')) or 'not_recorded'} | "
        f"Background: {RENDER_BACKGROUND_STYLE}"
    )
    draw_text_block(draw, (70, 112), subtitle, font(24, False), (204, 216, 232), width - 140, 2, 4)
    contract_line = (
        f"Focal contract: {clean(content_module.get('focal_priority')) or 'not_recorded'} | "
        f"{clean(content_module.get('athlete_focal_contract')) or 'not_recorded'} | "
        f"Fallback: {clean(content_module.get('fallback_comparison_status')) or 'not_recorded'}"
    )
    draw_text_block(draw, (70, 142), contract_line, font(19, False), (236, 242, 250), width - 140, 1, 4)

    panel_w = 720
    panel_gap = 50
    x0 = 70
    panel_top = 210
    thumb_top = 315
    thumb_max_w = 610
    thumb_max_h = 760
    meta_top = 1120
    for index, row in enumerate(rows[:3]):
        x = x0 + index * (panel_w + panel_gap)
        draw_rounded(draw, (x, panel_top, x + panel_w, height - 130), 18, (18, 31, 51), outline=(72, 103, 142), width=2)
        draw.text((x + 28, panel_top + 24), clean(row.get("format_id")).upper(), font=font(31, True), fill=PALETTE["ink"])
        draw_right_text(draw, x + panel_w - 28, panel_top + 27, clean(row.get("dimensions")), font(22, True), PALETTE["gold"])

        preview_path = Path(clean(row.get("path")))
        thumb_status = "preview missing"
        try:
            preview = Image.open(preview_path).convert("RGBA")
            preview.thumbnail((thumb_max_w, thumb_max_h), resample_filter())
            paste_x = x + (panel_w - preview.width) // 2
            paste_y = thumb_top + (thumb_max_h - preview.height) // 2
            draw.rectangle((paste_x - 4, paste_y - 4, paste_x + preview.width + 4, paste_y + preview.height + 4), fill=(236, 242, 250))
            canvas.alpha_composite(preview, (paste_x, paste_y))
            thumb_status = "preview loaded"
        except Exception:
            draw_rounded(draw, (x + 52, thumb_top, x + panel_w - 52, thumb_top + thumb_max_h), 12, (33, 42, 58), outline=(150, 72, 82), width=2)
            draw_text_block(draw, (x + 80, thumb_top + 330), "Preview image missing or unreadable", font(30, True), PALETTE["ink"], panel_w - 160, 3, 8)

        y = meta_top
        meta_lines = [
            f"QA: {clean(row.get('automated_qa_status'))}",
            f"Visual: {clean(row.get('visual_mode'))}",
            f"Photo/layout: {clean(row.get('photo_layout'))}",
            f"Hero: {clean(row.get('hero_asset_required'))}",
            f"Hero mode: {clean(row.get('hero_image_mode'))}",
            f"Focal: {clean(row.get('focal_priority'))}",
            f"Fallback: {clean(row.get('fallback_comparison_status'))}",
            f"Reference: {clean(row.get('reference_derivation'))}",
            f"Image: {thumb_status}",
        ]
        for line in meta_lines:
            y = draw_text_block(draw, (x + 30, y), line, font(21, False), (222, 229, 240), panel_w - 60, 2, 5)
            y += 2
    footer = "Review-only artifact. This board does not approve, publish, move files, or create a publish-ready lane."
    draw_text_block(draw, (70, height - 60), footer, font(28, True), PALETTE["ink"], width - 140, 2, 4)
    canvas.convert("RGB").save(contact_path)
    result["status"] = "visual_comparison_contact_sheet_ready"
    return result


def write_visual_comparison_board(
    render_result: Dict[str, Any],
    source_manifest: Dict[str, Any],
    generated_at_utc: str,
    freshness: Dict[str, str],
) -> Dict[str, Any]:
    formats = render_result.get("format_options") if isinstance(render_result.get("format_options"), list) else []
    content_module = render_result.get("content_module") if isinstance(render_result.get("content_module"), dict) else {}
    rows = [visual_comparison_row(row) for row in formats]
    primary_row = next((row for row in rows if clean(row.get("format_id")) == "ig_feed_4x5"), rows[0] if rows else {})

    def contract_value(key: str, default: str = "not_recorded") -> str:
        return clean(content_module.get(key)) or clean(primary_row.get(key)) or default

    contact_path = OUT_REVIEW_DRAFTS / "draft_preview_visual_contact_sheet.png"
    contact_sheet = write_visual_comparison_contact_sheet(rows, content_module, contact_path)
    next_step = visual_comparison_next_step(content_module)
    board = {
        "status": "review_only_visual_comparison_ready" if rows else "review_only_visual_comparison_no_formats",
        "path": OUT_VISUAL_COMPARISON_BOARD.as_posix(),
        "contact_sheet_path": contact_path.as_posix(),
        "contact_sheet_status": clean(contact_sheet.get("status")),
        "review_only": True,
        "publish_ready": False,
        "approval_status": "not_approved_human_review_required",
        "format_count": len(rows),
        "preview_freshness_status": clean(freshness.get("preview_freshness_status")),
        "renderer_generated_at_utc": generated_at_utc,
        "source_handoff_generated_at_utc": clean(source_manifest.get("generated_at_utc")),
        "visual_mode": contract_value("visual_mode", "not_selected"),
        "background_style": clean(render_result.get("render_background_style")) or RENDER_BACKGROUND_STYLE,
        "hero_asset_required": contract_value("hero_asset_required"),
        "hero_image_mode": contract_value("hero_image_mode"),
        "hero_image_source_class": contract_value("hero_image_source_class"),
        "action_photo_hero_contract": contract_value("action_photo_hero_contract"),
        "action_photo_candidate_status": contract_value("action_photo_candidate_status"),
        "action_photo_readiness_contract": contract_value("action_photo_readiness_contract"),
        "action_photo_slot_expectation": contract_value("action_photo_slot_expectation"),
        "action_photo_subject_metadata_required": contract_value("action_photo_subject_metadata_required"),
        "action_photo_crop_metadata_required": contract_value("action_photo_crop_metadata_required"),
        "action_photo_operator_review_cue": contract_value("action_photo_operator_review_cue"),
        "headshot_bridge_status": contract_value("headshot_bridge_status"),
        "composition_balance_contract": contract_value("composition_balance_contract"),
        "action_photo_replacement_composition_cue": contract_value("action_photo_replacement_composition_cue"),
        "headshot_bridge_composition_cue": contract_value("headshot_bridge_composition_cue"),
        "lower_left_right_balance_review_cue": contract_value("lower_left_right_balance_review_cue"),
        "roster_portrait_risk_cue": contract_value("roster_portrait_risk_cue"),
        "focal_entity_type": contract_value("focal_entity_type"),
        "focal_priority": contract_value("focal_priority"),
        "athlete_focal_contract": contract_value("athlete_focal_contract"),
        "fallback_comparison_status": contract_value("fallback_comparison_status"),
        "fallback_comparison_note": contract_value("fallback_comparison_note"),
        "score_layout_contract": contract_value("score_layout_contract"),
        "anti_dashboard_contract": contract_value("anti_dashboard_contract"),
        "anti_dashboard_review_cue": contract_value("anti_dashboard_review_cue"),
        "lower_third_contract": contract_value("lower_third_contract"),
        "lower_third_review_cue": contract_value("lower_third_review_cue"),
        "next_manual_review_step": next_step,
        "rows": rows,
    }
    lines = [
        "# HSD Renderer Visual Comparison Board",
        "",
        f"Version: `{VERSION}`",
        f"Status: `{board['status']}`",
        f"Generated: `{generated_at_utc}`",
        "",
        "## Guardrails",
        "",
        "- Review-only visual comparison artifact.",
        "- Does not approve previews.",
        "- Does not publish or mark anything publish-ready.",
        "- Does not move files into a publish-ready lane.",
        "- Does not download assets or call paid APIs.",
        "",
        "## Look First",
        "",
        f"- Contact sheet: `{board['contact_sheet_path']}`",
        f"- Contact sheet status: `{board['contact_sheet_status']}`",
        f"- Preview freshness: `{board['preview_freshness_status']}`",
        f"- Source handoff generated: `{board['source_handoff_generated_at_utc'] or 'not_recorded'}`",
        f"- Renderer generated: `{generated_at_utc}`",
        f"- Visual mode: `{board['visual_mode']}`",
        f"- Background style: `{board['background_style']}`",
        f"- Hero asset status: `{board['hero_asset_required']}`",
        f"- Hero image mode: `{board['hero_image_mode']}`",
        f"- Action-photo hero contract: `{board['action_photo_hero_contract']}`",
        f"- Action-photo candidate status: `{board['action_photo_candidate_status']}`",
        f"- Action-photo readiness contract: `{board['action_photo_readiness_contract']}`",
        f"- Action-photo slot expectation: `{board['action_photo_slot_expectation']}`",
        f"- Action-photo subject metadata required: `{board['action_photo_subject_metadata_required']}`",
        f"- Action-photo crop metadata required: `{board['action_photo_crop_metadata_required']}`",
        f"- Action-photo review cue: {board['action_photo_operator_review_cue']}",
        f"- Headshot bridge status: `{board['headshot_bridge_status']}`",
        f"- Composition balance contract: `{board['composition_balance_contract']}`",
        f"- Action-photo replacement composition cue: {board['action_photo_replacement_composition_cue']}",
        f"- Headshot bridge composition cue: {board['headshot_bridge_composition_cue']}",
        f"- Lower-left/right balance cue: {board['lower_left_right_balance_review_cue']}",
        f"- Roster portrait risk cue: {board['roster_portrait_risk_cue']}",
        f"- Focal entity: `{board['focal_entity_type']}`",
        f"- Focal priority: `{board['focal_priority']}`",
        f"- Athlete focal contract: `{board['athlete_focal_contract']}`",
        f"- Fallback comparison: `{board['fallback_comparison_status']}`",
        f"- Fallback note: {board['fallback_comparison_note']}",
        f"- Score layout contract: `{board['score_layout_contract']}`",
        f"- Anti-dashboard contract: `{board['anti_dashboard_contract']}`",
        f"- Anti-dashboard review cue: {board['anti_dashboard_review_cue']}",
        f"- Lower-third contract: `{board['lower_third_contract']}`",
        f"- Lower-third review cue: {board['lower_third_review_cue']}",
        "",
        "## Format Review",
        "",
    ]
    if rows:
        for row in rows:
            lines.extend(
                [
                    f"### {clean(row.get('format_id'))}",
                    "",
                    f"- Preview path: `{clean(row.get('path'))}`",
                    f"- Format label: `{clean(row.get('dimensions'))}`",
                    f"- Automated QA: `{clean(row.get('automated_qa_status'))}`",
                    f"- Visual mode: `{clean(row.get('visual_mode'))}`",
                    f"- Photo layout: `{clean(row.get('photo_layout'))}`",
                    f"- Background style: `{clean(row.get('background_style'))}`",
                    f"- Hero asset status: `{clean(row.get('hero_asset_required'))}`",
                    f"- Hero image mode: `{clean(row.get('hero_image_mode'))}`",
                    f"- Action-photo hero contract: `{clean(row.get('action_photo_hero_contract'))}`",
                    f"- Action-photo readiness contract: `{clean(row.get('action_photo_readiness_contract'))}`",
                    f"- Action-photo review cue: {clean(row.get('action_photo_operator_review_cue'))}",
                    f"- Headshot bridge status: `{clean(row.get('headshot_bridge_status'))}`",
                    f"- Composition balance contract: `{clean(row.get('composition_balance_contract'))}`",
                    f"- Roster portrait risk cue: {clean(row.get('roster_portrait_risk_cue'))}",
                    f"- Focal priority: `{clean(row.get('focal_priority'))}`",
                    f"- Athlete focal contract: `{clean(row.get('athlete_focal_contract'))}`",
                    f"- Fallback comparison: `{clean(row.get('fallback_comparison_status'))}`",
                    f"- Score layout contract: `{clean(row.get('score_layout_contract'))}`",
                    f"- Anti-dashboard contract: `{clean(row.get('anti_dashboard_contract'))}`",
                    f"- Anti-dashboard review cue: {clean(row.get('anti_dashboard_review_cue'))}",
                    f"- Lower-third contract: `{clean(row.get('lower_third_contract'))}`",
                    f"- Lower-third review cue: {clean(row.get('lower_third_review_cue'))}",
                    f"- Reference mockup: `{clean(row.get('reference_public_mockup_path'))}`",
                    f"- Reference layout: `{clean(row.get('reference_layout_path'))}`",
                    f"- Reference derivation: `{clean(row.get('reference_derivation'))}`",
                    "",
                ]
            )
    else:
        lines.append("- No generated preview formats were available.")
    lines.extend(
        [
            "## Next Manual Review Step",
            "",
            f"- {next_step}",
            "- Keep the decision in manual QA/intake files; this artifact is not approval.",
            "",
        ]
    )
    write_text(OUT_VISUAL_COMPARISON_BOARD, "\n".join(lines))
    return board


def render_preview(packet: Dict[str, Any]) -> Dict[str, Any]:
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    template = choose_template(packet)
    content_module = content_module_summary(packet, template)
    parsed_score = parse_final_score(packet) if clean(template.get("tone")) == "result" else {}
    raw_stat_module = select_verified_stat_module(packet, parsed_score) if parsed_score else {}
    public_canvas_copy = (
        photo_first_public_canvas_copy(parsed_score, raw_stat_module)
        if parsed_score
        and clean(raw_stat_module.get("status")) in {"verified_player_stat_module", "verified_supporting_stat_module"}
        and photo_first_eligible(raw_stat_module)
        else {}
    )
    public_canvas_text = [
        clean(public_canvas_copy.get(key))
        for key in ["kicker", "result_line", "athlete_line", "stat_line", "review_marker"]
        if clean(public_canvas_copy.get(key))
    ]
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
        layout_contract = athlete_photo_layout_for_format(content_module, spec)
        row.update(layout_contract)
        row.update(visual_mode_contract(content_module, layout_contract))
        row["render_background_style"] = RENDER_BACKGROUND_STYLE
        row["background_family"] = clean(row.get("background_family")) or RENDER_BACKGROUND_FAMILY
        row["render_background_cues"] = RENDER_BACKGROUND_CUES
        row["preview_qa_status"] = clean(qa_row.get("status"))
        row["preview_qa_title_bright_ratio"] = qa_row.get("title_bright_ratio", "")
        row["preview_qa_luma_stddev"] = qa_row.get("luma_stddev", "")
        row["review_watermark_contract"] = REVIEW_WATERMARK_CONTRACT
        row["review_watermark_status"] = clean(qa_row.get("review_watermark_status"))
        row["top_watermark_red_ratio"] = qa_row.get("top_watermark_red_ratio", "")
        row["footer_watermark_red_ratio"] = qa_row.get("footer_watermark_red_ratio", "")
        if clean(row.get("athlete_photo_layout_mode")) in {"photo_first_final_score", "square_photo_first_score_panel"}:
            geometry = photo_first_layout_geometry(spec)
            row["photo_first_template_geometry"] = geometry
            row["photo_first_type_levels_active"] = ",".join(PHOTO_FIRST_FINAL_SCORE_ACTIVE_TYPE_LEVELS)
            row["photo_first_type_scale_contract"] = "final-score public canvas uses named label/headline/score/support levels; small support text uses no heavy outline."
            row["photo_first_athlete_visual_max_share"] = geometry.get("athlete_visual_max_share")
            row["photo_first_athlete_visual_share"] = geometry.get("athlete_visual_share")
            row["photo_first_athlete_visual_status"] = geometry.get("athlete_visual_status")
            row["photo_first_safe_zone_status"] = geometry.get("safe_zone_status")
            row["photo_first_safe_zone_px"] = geometry.get("safe_zone_px")
            row["photo_first_safe_zone_policy"] = geometry.get("safe_zone_policy")
            row["photo_first_depth_layer_contract"] = geometry.get("depth_layer_contract")
            row["photo_first_depth_layer_order"] = geometry.get("depth_layer_order")
            row["photo_first_procedural_texture_contract"] = geometry.get("procedural_texture_contract")
            row["photo_first_team_color_weighting"] = geometry.get("team_color_weighting")
            row["photo_first_score_asymmetry_contract"] = geometry.get("score_asymmetry_contract")
            row["photo_first_team_identifier_treatment"] = "borderless_editorial_logo_identifier"
            row["photo_first_lower_third_treatment"] = "integrated_score_shelf_caption_strip_no_rounded_panel"
            row["photo_first_review_marker_treatment"] = "single_quiet_pinned_review_badge"
            row["photo_first_art_direction"] = (
                "premium_hsd_sports_editorial_photo_stage_with_team_accent_rim_light,"
                "blueprint_depth_layers,procedural_court_grain,asymmetric_score_treatment,"
                "borderless_team_identifiers,caption_lower_third,soft_athlete_stage,"
                "editorial_depth_bridge,integrated_lower_stat_band,quiet_badge_pin,"
                "and_review_only_guardrails"
            )
            row["public_render_canvas_text"] = public_canvas_text
            row["public_render_review_marker_count"] = 1
            row["public_render_banned_canvas_phrases"] = PUBLIC_RENDER_BANNED_CANVAS_PHRASES
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
        "public_render_canvas_text": public_canvas_text,
        "public_render_review_marker_count": 1 if public_canvas_text else 0,
        "public_render_banned_canvas_phrases": PUBLIC_RENDER_BANNED_CANVAS_PHRASES,
    }


def report_status_label(status: str) -> str:
    labels = {
        "draft_preview_created": "Review draft created",
        "blocked_missing_handoff": "Review draft blocked: missing handoff",
        "blocked_preview_not_created": "Review draft blocked: preview not created",
    }
    return labels.get(clean(status), clean(status).replace("_", " ").title() or "Not run")


def preview_freshness_detail(source_manifest: Dict[str, Any], generated_at_utc: str, preview_path: str) -> Dict[str, str]:
    source_generated_at = clean(source_manifest.get("generated_at_utc"))
    return {
        "preview_freshness_status": "generated_from_current_handoff_packet",
        "preview_freshness_detail": (
            "Renderer read the handoff manifest and created this review-only preview in the current output scope; "
            "manual review is still required before any later step."
        ),
        "renderer_generated_at_utc": generated_at_utc,
        "source_handoff_generated_at_utc": source_generated_at,
        "preview_decision_cue": "Use this preview only when renderer_generated_at_utc is at or after source_handoff_generated_at_utc; otherwise rerun the renderer.",
        "preview_output_scope": preview_path,
    }


def report_lines(status: str, manifest: Dict[str, Any], preview_path: str, reason: str = "", render_result: Dict[str, Any] | None = None) -> List[str]:
    packet = manifest.get("packet") if isinstance(manifest.get("packet"), dict) else {}
    render_result = render_result or {}
    template = render_result.get("template") if isinstance(render_result.get("template"), dict) else {}
    reference_pack = render_result.get("reference_pack") if isinstance(render_result.get("reference_pack"), dict) else {}
    formats = render_result.get("format_options") if isinstance(render_result.get("format_options"), list) else []
    primary_format = next(
        (
            row for row in formats
            if isinstance(row, dict) and (row.get("primary") is True or clean(row.get("format_id")) == "ig_feed_4x5")
        ),
        formats[0] if formats and isinstance(formats[0], dict) else {},
    )
    preview_qa = render_result.get("generated_preview_qa") if isinstance(render_result.get("generated_preview_qa"), list) else []
    slots = render_result.get("asset_slots") if isinstance(render_result.get("asset_slots"), list) else []
    content_module = render_result.get("content_module") if isinstance(render_result.get("content_module"), dict) else {}
    team_profiles = render_result.get("team_visual_profiles") if isinstance(render_result.get("team_visual_profiles"), list) else []
    visual_comparison = render_result.get("visual_comparison_board") if isinstance(render_result.get("visual_comparison_board"), dict) else {}
    public_canvas_text = render_result.get("public_render_canvas_text") if isinstance(render_result.get("public_render_canvas_text"), list) else []

    def module_value(key: str, default: str = "n/a") -> str:
        return clean(content_module.get(key)) or clean(primary_format.get(key)) or default

    lines = [
        "# HSD Manual Review Renderer",
        "",
        f"Version: `{VERSION}`",
        f"Renderer state: {report_status_label(status)}",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Guardrails",
        "",
        "- Manual-only mode.",
        "- Review draft is for human review only.",
        "- Does not publish.",
        "- Does not approve the image.",
        "- Does not call paid APIs.",
        "- Does not move files into a publish-ready lane.",
        "",
        "## Output",
        "",
        f"- Preview source packet: `{clean(packet.get('title')) or 'none'}`",
        "- Preview freshness: generated from the current handoff packet.",
        f"- Preview: `{preview_path or 'not_created'}`",
        f"- Visual comparison board: `{clean(visual_comparison.get('path')) or 'not_created'}`",
        f"- Visual contact sheet: `{clean(visual_comparison.get('contact_sheet_path')) or 'not_created'}`",
        f"- Source handoff generated: `{clean(manifest.get('generated_at_utc')) or 'not_recorded'}`",
        f"- Story: `{clean(packet.get('title')) or 'none'}`",
        f"- Template: `{clean(template.get('template_id')) or 'not_selected'}`",
        f"- Template family: `{clean(template.get('template_family')) or 'not_selected'}`",
        f"- Reference pack: `{clean(reference_pack.get('pack_id')) or 'not_used'}`",
        f"- Content module: `{clean(content_module.get('content_module_mode')) or 'not_selected'}` / `{clean(content_module.get('content_module_status')) or 'not_run'}`",
        f"- Visual mode: `{module_value('visual_mode', 'not_selected')}` focal_entity=`{module_value('focal_entity_type')}` hero_asset_required=`{module_value('hero_asset_required')}`",
        f"- Visual contract: score_lock=`{module_value('score_lock_variant')}` proof_strip=`{module_value('proof_strip_variant')}` copy_unlock=`{module_value('copy_unlock_state')}` background=`{module_value('background_family', clean(render_result.get('render_background_style')) or 'n/a')}`",
        f"- Hero image contract: mode=`{module_value('hero_image_mode')}` source=`{module_value('hero_image_source_class')}` action_photo=`{module_value('action_photo_hero_contract')}` status=`{module_value('action_photo_candidate_status')}`",
        f"- Action-photo readiness: contract=`{module_value('action_photo_readiness_contract')}` slot=`{module_value('action_photo_slot_expectation')}` headshot_bridge=`{module_value('headshot_bridge_status')}`",
        f"- Action-photo metadata: subject=`{module_value('action_photo_subject_metadata_required')}` crop=`{module_value('action_photo_crop_metadata_required')}`",
        f"- Action-photo review cue: {module_value('action_photo_operator_review_cue')}",
        f"- Composition balance contract: `{module_value('composition_balance_contract')}`",
        f"- Action-photo replacement composition cue: {module_value('action_photo_replacement_composition_cue')}",
        f"- Headshot bridge composition cue: {module_value('headshot_bridge_composition_cue')}",
        f"- Lower-left/right balance cue: {module_value('lower_left_right_balance_review_cue')}",
        f"- Roster portrait risk cue: {module_value('roster_portrait_risk_cue')}",
        f"- Athlete focal contract: priority=`{module_value('focal_priority')}` contract=`{module_value('athlete_focal_contract')}` fallback=`{module_value('fallback_comparison_status')}`",
        f"- Fallback comparison note: {module_value('fallback_comparison_note')}",
        f"- Score layout contract: `{module_value('score_layout_contract')}`",
        f"- Anti-dashboard contract: `{module_value('anti_dashboard_contract')}`",
        f"- Anti-dashboard review cue: {module_value('anti_dashboard_review_cue')}",
        f"- Lower-third contract: `{module_value('lower_third_contract')}`",
        f"- Lower-third review cue: {module_value('lower_third_review_cue')}",
        f"- Hero silhouette contract: mode=`{module_value('hero_silhouette_mode')}` cutout=`{module_value('hero_cutout_readiness')}` grid=`{module_value('grid_breaking_hero_contract')}`",
        f"- Blueprint style contract: background=`{RENDER_BACKGROUND_STYLE}` cues=`photo_first_blueprint_depth_layers, photo_first_procedural_court_grain, photo_first_asymmetric_score_treatment, photo_first_safe_zone_enforced`",
        f"- Template fit reason: {clean(content_module.get('template_fit_reason')) or 'n/a'}",
        f"- Game shape: `{clean(content_module.get('content_module_game_shape')) or clean(content_module.get('editorial_microcopy_game_shape')) or 'not_selected'}` / {clean(content_module.get('content_module_game_shape_label')) or clean(content_module.get('editorial_microcopy_game_shape_label')) or 'n/a'}",
        f"- Athlete-led render: `{clean(content_module.get('athlete_led_render_status')) or 'not_evaluated'}` missing=`{clean(content_module.get('athlete_led_missing_fields')) or 'none'}`",
        f"- Athlete proof bridge: used=`{clean(content_module.get('proof_artifact_bridge_used')) or 'false'}` source=`{clean(content_module.get('proof_source')) or 'handoff'}` proof_id=`{clean(content_module.get('proof_id')) or 'n/a'}`",
        f"- Athlete photo: `{clean(content_module.get('athlete_photo_status')) or 'not_applicable'}` / {clean(content_module.get('athlete_photo_approval_cue')) or 'n/a'}",
        f"- Athlete identity: `{clean(content_module.get('athlete_photo_identity_review_status')) or 'not_applicable'}` / resolution=`{clean(content_module.get('athlete_photo_identity_resolution_status')) or 'not_recorded'}`",
        f"- Stat source confidence: `{clean(content_module.get('stat_source_confidence')) or 'not_applicable'}`",
        f"- Stat review cue: {clean(content_module.get('stat_review_cue')) or 'n/a'}",
        f"- Editorial microcopy: `{clean(content_module.get('editorial_microcopy_variant')) or 'not_selected'}` / {clean(content_module.get('editorial_microcopy_headline')) or 'n/a'}",
        f"- Editorial review cue: {clean(content_module.get('editorial_microcopy_review_cue')) or 'n/a'}",
        f"- Public canvas text: `{'; '.join(clean(item) for item in public_canvas_text) or 'not_available'}`",
        f"- Public canvas review marker count: `{clean(render_result.get('public_render_review_marker_count')) or '0'}`",
        "- Preview decision cue: use only if the renderer manifest time is at or after the source handoff time; otherwise rerun the renderer.",
        f"- Next visual review step: {clean(visual_comparison.get('next_manual_review_step')) or 'Open the generated previews and record the manual visual QA decision.'}",
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
            visual_mode = clean(item.get("visual_mode")) or "n/a"
            lines.append(
                f"- `{item.get('format_id')}` | `{item.get('width')}x{item.get('height')}` | `{item.get('path')}` | reference=`{ref}` | derivation=`{derivation}` | visual_mode=`{visual_mode}` | photo_layout=`{photo_layout}` | publish_ready=`false`"
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

    generated_at_utc = datetime.now(timezone.utc).isoformat()
    freshness = preview_freshness_detail(source_manifest, generated_at_utc, preview)
    if status == "draft_preview_created":
        render_result["visual_comparison_board"] = write_visual_comparison_board(
            render_result,
            source_manifest,
            generated_at_utc,
            freshness,
        )
    manifest = {
        "version": VERSION,
        "generated_at_utc": generated_at_utc,
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
        "visual_comparison_board": render_result.get("visual_comparison_board", {}),
        "render_background_style": clean(render_result.get("render_background_style")) or RENDER_BACKGROUND_STYLE,
        "render_background_cues": clean(render_result.get("render_background_cues")) or RENDER_BACKGROUND_CUES,
        "public_render_canvas_text": render_result.get("public_render_canvas_text", []),
        "public_render_review_marker_count": render_result.get("public_render_review_marker_count", 0),
        "public_render_banned_canvas_phrases": render_result.get("public_render_banned_canvas_phrases", PUBLIC_RENDER_BANNED_CANVAS_PHRASES),
        "preview_source_title": clean(packet.get("title")),
        **freshness,
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
