#!/bin/bash
# =============================================================================
# VeriEnv Experiment Runner
# Runs browser agent experiments on local clone-coding websites
# =============================================================================

set -e

# ----------------------------- Configuration ---------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/.venv-verienv"
RESULTS_DIR="${AGENTLAB_EXP_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/results}"

# Default values
DEFAULT_VLLM_URL="${VLLM_API_URL:-http://localhost:8008/v1}"
DEFAULT_MODEL="vllm/qwen3-4b"
DEFAULT_JOBS=1
DEFAULT_REPEATS=1

# ----------------------------- Usage -----------------------------------------
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] --site <website>

Run VeriEnv browser agent experiments on clone-coding websites.

Required:
  --site, -s <name>       Website to test (e.g., allrecipes, babycenter, accuweather)

Options:
  --model, -m <model>     LLM model to use (default: $DEFAULT_MODEL)
  --jobs, -j <n>          Number of parallel jobs (default: $DEFAULT_JOBS)
  --repeats, -r <n>       Repeat each task N times (default: $DEFAULT_REPEATS)
  --vllm-url <url>        vLLM API URL (default: $DEFAULT_VLLM_URL)
  --no-stop               Don't stop the website server after experiment
  --headless              Run browser in headless mode (default: true)
  --no-headless           Run browser with visible UI
  --list-models           List available models
  --list-sites            List available websites
  --help, -h              Show this help message

Environment:
  AGENTLAB_EXP_ROOT       Results directory (default: $RESULTS_DIR)
  VLLM_API_URL            vLLM API URL (overridden by --vllm-url)
  OPENROUTER_API_KEY      API key for OpenRouter models (loaded from .env)

Examples:
  $(basename "$0") --site allrecipes
  $(basename "$0") --site allrecipes --model openrouter/meta-llama/llama-3.1-8b-instruct
  $(basename "$0") --site babycenter --jobs 2 --repeats 3
  $(basename "$0") --site accuweather --no-headless
  $(basename "$0") --site apartments --model vllm/qwen3-4b --vllm-url http://localhost:8008/v1

EOF
    exit 0
}

# ----------------------------- List helpers ----------------------------------
list_models() {
    cat <<EOF
Available models (via OpenRouter):
  openrouter/qwen/qwen3-8b                      (default, cheap)
  openrouter/meta-llama/llama-3.1-8b-instruct   (fast, good quality)
  openrouter/meta-llama/llama-3.1-70b-instruct  (high quality)
  openrouter/meta-llama/llama-3.1-405b-instruct (best quality, expensive)
  openrouter/anthropic/claude-3.5-sonnet:beta   (vision support)
  openrouter/anthropic/claude-3.7-sonnet        (vision support)
  openrouter/deepseek/deepseek-r1               (reasoning model)
  openrouter/openai/o3-mini                     (reasoning model)

Note: Check llm_configs.py for full list of supported models.
EOF
    exit 0
}

list_sites() {
    echo "Available websites with task_instructions.json:"
    echo ""
    for dir in "${SCRIPT_DIR}/websites/"*/; do
        site=$(basename "$dir")
        task_file="${dir}task_instructions.json"
        if [[ -f "$task_file" ]]; then
            count=$(python3 -c "import json; d=json.load(open('$task_file')); print(len(d) if isinstance(d,list) else len(d.get('tasks',d.get('data',[]))))" 2>/dev/null || echo "?")
            printf "  %-20s (%s tasks)\n" "$site" "$count"
        fi
    done
    exit 0
}

# ----------------------------- Parse arguments -------------------------------
SITE=""
MODEL="$DEFAULT_MODEL"
JOBS="$DEFAULT_JOBS"
REPEATS="$DEFAULT_REPEATS"
VLLM_URL="$DEFAULT_VLLM_URL"
NO_STOP=""
HEADLESS="--headless"

while [[ $# -gt 0 ]]; do
    case $1 in
        --site|-s)
            SITE="$2"
            shift 2
            ;;
        --model|-m)
            MODEL="$2"
            shift 2
            ;;
        --jobs|-j)
            JOBS="$2"
            shift 2
            ;;
        --repeats|-r)
            REPEATS="$2"
            shift 2
            ;;
        --vllm-url)
            VLLM_URL="$2"
            shift 2
            ;;
        --no-stop)
            NO_STOP="--no-stop"
            shift
            ;;
        --headless)
            HEADLESS="--headless"
            shift
            ;;
        --no-headless)
            HEADLESS=""
            shift
            ;;
        --list-models)
            list_models
            ;;
        --list-sites)
            list_sites
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# ----------------------------- Validation ------------------------------------
if [[ -z "$SITE" ]]; then
    echo "Error: --site is required"
    echo "Use --list-sites to see available websites"
    echo "Use --help for usage information."
    exit 1
fi

SITE_DIR="${SCRIPT_DIR}/websites/${SITE}"
if [[ ! -d "$SITE_DIR" ]]; then
    echo "Error: Website '$SITE' not found at $SITE_DIR"
    echo "Use --list-sites to see available websites"
    exit 1
fi

TASK_FILE="${SITE_DIR}/task_instructions.json"
if [[ ! -f "$TASK_FILE" ]]; then
    echo "Error: No task_instructions.json found for '$SITE'"
    exit 1
fi

if [[ ! -d "$VENV_PATH" ]]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Run: bash tools/setup_verienv_agentlab_venv.sh"
    exit 1
fi

# ----------------------------- Setup environment -----------------------------
echo "=============================================="
echo "VeriEnv Experiment Runner"
echo "=============================================="
echo "Site:      $SITE"
echo "Model:     $MODEL"
echo "Jobs:      $JOBS"
echo "Repeats:   $REPEATS"
echo "vLLM URL:  $VLLM_URL"
echo "Headless:  $([ -n "$HEADLESS" ] && echo 'yes' || echo 'no')"
echo "Results:   $RESULTS_DIR"
echo "=============================================="
echo ""

# Set environment variables
export AGENTLAB_EXP_ROOT="$RESULTS_DIR"
export VLLM_API_URL="$VLLM_URL"

# Create results directory if it doesn't exist
mkdir -p "$RESULTS_DIR"

# Activate virtual environment
source "${VENV_PATH}/bin/activate"

# Load .env file for API keys
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

# ----------------------------- Run experiment --------------------------------
echo "Starting experiment..."
echo ""

python "${SCRIPT_DIR}/AgentLab/experiments/run_verienv.py" \
    --site "$SITE" \
    --model "$MODEL" \
    --jobs "$JOBS" \
    --n-repeats "$REPEATS" \
    $HEADLESS \
    $NO_STOP

# Find the most recent experiment directory
LATEST_STUDY=$(ls -td "${RESULTS_DIR}"/*"${SITE}"* 2>/dev/null | head -n1)

if [[ -n "$LATEST_STUDY" && -d "$LATEST_STUDY" ]]; then
    echo ""
    echo "=============================================="
    echo "Generating detailed reports..."
    echo "=============================================="
    python "${SCRIPT_DIR}/tools/generate_exp_report.py" "$LATEST_STUDY"
fi

echo ""
echo "=============================================="
echo "Experiment completed!"
echo "Results saved to: $RESULTS_DIR"
echo "=============================================="

