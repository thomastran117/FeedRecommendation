from datetime import UTC, datetime
import math
from pathlib import Path

import pytest

from ingestion.config import AppConfig, DatabaseConfig, IngestionConfig
from ingestion.database import create_connection
from ingestion.indexing import ArticleIndexer
from ingestion.models import ScrapedArticle
from ingestion.repository import ArticleRepository


SCHEMA_SQL = Path(__file__).resolve().parents[2] / "data-models" / "schema" / "schema.sql"


def _build_article(normalized_url: str, title: str, body: str) -> ScrapedArticle:
    return ScrapedArticle(
        url=normalized_url,
        normalized_url=normalized_url,
        source_name="BBC News",
        source_url="https://www.bbc.com/news",
        rss_feed_url="https://feeds.bbci.co.uk/news/rss.xml",
        title=title,
        body=body,
        author=None,
        published_at=None,
        scraped_at=datetime(2026, 3, 21, 10, 0, tzinfo=UTC),
    )


@pytest.fixture()
def integration_connection():
    connection = None

    try:
        connection = create_connection(
            AppConfig(
                database=DatabaseConfig(
                    url="postgresql://postgres:postgres@localhost:5432/appdb",
                    host="localhost",
                    port=5432,
                ),
                ingestion=IngestionConfig(
                    schedule="*/15 * * * *",
                    feed_urls=["https://feeds.bbci.co.uk/news/rss.xml"],
                ),
            )
        )
    except Exception as error:
        pytest.skip(f"Postgres not available for integration test: {error}")

    schema_name = "ingestion_test_schema"

    with connection.cursor() as cursor:
        cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
        cursor.execute(f"CREATE SCHEMA {schema_name}")
        cursor.execute(f"SET search_path TO {schema_name}")
        cursor.execute(SCHEMA_SQL.read_text())
    connection.commit()

    try:
        yield connection, schema_name
    finally:
        if not connection.closed:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            connection.commit()
            connection.close()


def test_article_repository_inserts_and_detects_duplicates(integration_connection):
    connection, schema_name = integration_connection
    repository = ArticleRepository(connection, schema_name=schema_name)
    article = _build_article(
        "https://example.com/articles/1",
        "Market Rally",
        "Stocks rally again today",
    )

    article_id = repository.insert_article(article)

    assert article_id > 0
    assert repository.article_exists(article.normalized_url) is True


def test_article_indexer_writes_terms_and_weights(integration_connection):
    connection, schema_name = integration_connection
    repository = ArticleRepository(connection, schema_name=schema_name)
    indexer = ArticleIndexer(connection, schema_name=schema_name)
    article = _build_article(
        "https://example.com/articles/2",
        "Rally Title",
        "Body rally body",
    )

    article_id = repository.insert_article(article)
    indexer.index_article(article_id, article)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT t.term, ats.term_frequency, ats.tf_weight
            FROM {schema_name}.article_term_stats ats
            JOIN {schema_name}.terms t ON t.id = ats.term_id
            WHERE ats.article_id = %s
            ORDER BY t.term
            """,
            (article_id,),
        )
        rows = cursor.fetchall()

    assert rows == [
        ("body", 2, pytest.approx(1 + math.log(2))),
        ("rally", 2, pytest.approx(1 + math.log(2))),
        ("title", 1, pytest.approx(1.0)),
    ]
