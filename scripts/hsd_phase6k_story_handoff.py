from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from PIL import ImageDraw

PATCH_VERSION = "v4.6-phase6k-story-handoff-polish"
CONTEXT_PASS = "passed_final_score_story_context"
CTA_PASS = "passed_final_score_story_cta_hierarchy"

STORY_MANIFEST_FIELDS = [
    "render_patch_version",
    "story_context_status",
    "story_context_score",
    "story_context_reasons",
    "story_context_mode",
    "story_context_copy",
    "story_cta_status",
    "story_cta_score",
    "story_cta_reasons",
    "story_cta_prompt",
]

UNKNOWN_PATTERNS = (
    r"\bTBA\b",
    r"\bTBD\b",
    r"\bUNKNOWN\b",
    r"\bN/?A\b",
    r"\bNOT AVAILABLE\b",
    r"\bTO BE ANNOUNCED\b",
    r"\bTO BE DETERMINED\b",
)
GENERIC_PROMPTS = {
    "WHAT CHANGED THE GAME?",
    "WHAT STOOD OUT?",
    "WHO MADE THE DIFFERENCE LATE?",
    "WHERE DID THE GAME TURN?",
    "TELL US WHAT YOU SAW.",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def contains_unknown(value: Any) -> bool:
    text = clean(value).upper()
    return bool(text and any(re.search(pattern, text) for pattern in UNKNOWN_PATTERNS))


def safe_value(value: Any) -> str:
    text = clean(value)
    return "" if contains_unknown(text) else text


def short_team(base: Any, team: str) -> str:
    value = clean(team)
    if not value:
        return ""
    helper = getattr(base, "short_team", None)
    result = clean(helper(value) if callable(helper) else value)
    return result.upper()


def possessive(team: str) -> str:
    value = clean(team)
    if not value:
        return ""
    return f"{value}'" if value.endswith("S") else f"{value}'S"


def build_story_context(row: Dict[str, Any], base: Any) -> Dict[str, Any]:
    date_value = safe_value(base.event_date(row))
    location_value = safe_value(base.event_location(row))
    league_value = safe_value(base.event_league(row)) or "WNBA"

    segments: List[str] = [date_value or "FINAL"]
    if location_value:
        segments.append(location_value)
    segments.append(league_value)

    reasons: List[str] = []
    if any(contains_unknown(value) for value in segments):
        reasons.append("unknown_or_tba_context_copy")
    if not league_value:
        reasons.append("missing_league_context")
    if not segments:
        reasons.append("missing_story_context")

    if date_value and location_value:
        mode = "verified_date_location_league"
    elif date_value:
        mode = "verified_date_league"
    elif location_value:
        mode = "final_location_league"
    else:
        mode = "final_league"

    score = max(0.0, 1.0 - 0.35 * len(set(reasons)))
    return {
        "segments": segments,
        "story_context_status": CONTEXT_PASS if not reasons else "needs_final_score_story_context",
        "story_context_score": f"{score:.3f}",
        "story_context_reasons": ";".join(sorted(set(reasons))),
        "story_context_mode": mode,
        "story_context_copy": " • ".join(segments),
    }


def build_story_prompt(row: Dict[str, Any], score_winner: str, score_loser: str, base: Any) -> Dict[str, Any]:
    winner, loser = base.final_teams(row)
    winner_short = short_team(base, winner)
    loser_short = short_team(base, loser)
    margin = base.score_margin(score_winner, score_loser)

    if winner_short and loser_short:
        if margin is None:
            prompt = f"WHAT STOOD OUT IN {possessive(winner_short)} WIN OVER {loser_short}?"
        elif margin <= 3:
            prompt = f"WHO CLOSED IT FOR {winner_short} AGAINST {loser_short}?"
        elif margin <= 7:
            prompt = f"WHERE DID {winner_short} TURN IT AGAINST {loser_short}?"
        else:
            prompt = f"WHAT DROVE {possessive(winner_short)} {margin}-POINT WIN OVER {loser_short}?"
    elif winner_short:
        prompt = f"WHAT STOOD OUT IN {possessive(winner_short)} WIN?"
    else:
        prompt = "WHAT DECIDED THE FINISH?"

    reasons: List[str] = []
    upper = clean(prompt).upper()
    if not upper:
        reasons.append("missing_story_cta_prompt")
    if upper in GENERIC_PROMPTS:
        reasons.append("generic_story_cta_prompt")
    if winner_short and winner_short not in upper:
        reasons.append("story_cta_missing_winner")
    if loser_short and loser_short not in upper:
        reasons.append("story_cta_missing_loser")
    if contains_unknown(upper):
        reasons.append("story_cta_contains_unknown_copy")

    score = max(0.0, 1.0 - 0.25 * len(set(reasons)))
    return {
        "prompt": prompt,
        "story_cta_status": CTA_PASS if not reasons else "needs_final_score_story_cta_hierarchy",
        "story_cta_score": f"{score:.3f}",
        "story_cta_reasons": ";".join(sorted(set(reasons))),
        "story_cta_prompt": prompt,
    }


def _opaque_panel(image: Any, box: Tuple[int, int, int, int], base: Any) -> None:
    x, y, width, height = box
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=8,
        fill=(2, 3, 6, 255),
        outline=(*base.GOLD, 255),
        width=2,
    )


def repaint_story_context(image: Any, row: Dict[str, Any], base: Any) -> Tuple[int, Dict[str, Any]]:
    template_spec = base.spec("hsd_game_recap_final_score_c_story")
    context_box = base.zone(template_spec, "context_row")
    context = build_story_context(row, base)
    segments = context["segments"]

    _opaque_panel(image, context_box, base)
    inner_width = context_box[2] - 48
    separator_space = 20 * max(0, len(segments) - 1)
    segment_width = max(120, (inner_width - separator_space) // max(1, len(segments)))
    x_cursor = context_box[0] + 24
    overflow = 0
    for index, segment in enumerate(segments):
        overflow += base.draw_textured_text(
            image,
            (x_cursor, context_box[1] + 10, segment_width, context_box[3] - 20),
            segment,
            "context",
            25,
            14,
            base.INK,
            1,
            "center",
        )
        x_cursor += segment_width
        if index < len(segments) - 1:
            base.line(
                image,
                (
                    x_cursor + 5,
                    context_box[1] + 14,
                    x_cursor + 5,
                    context_box[1] + context_box[3] - 14,
                ),
                base.GOLD,
                2,
            )
            x_cursor += 20
    return overflow, context


def repaint_story_cta(
    image: Any,
    row: Dict[str, Any],
    score_winner: str,
    score_loser: str,
    base: Any,
) -> Tuple[int, Dict[str, Any]]:
    cta = build_story_prompt(row, score_winner, score_loser, base)
    hook = (56, 1410, 968, 230)
    _opaque_panel(image, hook, base)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((56, 1410, 226, 1640), radius=8, fill=(*base.GOLD_LIGHT, 255))
    overflow = 0
    overflow += base.draw_textured_text(image, (72, 1440, 138, 62), "YOUR", "context", 34, 18, base.DARK, 1, "center")
    overflow += base.draw_textured_text(image, (72, 1512, 138, 62), "TAKE", "context", 34, 18, base.DARK, 1, "center")
    overflow += base.draw_textured_text(
        image,
        (254, 1424, 730, 126),
        cta["prompt"],
        "display",
        48,
        23,
        base.INK,
        3,
        "left",
    )
    base.line(image, (254, 1552, 984, 1552), base.GOLD, 2)
    overflow += base.draw_textured_text(
        image,
        (254, 1562, 730, 54),
        "DROP YOUR READ BELOW.",
        "context",
        27,
        15,
        base.GOLD_LIGHT,
        1,
        "left",
    )
    return overflow, cta


def install_patch(base: Any) -> Any:
    if getattr(base, "_HSD_PHASE6K_INSTALLED", False):
        return base

    original_render_final_c = base.render_final_c
    original_make_manifest_item = base.make_manifest_item

    for field in STORY_MANIFEST_FIELDS:
        if field not in base.MANIFEST_FIELDS:
            base.MANIFEST_FIELDS.append(field)

    # This closes the generic source-row-only placeholder blind spot for future
    # helpers that inspect the base token set.
    if hasattr(base, "PLACEHOLDER_TOKENS"):
        base.PLACEHOLDER_TOKENS.update({"TBA", "TBD", "UNKNOWN"})

    def patched_story_prompt_for(row: Dict[str, Any], score_winner: str, score_loser: str) -> str:
        return build_story_prompt(row, score_winner, score_loser, base)["prompt"]

    base.story_prompt_for = patched_story_prompt_for

    def patched_render_final_c(row: Dict[str, Any], aliases: Dict[str, str], logos: Dict[str, str]):
        image, meta = original_render_final_c(row, aliases, logos)
        score_winner, score_loser = base.score_parts(row)
        context_overflow, context = repaint_story_context(image, row, base)
        cta_overflow, cta = repaint_story_cta(image, row, score_winner, score_loser, base)

        meta = dict(meta)
        meta.update({
            "route_decision": "rendered_final_c_story_phase6k_handoff_polish",
            "render_patch_version": PATCH_VERSION,
            **{key: value for key, value in context.items() if key != "segments"},
            **{key: value for key, value in cta.items() if key != "prompt"},
        })
        meta["zone_overflow_count"] = int(meta.get("zone_overflow_count") or 0) + context_overflow + cta_overflow
        meta["content_module_prompt"] = cta["prompt"]
        return image, meta

    def patched_make_manifest_item(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        item = original_make_manifest_item(*args, **kwargs)
        meta = kwargs.get("meta")
        if meta is None and len(args) >= 8:
            meta = args[7]
        meta = dict(meta or {})
        if clean(item.get("template_id")) == "hsd_game_recap_final_score_c_story":
            for field in STORY_MANIFEST_FIELDS:
                item[field] = clean(meta.get(field))
            context_ok = item.get("story_context_status") == CONTEXT_PASS
            cta_ok = item.get("story_cta_status") == CTA_PASS
            rendered_copy = " ".join([
                clean(item.get("story_context_copy")),
                clean(item.get("story_cta_prompt")),
            ])
            if contains_unknown(rendered_copy):
                item["placeholder_layer_count"] = max(1, int(item.get("placeholder_layer_count") or 0))
                context_ok = False
            if not (context_ok and cta_ok) or int(item.get("zone_overflow_count") or 0) != 0:
                item["near_post_ready_candidate"] = "false"
        return item

    base.render_final_c = patched_render_final_c
    base.make_manifest_item = patched_make_manifest_item
    base._HSD_PHASE6K_INSTALLED = True
    base._HSD_PHASE6K_PATCH_VERSION = PATCH_VERSION
    return base
