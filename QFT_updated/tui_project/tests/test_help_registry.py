"""Tests for help registry functionality."""

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

from host.help_registry import HelpRegistry, HelpTopic


def test_register_and_retrieve_topic() -> None:
    """Test registering and retrieving a help topic."""
    registry = HelpRegistry()
    topic = HelpTopic(
        title="Test Command",
        description="This is a test command.",
        examples=["$ test-command --option value"],
    )
    
    registry.register("test-command", topic)
    retrieved = registry.get("test-command")
    
    assert retrieved is not None
    assert retrieved.title == "Test Command"
    assert retrieved.description == "This is a test command."
    assert len(retrieved.examples) == 1


def test_duplicate_registration_raises_error() -> None:
    """Test that registering a duplicate topic raises ValueError."""
    registry = HelpRegistry()
    topic1 = HelpTopic(title="Command", description="First registration")
    topic2 = HelpTopic(title="Command", description="Second registration")
    
    registry.register("command", topic1)
    
    with pytest.raises(ValueError, match="already registered"):
        registry.register("command", topic2)


def test_get_nonexistent_topic() -> None:
    """Test that getting a non-existent topic returns None."""
    registry = HelpRegistry()
    result = registry.get("nonexistent")
    assert result is None


def test_list_topics() -> None:
    """Test listing all registered topics."""
    registry = HelpRegistry()
    
    topics = [
        ("cmd1", HelpTopic(title="Command 1", description="First")),
        ("cmd2", HelpTopic(title="Command 2", description="Second")),
        ("other.cmd", HelpTopic(title="Other Command", description="Third")),
    ]
    
    for topic_id, topic in topics:
        registry.register(topic_id, topic)
    
    all_topics = registry.list_topics()
    assert len(all_topics) == 3
    assert "cmd1" in all_topics
    assert "cmd2" in all_topics
    assert "other.cmd" in all_topics


def test_list_topics_with_prefix() -> None:
    """Test filtering topics by prefix."""
    registry = HelpRegistry()
    
    registry.register("cmd.foo", HelpTopic(title="Foo", description="Foo desc"))
    registry.register("cmd.bar", HelpTopic(title="Bar", description="Bar desc"))
    registry.register("other.baz", HelpTopic(title="Baz", description="Baz desc"))
    
    cmd_topics = registry.list_topics(prefix="cmd.")
    assert len(cmd_topics) == 2
    assert "cmd.foo" in cmd_topics
    assert "cmd.bar" in cmd_topics
    assert "other.baz" not in cmd_topics


def test_render_topic() -> None:
    """Test rendering a help topic to text."""
    registry = HelpRegistry()
    topic = HelpTopic(
        title="Test Command",
        description="This is a test command that does testing.",
        examples=["$ test --flag", "$ test input.txt"],
        subtopics=["test.advanced", "test.config"],
    )
    registry.register("test", topic)
    
    output = registry.render("test")
    
    assert "Test Command" in output
    assert "This is a test command" in output
    assert "Examples:" in output
    assert "$ test --flag" in output
    assert "Subtopics:" in output
    assert "test.advanced" in output


def test_render_nonexistent_topic_raises_error() -> None:
    """Test that rendering a non-existent topic raises KeyError."""
    registry = HelpRegistry()
    
    with pytest.raises(KeyError, match="not found"):
        registry.render("nonexistent")


def test_render_all_topics() -> None:
    """Test rendering all topics."""
    registry = HelpRegistry()
    
    registry.register("cmd1", HelpTopic(title="Command 1", description="First"))
    registry.register("cmd2", HelpTopic(title="Command 2", description="Second"))
    
    output = registry.render_all()
    
    assert "Command 1" in output
    assert "Command 2" in output


def test_render_all_with_prefix() -> None:
    """Test rendering topics filtered by prefix."""
    registry = HelpRegistry()
    
    registry.register("cmd.foo", HelpTopic(title="Foo", description="Foo desc"))
    registry.register("cmd.bar", HelpTopic(title="Bar", description="Bar desc"))
    registry.register("other.baz", HelpTopic(title="Baz", description="Baz desc"))
    
    output = registry.render_all(prefix="cmd.")
    
    assert "Foo" in output
    assert "Bar" in output
    assert "Baz" not in output


def test_topic_render_with_indent() -> None:
    """Test rendering a topic with indentation."""
    topic = HelpTopic(
        title="Indented Topic",
        description="This should be indented.",
    )
    
    output = topic.render(indent=4)
    lines = output.split("\n")
    
    # Check that lines are indented
    for line in lines:
        if line:  # Skip empty lines
            assert line.startswith("    ")


def test_empty_registry_render_all() -> None:
    """Test rendering all topics when registry is empty."""
    registry = HelpRegistry()
    output = registry.render_all()
    assert "No help topics found" in output
