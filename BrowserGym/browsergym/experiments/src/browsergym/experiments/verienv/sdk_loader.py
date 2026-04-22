"""
Dynamic SDK loader for VeriEnv benchmark.
Loads the appropriate SDK client for each website.
"""
from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional, Tuple


# Cache for loaded SDK info
_sdk_cache: dict[str, dict[str, Any]] = {}


def _find_sdk_info(clone_coding_root: Path, site: str) -> Optional[dict[str, Any]]:
    """Find SDK package path and client class for a given site."""
    if site in _sdk_cache:
        return _sdk_cache[site]
    
    site_path = clone_coding_root / "websites" / site
    if not site_path.is_dir():
        return None
    
    # Possible SDK locations (in order of preference)
    possible_paths = [
        f"{site}_sdk",
        f"{site.replace('-', '_').replace('.', '_')}_sdk",
        "sdk/python",
        "python_sdk",
        "python-sdk",
        "sdk",
    ]
    
    for pp in possible_paths:
        full_path = site_path / pp
        if not full_path.is_dir():
            continue
        
        # Find client.py
        for root, dirs, files in os.walk(str(full_path)):
            if "client.py" in files:
                pkg_name = os.path.basename(root)
                client_path = os.path.join(root, "client.py")
                
                try:
                    with open(client_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find class XxxClient
                    match = re.search(r'class\s+(\w+Client)', content)
                    if match:
                        client_class = match.group(1)
                        sdk_info = {
                            "sdk_path": os.path.dirname(root),
                            "pkg_name": pkg_name,
                            "client_class": client_class,
                        }
                        _sdk_cache[site] = sdk_info
                        return sdk_info
                except Exception:
                    continue
    
    return None


def _ensure_sdk_in_path(sdk_path: str) -> None:
    """Add SDK path to sys.path if not already there."""
    if sdk_path not in sys.path:
        sys.path.insert(0, sdk_path)


def load_sdk_client(
    clone_coding_root: Path,
    site: str,
    base_url: str,
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Load and instantiate the SDK client for a given site.
    
    Returns:
        Tuple of (client_instance, error_message)
        If successful, error_message is None.
        If failed, client_instance is None.
    """
    sdk_info = _find_sdk_info(clone_coding_root, site)
    if not sdk_info:
        return None, f"SDK not found for site: {site}"
    
    _ensure_sdk_in_path(sdk_info["sdk_path"])
    
    try:
        # Import the SDK module
        module = importlib.import_module(sdk_info["pkg_name"])
        
        # Get the client class
        client_class = getattr(module, sdk_info["client_class"])
        
        # Instantiate the client with base_url
        # Most clients accept base_url as first positional or keyword arg
        try:
            client = client_class(base_url)
        except TypeError:
            # Some clients might use different parameter names
            try:
                client = client_class(base_url=base_url)
            except TypeError:
                try:
                    client = client_class(url=base_url)
                except TypeError:
                    client = client_class()  # No URL needed
        
        return client, None
        
    except Exception as e:
        return None, f"Failed to load SDK for {site}: {type(e).__name__}: {e}"


def get_sdk_context(
    clone_coding_root: Path,
    site: str,
    base_url: str,
) -> Tuple[dict[str, Any], Optional[str]]:
    """
    Create an execution context with SDK client and common utilities.
    
    Returns:
        Tuple of (context_dict, error_message)
    """
    client, error = load_sdk_client(clone_coding_root, site, base_url)
    
    if error:
        return {}, error
    
    # Build execution context
    context = {
        "client": client,
        "c": client,  # Short alias
        "base_url": base_url,
        "True": True,
        "False": False,
        "None": None,
        # Common utility functions
        "any": any,
        "all": all,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "sorted": sorted,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
    }
    
    # Also add the SDK module itself for direct imports
    sdk_info = _find_sdk_info(clone_coding_root, site)
    if sdk_info:
        try:
            module = importlib.import_module(sdk_info["pkg_name"])
            context[sdk_info["pkg_name"]] = module
            context[sdk_info["client_class"]] = getattr(module, sdk_info["client_class"])
        except Exception:
            pass
    
    return context, None

