import pytest
from kor_core.kernel import Kernel

@pytest.mark.asyncio
async def test_kernel_boot_context_manager():
    """Verify ContextManager loads correctly on Kernel boot."""
    # Initialize Kernel with dummy config
    kernel = Kernel()
    
    await kernel.boot()
    
    try:
        # Check service registration
        assert kernel.registry.has_service("context")
        cm = kernel.registry.get_service("context")
        
        # Check standard resolvers
        assert cm.get_resolver("local") is not None
        assert cm.get_resolver("run") is not None
        
        # Resolve something simple (local file that guaranteed exists)
        # We search for pyproject.toml in CWD (which is root)
        res = await cm.resolve("local://pyproject.toml")
        assert "kor-core" in res.items[0].content
        
    finally:
        await kernel.shutdown()
