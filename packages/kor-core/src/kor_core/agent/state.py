from typing import TypedDict, Annotated, Sequence, Optional, List, Any
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of the KOR agent graph.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_step: str
    
    # Hub & Spoke Architecture Fields
    user_goal: Optional[str]
    spec: Optional[str]
    files_changed: Optional[List[str]]
    errors: Optional[List[str]]
    
    
    # External Tool Support (Phase 2)
    external_tools: Optional[List[Any]]  # Tool schemas from client
    pending_tool_calls: Optional[List[Any]]  # Tool calls to return to client

    # Native Planning (Phase 3)
    plan: Optional[List["PlanTask"]]
    current_task_id: Optional[str]

class PlanTask(TypedDict):
    """
    A single unit of work in the agent's plan.
    """
    id: str  # Unique identifier (1, 2, 2.1)
    description: str  # What needs to be done
    status: str  # pending, active, completed, failed
    result: Optional[str]  # Summary of what was accomplished
    parent_id: Optional[str]  # ID of parent task (for subtasks)
    depth: int  # Nesting level (0 = root, 1 = subtask, etc.)


