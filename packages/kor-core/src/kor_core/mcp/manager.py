from typing import Dict, Any
import logging
from .client import MCPClient

logger = logging.getLogger(__name__)

class MCPManager:
    """
    Manages multiple MCP clients defined in the configuration.
    """
    def __init__(self, config_plugins: Dict[str, Any]):
        self.clients: Dict[str, MCPClient] = {}
        self.config_plugins = config_plugins

    async def start_all(self):
        """Starts all configured MCP servers."""
        for name, config in self.config_plugins.items():
            if not config.get("enabled", True):
                continue
            
            command = config.get("command")
            args = config.get("args", [])
            env = config.get("env")

            if command:
                logger.info(f"Starting MCP Server: {name}")
                client = MCPClient(command, args, env)
                try:
                    await client.connect()
                    self.clients[name] = client
                    
                    # Log available tools
                    tools = await client.list_tools()
                    tool_names = [t.name for t in tools.tools]
                    logger.info(f"[{name}] Connected. Tools: {tool_names}")
                    
                except Exception as e:
                    logger.error(f"Failed to start MCP Server {name}: {e}")

    async def stop_all(self):
        """Stops all clients."""
        for name, client in self.clients.items():
            await client.disconnect()
            logger.info(f"Stopped MCP Server: {name}")
        self.clients.clear()

    def get_client(self, name: str) -> MCPClient:
        if name not in self.clients:
            raise KeyError(f"MCP Client '{name}' not found.")
        return self.clients[name]
