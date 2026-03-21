from datetime import UTC, datetime
from pathlib import Path

from ingestion.models import DiscoveredArticle
from ingestion.scraper import scrape_article


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_scrape_article_extracts_bbc_title_and_body():
    article_html = (FIXTURES_DIR / "bbc_article.html").read_text()
    discovered = DiscoveredArticle(
        article_url="https://www.bbc.com/news/articles/ce12345",
        normalized_url="https://www.bbc.com/news/articles/ce12345",
        source_name="BBC News",
        source_url="https://www.bbc.com/news",
        rss_feed_url="https://feeds.bbci.co.uk/news/rss.xml",
        title="RSS Title",
        author=None,
        published_at=None,
    )

    scraped = scrape_article(
        discovered,
        html_fetcher=lambda _: article_html,
        scraped_at_factory=lambda: datetime(2026, 3, 21, 9, 30, tzinfo=UTC),
    )

    assert scraped.url == "https://www.bbc.com/news/articles/ce12345"
    assert scraped.normalized_url == "https://www.bbc.com/news/articles/ce12345"
    assert scraped.title == "BBC Test Headline"
    assert scraped.author == "Test Author"
    assert scraped.published_at.isoformat() == "2026-03-21T08:15:00+00:00"
    assert scraped.body == "First paragraph of article body.\n\nSecond paragraph of article body."
    assert scraped.scraped_at.isoformat() == "2026-03-21T09:30:00+00:00"
