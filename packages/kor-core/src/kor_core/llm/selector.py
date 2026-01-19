from typing import Optional, Any, TYPE_CHECKING
import logging
from langchain_core.language_models.chat_models import BaseChatModel

from .registry import LLMRegistry
from .exceptions import ConfigurationError

if TYPE_CHECKING:
    # Avoid circular import, use string forward reference in annotation if needed
    # but here we can just use Any or Import locally
    from ..config import LLMConfig

logger = logging.getLogger(__name__)

class ModelSelector:
    """
    Responsible for selecting the appropriate LLM based on purpose or override.
    
    ModelSelector handles the resolution logic for choosing which LLM to use
    for a given task (e.g., coding, planning, supervisor). It follows a
    priority-based selection from configuration.
    
    Supports caching of model instances when config.cache_models is True.
    
    Attributes:
        registry (LLMRegistry): The registry of available LLM providers.
        config (LLMConfig): The LLM section of the system configuration.
    """
    
    def __init__(self, registry: LLMRegistry, config: "LLMConfig"):
        """
        Initializes the ModelSelector.
        
        Args:
            registry (LLMRegistry): The registry of LLM providers.
            config (LLMConfig): The LLM configuration object.
        """
        self.registry = registry
        self.config = config

    def get_model(
        self, 
        purpose: str = "default",
        override: Optional[str] = None
    ) -> BaseChatModel:
        """
        Resolves the model to use based on configuration priority.
        
        Priority order:
        1. Explicit override (e.g., "openai:gpt-4o").
        2. Purpose-specific configuration (e.g., [llm.purposes.coding]).
        3. Default configuration ([llm.default]).
        
        Args:
            purpose (str): The identifier for the operation (e.g., "supervisor", "coding").
            override (Optional[str]): An explicit "provider:model" string to force selection.
            
        Returns:
            BaseChatModel: A configured LangChain-compatible chat model instance.
            
        Raises:
            ConfigurationError: If no model can be resolved for the given purpose.
        """
        model = None

        # 1. Explicit Override
        if override:
            model = self._resolve_override(override)
            
        # 2. Purpose-Specific Lookup
        elif purpose in self.config.purposes:
            ref = self.config.purposes[purpose]
            logger.debug(f"Selected model for purpose '{purpose}': {ref.provider}/{ref.model}")
            model = self._create_model_from_ref(ref)
            
        # 3. Fallback to Default
        elif self.config.default:
            logger.debug(f"Using default model for purpose '{purpose}'")
            model = self._create_model_from_ref(self.config.default)
            
        # 4. No configuration found -> Error
        else:
            available_purposes = list(self.config.purposes.keys())
            msg = (
                f"No LLM configuration found for purpose '{purpose}' and no [llm.default] set.\n"
                f"Please configure [llm.purposes.{purpose}] or a fallback [llm.default] in your config.toml.\n"
                f"Available purposes: {available_purposes}"
            )
            raise ConfigurationError(msg)
            
        return model

    def _resolve_override(self, override: str) -> BaseChatModel:
        """
        Parses a 'provider:model' string and instantiates the model.
        
        Args:
            override (str): The override string (e.g., 'openai:gpt-4').
            
        Returns:
            BaseChatModel: The instantiated model.
            
        Raises:
            ConfigurationError: If format is invalid or provider is not configured.
        """
        if ":" not in override:
            raise ConfigurationError(f"Invalid model override format '{override}'. Expected 'provider:model'")
            
        provider_name, model_name = override.split(":", 1)
        
        provider_config = self.config.providers.get(provider_name)
        if not provider_config:
             raise ConfigurationError(
                 f"Provider '{provider_name}' specified in override is not configured in [llm.providers]."
             )
             
        # Merge basic params
        config_dict = provider_config.model_dump(exclude_none=True)
        final_config = {**config_dict, **config_dict.get("extra", {})}
        
        # Remove fields that shouldn't be in the direct kwargs
        final_config.pop("extra", None)
        final_config.pop("fallback", None)
        
        return self.registry.get_model(provider_name, model_name, final_config)

    def _create_model_from_ref(self, ref: Any) -> BaseChatModel:
        """
        Helper to instantiate a model from a ModelRef configuration object.
        
        Args:
            ref (ModelRef): The configuration reference for the model.
            
        Returns:
            BaseChatModel: The instantiated chat model.
            
        Raises:
            ConfigurationError: If the provider is not configured.
        """
        provider_name = ref.provider
        model_name = ref.model
        
        provider_config = self.config.providers.get(provider_name)
        if not provider_config:
             raise ConfigurationError(
                 f"Model expects provider '{provider_name}', but it is not configured [llm.providers.{provider_name}]"
             )
        
        config_dict = provider_config.model_dump(exclude_none=True)
        extra_dict = config_dict.pop("extra", {})
        
        ref_dict = ref.model_dump(exclude={"provider", "model"}, exclude_none=True)
        
        final_config = {
            **config_dict, 
            **extra_dict, 
            **ref_dict
        }
        
        final_config.pop("fallback", None)
        
        return self.registry.get_model(provider_name, model_name, final_config)

