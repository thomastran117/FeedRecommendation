from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from feed import ALGORITHM_VERSION
from feed.config import AppConfig, DatabaseConfig, FeedConfig
from feed.database import create_connection
from feed.models import RankedFeedItem
from feed.repository import FeedRepository
from feed.run import run


SCHEMA_SQL = Path(__file__).resolve().parents[2] / "data-models" / "schema" / "schema.sql"


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
                feed=FeedConfig(
                    schedule="*/15 * * * *",
                    article_window_days=7,
                    default_feed_size=50,
                    recency_weight=0.7,
                    popularity_weight=0.3,
                ),
            )
        )
    except Exception as error:
        pytest.skip(f"Postgres not available for integration test: {error}")

    schema_name = "feed_test_schema"

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


def _insert_article(connection, schema_name: str, *, article_id: int, published_at, scraped_at, is_valid=True):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {schema_name}.articles (
                id,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                article_id,
                f"https://example.com/articles/{article_id}",
                f"https://example.com/articles/{article_id}",
                "BBC News",
                "https://www.bbc.com/news",
                "https://feeds.bbci.co.uk/news/rss.xml",
                f"Article {article_id}",
                "Body text",
                None,
                published_at,
                scraped_at,
                len("Body text"),
                is_valid,
            ),
        )


def test_repository_replaces_feed_items_for_same_default_feed(integration_connection):
    connection, schema_name = integration_connection
    repository = FeedRepository(connection, schema_name=schema_name)
    now = datetime(2026, 3, 21, 10, 15, tzinfo=UTC)

    _insert_article(
        connection,
        schema_name,
        article_id=1,
        published_at=now - timedelta(days=1),
        scraped_at=now - timedelta(days=1),
    )
    _insert_article(
        connection,
        schema_name,
        article_id=2,
        published_at=now - timedelta(hours=1),
        scraped_at=now - timedelta(hours=1),
    )
    connection.commit()

    feed_id = repository.upsert_default_feed(
        generated_at=now,
        algorithm_version=ALGORITHM_VERSION,
        status="building",
        source_window_start=now - timedelta(days=7),
        source_window_end=now,
    )
    repository.replace_feed_items(
        feed_id,
        [
            RankedFeedItem(
                article_id=1,
                rank=1,
                score=1.0,
                recency_score=1.0,
                popularity_score=0.0,
            )
        ],
    )
    repository.replace_feed_items(
        feed_id,
        [
            RankedFeedItem(
                article_id=2,
                rank=1,
                score=0.8,
                recency_score=0.8,
                popularity_score=0.0,
            )
        ],
    )

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT id, status FROM {schema_name}.feeds WHERE feed_type = 'default'"
        )
        feed_rows = cursor.fetchall()
        cursor.execute(
            f"SELECT article_id, rank FROM {schema_name}.feed_items WHERE feed_id = %s ORDER BY rank",
            (feed_id,),
        )
        item_rows = cursor.fetchall()

    assert feed_rows == [(feed_id, "building")]
    assert item_rows == [(2, 1)]


def test_run_generates_default_feed_with_metadata_and_scores(integration_connection):
    connection, schema_name = integration_connection
    repository = FeedRepository(connection, schema_name=schema_name)
    now = datetime(2026, 3, 21, 10, 15, tzinfo=UTC)

    _insert_article(
        connection,
        schema_name,
        article_id=1,
        published_at=now - timedelta(days=1),
        scraped_at=now - timedelta(days=1),
    )
    _insert_article(
        connection,
        schema_name,
        article_id=2,
        published_at=None,
        scraped_at=now - timedelta(hours=2),
    )
    _insert_article(
        connection,
        schema_name,
        article_id=3,
        published_at=now - timedelta(days=10),
        scraped_at=now - timedelta(days=10),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {schema_name}.article_popularity_daily (article_id, bucket_date, click_count)
            VALUES (%s, %s, %s)
            """,
            (1, now.date(), 5),
        )
    connection.commit()

    summary = run(repository=repository, now=now, config_path="feed/tests/fixtures/application.test.yaml")

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                id,
                feed_type,
                generated_at,
                algorithm_version,
                status,
                source_window_start,
                source_window_end
            FROM {schema_name}.feeds
            """
        )
        feed_row = cursor.fetchone()
        cursor.execute(
            f"""
            SELECT article_id, rank, score, recency_score, popularity_score
            FROM {schema_name}.feed_items
            WHERE feed_id = %s
            ORDER BY rank
            """,
            (summary.feed_id,),
        )
        item_rows = cursor.fetchall()

    assert summary.candidates_considered == 2
    assert summary.items_written == 2
    assert feed_row[1] == "default"
    assert feed_row[3] == ALGORITHM_VERSION
    assert feed_row[4] == "ready"
    assert feed_row[5] == now - timedelta(days=7)
    assert feed_row[6] == now
    assert item_rows[0][0] == 2
    assert item_rows[0][4] == pytest.approx(0.0)
    assert item_rows[1][0] == 1
    assert item_rows[1][4] == pytest.approx(1.0)
