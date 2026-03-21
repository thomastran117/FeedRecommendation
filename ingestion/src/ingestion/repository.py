from __future__ import annotations

from contextlib import nullcontext

from psycopg.errors import UniqueViolation

from ingestion.models import ScrapedArticle


class ArticleRepository:
    def __init__(self, connection, schema_name: str | None = None):
        self.connection = connection
        self.schema_name = schema_name

    def article_exists(self, normalized_url: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 1
                FROM {self._qualify('articles')}
                WHERE normalized_url = %s
                LIMIT 1
                """,
                (normalized_url,),
            )
            return cursor.fetchone() is not None

    def insert_article(self, article: ScrapedArticle) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {self._qualify('articles')} (
                    url,
                    normalized_url,
                    source_name,
                    source_url,
                    rss_feed_url,
                    title,
                    body,
                    author,
                    published_at,
                    scraped_at,
                    body_length,
                    is_valid
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    article.url,
                    article.normalized_url,
                    article.source_name,
                    article.source_url,
                    article.rss_feed_url,
                    article.title,
                    article.body,
                    article.author,
                    article.published_at,
                    article.scraped_at,
                    len(article.body),
                    True,
                ),
            )
            return cursor.fetchone()[0]

    def transaction(self):
        if hasattr(self.connection, "transaction"):
            return self.connection.transaction()
        return nullcontext()

    def is_duplicate_error(self, error: Exception) -> bool:
        return isinstance(error, UniqueViolation)

    def _qualify(self, table_name: str) -> str:
        if not self.schema_name:
            return table_name
        return f"{self.schema_name}.{table_name}"
