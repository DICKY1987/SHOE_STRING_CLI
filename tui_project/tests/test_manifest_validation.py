"""Tests for manifest loading and validation."""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml  # type: ignore


# Append the src directory to the Python path so that host modules can be imported.
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from host.manifest import load_manifest, ManifestValidationError


def test_valid_manifest() -> None:
    """Ensure that a well‑formed manifest passes validation."""
    manifest_path = ROOT_DIR / "modules" / "ledger_view" / "tui.module.yaml"
    # Should not raise
    load_manifest(manifest_path)


def test_invalid_manifest_missing_required() -> None:
    """A manifest missing required keys should raise ManifestValidationError."""
    invalid_manifest = {
        # Missing module_id on purpose
        "semver": "0.1.0",
        "contract_semver": "1.0.0",
        "routes": [
            {"id": "foo", "title": "Foo", "slot": "main"},
        ],
    }
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(invalid_manifest, f)
        tmp_name = f.name
    with pytest.raises(ManifestValidationError):
        load_manifest(tmp_name)