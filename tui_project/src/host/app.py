"""Entry point for running the TUI host.

This module wires together discovery, metadata merging and runtime loading
of modules. It exposes a ``run`` function which starts an interactive
command‑line TUI session. The UI is intentionally minimal: it prints
a simple navigation menu listing the available routes and allows the
user to switch between them or trigger commands via identifiers or
keybindings. The underlying architecture mirrors what a richer curses
implementation would provide, keeping the business logic separate from
the presentation layer.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any, Dict, Tuple

from .discovery import discover_modules, ModuleInfo
from .registry import merge_module_metadata
from .store import Store


class RuntimeHostAPI:
    """Runtime host API passed to modules during normal operation."""

    def __init__(self, store: Store) -> None:
        self._store = store

    def dispatch(self, action: Dict[str, Any]) -> None:
        self._store.dispatch(action)

    def get_state(self, namespace: str) -> Any:
        return self._store.get_state(namespace)


def _build_runtime_modules(mod_infos: list[ModuleInfo], store: Store) -> Dict[str, Dict[str, Any]]:
    """Call ``build_module`` on each module with a real host API.

    Returns a mapping of module name to its build result. Any exceptions
    raised by modules propagate outwards so that errors surface clearly.
    """
    runtime_api = RuntimeHostAPI(store)
    result: Dict[str, Dict[str, Any]] = {}
    for mod_info in mod_infos:
        data = mod_info.module.build_module(runtime_api)  # type: ignore[no-untyped-call]
        result[mod_info.name] = data
    return result


def run(modules_path: str) -> None:
    """Run an interactive TUI host session.

    Parameters
    ----------
    modules_path:
        Filesystem path pointing to the directory containing module
        subdirectories. Each module must include a valid manifest and
        ``module.py`` as described in ``host.discovery``.
    """
    # Discover modules on disk
    try:
        mod_infos = discover_modules(modules_path)
    except Exception as exc:
        print(f"Error discovering modules: {exc}")
        raise SystemExit(1) from exc
    if not mod_infos:
        print("No modules discovered. Nothing to run.")
        return
    # Merge metadata to determine which module provides each route and command
    merge_result = merge_module_metadata(mod_infos)
    # Create state store
    store = Store(initial_state={})
    # Build modules with runtime host API
    runtime_modules = _build_runtime_modules(mod_infos, store)
    # Register reducers and initial state for all namespaces
    for mod_name, data in runtime_modules.items():
        reducers = data.get("reducers", {})
        initial_state = data.get("initial_state", {})
        for namespace, reducer in reducers.items():
            init = initial_state.get(namespace)
            store.register_reducer(namespace, reducer, init)
    # Build route map: id -> (title, slot, view_func, module_name)
    route_map: Dict[str, Tuple[str, str, Any, str]] = {}
    for rid, (mod_info, route_meta) in merge_result.route_selections.items():
        mod_name = mod_info.name
        # find matching route in runtime module data
        routes = runtime_modules[mod_name].get("routes", [])
        chosen = None
        for r in routes:
            if r.get("id") == rid:
                chosen = r
                break
        if chosen is None:
            # The metadata said this module provides the route but it wasn't returned at runtime
            continue
        title = chosen.get("title", rid)
        slot = chosen.get("slot", "main")
        view_func = chosen.get("view")  # a callable accepting state and returning string
        route_map[rid] = (title, slot, view_func, mod_name)
    # Build command map: id -> callable
    command_map: Dict[str, Any] = {}
    for cmd_id, mod_info in merge_result.command_selections.items():
        mod_name = mod_info.name
        cmd_func = runtime_modules[mod_name].get("commands", {}).get(cmd_id)
        if cmd_func is not None:
            command_map[cmd_id] = cmd_func
    # Resolve keybindings: key -> command id based on semver ordering
    keybindings_map: Dict[str, str] = {}
    for key, bindings in merge_result.keybindings.items():
        # Sort bindings by module semver desc; pick first
        sorted_bindings = sorted(
            bindings,
            key=lambda item: (item[0].manifest["semver"], item[0].name),
            reverse=True,
        )
        chosen_modinfo, kb = sorted_bindings[0]
        cmd_id = kb.get("command")
        if cmd_id in command_map:
            keybindings_map[key] = cmd_id
    # Provide warning about conflicts
    if merge_result.conflicts:
        print("Keybinding conflicts detected:")
        for conflict in merge_result.conflicts:
            mods = ", ".join(m.name for m, _ in conflict.bindings)
            print(f"  key '{conflict.key}' requested by modules: {mods}")
        print("The first declared module (by semantic version) will handle the binding.")
    # Determine a default route
    if not route_map:
        print("No routes defined by any module. Exiting.")
        return
    current_route = next(iter(route_map))
    # Interactive loop
    print("Entering TUI host. Type 'q' to quit. Available commands: 'help' for list of routes/commands.")
    while True:
        # Render current view
        title, slot, view_func, mod_name = route_map[current_route]
        state_namespace = mod_name  # by convention we use module name as state namespace
        state = store.get_state(state_namespace)
        view_output = ""
        if callable(view_func):
            try:
                view_output = view_func(state)
            except Exception as exc:
                view_output = f"Error rendering view for {current_route}: {exc}"
        # Print UI
        print("\n" + "=" * 80)
        print(f"Route: {current_route} ({title}) provided by {mod_name}")
        print("-" * 80)
        print(view_output)
        print("-" * 80)
        print("Routes:")
        for idx, (rid, (rtitle, slot, _, _)) in enumerate(route_map.items(), 1):
            marker = "*" if rid == current_route else " "
            print(f"  {idx}. {rid} - {rtitle} {marker}")
        print("Commands:")
        for cmd_id in command_map.keys():
            print(f"  - {cmd_id}")
        print("Keybindings:")
        for key, cmd_id in keybindings_map.items():
            print(f"  {key} → {cmd_id}")
        # Prompt user
        try:
            user_input = input("Select route number, command id, key or 'q': ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        if user_input.lower() == "q":
            break
        if user_input.lower() in ("help", "h"):  # show help and continue
            continue
        # Try interpreting as integer index into routes
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(route_map):
                current_route = list(route_map.keys())[idx]
                continue
        # Try interpreting as route id
        if user_input in route_map:
            current_route = user_input
            continue
        # Try interpreting as keybinding
        if user_input in keybindings_map:
            cmd_id = keybindings_map[user_input]
            cmd_func = command_map.get(cmd_id)
            if callable(cmd_func):
                try:
                    cmd_func()
                except Exception as exc:
                    print(f"Error executing command {cmd_id}: {exc}")
            continue
        # Try interpreting as command id directly
        if user_input in command_map:
            cmd_func = command_map[user_input]
            if callable(cmd_func):
                try:
                    cmd_func()
                except Exception as exc:
                    print(f"Error executing command {user_input}: {exc}")
            continue
        print(f"Unrecognised input: {user_input}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the modular TUI host.")
    parser.add_argument(
        "modules_path",
        type=str,
        help="Path to directory containing TUI modules",
    )
    args = parser.parse_args(argv)
    run(args.modules_path)


if __name__ == "__main__":
    main()