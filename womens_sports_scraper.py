"""
Her Sports Daily Women's Sports News Scraper v10 Final
-----------------------------------------------

This version rebuilds the editorial decision logic around one core rule:

A story must pass a women's-sports relevance gate before it can be scored.

Output files:
1. womens_sports_articles.csv
   Full scrape with relevance, score, decision, and reasons.

2. daily_content_brief.csv
   A tight editorial shortlist for what Her Sports Daily should consider posting.

v10 polish:
- Fixes story-type classification order.
- Fixes opinion/column false positives like “shatter myth.”
- Adds cricket T20I/ODI detection.
- Keeps decision reasons aligned when Must Post is capped.
- Stops "first round" from triggering Record / Milestone.
- Adds Recruiting / Roster News and Tournament Update story types.
- Makes true Must Post stories possible again, but caps them at 2.
- Keeps the hard women’s-sports relevance gate from v9.
- Keeps duplicate/topic control tight.
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

SPORT_MAXES = {
    "WNBA": 3,
    "NWSL / Women's Soccer": 2,
    "PWHL / Women's Hockey": 2,
    "NCAA Women's Basketball": 2,
    "Softball": 2,
    "Tennis": 2,
    "Golf / LPGA": 2,
    "Volleyball": 2,
    "Women's Sports": 1,
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


WOMENS_SPORTS_SOURCES = [
    "just women's sports", "just womens sports", "women in sport", "women's sports foundation",
    "the gist", "the ix", "swish appeal", "the next", "winsidr", "her hoop stats",
    "equalizer", "the ice garden", "hoopfeed", "togethxr", "shekicks", "girls soccer network"
]


SOURCE_RULES: List[Tuple[str, int, List[str]]] = [
    ("Official League / Governing Body", 10, ["wnba", "nwsl", "pwhl", "ncaa.com", "ussoccer", "u.s. soccer", "us soccer", "uswnt", "lpga", "wta tennis", "fifa", "team usa"]),
    ("Wire / Mainstream", 9, ["associated press", "ap news", "apnews", "reuters", "espn", "cbs sports", "yahoo sports", "usa today", "sports illustrated", "fox sports", "nbc sports", "the athletic"]),
    ("Business", 8, ["sports business journal", "front office sports", "sportspro", "axios", "sportico", "forbes"]),
    ("Specialty Women's Sports", 8, WOMENS_SPORTS_SOURCES),
    ("Advocacy / Foundation", 7, ["women in sport", "women's sports foundation"]),
]


WOMEN_CONTEXT_TERMS = [
    "women", "women's", "womens", "female", "girls", "wnba", "ncaaw", "ncaawbb",
    "nwsl", "uswnt", "pwhl", "wta", "lpga", "softball", "wcws", "volleyball",
    "gymnastics", "women's open", "women’s open", "women's college world series",
    "women’s college world series", "women's pro baseball", "wpbl"
]


MEN_CONTEXT_TERMS = [
    "men's", "mens", "nba", "nfl", "nhl", "mlb", "ufc", "wwe", "nascar",
    "formula 1", "premier league", "la liga", "bundesliga", "serie a",
]


MALE_ATHLETES = [
    "matteo arnaldi", "carlos alcaraz", "jannik sinner", "novak djokovic",
    "alexander zverev", "taylor fritz", "ben shelton", "rafael nadal",
    "roger federer", "lebron james", "stephen curry", "shohei ohtani",
]


FEMALE_ATHLETES = [
    "caitlin clark", "angel reese", "paige bueckers", "juju watkins", "aja wilson", "a'ja wilson",
    "sabrina ionescu", "breanna stewart", "napheesa collier", "diana taurasi", "kelsey plum",
    "cameron brink", "aliyah boston", "rhyne howard", "trinity rodman", "sophia smith",
    "alex morgan", "coco gauff", "naomi osaka", "serena williams", "venus williams",
    "victoria mboko", "amanda anisimova", "iga swiatek", "aryna sabalenka", "mirra andreeva",
    "madison keys", "jessica pegula", "ellyse perry", "simone biles", "suni lee",
    "nelly korda", "rose zhang", "jennifer kupcho", "lexi thompson", "sha'carri richardson",
    "sydney mclaughlin", "gabby thomas", "katie ledecky", "ilona maher", "reese atwood",
    "dawn staley", "kim mulkey", "geno auriemma",
]


SPORT_RULES: List[Tuple[str, List[str]]] = [
    ("WNBA", [
        "wnba", "indiana fever", "chicago sky", "las vegas aces", "new york liberty",
        "minnesota lynx", "seattle storm", "phoenix mercury", "atlanta dream",
        "washington mystics", "los angeles sparks", "dallas wings", "connecticut sun",
        "golden state valkyries", "portland fire", "toronto tempo", "a'ja wilson",
        "aja wilson", "caitlin clark", "angel reese", "paige bueckers", "kelsey mitchell",
    ]),
    ("NCAA Women's Basketball", [
        "ncaaw", "ncaawbb", "women's basketball", "women’s basketball",
        "college women's basketball", "college women’s basketball", "uconn women",
        "south carolina women", "south carolina women's basketball", "gamecocks women's basketball",
        "dawn staley", "usc women", "lsu women", "juju watkins",
    ]),
    ("NWSL / Women's Soccer", [
        "nwsl", "uswnt", "women's soccer", "women’s soccer", "women's football",
        "women’s football", "gotham fc", "angel city", "portland thorns",
        "washington spirit", "san diego wave", "kansas city current", "orlando pride",
        "north carolina courage", "boston legacy", "denver summit", "lionesses",
        "trinity rodman", "sophia smith", "alex morgan",
    ]),
    ("PWHL / Women's Hockey", [
        "pwhl", "women's hockey", "women’s hockey", "boston fleet", "minnesota frost",
        "new york sirens", "ottawa charge", "montréal victoire", "montreal victoire",
        "toronto sceptres", "seattle torrent", "vancouver goldeneyes",
    ]),
    ("Golf / LPGA", [
        "lpga", "women's open", "women’s open", "us women's open", "u.s. women's open",
        "u.s. women’s open", "nelly korda", "rose zhang", "jennifer kupcho", "lexi thompson",
    ]),
    ("Tennis", [
        "wta", "women's tennis", "women’s tennis", "serena williams", "venus williams",
        "coco gauff", "naomi osaka", "iga swiatek", "swiatek", "sabalenka",
        "victoria mboko", "amanda anisimova", "madison keys", "jessica pegula",
    ]),
    ("Softball", ["softball", "wcws", "women's college world series", "women’s college world series"]),
    ("Volleyball", ["volleyball", "lovb", "major league volleyball", "mlv", "pro volleyball", "nebraska volleyball"]),
    ("Gymnastics", ["gymnastics", "simone biles", "suni lee"]),
    ("Track & Field", ["track and field", "athletics", "sha'carri", "sydney mclaughlin", "gabby thomas"]),
    ("Rugby", ["women's rugby", "women’s rugby", "ilona maher"]),
    ("Cricket", ["women's cricket", "women’s cricket", "women's t20", "women’s t20", "t20i", "odi", "england women", "india women", "australia women"]),
    ("Baseball", ["women's baseball", "women’s baseball", "women's pro baseball", "wpbl"]),
]


TEAM_TOPIC_ENTITIES = [
    "indiana fever", "chicago sky", "las vegas aces", "new york liberty", "minnesota lynx",
    "seattle storm", "phoenix mercury", "atlanta dream", "washington mystics", "los angeles sparks",
    "dallas wings", "connecticut sun", "golden state valkyries", "portland fire", "toronto tempo",
    "gotham fc", "angel city", "portland thorns", "washington spirit", "san diego wave",
    "kansas city current", "orlando pride", "north carolina courage", "boston legacy",
    "denver summit", "uswnt", "texas softball", "oklahoma softball", "college world series",
    "women's college world series", "wcws", "pwhl", "unrivaled", "project b",
    "major league volleyball", "wpbl", "wimbledon", "french open", "roland garros",
    "us women's open", "u.s. women's open",
]


SOFT_VIRAL_TERMS = [
    "heartwarming", "sweet moment", "share moment", "shares moment", "viral moment",
    "reacts", "reaction", "outfit", "fashion", "boyfriend", "girlfriend", "fiancé",
    "fiance", "social media reacts", "fans react", "photo", "photos", "instagram post",
    "tiktok", "celebrates with", "message to",
]


RUMOR_TERMS = [
    "rumor", "rumors", "reportedly", "sources", "could", "might", "linked to",
    "trade speculation", "likely to be targeted", "expected to", "potential", "may",
]


OPINION_TERMS = [
    "power rankings", "ranking", "rankings", "way-too-early", "mock draft",
    "predictions", "odds", "takeaways", "winners and losers", "domino effects",
    "watch list", "mvp favorite", "best", "top 10", "top five", "talking points",
    "everything you need to know", "opinion", "column", "myth",
]


RECRUITING_ROSTER_TERMS = [
    "recruit", "recruits", "recruiting", "commit", "commits", "commitment",
    "lands", "land star", "transfer", "transfer portal", "portal", "roster",
    "signing class", "adds", "adds star", "verbal commit", "five-star",
    "4-star", "5-star",
]


TOURNAMENT_UPDATE_TERMS = [
    "first round", "first-round", "1st round", "opening round", "second round",
    "third round", "semifinal", "quarterfinal", "round of 16", "lead after",
    "takes lead", "holds lead", "trails", "struggles", "advances", "moves on",
]


GAME_PREVIEW_TERMS = [
    "preview", "faces", "face", "matchup", "schedule", "where to watch",
    "tonight", "tomorrow", "heads to", "head to", "friendly", "friendlies",
    "will face", "set to face", "prepares for", "opens against", "takes on",
]


TRUE_MILESTONE_TERMS = [
    "record", "new record", "sets record", "breaks record", "shatters",
    "shatter", "historic", "milestone", "first ever", "first-ever",
    "first time", "all-time", "youngest", "oldest", "most ever",
    "career high", "franchise record",
]


SENSITIVE_TERMS = [
    "abuse", "assault", "harassment", "lawsuit", "investigation", "arrest", "death",
    "died", "killed", "violence", "scandal", "allegation", "allegations",
]


HIGH_VALUE_TERMS = [
    "record", "historic", "first", "shatter", "shatters", "breaks", "milestone",
    "championship", "title", "wins", "defeats", "beats", "claims", "captures",
    "expansion", "media rights", "investment", "sponsorship", "viewership",
    "attendance", "sold out", "launch", "new league",
]


RESULT_TERMS = [
    "wins", "win over", "defeats", "beats", "tops", "claims title", "captures title",
    "wins championship", "won championship", "championship win", "final score",
    "score", "title defense",
]


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "over", "after",
    "before", "about", "what", "why", "how", "when", "where", "women", "womens",
    "woman", "sports", "sport", "news", "new", "latest", "watch", "live",
    "highlights", "full", "today", "game", "games", "season", "team", "teams",
    "player", "players", "says", "said", "more", "than", "will", "would",
    "could", "their", "they", "them", "have", "has", "been", "best", "top",
    "first", "second", "third",
}


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize(value: str) -> str:
    value = clean_text(value).lower()
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    return value


def phrase_in_text(phrase: str, text: str) -> bool:
    phrase = normalize(phrase)
    text = normalize(text)

    # Phrase matching with boundaries so "sun" does not match "Sunday".
    if len(phrase.split()) == 1:
        return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None

    return phrase in text


def any_phrase(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase_in_text(phrase, text) for phrase in phrases)


def count_phrases(text: str, phrases: Iterable[str]) -> int:
    return sum(1 for phrase in phrases if phrase_in_text(phrase, text))


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


def parse_date(raw_date: str) -> Tuple[str, Optional[datetime], str]:
    raw_date = clean_text(raw_date)
    if not raw_date:
        return "", None, ""

    try:
        parsed = parsedate_to_datetime(raw_date)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        hours = max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds() / 3600)
        return parsed.isoformat(), parsed, f"{hours:.1f}"
    except Exception:
        return raw_date, None, ""


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

            published_iso, published_dt, article_age_hours = parse_date(item.findtext("pubDate", default=""))
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
                "age_hours": article_age_hours,
                "categories": categories,
                "summary": summary,
            })

        return articles

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    source_title = clean_text(root.findtext("atom:title", default=url, namespaces=ns))

    for entry in entries:
        date_raw = (
            entry.findtext("atom:published", default="", namespaces=ns)
            or entry.findtext("atom:updated", default="", namespaces=ns)
        )
        published_iso, published_dt, article_age_hours = parse_date(date_raw)
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
            "age_hours": article_age_hours,
            "categories": "",
            "summary": summary,
        })

    return articles


def combined_text(article: Dict[str, str]) -> str:
    return normalize(" ".join([
        article.get("title", ""),
        article.get("summary", ""),
        article.get("categories", ""),
        article.get("source", ""),
    ]))


def source_tier_and_quality(source: str) -> Tuple[str, int]:
    source_text = normalize(source)

    for tier, quality, keywords in SOURCE_RULES:
        if any_phrase(source_text, keywords):
            return tier, quality

    if "google news" in source_text:
        return "Aggregator", 4

    return "Other", 6


def classify_sport(text: str) -> str:
    # Order matters. Golf before WNBA prevents "US Women's Open" type stories from being pulled into a basketball bucket.
    for sport, keywords in SPORT_RULES:
        if any_phrase(text, keywords):
            return sport
    return "Women's Sports"


def womens_relevance_gate(text: str, source: str, sport: str) -> Tuple[bool, str]:
    source_text = normalize(source)
    has_women_source = any_phrase(source_text, WOMENS_SPORTS_SOURCES)
    has_women_context = any_phrase(text, WOMEN_CONTEXT_TERMS) or has_women_source
    has_female_athlete = any_phrase(text, FEMALE_ATHLETES)
    has_male_athlete = any_phrase(text, MALE_ATHLETES)
    has_male_context = any_phrase(text, MEN_CONTEXT_TERMS) or has_male_athlete or re.search(r"\bhis\b", text) is not None

    if "baseball" in text and "softball" not in text and not any_phrase(text, ["women's baseball", "women's pro baseball", "wpbl"]):
        return False, "Blocked: baseball story without women's baseball/WPBL context."

    if has_male_context and not (has_women_context or has_female_athlete):
        return False, "Blocked: likely men's sports story with no women's context."

    if sport in {"Tennis", "Golf / LPGA"} and not (has_women_context or has_female_athlete):
        return False, f"Blocked: {sport} story without WTA/LPGA, women's event, or known female athlete context."

    if sport == "Women's Sports" and not (has_women_context or has_female_athlete):
        return False, "Blocked: no clear women's sports signal."

    if has_women_context or has_female_athlete or sport in {"WNBA", "NWSL / Women's Soccer", "PWHL / Women's Hockey", "NCAA Women's Basketball"}:
        return True, "Passed: clear women's sports signal."

    return False, "Blocked: insufficient relevance."


def extract_primary_entity(text: str) -> str:
    for name in FEMALE_ATHLETES:
        if phrase_in_text(name, text):
            return name.title()

    for entity in TEAM_TOPIC_ENTITIES:
        if phrase_in_text(entity, text):
            return entity.title()

    return ""


def topic_signature(text: str, sport: str, primary_entity: str) -> str:
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
    if "us women's open" in text or "u.s. women's open" in text or "women's open" in text:
        return "golf::us_womens_open"

    if primary_entity:
        return f"{sport.lower()}::{primary_entity.lower()}"

    words = re.findall(r"[a-zA-Z0-9']+", text)
    important = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    return f"{sport.lower()}::" + "_".join(important[:8])



def has_true_milestone_signal(text: str) -> bool:
    # Do not let routine tournament phrasing like "first round" become a milestone.
    if any_phrase(text, ["first round", "first-round", "1st round", "opening round"]):
        if not any_phrase(text, ["record", "historic", "milestone", "first ever", "first-ever", "all-time"]):
            return False

    return any_phrase(text, TRUE_MILESTONE_TERMS)


def classify_story_type(text: str) -> str:
    if any_phrase(text, SOFT_VIRAL_TERMS):
        return "Soft Viral / Social"
    if any_phrase(text, RUMOR_TERMS):
        return "Rumor / Needs Verification"
    if any_phrase(text, OPINION_TERMS):
        return "Opinion / Analysis"

    # Order matters. Preview/tournament/recruiting must be checked before broad milestone words.
    if any_phrase(text, GAME_PREVIEW_TERMS):
        return "Game Preview"
    if any_phrase(text, RECRUITING_ROSTER_TERMS):
        return "Recruiting / Roster News"
    if any_phrase(text, TOURNAMENT_UPDATE_TERMS):
        return "Tournament Update"
    if any_phrase(text, RESULT_TERMS):
        return "Game Recap / Result"

    # Business/money terms should beat record words like "record-breaking purse".
    if any_phrase(text, ["revenue", "media rights", "sponsorship", "valuation", "investment", "ratings", "viewership", "attendance", "purse", "prize money", "funding"]):
        return "Business / Growth"
    if has_true_milestone_signal(text):
        return "Record / Milestone"
    if any_phrase(text, ["expansion", "new team", "franchise", "launch", "debut", "inaugural"]):
        return "League Expansion"
    if any_phrase(text, ["announces", "announced", "signs", "signed", "traded", "trade", "draft", "hires", "fired"]):
        return "Breaking / Transaction"
    if any_phrase(text, ["profile", "story", "journey", "feature", "legacy", "comeback"]):
        return "Player Feature"
    if any_phrase(text, ["equal pay", "gender", "barrier", "trailblazer", "activism", "charity", "foundation", "women in sport"]):
        return "Culture / Advocacy"
    if any_phrase(text, ["injury", "injured", "questionable", "out", "return", "availability"]):
        return "Injury / Availability"
    return "General News"

def freshness_component(article: Dict[str, str], story_type: str) -> Tuple[int, str]:
    raw = article.get("age_hours", "")
    if not raw:
        return 5, "No parsed date."

    try:
        hours = float(raw)
    except ValueError:
        return 5, "No parsed date."

    fast_decay = {"Game Recap / Result", "Game Preview", "Breaking / Transaction", "Injury / Availability", "Rumor / Needs Verification", "Tournament Update", "Recruiting / Roster News"}

    if story_type in fast_decay:
        if hours <= 6:
            return 15, "Fresh under 6 hours."
        if hours <= 12:
            return 12, "Fresh under 12 hours."
        if hours <= 24:
            return 8, "Fresh under 24 hours."
        if hours <= 48:
            return 2, "Aging under 48 hours."
        return -25, "Expired for daily coverage."

    if hours <= 12:
        return 12, "Fresh under 12 hours."
    if hours <= 24:
        return 10, "Fresh under 24 hours."
    if hours <= 72:
        return 7, "Recent under 72 hours."
    if hours <= 168:
        return 3, "Still usable this week."
    return -15, "Too old."


def story_value_component(text: str, story_type: str) -> Tuple[int, str]:
    if story_type == "Record / Milestone":
        return 35, "Record or milestone."
    if story_type == "Business / Growth":
        return 30, "Business/growth story."
    if story_type == "League Expansion":
        return 30, "Expansion story."
    if story_type == "Game Recap / Result":
        if any_phrase(text, ["championship", "title", "final", "commissioner's cup", "national championship"]):
            return 40, "Championship or major result."
        return 24, "Game result."
    if story_type == "Breaking / Transaction":
        return 26, "Confirmed breaking or transaction story."
    if story_type == "Recruiting / Roster News":
        return 22, "Recruiting or roster-building story."
    if story_type == "Tournament Update":
        return 18, "Tournament update."
    if story_type == "Game Preview":
        return 18, "Preview story."
    if story_type == "Player Feature":
        return 14, "Feature story."
    if story_type == "Culture / Advocacy":
        return 14, "Culture/impact story."
    if story_type == "Injury / Availability":
        return 14, "Availability story."
    if story_type == "Opinion / Analysis":
        return 8, "Opinion/analysis story."
    if story_type == "Soft Viral / Social":
        return 4, "Soft viral/social item."
    if story_type == "Rumor / Needs Verification":
        return 3, "Rumor/speculation story."
    return 10, "General update."

def brand_component(sport: str) -> Tuple[int, str]:
    if sport in {"WNBA", "NWSL / Women's Soccer", "PWHL / Women's Hockey", "NCAA Women's Basketball"}:
        return 14, f"Core brand sport: {sport}."
    if sport in {"Softball", "Volleyball", "Tennis", "Golf / LPGA", "Gymnastics", "Track & Field"}:
        return 10, f"Strong secondary sport: {sport}."
    if sport in {"Rugby", "Cricket", "Baseball"}:
        return 7, f"Niche growth sport: {sport}."
    return 5, "General women's sports fit."


def engagement_component(text: str) -> Tuple[int, str]:
    score = 0
    reasons = []

    if any_phrase(text, FEMALE_ATHLETES):
        score += 6
        reasons.append("major athlete")

    high_value_matches = count_phrases(text, HIGH_VALUE_TERMS)
    if high_value_matches:
        score += min(5, high_value_matches * 2)
        reasons.append("high-interest keyword")

    return min(score, 10), ", ".join(reasons) if reasons else "normal interest"


def penalty_component(text: str, source_quality: int, story_type: str, eligibility_passed: bool, freshness_reason: str) -> Tuple[int, str]:
    penalty = 0
    reasons = []

    if not eligibility_passed:
        penalty -= 100
        reasons.append("failed relevance gate")
    if story_type == "Soft Viral / Social":
        penalty -= 28
        reasons.append("soft viral/social penalty")
    if story_type == "Rumor / Needs Verification":
        penalty -= 30
        reasons.append("rumor/speculation penalty")
    if story_type == "Opinion / Analysis":
        penalty -= 16
        reasons.append("opinion/analysis penalty")
    if any_phrase(text, SENSITIVE_TERMS):
        penalty -= 35
        reasons.append("sensitive topic penalty")
    if source_quality <= 5:
        penalty -= 8
        reasons.append("low source quality penalty")
    if "Expired" in freshness_reason or "Too old" in freshness_reason:
        penalty -= 20
        reasons.append("staleness penalty")

    return penalty, ", ".join(reasons) if reasons else "no major penalties"


def calculate_score(article: Dict[str, str], sport: str, story_type: str, source_quality: int, eligibility_passed: bool) -> Tuple[int, Dict[str, int], str]:
    text = combined_text(article)
    fresh_score, fresh_reason = freshness_component(article, story_type)
    value_score, value_reason = story_value_component(text, story_type)
    brand_score, brand_reason = brand_component(sport)
    engagement_score, engagement_reason = engagement_component(text)
    source_score = int(round(source_quality * 1.3))
    penalty_score, penalty_reason = penalty_component(text, source_quality, story_type, eligibility_passed, fresh_reason)

    total = fresh_score + value_score + brand_score + engagement_score + source_score + penalty_score
    total = max(0, min(100, total))

    parts = {
        "freshness_component": fresh_score,
        "story_value_component": value_score,
        "brand_fit_component": brand_score,
        "engagement_component": engagement_score,
        "source_component": source_score,
        "penalty_component": penalty_score,
    }

    score_reason = (
        f"{value_reason} {fresh_reason} {brand_reason} "
        f"Source quality {source_quality}/10. Engagement: {engagement_reason}. Penalties: {penalty_reason}."
    )

    return total, parts, score_reason


def verification_needed(text: str, source_quality: int, story_type: str) -> bool:
    if story_type == "Rumor / Needs Verification":
        return True
    if source_quality < 8 and story_type in {"Breaking / Transaction", "Game Recap / Result", "Record / Milestone"}:
        return True
    return False


def sensitive_flag(text: str) -> bool:
    return any_phrase(text, SENSITIVE_TERMS)


def editorial_decision(article: Dict[str, str]) -> Tuple[str, str]:
    score = int(article.get("editorial_score", "0") or 0)
    source_quality = int(article.get("source_quality", "0") or 0)
    story_type = article.get("story_type", "")

    if article.get("eligibility_passed") != "Yes":
        return "Skip", article.get("eligibility_reason", "Failed relevance gate.")
    if article.get("sensitive") == "Yes":
        return "Review Before Posting", "Sensitive topic requires manual review."
    if story_type == "Soft Viral / Social":
        if score >= 65 and source_quality >= 8:
            return "Save for Weekend", "Soft social item. Only use as filler."
        return "Skip", "Soft social item is not strong enough for daily brief."
    if story_type == "Rumor / Needs Verification":
        if score >= 72:
            return "Verify First", "Speculative story. Verify with stronger source before posting."
        return "Skip", "Speculative story is too weak."
    if story_type == "Opinion / Analysis":
        if score >= 78:
            return "Maybe Post", "Strong analysis/debate candidate, but not urgent news."
        if score >= 58:
            return "Save for Weekend", "Useful debate/filler item."
        return "Skip", "Opinion item below threshold."
    if article.get("verification_needed") == "Yes":
        if score >= 72:
            return "Verify First", "Needs stronger confirmation before posting."
        return "Skip", "Needs verification and score is not high enough."

    must_post_types = {
        "Record / Milestone",
        "Business / Growth",
        "League Expansion",
        "Breaking / Transaction",
        "Game Recap / Result",
    }

    if score >= 76 and source_quality >= 8 and story_type in must_post_types:
        return "Must Post", "High-score, timely, verified hard-news story."
    if score >= 68:
        return "Maybe Post", "Strong candidate, but not mandatory."
    if score >= 54:
        return "Save for Weekend", "Useful but not urgent."
    return "Skip", "Below daily brief threshold."

def time_sensitive(story_type: str) -> str:
    if story_type in {"Breaking / Transaction", "Game Preview", "Game Recap / Result", "Injury / Availability", "Rumor / Needs Verification", "Tournament Update", "Recruiting / Roster News"}:
        return "Yes"
    return "No"


def content_bucket(story_type: str, sport: str, text: str) -> str:
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the Game"
    if story_type in {"Game Recap / Result", "Game Preview", "Tournament Update"}:
        return "Tonight / Game Coverage"
    if story_type == "Recruiting / Roster News":
        return "Roster / Recruiting"
    if any_phrase(text, FEMALE_ATHLETES):
        return "Star Watch"
    if story_type in {"Culture / Advocacy", "Player Feature"}:
        return "Culture & Impact"
    if sport in {"NCAA Women's Basketball", "Softball", "Volleyball"}:
        return "College Spotlight"
    if story_type == "Soft Viral / Social":
        return "Social Filler"
    return "Daily News"


def content_lane(story_type: str, sport: str, text: str) -> str:
    if story_type == "Soft Viral / Social":
        return "Soft social filler"
    if any_phrase(text, FEMALE_ATHLETES):
        return "Star-driven engagement"
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the game"
    if story_type in {"Game Preview", "Game Recap / Result", "Tournament Update"}:
        return "Game coverage"
    if story_type == "Recruiting / Roster News":
        return "Roster/recruiting"
    if sport in {"NCAA Women's Basketball", "Softball", "Volleyball"}:
        return "College spotlight"
    return "Daily news"


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
    if story_type in {"Business / Growth", "League Expansion", "Player Feature", "Recruiting / Roster News"}:
        return "Post during daytime engagement window"
    if story_type == "Tournament Update":
        return "Post if the tournament story is still developing"
    if decision == "Save for Weekend":
        return "Save for weekend or filler slot"
    return "Use when convenient"


def post_format(story_type: str, score: int) -> str:
    if story_type in {"Breaking / Transaction", "Game Recap / Result", "Record / Milestone"} and score >= 76:
        return "Breaking graphic + carousel"
    if story_type == "Business / Growth":
        return "Data carousel"
    if story_type == "League Expansion":
        return "Map/expansion carousel"
    if story_type == "Game Preview":
        return "Tonight graphic"
    if story_type == "Tournament Update":
        return "Tournament update card"
    if story_type == "Recruiting / Roster News":
        return "Roster/recruiting graphic"
    if story_type == "Player Feature":
        return "Reel or story feature"
    if story_type == "Opinion / Analysis":
        return "Debate carousel"
    if story_type == "Soft Viral / Social":
        return "Stories only"
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
    if story_type == "Record / Milestone":
        return "This is the kind of milestone that shows where the game is headed."
    if story_type == "Recruiting / Roster News":
        return "The next wave of talent is already changing the future."
    if story_type == "Tournament Update":
        return "Here is where things stand in the tournament."
    if story_type == "Opinion / Analysis":
        return "Agree or disagree with this one?"
    if story_type == "Soft Viral / Social":
        return "A lighter moment for the feed."
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
    if story_type == "Record / Milestone":
        return f"Milestone watch: {title}"
    if story_type == "Recruiting / Roster News":
        return f"Roster watch: {title}"
    if story_type == "Tournament Update":
        return f"Tournament update: {title}"
    if story_type == "Opinion / Analysis":
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
    if story_type == "Record / Milestone":
        return "Slide 1: milestone | Slide 2: context | Slide 3: why it matters | Slide 4: what comes next"
    if story_type == "Recruiting / Roster News":
        return "Slide 1: roster/recruiting news | Slide 2: who is involved | Slide 3: why it matters | Slide 4: what comes next"
    if story_type == "Tournament Update":
        return "Slide 1: tournament headline | Slide 2: current standings/result | Slide 3: player/team to watch | Slide 4: what comes next"
    if story_type == "Opinion / Analysis":
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
    if story_type == "Record / Milestone":
        return "Use a milestone carousel with the record, context, and why it matters."
    if story_type == "Recruiting / Roster News":
        return "Use a roster/recruiting graphic with the player, school/team, and why it matters."
    if story_type == "Tournament Update":
        return "Use a tournament update card with current position, key player, and next round."
    if story_type == "Opinion / Analysis":
        return "Use a debate-style carousel and ask followers to agree or disagree."
    if story_type == "Soft Viral / Social":
        return "Use only as a Story or low-effort filler. Do not make it a main feed post."
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
    if story_type == "Record / Milestone":
        return "Records and milestones are proof points for the rise of women's sports."
    if story_type == "Recruiting / Roster News":
        return "Recruiting and roster stories show where the next wave of stars is coming from."
    if story_type == "Tournament Update":
        return "Tournament updates help followers keep track of the biggest ongoing events."
    if story_type == "Opinion / Analysis":
        return "This can create debate, but it is not urgent news."
    if story_type == "Soft Viral / Social":
        return "This is a lighter engagement item, not a core news story."
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
    if story_type == "Record / Milestone":
        return "A milestone worth putting into context."
    if story_type == "Recruiting / Roster News":
        return "A future-star angle with a clear roster-building hook."
    if story_type == "Tournament Update":
        return "A clean update on where the tournament stands right now."
    if story_type == "Soft Viral / Social":
        return "Light engagement only, best for Stories."
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
    if story_type == "Recruiting / Roster News":
        return f"{title} How big is this move for the program?"
    if story_type == "Tournament Update":
        return f"{title} Who are you watching next?"
    if story_type == "Opinion / Analysis":
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
    source = article.get("source", "")
    source_tier, source_quality = source_tier_and_quality(source)
    sport = classify_sport(text)
    eligibility_passed, eligibility_reason = womens_relevance_gate(text, source, sport)
    story_type = classify_story_type(text)
    primary_entity = extract_primary_entity(text)
    cluster_id = topic_signature(text, sport, primary_entity)
    sensitive = any_phrase(text, SENSITIVE_TERMS)
    verify = verification_needed(text, source_quality, story_type)

    score, score_parts, score_reason = calculate_score(article, sport, story_type, source_quality, eligibility_passed)

    article.update({
        "sport": sport,
        "story_type": story_type,
        "source_tier": source_tier,
        "source_quality": str(source_quality),
        "eligibility_passed": "Yes" if eligibility_passed else "No",
        "eligibility_reason": eligibility_reason,
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
        "verification_needed": "Yes" if verify else "No",
        "sensitive": "Yes" if sensitive else "No",
        "time_sensitive": time_sensitive(story_type),
        "content_bucket": content_bucket(story_type, sport, text),
        "content_lane": content_lane(story_type, sport, text),
    })

    decision, decision_reason = editorial_decision(article)
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
        title = normalize(article.get("title", ""))
        link = normalize(article.get("link", ""))
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

        if rank > 1 and article.get("editorial_decision") not in {"Review Before Posting", "Skip"}:
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
        if sport_counts.get(sport, 0) >= SPORT_MAXES.get(sport, 1):
            continue

        final_decision = decision
        final_decision_reason = article.get("decision_reason", "")
        if final_decision == "Must Post":
            if must_post_count >= MAX_MUST_POST_ITEMS:
                final_decision = "Maybe Post"
                final_decision_reason = "Downgraded from Must Post because the daily Must Post cap was reached."
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
            "eligibility_passed": article.get("eligibility_passed", ""),
            "eligibility_reason": article.get("eligibility_reason", ""),
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
            "decision_reason": final_decision_reason,
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
        "eligibility_passed",
        "eligibility_reason",
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
        "eligibility_passed",
        "eligibility_reason",
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
