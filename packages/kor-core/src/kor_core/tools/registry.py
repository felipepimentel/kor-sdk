"""
Tool Registry with Pluggable Search Backends

Provides flexible tool discovery using regex, BM25, or semantic search.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Type, Protocol
from .search import SearchBackend, RegexBackend, BM25Backend
from .base import KorTool

@dataclass
class ToolInfo:
    """
    Information and metadata about a registered tool.
    
    Attributes:
        name (str): The name of the tool.
        description (str): A brief description of what the tool does.
        tags (List[str]): Categorization tags for discovery.
        tool_class (Optional[Type[KorTool]]): The class used to instantiate the tool.
    """
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    tool_class: Optional[Type[KorTool]] = None
    
    @property
    def searchable_text(self) -> str:
        """
        Combined text for search indexing.
        
        Returns:
            str: Normalized text containing name, description, and tags.
        """
        return f"{self.name} {self.description} {' '.join(self.tags)}"

class ToolRegistry:
    """
    Central registry for tools with pluggable search backends.
    
    Manages tool registration, metadata, and discovery through various
    search strategies (Regex, BM25, Semantic).
    
    Attributes:
        BACKENDS (dict): Mapping of strategy names to backend classes.
    """
    
    BACKENDS = {
        "regex": RegexBackend[ToolInfo],
        "bm25": BM25Backend[ToolInfo],
    }
    
    def __init__(self, backend: str = "regex"):
        """
        Initializes the ToolRegistry.
        
        Args:
            backend (str): The search strategy to use ('regex' or 'bm25').
            
        Raises:
            ValueError: If an unknown backend is specified.
        """
        if backend not in self.BACKENDS:
            raise ValueError(f"Unknown backend: {backend}. Available: {list(self.BACKENDS.keys())}")
        
        self._backend: SearchBackend = self.BACKENDS[backend]()
        self._tools: Dict[str, ToolInfo] = {}
        self._indexed = False
    
    def register(self, tool: KorTool, tags: Optional[List[str]] = None) -> None:
        """
        Register a tool instance with optional tags.
        
        Args:
            tool (KorTool): The tool instance to register.
            tags (Optional[List[str]]): Metadata tags for discovery.
        """
        info = ToolInfo(
            name=tool.name,
            description=tool.description,
            tags=tags or [],
            tool_class=type(tool)
        )
        self._tools[tool.name] = info
        self._indexed = False  # Needs re-indexing
    
    def register_class(self, tool_cls: Type[KorTool], tags: Optional[List[str]] = None) -> None:
        """
        Register a tool class.
        
        Instantiates a temporary instance to extract metadata.
        
        Args:
            tool_cls (Type[KorTool]): The tool class to register.
            tags (Optional[List[str]]): Metadata tags.
        """
        instance = tool_cls()
        self.register(instance, tags)
    
    def _ensure_indexed(self) -> None:
        """Internal helper to ensure the search backend is up to date."""
        if not self._indexed:
            self._backend.index(list(self._tools.values()))
            self._indexed = True
    
    def search(self, query: str, top_k: int = 5) -> List[ToolInfo]:
        """
        Search for tools matching the query.
        
        Args:
            query (str): The search string.
            top_k (int): Maximum number of results to return.
            
        Returns:
            List[ToolInfo]: A list of matching tool metadata.
        """
        self._ensure_indexed()
        return self._backend.search(query, top_k)
    
    def get(self, name: str) -> Optional[ToolInfo]:
        """
        Retrieve tool metadata by name.
        
        Args:
            name (str): The tool name.
            
        Returns:
            Optional[ToolInfo]: Metadata if found, else None.
        """
        return self._tools.get(name)
    
    def get_all(self) -> List[ToolInfo]:
        """
        Get all registered tools metadata.
        
        Returns:
            List[ToolInfo]: List of all tool metadata objects.
        """
        return list(self._tools.values())
        
    def get_tool(self, name: str) -> Optional[KorTool]:
        """
        Get a fresh instance of a registered tool.
        
        Args:
            name (str): The tool name.
            
        Returns:
            Optional[KorTool]: A new tool instance if found, else None.
        """
        info = self._tools.get(name)
        if not info or not info.tool_class:
            return None
        # Instantiate fresh
        return info.tool_class()
    
    def format_results(self, results: List[ToolInfo]) -> str:
        """
        Format search results as a Markdown string for agent consumption.
        
        Args:
            results (List[ToolInfo]): Search results to format.
            
        Returns:
            str: Formatted Markdown string.
        """
        if not results:
            return "No matching tools found."
        
        lines = ["Available tools:"]
        for tool in results:
            lines.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(lines)

# Plugin extension point for semantic backend
def register_semantic_backend(backend_class: Type[SearchBackend]) -> None:
    """
    Register a custom semantic search backend (plugin extension point).
    
    Args:
        backend_class (Type[SearchBackend]): The custom backend class.
    """
    ToolRegistry.BACKENDS["semantic"] = backend_class

