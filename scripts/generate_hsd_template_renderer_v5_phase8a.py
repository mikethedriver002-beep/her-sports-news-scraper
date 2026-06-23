from __future__ import annotations

"""Phase 8A WNBA renderer wrapper.

This preserves Phase 6M asset assurance and replaces Phase 7 Tonight copy with
fit-safe, sport-mechanic copy from the Phase 8A language engine.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_hsd_template_renderer_v4_phase6m as phase6m
from hsd_phase8a_editorial_engine import VERSION as EDITORIAL_VERSION
from hsd_phase8a_editorial_engine import clean, generate_renderer_editorial

VERSION = "v4.6-phase6k-story-context-cta-polish"
PHASE8A_EFFECTIVE_VERSION = "v5.1-phase8a-editorial-language-fit-assets"

EXTRA_FIELDS = [
    "phase8a_effective_renderer_version", "phase8a_editorial_version", "phase8a_editorial_sport_id", "phase8a_editorial_kind",
    "phase8a_editorial_headline", "phase8a_debate_question", "phase8a_watch_title", "phase8a_watch_body", "phase8a_cta",
    "phase8a_editorial_quality_status", "phase8a_editorial_quality_score", "phase8a_editorial_quality_reasons",
    "phase8a_editorial_banned_count", "phase8a_editorial_banned_tokens", "phase8a_duplicate_clause_count", "phase8a_duplicate_clause_details", "phase8a_editorial_public_copy",
]

_CONFIGURED = False
_ORIGINALS: Dict[str, Any] = {}


def _base() -> Any:
    return phase6m._base()


def _variant_for_row(row: Dict[str, Any], module_mode: str) -> str:
    title = clean(row.get("watch_title")).upper()
    body = clean(row.get("watch_body")).upper()
    if "TEAM SPOTLIGHT" in title or "TEAM IDENTITY" in body or clean(row.get("asset_assurance_fallback")).lower() == "true":
        return "team_spotlight_fallback"
    if clean(module_mode).lower() == "player":
        return "preview"
    return "watch_point"


def _draw_verified_player_editorial(image: Image.Image, meta: Dict[str, Any], editorial: Dict[str, Any]) -> None:
    if int(meta.get("player_assets_used") or 0) < 1:
        return
    base = _base()
    player_name = clean(meta.get("player_names"))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((338, 1082, 970, 1278), radius=12, fill=(1, 2, 5, 235), outline=base.GOLD, width=2)
    base.draw_textured_text(image, (365, 1095, 580, 52), player_name or clean(editorial.get("editorial_headline")), "display", 37, 20, base.GOLD_LIGHT, 1, "left")
    base.draw_textured_text(image, (365, 1155, 580, 96), clean(editorial.get("watch_body")), "body", 26, 16, base.INK, 3, "left", uppercase=False)


def _editorial_underlying_render(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str], players: Dict[str, List[Dict[str, str]]], module_mode: str, fixtures: bool):
    variant = _variant_for_row(row, module_mode)
    editorial = generate_renderer_editorial(row, variant=variant)
    enriched = dict(row)
    enriched.update({"preview_label": "MATCHUP READ", "debate_question": editorial["debate_question"], "watch_title": editorial["watch_title"], "watch_body": editorial["watch_body"]})
    image, meta = _ORIGINALS["underlying_render_tonight"](enriched, aliases, logos, players, module_mode, fixtures)
    _draw_verified_player_editorial(image, meta, editorial)
    meta.update({
        "phase8a_effective_renderer_version": PHASE8A_EFFECTIVE_VERSION,
        "phase8a_editorial_version": EDITORIAL_VERSION,
        "phase8a_editorial_sport_id": editorial["phase8a_editorial_sport_id"],
        "phase8a_editorial_kind": editorial["phase8a_editorial_kind"],
        "phase8a_editorial_headline": editorial["editorial_headline"],
        "phase8a_debate_question": editorial["debate_question"],
        "phase8a_watch_title": editorial["watch_title"],
        "phase8a_watch_body": editorial["watch_body"],
        "phase8a_cta": editorial["cta"],
        "phase8a_editorial_quality_status": editorial["phase8a_editorial_quality_status"],
        "phase8a_editorial_quality_score": editorial["phase8a_editorial_quality_score"],
        "phase8a_editorial_quality_reasons": editorial["phase8a_editorial_quality_reasons"],
        "phase8a_editorial_banned_count": editorial["phase8a_editorial_banned_count"],
        "phase8a_editorial_banned_tokens": editorial["phase8a_editorial_banned_tokens"],
        "phase8a_duplicate_clause_count": editorial["phase8a_duplicate_clause_count"],
        "phase8a_duplicate_clause_details": editorial["phase8a_duplicate_clause_details"],
        "phase8a_editorial_public_copy": editorial["phase8a_editorial_public_copy"],
        # Backward-compatible Phase 7 fields for older validators and review cards.
        "phase7_editorial_quality_status": "passed_phase7_editorial_quality" if editorial["phase8a_editorial_quality_status"] == "passed_phase8a_editorial_quality" else "blocked_phase7_editorial_quality",
        "phase7_editorial_quality_score": editorial["phase8a_editorial_quality_score"],
        "phase7_editorial_quality_reasons": editorial["phase8a_editorial_quality_reasons"],
        "phase7_editorial_banned_count": editorial["phase8a_editorial_banned_count"],
        "phase7_editorial_banned_tokens": editorial["phase8a_editorial_banned_tokens"],
        "phase7_editorial_public_copy": editorial["phase8a_editorial_public_copy"],
    })
    return image, meta


def _manifest_wrapper(original_make_manifest_item):
    def wrapped(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        item = original_make_manifest_item(*args, **kwargs)
        meta = kwargs.get("meta")
        if meta is None and len(args) >= 8:
            meta = args[7]
        meta = dict(meta or {})
        item["phase8a_effective_renderer_version"] = PHASE8A_EFFECTIVE_VERSION
        if clean(item.get("template_id")) != "hsd_tonight_in_the_w_a":
            return item
        for field in EXTRA_FIELDS:
            if field in meta:
                item[field] = meta[field]
        public_copy = clean(meta.get("phase8a_editorial_public_copy"))
        if public_copy:
            item["rendered_copy"] = public_copy
            item["public_copy"] = public_copy
            item["rendered_copy_placeholder_count"] = 0
            item["rendered_copy_placeholder_tokens"] = ""
            item["public_copy_banned_count"] = int(meta.get("phase8a_editorial_banned_count") or 0)
            item["public_copy_banned_tokens"] = clean(meta.get("phase8a_editorial_banned_tokens"))
        if clean(meta.get("phase8a_editorial_quality_status")) != "passed_phase8a_editorial_quality":
            item["near_post_ready_candidate"] = "false"
        item["notes"] = ";".join(value for value in [clean(item.get("notes")), "phase8a_fit_safe_sport_mechanic_copy"] if value)
        return item
    return wrapped


def _patch_reports() -> None:
    base = _base()
    for path in [base.MANIFEST_JSON, base.REPORT_JSON]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
        tonight = [item for item in items if clean(item.get("template_id")) == "hsd_tonight_in_the_w_a"]
        payload.update({
            "phase8a_effective_renderer_version": PHASE8A_EFFECTIVE_VERSION,
            "phase8a_editorial_language_fit_assets": True,
            "phase8a_editorial_version": EDITORIAL_VERSION,
            "phase8a_tonight_rows": len(tonight),
            "phase8a_tonight_editorial_passed_rows": sum(clean(item.get("phase8a_editorial_quality_status")) == "passed_phase8a_editorial_quality" for item in tonight),
            "phase8a_tonight_generic_copy_rows": sum(int(item.get("phase8a_editorial_banned_count") or 0) > 0 for item in tonight),
            "phase8a_tonight_duplicate_clause_rows": sum(int(item.get("phase8a_duplicate_clause_count") or 0) > 0 for item in tonight),
        })
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if base.REPORT_MD.exists():
        base.REPORT_MD.write_text("\n".join([
            "# HSD Template Renderer v5.1 Phase 8A", "", f"Compatibility renderer: `{VERSION}`", f"Phase 8A effective renderer: `{PHASE8A_EFFECTIVE_VERSION}`", f"Editorial engine: `{EDITORIAL_VERSION}`", "",
            "Tonight and spotlight rows now use fit-safe sport-mechanic copy.",
            "Generic labels, duplicate CTA/body phrasing, fallback noun salad, and clipped CTA candidates are blocked.",
            "Phase 6M asset assurance, human visual approval, production cutover blocks, and auto-publish blocks remain active.", "",
        ]), encoding="utf-8")


def configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    phase6m.configure()
    base = _base()
    _ORIGINALS["underlying_render_tonight"] = phase6m._ORIGINALS["render_tonight"]
    phase6m._ORIGINALS["render_tonight"] = _editorial_underlying_render
    for field in EXTRA_FIELDS:
        if field not in base.MANIFEST_FIELDS:
            base.MANIFEST_FIELDS.append(field)
    base.make_manifest_item = _manifest_wrapper(base.make_manifest_item)
    _CONFIGURED = True


def main(argv: Optional[List[str]] = None) -> int:
    configure()
    exit_code = phase6m.main(argv)
    _patch_reports()
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
