"""
Commands Module - Slash Commands for KOR SDK

Provides support for markdown-based slash commands that can be loaded 
from plugin directories without any Python code.

Includes:
- Command dataclass
- CommandLoader for loading from filesystem
- CommandRegistry for registration and search
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .utils import parse_frontmatter

logger = logging.getLogger(__name__)


# =============================================================================
# Command Dataclass
# =============================================================================

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


# =============================================================================
# Command Registry
# =============================================================================

class CommandRegistry:
    """
    Central registry for slash commands.
    
    Provides command registration, lookup, and search functionality.
    """
    
    def __init__(self):
        """Initialize the CommandRegistry."""
        self._commands: Dict[str, Command] = {}
    
    def register(self, command: Command) -> None:
        """
        Register a command.
        
        Args:
            command: The Command object to register
        """
        if command.name in self._commands:
            logger.warning(f"Command '{command.name}' already registered. Overwriting.")
        self._commands[command.name] = command
        logger.debug(f"Registered command: /{command.name}")
    
    def get(self, name: str) -> Optional[Command]:
        """
        Get a command by name.
        
        Args:
            name: Command name (without leading slash)
            
        Returns:
            Command object or None if not found
        """
        # Remove leading slash if present
        name = name.lstrip("/")
        return self._commands.get(name)
    
    def get_all(self) -> List[Command]:
        """Get all registered commands."""
        return list(self._commands.values())
    
    def search(self, query: str, top_k: int = 5) -> List[Command]:
        """
        Search commands by name or description.
        
        Args:
            query: Search query
            top_k: Maximum number of results
            
        Returns:
            List of matching Command objects
        """
        query_lower = query.lower()
        results = []
        
        for command in self._commands.values():
            score = 0
            # Exact name match
            if command.name.lower() == query_lower:
                score = 100
            # Name contains query
            elif query_lower in command.name.lower():
                score = 50
            # Description contains query
            elif query_lower in command.description.lower():
                score = 25
            # Tags contain query
            elif any(query_lower in tag.lower() for tag in command.tags):
                score = 10
            
            if score > 0:
                results.append((score, command))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [cmd for _, cmd in results[:top_k]]
    
    def format_help(self, command_name: Optional[str] = None) -> str:
        """
        Format help text for commands.
        
        Args:
            command_name: Specific command to show help for, or None for all
            
        Returns:
            Formatted help string
        """
        if command_name:
            cmd = self.get(command_name)
            if not cmd:
                return f"Unknown command: /{command_name}"
            
            lines = [
                f"**/{cmd.name}** - {cmd.description}",
            ]
            if cmd.args:
                lines.append(f"Arguments: {', '.join(cmd.args)}")
            if cmd.tags:
                lines.append(f"Tags: {', '.join(cmd.tags)}")
            if cmd.content:
                lines.append(f"\n{cmd.content}")
            return "\n".join(lines)
        
        # Format all commands
        if not self._commands:
            return "No commands registered."
        
        lines = ["**Available Commands:**\n"]
        for cmd in sorted(self._commands.values(), key=lambda c: c.name):
            lines.append(f"- **/{cmd.name}**: {cmd.description}")
        return "\n".join(lines)
    
    def __len__(self) -> int:
        return len(self._commands)
    
    def __contains__(self, name: str) -> bool:
        return name.lstrip("/") in self._commands


# =============================================================================
# Command Loader
# =============================================================================

class CommandLoader:
    """
    Loads slash commands from filesystem directories.
    
    Expected file format:
    ```markdown
    ---
    name: deploy
    description: Deploy the application
    args: [environment, version]
    tags: [ops, deployment]
    ---
    
    ## Instructions
    
    1. Build the project
    2. Push to registry
    3. Notify team
    ```
    """
    
    def __init__(self, registry: Optional[CommandRegistry] = None):
        """
        Initialize the CommandLoader.
        
        Args:
            registry: Optional CommandRegistry to auto-register loaded commands
        """
        self.registry = registry or CommandRegistry()
    
    def load_directory(self, directory: Path) -> List[Command]:
        """
        Load all .md commands from a directory.
        
        Args:
            directory: Path to the commands directory
            
        Returns:
            List of loaded Command objects
        """
        loaded = []
        
        if not directory.exists():
            logger.debug(f"Commands directory does not exist: {directory}")
            return loaded
        
        for file_path in directory.glob("*.md"):
            try:
                command = self.load_file(file_path)
                if command:
                    self.registry.register(command)
                    loaded.append(command)
                    logger.info(f"Loaded command: /{command.name}")
            except Exception as e:
                logger.error(f"Failed to load command from {file_path}: {e}")
        
        return loaded
    
    def load_file(self, file_path: Path) -> Optional[Command]:
        """
        Load a single command from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Command object or None if loading failed
        """
        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)
        
        name = frontmatter.get("name", file_path.stem)
        description = frontmatter.get("description", "")
        args = frontmatter.get("args", [])
        tags = frontmatter.get("tags", [])
        
        # Normalize args and tags to lists
        if isinstance(args, str):
            args = [a.strip() for a in args.split(",")]
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        
        return Command(
            name=name,
            description=description,
            content=body,
            args=args,
            tags=tags,
            source_path=file_path
        )
    
    def load_from_config_dir(self) -> List[Command]:
        """Load commands from ~/.kor/commands/"""
        commands_dir = Path.home() / ".kor" / "commands"
        return self.load_directory(commands_dir)


__all__ = ["Command", "CommandLoader", "CommandRegistry", "parse_frontmatter"]
