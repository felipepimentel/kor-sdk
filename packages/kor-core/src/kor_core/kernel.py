from typing import Optional, Dict, Any
import logging
from .plugin import ServiceRegistry, KorContext
from .loader import PluginLoader
from .config import ConfigManager

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
            # Simple override logic (could be deeper merge)
            pass

        # 2. Setup Services
        self.registry = ServiceRegistry()
        
        # 3. Create Context (Injecting Config)
        # We pass the raw dict or the Pydantic model? Let's pass the model for type safety.
        # But KorContext originally typed config as Dict[str, Any].
        # We should update KorContext in plugin.py to be generic or update the type.
        # For now, we'll pass the model_dump() to match the signature.
        self.context = KorContext(self.registry, self.config.model_dump())
        
        self.loader = PluginLoader()
        self._is_initialized = False

    def load_plugins(self):
        """Discovers and loads core and external plugins."""
        pass

    def boot(self):
        """Starts the kernel lifecycle."""
        if self._is_initialized:
            return
        
        logger.info(f"Booting KOR Kernel (User: {self.config.user.name or 'Guest'})...")
        self.load_plugins()
        self.loader.load_plugins(self.context)
        self._is_initialized = True
        logger.info("KOR Kernel Ready.")
