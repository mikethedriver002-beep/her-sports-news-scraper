
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

VERSION = "v3.3.0-mermaid-official-player-backfill-v1"
CFG = Path("config/hsd_official_player_sources_v1.json")
FOCUS = Path("preview_player_focus.csv")
OUT_CSV = "official_player_headshot_candidates.csv"
OUT_MD = "official_player_headshot_report.md"
FIELDS = ["league","team_name","player_name","candidate_url","candidate_image_url","match_type","auto_approval_status","notes"]

try:
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
except Exception:
    requests = None
    BeautifulSoup = None
    urljoin = None

def main() -> None:
    cfg = read_json(CFG, {})
    focus = read_csv(FOCUS)
    rows = []
    if requests and BeautifulSoup:
        team_urls = cfg.get("leagues",{}).get("WNBA",{}).get("team_roster_pages",{})
        for f in focus:
            team = clean(f.get("team_name")); player = clean(f.get("player_name"))
            url = team_urls.get(team)
            if not (team and player and url):
                continue
            try:
                r = requests.get(url, timeout=12, headers={"User-Agent": "HSDMermaidPlayerBackfill/1.0"})
                if r.status_code >= 400:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text(" ")
                if player.lower() not in text.lower():
                    continue
                # conservative: find images whose alt/title contains player name
                found = []
                for img in soup.find_all("img"):
                    alt = clean(img.get("alt") or img.get("title") or "")
                    src = clean(img.get("src") or img.get("data-src") or "")
                    if src and player.lower() in alt.lower():
                        found.append(urljoin(url, src))
                for img_url in found[:3]:
                    rows.append({
                        "league": "WNBA",
                        "team_name": team,
                        "player_name": player,
                        "candidate_url": url,
                        "candidate_image_url": img_url,
                        "match_type": "official_roster_alt_exact",
                        "auto_approval_status": "candidate_needs_operator_review",
                        "notes": "Official roster page image with player name in alt/title."
                    })
            except Exception:
                continue
    write_csv(OUT_CSV, rows, FIELDS)
    lines = ["# Official Player Headshot Backfill", "", f"Generated: {now_iso()}", f"Version: {VERSION}", "", f"- candidates: {len(rows)}", ""]
    if rows:
        for r in rows:
            lines.append(f"- {r['team_name']} / {r['player_name']}: {r['candidate_image_url']}")
    else:
        lines.append("No official player headshot candidates found this run.")
    Path(OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"official_player_candidates": len(rows)}, indent=2))

if __name__ == "__main__":
    main()
