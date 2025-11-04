"""Manifest loader and validator for TUI modules.

This module encapsulates the logic for reading a TUI module manifest written
in YAML and validating it against the JSON schema defined in
``schema/tui.module.schema.json``. By centralising validation here the rest
of the system can trust that manifests conform to the expected shape. Any
validation error will be raised as a ``ManifestValidationError`` with a
detailed message enumerating all problems.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict

import jsonschema  # type: ignore
import yaml  # type: ignore

__all__ = ["ManifestValidationError", "load_manifest"]


class ManifestValidationError(Exception):
    """Raised when a manifest does not conform to the expected schema."""

    pass


def _load_schema() -> Dict[str, Any]:
    """Load the manifest JSON schema from the repository.

    The schema lives two directories up from this file under ``schema/``.
    It is loaded once at import time and cached for subsequent calls.
    """
    schema_path = pathlib.Path(__file__).resolve().parents[2] / "schema" / "tui.module.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


_SCHEMA: Dict[str, Any] = _load_schema()
_VALIDATOR = jsonschema.Draft7Validator(_SCHEMA)


def load_manifest(path: str | pathlib.Path) -> Dict[str, Any]:
    """Load and validate a TUI module manifest.

    Parameters
    ----------
    path:
        A filesystem path to a YAML manifest file.

    Returns
    -------
    Dict[str, Any]
        The loaded manifest as a dictionary.

    Raises
    ------
    ManifestValidationError
        If the manifest fails schema validation. The exception message
        contains human‑readable details of all validation errors.
    """
    manifest_path = pathlib.Path(path)
    with manifest_path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f)
    # Validate and collect any errors. We gather all errors up front to
    # provide comprehensive feedback rather than failing on the first one.
    errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        messages = []
        for err in errors:
            loc = ".".join(str(p) for p in err.path)
            messages.append(f"{loc or '(root)'}: {err.message}")
        raise ManifestValidationError(
            "Manifest validation error:\n" + "\n".join(messages)
        )
    return data