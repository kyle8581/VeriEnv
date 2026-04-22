#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_RANGE = (12000, 19999)


def repo_root() -> Path:
    env = os.environ.get("CLONE_CODING_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def registry_path(root: Path) -> Path:
    return root / ".ports.json"

def per_site_ports_path(root: Path, site: str) -> Path:
    return root / "websites" / site / "ports.json"


def load_registry(root: Path) -> Dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        return {"version": 1, "range": list(DEFAULT_RANGE), "sites": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "range": list(DEFAULT_RANGE), "sites": {}}


def save_registry(root: Path, reg: Dict[str, Any]) -> None:
    path = registry_path(root)
    path.write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def save_per_site_ports(root: Path, site: str, ports: Dict[str, int]) -> None:
    p = per_site_ports_path(root, site)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "site": site, "ports": dict(sorted(ports.items()))}
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def alloc_port(used: set[int], start: int, end: int, host: str = "127.0.0.1") -> int:
    for p in range(start, end + 1):
        if p in used:
            continue
        if is_free(p, host=host):
            return p
    raise SystemExit(f"No free port found in range {start}-{end}")


ENV_PORT_RE = re.compile(r"\b([A-Z0-9_]*PORT)\b")


def guess_env_port_vars(start_servers_text: str) -> List[str]:
    # Common vars we want to reserve even if script doesn't mention explicitly.
    common = ["PORT", "WEB_PORT", "API_PORT", "FRONTEND_PORT", "BACKEND_PORT"]
    found = set(m.group(1) for m in ENV_PORT_RE.finditer(start_servers_text))
    ordered: List[str] = []
    for v in common:
        if v in found:
            ordered.append(v)
            found.remove(v)
    for v in sorted(found):
        if v.endswith("_PORT") or v == "PORT":
            ordered.append(v)
    # Dedup while preserving order
    out: List[str] = []
    seen: set[str] = set()
    for v in ordered:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def reserve_ports(root: Path, site: str, vars_: List[str]) -> Dict[str, int]:
    reg = load_registry(root)
    r0, r1 = reg.get("range") or list(DEFAULT_RANGE)
    sites: Dict[str, Any] = reg.setdefault("sites", {})
    entry: Dict[str, Any] = sites.setdefault(site, {"ports": {}})
    ports: Dict[str, int] = entry.setdefault("ports", {})

    # First, load existing per-site ports.json if it exists and merge into ports
    # This ensures we respect ports assigned by rebuild --fix-conflicts
    site_ports_file = per_site_ports_path(root, site)
    if site_ports_file.exists():
        try:
            existing = json.loads(site_ports_file.read_text(encoding="utf-8"))
            existing_ports = existing.get("ports", {})
            for k, v in existing_ports.items():
                if isinstance(v, int) and k not in ports:
                    ports[k] = v
                elif isinstance(v, int) and k in ports and ports[k] != v:
                    # Per-site file takes precedence (from rebuild --fix-conflicts)
                    ports[k] = v
        except Exception:
            pass

    # Gather used ports across all reservations (central registry)
    used: set[int] = set()
    for s in sites.values():
        for p in (s.get("ports") or {}).values():
            if isinstance(p, int):
                used.add(p)
    
    # Also scan all per-site ports.json files to avoid conflicts
    websites_dir = root / "websites"
    if websites_dir.is_dir():
        for site_dir in websites_dir.iterdir():
            if not site_dir.is_dir():
                continue
            pf = site_dir / "ports.json"
            if pf.exists():
                try:
                    data = json.loads(pf.read_text(encoding="utf-8"))
                    for p in (data.get("ports") or {}).values():
                        if isinstance(p, int):
                            used.add(p)
                except Exception:
                    pass

    # Allocate missing vars
    for v in vars_:
        if v in ports and isinstance(ports[v], int):
            continue
        ports[v] = alloc_port(used, int(r0), int(r1))
        used.add(ports[v])

    save_registry(root, reg)
    reserved = {k: int(ports[k]) for k in vars_ if k in ports}
    # Also write a per-website file for portability/debugging.
    save_per_site_ports(root, site, reserved)
    return reserved


def cmd_reserve(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    site = args.site
    vars_ = args.vars or []
    if not vars_ and args.from_start_servers:
        text = (root / "websites" / site / "start_servers.sh").read_text(encoding="utf-8", errors="ignore")
        vars_ = guess_env_port_vars(text)
    if not vars_:
        vars_ = ["PORT"]
    reserved = reserve_ports(root, site, vars_)
    print(json.dumps({"ok": True, "site": site, "reserved": reserved}, indent=2))
    return 0


def cmd_print_exports(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    reg = load_registry(root)
    site = args.site
    ports = ((reg.get("sites") or {}).get(site) or {}).get("ports") or {}
    for k, v in sorted(ports.items()):
        if isinstance(v, int):
            print(f'export {k}="{v}"')
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else repo_root()
    reg = load_registry(root)
    print(json.dumps(reg, indent=2))
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    """Rebuild registry from all per-site ports.json files and fix conflicts."""
    root = Path(args.root).resolve() if args.root else repo_root()
    websites_dir = root / "websites"
    fix_conflicts = args.fix_conflicts
    dry_run = args.dry_run
    
    if not websites_dir.is_dir():
        print(f"ERROR: websites dir not found: {websites_dir}")
        return 1
    
    # Step 1: Collect all ports from individual ports.json files
    print("==> Scanning all ports.json files...")
    all_sites: Dict[str, Dict[str, int]] = {}
    port_to_sites: Dict[int, List[Tuple[str, str]]] = {}  # port -> [(site, var), ...]
    
    for site_dir in sorted(websites_dir.iterdir()):
        if not site_dir.is_dir():
            continue
        ports_file = site_dir / "ports.json"
        if not ports_file.exists():
            continue
        
        try:
            data = json.loads(ports_file.read_text(encoding="utf-8"))
            site_name = data.get("site") or site_dir.name
            ports = data.get("ports", {})
            if isinstance(ports, dict):
                all_sites[site_name] = {}
                for var, port in ports.items():
                    if isinstance(port, int):
                        all_sites[site_name][var] = port
                        port_to_sites.setdefault(port, []).append((site_name, var))
        except Exception as e:
            print(f"  WARNING: Could not read {ports_file}: {e}")
    
    print(f"  Found {len(all_sites)} sites with ports.json")
    
    # Step 2: Find conflicts
    conflicts: Dict[int, List[Tuple[str, str]]] = {
        port: sites for port, sites in port_to_sites.items() if len(sites) > 1
    }
    
    if conflicts:
        print(f"\n==> Found {len(conflicts)} port conflicts:")
        for port in sorted(conflicts.keys()):
            sites = conflicts[port]
            print(f"  Port {port}:")
            for site, var in sites:
                print(f"    - {site} ({var})")
    else:
        print("\n==> No conflicts found!")
    
    if not fix_conflicts or not conflicts:
        # Just rebuild the registry without fixing
        if not dry_run:
            reg = {"version": 1, "range": list(DEFAULT_RANGE), "sites": {}}
            for site_name, ports in all_sites.items():
                reg["sites"][site_name] = {"ports": ports}
            save_registry(root, reg)
            print(f"\n==> Registry rebuilt with {len(all_sites)} sites")
        return 0
    
    # Step 3: Fix conflicts by reassigning ports
    print("\n==> Fixing conflicts...")
    r0, r1 = DEFAULT_RANGE
    
    # Collect all used ports (keeping the first occurrence, reassigning others)
    used_ports: set[int] = set()
    reassignments: List[Tuple[str, str, int, int]] = []  # (site, var, old_port, new_port)
    
    # First pass: mark first occurrence of each port as "used"
    first_use: Dict[int, Tuple[str, str]] = {}
    for port, sites in sorted(port_to_sites.items()):
        if len(sites) == 1:
            # No conflict
            used_ports.add(port)
        else:
            # Conflict - keep the first one
            first_site, first_var = sites[0]
            first_use[port] = (first_site, first_var)
            used_ports.add(port)
    
    # Second pass: reassign conflicting ports
    for port, sites in sorted(conflicts.items()):
        # Skip the first site (it keeps the port)
        for site, var in sites[1:]:
            # Find a new port
            new_port = alloc_port(used_ports, r0, r1)
            used_ports.add(new_port)
            
            # Update the site's ports
            all_sites[site][var] = new_port
            reassignments.append((site, var, port, new_port))
            print(f"  {site}.{var}: {port} -> {new_port}")
    
    # Step 4: Save everything
    if dry_run:
        print("\n==> DRY RUN - no changes made")
    else:
        print("\n==> Saving changes...")
        
        # Save central registry
        reg = {"version": 1, "range": list(DEFAULT_RANGE), "sites": {}}
        for site_name, ports in all_sites.items():
            reg["sites"][site_name] = {"ports": ports}
        save_registry(root, reg)
        print(f"  Saved central registry: {registry_path(root)}")
        
        # Save individual ports.json files
        for site_name, ports in all_sites.items():
            save_per_site_ports(root, site_name, ports)
        print(f"  Updated {len(all_sites)} individual ports.json files")
    
    # Summary
    print(f"\n==> Summary:")
    print(f"  Total sites: {len(all_sites)}")
    print(f"  Conflicts found: {len(conflicts)}")
    print(f"  Ports reassigned: {len(reassignments)}")
    
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="", help="Repo root (defaults to autodetect)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("reserve", help="Reserve ports for a website")
    sp.add_argument("site", help="Website directory name under websites/")
    sp.add_argument("--vars", nargs="*", default=[], help="Env vars to reserve (e.g. FRONTEND_PORT BACKEND_PORT)")
    sp.add_argument("--from-start-servers", action="store_true", help="Infer vars by scanning start_servers.sh")
    sp.set_defaults(func=cmd_reserve)

    sp = sub.add_parser("exports", help="Print export statements for a website's reserved ports")
    sp.add_argument("site")
    sp.set_defaults(func=cmd_print_exports)

    sp = sub.add_parser("list", help="Print entire registry JSON")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("rebuild", help="Rebuild registry from all per-site ports.json files")
    sp.add_argument("--fix-conflicts", action="store_true", help="Automatically reassign conflicting ports")
    sp.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    sp.set_defaults(func=cmd_rebuild)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


