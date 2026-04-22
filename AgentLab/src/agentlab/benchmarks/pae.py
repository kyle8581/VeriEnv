"""
PAE (Practical Agent Environment) Benchmark for AgentLab.
Tasks involve navigating real-world websites to complete specific goals.
"""
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

class PAEWebJudge:
    """
    WebJudge for PAE benchmark evaluation.
    Uses LLM to evaluate agent performance on web tasks.
    """
    
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
        content = str(response)
        
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
        content = str(response)
        
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
        """Stage 3: Final evaluation based on key points, actions, and important images."""
        
        # 1. Identify Key Points
        key_points = self._identify_key_points(task_description)
        logger.info(f"Identified Key Points: {key_points}")
        
        # 2. Judge Images
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
1: The agent must have navigated to the relevant content or page that addresses the task.
2: You must carefully check whether the screenshots and action history meet the key points.
3: For tasks requiring finding specific items (recipes, products, etc.), the agent must have displayed relevant results.
4: For tasks requiring reading information (reviews, details, etc.), the agent must have shown that information.
5: If the task asks to "check" or "find" something, the relevant information should be visible in the final screenshots.

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
        for r in important_results[:10]:
            user_msg.add_image(r["image"], detail="high")
            
        messages = Discussion([
            SystemMessage(system_msg),
            user_msg
        ])
        
        response = self.model(messages)
        content = str(response)
        
        logger.info(f"Final PAEWebJudge Evaluation Content:\n{content}")
        
        success = "Status: \"success\"" in content or 'Status: "success"' in content or "Status: success" in content
        score = 1.0 if success else 0.0
        
        thoughts = ""
        try:
            if "Thoughts:" in content:
                thoughts = content.split("Thoughts:")[1].split("Status:")[0].strip()
        except:
            thoughts = content
        
        if return_details:
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
    """Extract factual actions from chat messages."""
    factual_actions = []
    for msg in chat_messages:
        role = msg.get("role")
        message = msg.get("message") or msg.get("content")
        
        if role == "assistant" and message:
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
from bgym import HighLevelActionSetArgs, EnvArgs


# Default action set for PAE (similar to mind2webonline/webarena)
PAE_ACTION_SET_ARGS = HighLevelActionSetArgs(
    subsets=["bid"],
    multiaction=False,
    strict=False,
    retry_with_force=True,
    demo_mode="off",
)


class PAEBenchmark(AbstractBenchmark):
    name: str = "pae"
    env_args_list: List[EnvArgs] = []
    data_path: str = os.getenv("CLONE_CODING_ROOT", ".") + "/data/pae_tasks.json"
    n_repeats: int = 1
    is_multi_tab: bool = True
    high_level_action_set_args: HighLevelActionSetArgs = PAE_ACTION_SET_ARGS

    def __init__(self, data_path: str = os.getenv("CLONE_CODING_ROOT", ".") + "/data/pae_tasks.json", n_repeats: int = 1):
        super().__init__(
            name="pae", 
            env_args_list=[], 
            data_path=data_path, 
            n_repeats=n_repeats,
            is_multi_tab=True,
            high_level_action_set_args=PAE_ACTION_SET_ARGS,
        )
        self._load_tasks()

    def _load_tasks(self):
        import json
        with open(self.data_path, "r") as f:
            tasks = json.load(f)
        
        for _ in range(self.n_repeats):
            for task in tasks:
                self.env_args_list.append(EnvArgs(
                    task_name=f"pae.{task['task_id']}",
                    task_seed=0,
                    max_steps=30,
                    headless=True,
                ))

    def prepare_backends(self):
        """Import browsergym.pae to register PAE environments."""
        import browsergym.pae
