"""
Her Sports Daily Graphics System Generator
-----------------------------------------

Reads:
    daily_content_brief.csv

Creates:
    tonight_in_the_w_visual_specs.csv
    graphic_copy_rules.csv
    daily_command_file.csv
    image_generation_prompts.csv
    hsd_graphics_system_hub.md

Purpose:
- Turn ranked stories into visual production instructions
- Create graphic-specific copy rules
- Create one daily command file for what to post first
- Create prompt-ready text for image generation workflows
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

INPUT_FILE = "daily_content_brief.csv"
TONIGHT_SPECS_FILE = "tonight_in_the_w_visual_specs.csv"
COPY_RULES_FILE = "graphic_copy_rules.csv"
DAILY_COMMAND_FILE = "daily_command_file.csv"
IMAGE_PROMPTS_FILE = "image_generation_prompts.csv"
HUB_FILE = "hsd_graphics_system_hub.md"

BRAND_NAME = "Her Sports Daily"


def clean(value: str) -> str:
    value = value or ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value


def rank_num(row: Dict[str, str]) -> int:
    try:
        return int(clean(row.get("rank", "999")))
    except Exception:
        return 999


def load_rows() -> List[Dict[str, str]]:
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=rank_num)
    return rows


def decision_score(decision: str) -> int:
    return {
        "Must Post": 100,
        "Maybe Post": 75,
        "Save for Weekend": 50,
        "Verify First": 20,
        "Review Before Posting": 15,
    }.get(clean(decision), 0)


def family(row: Dict[str, str]) -> str:
    sport = clean(row.get("sport", ""))
    story_type = clean(row.get("story_type", ""))
    decision = clean(row.get("editorial_decision", ""))

    if sport == "WNBA" and story_type in {"Game Preview", "Game Recap / Result", "Tournament Update", "Record / Milestone"}:
        return "Tonight in the W"
    if story_type == "Game Preview":
        return "Pregame Analysis"
    if story_type == "Game Recap / Result":
        return "Postgame Recap"
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the Game"
    if story_type == "Record / Milestone":
        return "Milestone Card"
    if story_type == "Recruiting / Roster News":
        return "Roster News"
    if decision == "Must Post":
        return "Breaking News"
    return "Standard Feed"


def template_name(row: Dict[str, str]) -> str:
    mapping = {
        "Tonight in the W": "Tonight in the W",
        "Pregame Analysis": "Pregame Matchup Card",
        "Postgame Recap": "Postgame Recap Card",
        "Growth of the Game": "Growth Carousel",
        "Milestone Card": "Milestone Graphic",
        "Roster News": "Roster Update Card",
        "Breaking News": "Breaking News Card",
        "Standard Feed": "Standard Feed Card",
    }
    return mapping.get(family(row), "Standard Feed Card")


def asset_shape(row: Dict[str, str]) -> str:
    fam = family(row)
    if fam in {"Tonight in the W", "Pregame Analysis", "Postgame Recap", "Growth of the Game"}:
        return "4-slide 4:5 carousel"
    return "single 4:5 feed card"


def posting_priority_score(row: Dict[str, str]) -> int:
    score = decision_score(row.get("editorial_decision", ""))
    try:
        editorial_score = int(clean(row.get("editorial_score", "0")))
    except Exception:
        editorial_score = 0

    freshness_bonus = 0
    try:
        age_hours = float(clean(row.get("age_hours", "999")))
        if age_hours <= 6:
            freshness_bonus = 10
        elif age_hours <= 12:
            freshness_bonus = 7
        elif age_hours <= 24:
            freshness_bonus = 4
    except Exception:
        pass

    sport_bonus = 0
    if clean(row.get("sport", "")) == "WNBA":
        sport_bonus = 8
    elif clean(row.get("sport", "")) in {"Softball", "NCAA Women's Basketball", "NWSL / Women's Soccer"}:
        sport_bonus = 5

    return score + editorial_score + freshness_bonus + sport_bonus


def short_text(text: str, limit: int) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].strip()
    return cut if cut else text[:limit].strip()


def visual_style_notes(template: str) -> str:
    mapping = {
        "Tonight in the W": "Use energetic sports graphic styling, matchup emphasis, strong hierarchy, top-left watermark safe zone, and clear CTA.",
        "Pregame Matchup Card": "Use versus layout, key player focus, one insight panel, and clean bold headline styling.",
        "Postgame Recap Card": "Use recap structure, outcome first, top performer callout, and one takeaway panel.",
        "Growth Carousel": "Use clean editorial design, stat-forward layout, strong number hierarchy, and easy-to-read supporting text.",
        "Milestone Graphic": "Use athlete hero image, big milestone number or phrase, and one concise context line.",
        "Roster Update Card": "Use athlete/program focus, breaking-update feel, and one concise why-it-matters line.",
        "Breaking News Card": "Use urgent headline hierarchy, punchy subhead, and minimal clutter.",
        "Standard Feed Card": "Use simple clean headline card with one supporting line and brand bug.",
    }
    return mapping.get(template, "Use clean editorial sports styling and clear hierarchy.")


def tonight_card_kind(row: Dict[str, str]) -> str:
    story_type = clean(row.get("story_type", ""))
    if story_type == "Game Preview":
        return "Pregame"
    if story_type == "Game Recap / Result":
        return "Postgame"
    if story_type == "Tournament Update":
        return "Update"
    if story_type == "Record / Milestone":
        return "Stat Watch"
    return "League Watch"


def write_tonight_specs(rows: List[Dict[str, str]]) -> None:
    candidates = [
        r for r in rows
        if clean(r.get("sport", "")) == "WNBA"
        and clean(r.get("editorial_decision", "")) in {"Must Post", "Maybe Post", "Save for Weekend"}
    ]
    candidates.sort(key=lambda r: (-posting_priority_score(r), rank_num(r)))
    selected = candidates[:6]

    fieldnames = [
        "slot", "card_kind", "headline_text", "subhead_text", "key_text",
        "layout_spec", "design_notes", "cta", "source", "link"
    ]
    with open(TONIGHT_SPECS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(selected, start=1):
            writer.writerow({
                "slot": str(idx),
                "card_kind": tonight_card_kind(row),
                "headline_text": short_text(f"Tonight in the W: {clean(row.get('headline', ''))}", 78),
                "subhead_text": short_text(clean(row.get("hook", "")) or clean(row.get("instagram_angle", "")), 110),
                "key_text": short_text(clean(row.get("why_it_matters", "")), 120),
                "layout_spec": "4:5 carousel, top-left watermark, main headline top third, supporting copy middle, CTA footer.",
                "design_notes": visual_style_notes("Tonight in the W"),
                "cta": "What are you watching tonight?",
                "source": clean(row.get("source", "")),
                "link": clean(row.get("link", "")),
            })


def write_copy_rules(rows: List[Dict[str, str]]) -> None:
    templates = [
        ("Tonight in the W", "Headline 78 max | subhead 110 max | CTA 45 max", "Lead with matchup or watch angle. Keep fast and punchy."),
        ("Pregame Matchup Card", "Headline 70 max | subhead 100 max | insight 120 max", "Lead with matchup. Add one watch point."),
        ("Predictions Card", "Headline 60 max | prediction line 80 max | support line 110 max", "State prediction clearly. Keep confidence level simple."),
        ("Postgame Recap Card", "Headline 70 max | recap line 110 max | takeaway 120 max", "Lead with result. Then give biggest takeaway."),
        ("Growth Carousel", "Headline 70 max | stat line 90 max | context line 120 max", "Lead with the number or business angle."),
        ("Milestone Graphic", "Headline 65 max | milestone line 80 max | context 110 max", "Lead with the milestone, not the full article title."),
        ("Breaking News Card", "Headline 68 max | subhead 95 max | why-it-matters 110 max", "Lead with urgency and clarity."),
    ]

    fieldnames = ["template_name", "copy_limits", "copy_rule", "design_rule", "brand_rule"]
    with open(COPY_RULES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for template_name_value, limits, copy_rule in templates:
            writer.writerow({
                "template_name": template_name_value,
                "copy_limits": limits,
                "copy_rule": copy_rule,
                "design_rule": visual_style_notes(template_name_value),
                "brand_rule": "Place the compact stacked Her Sports Daily watermark in the top-left safe zone unless layout requires another safe zone.",
            })


def write_daily_command(rows: List[Dict[str, str]]) -> None:
    enriched = sorted(rows, key=lambda r: (-posting_priority_score(r), rank_num(r)))
    fieldnames = [
        "post_sequence", "headline", "editorial_decision", "content_family", "template_name",
        "asset_shape", "action", "timing", "caption_direction", "graphic_direction", "reason"
    ]
    with open(DAILY_COMMAND_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(enriched, start=1):
            if idx == 1:
                action = "Make and post first"
            elif idx == 2:
                action = "Make and post second"
            elif idx == 3:
                action = "Make and post third"
            elif clean(row.get("editorial_decision", "")) in {"Must Post", "Maybe Post"}:
                action = "Make if time today"
            elif clean(row.get("editorial_decision", "")) == "Save for Weekend":
                action = "Save for weekend"
            else:
                action = "Hold"

            writer.writerow({
                "post_sequence": str(idx),
                "headline": clean(row.get("headline", "")),
                "editorial_decision": clean(row.get("editorial_decision", "")),
                "content_family": family(row),
                "template_name": template_name(row),
                "asset_shape": asset_shape(row),
                "action": action,
                "timing": clean(row.get("recommended_timing", "")),
                "caption_direction": short_text(clean(row.get("instagram_angle", "")), 120),
                "graphic_direction": short_text(clean(row.get("visual_brief", "")), 140),
                "reason": short_text(clean(row.get("decision_reason", "")), 140),
            })


def image_prompt(row: Dict[str, str]) -> str:
    template = template_name(row)
    headline = short_text(clean(row.get("headline", "")), 90)
    subhead = short_text(clean(row.get("why_it_matters", "")) or clean(row.get("instagram_angle", "")), 130)
    sport = clean(row.get("sport", "Women's sports"))
    family_name = family(row)
    visual_notes = visual_style_notes(template)

    if asset_shape(row) == "4-slide 4:5 carousel":
        return (
            f"Create a 4-slide 4:5 Instagram carousel for {BRAND_NAME}. "
            f"Template style: {template}. Sport: {sport}. Content family: {family_name}. "
            f"Use a bold editorial women's sports aesthetic with strong hierarchy. "
            f"Slide 1 headline: '{headline}'. "
            f"Slide 2 title: 'Why it matters' with body: '{subhead}'. "
            f"Slide 3 title: 'The angle' with body: '{short_text(clean(row.get('instagram_angle', '')) or clean(row.get('why_it_matters', '')), 120)}'. "
            f"Slide 4 title: 'Your take?' with a short CTA to comment and follow {BRAND_NAME}. "
            f"{visual_notes}"
        )
    return (
        f"Create a single 4:5 Instagram feed graphic for {BRAND_NAME}. "
        f"Template style: {template}. Sport: {sport}. Content family: {family_name}. "
        f"Main headline: '{headline}'. Supporting line: '{subhead}'. "
        f"Include a short footer CTA such as 'More women's sports daily'. "
        f"Use a clean modern sports editorial look. {visual_notes}"
    )


def write_image_prompts(rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        "rank", "headline", "content_family", "template_name", "asset_shape",
        "suggested_aspect_ratio", "image_generation_prompt"
    ]
    with open(IMAGE_PROMPTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "rank": clean(row.get("rank", "")),
                "headline": clean(row.get("headline", "")),
                "content_family": family(row),
                "template_name": template_name(row),
                "asset_shape": asset_shape(row),
                "suggested_aspect_ratio": "4:5",
                "image_generation_prompt": image_prompt(row),
            })


def write_hub(rows: List[Dict[str, str]]) -> None:
    top_rows = sorted(rows, key=lambda r: (-posting_priority_score(r), rank_num(r)))[:3]
    lines = [
        "# Her Sports Daily Graphics System Hub",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Files included",
        "",
        f"- `{TONIGHT_SPECS_FILE}`",
        f"- `{COPY_RULES_FILE}`",
        f"- `{DAILY_COMMAND_FILE}`",
        f"- `{IMAGE_PROMPTS_FILE}`",
        "",
        "## Top 3 priority posts",
        "",
    ]
    for idx, row in enumerate(top_rows, start=1):
        lines.extend([
            f"### Post {idx}: {clean(row.get('headline', ''))}",
            "",
            f"- Family: {family(row)}",
            f"- Template: {template_name(row)}",
            f"- Asset: {asset_shape(row)}",
            f"- Timing: {clean(row.get('recommended_timing', ''))}",
            "",
        ])

    lines.extend([
        "## What this system does",
        "",
        "- Creates visual specs for Tonight in the W graphics.",
        "- Creates copy rules for each main post type.",
        "- Creates one daily command file so you know what to make first.",
        "- Creates prompt-ready rows for an image generation workflow.",
        "",
    ])
    Path(HUB_FILE).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = load_rows()
    write_tonight_specs(rows)
    write_copy_rules(rows)
    write_daily_command(rows)
    write_image_prompts(rows)
    write_hub(rows)
    print(f"Created {TONIGHT_SPECS_FILE}")
    print(f"Created {COPY_RULES_FILE}")
    print(f"Created {DAILY_COMMAND_FILE}")
    print(f"Created {IMAGE_PROMPTS_FILE}")
    print(f"Created {HUB_FILE}")


if __name__ == "__main__":
    main()
