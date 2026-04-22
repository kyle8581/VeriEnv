"""
Sync tasks from todo.md into Linear (optional).

Usage:
  python scripts/linear_sync.py

Required env:
  LINEAR_API_KEY   - personal API key
  LINEAR_TEAM_ID   - team id to create issues in (can be discovered)

Notes:
- This script is intentionally optional. If env vars are missing, it exits with a helpful message.
- Tasks are identified by `DISC-<number>` and synced using Linear `externalId` so re-runs are idempotent.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import urllib.request


ROOT = Path(__file__).resolve().parents[1]
TODO_PATH = ROOT / "todo.md"
MAP_PATH = ROOT / ".linear_map.json"
API_URL = "https://api.linear.app/graphql"


@dataclass(frozen=True)
class Task:
    external_id: str  # e.g. DISC-1
    title: str  # e.g. "Project scaffolding"
    body: str  # e.g. "Create monorepo structure ..."
    status: str  # "todo" | "in_progress" | "done"


TASK_RE = re.compile(
    r"^\s*-\s*\[(?P<checked>[ xX])\]\s+\*\*(?P<key>DISC-\d+)\s+(?P<title>[^*]+)\*\*:\s+(?P<body>.+?)\s*$"
)


def _read_tasks(md: str) -> List[Task]:
    tasks: List[Task] = []
    current_section = ""

    for raw_line in md.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("## "):
            current_section = line[3:].strip().lower()

        m = TASK_RE.match(line)
        if not m:
            continue

        checked = m.group("checked").strip().lower() == "x"
        key = m.group("key").strip()
        title = m.group("title").strip()
        body = m.group("body").strip()

        if checked or current_section == "done":
            status = "done"
        elif current_section == "in progress":
            status = "in_progress"
        else:
            status = "todo"

        tasks.append(Task(external_id=key, title=title, body=body, status=status))

    return tasks


def _http_post_graphql(api_key: str, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(API_URL, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", api_key)

    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data=payload, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Linear API request failed: {e}") from e

    if "errors" in data:
        raise RuntimeError(f"Linear API returned errors: {data['errors']}")

    return data["data"]


def _discover_team_id(api_key: str) -> Tuple[str, List[Tuple[str, str]]]:
    q = """
    query ViewerTeams {
      viewer {
        teams {
          nodes { id name }
        }
      }
    }
    """
    data = _http_post_graphql(api_key, q, {})
    teams = [(t["id"], t["name"]) for t in data["viewer"]["teams"]["nodes"]]
    if not teams:
        raise RuntimeError("No Linear teams found for this API key.")
    return teams[0][0], teams


def _get_team_states(api_key: str, team_id: str) -> Dict[str, str]:
    q = """
    query TeamStates($teamId: String!) {
      team(id: $teamId) {
        states {
          nodes { id name type }
        }
      }
    }
    """
    data = _http_post_graphql(api_key, q, {"teamId": team_id})
    states = data["team"]["states"]["nodes"]

    # Prefer workflow types where available.
    state_by_type: Dict[str, str] = {}
    for s in states:
        if s.get("type"):
            state_by_type[s["type"]] = s["id"]

    # Fallback by name.
    state_by_name = {s["name"].lower(): s["id"] for s in states}

    unstarted = state_by_type.get("unstarted") or state_by_name.get("todo") or next(iter(state_by_name.values()))
    started = state_by_type.get("started") or state_by_name.get("in progress") or unstarted
    completed = state_by_type.get("completed") or state_by_name.get("done") or started

    return {"todo": unstarted, "in_progress": started, "done": completed}


def _find_issue_by_external_id(api_key: str, external_id: str) -> Optional[Dict[str, Any]]:
    q = """
    query FindIssue($externalId: String!) {
      issues(filter: { externalId: { eq: $externalId } }) {
        nodes { id identifier title url state { id name } }
      }
    }
    """
    data = _http_post_graphql(api_key, q, {"externalId": external_id})
    nodes = data["issues"]["nodes"]
    return nodes[0] if nodes else None


def _create_issue(api_key: str, team_id: str, state_id: str, task: Task) -> Dict[str, Any]:
    q = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { id identifier title url }
      }
    }
    """
    input_ = {
        "teamId": team_id,
        "title": f"{task.external_id} {task.title}",
        "description": task.body,
        "externalId": task.external_id,
        "stateId": state_id,
    }
    data = _http_post_graphql(api_key, q, {"input": input_})
    return data["issueCreate"]["issue"]


def _update_issue(api_key: str, issue_id: str, state_id: str, task: Task) -> Dict[str, Any]:
    q = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue { id identifier title url }
      }
    }
    """
    input_ = {
        "title": f"{task.external_id} {task.title}",
        "description": task.body,
        "stateId": state_id,
    }
    data = _http_post_graphql(api_key, q, {"id": issue_id, "input": input_})
    return data["issueUpdate"]["issue"]


def main() -> int:
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")
    if not api_key:
        print("LINEAR_API_KEY not set; skipping Linear sync.")
        return 0

    if not TODO_PATH.exists():
        print(f"todo.md not found at {TODO_PATH}")
        return 1

    md = TODO_PATH.read_text(encoding="utf-8")
    tasks = _read_tasks(md)
    if not tasks:
        print("No DISC-* tasks found in todo.md; nothing to sync.")
        return 0

    if not team_id:
        default_team_id, teams = _discover_team_id(api_key)
        teams_msg = ", ".join([f"{name} ({tid})" for tid, name in teams])
        print("LINEAR_TEAM_ID not set.")
        print(f"Discovered teams: {teams_msg}")
        print(f"Defaulting to first team: {default_team_id}")
        team_id = default_team_id

    state_ids = _get_team_states(api_key, team_id)

    linear_map: Dict[str, Any] = {}
    if MAP_PATH.exists():
        try:
            linear_map = json.loads(MAP_PATH.read_text(encoding="utf-8"))
        except Exception:
            linear_map = {}

    updated: Dict[str, Any] = {}

    for task in tasks:
        desired_state = state_ids[task.status]
        existing = _find_issue_by_external_id(api_key, task.external_id)
        if existing:
            issue = _update_issue(api_key, existing["id"], desired_state, task)
        else:
            issue = _create_issue(api_key, team_id, desired_state, task)

        updated[task.external_id] = {"id": issue["id"], "identifier": issue["identifier"], "url": issue["url"]}
        print(f"Synced {task.external_id} -> {issue['identifier']} ({issue['url']})")

    linear_map.update(updated)
    MAP_PATH.write_text(json.dumps(linear_map, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

