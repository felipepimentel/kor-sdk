from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import supervisor_node, coder_node, researcher_node

def create_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("Coder", coder_node)
    workflow.add_node("Researcher", researcher_node)

    # Edge logic
    for member in ["Coder", "Researcher"]:
        # Workers return to supervisor
        workflow.add_edge(member, "Supervisor") 

    # Supervisor conditional edge
    conditional_map = {
        "Coder": "Coder",
        "Researcher": "Researcher",
        "FINISH": END
    }
    
    workflow.add_conditional_edges(
        "Supervisor", 
        lambda x: x["next_step"], 
        conditional_map
    )

    workflow.set_entry_point("Supervisor")
    return workflow.compile()
