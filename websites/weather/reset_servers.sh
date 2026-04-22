#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_PORT="$(python -c 'import json;print(json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"]["PORT"])')"
BACKEND_PORT="${BACKEND_PORT:-12142}"

kill_pidfile () {
  local pidfile="$1"
  if [ -f "$pidfile" ]; then
    local pid
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      sleep 0.3
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$pidfile"
  fi
}

kill_port () {
  local port="$1"
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    pids="$(fuser -n tcp "$port" 2>/dev/null || true)"
  fi
  if [ -n "$pids" ]; then
    # shellcheck disable=SC2086
    kill $pids >/dev/null 2>&1 || true
    sleep 0.3
    # shellcheck disable=SC2086
    kill -9 $pids >/dev/null 2>&1 || true
  fi
}

echo "Stopping servers (if running)..."
kill_pidfile "$ROOT_DIR/.pids/frontend.pid"
kill_pidfile "$ROOT_DIR/.pids/backend.pid"
kill_port "$FRONTEND_PORT"
kill_port "$BACKEND_PORT"

echo "Resetting DB..."
rm -f "$ROOT_DIR/backend/weather.db" "$ROOT_DIR/backend/weather.db-shm" "$ROOT_DIR/backend/weather.db-wal"

if [ -f "$ROOT_DIR/backend/requirements.txt" ]; then
  (
    cd "$ROOT_DIR/backend"
    if [ ! -d ".venv" ]; then
      python -m venv .venv
    fi
    source ".venv/bin/activate"
    pip -q install --upgrade pip
    pip -q install -r requirements.txt
    alembic upgrade head
    python -m app.seed
  )
fi

echo "Done."

