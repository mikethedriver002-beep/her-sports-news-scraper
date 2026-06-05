"""
women_sports_scraper.py
~~~~~~~~~~~~~~~~~~~~~~~~

This script demonstrates how to automate news scraping for women's sports
using RSS feeds. It leverages the `feedparser` library to parse RSS feeds
from a variety of reputable sources and writes the results to a CSV file
for further analysis.

Usage:

    python womens_sports_scraper.py

The script will fetch articles from each defined feed URL, collect
information such as the article title, publication date, categories,
summary and link, and then save the aggregated results into
`womens_sports_articles.csv` in the current directory.

Note: This script is intended to be run as a one-off example. To build a
production-ready scraper, you may wish to handle exceptions more
robustly, respect websites' robots.txt policies, and schedule periodic
execution via tools like cron or Airflow.
"""

import csv
import datetime
from typing import List, Dict

import urllib.request
import xml.etree.ElementTree as ET


def parse_feed(url: str) -> List[Dict[str, str]]:
    """Parse a single RSS feed using built-in XML parsing and return articles.

    This function avoids third-party dependencies by fetching the RSS XML
    directly and parsing it with Python's standard library. It extracts
    common RSS elements like title, link, publication date, category and
    description/summary.

    Args:
        url: The URL to the RSS feed.

    Returns:
        A list of dictionaries, each representing an article with keys
        ``source``, ``title``, ``link``, ``published``, ``categories``, and
        ``summary``.
    """
    articles: List[Dict[str, str]] = []
    try:
        # Some websites may block requests without a User-Agent header.
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0; +https://example.com)"
            },
        )
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
    except Exception as exc:
        print(f"Failed to fetch feed {url}: {exc}")
        return articles

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        print(f"Failed to parse XML for {url}: {exc}")
        return articles

    # Determine namespace (if any) and set prefix accordingly
    # Many RSS feeds do not use namespaces; handle generic case
    channel = root.find('channel') if root.tag == 'rss' else root
    source_title = url
    if channel is not None:
        title_elem = channel.find('title')
        if title_elem is not None and title_elem.text:
            source_title = title_elem.text.strip()

        for item in channel.findall('item'):
            title = item.findtext('title', default='').strip()
            link = item.findtext('link', default='').strip()
            pub_date = item.findtext('pubDate', default='').strip()
            # Try to parse pubDate; if fail, keep raw
            try:
                # Example format: 'Wed, 05 Jun 2026 16:31:52 +0000'
                published_dt = datetime.datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                published_iso = published_dt.isoformat()
            except Exception:
                published_iso = pub_date

            # Categories can have multiple <category> tags
            categories_list = [cat.text.strip() for cat in item.findall('category') if cat.text]
            categories = ', '.join(categories_list)

            # Summary or description
            summary = item.findtext('description', default='').strip()

            articles.append({
                "source": source_title,
                "title": title,
                "link": link,
                "published": published_iso,
                "categories": categories,
                "summary": summary
            })

    return articles


def scrape_feeds(feed_urls: List[str]) -> List[Dict[str, str]]:
    """Collect articles from multiple RSS feeds.

    Args:
        feed_urls: A list of feed URLs to scrape.

    Returns:
        A consolidated list of article dictionaries from all feeds.
    """
    all_articles = []
    for url in feed_urls:
        print(f"Fetching feed: {url}")
        try:
            articles = parse_feed(url)
            print(f"  Retrieved {len(articles)} articles from {url}")
            all_articles.extend(articles)
        except Exception as exc:
            print(f"  Error processing {url}: {exc}")
    return all_articles


def save_to_csv(articles: List[Dict[str, str]], filename: str) -> None:
    """Save the list of articles to a CSV file.

    Args:
        articles: A list of article dictionaries.
        filename: The filename for the CSV file.
    """
    fieldnames = ["source", "title", "link", "published", "categories", "summary"]
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            writer.writerow(article)
    print(f"Saved {len(articles)} articles to {filename}")


def main() -> None:
    """Main entry point for the script."""
    # Define the RSS feeds to scrape. Feel free to add or remove feeds.
    feed_urls = [
        "https://justwomenssports.com/feed/",
        "https://womeninsport.org/feed/",
        "https://www.thegistsports.com/feed/",
        "https://www.womenssportsfoundation.org/feed/",  # general women's sports news
        "https://www.insidehighered.com/taxonomy/term/11204/feed",  # includes NCAA women's sports
        # Additional feeds can be added here
    ]

    # Collect articles from the feeds
    articles = scrape_feeds(feed_urls)

    # Save the results to a CSV file
    csv_filename = "womens_sports_articles.csv"
    save_to_csv(articles, csv_filename)


if __name__ == "__main__":
    main()