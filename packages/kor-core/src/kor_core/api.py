"""
KOR SDK - Public API

This module defines the official public interface for the KOR SDK.
All classes and functions exported here are considered stable and documented.
"""

from .kernel import Kernel
from .config import ConfigManager, KorConfig
from .plugin import KorPlugin, KorContext, ServiceRegistry
from .loader import PluginLoader
from .agent.runner import GraphRunner
from .agent.state import AgentState
from .tools import TerminalTool, BrowserTool, KorTool
from .mcp import MCPClient, MCPManager
from .events import HookManager, HookEvent

__all__ = [
    # Core
    "Kernel",
    "ConfigManager",
    "KorConfig",
    
    # Plugins
    "KorPlugin",
    "KorContext",
    "ServiceRegistry",
    "PluginLoader",
    
    # Agent
    "GraphRunner",
    "AgentState",
    
    # Tools
    "KorTool",
    "TerminalTool",
    "BrowserTool",
    
    # MCP
    "MCPClient",
    "MCPManager",
    
    # Events
    "HookManager",
    "HookEvent",
]
