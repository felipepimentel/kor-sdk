import logging
from typing import Optional, Dict, Any

from .protocols import ContextResolverProtocol
from .models import ContextQuery, ContextResult, ContextItem
from .exceptions import ContextError

# TODO: Import active MCP Clients registry when available.
# For now, we assume a mechanism to get a client by server name.

logger = logging.getLogger(__name__)

class MCPResolver(ContextResolverProtocol):
    """
    Resolves mcp://<server_name>/<resource_uri_or_path>
    
    Example:
    - mcp://git/README.md  -> Call 'git' server to read 'file:///repo/root/README.md' (if mapped)
    - mcp://postgres/schema -> Call 'postgres' server to read 'postgres://.../schema'
    
    The path part is often the resource URI itself, but schemes might conflict.
    So we treat the authority as Server Name, and the path as the Resource URI (local to that server).
    """
    
    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        # uri = mcp://server_name/path/to/resource
        # or mcp://server_name/protocol://uri
        
        # Simple parsing
        parts = uri.split("mcp://", 1)
        if len(parts) < 2:
             raise ContextError(f"Invalid MCP URI: {uri}")
             
        rest = parts[1]
        if "/" not in rest:
            raise ContextError(f"Invalid MCP URI (missing resource path): {uri}")
            
        server_name, resource_path = rest.split("/", 1)
        
        # TODO: Lookup client from Kernel/Registry
        # client = get_mcp_client(server_name)
        # For now, we stub this lookup or fail if not integrated.
        
        # We need access to the ToolRegistry or MCPClientManager
        try:
             # Attempt to access Kernel singleton
             from kor_core.kernel import get_kernel
             kernel = get_kernel()
             
             mcp_manager = None
             if kernel and hasattr(kernel, 'services'):
                  mcp_manager = kernel.services.get("mcp_manager")
             
             if not mcp_manager:
                 # Feature not yet fully integrated
                 # logger.debug("MCP Manager not found in Kernel services.")
                 # raise ContextError(f"MCP Manager not found. Cannot resolve {uri}")
                 
                 # During development/test, we might not have a full kernel.
                 # Check if we can get it from a global registry?
                 # For now, consistent failure is better than silence.
                 raise ContextError(f"MCP Manager unavailable. Integration incomplete for {server_name}")
                 
             client = mcp_manager.get_client(server_name)
             if not client:
                 raise ContextError(f"MCP Server '{server_name}' not found or not connected")
                 
             # Read Resource
             # Resource path might need decoding or full URI construction depending on server
             # The server expects a URI.
             # If the resource_path doesn't look like a URI, we might need to prefix it?
             # But the user provided `mcp://server/path`. We pass `path` as the resource URI?
             # Or `file://path`?
             
             # Let's assume the user passes the full internal URI relative to the server.
             result = await client.read_resource(resource_path)
             
             return ContextResult(
                 items=[
                     ContextItem(
                         id=resource_path,
                         content=result.contents[0].text, # data[0].text in MCP spec
                         source_uri=uri,
                         metadata={"mcp_server": server_name, "mimeType": result.contents[0].mimeType}
                     )
                 ]
             )
             
        except ImportError:
            raise ContextError("Kernel not available")
        except Exception as e:
            raise ContextError(f"MCP Resolution failed: {e}")
