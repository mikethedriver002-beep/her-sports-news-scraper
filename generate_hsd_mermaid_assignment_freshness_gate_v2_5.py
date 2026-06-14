from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

VERSION = "v3.3.5-mermaid-assignment-freshness-gate-v2.5"
CFG = Path("config/hsd_mermaid_assignment_freshness_gate_v2_5.json")

SLOT_INPUTS = ["mermaid_assignment_content_slots.csv", "mermaid_director_content_slots.csv", "mermaid_content_slots_v2.csv"]
GRAPH_INPUTS = ["mermaid_assignment_story_graph.csv", "mermaid_director_story_graph.csv", "mermaid_story_graph.csv"]

OUT_REPORT = Path("mermaid_assignment_freshness_gate_report.md")
OUT_MANIFEST = Path("mermaid_assignment_freshness_gate_manifest.json")
OUT_SLOTS = Path("mermaid_assignment_final_slots.csv")
OUT_FEED = Path("ig_feed_queue_v2_5.csv")
OUT_STORY = Path("ig_story_queue_v2_5.csv")
OUT_THREADS = Path("threads_queue_v2_5.csv")
OUT_HELD = Path("assignment_freshness_held_slots.csv")
OUT_PROMPTS = Path("mermaid_assignment_final_prompt_index.csv")
OUT_OPERATOR = Path("operator_next_actions_v2_5.md")
PACKET_DIR = Path("mermaid_assignment_final_packets")

SLOT_FIELDS = ["slot_id", "platform", "slot_time_et", "content_type", "headline", "league", "priority", "story_id", "status", "asset_state", "quality_score", "assignment_label", "freshness_label", "crosspost_group", "copy_hook", "threads_copy", "ig_caption_seed", "story_frame_text", "first_comment", "notes"]
HELD_FIELDS = ["slot_id", "platform", "headline", "story_id", "hold_reason", "replacement_status"]
PROMPT_FIELDS = ["story_id", "headline", "league", "content_type", "slot_id", "packet_dir", "public_prompt", "control_rules", "copy_desk", "threads_copy", "first_comment"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def low(v: Any) -> str:
    return clean(v).lower()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def first_csv(paths: List[str]) -> List[Dict[str, str]]:
    for p in paths:
        rows = read_csv(p)
        if rows:
            return rows
    return []


def text_of(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def preview_gate_blocked(cfg: Dict[str, Any]) -> tuple[bool, List[str]]:
    hay = "\n".join([
        text_of("operator_command_center.md"),
        text_of("graphics_upload_pack_status.csv"),
        text_of("preview_bundle_quality.md"),
        text_of("preview_bundle_quality.csv"),
        text_of("studio_preview_build_v2_report.md"),
        text_of("graphics_chat_direct_handoff.md"),
    ])
    hits = [s for s in cfg.get("preview_block_signals", []) if s.lower() in hay.lower()]
    return bool(hits), hits


def type_of(row: Dict[str, Any]) -> str:
    return clean(row.get("content_type") or row.get("assignment_type") or row.get("story_type"))


def is_preview(row: Dict[str, Any]) -> bool:
    return type_of(row) == "preview_event" or "preview" in low(type_of(row))


def copy_for(row: Dict[str, Any], freshness_label: str = "") -> Dict[str, str]:
    h = clean(row.get("headline"))
    lg = clean(row.get("league"))
    typ = type_of(row)
    if freshness_label == "nightcap_followup_angle":
        return {
            "copy_hook": f"{h}: what this changes next.",
            "threads_copy": f"{h}\n\nDifferent angle for the nightcap: what does this change next?",
            "ig_caption_seed": f"{h}\n\nA result worth revisiting through what comes next.",
            "story_frame_text": f"NEXT LAYER: {h}\nWhat changes after this?",
            "first_comment": "What changes next because of this?",
        }
    if typ == "preview_event":
        return {"copy_hook": f"{h}: the game lane to watch.", "threads_copy": f"{h}\n\nWho needs this one more?", "ig_caption_seed": f"{h}\n\nTonight’s watch point: pace, execution, and who owns the pressure moments.", "story_frame_text": f"WATCH THIS: {h}", "first_comment": "Which side are you trusting?"}
    if typ == "result_or_recap":
        return {"copy_hook": f"{h}: put this result on the board.", "threads_copy": f"{h}\n\nBiggest takeaway?", "ig_caption_seed": f"{h}\n\nThe result matters because it changes the conversation, not just the scoreboard.", "story_frame_text": f"RESULT CHECK: {h}", "first_comment": "What was the swing moment?"}
    if typ == "official_news_article" and lg == "LPGA":
        return {"copy_hook": f"The LPGA lane has a real storyline: {h}.", "threads_copy": f"{h}\n\nThe LPGA board is getting spicy. Are we paying enough attention?", "ig_caption_seed": f"{h}\n\nThe golf lane is giving HSD more to work with than people realize.", "story_frame_text": f"LPGA WATCH: {h}", "first_comment": "Are we underrating this LPGA moment?"}
    return {"copy_hook": f"{lg}: {h}.", "threads_copy": f"{h}\n\nAre we underrating this story?", "ig_caption_seed": f"{h}\n\nA women’s sports story worth keeping on the board.", "story_frame_text": f"ON THE BOARD: {h}", "first_comment": "What’s the angle people are missing?"}


def rank_candidates(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    typ_rank = {"official_news_article": 0, "result_or_recap": 1, "manual_packet": 2, "preview_event": 3, "ig_story_final_scores": 4}
    league_boost = {"LPGA": -7, "NWSL": -5, "WTA": -5, "USWNT": -5, "WNBA": 0}
    return sorted(rows, key=lambda r: (typ_rank.get(type_of(r), 9), league_boost.get(clean(r.get("league")), 0), -int(r.get("quality_score") or 0)))


def build_final_slots(cfg: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    slots = first_csv(SLOT_INPUTS)
    graph = first_csv(GRAPH_INPUTS)
    blocked, signals = preview_gate_blocked(cfg)
    held: List[Dict[str, Any]] = []
    final: List[Dict[str, Any]] = []
    used_non_threads: Set[str] = set()

    graph_by_id = {clean(g.get("story_id")): g for g in graph if clean(g.get("story_id"))}

    def fallback(exclude: Set[str], prefer_non_wnba: bool = False):
        pool = []
        for g in graph:
            sid = clean(g.get("story_id"))
            if not sid or sid in exclude:
                continue
            if type_of(g) == "preview_event" and blocked:
                continue
            if type_of(g) not in {"official_news_article", "result_or_recap", "manual_packet", "ig_story_final_scores"}:
                continue
            pool.append(g)
        if prefer_non_wnba:
            non = [p for p in pool if clean(p.get("league")).upper() != "WNBA"]
            if non:
                pool = non
        return rank_candidates(pool)[0] if pool else None

    # First pass: hold blocked preview slots and obvious duplicates.
    for s in slots:
        ss = dict(s)
        sid = clean(ss.get("story_id"))
        if is_preview(ss) and blocked:
            held.append({"slot_id": ss.get("slot_id"), "platform": ss.get("platform"), "headline": ss.get("headline"), "story_id": sid, "hold_reason": "preview_gate_blocked:" + "|".join(signals), "replacement_status": "pending"})
            if clean(ss.get("platform")) == "Threads" and "live" in low(ss.get("slot_id")):
                repl = fallback({clean(x.get("story_id")) for x in final}, prefer_non_wnba=True)
                if repl:
                    cp = copy_for(repl)
                    ns = {**ss, **repl, "slot_id": ss.get("slot_id"), "platform": ss.get("platform"), "slot_time_et": ss.get("slot_time_et"), "content_type": type_of(repl), "status": "ready_with_review", "freshness_label": "preview_blocked_replaced", **cp}
                    final.append(ns)
                    held[-1]["replacement_status"] = "replaced_with_" + clean(repl.get("story_id"))
                continue
            # Feed preview stays held, not reassigned as fake preview.
            continue
        if clean(ss.get("platform")) != "Threads" and sid:
            if sid in used_non_threads:
                held.append({"slot_id": ss.get("slot_id"), "platform": ss.get("platform"), "headline": ss.get("headline"), "story_id": sid, "hold_reason": "duplicate_non_threads_assignment", "replacement_status": "held"})
                continue
            used_non_threads.add(sid)
        ss["freshness_label"] = "fresh"
        final.append(ss)

    # Nightcap duplicate angle handling.
    feed_ids = {clean(s.get("story_id")) for s in final if clean(s.get("platform")) == "IG Feed"}
    for s in final:
        if clean(s.get("slot_id")) == "nightcap" and clean(s.get("story_id")) in feed_ids:
            s["freshness_label"] = "nightcap_followup_angle"
            s["crosspost_group"] = clean(s.get("crosspost_group")) or "intentional_nightcap_followup_" + clean(s.get("story_id"))
            s.update(copy_for(s, "nightcap_followup_angle"))

    # Platform mix: if feed is WNBA, make sure at least one Threads/Story support is non-WNBA if available.
    feed_is_wnba = any(clean(s.get("platform")) == "IG Feed" and clean(s.get("league")).upper() == "WNBA" for s in final)
    has_non_wnba_support = any(clean(s.get("platform")) in {"Threads", "IG Stories"} and clean(s.get("league")).upper() not in {"WNBA", ""} for s in final)
    if feed_is_wnba and not has_non_wnba_support:
        repl = fallback({clean(x.get("story_id")) for x in final}, prefer_non_wnba=True)
        if repl:
            for s in final:
                if clean(s.get("platform")) == "Threads":
                    cp = copy_for(repl)
                    s.update(repl)
                    s.update(cp)
                    s["slot_id"] = "threads_morning"
                    s["platform"] = "Threads"
                    s["freshness_label"] = "platform_mix_non_wnba_support"
                    s["status"] = "ready_with_review"
                    break

    # Normalize copy and fields.
    for s in final:
        cp = copy_for(s, clean(s.get("freshness_label")))
        for k, v in cp.items():
            s[k] = clean(s.get(k)) or v
        s["content_type"] = clean(s.get("content_type")) or type_of(s)
        s["status"] = clean(s.get("status")) or "ready_with_review"
        s["freshness_label"] = clean(s.get("freshness_label")) or "fresh"

    return final, held, signals


def compile_packets(slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if PACKET_DIR.exists():
        shutil.rmtree(PACKET_DIR)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in slots:
        if clean(s.get("status")) != "ready_with_review":
            continue
        sid = clean(s.get("story_id")) or "slot_" + clean(s.get("slot_id"))
        p = PACKET_DIR / sid
        p.mkdir(parents=True, exist_ok=True)
        public_prompt = f"# HSD Public Graphics Prompt\n\nCreate a premium Her Sports Daily social asset.\n\nStory: {s.get('headline')}\nLeague: {s.get('league')}\nPlatform slot: {s.get('platform')} / {s.get('slot_id')}\n\nPublic display direction:\n- {s.get('copy_hook')}\n- Keep it fast, sharp, premium, and social-first.\n- CTA idea: {s.get('first_comment')}\n"
        control = f"# Control Rules - Do Not Render\n\nFreshness label: {s.get('freshness_label')}\nContent type: {s.get('content_type')}\nAsset policy: exact logos only, exact player assets only, no generated people, no invented scores/stats/quotes.\n"
        (p / "content_packet.json").write_text(json.dumps({"version": VERSION, "slot": s}, indent=2), encoding="utf-8")
        (p / "render_plan.json").write_text(json.dumps({"version": VERSION, "slot_id": s.get("slot_id"), "prompt_split": True, "status": "ready_with_review"}, indent=2), encoding="utf-8")
        (p / "00_PUBLIC_PROMPT_TO_PASTE.md").write_text(public_prompt, encoding="utf-8")
        (p / "01_CONTROL_RULES_DO_NOT_RENDER.md").write_text(control, encoding="utf-8")
        (p / "02_COPY_DESK.md").write_text(clean(s.get("ig_caption_seed")) + "\n\nFirst comment: " + clean(s.get("first_comment")) + "\n", encoding="utf-8")
        (p / "03_THREADS_COPY.md").write_text(clean(s.get("threads_copy")) + "\n", encoding="utf-8")
        (p / "04_FIRST_COMMENT.md").write_text(clean(s.get("first_comment")) + "\n", encoding="utf-8")
        rows.append({"story_id": sid, "headline": s.get("headline"), "league": s.get("league"), "content_type": s.get("content_type"), "slot_id": s.get("slot_id"), "packet_dir": p.as_posix(), "public_prompt": (p / "00_PUBLIC_PROMPT_TO_PASTE.md").as_posix(), "control_rules": (p / "01_CONTROL_RULES_DO_NOT_RENDER.md").as_posix(), "copy_desk": (p / "02_COPY_DESK.md").as_posix(), "threads_copy": (p / "03_THREADS_COPY.md").as_posix(), "first_comment": (p / "04_FIRST_COMMENT.md").as_posix()})
    write_csv(OUT_PROMPTS, rows, PROMPT_FIELDS)
    if Path("mermaid_compiled_packets").exists():
        shutil.rmtree("mermaid_compiled_packets")
    shutil.copytree(PACKET_DIR, "mermaid_compiled_packets")
    write_csv("mermaid_compiled_packet_index.csv", rows, PROMPT_FIELDS)
    return rows


def write_outputs(final: List[Dict[str, Any]], held: List[Dict[str, Any]], packets: List[Dict[str, Any]], signals: List[str]) -> None:
    write_csv(OUT_SLOTS, final, SLOT_FIELDS)
    write_csv(OUT_HELD, held, HELD_FIELDS)
    write_csv(OUT_FEED, [s for s in final if clean(s.get("platform")) == "IG Feed" and clean(s.get("status")) == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_STORY, [s for s in final if clean(s.get("platform")) == "IG Stories" and clean(s.get("status")) == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_THREADS, [s for s in final if clean(s.get("platform")) == "Threads" and clean(s.get("status")) == "ready_with_review"], SLOT_FIELDS)
    # Aliases.
    write_csv("mermaid_content_slots_v2.csv", final, SLOT_FIELDS)
    write_csv("ig_feed_queue_v2.csv", read_csv(OUT_FEED), SLOT_FIELDS)
    write_csv("ig_story_queue_v2.csv", read_csv(OUT_STORY), SLOT_FIELDS)
    write_csv("threads_queue_v2.csv", read_csv(OUT_THREADS), SLOT_FIELDS)
    lines = ["# Mermaid Assignment Freshness Gate v2.5", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Verdict", "", "Freshness Gate ran after Assignment Desk. Blocked previews are held or replaced, nightcap duplicate angles are reshaped, and platform mix is checked.", "", "## Preview block signals", ""]
    lines += [f"- {x}" for x in signals] if signals else ["- None"]
    lines += ["", "## Counts", "", f"- final slots: {len(final)}", f"- held slots: {len(held)}", f"- packets: {len(packets)}", "", "## Final slots", ""]
    for s in final:
        lines += [f"### {s.get('slot_id')} — {s.get('platform')} / {s.get('slot_time_et')}", f"- Status: {s.get('status')}", f"- Headline: {s.get('headline')}", f"- Type: {s.get('content_type')}", f"- Freshness: {s.get('freshness_label')}", f"- Hook: {s.get('copy_hook')}", ""]
    if held:
        lines += ["## Held slots", ""]
        for h in held:
            lines.append(f"- {h.get('slot_id')}: {h.get('headline')} — {h.get('hold_reason')} / {h.get('replacement_status')}")
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("mermaid_master_content_board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_OPERATOR.write_text("# Operator Next Actions v2.5\n\nUse the freshness-gated queues and split prompt packets. Do not render held preview slots.\n", encoding="utf-8")
    OUT_MANIFEST.write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "final_slots": len(final), "held_slots": len(held), "packets": len(packets), "preview_block_signals": signals}, indent=2), encoding="utf-8")


def main() -> None:
    config = read_json(CFG, {})
    final, held, signals = build_final_slots(config)
    packets = compile_packets(final)
    write_outputs(final, held, packets, signals)
    print(json.dumps({"final_slots": len(final), "held_slots": len(held), "packets": len(packets), "preview_block_signals": signals}, indent=2))


if __name__ == "__main__":
    main()
