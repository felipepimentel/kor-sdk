from typing import Callable, Any, Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from .state import AgentState

class AgentFactory:
    """
    Creates executable agent nodes from configuration definitions.
    """
    
    def __init__(self, kernel):
        self.kernel = kernel
        
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
        # Assuming definition has .llm_purpose
        purpose = getattr(definition, "llm_purpose", "default")
        llm = self.kernel.model_selector.get_model(purpose)
        
        # Resolve Tools via Registry
        tools = []
        tool_names = getattr(definition, "tools", [])
        
        # We need to access the tool registry service
        # It might be registered as 'tools' in the service registry
        try:
            tool_registry = self.kernel.registry.get_service("tools")
            for t_name in tool_names:
                # Use the registry's factory method to get a fresh instance
                tool_instance = tool_registry.get_tool(t_name)
                
                if tool_instance:
                    # Inject registry if needed (like Explorer)
                    if hasattr(tool_instance, "registry"):
                        # Some tools might depend on the registry itself
                        tool_instance.registry = tool_registry
                    tools.append(tool_instance)
                else:
                    # Fallback or Log warning
                    pass
        except Exception:
            # Registry might not be ready or tools service missing
            pass
            
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
            
            # We must wrap the response in a way that LangGraph expects for state update
            # Usually strict state schema: {"messages": [response]}
            
            # Also, we should tag the message name?
            # LangChain messages support 'name' field, but ChatModel response is AIMessage.
            # We can coerce it or wrap it.
            # But usually AIMessage is enough.
            # If we want the supervisor to know WHO responded, we might need a custom artifact?
            # Or just rely on Last Message.
            
            # Let's customize the name property if supported by the model/platform
            response.name = name
            
            return {"messages": [response]}
            
        return agent_node
