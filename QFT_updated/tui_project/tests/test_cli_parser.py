"""Tests for CLI parser functionality."""

from __future__ import annotations

import pathlib
import sys

import pytest

# Append the src directory to the Python path so that host modules can be imported.
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from host.cli_parser import CLIParser, ParsedArgs, create_parser


def test_basic_argument_parsing() -> None:
    """Test parsing basic command-line arguments."""
    parser = CLIParser(prog="test")
    parser.add_argument("input", help="Input file")
    parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args(["input.txt", "--output", "output.txt"])
    
    assert args.input == "input.txt"
    assert args.output == "output.txt"


def test_parsed_args_get_method() -> None:
    """Test ParsedArgs.get() method with defaults."""
    parser = CLIParser(prog="test")
    parser.add_argument("--flag", action="store_true")
    
    args = parser.parse_args([])
    
    assert args.get("flag") is False
    assert args.get("nonexistent", "default") == "default"


def test_parsed_args_has_method() -> None:
    """Test ParsedArgs.has() method."""
    parser = CLIParser(prog="test")
    parser.add_argument("--flag", action="store_true")
    
    args = parser.parse_args(["--flag"])
    
    assert args.has("flag") is True
    assert args.has("nonexistent") is False


def test_parsed_args_to_dict() -> None:
    """Test converting ParsedArgs to dictionary."""
    parser = CLIParser(prog="test")
    parser.add_argument("input")
    parser.add_argument("--output", default="default.txt")
    
    args = parser.parse_args(["input.txt"])
    args_dict = args.to_dict()
    
    assert isinstance(args_dict, dict)
    assert args_dict["input"] == "input.txt"
    assert args_dict["output"] == "default.txt"


def test_boolean_flag() -> None:
    """Test parsing boolean flags."""
    parser = CLIParser(prog="test")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args_with_flag = parser.parse_args(["--verbose"])
    assert args_with_flag.verbose is True
    
    args_without_flag = parser.parse_args([])
    assert args_without_flag.verbose is False


def test_multiple_values() -> None:
    """Test parsing arguments with multiple values."""
    parser = CLIParser(prog="test")
    parser.add_argument("files", nargs="+", help="Input files")
    
    args = parser.parse_args(["file1.txt", "file2.txt", "file3.txt"])
    
    assert len(args.files) == 3
    assert "file1.txt" in args.files
    assert "file2.txt" in args.files


def test_choices() -> None:
    """Test parsing arguments with limited choices."""
    parser = CLIParser(prog="test")
    parser.add_argument("--level", choices=["debug", "info", "warning", "error"])
    
    args = parser.parse_args(["--level", "info"])
    assert args.level == "info"


def test_invalid_choice_raises_error() -> None:
    """Test that invalid choice causes SystemExit."""
    parser = CLIParser(prog="test")
    parser.add_argument("--level", choices=["debug", "info"])
    
    with pytest.raises(SystemExit):
        parser.parse_args(["--level", "invalid"])


def test_required_argument() -> None:
    """Test that missing required argument causes SystemExit."""
    parser = CLIParser(prog="test")
    parser.add_argument("required_arg", help="Required argument")
    
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_optional_with_default() -> None:
    """Test optional argument with default value."""
    parser = CLIParser(prog="test")
    parser.add_argument("--output", default="default.txt")
    
    args = parser.parse_args([])
    assert args.output == "default.txt"


def test_type_conversion() -> None:
    """Test automatic type conversion."""
    parser = CLIParser(prog="test")
    parser.add_argument("--count", type=int, default=0)
    
    args = parser.parse_args(["--count", "42"])
    assert args.count == 42
    assert isinstance(args.count, int)


def test_subparsers() -> None:
    """Test subparser functionality."""
    parser = CLIParser(prog="test")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add 'init' subcommand
    init_parser = subparsers.add_parser("init", help="Initialize")
    init_parser.add_argument("--force", action="store_true")
    
    # Add 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run")
    run_parser.add_argument("target")
    
    # Test init subcommand
    args_init = parser.parse_args(["init", "--force"])
    assert args_init.command == "init"
    assert args_init.force is True
    
    # Test run subcommand
    args_run = parser.parse_args(["run", "mytarget"])
    assert args_run.command == "run"
    assert args_run.target == "mytarget"


def test_create_parser_convenience() -> None:
    """Test the create_parser convenience function."""
    parser = create_parser(prog="myapp", description="My application")
    parser.add_argument("--version", action="store_true")
    
    args = parser.parse_args(["--version"])
    assert args.version is True


def test_parsed_args_repr() -> None:
    """Test string representation of ParsedArgs."""
    parser = CLIParser(prog="test")
    parser.add_argument("input")
    
    args = parser.parse_args(["test.txt"])
    repr_str = repr(args)
    
    assert "ParsedArgs" in repr_str
    assert "input" in repr_str


def test_short_and_long_flags() -> None:
    """Test both short and long flag variants."""
    parser = CLIParser(prog="test")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--output", "-o")
    
    # Test long flags
    args_long = parser.parse_args(["--verbose", "--output", "out.txt"])
    assert args_long.verbose is True
    assert args_long.output == "out.txt"
    
    # Test short flags
    args_short = parser.parse_args(["-v", "-o", "out.txt"])
    assert args_short.verbose is True
    assert args_short.output == "out.txt"


def test_parser_with_description() -> None:
    """Test that parser description is set correctly."""
    description = "This is a test application"
    parser = CLIParser(prog="test", description=description)
    
    # The description should be stored in the parser
    assert parser.parser.description == description


def test_attribute_access() -> None:
    """Test attribute-style access to parsed arguments."""
    parser = CLIParser(prog="test")
    parser.add_argument("--name", default="test")
    
    args = parser.parse_args([])
    
    # Both attribute and get() should work
    assert args.name == "test"
    assert args.get("name") == "test"
