"""
Exceptions for the Context System.
"""

class ContextError(Exception):
    """Base exception for all context-related errors."""
    pass

class ResolverNotFoundError(ContextError):
    """Raised when no resolver is found for a given URI scheme."""
    pass

class SourceError(ContextError):
    """Raised when a context source fails to fetch or validate."""
    pass

class ContextValidationError(ContextError):
    """Raised when context data fails validation."""
    pass
