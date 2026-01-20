"""
LLM Exceptions (re-exports from main exceptions module)

For backwards compatibility, this module re-exports LLM exceptions.
Prefer importing from kor_core.exceptions directly.
"""

from ..exceptions import LLMError, ProviderNotFoundError, ModelNotConfiguredError

# Local aliases for backwards compatibility
ConfigurationError = ModelNotConfiguredError
ProviderError = ProviderNotFoundError

__all__ = ["LLMError", "ConfigurationError", "ProviderError"]
