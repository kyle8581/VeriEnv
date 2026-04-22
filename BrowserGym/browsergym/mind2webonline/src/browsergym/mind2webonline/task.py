import logging
import json
import os
from typing import Dict, Tuple, Optional
from playwright.sync_api import Page
from browsergym.core.task import AbstractBrowserTask

logger = logging.getLogger(__name__)

class Mind2WebOnlineTask(AbstractBrowserTask):
    def __init__(
        self, 
        seed: int, 
        task_id: str, 
        data_path: str = os.getenv("CLONE_CODING_ROOT", ".") + "/mind2web_data_curation/Online_Mind2Web_accessible.json",
        **kwargs
    ) -> None:
        super().__init__(seed)
        self.task_id = task_id
        self.data_path = data_path
        
        # Load task data
        with open(self.data_path, "r") as f:
            self.all_tasks = json.load(f)
        
        self.task_data = next((t for t in self.all_tasks if t["task_id"] == task_id), None)
        if not self.task_data:
            # Try by index if task_id is a number string
            try:
                idx = int(task_id)
                if 0 <= idx < len(self.all_tasks):
                    self.task_data = self.all_tasks[idx]
            except ValueError:
                pass
        
        if not self.task_data:
            raise ValueError(f"Task with id {task_id} not found in {data_path}")
            
        self.goal = self.task_data["confirmed_task"]
        self.start_url = self.task_data["website"]
        self.level = self.task_data.get("level", "unknown")
        self.reference_length = self.task_data.get("reference_length", 0)

    def setup(self, page: Page) -> Tuple[str, dict]:
        logger.info(f"Navigating to start url: {self.start_url}")
        try:
            # Try normal navigation
            page.goto(self.start_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Initial navigation to {self.start_url} failed: {e}")
            if "ERR_HTTP2_PROTOCOL_ERROR" in str(e) or "net::ERR_NETWORK_CHANGED" in str(e):
                logger.info(f"Retrying navigation with 'commit' for {self.start_url} due to protocol/network error.")
                try:
                    page.goto(self.start_url, timeout=30000, wait_until="commit")
                except Exception as e2:
                    logger.error(f"Retry navigation also failed: {e2}")
                    # If it still fails, we try one last time with no wait_until or just re-raise
                    raise e2
            else:
                raise e
        return self.goal, {}

    def validate(self, page: Page, chat_messages: list[dict]) -> Tuple[float, bool, str, dict]:
        # Evaluation for Online-Mind2Web typically requires an LLM judge (WebJudge).
        # We provide the necessary information for the judge to run.
        
        reward = 0.0
        done = False
        msg = ""
        info = {
            "task_id": self.task_id,
            "goal": self.goal,
            "start_url": self.start_url,
            "level": self.level,
        }

        # Check if the agent has provided a final response
        if chat_messages and chat_messages[-1]["role"] == "assistant":
            # In a real scenario, we would call WebJudge here.
            # For now, we mark it as done and expect external evaluation or 
            # a later implementation of the LLM judge.
            done = True
            info["reason"] = "Agent provided a response. External evaluation required for Online-Mind2Web."
            
        return reward, done, msg, info

    def teardown(self) -> None:
        pass

