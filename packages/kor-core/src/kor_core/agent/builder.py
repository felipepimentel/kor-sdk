"""
Fluent builder for creating custom KOR agents.
"""

from typing import List, Type, Optional, Any
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from ..tools.base import KorTool

class AgentBuilder:
    """
    A fluent API for building custom KOR agents.
    
    Example:
        agent = (
            AgentBuilder()
            .with_model("gpt-4")
            .add_tool(TerminalTool)
            .add_tool(BrowserTool)
            .build()
        )
    """
    
    def __init__(self):
        self._model: Optional[BaseChatModel] = None
        self._model_name: str = "gpt-4-turbo-preview"
        self._tools: List[Type[KorTool]] = []
        self._system_prompt: str = "You are a helpful AI assistant."
    
    def with_model(self, model_name: str) -> "AgentBuilder":
        """Set the LLM model to use."""
        self._model_name = model_name
        return self
    
    def with_llm(self, llm: BaseChatModel) -> "AgentBuilder":
        """Set a custom LLM instance."""
        self._model = llm
        return self
    
    def add_tool(self, tool_cls: Type[KorTool]) -> "AgentBuilder":
        """Add a tool to the agent."""
        self._tools.append(tool_cls)
        return self
    
    def with_tools(self, tools: List[Type[KorTool]]) -> "AgentBuilder":
        """Set multiple tools at once."""
        self._tools.extend(tools)
        return self
    
    def with_system_prompt(self, prompt: str) -> "AgentBuilder":
        """Set the system prompt for the agent."""
        self._system_prompt = prompt
        return self
    
    def build(self) -> Any:
        """Build and return the configured agent graph."""
        # Get or create LLM
        llm = self._model or ChatOpenAI(model=self._model_name)
        
        # Instantiate tools
        tool_instances = [t() for t in self._tools]
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(tool_instances) if tool_instances else llm
        
        return {
            "llm": llm_with_tools,
            "tools": tool_instances,
            "system_prompt": self._system_prompt,
        }
