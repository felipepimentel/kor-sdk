"""
Built-in LLM Providers

These providers are included in kor-core and automatically registered.
"""

from .openai import OpenAIProvider
from .litellm import LiteLLMProvider

__all__ = ["OpenAIProvider", "LiteLLMProvider"]
