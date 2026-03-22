from datetime import UTC, datetime

from feed.models import ArticleCandidate
from feed.run import rank_default_feed, run


def build_candidate(
    article_id: int,
    *,
    published_at: datetime | None = None,
    scraped_at: datetime | None = None,
) -> ArticleCandidate:
    active_scraped_at = scraped_at or datetime(2026, 3, 21, 10, 0, tzinfo=UTC)
    article_time = published_at or active_scraped_at
    return ArticleCandidate(
        article_id=article_id,
        title=f"Article {article_id}",
        published_at=published_at,
        scraped_at=active_scraped_at,
        article_time=article_time,
    )


class FakeRepository:
    def __init__(self, candidates, popularity_by_article_id=None, fail_on_replace=False):
        self.candidates = candidates
        self.popularity_by_article_id = popularity_by_article_id or {}
        self.fail_on_replace = fail_on_replace
        self.feed_status_updates = []
        self.replaced_items = None
        self.feed_id = 101

    def upsert_default_feed(self, **kwargs):
        self.feed_status_updates.append(("upsert", kwargs["status"]))
        return self.feed_id

    def fetch_recent_valid_articles(self, **kwargs):
        return self.candidates

    def fetch_article_popularity(self, article_ids, **kwargs):
        return {article_id: self.popularity_by_article_id.get(article_id, 0) for article_id in article_ids}

    def replace_feed_items(self, feed_id, items):
        if self.fail_on_replace:
            raise RuntimeError("replace failed")
        self.replaced_items = (feed_id, items)

    def update_feed_status(self, feed_id, **kwargs):
        self.feed_status_updates.append((feed_id, kwargs["status"]))

    def transaction(self):
        class _Transaction:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return _Transaction()


def test_rank_default_feed_uses_recency_only_when_popularity_missing():
    candidates = [
        build_candidate(1, published_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC)),
        build_candidate(2, published_at=datetime(2026, 3, 21, 8, 0, tzinfo=UTC)),
    ]

    ranked = rank_default_feed(
        candidates=candidates,
        popularity_by_article_id={},
        recency_weight=0.7,
        popularity_weight=0.3,
        limit=50,
    )

    assert [item.article_id for item in ranked] == [2, 1]
    assert ranked[0].popularity_score == 0.0
    assert ranked[1].popularity_score == 0.0
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


def test_rank_default_feed_applies_popularity_and_breaks_ties_by_article_id():
    published_at = datetime(2026, 3, 21, 8, 0, tzinfo=UTC)
    candidates = [
        build_candidate(10, published_at=published_at),
        build_candidate(11, published_at=published_at),
    ]

    ranked = rank_default_feed(
        candidates=candidates,
        popularity_by_article_id={10: 0, 11: 0},
        recency_weight=0.7,
        popularity_weight=0.3,
        limit=50,
    )

    assert [item.article_id for item in ranked] == [11, 10]


def test_rank_default_feed_limits_to_top_n():
    candidates = [
        build_candidate(article_id, published_at=datetime(2026, 3, 21, article_id, 0, tzinfo=UTC))
        for article_id in range(1, 4)
    ]

    ranked = rank_default_feed(
        candidates=candidates,
        popularity_by_article_id={},
        recency_weight=0.7,
        popularity_weight=0.3,
        limit=2,
    )

    assert [item.article_id for item in ranked] == [3, 2]


def test_run_marks_feed_ready_and_writes_ranked_items():
    now = datetime(2026, 3, 21, 10, 15, tzinfo=UTC)
    candidates = [
        build_candidate(1, published_at=datetime(2026, 3, 20, 10, 0, tzinfo=UTC)),
        build_candidate(2, scraped_at=datetime(2026, 3, 21, 9, 0, tzinfo=UTC)),
    ]
    repository = FakeRepository(candidates, popularity_by_article_id={1: 10, 2: 0})

    summary = run(repository=repository, now=now, config_path="feed/tests/fixtures/application.test.yaml")

    assert summary.feed_id == 101
    assert summary.candidates_considered == 2
    assert summary.items_written == 2
    assert repository.replaced_items is not None
    assert [item.article_id for item in repository.replaced_items[1]] == [2, 1]
    assert repository.feed_status_updates[-1] == (101, "ready")


def test_run_marks_feed_failed_when_replacement_errors():
    now = datetime(2026, 3, 21, 10, 15, tzinfo=UTC)
    repository = FakeRepository([build_candidate(1)], fail_on_replace=True)

    try:
        run(repository=repository, now=now, config_path="feed/tests/fixtures/application.test.yaml")
    except RuntimeError as error:
        assert str(error) == "replace failed"
    else:
        raise AssertionError("Expected run() to raise when replacing items fails")

    assert repository.feed_status_updates[-1] == (101, "failed")
