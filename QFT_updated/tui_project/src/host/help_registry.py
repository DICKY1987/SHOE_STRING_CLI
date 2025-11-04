"""Help system registry for TUI commands and modules.

This module provides a centralized registry for help content, allowing
commands and modules to register their help text and making it available
for retrieval and rendering. The registry supports hierarchical help topics
and can generate formatted help output.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from . import formatting

__all__ = [
    "HelpRegistry",
    "HelpTopic",
]


class HelpTopic:
    """A help topic with title, description, and optional examples.

    Attributes
    ----------
    title : str
        The title of the help topic.
    description : str
        A description of the topic.
    examples : List[str]
        Optional list of example usages.
    subtopics : List[str]
        Optional list of subtopic identifiers.
    """

    def __init__(
        self,
        title: str,
        description: str,
        examples: Optional[List[str]] = None,
        subtopics: Optional[List[str]] = None,
    ) -> None:
        """Initialize a help topic.

        Parameters
        ----------
        title
            The title of the help topic.
        description
            A description of the topic.
        examples
            Optional list of example usages.
        subtopics
            Optional list of subtopic identifiers.
        """
        self.title = title
        self.description = description
        self.examples = examples or []
        self.subtopics = subtopics or []

    def render(self, indent: int = 0) -> str:
        """Render the help topic as formatted text.

        Parameters
        ----------
        indent
            Number of spaces to indent the output.

        Returns
        -------
        str
            The formatted help text.
        """
        prefix = " " * indent
        lines = [
            f"{prefix}{formatting.bold(self.title)}",
            f"{prefix}{self.description}",
        ]

        if self.examples:
            lines.append(f"{prefix}")
            lines.append(f"{prefix}{formatting.bold('Examples:')}")
            for example in self.examples:
                lines.append(f"{prefix}  {formatting.dim(example)}")

        if self.subtopics:
            lines.append(f"{prefix}")
            lines.append(f"{prefix}{formatting.bold('Subtopics:')}")
            for subtopic in self.subtopics:
                lines.append(f"{prefix}  {subtopic}")

        return "\n".join(lines)


class HelpRegistry:
    """Registry for help topics.

    This class maintains a mapping of topic identifiers to HelpTopic instances
    and provides methods for registering, retrieving, and rendering help content.
    """

    def __init__(self) -> None:
        """Initialize an empty help registry."""
        self._topics: Dict[str, HelpTopic] = {}

    def register(self, topic_id: str, topic: HelpTopic) -> None:
        """Register a help topic.

        Parameters
        ----------
        topic_id
            Unique identifier for the topic (e.g., "commands.init").
        topic
            The HelpTopic instance to register.

        Raises
        ------
        ValueError
            If a topic with the given ID is already registered.
        """
        if topic_id in self._topics:
            raise ValueError(f"Help topic '{topic_id}' is already registered")
        self._topics[topic_id] = topic

    def get(self, topic_id: str) -> Optional[HelpTopic]:
        """Retrieve a help topic by ID.

        Parameters
        ----------
        topic_id
            The identifier of the topic to retrieve.

        Returns
        -------
        Optional[HelpTopic]
            The help topic if found, None otherwise.
        """
        return self._topics.get(topic_id)

    def list_topics(self, prefix: Optional[str] = None) -> List[str]:
        """List all registered topic IDs.

        Parameters
        ----------
        prefix
            Optional prefix to filter topics by.

        Returns
        -------
        List[str]
            List of topic IDs, optionally filtered by prefix.
        """
        if prefix:
            return [tid for tid in self._topics.keys() if tid.startswith(prefix)]
        return list(self._topics.keys())

    def render(self, topic_id: str) -> str:
        """Render a help topic as formatted text.

        Parameters
        ----------
        topic_id
            The identifier of the topic to render.

        Returns
        -------
        str
            The formatted help text.

        Raises
        ------
        KeyError
            If the topic is not found.
        """
        topic = self._topics.get(topic_id)
        if topic is None:
            raise KeyError(f"Help topic '{topic_id}' not found")
        return topic.render()

    def render_all(self, prefix: Optional[str] = None) -> str:
        """Render all help topics as formatted text.

        Parameters
        ----------
        prefix
            Optional prefix to filter topics by.

        Returns
        -------
        str
            The formatted help text for all matching topics.
        """
        topic_ids = self.list_topics(prefix)
        if not topic_ids:
            return "No help topics found."

        lines = []
        for topic_id in sorted(topic_ids):
            topic = self._topics[topic_id]
            lines.append(topic.render())
            lines.append("")  # Blank line between topics

        return "\n".join(lines)


# Global registry instance
_global_registry: Optional[HelpRegistry] = None


def get_global_registry() -> HelpRegistry:
    """Get the global help registry instance.

    Returns
    -------
    HelpRegistry
        The global help registry.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = HelpRegistry()
    return _global_registry
