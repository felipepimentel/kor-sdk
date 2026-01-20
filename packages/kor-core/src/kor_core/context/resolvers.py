"""
Standard Context Resolvers.
"""
import asyncio
import logging
from typing import List, Optional
import shlex

from .protocols import ContextResolverProtocol
from .models import ContextQuery, ContextResult, ContextItem
from .sources import LocalContextSource, GitContextSource
from .exceptions import ContextError

# TODO: Move this import to avoid circular dep if needed, but for Protocol it's fine
# We need to access the VectorStore from the ServiceRegistry

logger = logging.getLogger(__name__)

class LocalResolver(ContextResolverProtocol):
    """
    Resolves local:// URIs using the LocalContextSource.
    """
    def __init__(self):
        self.source = LocalContextSource()

    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        items = await self.source.fetch(uri, query)
        return ContextResult(items=items)

class GitResolver(ContextResolverProtocol):
    """
    Resolves git:// URIs using the GitContextSource.
    """
    def __init__(self):
        self.source = GitContextSource()

    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        items = await self.source.fetch(uri, query)
        return ContextResult(items=items)

class ScriptResolver(ContextResolverProtocol):
    """
    Resolves run: URIs by executing a local script using the Kernel Sandbox.
    Format: run:scripts/my_script.py --arg value
    """
    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        from ..kernel import get_kernel
        
        cmd_str = uri.replace("run:", "").strip()
        # Basic validation handled by sandbox, but we ensure structure
        if not cmd_str:
            raise ContextError("Empty script command")
            
        # Add python3 prefix if it looks like a python script but lacks interpreter
        # TODO: Make this smarter or rely on shebangs + chmod. 
        # For now, explicit is better, but convenience matters.
        final_cmd = cmd_str
        if cmd_str.endswith(".py") and not cmd_str.startswith("python"):
             final_cmd = f"python3 {cmd_str}"
        
        # Execute via Sandbox
        kernel = get_kernel()
        try:
             # Sandbox runs synchronously or async depends on implementation
             # but our interface run_command is sync (for now) or wrapped.
             # Actually run_command in protocol is sync currently in sandbox.py?
             # Let's check sandbox.py... it is 'def run_command'.
             # Docker implementation might want async, but for V1 we used sync subprocess.
             output = await kernel.sandbox.run_command(final_cmd)
        except Exception as e:
             raise ContextError(f"Script resolution failed in sandbox: {e}")
            
        return ContextResult(
            items=[
                ContextItem(
                    id=cmd_str.split()[0], # Script name roughly
                    content=output,
                    source_uri=uri,
                    metadata={"type": "script_output", "cmd": final_cmd}
                )
            ]
        )

class MemoryResolver(ContextResolverProtocol):
    """
    Resolves memory:// URIs by querying the project's Vector Store.
    Format: memory://<query_string>
    """
    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        from ..kernel import get_kernel
        
        # Parse query from URI
        # memory://search_term or memory://?q=search_term
        # If parameters has 'q', use that. Else use the path.
        search_query = query.parameters.get("q")
        if not search_query:
            # strip scheme
            search_query = uri.replace("memory://", "").strip()
            
        if not search_query:
            raise ContextError("Empty memory query")
            
        kernel = get_kernel()
        if not kernel.registry.has_service("vector_store"):
             # Graceful degradation
             logger.warning("No Vector Store service registered. Memory resolution unavailable.")
             return ContextResult(items=[])
             
        vector_store = kernel.registry.get_service("vector_store")
        
        # Search
        # vector_store.search returns List[Dict] with 'text', 'metadata', etc.
        results = vector_store.search(search_query, top_k=5)
        
        items = []
        for res in results:
            content = res.get("text", "")
            meta = res.get("metadata", {}) or {}
            item_id = res.get("id") or meta.get("source") or "memory_item"
            
            items.append(ContextItem(
                id=item_id,
                content=content,
                source_uri=uri,
                metadata=meta
            ))
            
        return ContextResult(items=items)
