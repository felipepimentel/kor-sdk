import pytest
import asyncio
from typing import List, Dict, Any

from kor_core.context import (
    ContextManager, get_context_manager,
    ContextResolverProtocol, ContextQuery, ContextResult, ContextItem,
    ContextError, ResolverNotFoundError
)

# Mock Resolver
class MockResolver:
    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        return ContextResult(
            items=[
                ContextItem(id="test", content="mock data", source_uri=uri)
            ]
        )

# Tests
@pytest.fixture
def context_manager():
    # Helper to get a fresh instance if needed, 
    # but ContextManager is a singleton, so we must be careful.
    # We can reset its state for testing.
    cm = get_context_manager()
    cm.resolvers.clear()
    cm.schemes.clear()
    return cm

def test_singleton_nature():
    cm1 = get_context_manager()
    cm2 = get_context_manager()
    assert cm1 is cm2

def test_register_resolver(context_manager):
    resolver = MockResolver()
    context_manager.register_resolver("mock", resolver)
    assert context_manager.get_resolver("mock") == resolver

@pytest.mark.asyncio
async def test_resolve_success(context_manager):
    resolver = MockResolver()
    context_manager.register_resolver("mock", resolver)
    
    result = await context_manager.resolve("mock://test")
    assert len(result.items) == 1
    assert result.items[0].content == "mock data"
    assert result.items[0].source_uri == "mock://test"

@pytest.mark.asyncio
async def test_resolve_missing_scheme_defaults_to_local(context_manager):
    # This should now succeed and default to local, but 'noscheme' path likely doesn't exist.
    # We need to mock the 'local' resolver for this test to verify the call happens.
    resolver = MockResolver()
    context_manager.register_resolver("local", resolver)
    
    result = await context_manager.resolve("README.md")
    assert result.items[0].source_uri == "local://README.md"

    with pytest.raises(ResolverNotFoundError) as excinfo:
        await context_manager.resolve("unknown://test")
    assert "No resolver registered" in str(excinfo.value)

@pytest.mark.asyncio
async def test_resolve_with_mapping(context_manager):
    resolver = MockResolver()
    context_manager.register_resolver("mock", resolver)
    
    # Load config mapping
    context_manager.load_config({"alias:test": "mock://mapped"})
    
    # Resolve using alias
    result = await context_manager.resolve("alias:test")
    
    # Should resolve to mock://mapped
    assert result.items[0].source_uri == "mock://mapped"

@pytest.mark.asyncio
async def test_resolve_with_wildcard_mapping(context_manager):
    resolver = MockResolver()
    context_manager.register_resolver("mock", resolver)
    
    # Load wildcard mapping
    context_manager.load_config({"skill:*": "mock://skills"})
    
    # Resolve using wildcard matching URI
    result = await context_manager.resolve("skill:python")
    
    # Should resolve to mock://skills
    assert result.items[0].source_uri == "mock://skills"
