from pathlib import Path

from feed.config import AppConfig, load_config


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_config_reads_application_yaml_values():
    config = load_config(FIXTURES_DIR / "application.test.yaml")

    assert config.database.url == "postgresql://yaml-user:yaml-pass@yaml-host:6543/yaml-db"
    assert config.database.host == "yaml-host"
    assert config.database.port == 6543
    assert config.feed.schedule == "*/15 * * * *"
    assert config.feed.article_window_days == 7
    assert config.feed.default_feed_size == 50
    assert config.feed.recency_weight == 0.7
    assert config.feed.popularity_weight == 0.3


def test_environment_variables_override_yaml_values(monkeypatch):
    monkeypatch.setenv("THING_DATABASE_URL", "postgresql://env-user:env-pass@env-host:7777/env-db")
    monkeypatch.setenv("THING_DATABASE_HOST", "env-host")
    monkeypatch.setenv("THING_DATABASE_PORT", "7777")
    monkeypatch.setenv("THING_FEED_SCHEDULE", "*/10 * * * *")
    monkeypatch.setenv("THING_FEED_ARTICLE_WINDOW_DAYS", "14")
    monkeypatch.setenv("THING_FEED_DEFAULT_FEED_SIZE", "25")
    monkeypatch.setenv("THING_FEED_RECENCY_WEIGHT", "0.9")
    monkeypatch.setenv("THING_FEED_POPULARITY_WEIGHT", "0.1")

    config = load_config(FIXTURES_DIR / "application.test.yaml")

    assert config.database.url == "postgresql://env-user:env-pass@env-host:7777/env-db"
    assert config.database.host == "env-host"
    assert config.database.port == 7777
    assert config.feed.schedule == "*/10 * * * *"
    assert config.feed.article_window_days == 14
    assert config.feed.default_feed_size == 25
    assert config.feed.recency_weight == 0.9
    assert config.feed.popularity_weight == 0.1


def test_default_config_path_loads_application_yaml_from_feed_root(tmp_path, monkeypatch):
    config_path = tmp_path / "application.yaml"
    config_path.write_text(
        "\n".join(
            [
                "database:",
                "  url: postgresql://postgres:postgres@localhost:5432/appdb",
                "  host: localhost",
                "  port: 5432",
                "feed:",
                "  schedule: '*/15 * * * *'",
                "  article_window_days: 7",
                "  default_feed_size: 50",
                "  recency_weight: 0.7",
                "  popularity_weight: 0.3",
            ]
        )
    )

    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert isinstance(config, AppConfig)
    assert config.feed.default_feed_size == 50
