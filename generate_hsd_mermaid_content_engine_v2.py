
from __future__ import annotations
import csv, json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Iterable

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"

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
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def read_json(path: str | Path, default=None):
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default

def story_id(*parts: Any) -> str:
    h = hashlib.sha1("|".join(clean(p) for p in parts).encode("utf-8")).hexdigest()[:14]
    return "story_" + h

def score_priority(league: str, kind: str, source_state: str = "") -> str:
    l = clean(league).upper()
    if kind in {"breaking", "rumor_confirmed"}:
        return "P0"
    if l == "WNBA":
        return "P1"
    if l in {"WTA", "NWSL"}:
        return "P2"
    if l in {"LPGA", "VNL", "VOLLEYBALL"}:
        return "P3"
    return "P4"

VERSION = "v3.3.0-mermaid-content-engine-v2"
IN_GRAPH = "mermaid_story_graph.csv"
OUT_BOARD = "mermaid_master_content_board.md"
OUT_SLOTS = "mermaid_content_slots_v2.csv"
OUT_IG_FEED = "ig_feed_queue_v2.csv"
OUT_IG_STORY = "ig_story_queue_v2.csv"
OUT_THREADS = "threads_queue_v2.csv"
OUT_BREAKING = "breaking_news_queue.csv"
OUT_RUMOR = "rumor_watch_queue.csv"
OUT_JSON = "mermaid_content_engine_manifest.json"

FIELDS = ["slot_id","platform","slot_time_et","content_type","headline","league","priority","story_id","status","asset_state","notes"]

SLOTS = [
    ("threads_morning", "Threads", "9:00 AM", ["multisport_news","preview","slate_item","ig_story_final_scores"]),
    ("ig_feed_noon", "IG Feed", "12:00 PM", ["breaking_or_rumor","result","manual_packet","multisport_news"]),
    ("ig_stories", "IG Stories", "10:30 AM / rolling", ["ig_story_final_scores","breaking_or_rumor","multisport_news"]),
    ("ig_feed_evening_preview", "IG Feed", "4:45 PM", ["preview","slate_item"]),
    ("threads_live", "Threads", "7:00-11:30 PM", ["preview","live_threads","slate_item"]),
    ("nightcap", "Threads", "11:30 PM", ["result","ig_story_final_scores","breaking_or_rumor"]),
]

def pick_for_slot(stories: List[Dict[str,str]], allowed: List[str], used: set, platform: str) -> Dict[str,str] | None:
    candidates = []
    for s in stories:
        if s["story_id"] in used and platform != "Threads":
            continue
        if s["story_type"] not in allowed:
            continue
        if platform.lower() not in clean(s.get("platform_fit")).lower() and "Threads" != platform:
            # Allow some editorial routing anyway for IG Story/Feed if graph says broadly fit.
            if platform == "IG Feed" and "IG Feed" not in clean(s.get("platform_fit")):
                continue
            if platform == "IG Stories" and "IG Stories" not in clean(s.get("platform_fit")):
                continue
        candidates.append(s)
    candidates.sort(key=lambda s: (s.get("priority","P9"), s.get("league",""), s.get("headline","")))
    return candidates[0] if candidates else None

def main() -> None:
    stories = read_csv(IN_GRAPH)
    used = set()
    slots = []
    for slot_id, platform, time_et, allowed in SLOTS:
        s = pick_for_slot(stories, allowed, used, platform)
        if s:
            if platform != "Threads":
                used.add(s["story_id"])
            slots.append({
                "slot_id": slot_id,
                "platform": platform,
                "slot_time_et": time_et,
                "content_type": s.get("story_type"),
                "headline": s.get("headline"),
                "league": s.get("league"),
                "priority": s.get("priority"),
                "story_id": s.get("story_id"),
                "status": "ready_with_review",
                "asset_state": s.get("asset_state"),
                "notes": s.get("notes")
            })
        else:
            slots.append({
                "slot_id": slot_id,
                "platform": platform,
                "slot_time_et": time_et,
                "content_type": "",
                "headline": "",
                "league": "",
                "priority": "",
                "story_id": "",
                "status": "skip_no_strong_angle",
                "asset_state": "",
                "notes": "No suitable story atom for this slot."
            })
    write_csv(OUT_SLOTS, slots, FIELDS)
    write_csv(OUT_IG_FEED, [s for s in slots if s["platform"]=="IG Feed" and s["status"].startswith("ready")], FIELDS)
    write_csv(OUT_IG_STORY, [s for s in slots if s["platform"]=="IG Stories" and s["status"].startswith("ready")], FIELDS)
    write_csv(OUT_THREADS, [s for s in slots if s["platform"]=="Threads" and s["status"].startswith("ready")], FIELDS)
    write_csv(OUT_BREAKING, [s for s in stories if s["story_type"]=="breaking_or_rumor" and s["verification_state"] in {"confirmed_official","corroborated_report"}], list(stories[0].keys()) if stories else ["story_id"])
    write_csv(OUT_RUMOR, [s for s in stories if s["story_type"]=="breaking_or_rumor"], list(stories[0].keys()) if stories else ["story_id"])

    lines = ["# HSD Mermaid Master Content Board", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- story atoms: {len(stories)}", f"- ready slots: {sum(1 for s in slots if s['status'].startswith('ready'))}", ""]
    for s in slots:
        lines += [
            f"## {s['slot_id']} — {s['platform']} / {s['slot_time_et']}",
            f"- Status: {s['status']}",
            f"- Headline: {s['headline'] or '—'}",
            f"- League: {s['league'] or '—'}",
            f"- Type: {s['content_type'] or '—'}",
            f"- Notes: {s['notes'] or '—'}",
            ""
        ]
    Path(OUT_BOARD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "story_atoms": len(stories), "slots": len(slots)}, indent=2), encoding="utf-8")
    print(json.dumps({"story_atoms": len(stories), "slots": len(slots)}, indent=2))

if __name__ == "__main__":
    main()
