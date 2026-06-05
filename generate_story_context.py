"""
Her Sports Daily Story Context Enricher - CLEAN CONTEXT VERSION
---------------------------------------------------------------

Replaces the older generate_story_context.py.

Reads:
    daily_content_brief.csv
    womens_sports_articles.csv, if available

Creates:
    story_context_enriched.csv

Core rule:
    Do not turn boilerplate, category tags, or random numbers into "facts."

This version is deliberately conservative:
- Better HTML/article extraction using meta, JSON-LD, and paragraphs
- Filters boilerplate like "appeared first on", categories, newsletters, cookies, etc.
- Does not extract random "8 points" as a key number unless it is in a meaningful context
- Downgrades confidence when real article details cannot be safely extracted
- Leaves fields blank or flags manual review instead of inventing stats
"""

from __future__ import annotations

import csv
import html
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


DAILY_BRIEF_FILE = "daily_content_brief.csv"
ARTICLES_FILE = "womens_sports_articles.csv"
OUTPUT_FILE = "story_context_enriched.csv"


BOILERPLATE_PATTERNS = [
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
    "posted in",
    "filed under",
    "share this",
    "comments",
    "terms of service",
    "photo credit",
    "image credit",
    "copyright",
    "javascript",
    "enable cookies",
    "track the latest",
]

CATEGORY_HEAVY_WORDS = [
    "basketball, news",
    "soccer, news",
    "softball, news",
    "tennis, news",
    "wnba,",
    "ncaa,",
]


MEANINGFUL_VERBS = [
    "won", "wins", "win", "defeated", "defeats", "beat", "beats", "topped", "tops",
    "scored", "averaged", "recorded", "grabbed", "dished", "struck", "advanced",
    "clinched", "claims", "claimed", "captures", "captured", "announced", "signed",
    "committed", "landed", "sets", "set", "breaks", "broke", "shatters", "leads", "led",
    "finished", "opened", "closed", "earned",
]


STAT_CONTEXT_TERMS = [
    "points", "rebounds", "assists", "steals", "blocks", "runs", "hits", "rbis",
    "strikeouts", "innings", "goals", "saves", "record", "milestone", "all-time",
    "rookie", "career", "franchise", "championship", "title", "purse", "viewership",
    "attendance", "rating", "ratings", "revenue", "investment", "media rights",
]


def clean(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value).strip()
    return value


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())[:140]


def lower(value: str) -> str:
    return clean(value).lower()


def safe_get(row: Dict[str, str], field: str) -> str:
    return clean(row.get(field, ""))


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class BetterArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_h1 = False
        self.in_p = False
        self.current: List[str] = []
        self.title = ""
        self.h1 = ""
        self.meta_description = ""
        self.paragraphs: List[str] = []
        self.json_ld_blocks: List[str] = []
        self.in_json_ld = False
        self.current_script: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        attrs_dict = {k.lower(): v for k, v in attrs}
        tag = tag.lower()

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
            if content and (name == "description" or prop == "og:description" or prop == "twitter:description"):
                if not self.meta_description or len(content) > len(self.meta_description):
                    self.meta_description = clean(content)
        elif tag == "script":
            script_type = attrs_dict.get("type", "").lower()
            if "ld+json" in script_type or attrs_dict.get("id", "") == "__NEXT_DATA__":
                self.in_json_ld = True
                self.current_script = []

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
            if len(text) >= 60:
                self.paragraphs.append(text)
            self.in_p = False
            self.current = []
        elif tag == "script" and self.in_json_ld:
            block = "".join(self.current_script).strip()
            if block:
                self.json_ld_blocks.append(block)
            self.in_json_ld = False
            self.current_script = []

    def handle_data(self, data: str) -> None:
        if self.in_title or self.in_h1 or self.in_p:
            self.current.append(data)
        if self.in_json_ld:
            self.current_script.append(data)


def collect_json_strings(obj: Any, strings: List[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in {"articleBody", "description", "headline", "name", "text"} and isinstance(v, str):
                if len(clean(v)) >= 50:
                    strings.append(clean(v))
            else:
                collect_json_strings(v, strings)
    elif isinstance(obj, list):
        for item in obj:
            collect_json_strings(item, strings)
    elif isinstance(obj, str):
        # Only collect long strings that look article-ish.
        if len(clean(obj)) >= 150 and any(term in lower(obj) for term in STAT_CONTEXT_TERMS + MEANINGFUL_VERBS):
            strings.append(clean(obj))


def extract_json_text(blocks: Iterable[str]) -> List[str]:
    strings: List[str] = []
    for block in blocks:
        try:
            data = json.loads(block)
            collect_json_strings(data, strings)
        except Exception:
            continue
    return strings


def fetch_article_text(url: str) -> Tuple[str, str]:
    if not url:
        return "", "No URL available."

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailyBot/2.0; +https://github.com/)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(1000000)
            encoding = response.headers.get_content_charset() or "utf-8"
            html_text = raw.decode(encoding, errors="replace")
    except Exception as exc:
        return "", f"Fetch failed: {exc}"

    parser = BetterArticleParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass

    json_text = extract_json_text(parser.json_ld_blocks)

    pieces: List[str] = []
    if parser.h1:
        pieces.append(parser.h1)
    if parser.meta_description:
        pieces.append(parser.meta_description)
    pieces.extend(json_text[:4])
    pieces.extend(parser.paragraphs[:18])

    article_text = clean(" ".join(pieces))
    if not article_text:
        return "", "Fetched page, but no usable article text was extracted."

    return article_text, "Fetched article text."


def sentence_split(text: str) -> List[str]:
    text = clean(text)
    # Also split on long category-like separators.
    text = re.sub(r"\s+\|\s+", ". ", text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9$])", text)
    return [clean(s) for s in sentences if len(clean(s)) >= 45]


def is_boilerplate_sentence(sentence: str) -> bool:
    s = lower(sentence)

    if any(p in s for p in BOILERPLATE_PATTERNS):
        return True
    if any(p in s for p in CATEGORY_HEAVY_WORDS) and not any(v in s for v in MEANINGFUL_VERBS):
        return True

    # Category/tag lists often have many commas but no verbs.
    comma_count = sentence.count(",")
    if comma_count >= 5 and not any(re.search(rf"\b{re.escape(v)}\b", s) for v in MEANINGFUL_VERBS):
        return True

    # Very short promotional meta copy.
    if "news" in s and "wnba" in s and "stats" in s and "track" in s:
        return True

    return False


def has_meaningful_signal(sentence: str, headline_terms: Iterable[str], story_type: str) -> bool:
    s = lower(sentence)
    if is_boilerplate_sentence(sentence):
        return False

    headline_hits = sum(1 for term in headline_terms if term and term in s)
    verb_hit = any(re.search(rf"\b{re.escape(v)}\b", s) for v in MEANINGFUL_VERBS)
    stat_hit = any(term in s for term in STAT_CONTEXT_TERMS)
    number_hit = re.search(r"\$?\b\d+(?:\.\d+)?(?:[-–]\d+)?\b", s) is not None

    if headline_hits >= 2 and (verb_hit or stat_hit or number_hit):
        return True
    if verb_hit and stat_hit:
        return True
    if story_type in {"Business / Growth", "League Expansion"} and any(term in s for term in ["purse", "revenue", "media rights", "investment", "attendance", "viewership", "expansion"]):
        return True
    if story_type == "Record / Milestone" and any(term in s for term in ["record", "milestone", "all-time", "first", "career", "rookie"]):
        return True
    if story_type == "Game Recap / Result" and any(term in s for term in ["won", "defeated", "beat", "championship", "title", "score"]):
        return True

    return False


def score_sentence(sentence: str, headline_terms: Iterable[str], story_type: str) -> int:
    s = lower(sentence)
    if is_boilerplate_sentence(sentence):
        return -100

    score = 0
    score += 2 * sum(1 for term in headline_terms if term and term in s)
    score += 3 * sum(1 for term in STAT_CONTEXT_TERMS if term in s)
    score += 3 * sum(1 for verb in MEANINGFUL_VERBS if re.search(rf"\b{re.escape(verb)}\b", s))

    if re.search(r"\b\d{1,3}[-–]\d{1,3}\b", s):
        score += 8
    if re.search(r"\$\d", s):
        score += 8
    if re.search(r"\b\d+\s+(points|rebounds|assists|runs|hits|strikeouts|goals|saves)\b", s):
        score += 5

    if story_type == "Record / Milestone" and any(t in s for t in ["record", "all-time", "milestone", "first", "rookie"]):
        score += 8
    if story_type == "Game Recap / Result" and any(t in s for t in ["championship", "title", "won", "defeated", "beat"]):
        score += 8
    if story_type == "Business / Growth" and any(t in s for t in ["purse", "revenue", "viewership", "attendance", "media rights"]):
        score += 8

    return score


def best_sentences(text: str, headline: str, story_type: str, max_items: int = 4) -> List[str]:
    terms = set(re.findall(r"[a-zA-Z0-9']{4,}", lower(headline)))
    terms = {t for t in terms if t not in {"with", "from", "that", "this", "into", "sports", "women", "news"}}

    candidates = []
    for s in sentence_split(text):
        if not has_meaningful_signal(s, terms, story_type):
            continue
        candidates.append((score_sentence(s, terms, story_type), s))

    candidates.sort(key=lambda x: x[0], reverse=True)

    chosen: List[str] = []
    seen = set()
    for score, sentence in candidates:
        if score <= 0:
            continue
        k = key(sentence)
        if k in seen:
            continue
        chosen.append(sentence)
        seen.add(k)
        if len(chosen) >= max_items:
            break

    return chosen


def load_article_summary(brief_row: Dict[str, str], article_rows_by_key: Dict[str, Dict[str, str]]) -> str:
    headline = safe_get(brief_row, "headline")
    match = article_rows_by_key.get(key(headline), {})
    parts = [
        safe_get(match, "summary"),
        safe_get(brief_row, "why_it_matters"),
        safe_get(brief_row, "instagram_angle"),
        safe_get(brief_row, "decision_reason"),
    ]
    return clean(" ".join(p for p in parts if p and not is_boilerplate_sentence(p)))


def extract_final_score(sentences: Iterable[str]) -> str:
    for sentence in sentences:
        m = re.search(r"\b\d{1,3}[-–]\d{1,3}\b", sentence)
        if m and any(t in lower(sentence) for t in ["defeated", "beat", "won", "win", "score", "championship", "title"]):
            return clean(m.group(0))
    return ""


def extract_key_number(sentences: Iterable[str], story_type: str) -> str:
    for sentence in sentences:
        s = lower(sentence)

        if story_type == "Business / Growth":
            patterns = [
                r"\$[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|m|b)?",
                r"\b[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|percent|%)\b",
            ]
            if any(term in s for term in ["purse", "revenue", "viewership", "attendance", "investment", "media rights", "sponsorship"]):
                for p in patterns:
                    m = re.search(p, sentence, flags=re.I)
                    if m:
                        return clean(m.group(0))

        if story_type == "Record / Milestone":
            if any(term in s for term in ["record", "milestone", "all-time", "first", "career", "rookie", "franchise"]):
                patterns = [
                    r"\b\d+(?:st|nd|rd|th)?\s+(?:career|straight|consecutive|record|points|rebounds|assists|goals|saves|runs|hits|strikeouts)\b",
                    r"\brecord[- ]breaking\s+[^.]{0,60}",
                    r"\b\d+\b",
                ]
                for p in patterns:
                    m = re.search(p, sentence, flags=re.I)
                    if m:
                        return clean(m.group(0))

    return ""


def generic_summary_from_headline(row: Dict[str, str]) -> str:
    headline = safe_get(row, "headline")
    story_type = safe_get(row, "story_type")
    sport = safe_get(row, "sport")

    if story_type == "Record / Milestone":
        return f"Reported {sport} milestone story. Exact record details need verification from the source before graphic production."
    if story_type == "Game Recap / Result":
        return f"Reported {sport} result story. Final score, opponent, and top performers need verification from the source before graphic production."
    if story_type == "Business / Growth":
        return f"Reported {sport} business/growth story. Key number and business context need verification from the source before graphic production."
    if story_type == "Game Preview":
        return f"Reported {sport} preview story. Matchup, time, broadcast, and player notes need verification from the source before graphic production."
    return f"Reported {sport} story: {headline}"


def make_context(row: Dict[str, str], article_text: str, fallback_text: str, fetch_note: str) -> Dict[str, str]:
    headline = safe_get(row, "headline")
    story_type = safe_get(row, "story_type")
    sport = safe_get(row, "sport")

    combined = clean(" ".join([headline, article_text, fallback_text]))
    facts = best_sentences(combined, headline, story_type, 4)

    # Never use boilerplate as a key fact.
    facts = [f for f in facts if not is_boilerplate_sentence(f)]

    if len(facts) >= 3 and article_text:
        confidence = "High"
    elif len(facts) >= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    source_status = "article_fetched" if article_text else "fallback_only"
    manual_review = "Yes" if confidence == "Low" else "No"

    story_summary = facts[0] if facts else generic_summary_from_headline(row)
    key_fact_1 = facts[0] if len(facts) > 0 else ""
    key_fact_2 = facts[1] if len(facts) > 1 else ""
    key_fact_3 = facts[2] if len(facts) > 2 else ""
    key_fact_4 = facts[3] if len(facts) > 3 else ""

    final_score = extract_final_score(facts)
    key_number = extract_key_number(facts, story_type)

    verification_notes = []
    if article_text:
        verification_notes.append("Fetched article text and filtered for meaningful article sentences.")
    else:
        verification_notes.append(fetch_note or "Could not fetch article text.")
    if confidence == "Low":
        verification_notes.append("Do not add exact stats, scores, records, jersey numbers, or player details unless manually verified from the source.")
    if not facts:
        verification_notes.append("No reliable article facts were extracted. Packet should be treated as a research prompt, not final copy.")

    milestone_text = key_number or (story_summary if story_type == "Record / Milestone" and confidence != "Low" else "")
    business_impact = (key_fact_2 or story_summary) if story_type in {"Business / Growth", "League Expansion"} and confidence != "Low" else ""
    main_takeaway = key_fact_2 or key_fact_1 or generic_summary_from_headline(row)

    return {
        "rank": safe_get(row, "rank"),
        "headline": headline,
        "sport": sport,
        "story_type": story_type,
        "source": safe_get(row, "source"),
        "link": safe_get(row, "link"),
        "context_confidence": confidence,
        "context_source_status": source_status,
        "verified_context_notes": " ".join(verification_notes),
        "story_summary": story_summary,
        "key_fact_1": key_fact_1,
        "key_fact_2": key_fact_2,
        "key_fact_3": key_fact_3,
        "key_fact_4": key_fact_4,
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
        "milestone_text": milestone_text,
        "historical_context": main_takeaway if story_type == "Record / Milestone" and confidence != "Low" else "",
        "key_number": key_number,
        "number_context": story_summary if key_number else "",
        "business_impact": business_impact,
        "main_takeaway": main_takeaway,
        "next_game_or_implication": "",
        "manual_review_flag": manual_review,
    }


def main() -> None:
    brief_rows = load_csv(DAILY_BRIEF_FILE)
    article_rows = load_csv(ARTICLES_FILE)
    article_rows_by_key = {key(r.get("title", "")): r for r in article_rows}

    output_rows: List[Dict[str, str]] = []

    for row in brief_rows:
        article_text, fetch_note = fetch_article_text(safe_get(row, "link"))
        fallback_text = load_article_summary(row, article_rows_by_key)
        output_rows.append(make_context(row, article_text, fallback_text, fetch_note))

    fieldnames = [
        "rank", "headline", "sport", "story_type", "source", "link",
        "context_confidence", "context_source_status", "verified_context_notes",
        "story_summary", "key_fact_1", "key_fact_2", "key_fact_3", "key_fact_4",
        "winner", "loser", "final_score", "matchup", "game_time", "tv_network",
        "key_player_1", "key_player_1_statline", "key_player_2", "key_player_2_statline",
        "watch_angle", "round_or_event", "top_performer_1", "top_performer_1_statline",
        "top_performer_2", "top_performer_2_statline", "milestone_text", "historical_context",
        "key_number", "number_context", "business_impact", "main_takeaway",
        "next_game_or_implication", "manual_review_flag",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    print(f"Created {OUTPUT_FILE} with {len(output_rows)} rows.")


if __name__ == "__main__":
    main()
