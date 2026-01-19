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

def test_legacy_migration():
    """Test migration of legacy [model] section to [llm]."""
    manager = ConfigManager()
    legacy_data = {
        "model": {
            "provider": "openai",
            "name": "gpt-4"
        }
    }
    migrated = manager._migrate_legacy_config(legacy_data)
    assert "llm" in migrated
    assert migrated["llm"]["default"]["provider"] == "openai"
    assert "model" not in migrated

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
