"""
Tests for the ServiceRegistry class.

Validates service registration, retrieval, and typed accessors.
"""
import pytest
from kor_core.plugin import ServiceRegistry


def test_register_and_get_service():
    """Test basic service registration and retrieval."""
    registry = ServiceRegistry()
    
    service = {"value": 42}
    registry.register_service("my_service", service)
    
    retrieved = registry.get_service("my_service")
    assert retrieved == service


def test_duplicate_service_raises():
    """Test that registering duplicate service raises ValueError."""
    registry = ServiceRegistry()
    registry.register_service("test", "first")
    
    with pytest.raises(ValueError, match="already registered"):
        registry.register_service("test", "second")


def test_get_nonexistent_service_raises():
    """Test that getting non-existent service raises KeyError."""
    registry = ServiceRegistry()
    
    with pytest.raises(KeyError, match="not found"):
        registry.get_service("nonexistent")


def test_get_service_with_type_check():
    """Test type checking in get_service."""
    registry = ServiceRegistry()
    registry.register_service("string_service", "hello")
    
    # Should work with correct type
    assert registry.get_service("string_service", str) == "hello"
    
    # Should raise with wrong type
    with pytest.raises(TypeError):
        registry.get_service("string_service", int)


def test_has_service():
    """Test has_service method."""
    registry = ServiceRegistry()
    
    assert registry.has_service("missing") is False
    
    registry.register_service("present", 123)
    assert registry.has_service("present") is True


def test_register_tool():
    """Test tool registration."""
    registry = ServiceRegistry()
    
    def my_tool():
        return "tool result"
    
    registry.register_tool("my_tool", my_tool)
    
    retrieved = registry.get_tool("my_tool")
    assert retrieved() == "tool result"


def test_get_tool_nonexistent():
    """Test that get_tool returns None for missing tools."""
    registry = ServiceRegistry()
    
    assert registry.get_tool("missing") is None


def test_typed_accessor_tool_registry():
    """Test get_tool_registry typed accessor."""
    from kor_core.tools.registry import ToolRegistry
    
    registry = ServiceRegistry()
    tool_registry = ToolRegistry()
    registry.register_service("tools", tool_registry)
    
    retrieved = registry.get_tool_registry()
    assert isinstance(retrieved, ToolRegistry)


def test_typed_accessor_llm_registry():
    """Test get_llm_registry typed accessor."""
    from kor_core.llm.registry import LLMRegistry
    
    registry = ServiceRegistry()
    llm_registry = LLMRegistry()
    registry.register_service("llm", llm_registry)
    
    retrieved = registry.get_llm_registry()
    assert isinstance(retrieved, LLMRegistry)


def test_typed_accessor_missing_raises():
    """Test that typed accessors raise KeyError when service missing."""
    registry = ServiceRegistry()
    
    with pytest.raises(KeyError):
        registry.get_tool_registry()
