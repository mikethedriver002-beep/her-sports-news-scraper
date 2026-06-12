from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, quote

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

VERSION = "hsd-final-score-stories-v3.2.11-bebe-ops-v2.10"

INPUT_RESULTS_CONTRACT = Path(os.environ.get("HSD_RESULTS_CONTRACT", "results_contract_v2.csv"))
POLICY_PATH = Path(os.environ.get("HSD_FINAL_SCORE_STORIES_POLICY", "config/hsd_final_score_stories_policy_v1.json"))
LOGO_REGISTRY_PATH = Path(os.environ.get("HSD_VERIFIED_LOGO_REGISTRY", "config/hsd_verified_logo_registry_v1.json"))
LOCAL_LOGO_DIR = Path(os.environ.get("HSD_OPERATOR_BRAND_LOGOS_DIR", "operator/assets/brand_logos"))
LOCAL_PLAYER_DIR = Path(os.environ.get("HSD_OPERATOR_PLAYER_IMAGES_DIR", "operator/assets/player_images"))

OUT_QUEUE = Path("ig_story_results_queue.csv")
OUT_FRAMES = Path("ig_story_results_frames.md")
OUT_PROMPT = Path("ig_story_results_graphics_prompt.md")
OUT_STATUS_CSV = Path("ig_story_results_upload_pack_status.csv")
OUT_STATUS_JSON = Path("ig_story_results_upload_pack_status.json")
OUT_MANIFEST_CSV = Path("ig_story_results_upload_manifest.csv")
OUT_GUARD_MD = Path("final_score_story_guard_report.md")
OUT_GUARD_JSON = Path("final_score_story_guard_report.json")
OUT_CAPTIONS = Path("ig_story_caption_bank.md")
OUT_POLLS = Path("ig_story_poll_stickers.md")
OUT_PLAYER_CANDIDATES = Path("ig_story_player_image_candidates.csv")
OUT_PACK_DIR = Path("ig_story_results_upload_pack")
OUT_ZIP_DIR = Path("ig_story_results_upload_pack_zips")

QUEUE_FIELDS = [
    "story_id", "story_slug", "story_title", "story_type", "event_date_local", "games_count",
    "frames_count", "source_event_ids", "teams_required", "score_summary", "status", "decision",
    "block_reason", "zip_path"
]
STATUS_FIELDS = [
    "story_id", "story_slug", "upload_pack_status", "assets_expected", "assets_ready", "assets_missing",
    "missing_asset_names", "zip_path", "notes"
]
MANIFEST_FIELDS = [
    "story_id", "story_slug", "entity_name", "entity_type", "asset_role", "source_url", "source_method",
    "local_asset_path", "asset_filename", "asset_ready", "required", "notes"
]
PLAYER_FIELDS = [
    "event_id", "game", "player_name", "team_name", "stat_label", "stat_value", "source_url",
    "local_asset_path", "download_status", "usage_status", "notes"
]

FINAL_STATUS_TOKENS = {"final", "status_final", "completed", "post", "gameover"}
LIVE_STATUS_TOKENS = {"live", "in progress", "in-progress", "halftime", "quarter", "q1", "q2", "q3", "q4", "ot"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
USER_AGENT = "HSDFinalScoreStories/2.10 (+Her Sports Daily; exact assets only)"
FETCH_TIMEOUT_SECONDS = float(os.environ.get("HSD_FINAL_SCORE_STORIES_FETCH_TIMEOUT_SECONDS", "10"))
NETWORK_ENABLED = os.environ.get("HSD_FINAL_SCORE_STORIES_NETWORK", "1").strip().lower() not in {"0", "false", "no"}

TEAM_ALIASES = {
    "Atlanta": "Atlanta Dream",
    "Chicago": "Chicago Sky",
    "Connecticut": "Connecticut Sun",
    "Dallas": "Dallas Wings",
    "Golden State": "Golden State Valkyries",
    "Indiana": "Indiana Fever",
    "Las Vegas": "Las Vegas Aces",
    "Los Angeles": "Los Angeles Sparks",
    "LA Sparks": "Los Angeles Sparks",
    "Minnesota": "Minnesota Lynx",
    "New York": "New York Liberty",
    "Phoenix": "Phoenix Mercury",
    "Portland": "Portland Fire",
    "Seattle": "Seattle Storm",
    "Toronto": "Toronto Tempo",
    "Washington": "Washington Mystics",
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slugify(v: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def sha_id(prefix: str, *parts: Any) -> str:
    return prefix + "_" + hashlib.sha1("|".join(clean(p) for p in parts).encode("utf-8")).hexdigest()[:14]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def safe_unlink_tree(path: Path) -> None:
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def norm_team(name: str) -> str:
    name = clean(name)
    return TEAM_ALIASES.get(name, name)


def policy() -> Dict[str, Any]:
    default = {
        "max_results": 4,
        "max_result_age_hours": 36,
        "story_title_single_day": "Last Night in the W",
        "story_title_same_day": "Finals in the W",
        "story_shape": "1080x1920",
        "require_exact_team_logos": True,
        "allow_text_logo_fallback": False,
        "player_images": {"mode": "aggressive_optional", "required_for_scoreboard": False},
        "espn_fetch": {"enabled": True, "days_back": 2, "league": "wnba"},
    }
    cfg = read_json(POLICY_PATH)
    if isinstance(cfg, dict):
        # Shallow merge is enough for this policy.
        for k, v in cfg.items():
            if isinstance(v, dict) and isinstance(default.get(k), dict):
                default[k].update(v)
            else:
                default[k] = v
    return default


def parse_iso_date(value: str) -> str:
    value = clean(value)
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", value)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", value)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""


def age_hours_for_date(event_date: str) -> Optional[float]:
    if not event_date:
        return None
    try:
        y, m, d = [int(x) for x in event_date.split("-")]
        # Noon UTC avoids treating date-only finals as stale immediately after midnight.
        dt = datetime(y, m, d, 12, 0, 0, tzinfo=timezone.utc)
        return max(0.0, (now_utc() - dt).total_seconds() / 3600.0)
    except Exception:
        return None


def is_final_contract_row(row: Dict[str, str], max_age_hours: float) -> Tuple[bool, str]:
    kind = clean(row.get("row_kind")).lower()
    status = clean(row.get("status")).lower()
    eligibility = clean(row.get("content_eligibility")).lower()
    reason = clean(row.get("freshness_reason")).lower()
    if kind != "result":
        return False, f"row_kind={kind or 'missing'}"
    if any(tok in status for tok in LIVE_STATUS_TOKENS) or "live_game_not_final" in reason:
        return False, "live/non-final game held out"
    if eligibility != "eligible":
        return False, f"content_eligibility={eligibility or 'missing'}"
    if not ("final" in status or "final_only" in reason or clean(row.get("winner_team_name"))):
        return False, "missing final signal"
    event_date = clean(row.get("event_date_local"))
    age = age_hours_for_date(event_date)
    if age is not None and age > max_age_hours:
        return False, f"final older than {max_age_hours:.1f}h ({age:.1f}h)"
    return True, "verified recent final"


def parse_score_display(score_display: str) -> List[Dict[str, Any]]:
    s = clean(score_display)
    # Supports "Team A 106 - Team B 114" and en/em dashes.
    m = re.match(r"^(.+?)\s+(\d{1,3})\s*[-–—]\s*(.+?)\s+(\d{1,3})$", s)
    if not m:
        return []
    return [
        {"team": norm_team(m.group(1)), "score": int(m.group(2))},
        {"team": norm_team(m.group(3)), "score": int(m.group(4))},
    ]


def final_row_to_game(row: Dict[str, str]) -> Dict[str, Any]:
    event_date = clean(row.get("event_date_local"))
    teams_scores = parse_score_display(row.get("score_display", ""))
    winner = norm_team(row.get("winner_team_name"))
    loser = norm_team(row.get("loser_team_name"))
    if not teams_scores and winner and loser:
        teams_scores = [{"team": winner, "score": ""}, {"team": loser, "score": ""}]
    if not winner and teams_scores:
        ordered = sorted([x for x in teams_scores if isinstance(x.get("score"), int)], key=lambda x: x["score"], reverse=True)
        if ordered:
            winner = ordered[0]["team"]
            loser = ordered[-1]["team"] if len(ordered) > 1 else ""
    if winner and teams_scores:
        teams_scores = sorted(teams_scores, key=lambda x: (x.get("team") != winner, -(x.get("score") if isinstance(x.get("score"), int) else -1)))
    score_summary = ""
    if teams_scores:
        score_summary = " · ".join(f"{x['team']} {x['score']}" if x.get("score") != "" else x["team"] for x in teams_scores)
    teams = [x["team"] for x in teams_scores if x.get("team")]
    for t in [winner, loser]:
        if t and t not in teams:
            teams.append(t)
    headline = clean(row.get("headline")) or (f"{winner} beat {loser}" if winner and loser else score_summary)
    return {
        "event_id": clean(row.get("event_id")) or sha_id("event", headline, event_date, score_summary),
        "event_date_local": event_date,
        "headline": headline,
        "winner": winner,
        "loser": loser,
        "teams": teams,
        "teams_scores": teams_scores,
        "score_summary": score_summary or clean(row.get("score_display")),
        "source_id": clean(row.get("source_id")),
        "source_url": clean(row.get("source_url")),
        "source": "results_contract_v2.csv",
    }


def dedupe_games(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[str, Dict[str, Any]] = {}
    for g in games:
        key = clean(g.get("event_id")) or "|".join(sorted(g.get("teams", []))) + "|" + clean(g.get("event_date_local"))
        by_key.setdefault(key, g)
    return list(by_key.values())


def collect_contract_finals(cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    max_age = float(cfg.get("max_result_age_hours", 36))
    games: List[Dict[str, Any]] = []
    guard_notes: List[str] = []
    for row in read_csv(INPUT_RESULTS_CONTRACT):
        ok, reason = is_final_contract_row(row, max_age)
        label = clean(row.get("headline")) or clean(row.get("score_display")) or clean(row.get("event_id"))
        guard_notes.append(f"{'ALLOW' if ok else 'HOLD'} | {reason} | {label}")
        if ok:
            games.append(final_row_to_game(row))
    return dedupe_games(games), guard_notes


def looks_like_image_payload(raw: bytes, content_type: str = "") -> bool:
    head = raw[:1200].lower()
    ctype = content_type.lower()
    return (
        "image/" in ctype or b"<svg" in head or raw.startswith(b"\x89PNG") or raw.startswith(b"\xff\xd8")
        or (raw.startswith(b"RIFF") and b"WEBP" in raw[:20])
    )


def ext_for_url(url: str, content_type: str = "") -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in IMAGE_SUFFIXES else ".asset"


def blocked_substrings_for_team(registry: Dict[str, Any], team: str) -> List[str]:
    team_info = ((registry.get("teams") or {}).get(team) or {}) if isinstance(registry, dict) else {}
    return [clean(x) for x in team_info.get("blocked_url_substrings", []) if clean(x)]


def url_blocked_for_team(url: str, registry: Dict[str, Any], team: str) -> bool:
    return any(x and x in url for x in blocked_substrings_for_team(registry, team))


def local_logo_candidates(team: str) -> List[Path]:
    slugs = {slugify(team), slugify(team).replace("-", "_")}
    out: List[Path] = []
    if not LOCAL_LOGO_DIR.exists():
        return out
    for p in LOCAL_LOGO_DIR.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        stem = slugify(p.stem)
        if stem in slugs or stem.startswith(slugify(team)):
            out.append(p)
    return sorted(out)


def scrape_logo_urls_from_page(page_url: str, team: str, registry: Dict[str, Any]) -> List[str]:
    if not requests or not NETWORK_ENABLED:
        return []
    urls: List[str] = []
    try:
        r = requests.get(page_url, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT_SECONDS)
        if r.status_code >= 400 or not r.text:
            return []
        html = r.text
    except Exception:
        return []
    candidates = re.findall(r'''(?:src|href|content)=["']([^"']+)["']''', html, flags=re.I)
    team_slug = slugify(team)
    tokens = [x for x in team_slug.split("-") if len(x) > 2]
    for raw in candidates:
        u = urljoin(page_url, raw)
        low = u.lower()
        if url_blocked_for_team(u, registry, team):
            continue
        if not any(x in low for x in ["logo", "primary", "icon", "team", "mark", "cropped"] + tokens):
            continue
        if any(x in low for x in ["sprite", "favicon", "apple-touch", "placeholder", "background"]):
            continue
        if urlparse(u).scheme not in {"http", "https"}:
            continue
        if u not in urls:
            urls.append(u)
    return urls[:12]


def registry_logo_urls(team: str, registry: Dict[str, Any]) -> List[str]:
    """Return direct verified logo URLs only. Page crawling is attempted later only if direct URLs fail."""
    teams = registry.get("teams") or {}
    info = teams.get(team) or {}
    urls: List[str] = []
    for u in info.get("direct_urls", []) or []:
        if clean(u) and not url_blocked_for_team(clean(u), registry, team):
            urls.append(clean(u))
    return urls


def registry_scraped_logo_urls(team: str, registry: Dict[str, Any]) -> List[str]:
    teams = registry.get("teams") or {}
    info = teams.get(team) or {}
    urls: List[str] = []
    for page in info.get("page_urls", []) or []:
        for u in scrape_logo_urls_from_page(clean(page), team, registry):
            if u not in urls:
                urls.append(u)
    return urls


def download_url(url: str, dest: Path) -> Tuple[str, str]:
    if not NETWORK_ENABLED:
        return "", "network_disabled"
    if not requests:
        return "", "requests_unavailable"
    try:
        r = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "image/svg+xml,image/png,image/jpeg,image/webp,*/*"},
            timeout=FETCH_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        if r.status_code >= 400 or not r.content:
            return "", f"download_failed_status_{r.status_code}"
        if not looks_like_image_payload(r.content, r.headers.get("content-type", "")):
            return "", "download_not_image_payload"
        ext = ext_for_url(r.url or url, r.headers.get("content-type", ""))
        if ext in {".html", ".htm", ".asset"}:
            ext = ".svg" if b"<svg" in r.content[:1200].lower() else ".png"
        target = dest.with_suffix(ext)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(r.content)
        return target.as_posix(), f"downloaded:{r.status_code}:{urlparse(r.url or url).netloc}"
    except Exception as exc:
        return "", f"download_exception:{type(exc).__name__}"


def resolve_team_logo(team: str, registry: Dict[str, Any], dest_dir: Path) -> Dict[str, Any]:
    team = norm_team(team)
    # Highest trust: operator-approved local files.
    for p in local_logo_candidates(team):
        target = dest_dir / f"{slugify(team)}_operator-approved{p.suffix.lower()}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": p.as_posix(), "source_method": "operator_local_logo", "local_asset_path": target.as_posix(), "asset_ready": "Yes", "notes": "operator-approved local logo"}

    # Verified registry direct/current official URLs first.
    for idx, url in enumerate(registry_logo_urls(team, registry), start=1):
        if url_blocked_for_team(url, registry, team):
            continue
        path, status = download_url(url, dest_dir / f"{slugify(team)}_verified-logo-{idx}")
        if path:
            return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": url, "source_method": "verified_registry_direct_url", "local_asset_path": path, "asset_ready": "Yes", "notes": status}

    # Official/current team pages only after direct URLs fail.
    for idx, url in enumerate(registry_scraped_logo_urls(team, registry), start=1):
        if url_blocked_for_team(url, registry, team):
            continue
        path, status = download_url(url, dest_dir / f"{slugify(team)}_official-page-logo-{idx}")
        if path:
            return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": url, "source_method": "official_page_logo_candidate", "local_asset_path": path, "asset_ready": "Yes", "notes": status}

    return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": "", "source_method": "not_found", "local_asset_path": "", "asset_ready": "No", "notes": "missing exact real team logo; text fallback prohibited"}


def espn_scoreboard_dates(cfg: Dict[str, Any]) -> List[str]:
    days_back = int(((cfg.get("espn_fetch") or {}).get("days_back", 2)))
    today = now_utc().date()
    return [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(days_back + 1)]


def collect_espn_finals_and_players(cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    fetch_cfg = cfg.get("espn_fetch") or {}
    if not fetch_cfg.get("enabled", True) or not requests or not NETWORK_ENABLED:
        return [], [], ["ESPN fetch disabled, network disabled, or requests unavailable"]
    games: List[Dict[str, Any]] = []
    players: List[Dict[str, Any]] = []
    notes: List[str] = []
    for d in espn_scoreboard_dates(cfg):
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard?dates={d}"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT_SECONDS)
            if r.status_code >= 400:
                notes.append(f"ESPN {d}: status {r.status_code}")
                continue
            data = r.json()
        except Exception as exc:
            notes.append(f"ESPN {d}: {type(exc).__name__}")
            continue
        for ev in data.get("events", []) or []:
            comp = (ev.get("competitions") or [{}])[0]
            status = ((comp.get("status") or {}).get("type") or {})
            if not status.get("completed"):
                continue
            competitors = comp.get("competitors", []) or []
            teams_scores: List[Dict[str, Any]] = []
            winner = loser = ""
            for c in competitors:
                team = norm_team(((c.get("team") or {}).get("displayName") or (c.get("team") or {}).get("shortDisplayName") or ""))
                try:
                    score = int(c.get("score"))
                except Exception:
                    score = ""
                if not team:
                    continue
                teams_scores.append({"team": team, "score": score})
                if c.get("winner"):
                    winner = team
            if teams_scores:
                teams_scores = sorted(teams_scores, key=lambda x: -(x.get("score") if isinstance(x.get("score"), int) else -1))
                winner = winner or teams_scores[0]["team"]
                loser = teams_scores[-1]["team"] if len(teams_scores) > 1 else ""
            event_dt = parse_iso_date(ev.get("date", "")) or f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            score_summary = " · ".join(f"{x['team']} {x['score']}" for x in teams_scores)
            games.append({
                "event_id": clean(ev.get("id")) or sha_id("espn_event", event_dt, score_summary),
                "event_date_local": event_dt,
                "headline": clean(ev.get("shortName") or ev.get("name")) or f"{winner} beat {loser}",
                "winner": winner,
                "loser": loser,
                "teams": [x["team"] for x in teams_scores],
                "teams_scores": teams_scores,
                "score_summary": score_summary,
                "source_id": "espn_wnba_scoreboard",
                "source_url": url,
                "source": "espn_scoreboard_json",
            })
            # Optional leaders/headshots; never required for score-story cards.
            for c in competitors:
                team = norm_team(((c.get("team") or {}).get("displayName") or ""))
                for leader_group in c.get("leaders", []) or []:
                    stat_label = clean(leader_group.get("displayName") or leader_group.get("name"))
                    for leader in leader_group.get("leaders", []) or []:
                        athlete = leader.get("athlete") or {}
                        name = clean(athlete.get("displayName") or athlete.get("fullName"))
                        href = clean(((athlete.get("headshot") or {}).get("href")))
                        value = clean(leader.get("displayValue") or leader.get("value"))
                        if name:
                            players.append({"event_id": clean(ev.get("id")), "game": score_summary, "player_name": name, "team_name": team, "stat_label": stat_label, "stat_value": value, "source_url": href, "local_asset_path": "", "download_status": "not_downloaded", "usage_status": "optional_exact_candidate", "notes": "ESPN leader/headshot candidate; optional only"})
    return dedupe_games(games), players, notes


def download_optional_player_images(players: List[Dict[str, Any]], dest_dir: Path, limit: int = 8) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for row in players:
        name = clean(row.get("player_name"))
        url = clean(row.get("source_url"))
        if not name or not url or name in seen:
            out.append(row)
            continue
        seen.add(name)
        if len([r for r in out if r.get("local_asset_path")]) >= limit:
            row["download_status"] = "skipped_limit"
            out.append(row)
            continue
        path, status = download_url(url, dest_dir / f"{slugify(name)}_espn-headshot")
        row = dict(row)
        row["local_asset_path"] = path
        row["download_status"] = status
        row["usage_status"] = "optional_exact_candidate_downloaded" if path else "optional_exact_candidate_not_ready"
        out.append(row)
    return out


def choose_games(contract_games: List[Dict[str, Any]], espn_games: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Prefer contract rows because they already passed BeBe final-only guard; backfill from ESPN only when needed.
    max_results = int(cfg.get("max_results", 4))
    games = dedupe_games(contract_games + espn_games)
    games = sorted(games, key=lambda g: (clean(g.get("event_date_local")), clean(g.get("headline"))), reverse=True)
    return games[:max_results]


def game_line(game: Dict[str, Any]) -> str:
    if game.get("teams_scores"):
        return " · ".join(f"{x['team']} {x['score']}" for x in game["teams_scores"])
    return clean(game.get("score_summary") or game.get("headline"))


def build_frames(games: List[Dict[str, Any]], title: str) -> List[Dict[str, str]]:
    frames: List[Dict[str, str]] = []
    frames.append({
        "frame": "1",
        "role": "cover_scoreboard",
        "headline": title,
        "subhead": "Final scores from the W",
        "body": " / ".join(game_line(g) for g in games[:3]),
        "sticker": "Poll: Best win of the night?",
    })
    for idx, game in enumerate(games[:3], start=2):
        winner = clean(game.get("winner"))
        headline = f"{winner} gets the win" if winner else "Final Score"
        frames.append({
            "frame": str(idx),
            "role": "final_score_card",
            "headline": headline,
            "subhead": "FINAL",
            "body": game_line(game),
            "sticker": "Question: What stood out?" if idx == 2 else "",
        })
    frames.append({
        "frame": str(len(frames) + 1),
        "role": "engagement_cta",
        "headline": "Best win of the night?",
        "subhead": "Tap in with HSD",
        "body": "Vote in the poll or reply with your pick.",
        "sticker": "Poll: Fever / Liberty / Other",
    })
    return frames[:5]


def create_prompt(title: str, games: List[Dict[str, Any]], frames: List[Dict[str, str]], player_rows: List[Dict[str, Any]], required_teams: List[str]) -> str:
    games_txt = "\n".join(f"- {game_line(g)}" for g in games)
    frames_txt = "\n".join(f"Frame {f['frame']} ({f['role']}): {f['headline']} — {f['subhead']} — {f['body']}" for f in frames)
    player_names = ", ".join([clean(p.get("player_name")) for p in player_rows if clean(p.get("local_asset_path"))][:6]) or "None attached."
    team_list = ", ".join(required_teams)
    return f"""Create an Instagram Stories result pack for Her Sports Daily.

Output exactly {len(frames)} separate 1080x1920 PNG story frames. Do not make a single grid. Do not make feed-size graphics.

Title: {title}

Final scores to render exactly:
{games_txt}

Required team logos attached for: {team_list}
Use only the uploaded team logo files. Do not fetch external logo URLs. Do not invent, redraw, recolor, or substitute logos.

Optional exact player/headshot candidates attached: {player_names}
Use a player image only when it is attached and clearly mapped to that player. If unsure, omit the player image. Never substitute a player.

Frame plan:
{frames_txt}

Style direction: premium women’s sports media, sharp HSD desk energy, high contrast, clean score hierarchy, bold readable type, designed for mobile Stories. Keep space for Instagram stickers on the CTA/poll frame.

Display copy rules:
- You may render: FINAL, Last Night in the W, Final scores, Best win of the night?, What stood out?
- Do not render: Verified Final, source-safe context, BUNDLE LOCKED FACTS, target date, workflow labels, QA labels, all games listed, accuracy lock, or internal instructions.
- No live/in-progress games. No upcoming previews. No invented stats, records, quotes, injuries, or rankings.
- One small HSD watermark/bug only, top-left safe zone.
""".strip() + "\n"


def zip_folder(folder: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(folder))


def main() -> None:
    cfg = policy()
    registry = read_json(LOGO_REGISTRY_PATH)
    safe_unlink_tree(OUT_PACK_DIR)
    safe_unlink_tree(OUT_ZIP_DIR)
    OUT_PACK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_ZIP_DIR.mkdir(parents=True, exist_ok=True)

    contract_games, contract_guard_notes = collect_contract_finals(cfg)
    espn_games, player_candidates, espn_notes = collect_espn_finals_and_players(cfg)
    games = choose_games(contract_games, espn_games, cfg)

    guard_issues: List[str] = []
    if not games:
        guard_issues.append("no recent verified final games available for IG Story result graphics")

    required_teams = sorted({team for g in games for team in g.get("teams", []) if clean(team)})
    story_slug = "last-night-in-the-w"
    story_id = sha_id("story", story_slug, ";".join(g.get("event_id", "") for g in games))
    title = clean(cfg.get("story_title_single_day")) or "Last Night in the W"

    folder = OUT_PACK_DIR / story_slug
    asset_dir = folder / "assets_original"
    player_dir = folder / "optional_player_images"
    folder.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)
    player_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows: List[Dict[str, Any]] = []
    ready = 0
    missing: List[str] = []
    for team in required_teams:
        resolved = resolve_team_logo(team, registry, asset_dir)
        asset_ready = resolved.get("asset_ready") == "Yes" and bool(resolved.get("local_asset_path"))
        if asset_ready:
            ready += 1
        else:
            missing.append(team)
        manifest_rows.append({
            "story_id": story_id,
            "story_slug": story_slug,
            "entity_name": team,
            "entity_type": "team",
            "asset_role": "team_logo",
            "source_url": resolved.get("source_url", ""),
            "source_method": resolved.get("source_method", ""),
            "local_asset_path": resolved.get("local_asset_path", ""),
            "asset_filename": Path(resolved.get("local_asset_path", "")).name if resolved.get("local_asset_path") else "",
            "asset_ready": "Yes" if asset_ready else "No",
            "required": "Yes",
            "notes": resolved.get("notes", ""),
        })

    player_candidates = download_optional_player_images(player_candidates, player_dir, limit=8)
    for p in player_candidates:
        if p.get("local_asset_path"):
            manifest_rows.append({
                "story_id": story_id,
                "story_slug": story_slug,
                "entity_name": p.get("player_name", ""),
                "entity_type": "player",
                "asset_role": "optional_player_headshot",
                "source_url": p.get("source_url", ""),
                "source_method": "espn_leader_headshot_optional",
                "local_asset_path": p.get("local_asset_path", ""),
                "asset_filename": Path(p.get("local_asset_path", "")).name if p.get("local_asset_path") else "",
                "asset_ready": "Yes",
                "required": "No",
                "notes": p.get("notes", ""),
            })

    frames = build_frames(games, title) if games else []
    prompt = create_prompt(title, games, frames, player_candidates, required_teams) if games else "No verified final-score story pack created.\n"
    (folder / "00_PROMPT_TO_PASTE.md").write_text(prompt, encoding="utf-8")
    (folder / "01_UPLOAD_INSTRUCTIONS.md").write_text(
        "# HSD Final Score Stories Upload Instructions\n\n"
        "Upload `00_PROMPT_TO_PASTE.md` and every file inside `assets_original/`. Optional player images may be uploaded from `optional_player_images/` only if present.\n\n"
        "Do not allow the graphics chat to fetch logos or player images. Use attached real assets only. If any required logo is missing, do not generate.\n",
        encoding="utf-8",
    )

    upload_status = "ready_with_review"
    block_reason = ""
    if guard_issues:
        upload_status = "blocked_no_recent_finals"
        block_reason = "; ".join(guard_issues)
    elif missing:
        upload_status = "blocked_missing_exact_team_logos"
        block_reason = "Missing exact team logos: " + "; ".join(missing)

    zip_path = ""
    if upload_status in {"ready", "ready_with_review"}:
        zip_file = OUT_ZIP_DIR / f"{story_slug}_ig_story_results_upload_pack.zip"
        zip_folder(folder, zip_file)
        zip_path = zip_file.as_posix()

    score_summary = " | ".join(game_line(g) for g in games)
    queue_rows = [{
        "story_id": story_id,
        "story_slug": story_slug,
        "story_title": title,
        "story_type": "ig_story_final_scores",
        "event_date_local": ";".join(sorted({clean(g.get("event_date_local")) for g in games if clean(g.get("event_date_local"))})),
        "games_count": len(games),
        "frames_count": len(frames),
        "source_event_ids": json.dumps([g.get("event_id") for g in games]),
        "teams_required": "; ".join(required_teams),
        "score_summary": score_summary,
        "status": upload_status,
        "decision": "ready_for_graphics_review" if upload_status in {"ready", "ready_with_review"} else "blocked",
        "block_reason": block_reason,
        "zip_path": zip_path,
    }]
    status_rows = [{
        "story_id": story_id,
        "story_slug": story_slug,
        "upload_pack_status": upload_status,
        "assets_expected": len(required_teams),
        "assets_ready": ready,
        "assets_missing": len(missing),
        "missing_asset_names": "; ".join(missing),
        "zip_path": zip_path,
        "notes": "Final-score IG Story upload pack is ready with manual review." if zip_path else block_reason,
    }]

    write_csv(OUT_QUEUE, queue_rows, QUEUE_FIELDS)
    write_csv(OUT_STATUS_CSV, status_rows, STATUS_FIELDS)
    write_csv(OUT_MANIFEST_CSV, manifest_rows, MANIFEST_FIELDS)
    write_csv(OUT_PLAYER_CANDIDATES, player_candidates, PLAYER_FIELDS)

    frame_lines = ["# HSD IG Story Results Frames", "", f"Generated: {now_utc().isoformat()}", f"Version: {VERSION}", ""]
    if not games:
        frame_lines.append("No recent verified final-score frames were created.")
    for f in frames:
        frame_lines += [
            f"## Frame {f['frame']} — {f['role']}",
            "",
            f"- Headline: {f['headline']}",
            f"- Subhead: {f['subhead']}",
            f"- Body: {f['body']}",
            f"- Sticker: {f['sticker'] or 'none'}",
            "",
        ]
    OUT_FRAMES.write_text("\n".join(frame_lines) + "\n", encoding="utf-8")

    OUT_PROMPT.write_text("# HSD IG Story Results Graphics Prompt\n\n```text\n" + prompt + "```\n", encoding="utf-8")
    OUT_CAPTIONS.write_text(
        "# HSD IG Story Caption Bank\n\n"
        + (f"Final scores from the W: {score_summary}\n\n" if score_summary else "No caption generated because no final-score story pack was ready.\n")
        + "Suggested story caption: Which result stood out most?\n",
        encoding="utf-8",
    )
    OUT_POLLS.write_text(
        "# HSD IG Story Poll / Sticker Ideas\n\n"
        "- Poll: Best win of the night?\n"
        "- Question: What stood out?\n"
        "- Slider: How big was this result?\n",
        encoding="utf-8",
    )

    guard = {
        "version": VERSION,
        "generated_at_utc": now_utc().isoformat(),
        "upload_pack_status": upload_status,
        "games_from_results_contract": len(contract_games),
        "games_from_espn_fetch": len(espn_games),
        "games_selected": len(games),
        "required_team_logos": len(required_teams),
        "logos_ready": ready,
        "logos_missing": missing,
        "issues": guard_issues + ([block_reason] if block_reason else []),
        "contract_guard_notes": contract_guard_notes[:40],
        "espn_fetch_notes": espn_notes[:20],
        "outputs": [
            OUT_QUEUE.as_posix(), OUT_FRAMES.as_posix(), OUT_PROMPT.as_posix(), OUT_STATUS_CSV.as_posix(),
            OUT_MANIFEST_CSV.as_posix(), OUT_CAPTIONS.as_posix(), OUT_POLLS.as_posix(), OUT_PLAYER_CANDIDATES.as_posix(),
        ],
    }
    OUT_GUARD_JSON.write_text(json.dumps(guard, indent=2), encoding="utf-8")
    guard_lines = [
        "# HSD Final Score Story Guard Report",
        "",
        f"Generated: {guard['generated_at_utc']}",
        f"Version: {VERSION}",
        "",
        f"- upload_pack_status: {upload_status}",
        f"- games from results_contract_v2.csv: {len(contract_games)}",
        f"- games from ESPN scoreboard fetch: {len(espn_games)}",
        f"- games selected: {len(games)}",
        f"- required team logos: {len(required_teams)}",
        f"- logos ready: {ready}",
        f"- logos missing: {len(missing)}",
        f"- zip: {zip_path or 'none'}",
        "",
    ]
    if missing:
        guard_lines += ["## Missing exact team logos", "", *[f"- {x}" for x in missing], ""]
    guard_lines += ["## Selected finals", ""] + [f"- {game_line(g)}" for g in games] + [""]
    guard_lines += ["## Contract final-only guard", ""] + [f"- {x}" for x in contract_guard_notes[:25]] + [""]
    if espn_notes:
        guard_lines += ["## ESPN fetch notes", ""] + [f"- {x}" for x in espn_notes[:20]] + [""]
    OUT_GUARD_MD.write_text("\n".join(guard_lines), encoding="utf-8")

    OUT_STATUS_JSON.write_text(json.dumps({"version": VERSION, "generated_at_utc": now_utc().isoformat(), "stories": status_rows}, indent=2), encoding="utf-8")

    print(json.dumps({"final_score_story_status": upload_status, "games_selected": len(games), "logos_ready": ready, "logos_missing": len(missing), "zip": zip_path}, indent=2))


if __name__ == "__main__":
    main()
