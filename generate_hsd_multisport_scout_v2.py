
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

import html
from urllib.parse import urljoin, urlparse

VERSION = "v3.3.0-mermaid-multisport-scout-v2"
OUT_CSV = "multisport_scout_candidates.csv"
OUT_MD = "multisport_scout_report.md"
OUT_JSON = "multisport_scout_manifest.json"
CFG = "config/hsd_multisport_source_registry_v2.json"

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None

FIELDS = ["story_id","source_id","trust_band","sport","league","title","source_url","candidate_type","priority","verification_state","platform_fit","notes"]

def fetch_titles(src: Dict[str, Any]) -> List[Dict[str, str]]:
    if requests is None or BeautifulSoup is None:
        return []
    url = src.get("url", "")
    try:
        r = requests.get(url, headers={"User-Agent": "HSDMermaidScout/1.0"}, timeout=12)
        if r.status_code >= 400 or not r.text:
            return []
        text = r.text
        # ESPN-style json
        if "application/json" in r.headers.get("content-type","") or text.strip().startswith("{"):
            try:
                data = r.json()
                items = []
                for event in data.get("events", [])[:8]:
                    name = clean(event.get("name") or event.get("shortName"))
                    if name:
                        items.append({"title": name, "url": url, "type": "event"})
                return items
            except Exception:
                pass
        soup = BeautifulSoup(text, "html.parser")
        out = []
        seen = set()
        for a in soup.find_all("a", href=True):
            title = clean(a.get_text(" "))
            if len(title) < 12 or len(title) > 140:
                continue
            href = urljoin(url, a["href"])
            if href in seen:
                continue
            seen.add(href)
            out.append({"title": title, "url": href, "type": "news"})
            if len(out) >= 8:
                break
        return out
    except Exception:
        return []

def main() -> None:
    cfg = read_json(CFG, {"sources": []})
    rows = []
    for src in cfg.get("sources", []):
        band = clean(src.get("trust_band"))
        if band.lower() == "red":
            continue
        items = fetch_titles(src)
        for item in items[: int(cfg.get("limits",{}).get("max_items_per_source",8))]:
            league = clean(src.get("league"))
            sport = clean(src.get("sport"))
            title = clean(item.get("title"))
            rows.append({
                "story_id": story_id(src.get("source_id"), title, item.get("url")),
                "source_id": src.get("source_id"),
                "trust_band": band,
                "sport": sport,
                "league": league,
                "title": title,
                "source_url": item.get("url"),
                "candidate_type": clean(src.get("use")) or item.get("type"),
                "priority": score_priority(league, "news"),
                "verification_state": "official_source" if band.startswith("green") else "review",
                "platform_fit": "Threads; IG Stories; IG Feed if strong",
                "notes": "Official/green multi-sport scout candidate."
            })
    max_total = int(cfg.get("limits",{}).get("max_total_candidates",50))
    rows = rows[:max_total]
    write_csv(OUT_CSV, rows, FIELDS)
    lines = ["# HSD Mermaid Multi-Sport Scout", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- candidates: {len(rows)}", ""]
    by_league = {}
    for r in rows:
        by_league[r["league"]] = by_league.get(r["league"], 0) + 1
    lines += ["## By league", ""]
    lines += [f"- {k}: {v}" for k,v in sorted(by_league.items())] or ["- No candidates found."]
    lines += ["", "## Top candidates", ""]
    for r in rows[:25]:
        lines.append(f"- **{r['league']}** — {r['title']} ({r['source_id']})")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({"version": VERSION, "generated_at": now_iso(), "count": len(rows)}, indent=2), encoding="utf-8")
    print(json.dumps({"multisport_candidates": len(rows)}, indent=2))

if __name__ == "__main__":
    main()
