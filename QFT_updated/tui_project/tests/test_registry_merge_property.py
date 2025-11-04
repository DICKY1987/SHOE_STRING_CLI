"""Tests for merging module metadata and conflict resolution."""

from __future__ import annotations

import pathlib
import sys
from typing import Any

import pytest


# Make sure we can import the host packages
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from host.registry import merge_module_metadata
from host.discovery import ModuleInfo


def test_route_conflict_resolution() -> None:
    """Modules defining the same route ID should be resolved by semver."""
    # Dummy modules for metadata extraction. Build functions return only metadata; functions themselves are irrelevant here.
    class ModLow:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [
                    {"id": "foo", "title": "Foo (low)", "slot": "main"},
                ],
                "commands": {
                    "foo.cmd": lambda: None,
                },
                "reducers": {},
                "initial_state": {},
                "keybindings": [],
            }

    class ModHigh:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [
                    {"id": "foo", "title": "Foo (high)", "slot": "main"},
                ],
                "commands": {
                    "foo.cmd": lambda: None,
                },
                "reducers": {},
                "initial_state": {},
                "keybindings": [],
            }

    manifest_low = {
        "module_id": "modlow",
        "semver": "0.1.0",
        "contract_semver": "1.0.0",
        "routes": [{"id": "foo", "title": "Foo", "slot": "main"}],
    }
    manifest_high = {
        "module_id": "modhigh",
        "semver": "0.2.0",
        "contract_semver": "1.0.0",
        "routes": [{"id": "foo", "title": "Foo", "slot": "main"}],
    }
    mods = [
        ModuleInfo(name="modlow", manifest=manifest_low, module=ModLow),
        ModuleInfo(name="modhigh", manifest=manifest_high, module=ModHigh),
    ]
    result = merge_module_metadata(mods)
    chosen_mod, route_meta = result.route_selections["foo"]
    assert chosen_mod.name == "modhigh"


def test_keybinding_conflict_detection() -> None:
    """Conflicts should be reported when two modules request the same key."""
    class ModA:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [],
                "commands": {},
                "reducers": {},
                "initial_state": {},
                "keybindings": [
                    {"key": "x", "command": "cmd.a"},
                ],
            }

    class ModB:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [],
                "commands": {},
                "reducers": {},
                "initial_state": {},
                "keybindings": [
                    {"key": "x", "command": "cmd.b"},
                ],
            }

    manifest_a = {
        "module_id": "a",
        "semver": "0.1.0",
        "contract_semver": "1.0.0",
        "routes": [],
    }
    manifest_b = {
        "module_id": "b",
        "semver": "0.1.1",
        "contract_semver": "1.0.0",
        "routes": [],
    }
    mods = [
        ModuleInfo(name="a", manifest=manifest_a, module=ModA),
        ModuleInfo(name="b", manifest=manifest_b, module=ModB),
    ]
    result = merge_module_metadata(mods)
    # There should be exactly one conflict on key 'x'
    assert any(conflict.key == "x" for conflict in result.conflicts)