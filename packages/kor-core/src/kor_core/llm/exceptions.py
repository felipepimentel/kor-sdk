"""
Exceptions for LLM infrastructure.
"""

class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    pass

class ConfigurationError(LLMError):
    """Raised when LLM configuration is invalid or missing."""
    pass

class ProviderError(LLMError):
    """Raised when an LLM provider fails (API errors, authentication, etc)."""
    pass
