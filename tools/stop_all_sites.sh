#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WEBSITES_DIR="$ROOT_DIR/websites"

# Optional: pass one or more website directory names to stop only those sites.
# Example:
#   tools/stop_all_sites.sh adoptapet "allrecipes copy"
TARGET_SITES=("$@")

# DRY_RUN=1 prints actions without killing anything.
DRY_RUN="${DRY_RUN:-0}"

# USE_RESET=1 will call each site's reset_servers.sh (often resets DB state; data loss possible).
USE_RESET="${USE_RESET:-0}"

# REMOVE_VOLUMES=1 will run `docker compose down -v` for compose-based sites (data loss).
REMOVE_VOLUMES="${REMOVE_VOLUMES:-0}"

run() {
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] $*"
    return 0
  fi
  "$@"
}

usage() {
  cat <<EOF
Usage:
  $(basename "$0") [website_name...]

Examples:
  $(basename "$0")                 # stop all sites (non-destructive, no DB reset)
  $(basename "$0") adoptapet       # stop only adoptapet
  $(basename "$0") "allrecipes copy"  # stop a site with spaces (quote it)

Env flags:
  DRY_RUN=1        Print actions only
  USE_RESET=1      Run reset_servers.sh (often resets DB; data loss possible)
  REMOVE_VOLUMES=1 docker compose down -v for compose sites (data loss)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

list_managed_ports() {
  # Prefer per-site ports.json files; fall back to repo-level .ports.json.
  python3 - <<'PY' "$WEBSITES_DIR" "$ROOT_DIR/.ports.json" 2>/dev/null || true
import json, sys
from pathlib import Path

websites_dir = Path(sys.argv[1])
root_ports = Path(sys.argv[2])

ports=set()

def add_from_payload(payload):
  p = (payload or {}).get("ports") or {}
  if isinstance(p, dict):
    for v in p.values():
      if isinstance(v, int):
        ports.add(v)

if websites_dir.is_dir():
  for site in sorted(websites_dir.iterdir(), key=lambda p: p.name.lower()):
    if not site.is_dir():
      continue
    f = site / "ports.json"
    if not f.exists():
      continue
    try:
      add_from_payload(json.loads(f.read_text(encoding="utf-8")))
    except Exception:
      pass

if not ports and root_ports.exists():
  try:
    reg = json.loads(root_ports.read_text(encoding="utf-8"))
    sites = (reg.get("sites") or {})
    if isinstance(sites, dict):
      for v in sites.values():
        add_from_payload(v)
  except Exception:
    pass

for p in sorted(ports):
  print(p)
PY
}

ss_listeners() {
  # Print ss output (or empty if ss unavailable)
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp 2>/dev/null || true
  fi
}

print_ports_in_use() {
  local title="$1"
  shift || true
  local ports=("$@")

  echo
  echo "==> $title"
  if [ "${#ports[@]}" -eq 0 ]; then
    echo "  (no managed ports found yet; run tools/reserve_ports_all.sh to generate ports.json files)"
    return 0
  fi

  if command -v ss >/dev/null 2>&1; then
    local out
    out="$(ss_listeners)"
    local any=0
    for p in "${ports[@]}"; do
      # Best-effort match: look for ":PORT " in Local Address:Port column and show the whole line
      line="$(printf '%s\n' "$out" | grep -E "[:.]${p}\\s" | head -n 1 || true)"
      if [ -n "$line" ]; then
        any=1
        echo "  - :$p  IN USE  $line"
      fi
    done
    if [ "$any" -eq 0 ]; then
      echo "  All managed ports appear free."
    fi
    return 0
  fi

  # Fallback: lsof (slower, but widely available)
  if command -v lsof >/dev/null 2>&1; then
    local any=0
    for p in "${ports[@]}"; do
      if lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
        any=1
        echo "  - :$p  IN USE"
        lsof -iTCP:"$p" -sTCP:LISTEN 2>/dev/null | sed 's/^/      /' || true
      fi
    done
    if [ "$any" -eq 0 ]; then
      echo "  All managed ports appear free."
    fi
    return 0
  fi

  echo "  WARN: neither 'ss' nor 'lsof' is available to verify listening ports."
}

kill_port_best_effort() {
  local port="$1"
  if [[ -z "${port:-}" ]]; then
    return 0
  fi
  echo "  - killing processes listening on :$port (reserved port)"
  if [ "$DRY_RUN" = "1" ]; then
    echo "[dry-run] fuser -k ${port}/tcp"
    return 0
  fi
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
    return 0
  fi
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti "tcp:${port}" || true)"
    if [ -n "${pids:-}" ]; then
      kill $pids >/dev/null 2>&1 || true
      sleep 0.2
      pids2="$(lsof -ti "tcp:${port}" || true)"
      if [ -n "${pids2:-}" ]; then
        kill -9 $pids2 >/dev/null 2>&1 || true
      fi
    fi
  fi
}

site_ports_json_ports() {
  local site_dir="$1"
  [ -f "$site_dir/ports.json" ] || return 0
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

list_managed_ports_for_targets() {
  # If TARGET_SITES is empty, list all managed ports.
  if [ "${#TARGET_SITES[@]}" -eq 0 ]; then
    list_managed_ports
    return 0
  fi

  python3 - <<'PY' "$WEBSITES_DIR" "${TARGET_SITES[@]}" 2>/dev/null || true
import json, sys
from pathlib import Path

websites_dir = Path(sys.argv[1])
targets = set(sys.argv[2:])
ports=set()

for site in websites_dir.iterdir():
  if not site.is_dir():
    continue
  if site.name not in targets:
    continue
  f = site / "ports.json"
  if not f.exists():
    continue
  try:
    payload = json.loads(f.read_text(encoding="utf-8"))
    p = (payload or {}).get("ports") or {}
    if isinstance(p, dict):
      for v in p.values():
        if isinstance(v, int):
          ports.add(v)
  except Exception:
    pass

for p in sorted(ports):
  print(p)
PY
}

kill_pid_file() {
  local pid_file="$1"
  [ -f "$pid_file" ] || return 0

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "  - killing pid=$pid (from $(basename "$pid_file"))"
    run kill "$pid" >/dev/null 2>&1 || true
    # give it a moment, then hard kill
    sleep 0.2
    if kill -0 "$pid" >/dev/null 2>&1; then
      run kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  fi

  run rm -f "$pid_file" >/dev/null 2>&1 || true
}

stop_site() {
  local site_dir="$1"
  local site_name
  site_name="$(basename "$site_dir")"

  # Only target sites that have start_servers.sh (per request).
  if [ ! -f "$site_dir/start_servers.sh" ]; then
    return 0
  fi

  # Optional filtering by site names passed as args
  if [ "${#TARGET_SITES[@]}" -gt 0 ]; then
    local match=0
    local t
    for t in "${TARGET_SITES[@]}"; do
      if [ "$t" = "$site_name" ]; then
        match=1
        break
      fi
    done
    if [ "$match" -eq 0 ]; then
      return 0
    fi
  fi

  echo "==> Stopping: $site_name"

  # 1) Optional: reset_servers.sh (WARNING: usually resets DB state)
  if [ "$USE_RESET" = "1" ] && [ -f "$site_dir/reset_servers.sh" ]; then
    echo "  - using reset_servers.sh (USE_RESET=1)"
    if [ "$DRY_RUN" = "1" ]; then
      echo "[dry-run] (cd \"$site_dir\" && bash ./reset_servers.sh)"
      return 0
    fi
    (cd "$site_dir" && bash ./reset_servers.sh) || true
    return 0
  fi

  # 2) docker-compose based sites
  if [ -f "$site_dir/docker-compose.yml" ] && command -v docker >/dev/null 2>&1; then
    echo "  - using docker compose stop/down"
    if [ "$DRY_RUN" = "1" ]; then
      if [ "$REMOVE_VOLUMES" = "1" ]; then
        echo "[dry-run] docker compose -f \"$site_dir/docker-compose.yml\" down -v --remove-orphans"
      else
        echo "[dry-run] docker compose -f \"$site_dir/docker-compose.yml\" stop"
      fi
      return 0
    fi
    if [ "$REMOVE_VOLUMES" = "1" ]; then
      docker compose -f "$site_dir/docker-compose.yml" down -v --remove-orphans || true
    else
      docker compose -f "$site_dir/docker-compose.yml" stop || true
    fi
    # Continue: also kill any stray pids/ports for this site (best-effort).
  fi

  # 3) Fallback: known pid-file conventions
  kill_pid_file "$site_dir/.server_pid"

  if [ -d "$site_dir/.pids" ]; then
    shopt -s nullglob
    local p
    for p in "$site_dir/.pids/"*.pid; do
      kill_pid_file "$p"
    done
    shopt -u nullglob
  fi

  # 4) Last resort: try to kill based on port hint files (.something-port)
  # Not perfect, but helps for scripts that only record a port.
  local hint
  for hint in \
    "$site_dir"/.*port* \
    "$site_dir/web"/.*port* \
    "$site_dir/frontend"/.*port* \
    "$site_dir/apps/web"/.*port*; do
    if [ -f "$hint" ] && [ -s "$hint" ]; then
      local port
      port="$(cat "$hint" 2>/dev/null | tr -d '[:space:]' || true)"
      if [[ "$port" =~ ^[0-9]+$ ]]; then
        echo "  - killing processes listening on :$port (from $(basename "$hint"))"
        if [ "$DRY_RUN" = "1" ]; then
          echo "[dry-run] fuser -k ${port}/tcp"
        else
          if command -v fuser >/dev/null 2>&1; then
            fuser -k "${port}/tcp" >/dev/null 2>&1 || true
          elif command -v lsof >/dev/null 2>&1; then
            pids="$(lsof -ti "tcp:${port}" || true)"
            if [ -n "${pids:-}" ]; then
              kill $pids >/dev/null 2>&1 || true
            fi
          fi
        fi
      fi
      run rm -f "$hint" >/dev/null 2>&1 || true
    fi
  done

  # 5) If the site has reserved ports.json, kill anything still bound to those ports.
  # This is crucial for sites that don't write PID files (common for "Ctrl+C to stop" scripts).
  local rp
  while IFS= read -r rp; do
    if [[ -n "${rp:-}" && "$rp" =~ ^[0-9]+$ ]]; then
      kill_port_best_effort "$rp"
    fi
  done < <(site_ports_json_ports "$site_dir")
}

if [ ! -d "$WEBSITES_DIR" ]; then
  echo "ERROR: websites dir not found: $WEBSITES_DIR" >&2
  exit 1
fi

mapfile -t MANAGED_PORTS < <(list_managed_ports_for_targets || true)
print_ports_in_use "Ports in use BEFORE stop (managed ports)" "${MANAGED_PORTS[@]:-}"

count=0
while IFS= read -r -d '' site_dir; do
  count=$((count + 1))
  stop_site "$site_dir"
done < <(find "$WEBSITES_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)

print_ports_in_use "Ports in use AFTER stop (managed ports)" "${MANAGED_PORTS[@]:-}"

echo
echo "==> Done."
echo "Tip: DRY_RUN=1 $0"
echo "Tip: USE_RESET=1 $0        # runs reset_servers.sh (often resets DB; data loss possible)"
echo "Tip: REMOVE_VOLUMES=1 $0   # docker compose down -v (data loss)"


