"""
KOR Exception Hierarchy

Provides a structured exception system for the KOR SDK.
All custom exceptions inherit from KorError for easy catching.
"""


class KorError(Exception):
    """Base exception for all KOR errors."""
    
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


# Configuration Errors
class ConfigurationError(KorError):
    """Raised when configuration is invalid or missing."""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when a required configuration value is missing."""
    pass


# Plugin Errors
class PluginError(KorError):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    
    def __init__(self, plugin_name: str, reason: str):
        self.plugin_name = plugin_name
        super().__init__(f"Failed to load plugin '{plugin_name}': {reason}")


class PluginInitError(PluginError):
    """Raised when a plugin fails to initialize."""
    
    def __init__(self, plugin_name: str, reason: str):
        self.plugin_name = plugin_name
        super().__init__(f"Failed to initialize plugin '{plugin_name}': {reason}")


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are not satisfied."""
    
    def __init__(self, plugin_name: str, missing_deps: list):
        self.plugin_name = plugin_name
        self.missing_deps = missing_deps
        super().__init__(
            f"Plugin '{plugin_name}' has unsatisfied dependencies: {missing_deps}"
        )


# Tool Errors
class ToolError(KorError):
    """Base exception for tool-related errors."""
    pass


class ToolExecutionError(ToolError):
    """Raised when a tool execution fails."""
    
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' execution failed: {reason}")


class ToolNotFoundError(ToolError):
    """Raised when a requested tool doesn't exist."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool not found: '{tool_name}'")


# Agent Errors
class AgentError(KorError):
    """Base exception for agent-related errors."""
    pass


class AgentNotFoundError(AgentError):
    """Raised when a requested agent doesn't exist."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: '{agent_id}'")


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


# LLM Errors
class LLMError(KorError):
    """Base exception for LLM-related errors."""
    pass


class ProviderNotFoundError(LLMError):
    """Raised when a requested LLM provider is not registered."""
    
    def __init__(self, provider_name: str, available: list = None):
        self.provider_name = provider_name
        self.available = available or []
        msg = f"LLM provider not found: '{provider_name}'"
        if available:
            msg += f". Available: {available}"
        super().__init__(msg)


class ModelNotConfiguredError(LLMError):
    """Raised when no model is configured for a purpose."""
    
    def __init__(self, purpose: str):
        self.purpose = purpose
        super().__init__(
            f"No LLM configured for purpose '{purpose}'. "
            f"Configure [llm.purposes.{purpose}] or [llm.default] in config.toml"
        )


# Permission Errors
class PermissionDeniedError(KorError):
    """Raised when a permission request is denied."""
    
    def __init__(self, action: str, reason: str = None):
        self.action = action
        msg = f"Permission denied for action: '{action}'"
        if reason:
            msg += f". Reason: {reason}"
        super().__init__(msg)
