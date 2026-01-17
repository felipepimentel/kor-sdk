from typing import Optional, Dict, Any
import logging
import asyncio
from .plugin import ServiceRegistry, KorContext
from .loader import PluginLoader
from .config import ConfigManager
from .events.hook import HookManager, HookEvent

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
        self.hooks = HookManager()
        
        # 3. Create Context
        self.context = KorContext(self.registry, self.config.model_dump())
        
        self.loader = PluginLoader()
        self._is_initialized = False

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
        self.load_plugins()
        self.loader.load_plugins(self.context)
        self._is_initialized = True
        
        # Emit on_boot hook (synchronous wrapper for async emit)
        asyncio.get_event_loop().run_until_complete(self.hooks.emit(HookEvent.ON_BOOT))
        logger.info("KOR Kernel Ready.")

    def shutdown(self):
        """Shuts down the kernel."""
        logger.info("Shutting down KOR Kernel...")
        asyncio.get_event_loop().run_until_complete(self.hooks.emit(HookEvent.ON_SHUTDOWN))
        self._is_initialized = False
