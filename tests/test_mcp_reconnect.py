import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from kor_core.mcp.client import MCPClient
from kor_core.exceptions import ToolError

@pytest.mark.asyncio
async def test_mcp_auto_reconnect():
    """Verify call_tool triggers reconnect on failure."""
    
    client = MCPClient(command="test", args=[])
    client.connect = AsyncMock()
    client.session = AsyncMock()
    
    # First call fails
    client.session.call_tool.side_effect = [
        Exception("Connection brok-en"), # 1st call fails
        {"result": "success"}            # 2nd call succeeds (after reconnect)
    ]
    
    # We mock state to look connected initially
    # client.state is normally managed by connect/disconnect
    # Here, we only test the logic inside call_tool
    
    # Using a context where state is CONNECTED
    with patch("kor_core.mcp.client.ConnectionState") as MockState:
        client.state = MockState.CONNECTED
        
        result = await client.call_tool("my_tool", {})
        
        assert result == {"result": "success"}
        assert client.connect.call_count == 1  # Should have triggered one reconnect
        assert client._reconnect_attempts == 1

@pytest.mark.asyncio
async def test_mcp_reconnect_fails():
    """Verify failure propagates if reconnect also fails."""
    client = MCPClient(command="test", args=[])
    client.connect = AsyncMock(side_effect=Exception("Reconnect failed"))
    client.session = AsyncMock()
    client.session.call_tool.side_effect = Exception("Original error")
    
    with patch("kor_core.mcp.client.ConnectionState") as MockState:
        client.state = MockState.CONNECTED
        
        with pytest.raises(ToolError):
            await client.call_tool("my_tool", {})
            
        assert client._reconnect_attempts == 1
