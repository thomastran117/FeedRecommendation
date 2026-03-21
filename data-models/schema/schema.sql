CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    source_url TEXT,
    rss_feed_url TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ NOT NULL,
    body_length INTEGER NOT NULL CHECK (body_length >= 0),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    content_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX articles_published_at_idx ON articles (published_at DESC);

CREATE TABLE user_search_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    searched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX user_search_events_user_id_searched_at_idx
    ON user_search_events (user_id, searched_at DESC);

CREATE TABLE user_article_click_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    clicked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX user_article_click_events_user_id_clicked_at_idx
    ON user_article_click_events (user_id, clicked_at DESC);

CREATE INDEX user_article_click_events_article_id_clicked_at_idx
    ON user_article_click_events (article_id, clicked_at DESC);

CREATE INDEX user_article_click_events_user_id_article_id_clicked_at_idx
    ON user_article_click_events (user_id, article_id, clicked_at DESC);

CREATE TABLE terms (
    id BIGSERIAL PRIMARY KEY,
    term TEXT NOT NULL UNIQUE,
    document_frequency INTEGER NOT NULL DEFAULT 0 CHECK (document_frequency >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE article_term_stats (
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    term_id BIGINT NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    term_frequency INTEGER NOT NULL CHECK (term_frequency >= 0),
    tf_weight DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (article_id, term_id)
);

CREATE TABLE term_postings (
    term_id BIGINT NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tfidf_weight DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (term_id, article_id)
);

CREATE TYPE feed_type AS ENUM ('default', 'personalized');
CREATE TYPE feed_status AS ENUM ('ready', 'building', 'failed');

CREATE TABLE feeds (
    id BIGSERIAL PRIMARY KEY,
    feed_type feed_type NOT NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    algorithm_version TEXT,
    status feed_status NOT NULL DEFAULT 'ready',
    source_window_start TIMESTAMPTZ,
    source_window_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT feeds_default_requires_null_user
        CHECK (
            (feed_type = 'default' AND user_id IS NULL) OR
            (feed_type = 'personalized' AND user_id IS NOT NULL)
        )
);

CREATE UNIQUE INDEX feeds_single_default_idx
    ON feeds (feed_type)
    WHERE user_id IS NULL;

CREATE UNIQUE INDEX feeds_single_personalized_per_user_idx
    ON feeds (user_id)
    WHERE feed_type = 'personalized';

CREATE INDEX feeds_generated_at_idx ON feeds (generated_at DESC);

CREATE TABLE feed_items (
    feed_id BIGINT NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL CHECK (rank > 0),
    score DOUBLE PRECISION,
    recency_score DOUBLE PRECISION,
    popularity_score DOUBLE PRECISION,
    click_match_score DOUBLE PRECISION,
    search_match_score DOUBLE PRECISION,
    PRIMARY KEY (feed_id, rank),
    CONSTRAINT feed_items_unique_article_per_feed UNIQUE (feed_id, article_id)
);

CREATE TABLE article_popularity_daily (
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    bucket_date DATE NOT NULL,
    click_count INTEGER NOT NULL DEFAULT 0 CHECK (click_count >= 0),
    PRIMARY KEY (article_id, bucket_date)
);
