from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import supervisor_node, coder_node, researcher_node, explorer_node, architect_node, reviewer_node
from .factory import AgentFactory
from ..kernel import get_kernel

def create_graph(checkpointer=None):
    """
    Creates a dynamic agent graph based on configuration.
    """
    kernel = get_kernel()
    
    # Ensure initialized (for CLI tool usage where boot might be manual)
    if not kernel._is_initialized:
        kernel.boot()
        
    factory = AgentFactory(kernel)
    workflow = StateGraph(AgentState)
    
    # 1. Add Supervisor (Always present)
    # Ideally, supervisor itself should be configurable/dynamic too.
    # For V1, we keep the robust 'supervisor_node' from nodes.py
    # but we might want to inject the DYNAMIC list of members into it.
    workflow.add_node("Supervisor", supervisor_node)
    
    # 2. Add Member Nodes (Dynamic)
    # We read from config.agent.supervisor_members
    # Fallback to defaults if empty?
    members = kernel.config.agent.supervisor_members or ["Architect", "Coder", "Reviewer", "Researcher", "Explorer"]
    
    # Legacy mapping for hardcoded nodes
    legacy_nodes = {
        "Coder": coder_node,
        "Researcher": researcher_node,
        "Explorer": explorer_node,
        "Architect": architect_node,
        "Reviewer": reviewer_node
    }

    # 3. Dynamic Conditional Edges
    # Map each member name to itself to support the Supervisor's routing logic
    conditional_map = {name: name for name in members}
    conditional_map["FINISH"] = END
    conditional_map["Supervisor"] = "Supervisor"

    for member_name in members:
        node_func = None
        
        # A. Check for Configured Custom Definition
        if member_name in kernel.config.agent.definitions:
            definition = kernel.config.agent.definitions[member_name]
            node_func = factory.create_node(member_name, definition)
            
        # B. Fallback to Legacy Hardcoded Node
        elif member_name in legacy_nodes:
            node_func = legacy_nodes[member_name]
            
        # C. Critical Error if unknown
        if not node_func:
            print(f"Warning: Agent '{member_name}' has no definition and is not a built-in.")
            continue
            
        workflow.add_node(member_name, node_func)
        
        # Hub & Spoke Wiring: Specific nodes define their own routing via 'next_step'
        if member_name in ["Architect", "Coder", "Reviewer"]:
             workflow.add_conditional_edges(member_name, lambda x: x["next_step"], conditional_map)
        else:
             # Default Workers always report back to supervisor
             workflow.add_edge(member_name, "Supervisor")
    
    # We need to ensure supervisor_node uses the CORRECT list of members in its prompt.
    # The current supervisor_node in nodes.py has HARDCODED 'members' list.
    # We need to patching or passing context. 
    # To avoid changing nodes.py signature (AgentState -> Dict), 
    # we can assume supervisor_node reads from config/global state if we refactored it.
    # BUT we didn't refactor supervisor_node yet to read dynamic members.
    # We should probably do that next.
    
    workflow.add_conditional_edges(
        "Supervisor", 
        lambda x: x["next_step"], 
        conditional_map
    )

    workflow.set_entry_point("Supervisor")
    
    # Use kernel checkpointer if not provided
    if checkpointer is None:
        try:
            checkpointer = kernel.registry.get_service("checkpointer")
        except Exception:
            # Fallback or just no persistence
            pass
            
    return workflow.compile(checkpointer=checkpointer)
