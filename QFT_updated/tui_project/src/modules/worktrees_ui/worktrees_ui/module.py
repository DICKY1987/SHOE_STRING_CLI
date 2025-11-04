"""Implementation of the worktrees_ui TUI module.

This module lists git worktrees in a repository. It exposes a single
navigation route mounted in the ``nav`` slot and a refresh command. The
state holds a list of worktree names. The refresh command will add a
randomly named extra worktree to illustrate state updates. In a real
implementation this module would interface with ``git worktree list``.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List


def build_module(host_api: Any) -> Dict[str, Any]:
    """Return the module contributions for the worktrees UI."""
    initial_items: List[Dict[str, str]] = [
        {"name": "main"},
        {"name": "feature"},
    ]
    namespace = "worktrees_ui"

    def reducer(state: Dict[str, Any] | None, action: Dict[str, Any]) -> Dict[str, Any]:
        if state is None:
            state = {"items": list(initial_items)}
        if action.get("type") == "worktrees.refresh":
            # Simulate adding a new worktree occasionally
            items = list(initial_items)
            if random.random() < 0.5:
                items.append({"name": f"extra{random.randint(1, 10)}"})
            return {"items": items}
        return state

    def view(state: Dict[str, Any] | None) -> str:
        if not state:
            return "(no worktrees)"
        items = state.get("items", [])
        lines: List[str] = []
        lines.append("Worktrees")
        lines.append("---------")
        for item in items:
            lines.append(f" - {item['name']}")
        return "\n".join(lines)

    def refresh_command() -> None:
        host_api.dispatch({"type": "worktrees.refresh", "payload": None})

    return {
        "routes": [
            {"id": "worktrees", "title": "Worktrees", "slot": "nav", "view": view},
        ],
        "commands": {
            "worktrees.refresh": refresh_command,
        },
        "reducers": {
            namespace: reducer,
        },
        "initial_state": {
            namespace: {"items": list(initial_items)},
        },
        "keybindings": [
            {"key": "w", "command": "worktrees.refresh"},
        ],
    }