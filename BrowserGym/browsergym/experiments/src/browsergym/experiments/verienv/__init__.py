"""
VeriEnv: Local website-based benchmark for BrowserGym/AgentLab.

Tasks are generated from `{CLONE_CODING_ROOT}/websites/*/task_instructions.json`.

Task ids: `verienv.<site>.<idx>` (idx is the index in the JSON list).
"""

from __future__ import annotations

from .registry import ensure_registered  # noqa: F401

# Register tasks on import (BrowserGym loop does lazy import based on task_name prefix).
ensure_registered()


