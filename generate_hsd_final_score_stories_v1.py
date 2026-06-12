from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
import shutil
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

VERSION = "hsd-final-score-stories-v3.2.13-bebe-ops-v2.11"

INPUT_RESULTS_CONTRACT = Path(os.environ.get("HSD_RESULTS_CONTRACT", "results_contract_v2.csv"))
POLICY_PATH = Path(os.environ.get("HSD_FINAL_SCORE_STORIES_POLICY", "config/hsd_final_score_stories_policy_v1.json"))
LOGO_REGISTRY_PATH = Path(os.environ.get("HSD_VERIFIED_LOGO_REGISTRY", "config/hsd_verified_logo_registry_v1.json"))
LOCAL_LOGO_DIR = Path(os.environ.get("HSD_OPERATOR_BRAND_LOGOS_DIR", "operator/assets/brand_logos"))

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

QUEUE_FIELDS = ["story_id", "story_slug", "story_title", "story_type", "event_date_local", "games_count", "frames_count", "source_event_ids", "teams_required", "score_summary", "status", "decision", "block_reason", "zip_path"]
STATUS_FIELDS = ["story_id", "story_slug", "upload_pack_status", "assets_expected", "assets_ready", "assets_missing", "missing_asset_names", "zip_path", "notes"]
MANIFEST_FIELDS = ["story_id", "story_slug", "entity_name", "entity_type", "asset_role", "source_url", "source_method", "local_asset_path", "asset_filename", "asset_ready", "required", "notes"]
PLAYER_FIELDS = ["event_id", "game", "player_name", "team_name", "stat_label", "stat_value", "source_url", "local_asset_path", "download_status", "usage_status", "notes"]

LIVE_STATUS_TOKENS = {"live", "in progress", "in-progress", "halftime", "quarter", "q1", "q2", "q3", "q4", "ot"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
USER_AGENT = "HSDFinalScoreStories/2.10.1 (+Her Sports Daily; exact assets only)"
NETWORK_ENABLED = os.environ.get("HSD_FINAL_SCORE_STORIES_NETWORK", "1").strip().lower() not in {"0", "false", "no"}
START = time.monotonic()

TEAM_ALIASES = {
    "Atlanta": "Atlanta Dream", "Chicago": "Chicago Sky", "Connecticut": "Connecticut Sun",
    "Dallas": "Dallas Wings", "Golden State": "Golden State Valkyries", "Indiana": "Indiana Fever",
    "Las Vegas": "Las Vegas Aces", "Los Angeles": "Los Angeles Sparks", "LA Sparks": "Los Angeles Sparks",
    "Minnesota": "Minnesota Lynx", "New York": "New York Liberty", "Phoenix": "Phoenix Mercury",
    "Portland": "Portland Fire", "Seattle": "Seattle Storm", "Toronto": "Toronto Tempo", "Washington": "Washington Mystics",
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
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

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
        "min_contract_finals_before_skip_espn": 1,
        "max_total_runtime_seconds": 55,
        "logo_download_timeout_seconds": 5,
        "espn_download_timeout_seconds": 5,
        "max_logo_urls_per_team": 4,
        "story_title_single_day": "Last Night in the W",
        "story_shape": "1080x1920",
        "require_exact_team_logos": True,
        "allow_text_logo_fallback": False,
        "player_images": {"mode": "aggressive_optional", "required_for_scoreboard": False},
        "espn_fetch": {"enabled": True, "mode": "backfill_only", "days_back": 2, "league": "wnba"},
    }
    cfg = read_json(POLICY_PATH)
    if isinstance(cfg, dict):
        for k, v in cfg.items():
            if isinstance(v, dict) and isinstance(default.get(k), dict):
                default[k].update(v)
            else:
                default[k] = v
    return default

def time_left(cfg: Dict[str, Any]) -> float:
    return float(cfg.get("max_total_runtime_seconds", 55)) - (time.monotonic() - START)

def can_fetch(cfg: Dict[str, Any], min_left: float = 3.0) -> bool:
    return NETWORK_ENABLED and requests is not None and time_left(cfg) > min_left

def age_hours_for_date(event_date: str) -> Optional[float]:
    if not event_date:
        return None
    try:
        y, m, d = [int(x) for x in event_date.split("-")]
        dt = datetime(y, m, d, 12, 0, 0, tzinfo=timezone.utc)
        return max(0.0, (now_utc() - dt).total_seconds() / 3600.0)
    except Exception:
        return None

def parse_iso_date(value: str) -> str:
    value = clean(value)
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", value)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", value)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ""

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
    age = age_hours_for_date(clean(row.get("event_date_local")))
    if age is not None and age > max_age_hours:
        return False, f"final older than {max_age_hours:.1f}h ({age:.1f}h)"
    return True, "verified recent final"

def parse_score_display(score_display: str) -> List[Dict[str, Any]]:
    s = clean(score_display)
    m = re.match(r"^(.+?)\s+(\d{1,3})\s*[-–—]\s*(.+?)\s+(\d{1,3})$", s)
    if not m:
        return []
    return [{"team": norm_team(m.group(1)), "score": int(m.group(2))}, {"team": norm_team(m.group(3)), "score": int(m.group(4))}]

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
    teams = [x["team"] for x in teams_scores if x.get("team")]
    for t in [winner, loser]:
        if t and t not in teams:
            teams.append(t)
    score_summary = " · ".join(f"{x['team']} {x['score']}" if x.get("score") != "" else x["team"] for x in teams_scores)
    headline = clean(row.get("headline")) or (f"{winner} beat {loser}" if winner and loser else score_summary)
    return {"event_id": clean(row.get("event_id")) or sha_id("event", headline, event_date, score_summary), "event_date_local": event_date, "headline": headline, "winner": winner, "loser": loser, "teams": teams, "teams_scores": teams_scores, "score_summary": score_summary or clean(row.get("score_display")), "source_id": clean(row.get("source_id")), "source_url": clean(row.get("source_url")), "source": "results_contract_v2.csv"}

def dedupe_games(games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[str, Dict[str, Any]] = {}
    for g in games:
        key = clean(g.get("event_id")) or "|".join(sorted(g.get("teams", []))) + "|" + clean(g.get("event_date_local"))
        by_key.setdefault(key, g)
    return list(by_key.values())

def collect_contract_finals(cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    max_age = float(cfg.get("max_result_age_hours", 36))
    games: List[Dict[str, Any]] = []
    notes: List[str] = []
    for row in read_csv(INPUT_RESULTS_CONTRACT):
        ok, reason = is_final_contract_row(row, max_age)
        label = clean(row.get("headline")) or clean(row.get("score_display")) or clean(row.get("event_id"))
        notes.append(f"{'ALLOW' if ok else 'HOLD'} | {reason} | {label}")
        if ok:
            games.append(final_row_to_game(row))
    return dedupe_games(games), notes

def looks_like_image_payload(raw: bytes, content_type: str = "") -> bool:
    head = raw[:1200].lower()
    ctype = content_type.lower()
    return "image/" in ctype or b"<svg" in head or raw.startswith(b"\x89PNG") or raw.startswith(b"\xff\xd8") or (raw.startswith(b"RIFF") and b"WEBP" in raw[:20])

def ext_for_url(url: str, content_type: str = "") -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in IMAGE_SUFFIXES else ".asset"

def url_blocked_for_team(url: str, registry: Dict[str, Any], team: str) -> bool:
    info = ((registry.get("teams") or {}).get(team) or {}) if isinstance(registry, dict) else {}
    return any(clean(x) and clean(x) in url for x in info.get("blocked_url_substrings", []) or [])

def local_logo_candidates(team: str) -> List[Path]:
    slugs = {slugify(team), slugify(team).replace("-", "_")}
    if not LOCAL_LOGO_DIR.exists():
        return []
    out: List[Path] = []
    for p in LOCAL_LOGO_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES:
            stem = slugify(p.stem)
            if stem in slugs or stem.startswith(slugify(team)):
                out.append(p)
    return sorted(out)

def registry_logo_urls(team: str, registry: Dict[str, Any], cfg: Dict[str, Any]) -> List[str]:
    info = ((registry.get("teams") or {}).get(team) or {}) if isinstance(registry, dict) else {}
    urls: List[str] = []
    for u in info.get("direct_urls", []) or []:
        u = clean(u)
        if u and not url_blocked_for_team(u, registry, team) and u not in urls:
            urls.append(u)
    return urls[:int(cfg.get("max_logo_urls_per_team", 4))]

def scrape_logo_urls_from_page(page_url: str, team: str, registry: Dict[str, Any], cfg: Dict[str, Any]) -> List[str]:
    if not can_fetch(cfg):
        return []
    urls: List[str] = []
    try:
        timeout = min(float(cfg.get("logo_download_timeout_seconds", 5)), max(1.0, time_left(cfg)))
        r = requests.get(page_url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if r.status_code >= 400 or not r.text:
            return []
        candidates = re.findall(r'''(?:src|href|content)=["']([^"']+)["']''', r.text, flags=re.I)
    except Exception:
        return []
    tokens = [x for x in slugify(team).split("-") if len(x) > 2]
    for raw in candidates:
        u = urljoin(page_url, raw)
        low = u.lower()
        if url_blocked_for_team(u, registry, team):
            continue
        if not any(x in low for x in ["logo", "primary", "icon", "team", "mark", "cropped"] + tokens):
            continue
        if any(x in low for x in ["sprite", "favicon", "apple-touch", "placeholder", "background"]):
            continue
        if urlparse(u).scheme in {"http", "https"} and u not in urls:
            urls.append(u)
    return urls[:int(cfg.get("max_logo_urls_per_team", 4))]

def registry_scraped_logo_urls(team: str, registry: Dict[str, Any], cfg: Dict[str, Any]) -> List[str]:
    info = ((registry.get("teams") or {}).get(team) or {}) if isinstance(registry, dict) else {}
    urls: List[str] = []
    for page in info.get("page_urls", []) or []:
        for u in scrape_logo_urls_from_page(clean(page), team, registry, cfg):
            if u not in urls:
                urls.append(u)
    return urls[:int(cfg.get("max_logo_urls_per_team", 4))]

def download_url(url: str, dest: Path, cfg: Dict[str, Any], kind: str = "logo") -> Tuple[str, str]:
    if not can_fetch(cfg):
        return "", "network_unavailable_or_deadline_reached"
    timeout_key = "logo_download_timeout_seconds" if kind == "logo" else "espn_download_timeout_seconds"
    timeout = min(float(cfg.get(timeout_key, 5)), max(1.0, time_left(cfg)))
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "image/svg+xml,image/png,image/jpeg,image/webp,*/*"}, timeout=timeout, allow_redirects=True)
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

def resolve_team_logo(team: str, registry: Dict[str, Any], dest_dir: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    team = norm_team(team)
    for p in local_logo_candidates(team):
        target = dest_dir / f"{slugify(team)}_operator-approved{p.suffix.lower()}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": p.as_posix(), "source_method": "operator_local_logo", "local_asset_path": target.as_posix(), "asset_ready": "Yes", "notes": "operator-approved local logo"}
    attempts: List[str] = []
    for idx, url in enumerate(registry_logo_urls(team, registry, cfg), start=1):
        path, status = download_url(url, dest_dir / f"{slugify(team)}_verified-logo-{idx}", cfg, kind="logo")
        attempts.append(f"direct:{status}")
        if path:
            return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": url, "source_method": "verified_registry_direct_url", "local_asset_path": path, "asset_ready": "Yes", "notes": status}
    for idx, url in enumerate(registry_scraped_logo_urls(team, registry, cfg), start=1):
        path, status = download_url(url, dest_dir / f"{slugify(team)}_official-page-logo-{idx}", cfg, kind="logo")
        attempts.append(f"page:{status}")
        if path:
            return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": url, "source_method": "official_page_logo_candidate", "local_asset_path": path, "asset_ready": "Yes", "notes": status}
    return {"entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": "", "source_method": "not_found", "local_asset_path": "", "asset_ready": "No", "notes": "missing exact real team logo; text fallback prohibited; attempts=" + " | ".join(attempts[:4])}

def collect_espn_finals(cfg: Dict[str, Any], contract_count: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    fetch_cfg = cfg.get("espn_fetch") or {}
    mode = clean(fetch_cfg.get("mode") or "backfill_only")
    min_contract = int(cfg.get("min_contract_finals_before_skip_espn", 1))
    if mode == "backfill_only" and contract_count >= min_contract:
        return [], [f"Skipped ESPN backfill because Results Contract already had {contract_count} verified final(s)."]
    if not fetch_cfg.get("enabled", True) or not can_fetch(cfg):
        return [], ["ESPN fetch skipped: disabled, network unavailable, or deadline reached."]
    games: List[Dict[str, Any]] = []
    notes: List[str] = []
    days_back = int(fetch_cfg.get("days_back", 2))
    today = now_utc().date()
    for i in range(days_back + 1):
        if not can_fetch(cfg):
            notes.append("ESPN fetch stopped because runtime deadline was reached.")
            break
        d = (today - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard?dates={d}"
        try:
            timeout = min(float(cfg.get("espn_download_timeout_seconds", 5)), max(1.0, time_left(cfg)))
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
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
            teams_scores: List[Dict[str, Any]] = []
            winner = loser = ""
            for c in comp.get("competitors", []) or []:
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
            games.append({"event_id": clean(ev.get("id")) or sha_id("espn_event", event_dt, score_summary), "event_date_local": event_dt, "headline": clean(ev.get("shortName") or ev.get("name")) or f"{winner} beat {loser}", "winner": winner, "loser": loser, "teams": [x["team"] for x in teams_scores], "teams_scores": teams_scores, "score_summary": score_summary, "source_id": "espn_wnba_scoreboard", "source_url": url, "source": "espn_scoreboard_json"})
    return dedupe_games(games), notes

def choose_games(contract_games: List[Dict[str, Any]], espn_games: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    games = dedupe_games(contract_games + espn_games)
    games = sorted(games, key=lambda g: (clean(g.get("event_date_local")), clean(g.get("headline"))), reverse=True)
    return games[:int(cfg.get("max_results", 4))]

def game_line(game: Dict[str, Any]) -> str:
    return " · ".join(f"{x['team']} {x['score']}" for x in game.get("teams_scores", []) if x.get("team")) or clean(game.get("score_summary") or game.get("headline"))

def build_frames(games: List[Dict[str, Any]], title: str) -> List[Dict[str, str]]:
    """Build one cover, one card per selected final, and one CTA.

    Critical production rule: every selected final must appear in its own
    game-card frame. Do not cap game cards at three. If four finals are
    selected, output six frames total: cover + four cards + CTA.
    """
    game_lines = [game_line(g) for g in games]
    count = len(game_lines)
    cover_body = " / ".join(game_lines)
    if count >= 4:
        cover_body = f"{count} finals from the W. Every game gets a card."
    frames = [{
        "frame": "1",
        "role": "cover_scoreboard",
        "headline": title,
        "subhead": f"{count} final score{'s' if count != 1 else ''} from the W",
        "body": cover_body,
        "sticker": "Poll: Best win of the night?",
    }]
    for idx, game in enumerate(games, start=2):
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
        "sticker": "Poll: Best win / Biggest statement / Other",
    })
    return frames

def story_frame_coverage_issues(games: List[Dict[str, Any]], frames: List[Dict[str, str]]) -> List[str]:
    """Return selected game lines that do not have a dedicated final_score_card."""
    card_bodies = {clean(f.get("body")) for f in frames if f.get("role") == "final_score_card"}
    missing = []
    for game in games:
        line = clean(game_line(game))
        if line and line not in card_bodies:
            missing.append(line)
    return missing

def create_prompt(title: str, games: List[Dict[str, Any]], frames: List[Dict[str, str]], required_teams: List[str]) -> str:
    games_txt = "\n".join(f"- {game_line(g)}" for g in games)
    frames_txt = "\n".join(f"Frame {f['frame']} ({f['role']}): {f['headline']} — {f['subhead']} — {f['body']}" for f in frames)
    return f"""Create an Instagram Stories result pack for Her Sports Daily.

Output exactly {len(frames)} separate 1080x1920 PNG story frames. Do not make a single grid. Do not make feed-size graphics.

Title: {title}

Final scores to render exactly:
{games_txt}

Required team logos attached for: {', '.join(required_teams)}
Use only the uploaded team logo files. Do not fetch external logo URLs. Do not invent, redraw, recolor, or substitute logos.

Player images are optional. Use a player image only when it is attached and clearly mapped to that player. If unsure, omit the player image. Never substitute a player.

Frame plan:
{frames_txt}

Coverage rule: every final score listed above must appear in a dedicated final_score_card frame. Do not drop any game to fit the CTA. If four finals are selected, output cover plus four game cards plus CTA.

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

def write_all_outputs(cfg: Dict[str, Any], registry: Dict[str, Any], games: List[Dict[str, Any]], contract_count: int, espn_count: int, contract_notes: List[str], espn_notes: List[str], fatal: str = "") -> None:
    story_slug = "last-night-in-the-w"
    story_id = sha_id("story", story_slug, ";".join(g.get("event_id", "") for g in games), VERSION)
    title = clean(cfg.get("story_title_single_day")) or "Last Night in the W"
    folder = OUT_PACK_DIR / story_slug
    asset_dir = folder / "assets_original"
    folder.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)
    required_teams = sorted({team for g in games for team in g.get("teams", []) if clean(team)})
    manifest_rows: List[Dict[str, Any]] = []
    ready = 0
    missing: List[str] = []
    for team in required_teams:
        resolved = resolve_team_logo(team, registry, asset_dir, cfg)
        asset_ready = resolved.get("asset_ready") == "Yes" and bool(resolved.get("local_asset_path"))
        if asset_ready:
            ready += 1
        else:
            missing.append(team)
        manifest_rows.append({"story_id": story_id, "story_slug": story_slug, "entity_name": team, "entity_type": "team", "asset_role": "team_logo", "source_url": resolved.get("source_url", ""), "source_method": resolved.get("source_method", ""), "local_asset_path": resolved.get("local_asset_path", ""), "asset_filename": Path(resolved.get("local_asset_path", "")).name if resolved.get("local_asset_path") else "", "asset_ready": "Yes" if asset_ready else "No", "required": "Yes", "notes": resolved.get("notes", "")})
    frames = build_frames(games, title) if games else []
    frame_coverage_missing = story_frame_coverage_issues(games, frames) if games else []
    prompt = create_prompt(title, games, frames, required_teams) if games else "No verified final-score story pack created.\n"
    (folder / "00_PROMPT_TO_PASTE.md").write_text(prompt, encoding="utf-8")
    (folder / "01_UPLOAD_INSTRUCTIONS.md").write_text("# HSD Final Score Stories Upload Instructions\n\nUpload `00_PROMPT_TO_PASTE.md` and every file inside `assets_original/`. Do not allow the graphics chat to fetch logos or player images. Use attached real assets only. If any required logo is missing, do not generate.\n", encoding="utf-8")
    guard_issues: List[str] = []
    upload_status = "ready_with_review"
    block_reason = ""
    if fatal:
        upload_status = "blocked_generation_error"
        block_reason = fatal
        guard_issues.append(fatal)
    elif not games:
        upload_status = "blocked_no_recent_finals"
        block_reason = "no recent verified final games available for IG Story result graphics"
        guard_issues.append(block_reason)
    elif frame_coverage_missing:
        upload_status = "blocked_story_frame_coverage"
        block_reason = "Story frame plan omitted selected final(s): " + "; ".join(frame_coverage_missing)
        guard_issues.append(block_reason)
    elif missing:
        upload_status = "blocked_missing_exact_team_logos"
        block_reason = "Missing exact team logos: " + "; ".join(missing)
    zip_path = ""
    if upload_status in {"ready", "ready_with_review"}:
        zip_file = OUT_ZIP_DIR / f"{story_slug}_ig_story_results_upload_pack.zip"
        zip_folder(folder, zip_file)
        zip_path = zip_file.as_posix()
    score_summary = " | ".join(game_line(g) for g in games)
    queue_rows = [{"story_id": story_id, "story_slug": story_slug, "story_title": title, "story_type": "ig_story_final_scores", "event_date_local": ";".join(sorted({clean(g.get("event_date_local")) for g in games if clean(g.get("event_date_local"))})), "games_count": len(games), "frames_count": len(frames), "source_event_ids": json.dumps([g.get("event_id") for g in games]), "teams_required": "; ".join(required_teams), "score_summary": score_summary, "status": upload_status, "decision": "ready_for_graphics_review" if upload_status in {"ready", "ready_with_review"} else "blocked", "block_reason": block_reason, "zip_path": zip_path}]
    status_rows = [{"story_id": story_id, "story_slug": story_slug, "upload_pack_status": upload_status, "assets_expected": len(required_teams), "assets_ready": ready, "assets_missing": len(missing), "missing_asset_names": "; ".join(missing), "zip_path": zip_path, "notes": "Final-score IG Story upload pack is ready with manual review." if zip_path else block_reason}]
    write_csv(OUT_QUEUE, queue_rows, QUEUE_FIELDS)
    write_csv(OUT_STATUS_CSV, status_rows, STATUS_FIELDS)
    write_csv(OUT_MANIFEST_CSV, manifest_rows, MANIFEST_FIELDS)
    write_csv(OUT_PLAYER_CANDIDATES, [], PLAYER_FIELDS)
    frame_lines = ["# HSD IG Story Results Frames", "", f"Generated: {now_utc().isoformat()}", f"Version: {VERSION}", ""]
    if not games:
        frame_lines.append("No recent verified final-score frames were created.")
    for f in frames:
        frame_lines += [f"## Frame {f['frame']} — {f['role']}", "", f"- Headline: {f['headline']}", f"- Subhead: {f['subhead']}", f"- Body: {f['body']}", f"- Sticker: {f['sticker'] or 'none'}", ""]
    OUT_FRAMES.write_text("\n".join(frame_lines) + "\n", encoding="utf-8")
    OUT_PROMPT.write_text("# HSD IG Story Results Graphics Prompt\n\n```text\n" + prompt + "```\n", encoding="utf-8")
    OUT_CAPTIONS.write_text("# HSD IG Story Caption Bank\n\n" + (f"Final scores from the W: {score_summary}\n\n" if score_summary else "No caption generated because no final-score story pack was ready.\n") + "Suggested story caption: Which result stood out most?\n", encoding="utf-8")
    OUT_POLLS.write_text("# HSD IG Story Poll / Sticker Ideas\n\n- Poll: Best win of the night?\n- Question: What stood out?\n- Slider: How big was this result?\n", encoding="utf-8")
    guard = {"version": VERSION, "generated_at_utc": now_utc().isoformat(), "runtime_seconds": round(time.monotonic() - START, 2), "upload_pack_status": upload_status, "games_from_results_contract": contract_count, "games_from_espn_fetch": espn_count, "games_selected": len(games), "frame_coverage_missing": frame_coverage_missing, "required_team_logos": len(required_teams), "logos_ready": ready, "logos_missing": missing, "issues": guard_issues + ([block_reason] if block_reason else []), "contract_guard_notes": contract_notes[:60], "espn_fetch_notes": espn_notes[:30], "outputs": [OUT_QUEUE.as_posix(), OUT_FRAMES.as_posix(), OUT_PROMPT.as_posix(), OUT_STATUS_CSV.as_posix(), OUT_MANIFEST_CSV.as_posix(), OUT_CAPTIONS.as_posix(), OUT_POLLS.as_posix(), OUT_PLAYER_CANDIDATES.as_posix()]}
    OUT_GUARD_JSON.write_text(json.dumps(guard, indent=2), encoding="utf-8")
    guard_lines = ["# HSD Final Score Story Guard Report", "", f"Generated: {guard['generated_at_utc']}", f"Version: {VERSION}", "", f"- upload_pack_status: {upload_status}", f"- runtime_seconds: {guard['runtime_seconds']}", f"- games from results_contract_v2.csv: {contract_count}", f"- games from ESPN scoreboard fetch: {espn_count}", f"- games selected: {len(games)}", f"- frame coverage missing: {len(frame_coverage_missing)}", f"- required team logos: {len(required_teams)}", f"- logos ready: {ready}", f"- logos missing: {len(missing)}", f"- zip: {zip_path or 'none'}", ""]
    if missing:
        guard_lines += ["## Missing exact team logos", "", *[f"- {x}" for x in missing], ""]
    guard_lines += ["## Selected finals", ""] + ([f"- {game_line(g)}" for g in games] if games else ["- none"]) + [""]
    guard_lines += ["## Contract final-only guard", ""] + [f"- {x}" for x in contract_notes[:35]] + [""]
    guard_lines += ["## ESPN/backfill notes", ""] + [f"- {x}" for x in (espn_notes[:20] or ["none"])] + [""]
    OUT_GUARD_MD.write_text("\n".join(guard_lines), encoding="utf-8")
    OUT_STATUS_JSON.write_text(json.dumps({"version": VERSION, "generated_at_utc": now_utc().isoformat(), "stories": status_rows}, indent=2), encoding="utf-8")

def main() -> None:
    cfg = policy()
    registry = read_json(LOGO_REGISTRY_PATH)
    safe_unlink_tree(OUT_PACK_DIR)
    safe_unlink_tree(OUT_ZIP_DIR)
    OUT_PACK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_ZIP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        contract_games, contract_notes = collect_contract_finals(cfg)
        espn_games, espn_notes = collect_espn_finals(cfg, len(contract_games))
        games = choose_games(contract_games, espn_games, cfg)
        write_all_outputs(cfg, registry, games, len(contract_games), len(espn_games), contract_notes, espn_notes)
        status = json.loads(OUT_GUARD_JSON.read_text(encoding="utf-8")).get("upload_pack_status")
        print(json.dumps({"final_score_story_status": status, "games_selected": len(games), "runtime_seconds": round(time.monotonic() - START, 2)}, indent=2))
    except Exception as exc:
        try:
            write_all_outputs(cfg, registry, [], 0, 0, [], [], fatal=f"{type(exc).__name__}: {exc}")
        finally:
            print(json.dumps({"final_score_story_status": "blocked_generation_error", "error": f"{type(exc).__name__}: {exc}"}, indent=2))

if __name__ == "__main__":
    main()
