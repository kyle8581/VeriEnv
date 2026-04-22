#!/usr/bin/env bash
set -euo pipefail

ROOT="${CLONE_CODING_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
VENV_DIR="${ROOT}/.venv-verienv"

# AgentLab requires Python >=3.11,<3.13. Using 3.13 often forces source builds (e.g. greenlet) and fails.
# Allow overriding python binary via PYTHON_BIN (recommended: python3.12).
PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="python3.12"
  elif command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
  else
    PYTHON_BIN="python3"
  fi
fi

PY_VER="$("${PYTHON_BIN}" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"

if [[ "${PY_VER}" == "3.13" || "${PY_VER}" == "3.14" ]]; then
  echo "ERROR: ${PYTHON_BIN} is Python ${PY_VER}."
  echo "AgentLab requires Python >=3.11,<3.13, and Python 3.13 often fails to install deps (e.g. greenlet wheel build)."
  echo
  echo "Fix options:"
  echo "  - Install python3.12 and rerun"
  echo "  - Or rerun with: PYTHON_BIN=python3.12 bash tools/setup_verienv_agentlab_venv.sh"
  echo "  - Or use conda/mamba to create a py3.12 env, then rerun using that python"
  exit 1
fi

echo "==> Creating venv: ${VENV_DIR}"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip setuptools wheel

echo "==> Installing BrowserGym (core + experiments) editable"
python -m pip install -e "${ROOT}/BrowserGym/browsergym/core"
python -m pip install -e "${ROOT}/BrowserGym/browsergym/experiments"

echo "==> Installing AgentLab editable"
python -m pip install -e "${ROOT}/AgentLab"

echo
echo "Done."
echo "Activate with:"
echo "  source \"${VENV_DIR}/bin/activate\""
echo "Run a site benchmark with:"
echo "  python \"${ROOT}/AgentLab/experiments/run_verienv.py\" --site allrecipes --jobs 1"


