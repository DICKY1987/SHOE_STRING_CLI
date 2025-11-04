"""Registry composition and merge utilities.

This module is responsible for combining the metadata exported by many TUI
modules into a single coherent registry. It does not execute any module
logic directly: instead it calls each module's ``build_module`` function
with a stub host API to obtain its contributions. Based on the declared
semantic versions it then resolves conflicts deterministically.

The resulting registry describes which module provides each route and
command, along with the aggregated set of keybindings. Conflicts in
keybindings are captured in the returned structure so that the host can
surface them to the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from packaging.version import Version

from .discovery import ModuleInfo

__all__ = ["merge_module_metadata", "MetaHostAPI", "MergeResult", "KeybindingConflict"]


class MetaHostAPI:
    """A minimal host API used during metadata extraction.

    Modules receive an instance of this stub when their ``build_module``
    function is called for the purposes of discovery. It satisfies the
    API surface expected by modules (``dispatch`` and ``get_state``), but
    performs no work. This avoids executing side‑effects at discovery time.
    """

    def dispatch(self, action: Dict[str, Any]) -> None:
        # No state is mutated during metadata extraction.
        return

    def get_state(self, namespace: str) -> None:
        # Always return None at discovery time; modules should not rely on
        # any persisted state when simply describing themselves.
        return None


@dataclass
class KeybindingConflict:
    """Represents a conflict where multiple modules request the same key."""

    key: str
    bindings: List[Tuple[ModuleInfo, Dict[str, Any]]]


@dataclass
class MergeResult:
    """Composite result from merging many modules.

    Attributes
    ----------
    route_selections:
        Mapping from route identifier to the module chosen to provide it.
    command_selections:
        Mapping from command identifier to the module chosen to provide it.
    keybindings:
        Mapping from key to all requested bindings. Conflicts are present
        when a key appears more than once.
    conflicts:
        List of keybinding conflicts discovered during the merge.
    """

    route_selections: Dict[str, Tuple[ModuleInfo, Dict[str, Any]]]
    command_selections: Dict[str, ModuleInfo]
    keybindings: Dict[str, List[Tuple[ModuleInfo, Dict[str, Any]]]]
    conflicts: List[KeybindingConflict]


def merge_module_metadata(mod_infos: List[ModuleInfo]) -> MergeResult:
    """Merge metadata from a list of modules.

    Each module is asked to build itself with a ``MetaHostAPI`` to describe
    its contributions. Routes and commands with the same identifier are
    resolved deterministically based on the semantic version declared in
    the manifest: the module with the highest version wins. Keybindings
    are aggregated but never deduplicated; conflicts are recorded and
    returned to the caller.

    Parameters
    ----------
    mod_infos:
        List of discovered modules.

    Returns
    -------
    MergeResult
        The selections and conflicts derived from the provided modules.
    """
    meta_api = MetaHostAPI()
    # route id -> (ModuleInfo, route dict)
    route_selections: Dict[str, Tuple[ModuleInfo, Dict[str, Any]]] = {}
    # command id -> ModuleInfo
    command_selections: Dict[str, ModuleInfo] = {}
    # key -> list of (ModuleInfo, keybinding dict)
    keybindings: Dict[str, List[Tuple[ModuleInfo, Dict[str, Any]]]] = {}

    for mod_info in mod_infos:
        manifest = mod_info.manifest
        mod_semver = Version(manifest["semver"])
        # Build module to inspect its metadata. We ignore the returned
        # functions at this stage; only the identifiers are needed.
        try:
            meta = mod_info.module.build_module(meta_api)  # type: ignore[no-untyped-call]
        except Exception as exc:
            # It is important that metadata extraction never crashes the host.
            raise RuntimeError(
                f"Error building module '{mod_info.name}' for metadata extraction: {exc}"
            ) from exc
        # Routes
        for route in meta.get("routes", []):
            rid: str = route.get("id")
            if not rid:
                continue
            existing = route_selections.get(rid)
            if existing is None:
                route_selections[rid] = (mod_info, route)
            else:
                existing_mod, _ = existing
                existing_semver = Version(existing_mod.manifest["semver"])
                if mod_semver > existing_semver:
                    route_selections[rid] = (mod_info, route)
        # Commands
        for cmd_id in meta.get("commands", {}).keys():
            existing = command_selections.get(cmd_id)
            if existing is None:
                command_selections[cmd_id] = mod_info
            else:
                existing_semver = Version(existing.manifest["semver"])
                if mod_semver > existing_semver:
                    command_selections[cmd_id] = mod_info
        # Keybindings
        for kb in meta.get("keybindings", []):
            key = kb.get("key")
            if not key:
                continue
            keybindings.setdefault(key, []).append((mod_info, kb))
    # Compute conflicts
    conflicts: List[KeybindingConflict] = []
    for key, bindings in keybindings.items():
        if len(bindings) > 1:
            conflicts.append(KeybindingConflict(key=key, bindings=bindings))
    return MergeResult(
        route_selections=route_selections,
        command_selections=command_selections,
        keybindings=keybindings,
        conflicts=conflicts,
    )