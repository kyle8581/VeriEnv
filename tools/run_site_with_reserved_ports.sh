#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="${1:-}"

if [ -z "$SITE" ]; then
  echo "Usage: $0 <website-name>" >&2
  echo "Example: $0 apartments" >&2
  exit 2
fi

SITE_DIR="$ROOT_DIR/websites/$SITE"
if [ ! -d "$SITE_DIR" ]; then
  echo "ERROR: No such website dir: $SITE_DIR" >&2
  exit 1
fi
export SITE_DIR

export CLONE_CODING_ROOT="$ROOT_DIR"

# Reserve ports by scanning start_servers.sh when present; fallback to PORT only.
if [ -f "$SITE_DIR/start_servers.sh" ]; then
  python3 "$ROOT_DIR/tools/port_registry.py" reserve "$SITE" --from-start-servers >/dev/null
else
  python3 "$ROOT_DIR/tools/port_registry.py" reserve "$SITE" --vars PORT >/dev/null
fi

# If the site is docker-compose based, reserve explicit frontend/backend ports as well.
# (Compose host-port mappings are commonly 3000/8000 and collide heavily.)
if [ -f "$SITE_DIR/docker-compose.yml" ]; then
  python3 "$ROOT_DIR/tools/port_registry.py" reserve "$SITE" --vars FRONTEND_PORT BACKEND_PORT >/dev/null
fi

# Export reserved ports into the environment.
eval "$(python3 "$ROOT_DIR/tools/port_registry.py" exports "$SITE")"

API_PORT_EFFECTIVE="${API_PORT:-${BACKEND_PORT:-}}"
if [ -n "${API_PORT_EFFECTIVE:-}" ]; then
  export VITE_API_BASE_URL="http://localhost:${API_PORT_EFFECTIVE}"
  export NEXT_PUBLIC_API_URL="http://localhost:${API_PORT_EFFECTIVE}"
  export NEXT_PUBLIC_BACKEND_PORT="${API_PORT_EFFECTIVE}"
fi

if [ -n "${FRONTEND_PORT:-}" ]; then
  export FRONTEND_PORT
fi
if [ -n "${BACKEND_PORT:-}" ]; then
  export BACKEND_PORT
fi
if [ -n "${WEB_PORT:-}" ]; then
  export WEB_PORT
fi
if [ -n "${API_PORT:-}" ]; then
  export API_PORT
fi

echo "==> Reserved ports for $SITE:"
python3 "$ROOT_DIR/tools/port_registry.py" exports "$SITE" | sed 's/^export / - /'

cd "$SITE_DIR"

# Function to wait for a port to be listening
wait_for_port() {
  local port=$1
  local timeout=${2:-60}
  local start=$(date +%s)
  while ! ss -tlnp 2>/dev/null | grep -q ":$port "; do
    if (( $(date +%s) - start > timeout )); then
      echo "WARNING: Timeout waiting for port $port" >&2
      return 1
    fi
    sleep 0.5
  done
  return 0
}

# Wait for ANY of the given candidate ports to come up. Prints the port that succeeded.
wait_for_any_port() {
  local timeout=${1:-60}
  shift
  local candidates=("$@")
  local start=$(date +%s)
  while true; do
    for port in "${candidates[@]}"; do
      if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "$port"
        return 0
      fi
    done
    if (( $(date +%s) - start >= timeout )); then
      return 1
    fi
    sleep 0.5
  done
}

# Get ports to wait for
# Collect all candidate frontend ports; we succeed if ANY of them comes up.
FRONTEND_CANDIDATES=()
for var in FRONTEND_PORT WEB_PORT UI_PORT PORT; do
  val="${!var:-}"
  if [ -n "$val" ]; then FRONTEND_CANDIDATES+=("$val"); fi
done

BACKEND_CANDIDATES=()
for var in BACKEND_PORT API_PORT; do
  val="${!var:-}"
  if [ -n "$val" ]; then BACKEND_CANDIDATES+=("$val"); fi
done

if [ -f "start_servers.sh" ]; then
  # Run in background, redirect output to log file
  LOG_FILE="$SITE_DIR/.runtime/server.log"
  mkdir -p "$SITE_DIR/.runtime"
  nohup bash "./start_servers.sh" > "$LOG_FILE" 2>&1 &
  SERVER_PID=$!
  echo "$SERVER_PID" > "$SITE_DIR/.runtime/server.pid"
  echo "Started server (PID: $SERVER_PID), log: $LOG_FILE"
  
  # Wait for any frontend candidate port to come up
  ACTUAL_FRONTEND=""
  if [ ${#FRONTEND_CANDIDATES[@]} -gt 0 ]; then
    echo "Waiting for frontend port (candidates: ${FRONTEND_CANDIDATES[*]})..."
    ACTUAL_FRONTEND=$(wait_for_any_port 60 "${FRONTEND_CANDIDATES[@]}") || true
    if [ -n "$ACTUAL_FRONTEND" ]; then
      echo "Frontend ready on port $ACTUAL_FRONTEND"
    else
      echo "WARNING: No frontend port came up"
    fi
  fi

  ACTUAL_BACKEND=""
  if [ ${#BACKEND_CANDIDATES[@]} -gt 0 ]; then
    echo "Waiting for backend port (candidates: ${BACKEND_CANDIDATES[*]})..."
    ACTUAL_BACKEND=$(wait_for_any_port 30 "${BACKEND_CANDIDATES[@]}") || true
  fi

  # Write the actually-listening ports to .runtime/servers.json
  python3 - "$ACTUAL_FRONTEND" "$ACTUAL_BACKEND" << 'PY'
import json, os, sys
from pathlib import Path

site_dir = Path(os.environ.get("SITE_DIR", ".")).resolve()
actual_frontend = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
actual_backend = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
site_name = site_dir.name

# Fallback to env vars if no port was detected
if not actual_frontend:
    for var in ("FRONTEND_PORT", "WEB_PORT", "UI_PORT", "PORT"):
        if os.environ.get(var):
            actual_frontend = os.environ[var]
            break
if not actual_backend:
    for var in ("BACKEND_PORT", "API_PORT"):
        if os.environ.get(var):
            actual_backend = os.environ[var]
            break

# allrecipes is served as a single Next.js app, so evaluators expect the
# backend URL to reuse the frontend port.
if site_name == "allrecipes" and actual_frontend and not actual_backend:
    actual_backend = actual_frontend

runtime_dir = site_dir / ".runtime"
runtime_dir.mkdir(exist_ok=True)
data = {
    "frontend": {"port": int(actual_frontend)} if actual_frontend else {},
    "backend": {"port": int(actual_backend)} if actual_backend else {},
}
(runtime_dir / "servers.json").write_text(json.dumps(data, indent=2))
PY

  echo "Server ready!"
  exit 0
fi

if [ -f "docker-compose.yml" ]; then
  docker compose up -d --build

  ACTUAL_FRONTEND=""
  if [ ${#FRONTEND_CANDIDATES[@]} -gt 0 ]; then
    echo "Waiting for frontend port (candidates: ${FRONTEND_CANDIDATES[*]})..."
    ACTUAL_FRONTEND=$(wait_for_any_port 120 "${FRONTEND_CANDIDATES[@]}") || true
    if [ -n "$ACTUAL_FRONTEND" ]; then
      echo "Frontend ready on port $ACTUAL_FRONTEND"
    else
      echo "WARNING: No frontend port came up"
    fi
  fi

  ACTUAL_BACKEND=""
  if [ ${#BACKEND_CANDIDATES[@]} -gt 0 ]; then
    echo "Waiting for backend port (candidates: ${BACKEND_CANDIDATES[*]})..."
    ACTUAL_BACKEND=$(wait_for_any_port 30 "${BACKEND_CANDIDATES[@]}") || true
  fi

  python3 - "$ACTUAL_FRONTEND" "$ACTUAL_BACKEND" << 'PY'
import json, os, sys
from pathlib import Path

site_dir = Path(os.environ.get("SITE_DIR", ".")).resolve()
actual_frontend = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
actual_backend = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None

if not actual_frontend:
    for var in ("FRONTEND_PORT", "WEB_PORT", "UI_PORT", "PORT"):
        if os.environ.get(var):
            actual_frontend = os.environ[var]
            break
if not actual_backend:
    for var in ("BACKEND_PORT", "API_PORT"):
        if os.environ.get(var):
            actual_backend = os.environ[var]
            break

runtime_dir = site_dir / ".runtime"
runtime_dir.mkdir(exist_ok=True)
data = {
    "frontend": {"port": int(actual_frontend)} if actual_frontend else {},
    "backend": {"port": int(actual_backend)} if actual_backend else {},
}
(runtime_dir / "servers.json").write_text(json.dumps(data, indent=2))
PY
  echo "Docker containers ready!"
  exit 0
fi

echo "ERROR: No start_servers.sh or docker-compose.yml found in $SITE_DIR" >&2
exit 1


