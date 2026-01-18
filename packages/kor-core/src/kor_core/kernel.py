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

    def request_permission(self, action: str, details: Any) -> bool:
        """Requests permission for a sensitive action."""
        if self.permission_callback:
            return self.permission_callback(action, details)
        
        # Fallback to emitting hook and assuming true if no one handles it?
        # In a real professional system, we'd wait for an event response.
        return True # Default to true for now if not set

    def _register_core_tools(self):
        """Register built-in tools and services."""
        from .tools import ToolRegistry, TerminalTool, BrowserTool, create_search_tool
        
        # Initialize Registry service
        registry = ToolRegistry(backend="bm25")
        self.registry.register_service("tools", registry)
        
        # Register core tools
        registry.register(TerminalTool(), tags=["shell", "execute", "commands", "terminal", "system"])
        registry.register(BrowserTool(), tags=["web", "browse", "search", "http", "internet"])
        registry.register(create_search_tool(registry), tags=["discovery", "find", "tools", "help"])

    def load_plugins(self):
        """Discovers and loads core and external plugins."""
        # 1. Entry-points discovery
        self.loader.discover_entry_points()
        
        # 2. Directory-based discovery
        config_dir = self.config_manager.config_path.parent
        plugins_dir = config_dir / "plugins"
        self.loader.load_directory_plugins(plugins_dir)

    def boot(self):
        """Starts the kernel lifecycle."""
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
        
        # Export default prompts for user customization
        from .prompts import PromptLoader
        PromptLoader.export_defaults()
        
        self._is_initialized = True
        
        # Emit on_boot hook
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.hooks.emit(HookEvent.ON_BOOT))
        else:
            loop.run_until_complete(self.hooks.emit(HookEvent.ON_BOOT))
        
        logger.info("KOR Kernel Ready.")

    def shutdown(self):
        """Shuts down the kernel."""
        logger.info("Shutting down KOR Kernel...")
        asyncio.get_event_loop().run_until_complete(self.hooks.emit(HookEvent.ON_SHUTDOWN))
        self._is_initialized = False

def get_kernel():
    """Returns the global Kernel instance."""
    global _kernel_instance
    if _kernel_instance is None:
        from .kernel import Kernel
        _kernel_instance = Kernel()
    return _kernel_instance

_kernel_instance: Optional["Kernel"] = None
