from __future__ import annotations

from datetime import UTC, datetime

from bs4 import BeautifulSoup
import requests

from ingestion.models import DiscoveredArticle, ScrapedArticle
from ingestion.normalize import normalize_url


def default_html_fetcher(url: str) -> str:
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "ThingIngestionBot/0.1"},
    )
    response.raise_for_status()
    return response.text


def scrape_article(
    article: DiscoveredArticle,
    html_fetcher=default_html_fetcher,
    scraped_at_factory=None,
) -> ScrapedArticle:
    html = html_fetcher(article.article_url)
    soup = BeautifulSoup(html, "html.parser")

    canonical_url = _read_meta_or_link(
        soup,
        ("link", {"rel": "canonical"}, "href"),
    )
    final_url = canonical_url or article.article_url
    title = _read_meta(soup, "property", "og:title") or _read_title(soup) or article.title
    if not title:
        raise ValueError(f"Unable to extract title from {article.article_url}")

    body = _extract_body(soup)
    if not body:
        raise ValueError(f"Unable to extract body from {article.article_url}")

    author = (
        _read_meta(soup, "name", "byl")
        or _read_meta(soup, "property", "article:author")
        or article.author
    )
    published_at = _parse_iso_datetime(
        _read_meta(soup, "property", "article:published_time")
        or _read_meta(soup, "name", "article:published_time")
    ) or article.published_at
    current_time = scraped_at_factory() if scraped_at_factory else datetime.now(UTC)

    return ScrapedArticle(
        url=final_url,
        normalized_url=normalize_url(final_url),
        source_name=article.source_name,
        source_url=article.source_url,
        rss_feed_url=article.rss_feed_url,
        title=title,
        body=body,
        author=author,
        published_at=published_at,
        scraped_at=current_time,
    )


def _read_meta(soup: BeautifulSoup, attr_name: str, attr_value: str) -> str | None:
    node = soup.find("meta", attrs={attr_name: attr_value})
    if not node:
        return None

    content = node.get("content")
    if not isinstance(content, str):
        return None

    stripped = content.strip()
    return stripped or None


def _read_meta_or_link(soup: BeautifulSoup, descriptor) -> str | None:
    tag_name, attrs, attribute = descriptor
    node = soup.find(tag_name, attrs=attrs)
    if not node:
        return None

    value = node.get(attribute)
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    return stripped or None


def _read_title(soup: BeautifulSoup) -> str | None:
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        return title or None
    return None


def _extract_body(soup: BeautifulSoup) -> str:
    paragraphs = [
        node.get_text(" ", strip=True)
        for node in soup.select('p[data-component="text-block"]')
        if node.get_text(" ", strip=True)
    ]

    if not paragraphs:
        article_node = soup.find("article")
        if article_node:
            paragraphs = [
                node.get_text(" ", strip=True)
                for node in article_node.find_all("p")
                if node.get_text(" ", strip=True)
            ]

    return "\n\n".join(paragraphs)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
