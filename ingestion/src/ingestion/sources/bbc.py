from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

import requests

from ingestion.models import DiscoveredArticle
from ingestion.normalize import normalize_url


BBC_RSS_URL = "https://feeds.bbci.co.uk/news/rss.xml"
BBC_SOURCE_NAME = "BBC News"
BBC_SOURCE_URL = "https://www.bbc.com/news"
DC_NAMESPACE = {"dc": "http://purl.org/dc/elements/1.1/"}


def default_feed_fetcher(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


@dataclass
class BBCNewsRssSource:
    feed_fetcher: callable = default_feed_fetcher
    rss_feed_url: str = BBC_RSS_URL
    source_name: str = BBC_SOURCE_NAME
    source_url: str = BBC_SOURCE_URL

    def discover_articles(self) -> list[DiscoveredArticle]:
        rss_payload = self.feed_fetcher(self.rss_feed_url)
        root = ET.fromstring(rss_payload)
        articles: list[DiscoveredArticle] = []

        for item in root.findall("./channel/item"):
            link = _read_text(item.find("link"))
            if not link:
                continue

            published_at = _parse_rss_datetime(_read_text(item.find("pubDate")))
            author = _read_text(item.find("dc:creator", DC_NAMESPACE))
            title = _read_text(item.find("title"))

            articles.append(
                DiscoveredArticle(
                    article_url=link,
                    normalized_url=normalize_url(link),
                    source_name=self.source_name,
                    source_url=self.source_url,
                    rss_feed_url=self.rss_feed_url,
                    title=title,
                    author=author,
                    published_at=published_at,
                )
            )

        return articles


def _read_text(node: ET.Element | None) -> str | None:
    if node is None or node.text is None:
        return None

    value = node.text.strip()
    return value or None


def _parse_rss_datetime(value: str | None):
    if not value:
        return None

    parsed = parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
