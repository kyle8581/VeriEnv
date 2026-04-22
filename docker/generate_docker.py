#!/usr/bin/env python3
"""
Auto-generate Dockerfiles and docker-compose.yml for all website projects.

Strategy: Each site runs its own start_servers.sh inside a single container.
  - start_servers.sh already handles dependency installation, DB seeding,
    and starting frontend + backend servers.
  - The Dockerfile pre-installs deps at build time for faster startup.
  - Ports are mapped 1:1 from ports.json (host:container are the same).
  - Parses start_servers.sh to detect venv paths, port patterns, etc.
"""
import json
import os
import re
import argparse
from pathlib import Path

WEBSITES_DIR = Path(__file__).resolve().parent.parent / "websites"
OUTPUT_DIR = Path(__file__).resolve().parent / "generated"
SKIP_DIRS = {"data", "screenshot", "screenshots", "__pycache__"}


def load_ports(site_path: Path) -> dict:
    pf = site_path / "ports.json"
    if pf.exists():
        with open(pf) as f:
            return json.load(f).get("ports", {})
    return {}


def fe_port(ports: dict) -> int:
    return ports.get("FRONTEND_PORT") or ports.get("WEB_PORT") or ports.get("UI_PORT") or ports.get("PORT") or 3000


def be_port(ports: dict) -> int:
    return ports.get("BACKEND_PORT") or ports.get("API_PORT") or ports.get("PORT") or 8000


def detect_runtime(site_path: Path) -> tuple:
    """Detect whether site needs Node.js and/or Python."""
    needs_node = False
    needs_python = False
    for sub in ["frontend", "apps/web", "app", "web", "."]:
        if (site_path / sub / "package.json").exists():
            needs_node = True
            break
    for sub in ["backend", "apps/api", "server", "."]:
        if (site_path / sub / "requirements.txt").exists():
            needs_python = True
            break
    return needs_node, needs_python


def _normalize_shell_path(raw: str) -> str:
    """Resolve shell variables in a path to a relative path inside /app."""
    normalized = raw
    # Strip common root-dir variables
    for var in [
        "$ROOT_DIR/", "${ROOT_DIR}/", "$REPO_ROOT/", "${REPO_ROOT}/",
        "$ROOT/", "${ROOT}/", "$SCRIPT_DIR/", "${SCRIPT_DIR}/",
        "$BASE_DIR/", "${BASE_DIR}/", "$DIR/", "${DIR}/",
    ]:
        normalized = normalized.replace(var, "")
    for var in [
        "$BACKEND_DIR/", "${BACKEND_DIR}/", "$BE_DIR/", "${BE_DIR}/",
    ]:
        normalized = normalized.replace(var, "backend/")
    for var in [
        "$API_DIR/", "${API_DIR}/",
    ]:
        normalized = normalized.replace(var, "apps/api/")
    for var in [
        "$FRONTEND_DIR/", "${FRONTEND_DIR}/", "$FE_DIR/", "${FE_DIR}/",
    ]:
        normalized = normalized.replace(var, "frontend/")
    # Strip quotes
    normalized = normalized.strip("\"'")
    # If still starts with $ (unresolvable variable), guess directory from context
    if normalized.startswith("$"):
        lower = raw.lower()
        if "venv" in lower:
            # Variable like $VENV — guess the full venv path
            if "backend" in lower or "be_dir" in lower:
                return "backend/.venv"
            elif "api" in lower:
                return "apps/api/.venv"
            else:
                return ".venv"
        else:
            # Variable like $BACKEND_DIR — guess the directory
            if "backend" in lower or "be_dir" in lower:
                return "backend"
            elif "api" in lower:
                return "apps/api"
            elif "frontend" in lower or "fe_dir" in lower:
                return "frontend"
            else:
                return ""
    return normalized


def _resolve_cd_context(content: str, match_pos: int) -> str:
    """Find the most recent 'cd' target before match_pos to resolve relative paths.

    Handles patterns like:
        cd "$ROOT_DIR/backend" && python3 -m venv .venv
        (cd "$ROOT/apps/api" ; python3 -m venv .venv)
    """
    # Look backwards from match_pos for cd commands
    preceding = content[:match_pos]
    # Find last cd/pushd command — may be on the same line or in a subshell
    cd_matches = list(re.finditer(
        r'(?:cd|pushd)\s+["\']?([^\s"\';&|)>]+)["\']?', preceding
    ))
    if not cd_matches:
        return ""
    last_cd = cd_matches[-1]
    cd_target = _normalize_shell_path(last_cd.group(1))
    # Only use cd context if it's close (same logical block — within ~200 chars)
    if match_pos - last_cd.end() > 200:
        return ""
    # Ignore cd to root / current dir
    if cd_target in ("", ".", "/app"):
        return ""
    return cd_target


def parse_start_servers(site_path: Path) -> dict:
    """Parse start_servers.sh for venv paths, port usage, build steps, etc."""
    ss = site_path / "start_servers.sh"
    if not ss.exists():
        return {}
    content = ss.read_text()
    info = {
        "has_docker_compose": "docker compose" in content or "docker-compose" in content,
        "uses_venv": ".venv" in content or "venv" in content,
        "venv_paths": [],
        "has_frontend_port": False,
        "has_backend_port": False,
        "runtime_pip": "pip install" in content,
        "runtime_npm": "npm install" in content or "npm ci" in content,
        "has_npm_build": False,
        "npm_build_envs": {},
    }

    venv_paths_seen = set()

    def _add_venv(path: str):
        """Deduplicate and store a venv path."""
        path = path.rstrip("/")
        if path and path not in venv_paths_seen:
            venv_paths_seen.add(path)
            info["venv_paths"].append(path)

    # --- Pattern 1: python3 -m venv PATH (with cd-context resolution) ---
    for m in re.finditer(r'python3 -m venv\s+["\']?([^\s"\';&)]+)', content):
        raw = m.group(1)
        normalized = _normalize_shell_path(raw)
        # If the venv target is just ".venv" or "venv", resolve via cd context
        if normalized in (".venv", "venv"):
            cd_ctx = _resolve_cd_context(content, m.start())
            if cd_ctx:
                normalized = f"{cd_ctx}/.venv"
        _add_venv(normalized)

    # --- Pattern 2: source/activate references ---
    #   source backend/.venv/bin/activate
    #   . .venv/bin/activate
    #   . "$ROOT_DIR/backend/.venv/bin/activate"
    for m in re.finditer(
        r'(?:source|\.) +["\']?([^\s"\';&)]+/bin/activate)', content
    ):
        raw = m.group(1)
        # Strip /bin/activate to get venv root
        venv_root = re.sub(r'/bin/activate$', '', _normalize_shell_path(raw))
        if venv_root in (".venv", "venv"):
            cd_ctx = _resolve_cd_context(content, m.start())
            if cd_ctx:
                venv_root = f"{cd_ctx}/.venv"
        _add_venv(venv_root)

    # --- Pattern 3: direct venv binary references ---
    #   backend/.venv/bin/uvicorn
    #   .venv/bin/python3 -m uvicorn
    #   apps/api/.venv/bin/pip install
    for m in re.finditer(
        r'([^\s"\';&|()]+/\.venv)/bin/(?:python3?|pip|uvicorn|gunicorn)', content
    ):
        raw = m.group(1)
        venv_root = _normalize_shell_path(raw)
        # Skip ../X paths — they are relative from a cd subdir context
        # and the same venv should have been found via Pattern 1 or 2
        if venv_root.startswith("../"):
            continue
        _add_venv(venv_root)

    # --- Detect npm run build / next build ---
    if re.search(r'npm run build|next build|npx next build', content):
        info["has_npm_build"] = True
        # Capture NEXT_PUBLIC_* env vars used inline with the build command
        for m in re.finditer(
            r'(NEXT_PUBLIC_\w+)=["\']?http://[^:]+:(\$\{?\w+\}?|\d+)', content
        ):
            info["npm_build_envs"][m.group(1)] = m.group(2)

    # --- Detect port usage ---
    if any(x in content for x in ["FRONTEND_PORT", "WEB_PORT", "UI_PORT"]):
        info["has_frontend_port"] = True
    if any(x in content for x in ["BACKEND_PORT", "API_PORT"]):
        info["has_backend_port"] = True
    if re.search(r'(uvicorn|gunicorn|python)', content):
        info["has_backend_port"] = True

    return info


def detect_exposed_ports(site_path: Path, ports: dict) -> list:
    """Return unique *primary* port values from ports.json.

    Only expose the normalized FRONTEND_PORT and BACKEND_PORT to avoid
    conflicts from legacy alias ports (PORT, WEB_PORT, API_PORT, etc.).
    """
    normalized = _normalize_port_env(ports)
    exposed = set()
    for value in normalized.values():
        if isinstance(value, int) and value > 0:
            exposed.add(value)

    # Fallback when ports.json is empty or has no int values
    if not exposed:
        info = parse_start_servers(site_path)
        has_frontend = (
            info.get("has_frontend_port")
            or (site_path / "frontend").is_dir()
            or (site_path / "apps" / "web").is_dir()
        )
        has_backend = (
            info.get("has_backend_port")
            or (site_path / "backend").is_dir()
            or (site_path / "apps" / "api").is_dir()
        )
        if has_frontend:
            exposed.add(fe_port(ports))
        if has_backend:
            exposed.add(be_port(ports))
        if not exposed:
            exposed.add(fe_port(ports))

    return sorted(exposed)


def find_requirements_files(site_path: Path) -> list:
    results = []
    for sub in ["backend", "apps/api", "server", "."]:
        p = site_path / sub / "requirements.txt"
        if p.exists():
            results.append(str(Path(sub) / "requirements.txt"))
    return results


def find_package_dirs(site_path: Path) -> list:
    results = []
    for sub in ["frontend", "apps/web", "app", "web", "."]:
        p = site_path / sub / "package.json"
        if p.exists():
            results.append(sub)
    return results


def _normalize_port_env(ports: dict) -> dict:
    """Normalize port env vars so all frontend/backend aliases point to the
    canonical FRONTEND_PORT / BACKEND_PORT values.

    ports.json often has legacy keys (PORT, WEB_PORT, API_PORT) with old values
    alongside the canonical keys (FRONTEND_PORT, BACKEND_PORT). If we export
    all of them, start_servers.sh may pick up the wrong (legacy) value.

    This remaps everything:
      PORT, WEB_PORT, UI_PORT  ->  FRONTEND_PORT value
      API_PORT                 ->  BACKEND_PORT value
    """
    fe = ports.get("FRONTEND_PORT") or ports.get("WEB_PORT") or ports.get("UI_PORT") or ports.get("PORT")
    be = ports.get("BACKEND_PORT") or ports.get("API_PORT")

    result = {}
    fe_aliases = {"PORT", "WEB_PORT", "UI_PORT", "FRONTEND_PORT"}
    be_aliases = {"API_PORT", "BACKEND_PORT"}

    for k, v in ports.items():
        if not isinstance(v, int):
            continue
        if k in fe_aliases and fe:
            result[k] = fe
        elif k in be_aliases and be:
            result[k] = be
        else:
            result[k] = v

    return result


def _build_env_string(ports: dict) -> str:
    """Build an inline env-var prefix for shell commands.

    E.g. 'FRONTEND_PORT=12149 BACKEND_PORT=12150 ...'
    Used to pass port vars into npm run build for NEXT_PUBLIC_* interpolation.
    """
    normalized = _normalize_port_env(ports)
    parts = []
    for k, v in sorted(normalized.items()):
        parts.append(f"{k}={v}")
    return " ".join(parts)


def gen_dockerfile(site_path: Path, needs_node: bool, needs_python: bool,
                   exposed_ports: list, ports: dict = None) -> str:
    """Generate a multi-stage Dockerfile.

    Stage 1 (builder): has gcc, libffi-dev, gnupg — compiles C extensions,
        installs Python venvs, npm deps, and pre-builds the frontend.
    Stage 2 (runtime): slim image without build tools — only runtime deps.
        COPY from builder: /app (source+venvs+node_modules+.next) and
        system Python site-packages.
    """
    lines = []
    if ports is None:
        ports = {}
    expose_str = " ".join(str(p) for p in exposed_ports)
    req_files = find_requirements_files(site_path)
    pkg_dirs = find_package_dirs(site_path)
    ss_info = parse_start_servers(site_path)

    # Determine venv paths from start_servers.sh
    venv_paths = ss_info.get("venv_paths", [])

    # ENV line shared by both stages — normalize so all aliases use canonical ports
    normalized_ports = _normalize_port_env(ports)
    env_parts = [f"{k}={v}" for k, v in sorted(normalized_ports.items())]
    env_line = f"ENV {' '.join(env_parts)}" if env_parts else ""

    # ================================================================
    # STAGE 1: builder  (has gcc / build tools)
    # ================================================================
    if needs_node and needs_python:
        lines.append("FROM python:3.11-slim AS builder")
        lines.append("")
        lines.append("# Install Node.js 22 + build tools")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl gcc libffi-dev gnupg psmisc procps && \\")
        lines.append("    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \\")
        lines.append("    apt-get install -y nodejs && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")
    elif needs_node:
        lines.append("FROM node:22-slim AS builder")
        lines.append("")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl psmisc procps python3 && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")
    elif needs_python:
        lines.append("FROM python:3.11-slim AS builder")
        lines.append("")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl gcc libffi-dev psmisc procps && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")
    else:
        lines.append("FROM python:3.11-slim AS builder")
        lines.append("")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl gcc libffi-dev gnupg psmisc procps && \\")
        lines.append("    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \\")
        lines.append("    apt-get install -y nodejs && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")

    lines.append("")
    lines.append("WORKDIR /app")

    if env_line:
        lines.append("")
        lines.append("# Port environment variables from ports.json")
        lines.append(env_line)

    lines.append("")
    lines.append("# Copy everything")
    lines.append("COPY . .")

    # --- Pre-install Python deps (venvs only — system copy happens in runtime stage) ---
    if needs_python and req_files:
        lines.append("")
        lines.append("# Pre-install Python deps into venvs")

        # Create venvs at all paths found in start_servers.sh
        created_venvs = set()
        if not venv_paths:
            # Fallback: common venv locations based on directory structure
            backend_dir = str(Path(req_files[0]).parent)
            if backend_dir == ".":
                venv_paths = [".venv"]
            else:
                venv_paths = [f"{backend_dir}/.venv", ".venv"]

        for vp in venv_paths:
            if vp in created_venvs:
                continue
            created_venvs.add(vp)
            lines.append(f"RUN python3 -m venv {vp} && \\")
            lines.append(f"    . {vp}/bin/activate && \\")
            lines.append("    pip install --upgrade pip && \\")
            lines.append(f"    pip install --no-cache-dir -r {req_files[0]}")

        # Also install to system Python (some start_servers.sh scripts use system python directly)
        lines.append(f"RUN pip install --no-cache-dir -r {req_files[0]}")

    # --- Pre-install Node deps ---
    if needs_node and pkg_dirs:
        lines.append("")
        lines.append("# Pre-install Node deps")
        for pkg_dir in pkg_dirs:
            if pkg_dir == ".":
                lines.append("RUN npm ci 2>/dev/null || npm install")
            else:
                lines.append(f"RUN cd {pkg_dir} && (npm ci 2>/dev/null || npm install)")

    # --- Pre-build frontend if start_servers.sh does npm run build ---
    if ss_info.get("has_npm_build") and needs_node and pkg_dirs:
        lines.append("")
        lines.append("# Pre-build frontend (saves 60-180s at container startup)")
        env_prefix = _build_env_string(ports)
        for pkg_dir in pkg_dirs:
            cd_prefix = f"cd {pkg_dir} && " if pkg_dir != "." else ""
            if env_prefix:
                lines.append(f"RUN {cd_prefix}{env_prefix} npm run build || true")
            else:
                lines.append(f"RUN {cd_prefix}npm run build || true")

        # Prune devDependencies after build (next start only needs production deps + .next/)
        lines.append("")
        lines.append("# Strip devDependencies (no longer needed after build)")
        for pkg_dir in pkg_dirs:
            cd_prefix = f"cd {pkg_dir} && " if pkg_dir != "." else ""
            lines.append(f"RUN {cd_prefix}npm prune --omit=dev 2>/dev/null || true")

    # --- Clean caches so COPY --from=builder is smaller ---
    lines.append("")
    lines.append("# Clean build caches")
    lines.append("RUN rm -rf ~/.npm /tmp/* ~/.cache /root/.cache")
    lines.append("RUN chmod +x start_servers.sh")

    # ================================================================
    # STAGE 2: runtime  (no gcc / build tools — slim)
    # ================================================================
    lines.append("")
    lines.append("# ---- runtime stage (no build tools) ----")
    if needs_node and needs_python:
        lines.append("FROM python:3.11-slim")
        lines.append("")
        lines.append("# Runtime deps only — no gcc, no libffi-dev, no gnupg")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl psmisc procps gnupg && \\")
        lines.append("    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \\")
        lines.append("    apt-get install -y nodejs && \\")
        lines.append("    apt-get purge -y gnupg && apt-get autoremove -y && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")
    elif needs_node:
        lines.append("FROM node:22-slim")
        lines.append("")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl psmisc procps python3 && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")
    elif needs_python:
        lines.append("FROM python:3.11-slim")
        lines.append("")
        lines.append("# Runtime deps only — no gcc, no libffi-dev")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl psmisc procps && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")
    else:
        lines.append("FROM python:3.11-slim")
        lines.append("")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends \\")
        lines.append("    curl psmisc procps gnupg && \\")
        lines.append("    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \\")
        lines.append("    apt-get install -y nodejs && \\")
        lines.append("    apt-get purge -y gnupg && apt-get autoremove -y && \\")
        lines.append("    rm -rf /var/lib/apt/lists/*")

    lines.append("")
    lines.append("WORKDIR /app")

    if env_line:
        lines.append("")
        lines.append(env_line)

    # Copy application from builder (source + venvs + node_modules + .next)
    lines.append("")
    lines.append("# Copy application from builder")
    lines.append("COPY --from=builder /app /app")

    # Copy system Python packages from builder for scripts that use system python
    if needs_python:
        lines.append("")
        lines.append("# Copy system Python packages (for scripts using system python directly)")
        lines.append("COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages")
        lines.append("COPY --from=builder /usr/local/bin /usr/local/bin")

    lines.append("")
    lines.append(f"EXPOSE {expose_str}")
    lines.append("")
    lines.append("# start_servers.sh backgrounds servers then exits;")
    lines.append("# sleep infinity keeps the container alive.")
    lines.append('CMD ["bash", "-c", "./start_servers.sh && sleep infinity"]')
    lines.append("")
    return "\n".join(lines)


def gen_dockerignore() -> str:
    return """\
node_modules
frontend/node_modules
apps/web/node_modules
app/node_modules
web/node_modules
.next
frontend/.next
apps/web/.next
app/.next
web/.next
.venv
backend/.venv
apps/api/.venv
__pycache__
*.pyc
.logs
.pids
.runtime
*.log
.git
screenshot
*.png
*.md
!README.md
"""


def gen_site_compose(name: str, exposed_ports: list, ports: dict = None) -> str:
    """Generate a per-site docker-compose.yml with 1:1 port mapping and env vars."""
    port_lines = "\n".join(f'      - "{p}:{p}"' for p in exposed_ports)
    env_lines = ""
    if ports:
        normalized = _normalize_port_env(ports)
        env_entries = [f'      - {k}={v}' for k, v in sorted(normalized.items())]
        if env_entries:
            env_lines = "    environment:\n" + "\n".join(env_entries) + "\n"
    return (
        f"services:\n"
        f"  {name}:\n"
        f"    build:\n"
        f"      context: ../../websites/{name}\n"
        f"      dockerfile: Dockerfile\n"
        f"    ports:\n"
        f"{port_lines}\n"
        f"{env_lines}"
        f"    restart: unless-stopped\n"
    )


def gen_site(name: str, dry_run: bool = False) -> dict:
    site_path = WEBSITES_DIR / name
    if not site_path.is_dir():
        return {}
    ss = site_path / "start_servers.sh"
    if not ss.exists():
        return {}
    ports = load_ports(site_path)
    if not ports:
        return {}

    needs_node, needs_python = detect_runtime(site_path)
    exposed_ports = detect_exposed_ports(site_path, ports)
    ss_info = parse_start_servers(site_path)

    if not needs_node and not needs_python:
        print(f"  {name}: SKIPPED (no deps found)")
        return {}

    venv_info = ",".join(ss_info.get("venv_paths", [])) or "none"
    flags = []
    if ss_info.get("has_docker_compose"):
        flags.append("docker-in-docker")
    print(f"  {name}: node={needs_node} py={needs_python} ports={exposed_ports} venv=[{venv_info}] {' '.join(flags)}")

    result = {
        "site": name,
        "needs_node": needs_node,
        "needs_python": needs_python,
        "ports": ports,
        "exposed_ports": exposed_ports,
    }
    if dry_run:
        return result

    dockerfile_content = gen_dockerfile(site_path, needs_node, needs_python, exposed_ports, ports)
    (site_path / "Dockerfile").write_text(dockerfile_content)
    (site_path / ".dockerignore").write_text(gen_dockerignore())

    gen_dir = OUTPUT_DIR / name
    gen_dir.mkdir(parents=True, exist_ok=True)
    (gen_dir / "Dockerfile").write_text(dockerfile_content)
    (gen_dir / "docker-compose.yml").write_text(
        gen_site_compose(name, exposed_ports, ports)
    )
    return result


def master_compose(results: list) -> str:
    lines = [
        "# Auto-generated master docker-compose.yml",
        "# Each site runs start_servers.sh in a single container.",
        "# Use profiles to selectively start sites:",
        "#   docker compose --profile airbnb --profile booking up -d",
        "#   docker compose --profile all up -d",
        "",
        "services:",
    ]
    for r in sorted(results, key=lambda x: x.get("site", "")):
        site = r.get("site", "")
        exposed = r.get("exposed_ports", [])
        site_ports = r.get("ports", {})
        if not site or not exposed:
            continue
        port_mappings = [f'      - "{p}:{p}"' for p in exposed]
        normalized_sp = _normalize_port_env(site_ports)
        env_entries = [f'      - {k}={v}' for k, v in sorted(normalized_sp.items())]
        lines.append("")
        lines.append(f"  {site}:")
        lines.append(f"    build:")
        lines.append(f"      context: ../websites/{site}")
        lines.append(f"      dockerfile: Dockerfile")
        lines.append(f"    ports:")
        for pm in port_mappings:
            lines.append(pm)
        if env_entries:
            lines.append(f"    environment:")
            for ee in env_entries:
                lines.append(ee)
        lines.append(f"    profiles:")
        lines.append(f'      - "{site}"')
        lines.append(f'      - "all"')
        lines.append(f"    restart: unless-stopped")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Generate Docker configs for websites")
    ap.add_argument("--site", help="Generate for a single site only")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.site:
        sites = [args.site]
    else:
        sites = sorted([
            d.name for d in WEBSITES_DIR.iterdir()
            if d.is_dir() and d.name not in SKIP_DIRS
        ])

    print(f"Generating Docker configs for {len(sites)} sites...\n")
    results = []
    skipped = 0
    for s in sites:
        r = gen_site(s, args.dry_run)
        if r:
            results.append(r)
        else:
            skipped += 1

    if not args.dry_run and results:
        compose_path = OUTPUT_DIR.parent / "docker-compose.yml"
        compose_path.write_text(master_compose(results))
        catalog = {"total_sites": len(results), "skipped": skipped, "sites": results}
        with open(OUTPUT_DIR / "catalog.json", "w") as f:
            json.dump(catalog, f, indent=2)
        print(f"\nMaster docker-compose.yml written to {compose_path}")
        print(f"Catalog written to {OUTPUT_DIR / 'catalog.json'}")

    print(f"\nSummary: {len(results)} sites configured, {skipped} skipped")


if __name__ == "__main__":
    main()
