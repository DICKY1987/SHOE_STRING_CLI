"""Simple state store and event bus for the TUI host.

The store keeps per‑namespace state and applies reducers in response to
dispatched actions. Reducers are pure functions of the form

    def reducer(state: Any, action: Dict[str, Any]) -> Any

which return a new state for their namespace. Listeners can subscribe
to be notified of every dispatched action; this can be used to trigger
side effects or update derived views. The store does not perform any
threading or asynchronous work: all updates happen synchronously.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

Action = Dict[str, Any]
Reducer = Callable[[Any, Action], Any]


class Store:
    """A namespaced state container with reducer support."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] | None = None) -> None:
        # Namespace -> current state
        self._state: Dict[str, Any] = dict(initial_state or {})
        # Namespace -> reducer function
        self._reducers: Dict[str, Reducer] = {}
        # Callbacks invoked after every action
        self._listeners: List[Callable[[Action], None]] = []

    def register_reducer(self, namespace: str, reducer: Reducer, initial_state: Any | None = None) -> None:
        """Register a reducer for a namespace and optionally set its initial state."""
        if namespace in self._reducers:
            raise ValueError(f"Reducer already registered for namespace '{namespace}'")
        self._reducers[namespace] = reducer
        if initial_state is not None:
            self._state[namespace] = initial_state
        else:
            # Ensure the namespace exists in state even if empty
            self._state.setdefault(namespace, {})

    def dispatch(self, action: Action) -> None:
        """Dispatch an action to all reducers and notify listeners."""
        # Apply reducers
        for namespace, reducer in self._reducers.items():
            current_state = self._state.get(namespace)
            new_state = reducer(current_state, action)
            self._state[namespace] = new_state
        # Notify listeners
        for listener in list(self._listeners):
            listener(action)

    def get_state(self, namespace: str) -> Any:
        """Return state for a namespace, or None if none exists."""
        return self._state.get(namespace)

    def subscribe(self, callback: Callable[[Action], None]) -> None:
        """Add a callback invoked on every dispatched action."""
        self._listeners.append(callback)

    @property
    def state(self) -> Dict[str, Any]:
        """Return a snapshot of the current store state."""
        return dict(self._state)