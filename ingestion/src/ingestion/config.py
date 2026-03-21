from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = Path("application.yaml")
DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/appdb"
DEFAULT_DATABASE_HOST = "localhost"
DEFAULT_DATABASE_PORT = 5432
DEFAULT_INGESTION_SCHEDULE = "*/15 * * * *"
DEFAULT_FEED_URLS = ["https://feeds.bbci.co.uk/news/rss.xml"]


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    host: str
    port: int


@dataclass(frozen=True)
class IngestionConfig:
    schedule: str
    feed_urls: list[str]


@dataclass(frozen=True)
class AppConfig:
    database: DatabaseConfig
    ingestion: IngestionConfig


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    raw_config = yaml.safe_load(path.read_text()) if path.exists() else {}

    database_section = raw_config.get("database", {})
    ingestion_section = raw_config.get("ingestion", {})

    database_url = os.getenv("THING_DATABASE_URL", database_section.get("url", DEFAULT_DATABASE_URL))
    database_host = os.getenv("THING_DATABASE_HOST", database_section.get("host", DEFAULT_DATABASE_HOST))
    database_port = int(os.getenv("THING_DATABASE_PORT", database_section.get("port", DEFAULT_DATABASE_PORT)))
    ingestion_schedule = os.getenv(
        "THING_INGESTION_SCHEDULE",
        ingestion_section.get("schedule", DEFAULT_INGESTION_SCHEDULE),
    )
    feed_urls = ingestion_section.get("feed_urls", DEFAULT_FEED_URLS)

    return AppConfig(
        database=DatabaseConfig(
            url=database_url,
            host=database_host,
            port=database_port,
        ),
        ingestion=IngestionConfig(
            schedule=ingestion_schedule,
            feed_urls=list(feed_urls),
        ),
    )
