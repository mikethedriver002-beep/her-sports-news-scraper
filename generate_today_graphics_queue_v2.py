"""
Her Sports Daily Today Graphics Queue Generator v2 - CLEAN CONTEXT VERSION
-------------------------------------------------------------------------

Replaces the older generate_today_graphics_queue_v2.py.

Reads:
    story_context_enriched.csv plus the existing HSD output files

Creates:
    today_graphics_queue.md
    today_graphics_queue.csv
    top_3_graphic_packets.md

Core rule:
    If context is weak, say so clearly. Do not turn weak context into generic fake slide copy.
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


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())[:140]


def safe_int(value: str, default: int = 999) -> int:
    try:
        return int(clean(value))
    except Exception:
        return default


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
        return ["- Context status: No enriched context available. Verify source before using stats."]

    bullets: List[str] = []
    confidence = clean(ctx.get("context_confidence", ""))
    manual = clean(ctx.get("manual_review_flag", ""))

    summary = clean(ctx.get("story_summary", ""))
    if summary:
        bullets.append(f"- Summary: {summary}")

    for field in ["key_fact_1", "key_fact_2", "key_fact_3"]:
        value = clean(ctx.get(field, ""))
        if value and value != summary:
            bullets.append(f"- Verified detail: {value}")

    for label, field in [
        ("Final score", "final_score"),
        ("Key number", "key_number"),
        ("Main takeaway", "main_takeaway"),
    ]:
        value = clean(ctx.get(field, ""))
        if value and value not in " ".join(bullets):
            bullets.append(f"- {label}: {value}")

    bullets.append(f"- Context confidence: {confidence or 'Unknown'}")
    bullets.append(f"- Manual review flag: {manual or 'Yes'}")
    notes = clean(ctx.get("verified_context_notes", ""))
    if notes:
        bullets.append(f"- Verification notes: {notes}")

    return bullets


def build_slides(row: Dict[str, str], ctx: Dict[str, str]) -> List[Dict[str, str]]:
    headline = clean(row.get("headline", ""))
    content_family = clean(row.get("content_family", ""))
    confidence = clean(ctx.get("context_confidence", ""))
    manual_review = clean(ctx.get("manual_review_flag", "Yes"))

    summary = clean(ctx.get("story_summary", ""))
    fact1 = clean(ctx.get("key_fact_1", ""))
    fact2 = clean(ctx.get("key_fact_2", ""))
    fact3 = clean(ctx.get("key_fact_3", ""))
    final_score = clean(ctx.get("final_score", ""))
    key_number = clean(ctx.get("key_number", ""))
    takeaway = clean(ctx.get("main_takeaway", ""))

    if not ctx or confidence == "Low":
        return [
            {"num": "1", "role": "Hook", "title": headline, "body": "The story is worth tracking, but exact stats need verification before publishing."},
            {"num": "2", "role": "Research needed", "title": "Verify before designing", "body": summary or "Open the source and confirm the specific details before creating the final graphic."},
            {"num": "3", "role": "Do not invent", "title": "Accuracy check", "body": "Do not add scores, stat lines, records, jersey numbers, or player details unless verified."},
            {"num": "4", "role": "CTA", "title": "Your take?", "body": "Follow Her Sports Daily for verified women's sports coverage."},
        ]

    if "Postgame" in content_family or "Recap" in content_family or clean(ctx.get("story_type", "")) == "Game Recap / Result":
        slide2_body = fact1 or summary
        if final_score and final_score not in slide2_body:
            slide2_body = f"{slide2_body} Final score: {final_score}."
        return [
            {"num": "1", "role": "Hook", "title": headline, "body": "The result you need to know."},
            {"num": "2", "role": "What happened", "title": "What happened", "body": slide2_body},
            {"num": "3", "role": "Why it matters", "title": "Why it matters", "body": takeaway or fact2 or fact3},
            {"num": "4", "role": "CTA", "title": "Your take?", "body": "Follow Her Sports Daily for more women's sports coverage."},
        ]

    if "Growth" in content_family or clean(ctx.get("story_type", "")) in {"Business / Growth", "League Expansion"}:
        return [
            {"num": "1", "role": "Hook", "title": headline, "body": "The growth story to know."},
            {"num": "2", "role": "The number", "title": "The number to know", "body": key_number or fact1 or summary},
            {"num": "3", "role": "Impact", "title": "Why it matters", "body": takeaway or fact2},
            {"num": "4", "role": "CTA", "title": "More growth stories?", "body": "Follow Her Sports Daily for the business of women's sports."},
        ]

    if "Milestone" in content_family or clean(ctx.get("story_type", "")) == "Record / Milestone":
        return [
            {"num": "1", "role": "Hook", "title": headline, "body": "A milestone worth putting into context."},
            {"num": "2", "role": "The milestone", "title": "The milestone", "body": key_number or fact1 or summary},
            {"num": "3", "role": "Context", "title": "Why it matters", "body": takeaway or fact2},
            {"num": "4", "role": "CTA", "title": "How big is this?", "body": "Follow Her Sports Daily for more."},
        ]

    return [
        {"num": "1", "role": "Hook", "title": headline, "body": "The story you need to know."},
        {"num": "2", "role": "Context", "title": "The context", "body": fact1 or summary},
        {"num": "3", "role": "Angle", "title": "The angle", "body": takeaway or fact2 or fact3},
        {"num": "4", "role": "CTA", "title": "Your take?", "body": "Follow Her Sports Daily for more."},
    ]


def packet_for_row(row: Dict[str, str], caption_rows: List[Dict[str, str]], prompt_rows: List[Dict[str, str]], ctx_by_key: Dict[str, Dict[str, str]]) -> str:
    headline = clean(row.get("headline", ""))
    ctx = ctx_by_key.get(key(headline), {})
    caption = choose_caption(caption_rows, headline)
    prompt = choose_prompt(prompt_rows, headline)
    slides = build_slides(row, ctx)

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

    lines.extend(context_bullets(ctx))

    lines.extend([
        "",
        "### Production accuracy rules",
        "- Do not invent stats, scores, records, jersey numbers, player teams, or uniform details.",
        "- If context confidence is Low or manual review is Yes, verify the source before final design.",
        "- If a player jersey number cannot be verified from reliable sources, do not show the number.",
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
        lines.extend([
            f"**Slide {slide['num']} - {slide['role']}:** {slide['title']}",
            slide["body"],
            "",
        ])

    lines.extend([
        "### Caption",
        caption or "Use the caption bank for this story, or write a direct caption from the verified context above.",
        "",
        "### Image prompt",
        prompt or "Use the template, verified story context, slide copy, and design direction above to create the graphic.",
        "",
        "---",
        "",
    ])

    return "\n".join(lines)


def write_queue_md(rows, caption_rows, prompt_rows, ctx_by_key) -> None:
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
        lines.append(packet_for_row(row, caption_rows, prompt_rows, ctx_by_key))

    Path(QUEUE_MD_FILE).write_text("\n".join(lines), encoding="utf-8")


def write_top_3(rows, caption_rows, prompt_rows, ctx_by_key) -> None:
    lines = [
        "# Top 3 Graphic Packets",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "These are the first three graphics to make today.",
        "",
    ]

    for row in rows[:3]:
        lines.append(packet_for_row(row, caption_rows, prompt_rows, ctx_by_key))

    Path(TOP_3_PACKETS_FILE).write_text("\n".join(lines), encoding="utf-8")


def write_queue_csv(rows, caption_rows, prompt_rows, ctx_by_key) -> None:
    fieldnames = [
        "post_sequence", "headline", "action", "editorial_decision", "content_family",
        "template_name", "asset_shape", "timing", "context_confidence", "manual_review_flag",
        "story_summary", "key_fact_1", "key_fact_2", "key_fact_3", "final_score",
        "key_number", "main_takeaway", "caption", "image_generation_prompt",
    ]

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
                "manual_review_flag": clean(ctx.get("manual_review_flag", "")),
                "story_summary": clean(ctx.get("story_summary", "")),
                "key_fact_1": clean(ctx.get("key_fact_1", "")),
                "key_fact_2": clean(ctx.get("key_fact_2", "")),
                "key_fact_3": clean(ctx.get("key_fact_3", "")),
                "final_score": clean(ctx.get("final_score", "")),
                "key_number": clean(ctx.get("key_number", "")),
                "main_takeaway": clean(ctx.get("main_takeaway", "")),
                "caption": choose_caption(caption_rows, headline),
                "image_generation_prompt": choose_prompt(prompt_rows, headline),
            })


def main() -> None:
    rows = get_primary_rows()[:8]
    caption_rows = load_csv(CAPTION_BANK_FILE)
    prompt_rows = load_csv(IMAGE_PROMPTS_FILE)
    ctx_by_key = context_index(load_csv(STORY_CONTEXT_FILE))

    write_queue_md(rows, caption_rows, prompt_rows, ctx_by_key)
    write_top_3(rows, caption_rows, prompt_rows, ctx_by_key)
    write_queue_csv(rows, caption_rows, prompt_rows, ctx_by_key)

    print(f"Created {QUEUE_MD_FILE}")
    print(f"Created {TOP_3_PACKETS_FILE}")
    print(f"Created {QUEUE_CSV_FILE}")


if __name__ == "__main__":
    main()
