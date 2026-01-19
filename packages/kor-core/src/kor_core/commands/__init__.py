"""
Commands Module

Provides support for markdown-based slash commands that can be loaded 
from plugin directories without any Python code.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

@dataclass
class Command:
    """
    Represents a slash command loaded from a markdown file.
    
    Commands are defined in markdown with YAML frontmatter for metadata.
    The content provides instructions or templates for the command.
    
    Attributes:
        name: Unique command name (e.g., 'deploy', 'review')
        description: Human-readable description of what the command does
        content: Markdown content with instructions/templates
        args: List of expected argument names
        tags: Optional tags for categorization
        source_path: Path to the source markdown file
    """
    name: str
    description: str
    content: str
    args: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None
    
    @property
    def searchable_text(self) -> str:
        """Combined text for search indexing."""
        return f"{self.name} {self.description} {' '.join(self.tags)}"


from .loader import CommandLoader
from .registry import CommandRegistry

__all__ = ["Command", "CommandLoader", "CommandRegistry"]
