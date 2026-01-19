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
    ToolRegistry,
    ToolInfo,
    MCPClient,
    MCPManager,
    HookManager,
    HookEvent,
    # Exceptions
    KorError,
    ConfigurationError,
    PluginError,
    PluginLoadError,
    PluginInitError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    AgentError,
    LLMError,
    PermissionDeniedError,
)

from .tools.decorators import tool
from .kernel import get_kernel, set_kernel, reset_kernel

__all__ = [
    # Core
    "Kernel",
    "ConfigManager",
    "KorConfig",
    "get_kernel",
    "set_kernel",
    "reset_kernel",
    
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
    "ToolRegistry",
    "ToolInfo",
    "tool",
    
    # MCP
    "MCPClient",
    "MCPManager",
    
    # Events
    "HookManager",
    "HookEvent",
    
    # Exceptions
    "KorError",
    "ConfigurationError",
    "PluginError",
    "PluginLoadError",
    "PluginInitError",
    "ToolError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "AgentError",
    "LLMError",
    "PermissionDeniedError",
]

__version__ = "0.1.0"

