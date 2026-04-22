#!/usr/bin/env python3
"""
Generate a comprehensive experiment report JSON from AgentLab experiment results.

Extracts:
1. Task instruction
2. Judge code for agent evaluation
3. Tool call results (agent answers)
4. Full input/output per step
5. Pass/fail status

Usage:
    python tools/generate_exp_report.py <exp_dir>
    python tools/generate_exp_report.py <study_dir>  # processes all experiments
"""

from __future__ import annotations

import argparse
import gzip
import json
import pickle
import re
from pathlib import Path
from typing import Any


def load_pickle(path: Path) -> Any:
    """Load a pickle file (gzipped or not)."""
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            return pickle.load(f)
    else:
        with open(path, "rb") as f:
            return pickle.load(f)


def extract_task_info(task_name: str, clone_root: Path) -> dict:
    """Extract task instruction and judge code from task_instructions.json."""
    # Parse task name: verienv.<site>.<idx>
    match = re.match(r"verienv\.(\w+)\.(\d+)", task_name)
    if not match:
        return {"error": f"Could not parse task name: {task_name}"}
    
    site = match.group(1)
    idx = int(match.group(2))
    
    task_file = clone_root / "websites" / site / "task_instructions.json"
    if not task_file.exists():
        return {"error": f"Task file not found: {task_file}"}
    
    try:
        data = json.loads(task_file.read_text(encoding="utf-8"))
        tasks = data if isinstance(data, list) else (data.get("tasks") or [])
        if idx >= len(tasks):
            return {"error": f"Task index {idx} out of range (max: {len(tasks)-1})"}
        
        task = tasks[idx]
        return {
            "site": site,
            "task_idx": idx,
            "instruction": task.get("instruction") or task.get("goal") or task.get("prompt"),
            "start_url": task.get("start_url") or task.get("url"),
            "difficulty": task.get("difficulty"),
            "eval_type": task.get("eval_type"),
            "judge_code": task.get("checks") or task.get("judge") or task.get("evaluation"),
            "full_task": task,
        }
    except Exception as e:
        return {"error": f"Failed to load task: {e}"}


def extract_step_info(step_file: Path, exp_dir: Path) -> dict:
    """Extract relevant info from a step pickle file."""
    step = load_pickle(step_file)
    
    result = {
        "step": step.step,
        "action": step.action,
        "reward": step.reward,
        "raw_reward": step.raw_reward,
        "terminated": step.terminated,
        "truncated": step.truncated,
    }
    
    # Add screenshot path (stored directly in exp_dir as screenshot_step_X.png)
    screenshot_file = exp_dir / f"screenshot_step_{step.step}.png"
    if screenshot_file.exists():
        result["screenshot_path"] = f"screenshot_step_{step.step}.png"
    else:
        result["screenshot_path"] = None
    
    # Extract observation info
    if hasattr(step, "obs") and step.obs:
        obs = step.obs
        result["obs"] = {
            "goal": obs.get("goal"),
            "url": obs.get("url"),
            "last_action": obs.get("last_action"),
            "last_action_error": obs.get("last_action_error"),
            "focused_element_bid": obs.get("focused_element_bid"),
            # Truncate large text fields
            "axtree_txt": (obs.get("axtree_txt") or "")[:5000] + ("..." if len(obs.get("axtree_txt") or "") > 5000 else ""),
        }
        # Extract chat messages from obs
        chat_msgs = obs.get("chat_messages")
        if chat_msgs:
            result["obs"]["chat_messages"] = [
                {"role": m.get("role"), "message": m.get("message", "")[:500]}
                for m in chat_msgs
            ]
    
    # Extract agent info (LLM interaction)
    if hasattr(step, "agent_info") and step.agent_info:
        ai = step.agent_info
        result["agent_info"] = {}
        
        if hasattr(ai, "think") and ai.think:
            result["agent_info"]["think"] = ai.think
        
        if hasattr(ai, "chat_messages") and ai.chat_messages:
            # Extract full LLM conversation
            llm_messages = []
            for msg in ai.chat_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                # Content can be a list of dicts (multimodal) or string
                if isinstance(content, list):
                    text_content = ""
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_content += item.get("text", "")
                    content = text_content
                llm_messages.append({
                    "role": role,
                    "content": content[:10000] if isinstance(content, str) else str(content)[:10000],
                })
            result["agent_info"]["llm_messages"] = llm_messages
        
        if hasattr(ai, "stats") and ai.stats:
            result["agent_info"]["stats"] = ai.stats
    
    # Extract task info (evaluation results)
    if hasattr(step, "task_info") and step.task_info:
        result["task_info"] = step.task_info
    
    return result


def process_experiment(exp_dir: Path, clone_root: Path) -> dict:
    """Process a single experiment directory and generate report."""
    report = {
        "exp_dir": str(exp_dir),
        "exp_name": exp_dir.name,
    }
    
    # Load exp_args
    exp_args_file = exp_dir / "exp_args.pkl"
    if exp_args_file.exists():
        exp_args = load_pickle(exp_args_file)
        report["task_name"] = exp_args.env_args.task_name if hasattr(exp_args, "env_args") else None
        report["agent_name"] = exp_args.agent_args.agent_name if hasattr(exp_args, "agent_args") else None
        report["exp_date"] = str(exp_args.exp_date) if hasattr(exp_args, "exp_date") else None
        
        # Get task info
        if report["task_name"]:
            report["task"] = extract_task_info(report["task_name"], clone_root)
    
    # Load summary_info
    summary_file = exp_dir / "summary_info.json"
    if summary_file.exists():
        report["summary"] = json.loads(summary_file.read_text())
    
    # Load goal_object
    goal_file = exp_dir / "goal_object.pkl.gz"
    if goal_file.exists():
        goal = load_pickle(goal_file)
        if isinstance(goal, tuple) and len(goal) > 0:
            goal = goal[0]
        if isinstance(goal, dict):
            report["goal_object"] = goal
        else:
            report["goal_object"] = str(goal)
    
    # Load all steps
    step_files = sorted(exp_dir.glob("step_*.pkl.gz"), key=lambda p: int(re.search(r"step_(\d+)", p.name).group(1)))
    report["steps"] = []
    for sf in step_files:
        try:
            step_info = extract_step_info(sf, exp_dir)
            report["steps"].append(step_info)
        except Exception as e:
            report["steps"].append({"error": str(e), "file": sf.name})
    
    # Determine pass/fail
    report["n_steps"] = len(report["steps"])
    report["final_reward"] = report["summary"].get("cum_reward", 0) if "summary" in report else 0
    report["passed"] = report["final_reward"] > 0
    
    # Extract final answer if available
    final_answer = None
    for step in reversed(report["steps"]):
        action = step.get("action", "")
        if action and "send_msg_to_user" in str(action):
            # Extract the message from send_msg_to_user("...")
            match = re.search(r'send_msg_to_user\s*\(\s*["\'](.+?)["\']\s*\)', str(action), re.DOTALL)
            if match:
                final_answer = match.group(1)
                break
        elif action and "stop" in str(action).lower():
            match = re.search(r'stop\s*\[\s*(.+?)\s*\]', str(action), re.DOTALL)
            if match:
                final_answer = match.group(1)
                break
    report["final_answer"] = final_answer
    
    return report


def process_study(study_dir: Path, clone_root: Path) -> list[dict]:
    """Process all experiments in a study directory.
    
    Generates a report.json in EACH experiment folder.
    Returns list of all reports for summary.
    """
    reports = []
    
    # Find all experiment subdirectories (they contain exp_args.pkl)
    for exp_dir in sorted(study_dir.iterdir()):
        if exp_dir.is_dir() and (exp_dir / "exp_args.pkl").exists():
            print(f"Processing: {exp_dir.name}")
            try:
                report = process_experiment(exp_dir, clone_root)
                # Save individual report.json in the experiment folder
                report_file = exp_dir / "report.json"
                report_file.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False))
                print(f"  -> {report_file.name} (passed={report.get('passed')})")
                reports.append(report)
            except Exception as e:
                print(f"  Error: {e}")
                reports.append({"exp_dir": str(exp_dir), "error": str(e)})
    
    return reports


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive experiment report")
    parser.add_argument("path", type=str, help="Path to experiment or study directory")
    parser.add_argument("--clone-root", type=str, default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        help="Path to clone-coding root")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output summary JSON file for study (default: <path>/study_summary.json)")
    args = parser.parse_args()
    
    path = Path(args.path).resolve()
    clone_root = Path(args.clone_root).resolve()
    
    if not path.exists():
        print(f"Error: Path not found: {path}")
        return 1
    
    # Determine if this is a single experiment or a study
    if (path / "exp_args.pkl").exists():
        # Single experiment
        print(f"Processing single experiment: {path.name}")
        report = process_experiment(path, clone_root)
        output_file = path / "report.json"
        output_file.write_text(json.dumps(report, indent=2, default=str, ensure_ascii=False))
        print(f"Report saved to: {output_file}")
    else:
        # Study directory - generate report.json in EACH experiment folder
        print(f"Processing study: {path.name}")
        print(f"Generating report.json for each experiment...\n")
        reports = process_study(path, clone_root)
        
        # Generate study summary
        summary = {
            "study_dir": str(path),
            "total_experiments": len(reports),
            "passed": sum(1 for r in reports if r.get("passed")),
            "failed": sum(1 for r in reports if not r.get("passed") and "error" not in r),
            "errors": sum(1 for r in reports if "error" in r),
            "pass_rate": 0,
            "experiments_summary": [
                {
                    "task_name": r.get("task_name"),
                    "passed": r.get("passed"),
                    "final_answer": r.get("final_answer"),
                    "n_steps": r.get("n_steps"),
                    "final_reward": r.get("final_reward"),
                }
                for r in reports if "error" not in r
            ]
        }
        summary["pass_rate"] = summary["passed"] / summary["total_experiments"] if summary["total_experiments"] > 0 else 0
        
        summary_file = Path(args.output) if args.output else path / "study_summary.json"
        summary_file.write_text(json.dumps(summary, indent=2, default=str, ensure_ascii=False))
        
        print(f"\n{'='*50}")
        print(f"Study Summary")
        print(f"{'='*50}")
        print(f"  Total experiments: {summary['total_experiments']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Pass rate: {summary['pass_rate']:.1%}")
        print(f"\nIndividual reports: <exp_folder>/report.json")
        print(f"Study summary: {summary_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())

