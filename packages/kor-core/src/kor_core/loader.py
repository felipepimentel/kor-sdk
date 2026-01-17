import importlib
import importlib.metadata
import pkgutil
import sys
import os
import json
from pathlib import Path
from typing import List, Type, Dict, Set, Optional
import logging
from .plugin import KorPlugin, KorContext
from .plugin.manifest import PluginManifest, AgentDefinition

logger = logging.getLogger(__name__)

class PluginLoader:
    """
    Responsible for discovering, resolving dependencies, and loading plugins.
    """
    def __init__(self):
        self._plugins: Dict[str, KorPlugin] = {}
        self._discovered_classes: List[Type[KorPlugin]] = []
        self._discovered_agents: List[AgentDefinition] = []

    def register_plugin_class(self, plugin_cls: Type[KorPlugin]):
        """Manually register a plugin class."""
        self._discovered_classes.append(plugin_cls)

    def discover_entry_points(self, group: str = "kor.plugins") -> None:
        """
        Discovers plugins via Python entry-points.
        Packages can declare: [project.entry-points."kor.plugins"]
        """
        try:
            eps = importlib.metadata.entry_points(group=group)
            for ep in eps:
                try:
                    plugin_cls = ep.load()
                    if isinstance(plugin_cls, type) and issubclass(plugin_cls, KorPlugin):
                        self.register_plugin_class(plugin_cls)
                        logger.info(f"Discovered plugin via entry-point: {ep.name}")
                except Exception as e:
                    logger.error(f"Failed to load entry-point {ep.name}: {e}")
        except Exception as e:
            logger.debug(f"No entry-points found for group '{group}': {e}")

    def load_directory_plugins(self, plugins_dir: Path) -> None:
        """
        Scans a directory for plugins with plugin.json manifests.
        """
        if not plugins_dir.exists():
            return

        for entry in plugins_dir.iterdir():
            if entry.is_dir():
                manifest_path = entry / "plugin.json"
                if manifest_path.exists():
                    try:
                        self._load_plugin_from_manifest(manifest_path, entry)
                    except Exception as e:
                        logger.error(f"Failed to load plugin from {entry}: {e}")

    def _load_plugin_from_manifest(self, manifest_path: Path, root_dir: Path):
        with open(manifest_path, "rb") as f:
            data = json.load(f)
        
        manifest = PluginManifest(**data)
        logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")

        # Store agents
        if manifest.agents:
            self._discovered_agents.extend(manifest.agents)

        # If it has a python entry point, load it
        if manifest.entry_point:
            # Add plugin root to sys.path to allow imports
            sys.path.insert(0, str(root_dir))
            try:
                module_name = manifest.entry_point.replace(".py", "").replace("/", ".")
                module = importlib.import_module(module_name)
                # Look for KorPlugin subclasses in the module
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type) and issubclass(attribute, KorPlugin) and attribute is not KorPlugin:
                        self.register_plugin_class(attribute)
            except Exception as e:
                logger.error(f"Failed to load entry point {manifest.entry_point} for {manifest.name}: {e}")
            finally:
                sys.path.pop(0)

    def load_plugins(self, context: KorContext) -> None:
        """
        Instantiates and initializes all registered plugins.
        """
        # 0. Register agents found in manifests
        try:
             # We assume agents service is registered (Kernel does it)
             agent_registry = context.registry.get_service("agents")
             for agent_def in self._discovered_agents:
                 agent_registry.register(agent_def)
                 logger.info(f"Registered agent from manifest: {agent_def.id}")
        except Exception as e:
             logger.warning(f"Could not register agents: {e}")

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

        # 2. Resolve Dependencies (Simple pass for now)
        
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
