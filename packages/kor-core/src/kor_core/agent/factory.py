from typing import Callable, Any, Dict, Optional, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
import logging
from .state import AgentState

if TYPE_CHECKING:
    from ..llm.selector import ModelSelector
    from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Creates executable agent nodes from configuration definitions.
    
    Uses explicit dependency injection for cleaner architecture and testing.
    
    Attributes:
        model_selector (ModelSelector): For resolving LLM models by purpose.
        tool_registry (ToolRegistry): For resolving tools by name.
    """
    
    def __init__(
        self, 
        model_selector: "ModelSelector",
        tool_registry: Optional["ToolRegistry"] = None
    ):
        """
        Initializes the AgentFactory with explicit dependencies.
        
        Args:
            model_selector (ModelSelector): The model selector for LLM resolution.
            tool_registry (Optional[ToolRegistry]): The tool registry for tool resolution.
        """
        self.model_selector = model_selector
        self.tool_registry = tool_registry
    
    @classmethod
    def from_kernel(cls, kernel) -> "AgentFactory":
        """
        Factory method to create an AgentFactory from a Kernel instance.
        
        This maintains backward compatibility while using the new DI pattern.
        
        Args:
            kernel: The Kernel instance.
            
        Returns:
            AgentFactory: A configured factory instance.
        """
        tool_registry = None
        try:
            tool_registry = kernel.registry.get_tool_registry()
        except (KeyError, AttributeError):
            logger.debug("Tool registry not available")
        
        return cls(
            model_selector=kernel.model_selector,
            tool_registry=tool_registry
        )
        
    def create_node(self, name: str, definition: Any) -> Callable[[AgentState], Dict[str, Any]]:
        """
        Creates a LangGraph-compatible node function.
        
        Args:
            name: The name of the agent (e.g. "SecurityAuditor")
            definition: An AgentDefinition instance or dict
            
        Returns:
            A function that takes AgentState and returns a state update.
        """
        # Resolve LLM via Selector
        purpose = getattr(definition, "llm_purpose", "default")
        llm = self.model_selector.get_model(purpose)
        
        # Resolve Tools via Registry
        tools = []
        tool_names = getattr(definition, "tools", [])
        
        if self.tool_registry and tool_names:
            for t_name in tool_names:
                tool_instance = self.tool_registry.get_tool(t_name)
                
                if tool_instance:
                    # Inject registry if needed (like Explorer)
                    if hasattr(tool_instance, "registry"):
                        tool_instance.registry = self.tool_registry
                    tools.append(tool_instance)
                else:
                    logger.warning(f"Tool '{t_name}' not found in registry for agent '{name}'")
            
        # Bind Tools
        if tools:
            llm = llm.bind_tools(tools)
            
        # Create the node function closure
        def agent_node(state: AgentState) -> Dict[str, Any]:
            # Construct system prompt
            role = getattr(definition, "role", "You are a helpful assistant.")
            goal = getattr(definition, "goal", "")
            
            system_message = f"{role}\nYour goal is: {goal}"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                MessagesPlaceholder(variable_name="messages")
            ])
            
            chain = prompt | llm
            response = chain.invoke(state)
            
            # Tag the message with agent name
            response.name = name
            
            return {"messages": [response]}
            
        return agent_node

