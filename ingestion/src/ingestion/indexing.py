from __future__ import annotations

from collections import Counter
import math
import re

from ingestion.models import ScrapedArticle


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def combine_article_text(title: str, body: str) -> str:
    return f"{title}\n\n{body}"


def tokenize_text(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def compute_term_frequencies(title: str, body: str) -> dict[str, int]:
    combined_text = combine_article_text(title, body)
    return dict(Counter(tokenize_text(combined_text)))


class ArticleIndexer:
    def __init__(self, connection, schema_name: str | None = None):
        self.connection = connection
        self.schema_name = schema_name

    def index_article(self, article_id: int, article: ScrapedArticle) -> None:
        term_counts = compute_term_frequencies(article.title, article.body)
        if not term_counts:
            return

        total_document_count = self._fetch_total_document_count()

        for term, term_frequency in term_counts.items():
            term_id, document_frequency = self._upsert_term_and_increment_frequency(term)
            tf_weight = 1.0 + math.log(term_frequency)
            tfidf_weight = tf_weight * math.log(total_document_count / document_frequency)

            with self.connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {self._qualify('article_term_stats')} (
                        article_id,
                        term_id,
                        term_frequency,
                        tf_weight
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (article_id, term_id, term_frequency, tf_weight),
                )
                cursor.execute(
                    f"""
                    INSERT INTO {self._qualify('term_postings')} (
                        term_id,
                        article_id,
                        tfidf_weight
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (term_id, article_id, tfidf_weight),
                )

    def _fetch_total_document_count(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {self._qualify('articles')}")
            return cursor.fetchone()[0]

    def _upsert_term_and_increment_frequency(self, term: str) -> tuple[int, int]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {self._qualify('terms')} (term, document_frequency)
                VALUES (%s, 0)
                ON CONFLICT (term) DO NOTHING
                """,
                (term,),
            )
            cursor.execute(
                f"""
                UPDATE {self._qualify('terms')}
                SET document_frequency = document_frequency + 1
                WHERE term = %s
                RETURNING id, document_frequency
                """,
                (term,),
            )
            term_id, document_frequency = cursor.fetchone()
            return term_id, document_frequency

    def _qualify(self, table_name: str) -> str:
        if not self.schema_name:
            return table_name
        return f"{self.schema_name}.{table_name}"
