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
    Resolves run: URIs by executing a local script.
    Format: run:scripts/my_script.py --arg value
    """
    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        cmd_str = uri.replace("run:", "").strip()
        parts = shlex.split(cmd_str)
        if not parts:
            raise ContextError("Empty script command")
            
        script = parts[0]
        args = parts[1:]
        
        # Execute
        proc = await asyncio.create_subprocess_exec(
            "python3", script, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise ContextError(f"Script resolution failed: {stderr.decode()}")
            
        return ContextResult(
            items=[
                ContextItem(
                    id=script,
                    content=stdout.decode(),
                    source_uri=uri,
                    metadata={"type": "script_output", "cmd": cmd_str}
                )
            ]
        )
