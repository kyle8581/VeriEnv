#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Read ports from ports.json
SITE_PORT="$(python3 -c 'import json; p=json.load(open("ports.json"))["ports"]; print(p.get("FRONTEND_PORT") or p.get("WEB_PORT") or p.get("PORT"))')"
BACKEND_PORT="$(python3 -c 'import json; p=json.load(open("ports.json"))["ports"]; print(p.get("BACKEND_PORT") or p.get("API_PORT") or int(p.get("PORT",0))+1)')"

mkdir -p "$ROOT_DIR/logs" "$ROOT_DIR/.pids" "$ROOT_DIR/backend/var"

echo "Starting LinkedIn clone…"
echo "  - frontend: http://127.0.0.1:${SITE_PORT}"
echo "  - backend:  http://127.0.0.1:${BACKEND_PORT} (API prefix: /api)"

# Install backend deps
if ! python3 -c "import fastapi" 2>/dev/null; then
  python3 -m pip install -r "$ROOT_DIR/backend/requirements.txt" >/dev/null
fi

# Ensure DB exists + seeded (idempotent)
PYTHONPATH="$ROOT_DIR/backend" python3 -c "from app.seed.seed_data import seed_db; seed_db(reset=False); print('DB seeded (idempotent).')"

# Start backend (FastAPI)
if [[ -f "$ROOT_DIR/.pids/backend.pid" ]] && kill -0 "$(cat "$ROOT_DIR/.pids/backend.pid")" 2>/dev/null; then
  echo "Backend already running (pid $(cat "$ROOT_DIR/.pids/backend.pid"))."
else
  # NOTE: use the `uvicorn` entrypoint (more reliable than `python3 -m uvicorn` in this environment).
  nohup setsid uvicorn app.main:app --app-dir "$ROOT_DIR/backend" --host 0.0.0.0 --port "$BACKEND_PORT" \
    >"$ROOT_DIR/logs/backend.log" 2>&1 &
  echo $! >"$ROOT_DIR/.pids/backend.pid"
  echo "Backend started (pid $(cat "$ROOT_DIR/.pids/backend.pid"))."
fi

# Install frontend deps
cd "$ROOT_DIR/frontend"
npm ci >/dev/null

# Start frontend dev server (supports proxy to backend)
if [[ -f "$ROOT_DIR/.pids/frontend.pid" ]] && kill -0 "$(cat "$ROOT_DIR/.pids/frontend.pid")" 2>/dev/null; then
  echo "Frontend already running (pid $(cat "$ROOT_DIR/.pids/frontend.pid"))."
else
  if ss -ltnH "sport = :$SITE_PORT" | grep -q .; then
    echo "ERROR: Port ${SITE_PORT} is already in use. Run ./reset_servers.sh or stop the process using that port."
    exit 1
  fi
  nohup setsid npm run dev -- --host 0.0.0.0 --port "$SITE_PORT" >"$ROOT_DIR/logs/frontend.log" 2>&1 &
  echo $! >"$ROOT_DIR/.pids/frontend.pid"
  echo "Frontend started (pid $(cat "$ROOT_DIR/.pids/frontend.pid"))."
fi

echo "Done."

