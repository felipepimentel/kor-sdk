from typing import Dict, Optional, Any, List
import logging
from langchain_core.language_models.chat_models import BaseChatModel

from .provider import BaseLLMProvider
from ..exceptions import ConfigurationError, LLMError

logger = logging.getLogger(__name__)

class LLMRegistry:
    """
    Central registry for LLM providers.
    Manages the lifecycle of providers and caches model instances.
    """
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        # Cache key: "provider:model:config_hash" -> Model Instance
        self._model_cache: Dict[str, BaseChatModel] = {}
        self._cache_enabled = True
        
        # Register default internal providers
        # Note: MockProvider is now registered by Kernel during boot to ensure visibility
        pass

    def register(self, provider: BaseLLMProvider) -> None:
        """Registers a new LLM provider."""
        if provider.name in self._providers:
            logger.warning(f"Overwriting existing LLM provider: {provider.name}")
        
        self._providers[provider.name] = provider
        logger.debug(f"Registered LLM provider: {provider.name}")

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Retrieves a provider by name."""
        return self._providers.get(name)

    def get(self, name: str) -> Optional[BaseLLMProvider]:
        """Alias for get_provider."""
        return self.get_provider(name)

    def list_providers(self) -> List[str]:
        """Returns a list of registered provider names."""
        return list(self._providers.keys())

    def get_model(
        self, 
        provider_name: str, 
        model_name: str, 
        config: Dict[str, Any]
    ) -> BaseChatModel:
        """
        Gets a model instance from the specified provider.
        Uses caching if enabled to return existing instances.
        
        Args:
            provider_name: Name of the provider (e.g. "openai")
            model_name: Name of the model (e.g. "gpt-4")
            config: Configuration dictionary for the provider
        
        Returns:
            A BaseChatModel instance.
            
        Raises:
            ConfigurationError: If provider not found.
            LLMError: If model instantiation fails.
        """
        provider = self.get_provider(provider_name)
        if not provider:
            raise ConfigurationError(
                f"LLM Provider '{provider_name}' is not registered. "
                f"Available providers: {', '.join(self.list_providers())}"
            )
            
        # 1. Check Cache
        # We assume config dict is JSON-serializable hashable enough for this purpose
        # Or we rely on a stable string representation
        try:
            config_hash = hash(frozenset((k, str(v)) for k, v in config.items()))
        except Exception:
             # If config is complex object, fallback to no-cache or unsafe hash
             config_hash = 0
             
        cache_key = f"{provider_name}:{model_name}:{config_hash}"
        
        if self._cache_enabled and cache_key in self._model_cache:
            return self._model_cache[cache_key]

        # 2. Instantiate
        try:
            logger.debug(f"Instantiating new model: {provider_name}/{model_name}")
            model = provider.get_chat_model(model_name, config)
        except Exception as e:
            raise LLMError(f"Failed to instantiate model {model_name} from {provider_name}: {str(e)}") from e
        
        # 3. Cache
        if self._cache_enabled:
            self._model_cache[cache_key] = model
            
        return model

    def enable_cache(self, enabled: bool = True):
        self._cache_enabled = enabled
        if not enabled:
            self._model_cache.clear()
