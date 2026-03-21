from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class DiscoveredArticle:
    article_url: str
    normalized_url: str
    source_name: str
    source_url: str
    rss_feed_url: str
    title: str | None
    author: str | None
    published_at: datetime | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ScrapedArticle:
    url: str
    normalized_url: str
    source_name: str
    source_url: str
    rss_feed_url: str
    title: str
    body: str
    author: str | None
    published_at: datetime | None
    scraped_at: datetime

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ScrapeFailure:
    article_url: str
    normalized_url: str
    source_name: str
    error: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IngestionSummary:
    discovered: int = 0
    skipped: int = 0
    inserted: int = 0
    indexed: int = 0
    scrape_failures: int = 0
    persist_failures: int = 0
