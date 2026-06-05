"""
Her Sports Daily Today Graphics Queue Generator
----------------------------------------------

This is the bridge between the automated GitHub content system and the
ChatGPT/design workflow.

Reads, when available:
    master_posting_dashboard.csv
    daily_command_file.csv
    ready_to_post_graphic_copy.csv
    caption_bank_v2.csv
    image_generation_prompts.csv
    daily_content_brief.csv

Creates:
    today_graphics_queue.md
    today_graphics_queue.csv
    top_3_graphic_packets.md

Use:
    Open today_graphics_queue.md, copy one graphic packet, and paste it into
    the graphics/design chat.
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

QUEUE_MD_FILE = "today_graphics_queue.md"
QUEUE_CSV_FILE = "today_graphics_queue.csv"
TOP_3_PACKETS_FILE = "top_3_graphic_packets.md"

BRAND_NAME = "Her Sports Daily"


def clean(value: str) -> str:
    value = value or ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_int(value: str, default: int = 999) -> int:
    try:
        return int(clean(value))
    except Exception:
        return default


def index_by_headline(rows: List[Dict[str, str]], headline_key: str = "headline") -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        key = clean(row.get(headline_key, "")).lower()
        if key:
            out.setdefault(key, []).append(row)
    return out


def choose_caption(caption_rows: List[Dict[str, str]], headline: str) -> str:
    key = clean(headline).lower()
    matches = [r for r in caption_rows if clean(r.get("headline", "")).lower() == key]
    if not matches:
        return ""
    for row in matches:
        if clean(row.get("caption_variant", "")) == "carousel":
            return clean(row.get("caption", ""))
    return clean(matches[0].get("caption", ""))


def choose_prompt(prompt_rows: List[Dict[str, str]], headline: str) -> str:
    key = clean(headline).lower()
    for row in prompt_rows:
        if clean(row.get("headline", "")).lower() == key:
            return clean(row.get("image_generation_prompt", ""))
    return ""


def slide_rows_for_headline(copy_rows: List[Dict[str, str]], headline: str) -> List[Dict[str, str]]:
    key = clean(headline).lower()
    matches = [r for r in copy_rows if clean(r.get("headline", "")).lower() == key]
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
        converted = []
        for row in dashboard_rows:
            converted.append({
                "post_sequence": row.get("posting_order", ""),
                "headline": row.get("headline", ""),
                "editorial_decision": row.get("editorial_decision", ""),
                "content_family": row.get("content_family", ""),
                "template_name": row.get("template_name", ""),
                "asset_shape": row.get("recommended_asset", ""),
                "action": row.get("post_now_or_later", ""),
                "timing": row.get("recommended_timing", ""),
                "caption_direction": "",
                "graphic_direction": row.get("why_this_is_priority", ""),
                "reason": row.get("why_this_is_priority", ""),
            })
        return converted

    if brief_rows:
        brief_rows.sort(key=lambda r: safe_int(r.get("rank", "999")))
        converted = []
        for idx, row in enumerate(brief_rows, start=1):
            converted.append({
                "post_sequence": str(idx),
                "headline": row.get("headline", ""),
                "editorial_decision": row.get("editorial_decision", ""),
                "content_family": row.get("content_bucket", ""),
                "template_name": row.get("post_format", ""),
                "asset_shape": row.get("post_format", ""),
                "action": row.get("recommended_timing", ""),
                "timing": row.get("recommended_timing", ""),
                "caption_direction": row.get("instagram_angle", ""),
                "graphic_direction": row.get("visual_brief", ""),
                "reason": row.get("decision_reason", ""),
            })
        return converted

    return []


def packet_for_row(row: Dict[str, str], copy_rows: List[Dict[str, str]], caption_rows: List[Dict[str, str]], prompt_rows: List[Dict[str, str]]) -> str:
    headline = clean(row.get("headline", ""))
    slides = slide_rows_for_headline(copy_rows, headline)
    caption = choose_caption(caption_rows, headline)
    prompt = choose_prompt(prompt_rows, headline)

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
        "### Design direction",
        clean(row.get("graphic_direction", "")) or "Use Her Sports Daily clean sports editorial styling with strong hierarchy.",
        "",
        "### Caption direction",
        clean(row.get("caption_direction", "")) or "Keep it direct, contextual, and fan-facing.",
        "",
        "### Slide copy",
        "",
    ]

    if slides:
        for slide in slides:
            title = clean(slide.get("slide_title", "")) or clean(slide.get("headline_max_70", ""))
            body = clean(slide.get("slide_body_max_120", "")) or clean(slide.get("subhead_max_110", ""))
            number = clean(slide.get("slide_number", ""))
            role = clean(slide.get("slide_role", ""))
            lines.extend([
                f"**Slide {number} - {role}:** {title}",
                body,
                "",
            ])
    else:
        lines.extend([
            "**Slide 1 - Hook:** " + headline,
            clean(row.get("graphic_direction", "")) or "The story you need to know.",
            "",
            "**Slide 2 - Context:** Why it matters",
            clean(row.get("reason", "")) or clean(row.get("caption_direction", "")),
            "",
            "**Slide 3 - Angle:** The Her Sports Daily angle",
            clean(row.get("caption_direction", "")),
            "",
            "**Slide 4 - CTA:** Your take?",
            "Comment below and follow Her Sports Daily.",
            "",
        ])

    lines.extend([
        "### Caption",
        caption or "Use the caption bank for this story, or write a direct caption from the angle above.",
        "",
        "### Image prompt",
        prompt or "Use the template, headline, slide copy, and design direction above to create the graphic.",
        "",
        "---",
        "",
    ])

    return "\n".join(lines)


def write_queue_md(rows: List[Dict[str, str]], copy_rows: List[Dict[str, str]], caption_rows: List[Dict[str, str]], prompt_rows: List[Dict[str, str]]) -> None:
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
        lines.append(packet_for_row(row, copy_rows, caption_rows, prompt_rows))

    Path(QUEUE_MD_FILE).write_text("\n".join(lines), encoding="utf-8")


def write_top_3(rows: List[Dict[str, str]], copy_rows: List[Dict[str, str]], caption_rows: List[Dict[str, str]], prompt_rows: List[Dict[str, str]]) -> None:
    top = rows[:3]
    lines = [
        "# Top 3 Graphic Packets",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "These are the first three graphics to make today.",
        "",
    ]

    for row in top:
        lines.append(packet_for_row(row, copy_rows, caption_rows, prompt_rows))

    Path(TOP_3_PACKETS_FILE).write_text("\n".join(lines), encoding="utf-8")


def write_queue_csv(rows: List[Dict[str, str]], copy_rows: List[Dict[str, str]], caption_rows: List[Dict[str, str]], prompt_rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        "post_sequence",
        "headline",
        "action",
        "editorial_decision",
        "content_family",
        "template_name",
        "asset_shape",
        "timing",
        "design_direction",
        "caption_direction",
        "caption",
        "image_generation_prompt",
    ]

    with open(QUEUE_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            headline = clean(row.get("headline", ""))
            writer.writerow({
                "post_sequence": clean(row.get("post_sequence", "")),
                "headline": headline,
                "action": clean(row.get("action", "")),
                "editorial_decision": clean(row.get("editorial_decision", "")),
                "content_family": clean(row.get("content_family", "")),
                "template_name": clean(row.get("template_name", "")),
                "asset_shape": clean(row.get("asset_shape", "")),
                "timing": clean(row.get("timing", "")),
                "design_direction": clean(row.get("graphic_direction", "")),
                "caption_direction": clean(row.get("caption_direction", "")),
                "caption": choose_caption(caption_rows, headline),
                "image_generation_prompt": choose_prompt(prompt_rows, headline),
            })


def main() -> None:
    rows = get_primary_rows()
    copy_rows = load_csv(GRAPHIC_COPY_FILE)
    caption_rows = load_csv(CAPTION_BANK_FILE)
    prompt_rows = load_csv(IMAGE_PROMPTS_FILE)

    # Keep the queue focused. The full CSV can contain everything, but the MD should not become overwhelming.
    rows = rows[:8]

    write_queue_md(rows, copy_rows, caption_rows, prompt_rows)
    write_top_3(rows, copy_rows, caption_rows, prompt_rows)
    write_queue_csv(rows, copy_rows, caption_rows, prompt_rows)

    print(f"Created {QUEUE_MD_FILE}")
    print(f"Created {TOP_3_PACKETS_FILE}")
    print(f"Created {QUEUE_CSV_FILE}")


if __name__ == "__main__":
    main()
