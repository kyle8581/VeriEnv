#!/bin/bash
#
# Run VeriEnv benchmark on all (or selected) websites
#
# Usage:
#   ./tools/run_all_verienv.sh                     # Run all active sites (auto-detected)
#   ./tools/run_all_verienv.sh target twitter      # Run specific sites
#   ./tools/run_all_verienv.sh --som               # Run all with SoM enabled
#   ./tools/run_all_verienv.sh --som target        # Run specific site with SoM
#   ./tools/run_all_verienv.sh --sites-file f.json # Run only sites listed in JSON file
#   ./tools/run_all_verienv.sh --filter-success 3  # Auto-filter: only sites with >= 3 successes
#   ./tools/run_all_verienv.sh --list              # List available sites
#   ./tools/run_all_verienv.sh --check             # Check which sites are active
#
# Environment variables:
#   N_REPEATS=5       Number of trials per task (default: 5)
#   MODEL=openrouter/qwen/qwen3-8b  Model to use
#   JOBS=4            Parallel jobs
#   DRY_RUN=1         Print commands without executing
#   NO_THINK=1        Disable thinking mode for Qwen3 (faster inference)
#   SKIP_COMPLETED=1  Skip sites that already have completed experiments (default: 1)
#   RETRY_FAILED=1    Retry sites where all tasks failed (default: 1, overrides SKIP_COMPLETED)
#   MAX_STEPS=20      Maximum steps per episode (default: 20)
#   SOM=1             Enable Set-of-Marks observation (bounding box screenshots)
  SKIP_SITES="boardgamegeek twitter booking"  Space/comma separated site skip list

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Defaults
export VLLM_API_URL="http://localhost:8000/v1"
N_REPEATS="${N_REPEATS:-1}"
MODEL="${MODEL:-vllm/qwen3-vl-4b}"
JOBS="${JOBS:-20}"
DRY_RUN="${DRY_RUN:-0}"
RESULTS_DIR="${RESULTS_DIR:-$ROOT_DIR/results_qwen3-vl-4b-som}"
NO_THINK="${NO_THINK:-0}"  # Set to 1 to disable thinking mode for Qwen3
SKIP_COMPLETED="${SKIP_COMPLETED:-1}"  # Set to 0 to re-run completed sites
RETRY_FAILED="${RETRY_FAILED:-1}"  # Set to 1 to retry sites where all tasks failed
MAX_STEPS="${MAX_STEPS:-20}"  # Maximum steps per episode
SOM="${SOM:-0}"  # Set to 1 to enable Set-of-Marks (SoM) observation with bounding box screenshots
WAIT_AFTER_ACTION="${WAIT_AFTER_ACTION:-}"  # Seconds to wait after each action (default: 0.5, set higher for slow sites)
SKIP_SITES="${SKIP_SITES:-boardgamegeek}"

# Sites that need extra wait time for page rendering
SLOW_SITES="accuweather"

# Pre-flight: detect config mismatches and auto-fix CORS where possible.
echo "🔍 Verifying port configurations..."
python3 "$ROOT_DIR/tools/verify_ports.py" --mode misconfig || true
echo

# Function to detect active sites (frontend + backend running)
detect_active_sites() {
    python3 << 'PYEOF'
import json
import os
import subprocess
from pathlib import Path

# Get all listening ports
listening_ports = set()
try:
    output = subprocess.check_output(["ss", "-tlnp"], text=True)
    for line in output.split("\n"):
        if "LISTEN" in line:
            parts = line.split()
            for p in parts:
                if ":" in p:
                    port = p.split(":")[-1]
                    if port.isdigit():
                        listening_ports.add(int(port))
except:
    pass

websites_dir = Path("websites")
active_sites = []

for site in sorted(os.listdir(websites_dir)):
    site_path = websites_dir / site
    if not site_path.is_dir():
        continue
    
    # 1. Check task_instructions.json exists and has valid tasks
    task_file = site_path / "task_instructions.json"
    if not task_file.exists():
        continue
    
    try:
        data = json.loads(task_file.read_text())
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        if len(tasks) == 0:
            continue
        
        # Check if tasks have valid judge_for_webagent
        valid_tasks = 0
        for task in tasks:
            judge = task.get("judge_for_webagent")
            if judge and isinstance(judge, dict):
                if judge.get("checks") or judge.get("eval_type"):
                    valid_tasks += 1
        
        if valid_tasks == 0:
            continue
            
    except:
        continue
    
    # 2. Check ports are active (need at least 2: frontend + backend)
    ports_to_check = []
    
    # ports.json
    ports_file = site_path / "ports.json"
    if ports_file.exists():
        try:
            p = json.loads(ports_file.read_text()).get("ports", {})
            for key in ["WEB_PORT", "FRONTEND_PORT", "PORT", "BACKEND_PORT", "API_PORT"]:
                if p.get(key):
                    ports_to_check.append(int(p[key]))
        except:
            pass
    
    # .runtime/servers.json
    runtime = site_path / ".runtime" / "servers.json"
    if runtime.exists():
        try:
            data = json.loads(runtime.read_text())
            for key in ["frontend_port", "backend_port"]:
                if data.get(key):
                    ports_to_check.append(int(data[key]))
        except:
            pass
    
    active_ports = [p for p in set(ports_to_check) if p in listening_ports]
    
    # Need at least 1 active port (some sites serve everything on a single port)
    if len(active_ports) >= 1:
        active_sites.append(site)

# Print as space-separated for bash
print(" ".join(active_sites))
PYEOF
}

# Function to detect candidate sites (valid tasks, regardless of server state)
detect_candidate_sites() {
    python3 << 'PYEOF'
import json
import os
from pathlib import Path

websites_dir = Path("websites")
candidates = []

for site in sorted(os.listdir(websites_dir)):
    site_path = websites_dir / site
    if not site_path.is_dir():
        continue

    task_file = site_path / "task_instructions.json"
    if not task_file.exists():
        continue

    try:
        data = json.loads(task_file.read_text())
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        if len(tasks) == 0:
            continue

        valid_tasks = 0
        for task in tasks:
            judge = task.get("judge_for_webagent")
            if judge and isinstance(judge, dict):
                if judge.get("checks") or judge.get("eval_type"):
                    valid_tasks += 1

        if valid_tasks == 0:
            continue
    except:
        continue

    candidates.append(site)

print(" ".join(candidates))
PYEOF
}

# Function to check site experiment status
# Returns: "completed", "all_failed", "partial", or "none"
get_site_status() {
    local site="$1"
    local model="$2"
    local n_repeats="$3"
    local results_dir="$4"
    
    python3 << PYEOF
import json
import os
from pathlib import Path

site = "$site"
model = "$model"
n_repeats = $n_repeats
results_dir = Path("$results_dir")

# Get number of tasks for this site
root = Path(os.getenv("CLONE_CODING_ROOT", "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"))
task_file = root / "websites" / site / "task_instructions.json"

if not task_file.exists():
    print("none")
    exit()

try:
    data = json.loads(task_file.read_text())
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    n_tasks = len(tasks)
except:
    print("none")
    exit()

if n_tasks == 0:
    print("none")
    exit()

# Expected number of experiments
expected = n_tasks * n_repeats

# Extract core model name
model_core = model.split("/")[-1].lower().replace("_", "-")
site_pattern = f"verienv-{site}".lower()

completed = 0
successful = 0
total_found = 0

for study_dir in results_dir.iterdir():
    if not study_dir.is_dir():
        continue
    study_name = study_dir.name.lower()
    if site_pattern not in study_name:
        continue
    if model_core not in study_name:
        continue
        
    for exp_dir in study_dir.iterdir():
        if not exp_dir.is_dir():
            continue
        summary_file = exp_dir / "summary_info.json"
        if summary_file.exists():
            try:
                summary = json.loads(summary_file.read_text())
                if "cum_reward" in summary:
                    total_found += 1
                    completed += 1
                    # Check if it was successful (reward > 0)
                    if summary.get("cum_reward", 0) > 0:
                        successful += 1
                    # Check if it failed due to error
                    elif summary.get("err_msg"):
                        pass  # This is an error, not a success
            except:
                pass

if total_found == 0:
    print("none")
elif completed >= expected:
    if successful == 0:
        print("all_failed")  # All completed but none successful
    else:
        print("completed")
elif successful == 0:
    # Some experiments done, but ALL of them failed
    print("all_failed")
else:
    print("partial")
PYEOF
}

# Function to check and display active sites
check_active_sites() {
    echo "🔍 Checking active sites (frontend + backend running)..."
    echo ""
    
    python3 << 'PYEOF'
import json
import os
import subprocess
from pathlib import Path

# Get all listening ports
listening_ports = set()
try:
    output = subprocess.check_output(["ss", "-tlnp"], text=True)
    for line in output.split("\n"):
        if "LISTEN" in line:
            parts = line.split()
            for p in parts:
                if ":" in p:
                    port = p.split(":")[-1]
                    if port.isdigit():
                        listening_ports.add(int(port))
except:
    pass

websites_dir = Path("websites")
active = []
inactive = []

for site in sorted(os.listdir(websites_dir)):
    site_path = websites_dir / site
    if not site_path.is_dir():
        continue
    
    task_file = site_path / "task_instructions.json"
    if not task_file.exists():
        continue
    
    try:
        data = json.loads(task_file.read_text())
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        if len(tasks) == 0:
            continue
    except:
        continue
    
    ports_to_check = []
    ports_file = site_path / "ports.json"
    if ports_file.exists():
        try:
            p = json.loads(ports_file.read_text()).get("ports", {})
            for key in ["WEB_PORT", "FRONTEND_PORT", "PORT", "BACKEND_PORT", "API_PORT"]:
                if p.get(key):
                    ports_to_check.append(int(p[key]))
        except:
            pass
    
    runtime = site_path / ".runtime" / "servers.json"
    if runtime.exists():
        try:
            data = json.loads(runtime.read_text())
            for key in ["frontend_port", "backend_port"]:
                if data.get(key):
                    ports_to_check.append(int(data[key]))
        except:
            pass
    
    active_ports = [p for p in set(ports_to_check) if p in listening_ports]
    
    if len(active_ports) >= 1:
        active.append((site, len(tasks), active_ports[:2]))
    else:
        inactive.append((site, len(tasks), ports_to_check[:2] if ports_to_check else []))

print(f"✅ Active sites ({len(active)}):")
for site, task_count, ports in active:
    print(f"   {site}: {task_count} tasks, ports {ports}")

print(f"\n❌ Inactive sites ({len(inactive)}):")
for site, task_count, ports in inactive[:10]:
    print(f"   {site}: ports {ports} not listening")
if len(inactive) > 10:
    print(f"   ... and {len(inactive) - 10} more")

print(f"\n📊 Summary: {len(active)} active / {len(active) + len(inactive)} total")
PYEOF
}

show_help() {
    echo "🔬 VeriEnv Batch Experiment Runner"
    echo ""
    echo "Usage:"
    echo "  $0                              Run all active sites (auto-detected)"
    echo "  $0 target twitter               Run specific sites"
    echo "  $0 --som target twitter         Run with SoM enabled"
    echo "  $0 --sites-file good.json       Run only sites listed in JSON file"
    echo "  $0 --filter-success 3           Auto-filter: sites with >= 3 past successes"
    echo "  $0 --filter-success 3 --som     Combine flags"
    echo "  $0 --list                       List active sites"
    echo "  $0 --check                      Check which sites are active"
    echo ""
    echo "Options:"
    echo "  --som                      Enable Set-of-Marks (bounding box overlay on screenshots)"
    echo "  --sites-file FILE          Read site list from a JSON file ({\"sites\": [...]})"
    echo "  --filter-success N         Only run sites with >= N successful past trajectories"
    echo ""
    echo "Environment variables:"
    echo "  N_REPEATS=5                Number of trials per task (default: 5)"
    echo "  MODEL=openrouter/...       Model to use"
    echo "  JOBS=4                     Parallel jobs"
    echo "  MAX_STEPS=20               Maximum steps per episode (default: 20)"
    echo "  DRY_RUN=1                  Print commands without executing"
    echo "  RESULTS_DIR=./results      Where to save results"
    echo "  SOM=1                      Same as --som flag"
    echo ""
    echo "Example:"
    echo "  $0 --filter-success 3              # Run only well-working sites"
    echo "  $0 --filter-success 3 --som        # Same, with SoM enabled"
    echo "  $0 --sites-file good_sites.json    # Run from a curated list"
    echo "  N_REPEATS=3 MAX_STEPS=30 $0 target # Run specific site"
}

list_sites() {
    echo "📋 Detecting active sites (frontend + backend running)..."
    echo ""
    DETECTED=$(detect_active_sites)
    if [[ -z "$DETECTED" ]]; then
        echo "❌ No active sites found!"
        echo "   Make sure servers are running: tmux attach -t sites"
        exit 1
    fi
    
    IFS=' ' read -ra SITE_ARRAY <<< "$DETECTED"
    echo "✅ Active sites (${#SITE_ARRAY[@]} total):"
    echo ""
    for site in "${SITE_ARRAY[@]}"; do
        echo "  - $site"
    done
}

# Parse arguments
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

if [[ "$1" == "--list" ]]; then
    list_sites
    exit 0
fi

if [[ "$1" == "--check" ]]; then
    check_active_sites
    exit 0
fi

# Parse flags from arguments
POSITIONAL_ARGS=()
SITES_FILE=""
FILTER_SUCCESS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --som)
            SOM=1
            shift
            ;;
        --sites-file)
            SITES_FILE="$2"
            shift 2
            ;;
        --filter-success)
            FILTER_SUCCESS="$2"
            shift 2
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Determine which sites to run
if [[ -n "$SITES_FILE" ]]; then
    # Read sites from JSON file (expects {"sites": [...]} format)
    if [[ ! -f "$SITES_FILE" ]]; then
        echo "❌ Error: Sites file '$SITES_FILE' not found"
        exit 1
    fi
    SITES_FROM_FILE=$(python3 -c "
import json, sys
data = json.load(open('$SITES_FILE'))
sites = data.get('sites', data) if isinstance(data, dict) else data
print(' '.join(sites))
")
    read -ra SITES <<< "$SITES_FROM_FILE"
    echo "📄 Loaded ${#SITES[@]} sites from $SITES_FILE"
elif [[ -n "$FILTER_SUCCESS" ]]; then
    # Auto-filter from previous results: only sites with >= N successes
    SITES_FROM_FILTER=$(python3 "$SCRIPT_DIR/filter_sites.py" \
        --results-dir "$RESULTS_DIR" \
        --min-success "$FILTER_SUCCESS" \
        --quiet)
    # The script outputs the JSON path; read sites from it
    SITES_FROM_JSON=$(python3 -c "
import json, sys
data = json.load(open('$SITES_FROM_FILTER'))
print(' '.join(data['sites']))
")
    read -ra SITES <<< "$SITES_FROM_JSON"
    echo "🔍 Filtered to ${#SITES[@]} sites with >= $FILTER_SUCCESS successful trajectories"
elif [[ ${#POSITIONAL_ARGS[@]} -gt 0 ]]; then
    SITES=("${POSITIONAL_ARGS[@]}")
else
    # Auto-detect candidate sites (valid tasks)
    CANDIDATE_SITES_STR=$(detect_candidate_sites)
    read -ra CANDIDATE_SITES <<< "$CANDIDATE_SITES_STR"
    SITES=("${CANDIDATE_SITES[@]}")
fi

# Apply explicit skip list after site selection.
if [[ -n "$SKIP_SITES" ]]; then
    SKIP_SITES_NORMALIZED="${SKIP_SITES//,/ }"
    read -ra SKIP_SITE_ARRAY <<< "$SKIP_SITES_NORMALIZED"
    FILTERED_SITES=()
    SKIP_LOOKUP=" ${SKIP_SITE_ARRAY[*]} "
    for site in "${SITES[@]}"; do
        if [[ "$SKIP_LOOKUP" == *" $site "* ]]; then
            echo "⏭️  Excluding $site (skip list)"
            continue
        fi
        FILTERED_SITES+=("$site")
    done
    SITES=("${FILTERED_SITES[@]}")
fi

# Validate sites
for site in "${SITES[@]}"; do
    if [[ ! -d "websites/$site" ]]; then
        echo "❌ Error: Site '$site' not found in websites/"
        exit 1
    fi
done

# Activate venv
VENV_PATH="$ROOT_DIR/.venv-verienv"
if [[ -d "$VENV_PATH" ]]; then
    source "$VENV_PATH/bin/activate"
else
    echo "⚠️  Virtual environment not found. Run: bash tools/setup_verienv_agentlab_venv.sh"
fi

# Check API key
if [[ -z "$OPENROUTER_API_KEY" ]]; then
    if [[ -f "$ROOT_DIR/AgentLab/.env" ]]; then
        export $(grep -v '^#' "$ROOT_DIR/AgentLab/.env" | xargs)
    fi
fi

if [[ -z "$OPENROUTER_API_KEY" && "$MODEL" == openrouter/* ]]; then
    echo "❌ Error: OPENROUTER_API_KEY not set"
    echo "   Set it in AgentLab/.env or export it"
    exit 1
fi

# Set results directory
export AGENTLAB_EXP_ROOT="$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"

# Verify and create .runtime/servers.json for all sites to ensure correct port mapping
echo "🔍 Verifying port configurations..."
python3 << 'PYEOF'
import json
import socket
from pathlib import Path

def check_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False

websites = Path("websites")
fixed = 0
for site_dir in websites.iterdir():
    if not site_dir.is_dir():
        continue
    
    ports_file = site_dir / "ports.json"
    if not ports_file.exists():
        continue
    
    try:
        ports = json.loads(ports_file.read_text()).get("ports", {})
    except:
        continue
    
    # Try all candidate frontend ports, pick the one actually listening
    frontend_candidates = [int(ports[k]) for k in ("FRONTEND_PORT", "WEB_PORT", "UI_PORT", "PORT") if ports.get(k)]
    backend_port = ports.get("BACKEND_PORT") or ports.get("API_PORT")
    backend_port = int(backend_port) if backend_port else None
    
    if not frontend_candidates:
        continue
    
    # Find the first actually-listening frontend port
    frontend_port = None
    for p in frontend_candidates:
        if check_port(p):
            frontend_port = p
            break
    
    if frontend_port:
        runtime_dir = site_dir / ".runtime"
        runtime_dir.mkdir(exist_ok=True)
        runtime_data = {
            "frontend": {"port": frontend_port},
            "backend": {"port": backend_port} if backend_port and check_port(backend_port) else {},
        }
        (runtime_dir / "servers.json").write_text(json.dumps(runtime_data, indent=2))
        fixed += 1

print(f"✅ Verified {fixed} sites with .runtime/servers.json")
PYEOF

check_site_ports() {
    local site="$1"
    python3 -c "
import json, socket
from pathlib import Path

def check_port(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', int(port))) == 0
        s.close()
        return result
    except:
        return False

site_dir = Path('websites/$site')
frontend_ok = False
backend_ok = False

# Try .runtime/servers.json first
runtime = site_dir / '.runtime' / 'servers.json'
if runtime.exists():
    d = json.loads(runtime.read_text())
    fp = d.get('frontend',{}).get('port')
    bp = d.get('backend',{}).get('port')
    if fp and check_port(fp):
        frontend_ok = True
    if bp and check_port(bp):
        backend_ok = True

# If .runtime didn't work, try all candidates from ports.json
if not frontend_ok:
    pf = site_dir / 'ports.json'
    if pf.exists():
        p = json.loads(pf.read_text()).get('ports',{})
        for key in ('FRONTEND_PORT', 'WEB_PORT', 'UI_PORT', 'PORT'):
            val = p.get(key)
            if val and check_port(int(val)):
                frontend_ok = True
                break
        if not backend_ok:
            for key in ('BACKEND_PORT', 'API_PORT'):
                val = p.get(key)
                if val and check_port(int(val)):
                    backend_ok = True
                    break

# Need at least frontend running
if not frontend_ok:
    exit(1)
" 2>/dev/null
}

wait_for_site_ports() {
    local site="$1"
    local timeout="${2:-120}"
    local start_time
    start_time=$(date +%s)
    while true; do
        if check_site_ports "$site"; then
            return 0
        fi
        if (( $(date +%s) - start_time >= timeout )); then
            return 1
        fi
        sleep 5
    done
}

try_start_site() {
    local site="$1"
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "[DRY RUN] bash $ROOT_DIR/tools/run_site_with_reserved_ports.sh $site"
        return 0
    fi
    echo "🚀 Attempting to start $site..."
    bash "$ROOT_DIR/tools/run_site_with_reserved_ports.sh" "$site" || true
}

echo "🚀 VeriEnv Batch Experiment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -n "$SITES_FILE" ]]; then
    echo "📊 Sites: ${#SITES[@]} (from $SITES_FILE)"
elif [[ -n "$FILTER_SUCCESS" ]]; then
    echo "📊 Sites: ${#SITES[@]} (filtered: >= $FILTER_SUCCESS successes)"
elif [[ ${#POSITIONAL_ARGS[@]} -gt 0 ]]; then
    echo "📊 Sites: ${#SITES[@]} (specified)"
else
    echo "📊 Sites: ${#SITES[@]} (auto-detected)"
fi
echo "🔁 Repeats: $N_REPEATS per task"
echo "🤖 Model: $MODEL"
echo "⚡ Jobs: $JOBS"
echo "🦶 Max steps: $MAX_STEPS"
if [[ "$SOM" == "1" ]]; then
    echo "🎯 SoM: enabled (bounding box overlay)"
else
    echo "🎯 SoM: disabled"
fi
if [[ "$NO_THINK" == "1" ]]; then
    echo "🧠 Thinking: disabled (faster)"
else
    echo "🧠 Thinking: enabled"
fi
if [[ "$SKIP_COMPLETED" == "1" ]]; then
    echo "⏭️  Skip completed: yes"
else
    echo "⏭️  Skip completed: no (re-run all)"
fi
if [[ "$RETRY_FAILED" == "1" ]]; then
    echo "🔄 Retry failed: yes (all-failed sites will be retried)"
else
    echo "🔄 Retry failed: no"
fi
echo "🚫 Skip list: ${SKIP_SITES:-<none>}"
echo "📁 Results: $RESULTS_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Log file
LOG_FILE="$RESULTS_DIR/batch_run_$(date +%Y%m%d_%H%M%S).log"
echo "📝 Log file: $LOG_FILE"
echo ""

# Results tracking
PASSED_SITES=()
FAILED_SITES=()
SKIPPED_SITES=()

# Run each site
for i in "${!SITES[@]}"; do
    site="${SITES[$i]}"
    progress="[$((i+1))/${#SITES[@]}]"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$progress 🌐 Running: $site"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check experiment status
    site_status=$(get_site_status "$site" "$MODEL" "$N_REPEATS" "$RESULTS_DIR")
    
    # RETRY_FAILED takes priority over SKIP_COMPLETED
    if [[ "$RETRY_FAILED" == "1" ]] && [[ "$site_status" == "all_failed" ]]; then
        echo "🔄 Retrying $site (all previous attempts failed)"
    elif [[ "$RETRY_FAILED" == "0" ]] && [[ "$site_status" == "all_failed" ]]; then
        echo "⏭️  Skipping $site (all previous attempts failed)"
        SKIPPED_SITES+=("$site")
        continue
    elif [[ "$SKIP_COMPLETED" == "1" ]] && [[ "$site_status" == "completed" ]]; then
        echo "⏭️  Skipping $site (already completed with success)"
        SKIPPED_SITES+=("$site")
        continue
    fi
    
    # Verify server is running; try to start if not
    if ! check_site_ports "$site"; then
        try_start_site "$site"
        if ! wait_for_site_ports "$site" "${STARTUP_WAIT_SECONDS:-180}"; then
            echo "⚠️  Skipping $site (server not running after start attempt)"
            SKIPPED_SITES+=("$site")
            continue
        fi
    fi
    
    NO_THINK_FLAG=""
    if [[ "$NO_THINK" == "1" ]]; then
        NO_THINK_FLAG="--no-think"
    fi

    SOM_FLAG=""
    if [[ "$SOM" == "1" ]]; then
        SOM_FLAG="--som"
    fi

    WAIT_FLAG=""
    if [[ -n "$WAIT_AFTER_ACTION" ]]; then
        WAIT_FLAG="--wait-after-action $WAIT_AFTER_ACTION"
    elif echo " $SLOW_SITES " | grep -q " $site "; then
        WAIT_FLAG="--wait-after-action 3.0"
    fi
    
    CMD="python AgentLab/experiments/run_verienv.py \
        --site $site \
        --n-repeats $N_REPEATS \
        --model $MODEL \
        --jobs $JOBS \
        --max-steps $MAX_STEPS \
        --no-stop $NO_THINK_FLAG $SOM_FLAG $WAIT_FLAG"
    
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "[DRY RUN] $CMD"
        continue
    fi

    START_TIME=$(date +%s)

    # Safely run the command using 'eval' and proper array expansion to avoid parsing issues
    if eval "$CMD" 2>&1 | tee -a "$LOG_FILE"; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "✅ $site completed in ${DURATION}s"
        PASSED_SITES+=("$site")
    else
        echo "❌ $site failed"
        FAILED_SITES+=("$site")
    fi

done


# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 BATCH RUN SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Passed: ${#PASSED_SITES[@]}"
echo "❌ Failed: ${#FAILED_SITES[@]}"
echo "⏭️  Skipped: ${#SKIPPED_SITES[@]} (already completed)"

if [[ ${#FAILED_SITES[@]} -gt 0 ]]; then
    echo ""
    echo "Failed sites:"
    for site in "${FAILED_SITES[@]}"; do
        echo "  - $site"
    done
fi

echo ""
echo "📁 Results saved to: $RESULTS_DIR"
echo "📝 Log file: $LOG_FILE"
echo ""
echo "🔍 View results:"
echo "   ./start_dashboard.sh 5050"
echo ""
echo "📤 Extract successful trajectories:"
echo "   python tools/extract_successful_trajectories.py --latest"

