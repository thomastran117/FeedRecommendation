from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import isclose
import sys

from feed import ALGORITHM_VERSION
from feed.config import load_config
from feed.database import create_connection
from feed.models import ArticleCandidate, FeedRunSummary, RankedFeedItem
from feed.repository import FeedRepository


def run(
    repository: FeedRepository | None = None,
    *,
    config_path: str | None = None,
    now: datetime | None = None,
) -> FeedRunSummary:
    app_config = load_config(config_path)
    generated_at = now or datetime.now(UTC)
    source_window_end = generated_at
    source_window_start = generated_at - timedelta(days=app_config.feed.article_window_days)

    should_close_connection = repository is None
    connection = None

    if repository is None:
        connection = create_connection(app_config)
        repository = FeedRepository(connection)

    feed_id = repository.upsert_default_feed(
        generated_at=generated_at,
        algorithm_version=ALGORITHM_VERSION,
        status="building",
        source_window_start=source_window_start,
        source_window_end=source_window_end,
    )

    try:
        candidates = repository.fetch_recent_valid_articles(
            source_window_start=source_window_start,
            source_window_end=source_window_end,
        )
        raw_popularity = repository.fetch_article_popularity(
            [candidate.article_id for candidate in candidates],
            source_window_start=source_window_start,
            source_window_end=source_window_end,
        )
        ranked_items = rank_default_feed(
            candidates=candidates,
            popularity_by_article_id=raw_popularity,
            recency_weight=app_config.feed.recency_weight,
            popularity_weight=app_config.feed.popularity_weight,
            limit=app_config.feed.default_feed_size,
        )

        with repository.transaction():
            repository.replace_feed_items(feed_id, ranked_items)
            repository.update_feed_status(
                feed_id,
                status="ready",
                generated_at=generated_at,
                algorithm_version=ALGORITHM_VERSION,
                source_window_start=source_window_start,
                source_window_end=source_window_end,
            )

        print(
            "feed_id={feed_id} candidates_considered={candidates} items_written={items}".format(
                feed_id=feed_id,
                candidates=len(candidates),
                items=len(ranked_items),
            )
        )
        return FeedRunSummary(
            feed_id=feed_id,
            candidates_considered=len(candidates),
            items_written=len(ranked_items),
            generated_at=generated_at,
        )
    except Exception:
        repository.update_feed_status(
            feed_id,
            status="failed",
            generated_at=generated_at,
            algorithm_version=ALGORITHM_VERSION,
            source_window_start=source_window_start,
            source_window_end=source_window_end,
        )
        raise
    finally:
        if should_close_connection and connection is not None:
            connection.close()


def rank_default_feed(
    *,
    candidates: list[ArticleCandidate],
    popularity_by_article_id: dict[int, int],
    recency_weight: float,
    popularity_weight: float,
    limit: int,
) -> list[RankedFeedItem]:
    if not candidates:
        return []

    article_timestamps = [candidate.article_time.timestamp() for candidate in candidates]
    oldest_time = min(article_timestamps)
    newest_time = max(article_timestamps)
    time_span = newest_time - oldest_time
    max_raw_popularity = max((popularity_by_article_id.get(candidate.article_id, 0) for candidate in candidates), default=0)

    ranked_items: list[RankedFeedItem] = []
    for candidate in candidates:
        article_time = candidate.article_time.timestamp()
        recency_score = _compute_recency_score(article_time, oldest_time, newest_time, time_span)
        raw_popularity = popularity_by_article_id.get(candidate.article_id, 0)
        popularity_score = 0.0 if max_raw_popularity == 0 else raw_popularity / max_raw_popularity
        final_score = (recency_weight * recency_score) + (popularity_weight * popularity_score)
        ranked_items.append(
            RankedFeedItem(
                article_id=candidate.article_id,
                rank=0,
                score=final_score,
                recency_score=recency_score,
                popularity_score=popularity_score,
            )
        )

    ranked_items.sort(
        key=lambda item: (
            item.score,
            item.article_id,
        ),
        reverse=True,
    )

    return [
        RankedFeedItem(
            article_id=item.article_id,
            rank=index,
            score=item.score,
            recency_score=item.recency_score,
            popularity_score=item.popularity_score,
            click_match_score=item.click_match_score,
            search_match_score=item.search_match_score,
        )
        for index, item in enumerate(ranked_items[:limit], start=1)
    ]


def _compute_recency_score(article_time: float, oldest_time: float, newest_time: float, time_span: float) -> float:
    if isclose(time_span, 0.0):
        return 1.0
    return (article_time - oldest_time) / (newest_time - oldest_time)


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        print(f"Feed generation failed: {error}", file=sys.stderr)
        raise
