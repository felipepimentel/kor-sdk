"""
Command Loader

Loads slash commands from markdown files with YAML frontmatter.
"""

from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .registry import CommandRegistry
    from . import Command
import logging

logger = logging.getLogger(__name__)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.
    
    Args:
        content: Raw markdown file content
        
    Returns:
        Tuple of (frontmatter_dict, remaining_content)
    """
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                frontmatter = yaml.safe_load(parts[1]) or {}
            except ImportError:
                # Fallback to simple parsing if pyyaml not installed
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        value = value.strip()
                        # Handle list syntax [item1, item2]
                        if value.startswith("[") and value.endswith("]"):
                            value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]
                        frontmatter[key.strip()] = value
            except Exception as e:
                logger.warning(f"Failed to parse YAML frontmatter: {e}")
            body = parts[2].strip()
    
    return frontmatter, body


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
    
    def __init__(self, registry: Optional["CommandRegistry"] = None):
        """
        Initialize the CommandLoader.
        
        Args:
            registry: Optional CommandRegistry to auto-register loaded commands
        """
        from .registry import CommandRegistry
        self.registry = registry or CommandRegistry()
    
    def load_directory(self, directory: Path) -> List["Command"]:
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
    
    def load_file(self, file_path: Path) -> Optional["Command"]:
        """
        Load a single command from a markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Command object or None if loading failed
        """
        from . import Command
        
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
    
    def load_from_config_dir(self) -> List["Command"]:
        """Load commands from ~/.kor/commands/"""
        commands_dir = Path.home() / ".kor" / "commands"
        return self.load_directory(commands_dir)
