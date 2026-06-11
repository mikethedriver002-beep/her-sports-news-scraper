from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
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

VERSION = "hsd-player-image-assets-v1.7.0-preview-focus"
INPUT_PREVIEW_FOCUS = os.environ.get("HSD_PREVIEW_PLAYER_FOCUS", "preview_player_focus.csv")

INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_PLAYER_ASSETS = os.environ.get("HSD_PLAYER_ASSETS", "player_assets.csv")
INPUT_BUNDLE_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_BUNDLE_QUEUE = os.environ.get("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
INPUT_BUNDLE_PACKETS = os.environ.get("HSD_STUDIO_BUNDLE_PACKETS", "studio_bundle_packets.md")
INPUT_LAUNCH_GRAPHICS_BRIEF = os.environ.get("HSD_LAUNCH_GRAPHICS_BRIEF", "launch_graphics_chat_brief.md")
INPUT_MANUAL_PLAYER_ASSETS = os.environ.get("HSD_MANUAL_PLAYER_ASSETS", "manual_player_assets.csv")
PLAYER_IMAGE_DIR = Path(os.environ.get("HSD_PLAYER_IMAGE_DIR", "player_image_assets"))

BING_API_KEY = os.environ.get("BING_SEARCH_API_KEY", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
FREE_SEARCH_ENABLED = os.environ.get("HSD_PLAYER_IMAGE_FREE_SEARCH", "1").strip().lower() not in {"0", "false", "no"}
PLAYER_IMAGES_REQUIRED = os.environ.get("HSD_PLAYER_IMAGES_REQUIRED", "1").strip().lower() not in {"0", "false", "no"}
ALLOW_PREVIEW_PLAYER_IMAGES = os.environ.get("HSD_ALLOW_PREVIEW_PLAYER_IMAGES", "0").strip().lower() in {"1", "true", "yes"}
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
    "bundle_slug", "bundle_name", "sport", "league", "player_name", "team_name", "required", "status", "approved_asset_id", "source_url",
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
    "wikipedia", "sports", "dallaswings", "sparks", "dallas", "latimes", "ocregister", "nwsl", "soccer",
    "football", "volleyball", "ncaa", "athlete", "player", "roster", "headshot", "portrait"
]
PERSON_EXCLUDE = {
    "Her Sports Daily", "Main WNBA Result", "Final Score", "Top Performers", "Women’s Sports", "Women's Sports",
    "Tonight In The W", "What Stood Out", "Follow Her Sports Daily", "Around Women's Sports", "Quick Final Story Recap",
    "Biggest Takeaway", "Source Items", "Dallas Wings", "Los Angeles Sparks"
}
STAT_WORDS = [
    "pts", "reb", "ast", "stl", "blk", "goals", "goal", "assists", "assist", "saves", "save", "kills", "digs", "aces",
    "blocks", "sets", "shots", "points", "mvp", "mop", "record", "top performers", "leaders", "performers", "scored",
    "posted", "minutes"
]
SPORT_KEYWORDS = {
    "wnba": ("basketball", "WNBA"),
    "nwsl": ("soccer", "NWSL"),
    "uswnt": ("soccer", "USWNT"),
    "soccer": ("soccer", "Soccer"),
    "volleyball": ("volleyball", "Volleyball"),
    "softball": ("softball", "Softball"),
    "golf": ("golf", "Golf"),
    "tennis": ("tennis", "Tennis"),
}
HEADERS = {"User-Agent": "HSDPlayerImageAssets/1.6 (+https://hersportsdaily.local)"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-") or "asset"


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
    return "\n".join([read_text(INPUT_BUNDLE_PROMPTS), read_text(INPUT_BUNDLE_PACKETS), read_text(INPUT_LAUNCH_GRAPHICS_BRIEF)])


def preview_focus_rows() -> List[Dict[str, str]]:
    return read_csv(INPUT_PREVIEW_FOCUS)


def bundle_prompt_section(bundle_name: str, prompts_md: str) -> str:
    if not prompts_md or not bundle_name:
        return ""
    escaped = re.escape(bundle_name)
    m = re.search(rf"##\s+{escaped}\s*\n(.*?)(?=\n##\s+|\Z)", prompts_md, re.S)
    return m.group(1).strip() if m else ""


def known_team_names(approved_rows: List[Dict[str, str]]) -> List[str]:
    names = set(PLAYER_TEAM_HINTS.values())
    for row in approved_rows:
        entity_type = clean(row.get("entity_type")).lower()
        name = clean(row.get("entity_name"))
        if not name:
            continue
        if entity_type in {"team", "logo", "club", "school", "country", "nation"}:
            names.add(name)
        elif entity_type != "player" and any(tok in name.lower() for tok in ["wings", "sparks", "lynx", "storm", "mercury", "aces", "dream", "sky", "sun", "fever", "liberty", "mystics", "fc", "united", "city", "state", "texas", "usa", "brazil"]):
            names.add(name)
    return sorted(names, key=len, reverse=True)


def infer_sport_league(bundle_row: Dict[str, str], prompt_blob: str) -> Tuple[str, str]:
    blob = " ".join([
        clean(bundle_row.get("bundle_name")), clean(bundle_row.get("bundle_type")), clean(bundle_row.get("sports_mix")),
        clean(bundle_row.get("content_family")), prompt_blob,
    ]).lower()
    for key, pair in SPORT_KEYWORDS.items():
        if key in blob:
            return pair
    return ("athlete", "")


def candidate_person_names_from_line(line: str, teams: List[str]) -> List[str]:
    compact = clean(line)
    low = compact.lower()

    # Never mine people from instruction, asset, schedule, or prompt-control lines.
    # v1.6.1 overfired here and treated teams / internal prompt phrases as people.
    instruction_bits = [
        "asset", "assets", "logo", "logos", "watermark", "uploaded", "prompt", "graphics chat",
        "slide ", "carousel", "games:", "schedule board", "previewing", "do not invent", "use only",
        "approved team", "caption seed", "accuracy lock", "source items",
    ]
    if any(bit in low for bit in instruction_bits):
        return []

    stat_word_hit = any(re.search(rf"\b{re.escape(word)}\b", low) for word in STAT_WORDS)
    stat_abbrev_hit = bool(re.search(r"\b\d+\s*(?:pts|reb|ast|stl|blk|goals?|assists?|saves?|kills|digs|aces)\b", low))
    if not (stat_word_hit or stat_abbrev_hit):
        return []

    pattern = r"[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+(?:\s+[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+){1,2}"
    out: List[str] = []
    seen = set()
    for m in re.finditer(pattern, compact):
        name = clean(m.group(0))
        if name in PERSON_EXCLUDE or not valid_person_extract(name, teams):
            continue
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def detect_team_for_line(line: str, teams: List[str], current_team: str = "") -> str:
    low = line.lower()
    for team in teams:
        if team.lower() in low:
            return team
    return current_team


BAD_PERSON_EXTRACTS = {
    "HSD Bundle Prompts", "PLAYER IMAGE STATUS", "One Dallas", "One Sparks", "Los Angeles", "Verified Final",
    "Use Dallas", "BUNDLE LOCKED FACTS", "Graphics Chat Starter", "HER SPORTS DAILY", "Los Angeles Sparks.",
    "Source Items", "Approved exact assets", "Fact warnings", "Safe graphics mode", "Critical instruction",
    "Connecticut Sun", "Toronto Tempo", "Seattle Storm", "Los Angeles Sparks",
}
BAD_PERSON_TOKENS = {"HSD", "BUNDLE", "LOCKED", "FACTS", "GRAPHICS", "CHAT", "STARTER", "VERIFIED", "FINAL", "STATUS", "PROMPT", "PROMPTS", "SOURCE", "ASSET", "ASSETS", "UPLOAD"}


def valid_person_extract(name: str, teams: List[str]) -> bool:
    name = clean(name).strip(" .,:;|/-_")
    if not name or name in BAD_PERSON_EXTRACTS or name in teams:
        return False
    parts = name.split()
    if len(parts) < 2 or len(parts) > 3:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    if {p.upper() for p in parts} & BAD_PERSON_TOKENS:
        return False
    if parts[0] in {"One", "Use", "Safe", "Critical", "Approved", "Source", "Fact", "Player"}:
        return False
    if parts[-1].rstrip(".") in {"Wings", "Sparks", "Aces", "Storm", "Lynx", "Mercury", "Fire", "Valkyries"}:
        return False
    return True


def required_players() -> List[Tuple[str, str, str, str, str, str]]:
    prompts_md = read_text(INPUT_BUNDLE_PROMPTS)
    queue_rows = read_csv(INPUT_BUNDLE_QUEUE)
    approved_rows = read_csv(INPUT_APPROVED_ASSETS)
    teams = known_team_names(approved_rows)
    req: List[Tuple[str, str, str, str, str, str]] = []
    seen = set()

    def add(bundle_slug: str, bundle_name: str, player_name: str, team_name: str, sport: str, league: str):
        player_name = clean(player_name).strip(" .,:;|/-_")
        if bundle_slug == "general-bundle":
            return
        if not valid_person_extract(player_name, teams):
            return
        key = (bundle_slug, player_name)
        if key in seen:
            return
        seen.add(key)
        req.append((bundle_slug, bundle_name, player_name, team_name, sport, league))

    for row in queue_rows:
        bundle_name = clean(row.get("bundle_name") or row.get("post_slug") or row.get("bundle_slug"))
        bundle_slug = clean(row.get("post_slug") or row.get("bundle_slug") or slugify(bundle_name))
        if any(x in bundle_name.lower() for x in ["preview", "schedule"]) and not ALLOW_PREVIEW_PLAYER_IMAGES:
            # Preview/schedule bundles are team/logo driven unless explicit preview player mode is enabled.
            continue
        section = bundle_prompt_section(bundle_name, prompts_md)
        blob = "\n".join([
            clean(row.get("bundle_name")), clean(row.get("source_headlines")), clean(row.get("caption_seed")),
            clean(row.get("accuracy_lock")), clean(row.get("bundle_prompt")), section,
        ])
        # Preview bundles may use explicit preview player focus rows even without stat lines.
        preview_context = " ".join([
            clean(row.get("bundle_name")), clean(row.get("bundle_type")), clean(row.get("content_family")),
            clean(row.get("asset_type")), clean(row.get("source_headlines")), clean(row.get("caption_seed")),
        ]).lower()
        has_real_stat_line = bool(re.search(r"\b\d+\s*(?:pts|reb|ast|stl|blk|goals?|assists?|saves?|kills|digs|aces)\b", blob.lower()))
        preview_focus = [x for x in preview_focus_rows() if clean(x.get("bundle_slug")) == bundle_slug or clean(x.get("bundle_name")) == bundle_name]
        if any(tok in preview_context for tok in ["preview", "schedule", "tonight in the w"]) and not has_real_stat_line and not preview_focus:
            continue
        for pf in preview_focus:
            add(bundle_slug, bundle_name, clean(pf.get("player_name")), clean(pf.get("team_name")), infer_sport_league(row, blob)[0], infer_sport_league(row, blob)[1])
        sport, league = infer_sport_league(row, blob)
        current_team = ""
        for raw in blob.splitlines():
            line = clean(raw)
            if not line:
                continue
            current_team = detect_team_for_line(line, teams, current_team)
            for name in candidate_person_names_from_line(line, teams):
                add(bundle_slug, bundle_name, name, current_team or PLAYER_TEAM_HINTS.get(name, ""), sport, league)
        if "main wnba result" in bundle_name.lower() and "dallas wings" in blob.lower() and "los angeles sparks" in blob.lower():
            for name in MAIN_RESULT_PLAYER_SET:
                add(bundle_slug, bundle_name, name, PLAYER_TEAM_HINTS.get(name, ""), sport or "basketball", league or "WNBA")

    # Only use legacy prompt fallback when there is no active Studio bundle queue.
    # This prevents stale Main WNBA player requirements from leaking into preview-only runs.
    if not req and not queue_rows:
        blob = prompt_text()
        sport, league = infer_sport_league({}, blob)
        if "Main WNBA Result" in blob and "Dallas Wings" in blob and "Los Angeles Sparks" in blob:
            for name in MAIN_RESULT_PLAYER_SET:
                add("main-wnba-result", "Main WNBA Result", name, PLAYER_TEAM_HINTS.get(name, ""), sport or "basketball", league or "WNBA")
        for raw in blob.splitlines():
            for name in candidate_person_names_from_line(raw, teams):
                add("general-bundle", "General Bundle", name, PLAYER_TEAM_HINTS.get(name, ""), sport, league)
    return req


def file_ext_from_url_or_type(url: str, ctype: str = "") -> str:
    if ctype:
        ext = mimetypes.guess_extension(ctype.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    ext = Path(urlparse(url).path).suffix
    return ext if ext.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def copy_manual_file(player_name: str) -> Tuple[str, str, str]:
    slug = slugify(player_name)
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        for p in [PLAYER_IMAGE_DIR / f"{slug}{ext}", PLAYER_IMAGE_DIR / player_name / f"{slug}{ext}", PLAYER_IMAGE_DIR / slug / f"{slug}{ext}"]:
            if p.exists():
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                dest = OUT_DIR / f"{slug}_manual{p.suffix.lower()}"
                shutil.copy2(p, dest)
                return dest.as_posix(), "manual_file", p.as_posix()
    return "", "", ""


def manual_url_rows() -> Dict[str, str]:
    out: Dict[str, str] = {}
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
    return urljoin(base, url) if base else url


def url_candidate_ok(player_name: str, team_name: str, url: str, title: str = "") -> bool:
    blob = f"{unquote(url)} {title}".lower()
    if not url.startswith("http"):
        return False
    if any(bit in blob for bit in BAD_URL_BITS):
        return False
    first = player_name.split()[0].replace("'", "").lower()
    last = player_name.split()[-1].replace("'", "").lower()
    if first not in blob and last not in blob:
        return False
    if team_name:
        team_last = team_name.split()[-1].lower()
        if team_last not in blob and not any(bit in blob for bit in GOOD_SOURCE_BITS):
            return False
    return True


def score_candidate(player_name: str, team_name: str, url: str, title: str, method: str, page_url: str = "", sport: str = "", league: str = "") -> int:
    blob = f"{unquote(url)} {title} {page_url}".lower()
    first = player_name.split()[0].replace("'", "").lower()
    last = player_name.split()[-1].replace("'", "").lower()
    score = 0
    if first in blob:
        score += 15
    if last in blob:
        score += 25
    if player_name.lower().replace("'", "") in blob.replace("'", ""):
        score += 30
    if team_name and team_name.split()[-1].lower() in blob:
        score += 15
    if league and league.lower() in blob:
        score += 12
    if sport and sport.lower() in blob:
        score += 8
    if any(bit in blob for bit in ["headshot", "portrait", "player", "roster", "athlete"]):
        score += 10
    if any(bit in blob for bit in ["espn", "wnba", "wikimedia", "wikipedia"]):
        score += 15
    if method.startswith("manual"):
        score += 100
    if method in {"wnba_roster_html", "wikipedia_pageimage", "wikidata_p18", "commons_api"}:
        score += 12
    return score


def add_candidate(out: List[Dict[str, Any]], player_name: str, team_name: str, candidate_url: str, page_url: str, title: str, method: str, sport: str = "", league: str = "") -> None:
    candidate_url = normalize_img_url(clean(candidate_url), page_url)
    if not candidate_url or not url_candidate_ok(player_name, team_name, candidate_url, title):
        return
    out.append({
        "candidate_id": sid("pcand", player_name, candidate_url),
        "player_name": player_name,
        "team_name": team_name,
        "candidate_url": candidate_url,
        "page_url": page_url,
        "source_domain": urlparse(candidate_url).netloc,
        "title": clean(title),
        "method": method,
        "score": score_candidate(player_name, team_name, candidate_url, title, method, page_url, sport, league),
        "download_status": "",
        "local_path": "",
        "width_px": 0,
        "height_px": 0,
        "mime_type": "",
        "approved": "No",
        "reject_reason": "",
    })


def image_dims(path: Path) -> Tuple[int, int]:
    if Image is None or not path.exists():
        return 0, 0
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return 0, 0


def download_image(url: str, player_name: str, method: str) -> Tuple[str, str, str, int, int, str]:
    if requests is None:
        return "", "requests_missing", "", 0, 0, ""
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code >= 400:
            return "", f"http_{r.status_code}", r.headers.get("Content-Type", ""), 0, 0, ""
        ctype = r.headers.get("Content-Type", "")
        ext = file_ext_from_url_or_type(url, ctype)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = OUT_DIR / f"{slugify(player_name)}_{sid('img', url)}{ext}"
        raw_path.write_bytes(r.content)
        w, h = image_dims(raw_path)
        if w < MIN_WIDTH or h < MIN_HEIGHT:
            return raw_path.as_posix(), "too_small", ctype, w, h, raw_path.as_posix()
        return raw_path.as_posix(), "downloaded", ctype, w, h, raw_path.as_posix()
    except Exception:
        return "", "download_error", "", 0, 0, ""


def wnba_roster_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if requests is None:
        return out
    for page_url in TEAM_ROSTER_URLS.get(team, []):
        try:
            time.sleep(REQUEST_SLEEP)
            r = requests.get(page_url, headers=HEADERS, timeout=25)
            if r.status_code >= 400:
                continue
            text = r.text
            low = text.lower()
            first = player.split()[0].lower()
            last = player.split()[-1].lower()
            if first not in low and last not in low:
                continue
            if BeautifulSoup is not None:
                soup = BeautifulSoup(text, "html.parser")
                for img in soup.select("img[src],img[data-src],source[srcset]"):
                    alt = clean(img.get("alt") or img.get("aria-label") or img.get("title") or "")
                    blob = alt.lower()
                    if player.lower() in blob or last in blob:
                        src = img.get("src") or img.get("data-src") or (img.get("srcset", "").split(" ")[0])
                        add_candidate(out, player, team, src, page_url, alt, "wnba_roster_html", sport, league)
        except Exception:
            continue
    return out


def wikipedia_pageimage_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
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
                "gsrsearch": f'"{player}" {sport or league or "athlete"}',
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
                add_candidate(out, player, team, thumb, page_url, title, "wikipedia_pageimage", sport, league)
    except Exception:
        pass
    return out


def commons_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
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
                "gsrsearch": f'{player} {sport or league or "athlete"}',
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
            u = infos[0].get("url", "")
            add_candidate(out, player, team, u, f"https://commons.wikimedia.org/wiki/{quote(title.replace(' ', '_'))}", title, "commons_api", sport, league)
    except Exception:
        pass
    return out


def wikidata_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if requests is None:
        return out
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={"action": "wbsearchentities", "search": player, "language": "en", "format": "json", "limit": "3"},
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
                params={"action": "wbgetclaims", "entity": qid, "property": "P18", "format": "json"},
                headers=HEADERS,
                timeout=20,
            )
            for claim in c.json().get("claims", {}).get("P18", []):
                fn = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                if fn:
                    u = f"https://commons.wikimedia.org/wiki/Special:Redirect/file/{quote(fn)}"
                    add_candidate(out, player, team, u, f"https://www.wikidata.org/wiki/{qid}", f"{label} {desc}", "wikidata_p18", sport, league)
    except Exception:
        pass
    return out


def duckduckgo_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not FREE_SEARCH_ENABLED or DDGS is None:
        return out
    queries = [
        f'"{player}" "{team}" {league or sport or "athlete"} photo',
        f'"{player}" {league or sport or "athlete"} headshot',
        f'"{player}" {sport or league or "athlete"} portrait',
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
                add_candidate(out, player, team, url, page, title, "duckduckgo_images_free", sport, league)
        except Exception:
            continue
    return out


def bing_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not BING_API_KEY or requests is None:
        return out
    for q in [f"{player} {team} {league or sport or 'athlete'} photo", f"{player} {team} headshot {league or sport or 'athlete'}", f"{player} {sport or league or 'athlete'} portrait"]:
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
                add_candidate(out, player, team, clean(item.get("contentUrl")), clean(item.get("hostPageUrl")), clean(item.get("name")), "bing_image_search", sport, league)
        except Exception:
            continue
    return out


def serpapi_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not SERPAPI_KEY or requests is None:
        return out
    try:
        time.sleep(REQUEST_SLEEP)
        r = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google_images", "q": f"{player} {team} {league or sport or 'athlete'} photo", "api_key": SERPAPI_KEY, "safe": "active"},
            headers=HEADERS,
            timeout=25,
        )
        if r.status_code >= 400:
            return out
        for item in r.json().get("images_results", [])[:MAX_CANDIDATES]:
            add_candidate(out, player, team, clean(item.get("original") or item.get("thumbnail")), clean(item.get("source") or item.get("link")), clean(item.get("title")), "serpapi_google_images", sport, league)
    except Exception:
        pass
    return out


def gather_candidates(player: str, team: str, sport: str = "", league: str = "") -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    candidates.extend(wnba_roster_candidates(player, team, sport, league))
    candidates.extend(wikipedia_pageimage_candidates(player, team, sport, league))
    candidates.extend(wikidata_candidates(player, team, sport, league))
    candidates.extend(commons_candidates(player, team, sport, league))
    candidates.extend(duckduckgo_candidates(player, team, sport, league))
    candidates.extend(serpapi_candidates(player, team, sport, league))
    candidates.extend(bing_candidates(player, team, sport, league))
    seen = set()
    out: List[Dict[str, Any]] = []
    for c in sorted(candidates, key=lambda x: int(x.get("score") or 0), reverse=True):
        u = c.get("candidate_url")
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(c)
    return out[: MAX_CANDIDATES * 4]


def make_asset_row(player_name: str, team_name: str, local_path: str, source_url: str, method: str, sport: str = "athlete", league: str = "") -> Tuple[Dict[str, str], Dict[str, str]]:
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
        "approved_by": "HSD people/player image sourcing pipeline",
        "approved_utc": now(),
        "usage_scope": "HSD social graphics",
        "notes": f"Required people/player image sourced via {method}."
    }
    player = {
        "player_id": f"{slugify(league or sport or 'athlete')}_{slugify(player_name)}",
        "sport": sport or "athlete",
        "league": league,
        "player_slug": slugify(player_name),
        "player_name": player_name,
        "headshot_asset_id": approved_id,
        "status": "asset_found",
        "notes": f"Required people/player image sourced via {method}."
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

    for bundle_slug, bundle_name, player_name, team_name, sport, league in required_players():
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
                    "width_px": w, "height_px": h, "mime_type": ctype, "approved": "Yes" if path and dl_status == "downloaded" else "No", "reject_reason": "" if path and dl_status == "downloaded" else dl_status,
                })
                if path and dl_status == "downloaded":
                    local_path, source_url, method, status = path, url, "manual_csv", f"found_{dl_status}"

            if not local_path:
                for c in gather_candidates(player_name, team_name, sport, league):
                    url = c["candidate_url"]
                    path, dl_status, ctype, w, h, _ = download_image(url, player_name, c["method"])
                    c["download_status"] = dl_status
                    c["local_path"] = path
                    c["width_px"] = w
                    c["height_px"] = h
                    c["mime_type"] = ctype
                    approved_now = bool(path) and dl_status == "downloaded" and int(c.get("score") or 0) >= AUTO_APPROVE_SCORE
                    c["approved"] = "Yes" if approved_now else "No"
                    c["reject_reason"] = "" if approved_now else (dl_status if not path or dl_status != "downloaded" else f"score_below_{AUTO_APPROVE_SCORE}")
                    candidate_rows.append(c)
                    if approved_now:
                        local_path = path
                        source_url = url
                        method = c["method"]
                        status = f"found_{dl_status}"
                        break

            if local_path:
                approved, player = make_asset_row(player_name, team_name, local_path, source_url, method, sport, league)
                approved_id = approved["approved_asset_id"]
                added_approved.append(approved)
                added_players.append(player)
            else:
                notes = "Required people/player image missing. Free pipeline tried local/manual files, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images. Add a manual image file or source URL if unresolved."

        requirements.append({
            "bundle_slug": bundle_slug,
            "bundle_name": bundle_name,
            "sport": sport,
            "league": league,
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
        "# HSD People and Player Image Sourcing Report",
        "",
        f"Generated: {now()}",
        f"Version: {VERSION}",
        "",
        f"People/player images required: {'Yes' if PLAYER_IMAGES_REQUIRED else 'No'}",
        f"Required people rows: {len(requirements)}",
        f"Found required people/player images: {len(found)}",
        f"Missing required people/player images: {len(missing)}",
        f"Free search enabled: {'Yes' if FREE_SEARCH_ENABLED else 'No'}",
        f"DuckDuckGo package available: {'Yes' if DDGS is not None else 'No'}",
        f"Candidate rows inspected: {len(candidate_rows)}",
        "",
        "## Required people and players",
        "",
    ]
    for r in requirements:
        lines.append(f"- {r['status']} | {r['bundle_slug']} | {r['player_name']} | {r['team_name']} | {r.get('local_path') or 'missing'} | {r.get('sourcing_method')}")
    if missing:
        lines += [
            "", "## Missing image action", "",
            "The no-paid-API lane tried local files, manual CSV, official WNBA roster pages when applicable, Wikipedia/Wikidata/Commons, and DuckDuckGo Images.",
            "For any remaining misses, add a file such as `player_image_assets/paige-bueckers.png` or add `manual_player_assets.csv` with `player_name,source_url`. This works for non-WNBA athletes too.",
            "",
        ]
    Path(OUT_REPORT).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Created HSD people/player image asset outputs")
    print(json.dumps({
        "required_people": len(requirements),
        "found_required_people_images": len(found),
        "missing_required_people_images": len(missing),
        "candidate_rows": len(candidate_rows),
        "added_people_assets": len(added_approved),
    }, indent=2))


if __name__ == "__main__":
    main()
