"""
KOR Core SDK

The foundational package for building AI agents with the KOR framework.
"""

from .api import (
    Kernel,
    ConfigManager,
    KorConfig,
    KorPlugin,
    KorContext,
    ServiceRegistry,
    PluginLoader,
    GraphRunner,
    AgentState,
    KorTool,
    TerminalTool,
    BrowserTool,
    MCPClient,
    MCPManager,
    HookManager,
    HookEvent,
)

from .tools.decorators import tool

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
    "tool",
    
    # MCP
    "MCPClient",
    "MCPManager",
    
    # Events
    "HookManager",
    "HookEvent",
]

__version__ = "0.1.0"
