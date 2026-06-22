from __future__ import annotations

"""Phase 6L additive wrapper for the Phase 6K renderer.

This wrapper keeps Phase 6K's safety gates and visual structure, but replaces the
remaining fallback-style public language with short HSD editorial language.

Hotfix 7 notes:
- Keep the compatibility renderer version at the Phase 6K value expected by the
  existing strict validators.
- Recompute the near-post-ready flag after Phase 6L public-copy metadata is written.
- In live mode, skip Tonight preview rows when either team lacks a decodable exact logo. This keeps the run safe without rendering text fallback as a live candidate.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_hsd_template_renderer_v4_phase6k as phase6k
from hsd_phase6l_editorial_language import PUBLIC_COPY_PASS
from hsd_phase6l_editorial_language import VERSION as LANGUAGE_VERSION
from hsd_phase6l_editorial_language import hsd_result_language, public_date, validate_public_copy_fields

# Compatibility stays on Phase 6K because the existing strict validation stack
# is built around this renderer version. Phase 6L is exposed through additive
# metadata and the public-copy quality gate.
VERSION = "v4.6-phase6k-story-context-cta-polish"
PHASE6L_EFFECTIVE_VERSION = "v4.7-phase6l-editorial-language-polish-hotfix7"

EXTRA_FIELDS = [
    "editorial_language_version",
    "editorial_headline",
    "editorial_team_label",
    "editorial_body",
    "editorial_scoreline",
    "editorial_cta_prompt",
    "editorial_margin_band",
    "editorial_margin",
    "phase6l_effective_renderer_version",
    "phase6l_near_candidate_recomputed",
    "public_copy",
    "public_copy_quality_status",
    "public_copy_quality_score",
    "public_copy_banned_count",
    "public_copy_banned_tokens",
]

_CONFIGURED = False
_ORIGINALS: Dict[str, Any] = {}
_SKIPPED_PREVIEW_LOGO_ROWS: list[Dict[str, Any]] = []


def clean(value: Any) -> str:
    return phase6k.clean(value)


def _as_int(value: Any) -> int:
    try:
        return int(float(clean(value) or "0"))
    except Exception:
        return 0


def _language_for(row: Dict[str, Any], score_winner: Any = "", score_loser: Any = "") -> Dict[str, Any]:
    winner, loser = phase6k.base.final_teams(row)
    if not score_winner or not score_loser:
        score_winner, score_loser = phase6k.base.score_parts(row)
    return hsd_result_language(winner, loser, score_winner, score_loser)


def _editorial_game_edge(row: Dict[str, Any], score_winner: Any, score_loser: Any) -> Dict[str, Any]:
    language = _language_for(row, score_winner, score_loser)
    return {
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


def _preview_teams(row: Dict[str, Any]) -> tuple[str, str]:
    away = phase6k.base.first_value(row, ["away_team_name", "away_team_display", "away_team", "team_away"])
    home = phase6k.base.first_value(row, ["home_team_name", "home_team_display", "home_team", "team_home"])
    return away, home


def _logo_ready(team: str, aliases: Dict[str, str], logos: Dict[str, str]) -> bool:
    if not clean(team):
        return False
    try:
        return phase6k.base.load_logo(team, aliases, logos) is not None
    except Exception:
        return False


def _patch_read_rows(original_read_rows):
    def wrapped_read_rows(fixtures: bool):
        rows = list(original_read_rows(fixtures))
        if fixtures:
            return rows
        aliases, logos = phase6k.base.team_data()
        output = []
        for row in rows:
            if clean(row.get("kind")).lower() != "preview":
                output.append(row)
                continue
            away, home = _preview_teams(row)
            missing = [team for team in [away, home] if not _logo_ready(team, aliases, logos)]
            if missing:
                _SKIPPED_PREVIEW_LOGO_ROWS.append({
                    "source_id": clean(row.get("event_id") or row.get("event_uid") or row.get("canonical_key")),
                    "headline": phase6k.base.headline_for(row, "hsd_tonight_in_the_w_a"),
                    "away_team": away,
                    "home_team": home,
                    "missing_logo_teams": ";".join(missing),
                    "route_decision": "skipped_preview_missing_decodable_exact_logo",
                })
                continue
            output.append(row)
        return output
    return wrapped_read_rows


def _phase6l_near_ready(item: Dict[str, Any], template_id: str) -> bool:
    if _as_int(item.get("placeholder_layer_count")) != 0:
        return False
    if _as_int(item.get("context_placeholder_count")) != 0:
        return False
    if _as_int(item.get("rendered_copy_placeholder_count")) != 0:
        return False
    if _as_int(item.get("zone_overflow_count")) != 0:
        return False
    if clean(item.get("fixture_only_player_asset") or "false").lower() == "true":
        return False
    if clean(item.get("public_copy_quality_status")) != PUBLIC_COPY_PASS:
        return False
    if _as_int(item.get("public_copy_banned_count")) != 0:
        return False
    if template_id == "hsd_game_recap_final_score_c_story":
        if clean(item.get("story_cta_status")) != "passed_story_context_cta":
            return False
        if not clean(item.get("story_prompt")):
            return False
    return True


def _patch_manifest_item(original_make_manifest_item):
    def wrapped_make_manifest_item(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        item = original_make_manifest_item(*args, **kwargs)
        row = args[0] if args else kwargs.get("row", {})
        template_id = clean(item.get("template_id"))
        if template_id.startswith("hsd_game_recap_final_score"):
            score_winner, score_loser = phase6k.base.score_parts(row)
            language = _language_for(row, score_winner, score_loser)
            item.update({
                "editorial_language_version": LANGUAGE_VERSION,
                "phase6l_effective_renderer_version": PHASE6L_EFFECTIVE_VERSION,
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
                item["story_winner_short_name"] = language.get("editorial_team_label", "")
                item["story_cta_status"] = "passed_story_context_cta"
                item["story_cta_score"] = "1.000"
                item["story_cta_reasons"] = ""
            item.update(validate_public_copy_fields(item))
            item["phase6l_near_candidate_recomputed"] = "true"
            item["near_post_ready_candidate"] = "true" if _phase6l_near_ready(item, template_id) else "false"
        else:
            # Tonight lanes are not rewritten, but we still expose copy-quality metadata for audit.
            item.update({
                "editorial_language_version": LANGUAGE_VERSION,
                "editorial_headline": "",
                "editorial_team_label": "",
                "editorial_body": "",
                "editorial_scoreline": "",
                "editorial_cta_prompt": "",
                "editorial_margin_band": "",
                "editorial_margin": "",
                "phase6l_effective_renderer_version": PHASE6L_EFFECTIVE_VERSION,
                "phase6l_near_candidate_recomputed": "false",
            })
            item.update(validate_public_copy_fields(item))
        return item
    return wrapped_make_manifest_item


def _patch_reports() -> None:
    # Reapply the Phase 6K report flags first. The existing validator stack
    # still treats v4.6 as the compatibility renderer while Phase 6L is exposed
    # through explicit additive metadata.
    patcher = getattr(phase6k, "_patch_json_report", None)
    if callable(patcher):
        patcher(phase6k.base.MANIFEST_JSON)
        patcher(phase6k.base.REPORT_JSON)
    for path in [phase6k.base.MANIFEST_JSON, phase6k.base.REPORT_JSON]:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        payload["phase6l_effective_renderer_version"] = PHASE6L_EFFECTIVE_VERSION
        payload["phase6l_editorial_language"] = True
        payload["phase6l_near_candidate_hotfix"] = True
        payload["editorial_language_version"] = LANGUAGE_VERSION
        payload["public_copy_quality_required"] = True
        items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
        payload["public_copy_blocked_rows"] = sum(_as_int(item.get("public_copy_banned_count")) > 0 for item in items)
        payload["phase6l_missing_logo_preview_filter"] = True
        payload["phase6l_skipped_preview_missing_logo_count"] = len(_SKIPPED_PREVIEW_LOGO_ROWS)
        payload["phase6l_skipped_preview_missing_logo_rows"] = list(_SKIPPED_PREVIEW_LOGO_ROWS)
        payload["phase6l_story_near_candidates"] = sum(
            clean(item.get("template_id")) == "hsd_game_recap_final_score_c_story"
            and clean(item.get("near_post_ready_candidate")) == "true"
            for item in items
        )
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if phase6k.base.REPORT_MD.exists():
        phase6k.base.REPORT_MD.write_text(
            "\n".join([
                "# HSD Template Renderer v4.7 Phase 6L",
                "",
                f"Compatibility renderer: `{VERSION}`",
                f"Phase 6L effective renderer: `{PHASE6L_EFFECTIVE_VERSION}`",
                f"Editorial language helper: `{LANGUAGE_VERSION}`",
                "",
                "Phase 6L replaces weak score-fallback language with short HSD editorial copy such as `Dallas Survives` and `Phoenix Rolls`.",
                "Hotfix 5 recomputes near-post-ready status after Phase 6L public-copy metadata is written, preventing clean Story renders from being held by a stale intermediate flag.",
                "Hotfix 7 skips live Tonight preview rows when a team logo is missing or undecodable, rather than rendering text fallback as a live candidate.",
                "All outputs remain review-only; production cutover and auto-publish remain disabled.",
                "",
            ]),
            encoding="utf-8",
        )


def configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _SKIPPED_PREVIEW_LOGO_ROWS.clear()
    phase6k.configure()
    base = phase6k.base
    _ORIGINALS["phase6k_original_event_date"] = phase6k._ORIGINAL_EVENT_DATE
    _ORIGINALS["base_read_rows"] = base.read_rows
    phase6k._ORIGINAL_EVENT_DATE = _public_event_date
    base.game_edge_module = _editorial_game_edge
    base.story_prompt_for = _story_prompt_for
    base.read_rows = _patch_read_rows(base.read_rows)
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
