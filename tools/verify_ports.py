#!/usr/bin/env python3
"""
Verify and fix port/CORS configurations for websites.
Separates not-running sites from real configuration mismatches.
"""
import argparse
import ast
import json
import socket
import subprocess
from pathlib import Path


def get_listening_ports() -> dict[int, str]:
    """Get all listening ports and their process info."""
    result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
    ports: dict[int, str] = {}
    for line in result.stdout.split("\n"):
        if "LISTEN" not in line:
            continue
        parts = line.split()
        for p in parts:
            if ":" in p:
                port_str = p.split(":")[-1]
                if port_str.isdigit():
                    port = int(port_str)
                    proc_info = ""
                    for part in parts:
                        if "users:" in part:
                            proc_info = part
                            break
                    ports[port] = proc_info
    return ports


def check_port(port: int) -> bool:
    """Check if a port is listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


def resolve_config_ports(ports: dict) -> tuple[int | None, int | None]:
    frontend = ports.get("FRONTEND_PORT") or ports.get("WEB_PORT") or ports.get("UI_PORT") or ports.get("PORT")
    backend = ports.get("BACKEND_PORT") or ports.get("API_PORT")
    return (int(frontend) if frontend else None), (int(backend) if backend else None)


def read_runtime_ports(site_dir: Path) -> tuple[int | None, int | None]:
    runtime_file = site_dir / ".runtime" / "servers.json"
    if not runtime_file.exists():
        return None, None
    try:
        data = json.loads(runtime_file.read_text())
        frontend = data.get("frontend", {}).get("port")
        backend = data.get("backend", {}).get("port")
        return (int(frontend) if frontend else None), (int(backend) if backend else None)
    except Exception:
        return None, None


def write_runtime(site_dir: Path, frontend: int | None, backend: int | None) -> None:
    runtime_dir = site_dir / ".runtime"
    runtime_dir.mkdir(exist_ok=True)
    runtime_data = {
        "frontend": {"port": frontend} if frontend else {},
        "backend": {"port": backend} if backend else {},
    }
    (runtime_dir / "servers.json").write_text(json.dumps(runtime_data, indent=2))


def update_cors_origins(config_path: Path, frontend_port: int) -> bool:
    """Ensure cors_origins includes localhost + 127.0.0.1 for frontend_port."""
    lines = config_path.read_text().splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if "cors_origins" not in line or "=" not in line:
            continue
        left, right = line.split("=", 1)
        value_str = right.split("#", 1)[0].strip()
        try:
            parsed = ast.literal_eval(value_str)
        except Exception:
            continue

        if isinstance(parsed, str):
            items = [p.strip() for p in parsed.split(",") if p.strip()]
            is_string = True
        elif isinstance(parsed, (list, tuple, set)):
            items = list(parsed)
            is_string = False
        else:
            continue

        desired = [
            f"http://localhost:{frontend_port}",
            f"http://127.0.0.1:{frontend_port}",
        ]
        changed = False
        for d in desired:
            if d not in items:
                items.append(d)
                changed = True

        if not changed:
            return False

        if is_string:
            new_value = repr(", ".join(items))
        else:
            new_value = "[" + ", ".join(repr(i) for i in items) + "]"

        lines[idx] = f"{left.rstrip()} = {new_value}\n"
        config_path.write_text("".join(lines))
        return True

    return False


def find_cors_config(site_dir: Path) -> Path | None:
    candidates = [
        site_dir / "backend" / "app" / "core" / "config.py",
        site_dir / "backend" / "app" / "config.py",
        site_dir / "backend" / "app" / "settings.py",
        site_dir / "apps" / "api" / "app" / "config.py",
        site_dir / "apps" / "api" / "app" / "settings.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def verify_site(
    site_dir: Path,
    listening_ports: dict[int, str],
    *,
    write_runtime_files: bool,
    fix_cors: bool,
) -> dict:
    site = site_dir.name
    result = {"site": site, "status": "unknown", "issues": [], "fixes": []}

    ports_file = site_dir / "ports.json"
    if not ports_file.exists():
        result["status"] = "no_config"
        return result

    try:
        ports = json.loads(ports_file.read_text()).get("ports", {})
    except Exception:
        result["status"] = "invalid_config"
        result["issues"].append("Cannot parse ports.json")
        return result

    configured_frontend, configured_backend = resolve_config_ports(ports)
    if not configured_frontend:
        result["status"] = "no_frontend_port"
        result["issues"].append("No frontend port configured")
        return result

    runtime_frontend, runtime_backend = read_runtime_ports(site_dir)

    actual_frontend = None
    if runtime_frontend and runtime_frontend in listening_ports:
        actual_frontend = runtime_frontend
    elif configured_frontend in listening_ports:
        actual_frontend = configured_frontend

    actual_backend = None
    if runtime_backend and runtime_backend in listening_ports:
        actual_backend = runtime_backend
    elif configured_backend and configured_backend in listening_ports:
        actual_backend = configured_backend

    if not actual_frontend and not actual_backend:
        result["status"] = "not_running"
        result["issues"].append("Frontend/Backend not listening")
        return result

    if actual_frontend and configured_frontend != actual_frontend:
        result["issues"].append(
            f"Frontend port mismatch (ports.json {configured_frontend} != running {actual_frontend})"
        )

    if configured_backend and actual_backend and configured_backend != actual_backend:
        result["issues"].append(
            f"Backend port mismatch (ports.json {configured_backend} != running {actual_backend})"
        )

    if configured_backend and not actual_backend:
        result["issues"].append("Backend not listening")

    if result["issues"]:
        result["status"] = "misconfig"
    else:
        result["status"] = "ok"

    result["frontend_port"] = actual_frontend or configured_frontend
    result["backend_port"] = actual_backend or configured_backend

    if write_runtime_files:
        write_runtime(site_dir, result["frontend_port"], result["backend_port"])

    if fix_cors and result["frontend_port"]:
        cors_path = find_cors_config(site_dir)
        if cors_path and update_cors_origins(cors_path, int(result["frontend_port"])):
            result["fixes"].append(f"Updated cors_origins in {cors_path}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "misconfig"], default="all")
    parser.add_argument("--no-fix-cors", action="store_true", help="Do not update CORS origins")
    parser.add_argument("--no-runtime", action="store_true", help="Do not write .runtime/servers.json")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    websites_dir = root / "websites"
    listening_ports = get_listening_ports()

    print(f"Found {len(listening_ports)} listening ports\n")

    results = {
        "ok": [],
        "misconfig": [],
        "not_running": [],
        "invalid_config": [],
        "no_config": [],
        "no_frontend_port": [],
    }

    for site_dir in sorted(websites_dir.iterdir()):
        if not site_dir.is_dir():
            continue

        result = verify_site(
            site_dir,
            listening_ports,
            write_runtime_files=not args.no_runtime,
            fix_cors=not args.no_fix_cors,
        )
        results.setdefault(result["status"], []).append(result)

        if args.mode == "misconfig":
            if result["status"] != "misconfig":
                continue
            print(f"❌ {result['site']}: {', '.join(result['issues'])}")
            for fix in result.get("fixes", []):
                print(f"   ✅ {fix}")
            continue

        if result["status"] == "ok":
            continue
        if result["status"] == "not_running":
            print(f"⚪ {result['site']}: not running")
            continue
        if result["status"] in {"invalid_config", "no_config", "no_frontend_port"}:
            print(f"⚠️  {result['site']}: {', '.join(result['issues'])}")
            continue
        if result["status"] == "misconfig":
            print(f"❌ {result['site']}: {', '.join(result['issues'])}")
            for fix in result.get("fixes", []):
                print(f"   ✅ {fix}")

    print(f"\n{'='*50}")
    print(f"✅ OK: {len(results['ok'])} sites")
    print(f"❌ Misconfig: {len(results['misconfig'])} sites")
    print(f"⚪ Not running: {len(results['not_running'])} sites")

    if args.mode == "misconfig" and results["misconfig"]:
        print("\nSites with misconfig:")
        for r in results["misconfig"]:
            print(f"  - {r['site']}")


if __name__ == "__main__":
    main()

