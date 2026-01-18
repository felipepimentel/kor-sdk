from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .state import AgentState
from ..config import ConfigManager
from ..tools.terminal import TerminalTool
from ..tools.browser import BrowserTool

def get_tool_from_registry(name: str):
    """Attempt to get a tool from the global registry, fallback to defaults."""
    try:
        from ..kernel import get_kernel
        k = get_kernel()
        k.boot()
        registry = k.registry.get_service("tools")
        if registry:
            tool_info = registry.get(name)
            if tool_info:
                tool = tool_info.tool_class()
                # Inject registry if the tool needs it (e.g. SearchToolsTool)
                if hasattr(tool, "registry"): tool.registry = registry
                return tool
                
            # If name is not found, try a semantic search as fallback?
            # For now, we prefer exact names or known fallbacks.
    except Exception as e:
        print(f"Tool lookup error: {e}")
        pass
    
    # Fallbacks for built-in tools if registry is missing
    if name == "terminal": return TerminalTool()
    if name == "browser": return BrowserTool()
    return None

def get_best_tool_for_node(node_name: str, task_context: str = "") -> Any:
    """Discovers the best tool for a given node based on defaults or registry."""
    # Mapping of nodes to their 'preferred' primary tool
    defaults = {
        "Coder": "terminal",
        "Researcher": "browser",
        "Explorer": "search_tools"
    }
    
    # 1. Check if the task context explicitly mentions a tool
    # 2. Return the default for the node
    tool_name = defaults.get(node_name)
    return get_tool_from_registry(tool_name) if tool_name else None


# --- Supervisor Node ---
from ..prompts import PromptLoader

# --- Supervisor Node ---
members = ["Coder", "Researcher", "Explorer"]
# Load prompt from file
system_prompt_template = PromptLoader.load("supervisor")
# Fallback if file load fails (though simple loader returns empty str, we might want default)
if not system_prompt_template:
    system_prompt_template = (
        "You are a supervisor tasked with managing a conversation between the"
        " following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )

options = ["FINISH"] + members

def get_model():
    """Factory to get the configured chat model."""
    try:
        config = ConfigManager().load()
        if config.model.provider == "openai":
            # Ensure API key is set if needed (LangChain usually handles env vars, 
            # but we can pass it explicitly if in secrets)
            api_key = config.secrets.openai_api_key
            return ChatOpenAI(
                model=config.model.name, 
                temperature=config.model.temperature,
                api_key=api_key
            )
        elif config.model.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            api_key = config.secrets.anthropic_api_key
            return ChatAnthropic(
                model=config.model.name,
                temperature=config.model.temperature,
                api_key=api_key
            )
    except Exception as e:
        print(f"Failed to load model: {e}")
    return None

def supervisor_node(state: AgentState):
    """Decides which worker should act next."""
    llm = get_model()
    
    if not llm:
        last_msg_obj = state['messages'][-1]
        # If the last message is from a worker, we should finish (for simple one-shot tasks)
        if hasattr(last_msg_obj, "name") and last_msg_obj.name in members:
             return {"next_step": "FINISH"}

        last_msg = last_msg_obj.content.lower()
        if "code" in last_msg or "file" in last_msg or "list" in last_msg:
            return {"next_step": "Coder"}
        elif "research" in last_msg or "search" in last_msg or "web" in last_msg:
            return {"next_step": "Researcher"}
        return {"next_step": "FINISH"}

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_template),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    schema = {
        "name": "route",
        "description": "Select the next worker or FINISH",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {"type": "string", "enum": options}
            },
            "required": ["next"]
        }
    }

    supervisor_chain = prompt | llm.with_structured_output(schema)

    return supervisor_chain.invoke(state)

# --- Worker Nodes ---

def coder_node(state: AgentState):
    """
    Coder Worker. Can execute terminal commands.
    """
    # Simple logic: If the user message asks to list files, we do it.
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Coder", last_msg)
    
    response = "I am ready to code."
    
    # Very naive instruction following for V1
    if "list" in last_msg.lower():
        output = tool._run("ls -la") if tool else "No tool available"
        response = f"Listing files:\n{output}"
    
    return {
        "messages": [
            HumanMessage(content=f"[Coder] {response}", name="Coder")
        ]
    }

def researcher_node(state: AgentState):
    """
    Researcher Worker. Can search the web.
    """
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Researcher", last_msg)
    
    response = "I am ready to research."
    # Naive extraction (in real world an Agent would decide arguments)
    if "search" in last_msg.lower() or "research" in last_msg.lower():
        # Strip "search"
        query = last_msg.replace("search", "").replace("research", "").strip() or "python mcp"
        output = tool._run(query) if tool else "No tool available"
        response = f"Search Results for '{query}':\n{output}"

    return {
        "messages": [
            HumanMessage(content=f"[Researcher] {response}", name="Researcher")
        ]
    }

def explorer_node(state: AgentState):
    """
    Discovery Worker. Can search for available tools.
    """
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Explorer", last_msg)
    
    response = "I am ready to discover capabilities."
    if "tool" in last_msg.lower() or "find" in last_msg.lower():
        query = last_msg.replace("find", "").replace("tool", "").strip() or "general"
        output = tool._run(query) if tool else "No tool available"
        response = f"Discovered Capabilities for '{query}':\n{output}"
        
    return {
        "messages": [
            HumanMessage(content=f"[Explorer] {response}", name="Explorer")
        ]
    }
