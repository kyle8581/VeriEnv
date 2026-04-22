import json
import os
from browsergym.core.registration import register_task
from . import task

# Default path to the WebVoyager PAE-generated tasks (JSONL format)
DATA_PATH = os.getenv(
    "WEBVOYAGER_DATA_PATH",
    os.getenv("CLONE_CODING_ROOT", ".") + "/tools/webvoyager_original.jsonl",
)

# Maximum number of tasks to register (0 = all).
# With 128K+ PAE tasks, registering all at module load is expensive.
# Set WEBVOYAGER_MAX_TASKS env var to limit, or default to 1000.
MAX_TASKS = int(os.getenv("WEBVOYAGER_MAX_TASKS", "1000"))

# Optional: filter by website name (comma-separated)
FILTER_SITES = os.getenv("WEBVOYAGER_FILTER_SITES", "")


def register_webvoyager_tasks():
    if not os.path.exists(DATA_PATH):
        return

    filter_sites = set()
    if FILTER_SITES:
        filter_sites = {s.strip() for s in FILTER_SITES.split(",") if s.strip()}

    count = 0
    with open(DATA_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            task_data = json.loads(line)

            if filter_sites and task_data.get("web_name") not in filter_sites:
                continue

            task_id = task_data.get("id", str(count))
            # Sanitize ID: gymnasium requires [A-Za-z0-9._-] only
            safe_id = task_id.replace(" ", "_")
            register_task(
                id=f"webvoyager.{safe_id}",
                task_class=task.WebVoyagerTask,
                task_kwargs={
                    "task_id": task_id,  # Keep original for data lookup
                    "data_path": DATA_PATH,
                },
            )
            count += 1
            if MAX_TASKS > 0 and count >= MAX_TASKS:
                break


register_webvoyager_tasks()
