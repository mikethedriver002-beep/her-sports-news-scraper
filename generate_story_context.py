"""
Her Sports Daily Story Context Enricher
--------------------------------------

Reads:
    daily_content_brief.csv
    womens_sports_articles.csv, if available

Creates:
    story_context_enriched.csv

Purpose:
- Pull real article context from story URLs when possible
- Extract usable facts for graphics
- Avoid fake scores, fake stats, fake player details
- Mark weak/uncertain context clearly instead of inventing details

This script uses only Python standard library, so it works in GitHub Actions.
"""

from __future__ import annotations

import csv
import html
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Tuple

DAILY_BRIEF_FILE = "daily_content_brief.csv"
ARTICLES_FILE = "womens_sports_articles.csv"
OUTPUT_FILE = "story_context_enriched.csv"


def clean(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())[:140]


def safe_get(row: Dict[str, str], field: str) -> str:
    return clean(row.get(field, ""))


class ArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_p = False
        self.in_h1 = False
        self.current_text: List[str] = []
        self.title_parts: List[str] = []
        self.h1_parts: List[str] = []
        self.paragraphs: List[str] = []
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        attrs_dict = {k.lower(): v for k, v in attrs}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
            self.current_text = []
        elif tag == "h1":
            self.in_h1 = True
            self.current_text = []
        elif tag == "p":
            self.in_p = True
            self.current_text = []
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if name == "description" or prop == "og:description":
                if content and not self.meta_description:
                    self.meta_description = clean(content)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        text = clean(" ".join(self.current_text))
        if tag == "title" and self.in_title:
            self.title_parts.append(text)
            self.in_title = False
            self.current_text = []
        elif tag == "h1" and self.in_h1:
            self.h1_parts.append(text)
            self.in_h1 = False
            self.current_text = []
        elif tag == "p" and self.in_p:
            if len(text) >= 50:
                self.paragraphs.append(text)
            self.in_p = False
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.in_title or self.in_h1 or self.in_p:
            self.current_text.append(data)


def fetch_article_text(url: str) -> Tuple[str, str]:
    if not url:
        return "", "No URL available."
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailyBot/1.0; +https://github.com/)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read(800000)
            encoding = response.headers.get_content_charset() or "utf-8"
            html_text = raw.decode(encoding, errors="replace")
    except Exception as exc:
        return "", f"Fetch failed: {exc}"

    parser = ArticleHTMLParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass

    pieces: List[str] = []
    if parser.h1_parts:
        pieces.append(parser.h1_parts[0])
    if parser.meta_description:
        pieces.append(parser.meta_description)
    pieces.extend(parser.paragraphs[:12])
    article_text = clean(" ".join(pieces))

    if not article_text:
        article_text = clean(re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.I | re.S))
        article_text = clean(article_text[:6000])

    return article_text, "Fetched article HTML and extracted readable text."


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def merge_article_summary(brief_row: Dict[str, str], article_rows_by_key: Dict[str, Dict[str, str]]) -> str:
    headline = safe_get(brief_row, "headline")
    match = article_rows_by_key.get(key(headline), {})
    parts = [
        safe_get(match, "summary"),
        safe_get(match, "categories"),
        safe_get(brief_row, "why_it_matters"),
        safe_get(brief_row, "instagram_angle"),
        safe_get(brief_row, "decision_reason"),
    ]
    return clean(" ".join(p for p in parts if p))


def sentence_split(text: str) -> List[str]:
    text = clean(text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [clean(s) for s in sentences if len(clean(s)) >= 35]


def best_sentences(text: str, headline: str, story_type: str, max_items: int = 4) -> List[str]:
    sentences = sentence_split(text)
    if not sentences:
        return []

    keywords = set(re.findall(r"[a-zA-Z0-9']{4,}", headline.lower()))
    type_terms = {
        "Game Recap / Result": ["defeated", "beat", "won", "score", "championship", "title", "led", "points", "runs"],
        "Game Preview": ["will face", "matchup", "tip", "watch", "broadcast", "schedule", "enters"],
        "Record / Milestone": ["record", "milestone", "first", "history", "career", "all-time"],
        "Business / Growth": ["purse", "revenue", "viewership", "attendance", "investment", "sponsorship", "media rights"],
        "League Expansion": ["expansion", "franchise", "market", "launch", "team"],
        "Recruiting / Roster News": ["recruit", "commit", "transfer", "roster", "signed", "landed"],
        "Tournament Update": ["round", "lead", "advanced", "semifinal", "quarterfinal", "tournament"],
    }.get(story_type, [])

    scored = []
    for s in sentences:
        lower = s.lower()
        score = sum(1 for kw in keywords if kw in lower)
        score += 3 * sum(1 for term in type_terms if term in lower)
        if re.search(r"\b\d+[-–]\d+\b|\b\d+\s*(points|rebounds|assists|runs|hits|strikeouts|goals|saves)\b", lower):
            score += 5
        if any(word in lower for word in ["won", "defeated", "beat", "record", "championship", "title", "announced"]):
            score += 2
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    chosen: List[str] = []
    seen = set()
    for score, s in scored:
        normalized = key(s)
        if normalized in seen:
            continue
        if score <= 0 and len(chosen) >= 2:
            continue
        chosen.append(s)
        seen.add(normalized)
        if len(chosen) >= max_items:
            break
    return chosen


def extract_score(text: str) -> str:
    patterns = [
        r"\b(?:defeated|beat|beats|topped|tops|won|wins)\s+[^.]{0,80}?\b(\d{1,3})[-–](\d{1,3})\b",
        r"\b(\d{1,3})[-–](\d{1,3})\b",
        r"\b(\d{1,2})\s*to\s*(\d{1,2})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean(m.group(0))
    return ""


def extract_key_number(text: str) -> str:
    patterns = [
        r"\$[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|M|B)?",
        r"\b[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|percent|%)\b",
        r"\b[0-9]+(?:st|nd|rd|th)?\s+(?:career|straight|consecutive|record|points|rebounds|assists|runs|hits|strikeouts|goals|saves)\b",
        r"\brecord[- ]breaking\s+[^.]{0,60}",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return clean(m.group(0))
    return ""


def extract_entities_from_headline(headline: str) -> Tuple[str, str]:
    h = clean(headline)
    for sep in [" vs. ", " vs ", " over "]:
        if sep in h:
            left, right = h.split(sep, 1)
            return clean(left), clean(right)
    for word in ["beats", "beat", "defeats", "defeated"]:
        if f" {word} " in h.lower():
            parts = re.split(rf"\b{word}\b", h, flags=re.I)
            if len(parts) >= 2:
                return clean(parts[0]), clean(parts[1])
    return "", ""


def make_context(row: Dict[str, str], article_text: str, fallback_text: str) -> Dict[str, str]:
    headline = safe_get(row, "headline")
    story_type = safe_get(row, "story_type")
    sport = safe_get(row, "sport")
    combined = clean(" ".join([headline, fallback_text, article_text]))

    source_status = "article_fetched" if article_text else "fallback_only"
    confidence = "Medium" if article_text else "Low"
    verification_notes = "Used fetched article text." if article_text else "Could not fetch full article. Used available CSV summary and headline only. Verify before adding specific stats."

    facts = best_sentences(combined, headline, story_type, 4)
    while len(facts) < 4:
        facts.append("")

    score_text = extract_score(combined)
    key_number = extract_key_number(combined)
    entity_1, entity_2 = extract_entities_from_headline(headline)

    story_summary = facts[0] if facts[0] else safe_get(row, "why_it_matters") or headline
    main_takeaway = facts[1] if facts[1] else safe_get(row, "instagram_angle") or safe_get(row, "why_it_matters")

    return {
        "rank": safe_get(row, "rank"),
        "headline": headline,
        "sport": sport,
        "story_type": story_type,
        "source": safe_get(row, "source"),
        "link": safe_get(row, "link"),
        "context_confidence": confidence,
        "context_source_status": source_status,
        "verified_context_notes": verification_notes,
        "story_summary": story_summary,
        "key_fact_1": facts[0],
        "key_fact_2": facts[1],
        "key_fact_3": facts[2],
        "key_fact_4": facts[3],
        "winner": entity_1 if story_type == "Game Recap / Result" else "",
        "loser": entity_2 if story_type == "Game Recap / Result" else "",
        "final_score": score_text if story_type == "Game Recap / Result" else "",
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
        "milestone_text": (key_number or story_summary) if story_type == "Record / Milestone" else "",
        "historical_context": main_takeaway if story_type == "Record / Milestone" else "",
        "key_number": key_number,
        "number_context": story_summary if key_number else "",
        "business_impact": main_takeaway if story_type in {"Business / Growth", "League Expansion"} else "",
        "main_takeaway": main_takeaway,
        "next_game_or_implication": "",
        "manual_review_flag": "Yes" if confidence == "Low" else "No",
    }


def main() -> None:
    brief_rows = load_csv(DAILY_BRIEF_FILE)
    article_rows = load_csv(ARTICLES_FILE)
    article_rows_by_key = {key(r.get("title", "")): r for r in article_rows}
    output_rows: List[Dict[str, str]] = []

    for row in brief_rows:
        link = safe_get(row, "link")
        article_text, fetch_note = fetch_article_text(link)
        fallback_text = merge_article_summary(row, article_rows_by_key)
        context = make_context(row, article_text, fallback_text)
        if fetch_note and context["context_source_status"] == "fallback_only":
            context["verified_context_notes"] = fetch_note + " " + context["verified_context_notes"]
        output_rows.append(context)

    fieldnames = [
        "rank", "headline", "sport", "story_type", "source", "link", "context_confidence",
        "context_source_status", "verified_context_notes", "story_summary", "key_fact_1", "key_fact_2",
        "key_fact_3", "key_fact_4", "winner", "loser", "final_score", "matchup", "game_time",
        "tv_network", "key_player_1", "key_player_1_statline", "key_player_2", "key_player_2_statline",
        "watch_angle", "round_or_event", "top_performer_1", "top_performer_1_statline",
        "top_performer_2", "top_performer_2_statline", "milestone_text", "historical_context",
        "key_number", "number_context", "business_impact", "main_takeaway", "next_game_or_implication",
        "manual_review_flag",
    ]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    print(f"Created {OUTPUT_FILE} with {len(output_rows)} rows.")


if __name__ == "__main__":
    main()
