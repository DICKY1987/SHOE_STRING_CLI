"""Snapshot tests for the ledger_view module's rendering logic."""

from __future__ import annotations

import pathlib
import sys
from typing import Any, Dict, List


# Append src to path to import module
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import ledger module
from modules.ledger_view.ledger_view import module as ledger_module  # type: ignore


class StubHostAPI:
    """Minimal host API used for testing: records dispatched actions."""

    def __init__(self) -> None:
        self.actions: List[Dict[str, Any]] = []

    def dispatch(self, action: Dict[str, Any]) -> None:
        self.actions.append(action)

    def get_state(self, namespace: str) -> None:
        return None


def test_ledger_view_snapshot() -> None:
    """Verify that the ledger view renders the expected table for initial state."""
    host_api = StubHostAPI()
    data = ledger_module.build_module(host_api)
    namespace = "ledger_view"
    initial_state = data["initial_state"][namespace]
    # Find the view function for the ledger route
    view_func = None
    for route in data["routes"]:
        if route.get("id") == "ledger":
            view_func = route.get("view")
            break
    assert callable(view_func)
    output = view_func(initial_state)
    # Compute expected output manually
    entries: List[Dict[str, str]] = [
        {"id": "A1", "date": "2025-10-28", "amount": "$42.00"},
        {"id": "A2", "date": "2025-10-29", "amount": "$15.00"},
        {"id": "A3", "date": "2025-10-30", "amount": "$99.00"},
    ]
    lines: List[str] = []
    lines.append("ID    Date         Amount")
    lines.append("--------------------------")
    for e in entries:
        lines.append(f"{e['id']:<5} {e['date']}   {e['amount']:>7}")
    expected = "\n".join(lines)
    assert output == expected