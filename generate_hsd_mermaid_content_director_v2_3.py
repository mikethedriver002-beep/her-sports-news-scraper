from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

VERSION = "v3.3.3-mermaid-content-director-v2.3"
CFG_PATH = Path("config/hsd_mermaid_content_director_v2_3.json")

IN_GRAPH_CANDIDATES = ["mermaid_classified_story_graph.csv", "mermaid_quality_story_graph.csv", "mermaid_story_graph.csv"]
IN_SLOTS_CANDIDATES = ["mermaid_content_slots_v2_2.csv", "mermaid_quality_content_slots.csv", "mermaid_content_slots_v2.csv"]

OUT_REPORT = Path("mermaid_content_director_report.md")
OUT_MANIFEST = Path("mermaid_content_director_manifest.json")
OUT_GRAPH = Path("mermaid_director_story_graph.csv")
OUT_SLOTS = Path("mermaid_director_content_slots.csv")
OUT_FEED = Path("ig_feed_queue_v2_3.csv")
OUT_STORY = Path("ig_story_queue_v2_3.csv")
OUT_THREADS = Path("threads_queue_v2_3.csv")
OUT_CROSSPOST = Path("content_director_crosspost_plan.csv")
OUT_REJECTED = Path("content_director_rejected_wrong_sport.csv")
OUT_FLOORS = Path("content_director_sport_floor_status.csv")
OUT_ASSETS = Path("content_director_asset_strategy.csv")
OUT_PROMPT_INDEX = Path("mermaid_director_prompt_index.csv")
OUT_OPERATOR = Path("operator_next_actions_v2_3.md")
PACKET_DIR = Path("mermaid_director_compiled_packets")

GRAPH_FIELDS = ["story_id", "story_type", "sport", "league", "headline", "event_date", "priority", "verification_state", "source_state", "platform_fit", "asset_state", "source_ref", "notes", "quality_score", "quality_status", "quality_reason", "director_status", "director_reason"]
SLOT_FIELDS = ["slot_id", "platform", "slot_time_et", "content_type", "headline", "league", "priority", "story_id", "status", "asset_state", "quality_score", "director_label", "crosspost_group", "copy_hook", "threads_copy", "ig_caption_seed", "story_frame_text", "first_comment", "notes"]
REJECT_FIELDS = ["story_id", "league", "headline", "reason", "source_ref"]
FLOOR_FIELDS = ["league", "target", "usable_count", "status", "shortfall", "notes"]
ASSET_FIELDS = ["story_id", "headline", "league", "story_type", "recommended_asset_strategy", "player_graphics_status", "logo_need", "notes"]
CROSSPOST_FIELDS = ["crosspost_group", "story_id", "headline", "platforms", "intentional", "reason"]
PROMPT_FIELDS = ["story_id", "headline", "league", "story_type", "quality_score", "packet_dir", "graphics_prompt", "copy_desk", "threads_copy", "first_comment"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def low(v: Any) -> str:
    return clean(v).lower()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", low(v)).strip("-") or "item"


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default


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
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def load_cfg() -> Dict[str, Any]:
    return read_json(CFG_PATH, {})


def first_existing_csv(paths: List[str]) -> List[Dict[str, str]]:
    for p in paths:
        rows = read_csv(p)
        if rows:
            return rows
    return []


def is_wrong_sport(row: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    league = clean(row.get("league"))
    headline = low(row.get("headline") or row.get("title"))
    filters = cfg.get("wrong_sport_filters", {}).get(league, [])
    for term in filters:
        if low(term) in headline:
            return f"wrong_sport_filter:{term}"
    # Extra NCAA sanity: softball candidates must actually say softball, WCWS, college world series, or a softball-ish result/story signal.
    if league == "NCAA Softball":
        if not any(x in headline for x in ["softball", "wcws", "college world series", "women's college world series", "women’s college world series"]):
            return "ncaa_softball_missing_softball_signal"
    return ""


def normalize_type(row: Dict[str, Any]) -> str:
    st = low(row.get("story_type") or row.get("content_type"))
    headline = low(row.get("headline"))
    src = low(row.get("source_state") or row.get("source_ref"))
    if "rumor" in st or "breaking" in st:
        return "breaking_or_rumor"
    if "ig_story_final" in st or "final" in st or "result" in st or "recap" in st:
        return "result_or_recap"
    if "preview_event" in st or "preview" in st or "slate" in st:
        return "preview_event"
    if "scoreboard" in src and (" at " in headline or " vs " in headline):
        return "preview_event"
    if " at " in headline or " vs " in headline:
        return "preview_event"
    if "official_news" in st or "news" in st:
        return "official_news_article"
    if "manual" in st:
        return "manual_packet"
    return clean(row.get("story_type") or row.get("content_type") or "official_story_review")


def build_director_graph(cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows = first_existing_csv(IN_GRAPH_CANDIDATES)
    out: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for r in rows:
        headline = clean(r.get("headline"))
        sid = clean(r.get("story_id")) or slug(headline)
        if not headline or sid in seen:
            continue
        seen.add(sid)
        reason = is_wrong_sport(r, cfg)
        if reason:
            rejected.append({"story_id": sid, "league": clean(r.get("league")), "headline": headline, "reason": reason, "source_ref": clean(r.get("source_ref"))})
            continue
        typ = normalize_type(r)
        rr = dict(r)
        rr["story_id"] = sid
        rr["story_type"] = typ
        rr["headline"] = headline
        rr["quality_score"] = clean(rr.get("quality_score")) or "60"
        rr["quality_status"] = clean(rr.get("quality_status")) or "use"
        rr["director_status"] = "usable"
        rr["director_reason"] = "passed content director filters"
        out.append(rr)
    out.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", ""), r.get("headline", "")))
    write_csv(OUT_GRAPH, out, GRAPH_FIELDS)
    write_csv(OUT_REJECTED, rejected, REJECT_FIELDS)
    return out, rejected


def floor_status(graph: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in graph:
        lg = clean(r.get("league")) or "Unknown"
        counts[lg] = counts.get(lg, 0) + 1
    rows = []
    for league, target in cfg.get("floor_targets", {}).items():
        have = counts.get(league, 0)
        short = max(0, int(target) - have)
        rows.append({"league": league, "target": target, "usable_count": have, "status": "PASS" if short == 0 else "SHORT", "shortfall": short, "notes": "Content Director does not invent stories; SHORT means source coverage or parser needs work."})
    write_csv(OUT_FLOORS, rows, FLOOR_FIELDS)
    return rows


def copy_pack(row: Dict[str, Any], platform: str = "") -> Dict[str, str]:
    headline = clean(row.get("headline"))
    league = clean(row.get("league"))
    typ = normalize_type(row)
    if typ == "preview_event":
        hook = f"{headline}: the matchup lane to watch."
        threads = f"{headline}\n\nWho needs this one more?"
        caption = f"{headline}\n\nTonight’s HSD watch point: pace, execution, and who owns the pressure moments."
        story = f"WATCH THIS: {headline}\nOne matchup. One question: who controls the game first?"
        first = "Which side are you trusting tonight?"
    elif typ == "result_or_recap":
        hook = f"{headline}: put this result on the board."
        threads = f"{headline}\n\nBiggest takeaway?"
        caption = f"{headline}\n\nThe result matters because it changes the conversation, not just the scoreboard."
        story = f"RESULT CHECK: {headline}\nWhat changed after this one?"
        first = "What was the swing moment?"
    elif typ == "official_news_article":
        if league == "LPGA":
            hook = f"The LPGA board has a real HSD storyline: {headline}."
            threads = f"{headline}\n\nLPGA storylines are getting spicy. Are we paying enough attention?"
            caption = f"{headline}\n\nThe golf lane is giving HSD more to work with than people realize."
            story = f"LPGA WATCH: {headline}\nThis is a real women’s sports storyline."
            first = "Are we underrating this LPGA moment?"
        elif league == "NWSL":
            hook = f"NWSL watch: {headline}."
            threads = f"{headline}\n\nWhat’s the NWSL angle people are missing?"
            caption = f"{headline}\n\nHSD is keeping the soccer lane active."
            story = f"NWSL WATCH: {headline}\nKeep this one on the board."
            first = "What’s your read on this?"
        elif league == "WTA":
            hook = f"WTA watch: {headline}."
            threads = f"{headline}\n\nWho’s actually trending up right now?"
            caption = f"{headline}\n\nThe tennis lane belongs on the HSD board too."
            story = f"WTA WATCH: {headline}\nThis belongs on the radar."
            first = "Who are you watching in this stretch?"
        else:
            hook = f"{league}: {headline}."
            threads = f"{headline}\n\nAre we underrating this story?"
            caption = f"{headline}\n\nA women’s sports story worth keeping on the board."
            story = f"ON THE BOARD: {headline}"
            first = "What’s the angle people are missing?"
    else:
        hook = f"{league}: {headline}."
        threads = f"{headline}\n\nWhat are you watching here?"
        caption = f"{headline}\n\nHSD is tracking the bigger picture."
        story = f"HSD WATCH: {headline}"
        first = "Are we underrating this?"
    return {"copy_hook": hook, "threads_copy": threads, "ig_caption_seed": caption, "story_frame_text": story, "first_comment": first}


def choose_director_slots(graph: List[Dict[str, Any]], cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    usable = [r for r in graph if clean(r.get("director_status")) == "usable" and int(r.get("quality_score") or 0) >= 50]
    used_non_threads: Set[str] = set()
    crossposts: List[Dict[str, Any]] = []

    def rank(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        priority_order = {"manual_packet": 0, "result_or_recap": 1, "preview_event": 2, "official_news_article": 3, "ig_story_final_scores": 4}
        return sorted(rows, key=lambda r: (priority_order.get(normalize_type(r), 8), -int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", "")))

    def pick(pred, allow_dup=False):
        rows = rank([r for r in usable if pred(r)])
        for r in rows:
            if allow_dup or r["story_id"] not in used_non_threads:
                return r
        return None

    def non_wnba(r): return clean(r.get("league")).upper() not in {"WNBA", ""}
    def typ(t): return lambda r: normalize_type(r) == t
    def preview(r): return normalize_type(r) == "preview_event"
    def result(r): return normalize_type(r) == "result_or_recap" or "final" in low(r.get("story_type"))
    def strong_feed(r): return int(r.get("quality_score") or 0) >= 70 and normalize_type(r) in {"manual_packet", "result_or_recap", "preview_event", "official_news_article"}

    specs = [
        ("threads_morning", "Threads", "9:00 AM", lambda r: non_wnba(r) and normalize_type(r) == "official_news_article", True, "non_wnba_morning_conversation"),
        ("ig_feed_noon", "IG Feed", "12:00 PM", strong_feed, False, "best_feed_post"),
        ("ig_stories_rolling_1", "IG Stories", "10:30 AM", lambda r: non_wnba(r) or int(r.get("quality_score") or 0) >= 75, False, "story_card_one"),
        ("ig_stories_rolling_2", "IG Stories", "12:30 PM", lambda r: normalize_type(r) in {"official_news_article", "preview_event", "result_or_recap"}, False, "story_card_two"),
        ("ig_feed_evening_preview", "IG Feed", "4:45 PM", preview, False, "evening_preview_anchor"),
        ("threads_live", "Threads", "7:00-11:30 PM", preview, True, "live_preview_discussion"),
        ("nightcap", "Threads", "11:30 PM", result, True, "nightcap_result_discussion"),
    ]
    slots: List[Dict[str, Any]] = []
    seen_story_platforms: Dict[str, List[str]] = {}
    for slot_id, platform, time_et, pred, allow_dup, label in specs:
        r = pick(pred, allow_dup=allow_dup)
        if not r:
            slots.append({"slot_id": slot_id, "platform": platform, "slot_time_et": time_et, "status": "skip_no_director_pick", "director_label": label, "notes": "No director-approved story fit this slot."})
            continue
        sid = clean(r.get("story_id"))
        if platform != "Threads":
            used_non_threads.add(sid)
        platforms = seen_story_platforms.setdefault(sid, [])
        platforms.append(platform)
        group = ""
        if len(platforms) > 1:
            group = f"crosspost_{sid}"
        cp = copy_pack(r, platform)
        slots.append({
            "slot_id": slot_id,
            "platform": platform,
            "slot_time_et": time_et,
            "content_type": normalize_type(r),
            "headline": clean(r.get("headline")),
            "league": clean(r.get("league")),
            "priority": clean(r.get("priority")),
            "story_id": sid,
            "status": "ready_with_review",
            "asset_state": clean(r.get("asset_state")),
            "quality_score": clean(r.get("quality_score")),
            "director_label": label,
            "crosspost_group": group,
            "copy_hook": cp["copy_hook"],
            "threads_copy": cp["threads_copy"],
            "ig_caption_seed": cp["ig_caption_seed"],
            "story_frame_text": cp["story_frame_text"],
            "first_comment": cp["first_comment"],
            "notes": clean(r.get("director_reason")),
        })
    # Mark intentional crossposts after all slots are picked.
    by_sid: Dict[str, List[Dict[str, Any]]] = {}
    for s in slots:
        if s.get("status") == "ready_with_review":
            by_sid.setdefault(s.get("story_id", ""), []).append(s)
    for sid, ss in by_sid.items():
        if len(ss) > 1:
            group = f"crosspost_{sid}"
            for s in ss:
                s["crosspost_group"] = group
            crossposts.append({"crosspost_group": group, "story_id": sid, "headline": ss[0].get("headline"), "platforms": " | ".join(s.get("platform", "") for s in ss), "intentional": "Yes", "reason": "Content Director allowed platform-shaped crosspost."})
    write_csv(OUT_SLOTS, slots, SLOT_FIELDS)
    write_csv(OUT_CROSSPOST, crossposts, CROSSPOST_FIELDS)
    write_csv(OUT_FEED, [s for s in slots if s.get("platform") == "IG Feed" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_STORY, [s for s in slots if s.get("platform") == "IG Stories" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_THREADS, [s for s in slots if s.get("platform") == "Threads" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    # Aliases used by existing artifact paths.
    write_csv("mermaid_content_slots_v2.csv", slots, SLOT_FIELDS)
    write_csv("ig_feed_queue_v2.csv", read_csv(OUT_FEED), SLOT_FIELDS)
    write_csv("ig_story_queue_v2.csv", read_csv(OUT_STORY), SLOT_FIELDS)
    write_csv("threads_queue_v2.csv", read_csv(OUT_THREADS), SLOT_FIELDS)
    return slots, crossposts


def asset_strategy(graph: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = {clean(s.get("story_id")) for s in slots if clean(s.get("story_id"))}
    rows: List[Dict[str, Any]] = []
    for r in graph:
        if r.get("story_id") not in ids:
            continue
        typ = normalize_type(r)
        if typ == "preview_event":
            strat = "exact team logos plus editorial matchup typography; player graphics only if every required team has exact registry-approved players"
            player = "conditional_exact_only"
        elif typ == "official_news_article":
            strat = "league/event/team logo, article/source visual only if rights-safe, premium text-first editorial card"
            player = "only if exact subject/player asset exists"
        elif typ == "result_or_recap":
            strat = "exact team logos, final score typography, leaders only if verified; player image only if exact approved"
            player = "conditional_exact_only"
        else:
            strat = "text-first editorial card with exact logos if available"
            player = "not_required"
        rows.append({"story_id": r.get("story_id"), "headline": r.get("headline"), "league": r.get("league"), "story_type": typ, "recommended_asset_strategy": strat, "player_graphics_status": player, "logo_need": "exact_logo_required_when_team_or_league_visible", "notes": "Content Director asset strategy. No generated players or logos."})
    write_csv(OUT_ASSETS, rows, ASSET_FIELDS)
    return rows


def compile_packets(graph: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if PACKET_DIR.exists():
        shutil.rmtree(PACKET_DIR)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    slot_by_id = {clean(s.get("story_id")): s for s in slots if clean(s.get("story_id"))}
    rows: List[Dict[str, Any]] = []
    for r in graph:
        sid = clean(r.get("story_id"))
        if sid not in slot_by_id:
            continue
        s = slot_by_id[sid]
        p = PACKET_DIR / sid
        p.mkdir(parents=True, exist_ok=True)
        packet = {"version": VERSION, "story": r, "slot": s, "locked_facts": {"headline": r.get("headline"), "league": r.get("league"), "story_type": normalize_type(r), "source_ref": r.get("source_ref")}}
        render = {"version": VERSION, "story_id": sid, "slot_id": s.get("slot_id"), "asset_policy": "exact assets only; no generated people/logos/stats", "status": "ready_with_review"}
        prompt = f"# HSD Content Director Graphics Prompt\n\nStory: {r.get('headline')}\nLeague: {r.get('league')}\nType: {normalize_type(r)}\nSlot: {s.get('slot_id')} / {s.get('platform')}\n\nCreate a premium Her Sports Daily social asset. The tone is smart, sharp, women’s sports desk, and fast to understand.\n\nLocked facts:\n- Headline: {r.get('headline')}\n- Source/ref: {r.get('source_ref')}\n\nDisplay direction:\n- {s.get('copy_hook')}\n- Use exact logos and exact player assets only.\n- Player graphics are required when appropriate, but only if exact approved player assets are present.\n- Do not invent faces, jerseys, logos, stats, results, injuries, or quotes.\n- No internal workflow labels.\n\nCTA: {s.get('first_comment')}\n"
        (p / "content_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
        (p / "render_plan.json").write_text(json.dumps(render, indent=2), encoding="utf-8")
        (p / "00_GRAPHICS_PROMPT.md").write_text(prompt, encoding="utf-8")
        (p / "02_COPY_DESK.md").write_text((s.get("ig_caption_seed") or "") + "\n", encoding="utf-8")
        (p / "03_THREADS_COPY.md").write_text((s.get("threads_copy") or "") + "\n", encoding="utf-8")
        (p / "04_FIRST_COMMENT.md").write_text((s.get("first_comment") or "") + "\n", encoding="utf-8")
        rows.append({"story_id": sid, "headline": r.get("headline"), "league": r.get("league"), "story_type": normalize_type(r), "quality_score": r.get("quality_score"), "packet_dir": p.as_posix(), "graphics_prompt": (p / "00_GRAPHICS_PROMPT.md").as_posix(), "copy_desk": (p / "02_COPY_DESK.md").as_posix(), "threads_copy": (p / "03_THREADS_COPY.md").as_posix(), "first_comment": (p / "04_FIRST_COMMENT.md").as_posix()})
    write_csv(OUT_PROMPT_INDEX, rows, PROMPT_FIELDS)
    write_csv("mermaid_compiled_packet_index.csv", rows, PROMPT_FIELDS)
    if Path("mermaid_compiled_packets").exists():
        shutil.rmtree("mermaid_compiled_packets")
    shutil.copytree(PACKET_DIR, "mermaid_compiled_packets")
    return rows


def write_board(graph, slots, rejected, floors, crossposts, assets, packets) -> None:
    lines = ["# HSD Mermaid Master Content Board v2.3", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Content Director Verdict", "", "Content Director ran. This board is slot-deduped, wrong-sport filtered, platform-shaped, and asset-aware.", "", "## Counts", "", f"- director story graph rows: {len(graph)}", f"- content slots: {len(slots)}", f"- rejected wrong-sport rows: {len(rejected)}", f"- intentional crosspost groups: {len(crossposts)}", f"- asset strategy rows: {len(assets)}", f"- compiled packets: {len(packets)}", "", "## Sport floors", ""]
    for f in floors:
        lines.append(f"- {f['league']}: {f['usable_count']}/{f['target']} — {f['status']}")
    lines += ["", "## Slots", ""]
    for s in slots:
        lines += [f"### {s.get('slot_id')} — {s.get('platform')} / {s.get('slot_time_et')}", f"- Status: {s.get('status')}", f"- Headline: {s.get('headline') or '—'}", f"- League: {s.get('league') or '—'}", f"- Type: {s.get('content_type') or '—'}", f"- Director label: {s.get('director_label') or '—'}", f"- Crosspost: {s.get('crosspost_group') or 'No'}", f"- Hook: {s.get('copy_hook') or '—'}", ""]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("mermaid_master_content_board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_operator(slots, floors, rejected) -> None:
    short = [f for f in floors if f.get("status") == "SHORT"]
    lines = ["# Operator Next Actions v2.3", "", f"Generated: {now_iso()}", "", "## Do next", ""]
    if short:
        lines.append("1. Source floors still short: " + ", ".join(f"{f['league']} ({f['shortfall']})" for f in short))
    else:
        lines.append("1. Sport floors passed for this run.")
    if rejected:
        lines.append(f"2. Wrong-sport filter rejected {len(rejected)} polluted rows. Review if a real softball item was overfiltered.")
    else:
        lines.append("2. Wrong-sport filter found no polluted rows.")
    lines.append("3. Use Content Director queues and compiled packets for handoff.")
    lines += ["", "## Ready slots", ""]
    for s in slots:
        if s.get("status") == "ready_with_review":
            lines.append(f"- {s.get('platform')} / {s.get('slot_time_et')}: {s.get('headline')}")
    OUT_OPERATOR.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    cfg = load_cfg()
    graph, rejected = build_director_graph(cfg)
    floors = floor_status(graph, cfg)
    slots, crossposts = choose_director_slots(graph, cfg)
    assets = asset_strategy(graph, slots)
    packets = compile_packets(graph, slots)
    write_board(graph, slots, rejected, floors, crossposts, assets, packets)
    write_operator(slots, floors, rejected)
    # Existing artifact aliases.
    write_csv("mermaid_story_graph.csv", graph, GRAPH_FIELDS)
    manifest = {"version": VERSION, "generated_at": now_iso(), "director_story_graph_rows": len(graph), "slots": len(slots), "rejected_wrong_sport": len(rejected), "crossposts": len(crossposts), "asset_strategy_rows": len(assets), "packets": len(packets)}
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Append to Upper Echelon report if it already exists.
    if Path("mermaid_upper_echelon_report.md").exists():
        prev = Path("mermaid_upper_echelon_report.md").read_text(encoding="utf-8", errors="replace")
        Path("mermaid_upper_echelon_report.md").write_text(prev + "\n---\n\n" + OUT_REPORT.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
