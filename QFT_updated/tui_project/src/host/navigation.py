"""Navigation utilities for TUI applications.

This module provides utilities for handling navigation between different
views and screens in the TUI application. It includes route management
and navigation history tracking.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

__all__ = [
    "Route",
    "Navigator",
]


class Route:
    """A navigation route definition.

    Attributes
    ----------
    route_id : str
        Unique identifier for the route.
    title : str
        Display title for the route.
    handler : Optional[Callable]
        Optional function to call when navigating to this route.
    metadata : Dict[str, Any]
        Additional metadata about the route.
    """

    def __init__(
        self,
        route_id: str,
        title: str,
        handler: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a route.

        Parameters
        ----------
        route_id
            Unique identifier for the route.
        title
            Display title for the route.
        handler
            Optional function to call when navigating to this route.
        metadata
            Additional metadata about the route.
        """
        self.route_id = route_id
        self.title = title
        self.handler = handler
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Route(route_id={self.route_id!r}, title={self.title!r})"


class Navigator:
    """Navigation manager for the TUI application.

    This class manages routes and navigation history, allowing the application
    to switch between different views and maintain a navigation stack.
    """

    def __init__(self) -> None:
        """Initialize the navigator."""
        self._routes: Dict[str, Route] = {}
        self._history: List[str] = []
        self._current_route: Optional[str] = None

    def register_route(self, route: Route) -> None:
        """Register a navigation route.

        Parameters
        ----------
        route
            The Route to register.

        Raises
        ------
        ValueError
            If a route with the same ID is already registered.
        """
        if route.route_id in self._routes:
            raise ValueError(f"Route '{route.route_id}' is already registered")
        self._routes[route.route_id] = route

    def get_route(self, route_id: str) -> Optional[Route]:
        """Get a route by ID.

        Parameters
        ----------
        route_id
            The route identifier.

        Returns
        -------
        Optional[Route]
            The route if found, None otherwise.
        """
        return self._routes.get(route_id)

    def list_routes(self) -> List[Route]:
        """Get a list of all registered routes.

        Returns
        -------
        List[Route]
            List of all registered routes.
        """
        return list(self._routes.values())

    def navigate_to(self, route_id: str, push_history: bool = True) -> bool:
        """Navigate to a route.

        Parameters
        ----------
        route_id
            The ID of the route to navigate to.
        push_history
            Whether to add the current route to history.

        Returns
        -------
        bool
            True if navigation was successful, False if route not found.
        """
        route = self._routes.get(route_id)
        if route is None:
            return False

        if push_history and self._current_route is not None:
            self._history.append(self._current_route)

        self._current_route = route_id

        if route.handler:
            route.handler()

        return True

    def go_back(self) -> bool:
        """Navigate back to the previous route in history.

        Returns
        -------
        bool
            True if navigation was successful, False if history is empty.
        """
        if not self._history:
            return False

        previous_route_id = self._history.pop()
        return self.navigate_to(previous_route_id, push_history=False)

    def current_route(self) -> Optional[Route]:
        """Get the current route.

        Returns
        -------
        Optional[Route]
            The current route if set, None otherwise.
        """
        if self._current_route is None:
            return None
        return self._routes.get(self._current_route)

    def history(self) -> List[str]:
        """Get the navigation history.

        Returns
        -------
        List[str]
            List of route IDs in navigation history.
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the navigation history."""
        self._history.clear()


# Global navigator instance
_global_navigator: Optional[Navigator] = None


def get_global_navigator() -> Navigator:
    """Get the global navigator instance.

    Returns
    -------
    Navigator
        The global navigator.
    """
    global _global_navigator
    if _global_navigator is None:
        _global_navigator = Navigator()
    return _global_navigator
