#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${ROOT_DIR}/.pids"
LOG_DIR="${ROOT_DIR}/logs"

kill_if_running () {
  local pid_file="$1"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}")"
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" || true
      # give it a moment, then force kill
      sleep 0.5
      kill -9 "${pid}" 2>/dev/null || true
    fi
    rm -f "${pid_file}"
  fi
}

kill_if_running "${PID_DIR}/frontend.pid"
kill_if_running "${PID_DIR}/backend.pid"

# Reset DB to initial seeded state
if [[ -f "${ROOT_DIR}/backend/app.db" ]]; then
  rm -f "${ROOT_DIR}/backend/app.db"
fi

( cd "${ROOT_DIR}/backend" && python -m alembic upgrade head && python -m app.seed )

# Optional: clear logs
mkdir -p "${LOG_DIR}"
rm -f "${LOG_DIR}/backend.log" "${LOG_DIR}/frontend.log" 2>/dev/null || true

echo "Reset complete. Run ./start_servers.sh to start services."

