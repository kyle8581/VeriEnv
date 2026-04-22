import json
import os
from browsergym.core.registration import register_task
from . import task

DATA_PATH = os.getenv("CLONE_CODING_ROOT", ".") + "/mind2web_data_curation/Online_Mind2Web_accessible.json"

def register_mind2webonline_tasks():
    if not os.path.exists(DATA_PATH):
        return

    with open(DATA_PATH, "r") as f:
        all_tasks = json.load(f)

    for i, task_data in enumerate(all_tasks):
        task_id = task_data["task_id"]
        # Register by task_id
        register_task(
            id=f"mind2webonline.{task_id}",
            task_class=task.Mind2WebOnlineTask,
            task_kwargs={
                "task_id": task_id,
                "data_path": DATA_PATH,
            },
        )
        # Also register by index for easier access
        register_task(
            id=f"mind2webonline.{i}",
            task_class=task.Mind2WebOnlineTask,
            task_kwargs={
                "task_id": task_id,
                "data_path": DATA_PATH,
            },
        )

register_mind2webonline_tasks()

