from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict

class ServiceRegistry:
    """
    Central registry for capabilities and tools shared between plugins.
    """
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}

    def register_service(self, name: str, service: Any) -> None:
        """Register a shared service implementation."""
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered.")
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        """Retrieve a service by name."""
        if name not in self._services:
            raise KeyError(f"Service '{name}' not found.")
        return self._services[name]

    def register_tool(self, name: str, tool: Any) -> None:
        """Register an executable tool/function."""
        self._tools[name] = tool

    def get_tool(self, name: str) -> Any:
        """Retrieve a tool by name."""
        return self._tools.get(name)

class KorContext:
    """
    Context object injected into plugins during initialization.
    Provides access to core system capabilities.
    """
    def __init__(self, registry: ServiceRegistry, config: Dict[str, Any]):
        self.registry = registry
        self.config = config
        # Future: Add .ui, .mcp, .store here

class KorPlugin(ABC):
    """
    Abstract Base Class for all KOR Plugins.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the plugin (e.g., 'kor-aws')."""
        pass

    @property
    def provides(self) -> List[str]:
        """List of capabilities provided by this plugin."""
        return []

    @property
    def dependencies(self) -> List[str]:
        """List of capabilities required by this plugin."""
        return []

    @abstractmethod
    def initialize(self, context: KorContext) -> None:
        """
        Called when the plugin is loaded.
        Use this to register tools, services, and hooks.
        """
        pass
