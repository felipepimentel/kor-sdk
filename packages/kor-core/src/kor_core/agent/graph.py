from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import supervisor_node, external_tool_executor_node
from .factory import AgentFactory
from ..kernel import get_kernel

def create_graph(checkpointer=None):
    """
    Creates a dynamic agent graph based on configuration.
    """
    kernel = get_kernel()
    
    # Ensure initialized (for CLI tool usage where boot might be manual)
    if not kernel._is_initialized:
        kernel.boot_sync()
        
    factory = AgentFactory.from_kernel(kernel)
    workflow = StateGraph(AgentState)
    
    # 1. Add Supervisor (Always present)
    workflow.add_node("Supervisor", supervisor_node)
    
    # 2. Add ExternalToolExecutor (For client-side tools)
    workflow.add_node("ExternalToolExecutor", external_tool_executor_node)
    
    # 3. Add Member Nodes (Dynamic from config)
    members = kernel.config.agent.supervisor_members
    
    # 4. Dynamic Conditional Edges
    conditional_map = {name: name for name in members}
    conditional_map["FINISH"] = END
    conditional_map["Supervisor"] = "Supervisor"
    conditional_map["ExternalToolExecutor"] = "ExternalToolExecutor"

    for member_name in members:
        # Get or create agent definition from config
        if member_name in kernel.config.agent.definitions:
            definition = kernel.config.agent.definitions[member_name]
        else:
            # Create default definition for known agents
            from ..config import AgentWorkerConfig
            definition = AgentWorkerConfig(
                name=member_name,
                role=f"You are the {member_name} agent.",
                goal=f"Fulfill the {member_name} role.",
                tools=[]
            )
            
        node_func = factory.create_node(member_name, definition)
        workflow.add_node(member_name, node_func)
        
        # Hub & Spoke Wiring: Specific nodes define their own routing
        if member_name in ["Architect", "Coder", "Reviewer"]:
             workflow.add_conditional_edges(member_name, lambda x: x["next_step"], conditional_map)
        else:
             workflow.add_edge(member_name, "Supervisor")
    
    # We need to ensure supervisor_node uses the CORRECT list of members in its prompt.
    # The current supervisor_node in nodes.py has HARDCODED 'members' list.
    # We need to patching or passing context. 
    # To avoid changing nodes.py signature (AgentState -> Dict), 
    # we can assume supervisor_node reads from config/global state if we refactored it.
    # BUT we didn't refactor supervisor_node yet to read dynamic members.
    # We should probably do that next.
    
    # ExternalToolExecutor uses conditional routing (FINISH or Supervisor)
    workflow.add_conditional_edges(
        "ExternalToolExecutor",
        lambda x: x["next_step"],
        conditional_map
    )
    
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
