from __future__ import annotations

"""Phase 6K additive wrapper for Template Renderer v4.

This module deliberately leaves the Phase 6J renderer untouched. It imports that
renderer, replaces only the Story context/CTA behavior, adds manifest-visible
rendered-copy metadata, records intentional Final Score B downgrades, and then
runs the original renderer entry point.
"""

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generate_hsd_template_renderer_v4 as base

_ORIGINAL_EVENT_DATE = base.event_date
_ORIGINAL_EVENT_LOCATION = base.event_location
_ORIGINAL_EVENT_LEAGUE = base.event_league

VERSION = "v4.6-phase6k-story-context-cta-polish"

CONTEXT_FORBIDDEN_TOKENS = {
    "DATE TBA",
    "DATE TBD",
    "LOCATION TBA",
    "LOCATION TBD",
    "VENUE TBA",
    "VENUE TBD",
    "TIME TBA",
    "TIME TBD",
    "TV TBA",
    "TV TBD",
    "UNKNOWN LOCATION",
    "NOT AVAILABLE",
    "VENUE NAME",
    "CITY, STATE",
    "COMPETITION NAME",
}
UNVERIFIED_CONTEXT_EXACT = {
    "",
    "TBA",
    "TBD",
    "UNKNOWN",
    "UNKNOWN LOCATION",
    "N/A",
    "NA",
    "NONE",
    "DATE TBA",
    "LOCATION TBA",
    "VENUE TBA",
    "VENUE NAME",
    "CITY, STATE",
    "COMPETITION NAME",
}
GENERIC_STORY_PROMPTS = {
    "WHAT CHANGED THE GAME?",
    "WHO MADE THE DIFFERENCE LATE?",
    "WHERE DID THE GAME TURN?",
}
STORY_CTA_LABEL = "YOUR TAKE"
STORY_CTA_BODY = "DROP YOUR READ BELOW."
LIVE_COPY_FORBIDDEN_TOKENS = CONTEXT_FORBIDDEN_TOKENS | {
    "PRIMARY TEAM",
    "SECONDARY TEAM",
    "TEAM LOGO SLOT",
    "PLAYER NAME",
    "SCORE SLOT",
    "FEATURED PLAYER",
    "PLAYER FEATURE",
    "00-00",
    "00–00",
}

EXTRA_MANIFEST_FIELDS = [
    "context_date",
    "context_date_status",
    "context_location",
    "context_location_status",
    "context_time",
    "context_time_status",
    "context_network",
    "context_network_status",
    "context_league",
    "context_segments",
    "context_segment_count",
    "context_placeholder_count",
    "context_placeholder_tokens",
    "story_winner_short_name",
    "story_prompt",
    "story_cta_label",
    "story_cta_body",
    "story_cta_status",
    "story_cta_score",
    "story_cta_reasons",
    "rendered_copy",
    "rendered_copy_placeholder_count",
    "rendered_copy_placeholder_tokens",
    "source_placeholder_observation_count",
    "source_placeholder_observation_tokens",
]

_FINAL_B_ROUTING: List[Dict[str, Any]] = []
_LAST_TONIGHT_CONTEXT: Dict[str, Any] = {}


def clean(value: Any) -> str:
    return base.clean(value)


def verified_context_value(value: Any) -> str:
    text = clean(value)
    upper = text.upper()
    if upper in UNVERIFIED_CONTEXT_EXACT:
        return ""
    if upper.startswith(("TBA", "TBD", "UNKNOWN")):
        return ""
    if upper.endswith(" TBA") or upper.endswith(" TBD"):
        return ""
    if any(token in upper for token in {"PLACEHOLDER", "TEMPLATE LABEL", "FIXTURE LABEL"}):
        return ""
    return text


def rendered_context_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    date_value = verified_context_value(_ORIGINAL_EVENT_DATE(row))
    location_value = verified_context_value(_ORIGINAL_EVENT_LOCATION(row))
    league_value = verified_context_value(_ORIGINAL_EVENT_LEAGUE(row)) or "WNBA"

    segments = [value for value in [date_value, location_value, league_value] if value]
    rendered = " • ".join(segments)
    upper = rendered.upper()
    placeholder_hits = sorted(token for token in CONTEXT_FORBIDDEN_TOKENS if token in upper)
    return {
        "context_date": date_value,
        "context_date_status": "verified" if date_value else "omitted_missing",
        "context_location": location_value,
        "context_location_status": "verified" if location_value else "omitted_missing",
        "context_league": league_value,
        "context_segments": rendered,
        "context_segment_count": len(segments),
        "context_placeholder_count": len(placeholder_hits),
        "context_placeholder_tokens": ";".join(placeholder_hits),
    }


def final_a_context_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    date_value = verified_context_value(_ORIGINAL_EVENT_DATE(row))
    league_value = verified_context_value(_ORIGINAL_EVENT_LEAGUE(row)) or "WNBA"
    segments = ["FINAL", league_value]
    if date_value:
        segments.append(date_value)
    rendered = " • ".join(segments)
    upper = rendered.upper()
    placeholder_hits = sorted(token for token in CONTEXT_FORBIDDEN_TOKENS if token in upper)
    return {
        "context_date": date_value,
        "context_date_status": "verified" if date_value else "omitted_missing",
        "context_location": "",
        "context_location_status": "not_rendered",
        "context_time": "",
        "context_time_status": "not_rendered",
        "context_network": "",
        "context_network_status": "not_rendered",
        "context_league": league_value,
        "context_segments": rendered,
        "context_segment_count": len(segments),
        "context_placeholder_count": len(placeholder_hits),
        "context_placeholder_tokens": ";".join(placeholder_hits),
    }


def tonight_context_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    time_value = verified_context_value(row.get("time_et") or row.get("start_time_et"))
    network_value = verified_context_value(row.get("tv_network"))
    preview_value = verified_context_value(row.get("preview_label")) or "MATCHUP PREVIEW"
    typed_segments: List[Tuple[str, str]] = []
    if time_value:
        typed_segments.append(("time", time_value))
    if network_value:
        typed_segments.append(("network", network_value))
    typed_segments.append(("preview", preview_value))
    rendered = " • ".join(value for _kind, value in typed_segments)
    upper_rendered = rendered.upper()
    hits = sorted(token for token in LIVE_COPY_FORBIDDEN_TOKENS if token in upper_rendered)
    return {
        "context_date": "",
        "context_date_status": "not_rendered",
        "context_location": "",
        "context_location_status": "not_rendered",
        "context_time": time_value,
        "context_time_status": "verified" if time_value else "omitted_missing",
        "context_network": network_value,
        "context_network_status": "verified" if network_value else "omitted_missing",
        "context_league": "",
        "context_segments": rendered,
        "context_segment_count": len(typed_segments),
        "context_placeholder_count": len(hits),
        "context_placeholder_tokens": ";".join(hits),
        "typed_segments": typed_segments,
    }


def draw_context_tonight(image: Image.Image, row: Dict[str, Any]) -> int:
    global _LAST_TONIGHT_CONTEXT
    meta = tonight_context_metadata(row)
    _LAST_TONIGHT_CONTEXT = dict(meta)
    box = (82, 538, 916, 64)
    base.panel(image, box, base.GOLD, 12, (1, 2, 5, 224), 2)
    typed_segments = meta["typed_segments"]
    draw = ImageDraw.Draw(image, "RGBA")
    if not typed_segments:
        return 0
    gap = 18
    usable = box[2] - 56 - gap * max(0, len(typed_segments) - 1)
    segment_width = max(170, usable // len(typed_segments))
    x_cursor = box[0] + 28
    overflow = 0
    for index, (kind, value) in enumerate(typed_segments):
        icon_x = x_cursor + 22
        icon_y = box[1] + box[3] // 2
        if kind == "time":
            base.icon_clock(draw, (icon_x, icon_y), 14)
        elif kind == "network":
            base.icon_tv(draw, (icon_x - 16, icon_y - 12, 32, 22))
        else:
            base.icon_star(draw, (icon_x, icon_y), 15)
        overflow += base.draw_textured_text(
            image,
            (x_cursor + 48, box[1] + 9, segment_width - 52, box[3] - 18),
            value,
            "context",
            24,
            14,
            base.INK,
            1,
            "left",
        )
        x_cursor += segment_width
        if index < len(typed_segments) - 1:
            base.line(image, (x_cursor + 3, box[1] + 11, x_cursor + 3, box[1] + box[3] - 11), base.GOLD, 2)
            x_cursor += gap
    return overflow


def rendered_copy_for(row: Dict[str, Any], template_id: str, item: Dict[str, Any]) -> str:
    """Return an audit string covering every dynamic text field drawn by the renderer."""
    pieces: List[str] = [
        clean(item.get("context_segments")),
        clean(item.get("headline")) or base.headline_for(row, template_id),
        clean(item.get("content_module_title")),
        clean(item.get("content_module_body")),
        clean(item.get("content_module_prompt")),
        clean(item.get("story_prompt")),
        clean(item.get("story_cta_label")),
        clean(item.get("story_cta_body")),
        clean(item.get("player_names")),
    ]
    if template_id.startswith("hsd_game_recap_final_score"):
        winner, loser = base.final_teams(row)
        score_winner, score_loser = base.score_parts(row)
        combined_score = f"{score_winner}-{score_loser}" if score_winner and score_loser else ""
        pieces.extend(["FINAL", winner, score_winner, loser, score_loser, combined_score])
        if template_id in {"hsd_game_recap_final_score_a", "hsd_game_recap_final_score_b"}:
            editorial_reader = getattr(base, "explicit_editorial_summary", lambda _row: "")
            pieces.append(clean(editorial_reader(row)))
    if template_id == "hsd_tonight_in_the_w_a":
        home = base.first_value(row, ["home_team_name", "home_team_display", "home_team"])
        away = base.first_value(row, ["away_team_name", "away_team_display", "away_team"])
        pieces.extend([
            away,
            home,
            clean(row.get("debate_question") or "WHO HAS THE EDGE TONIGHT?"),
            "SOUND OFF IN THE COMMENTS.",
        ])
        if clean(item.get("module_mode")).lower() == "player":
            pieces.extend([
                clean(item.get("player_names")) or "PLAYER FEATURE",
                "PLAYER SPOTLIGHT • MATCHUP IMPACT • LATE-GAME EDGE",
            ])
        else:
            pieces.extend([
                clean(row.get("watch_title") or "WATCH POINT"),
                clean(row.get("watch_body") or "PACE • STARS • LATE-GAME EDGE"),
            ])
    return " | ".join(piece for piece in pieces if piece)


def context_segment_boxes(
    box: Tuple[int, int, int, int],
    segment_count: int,
    *,
    horizontal_padding: int = 24,
    separator_gap: int = 22,
) -> List[Tuple[int, int, int, int]]:
    if segment_count <= 0:
        return []
    x, y, width, height = box
    available = width - horizontal_padding * 2 - separator_gap * (segment_count - 1)
    if available <= 0:
        raise ValueError("context panel is too narrow for requested segment count")
    base_width, remainder = divmod(available, segment_count)
    boxes: List[Tuple[int, int, int, int]] = []
    cursor = x + horizontal_padding
    for index in range(segment_count):
        current_width = base_width + (1 if index < remainder else 0)
        boxes.append((cursor, y + 10, current_width, height - 20))
        cursor += current_width + separator_gap
    return boxes


def draw_context_panel(image: Image.Image, row: Dict[str, Any], story: bool = False) -> Tuple[int, Dict[str, Any]]:
    if story:
        template_spec = base.spec("hsd_game_recap_final_score_c_story")
        box = base.zone(template_spec, "context_row")
        start_size, floor_size = 25, 14
    else:
        box = (80, 308, 920, 66)
        start_size, floor_size = 22, 14

    meta = rendered_context_metadata(row)
    segments = [part.strip() for part in clean(meta["context_segments"]).split("•") if part.strip()]
    if not segments:
        segments = ["WNBA"]
        meta.update({
            "context_league": "WNBA",
            "context_segments": "WNBA",
            "context_segment_count": 1,
            "context_placeholder_count": 0,
        })

    base.panel(image, box, base.GOLD, 8, (1, 2, 5, 228 if story else 224), 2)
    boxes = context_segment_boxes(box, len(segments))
    overflow = 0
    for index, (segment, text_box) in enumerate(zip(segments, boxes)):
        overflow += base.draw_textured_text(
            image,
            text_box,
            segment,
            "context",
            start_size,
            floor_size,
            base.INK,
            1,
            "center",
        )
        if index < len(boxes) - 1:
            left = text_box[0] + text_box[2]
            next_left = boxes[index + 1][0]
            separator_x = left + max(1, (next_left - left) // 2)
            base.line(
                image,
                (separator_x, box[1] + 14, separator_x, box[1] + box[3] - 14),
                base.GOLD,
                2,
            )
    return overflow, meta


def draw_context_final(image: Image.Image, row: Dict[str, Any], story: bool = False) -> int:
    overflow, _meta = draw_context_panel(image, row, story=story)
    return overflow


def possessive_team(value: str) -> str:
    team = clean(value).upper() or "THE WINNER"
    return f"{team}'" if team.endswith("S") else f"{team}'S"


def story_prompt_for(row: Dict[str, Any], score_winner: str, score_loser: str) -> str:
    winner, _ = base.final_teams(row)
    winner_short = base.short_team(winner) or clean(winner).upper() or "THE WINNER"
    winner_possessive = possessive_team(winner_short)
    margin = base.score_margin(score_winner, score_loser)
    if margin is None:
        return f"WHAT STOOD OUT IN {winner_possessive} WIN?"
    if margin <= 3:
        return f"WHAT SEALED {winner_possessive} LATE WIN?"
    if margin <= 7:
        return f"WHERE DID {winner_short} TAKE CONTROL?"
    return f"WHAT FUELED {winner_possessive} SEPARATION?"


def story_cta_metadata(row: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    winner, _ = base.final_teams(row)
    winner_short = base.short_team(winner) or clean(winner).upper()
    label = STORY_CTA_LABEL
    body = STORY_CTA_BODY
    reasons: List[str] = []
    prompt_upper = clean(prompt).upper()
    if not prompt_upper:
        reasons.append("missing_story_prompt")
    if prompt_upper in GENERIC_STORY_PROMPTS:
        reasons.append("generic_story_prompt")
    if winner_short and winner_short.upper() not in prompt_upper:
        reasons.append("story_prompt_not_matchup_specific")
    if not label:
        reasons.append("missing_story_cta_label")
    if not body:
        reasons.append("missing_story_cta_body")
    score = max(0.0, 1.0 - 0.2 * len(set(reasons)))
    return {
        "story_winner_short_name": winner_short,
        "story_prompt": clean(prompt),
        "story_cta_label": label,
        "story_cta_body": body,
        "story_cta_status": "passed_story_context_cta" if not reasons else "needs_story_context_cta",
        "story_cta_score": f"{score:.3f}",
        "story_cta_reasons": ";".join(sorted(set(reasons))),
    }


def render_final_c(
    row: Dict[str, Any],
    aliases: Dict[str, str],
    logos: Dict[str, str],
) -> Tuple[Image.Image, Dict[str, Any]]:
    template_id = "hsd_game_recap_final_score_c_story"
    template_spec = base.spec(template_id)
    image = Image.open(base.clean_plate_path(template_id)).convert("RGBA")
    winner, loser = base.final_teams(row)
    score_winner, score_loser = base.score_parts(row)

    overflow, context_meta = draw_context_panel(image, row, story=True)

    primary_panel = (56, 466, 968, 370)
    base.panel(image, primary_panel, base.GOLD, 8, (2, 3, 6, 232), 2)
    primary_logo = base.zone(template_spec, "primary_logo_slot")
    primary_team = base.zone(template_spec, "primary_team")
    primary_score = base.zone(template_spec, "primary_score")
    logo_modes = [base.draw_team_asset(image, winner, primary_logo, aliases, logos, base.GOLD)]
    overflow += base.draw_textured_text(image, primary_team, winner, "display", 58, 27, base.INK, 2, "left")
    base.line(
        image,
        (
            primary_team[0],
            primary_team[1] + primary_team[3] - 8,
            primary_team[0] + primary_team[2],
            primary_team[1] + primary_team[3] - 8,
        ),
        base.GOLD,
        2,
    )
    overflow += base.draw_textured_text(image, primary_score, score_winner, "score", 245, 110, base.INK, 1, "center")

    secondary_panel = (56, 804, 968, 350)
    base.panel(image, secondary_panel, base.GOLD, 8, (2, 3, 6, 232), 2)
    secondary_logo = base.zone(template_spec, "secondary_logo_slot")
    secondary_team = base.zone(template_spec, "secondary_team")
    secondary_score = base.zone(template_spec, "secondary_score")
    logo_modes.append(base.draw_team_asset(image, loser, secondary_logo, aliases, logos, base.MUTED))
    overflow += base.draw_textured_text(image, secondary_team, loser, "display", 54, 25, base.MUTED, 2, "left")
    base.line(
        image,
        (
            secondary_team[0],
            secondary_team[1] + secondary_team[3] - 8,
            secondary_team[0] + secondary_team[2],
            secondary_team[1] + secondary_team[3] - 8,
        ),
        base.GOLD,
        2,
    )
    overflow += base.draw_textured_text(image, secondary_score, score_loser, "score", 220, 100, base.INK, 1, "center")

    performer = (56, 1184, 968, 210)
    base.panel(image, performer, base.GOLD, 8, (2, 3, 6, 235), 2)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((56, 1184, 160, 1394), fill=(*base.GOLD_LIGHT, 244))
    performer_name = base.explicit_performer_for(row)
    stat_list = base.verified_stat_values(row)
    if performer_name and stat_list:
        module_mode = "verified_player_stats"
        module_title = "KEY PLAYER"
        module_body = f"{performer_name} • " + " • ".join(f"{value} {label}" for value, label in stat_list[:4])
        overflow += base.draw_textured_text(image, (62, 1208, 96, 58), "KEY", "context", 24, 12, base.DARK, 1, "center")
        overflow += base.draw_textured_text(image, (62, 1298, 96, 58), "PLAYER", "context", 22, 11, base.DARK, 1, "center")
        overflow += base.draw_textured_text(image, (190, 1195, 790, 54), performer_name, "display", 44, 23, base.INK, 1, "left")
        for index, (value, label_text) in enumerate(stat_list[:4]):
            x = 190 + index * 190
            overflow += base.draw_textured_text(image, (x, 1250, 145, 82), value, "score", 68, 32, base.GOLD_LIGHT, 1, "center")
            overflow += base.draw_textured_text(image, (x, 1330, 145, 40), label_text, "context", 22, 13, base.INK, 1, "center")
    else:
        module_mode = "game_edge"
        edge = base.game_edge_module(row, score_winner, score_loser)
        module_title = edge["title"]
        module_body = edge["body"]
        overflow += base.draw_textured_text(image, (62, 1208, 96, 58), "GAME", "context", 24, 12, base.DARK, 1, "center")
        overflow += base.draw_textured_text(image, (62, 1298, 96, 58), "EDGE", "context", 22, 11, base.DARK, 1, "center")
        overflow += base.draw_textured_text(image, (190, 1195, 590, 54), edge["headline"], "display", 44, 23, base.INK, 1, "left")
        overflow += base.draw_textured_text(image, (190, 1252, 610, 95), edge["body"], "body", 27, 16, base.MUTED, 2, "left", uppercase=False)
        if edge["margin"]:
            overflow += base.draw_textured_text(image, (815, 1204, 165, 98), edge["margin"], "score", 78, 40, base.GOLD_LIGHT, 1, "center")
            overflow += base.draw_textured_text(image, (820, 1310, 155, 34), "MARGIN", "context", 20, 12, base.INK, 1, "center")

    prompt = story_prompt_for(row, score_winner, score_loser)
    cta_meta = story_cta_metadata(row, prompt)
    hook = (56, 1410, 968, 230)
    base.panel(image, hook, base.GOLD, 8, (2, 3, 6, 235), 2)
    draw.rectangle((56, 1410, 220, 1640), fill=(*base.GOLD_LIGHT, 244))
    overflow += base.draw_textured_text(image, (72, 1450, 132, 52), "YOUR", "context", 28, 16, base.DARK, 1, "center")
    overflow += base.draw_textured_text(image, (72, 1510, 132, 58), "TAKE", "display", 42, 22, base.DARK, 1, "center")
    base.line(image, (222, 1430, 222, 1620), base.GOLD, 2)
    overflow += base.draw_textured_text(image, (252, 1428, 724, 118), prompt, "display", 47, 24, base.INK, 3, "left")
    base.line(image, (252, 1550, 976, 1550), base.GOLD, 1)
    overflow += base.draw_textured_text(
        image,
        (252, 1560, 724, 50),
        STORY_CTA_BODY,
        "context",
        27,
        15,
        base.GOLD_LIGHT,
        1,
        "left",
    )
    overflow += base.draw_textured_text(
        image,
        (100, 1810, 880, 55),
        "WOMEN'S SPORTS. ALL DAY. EVERY DAY.",
        "context",
        27,
        15,
        base.GOLD_LIGHT,
        1,
        "center",
    )

    meta: Dict[str, Any] = {
        "route_decision": "rendered_final_c_story_phase6k_context_cta",
        "player_assets_used": 0,
        "player_names": "",
        "player_asset_kind": "",
        "fixture_only_player_asset": "false",
        "team_logo_count": sum(mode == "approved_logo" for mode in logo_modes),
        "team_logo_modes": ";".join(logo_modes),
        "zone_overflow_count": overflow,
        **context_meta,
        **cta_meta,
    }
    meta = base.final_score_polish_meta(row, meta, template_id, score_winner, score_loser)
    return image, base.final_score_content_meta(
        row,
        meta,
        template_id,
        module_mode,
        module_title,
        module_body,
        len(stat_list) if module_mode == "verified_player_stats" else 0,
        prompt=prompt,
        player_name=performer_name,
    )


def _manifest_item(
    original_make_manifest_item,
    row: Dict[str, Any],
    template_id: str,
    platform: str,
    variant: str,
    module_mode: str,
    output: Path,
    image: Image.Image,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    item = original_make_manifest_item(
        row,
        template_id,
        platform,
        variant,
        module_mode,
        output,
        image,
        meta,
    )
    is_final = template_id.startswith("hsd_game_recap_final_score")
    if template_id == "hsd_tonight_in_the_w_a":
        context_meta = {key: value for key, value in tonight_context_metadata(row).items() if key != "typed_segments"}
    elif template_id == "hsd_game_recap_final_score_a":
        context_meta = final_a_context_metadata(row)
    elif is_final:
        context_meta = rendered_context_metadata(row)
        context_meta.update({
            "context_time": "",
            "context_time_status": "not_rendered",
            "context_network": "",
            "context_network_status": "not_rendered",
        })
    else:
        context_meta = {
            "context_date": "",
            "context_date_status": "",
            "context_location": "",
            "context_location_status": "",
            "context_time": "",
            "context_time_status": "",
            "context_network": "",
            "context_network_status": "",
            "context_league": "",
            "context_segments": "",
            "context_segment_count": 0,
            "context_placeholder_count": 0,
            "context_placeholder_tokens": "",
        }
    for field in EXTRA_MANIFEST_FIELDS:
        if field.startswith("context_"):
            item[field] = meta.get(field, context_meta.get(field, ""))
        else:
            item[field] = meta.get(field, "")

    rendered_copy = rendered_copy_for(row, template_id, item)
    rendered_hits = sorted(token for token in LIVE_COPY_FORBIDDEN_TOKENS if token in rendered_copy.upper())
    item["rendered_copy"] = rendered_copy
    item["rendered_copy_placeholder_count"] = len(rendered_hits)
    item["rendered_copy_placeholder_tokens"] = ";".join(rendered_hits)
    source_placeholder_tokens = base.content_has_placeholder(row)
    item["source_placeholder_observation_count"] = len(source_placeholder_tokens)
    item["source_placeholder_observation_tokens"] = ";".join(source_placeholder_tokens)
    rendered_placeholder_count = max(
        int(item.get("context_placeholder_count") or 0),
        len(rendered_hits),
    )
    # Phase 6K distinguishes raw source observations from copy that actually
    # reached the image. Filtered context such as LOCATION TBA is omitted and
    # therefore must not remain a false placeholder-layer blocker.
    item["placeholder_layer_count"] = rendered_placeholder_count
    story_pass = (
        template_id != "hsd_game_recap_final_score_c_story"
        or clean(item.get("story_cta_status")) == "passed_story_context_cta"
    )
    item["near_post_ready_candidate"] = "true" if (
        int(item.get("placeholder_layer_count") or 0) == 0
        and int(item.get("zone_overflow_count") or 0) == 0
        and clean(item.get("fixture_only_player_asset") or "false") != "true"
        and story_pass
    ) else "false"
    item["notes"] = clean(meta.get("route_decision") or item.get("notes"))
    return item


def build_contact(items: List[Dict[str, Any]]) -> None:
    if not items:
        return
    columns = 3
    cell_width = 340
    cell_height = 500
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGB", (columns * cell_width + 40, rows * cell_height + 90), (242, 242, 242))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 22), "HSD Template Renderer v4.6 Phase 6K — Story Context + CTA", fill=(20, 20, 20), font=ImageFont.load_default())
    for index, item in enumerate(items):
        path = Path(clean(item.get("output_path")))
        if not path.exists():
            continue
        render = Image.open(path).convert("RGB")
        render.thumbnail((300, 400), Image.Resampling.LANCZOS)
        column = index % columns
        row_index = index // columns
        x = 20 + column * cell_width + (300 - render.width) // 2
        y = 62 + row_index * cell_height
        sheet.paste(render, (x, y))
        label_x = 20 + column * cell_width
        draw.text((label_x, y + 408), f"{item['template_id']} • {item['platform']} • {item['module_mode']}", fill=(20, 20, 20), font=ImageFont.load_default())
        draw.text((label_x, y + 430), clean(item.get("headline"))[:44], fill=(80, 80, 80), font=ImageFont.load_default())
        draw.text(
            (label_x, y + 450),
            f"context={item.get('context_location_status') or 'n/a'} cta={item.get('story_cta_status') or 'n/a'} near={item.get('near_post_ready_candidate')}",
            fill=(80, 80, 80),
            font=ImageFont.load_default(),
        )
    sheet.save(base.CONTACT, quality=92)


def _patch_json_report(path: Path) -> None:
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return
    payload["version"] = VERSION
    payload["phase6k_story_context_cta"] = True
    payload["rendered_copy_metadata_required"] = True
    payload["rendered_copy_placeholder_rows"] = sum(
        int(item.get("rendered_copy_placeholder_count") or 0) > 0
        for item in (payload.get("items") or [])
        if isinstance(item, dict)
    )
    payload["final_score_b_routing"] = list(_FINAL_B_ROUTING)
    payload["final_score_b_rendered_count"] = sum(bool(row.get("rendered")) for row in _FINAL_B_ROUTING)
    payload["final_score_b_downgraded_count"] = sum(not bool(row.get("rendered")) for row in _FINAL_B_ROUTING)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def configure() -> None:
    base.VERSION = VERSION
    base.event_date = lambda row: verified_context_value(_ORIGINAL_EVENT_DATE(row))
    base.event_location = lambda row: verified_context_value(_ORIGINAL_EVENT_LOCATION(row))
    base.event_league = lambda row: verified_context_value(_ORIGINAL_EVENT_LEAGUE(row)) or "WNBA"
    for field in EXTRA_MANIFEST_FIELDS:
        if field not in base.MANIFEST_FIELDS:
            base.MANIFEST_FIELDS.append(field)

    original_make_manifest_item = base.make_manifest_item
    original_render_tonight = base.render_tonight
    original_render_final_b = base.render_final_b

    def wrapped_make_manifest_item(
        row: Dict[str, Any],
        template_id: str,
        platform: str,
        variant: str,
        module_mode: str,
        output: Path,
        image: Image.Image,
        meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        return _manifest_item(
            original_make_manifest_item,
            row,
            template_id,
            platform,
            variant,
            module_mode,
            output,
            image,
            meta,
        )

    def wrapped_render_tonight(*args, **kwargs):
        global _LAST_TONIGHT_CONTEXT
        _LAST_TONIGHT_CONTEXT = {}
        image, meta = original_render_tonight(*args, **kwargs)
        meta.update({key: value for key, value in _LAST_TONIGHT_CONTEXT.items() if key != "typed_segments"})
        return image, meta

    def wrapped_render_final_b(*args, **kwargs):
        image, meta = original_render_final_b(*args, **kwargs)
        row = args[0] if args else kwargs.get("row", {})
        decision = clean(meta.get("route_decision"))
        _FINAL_B_ROUTING.append({
            "source_id": clean(row.get("event_id") or row.get("event_uid")),
            "headline": base.headline_for(row, "hsd_game_recap_final_score_b"),
            "route_decision": decision,
            "rendered": image is not None,
        })
        return image, meta

    base.story_prompt_for = story_prompt_for
    base.draw_context_tonight = draw_context_tonight
    base.draw_context_final = draw_context_final
    base.render_tonight = wrapped_render_tonight
    base.render_final_c = render_final_c
    base.render_final_b = wrapped_render_final_b
    base.make_manifest_item = wrapped_make_manifest_item
    base.build_contact = build_contact


def main(argv: Optional[List[str]] = None) -> int:
    _FINAL_B_ROUTING.clear()
    configure()
    exit_code = base.main(argv)
    _patch_json_report(base.MANIFEST_JSON)
    _patch_json_report(base.REPORT_JSON)
    base.REPORT_MD.write_text(
        "\n".join([
            "# HSD Template Renderer v4.6 Phase 6K",
            "",
            f"Version: `{VERSION}`",
            "",
            "Story context now omits unverified locations instead of rendering TBA copy.",
            "Every Story prompt is matchup-specific and uses a stronger YOUR TAKE hierarchy.",
            "Final Score B remains conditional on a matching real player asset and verified stats.",
            "All outputs remain review-only; production cutover and auto-publish remain disabled.",
            "",
        ]),
        encoding="utf-8",
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
