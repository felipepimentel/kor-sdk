import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from kor_core.context.models import ContextQuery
from kor_core.context.mcp import MCPResolver
from kor_core.context.exceptions import ContextError

# Mock response structure mimicking mcp.types
class MockResourceContent:
    def __init__(self, text, mimeType="text/plain"):
        self.text = text
        self.mimeType = mimeType

class MockReadResourceResult:
    def __init__(self, contents):
        self.contents = contents

@pytest.fixture
def mock_kernel():
    """Mock the global kernel."""
    with patch("kor_core.kernel.get_kernel") as mock_get:
        kernel = MagicMock()
        mock_get.return_value = kernel
        
        # Mock MCP Manager service
        mcp_manager = MagicMock()
        kernel.services = {"mcp_manager": mcp_manager}
        
        yield kernel, mcp_manager

@pytest.mark.asyncio
async def test_mcp_resolve_success(mock_kernel):
    """Test successful MCP resource resolution."""
    kernel, mcp_manager = mock_kernel
    
    # Mock Client
    client = AsyncMock()
    client.read_resource.return_value = MockReadResourceResult([
        MockResourceContent("Resource Content")
    ])
    mcp_manager.get_client.return_value = client
    
    resolver = MCPResolver()
    result = await resolver.resolve("mcp://test-server/path/to/resource", ContextQuery("uri"))
    
    assert len(result.items) == 1
    item = result.items[0]
    assert item.content == "Resource Content"
    assert item.id == "path/to/resource"
    assert item.metadata["mcp_server"] == "test-server"
    
    # Verify client call
    client.read_resource.assert_called_once_with("path/to/resource")

@pytest.mark.asyncio
async def test_mcp_resolve_server_not_found(mock_kernel):
    """Test resolution when server is missing."""
    _, mcp_manager = mock_kernel
    mcp_manager.get_client.return_value = None
    
    resolver = MCPResolver()
    
    with pytest.raises(ContextError) as exc:
        await resolver.resolve("mcp://missing-server/path", ContextQuery("uri"))
        
    assert "not found" in str(exc.value)

@pytest.mark.asyncio
async def test_mcp_resolve_invalid_uri():
    """Test invalid URI formats."""
    resolver = MCPResolver()
    
    with pytest.raises(ContextError):
        await resolver.resolve("mcp://incomplete", ContextQuery("uri"))
