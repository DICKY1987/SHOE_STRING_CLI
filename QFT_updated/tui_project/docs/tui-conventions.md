# TUI Conventions

This document outlines the conventions and best practices for developing TUI modules and using the host utilities.

## Code Style

### Python Style

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Include docstrings in NumPy style format
- Use `from __future__ import annotations` for forward compatibility

### Imports

```python
from __future__ import annotations

import standard_library_modules
from typing import Type, Hints

from . import relative_imports
from .sibling_module import SpecificClass

__all__ = ["PublicAPI", "ExportedClasses"]
```

### Docstrings

Use NumPy-style docstrings for consistency:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description on one line.

    Longer description providing more details about what the function
    does, its behavior, and any important notes.

    Parameters
    ----------
    param1
        Description of param1.
    param2
        Description of param2.

    Returns
    -------
    bool
        Description of return value.

    Raises
    ------
    ValueError
        When and why this exception is raised.
    """
    pass
```

## Output Conventions

### Color and Formatting

Always use the formatting utilities from `host.formatting`:

```python
from host import formatting

# Use color functions
print(formatting.green("Success message"))
print(formatting.red("Error message"))
print(formatting.yellow("Warning message"))

# Use text styling
print(formatting.bold("Important text"))
print(formatting.dim("Less important text"))

# Colors are automatically disabled when:
# - NO_COLOR environment variable is set
# - Output is not to a TTY
# - TERM=dumb
```

### Messages

Use the messaging utilities from `host.messages`:

```python
from host import messages

# Standard message types
messages.info("Starting operation...")
messages.warn("Configuration file not found, using defaults")
messages.error("Failed to connect to database")
messages.success("Operation completed successfully")
```

Message conventions:
- `info()`: General informational messages
- `warn()`: Warnings that don't prevent operation
- `error()`: Errors that prevent operation
- `success()`: Confirmation of successful completion

### Progress Indicators

For long-running operations, use progress indicators:

```python
from host import progress

# Simple status message
progress.show_status("Loading modules...")

# Progress indicator with context manager
with progress.ProgressIndicator("Processing files") as p:
    # Do work here
    pass  # Automatically shows completion

# Spinner for indeterminate operations
spinner = progress.Spinner("Connecting to server")
spinner.start()
try:
    # Do work here
    spinner.stop(formatting.green("✓ Connected"))
except Exception:
    spinner.stop(formatting.red("✗ Failed"))
```

## Help System

### Registering Help Topics

All commands and features should register help content:

```python
from host.help_registry import HelpTopic, get_global_registry

# Register a help topic
registry = get_global_registry()
topic = HelpTopic(
    title="My Command",
    description="Description of what this command does.",
    examples=[
        "$ my-command --option value",
        "$ my-command --help",
    ],
    subtopics=["my-command.advanced", "my-command.config"]
)
registry.register("my-command", topic)
```

### Help Topic Naming

Use hierarchical naming with dots:
- Top-level commands: `command-name`
- Subcommands: `command-name.subcommand`
- Topics: `topic.subtopic.detail`

## CLI Parsing

### Using the CLI Parser

```python
from host.cli_parser import CLIParser

parser = CLIParser(
    prog="my-command",
    description="Description of the command"
)

parser.add_argument("input", help="Input file path")
parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
parser.add_argument("--output", "-o", help="Output file path")

args = parser.parse_args()

# Access parsed arguments
input_file = args.input
verbose = args.verbose
output_file = args.get("output", "default.out")
```

### Argument Naming

- Use lowercase with hyphens for flags: `--my-flag`
- Provide short versions for common options: `-v` for `--verbose`
- Use descriptive names that indicate purpose
- Group related options with common prefixes

## Navigation

### Defining Routes

```python
from host.navigation import Route, get_global_navigator

def my_handler():
    """Handle navigation to this route."""
    print("Navigated to my route")

route = Route(
    route_id="main.my-view",
    title="My View",
    handler=my_handler,
    metadata={"icon": "📊", "category": "views"}
)

navigator = get_global_navigator()
navigator.register_route(route)
```

### Navigation Patterns

- Route IDs should be hierarchical: `category.subcategory.view`
- Use navigation history for back/forward functionality
- Call handlers when routes are activated
- Store view state in metadata when needed

## Error Handling

### Exception Messages

Provide clear, actionable error messages:

```python
from host import messages

try:
    result = risky_operation()
except FileNotFoundError as e:
    messages.error(f"Configuration file not found: {e.filename}")
    messages.info("Run 'init' to create default configuration")
    sys.exit(1)
except PermissionError:
    messages.error("Permission denied accessing configuration")
    messages.info("Check file permissions or run with appropriate privileges")
    sys.exit(1)
```

### Error Message Conventions

- State what went wrong clearly
- Provide the specific error details when helpful
- Suggest how to fix the problem
- Use appropriate message type (error vs warning)

## Testing

### Test Structure

```python
"""Tests for my_module functionality."""

from __future__ import annotations

import pathlib
import sys

import pytest

# Add src to path
THIS_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = THIS_DIR.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from host.my_module import my_function


def test_basic_functionality() -> None:
    """Test basic functionality works as expected."""
    result = my_function("input")
    assert result == "expected"


def test_error_handling() -> None:
    """Test that errors are handled correctly."""
    with pytest.raises(ValueError):
        my_function(None)
```

### Test Conventions

- One test file per module: `test_module_name.py`
- Descriptive test names: `test_what_is_being_tested`
- Docstrings explaining what is tested
- Test both success and failure cases
- Use pytest fixtures for common setup
- Mock external dependencies

## Module Manifests

### Manifest Structure

```yaml
# tui.module.yaml
module_id: my_module
semver: "1.0.0"
contract_semver: "1.0.0"
routes:
  - id: main.my-view
    title: My View
    slot: main
keybindings:
  - key: "m"
    command: navigate.my-view
    context: global
```

### Manifest Conventions

- Use kebab-case for IDs
- Include all routes the module provides
- Document keybindings clearly
- Specify semantic versions
- Validate against schema before committing

## Environment Variables

### Supported Variables

- `NO_COLOR`: Disable all color output (respects standard)
- `TERM`: Terminal type (`dumb` disables colors)
- Custom variables should use module prefix: `TUI_MODULE_OPTION`

### Checking Environment

```python
import os

# Check for NO_COLOR
no_color = bool(os.environ.get("NO_COLOR"))

# Check for custom options
custom_option = os.environ.get("TUI_MY_MODULE_OPTION", "default")
```

## File Operations

### Path Handling

Always use `pathlib` for path operations:

```python
from pathlib import Path

# Construct paths safely
config_dir = Path.home() / ".config" / "my_app"
config_file = config_dir / "config.yaml"

# Check existence
if config_file.exists():
    # Read file
    with config_file.open("r", encoding="utf-8") as f:
        content = f.read()

# Create directories
config_dir.mkdir(parents=True, exist_ok=True)
```

### File Conventions

- Use UTF-8 encoding for all text files
- Close files properly (use context managers)
- Handle missing files gracefully
- Validate file contents after reading

## Performance

### Optimization Guidelines

- Import modules only when needed (lazy imports)
- Cache expensive computations
- Use generators for large datasets
- Profile before optimizing
- Document performance characteristics

### Performance Testing

Include performance tests for critical paths:

```python
import time

def test_large_dataset_performance():
    """Ensure processing large datasets completes in reasonable time."""
    start = time.time()
    process_large_dataset()
    elapsed = time.time() - start
    assert elapsed < 1.0, f"Processing took too long: {elapsed:.2f}s"
```

## Versioning

### Semantic Versioning

- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes

### Compatibility

- Host utilities maintain backwards compatibility within major versions
- Modules specify required host version in manifest
- Breaking changes require major version bumps
