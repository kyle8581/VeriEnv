#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ACTION="${1:-reset}"

PORT="$(python -c 'import json; print(json.load(open("ports.json"))["ports"]["PORT"])')"
BACKEND_PORT="$PORT"
FRONTEND_PORT="$((PORT + 1))"

collect_listening_pids() {
  # Best-effort: find PIDs listening on provided TCP ports.
  python - "$@" <<'PY'
import re
import subprocess
import sys

ports = set(sys.argv[1:])
if not ports:
    raise SystemExit(0)

try:
    out = subprocess.check_output(["ss", "-ltnp"], text=True, stderr=subprocess.DEVNULL)
except Exception:
    raise SystemExit(0)

pids = set()
for line in out.splitlines():
    parts = line.split()
    if len(parts) < 6:
        continue
    local = parts[3]
    if not any(f":{p}" in local for p in ports):
        continue
    for m in re.finditer(r"\bpid=(\d+)\b", line):
        pids.add(m.group(1))

for pid in sorted(pids, key=lambda x: int(x)):
    print(pid)
PY
}

kill_best_effort() {
  local pid="$1"
  if [[ -z "${pid:-}" ]]; then
    return 0
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi

  local pgid=""
  pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"

  if [[ -n "${pgid:-}" ]]; then
    echo "Stopping process group $pgid (pid $pid)"
    kill -TERM -- "-$pgid" 2>/dev/null || true
    sleep 1
    kill -KILL -- "-$pgid" 2>/dev/null || true
  else
    echo "Stopping pid $pid"
    kill -TERM "$pid" 2>/dev/null || true
    sleep 1
    kill -KILL "$pid" 2>/dev/null || true
  fi
}

stop_if_running() {
  declare -A seen=()

  if [[ -f ".server_pids" ]]; then
    mapfile -t PIDS < ".server_pids" || true
    for pid in "${PIDS[@]:-}"; do
      if [[ -n "${pid:-}" ]]; then
        seen["$pid"]=1
      fi
    done
    rm -f ".server_pids"
  fi

  # Also stop anything currently listening on the expected ports.
  while IFS= read -r pid; do
    if [[ -n "${pid:-}" ]]; then
      seen["$pid"]=1
    fi
  done < <(collect_listening_pids "$BACKEND_PORT" "$FRONTEND_PORT" || true)

  for pid in "${!seen[@]}"; do
    kill_best_effort "$pid"
  done
}

case "$ACTION" in
  stop)
    stop_if_running
    echo "Stopped (best-effort)."
    exit 0
    ;;
  reset)
    stop_if_running
    echo "Resetting DB..."
    if [[ ! -x "backend/.venv/bin/python" ]]; then
      echo "Creating backend venv..."
      python -m venv "backend/.venv"
      "backend/.venv/bin/pip" install -r "backend/requirements.txt"
    fi
    (cd "backend" && "../backend/.venv/bin/python" manage.py reset-db)
    echo "DB reset complete."
    ;;
  *)
    echo "Usage: ./reset_servers.sh [reset|stop]"
    exit 1
    ;;
esac

