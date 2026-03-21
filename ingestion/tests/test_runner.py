from datetime import UTC, datetime

from ingestion.models import DiscoveredArticle, ScrapedArticle
from ingestion.run import run


class DummySource:
    def __init__(self, articles):
        self._articles = articles

    def discover_articles(self):
        return self._articles


def build_article(index: int) -> DiscoveredArticle:
    return DiscoveredArticle(
        article_url=f"https://example.com/articles/{index}?utm_source=rss",
        normalized_url=f"https://example.com/articles/{index}",
        source_name="BBC News",
        source_url="https://www.bbc.com/news",
        rss_feed_url="https://feeds.bbci.co.uk/news/rss.xml",
        title=f"Article {index}",
        author=None,
        published_at=None,
    )


def build_scraped(article: DiscoveredArticle) -> ScrapedArticle:
    return ScrapedArticle(
        url=article.article_url,
        normalized_url=article.normalized_url,
        source_name=article.source_name,
        source_url=article.source_url,
        rss_feed_url=article.rss_feed_url,
        title=article.title or "Title",
        body=f"Body for {article.normalized_url}",
        author=article.author,
        published_at=article.published_at,
        scraped_at=datetime(2026, 3, 21, 10, 0, tzinfo=UTC),
    )


class FakeRepository:
    def __init__(self, existing_urls=None, fail_on_insert=None):
        self.existing_urls = set(existing_urls or [])
        self.fail_on_insert = set(fail_on_insert or [])
        self.inserted_articles = []
        self.next_article_id = 1

    def article_exists(self, normalized_url: str) -> bool:
        return normalized_url in self.existing_urls

    def insert_article(self, article: ScrapedArticle) -> int:
        if article.normalized_url in self.fail_on_insert:
            raise RuntimeError("insert failed")

        article_id = self.next_article_id
        self.next_article_id += 1
        self.inserted_articles.append((article_id, article))
        self.existing_urls.add(article.normalized_url)
        return article_id


class FakeIndexer:
    def __init__(self, fail_on_article_ids=None):
        self.fail_on_article_ids = set(fail_on_article_ids or [])
        self.indexed_article_ids = []

    def index_article(self, article_id: int, article: ScrapedArticle) -> None:
        if article_id in self.fail_on_article_ids:
            raise RuntimeError("index failed")

        self.indexed_article_ids.append(article_id)


def test_runner_skips_known_urls_and_indexes_new_articles():
    articles = [build_article(index) for index in range(3)]
    source = DummySource(articles)
    repository = FakeRepository(existing_urls={"https://example.com/articles/1"})
    indexer = FakeIndexer()

    summary = run(
        sources=[source],
        scrape_fn=build_scraped,
        repository=repository,
        indexer=indexer,
    )

    assert summary.discovered == 3
    assert summary.skipped == 1
    assert summary.inserted == 2
    assert summary.indexed == 2
    assert summary.scrape_failures == 0
    assert summary.persist_failures == 0
    assert [article_id for article_id, _ in repository.inserted_articles] == [1, 2]
    assert indexer.indexed_article_ids == [1, 2]


def test_runner_continues_after_scrape_and_persist_failures():
    articles = [build_article(index) for index in range(3)]
    source = DummySource(articles)
    repository = FakeRepository(fail_on_insert={"https://example.com/articles/2"})
    indexer = FakeIndexer()

    def flaky_scrape(article: DiscoveredArticle) -> ScrapedArticle:
        if article.normalized_url.endswith("/1"):
            raise RuntimeError("boom")
        return build_scraped(article)

    summary = run(
        sources=[source],
        scrape_fn=flaky_scrape,
        repository=repository,
        indexer=indexer,
    )

    assert summary.discovered == 3
    assert summary.skipped == 0
    assert summary.inserted == 1
    assert summary.indexed == 1
    assert summary.scrape_failures == 1
    assert summary.persist_failures == 1
    assert indexer.indexed_article_ids == [1]
