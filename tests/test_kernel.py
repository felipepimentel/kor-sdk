"""
Kernel Tests

Basic smoke tests for the KOR Kernel.
"""

from kor_core import Kernel, ConfigManager, KorConfig

def test_kernel_initialization():
    """Test that Kernel can be instantiated."""
    kernel = Kernel()
    assert kernel is not None
    assert kernel.config is not None

def test_kernel_boot():
    """Test that Kernel boots successfully."""
    kernel = Kernel()
    kernel.boot_sync()
    assert kernel._is_initialized is True

def test_config_manager():
    """Test ConfigManager loads config."""
    manager = ConfigManager()
    config = manager.load()
    assert isinstance(config, KorConfig)

def test_kernel_registry():
    """Test that Kernel has a service registry."""
    kernel = Kernel()
    assert kernel.registry is not None
