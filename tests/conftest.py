import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

# Add packages to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "kor-core" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "kor-cli" / "src"))

from kor_core.kernel import Kernel, reset_kernel
from kor_core.config import KorConfig, LLMConfig
from kor_core.llm.registry import LLMRegistry

@pytest.fixture(scope="function")
def event_loop():
    """Create a fresh event loop for each test function."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config():
    """Returns a basic KorConfig with mocks."""
    config = KorConfig()
    # Ensure defaults are valid for testing
    config.llm.default = {"provider": "mock", "model": "mock-gpt"} 
    return config

@pytest.fixture
def kernel(mock_config):
    """Provides a fresh Kernel instance for each test."""
    reset_kernel()
    k = Kernel()
    k.config = mock_config
    # Mock components that might need external IO
    k.config_manager = MagicMock()
    k.config_manager.load.return_value = mock_config
    return k

@pytest.fixture
def llm_registry():
    return LLMRegistry()

