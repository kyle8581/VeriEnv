from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from browsergym.core.registration import register_task

from .task import VeriEnvTask

_REGISTERED = False


def _find_clone_coding_root() -> Path:
    # Preferred explicit override
    env = os.getenv("CLONE_CODING_ROOT")
    if env:
        return Path(env).resolve()

    # Infer from this file location by searching parents for `websites/`
    here = Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "websites").is_dir():
            return p
    # Fallback to the known path used in this workspace
    return Path("{CLONE_CODING_ROOT}").resolve()


def _load_tasks(site_dir: Path) -> list[dict[str, Any]]:
    path = site_dir / "task_instructions.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(data, list):
        tasks = data
    elif isinstance(data, dict):
        tasks = data.get("tasks") or data.get("data") or data.get("items") or []
    else:
        tasks = []

    if not isinstance(tasks, list):
        return []
    # Keep only dict tasks
    return [t for t in tasks if isinstance(t, dict)]


def ensure_registered() -> None:
    """Register all verienv tasks once per process."""
    global _REGISTERED
    if _REGISTERED:
        return

    root = _find_clone_coding_root()
    websites_dir = root / "websites"
    if not websites_dir.is_dir():
        _REGISTERED = True
        return

    for site_dir in sorted(websites_dir.iterdir()):
        if not site_dir.is_dir():
            continue
        tasks = _load_tasks(site_dir)
        if not tasks:
            continue

        site = site_dir.name
        for idx, task in enumerate(tasks):
            # optional filtering
            if task.get("is_valid") is False:
                continue
            task_id = f"verienv.{site}.{idx}"
            register_task(
                id=task_id,
                task_class=VeriEnvTask,
                default_task_kwargs={
                    "clone_coding_root": str(root),
                    "site": site,
                    "task_index": idx,
                },
                # local sites should be deterministic if DB isn't shared/reset; keep nondeterministic=True
                nondeterministic=True,
            )

    _REGISTERED = True


