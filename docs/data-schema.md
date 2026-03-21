# Data Schema

The database model is defined from the top-level `data-models/` folder, not from application ORM files.

Canonical locations:
- `data-models/schema/` for schema definitions
- `data-models/migrations/` for SQL migrations
- `data-models/docs/schema.md` for the detailed storage reference

## MVP table groups

Source-of-truth tables:
- `users`
- `articles`
- `user_search_events`
- `user_article_click_events`
- `feeds`
- `feed_items`

Search/index tables:
- `terms`
- `article_term_stats`
- `term_postings`

Derived tables:
- `article_popularity_daily`

## Important rules

- `normalized_url` is the canonical deduplication key for articles.
- Article rows do not store `category` in the MVP schema.
- The MVP tracks only `click` article engagement events.
- There is one current default feed and at most one current personalized feed per user.
- Feed generation updates existing feed rows and replaces their `feed_items`.
- `articles.source_name` is stored but not indexed by default because there is no current feature that depends on source-based lookup.

## Source of truth vs derived state

Source-of-truth behavior data:
- `user_search_events`
- `user_article_click_events`

Derived state:
- `term_postings`
- `article_term_stats`
- `article_popularity_daily`
- current feed ordering and score columns

Derived tables may be rebuilt from source data if needed.

## Normalized URL

A normalized URL is the cleaned canonical form of an article URL used to deduplicate content.
It should remove differences that do not change article identity, such as tracking query parameters, URL fragments, and host casing differences.

For the detailed table-by-table reference, use [`data-models/docs/schema.md`](/Users/imanullah/Documents/dev/Thing/data-models/docs/schema.md).
