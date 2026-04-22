#!/usr/bin/env python3
"""
Start remaining websites locally (source code, not Docker) and manage cloudflared tunnel.

Usage:
  python3 run_local_sites.py --start           # Start all remaining sites + cloudflared
  python3 run_local_sites.py --stop            # Stop everything
  python3 run_local_sites.py --status          # Show running sites
  python3 run_local_sites.py --start --sites drugs,ebay  # Start specific sites only
  python3 run_local_sites.py --dashboard       # Generate dashboard HTML only
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WEBSITES_DIR = Path(__file__).resolve().parent.parent / "websites"
DOCKER_DIR = Path(__file__).resolve().parent
STATE_FILE = DOCKER_DIR / ".local_sites_state.json"
CLOUDFLARED = DOCKER_DIR / "cloudflared"
CLOUDFLARED_CONFIG = Path.home() / ".cloudflared" / "config.yml"
DASHBOARD_FILE = WEBSITES_DIR.parent / "dashboard.html"

REMAINING_SITES = [
    "drugs", "ebay", "epicurious", "espn", "extraspace",
    "finance.google", "finance.yahoo", "flightaware", "foxsports", "gamestop",
    "health.usnews", "healthline", "hiring.amazon", "ign", "ikea",
    "indeed", "instacart", "jetblue", "kbb", "koa",
    "kohls", "landwatch", "last.fm", "linkedin", "map",
    "marriott", "menards", "nba", "new.mta.info", "nps.gov",
    "petfinder", "pinterest", "qatarairways", "recreation.gov", "redfin",
    "rei", "rentalcars", "resy", "rottentomatoes", "seatgeek",
    "shopping", "shopping.google", "sixflags", "soundcloud", "spothero",
    "store.steampowered", "stubhub", "student", "target", "tesla",
    "theweathernetwork", "thumbtack", "ticketcenter", "ultimate-guitar",
    "umich.edu", "underarmour", "uniqlo", "ups", "us.megabus",
    "usnews.education", "weather", "webmd", "yelp",
]

HF_SITES = [
    "accuweather", "airbnb", "allrecipes", "amazon", "apartments",
    "apple", "babycenter", "bestbuy", "boardgamegeek", "budget",
    "ca.gov", "cabelas", "carmax", "carnival", "cars",
    "cookpad", "coursera.org", "craigslist.org", "delta", "discogs",
]

HOSTNAME_MAP = {
    "finance.google": "finance-google",
    "finance.yahoo": "finance-yahoo",
    "health.usnews": "health-usnews",
    "hiring.amazon": "hiring-amazon",
    "last.fm": "last-fm",
    "new.mta.info": "new-mta-info",
    "nps.gov": "nps-gov",
    "recreation.gov": "recreation-gov",
    "shopping.google": "shopping-google",
    "store.steampowered": "store-steampowered",
    "ultimate-guitar": "ultimate-guitar",
    "umich.edu": "umich-edu",
    "us.megabus": "us-megabus",
    "usnews.education": "usnews-education",
    "coursera.org": "coursera-org",
    "craigslist.org": "craigslist-org",
    "ca.gov": "ca-gov",
}


def get_hostname(site: str) -> str:
    base = HOSTNAME_MAP.get(site, site.replace(".", "-").replace("_", "-"))
    return f"{base}.verienv.com"


def load_ports(site: str) -> dict:
    pf = WEBSITES_DIR / site / "ports.json"
    if pf.exists():
        with open(pf) as f:
            return json.load(f).get("ports", {})
    return {}


def get_frontend_port(site: str) -> int | None:
    ports = load_ports(site)
    return ports.get("FRONTEND_PORT") or ports.get("WEB_PORT") or ports.get("PORT")


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"sites": {}, "cloudflared_pid": None}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def start_site(site: str) -> dict | None:
    site_dir = WEBSITES_DIR / site
    start_script = site_dir / "start_servers.sh"

    if not start_script.exists():
        print(f"  SKIP {site}: no start_servers.sh")
        return None

    fe_port = get_frontend_port(site)
    if not fe_port:
        print(f"  SKIP {site}: no frontend port in ports.json")
        return None

    log_dir = DOCKER_DIR / "logs" / site
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "local_run.log"

    with open(log_file, "w") as lf:
        proc = subprocess.Popen(
            ["bash", str(start_script)],
            cwd=str(site_dir),
            stdout=lf,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )

    return {
        "pid": proc.pid,
        "pgid": os.getpgid(proc.pid),
        "port": fe_port,
        "hostname": get_hostname(site),
        "log": str(log_file),
    }


def stop_site(site: str, info: dict):
    pgid = info.get("pgid")
    pid = info.get("pid")

    if pgid:
        try:
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(0.3)
            os.killpg(pgid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass

    if pid and is_pid_alive(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass

    port = info.get("port")
    if port:
        subprocess.run(
            f"fuser -k {port}/tcp 2>/dev/null || true",
            shell=True, capture_output=True,
        )
        be_ports = load_ports(site)
        be_port = be_ports.get("BACKEND_PORT") or be_ports.get("API_PORT")
        if be_port and be_port != port:
            subprocess.run(
                f"fuser -k {be_port}/tcp 2>/dev/null || true",
                shell=True, capture_output=True,
            )


def check_site_health(port: int, timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.urlopen(f"http://localhost:{port}/", timeout=timeout)
        return req.getcode() == 200
    except Exception:
        return False


def start_cloudflared() -> int | None:
    if not CLOUDFLARED.exists():
        print("ERROR: cloudflared binary not found")
        return None

    log_file = DOCKER_DIR / "logs" / "cloudflared.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "w") as lf:
        proc = subprocess.Popen(
            [str(CLOUDFLARED), "tunnel", "--config", str(CLOUDFLARED_CONFIG), "run"],
            stdout=lf,
            stderr=subprocess.STDOUT,
        )

    print(f"  cloudflared started (PID {proc.pid})")
    return proc.pid


def stop_cloudflared(pid: int):
    if pid and is_pid_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            if is_pid_alive(pid):
                os.kill(pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
    subprocess.run("pkill -f 'cloudflared tunnel' 2>/dev/null || true",
                    shell=True, capture_output=True)


def generate_dashboard():
    sites_data = []

    for site in sorted(REMAINING_SITES):
        hostname = get_hostname(site)
        sites_data.append({
            "name": site,
            "url": f"https://{hostname}",
            "type": "cloudflared",
        })

    for site in sorted(HF_SITES):
        hf_hostname = HOSTNAME_MAP.get(site, site.replace(".", "-").replace("_", "-"))
        sites_data.append({
            "name": site,
            "url": f"https://hyungjoochae-{hf_hostname}-clone.hf.space",
            "type": "huggingface",
        })

    all_sites = sorted(sites_data, key=lambda x: x["name"])

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Website Clone Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
  .header { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 2rem; text-align: center; border-bottom: 1px solid #334155; }
  .header h1 { font-size: 2rem; font-weight: 700; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .header p { color: #94a3b8; margin-top: 0.5rem; }
  .controls { display: flex; justify-content: center; gap: 1rem; padding: 1.5rem; flex-wrap: wrap; }
  .search { padding: 0.75rem 1.25rem; border-radius: 0.5rem; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; width: 300px; font-size: 1rem; outline: none; transition: border 0.2s; }
  .search:focus { border-color: #60a5fa; }
  .filter-btn { padding: 0.5rem 1rem; border-radius: 0.5rem; border: 1px solid #334155; background: #1e293b; color: #94a3b8; cursor: pointer; transition: all 0.2s; }
  .filter-btn.active, .filter-btn:hover { background: #3b82f6; color: white; border-color: #3b82f6; }
  .stats { text-align: center; color: #64748b; padding: 0 1.5rem 1rem; font-size: 0.875rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; padding: 1.5rem; max-width: 1600px; margin: 0 auto; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.25rem; transition: all 0.2s; cursor: pointer; text-decoration: none; color: inherit; display: flex; flex-direction: column; gap: 0.5rem; }
  .card:hover { border-color: #60a5fa; transform: translateY(-2px); box-shadow: 0 4px 20px rgba(96,165,250,0.1); }
  .card-name { font-size: 1.1rem; font-weight: 600; color: #f1f5f9; }
  .card-url { font-size: 0.8rem; color: #64748b; word-break: break-all; }
  .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
  .badge.cf { background: #f97316; color: white; }
  .badge.hf { background: #eab308; color: #1e293b; }
  .hidden { display: none; }
</style>
</head>
<body>
<div class="header">
  <h1>Website Clone Dashboard</h1>
  <p>TOTAL_COUNT functional website clones</p>
</div>
<div class="controls">
  <input type="text" class="search" placeholder="Search sites..." oninput="filterSites()">
  <button class="filter-btn active" onclick="setFilter('all')">All</button>
  <button class="filter-btn" onclick="setFilter('cloudflared')">Cloudflared</button>
  <button class="filter-btn" onclick="setFilter('huggingface')">HuggingFace</button>
</div>
<div class="stats" id="stats"></div>
<div class="grid" id="grid"></div>
<script>
const sites = SITES_JSON;
let currentFilter = 'all';

function renderSites(filtered) {
  const grid = document.getElementById('grid');
  grid.innerHTML = filtered.map(s => `
    <a class="card" href="${s.url}" target="_blank" data-type="${s.type}">
      <div style="display:flex;align-items:center;gap:0.5rem;">
        <span class="card-name">${s.name}</span>
        <span class="badge ${s.type === 'cloudflared' ? 'cf' : 'hf'}">${s.type === 'cloudflared' ? 'CF' : 'HF'}</span>
      </div>
      <div class="card-url">${s.url}</div>
    </a>
  `).join('');
  document.getElementById('stats').textContent = `Showing ${filtered.length} of ${sites.length} sites`;
}

function filterSites() {
  const q = document.querySelector('.search').value.toLowerCase();
  const filtered = sites.filter(s =>
    (currentFilter === 'all' || s.type === currentFilter) &&
    s.name.toLowerCase().includes(q)
  );
  renderSites(filtered);
}

function setFilter(f) {
  currentFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  filterSites();
}

renderSites(sites);
</script>
</body>
</html>"""
    html = html.replace("TOTAL_COUNT", str(len(all_sites)))
    html = html.replace("SITES_JSON", json.dumps(all_sites))

    DASHBOARD_FILE.write_text(html)
    print(f"Dashboard written to {DASHBOARD_FILE}")
    return DASHBOARD_FILE


def cmd_start(sites: list[str], batch_size: int = 10):
    state = load_state()

    print(f"Starting {len(sites)} sites locally...\n")

    for batch_start in range(0, len(sites), batch_size):
        batch = sites[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(sites) + batch_size - 1) // batch_size
        print(f"--- Batch {batch_num}/{total_batches} ({len(batch)} sites) ---")

        for site in batch:
            if site in state["sites"] and is_pid_alive(state["sites"][site].get("pid", 0)):
                print(f"  {site}: already running (PID {state['sites'][site]['pid']})")
                continue

            info = start_site(site)
            if info:
                state["sites"][site] = info
                print(f"  {site}: started (PID {info['pid']}, port {info['port']})")
            save_state(state)

        if batch_start + batch_size < len(sites):
            print(f"  Waiting 5s for batch to initialize...")
            time.sleep(5)

    # Start cloudflared
    print(f"\nStarting cloudflared tunnel...")
    if state.get("cloudflared_pid") and is_pid_alive(state["cloudflared_pid"]):
        print("  cloudflared already running, restarting...")
        stop_cloudflared(state["cloudflared_pid"])
        time.sleep(1)

    cf_pid = start_cloudflared()
    state["cloudflared_pid"] = cf_pid
    save_state(state)

    # Wait and check health
    print(f"\nWaiting 30s for sites to become ready...")
    time.sleep(30)

    ready = 0
    not_ready = []
    for site in sites:
        info = state["sites"].get(site, {})
        port = info.get("port")
        if port and check_site_health(port):
            ready += 1
        else:
            not_ready.append(site)

    print(f"\n{'='*60}")
    print(f"Ready: {ready}/{len(sites)} sites")
    if not_ready:
        print(f"Not ready yet: {', '.join(not_ready[:20])}")
        if len(not_ready) > 20:
            print(f"  ... and {len(not_ready)-20} more")
        print("(Some sites need more startup time, check --status later)")

    # Generate dashboard
    generate_dashboard()
    print(f"\nAll cloudflared URLs use https://<site>.verienv.com")


def cmd_stop():
    state = load_state()
    print("Stopping all sites...")

    for site, info in state.get("sites", {}).items():
        stop_site(site, info)
        print(f"  Stopped {site}")

    if state.get("cloudflared_pid"):
        stop_cloudflared(state["cloudflared_pid"])
        print("  Stopped cloudflared")

    state = {"sites": {}, "cloudflared_pid": None}
    save_state(state)
    print("All stopped.")


def cmd_status():
    state = load_state()
    sites = state.get("sites", {})

    if not sites:
        print("No sites are running.")
        return

    running = 0
    healthy = 0
    dead = 0

    for site in sorted(sites):
        info = sites[site]
        pid = info.get("pid", 0)
        port = info.get("port")
        alive = is_pid_alive(pid)
        health = check_site_health(port) if port and alive else False

        if alive and health:
            status = "\033[92mHEALTHY\033[0m"
            running += 1
            healthy += 1
        elif alive:
            status = "\033[93mRUNNING\033[0m"
            running += 1
        else:
            status = "\033[91mDEAD\033[0m"
            dead += 1

        hostname = info.get("hostname", "")
        print(f"  {site:30s} PID {pid:>7d}  :{port}  {status:20s}  https://{hostname}")

    cf_pid = state.get("cloudflared_pid")
    cf_status = "RUNNING" if cf_pid and is_pid_alive(cf_pid) else "STOPPED"
    print(f"\n  cloudflared: {cf_status} (PID {cf_pid})")
    print(f"\n  Total: {running} running, {healthy} healthy, {dead} dead")


def main():
    ap = argparse.ArgumentParser(description="Run local sites with cloudflared")
    ap.add_argument("--start", action="store_true", help="Start sites + cloudflared")
    ap.add_argument("--stop", action="store_true", help="Stop everything")
    ap.add_argument("--status", action="store_true", help="Show status")
    ap.add_argument("--dashboard", action="store_true", help="Generate dashboard only")
    ap.add_argument("--sites", help="Comma-separated site list (default: all remaining)")
    ap.add_argument("--batch-size", type=int, default=10, help="Sites per batch")
    args = ap.parse_args()

    if args.dashboard:
        generate_dashboard()
        return

    if args.stop:
        cmd_stop()
        return

    if args.status:
        cmd_status()
        return

    if args.start:
        sites = args.sites.split(",") if args.sites else REMAINING_SITES
        cmd_start(sites, batch_size=args.batch_size)
        return

    ap.print_help()


if __name__ == "__main__":
    main()
