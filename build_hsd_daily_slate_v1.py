
from __future__ import annotations
import csv, json, re, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

VERSION = "hsd-daily-slate-v3.1-dedupe-caps"
OUT_CSV = Path("daily_slate_plan.csv")
OUT_MD = Path("daily_slate_plan.md")
FIELDS = ["slot_rank","content_type","source_type","headline","event_date","priority","eligibility","reason","source_id","source_url"]

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()
def norm(v: str) -> str:
    v = clean(v).lower()
    v = re.sub(r"[^a-z0-9]+", " ", v)
    return re.sub(r"\s+", " ", v).strip()
def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists(): return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))
def load_config() -> Dict[str, Any]:
    p = Path("config/daily_slate.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"max_posts":{"balanced":3},"caps":{"breaking":1,"result":2,"preview":1,"feature":1}}
def add_item(items: list, seen: set, item: dict):
    key = (item["content_type"], norm(item["headline"]), item.get("event_date",""))
    if key in seen: return
    seen.add(key); items.append(item)
def main() -> None:
    cfg = load_config()
    volume = clean(os.environ.get("HSD_CONTENT_VOLUME", "balanced"))
    max_posts = int(cfg.get("max_posts", {}).get(volume, 3))
    caps = cfg.get("caps", {"breaking":1, "result":2, "preview":1, "feature":1})
    items, seen = [], set()
    for r in read_csv("story_candidates_manual.csv"):
        if r.get("publish_eligible") == "Yes":
            add_item(items, seen, {"content_type": r.get("story_kind","breaking"), "source_type":"manual", "headline": r.get("title") or r.get("source_url"), "event_date":"", "priority":r.get("priority","P2"), "eligibility":"eligible", "reason":r.get("reason","manual"), "source_id":r.get("story_id",""), "source_url":r.get("canonical_url") or r.get("source_url")})
    for r in read_csv("story_candidates_discovery.csv"):
        if r.get("publish_eligible") == "Yes":
            add_item(items, seen, {"content_type":"breaking", "source_type":"discovery", "headline":r.get("title"), "event_date":"", "priority":"P2", "eligibility":"eligible", "reason":r.get("reason","discovery"), "source_id":r.get("story_id",""), "source_url":r.get("canonical_url")})
    for r in read_csv("results_contract_v2.csv"):
        if r.get("content_eligibility") == "eligible":
            ctype = "result" if r.get("row_kind") == "result" else "preview" if r.get("row_kind") == "preview" else "feature"
            add_item(items, seen, {"content_type":ctype, "source_type":"results_contract", "headline":r.get("headline"), "event_date":r.get("event_date_local"), "priority":"P1" if ctype=="result" else "P2", "eligibility":"eligible", "reason":r.get("freshness_reason","results"), "source_id":r.get("event_id",""), "source_url":r.get("source_url","")})
    order = {"breaking":0, "result":1, "preview":2, "feature":3}
    items = sorted(items, key=lambda x: (order.get(x["content_type"],9), x.get("priority","P9"), x.get("event_date",""), x.get("headline","")))
    selected, cap_counts = [], {}
    for item in items:
        c = item["content_type"]
        if cap_counts.get(c,0) >= int(caps.get(c,99)): continue
        selected.append(item); cap_counts[c] = cap_counts.get(c,0)+1
        if len(selected) >= max_posts: break
    for i,item in enumerate(selected,1): item["slot_rank"] = i
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(selected)
    OUT_MD.write_text("# HSD Daily Slate Plan\n\n" + f"Generated: {datetime.now(timezone.utc).isoformat()}\nVersion: {VERSION}\n\n" + "\n".join(f"{x['slot_rank']}. **{x['content_type']}** — {x['headline']} ({x['reason']})" for x in selected) + "\n", encoding="utf-8")
    print(json.dumps({"slate_items":len(selected), "max_posts":max_posts, "caps":cap_counts}, indent=2))
if __name__ == "__main__":
    main()
