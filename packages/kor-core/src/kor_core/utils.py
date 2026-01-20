"""
Common Utilities for KOR SDK

Provides shared helper functions used across multiple modules.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Frontmatter Parsing
# =============================================================================

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.
    
    Supports standard markdown frontmatter format:
    ```markdown
    ---
    name: example
    tags: [a, b, c]
    ---
    Body content here
    ```
    
    Args:
        content: Raw markdown file content
        
    Returns:
        Tuple of (frontmatter_dict, body_content)
    
    Example:
        >>> content = '''---
        ... name: example
        ... tags: [a, b]
        ... ---
        ... Body content here
        ... '''
        >>> fm, body = parse_frontmatter(content)
        >>> fm['name']
        'example'
    """
    frontmatter: Dict[str, Any] = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                frontmatter = yaml.safe_load(parts[1]) or {}
            except ImportError:
                # Fallback to simple parsing if PyYAML not installed
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        value = value.strip()
                        # Handle list syntax [item1, item2]
                        if value.startswith("[") and value.endswith("]"):
                            value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]
                        frontmatter[key.strip()] = value
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
            body = parts[2].strip()
    
    return frontmatter, body


def safe_load_yaml(content: str) -> Dict[str, Any]:
    """
    Safely load YAML content with fallback for missing PyYAML.
    
    This centralizes YAML parsing across the SDK, providing a consistent
    fallback mechanism when PyYAML is not installed.
    
    Args:
        content: YAML string to parse
        
    Returns:
        Parsed dictionary (empty dict on failure)
    """
    try:
        import yaml
        return yaml.safe_load(content) or {}
    except ImportError:
        logger.debug("PyYAML not installed, using basic parsing")
        # Basic key: value parsing fallback
        result: Dict[str, Any] = {}
        for line in content.strip().split("\n"):
            if ":" in line and not line.strip().startswith("#"):
                key, value = line.split(":", 1)
                value = value.strip()
                # Handle list syntax [item1, item2]
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip("\"'") for v in value[1:-1].split(",")]
                result[key.strip()] = value
        return result
    except Exception as e:
        logger.warning(f"Failed to parse YAML: {e}")
        return {}


# =============================================================================
# Base Loader (Generic)
# =============================================================================

class BaseLoader(ABC, Generic[T]):
    """
    Base class for filesystem-based resource loaders.
    
    .. warning::
        Deprecated in favor of `kor_core.context` adapters. 
        Will be removed in v1.0.
    
    Provides common pattern for loading resources from markdown/yaml files.
    Subclasses only need to implement load_file() and get_key().
    
    Example:
        ```python
        class CommandLoader(BaseLoader[Command]):
            def load_file(self, file_path: Path) -> Optional[Command]:
                content = file_path.read_text()
                fm, body = parse_frontmatter(content)
                return Command(
                    name=fm.get("name", file_path.stem),
                    description=fm.get("description", ""),
                    content=body
                )
            
            def get_key(self, item: Command) -> str:
                return item.name
        ```
    """
    
    def __init__(self):
        self._loaded: Dict[str, T] = {}
        # import warnings
        # warnings.warn(
        #     f"{self.__class__.__name__} is deprecated. Use ContextManager instead.",
        #     DeprecationWarning,
        #     stacklevel=2
        # )
    
    @property
    def file_patterns(self) -> List[str]:
        """File patterns to search for (default: *.md)."""
        return ["*.md"]
    
    def load_directory(self, directory: Path) -> List[T]:
        """
        Load all resources from a directory.
        
        Args:
            directory: Path to directory containing resource files
            
        Returns:
            List of loaded resources
        """
        loaded = []
        
        if not directory.exists():
            logger.debug(f"Directory does not exist: {directory}")
            return loaded
        
        for pattern in self.file_patterns:
            for file_path in directory.glob(pattern):
                try:
                    item = self.load_file(file_path)
                    if item:
                        key = self.get_key(item)
                        self._loaded[key] = item
                        loaded.append(item)
                        logger.debug(f"Loaded: {key}")
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")
        
        return loaded
    
    @abstractmethod
    def load_file(self, file_path: Path) -> Optional[T]:
        """
        Load a single resource from a file.
        
        Args:
            file_path: Path to the resource file
            
        Returns:
            Loaded resource or None if loading failed
        """
        pass
    
    @abstractmethod
    def get_key(self, item: T) -> str:
        """
        Get unique key for the loaded item.
        
        Args:
            item: The loaded resource
            
        Returns:
            Unique string identifier
        """
        pass
    
    def get(self, key: str) -> Optional[T]:
        """Get a loaded item by key."""
        return self._loaded.get(key)
    
    def get_all(self) -> List[T]:
        """Get all loaded items."""
        return list(self._loaded.values())
    
    def __len__(self) -> int:
        return len(self._loaded)
    
    def __contains__(self, key: str) -> bool:
        return key in self._loaded


__all__ = ["parse_frontmatter", "safe_load_yaml", "BaseLoader"]
