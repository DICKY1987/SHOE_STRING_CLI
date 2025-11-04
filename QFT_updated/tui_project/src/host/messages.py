"""Message display utilities for user feedback.

This module provides consistent message formatting for informational messages,
warnings, errors, and success messages. All functions respect color support
and provide both colored and plain-text output as appropriate.
"""

from __future__ import annotations

import sys
from typing import Optional, TextIO

from . import formatting

__all__ = [
    "info",
    "warn",
    "error",
    "success",
    "print_message",
]


def print_message(
    message: str,
    prefix: str = "",
    color_fn: Optional[callable] = None,
    file: Optional[TextIO] = None,
) -> None:
    """Print a formatted message with optional prefix and color.

    Parameters
    ----------
    message
        The message to print.
    prefix
        Optional prefix to prepend to the message (e.g., "ERROR:", "INFO:").
    color_fn
        Optional color function from formatting module to apply.
    file
        Optional file object to write to. Defaults to stdout.
    """
    if file is None:
        file = sys.stdout
    
    if prefix:
        formatted_prefix = f"{prefix} "
        if color_fn:
            formatted_prefix = color_fn(formatted_prefix)
    else:
        formatted_prefix = ""
    
    print(f"{formatted_prefix}{message}", file=file)


def info(message: str, file: Optional[TextIO] = None) -> None:
    """Print an informational message.

    Parameters
    ----------
    message
        The message to print.
    file
        Optional file object to write to. Defaults to stdout.
    """
    print_message(message, prefix="INFO:", color_fn=formatting.cyan, file=file)


def warn(message: str, file: Optional[TextIO] = None) -> None:
    """Print a warning message.

    Parameters
    ----------
    message
        The warning message to print.
    file
        Optional file object to write to. Defaults to stderr.
    """
    if file is None:
        file = sys.stderr
    print_message(message, prefix="WARNING:", color_fn=formatting.yellow, file=file)


def error(message: str, file: Optional[TextIO] = None) -> None:
    """Print an error message.

    Parameters
    ----------
    message
        The error message to print.
    file
        Optional file object to write to. Defaults to stderr.
    """
    if file is None:
        file = sys.stderr
    print_message(message, prefix="ERROR:", color_fn=formatting.red, file=file)


def success(message: str, file: Optional[TextIO] = None) -> None:
    """Print a success message.

    Parameters
    ----------
    message
        The success message to print.
    file
        Optional file object to write to. Defaults to stdout.
    """
    print_message(message, prefix="SUCCESS:", color_fn=formatting.green, file=file)
