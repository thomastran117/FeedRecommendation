from __future__ import annotations

from contextlib import nullcontext
import sys

from ingestion.config import load_config
from ingestion.database import create_connection
from ingestion.indexing import ArticleIndexer
from ingestion.models import DiscoveredArticle, IngestionSummary, ScrapedArticle
from ingestion.registry import get_sources
from ingestion.repository import ArticleRepository
from ingestion.scraper import scrape_article


def run(
    sources=None,
    scrape_fn=None,
    repository=None,
    indexer=None,
    config_path: str | None = None,
) -> IngestionSummary:
    app_config = load_config(config_path)
    article_sources = sources if sources is not None else get_sources(app_config)
    scraper = scrape_fn if scrape_fn is not None else scrape_article
    should_close_connection = repository is None or indexer is None
    connection = None

    if repository is None or indexer is None:
        connection = create_connection(app_config)
        repository = repository or ArticleRepository(connection)
        indexer = indexer or ArticleIndexer(connection)

    summary = IngestionSummary()

    try:
        discovered: list[DiscoveredArticle] = []
        for source in article_sources:
            discovered.extend(source.discover_articles())

        summary = IngestionSummary(discovered=len(discovered))

        for article in discovered:
            if repository.article_exists(article.normalized_url):
                summary = _replace_summary(summary, skipped=summary.skipped + 1)
                continue

            try:
                scraped = scraper(article)
            except Exception as error:
                print(f"Failed to scrape {article.normalized_url}: {error}", file=sys.stderr)
                summary = _replace_summary(summary, scrape_failures=summary.scrape_failures + 1)
                continue

            if not _is_valid_article(scraped):
                summary = _replace_summary(summary, persist_failures=summary.persist_failures + 1)
                continue

            try:
                transaction = repository.transaction() if hasattr(repository, "transaction") else nullcontext()
                with transaction:
                    article_id = repository.insert_article(scraped)
                    indexer.index_article(article_id, scraped)
            except Exception as error:
                if hasattr(repository, "is_duplicate_error") and repository.is_duplicate_error(error):
                    summary = _replace_summary(summary, skipped=summary.skipped + 1)
                    continue
                print(f"Failed to persist {article.normalized_url}: {error}", file=sys.stderr)
                summary = _replace_summary(summary, persist_failures=summary.persist_failures + 1)
                continue

            summary = _replace_summary(
                summary,
                inserted=summary.inserted + 1,
                indexed=summary.indexed + 1,
            )

        print(
            "discovered={discovered} skipped={skipped} inserted={inserted} "
            "indexed={indexed} scrape_failures={scrape_failures} persist_failures={persist_failures}".format(
                **summary.__dict__
            )
        )
        return summary
    finally:
        if should_close_connection and connection is not None:
            connection.close()


def _is_valid_article(article: ScrapedArticle) -> bool:
    return bool(article.title and article.title.strip() and article.body and article.body.strip())


def _replace_summary(summary: IngestionSummary, **changes) -> IngestionSummary:
    values = summary.__dict__.copy()
    values.update(changes)
    return IngestionSummary(**values)


if __name__ == "__main__":
    run()
