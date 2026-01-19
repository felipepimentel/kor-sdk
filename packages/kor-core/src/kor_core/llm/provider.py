from typing import Protocol, runtime_checkable, Any, Dict, Optional
from abc import abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

@runtime_checkable
class BaseLLMProvider(Protocol):
    """
    Protocol for LLM providers.
    Plugins must implement this interface to register as an LLM provider.
    """
    
    name: str  # e.g., "openai", "anthropic", "custom"
    
    @abstractmethod
    def get_chat_model(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ) -> BaseChatModel:
        """
        Returns a LangChain-compatible chat model.
        
        Args:
            model_name: The identifier of the model (e.g., "gpt-4", "claude-3-opus")
            config: Provider-specific configuration (api_key, base_url, extra, etc.)
        """
        ...
    
    def get_streaming_model(
        self,
        model_name: str,
        config: Dict[str, Any]
    ) -> BaseChatModel:
        """
        Returns a streaming-enabled model instance.
        Default implementation calls get_chat_model with streaming=True in config.
        """
        # Create a copy of config to avoid mutation
        streaming_config = config.copy()
        streaming_config["streaming"] = True
        return self.get_chat_model(model_name, streaming_config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates that the provided configuration is sufficient for this provider.
        Returns True if valid, False otherwise.
        """
        # Default simple validation
        return True
