"""Implementation of the ledger_view TUI module.

This module provides a simple ledger table with a reload command. The state
consists of a list of entries each with an ID, date and amount. The
``reload`` command generates new random amounts to simulate data being
refreshed. The module follows the contract described in the host
documentation: it exports routes, commands, reducers, initial state and
keybindings via a ``build_module`` function.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List


def build_module(host_api: Any) -> Dict[str, Any]:
    """Return the module contributions for the ledger view.

    The ``host_api`` parameter is used to dispatch actions back to the host
    when commands are invoked. It must implement ``dispatch(action: Dict)``.
    """
    # Static set of sample entries used to initialise state and reload.
    initial_entries: List[Dict[str, str]] = [
        {"id": "A1", "date": "2025-10-28", "amount": "$42.00"},
        {"id": "A2", "date": "2025-10-29", "amount": "$15.00"},
        {"id": "A3", "date": "2025-10-30", "amount": "$99.00"},
    ]

    namespace = "ledger_view"

    def reducer(state: Dict[str, Any] | None, action: Dict[str, Any]) -> Dict[str, Any]:
        """Pure reducer updating the ledger state based on actions."""
        if state is None:
            state = {"entries": list(initial_entries)}
        if action.get("type") == "ledger.reload":
            # Generate a new list of entries with random amounts to simulate a reload
            new_entries: List[Dict[str, str]] = []
            for entry in initial_entries:
                amount = random.uniform(5.0, 200.0)
                new_entries.append({**entry, "amount": f"${amount:.2f}"})
            return {"entries": new_entries}
        return state

    def view(state: Dict[str, Any] | None) -> str:
        """Render the ledger table as a multi‑line string."""
        if not state:
            return "(no data)"
        entries: List[Dict[str, str]] = state.get("entries", [])
        lines: List[str] = []
        lines.append("ID    Date         Amount")
        lines.append("--------------------------")
        for e in entries:
            lines.append(f"{e['id']:<5} {e['date']}   {e['amount']:>7}")
        return "\n".join(lines)

    def reload_command() -> None:
        """Dispatch an action to reload the ledger entries."""
        host_api.dispatch({"type": "ledger.reload", "payload": None})

    return {
        "routes": [
            {"id": "ledger", "title": "Ledger", "slot": "main", "view": view},
        ],
        "commands": {
            "ledger.reload": reload_command,
        },
        "reducers": {
            namespace: reducer,
        },
        "initial_state": {
            namespace: {"entries": list(initial_entries)},
        },
        "keybindings": [
            {"key": "r", "command": "ledger.reload"},
        ],
    }