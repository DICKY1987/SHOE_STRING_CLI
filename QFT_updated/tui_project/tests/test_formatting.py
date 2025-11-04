"""Tests for formatting utilities."""

from __future__ import annotations

import os
import pathlib
import sys
from io import StringIO
from unittest.mock import patch

import pytest

# Append the src directory to the Python path so that host modules can be imported.
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from host import formatting


def test_supports_color_with_no_color_env() -> None:
    """Test that NO_COLOR environment variable disables colors."""
    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        with patch("sys.stdout.isatty", return_value=True):
            assert formatting.supports_color() is False


def test_supports_color_without_tty() -> None:
    """Test that colors are disabled when not connected to TTY."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("sys.stdout.isatty", return_value=False):
            assert formatting.supports_color() is False


def test_supports_color_with_dumb_term() -> None:
    """Test that colors are disabled with TERM=dumb."""
    with patch.dict(os.environ, {"TERM": "dumb"}):
        with patch("sys.stdout.isatty", return_value=True):
            assert formatting.supports_color() is False


def test_supports_color_normal_conditions() -> None:
    """Test that colors are enabled under normal conditions."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("sys.stdout.isatty", return_value=True):
            assert formatting.supports_color() is True


def test_bold_with_color_support() -> None:
    """Test bold formatting when colors are supported."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.bold("test")
        assert "\033[1m" in result
        assert "test" in result
        assert "\033[0m" in result


def test_bold_without_color_support() -> None:
    """Test bold formatting when colors are not supported."""
    with patch("host.formatting.supports_color", return_value=False):
        result = formatting.bold("test")
        assert result == "test"
        assert "\033[" not in result


def test_dim_formatting() -> None:
    """Test dim formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.dim("test")
        assert "\033[2m" in result


def test_green_color() -> None:
    """Test green color formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.green("test")
        assert "\033[32m" in result


def test_red_color() -> None:
    """Test red color formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.red("test")
        assert "\033[31m" in result


def test_yellow_color() -> None:
    """Test yellow color formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.yellow("test")
        assert "\033[33m" in result


def test_blue_color() -> None:
    """Test blue color formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.blue("test")
        assert "\033[34m" in result


def test_cyan_color() -> None:
    """Test cyan color formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.cyan("test")
        assert "\033[36m" in result


def test_reset_formatting() -> None:
    """Test reset formatting."""
    with patch("host.formatting.supports_color", return_value=True):
        result = formatting.reset("test")
        assert "\033[0m" in result
        assert result.startswith("\033[0m")


def test_strip_ansi_removes_color_codes() -> None:
    """Test that strip_ansi removes ANSI escape codes."""
    text_with_codes = "\033[31mRed text\033[0m and \033[1mbold\033[0m"
    result = formatting.strip_ansi(text_with_codes)
    assert result == "Red text and bold"
    assert "\033[" not in result


def test_strip_ansi_with_cursor_codes() -> None:
    """Test that strip_ansi removes cursor movement codes."""
    text_with_codes = "\033[2J\033[H\033[31mText\033[0m"
    result = formatting.strip_ansi(text_with_codes)
    assert "\033[" not in result
    assert "Text" in result


def test_strip_ansi_plain_text() -> None:
    """Test that strip_ansi doesn't modify plain text."""
    plain_text = "This is plain text without codes"
    result = formatting.strip_ansi(plain_text)
    assert result == plain_text


def test_multiple_color_functions() -> None:
    """Test combining multiple color functions."""
    with patch("host.formatting.supports_color", return_value=True):
        # Each function should apply its own formatting
        red_text = formatting.red("error")
        green_text = formatting.green("success")
        
        assert "\033[31m" in red_text
        assert "\033[32m" in green_text
        assert red_text != green_text


def test_color_functions_preserve_text() -> None:
    """Test that color functions preserve the original text."""
    original = "Hello, World!"
    
    with patch("host.formatting.supports_color", return_value=False):
        # Without color support, text should be unchanged
        assert formatting.red(original) == original
        assert formatting.green(original) == original
        assert formatting.blue(original) == original


def test_formatting_with_empty_string() -> None:
    """Test formatting functions with empty string."""
    with patch("host.formatting.supports_color", return_value=True):
        assert "\033[" in formatting.red("")
        assert "\033[" in formatting.bold("")
    
    with patch("host.formatting.supports_color", return_value=False):
        assert formatting.red("") == ""
        assert formatting.bold("") == ""


def test_strip_ansi_with_multiple_sequences() -> None:
    """Test strip_ansi with multiple different ANSI sequences."""
    text = "\033[1m\033[31mBold Red\033[0m\033[2mDim\033[0m"
    result = formatting.strip_ansi(text)
    assert result == "Bold RedDim"


def test_all_exports() -> None:
    """Test that all expected functions are exported."""
    expected_exports = [
        "supports_color",
        "bold",
        "dim",
        "green",
        "red",
        "yellow",
        "blue",
        "cyan",
        "reset",
        "strip_ansi",
    ]
    
    for export in expected_exports:
        assert hasattr(formatting, export), f"Missing export: {export}"
        assert callable(getattr(formatting, export)), f"Not callable: {export}"
