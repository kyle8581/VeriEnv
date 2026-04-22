#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove stale Next.js lock file
rm -f "${ROOT_DIR}/frontend/.next/dev/lock" 2>/dev/null || true

# Read ports: env var > FRONTEND_PORT from ports.json > PORT fallback
FRONTEND_PORT="${FRONTEND_PORT:-$(python3 -c 'import json;p=json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"];print(p.get("FRONTEND_PORT") or p.get("WEB_PORT") or p.get("PORT"))')}"
BACKEND_PORT="${BACKEND_PORT:-$(python3 -c 'import json;p=json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"];print(p.get("BACKEND_PORT") or p.get("API_PORT") or p.get("PORT"))')}"

mkdir -p "$ROOT_DIR/.pids" "$ROOT_DIR/.logs"

if command -v lsof >/dev/null 2>&1; then
  if lsof -tiTCP:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $FRONTEND_PORT is already in use. Run ./reset_servers.sh first."
    exit 1
  fi
  if lsof -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $BACKEND_PORT is already in use. Run ./reset_servers.sh first."
    exit 1
  fi
fi

echo "Starting backend on :$BACKEND_PORT"
(
  cd "$ROOT_DIR/backend"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source ".venv/bin/activate"
  pip -q install --upgrade pip
  pip -q install -r requirements.txt
  alembic upgrade head >/dev/null 2>&1 || true
  nohup uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload >"$ROOT_DIR/.logs/backend.log" 2>&1 &
  echo $! >"$ROOT_DIR/.pids/backend.pid"
)

echo "Starting frontend on :$FRONTEND_PORT"
(
  cd "$ROOT_DIR/frontend"
  npm install --silent
  nohup npm run dev -- --port "${FRONTEND_PORT}" >"$ROOT_DIR/.logs/frontend.log" 2>&1 &
  echo $! >"$ROOT_DIR/.pids/frontend.pid"
)

echo ""
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Backend:  http://localhost:$BACKEND_PORT"
echo ""
echo "Logs:"
echo "  $ROOT_DIR/.logs/frontend.log"
echo "  $ROOT_DIR/.logs/backend.log"

