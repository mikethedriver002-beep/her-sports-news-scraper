"""
Her Sports Daily Story Context Enricher v4
------------------------------------------

Replaces generate_story_context.py.

What v4 adds:
- Missing-context search layer.
- If the direct article does not provide enough context, the script runs targeted
  Google News RSS searches for score, box score, record details, stats, purse,
  matchup, and official/secondary coverage.
- It uses supplemental search results as context candidates, but it does NOT
  blindly trust Google News aggregator copy.
- It records sources/queries used so every extracted fact has an audit trail.
- It still refuses to invent missing facts.

Output:
    story_context_enriched.csv
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


DAILY_BRIEF_FILE = "daily_content_brief.csv"
ARTICLES_FILE = "womens_sports_articles.csv"
OUTPUT_FILE = "story_context_enriched.csv"

MAX_SEARCH_RESULTS_PER_QUERY = 8
MAX_SUPPLEMENTAL_QUERIES = 5
REQUEST_SLEEP_SECONDS = 0.4


AGGREGATOR_BAD_PHRASES = [
    "comprehensive up-to-date news coverage",
    "aggregated from sources all over the world by google news",
    "google news",
    "full coverage",
    "view full coverage",
]

BOILERPLATE_PHRASES = [
    "appeared first on",
    "the post ",
    "all rights reserved",
    "privacy policy",
    "cookie policy",
    "sign up",
    "newsletter",
    "subscribe",
    "read more",
    "click here",
    "follow us",
    "advertisement",
    "related articles",
    "terms of service",
    "photo credit",
    "image credit",
    "copyright",
    "enable cookies",
    "track the latest",
    "javascript",
]

MEANINGFUL_VERBS = [
    "won", "wins", "win", "defeated", "defeats", "beat", "beats", "topped", "tops",
    "scored", "averaged", "recorded", "grabbed", "dished", "advanced", "clinched",
    "claims", "claimed", "captures", "captured", "announced", "signed", "committed",
    "landed", "sets", "set", "breaks", "broke", "shatters", "leads", "led", "earned",
    "extends", "opened", "begins", "begin", "finished", "posted",
]

STAT_TERMS = [
    "points", "rebounds", "assists", "steals", "blocks", "runs", "hits", "rbis",
    "strikeouts", "innings", "goals", "saves", "record", "milestone", "all-time",
    "rookie", "career", "franchise", "championship", "title", "purse", "viewership",
    "attendance", "rating", "ratings", "revenue", "investment", "media rights",
    "commissioner's cup", "commissioner’s cup", "box score", "final score",
]

OFFICIAL_SOURCE_TERMS = [
    "wnba", "nwslsoccer", "thepwhl", "ncaa.com", "lpga", "wta", "team usa",
    "u.s. soccer", "us soccer", "uswnt", "sec sports", "big ten", "acc",
]

STRONG_SOURCE_TERMS = [
    "associated press", "ap news", "apnews", "espn", "cbs sports", "yahoo sports",
    "reuters", "usa today", "sports illustrated", "the athletic", "just women's sports",
    "just womens sports", "swish appeal", "the next", "equalizer",
]

SPORT_MISMATCH_TERMS = {
    "WNBA": ["french open", "wimbledon", "roland garros", "nfl", "nba", "mlb", "nhl", "men's"],
    "Softball": ["french open", "nfl", "nba", "wnba record", "men's baseball"],
    "Golf / LPGA": ["wnba", "nfl", "nba", "men's"],
    "Tennis": ["wnba", "nfl", "nba", "mlb"],
}


def clean(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value).strip()
    return value


def low(value: str) -> str:
    return clean(value).lower()


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", low(value))[:140]


def safe_get(row: Dict[str, str], field: str) -> str:
    return clean(row.get(field, ""))


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_google_news_url(url: str) -> bool:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        return "news.google." in host or host == "news.google.com"
    except Exception:
        return False


def has_aggregator_garbage(text: str) -> bool:
    s = low(text)
    return any(phrase in s for phrase in AGGREGATOR_BAD_PHRASES)


def headline_terms(headline: str) -> set[str]:
    stop = {
        "with", "from", "that", "this", "into", "sports", "women", "news", "over",
        "after", "before", "begin", "begins", "first", "month", "latest", "2026",
        "ncaa", "wnba", "title", "wins", "win",
    }
    return {t for t in re.findall(r"[a-zA-Z0-9']{4,}", low(headline)) if t not in stop}


def source_quality(source: str) -> str:
    s = low(source)
    if any(term in s for term in OFFICIAL_SOURCE_TERMS):
        return "Official"
    if any(term in s for term in STRONG_SOURCE_TERMS):
        return "Strong"
    return "Other"


def source_weight(source: str) -> int:
    q = source_quality(source)
    if q == "Official":
        return 10
    if q == "Strong":
        return 8
    return 5


class ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_h1 = False
        self.in_p = False
        self.in_json = False
        self.current: List[str] = []
        self.current_json: List[str] = []
        self.title = ""
        self.h1 = ""
        self.meta_description = ""
        self.paragraphs: List[str] = []
        self.json_blocks: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        tag = tag.lower()
        attrs_dict = {k.lower(): v for k, v in attrs}

        if tag == "title":
            self.in_title = True
            self.current = []
        elif tag == "h1":
            self.in_h1 = True
            self.current = []
        elif tag == "p":
            self.in_p = True
            self.current = []
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if content and (name == "description" or prop in {"og:description", "twitter:description"}):
                if len(clean(content)) > len(self.meta_description):
                    self.meta_description = clean(content)
        elif tag == "script":
            if "ld+json" in attrs_dict.get("type", "").lower():
                self.in_json = True
                self.current_json = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        text = clean(" ".join(self.current))

        if tag == "title" and self.in_title:
            self.title = text
            self.in_title = False
            self.current = []
        elif tag == "h1" and self.in_h1:
            self.h1 = text
            self.in_h1 = False
            self.current = []
        elif tag == "p" and self.in_p:
            if 60 <= len(text) <= 700:
                self.paragraphs.append(text)
            self.in_p = False
            self.current = []
        elif tag == "script" and self.in_json:
            block = "".join(self.current_json).strip()
            if block:
                self.json_blocks.append(block)
            self.in_json = False
            self.current_json = []

    def handle_data(self, data: str) -> None:
        if self.in_title or self.in_h1 or self.in_p:
            self.current.append(data)
        if self.in_json:
            self.current_json.append(data)


def collect_json_article_text(obj: Any, strings: List[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"articleBody", "description", "headline"} and isinstance(v, str):
                text = clean(v)
                if len(text) >= 60:
                    strings.append(text)
            else:
                collect_json_article_text(v, strings)
    elif isinstance(obj, list):
        for item in obj:
            collect_json_article_text(item, strings)


def extract_json_text(blocks: Iterable[str]) -> List[str]:
    strings: List[str] = []
    for block in blocks:
        try:
            collect_json_article_text(json.loads(block), strings)
        except Exception:
            continue
    return strings


def fetch_article_text(url: str) -> Tuple[str, str]:
    if not url:
        return "", "No URL available."

    if is_google_news_url(url):
        return "", "Skipped Google News aggregator URL."

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailyBot/4.0; +https://github.com/)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            final_url = response.geturl()
            if is_google_news_url(final_url):
                return "", "Resolved URL is still Google News aggregator. Skipped."
            raw = response.read(1000000)
            encoding = response.headers.get_content_charset() or "utf-8"
            html_text = raw.decode(encoding, errors="replace")
    except Exception as exc:
        return "", f"Fetch failed: {exc}"

    parser = ArticleParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass

    pieces: List[str] = []
    if parser.h1:
        pieces.append(parser.h1)
    if parser.meta_description:
        pieces.append(parser.meta_description)
    pieces.extend(extract_json_text(parser.json_blocks)[:3])
    pieces.extend(parser.paragraphs[:14])

    article_text = clean(" ".join(pieces))
    if not article_text:
        return "", "Fetched page, but extracted no usable article text."

    if has_aggregator_garbage(article_text):
        return "", "Fetched text looked like aggregator/search-result content. Skipped."

    return article_text, "Fetched direct article text."


def google_news_rss(query: str) -> str:
    return (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )


def tidy_google_title(title: str, source: str) -> str:
    title = clean(title)
    source = clean(source)
    if source and title.endswith(f" - {source}"):
        return title[: -(len(source) + 3)].strip()
    return title


def parse_google_news_feed(query: str) -> List[Dict[str, str]]:
    url = google_news_rss(query)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(500000)
        root = ET.fromstring(raw)
    except Exception:
        return []

    results: List[Dict[str, str]] = []
    channel = root.find("channel")
    if channel is None:
        return results

    for item in channel.findall("item")[:MAX_SEARCH_RESULTS_PER_QUERY]:
        source = ""
        source_node = item.find("source")
        if source_node is not None and source_node.text:
            source = clean(source_node.text)
        title = tidy_google_title(item.findtext("title", default=""), source)
        description = clean(item.findtext("description", default=""))
        link = clean(item.findtext("link", default=""))
        text = clean(f"{title}. {description}")
        if text:
            results.append({
                "query": query,
                "title": title,
                "description": description,
                "source": source,
                "link": link,
                "text": text,
                "source_quality": source_quality(source),
            })

    return results


def build_queries(row: Dict[str, str]) -> List[str]:
    headline = safe_get(row, "headline")
    sport = safe_get(row, "sport")
    story_type = safe_get(row, "story_type")
    source = safe_get(row, "source")

    base = headline
    queries: List[str] = []

    if story_type == "Game Recap / Result":
        queries.extend([
            f'"{headline}" score',
            f'{headline} final score',
            f'{headline} box score',
        ])
        if sport == "Softball":
            queries.extend([
                f'{headline} opponent score softball',
                f'site:ncaa.com {headline} score',
            ])
        elif sport == "WNBA":
            queries.extend([
                f'{headline} WNBA box score',
                f'site:wnba.com {headline} box score',
            ])

    elif story_type == "Record / Milestone":
        queries.extend([
            f'"{headline}" record stats',
            f'{headline} exact record',
            f'{headline} milestone stats',
        ])
        if sport == "WNBA":
            queries.append(f'{headline} WNBA records stats')

    elif story_type in {"Business / Growth", "League Expansion"}:
        queries.extend([
            f'"{headline}"',
            f'{headline} amount number details',
            f'{headline} purse revenue viewership attendance investment',
        ])

    elif story_type == "Game Preview":
        queries.extend([
            f'"{headline}" time TV broadcast',
            f'{headline} matchup preview',
            f'{headline} key players',
        ])

    else:
        queries.extend([
            f'"{headline}"',
            f'{headline} details',
        ])

    # Add source-specific query if source is useful.
    if source and "google" not in low(source):
        queries.append(f'{headline} {source}')

    # Keep unique and capped.
    seen = set()
    unique: List[str] = []
    for q in queries:
        q = clean(q)
        if q and q.lower() not in seen:
            unique.append(q)
            seen.add(q.lower())
        if len(unique) >= MAX_SUPPLEMENTAL_QUERIES:
            break

    return unique


def split_sentences(text: str) -> List[str]:
    text = clean(text)
    text = re.sub(r"\s+\|\s+", ". ", text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9$])", text)
    return [clean(s) for s in sentences if 35 <= len(clean(s)) <= 420]


def looks_like_junk(sentence: str, sport: str, headline: str) -> bool:
    s = low(sentence)
    h = low(headline)

    if any(p in s for p in AGGREGATOR_BAD_PHRASES + BOILERPLATE_PHRASES):
        return True

    if sentence.count(",") >= 6 and not any(v in s for v in MEANINGFUL_VERBS):
        return True

    title_case_chunks = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,}", sentence)
    if len(title_case_chunks) >= 4 and len(sentence) > 180:
        return True

    for term in SPORT_MISMATCH_TERMS.get(sport, []):
        if term in s and term not in h:
            return True

    return False


def sentence_score(sentence: str, headline: str, story_type: str, sport: str, source: str = "") -> int:
    if looks_like_junk(sentence, sport, headline):
        return -100

    s = low(sentence)
    terms = headline_terms(headline)

    score = source_weight(source)
    score += 4 * sum(1 for t in terms if t in s)
    score += 5 * sum(1 for v in MEANINGFUL_VERBS if re.search(rf"\b{re.escape(v)}\b", s))
    score += 3 * sum(1 for t in STAT_TERMS if t in s)

    if re.search(r"\b\d{1,3}[-–]\d{1,3}\b", s):
        score += 12
    if re.search(r"\$\d", s):
        score += 12
    if re.search(r"\b\d+\s+(points|rebounds|assists|runs|hits|strikeouts|goals|saves)\b", s):
        score += 10

    if story_type == "Game Recap / Result" and any(x in s for x in ["won", "defeated", "beat", "championship", "title", "score"]):
        score += 10
    if story_type == "Record / Milestone" and any(x in s for x in ["record", "milestone", "all-time", "rookie", "franchise", "career"]):
        score += 10
    if story_type == "Business / Growth" and any(x in s for x in ["purse", "revenue", "viewership", "attendance", "investment", "media rights"]):
        score += 10

    return score


def best_sentences_from_text(text: str, headline: str, story_type: str, sport: str, max_items: int = 4) -> List[str]:
    scored = []
    for sentence in split_sentences(text):
        score = sentence_score(sentence, headline, story_type, sport)
        if score > 0:
            scored.append((score, sentence))
    scored.sort(key=lambda x: x[0], reverse=True)

    chosen: List[str] = []
    seen = set()
    for score, sentence in scored:
        k = key(sentence)
        if k in seen:
            continue
        chosen.append(sentence)
        seen.add(k)
        if len(chosen) >= max_items:
            break
    return chosen


def relevant_result(result: Dict[str, str], headline: str, sport: str) -> bool:
    text = result.get("text", "")
    s = low(text)
    terms = headline_terms(headline)

    if has_aggregator_garbage(text) or looks_like_junk(text, sport, headline):
        return False

    # Must share at least two meaningful terms, unless from official/strong source and shares one rare term.
    hits = sum(1 for t in terms if t in s)
    if hits >= 2:
        return True
    if hits >= 1 and source_quality(result.get("source", "")) in {"Official", "Strong"}:
        return True

    return False


def gather_supplemental_results(row: Dict[str, str]) -> Tuple[List[Dict[str, str]], List[str]]:
    queries = build_queries(row)
    all_results: List[Dict[str, str]] = []
    seen = set()

    for query in queries:
        results = parse_google_news_feed(query)
        time.sleep(REQUEST_SLEEP_SECONDS)
        for result in results:
            identity = key(result.get("title", "") + result.get("source", ""))
            if identity in seen:
                continue
            seen.add(identity)
            if relevant_result(result, safe_get(row, "headline"), safe_get(row, "sport")):
                all_results.append(result)

    return all_results, queries


def best_supplemental_sentences(results: List[Dict[str, str]], row: Dict[str, str], max_items: int = 4) -> List[Dict[str, str]]:
    headline = safe_get(row, "headline")
    story_type = safe_get(row, "story_type")
    sport = safe_get(row, "sport")

    scored: List[Tuple[int, Dict[str, str]]] = []
    for result in results:
        text = result.get("text", "")
        # Titles are often the best compact facts. Score the full title/description and sentence pieces.
        candidates = [clean(result.get("title", ""))]
        candidates.extend(split_sentences(text))
        for sentence in candidates:
            if not sentence:
                continue
            score = sentence_score(sentence, headline, story_type, sport, result.get("source", ""))
            if score > 0:
                scored.append((score, {
                    "sentence": sentence,
                    "source": result.get("source", ""),
                    "source_quality": result.get("source_quality", ""),
                    "query": result.get("query", ""),
                    "link": result.get("link", ""),
                }))

    scored.sort(key=lambda x: x[0], reverse=True)

    chosen: List[Dict[str, str]] = []
    seen = set()
    for score, item in scored:
        k = key(item["sentence"])
        if k in seen:
            continue
        item["score"] = str(score)
        chosen.append(item)
        seen.add(k)
        if len(chosen) >= max_items:
            break

    return chosen


def fact_from_headline(headline: str, story_type: str, sport: str) -> Dict[str, str]:
    h = clean(headline)
    h_low = low(h)
    out = {
        "summary": h,
        "fact_1": h,
        "fact_2": "",
        "final_score": "",
        "key_number": "",
        "main_takeaway": f"Headline-confirmed {sport} story. Verify specifics before adding exact stats.",
    }

    score_match = re.search(r"\b\d{1,3}[-–]\d{1,3}\b", h)
    points_match = re.search(r"\b([A-Z][A-Za-z'. -]+?)\s+scores\s+(\d+)\b", h)
    money_match = re.search(r"\$[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|m|b)?", h, flags=re.I)
    ordinal_record_match = re.search(r"\brecord\s+\d+(?:st|nd|rd|th)?\b", h, flags=re.I)

    if story_type == "Game Recap / Result":
        if score_match:
            out["final_score"] = score_match.group(0)
        if points_match:
            out["fact_2"] = f"{clean(points_match.group(1))} scored {points_match.group(2)}."
        if "championship" in h_low or "title" in h_low:
            out["main_takeaway"] = "Championship result is headline-confirmed. Verify opponent, score, and top performers before adding them."
        elif score_match:
            out["main_takeaway"] = "Result and score are headline-confirmed. Verify top performers before adding additional stat lines."

    elif story_type == "Record / Milestone":
        if ordinal_record_match:
            out["key_number"] = ordinal_record_match.group(0)
        out["main_takeaway"] = "Milestone is headline-confirmed. Verify exact record details before adding supporting stats."

    elif story_type in {"Business / Growth", "League Expansion"}:
        if money_match:
            out["key_number"] = money_match.group(0)
        out["main_takeaway"] = "Business/growth angle is headline-confirmed. Verify exact numbers from the source before designing."

    return out


def extract_final_score(facts: Iterable[str]) -> str:
    for fact in facts:
        m = re.search(r"\b\d{1,3}[-–]\d{1,3}\b", fact)
        if m:
            return m.group(0)
    return ""


def extract_key_number(facts: Iterable[str], story_type: str) -> str:
    for fact in facts:
        s = low(fact)

        if story_type == "Business / Growth":
            if any(t in s for t in ["purse", "revenue", "viewership", "attendance", "investment", "media rights", "sponsorship"]):
                m = re.search(r"\$[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|m|b)?|\b[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|percent|%)\b", fact, flags=re.I)
                if m:
                    return clean(m.group(0))

        if story_type == "Record / Milestone":
            if any(t in s for t in ["record", "milestone", "all-time", "rookie", "franchise", "career", "points", "assists", "steals"]):
                m = re.search(r"\brecord\s+\d+(?:st|nd|rd|th)?\b|\b\d+\s+(points|rebounds|assists|steals|blocks|goals|runs|hits|strikeouts)\b|\b\d+(?:st|nd|rd|th)?\b", fact, flags=re.I)
                if m:
                    return clean(m.group(0))

    return ""


def load_article_summary(brief_row: Dict[str, str], article_rows_by_key: Dict[str, Dict[str, str]]) -> str:
    headline = safe_get(brief_row, "headline")
    match = article_rows_by_key.get(key(headline), {})
    summary = safe_get(match, "summary")
    if summary and not has_aggregator_garbage(summary) and not any(p in low(summary) for p in BOILERPLATE_PHRASES):
        return summary
    return ""


def make_context(row: Dict[str, str], article_text: str, fallback_text: str, fetch_note: str, supplemental_items: List[Dict[str, str]], queries: List[str]) -> Dict[str, str]:
    headline = safe_get(row, "headline")
    story_type = safe_get(row, "story_type")
    sport = safe_get(row, "sport")

    direct_facts = best_sentences_from_text(article_text, headline, story_type, sport, 4) if article_text else []
    fallback_facts = best_sentences_from_text(fallback_text, headline, story_type, sport, 2) if fallback_text else []
    supplemental_facts = [item["sentence"] for item in supplemental_items]

    headline_fact = fact_from_headline(headline, story_type, sport)

    facts: List[str] = []
    for item in direct_facts + supplemental_facts + fallback_facts:
        if item and key(item) not in {key(x) for x in facts}:
            facts.append(item)

    if facts:
        summary = facts[0]
        fact_1 = facts[0]
        fact_2 = facts[1] if len(facts) > 1 else headline_fact["fact_2"]
        fact_3 = facts[2] if len(facts) > 2 else ""
        fact_4 = facts[3] if len(facts) > 3 else ""
    else:
        summary = headline_fact["summary"]
        fact_1 = headline_fact["fact_1"]
        fact_2 = headline_fact["fact_2"]
        fact_3 = ""
        fact_4 = ""

    all_fact_text = facts + [headline_fact["fact_1"], headline_fact["fact_2"]]
    final_score = extract_final_score(all_fact_text) or headline_fact["final_score"]
    key_number = extract_key_number(all_fact_text, story_type) or headline_fact["key_number"]

    # Determine context source and confidence.
    if direct_facts and supplemental_facts:
        source_status = "direct_article_plus_supplemental_search"
        confidence = "High"
        manual_review = "No"
    elif direct_facts and len(direct_facts) >= 2:
        source_status = "direct_article_text"
        confidence = "High"
        manual_review = "No"
    elif supplemental_facts:
        source_status = "supplemental_search"
        # Exact scores/numbers from supplemental search are useful, but still review unless source is official.
        has_official_supp = any(item.get("source_quality") == "Official" for item in supplemental_items)
        confidence = "High" if has_official_supp and (final_score or key_number or len(supplemental_facts) >= 2) else "Medium"
        manual_review = "No" if confidence == "High" else "Yes"
    elif fallback_facts:
        source_status = "fallback_summary"
        confidence = "Medium"
        manual_review = "Yes"
    else:
        source_status = "headline_only"
        confidence = "Medium" if fact_1 else "Low"
        manual_review = "Yes"

    main_takeaway = fact_2 or headline_fact["main_takeaway"]

    source_lines = []
    for item in supplemental_items[:5]:
        sentence = item.get("sentence", "")
        source = item.get("source", "")
        quality = item.get("source_quality", "")
        if sentence and source:
            source_lines.append(f"{source} ({quality}): {sentence}")

    notes = []
    notes.append(fetch_note)
    if queries:
        notes.append("Supplemental searches used: " + " | ".join(queries))
    if source_lines:
        notes.append("Supplemental source context: " + " || ".join(source_lines[:3]))
    if manual_review == "Yes":
        notes.append("Verify exact stats, scores, records, player details, and jersey numbers before final design.")

    return {
        "rank": safe_get(row, "rank"),
        "headline": headline,
        "sport": sport,
        "story_type": story_type,
        "source": safe_get(row, "source"),
        "link": safe_get(row, "link"),
        "context_confidence": confidence,
        "context_source_status": source_status,
        "verified_context_notes": " ".join(n for n in notes if n),
        "story_summary": summary,
        "key_fact_1": fact_1,
        "key_fact_2": fact_2,
        "key_fact_3": fact_3,
        "key_fact_4": fact_4,
        "winner": "",
        "loser": "",
        "final_score": final_score,
        "matchup": headline if story_type == "Game Preview" else "",
        "game_time": "",
        "tv_network": "",
        "key_player_1": "",
        "key_player_1_statline": "",
        "key_player_2": "",
        "key_player_2_statline": "",
        "watch_angle": main_takeaway if story_type == "Game Preview" else "",
        "round_or_event": "",
        "top_performer_1": "",
        "top_performer_1_statline": "",
        "top_performer_2": "",
        "top_performer_2_statline": "",
        "milestone_text": key_number or (summary if story_type == "Record / Milestone" else ""),
        "historical_context": main_takeaway if story_type == "Record / Milestone" else "",
        "key_number": key_number,
        "number_context": summary if key_number else "",
        "business_impact": main_takeaway if story_type in {"Business / Growth", "League Expansion"} else "",
        "main_takeaway": main_takeaway,
        "next_game_or_implication": "",
        "manual_review_flag": manual_review,
        "supplemental_search_queries": " | ".join(queries),
        "supplemental_source_count": str(len(supplemental_items)),
        "supplemental_sources": " || ".join(source_lines[:8]),
    }


def main() -> None:
    brief_rows = load_csv(DAILY_BRIEF_FILE)
    article_rows = load_csv(ARTICLES_FILE)
    article_rows_by_key = {key(r.get("title", "")): r for r in article_rows}

    output_rows: List[Dict[str, str]] = []

    for row in brief_rows:
        article_text, fetch_note = fetch_article_text(safe_get(row, "link"))
        fallback_text = load_article_summary(row, article_rows_by_key)

        # Always run supplemental search for Must Post/Maybe Post, or when direct facts are weak.
        supplemental_results, queries = gather_supplemental_results(row)
        supplemental_items = best_supplemental_sentences(supplemental_results, row, 5)

        output_rows.append(make_context(row, article_text, fallback_text, fetch_note, supplemental_items, queries))

    fieldnames = [
        "rank", "headline", "sport", "story_type", "source", "link",
        "context_confidence", "context_source_status", "verified_context_notes",
        "story_summary", "key_fact_1", "key_fact_2", "key_fact_3", "key_fact_4",
        "winner", "loser", "final_score", "matchup", "game_time", "tv_network",
        "key_player_1", "key_player_1_statline", "key_player_2", "key_player_2_statline",
        "watch_angle", "round_or_event", "top_performer_1", "top_performer_1_statline",
        "top_performer_2", "top_performer_2_statline", "milestone_text", "historical_context",
        "key_number", "number_context", "business_impact", "main_takeaway",
        "next_game_or_implication", "manual_review_flag", "supplemental_search_queries",
        "supplemental_source_count", "supplemental_sources",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    print(f"Created {OUTPUT_FILE} with {len(output_rows)} rows.")


if __name__ == "__main__":
    main()
