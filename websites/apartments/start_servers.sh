#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
# Read ports from ports.json (standard pattern)
FRONTEND_PORT="${FRONTEND_PORT:-$(python3 -c 'import json; p=json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"]; print(p.get("FRONTEND_PORT") or p.get("WEB_PORT") or p.get("UI_PORT") or p.get("PORT"))')}"
BACKEND_PORT="${BACKEND_PORT:-$(python3 -c 'import json; p=json.load(open("'"$ROOT_DIR"'/ports.json"))["ports"]; print(p.get("BACKEND_PORT") or p.get("API_PORT") or p.get("PORT"))')}"
WEB_PORT="${FRONTEND_PORT}"
API_PORT="${BACKEND_PORT}"
FRONTEND_MODE="${FRONTEND_MODE:-dev}" # dev|prod

PID_DIR="${ROOT_DIR}/.pids"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${PID_DIR}" "${LOG_DIR}"

# Kill any existing processes on the ports
echo "Cleaning up ports ${BACKEND_PORT} and ${FRONTEND_PORT}..."
fuser -k "${BACKEND_PORT}/tcp" 2>/dev/null || true
fuser -k "${FRONTEND_PORT}/tcp" 2>/dev/null || true

# Remove Next.js lock file if exists
rm -f "${ROOT_DIR}/frontend/.next/dev/lock" 2>/dev/null || true

# Install backend dependencies
echo "Installing backend dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
  pip install -q -r "${ROOT_DIR}/backend/requirements.txt"
fi

echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT}"
( cd "${ROOT_DIR}/backend" && \
  python3 -m alembic upgrade head && \
  python3 -m app.seed && \
  nohup python3 -m uvicorn app.main:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" \
    > "${LOG_DIR}/backend.log" 2>&1 & echo $! > "${PID_DIR}/backend.pid" )

# Wait for backend to start
sleep 2

if [[ -f "${ROOT_DIR}/frontend/package.json" ]]; then
  # Keep frontend pointing at the started backend port.
  cat > "${ROOT_DIR}/frontend/.env.local" <<EOF
NEXT_PUBLIC_API_BASE_URL=http://${BACKEND_HOST}:${BACKEND_PORT}
EOF

  echo "Starting frontend on http://127.0.0.1:${FRONTEND_PORT} (${FRONTEND_MODE})"
  if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
    ( cd "${ROOT_DIR}/frontend" && npm install )
  fi
  if [[ "${FRONTEND_MODE}" == "prod" ]]; then
    ( cd "${ROOT_DIR}/frontend" && npm run build )
    ( cd "${ROOT_DIR}/frontend" && nohup npm run start -- -p "${FRONTEND_PORT}" > "${LOG_DIR}/frontend.log" 2>&1 & echo $! > "${PID_DIR}/frontend.pid" )
  else
    ( cd "${ROOT_DIR}/frontend" && nohup npm run dev -- --port "${FRONTEND_PORT}" > "${LOG_DIR}/frontend.log" 2>&1 & echo $! > "${PID_DIR}/frontend.pid" )
  fi
elif [[ -d "${ROOT_DIR}/frontend" ]]; then
  echo "Frontend directory exists but is not initialized (missing package.json)."
  echo "Backend is running; scaffold the frontend, then re-run this script."
else
  echo "Frontend directory not found at ${ROOT_DIR}/frontend"
  echo "Backend is running; once frontend exists, re-run this script."
fi

cat <<EOF

Done.

Backend:
  - URL: http://${BACKEND_HOST}:${BACKEND_PORT}
  - Docs: http://${BACKEND_HOST}:${BACKEND_PORT}/docs
Frontend:
  - URL: http://127.0.0.1:${FRONTEND_PORT}

EOF

