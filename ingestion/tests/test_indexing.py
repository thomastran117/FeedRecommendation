import math

from ingestion.indexing import combine_article_text, compute_term_frequencies, tokenize_text


def test_tokenize_text_uses_simple_lowercase_combined_tokens():
    tokens = tokenize_text("Breaking News\n\nMarkets rally, rally again.")

    assert tokens == ["breaking", "news", "markets", "rally", "rally", "again"]


def test_combine_article_text_includes_title_and_body():
    combined = combine_article_text("Big Title", "Body paragraph")

    assert combined == "Big Title\n\nBody paragraph"


def test_compute_term_frequencies_counts_tokens_from_combined_text():
    counts = compute_term_frequencies("Title title", "Body title body")

    assert counts == {
        "title": 3,
        "body": 2,
    }


def test_tf_weight_formula_is_log_scaled():
    counts = compute_term_frequencies("One", "one one one")

    tf_weight = 1 + math.log(counts["one"])

    assert tf_weight == 1 + math.log(4)
