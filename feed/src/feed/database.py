from __future__ import annotations

import psycopg

from feed.config import AppConfig, load_config


def create_connection(config: AppConfig | None = None):
    active_config = config or load_config()
    return psycopg.connect(active_config.database.url, autocommit=True)
