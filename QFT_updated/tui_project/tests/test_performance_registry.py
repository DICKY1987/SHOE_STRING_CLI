"""Performance tests for registry module to validate optimization improvements."""

from __future__ import annotations

import pathlib
import sys
import time
from typing import Any

# Make sure we can import the host packages
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from host.registry import merge_module_metadata
from host.discovery import ModuleInfo


def test_version_caching_performance() -> None:
    """Test that Version objects are cached and not repeatedly created."""
    
    class TestMod:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [{"id": "test_route", "title": "Test", "slot": "main"}],
                "commands": {},
                "reducers": {},
                "initial_state": {},
                "keybindings": [],
            }
    
    # Create multiple modules with same version
    manifest = {
        "module_id": "testmod",
        "semver": "1.0.0",
        "contract_semver": "1.0.0",
        "routes": [{"id": "test_route", "title": "Test", "slot": "main"}],
    }
    
    # Create 100 modules to test caching benefits
    mods = [
        ModuleInfo(name=f"mod{i}", manifest=manifest.copy(), module=TestMod)
        for i in range(100)
    ]
    
    start = time.time()
    result = merge_module_metadata(mods)
    elapsed = time.time() - start
    
    # Should complete quickly with caching
    assert elapsed < 1.0, f"Merging took too long: {elapsed}s"
    assert len(result.route_selections) > 0


def test_merge_metadata_with_many_modules() -> None:
    """Test that metadata merging is efficient with many modules."""
    
    class TestMod1:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [{"id": "route1", "title": "Route 1", "slot": "main"}],
                "commands": {"cmd1": lambda: None},
                "reducers": {},
                "initial_state": {},
                "keybindings": [],
            }
    
    class TestMod2:
        @staticmethod
        def build_module(host_api: Any) -> dict:
            return {
                "routes": [{"id": "route2", "title": "Route 2", "slot": "main"}],
                "commands": {"cmd2": lambda: None},
                "reducers": {},
                "initial_state": {},
                "keybindings": [],
            }
    
    # Create many modules with different versions
    mods = []
    for i in range(50):
        manifest = {
            "module_id": f"mod{i}",
            "semver": f"{i % 10}.{i % 5}.0",
            "contract_semver": "1.0.0",
            "routes": [{"id": f"route{i % 2 + 1}", "title": f"Route {i % 2 + 1}", "slot": "main"}],
        }
        mod_class = TestMod1 if i % 2 == 0 else TestMod2
        mods.append(ModuleInfo(name=f"mod{i}", manifest=manifest, module=mod_class))
    
    start = time.time()
    result = merge_module_metadata(mods)
    elapsed = time.time() - start
    
    # Should complete efficiently
    assert elapsed < 0.5, f"Merging took too long: {elapsed}s"
    assert "route1" in result.route_selections
    assert "route2" in result.route_selections


if __name__ == "__main__":
    print("Running performance tests...")
    
    print("Test 1: Version caching...")
    test_version_caching_performance()
    print("✓ Version caching test passed")
    
    print("Test 2: Many modules merging...")
    test_merge_metadata_with_many_modules()
    print("✓ Many modules test passed")
    
    print("\nAll performance tests passed!")
