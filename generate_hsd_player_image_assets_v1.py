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
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

try:
    import requests
except Exception:
    requests = None

VERSION = "hsd-player-image-assets-v1"

INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_PLAYER_ASSETS = os.environ.get("HSD_PLAYER_ASSETS", "player_assets.csv")
INPUT_BUNDLE_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_MANUAL_PLAYER_ASSETS = os.environ.get("HSD_MANUAL_PLAYER_ASSETS", "manual_player_assets.csv")
PLAYER_IMAGE_DIR = Path(os.environ.get("HSD_PLAYER_IMAGE_DIR", "player_image_assets"))
BING_API_KEY = os.environ.get("BING_SEARCH_API_KEY", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
PLAYER_IMAGES_REQUIRED = os.environ.get("HSD_PLAYER_IMAGES_REQUIRED", "1").strip().lower() not in {"0", "false", "no"}
MAX_CANDIDATES = int(os.environ.get("HSD_PLAYER_IMAGE_MAX_CANDIDATES", "5"))

OUT_REQUIREMENTS = "player_image_requirements.csv"
OUT_REPORT = "player_image_sourcing_report.md"
OUT_UPDATED_APPROVED = "approved_graphics_assets.csv"
OUT_UPDATED_PLAYER_ASSETS = "player_assets.csv"
OUT_DIR = Path("data/assets/player_images")

APPROVED_FIELDS = [
    "approved_asset_id","asset_id","approved_variant","entity_type","entity_name","source_url","page_url",
    "master_path","web_path","rights_status","approved_by","approved_utc","usage_scope","notes"
]
PLAYER_FIELDS = ["player_id","sport","league","player_slug","player_name","headshot_asset_id","status","notes"]
REQ_FIELDS = [
    "bundle_slug","player_name","team_name","required","status","approved_asset_id","source_url",
    "local_path","sourcing_method","notes"
]

# This list is intentionally strict and only includes players that appear in the current lead result context.
PLAYER_TEAM_HINTS = {
    "Jessica Shepard": "Dallas Wings",
    "Arike Ogunbowale": "Dallas Wings",
    "Paige Bueckers": "Dallas Wings",
    "Kelsey Plum": "Los Angeles Sparks",
    "Ariel Atkins": "Los Angeles Sparks",
    "Dearica Hamby": "Los Angeles Sparks",
    "Nneka Ogwumike": "Los Angeles Sparks",
    "Cameron Brink": "Los Angeles Sparks",
}

# Current exact result override. This makes the graphics prompt two-sided instead of Wings-only.
MAIN_RESULT_PLAYER_SET = [
    "Jessica Shepard", "Arike Ogunbowale", "Paige Bueckers",
    "Kelsey Plum", "Ariel Atkins", "Dearica Hamby", "Nneka Ogwumike", "Cameron Brink",
]

BAD_URL_BITS = ["logo", "icon", "fallback", "placeholder", "sprite", "silhouette", "default", "pdf", "svg"]
GOOD_SOURCE_BITS = ["wnba", "espn", "yahoo", "getty", "imagn", "apnews", "basketball", "usatoday", "wikimedia"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-")


def sid(prefix: str, *parts: Any) -> str:
    return f"{prefix}_{hashlib.sha1('|'.join(clean(p) for p in parts).encode()).hexdigest()[:14]}"


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def prompt_text() -> str:
    p = Path(INPUT_BUNDLE_PROMPTS)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def required_players() -> List[Tuple[str, str, str]]:
    text = prompt_text()
    req: List[Tuple[str, str, str]] = []
    # Always require full lead-result player set when the main result is present.
    if "Main WNBA Result" in text and "Dallas Wings" in text and "Los Angeles Sparks" in text:
        for name in MAIN_RESULT_PLAYER_SET:
            req.append(("main-wnba-result", name, PLAYER_TEAM_HINTS.get(name, "")))
    # Also catch any player stat lines in prompts.
    for name, team in PLAYER_TEAM_HINTS.items():
        if re.search(r"\b" + re.escape(name) + r"\b", text, re.I):
            item = ("main-wnba-result", name, team)
            if item not in req:
                req.append(item)
    return req


def file_ext_from_url_or_type(url: str, ctype: str = "") -> str:
    if ctype:
        ext = mimetypes.guess_extension(ctype.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    ext = Path(urlparse(url).path).suffix
    return ext or ".jpg"


def copy_manual_file(player_name: str) -> Tuple[str, str]:
    slug = slugify(player_name)
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        for p in [PLAYER_IMAGE_DIR / f"{slug}{ext}", PLAYER_IMAGE_DIR / player_name / f"{slug}{ext}"]:
            if p.exists():
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                dest = OUT_DIR / f"{slug}_manual{p.suffix.lower()}"
                shutil.copy2(p, dest)
                return dest.as_posix(), "manual_file"
    return "", ""


def manual_url_rows() -> Dict[str, str]:
    out = {}
    for row in read_csv(INPUT_MANUAL_PLAYER_ASSETS):
        name = clean(row.get("player_name") or row.get("name"))
        url = clean(row.get("source_url") or row.get("url") or row.get("image_url"))
        local = clean(row.get("local_path") or row.get("path"))
        if name and (url or local):
            out[name] = local or url
    return out


def download_image(url: str, player_name: str, method: str) -> Tuple[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not url:
        return "", "missing_url"
    if Path(url).exists():
        ext = Path(url).suffix or ".jpg"
        dest = OUT_DIR / f"{slugify(player_name)}_{method}{ext}"
        shutil.copy2(url, dest)
        return dest.as_posix(), "copied_manual_path"
    if requests is None:
        return "", "requests_missing"
    try:
        r = requests.get(url, headers={"User-Agent": "HSDPlayerImageAssets/1.0"}, timeout=25, allow_redirects=True)
        if r.status_code >= 400 or not r.content:
            return "", f"download_failed_{r.status_code}"
        ctype = r.headers.get("content-type", "")
        ext = file_ext_from_url_or_type(url, ctype)
        if ext.lower() == ".svg":
            return "", "not_player_photo_svg"
        dest = OUT_DIR / f"{slugify(player_name)}_{method}{ext}"
        dest.write_bytes(r.content)
        return dest.as_posix(), f"downloaded_{r.status_code}"
    except Exception as exc:
        return "", f"download_error:{exc}"


def url_candidate_ok(player_name: str, team_name: str, url: str, title: str = "") -> bool:
    blob = f"{url} {title}".lower()
    last = player_name.split()[-1].replace("'", "").lower()
    if last not in blob:
        return False
    if any(bit in blob for bit in BAD_URL_BITS):
        return False
    if team_name and team_name.split()[-1].lower() not in blob and "wnba" not in blob and not any(bit in blob for bit in GOOD_SOURCE_BITS):
        return False
    return True


def bing_candidates(player_name: str, team_name: str) -> List[Tuple[str, str]]:
    if not BING_API_KEY or requests is None:
        return []
    queries = [
        f"{player_name} {team_name} WNBA photo",
        f"{player_name} {team_name} headshot WNBA",
        f"{player_name} WNBA portrait",
    ]
    out: List[Tuple[str, str]] = []
    for q in queries:
        try:
            r = requests.get(
                "https://api.bing.microsoft.com/v7.0/images/search",
                params={"q": q, "count": str(MAX_CANDIDATES), "safeSearch": "Moderate", "imageType": "Photo"},
                headers={"Ocp-Apim-Subscription-Key": BING_API_KEY, "User-Agent": "HSDPlayerImageAssets/1.0"},
                timeout=20,
            )
            if r.status_code >= 400:
                continue
            for item in r.json().get("value", []):
                url = clean(item.get("contentUrl"))
                title = clean(item.get("name"))
                if url and url_candidate_ok(player_name, team_name, url, title):
                    out.append((url, "bing_image_search"))
        except Exception:
            continue
    # dedupe
    seen = set(); deduped = []
    for u, m in out:
        if u not in seen:
            seen.add(u); deduped.append((u, m))
    return deduped[:MAX_CANDIDATES]


def serpapi_candidates(player_name: str, team_name: str) -> List[Tuple[str, str]]:
    if not SERPAPI_KEY or requests is None:
        return []
    out = []
    q = f"{player_name} {team_name} WNBA photo"
    try:
        r = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google_images", "q": q, "api_key": SERPAPI_KEY, "safe": "active"},
            headers={"User-Agent": "HSDPlayerImageAssets/1.0"},
            timeout=25,
        )
        if r.status_code >= 400:
            return []
        for item in r.json().get("images_results", [])[:MAX_CANDIDATES]:
            url = clean(item.get("original") or item.get("thumbnail"))
            title = clean(item.get("title"))
            if url and url_candidate_ok(player_name, team_name, url, title):
                out.append((url, "serpapi_google_images"))
    except Exception:
        return []
    return out


def make_asset_row(player_name: str, team_name: str, local_path: str, source_url: str, method: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    asset_id = sid("ast", player_name, source_url or local_path)
    approved_id = sid("appr", player_name, source_url or local_path)
    approved = {
        "approved_asset_id": approved_id,
        "asset_id": asset_id,
        "approved_variant": "primary_player_photo_v1",
        "entity_type": "player",
        "entity_name": player_name,
        "source_url": source_url or local_path,
        "page_url": source_url or local_path,
        "master_path": local_path,
        "web_path": local_path,
        "rights_status": "auto_approved_by_hsd_aggressive_policy",
        "approved_by": "HSD required player image pipeline",
        "approved_utc": now(),
        "usage_scope": "HSD social graphics",
        "notes": f"Required player image sourced via {method}."
    }
    player = {
        "player_id": f"wnba_{slugify(player_name)}",
        "sport": "basketball",
        "league": "WNBA",
        "player_slug": slugify(player_name),
        "player_name": player_name,
        "headshot_asset_id": approved_id,
        "status": "asset_found",
        "notes": f"Required player image sourced via {method}."
    }
    return approved, player


def main() -> None:
    approved_rows = read_csv(INPUT_APPROVED_ASSETS)
    player_rows = read_csv(INPUT_PLAYER_ASSETS)
    manual_urls = manual_url_rows()
    requirements = []
    added_approved = []
    added_players = []

    existing_player_assets = {r.get("entity_name"): r for r in approved_rows if r.get("entity_type") == "player" and r.get("approved_asset_id")}

    for bundle_slug, player_name, team_name in required_players():
        status = "missing"
        local_path = ""
        source_url = ""
        method = ""
        approved_id = existing_player_assets.get(player_name, {}).get("approved_asset_id", "")
        notes = ""

        if approved_id:
            status = "found_existing"
            source_url = existing_player_assets[player_name].get("source_url", "")
            local_path = existing_player_assets[player_name].get("master_path", "")
            method = "existing_approved"
        else:
            # 1. local manual files
            local_path, method = copy_manual_file(player_name)
            if local_path:
                source_url = local_path
                status = "found_manual_file"
            # 2. manual CSV URL/path
            if not local_path and player_name in manual_urls:
                url = manual_urls[player_name]
                local_path, dl_status = download_image(url, player_name, "manual_csv")
                if local_path:
                    source_url = url
                    method = "manual_csv"
                    status = f"found_{dl_status}"
            # 3. SerpAPI/Bing automatic candidates
            if not local_path:
                candidates = serpapi_candidates(player_name, team_name) + bing_candidates(player_name, team_name)
                for url, cand_method in candidates:
                    path, dl_status = download_image(url, player_name, cand_method)
                    if path:
                        local_path = path
                        source_url = url
                        method = cand_method
                        status = f"found_{dl_status}"
                        break

            if local_path:
                approved, player = make_asset_row(player_name, team_name, local_path, source_url, method)
                approved_id = approved["approved_asset_id"]
                added_approved.append(approved)
                added_players.append(player)
            else:
                notes = "Required player image missing. Add BING_SEARCH_API_KEY, SERPAPI_KEY, manual_player_assets.csv, or file in player_image_assets/<player-slug>.png."

        requirements.append({
            "bundle_slug": bundle_slug,
            "player_name": player_name,
            "team_name": team_name,
            "required": "Yes" if PLAYER_IMAGES_REQUIRED else "No",
            "status": status,
            "approved_asset_id": approved_id,
            "source_url": source_url,
            "local_path": local_path,
            "sourcing_method": method,
            "notes": notes,
        })

    # Merge approved assets and player rows, replacing stale missing rows where possible.
    by_approved = {r.get("approved_asset_id"): r for r in approved_rows if r.get("approved_asset_id")}
    for r in added_approved:
        by_approved[r["approved_asset_id"]] = r
    merged_approved = list(by_approved.values())

    by_player = {r.get("player_name"): r for r in player_rows if r.get("player_name")}
    for r in added_players:
        by_player[r["player_name"]] = r
    merged_players = list(by_player.values())

    write_csv(OUT_UPDATED_APPROVED, merged_approved, APPROVED_FIELDS)
    Path("approved_graphics_assets.json").write_text(json.dumps(merged_approved, indent=2), encoding="utf-8")
    write_csv(OUT_UPDATED_PLAYER_ASSETS, merged_players, PLAYER_FIELDS)
    Path("player_assets.json").write_text(json.dumps(merged_players, indent=2), encoding="utf-8")
    write_csv(OUT_REQUIREMENTS, requirements, REQ_FIELDS)

    missing = [r for r in requirements if r["required"] == "Yes" and not r["approved_asset_id"]]
    lines = [
        "# HSD Player Image Sourcing Report",
        "",
        f"Generated: {now()}",
        "",
        f"Player images required: {'Yes' if PLAYER_IMAGES_REQUIRED else 'No'}",
        f"Required player rows: {len(requirements)}",
        f"Missing required player images: {len(missing)}",
        "",
        "## Required players",
        "",
    ]
    for r in requirements:
        lines.append(f"- {r['status']} | {r['player_name']} | {r['team_name']} | {r.get('local_path') or 'missing'}")
    if missing:
        lines += ["", "## Missing image action", "", "Add one of the following:", "", "- `BING_SEARCH_API_KEY` GitHub secret", "- `SERPAPI_KEY` GitHub secret", "- `manual_player_assets.csv` with `player_name,source_url`", "- image files in `player_image_assets/` named like `paige-bueckers.png`", ""]
    Path(OUT_REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Created HSD player image asset outputs")
    print(json.dumps({"required_players": len(requirements), "missing_required_player_images": len(missing), "added_player_assets": len(added_approved)}, indent=2))


if __name__ == "__main__":
    main()
