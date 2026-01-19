"""
ExternalToolExecutor node.

This node handles tool calls for tools that exist on the client side.
It binds external tools to the LLM and, if the LLM generates tool calls,
populates `pending_tool_calls` so the Adapter can return them to the client.
"""
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
from ...kernel import get_kernel
from ..state import AgentState
import json
import logging

logger = logging.getLogger(__name__)


def external_tool_executor_node(state: AgentState):
    """
    Handles external tool invocation.
    
    If external_tools are present in the state, this node binds them to the LLM
    and invokes it. If the LLM generates tool_calls, we store them in
    pending_tool_calls and signal FINISH so the adapter can return them.
    """
    kernel = get_kernel()
    external_tools = state.get("external_tools", [])
    
    if not external_tools:
        return {
            "messages": [AIMessage(content="[ExternalToolExecutor] No external tools provided.", name="ExternalToolExecutor")],
            "next_step": "Supervisor"
        }
    
    try:
        llm = kernel.model_selector.get_model("default")
    except Exception as e:
        logger.warning(f"No LLM available for external tool execution: {e}")
        llm = None
    
    if not llm:
        # Fallback: Generate a mock tool call using the first available tool
        # This enables testing the full pipeline without an LLM
        first_tool = external_tools[0] if external_tools else None
        if first_tool and first_tool.get("type") == "function":
            func_def = first_tool.get("function", {})
            tool_name = func_def.get("name", "unknown_tool")
            
            # Try to extract a city from the last message for weather-like tools
            last_msg = ""
            for msg in reversed(state.get("messages", [])):
                if hasattr(msg, "content") and not getattr(msg, "name", None):
                    last_msg = msg.content
                    break
            
            # Simple heuristic: extract city name (words after "in" or capitalized words)
            import re
            city_match = re.search(r'\bin\s+([A-Z][a-z]+)', last_msg)
            city = city_match.group(1) if city_match else "Unknown"
            
            mock_args = {"city": city}  # Generic args
            
            mock_tool_call = {
                "id": f"call_mock_{tool_name}",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(mock_args)
                }
            }
            
            logger.info(f"[Fallback] Generating mock tool call: {mock_tool_call}")
            return {
                "messages": [AIMessage(content=f"[ExternalToolExecutor] Calling {tool_name}...", name="ExternalToolExecutor")],
                "pending_tool_calls": [mock_tool_call],
                "next_step": "FINISH"
            }
        
        return {
            "messages": [AIMessage(content="[ExternalToolExecutor] No LLM and no suitable tools for fallback.", name="ExternalToolExecutor")],
            "next_step": "FINISH"
        }
    
    # Convert OpenAI-style tool schemas to LangChain StructuredTool format
    # OpenAI format: {"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}
    langchain_tools = []
    for tool_schema in external_tools:
        if tool_schema.get("type") == "function":
            func_def = tool_schema.get("function", {})
            name = func_def.get("name", "unknown_tool")
            description = func_def.get("description", "")
            parameters = func_def.get("parameters", {})
            
            # Create a dummy tool that does nothing (we won't execute it)
            # We just need the schema for LLM binding
            def placeholder_func(**kwargs):
                return json.dumps(kwargs)
            
            tool = StructuredTool.from_function(
                func=placeholder_func,
                name=name,
                description=description,
                args_schema=None  # We'll let the LLM figure it out from the description
            )
            langchain_tools.append(tool)
    
    if not langchain_tools:
        return {
            "messages": [AIMessage(content="[ExternalToolExecutor] Could not parse external tools.", name="ExternalToolExecutor")],
            "next_step": "Supervisor"
        }
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(langchain_tools)
    
    # Get the last user message for context
    last_user_msg = ""
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "content") and not getattr(msg, "name", None):
            last_user_msg = msg.content
            break
    
    try:
        response = llm_with_tools.invoke(last_user_msg)
    except Exception as e:
        logger.error(f"Error invoking LLM with tools: {e}")
        return {
            "messages": [AIMessage(content=f"Error: {e}", name="ExternalToolExecutor")],
            "next_step": "FINISH"
        }
    
    # Check if the LLM wants to call a tool
    if hasattr(response, "tool_calls") and response.tool_calls:
        # Format tool calls in OpenAI format
        openai_tool_calls = []
        for tc in response.tool_calls:
            openai_tool_calls.append({
                "id": tc.get("id", f"call_{hash(tc['name'])}"),
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc.get("args", {}))
                }
            })
        
        return {
            "messages": [response],
            "pending_tool_calls": openai_tool_calls,
            "next_step": "FINISH"  # Return control to adapter
        }
    
    # No tool calls, just return the response
    return {
        "messages": [response],
        "next_step": "Supervisor"
    }
