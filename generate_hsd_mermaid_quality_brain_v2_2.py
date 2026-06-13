from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set
from urllib.parse import urljoin, urlparse

VERSION = "v3.3.2-mermaid-quality-brain-v2.2"
CFG_PATH = Path("config/hsd_mermaid_quality_brain_v2_2.json")
SOURCE_CFG = Path("config/hsd_multisport_source_registry_v2.json")

OUT_REPORT = Path("mermaid_quality_brain_v2_2_report.md")
OUT_MANIFEST = Path("mermaid_quality_brain_v2_2_manifest.json")
OUT_SCOUT_ALL = Path("multisport_scout_candidates_v2_2.csv")
OUT_SCOUT_FILTERED = Path("multisport_scout_candidates_filtered_v2_2.csv")
OUT_SCOUT_REJECTED = Path("multisport_rejected_candidates_v2_2.csv")
OUT_FLOORS = Path("multisport_sport_floor_report.md")
OUT_FLOORS_CSV = Path("multisport_sport_floor_status.csv")
OUT_GRAPH = Path("mermaid_classified_story_graph.csv")
OUT_BOARD = Path("mermaid_master_content_board_v2_2.md")
OUT_SLOTS = Path("mermaid_content_slots_v2_2.csv")
OUT_FEED = Path("ig_feed_queue_v2_2.csv")
OUT_STORY = Path("ig_story_queue_v2_2.csv")
OUT_THREADS = Path("threads_queue_v2_2.csv")
OUT_PROMPT_INDEX = Path("mermaid_quality_prompt_index_v2_2.csv")
OUT_OPERATOR = Path("operator_next_actions_v2_2.md")
PACKET_DIR = Path("mermaid_quality_compiled_packets_v2_2")

SCOUT_FIELDS = ["story_id", "source_id", "trust_band", "sport", "league", "title", "source_url", "candidate_type", "priority", "verification_state", "platform_fit", "notes", "quality_score", "quality_status", "quality_reason", "classified_type"]
GRAPH_FIELDS = ["story_id", "story_type", "sport", "league", "headline", "event_date", "priority", "verification_state", "source_state", "platform_fit", "asset_state", "source_ref", "notes", "quality_score", "quality_status", "quality_reason"]
SLOT_FIELDS = ["slot_id", "platform", "slot_time_et", "content_type", "headline", "league", "priority", "story_id", "status", "asset_state", "quality_score", "copy_hook", "threads_copy", "ig_caption_seed", "first_comment", "notes"]
FLOOR_FIELDS = ["league", "floor", "usable_count", "status", "shortfall", "notes"]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def low(v: Any) -> str:
    return clean(v).lower()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def story_id(*parts: Any) -> str:
    import hashlib
    return "story_" + hashlib.sha1("|".join(clean(p) for p in parts).encode("utf-8")).hexdigest()[:14]


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


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return {} if default is None else default
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {} if default is None else default


def cfg() -> Dict[str, Any]:
    return read_json(CFG_PATH, {})


def run_v21() -> None:
    if Path("generate_hsd_mermaid_quality_brain_v2_1.py").exists():
        subprocess.run([sys.executable, "generate_hsd_mermaid_quality_brain_v2_1.py"], text=True, timeout=180)


def priority_for(league: str, typ: str) -> str:
    l = clean(league).upper()
    if typ in {"breaking_or_rumor", "confirmed_breaking"}:
        return "P0"
    if l == "WNBA":
        return "P1"
    if l in {"NWSL", "WTA", "USWNT"}:
        return "P2"
    if l in {"LPGA", "VNL", "VOLLEYBALL", "FIFA WOMEN"}:
        return "P3"
    return "P4"


def junk_reason(title: str, url: str, c: Dict[str, Any]) -> str:
    t = low(title)
    if not t or len(t) < 12:
        return "missing_or_short_title"
    if t in {low(x) for x in c.get("junk_exact_titles", [])}:
        return "junk_exact_title"
    if t in {low(x) for x in c.get("team_homepage_titles", [])}:
        return "team_homepage_title"
    for term in c.get("junk_contains", []):
        if low(term) in t:
            return f"junk_contains:{term}"
    if re.search(r"/(privacy|terms|tickets|shop|store|standings|stats|players?)(/|$)", low(url)):
        return "junk_url_path"
    if len(t.split()) <= 3 and not re.search(r"\bat\b|\bvs\b|\bopen\b|\bcup\b|\bfinal\b|\bpreview\b", t):
        return "section_like_title"
    return ""


def classify_candidate(row: Dict[str, Any]) -> str:
    title = clean(row.get("title") or row.get("headline"))
    url = low(row.get("source_url") or row.get("source_ref"))
    sid = low(row.get("source_id") or row.get("source_state"))
    ctype = low(row.get("candidate_type") or row.get("story_type"))
    t = low(title)
    if "rumor" in ctype or "breaking" in ctype:
        return "breaking_or_rumor"
    if "final" in ctype or "result" in ctype or "final" in t:
        return "result_or_recap"
    if "scoreboard" in sid and (" at " in t or " vs " in t):
        return "preview_event"
    if ("schedule" in ctype or "schedule" in url or "scoreboard" in sid) and (" at " in t or " vs " in t):
        return "preview_event"
    if "/news/" in url or ctype == "news":
        return "official_news_article"
    if "schedule" in ctype or "schedule" in url or "tournament" in url:
        return "schedule_reference_review"
    return "official_story_review"


def score_candidate(row: Dict[str, Any], c: Dict[str, Any]) -> Tuple[int, str, str, str]:
    title = clean(row.get("title") or row.get("headline"))
    url = clean(row.get("source_url") or row.get("source_ref"))
    league = clean(row.get("league"))
    typ = classify_candidate(row)
    jr = junk_reason(title, url, c)
    if jr:
        return 0, "hold", jr, typ
    score = 10
    reasons = []
    league_bonus = {"WNBA": 18, "NWSL": 16, "WTA": 15, "USWNT": 14, "LPGA": 13, "VNL": 12, "Volleyball": 12, "FIFA Women": 11, "NCAA Softball": 10}.get(league, 6)
    score += league_bonus
    reasons.append(f"league:{league}")
    if clean(row.get("trust_band")).startswith("green") or clean(row.get("verification_state")) in {"official_source", "verified_score_contract", "slate_selected"}:
        score += 16
        reasons.append("trusted")
    if typ == "preview_event":
        score += 30
        reasons.append("preview_event")
    elif typ == "official_news_article":
        score += 24
        reasons.append("official_article")
    elif typ == "result_or_recap":
        score += 26
        reasons.append("result")
    elif typ == "breaking_or_rumor":
        score += 18
        reasons.append("breaking_review")
    elif typ == "schedule_reference_review":
        score += 4
        reasons.append("schedule_reference")
    if len(title) >= 35:
        score += 8
        reasons.append("headline_length")
    hits = [kw for kw in c.get("story_signal_keywords", []) if low(kw) in low(title)]
    if hits:
        score += min(18, 6 * len(hits))
        reasons.append("signals:" + ",".join(hits[:3]))
    status = "use" if score >= int(c.get("min_quality_score", 50)) else "review" if score >= 35 else "hold"
    return score, status, "; ".join(reasons), typ


def supplemental_scout(c: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not c.get("source_balancing", {}).get("supplemental_fetch_enabled", True):
        return []
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception:
        return []
    source_cfg = read_json(SOURCE_CFG, {"sources": []})
    out = []
    max_links = int(c.get("source_balancing", {}).get("max_links_per_source", 10))
    timeout = int(c.get("source_balancing", {}).get("timeout_seconds", 12))
    for src in source_cfg.get("sources", []):
        url = clean(src.get("url"))
        if not url:
            continue
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "HSDMermaidQualityBrain/2.2"})
            if r.status_code >= 400 or not r.text:
                continue
            # ESPN JSON scoreboard support.
            if r.text.strip().startswith("{"):
                try:
                    data = r.json()
                    for ev in data.get("events", [])[:max_links]:
                        title = clean(ev.get("name") or ev.get("shortName"))
                        if title:
                            out.append(make_scout(src, title, url, "scoreboard_crosscheck", "supplemental_json_scoreboard"))
                    continue
                except Exception:
                    pass
            soup = BeautifulSoup(r.text, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                title = clean(a.get_text(" "))
                href = urljoin(url, a.get("href"))
                if href in seen:
                    continue
                seen.add(href)
                if not title:
                    continue
                # Keep candidates first, filter later.
                out.append(make_scout(src, title, href, clean(src.get("use")), "supplemental_html_link"))
                if len([x for x in out if x.get("source_id") == src.get("source_id")]) >= max_links:
                    break
        except Exception:
            continue
    return out


def make_scout(src: Dict[str, Any], title: str, url: str, candidate_type: str, note: str) -> Dict[str, Any]:
    league = clean(src.get("league"))
    return {
        "story_id": story_id(src.get("source_id"), title, url),
        "source_id": clean(src.get("source_id")),
        "trust_band": clean(src.get("trust_band")),
        "sport": clean(src.get("sport")),
        "league": league,
        "title": clean(title),
        "source_url": clean(url),
        "candidate_type": clean(candidate_type),
        "priority": priority_for(league, "news"),
        "verification_state": "official_source" if clean(src.get("trust_band")).startswith("green") else "review",
        "platform_fit": "Threads; IG Stories; IG Feed if strong",
        "notes": note,
    }


def build_scout(c: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows = []
    seen = set()
    for source in ["multisport_scout_candidates.csv", "multisport_scout_candidates_filtered.csv", "multisport_scout_candidates_v2_2.csv"]:
        for r in read_csv(source):
            key = clean(r.get("story_id")) or story_id(r.get("source_id"), r.get("title"), r.get("source_url"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(r))
    for r in supplemental_scout(c):
        key = clean(r.get("story_id"))
        if key not in seen:
            seen.add(key)
            rows.append(r)
    scored, rejected = [], []
    for r in rows:
        score, status, reason, typ = score_candidate(r, c)
        rr = dict(r)
        rr.update({"quality_score": score, "quality_status": status, "quality_reason": reason, "classified_type": typ})
        if status in {"use", "review"}:
            scored.append(rr)
        else:
            rejected.append(rr)
    scored.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("league", ""), r.get("title", "")))
    caps = c.get("league_caps", {})
    kept, league_counts = [], {}
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
    write_csv(OUT_SCOUT_ALL, rows, SCOUT_FIELDS)
    write_csv(OUT_SCOUT_FILTERED, kept, SCOUT_FIELDS)
    write_csv(OUT_SCOUT_REJECTED, rejected, SCOUT_FIELDS)
    # Also alias the filtered/rejected names used by v2.1 artifact inspection.
    write_csv("multisport_scout_candidates_filtered.csv", kept, SCOUT_FIELDS)
    write_csv("multisport_rejected_candidates.csv", rejected, SCOUT_FIELDS)
    return rows, kept, rejected


def build_floor_report(filtered: List[Dict[str, Any]], c: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    counts = {}
    for r in filtered:
        league = clean(r.get("league")) or "Unknown"
        counts[league] = counts.get(league, 0) + 1
    for league, floor in c.get("sport_floors", {}).items():
        have = counts.get(league, 0)
        short = max(0, int(floor) - have)
        rows.append({"league": league, "floor": floor, "usable_count": have, "status": "PASS" if short == 0 else "SHORT", "shortfall": short, "notes": "No story invented; shortfall means source extraction needs more/better candidates."})
    write_csv(OUT_FLOORS_CSV, rows, FLOOR_FIELDS)
    lines = ["# Multi-Sport Sport Floor Report", "", f"Generated: {now_iso()}", f"Version: {VERSION}", ""]
    for r in rows:
        lines.append(f"- {r['league']}: {r['usable_count']}/{r['floor']} — {r['status']}")
    OUT_FLOORS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def add_graph_row(out: List[Dict[str, Any]], seen: Set[str], row: Dict[str, Any]) -> None:
    sid = clean(row.get("story_id")) or story_id(row.get("headline"), row.get("league"), row.get("source_ref"))
    if sid in seen:
        return
    seen.add(sid)
    rr = {k: row.get(k, "") for k in GRAPH_FIELDS}
    rr["story_id"] = sid
    out.append(rr)


def build_graph(filtered: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out, seen = [], set()
    for r in read_csv("mermaid_story_graph.csv") + read_csv("mermaid_quality_story_graph.csv"):
        stype = clean(r.get("story_type"))
        headline = clean(r.get("headline"))
        if not headline:
            continue
        if stype == "multisport_news":
            continue
        score = clean(r.get("quality_score")) or "78"
        add_graph_row(out, seen, {**r, "quality_score": score, "quality_status": "use", "quality_reason": clean(r.get("quality_reason")) or "core story graph"})
    for r in filtered:
        typ = clean(r.get("classified_type")) or classify_candidate(r)
        headline = clean(r.get("title"))
        add_graph_row(out, seen, {
            "story_id": clean(r.get("story_id")),
            "story_type": typ,
            "sport": clean(r.get("sport")),
            "league": clean(r.get("league")),
            "headline": headline,
            "event_date": "",
            "priority": priority_for(r.get("league"), typ),
            "verification_state": clean(r.get("verification_state")) or "official_source",
            "source_state": clean(r.get("source_id")),
            "platform_fit": clean(r.get("platform_fit")),
            "asset_state": "needs_assets" if typ != "preview_event" else "logos_needed",
            "source_ref": clean(r.get("source_url")),
            "notes": "Quality Brain v2.2 classified scout candidate.",
            "quality_score": r.get("quality_score", ""),
            "quality_status": r.get("quality_status", ""),
            "quality_reason": r.get("quality_reason", ""),
        })
    out.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", ""), r.get("headline", "")))
    write_csv(OUT_GRAPH, out, GRAPH_FIELDS)
    write_csv("mermaid_story_graph.csv", out, GRAPH_FIELDS)
    return out


def copy_for(row: Dict[str, Any]) -> Dict[str, str]:
    h, league, typ = clean(row.get("headline")), clean(row.get("league")), low(row.get("story_type"))
    if typ == "preview_event" or "preview" in typ:
        return {"hook": f"{h}: matchup on the board.", "threads": f"{h}\n\nWhich side are you watching closest?", "caption": f"{h}\n\nTonight’s watch point: pace, execution, and who owns the key moments.", "first": "Who needs this one more?"}
    if "result" in typ or "recap" in typ:
        return {"hook": f"{h}: circle this result.", "threads": f"{h}\n\nBiggest takeaway?", "caption": f"{h}\n\nA result worth putting on the board.", "first": "What was the swing moment?"}
    if "news" in typ:
        return {"hook": f"{league}: {h}", "threads": f"{h}\n\nThis is on the HSD board. Are we underrating it?", "caption": f"{h}\n\nA women’s sports story to keep on the radar.", "first": "What’s the angle people are missing?"}
    return {"hook": f"{league}: {h}", "threads": f"{h}\n\nWhat are you watching here?", "caption": f"{h}\n\nHSD is tracking the bigger picture.", "first": "Are we underrating this story?"}


def pick_slots(graph: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    usable = [r for r in graph if clean(r.get("quality_status")) in {"use", "review"} and int(r.get("quality_score") or 0) >= 50]
    used_ig: Set[str] = set()
    def choose(pred, allow_dup=False):
        rows = [r for r in usable if pred(r)]
        rows.sort(key=lambda r: (-int(r.get("quality_score") or 0), r.get("priority", "P9"), r.get("league", "")))
        for r in rows:
            if allow_dup or r.get("story_id") not in used_ig:
                return r
        return None
    def non_wnba(r): return clean(r.get("league")).upper() not in {"WNBA", ""}
    def preview(r): return clean(r.get("story_type")) == "preview_event" or "preview" in low(r.get("story_type")) or "slate" in low(r.get("story_type"))
    def result(r): return "result" in low(r.get("story_type")) or "final" in low(r.get("story_type")) or "recap" in low(r.get("story_type"))
    specs = [
        ("threads_morning", "Threads", "9:00 AM", lambda r: non_wnba(r) and clean(r.get("story_type")) in {"official_news_article", "preview_event"}, True),
        ("ig_feed_noon", "IG Feed", "12:00 PM", lambda r: int(r.get("quality_score") or 0) >= 70 and clean(r.get("story_type")) in {"official_news_article", "result_or_recap", "preview_event", "ig_story_final_scores", "manual_packet"}, False),
        ("ig_stories_rolling_1", "IG Stories", "10:30 AM", lambda r: non_wnba(r) or int(r.get("quality_score") or 0) >= 70, False),
        ("ig_stories_rolling_2", "IG Stories", "12:30 PM", lambda r: clean(r.get("story_type")) in {"official_news_article", "preview_event", "result_or_recap"}, False),
        ("ig_feed_evening_preview", "IG Feed", "4:45 PM", preview, False),
        ("threads_live", "Threads", "7:00-11:30 PM", preview, True),
        ("nightcap", "Threads", "11:30 PM", result, True),
    ]
    slots = []
    for sid, platform, time_et, pred, allow_dup in specs:
        r = choose(pred, allow_dup)
        if not r:
            slots.append({"slot_id": sid, "platform": platform, "slot_time_et": time_et, "status": "skip_no_quality_story", "notes": "No quality story fit this slot."})
            continue
        if platform != "Threads":
            used_ig.add(r.get("story_id"))
        cp = copy_for(r)
        slots.append({"slot_id": sid, "platform": platform, "slot_time_et": time_et, "content_type": r.get("story_type"), "headline": r.get("headline"), "league": r.get("league"), "priority": r.get("priority"), "story_id": r.get("story_id"), "status": "ready_with_review", "asset_state": r.get("asset_state"), "quality_score": r.get("quality_score"), "copy_hook": cp["hook"], "threads_copy": cp["threads"], "ig_caption_seed": cp["caption"], "first_comment": cp["first"], "notes": r.get("quality_reason")})
    write_csv(OUT_SLOTS, slots, SLOT_FIELDS)
    write_csv("mermaid_content_slots_v2.csv", slots, SLOT_FIELDS)
    write_csv(OUT_FEED, [s for s in slots if s.get("platform") == "IG Feed" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_STORY, [s for s in slots if s.get("platform") == "IG Stories" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv(OUT_THREADS, [s for s in slots if s.get("platform") == "Threads" and s.get("status") == "ready_with_review"], SLOT_FIELDS)
    write_csv("ig_feed_queue_v2.csv", read_csv(OUT_FEED), SLOT_FIELDS)
    write_csv("ig_story_queue_v2.csv", read_csv(OUT_STORY), SLOT_FIELDS)
    write_csv("threads_queue_v2.csv", read_csv(OUT_THREADS), SLOT_FIELDS)
    return slots


def compile_packets(graph: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if PACKET_DIR.exists():
        shutil.rmtree(PACKET_DIR)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    ids = {clean(s.get("story_id")) for s in slots if clean(s.get("story_id"))}
    idx = []
    for r in [g for g in graph if clean(g.get("story_id")) in ids]:
        sid = clean(r.get("story_id"))
        p = PACKET_DIR / sid
        p.mkdir(parents=True, exist_ok=True)
        cp = copy_for(r)
        packet = {"version": VERSION, "story": r, "quality_score": r.get("quality_score"), "locked_facts": {"headline": r.get("headline"), "league": r.get("league"), "verification_state": r.get("verification_state"), "source_ref": r.get("source_ref")}}
        render = {"version": VERSION, "story_id": sid, "format_policy": "exact assets only; no fake players/logos/stats", "copy_hook": cp["hook"], "status": "ready_with_review"}
        prompt = f"# HSD Quality Brain v2.2 Graphics Prompt\n\nStory: {r.get('headline')}\nLeague: {r.get('league')}\nType: {r.get('story_type')}\nVerification: {r.get('verification_state')}\n\nCreate a premium Her Sports Daily social asset. Use HSD voice: smart, fast, confident, women’s sports desk.\n\nLocked facts:\n- Headline: {r.get('headline')}\n- Source/ref: {r.get('source_ref')}\n\nDisplay direction:\n- {cp['hook']}\n- Keep public copy clean and editorial.\n- Player graphics are required when appropriate, but only with exact approved player assets.\n- Do not invent faces, jerseys, logos, stats, quotes, or results.\n\nCTA: {cp['first']}\n"
        (p / "content_packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
        (p / "render_plan.json").write_text(json.dumps(render, indent=2), encoding="utf-8")
        (p / "00_GRAPHICS_PROMPT.md").write_text(prompt, encoding="utf-8")
        (p / "02_COPY_DESK.md").write_text(cp["caption"] + "\n", encoding="utf-8")
        (p / "03_THREADS_COPY.md").write_text(cp["threads"] + "\n", encoding="utf-8")
        (p / "04_FIRST_COMMENT.md").write_text(cp["first"] + "\n", encoding="utf-8")
        idx.append({"story_id": sid, "headline": r.get("headline"), "league": r.get("league"), "story_type": r.get("story_type"), "quality_score": r.get("quality_score"), "packet_dir": p.as_posix(), "graphics_prompt": (p / "00_GRAPHICS_PROMPT.md").as_posix(), "threads_copy": (p / "03_THREADS_COPY.md").as_posix()})
    write_csv(OUT_PROMPT_INDEX, idx, ["story_id", "headline", "league", "story_type", "quality_score", "packet_dir", "graphics_prompt", "threads_copy"])
    write_csv("mermaid_compiled_packet_index.csv", idx, ["story_id", "headline", "league", "story_type", "quality_score", "packet_dir", "graphics_prompt", "threads_copy"])
    if Path("mermaid_compiled_packets").exists():
        shutil.rmtree("mermaid_compiled_packets")
    shutil.copytree(PACKET_DIR, "mermaid_compiled_packets")
    return idx


def write_board(slots: List[Dict[str, Any]], graph: List[Dict[str, Any]], filtered: List[Dict[str, Any]], rejected: List[Dict[str, Any]], floors: List[Dict[str, Any]], packets: List[Dict[str, Any]]) -> None:
    lines = ["# HSD Mermaid Master Content Board v2.2", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## Counts", "", f"- classified story graph rows: {len(graph)}", f"- filtered scout candidates: {len(filtered)}", f"- rejected scout candidates: {len(rejected)}", f"- quality slots: {len(slots)}", f"- compiled packets: {len(packets)}", "", "## Sport floors", ""]
    for f in floors:
        lines.append(f"- {f['league']}: {f['usable_count']}/{f['floor']} — {f['status']}")
    lines += ["", "## Slots", ""]
    for s in slots:
        lines += [f"### {s.get('slot_id')} — {s.get('platform')} / {s.get('slot_time_et')}", f"- Status: {s.get('status')}", f"- Headline: {s.get('headline') or '—'}", f"- League: {s.get('league') or '—'}", f"- Type: {s.get('content_type') or '—'}", f"- Score: {s.get('quality_score') or '—'}", f"- Hook: {s.get('copy_hook') or '—'}", ""]
    OUT_BOARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("mermaid_master_content_board.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(all_rows, filtered, rejected, floors, graph, slots, packets) -> None:
    lines = ["# Mermaid Quality Brain v2.2 Report", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", "## What changed", "", "- Classifies scoreboard matchups as preview events instead of news.", "- Runs supplemental source scan per league before filtering.", "- Enforces sport floors and reports shortfalls instead of letting WNBA/WTA swallow the board.", "- Rebuilds queues and prompt packets with HSD-style hooks.", "", "## Counts", "", f"- total scout candidates considered: {len(all_rows)}", f"- filtered usable/review candidates: {len(filtered)}", f"- rejected/held candidates: {len(rejected)}", f"- classified graph rows: {len(graph)}", f"- content slots: {len(slots)}", f"- compiled packets: {len(packets)}", "", "## Top filtered candidates", ""]
    for r in filtered[:25]:
        lines.append(f"- {r.get('quality_score')} / {r.get('classified_type')} / **{r.get('league')}** — {r.get('title')}")
    lines += ["", "## Rejected examples", ""]
    for r in rejected[:20]:
        lines.append(f"- {r.get('quality_reason')} — {r.get('title')}")
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Make this visible in the existing artifact path.
    prev = Path("mermaid_upper_echelon_report.md").read_text(encoding="utf-8", errors="replace") if Path("mermaid_upper_echelon_report.md").exists() else "# HSD Mermaid Upper Echelon Report\n"
    Path("mermaid_upper_echelon_report.md").write_text(prev + "\n---\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def write_operator(slots: List[Dict[str, Any]], floors: List[Dict[str, Any]]) -> None:
    lines = ["# Operator Next Actions v2.2", "", f"Generated: {now_iso()}", "", "## Do next", ""]
    short = [f for f in floors if f.get("status") == "SHORT"]
    if short:
        lines.append("1. Source extraction still has floor shortfalls: " + ", ".join(f"{f['league']} ({f['shortfall']})" for f in short))
    else:
        lines.append("1. Sport floors passed for available configured sources.")
    lines.append("2. Use the v2.2 quality queues and compiled packets for handoff.")
    lines.append("3. Keep player-led graphics tied to registry-approved assets only.")
    lines += ["", "## Ready slots", ""]
    for s in slots:
        if s.get("status") == "ready_with_review":
            lines.append(f"- {s.get('platform')} / {s.get('slot_time_et')}: {s.get('headline')}")
    OUT_OPERATOR.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    run_v21()
    c = cfg()
    all_rows, filtered, rejected = build_scout(c)
    floors = build_floor_report(filtered, c)
    graph = build_graph(filtered)
    slots = pick_slots(graph)
    packets = compile_packets(graph, slots)
    write_board(slots, graph, filtered, rejected, floors, packets)
    write_report(all_rows, filtered, rejected, floors, graph, slots, packets)
    write_operator(slots, floors)
    manifest = {"version": VERSION, "generated_at": now_iso(), "total_scout_candidates": len(all_rows), "filtered_candidates": len(filtered), "rejected_candidates": len(rejected), "classified_graph_rows": len(graph), "slots": len(slots), "packets": len(packets)}
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
