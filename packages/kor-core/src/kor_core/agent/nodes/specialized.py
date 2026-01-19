from langchain_core.messages import HumanMessage
from ..state import AgentState
from .base import get_best_tool_for_node

def researcher_node(state: AgentState):
    """Researcher Worker. Can search the web."""
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Researcher", last_msg)
    
    response = "I am ready to research."
    if "search" in last_msg.lower() or "research" in last_msg.lower():
        query = last_msg.replace("search", "").replace("research", "").strip() or "python mcp"
        output = tool._run(query) if tool else "No tool available"
        response = f"Search Results for '{query}':\n{output}"

    return {
        "messages": [HumanMessage(content=f"[Researcher] {response}", name="Researcher")]
    }

def explorer_node(state: AgentState):
    """Discovery Worker. Can search for available tools."""
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Explorer", last_msg)
    
    response = "I am ready to discover capabilities."
    if "tool" in last_msg.lower() or "find" in last_msg.lower():
        query = last_msg.replace("find", "").replace("tool", "").strip() or "general"
        output = tool._run(query) if tool else "No tool available"
        response = f"Discovered Capabilities for '{query}':\n{output}"
        
    return {
        "messages": [HumanMessage(content=f"[Explorer] {response}", name="Explorer")]
    }
