from typing import Optional, Dict, Any
import logging
import asyncio
from .plugin import ServiceRegistry, KorContext
from .loader import PluginLoader
from .config import ConfigManager
from .events.hook import HookManager, HookEvent
from .agent.registry import AgentRegistry

logger = logging.getLogger(__name__)

class Kernel:
    """
    The Core Orchestrator of the KOR system.
    """
    def __init__(self, config_options: Optional[Dict[str, Any]] = None):
        # 1. Load Configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        
        # Override with runtime options if any
        if config_options:
            pass

        # 2. Setup Services
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
        
        # 3. Register Core Tools
        self._register_core_tools()

        # 4. Create Context
        self.context = KorContext(self.registry, self.config.model_dump())
        self.loader = PluginLoader()
        self._is_initialized = False
        self.permission_callback: Optional[Callable[[str, Any], bool]] = None
        
        # Placeholder for selector (initialized in boot)
        self.model_selector = None

    def request_permission(self, action: str, details: Any) -> bool:
        """
        Requests permission for a sensitive action.
        
        Security behavior:
        - If permission_callback is set, it decides
        - If paranoid_mode is enabled, always deny
        - Otherwise, warn and allow (for development convenience)
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
        """Register built-in tools and services."""
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
        """Discovers and loads core and external plugins."""
        # 1. Entry-points discovery
        self.loader.discover_entry_points()
        
        # 2. Directory-based discovery
        config_dir = self.config_manager.config_path.parent
        plugins_dir = config_dir / "plugins"
        self.loader.load_directory_plugins(plugins_dir)

    async def boot(self):
        """Starts the kernel lifecycle (asynchronous)."""
        if self._is_initialized:
            return
        
        logger.info(f"Booting KOR Kernel (User: {self.config.user.name or 'Guest'})...")
        
        # Register default internal agent
        from .plugin.manifest import AgentDefinition
        self.agent_registry.register(AgentDefinition(
            id="default-supervisor",
            name="Default Supervisor",
            description="Standard supervisor with Coder and Researcher",
            entry="kor_core.agent.graph:create_graph"
        ))

        self.load_plugins()
        self.loader.load_plugins(self.context)
        
        # Initialize Model Selector (after plugins loaded providers)
        from .llm import ModelSelector
        self.model_selector = ModelSelector(self.llm_registry, self.config.llm)
        
        # Initialize Persistence
        from .agent.persistence import get_checkpointer
        self.checkpointer = get_checkpointer(self.config.persistence)
        self.registry.register_service("checkpointer", self.checkpointer)
        
        # Export default prompts for user customization
        from .prompts import PromptLoader
        PromptLoader.export_defaults()
        
        self._is_initialized = True
        
        # Emit on_boot hook
        await self.hooks.emit(HookEvent.ON_BOOT)
        
        logger.info("KOR Kernel Ready.")

    def boot_sync(self):
        """
        Starts the kernel lifecycle (synchronous wrapper).
        Use this in non-async contexts.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are in an async context but called sync boot.
                # This is tricky in Python. We'll try to use a task for the hooks.
                self._boot_sequential_sync()
                loop.create_task(self.hooks.emit(HookEvent.ON_BOOT))
            else:
                loop.run_until_complete(self.boot())
        except RuntimeError:
            # No loop exists
            asyncio.run(self.boot())

    def _boot_sequential_sync(self):
        """Internal helper for sync boot setup (excluding async hooks)."""
        if self._is_initialized:
            return
            
        from .plugin.manifest import AgentDefinition
        self.agent_registry.register(AgentDefinition(
            id="default-supervisor",
            name="Default Supervisor",
            description="Standard supervisor with Coder and Researcher",
            entry="kor_core.agent.graph:create_graph"
        ))

        self.load_plugins()
        self.loader.load_plugins(self.context)
        
        from .llm import ModelSelector
        self.model_selector = ModelSelector(self.llm_registry, self.config.llm)
        
        from .agent.persistence import get_checkpointer
        self.checkpointer = get_checkpointer(self.config.persistence)
        self.registry.register_service("checkpointer", self.checkpointer)
        
        from .prompts import PromptLoader
        PromptLoader.export_defaults()
        
        self._is_initialized = True


    async def shutdown(self):
        """Shuts down the kernel."""
        logger.info("Shutting down KOR Kernel...")
        
        # Stop LSP Clients
        if hasattr(self, "lsp_manager"):
            await self.lsp_manager.stop_all()
            
        await self.hooks.emit(HookEvent.ON_SHUTDOWN)
        self._is_initialized = False


# Singleton management using contextvars for async-safe isolation
from contextvars import ContextVar

_kernel_context: ContextVar[Optional["Kernel"]] = ContextVar("kor_kernel", default=None)


def get_kernel() -> "Kernel":
    """
    Returns the global Kernel instance.
    
    Uses contextvars for async-safe isolation, allowing each async context
    to have its own kernel instance if needed.
    """
    kernel = _kernel_context.get()
    if kernel is None:
        kernel = Kernel()
        _kernel_context.set(kernel)
    return kernel


def set_kernel(kernel: "Kernel") -> None:
    """
    Sets the global Kernel instance.
    
    Useful for testing or when using a pre-configured kernel.
    """
    _kernel_context.set(kernel)


def reset_kernel() -> None:
    """
    Resets the global Kernel instance.
    
    Primarily used for testing to ensure a clean state between tests.
    """
    _kernel_context.set(None)

