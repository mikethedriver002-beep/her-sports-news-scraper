from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup


VERSION = "news-sync-v1"

INPUT_RESULTS_QUEUE = os.environ.get("HSD_RESULTS_GRAPHICS_QUEUE", "results_graphics_queue.md")
INPUT_RESULTS_RECS = os.environ.get("HSD_RESULTS_RECOMMENDATIONS", "daily_results_recommendations.md")
INPUT_WNBA_BOX = os.environ.get("HSD_WNBA_BOX_SUMMARY", "wnba_box_score_summary.md")
INPUT_RESULTS_HUB = os.environ.get("HSD_RESULTS_HUB", "results_system_hub.md")

SOURCE_REGISTRY_FILE = os.environ.get("HSD_NEWS_SOURCE_REGISTRY", "news_source_registry.json")
ANGLE_RULES_FILE = os.environ.get("HSD_NEWS_ANGLE_RULES", "news_angle_rules.json")

MAX_MUST_POST = int(os.environ.get("HSD_NEWS_MAX_MUST_POST", "5"))
MAX_STRONG_MAYBE = int(os.environ.get("HSD_NEWS_MAX_STRONG_MAYBE", "5"))
FETCH_TIMEOUT = int(os.environ.get("HSD_NEWS_FETCH_TIMEOUT", "15"))
REQUEST_SLEEP_SECONDS = float(os.environ.get("HSD_NEWS_REQUEST_SLEEP_SECONDS", "0.35"))
ENABLE_FETCH = os.environ.get("HSD_NEWS_ENABLE_FETCH", "true").lower() != "false"

NEWS_CANDIDATES_CSV = "news_candidate_queue.csv"
NEWS_SOURCE_OBS_CSV = "news_source_observations.csv"
NEWS_FACT_PACKETS_CSV = "news_fact_packets.csv"
NEWS_BRIEF_QUEUE_MD = "news_brief_queue.md"
NEWS_SOCIAL_PACKETS_MD = "news_social_packets.md"
NEWS_GRAPHICS_HANDOFF_MD = "news_graphics_handoff.md"
NEWS_MANUAL_REVIEW_CSV = "news_manual_review_queue.csv"
NEWS_SYNC_HUB_MD = "news_sync_hub.md"
NEWS_MANIFEST_JSON = "news_sync_manifest.json"

USER_AGENT = "Mozilla/5.0 (compatible; HerSportsDailyNewsSync/1.0; +https://hersportsdaily.example)"


CANDIDATE_FIELDS = [
    "run_id", "candidate_id", "queue_section", "content_action", "sport", "league",
    "editorial_tier", "editorial_bucket", "template", "selected_source", "all_sources",
    "confidence", "manual_review", "editorial_rank", "outcome_type", "matchup",
    "final_score", "winner", "loser", "game_status", "date", "source_url",
    "graphics_headline", "graphics_subhead", "slide1_hook", "slide2_result",
    "slide3_context", "slide4_cta", "raw_block",
]

SOURCE_OBS_FIELDS = [
    "run_id", "candidate_id", "source_id", "source_name", "source_priority",
    "source_type", "url", "domain", "fetch_status", "http_status", "title",
    "description", "matched_terms", "published_hint", "usable_context",
    "context_signal", "fetched_at_utc", "review_flag", "notes",
]

PACKET_FIELDS = [
    "run_id", "candidate_id", "queue_section", "sport", "league", "editorial_bucket",
    "content_family", "publish_recommendation", "urgency", "headline", "dek",
    "brief_120w", "caption_hard_fact", "caption_voice", "story_text",
    "slide3_context", "graphics_handoff", "source_count", "primary_source_count",
    "source_urls_json", "context_signal", "top_performers", "review_flags",
    "manual_review", "score_accuracy_check", "rights_safe_note",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def norm(value: Any) -> str:
    return clean(value).lower()


def stable_id(*parts: Any) -> str:
    blob = "|".join(clean(p) for p in parts)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def load_json(path: str, default: Any) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            out = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                out[field] = value
            w.writerow(out)


def parse_key_value_line(line: str) -> Tuple[str, str]:
    line = line.strip()
    line = re.sub(r"^\*\*", "", line)
    line = re.sub(r"\*\*$", "", line)
    if ":" not in line:
        return "", ""
    k, v = line.split(":", 1)
    k = k.replace("**", "").strip().lower()
    v = v.replace("**", "").strip()
    return k, v


def parse_graphics_queue(text: str, run_id: str) -> List[Dict[str, Any]]:
    """
    Parses Results Desk v4.3 style `results_graphics_queue.md`.

    It does not try to re-score games. Results Desk remains the scorer of record.
    """
    blocks = re.split(r"\n---\n", text)
    candidates: List[Dict[str, Any]] = []
    current_section = ""

    for block in blocks:
        if "# MUST POST" in block:
            current_section = "MUST POST"
        elif "# STRONG MAYBE" in block:
            current_section = "STRONG MAYBE"
        elif "# WATCHLIST" in block:
            current_section = "WATCHLIST"

        if "## RESULT GRAPHIC" not in block:
            continue

        lines = [ln.rstrip() for ln in block.splitlines()]
        row: Dict[str, Any] = {"run_id": run_id, "queue_section": current_section, "raw_block": block.strip()}

        first = next((ln for ln in lines if ln.startswith("## RESULT GRAPHIC")), "")
        row["graphics_headline"] = clean(re.sub(r"^## RESULT GRAPHIC\s+\d+:\s*", "", first))
        row["candidate_id"] = stable_id(run_id, row["graphics_headline"], current_section)

        in_verified = False
        in_slide_copy = False
        slide_key = None

        for ln in lines:
            k, v = parse_key_value_line(ln)
            if k:
                mapped = {
                    "queue section": "queue_section",
                    "sport": "sport",
                    "league": "league",
                    "editorial tier": "editorial_tier",
                    "editorial bucket": "editorial_bucket",
                    "content action": "content_action",
                    "template": "template",
                    "selected source": "selected_source",
                    "all sources": "all_sources",
                    "confidence": "confidence",
                    "manual review": "manual_review",
                    "editorial rank": "editorial_rank",
                    "outcome type": "outcome_type",
                }.get(k)
                if mapped:
                    row[mapped] = clean(v)

            if ln.startswith("### Verified result context"):
                in_verified = True
                in_slide_copy = False
                continue
            if ln.startswith("### Slide copy"):
                in_verified = False
                in_slide_copy = True
                continue
            if ln.startswith("### ") and not ln.startswith("### Verified") and not ln.startswith("### Slide"):
                in_verified = False
                in_slide_copy = False

            if in_verified and ln.strip().startswith("- "):
                item = ln.strip()[2:]
                k2, v2 = parse_key_value_line(item)
                mapped2 = {
                    "matchup": "matchup",
                    "final score": "final_score",
                    "winner": "winner",
                    "loser": "loser",
                    "outcome": "outcome_type",
                    "game status": "game_status",
                    "date": "date",
                    "source url/api": "source_url",
                }.get(k2)
                if mapped2:
                    row[mapped2] = clean(v2)

            if in_slide_copy:
                if ln.startswith("**Slide 1"):
                    slide_key = "slide1_hook"
                    row[slide_key] = clean(ln.split("**", 2)[-1])
                    continue
                if ln.startswith("**Slide 2"):
                    slide_key = "slide2_result"
                    continue
                if ln.startswith("**Slide 3"):
                    slide_key = "slide3_context"
                    continue
                if ln.startswith("**Slide 4"):
                    slide_key = "slide4_cta"
                    continue
                if slide_key and ln.strip() and not ln.startswith("###"):
                    existing = row.get(slide_key, "")
                    row[slide_key] = clean((existing + " " + ln.strip()).strip())

        # sanitize and fill
        for f in CANDIDATE_FIELDS:
            row.setdefault(f, "")

        if row.get("queue_section") in {"MUST POST", "STRONG MAYBE"}:
            candidates.append(row)

    # enforce news-sync scope cap
    must = [c for c in candidates if c.get("queue_section") == "MUST POST"][:MAX_MUST_POST]
    maybe = [c for c in candidates if c.get("queue_section") == "STRONG MAYBE"][:MAX_STRONG_MAYBE]
    return must + maybe


def parse_box_score_summary(text: str) -> Dict[str, str]:
    """
    Best-effort parser for `wnba_box_score_summary.md`.
    Returns matchup/headline-ish key -> top performer text.
    """
    out: Dict[str, str] = {}
    if not text.strip():
        return out

    # The file varies across versions, so parse broadly.
    chunks = re.split(r"\n(?=##|\d+\.|\- \*\*)", text)
    for chunk in chunks:
        ch = clean(chunk)
        if not ch:
            continue

        # look for known player-stat-rich lines
        if any(name in ch for name in ["A'ja", "Arike", "Paige", "Natasha", "DeWanna", "Jackie", "Jessica", "Olivia"]):
            # key by teams if present, otherwise by first sentence
            key = ""
            team_hits = []
            for team in [
                "Dallas", "Los Angeles", "Phoenix", "Portland", "Minnesota", "Seattle",
                "Las Vegas", "Golden State", "Chicago", "Connecticut"
            ]:
                if team.lower() in ch.lower():
                    team_hits.append(team)
            if len(team_hits) >= 2:
                key = " ".join(team_hits[:2]).lower()
            else:
                key = clean(ch[:80]).lower()
            out[key] = ch

    return out


def find_top_performers(candidate: Dict[str, Any], box_map: Dict[str, str]) -> str:
    blob = " ".join([
        candidate.get("graphics_headline", ""),
        candidate.get("matchup", ""),
        candidate.get("final_score", ""),
        candidate.get("slide3_context", ""),
    ]).lower()

    best = ""
    best_score = 0
    for key, val in box_map.items():
        score = 0
        for token in key.split():
            if len(token) >= 4 and token in blob:
                score += 1
        if score > best_score:
            best_score = score
            best = val

    if best_score >= 1:
        return best
    return ""


def source_registry_defaults() -> Dict[str, Any]:
    return {
        "sources": [
            {
                "source_id": "wnba",
                "name": "WNBA official",
                "priority": 100,
                "type": "official_league",
                "sports": ["basketball"],
                "leagues_contains": ["WNBA", "NBA W"],
                "urls": ["https://www.wnba.com/"],
                "notes": "Official WNBA league source. Use for schedule, stats, news, transactions, injuries."
            },
            {
                "source_id": "espn_wnba",
                "name": "ESPN WNBA",
                "priority": 75,
                "type": "scoreboard_backup",
                "sports": ["basketball"],
                "leagues_contains": ["WNBA", "NBA W"],
                "urls": ["https://www.espn.com/wnba/scoreboard"],
                "notes": "Backup box score and story-link source."
            },
            {
                "source_id": "ap_wnba",
                "name": "AP WNBA hub",
                "priority": 70,
                "type": "wire_context",
                "sports": ["basketball"],
                "leagues_contains": ["WNBA", "NBA W"],
                "urls": ["https://apnews.com/hub/wnba-basketball"],
                "notes": "Use for wire-style context, never copied prose."
            },
            {
                "source_id": "volleyball_world",
                "name": "Volleyball World",
                "priority": 95,
                "type": "official_competition",
                "sports": ["volleyball"],
                "leagues_contains": ["VNL", "Nations League", "Volleyball"],
                "urls": ["https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/"],
                "notes": "Official VNL and global volleyball narrative source."
            },
            {
                "source_id": "cev",
                "name": "CEV",
                "priority": 85,
                "type": "official_confederation",
                "sports": ["volleyball"],
                "leagues_contains": ["CEV", "European"],
                "urls": ["https://www.cev.eu/"],
                "notes": "Official European volleyball context source."
            },
            {
                "source_id": "ehf",
                "name": "EHF Champions League Women",
                "priority": 85,
                "type": "official_competition",
                "sports": ["handball"],
                "leagues_contains": ["EHF", "Champions League"],
                "urls": ["https://ehfcl.eurohandball.com/women/"],
                "notes": "Official women's handball competition source."
            }
        ],
        "team_sources": {
            "dallas wings": ["https://wings.wnba.com/"],
            "los angeles sparks": ["https://sparks.wnba.com/"],
            "phoenix mercury": ["https://mercury.wnba.com/"],
            "minnesota lynx": ["https://lynx.wnba.com/"],
            "seattle storm": ["https://storm.wnba.com/"],
            "las vegas aces": ["https://aces.wnba.com/"],
            "golden state valkyries": ["https://valkyries.wnba.com/"],
            "chicago sky": ["https://sky.wnba.com/"],
            "connecticut sun": ["https://sun.wnba.com/"]
        }
    }


def angle_rules_defaults() -> Dict[str, Any]:
    return {
        "basketball": {
            "close_margin_max": 6,
            "statement_margin_min": 15,
            "high_score_min": 95,
            "default_family": "Tonight in the W",
        },
        "volleyball": {
            "five_set_scores": ["3-2", "2-3"],
            "default_family": "Around Women's Sports",
        },
        "context_fallbacks": {
            "basketball": "This result stands out because the verified box score gives it a real player-performance angle.",
            "volleyball": "This result matters most when paired with tournament context, rankings, or an official competition recap.",
            "default": "This result belongs in today's wider women's sports conversation, but it needs one more sourced context signal before being treated as a full story."
        }
    }


def registry_sources_for_candidate(candidate: Dict[str, Any], registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    sport = norm(candidate.get("sport"))
    league = norm(candidate.get("league"))
    matchup = norm(candidate.get("matchup"))
    result: List[Dict[str, Any]] = []

    for src in registry.get("sources", []):
        sports = [s.lower() for s in src.get("sports", [])]
        league_terms = [s.lower() for s in src.get("leagues_contains", [])]
        if sport in sports or any(term and term in league for term in league_terms):
            result.append(src)

    # team site sources for WNBA
    if sport == "basketball" or "wnba" in league or "nba w" in league:
        for team_slug, urls in registry.get("team_sources", {}).items():
            if team_slug in matchup or team_slug in norm(candidate.get("graphics_headline")):
                result.append({
                    "source_id": "team_" + team_slug.replace(" ", "_"),
                    "name": team_slug.title() + " official",
                    "priority": 90,
                    "type": "official_team",
                    "sports": ["basketball"],
                    "urls": urls,
                    "notes": "Official team site."
                })

    # de-dupe by source_id/url
    seen = set()
    deduped = []
    for src in sorted(result, key=lambda s: int(s.get("priority", 0)), reverse=True):
        key = src.get("source_id", "") + "|" + "|".join(src.get("urls", []))
        if key not in seen:
            seen.add(key)
            deduped.append(src)
    return deduped


def fetch_page_metadata(url: str) -> Dict[str, Any]:
    result = {
        "url": url,
        "domain": urlparse(url).netloc,
        "fetch_status": "not_run",
        "http_status": "",
        "title": "",
        "description": "",
        "published_hint": "",
        "notes": "",
    }
    if not ENABLE_FETCH:
        result["fetch_status"] = "disabled"
        return result

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT)
        result["http_status"] = str(r.status_code)
        if r.status_code >= 400:
            result["fetch_status"] = "http_error"
            result["notes"] = f"HTTP {r.status_code}"
            return result

        soup = BeautifulSoup(r.text, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = clean(soup.title.string)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = clean(og_title.get("content"))

        desc = ""
        for attrs in [
            {"name": "description"},
            {"property": "og:description"},
            {"name": "twitter:description"},
        ]:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                desc = clean(tag.get("content"))
                break

        published = ""
        for attrs in [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"name": "date"},
            {"itemprop": "datePublished"},
        ]:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content"):
                published = clean(tag.get("content"))
                break

        result.update({
            "fetch_status": "ok",
            "title": title[:240],
            "description": desc[:500],
            "published_hint": published[:100],
        })
    except Exception as exc:
        result["fetch_status"] = "error"
        result["notes"] = str(exc)[:240]
    return result


def terms_for_candidate(candidate: Dict[str, Any]) -> List[str]:
    terms = []
    for field in ["winner", "loser", "matchup", "graphics_headline", "league"]:
        val = clean(candidate.get(field))
        if not val:
            continue
        for part in re.split(r"\bvs\b|,| and | beat | over |\|", val, flags=re.I):
            part = clean(part)
            if len(part) >= 4:
                terms.append(part.lower())
    # remove scores and short tokens
    cleaned = []
    for term in terms:
        term = re.sub(r"\b\d+\b", "", term).strip()
        if len(term) >= 4 and term not in cleaned:
            cleaned.append(term)
    return cleaned[:12]


def source_observations_for_candidate(candidate: Dict[str, Any], registry: Dict[str, Any], run_id: str) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []
    terms = terms_for_candidate(candidate)
    sources = registry_sources_for_candidate(candidate, registry)

    for source in sources:
        for url in source.get("urls", []):
            meta = fetch_page_metadata(url)
            hay = norm(" ".join([meta.get("title", ""), meta.get("description", ""), meta.get("url", "")]))
            matched = [t for t in terms if t and t in hay]

            usable_context = "No"
            context_signal = ""
            review_flag = ""
            if meta.get("fetch_status") == "ok":
                if matched:
                    usable_context = "Yes"
                    context_signal = f"Matched source metadata terms: {', '.join(matched[:4])}"
                elif source.get("type", "").startswith("official"):
                    usable_context = "Partial"
                    context_signal = f"Official source available: {source.get('name')}"
                else:
                    usable_context = "Partial"
                    context_signal = f"Secondary source available: {source.get('name')}"
            else:
                review_flag = "source_fetch_failed"

            observations.append({
                "run_id": run_id,
                "candidate_id": candidate.get("candidate_id"),
                "source_id": source.get("source_id", ""),
                "source_name": source.get("name", ""),
                "source_priority": source.get("priority", ""),
                "source_type": source.get("type", ""),
                "url": url,
                "domain": meta.get("domain", ""),
                "fetch_status": meta.get("fetch_status", ""),
                "http_status": meta.get("http_status", ""),
                "title": meta.get("title", ""),
                "description": meta.get("description", ""),
                "matched_terms": ", ".join(matched),
                "published_hint": meta.get("published_hint", ""),
                "usable_context": usable_context,
                "context_signal": context_signal,
                "fetched_at_utc": utc_now(),
                "review_flag": review_flag,
                "notes": meta.get("notes", "") or source.get("notes", ""),
            })
            time.sleep(REQUEST_SLEEP_SECONDS)

    return observations


def parse_score(candidate: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    # final score display usually like "dallas wings 104 - los angeles sparks 96"
    s = clean(candidate.get("final_score"))
    nums = [int(x) for x in re.findall(r"\b\d+\b", s)]
    if len(nums) >= 2:
        return nums[0], nums[1]  # away, home based on Results Desk display
    return None, None


def infer_angle(candidate: Dict[str, Any], top_performers: str, angle_rules: Dict[str, Any]) -> Tuple[str, str, str]:
    sport = norm(candidate.get("sport"))
    headline = candidate.get("graphics_headline", "")
    outcome = norm(candidate.get("outcome_type"))
    final_score = candidate.get("final_score", "")
    away_score, home_score = parse_score(candidate)
    margin = None
    if away_score is not None and home_score is not None:
        margin = abs(away_score - home_score)

    if sport == "basketball":
        family = angle_rules.get("basketball", {}).get("default_family", "Tonight in the W")
        if away_score is not None and home_score is not None and max(away_score, home_score) >= angle_rules.get("basketball", {}).get("high_score_min", 95):
            return family, "high-scoring WNBA result", "The scoreline and top-performer data give this game a clear offensive hook."
        if margin is not None and margin <= angle_rules.get("basketball", {}).get("close_margin_max", 6):
            return family, "close WNBA finish", "The margin makes this one useful as a close-finish WNBA brief."
        if margin is not None and margin >= angle_rules.get("basketball", {}).get("statement_margin_min", 15):
            return family, "statement WNBA win", "The margin gives this result a stronger team-form angle than a routine score post."
        if top_performers:
            return family, "player-led WNBA result", "The verified top-performer line gives this result a player-first angle."
        return family, "WNBA result watch", angle_rules.get("context_fallbacks", {}).get("basketball")

    if sport == "volleyball":
        family = angle_rules.get("volleyball", {}).get("default_family", "Around Women's Sports")
        fs = final_score.lower()
        if "3-2" in fs or "2-3" in fs:
            return family, "five-set volleyball result", "A five-set final gives this result enough tension for a short tournament brief."
        if "3-0" in fs or "0-3" in fs:
            return family, "straight-sets volleyball result", "The clean scoreline works best when paired with ranking, stage, or official competition context."
        return family, "volleyball results watch", angle_rules.get("context_fallbacks", {}).get("volleyball")

    if outcome == "draw":
        return "Around Women's Sports", "draw result", "A draw is valid here, but it needs competition context before becoming a full news brief."

    return "Around Women's Sports", "results watch", angle_rules.get("context_fallbacks", {}).get("default")


def source_summary(observations: List[Dict[str, Any]]) -> Tuple[int, int, List[str], str, List[str]]:
    usable = [o for o in observations if o.get("usable_context") in {"Yes", "Partial"}]
    primary = [o for o in usable if "official" in norm(o.get("source_type"))]
    urls = [o.get("url", "") for o in usable if o.get("url")]
    signals = [o.get("context_signal", "") for o in usable if o.get("context_signal")]
    flags = [o.get("review_flag", "") for o in observations if o.get("review_flag")]
    return len(usable), len(primary), urls, (signals[0] if signals else ""), flags


def make_brief(candidate: Dict[str, Any], top_performers: str, context_signal: str, angle_tag: str) -> Tuple[str, str, str, str, str, str, str]:
    winner = clean(candidate.get("winner"))
    loser = clean(candidate.get("loser"))
    final_score = clean(candidate.get("final_score"))
    headline_base = clean(candidate.get("graphics_headline")) or f"{winner} beat {loser}"
    sport = norm(candidate.get("sport"))
    content_family = "Tonight in the W" if sport == "basketball" else "Around Women's Sports"

    if top_performers:
        # Pull a concise top performer phrase without over-rewriting the source.
        performer_sentence = clean(top_performers)
        performer_sentence = re.sub(r"^[-*\d.\s]+", "", performer_sentence)
        performer_sentence = performer_sentence[:260]
        dek = f"{final_score}. {performer_sentence}"
        context_line = performer_sentence
    else:
        dek = clean(candidate.get("graphics_subhead")) or final_score
        context_line = context_signal or clean(candidate.get("slide3_context"))

    if winner and loser:
        lede = f"{winner} beat {loser}, with the verified final listed as {final_score}."
    elif clean(candidate.get("outcome_type")) == "draw":
        lede = f"{headline_base}, with the verified final listed as {final_score}."
    else:
        lede = f"{headline_base}. The verified final was {final_score}."

    if top_performers:
        second = f"The best production angle is {angle_tag}: {context_line}"
    elif context_signal:
        second = f"The strongest current context signal is source-backed: {context_signal}"
    else:
        second = "The result is verified, but richer narrative context still needs an official recap, stat page, or competition note."

    close = "Her Sports Daily will treat the score as verified and keep player or milestone claims limited to sourced fields."
    brief = f"{lede} {second} {close}"

    # Trim to around 120-160 words if it gets too long
    words = brief.split()
    if len(words) > 155:
        brief = " ".join(words[:155]).rstrip(",.;") + "."

    caption_hard = f"{headline_base}. Verified final: {final_score}."
    if top_performers:
        caption_voice = f"{headline_base}. The box-score angle makes this one worth more than a score-only post."
    elif "five-set" in angle_tag:
        caption_voice = f"{headline_base}. Five sets, one result, and a clean Around Women's Sports angle."
    else:
        caption_voice = f"{headline_base}. A verified result for the HSD radar."

    story_text = f"{headline_base}\n\nVerified final: {final_score}\n\nAngle: {angle_tag}"
    slide3 = context_line if context_line else clean(candidate.get("slide3_context"))
    graphics_handoff = (
        f"Use as {content_family}. Headline: {headline_base}. "
        f"Final score: {final_score}. Slide 3 context: {slide3}. "
        "Do not invent player stats beyond the packet."
    )
    return headline_base, dek, brief, caption_hard, caption_voice, story_text, graphics_handoff


def build_fact_packet(candidate: Dict[str, Any], observations: List[Dict[str, Any]], box_map: Dict[str, str], angle_rules: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    top_performers = find_top_performers(candidate, box_map)
    content_family, angle_tag, angle_context = infer_angle(candidate, top_performers, angle_rules)
    src_count, primary_count, urls, source_context_signal, flags = source_summary(observations)

    context_signal = source_context_signal or angle_context
    headline, dek, brief, cap_hard, cap_voice, story_text, graphics_handoff = make_brief(
        candidate, top_performers, context_signal, angle_tag
    )

    manual_review = "No"
    review_flags = list(flags)

    if clean(candidate.get("manual_review")).lower() == "yes":
        manual_review = "Yes"
        review_flags.append("results_desk_manual_review")

    # Strong rule: P1 needs either top performers or at least one usable/official source.
    if candidate.get("queue_section") == "MUST POST":
        if not top_performers and primary_count < 1:
            manual_review = "Yes"
            review_flags.append("no_primary_context_for_must_post")
    elif src_count < 1:
        manual_review = "Yes"
        review_flags.append("no_usable_context_for_strong_maybe")

    if "source_fetch_failed" in review_flags and src_count == 0:
        manual_review = "Yes"

    # score lock: news layer never overrides result desk final score
    score_accuracy_check = "locked_to_results_desk"

    if manual_review == "Yes":
        publish_reco = "Hold for editor"
    elif candidate.get("queue_section") == "MUST POST":
        publish_reco = "Publish short brief"
    else:
        publish_reco = "Publish if useful / use for roundup"

    urgency = "P1" if candidate.get("queue_section") == "MUST POST" else "P2"

    return {
        "run_id": run_id,
        "candidate_id": candidate.get("candidate_id"),
        "queue_section": candidate.get("queue_section"),
        "sport": candidate.get("sport"),
        "league": candidate.get("league"),
        "editorial_bucket": candidate.get("editorial_bucket"),
        "content_family": content_family,
        "publish_recommendation": publish_reco,
        "urgency": urgency,
        "headline": headline,
        "dek": dek,
        "brief_120w": brief,
        "caption_hard_fact": cap_hard,
        "caption_voice": cap_voice,
        "story_text": story_text,
        "slide3_context": clean(top_performers or context_signal or candidate.get("slide3_context")),
        "graphics_handoff": graphics_handoff,
        "source_count": src_count,
        "primary_source_count": primary_count,
        "source_urls_json": json.dumps(urls, ensure_ascii=False),
        "context_signal": context_signal,
        "top_performers": top_performers,
        "review_flags": "; ".join(sorted(set([f for f in review_flags if f]))),
        "manual_review": manual_review,
        "score_accuracy_check": score_accuracy_check,
        "rights_safe_note": "Facts and links only. Do not copy article body or source prose.",
    }


def markdown_brief_queue(packets: List[Dict[str, Any]], observations_by_candidate: Dict[str, List[Dict[str, Any]]]) -> str:
    lines = [
        "# Her Sports Daily News Brief Queue v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "This is the news layer on top of Results Desk. Results Desk remains the score source of truth.",
        "",
    ]

    for section in ["MUST POST", "STRONG MAYBE"]:
        group = [p for p in packets if p.get("queue_section") == section]
        lines.extend([f"## {section}", ""])
        if not group:
            lines.extend(["No items.", ""])
            continue

        for idx, p in enumerate(group, 1):
            cid = p.get("candidate_id")
            source_obs = observations_by_candidate.get(cid, [])
            urls = []
            try:
                urls = json.loads(p.get("source_urls_json") or "[]")
            except Exception:
                urls = []

            lines.extend([
                f"### NEWS PACKET {idx}: {p.get('headline')}",
                "",
                f"**Urgency:** {p.get('urgency')}",
                f"**Content family:** {p.get('content_family')}",
                f"**Recommendation:** {p.get('publish_recommendation')}",
                f"**Manual review:** {p.get('manual_review')}",
                f"**Review flags:** {p.get('review_flags') or 'None'}",
                f"**Source depth:** {p.get('source_count')} usable / {p.get('primary_source_count')} primary",
                "",
                "#### Headline",
                p.get("headline", ""),
                "",
                "#### Dek",
                p.get("dek", ""),
                "",
                "#### Short brief",
                p.get("brief_120w", ""),
                "",
                "#### Caption options",
                f"- Hard fact: {p.get('caption_hard_fact')}",
                f"- Voice: {p.get('caption_voice')}",
                "",
                "#### Story text",
                p.get("story_text", ""),
                "",
                "#### Slide 3 / context",
                p.get("slide3_context", ""),
                "",
                "#### Sources",
            ])

            if urls:
                for url in urls[:8]:
                    lines.append(f"- {url}")
            else:
                lines.append("- No usable source URL captured. Hold if this is Must Post.")

            if source_obs:
                lines.extend(["", "#### Source observation notes"])
                for obs in source_obs[:6]:
                    lines.append(
                        f"- {obs.get('source_name')} | {obs.get('fetch_status')} | "
                        f"{obs.get('usable_context')} | {obs.get('context_signal') or obs.get('notes')}"
                    )

            lines.extend(["", "---", ""])

    return "\n".join(lines)


def markdown_social_packets(packets: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily Social Packets v1",
        "",
        f"Generated: {utc_now()}",
        "",
    ]
    for p in packets:
        lines.extend([
            f"## {p.get('headline')}",
            "",
            f"**Queue:** {p.get('queue_section')} | **Manual review:** {p.get('manual_review')}",
            "",
            "### Instagram caption",
            p.get("caption_voice", ""),
            "",
            "### X / Threads / Bluesky",
            p.get("caption_hard_fact", ""),
            "",
            "### Story text",
            p.get("story_text", ""),
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def markdown_graphics_handoff(packets: List[Dict[str, Any]]) -> str:
    lines = [
        "# Her Sports Daily News-to-Graphics Handoff v1",
        "",
        f"Generated: {utc_now()}",
        "",
        "Use this to upgrade result graphics with news-safe context.",
        "",
    ]
    for p in packets:
        lines.extend([
            f"## {p.get('headline')}",
            "",
            f"**Content family:** {p.get('content_family')}",
            f"**Manual review:** {p.get('manual_review')}",
            "",
            p.get("graphics_handoff", ""),
            "",
            "**Accuracy lock:** Do not change score, winner, loser, or player stats beyond this packet.",
            "",
            "---",
            "",
        ])
    return "\n".join(lines)


def markdown_hub(run_id: str, candidates: List[Dict[str, Any]], observations: List[Dict[str, Any]], packets: List[Dict[str, Any]]) -> str:
    manual = [p for p in packets if p.get("manual_review") == "Yes"]
    publish = [p for p in packets if p.get("manual_review") != "Yes"]
    p1 = [p for p in packets if p.get("urgency") == "P1"]
    p2 = [p for p in packets if p.get("urgency") == "P2"]

    usable_sources = [o for o in observations if o.get("usable_context") in {"Yes", "Partial"}]
    source_failures = [o for o in observations if o.get("review_flag")]

    lines = [
        "# Her Sports Daily News Sync v1 Hub",
        "",
        f"Run ID: `{run_id}`",
        f"Generated: `{utc_now()}`",
        "",
        "## Architecture",
        "",
        "- Results Desk remains the scorer of record.",
        "- News Sync consumes Results Desk outputs and builds source-backed editorial packets.",
        "- The two systems are connected, but not merged into one fragile scraper.",
        "",
        "## Run summary",
        "",
        f"- News candidates read: {len(candidates)}",
        f"- Source observations: {len(observations)}",
        f"- Usable source observations: {len(usable_sources)}",
        f"- Fact packets built: {len(packets)}",
        f"- Publish-ready packets: {len(publish)}",
        f"- Manual review packets: {len(manual)}",
        f"- P1 / Must Post packets: {len(p1)}",
        f"- P2 / Strong Maybe packets: {len(p2)}",
        f"- Source fetch flags: {len(source_failures)}",
        "",
        "## Manual review rules",
        "",
        "- Hold if Results Desk marked the item for review.",
        "- Hold if Must Post has neither top-performer data nor a primary/official source.",
        "- Hold if no usable source context was captured.",
        "- Never invent player stats, rankings, quotes, injuries, or milestones.",
        "- Store facts, summaries, and links only. Do not copy full article text.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    run_id = stable_id(VERSION, utc_now())

    registry = load_json(SOURCE_REGISTRY_FILE, source_registry_defaults())
    angle_rules = load_json(ANGLE_RULES_FILE, angle_rules_defaults())

    queue_text = read_text(INPUT_RESULTS_QUEUE)
    recs_text = read_text(INPUT_RESULTS_RECS)
    box_text = read_text(INPUT_WNBA_BOX)

    candidates = parse_graphics_queue(queue_text, run_id)
    box_map = parse_box_score_summary(box_text)

    all_observations: List[Dict[str, Any]] = []
    observations_by_candidate: Dict[str, List[Dict[str, Any]]] = {}

    for candidate in candidates:
        obs = source_observations_for_candidate(candidate, registry, run_id)
        all_observations.extend(obs)
        observations_by_candidate[candidate["candidate_id"]] = obs

    packets = []
    for candidate in candidates:
        obs = observations_by_candidate.get(candidate["candidate_id"], [])
        packet = build_fact_packet(candidate, obs, box_map, angle_rules, run_id)
        packets.append(packet)

    manual_packets = [p for p in packets if p.get("manual_review") == "Yes"]

    write_csv(NEWS_CANDIDATES_CSV, candidates, CANDIDATE_FIELDS)
    write_csv(NEWS_SOURCE_OBS_CSV, all_observations, SOURCE_OBS_FIELDS)
    write_csv(NEWS_FACT_PACKETS_CSV, packets, PACKET_FIELDS)
    write_csv(NEWS_MANUAL_REVIEW_CSV, manual_packets, PACKET_FIELDS)

    Path(NEWS_BRIEF_QUEUE_MD).write_text(markdown_brief_queue(packets, observations_by_candidate), encoding="utf-8")
    Path(NEWS_SOCIAL_PACKETS_MD).write_text(markdown_social_packets(packets), encoding="utf-8")
    Path(NEWS_GRAPHICS_HANDOFF_MD).write_text(markdown_graphics_handoff(packets), encoding="utf-8")
    Path(NEWS_SYNC_HUB_MD).write_text(markdown_hub(run_id, candidates, all_observations, packets), encoding="utf-8")

    manifest = {
        "version": VERSION,
        "run_id": run_id,
        "generated_at_utc": utc_now(),
        "inputs": {
            "results_graphics_queue": INPUT_RESULTS_QUEUE,
            "daily_results_recommendations": INPUT_RESULTS_RECS,
            "wnba_box_score_summary": INPUT_WNBA_BOX,
            "results_system_hub": INPUT_RESULTS_HUB,
        },
        "outputs": [
            NEWS_CANDIDATES_CSV,
            NEWS_SOURCE_OBS_CSV,
            NEWS_FACT_PACKETS_CSV,
            NEWS_BRIEF_QUEUE_MD,
            NEWS_SOCIAL_PACKETS_MD,
            NEWS_GRAPHICS_HANDOFF_MD,
            NEWS_MANUAL_REVIEW_CSV,
            NEWS_SYNC_HUB_MD,
        ],
        "counts": {
            "candidates": len(candidates),
            "source_observations": len(all_observations),
            "fact_packets": len(packets),
            "manual_review": len(manual_packets),
            "publish_ready": len([p for p in packets if p.get("manual_review") != "Yes"]),
        },
        "settings": {
            "max_must_post": MAX_MUST_POST,
            "max_strong_maybe": MAX_STRONG_MAYBE,
            "enable_fetch": ENABLE_FETCH,
        }
    }
    Path(NEWS_MANIFEST_JSON).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Created Her Sports Daily News Sync v1 outputs")
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
