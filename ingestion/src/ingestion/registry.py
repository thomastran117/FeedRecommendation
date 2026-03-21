from ingestion.config import AppConfig, load_config
from ingestion.sources.base import ArticleDiscoverySource
from ingestion.sources.bbc import BBCNewsRssSource, BBC_RSS_URL


def get_sources(config: AppConfig | None = None) -> list[ArticleDiscoverySource]:
    active_config = config or load_config()
    sources: list[ArticleDiscoverySource] = []

    for feed_url in active_config.ingestion.feed_urls:
        if feed_url == BBC_RSS_URL:
            sources.append(BBCNewsRssSource(rss_feed_url=feed_url))
            continue

        raise ValueError(f"Unsupported feed URL configured: {feed_url}")

    return sources
