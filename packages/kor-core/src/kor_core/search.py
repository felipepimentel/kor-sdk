"""
Unified Search Infrastructure for KOR SDK

Provides:
- Searchable protocol for items that can be indexed
- Pluggable search backends (Regex, BM25, Semantic)
- SearchableRegistry base class for registries with search capabilities
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, TypeVar, Generic, Type, Protocol

logger = logging.getLogger(__name__)


# =============================================================================
# Protocol
# =============================================================================

class Searchable(Protocol):
    """
    Protocol for items that can be indexed and searched.
    
    Items must have a 'name' property for identification and a 'searchable_text'
    property that returns the combined text for search indexing.
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for the item."""
        ...
    
    @property
    def searchable_text(self) -> str:
        """Combined text for search indexing."""
        ...


T = TypeVar("T", bound=Searchable)


# =============================================================================
# Search Backends
# =============================================================================

class SearchBackend(ABC, Generic[T]):
    """
    Abstract base for search backends.
    
    Backends are responsible for indexing items and returning search results.
    """
    
    @abstractmethod
    def index(self, items: List[T]) -> None:
        """Index the items for searching."""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[T]:
        """Search for items matching the query."""
        pass


class RegexBackend(SearchBackend[T]):
    """
    Simple regex/keyword matching backend.
    
    Uses word-level matching with scoring based on number of matches.
    No external dependencies required.
    """
    
    def __init__(self):
        self._items: List[T] = []
    
    def index(self, items: List[T]) -> None:
        self._items = items
    
    def search(self, query: str, top_k: int = 5) -> List[T]:
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        scored = []
        for item in self._items:
            text = item.searchable_text.lower()
            matches = sum(1 for word in query_words if word in text)
            if matches > 0:
                scored.append((matches, item))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]


class BM25Backend(SearchBackend[T]):
    """
    BM25 ranking backend using rank_bm25.
    
    Provides better ranking than simple keyword matching.
    Requires: pip install rank-bm25
    """
    
    def __init__(self, name: str = "Backend"):
        self._items: List[T] = []
        self._bm25 = None
        self._name = name
    
    def index(self, items: List[T]) -> None:
        self._items = items
        
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(
                f"rank-bm25 is required for BM25Backend ({self._name}). "
                "Install with: pip install rank-bm25"
            )
        
        tokenized_corpus = [
            item.searchable_text.lower().split() for item in items
        ]
        self._bm25 = BM25Okapi(tokenized_corpus)
    
    def search(self, query: str, top_k: int = 5) -> List[T]:
        if not self._bm25:
            return []
        
        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)
        
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0:
                results.append(self._items[idx])
        
        return results


# =============================================================================
# Searchable Registry
# =============================================================================

class SearchableRegistry(Generic[T]):
    """
    Generic base class for registries with pluggable search backends.
    
    Manages item registration, metadata, and discovery through various
    search strategies (Regex, BM25, Semantic).
    
    Type Parameters:
        T: The type of items stored in the registry (must implement Searchable).
    
    Attributes:
        BACKENDS (dict): Mapping of strategy names to backend classes.
    
    Example:
        class ToolRegistry(SearchableRegistry[ToolInfo]):
            pass
            
        registry = ToolRegistry(backend="bm25")
        registry.register(my_tool_info)
        results = registry.search("terminal execute")
    """
    
    BACKENDS: Dict[str, Type[SearchBackend]] = {
        "regex": RegexBackend,
        "bm25": BM25Backend,
    }
    
    def __init__(self, backend: str = "regex"):
        """
        Initializes the SearchableRegistry.
        
        Args:
            backend (str): The search strategy to use ('regex' or 'bm25').
            
        Raises:
            ValueError: If an unknown backend is specified.
        """
        if backend not in self.BACKENDS:
            raise ValueError(
                f"Unknown backend: {backend}. Available: {list(self.BACKENDS.keys())}"
            )
        
        self._backend: SearchBackend = self.BACKENDS[backend]()
        self._items: Dict[str, T] = {}
        self._indexed = False
        self._backend_name = backend
    
    def register(self, item: T, tags: Optional[List[str]] = None) -> None:
        """
        Register an item in the registry.
        
        Args:
            item (T): The item to register (must have 'name' attribute).
            tags (Optional[List[str]]): Metadata tags (if supported by item type).
        """
        name = getattr(item, "name", str(item))
        self._items[name] = item
        self._indexed = False  # Needs re-indexing
        logger.debug(f"Registered item: {name}")
    
    def _ensure_indexed(self) -> None:
        """Internal helper to ensure the search backend is up to date."""
        if not self._indexed and self._items:
            self._backend.index(list(self._items.values()))
            self._indexed = True
    
    def search(self, query: str, top_k: int = 5) -> List[T]:
        """
        Search for items matching the query.
        
        Args:
            query (str): The search string.
            top_k (int): Maximum number of results to return.
            
        Returns:
            List[T]: A list of matching items.
        """
        self._ensure_indexed()
        return self._backend.search(query, top_k)
    
    def get(self, name: str) -> Optional[T]:
        """
        Retrieve an item by name.
        
        Args:
            name (str): The item name.
            
        Returns:
            Optional[T]: The item if found, else None.
        """
        return self._items.get(name)
    
    def get_all(self) -> List[T]:
        """
        Get all registered items.
        
        Returns:
            List[T]: List of all registered items.
        """
        return list(self._items.values())
    
    def __len__(self) -> int:
        """Returns the number of registered items."""
        return len(self._items)
    
    def __contains__(self, name: str) -> bool:
        """Check if an item is registered."""
        return name in self._items
    
    def clear(self) -> None:
        """Remove all registered items."""
        self._items.clear()
        self._indexed = False

    @classmethod
    def register_semantic_backend(cls, backend_class: Type[SearchBackend]) -> None:
        """
        Register a custom semantic search backend (plugin extension point).
        
        Args:
            backend_class (Type[SearchBackend]): The custom backend class.
        """
        cls.BACKENDS["semantic"] = backend_class
        logger.info("Registered semantic search backend")
