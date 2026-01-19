"""
LSP Config Loader

Loads Language Server Protocol configurations from .lsp.json files.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LSPServerConfig:
    """
    Configuration for a Language Server.
    
    Attributes:
        name: Identifier for the server (usually the language name)
        command: Command to start the server
        args: Arguments for the command
        extension_to_language: Mapping of file extensions to language IDs
        root_uri: Optional workspace root URI
        initialization_options: Optional LSP initialization options
    """
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    extension_to_language: Dict[str, str] = field(default_factory=dict)
    root_uri: Optional[str] = None
    initialization_options: Dict[str, Any] = field(default_factory=dict)
    
    def get_language_for_file(self, file_path: Path) -> Optional[str]:
        """
        Get the language ID for a given file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language ID or None if not matched
        """
        suffix = file_path.suffix.lower()
        return self.extension_to_language.get(suffix)


class LSPConfigLoader:
    """
    Loads LSP server configurations from .lsp.json files.
    
    Expected format:
    ```json
    {
      "python": {
        "command": "pylsp",
        "args": [],
        "extensionToLanguage": {".py": "python", ".pyi": "python"}
      },
      "typescript": {
        "command": "typescript-language-server",
        "args": ["--stdio"],
        "extensionToLanguage": {".ts": "typescript", ".tsx": "typescriptreact"}
      }
    }
    ```
    """
    
    def __init__(self):
        """Initialize the LSPConfigLoader."""
        self._configs: Dict[str, LSPServerConfig] = {}
    
    def load_file(self, config_path: Path) -> Dict[str, LSPServerConfig]:
        """
        Load LSP configurations from a .lsp.json file.
        
        Args:
            config_path: Path to the .lsp.json file
            
        Returns:
            Dictionary mapping language names to configurations
        """
        if not config_path.exists():
            logger.debug(f"LSP config file does not exist: {config_path}")
            return {}
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in LSP config {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load LSP config {config_path}: {e}")
            return {}
        
        loaded = {}
        
        for lang_name, lang_data in data.items():
            try:
                # Support both camelCase and snake_case for compatibility
                ext_map = lang_data.get("extensionToLanguage", 
                                        lang_data.get("extension_to_language", {}))
                init_opts = lang_data.get("initializationOptions",
                                          lang_data.get("initialization_options", {}))
                
                config = LSPServerConfig(
                    name=lang_name,
                    command=lang_data.get("command", ""),
                    args=lang_data.get("args", []),
                    extension_to_language=ext_map,
                    root_uri=lang_data.get("rootUri", lang_data.get("root_uri")),
                    initialization_options=init_opts
                )
                loaded[lang_name] = config
                self._configs[lang_name] = config
                logger.info(f"Loaded LSP server config: {lang_name}")
            except Exception as e:
                logger.error(f"Failed to parse LSP config '{lang_name}': {e}")
        
        return loaded
    
    def get_config(self, name: str) -> Optional[LSPServerConfig]:
        """Get a specific language server configuration."""
        return self._configs.get(name)
    
    def get_all(self) -> List[LSPServerConfig]:
        """Get all loaded configurations."""
        return list(self._configs.values())
    
    def get_config_for_file(self, file_path: Path) -> Optional[LSPServerConfig]:
        """
        Find the appropriate LSP config for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            LSPServerConfig or None if no matching config found
        """
        suffix = file_path.suffix.lower()
        
        for config in self._configs.values():
            if suffix in config.extension_to_language:
                return config
        
        return None
