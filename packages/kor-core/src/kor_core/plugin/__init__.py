from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, TypeVar, Type

T = TypeVar("T")

class ServiceRegistry:
    """
    Central registry for capabilities and tools shared between plugins.
    
    The registry allows plugins to expose their own services to other parts
    of the system and retrieve services registered by other plugins.
    """
    def __init__(self):
        """Initializes the ServiceRegistry with empty services and tools dictionaries."""
        self._services: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}

    def register_service(self, name: str, service: Any) -> None:
        """
        Register a shared service implementation.
        
        Args:
            name (str): The unique name of the service (e.g., 'tools', 'llm').
            service (Any): The service instance to register.
            
        Raises:
            ValueError: If a service with the same name is already registered.
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered.")
        self._services[name] = service

    def get_service(self, name: str, expected_type: Optional[Type[T]] = None) -> T:
        """
        Retrieve a service by name, optionally asserting its type.
        
        Args:
            name (str): The name of the service to retrieve.
            expected_type (Optional[Type[T]]): The type (class) that the service
                is expected to be an instance of.
                
        Returns:
            T: The service instance.
            
        Raises:
            KeyError: If the service is not found.
            TypeError: If the service is not an instance of expected_type.
        """
        if name not in self._services:
            raise KeyError(f"Service '{name}' not found.")
        
        service = self._services[name]
        if expected_type and not isinstance(service, expected_type):
            raise TypeError(f"Service '{name}' is not of type {expected_type}")
            
        return service

    def register_tool(self, name: str, tool: Any) -> None:
        """
        Register an executable tool/function.
        
        Args:
            name (str): The name of the tool.
            tool (Any): The tool instance or function to register.
        """
        self._tools[name] = tool

    def get_tool(self, name: str) -> Any:
        """
        Retrieve a tool by name.
        
        Args:
            name (str): The name of the tool to retrieve.
            
        Returns:
            Any: The tool instance or function, or None if not found.
        """
        return self._tools.get(name)

class KorContext:
    """
    Context object injected into plugins during initialization.
    
    Provides plugins with controlled access to core system capabilities like
    the service registry and configuration.
    
    Attributes:
        registry (ServiceRegistry): Access to the shared service registry.
        config (Dict[str, Any]): The current system configuration dictionary.
    """
    def __init__(self, registry: ServiceRegistry, config: Dict[str, Any]):
        """
        Initializes the KorContext.
        
        Args:
            registry (ServiceRegistry): The active service registry.
            config (Dict[str, Any]): The system configuration.
        """
        self.registry = registry
        self.config = config

class KorPlugin(ABC):
    """
    Abstract Base Class for all KOR Plugins.
    
    Plugins are the primary way to extend KOR with new providers, tools,
    and services. Every plugin must implement the `id` property and the
    `initialize` method.
    """
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique identifier for the plugin.
        
        Returns:
            str: The plugin ID (e.g., 'kor-aws', 'kor-plugin-llm-openai').
        """
        pass

    @property
    def provides(self) -> List[str]:
        """
        List of capabilities provided by this plugin.
        
        Returns:
            List[str]: Capability names (e.g., ['llm-provider-openai']).
        """
        return []

    @property
    def dependencies(self) -> List[str]:
        """
        List of capabilities required by this plugin.
        
        Returns:
            List[str]: Required capability names.
        """
        return []

    @abstractmethod
    def initialize(self, context: KorContext) -> None:
        """
        Called when the plugin is loaded by the kernel.
        
        Use this method to register tools, services, and hooks using the
        provided `context`.
        
        Args:
            context (KorContext): The plugin's interface to the KOR system.
        """
        pass

