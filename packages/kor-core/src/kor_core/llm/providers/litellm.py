"""
LiteLLM Universal Provider

Built-in provider supporting OpenAI, Anthropic, VertexAI, Bedrock, OpenRouter, and more.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class LiteLLMProvider:
    """
    Universal LLM Provider using LiteLLM.
    Supports OpenAI, Anthropic, VertexAI, Bedrock, OpenRouter, Perplexity, etc.
    """
    
    name = "litellm"
    
    def get_chat_model(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ):
        """Creates a ChatLiteLLM instance."""
        try:
            from langchain_community.chat_models import ChatLiteLLM
        except ImportError:
            raise ImportError(
                "langchain-community is required for LiteLLM provider. "
                "Install with: pip install langchain-community litellm"
            )
        
        kwargs = {
            "model": model_name,
            "temperature": config.get("temperature", 0.7),
        }
        
        # Optional params
        if config.get("max_tokens"):
            kwargs["max_tokens"] = config.get("max_tokens")
            
        if config.get("timeout"):
            kwargs["request_timeout"] = config.get("timeout")
            
        if config.get("api_key"):
            kwargs["api_key"] = config.get("api_key")
            
        if config.get("base_url"):
            kwargs["base_url"] = config.get("base_url")

        # Merge 'extra' config (custom litellm specific params)
        extra = config.get("extra", {})
        kwargs.update(extra)
        
        # Handle streaming
        if config.get("streaming"):
            kwargs["streaming"] = True

        return ChatLiteLLM(**kwargs)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        # LiteLLM is very flexible, often relies on Env Vars.
        return True
