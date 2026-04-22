#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBSITES_DIR="$ROOT/websites"

S00="$ROOT/00_cursor_command.sh"
S01="$ROOT/01_cursor_bug_report.sh"
S02="$ROOT/02_cursor_task_generation.sh"

# If STOP_ON_FAIL=1, abort on the first failed website. Default: keep going.
STOP_ON_FAIL="${STOP_ON_FAIL:-0}"

is_png_only_dir() {
  local dir="$1"

  # If there's ANY entry other than *.png or *.log (including subfolders) or ports.json, it's "finished" => skip.
  if find "$dir" -mindepth 1 -maxdepth 1 ! -name '*.png' ! -name '*.log' ! -name 'ports.json' -print -quit | grep -q .; then
    return 1
  fi

  # Optional: require at least one png to process
  if ! find "$dir" -mindepth 1 -maxdepth 1 -name '*.png' ! -name '*.log' ! -name 'ports.json' -print -quit | grep -q .; then
    return 1
  fi
}

run_sequence() {
  local site_dir="$1"
  (
    cd "$site_dir"
    bash "$S00" > 00_cursor_command.log
    bash "$S01" > 01_cursor_bug_report.log
    bash "$S02" > 02_cursor_task_generation.log
  )
}

processed=0
skipped=0
failed=0

# Collect the list of website dirs in an array to avoid re-reading and debug display
mapfile -d '' site_dirs < <(find "$WEBSITES_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
total_sites=${#site_dirs[@]}

echo "==> Found $total_sites sites to process:"
for sd in "${site_dirs[@]}"; do
  echo "  - $(basename "$sd")"
done
echo "====================="

for site_dir in "${site_dirs[@]}"; do
  site_dir="${site_dir%/}"  # Remove trailing slash if present
  site_name="$(basename "$site_dir")"

  if ! is_png_only_dir "$site_dir"; then
    echo "==> SKIP (already implemented): $site_name"
    skipped=$((skipped + 1))
    continue
  fi

  echo "==> RUN: $site_name"
  processed=$((processed + 1))

  if run_sequence "$site_dir"; then
    echo "==> OK: $site_name"
  else
    echo "==> FAIL: $site_name" >&2
    failed=$((failed + 1))
    if [ "$STOP_ON_FAIL" = "1" ]; then
      exit 1
    fi
  fi
done

echo "==> Done. processed=$processed skipped=$skipped failed=$failed"