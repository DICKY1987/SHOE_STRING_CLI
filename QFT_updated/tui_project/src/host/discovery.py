"""Module discovery for TUI modules.

The discovery mechanism scans a directory on disk for subdirectories that
contain a ``tui.module.yaml`` manifest and associated Python code. Each
module directory is expected to follow the convention::

    <module_name>/
        tui.module.yaml
        <module_name>/
            __init__.py
            module.py

The ``module.py`` file must define a top‑level function called
``build_module(host_api)`` which returns a dictionary describing the
module's contributions (routes, commands, reducers, keybindings, etc.).

The discovery process uses the manifest loader to validate manifests and
performs a dynamic import of ``module.py``. The resulting objects are
returned as a list of dictionaries containing the module name, manifest
content and module code.
"""

from __future__ import annotations

import importlib.util
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List

from .manifest import ManifestValidationError, load_manifest

__all__ = ["ModuleInfo", "discover_modules"]


@dataclass
class ModuleInfo:
    """Container for information about a discovered module."""

    name: str
    manifest: Dict[str, Any]
    module: Any  # the imported module object


def _import_module(module_dir: pathlib.Path) -> Any:
    """Import the module's Python code dynamically.

    The implementation expects a ``module.py`` file within a package
    subdirectory named after the module. For example, for a module
    directory ``ledger_view/`` the code must live in
    ``ledger_view/ledger_view/module.py``.
    """
    pkg_name = module_dir.name
    module_file = module_dir / pkg_name / "module.py"
    if not module_file.exists():
        raise ImportError(f"Missing module file: {module_file}")
    spec = importlib.util.spec_from_file_location(
        f"{pkg_name}.module", module_file
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {module_file}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def discover_modules(base_path: str | pathlib.Path) -> List[ModuleInfo]:
    """Discover all TUI modules under a given directory.

    Parameters
    ----------
    base_path:
        Path to the directory containing module subdirectories.

    Returns
    -------
    List[ModuleInfo]
        Information about each discovered module. The list is ordered
        alphabetically by module name for deterministic behaviour.

    Raises
    ------
    ManifestValidationError
        If any manifest fails validation.
    ImportError
        If the module's code cannot be imported.
    """
    base = pathlib.Path(base_path)
    modules: List[ModuleInfo] = []
    if not base.is_dir():
        raise NotADirectoryError(f"Module path {base} is not a directory")
    for module_dir in sorted(base.iterdir()):
        if not module_dir.is_dir():
            continue
        manifest_file = module_dir / "tui.module.yaml"
        if not manifest_file.exists():
            # Skip directories that do not contain a manifest
            continue
        manifest = load_manifest(manifest_file)
        mod = _import_module(module_dir)
        modules.append(ModuleInfo(name=module_dir.name, manifest=manifest, module=mod))
    return modules