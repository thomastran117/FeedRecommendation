from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = Path("application.yaml")
DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/appdb"
DEFAULT_DATABASE_HOST = "localhost"
DEFAULT_DATABASE_PORT = 5432
DEFAULT_FEED_SCHEDULE = "*/15 * * * *"
DEFAULT_ARTICLE_WINDOW_DAYS = 7
DEFAULT_DEFAULT_FEED_SIZE = 50
DEFAULT_RECENCY_WEIGHT = 0.7
DEFAULT_POPULARITY_WEIGHT = 0.3


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    host: str
    port: int


@dataclass(frozen=True)
class FeedConfig:
    schedule: str
    article_window_days: int
    default_feed_size: int
    recency_weight: float
    popularity_weight: float


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    feed: FeedConfig


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    raw_config = yaml.safe_load(path.read_text()) if path.exists() else {}

    database_section = raw_config.get("database", {})
    feed_section = raw_config.get("feed", {})

    database_url = os.getenv("THING_DATABASE_URL", database_section.get("url", DEFAULT_DATABASE_URL))
    database_host = os.getenv("THING_DATABASE_HOST", database_section.get("host", DEFAULT_DATABASE_HOST))
    database_port = int(os.getenv("THING_DATABASE_PORT", database_section.get("port", DEFAULT_DATABASE_PORT)))
    feed_schedule = os.getenv(
        "THING_FEED_SCHEDULE",
        feed_section.get("schedule", DEFAULT_FEED_SCHEDULE),
    )
    article_window_days = int(
        os.getenv(
            "THING_FEED_ARTICLE_WINDOW_DAYS",
            feed_section.get("article_window_days", DEFAULT_ARTICLE_WINDOW_DAYS),
        )
    )
    default_feed_size = int(
        os.getenv(
            "THING_FEED_DEFAULT_FEED_SIZE",
            feed_section.get("default_feed_size", DEFAULT_DEFAULT_FEED_SIZE),
        )
    )
    recency_weight = float(
        os.getenv(
            "THING_FEED_RECENCY_WEIGHT",
            feed_section.get("recency_weight", DEFAULT_RECENCY_WEIGHT),
        )
    )
    popularity_weight = float(
        os.getenv(
            "THING_FEED_POPULARITY_WEIGHT",
            feed_section.get("popularity_weight", DEFAULT_POPULARITY_WEIGHT),
        )
    )

    return AppConfig(
        database=DatabaseConfig(
            url=database_url,
            host=database_host,
            port=database_port,
        ),
        feed=FeedConfig(
            schedule=feed_schedule,
            article_window_days=article_window_days,
            default_feed_size=default_feed_size,
            recency_weight=recency_weight,
            popularity_weight=popularity_weight,
        ),
    )
