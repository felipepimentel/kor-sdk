"""
KOR Context Vertical.
"""

from .models import ContextQuery, ContextResult, ContextItem
from .protocols import ContextSourceProtocol, ContextSinkProtocol, ContextResolverProtocol
from .manager import ContextManager, get_context_manager
from .exceptions import ContextError, ResolverNotFoundError, SourceError

# Adapters
from .sources import LocalContextSource, GitContextSource
from .resolvers import LocalResolver, GitResolver, ScriptResolver
from .skills import SkillResolver
from .mcp import MCPResolver

__all__ = [
    "ContextQuery",
    "ContextResult",
    "ContextItem",
    "ContextSourceProtocol",
    "ContextSinkProtocol",
    "ContextResolverProtocol",
    "ContextManager",
    "get_context_manager",
    "ContextError",
    "ResolverNotFoundError",
    "SourceError",
    # Adapters
    "LocalContextSource",
    "GitContextSource",
    "LocalResolver",
    "GitResolver",
    "ScriptResolver",
    "SkillResolver",
    "MCPResolver",
]
