# Data Schema Reference

This document describes the canonical database model for the MVP.

The source of truth for schema definitions and migrations is the top-level `data-models/` folder.
Application-level ORM files may mirror parts of this model for querying, but they must not define schema ownership.

## Source-of-truth tables

### `users`

Identity and authentication records.

Key fields:
- `email` unique
- `password`

### `articles`

Canonical article storage.

Key fields:
- `url`
- `normalized_url` unique
- `source_name`
- `source_url`
- `rss_feed_url`
- `title`
- `body`
- `author`
- `published_at`
- `scraped_at`
- `body_length`
- `is_valid`

`normalized_url` is the cleaned canonical article URL used for deduplication.
It removes irrelevant differences such as tracking parameters, fragments, and host casing so the same article is not stored twice under slightly different URLs.

### `user_search_events`

Append-only search history.

Key fields:
- `user_id`
- `query_text`
- `normalized_query`
- `searched_at`

### `user_article_click_events`

Append-only article engagement history.

MVP tracks only `click` events.
There is no separate `view` event table or event type in the schema.

Key fields:
- `user_id`
- `article_id`
- `clicked_at`

## Search and indexing tables

### `terms`

One row per normalized token with aggregate document frequency.

### `article_term_stats`

Per-article term statistics used to support incremental indexing and downstream recomputation without reparsing full article bodies.

### `term_postings`

Postings list storage for query-time TF-IDF/cosine lookup.

## Feed tables

### `feeds`

Current feed metadata.

Rules:
- one global default feed exists at a time
- each user can have at most one personalized feed
- feed generation updates existing feed rows instead of creating snapshots

Key fields:
- `feed_type`
- `user_id`
- `generated_at`
- `algorithm_version`
- `status`
- `source_window_start`
- `source_window_end`

### `feed_items`

Current ordered feed contents for a feed.

Rules:
- items are replaced when a feed is regenerated
- each `rank` is unique within a feed
- each article appears at most once within a feed

Optional score fields are stored so ranking behavior is inspectable without adding a separate candidate-history model.

## Derived tables

### `article_popularity_daily`

Derived daily click aggregates per article.

This table is not a source of truth for engagement. Raw click rows remain authoritative.

## Lifecycle rules

- Schema changes start in `data-models/schema/`.
- Migration history is authored in `data-models/migrations/`.
- `docs/data-schema.md` and this document should stay aligned when the storage model changes.
- No new schema changes should be authored under application-owned migration folders.
