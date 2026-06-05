"""
Her Sports Daily Women's Sports News Scraper v6
-----------------------------------------------

Creates two CSV files:

1. womens_sports_articles.csv
   Full scraped article database.

2. daily_content_brief.csv
   A filtered, ranked posting brief with duplicate topic control, source quality
   scoring, story clustering, and max story limits per athlete/topic.

This version makes the brief less aggressive by:
- capping Must Post items
- excluding likely men's sports stories
- using stricter source quality scoring
- allowing only one daily brief item per repeated topic/entity
- demoting rumors and low-verification stories
"""

from __future__ import annotations

import csv
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Dict, Iterable, List, Tuple


OUTPUT_FILE = "womens_sports_articles.csv"
DAILY_BRIEF_FILE = "daily_content_brief.csv"
MAX_DAILY_BRIEF_ITEMS = 15
MAX_MUST_POST_ITEMS = 5
MAX_PER_CLUSTER = 1
MAX_PER_PRIMARY_ENTITY = 1
MAX_PER_SPORT = 4
MAX_PER_SOURCE = 3


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
    ("Tennis", ["tennis", "wta", "wimbledon", "us open", "french open", "australian open", "coco gauff", "naomi osaka", "swiatek", "sabalenka", "serena", "venus"]),
    ("Golf / LPGA", ["lpga", "women's open", "u.s. women's open", "us women's open", "golf", "nelly korda", "lexi thompson", "rose zhang", "kupcho", "lydia ko", "hannah green", "minjee lee", "jennifer kupcho"]),
    ("Softball", ["softball", "college world series", "wcws"]),
    ("Volleyball", ["volleyball", "lovb", "major league volleyball", "mlv", "pro volleyball", "nebraska volleyball"]),
    ("Gymnastics", ["gymnastics", "simone biles", "suni lee", "olympic gymnastics"]),
    ("Track & Field", ["track", "athletics", "sprint", "sha'carri", "sydney mclaughlin", "gabby thomas"]),
    ("Rugby", ["rugby", "women's rugby"]),
    ("Cricket", ["cricket", "t20", "women's world cup"]),
    ("Baseball", ["women's baseball", "women's pro baseball", "wpbl"]),
]


STORY_TYPE_RULES: List[Tuple[str, List[str]]] = [
    ("Breaking News", ["breaking", "announces", "announced", "reportedly", "signs", "signed", "traded", "trade", "draft", "hires", "fired"]),
    ("Game Recap", ["defeats", "beats", "tops", "leads", "wins", "loss", "score", "opener", "final", "semifinal", "championship"]),
    ("Game Preview", ["preview", "faces", "matchup", "schedule", "where to watch", "odds", "tonight", "tomorrow"]),
    ("Business / Growth", ["revenue", "media rights", "sponsorship", "valuation", "investment", "ratings", "viewership", "attendance", "ticket", "expansion"]),
    ("League Expansion", ["expansion", "new team", "franchise", "launch", "debut", "inaugural"]),
    ("Player Profile", ["profile", "story", "journey", "feature", "legacy", "returns", "comeback"]),
    ("Awards / Rankings", ["award", "honor", "ranking", "ranked", "player of the week", "mvp", "all-star"]),
    ("Injury / Availability", ["injury", "injured", "questionable", "out", "return", "availability"]),
    ("Culture / Advocacy", ["equal pay", "gender", "barrier", "trailblazer", "activism", "charity", "foundation", "women in sport"]),
]


BIG_ENGAGEMENT_NAMES = [
    "caitlin clark", "angel reese", "paige bueckers", "juju watkins", "aja wilson", "a'ja wilson",
    "sabrina ionescu", "breanna stewart", "napheesa collier", "diana taurasi", "kelsey plum",
    "cameron brink", "aliyah boston", "rhyne howard", "trinity rodman", "sophia smith",
    "alex morgan", "coco gauff", "naomi osaka", "serena williams", "venus williams",
    "simone biles", "suni lee", "nelly korda", "rose zhang", "sha'carri richardson",
    "sydney mclaughlin", "katie ledecky", "ilona maher",
]


TEAM_AND_TOPIC_ENTITIES = [
    # WNBA
    "indiana fever", "chicago sky", "las vegas aces", "new york liberty", "minnesota lynx",
    "seattle storm", "phoenix mercury", "atlanta dream", "washington mystics", "los angeles sparks",
    "dallas wings", "connecticut sun", "golden state valkyries", "portland fire", "toronto tempo",
    # NWSL
    "gotham fc", "angel city", "portland thorns", "washington spirit", "san diego wave",
    "kansas city current", "orlando pride", "north carolina courage", "houston dash",
    "boston legacy", "denver summit", "utah royals", "seattle reign", "bay fc",
    # Other leagues and topics
    "pwhl", "unrivaled", "project b", "major league volleyball", "women's pro baseball league",
    "wpbl", "uswnt", "world cup", "college world series", "wimbledon", "french open",
]


HIGH_INTENT_KEYWORDS = [
    "record", "historic", "first", "breaks", "milestone", "championship", "title",
    "wins", "upset", "rivalry", "sold out", "attendance", "viewership", "media rights",
    "expansion", "launch", "new league", "contract", "salary", "injury", "returns",
]


NEGATIVE_OR_SENSITIVE_KEYWORDS = [
    "abuse", "assault", "harassment", "lawsuit", "investigation", "arrest", "death",
    "died", "killed", "violence", "scandal",
]


RUMOR_WORDS = ["rumor", "rumors", "reportedly", "sources", "could", "might", "trade speculation", "linked to"]

LIKELY_MENS_STORY_KEYWORDS = [
    "men's", "mens ", "men’s", "men's golf", "men’s golf", "men's basketball", "men’s basketball",
    "men's soccer", "men’s soccer", "men's tennis", "men’s tennis", "boys "
]


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "over", "after", "before",
    "about", "what", "why", "how", "when", "where", "women", "womens", "woman", "sports",
    "sport", "news", "new", "latest", "watch", "live", "highlights", "full", "today",
    "game", "games", "season", "team", "teams", "player", "players", "says", "said",
    "more", "than", "will", "would", "could", "their", "they", "them", "have", "has",
    "been", "best", "top", "after", "before", "during", "around", "against", "again"
}


SOURCE_TIERS = [
    ("Official", 10, ["wnba.com", "nwslsoccer", "thepwhl", "ncaa.com", "us soccer", "ussoccer", "lpga", "wta tennis", "wtatennis", "fifa"]),
    ("Wire / Mainstream", 9, ["associated press", "ap news", "apnews", "reuters", "espn", "cbs sports", "yahoo sports", "usa today", "sports illustrated", "fox sports", "nbc"]),
    ("Business", 8, ["sports business journal", "front office sports", "sportspro", "axios", "sportico", "forbes"]),
    ("Specialty Women's Sports", 8, ["just women", "the gist", "the ix", "swish appeal", "the next", "winsidr", "her hoop stats", "equalizer", "the ice garden", "hoopfeed", "togethxr"]),
    ("Advocacy / Foundation", 7, ["women in sport", "women's sports foundation"]),
]


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


def parse_date(raw_date: str) -> str:
    raw_date = clean_text(raw_date)
    if not raw_date:
        return ""
    try:
        return parsedate_to_datetime(raw_date).isoformat()
    except Exception:
        return raw_date


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

            title = tidy_google_title(item.findtext("title", default=""), item_source)
            link = clean_text(item.findtext("link", default=""))
            published = parse_date(item.findtext("pubDate", default=""))
            categories = ", ".join(clean_text(c.text or "") for c in item.findall("category") if c.text)
            summary = clean_text(item.findtext("description", default=""))

            articles.append({
                "source": item_source,
                "title": title,
                "link": link,
                "published": published,
                "categories": categories,
                "summary": summary,
            })

        return articles

    # Basic Atom support
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    source_title = clean_text(root.findtext("atom:title", default=url, namespaces=ns))

    for entry in entries:
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ns))
        published = parse_date(
            entry.findtext("atom:published", default="", namespaces=ns)
            or entry.findtext("atom:updated", default="", namespaces=ns)
        )
        summary = clean_text(entry.findtext("atom:summary", default="", namespaces=ns))
        link = ""

        link_elem = entry.find("atom:link", ns)
        if link_elem is not None:
            link = link_elem.attrib.get("href", "")

        articles.append({
            "source": source_title,
            "title": title,
            "link": link,
            "published": published,
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


def keyword_present(text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def classify_sport(text: str) -> str:
    # Score-based sport detection is safer than first-match detection.
    # It prevents broad terms like "sun" or "dream" from incorrectly turning
    # golf, tennis, or soccer stories into WNBA stories.
    scores: Dict[str, int] = {}

    for sport, keywords in SPORT_RULES:
        score = 0
        for keyword in keywords:
            if keyword_present(text, keyword):
                # Specific phrases and athlete names are stronger than short team names.
                if len(keyword) <= 4:
                    score += 1
                elif " " in keyword:
                    score += 3
                else:
                    score += 2
        if score:
            scores[sport] = score

    if not scores:
        return "Women's Sports"

    return max(scores.items(), key=lambda item: item[1])[0]

def classify_story_type(text: str) -> str:
    for story_type, keywords in STORY_TYPE_RULES:
        if any(keyword in text for keyword in keywords):
            return story_type
    return "General News"


def get_content_bucket(sport: str, story_type: str, text: str) -> str:
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the Game"
    if story_type in {"Game Recap", "Game Preview"}:
        return "Tonight / Game Coverage"
    if any(name in text for name in BIG_ENGAGEMENT_NAMES):
        return "Star Watch"
    if story_type in {"Culture / Advocacy", "Player Profile"}:
        return "Culture & Impact"
    if sport in {"NCAA Women's Basketball", "Softball", "Volleyball"}:
        return "College Spotlight"
    return "Daily News"


def source_tier_and_quality(source: str, link: str = "") -> Tuple[str, int]:
    # Score source quality from the source name first. Do not use the full link
    # for keyword matching, because Google News links can contain topic words
    # like WNBA and accidentally make non-official sources look official.
    source_text = clean_text(source).lower()
    host_text = ""
    try:
        host_text = urllib.parse.urlparse(link).netloc.lower()
    except Exception:
        host_text = ""

    combined = f"{source_text} {host_text}".strip()

    for tier, quality, keywords in SOURCE_TIERS:
        if any(keyword in combined for keyword in keywords):
            return tier, quality

    if "news.google.com" in host_text:
        return "Aggregator", 5

    return "Other", 6

def calculate_priority(text: str, sport: str, story_type: str, source_quality: int) -> int:
    score = 3

    if any(name in text for name in BIG_ENGAGEMENT_NAMES):
        score += 3

    if sport in {"WNBA", "NWSL / Women's Soccer", "NCAA Women's Basketball", "PWHL / Women's Hockey"}:
        score += 2
    elif sport in {"Tennis", "Softball", "Volleyball", "Golf / LPGA"}:
        score += 1

    if story_type in {"Breaking News", "Game Recap", "Business / Growth", "League Expansion"}:
        score += 2
    elif story_type in {"Game Preview", "Awards / Rankings"}:
        score += 1

    matched_high_intent = sum(1 for keyword in HIGH_INTENT_KEYWORDS if keyword in text)
    score += min(matched_high_intent, 2)

    if source_quality >= 9:
        score += 1
    elif source_quality <= 5:
        score -= 1

    if any(keyword in text for keyword in NEGATIVE_OR_SENSITIVE_KEYWORDS):
        score -= 2

    if any(keyword in text for keyword in RUMOR_WORDS):
        score -= 1

    return max(1, min(score, 10))


def extract_primary_entity(text: str) -> str:
    for name in BIG_ENGAGEMENT_NAMES:
        if name in text:
            return name.title()

    for entity in TEAM_AND_TOPIC_ENTITIES:
        if entity in text:
            return entity.title()

    return ""


def topic_key_from_text(text: str, sport: str) -> str:
    primary = extract_primary_entity(text)
    if primary:
        return f"{sport.lower()}::{primary.lower()}"

    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    important = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    return f"{sport.lower()}::" + "_".join(important[:8])


def choose_post_format(story_type: str, priority: int) -> str:
    if priority >= 8 and story_type in {"Breaking News", "Game Recap"}:
        return "Breaking graphic + carousel"
    if story_type == "Business / Growth":
        return "Data carousel"
    if story_type == "League Expansion":
        return "Map/expansion carousel"
    if story_type == "Game Preview":
        return "Tonight graphic"
    if story_type == "Player Profile":
        return "Reel or story feature"
    if story_type == "Awards / Rankings":
        return "Single graphic"
    return "Story post"


def why_it_matters(article: Dict[str, str], sport: str, story_type: str, priority: int) -> str:
    title = article.get("title", "")

    if story_type == "Business / Growth":
        return "This is a growth-of-the-game story that helps show why women's sports are becoming a major media and business opportunity."
    if story_type == "League Expansion":
        return "Expansion stories show where fan demand is rising and help followers understand how quickly the women's sports landscape is changing."
    if story_type == "Game Recap":
        return f"This is timely {sport} coverage with a result fans may want explained quickly."
    if story_type == "Game Preview":
        return f"This gives followers a reason to watch {sport} and can feed your pregame graphics."
    if priority >= 8:
        return "This has high engagement potential because it includes a major athlete, record, milestone, or highly searchable topic."
    if "record" in title.lower() or "historic" in title.lower():
        return "Records and historic moments are strong proof points for the rise of women's sports."
    return "This is a useful daily update that can help keep the audience informed and consistent with the brand."


def instagram_angle(article: Dict[str, str], sport: str, story_type: str, priority: int) -> str:
    title = article.get("title", "")

    if story_type == "Business / Growth":
        return "The business of women's sports is not emerging anymore. It is becoming big business."
    if story_type == "League Expansion":
        return "Another sign that women's sports demand is outgrowing the old model."
    if story_type == "Game Recap":
        return f"What happened, who stood out, and why it matters for {sport} fans."
    if story_type == "Game Preview":
        return f"What to watch tonight in {sport}, with one key player and one key matchup."
    if story_type == "Player Profile":
        return "The athlete story behind the headline."
    if priority >= 8:
        return "This is the kind of story casual fans will stop scrolling for."
    return f"Quick hit: {title}"


def suggested_caption(article: Dict[str, str], sport: str, story_type: str) -> str:
    title = article.get("title", "").strip()
    if story_type == "Game Preview":
        return f"{sport} watchlist: {title} What are you watching for?"
    if story_type == "Game Recap":
        return f"{title} Here is the quick breakdown and why it matters."
    if story_type == "Business / Growth":
        return f"{title} The growth of women's sports keeps getting harder to ignore."
    if story_type == "League Expansion":
        return f"{title} More teams, more investment, more proof that the demand is real."
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


def is_sensitive_text(text: str) -> bool:
    return any(keyword in text for keyword in NEGATIVE_OR_SENSITIVE_KEYWORDS)


def needs_verification_text(text: str, source_quality: int) -> bool:
    return source_quality < 8 or any(keyword in text for keyword in RUMOR_WORDS) or is_sensitive_text(text)


def editorial_decision(
    priority: int,
    source_quality: int,
    sensitive: bool,
    verification_needed: bool,
    duplicate_rank: int,
    story_type: str,
    content_lane_value: str,
    headline: str,
    excluded: bool,
) -> str:
    if excluded:
        return "Skip"
    if sensitive:
        return "Review Before Posting"
    if duplicate_rank > 1:
        return "Skip Duplicate"
    if verification_needed:
        if priority >= 9 and source_quality >= 8:
            return "Maybe Post"
        return "Verify First"

    must_post_story = (
        story_type in {"Breaking News", "Business / Growth", "League Expansion"}
        or content_lane_value == "Star-driven engagement"
        or any(word in headline.lower() for word in ["championship", "title", "record", "historic", "first"])
    )

    if priority >= 10 and source_quality >= 8 and must_post_story:
        return "Must Post"
    if priority >= 8 and source_quality >= 7:
        return "Maybe Post"
    if priority >= 6:
        return "Save for Weekend"
    return "Skip"

def recommended_timing(priority: int, story_type: str, verification_needed: bool) -> str:
    if verification_needed:
        return "Verify first"
    if priority >= 9 or story_type == "Breaking News":
        return "Post ASAP"
    if story_type == "Game Preview":
        return "Post before tipoff/kickoff"
    if story_type == "Game Recap":
        return "Post within 2 hours"
    if story_type in {"Business / Growth", "League Expansion", "Player Profile"}:
        return "Post during daytime engagement window"
    return "Use as filler"


def time_sensitive(story_type: str) -> str:
    if story_type in {"Breaking News", "Game Preview", "Game Recap", "Injury / Availability"}:
        return "Yes"
    return "No"


def content_lane(story_type: str, sport: str, text: str) -> str:
    if any(name in text for name in BIG_ENGAGEMENT_NAMES):
        return "Star-driven engagement"
    if story_type in {"Business / Growth", "League Expansion"}:
        return "Growth of the game"
    if story_type in {"Game Preview", "Game Recap"}:
        return "Game coverage"
    if sport in {"NCAA Women's Basketball", "Softball", "Volleyball"}:
        return "College spotlight"
    return "Daily news"


def hook(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    if story_type == "Business / Growth":
        return "Women's sports are becoming impossible for the business world to ignore."
    if story_type == "League Expansion":
        return "Another market is betting big on women's sports."
    if story_type == "Game Preview":
        return "Here is why this matchup is worth your time tonight."
    if story_type == "Game Recap":
        return "Here is the quick version of what happened and why it matters."
    if story_type == "Breaking News":
        return "This is developing, but it is already worth tracking."
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
    if story_type == "Game Recap":
        return f"Quick recap: {title}"
    if story_type == "Breaking News":
        return f"Breaking: {title}"
    return title


def carousel_outline(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    if story_type == "Business / Growth":
        return "Slide 1: headline stat | Slide 2: what changed | Slide 3: why it matters | Slide 4: what comes next"
    if story_type == "League Expansion":
        return "Slide 1: expansion headline | Slide 2: market/team details | Slide 3: why demand is rising | Slide 4: fan question"
    if story_type == "Game Preview":
        return "Slide 1: matchup | Slide 2: player to watch | Slide 3: key matchup | Slide 4: prediction or question"
    if story_type == "Game Recap":
        return "Slide 1: result | Slide 2: top performer | Slide 3: turning point | Slide 4: what is next"
    if story_type == "Breaking News":
        return "Slide 1: news | Slide 2: confirmed details | Slide 3: context | Slide 4: what to watch next"
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
    if story_type == "Game Recap":
        return "Use a quick recap carousel with final result, top performer, and next game."
    if story_type == "Player Profile":
        return "Use an athlete-first reel or carousel with one personal angle."
    if story_type == "Breaking News":
        return "Use a breaking graphic with source credit and one context slide."
    return f"Use a simple {sport} news card with headline, context, and one engagement question."


def is_likely_mens_story_text(text: str) -> bool:
    # Skip obvious men's sports stories that come through broad NCAA or golf feeds.
    # Keep stories that explicitly mention women's/girls content.
    if any(term in text for term in ["women", "women's", "women’s", "girls", "wnba", "nwsl", "pwhl", "lpga", "wta", "uswnt"]):
        return False
    return any(keyword in text for keyword in LIKELY_MENS_STORY_KEYWORDS)


def enrich_article(article: Dict[str, str]) -> Dict[str, str]:
    text = combined_text(article)
    sport = classify_sport(text)
    story_type = classify_story_type(text)
    source_tier, source_quality = source_tier_and_quality(article.get("source", ""), article.get("link", ""))
    priority = calculate_priority(text, sport, story_type, source_quality)
    bucket = get_content_bucket(sport, story_type, text)
    primary_entity = extract_primary_entity(text)
    cluster_id = topic_key_from_text(text, sport)
    sensitive = is_sensitive_text(text)
    verification_needed = needs_verification_text(text, source_quality)
    excluded = is_likely_mens_story_text(text)

    article.update({
        "sport": sport,
        "story_type": story_type,
        "priority_score": str(priority),
        "source_tier": source_tier,
        "source_quality": str(source_quality),
        "content_bucket": bucket,
        "primary_entity": primary_entity,
        "cluster_id": cluster_id,
        "sensitive": "Yes" if sensitive else "No",
        "verification_needed": "Yes" if verification_needed else "No",
        "why_it_matters": why_it_matters(article, sport, story_type, priority),
        "instagram_angle": instagram_angle(article, sport, story_type, priority),
        "post_format": choose_post_format(story_type, priority),
        "suggested_caption": suggested_caption(article, sport, story_type),
        "hashtags": hashtags(sport),
        "time_sensitive": time_sensitive(story_type),
        "content_lane": content_lane(story_type, sport, text),
        "excluded": "Yes" if excluded else "No",
        "exclude_reason": "Likely men's sports story" if excluded else "",
    })
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
    cluster_counts: Dict[str, int] = {}

    for article in articles:
        cluster_id = article.get("cluster_id", "")
        cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1

    sorted_articles = sorted(
        articles,
        key=lambda x: (
            x.get("cluster_id", ""),
            int(x.get("priority_score", "0")),
            int(x.get("source_quality", "0")),
            x.get("published", ""),
        ),
        reverse=True,
    )

    rank_by_cluster: Dict[str, int] = {}
    for article in sorted_articles:
        cluster_id = article.get("cluster_id", "")
        rank_by_cluster[cluster_id] = rank_by_cluster.get(cluster_id, 0) + 1
        article["cluster_rank"] = str(rank_by_cluster[cluster_id])
        article["related_story_count"] = str(cluster_counts.get(cluster_id, 1))
        article["duplicate_status"] = "Primary" if rank_by_cluster[cluster_id] == 1 else "Related / duplicate angle"

    return articles


def duplicate_limit_reason(article: Dict[str, str], cluster_count: int, entity_count: int, sport_count: int, source_count: int) -> str:
    if cluster_count >= MAX_PER_CLUSTER:
        return f"Skipped because this topic already has {MAX_PER_CLUSTER} stories in the brief."
    if article.get("primary_entity") and entity_count >= MAX_PER_PRIMARY_ENTITY:
        return f"Skipped because {article.get('primary_entity')} already has {MAX_PER_PRIMARY_ENTITY} stories in the brief."
    if sport_count >= MAX_PER_SPORT:
        return f"Skipped because {article.get('sport')} already has {MAX_PER_SPORT} stories in the brief."
    if source_count >= MAX_PER_SOURCE:
        return f"Skipped because {article.get('source')} already has {MAX_PER_SOURCE} stories in the brief."
    return ""


def build_daily_content_brief(articles: List[Dict[str, str]], max_items: int = MAX_DAILY_BRIEF_ITEMS) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    cluster_counts: Dict[str, int] = {}
    entity_counts: Dict[str, int] = {}
    sport_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    must_post_count = 0

    candidates = sorted(
        articles,
        key=lambda x: (
            int(x.get("priority_score", "0")),
            int(x.get("source_quality", "0")),
            x.get("published", ""),
        ),
        reverse=True,
    )

    for article in candidates:
        priority = int(article.get("priority_score", "0") or 0)
        source_quality = int(article.get("source_quality", "0") or 0)
        title = article.get("title", "").strip()
        cluster_id = article.get("cluster_id", "")
        primary_entity = article.get("primary_entity", "")
        sport = article.get("sport", "Women's Sports")
        source = article.get("source", "")
        sensitive = article.get("sensitive") == "Yes"
        verification_needed = article.get("verification_needed") == "Yes"
        cluster_rank = int(article.get("cluster_rank", "1") or 1)
        excluded = article.get("excluded") == "Yes"

        if not title or priority < 6 or excluded:
            continue

        # Daily brief gets only the primary version of a topic.
        # Duplicates still exist in the full CSV for research, but not here.
        if cluster_rank > 1:
            continue

        cluster_count = cluster_counts.get(cluster_id, 0)
        entity_count = entity_counts.get(primary_entity, 0) if primary_entity else 0
        sport_count = sport_counts.get(sport, 0)
        source_count = source_counts.get(source, 0)

        limit_reason = duplicate_limit_reason(article, cluster_count, entity_count, sport_count, source_count)
        if limit_reason:
            continue

        decision = editorial_decision(
            priority=priority,
            source_quality=source_quality,
            sensitive=sensitive,
            verification_needed=verification_needed,
            duplicate_rank=cluster_rank,
            story_type=article.get("story_type", ""),
            content_lane_value=article.get("content_lane", ""),
            headline=title,
            excluded=excluded,
        )

        # Keep the daily brief actionable. Skip means do not include it.
        if decision in {"Skip", "Skip Duplicate"}:
            continue

        # Cap Must Post so the brief feels selective.
        if decision == "Must Post":
            if must_post_count >= MAX_MUST_POST_ITEMS:
                decision = "Maybe Post"
            else:
                must_post_count += 1

        rank = len(selected) + 1

        selected.append({
            "rank": str(rank),
            "editorial_decision": decision,
            "recommended_timing": recommended_timing(priority, article.get("story_type", ""), verification_needed),
            "priority_score": str(priority),
            "source_quality": str(source_quality),
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
            "headline": title,
            "link": article.get("link", ""),
            "post_format": article.get("post_format", ""),
            "hook": hook(article),
            "first_slide": first_slide(article),
            "carousel_outline": carousel_outline(article),
            "instagram_angle": article.get("instagram_angle", ""),
            "why_it_matters": article.get("why_it_matters", ""),
            "caption_starter": article.get("suggested_caption", ""),
            "visual_brief": visual_brief(article),
            "hashtags": article.get("hashtags", ""),
            "published": article.get("published", ""),
            "notes": "",
        })

        cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
        if primary_entity:
            entity_counts[primary_entity] = entity_counts.get(primary_entity, 0) + 1
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1

        if len(selected) >= max_items:
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
    enriched.sort(
        key=lambda x: (
            int(x.get("priority_score", "0")),
            int(x.get("source_quality", "0")),
            x.get("published", ""),
        ),
        reverse=True,
    )
    return enriched


def save_articles_csv(articles: List[Dict[str, str]], filename: str = OUTPUT_FILE) -> None:
    fieldnames = [
        "priority_score",
        "source_quality",
        "source_tier",
        "content_bucket",
        "content_lane",
        "sport",
        "story_type",
        "source",
        "title",
        "published",
        "link",
        "post_format",
        "instagram_angle",
        "why_it_matters",
        "suggested_caption",
        "hashtags",
        "primary_entity",
        "cluster_id",
        "cluster_rank",
        "related_story_count",
        "duplicate_status",
        "verification_needed",
        "sensitive",
        "time_sensitive",
        "excluded",
        "exclude_reason",
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
