import pytest
from unittest.mock import AsyncMock, patch
from kor_core.kernel import Kernel
from kor_core.events.hook import HookEvent

@pytest.mark.asyncio
async def test_kernel_context_manager():
    """Verify async context manager calls boot and shutdown."""
    
    with patch("kor_core.kernel.Kernel.boot", new_callable=AsyncMock) as mock_boot, \
         patch("kor_core.kernel.Kernel.shutdown", new_callable=AsyncMock) as mock_shutdown:
        
        async with Kernel() as k:
            assert isinstance(k, Kernel)
            mock_boot.assert_awaited_once()
            mock_shutdown.assert_not_awaited()
            
        mock_shutdown.assert_awaited_once()

@pytest.mark.asyncio
async def test_kernel_shutdown_cleanup(kernel):
    """Verify shutdown cleans up resources and emits hooks."""
    mock_emit = AsyncMock()
    kernel.hooks.emit = mock_emit
    
    # Mock lsp manager
    kernel.lsp_manager = AsyncMock()
    
    await kernel.shutdown()
    
    # Check LSP stopped
    kernel.lsp_manager.stop_all.assert_awaited_once()
    
    # Check hook emitted
    mock_emit.assert_awaited_with(HookEvent.ON_SHUTDOWN)
    
    assert kernel._is_initialized is False
