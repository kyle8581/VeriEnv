#!/usr/bin/env python3
"""
Validate port configurations across all websites.
Run this before starting all sites to catch issues early.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

WEBSITES_DIR = Path(os.getenv("CLONE_CODING_ROOT", str(Path(__file__).resolve().parents[1]))) / "websites"


def main():
    print("=" * 60)
    print("Port Configuration Validator")
    print("=" * 60)
    
    issues = []
    port_usage = defaultdict(list)  # port -> list of (site, type)
    
    for site_dir in sorted(WEBSITES_DIR.iterdir()):
        if not site_dir.is_dir():
            continue
        
        site_name = site_dir.name
        ports_json = site_dir / "ports.json"
        start_script = site_dir / "start_servers.sh"
        
        # Check ports.json
        if not ports_json.exists():
            if start_script.exists():
                issues.append(f"⚠️  {site_name}: start_servers.sh exists but no ports.json")
            continue
        
        try:
            data = json.loads(ports_json.read_text())
            ports = data.get("ports", {})
        except Exception as e:
            issues.append(f"❌ {site_name}: Invalid ports.json - {e}")
            continue
        
        # Get frontend and backend ports
        fe_port = ports.get("FRONTEND_PORT") or ports.get("WEB_PORT") or ports.get("UI_PORT") or ports.get("PORT")
        be_port = ports.get("BACKEND_PORT") or ports.get("API_PORT")
        
        if fe_port:
            port_usage[fe_port].append((site_name, "frontend"))
        if be_port:
            port_usage[be_port].append((site_name, "backend"))
        
        # Check start_servers.sh reads from ports.json
        if start_script.exists():
            content = start_script.read_text()
            if 'ports.json' not in content:
                issues.append(f"⚠️  {site_name}: start_servers.sh doesn't read from ports.json")
    
    # Check for port conflicts
    print("\n📊 Port Conflicts:")
    conflicts = 0
    for port, users in sorted(port_usage.items()):
        if len(users) > 1:
            # Check if it's the same site (frontend + backend on same port is OK for some apps)
            sites = set(u[0] for u in users)
            if len(sites) > 1:
                conflicts += 1
                print(f"  ❌ Port {port}: {users}")
    
    if conflicts == 0:
        print("  ✅ No port conflicts found!")
    
    # Print issues
    print(f"\n⚠️  Configuration Issues ({len(issues)}):")
    for issue in issues[:20]:
        print(f"  {issue}")
    if len(issues) > 20:
        print(f"  ... and {len(issues) - 20} more")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Total sites with ports.json: {len(port_usage)}")
    print(f"Port conflicts: {conflicts}")
    print(f"Configuration issues: {len(issues)}")
    print("=" * 60)
    
    return 0 if conflicts == 0 and len(issues) == 0 else 1


if __name__ == "__main__":
    exit(main())




