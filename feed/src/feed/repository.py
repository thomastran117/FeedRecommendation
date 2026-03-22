from __future__ import annotations

from contextlib import nullcontext
from datetime import date, datetime

from feed.models import ArticleCandidate, RankedFeedItem


class FeedRepository:
    def __init__(self, connection, schema_name: str | None = None):
        self.connection = connection
        self.schema_name = schema_name

    def fetch_recent_valid_articles(
        self,
        source_window_start: datetime,
        source_window_end: datetime,
    ) -> list[ArticleCandidate]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    id,
                    title,
                    published_at,
                    scraped_at,
                    COALESCE(published_at, scraped_at) AS article_time
                FROM {self._qualify('articles')}
                WHERE is_valid = TRUE
                  AND COALESCE(published_at, scraped_at) >= %s
                  AND COALESCE(published_at, scraped_at) <= %s
                ORDER BY id DESC
                """,
                (source_window_start, source_window_end),
            )
            rows = cursor.fetchall()

        return [
            ArticleCandidate(
                article_id=row[0],
                title=row[1],
                published_at=row[2],
                scraped_at=row[3],
                article_time=row[4],
            )
            for row in rows
        ]

    def fetch_article_popularity(
        self,
        article_ids: list[int],
        source_window_start: datetime,
        source_window_end: datetime,
    ) -> dict[int, int]:
        if not article_ids:
            return {}

        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT article_id, COALESCE(SUM(click_count), 0) AS raw_popularity
                FROM {self._qualify('article_popularity_daily')}
                WHERE article_id = ANY(%s)
                  AND bucket_date >= %s
                  AND bucket_date <= %s
                GROUP BY article_id
                """,
                (
                    article_ids,
                    source_window_start.date(),
                    source_window_end.date(),
                ),
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def upsert_default_feed(
        self,
        *,
        generated_at: datetime,
        algorithm_version: str,
        status: str,
        source_window_start: datetime,
        source_window_end: datetime,
    ) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {self._qualify('feeds')} (
                    feed_type,
                    user_id,
                    generated_at,
                    algorithm_version,
                    status,
                    source_window_start,
                    source_window_end
                )
                VALUES ('default', NULL, %s, %s, %s, %s, %s)
                ON CONFLICT (feed_type) WHERE user_id IS NULL
                DO UPDATE SET
                    generated_at = EXCLUDED.generated_at,
                    algorithm_version = EXCLUDED.algorithm_version,
                    status = EXCLUDED.status,
                    source_window_start = EXCLUDED.source_window_start,
                    source_window_end = EXCLUDED.source_window_end,
                    updated_at = NOW()
                RETURNING id
                """,
                (
                    generated_at,
                    algorithm_version,
                    status,
                    source_window_start,
                    source_window_end,
                ),
            )
            return cursor.fetchone()[0]

    def update_feed_status(
        self,
        feed_id: int,
        *,
        status: str,
        generated_at: datetime,
        algorithm_version: str,
        source_window_start: datetime,
        source_window_end: datetime,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {self._qualify('feeds')}
                SET generated_at = %s,
                    algorithm_version = %s,
                    status = %s,
                    source_window_start = %s,
                    source_window_end = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    generated_at,
                    algorithm_version,
                    status,
                    source_window_start,
                    source_window_end,
                    feed_id,
                ),
            )

    def replace_feed_items(self, feed_id: int, items: list[RankedFeedItem]) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {self._qualify('feed_items')} WHERE feed_id = %s",
                (feed_id,),
            )

            if not items:
                return

            values = [
                (
                    feed_id,
                    item.article_id,
                    item.rank,
                    item.score,
                    item.recency_score,
                    item.popularity_score,
                    item.click_match_score,
                    item.search_match_score,
                )
                for item in items
            ]
            cursor.executemany(
                f"""
                INSERT INTO {self._qualify('feed_items')} (
                    feed_id,
                    article_id,
                    rank,
                    score,
                    recency_score,
                    popularity_score,
                    click_match_score,
                    search_match_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                values,
            )

    def transaction(self):
        if hasattr(self.connection, "transaction"):
            return self.connection.transaction()
        return nullcontext()

    def _qualify(self, table_name: str) -> str:
        if not self.schema_name:
            return table_name
        return f"{self.schema_name}.{table_name}"
