"""
Tests for the @tool decorator.

Validates that the decorator correctly creates tool classes from functions.
"""
import pytest
from kor_core.tools.decorators import tool
from kor_core.tools.base import KorTool


def test_tool_decorator_basic():
    """Test basic @tool decorator usage."""
    @tool
    def my_tool(query: str) -> str:
        """A simple test tool."""
        return f"Result: {query}"
    
    # Decorator should return a class
    assert isinstance(my_tool, type)
    assert issubclass(my_tool, KorTool)
    
    # Instantiate and check metadata
    instance = my_tool()
    assert instance.name == "my_tool"
    assert "simple test tool" in instance.description


def test_tool_decorator_with_args():
    """Test @tool decorator with custom name and description."""
    @tool(name="custom_name", description="Custom description")
    def another_tool(x: int, y: int) -> int:
        """Original docstring."""
        return x + y
    
    instance = another_tool()
    assert instance.name == "custom_name"
    assert instance.description == "Custom description"


def test_tool_decorator_run():
    """Test that decorated tool can execute."""
    @tool
    def echo_tool(message: str) -> str:
        """Echoes the message."""
        return message.upper()
    
    instance = echo_tool()
    result = instance._run(message="hello")
    assert result == "HELLO"


def test_tool_decorator_async():
    """Test @tool decorator with async function."""
    import asyncio
    
    @tool
    async def async_tool(value: int) -> int:
        """Async tool that doubles."""
        await asyncio.sleep(0.01)
        return value * 2
    
    instance = async_tool()
    result = asyncio.run(instance._arun(value=5))
    assert result == "10"  # Returns string


def test_tool_decorator_no_docstring():
    """Test @tool decorator handles missing docstring."""
    @tool
    def no_doc_tool(x: str) -> str:
        return x
    
    instance = no_doc_tool()
    assert instance.description == "No description"


def test_tool_decorator_default_params():
    """Test @tool decorator with default parameter values."""
    @tool
    def tool_with_defaults(required: str, optional: str = "default") -> str:
        """Tool with defaults."""
        return f"{required}-{optional}"
    
    instance = tool_with_defaults()
    result = instance._run(required="value")
    assert result == "value-default"


def test_tool_args_schema():
    """Test that args_schema is correctly generated."""
    @tool
    def typed_tool(name: str, count: int, enabled: bool = True) -> str:
        """Typed parameters."""
        return "ok"
    
    instance = typed_tool()
    schema = instance.args_schema
    
    # Check schema fields
    assert "name" in schema.model_fields
    assert "count" in schema.model_fields
    assert "enabled" in schema.model_fields
