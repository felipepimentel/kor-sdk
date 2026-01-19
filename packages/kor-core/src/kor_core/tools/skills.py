"""
Skills Meta-Tools

Tools that allow agents to discover and retrieve skills dynamically.
Skills are reusable knowledge/procedures that help agents perform tasks.
"""

from typing import Type, Optional

from pydantic import BaseModel, Field

from .base import KorTool
from ..skills import SkillRegistry


class SearchSkillsInput(BaseModel):
    """Input schema for SearchSkillsTool."""
    query: str = Field(description="Search query to find relevant skills")
    top_k: int = Field(default=3, description="Maximum number of skills to return")
    include_content: bool = Field(default=False, description="Include skill content in results")


class SearchSkillsTool(KorTool):
    """
    Meta-tool that searches for available skills.
    
    Skills are reusable knowledge/procedures that help the agent
    perform tasks more effectively.
    """
    name: str = "search_skills"
    description: str = "Search for available skills (knowledge/procedures) matching a query. Use this to find relevant instructions for your task."
    args_schema: Type[BaseModel] = SearchSkillsInput
    
    registry: Optional[SkillRegistry] = None
    
    def _run(self, query: str, top_k: int = 3, include_content: bool = False) -> str:
        if not self.registry:
            return "Error: Skill registry not configured."
        
        results = self.registry.search(query, top_k)
        return self.registry.format_results(results, include_content)


class GetSkillInput(BaseModel):
    """Input schema for GetSkillTool."""
    skill_name: str = Field(description="Name of the skill to retrieve")


class GetSkillTool(KorTool):
    """
    Tool to retrieve a specific skill's full content.
    """
    name: str = "get_skill"
    description: str = "Get the full content of a skill by name."
    args_schema: Type[BaseModel] = GetSkillInput
    
    registry: Optional[SkillRegistry] = None
    
    def _run(self, skill_name: str) -> str:
        if not self.registry:
            return "Error: Skill registry not configured."
        
        skill = self.registry.get(skill_name)
        if not skill:
            return f"Skill not found: {skill_name}"
        
        return f"# {skill.name}\n\n{skill.description}\n\n{skill.content}"


def create_skill_tools(registry: SkillRegistry) -> tuple:
    """
    Factory function to create skill tools with a registry.
    
    Args:
        registry: The SkillRegistry to use for searching and retrieving skills
        
    Returns:
        Tuple of (SearchSkillsTool, GetSkillTool) configured with the registry
    """
    search_tool = SearchSkillsTool()
    search_tool.registry = registry
    
    get_tool = GetSkillTool()
    get_tool.registry = registry
    
    return search_tool, get_tool


__all__ = [
    "SearchSkillsTool",
    "GetSkillTool",
    "SearchSkillsInput",
    "GetSkillInput",
    "create_skill_tools"
]
