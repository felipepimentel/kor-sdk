"""
Integration Tests for Kernel Lifecycle.

Tests the full kernel boot -> operate -> shutdown cycle.
"""
import pytest
import asyncio
from kor_core import Kernel, reset_kernel


@pytest.fixture(autouse=True)
def clean_kernel():
    """Reset kernel before each test."""
    reset_kernel()
    yield
    reset_kernel()


def test_kernel_full_lifecycle():
    """Test complete kernel lifecycle: init -> boot -> shutdown."""
    kernel = Kernel()
    
    # Should not be initialized yet
    assert kernel._is_initialized is False
    
    # Boot
    kernel.boot_sync()
    assert kernel._is_initialized is True
    
    # Registry should have core services
    assert kernel.registry.has_service("tools")
    assert kernel.registry.has_service("agents")
    
    # Shutdown
    asyncio.run(kernel.shutdown())


@pytest.mark.asyncio
async def test_kernel_async_context_manager():
    """Test kernel as async context manager."""
    async with Kernel() as kernel:
        assert kernel._is_initialized is True
        assert kernel.registry is not None
    
    # After exiting, kernel should be shut down
    # (no explicit check needed, just ensure no exceptions)


def test_kernel_with_config_overrides():
    """Test kernel initialization with runtime config overrides."""
    kernel = Kernel(config_options={
        "user": {"name": "TestUser"}
    })
    kernel.boot_sync()
    
    assert kernel.config.user.name == "TestUser"


def test_kernel_model_selector_available():
    """Test that model selector is available after boot."""
    kernel = Kernel()
    kernel.boot_sync()
    
    assert kernel.model_selector is not None


def test_kernel_hook_manager():
    """Test that hook manager is functional."""
    kernel = Kernel()
    kernel.boot_sync()
    
    assert kernel.hooks is not None
    
    # Should be able to add hooks
    called = []
    
    async def on_shutdown():
        called.append("shutdown")
    
    from kor_core.events import HookEvent
    kernel.hooks.register(HookEvent.ON_SHUTDOWN, on_shutdown)
    
    asyncio.run(kernel.shutdown())
    assert "shutdown" in called


def test_kernel_permission_callback():
    """Test permission callback functionality."""
    kernel = Kernel()
    
    # Default behavior without callback (paranoid mode off)
    assert kernel.request_permission("test", {}) is True
    
    # With callback
    def deny_all(action, details):
        return False
    
    kernel.permission_callback = deny_all
    assert kernel.request_permission("test", {}) is False


def test_kernel_paranoid_mode():
    """Test paranoid mode denies without callback."""
    kernel = Kernel()
    kernel.config.security.paranoid_mode = True
    
    # Should deny in paranoid mode without callback
    assert kernel.request_permission("dangerous_action", {}) is False


def test_kernel_singleton_pattern():
    """Test get_kernel returns same instance."""
    from kor_core import get_kernel, set_kernel
    
    k1 = get_kernel()
    k2 = get_kernel()
    
    # Same instance
    assert k1 is k2
    
    # Can set custom kernel
    custom = Kernel()
    set_kernel(custom)
    
    k3 = get_kernel()
    assert k3 is custom


def test_kernel_registers_core_tools():
    """Test that core tools are registered after boot."""
    kernel = Kernel()
    kernel.boot_sync()
    
    tool_registry = kernel.registry.get_service("tools")
    
    # Should have terminal tool
    terminal = tool_registry.get_tool("terminal")
    assert terminal is not None
    
    # Should have browser tool
    browser = tool_registry.get_tool("browser")
    assert browser is not None
