#!/bin/sh
set -e
echo "[entrypoint] Starting frontend..."
if [ -f prisma/schema.prisma ]; then
    npx prisma migrate deploy 2>/dev/null || true
    if [ ! -f dev.db ] || [ "${RESET_DB:-0}" = "1" ]; then
        npx prisma db seed 2>/dev/null || npm run db:seed 2>/dev/null || true
    fi
fi
exec "$@"
