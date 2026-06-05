"""
Her Sports Daily Women's Sports News Scraper v8
-----------------------------------------------

This version tightens the editorial logic after reviewing real daily brief outputs.

Output files:
1. womens_sports_articles.csv
   Full scrape with scores, classifications, duplicate info, and decision reasons.

2. daily_content_brief.csv
   A small, stricter editorial shortlist for what Her Sports Daily should consider posting.

Core idea:
- Scoring is 0 to 100, not everything gets a 10.
- "Must Post" is rare and capped.
- Ranking/opinion/rumor stories cannot become Must Post.
- Duplicate topics are removed from the daily brief.
- The brief prioritizes strong, fresh, women’s-sports-relevant stories from trusted sources.
"""

from __future__ import annotations

import csv
import html
import math
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, Iterable, List, Optional, Tuple


OUTPUT_FILE = "womens_sports_articles.csv"
DAILY_BRIEF_FILE = "daily_content_brief.csv"

MAX_DAILY_BRIEF_ITEMS = 10
MAX_MUST_POST_ITEMS = 2
MAX_PER_CLUSTER = 1
MAX_PER_PRIMARY_ENTITY = 1
MAX_PER_SOURCE = 3

# Sport maxes are intentionally tighter so the brief does not become all WNBA or all softball.
SPORT_MAXES = {
    "WNBA": 4,
    "NWSL / Women's Soccer": 3,
    "PWHL / Women's Hockey": 3,
    "NCAA Women's Basketball": 3,
    "Softball": 2,
    "Tennis": 2,
    "Golf / LPGA": 2,
    "Volleyball": 2,
    "Women's Sports": 2,
}


def google_news(query: str) -> str:
    return (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )


FEED_URLS = [
    # Direct RSS feeds
    "https://justwomenssports.com/feed/",
    "https://womeninsport.org/feed/",
    "https://www.womenssportsfoundation.org/feed/",
    "https://winsidr.com/feed",
    "https://herhoopstats.substack.com/feed",
    "https://equalizersoccer.com/feed/",
    "https://shekicks.net/feed/",
    "https://girlssoccernetwork.com/feed/",
    "https://sports.yahoo.com/wnba/rss",

    # Mainstream sources through Google News RSS
    google_news("site:apnews.com women's sports OR WNBA OR NWSL OR PWHL when:3d"),
    google_news("site:espn.com WNBA OR women's college basketball OR NWSL when:3d"),
    google_news("site:sports.yahoo.com women's sports OR WNBA OR NWSL OR PWHL when:3d"),
    google_news("site:cbssports.com WNBA OR women's college basketball OR NWSL when:3d"),
    google_news("site:foxsports.com WNBA OR women's college basketball OR women's soccer when:3d"),
    google_news("site:reuters.com women's sports OR WNBA OR NWSL OR PWHL when:7d"),
    google_news("site:usatoday.com women's sports OR WNBA OR NWSL OR NCAA women when:7d"),
    google_news("site:si.com WNBA OR women's sports OR NWSL when:7d"),

    # Official league and governing body sources
    google_news("site:wnba.com/news WNBA when:3d"),
    google_news("site:nwslsoccer.com/news NWSL when:3d"),
    google_news("site:thepwhl.com/en/news PWHL when:3d"),
    google_news("site:ussoccer.com USWNT women's soccer when:7d"),
    google_news("site:ncaa.com women's basketball OR softball OR volleyball OR gymnastics when:7d"),
    google_news("site:lpga.com LPGA women's golf when:7d"),
    google_news("site:wtatennis.com WTA tennis women when:7d"),

    # Specialty and niche women’s sports outlets
    google_news("site:swishappeal.com WNBA OR women's basketball when:7d"),
    google_news("site:thenexthoops.com WNBA OR women's basketball when:7d"),
    google_news("site:theixsports.com women's sports OR WNBA OR NWSL OR PWHL when:7d"),
    google_news("site:theicegarden.com women's hockey OR PWHL when:7d"),
    google_news("site:equalizersoccer.com NWSL OR USWNT OR women's soccer when:7d"),
    google_news("site:thegistsports.com women's sports OR WNBA OR NWSL OR PWHL when:7d"),
    google_news("site:togethxr.com women's sports OR WNBA OR NWSL OR athlete when:14d"),
    google_news("site:hoopfeed.com WNBA OR women's basketball when:14d"),

    # Business and growth stories
    google_news("site:sportsbusinessjournal.com women's sports OR WNBA OR NWSL OR PWHL when:14d"),
    google_news("site:frontofficesports.com women's sports OR WNBA OR NWSL OR PWHL when:14d"),
    google_news("site:sportspro.com women's sports OR WNBA OR NWSL OR PWHL when:14d"),
    google_news("site:axios.com women's sports OR WNBA OR NWSL OR PWHL when:14d"),

    # Broader topic searches
    google_news("women's sports record attendance viewership investment when:7d"),
    google_news("women's sports expansion new league media rights sponsorship when:14d"),
    google_news("WNBA NWSL PWHL women's sports when:3d"),
    google_news("women's college basketball softball volleyball gymnastics when:7d"),
]


SPORT_RULES: List[Tuple[str, List[str]]] = [
    ("WNBA", ["wnba", "fever", "sky", "aces", "liberty", "lynx", "storm", "mercury", "dream", "mystics", "sparks", "wings", "sun", "valkyries", "fire", "tempo"]),
    ("NCAA Women's Basketball", ["women's basketball", "ncaa basketball", "march madness", "final four", "uconn", "south carolina", "usc", "lsu", "notre dame", "iowa"]),
    ("NWSL / Women's Soccer", ["nwsl", "uswnt", "women's soccer", "women's football", "gotham", "thorns", "angel city", "spirit", "wave", "royals", "legacy fc", "summit fc", "lionesses"]),
    ("PWHL / Women's Hockey", ["pwhl", "women's hockey", "fleet", "frost", "sirens", "charge", "victoire", "sceptres", "torrent", "goldeneyes"]),
    ("Tennis", ["tennis", "wta", "wimbledon", "us open", "french open", "australian open", "roland garros", "coco gauff", "naomi osaka", "swiatek", "sabalenka", "serena", "venus"]),
    ("Golf / LPGA", ["lpga", "women's open", "golf", "nelly korda", "lexi thompson", "rose zhang", "kupcho"]),
    ("Softball", ["softball", "college world series", "wcws"]),
    ("Volleyball", ["volleyball", "lovb", "major league volleyball", "mlv", "pro volleyball", "nebraska volleyball"]),
    ("Gymnastics", ["gymnastics", "simone biles", "suni lee", "olympic gymnastics"]),
    ("Track & Field", ["track", "athletics", "sprint", "sha'carri", "sydney mclaughlin", "gabby thomas"]),
    ("Rugby", ["rugby", "women's rugby"]),
    ("Cricket", ["cricket", "t20", "women's world cup"]),
    ("Baseball", ["women's baseball", "women's pro baseball", "wpbl"]),
]


BIG_NAMES = [
    "caitlin clark", "angel reese", "paige bueckers", "juju watkins", "aja wilson", "a'ja wilson",
    "sabrina ionescu", "breanna stewart", "napheesa collier", "diana taurasi", "kelsey plum",
    "cameron brink", "aliyah boston", "rhyne howard", "trinity rodman", "sophia smith",
    "alex morgan", "coco gauff", "naomi osaka", "serena williams", "venus williams",
    "simone biles", "suni lee", "nelly korda", "rose zhang", "jennifer kupcho",
    "sha'carri richardson", "sydney mclaughlin", "katie ledecky", "ilona maher",
    "reese atwood", "kelsey mitchell", "raven johnson",
]


FEMALE_ATHLETE_SPORT_HINTS = {
    "caitlin clark": "WNBA",
    "angel reese": "WNBA",
    "paige bueckers": "WNBA",
    "juju watkins": "NCAA Women's Basketball",
    "aja wilson": "WNBA",
    "a'ja wilson": "WNBA",
    "sabrina ionescu": "WNBA",
    "breanna stewart": "WNBA",
    "napheesa collier": "WNBA",
    "diana taurasi": "WNBA",
    "kelsey plum": "WNBA",
    "cameron brink": "WNBA",
    "aliyah boston": "WNBA",
    "rhyne howard": "WNBA",
    "kelsey mitchell": "WNBA",
    "raven johnson": "NCAA Women's Basketball",
    "trinity rodman": "NWSL / Women's Soccer",
    "sophia smith": "NWSL / Women's Soccer",
    "alex morgan": "NWSL / Women's Soccer",
    "coco gauff": "Tennis",
    "naomi osaka": "Tennis",
    "serena williams": "Tennis",
    "venus williams": "Tennis",
    "simone biles": "Gymnastics",
    "suni lee": "Gymnastics",
    "nelly korda": "Golf / LPGA",
    "rose zhang": "Golf / LPGA",
    "jennifer kupcho": "Golf / LPGA",
    "sha'carri richardson": "Track & Field",
    "sydney mclaughlin": "Track & Field",
    "katie ledecky": "Women's Sports",
    "ilona maher": "Rugby",
}


MALE_ATHLETE_OR_EVENT_TERMS = [
    "matteo arnaldi", "atp", "men's singles", "mens singles", "men’s singles",
    "men's semifinal", "men’s semifinal", "nba", "nfl", "nhl", "mlb", "men's basketball",
    "men’s basketball", "men's baseball", "men’s baseball", "diii baseball championship",
    "di baseball championship", "dii baseball championship",
]


LOW_VALUE_SOFT_STORY_TERMS = [
    "heartwarming moment", "shares moment", "share heartwarming", "reacts to", "reaction to",
    "trolls", "fans react", "social media reacts", "outfit", "fashion", "boyfriend",
    "girlfriend", "dating", "viral moment",
]


GUIDE_OR_EXPLAINER_TERMS = [
    "everything you need to know", "how to watch", "preview", "prediction",
    "talking points", "takeaways", "what to know",
]


TEAM_AND_TOPIC_ENTITIES = [
    # WNBA
    "indiana fever", "chicago sky", "las vegas aces", "new york liberty", "minnesota lynx",
    "seattle storm", "phoenix mercury", "atlanta dream", "washington mystics", "los angeles sparks",
    "dallas wings", "connecticut sun", "golden state valkyries", "portland fire", "toronto tempo",
    # Soccer
    "gotham fc", "angel city", "portland thorns", "washington spirit", "san diego wave",
    "kansas city current", "orlando pride", "north carolina courage", "houston dash",
    "boston legacy", "denver summit", "utah royals", "seattle reign", "bay fc", "uswnt",
    # Softball and college
    "texas softball", "texas", "saint leo", "oklahoma", "college world series", "women's college world series", "wcws",
    # Other leagues and topics
    "pwhl", "unrivaled", "project b", "major league volleyball", "women's pro baseball league",
    "wpbl", "world cup", "wimbledon", "french open", "roland garros", "us women's open",
]


SOURCE_KEYWORDS: List[Tuple[str, int, List[str]]] = [
    ("Official League / Governing Body", 10, ["wnba", "nwsl", "pwhl", "ncaa.com", "ussoccer", "lpga", "wta tennis", "fifa", "team usa"]),
    ("Wire / Mainstream", 9, ["associated press", "ap news", "apnews", "reuters", "espn", "cbs sports", "yahoo sports", "usa today", "sports illustrated", "fox sports", "nbc sports", "the athletic"]),
    ("Business", 8, ["sports business journal", "front office sports", "sportspro", "axios", "sportico", "forbes"]),
    ("Specialty Women's Sports", 8, ["just women's sports", "just womens sports", "the gist", "the ix", "swish appeal", "the next", "winsidr", "her hoop stats", "equalizer", "the ice garden", "hoopfeed", "togethxr"]),
    ("Advocacy / Foundation", 7, ["women in sport", "women's sports foundation"]),
]


WOMENS_CONTEXT_TERMS = [
    "women", "women's", "womens", "female", "girls", "wnba", "nwsl", "pwhl", "wta",
    "lpga", "uswnt", "softball", "volleyball", "gymnastics", "wcws", "ncaaw",
]


MALE_OR_UNRELATED_TERMS = [
    "nba", "nfl", "nhl", "mlb", "men's", "mens", "premier league", "la liga",
    "ufc", "boxing", "wwe", "nascar", "formula 1",
]


SENSITIVE_TERMS = [
    "abuse", "assault", "harassment", "lawsuit", "investigation", "arrest", "death",
    "died", "killed", "violence", "scandal", "allegation", "allegations",
]


RUMOR_OR_SPECULATION_TERMS = [
    "rumor", "rumors", "reportedly", "sources", "could", "might", "linked to",
    "trade speculation", "likely to be targeted", "expected to", "potential",
]


OPINION_OR_LOW_URGENCY_TERMS = [
    "power rankings", "rankings", "way-too-early", "mock draft", "predictions",
    "odds", "takeaways", "winners and losers", "domino effects", "watch list",
    "awards", "mvp favorite", "best", "top 10", "top five",
]


HIGH_VALUE_TERMS = [
    "championship", "title", "wins", "defeats", "beats", "record", "historic",
    "first", "shatter", "expansion", "media rights", "investment", "sponsorship",
    "viewership", "attendance", "sold out", "launch", "new league",
]


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "over", "after", "before",
    "about", "what", "why", "how", "when", "where", "women", "womens", "woman", "sports",
    "sport", "news", "new", "latest", "watch", "live", "highlights", "full", "today",
    "game", "games", "season", "team", "teams", "player", "players", "says", "said",
    "more", "than", "will", "would", "could", "their", "they", "them", "have", "has",
    "been", "best", "top", "after", "before", "during", "around", "against", "again",
    "first", "second", "third",
}


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; HerSportsDailyBot/1.0; +https://github.com/)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def parse_date(raw_date: str) -> Tuple[str, Optional[datetime]]:
    raw_date = clean_text(raw_date)
    if not raw_date:
        return "", None

    try:
        parsed = parsedate_to_datetime(raw_date)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat(), parsed
    except Exception:
        return raw_date, None


def age_hours(published_dt: Optional[datetime]) -> Optional[float]:
    if not published_dt:
        return None
    now = datetime.now(timezone.utc)
    return max(0.0, (now - published_dt).total_seconds() / 3600)


def tidy_google_title(title: str, source: str) -> str:
    title = clean_text(title)
    source = clean_text(source)
    if source and title.endswith(f" - {source}"):
        return title[: -(len(source) + 3)].strip()
    return title


def parse_feed(url: str) -> List[Dict[str, str]]:
    articles: List[Dict[str, str]] = []

    try:
        xml_data = fetch_url(url)
        root = ET.fromstring(xml_data)
    except Exception as exc:
        print(f"Feed failed: {url} | {exc}")
        return articles

    channel = root.find("channel")
    source_title = url

    if channel is not None:
        source_title = clean_text(channel.findtext("title", default=url))

        for item in channel.findall("item"):
            item_source = source_title
            source_node = item.find("source")
            if source_node is not None and source_node.text:
                item_source = clean_text(source_node.text)

            published_iso, published_dt = parse_date(item.findtext("pubDate", default=""))
            title = tidy_google_title(item.findtext("title", default=""), item_source)
            link = clean_text(item.findtext("link", default=""))
            categories = ", ".join(clean_text(c.text or "") for c in item.findall("category") if c.text)
            summary = clean_text(item.findtext("description", default=""))

            articles.append({
                "source": item_source,
                "title": title,
                "link": link,
                "published": published_iso,
                "published_timestamp": published_dt.isoformat() if published_dt else "",
                "age_hours": "" if age_hours(published_dt) is None else f"{age_hours(published_dt):.1f}",
                "categories": categories,
                "summary": summary,
            })

        return articles

    # Basic Atom support
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    source_title = clean_text(root.findtext("atom:title", default=url, namespaces=ns))

    for entry in entries:
        date_raw = (
            entry.findtext("atom:published", default="", namespaces=ns)
            or entry.findtext("atom:updated", default="", namespaces=ns)
        )
        published_iso, published_dt = parse_date(date_raw)
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ns))
        summary = clean_text(entry.findtext("atom:summary", default="", namespaces=ns))
        link = ""

        link_elem = entry.find("atom:link", ns)
        if link_elem is not None:
            link = link_elem.attrib.get("href", "")

        articles.append({
            "source": source_title,
            "title": title,
            "link": link,
            "published": published_iso,
            "published_timestamp": published_dt.isoformat() if published_dt else "",
            "age_hours": "" if age_hours(published_dt) is None else f"{age_hours(published_dt):.1f}",
            "categories": "",
            "summary": summary,
        })

    return articles


def combined_text(article: Dict[str, str]) -> str:
    return " ".join([
        article.get("title", ""),
        article.get("summary", ""),
        article.get("categories", ""),
        article.get("source", ""),
    ]).lower()


def has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def count_any(text: str, terms: Iterable[str]) -> int:
    return sum(1 for term in terms if term in text)


def classify_sport(text: str) -> str:
    # Use athlete hints first because broad Google summaries can include unrelated league terms.
    for athlete, sport in FEMALE_ATHLETE_SPORT_HINTS.items():
        if athlete in text:
            return sport

    # Then use specific sport keyword rules.
    sport_scores: Dict[str, int] = {}
    for sport, keywords in SPORT_RULES:
        sport_scores[sport] = sum(1 for keyword in keywords if keyword in text)

    if sport_scores:
        best_sport, best_score = max(sport_scores.items(), key=lambda item: item[1])
        if best_score > 0:
            return best_sport

    return "Women's Sports"


def classify_story_type(text: str) -> str:
    if has_any(text, RUMOR_OR_SPECULATION_TERMS):
        return "Rumor / Needs Verification"

    if has_any(text, OPINION_OR_LOW_URGENCY_TERMS) or has_any(text, GUIDE_OR_EXPLAINER_TERMS):
        return "Opinion / Rankings"

    # True results require explicit result verbs. Do not treat "Championship" alone as a result.
    result_phrases = [
        "wins", "won", "defeats", "defeated", "beats", "beat", "tops", "topped",
        "takes down", "claims title", "wins title", "wins championship",
        "captures title", "secures championship", "final score"
    ]
    if any(term in text for term in result_phrases):
        return "Game Recap / Result"

    if any(term in text for term in ["announces", "announced", "signs", "signed", "traded", "trade", "draft", "hires", "fired"]):
        return "Breaking / Transaction"

    if any(term in text for term in ["revenue", "media rights", "sponsorship", "valuation", "investment", "ratings", "viewership", "attendance", "sold out"]):
        return "Business / Growth"

    if any(term in text for term in ["expansion", "new team", "franchise", "launch", "debut", "inaugural"]):
        return "League Expansion"

    if any(term in text for term in ["preview", "faces", "matchup", "schedule", "where to watch", "tonight", "tomorrow"]):
        return "Game Preview"

    if any(term in text for term in ["profile", "story", "journey", "feature", "legacy", "comeback"]):
        return "Player Feature"

    if any(term in text for term in ["equal pay", "gender", "barrier", "trailblazer", "activism", "charity", "foundation", "women in sport"]):
        return "Culture / Advocacy"

    if any(term in text for term in ["injury", "injured", "questionable", "out", "return", "availability"]):
        return "Injury / Availability"

    return "General News"


def source_tier_and_quality(source: str) -> Tuple[str, int]:
    source_text = source.lower()
    for tier, quality, keywords in SOURCE_KEYWORDS:
        if any(keyword in source_text for keyword in keywords):
            return tier, quality
    if "google news" in source_text:
        return "Aggregator", 4
    return "Other", 6


def extract_primary_entity(text: str) -> str:
    for name in BIG_NAMES:
        if name in text:
            return name.title()

    for entity in TEAM_AND_TOPIC_ENTITIES:
        if entity in text:
            return entity.title()

    return ""


def topic_signature(text: str, sport: str, primary_entity: str) -> str:
    # Force known recurring stories into one cluster.
    if "texas" in text and ("softball" in text or "college world series" in text or "wcws" in text):
        return "softball::texas_wcws_title"
    if "saint leo" in text and "softball" in text:
        return "softball::saint_leo_softball_title"
    if "serena" in text and "mboko" in text:
        return "tennis::serena_mboko_hsbc"
    if "caitlin clark" in text and ("record" in text or "records" in text):
        return "wnba::caitlin_clark_records"
    if "a'ja wilson" in text or "aja wilson" in text:
        return "wnba::aja_wilson"
    if "pwhl" in text and "expansion" in text:
        return "pwhl::expansion_targets"

    if primary_entity:
        return f"{sport.lower()}::{primary_entity.lower()}"

    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    important = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    return f"{sport.lower()}::" + "_".join(important[:8])


def is_wrong_or_low_fit(text: str, sport: str) -> bool:
    # Hard blocks for clearly men's or unrelated stories that broad feeds sometimes pull.
    if has_any(text, MALE_ATHLETE_OR_EVENT_TERMS):
        return True

    # Tennis and golf are mixed-gender news environments. Require an explicit women's signal
    # or a known female athlete for those sports.
    if sport in {"Tennis", "Golf / LPGA"}:
        has_female_athlete = any(name in text for name in FEMALE_ATHLETE_SPORT_HINTS)
        has_women_signal = has_any(text, ["women", "women's", "womens", "wta", "lpga", "us women's open", "ladies"])
        if not has_female_athlete and not has_women_signal:
            return True

    # Generic NCAA baseball is not women's sports unless explicitly WPBL/women's baseball.
    if "baseball championship" in text and not has_any(text, ["women's baseball", "womens baseball", "wpbl", "women's pro baseball"]):
        return True

    # Keep stories that clearly include women's sport context.
    has_women_context = has_any(text, WOMENS_CONTEXT_TERMS) or sport not in {"Women's Sports"}
    if has_women_context:
        return False

    if has_any(text, MALE_OR_UNRELATED_TERMS):
        return True

    return False


def freshness_score(article: Dict[str, str], story_type: str) -> Tuple[int, str]:
    raw = article.get("age_hours", "")
    if not raw:
        return 6, "No parsed date"

    try:
        hours = float(raw)
    except ValueError:
        return 6, "No parsed date"

    # Hard expiration rules. Game/previews get stale quickly. Business/features can live longer.
    if story_type in {"Game Recap / Result", "Game Preview", "Breaking / Transaction", "Injury / Availability", "Rumor / Needs Verification"}:
        if hours <= 12:
            return 18, "Fresh under 12 hours"
        if hours <= 24:
            return 15, "Fresh under 24 hours"
        if hours <= 48:
            return 10, "Recent under 48 hours"
        if hours <= 72:
            return 5, "Aging under 72 hours"
        return -25, "Expired for daily coverage"

    # Evergreen or business stories decay slower.
    if hours <= 24:
        return 15, "Fresh under 24 hours"
    if hours <= 72:
        return 12, "Recent under 72 hours"
    if hours <= 168:
        return 8, "Still usable this week"
    if hours <= 336:
        return 2, "Evergreen but old"
    return -15, "Too old"


def story_value_score(text: str, story_type: str, sport: str) -> Tuple[int, str]:
    # This is intentionally conservative. "Championship" as an event name is not enough.
    true_title_result = any(term in text for term in [
        "wins championship", "won championship", "wins the championship", "claims title",
        "wins title", "captures title", "defeats", "defeated", "beats", "beat", "wins 2026",
        "wins the 2026", "final score"
    ])

    if true_title_result:
        return 36, "Confirmed result/title story"
    if any(term in text for term in ["record", "historic", "first", "shatter", "shatters", "breaks record"]):
        return 32, "Record or historic milestone"
    if story_type == "Business / Growth":
        return 30, "Business/growth story"
    if story_type == "League Expansion":
        return 30, "Expansion story"
    if story_type == "Breaking / Transaction":
        return 26, "Confirmed breaking/transaction story"
    if story_type == "Game Recap / Result":
        return 24, "Game result story"
    if story_type == "Game Preview":
        return 16, "Preview story"
    if story_type == "Player Feature":
        return 14, "Feature story"
    if story_type == "Culture / Advocacy":
        return 14, "Culture/impact story"
    if story_type == "Injury / Availability":
        return 13, "Availability story"
    if story_type == "Opinion / Rankings":
        return 6, "Opinion/ranking/explainer story"
    if story_type == "Rumor / Needs Verification":
        return 4, "Rumor/speculation story"
    return 10, "General update"


def brand_fit_score(text: str, sport: str) -> Tuple[int, str]:
    if sport in {"WNBA", "NWSL / Women's Soccer", "PWHL / Women's Hockey", "NCAA Women's Basketball"}:
        return 15, f"Core brand sport: {sport}"
    if sport in {"Softball", "Volleyball", "Tennis", "Golf / LPGA", "Gymnastics", "Track & Field"}:
        return 11, f"Strong secondary sport: {sport}"
    if sport in {"Rugby", "Cricket", "Baseball"}:
        return 8, f"Niche growth sport: {sport}"
    return 5, "General women's sports fit"


def engagement_score(text: str) -> Tuple[int, str]:
    score = 0
    reasons = []

    if has_any(text, BIG_NAMES):
        score += 8
        reasons.append("major athlete")
    high_value_matches = count_any(text, HIGH_VALUE_TERMS)
    if high_value_matches:
        score += min(6, high_value_matches * 2)
        reasons.append("high-interest keyword")

    return min(score, 12), ", ".join(reasons) if reasons else "normal interest"


def penalty_score(text: str, source_quality: int, story_type: str, freshness_reason: str) -> Tuple[int, List[str]]:
    penalty = 0
    reasons = []

    if has_any(text, RUMOR_OR_SPECULATION_TERMS):
        penalty -= 22
        reasons.append("rumor/speculation penalty")
    if story_type == "Opinion / Rankings":
        penalty -= 18
        reasons.append("opinion/ranking/explainer penalty")
    if has_any(text, LOW_VALUE_SOFT_STORY_TERMS):
        penalty -= 24
        reasons.append("soft/viral story penalty")
    if has_any(text, SENSITIVE_TERMS):
        penalty -= 25
        reasons.append("sensitive topic penalty")
    if has_any(text, MALE_ATHLETE_OR_EVENT_TERMS):
        penalty -= 40
        reasons.append("men's/unrelated story penalty")
    if source_quality <= 5:
        penalty -= 10
        reasons.append("low source quality penalty")
    if "Expired" in freshness_reason or "Too old" in freshness_reason:
        penalty -= 20
        reasons.append("staleness penalty")
    if len(text) < 80:
        penalty -= 4
        reasons.append("thin headline/context penalty")

    return penalty, reasons


def calculate_editorial_score(article: Dict[str, str], sport: str, story_type: str, source_quality: int) -> Tuple[int, str, Dict[str, int]]:
    text = combined_text(article)

    fresh, freshness_reason = freshness_score(article, story_type)
    story_value, story_reason = story_value_score(text, story_type, sport)
    brand_fit, brand_reason = brand_fit_score(text, sport)
    engagement, engagement_reason = engagement_score(text)
    source_component = int(round(source_quality * 1.4))  # max 14

    penalty, penalty_reasons = penalty_score(text, source_quality, story_type, freshness_reason)

    total = fresh + story_value + brand_fit + engagement + source_component + penalty
    total = max(0, min(100, total))

    parts = {
        "freshness_component": fresh,
        "story_value_component": story_value,
        "brand_fit_component": brand_fit,
        "engagement_component": engagement,
        "source_component": source_component,
        "penalty_component": penalty,
    }

    reason = (
        f"{story_reason}; {freshness_reason}; {brand_reason}; "
        f"source quality {source_quality}/10; engagement: {engagement_reason}"
    )
    if penalty_reasons:
        reason += "; penalties: " + ", ".join(penalty_reasons)

    return total, reason, parts


def verification_needed(text: str, source_quality: int) -> bool:
    return source_quality < 8 or has_any(text, RUMOR_OR_SPECULATION_TERMS)


def sensitive_flag(text: str) -> bool:
    return has_any(text, SENSITIVE_TERMS)


def time_sensitive(story_type: str) -> str:
    if story_type in {"Breaking / Transaction", "Game Preview", "Game Recap / Result", "Injury / Availability", "Rumor / Needs Verification"}:
        return "Yes"
    return "No"


def content_bucket(story_type: str, sport: str, text: str) -> str:
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the Game"
    if story_type in {"Game Recap / Result", "Game Preview"}:
        return "Tonight / Game Coverage"
    if has_any(text, BIG_NAMES):
        return "Star Watch"
    if story_type in {"Culture / Advocacy", "Player Feature"}:
        return "Culture & Impact"
    if sport in {"NCAA Women's Basketball", "Softball", "Volleyball"}:
        return "College Spotlight"
    return "Daily News"


def content_lane(story_type: str, sport: str, text: str) -> str:
    if has_any(text, BIG_NAMES):
        return "Star-driven engagement"
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the game"
    if story_type in {"Game Preview", "Game Recap / Result"}:
        return "Game coverage"
    if sport in {"NCAA Women's Basketball", "Softball", "Volleyball"}:
        return "College spotlight"
    return "Daily news"


def base_decision(article: Dict[str, str]) -> Tuple[str, str]:
    score = int(article.get("editorial_score", "0") or 0)
    source_quality = int(article.get("source_quality", "0") or 0)
    story_type = article.get("story_type", "")

    if article.get("wrong_or_low_fit") == "Yes":
        return "Skip", "Likely wrong-sport or low-fit story."
    if article.get("sensitive") == "Yes":
        return "Review Before Posting", "Sensitive topic requires manual review."
    if article.get("verification_needed") == "Yes" and score >= 62:
        return "Verify First", "Needs verification before posting because it is speculative or not from a strong enough source."
    if article.get("verification_needed") == "Yes":
        return "Skip", "Too speculative or weakly sourced."
    if story_type == "Opinion / Rankings" and score < 78:
        return "Save for Weekend", "Opinion/ranking/explainer stories are lower urgency."
    if story_type == "Opinion / Rankings":
        return "Maybe Post", "Strong ranking/explainer story, but not urgent."
    if "Expired" in article.get("score_reason", "") or "Too old" in article.get("score_reason", ""):
        return "Skip", "Too stale for daily coverage."
    if score >= 92 and source_quality >= 8 and story_type not in {"Opinion / Rankings", "Rumor / Needs Verification"}:
        return "Must Post", "High score, strong source, timely, and not speculative."
    if score >= 78:
        return "Maybe Post", "Strong candidate, but not mandatory."
    if score >= 64:
        return "Save for Weekend", "Useful but not urgent."
    return "Skip", "Below posting threshold."


def recommended_timing(decision: str, story_type: str) -> str:
    if decision == "Verify First":
        return "Verify first"
    if decision == "Review Before Posting":
        return "Manual review first"
    if decision == "Must Post":
        return "Post ASAP"
    if story_type == "Game Preview":
        return "Post before tipoff/kickoff"
    if story_type == "Game Recap / Result":
        return "Post within 2 hours if still fresh"
    if story_type in {"Business / Growth", "League Expansion", "Player Feature"}:
        return "Post during daytime engagement window"
    if decision == "Save for Weekend":
        return "Save for weekend or filler slot"
    return "Use when convenient"


def post_format(story_type: str, score: int) -> str:
    if story_type in {"Breaking / Transaction", "Game Recap / Result"} and score >= 80:
        return "Breaking graphic + carousel"
    if story_type == "Business / Growth":
        return "Data carousel"
    if story_type == "League Expansion":
        return "Map/expansion carousel"
    if story_type == "Game Preview":
        return "Tonight graphic"
    if story_type == "Player Feature":
        return "Reel or story feature"
    if story_type == "Opinion / Rankings":
        return "Debate carousel"
    return "Story post"


def hook(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    if story_type == "Business / Growth":
        return "Women's sports are becoming impossible for the business world to ignore."
    if story_type == "League Expansion":
        return "Another market is betting big on women's sports."
    if story_type == "Game Preview":
        return "Here is why this matchup is worth your time tonight."
    if story_type == "Game Recap / Result":
        return "Here is the quick version of what happened and why it matters."
    if story_type == "Breaking / Transaction":
        return "This is developing, but it is already worth tracking."
    if story_type == "Opinion / Rankings":
        return "Agree or disagree with this one?"
    return article.get("title", "")


def first_slide(article: Dict[str, str]) -> str:
    title = article.get("title", "")
    story_type = article.get("story_type", "")
    if story_type == "Business / Growth":
        return f"The business of women's sports keeps growing: {title}"
    if story_type == "League Expansion":
        return f"Expansion watch: {title}"
    if story_type == "Game Preview":
        return f"Tonight's watchlist: {title}"
    if story_type == "Game Recap / Result":
        return f"Quick recap: {title}"
    if story_type == "Breaking / Transaction":
        return f"Breaking: {title}"
    if story_type == "Opinion / Rankings":
        return f"Debate this: {title}"
    return title


def carousel_outline(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    if story_type == "Business / Growth":
        return "Slide 1: headline stat | Slide 2: what changed | Slide 3: why it matters | Slide 4: what comes next"
    if story_type == "League Expansion":
        return "Slide 1: expansion headline | Slide 2: market/team details | Slide 3: why demand is rising | Slide 4: fan question"
    if story_type == "Game Preview":
        return "Slide 1: matchup | Slide 2: player to watch | Slide 3: key matchup | Slide 4: prediction or question"
    if story_type == "Game Recap / Result":
        return "Slide 1: result | Slide 2: top performer | Slide 3: turning point | Slide 4: what is next"
    if story_type == "Breaking / Transaction":
        return "Slide 1: news | Slide 2: confirmed details | Slide 3: context | Slide 4: what to watch next"
    if story_type == "Opinion / Rankings":
        return "Slide 1: claim/ranking | Slide 2: why it matters | Slide 3: counterpoint | Slide 4: ask followers"
    return "Slide 1: headline | Slide 2: context | Slide 3: why it matters | Slide 4: audience question"


def visual_brief(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    sport = article.get("sport", "")
    if story_type == "Business / Growth":
        return "Use a clean data carousel with bold numbers and simple context."
    if story_type == "League Expansion":
        return "Use a map, team/logo style graphic, or market comparison carousel."
    if story_type == "Game Preview":
        return "Use a Tonight graphic with matchup, time/network if available, and one key player."
    if story_type == "Game Recap / Result":
        return "Use a quick recap carousel with final result, top performer, and next game."
    if story_type == "Player Feature":
        return "Use an athlete-first reel or carousel with one personal angle."
    if story_type == "Breaking / Transaction":
        return "Use a breaking graphic with source credit and one context slide."
    if story_type == "Opinion / Rankings":
        return "Use a debate-style carousel and ask followers to agree or disagree."
    return f"Use a simple {sport} news card with headline, context, and one engagement question."


def why_it_matters(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    sport = article.get("sport", "")

    if story_type == "Business / Growth":
        return "This helps show the business momentum behind women's sports."
    if story_type == "League Expansion":
        return "Expansion stories show where fan demand and investor confidence are rising."
    if story_type == "Game Recap / Result":
        return f"This is timely {sport} coverage with a result fans may want explained quickly."
    if story_type == "Game Preview":
        return f"This gives followers a reason to watch {sport}."
    if story_type == "Opinion / Rankings":
        return "This can create debate, but it is not urgent news."
    if article.get("editorial_score", "0").isdigit() and int(article.get("editorial_score", "0")) >= 80:
        return "This has strong engagement potential due to timeliness, source strength, or major athlete relevance."
    return "This is a useful update, but it should be weighed against stronger stories."


def instagram_angle(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    sport = article.get("sport", "")
    title = article.get("title", "")

    if story_type == "Business / Growth":
        return "The business of women's sports is not emerging anymore. It is becoming big business."
    if story_type == "League Expansion":
        return "Another sign that women's sports demand is outgrowing the old model."
    if story_type == "Game Recap / Result":
        return f"What happened, who stood out, and why it matters for {sport} fans."
    if story_type == "Game Preview":
        return f"What to watch tonight in {sport}, with one key player and one key matchup."
    if story_type == "Opinion / Rankings":
        return "Use this as a debate starter, not a hard-news post."
    return f"Quick hit: {title}"


def caption_starter(article: Dict[str, str]) -> str:
    title = article.get("title", "")
    story_type = article.get("story_type", "")
    sport = article.get("sport", "")

    if story_type == "Game Preview":
        return f"{sport} watchlist: {title} What are you watching for?"
    if story_type == "Game Recap / Result":
        return f"{title} Here is the quick breakdown and why it matters."
    if story_type == "Business / Growth":
        return f"{title} The growth of women's sports keeps getting harder to ignore."
    if story_type == "League Expansion":
        return f"{title} More teams, more investment, more proof that the demand is real."
    if story_type == "Opinion / Rankings":
        return f"{title} Agree or disagree?"
    return f"{title} What should we cover next?"


def hashtags(sport: str) -> str:
    base = ["#WomensSports", "#HerSportsDaily", "#SportsNews"]
    sport_tags = {
        "WNBA": ["#WNBA", "#WomensBasketball"],
        "NCAA Women's Basketball": ["#NCAAWBB", "#WomensBasketball"],
        "NWSL / Women's Soccer": ["#NWSL", "#USWNT", "#WomensSoccer"],
        "PWHL / Women's Hockey": ["#PWHL", "#WomensHockey"],
        "Tennis": ["#WTA", "#Tennis"],
        "Golf / LPGA": ["#LPGA", "#Golf"],
        "Softball": ["#Softball", "#WCWS"],
        "Volleyball": ["#Volleyball", "#NCAAVB"],
        "Gymnastics": ["#Gymnastics"],
        "Track & Field": ["#TrackAndField"],
        "Rugby": ["#Rugby"],
        "Cricket": ["#Cricket"],
        "Baseball": ["#Baseball", "#WomensBaseball"],
    }
    return " ".join(base + sport_tags.get(sport, []))


def enrich_article(article: Dict[str, str]) -> Dict[str, str]:
    text = combined_text(article)
    sport = classify_sport(text)
    story_type = classify_story_type(text)
    source_tier, source_quality = source_tier_and_quality(article.get("source", ""))
    primary_entity = extract_primary_entity(text)
    cluster_id = topic_signature(text, sport, primary_entity)
    wrong_or_low_fit = is_wrong_or_low_fit(text, sport)
    sensitive = sensitive_flag(text)
    verify = verification_needed(text, source_quality)

    score, score_reason, score_parts = calculate_editorial_score(article, sport, story_type, source_quality)
    if wrong_or_low_fit:
        score = max(0, score - 60)
        score_reason += "; penalties: wrong-sport/low-fit filter"

    article.update({
        "sport": sport,
        "story_type": story_type,
        "source_tier": source_tier,
        "source_quality": str(source_quality),
        "editorial_score": str(score),
        "priority_score": str(max(1, min(10, math.ceil(score / 10)))),
        "score_reason": score_reason,
        "freshness_component": str(score_parts["freshness_component"]),
        "story_value_component": str(score_parts["story_value_component"]),
        "brand_fit_component": str(score_parts["brand_fit_component"]),
        "engagement_component": str(score_parts["engagement_component"]),
        "source_component": str(score_parts["source_component"]),
        "penalty_component": str(score_parts["penalty_component"]),
        "primary_entity": primary_entity,
        "cluster_id": cluster_id,
        "wrong_or_low_fit": "Yes" if wrong_or_low_fit else "No",
        "verification_needed": "Yes" if verify else "No",
        "sensitive": "Yes" if sensitive else "No",
        "time_sensitive": time_sensitive(story_type),
        "content_bucket": content_bucket(story_type, sport, text),
        "content_lane": content_lane(story_type, sport, text),
    })

    decision, decision_reason = base_decision(article)
    article["editorial_decision"] = decision
    article["decision_reason"] = decision_reason
    article["recommended_timing"] = recommended_timing(decision, story_type)
    article["post_format"] = post_format(story_type, score)
    article["hook"] = hook(article)
    article["first_slide"] = first_slide(article)
    article["carousel_outline"] = carousel_outline(article)
    article["instagram_angle"] = instagram_angle(article)
    article["why_it_matters"] = why_it_matters(article)
    article["caption_starter"] = caption_starter(article)
    article["hashtags"] = hashtags(sport)
    article["visual_brief"] = visual_brief(article)

    return article


def dedupe_articles(articles: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    deduped = []

    for article in articles:
        title = article.get("title", "").lower()
        link = article.get("link", "").lower()
        key = re.sub(r"[^a-z0-9]+", "", title)[:140] or link

        if key and key not in seen:
            seen.add(key)
            deduped.append(article)

    return deduped


def assign_cluster_metadata(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    cluster_totals: Dict[str, int] = {}
    for article in articles:
        cluster_id = article.get("cluster_id", "")
        cluster_totals[cluster_id] = cluster_totals.get(cluster_id, 0) + 1

    sorted_articles = sorted(
        articles,
        key=lambda x: (
            x.get("cluster_id", ""),
            int(x.get("editorial_score", "0")),
            int(x.get("source_quality", "0")),
            x.get("published", ""),
        ),
        reverse=True,
    )

    cluster_ranks: Dict[str, int] = {}
    for article in sorted_articles:
        cluster_id = article.get("cluster_id", "")
        cluster_ranks[cluster_id] = cluster_ranks.get(cluster_id, 0) + 1
        rank = cluster_ranks[cluster_id]

        article["cluster_rank"] = str(rank)
        article["related_story_count"] = str(cluster_totals.get(cluster_id, 1))
        article["duplicate_status"] = "Primary" if rank == 1 else "Duplicate / alternate angle"

        # Duplicate stories should not survive the brief unless manually reviewed later.
        if rank > 1 and article.get("editorial_decision") != "Review Before Posting":
            article["editorial_decision"] = "Skip Duplicate"
            article["decision_reason"] = "Another stronger version of this topic already exists."

    return articles


def sort_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return sorted(
        articles,
        key=lambda x: (
            int(x.get("editorial_score", "0")),
            int(x.get("source_quality", "0")),
            x.get("published", ""),
        ),
        reverse=True,
    )


def build_daily_content_brief(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    selected_clusters: set[str] = set()
    selected_entities: set[str] = set()
    source_counts: Dict[str, int] = {}
    sport_counts: Dict[str, int] = {}
    must_post_count = 0

    candidates = sort_articles(articles)

    for article in candidates:
        decision = article.get("editorial_decision", "")
        if decision in {"Skip", "Skip Duplicate"}:
            continue

        score = int(article.get("editorial_score", "0") or 0)
        cluster_id = article.get("cluster_id", "")
        primary_entity = article.get("primary_entity", "")
        source = article.get("source", "")
        sport = article.get("sport", "Women's Sports")

        if cluster_id in selected_clusters:
            continue
        if primary_entity and primary_entity in selected_entities:
            continue
        if source_counts.get(source, 0) >= MAX_PER_SOURCE:
            continue
        if sport_counts.get(sport, 0) >= SPORT_MAXES.get(sport, 2):
            continue

        # Cap Must Post. If the story is still good, downgrade it instead of skipping.
        final_decision = decision
        if final_decision == "Must Post":
            if must_post_count >= MAX_MUST_POST_ITEMS:
                final_decision = "Maybe Post"
            else:
                must_post_count += 1

        rank = len(selected) + 1
        selected.append({
            "rank": str(rank),
            "editorial_decision": final_decision,
            "recommended_timing": recommended_timing(final_decision, article.get("story_type", "")),
            "editorial_score": article.get("editorial_score", ""),
            "priority_score": article.get("priority_score", ""),
            "source_quality": article.get("source_quality", ""),
            "source_tier": article.get("source_tier", ""),
            "time_sensitive": article.get("time_sensitive", ""),
            "verification_needed": article.get("verification_needed", ""),
            "sensitive": article.get("sensitive", ""),
            "duplicate_status": article.get("duplicate_status", ""),
            "related_story_count": article.get("related_story_count", ""),
            "cluster_rank": article.get("cluster_rank", ""),
            "cluster_id": cluster_id,
            "primary_entity": primary_entity,
            "content_lane": article.get("content_lane", ""),
            "content_bucket": article.get("content_bucket", ""),
            "sport": sport,
            "story_type": article.get("story_type", ""),
            "source": source,
            "headline": article.get("title", ""),
            "link": article.get("link", ""),
            "post_format": article.get("post_format", ""),
            "hook": article.get("hook", ""),
            "first_slide": article.get("first_slide", ""),
            "carousel_outline": article.get("carousel_outline", ""),
            "instagram_angle": article.get("instagram_angle", ""),
            "why_it_matters": article.get("why_it_matters", ""),
            "caption_starter": article.get("caption_starter", ""),
            "visual_brief": article.get("visual_brief", ""),
            "hashtags": article.get("hashtags", ""),
            "published": article.get("published", ""),
            "age_hours": article.get("age_hours", ""),
            "decision_reason": article.get("decision_reason", ""),
            "score_reason": article.get("score_reason", ""),
            "notes": "",
        })

        selected_clusters.add(cluster_id)
        if primary_entity:
            selected_entities.add(primary_entity)
        source_counts[source] = source_counts.get(source, 0) + 1
        sport_counts[sport] = sport_counts.get(sport, 0) + 1

        if len(selected) >= MAX_DAILY_BRIEF_ITEMS:
            break

    return selected


def scrape_feeds() -> List[Dict[str, str]]:
    all_articles: List[Dict[str, str]] = []

    for url in FEED_URLS:
        print(f"Fetching feed: {url}")
        articles = parse_feed(url)
        print(f"  Retrieved {len(articles)} articles")
        all_articles.extend(articles)

    enriched = [enrich_article(article) for article in dedupe_articles(all_articles)]
    enriched = assign_cluster_metadata(enriched)
    return sort_articles(enriched)


def save_articles_csv(articles: List[Dict[str, str]], filename: str = OUTPUT_FILE) -> None:
    fieldnames = [
        "editorial_decision",
        "editorial_score",
        "priority_score",
        "source_quality",
        "source_tier",
        "recommended_timing",
        "decision_reason",
        "score_reason",
        "freshness_component",
        "story_value_component",
        "brand_fit_component",
        "engagement_component",
        "source_component",
        "penalty_component",
        "content_bucket",
        "content_lane",
        "sport",
        "story_type",
        "source",
        "title",
        "published",
        "age_hours",
        "link",
        "post_format",
        "hook",
        "first_slide",
        "carousel_outline",
        "instagram_angle",
        "why_it_matters",
        "caption_starter",
        "visual_brief",
        "hashtags",
        "primary_entity",
        "cluster_id",
        "cluster_rank",
        "related_story_count",
        "duplicate_status",
        "verification_needed",
        "sensitive",
        "wrong_or_low_fit",
        "time_sensitive",
        "categories",
        "summary",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            writer.writerow({field: article.get(field, "") for field in fieldnames})

    print(f"Saved {len(articles)} articles to {filename}")


def save_daily_brief_csv(brief_rows: List[Dict[str, str]], filename: str = DAILY_BRIEF_FILE) -> None:
    fieldnames = [
        "rank",
        "editorial_decision",
        "recommended_timing",
        "editorial_score",
        "priority_score",
        "source_quality",
        "source_tier",
        "time_sensitive",
        "verification_needed",
        "sensitive",
        "duplicate_status",
        "related_story_count",
        "cluster_rank",
        "cluster_id",
        "primary_entity",
        "content_lane",
        "content_bucket",
        "sport",
        "story_type",
        "source",
        "headline",
        "link",
        "post_format",
        "hook",
        "first_slide",
        "carousel_outline",
        "instagram_angle",
        "why_it_matters",
        "caption_starter",
        "visual_brief",
        "hashtags",
        "published",
        "age_hours",
        "decision_reason",
        "score_reason",
        "notes",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in brief_rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    print(f"Saved {len(brief_rows)} brief rows to {filename}")


def main() -> None:
    articles = scrape_feeds()
    brief_rows = build_daily_content_brief(articles)

    save_articles_csv(articles)
    save_daily_brief_csv(brief_rows)


if __name__ == "__main__":
    main()
