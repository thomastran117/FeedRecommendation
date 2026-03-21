# Architecture

## Purpose

This project is a news ingestion, search, and recommendation system.

It ingests articles from external news sources, indexes them for search, and generates a feed for users. For the MVP, the system favors a smaller operational footprint over extra decoupling, with scheduled jobs doing the heavy lifting through a shared database.

The current stack choice is:

- Client: React + JavaScript
- Backend services: Python + FastAPI
- Persistence: Postgres
- Scheduling: cron-triggered jobs for ingestion/indexing and feed generation

## High-level goals

The architecture is optimized for:

- simple service boundaries
- low operational complexity
- availability over perfect freshness
- batch-oriented recommendation generation
- clear separation between scheduled data preparation, feed generation, and API serving

## High-level system layout

```text
React client
    ↓
REST service
    ↓
shared database

Ingestion + indexing cron job
        ↓
     shared database

Feed cron job → shared database
```

## Main components

### 1. Client

The client is a basic React application written in JavaScript.

Responsibilities:

- render the homepage/feed
- render search UI and results
- call the REST service for feed, article, and search data
- log user actions through backend endpoints

The client does not talk directly to ingestion or feed generation jobs.

### 2. REST service

The REST service is a FastAPI application that reads from and writes to the shared database.

Responsibilities:

- serve feed data
- serve search results
- serve article detail data
- record user search events
- record user click events
- expose data needed by the client

Non-responsibilities:

- no ingestion orchestration
- no feed batch generation
- no scheduled job execution

This service is intentionally independent from the cron jobs.

### 3. Ingestion and indexing job

The ingestion pipeline is triggered by cron every few minutes and performs article acquisition plus search indexing in the same run for now.

Responsibilities:

- fetch RSS feeds
- run a constrained web crawler to collect initial article URLs during bootstrap
- discover new article URLs
- normalize URLs
- scrape article pages
- clean article content
- validate that scraped articles are usable
- write articles to the shared database
- tokenize and preprocess article text
- update vocabulary and index structures
- maintain search-side data needed by TF-IDF/cosine search
- prepare article-side text representations used later by recommendations

For the MVP, ingestion and indexing stay together in one cron job to keep the system simple. We may split them into separate stages later if indexing work grows enough to justify more decoupling.

### 5. Feed generation job

The feed generation pipeline is also triggered by cron every few minutes. The current design uses a 15-minute batch interval.

Responsibilities:

- compute the global default feed
- compute personalized feeds for users who pass the personalization threshold
- update the current default feed and current per-user feeds in the database

The feed job does not serve requests directly. It only prepares data for the REST service.

## Shared database model

Multiple services write to the same database. This is acceptable in the current design because the services are operationally decoupled even though they share storage.

Schema definitions and migrations are owned by the top-level `data-models/` folder.
Application code may use an ORM for database access, but schema authority does not live in the app folder.

Broad table groups:

- article storage
- indexing/search storage
- user event storage
- feed storage
- article popularity/statistics

### Core article table

Recommended core fields:

- `article_id`
- `url`
- `normalized_url`
- `source`
- `title`
- `body`
- `author`
- `published_at`
- `scraped_at`
- `body_length`
- `is_valid`

Important rules:

- deduplicate on normalized URL
- store `title` and `body` separately
- keep `published_at` and `scraped_at` distinct
- keep source metadata simple on the article row for MVP

## Ingestion strategy

### Bootstrap phase

The first dataset is created through a constrained web crawler over archive, category, or pagination pages.

This is a one-time or occasional process used to seed the database with historical content.

The crawler is intentionally constrained and is meant to gather enough initial content for the MVP rather than behave like a broad general-purpose crawler.

### Ongoing ingestion phase

After bootstrap, ongoing ingestion is feed-driven.

Flow:

```text
cron trigger
→ fetch RSS feeds
→ extract article URLs
→ normalize URLs
→ skip known URLs
→ scrape article page
→ validate/clean article
→ store article
→ update search index data
```

No full BFS crawling is part of normal operation after bootstrap.

## Search design

Search is implemented with:

- inverted index
- TF-IDF
- cosine similarity
- small boosts such as title match and recency

### Search flow

```text
user query
→ preprocess query
→ lookup postings in inverted index
→ build candidate documents
→ score with TF-IDF cosine similarity
→ apply title and recency boosts
→ return ranked results
```

### Search indexing notes

- vocabulary is dynamic and expands as new articles are indexed
- sparse representations should be used rather than dense full-vocabulary vectors
- document frequencies and postings should be updated incrementally during the scheduled ingestion/indexing run
- full rebuilds on every new article should be avoided

### Search logging

Searches are part of the domain model, not just the UI.

Each user search should be logged with at least:

- `user_id`
- `query_text`
- `timestamp`

These events later feed the recommendation system.

## Recommendation and feed design

The system only needs recommendations for the feed.

It does not currently require a separate related-articles feature.

### Feed types

There are two feed modes:

#### Default feed

Used for:

- cold start users
- fallback when personalized feed data is unavailable

Default feed ranking is based on:

- recency
- popularity

This feed should always exist in precomputed form as a current stored row.

#### Personalized feed

Used only when a user has enough behavior data.

Personalization threshold:

- at least 5 searches
- at least 15 clicks

Until both thresholds are satisfied, the user remains on the default feed.

### Recommendation signals

Once the threshold is reached, personalized ranking combines:

- recency
- popularity
- click-based relevance
- search-based relevance

Conceptually:

```text
score = recency + popularity + clickMatch + searchMatch
```

#### Click signal

- represent articles with TF-IDF-style text features
- combine recently clicked article vectors into a user click profile
- compare candidate articles against that profile with cosine similarity

#### Search signal

- take the user's recent queries
- vectorize them into a query-interest profile
- compare candidate articles against that profile

### Candidate generation for personalized feeds

Do not score every article in the corpus.

Candidates should come from a union of:

- recent articles
- popular recent articles
- articles matching recent search terms
- articles similar to clicked articles

Then rank only that smaller candidate set.

### Batch feed generation

Feeds favor availability over perfect real-time freshness.

Current decision:

- precompute feeds every 15 minutes
- do not recompute on every user request
- after new clicks/searches, wait until the next batch run

This means:

- the default feed is recomputed on schedule and updated in place
- personalized feeds are recomputed on schedule and updated in place
- the REST service serves the current stored feed rows

### Feed serving behavior

When a user opens the app:

- if the user has fewer than 5 searches or fewer than 15 clicks, serve the default feed
- otherwise serve the current personalized feed for that user
- if a personalized feed row is missing, fall back to the default feed

## Service boundaries and coupling

The project deliberately avoids tight orchestration.

### Desired coupling model

- REST is independent from cron jobs
- feed generation is independent from request serving
- all services share the database, but their responsibilities stay distinct

This keeps the mental model simple:

- cron jobs prepare data
- REST serves data
- client renders data

## Key design decisions

### Availability over freshness

The feed is precomputed in batches rather than ranked in real time.

Why:

- simpler implementation
- predictable compute cost
- fast request serving
- acceptable staleness for the MVP

### Default feed as a first-class feature

The system always maintains a default feed.

Why:

- cold start support
- fallback path when personalized data is missing
- simpler serving logic

### No PageRank

Search is based on text relevance rather than a link graph.

Why:

- this is a news/article system rather than a general web search engine
- article text, title, recency, and popularity are more useful than page authority

### No real-time personalized reranking on request

The system uses scheduled feed generation instead.

Why:

- simpler operational model
- easier MVP implementation
- decoupling can be added later if needed

## MVP boundaries

Included in MVP:

- React frontend
- Python FastAPI backend
- shared database
- RSS-based ingestion
- constrained bootstrap web crawler
- single cron-based ingestion and indexing pipeline
- TF-IDF/cosine search
- default feed
- personalized feed after threshold
- 15-minute feed batch generation
- click event tracking

Not in MVP:

- category storage on articles
- real-time feed recomputation after every event
- view-event tracking
- collaborative filtering
- neural recommenders
- PageRank
- queue-based decoupling between ingestion and indexing
- broad general-purpose crawling after bootstrap

## Operational notes

- ingestion and feed generation should be safe to run repeatedly from cron
- scheduled ingestion/indexing runs should be idempotent where practical
- URL normalization is critical to avoid duplicate articles
- article validation should filter out empty or obviously broken scrapes before indexing
- feed generation should always leave a usable default feed available

## One-paragraph summary

This project is a news ingestion, search, and recommendation system built with a React client, a Python FastAPI backend, cron jobs, and a shared database. Articles are seeded with a constrained web crawler and then kept fresh through RSS-driven ingestion. For the MVP, the same scheduled ingestion job also updates the search index, while a separate batch feed job precomputes both a default cold-start feed and personalized feeds every 15 minutes. Search uses TF-IDF and cosine similarity, while personalization is unlocked only after a user reaches at least 5 searches and 15 clicks.
