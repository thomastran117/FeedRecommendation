from pathlib import Path

from ingestion.config import AppConfig, load_config


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_config_reads_application_yaml_values():
    config = load_config(FIXTURES_DIR / "application.test.yaml")

    assert config.database.url == "postgresql://yaml-user:yaml-pass@yaml-host:6543/yaml-db"
    assert config.database.host == "yaml-host"
    assert config.database.port == 6543
    assert config.ingestion.schedule == "*/15 * * * *"
    assert config.ingestion.feed_urls == ["https://feeds.bbci.co.uk/news/rss.xml"]


def test_environment_variables_override_yaml_values(monkeypatch):
    monkeypatch.setenv("THING_DATABASE_URL", "postgresql://env-user:env-pass@env-host:7777/env-db")
    monkeypatch.setenv("THING_DATABASE_HOST", "env-host")
    monkeypatch.setenv("THING_DATABASE_PORT", "7777")
    monkeypatch.setenv("THING_INGESTION_SCHEDULE", "*/10 * * * *")

    config = load_config(FIXTURES_DIR / "application.test.yaml")

    assert config.database.url == "postgresql://env-user:env-pass@env-host:7777/env-db"
    assert config.database.host == "env-host"
    assert config.database.port == 7777
    assert config.ingestion.schedule == "*/10 * * * *"


def test_default_config_path_loads_application_yaml_from_ingestion_root(tmp_path, monkeypatch):
    config_path = tmp_path / "application.yaml"
    config_path.write_text(
        "\n".join(
            [
                "database:",
                "  url: postgresql://postgres:postgres@localhost:5432/appdb",
                "  host: localhost",
                "  port: 5432",
                "ingestion:",
                "  schedule: '*/15 * * * *'",
                "  feed_urls:",
                "    - https://feeds.bbci.co.uk/news/rss.xml",
            ]
        )
    )

    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert isinstance(config, AppConfig)
    assert config.database.port == 5432
