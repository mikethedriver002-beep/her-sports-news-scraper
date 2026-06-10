from __future__ import annotations
import csv, hashlib, json, os, re, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

try:
    import requests
except Exception:
    requests = None

try:
    import feedparser
except Exception:
    feedparser = None

VERSION = "hsd-discovery-ingest-v3.0"

REGISTRY = Path("config/source_registry.json")
OUT_CSV = Path("story_candidates_discovery.csv")
OUT_JSONL = Path("story_candidates_discovery.jsonl")
OUT_REPORT = Path("discovery_sources_report.md")

FIELDS = ["story_id","source_id","source_type","source_tier","title","source_url","canonical_url","published_at","summary","risk_tier","publish_eligible","reason"]

def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()

def canonicalize(url: str) -> str:
    try:
        s = urlsplit(clean(url))
        query = [(k, v) for k, v in parse_qsl(s.query) if not k.startswith("utm_") and k not in {"fbclid","gclid"}]
        return urlunsplit((s.scheme.lower(), s.netloc.lower(), s.path.rstrip("/") or "/", urlencode(query), ""))
    except Exception:
        return clean(url)

def story_id(url: str, title: str) -> str:
    return "disc_" + hashlib.sha1((canonicalize(url) or clean(title)).encode()).hexdigest()[:14]

def load_registry() -> Dict[str, Any]:
    if not REGISTRY.exists():
        return {"sources": []}
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def feed_entries(src: Dict[str, Any]) -> List[Dict[str, str]]:
    if feedparser is None:
        return []
    rows = []
    for url in src.get("urls", []):
        try:
            parsed = feedparser.parse(url)
            for e in parsed.entries[:50]:
                link = e.get("link", "")
                rows.append({
                    "title": clean(e.get("title", "")),
                    "source_url": link,
                    "canonical_url": canonicalize(link),
                    "published_at": clean(e.get("published", "") or e.get("updated", "")),
                    "summary": clean(e.get("summary", "")),
                })
        except Exception:
            continue
    return rows

def reddit_public_json(src: Dict[str, Any]) -> List[Dict[str, str]]:
    if requests is None:
        return []
    rows = []
    for sub in src.get("subreddits", []):
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={int(src.get('limit', 25))}"
        try:
            r = requests.get(url, headers={"User-Agent": "HSDDiscovery/3.0"}, timeout=20)
            if r.status_code >= 400:
                continue
            for child in r.json().get("data", {}).get("children", []):
                d = child.get("data", {})
                link = d.get("url") or f"https://www.reddit.com{d.get('permalink','')}"
                rows.append({
                    "title": clean(d.get("title")),
                    "source_url": link,
                    "canonical_url": canonicalize(link),
                    "published_at": datetime.fromtimestamp(d.get("created_utc", time.time()), tz=timezone.utc).isoformat(),
                    "summary": clean(d.get("selftext", ""))[:500],
                })
        except Exception:
            continue
    return rows

def main() -> None:
    registry = load_registry()
    candidates = []
    for src in registry.get("sources", []):
        if not src.get("enabled"):
            continue
        stype = src.get("source_type")
        rows = []
        if stype == "rss":
            rows = feed_entries(src)
        elif stype == "reddit_public_json":
            rows = reddit_public_json(src)
        else:
            continue
        for r in rows:
            risk = "green_official" if src.get("tier") == "official" else "yellow_discovery_only"
            eligible = "Yes" if risk.startswith("green") else "No"
            reason = "official feed candidate" if eligible == "Yes" else "discovery only; needs verification"
            candidates.append({
                "story_id": story_id(r.get("canonical_url",""), r.get("title","")),
                "source_id": src.get("source_id",""),
                "source_type": stype,
                "source_tier": src.get("tier",""),
                "title": r.get("title",""),
                "source_url": r.get("source_url",""),
                "canonical_url": r.get("canonical_url",""),
                "published_at": r.get("published_at",""),
                "summary": r.get("summary",""),
                "risk_tier": risk,
                "publish_eligible": eligible,
                "reason": reason,
            })
    # dedupe
    by_id = {r["story_id"]: r for r in candidates}
    candidates = list(by_id.values())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(candidates)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in candidates) + ("\n" if candidates else ""), encoding="utf-8")
    OUT_REPORT.write_text(
        "# HSD Discovery Sources Report\n\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
        f"- candidates: {len(candidates)}\n"
        f"- publish eligible: {sum(1 for r in candidates if r['publish_eligible']=='Yes')}\n"
        f"- discovery only: {sum(1 for r in candidates if r['publish_eligible']!='Yes')}\n",
        encoding="utf-8"
    )
    print(json.dumps({"discovery_candidates": len(candidates)}, indent=2))

if __name__ == "__main__":
    main()
