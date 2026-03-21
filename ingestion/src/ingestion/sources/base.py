from __future__ import annotations

from typing import Protocol

from ingestion.models import DiscoveredArticle


class ArticleDiscoverySource(Protocol):
    def discover_articles(self) -> list[DiscoveredArticle]:
        ...
