# Decisions

## Purpose

This document captures key architectural and design decisions made during the development of the news ingestion, search, and recommendation system.  
It exists to give future contributors and agents clear context on *why* the system is designed the way it is.

---

## 1. Data Ingestion Strategy

### Decision
Use **RSS-based ingestion** for article discovery.

### Reasoning
- RSS provides structured, reliable, and low-cost updates
- Keeps the ingestion boundary simple and deterministic
- Avoids crawler complexity and irrelevant-page discovery

---

## 2. No Web Crawler

### Decision
Do **not implement a web crawler** for article discovery in the MVP.

### Reasoning
- Not needed for a news-focused system
- RSS provides sufficient coverage of new content
- Simplifies architecture and reduces compute

---

## 3. Dynamic Vocabulary

### Decision
Use a **dynamic vocabulary** that grows as new articles are ingested.

### Reasoning
- New words constantly appear in news
- Avoids expensive re-indexing
- Works naturally with sparse representations

---

## 4. Search Design

### Decision
Use:
- Inverted index
- TF-IDF
- Cosine similarity

### Explicitly NOT used
- PageRank
- Graph-based ranking

### Reasoning
- News articles do not form a strong link graph
- Text relevance is more important than authority
- Matches course scope and expectations

---

## 5. Incremental Indexing

### Decision
Update index **incrementally** during the scheduled ingestion/indexing workflow.

### Reasoning
- Avoid full index rebuilds
- Efficient for repeated cron-driven ingestion runs
- Keeps system responsive

---

## 6. Combined Article Indexing

### Decision
Index each article as one combined text document built from its title and body.

### Reasoning
- Fits the current schema without adding separate field-specific index tables
- Works for both search and recommendation features in the MVP
- Keeps title-aware relevance as a later scoring concern rather than a schema change now

---

## 7. Recommendation System Approach

### Decision
Use a **hybrid recommender** based on:
- recency
- popularity
- click similarity
- search similarity

### Reasoning
- Works well with small datasets
- Handles cold start naturally
- No need for complex ML models

---

## 8. Cold Start Strategy

### Decision
Users remain on default feed until:
- at least 5 searches
- at least 15 clicks

### Reasoning
- Ensures enough signal before personalization
- Avoids poor early recommendations
- Simple and deterministic rule

---

## 9. Default Feed

### Decision
Default feed is based on:
- recency
- popularity

### Reasoning
- Provides strong fallback
- Works for new users
- Simple to compute and maintain

---

## 10. Personalized Feed

### Decision
Personalized feed uses:
- click profile (article similarity)
- search profile (query similarity)

### Reasoning
- Captures both user behavior and intent
- Reuses TF-IDF infrastructure
- Avoids dependency on categories

---

## 11. No Category Normalization

### Decision
Do **not store categories in the MVP article schema** and do not rely on them for recommendations.

### Reasoning
- Different sources use inconsistent category labels
- Adds ingestion complexity and schema noise
- Text-based similarity is more reliable

---

## 12. Candidate Generation Strategy

### Decision
Do **not score entire corpus**.

Instead, generate candidates from:
- recent articles
- popular articles
- search overlap
- click similarity

### Reasoning
- Reduces compute cost
- Improves performance
- Aligns with real-world systems

---

## 13. Feed Generation Strategy

### Decision
Use **batch feed generation every 15 minutes**.

### Reasoning
- Favors availability over real-time freshness
- Simplifies serving layer
- Keeps request handling lightweight in the REST service

---

## 14. No Real-Time Feed Updates

### Decision
Do not update feed immediately after user actions.

### Reasoning
- Acceptable staleness for MVP
- Reduces system complexity
- Batch updates are sufficient

---

## 15. Precomputed Feeds

### Decision
Store:
- default feed
- user-specific feeds

### Reasoning
- Fast retrieval
- Decouples serving from computation
- Improves reliability

---

## 16. Service Architecture

### Decision
Use a small set of MVP services:
- Node/Express REST API service
- scheduled ingestion and indexing job
- scheduled feed generation job

Connected via:
- shared database

### Reasoning
- Clear separation of concerns
- Lower operational complexity for the MVP
- Easier to build and debug early

---

## 17. Ingestion and Indexing in One Job

### Decision
Run ingestion and indexing in the same cron-triggered workflow for now.

### Reasoning
- Keeps the MVP simpler to implement
- Avoids introducing queue infrastructure too early
- We can split these stages later if indexing work grows

---

## 18. YAML Config With Environment Overrides

### Decision
Store ingestion runtime defaults in `application.yaml` and allow environment variables to override them.

### Reasoning
- Keeps local defaults easy to inspect and edit
- Makes deployment configuration straightforward in Docker Compose
- Allows database URL and port changes without changing code

---

## 19. Defer Extra Decoupling Until After MVP

### Decision
Do not introduce queue-based decoupling between ingestion and indexing yet.

Use:
- shared database
- cron-triggered jobs

Add more decoupling later only if scale or reliability needs justify it.

### Reasoning
- Keeps the architecture easier to understand
- Reduces moving parts during early product development
- Preserves a clear path to split the workflow later

---

## 20. Feed Scope

### Decision
Recommendation system is used **only for the feed**.

### Reasoning
- Reduces system scope
- Avoids unnecessary features (e.g., related articles initially)

---

## 21. Click-Only Engagement Tracking

### Decision
Track only `click` as the article engagement event for the MVP.

### Reasoning
- Simplifies the event model
- Keeps personalization logic focused on one strong signal
- Avoids ambiguous overlap between click and view semantics

---

## 22. Current-State Feed Storage

### Decision
Store one current default feed and one current personalized feed per user, updating those rows in place during feed generation.

### Reasoning
- Simplifies feed lookup and replacement logic
- Matches the requirement that a user has one feed at a time
- Avoids carrying snapshot history that the MVP does not need

---

## 23. Database Definitions Live In `data-models/`

### Decision
Use the top-level `data-models/` folder as the only source of truth for schema definitions and migrations.

### Reasoning
- Keeps database ownership outside any single application service
- Prevents ORM schema files from becoming a second source of truth
- Makes schema, migration history, and storage documentation easier to discover
- Keeps MVP focused

---

## 24. Simplicity Over Perfection

### Decision
Favor:
- simple heuristics
- understandable logic
- deterministic rules
- lower operational complexity

Over:
- complex ML models
- heavy optimization
- extra infrastructure before it is needed

### Reasoning
- Aligns with project scope
- Easier to debug and explain
- Faster to implement

---

## Summary

The system prioritizes:
- simplicity
- low operational complexity
- availability
- incremental computation

While intentionally avoiding:
- unnecessary complexity
- heavy real-time computation
- queue-based decoupling before it is needed
- crawler-based article discovery
