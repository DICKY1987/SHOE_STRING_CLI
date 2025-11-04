"""Formatting utilities for TUI output.

This module provides utilities for formatting console output with support for
ANSI color codes, TTY detection, and NO_COLOR environment variable compliance.
All formatting functions respect the NO_COLOR convention and automatically
disable colors when output is not to a TTY.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

__all__ = [
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


def supports_color() -> bool:
    """Check if the current environment supports color output.

    Color is supported if all of the following are true:
    - The NO_COLOR environment variable is not set
    - stdout is connected to a TTY
    - The TERM environment variable is not 'dumb'

    Returns
    -------
    bool
        True if color output should be enabled, False otherwise.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def _colorize(text: str, code: str) -> str:
    """Apply ANSI color code to text if colors are supported.

    Parameters
    ----------
    text
        The text to colorize.
    code
        The ANSI escape code to apply.

    Returns
    -------
    str
        The colorized text if colors are supported, otherwise the original text.
    """
    if not supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    """Format text as bold.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Bold-formatted text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "1")


def dim(text: str) -> str:
    """Format text as dim/faint.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Dim-formatted text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "2")


def green(text: str) -> str:
    """Format text in green color.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Green-colored text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "32")


def red(text: str) -> str:
    """Format text in red color.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Red-colored text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "31")


def yellow(text: str) -> str:
    """Format text in yellow color.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Yellow-colored text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "33")


def blue(text: str) -> str:
    """Format text in blue color.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Blue-colored text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "34")


def cyan(text: str) -> str:
    """Format text in cyan color.

    Parameters
    ----------
    text
        The text to format.

    Returns
    -------
    str
        Cyan-colored text if colors are supported, otherwise the original text.
    """
    return _colorize(text, "36")


def reset(text: str) -> str:
    """Reset all formatting for text.

    Parameters
    ----------
    text
        The text to reset formatting for.

    Returns
    -------
    str
        The text with all formatting reset.
    """
    if not supports_color():
        return text
    return f"\033[0m{text}"


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from text.

    This function removes color codes, cursor movement, and other ANSI
    control sequences from the input text.

    Parameters
    ----------
    text
        The text to strip ANSI codes from.

    Returns
    -------
    str
        The text with all ANSI escape codes removed.
    """
    import re
    # More comprehensive regex that matches CSI sequences
    ansi_escape = re.compile(r'\033\[[0-9;]*[a-zA-Z]|\033\[[\?]?[0-9;]*[a-zA-Z]')
    return ansi_escape.sub('', text)
