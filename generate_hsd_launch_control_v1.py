from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


VERSION = "hsd-launch-control-v1.1"

INPUT_BUNDLE_QUEUE = os.environ.get("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
INPUT_BUNDLE_PACKETS = os.environ.get("HSD_STUDIO_BUNDLE_PACKETS", "studio_bundle_packets.md")
INPUT_BUNDLE_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts.md")
INPUT_BUNDLE_CAPTIONS = os.environ.get("HSD_STUDIO_BUNDLE_CAPTIONS", "studio_bundle_caption_bank.md")
INPUT_STUDIO_COMMAND = os.environ.get("HSD_STUDIO_COMMAND", "studio_command_center.md")
INPUT_STUDIO_MANIFEST = os.environ.get("HSD_STUDIO_MANIFEST", "studio_manifest.json")
INPUT_STUDIO_SOP = os.environ.get("HSD_STUDIO_SOP", "studio_graphics_sop.json")
INPUT_STUDIO_BRAND = os.environ.get("HSD_STUDIO_BRAND", "studio_brand_config.json")

OUT_COMMAND_CENTER = "launch_command_center.md"
OUT_DAILY_RUNBOOK = "launch_daily_runbook.md"
OUT_GRAPHICS_CHAT_BRIEF = "launch_graphics_chat_brief.md"
OUT_PUBLISH_QUEUE = "launch_instagram_publish_queue.csv"
OUT_CAPTION_DRAFTS = "launch_caption_drafts.md"
OUT_STORY_PLAN = "launch_story_plan.md"
OUT_QUALITY_GATE = "launch_quality_gate.csv"
OUT_ACCOUNT_SETUP = "launch_account_setup_checklist.md"
OUT_CONTENT_CALENDAR = "launch_7_day_content_calendar.md"
OUT_OPERATING_SOP = "launch_operating_sop.md"
OUT_DAILY_OPERATOR_CHECKLIST = "launch_daily_operator_checklist.md"
OUT_POST_PUBLISH_TRACKER = "launch_post_publish_tracker.csv"
OUT_METRICS_INPUT = "launch_metrics_manual_input.csv"
OUT_PERFORMANCE_DASHBOARD = "launch_7_day_performance_dashboard.md"
OUT_DOUBLE_DOWN_REPORT = "launch_what_to_double_down_on.md"
OUT_PILLAR_BALANCE = "launch_content_pillar_balance.csv"
OUT_GROWTH_EXPERIMENT_LOG = "launch_growth_experiment_log.csv"
OUT_DASHBOARD = "launch_dashboard/index.html"
OUT_ANALYTICS_DASHBOARD = "launch_analytics_dashboard/index.html"
OUT_MANIFEST = "launch_manifest.json"

PUBLISH_FIELDS = [
    "publish_rank", "post_status", "priority", "bundle_name", "bundle_type",
    "post_format", "asset_shape", "slide_count", "recommended_window",
    "source_items_count", "caption_seed", "caption_draft", "primary_prompt_source",
    "graphics_file_naming", "publish_decision", "notes"
]

QUALITY_FIELDS = [
    "bundle_id", "bundle_name", "check_order", "check_type", "status", "instruction"
]

POST_TRACKER_FIELDS = [
    "post_id", "bundle_name", "content_pillar", "post_format", "asset_file_stem",
    "publish_status", "planned_window", "actual_publish_date", "actual_publish_time_local",
    "graphics_done", "quality_gate_done", "caption_done", "posted_to_feed",
    "posted_to_story", "metrics_logged_24h", "metrics_logged_7d", "notes"
]

METRICS_FIELDS = [
    "post_id", "post_date", "bundle_name", "content_pillar", "post_format",
    "publish_time_local", "reach", "impressions", "accounts_engaged", "likes",
    "comments", "saves", "shares", "follows", "profile_visits",
    "caption_hook", "creative_notes", "source_run", "notes"
]

PILLAR_FIELDS = [
    "content_pillar", "target_share_pct", "planned_posts_7d", "published_posts_7d",
    "avg_score", "avg_save_rate", "avg_share_rate", "recommendation"
]

EXPERIMENT_FIELDS = [
    "experiment_id", "start_date", "end_date", "status", "hypothesis",
    "content_pillar", "variable", "control", "variant", "metric_to_watch",
    "result", "decision", "notes"
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def find_input(path: str) -> Path:
    candidates = [
        Path(path),
        Path("studio_run_history") / "latest" / path,
        Path("news_run_history") / "latest" / path,
    ]
    for p in candidates:
        if p.exists():
            return p
    return Path(path)


def load_text(path: str) -> str:
    p = find_input(path)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""


def load_csv(path: str) -> List[Dict[str, str]]:
    p = find_input(path)
    if p.exists() and p.is_file():
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    return []


def load_json(path: str) -> Dict[str, Any]:
    p = find_input(path)
    if p.exists() and p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def recommended_window(priority: str, rank: int) -> str:
    p = clean(priority).upper()
    if "POST FIRST" in p:
        return "ASAP after graphics QA"
    if "POST NEXT" in p:
        return "Next available WNBA slot, usually 1 to 3 hours after lead post"
    if "ROUNDUP" in p:
        return "Roundup window, later same day or next morning"
    if "DIVERSITY" in p:
        return "Diversity slot, story-first or feed slot when audience is active"
    return "Use editor judgment"


def publish_decision(priority: str) -> str:
    p = clean(priority).upper()
    if "POST FIRST" in p:
        return "Make and post"
    if "POST NEXT" in p:
        return "Make if WNBA slate has room"
    if "ROUNDUP" in p:
        return "Make as roundup"
    if "DIVERSITY" in p:
        return "Make as diversity/soccer radar"
    return "Review"


def post_format(bundle: Dict[str, str]) -> str:
    slides = clean(bundle.get("slide_count"))
    if slides and slides != "1":
        return f"{slides}-slide carousel"
    return clean(bundle.get("asset_type")) or "carousel"


def file_stub(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", clean(name).lower()).strip("_")
    return s[:60] or "hsd_post"


def make_caption(bundle: Dict[str, str]) -> str:
    seed = clean(bundle.get("caption_seed"))
    name = clean(bundle.get("bundle_name"))
    btype = clean(bundle.get("bundle_type")).lower()

    if "main_wnba" in btype:
        opener = seed
        closer = "This is the kind of result that belongs on the radar."
    elif "wnba" in btype:
        opener = seed
        closer = "The W had a full slate, so we bundled the results worth knowing."
    elif "volleyball" in btype:
        opener = seed
        closer = "Around Women’s Sports means keeping up with the results outside the biggest headlines too."
    elif "soccer" in btype:
        opener = seed
        closer = "Women’s soccer radar stays on."
    else:
        opener = seed or name
        closer = "Follow Her Sports Daily for more women’s sports coverage."

    hashtags = "#WomensSports #HerSportsDaily #WNBA #WomensSoccer #Volleyball"
    if "volleyball" in btype:
        hashtags = "#WomensSports #HerSportsDaily #Volleyball #WomenInSports #SportsNews"
    if "soccer" in btype:
        hashtags = "#WomensSports #HerSportsDaily #WomensSoccer #WomenInSports #SportsNews"
    if "wnba" in btype:
        hashtags = "#WomensSports #HerSportsDaily #WNBA #WomenInSports #SportsNews"

    return f"{opener}\n\n{closer}\n\n{hashtags}"


def build_publish_queue(bundles: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for i, b in enumerate(bundles, 1):
        name = clean(b.get("bundle_name"))
        priority = clean(b.get("production_priority"))
        rows.append({
            "publish_rank": i,
            "post_status": "Ready for graphics",
            "priority": priority,
            "bundle_name": name,
            "bundle_type": clean(b.get("bundle_type")),
            "post_format": post_format(b),
            "asset_shape": clean(b.get("asset_shape")),
            "slide_count": clean(b.get("slide_count")),
            "recommended_window": recommended_window(priority, i),
            "source_items_count": clean(b.get("source_items_count")),
            "caption_seed": clean(b.get("caption_seed")),
            "caption_draft": make_caption(b),
            "primary_prompt_source": "studio_bundle_packets.md",
            "graphics_file_naming": f"{i:02d}_{file_stub(name)}_1080x1350",
            "publish_decision": publish_decision(priority),
            "notes": "Bundle-first. Do not duplicate with individual backup graphics unless intentionally making an extra post.",
        })
    return rows


def build_quality_gate(bundles: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    checks = [
        ("bundle_prompt", "Use the prompt from studio_bundle_packets.md, not the individual backup prompt."),
        ("score_lock", "Every winner, loser, and score must match the bundle accuracy lock exactly."),
        ("side_lock", "No team side, score side, scoreboard order, or logo side may be swapped."),
        ("watermark", "Locked HSD watermark bug must appear consistently, top-left unless safe-zone conflict."),
        ("no_fake_assets", "No fake jerseys, fake uniforms, fake logos, fake player images, or invented numbers."),
        ("context_lock", "Do not add stats, quotes, rankings, injuries, or milestones beyond the bundle."),
        ("end_slide", "Carousel must include the required branded CTA/end slide."),
        ("export", "Export feed graphic at 1080x1350. Make story crop only when needed."),
        ("caption", "Caption must not add unsupported claims."),
    ]
    rows = []
    for b in bundles:
        bid = clean(b.get("bundle_id")) or stable_id(b.get("bundle_name"), b.get("source_headlines"))
        for idx, (ctype, instruction) in enumerate(checks, 1):
            rows.append({
                "bundle_id": bid,
                "bundle_name": clean(b.get("bundle_name")),
                "check_order": idx,
                "check_type": ctype,
                "status": "Required",
                "instruction": instruction,
            })
    return rows



def content_pillar_from_bundle(bundle_name: str, bundle_type: str) -> str:
    blob = f"{bundle_name} {bundle_type}".lower()
    if "main_wnba" in blob or "main wnba" in blob:
        return "WNBA Lead"
    if "wnba" in blob or "tonight in the w" in blob:
        return "WNBA Roundup"
    if "volleyball" in blob:
        return "Volleyball"
    if "soccer" in blob:
        return "Women's Soccer"
    return "Around Women's Sports"


def numeric(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        value = str(value).replace(",", "").strip()
        if not value:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def metric_score(row: Dict[str, str]) -> float:
    return (
        numeric(row.get("likes"))
        + numeric(row.get("comments")) * 2
        + numeric(row.get("saves")) * 4
        + numeric(row.get("shares")) * 5
        + numeric(row.get("follows")) * 6
    )


def rate(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def read_existing_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def build_post_publish_tracker(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = {clean(r.get("post_id")): r for r in read_existing_csv(OUT_POST_PUBLISH_TRACKER) if clean(r.get("post_id"))}
    rows: List[Dict[str, Any]] = []

    for q in queue:
        post_id = clean(q.get("graphics_file_naming")) or stable_id(q.get("bundle_name"), q.get("priority"))
        previous = existing.get(post_id, {})
        pillar = content_pillar_from_bundle(q.get("bundle_name", ""), q.get("bundle_type", ""))

        row = {
            "post_id": post_id,
            "bundle_name": q.get("bundle_name", ""),
            "content_pillar": pillar,
            "post_format": q.get("post_format", ""),
            "asset_file_stem": q.get("graphics_file_naming", ""),
            "publish_status": previous.get("publish_status", "Planned"),
            "planned_window": q.get("recommended_window", ""),
            "actual_publish_date": previous.get("actual_publish_date", ""),
            "actual_publish_time_local": previous.get("actual_publish_time_local", ""),
            "graphics_done": previous.get("graphics_done", "No"),
            "quality_gate_done": previous.get("quality_gate_done", "No"),
            "caption_done": previous.get("caption_done", "No"),
            "posted_to_feed": previous.get("posted_to_feed", "No"),
            "posted_to_story": previous.get("posted_to_story", "No"),
            "metrics_logged_24h": previous.get("metrics_logged_24h", "No"),
            "metrics_logged_7d": previous.get("metrics_logged_7d", "No"),
            "notes": previous.get("notes", ""),
        }
        rows.append(row)

    # Preserve older posts that are no longer in today's queue.
    current_ids = {r["post_id"] for r in rows}
    for post_id, previous in existing.items():
        if post_id not in current_ids:
            rows.append(previous)

    return rows


def build_metrics_input(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = {clean(r.get("post_id")): r for r in read_existing_csv(OUT_METRICS_INPUT) if clean(r.get("post_id"))}
    rows: List[Dict[str, Any]] = []

    for q in queue:
        post_id = clean(q.get("graphics_file_naming")) or stable_id(q.get("bundle_name"), q.get("priority"))
        previous = existing.get(post_id, {})
        pillar = content_pillar_from_bundle(q.get("bundle_name", ""), q.get("bundle_type", ""))

        row = {field: previous.get(field, "") for field in METRICS_FIELDS}
        row.update({
            "post_id": post_id,
            "bundle_name": previous.get("bundle_name", q.get("bundle_name", "")),
            "content_pillar": previous.get("content_pillar", pillar),
            "post_format": previous.get("post_format", q.get("post_format", "")),
            "caption_hook": previous.get("caption_hook", clean(q.get("caption_seed"))[:160]),
            "source_run": previous.get("source_run", VERSION),
        })
        rows.append(row)

    current_ids = {r["post_id"] for r in rows}
    for post_id, previous in existing.items():
        if post_id not in current_ids:
            rows.append(previous)

    return rows


def metrics_with_data(metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        r for r in metrics
        if numeric(r.get("reach")) or numeric(r.get("likes")) or numeric(r.get("saves")) or numeric(r.get("shares")) or numeric(r.get("follows"))
    ]


def summarize_by_pillar(metrics: List[Dict[str, Any]], queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pillars = {
        "WNBA Lead": {"target": 25},
        "WNBA Roundup": {"target": 25},
        "Volleyball": {"target": 20},
        "Women's Soccer": {"target": 20},
        "Around Women's Sports": {"target": 10},
    }

    planned_counts: Dict[str, int] = {}
    for q in queue:
        pillar = content_pillar_from_bundle(q.get("bundle_name", ""), q.get("bundle_type", ""))
        planned_counts[pillar] = planned_counts.get(pillar, 0) + 1

    published: Dict[str, List[Dict[str, Any]]] = {}
    for m in metrics_with_data(metrics):
        pillar = clean(m.get("content_pillar")) or "Around Women's Sports"
        published.setdefault(pillar, []).append(m)

    rows = []
    for pillar, cfg in pillars.items():
        data = published.get(pillar, [])
        avg_score = sum(metric_score(r) for r in data) / len(data) if data else 0.0
        avg_save_rate = sum(rate(numeric(r.get("saves")), numeric(r.get("reach"))) for r in data) / len(data) if data else 0.0
        avg_share_rate = sum(rate(numeric(r.get("shares")), numeric(r.get("reach"))) for r in data) / len(data) if data else 0.0

        if not data:
            recommendation = "Need data"
        elif avg_save_rate >= 0.01 or avg_share_rate >= 0.005:
            recommendation = "Double down"
        elif avg_score > 0:
            recommendation = "Keep testing"
        else:
            recommendation = "Rework"

        rows.append({
            "content_pillar": pillar,
            "target_share_pct": cfg["target"],
            "planned_posts_7d": planned_counts.get(pillar, 0),
            "published_posts_7d": len(data),
            "avg_score": round(avg_score, 2),
            "avg_save_rate": f"{avg_save_rate:.2%}",
            "avg_share_rate": f"{avg_share_rate:.2%}",
            "recommendation": recommendation,
        })
    return rows


def build_growth_experiment_log(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = read_existing_csv(OUT_GROWTH_EXPERIMENT_LOG)
    existing_ids = {clean(r.get("experiment_id")) for r in existing}

    seeds = [
        {
            "experiment_id": "EXP-001",
            "start_date": "",
            "end_date": "",
            "status": "Proposed",
            "hypothesis": "Bundle-first posting will create higher saves and shares than posting every result individually.",
            "content_pillar": "All",
            "variable": "Packaging",
            "control": "Individual result cards",
            "variant": "Bundle carousel",
            "metric_to_watch": "Save rate and share rate",
            "result": "",
            "decision": "",
            "notes": "Run for 7 days before deciding.",
        },
        {
            "experiment_id": "EXP-002",
            "start_date": "",
            "end_date": "",
            "status": "Proposed",
            "hypothesis": "Women’s Soccer Radar will increase reach diversity and attract non-WNBA followers.",
            "content_pillar": "Women's Soccer",
            "variable": "Content pillar",
            "control": "WNBA-only slate",
            "variant": "Soccer radar slot",
            "metric_to_watch": "Follows per reach",
            "result": "",
            "decision": "",
            "notes": "Watch comments and saves.",
        },
        {
            "experiment_id": "EXP-003",
            "start_date": "",
            "end_date": "",
            "status": "Proposed",
            "hypothesis": "Stat-forward WNBA slides will increase saves compared with score-only slides.",
            "content_pillar": "WNBA",
            "variable": "Slide 3 context",
            "control": "Score-only context",
            "variant": "Top performer stat panel",
            "metric_to_watch": "Save rate",
            "result": "",
            "decision": "",
            "notes": "Use only verified stats.",
        },
    ]

    rows = existing[:]
    for seed in seeds:
        if seed["experiment_id"] not in existing_ids:
            rows.append(seed)
    return rows


def markdown_daily_operator_checklist(queue: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Daily Account Operator Checklist v1.1",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Morning setup",
        "",
        "- Check that Results Desk, News Sync, Studio Bridge, and Launch Control all ran.",
        "- Open `launch_command_center.md`.",
        "- Confirm the bundle slate has at least one post worth making.",
        "- Check `launch_quality_gate.csv` before any post goes live.",
        "",
        "## Graphics production",
        "",
        "- Open `launch_graphics_chat_brief.md`.",
        "- Paste Bundle 1 first into the graphics chat.",
        "- Export using the file stem from `launch_instagram_publish_queue.csv`.",
        "- Do not use individual graphics if the bundle already covers the result unless it is intentional.",
        "",
        "## Posting",
        "",
    ]
    for q in queue:
        lines.append(f"- {q.get('publish_rank')}. {q.get('bundle_name')}: {q.get('publish_decision')} during `{q.get('recommended_window')}`.")
    lines.extend([
        "",
        "## After posting",
        "",
        "- Mark the post in `launch_post_publish_tracker.csv`.",
        "- Log initial notes after 15 to 60 minutes.",
        "- Enter 24-hour metrics in `launch_metrics_manual_input.csv`.",
        "- Recheck the 7-day dashboard before deciding what to double down on.",
        "",
        "## End of day",
        "",
        "- Review `launch_what_to_double_down_on.md`.",
        "- Update `launch_growth_experiment_log.csv`.",
        "- Note which pillar created the best saves, shares, follows, and comments.",
        "",
    ])
    return "\n".join(lines)


def markdown_performance_dashboard(metrics: List[Dict[str, Any]], pillar_rows: List[Dict[str, Any]]) -> str:
    data = metrics_with_data(metrics)
    lines = [
        "# Her Sports Daily 7-Day Performance Dashboard v1.1",
        "",
        f"Generated: {utc_now()}",
        "",
    ]

    if not data:
        lines.extend([
            "No performance metrics have been entered yet.",
            "",
            "Start by filling `launch_metrics_manual_input.csv` after each post has at least 24 hours of data.",
            "",
            "## Metrics to enter",
            "",
            "- Reach",
            "- Impressions",
            "- Accounts engaged",
            "- Likes",
            "- Comments",
            "- Saves",
            "- Shares",
            "- Follows",
            "- Profile visits",
            "",
        ])
    else:
        total_reach = sum(numeric(r.get("reach")) for r in data)
        total_saves = sum(numeric(r.get("saves")) for r in data)
        total_shares = sum(numeric(r.get("shares")) for r in data)
        total_follows = sum(numeric(r.get("follows")) for r in data)
        best = sorted(data, key=metric_score, reverse=True)[:5]

        lines.extend([
            "## 7-day totals",
            "",
            f"- Posts with data: {len(data)}",
            f"- Total reach: {int(total_reach):,}",
            f"- Total saves: {int(total_saves):,}",
            f"- Total shares: {int(total_shares):,}",
            f"- Total follows: {int(total_follows):,}",
            "",
            "## Top posts by weighted score",
            "",
        ])
        for r in best:
            lines.append(f"- **{r.get('bundle_name')}** | Score {metric_score(r):.1f} | Saves {r.get('saves')} | Shares {r.get('shares')} | Follows {r.get('follows')}")

    lines.extend([
        "",
        "## Pillar balance",
        "",
        "| Pillar | Target | Planned | Published | Avg Score | Avg Save Rate | Avg Share Rate | Recommendation |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ])
    for r in pillar_rows:
        lines.append(
            f"| {r['content_pillar']} | {r['target_share_pct']}% | {r['planned_posts_7d']} | {r['published_posts_7d']} | {r['avg_score']} | {r['avg_save_rate']} | {r['avg_share_rate']} | {r['recommendation']} |"
        )

    lines.append("")
    return "\n".join(lines)


def markdown_double_down_report(metrics: List[Dict[str, Any]], pillar_rows: List[Dict[str, Any]], queue: List[Dict[str, Any]]) -> str:
    data = metrics_with_data(metrics)
    lines = [
        "# Her Sports Daily What To Double Down On v1.1",
        "",
        f"Generated: {utc_now()}",
        "",
    ]

    if not data:
        lines.extend([
            "No post metrics are available yet, so this report is using the launch plan as the starting hypothesis.",
            "",
            "## Starting hypothesis",
            "",
            "1. Lead with the Main WNBA Result because it is the clearest high-intent post.",
            "2. Keep the Tonight in the W Mini-Roundup if the WNBA slate has enough depth.",
            "3. Keep Volleyball and Women’s Soccer Radar as audience-expansion slots.",
            "4. Judge the next seven days by saves, shares, follows, and comments, not likes alone.",
            "",
            "## Today's slate to test",
            "",
        ])
        for q in queue:
            lines.append(f"- **{q.get('bundle_name')}**: {q.get('publish_decision')}")
    else:
        top_pillars = [r for r in pillar_rows if r["recommendation"] == "Double down"]
        top_posts = sorted(data, key=metric_score, reverse=True)[:3]

        lines.extend([
            "## Double down",
            "",
        ])
        if top_pillars:
            for r in top_pillars:
                lines.append(f"- **{r['content_pillar']}** because avg save/share performance is strong.")
        else:
            lines.append("- No pillar has earned a clear double-down decision yet.")

        lines.extend([
            "",
            "## Top post lessons",
            "",
        ])
        for r in top_posts:
            lines.append(f"- **{r.get('bundle_name')}**: score {metric_score(r):.1f}. Notes: {r.get('notes', '')}")

    lines.extend([
        "",
        "## Decision rule",
        "",
        "- Double down on posts with high saves and shares.",
        "- Rework posts with reach but no saves or follows.",
        "- Keep testing pillars that earn comments, follows, or shares even if likes are modest.",
        "",
    ])
    return "\n".join(lines)


def make_analytics_dashboard(metrics: List[Dict[str, Any]], pillar_rows: List[Dict[str, Any]], experiments: List[Dict[str, Any]], report: str) -> str:
    def esc(value: Any) -> str:
        return html.escape(clean(value))

    data = metrics_with_data(metrics)
    total_reach = sum(numeric(r.get("reach")) for r in data)
    total_saves = sum(numeric(r.get("saves")) for r in data)
    total_shares = sum(numeric(r.get("shares")) for r in data)
    total_follows = sum(numeric(r.get("follows")) for r in data)

    pillar_cards = []
    for r in pillar_rows:
        pillar_cards.append(f"""
        <div class="card">
          <h3>{esc(r['content_pillar'])}</h3>
          <p><b>Target:</b> {esc(r['target_share_pct'])}%</p>
          <p><b>Planned:</b> {esc(r['planned_posts_7d'])} | <b>Published:</b> {esc(r['published_posts_7d'])}</p>
          <p><b>Avg score:</b> {esc(r['avg_score'])}</p>
          <p><b>Recommendation:</b> {esc(r['recommendation'])}</p>
        </div>
        """)

    exp_rows = []
    for e in experiments[:20]:
        exp_rows.append(f"<tr><td>{esc(e.get('experiment_id'))}</td><td>{esc(e.get('status'))}</td><td>{esc(e.get('hypothesis'))}</td><td>{esc(e.get('metric_to_watch'))}</td></tr>")

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HSD Analytics Loop</title>
<style>
:root {{ --bg:#0f1020; --panel:#181a2f; --text:#f8f4ff; --muted:#c5bdd9; --pink:#ff4fd8; --cyan:#7cf7ff; --border:rgba(255,255,255,.14); }}
body {{ margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text); background:radial-gradient(circle at 15% 0%, rgba(255,79,216,.18), transparent 30%), radial-gradient(circle at 85% 0%, rgba(124,247,255,.12), transparent 30%), var(--bg); }}
header {{ position:sticky; top:0; background:rgba(15,16,32,.94); border-bottom:1px solid var(--border); padding:20px; }}
main {{ max-width:1280px; margin:0 auto; padding:22px; }}
h1 {{ margin:0; font-size:clamp(28px,4vw,46px); }}
.kpis, .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }}
@media(max-width:900px) {{ .kpis, .grid {{ grid-template-columns:1fr; }} }}
.card {{ background:rgba(24,26,47,.96); border:1px solid var(--border); border-radius:18px; padding:16px; box-shadow:0 12px 32px rgba(0,0,0,.24); }}
.big {{ font-size:30px; font-weight:900; color:var(--cyan); }}
pre {{ white-space:pre-wrap; overflow:auto; background:rgba(0,0,0,.25); border:1px solid var(--border); border-radius:14px; padding:14px; }}
table {{ width:100%; border-collapse:collapse; background:rgba(24,26,47,.96); border-radius:18px; overflow:hidden; }}
td, th {{ padding:10px; border-bottom:1px solid var(--border); font-size:12px; text-align:left; color:var(--muted); }}
th {{ color:var(--text); }}
</style>
</head>
<body>
<header><h1>Her Sports Daily Analytics Loop</h1><div>Generated {esc(utc_now())}</div></header>
<main>
<section class="kpis">
<div class="card"><div>Posts with data</div><div class="big">{len(data)}</div></div>
<div class="card"><div>Total reach</div><div class="big">{int(total_reach):,}</div></div>
<div class="card"><div>Total saves</div><div class="big">{int(total_saves):,}</div></div>
<div class="card"><div>Total follows</div><div class="big">{int(total_follows):,}</div></div>
</section>
<section><h2>Pillar Balance</h2><div class="grid">{''.join(pillar_cards)}</div></section>
<section><h2>Growth Experiments</h2><table><thead><tr><th>ID</th><th>Status</th><th>Hypothesis</th><th>Metric</th></tr></thead><tbody>{''.join(exp_rows)}</tbody></table></section>
<section><h2>Double Down Report</h2><div class="card"><pre>{esc(report)}</pre></div></section>
</main>
</body>
</html>"""


def markdown_command_center(bundles: List[Dict[str, str]], queue: List[Dict[str, Any]], studio_manifest: Dict[str, Any]) -> str:
    lines = [
        "# Her Sports Daily Launch Command Center v1",
        "",
        f"Generated: `{utc_now()}`",
        "",
        "## Purpose",
        "",
        "This turns Studio Bridge Bundle Mode into the daily launch workflow. Use `studio_bundle_packets.md` as the graphics source of truth. Individual graphics remain backups only.",
        "",
        "## Launch status",
        "",
        f"- Bundle posts ready: {len(bundles)}",
        f"- Publish queue rows: {len(queue)}",
        f"- Studio source version: {studio_manifest.get('version', 'unknown')}",
        f"- Studio bundles created: {studio_manifest.get('counts', {}).get('studio_bundles_created', 'unknown')}",
        "",
        "## Open first",
        "",
        "1. `launch_graphics_chat_brief.md`",
        "2. `launch_instagram_publish_queue.csv`",
        "3. `launch_caption_drafts.md`",
        "4. `launch_quality_gate.csv`",
        "5. `launch_daily_runbook.md`",
        "",
        "## Bundle-first publishing slate",
        "",
    ]

    for row in queue:
        lines.extend([
            f"### {row['publish_rank']}. {row['bundle_name']}",
            "",
            f"- Decision: **{row['publish_decision']}**",
            f"- Priority: {row['priority']}",
            f"- Format: {row['post_format']}",
            f"- Window: {row['recommended_window']}",
            f"- File name stem: `{row['graphics_file_naming']}`",
            "",
        ])

    lines.extend([
        "## Rule",
        "",
        "Do not make every individual backup graphic after posting the bundle that already covers those results. Bundle first, backups only when useful.",
        "",
    ])
    return "\n".join(lines)


def markdown_graphics_chat_brief(bundles: List[Dict[str, str]], bundle_packets: str) -> str:
    starter = """# Graphics Chat Starter Prompt

This chat is for Her Sports Daily graphics production.

Use `studio_bundle_packets.md` as the daily graphics source of truth. Make bundle graphics first. Individual packets are backups only.

Non-negotiables:
- Follow the locked Her Sports Daily brand system.
- Use the locked watermark bug consistently.
- Never fabricate jerseys, jersey numbers, uniforms, logos, player teams, quotes, injuries, rankings, or milestones.
- Never swap team sides, winners, losers, or scores.
- Use safe text-forward graphics unless approved reference images are supplied.
- Every carousel needs the branded CTA/end slide.
- Check the bundle accuracy lock before final output.

When I paste a bundle packet, create the graphic exactly from that packet.
"""
    lines = [
        "# Her Sports Daily Launch Graphics Chat Brief v1",
        "",
        f"Generated: {utc_now()}",
        "",
        starter,
        "",
        "## Bundle packet source",
        "",
        "The following content is copied from `studio_bundle_packets.md`.",
        "",
        bundle_packets.strip() if bundle_packets.strip() else "No bundle packets found.",
        "",
    ]
    return "\n".join(lines)


def markdown_caption_drafts(queue: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Launch Caption Drafts v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Use these as first-pass captions. Do not add unsupported stats, injuries, quotes, rankings, or records.",
        "",
    ]
    for row in queue:
        lines.extend([
            f"## {row['publish_rank']}. {row['bundle_name']}",
            "",
            f"**Decision:** {row['publish_decision']}",
            f"**Window:** {row['recommended_window']}",
            "",
            "```text",
            row["caption_draft"],
            "```",
            "",
        ])
    return "\n".join(lines)


def markdown_story_plan(queue: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Launch Story Plan v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Use stories to reinforce the feed slate without duplicating every carousel slide.",
        "",
    ]
    for row in queue:
        lines.extend([
            f"## {row['bundle_name']}",
            "",
            f"- Story 1: Tease the result or roundup headline.",
            f"- Story 2: Show the strongest score/stat row from the bundle.",
            f"- Story 3: Add a poll or question sticker, then point to the feed post.",
            f"- Do not add unsupported details beyond the bundle.",
            "",
        ])
    return "\n".join(lines)


def markdown_runbook() -> str:
    return f"""# Her Sports Daily Daily Launch Runbook v1

Generated: {utc_now()}

## Daily workflow

1. Run Results Desk.
2. Run News Sync.
3. Run Studio Bridge.
4. Run Launch Control.
5. Open `launch_command_center.md`.
6. Open `launch_graphics_chat_brief.md`.
7. Make bundle graphics from `studio_bundle_packets.md`.
8. Run through `launch_quality_gate.csv`.
9. Use `launch_caption_drafts.md` for copy.
10. Publish using `launch_instagram_publish_queue.csv`.

## Production rule

Bundle-first. Individual graphics are backups only.

## Quality rule

No post goes live until the score, winner, loser, stat line, watermark, end slide, and no-fabrication checks pass.
"""


def markdown_account_setup() -> str:
    return """# Her Sports Daily Account Setup Checklist v1

## Profile

- Profile image uses the locked HSD watermark bug or approved profile mark.
- Bio clearly says women’s sports coverage.
- No website link unless one actually exists.
- Highlights prepared: WNBA, Soccer, Volleyball, Results, About.

## First pinned posts

1. About Her Sports Daily
2. Why women’s sports coverage matters
3. Best current bundle/results post

## Posting baseline

- Post bundle-first.
- Use individual graphics only when a single result deserves extra treatment.
- Keep comments open and ask simple engagement questions.
- Save all final graphics and captions in the run archive.
"""


def markdown_content_calendar(queue: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily 7-Day Launch Content Calendar v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "This is the starting cadence. Adjust based on actual results and bandwidth.",
        "",
        "## Day 1",
        "- Publish today’s Main WNBA Result.",
        "- Publish one supporting bundle if ready.",
        "- Story recap with poll.",
        "",
        "## Day 2",
        "- Publish one Around Women’s Sports roundup.",
        "- Story: what should we cover more?",
        "",
        "## Day 3",
        "- Publish WNBA mini-roundup or best available result.",
        "- Test one explainer-style caption.",
        "",
        "## Day 4",
        "- Publish women’s soccer or volleyball radar.",
        "- Start tracking which sports get saves and follows.",
        "",
        "## Day 5",
        "- Publish best result of the day.",
        "- Story Q&A or poll.",
        "",
        "## Day 6",
        "- Publish weekly results roundup.",
        "- Use comments to ask what fans missed.",
        "",
        "## Day 7",
        "- Review performance.",
        "- Keep what drove follows, saves, and shares.",
        "",
        "## Current bundle candidates",
        "",
    ]
    for row in queue:
        lines.append(f"- {row['bundle_name']}: {row['publish_decision']}")
    lines.append("")
    return "\n".join(lines)


def markdown_operating_sop() -> str:
    return """# Her Sports Daily Launch Operating SOP v1

## Source of truth hierarchy

1. Results Desk: scores and final results
2. News Sync: context and source checks
3. Studio Bridge: graphics packets and bundle mode
4. Launch Control: publishing order and captions

## Posting hierarchy

1. Bundle posts
2. Individual backup graphics
3. Stories
4. Reels or video edits

## Never do

- Do not invent stats.
- Do not use fake player images.
- Do not use fake jersey numbers.
- Do not swap score sides.
- Do not create a new watermark.
- Do not mention a website unless one exists.

## Review before every post

- Score lock
- Winner and loser lock
- Stat lock
- Watermark lock
- End slide
- Caption support
"""


def make_dashboard(queue: List[Dict[str, Any]], command: str, runbook: str) -> str:
    def esc(x: Any) -> str:
        return html.escape(clean(x))

    cards = []
    for row in queue:
        cards.append(f"""
        <div class="card">
          <div class="meta"><span>{esc(row['priority'])}</span><span>{esc(row['post_format'])}</span><span>{esc(row['recommended_window'])}</span></div>
          <h3>{esc(row['publish_rank'])}. {esc(row['bundle_name'])}</h3>
          <p><b>Decision:</b> {esc(row['publish_decision'])}</p>
          <p><b>Caption:</b> {esc(row['caption_seed'])}</p>
          <pre>{esc(row['caption_draft'])}</pre>
        </div>
        """)

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HSD Launch Control</title>
<style>
:root {{ --bg:#0f1020; --panel:#181a2f; --text:#f8f4ff; --muted:#c5bdd9; --pink:#ff4fd8; --cyan:#7cf7ff; --border:rgba(255,255,255,.14); }}
body {{ margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text); background:radial-gradient(circle at 15% 0%, rgba(255,79,216,.18), transparent 30%), radial-gradient(circle at 85% 0%, rgba(124,247,255,.12), transparent 30%), var(--bg); }}
header {{ position:sticky; top:0; background:rgba(15,16,32,.94); border-bottom:1px solid var(--border); padding:20px; }}
main {{ max-width:1280px; margin:0 auto; padding:22px; }}
h1 {{ margin:0; font-size:clamp(28px,4vw,46px); }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
@media(max-width:900px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{ background:rgba(24,26,47,.96); border:1px solid var(--border); border-radius:18px; padding:16px; box-shadow:0 12px 32px rgba(0,0,0,.24); }}
.meta {{ display:flex; gap:6px; flex-wrap:wrap; }}
.meta span {{ border:1px solid var(--border); border-radius:999px; padding:5px 8px; color:var(--muted); font-size:12px; font-weight:800; }}
pre {{ white-space:pre-wrap; overflow:auto; background:rgba(0,0,0,.25); border:1px solid var(--border); border-radius:14px; padding:14px; }}
</style>
</head>
<body>
<header><h1>Her Sports Daily Launch Control</h1><div>Generated {esc(utc_now())}</div></header>
<main>
<section><h2>Publish Queue</h2><div class="grid">{''.join(cards)}</div></section>
<section><h2>Command Center</h2><div class="card"><pre>{esc(command)}</pre></div></section>
<section><h2>Runbook</h2><div class="card"><pre>{esc(runbook)}</pre></div></section>
</main>
</body>
</html>"""


def main() -> None:
    bundles = load_csv(INPUT_BUNDLE_QUEUE)
    bundle_packets = load_text(INPUT_BUNDLE_PACKETS)
    bundle_prompts = load_text(INPUT_BUNDLE_PROMPTS)
    bundle_captions = load_text(INPUT_BUNDLE_CAPTIONS)
    studio_command = load_text(INPUT_STUDIO_COMMAND)
    studio_manifest = load_json(INPUT_STUDIO_MANIFEST)
    studio_sop = load_json(INPUT_STUDIO_SOP)
    brand = load_json(INPUT_STUDIO_BRAND)

    if not bundles:
        Path("launch_setup_error.md").write_text(
            "# Launch Control Setup Error\n\nNo bundle rows found. Run Studio Bridge Bundle Mode first.\n",
            encoding="utf-8",
        )

    publish_queue = build_publish_queue(bundles)
    quality_gate = build_quality_gate(bundles)
    post_tracker = build_post_publish_tracker(publish_queue)
    metrics_input = build_metrics_input(publish_queue)
    pillar_rows = summarize_by_pillar(metrics_input, publish_queue)
    experiments = build_growth_experiment_log(publish_queue)
    double_down_report = markdown_double_down_report(metrics_input, pillar_rows, publish_queue)

    command = markdown_command_center(bundles, publish_queue, studio_manifest)
    runbook = markdown_runbook()

    write_csv(OUT_PUBLISH_QUEUE, publish_queue, PUBLISH_FIELDS)
    write_csv(OUT_QUALITY_GATE, quality_gate, QUALITY_FIELDS)
    write_csv(OUT_POST_PUBLISH_TRACKER, post_tracker, POST_TRACKER_FIELDS)
    write_csv(OUT_METRICS_INPUT, metrics_input, METRICS_FIELDS)
    write_csv(OUT_PILLAR_BALANCE, pillar_rows, PILLAR_FIELDS)
    write_csv(OUT_GROWTH_EXPERIMENT_LOG, experiments, EXPERIMENT_FIELDS)

    Path(OUT_COMMAND_CENTER).write_text(command, encoding="utf-8")
    Path(OUT_DAILY_RUNBOOK).write_text(runbook, encoding="utf-8")
    Path(OUT_GRAPHICS_CHAT_BRIEF).write_text(markdown_graphics_chat_brief(bundles, bundle_packets), encoding="utf-8")
    Path(OUT_CAPTION_DRAFTS).write_text(markdown_caption_drafts(publish_queue), encoding="utf-8")
    Path(OUT_STORY_PLAN).write_text(markdown_story_plan(publish_queue), encoding="utf-8")
    Path(OUT_ACCOUNT_SETUP).write_text(markdown_account_setup(), encoding="utf-8")
    Path(OUT_CONTENT_CALENDAR).write_text(markdown_content_calendar(publish_queue), encoding="utf-8")
    Path(OUT_OPERATING_SOP).write_text(markdown_operating_sop(), encoding="utf-8")
    Path(OUT_DAILY_OPERATOR_CHECKLIST).write_text(markdown_daily_operator_checklist(publish_queue), encoding="utf-8")
    Path(OUT_PERFORMANCE_DASHBOARD).write_text(markdown_performance_dashboard(metrics_input, pillar_rows), encoding="utf-8")
    Path(OUT_DOUBLE_DOWN_REPORT).write_text(double_down_report, encoding="utf-8")

    Path("launch_dashboard").mkdir(exist_ok=True)
    Path(OUT_DASHBOARD).write_text(make_dashboard(publish_queue, command, runbook), encoding="utf-8")
    Path("launch_analytics_dashboard").mkdir(exist_ok=True)
    Path(OUT_ANALYTICS_DASHBOARD).write_text(make_analytics_dashboard(metrics_input, pillar_rows, experiments, double_down_report), encoding="utf-8")

    manifest = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "inputs": {
            "studio_bundle_queue": INPUT_BUNDLE_QUEUE,
            "studio_bundle_packets": INPUT_BUNDLE_PACKETS,
            "studio_command": INPUT_STUDIO_COMMAND,
            "studio_manifest": INPUT_STUDIO_MANIFEST,
        },
        "outputs": [
            OUT_COMMAND_CENTER,
            OUT_DAILY_RUNBOOK,
            OUT_GRAPHICS_CHAT_BRIEF,
            OUT_PUBLISH_QUEUE,
            OUT_CAPTION_DRAFTS,
            OUT_STORY_PLAN,
            OUT_QUALITY_GATE,
            OUT_ACCOUNT_SETUP,
            OUT_CONTENT_CALENDAR,
            OUT_OPERATING_SOP,
            OUT_DAILY_OPERATOR_CHECKLIST,
            OUT_POST_PUBLISH_TRACKER,
            OUT_METRICS_INPUT,
            OUT_PERFORMANCE_DASHBOARD,
            OUT_DOUBLE_DOWN_REPORT,
            OUT_PILLAR_BALANCE,
            OUT_GROWTH_EXPERIMENT_LOG,
            OUT_DASHBOARD,
            OUT_ANALYTICS_DASHBOARD,
        ],
        "counts": {
            "bundles_read": len(bundles),
            "publish_queue_rows": len(publish_queue),
            "quality_gate_rows": len(quality_gate),
            "post_tracker_rows": len(post_tracker),
            "metrics_input_rows": len(metrics_input),
            "pillar_balance_rows": len(pillar_rows),
            "growth_experiments": len(experiments),
            "metrics_rows_with_data": len(metrics_with_data(metrics_input)),
        },
        "source_versions": {
            "studio_manifest_version": studio_manifest.get("version", ""),
            "studio_sop_version": studio_sop.get("version", ""),
            "brand_name": brand.get("brand_name", ""),
        }
    }
    Path(OUT_MANIFEST).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Created HSD Launch Control outputs")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
