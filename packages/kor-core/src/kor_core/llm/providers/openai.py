"""
OpenAI LLM Provider

Built-in provider for OpenAI and OpenAI-compatible APIs.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI LLM Provider Implementation."""
    
    name = "openai"
    
    def get_chat_model(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ):
        """Creates a ChatOpenAI instance."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai is required for OpenAI provider. "
                "Install with: pip install langchain-openai"
            )
        
        # Extract known args
        api_key = config.get("api_key")
        base_url = config.get("base_url")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens")
        timeout = config.get("timeout")
        
        # Extra args (like max_retries, organization, etc.)
        extra = config.get("extra", {})
        
        # Merge all into kwargs for ChatOpenAI
        kwargs = {
            "model": model_name,
            "api_key": api_key,
            "temperature": temperature,
            "base_url": base_url,
            **extra
        }
        
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        
        if timeout is not None:
            kwargs["timeout"] = timeout
        
        if config.get("streaming"):
            kwargs["streaming"] = True
            
        return ChatOpenAI(**kwargs)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return bool(config.get("api_key"))
