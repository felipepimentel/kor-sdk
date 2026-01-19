import pytest
from dataclasses import dataclass
from unittest.mock import patch, MagicMock
from kor_core.search import SearchableRegistry

@dataclass
class SimpleItem:
    name: str
    description: str = ""
    
    @property
    def searchable_text(self):
        return f"{self.name} {self.description}"

class SimpleRegistry(SearchableRegistry[SimpleItem]):
    pass

def test_registry_registration_and_retrieval():
    """Verify basic registration and get."""
    registry = SimpleRegistry()
    item = SimpleItem(name="item1")
    
    registry.register(item)
    
    assert registry.get("item1") == item
    assert "item1" in registry
    assert len(registry) == 1

def test_registry_search_regex():
    """Verify regex search backend."""
    registry = SimpleRegistry(backend="regex")
    registry.register(SimpleItem(name="apple", description="a red fruit"))
    registry.register(SimpleItem(name="banana", description="a yellow fruit"))
    
    results = registry.search("red")
    assert len(results) == 1
    assert results[0].name == "apple"
    
    results = registry.search("fruit")
    assert len(results) == 2

def test_registry_search_bm25():
    """Verify bm25 search backend using a mock."""
    # Create a mock module for rank_bm25
    mock_rank_bm25 = MagicMock()
    mock_bm25_instance = MagicMock()
    # Mocking get_scores to return high scores for expected items
    # Query: "dog"
    # Items: [dog, cat]
    # We want index 0 (dog) to have higher score
    mock_bm25_instance.get_scores.return_value = [1.0, 0.0] 
    mock_rank_bm25.BM25Okapi.return_value = mock_bm25_instance

    with patch.dict("sys.modules", {"rank_bm25": mock_rank_bm25}):
        registry = SimpleRegistry(backend="bm25")
        
        registry.register(SimpleItem(name="dog", description="barking animal"))
        registry.register(SimpleItem(name="cat", description="meowing animal"))
        
        # This calls index() which imports rank_bm25.BM25Okapi (getting our mock)
        results = registry.search("dog")
        
        assert len(results) >= 1
        assert results[0].name == "dog"

def test_invalid_backend():
    """Verify error on unknown backend."""
    with pytest.raises(ValueError):
        SimpleRegistry(backend="unknown")
