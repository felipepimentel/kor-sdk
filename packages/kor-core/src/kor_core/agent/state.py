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

