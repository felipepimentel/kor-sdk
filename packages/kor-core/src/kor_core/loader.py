import importlib
import pkgutil
import sys
from typing import List, Type, Dict, Set
import logging
from .plugin import KorPlugin, KorContext

logger = logging.getLogger(__name__)

class PluginLoader:
    """
    Responsible for discovering, resolving dependencies, and loading plugins.
    """
    def __init__(self):
        self._plugins: Dict[str, KorPlugin] = {}
        self._discovered_classes: List[Type[KorPlugin]] = []

    def register_plugin_class(self, plugin_cls: Type[KorPlugin]):
        """Manually register a plugin class."""
        self._discovered_classes.append(plugin_cls)

    def load_plugins(self, context: KorContext) -> None:
        """
        Instantiates and initializes all registered plugins.
        TODO: Implement topological sort for dependencies.
        """
        # 1. Instantiate all plugins
        temp_registry: Dict[str, KorPlugin] = {}
        for cls in self._discovered_classes:
            try:
                plugin = cls()
                if plugin.id in temp_registry:
                    logger.warning(f"Duplicate plugin ID found: {plugin.id}. Skipping.")
                    continue
                temp_registry[plugin.id] = plugin
            except Exception as e:
                logger.error(f"Failed to instantiate plugin {cls}: {e}")

        # 2. Resolve Dependencies (Simple pass for now, assume order doesn't matter for init logic 
        # unless we strictly enforce it. For strict injection, we'd sort here).
        # For simplicity v1: Just load them all.
        
        # 3. Initialize
        for plugin_id, plugin in temp_registry.items():
            logger.info(f"Initializing plugin: {plugin_id}")
            try:
                plugin.initialize(context)
                self._plugins[plugin_id] = plugin
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_id}: {e}")

    def get_plugin(self, plugin_id: str) -> KorPlugin:
        return self._plugins[plugin_id]
