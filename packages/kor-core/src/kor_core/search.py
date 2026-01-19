"""
Shared Search Infrastructure for KOR SDK
"""

import re
from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic, Protocol

class Searchable(Protocol):
    """Protocol for items that can be indexed and searched."""
    @property
    def searchable_text(self) -> str:
        ...

T = TypeVar("T", bound=Searchable)

class SearchBackend(ABC, Generic[T]):
    """Abstract base for search backends."""
    
    @abstractmethod
    def index(self, items: List[T]) -> None:
        """Index the items for searching."""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[T]:
        """Search for items matching the query."""
        pass

class RegexBackend(SearchBackend[T]):
    """Simple regex/keyword matching backend."""
    
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
    """BM25 ranking backend using rank_bm25."""
    
    def __init__(self, name: str = "Backend"):
        self._items: List[T] = []
        self._bm25 = None
        self._name = name
    
    def index(self, items: List[T]) -> None:
        self._items = items
        
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(f"rank-bm25 is required for BM25Backend ({self._name}). Install with: pip install rank-bm25")
        
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
