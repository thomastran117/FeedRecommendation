#!/bin/sh
set -eu

cd /app

python - <<'PY' > /app/.cron_env
import os

for key, value in sorted(os.environ.items()):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    print(f'export {key}="{escaped}"')
PY

SCHEDULE="$(PYTHONPATH=/app/src python - <<'PY'
from feed.config import load_config

print(load_config().feed.schedule)
PY
)"

cat > /etc/cron.d/thing-feed <<EOF
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin
PYTHONPATH=/app/src

${SCHEDULE} root /usr/local/bin/run-feed.sh >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

chmod 0644 /etc/cron.d/thing-feed

echo "Configured feed cron schedule: ${SCHEDULE}"

exec cron -f
