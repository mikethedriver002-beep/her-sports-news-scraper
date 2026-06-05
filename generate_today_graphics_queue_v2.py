"""
Her Sports Daily Today Graphics Queue Generator v2
-------------------------------------------------

Reads:
    master_posting_dashboard.csv
    daily_command_file.csv
    ready_to_post_graphic_copy.csv
    caption_bank_v2.csv
    image_generation_prompts.csv
    daily_content_brief.csv
    story_context_enriched.csv

Creates:
    today_graphics_queue.md
    today_graphics_queue.csv
    top_3_graphic_packets.md

This version adds verified story context and reduces generic slide copy.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

MASTER_DASHBOARD_FILE = "master_posting_dashboard.csv"
DAILY_COMMAND_FILE = "daily_command_file.csv"
GRAPHIC_COPY_FILE = "ready_to_post_graphic_copy.csv"
CAPTION_BANK_FILE = "caption_bank_v2.csv"
IMAGE_PROMPTS_FILE = "image_generation_prompts.csv"
DAILY_BRIEF_FILE = "daily_content_brief.csv"
STORY_CONTEXT_FILE = "story_context_enriched.csv"
QUEUE_MD_FILE = "today_graphics_queue.md"
QUEUE_CSV_FILE = "today_graphics_queue.csv"
TOP_3_PACKETS_FILE = "top_3_graphic_packets.md"


def clean(value: str) -> str:
    value = value or ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value


def safe_int(value: str, default: int = 999) -> int:
    try:
        return int(clean(value))
    except Exception:
        return default


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())[:140]


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def context_index(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {key(row.get("headline", "")): row for row in rows if key(row.get("headline", ""))}


def choose_caption(caption_rows: List[Dict[str, str]], headline: str) -> str:
    matches = [r for r in caption_rows if key(r.get("headline", "")) == key(headline)]
    if not matches:
        return ""
    for row in matches:
        if clean(row.get("caption_variant", "")) == "carousel":
            return clean(row.get("caption", ""))
    return clean(matches[0].get("caption", ""))


def choose_prompt(prompt_rows: List[Dict[str, str]], headline: str) -> str:
    for row in prompt_rows:
        if key(row.get("headline", "")) == key(headline):
            return clean(row.get("image_generation_prompt", ""))
    return ""


def slide_rows_for_headline(copy_rows: List[Dict[str, str]], headline: str) -> List[Dict[str, str]]:
    matches = [r for r in copy_rows if key(r.get("headline", "")) == key(headline)]
    matches.sort(key=lambda r: safe_int(r.get("slide_number", "999")))
    return matches


def get_primary_rows() -> List[Dict[str, str]]:
    command_rows = load_csv(DAILY_COMMAND_FILE)
    dashboard_rows = load_csv(MASTER_DASHBOARD_FILE)
    brief_rows = load_csv(DAILY_BRIEF_FILE)

    if command_rows:
        command_rows.sort(key=lambda r: safe_int(r.get("post_sequence", "999")))
        return command_rows

    if dashboard_rows:
        dashboard_rows.sort(key=lambda r: safe_int(r.get("posting_order", "999")))
        return [{
            "post_sequence": r.get("posting_order", ""),
            "headline": r.get("headline", ""),
            "editorial_decision": r.get("editorial_decision", ""),
            "content_family": r.get("content_family", ""),
            "template_name": r.get("template_name", ""),
            "asset_shape": r.get("recommended_asset", ""),
            "action": r.get("post_now_or_later", ""),
            "timing": r.get("recommended_timing", ""),
            "caption_direction": "",
            "graphic_direction": r.get("why_this_is_priority", ""),
            "reason": r.get("why_this_is_priority", ""),
        } for r in dashboard_rows]

    if brief_rows:
        brief_rows.sort(key=lambda r: safe_int(r.get("rank", "999")))
        return [{
            "post_sequence": str(i),
            "headline": r.get("headline", ""),
            "editorial_decision": r.get("editorial_decision", ""),
            "content_family": r.get("content_bucket", ""),
            "template_name": r.get("post_format", ""),
            "asset_shape": r.get("post_format", ""),
            "action": r.get("recommended_timing", ""),
            "timing": r.get("recommended_timing", ""),
            "caption_direction": r.get("instagram_angle", ""),
            "graphic_direction": r.get("visual_brief", ""),
            "reason": r.get("decision_reason", ""),
        } for i, r in enumerate(brief_rows, start=1)]
    return []


def context_bullets(ctx: Dict[str, str]) -> List[str]:
    if not ctx:
        return []
    bullets = []
    used = set()
    for label, field in [
        ("Summary", "story_summary"),
        ("Key fact", "key_fact_1"),
        ("Key fact", "key_fact_2"),
        ("Key fact", "key_fact_3"),
        ("Score", "final_score"),
        ("Key number", "key_number"),
        ("Main takeaway", "main_takeaway"),
    ]:
        value = clean(ctx.get(field, ""))
        if value and value not in used:
            bullets.append(f"- {label}: {value}")
            used.add(value)
    return bullets[:7]


def factual_slide_copy(row: Dict[str, str], ctx: Dict[str, str], fallback_slides: List[Dict[str, str]]) -> List[Dict[str, str]]:
    headline = clean(row.get("headline", ""))
    story_type = clean(ctx.get("story_type", "")) or clean(row.get("content_family", ""))
    summary = clean(ctx.get("story_summary", ""))
    fact1 = clean(ctx.get("key_fact_1", ""))
    fact2 = clean(ctx.get("key_fact_2", ""))
    fact3 = clean(ctx.get("key_fact_3", ""))
    score = clean(ctx.get("final_score", ""))
    key_number = clean(ctx.get("key_number", ""))
    takeaway = clean(ctx.get("main_takeaway", ""))

    if ctx:
        slides = [{"num": "1", "role": "Hook", "title": headline, "body": "The story you need to know."}]
        if story_type == "Game Recap / Result":
            body2 = fact1 or summary or "Verified result context should be reviewed before posting."
            if score and score not in body2:
                body2 = f"{body2} Score detail found: {score}."
            slides.append({"num": "2", "role": "What happened", "title": "What happened", "body": body2})
            slides.append({"num": "3", "role": "Why it matters", "title": "Why it matters", "body": takeaway or fact2 or "This result adds context to the season and postseason picture."})
        elif story_type == "Game Preview":
            slides.append({"num": "2", "role": "What to watch", "title": "What to watch", "body": clean(ctx.get("watch_angle", "")) or fact1 or summary})
            slides.append({"num": "3", "role": "Stakes", "title": "The stakes", "body": takeaway or fact2 or "This matchup has a clear watch angle for fans."})
        elif story_type == "Record / Milestone":
            slides.append({"num": "2", "role": "The milestone", "title": "The milestone", "body": clean(ctx.get("milestone_text", "")) or key_number or fact1 or summary})
            slides.append({"num": "3", "role": "Context", "title": "Why it matters", "body": clean(ctx.get("historical_context", "")) or takeaway or fact2})
        elif story_type in {"Business / Growth", "League Expansion"}:
            slides.append({"num": "2", "role": "The number", "title": "The number to know", "body": key_number or fact1 or summary})
            slides.append({"num": "3", "role": "Impact", "title": "Why it matters", "body": clean(ctx.get("business_impact", "")) or takeaway or fact2})
        else:
            slides.append({"num": "2", "role": "Context", "title": "The context", "body": fact1 or summary})
            slides.append({"num": "3", "role": "Angle", "title": "The angle", "body": takeaway or fact2 or fact3})
        slides.append({"num": "4", "role": "CTA", "title": "Your take?", "body": "Follow Her Sports Daily for more women's sports coverage."})
        for slide in slides:
            if not clean(slide["body"]):
                slide["body"] = "Verify story details before posting."
        return slides

    output = []
    for s in fallback_slides:
        output.append({
            "num": clean(s.get("slide_number", "")),
            "role": clean(s.get("slide_role", "")),
            "title": clean(s.get("slide_title", "")) or clean(s.get("headline_max_70", "")),
            "body": clean(s.get("slide_body_max_120", "")) or clean(s.get("subhead_max_110", "")),
        })
    return output


def packet_for_row(row: Dict[str, str], copy_rows: List[Dict[str, str]], caption_rows: List[Dict[str, str]], prompt_rows: List[Dict[str, str]], ctx_by_key: Dict[str, Dict[str, str]]) -> str:
    headline = clean(row.get("headline", ""))
    ctx = ctx_by_key.get(key(headline), {})
    fallback_slides = slide_rows_for_headline(copy_rows, headline)
    caption = choose_caption(caption_rows, headline)
    prompt = choose_prompt(prompt_rows, headline)
    slides = factual_slide_copy(row, ctx, fallback_slides)

    lines = [
        f"## GRAPHIC {clean(row.get('post_sequence', ''))}: {headline}",
        "",
        f"**Action:** {clean(row.get('action', ''))}",
        f"**Decision:** {clean(row.get('editorial_decision', ''))}",
        f"**Content family:** {clean(row.get('content_family', ''))}",
        f"**Template:** {clean(row.get('template_name', ''))}",
        f"**Asset shape:** {clean(row.get('asset_shape', ''))}",
        f"**Timing:** {clean(row.get('timing', ''))}",
        "",
        "### Verified story context",
    ]
    if ctx:
        lines.extend(context_bullets(ctx))
        lines.append(f"- Context confidence: {clean(ctx.get('context_confidence', ''))}")
        lines.append(f"- Manual review flag: {clean(ctx.get('manual_review_flag', ''))}")
        lines.append(f"- Verification notes: {clean(ctx.get('verified_context_notes', ''))}")
    else:
        lines.append("- No enriched context available. Use source link and manual verification before adding stats.")
    lines.extend([
        "",
        "### Design direction",
        clean(row.get("graphic_direction", "")) or "Use Her Sports Daily clean sports editorial styling with strong hierarchy.",
        "",
        "### Caption direction",
        clean(row.get("caption_direction", "")) or "Keep it direct, contextual, and fan-facing.",
        "",
        "### Slide copy",
        "",
    ])
    for slide in slides:
        lines.extend([f"**Slide {slide['num']} - {slide['role']}:** {slide['title']}", slide["body"], ""])
    lines.extend([
        "### Caption",
        caption or "Use the caption bank for this story, or write a direct caption from the angle above.",
        "",
        "### Image prompt",
        prompt or "Use the template, headline, verified story context, slide copy, and design direction above to create the graphic.",
        "",
        "---",
        "",
    ])
    return "\n".join(lines)


def write_queue_md(rows, copy_rows, caption_rows, prompt_rows, ctx_by_key) -> None:
    lines = [
        "# Her Sports Daily Today Graphics Queue",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Use this file as the bridge between the automated news system and the graphics chat.",
        "Copy one full GRAPHIC packet and paste it into the graphics/design chat.",
        "",
        "## Quick order",
        "",
    ]
    for row in rows:
        lines.append(f"{clean(row.get('post_sequence', ''))}. **{clean(row.get('action', ''))}** - {clean(row.get('headline', ''))}")
    lines.append("")
    for row in rows:
        lines.append(packet_for_row(row, copy_rows, caption_rows, prompt_rows, ctx_by_key))
    Path(QUEUE_MD_FILE).write_text("\n".join(lines), encoding="utf-8")


def write_top_3(rows, copy_rows, caption_rows, prompt_rows, ctx_by_key) -> None:
    lines = ["# Top 3 Graphic Packets", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", "These are the first three graphics to make today.", ""]
    for row in rows[:3]:
        lines.append(packet_for_row(row, copy_rows, caption_rows, prompt_rows, ctx_by_key))
    Path(TOP_3_PACKETS_FILE).write_text("\n".join(lines), encoding="utf-8")


def write_queue_csv(rows, caption_rows, prompt_rows, ctx_by_key) -> None:
    fieldnames = ["post_sequence", "headline", "action", "editorial_decision", "content_family", "template_name", "asset_shape", "timing", "context_confidence", "story_summary", "key_fact_1", "key_fact_2", "key_fact_3", "final_score", "key_number", "main_takeaway", "manual_review_flag", "caption", "image_generation_prompt"]
    with open(QUEUE_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            headline = clean(row.get("headline", ""))
            ctx = ctx_by_key.get(key(headline), {})
            writer.writerow({
                "post_sequence": clean(row.get("post_sequence", "")),
                "headline": headline,
                "action": clean(row.get("action", "")),
                "editorial_decision": clean(row.get("editorial_decision", "")),
                "content_family": clean(row.get("content_family", "")),
                "template_name": clean(row.get("template_name", "")),
                "asset_shape": clean(row.get("asset_shape", "")),
                "timing": clean(row.get("timing", "")),
                "context_confidence": clean(ctx.get("context_confidence", "")),
                "story_summary": clean(ctx.get("story_summary", "")),
                "key_fact_1": clean(ctx.get("key_fact_1", "")),
                "key_fact_2": clean(ctx.get("key_fact_2", "")),
                "key_fact_3": clean(ctx.get("key_fact_3", "")),
                "final_score": clean(ctx.get("final_score", "")),
                "key_number": clean(ctx.get("key_number", "")),
                "main_takeaway": clean(ctx.get("main_takeaway", "")),
                "manual_review_flag": clean(ctx.get("manual_review_flag", "")),
                "caption": choose_caption(caption_rows, headline),
                "image_generation_prompt": choose_prompt(prompt_rows, headline),
            })


def main() -> None:
    rows = get_primary_rows()[:8]
    copy_rows = load_csv(GRAPHIC_COPY_FILE)
    caption_rows = load_csv(CAPTION_BANK_FILE)
    prompt_rows = load_csv(IMAGE_PROMPTS_FILE)
    context_rows = load_csv(STORY_CONTEXT_FILE)
    ctx_by_key = context_index(context_rows)
    write_queue_md(rows, copy_rows, caption_rows, prompt_rows, ctx_by_key)
    write_top_3(rows, copy_rows, caption_rows, prompt_rows, ctx_by_key)
    write_queue_csv(rows, caption_rows, prompt_rows, ctx_by_key)
    print(f"Created {QUEUE_MD_FILE}")
    print(f"Created {TOP_3_PACKETS_FILE}")
    print(f"Created {QUEUE_CSV_FILE}")


if __name__ == "__main__":
    main()
