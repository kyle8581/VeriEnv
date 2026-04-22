#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

SITE_PORT="$(python3 -c 'import json; print(json.load(open("ports.json"))["ports"]["PORT"])')"
BACKEND_PORT="$((SITE_PORT + 1))"

stop_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      # Try to stop the whole process group first (start_servers.sh uses `setsid`).
      kill -TERM "-$pid" 2>/dev/null || true
      kill -TERM "$pid" 2>/dev/null || true
      # Give it a moment, then force if needed.
      sleep 0.5 || true
      if kill -0 "$pid" 2>/dev/null; then
        kill -KILL "-$pid" 2>/dev/null || true
        kill -KILL "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pid_file"
  fi
}

kill_port() {
  local port="$1"
  # Extract pids from ss output like: users:(("node",pid=123,fd=22))
  local pids
  pids="$(ss -ltnpH "sport = :$port" 2>/dev/null | sed -n 's/.*pid=\\([0-9]\\+\\).*/\\1/p' | sort -u || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi
  for pid in $pids; do
    kill -TERM "-$pid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true
  done
}

echo "Resetting LinkedIn clone servers and DB…"

stop_pid "$ROOT_DIR/.pids/frontend.pid"
stop_pid "$ROOT_DIR/.pids/backend.pid"

# Also ensure ports are free even if pidfiles were missing/stale.
kill_port "$SITE_PORT"
kill_port "$BACKEND_PORT"

# Wait briefly for ports to be released.
for _ in $(seq 1 30); do
  if ss -ltnH "sport = :$SITE_PORT" | grep -q .; then
    sleep 0.1
    continue
  fi
  if ss -ltnH "sport = :$BACKEND_PORT" | grep -q .; then
    sleep 0.1
    continue
  fi
  break
done

mkdir -p "$ROOT_DIR/backend/var"
rm -f "$ROOT_DIR/backend/var/app.db" "$ROOT_DIR/backend/var/app.db-shm" "$ROOT_DIR/backend/var/app.db-wal" || true

python3 -m pip install -r "$ROOT_DIR/backend/requirements.txt" >/dev/null
PYTHONPATH="$ROOT_DIR/backend" python3 -c "from app.seed.seed_data import seed_db; seed_db(reset=True); print('DB reset + seeded.')"

echo "Restarting servers…"
bash "$ROOT_DIR/start_servers.sh"

