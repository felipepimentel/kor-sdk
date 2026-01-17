"""
Tool Registry with Pluggable Search Backends

Provides flexible tool discovery using regex, BM25, or semantic search.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Type, Protocol
from .base import KorTool

@dataclass
class ToolInfo:
    """Information about a registered tool."""
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    tool_class: Optional[Type[KorTool]] = None
    
    @property
    def searchable_text(self) -> str:
        """Combined text for search indexing."""
        return f"{self.name} {self.description} {' '.join(self.tags)}"

class SearchBackend(ABC):
    """Abstract base for search backends."""
    
    @abstractmethod
    def index(self, tools: List[ToolInfo]) -> None:
        """Index the tools for searching."""
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[ToolInfo]:
        """Search for tools matching the query."""
        pass

class RegexBackend(SearchBackend):
    """Simple regex/keyword matching backend."""
    
    def __init__(self):
        self._tools: List[ToolInfo] = []
    
    def index(self, tools: List[ToolInfo]) -> None:
        self._tools = tools
    
    def search(self, query: str, top_k: int = 5) -> List[ToolInfo]:
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        scored = []
        for tool in self._tools:
            text = tool.searchable_text.lower()
            # Score by number of matching words
            matches = sum(1 for word in query_words if word in text)
            if matches > 0:
                scored.append((matches, tool))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [tool for _, tool in scored[:top_k]]

class BM25Backend(SearchBackend):
    """BM25 ranking backend using rank_bm25."""
    
    def __init__(self):
        self._tools: List[ToolInfo] = []
        self._bm25 = None
        self._tokenized_corpus = []
    
    def index(self, tools: List[ToolInfo]) -> None:
        self._tools = tools
        
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("rank-bm25 is required for BM25Backend. Install with: pip install rank-bm25")
        
        # Tokenize the corpus
        self._tokenized_corpus = [
            tool.searchable_text.lower().split() for tool in tools
        ]
        self._bm25 = BM25Okapi(self._tokenized_corpus)
    
    def search(self, query: str, top_k: int = 5) -> List[ToolInfo]:
        if not self._bm25:
            return []
        
        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0:
                results.append(self._tools[idx])
        
        return results

class ToolRegistry:
    """
    Central registry for tools with pluggable search backend.
    
    Usage:
        registry = ToolRegistry(backend="bm25")
        registry.register(TerminalTool(), tags=["shell", "execute"])
        results = registry.search("run command")
    """
    
    BACKENDS = {
        "regex": RegexBackend,
        "bm25": BM25Backend,
    }
    
    def __init__(self, backend: str = "bm25"):
        if backend not in self.BACKENDS:
            raise ValueError(f"Unknown backend: {backend}. Available: {list(self.BACKENDS.keys())}")
        
        self._backend: SearchBackend = self.BACKENDS[backend]()
        self._tools: Dict[str, ToolInfo] = {}
        self._indexed = False
    
    def register(self, tool: KorTool, tags: Optional[List[str]] = None) -> None:
        """Register a tool with optional tags."""
        info = ToolInfo(
            name=tool.name,
            description=tool.description,
            tags=tags or [],
            tool_class=type(tool)
        )
        self._tools[tool.name] = info
        self._indexed = False  # Needs re-indexing
    
    def register_class(self, tool_cls: Type[KorTool], tags: Optional[List[str]] = None) -> None:
        """Register a tool class (instantiates temporarily for metadata)."""
        instance = tool_cls()
        self.register(instance, tags)
    
    def _ensure_indexed(self) -> None:
        """Ensure the backend has indexed all tools."""
        if not self._indexed:
            self._backend.index(list(self._tools.values()))
            self._indexed = True
    
    def search(self, query: str, top_k: int = 5) -> List[ToolInfo]:
        """Search for tools matching the query."""
        self._ensure_indexed()
        return self._backend.search(query, top_k)
    
    def get(self, name: str) -> Optional[ToolInfo]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all(self) -> List[ToolInfo]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def format_results(self, results: List[ToolInfo]) -> str:
        """Format search results as a string for the agent."""
        if not results:
            return "No matching tools found."
        
        lines = ["Available tools:"]
        for tool in results:
            lines.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(lines)

# Plugin extension point for semantic backend
def register_semantic_backend(backend_class: Type[SearchBackend]) -> None:
    """Register a custom semantic search backend (plugin extension point)."""
    ToolRegistry.BACKENDS["semantic"] = backend_class
