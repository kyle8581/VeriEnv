from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple

import playwright.sync_api

from browsergym.core.task import AbstractBrowserTask

from .judge_dsl import JudgeResult, eval_rinfo_checks, parse_judge_spec
from .sdk_executor import eval_rprog_generic
from .programs.allrecipes import eval_allrecipes_program_check


@dataclass(frozen=True)
class SitePorts:
    frontend_url: str
    backend_url: str


def _ports_for_site(clone_coding_root: Path, site: str) -> SitePorts:
    site_dir = clone_coding_root / "websites" / site

    def _url_for(port: int) -> str:
        return f"http://127.0.0.1:{int(port)}"

    runtime_frontend_port = None
    runtime_backend_port = None

    # First check .runtime/servers.json for actual running ports
    runtime_path = site_dir / ".runtime" / "servers.json"
    if runtime_path.exists():
        try:
            runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            runtime_frontend_port = runtime.get("frontend", {}).get("port")
            runtime_backend_port = runtime.get("backend", {}).get("port")
        except Exception:
            pass

    # Fallback to ports.json
    ports_path = site_dir / "ports.json"
    ports: dict[str, Any] = {}
    if ports_path.exists():
        try:
            p = json.loads(ports_path.read_text(encoding="utf-8"))
            ports = (p.get("ports") or {}) if isinstance(p, dict) else {}
        except Exception:
            ports = {}

    # Prefer runtime ports (actual running ports) over static ports.json
    frontend_port = runtime_frontend_port or ports.get("FRONTEND_PORT") or ports.get("PORT") or ports.get("WEB_PORT") or 3000
    backend_port = runtime_backend_port or ports.get("BACKEND_PORT") or ports.get("API_PORT") or (int(frontend_port) + 1)

    frontend_url = _url_for(frontend_port)

    # allrecipes is a Next.js fullstack app; its python SDK expects the Next base URL
    if site == "allrecipes":
        backend_url = frontend_url
    else:
        backend_url = _url_for(backend_port)

    return SitePorts(frontend_url=frontend_url, backend_url=backend_url)


def _load_task_spec(clone_coding_root: Path, site: str, task_index: int) -> dict[str, Any]:
    site_dir = clone_coding_root / "websites" / site
    path = site_dir / "task_instructions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data if isinstance(data, list) else (data.get("tasks") or [])
    if not isinstance(tasks, list):
        raise ValueError(f"Unexpected task list shape for {path}")
    task = tasks[task_index]
    if not isinstance(task, dict):
        raise ValueError(f"Task at index {task_index} is not an object in {path}")
    return task


def _parse_send_msg_payload(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        try:
            return str(ast.literal_eval(raw))
        except Exception:
            return raw


def _last_assistant_message(chat_messages: list[dict[str, Any]]) -> str | None:
    """Get the last assistant message that is a real answer (not the initial greeting).
    
    The agent's answer must come AFTER a user message (the task instruction).
    This skips the initial "Hi! I am your UI assistant..." greeting.
    """
    # Find the last user message index
    last_user_idx = -1
    for i, msg in enumerate(chat_messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            last_user_idx = i
    
    # Only consider assistant messages that come after the last user message
    for msg in reversed(chat_messages):
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            # Skip if this message is before or at the user message
            msg_idx = chat_messages.index(msg)
            if msg_idx <= last_user_idx:
                continue
            m = msg.get("message") or msg.get("msg")
            if isinstance(m, str) and m.strip():
                # If the assistant message includes an explicit send_msg_to_user action,
                # extract the payload so we can score it as the final answer.
                match = re.search(r"send_msg_to_user\((.*?)\)", m, flags=re.DOTALL)
                if match:
                    payload = _parse_send_msg_payload(match.group(1))
                    if payload is not None:
                        return payload
                # Also skip the greeting message pattern
                if "UI assistant" in m and "can perform web tasks" in m:
                    continue
                return m
    return None


class VeriEnvTask(AbstractBrowserTask):
    """Local website task with WebArena-like STOP[answer] termination and JSON-based judging."""

    @classmethod
    def get_task_id(cls):
        return "verienv"

    def __init__(self, seed: int, clone_coding_root: str, site: str, task_index: int) -> None:
        super().__init__(seed)
        self.clone_coding_root = Path(clone_coding_root).resolve()
        self.site = site
        self.task_index = int(task_index)
        self._done = False

        # Make tasks snappier than default
        self.slow_mo = 0
        self.timeout = 10000

        self.task_spec = _load_task_spec(self.clone_coding_root, self.site, self.task_index)
        self.ports = _ports_for_site(self.clone_coding_root, self.site)

    def setup(self, page: playwright.sync_api.Page) -> tuple[str, dict]:
        instruction = str(self.task_spec.get("instruction") or "").strip()
        judge_raw = self.task_spec.get("judge_for_webagent") or {}
        judge = parse_judge_spec(judge_raw)
        # If checks reference ^a_* fields, nudge the agent to respond as JSON.
        expected_keys = sorted(judge.expected_answer_keys())

        goal_lines = [instruction]
        # goal_lines.append("")
        # goal_lines.append(
        #     "When finished, use the STOP action to send your final answer (stop [answer])."
        # )
        if expected_keys:
            goal_lines.append(
                "Return your final answer as a JSON object containing these keys: "
                + ", ".join(expected_keys)
            )

        # Start at homepage
        page.goto(self.ports.frontend_url + "/", timeout=20000)

        info = {
            "site": self.site,
            "task_index": self.task_index,
            "frontend_url": self.ports.frontend_url,
            "backend_url": self.ports.backend_url,
            "judge": judge.to_dict(),
        }
        return "\n".join(goal_lines).strip(), info

    def validate(
        self, page: playwright.sync_api.Page, chat_messages: list[dict[str, Any]]
    ) -> Tuple[float, bool, str, dict]:
        if self._done:
            return 0.0, True, "", {"status": "already_done"}

        answer = _last_assistant_message(chat_messages)
        if not answer:
            return 0.0, False, "", {"status": "running"}

        judge = parse_judge_spec(self.task_spec.get("judge_for_webagent"))

        # rprog checks
        if judge.eval_type == "rprog":
            # program_check (legacy allrecipes)
            if judge.program_check:
                ok, details = self._eval_program_check(judge.program_check)
                self._done = True
                return (1.0 if ok else 0.0), True, "", {
                    "status": "judged",
                    "eval_type": "rprog",
                    "program_check": judge.program_check,
                    "passed": ok,
                    "details": details,
                }

            # Extract browser context for SDK (cart_id, session, etc.)
            browser_context = self._extract_browser_context(page)

            # generic rprog executor (SDK-based)
            judge_raw = self.task_spec.get("judge_for_webagent", {})
            ok, details = eval_rprog_generic(
                clone_coding_root=self.clone_coding_root,
                site=self.site,
                judge=judge_raw if isinstance(judge_raw, dict) else {},
                backend_url=self.ports.backend_url,
                frontend_url=self.ports.frontend_url,
                browser_context=browser_context,
            )
            self._done = True
            return (1.0 if ok else 0.0), True, "", {
                "status": "judged",
                "eval_type": "rprog",
                "passed": ok,
                "details": details,
            }

        # rinfo checks against the submitted answer
        jr = self._eval_rinfo(answer, page, judge)
        self._done = True
        return (1.0 if jr.passed else 0.0), True, "", {
            "status": "judged",
            "eval_type": "rinfo",
            "passed": jr.passed,
            "details": jr.to_dict(),
        }

    def _eval_rinfo(self, answer_text: str, page: playwright.sync_api.Page, judge) -> JudgeResult:
        # Try to parse JSON for ^a_* field access; otherwise fall back to string
        answer_obj: Any = None
        try:
            answer_obj = json.loads(answer_text)
        except Exception:
            answer_obj = None
        # allow rprog string judges (e.g. babycenter) to access current url as variable
        ctx = {"url": page.url}
        return eval_rinfo_checks(
            judge.checks,
            answer_text=answer_text,
            answer_obj=answer_obj,
            ctx=ctx,
            parse_mode=judge.parse_mode,
        )

    def _extract_browser_context(self, page: playwright.sync_api.Page) -> dict[str, Any]:
        """Extract general browser state for SDK verification.
        
        Returns raw cookies and localStorage - site-specific interpretation
        is done in sdk_helpers.py.
        """
        context: dict[str, Any] = {}
        
        try:
            # Pass all cookies (site helpers will extract what they need)
            context["cookies"] = page.context.cookies()
            
            # Pass localStorage as dict
            context["localStorage"] = page.evaluate("""
                (() => {
                    const data = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        data[key] = localStorage.getItem(key);
                    }
                    return data;
                })()
            """) or {}
            
            # Current URL for context
            context["url"] = page.url
                    
        except Exception:
            pass
        
        return context

    def _eval_program_check(self, check_expr: str) -> tuple[bool, dict[str, Any]]:
        # Only allow a single function call with literals.
        try:
            node = ast.parse(check_expr, mode="eval")
        except SyntaxError as e:
            return False, {"error": f"Invalid program.check syntax: {e}", "expr": check_expr}

        if not isinstance(node.body, ast.Call) or not isinstance(node.body.func, ast.Name):
            return False, {"error": "program.check must be a simple function call", "expr": check_expr}

        fn_name = node.body.func.id

        # Evaluate supported site-specific programs
        if self.site == "allrecipes":
            ok, details = eval_allrecipes_program_check(
                fn_name=fn_name,
                call=node.body,
                clone_coding_root=self.clone_coding_root,
                base_url=self.ports.backend_url,
            )
            return ok, details

        return False, {"error": f"Unsupported rprog site: {self.site}", "fn": fn_name}

