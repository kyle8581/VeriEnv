#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove stale Next.js lock file
rm -f "${ROOT_DIR}/frontend/.next/dev/lock" 2>/dev/null || true

# Load local env if present (optional)
if [[ -f "${ROOT_DIR}/.env" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
fi

# Read ports from ports.json (standard pattern)
FRONTEND_PORT="${FRONTEND_PORT:-$(python3 -c 'import json; p=json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"]; print(p.get("FRONTEND_PORT") or p.get("WEB_PORT") or p.get("UI_PORT") or p.get("PORT"))')}"
BACKEND_PORT="${BACKEND_PORT:-$(python3 -c 'import json; p=json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"]; print(p.get("BACKEND_PORT") or p.get("API_PORT") or p.get("PORT"))')}"
WEB_PORT="${FRONTEND_PORT}"
API_PORT="${BACKEND_PORT}"

export NEXT_PUBLIC_WEB_URL="${NEXT_PUBLIC_WEB_URL:-http://localhost:${WEB_PORT}}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-}"
export API_INTERNAL_URL="${API_INTERNAL_URL:-http://127.0.0.1:${API_PORT}}"

mkdir -p "${ROOT_DIR}/.data"
DB_PATH="${ROOT_DIR}/.data/discogs.db"
export DATABASE_URL="${DATABASE_URL:-sqlite+pysqlite:////${DB_PATH}}"
export JWT_SECRET="${JWT_SECRET:-dev_secret_change_me}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:${WEB_PORT}}"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "DB not found; seeding initial data..."
  "${ROOT_DIR}/reset_servers.sh"
fi

cleanup() {
  echo "Shutting down..."
  if [[ -n "${API_PID:-}" ]] && kill -0 "${API_PID}" 2>/dev/null; then
    kill "${API_PID}" || true
  fi
  if [[ -n "${WEB_PID:-}" ]] && kill -0 "${WEB_PID}" 2>/dev/null; then
    kill "${WEB_PID}" || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting FastAPI on ${API_INTERNAL_URL} (port ${API_PORT})"
PYTHONPATH="${ROOT_DIR}/backend" uvicorn app.main:app --app-dir "${ROOT_DIR}/backend" --host 0.0.0.0 --port "${API_PORT}" &
API_PID=$!

echo "Starting Next.js on http://localhost:${WEB_PORT}"
cd "${ROOT_DIR}/frontend"
npm install --silent
if [ ! -f .next/BUILD_ID ]; then npm run build --silent; fi
npm run start --silent -- -p "${WEB_PORT}" &
WEB_PID=$!

echo "Servers running:"
echo "- Web: http://localhost:${WEB_PORT}"
echo "- Public API: http://localhost:${WEB_PORT}/api/backend"
echo "- Internal API: ${API_INTERNAL_URL}"

wait "${API_PID}" "${WEB_PID}"

