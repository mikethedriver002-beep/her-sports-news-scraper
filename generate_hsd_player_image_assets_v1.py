from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote, unquote, urljoin, urlparse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

try:
    from duckduckgo_search import DDGS
except Exception:  # pragma: no cover
    DDGS = None

VERSION = "hsd-player-image-assets-v1.5-free-sourcing"

INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_PLAYER_ASSETS = os.environ.get("HSD_PLAYER_ASSETS", "player_assets.csv")
INPUT_BUNDLE_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_BUNDLE_QUEUE = os.environ.get("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
INPUT_LAUNCH_GRAPHICS_BRIEF = os.environ.get("HSD_LAUNCH_GRAPHICS_BRIEF", "launch_graphics_chat_brief.md")
INPUT_MANUAL_PLAYER_ASSETS = os.environ.get("HSD_MANUAL_PLAYER_ASSETS", "manual_player_assets.csv")
PLAYER_IMAGE_DIR = Path(os.environ.get("HSD_PLAYER_IMAGE_DIR", "player_image_assets"))

BING_API_KEY = os.environ.get("BING_SEARCH_API_KEY", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
FREE_SEARCH_ENABLED = os.environ.get("HSD_PLAYER_IMAGE_FREE_SEARCH", "1").strip().lower() not in {"0", "false", "no"}
PLAYER_IMAGES_REQUIRED = os.environ.get("HSD_PLAYER_IMAGES_REQUIRED", "1").strip().lower() not in {"0", "false", "no"}
MAX_CANDIDATES = int(os.environ.get("HSD_PLAYER_IMAGE_MAX_CANDIDATES", "8"))
REQUEST_SLEEP = float(os.environ.get("HSD_PLAYER_IMAGE_REQUEST_SLEEP", "0.35"))
MIN_WIDTH = int(os.environ.get("HSD_PLAYER_IMAGE_MIN_WIDTH", "160"))
MIN_HEIGHT = int(os.environ.get("HSD_PLAYER_IMAGE_MIN_HEIGHT", "160"))
AUTO_APPROVE_SCORE = int(os.environ.get("HSD_PLAYER_IMAGE_AUTO_APPROVE_SCORE", "35"))

OUT_REQUIREMENTS = "player_image_requirements.csv"
OUT_REPORT = "player_image_sourcing_report.md"
OUT_CANDIDATES = "player_image_candidates.csv"
OUT_UPDATED_APPROVED = "approved_graphics_assets.csv"
OUT_UPDATED_PLAYER_ASSETS = "player_assets.csv"
OUT_DIR = Path("data/assets/player_images")

APPROVED_FIELDS = [
    "approved_asset_id", "asset_id", "approved_variant", "entity_type", "entity_name", "source_url", "page_url",
    "master_path", "web_path", "rights_status", "approved_by", "approved_utc", "usage_scope", "notes"
]
PLAYER_FIELDS = ["player_id", "sport", "league", "player_slug", "player_name", "headshot_asset_id", "status", "notes"]
REQ_FIELDS = [
    "bundle_slug", "player_name", "team_name", "required", "status", "approved_asset_id", "source_url",
    "local_path", "sourcing_method", "notes"
]
CANDIDATE_FIELDS = [
    "candidate_id", "player_name", "team_name", "candidate_url", "page_url", "source_domain", "title", "method",
    "score", "download_status", "local_path", "width_px", "height_px", "mime_type", "approved", "reject_reason"
]

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

MAIN_RESULT_PLAYER_SET = [
    "Jessica Shepard", "Arike Ogunbowale", "Paige Bueckers",
    "Kelsey Plum", "Ariel Atkins", "Dearica Hamby", "Nneka Ogwumike", "Cameron Brink",
]

TEAM_ROSTER_URLS = {
    "Dallas Wings": ["https://wings.wnba.com/roster/", "https://www.wnba.com/team/1611661321/dallas-wings"],
    "Los Angeles Sparks": ["https://sparks.wnba.com/roster/", "https://www.wnba.com/team/1611661320/los-angeles-sparks"],
    "Las Vegas Aces": ["https://aces.wnba.com/roster/"],
    "Minnesota Lynx": ["https://lynx.wnba.com/roster/"],
    "Phoenix Mercury": ["https://mercury.wnba.com/roster/"],
    "Seattle Storm": ["https://storm.wnba.com/roster/"],
}

BAD_URL_BITS = [
    "logo", "icon", "fallback", "placeholder", "sprite", "silhouette", "default", "pdf", ".svg",
    "facebook", "twitter", "instagram", "youtube", "favicon", "blank", "loading", "avatar-default",
]
GOOD_SOURCE_BITS = [
    "wnba", "espn", "yahoo", "getty", "imagn", "apnews", "basketball", "usatoday", "wikimedia",
    "wikipedia", "sports", "dallaswings", "sparks", "dallas", "latimes", "ocregister",
]
HEADERS = {"User-Agent": "HSDPlayerImageAssets/1.5 (+https://hersportsdaily.local)"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-") or "player"


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


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def prompt_text() -> str:
    return "\n".join([read_text(INPUT_BUNDLE_PROMPTS), read_text(INPUT_LAUNCH_GRAPHICS_BRIEF)])


def required_players() -> List[Tuple[str, str, str]]:
    text = prompt_text()
    req: List[Tuple[str, str, str]] = []
    if "Main WNBA Result" in text and "Dallas Wings" in text and "Los Angeles Sparks" in text:
        for name in MAIN_RESULT_PLAYER_SET:
            req.append(("main-wnba-result", name, PLAYER_TEAM_HINTS.get(name, "")))
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
    if ext.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        return ext
    return ".jpg"


def copy_manual_file(player_name: str) -> Tuple[str, str, str]:
    slug = slugify(player_name)
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        candidates = [
            PLAYER_IMAGE_DIR / f"{slug}{ext}",
            PLAYER_IMAGE_DIR / player_name / f"{slug}{ext}",
            PLAYER_IMAGE_DIR / slug / f"{slug}{ext}",
        ]
        for p in candidates:
            if p.exists():
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                dest = OUT_DIR / f"{slug}_manual{p.suffix.lower()}"
                shutil.copy2(p, dest)
                return dest.as_posix(), "manual_file", p.as_posix()
    return "", "", ""


def manual_url_rows() -> Dict[str, str]:
    out = {}
    for row in read_csv(INPUT_MANUAL_PLAYER_ASSETS):
        name = clean(row.get("player_name") or row.get("name"))
        url = clean(row.get("source_url") or row.get("url") or row.get("image_url"))
        local = clean(row.get("local_path") or row.get("path"))
        if name and (url or local):
            out[name] = local or url
    return out


def normalize_img_url(url: str, base: str = "") -> str:
    if not url:
        return ""
    url = url.replace("\\/", "/")
    if url.startswith("//"):
        return "https:" + url
    if base:
        return urljoin(base, url)
    return url


def url_candidate_ok(player_name: str, team_name: str, url: str, title: str = "") -> bool:
    blob = f"{unquote(url)} {title}".lower()
    if not url.startswith("http"):
        return False
    if any(bit in blob for bit in BAD_URL_BITS):
        return False
    last = player_name.split()[-1].replace("'", "").lower()
    first = player_name.split()[0].replace("'", "").lower()
    # Accept candidate if first/last are in title/blob, or source is a known roster page and last name appears.
    if last not in blob and first not in blob:
        return False
    if team_name:
        team_last = team_name.split()[-1].lower()
        if team_last not in blob and "wnba" not in blob and not any(bit in blob for bit in GOOD_SOURCE_BITS):
            return False
    return True


def score_candidate(player_name: str, team_name: str, url: str, title: str, method: str, page_url: str = "") -> int:
    blob = f"{unquote(url)} {title} {page_url}".lower()
    first = player_name.split()[0].replace("'", "").lower()
    last = player_name.split()[-1].replace("'", "").lower()
    score = 0
    if first in blob: score += 15
    if last in blob: score += 25
    if player_name.lower().replace("'", "") in blob.replace("'", ""): score += 30
    if team_name and team_name.split()[-1].lower() in blob: score += 15
    if "wnba" in blob: score += 15
    if any(bit in blob for bit in ["headshot", "portrait", "player", "roster", "athlete"]): score += 10
    if any(bit in blob for bit in ["espn", "wnba", "wikimedia", "wikipedia"]): score += 15
    if method.startswith("manual"): score += 100
    if method in {"wnba_roster_html", "wikipedia_pageimage", "wikidata_p18", "commons_api"}: score += 15
    if any(bit in blob for bit in BAD_URL_BITS): score -= 80
    return score


def image_probe(local_path: str) -> Tuple[bool, int, int, str]:
    if not local_path or not Path(local_path).exists():
        return False, 0, 0, "missing_file"
    if Image is None:
        return True, 0, 0, "pil_missing_assumed_ok"
    try:
        with Image.open(local_path) as im:
            w, h = im.size
            if w < MIN_WIDTH or h < MIN_HEIGHT:
                return False, w, h, f"too_small_{w}x{h}"
            # Reject ultra-wide logos/banners.
            ratio = max(w / max(h, 1), h / max(w, 1))
            if ratio > 3.8:
                return False, w, h, f"bad_aspect_{ratio:.2f}"
            return True, w, h, "ok"
    except Exception as exc:
        return False, 0, 0, f"image_open_error:{exc}"


def download_image(url: str, player_name: str, method: str) -> Tuple[str, str, str, int, int, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not url:
        return "", "missing_url", "", 0, 0, ""
    if Path(url).exists():
        ext = Path(url).suffix or ".jpg"
        dest = OUT_DIR / f"{slugify(player_name)}_{method}{ext}"
        shutil.copy2(url, dest)
        ok, w, h, reason = image_probe(dest.as_posix())
        return (dest.as_posix() if ok else ""), ("copied_manual_path" if ok else reason), ext.replace(".", ""), w, h, str(dest)
    if requests is None:
        return "", "requests_missing", "", 0, 0, ""
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        if r.status_code >= 400 or not r.content:
            return "", f"download_failed_{r.status_code}", r.headers.get("content-type", ""), 0, 0, ""
        ctype = r.headers.get("content-type", "")
        if "svg" in ctype or url.lower().endswith(".svg"):
            return "", "not_player_photo_svg", ctype, 0, 0, ""
        if ctype and not ctype.startswith("image/") and b"<html" in r.content[:200].lower():
            return "", "not_image_html", ctype, 0, 0, ""
        ext = file_ext_from_url_or_type(url, ctype)
        dest = OUT_DIR / f"{slugify(player_name)}_{method}_{sid('dl', url)[-6:]}{ext}"
        dest.write_bytes(r.content)
        ok, w, h, reason = image_probe(dest.as_posix())
        if not ok:
            try: dest.unlink()
            except Exception: pass
            return "", reason, ctype, w, h, ""
        return dest.as_posix(), f"downloaded_{r.status_code}", ctype, w, h, dest.as_posix()
    except Exception as exc:
        return "", f"download_error:{exc}", "", 0, 0, ""


def add_candidate(out: List[Dict[str, Any]], player: str, team: str, url: str, page: str, title: str, method: str) -> None:
    url = normalize_img_url(url, page)
    if not url or not url.startswith("http"):
        return
    if not url_candidate_ok(player, team, url, title):
        return
    out.append({
        "candidate_id": sid("pcand", player, url),
        "player_name": player,
        "team_name": team,
        "candidate_url": url,
        "page_url": page,
        "source_domain": urlparse(url).netloc,
        "title": clean(title),
        "method": method,
        "score": score_candidate(player, team, url, title, method, page),
        "download_status": "not_tried",
        "local_path": "",
        "width_px": "",
        "height_px": "",
        "mime_type": "",
        "approved": "No",
        "reject_reason": "",
    })


def wnba_roster_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if requests is None:
        return out
    urls = TEAM_ROSTER_URLS.get(team, [])
    for page_url in urls:
        try:
            time.sleep(REQUEST_SLEEP)
            r = requests.get(page_url, headers=HEADERS, timeout=25)
            if r.status_code >= 400:
                continue
            text = r.text
            low = text.lower()
            last = player.split()[-1].lower()
            first = player.split()[0].lower()
            if first not in low and last not in low:
                continue
            # Look around player mentions for image URLs.
            for m in re.finditer(re.escape(last), text, flags=re.I):
                window = text[max(0, m.start()-4000):m.end()+4000]
                for u in re.findall(r'https?:\\?/\\?/[^"\'<> ]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"\'<> ]*)?', window, flags=re.I):
                    add_candidate(out, player, team, u, page_url, f"{player} {team} roster", "wnba_roster_html")
                for u in re.findall(r'(?:src|data-src|srcset)=["\']([^"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^"\']*)?)', window, flags=re.I):
                    add_candidate(out, player, team, u.split(' ')[0], page_url, f"{player} {team} roster", "wnba_roster_html")
            if BeautifulSoup is not None:
                soup = BeautifulSoup(text, "html.parser")
                for img in soup.select("img[src],img[data-src],source[srcset]"):
                    alt = clean(img.get("alt") or img.get("aria-label") or img.get("title") or "")
                    blob = alt.lower()
                    if player.lower() in blob or last in blob:
                        src = img.get("src") or img.get("data-src") or (img.get("srcset", "").split(" ")[0])
                        add_candidate(out, player, team, src, page_url, alt, "wnba_roster_html")
        except Exception:
            continue
    return out


def wikipedia_pageimage_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if requests is None:
        return out
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f'"{player}" basketball',
                "gsrlimit": "3",
                "prop": "pageimages|info",
                "pithumbsize": "1200",
                "inprop": "url",
                "format": "json",
            },
            headers=HEADERS,
            timeout=20,
        )
        if r.status_code >= 400:
            return out
        for page in r.json().get("query", {}).get("pages", {}).values():
            title = clean(page.get("title"))
            thumb = page.get("thumbnail", {}).get("source", "")
            page_url = page.get("fullurl", "")
            if thumb and player.split()[-1].lower() in title.lower():
                add_candidate(out, player, team, thumb, page_url, title, "wikipedia_pageimage")
    except Exception:
        return out
    return out


def commons_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if requests is None:
        return out
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f'{player} basketball',
                "gsrnamespace": "6",
                "gsrlimit": str(MAX_CANDIDATES),
                "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata",
                "format": "json",
            },
            headers=HEADERS,
            timeout=20,
        )
        if r.status_code >= 400:
            return out
        for page in r.json().get("query", {}).get("pages", {}).values():
            title = clean(page.get("title"))
            infos = page.get("imageinfo", [])
            if not infos:
                continue
            info = infos[0]
            u = info.get("url", "")
            add_candidate(out, player, team, u, f"https://commons.wikimedia.org/wiki/{quote(title.replace(' ', '_'))}", title, "commons_api")
    except Exception:
        return out
    return out


def wikidata_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if requests is None:
        return out
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={"action":"wbsearchentities", "search":player, "language":"en", "format":"json", "limit":"3"},
            headers=HEADERS,
            timeout=20,
        )
        if r.status_code >= 400:
            return out
        for item in r.json().get("search", []):
            qid = item.get("id")
            desc = clean(item.get("description"))
            label = clean(item.get("label"))
            if not qid or player.split()[-1].lower() not in label.lower():
                continue
            c = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={"action":"wbgetclaims", "entity":qid, "property":"P18", "format":"json"},
                headers=HEADERS,
                timeout=20,
            )
            for claim in c.json().get("claims", {}).get("P18", []):
                fn = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                if fn:
                    u = f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quote(fn)}"
                    add_candidate(out, player, team, u, f"https://www.wikidata.org/wiki/{qid}", f"{label} {desc}", "wikidata_p18")
    except Exception:
        return out
    return out


def duckduckgo_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not FREE_SEARCH_ENABLED or DDGS is None:
        return out
    queries = [
        f'"{player}" "{team}" WNBA photo',
        f'"{player}" WNBA headshot',
        f'"{player}" basketball portrait',
    ]
    for q in queries:
        try:
            time.sleep(REQUEST_SLEEP)
            with DDGS() as ddgs:
                results = list(ddgs.images(q, max_results=MAX_CANDIDATES, safesearch="moderate"))
            for item in results:
                url = clean(item.get("image") or item.get("thumbnail") or "")
                title = clean(item.get("title") or item.get("source") or q)
                page = clean(item.get("url") or item.get("source") or "")
                add_candidate(out, player, team, url, page, title, "duckduckgo_images_free")
        except Exception:
            continue
    return out


def bing_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not BING_API_KEY or requests is None:
        return out
    for q in [f"{player} {team} WNBA photo", f"{player} {team} headshot WNBA", f"{player} WNBA portrait"]:
        try:
            time.sleep(REQUEST_SLEEP)
            r = requests.get(
                "https://api.bing.microsoft.com/v7.0/images/search",
                params={"q": q, "count": str(MAX_CANDIDATES), "safeSearch": "Moderate", "imageType": "Photo"},
                headers={"Ocp-Apim-Subscription-Key": BING_API_KEY, **HEADERS},
                timeout=20,
            )
            if r.status_code >= 400:
                continue
            for item in r.json().get("value", []):
                add_candidate(out, player, team, clean(item.get("contentUrl")), clean(item.get("hostPageUrl")), clean(item.get("name")), "bing_image_search")
        except Exception:
            continue
    return out


def serpapi_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not SERPAPI_KEY or requests is None:
        return out
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google_images", "q": f"{player} {team} WNBA photo", "api_key": SERPAPI_KEY, "safe": "active"},
            headers=HEADERS,
            timeout=25,
        )
        if r.status_code >= 400:
            return out
        for item in r.json().get("images_results", [])[:MAX_CANDIDATES]:
            add_candidate(out, player, team, clean(item.get("original") or item.get("thumbnail")), clean(item.get("source") or item.get("link")), clean(item.get("title")), "serpapi_google_images")
    except Exception:
        return out
    return out


def gather_candidates(player: str, team: str) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    # Free/no-key sources first.
    candidates.extend(wnba_roster_candidates(player, team))
    candidates.extend(wikipedia_pageimage_candidates(player, team))
    candidates.extend(wikidata_candidates(player, team))
    candidates.extend(commons_candidates(player, team))
    candidates.extend(duckduckgo_candidates(player, team))
    # Optional paid/API sources last if user later enables them.
    candidates.extend(serpapi_candidates(player, team))
    candidates.extend(bing_candidates(player, team))
    # Dedupe + sort by score.
    seen = set(); out = []
    for c in sorted(candidates, key=lambda x: int(x.get("score") or 0), reverse=True):
        u = c.get("candidate_url")
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(c)
    return out[:MAX_CANDIDATES * 4]


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
        "approved_by": "HSD free player image sourcing pipeline",
        "approved_utc": now(),
        "usage_scope": "HSD social graphics",
        "notes": f"Required player image sourced via {method}. Free/no-paid-API capable pipeline."
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
    requirements: List[Dict[str, Any]] = []
    added_approved: List[Dict[str, str]] = []
    added_players: List[Dict[str, str]] = []
    candidate_rows: List[Dict[str, Any]] = []

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
            local_path, method, source_url = copy_manual_file(player_name)
            if local_path:
                status = "found_manual_file"

            if not local_path and player_name in manual_urls:
                url = manual_urls[player_name]
                path, dl_status, ctype, w, h, _ = download_image(url, player_name, "manual_csv")
                candidate_rows.append({
                    "candidate_id": sid("pcand", player_name, url), "player_name": player_name, "team_name": team_name,
                    "candidate_url": url, "page_url": url, "source_domain": urlparse(url).netloc, "title": "manual_csv",
                    "method": "manual_csv", "score": 999, "download_status": dl_status, "local_path": path,
                    "width_px": w, "height_px": h, "mime_type": ctype, "approved": "Yes" if path else "No", "reject_reason": "" if path else dl_status,
                })
                if path:
                    local_path = path
                    source_url = url
                    method = "manual_csv"
                    status = f"found_{dl_status}"

            if not local_path:
                candidates = gather_candidates(player_name, team_name)
                for c in candidates:
                    url = c["candidate_url"]
                    path, dl_status, ctype, w, h, raw_path = download_image(url, player_name, c["method"])
                    c["download_status"] = dl_status
                    c["local_path"] = path
                    c["width_px"] = w
                    c["height_px"] = h
                    c["mime_type"] = ctype
                    approved_now = bool(path) and int(c.get("score") or 0) >= AUTO_APPROVE_SCORE
                    c["approved"] = "Yes" if approved_now else "No"
                    c["reject_reason"] = "" if approved_now else (dl_status if not path else f"score_below_{AUTO_APPROVE_SCORE}")
                    candidate_rows.append(c)
                    if approved_now:
                        local_path = path
                        source_url = url
                        method = c["method"]
                        status = f"found_{dl_status}"
                        break

            if local_path:
                approved, player = make_asset_row(player_name, team_name, local_path, source_url, method)
                approved_id = approved["approved_asset_id"]
                added_approved.append(approved)
                added_players.append(player)
            else:
                notes = "Required player image missing. Free pipeline tried local/manual, WNBA roster pages, Wikipedia/Wikidata/Commons, DuckDuckGo Images. Add a manual image file or source URL if unresolved."

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
    write_csv(OUT_CANDIDATES, candidate_rows, CANDIDATE_FIELDS)

    missing = [r for r in requirements if r["required"] == "Yes" and not r["approved_asset_id"]]
    found = [r for r in requirements if r.get("approved_asset_id")]
    lines = [
        "# HSD Player Image Sourcing Report",
        "",
        f"Generated: {now()}",
        f"Version: {VERSION}",
        "",
        f"Player images required: {'Yes' if PLAYER_IMAGES_REQUIRED else 'No'}",
        f"Required player rows: {len(requirements)}",
        f"Found required player images: {len(found)}",
        f"Missing required player images: {len(missing)}",
        f"Free search enabled: {'Yes' if FREE_SEARCH_ENABLED else 'No'}",
        f"DuckDuckGo package available: {'Yes' if DDGS is not None else 'No'}",
        f"Candidate rows inspected: {len(candidate_rows)}",
        "",
        "## Required players",
        "",
    ]
    for r in requirements:
        lines.append(f"- {r['status']} | {r['player_name']} | {r['team_name']} | {r.get('local_path') or 'missing'} | {r.get('sourcing_method')}")
    if missing:
        lines += [
            "", "## Missing image action", "",
            "The no-paid-API lane tried local files, manual CSV, WNBA/team roster pages, Wikipedia/Wikidata/Commons, and DuckDuckGo Images.",
            "For any remaining misses, add a file such as `player_image_assets/paige-bueckers.png` or add `manual_player_assets.csv` with `player_name,source_url`.",
            "",
        ]
    Path(OUT_REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Created HSD player image asset outputs")
    print(json.dumps({"required_players": len(requirements), "found_required_player_images": len(found), "missing_required_player_images": len(missing), "candidate_rows": len(candidate_rows), "added_player_assets": len(added_approved)}, indent=2))


if __name__ == "__main__":
    main()
