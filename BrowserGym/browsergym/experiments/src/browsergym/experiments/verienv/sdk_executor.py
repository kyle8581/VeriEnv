from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from .sdk_helpers import get_helper_env

def _find_sdk_package(clone_coding_root: Path, site: str) -> tuple[Path | None, str | None]:
    """
    Heuristically locate the python SDK package for a site.

    Returns (sys_path_to_add, package_name) or (None, None) if not found.
    """
    site_dir = clone_coding_root / "websites" / site
    if not site_dir.exists():
        return None, None

    candidates = [
        "sdk/python",
        "python_sdk",
        "python-sdk",
        "sdk-python",  # menards uses this
        "sdk",
        f"{site}_sdk",
    ]

    for cand in candidates:
        base = site_dir / cand
        if not base.exists():
            continue
        # Walk to find client.py
        for root, _dirs, files in os.walk(base):
            if "client.py" in files:
                package_dir = Path(root)
                package_name = package_dir.name  # e.g., instacart_sdk
                sys_path = package_dir.parent  # add parent so package imports resolve
                return sys_path, package_name

    return None, None


def load_sdk_module(clone_coding_root: Path, site: str) -> ModuleType | None:
    """
    Load the SDK python module for a site, if present.
    """
    sys_path, package_name = _find_sdk_package(clone_coding_root, site)
    if not sys_path or not package_name:
        return None

    sys_path_str = str(sys_path)
    if sys_path_str not in sys.path:
        sys.path.insert(0, sys_path_str)

    try:
        return importlib.import_module(package_name)
    except Exception:
        return None


def _extract_script_lines(judge: dict[str, Any]) -> list[str]:
    """
    Extract executable python lines from judge_for_webagent checks.
    - For dynamic checks (op-based), generates function calls.
    - Prefers `_original_string` (complete code) over `_unparsed` (may be partial).
    - Strips leading 'rprog:' prefixes.
    """
    lines: list[str] = []

    def _split_and_add(raw: str) -> None:
        raw = raw.replace("rprog:", "", 1).strip()
        for part in raw.split(";"):
            part = part.strip()
            if part:
                lines.append(part)

    # First, check if there's a complete _original_string (preferred)
    original_string = judge.get("_original_string")
    if original_string:
        _split_and_add(str(original_string))
        return lines

    checks = judge.get("checks") or []
    for c in checks:
        if not isinstance(c, dict):
            continue
        
        # Handle dynamic op-based checks (e.g., cart_has_items, cart_subtotal_exists)
        if c.get("_dynamic"):
            op = c.get("op", "")
            expected = c.get("expected", "")
            if op == "cart_has_items":
                # Parse expected like "quantity>=1"
                import re
                m = re.match(r"quantity>=(\d+)", str(expected))
                if m:
                    qty = m.group(1)
                    lines.append(f"cart_has_items(quantity={qty})")
                else:
                    lines.append("cart_has_items()")
                continue
            elif op == "cart_subtotal_exists":
                lines.append("cart_subtotal_exists()")
                continue
            # Fallback: call op as function
            lines.append(f"{op}()")
            continue
        
        raw = c.get("_unparsed") or c.get("_original")
        if raw:
            _split_and_add(str(raw))

    return lines


def eval_rprog_generic(
    *,
    clone_coding_root: Path,
    site: str,
    judge: dict[str, Any],
    backend_url: str,
    frontend_url: str,
    browser_context: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Execute rprog checks by running the embedded python snippets with the site's SDK.
    Returns (passed, details).
    """
    sdk_module = load_sdk_module(clone_coding_root, site)
    if sdk_module is None:
        return False, {"error": "SDK module not found", "site": site}

    script_lines = _extract_script_lines(judge)
    if not script_lines:
        return False, {"error": "No executable rprog checks", "site": site}

    env: dict[str, Any] = {
        "__builtins__": __builtins__,
        "base_url": backend_url,
        "backend_url": backend_url,
        "frontend_url": frontend_url,
    }

    # Expose SDK module symbols (Client classes, helpers, etc.)
    for name, value in sdk_module.__dict__.items():
        if not name.startswith("_"):
            env.setdefault(name, value)

    # Inject site-specific helper functions (cart_contains, etc.)
    env.update(get_helper_env(
        site,
        backend_url=backend_url,
        frontend_url=frontend_url,
        sdk_module=sdk_module,
        browser_context=browser_context or {},
    ))

    code = "\n".join(script_lines)
    try:
        exec(compile(code, filename="<rprog_sdk>", mode="exec"), env, env)
        return True, {"status": "ok"}
    except AssertionError as e:
        return False, {"error": f"AssertionError: {e}", "code": code}
    except Exception as e:
        return False, {"error": f"{type(e).__name__}: {e}", "code": code}

