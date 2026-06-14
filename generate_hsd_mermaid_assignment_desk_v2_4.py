from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

VERSION = "v3.3.4-mermaid-assignment-desk-v2.4"
CFG_PATH = Path("config/hsd_mermaid_assignment_desk_v2_4.json")

GRAPH_INPUTS = ["mermaid_director_story_graph.csv", "mermaid_classified_story_graph.csv", "mermaid_quality_story_graph.csv", "mermaid_story_graph.csv"]

OUT_REPORT = Path("mermaid_assignment_desk_report.md")
OUT_MANIFEST = Path("mermaid_assignment_desk_manifest.json")
OUT_GRAPH = Path("mermaid_assignment_story_graph.csv")
OUT_SLOTS = Path("mermaid_assignment_content_slots.csv")
OUT_FEED = Path("ig_feed_queue_v2_4.csv")
OUT_STORY = Path("ig_story_queue_v2_4.csv")
OUT_THREADS = Path("threads_queue_v2_4.csv")
OUT_HELD = Path("assignment_desk_held_stories.csv")
OUT_CROSSPOST = Path("assignment_desk_crosspost_plan.csv")
OUT_FLOORS = Path("assignment_desk_sport_floor_status.csv")
OUT_ASSETS = Path("assignment_desk_asset_strategy.csv")
OUT_PROMPTS = Path("mermaid_assignment_prompt_index.csv")
OUT_OPERATOR = Path("operator_next_actions_v2_4.md")
PACKET_DIR = Path("mermaid_assignment_compiled_packets")

GRAPH_FIELDS = ["story_id", "story_type", "sport", "league", "headline", "event_date", "priority", "verification_state", "source_state", "platform_fit", "asset_state", "source_ref", "notes", "quality_score", "quality_status", "quality_reason", "assignment_type", "assignment_status", "assignment_reason"]
SLOT_FIELDS = ["slot_id", "platform", "slot_time_et", "content_type", "headline", "league", "priority", "story_id", "status", "asset_state", "quality_score", "assignment_label", "crosspost_group", "copy_hook", "threads_copy", "ig_caption_seed", "story_frame_text", "first_comment", "notes"]
HELD_FIELDS = ["story_id", "league", "headline", "hold_reason", "source_ref"]
FLOOR_FIELDS = ["league", "target", "usable_count", "status", "shortfall", "notes"]
ASSET_FIELDS = ["story_id", "headline", "league", "assignment_type", "recommended_asset_strategy", "player_graphics_status", "prompt_split", "notes"]
PROMPT_FIELDS = ["story_id", "headline", "league", "assignment_type", "slot_id", "packet_dir", "public_prompt", "control_rules", "copy_desk", "threads_copy", "first_comment"]
CROSSPOST_FIELDS = ["crosspost_group", "story_id", "headline", "slots", "platforms", "intentional", "reason"]


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
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def cfg() -> Dict[str, Any]:
    return read_json(CFG_PATH, {})


def load_graph() -> List[Dict[str, str]]:
    for p in GRAPH_INPUTS:
        rows = read_csv(p)
        if rows:
            return rows
    return []


def matchup_like(headline: str) -> bool:
    h = low(headline)
    return bool(re.search(r"\b(at|vs\.?|versus)\b", h))


def schedule_source(row: Dict[str, Any]) -> bool:
    combined = low(" ".join([row.get("source_state", ""), row.get("source_ref", ""), row.get("notes", ""), row.get("story_type", "")]))
    return any(x in combined for x in ["scoreboard", "schedule", "slate", "preview", "game/_/gameid", "site.api.espn"])


def article_source(row: Dict[str, Any]) -> bool:
    combined = low(" ".join([row.get("source_ref", ""), row.get("source_state", ""), row.get("story_type", "")]))
    return "/news/" in combined or "official_news" in combined or "news_article" in combined


def hold_reason(row: Dict[str, Any], c: Dict[str, Any]) -> str:
    headline = clean(row.get("headline"))
    h = low(headline)
    league = clean(row.get("league"))
    if not headline or len(headline) < 8:
        return "missing_or_too_short"
    if h in {low(x) for x in c.get("generic_hold_titles", [])}:
        return "generic_title"
    for term in c.get("wrong_sport_filters", {}).get(league, []):
        if low(term) in h:
            return f"wrong_sport:{term}"
    if league == "NCAA Softball" and not any(x in h for x in ["softball", "wcws", "college world series", "women's college world series", "women’s college world series"]):
        return "ncaa_softball_missing_softball_signal"
    if league == "NWSL" and h in {"challenge cup", "regular season", "schedule"}:
        return "generic_nwsl_reference"
    return ""


def assignment_type(row: Dict[str, Any]) -> str:
    st = low(row.get("story_type"))
    headline = clean(row.get("headline"))
    league = clean(row.get("league"))
    if "breaking" in st or "rumor" in st:
        return "breaking_or_rumor"
    if "final" in st or "result" in st or "recap" in st or "last night" in low(headline):
        return "result_or_recap"
    if matchup_like(headline) and schedule_source(row) and not article_source(row):
        return "preview_event"
    if league == "LPGA" and article_source(row):
        return "official_news_article"
    if article_source(row):
        return "official_news_article"
    if "manual" in st:
        return "manual_packet"
    if matchup_like(headline) and schedule_source(row):
        return "preview_event"
    if "news" in st:
        return "official_news_article"
    return "official_story_review"


def build_assignment_graph(c: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows = load_graph()
    out: List[Dict[str, Any]] = []
    held: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for r in rows:
        headline = clean(r.get("headline"))
        sid = clean(r.get("story_id")) or slug(headline)
        if not headline or sid in seen:
            continue
        seen.add(sid)
        reason = hold_reason(r, c)
        if reason:
            held.append({"story_id": sid, "league": clean(r.get("league")), "headline": headline, "hold_reason": reason, "source_ref": clean(r.get("source_ref"))})
            continue
        typ = assignment_type(r)
        rr = dict(r)
        rr.update({
            "story_id": sid,
            "headline": headline,
            "assignment_type": typ,
            "story_type": typ,
            "quality_score": clean(r.get("quality_score")) or "60",
            "quality_status": clean(r.get("quality_status")) or "use",
            "assignment_status": "usable",
            "assignment_reason": "assignment desk approved",
        })
        out.append(rr)
    out.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", ""), r.get("headline", "")))
    write_csv(OUT_GRAPH, out, GRAPH_FIELDS)
    write_csv(OUT_HELD, held, HELD_FIELDS)
    return out, held


def floor_status(graph: List[Dict[str, Any]], c: Dict[str, Any]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in graph:
        lg = clean(r.get("league")) or "Unknown"
        counts[lg] = counts.get(lg, 0) + 1
    rows: List[Dict[str, Any]] = []
    for league, target in c.get("floor_targets", {}).items():
        have = counts.get(league, 0)
        short = max(0, int(target) - have)
        rows.append({"league": league, "target": target, "usable_count": have, "status": "PASS" if short == 0 else "SHORT", "shortfall": short, "notes": "Assignment Desk does not invent stories; SHORT means source/parser gap."})
    write_csv(OUT_FLOORS, rows, FLOOR_FIELDS)
    return rows


def copy_for(row: Dict[str, Any]) -> Dict[str, str]:
    h = clean(row.get("headline"))
    league = clean(row.get("league"))
    typ = assignment_type(row)
    if typ == "preview_event":
        return {
            "hook": f"{h}: the game lane to watch.",
            "threads": f"{h}\n\nWho needs this one more?",
            "caption": f"{h}\n\nTonight’s HSD watch point: pace, execution, and who owns the pressure moments.",
            "story": f"WATCH THIS: {h}\nWho controls the game first?",
            "first": "Which side are you trusting tonight?",
        }
    if typ == "result_or_recap":
        return {
            "hook": f"{h}: put this result on the board.",
            "threads": f"{h}\n\nBiggest takeaway?",
            "caption": f"{h}\n\nThe result matters because it changes the conversation, not just the scoreboard.",
            "story": f"RESULT CHECK: {h}\nWhat changed after this one?",
            "first": "What was the swing moment?",
        }
    if typ == "official_news_article" and league == "LPGA":
        return {
            "hook": f"The LPGA lane has a real storyline: {h}.",
            "threads": f"{h}\n\nThe LPGA board is getting spicy. Are we paying enough attention?",
            "caption": f"{h}\n\nThe golf lane is giving HSD more to work with than people realize.",
            "story": f"LPGA WATCH: {h}\nThis belongs on the board.",
            "first": "Are we underrating this LPGA moment?",
        }
    if typ == "official_news_article" and league == "NWSL":
        return {
            "hook": f"NWSL watch: {h}.",
            "threads": f"{h}\n\nWhat’s the NWSL angle people are missing?",
            "caption": f"{h}\n\nHSD is keeping the soccer lane active.",
            "story": f"NWSL WATCH: {h}\nKeep this one on the board.",
            "first": "What’s your read on this?",
        }
    return {
        "hook": f"{league}: {h}.",
        "threads": f"{h}\n\nAre we underrating this story?",
        "caption": f"{h}\n\nA women’s sports story worth keeping on the board.",
        "story": f"ON THE BOARD: {h}",
        "first": "What’s the angle people are missing?",
    }


def rank(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    type_rank = {"manual_packet": 0, "result_or_recap": 1, "official_news_article": 2, "preview_event": 3, "official_story_review": 4}
    league_boost = {"LPGA": -6, "NWSL": -5, "WTA": -5, "USWNT": -5, "WNBA": 0}
    return sorted(rows, key=lambda r: (type_rank.get(assignment_type(r), 9), league_boost.get(clean(r.get("league")), 0), -int(r.get("quality_score") or 0), r.get("priority", "P9")))


def choose_slots(graph: List[Dict[str, Any]], c: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    usable = [r for r in graph if clean(r.get("assignment_status")) == "usable"]
    used_ig: Set[str] = set()
    used_any: Dict[str, List[str]] = {}
    slots: List[Dict[str, Any]] = []

    def pick(pred, allow_threads_dup=False):
        candidates = rank([r for r in usable if pred(r)])
        for r in candidates:
            sid = r.get("story_id")
            if sid not in used_ig:
                return r
            if allow_threads_dup:
                return r
        return None

    def add(slot_id: str, platform: str, time_et: str, pred, label: str, allow_threads_dup: bool = False):
        r = pick(pred, allow_threads_dup=allow_threads_dup)
        if not r:
            slots.append({"slot_id": slot_id, "platform": platform, "slot_time_et": time_et, "status": "skip_no_assignment", "assignment_label": label, "notes": "No assignment-approved story fit this slot."})
            return
        sid = clean(r.get("story_id"))
        if platform != "Threads":
            used_ig.add(sid)
        used_any.setdefault(sid, []).append(slot_id)
        cp = copy_for(r)
        slots.append({
            "slot_id": slot_id,
            "platform": platform,
            "slot_time_et": time_et,
            "content_type": assignment_type(r),
            "headline": clean(r.get("headline")),
            "league": clean(r.get("league")),
            "priority": clean(r.get("priority")),
            "story_id": sid,
            "status": "ready_with_review",
            "asset_state": clean(r.get("asset_state")),
            "quality_score": clean(r.get("quality_score")),
            "assignment_label": label,
            "crosspost_group": "",
            "copy_hook": cp["hook"],
            "threads_copy": cp["threads"],
            "ig_caption_seed": cp["caption"],
            "story_frame_text": cp["story"],
            "first_comment": cp["first"],
            "notes": clean(r.get("assignment_reason")),
        })

    non_wnba_article = lambda r: clean(r.get("league")).upper() != "WNBA" and assignment_type(r) == "official_news_article"
    best_feed = lambda r: assignment_type(r) in {"official_news_article", "result_or_recap", "manual_packet"} and int(r.get("quality_score") or 0) >= 65
    story_support = lambda r: assignment_type(r) in {"official_news_article", "preview_event", "result_or_recap"}
    preview = lambda r: assignment_type(r) == "preview_event"
    result = lambda r: assignment_type(r) == "result_or_recap"

    add("threads_morning", "Threads", "9:00 AM", non_wnba_article, "non_wnba_debate_starter", allow_threads_dup=True)
    add("ig_feed_noon", "IG Feed", "12:00 PM", best_feed, "strongest_feed_assignment")
    add("ig_stories_rolling_1", "IG Stories", "10:30 AM", story_support, "supporting_story_card_one")
    add("ig_stories_rolling_2", "IG Stories", "12:30 PM", story_support, "supporting_story_card_two")
    add("ig_feed_evening_preview", "IG Feed", "4:45 PM", preview, "actual_evening_preview_only")
    add("threads_live", "Threads", "7:00-11:30 PM", preview, "live_preview_debate", allow_threads_dup=True)
    add("nightcap", "Threads", "11:30 PM", result, "nightcap_result_only", allow_threads_dup=True)

    crossposts: List[Dict[str, Any]] = []
    by_story: Dict[str, List[Dict[str, Any]]] = {}
    for s in slots:
        if s.get("status") == "ready_with_review":
            by_story.setdefault(s.get("story_id", ""), []).append(s)
    for sid, ss in by_story.items():
        if len(ss) > 1:
            group = f"crosspost_{sid}"
            for s in ss:
                s["crosspost_group"] = group
            crossposts.append({"crosspost_group": group, "story_id": sid, "headline": ss[0].get("headline"), "slots": " | ".join(s.get("slot_id", "") for s in ss), "platforms": " | ".join(s.get("platform", "") for s in ss), "intentional": "Yes", "reason": "Assignment Desk platform-shaped crosspost."})

    write_csv(OUT_SLOTS, slots, SLOT_FIELDS)
    write_csv(OUT_CROSSPOST, crossposts, CROSSPOST_FIELDS)
    write_csv(OUT_FEED, [s for s in slots if s.get("platform") == "IG Feed" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_STORY, [s for s in slots if s.get("platform") == "IG Stories" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_THREADS, [s for s in slots if s.get("platform") == "Threads" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv("mermaid_content_slots_v2.csv", slots, SLOT_FIELDS)
    write_csv("ig_feed_queue_v2.csv", read_csv(OUT_FEED), SLOT_FIELDS)
    write_csv("ig_story_queue_v2.csv", read_csv(OUT_STORY), SLOT_FIELDS)
    write_csv("threads_queue_v2.csv", read_csv(OUT_THREADS), SLOT_FIELDS)
    return slots, crossposts


def asset_strategy(graph: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = {s.get("story_id") for s in slots if s.get("status") == "ready_with_review"}
    rows: List[Dict[str, Any]] = []
    for r in graph:
        if r.get("story_id") not in ids:
            continue
        typ = assignment_type(r)
        if typ == "preview_event":
            strat = "exact team logos plus matchup typography; player graphics only if every team has exact registry assets"
            player = "conditional_exact_only"
        elif typ == "official_news_article":
            strat = "text-first premium editorial card; use league/event/team logos or rights-safe source visual if available"
            player = "only_if_exact_subject_asset_exists"
        elif typ == "result_or_recap":
            strat = "exact logos plus score/result typography; player only if exact and verified"
            player = "conditional_exact_only"
        else:
            strat = "premium text-first editorial card"
            player = "not_required"
        rows.append({"story_id": r.get("story_id"), "headline": r.get("headline"), "league": r.get("league"), "assignment_type": typ, "recommended_asset_strategy": strat, "player_graphics_status": player, "prompt_split": "public_prompt_plus_control_rules", "notes": "Do not place control rules in public display prompt."})
    write_csv(OUT_ASSETS, rows, ASSET_FIELDS)
    return rows


def compile_packets(graph: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if PACKET_DIR.exists():
        shutil.rmtree(PACKET_DIR)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    slot_by_sid = {s.get("story_id"): s for s in slots if s.get("status") == "ready_with_review"}
    rows: List[Dict[str, Any]] = []
    for r in graph:
        sid = r.get("story_id")
        if sid not in slot_by_sid:
            continue
        s = slot_by_sid[sid]
        cp = copy_for(r)
        p = PACKET_DIR / sid
        p.mkdir(parents=True, exist_ok=True)
        public_prompt = f"# HSD Public Graphics Prompt\n\nCreate a premium Her Sports Daily social asset.\n\nStory: {r.get('headline')}\nLeague: {r.get('league')}\nFormat lane: {s.get('platform')} / {s.get('slot_id')}\n\nPublic display direction:\n- {s.get('copy_hook')}\n- Use clean, confident HSD editorial language.\n- Keep the visual fast to read, premium, and social-first.\n- CTA idea: {s.get('first_comment')}\n"
        control_rules = f"# Control Rules - Do Not Render\n\nLocked source/ref: {r.get('source_ref')}\nAssignment type: {assignment_type(r)}\nAsset policy: exact logos only, exact player assets only, no generated players, no invented stats, no invented scores, no invented quotes.\nPlayer graphics: required when appropriate only if exact approved assets exist.\n"
        copy_desk = f"{s.get('ig_caption_seed')}\n\nFirst comment: {s.get('first_comment')}\n"
        (p / "content_packet.json").write_text(json.dumps({"version": VERSION, "story": r, "slot": s}, indent=2), encoding="utf-8")
        (p / "render_plan.json").write_text(json.dumps({"version": VERSION, "story_id": sid, "slot_id": s.get("slot_id"), "prompt_split": True, "status": "ready_with_review"}, indent=2), encoding="utf-8")
        (p / "00_PUBLIC_PROMPT_TO_PASTE.md").write_text(public_prompt, encoding="utf-8")
        (p / "01_CONTROL_RULES_DO_NOT_RENDER.md").write_text(control_rules, encoding="utf-8")
        (p / "02_COPY_DESK.md").write_text(copy_desk, encoding="utf-8")
        (p / "03_THREADS_COPY.md").write_text((s.get("threads_copy") or "") + "\n", encoding="utf-8")
        (p / "04_FIRST_COMMENT.md").write_text((s.get("first_comment") or "") + "\n", encoding="utf-8")
        rows.append({"story_id": sid, "headline": r.get("headline"), "league": r.get("league"), "assignment_type": assignment_type(r), "slot_id": s.get("slot_id"), "packet_dir": p.as_posix(), "public_prompt": (p / "00_PUBLIC_PROMPT_TO_PASTE.md").as_posix(), "control_rules": (p / "01_CONTROL_RULES_DO_NOT_RENDER.md").as_posix(), "copy_desk": (p / "02_COPY_DESK.md").as_posix(), "threads_copy": (p / "03_THREADS_COPY.md").as_posix(), "first_comment": (p / "04_FIRST_COMMENT.md").as_posix()})
    write_csv(OUT_PROMPTS, rows, PROMPT_FIELDS)
    write_csv("mermaid_compiled_packet_index.csv", rows, PROMPT_FIELDS)
    if Path("mermaid_compiled_packets").exists():
        shutil.rmtree("mermaid_compiled_packets")
    shutil.copytree(PACKET_DIR, "mermaid_compiled_packets")
    return rows


def write_board(graph, slots, held, floors, crossposts, assets, packets) -> None:
    lines = ["# HSD Mermaid Assignment Desk v2.4", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Verdict", "", "Assignment Desk ran. This is the editorial assignment layer: true previews only, one strongest feed post, support slots, Threads debate, intentional crossposts, and split public/control prompts.", "", "## Counts", "", f"- assignment story graph rows: {len(graph)}", f"- content slots: {len(slots)}", f"- held stories: {len(held)}", f"- crosspost groups: {len(crossposts)}", f"- asset strategy rows: {len(assets)}", f"- prompt packets: {len(packets)}", "", "## Sport floors", ""]
    for f in floors:
        lines.append(f"- {f['league']}: {f['usable_count']}/{f['target']} — {f['status']}")
    lines += ["", "## Assignment slots", ""]
    for s in slots:
        lines += [f"### {s.get('slot_id')} — {s.get('platform')} / {s.get('slot_time_et')}", f"- Status: {s.get('status')}", f"- Headline: {s.get('headline') or '—'}", f"- League: {s.get('league') or '—'}", f"- Type: {s.get('content_type') or '—'}", f"- Crosspost: {s.get('crosspost_group') or 'No'}", f"- Hook: {s.get('copy_hook') or '—'}", ""]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("mermaid_master_content_board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_operator(slots, floors, held) -> None:
    short = [f for f in floors if f.get("status") == "SHORT"]
    lines = ["# Operator Next Actions v2.4", "", f"Generated: {now_iso()}", "", "## Do next", ""]
    if short:
        lines.append("1. Source/parser floors short: " + ", ".join(f"{f['league']} ({f['shortfall']})" for f in short))
    else:
        lines.append("1. Sport floors passed this run.")
    lines.append(f"2. Held stories: {len(held)}. Review only if a good story got overfiltered.")
    lines.append("3. Use 00_PUBLIC_PROMPT_TO_PASTE.md for graphics chats. Keep 01_CONTROL_RULES_DO_NOT_RENDER.md as reference only.")
    lines += ["", "## Ready assignments", ""]
    for s in slots:
        if s.get("status") == "ready_with_review":
            lines.append(f"- {s.get('platform')} / {s.get('slot_time_et')}: {s.get('headline')}")
    OUT_OPERATOR.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    c = cfg()
    graph, held = build_assignment_graph(c)
    floors = floor_status(graph, c)
    slots, crossposts = choose_slots(graph, c)
    assets = asset_strategy(graph, slots)
    packets = compile_packets(graph, slots)
    write_csv(OUT_GRAPH, graph, GRAPH_FIELDS)
    write_csv("mermaid_story_graph.csv", graph, GRAPH_FIELDS)
    write_board(graph, slots, held, floors, crossposts, assets, packets)
    write_operator(slots, floors, held)
    manifest = {"version": VERSION, "generated_at": now_iso(), "assignment_story_graph_rows": len(graph), "slots": len(slots), "held_stories": len(held), "crosspost_groups": len(crossposts), "asset_strategy_rows": len(assets), "prompt_packets": len(packets)}
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if Path("mermaid_upper_echelon_report.md").exists():
        prev = Path("mermaid_upper_echelon_report.md").read_text(encoding="utf-8", errors="replace")
        Path("mermaid_upper_echelon_report.md").write_text(prev + "\n---\n\n" + OUT_REPORT.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
