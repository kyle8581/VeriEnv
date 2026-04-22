#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load local env if present (optional)
if [[ -f "${ROOT_DIR}/.env" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
fi

mkdir -p "${ROOT_DIR}/.data"

DB_PATH="${ROOT_DIR}/.data/discogs.db"
export DATABASE_URL="sqlite+pysqlite:////${DB_PATH}"
export JWT_SECRET="${JWT_SECRET:-dev_secret_change_me}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:12042}"

echo "Resetting DB at ${DB_PATH}"
rm -f "${DB_PATH}"

echo "Running migrations..."
(cd "${ROOT_DIR}/backend" && DATABASE_URL="sqlite+pysqlite:///../.data/discogs.db" PYTHONPATH="." alembic -c alembic.ini upgrade head)

echo "Seeding realistic data..."
(cd "${ROOT_DIR}" && PYTHONPATH="backend" python -m app.db.seed)

echo "Done."

