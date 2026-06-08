from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import requests
except Exception:
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

VERSION = "hsd-asset-desk-v1.1"

INPUT_BUNDLE_QUEUE = os.environ.get("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
INPUT_BUNDLE_PACKETS = os.environ.get("HSD_STUDIO_BUNDLE_PACKETS", "studio_bundle_packets.md")
INPUT_LAUNCH_GRAPHICS_BRIEF = os.environ.get("HSD_LAUNCH_GRAPHICS_BRIEF", "launch_graphics_chat_brief.md")
INPUT_PUBLISH_QUEUE = os.environ.get("HSD_LAUNCH_PUBLISH_QUEUE", "launch_instagram_publish_queue.csv")

RIGHTS_MODE = os.environ.get("HSD_ASSET_RIGHTS_MODE", "aggressive").lower().strip()
DOWNLOAD_ASSETS = os.environ.get("HSD_ASSET_DOWNLOAD", "1").strip().lower() not in {"0", "false", "no"}
BING_API_KEY = os.environ.get("BING_SEARCH_API_KEY", "").strip()
MAX_BING = int(os.environ.get("HSD_ASSET_BING_MAX", "6"))

OUT_RAW = Path("data/assets/raw")
OUT_APPROVED = Path("data/assets/approved")

ASSET_FIELDS = [
    "asset_id","asset_type","entity_type","sport","league","entity_name","source_url","page_url",
    "source_domain","discovered_via","candidate_score","approval_status","approved_asset_id",
    "rights_status","rights_notes","download_path","checksum_sha256","width_px","height_px"
]
TEAM_FIELDS = ["team_id","sport","league","team_slug","team_name","logo_asset_id","status","notes"]
PLAYER_FIELDS = ["player_id","sport","league","player_slug","player_name","headshot_asset_id","status","notes"]
APPROVED_FIELDS = [
    "approved_asset_id","asset_id","approved_variant","entity_type","entity_name","source_url","page_url",
    "master_path","web_path","rights_status","approved_by","approved_utc","usage_scope","notes"
]
INTEGRATION_FIELDS = [
    "bundle_id","post_slug","post_type","pillar","priority","team_ids","player_ids","required_asset_ids",
    "optional_asset_ids","template_name","status"
]
SEED_FIELDS = ["entity_name","entity_type","sport","league","source_url","search_query","notes"]

WNBA_APPROVED_LOGOS = {
    "Dallas Wings": "https://cdn.wnba.com/logos/wnba/1611661321/primary/D/logo.svg",
    "Las Vegas Aces": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Las_Vegas_Aces_logo.svg",
    "Golden State Valkyries": "https://cdn.wnba.com/logos/wnba/1611661331/primary/L/logo.svg",
    "Phoenix Mercury": "https://cdn.wnba.com/logos/wnba/1611661330/primary/L/logo.svg",
    "Seattle Storm": "https://cdn.wnba.com/logos/wnba/1611661328/primary/D/logo.svg",
}

WNBA_REVIEW_ONLY = {
    "Los Angeles Sparks": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Minnesota Lynx": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Portland Fire": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Atlanta Dream": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Indiana Fever": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Chicago Sky": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Washington Mystics": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "New York Liberty": "No auto-approved logo in v1.1. Use text-forward until verified.",
    "Connecticut Sun": "No auto-approved logo in v1.1. Use text-forward until verified.",
}

COUNTRY_CODES = {
    "USA W":"us","United States W":"us","France W":"fr","Belgium W":"be","Thailand W":"th",
    "Brazil W":"br","Brazil U20 W":"br","Bulgaria W":"bg","Canada W":"ca","China W":"cn",
    "Serbia W":"rs","Italy W":"it","Turkey W":"tr","Mexico W":"mx","Australia W":"au",
    "Japan W":"jp","South Africa W":"za","Korea Republic U20 W":"kr","Korea Republic W":"kr",
}

PLAYER_TEAM_HINTS = {
    "Arike Ogunbowale": "Dallas Wings",
    "Paige Bueckers": "Dallas Wings",
    "Jessica Shepard": "Los Angeles Sparks",
    "A'ja Wilson": "Las Vegas Aces",
    "Jackie Young": "Las Vegas Aces",
    "Gabby Williams": "Seattle Storm",
    "DeWanna Bonner": "Phoenix Mercury",
    "Natasha Mack": "Phoenix Mercury",
    "Natasha Howard": "Indiana Fever",
    "Olivia Miles": "Minnesota Lynx",
}

BLOCKED_URL_PATTERNS = [
    "fallback", "fallbackimage", "wnba-secondary-logo", "volleyball-nations-league-logo-nav",
    "app-icon", "background", "dollar-bank", "jusco", "gulf-of-mexico", "chatgpt-logo",
    ".pdf", "apple.svg", "google.svg"
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-")


def sid(prefix: str, *parts: Any) -> str:
    return f"{prefix}_{hashlib.sha1('|'.join(clean(p) for p in parts).encode()).hexdigest()[:14]}"


def find_file(filename: str) -> Path:
    candidates = [Path(filename)]
    for root in ["studio_run_history", "launch_run_history", "asset_run_history", "news_run_history"]:
        r = Path(root)
        if r.exists():
            candidates += sorted(r.rglob(Path(filename).name), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in candidates:
        if p.exists() and p.is_file() and p.stat().st_size > 0:
            return p
    return Path(filename)


def read_csv_any(filename: str) -> List[Dict[str, str]]:
    p = find_file(filename)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def read_text_any(filename: str) -> str:
    p = find_file(filename)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def parse_bundle_text(text: str) -> List[Dict[str, str]]:
    bundles = []
    blocks = re.split(r"\n(?=##\s+BUNDLE\s+\d+:)", text)
    for block in blocks:
        m = re.search(r"##\s+BUNDLE\s+(\d+):\s*(.+)", block)
        if not m:
            continue
        rank, name = m.group(1), clean(m.group(2))
        caption = ""
        cap = re.search(r"### Caption seed\s+(.+?)(?:\n###|\n---|\Z)", block, re.S)
        if cap:
            caption = clean(cap.group(1))
        lock = ""
        lm = re.search(r"### Accuracy lock\s+(.+?)(?:\n---|\Z)", block, re.S)
        if lm:
            lock = clean(lm.group(1))
        source = ""
        sm = re.search(r"Source items:\s*(.+)", block)
        if sm:
            source = clean(sm.group(1))
        bundle_type = "main_wnba_lead" if "Main WNBA" in name else "wnba_mini_roundup" if "WNBA" in name or "Tonight in the W" in name else "volleyball_roundup" if "Volleyball" in name else "soccer_radar" if "Soccer" in name else "bundle"
        bundles.append({
            "bundle_rank": rank,
            "bundle_id": sid("bundle", name, source, caption),
            "bundle_name": name,
            "bundle_type": bundle_type,
            "production_priority": "POST FIRST" if rank == "1" else "POST NEXT",
            "source_headlines": source or lock,
            "caption_seed": caption,
            "accuracy_lock": lock,
            "source_items_count": "",
        })
    return bundles


def load_bundles() -> List[Dict[str, str]]:
    rows = read_csv_any(INPUT_BUNDLE_QUEUE)
    if rows:
        return rows
    text = read_text_any(INPUT_BUNDLE_PACKETS) + "\n" + read_text_any(INPUT_LAUNCH_GRAPHICS_BRIEF)
    return parse_bundle_text(text)


def extract_teams_and_players(bundles: List[Dict[str, str]]) -> Tuple[List[str], List[str]]:
    blob = "\n".join(" | ".join(str(v) for v in b.values()) for b in bundles)
    teams = []
    for name in list(WNBA_APPROVED_LOGOS) + list(WNBA_REVIEW_ONLY) + list(COUNTRY_CODES):
        if re.search(r"\b" + re.escape(name) + r"\b", blob, re.I):
            teams.append(name)
    # catch common final-score sentence "X 104, Y 96"
    for m in re.finditer(r"([A-Z][A-Za-z .'\-]+?)\s+\d{1,3},\s+([A-Z][A-Za-z .'\-]+?)\s+\d{1,3}", blob):
        for t in [clean(m.group(1)), clean(m.group(2))]:
            if 2 < len(t) < 40 and not any(x.lower() in t.lower() for x in ["verified", "top performers"]):
                teams.append(t)
    players = []
    for m in re.finditer(r"([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){1,3})\s*\(", blob):
        n = clean(m.group(1))
        if n not in teams and len(n.split()) >= 2:
            players.append(n)
    for p in PLAYER_TEAM_HINTS:
        if re.search(r"\b" + re.escape(p) + r"\b", blob, re.I):
            players.append(p)
    return sorted(set(teams)), sorted(set(players))


def infer_sport_league(entity: str) -> Tuple[str, str]:
    if entity in WNBA_APPROVED_LOGOS or entity in WNBA_REVIEW_ONLY or entity in PLAYER_TEAM_HINTS:
        return "basketball", "WNBA"
    if entity in COUNTRY_CODES:
        if "U20" in entity or entity in {"Brazil W","Japan W","Mexico W","Australia W","South Africa W","Korea Republic U20 W"}:
            return "soccer", "International Soccer"
        return "volleyball", "International Volleyball"
    return "", ""


def bad_asset_url(url: str) -> bool:
    u = url.lower()
    return any(p in u for p in BLOCKED_URL_PATTERNS)


def download(url: str, asset_id: str) -> Tuple[str, str]:
    if not DOWNLOAD_ASSETS or requests is None:
        return "", ""
    try:
        r = requests.get(url, headers={"User-Agent":"HSDAssetDesk/1.1"}, timeout=20)
        if r.status_code >= 400:
            return "", ""
        ext = mimetypes.guess_extension(r.headers.get("content-type","").split(";")[0]) or Path(urlparse(url).path).suffix or ".asset"
        if ext == ".jpe":
            ext = ".jpg"
        OUT_RAW.mkdir(parents=True, exist_ok=True)
        OUT_APPROVED.mkdir(parents=True, exist_ok=True)
        raw = OUT_RAW / f"{asset_id}{ext}"
        appr = OUT_APPROVED / f"{asset_id}{ext}"
        raw.write_bytes(r.content)
        appr.write_bytes(r.content)
        return appr.as_posix(), hashlib.sha256(r.content).hexdigest()
    except Exception:
        return "", ""


def make_asset(entity: str, entity_type: str, url: str, page_url: str, discovered: str, variant: str, auto_approve: bool = True) -> Dict[str, Any]:
    sport, league = infer_sport_league(entity)
    asset_id = sid("ast", entity, url)
    approved_id = sid("appr", entity, url) if auto_approve and not bad_asset_url(url) else ""
    path, checksum = download(url, approved_id or asset_id)
    status = "approved" if approved_id else "review"
    score = 95 if approved_id else 10
    return {
        "asset_id": asset_id,
        "asset_type": "logo" if entity_type == "team" else "headshot",
        "entity_type": entity_type,
        "sport": sport,
        "league": league,
        "entity_name": entity,
        "source_url": url,
        "page_url": page_url,
        "source_domain": urlparse(url).netloc,
        "discovered_via": discovered,
        "candidate_score": score,
        "approval_status": status,
        "approved_asset_id": approved_id,
        "rights_status": "auto_approved_by_hsd_aggressive_policy" if approved_id else "manual_review_required",
        "rights_notes": "Curated exact-match asset, not fallback/nav/random Wikimedia." if approved_id else "Not auto-approved. Use text-forward until verified.",
        "download_path": path,
        "checksum_sha256": checksum,
        "width_px": "",
        "height_px": "",
        "approved_variant": variant,
    }


def bing_player_candidates(player: str) -> List[Dict[str, Any]]:
    if not BING_API_KEY or requests is None:
        return []
    out = []
    q = f"{player} WNBA headshot official"
    try:
        r = requests.get(
            "https://api.bing.microsoft.com/v7.0/images/search",
            params={"q": q, "count": str(MAX_BING), "safeSearch": "Moderate"},
            headers={"Ocp-Apim-Subscription-Key": BING_API_KEY, "User-Agent": "HSDAssetDesk/1.1"},
            timeout=20,
        )
        if r.status_code >= 400:
            return []
        for item in r.json().get("value", []):
            url = item.get("contentUrl", "")
            page = item.get("hostPageUrl", "")
            if bad_asset_url(url):
                continue
            if player.split()[0].lower() not in (item.get("name","") + " " + page + " " + url).lower():
                continue
            out.append(make_asset(player, "player", url, page, "bing_image_search", "primary_player_image_v1", auto_approve=True))
    except Exception:
        pass
    return out


def build_assets(teams: List[str], players: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, str]]]:
    rows, seeds = [], []
    for team in teams:
        sport, league = infer_sport_league(team)
        if team in WNBA_APPROVED_LOGOS:
            url = WNBA_APPROVED_LOGOS[team]
            rows.append(make_asset(team, "team", url, url, "curated_exact_logo_map", "primary_logo_v1", True))
            seeds.append({"entity_name":team,"entity_type":"team","sport":sport,"league":league,"source_url":url,"search_query":"","notes":"Curated exact logo map"})
        elif team in COUNTRY_CODES:
            code = COUNTRY_CODES[team]
            url = f"https://flagcdn.com/w320/{code}.png"
            rows.append(make_asset(team, "team", url, url, "curated_country_flag_map", "primary_flag_v1", True))
            seeds.append({"entity_name":team,"entity_type":"team","sport":sport,"league":league,"source_url":url,"search_query":"","notes":"Curated exact country flag map"})
        else:
            seeds.append({"entity_name":team,"entity_type":"team","sport":sport,"league":league,"source_url":"","search_query":f"{team} logo official","notes":"Needs manual verification; no auto-approved asset"})
    for player in players:
        sport, league = infer_sport_league(player)
        seeds.append({"entity_name":player,"entity_type":"player","sport":sport,"league":league,"source_url":"","search_query":f"{player} WNBA headshot official","notes":"Bing/API only. No WNBA fallback images allowed."})
        rows.extend(bing_player_candidates(player))
    approved = [r for r in rows if r.get("approved_asset_id")]
    return rows, approved, seeds


def approved_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            "approved_asset_id": r["approved_asset_id"],
            "asset_id": r["asset_id"],
            "approved_variant": r.get("approved_variant", "primary_asset_v1"),
            "entity_type": r["entity_type"],
            "entity_name": r["entity_name"],
            "source_url": r["source_url"],
            "page_url": r["page_url"],
            "master_path": r.get("download_path", ""),
            "web_path": r.get("download_path", ""),
            "rights_status": r["rights_status"],
            "approved_by": "HSD aggressive asset policy with v1.1 exact-match guard",
            "approved_utc": now(),
            "usage_scope": "HSD social graphics",
            "notes": "Auto-approved only after exact-match/fallback guard.",
        })
    return out


def build_team_rows(teams: List[str], approved: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name = {r["entity_name"]: r for r in approved if r["entity_type"] == "team"}
    out = []
    for team in teams:
        sport, league = infer_sport_league(team)
        asset = by_name.get(team, {})
        out.append({
            "team_id": f"{slugify(league or sport)}_{slugify(team)}",
            "sport": sport,
            "league": league,
            "team_slug": slugify(team),
            "team_name": team,
            "logo_asset_id": asset.get("approved_asset_id", ""),
            "status": "asset_found" if asset else "text_forward_only",
            "notes": "Approved exact asset." if asset else (WNBA_REVIEW_ONLY.get(team) or "No approved exact asset.")
        })
    return out


def build_player_rows(players: List[str], approved: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name = {r["entity_name"]: r for r in approved if r["entity_type"] == "player"}
    out = []
    for player in players:
        sport, league = infer_sport_league(player)
        asset = by_name.get(player, {})
        out.append({
            "player_id": f"{slugify(league or sport)}_{slugify(player)}",
            "sport": sport or "basketball",
            "league": league or "WNBA",
            "player_slug": slugify(player),
            "player_name": player,
            "headshot_asset_id": asset.get("approved_asset_id", ""),
            "status": "asset_found" if asset else "text_forward_only",
            "notes": "Approved exact player image." if asset else "No player image approved. Do not use WNBA fallback or fake player image."
        })
    return out


def bundle_blob(bundle: Dict[str, str]) -> str:
    return " ".join(str(v).lower() for v in bundle.values())


def build_integration(bundles: List[Dict[str, str]], teams: List[Dict[str, Any]], players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for i, b in enumerate(bundles, 1):
        blob = bundle_blob(b)
        team_ids, player_ids, req_assets, opt_assets = [], [], [], []
        for t in teams:
            if t["team_name"].lower() in blob:
                team_ids.append(t["team_id"])
                if t["logo_asset_id"]:
                    req_assets.append(t["logo_asset_id"])
        for p in players:
            if p["player_name"].lower() in blob:
                player_ids.append(p["player_id"])
                if p["headshot_asset_id"]:
                    opt_assets.append(p["headshot_asset_id"])
        btype = clean(b.get("bundle_type")).lower()
        template = "radar_v2" if "soccer" in btype else "roundup_v2" if "roundup" in btype or "volleyball" in btype else "result_slide_v2"
        pillar = "Women's Soccer" if "soccer" in btype else "Volleyball" if "volleyball" in btype else "WNBA"
        out.append({
            "bundle_id": b.get("bundle_id") or sid("bundle", i, b.get("bundle_name")),
            "post_slug": slugify(b.get("bundle_name") or f"bundle-{i}"),
            "post_type": "carousel",
            "pillar": pillar,
            "priority": b.get("production_priority", ""),
            "team_ids": json.dumps(team_ids),
            "player_ids": json.dumps(player_ids),
            "required_asset_ids": json.dumps(req_assets),
            "optional_asset_ids": json.dumps(opt_assets),
            "template_name": template,
            "status": "ready_with_assets" if req_assets or opt_assets else "premium_text_forward",
        })
    return out


def review_md(teams, players, rows, approved) -> str:
    lines = [
        "# HSD Asset Desk v1.1 Candidate Review",
        "",
        f"Generated: {now()}",
        "",
        "v1.1 blocks generic fallback images, VNL nav logos, random Wikimedia logo matches, app icons, PDFs, and WNBA fallback player images.",
        "",
        f"Teams detected: {len(teams)}",
        f"Players detected: {len(players)}",
        f"Approved assets: {len(approved)}",
        "",
    ]
    if approved:
        lines.append("## Approved")
        for a in approved:
            lines.append(f"- approved | {a['entity_name']} | {a['asset_type']} | {a['source_url']}")
    lines.append("")
    lines.append("## Text-forward / needs verification")
    for team in teams:
        if team not in {a["entity_name"] for a in approved if a["entity_type"] == "team"}:
            lines.append(f"- {team}: no exact approved logo. Use text-forward.")
    for player in players:
        if player not in {a["entity_name"] for a in approved if a["entity_type"] == "player"}:
            lines.append(f"- {player}: no exact approved player image. Use text-forward.")
    return "\n".join(lines) + "\n"


def main() -> None:
    bundles = load_bundles()
    teams, players = extract_teams_and_players(bundles)
    asset_rows, approved_asset_candidates, seeds = build_assets(teams, players)
    approved = approved_rows(approved_asset_candidates)
    team_rows = build_team_rows(teams, approved_asset_candidates)
    player_rows = build_player_rows(players, approved_asset_candidates)
    integration_rows = build_integration(bundles, team_rows, player_rows)

    write_csv("asset_manifest.csv", asset_rows, ASSET_FIELDS)
    Path("asset_manifest.json").write_text(json.dumps(asset_rows, indent=2), encoding="utf-8")
    write_csv("asset_source_seed_list.csv", seeds, SEED_FIELDS)
    write_csv("approved_graphics_assets.csv", approved, APPROVED_FIELDS)
    Path("approved_graphics_assets.json").write_text(json.dumps(approved, indent=2), encoding="utf-8")
    write_csv("team_assets.csv", team_rows, TEAM_FIELDS)
    Path("team_assets.json").write_text(json.dumps(team_rows, indent=2), encoding="utf-8")
    write_csv("player_assets.csv", player_rows, PLAYER_FIELDS)
    Path("player_assets.json").write_text(json.dumps(player_rows, indent=2), encoding="utf-8")
    write_csv("launch_integration_points.csv", integration_rows, INTEGRATION_FIELDS)
    write_csv("asset_rights_review.csv", [
        {"asset_id": r["asset_id"], "review_status": r["approval_status"], "decision_reason": r["rights_notes"]}
        for r in asset_rows
    ], ["asset_id","review_status","decision_reason"])

    Path("asset_candidates_review.md").write_text(review_md(teams, players, asset_rows, approved_asset_candidates), encoding="utf-8")

    Path("asset_desk_manifest.json").write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "rights_mode": RIGHTS_MODE,
        "download": DOWNLOAD_ASSETS,
        "inputs": {
            "bundle_queue": str(find_file(INPUT_BUNDLE_QUEUE)),
            "bundle_packets": str(find_file(INPUT_BUNDLE_PACKETS)),
            "launch_graphics_brief": str(find_file(INPUT_LAUNCH_GRAPHICS_BRIEF)),
        },
        "counts": {
            "bundles": len(bundles),
            "teams_detected": len(teams),
            "players_detected": len(players),
            "asset_candidates": len(asset_rows),
            "approved_assets": len(approved),
            "integration_rows": len(integration_rows),
        },
        "guardrails": [
            "No WNBA fallback player images are approved.",
            "No generic VNL nav logos are approved as team logos.",
            "No random Wikimedia logo search results are approved.",
            "No PDF/app icon/background/logo-nav assets are approved.",
            "If exact asset cannot be verified, output remains text-forward."
        ],
    }, indent=2), encoding="utf-8")

    print("Created HSD Asset Desk v1.1 outputs")


if __name__ == "__main__":
    main()
