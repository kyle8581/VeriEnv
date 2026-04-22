import json
import os
from browsergym.core.registration import register_task
from . import task

DATA_PATH = os.getenv("CLONE_CODING_ROOT", ".") + "/data/pae_tasks.json"

def register_pae_tasks():
    if not os.path.exists(DATA_PATH):
        return

    with open(DATA_PATH, "r") as f:
        all_tasks = json.load(f)

    for i, task_data in enumerate(all_tasks):
        task_id = task_data["task_id"]
        # Register by task_id
        register_task(
            id=f"pae.{task_id}",
            task_class=task.PAETask,
            task_kwargs={
                "task_id": task_id,
                "data_path": DATA_PATH,
            },
        )
        # Also register by index for easier access
        register_task(
            id=f"pae.{i}",
            task_class=task.PAETask,
            task_kwargs={
                "task_id": task_id,
                "data_path": DATA_PATH,
            },
        )

register_pae_tasks()
