from __future__ import annotations

"""Phase 6L additive wrapper for the Phase 6K renderer.

This wrapper keeps Phase 6K's safety gates and visual structure, but replaces the
remaining fallback-style public language with short HSD editorial language.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_hsd_template_renderer_v4_phase6k as phase6k
from hsd_phase6l_editorial_language import VERSION as LANGUAGE_VERSION
from hsd_phase6l_editorial_language import hsd_result_language, public_date, validate_public_copy_fields

VERSION = "v4.7-phase6l-editorial-language-polish"
EXTRA_FIELDS = [
    "editorial_language_version",
    "editorial_headline",
    "editorial_body",
    "editorial_scoreline",
    "editorial_cta_prompt",
    "editorial_margin_band",
    "editorial_margin",
    "public_copy",
    "public_copy_quality_status",
    "public_copy_quality_score",
    "public_copy_banned_count",
    "public_copy_banned_tokens",
]

_CONFIGURED = False
_ORIGINALS: Dict[str, Any] = {}


def clean(value: Any) -> str:
    return phase6k.clean(value)


def _language_for(row: Dict[str, Any], score_winner: Any = "", score_loser: Any = "") -> Dict[str, Any]:
    winner, loser = phase6k.base.final_teams(row)
    if not score_winner or not score_loser:
        score_winner, score_loser = phase6k.base.score_parts(row)
    return hsd_result_language(winner, loser, score_winner, score_loser)


def _editorial_game_edge(row: Dict[str, Any], score_winner: Any, score_loser: Any) -> Dict[str, Any]:
    language = _language_for(row, score_winner, score_loser)
    return {
        # Replaces the weak GAME EDGE/MARGIN copy path with a public-facing read.
        "title": "FINAL READ",
        "headline": language["editorial_headline"],
        "body": language["editorial_body"],
        # Empty margin prevents +20 MARGIN / FINAL MARGIN visual treatment.
        "margin": "",
    }


def _story_prompt_for(row: Dict[str, Any], score_winner: Any, score_loser: Any) -> str:
    return _language_for(row, score_winner, score_loser)["editorial_cta_prompt"]


def _public_event_date(row: Dict[str, Any]) -> str:
    raw = _ORIGINALS["phase6k_original_event_date"](row)
    return public_date(raw)


def _patch_manifest_item(original_make_manifest_item):
    def wrapped_make_manifest_item(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        item = original_make_manifest_item(*args, **kwargs)
        meta = kwargs.get("meta")
        if meta is None and len(args) >= 8:
            meta = args[7]
        row = args[0] if args else kwargs.get("row", {})
        template_id = clean(item.get("template_id"))
        if template_id.startswith("hsd_game_recap_final_score"):
            score_winner, score_loser = phase6k.base.score_parts(row)
            language = _language_for(row, score_winner, score_loser)
            item.update({
                "editorial_language_version": LANGUAGE_VERSION,
                **language,
            })
            # Make the manifest content-module fields match what the public should read.
            if clean(item.get("content_module_mode")) == "game_edge" or template_id in {
                "hsd_game_recap_final_score_a",
                "hsd_game_recap_final_score_c_story",
            }:
                item["content_module_title"] = "FINAL READ"
                item["content_module_body"] = language["editorial_body"]
                item["content_module_prompt"] = language["editorial_cta_prompt"]
            if template_id == "hsd_game_recap_final_score_c_story":
                item["story_prompt"] = language["editorial_cta_prompt"]
            item.update(validate_public_copy_fields(item))
            item["near_post_ready_candidate"] = "true" if (
                clean(item.get("near_post_ready_candidate")) == "true"
                and int(item.get("public_copy_banned_count") or 0) == 0
            ) else "false"
        else:
            # Tonight lanes are not rewritten, but we still expose copy-quality metadata for audit.
            item.update({
                "editorial_language_version": LANGUAGE_VERSION,
                "editorial_headline": "",
                "editorial_body": "",
                "editorial_scoreline": "",
                "editorial_cta_prompt": "",
                "editorial_margin_band": "",
                "editorial_margin": "",
            })
            item.update(validate_public_copy_fields(item))
        return item
    return wrapped_make_manifest_item


def _patch_reports() -> None:
    for path in [phase6k.base.MANIFEST_JSON, phase6k.base.REPORT_JSON]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        payload["version"] = VERSION
        payload["phase6l_editorial_language"] = True
        payload["editorial_language_version"] = LANGUAGE_VERSION
        payload["public_copy_quality_required"] = True
        items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
        payload["public_copy_blocked_rows"] = sum(int(item.get("public_copy_banned_count") or 0) > 0 for item in items)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if phase6k.base.REPORT_MD.exists():
        phase6k.base.REPORT_MD.write_text(
            "\n".join([
                "# HSD Template Renderer v4.7 Phase 6L",
                "",
                f"Version: `{VERSION}`",
                f"Editorial language helper: `{LANGUAGE_VERSION}`",
                "",
                "Phase 6L replaces weak score-fallback language with short HSD editorial copy such as `Dallas Survives` and `Phoenix Rolls`.",
                "It also blocks public fallback phrases like `closed with a 20-point victory`, `points clear`, and `MARGIN` as an editorial punchline.",
                "All outputs remain review-only; production cutover and auto-publish remain disabled.",
                "",
            ]),
            encoding="utf-8",
        )


def configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    phase6k.configure()
    base = phase6k.base
    _ORIGINALS["phase6k_original_event_date"] = phase6k._ORIGINAL_EVENT_DATE
    phase6k._ORIGINAL_EVENT_DATE = _public_event_date
    base.VERSION = VERSION
    base.game_edge_module = _editorial_game_edge
    base.story_prompt_for = _story_prompt_for
    phase6k.story_prompt_for = _story_prompt_for
    for field in EXTRA_FIELDS:
        if field not in base.MANIFEST_FIELDS:
            base.MANIFEST_FIELDS.append(field)
    base.make_manifest_item = _patch_manifest_item(base.make_manifest_item)
    _CONFIGURED = True


def main(argv: Optional[list[str]] = None) -> int:
    configure()
    exit_code = phase6k.base.main(argv)
    _patch_reports()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
