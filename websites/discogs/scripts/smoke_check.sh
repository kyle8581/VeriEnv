#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

WEB_PORT="${PORT:-12042}"
BASE="http://localhost:${WEB_PORT}"

rm -f /tmp/discogs_smoke.log

echo "Starting servers for smoke check..."
"${ROOT_DIR}/start_servers.sh" > /tmp/discogs_smoke.log 2>&1 &
PID=$!

cleanup() {
  kill "${PID}" 2>/dev/null || true
  wait "${PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Waiting for web..."
for i in {1..60}; do
  if curl -fsS "${BASE}/api/backend/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Checking key pages..."
curl -fsS -o /dev/null "${BASE}/"
curl -fsS -o /dev/null "${BASE}/genre/rock"

# banner release is deterministic from seed and should exist
RID="$(curl -fsS "${BASE}/api/backend/home" | python -c 'import json,sys; print(json.load(sys.stdin)["banner"]["release_id"])')"
curl -fsS -o /dev/null "${BASE}/release/${RID}"
curl -fsS -o /dev/null "${BASE}/sell/release/${RID}"

echo "OK"

