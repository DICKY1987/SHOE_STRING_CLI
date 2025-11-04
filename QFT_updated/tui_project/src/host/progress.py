"""Progress indicator utilities.

This module provides utilities for displaying progress indicators and status
updates during long-running operations. It supports both simple status messages
and animated progress indicators that respect TTY detection.
"""

from __future__ import annotations

import sys
import time
from typing import Optional, TextIO

from . import formatting

__all__ = [
    "ProgressIndicator",
    "Spinner",
    "show_status",
]


def show_status(message: str, file: Optional[TextIO] = None) -> None:
    """Display a status message.

    Parameters
    ----------
    message
        The status message to display.
    file
        Optional file object to write to. Defaults to stdout.
    """
    if file is None:
        file = sys.stdout
    print(formatting.dim(f"⏳ {message}"), file=file, flush=True)


class ProgressIndicator:
    """Base class for progress indicators.

    This class provides common functionality for progress indicators including
    TTY detection and output management.
    """

    def __init__(self, message: str = "", file: Optional[TextIO] = None) -> None:
        """Initialize the progress indicator.

        Parameters
        ----------
        message
            Optional message to display with the indicator.
        file
            Optional file object to write to. Defaults to stdout.
        """
        self.message = message
        self.file = file or sys.stdout
        self.active = False
        self._supports_tty = self.file.isatty()

    def start(self) -> None:
        """Start the progress indicator."""
        self.active = True
        if self._supports_tty:
            self._write(f"{self.message}...")
        else:
            self._write(f"{self.message}...\n")

    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop the progress indicator.

        Parameters
        ----------
        final_message
            Optional message to display when stopping.
        """
        self.active = False
        if final_message:
            if self._supports_tty:
                self._write(f"\r{final_message}\n")
            else:
                self._write(f"{final_message}\n")
        elif self._supports_tty:
            self._write("\n")

    def _write(self, text: str) -> None:
        """Write text to the output file.

        Parameters
        ----------
        text
            The text to write.
        """
        self.file.write(text)
        self.file.flush()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.stop(formatting.green("✓ Done"))
        else:
            self.stop(formatting.red("✗ Failed"))
        return False


class Spinner(ProgressIndicator):
    """Animated spinner progress indicator.

    This class provides a simple animated spinner that cycles through
    a set of frames. The spinner only animates when output is to a TTY.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "", file: Optional[TextIO] = None) -> None:
        """Initialize the spinner.

        Parameters
        ----------
        message
            Optional message to display with the spinner.
        file
            Optional file object to write to. Defaults to stdout.
        """
        super().__init__(message, file)
        self._frame_index = 0

    def update(self) -> None:
        """Update the spinner to the next frame.

        This method should be called periodically during a long operation
        to animate the spinner. It has no effect if output is not to a TTY.
        """
        if not self.active or not self._supports_tty:
            return

        frame = self.FRAMES[self._frame_index]
        self._frame_index = (self._frame_index + 1) % len(self.FRAMES)

        # Move cursor to start of line and redraw
        self._write(f"\r{formatting.cyan(frame)} {self.message}...")

    def spin_for(self, duration: float, update_interval: float = 0.1) -> None:
        """Spin for a specific duration.

        This is a convenience method for testing or simple operations.

        Parameters
        ----------
        duration
            How long to spin in seconds.
        update_interval
            How often to update the spinner in seconds.
        """
        if not self.active:
            self.start()

        end_time = time.time() + duration
        while time.time() < end_time:
            self.update()
            time.sleep(update_interval)
