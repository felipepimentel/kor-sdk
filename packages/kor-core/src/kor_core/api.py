"""
KOR SDK - Public API

This module defines the official public interface for the KOR SDK.
All classes and functions exported here are considered stable and documented.

The primary interface is the `Kor` facade class, which provides a simple,
Pythonic way to interact with the KOR SDK.
"""

from typing import Optional, Any, List, TYPE_CHECKING

from .kernel import Kernel
from .config import ConfigManager, KorConfig
from .plugin import KorPlugin, KorContext, ServiceRegistry, PluginLoader
from .agent.runner import GraphRunner
from .agent.state import AgentState
from .agent.models import AgentDefinition
from .tools import TerminalTool, BrowserTool, KorTool, ToolRegistry, ToolInfo
from .mcp import MCPClient, MCPManager
from .events import HookManager, HookEvent
from .exceptions import (
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

if TYPE_CHECKING:
    from .llm.selector import ModelSelector
    from .skills import SkillRegistry


# =============================================================================
# Kor Facade - Pythonic Interface
# =============================================================================

class Kor:
    """
    The main facade for the KOR SDK.
    
    Provides a simple, fluent interface for common operations:
    
    Example:
        ```python
        from kor_core import Kor
        
        # Simple initialization
        kor = Kor()
        kor.boot()
        
        # Access subsystems intuitively
        kor.tools.register(my_tool)
        kor.hooks.on(HookEvent.ON_BOOT, my_callback)
        model = kor.llm.get_model("gpt-4")
        
        # Run an agent
        result = await kor.run("Analyze this code")
        ```
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        config_options: Optional[dict] = None
    ):
        """
        Initialize the Kor facade.
        
        Args:
            api_key: Optional API key (will be used for the default provider).
            model: Optional model ID (e.g. "openai:gpt-4o") to set as default.
            config_options: Optional dictionary of configuration overrides.
        """
        config_options = config_options or {}
        
        # Zero-Config: Inject simple args into config options
        if api_key:
            # We assume the user wants to set the key for the implied default provider
            # This is a heuristic: if model is "anthropic:...", set anthropic key, etc.
            # But for simple "zero config", we'll set it in secrets.openai (often default) 
            # OR rely on the provider unification logic.
            # To be safe and generic, we set it in `secrets.openai_api_key` as a fallback common case,
            # but a more robust way is needed if we want to support any provider.
            # For now, let's map it to the most likely default based on model name or fallback to openai.
            
            target_secret = "secrets.openai_api_key" # Default assumption
            if model and "claude" in model:
                target_secret = "secrets.anthropic_api_key"
            
            config_options[target_secret] = api_key
            
        if model:
            # parsing "provider:model"
            if ":" in model:
                provider, model_name = model.split(":", 1)
            else:
                provider = "openai" # default
                model_name = model
                
            config_options["llm.default"] = {
                "provider": provider,
                "model": model_name
            }

        self._kernel = Kernel(config_options=config_options)
        self._booted = False
    
    def boot(self) -> "Kor":
        """
        Boot the KOR system.
        
        Initializes the kernel, loads plugins, and prepares all subsystems.
        
        Returns:
            Self for method chaining.
        """
        self._kernel.boot_sync()
        self._booted = True
        return self
    
    async def boot_async(self) -> "Kor":
        """
        Boot the KOR system asynchronously.
        
        Returns:
            Self for method chaining.
        """
        await self._kernel.boot()
        self._booted = True
        return self
    
    @property
    def kernel(self) -> Kernel:
        """Direct access to the kernel for advanced usage."""
        return self._kernel
    
    @property
    def tools(self) -> ToolRegistry:
        """
        Access the tool registry.
        
        Example:
            kor.tools.register(my_tool)
            tool = kor.tools.get("terminal")
            results = kor.tools.search("file operations")
        """
        return self._kernel.registry.get_tool_registry()
    
    @property
    def hooks(self) -> HookManager:
        """
        Access the event/hook manager.
        
        Example:
            kor.hooks.on(HookEvent.ON_BOOT, lambda: print("Booted!"))
            await kor.hooks.emit(HookEvent.ON_BOOT)
        """
        return self._kernel.hooks
    
    @property
    def llm(self) -> "ModelSelector":
        """
        Access the LLM model selector.
        
        Example:
            model = kor.llm.get_model("coding")
            model = kor.llm.get_model(override="openai:gpt-4")
        """
        return self._kernel.model_selector

    @property
    def mcp(self) -> MCPManager:
        """
        Access the Model Context Protocol manager.
        """
        return self._kernel.mcp

    @property
    def plugins(self) -> PluginLoader:
        """
        Access the plugin loader.
        """
        return self._kernel.loader
    
    @property
    def skills(self) -> "SkillRegistry":
        """
        Access the skills registry.
        
        Example:
            skills = kor.skills.search("python testing")
            skill = kor.skills.get("pytest-basics")
        """
        return self._kernel.registry.get_service("skills")
    
    @property
    def is_active(self) -> bool:
        """Check if the kernel is booted and active."""
        return self._booted

    @property
    def agents(self):
        """Access the agent registry."""
        return self._kernel.agent_registry

    @property
    def config(self) -> KorConfig:
        """Access the current configuration."""
        return self._kernel.config
    
    @property
    def registry(self) -> ServiceRegistry:
        """Access the service registry for advanced usage."""
        return self._kernel.registry
    
    def run(
        self, 
        prompt: str, 
        thread_id: str = "default",
        force_graph: Optional[Any] = None
    ):
        """
        Run an agent with the given prompt.
        
        Args:
            prompt: The user's request/question
            thread_id: Session ID for state persistence
            force_graph: Optional graph instance to use instead of default
            
        Returns:
            AsyncGenerator yielding events from the agent
        """
        runner = GraphRunner(graph=force_graph)
        return runner.run(prompt, thread_id=thread_id)
    
    def run_sync(
        self, 
        prompt: str, 
        thread_id: str = "default",
        force_graph: Optional[Any] = None
    ) -> List[Any]:
        """
        Run an agent synchronously and collect all events.
        
        WARNING: Do not use this method if you are already inside an async loop 
        (like Jupyter or an async web framework). Use `await kor.run(...)` instead.
        
        Args:
            prompt: The user's request/question
            thread_id: Session ID
            force_graph: Optional graph instance
            
        Returns:
            List of all events generated
            
        Raises:
            RuntimeError: If called from an active event loop.
        """
        import asyncio
        events = []
        
        async def _collect():
            async for event in self.run(prompt, thread_id, force_graph):
                events.append(event)
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            raise RuntimeError(
                "You are trying to call 'run_sync' from an active async event loop.\n"
                "In Jupyter/Colab or async functions, use:\n\n"
                "    async for event in kor.run(prompt):\n"
                "        print(event)\n"
                "\nOr if you just want the list:\n"
                "    events = [e async for e in kor.run(prompt)]"
            )
        
        return asyncio.run(_collect())
    
    def shutdown(self) -> None:
        """Gracefully shutdown the KOR system."""
        import asyncio
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If we are in a loop (e.g. Jupyter), we should schedule the shutdown task
            # but we can't await it here because this is a sync method.
            # Best effort: create a task. The user ideally should use an async shutdown if in async context.
            loop.create_task(self._kernel.shutdown())
        else:
            asyncio.run(self._kernel.shutdown())
             
        self._booted = False
    
    def __repr__(self) -> str:
        status = "booted" if self._booted else "not booted"
        return f"<Kor({status})>"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Facade (Primary API)
    "Kor",
    
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
    "AgentDefinition",
    
    # Tools
    "KorTool",
    "TerminalTool",
    "BrowserTool",
    "ToolRegistry",
    "ToolInfo",
    
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
