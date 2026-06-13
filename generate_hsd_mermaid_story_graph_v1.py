
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

VERSION = "v3.3.0-mermaid-story-graph-v1"
OUT_CSV = "mermaid_story_graph.csv"
OUT_JSONL = "mermaid_story_graph.jsonl"
OUT_MD = "mermaid_story_graph_report.md"
FIELDS = ["story_id","story_type","sport","league","headline","event_date","priority","verification_state","source_state","platform_fit","asset_state","source_ref","notes"]

def add(rows, seen, story_type, sport, league, headline, event_date="", verification_state="review", source_state="", platform_fit="", asset_state="", source_ref="", notes=""):
    if not clean(headline):
        return
    sid = story_id(story_type, league, headline, event_date, source_ref)
    if sid in seen:
        return
    seen.add(sid)
    rows.append({
        "story_id": sid,
        "story_type": story_type,
        "sport": clean(sport),
        "league": clean(league),
        "headline": clean(headline),
        "event_date": clean(event_date),
        "priority": score_priority(league, story_type, source_state),
        "verification_state": clean(verification_state),
        "source_state": clean(source_state),
        "platform_fit": clean(platform_fit),
        "asset_state": clean(asset_state),
        "source_ref": clean(source_ref),
        "notes": clean(notes)
    })

def main() -> None:
    rows = []; seen = set()
    # Results contract
    for r in read_csv("results_contract_v2.csv"):
        elig = clean(r.get("content_eligibility"))
        kind = clean(r.get("row_kind"))
        if elig == "eligible":
            add(rows, seen, kind or "result", r.get("sport"), r.get("league"), r.get("headline"), r.get("event_date_local"), "verified_score_contract", r.get("source_id"), "IG Feed; IG Stories; Threads", "score_assets_needed", r.get("source_url"), r.get("freshness_reason"))
        elif kind == "live":
            add(rows, seen, "live_threads", r.get("sport"), r.get("league"), r.get("headline"), r.get("event_date_local"), "live_review", r.get("source_id"), "Threads", "text_only", r.get("source_url"), "Live game held from result graphics.")
    # Daily slate
    for r in read_csv("daily_slate_plan.csv"):
        add(rows, seen, clean(r.get("content_type")) or "slate_item", "", "", r.get("headline"), r.get("event_date"), "slate_selected", r.get("source_type"), "IG Feed; Threads", "review", r.get("source_url"), r.get("reason"))
    # Final score story
    for r in read_csv("ig_story_results_queue.csv"):
        add(rows, seen, "ig_story_final_scores", "basketball", "WNBA", r.get("headline") or "Last Night in the W", "", "verified_final_scores", "final_score_stories", "IG Stories; Threads", "ready_with_review", "", "Final-score story pack item.")
    # Manual workflow
    for r in read_csv("manual_workflow_content_packets.csv"):
        add(rows, seen, r.get("story_type") or "manual_packet", r.get("sport"), r.get("league"), r.get("headline"), r.get("event_date"), r.get("content_readiness") or "review", r.get("source_type"), r.get("platform_targets"), "manual_workflow_pack", r.get("source_urls"), r.get("angle"))
    # Multi-sport scout
    for r in read_csv("multisport_scout_candidates.csv"):
        add(rows, seen, "multisport_news", r.get("sport"), r.get("league"), r.get("title"), "", r.get("verification_state"), r.get("source_id"), r.get("platform_fit"), "needs_assets", r.get("source_url"), r.get("notes"))
    # Rumor/social desk
    for r in read_csv("social_rumor_candidates.csv"):
        add(rows, seen, "breaking_or_rumor", r.get("sport"), r.get("league"), r.get("claim_text"), "", r.get("verification_state"), r.get("publish_lane"), "Threads; IG Stories if verified", "text_or_source_card", r.get("source_url"), r.get("required_next_step"))
    rows.sort(key=lambda r: (r["priority"], r["league"], r["story_type"], r["headline"]))
    write_csv(OUT_CSV, rows, FIELDS)
    Path(OUT_JSONL).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")
    lines = ["# HSD Mermaid Story Graph", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- stories: {len(rows)}", ""]
    by_league = {}
    for r in rows:
        by_league[r["league"] or "Unknown"] = by_league.get(r["league"] or "Unknown", 0) + 1
    lines += ["## By league", ""]
    lines += [f"- {k}: {v}" for k,v in sorted(by_league.items())]
    lines += ["", "## Top stories", ""]
    for r in rows[:30]:
        lines.append(f"- {r['priority']} / {r['story_type']} / **{r['league']}** — {r['headline']} [{r['verification_state']}]")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"story_graph_rows": len(rows)}, indent=2))

if __name__ == "__main__":
    main()
