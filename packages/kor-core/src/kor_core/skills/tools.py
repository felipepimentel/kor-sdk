"""
Search Skills Meta-Tool

A special tool that allows agents to discover relevant skills dynamically.
"""

from typing import Type, Optional
from pydantic import BaseModel, Field
from ..tools.base import KorTool
from .registry import SkillRegistry

class SearchSkillsInput(BaseModel):
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
    """Factory function to create skill tools with a registry."""
    search_tool = SearchSkillsTool()
    search_tool.registry = registry
    
    get_tool = GetSkillTool()
    get_tool.registry = registry
    
    return search_tool, get_tool
