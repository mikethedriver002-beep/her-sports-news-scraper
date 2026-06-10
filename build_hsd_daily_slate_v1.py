from __future__ import annotations
import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

VERSION = "hsd-daily-slate-v3.0"
OUT_CSV = Path("daily_slate_plan.csv")
OUT_MD = Path("daily_slate_plan.md")
FIELDS = ["slot_rank","content_type","source_type","headline","event_date","priority","eligibility","reason","source_id","source_url"]

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def load_config() -> Dict[str, Any]:
    p = Path("config/daily_slate.json")
    if not p.exists():
        return {"max_posts": {"balanced": 3}, "fallback_order": ["breaking","result","preview","feature"]}
    return json.loads(p.read_text(encoding="utf-8"))

def main() -> None:
    cfg = load_config()
    volume = clean(__import__("os").environ.get("HSD_CONTENT_VOLUME", "balanced"))
    max_posts = int(cfg.get("max_posts", {}).get(volume, 3))
    items = []
    for r in read_csv("story_candidates_manual.csv"):
        if r.get("publish_eligible") == "Yes":
            items.append({"content_type": r.get("story_kind","breaking"), "source_type": "manual", "headline": r.get("title") or r.get("source_url"), "event_date": "", "priority": r.get("priority","P2"), "eligibility": "eligible", "reason": r.get("reason","manual"), "source_id": r.get("story_id",""), "source_url": r.get("canonical_url") or r.get("source_url")})
    for r in read_csv("story_candidates_discovery.csv"):
        if r.get("publish_eligible") == "Yes":
            items.append({"content_type": "breaking", "source_type": "discovery", "headline": r.get("title"), "event_date": "", "priority": "P2", "eligibility": "eligible", "reason": r.get("reason","discovery"), "source_id": r.get("story_id",""), "source_url": r.get("canonical_url")})
    for r in read_csv("results_contract_v2.csv"):
        if r.get("content_eligibility") == "eligible":
            ctype = "result" if r.get("row_kind") == "result" else "preview"
            items.append({"content_type": ctype, "source_type": "results_contract", "headline": r.get("headline"), "event_date": r.get("event_date_local"), "priority": "P1" if ctype=="result" else "P2", "eligibility": "eligible", "reason": r.get("freshness_reason","results"), "source_id": r.get("event_id",""), "source_url": r.get("source_url","")})
    order = {"breaking": 0, "result": 1, "preview": 2, "feature": 3}
    items = sorted(items, key=lambda x: (order.get(x["content_type"], 9), x.get("priority","P9"), x.get("headline","")))[:max_posts]
    for i, item in enumerate(items, start=1):
        item["slot_rank"] = i
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(items)
    OUT_MD.write_text("# HSD Daily Slate Plan\n\n" + f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n" + "\n".join(f"{x['slot_rank']}. **{x['content_type']}** — {x['headline']}" for x in items) + "\n", encoding="utf-8")
    print(json.dumps({"slate_items": len(items), "max_posts": max_posts}, indent=2))

if __name__ == "__main__":
    main()
