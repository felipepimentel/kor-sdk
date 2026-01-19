"""
Tool Registry with Pluggable Search Backends
"""

from dataclasses import dataclass, field
from typing import List, Optional, Type
from ..searchable_registry import SearchableRegistry
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
        """Combined text for search indexing."""
        return f"{self.name} {self.description} {' '.join(self.tags)}"

class ToolRegistry(SearchableRegistry[ToolInfo]):
    """
    Central registry for tools using the unified SearchableRegistry base.
    """
    
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
        # Use parent class register method
        super().register(info)
    
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
        
    def get_tool(self, name: str) -> Optional[KorTool]:
        """
        Get a fresh instance of a registered tool.
        
        Args:
            name (str): The tool name.
            
        Returns:
            Optional[KorTool]: A new tool instance if found, else None.
        """
        info = self.get(name)
        if not info or not info.tool_class:
            return None
        # Instantiate fresh
        return info.tool_class()
    
    def format_results(self, results: List[ToolInfo]) -> str:
        """
        Format search results as a Markdown string.
        """
        if not results:
            return "No matching tools found."
        
        lines = ["Available tools:"]
        for tool in results:
            lines.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(lines)
