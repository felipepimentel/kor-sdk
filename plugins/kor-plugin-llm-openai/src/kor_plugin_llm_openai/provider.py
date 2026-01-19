from typing import Dict, Any, List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from kor_core.llm import BaseLLMProvider

class OpenAIProvider:
    """OpenAI LLM Provider Implementation."""
    
    name = "openai"
    
    def get_chat_model(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ) -> BaseChatModel:
        """Creates a ChatOpenAI instance."""
        
        # Extract known args
        api_key = config.get("api_key")
        base_url = config.get("base_url")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens")
        timeout = config.get("timeout")
        
        # Extra args (like max_retries, organization, etc.)
        # LangChain's ChatOpenAI accepts them via **kwargs usually
        extra = config.get("extra", {})
        
        # Merge all into kwargs for ChatOpenAI
        # We explicitly set widely used params
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
        
        # Support streaming if requested via get_streaming_model wrapper or config
        if config.get("streaming"):
            kwargs["streaming"] = True
            
        return ChatOpenAI(**kwargs)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return bool(config.get("api_key"))
