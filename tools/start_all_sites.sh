#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WEBSITES_DIR="$ROOT_DIR/websites"

# DRY_RUN=1 prints actions without starting anything.
DRY_RUN="${DRY_RUN:-0}"

# MAX_PARALLEL limits how many start scripts we launch concurrently.
MAX_PARALLEL="${MAX_PARALLEL:-4}"

# SKIP_IF_RUNNING=1 skips a site if any of its reserved ports are currently listening.
SKIP_IF_RUNNING="${SKIP_IF_RUNNING:-1}"

# ONLY_WITH_TASKS=1 only starts websites that have task_instructions.json
ONLY_WITH_TASKS="${ONLY_WITH_TASKS:-1}"

# LOG_DIR for start logs (one file per site).
LOG_DIR="${LOG_DIR:-$ROOT_DIR/.logs/start_all}"

# PORT_FORWARD_FILE: if set, write SSH port-forward command to this file
PORT_FORWARD_FILE="${PORT_FORWARD_FILE:-}"

export CLONE_CODING_ROOT="$ROOT_DIR"

# Collect ports for forwarding
declare -a FORWARD_PORTS=()

run() {
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] $*"
    return 0
  fi
  "$@"
}

port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN
    return $?
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

site_reserved_ports() {
  local site_dir="$1"
  python3 - <<'PY' "$site_dir/ports.json" 2>/dev/null || true
import json,sys
path=sys.argv[1]
try:
  p=json.load(open(path,"r",encoding="utf-8"))
except Exception:
  raise SystemExit(0)
ports=p.get("ports") or {}
if isinstance(ports, dict):
  for v in ports.values():
    if isinstance(v,int):
      print(v)
PY
}

should_skip_running() {
  local site_dir="$1"
  [ "$SKIP_IF_RUNNING" = "1" ] || return 1
  [ -f "$site_dir/ports.json" ] || return 1

  local p
  while IFS= read -r p; do
    if [ -n "${p:-}" ] && port_listening "$p"; then
      return 0
    fi
  done < <(site_reserved_ports "$site_dir")
  return 1
}

start_site_detached() {
  local site_dir="$1"
  local site_name
  site_name="$(basename "$site_dir")"

  if [ ! -f "$site_dir/start_servers.sh" ]; then
    return 0
  fi

  # Check if we should only start sites with task_instructions.json
  if [ "$ONLY_WITH_TASKS" = "1" ] && [ ! -f "$site_dir/task_instructions.json" ]; then
    echo "==> SKIP (no task_instructions.json): $site_name"
    return 0
  fi

  # Ensure ports are reserved and ports.json exists (so we can skip conflicts + dashboard can display).
  run python3 "$ROOT_DIR/tools/port_registry.py" reserve "$site_name" --from-start-servers >/dev/null || true
  if [ -f "$site_dir/docker-compose.yml" ]; then
    run python3 "$ROOT_DIR/tools/port_registry.py" reserve "$site_name" --vars FRONTEND_PORT BACKEND_PORT >/dev/null || true
  fi

  if should_skip_running "$site_dir"; then
    echo "==> SKIP (already running): $site_name"
    return 0
  fi
  
  # Collect ports for forwarding
  local p
  while IFS= read -r p; do
    if [ -n "${p:-}" ]; then
      FORWARD_PORTS+=("$p")
    fi
  done < <(site_reserved_ports "$site_dir")

  mkdir -p "$LOG_DIR"
  local log_file="$LOG_DIR/${site_name//\//_}.log"

  echo "==> START: $site_name"
  echo "  - log: $log_file"

  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] nohup \"$ROOT_DIR/tools/run_site_with_reserved_ports.sh\" \"$site_name\" >\"$log_file\" 2>&1 &"
    return 0
  fi

  # Detach each site start. Some start_servers.sh run in foreground; nohup ensures we don't block.
  nohup "$ROOT_DIR/tools/run_site_with_reserved_ports.sh" "$site_name" >"$log_file" 2>&1 &
}

wait_for_slot() {
  local max="$1"
  while true; do
    local running
    running="$(jobs -pr | wc -l | tr -d ' ')"
    if [ "${running:-0}" -lt "$max" ]; then
      return 0
    fi
    sleep 0.2
  done
}

if [ ! -d "$WEBSITES_DIR" ]; then
  echo "ERROR: websites dir not found: $WEBSITES_DIR" >&2
  exit 1
fi

echo "==> Starting all sites (detached)"
echo "- MAX_PARALLEL=$MAX_PARALLEL"
echo "- SKIP_IF_RUNNING=$SKIP_IF_RUNNING"
echo "- ONLY_WITH_TASKS=$ONLY_WITH_TASKS"
echo "- LOG_DIR=$LOG_DIR"
echo

count=0
while IFS= read -r -d '' site_dir; do
  if [ -f "$site_dir/start_servers.sh" ]; then
    count=$((count + 1))
    wait_for_slot "$MAX_PARALLEL"
    start_site_detached "$site_dir" &
  fi
done < <(find "$WEBSITES_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)

wait || true
echo
echo "==> Done launching. Check logs in: $LOG_DIR"

# Generate port forwarding command
if [ ${#FORWARD_PORTS[@]} -gt 0 ]; then
  # Remove duplicates and sort
  UNIQUE_PORTS=($(printf '%s\n' "${FORWARD_PORTS[@]}" | sort -u -n))
  
  # Build SSH port forward arguments
  FORWARD_ARGS=""
  for port in "${UNIQUE_PORTS[@]}"; do
    FORWARD_ARGS="$FORWARD_ARGS -L ${port}:localhost:${port}"
  done
  
  SERVER_HOST="${SSH_SERVER:-$(hostname)}"
  SSH_USER="${SSH_USER:-${USER}}"
  
  SSH_CMD="ssh$FORWARD_ARGS $SSH_USER@$SERVER_HOST"
  
  echo
  echo "==> Port Forwarding Command (run on your laptop):"
  echo "=============================================="
  echo "$SSH_CMD"
  echo "=============================================="
  echo
  echo "Total ports to forward: ${#UNIQUE_PORTS[@]}"
  echo "Ports: ${UNIQUE_PORTS[*]}"
  
  # Save to file if requested
  if [ -n "$PORT_FORWARD_FILE" ]; then
    echo "$SSH_CMD" > "$PORT_FORWARD_FILE"
    echo "Saved to: $PORT_FORWARD_FILE"
  fi
  
  # Also save to default location
  FORWARD_SCRIPT="$ROOT_DIR/port_forward.sh"
  cat > "$FORWARD_SCRIPT" << EOF
#!/usr/bin/env bash
# Auto-generated port forwarding script
# Run this on your laptop to access all running websites

SERVER_HOST="\${1:-$SERVER_HOST}"
SSH_USER="\${SSH_USER:-$SSH_USER}"

echo "Forwarding ${#UNIQUE_PORTS[@]} ports to \$SERVER_HOST..."
echo "Press Ctrl+C to stop"
echo

ssh$FORWARD_ARGS \$SSH_USER@\$SERVER_HOST
EOF
  chmod +x "$FORWARD_SCRIPT"
  echo "Port forward script saved to: $FORWARD_SCRIPT"
fi

echo
echo "Tip: DRY_RUN=1 $0"
echo "Tip: MAX_PARALLEL=2 $0"
echo "Tip: SKIP_IF_RUNNING=0 $0   # force re-launch even if ports are listening"
echo "Tip: ONLY_WITH_TASKS=1 $0   # only start sites with task_instructions.json"








