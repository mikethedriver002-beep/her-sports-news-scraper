from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

VERSION = "v3.3.1-mermaid-quality-brain-v2.1"
CFG_PATH = Path("config/hsd_mermaid_quality_brain_v2_1.json")

OUT_FILTERED_SCOUT = Path("multisport_scout_candidates_filtered.csv")
OUT_REJECTED_SCOUT = Path("multisport_rejected_candidates.csv")
OUT_QUALITY_GRAPH = Path("mermaid_quality_story_graph.csv")
OUT_BOARD = Path("mermaid_master_content_board_v2_1.md")
OUT_SLOTS = Path("mermaid_quality_content_slots.csv")
OUT_IG_FEED = Path("ig_feed_queue_v2_1.csv")
OUT_IG_STORY = Path("ig_story_queue_v2_1.csv")
OUT_THREADS = Path("threads_queue_v2_1.csv")
OUT_BREAKING = Path("breaking_news_queue_v2_1.csv")
OUT_RUMOR = Path("rumor_watch_queue_v2_1.csv")
OUT_DEBT = Path("player_asset_debt_v2_1.csv")
OUT_REPORT = Path("mermaid_quality_brain_report.md")
OUT_MANIFEST = Path("mermaid_quality_brain_manifest.json")
OUT_PROMPT_INDEX = Path("mermaid_quality_prompt_index.csv")
OUT_OPERATOR_NEXT = Path("operator_next_actions_v2_1.md")
PACKET_DIR = Path("mermaid_quality_compiled_packets")

SCOUT_FIELDS = [
    "story_id", "source_id", "trust_band", "sport", "league", "title", "source_url",
    "candidate_type", "priority", "verification_state", "platform_fit", "notes",
    "quality_score", "quality_status", "quality_reason"
]
GRAPH_FIELDS = [
    "story_id", "story_type", "sport", "league", "headline", "event_date", "priority",
    "verification_state", "source_state", "platform_fit", "asset_state", "source_ref",
    "notes", "quality_score", "quality_status", "quality_reason"
]
SLOT_FIELDS = [
    "slot_id", "platform", "slot_time_et", "content_type", "headline", "league",
    "priority", "story_id", "status", "asset_state", "quality_score", "copy_hook", "threads_copy",
    "ig_caption_seed", "first_comment", "notes"
]
DEBT_FIELDS = [
    "league", "team_name", "needed_for", "missing_player_options", "debt_type", "priority",
    "recommended_action", "source_signal"
]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def lower(v: Any) -> str:
    return clean(v).lower()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", lower(v)).strip("-") or "item"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: str | Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    p = Path(path)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default


def load_cfg() -> Dict[str, Any]:
    return read_json(CFG_PATH, {})


def is_team_homepage_title(title: str, cfg: Dict[str, Any]) -> bool:
    return lower(title) in {lower(t) for t in cfg.get("team_homepage_titles", [])}


def score_scout(row: Dict[str, str], cfg: Dict[str, Any]) -> Tuple[int, str, str]:
    title = clean(row.get("title"))
    title_l = lower(title)
    url = clean(row.get("source_url"))
    url_l = lower(url)
    league = clean(row.get("league"))
    source_id = clean(row.get("source_id"))
    candidate_type = lower(row.get("candidate_type"))
    reasons: List[str] = []
    score = 0

    if not title or len(title) < 12:
        return 0, "hold", "title too short or missing"

    if title_l in {lower(t) for t in cfg.get("junk_exact_titles", [])}:
        return 0, "hold", f"junk exact title: {title}"

    if is_team_homepage_title(title, cfg):
        return 0, "hold", "team homepage title, not a story"

    for term in cfg.get("junk_contains", []):
        if lower(term) in title_l:
            return 0, "hold", f"junk title contains {term}"

    if re.search(r"/(privacy|terms|tickets|shop|store|stats|standings|players?)(/|$)", url_l):
        score -= 25
        reasons.append("url path looks like nav/reference page")

    score += int(cfg.get("league_priority_bonus", {}).get(league, 5))
    reasons.append(f"league bonus {league}")

    if row.get("trust_band", "").startswith("green"):
        score += 16
        reasons.append("green source")

    if "/news/" in url_l:
        score += 24
        reasons.append("news path")

    if re.search(r"/(schedule|tournament|match|game|score|results?)(/|$)", url_l):
        score += 12
        reasons.append("schedule/result path")

    if len(title) >= 35:
        score += 12
        reasons.append("headline length ok")

    signal_hits = [kw for kw in cfg.get("story_signal_keywords", []) if lower(kw) in title_l]
    if signal_hits:
        score += min(24, 8 * len(signal_hits))
        reasons.append("story signals: " + ", ".join(signal_hits[:4]))

    # Penalize bare section labels even if they survived exact filters.
    if len(title.split()) <= 3 and not signal_hits:
        score -= 25
        reasons.append("short section-like title")

    if source_id.startswith("espn_wnba_scoreboard"):
        score += 18
        reasons.append("scoreboard event crosscheck")

    if candidate_type in {"schedule_results", "scoreboard_crosscheck"} and " at " in title_l:
        score += 18
        reasons.append("matchup/event title")

    use_min = int(cfg.get("quality_thresholds", {}).get("use_min_score", 55))
    review_min = int(cfg.get("quality_thresholds", {}).get("review_min_score", 35))
    if score >= use_min:
        status = "use"
    elif score >= review_min:
        status = "review"
    else:
        status = "hold"
    return score, status, "; ".join(reasons)


def filter_and_balance_scout(cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows = read_csv("multisport_scout_candidates.csv")
    scored: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for r in rows:
        score, status, reason = score_scout(r, cfg)
        rr = dict(r)
        rr.update({"quality_score": score, "quality_status": status, "quality_reason": reason})
        if status in {"use", "review"}:
            scored.append(rr)
        else:
            rejected.append(rr)

    # Balance by league after quality score.
    caps = cfg.get("league_caps", {})
    scored.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("league", ""), r.get("title", "")))
    kept: List[Dict[str, Any]] = []
    league_counts: Dict[str, int] = {}
    for r in scored:
        league = clean(r.get("league")) or "Unknown"
        cap = int(caps.get(league, 4))
        if league_counts.get(league, 0) >= cap:
            rr = dict(r)
            rr["quality_status"] = "hold"
            rr["quality_reason"] = clean(rr.get("quality_reason")) + "; over league cap"
            rejected.append(rr)
            continue
        kept.append(r)
        league_counts[league] = league_counts.get(league, 0) + 1

    write_csv(OUT_FILTERED_SCOUT, kept, SCOUT_FIELDS)
    write_csv(OUT_REJECTED_SCOUT, rejected, SCOUT_FIELDS)
    return kept, rejected


def graph_from_base_and_scout(filtered_scout: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    base = read_csv("mermaid_story_graph.csv")
    output: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def add(row: Dict[str, Any]) -> None:
        sid = clean(row.get("story_id")) or f"story_{len(output)+1:04d}"
        if sid in seen:
            return
        seen.add(sid)
        rr = dict(row)
        rr.setdefault("quality_score", "")
        rr.setdefault("quality_status", "use")
        rr.setdefault("quality_reason", "existing story graph source")
        output.append(rr)

    # Keep high-trust non-scout items from existing graph.
    for r in base:
        stype = lower(r.get("story_type"))
        headline = clean(r.get("headline"))
        if not headline:
            continue
        if stype == "multisport_news":
            # Replace old noisy scout entries with filtered scout below.
            continue
        score = 70
        status = "use"
        reason = "core workflow story"
        if stype in {"preview", "slate_item", "ig_story_final_scores", "result", "manual_packet", "breaking_or_rumor", "live_threads"}:
            score = 78
        rr = dict(r)
        rr.update({"quality_score": score, "quality_status": status, "quality_reason": reason})
        add(rr)

    for r in filtered_scout:
        title = clean(r.get("title"))
        rr = {
            "story_id": clean(r.get("story_id")),
            "story_type": "multisport_news",
            "sport": clean(r.get("sport")),
            "league": clean(r.get("league")),
            "headline": title,
            "event_date": "",
            "priority": clean(r.get("priority")),
            "verification_state": clean(r.get("verification_state")),
            "source_state": clean(r.get("source_id")),
            "platform_fit": clean(r.get("platform_fit")),
            "asset_state": "needs_assets",
            "source_ref": clean(r.get("source_url")),
            "notes": "Quality-filtered multi-sport scout candidate.",
            "quality_score": r.get("quality_score", ""),
            "quality_status": r.get("quality_status", ""),
            "quality_reason": r.get("quality_reason", "")
        }
        add(rr)

    output.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", ""), r.get("headline", "")))
    write_csv(OUT_QUALITY_GRAPH, output, GRAPH_FIELDS)
    return output


def bridge_player_debt() -> List[Dict[str, Any]]:
    debt = read_csv("player_asset_debt.csv")
    output: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str, str]] = set()

    def add(row: Dict[str, Any]) -> None:
        key = (clean(row.get("team_name")), clean(row.get("needed_for")), clean(row.get("debt_type")))
        if key in seen:
            return
        seen.add(key)
        output.append(row)

    for r in debt:
        add({
            "league": clean(r.get("league")) or "WNBA",
            "team_name": clean(r.get("team_name")),
            "needed_for": clean(r.get("needed_for")) or "player_graphics",
            "missing_player_options": clean(r.get("missing_player_options")) or clean(r.get("player_name")),
            "debt_type": clean(r.get("debt_type")) or "missing_exact_player_asset",
            "priority": clean(r.get("priority")) or "P2",
            "recommended_action": clean(r.get("recommended_action")) or "Add an exact approved player asset to the registry.",
            "source_signal": "existing_player_asset_debt"
        })

    for r in read_csv("tonight_preview_player_lock_v2.csv"):
        if clean(r.get("player_gate_status")).upper() == "PASS":
            continue
        team = clean(r.get("team_name"))
        if not team:
            continue
        requested = clean(r.get("requested_players")) or "at least one exact active player image for this team"
        add({
            "league": "WNBA",
            "team_name": team,
            "needed_for": "preview_player_graphics",
            "missing_player_options": requested,
            "debt_type": "missing_exact_player_asset_for_slate_team",
            "priority": "P1",
            "recommended_action": "Add one exact official/approved player headshot or cutout for this team before allowing player-led preview slides.",
            "source_signal": "tonight_preview_player_lock_v2_fail"
        })

    write_csv(OUT_DEBT, output, DEBT_FIELDS)
    # Also overwrite the older debt file so downstream humans see the truth.
    write_csv("player_asset_debt.csv", output, DEBT_FIELDS)
    return output


def copy_pack(row: Dict[str, Any]) -> Dict[str, str]:
    headline = clean(row.get("headline"))
    league = clean(row.get("league"))
    stype = lower(row.get("story_type"))
    if "preview" in stype or "slate" in stype:
        hook = f"{headline}: this is the matchup lane to watch tonight."
        threads = f"{headline}\n\nWhich side are you watching closest?"
        caption = f"{headline}\n\nTonight’s watch point: pace, execution, and who owns the key moments."
        first = "Which team needs this one more?"
    elif "final" in stype or "result" in stype:
        hook = f"{headline}: circle this result."
        threads = f"{headline}\n\nBiggest takeaway?"
        caption = f"{headline}\n\nA result worth putting on the board."
        first = "What was the biggest swing in this one?"
    elif "rumor" in stype or "breaking" in stype:
        hook = f"{headline}: source state matters here."
        threads = f"{headline}\n\nTracking this with source context. What are you watching?"
        caption = f"{headline}\n\nHSD note: this stays source-labeled until it is official."
        first = "Would this change the bigger picture?"
    else:
        hook = f"{league}: {headline}"
        threads = f"{headline}\n\nThis is on the HSD board. Are we underrating it?"
        caption = f"{headline}\n\nA women’s sports story to keep on the radar."
        first = "What’s the angle people are missing?"
    return {"copy_hook": hook, "threads_copy": threads, "ig_caption_seed": caption, "first_comment": first}


def choose_slots(graph: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    usable = [r for r in graph if clean(r.get("quality_status")) in {"use", "review"}]
    used_ig: Set[str] = set()

    def candidates(fn):
        return [r for r in usable if fn(r)]

    def pick(fn, allow_duplicate=False):
        rows = candidates(fn)
        rows.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", ""), r.get("headline", "")))
        for r in rows:
            if allow_duplicate or r.get("story_id") not in used_ig:
                return r
        return None

    def is_non_wnba(r):
        return clean(r.get("league")).upper() not in {"WNBA", ""} and int(r.get("quality_score") or 0) >= 55

    def is_preview(r):
        return "preview" in lower(r.get("story_type")) or "slate" in lower(r.get("story_type"))

    def is_result(r):
        st = lower(r.get("story_type"))
        return "result" in st or "final" in st

    def is_breaking(r):
        return "rumor" in lower(r.get("story_type")) or "breaking" in lower(r.get("story_type"))

    slots_spec = [
        ("threads_morning", "Threads", "9:00 AM", lambda r: is_non_wnba(r) or clean(r.get("quality_status")) == "use", True),
        ("ig_feed_noon", "IG Feed", "12:00 PM", lambda r: int(r.get("quality_score") or 0) >= 70 and not lower(r.get("headline")) in {"atlanta dream", "connecticut sun"}, False),
        ("ig_stories_rolling_1", "IG Stories", "10:30 AM", lambda r: int(r.get("quality_score") or 0) >= 60, False),
        ("ig_stories_rolling_2", "IG Stories", "12:30 PM", lambda r: int(r.get("quality_score") or 0) >= 55, False),
        ("ig_feed_evening_preview", "IG Feed", "4:45 PM", is_preview, False),
        ("threads_live", "Threads", "7:00-11:30 PM", lambda r: is_preview(r) or lower(r.get("story_type")) == "live_threads", True),
        ("nightcap", "Threads", "11:30 PM", lambda r: is_result(r) or "ig_story_final_scores" in lower(r.get("story_type")), True),
    ]

    slots: List[Dict[str, Any]] = []
    for slot_id, platform, time_et, fn, allow_dup in slots_spec:
        r = pick(fn, allow_dup)
        if r and platform != "Threads":
            used_ig.add(r.get("story_id"))
        if not r:
            slots.append({
                "slot_id": slot_id, "platform": platform, "slot_time_et": time_et,
                "content_type": "", "headline": "", "league": "", "priority": "",
                "story_id": "", "status": "skip_no_quality_story", "asset_state": "",
                "quality_score": "", "copy_hook": "", "threads_copy": "", "ig_caption_seed": "",
                "first_comment": "", "notes": "No quality-filtered story fit this slot."
            })
            continue
        copy = copy_pack(r)
        slots.append({
            "slot_id": slot_id,
            "platform": platform,
            "slot_time_et": time_et,
            "content_type": r.get("story_type"),
            "headline": r.get("headline"),
            "league": r.get("league"),
            "priority": r.get("priority"),
            "story_id": r.get("story_id"),
            "status": "ready_with_review",
            "asset_state": r.get("asset_state"),
            "quality_score": r.get("quality_score"),
            "copy_hook": copy["copy_hook"],
            "threads_copy": copy["threads_copy"],
            "ig_caption_seed": copy["ig_caption_seed"],
            "first_comment": copy["first_comment"],
            "notes": r.get("quality_reason") or r.get("notes")
        })

    write_csv(OUT_SLOTS, slots, SLOT_FIELDS)
    ig_feed = [s for s in slots if s["platform"] == "IG Feed" and s["status"] == "ready_with_review"]
    ig_story = [s for s in slots if s["platform"] == "IG Stories" and s["status"] == "ready_with_review"]
    threads = [s for s in slots if s["platform"] == "Threads" and s["status"] == "ready_with_review"]
    write_csv(OUT_IG_FEED, ig_feed, SLOT_FIELDS)
    write_csv(OUT_IG_STORY, ig_story, SLOT_FIELDS)
    write_csv(OUT_THREADS, threads, SLOT_FIELDS)
    # overwrite the v2 queues too, because these are now quality-brain routed
    write_csv("ig_feed_queue_v2.csv", ig_feed, SLOT_FIELDS)
    write_csv("ig_story_queue_v2.csv", ig_story, SLOT_FIELDS)
    write_csv("threads_queue_v2.csv", threads, SLOT_FIELDS)
    return slots


def write_breaking_and_rumor(graph: List[Dict[str, Any]]) -> None:
    breaking = []
    rumor = []
    for r in graph:
        if "rumor" not in lower(r.get("story_type")) and "breaking" not in lower(r.get("story_type")):
            continue
        rumor.append(r)
        if clean(r.get("verification_state")) in {"confirmed_official", "corroborated_report"}:
            breaking.append(r)
    fields = GRAPH_FIELDS
    write_csv(OUT_BREAKING, breaking, fields)
    write_csv(OUT_RUMOR, rumor, fields)
    write_csv("breaking_news_queue.csv", breaking, fields)
    write_csv("rumor_watch_queue.csv", rumor, fields)


def compile_quality_packets(graph: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if PACKET_DIR.exists():
        shutil.rmtree(PACKET_DIR)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)

    selected_ids = {clean(s.get("story_id")) for s in slots if clean(s.get("story_id"))}
    selected = [r for r in graph if clean(r.get("story_id")) in selected_ids]
    index: List[Dict[str, Any]] = []

    for r in selected:
        sid = clean(r.get("story_id"))
        pdir = PACKET_DIR / sid
        pdir.mkdir(parents=True, exist_ok=True)
        copy = copy_pack(r)
        content_packet = {
            "version": VERSION,
            "story": r,
            "quality": {
                "score": r.get("quality_score"),
                "status": r.get("quality_status"),
                "reason": r.get("quality_reason")
            },
            "locked_facts": {
                "headline": r.get("headline"),
                "league": r.get("league"),
                "sport": r.get("sport"),
                "event_date": r.get("event_date"),
                "verification_state": r.get("verification_state")
            }
        }
        render_plan = {
            "version": VERSION,
            "story_id": sid,
            "recommended_formats": r.get("platform_fit"),
            "asset_policy": "exact logos and exact player assets only; no generated people/logos",
            "copy_hook": copy["copy_hook"],
            "status": "ready_with_review"
        }
        prompt = f"""# HSD Quality-Brain Graphics Prompt

Story: {clean(r.get('headline'))}
League: {clean(r.get('league'))}
Type: {clean(r.get('story_type'))}
Verification: {clean(r.get('verification_state'))}

Create a premium Her Sports Daily asset with sharp editorial hierarchy and clean social-first energy.

Locked facts:
- Headline: {clean(r.get('headline'))}
- League: {clean(r.get('league'))}
- Source/ref: {clean(r.get('source_ref'))}

Display copy direction:
- {copy['copy_hook']}
- Keep public-facing language clean.
- Do not render workflow labels or internal QA language.
- Player graphics are required when appropriate, but only if exact approved player assets are present.
- Do not invent faces, jerseys, logos, stats, quotes, or results.

CTA:
- {copy['first_comment']}
"""
        (pdir / "content_packet.json").write_text(json.dumps(content_packet, indent=2), encoding="utf-8")
        (pdir / "render_plan.json").write_text(json.dumps(render_plan, indent=2), encoding="utf-8")
        (pdir / "00_GRAPHICS_PROMPT.md").write_text(prompt, encoding="utf-8")
        (pdir / "02_COPY_DESK.md").write_text(copy["ig_caption_seed"] + "\n", encoding="utf-8")
        (pdir / "03_THREADS_COPY.md").write_text(copy["threads_copy"] + "\n", encoding="utf-8")
        (pdir / "04_FIRST_COMMENT.md").write_text(copy["first_comment"] + "\n", encoding="utf-8")
        index.append({
            "story_id": sid,
            "headline": r.get("headline"),
            "league": r.get("league"),
            "story_type": r.get("story_type"),
            "quality_score": r.get("quality_score"),
            "packet_dir": pdir.as_posix(),
            "graphics_prompt": (pdir / "00_GRAPHICS_PROMPT.md").as_posix(),
            "copy_desk": (pdir / "02_COPY_DESK.md").as_posix(),
            "threads_copy": (pdir / "03_THREADS_COPY.md").as_posix(),
            "first_comment": (pdir / "04_FIRST_COMMENT.md").as_posix()
        })
    write_csv(OUT_PROMPT_INDEX, index, ["story_id", "headline", "league", "story_type", "quality_score", "packet_dir", "graphics_prompt", "copy_desk", "threads_copy", "first_comment"])
    return index


def write_board(slots: List[Dict[str, Any]], graph: List[Dict[str, Any]], filtered: List[Dict[str, Any]], rejected: List[Dict[str, Any]], debt: List[Dict[str, Any]], packets: List[Dict[str, Any]]) -> None:
    by_league: Dict[str, int] = {}
    for r in graph:
        by_league[clean(r.get("league")) or "Unknown"] = by_league.get(clean(r.get("league")) or "Unknown", 0) + 1

    lines = [
        "# HSD Mermaid Master Content Board v2.1",
        "",
        f"Generated: {now_iso()}",
        f"Version: {VERSION}",
        "",
        "## Quality Brain Status",
        "",
        f"- quality story atoms: {len(graph)}",
        f"- filtered multi-sport candidates: {len(filtered)}",
        f"- rejected/junk candidates: {len(rejected)}",
        f"- content slots: {len(slots)}",
        f"- quality packets: {len(packets)}",
        f"- player asset debt rows: {len(debt)}",
        "",
        "## League mix",
        ""
    ]
    lines += [f"- {k}: {v}" for k, v in sorted(by_league.items())]
    lines += ["", "## Today’s quality-routed slots", ""]
    for s in slots:
        lines += [
            f"### {s['slot_id']} — {s['platform']} / {s['slot_time_et']}",
            f"- Status: {s['status']}",
            f"- Headline: {s['headline'] or '—'}",
            f"- League: {s['league'] or '—'}",
            f"- Type: {s['content_type'] or '—'}",
            f"- Quality score: {s['quality_score'] or '—'}",
            f"- Copy hook: {s['copy_hook'] or '—'}",
            f"- First comment: {s['first_comment'] or '—'}",
            ""
        ]
    OUT_BOARD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(filtered, rejected, graph, slots, debt, packets) -> None:
    lines = [
        "# Mermaid Quality Brain v2.1 Report",
        "",
        f"Generated: {now_iso()}",
        f"Version: {VERSION}",
        "",
        "## Verdict",
        "",
        "Quality Brain ran. This pass filters scout junk, balances sports, bridges player asset debt, rebuilds content slots, and creates HSD-style quality packets.",
        "",
        "## Counts",
        "",
        f"- filtered multi-sport candidates: {len(filtered)}",
        f"- rejected scout candidates: {len(rejected)}",
        f"- quality story graph rows: {len(graph)}",
        f"- quality content slots: {len(slots)}",
        f"- player asset debt rows: {len(debt)}",
        f"- quality compiled packets: {len(packets)}",
        "",
        "## Top filtered candidates",
        ""
    ]
    for r in filtered[:20]:
        lines.append(f"- {r.get('quality_score')} / {r.get('quality_status')} / **{r.get('league')}** — {r.get('title')}")
    lines += ["", "## Rejected examples", ""]
    for r in rejected[:20]:
        lines.append(f"- {r.get('quality_score')} / {r.get('quality_reason')} — {r.get('title')}")
    lines += ["", "## Player asset debt", ""]
    if debt:
        for d in debt:
            lines.append(f"- **{d.get('team_name')}**: {d.get('debt_type')} — {d.get('recommended_action')}")
    else:
        lines.append("- No player asset debt rows found.")
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_operator_next(slots, debt, filtered, rejected) -> None:
    lines = [
        "# Operator Next Actions v2.1",
        "",
        f"Generated: {now_iso()}",
        "",
        "## Do first",
        "",
    ]
    if debt:
        lines.append("1. Fill player asset debt before forcing player-led preview graphics.")
    else:
        lines.append("1. Player asset debt is clear for this run.")
    lines.append("2. Review quality-routed queues, not the old raw v2 queues.")
    lines.append("3. Use `mermaid_quality_compiled_packets/` for copy/prompt handoff.")
    lines += ["", "## Ready queues", ""]
    for s in slots:
        if s.get("status") == "ready_with_review":
            lines.append(f"- {s.get('platform')} / {s.get('slot_time_et')}: {s.get('headline')}")
    OUT_OPERATOR_NEXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    cfg = load_cfg()
    filtered, rejected = filter_and_balance_scout(cfg)
    debt = bridge_player_debt()
    graph = graph_from_base_and_scout(filtered, cfg)
    write_breaking_and_rumor(graph)
    slots = choose_slots(graph)
    packets = compile_quality_packets(graph, slots)
    write_board(slots, graph, filtered, rejected, debt, packets)
    write_report(filtered, rejected, graph, slots, debt, packets)
    write_operator_next(slots, debt, filtered, rejected)

    manifest = {
        "version": VERSION,
        "generated_at": now_iso(),
        "filtered_multisport_candidates": len(filtered),
        "rejected_scout_candidates": len(rejected),
        "quality_story_graph_rows": len(graph),
        "quality_content_slots": len(slots),
        "player_asset_debt_rows": len(debt),
        "quality_packets": len(packets),
        "outputs": [
            str(OUT_FILTERED_SCOUT), str(OUT_REJECTED_SCOUT), str(OUT_QUALITY_GRAPH), str(OUT_BOARD),
            str(OUT_SLOTS), str(OUT_IG_FEED), str(OUT_IG_STORY), str(OUT_THREADS), str(OUT_DEBT),
            str(OUT_REPORT), str(OUT_PROMPT_INDEX), str(OUT_OPERATOR_NEXT)
        ]
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
