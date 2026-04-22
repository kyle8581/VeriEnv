#!/bin/sh
set -e
echo "[entrypoint] Starting backend..."
if [ ! -f /app/data/app.db ] && [ ! -f /app/app.db ]; then
    echo "[entrypoint] No database found, running seed..."
    python3 -m app.seed 2>/dev/null || python3 scripts/seed.py 2>/dev/null || true
fi
if [ "${RESET_DB:-0}" = "1" ] && [ -f /app/data/app.db.seed ]; then
    cp /app/data/app.db.seed /app/data/app.db
fi
exec "$@"
