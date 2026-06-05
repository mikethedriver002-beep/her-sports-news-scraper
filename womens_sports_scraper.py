"""
Her Sports Daily Women's Sports News Scraper v3
-----------------------------------------------

This scraper pulls women's sports headlines from RSS feeds and turns them into
two CSVs:

1. womens_sports_articles.csv
   Full article database with priority, sport, story type, post angle, caption, etc.

2. daily_content_brief.csv
   A smaller, cleaner shortlist of the best stories to consider posting today.

It uses only Python's standard library, so it works cleanly in GitHub Actions.
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
MAX_DAILY_BRIEF_ITEMS = 25


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

    # Broader topic searches to catch stories we missed
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
    ("Golf / LPGA", ["lpga", "women's open", "golf", "nelly korda", "lexi thompson", "rose zhang", "kupcho"]),
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


HIGH_INTENT_KEYWORDS = [
    "record", "historic", "first", "breaks", "milestone", "championship", "title",
    "wins", "upset", "rivalry", "sold out", "attendance", "viewership", "media rights",
    "expansion", "launch", "new league", "contract", "salary", "injury", "returns",
]


NEGATIVE_OR_SENSITIVE_KEYWORDS = [
    "abuse", "assault", "harassment", "lawsuit", "investigation", "arrest", "death",
    "died", "killed", "violence", "scandal",
]


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "over", "after", "before",
    "about", "what", "why", "how", "when", "where", "women", "womens", "woman", "sports",
    "sport", "news", "new", "latest", "watch", "live", "highlights", "full", "today",
    "game", "games", "season", "team", "teams", "player", "players"
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


def classify_sport(text: str) -> str:
    for sport, keywords in SPORT_RULES:
        if any(keyword in text for keyword in keywords):
            return sport
    return "Women's Sports"


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


def calculate_priority(text: str, sport: str, story_type: str) -> int:
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

    if any(keyword in text for keyword in NEGATIVE_OR_SENSITIVE_KEYWORDS):
        score -= 2

    return max(1, min(score, 10))


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


def enrich_article(article: Dict[str, str]) -> Dict[str, str]:
    text = combined_text(article)
    sport = classify_sport(text)
    story_type = classify_story_type(text)
    priority = calculate_priority(text, sport, story_type)
    bucket = get_content_bucket(sport, story_type, text)

    article.update({
        "sport": sport,
        "story_type": story_type,
        "priority_score": str(priority),
        "content_bucket": bucket,
        "why_it_matters": why_it_matters(article, sport, story_type, priority),
        "instagram_angle": instagram_angle(article, sport, story_type, priority),
        "post_format": choose_post_format(story_type, priority),
        "suggested_caption": suggested_caption(article, sport, story_type),
        "hashtags": hashtags(sport),
    })
    return article


def dedupe_articles(articles: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    deduped = []

    for article in articles:
        title = article.get("title", "").lower()
        link = article.get("link", "").lower()
        key = re.sub(r"[^a-z0-9]+", "", title)[:120] or link

        if key and key not in seen:
            seen.add(key)
            deduped.append(article)

    return deduped


def topic_key(title: str) -> str:
    words = re.findall(r"[a-zA-Z0-9']+", title.lower())
    important = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    return " ".join(important[:8])


def is_sensitive(article: Dict[str, str]) -> bool:
    text = combined_text(article)
    return any(keyword in text for keyword in NEGATIVE_OR_SENSITIVE_KEYWORDS)


def coverage_slot(priority: int, rank: int, sensitive: bool) -> str:
    if sensitive:
        return "Review Before Posting"
    if rank <= 3 and priority >= 8:
        return "Lead Story"
    if priority >= 8:
        return "Strong Candidate"
    if priority >= 6:
        return "Story Filler"
    return "Watchlist"


def visual_brief(article: Dict[str, str]) -> str:
    story_type = article.get("story_type", "")
    sport = article.get("sport", "")

    if story_type == "Business / Growth":
        return "Use a clean data carousel: headline stat, why it matters, trend context, what comes next."
    if story_type == "League Expansion":
        return "Use a map or team/logo style carousel showing the new market and why the expansion matters."
    if story_type == "Game Preview":
        return "Use a Tonight graphic: matchup, time/network if available, one key player, one prediction angle."
    if story_type == "Game Recap":
        return "Use a quick recap carousel: final result, top performer, turning point, next game."
    if story_type == "Player Profile":
        return "Use a reel or carousel focused on the athlete, their background, and why fans should care."
    if story_type == "Breaking News":
        return "Use a breaking graphic with a short headline, source tag, and one context slide."
    return f"Use a simple {sport} news card with headline, context, and one engagement question."


def hook(article: Dict[str, str]) -> str:
    title = article.get("title", "")
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
    return title


def build_daily_content_brief(articles: List[Dict[str, str]], max_items: int = MAX_DAILY_BRIEF_ITEMS) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    seen_topics = set()
    sport_counts: Dict[str, int] = {}
    bucket_counts: Dict[str, int] = {}

    candidates = sorted(
        articles,
        key=lambda x: (int(x.get("priority_score", "0")), x.get("published", "")),
        reverse=True,
    )

    for article in candidates:
        priority = int(article.get("priority_score", "0") or 0)
        title = article.get("title", "").strip()
        sport = article.get("sport", "Women's Sports")
        bucket = article.get("content_bucket", "Daily News")
        key = topic_key(title)

        if not title or priority < 5:
            continue
        if key in seen_topics:
            continue
        if sport_counts.get(sport, 0) >= 6:
            continue
        if bucket_counts.get(bucket, 0) >= 7:
            continue

        rank = len(selected) + 1
        sensitive = is_sensitive(article)
        status = "Manual review" if sensitive else ("Post candidate" if priority >= 8 else "Maybe")

        selected.append({
            "rank": str(rank),
            "coverage_slot": coverage_slot(priority, rank, sensitive),
            "priority_score": str(priority),
            "status": status,
            "content_bucket": bucket,
            "sport": sport,
            "story_type": article.get("story_type", ""),
            "source": article.get("source", ""),
            "headline": title,
            "link": article.get("link", ""),
            "post_format": article.get("post_format", ""),
            "hook": hook(article),
            "instagram_angle": article.get("instagram_angle", ""),
            "why_it_matters": article.get("why_it_matters", ""),
            "caption_starter": article.get("suggested_caption", ""),
            "visual_brief": visual_brief(article),
            "hashtags": article.get("hashtags", ""),
            "published": article.get("published", ""),
            "notes": "",
        })

        seen_topics.add(key)
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

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
    enriched.sort(key=lambda x: (int(x.get("priority_score", "0")), x.get("published", "")), reverse=True)
    return enriched


def save_articles_csv(articles: List[Dict[str, str]], filename: str = OUTPUT_FILE) -> None:
    fieldnames = [
        "priority_score",
        "content_bucket",
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
        "coverage_slot",
        "priority_score",
        "status",
        "content_bucket",
        "sport",
        "story_type",
        "source",
        "headline",
        "link",
        "post_format",
        "hook",
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
