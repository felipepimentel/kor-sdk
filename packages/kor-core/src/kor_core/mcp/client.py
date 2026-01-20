import asyncio
import logging
from enum import Enum
from contextlib import AsyncExitStack
from typing import Optional, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ..exceptions import ToolError

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"

class MCPClient:
    """
    A persistent wrapper around an MCP Client Session.
    Handles connection lifecycle to a single server with retry logic.
    """
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        self.session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()
        self.state = ConnectionState.DISCONNECTED
        self.max_retries = 3
        self.initial_backoff = 1.0 # seconds
        self._reconnect_attempts = 0

    async def connect(self, retry: bool = True):
        """
        Establishes the connection to the MCP server.
        If retry=True, uses exponential backoff.
        """
        if self.state == ConnectionState.CONNECTING:
            return
        
        # Clean up any existing stack
        await self.disconnect()
        
        self.state = ConnectionState.CONNECTING
        retries = 0
        backoff = self.initial_backoff

        while True:
            try:
                logger.info(f"Connecting to MCP server: {self.params.command} (Attempt {retries + 1})")
                self._exit_stack = AsyncExitStack()
                
                read, write = await self._exit_stack.enter_async_context(
                    stdio_client(self.params)
                )
                self.session = await self._exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await self.session.initialize()
                
                self.state = ConnectionState.CONNECTED
                self._reconnect_attempts = 0  # Reset on successful connection
                logger.info("Successfully connected to MCP server.")
                return
            except Exception as e:
                retries += 1
                if not retry or retries >= self.max_retries:
                    self.state = ConnectionState.FAILED
                    logger.error(f"Failed to connect to MCP server after {retries} attempts: {e}")
                    raise ToolError(f"MCP Connection failed: {e}") from e
                
                logger.warning(f"Connection failed: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2 # Exponential backoff

    async def disconnect(self):
        """Closes the connection gracefully."""
        if self._exit_stack:
            await self._exit_stack.aclose()
        self.session = None
        self.state = ConnectionState.DISCONNECTED
        logger.debug("Disconnected from MCP server.")

    async def is_alive(self) -> bool:
        """Checks if the connection is still alive by listing tools."""
        if self.state != ConnectionState.CONNECTED or not self.session:
            return False
        try:
            # A simple lightweight call to check responsiveness
            await self.session.list_tools()
            return True
        except Exception:
            self.state = ConnectionState.FAILED
            return False

    async def list_tools(self):
        """Lists tools available through this MCP server."""
        if self.state != ConnectionState.CONNECTED:
            await self.connect()
            
        try:
            return await self.session.list_tools()
        except Exception as e:
            logger.error(f"MCP list_tools failed: {e}")
            self.state = ConnectionState.FAILED
            raise ToolError(f"Failed to list MCP tools: {e}")


    async def list_resources(self):
        """Lists resources available through this MCP server."""
        if self.state != ConnectionState.CONNECTED:
            await self.connect()
            
        try:
            return await self.session.list_resources()
        except Exception as e:
            logger.error(f"MCP list_resources failed: {e}")
            # Resources might not be supported by all servers, so we don't necessarily fail state
            # self.state = ConnectionState.FAILED 
            raise ToolError(f"Failed to list MCP resources: {e}")

    async def read_resource(self, uri: str):
        """Reads a resource from the MCP server."""
        if self.state != ConnectionState.CONNECTED:
            await self.connect()
            
        try:
            return await self.session.read_resource(uri)
        except Exception as e:
            logger.error(f"MCP read_resource failed ({uri}): {e}")
            raise ToolError(f"Failed to read MCP resource '{uri}': {e}")

    async def call_tool(self, name: str, arguments: dict):
        """Calls a specific tool on the MCP server."""
        if self.state != ConnectionState.CONNECTED:
            await self.connect()
            
        try:
            return await self.session.call_tool(name, arguments)
        except Exception as e:
            logger.error(f"MCP call_tool failed ({name}): {e}")
            self.state = ConnectionState.FAILED
            
            # Auto-reconnect on transient failures
            # We assume most errors here might be pipe broken or connection lost
            if self._reconnect_attempts < 1:
                logger.warning(f"Attempting valid auto-reconnect for tool '{name}'...")
                self._reconnect_attempts += 1
                try:
                    await self.connect()
                    return await self.session.call_tool(name, arguments)
                except Exception as retry_err:
                    logger.error(f"Auto-reconnect failed: {retry_err}")
                    # Fall through to raise original or new error
            
            raise ToolError(f"Failed to call MCP tool '{name}': {e}")

