from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ArticleCandidate:
    article_id: int
    title: str
    published_at: datetime | None
    scraped_at: datetime
    article_time: datetime


@dataclass(frozen=True)
class RankedFeedItem:
    article_id: int
    rank: int
    score: float
    recency_score: float
    popularity_score: float
    click_match_score: float = 0.0
    search_match_score: float = 0.0


@dataclass(frozen=True)
class FeedRunSummary:
    feed_id: int
    candidates_considered: int
    items_written: int
    generated_at: datetime
