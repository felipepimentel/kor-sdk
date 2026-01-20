from typing import List, Dict, Any
from kor_core.context import get_context_manager
from kor_core.tools.base import BaseTool
from kor_core.exceptions import ToolError

class GetContextTool(BaseTool):
    """
    Tool to fetch context from various sources (files, skills, MCP, etc.)
    using the KOR Context Platform.
    """
    name: str = "get_context"
    description: str = (
        "Fetch context from a URI. Supports schemes: "
        "local:// (files), git:// (repos), skill:// (skills), mcp:// (external tools), "
        "and project aliases (project:rules, project:agent)."
    )
    
    def _run(self, uri: str, query: str = None) -> str:
        """Sync execution (not supported)."""
        raise NotImplementedError("GetContextTool is async only.")

    async def _arun(self, uri: str, query: str = None) -> str:
        """
        Execute the context resolution.
        
        Args:
            uri: The context URI (e.g., 'project:rules', 'skill:git', 'local://README.md')
            query: Optional query parameters (not commonly used yet)
            
        Returns:
            The content of the resolved context item.
        """
        try:
            cm = get_context_manager()
            result = await cm.resolve(uri, parameters={"query": query})
            
            if not result.items:
                return "No context found."
                
            # For now, return the content of the first item
            # Future: Return structured XML or handling for multiple items
            return result.items[0].content
            
        except Exception as e:
            raise ToolError(f"Failed to fetch context for '{uri}': {str(e)}")
