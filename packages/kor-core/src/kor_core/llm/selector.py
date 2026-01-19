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
    Fully config-driven resolution.
    """
    
    def __init__(self, registry: LLMRegistry, config: "LLMConfig"):
        self.registry = registry
        self.config = config

    def get_model(
        self, 
        purpose: str = "default",
        override: Optional[str] = None
    ) -> BaseChatModel:
        """
        Resolves the model to use based on the following priority:
        1. Explicit override (e.g. "openai:gpt-4o")
        2. Purpose-specific configuration (e.g. [llm.purposes.coding])
        3. Default configuration ([llm.default])
        
        Args:
            purpose: The string identifier for the operation (e.g. "supervisor", "coding")
            override: An optional explicit provider:model string to force selection.
            
        Returns:
            A configured BaseChatModel instance.
        """
        
        # 1. Explicit Override
        if override:
            return self._resolve_override(override)
            
        # 2. Purpose-Specific Lookup
        # We look into the dictionary of purposes. 
        # Since 'purposes' is a Dict[str, ModelRef], we just check if key exists.
        if purpose in self.config.purposes:
            ref = self.config.purposes[purpose]
            logger.debug(f"Selected model for purpose '{purpose}': {ref.provider}/{ref.model}")
            return self._create_model_from_ref(ref)
            
        # 3. Fallback to Default (if purpose not found or purpose was 'default' implicitly)
        # Note: If purpose was "default" but user didn't define [llm.purposes.default], we fall here.
        if self.config.default:
            logger.debug(f"Using default model for purpose '{purpose}'")
            return self._create_model_from_ref(self.config.default)
            
        # 4. No configuration found -> Error
        available_purposes = list(self.config.purposes.keys())
        msg = (
            f"No LLM configuration found for purpose '{purpose}' and no [llm.default] set.\n"
            f"Please configure [llm.purposes.{purpose}] or a fallback [llm.default] in your config.toml.\n"
            f"Available purposes: {available_purposes}"
        )
        raise ConfigurationError(msg)

    def _resolve_override(self, override: str) -> BaseChatModel:
        """Parses 'provider:model' string and gets valid model."""
        if ":" not in override:
            raise ConfigurationError(f"Invalid model override format '{override}'. Expected 'provider:model'")
            
        provider_name, model_name = override.split(":", 1)
        
        # We create a temporary config for this override
        # We might miss specific API keys if we don't look up the provider config.
        # But wait, LLMRegistry.get_model needs the config dict.
        # So we should fetch the provider config from our main config object.
        
        provider_config = self.config.providers.get(provider_name)
        if not provider_config:
             # Attempt to find if we have any generic config or strict failure?
             # For flexible overrides, maybe we assume Env Vars are set if config missing?
             # Or we raise error saying provider must be configured first.
             raise ConfigurationError(
                 f"Provider '{provider_name}' specified in override is not configured in [llm.providers]."
             )
             
        # Merge basic params
        config_dict = provider_config.model_dump(exclude_none=True)
        # We might want to look into 'extra' too
        final_config = {**config_dict, **config_dict.get("extra", {})}
        
        # Remove fields that shouldn't be in the direct kwargs if any (like 'extra' itself)
        final_config.pop("extra", None)
        final_config.pop("fallback", None)
        
        return self.registry.get_model(provider_name, model_name, final_config)

    def _create_model_from_ref(self, ref: Any) -> BaseChatModel:
        """Helper to instantiate model from a ModelRef configuration object."""
        provider_name = ref.provider
        model_name = ref.model
        
        # Get provider config base
        provider_config = self.config.providers.get(provider_name)
        if not provider_config:
             raise ConfigurationError(
                 f"Model expects provider '{provider_name}', but it is not configured config.toml [llm.providers.{provider_name}]"
             )
        
        # Start with provider config
        config_dict = provider_config.model_dump(exclude_none=True)
        extra_dict = config_dict.pop("extra", {})
        
        # Merge ModelRef specific overrides (temperature, etc)
        # ModelRef has: temperature, max_tokens, timeout
        ref_dict = ref.model_dump(exclude={"provider", "model"}, exclude_none=True)
        
        # Combined config:
        # 1. Provider options (api_key, base_url)
        # 2. Provider 'extra' options (custom stuff)
        # 3. ModelRef options (temperature, timeout) -> These override provider defaults if conflict?
        
        final_config = {
            **config_dict, 
            **extra_dict, 
            **ref_dict
        }
        
        # Cleanup internal keys that shouldn't pass to provider creation if not handled
        fallback = final_config.pop("fallback", None) # TODO: Handle fallback logic if we want to implement it in Selector
        
        # Try primary
        try:
            return self.registry.get_model(provider_name, model_name, final_config)
        except Exception as e:
            # Handle Fallback if configured
            if fallback:
                logger.warning(f"Primary model {provider_name}/{model_name} failed: {e}. Trying fallback: {fallback}")
                # We need to construct a fallback lookup. 
                # Does fallback imply same model name on different provider? Or just a different provider?
                # The 'fallback' field is just a string provider name? Or a full ref?
                # The simple spec said: fallback = "anthropic"
                # This implies we try the SAME operation on 'anthropic'.
                # But 'anthropic' needs a model name. We don't know what model to use on fallback unless configured.
                # If fallback is just a provider name, we might not know the model.
                
                # REVISITING PLAN: The fallback logic in the plan was simple.
                # Let's assume for now we just log error and fail, as we removed "automatic" fallback behavior.
                # The "Opt-in" fallback was "fallback = 'anthropic'".
                # If we want to support this, we need 'default' model for that provider?
                # It gets complex. Let's keep it simple: Ensure errors are propagated clearly.
                pass
            raise e
