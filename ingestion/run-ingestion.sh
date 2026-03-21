#!/bin/sh
set -eu

if [ -f /app/.cron_env ]; then
    . /app/.cron_env
fi

cd /app
exec /usr/local/bin/python -m ingestion.run
