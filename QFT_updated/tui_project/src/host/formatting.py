from __future__ import annotations

import os
import sys
from typing import Optional

CSI = "\033["

COLORS = {
    "reset": "0m",
    "bold": "1m",
    "underline": "4m",
    "dim": "2m",
    "red": "31m",
    "green": "32m",
    "yellow": "33m",
    "blue": "34m",
    "magenta": "35m",
    "cyan": "36m",
    "white": "37m",
}

LEVEL_COLOR = {
    "error": "red",
    "warn": "yellow",
    "warning": "yellow",
    "success": "green",
    "info": "cyan",
}


def _isatty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def color_supported() -> bool:
    """
    Returns True if color output is supported and enabled for the current environment.
    Honors NO_COLOR (https://no-color.org/) and requires a TTY.
    """
    if os.environ.get("NO_COLOR"):
        return False
    return _isatty()


def _wrap(code: str, text: str) -> str:
    return f"{CSI}{code}{text}{CSI}{COLORS['reset']}"


def bold(text: str, enabled: Optional[bool] = None) -> str:
    if enabled is None:
        enabled = color_supported()
    return _wrap(COLORS["bold"], text) if enabled else text


def underline(text: str, enabled: Optional[bool] = None) -> str:
    if enabled is None:
        enabled = color_supported()
    return _wrap(COLORS["underline"], text) if enabled else text


def dim(text: str, enabled: Optional[bool] = None) -> str:
    if enabled is None:
        enabled = color_supported()
    return _wrap(COLORS["dim"], text) if enabled else text


def color(text: str, color_name: str, enabled: Optional[bool] = None) -> str:
    if enabled is None:
        enabled = color_supported()
    code = COLORS.get(color_name)
    if not code or not enabled:
        return text
    return _wrap(code, text)


def colorize_level(text: str, level: str, enabled: Optional[bool] = None) -> str:
    c = LEVEL_COLOR.get(level.lower())
    return color(text, c, enabled=enabled) if c else text
