"""
MCP Config Loader

Loads MCP server configurations from .mcp.json files.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """
    Configuration for a single MCP server.
    
    Attributes:
        name: Unique identifier for the server
        command: Command to start the server (e.g., 'npx')
        args: Arguments for the command
        env: Environment variables to set
        auto_start: Whether to start automatically on kernel boot
    """
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    auto_start: bool = True
    
    def get_resolved_env(self) -> Dict[str, str]:
        """
        Resolve environment variable references like ${VAR_NAME}.
        
        Returns:
            Dictionary with resolved environment variables
        """
        resolved = {}
        for key, value in self.env.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = os.environ.get(var_name, "")
            else:
                resolved[key] = value
        return resolved


class MCPConfigLoader:
    """
    Loads MCP server configurations from .mcp.json files.
    
    Expected format:
    ```json
    {
      "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
        "auto_start": true
      },
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
      }
    }
    ```
    """
    
    def __init__(self):
        """Initialize the MCPConfigLoader."""
        self._configs: Dict[str, MCPServerConfig] = {}
    
    def load_file(self, config_path: Path) -> Dict[str, MCPServerConfig]:
        """
        Load MCP configurations from a .mcp.json file.
        
        Args:
            config_path: Path to the .mcp.json file
            
        Returns:
            Dictionary mapping server names to configurations
        """
        if not config_path.exists():
            logger.debug(f"MCP config file does not exist: {config_path}")
            return {}
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in MCP config {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load MCP config {config_path}: {e}")
            return {}
        
        loaded = {}
        
        for server_name, server_data in data.items():
            try:
                config = MCPServerConfig(
                    name=server_name,
                    command=server_data.get("command", ""),
                    args=server_data.get("args", []),
                    env=server_data.get("env", {}),
                    auto_start=server_data.get("auto_start", True)
                )
                loaded[server_name] = config
                self._configs[server_name] = config
                logger.info(f"Loaded MCP server config: {server_name}")
            except Exception as e:
                logger.error(f"Failed to parse MCP server config '{server_name}': {e}")
        
        return loaded
    
    def get_config(self, name: str) -> Optional[MCPServerConfig]:
        """Get a specific server configuration."""
        return self._configs.get(name)
    
    def get_all(self) -> List[MCPServerConfig]:
        """Get all loaded server configurations."""
        return list(self._configs.values())
    
    def get_auto_start_configs(self) -> List[MCPServerConfig]:
        """Get configurations for servers that should auto-start."""
        return [c for c in self._configs.values() if c.auto_start]
