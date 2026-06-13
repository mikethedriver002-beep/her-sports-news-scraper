
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

VERSION = "v3.3.0-mermaid-prompt-compiler-v2"
IN_GRAPH = "mermaid_story_graph.csv"
OUT_DIR = Path("mermaid_compiled_packets")
OUT_INDEX = "mermaid_compiled_packet_index.csv"
OUT_MD = "mermaid_prompt_compiler_report.md"
FIELDS = ["packet_id","story_id","headline","league","story_type","packet_dir","graphics_prompt","copy_desk","threads_copy","first_comment"]

BANNED = ["Verified Final", "BUNDLE LOCKED FACTS", "source-safe context", "graphics-safe context", "Do not alter", "What stood out?"]

def prompt_for(row: Dict[str,str]) -> str:
    story_type = clean(row.get("story_type"))
    league = clean(row.get("league"))
    headline = clean(row.get("headline"))
    if "preview" in story_type.lower() or "slate" in story_type.lower():
        return f"""Create a premium HSD preview asset for {league}.\nLocked headline: {headline}\nUse pregame language only. Do not use postgame/result language. Show why this matters, not just the schedule. Use exact assets only. No generated players or logos.\n"""
    if "final" in story_type.lower() or "result" in story_type.lower():
        return f"""Create a premium HSD result asset for {league}.\nLocked headline: {headline}\nUse verified final-score/result framing only if the result source is verified. Use exact team logos. Player images only if exact and approved.\n"""
    if "rumor" in story_type.lower() or "breaking" in story_type.lower():
        return f"""Create source-labeled breaking/news copy for HSD.\nClaim: {headline}\nDo not present as confirmed unless verification_state says confirmed_official. Use attribution and review language.\n"""
    return f"""Create a premium HSD women’s sports asset.\nLocked headline: {headline}\nLeague: {league}\nUse exact facts only and keep display copy editorial, clean, and social-native.\n"""

def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rows = []
    for story in read_csv(IN_GRAPH):
        packet_id = "packet_" + story["story_id"].replace("story_","")
        pdir = OUT_DIR / packet_id
        pdir.mkdir(exist_ok=True)
        content_packet = {
            "packet_id": packet_id,
            "version": VERSION,
            "story": story,
            "locked_facts": {
                "headline": story.get("headline"),
                "league": story.get("league"),
                "sport": story.get("sport"),
                "event_date": story.get("event_date"),
                "verification_state": story.get("verification_state")
            },
            "platform_fit": story.get("platform_fit"),
            "asset_state": story.get("asset_state")
        }
        render_plan = {
            "packet_id": packet_id,
            "story_id": story.get("story_id"),
            "recommended_formats": story.get("platform_fit"),
            "graphics_policy": "exact assets only; no generated players/logos",
            "prompt_family": story.get("story_type"),
            "status": "ready_with_review"
        }
        graphics_prompt = prompt_for(story)
        for b in BANNED:
            graphics_prompt = graphics_prompt.replace(b, "")
        copy_desk = f"# Copy Desk\n\nHeadline: {story.get('headline')}\n\nCaption angle: {story.get('notes') or story.get('headline')}\n\nCTA: Tap in with HSD.\n"
        threads = f"{story.get('headline')}\n\nWhat are you watching here?"
        first_comment = "What’s the angle people are missing?"
        (pdir / "content_packet.json").write_text(json.dumps(content_packet, indent=2), encoding="utf-8")
        (pdir / "render_plan.json").write_text(json.dumps(render_plan, indent=2), encoding="utf-8")
        (pdir / "00_PROMPT_TO_PASTE.md").write_text(graphics_prompt, encoding="utf-8")
        (pdir / "02_COPY_DESK.md").write_text(copy_desk, encoding="utf-8")
        (pdir / "03_THREADS_COPY.md").write_text(threads + "\n", encoding="utf-8")
        (pdir / "04_FIRST_COMMENT.md").write_text(first_comment + "\n", encoding="utf-8")
        rows.append({
            "packet_id": packet_id,
            "story_id": story.get("story_id"),
            "headline": story.get("headline"),
            "league": story.get("league"),
            "story_type": story.get("story_type"),
            "packet_dir": pdir.as_posix(),
            "graphics_prompt": (pdir / "00_PROMPT_TO_PASTE.md").as_posix(),
            "copy_desk": (pdir / "02_COPY_DESK.md").as_posix(),
            "threads_copy": (pdir / "03_THREADS_COPY.md").as_posix(),
            "first_comment": (pdir / "04_FIRST_COMMENT.md").as_posix()
        })
    write_csv(OUT_INDEX, rows, FIELDS)
    lines = ["# HSD Mermaid Prompt Compiler v2", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- packets compiled: {len(rows)}", ""]
    for r in rows[:30]:
        lines.append(f"- {r['league']} / {r['story_type']} — {r['headline']}")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"compiled_packets": len(rows)}, indent=2))

if __name__ == "__main__":
    main()
