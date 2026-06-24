from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from hsd_run_io import input_path, output_path, read_csv, write_csv, write_text

try:
    import requests
except Exception:
    requests = None

try:
    import feedparser
except Exception:
    feedparser = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

VERSION = "hsd-discovery-ingest-v3.4.0-quality-freshness"

REGISTRY = "config/source_registry.json"
OUT_CSV = "story_candidates_discovery.csv"
OUT_JSONL = "story_candidates_discovery.jsonl"
OUT_REPORT = "discovery_sources_report.md"
SOCIAL_INBOX = "operator/inbox/social_rumor_inbox.csv"
FETCH_TIMEOUT = int(os.environ.get("HSD_DISCOVERY_FETCH_TIMEOUT", "15"))
MAX_PAGE_LEADS_PER_SOURCE = 10
ENABLE_FETCH = os.environ.get("HSD_DISCOVERY_ENABLE_FETCH", os.environ.get("HSD_NEWS_ENABLE_FETCH", "true")).lower() != "false"

FIELDS = [
    "story_id", "source_id", "source_type", "source_tier", "source_trust_band", "title", "source_url",
    "canonical_url", "published_at", "summary", "risk_tier", "publish_eligible", "reason",
    "lead_source", "lead_score", "freshness_date", "freshness_label", "freshness_score",
    "urgency_score", "quality_score", "quality_reason", "promotion_hint", "review_next_step",
]

GREEN_TIERS = {"official", "operator", "wire", "primary_media", "stats_provider"}
YELLOW_TIERS = {"social", "social_manual", "community", "discovery", "media_review"}
RED_TIERS = {"red", "prohibited"}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def norm(v: Any) -> str:
    return clean(v).lower()


def canonicalize(url: str) -> str:
    try:
        s = urlsplit(clean(url))
        query = [(k, v) for k, v in parse_qsl(s.query) if not k.startswith("utm_") and k not in {"fbclid", "gclid"}]
        return urlunsplit((s.scheme.lower(), s.netloc.lower(), s.path.rstrip("/") or "/", urlencode(query), ""))
    except Exception:
        return clean(url)


def story_id(url: str, title: str) -> str:
    return "disc_" + hashlib.sha1((canonicalize(url) or clean(title)).encode()).hexdigest()[:14]


def now_utc() -> datetime:
    raw = clean(os.environ.get("HSD_DISCOVERY_NOW_UTC"))
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def parse_date_hint(*values: Any) -> datetime | None:
    for value in values:
        text = clean(value)
        if not text:
            continue
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            pass
        patterns = [
            r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b",
            r"/(20\d{2})/(\d{1,2})/(\d{1,2})(?:/|-)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def load_registry() -> Dict[str, Any]:
    path = input_path(REGISTRY)
    if not path.exists():
        return {"sources": []}
    return json.loads(path.read_text(encoding="utf-8"))


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


STORY_TERMS = {
    "announce", "announces", "announced", "sign", "signs", "signed", "trade", "trades", "traded",
    "waive", "waives", "waived", "injury", "injured", "roster", "award", "record", "expansion",
    "coach", "hired", "named", "launch", "partnership", "preview", "beat", "beats", "defeat",
    "defeats", "win", "wins", "won", "final", "score", "result", "title", "championship",
    "semifinal", "quarterfinal", "ranking", "rankings", "draw", "returns", "retires", "commits",
}

VISUAL_TERMS = {
    "beat", "beats", "defeat", "defeats", "win", "wins", "won", "final", "score", "result",
    "preview", "highlight", "title", "championship", "record", "top", "ranking", "draw",
}

GENERIC_LINK_TERMS = {
    "home", "tickets", "schedule", "standings", "stats", "roster", "shop", "watch", "video",
    "photos", "newsletter", "privacy", "terms", "contact", "app", "login", "sign in", "scores",
    "teams", "players", "more", "menu", "subscribe", "buy tickets",
    "coaches", "rowing",
}

LOW_VALUE_PATH_PARTS = {
    "/news/category/",
    "/news/doubles",
    "/news/coaches",
    "/news/previews",
    "/news/hot-shots",
    "/news/player-feature",
    "/news/social-buzz",
    "/sports/rowing",
    "/sports/tennis-men",
    "/sports/tennis-women",
    "/sports/trackfield-outdoor-men",
    "/sports/trackfield-outdoor-women",
    "/sports/swimming-women",
}

BETTING_TERMS = {"odds", "sportsbook", "draftkings", "betting", "wager"}
URGENT_TERMS = {
    "announce", "announces", "announced", "breaking", "sign", "signs", "signed", "trade",
    "trades", "traded", "injury", "injured", "roster", "expansion", "named", "hired",
    "returns", "retires", "fined", "waive", "waives", "waived", "final", "score", "beat",
    "beats", "defeat", "defeats", "wins", "won",
}
EVERGREEN_TERMS = {
    "all-time", "history", "historic", "best places", "most outstanding", "single-season",
    "power rankings", "rankings", "things i like", "near", "nears", "watch guide",
}


def row_policy(src: Dict[str, Any], band: str) -> Dict[str, str]:
    if band == "green":
        return {
            "risk_tier": "green_official_or_primary",
            "publish_eligible": "Yes",
            "reason": "green registered free-source lead; editor review required",
            "review_next_step": "Open the free source URL, verify the exact fact, then decide whether to promote into News or Studio.",
        }
    if band == "red":
        return {
            "risk_tier": "red_prohibited",
            "publish_eligible": "No",
            "reason": "red/prohibited source policy",
            "review_next_step": "Do not promote this lead.",
        }
    return {
        "risk_tier": "yellow_discovery_only",
        "publish_eligible": "No",
        "reason": "discovery only; needs official, wire, primary, or operator-verified confirmation",
        "review_next_step": "Use as a lead only; add confirmation before any factual claim is used.",
    }


def promotion_hint(title: str, summary: str = "") -> str:
    text = norm(f"{title} {summary}")
    if any(term in text for term in VISUAL_TERMS):
        return "studio_brief"
    if any(term in text for term in STORY_TERMS):
        return "news_packet"
    return "manual_story_candidate"


def normalized_link_title(title: str) -> str:
    text = clean(re.sub(r"\bRead More\b", " ", clean(title), flags=re.I))
    words = text.split()
    if len(words) >= 4 and len(words) % 2 == 0:
        half = len(words) // 2
        if [word.lower() for word in words[:half]] == [word.lower() for word in words[half:]]:
            text = " ".join(words[:half])
    return clean(text)


def low_value_link(title: str, url: str, src: Dict[str, Any]) -> bool:
    low_title = norm(title)
    low_url = norm(url)
    if not low_title:
        return True
    if low_title.startswith("view all"):
        return True
    if low_title in GENERIC_LINK_TERMS:
        return True
    if any(part in low_url for part in LOW_VALUE_PATH_PARTS):
        return True
    if any(term in low_title or term in low_url for term in BETTING_TERMS):
        return True
    if re.fullmatch(r"all [a-z ]+ news", low_title):
        return True
    if ("men" in low_title or "-men" in low_url or "/men" in low_url) and not any(token in low_title or token in low_url for token in ["women", "womens", "women's", "wnba", "wta"]):
        return True
    source_id = norm(src.get("source_id"))
    if "softball" in source_id and not any(token in low_title or token in low_url for token in ["softball", "wcws", "college-world-series"]):
        return True
    return False


def lead_score(title: str, url: str, summary: str = "") -> int:
    title = normalized_link_title(title)
    if low_value_link(title, url, {}):
        return 0
    text = norm(f"{title} {url} {summary}")
    title_text = norm(title)
    if not title_text or title_text in GENERIC_LINK_TERMS:
        return 0
    score = 0
    score += min(5, sum(1 for term in STORY_TERMS if term in text))
    if any(part in norm(url) for part in ["/news/", "/story/", "/article/", "/press-release/", "/sports/"]):
        score += 2
    if len(title_text.split()) >= 5:
        score += 1
    if any(term in title_text for term in GENERIC_LINK_TERMS) and len(title_text.split()) <= 3:
        score -= 3
    return max(score, 0)


def urgency_score(title: str, summary: str = "") -> int:
    text = norm(f"{title} {summary}")
    score = min(20, sum(1 for term in URGENT_TERMS if term in text) * 4)
    if any(term in text for term in ["today", "tonight", "this week", "week 6", "all-star"]):
        score += 4
    return min(score, 24)


def is_evergreen(title: str, summary: str = "", url: str = "") -> bool:
    text = norm(f"{title} {summary} {url}")
    return any(term in text for term in EVERGREEN_TERMS)


def freshness_payload(title: str, url: str, published_at: str, summary: str = "") -> Dict[str, str]:
    now = now_utc()
    date_hint = parse_date_hint(published_at, url, title)
    evergreen = is_evergreen(title, summary, url)
    if date_hint:
        days = (now.date() - date_hint.date()).days
        if days < 0:
            label, score = "future_dated", 18
        elif days == 0:
            label, score = "today", 36
        elif days <= 2:
            label, score = "last_48_hours", 32
        elif days <= 7:
            label, score = "this_week", 26
        elif days <= 30:
            label, score = "recent_30_days", 14
        else:
            label, score = "stale_over_30_days", 3
        if evergreen:
            label = f"{label}_evergreen_angle"
            score = max(3, score - 10)
        return {
            "freshness_date": date_hint.date().isoformat(),
            "freshness_label": label,
            "freshness_score": str(score),
        }
    if evergreen:
        return {"freshness_date": "", "freshness_label": "evergreen_undated", "freshness_score": "6"}
    if str(now.year) in f"{title} {url}":
        return {"freshness_date": "", "freshness_label": "current_year_undated", "freshness_score": "16"}
    return {"freshness_date": "", "freshness_label": "undated", "freshness_score": "10"}


def quality_payload(src: Dict[str, Any], title: str, url: str, summary: str, lead_score_value: int, published_at: str) -> Dict[str, str]:
    freshness = freshness_payload(title, url, published_at, summary)
    urgent = urgency_score(title, summary)
    source_bonus = 16 if trust_band(src) == "green" else 7
    evergreen_penalty = 12 if is_evergreen(title, summary, url) else 0
    score = min(
        100,
        max(
            0,
            (lead_score_value * 6)
            + int(freshness["freshness_score"])
            + urgent
            + source_bonus
            - evergreen_penalty,
        ),
    )
    reason = (
        f"lead={lead_score_value}; freshness={freshness['freshness_label']}:{freshness['freshness_score']}; "
        f"urgency={urgent}; source={trust_band(src)}; evergreen_penalty={evergreen_penalty}"
    )
    return {
        **freshness,
        "urgency_score": str(urgent),
        "quality_score": str(score),
        "quality_reason": reason,
    }


def candidate_row(src: Dict[str, Any], row: Dict[str, str], *, lead_source: str, band: str) -> Dict[str, str]:
    policy = row_policy(src, band)
    title = normalized_link_title(row.get("title", ""))
    summary = clean(row.get("summary"))
    source_url = clean(row.get("source_url"))
    score = clean(row.get("lead_score")) or str(lead_score(title, source_url, summary))
    published_at = clean(row.get("published_at"))
    quality = quality_payload(src, title, source_url, summary, int(score or 0), published_at)
    return {
        "story_id": story_id(row.get("canonical_url", ""), title),
        "source_id": clean(src.get("source_id", "")),
        "source_type": clean(src.get("source_type", "")),
        "source_tier": clean(src.get("tier", "")),
        "source_trust_band": band,
        "title": title,
        "source_url": source_url,
        "canonical_url": clean(row.get("canonical_url")) or canonicalize(source_url),
        "published_at": published_at,
        "summary": summary,
        "risk_tier": policy["risk_tier"],
        "publish_eligible": policy["publish_eligible"],
        "reason": clean(row.get("reason")) or policy["reason"],
        "lead_source": lead_source,
        "lead_score": score,
        **quality,
        "promotion_hint": clean(row.get("promotion_hint")) or promotion_hint(title, summary),
        "review_next_step": clean(row.get("review_next_step")) or policy["review_next_step"],
    }


def same_registered_domain(url: str, src: Dict[str, Any]) -> bool:
    domains = [clean(d).lower().removeprefix("www.") for d in src.get("domains", []) if clean(d)]
    if not domains:
        return True
    host = urlsplit(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in domains)


def feed_entries(src: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for url in src.get("urls", []):
        try:
            if feedparser is not None:
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
            elif requests is not None and ENABLE_FETCH:
                response = requests.get(url, headers={"User-Agent": "HSDDiscovery/3.3 FreeSource"}, timeout=FETCH_TIMEOUT)
                if response.status_code >= 400:
                    continue
                root = ElementTree.fromstring(response.text.encode("utf-8"))
                for item in root.findall(".//item")[:50]:
                    title = clean(item.findtext("title"))
                    link = clean(item.findtext("link"))
                    summary = clean(item.findtext("description"))
                    published = clean(item.findtext("pubDate"))
                    rows.append({
                        "title": title,
                        "source_url": link,
                        "canonical_url": canonicalize(link),
                        "published_at": published,
                        "summary": summary,
                    })
        except Exception:
            continue
    return rows


def links_from_html(url: str, text: str, src: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if BeautifulSoup is not None:
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup.find_all("a", href=True):
            title = normalized_link_title(tag.get_text(" "))
            href = urljoin(url, clean(tag.get("href")))
            if not same_registered_domain(href, src):
                continue
            if low_value_link(title, href, src):
                continue
            score = lead_score(title, href)
            if score < 3:
                continue
            rows.append({
                "title": title,
                "source_url": href,
                "canonical_url": canonicalize(href),
                "published_at": "",
                "summary": f"Free public source link captured from {clean(src.get('source_id'))}.",
                "lead_score": str(score),
            })
    else:
        for href, label in re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, flags=re.I | re.S):
            title = normalized_link_title(re.sub(r"<[^>]+>", " ", html.unescape(label)))
            link = urljoin(url, clean(href))
            if not same_registered_domain(link, src):
                continue
            if low_value_link(title, link, src):
                continue
            score = lead_score(title, link)
            if score < 3:
                continue
            rows.append({
                "title": title,
                "source_url": link,
                "canonical_url": canonicalize(link),
                "published_at": "",
                "summary": f"Free public source link captured from {clean(src.get('source_id'))}.",
                "lead_score": str(score),
            })
    return rows


def public_page_leads(src: Dict[str, Any]) -> List[Dict[str, str]]:
    if requests is None or not ENABLE_FETCH:
        return []
    rows: List[Dict[str, str]] = []
    for url in src.get("urls", [])[:4]:
        try:
            response = requests.get(url, headers={"User-Agent": "HSDDiscovery/3.3 FreeSource"}, timeout=FETCH_TIMEOUT)
            if response.status_code >= 400:
                continue
            rows.extend(links_from_html(url, response.text, src))
        except Exception:
            continue
    rows = sorted(rows, key=lambda row: (-int(row.get("lead_score") or 0), row.get("title", "")))
    return rows[:MAX_PAGE_LEADS_PER_SOURCE]


def reddit_public_json(src: Dict[str, Any]) -> List[Dict[str, str]]:
    if requests is None or not ENABLE_FETCH:
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


def social_manual_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    pseudo_source = {
        "source_id": "social_rumor_manual_inbox",
        "source_type": "social_manual",
        "tier": "social_manual",
    }
    for row in read_csv(SOCIAL_INBOX):
        title = clean(row.get("claim_text") or row.get("title") or row.get("source_url"))
        source_url = clean(row.get("source_url"))
        if not title and not source_url:
            continue
        rows.append(
            candidate_row(
                pseudo_source,
                {
                    "title": title,
                    "source_url": source_url,
                    "canonical_url": canonicalize(source_url),
                    "published_at": clean(row.get("published_at")),
                    "summary": clean(" / ".join(part for part in [
                        row.get("platform", ""),
                        row.get("source_handle", ""),
                        row.get("teams_people", ""),
                        row.get("operator_notes", ""),
                    ] if clean(part))),
                    "reason": "manual social lead; requires official, wire, primary, or operator-verified confirmation",
                    "promotion_hint": "manual_story_candidate",
                    "review_next_step": "Use the social URL as a tip only; find official, wire, primary, or operator-verified confirmation.",
                },
                lead_source="manual_social_inbox",
                band="yellow",
            )
        )
    return rows


def main() -> None:
    registry = load_registry()
    candidates: List[Dict[str, str]] = []
    counts_by_lead_source: Dict[str, int] = {}
    skipped_enabled_unknown = 0
    skipped_uncrawled_policy = 0

    for src in registry.get("sources", []):
        if not src.get("enabled"):
            continue
        stype = clean(src.get("source_type"))
        band = trust_band(src)
        rows: List[Dict[str, str]] = []
        lead_source = ""
        if stype == "rss":
            rows = feed_entries(src)
            lead_source = "rss_feed"
        elif stype == "reddit_public_json":
            rows = reddit_public_json(src)
            lead_source = "reddit_public_json"
        elif stype in {"official_site", "wire"}:
            rows = public_page_leads(src)
            lead_source = "free_public_page"
        elif stype in {"official_site_collection", "scoreboard_site", "manual", "social_manual_only", "prohibited"}:
            # These are registered for policy/cross-check/manual use. Manual/social inbox rows are read explicitly below.
            skipped_uncrawled_policy += 1
            continue
        else:
            skipped_enabled_unknown += 1
            continue

        for r in rows:
            candidate = candidate_row(src, r, lead_source=lead_source, band=band)
            if not candidate["title"] and not candidate["source_url"]:
                continue
            candidates.append(candidate)
            counts_by_lead_source[lead_source] = counts_by_lead_source.get(lead_source, 0) + 1

    for candidate in social_manual_rows():
        candidates.append(candidate)
        counts_by_lead_source[candidate["lead_source"]] = counts_by_lead_source.get(candidate["lead_source"], 0) + 1

    by_id = {r["story_id"]: r for r in candidates}
    candidates = sorted(
        by_id.values(),
        key=lambda row: (
            -int(row.get("quality_score") or 0),
            -int(row.get("freshness_score") or 0),
            -int(row.get("lead_score") or 0),
            row.get("publish_eligible") != "Yes",
            row.get("title", ""),
        ),
    )

    write_csv(OUT_CSV, candidates, FIELDS)
    write_text(OUT_JSONL, "\n".join(json.dumps(r, ensure_ascii=False) for r in candidates) + ("\n" if candidates else ""))

    lines = [
        "# HSD Discovery Sources Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Version: {VERSION}",
        f"- candidates: {len(candidates)}",
        f"- publish eligible: {sum(1 for r in candidates if r['publish_eligible'] == 'Yes')}",
        f"- discovery only: {sum(1 for r in candidates if r['publish_eligible'] != 'Yes')}",
        f"- today / last 48 hours: {sum(1 for r in candidates if r['freshness_label'] in {'today', 'last_48_hours'})}",
        f"- stale or evergreen: {sum(1 for r in candidates if 'stale' in r['freshness_label'] or 'evergreen' in r['freshness_label'])}",
        f"- RSS/feed leads: {counts_by_lead_source.get('rss_feed', 0)}",
        f"- Free public page leads: {counts_by_lead_source.get('free_public_page', 0)}",
        f"- Reddit public JSON leads: {counts_by_lead_source.get('reddit_public_json', 0)}",
        f"- Manual social leads: {counts_by_lead_source.get('manual_social_inbox', 0)}",
        f"- enabled source types skipped by review-safe policy: {skipped_uncrawled_policy}",
        f"- enabled unknown source types skipped: {skipped_enabled_unknown}",
        "",
        "Official and wire pages are sampled only for free public story links. Social rows come from manual inbox files only; no login, credentialed scraping, paid APIs, auto-publishing, or automatic promotion is used.",
        "",
        "## Top Leads",
        "",
    ]
    for row in candidates[:25]:
        lines.append(
            f"- `{row['quality_score']}` quality | `{row['freshness_label']}` | `{row['promotion_hint']}` | "
            f"`{row['source_trust_band']}` | {row['title']} | {row['review_next_step']}"
        )
    if not candidates:
        lines.append("No discovery candidates found.")
    write_text(OUT_REPORT, "\n".join(lines) + "\n")
    print(json.dumps({
        "version": VERSION,
        "output_scope": "run_scoped" if output_path(OUT_CSV) != Path(OUT_CSV) else "legacy_root",
        "discovery_candidates": len(candidates),
        "free_public_page_leads": counts_by_lead_source.get("free_public_page", 0),
        "manual_social_leads": counts_by_lead_source.get("manual_social_inbox", 0),
        "fresh_today_or_48h": sum(1 for r in candidates if r["freshness_label"] in {"today", "last_48_hours"}),
        "stale_or_evergreen": sum(1 for r in candidates if "stale" in r["freshness_label"] or "evergreen" in r["freshness_label"]),
        "skipped_enabled_unknown": skipped_enabled_unknown,
    }, indent=2))


if __name__ == "__main__":
    main()
