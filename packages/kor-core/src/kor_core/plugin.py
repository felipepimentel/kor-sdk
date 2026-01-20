"""
Plugin System

Responsible for discovering, resolving dependencies, and loading plugins.
Supports both Python-based plugins and declarative-only plugins.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, TypeVar, Type, TYPE_CHECKING
import importlib
import importlib.metadata
import sys
import json
from pathlib import Path
import logging
from pydantic import BaseModel, Field

from .agent.models import AgentDefinition
from .config import MCPServerConfig, LSPServerConfig

if TYPE_CHECKING:
    from .tools.registry import ToolRegistry
    from .llm.registry import LLMRegistry
    from .agent.registry import AgentRegistry
    from .commands import Command

logger = logging.getLogger(__name__)
T = TypeVar("T")

# =============================================================================
# Service Registry & Context
# =============================================================================

class ServiceRegistry:
    """
    Central registry for capabilities and tools shared between plugins.
    """
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}

    def register_service(self, name: str, service: Any) -> None:
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered.")
        self._services[name] = service

    def get_service(self, name: str, expected_type: Optional[Type[T]] = None) -> T:
        if name not in self._services:
            raise KeyError(f"Service '{name}' not found.")
        
        service = self._services[name]
        if expected_type and not isinstance(service, expected_type):
            raise TypeError(f"Service '{name}' is not of type {expected_type}")
            
        return service

    def register_tool(self, name: str, tool: Any) -> None:
        self._tools[name] = tool

    def get_tool(self, name: str) -> Any:
        return self._tools.get(name)

    # Typed accessors
    def get_tool_registry(self) -> "ToolRegistry":
        from .tools.registry import ToolRegistry
        return self.get_service("tools", ToolRegistry)

    def get_llm_registry(self) -> "LLMRegistry":
        from .llm.registry import LLMRegistry
        return self.get_service("llm", LLMRegistry)

    def get_agent_registry(self) -> "AgentRegistry":
        from .agent.registry import AgentRegistry
        return self.get_service("agents", AgentRegistry)

    def has_service(self, name: str) -> bool:
        return name in self._services

class KorContext:
    """
    Context object injected into plugins during initialization.
    """
    def __init__(self, registry: ServiceRegistry, config: Dict[str, Any]):
        self.registry = registry
        self.config = config

class KorPlugin(ABC):
    """
    Abstract Base Class for all KOR Plugins.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier (e.g., 'kor-aws')."""
        pass

    @property
    def provides(self) -> List[str]:
        return []

    @property
    def dependencies(self) -> List[str]:
        return []

    @abstractmethod
    def initialize(self, context: KorContext) -> None:
        """Register tools, services, and hooks."""
        pass


# =============================================================================
# Manifest
# =============================================================================

class PluginPermission(BaseModel):
    scope: str
    reason: str

class PluginManifest(BaseModel):
    """
    Schema for plugin.json.
    """
    # Core fields
    name: str = Field(pattern=r"^[a-z0-9-]+$", description="Unique plugin identifier")
    version: str = Field(description="Semantic version (x.y.z)")
    description: str = Field(description="Human-readable description")
    
    # Entry point
    entry_point: Optional[str] = Field(
        default=None, 
        description="Python module:Class (e.g., 'my_plugin:MyPlugin')"
    )
    
    # Capabilities
    provides: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    permissions: List[PluginPermission] = Field(default_factory=list)
    
    # Agents (Uses Unified AgentDefinition)
    agents: List[AgentDefinition] = Field(default_factory=list)
    
    # Resource paths
    commands_dir: str = "commands"
    agents_dir: str = "agents"
    skills_dir: str = "skills"
    hooks_path: str = "hooks.json"
    mcp_path: str = ".mcp.json"
    lsp_path: str = ".lsp.json"
    
    # Context Platform
    context_schemes: List[str] = Field(default_factory=list, description="URI schemes handled by this plugin")


# =============================================================================
# Plugin Loader
# =============================================================================

class PluginLoader:
    """
    Responsible for discovering, resolving dependencies, and loading plugins.
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
        """Discovers plugins via Python entry-points."""
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
        """Scans a directory for plugins with plugin.json manifests."""
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
        
        # NOTE: If JSON contains "agents", they will be parsed into AgentDefinition objects
        # because PluginManifest.agents is typed as List[AgentDefinition]
        manifest = PluginManifest(**data)
        logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")
        self._discovered_manifests[manifest.name] = manifest

        # Store agents from manifest
        if manifest.agents:
            self._discovered_agents.extend(manifest.agents)

        # Load declarative resources
        self._load_declarative_commands(root_dir, manifest)
        self._load_declarative_skills(root_dir, manifest)
        self._load_declarative_hooks(root_dir, manifest)
        self._load_declarative_mcp(root_dir, manifest)
        self._load_declarative_lsp(root_dir, manifest)

        # Load Python entry point if exists
        if manifest.entry_point:
            src_dir = root_dir / "src"
            if src_dir.exists():
                sys.path.insert(0, str(src_dir))
                path_to_remove = str(src_dir)
            else:
                sys.path.insert(0, str(root_dir))
                path_to_remove = str(root_dir)
                
            try:
                if ":" not in manifest.entry_point:
                    logger.error(f"Invalid entry_point format '{manifest.entry_point}'")
                else:
                    module_name, class_name = manifest.entry_point.split(":")
                    module = importlib.import_module(module_name)
                    plugin_cls = getattr(module, class_name)
                    if isinstance(plugin_cls, type) and issubclass(plugin_cls, KorPlugin):
                        self.register_plugin_class(plugin_cls)
            except Exception as e:
                logger.error(f"Failed to load entry point {manifest.entry_point}: {e}")
            finally:
                if path_to_remove in sys.path:
                    sys.path.remove(path_to_remove)
    
    def _load_declarative_commands(self, root_dir: Path, manifest: PluginManifest) -> None:
        commands_dir = root_dir / manifest.commands_dir
        if not commands_dir.exists(): return
        
        try:
            from .commands import CommandLoader
            loader = CommandLoader()
            commands = loader.load_directory(commands_dir)
            self._discovered_commands.extend(commands)
        except Exception as e:
            logger.error(f"Failed to load commands from {manifest.name}: {e}")
    
    def _load_declarative_skills(self, root_dir: Path, manifest: PluginManifest) -> None:
        skills_dir = root_dir / manifest.skills_dir
        if not skills_dir.exists(): return
        
        try:
            from .skills import SkillLoader
            loader = SkillLoader()
            skills = loader.load_directory(skills_dir)
            if skills:
                logger.info(f"Loaded {len(skills)} skills from {manifest.name}")
        except Exception as e:
            logger.error(f"Failed to load skills from {manifest.name}: {e}")
    
    def _load_declarative_hooks(self, root_dir: Path, manifest: PluginManifest) -> None:
        hooks_path = root_dir / manifest.hooks_path
        if not hooks_path.exists(): return
        
        try:
            from .events import HooksLoader
            loader = HooksLoader()
            hooks = loader.load_file(hooks_path)
            self._discovered_hooks.update(hooks)
        except Exception as e:
            logger.error(f"Failed to load hooks from {manifest.name}: {e}")
    
    def _load_declarative_mcp(self, root_dir: Path, manifest: PluginManifest) -> None:
        mcp_path = root_dir / manifest.mcp_path
        if not mcp_path.exists(): return
        
        try:
            from .mcp.loader import MCPConfigLoader
            loader = MCPConfigLoader()
            configs = loader.load_file(mcp_path)
            self._discovered_mcp_configs.update(configs)
        except Exception as e:
            logger.error(f"Failed to load MCP configs from {manifest.name}: {e}")
    
    def _load_declarative_lsp(self, root_dir: Path, manifest: PluginManifest) -> None:
        lsp_path = root_dir / manifest.lsp_path
        if not lsp_path.exists(): return
        
        try:
            from .lsp.loader import LSPConfigLoader
            loader = LSPConfigLoader()
            configs = loader.load_file(lsp_path)
            self._discovered_lsp_configs.update(configs)
        except Exception as e:
            logger.error(f"Failed to load LSP configs from {manifest.name}: {e}")

    def load_plugins(self, context: KorContext) -> None:
        """Instantiates and initializes all registered plugins."""
        # 0. Register agents found in manifests
        try:
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
                    logger.warning(f"Duplicate plugin ID {plugin.id}. Skipping.")
                    continue
                temp_registry[plugin.id] = plugin
            except Exception as e:
                logger.error(f"Failed to instantiate plugin {cls}: {e}")

        # 2. Resolve Dependencies (Simple pass)
        
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
