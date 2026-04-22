#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove stale Next.js lock file
rm -f "${ROOT_DIR}/frontend/.next/dev/lock" 2>/dev/null || true
cd "$ROOT_DIR"

# Read ports from ports.json (prefer specific ports over PORT)
FRONTEND_PORT="$(python3 -c 'import json; p=json.load(open("ports.json"))["ports"]; print(p.get("FRONTEND_PORT") or p.get("WEB_PORT") or p.get("PORT"))')"
BACKEND_PORT="$(python3 -c 'import json; p=json.load(open("ports.json"))["ports"]; print(p.get("BACKEND_PORT") or p.get("API_PORT") or int(p.get("PORT",0))+1)')"

echo "Using backend port:  $BACKEND_PORT"
echo "Using frontend port: $FRONTEND_PORT"

export NEXT_PUBLIC_API_BASE_URL=""

# Best-effort cleanup in case a previous run crashed and left listeners behind.
./reset_servers.sh stop >/dev/null 2>&1 || true

wait_http_ok() {
  local url="$1"
  local tries="${2:-50}"
  local delay="${3:-0.2}"
  for _ in $(seq 1 "$tries"); do
    if curl -fsS -o /dev/null "$url" 2>/dev/null; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

wait_frontend_health() {
  local url="$1"
  local tries="${2:-75}"
  local delay="${3:-0.2}"
  python3 - "$url" "$tries" "$delay" <<'PY'
import json
import sys
import time
import urllib.request

url = sys.argv[1]
tries = int(sys.argv[2])
delay = float(sys.argv[3])

for _ in range(tries):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            if getattr(r, "status", 200) != 200:
                raise RuntimeError("non-200")
            data = json.loads(r.read().decode("utf-8"))
            if data.get("site") == "coursera.org" and data.get("service") == "frontend":
                raise SystemExit(0)
    except Exception:
        pass
    time.sleep(delay)

raise SystemExit(1)
PY
}

# --------------------
# Backend
# --------------------
if [[ ! -x "backend/.venv/bin/python3" ]]; then
  echo "Creating backend venv..."
  python3 -m venv "backend/.venv"
  "backend/.venv/bin/pip" install -r "backend/requirements.txt"
fi

echo "Starting backend..."
(
  cd "backend"
  exec setsid -w "../backend/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port "$BACKEND_PORT"
) &
BACKEND_PID="$!"

# --------------------
# Frontend
# --------------------
if [[ ! -d "frontend/node_modules" ]]; then
  echo "Installing frontend deps..."
  (cd "frontend" && npm install)
fi

echo "Building frontend..."
(cd "frontend" && if [ ! -f .next/BUILD_ID ]; then npm run build; fi)

echo "Starting frontend..."
(
  cd "frontend"
  exec setsid -w node "./node_modules/next/dist/bin/next" start -p "$FRONTEND_PORT" -H 0.0.0.0
) &
FRONTEND_PID="$!"

printf "%s\n" "$BACKEND_PID" "$FRONTEND_PID" > ".server_pids"
echo "Wrote PIDs to .server_pids"

if ! wait_http_ok "http://127.0.0.1:${BACKEND_PORT}/docs" 50 0.2; then
  echo "Backend did not become ready on :$BACKEND_PORT"
  ./reset_servers.sh stop >/dev/null 2>&1 || true
  exit 1
fi

if ! wait_frontend_health "http://127.0.0.1:${FRONTEND_PORT}/health" 75 0.2; then
  echo "Frontend did not become ready on :$FRONTEND_PORT"
  ./reset_servers.sh stop >/dev/null 2>&1 || true
  exit 1
fi

echo
echo "Backend:  http://127.0.0.1:${BACKEND_PORT}  (OpenAPI: /docs)"
echo "Frontend: http://127.0.0.1:${FRONTEND_PORT}"
echo
echo "To stop:  ./reset_servers.sh stop"

