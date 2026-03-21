from pathlib import Path

from ingestion.sources.bbc import BBCNewsRssSource


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_discover_articles_parses_bbc_feed_and_normalizes_urls():
    feed_xml = (FIXTURES_DIR / "bbc_feed.xml").read_text()
    source = BBCNewsRssSource(feed_fetcher=lambda _: feed_xml)

    articles = source.discover_articles()

    assert len(articles) == 6
    first = articles[0]
    assert first.source_name == "BBC News"
    assert first.source_url == "https://www.bbc.com/news"
    assert first.rss_feed_url == "https://feeds.bbci.co.uk/news/rss.xml"
    assert first.article_url == "https://www.bbc.com/news/articles/ce12345?utm_source=rss&utm_medium=feed#section"
    assert first.normalized_url == "https://www.bbc.com/news/articles/ce12345"
    assert first.title == "Article One"
    assert first.author == "BBC News"
    assert first.published_at.isoformat() == "2026-03-21T09:00:00+00:00"
