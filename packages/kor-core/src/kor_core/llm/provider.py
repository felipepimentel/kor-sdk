"""
LLM Provider Infrastructure

Provides:
- BaseLLMProvider: Protocol for LLM providers
- UnifiedProvider: Single provider supporting any OpenAI-compatible API
"""

from typing import Protocol, runtime_checkable, Any, Dict
from abc import abstractmethod
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Protocol
# =============================================================================

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
    ):
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
    ):
        """
        Returns a streaming-enabled model instance.
        Default implementation calls get_chat_model with streaming=True in config.
        """
        streaming_config = config.copy()
        streaming_config["streaming"] = True
        return self.get_chat_model(model_name, streaming_config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates that the provided configuration is sufficient for this provider.
        Returns True if valid, False otherwise.
        """
        return True


# =============================================================================
# Unified Provider
# =============================================================================

class UnifiedProvider:
    """
    Universal LLM Provider using OpenAI-compatible API.
    
    Supports ANY endpoint that is OpenAI-compatible:
    - OpenAI directly
    - Azure OpenAI
    - Anthropic via proxy
    - Corporate internal endpoints
    - Local models (Ollama, LM Studio, vLLM, etc.)
    """
    
    def __init__(self, name: str = "unified"):
        self.name = name

    def get_chat_model(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ):
        """
        Creates a ChatOpenAI instance configured for the specified endpoint.
        
        Args:
            model_name: Model identifier (e.g., "gpt-4", "claude-3-opus")
            config: Configuration including:
                - api_key: API key (optional for some endpoints)
                - base_url: Custom API endpoint (optional)
                - temperature: Model temperature (default: 0.7)
                - max_tokens: Max tokens (optional)
                - timeout: Request timeout (optional)
                - streaming: Enable streaming (optional)
                - extra: Additional kwargs to pass to ChatOpenAI
                
        Returns:
            ChatOpenAI instance
        """
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for UnifiedProvider. "
                "Install with: pip install langchain-openai"
            )
        
        # Build kwargs
        kwargs = {
            "model": model_name,
            "temperature": config.get("temperature", 0.7),
        }
        
        # API key - some endpoints don't need it
        api_key = config.get("api_key")
        if api_key:
            kwargs["api_key"] = api_key
        else:
            # LangChain requires a value, use dummy for local endpoints
            kwargs["api_key"] = "not-needed"
        
        # Custom endpoint
        base_url = config.get("base_url")
        if base_url:
            kwargs["base_url"] = base_url
        
        # Optional parameters
        if config.get("max_tokens"):
            kwargs["max_tokens"] = config["max_tokens"]
        
        if config.get("timeout"):
            kwargs["timeout"] = config["timeout"]
            
        if config.get("streaming"):
            kwargs["streaming"] = True
        
        # Extra kwargs (organization, max_retries, etc.)
        extra = config.get("extra", {})
        kwargs.update(extra)
        
        logger.debug(f"Creating UnifiedProvider model: {model_name} @ {base_url or 'openai'}")
        
        return ChatOpenAI(**kwargs)
    
    def get_streaming_model(
        self,
        model_name: str,
        config: Dict[str, Any]
    ):
        """Returns a streaming-enabled model instance."""
        streaming_config = config.copy()
        streaming_config["streaming"] = True
        return self.get_chat_model(model_name, streaming_config)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validates configuration. UnifiedProvider is flexible - minimal requirements."""
        # Must have either api_key or base_url (for local endpoints)
        return bool(config.get("api_key") or config.get("base_url"))


__all__ = ["BaseLLMProvider", "UnifiedProvider"]
