import logging
import json
import os
from typing import Dict, Tuple, Optional
from playwright.sync_api import Page
from browsergym.core.task import AbstractBrowserTask

logger = logging.getLogger(__name__)


def _load_tasks_from_jsonl(path: str) -> list[dict]:
    """Load tasks from a JSONL file."""
    tasks = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


class WebVoyagerTask(AbstractBrowserTask):
    """
    WebVoyager benchmark task.

    Each task navigates to a real website and asks the agent to complete an
    open-ended information-seeking or interaction goal. Evaluation is typically
    performed by a VLM judge (external, post-hoc).

    Task data format (JSONL):
        {"web_name": "...", "id": "...", "ques": "...", "web": "https://..."}
    """

    def __init__(
        self,
        seed: int,
        task_id: str,
        data_path: str = os.getenv("CLONE_CODING_ROOT", ".") + "/tools/webvoyager_pae_byqwen7b.jsonl",
        **kwargs,
    ) -> None:
        super().__init__(seed)
        self.task_id = task_id
        self.data_path = data_path

        # Load task data
        all_tasks = _load_tasks_from_jsonl(self.data_path)

        self.task_data = None
        for t in all_tasks:
            if t.get("id") == task_id:
                self.task_data = t
                break

        if not self.task_data:
            # Try by index
            try:
                idx = int(task_id)
                if 0 <= idx < len(all_tasks):
                    self.task_data = all_tasks[idx]
            except ValueError:
                pass

        if not self.task_data:
            raise ValueError(f"Task with id {task_id} not found in {data_path}")

        self.goal = self.task_data["ques"]
        self.start_url = self.task_data["web"]
        self.web_name = self.task_data.get("web_name", "unknown")

    def setup(self, page: Page) -> Tuple[str, dict]:
        logger.info(f"Navigating to start url: {self.start_url}")
        try:
            page.goto(self.start_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Initial navigation to {self.start_url} failed: {e}")
            if "ERR_HTTP2_PROTOCOL_ERROR" in str(e) or "net::ERR_NETWORK_CHANGED" in str(e):
                logger.info(
                    f"Retrying navigation with 'commit' for {self.start_url} "
                    "due to protocol/network error."
                )
                try:
                    page.goto(self.start_url, timeout=30000, wait_until="commit")
                except Exception as e2:
                    logger.error(f"Retry navigation also failed: {e2}")
                    raise e2
            else:
                raise e
        return self.goal, {}

    def validate(self, page: Page, chat_messages: list[dict]) -> Tuple[float, bool, str, dict]:
        """
        WebVoyager evaluation is done by a VLM judge (external, post-hoc).
        Here we just mark the episode as done when the agent provides a response.
        """
        reward = 0.0
        done = False
        msg = ""
        info = {
            "task_id": self.task_id,
            "goal": self.goal,
            "start_url": self.start_url,
            "web_name": self.web_name,
        }

        # Check if the agent has provided a final response
        if chat_messages and chat_messages[-1]["role"] == "assistant":
            done = True
            info["reason"] = (
                "Agent provided a response. External VLM evaluation required for WebVoyager."
            )

        return reward, done, msg, info

    def teardown(self) -> None:
        pass
