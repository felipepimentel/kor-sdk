"""
Protocols for the Context System.
"""

from typing import Protocol, List, Dict, Any, Union
from .models import ContextQuery, ContextResult, ContextItem

class ContextSourceProtocol(Protocol):
    """
    Protocol for a Context Source (e.g., Jira, Git, Local File).
    """
    async def fetch(self, uri: str, query: ContextQuery) -> List[ContextItem]:
        """Fetch context items from the source."""
        ...

    async def validate(self, config: Dict[str, Any]) -> bool:
        """Validate the configuration for this source."""
        ...

class ContextSinkProtocol(Protocol):
    """
    Protocol for a Context Sink (Write-Back).
    """
    async def save(self, item: ContextItem, scope: str) -> bool:
        """Persist a context item to the sink."""
        ...

class ContextResolverProtocol(Protocol):
    """
    Protocol for resolving a URI to Context Items.
    Acts as the bridge between the URI and the Source/Action.
    """
    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        """Resolve a URI (and optional query) to a result."""
        ...
