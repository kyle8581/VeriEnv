import base64
import os
import importlib.resources
import io
from copy import deepcopy
from dataclasses import dataclass
from functools import partial
from typing import Any, Literal

import numpy as np
import PIL.Image
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.experiments import Agent, AgentInfo
from browsergym.experiments.benchmark import Benchmark, HighLevelActionSetArgs
from browsergym.utils.obs import overlay_som

from agentlab.llm.base_api import AbstractChatModel
from agentlab.llm.chat_api import BaseModelArgs, make_system_message, make_user_message
from agentlab.llm.llm_configs import CHAT_MODEL_ARGS_DICT
from agentlab.llm.llm_utils import ParseError, extract_code_blocks, retry, truncate_tokens
from agentlab.llm.tracking import cost_tracker_decorator

from ..agent_args import AgentArgs
from . import few_shots
from .prompts import TEMPLATES

FEW_SHOT_FILES = importlib.resources.files(few_shots)
VisualWebArenaObservationType = Literal["axtree", "axtree_som", "axtree_screenshot"]


def image_data_to_uri(
    image_data: bytes | np.ndarray, output_format: Literal["png", "jpeg"] = "png"
) -> str:
    assert output_format in ("png", "jpeg")
    # load input image data (auto-detect input format)
    if isinstance(image_data, np.ndarray):
        image = PIL.Image.fromarray(image_data)
    else:
        image = PIL.Image.open(io.BytesIO(image_data))
    # TODO: is this necessary?
    if image.mode in ("RGBA", "LA"):
        image = image.convert("RGB")
    # convert image to desired output format
    with io.BytesIO() as image_buffer:
        image.save(image_buffer, format=output_format.upper())
        image_data = image_buffer.getvalue()
    # convert to base64 data/image URI
    image_b64 = base64.b64encode(image_data).decode("utf-8")
    image_b64 = f"data:image/{output_format};base64," + image_b64
    return image_b64


@dataclass
class VisualWebArenaAgentArgs(AgentArgs):
    agent_name: str = "VisualWebArenaAgent"
    temperature: float = 0.1
    chat_model_args: BaseModelArgs = None
    action_set_args: HighLevelActionSetArgs = None
    observation_type: VisualWebArenaObservationType = "axtree_som"
    with_few_shot_examples: bool = True

    def __post_init__(self):
        self.agent_name = (
            f"{self.agent_name}-{self.observation_type}-{self.chat_model_args.model_name}".replace(
                "/", "_"
            )
        )

    def make_agent(self) -> Agent:
        return VisualWebArenaAgent(
            temperature=self.temperature,
            chat_model=self.chat_model_args.make_model(),
            action_set=self.action_set_args.make_action_set(),
            observation_type=self.observation_type,
            with_few_shot_examples=self.with_few_shot_examples,
        )

    def set_benchmark(self, benchmark: Benchmark, demo_mode: bool):
        self.action_set_args = deepcopy(benchmark.high_level_action_set_args)

    def set_reproducibility_mode(self):
        self.temperature = 0.0

    def prepare(self):
        return self.chat_model_args.prepare_server()

    def close(self):
        return self.chat_model_args.close_server()


def _fix_action_syntax(action: str) -> str:
    """Fix common syntax errors in generated actions."""
    import re

    # Fix double closing parentheses: click("140")) -> click("140")
    # Match function calls and fix trailing extra parens
    action = re.sub(r'\)\)+', ')', action)

    # Fix missing closing quote: click("140) -> click("140")
    # Only if there's an unmatched quote
    if action.count('"') % 2 == 1:
        action = action.rstrip(')')
        action += '")'

    return action


def _convert_adp_action(action: str) -> str:
    """Convert ADP-style actions to BrowserGym format.

    ADP format:  click(bid="100"), type(bid="20", text="laptop", press_enter_after=0)
    BrowserGym:  click("100"), fill("20", "laptop")
    """
    import re

    # type(bid="X", text="Y", press_enter_after=N) -> fill("X", "Y")
    m = re.match(r'type\(bid="([^"]*)",\s*text="([^"]*)"(?:,\s*press_enter_after=(\d+))?\)', action)
    if m:
        bid, text, enter = m.group(1), m.group(2), m.group(3)
        return f'fill("{bid}", "{text}")'

    # click(bid="X") -> click("X")
    m = re.match(r'click\(bid="([^"]*)"\)', action)
    if m:
        return f'click("{m.group(1)}")'

    # hover(bid="X") -> hover("X")
    m = re.match(r'hover\(bid="([^"]*)"\)', action)
    if m:
        return f'hover("{m.group(1)}")'

    # scroll(delta_x=N, delta_y=M) -> scroll(N, M)
    m = re.match(r'scroll\(delta_x=([^,]+),\s*delta_y=([^)]+)\)', action)
    if m:
        return f'scroll({m.group(1)}, {m.group(2)})'

    # select_option(bid="X", option="Y") -> select_option("X", "Y")
    m = re.match(r'select_option\(bid="([^"]*)",\s*option="([^"]*)"\)', action)
    if m:
        return f'select_option("{m.group(1)}", "{m.group(2)}")'

    # goto(url="X") -> goto("X")
    m = re.match(r'goto\(url="([^"]*)"\)', action)
    if m:
        return f'goto("{m.group(1)}")'

    # If no conversion needed, return as-is
    return action


def parser(response: str) -> dict:
    import re

    # Try backtick code blocks first
    blocks = extract_code_blocks(response)
    if len(blocks) > 0:
        action = _fix_action_syntax(blocks[0][1])
        thought = response
        return {"action": action, "think": thought}

    # Fallback: try <action> tags (closed)
    match = re.search(r"<action>\s*(.+?)\s*</action>", response, re.DOTALL)
    if match:
        action = _fix_action_syntax(match.group(1).strip())
        thought = response
        return {"action": action, "think": thought}

    # Fallback: try unclosed <action> tag (model sometimes omits </action>)
    match = re.search(r"<action>\s*(.+)", response, re.DOTALL)
    if match:
        raw = match.group(1).strip()
        # Take only the first line as the action (ignore trailing noise)
        action = raw.split("\n")[0].strip()
        if action:
            action = _fix_action_syntax(action)
            thought = response
            return {"action": action, "think": thought}

    # Fallback: try JSON format {"thought": "...", "action": "..."}  (ADP format)
    import json as _json
    try:
        parsed = _json.loads(response)
        if isinstance(parsed, dict) and "action" in parsed:
            action = _fix_action_syntax(parsed["action"])
            action = _convert_adp_action(action)
            thought = parsed.get("thought", response)
            return {"action": action, "think": thought}
    except (_json.JSONDecodeError, TypeError):
        pass

    raise ParseError("No code block, <action> tag, or JSON action found in the response")


class VisualWebArenaAgent(Agent):
    def __init__(
        self,
        temperature: float,
        chat_model: AbstractChatModel,
        action_set: HighLevelActionSet,
        observation_type: VisualWebArenaObservationType,
        with_few_shot_examples: bool,
    ):
        self.temperature = temperature
        self.chat_model = chat_model
        self.action_set = action_set
        self.observation_type = observation_type
        self.with_few_shot_examples = with_few_shot_examples

        self.action_history = ["None"]

        self.intro_messages: list[dict] = []

        # pre-build the prompt's intro message
        self.intro_messages.append(
            {
                "type": "text",
                "text": TEMPLATES[observation_type]["intro"].format(
                    action_space_description=self.action_set.describe(
                        with_long_description=True, with_examples=False
                    )
                ),
            }
        )

        self.few_shot_messages: list[dict] = []

        # pre-build the prompt's few-shot example messages
        if with_few_shot_examples:
            examples = TEMPLATES[observation_type]["examples"]
            for i, example in enumerate(examples):
                if len(example) == 2:
                    # text-only example
                    observation, action = example
                    self.few_shot_messages.append(
                        {
                            "type": "text",
                            "text": f"""\
Example {i + 1}/{len(examples)}:

{observation}
ACTION: {action}
""",
                        }
                    )
                elif len(example) == 3:
                    # example with screenshot
                    observation, action, screenshot_filename = example
                    screenshot_data = FEW_SHOT_FILES.joinpath(screenshot_filename).read_bytes()
                    self.few_shot_messages.extend(
                        [
                            {
                                "type": "text",
                                "text": f"""\
Example {i + 1}/{len(examples)}:

{observation}
""",
                            },
                            {
                                "type": "text",
                                "text": """\
SCREENSHOT:
""",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data_to_uri(screenshot_data)},
                            },
                            {
                                "type": "text",
                                "text": f"""\
ACTION: {action}
""",
                            },
                        ]
                    )
                else:
                    raise ValueError("Unexpected format for few-shot example.")

    def obs_preprocessor(self, obs):
        obs = super().obs_preprocessor(obs)
        if self.observation_type == "axtree_som" and "screenshot" in obs and "extra_element_properties" in obs:
            obs["screenshot_som"] = overlay_som(obs["screenshot"], obs["extra_element_properties"])
        return obs

    @cost_tracker_decorator
    def get_action(self, obs: Any) -> tuple[str, dict]:
        """
        Replica of VisualWebArena agent
        https://github.com/web-arena-x/visualwebarena/blob/89f5af29305c3d1e9f97ce4421462060a70c9a03/agent/prompts/prompt_constructor.py#L211
        https://github.com/web-arena-x/visualwebarena/blob/89f5af29305c3d1e9f97ce4421462060a70c9a03/agent/prompts/prompt_constructor.py#L272

        Args:
            obs (Any): Observation from the environment

        Returns:
            tuple[str, dict]: Action and AgentInfo
        """
        user_messages = []

        # 1. add few-shot examples (if any)
        user_messages.extend(self.few_shot_messages)

        # 2. add the current observation to the user prompt
        active_tab = obs["active_page_index"][0]
        open_tab_titles = obs["open_pages_titles"]
        cur_tabs_txt = " | ".join(
            f"Tab {i}{' (current)' if i == active_tab else ''}: {title}"
            for i, title in enumerate(open_tab_titles)
        )
        cur_axtree_txt = obs["axtree_txt"]
        cur_url = obs["url"]
        # Prevent oversized prompts: always enforce char-based truncation first,
        # then optionally try token-based truncation.
        max_obs_chars = int(os.getenv("BROWSERGYM_MAX_OBS_CHARS", "4000"))
        if max_obs_chars > 0 and len(cur_axtree_txt) > max_obs_chars:
            cur_axtree_txt = cur_axtree_txt[:max_obs_chars] + "\n... [truncated]"
        user_messages.append(
            {
                "type": "text",
                "text": f"""\
OBSERVATION:

{cur_tabs_txt}

{cur_axtree_txt}

URL: {cur_url}

PREVIOUS ACTION: {self.action_history[-1]}
""",
            }
        )

        if self.observation_type in ("axtree_som", "axtree_screenshot"):
            if self.observation_type == "axtree_som" and "screenshot_som" in obs:
                cur_screenshot = obs["screenshot_som"]
            elif self.observation_type == "axtree_som":
                cur_screenshot = overlay_som(obs["screenshot"], obs["extra_element_properties"])
            else:
                cur_screenshot = obs["screenshot"]
            user_messages.extend(
                [
                    {
                        "type": "text",
                        "text": """\
SCREENSHOT:
""",
                    },
                    {"type": "image_url", "image_url": {"url": image_data_to_uri(cur_screenshot)}},
                ]
            )

        # 3. add the objective (goal) to the user prompt
        user_messages.append(
            {
                "type": "text",
                "text": f"""\
OBJECTIVE:
""",
            }
        )
        user_messages.extend(obs["goal_object"])

        # Merge intro (system) into user message to match training format
        # Training data has everything in a single <|im_start|>user message
        all_user_content = self.intro_messages + user_messages

        # Flatten multimodal content list to plain text string when no images
        # are present, to match the alpaca-style training format exactly.
        if all(item.get("type") == "text" for item in all_user_content):
            plain_text = "".join(item["text"] for item in all_user_content)
            messages = [
                make_user_message(content=plain_text),
            ]
        else:
            messages = [
                make_user_message(content=all_user_content),
            ]

        # finally, query the chat model
        answer: dict = retry(self.chat_model, messages, n_retry=3, parser=parser)

        action = answer.get("action", None)
        thought = answer.get("think", None)

        self.action_history.append(action)

        return (
            action,
            AgentInfo(
                think=thought,
                chat_messages=messages,
            ),
        )


# A WebArena agent is a VisualWebArena agent with only axtree observation
WebArenaAgent = partial(
    VisualWebArenaAgentArgs,
    agent_name="WebArenaAgent",
    observation_type="axtree",
)

WA_AGENT_4O_MINI = WebArenaAgent(
    temperature=0.1,
    chat_model_args=CHAT_MODEL_ARGS_DICT["openai/gpt-4o-mini-2024-07-18"],
)

WA_AGENT_4O = WebArenaAgent(
    temperature=0.1,
    chat_model_args=CHAT_MODEL_ARGS_DICT["openai/gpt-4o-mini-2024-07-18"],
)

WA_AGENT_SONNET = WebArenaAgent(
    temperature=0.1,
    chat_model_args=CHAT_MODEL_ARGS_DICT["openrouter/anthropic/claude-3.5-sonnet:beta"],
)

VWA_AGENT_4O_MINI = VisualWebArenaAgentArgs(
    temperature=0.1,
    chat_model_args=CHAT_MODEL_ARGS_DICT["openai/gpt-4o-mini-2024-07-18"],
)

VWA_AGENT_4O = VisualWebArenaAgentArgs(
    temperature=0.1,
    chat_model_args=CHAT_MODEL_ARGS_DICT["azure/gpt-4o-2024-08-06"],
)

VWA_AGENT_SONNET = VisualWebArenaAgentArgs(
    temperature=0.1,
    chat_model_args=CHAT_MODEL_ARGS_DICT["openrouter/anthropic/claude-3.5-sonnet:beta"],
)
