"""
Search Tools Meta-Tool

A special tool that allows agents to discover relevant tools dynamically.
"""

from typing import Type, Optional
from pydantic import BaseModel, Field
from .base import KorTool
from .registry import ToolRegistry

class SearchToolsInput(BaseModel):
    query: str = Field(description="Search query to find relevant tools")
    top_k: int = Field(default=5, description="Maximum number of tools to return")

class SearchToolsTool(KorTool):
    """
    Meta-tool that searches for available tools.
    
    This reduces token usage by only loading relevant tools
    instead of passing all tools to the LLM context.
    """
    name: str = "search_tools"
    description: str = "Search for available tools matching a query. Use this to find the right tool for your task."
    args_schema: Type[BaseModel] = SearchToolsInput
    
    # Reference to the tool registry (must be set before use)
    registry: Optional[ToolRegistry] = None
    
    def _run(self, query: str, top_k: int = 5) -> str:
        if not self.registry:
            return "Error: Tool registry not configured."
        
        results = self.registry.search(query, top_k)
        return self.registry.format_results(results)

def create_search_tool(registry: ToolRegistry) -> SearchToolsTool:
    """Factory function to create a SearchToolsTool with a registry."""
    tool = SearchToolsTool()
    tool.registry = registry
    return tool
