from pathlib import Path
from ..state import AgentState
from ..planning import Planner

def ensure_plan_node(state: AgentState) -> dict:
    """
    Node that ensures the agent's internal plan is synced with PLAN.md.
    
    This node acts as an initializer/synchronizer. It allows the agent
    to pick up a plan created by a human (via file) or persist its 
    own plan to the file system.
    """
    # 1. Initialize Planner from current state
    planner = Planner.from_state(
        state.get("plan", []), 
        state.get("current_task_id")
    )
    
    # 2. Bind to physical file
    # By default, we look for PLAN.md in the current working directory.
    # Future: This could be configurable via state or kernel config.
    plan_path = Path("PLAN.md") 
    planner.bind_to_file(plan_path)
    
    # 3. Sync (Read file if exists, else write state)
    planner.sync()
    
    # 4. Return updated fields to patch State
    return {
        "plan": planner.tasks,
        "current_task_id": planner.current_task_id
    }
