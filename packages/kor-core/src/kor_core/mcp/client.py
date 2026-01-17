from contextlib import AsyncExitStack
from typing import Optional, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """
    A wrapper around an MCP Client Session.
    Handles connection lifecycle to a single server.
    """
    def __init__(self, command: str, args: list[str], env: Optional[Dict[str, str]] = None):
        self.params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        self.session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()

    async def connect(self):
        """Establishes the connection to the MCP server."""
        # Clean up any existing stack
        await self.disconnect()
        
        self._exit_stack = AsyncExitStack()
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self.params)
        )
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()

    async def disconnect(self):
        """Closes the connection."""
        if self._exit_stack:
            await self._exit_stack.aclose()
        self.session = None

    async def list_tools(self):
        if not self.session:
            raise ConnectionError("Client not connected.")
        return await self.session.list_tools()

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise ConnectionError("Client not connected.")
        return await self.session.call_tool(name, arguments)
