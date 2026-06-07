from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


VERSION = "hsd-studio-bridge-v1"

INPUT_NEWS_FACT_PACKETS = os.environ.get("HSD_NEWS_FACT_PACKETS", "news_fact_packets.csv")
INPUT_NEWS_DAILY_PLAN = os.environ.get("HSD_NEWS_DAILY_PLAN", "news_daily_plan.md")
INPUT_NEWS_BRIEF_QUEUE = os.environ.get("HSD_NEWS_BRIEF_QUEUE", "news_brief_queue.md")
INPUT_NEWS_GRAPHICS_HANDOFF = os.environ.get("HSD_NEWS_GRAPHICS_HANDOFF", "news_graphics_handoff.md")
INPUT_NEWS_SOCIAL_PACKETS = os.environ.get("HSD_NEWS_SOCIAL_PACKETS", "news_social_packets.md")
INPUT_NEWS_HUB = os.environ.get("HSD_NEWS_HUB", "news_sync_hub.md")
INPUT_RESULTS_GRAPHICS_QUEUE = os.environ.get("HSD_RESULTS_GRAPHICS_QUEUE", "results_graphics_queue.md")
INPUT_RESULTS_HUB = os.environ.get("HSD_RESULTS_HUB", "results_system_hub.md")
INPUT_STUDIO_BRAND_CONFIG = os.environ.get("HSD_STUDIO_BRAND_CONFIG", "studio_brand_config.json")
INPUT_STUDIO_SOP = os.environ.get("HSD_STUDIO_SOP", "studio_graphics_sop.json")

MAX_TOP_PACKETS = int(os.environ.get("HSD_STUDIO_MAX_TOP_PACKETS", "6"))
MAX_QUEUE_ITEMS = int(os.environ.get("HSD_STUDIO_MAX_QUEUE_ITEMS", "14"))

OUT_COMMAND_CENTER = "studio_command_center.md"
OUT_GRAPHICS_QUEUE_CSV = "studio_graphics_queue.csv"
OUT_TOP_PACKETS = "studio_top_graphic_packets.md"
OUT_IMAGE_PROMPTS = "studio_image_prompts.md"
OUT_CAPTION_BANK = "studio_caption_bank.md"
OUT_ACCURACY_CHECKLIST_CSV = "studio_accuracy_checklist.csv"
OUT_MANUAL_REVIEW_CSV = "studio_manual_review_graphics.csv"
OUT_POST_SCHEDULE = "studio_post_schedule.md"
OUT_BRAND_CONFIG = "studio_brand_config.json"
OUT_SOP = "studio_graphics_sop.json"
OUT_MANIFEST = "studio_manifest.json"
OUT_WATERMARK_SVG = "brand_assets/hsd_watermark_bug.svg"

QUEUE_FIELDS = [
    "studio_rank", "production_bucket", "asset_type", "asset_shape", "content_family",
    "template", "sport", "league", "source_queue", "headline", "final_score",
    "angle", "context_quality", "quality_score", "manual_review",
    "production_ready", "graphics_safety_mode", "watermark_rule",
    "slide_count", "caption_seed", "graphic_prompt", "accuracy_lock",
    "source_urls_json", "packet_id",
]

CHECKLIST_FIELDS = [
    "packet_id", "headline", "check_type", "status", "instruction",
]

MANUAL_FIELDS = QUEUE_FIELDS + ["review_reason"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def norm(value: Any) -> str:
    return clean(value).lower()


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def load_text(path: str) -> str:
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    latest_paths = [
        Path("news_run_history") / "latest" / path,
        Path("results_run_history") / "latest" / path,
    ]
    for candidate in latest_paths:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="replace")
    return ""


def load_csv(path: str) -> List[Dict[str, str]]:
    candidates = [
        Path(path),
        Path("news_run_history") / "latest" / path,
        Path("results_run_history") / "latest" / path,
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            with p.open(newline="", encoding="utf-8", errors="replace") as f:
                return list(csv.DictReader(f))
    return []


def load_json(path: str, default: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                out[field] = value
            writer.writerow(out)


def default_brand_config() -> Dict[str, Any]:
    return {
        "brand_name": "Her Sports Daily",
        "locked_watermark": {
            "file": OUT_WATERMARK_SVG,
            "rule": "Use one consistent compact stacked square HER SPORTS DAILY logo bug in the top-left unless a player face or scoreboard safe zone requires a small top-right shift.",
            "safe_zone": "48 px minimum margin on 1080x1350. Never stretch, recolor, rotate, or regenerate differently."
        },
        "colors": {
            "dark_night": "#0F1020",
            "deep_panel": "#181A2F",
            "neon_pink": "#FF4FD8",
            "electric_cyan": "#7CF7FF",
            "off_white": "#F8F4FF",
            "muted_lavender": "#C5BDD9"
        },
        "fonts": {
            "headline": "Anton or bold condensed sans fallback",
            "body": "Inter or clean geometric sans fallback",
            "score": "Anton or bold condensed sans fallback",
            "note": "No font files are included or redistributed."
        },
        "layout": {
            "primary_feed_size": "1080x1350",
            "story_size": "1080x1920",
            "safe_margin_px": 72,
            "carousel_end_slide_required": True,
            "visual_style": "bold women’s sports editorial, dark neon system, oversized score/type hierarchy, clean source-safe context panels"
        }
    }


def default_sop() -> Dict[str, Any]:
    return {
        "version": VERSION,
        "non_negotiables": [
            "Never fabricate jersey numbers, player teams, uniforms, logos, quotes, injuries, rankings, or milestones.",
            "Never swap team sides, logos, scores, or winners. Scoreboard rows must be validated against the final_score field.",
            "Use the locked HSD watermark bug every time. Do not regenerate a different watermark.",
            "If player identity, team, jersey number, or image rights are not verified, use text-forward graphics, silhouettes, generic court/field textures, or supplied approved reference images.",
            "Every carousel must include a branded end slide.",
            "Results Desk remains score source of truth. News Sync remains context source of truth."
        ],
        "asset_modes": {
            "safe_text_forward": "Use typography, verified score, abstract sport texture, team names, and HSD brand system. No player jersey renderings.",
            "verified_player_context": "Only use player imagery when user supplies/approves reference images or source-safe assets. Do not invent jersey numbers.",
            "roundup": "Use multi-result cards with verified scores and minimal context. No fake action scenes."
        },
        "watermark": "Compact stacked square HER SPORTS DAILY logo bug. Top-left by default.",
        "required_checks": [
            "Winner/check final score pairing",
            "Loser/check final score pairing",
            "Player stat lock",
            "Watermark present and consistent",
            "No invented jersey numbers",
            "No fake logos unless official assets supplied",
            "Carousel end slide included"
        ]
    }


def ensure_brand_files(brand: Dict[str, Any], sop: Dict[str, Any]) -> None:
    Path("brand_assets").mkdir(exist_ok=True)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="Her Sports Daily logo bug">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="{brand["colors"]["neon_pink"]}"/>
      <stop offset="1" stop-color="{brand["colors"]["electric_cyan"]}"/>
    </linearGradient>
  </defs>
  <rect x="18" y="18" width="476" height="476" rx="82" fill="{brand["colors"]["dark_night"]}" stroke="url(#g)" stroke-width="18"/>
  <rect x="48" y="48" width="416" height="416" rx="58" fill="{brand["colors"]["deep_panel"]}" opacity="0.96"/>
  <text x="256" y="175" text-anchor="middle" font-family="Arial Black, Impact, sans-serif" font-size="78" font-weight="900" fill="{brand["colors"]["off_white"]}" letter-spacing="-2">HER</text>
  <text x="256" y="270" text-anchor="middle" font-family="Arial Black, Impact, sans-serif" font-size="70" font-weight="900" fill="{brand["colors"]["neon_pink"]}" letter-spacing="-2">SPORTS</text>
  <text x="256" y="360" text-anchor="middle" font-family="Arial Black, Impact, sans-serif" font-size="70" font-weight="900" fill="{brand["colors"]["electric_cyan"]}" letter-spacing="-2">DAILY</text>
</svg>
"""
    Path(OUT_WATERMARK_SVG).write_text(svg, encoding="utf-8")
    Path(OUT_BRAND_CONFIG).write_text(json.dumps(brand, indent=2), encoding="utf-8")
    Path(OUT_SOP).write_text(json.dumps(sop, indent=2), encoding="utf-8")


def parse_source_urls(packet: Dict[str, str]) -> List[str]:
    raw = packet.get("source_urls_json", "")
    try:
        data = json.loads(raw) if raw else []
        if isinstance(data, list):
            return [clean(x) for x in data if clean(x)]
    except Exception:
        pass
    return []


def source_queue(packet: Dict[str, str]) -> str:
    return clean(packet.get("queue_section")) or clean(packet.get("urgency"))


def is_wnba(packet: Dict[str, str]) -> bool:
    return norm(packet.get("content_family")) == "tonight in the w" or "wnba" in norm(packet.get("league"))


def is_soccer(packet: Dict[str, str]) -> bool:
    return norm(packet.get("sport")) == "soccer"


def is_volleyball(packet: Dict[str, str]) -> bool:
    return norm(packet.get("sport")) == "volleyball"


def packet_angle(packet: Dict[str, str]) -> str:
    story = clean(packet.get("story_text"))
    m = re.search(r"Angle:\s*(.+)$", story, re.I | re.M)
    if m:
        return clean(m.group(1))
    return clean(packet.get("context_signal"))


def packet_final_score(packet: Dict[str, str]) -> str:
    story = clean(packet.get("story_text"))
    m = re.search(r"Verified final:\s*(.+?)(?:\s+Angle:|$)", story, re.I)
    if m:
        return clean(m.group(1))
    hard = clean(packet.get("caption_hard_fact"))
    m = re.search(r"Verified final:\s*(.+)$", hard, re.I)
    if m:
        return clean(m.group(1)).rstrip(".")
    return ""


def graphics_safety_mode(packet: Dict[str, str]) -> str:
    if is_wnba(packet) and clean(packet.get("top_performers")):
        return "verified_stats_text_forward"
    if is_soccer(packet):
        return "score_safe_soccer_text_forward"
    if is_volleyball(packet):
        return "score_safe_volleyball_text_forward"
    return "safe_text_forward"


def asset_type_for_packet(packet: Dict[str, str], rank: int) -> Tuple[str, str, int]:
    queue = source_queue(packet).upper()
    sport = norm(packet.get("sport"))
    if queue == "MUST POST" and is_wnba(packet):
        return "4-slide carousel", "1080x1350", 4
    if queue == "MUST POST":
        return "single result card + story crop", "1080x1350 + 1080x1920", 1
    if queue == "DIVERSITY WATCH":
        return "diversity watch result card", "1080x1350", 1
    if sport == "volleyball":
        return "roundup card", "1080x1350", 1
    return "single result card", "1080x1350", 1


def production_bucket(packet: Dict[str, str], rank: int) -> str:
    queue = source_queue(packet).upper()
    if queue == "MUST POST" and rank == 1:
        return "MAKE FIRST"
    if queue == "MUST POST":
        return "MAKE NEXT"
    if queue == "DIVERSITY WATCH":
        return "DIVERSITY WATCH"
    if queue == "STRONG MAYBE":
        return "ROUNDUP BANK"
    return "HOLD / EXTRA"


def accuracy_lock(packet: Dict[str, str]) -> str:
    return (
        f"LOCKED FACTS: headline='{clean(packet.get('headline'))}'; "
        f"final_score='{packet_final_score(packet)}'; "
        f"angle='{packet_angle(packet)}'. "
        "Do not alter winner, loser, score, player stats, or source-safe context."
    )


def template_for_packet(packet: Dict[str, str]) -> str:
    if is_wnba(packet):
        if "close" in packet_angle(packet).lower():
            return "Tonight in the W: Close Finish Carousel"
        if "statement" in packet_angle(packet).lower():
            return "Tonight in the W: Statement Win Carousel"
        if "high-scoring" in packet_angle(packet).lower():
            return "Tonight in the W: High-Scoring Result Carousel"
        return "Tonight in the W: Result Carousel"
    if is_soccer(packet):
        return "Around Women's Sports: Soccer Diversity Card"
    if is_volleyball(packet):
        return "Around Women's Sports: Volleyball Roundup Card"
    return "Around Women's Sports: Result Card"


def build_graphic_prompt(packet: Dict[str, str], brand: Dict[str, Any], sop: Dict[str, Any], rank: int) -> str:
    headline = clean(packet.get("headline"))
    final_score = packet_final_score(packet)
    angle = packet_angle(packet)
    content_family = clean(packet.get("content_family"))
    top_perf = clean(packet.get("top_performers"))
    slide3 = clean(packet.get("slide3_context")) or top_perf or clean(packet.get("context_signal"))
    asset_type, asset_shape, slide_count = asset_type_for_packet(packet, rank)
    safety = graphics_safety_mode(packet)

    base_rules = (
        "Create a Her Sports Daily graphic using the locked brand system. "
        "Use dark-night background, neon pink/electric cyan accents, bold condensed headline type, clean sans body type, "
        "and the single locked compact stacked HER SPORTS DAILY watermark bug in the top-left. "
        "Do not create a new watermark. Do not invent jerseys, jersey numbers, logos, player photos, quotes, injuries, rankings, or milestones."
    )

    scoreboard_rules = (
        f"Score accuracy lock: {final_score}. Keep winner, loser, and score paired exactly as written. "
        "Before final output, visually check that no team/score/logo side is swapped."
    )

    if slide_count >= 4:
        prompt = f"""
GRAPHIC PACKET {rank}: {headline}
Asset: {asset_type}, {asset_shape}
Content family: {content_family}
Safety mode: {safety}

{base_rules}

Slide 1:
Headline: {headline}
Subhead: Verified result: {final_score}

Slide 2:
Result card: {final_score}
Use oversized scoreboard typography. Keep winner/score pairing exact.

Slide 3:
Context: {slide3}
Use only the stats/context shown here. No added stats.

Slide 4:
CTA / end slide:
Text: Your take? Follow Her Sports Daily for more women’s sports coverage.
This is the required branded carousel end slide.

{scoreboard_rules}

Watermark rule:
{brand["locked_watermark"]["rule"]}

Do not use visible jersey numbers unless the user supplies verified reference images. Use text-first composition, silhouettes, abstract court/arena textures, or supplied approved images only.
""".strip()
    else:
        prompt = f"""
GRAPHIC PACKET {rank}: {headline}
Asset: {asset_type}, {asset_shape}
Content family: {content_family}
Safety mode: {safety}

{base_rules}

Main copy:
Headline: {headline}
Verified final: {final_score}
Context line: {slide3}

Layout:
Use one bold scoreboard/result card. Prioritize readability at Instagram feed size. Add small source-safe context ribbon. Add the locked HSD watermark bug top-left.

{scoreboard_rules}

Do not use visible jersey numbers unless the user supplies verified reference images. Use text-first composition, silhouettes, abstract field/court textures, or supplied approved images only.
""".strip()

    return prompt


def build_queue(packets: List[Dict[str, str]], brand: Dict[str, Any], sop: Dict[str, Any]) -> List[Dict[str, Any]]:
    def sort_key(p: Dict[str, str]) -> Tuple[int, int, str]:
        q = source_queue(p).upper()
        if q == "MUST POST":
            priority = 0
        elif q == "STRONG MAYBE":
            priority = 1
        elif q == "DIVERSITY WATCH":
            priority = 2
        else:
            priority = 3
        try:
            score = -int(float(p.get("quality_score") or 0))
        except Exception:
            score = 0
        return (priority, score, clean(p.get("headline")))

    valid = [p for p in packets if clean(p.get("production_ready")).lower() != "no"]
    valid = sorted(valid, key=sort_key)[:MAX_QUEUE_ITEMS]

    rows: List[Dict[str, Any]] = []
    for i, p in enumerate(valid, 1):
        asset_type, asset_shape, slide_count = asset_type_for_packet(p, i)
        row = {
            "studio_rank": i,
            "production_bucket": production_bucket(p, i),
            "asset_type": asset_type,
            "asset_shape": asset_shape,
            "content_family": clean(p.get("content_family")),
            "template": template_for_packet(p),
            "sport": clean(p.get("sport")),
            "league": clean(p.get("league")),
            "source_queue": source_queue(p),
            "headline": clean(p.get("headline")),
            "final_score": packet_final_score(p),
            "angle": packet_angle(p),
            "context_quality": clean(p.get("context_quality")),
            "quality_score": clean(p.get("quality_score")),
            "manual_review": clean(p.get("manual_review")),
            "production_ready": clean(p.get("production_ready")),
            "graphics_safety_mode": graphics_safety_mode(p),
            "watermark_rule": brand["locked_watermark"]["rule"],
            "slide_count": slide_count,
            "caption_seed": clean(p.get("caption_voice") or p.get("caption_hard_fact")),
            "graphic_prompt": build_graphic_prompt(p, brand, sop, i),
            "accuracy_lock": accuracy_lock(p),
            "source_urls_json": json.dumps(parse_source_urls(p), ensure_ascii=False),
            "packet_id": stable_id(VERSION, clean(p.get("headline")), packet_final_score(p), source_queue(p)),
        }
        rows.append(row)

    return rows


def build_checklist(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    required = [
        ("score_lock", "Confirm headline winner and final score match packet exactly."),
        ("side_lock", "Confirm no team side, logo side, or score side is swapped."),
        ("watermark", "Confirm locked HSD watermark bug is top-left and consistent."),
        ("no_fake_jerseys", "Confirm there are no fabricated jersey numbers, fake uniforms, or invented player details."),
        ("context_lock", "Confirm Slide 3/context uses only packet text."),
        ("end_slide", "For carousel assets, confirm branded end slide is included."),
        ("export_size", "Confirm 1080x1350 feed export, plus 1080x1920 story crop if requested."),
    ]
    for row in rows:
        for check_type, instruction in required:
            if check_type == "end_slide" and int(row.get("slide_count") or 1) < 2:
                status = "N/A"
            else:
                status = "Required"
            checks.append({
                "packet_id": row.get("packet_id"),
                "headline": row.get("headline"),
                "check_type": check_type,
                "status": status,
                "instruction": instruction,
            })
    return checks


def build_manual_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    manual = []
    for row in rows:
        reasons = []
        if clean(row.get("manual_review")).lower() == "yes":
            reasons.append("News Sync manual_review is Yes.")
        if not clean(row.get("final_score")):
            reasons.append("Missing final score.")
        if clean(row.get("production_ready")).lower() == "no":
            reasons.append("News Sync production_ready is No.")
        if reasons:
            r = dict(row)
            r["review_reason"] = "; ".join(reasons)
            manual.append(r)
    return manual


def markdown_command_center(rows: List[Dict[str, Any]], brand: Dict[str, Any], hub_text: str) -> str:
    must = [r for r in rows if r["production_bucket"] in {"MAKE FIRST", "MAKE NEXT"}]
    roundup = [r for r in rows if r["production_bucket"] == "ROUNDUP BANK"]
    diversity = [r for r in rows if r["production_bucket"] == "DIVERSITY WATCH"]
    manual = build_manual_rows(rows)

    lines = [
        "# Her Sports Daily Studio Command Center v1",
        "",
        f"Generated: `{utc_now()}`",
        "",
        "## What this file is",
        "",
        "This is the production bridge from Results Desk + News Sync into the graphics workflow.",
        "",
        "Results Desk controls scores. News Sync controls context. Studio Bridge controls what to make, how to make it, and what must be checked before posting.",
        "",
        "## Run summary",
        "",
        f"- Studio graphics queued: {len(rows)}",
        f"- Make First / Make Next: {len(must)}",
        f"- Roundup bank: {len(roundup)}",
        f"- Diversity Watch: {len(diversity)}",
        f"- Manual review graphics: {len(manual)}",
        "",
        "## Open first",
        "",
        "1. `studio_top_graphic_packets.md`",
        "2. `studio_image_prompts.md`",
        "3. `studio_accuracy_checklist.csv`",
        "4. `studio_caption_bank.md`",
        "5. `brand_assets/hsd_watermark_bug.svg`",
        "",
        "## Production order",
        "",
    ]

    for row in rows[:MAX_TOP_PACKETS]:
        lines.extend([
            f"### {row['studio_rank']}. {row['headline']}",
            "",
            f"- Bucket: **{row['production_bucket']}**",
            f"- Asset: {row['asset_type']} ({row['asset_shape']})",
            f"- Template: {row['template']}",
            f"- Final score: {row['final_score']}",
            f"- Safety mode: {row['graphics_safety_mode']}",
            f"- Watermark: {row['watermark_rule']}",
            "",
        ])

    lines.extend([
        "## Non-negotiable production rules",
        "",
        "- Never fabricate jersey numbers, fake uniforms, logos, player teams, quotes, injuries, rankings, or milestones.",
        "- Use the locked watermark bug from `brand_assets/hsd_watermark_bug.svg` every time.",
        "- Every carousel gets a branded end slide.",
        "- Check scoreboard sides manually before posting.",
        "- If no approved player image/reference exists, use the safe text-forward prompt.",
        "",
        "## Source health from News Sync",
        "",
        "```text",
        clean(hub_text)[:2500],
        "```",
        "",
    ])

    return "\n".join(lines)


def markdown_top_packets(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Top Graphic Packets v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Paste one packet at a time into the graphics chat. The prompt already includes score locks, watermark rules, and no-fabrication rules.",
        "",
    ]

    for row in rows[:MAX_TOP_PACKETS]:
        lines.extend([
            f"## GRAPHIC {row['studio_rank']}: {row['headline']}",
            "",
            f"**Bucket:** {row['production_bucket']}",
            f"**Asset:** {row['asset_type']}",
            f"**Shape:** {row['asset_shape']}",
            f"**Template:** {row['template']}",
            f"**Safety mode:** {row['graphics_safety_mode']}",
            "",
            "### Prompt",
            "",
            "```text",
            row["graphic_prompt"],
            "```",
            "",
            "### Accuracy lock",
            "",
            row["accuracy_lock"],
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def markdown_image_prompts(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Image Prompts v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Use these only after checking the accuracy checklist. Do not remove the no-fabrication language.",
        "",
    ]

    for row in rows:
        lines.extend([
            f"## Prompt {row['studio_rank']}: {row['headline']}",
            "",
            "```text",
            row["graphic_prompt"],
            "```",
            "",
        ])
    return "\n".join(lines)


def markdown_caption_bank(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Caption Bank v1",
        "",
        f"Generated: {utc_now()}",
        "",
    ]
    for row in rows:
        lines.extend([
            f"## {row['headline']}",
            "",
            f"**Bucket:** {row['production_bucket']}",
            "",
            f"Caption seed: {row['caption_seed']}",
            "",
            "Accuracy note: Caption must not add player stats, records, rankings, injuries, or quotes beyond the packet.",
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def markdown_post_schedule(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Studio Post Schedule v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Use this as a production order, not a rigid clock. Post timing should still consider game freshness and your actual bandwidth.",
        "",
    ]

    schedule = [
        ("ASAP", [r for r in rows if r["production_bucket"] == "MAKE FIRST"]),
        ("Next", [r for r in rows if r["production_bucket"] == "MAKE NEXT"]),
        ("Roundup window", [r for r in rows if r["production_bucket"] == "ROUNDUP BANK"]),
        ("Diversity / soccer radar", [r for r in rows if r["production_bucket"] == "DIVERSITY WATCH"]),
    ]

    for label, group in schedule:
        lines.append(f"## {label}")
        if not group:
            lines.append("")
            lines.append("No items.")
            lines.append("")
            continue
        for r in group:
            lines.append(f"- **{r['headline']}** | {r['asset_type']} | {r['template']}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    brand = default_brand_config()
    user_brand = load_json(INPUT_STUDIO_BRAND_CONFIG, {})
    if isinstance(user_brand, dict) and user_brand:
        for k, v in user_brand.items():
            if isinstance(v, dict) and isinstance(brand.get(k), dict):
                brand[k].update(v)
            else:
                brand[k] = v

    sop = default_sop()
    user_sop = load_json(INPUT_STUDIO_SOP, {})
    if isinstance(user_sop, dict) and user_sop:
        sop.update(user_sop)

    ensure_brand_files(brand, sop)

    packets = load_csv(INPUT_NEWS_FACT_PACKETS)
    news_hub = load_text(INPUT_NEWS_HUB)

    rows = build_queue(packets, brand, sop)
    checklist = build_checklist(rows)
    manual_rows = build_manual_rows(rows)

    write_csv(OUT_GRAPHICS_QUEUE_CSV, rows, QUEUE_FIELDS)
    write_csv(OUT_ACCURACY_CHECKLIST_CSV, checklist, CHECKLIST_FIELDS)
    write_csv(OUT_MANUAL_REVIEW_CSV, manual_rows, MANUAL_FIELDS)

    Path(OUT_COMMAND_CENTER).write_text(markdown_command_center(rows, brand, news_hub), encoding="utf-8")
    Path(OUT_TOP_PACKETS).write_text(markdown_top_packets(rows), encoding="utf-8")
    Path(OUT_IMAGE_PROMPTS).write_text(markdown_image_prompts(rows), encoding="utf-8")
    Path(OUT_CAPTION_BANK).write_text(markdown_caption_bank(rows), encoding="utf-8")
    Path(OUT_POST_SCHEDULE).write_text(markdown_post_schedule(rows), encoding="utf-8")

    manifest = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "inputs": {
            "news_fact_packets": INPUT_NEWS_FACT_PACKETS,
            "news_daily_plan": INPUT_NEWS_DAILY_PLAN,
            "news_brief_queue": INPUT_NEWS_BRIEF_QUEUE,
            "news_graphics_handoff": INPUT_NEWS_GRAPHICS_HANDOFF,
            "news_hub": INPUT_NEWS_HUB,
            "results_graphics_queue": INPUT_RESULTS_GRAPHICS_QUEUE,
            "results_hub": INPUT_RESULTS_HUB,
        },
        "outputs": [
            OUT_COMMAND_CENTER,
            OUT_GRAPHICS_QUEUE_CSV,
            OUT_TOP_PACKETS,
            OUT_IMAGE_PROMPTS,
            OUT_CAPTION_BANK,
            OUT_ACCURACY_CHECKLIST_CSV,
            OUT_MANUAL_REVIEW_CSV,
            OUT_POST_SCHEDULE,
            OUT_BRAND_CONFIG,
            OUT_SOP,
            OUT_WATERMARK_SVG,
        ],
        "counts": {
            "news_packets_read": len(packets),
            "studio_graphics_queued": len(rows),
            "manual_review_graphics": len(manual_rows),
            "checklist_rows": len(checklist),
        },
        "rules": sop.get("non_negotiables", []),
    }
    Path(OUT_MANIFEST).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Created HSD Studio Bridge outputs")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
