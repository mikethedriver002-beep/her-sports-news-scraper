from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    import requests
except Exception:
    requests = None

try:
    import feedparser
except Exception:
    feedparser = None

VERSION = "hsd-discovery-ingest-v3.2.4-bebe-ops-v2.3"

REGISTRY = Path("config/source_registry.json")
OUT_CSV = Path("story_candidates_discovery.csv")
OUT_JSONL = Path("story_candidates_discovery.jsonl")
OUT_REPORT = Path("discovery_sources_report.md")

FIELDS = [
    "story_id", "source_id", "source_type", "source_tier", "source_trust_band", "title", "source_url",
    "canonical_url", "published_at", "summary", "risk_tier", "publish_eligible", "reason",
]

GREEN_TIERS = {"official", "operator", "wire", "primary_media", "stats_provider"}
YELLOW_TIERS = {"social", "social_manual", "community", "discovery", "media_review"}
RED_TIERS = {"red", "prohibited"}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def canonicalize(url: str) -> str:
    try:
        s = urlsplit(clean(url))
        query = [(k, v) for k, v in parse_qsl(s.query) if not k.startswith("utm_") and k not in {"fbclid", "gclid"}]
        return urlunsplit((s.scheme.lower(), s.netloc.lower(), s.path.rstrip("/") or "/", urlencode(query), ""))
    except Exception:
        return clean(url)


def story_id(url: str, title: str) -> str:
    return "disc_" + hashlib.sha1((canonicalize(url) or clean(title)).encode()).hexdigest()[:14]


def load_registry() -> Dict[str, Any]:
    if not REGISTRY.exists():
        return {"sources": []}
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def trust_band(src: Dict[str, Any]) -> str:
    band = clean(src.get("trust_band")).lower()
    tier = clean(src.get("tier")).lower()
    if "red" in band or tier in RED_TIERS:
        return "red"
    if "green" in band or tier in GREEN_TIERS:
        return "green"
    if tier in YELLOW_TIERS or "yellow" in band:
        return "yellow"
    return "yellow"


def feed_entries(src: Dict[str, Any]) -> List[Dict[str, str]]:
    if feedparser is None:
        return []
    rows: List[Dict[str, str]] = []
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
    rows: List[Dict[str, str]] = []
    for sub in src.get("subreddits", []):
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={int(src.get('limit', 25))}"
        try:
            r = requests.get(url, headers={"User-Agent": "HSDDiscovery/3.2.1 BeBeOps"}, timeout=20)
            if r.status_code >= 400:
                continue
            for child in r.json().get("data", {}).get("children", []):
                d = child.get("data", {})
                link = d.get("url") or f"https://www.reddit.com{d.get('permalink', '')}"
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
    candidates: List[Dict[str, str]] = []
    skipped_enabled_unknown = 0

    for src in registry.get("sources", []):
        if not src.get("enabled"):
            continue
        stype = clean(src.get("source_type"))
        band = trust_band(src)
        rows: List[Dict[str, str]] = []
        if stype == "rss":
            rows = feed_entries(src)
        elif stype == "reddit_public_json":
            rows = reddit_public_json(src)
        elif stype in {"official_site", "official_site_collection", "scoreboard_site", "wire", "manual", "social_manual_only", "prohibited"}:
            # These are registered for policy/cross-check/manual use. The current ingest lane does not crawl pages directly.
            continue
        else:
            skipped_enabled_unknown += 1
            continue

        for r in rows:
            risk = "green_official_or_primary" if band == "green" else "yellow_discovery_only" if band == "yellow" else "red_prohibited"
            eligible = "Yes" if band == "green" else "No"
            reason = "green registered feed candidate" if eligible == "Yes" else "discovery only; needs green confirmation"
            candidates.append({
                "story_id": story_id(r.get("canonical_url", ""), r.get("title", "")),
                "source_id": clean(src.get("source_id", "")),
                "source_type": stype,
                "source_tier": clean(src.get("tier", "")),
                "source_trust_band": band,
                "title": r.get("title", ""),
                "source_url": r.get("source_url", ""),
                "canonical_url": r.get("canonical_url", ""),
                "published_at": r.get("published_at", ""),
                "summary": r.get("summary", ""),
                "risk_tier": risk,
                "publish_eligible": eligible,
                "reason": reason,
            })

    by_id = {r["story_id"]: r for r in candidates}
    candidates = list(by_id.values())

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(candidates)
    OUT_JSONL.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in candidates) + ("\n" if candidates else ""), encoding="utf-8")

    lines = [
        "# HSD Discovery Sources Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Version: {VERSION}",
        f"- candidates: {len(candidates)}",
        f"- publish eligible: {sum(1 for r in candidates if r['publish_eligible'] == 'Yes')}",
        f"- discovery only: {sum(1 for r in candidates if r['publish_eligible'] != 'Yes')}",
        f"- enabled source types skipped because this lane does not crawl them: {skipped_enabled_unknown}",
        "",
        "Registered official-site sources are still used by the source registry, manual inbox risk tiering, and operator cross-check policy even when this discovery lane does not crawl them directly.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"discovery_candidates": len(candidates), "skipped_enabled_unknown": skipped_enabled_unknown}, indent=2))


if __name__ == "__main__":
    main()
