import importlib
import importlib.metadata
import sys
import json
from pathlib import Path
from typing import List, Type, Dict
import logging
from .plugin import KorPlugin, KorContext
from .plugin.manifest import PluginManifest, AgentDefinition
from .config import KorConfig, MCPServerConfig, LSPServerConfig

if TYPE_CHECKING:
    from .commands import Command

logger = logging.getLogger(__name__)

class PluginLoader:
    """
    Responsible for discovering, resolving dependencies, and loading plugins.
    
    Supports both Python-based plugins and declarative-only plugins with:
    - Slash commands (commands/*.md)
    - Skills (skills/*/SKILL.md)
    - Hooks (hooks.json)
    - MCP configs (.mcp.json)
    - LSP configs (.lsp.json)
    """
    def __init__(self):
        self._plugins: Dict[str, KorPlugin] = {}
        self._discovered_classes: List[Type[KorPlugin]] = []
        self._discovered_agents: List[AgentDefinition] = []
        self._discovered_manifests: Dict[str, PluginManifest] = {}
        
        # Declarative resource storage
        self._discovered_commands: List["Command"] = []
        self._discovered_hooks: Dict[str, List] = {}
        self._discovered_mcp_configs: Dict[str, "MCPServerConfig"] = {}
        self._discovered_lsp_configs: Dict[str, "LSPServerConfig"] = {}

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
        self._discovered_manifests[manifest.name] = manifest

        # Store agents from manifest
        if manifest.agents:
            self._discovered_agents.extend(manifest.agents)

        # Load declarative resources (no Python required)
        self._load_declarative_commands(root_dir, manifest)
        self._load_declarative_skills(root_dir, manifest)
        self._load_declarative_hooks(root_dir, manifest)
        self._load_declarative_mcp(root_dir, manifest)
        self._load_declarative_lsp(root_dir, manifest)

        # If it has a python entry point, load it (OPTIONAL now)
        if manifest.entry_point:
            # Check for 'src' layout
            src_dir = root_dir / "src"
            if src_dir.exists():
                sys.path.insert(0, str(src_dir))
                path_to_remove = str(src_dir)
            else:
                sys.path.insert(0, str(root_dir))
                path_to_remove = str(root_dir)
                
            try:
                # Handle "module:Class" syntax (required format)
                if ":" not in manifest.entry_point:
                    logger.error(f"Invalid entry_point format '{manifest.entry_point}'. Use 'module:Class' format.")
                else:
                    module_name, class_name = manifest.entry_point.split(":")
                    module = importlib.import_module(module_name)
                    plugin_cls = getattr(module, class_name)
                    if isinstance(plugin_cls, type) and issubclass(plugin_cls, KorPlugin):
                        self.register_plugin_class(plugin_cls)
                             
            except Exception as e:
                logger.error(f"Failed to load entry point {manifest.entry_point} for {manifest.name}: {e}")
            finally:
                if path_to_remove in sys.path:
                    sys.path.remove(path_to_remove)
    
    def _load_declarative_commands(self, root_dir: Path, manifest: PluginManifest) -> None:
        """Load slash commands from the commands directory."""
        commands_dir = root_dir / manifest.commands_dir
        if not commands_dir.exists():
            return
        
        try:
            from .commands import CommandLoader
            loader = CommandLoader()
            commands = loader.load_directory(commands_dir)
            self._discovered_commands.extend(commands)
            if commands:
                logger.info(f"Loaded {len(commands)} commands from {manifest.name}")
        except ImportError:
            logger.debug("Commands module not available")
        except Exception as e:
            logger.error(f"Failed to load commands from {manifest.name}: {e}")
    
    def _load_declarative_skills(self, root_dir: Path, manifest: PluginManifest) -> None:
        """Load skills from the skills directory."""
        skills_dir = root_dir / manifest.skills_dir
        if not skills_dir.exists():
            return
        
        try:
            from .skills.loader import SkillLoader
            loader = SkillLoader()
            skills = loader.load_directory(skills_dir)
            if skills:
                logger.info(f"Loaded {len(skills)} skills from {manifest.name}")
        except ImportError:
            logger.debug("Skills module not available")
        except Exception as e:
            logger.error(f"Failed to load skills from {manifest.name}: {e}")
    
    def _load_declarative_hooks(self, root_dir: Path, manifest: PluginManifest) -> None:
        """Load hooks from hooks.json."""
        hooks_path = root_dir / manifest.hooks_path
        if not hooks_path.exists():
            return
        
        try:
            from .hooks import HooksLoader
            loader = HooksLoader()
            hooks = loader.load_file(hooks_path)
            self._discovered_hooks.update(hooks)
            if hooks:
                logger.info(f"Loaded hooks for {len(hooks)} events from {manifest.name}")
        except ImportError:
            logger.debug("Hooks module not available")
        except Exception as e:
            logger.error(f"Failed to load hooks from {manifest.name}: {e}")
    
    def _load_declarative_mcp(self, root_dir: Path, manifest: PluginManifest) -> None:
        """Load MCP server configs from .mcp.json."""
        mcp_path = root_dir / manifest.mcp_path
        if not mcp_path.exists():
            return
        
        try:
            from .loaders import MCPConfigLoader
            loader = MCPConfigLoader()
            configs = loader.load_file(mcp_path)
            self._discovered_mcp_configs.update(configs)
            if configs:
                logger.info(f"Loaded {len(configs)} MCP configs from {manifest.name}")
        except ImportError:
            logger.debug("MCP config loader not available")
        except Exception as e:
            logger.error(f"Failed to load MCP configs from {manifest.name}: {e}")
    
    def _load_declarative_lsp(self, root_dir: Path, manifest: PluginManifest) -> None:
        """Load LSP configs from .lsp.json."""
        lsp_path = root_dir / manifest.lsp_path
        if not lsp_path.exists():
            return
        
        try:
            from .loaders import LSPConfigLoader
            loader = LSPConfigLoader()
            configs = loader.load_file(lsp_path)
            self._discovered_lsp_configs.update(configs)
            if configs:
                logger.info(f"Loaded {len(configs)} LSP configs from {manifest.name}")
        except ImportError:
            logger.debug("LSP config loader not available")
        except Exception as e:
            logger.error(f"Failed to load LSP configs from {manifest.name}: {e}")

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
