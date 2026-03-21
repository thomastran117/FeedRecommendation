# RSS Ingestion

The ingestion job lives under the top-level `ingestion/` folder and is intended to run as a cron-triggered Python process.

Configuration lives in `ingestion/application.yaml` and can be overridden with environment variables.

## Current v1 behavior

- fetch configured RSS feeds
- extract article links and RSS metadata
- normalize each article URL
- skip known articles by `normalized_url`
- scrape only unknown articles
- validate article title and body
- insert valid articles into the database
- update search index tables for newly inserted articles
- print a concise run summary with discovered, skipped, inserted, indexed, and failure counts

When deployed with Docker Compose, the ingestion container runs this job on a 15-minute cron schedule by default.

RSS is the only supported discovery path. There is no bootstrap crawler or crawler fallback in the current architecture.

## Responsibility split

The ingestion flow is intentionally split into two stages:

1. Discovery
   - each source exposes `discover_articles()`
   - the method returns normalized article links and any RSS metadata available for those links

2. Scraping
   - the scraper accepts a discovered article
   - it fetches the article page and extracts the normalized article result shape

The current persistence/indexing flow is:

- fetch RSS feeds
- extract article URLs
- normalize URLs
- skip known URLs
- scrape article page
- validate article
- store article
- update search index data

This keeps RSS parsing concerns separate from article-page parsing concerns.

## Combined indexing

Search and recommendation indexing currently use one combined article text built from the article title plus the article body.

- `title` and `body` remain separate fields on the article row
- indexing combines them into a single text representation for TF-IDF storage
- there are no separate title and body term statistics in v1
- any future title-specific boost belongs in the search scoring layer rather than a separate index in this version

## Source contract

Each RSS source implements:

- `discover_articles() -> list[DiscoveredArticle]`

`DiscoveredArticle` includes:

- `article_url`
- `normalized_url`
- `source_name`
- `source_url`
- `rss_feed_url`
- optional `title`
- optional `author`
- optional `published_at`

## Current source registry

The registry currently contains only the BBC News RSS source:

- `https://feeds.bbci.co.uk/news/rss.xml`

Additional sources should plug into the same discovery contract and return the same normalized discovery shape.

## Configuration

`application.yaml` currently supports:

- `database.url`
- `database.host`
- `database.port`
- `ingestion.schedule`
- `ingestion.feed_urls`

Environment variables override YAML values. Current overrides are:

- `THING_DATABASE_URL`
- `THING_DATABASE_HOST`
- `THING_DATABASE_PORT`
- `THING_INGESTION_SCHEDULE`

This makes it easy to change the database URL or port without editing the YAML file.
