"""
Command Registry

Central registry for slash commands with search functionality.
"""

from typing import List, Dict, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from . import Command

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Central registry for slash commands.
    
    Provides command registration, lookup, and search functionality.
    """
    
    def __init__(self):
        """Initialize the CommandRegistry."""
        self._commands: Dict[str, "Command"] = {}
    
    def register(self, command: "Command") -> None:
        """
        Register a command.
        
        Args:
            command: The Command object to register
        """
        
        if command.name in self._commands:
            logger.warning(f"Command '{command.name}' already registered. Overwriting.")
        self._commands[command.name] = command
        logger.debug(f"Registered command: /{command.name}")
    
    def get(self, name: str) -> Optional["Command"]:
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
    
    def get_all(self) -> List["Command"]:
        """Get all registered commands."""
        return list(self._commands.values())
    
    def search(self, query: str, top_k: int = 5) -> List["Command"]:
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
