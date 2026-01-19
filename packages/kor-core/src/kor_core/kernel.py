from typing import Optional, Dict, Any, Callable
import logging
import asyncio
import os
from .plugin import ServiceRegistry, KorContext
from .loader import PluginLoader
from .config import ConfigManager
from .events.hook import HookManager, HookEvent
from .agent.registry import AgentRegistry

logger = logging.getLogger(__name__)

class Kernel:
    """
    The Core Orchestrator of the KOR system.
    
    The Kernel manages the lifecycle of the KOR SDK, including service registration,
    plugin loading, configuration management, and event handling. It acts as the
    central hub for all SDK operations.
    
    Attributes:
        config_manager (ConfigManager): Handles loading and saving configuration.
        config (KorConfig): The current validated configuration.
        registry (ServiceRegistry): Central registry for all shared services.
        agent_registry (AgentRegistry): Registry for agent definitions.
        llm_registry (LLMRegistry): Registry for LLM providers.
        lsp_manager (LSPManager): Manager for Language Server Protocol clients.
        hooks (HookManager): Event emitter for system lifecycle hooks.
        context (KorContext): Context object shared with plugins.
        loader (PluginLoader): Discovers and loads external plugins.
    """
    def __init__(self, config_options: Optional[Dict[str, Any]] = None):
        """
        Initializes the Kernel.
        
        Args:
            config_options (Optional[Dict[str, Any]]): Optional runtime configuration
                overrides to apply during initialization.
        """
        # 1. Load Configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        
        # Override with runtime options if any
        if config_options:
            logger.debug(f"Applying runtime config overrides: {list(config_options.keys())}")
            self.config_manager.update(config_options)
            # Re-validate after overrides
            self.config = self.config_manager.config

        # 2. Apply network configuration (proxy, SSL)
        self._apply_network_config()

        # 3. Setup Services
        self.registry = ServiceRegistry()
        self.agent_registry = AgentRegistry()
        self.registry.register_service("agents", self.agent_registry)
        
        # LLM Services
        from .llm import LLMRegistry
        self.llm_registry = LLMRegistry()
        self.registry.register_service("llm", self.llm_registry)
        
        # LSP Services
        from .lsp.manager import LSPManager
        self.lsp_manager = LSPManager(self.config.languages)
        self.registry.register_service("lsp", self.lsp_manager)
        
        self.hooks = HookManager()
        from .events.telemetry import setup_telemetry
        setup_telemetry(self.hooks)
        
        # 4. Register Core Tools
        self._register_core_tools()

        # 5. Create Context
        self.context = KorContext(self.registry, self.config.model_dump())
        self.loader = PluginLoader()
        self._is_initialized = False
        self.permission_callback: Optional[Callable[[str, Any], bool]] = None
        
        # Placeholder for selector (initialized in boot)
        self.model_selector = None

    def _apply_network_config(self):
        """Apply network configuration (proxy, SSL, timeouts) to environment."""
        net = self.config.network
        
        if net.http_proxy:
            os.environ["HTTP_PROXY"] = net.http_proxy
            os.environ["http_proxy"] = net.http_proxy
            logger.info(f"HTTP proxy configured: {net.http_proxy}")
            
        if net.https_proxy:
            os.environ["HTTPS_PROXY"] = net.https_proxy
            os.environ["https_proxy"] = net.https_proxy
            logger.info(f"HTTPS proxy configured: {net.https_proxy}")
            
        if net.no_proxy:
            os.environ["NO_PROXY"] = net.no_proxy
            os.environ["no_proxy"] = net.no_proxy
            
        if net.ca_bundle:
            os.environ["REQUESTS_CA_BUNDLE"] = net.ca_bundle
            os.environ["SSL_CERT_FILE"] = net.ca_bundle
            os.environ["CURL_CA_BUNDLE"] = net.ca_bundle
            logger.info(f"Custom CA bundle: {net.ca_bundle}")
            
        if not net.verify_ssl:
            os.environ["CURL_SSL_VERIFY"] = "0"
            logger.warning("SSL verification disabled - not recommended for production")

    def request_permission(self, action: str, details: Any) -> bool:
        """
        Requests permission for a sensitive action.
        
        Security behavior:
        - If permission_callback is set, it decides.
        - If paranoid_mode is enabled, always deny without callback.
        - Otherwise, warn and allow (for development convenience).

        Args:
            action (str): A string identifying the action (e.g., 'terminal_run').
            details (Any): Additional context about the action.
            
        Returns:
            bool: True if permission is granted, False otherwise.
        """
        if self.permission_callback:
            return self.permission_callback(action, details)
        
        # No callback set - check security policy
        if self.config.security.paranoid_mode:
            logger.warning(f"Permission DENIED (paranoid_mode=true): {action}")
            return False
        
        # Non-paranoid: warn and allow for development convenience
        logger.warning(f"No permission callback set. Allowing action: {action}")
        return True

    def _register_core_tools(self):
        """Register built-in tools and services like Terminal, Browser, and File tools."""
        from .tools import ToolRegistry, TerminalTool, BrowserTool, create_search_tool, ReadFileTool, WriteFileTool, ListDirTool
        from .tools.lsp import LSPHoverTool, LSPDefinitionTool
        
        # Initialize Registry service
        registry = ToolRegistry(backend="bm25")
        self.registry.register_service("tools", registry)
        
        # Register core tools
        registry.register(TerminalTool(), tags=["shell", "execute", "commands", "terminal", "system"])
        registry.register(BrowserTool(), tags=["web", "browse", "search", "http", "internet"])
        registry.register(ReadFileTool(), tags=["file", "read", "fs", "system"])
        registry.register(WriteFileTool(), tags=["file", "write", "create", "fs", "system"])
        registry.register(ListDirTool(), tags=["file", "list", "dir", "fs", "system"])
        registry.register(create_search_tool(registry), tags=["discovery", "find", "tools", "help"])
        registry.register(LSPHoverTool(), tags=["lsp", "code", "hover", "docs"])
        registry.register(LSPDefinitionTool(), tags=["lsp", "code", "definition", "navigation"])

    def load_plugins(self):
        """Discovers and loads core and external plugins from entry points and directories."""
        # 1. Entry-points discovery
        self.loader.discover_entry_points()
        
        # 2. Directory-based discovery
        config_dir = self.config_manager.config_path.parent
        plugins_dir = config_dir / "plugins"
        self.loader.load_directory_plugins(plugins_dir)

    def _register_builtin_providers(self):
        """Register built-in LLM providers (OpenAI, LiteLLM)."""
        try:
            from .llm.providers import OpenAIProvider
            self.llm_registry.register(OpenAIProvider())
            logger.debug("Registered built-in OpenAI provider")
        except ImportError:
            logger.debug("OpenAI provider not available (missing langchain-openai)")
        except Exception as e:
            logger.warning(f"Failed to register OpenAI provider: {e}")
            
        try:
            from .llm.providers import LiteLLMProvider
            self.llm_registry.register(LiteLLMProvider())
            logger.debug("Registered built-in LiteLLM provider")
        except ImportError:
            logger.debug("LiteLLM provider not available (missing langchain-community)")
        except Exception as e:
            logger.warning(f"Failed to register LiteLLM provider: {e}")

    def _initialize_internal(self):
        """Internal helper for common initialization steps (Async/Sync agnostic)."""
        if self._is_initialized:
            return

        logger.info(f"Initializing KOR Kernel (User: {self.config.user.name or 'Guest'})...")
        
        # Register default internal agent
        from .plugin.manifest import AgentDefinition
        self.agent_registry.register(AgentDefinition(
            id="default-supervisor",
            name="Default Supervisor",
            description="Standard supervisor with Coder and Researcher",
            entry="kor_core.agent.graph:create_graph"
        ))

        # Register built-in LLM providers
        self._register_builtin_providers()

        # Load Plugins
        self.load_plugins()
        self.loader.load_plugins(self.context)
        
        # Initialize Model Selector
        from .llm import ModelSelector
        self.model_selector = ModelSelector(self.llm_registry, self.config.llm)
        
        # Initialize Persistence
        from .agent.persistence import get_checkpointer
        self.checkpointer = get_checkpointer(self.config.persistence)
        self.registry.register_service("checkpointer", self.checkpointer)
        
        # Export default prompts
        from .prompts import PromptLoader
        PromptLoader.export_defaults()
        
        self._is_initialized = True

    async def boot(self):
        """
        Starts the kernel lifecycle asynchronously.
        This is the primary way to initialize the KOR environment in async code.
        """
        if self._is_initialized:
            return
            
        self._initialize_internal()
        
        # Emit on_boot hook
        await self.hooks.emit(HookEvent.ON_BOOT)
        logger.info("KOR Kernel Ready.")

    def boot_sync(self):
        """
        Starts the kernel lifecycle (synchronous wrapper).
        Convenience method for non-async environments (CLI, scripts).
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in an async context but called sync boot.
                # Initialize internal state synchronously
                self._initialize_internal()
                # Schedule hook emission for later
                loop.create_task(self.hooks.emit(HookEvent.ON_BOOT))
            else:
                loop.run_until_complete(self.boot())
        except RuntimeError:
            # No loop exists
            asyncio.run(self.boot())


    async def shutdown(self):
        """
        Shuts down the kernel and cleans up resources.
        
        Stops all LSP clients and emits the ON_SHUTDOWN hook.
        """
        logger.info("Shutting down KOR Kernel...")
        
        # Stop LSP Clients
        if hasattr(self, "lsp_manager"):
            await self.lsp_manager.stop_all()
            
        await self.hooks.emit(HookEvent.ON_SHUTDOWN)
        self._is_initialized = False

    async def __aenter__(self) -> "Kernel":
        """
        Async context manager entry - boots the kernel.
        
        Returns:
            Kernel: The booted kernel instance.
        
        Example:
            async with Kernel() as kernel:
                # kernel is ready to use
                model = kernel.model_selector.get_model()
        """
        await self.boot()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Async context manager exit - shuts down the kernel.
        
        Ensures proper cleanup of resources regardless of exceptions.
        
        Returns:
            bool: False to propagate any exceptions.
        """
        await self.shutdown()
        return False


# Singleton management using contextvars for async-safe isolation
from contextvars import ContextVar

_kernel_context: ContextVar[Optional["Kernel"]] = ContextVar("kor_kernel", default=None)


def get_kernel() -> "Kernel":
    """
    Returns the global Kernel instance.
    
    Uses contextvars for async-safe isolation, allowing each async context
    to have its own kernel instance if needed. If no instance exists in the
    current context, a new one is created.
    
    Returns:
        Kernel: The active Kernel instance.
    """
    kernel = _kernel_context.get()
    if kernel is None:
        kernel = Kernel()
        _kernel_context.set(kernel)
    return kernel


def set_kernel(kernel: "Kernel") -> None:
    """
    Sets the global Kernel instance for the current context.
    
    Useful for testing or when injecting a pre-configured kernel.
    
    Args:
        kernel (Kernel): The Kernel instance to set.
    """
    _kernel_context.set(kernel)


def reset_kernel() -> None:
    """
    Resets the global Kernel instance for the current context.
    
    Primarily used for testing to ensure a clean state between test cases.
    """
    _kernel_context.set(None)


