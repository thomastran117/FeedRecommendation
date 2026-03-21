FROM python:3.14-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml application.yaml ./
COPY src ./src
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY run-ingestion.sh /usr/local/bin/run-ingestion.sh

RUN pip install --no-cache-dir .
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /usr/local/bin/run-ingestion.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
