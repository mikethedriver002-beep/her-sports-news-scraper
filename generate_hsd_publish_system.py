"""
Her Sports Daily Publish System Generator
----------------------------------------

Reads:
    daily_content_brief.csv

Creates:
    tonight_in_the_w_graphic_templates.csv
    post_template_mapper.csv
    master_posting_dashboard.csv
    ready_to_post_graphic_copy.csv
    hsd_publish_system_hub.md

Purpose:
- Map stories to your real content formats
- Prioritize what to post first, second, and third
- Create ready-to-post graphic copy with simple character limits
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


INPUT_FILE = "daily_content_brief.csv"
TONIGHT_TEMPLATES_FILE = "tonight_in_the_w_graphic_templates.csv"
TEMPLATE_MAPPER_FILE = "post_template_mapper.csv"
MASTER_DASHBOARD_FILE = "master_posting_dashboard.csv"
GRAPHIC_COPY_FILE = "ready_to_post_graphic_copy.csv"
HUB_FILE = "hsd_publish_system_hub.md"

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
        return "Milestone / Stat Watch"
    if story_type == "Recruiting / Roster News":
        return "Roster / Recruiting"
    if decision == "Must Post":
        return "Breaking News"
    return "Standard Feed Post"


def template_name(row: Dict[str, str]) -> str:
    fam = family(row)
    mapping = {
        "Tonight in the W": "Tonight in the W 4-Slide Template",
        "Pregame Analysis": "Pregame Matchup Template",
        "Postgame Recap": "Postgame Recap Template",
        "Growth of the Game": "Growth Carousel Template",
        "Milestone / Stat Watch": "Milestone Graphic Template",
        "Roster / Recruiting": "Recruiting News Template",
        "Breaking News": "Breaking News Card Template",
        "Standard Feed Post": "Standard Feed Card Template",
    }
    return mapping.get(fam, "Standard Feed Card Template")


def asset_type(row: Dict[str, str]) -> str:
    fam = family(row)
    mapping = {
        "Tonight in the W": "4-slide carousel",
        "Pregame Analysis": "4-slide carousel",
        "Postgame Recap": "single card or 4-slide carousel",
        "Growth of the Game": "4-slide carousel",
        "Milestone / Stat Watch": "single card or 3-slide carousel",
        "Roster / Recruiting": "single card + Story follow-up",
        "Breaking News": "single card + carousel",
        "Standard Feed Post": "single feed card",
    }
    return mapping.get(fam, "single feed card")


def post_order_bucket(row: Dict[str, str]) -> str:
    decision = clean(row.get("editorial_decision", ""))
    if decision == "Must Post":
        return "Post first"
    if decision == "Maybe Post":
        return "Post second"
    if decision == "Save for Weekend":
        return "Backlog"
    return "Hold"


def dashboard_priority_score(row: Dict[str, str]) -> int:
    base = decision_score(row.get("editorial_decision", ""))
    try:
        editorial_score = int(clean(row.get("editorial_score", "0")))
    except Exception:
        editorial_score = 0

    sport_bonus = 0
    if clean(row.get("sport", "")) == "WNBA":
        sport_bonus = 8
    elif clean(row.get("sport", "")) in {"Softball", "NCAA Women's Basketball", "NWSL / Women's Soccer"}:
        sport_bonus = 5

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

    return base + editorial_score + sport_bonus + freshness_bonus


def short_copy(text: str, limit: int) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].strip()
    if not cut:
        cut = text[:limit].strip()
    return cut


def ready_headline(row: Dict[str, str], limit: int = 70) -> str:
    headline = clean(row.get("headline", ""))
    return short_copy(headline, limit)


def ready_subhead(row: Dict[str, str], limit: int = 110) -> str:
    story_type = clean(row.get("story_type", ""))
    why = clean(row.get("why_it_matters", ""))
    angle = clean(row.get("instagram_angle", ""))

    if story_type in {"Business / Growth", "League Expansion"}:
        text = why
    elif story_type in {"Game Preview", "Game Recap / Result"}:
        text = angle or why
    else:
        text = why or angle

    return short_copy(text, limit)


def ready_footer(row: Dict[str, str], limit: int = 45) -> str:
    sport = clean(row.get("sport", "Women's Sports"))
    prompts = {
        "WNBA": "More WNBA coverage daily",
        "Softball": "More softball coverage daily",
        "Golf / LPGA": "More LPGA coverage daily",
        "NCAA Women's Basketball": "More women's hoops daily",
        "NWSL / Women's Soccer": "More women's soccer daily",
    }
    return short_copy(prompts.get(sport, "More women's sports daily"), limit)


def slide_texts(row: Dict[str, str]) -> List[Dict[str, str]]:
    sport = clean(row.get("sport", ""))
    story_type = clean(row.get("story_type", ""))
    headline = ready_headline(row, 65)
    why = short_copy(clean(row.get("why_it_matters", "")), 120)
    angle = short_copy(clean(row.get("instagram_angle", "")), 120)

    slide_1 = {"slide_number": "1", "slide_role": "Hook", "slide_title": headline, "slide_body": "The story you need to know."}
    slide_2 = {"slide_number": "2", "slide_role": "Context", "slide_title": "Why it matters", "slide_body": why or angle or headline}
    slide_3 = {"slide_number": "3", "slide_role": "Angle", "slide_title": "The angle", "slide_body": angle or why or headline}
    slide_4 = {"slide_number": "4", "slide_role": "CTA", "slide_title": f"Your take on this {sport} story?", "slide_body": "Follow Her Sports Daily for more."}

    if story_type == "Game Preview":
        slide_2["slide_title"] = "What to watch"
        slide_2["slide_body"] = angle or "Watch the stars, matchup edges, and momentum."
    elif story_type == "Game Recap / Result":
        slide_2["slide_title"] = "What happened"
        slide_2["slide_body"] = why or "Quick recap and top takeaway."
    elif story_type in {"Business / Growth", "League Expansion"}:
        slide_2["slide_title"] = "The number to know"
        slide_3["slide_title"] = "Why this matters"
    elif story_type == "Record / Milestone":
        slide_2["slide_title"] = "The milestone"

    return [slide_1, slide_2, slide_3, slide_4]


def tonight_template_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    candidates = [
        r for r in rows
        if clean(r.get("sport", "")) == "WNBA"
        and clean(r.get("editorial_decision", "")) in {"Must Post", "Maybe Post", "Save for Weekend"}
    ]
    candidates.sort(key=lambda r: (-dashboard_priority_score(r), rank_num(r)))
    selected = candidates[:6]

    output = []
    for idx, row in enumerate(selected, start=1):
        card_kind = "Pregame"
        story_type = clean(row.get("story_type", ""))
        if story_type == "Game Recap / Result":
            card_kind = "Postgame"
        elif story_type == "Record / Milestone":
            card_kind = "Stat Watch"
        elif story_type == "Tournament Update":
            card_kind = "Update"

        output.append({
            "slot": str(idx),
            "template_name": "Tonight in the W 4-Slide Template",
            "card_kind": card_kind,
            "headline": short_copy(f"Tonight in the W: {clean(row.get('headline', ''))}", 75),
            "subhead": ready_subhead(row, 100),
            "key_text": short_copy(clean(row.get("hook", "")) or clean(row.get("instagram_angle", "")), 100),
            "cta": "Who are you watching tonight?",
            "source": clean(row.get("source", "")),
            "link": clean(row.get("link", "")),
        })
    return output


def write_tonight_templates(rows: List[Dict[str, str]]) -> None:
    fieldnames = ["slot", "template_name", "card_kind", "headline", "subhead", "key_text", "cta", "source", "link"]
    with open(TONIGHT_TEMPLATES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in tonight_template_rows(rows):
            writer.writerow(row)


def write_template_mapper(rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        "rank", "headline", "editorial_decision", "sport", "story_type",
        "content_family", "template_name", "asset_type", "recommended_use",
        "reason_for_template_choice"
    ]
    with open(TEMPLATE_MAPPER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            fam = family(row)
            writer.writerow({
                "rank": clean(row.get("rank", "")),
                "headline": clean(row.get("headline", "")),
                "editorial_decision": clean(row.get("editorial_decision", "")),
                "sport": clean(row.get("sport", "")),
                "story_type": clean(row.get("story_type", "")),
                "content_family": fam,
                "template_name": template_name(row),
                "asset_type": asset_type(row),
                "recommended_use": post_order_bucket(row),
                "reason_for_template_choice": clean(row.get("visual_brief", "")) or fam,
            })


def write_master_dashboard(rows: List[Dict[str, str]]) -> None:
    enriched = []
    for row in rows:
        score = dashboard_priority_score(row)
        enriched.append((score, row))
    enriched.sort(key=lambda x: (-x[0], rank_num(x[1])))

    fieldnames = [
        "posting_order", "priority_score", "rank", "headline", "editorial_decision",
        "sport", "story_type", "content_family", "template_name",
        "recommended_asset", "recommended_timing", "post_now_or_later",
        "why_this_is_priority"
    ]

    with open(MASTER_DASHBOARD_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, (score, row) in enumerate(enriched, start=1):
            decision = clean(row.get("editorial_decision", ""))
            if idx == 1:
                post_now = "Post 1st"
            elif idx == 2:
                post_now = "Post 2nd"
            elif idx == 3:
                post_now = "Post 3rd"
            elif decision in {"Must Post", "Maybe Post"}:
                post_now = "Post later today"
            elif decision == "Save for Weekend":
                post_now = "Save for weekend"
            else:
                post_now = "Hold"

            writer.writerow({
                "posting_order": str(idx),
                "priority_score": str(score),
                "rank": clean(row.get("rank", "")),
                "headline": clean(row.get("headline", "")),
                "editorial_decision": decision,
                "sport": clean(row.get("sport", "")),
                "story_type": clean(row.get("story_type", "")),
                "content_family": family(row),
                "template_name": template_name(row),
                "recommended_asset": asset_type(row),
                "recommended_timing": clean(row.get("recommended_timing", "")),
                "post_now_or_later": post_now,
                "why_this_is_priority": short_copy(clean(row.get("decision_reason", "")), 140),
            })


def write_ready_graphic_copy(rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        "rank", "headline", "template_name", "headline_max_70", "subhead_max_110",
        "footer_max_45", "slide_number", "slide_role", "slide_title", "slide_body_max_120"
    ]

    with open(GRAPHIC_COPY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            template = template_name(row)
            base = {
                "rank": clean(row.get("rank", "")),
                "headline": clean(row.get("headline", "")),
                "template_name": template,
                "headline_max_70": ready_headline(row, 70),
                "subhead_max_110": ready_subhead(row, 110),
                "footer_max_45": ready_footer(row, 45),
            }
            for slide in slide_texts(row):
                writer.writerow({
                    **base,
                    "slide_number": slide["slide_number"],
                    "slide_role": slide["slide_role"],
                    "slide_title": short_copy(slide["slide_title"], 55),
                    "slide_body_max_120": short_copy(slide["slide_body"], 120),
                })


def write_hub(rows: List[Dict[str, str]]) -> None:
    top3 = []
    dashboard_rows = []
    with open(MASTER_DASHBOARD_FILE, newline="", encoding="utf-8") as f:
        dashboard_rows = list(csv.DictReader(f))
    top3 = dashboard_rows[:3]

    lines = [
        "# Her Sports Daily Publish System Hub",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Files included",
        "",
        f"- `{TONIGHT_TEMPLATES_FILE}`",
        f"- `{TEMPLATE_MAPPER_FILE}`",
        f"- `{MASTER_DASHBOARD_FILE}`",
        f"- `{GRAPHIC_COPY_FILE}`",
        "",
        "## Top 3 posts to make first",
        "",
    ]

    for row in top3:
        lines.extend([
            f"### {row.get('post_now_or_later', '')}: {row.get('headline', '')}",
            "",
            f"- Sport: {row.get('sport', '')}",
            f"- Story type: {row.get('story_type', '')}",
            f"- Template: {row.get('template_name', '')}",
            f"- Asset: {row.get('recommended_asset', '')}",
            f"- Timing: {row.get('recommended_timing', '')}",
            "",
        ])

    lines.extend([
        "## What this system solves",
        "",
        "- It picks the order of what to post first, second, and third.",
        "- It maps each story to the right Her Sports Daily format.",
        "- It gives you shorter ready-to-post graphic copy with simple limits.",
        "- It creates a Tonight in the W graphic template queue automatically.",
        "",
    ])

    Path(HUB_FILE).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = load_rows()
    write_tonight_templates(rows)
    write_template_mapper(rows)
    write_master_dashboard(rows)
    write_ready_graphic_copy(rows)
    write_hub(rows)
    print(f"Created {TONIGHT_TEMPLATES_FILE}")
    print(f"Created {TEMPLATE_MAPPER_FILE}")
    print(f"Created {MASTER_DASHBOARD_FILE}")
    print(f"Created {GRAPHIC_COPY_FILE}")
    print(f"Created {HUB_FILE}")


if __name__ == "__main__":
    main()
