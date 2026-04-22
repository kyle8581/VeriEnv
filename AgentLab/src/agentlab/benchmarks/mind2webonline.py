import logging
import json
import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image
import io
import base64

from agentlab.llm.chat_api import ChatModel
from agentlab.llm.llm_utils import Discussion, image_to_jpg_base64_url, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

class WebJudge:
    def __init__(self, model: ChatModel, score_threshold: int = 3):
        self.model = model
        self.score_threshold = score_threshold

    def _identify_key_points(self, task_description: str) -> str:
        """Stage 1: Identify key points from the task description."""
        system_msg = """You are an expert tasked with analyzing a given task to identify the key points explicitly stated in the task description.

**Objective**: Carefully analyze the task description and extract the critical elements explicitly mentioned in the task for achieving its goal.

**Instructions**:
1. Read the task description carefully.
2. Identify and extract **key points** directly stated in the task description.
   - A **key point** is a critical element, condition, or step explicitly mentioned in the task description.
   - Do not infer or add any unstated elements.
   - Words such as "best," "highest," "cheapest," "latest," "most recent," "lowest," "closest," "highest-rated," "largest," and "newest" must go through the sort function(e.g., the key point should be "Filter by highest").

**Respond with**:
- **Key Points**: A numbered list of the explicit key points for completing this task, one per line, without explanations or additional details."""
        
        user_prompt = f"Task: {task_description}"
        messages = Discussion([
            SystemMessage(system_msg),
            HumanMessage(user_prompt)
        ])
        
        response = self.model(messages)
        content = str(response)  # AIMessage is a dict, use str() for content
        
        # Extract key points part
        try:
            if "**Key Points**:" in content:
                key_points = content.split("**Key Points**:")[1].strip()
            elif "Key Points:" in content:
                key_points = content.split("Key Points:")[1].strip()
            else:
                key_points = content.strip()
        except:
            key_points = content.strip()
            
        return key_points

    def _judge_image(self, task_description: str, key_points: str, image: np.ndarray) -> Dict[str, Any]:
        """Stage 2: Judge an individual image against key points."""
        system_msg = """You are an expert evaluator tasked with determining whether an image contains information about the necessary steps to complete a task.

**Objective**: Analyze the provided image and decide if it shows essential steps or evidence required for completing the task. Use your reasoning to explain your decision before assigning a score.

**Instructions**:
1. Provide a detailed description of the image, including its contents, visible elements, text (if any), and any notable features.

2. Carefully examine the image and evaluate whether it contains necessary steps or evidence crucial to task completion:  
- Identify key points that could be relevant to task completion, such as actions, progress indicators, tool usage, applied filters, or step-by-step instructions.  
- Does the image show actions, progress indicators, or critical information directly related to completing the task?  
- Is this information indispensable for understanding or ensuring task success?
- If the image contains partial but relevant information, consider its usefulness rather than dismissing it outright.

3. Provide your response in the following format:  
- **Reasoning**: [Your explanation]  
- **Score**: [1-5]

**Score Scale**:
- **1**: The image does not contain any necessary steps or relevant information.  
- **2**: The image contains minimal or ambiguous information, unlikely to be essential.  
- **3**: The image includes some relevant steps or hints but lacks clarity or completeness.  
- **4**: The image contains important steps or evidence that are highly relevant but not fully comprehensive.  
- **5**: The image clearly displays necessary steps or evidence crucial for completing the task."""

        user_msg = HumanMessage("")
        user_msg.add_text(f"**Task**: {task_description}\n\n**Key Points for Task Completion**: {key_points}\n\nThe snapshot of the web page is shown in the image.")
        user_msg.add_image(image, detail="high")
        
        messages = Discussion([
            SystemMessage(system_msg),
            user_msg
        ])
        
        response = self.model(messages)
        content = str(response)  # AIMessage is a dict, use str() for content
        
        # Parse score and reasoning
        score = 0
        reasoning = ""
        try:
            score_match = re.search(r"Score[:\s*]*([1-5])", content, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
            
            reasoning_match = re.search(r"Reasoning[:\s*]*(.*?)(?:\n\n|\nScore|$)", content, re.IGNORECASE | re.DOTALL)
            if reasoning_match:
                reasoning = reasoning_match.group(1).strip()
            else:
                reasoning = content.strip()
        except Exception as e:
            logger.warning(f"Failed to parse judge_image response: {e}")
            
        return {"score": score, "reasoning": reasoning, "image": image}

    def evaluate(self, task_description: str, action_history: List[str], screenshots: List[np.ndarray], return_details: bool = False) -> float | Dict[str, Any]:
        """Stage 3: Final evaluation based on key points, actions, and important images.
        
        Args:
            task_description: The task description
            action_history: List of actions taken by the agent
            screenshots: List of screenshots (numpy arrays)
            return_details: If True, return a dict with detailed results instead of just score
            
        Returns:
            If return_details=False: float score (0.0 or 1.0)
            If return_details=True: Dict with all evaluation details
        """
        
        # 1. Identify Key Points
        key_points = self._identify_key_points(task_description)
        logger.info(f"Identified Key Points: {key_points}")
        
        # 2. Judge Images
        # Judging images sequentially to avoid async issues with Playwright sync API
        image_results = []
        for i, img in enumerate(screenshots):
            result = self._judge_image(task_description, key_points, img)
            result["step_index"] = i
            image_results.append(result)
        
        # Filter images that meet the threshold
        important_results = [r for r in image_results if r["score"] >= self.score_threshold]
        
        # 3. Final Evaluation
        system_msg = """You are an expert in evaluating the performance of a web navigation agent. The agent is designed to help a human user navigate a website to complete a task. Given the user's task, the agent's action history, key points for task completion, some potentially important web pages in the agent's trajectory and their reasons, your goal is to determine whether the agent has completed the task and achieved all requirements.

Your response must strictly follow the following evaluation criteria!
*Important Evaluation Criteria*:
1: The filtered results must be displayed correctly. If filters were not properly applied (i.e., missing selection, missing confirmation, or no visible effect in results), the task is not considered successful.
2: You must carefully check whether these snapshots and action history meet these key points. Ensure that specific filter conditions, such as "best," "highest," "cheapest," "latest," "most recent," "lowest," "closest," "highest-rated," "largest," and "newest" are correctly applied using the filter function(e.g., sort function).
3: Certain key points or requirements should be applied by the filter. Otherwise, a search with all requirements as input will be deemed a failure since it cannot guarantee that all results meet the requirements!
4: If the task requires filtering by a specific range of money, years, or the number of beds and bathrooms, the applied filter must exactly match the given requirement. Any deviation results in failure. To ensure the task is successful, the applied filter must precisely match the specified range without being too broad or too narrow.
Examples of Failure Cases:
- If the requirement is less than $50, but the applied filter is less than $25, it is a failure.
- If the requirement is $1500-$2500, but the applied filter is $2000-$2500, it is a failure.
- If the requirement is $25-$200, but the applied filter is $0-$200, it is a failure.
- If the required years are 2004-2012, but the filter applied is 2001-2012, it is a failure.
- If the required years are before 2015, but the applied filter is 2000-2014, it is a failure.
- If the task requires exactly 2 beds, but the filter applied is 2+ beds, it is a failure.
5: Some tasks require a submission action or a display of results to be considered successful.
6: If the retrieved information is invalid or empty(e.g., No match was found), but the agent has correctly performed the required action, it should still be considered successful.
7: If the current page already displays all available items, then applying a filter is not necessary. As long as the agent selects items that meet the requirements (e.g., the cheapest or lowest price), the task is still considered successful.

*IMPORTANT*
Format your response into two lines as shown below:

Thoughts: <your thoughts and reasoning process based on double-checking each key points and the evaluation criteria>
Status: "success" or "failure" """

        history_str = "\n".join([f"{i+1}. {action}" for i, action in enumerate(action_history)])
        thoughts_str = "\n".join([f"{i+1}. {r['reasoning']}" for i, r in enumerate(important_results)])
        
        final_prompt = f"""User Task: {task_description}

Key Points:
{key_points}

Action History:
{history_str}

The potentially important snapshots of the webpage in the agent's trajectory and their reasons:
{thoughts_str}"""

        user_msg = HumanMessage(final_prompt)
        # Add important images to the final prompt
        for r in important_results[:10]: # Limit to 10 images to avoid token limits
            user_msg.add_image(r["image"], detail="high")
            
        messages = Discussion([
            SystemMessage(system_msg),
            user_msg
        ])
        
        response = self.model(messages)
        content = str(response)  # AIMessage is a dict, use str() for content
        
        logger.info(f"Final WebJudge Evaluation Content:\n{content}")
        
        # Parse final result
        success = "Status: \"success\"" in content or 'Status: "success"' in content or "Status: success" in content
        score = 1.0 if success else 0.0
        
        # Extract thoughts from response
        thoughts = ""
        try:
            if "Thoughts:" in content:
                thoughts = content.split("Thoughts:")[1].split("Status:")[0].strip()
        except:
            thoughts = content
        
        if return_details:
            # Prepare serializable image results (without numpy arrays)
            serializable_image_results = []
            for r in image_results:
                serializable_image_results.append({
                    "step_index": r["step_index"],
                    "score": r["score"],
                    "reasoning": r["reasoning"],
                    "is_important": r["score"] >= self.score_threshold
                })
            
            important_step_indices = [r["step_index"] for r in important_results]
            
            return {
                "score": score,
                "success": success,
                "key_points": key_points,
                "action_history": action_history,
                "image_judgments": serializable_image_results,
                "important_step_indices": important_step_indices,
                "final_thoughts": thoughts,
                "final_response": content,
                "num_screenshots": len(screenshots),
                "num_important_images": len(important_results),
            }
        
        return score

def get_factual_actions(chat_messages: List[Dict[str, Any]]) -> List[str]:
    """
    Extract factual actions from chat messages.
    """
    factual_actions = []
    for msg in chat_messages:
        # In AgentLab, messages might be in different formats. 
        # For evaluation, we usually look at the assistant's message field.
        # This function might need adjustment based on how chat_messages is populated in AgentLab loop.
        role = msg.get("role")
        message = msg.get("message") or msg.get("content")
        
        if role == "assistant" and message:
            # Extract action from ```action```
            import re
            matches = re.findall(r'```(?:python)?\n?(.*?)\n?```', str(message), re.DOTALL)
            for action in matches:
                factual_actions.append(action.strip())
            if not matches:
                match = re.search(r'In summary, the next action I will perform is ```(.*?)```', str(message))
                if match:
                    factual_actions.append(match.group(1).strip())
    return factual_actions

from .abstract_env import AbstractBenchmark, AbstractEnvArgs
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Mind2WebOnlineEnvArgs(AbstractEnvArgs):
    task_id: str
    max_steps: int = 30
    headless: bool = True

    def make_env(self, action_mapping, exp_dir, exp_task_kwargs=None) -> Any:
        import gymnasium as gym
        import browsergym.mind2webonline
        
        env = gym.make(
            f"browsergym/mind2webonline.{self.task_id}",
            disable_env_checker=True,
            max_episode_steps=self.max_steps,
            headless=self.headless,
            action_mapping=action_mapping,
        )
        return env

class Mind2WebOnlineBenchmark(AbstractBenchmark):
    name: str = "mind2webonline"
    env_args_list: List[Mind2WebOnlineEnvArgs] = []

    def __init__(self, data_path: str = os.getenv("CLONE_CODING_ROOT", ".") + "/mind2web_data_curation/Online_Mind2Web_accessible.json"):
        super().__init__(name=self.name, env_args_list=[])
        self.data_path = data_path
        self._load_tasks()

    def _load_tasks(self):
        import json
        with open(self.data_path, "r") as f:
            tasks = json.load(f)
        
        for task in tasks:
            self.env_args_list.append(Mind2WebOnlineEnvArgs(task_id=task["task_id"]))
