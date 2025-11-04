"""Command-line argument parser for TUI applications.

This module provides a CLI parser that integrates with the help registry
and provides consistent argument parsing across the TUI system. It uses
the standard library argparse module as a foundation.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Optional, Sequence

from . import formatting
from .help_registry import get_global_registry

__all__ = [
    "CLIParser",
    "ParsedArgs",
    "create_parser",
]


class ParsedArgs:
    """Container for parsed command-line arguments.

    This class wraps the argparse.Namespace and provides convenient
    access to parsed arguments with type safety.
    """

    def __init__(self, namespace: argparse.Namespace) -> None:
        """Initialize from an argparse Namespace.

        Parameters
        ----------
        namespace
            The argparse Namespace containing parsed arguments.
        """
        self._namespace = namespace

    def get(self, key: str, default: Any = None) -> Any:
        """Get an argument value.

        Parameters
        ----------
        key
            The argument name.
        default
            Default value if the argument is not present.

        Returns
        -------
        Any
            The argument value or default.
        """
        return getattr(self._namespace, key, default)

    def has(self, key: str) -> bool:
        """Check if an argument is present.

        Parameters
        ----------
        key
            The argument name.

        Returns
        -------
        bool
            True if the argument is present.
        """
        return hasattr(self._namespace, key)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary of argument names to values.
        """
        return vars(self._namespace)

    def __getattr__(self, name: str) -> Any:
        """Allow attribute access to arguments."""
        return getattr(self._namespace, name)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ParsedArgs({self.to_dict()})"


class CLIParser:
    """Command-line parser with help registry integration.

    This parser extends argparse functionality with integration to the
    help registry and consistent formatting.
    """

    def __init__(
        self,
        prog: Optional[str] = None,
        description: Optional[str] = None,
        epilog: Optional[str] = None,
        add_help: bool = True,
    ) -> None:
        """Initialize the CLI parser.

        Parameters
        ----------
        prog
            Program name (defaults to sys.argv[0]).
        description
            Program description.
        epilog
            Text to display after the argument help.
        add_help
            Whether to add a -h/--help option.
        """
        self.parser = argparse.ArgumentParser(
            prog=prog,
            description=description,
            epilog=epilog,
            add_help=add_help,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._help_registry = get_global_registry()

    def add_argument(self, *args, **kwargs) -> None:
        """Add an argument to the parser.

        This is a pass-through to argparse.ArgumentParser.add_argument.
        See argparse documentation for argument details.
        """
        self.parser.add_argument(*args, **kwargs)

    def add_subparsers(self, **kwargs) -> argparse._SubParsersAction:
        """Add subparsers for subcommands.

        This is a pass-through to argparse.ArgumentParser.add_subparsers.
        See argparse documentation for argument details.

        Returns
        -------
        argparse._SubParsersAction
            The subparsers action.
        """
        return self.parser.add_subparsers(**kwargs)

    def parse_args(
        self, args: Optional[Sequence[str]] = None
    ) -> ParsedArgs:
        """Parse command-line arguments.

        Parameters
        ----------
        args
            List of argument strings. If None, uses sys.argv[1:].

        Returns
        -------
        ParsedArgs
            Parsed arguments container.
        """
        namespace = self.parser.parse_args(args)
        return ParsedArgs(namespace)

    def print_help(self) -> None:
        """Print help message."""
        self.parser.print_help()

    def error(self, message: str) -> None:
        """Print error message and exit.

        Parameters
        ----------
        message
            Error message to print.
        """
        self.parser.error(message)


def create_parser(
    prog: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> CLIParser:
    """Create a CLI parser with common defaults.

    This is a convenience function that creates a parser with
    standard configuration.

    Parameters
    ----------
    prog
        Program name.
    description
        Program description.
    **kwargs
        Additional arguments to pass to CLIParser.

    Returns
    -------
    CLIParser
        Configured CLI parser.
    """
    return CLIParser(prog=prog, description=description, **kwargs)
