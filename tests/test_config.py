import os
import tempfile
from pathlib import Path
import pytest
from kor_core.config import ConfigManager, KorConfig, SecurityConfig, LLMConfig

def test_config_loading_default():
    """Test that ConfigManager loads default configuration."""
    manager = ConfigManager()
    config = manager.load()
    assert isinstance(config, KorConfig)
    # Default name is None in UserConfig
    assert config.user.name is None

def test_config_loading_custom_path():
    """Test loading config from a custom path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "custom_config.toml"
        manager = ConfigManager(config_path)
        config = manager.load()
        assert config_path.exists()
        assert isinstance(config, KorConfig)

def test_env_var_interpolation():
    """Test that environment variables are correctly interpolated."""
    os.environ["KOR_TEST_KEY"] = "secret-123"
    try:
        manager = ConfigManager()
        data = {"secrets": {"openai_api_key": "${KOR_TEST_KEY}"}}
        interpolated = manager._interpolate_env_vars(data)
        assert interpolated["secrets"]["openai_api_key"] == "secret-123"
    finally:
        del os.environ["KOR_TEST_KEY"]

def test_config_validation_pydantic():
    """Test Pydantic validation for config."""
    config = KorConfig()
    # Pydantic should allow setting valid values
    config.security.paranoid_mode = True
    assert config.security.paranoid_mode is True
    
    # Test invalid type assignment if validate_assignment is on (it should be)
    # Note: By default Pydantic might try to coerce, but let's check.
    with pytest.raises(Exception):
        config.security.paranoid_mode = "not-a-bool"


def test_config_save_load():
    """Test saving and then loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_save.toml"
        manager = ConfigManager(config_path)
        
        config = manager.load()
        config.user.name = "TestUser"
        manager.save(config)
        
        # Load again
        new_manager = ConfigManager(config_path)
        new_config = new_manager.load()
        assert new_config.user.name == "TestUser"


def test_config_update():
    """Test in-memory update of configuration."""
    manager = ConfigManager()
    manager.load()
    
    manager.update({"user": {"name": "UpdatedUser"}})
    assert manager.config.user.name == "UpdatedUser"


def test_config_set_dot_notation():
    """Test setting config values with dot notation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_set.toml"
        manager = ConfigManager(config_path)
        manager.load()
        
        manager.set("user.name", "DotNotationUser", persist=False)
        assert manager.config.user.name == "DotNotationUser"


def test_network_config_defaults():
    """Test network configuration has sensible defaults."""
    from kor_core.config import NetworkConfig
    
    network = NetworkConfig()
    assert network.http_proxy is None
    assert network.verify_ssl is True
    assert network.connect_timeout == 30
    assert network.read_timeout == 120


def test_agent_definition():
    """Test AgentDefinition schema."""
    from kor_core.config import AgentDefinition
    
    agent = AgentDefinition(
        name="TestAgent",
        role="Test role",
        goal="Test goal",
        tools=["terminal", "browser"]
    )
    assert agent.name == "TestAgent"
    assert len(agent.tools) == 2


def test_empty_env_var_interpolation():
    """Test env var interpolation with missing variable."""
    manager = ConfigManager()
    
    # Non-existent env var should remain as-is
    data = {"key": "${NONEXISTENT_VAR}"}
    interpolated = manager._interpolate_env_vars(data)
    # Should keep the placeholder or return empty depending on implementation
    assert interpolated["key"] == "${NONEXISTENT_VAR}" or interpolated["key"] == ""

