"""
Tests for the KOR exception hierarchy.

Validates that all custom exceptions work correctly and have proper messages.
"""
from kor_core.exceptions import (
    KorError,
    ConfigurationError,
    MissingConfigError,
    PluginError,
    PluginLoadError,
    PluginInitError,
    PluginDependencyError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    AgentError,
    AgentNotFoundError,
    LLMError,
    ProviderNotFoundError,
    ModelNotConfiguredError,
    PermissionDeniedError,
)


def test_kor_error_base():
    """Test base KorError."""
    error = KorError("Something went wrong")
    assert str(error) == "Something went wrong"
    assert error.message == "Something went wrong"


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("Invalid config")
    assert isinstance(error, KorError)
    assert "Invalid config" in str(error)


def test_missing_config_error():
    """Test MissingConfigError inherits from ConfigurationError."""
    error = MissingConfigError("Required field missing")
    assert isinstance(error, ConfigurationError)
    assert isinstance(error, KorError)


def test_plugin_load_error():
    """Test PluginLoadError formatting."""
    error = PluginLoadError("my-plugin", "Module not found")
    assert error.plugin_name == "my-plugin"
    assert "my-plugin" in str(error)
    assert "Module not found" in str(error)


def test_plugin_init_error():
    """Test PluginInitError formatting."""
    error = PluginInitError("my-plugin", "Dependencies missing")
    assert error.plugin_name == "my-plugin"
    assert "initialize" in str(error).lower()


def test_plugin_dependency_error():
    """Test PluginDependencyError with missing deps list."""
    error = PluginDependencyError("my-plugin", ["dep1", "dep2"])
    assert error.plugin_name == "my-plugin"
    assert error.missing_deps == ["dep1", "dep2"]
    assert "dep1" in str(error)
    assert "dep2" in str(error)


def test_tool_execution_error():
    """Test ToolExecutionError formatting."""
    error = ToolExecutionError("terminal", "Command failed")
    assert error.tool_name == "terminal"
    assert "terminal" in str(error)
    assert "Command failed" in str(error)


def test_tool_not_found_error():
    """Test ToolNotFoundError."""
    error = ToolNotFoundError("unknown_tool")
    assert error.tool_name == "unknown_tool"
    assert "unknown_tool" in str(error)


def test_agent_not_found_error():
    """Test AgentNotFoundError."""
    error = AgentNotFoundError("supervisor-v2")
    assert error.agent_id == "supervisor-v2"
    assert "supervisor-v2" in str(error)


def test_provider_not_found_error():
    """Test ProviderNotFoundError with available list."""
    error = ProviderNotFoundError("gpt5", available=["openai", "anthropic"])
    assert error.provider_name == "gpt5"
    assert error.available == ["openai", "anthropic"]
    assert "gpt5" in str(error)
    assert "openai" in str(error)


def test_provider_not_found_error_no_available():
    """Test ProviderNotFoundError without available list."""
    error = ProviderNotFoundError("unknown")
    assert error.available == []
    assert "unknown" in str(error)


def test_model_not_configured_error():
    """Test ModelNotConfiguredError."""
    error = ModelNotConfiguredError("coding")
    assert error.purpose == "coding"
    assert "coding" in str(error)
    assert "config.toml" in str(error)


def test_permission_denied_error():
    """Test PermissionDeniedError with and without reason."""
    error = PermissionDeniedError("delete_file")
    assert error.action == "delete_file"
    assert "delete_file" in str(error)
    
    error_with_reason = PermissionDeniedError("execute", reason="Paranoid mode")
    assert "Paranoid mode" in str(error_with_reason)


def test_exception_hierarchy():
    """Test that all exceptions inherit from KorError."""
    exceptions = [
        ConfigurationError("test"),
        PluginError("test"),
        ToolError("test"),
        AgentError("test"),
        LLMError("test"),
        PermissionDeniedError("test"),
    ]
    
    for exc in exceptions:
        assert isinstance(exc, KorError)
        
    # Test can be caught with KorError
    try:
        raise PluginLoadError("plugin", "reason")
    except KorError as e:
        assert "plugin" in str(e)
